"""Card t_4d11b46d: the wind gate at the Southampton block exit, and the meter that explains it.

Nothing here runs GameMaker. The checks pin the new drawing to the data and the arithmetic the game already follows:

  1. the three tiles the gate stands on are the quay_bridge_wind trigger row, so the barrier is drawn exactly where
     the data already turns a walk back;
  2. the flag that opens it is morgan_resolved, the flag the morgan_gate encounter sets on the spare and on the kill;
  3. the storm draws the gate and the meter AFTER the eight step flash, so a flash cannot wipe them;
  4. the clock is the storm's own step count, and the bar is the mercy pp_battle_publish_outcome carries in
     global.pp.last_battle.mercy, so the map bar and the battle's WILL bar are one number.
"""

from __future__ import annotations

import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORM = os.path.join(ROOT, "game", "scripts", "pp_storm", "pp_storm.gml")
DIRECTOR = os.path.join(ROOT, "game", "scripts", "pp_battle_director", "pp_battle_director.gml")
OVERWORLD = os.path.join(ROOT, "game", "scripts", "pp_overworld", "pp_overworld.gml")


def read(path):
    with io.open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return handle.read()


def body(text, name):
    start = text.find("function %s(" % name)
    assert start >= 0, name
    return text[start:text.find("\n}", start)]


def load(*parts):
    return json.loads(read(os.path.join(ROOT, *parts)))


QUAY = [m for m in load("data", "maps", "all.json")["maps"] if m["id"] == "southampton_town_quay"][0]
WIND = sorted((t["x"], t["y"]) for t in QUAY["triggers"] if t["id"] == "quay_bridge_wind")
MORGAN = [e for e in load("data", "encounters", "all.json")["encounters"] if e["id"] == "morgan_gate"][0]


def test_the_gate_stands_on_the_wind_trigger_row():
    storm = read(STORM)
    x1 = int(re.search(r"^#macro PP_STORM_GATE_X1 (\d+)$", storm, re.M).group(1))
    x2 = int(re.search(r"^#macro PP_STORM_GATE_X2 (\d+)$", storm, re.M).group(1))
    y = int(re.search(r"^#macro PP_STORM_GATE_Y (\d+)$", storm, re.M).group(1))
    assert WIND == [(x, y) for x in range(x1, x2 + 1)], (WIND, x1, x2, y)
    assert len(WIND) == 3


def test_the_gate_opens_on_the_flag_the_fight_sets():
    assert "morgan_resolved" in MORGAN["flags_on_spare"]
    assert "morgan_resolved" in MORGAN["flags_on_kill"]
    storm = read(STORM)
    assert '#macro PP_STORM_GATE_FLAG "morgan_resolved"' in storm
    gate = body(storm, "pp_storm_gate_open")
    assert "pp_ledger_flag(global.pp_ledger, PP_STORM_GATE_FLAG)" in gate


def test_the_gate_is_drawn_shut_then_drawn_open_on_the_same_tiles():
    storm = read(STORM)
    draw = body(storm, "pp_storm_gate_draw")
    # the mouth is the three tiles, in screen space, from the camera the rest of the world uses
    assert "_gx = PP_STORM_GATE_X1 * PP_TILE - floor(_world.cam_x)" in draw
    assert "PP_STORM_GATE_Y * PP_TILE - floor(_world.cam_y)" in draw
    assert "_gw = (PP_STORM_GATE_X2 - PP_STORM_GATE_X1 + 1) * PP_TILE" in draw
    # shut: a dither cell over every 8x8 of the 48x16 mouth and the word on a tag beside it
    assert "while (_cy < 2)" in draw and "(_gw div 8)" in draw
    assert 'pp_font_draw_plated_centre("WIND", pp_storm_gate_tag_x(_gx, _gw, "WIND"), _gy + 4, 1)' in draw
    # open: the same posts, coping and tag position, a different word, no cells
    assert "if (_s.gate_open)" in draw
    opening = draw[draw.index("if (_s.gate_open)"):draw.index("var _on")]
    assert 'pp_font_draw_plated_centre("OPEN", pp_storm_gate_tag_x(_gx, _gw, "OPEN"), _gy + 4, 1)' in opening
    assert "spr_pp_dither" not in opening
    # the tag is placed by one function, east of the mouth, over the wall and off the walk
    tag = body(read(STORM), "pp_storm_gate_tag_x")
    assert "_gx + _gw + 4 + floor(pp_font_width(_text) / 2)" in tag


def test_the_storm_draws_the_gate_and_the_meter_after_the_flash():
    draw = body(read(STORM), "pp_storm_draw")
    flash = draw.index("_s.flash_left > 0")
    gate = draw.index("pp_storm_gate_draw(_world, _s)")
    hud = draw.index("pp_storm_hud_draw(_s)")
    assert flash < gate < hud
    tail = draw[gate:]
    assert tail.index("pp_storm_hud_draw(_s)") > tail.index("pp_storm_gate_draw(_world, _s)")


def test_the_clock_is_the_storms_own_step_count():
    hud = body(read(STORM), "pp_storm_hud_draw")
    assert "var _secs = _s.steps div 60;" in hud
    assert '"STORM " + string(_secs div 60) + ":" + string_format(_secs mod 60, 2, 0)' in hud
    assert "pp_font_draw_plated_centre(_clock" in hud


def test_the_wind_meter_is_the_mercy_the_fight_carried():
    publish = body(read(DIRECTOR), "pp_battle_publish_outcome")
    assert "global.pp.last_battle.mercy" in publish
    assert 'variable_struct_exists(_battle, "talk_mercy")' in publish
    flow = body(read(OVERWORLD), "pp_flow_battle_result")
    assert "global.pp.last_battle.mercy = _mercy" in flow

    storm = read(STORM)
    mercy = body(storm, "pp_storm_mercy")
    assert 'string(global.pp.last_battle.enemy) != "morgan"' in mercy
    assert "global.pp.last_battle.mercy" in mercy
    wind = body(storm, "pp_storm_wind")
    assert "return 100 - _m;" in wind
    hud = body(storm, "pp_storm_hud_draw")
    assert '"MERCY "' in hud and "pp_storm_mercy()" in hud and "pp_storm_wind()" in hud


def test_the_gate_change_did_not_grow_a_second_hook_or_a_long_dash():
    overworld = read(OVERWORLD)
    assert overworld.count("pp_storm_step(_world);") == 1 and overworld.count("pp_storm_draw(_world);") == 1
    for path in (STORM, DIRECTOR, OVERWORLD):
        text = read(path)
        assert chr(0x2013) not in text and chr(0x2014) not in text, path
