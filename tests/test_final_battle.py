"""Pins for the BATTLE role of FINAL-SCOPE 2026-11-03: names (D1), weapons (D2), outcomes and disintegration (D3, C1).

No dash characters anywhere in this file (the project refuses them at the door).
Run: python -m pytest tests/test_final_battle.py -q
"""
from __future__ import annotations

import json
import os
import re

import pytest
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRECTOR = os.path.join(ROOT, "game", "scripts", "pp_battle_director", "pp_battle_director.gml")
CONFIG = os.path.join(ROOT, "game", "scripts", "pp_config", "pp_config.gml")
WEAPONS = os.path.join(ROOT, "game", "sprites_src", "weapons")
CHARS = os.path.join(ROOT, "game", "sprites_src", "chars")
YPP = os.path.join(ROOT, "game", "PrimordialParadox.yyp")


def read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def load(*parts):
    return json.loads(read(os.path.join(ROOT, *parts)))


def body(name):
    text = read(DIRECTOR)
    start = text.find("function %s(" % name)
    assert start >= 0, name
    return text[start:text.find("\n}", start)]


GODS = {"zander": ("spr_pp_master_bolt", 0x21, 0x31), "konrad": ("spr_pp_adamantine_scythe", 0x27, 0x00),
        "hadrian": ("spr_pp_bident", 0x23, 0x03), "percy": ("spr_pp_trident", 0x12, 0x28)}


def test_party_names_are_the_reincarnation_names():
    screen = [s for s in load("data", "ui_layouts.json")["screens"] if s["name"] == "battle"][0]
    assert [r["name"] for r in screen["party"]] == ["ZANDER", "KONRAD", "HADRIAN"]
    assert [r.split()[0] for r in screen["text"]["status_rows"]] == ["ZANDER", "KONRAD", "HADRIAN"]


def test_party_panel_fits_the_longest_name():
    panel = load("data", "ui_layouts.json")["battle_b"]["panel"]
    spans = []
    for i, name in enumerate(("ZANDER", "KONRAD", "HADRIAN")):
        c = panel["party_x"] + i * panel["party_step"] + panel["name_dx"]
        spans.append((c - len(name) * 4, c + len(name) * 4))
    for (_a0, a1), (b0, _b1) in zip(spans, spans[1:]):
        assert a1 + 4 <= b0
    assert spans[0][0] >= panel["x"] and spans[-1][1] + 4 <= panel["rule_x"]


def test_enemy_labels_and_plate_width():
    names = {e["id"]: e["name"] for e in load("data", "enemies", "all.json")["enemies"]}
    assert names["morgan"] == "CAPTAIN MORGAN" and names["percy"] == "PERCY"
    plate = load("data", "ui_layouts.json")["battle_b"]["plate"]
    assert len(names["morgan"]) * 8 <= plate["w"] * 8, "the label must fit the plate"


def test_outcome_contract_c1():
    record = body("pp_battle_record")
    assert "pp_battle_publish_outcome(_battle)" in record
    publish = body("pp_battle_publish_outcome")
    assert "global.pp.last_battle = { enemy: _enemy, outcome: _outcome };" in publish
    assert '"PP: battle outcome " + _enemy + " " + _outcome' in publish
    outcome = body("pp_battle_outcome")
    for word in ('"defeat"', '"spare"', '"kill"'):
        assert word in outcome


def test_quay_percy_cannot_be_interrupted_and_fights_on_the_quay():
    enc = {e["id"]: e for e in load("data", "encounters", "all.json")["encounters"]}
    assert enc["percy"].get("interrupt_off") is True
    assert enc["percy"]["background"] == "quay_town"
    ready = body("pp_battle_interrupt_ready")
    assert 'variable_struct_exists(_battle.encounter, "interrupt_off")' in ready


def test_kill_disintegrates_inside_the_message_phase():
    macros = dict(re.findall(r"^#macro\s+(PP_DISSOLVE_\w+)\s+(\d+)", read(CONFIG), re.M))
    assert 60 <= int(macros["PP_DISSOLVE_STEPS"]) <= 90, "60 to 90 frames asked for"
    enter = body("pp_battle_enter_result")
    assert "PPResult.kill" in enter and "pp_battle_dissolve_begin(_battle, _lines)" in enter
    assert enter.index("pp_audio_music_stop()") < enter.index("pp_battle_say(")
    assert "pp_battle_dissolve_step(_battle)" in body("pp_battle_step_message")
    begin = body("pp_battle_dissolve_begin")
    assert 'pp_audio_play("hit_heavy")' in begin and "PPBattlePhase.message" in begin
    assert "pp_battle_say(_battle, _battle.dissolve_lines" in body("pp_battle_dissolve_step")
    assert "pp_battle_draw_dissolve(" in body("pp_battle_draw_enemy_big")
    sfx = read(os.path.join(ROOT, "game", "scripts", "pp_audio", "pp_audio.gml"))
    assert '"hit_heavy"' in sfx and '"crit"' in sfx, "the sounds reused must be registered cues"


def test_dissolve_adds_no_phase_and_no_spare_animation():
    enum = re.search(r"enum\s+PPBattlePhase\s*\{(.*?)\}", read(CONFIG), re.S).group(1)
    assert re.findall(r"(\w+)\s*=", enum) == ["intro", "menu", "resolve", "message", "telegraph", "dodge", "result",
                                              "ended"]
    assert "PPResult.spare" not in body("pp_battle_dissolve_begin")


@pytest.mark.parametrize("member", sorted(GODS))
def test_each_god_has_a_weapon_row_and_a_legal_sheet(member):
    sheet, body_idx, acc_idx = GODS[member]
    rows = [r for r in load("data", "items.json")["items"] if r.get("wielder") == member]
    assert len(rows) == 1 and rows[0]["kind"] == "weapon" and rows[0]["sprite"] == sheet
    assert (rows[0]["damage_min"], rows[0]["damage_max"]) == (2, 12), "balance does not move"
    side = load("game", "sprites_src", "weapons", sheet + ".json")
    assert (side["frame_w"], side["frame_h"], side["frames"]) == (32, 32, 4)
    assert rows[0]["slash_frames"] == side["frame_roles"]["slash_frames"] == [1, 2, 3]
    palette = [c.lstrip("#") for c in load("data", "nes_palette.json")["colours"]]
    allowed = {tuple(int(palette[i][j:j + 2], 16) for j in (0, 2, 4)) for i in (0x0F, body_idx, acc_idx)}
    with Image.open(os.path.join(WEAPONS, sheet + ".png")) as img:
        img = img.convert("RGBA")
        assert img.size == (128, 32)
        seen = set()
        for ty in range(4):
            for tx in range(16):
                tile = set()
                for y in range(ty * 8, ty * 8 + 8):
                    for x in range(tx * 8, tx * 8 + 8):
                        r, g, b, a = img.getpixel((x, y))
                        if a:
                            tile.add((r, g, b))
                assert len(tile) <= 3
                seen |= tile
        assert seen <= allowed, "the sheet wears its owner's reserved hero triple only"
    assert ('"name": "%s.png"' % sheet) in read(YPP)


def test_party_sheets_hold_their_weapons_in_one_triple():
    for member in ("zander", "konrad", "hadrian", "percy"):
        with Image.open(os.path.join(CHARS, member + "_battle.png")) as img:
            img = img.convert("RGBA")
            colours = {img.getpixel((x, y))[:3] for x in range(img.width) for y in range(img.height)
                       if img.getpixel((x, y))[3]}
            assert len(colours) == 3, member
            assert any(img.getpixel((x, y))[3] for x in range(16, 24) for y in range(0, 6)), member + " holds nothing up"


def test_percy_enemy_sheet_shows_the_trident():
    side = load("game", "sprites_src", "enemies", "percy_big.json")
    assert "trident" in side["note"]
    with Image.open(os.path.join(ROOT, "game", "sprites_src", "enemies", "percy_big.png")) as img:
        img = img.convert("RGBA")
        opaque = [(x, y) for x in range(48, 64) for y in range(6, 18) if img.getpixel((x, y))[3]]
        assert len(opaque) > 30, "prongs are missing"


def test_fight_rotates_through_the_party_by_data():
    assert "_battle.fight_count mod _n" in body("pp_battle_next_striker")
    assert "pp_battle_strike_begin(_battle)" in body("pp_battle_step_resolve")
    assert "pp_battle_strike_end(_battle)" in body("pp_battle_after_message")
    code = re.sub(r"//[^\n]*", "", read(DIRECTOR)).lower()
    for name in ("zander", "konrad", "hadrian"):
        assert name not in code, "a member is named in code"
    draw = body("pp_battle_draw_party_b")
    assert "_battle.striker == i" in draw and "pp_battle_flicker_now(_battle, i)" in draw


def test_battle_data_has_no_dashes():
    for rel in ("data/items.json", "data/ui_layouts.json", "data/enemies/all.json"):
        text = read(os.path.join(ROOT, rel))
        assert chr(0x2014) not in text and chr(0x2013) not in text, rel
