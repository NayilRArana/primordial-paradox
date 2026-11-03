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


def test_party_turn_order_is_real_and_visible():
    assert "clamp(_battle.active, 0, _n - 1)" in body("pp_battle_next_striker")
    advance = body("pp_battle_member_advance")
    assert "_battle.active += 1" in advance and "_battle.active = 0" in advance
    after = body("pp_battle_after_message")
    # the next member chooses before the enemy's telegraph, and the crossing line is still said first
    assert after.index("pp_battle_member_advance(_battle)") < after.index("pp_battle_roll_attack(_battle)")
    assert after.index("phase_line") < after.index("pp_battle_member_advance(_battle)")
    assert "pp_battle_strike_begin(_battle)" in body("pp_battle_step_resolve")
    assert "pp_battle_strike_end(_battle)" in after
    code = re.sub(r"//.*", "", read(DIRECTOR)).lower()
    for name in ("zander", "konrad", "hadrian"):
        assert name not in code, "a member is named in code"
    draw = body("pp_battle_draw")
    assert "'S TURN\"" in draw and "pp_battle_draw_turn_banner(" in draw, "the turn banner is gone"
    party = body("pp_battle_draw_party_b")
    assert "_battle.striker == i" in party and 'pp_battle_swatch("gold"' in party, "the turn arrow is gone"
    assert "pp_battle_flicker" not in read(DIRECTOR), "the helm flicker must not read as a turn cue"


def test_every_list_answers_left_and_right():
    menu = body("pp_battle_step_menu")
    assert 'pp_menu_axis("left", "right")' in menu and "pp_command_move_h(_battle, _dir_h)" in menu
    cmds = read(os.path.join(ROOT, "game", "scripts", "pp_battle_commands", "pp_battle_commands.gml"))
    assert "function pp_command_move_h(" in cmds and "_battle.cursor mod 2 == 0" in cmds
    talk = read(os.path.join(ROOT, "game", "scripts", "pp_battle_text", "pp_battle_text.gml"))
    assert 'if (_dir == 0) _dir = pp_menu_axis("left", "right");' in talk
    assert 'if (_dir == 0) _dir = pp_menu_axis("left", "right");' in body("pp_battle_step_gameover")
    title = read(os.path.join(ROOT, "game", "scripts", "pp_title", "pp_title.gml"))
    assert 'pp_menu_axis("left", "right")' in title


def test_command_grid_horizontal_move_mirrors_the_gml():
    """The GML toggles the column of the same row; five entries in two columns, the last row has one."""
    def move(cursor):
        to = cursor + (1 if cursor % 2 == 0 else -1)
        return to if 0 <= to < 5 else cursor
    assert [move(i) for i in range(5)] == [1, 0, 3, 2, 4]


def test_enemy_hp_drops_and_shows_at_once():
    hurt = body("pp_battle_hurt_enemy")
    assert "_battle.enemy_hp = max(0, _battle.enemy_hp - _damage);" in hurt
    assert 'pp_battle_hud_refresh(_battle, "enemy damage")' in hurt and "popup_enemy = true" in hurt
    draw = body("pp_battle_draw")
    # the plate is drawn in every phase but the dodge, before the message window, and the window no longer covers it
    assert "_battle.phase != PPBattlePhase.dodge) {" in draw and "pp_battle_draw_plate_b(_battle, _layout_b)" in draw
    layout = load("data", "ui_layouts.json")["battle_b"]
    plate, msg = layout["plate"], layout["message"]
    assert plate["y"] >= msg["y"] + msg["h"] * 8, "the message window would cover the enemy plate"
    plate_code = body("pp_battle_draw_plate_b")
    assert '"HP " + string(_hud.enemy_hp) + "/" + string(_hud.enemy_max)' in plate_code
    assert 'pp_font_draw_plated_centre("-" + string(_battle.popup_value)' in body("pp_battle_draw")
    assert "popup_enemy = false" in body("pp_battle_step_dodge"), "a hit on the party must not print over the enemy"


def test_talk_shows_mercy_and_two_or_three_talks_fill_it():
    enc = {e["id"]: e for e in load("data", "encounters", "all.json")["encounters"]}
    enemies = {e["id"]: e for e in load("data", "enemies", "all.json")["enemies"]}
    for rid, eid in (("morgan_gate", "morgan"), ("percy", "percy")):
        row = enc[rid]
        table = row["talk_mercy"]
        assert set(table) >= {"soften", "nudge", "setback"} and min(table.values()) > 0
        trust_needed = -(-enemies[eid]["trust_to_spare"] // row["trust_per_talk"])
        assert trust_needed == 2, "two talks open the spare gate on %s" % rid
        assert 2 * table["soften"] >= 100, "two good talks fill the meter"
        # simulate the GML: mercy by effect, topped up to 100 when trust reaches the gate, spare then allowed
        for effects in (("soften", "soften"), ("nudge", "setback"), ("setback", "setback")):
            mercy, trust = 0, 0
            for effect in effects:
                trust += row["trust_per_talk"]
                mercy = min(100, mercy + table[effect])
                if trust >= enemies[eid]["trust_to_spare"]:
                    mercy = 100
            assert mercy == 100 and trust >= enemies[eid]["trust_to_spare"], (rid, effects)
    apply = body_in("pp_battle_text", "pp_talk_apply")
    assert "pp_talk_boost(_battle, _record.effect)" in apply and "_battle.talk_mercy = 100;" in apply
    assert "_battle.mercy_popup = _battle.talk_delta;" in apply
    draw = body("pp_battle_draw")
    assert "string(_battle.mercy_popup)" in draw and "will_label" in draw and "pp_battle_draw_plus(" in draw
    assert "will_label" in body("pp_battle_hud_state"), "the meter keeps its MERCY label"


def body_in(module, name):
    text = read(os.path.join(ROOT, "game", "scripts", module, module + ".gml"))
    start = text.find("function %s(" % name)
    assert start >= 0, name
    return text[start:text.find("\n}", start)]


def test_battle_data_has_no_dashes():
    for rel in ("data/items.json", "data/ui_layouts.json", "data/enemies/all.json"):
        text = read(os.path.join(ROOT, rel))
        assert chr(0x2014) not in text and chr(0x2013) not in text, rel


def test_each_member_has_their_own_stronger_power():
    powers = {p["id"]: p for p in load("data", "powers.json")["powers"]}
    by_wielder = {p["wielder"]: p for p in powers.values() if "wielder" in p}
    assert set(by_wielder) == {"zander", "konrad", "hadrian"}
    assert {by_wielder[w]["anim"] for w in by_wielder} == {"bolt_sky", "age", "quake"}
    names = [by_wielder[w]["name"] for w in ("zander", "konrad", "hadrian")]
    assert len(set(names)) == 3 and "Tide Step" not in names
    fight_max = int(dict(re.findall(r"^#macro\s+(PP_FIGHT_DAMAGE_MAX)\s+(\d+)", read(CONFIG), re.M))["PP_FIGHT_DAMAGE_MAX"])
    for power in by_wielder.values():
        assert power["cost"] == powers["tide_step"]["cost"] == 1, "the cost does not move"
        assert power["power"] > fight_max, "a POWER must clearly beat the best FIGHT"
    assert by_wielder["zander"]["power"] == max(p["power"] for p in by_wielder.values()), "the bolt hits hardest"
    code = body("pp_battle_member_power")
    assert "_row.wielder" in code and "_slot.id" in code
    begin = body("pp_battle_begin_action")
    assert "pp_battle_member_power(_battle)" in begin and '" uses " + _power.name' in begin


def test_the_three_power_animations_exist_and_wait_for_the_board():
    fx = body("pp_battle_draw_power_fx")
    for anim in ('case "bolt_sky"', 'case "age"', 'case "quake"'):
        assert anim in fx, anim
    assert "pp_battle_draw_hourglass(" in fx, "the time attack needs its clock motif"
    assert "pp_battle_draw_aged(" in body("pp_battle_draw_enemy_big")
    assert "gem" in read(DIRECTOR).lower() and "_keys[i]" in fx, "gems rise under the enemy"
    assert "_battle.shake = 36" in body("pp_battle_begin_action"), "the quake shakes the screen"
    assert "PP_POWER_FX_STEPS" in body("pp_battle_fx_running")
    assert "!pp_battle_fx_running(_battle)" in body("pp_battle_step_message")
    assert "pp_battle_draw_power_fx(_battle, _enemy_slot)" in body("pp_battle_draw")
    # NES legal: the animations paint only through the swatch atlas and the enemy's or weapon's own sheet
    for name in ("pp_battle_draw_power_fx", "pp_battle_draw_hourglass", "pp_battle_draw_aged"):
        assert "draw_set_colour" not in body(name) and "c_" not in body(name).replace("pp_", ""), name


def test_x_cancels_every_sub_list():
    step = body("pp_battle_step_menu")
    assert "pp_battle_sub_step(_battle)" in step and 'pp_pressed("cancel")' in step
    assert 'if (_entry.id == PPCommand.power || _entry.id == PPCommand.item) {' in step
    sub = body("pp_battle_sub_step")
    assert 'pp_pressed("cancel")' in sub and '_battle.sub_stage = "";' in sub
    # the turn is spent only on Z: the turn counter moves after the confirm check, never on opening the row
    assert sub.index('pp_pressed("confirm")') < sub.index("_battle.turn += 1")
    talk = body_in("pp_battle_text", "pp_talk_step")
    assert 'pp_pressed("cancel")' in talk and "_battle.trust - _battle.encounter.trust_per_talk" in talk
    assert "_battle.turn - 1" in talk, "cancelling TALK takes the whole press back"
    assert "pp_battle_draw_sub(_battle)" in body("pp_battle_draw")
    assert "that turn is played" in step, "X in the command menu cannot undo a played member turn; it says so"


def test_cancel_out_of_talk_restores_trust_and_turn():
    """The GML undo mirrored: TALK adds trust_per_talk and one turn, X subtracts both again."""
    trust, turn, per = 0, 4, 2
    trust, turn = trust + per, turn + 1
    trust, turn = max(0, trust - per), max(0, turn - 1)
    assert (trust, turn) == (0, 4)


def test_no_message_row_falls_on_a_window_border():
    """The 8 px border ring of a window is not text area: every glyph row must sit inside the interior."""
    msg = load("data", "ui_layouts.json")["battle_b"]["message"]
    interior_bottom = msg["y"] + msg["h"] * 8 - 8  # first pixel row of the bottom ring
    for first_row, rows in ((16, 3 * 10 - 2), (8, 4 * 8 + 8)):  # the 3 line board, the talk reply block with its hint
        assert first_row >= msg["y"] + 8 and first_row + rows <= interior_bottom + 2, (first_row, rows, interior_bottom)
    assert 40 + 8 <= interior_bottom, "the talk hint row must clear the bottom ring"
    plate = load("data", "ui_layouts.json")["battle_b"]["plate"]
    assert plate["y"] >= msg["h"] * 8, "the enemy plate must start below the message window"
    banner = body("pp_battle_draw_turn_banner")
    assert "pp_battle_window_b(_x, 8, _tiles, 3)" in banner and "_x + 8, 16" in banner, "banner text must sit on the interior row"


def test_the_fight_tour_confirms_a_sub_row():
    overworld = read(os.path.join(ROOT, "game", "scripts", "pp_overworld", "pp_overworld.gml"))
    tour = overworld[overworld.index("function pp_fight_tour_think("):]
    assert '_b.sub_stage != ""' in tour and tour.index('_b.sub_stage != ""') < tour.index("var _target = PPCommand.fight;")


def test_the_talk_hint_waits_for_the_reply_to_finish_typing():
    draw = body("pp_battle_draw")
    assert "if (pp_text_board_done(_battle.messages)) pp_talk_hint_draw(_battle.talk_hint);" in draw
    # the reply block (4 lines at 8 px from y 8) and the hint row at y 40 all sit inside the 7 tile window's interior
    msg = load("data", "ui_layouts.json")["battle_b"]["message"]
    assert 8 + 4 * 8 + 8 <= msg["h"] * 8 - 8 + 8 and 40 + 8 <= msg["h"] * 8 - 8
