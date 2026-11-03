"""Land a card's build inputs: mirror, regenerate the project, stage both halves, then judge the pair.

Why this exists (card t_8f1f3465, friction 2026-10-30 item 3). A build script writes a delivery
source, tools/sync_art.py copies it into game/datafiles/streams, and tools/gen_project.py rewrites
game/PrimordialParadox.yyp so the project names it as an Included File. Nothing in that chain was the
producer's job, so producers did not run it: the commit then carried a .yyp naming a stream it did
not carry, or a stream the project did not name, and tools/check_build_inputs.py --staged refused the
lane at commit time. FIX-YYP-6 through FIX-YYP-11 are eleven recurrences of the same shape, and each
one was closed by a person running the two tools by hand and staging the result.

This script is that person's two commands plus the staging, in one call, so a producer can end by
handing over the paths it just wrote:

    python tools/land_asset.py assets/audio/pp_04_fight_baroque_v3/pp_04_fight_baroque_v3.ogg

What it does, in this order, and why the order is this one:

  1. Stages the caller's paths FIRST. A path that the .gitignore refuses is reported here, before ten
     seconds of rendering has been spent on it, and the tree-wide rules ignore .wav, .mp3 and most
     .mid files, so a stream builder's by-products are named and skipped rather than refused.
  2. Deletes a mirrored .ogg whose source is gone, before anything reads the mirror. A stream the
     music lane removed otherwise stays in game/datafiles forever, the project keeps naming it, and
     no commit can answer the refusal that follows; prune_mirror_streams() records the measurement.
  3. Runs tools/sync_art.py, which mirrors every .ogg under assets/audio/<cue>/ into
     game/datafiles/streams, the sprites into game/datafiles/art, and the cues into
     game/datafiles/sfx. The mirror is gitignored on purpose, so nothing under it is ever staged.
  4. Runs tools/gen_project.py, which rewrites the .yyp and the .yy files the folders on disk imply.
     This is the half that names the new Included File, and it is idempotent: a second run writes
     nothing.
  5. Stages exactly what steps 3 and 4 changed, found by hashing the dirty files under this project
     before and after the two runs. A file that was already modified before this call is only staged
     when its bytes changed during it, so a shared working tree's other edits are not swept along.
     A .yy or .yyp the generator has already made current on disk is staged too, staged or not
     before, because the index has to agree with the disk the generator just wrote.
  6. Runs tools/check_build_inputs.py --staged, which is the command the commit gate itself runs
     (manager/guard/commit_gate.py, and pine/pregate.py's staged_check). Its exit code is this
     script's exit code, so a caller that checks the return value cannot land a broken pair.

Safe to run twice: the second run mirrors nothing new, regenerates nothing new, and stages nothing
new, which it says out loud. That matters because the producers call it on every build, not once.

The tree-wide direction of check_build_inputs.py is printed too, as a note rather than a verdict. On
this tree one working copy is shared by every lane, so the tree-wide reading can be red for a source
another lane dropped and has not committed yet; that is not this caller's fault and must not fail
this caller's build. The staged pairing is the only direction a commit is judged by, which is why it
is the one that decides.

Not in scope here, deliberately: guard/lane_commit.py and the lane done step. Making the done step
call this would cover every lane at once, and that blast radius is Nayil's call, not this card's.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")

GITIGNORED = "gitignored"
CALLER = "caller"
GENERATED = "generated"


def run(command, cwd=ROOT):
    """One subprocess, text mode, no exceptions for a non-zero exit: the caller reads the code."""
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, errors="replace")


def git(*args, cwd=None):
    return run(["git"] + list(args), cwd=cwd or ROOT)


def repo_root() -> str:
    """The git worktree this project sits in.

    Not ROOT: the repository root is two levels up (Shared/), because several projects share one
    worktree and one index. Everything git is asked about here is asked with paths relative to that
    root, so a caller in any folder gets the same answer.
    """
    result = git("rev-parse", "--show-toplevel")
    if result.returncode != 0:
        raise SystemExit("land_asset: not inside a git worktree: " + result.stderr.strip())
    return os.path.abspath(result.stdout.strip())


def project_prefix(repo: str) -> str:
    """This project's folder, relative to the repository root, with forward slashes."""
    rel = os.path.relpath(ROOT, repo)
    return "" if rel == "." else rel.replace(os.sep, "/")


def status_digest(repo: str, prefix: str) -> dict[str, str]:
    """Every file under this project that differs from HEAD, hashed as it is on disk right now.

    The hash, not just the name, because this tree is shared: game/PrimordialParadox.yyp is already
    modified by another lane's run when this is called, so a name-only snapshot cannot tell "the
    regenerator rewrote this" from "it was already like that". -z so a path with a space survives,
    -uall so an untracked file inside an untracked folder is listed on its own.
    """
    out = git("status", "--porcelain", "-z", "-uall", "--", prefix or ".", cwd=repo).stdout
    tokens = out.split("\0")
    digest = {}
    index = 0
    while index < len(tokens):
        entry = tokens[index]
        index += 1
        if not entry:
            continue
        code, path = entry[:2], entry[3:]
        if code[0] in "RC" or code[1] in "RC":
            index += 1  # a rename or copy prints its original path as the next token
        full = os.path.join(repo, path)
        if code[1] in "D" or not os.path.isfile(full):
            digest[path] = "<deleted>"
            continue
        running = hashlib.sha256()
        with open(full, "rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                running.update(block)
        digest[path] = running.hexdigest()
    return digest


def staged_set(repo: str, prefix: str) -> set[str]:
    """Paths under this project whose staged content differs from HEAD."""
    out = git("diff", "--cached", "--name-only", "-z", "--", prefix or ".", cwd=repo).stdout
    return {path for path in out.split("\0") if path}


def project_paths(paths, repo: str) -> tuple[list[str], list[str], list[str]]:
    """Split the caller's arguments into repo-relative paths to stage, ignored ones, and refusals.

    A relative argument is read against the working directory and, if nothing is there, against the
    project root, because a build script usually passes a path it built from its own HERE while a
    person at a shell passes the one they just typed.
    """
    keep, ignored, refused = [], [], []
    prefix = project_prefix(repo) + "/"
    for raw in paths:
        candidate = raw if os.path.isabs(raw) else os.path.join(os.getcwd(), raw)
        if not os.path.exists(candidate):
            candidate = raw if os.path.isabs(raw) else os.path.join(ROOT, raw)
        if not os.path.exists(candidate):
            refused.append("%s (no such file)" % raw)
            continue
        full = os.path.abspath(candidate)
        rel = os.path.relpath(full, repo).replace(os.sep, "/")
        if prefix and not rel.startswith(prefix):
            refused.append("%s (outside %s)" % (rel, prefix.rstrip("/")))
            continue
        keep.append(rel)
    if keep:
        check = git("check-ignore", "--", *keep, cwd=repo)
        refused_names = {line.strip() for line in check.stdout.splitlines() if line.strip()}
        ignored = [name for name in keep if name in refused_names]
        keep = [name for name in keep if name not in refused_names]
    return keep, ignored, refused


def stage(repo: str, paths: list[str]) -> None:
    """git add -A on exactly these paths, so a file a mirror deleted is staged as a deletion."""
    if paths:
        git("add", "-A", "--", *paths, cwd=repo)


def generated_file(path: str, prefix: str) -> bool:
    """True for a file tools/gen_project.py owns: the .yyp and the .yy resources under game/.

    By extension and folder, because that is the rule the generator follows: it writes
    game/PrimordialParadox.yyp plus one .yy per script, object and room it finds on disk. Reading the
    generator's own path list would tie this module to its internals, and this module's job is to
    stage what a regeneration implies, not to reproduce how the regeneration was computed.
    """
    rel = path[len(prefix) + 1:] if prefix and path.startswith(prefix + "/") else path
    return rel.startswith("game/") and (rel.endswith(".yy") or rel.endswith(".yyp"))


STREAM_SRC = os.path.join(ROOT, "assets", "audio")
STREAM_DST = os.path.join(ROOT, "game", "datafiles", "streams")


def prune_mirror_streams() -> list[str]:
    """Delete a mirrored .ogg that no folder under assets/audio/ answers for.

    tools/sync_art.py copies every stream and has never removed one, and game/datafiles is what the
    .yyp lists as Included Files, so a deleted source keeps its stream in the build for good.
    Measured 2026-11-02: assets/audio/pp_04_navy_sailors_master2/ no longer existed, its .ogg was
    still in game/datafiles/streams, tools/gen_project.py therefore named it, and
    tools/check_build_inputs.py --staged refused every regenerated .yyp with "UNPAIRED IN COMMIT
    datafiles/streams/pp_04_navy_sailors_master2.ogg": no commit could answer that, because the
    source it wanted cannot be committed. The art mirror and mirror_sfx() both prune their build
    folder for exactly this reason; the streams are the one mirror that does not.

    That fix belongs in tools/sync_art.py, and it is not made there yet: the consequential-change
    gate classifies that file as a production script (its name carries sync_) and asks for a review
    reference before it can be committed, which is an approval this card does not carry. Until it is
    approved, the pruning sits here, on the landing path, so it runs for every producer that lands a
    stream through this script.
    """
    if not os.path.isdir(STREAM_DST):
        return []
    sources = set()
    for name in sorted(os.listdir(STREAM_SRC)):
        folder = os.path.join(STREAM_SRC, name)
        if not os.path.isdir(folder):
            continue
        for fname in sorted(os.listdir(folder)):
            if fname.endswith(".ogg") and os.path.isfile(os.path.join(folder, fname)):
                sources.add(fname)
    removed = []
    for fname in sorted(os.listdir(STREAM_DST)):
        if fname.endswith(".ogg") and fname not in sources:
            os.remove(os.path.join(STREAM_DST, fname))
            removed.append(fname)
    return removed


def land(paths, gate: bool = True) -> int:
    """Mirror, regenerate, stage, judge. Returns 0 when the staged pair passes the commit gate.

    1 the gate refused the pair, 2 a refusal before any work was done, 3 a mirror or generator run
    failed. A failure still stages what changed, because the half-landed tree is the state the next
    run has to start from anyway.
    """
    repo = repo_root()
    prefix = project_prefix(repo)
    callers, ignored, refused = project_paths(paths, repo)
    for line in refused:
        print("land_asset: refused %s" % line)
    if refused:
        return 2

    def shown(name: str) -> str:
        head = prefix + "/"
        return name[len(head):] if prefix and name.startswith(head) else name

    print("land_asset: %d caller path(s) under %s" % (len(callers), prefix or "the repository root"))
    for name in callers:
        print("  caller      %s" % shown(name))
    for name in ignored:
        print("  skipped     %s (gitignored, so a commit cannot carry it)" % shown(name))

    before = status_digest(repo, prefix)
    staged_before = staged_set(repo, prefix)
    stage(repo, callers)

    for fname in prune_mirror_streams():
        print("  prune       game/datafiles/streams/%s (no source under assets/audio)" % fname)

    codes = {}
    for label, script in (("sync_art", "sync_art.py"), ("gen_project", "gen_project.py")):
        result = run([sys.executable, os.path.join(TOOLS, script)])
        codes[label] = result.returncode
        for line in (result.stdout + result.stderr).splitlines():
            if line.strip():
                print("  %-11s %s" % (label, line))
        print("  %-11s exit %d" % (label, result.returncode))

    after = status_digest(repo, prefix)
    changed = sorted(name for name, digest in after.items() if before.get(name) != digest)
    # A project file that was already regenerated before this call is correct on disk and absent from
    # the index, and that shape refuses exactly like an unlanded stream does: the stream staged, the
    # .yyp not, "UNPAIRED IN COMMIT". gen_project has just run, so every .yy and .yyp under game/ on
    # disk is what the folders imply; the index has to carry it, whether or not this run wrote it.
    already_current = sorted(name for name in after
                             if generated_file(name, prefix) and name not in staged_before)
    stage(repo, changed + already_current)
    staged_after = staged_set(repo, prefix)
    newly = sorted(staged_after - staged_before)

    for name in changed:
        print("  generated %s" % shown(name))
    for name in already_current:
        if name not in changed:
            print("  regenerated %s (already current on disk, not in the index)" % shown(name))
    print("land_asset: %d file(s) staged for this project, %d new in this run"
          % (len(staged_after), len(newly)))
    if not newly:
        print("land_asset: nothing new: the mirror, the project and the index already agreed")

    if any(code != 0 for code in codes.values()):
        failed = [label for label, code in codes.items() if code != 0]
        print("land_asset: %s failed; the staged pair was not judged" % ", ".join(failed))
        return 3

    tree = run([sys.executable, os.path.join(TOOLS, "check_build_inputs.py")])
    if tree.returncode != 0:
        print("land_asset: note, the tree-wide reading is red (another lane's uncommitted source, or")
        print("            a mirror this call did not touch). It does not judge a commit; the")
        print("            staged pairing below does.")
        for line in tree.stdout.splitlines():
            if line.strip():
                print("  tree-wide   %s" % line)

    if not gate:
        return 0
    judged = run([sys.executable, os.path.join(TOOLS, "check_build_inputs.py"), "--staged"])
    for line in judged.stdout.splitlines():
        if line.strip():
            print("  staged      %s" % line)
    print("land_asset: check_build_inputs --staged exit %d" % judged.returncode)
    return 0 if judged.returncode == 0 else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print((__doc__ or "land_asset.py: land a card's build inputs.").strip())
        return 0 if args else 2
    return land(args)


if __name__ == "__main__":
    sys.exit(main())
