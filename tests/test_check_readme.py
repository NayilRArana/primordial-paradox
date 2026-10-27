"""Tests for tools/check_readme.py: the README's promises are measured, not read.

Card t_7b18be6f (PUB-1). The checker is the one tool that holds the page a judge opens first to
what is actually on disk, so every claim it makes needs a test that would fail if the claim stopped
being true. Three kinds of test here:

1. the real README passes the real tree (the live check, no execution),
2. every class of mistake the checker claims to catch DOES fail on a fixture, including a pasted
   exit code that disagrees with the tool's own, because that is the branch a stale README needs,
3. the parsers (path shapes, commands, pasted rows, counts) answer on their own, so a change to
   one regex cannot quietly widen what the file is allowed to say.
"""

from __future__ import annotations

import os

import check_readme

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------------------------------- live check


def test_the_real_readme_passes_the_real_tree(capsys):
    """The check the card runs: 0 problems on the committed README, without executing the block."""
    assert check_readme.main([]) == 0
    out = capsys.readouterr().out
    assert "check_readme: PASS" in out
    assert "0 problem(s)" in out


def test_a_missing_readme_is_a_bad_argument_not_a_failure(tmp_path):
    assert check_readme.main(["--readme", str(tmp_path / "nope.md")]) == 2


# --------------------------------------------------------------------------- 1. paths


def test_is_repo_path_accepts_a_known_root():
    assert check_readme.is_repo_path("tools/check_data.py")
    assert check_readme.is_repo_path("knowledge/NES-AUDIT.md")
    assert check_readme.is_repo_path("tests/test_check_data.py")


def test_is_repo_path_accepts_a_root_file_only_by_its_exact_name():
    assert check_readme.is_repo_path("README.md")
    assert not check_readme.is_repo_path("readme.md")


def test_is_repo_path_rejects_prose_a_url_and_an_unknown_root():
    assert not check_readme.is_repo_path("not a path")
    assert not check_readme.is_repo_path("https://example.com/tools/x.py")
    assert not check_readme.is_repo_path("notes/some-note.md")
    assert not check_readme.is_repo_path("")


def test_normalise_turns_backslashes_into_slashes_and_drops_trailing_punctuation():
    assert check_readme.normalise("tools\\art\\a.py.") == "tools/art/a.py"
    assert check_readme.normalise("/knowledge/x.md") == "knowledge/x.md"


def test_collect_separates_commands_from_paths_and_dedupes():
    lines = [
        "Run `python tools/check_data.py` and read `knowledge/NES-AUDIT.md`.",
        "Also read `knowledge/NES-AUDIT.md` again, and see [the audit](knowledge/CHAR-PIPE-REVIEW.md).",
        "A link to the web is not a path: [docs](https://example.com/x.md).",
    ]
    paths, commands = check_readme.collect(lines)
    assert paths == ["knowledge/NES-AUDIT.md", "knowledge/CHAR-PIPE-REVIEW.md"]
    assert commands == ["python tools/check_data.py"]


def test_collect_reads_a_fenced_block_because_that_is_what_a_reader_copies():
    """The README's own commands live in fences, and fences were not read: rule 2 said 0 commands.

    Measured 2026-10-26 in the public export, where the whole README is three fences and the checker
    reported "0 command(s)": the two commands a judge copies were never resolved against the tree.
    """
    lines = [
        "Prose that names a fence:",
        "```sh",
        "python tools/check_data.py",
        "$ python -m pytest -q",
        "```",
        "```",
        "the pasted output of a run, is not a command: 4 passed in 1.2s",
        "```",
    ]
    paths, commands = check_readme.collect(lines)
    assert paths == []
    assert commands == ["python tools/check_data.py", "python -m pytest -q"]


def test_check_commands_flags_a_missing_script_named_inside_a_fence(tmp_path, capsys):
    """The negative control for the fenced rule: a fence naming a script that is not there must fail."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "good.py").write_text("", encoding="utf-8")
    (tmp_path / "README.md").write_text(
        "Copy this:\n\n```sh\npython tools/good.py\npython tools/nope.py\n```\n", encoding="utf-8")
    assert check_readme.main(["--readme", str(tmp_path / "README.md"), "--root", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "MISSING" in out and "tools/nope.py" in out


def test_the_real_readme_commands_all_resolve():
    """Every command the live README tells a reader to run names something this tree holds."""
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as fh:
        _paths, commands = check_readme.collect(fh.read().splitlines())
    assert commands, "the README tells a reader to run something, so the list cannot be empty"
    assert check_readme.check_commands(commands, ROOT) == []


def test_check_paths_names_the_path_that_is_not_on_disk(tmp_path, capsys):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "present.py").write_text("", encoding="utf-8")
    missing = check_readme.check_paths(["tools/present.py", "data/missing.json"], str(tmp_path))
    out = capsys.readouterr().out
    assert missing == ["data/missing.json"]
    assert "MISSING  data/missing.json" in out
    assert "2 path(s): 1 exist, 1 missing, 0 exempt" in out


def test_check_paths_prints_an_exemption_and_does_not_call_it_missing(capsys):
    """The one exemption is a path inside the GameMaker project file, and it is printed, not skipped."""
    missing = check_readme.check_paths(["datafiles/streams/percy_theme_v3.ogg"], ROOT)
    out = capsys.readouterr().out
    assert missing == []
    assert "EXEMPT" in out
    assert "1 exempt" in out


def test_the_exempt_run_output_is_printed_with_its_reason(capsys):
    """The path a Meta run writes is gitignored, so it is exempt by name and its reason is printed.

    Card t_582bf539. README.md points a reader at the reference run's folder under output/, which
    .gitignore keeps out of the tree, so the live check failed on every clean checkout. The exemption
    covers that ONE path and nothing else: an unnamed path under output/ must still fail.
    """
    assert check_readme.main([]) == 0
    out = capsys.readouterr().out
    reason = check_readme.EXEMPT["output/meta_art/title_backdrop/c1"]
    assert "EXEMPT   output/meta_art/title_backdrop/c1" in out
    assert reason in out
    # the exemption is not a blanket rule over the ignored folder
    assert check_readme.check_paths(["output/meta_art/some_other_run/c1"], ROOT) == [
        "output/meta_art/some_other_run/c1"]


# --------------------------------------------------------------------------- 2. commands


def test_check_commands_flags_a_script_that_is_not_there(tmp_path, capsys):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "good.py").write_text("", encoding="utf-8")
    problems = check_readme.check_commands(
        ["python tools/good.py", "python tools/nope.py"], str(tmp_path))
    out = capsys.readouterr().out
    assert problems == ["python tools/nope.py"]
    assert "MISSING" in out


def test_check_commands_resolves_the_short_form_the_gate_prints(tmp_path, capsys):
    """Every pasted row writes `check_data.py`, not `tools/check_data.py`, so the short form must work."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "check_data.py").write_text("", encoding="utf-8")
    assert check_readme.check_commands(["python check_data.py"], str(tmp_path)) == []
    capsys.readouterr()


def test_check_commands_resolves_a_tool_under_tools_art(tmp_path, capsys):
    (tmp_path / "tools" / "art").mkdir(parents=True)
    (tmp_path / "tools" / "art" / "make_x.py").write_text("", encoding="utf-8")
    assert check_readme.check_commands(["python make_x.py"], str(tmp_path)) == []
    capsys.readouterr()


def test_check_commands_treats_git_as_present_by_definition(capsys):
    assert check_readme.check_commands(["git status"], ROOT) == []
    capsys.readouterr()


def test_check_commands_checks_a_module_it_can_import(capsys):
    assert check_readme.check_commands(["python -m pytest"], ROOT) == []
    assert check_readme.check_commands(["python -m no_such_module_here"]) != []
    capsys.readouterr()


def test_check_commands_skips_a_command_with_no_script_named(capsys):
    assert check_readme.check_commands(["python --version"], ROOT) == []
    assert "skipped" in capsys.readouterr().out


def test_check_commands_requires_the_ps1_a_powershell_line_names(tmp_path, capsys):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "run.ps1").write_text("", encoding="utf-8")
    assert check_readme.check_commands(["powershell tools/run.ps1"], str(tmp_path)) == []
    assert check_readme.check_commands(["powershell tools/gone.ps1"], str(tmp_path)) == [
        "powershell tools/gone.ps1"]
    capsys.readouterr()


# --------------------------------------------------------------------------- 3. pasted exit codes


def test_pasted_rows_reads_a_gate_row_and_ignores_prose():
    lines = [
        "The block below was pasted from a run:",
        "    check_data.py        exit 0  check_data: all files pass",
        "    nes_audit_all.py     exit 1  nes_audit_all: FAIL  183 file(s), 35 failing",
        "  check_data.py exit 0 this line is indented by two spaces and is not a pasted row",
    ]
    rows = check_readme.pasted_rows(lines)
    assert [r["name"] for r in rows] == ["check_data.py", "nes_audit_all.py"]
    assert rows[0]["expected"] == 0
    assert rows[0]["args"] == []
    assert rows[1]["expected"] == 1


def test_pasted_rows_keeps_a_tool_argument():
    rows = check_readme.pasted_rows(["    palette_synergy.py --gate      exit 0  PASS"])
    assert rows[0]["name"] == "palette_synergy.py"
    assert rows[0]["args"] == ["--gate"]


def test_check_pasted_without_run_lists_what_it_would_run_and_says_so(tmp_path, capsys):
    rows = [{"name": "exit_two.py", "args": [], "expected": 2, "text": ""}]
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "exit_two.py").write_text("import sys\nsys.exit(2)\n", encoding="utf-8")
    assert check_readme.check_pasted(rows, run=False, root=str(tmp_path)) == []
    out = capsys.readouterr().out
    assert "ready" in out
    assert "(not executed; pass --run)" in out


def test_check_pasted_agrees_when_the_real_exit_code_matches(tmp_path, capsys):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "exit_two.py").write_text("import sys\nsys.exit(2)\n", encoding="utf-8")
    rows = [{"name": "exit_two.py", "args": [], "expected": 2, "text": ""}]
    assert check_readme.check_pasted(rows, run=True, root=str(tmp_path)) == []
    assert "match" in capsys.readouterr().out


def test_check_pasted_fails_a_stale_exit_code(tmp_path, capsys):
    """The branch the file exists for: a tool that moved on and a pasted number that did not."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "exit_two.py").write_text("import sys\nsys.exit(2)\n", encoding="utf-8")
    rows = [{"name": "exit_two.py", "args": [], "expected": 0, "text": ""}]
    assert check_readme.check_pasted(rows, run=True, root=str(tmp_path)) == ["exit_two.py"]
    assert "DISAGREE" in capsys.readouterr().out


def test_check_pasted_reports_a_missing_tool(tmp_path, capsys):
    (tmp_path / "tools").mkdir()
    rows = [{"name": "gone.py", "args": [], "expected": 0, "text": ""}]
    assert check_readme.check_pasted(rows, run=True, root=str(tmp_path)) == ["gone.py"]
    assert "MISSING TOOL" in capsys.readouterr().out


# --------------------------------------------------------------------------- 4. dashes


def test_check_dashes_finds_all_four_characters(capsys):
    text = "a \u2012 b \u2013 c \u2014 d \u2015 e"
    assert sorted(check_readme.check_dashes(text)) == sorted(
        ["figure dash", "en dash", "em dash", "horizontal bar"])
    assert "4 long dash character(s) found" in capsys.readouterr().out


def test_check_dashes_is_clean_on_plain_ascii(capsys):
    assert check_readme.check_dashes("a - b, a semicolon; a colon:") == []
    assert "0 long dash character(s) found" in capsys.readouterr().out


# --------------------------------------------------------------------------- 5. counts


def fixture_tree(tmp_path):
    """A small tree every count in live_counts can read, so the numbers are asserted, not assumed."""
    root = tmp_path / "tree"
    for folder in ("specs", "data/sub", "tools", "knowledge", "tests", "game"):
        (root / folder).mkdir(parents=True)
    (root / "specs" / "a.md").write_text("", encoding="utf-8")
    (root / "specs" / "b.md").write_text("", encoding="utf-8")
    (root / "specs" / "not-a-spec.txt").write_text("", encoding="utf-8")
    (root / "data" / "x.json").write_text("{}", encoding="utf-8")
    (root / "data" / "sub" / "y.json").write_text("{}", encoding="utf-8")
    (root / "data" / "sub" / "z.txt").write_text("", encoding="utf-8")
    (root / "tools" / "t.py").write_text("", encoding="utf-8")
    (root / "knowledge" / "k.md").write_text("", encoding="utf-8")
    (root / "tests" / "test_one.py").write_text(
        "def test_a():\n    pass\n\n\ndef test_b():\n    pass\n", encoding="utf-8")
    (root / "tests" / "helper.py").write_text("", encoding="utf-8")
    (root / "game" / "PrimordialParadox.yyp").write_text(
        '{"resources": [\n{"resourceType": "GMSprite"},\n{"resourceType": "GMScript"}]}', encoding="utf-8")
    return root


def test_live_counts_reads_the_tree_it_is_pointed_at(tmp_path):
    counts = dict(check_readme.live_counts(str(fixture_tree(tmp_path))))
    assert counts["specs/*.md"] == 2
    assert counts["game resources in PrimordialParadox.yyp"] == 2
    assert counts["data/**/*.json"] == 2
    assert counts["tools/**/*.py"] == 1
    assert counts["tests/test_*.py"] == 1
    assert counts["test functions in tests/"] == 2
    assert counts["knowledge/**/*.md"] == 1


def test_live_counts_does_not_count_a_test_helper_as_a_test_file(tmp_path):
    """A helper module in tests/ is not a test file: only test_*.py counts, the same rule the suite uses."""
    counts = dict(check_readme.live_counts(str(fixture_tree(tmp_path))))
    assert counts["tests/test_*.py"] == 1


def test_check_counts_prints_every_row_and_never_fails(tmp_path, capsys):
    assert check_readme.check_counts(str(fixture_tree(tmp_path))) == []
    out = capsys.readouterr().out
    assert "5. THE INVENTORY TABLE" in out
    assert "live re-count" in out


def test_the_real_tree_counts_are_positive(capsys):
    counts = dict(check_readme.live_counts(ROOT))
    assert counts["tests/test_*.py"] > 0
    assert counts["test functions in tests/"] > 0
    assert counts["tools/**/*.py"] > 0
    capsys.readouterr()


# --------------------------------------------------------------------------- main


def test_main_fails_a_missing_path_and_passes_once_it_is_there(tmp_path, capsys):
    root = fixture_tree(tmp_path)
    readme = root / "README.md"
    readme.write_text("Read `tools/t.py` and `knowledge/k.md`.\n", encoding="utf-8")
    assert check_readme.main(["--readme", str(readme), "--root", str(root)]) == 0

    readme.write_text("Read `tools/t.py` and `knowledge/gone.md`.\n", encoding="utf-8")
    assert check_readme.main(["--readme", str(readme), "--root", str(root)]) == 1
    out = capsys.readouterr().out
    assert "MISSING PATH   knowledge/gone.md" in out


def test_main_fails_a_long_dash_in_the_file(tmp_path, capsys):
    root = fixture_tree(tmp_path)
    readme = root / "README.md"
    readme.write_text("Read `tools/t.py` \u2014 then stop.\n", encoding="utf-8")
    assert check_readme.main(["--readme", str(readme), "--root", str(root)]) == 1
    assert "LONG DASH      em dash" in capsys.readouterr().out


def test_main_fails_a_command_that_names_a_missing_tool(tmp_path, capsys):
    root = fixture_tree(tmp_path)
    readme = root / "README.md"
    readme.write_text("Run `python tools/gone.py` first.\n", encoding="utf-8")
    assert check_readme.main(["--readme", str(readme), "--root", str(root)]) == 1
    assert "BAD COMMAND    python tools/gone.py" in capsys.readouterr().out
