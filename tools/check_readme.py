#!/usr/bin/env python3
"""check_readme.py: prove that the README's commands run and its paths exist.

Card t_99a4a385 (H4 SUBMIT-KIT). The README is the page a judge reads first, so it is the one page
that must not be aspirational. This checker holds it to three things, and prints every row:

1. PATHS. Every repository path the README names in a code span or a relative link exists on disk.
   A path that is named because a gate printed it, but is not a working tree path (the
   `datafiles/streams/...` entries live inside the GameMaker project file), is listed in EXEMPT with
   the reason beside it and printed as an exemption on every run, so nothing is skipped silently.
2. COMMANDS. Every command the README tells a reader to run names a script that exists, or a module
   this interpreter can import.
3. PASTED EXIT CODES. The block of gate results pasted into the README carries an exit code per
   tool. With `--run` this executes each one and compares, so the pasted number cannot go stale
   without the checker saying so. Without `--run` it only lists what it would run.
4. DASHES. Zero U+2012, U+2013, U+2014 or U+2015 in the file. The project's house rule is no long
   dash punctuation anywhere a reader sees it.

Usage
    python tools\\check_readme.py                 paths, commands, dashes, no execution
    python tools\\check_readme.py --run           also run the pasted gate block and compare exits
    python tools\\check_readme.py --counts        re-read the inventory table's numbers from disk
    python tools\\check_readme.py --readme X      check another file (default README.md at the root)

Exit codes: 0 everything checked holds, 1 a path is missing, a command names a file that is not
there, a pasted exit code disagrees with the real one, or a long dash is present, 2 bad argument.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

KNOWN_ROOTS = {
    "specs", "game", "data", "tools", "tests", "knowledge", "output", "docs", "assets", "build",
}
ROOT_FILES = {
    "README.md", "LICENSE-OPTIONS.md", "LICENCE", "LICENSE", "CREDITS.md", "EVENT-LOG.md",
    "DEVLOG.md", "PLAN.md", "pytest.ini", "ROADMAP-2026-10-24.md",
}

# Named in the README because a gate printed them, not because they are working tree paths.
EXEMPT = {
    "datafiles/streams/percy_theme_v3.ogg":
        "a path inside game/PrimordialParadox.yyp, quoted from check_build_inputs.py output",
    # README.md names this folder as the reference Meta run (META-ART-1, card t_9332fe42). The run
    # writes it under output/, which .gitignore line 28 keeps out of git, so a checkout never holds
    # it and the test that runs this checker on the real tree failed on every clean tree (card
    # t_582bf539: HEAD red at 23d0d45e, 1 failed 30 passed). The entry is one exact path with a
    # reason, not a blanket output/ rule: a new path under output/ is still a missing path.
    "output/meta_art/title_backdrop/c1":
        "the reference Meta run's output folder; output/ is gitignored, so no checkout carries it",
}

DASHES = {"\u2012": "figure dash", "\u2013": "en dash", "\u2014": "em dash", "\u2015": "horizontal bar"}

CODE_SPAN = re.compile(r"`([^`\n]+)`")
LINK_TARGET = re.compile(r"\]\(([^)\n]+)\)")
PASTED_ROW = re.compile(r"^\s{4}(\S+\.py)((?:\s+[A-Za-z0-9_./:-]+)*?)\s+exit\s+(\d+)\s{2,}(.*)$")
COMMAND = re.compile(r"^(python|python3|py|powershell|git)\s+(.+)$")
PATH_SHAPE = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*/?$")


def is_repo_path(token):
    token = token.strip().rstrip(".,;:)")
    if not token or " " in token or "://" in token:
        return False
    norm = token.replace("\\", "/").strip("/")
    if not PATH_SHAPE.match(norm):
        return False
    head = norm.split("/")[0]
    if "/" not in norm:
        return norm in ROOT_FILES
    return head in KNOWN_ROOTS


def normalise(token):
    return token.strip().rstrip(".,;:)").replace("\\", "/").strip("/")


def collect(lines):
    paths = []
    commands = []
    in_fence = False
    for line in lines:
        # A fenced block is where a reader copies from, and it was not being read: the README tells a
        # reader to run "python tools/check_data.py" inside a sh block, and rule 2 reported "0
        # command(s)" on it (measured 2026-10-26 in the public export, which is the tree a judge
        # reads). Only lines that start with a known runner count, so prose and output stay prose.
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            token = line.strip()
            if token.startswith("$ "):
                token = token[2:].strip()
            if COMMAND.match(token):
                commands.append(token)
            continue
        for token in CODE_SPAN.findall(line):
            token = token.strip()
            match = COMMAND.match(token)
            if match:
                commands.append(token)
            elif is_repo_path(token):
                paths.append(normalise(token))
        for target in LINK_TARGET.findall(line):
            target = target.strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            if is_repo_path(target):
                paths.append(normalise(target))
    seen = []
    for path in paths:
        if path not in seen:
            seen.append(path)
    command_seen = []
    for command in commands:
        if command not in command_seen:
            command_seen.append(command)
    return seen, command_seen


def resolve_tool(name, root=ROOT):
    """Find a tool by bare file name, so the README may write the short form the gate printed."""
    for folder in ("tools", os.path.join("tools", "art")):
        candidate = os.path.join(root, folder, name)
        if os.path.exists(candidate):
            return os.path.join(folder, name)
    return None


def check_paths(paths, root=ROOT):
    missing = []
    exempt = []
    print("1. PATHS the README names")
    for path in paths:
        if path in EXEMPT:
            exempt.append(path)
            print("   EXEMPT   %-46s %s" % (path, EXEMPT[path]))
            continue
        full = os.path.join(root, path.replace("/", os.sep))
        ok = os.path.exists(full)
        print("   %-8s %-46s %s" % ("exists" if ok else "MISSING", path, "" if ok else "not on disk"))
        if not ok:
            missing.append(path)
    print("   %d path(s): %d exist, %d missing, %d exempt" % (len(paths), len(paths) - len(missing) - len(exempt), len(missing), len(exempt)))
    return missing


def check_commands(commands, root=ROOT):
    problems = []
    print("2. COMMANDS the README tells a reader to run")
    for command in commands:
        parts = command.split()
        runner = parts[0]
        if runner == "git":
            print("   ok       %-60s git is on this machine by definition of a checkout" % command)
            continue
        if runner in ("powershell",):
            target = next((p for p in parts[1:] if p.lower().endswith((".ps1", ".vbs"))), None)
            ok = target is not None and os.path.exists(os.path.join(root, target.replace("\\", "/")))
            print("   %-8s %s" % ("ok" if ok else "MISSING", command))
            if not ok:
                problems.append(command)
            continue
        rest = parts[1:]
        if rest and rest[0] == "-m":
            module = rest[1] if len(rest) > 1 else ""
            ok = importlib.util.find_spec(module) is not None
            print("   %-8s %-60s module %s" % ("ok" if ok else "MISSING", command, module))
            if not ok:
                problems.append(command)
            continue
        target = next((p for p in rest if p.lower().endswith((".py", ".ps1"))), None)
        if target is None:
            print("   skipped  %s (no script named; nothing to resolve)" % command)
            continue
        resolved = target if os.path.exists(os.path.join(root, target.replace("\\", "/"))) else resolve_tool(os.path.basename(target), root)
        ok = resolved is not None
        print("   %-8s %-60s %s" % ("ok" if ok else "MISSING", command, resolved or "no such tool"))
        if not ok:
            problems.append(command)
    print("   %d command(s), %d problem(s)" % (len(commands), len(problems)))
    return problems


def pasted_rows(lines):
    rows = []
    for line in lines:
        match = PASTED_ROW.match(line)
        if not match:
            continue
        name, args, code, text = match.groups()
        rows.append({"name": name, "args": args.split(), "expected": int(code), "text": text.strip()})
    return rows


def check_pasted(rows, run=False, root=ROOT, timeout=400):
    print("3. PASTED GATE EXIT CODES")
    if not rows:
        print("   no pasted rows found in this file")
        return []
    problems = []
    for row in rows:
        tool = resolve_tool(row["name"], root)
        if tool is None:
            print("   MISSING TOOL %s" % row["name"])
            problems.append(row["name"])
            continue
        command = [sys.executable, tool] + row["args"]
        if not run:
            print("   ready    %-40s expected exit %d" % (row["name"] + " " + " ".join(row["args"]), row["expected"]))
            continue
        try:
            # stdin=DEVNULL, not inherited: this tool is run by the commit gate and under pytest,
            # and in both cases the inherited standard input is not a valid handle. Measured in
            # tests/test_check_readme.py on 2026-10-26 (card t_7b18be6f): the run died with
            # "OSError: [WinError 6] The handle is invalid" inside subprocess.Popen before the
            # tool it was measuring started, which reads exactly like a broken tool.
            proc = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=timeout,
                                  stdin=subprocess.DEVNULL)
            actual = proc.returncode
            first = (proc.stdout or proc.stderr).strip().splitlines()
            tail = first[-1].strip() if first else ""
            agree = actual == row["expected"]
            print("   %-8s %-40s expected %d, got %d  %s" % (
                "match" if agree else "DISAGREE", row["name"] + " " + " ".join(row["args"]),
                row["expected"], actual, tail[:90]))
            if not agree:
                problems.append(row["name"])
        except subprocess.TimeoutExpired:
            print("   TIMEOUT  %s after %d s" % (row["name"], timeout))
            problems.append(row["name"])
    print("   %d pasted row(s), %d problem(s)%s" % (len(rows), len(problems), "" if run else " (not executed; pass --run)"))
    return problems


def live_counts(root=ROOT):
    """The numbers the README's inventory table quotes, re-read from disk. They move every day."""
    def walk(folder, suffix):
        total = 0
        base = os.path.join(root, folder)
        for dirpath, _dirnames, filenames in os.walk(base):
            total += sum(1 for name in filenames if name.endswith(suffix))
        return total

    tests_folder = os.path.join(root, "tests")
    test_files = [n for n in sorted(os.listdir(tests_folder)) if n.startswith("test_") and n.endswith(".py")]
    test_functions = 0
    for name in test_files:
        with open(os.path.join(tests_folder, name), encoding="utf-8", errors="replace") as fh:
            test_functions += sum(1 for line in fh if line.lstrip().startswith("def test_"))

    resources = 0
    yyp = os.path.join(root, "game", "PrimordialParadox.yyp")
    if os.path.exists(yyp):
        with open(yyp, encoding="utf-8", errors="replace") as fh:
            resources = sum(1 for line in fh if '"resourceType"' in line)

    return [
        ("specs/*.md", len([n for n in os.listdir(os.path.join(root, "specs")) if n.endswith(".md")])),
        ("game resources in PrimordialParadox.yyp", resources),
        ("data/**/*.json", walk("data", ".json")),
        ("tools/**/*.py", walk("tools", ".py")),
        ("tests/test_*.py", len(test_files)),
        ("test functions in tests/", test_functions),
        ("knowledge/**/*.md", walk("knowledge", ".md")),
    ]


def check_counts(root=ROOT):
    print("5. THE INVENTORY TABLE, re-read from disk")
    for label, value in live_counts(root):
        print("   %-42s %s" % (label, value))
    print("   this is a live re-count; the README table carries the date it was read")
    return []


def check_dashes(text):
    print("4. LONG DASH PUNCTUATION")
    found = []
    for char, name in DASHES.items():
        count = text.count(char)
        print("   %-16s %d" % (name, count))
        if count:
            found.append(name)
    print("   %d long dash character(s) found" % sum(text.count(c) for c in DASHES))
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check that the README's commands run and its paths exist.")
    parser.add_argument("--readme", default=os.path.join(ROOT, "README.md"))
    parser.add_argument("--root", default=ROOT)
    parser.add_argument("--run", action="store_true", help="execute the pasted gate block and compare exit codes")
    parser.add_argument("--counts", action="store_true", help="re-read the inventory table's numbers from disk")
    parser.add_argument("--timeout", type=int, default=400)
    args = parser.parse_args(argv)

    if not os.path.exists(args.readme):
        print("check_readme: no such file: %s" % args.readme)
        return 2
    with open(args.readme, encoding="utf-8") as fh:
        text = fh.read()
    lines = text.splitlines()

    paths, commands = collect(lines)
    rows = pasted_rows(lines)
    missing = check_paths(paths, args.root)
    command_problems = check_commands(commands, args.root)
    exit_problems = check_pasted(rows, args.run, args.root, args.timeout)
    dashes = check_dashes(text)
    if args.counts:
        check_counts(args.root)

    problems = len(missing) + len(command_problems) + len(exit_problems) + len(dashes)
    print("check_readme: %d path(s), %d command(s), %d pasted row(s), %d problem(s)" % (len(paths), len(commands), len(rows), problems))
    if problems:
        for item in missing:
            print("  MISSING PATH   %s" % item)
        for item in command_problems:
            print("  BAD COMMAND    %s" % item)
        for item in exit_problems:
            print("  STALE EXIT     %s" % item)
        for item in dashes:
            print("  LONG DASH      %s" % item)
        return 1
    print("check_readme: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
