r"""Whole-history privacy sweep of the PUBLIC repo (card t_0428107f, 2026-11-02).

The publisher (manager\tools\publish_pp.py) gates the commits a push would SEND. That gate is right
for a push and is not a statement about the repository: once a commit is on GitHub it stays in the
history, and a reader can ask any commit for any file. This tool answers the other question: is
anything private in the WHOLE history, and in the final tree, of a fresh clone?

It imports the publisher's own rule sets instead of copying them, so a rule widened there cannot be
narrower here:
  publish_pp.push_gate          both rule sets, over the files one commit changes
  publish_pp.private_findings   the PRIVATE patterns, the uncredited-email rule, the name rule
  publish_pp.read_names         the name list under Private\publish, read and never printed
  publish_pp.name_matcher       the whole-word matcher the gate builds from that list
  guard\leak_scan.py            the credential shapes (scan_rev, scan_lines)

Three passes, because each proves something the others do not:
  1. every commit reachable from HEAD, through publish_pp.push_gate, handed the full rev-list (the
     publisher gate's own code path, with the whole history as its input instead of a push range);
  2. the final tree, every path at HEAD, through the same two rule sets;
  3. a blob census: every distinct blob reachable from HEAD, read once and put through both rule
     sets. This is the completeness proof for 1 and 2. Every blob a commit ever carried is
     reachable from HEAD, so a census that reads all of them cannot miss a file because a diff or a
     revision was read wrong, and it reports what neither rule set reads (an extension gap).

What it prints: the path, the line and the rule name. Never the matched text: a leak report that
repeats the leak is a second leak, and this output lands in a terminal, a log and a card comment.

Usage:
  python tools/sweep_public_history.py --clone D:\Temp\pp-sweep-clone-20261102-1502
  python tools/sweep_public_history.py --clone ... --json output/privacy_sweep_2026-11-02.json

Exit 0 clean, 1 any finding, 2 a rule that could not run (which is never a pass).
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# <shared>\projects\primordial-paradox\tools -> <shared>\projects\arananet\manager\tools
MANAGER_TOOLS = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir, "arananet", "manager", "tools"))
DEFAULT_CLONE = r"D:\Temp\pp-sweep-clone-20261102-1502"
CHUNK = 250  # blobs per `git cat-file --batch` call


def load_module(name, path):
    """Import a module from an absolute path, or stop with exit 2: a rule that cannot load is not a pass."""
    if not os.path.isfile(path):
        raise SystemExit("cannot run: no module at %s" % path)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit("cannot run: %s is not importable" % path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo, *args):
    """One git call in repo. A failure stops the sweep: silence here would read as a clean result."""
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True, stdin=subprocess.DEVNULL)
    if proc.returncode != 0:
        raise SystemExit("git %s failed in %s: %s"
                         % (" ".join(args[:3]), repo, proc.stderr.decode("utf-8", "replace").strip()[:300]))
    return proc.stdout.decode("utf-8", "replace").strip()


def object_types(repo, shas):
    """{sha: type} for a list of object ids, in one call."""
    if not shas:
        return {}
    proc = subprocess.run(["git", "-C", repo, "cat-file", "--batch-check"],
                          input=("\n".join(shas) + "\n").encode("utf-8"), capture_output=True)
    if proc.returncode != 0:
        raise SystemExit("git cat-file --batch-check failed in %s: %s"
                         % (repo, proc.stderr.decode("utf-8", "replace").strip()[:300]))
    kinds = {}
    for line in proc.stdout.decode("utf-8", "replace").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] in ("blob", "tree", "commit", "tag"):
            kinds[parts[0]] = parts[1]
    return kinds


def read_objects(repo, shas):
    """{sha: bytes} for a list of blob ids, chunked so a big history does not sit in one buffer."""
    got = {}
    for start in range(0, len(shas), CHUNK):
        chunk = shas[start:start + CHUNK]
        proc = subprocess.run(["git", "-C", repo, "cat-file", "--batch"],
                              input=("\n".join(chunk) + "\n").encode("utf-8"), capture_output=True)
        if proc.returncode != 0:
            raise SystemExit("git cat-file --batch failed in %s: %s"
                             % (repo, proc.stderr.decode("utf-8", "replace").strip()[:300]))
        data, pos = proc.stdout, 0
        for sha in chunk:
            nl = data.find(b"\n", pos)
            if nl < 0:
                break
            parts = data[pos:nl].split(b" ")
            pos = nl + 1
            if len(parts) < 3:
                continue
            try:
                size = int(parts[2])
            except ValueError:
                continue
            got[sha] = data[pos:pos + size]
            pos += size + 1
    return got


def as_line(finding):
    path, line, rule = finding
    return "%s:%s [%s]" % (path, line, rule) if line else "%s [%s]" % (path, rule)


def scan_tree(pp, leak_scan_path, repo, rev, matcher):
    """Pass 2: every path in one revision's tree, both rule sets. Returns (findings, files, read)."""
    paths = [p for p in git(repo, "ls-tree", "-r", "--name-only", rev).splitlines() if p]
    findings = list(pp.leak_scan_findings(repo, rev, paths, leak_scan_path))
    blobs = pp.read_blobs(repo, rev, paths)
    for path, text in blobs.items():
        findings.extend(pp.private_findings(path, text, matcher))
    return findings, paths, blobs


def census(pp, leak_scan, repo, matcher):
    """Pass 3: every distinct blob reachable from HEAD, both rule sets, deduped by content id.

    Returns a dict with the findings, the blob counts, which PRIVATE alternative fired per finding,
    and the paths neither rule set reads.
    """
    listing = [ln for ln in git(repo, "rev-list", "--objects", "HEAD").splitlines() if ln]
    first_path = {}
    ids = []
    for entry in listing:
        parts = entry.split(" ", 1)
        sha = parts[0]
        if sha in first_path:
            continue
        first_path[sha] = parts[1] if len(parts) > 1 else ""
        ids.append(sha)
    kinds = object_types(repo, ids)
    blobs = [sha for sha in ids if kinds.get(sha) == "blob"]
    findings = []
    read_private = read_keys = read_any = 0
    unread_by_rule = []
    alternatives = {}
    for sha, raw in read_objects(repo, blobs).items():
        path = first_path.get(sha, sha)
        norm = path.replace("\\", "/")
        ext = os.path.splitext(norm)[1].lower()
        size = len(raw)
        private_here = ext in pp.TEXT_EXT and size <= pp.MAX_BYTES
        keys_here = (ext in leak_scan.TEXT_EXT and size <= leak_scan.MAX
                     and not leak_scan.skipped_by_dirs(norm)
                     and not leak_scan.skipped_by_allowlist(norm))
        if private_here or keys_here:
            read_any += 1
        else:
            unread_by_rule.append(path)
            continue
        text = raw.decode("utf-8", "ignore")
        if keys_here:
            read_keys += 1
            if leak_scan.CRED_NAMED.search(norm):
                findings.append((path, 0, "credential-named file (not opened)"))
            else:
                leak_scan.scan_lines(path, text.splitlines(), findings)
        if private_here:
            read_private += 1
            fresh = pp.private_findings(path, text, matcher)
            findings.extend(fresh)
            # Which alternative of a rule fired, for the report: derived from the same line and the
            # same patterns, never from the matched text.
            lines = None
            for _p, line_no, rule in fresh:
                if rule.startswith("email"):
                    key = "email not credited"
                elif rule == "personal name":
                    key = "personal name"
                else:
                    if lines is None:
                        lines = text.splitlines()
                    line = lines[line_no - 1][:4000] if 0 < line_no <= len(lines) else ""
                    key = rule
                    for index, (name, rx) in enumerate(pp.PRIVATE):
                        if name == rule and rx.search(line):
                            key = "%s #%d" % (rule, index)
                            break
                alternatives[key] = alternatives.get(key, 0) + 1
    return {"findings": findings, "blobs": len(blobs), "read_any": read_any,
            "read_private": read_private, "read_keys": read_keys,
            "unread_by_rule": sorted(unread_by_rule), "alternatives": alternatives}


def rule_counts(findings):
    counts = {}
    for item in findings:
        rule = item["rule"] if isinstance(item, dict) else item[2]
        counts[rule] = counts.get(rule, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def main(argv=None):
    ap = argparse.ArgumentParser(description="sweep a fresh public clone: whole history plus final tree")
    ap.add_argument("--clone", default=DEFAULT_CLONE, help="a fresh git clone of the public repo")
    ap.add_argument("--rev", default="HEAD", help="the revision the history ends at (default HEAD)")
    ap.add_argument("--names-file", help="the name list (default: publish_pp.NAMES_FILE)")
    ap.add_argument("--leak-scan", help="guard\\leak_scan.py (default: publish_pp.LEAK_SCAN)")
    ap.add_argument("--json", help="write the full result to this path")
    ap.add_argument("--skip-history", action="store_true",
                    help="skip pass 1 (the per-commit gate); the census still covers every blob")
    a = ap.parse_args(argv)

    repo = os.path.abspath(a.clone)
    if not os.path.isdir(os.path.join(repo, ".git")):
        raise SystemExit("cannot run: %s is not a git clone (no .git)" % repo)
    pp = load_module("publish_pp", os.path.join(MANAGER_TOOLS, "publish_pp.py"))
    leak_scan_path = a.leak_scan or pp.LEAK_SCAN
    leak_scan = load_module("leak_scan", leak_scan_path)
    names_file = a.names_file or pp.NAMES_FILE

    # Fail closed, as the push gate does: without the name list the name rule cannot fire, and a rule
    # that cannot fire is not a rule that passed.
    names = pp.read_names(names_file)
    if not names:
        raise SystemExit("cannot run: no name list at %s; the name rule would be unmeasured" % names_file)
    matcher = pp.name_matcher(names)

    head = git(repo, "rev-parse", a.rev)
    commits = [c for c in git(repo, "rev-list", "--reverse", a.rev).splitlines() if c]
    print("sweep: clone %s" % repo)
    print("sweep: HEAD %s, %d commit(s) reachable, name list %d entries from %s (as whole words, %d or more letters)"
          % (head, len(commits), len(names), os.path.basename(names_file), pp.NAME_MIN_LETTERS))

    findings_history = []
    if a.skip_history:
        print("sweep: pass 1 SKIPPED by request; the blob census still covers every file of every commit")
    else:
        print("sweep: pass 1, publish_pp.push_gate over the full rev-list")
        findings_history = pp.push_gate(repo, commits, leak_scan=leak_scan_path,
                                        names_file=names_file, verbose=False)

    print("sweep: pass 2, the final tree at %s" % head[:12])
    findings_tree, tree_paths, tree_read = scan_tree(pp, leak_scan_path, repo, a.rev, matcher)

    print("sweep: pass 3, blob census over every object reachable from %s" % head[:12])
    cen = census(pp, leak_scan, repo, matcher)

    combined = {}
    for source, findings in (("history", findings_history), ("tree", findings_tree),
                             ("census", cen["findings"])):
        for finding in findings:
            entry = combined.setdefault((finding[0], finding[1], finding[2]),
                                        {"path": finding[0], "line": finding[1], "rule": finding[2],
                                         "in_history": False, "in_tree": False, "in_census": False})
            entry["in_" + source] = True
    merged = sorted(combined.values(), key=lambda f: (f["path"], f["line"], f["rule"]))

    print("")
    for finding in merged:
        print("REFUSE %s" % as_line((finding["path"], finding["line"], finding["rule"])))
    ext_gap = {}
    for path in cen["unread_by_rule"]:
        ext = os.path.splitext(path)[1].lower() or "(none)"
        ext_gap[ext] = ext_gap.get(ext, 0) + 1
    print("")
    print("sweep: neither rule set reads %d blob(s) by extension: %s"
          % (sum(ext_gap.values()), ", ".join("%s x%d" % (k, v) for k, v in sorted(ext_gap.items())) or "none"))
    print("sweep: rule counts (deduped over the three passes): %s"
          % (", ".join("%s x%d" % (k, v) for k, v in rule_counts(merged).items()) or "none"))
    at_head = [f for f in merged if f["in_tree"]]
    print("sweep: %d of %d distinct finding(s) are still in the final tree at %s; %d are history only"
          % (len(at_head), len(merged), head[:12], len(merged) - len(at_head)))
    print("sweep: which pattern fired (census lines): %s"
          % (", ".join("%s x%d" % (k, v) for k, v in sorted(cen["alternatives"].items())) or "none"))

    result = {
        "clone": repo,
        "head": head,
        "commits": len(commits),
        "commits_oldest": git(repo, "log", "--reverse", "--format=%aI", a.rev).splitlines()[0],
        "commits_newest": git(repo, "log", "-1", "--format=%aI", a.rev),
        "tree_files": len(tree_paths),
        "tree_files_read": len(tree_read),
        "blobs_reachable": cen["blobs"],
        "blobs_read_any_rule": cen["read_any"],
        "blobs_read_private": cen["read_private"],
        "blobs_read_keys": cen["read_keys"],
        "unread_by_rule": cen["unread_by_rule"],
        "names_entries": len(names),
        "findings_history": len(findings_history),
        "findings_tree": len(findings_tree),
        "findings_census": len(cen["findings"]),
        "findings_distinct": len(merged),
        "findings_at_head": len(at_head),
        "by_rule": rule_counts(merged),
        "by_alternative": cen["alternatives"],
        "findings": merged,
    }
    if a.json:
        out = os.path.abspath(a.json)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(result, fh, indent=1, sort_keys=True)
            fh.write("\n")
        print("sweep: wrote %s" % out)

    verdict = "CLEAN" if not merged else "FINDINGS"
    print("SWEEP SUMMARY: commits %d | tree files %d | blobs reachable %d (read %d, unread by rule %d) | "
          "findings history %d, tree %d, census %d, distinct %d | by rule %s | VERDICT %s"
          % (len(commits), len(tree_paths), cen["blobs"], cen["read_any"], len(cen["unread_by_rule"]),
             len(findings_history), len(findings_tree), len(cen["findings"]), len(merged),
             " ".join("%s=%d" % (k, v) for k, v in rule_counts(merged).items()) or "none", verdict))
    return 0 if not merged else 1


if __name__ == "__main__":
    sys.exit(main())
