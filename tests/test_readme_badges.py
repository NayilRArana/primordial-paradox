"""Tests for tools/readme_badges.py: the block is a measurement, and a stale one is refused.

Card t_4f984c7b (SUB-KIT-FINAL). The tool exists for one property: a badge in the README may not
say something the tree no longer says. So the tests work on the two halves of that property.
What goes in: a run decides both the table and the picture, the region between the markers is the
only thing rewritten, and a missing marker stops the tool instead of appending a second block.
What comes out: `--verify` compares a fresh run against the README by plain equality, and a
README that says PASS where the run says FAIL is a refusal, not a warning.

No test here reruns the four real gates. Two of them take minutes, and a suite that waits on
them teaches the next lane to skip the suite. The last test instead holds the shipped README to
its own badge files, which catches a block and a picture that disagree, and the desktop rerun
happens when the tool is run.
"""

from __future__ import annotations

import os

import pytest

import readme_badges as rb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def result(slug="check_data", label="check_data", exit_code=0, command=None):
    return {
        "slug": slug,
        "label": label,
        "command": command or "python tools/%s.py" % slug,
        "exit": exit_code,
        "status": rb.status_of(exit_code),
        "seconds": 0.5,
    }


def readme_with_block(block, before="# Title\n\ntext\n\n", after="\n\n## Later\n\nmore prose\n"):
    return before + block + after


# --------------------------------------------------------------------------- the verdict


def test_status_of_reads_the_exit_code():
    assert rb.status_of(0) == "PASS"
    assert rb.status_of(1) == "FAIL"
    assert rb.status_of(3) == "FAIL"
    assert rb.status_of(None) == "TIMEOUT"


def test_the_four_gates_are_the_ones_the_checklist_runs():
    labels = [gate["label"] for gate in rb.GATES]
    assert labels == ["check_data", "check_cleanroom", "nes_audit_all", "play_demo --check"]
    assert rb.command_text(rb.GATES[3]) == "python tools/play_demo.py --check"
    for gate in rb.GATES:
        assert os.path.exists(os.path.join(ROOT, gate["tool"].replace("/", os.sep))), gate["tool"]


# --------------------------------------------------------------------------- the badge picture


def test_a_badge_is_svg_and_says_what_it_was_given():
    good = rb.render_badge("check_data", "PASS")
    bad = rb.render_badge("check_data", "FAIL")
    for svg, status in ((good, "PASS"), (bad, "FAIL")):
        assert svg.startswith("<svg")
        assert svg.rstrip().endswith("</svg>")
        assert "check_data" in svg and status in svg
        assert ROOT not in svg
    assert good != bad
    assert rb.render_badge("check_data", "PASS") == good


def test_a_badge_escapes_text_that_looks_like_markup():
    svg = rb.render_badge("a<b", "PASS")
    assert "&lt;" in svg and "a<b" not in svg


# --------------------------------------------------------------------------- the block


def test_the_block_lists_one_row_per_gate_and_parses_back():
    results = [result("check_data"), result("play_demo_check", "play_demo --check", 1)]
    block = rb.build_block(results)
    assert block.startswith(rb.START) and block.endswith(rb.END)
    rows = rb.parse_block(block)
    assert [row["label"] for row in rows] == ["check_data", "play_demo --check"]
    assert [row["status"] for row in rows] == ["PASS", "FAIL"]
    assert rows[1]["command"] == "python tools/play_demo_check.py"
    for row in rows:
        assert "docs/badges/" in block


def test_the_block_names_a_badge_path_per_gate():
    results = [result("check_data"), result("nes_audit_all", "nes_audit_all", 1)]
    block = rb.build_block(results)
    assert "docs/badges/check_data.svg" in block
    assert "docs/badges/nes_audit_all.svg" in block


def test_no_marker_pair_means_no_block():
    assert rb.find_block("# Title\n\ntext\n") is None
    assert rb.find_block(rb.START + "\nno end here\n") is None
    block = rb.build_block([result()])
    assert rb.find_block(block) == block


def test_replacing_the_block_leaves_the_rest_of_the_readme_alone():
    old = rb.build_block([result(exit_code=0)])
    text = readme_with_block(old)
    new = rb.build_block([result(exit_code=1)])
    updated = rb.replace_block(text, new)
    assert updated.startswith("# Title")
    assert updated.endswith("## Later\n\nmore prose\n")
    assert new in updated and old not in updated
    assert rb.replace_block("# no markers\n", new) is None


# --------------------------------------------------------------------------- the checks


def test_check_badges_finds_a_missing_file(tmp_path):
    block = rb.build_block([result()])
    text = readme_with_block(block)
    (tmp_path / "README.md").write_text(text, encoding="utf-8")
    problems = rb.check_badges([result()], str(tmp_path))
    assert problems and "missing" in problems[0]


def test_check_badges_finds_a_picture_that_disagrees(tmp_path):
    results = [result()]
    rb.write_badges(results, str(tmp_path))
    assert rb.check_badges(results, str(tmp_path)) == []
    rb.write_badges([result(exit_code=1)], str(tmp_path))
    problems = rb.check_badges(results, str(tmp_path))
    assert problems and "does not match" in problems[0]


def test_verify_accepts_a_readme_that_matches_the_run(tmp_path, capsys):
    results = [result()]
    (tmp_path / "README.md").write_text(readme_with_block(rb.build_block(results)), encoding="utf-8")
    rb.write_badges(results, str(tmp_path))
    assert rb.verify(str(tmp_path), results=results) == 0
    assert "match this run" in capsys.readouterr().out


def test_verify_refuses_a_block_that_says_pass_when_the_gate_says_fail(tmp_path, capsys):
    """The negative control for the whole tool: last night's green against this morning's red."""
    claimed = [result()]
    (tmp_path / "README.md").write_text(readme_with_block(rb.build_block(claimed)), encoding="utf-8")
    rb.write_badges(claimed, str(tmp_path))
    assert rb.verify(str(tmp_path), results=[result(exit_code=1)]) == 1
    out = capsys.readouterr().out
    assert "stale" in out and "README says PASS, this run says FAIL" in out


def test_verify_refuses_a_readme_with_no_markers(tmp_path, capsys):
    (tmp_path / "README.md").write_text("# Title\n\nno block here\n", encoding="utf-8")
    assert rb.verify(str(tmp_path), results=[result()]) == 1
    assert "nothing to verify" in capsys.readouterr().out


def test_write_rewrites_the_block_and_the_badges(tmp_path, capsys):
    stale = [result(exit_code=1)]
    (tmp_path / "README.md").write_text(readme_with_block(rb.build_block(stale)), encoding="utf-8")
    fresh = [result(exit_code=0)]
    assert rb.write(str(tmp_path), results=fresh) == 0
    text = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "| PASS |" in text and "| FAIL |" not in text
    assert text.startswith("# Title") and text.endswith("more prose\n")
    for item in fresh:
        assert os.path.exists(os.path.join(str(tmp_path), "docs", "badges", item["slug"] + ".svg"))
    assert "wrote 1 badge file(s)" in capsys.readouterr().out


def test_write_refuses_a_readme_with_no_markers(tmp_path, capsys):
    (tmp_path / "README.md").write_text("# Title\n", encoding="utf-8")
    assert rb.write(str(tmp_path), results=[result()]) == 1
    assert "add the two markers first" in capsys.readouterr().out


def test_main_needs_exactly_one_mode(capsys):
    assert rb.main(["--list"]) == 0
    assert rb.main([]) == 2
    assert rb.main(["--write", "--verify"]) == 2


# --------------------------------------------------------------------------- the shipped README


def test_the_shipped_readme_carries_the_block_and_the_four_gates():
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as fh:
        text = fh.read()
    block = rb.find_block(text)
    assert block is not None
    rows = rb.parse_block(block)
    assert [row["label"] for row in rows] == [gate["label"] for gate in rb.GATES]


def test_every_shipped_badge_is_the_picture_the_block_claims():
    """A block and a picture that disagree is the one failure a reader cannot see for himself."""
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as fh:
        text = fh.read()
    rows = rb.parse_block(rb.find_block(text))
    assert rows
    for row in rows:
        path = os.path.join(ROOT, "docs", "badges", row["label"].replace(" ", "_") + ".svg")
        if "play_demo" in row["label"]:
            path = os.path.join(ROOT, "docs", "badges", "play_demo_check.svg")
        assert os.path.exists(path), path
        with open(path, encoding="utf-8") as fh:
            svg = fh.read()
        assert row["status"] in svg
