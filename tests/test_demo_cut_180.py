"""The 180 second cut's overlay window, measured (cards t_bdb645a5 and t_746512f4).

The panel's fix 2 asks for the AI verdict, the three bake receipts and the network line to be on the frames of S5.
The drawing belongs to tools/demo_overlay.py; what this file holds down is the cut's own part of the promise: which
window tools/demo_cut_180.py composites, at which clocks, and that the rectangle it lays down is inside the picture,
clear of the game's dialogue box and clear of the battle HUD bands the card says have to stay visible behind it. The
clocks are read out of knowledge/DEMO-SCRIPT.md's S5 heading, which is the document that owns the shot's shape, so a
window that drifts out of the shot fails here instead of in a capture.

Card t_746512f4 replaced two short windows (receipts 1:23.4 to 1:44.0, network 1:41.0 to 1:44.0) with one window
over the whole shot, because a judge sampling one still every thirty seconds stepped over both of them: the panel's
own frames are at 15.0, 45.0, 75.0, 105.0, 135.0 and 165.0 s, and none of them falls inside either old window. The
rows below measure the replacement: one window, the whole clock, one rectangle carrying all four facts.

Run: python -m pytest tests/test_demo_cut_180.py -q
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
SCRIPT = os.path.join(ROOT, "knowledge", "DEMO-SCRIPT.md")
LEDGER = os.path.join(ROOT, "data", "receipts", "meta_receipts.jsonl")


def load_tool(name):
    path = os.path.join(TOOLS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def cut():
    return load_tool("demo_cut_180")


def clock(text):
    """"1:18.00" as 78.0 seconds."""
    minutes, seconds = text.split(":")
    return int(minutes) * 60 + float(seconds)


def shot_clock(shot, path=SCRIPT):
    """The shot's own clock, verbatim from the script's heading: '### S5, ... 1:18.00 to 1:50.00 (1,920 steps)'."""
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.startswith("### %s," % shot):
                continue
            found = re.search(r"(\d+:\d+\.\d+) to (\d+:\d+\.\d+)", line)
            assert found, "the %s heading carries no clock: %r" % (shot, line)
            return clock(found.group(1)), clock(found.group(2))
    raise AssertionError("%s has no '### %s,' heading" % (path, shot))


def ledger_newest(path=LEDGER):
    """The newest ledger line per receipt name, as the overlay's own reader takes it."""
    best = {}
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            best[row["name"]] = row
    return best


def test_the_one_window_the_cut_composites_runs_the_whole_s5_clock(cut):
    lo, hi = shot_clock("S5")
    assert (lo, hi) == (78.0, 110.0), "the script puts S5 at 1:18.00 to 1:50.00"
    assert len(cut.OVERLAY_WINDOWS) == 1, "one window, so a still taken anywhere in S5 lands inside it"
    shot, kind, start, end, rows = cut.OVERLAY_WINDOWS[0]
    assert (shot, kind) == ("S5", "verdict")
    assert (start, end) == (lo, hi), "the window is the shot: 1:18.00 to 1:50.00, not a slice of it"
    assert rows == (), "it carries no bake row: its words come from the header, the effects and the ledger"
    # The panel's own six sample clocks, measured against the window: every one inside S5 is inside the window.
    for sample in (78.0, 90.0, 105.0, 109.0):
        assert start <= sample <= end, "a still at %.1f s shows the window" % sample


def test_the_window_draws_the_three_ledger_receipts_and_their_numbers(cut):
    items = [item for item in cut.overlay_plan() if item["kind"] == "verdict"]
    assert len(items) == 1, "one rectangle carries all four facts"
    lines = items[0]["lines"]
    ledger = ledger_newest()
    for name in cut.demo_overlay.RECEIPT_PLATE_NAMES:
        carrying = [line for line in lines if name.upper() in line]
        assert len(carrying) == 1, "%s is printed once on the window" % name
        row = ledger[name]
        assert row["id"] in carrying[0], "the window prints the id of the receipt the ledger holds"
        assert str(row["value"]).split(".")[0] in carrying[0], "and the number that receipt backs"


def test_the_plan_lays_down_one_verdict_window(cut):
    items = cut.overlay_plan()
    assert [item["kind"] for item in items] == ["verdict"]
    assert items[0]["rows"] == [], "a window with no bake row prints no hash"
    assert items[0]["lines"][0] == "MUSE SPARK 1.3", "the model is named on the window"
    assert items[0]["lines"][-1].startswith("NETWORK "), "and the network line is the last thing on it"


def test_every_rectangle_is_inside_the_picture_and_clears_the_game_windows(cut):
    dialogue = cut.demo_overlay.scale_rect(cut.demo_overlay.DIALOGUE_BOX)
    for item in cut.overlay_plan():
        x1, y1, x2, y2 = item["rect"]
        assert 0 <= x1 < x2 <= cut.FRAME_W, "%s is outside the frame horizontally" % item["name"]
        assert 0 <= y1 < y2 <= cut.FRAME_H, "%s is outside the frame vertically" % item["name"]
        assert y2 <= dialogue[1], "%s covers the game's own dialogue box" % item["name"]
        for hud_name, game_rect in cut.demo_overlay.battle_hud_rects():
            assert not cut.demo_overlay.intersects(tuple(item["rect"]), cut.demo_overlay.scale_rect(game_rect)), \
                "%s covers %s" % (item["name"], hud_name)


def test_the_cut_says_which_receipts_it_draws_and_which_rows_it_does_not(cut):
    """The record beside the video must not claim a row receipt the bake does not hold, or hide the receipts it draws."""
    text = cut.RECEIPT_NOT_DRAWN
    assert "fight/morgan/1" in text, "the row receipts that are still refused are named"
    for name in ("meta.model_calls", "meta.live_rows", "meta.live_share_pct"):
        assert name in text, "and the three receipts the cut does draw are named"
    assert "fallback" in text, "and the window's own words about those rows are named"
    assert not any(dash in text for dash in (u"\u2014", u"\u2013", u"\u2012", u"\u2015"))


def test_the_cut_imports_and_plans_without_the_narrator_module(tmp_path):
    """The narrator is the assistant lane's module (card t_2514df86); the picture must not depend on it.

    Card t_b231fe46: a checkout that only builds the cut may not carry tools/demo_voiceover.py, and before this
    row the import at the top of the tool made that checkout unable to even plan. The module is blocked by name
    here rather than removed, so the test measures the guard the file really carries.
    """

    class Blocker:
        def find_spec(self, name, path=None, target=None):
            if name == "demo_voiceover":
                raise ImportError("blocked on purpose: a checkout without tools/demo_voiceover.py")
            return None

    blocker = Blocker()
    saved = sys.modules.pop("demo_voiceover", None)
    sys.meta_path.insert(0, blocker)
    try:
        module = load_tool("demo_cut_180")
        assert module.demo_voiceover is None, "the blocker did not hide the narrator module"
        assert module.voiceover_plan() == [], "a silent checkout still plans narrator rows"
        assert module.build_voiceover(str(tmp_path)) == (None, []), "a silent checkout still builds a track"
        assert module.narration_checks("absent.mp4", str(tmp_path), []) == [], "rows were measured with no narrator"
        assert module.voiceover_meta() == {}, "narrator settings were read with no narrator module"
        plan = module.title_card_plan()
        assert plan["clock"] and plan["seconds"] > 0, "the title card's own plan stopped working"
    finally:
        sys.meta_path.remove(blocker)
        if saved is not None:
            sys.modules["demo_voiceover"] = saved
