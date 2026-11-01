#!/usr/bin/env python3
"""Pins for the battle HUD readout and its refresh hook (card t_8dcd842f).

The first fight on the demo route could not be read: the party's hp and will were drawn by four separate sites that
each did their own division, the number the player needed was underneath the dodge arena for the whole of the phase
that takes hp away, and nothing outside a draw call could say what the screen was showing.

These tests hold down the four things this card changed:

  1. ONE READER. pp_battle_hud_state reads the fight's own fields (actor.hp, actor.max_hp, actor.will,
     actor.will_max, enemy_hp, enemy.max_hp, talk_mercy over the talk data's will.max), writes none of them back, and
     returns every fraction clamped to 0..1 with every maximum floored at 1.
  2. ONE HOOK. pp_battle_hud_refresh is called by the code that moves a number, logs "PP: hud ..." only when a
     number changed, and pp_battle_step runs a guard once a step so a meter written by another module still reaches
     the log.
  3. THE DODGE STRIP. The readout printed while the arena owns the field sits above the arena's own top edge (so no
     hazard can hide behind it), above the party panel it stands in for, inside the 256 x 240 frame, and it is drawn
     after the arena, which dims the whole frame first.
  4. THE PIXELS. The strip is composed here from the GML's own geometry, the project's own palette roles and the
     font sheet, and every 8 x 8 cell must read back as the character the reader's text asks for. That is the only
     reading of this card's "HP 20/20 is readable" a machine on this host can take: tools/idle_check.py refuses to
     open a game window while a desktop automation is resident, so a fresh take is not available to this run.

No em dash or en dash anywhere in this file: the project refuses them at the door (tests/test_project.py).

Run: python -m pytest tests/test_battle_hud.py -q
"""

from __future__ import annotations

import json
import os
import re

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRECTOR = os.path.join(ROOT, "game", "scripts", "pp_battle_director", "pp_battle_director.gml")
CONFIG = os.path.join(ROOT, "game", "scripts", "pp_config", "pp_config.gml")
LAYOUT = os.path.join(ROOT, "data", "ui_layouts.json")
PALETTE = os.path.join(ROOT, "data", "palette.json")
ROOM_PALETTES = os.path.join(ROOT, "data", "room_palettes.json")
FONT = os.path.join(ROOT, "game", "sprites_src", "title", "spr_pp_font8.png")

# The sheet's glyph order, from pp_font_glyphs. tools/check_font_coverage.py proves the PNG matches this string frame
# by frame, so a cell read back against it is a character and not a guess.
GLYPHS = " !\"'()*,-./0123456789:?ABCDEFGHIJKLMNOPQRSTUVWXYZ[]abcdefghijklmnopqrstuvwxyz"
CELL = 8
FRAME_W, FRAME_H = 256, 240

# The room the demo's first fight is fought in, from data/room_palettes.json's deck_day entry: the strip spends ink,
# dim and text, the three roles every set carries (card R48's rule, which this card does not move).
ROOM_SET = "deck_day"


def read(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def code_only(text):
    """Drop comments: the rules below judge calls, and the card's own prose names them."""
    return "\n".join(line.split("//")[0] for line in text.splitlines())


def function_body(code, name):
    """One GML function's body, by matching braces from its opening brace."""
    match = re.search(r"\bfunction\s+%s\s*\(" % re.escape(name), code)
    assert match is not None, "no function %s in the director" % name
    start = code.find("{", match.end())
    depth = 0
    for index in range(start, len(code)):
        if code[index] == "{":
            depth += 1
        elif code[index] == "}":
            depth -= 1
            if depth == 0:
                return code[start:index + 1]
    raise AssertionError("function %s never closes" % name)


def director():
    return code_only(read(DIRECTOR))


# --------------------------------------------------------------------------------------------------------------
# 1. One reader


def test_the_readout_has_one_reader_over_the_fights_own_fields():
    body = function_body(director(), "pp_battle_hud_state")
    for field in ("_battle.actor.hp", "_battle.actor.max_hp", "_battle.actor.will", "_battle.actor.will_max",
                  "_battle.enemy_hp", "_battle.enemy.max_hp", "_battle.talk_mercy"):
        assert field in body, "the reader does not read %s" % field
    # A second stats store is what the card forbids: nothing in the reader may write a field back.
    assert not re.search(r"_battle\s*\.\s*\w+\s*=(?!=)", body), "the reader writes a battle field"
    assert not re.search(r"_battle\s*\.\s*actor\s*\.\s*\w+\s*=(?!=)", body), "the reader writes an actor field"


def test_every_meter_is_a_clamped_ratio_with_a_floored_maximum():
    body = function_body(director(), "pp_battle_hud_state")
    for key in ("hp_frac", "will_frac", "mercy_frac", "enemy_frac"):
        assert re.search(r"%s:\s*clamp\(" % key, body), "%s is not clamped at the reader" % key
    # Four maxima, four floors: a data row holding a 0 cannot divide by zero.
    assert len(re.findall(r"max\(1,", body)) >= 4, "a maximum is not floored at 1"


def test_the_hp_line_is_the_formatted_text_the_card_asks_for():
    body = function_body(director(), "pp_battle_hud_state")
    hp = re.search(r'hp_text:\s*(.+?),?\n', body)
    will = re.search(r'will_text:\s*(.+?),?\n', body)
    assert hp is not None and will is not None, "the reader names no hp_text or will_text"
    assert '"HP "' in hp.group(1) and '"/"' in hp.group(1), "the hp line is not built as 'HP <hp>/<max>'"
    assert '"WILL "' in will.group(1) and '"/"' in will.group(1), "the will line is not built as 'WILL <will>/<max>'"


def test_every_draw_site_takes_its_numbers_from_the_reader():
    code = director()
    sites = ["pp_battle_draw", "pp_battle_draw_hud_field"]
    # The battle screen B panel and plate are another card's code and may not be in this commit; when they are, they
    # must read the same struct as the rest.
    for optional in ("pp_battle_draw_party_b", "pp_battle_draw_plate_b"):
        if re.search(r"\bfunction\s+%s\s*\(" % optional, code):
            sites.append(optional)
    for name in sites:
        body = function_body(code, name)
        assert "pp_battle_hud_state(_battle)" in body, "%s does not read the hud state" % name
        assert not re.search(r"/\s*max\(1,\s*_battle\.", body), "%s divides a value itself" % name


# --------------------------------------------------------------------------------------------------------------
# 2. One hook


def test_the_hook_logs_a_line_and_only_when_a_number_moved():
    body = function_body(director(), "pp_battle_hud_refresh")
    assert "_battle.hud = _hud" in body, "the hook does not store the state on the fight"
    assert "show_debug_message" in body and '"PP: hud "' in body, "the hook writes no hud line"
    for key in ("_last.hp == _hud.hp", "_last.will == _hud.will", "_last.enemy_hp == _hud.enemy_hp",
                "_last.mercy == _hud.mercy"):
        assert key in body, "the hook does not compare %s, so it would repeat its line every step" % key


def test_the_code_that_moves_a_number_calls_the_hook():
    code = director()
    calls = {
        "pp_battle_new": "fight start",
        "pp_battle_hurt_enemy": "enemy damage",
        "pp_battle_step_dodge": "party hit",
        "pp_battle_begin_action": "will spent",
    }
    for name, why in calls.items():
        body = function_body(code, name)
        assert 'pp_battle_hud_refresh(_battle, "%s")' % why in body, \
            "%s does not call the hook after it moves a number" % name


def test_the_step_runs_the_guard_so_a_meter_written_elsewhere_still_reaches_the_log():
    code = director()
    step = function_body(code, "pp_battle_step")
    assert "pp_battle_hud_guard(_battle)" in step, "the step runs no hud guard"
    guard = function_body(code, "pp_battle_hud_guard")
    assert "pp_battle_hud_refresh(_battle," in guard, "the guard never refreshes"
    for field in ("_last.hp", "_last.will", "_last.enemy_hp", "_last.mercy"):
        assert field in guard, "the guard does not watch %s" % field


# --------------------------------------------------------------------------------------------------------------
# 3. The dodge strip


def strip_geometry():
    body = function_body(director(), "pp_battle_hud_strip")
    match = re.search(r"return\s*\{(.+?)\}\s*;", body, re.S)
    assert match is not None, "pp_battle_hud_strip returns no struct literal"
    out = {}
    for key, value in re.findall(r"(\w+):\s*(-?\d+)", match.group(1)):
        out[key] = int(value)
    for key in ("x1", "y1", "x2", "y2", "text_x", "bar_x", "bar_w", "bar_h", "hp_y", "will_y"):
        assert key in out, "the strip does not name %s" % key
    return out


def arena_rect():
    code = read(CONFIG)
    numbers = {}
    for macro in ("PP_ARENA_CX", "PP_ARENA_CY", "PP_ARENA_W", "PP_ARENA_H"):
        match = re.search(r"#macro\s+%s\s+(-?\d+)" % macro, code)
        assert match is not None, "pp_config names no %s" % macro
        numbers[macro] = int(match.group(1))
    cx, cy = numbers["PP_ARENA_CX"], numbers["PP_ARENA_CY"]
    w, h = numbers["PP_ARENA_W"], numbers["PP_ARENA_H"]
    return cx - w // 2, cy - h // 2, cx - w // 2 + w, cy - h // 2 + h


def panel_rect():
    """The top row of the party readout on each screen the director can draw: the legacy stat row's y, parsed from
    the draw call itself, and the battle_b panel when the layout file still carries one. The panel is optional: an
    earlier card removed and re-added that row, so a test that required it would fail on a file change that is not
    this card's."""
    rows = []
    body = function_body(director(), "pp_battle_draw")
    legacy = re.search(r"_row_hud\.will_text,\s*16(\s*\+\s*_shake_x)?,\s*(\d+)", body)
    assert legacy is not None, "the legacy stat row's row is not where this test can read it"
    rows.append(("legacy stat row", int(legacy.group(2))))
    screens = json.loads(read(LAYOUT))["screens"]
    for screen in screens:
        if screen.get("name") == "battle_b":
            rows.append(("battle_b panel", screen["panel"]["y"] * CELL))
    return rows


def test_the_strip_is_above_the_arena_it_stands_in_for():
    strip = strip_geometry()
    ax1, ay1, ax2, ay2 = arena_rect()
    assert strip["y2"] < ay1, "the strip reaches row %d, and the arena starts at row %d" % (strip["y2"], ay1)
    assert strip["x1"] < ax2 and strip["x2"] > ax1, "the strip is not over the field the arena covers"


def test_the_strip_stands_clear_of_the_panel_and_inside_the_frame():
    strip = strip_geometry()
    for name, top in panel_rect():
        assert strip["y2"] < top, "the strip reaches row %d, and the %s starts at row %d" % (strip["y2"], name, top)
    assert 0 <= strip["x1"] < strip["x2"] < FRAME_W, "the strip is not inside the frame width"
    assert 0 <= strip["y1"] < strip["y2"] < FRAME_H, "the strip is not inside the frame height"


def test_the_strip_s_lines_and_bars_fit_inside_its_own_plate():
    strip = strip_geometry()
    for row in (strip["hp_y"], strip["will_y"]):
        assert row >= strip["y1"] + 2, "a text row starts on the plate's border"
        assert row + CELL - 1 <= strip["y2"] - 1, "a text row runs past the plate"
    assert strip["text_x"] >= strip["x1"] + 2, "the text starts on the plate's border"
    assert strip["text_x"] + 10 * CELL <= strip["bar_x"], "a ten character line would run into the meter"
    assert strip["bar_x"] + strip["bar_w"] - 1 <= strip["x2"] - 2, "the meter runs past the plate"
    for row in (strip["hp_y"] + 1, strip["will_y"] + 1):
        assert row + strip["bar_h"] - 1 <= strip["y2"] - 1, "a meter runs past the plate"


def test_the_strip_is_drawn_after_the_arena():
    body = function_body(director(), "pp_battle_draw")
    arena = body.find("pp_arena_draw(_battle.arena)")
    strip = body.find("pp_battle_draw_hud_field(_battle)")
    assert arena >= 0 and strip >= 0, "the director does not draw the arena and the strip"
    assert arena < strip, "the strip is drawn before the arena, which dims the whole frame first"


# --------------------------------------------------------------------------------------------------------------
# 4. The pixels


def role_colour(set_id, role):
    """The colour a room set resolves a role to, through data/palette.json's own index map, the way pp_role_colour
    does at run time. Read here rather than restated, so a palette edit moves this test with the game."""
    palette = json.loads(read(PALETTE))
    sets = json.loads(read(ROOM_PALETTES))["sets"]
    chosen = [entry for entry in sets if entry["id"] == set_id]
    assert chosen, "data/room_palettes.json has no %s set" % set_id
    assert role in chosen[0]["roles"], "the %s set does not carry the %s role" % (set_id, role)
    hex_code = palette["colours"][palette["roles"][role]]
    return tuple(int(hex_code[i:i + 2], 16) for i in (1, 3, 5))


def font_sheet():
    return Image.open(FONT).convert("RGBA")


def glyph_colour(sheet):
    """The one ink the sheet's glyphs are drawn in. The sheet is a single colour with alpha, so the most common
    non transparent value is the ink and it is used for every pixel the mask covers."""
    counts = {}
    for _, colour in sheet.getcolors(maxcolors=1 << 16):
        counts[colour] = counts.get(colour, 0) + colour[3]
    opaque = [colour for colour in counts if colour[3] > 0]
    assert opaque, "the font sheet is fully transparent"
    return max(opaque, key=lambda colour: counts[colour])


def text_parts(name):
    """The literal parts of one formatted line in the reader, so the expectation comes from the GML and not from a
    copy of it. 'HP ' + string(_hp) + '/' + string(_hp_max) has two literals: 'HP ' and '/'."""
    body = function_body(director(), "pp_battle_hud_state")
    line = re.search(r"%s:\s*(.+?),\n" % name, body)
    assert line is not None, "the reader names no %s" % name
    parts = re.findall(r'"([^"]*)"', line.group(1))
    assert len(parts) == 2, "%s is not two literals and two numbers" % name
    return parts


def compose_strip(hp, hp_max, will, will_max):
    """The dodge strip as the GML draws it: an ink plate, two lines of the sheet's glyphs, two meters."""
    strip = strip_geometry()
    ink = role_colour(ROOM_SET, "ink")
    dim = role_colour(ROOM_SET, "dim")
    fill = role_colour(ROOM_SET, "text")
    sheet = font_sheet()
    glyph_ink = glyph_colour(sheet)

    image = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 255))
    # The field behind the strip is whatever the scene puts there; the plate is what makes the numbers readable, so
    # the composition only has to hold the plate and what it carries.
    for x in range(strip["x1"], strip["x2"] + 1):
        for y in range(strip["y1"], strip["y2"] + 1):
            image.putpixel((x, y), ink + (255,))

    hp_parts, will_parts = text_parts("hp_text"), text_parts("will_text")
    lines = (
        (hp_parts[0] + str(hp) + hp_parts[1] + str(hp_max), strip["text_x"], strip["hp_y"]),
        (will_parts[0] + str(will) + will_parts[1] + str(will_max), strip["text_x"], strip["will_y"]),
    )
    for text, x, y in lines:
        for index, char in enumerate(text):
            glyph = GLYPHS.find(char)
            assert glyph >= 0, "%r is not in the font sheet" % char
            for gx in range(CELL):
                for gy in range(CELL):
                    pixel = sheet.getpixel((glyph * CELL + gx, gy))
                    if pixel[3] > 0:
                        image.putpixel((x + index * CELL + gx, y + gy), glyph_ink[:3] + (255,))

    fills = []
    for frac, y in ((hp / float(hp_max), strip["hp_y"] + 1), (will / float(will_max), strip["will_y"] + 1)):
        for x in range(strip["bar_x"], strip["bar_x"] + strip["bar_w"]):
            for row in range(y, y + strip["bar_h"]):
                image.putpixel((x, row), dim + (255,))
        count = int(strip["bar_w"] * max(0.0, min(1.0, frac)))
        if frac > 0 and count < 1:
            count = 1
        for x in range(strip["bar_x"], strip["bar_x"] + count):
            for row in range(y, y + strip["bar_h"]):
                image.putpixel((x, row), fill + (255,))
        fills.append(count)
    return image.convert("RGB"), [text for text, _x, _y in lines], fills


def read_cells(image, x, y, count):
    """Each 8 x 8 cell as a set of inked pixels, which is the character the sheet drew there."""
    ink = role_colour(ROOM_SET, "ink")
    glyph = glyph_colour(font_sheet())[:3]
    out = []
    for cell in range(count):
        marks = set()
        for gx in range(CELL):
            for gy in range(CELL):
                if image.getpixel((x + cell * CELL + gx, y + gy)) == glyph:
                    marks.add((gx, gy))
        assert ink != glyph, "the plate and the glyphs are the same colour, so nothing is readable"
        out.append(frozenset(marks))
    return out


def sheet_cells(text):
    sheet = font_sheet()
    out = []
    for char in text:
        glyph = GLYPHS.find(char)
        marks = set()
        for gx in range(CELL):
            for gy in range(CELL):
                if sheet.getpixel((glyph * CELL + gx, gy))[3] > 0:
                    marks.add((gx, gy))
        out.append(frozenset(marks))
    return out


def test_the_strip_pixels_read_back_as_the_lines_it_asks_for():
    image, lines, fills = compose_strip(20, 20, 3, 3)
    assert lines == ["HP 20/20", "WILL 3/3"], "the reader asks for %r" % (lines,)
    strip = strip_geometry()
    read_back = read_cells(image, strip["text_x"], strip["hp_y"], len(lines[0]))
    assert read_back == sheet_cells(lines[0]), "the hp line does not read back as %r" % lines[0]
    read_back = read_cells(image, strip["text_x"], strip["will_y"], len(lines[1]))
    assert read_back == sheet_cells(lines[1]), "the will line does not read back as %r" % lines[1]
    assert fills == [strip["bar_w"], strip["bar_w"]], "a full meter is not full"


def test_a_hit_changes_the_pixels_and_shortens_the_meter():
    strip = strip_geometry()
    full, full_lines, full_fills = compose_strip(20, 20, 3, 3)
    hurt, hurt_lines, hurt_fills = compose_strip(14, 20, 3, 3)
    assert hurt_lines[0] == "HP 14/20", "the reader asks for %r" % hurt_lines[0]
    read_back = read_cells(hurt, strip["text_x"], strip["hp_y"], len(hurt_lines[0]))
    assert read_back == sheet_cells(hurt_lines[0]), "the hit's line does not read back as %r" % hurt_lines[0]
    assert hurt_lines[0] != full_lines[0], "the line did not change"
    assert hurt_fills[0] < full_fills[0], "the hp meter did not shorten: %d against %d" % \
        (hurt_fills[0], full_fills[0])
    # The meter's own arithmetic: whole pixels of the track, the rule pp_battle_draw_meter states.
    assert hurt_fills[0] == int(strip["bar_w"] * 14 / 20.0), "the hp meter is not the ratio of the track"
    assert hurt_fills[1] == full_fills[1], "the will meter moved on a hit, which changes no will"


def test_an_empty_meter_still_shows_one_pixel_and_never_a_negative_fill():
    strip = strip_geometry()
    empty, _lines, fills = compose_strip(20, 20, 0, 3)
    assert fills[1] == 0, "zero will filled %d pixels" % fills[1]
    dim = role_colour(ROOM_SET, "dim")
    assert empty.getpixel((strip["bar_x"], strip["will_y"] + 1)) == dim, "the empty track is not the dim role"
    assert _lines[1] == "WILL 0/3", "the reader asks for %r" % _lines[1]
