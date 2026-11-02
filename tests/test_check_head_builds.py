"""Argument parsing and the dry-run mode of tools/check_head_builds.py.

The full script extracts HEAD, rebuilds the mirrors and the project graph, compiles with GameMaker and runs two
test files. None of that belongs in a unit test: this file proves the flag parsing and that --dry-run prints a
plan and exits 0 without touching git, disk or the compiler, which is the exact contract every caller depends on.
"""

from __future__ import annotations

import check_head_builds


def test_flags_keep_and_dry_run_parse():
    args = check_head_builds.parse_args(["--keep", "--dry-run"])
    assert args.keep is True
    assert args.dry_run is True


def test_ref_and_base_and_python_parse():
    args = check_head_builds.parse_args(["--ref", "v1.2.3", "--base", "Z:/tmp", "--python", "C:/py/python.exe"])
    assert args.ref == "v1.2.3"
    assert args.base == "Z:/tmp"
    assert args.python == "C:/py/python.exe"


def test_defaults():
    args = check_head_builds.parse_args([])
    assert args.ref == "HEAD"
    assert args.keep is False
    assert args.dry_run is False
    assert args.base is None
    assert args.python is None


def test_dry_run_exits_zero_without_compiling(capsys):
    code = check_head_builds.main(["--dry-run"])
    out = capsys.readouterr().out
    assert code == 0
    assert "DRY RUN" in out
    assert "compile" in out, "the plan must name the compile step it is not going to run"
    assert "VERDICT:" not in out, "a dry run must not run the gate steps or print a verdict"


def test_step_labels_cover_every_gate():
    # The verdict line and the runner share STEP_LABELS; a step dropped here would silently leave the gate untested.
    assert check_head_builds.STEP_LABELS == (
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
