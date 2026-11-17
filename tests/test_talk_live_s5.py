"""The S5 live record: the tool that writes it, and the drawing that reads it, agreeing without a model.

Judge panel 2026-11-17, fix 2 says shot S5's verdict has to be the bridge's, not a hand written effect, and that
data/meta_bake.json stays the fallback. tools/talk_live_s5.py asks the bridge and writes the answers down;
tools/demo_overlay.py reads the record and prints one line per turn. No test here calls a model: the bridge's answer
shape is a documented dict, so the tests build a record with the tool's own build_record out of fake answers and then
read it back through the drawing's own loader. What that proves is the seam, which is what breaks when either file
changes, and it costs nothing to run on a machine with no LM Studio and no key.
"""

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tests"))

import demo_overlay                                    # noqa: E402
import talk_live_s5                                    # noqa: E402


TURNS = [
    {"turn": 1, "row": "fight/morgan/1", "player_text": "May I see the form?", "effect": "soften",
     "mercy": 50, "text": "Captain Morgan takes the page."},
    {"turn": 2, "row": "fight/morgan/2", "player_text": "Lovely handwriting.", "effect": "nudge",
     "mercy": 35, "text": "Captain Morgan smooths the page flat."},
    {"turn": 3, "row": "fight/morgan/3", "player_text": "The captain is coming!", "effect": "setback",
     "mercy": 20, "text": "Captain Morgan stops reading."},
]


def answer(effect, source="open-weights", latency=900, verdict="persuaded"):
    return {
        "verdict": verdict,
        "effect": effect,
        "will_delta": 20 if effect == "soften" else 0,
        "reply": ["FORM FIRST."],
        "source": source,
        "origin": source,
        "mood": "warm",
        "model": "",
        "cached": False,
        "latency_ms": latency,
        "tried": [{"rung": source, "result": "answered"}],
    }


def record(answers):
    will_before = [0, 50, 85]
    will_after = [50, 85, 100]
    return talk_live_s5.build_record(TURNS, will_before, will_after, answers, ["cache", "local", "bake"],
                                     14.0, "v1", "http://127.0.0.1:51234/v1")


def test_the_record_is_not_written_under_data():
    """data/ is a build input and this record names an endpoint, so the tool must never write there."""
    relative = os.path.relpath(talk_live_s5.OUT_PATH, ROOT).replace("\\", "/")
    assert relative == "output/demo/talk_live_s5.json", "the record is a cut artifact, not game data"
    assert not relative.startswith("data/")
    assert demo_overlay.LIVE_RECORD_PATH == talk_live_s5.OUT_PATH, (
        "the drawing reads the file the tool writes")


def test_the_record_carries_the_effects_and_says_which_agree():
    built = record([answer("soften"), answer("soften"), answer("none", source="fallback")])
    assert built["kind"] == "talk_live_s5"
    assert [row["answer"]["effect"] for row in built["turns"]] == ["soften", "soften", "none"]
    assert [row["agrees"] for row in built["turns"]] == [True, False, False], (
        "turn 2 answered soften where the take moved nudge, and turn 3 answered nothing")
    assert built["live"] is False, "a fallback turn means the record is not all live"
    assert built["when"].endswith("Z") and "T" in built["when"], "the stamp is UTC"


def test_the_drawing_prints_the_record_the_tool_wrote(tmp_path, monkeypatch):
    """The seam: build_record's rows are what demo_overlay's loader accepts and what live_turn_line prints."""
    built = record([answer("soften", latency=938), answer("soften", latency=843),
                    answer("none", source="fallback", latency=1016)])
    path = tmp_path / "talk_live_s5.json"
    path.write_text(json.dumps(built), encoding="utf-8")
    monkeypatch.setattr(demo_overlay, "LIVE_RECORD_PATH", str(path))

    loaded = demo_overlay.load_live_record()
    assert loaded["turns"] == built["turns"]
    lines = demo_overlay.verdict_live_lines(loaded)
    assert lines == [
        "T1 SOFTEN MAY I SEE THE FORM? OPEN-WEIGHTS 938 MS",
        "T2 SOFTEN LOVELY HANDWRITING. OPEN-WEIGHTS 843 MS TAKE NUDGE",
        "T3 THE CAPTAIN IS COMING! FALLBACK 1016 MS TAKE SETBACK",
    ]

    bake, index = demo_overlay.load_bake(os.path.join(ROOT, "data", "meta_bake.json"))
    window = demo_overlay.plan("S5", bake, index, caption="", rows=(), verdict_box=True)["verdict_box"]
    texts = [line["source_text"] for line in window["lines"]]
    assert texts[:3] == lines, "the window is the record, in turn order"
    assert len(texts) == 6, "three turns and the three bake receipts"


def test_every_line_fits_the_window_and_the_font(tmp_path, monkeypatch):
    """The width the drawing enforces is len(text) * size against the window's inner width, measured on the lines."""
    built = record([answer("soften"), answer("nudge"), answer("setback")])
    path = tmp_path / "talk_live_s5.json"
    path.write_text(json.dumps(built), encoding="utf-8")
    monkeypatch.setattr(demo_overlay, "LIVE_RECORD_PATH", str(path))
    bake, index = demo_overlay.load_bake(os.path.join(ROOT, "data", "meta_bake.json"))
    window = demo_overlay.plan("S5", bake, index, caption="", rows=(), verdict_box=True)["verdict_box"]
    inner_right = window["rect"][2] - demo_overlay.PLATE_BORDER
    inner_bottom = window["rect"][3]
    for line in window["lines"]:
        assert line["box"][2] <= inner_right, "%r runs past the border" % line["source_text"]
        assert line["box"][3] <= inner_bottom, "%r runs past the bottom border" % line["source_text"]
        assert not any(dash in line["source_text"] for dash in demo_overlay.LONG_DASHES), line["source_text"]
    for line in window["lines"][:3]:
        assert line["source_text"] == line["source_text"].upper(), (
            "a turn line is the record's own words upper cased, so no lower case glyph reaches the frame")


def test_the_table_says_a_fallback_turn_is_not_an_agreement():
    built = record([answer("soften"), answer("soften"), answer("none", source="fallback")])
    out = "\n".join(talk_live_s5.table(built))
    assert "agrees yes" in out and "agrees no" in out
    assert "fallback" in out, "the rung is named beside the turn it answered"


def test_the_mercy_chain_is_the_encounters_own_numbers():
    """0, then the encounter's own soften 50, nudge 35 and setback 20, clamped to the meter's ends."""
    rows = [{"effect": "soften"}, {"effect": "nudge"}, {"effect": "setback"}]
    before, after = talk_live_s5.will_chain(rows, {"soften": 50, "nudge": 35, "setback": 20, "none": 0})
    assert before == [0, 50, 85]
    assert after == [50, 85, 100]


def test_a_file_that_is_not_a_record_is_refused_by_the_drawing(tmp_path, monkeypatch):
    path = tmp_path / "talk_live_s5.json"
    path.write_text(json.dumps({"kind": "talk_bake", "turns": []}), encoding="utf-8")
    monkeypatch.setattr(demo_overlay, "LIVE_RECORD_PATH", str(path))
    with pytest.raises(demo_overlay.OverlayError):
        demo_overlay.load_live_record()
