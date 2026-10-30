#!/usr/bin/env python3
r"""window_ledger.py: write WINDOW-LEDGER.md, the demo to commit map the hackathon rules ask for.

Why (card t_a1228645): the Meta Global AI Developer Hackathon FAQ says a project that existed
before the window may enter, but the submission and the demo "must clearly identify and only
showcase the features, code and functionality built during the hackathon", and unclear original
contributions can lead to disqualification (Abhay, FAQ thread, 2026-10-26 10:26 AM). This project
predates the window, so the defense is a repo where the pre-event tree is one tagged commit and
every later commit is event work, plus this page: one row per thing the demo shows, the commit
that landed it in the window, and what the baseline already had. A feature with no in-window
commit is named as an exposure instead of being quietly demoed.

The rows are the demo's own shots, taken from the cut document, so the check the cut is held to is
"every shot in the demo is covered by a row, and every row has a commit". `--cut` reads the shot
ids out of the cut document and fails on a shot nothing covers. `--check` fails when a row has no
in-window commit, when a commit does not resolve, or when the file on disk is stale.

Commit ids are this repository's. The private monorepo and the public export carry the same work
under different ids, because the export rewrites paths, so the header line names the baseline tag
and its commit here and every row is resolved from that same repository. Run it in the repository
whose ids you want to quote: `python tools/window_ledger.py --repo D:/repos/pp-public`.

Usage:
  python tools/window_ledger.py                      write WINDOW-LEDGER.md, print the row count
  python tools/window_ledger.py --check              write nothing: exit 1 when the file is stale
                                                     or a row has no in-window commit
  python tools/window_ledger.py --print              print the text, write nothing
  python tools/window_ledger.py --cut <path.md>      also require every shot in the cut to be covered
  python tools/window_ledger.py --repo <path>        resolve ids in that checkout instead of this one
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)
TAG = "hackathon-baseline-2026-10-25"
LONG_DASHES = {"\u2013": "-", "\u2014": "-", "\u2015": "-", "\u2212": "-"}
NOWIN = 0x08000000 if os.name == "nt" else 0
SHOT_ID = re.compile(r"^\|\s*([A-G][0-9])\s*\|", re.M)

# One row per thing the demo puts on screen, with the shots from the cut it appears in and the paths
# the feature lives in. A path ending in "/" is a folder, a path carrying "*" is a glob, anything
# else is a file. "showcase" is the subject pattern of the commits that landed the feature itself:
# the newest match is the commit quoted, so a row changes only when that feature moves again.
FEATURES = [
    {"id": "L1", "shots": "A4,B2,F1",
     "demo": "The attract and the title screen, PRESS START at 256 by 240",
     "paths": ["game/objects/obj_pp_title/", "game/scripts/pp_title/", "data/title.json",
               "data/title_timing.json", "data/title_flash.json", "data/intro_stars.json"],
     "showcase": r"ART-B-OPENING|INTRO-POLISH|^PP-TITLE"},
    {"id": "L2", "shots": "B3,B4",
     "demo": "The six crawl beats on a thirty character box, SOUTHAMPTON. OCTOBER.",
     "paths": ["data/intro_text.json", "game/scripts/pp_scene/", "game/scripts/pp_text/"],
     "showcase": r"PP-VOICE-1|INTRO-POLISH"},
    {"id": "L3", "shots": "B5",
     "demo": "The ship room loads and the route starts",
     "paths": ["game/rooms/rm_pp_ship/", "game/scripts/pp_overworld/", "data/slice.json",
               "data/maps/", "game/scripts/pp_map/"],
     "showcase": r"DEMO-ROUTE|SHIP-AREA|MAP-AUDIT"},
    {"id": "L4", "shots": "B6",
     "demo": "Eight steps of a free walk, hold to walk",
     "paths": ["game/scripts/pp_input/", "game/scripts/pp_overworld/", "game/scripts/pp_touch/"],
     "showcase": r"FREE-MOVE|WALK-INPUT|ANDROID-TOUCH"},
    {"id": "L5", "shots": "B7,C2",
     "demo": "Confirm opens the sailor's box: thirty characters a line, three lines, the spaces kept",
     "paths": ["game/scripts/pp_dialogue/", "game/scripts/pp_text/", "game/scripts/pp_battle_text/",
               "data/dialogue/"],
     "showcase": r"TEXT-BOX-FIX|SHIP-TALK|DIALOGUE|TALK-BOX"},
    {"id": "L6", "shots": "A1,A2,C1,C3,C4",
     "demo": "The TALK prompt, the same three lines every turn, and the WILL bar the answer moves",
     "paths": ["game/scripts/pp_talk_live/", "game/scripts/pp_battle_commands/",
               "game/scripts/pp_battle_director/", "data/talk_cards.json", "data/talk_live.json",
               "data/talk/", "data/meta_bake.json"],
     "showcase": r"LIVE-TALK|TALK-BUDGET|TALK-CACHE|BAKE-REBAKE|TALK-REPLAY|META-LIVE"},
    {"id": "L7", "shots": "A3,C5,C6,C7",
     "demo": "The reply board, the third talk, and SPARE at full health",
     "paths": ["game/scripts/pp_battle_commands/", "game/scripts/pp_battle_director/",
               "data/talk_cards.json", "data/enemies/", "game/scripts/pp_talk_live/"],
     "showcase": r"PP-VOICE|BATTLE-DEMO-FIX|SPARE|BAKE-OVERLAY"},
    {"id": "L8", "shots": "D1,D2,D3",
     "demo": "The checker refusing a model frame, then passing the quantised one",
     "paths": ["tools/nes_check.py", "game/scripts/pp_nes_check.py", "tests/test_nes_check.py",
               "tools/nes_audit_all.py"],
     "showcase": r"NES-CHECK|CONTROLS-THAT-FAIL|controls can fail"},
    {"id": "L9", "shots": "D4",
     "demo": "The quantiser's own verdict: legal is not good",
     "paths": ["tools/quantize_concept.py", "tests/test_quantize_concept.py"],
     "showcase": r"QUANTIZE"},
    {"id": "L10", "shots": "E1,E2,E3",
     "demo": "The Muse Image concept, the SAM 3.1 cut, and the cache count",
     "paths": ["tools/meta_client.py", "tools/meta_art.py", "tools/meta_spend_ledger.py",
               "data/ai_cache/", "knowledge/meta_art_reference/", "knowledge/META-SPEND.md"],
     "showcase": r"META-ART-1|META-LIVE|META-SPEND|META-ART"},
    {"id": "L11", "shots": "",
     "demo": "The cues under the cut (PP-01, PP-04, PP-05) and the mix bed",
     "paths": ["data/audio.json", "data/audio_cues_source.json", "game/datafiles/streams/",
               "tools/demo_bed.py", "tools/final_mix.py", "data/audio/"],
     "showcase": r"SCORE-FINAL|BAROQUE-CUES|AUDIO-STATES|DEMO-BED|CUE"},
    {"id": "L12", "shots": "F1,G1,G2",
     "demo": "How it was built: one person, agent roles, and a checker that says no",
     "paths": ["BUILT-WITH-AGENTS.md", "README.md", "HACKATHON.md", "EVENT-LOG.md",
               "tools/event_log.py", "tools/window_ledger.py", "tests/"],
     "showcase": r"BUILT-WITH-AGENTS|EVENT-LOG|^SUB-KIT"},
    {"id": "L13", "shots": "B1",
     "demo": "The frame itself: 256 by 240, every colour a 2C02 output",
     "paths": ["tools/check_runtime_palette.py", "tests/test_runtime_palette.py",
               "data/palette_ppu.json", "game/scripts/pp_look/", "game/scripts/pp_camera/",
               "game/scripts/pp_data/"],
     "showcase": r"RUNTIME-PALETTE|PALETTE-REPORT|NES-AUDIT"},
]


def plain(text):
    """The repo's writing rule: a long dash never reaches the page."""
    for bad, good in LONG_DASHES.items():
        text = text.replace(bad, good)
    return text.strip()


def git(args, cwd):
    """Run one git command in cwd and return stdout, or raise with git's own message.

    The GIT_* variables that point git at another index or object store are dropped: a pre-commit
    hook or another lane's shell exports them, and a ledger read from a redirected index describes a
    tree nobody checked out. stdin is closed for the reason knowledge/SPAWN-HANDLES-2026-10-25.md
    measured: a dead parent handle fails the spawn before git runs at all.
    """
    env = {k: v for k, v in os.environ.items()
           if k not in ("GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR",
                        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES")}
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, encoding="utf-8",
                          errors="replace", env=env, creationflags=NOWIN, stdin=subprocess.DEVNULL)
    if proc.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), (proc.stderr or "").strip()[:400]))
    return proc.stdout


def project_path(repo):
    """The project's own path inside its repository, as a pathspec git reads from the root.

    Asked of git, not written down: Shared carries the project at projects/primordial-paradox, and
    the export and the local window repo carry it at the root, where the path is ".". A hardcoded
    prefix matched nothing in the export (the same trap card t_43904993 fixed in event_log.py).
    """
    try:
        root = git(["rev-parse", "--show-toplevel"], cwd=repo).strip()
    except (RuntimeError, OSError):
        return "projects/primordial-paradox"
    return os.path.relpath(repo, root).replace(os.sep, "/")


def matches(path, patterns):
    """Does this project path belong to the feature: a folder, a glob within one level, or a file.

    The glob is read the way a pathspec reads it, so `data/maps/*.json` covers the files directly in
    data/maps and not data/maps/osm/quay.json. fnmatch alone crosses the separator, and a row that
    silently swallowed a nested tree is a row whose commit count nobody can check.
    """
    for pattern in patterns:
        if pattern.endswith("/"):
            if path.startswith(pattern):
                return True
        elif any(ch in pattern for ch in "*?["):
            rx = re.escape(pattern).replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
            if re.fullmatch(rx, path):
                return True
        elif path == pattern or path.startswith(pattern + "/"):
            return True
    return False


def parse_log(raw):
    """Turn `git log --format=... --name-only` output into commits with their files.

    Each commit is one header line of three NUL separated fields (sha, date, subject) followed by
    one path per line. A path never carries a NUL, so no subject and no path can be merged.
    """
    commits, current = [], None
    for line in raw.splitlines():
        if "\x00" in line:
            fields = line.split("\x00")
            if len(fields) < 3:
                raise ValueError("header with %d field(s): %r" % (len(fields), line[:120]))
            current = {"sha": plain(fields[0]), "when": plain(fields[1]),
                       "subject": plain(fields[2]), "files": []}
            commits.append(current)
        elif line.strip() and current is not None:
            current["files"].append(line.strip())
    return commits


def collect(repo):
    root = git(["rev-parse", "--show-toplevel"], cwd=repo).strip()
    project = project_path(repo)
    tag_sha = git(["rev-parse", "--short=7", TAG + "^{commit}"], cwd=root).strip()
    tag_when = git(["log", "-1", "--format=%cd", "--date=format-local:%Y-%m-%d %H:%M",
                    TAG + "^{commit}"], cwd=root).strip()
    raw = git(["log", "--reverse", "--abbrev=7", "--date=format-local:%Y-%m-%d %H:%M",
               "--format=%h%x00%cd%x00%s", TAG + "..HEAD", "--name-only", "--", project], cwd=root)
    commits = parse_log(raw)
    if project != ".":
        cut = project + "/"
        for commit in commits:
            commit["files"] = [f[len(cut):] if f.startswith(cut) else f for f in commit["files"]]
    baseline = set()
    for line in git(["ls-tree", "-r", "--name-only", TAG], cwd=root).splitlines():
        path = line.strip()
        if project != ".":
            if not path.startswith(project + "/"):
                continue
            path = path[len(project) + 1:]
        baseline.add(path)
    head = set()
    for line in git(["ls-tree", "-r", "--name-only", "HEAD"], cwd=root).splitlines():
        path = line.strip()
        if project != ".":
            if not path.startswith(project + "/"):
                continue
            path = path[len(project) + 1:]
        head.add(path)
    return {"root": root, "project": project, "tag_sha": tag_sha, "tag_when": tag_when,
            "commits": commits, "baseline": baseline, "head": head}


def resolve(feature, commits, baseline_set, head_set):
    """The commit that landed this feature in the window, and whether the baseline had it.

    Two answers per row. The commit is the newest in-window commit whose subject names the feature
    and which touches one of its paths; when no subject matches, the newest commit touching a path
    is quoted and the row says so, because a path was moved by something else. The baseline answer
    is read off two trees, the tagged one and HEAD: a path in the tagged tree was already there, and
    a path in HEAD but not in the tag was added in the window.
    """
    touching = [c for c in reversed(commits) if any(matches(f, feature["paths"]) for f in c["files"])]
    rx = re.compile(feature["showcase"], re.I) if feature["showcase"] else None
    named = [c for c in touching if rx and rx.search(c["subject"])]
    chosen = named[0] if named else (touching[0] if touching else None)
    baseline_hits = sorted(p for p in baseline_set if matches(p, feature["paths"]))
    new_paths = sorted(p for p in head_set if matches(p, feature["paths"]) and p not in baseline_set)
    return {"commit": chosen, "named": bool(named), "touching": len(touching),
            "baseline": baseline_hits, "new_paths": new_paths}


def short(subject, limit=110):
    subject = re.sub(r"\s+", " ", subject).strip()
    return subject if len(subject) <= limit else subject[:limit - 3].rstrip() + "..."


def names(paths, show=2):
    """Paths the way a reader needs them: a folder with many files in it is one entry.

    A row that names 370 cached answers is unreadable, and the count is the fact worth keeping, so
    files that share a parent folder are collapsed to `folder/ (N files)` and only a folder with one
    or two files in it is spelled out.
    """
    groups = {}
    for path in paths:
        parent = path.rsplit("/", 1)[0] + "/" if "/" in path else ""
        groups.setdefault(parent, []).append(path)
    entries = []
    for parent, members in groups.items():
        if parent and len(members) > 2:
            entries.append("`%s` (%d files)" % (parent, len(members)))
        else:
            entries.extend("`%s`" % p for p in members)
    picked = ", ".join(entries[:show])
    return picked if len(entries) <= show else "%s and %d more" % (picked, len(entries) - show)


def render(data, rows):
    head = ("WINDOW-LEDGER. What the demo shows, and the commit in this repository that built it. "
            "Baseline tag %s at %s (%s local): everything in that commit existed before the hackathon "
            "window, and every commit after it is event work. Commit ids are this repository's, "
            "resolved from the tagged tree at generation time. Generated by "
            "python tools/window_ledger.py; run it with --cut <the cut document> to hold every shot "
            "in the cut to a row." %
            (TAG, data["tag_sha"], data["tag_when"]))
    out = [plain(head), ""]
    out.append("| Row | What the demo shows (shots) | In-window commit | Landed | What that commit did "
               "| At the baseline tag |")
    out.append("| --- | --- | --- | --- | --- | --- |")
    for feature, row in rows:
        commit = row["commit"]
        sha = ("`" + commit["sha"] + "`") if commit else "NONE"
        when = commit["when"] if commit else ""
        what = short(commit["subject"]) if commit else "no in-window commit touches this"
        if commit and not row["named"]:
            what += " (newest commit touching these paths, its subject does not name the feature)"
        known, added = row["baseline"], row["new_paths"]
        parts = []
        if known:
            parts.append("had " + names(known))
        if added:
            parts.append("the window added " + names(added))
        base = "; ".join(parts) if parts else "nothing at either tree"
        shots = feature["shots"] or "audio under A to F"
        out.append("| %s | %s (%s) | %s | %s | %s | %s |" %
                   (feature["id"], plain(feature["demo"]), shots, sha, when, plain(what), base))
    out.append("")
    missing = [(f, r) for f, r in rows if not r["commit"]]
    by_path = [(f, r) for f, r in rows if r["commit"] and not r["named"]]
    if missing:
        out.append("## Exposures: no in-window commit")
        out.append("")
        for feature, _ in missing:
            out.append("- %s %s: nothing landed this in the window. Cut it from the demo or say "
                       "plainly that it is baseline work." % (feature["id"], plain(feature["demo"])))
        out.append("")
    if by_path:
        out.append("## Read before demoing: mapped by path, not by name")
        out.append("")
        out.append("These rows have a commit, and that commit touches the feature's files without "
                   "naming the feature. The feature itself is baseline work: a shot of it shows "
                   "pre-window behaviour, so the cut either labels it as the baseline or leaves it out.")
        out.append("")
        for feature, row in by_path:
            out.append("- %s %s: `%s` %s" % (feature["id"], plain(feature["demo"]),
                                             row["commit"]["sha"], plain(short(row["commit"]["subject"], 90))))
        out.append("")
    if not missing and not by_path:
        out.append("Every row is named by an in-window commit's own subject, so every shot in the "
                   "cut is work that landed during the event. Nothing else is in the demo.")
        out.append("")
    out.append("Baseline work is identified, never claimed: the tagged commit is the whole of it, "
               "and a shot counts as window work only when the commit beside its row is what the "
               "shot shows.")
    return "\n".join(out) + "\n"


def parse_cut_shots(path):
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        raise RuntimeError("cannot read the cut document %s: %s" % (path, exc))
    return sorted(set(SHOT_ID.findall(text)))


def coverage(cut_shots, rows):
    """Every shot in the cut is covered by a row, and every row has a commit."""
    covered = {}
    for feature, _ in rows:
        for shot in (feature["shots"] or "").split(","):
            if shot.strip():
                covered.setdefault(shot.strip(), feature["id"])
    uncovered = [s for s in cut_shots if s not in covered]
    return covered, uncovered


def main(argv=None):
    parser = argparse.ArgumentParser(description="Write WINDOW-LEDGER.md: the demo to commit map.")
    parser.add_argument("--check", action="store_true", help="exit 1 when stale or a row has no commit")
    parser.add_argument("--print", dest="show", action="store_true", help="print the text, write nothing")
    parser.add_argument("--cut", help="cut document whose shot ids must all be covered")
    parser.add_argument("--repo", default=REPO, help="checkout to resolve commit ids in")
    args = parser.parse_args(argv)

    global data
    try:
        data = collect(args.repo)
    except (RuntimeError, OSError, ValueError) as exc:
        print("window_ledger: %s" % exc)
        return 2

    rows = [(feature, resolve(feature, data["commits"], data["baseline"], data["head"]))
            for feature in FEATURES]
    text = render(data, rows)
    out_path = os.path.join(REPO, "WINDOW-LEDGER.md")

    problems, notes = [], []
    for feature, row in rows:
        if not row["commit"]:
            problems.append("%s has no in-window commit" % feature["id"])
        elif not row["named"]:
            notes.append("%s is mapped by path only (%s), no commit subject names it" %
                         (feature["id"], row["commit"]["sha"]))
    if args.cut:
        try:
            shots = parse_cut_shots(args.cut)
        except RuntimeError as exc:
            print("window_ledger: %s" % exc)
            return 2
        covered, uncovered = coverage(shots, rows)
        if uncovered:
            problems.append("shot(s) %s are in the cut and in no ledger row" % ", ".join(uncovered))
        print("window_ledger: %d shot(s) in the cut, %d covered" % (len(shots), len(covered)))

    if args.show:
        print(text, end="")
        return 0 if not problems else 1
    if args.check:
        try:
            with open(out_path, encoding="utf-8") as handle:
                on_disk = handle.read()
        except OSError:
            on_disk = None
        disk_tag = re.search(r"Baseline tag \S+ at ([0-9a-f]{7})", on_disk or "")
        if on_disk is not None and disk_tag and disk_tag.group(1) != data["tag_sha"]:
            # The same work has different ids in the private monorepo and in the export, because the
            # export rewrites paths. A file written in one namespace is not stale in the other, and
            # rewriting it here would replace the ids a judge can actually resolve with ids it cannot.
            print("window_ledger: WINDOW-LEDGER.md was written in another hash namespace (baseline "
                  "%s there, %s here), so it is not checked here" % (disk_tag.group(1), data["tag_sha"]))
        elif on_disk != text:
            problems.append("WINDOW-LEDGER.md is stale, run python tools/window_ledger.py")
        if problems:
            for problem in problems:
                print("window_ledger: %s" % problem)
            return 1
        for note in notes:
            print("window_ledger: note: %s" % note)
        print("window_ledger: %d row(s), every row has an in-window commit" % len(rows))
        return 0

    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("window_ledger: WINDOW-LEDGER.md %d row(s), baseline %s" % (len(rows), data["tag_sha"]))
    for feature, row in rows:
        print("  %s %s -> %s" % (feature["id"], feature["shots"] or "audio",
                                 row["commit"]["sha"] if row["commit"] else "NONE"))
    for note in notes:
        print("window_ledger: note: %s" % note)
    for problem in problems:
        print("window_ledger: %s" % problem)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
