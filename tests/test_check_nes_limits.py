"""Tests for tools/check_nes_limits.py: the 256x240 and at most 16 colours limit is measured, not asserted.

What these tests hold down (judge panel 2026-11-17 fix 5, card t_1b404055):

  1. THE REAL TREE PASSES, and the numbers it prints are the ones it measured: a 256x240 frame, and a colour
     count the scene's own palette and the composed title frame agree on.
  2. A ROOM OFF THE FRAME IS NAMED. A room whose roomSettings leave 256x240 fails with the room's name, so a
     red run points at the file to fix.
  3. A FRAME MACRO OFF THE FRAME IS NAMED, for the same reason, on the engine's own constant.
  4. TOO MANY COLOURS IS A FAILURE, not a warning: 17 colours against a limit of 16 is refused, and the
     failure prints the colours it counted.
  5. AN UNREADABLE TREE IS REFUSED, not passed: a missing pp_config.gml is an error that names the path, so a
     tree this check cannot see never reads as a tree that passes.
  6. THE VERDICT LINE IS THE BADGE'S WORD. A pass starts with PASS (the badge on the title card says PASS and
     nothing else) and a failure starts with FAIL.

Run: python -m pytest tests/test_check_nes_limits.py -q
"""

from __future__ import annotations

import os
import re
import shutil

import pytest

import check_nes_limits

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEX = re.compile(r"^#[0-9a-f]{6}$")


@pytest.fixture(scope="module")
def measured():
    return check_nes_limits.measure(ROOT)


def _skeleton(tmp_path):
    """A root holding exactly what this check reads: the config macros, the four rooms, and the title art.

    Copied rather than mocked on purpose, so a test that breaks one room's size still measures the other
    three and still composes the title frame: the failure it asserts on is the only one in the tree.
    """
    root = str(tmp_path / "repo")
    os.makedirs(os.path.join(root, "game", "scripts", "pp_config"))
    shutil.copy2(os.path.join(ROOT, check_nes_limits.CONFIG), os.path.join(root, check_nes_limits.CONFIG))
    for name in os.listdir(os.path.join(ROOT, check_nes_limits.ROOMS)):
        source = os.path.join(ROOT, check_nes_limits.ROOMS, name)
        if os.path.isdir(source):
            shutil.copytree(source, os.path.join(root, check_nes_limits.ROOMS, name))
    for relative in (os.path.join("data", "title.json"), os.path.join("data", "nes_palette.json"),
                     os.path.join("data", "palettes", "scene_title.json")):
        os.makedirs(os.path.dirname(os.path.join(root, relative)), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, relative), os.path.join(root, relative))
    shutil.copytree(os.path.join(ROOT, "game", "sprites_src", "title"),
                    os.path.join(root, "game", "sprites_src", "title"))
    return root


def test_the_real_tree_passes_with_a_256x240_frame(measured):
    assert measured["pass"], measured["failures"]
    assert measured["frame"] == [check_nes_limits.FRAME_W, check_nes_limits.FRAME_H]
    assert measured["config_frame"] == [check_nes_limits.FRAME_W, check_nes_limits.FRAME_H]
    assert measured["rooms"], "the measure found no room, so it measured nothing"
    for name, size in measured["rooms"].items():
        assert size == [check_nes_limits.FRAME_W, check_nes_limits.FRAME_H], "%s is %r" % (name, size)


def test_the_colour_count_is_the_one_it_lists(measured):
    """The count is the length of the list it prints, and every entry is a colour, never an index."""
    assert measured["colours"] == len(measured["colour_list"])
    assert measured["colours"] == len(set(measured["colour_list"])), "a colour is counted twice"
    assert measured["colours"] <= check_nes_limits.COLOUR_LIMIT, measured["colour_list"]
    for colour in measured["colour_list"]:
        assert HEX.match(colour), "%r is not a #rrggbb colour" % (colour,)


def test_a_room_off_the_frame_is_named(tmp_path):
    root = _skeleton(tmp_path)
    room = os.path.join(root, check_nes_limits.ROOMS, "rm_pp_title", "rm_pp_title.yy")
    with open(room, "r", encoding="utf-8-sig") as handle:
        body = handle.read()
    body = body.replace('"Height": 240', '"Height": 200', 1)
    with open(room, "w", encoding="utf-8") as handle:
        handle.write(body)

    failures = check_nes_limits.check(root)
    assert any("rm_pp_title" in line and "not 256x240" in line for line in failures), failures


def test_a_frame_macro_off_the_frame_is_named(tmp_path):
    root = _skeleton(tmp_path)
    config = os.path.join(root, check_nes_limits.CONFIG)
    with open(config, "r", encoding="utf-8-sig") as handle:
        text = handle.read()
    text = text.replace("#macro PP_FRAME_H 240", "#macro PP_FRAME_H 200", 1)
    with open(config, "w", encoding="utf-8") as handle:
        handle.write(text)

    failures = check_nes_limits.check(root)
    assert any("PP_FRAME_H" in line and "200" in line for line in failures), failures


def test_too_many_colours_is_refused(monkeypatch):
    """The rule itself: 17 colours against the limit of 16, with the colours printed so the job has a size."""
    seventeen = {(index, index, index) for index in range(17)}
    monkeypatch.setattr(check_nes_limits, "title_screen", lambda root: (check_nes_limits.FRAME_W,
                                                                       check_nes_limits.FRAME_H, seventeen))
    result = check_nes_limits.measure(ROOT)
    assert not result["pass"]
    assert any("17 colours" in line and "limit is 16" in line for line in result["failures"]), result["failures"]
    assert "#101010" in result["failures"][0], "the failure does not print the colours it counted"


def test_an_unreadable_tree_is_refused_not_passed(tmp_path):
    """A tree with no pp_config.gml is a tree this check cannot see, so it must not read as a passing tree."""
    root = str(tmp_path / "empty")
    os.makedirs(root)
    failures = check_nes_limits.check(root)
    assert failures, "a tree with no config passed"
    assert any(check_nes_limits.CONFIG.replace("/", os.sep) in line or
               check_nes_limits.CONFIG in line for line in failures), failures


def test_the_verdict_line_starts_with_the_badge_word(measured):
    """The badge prints PASS, so the line the check log carries starts with the same word."""
    assert check_nes_limits.verdict_line(measured).startswith("PASS ")
    assert "256x240" in check_nes_limits.verdict_line(measured)
    failing = {"pass": False, "failures": ["the title screen can show 17 colours"], "frame": [256, 240],
               "colours": 17, "limit": 16}
    assert check_nes_limits.verdict_line(failing).startswith("FAIL ")
