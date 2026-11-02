#!/usr/bin/env python3
"""Pins for the demo route's battle room: the enemy is a sheet, and the backdrop is inside the palette (card t_021a589c).

The card was written from FIRST-FIGHT-FINDING-2026-10-26.md: the arena "renders the enemy as a plain white block" and
the backdrop "uses a deep blue that is off palette". Both claims are measurable, so neither is settled here by reading
the code and agreeing with it. tools/verify_battle_room.py composes the room out of the shipped art at the numbers
pp_battle_director.gml reads, and these tests hold its two measurements down:

  1. THE ENEMY IS THE SHEET. The slot the layout names carries navy_sailor's own frame 0 pixel for pixel, and no one
     colour covers the slot, which is what the placeholder block does.
  2. THE BACKDROP IS IN THE PALETTE. Every pixel of the strip the fight draws is within 12 of a colour the union of
     data/palette.json and data/nes_palette.json names, so there are zero off palette pixels, the deep blue among
     them.

The second pin is also a record of finding 3's correction (2026-10-27, card t_f3b7c557): the deep blue is
data/nes_palette.json entry 2 at distance 0, and the off palette reading came from the recorder's 4:2:0 chroma
subsampling, not from the art. A later card that repaints the strip to satisfy the stale half of the finding would
break test_the_deep_blue_is_a_palette_entry and be told why.

No em dash or en dash anywhere in this file: the project refuses them at the door (tests/test_project.py).

Run: python -m pytest tests/test_battle_room_sprites.py -q
"""

from __future__ import annotations

import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import verify_battle_room as room  # noqa: E402  the composition and the measurements, never a copy of them

DIRECTOR = os.path.join(ROOT, "game", "scripts", "pp_battle_director", "pp_battle_director.gml")
NES_PALETTE = os.path.join(ROOT, "data", "nes_palette.json")


@pytest.fixture(scope="module")
def report() -> dict:
    """The verifier's report, composed once: the composition reads the art and measures 43k pixels."""
    return room.verify()


def director_body(name: str) -> str:
    return room.body(name)


def nes_entries() -> set:
    with open(NES_PALETTE, "r", encoding="utf-8") as handle:
        return {text.lower() for text in json.load(handle)["colours"]}


# ---- 1. The room is the route's fight, resolved from data -------------------------------------------------------


def test_the_route_fight_is_the_sailor_on_the_deck(report):
    """data/slice.json's fight step, its encounter, its enemy row, the map's room palette and the strip, in one line."""
    fight = report["fight"]
    assert fight["route_step"] == "fight"
    assert fight["encounter"] == "tutorial_sailors"
    assert fight["enemy"] == "navy_sailor"
    assert fight["map"] == "ship_small"
    assert fight["room_set"] == "deck_day"
    assert fight["strip_stem"] == "deck_night", "the deck set no longer resolves to the deck strip"
    if fight["strip_upgrade_table"]:
        assert fight["strip_upgraded"] == "ship_deck", "the strip upgrade table no longer names the deck's own strip"
    else:
        assert fight["strip_upgraded"] == "deck_night", "with no upgrade table the fight draws the deck stem"
    assert report["strip_drawn"] in ("bg_battle_deck_night", "bg_battle_ship_deck"), \
        "the composition drew a strip that is neither the deck stem nor its upgrade"


def test_the_strip_and_the_enemy_sheet_are_both_in_the_art_index(report):
    """A name the index does not carry is a room the game draws with a rectangle instead of the art.

    The strip checked is the one the composition drew: `bg_battle_ship_deck` when the source tree carries the 2026-11-01
    upgrade, and the pre-upgrade stem when it does not, which is exactly what pp_battle_bg_sprite decides at run time.
    """
    index = room.art_index()
    strip = report["strip_drawn"]
    assert strip in index, "%s is not in the art index" % strip
    assert index[strip].get("kind") == "background", "%s is not indexed as a background strip" % strip
    assert index[strip]["frame_w"] == 256, "%s is not a full width strip" % strip
    assert report["strip_upgraded_in_source"] == ("bg_battle_" + report["fight"]["strip_upgraded"] in index)
    assert report["fight"]["enemy"] in index, "%s has no sheet in the art index" % report["fight"]["enemy"]


def test_the_enemy_sheet_is_the_size_the_slot_states(report):
    """pp_battle_draw_enemy draws one frame at 1:1, so a sheet that is not the slot's size would be cropped or stretched."""
    index = room.art_index()
    row = index[report["fight"]["enemy"]]
    slot = room.enemy_slot()
    assert (row["frame_w"], row["frame_h"]) == (slot["w"], slot["h"]), \
        "the enemy's sheet is not the size the layout's slot states"


# ---- 2. The enemy is the sheet, not the white block ---------------------------------------------------------------


def test_the_enemy_slot_carries_the_sheet_pixel_for_pixel(report):
    """The card's first claim, measured: every pixel the sheet paints is that pixel, and the slot is not one colour."""
    measured = report["claims"]["enemy_is_a_character_sheet_not_a_white_block"]["measured"]
    assert measured["flat_block"] is False, "the enemy slot is one flat colour, which is the placeholder block"
    assert measured["matches_sheet_share"] == 1.0, \
        "%d of the sheet's pixels did not land in the slot" % measured["sheet_painted_pixels"]
    assert 0.2 <= measured["sheet_painted_share"] <= 0.6, \
        "the sheet paints %.2f of its slot, which is not the figure the sailor's own frame paints" % \
        measured["sheet_painted_share"]
    assert measured["text_role_share"] == 0.0, \
        "the slot carries the text role the placeholder block paints, so the block is what drew"


def test_the_director_looks_the_sheet_up_before_it_draws_a_block():
    """The draw order inside the function is the claim: a sheet in the index is drawn, the block is the last resort.

    pp_battle_draw_enemy draws the art first and falls through to the rectangle only when pp_battle_enemy_sprite
    answered "", and that only answers "" when pp_art_has failed. Pinned as order, not as prose, because the two
    draws in the wrong order draw a block over the art.
    """
    draw = director_body("pp_battle_draw_enemy")
    art = draw.find("pp_art_draw(")
    block = draw.find("draw_rectangle(")
    assert art >= 0 and block >= 0, "pp_battle_draw_enemy no longer has both an art draw and a block"
    assert art < block, "the placeholder block is drawn before the enemy's sheet"
    assert "if (_name != \"\")" in draw, "the art draw is no longer guarded on a name the index answered"

    sprite = director_body("pp_battle_enemy_sprite")
    assert "pp_art_has(_name)" in sprite, "the resolver no longer asks the art index"
    assert sprite.find("pp_art_has(_name)") < sprite.find("return _name;"), \
        "the resolver answers a sheet name before it has asked the art index for it"
    assert 'return "";' in sprite, "the resolver no longer answers an empty name when the index has none"


# ---- 3. The backdrop is inside the palette, deep blue included ----------------------------------------------------


def test_the_backdrop_has_no_off_palette_pixel(report):
    """The card's second claim, measured on the strip the fight draws: zero pixels outside the two palette files."""
    measured = report["claims"]["backdrop_inside_the_palette"]["measured"]
    assert measured["off_palette_pixels"] == 0, \
        "the backdrop carries %d off palette pixels: %s" % (measured["off_palette_pixels"],
                                                           measured["off_palette_colours"])
    assert measured["on_union_share"] == 1.0
    assert measured["on_nes_share"] == 1.0, \
        "the backdrop is not all NES 2C02 colours, which is RULE 0 point 1"


def test_the_deep_blue_is_a_palette_entry(report):
    """Finding 3's deep blue, named and measured: #0000bc is data/nes_palette.json entry 2, at distance 0.

    It is NOT a colour of data/palette.json's 54 roles, and the report carries that number too (nearest_game), so the
    palette lane's open question stays visible instead of being quietly answered here.
    """
    measured = report["claims"]["backdrop_inside_the_palette"]["measured"]
    deep = measured["deep_blues"]
    assert "#0000bc" in deep, "the strip the fight draws no longer carries the deep blue finding 3 named"
    assert deep["#0000bc"]["pixels"] > 1000, "the deep blue is a handful of pixels, not the backdrop's own band"
    assert deep["#0000bc"]["nearest_nes"] == 0, "the deep blue is not a NES 2C02 entry"
    assert "#0000bc" in nes_entries(), "data/nes_palette.json no longer lists #0000bc"
    for colour, numbers in deep.items():
        assert numbers["nearest_nes"] <= room.PALETTE_TOLERANCE, \
            "%s is a deep blue outside data/nes_palette.json" % colour


def test_every_sheet_the_room_draws_is_on_palette(report):
    """The card's third constraint, measured: strip, enemy and the four party sheets, all on the union palette."""
    measured = report["claims"]["every_sheet_the_room_draws_is_on_palette"]["measured"]
    assert set(measured) == {report["strip_drawn"], "navy_sailor", "konrad_battle", "zander_battle",
                             "hadrian_battle"}, "the room's own sheet sweep changed its set"
    for name, numbers in measured.items():
        assert numbers["in_index"], "%s is not in the art index" % name
        assert numbers["off_palette_colours"] == {}, "%s carries off palette pixels: %s" % (
            name, numbers["off_palette_colours"])
        assert numbers["on_union_share"] == 1.0


def test_the_verifier_reads_the_gml_tables_instead_of_restating_them(report):
    """The strip is resolved by the game's own switch tables, so a re-armed table either changes the room or stops.

    pp_battle_bg_upgrade is read as optional: a checkout from before that card has no table, and the game then draws
    the pre-upgrade stem. Both trees are measured the same way, and the report says which one this is.
    """
    by_room = room.switch_table("pp_battle_bg_for_room")
    assert by_room.get("deck_day") == "deck_night"
    assert len(by_room) >= 3, "the room table lost its arms, so the composition would measure off the wrong strip"
    upgrade = room.switch_table_optional("pp_battle_bg_upgrade")
    assert report["fight"]["strip_upgrade_table"] == bool(upgrade)
    if upgrade:
        assert upgrade.get("deck_night") == "ship_deck"
        assert len(upgrade) >= 3
        assert report["fight"]["strip_upgraded"] == "ship_deck"
    else:
        assert report["fight"]["strip_upgraded"] == report["fight"]["strip_stem"], \
            "there is no upgrade table, so the drawn strip must be the room's own stem"
