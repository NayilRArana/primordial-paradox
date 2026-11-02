#!/usr/bin/env python
"""Check knowledge/RELEASE-CHECKLIST-2026-11-02.md (card t_e4276b12).

What it refuses:
  - a route row with no verdict, or a verdict outside the four the file defines;
  - a PASS, FAIL or TEST ONLY row whose evidence names a repository path that does not exist;
  - a NO EVIDENCE row that does not carry the words NO EVIDENCE.

It prints the count of rows by verdict and exits non zero if any row is refused.
Usage:  python tools/check_release_checklist.py knowledge/RELEASE-CHECKLIST-2026-11-02.md
"""
import os
import re
import sys

VERDICTS = ("PASS", "FAIL", "TEST ONLY", "NO EVIDENCE")
PREFIXES = ("data/", "game/", "tests/", "tools/", "output/", "build/", "knowledge/", "docs/")
TICKED = re.compile(r"`([^`]+)`")
LINE_SUFFIX = re.compile(r":(\d+)(?:-(\d+))?$")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def line_count(path):
    try:
        with open(path, "rb") as fh:
            return fh.read().count(b"\n") + 1
    except OSError:
        return 0



def rows(text):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 6:
            continue
        if not cells[0].isdigit():
            continue
        out.append(cells)
    return out


def main(path):
    text = open(path, encoding="utf-8").read()
    table = rows(text)
    problems = []
    counts = {v: 0 for v in VERDICTS}
    checked_paths = 0

    for num, step, _data, evidence, verdict, owner in table:
        if verdict not in VERDICTS:
            problems.append("row %s (%s): verdict %r is not one of %s" % (num, step, verdict, ", ".join(VERDICTS)))
            continue
        counts[verdict] += 1
        if verdict == "NO EVIDENCE":
            if "NO EVIDENCE" not in evidence:
                problems.append("row %s (%s): NO EVIDENCE verdict without the words in the evidence cell" % (num, step))
            continue
        found = 0
        for token in TICKED.findall(evidence):
            if not token.startswith(PREFIXES):
                continue
            m = LINE_SUFFIX.search(token)
            rel = LINE_SUFFIX.sub("", token)
            if any(ch in rel for ch in "*?["):
                continue
            found += 1
            checked_paths += 1
            full = os.path.join(ROOT, rel)
            if not os.path.exists(full):
                problems.append("row %s (%s): evidence path missing: %s" % (num, step, rel))
                continue
            if m:
                total_lines = line_count(full)
                for cited in (m.group(1), m.group(2)):
                    if cited and int(cited) > total_lines:
                        problems.append("row %s (%s): %s cites line %s, the file has %d"
                                        % (num, step, rel, cited, total_lines))
        if found == 0:
            problems.append("row %s (%s): %s row names no repository path" % (num, step, verdict))
        if not owner:
            problems.append("row %s (%s): no owner named" % (num, step))

    total = sum(counts.values())
    print("rows: %d" % total)
    if total != 15:
        problems.append("expected 15 rows (13 route steps plus music and the party), found %d" % total)
    for v in VERDICTS:
        print("  %-12s %d" % (v, counts[v]))
    print("paths checked: %d" % checked_paths)
    if problems:
        print("\nREFUSED (%d):" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1
    print("\nPASS: every row carries a verdict, every named path exists, every NO EVIDENCE row says so")
    return 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "knowledge/RELEASE-CHECKLIST-2026-11-02.md"
    sys.exit(main(target if os.path.isabs(target) else os.path.join(ROOT, target)))
