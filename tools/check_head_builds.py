"""Prove that a clean checkout of HEAD builds and passes the data and project gates.

Why this exists. On 2026-11-01 HEAD did not compile and nobody noticed for hours, because the only proof a
checkout builds was a person running the checks by hand. This script turns that manual proof into one command.

What it does, in order:
  1. `git archive` the projects/primordial-paradox subtree at a ref (default HEAD) into a NEW folder under a
     base directory (default D:\\Temp), with autocrlf off, so the files are the committed bytes.
  2. In that checkout, run tools/sync_data.py, tools/sync_art.py and tools/gen_project.py, which rebuild the
     generated mirrors and the project graph exactly as a build would.
  3. Check that the regenerated game/PrimordialParadox.yyp is byte for byte identical to the committed one.
  4. Run tools/check_data.py.
  5. Compile with tools/run.ps1 -Compile -SkipChecks (run.ps1 takes the build lock itself; this script frees
     memory first and reports free RAM, because the compile wants about 2.5 GB).
  6. Run tests/test_gml_enum_members.py and tests/test_project.py.

Exit code is 0 only when every step passed. The last line printed is a single verdict line, PASS or FAIL, with
each step's exit code.

The checkout is never deleted, whether or not --keep is given. This script never removes anything from disk:
the "never delete" rule is absolute, so a failed run leaves its checkout behind for inspection.

Usage:
    python tools/check_head_builds.py                 # prove HEAD builds and passes the gates
    python tools/check_head_builds.py --ref v1.2.3    # prove a specific ref
    python tools/check_head_builds.py --dry-run       # print the plan only, run nothing, never compile
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tarfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
REPO_ROOT = os.path.dirname(os.path.dirname(PROJECT_ROOT))

# The git archive pathspec and the repo-relative project file, with forward slashes, which is what git wants.
PP_REL = "projects/primordial-paradox"
YPP_REL = PP_REL + "/game/PrimordialParadox.yyp"

# The interpreter the card pins. Overridable with --python or the PP_PYTHON environment variable.
DEFAULT_PYTHON = r"<home>\AppData\Local\Python\pythoncore-3.14-64\python.exe"

DEFAULT_BASE = r"D:\Temp"
TMP_DIR = r"D:\Temp\hermes-tmp"

# The steps in run order, so the verdict line and the runner cannot drift apart.
STEP_LABELS = (
    "extract",
    "sync_data",
    "sync_art",
    "gen_project",
    "yyp",
    "check_data",
    "compile",
    "enum_tests",
    "project_tests",
)

COMPILE_TIMEOUT_S = 900
FREE_RAM_FLOOR_GB = 2.5


def parse_args(argv):
    """Parse the command line into a namespace; a None argv reads sys.argv[1:]."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=None,
                        help="the Shared git repo (default: resolved from this file's location)")
    parser.add_argument("--ref", default="HEAD", help="git ref to extract (default: HEAD)")
    parser.add_argument("--base", default=None,
                        help="folder to create the checkout under (default: D:\\Temp)")
    parser.add_argument("--python", default=None, help="interpreter to run the tools and tests with")
    parser.add_argument("--keep", action="store_true",
                        help="leave the checkout in place (this is the default: the script never deletes)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the plan and exit 0 without touching git, disk or the compiler")
    return parser.parse_args(argv)


def _python(args):
    return args.python or os.environ.get("PP_PYTHON") or DEFAULT_PYTHON


def _env():
    """A child environment with TEMP/TMP/TMPDIR pinned to D:\\Temp\\hermes-tmp (D: has room)."""
    os.makedirs(TMP_DIR, exist_ok=True)
    env = os.environ.copy()
    env["TEMP"] = TMP_DIR
    env["TMP"] = TMP_DIR
    env["TMPDIR"] = TMP_DIR
    return env


def _short_sha(repo, ref):
    proc = subprocess.run(["git", "-C", repo, "rev-parse", "--short=8", ref],
                          stdin=subprocess.DEVNULL, capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _committed_yyp(repo, ref):
    proc = subprocess.run(["git", "-C", repo, "show", "%s:%s" % (ref, YPP_REL)],
                          stdin=subprocess.DEVNULL, capture_output=True)
    if proc.returncode != 0:
        return None
    return proc.stdout


def _new_checkout_dir(base, short):
    os.makedirs(base, exist_ok=True)
    name = "pp-check-%s-%s" % (short, time.strftime("%Y%m%d-%H%M%S"))
    dest = os.path.join(base, name)
    suffix = 0
    while os.path.exists(dest):
        suffix += 1
        dest = os.path.join(base, "%s-%d" % (name, suffix))
    os.makedirs(dest)
    return dest


def extract_head(repo, ref, dest):
    """git archive the PP subtree at ref into dest, autocrlf off, using Python's tarfile reader.

    The tree-ish form `ref:projects/primordial-paradox` exports the subtree with its files at the
    archive root, so dest holds game/, tools/, tests/ and data/ directly. tarfile's data filter
    strips any absolute or traversal path as defence in depth, even though git archive never
    writes one.
    """
    treeish = "%s:%s" % (ref, PP_REL)
    cmd = ["git", "-C", repo, "-c", "core.autocrlf=false", "archive", "--format=tar", treeish]
    proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdout is not None and proc.stderr is not None
    try:
        with tarfile.open(fileobj=proc.stdout, mode="r|") as tf:
            tf.extractall(dest, filter="data")
    finally:
        proc.stdout.close()
        proc.wait()
    if proc.returncode != 0:
        err = proc.stderr.read().decode("utf-8", "replace").strip()
        raise RuntimeError("git archive failed (%d): %s" % (proc.returncode, err))


def _run(args_list, cwd, timeout=None):
    return subprocess.run(args_list, cwd=cwd, env=_env(), stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, encoding="utf-8", errors="replace", timeout=timeout)


def _step_tool(dest, script, py, extra=()):
    cmd = [py, os.path.join(dest, "tools", script)] + list(extra)
    proc = _run(cmd, dest)
    print(proc.stdout.rstrip())
    return proc.returncode


def free_ram_gb():
    """Available physical memory in GiB from GlobalMemoryStatusEx, or None off Windows or on failure."""
    try:
        import ctypes

        class _MS(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        st = _MS()
        st.dwLength = ctypes.sizeof(_MS)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
            return None
        return st.ullAvailPhys / (2.0 ** 30)
    except (AttributeError, OSError):
        return None


def _trim_working_set():
    """Trim this process's own working set, a best-effort RAM release before the compile.

    Returns True when the Win32 trim was attempted, False on a host where the call is unavailable.
    """
    try:
        import ctypes
        ctypes.windll.kernel32.SetProcessWorkingSetSize(
            ctypes.windll.kernel32.GetCurrentProcess(), -1, -1)
        return True
    except (AttributeError, OSError):
        return False


def _free_ram_preflight():
    gb = free_ram_gb()
    if gb is None:
        print("compile: free RAM unknown on this host")
        return
    print("compile: %.2f GB free RAM before compile" % gb)
    if gb < FREE_RAM_FLOOR_GB:
        print("compile: WARNING only %.2f GB free; the compile wants about %.1f GB" % (gb, FREE_RAM_FLOOR_GB))
        _trim_working_set()
        after = free_ram_gb()
        if after is not None:
            print("compile: %.2f GB free after trim" % after)


def _step_compile(dest, py):
    _free_ram_preflight()
    ps1 = os.path.join(dest, "tools", "run.ps1")
    proc = _run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", ps1, "-Compile", "-SkipChecks"], dest, timeout=COMPILE_TIMEOUT_S)
    print(proc.stdout.rstrip())
    return proc.returncode


def _step_pytest(dest, py, test_files):
    cmd = [py, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    cmd += [os.path.join(dest, f) for f in test_files]
    proc = _run(cmd, dest)
    print(proc.stdout.rstrip())
    return proc.returncode


def _step_yyp(repo, ref, dest):
    committed = _committed_yyp(repo, ref)
    if committed is None:
        print("yyp: could not read the committed file at %s:%s" % (ref, YPP_REL))
        return 1
    with open(os.path.join(dest, "game", "PrimordialParadox.yyp"), "rb") as fh:
        regenerated = fh.read()
    if committed == regenerated:
        print("yyp: regenerated PrimordialParadox.yyp is byte for byte identical to the committed file")
        return 0
    print("yyp: MISMATCH, committed %d bytes vs regenerated %d bytes" % (len(committed), len(regenerated)))
    return 1


def _dry_run(args):
    print("DRY RUN: nothing is checked out and nothing is compiled.")
    print("  repo   : %s" % (args.repo or REPO_ROOT))
    print("  ref    : %s" % args.ref)
    print("  base   : %s" % (args.base or DEFAULT_BASE))
    print("  python : %s" % _python(args))
    print("  steps  : " + " -> ".join(STEP_LABELS))
    return 0


def main(argv=None):
    """Run the proof and return 0 only when every step passed; prints one verdict line at the end."""
    args = parse_args(argv)
    if args.dry_run:
        return _dry_run(args)

    py = _python(args)
    repo = args.repo or REPO_ROOT
    ref = args.ref
    short = _short_sha(repo, ref)
    if short is None:
        print("VERDICT: FAIL | ref=%s | extract=-1 | error=cannot resolve ref" % ref)
        return 1

    base = args.base or DEFAULT_BASE
    dest = _new_checkout_dir(base, short)
    print("checkout: %s (ref %s)" % (dest, short))

    results = {}
    steps = (
        ("extract", lambda: _step_extract(repo, ref, dest)),
        ("sync_data", lambda: _step_tool(dest, "sync_data.py", py)),
        ("sync_art", lambda: _step_tool(dest, "sync_art.py", py)),
        ("gen_project", lambda: _step_tool(dest, "gen_project.py", py)),
        ("yyp", lambda: _step_yyp(repo, ref, dest)),
        ("check_data", lambda: _step_tool(dest, "check_data.py", py, ["--root", dest])),
        ("compile", lambda: _step_compile(dest, py)),
        ("enum_tests", lambda: _step_pytest(dest, py, ["tests/test_gml_enum_members.py"])),
        ("project_tests", lambda: _step_pytest(dest, py, ["tests/test_project.py"])),
    )

    for label, run in steps:
        try:
            rc = run()
        except (subprocess.TimeoutExpired, OSError, RuntimeError) as exc:
            print("step %s: error %s" % (label, exc))
            results[label] = 1
            break
        results[label] = rc
        print("step %s: exit %d" % (label, rc))
        if rc != 0:
            break

    all_ok = len(results) == len(steps) and all(v == 0 for v in results.values())
    parts = ["ref=%s" % short, "checkout=%s" % dest]
    for label in STEP_LABELS:
        parts.append("%s=%s" % (label, results.get(label, "notrun")))
    print("VERDICT: %s | %s" % ("PASS" if all_ok else "FAIL", " ".join(parts)))
    if args.keep:
        print("checkout kept at %s (requested with --keep)" % dest)
    else:
        print("checkout left at %s (this script never deletes it)" % dest)
    return 0 if all_ok else 1


def _step_extract(repo, ref, dest):
    extract_head(repo, ref, dest)
    print("extracted %s:%s into %s" % (ref, PP_REL, dest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
