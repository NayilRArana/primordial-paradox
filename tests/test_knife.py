#!/usr/bin/env python3
"""Pins for Dad's Good Knife (card PP-KNIFE, t_503707c8).

Nayil's order: Zeus fights with a knife. What that means in this tree, measured before anything was written:
nothing named a starting weapon at all. data/items.json held one consumable, data/characters/party.json named no
weapon, and the FIGHT command resolved from the timing bar alone with the line "* You strike for N.". The only
weapon named for Zander anywhere was the thunderbolt, and that is his god form's power and the decoration in
data/intro_stars.json, which the card forbids touching. So this card ADDS the weapon row and moves the wording, and
it moves no number.

What these tests hold down, in five groups:

  1. ONE ID, ONE ROW. The party names the weapon by id, the row exists, and the name lives in that row's `name`
     field and nowhere else in the tree, so a rename is one edit.
  2. BALANCE DOES NOT MOVE. The row's damage band equals PP_FIGHT_DAMAGE_MIN and PP_FIGHT_DAMAGE_MAX as
     pp_config.gml declares them, one hit at 100 percent, which is what the bar already gave.
  3. THE LINES ARE DATA. The director fills {name} and {damage} from the row, prints the plain line only when there
     is no weapon, and never carries the knife's name in GML.
  4. THE SWING IS DRAWN. The slash walks the frames the row names, one frame every PP_SLASH_FRAME_STEPS steps of the
     FIGHT message, over the enemy's own slot, between the party draw and the HUD.
  5. THE ART REACHES THE BUILD. Four 16x16 frames in one 3 colour palette plus transparency, mirrored by
     tools/sync_art.py, listed in the .yyp, and the folder named by tools/check_build_inputs.py.

No em dash or en dash anywhere in this file: the project refuses them at the door (tests/test_project.py).

Run: python -m pytest tests/test_knife.py -q
"""

from __future__ import annotations

import json
import os
import re
import sys

import pytest
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import sync_art  # noqa: E402  the mirror rules themselves, never a copy of them

DIRECTOR = os.path.join(ROOT, "game", "scripts", "pp_battle_director", "pp_battle_director.gml")
CONFIG = os.path.join(ROOT, "game", "scripts", "pp_config", "pp_config.gml")
FONT = os.path.join(ROOT, "game", "scripts", "pp_font", "pp_font.gml")
ITEMS = os.path.join(ROOT, "data", "items.json")
PARTY = os.path.join(ROOT, "data", "characters", "party.json")
WEAPONS = os.path.join(ROOT, "game", "sprites_src", "weapons")
SHEET = os.path.join(WEAPONS, "spr_pp_knife.png")
SIDECAR = os.path.join(WEAPONS, "spr_pp_knife.json")
YPP = os.path.join(ROOT, "game", "PrimordialParadox.yyp")

# Text files that are history rather than definition: a rename is allowed to survive in the changelog and in the
# study library, which is what "the old name only in history" means.
HISTORY = ("DEVLOG.md", "EVENT-LOG.md", "knowledge/study/", "knowledge/PROVENANCE.md", "output/", "cache/",
           "data/ai_cache/", ".git/", "__pycache__/", ".bak", "tests/test_knife.py")


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def load(path: str) -> dict:
    return json.loads(read(path))


def body(name: str, path: str = DIRECTOR) -> str:
    """One GML function's body, from its `function name(` to the closing brace at the start of a line."""
    text = read(path)
    start = text.find("function %s(" % name)
    assert start >= 0, "%s is not in %s" % (name, os.path.basename(path))
    end = text.find("\n}", start)
    assert end > start, "%s has no top level closing brace" % name
    return text[start:end]


def macro(name: str) -> int:
    match = re.search(r"^#macro\s+%s\s+(-?\d+)\s*$" % re.escape(name), read(CONFIG), re.MULTILINE)
    assert match, "%s is not a macro in pp_config.gml" % name
    return int(match.group(1))


def hero() -> dict:
    for row in load(PARTY)["characters"]:
        if row["id"] == "hero":
            return row
    raise AssertionError("data/characters/party.json has no hero")


def item(item_id: str) -> dict:
    for row in load(ITEMS)["items"]:
        if row["id"] == item_id:
            return row
    raise AssertionError("data/items.json has no item %r" % item_id)


def knife() -> dict:
    return item(hero()["weapon"])


def sidecar() -> dict:
    return load(SIDECAR)


def index_entries() -> dict:
    return {entry["name"]: entry for entry in sync_art.source_entries()}


# ---- 1. One id, one row -------------------------------------------------------------------------------------------

def test_the_party_names_its_weapon_by_id_and_the_row_is_a_weapon():
    named = hero().get("weapon")
    assert isinstance(named, str) and named != "", "the hero names no weapon, so a FIGHT has nothing to brandish"
    row = item(named)
    assert row.get("kind") == "weapon", "%r is not a weapon row, it is %r" % (named, row.get("kind"))


def test_the_name_lives_in_one_field_the_engine_reads():
    """The card's rule: keep the name in one data field everything else reads. So the name is one row's `name` field
    in data/items.json, no GML carries it, and no second data file defines an item by it. Prose is allowed to say it:
    the S1 scene has Kronos packing the case and calling it what it is (authoring/dialogue/s1_move_in.json), and a
    character saying the name is the point, not a second definition of it."""
    name = knife()["name"]
    assert name == "Dad's Good Knife", "the working name changed; PP-SCENES-1 picks the final one, not this card"

    named = [row["id"] for row in load(ITEMS)["items"] if row.get("name") == name]
    assert named == [knife()["id"]], "the name is carried by %s, so it is not one field" % named

    in_gml = []
    for base, _dirs, files in os.walk(os.path.join(ROOT, "game")):
        for fname in files:
            if not fname.endswith(".gml"):
                continue
            path = os.path.join(base, fname)
            if name in read(path):
                in_gml.append(os.path.relpath(path, ROOT))
    assert in_gml == [], "the knife's name is in GML (%s), so data is no longer the one place it lives" % in_gml


def test_no_file_names_the_old_god_form_weapon_as_the_starting_weapon():
    """The thunderbolt is Zander's god form and the constellation in data/intro_stars.json, and the card forbids
    touching that decoration. The knife is a separate row, so the two must not be the same id."""
    star_file = load(os.path.join(ROOT, "data", "intro_stars.json"))
    shapes = [group.get("name", "") for group in star_file.get("shapes", [])]
    assert "thunderbolt" in shapes, "the intro star file no longer draws a thunderbolt; this pin needs rereading"
    assert knife()["id"] != "thunderbolt"
    assert knife()["id"] != "bolt"


# ---- 2. Balance does not move -------------------------------------------------------------------------------------

def test_the_weapon_row_carries_the_numbers_the_fight_bar_already_gave():
    row = knife()
    assert row["damage_min"] == macro("PP_FIGHT_DAMAGE_MIN"), "the knife moved the damage floor"
    assert row["damage_max"] == macro("PP_FIGHT_DAMAGE_MAX"), "the knife moved the damage ceiling"
    assert row["hits"] == 1, "the knife is one hit; JRPG-MECHANICS decision 4 gives sickle and bolt one hit"
    assert row["hit_chance"] == 100, "a knife that can miss is a balance change this card may not make"


def test_the_party_health_and_multiplier_are_untouched():
    row = hero()
    assert row["max_hp"] == 20 and row["will_max"] == 3 and row["power_multiplier"] == 1.0
    assert row["starting_items"] == [{"id": "salve", "count": 2}], "the starting items changed, which is not this card"


def test_the_item_file_still_carries_a_working_consumable():
    salve = item("salve")
    assert salve["heal"] == 6 and salve["max_carry"] == 8


# ---- 3. The lines are data ----------------------------------------------------------------------------------------

def test_the_director_fills_the_lines_from_the_row_and_keeps_the_name_out_of_gml():
    text = read(DIRECTOR)
    assert "Dad's Good Knife" not in text, "the knife's name is in GML, so data is no longer the one place it lives"
    fill = body("pp_battle_line_fill")
    assert 'string_replace_all(_out, "{name}", pp_battle_weapon_name(_battle))' in fill
    assert 'string_replace_all(_out, "{damage}", string(_damage))' in fill


def test_the_fight_message_is_the_rows_own_lines():
    lines = body("pp_battle_fight_lines")
    assert 'variable_struct_exists(_w, "attack_line")' in lines
    assert 'variable_struct_exists(_w, "damage_line")' in lines
    assert "_plain" in lines, "a fight with no weapon needs a line, or it opens an empty board"
    resolve = body("pp_battle_step_resolve")
    assert "pp_battle_say(_battle, pp_battle_fight_lines(_battle, _damage), \"enemy_turn\")" in resolve, \
        "the FIGHT resolve no longer prints the weapon's own lines"


def test_the_two_lines_are_deadpan_and_carry_the_narration_marker():
    row = knife()
    for field in ("attack_line", "damage_line"):
        line = row[field]
        assert line.startswith("* "), "%s does not open with the narration marker spec 19 Q6 gives every line" % field
        assert line.endswith("."), "%s does not end on a full stop" % field
    assert "{name}" in row["attack_line"], "the attack line must read the name from the field, not from a copy"
    assert "{damage}" in row["damage_line"], "the damage line must carry the number the fight rolled"
    assert row["description"].endswith("."), "the one line item description ends on a full stop"
    assert "{" not in row["description"], "the description is printed as it stands, so it takes no token"


def test_the_old_weapon_wording_is_not_in_live_code():
    """The card's grep check, held down as a test rather than as a command someone has to remember to run. The line the
    FIGHT command printed before the knife, `* You strike for N.`, is allowed to survive in the changelog and in the
    repo's own voice study (DEVLOG.md, knowledge/VOICE-PUNCHUP-1.md, which is where the replacement came from), and
    nowhere in the code or the data the game ships."""
    old = "You strike for"
    hits = []
    for folder in ("game", "data"):
        for base, _dirs, files in os.walk(os.path.join(ROOT, folder)):
            for fname in files:
                if not fname.endswith((".gml", ".json")):
                    continue
                path = os.path.join(base, fname)
                if old in read(path):
                    hits.append(os.path.relpath(path, ROOT))
    assert hits == [], "the pre knife wording is in live code: %s" % hits

    # And the fallback a fight with no weapon prints is the voice study's own replacement, not a second new line.
    assert 'var _plain = "* You swing for " + string(_damage) + ". No comment.";' in body("pp_battle_fight_lines")


def test_nothing_in_the_rows_text_is_blood_or_gore():
    row = knife()
    text = " ".join(row[field] for field in ("name", "description", "attack_line", "damage_line")).lower()
    for word in ("blood", "bleed", "gore", "guts", "wound", "sever", "dismember"):
        assert word not in text, "%r is in a line the card forbids" % word


def test_every_character_the_rows_text_prints_is_in_the_font():
    order = re.search(r"function pp_font_glyphs\(\)\s*\{\s*return\s+\"(.*?)\";", read(FONT), re.S).group(1)
    row = knife()
    printed = " ".join(row[field] for field in ("name", "description", "attack_line", "damage_line"))
    printed = printed.replace("{name}", "NAME").replace("{damage}", "8")
    missing = sorted({char for char in printed if char not in order})
    assert missing == [], "these characters would draw as spaces: %s" % missing


# ---- 4. The swing is drawn ----------------------------------------------------------------------------------------

def test_the_slash_walks_the_frames_the_row_names():
    swing = body("pp_battle_slash_frame")
    assert 'variable_struct_exists(_w, "slash_frames")' in swing
    assert "_battle.phase_steps div PP_SLASH_FRAME_STEPS" in swing, "the swing no longer advances with the message"
    assert "_battle.action != PPCommand.fight" in swing, "the swing must be the FIGHT command's, not any command's"
    assert "_battle.phase != PPBattlePhase.message" in swing, "the swing only runs while the turn's board is open"
    assert "return 0;" in swing, "the swing needs an off state, and 0 is the icon's own frame"
    steps = macro("PP_SLASH_FRAME_STEPS")
    assert 1 <= steps <= 12, "a step count outside 1..12 either strobes or freezes the swing at 60 fps"
    frames = knife()["slash_frames"]
    assert len(frames) >= 2, "the card asks for 2 or 3 slash frames"
    assert 1 not in [0] and all(frame >= 1 for frame in frames), "frame 0 is the icon, so a slash frame is 1 or up"
    assert frames == [fact["index"] for fact in sidecar()["frames_detail"] if fact["name"].startswith("slash")], \
        "the item's slash_frames and the sheet's frame order disagree"


def test_the_swing_is_drawn_over_the_enemy_slot_between_the_party_and_the_hud():
    draw = body("pp_battle_draw")
    order = [draw.find("pp_battle_draw_enemy(_battle, _enemy_slot)"),
             draw.find("pp_battle_draw_party(_battle)"),
             draw.find("pp_battle_draw_slash(_battle, _enemy_slot)"),
             draw.find("pp_font_draw_centre(_battle.enemy.name")]
    assert all(index >= 0 for index in order), "one of the four draws is gone from pp_battle_draw"
    assert order == sorted(order), "the swing must draw after the party and before the enemy's name"
    slash = body("pp_battle_draw_slash")
    assert "PP_UNTINTED" in slash, "the sheet's own three colours are the strip's palette, so no tint"
    assert '_slot.x + (_slot.w - 16) div 2' in slash, "the swing must sit inside the enemy's own slot"


def test_the_menu_says_what_the_hand_is_holding():
    menu = body("pp_battle_draw_menu")
    assert 'pp_battle_weapon_name(_battle)' in menu, "the menu row no longer reads the weapon from data"
    assert '"HELD: "' in menu
    row = knife()
    assert len("HELD: " + row["name"]) <= 28, "the band's bottom line holds 28 columns at the 8 px pitch"


# ---- 5. The art reaches the build ---------------------------------------------------------------------------------

def test_the_sheet_is_four_sixteen_pixel_frames_in_one_palette():
    facts = sidecar()
    assert (facts["frame_w"], facts["frame_h"], facts["frames"]) == (16, 16, 4)
    assert facts["frame_roles"] == {"icon": 0, "slash_frames": [1, 2, 3]}
    assert len(facts["sprite_palettes_used"]) == 1, "the card asks for ONE sprite palette for the icon and the swing"
    assert facts["colour_count"] == 3, "one palette of 3 colours plus transparency"
    with Image.open(SHEET) as image:
        assert image.size == (64, 16), "the sheet is four frames in one row"


def test_every_eight_by_eight_tile_carries_three_colours_or_fewer():
    with Image.open(SHEET) as image:
        pixels = image.convert("RGBA").load()
        for tile_y in range(2):
            for tile_x in range(8):
                seen = set()
                for y in range(tile_y * 8, tile_y * 8 + 8):
                    for x in range(tile_x * 8, tile_x * 8 + 8):
                        r, g, b, a = pixels[x, y]
                        if a:
                            seen.add((r, g, b))
                assert len(seen) <= 3, "tile %d,%d carries %d opaque colours" % (tile_x, tile_y, len(seen))


def test_the_sheet_wears_the_triple_the_strip_reserves_for_zander():
    reserved = load(os.path.join(ROOT, "data", "scene_palettes.json"))["hero_palettes"]["zander"]["colours"]
    used = [row["index"] for row in sidecar()["colours_used"]]
    assert sorted(used) == sorted(reserved), "the sheet wears %s, the reserved hero triple is %s" % (used, reserved)


def test_the_mirror_carries_the_sheet_into_the_build():
    entry = index_entries().get("spr_pp_knife")
    assert entry, "spr_pp_knife is not in the art index, so the swing draws nothing"
    assert (entry["frame_w"], entry["frame_h"], entry["frames"]) == (16, 16, 4)
    assert os.path.abspath(sync_art.WEAPON_SRC) in [os.path.abspath(folder) for folder in sync_art._folders()]


def test_the_committed_project_ships_the_sheet():
    assert '"name": "spr_pp_knife.png"' in read(YPP), "spr_pp_knife.png is not an Included File of the project"


def test_the_build_input_checker_names_the_weapon_folder():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "pp_check_build_inputs_knife", os.path.join(TOOLS, "check_build_inputs.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    named = [os.path.abspath(folder) for folder in module.ART_SOURCES]
    assert os.path.abspath(WEAPONS) in named, "the weapon folder is mirrored but not named in ART_SOURCES"
