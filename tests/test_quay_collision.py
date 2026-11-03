"""Final scope 2026-11-03, items 2, 3 and 8 (the WORLD role): the Town Quay collision, the hero's height and the storm.

Pins, on the committed data and the shipped GML:
  collision   tools/quay_collision_audit.py is clean: no drawn solid tile walkable, no ground tile blocked, no story tile,
              no walkable tile on the map edge, only doors (and the two overhead crane tiles) walkable among structures;
              the committed room equals a fresh build of the generator (so the layout cannot undo the fix)
  feet box    10x8 at the feet; a walker pushed into every kind of wall stops with at most half of him drawn over it
  height      the hero sheet and every sheet pp_overworld.gml draws a person from are 16 px tall, the sailors' height
  storm       pp_storm.gml is hooked into the overworld once each way, only for the quay, draws no alpha blend, asks only
              for roles the quay palette set declares, and its dither mask and thunder cue exist
"""
import io
import json
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import quay_collision_audit as audit  # noqa: E402
import walker_bot  # noqa: E402
import make_quay_town  # noqa: E402

OVERWORLD = os.path.join(ROOT, "game", "scripts", "pp_overworld", "pp_overworld.gml")
STORM = os.path.join(ROOT, "game", "scripts", "pp_storm", "pp_storm.gml")
CHARS = os.path.join(ROOT, "game", "sprites_src", "chars")


def read(path):
    with io.open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def code(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return "\n".join(line.split("//")[0] for line in text.splitlines())


def test_the_audit_is_clean_for_the_quay():
    result = audit.audit()
    assert audit.problems(result) == [], audit.problems(result)
    assert result["hero"]["feet_w"] == 10 and result["hero"]["feet_h"] == 8


def test_no_tile_is_story_blocked_and_the_bollard_is_solid():
    room = audit.room()
    assert not any("2" in row for row in room["collision"])
    assert room["collision"][8][8] == "1"


def test_the_top_row_is_an_edge_guard():
    assert set(audit.room()["collision"][0]) == {"1"}


def test_the_generator_builds_the_committed_collision():
    built = make_quay_town.build_all()
    assert built["room"]["collision"] == audit.room()["collision"]
    assert built["room"]["tiles"] == audit.room()["tiles"]


def test_a_walker_pushed_into_a_wall_leaves_at_most_half_of_him_over_it():
    room = audit.room()
    coll = room["collision"]
    tile = walker_bot.TILE
    checked = 0
    for ty in range(1, room["height"]):
        for tx in range(room["width"]):
            if coll[ty][tx] != "0" or coll[ty - 1][tx] != "1" or coll[ty][max(tx - 1, 0)] != "0" or coll[ty][min(tx + 1, 47)] != "0":
                continue
            px, py = tx * tile, ty * tile
            for _ in range(40):
                px, py, _moved, _hx, _hy = walker_bot.free_step(coll, px, py, 0, -1)
            top_of_feet = py + tile - walker_bot.FEET_H
            assert top_of_feet >= ty * tile, (tx, ty, py)          # the feet never enter the wall row
            over_the_wall = max(0, ty * tile - py)                   # figure rows above the tile he stands on
            assert over_the_wall <= tile - walker_bot.FEET_H, (tx, ty, over_the_wall)
            checked += 1
    assert checked > 30, checked


def test_every_person_the_overworld_draws_is_as_tall_as_the_sailor():
    src = read(OVERWORLD)
    sheets = re.findall(r'#macro PP_(?:HERO_SHEET8|HERO_SHEET|SAILOR_SHEET|PERCY_SHEET) "([a-z0-9_]+)"', src)
    assert set(sheets) >= {"zeus_ow_walk8", "zander_ow_v2", "sailor_ow_v2", "percy_ow_v2"}, sheets
    heights = {}
    for name in sheets:
        meta = json.loads(read(os.path.join(CHARS, name + ".json")))
        image = Image.open(os.path.join(CHARS, name + ".png"))
        assert image.height == meta["frame_h"], name
        heights[name] = meta["frame_h"]
    assert set(heights.values()) == {16}, heights
    assert "#macro PP_HERO8_DY 0" in src


def test_the_hero_sheet_keeps_eight_directions_of_two_frames():
    meta = json.loads(read(os.path.join(CHARS, "zeus_ow_walk8.json")))
    assert meta["frames"] == 16 and meta["frames_per_direction"] == 2 and len(meta["directions"]) == 8
    assert (meta["frame_w"], meta["frame_h"]) == (16, 16)


def test_the_storm_is_hooked_once_each_way_and_only_for_the_quay():
    src = code(read(OVERWORLD))
    assert src.count("pp_storm_step(_world);") == 1 and src.count("pp_storm_draw(_world);") == 1
    assert src.index("pp_map_draw_above(") < src.index("pp_storm_draw(_world);") < src.index("pp_dialogue_draw(_world.dialogue)")
    storm = code(read(STORM))
    assert '#macro PP_STORM_ROOM "southampton_town_quay"' in storm
    assert storm.count("if (!pp_storm_active(_world)) return;") == 2


def test_the_storm_blends_nothing_and_asks_only_for_roles_the_quay_declares():
    storm = code(read(STORM))
    for banned in ("draw_set_alpha", "merge_colour", "gpu_set_blendmode", "make_colour", "random("):
        assert banned not in storm, banned
    declared = [s for s in json.loads(read(os.path.join(ROOT, "data", "room_palettes.json")))["sets"] if s["id"] == "quay_night"][0]["roles"]
    asked = set(re.findall(r'pp_role_colour\("([a-z_0-9]+)"\)', storm))
    assert asked and asked <= set(declared), sorted(asked - set(declared))


def test_the_dither_mask_is_one_pixel_in_four_and_the_thunder_cue_exists():
    mask = Image.open(os.path.join(CHARS, "..", "title", "spr_pp_dither25.png")).convert("RGBA")
    drawn = [(x, y) for y in range(mask.height) for x in range(mask.width) if mask.getpixel((x, y))[3]]
    assert mask.size == (16, 16) and len(drawn) == 64 and all(x % 2 == 0 and y % 2 == 0 for x, y in drawn)
    assert "spr_pp_dither25" in read(STORM)
    audio = json.loads(read(os.path.join(ROOT, "data", "audio.json")))
    assert any(row.get("id") == "thunder_soft" for row in audio["cues"] if isinstance(row, dict)) or "thunder_soft" in json.dumps(audio)


def test_the_storm_script_is_registered_and_has_no_long_dash():
    yyp = read(os.path.join(ROOT, "game", "PrimordialParadox.yyp"))
    assert '"scripts/pp_storm/pp_storm.yy"' in yyp
    for path in (STORM, os.path.join(ROOT, "tools", "quay_collision_audit.py"), os.path.join(ROOT, "tools", "art", "make_storm_art.py")):
        assert chr(0x2013) not in read(path) and chr(0x2014) not in read(path), path
