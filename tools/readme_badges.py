#!/usr/bin/env python3
"""readme_badges.py: the README's badge block, written by rerunning the gates it claims.

Card t_4f984c7b (SUB-KIT-FINAL), checklist item 5's companion. A badge a human types is a claim
about a moment that has already passed, and a judge has no way to tell last night's green from
this morning's red. So no badge here is typed: the block lives between two markers in README.md,
this tool runs every gate named in it, renders one SVG badge per gate into docs/badges/, and
rewrites only what sits between the markers. Text and picture come from the same run, which is
what makes a stale badge impossible rather than unlikely.

The four gates are the ones the submission checklist tells a reader to run:

    python tools\\check_data.py            the data files load and agree
    python tools\\check_cleanroom.py       no study reference, no foreign name, no foreign phrase
    python tools\\nes_audit_all.py         every asset and frame against the picture chip's limits
    python tools\\play_demo.py --check     the recorded take is the game, long enough and in step

A gate that exits 0 is PASS. Anything else is FAIL, and the badge says so: a red badge in the
block is a fact about the tree, not an error in the tool, and that is the whole point of writing
the block from a run instead of from memory. The output carries no timestamp and no absolute
path, so two runs on an unchanged tree write byte identical files, and `--verify` can compare the
README against a fresh run by plain equality.

Usage
    python tools\\readme_badges.py --write     run the gates, write docs\\badges\\*.svg and the README block
    python tools\\readme_badges.py --verify    run the gates and refuse when the README block is stale
    python tools\\readme_badges.py --list      print the gates and their commands, run nothing

Exit codes: 0 the block and the badges match this run, or were just written; 1 a gate disagrees
with the README, a badge file is missing or disagrees, or a marker is absent; 2 bad argument.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "README.md")
BADGE_DIR = "docs/badges"

START = "<!-- README-BADGES:START -->"
END = "<!-- README-BADGES:END -->"

GREY = (60, 63, 74)
PASS_C = (60, 150, 92)
FAIL_C = (186, 68, 68)
INK = (255, 255, 255)

DEFAULT_TIMEOUT = 900

# The gates, in the order the checklist runs them. The arguments are a repository relative tool
# and its own arguments, so the README line is printable and the same list is what gets executed.
GATES = [
    {"slug": "check_data", "tool": "tools/check_data.py", "args": [], "label": "check_data"},
    {"slug": "check_cleanroom", "tool": "tools/check_cleanroom.py", "args": [], "label": "check_cleanroom"},
    {"slug": "nes_audit_all", "tool": "tools/nes_audit_all.py", "args": [], "label": "nes_audit_all"},
    {"slug": "play_demo_check", "tool": "tools/play_demo.py", "args": ["--check"], "label": "play_demo --check"},
]


def command_text(gate):
    return " ".join(["python", gate["tool"]] + gate["args"])


def status_of(exit_code):
    if exit_code is None:
        return "TIMEOUT"
    return "PASS" if exit_code == 0 else "FAIL"


def run_gate(gate, root=ROOT, timeout=DEFAULT_TIMEOUT, python=None):
    """Run one gate and keep only what the block needs: its exit code and how long it took."""
    runner = python or sys.executable
    command = [runner, os.path.join(root, gate["tool"].replace("/", os.sep))] + list(gate["args"])
    started = time.time()
    try:
        # stdin=DEVNULL for the same reason check_readme gives: this tool is run by a commit gate
        # and by pytest, and an inherited handle is not a valid one there. Measured on the sibling
        # tool on 2026-10-26; a child that cannot start reads exactly like a failing gate.
        proc = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=timeout,
                              stdin=subprocess.DEVNULL)
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        exit_code = None
    except OSError:
        exit_code = None
    return {
        "slug": gate["slug"],
        "label": gate["label"],
        "command": command_text(gate),
        "exit": exit_code,
        "status": status_of(exit_code),
        "seconds": round(time.time() - started, 1),
    }


def run_all(root=ROOT, timeout=DEFAULT_TIMEOUT, python=None):
    return [run_gate(gate, root, timeout, python) for gate in GATES]


def render_badge(label, status):
    """One flat SVG badge: the gate name on the left, its verdict on the right.

    No timestamp and no absolute path: the file is a picture of this run's verdict, and the date
    of that run is the commit that carries it. Keeping it free of both is what lets `--verify`
    compare bytes instead of guessing what may legitimately differ.
    """
    colour = PASS_C if status == "PASS" else FAIL_C
    left = 8 + 7 * len(label)
    right = 14 + 7 * len(status)
    width = left + right
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" viewBox="0 0 {w} 20" '
        'font-family="Consolas, \'DejaVu Sans Mono\', monospace" font-size="11">'
        '<rect width="{left}" height="20" fill="rgb({gr},{gg},{gb})"/>'
        '<rect x="{left}" width="{right}" height="20" fill="rgb({r},{g0},{b})"/>'
        '<text x="4" y="14" fill="rgb({ir},{ig},{ib})">{label}</text>'
        '<text x="{tx}" y="14" fill="rgb({ir},{ig},{ib})">{status}</text>'
        "</svg>\n"
    ).format(
        w=width, left=left, right=right, tx=left + 7,
        gr=GREY[0], gg=GREY[1], gb=GREY[2],
        r=colour[0], g0=colour[1], b=colour[2],
        ir=INK[0], ig=INK[1], ib=INK[2],
        label=_esc(label), status=_esc(status),
    )


def _esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def badge_path(slug):
    """The badge's address in the README. Always forward slashes, whatever the host separator is.

    os.path.join would write docs\\badges\\check_data.svg on this machine, which check_readme accepts
    (it normalises) and markdown does not (a backslash is an escape), so the picture would be a link
    that never renders on the page a judge reads.
    """
    return BADGE_DIR + "/" + slug + ".svg"


def build_block(results):
    """The README region, from a run. Only what the run measured goes in it."""
    lines = [
        START,
        "",
        "| gate | badge | command | result |",
        "| --- | --- | --- | --- |",
    ]
    for result in results:
        lines.append("| %s | ![%s](%s) | `%s` | %s |" % (
            result["label"], result["label"], badge_path(result["slug"]),
            result["command"], result["status"]))
    lines.append("")
    lines.append("Written by `python tools/readme_badges.py --write`, which reruns every gate above and "
                 "renders the badges from that run; `python tools/readme_badges.py --verify` refuses a "
                 "README that disagrees with the tree.")
    lines.append(END)
    return "\n".join(lines)


def find_block(text):
    """The region between the markers, markers included, or None when either one is missing."""
    if START not in text or END not in text:
        return None
    start = text.index(START)
    end = text.index(END, start) + len(END)
    return text[start:end]


def parse_block(block):
    """Rows out of a block: label, command and the verdict the table claims."""
    rows = []
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("| ") or line.startswith("| gate ") or line.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        rows.append({"label": cells[0], "command": cells[2].strip("`"), "status": cells[3]})
    return rows


def replace_block(text, block):
    current = find_block(text)
    if current is None:
        return None
    return text.replace(current, block, 1)


def write_badges(results, root=ROOT):
    folder = os.path.join(root, BADGE_DIR.replace("/", os.sep))
    os.makedirs(folder, exist_ok=True)
    written = []
    for result in results:
        path = os.path.join(folder, result["slug"] + ".svg")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render_badge(result["label"], result["status"]))
        written.append(path)
    return written


def check_badges(results, root=ROOT):
    """Every badge file on disk must be the picture this run would draw."""
    problems = []
    for result in results:
        path = os.path.join(root, BADGE_DIR.replace("/", os.sep), result["slug"] + ".svg")
        if not os.path.exists(path):
            problems.append("%s is missing" % badge_path(result["slug"]))
            continue
        with open(path, encoding="utf-8") as fh:
            have = fh.read()
        want = render_badge(result["label"], result["status"])
        if have != want:
            problems.append("%s does not match this run" % badge_path(result["slug"]))
    return problems


def print_results(results):
    for result in results:
        print("   %-6s %-22s exit %-5s %6.1f s  %s" % (
            result["status"], result["label"],
            "none" if result["exit"] is None else str(result["exit"]),
            result["seconds"], result["command"]))
    passed = sum(1 for result in results if result["status"] == "PASS")
    print("readme_badges: %d gate(s), %d PASS, %d not PASS" % (len(results), passed, len(results) - passed))


def verify(root=ROOT, results=None, timeout=DEFAULT_TIMEOUT):
    path = os.path.join(root, "README.md")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    block = find_block(text)
    if block is None:
        print("readme_badges: README.md carries no %s / %s pair, so there is nothing to verify" % (START, END))
        return 1
    results = results if results is not None else run_all(root, timeout)
    problems = check_badges(results, root)
    want = parse_block(build_block(results))
    have = parse_block(block)
    if have != want:
        print("readme_badges: the README block is stale")
        by_label = {row["label"]: row for row in want}
        for row in have:
            current = by_label.get(row["label"])
            if current is None:
                print("   gone     %-22s the gate is no longer in the block" % row["label"])
            elif current["status"] != row["status"]:
                print("   %-8s %-22s README says %s, this run says %s" % (
                    "STALE", row["label"], row["status"], current["status"]))
    for problem in problems:
        print("readme_badges: %s" % problem)
    if have != want or problems:
        return 1
    print("readme_badges: the README block and every badge match this run")
    return 0


def write(root=ROOT, results=None, timeout=DEFAULT_TIMEOUT):
    path = os.path.join(root, "README.md")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if find_block(text) is None:
        print("readme_badges: README.md has no %s / %s pair to replace; add the two markers first" % (START, END))
        return 1
    results = results if results is not None else run_all(root, timeout)
    for result in results:
        print("   %-6s %-22s exit %s" % (
            result["status"], result["label"], "none" if result["exit"] is None else result["exit"]))
    written = write_badges(results, root)
    updated = replace_block(text, build_block(results))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(updated)
    print("readme_badges: wrote %d badge file(s) and the README block" % len(written))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Rewrite the README badge block by rerunning its gates.")
    parser.add_argument("--root", default=ROOT, help="repository root (default: this file's parent)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="per gate, in seconds")
    parser.add_argument("--write", action="store_true", help="run the gates, write the badges and the block")
    parser.add_argument("--verify", action="store_true", help="run the gates and refuse a stale block")
    parser.add_argument("--list", action="store_true", help="print the gates and run nothing")
    args = parser.parse_args(argv)

    if args.list:
        for gate in GATES:
            print("   %-22s %s" % (gate["label"], command_text(gate)))
        return 0
    chosen = [flag for flag, on in (("write", args.write), ("verify", args.verify)) if on]
    if len(chosen) != 1:
        print("readme_badges: pass exactly one of --write, --verify or --list")
        return 2

    if args.write:
        return write(args.root, timeout=args.timeout)
    results = run_all(args.root, args.timeout)
    print_results(results)
    return verify(args.root, results=results)


if __name__ == "__main__":
    sys.exit(main())
