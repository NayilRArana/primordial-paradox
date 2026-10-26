"""Tests for the dodge arena's dim and its roles (card t_06ef8607).

Two defects, both measured on a real first fight before this file existed:

1. The dim was `draw_rectangle` at alpha 0.6 (spec 08 line 11's "60 percent black rectangle"). A band of alpha is a
   blended ramp: every pixel under it is a colour the 54 master entries do not name, and a real dodge frame of the
   2026-10-26 recording measured 0.6702 against the capture's 0.90 picture floor because of it
   (knowledge\\BATTLE-DIM-OFF-PALETTE-2026-10-26.md, card t_e92abcb0).

2. The arena asked for `hazard`, `marker` and `marker_trail`, and the set the demo fights in (`deck_day`) declares none
   of the three, so the dodge phase drew its hazards and the player's marker in PP_COLOUR_MISSING magenta
   (build\\first_fight_talk_game.log:88 to :90).

What is pinned here is the rule, not the picture:

  test_the_dodge_dim_is_a_dither_and_not_a_blend        no alpha in pp_arena_draw, the tiled mask is what it draws
  test_the_mask_is_the_half_checker_spec_13_allows      the sheet really is a 1 px 50 percent checker of one colour
  test_the_mask_reaches_the_build                       sync_art indexes it, so the runtime can load it
  test_the_arena_asks_only_for_roles_every_set_carries  no role the room set cannot resolve, ever again
  test_the_marker_is_the_brightest_role_the_sets_carry  spec 08's "brightest palette colour" as a measurement
  test_the_spec_and_the_code_tell_the_same_story        spec 08's amended lines and this code cannot drift apart

Honest limit: none of this renders a frame. The draw is proven by the mask's own geometry and by the sim in
build\\_probe_battle_dim.py, and the appearance stays unproven until the next capture measures a dodge frame.
"""

from __future__ import annotations

import json
import os
import re

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARENA = "game/scripts/pp_dodge_arena/pp_dodge_arena.gml"
MASK_PNG = "game/sprites_src/title/spr_pp_dither.png"
MASK_JSON = "game/sprites_src/title/spr_pp_dither.json"

FRAME_W = 256
FRAME_H = 240
TILE = 16
MASK_RGB = (255, 255, 255)


def read(relative: str) -> str:
    with open(os.path.join(ROOT, *relative.split("/")), "r", encoding="utf-8-sig") as handle:
        return handle.read()


def read_json(relative: str):
    return json.loads(read(relative))


def gml_code_only(text: str) -> str:
    """Strip comments, so the rules are judged on code and a comment that names a role is not a call."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return "\n".join(line.split("//")[0] for line in text.splitlines())


def function_body(code: str, name: str) -> str:
    """The body of one GML function, by matching braces from its opening brace."""
    match = re.search(r"\bfunction\s+%s\s*\(" % re.escape(name), code)
    if not match:
        return ""
    start = code.find("{", match.end())
    depth = 0
    for index in range(start, len(code)):
        if code[index] == "{":
            depth += 1
        elif code[index] == "}":
            depth -= 1
            if depth == 0:
                return code[start:index + 1]
    return ""


def role_calls(code: str) -> set:
    """Every role name the module resolves through pp_role_colour."""
    return set(re.findall(r'pp_role_colour\s*\(\s*"([a-z0-9_]+)"\s*\)', code))


def luminance(hexv: str) -> float:
    raw = hexv.lstrip("#")
    channels = []
    for index in (0, 2, 4):
        c = int(raw[index:index + 2], 16) / 255.0
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def universal_roles() -> set:
    """The roles every palette set in data/room_palettes.json declares."""
    sets = [set(room_set["roles"]) for room_set in read_json("data/room_palettes.json")["sets"]]
    return set.intersection(*sets)


def test_the_dodge_dim_is_a_dither_and_not_a_blend():
    body = function_body(gml_code_only(read(ARENA)), "pp_arena_draw")
    assert body, "pp_arena_draw is gone"
    assert "draw_set_alpha" not in body, "the dodge dim sets an alpha again, and a band of alpha is a blended ramp"
    assert not re.search(r"\b0\.\d+\b", body), "a fractional alpha is back in the arena's draw"
    assert 'pp_art_draw_tiled("spr_pp_dither"' in body, "the dim does not draw the checker mask"
    assert 'pp_role_colour("ink")' in body, "the dim does not spend the room's ink role"


def test_the_mask_is_the_half_checker_spec_13_allows():
    with Image.open(os.path.join(ROOT, *MASK_PNG.split("/"))) as handle:
        image = handle.convert("RGBA")
    assert image.size == (TILE, TILE), "the mask is %dx%d" % image.size
    assert FRAME_W % TILE == 0 and FRAME_H % TILE == 0, "the tile does not divide the 256x240 frame"

    pixels = image.load()
    drawn = set()
    for y in range(TILE):
        for x in range(TILE):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            assert a == 255, "the mask has a partly transparent pixel at %d,%d" % (x, y)
            assert (r, g, b) == MASK_RGB, "the mask carries %r at %d,%d, and only the tint identity tints exactly" \
                                         % ((r, g, b), x, y)
            drawn.add((x, y))
    checker = {(x, y) for y in range(TILE) for x in range(TILE) if (x + y) % 2 == 0}
    assert drawn == checker, "the mask is not the one pixel 50 percent checker"
    assert len(drawn) * 2 == TILE * TILE, "the mask does not draw exactly half its pixels"

    meta = read_json(MASK_JSON)
    assert meta["name"] == "spr_pp_dither"
    assert (meta["frame_w"], meta["frame_h"], meta["frames"]) == (TILE, TILE, 1)
    assert meta["kind"] == "mask", "the sidecar does not declare a mask, so no checker knows the palette rule cannot apply"


def test_the_mask_reaches_the_build():
    import sync_art

    entries = {entry["name"]: entry for entry in sync_art.source_entries()}
    assert "spr_pp_dither" in entries, "sync_art does not index the mask, so the arena cannot load it"
    assert entries["spr_pp_dither"]["frame_w"] == TILE and entries["spr_pp_dither"]["frames"] == 1


def test_the_arena_asks_only_for_roles_every_set_carries():
    code = gml_code_only(read(ARENA))
    asked = role_calls(code)
    assert asked, "the arena asks for no roles at all"
    missing = sorted(asked - universal_roles())
    assert missing == [], ("the arena asks for %s, which not every room palette set declares: a role a set does not "
                           "carry draws PP_COLOUR_MISSING magenta" % ", ".join(missing))
    for gone in ("hazard", "marker", "marker_trail"):
        assert gone not in asked, "%r is back in the arena, and deck_day does not declare it" % gone


def test_the_marker_is_the_brightest_role_the_sets_carry():
    palette = read_json("data/palette.json")
    roles, colours = palette["roles"], palette["colours"]
    shared = universal_roles()
    ranked = sorted(((luminance(colours[roles[name]]), name) for name in shared), reverse=True)
    brightest = ranked[0][1]
    assert brightest == "text", "the brightest role every set carries is %r, and the arena's comment says text" % brightest

    body = function_body(gml_code_only(read(ARENA)), "pp_arena_draw")
    marker_draw = body[body.index('pp_role_colour("paper")'):] if 'pp_role_colour("paper")' in body else body
    assert 'pp_role_colour("text")' in marker_draw, "the marker is not drawn in the brightest shared role"
    for dimmer in ("dim", "paper", "ink"):
        assert luminance(colours[roles[brightest]]) > luminance(colours[roles[dimmer]]), \
            "%r is not brighter than %r" % (brightest, dimmer)


def test_the_spec_and_the_code_tell_the_same_story():
    spec = " ".join(read("specs/08-dodge-arena.md").split())
    assert "50 percent checker of the ink role" in spec, "spec 08 no longer states the dither the code draws"
    before_amendment, _, after = spec.partition("Amendment, 2026-10-26, card t_06ef8607. This line read")
    assert "60 percent black rectangle" not in before_amendment, \
        "spec 08 still asks for the rectangle the code no longer draws"
    assert "60 percent black rectangle" in after, "the amendment no longer records what the line used to say"
    for role in ("text", "dim", "paper"):
        assert role in spec, "spec 08 does not name the %r role the arena spends" % role
    code = gml_code_only(read(ARENA))
    for role in ("text", "dim", "paper", "ink"):
        assert 'pp_role_colour("%s")' % role in code, "the code no longer spends %r" % role
