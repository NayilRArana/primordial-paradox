#!/usr/bin/env python3
"""Three battles, each played start to finish (card THREE-BATTLES, Nayil's order 2026-11-01).

Morgan at the Town Quay gate (morgan_gate, started by the gate scene), the navy sailor on the deck (tutorial_sailors,
trigger 4,7) and Percy in his office (percy, scene percy_lore_stop at 7,3). For every one: a clear intro, a FIGHT and POWER
kill to hp 0, a TALK then SPARE ending whose condition is printed in the TALK hint and enforced by data, the right result
text and flags, the room and its music on the way back, and no soft lock (SPARE too early is refused gently, a lost fight
is a defeat). battle_sim.py mirrors the director; the GML text that matters is pinned at the bottom.

Run: python -m pytest tests/test_three_battles.py -q
"""
import json
import os
import re

import pytest

import battle_sim as sim

ROOT = sim.ROOT
THREE = ("morgan_gate", "tutorial_sailors", "percy")
ROOM = {"morgan_gate": "southampton_town_quay", "tutorial_sailors": "ship_small", "percy": "southampton_town_quay"}
ROOM_MUSIC = {"southampton_town_quay": "PP-03", "ship_small": "PP-05", "ship_cabin": "PP-05"}
BARS = [60, 100, 55, 80, 70, 90, 65, 85, 75, 95]


def src(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as handle:
        return handle.read()


def kill_run(enc_id, flags=()):
    b = sim.Battle(enc_id, flags)
    used_power, n = False, 0
    while not b.ended():
        assert b.turn < 40, "soft lock: the kill never lands"
        if not used_power and b.command_state("power")[0]:
            b.do("power")
            used_power = True
        else:
            b.do("fight", BARS[n % len(BARS)])
            n += 1
    assert used_power, "POWER must be usable in every fight"
    return b


def spare_run(enc_id, flags=()):
    b = sim.Battle(enc_id, flags)
    ok, why = b.command_state("spare")
    assert not ok and why and why != "mercy is off duty", "SPARE before the condition must refuse gently"
    turns = b.turn
    assert b.do("spare") == "refused" and b.turn == turns, "a refused SPARE spends no turn"
    need = -(-b.enemy["trust_to_spare"] // b.enc["trust_per_talk"])
    for k in range(need):
        assert not b.ended()
        b.do("talk", k % 3)
        assert b.hint == b.spare_hint() and b.hint
        if k < need - 1:
            assert str(need - 1 - k) in b.hint and b.command_state("spare")[0] is False
    assert b.hint == b.enemy["spare_ready_hint"]
    assert b.command_state("spare") == (True, "")
    assert b.do("spare") == "spare"
    return b


@pytest.mark.parametrize("enc_id", THREE)
def test_data_ids_resolve_and_text_fits(enc_id):
    enc = sim.ENCOUNTERS[enc_id]
    enemy = sim.ENEMIES[enc["enemies"][0]]
    for key in ("intro_dialogue", "win_dialogue_kill", "win_dialogue_spare", "lose_dialogue"):
        assert enc[key] in sim.DIALOGUE, (enc_id, key)
        lines = sim.DIALOGUE[enc[key]].get("lines") or [l for p in sim.DIALOGUE[enc[key]]["pages"] for l in p["lines"]]
        assert lines and all(len(l) <= 30 for l in lines), (enc[key], lines)
    for pid in enemy["patterns"]:
        assert pid in {p["id"] for p in sim.load("data/patterns/all.json")["patterns"]}
    assert enemy["talk_dialogue"] in sim.DIALOGUE
    flags = set(sim.load("data/flags.json")["flags"])
    assert set(enc["flags_on_kill"]) <= flags and set(enc["flags_on_spare"]) <= flags
    assert enc["flags_on_kill"] != enc["flags_on_spare"] and enc["flags_on_kill"] and enc["flags_on_spare"]
    for key in ("spare_hint", "spare_ready_hint"):
        text = enemy[key].replace("{n}", "3")
        assert len(text) <= 28 and re.fullmatch(r"[A-Z0-9 .,:!']+", text), text
    assert "{n}" in enemy["spare_hint"] and enemy["spare_refusal"] and len(enemy["spare_refusal"]) <= 21
    assert enemy["trust_to_spare"] >= 1 and enc["trust_per_talk"] >= 1


@pytest.mark.parametrize("enc_id", THREE)
def test_kill_ending_to_hp_zero_by_fight_and_power(enc_id):
    b = kill_run(enc_id)
    assert (b.enemy_hp, b.result, b.outcome(), b.defeated) == (0, "kill", "kill", False)
    assert b.hp > 0 and b.turn >= 3


@pytest.mark.parametrize("enc_id", THREE)
def test_spare_ending_by_talk_then_spare(enc_id):
    b = spare_run(enc_id)
    assert (b.result, b.outcome(), b.enemy_hp, b.defeated) == ("spare", "spare", 0, False)
    assert b.enemy["trust_to_spare"] <= 3


@pytest.mark.parametrize("enc_id", THREE)
def test_a_lost_fight_is_a_defeat_not_a_soft_lock(enc_id):
    b = sim.Battle(enc_id)
    while not b.ended():
        assert b.turn < 40
        b.do("fight", 0, dodge="stand")
    assert (b.outcome(), b.hp) == ("defeat", 0)
    assert sim.DIALOGUE[b.enc["lose_dialogue"]]["lines"]


@pytest.mark.parametrize("enc_id", THREE)
def test_a_fight_takes_about_one_to_two_minutes(enc_id):
    b = sim.Battle(enc_id)
    while not b.ended():
        b.do("fight", 60)
    assert 55 <= sim.pacing_seconds(b.turn) <= 135, (enc_id, b.turn)


@pytest.mark.parametrize("enc_id", THREE)
def test_each_fight_starts_in_one_room_with_room_music_and_a_walkable_return_tile(enc_id):
    # FLOW 2026-11-03: the ship cabin scenes are retired data nothing leads to; only reachable rooms count.
    pts = [p for p in sim.start_points(enc_id) if p[0] != "ship_cabin"]
    assert pts and {room for room, _, _ in pts} == {ROOM[enc_id]}, pts
    room = sim.MAPS[ROOM[enc_id]]
    assert room["music"] == ROOM_MUSIC[ROOM[enc_id]] and room["music"] != sim.ENCOUNTERS[enc_id]["music"]
    for _, _, (x, y) in pts:
        assert room["collision"][y][x] == "0", (enc_id, x, y)


def test_exactly_three_fights_and_the_hound_is_kept_but_never_triggered():
    """Nayil's order (manager decision 2026-11-01): exactly three battles, Morgan, one Navy sailor, Percy in his office.

    Every fight ends by spare or 0 HP: no forced defeat and no hound fight. Card t_866814e6 had put the hound's own
    trigger back at (6,7) on the deck and added deck_collapse, a forced defeat, at (7,4) in Percy's office, for a 180 s
    take; Nayil's order overrode that design and both triggers are gone again. The hound's rows and the deck_collapse
    row stay in the data and the director's forced_defeat read stays as inert engine support, but no trigger and no
    scene starts any of them, which is what this pin holds. The name is kept for the history of the pin.
    """
    live = {e for e in sim.ENCOUNTERS if sim.start_points(e)}
    assert live == set(THREE), live
    assert "deck_hound" in sim.ENEMIES and sim.start_points("deck_hound") == [], (
        "the hound has a door again: %s" % (sim.start_points("deck_hound"),))
    assert sim.start_points("deck_collapse") == [], (
        "the forced defeat has a door again: %s" % (sim.start_points("deck_collapse"),))
    assert not any(sim.ENCOUNTERS[e].get("forced_defeat") for e in live), (
        "a fight that can be started is a forced defeat: %s" % sorted(e for e in live if sim.ENCOUNTERS[e].get("forced_defeat")))
    small = sim.MAPS["ship_small"]
    fights = [(t["x"], t["y"], t["id"]) for t in small["triggers"] if t["kind"] in ("battle", "marker")]
    assert fights == [(4, 7, "tutorial_sailors")], "the deck's fight triggers are not the one deck watch at 4,7: %s" % (fights,)
    assert any((t["x"], t["y"], t["kind"], t["id"], t["condition"]) == (18, 7, "map", "ship_cabin", "ship_door_open") for t in small["triggers"])
    cabin = sim.MAPS["ship_cabin"]
    assert [t["id"] for t in cabin["triggers"] if t["kind"] == "battle"] == [], (
        "Percy's office has a battle trigger; his fight starts from the scene percy_lore_stop")
    assert "petty_officer" not in sim.ENEMIES and "dock_petty_officer" not in sim.ENCOUNTERS


@pytest.mark.parametrize("outcome", ["spare", "kill"])
def test_morgan_fight_follows_the_quay_scene(outcome):
    # FLOW 2026-11-03: the gate is gone; Captain Morgan's fight starts from his own encounter scene on the quay.
    out = sim.run_scene("quay_morgan_encounter", set(), {"morgan_gate": outcome})
    assert out["started"] == ["morgan_gate"] and out["map"] == "southampton_town_quay"
    assert ("morgan_" + ("spared" if outcome == "spare" else "killed")) in out["flags"] and "morgan_resolved" in out["flags"]
    assert ("morgan_killed" in out["flags"]) != ("morgan_spared" in out["flags"])
    assert out["last"] == ("quay_morgan_spare" if outcome == "spare" else "quay_morgan_kill")


@pytest.mark.parametrize("outcome", ["spare", "kill"])
def test_percy_fight_follows_the_quay_scene(outcome):
    out = sim.run_scene("quay_percy_encounter", set(), {"percy": outcome})
    assert out["started"] == ["percy"] and out["map"] == "southampton_town_quay" and "demo_complete" in out["flags"]
    assert out["last"] == ("quay_percy_spare" if outcome == "spare" else "quay_percy_kill")


@pytest.mark.parametrize("outcome", ["spare", "kill"])
def test_sailor_fight_opens_the_door_to_percy(outcome):
    enc = sim.ENCOUNTERS["tutorial_sailors"]
    flags = set(enc["flags_on_spare"] if outcome == "spare" else enc["flags_on_kill"])
    assert "ship_door_open" in flags and ("sailor_spared" if outcome == "spare" else "sailor_killed") in flags


@pytest.mark.parametrize("outcome", ["spare", "kill"])
def test_percy_office_fight_then_the_ending_scene(outcome):
    cabin = sim.MAPS["ship_cabin"]
    assert "Percy" in cabin["name"] and "Office" in cabin["name"]
    lore = [t for t in cabin["triggers"] if (t["x"], t["y"]) == (7, 3)][0]
    assert (lore["kind"], lore["id"]) == ("scene", "percy_lore_stop") and lore["condition"] in sim.run_scene("ship_boarding", set(), {})["flags"]
    out = sim.run_scene("percy_lore_stop", {"ship_deck_seen"}, {"percy": outcome})
    assert out["started"] == ["percy"] and out["map"] == "ship_cabin" and "demo_complete" in out["flags"]
    assert out["last"] == ("percy_aftermath" if outcome == "spare" else "percy_aftermath_kill")
    assert out["said"][0] == "percy_lore_stop" and "demo_end_card" in out["said"]
    assert ("percy_spared" in out["flags"]) != ("percy_killed" in out["flags"])


def test_percy_interrupt_then_the_rematch_in_the_office_also_ends():
    b = sim.Battle("percy")
    while not b.interrupt_ready():
        assert b.turn < 20
        b.do("fight", 60)
    assert b.command_state("spare") == (True, "") and b.do("spare") == "interrupted"
    out = sim.run_scene("percy_lore_stop", {"ship_deck_seen"}, {"percy": "interrupted"})
    assert out["last"] == "prometheus_interrupt" and {"met_prometheus", "percy_standing"} <= out["flags"]
    trig = [t for t in sim.MAPS["ship_cabin"]["triggers"] if (t["x"], t["y"]) == (7, 2)][0]
    assert (trig["kind"], trig["id"], trig["condition"], trig["once"]) == ("scene", "percy_rematch", "percy_standing", False)
    again = sim.Battle("percy", out["flags"])
    again.enemy_hp = 16
    assert not again.interrupt_ready() and again.command_state("spare")[0] is False, "no second interruption, a gentle refusal"
    assert spare_run("percy", out["flags"]).outcome() == "spare"
    final = sim.run_scene("percy_rematch", out["flags"], {"percy": "spare"})
    assert final["last"] == "percy_aftermath" and "demo_complete" in final["flags"]


def test_enemy_phases_still_cross_in_the_short_percy_fight():
    b = sim.Battle("percy")
    while b.enemy_hp > 16:
        b.do("fight", 60)
    assert b.crossed == ["percy_wall", "percy_fan"] and b.attack["max"] >= 5


def test_gml_hooks_are_wired():
    text, cmds, d = src("game/scripts/pp_battle_text/pp_battle_text.gml"), src("game/scripts/pp_battle_commands/pp_battle_commands.gml"), src("game/scripts/pp_battle_director/pp_battle_director.gml")
    assert "function pp_battle_spare_hint" in text and "pp_battle_spare_hint(_battle)" in text and text.count("pp_talk_hint_draw(pp_battle_spare_hint(_battle))") == 1
    assert "function pp_battle_spare_refusal" in cmds and "_reason = pp_battle_spare_refusal(_battle);" in cmds
    assert "pp_battle_saved_powers(_ledger, _party)" in d and "starting_powers" in d
    assert "string_replace(string(_enemy[$ _key]), \"{n}\", string(_need))" in text


def test_no_dashes_in_the_new_text():
    bad = ("\u2014", "\u2013")
    blob = "".join(json.dumps(json.load(open(os.path.join(ROOT, p), encoding="utf-8")), ensure_ascii=False) for p in
                   ("data/enemies/all.json", "data/encounters/all.json", "data/dialogue/all.json", "data/scenes/all.json"))
    blob += src("tests/test_three_battles.py") + src("tests/battle_sim.py")
    assert not any(b in blob for b in bad)
