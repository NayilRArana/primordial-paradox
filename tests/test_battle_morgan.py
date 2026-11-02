#!/usr/bin/env python3
"""Pins for the full encounter morgan_gate (card BATTLE-FULL, 2026-10-27).

Holds down: the enemy, its patterns, its ACT effects and its lines are data; every id resolves; every option has an
effect row; the lines fit the 28 column talk block; a win by FIGHT, a win by TALK then SPARE and a loss are all
reachable by the numbers; the GML hooks (act effect, skip turn, hit flash, shake, hit cue) are wired.

Run: python -m pytest tests/test_battle_petty_officer.py -q
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def src(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


ENEMY = next(e for e in load("data/enemies/all.json")["enemies"] if e["id"] == "morgan")
ENC = next(e for e in load("data/encounters/all.json")["encounters"] if e["id"] == "morgan_gate")
PATTERNS = {p["id"]: p for p in load("data/patterns/all.json")["patterns"]}
DIALOGUE = {d["id"]: d for d in load("data/dialogue/all.json")["dialogue"]}
DIRECTOR = "game/scripts/pp_battle_director/pp_battle_director.gml"
TEXT = "game/scripts/pp_battle_text/pp_battle_text.gml"


def test_ids_resolve():
    assert ENC["enemies"] == ["morgan"]
    for pid in ENEMY["patterns"]:
        assert pid in PATTERNS
    for key in ("intro_dialogue", "win_dialogue_kill", "win_dialogue_spare", "lose_dialogue"):
        assert ENC[key] in DIALOGUE
    assert ENEMY["talk_dialogue"] in DIALOGUE and ENC["talk"]["options_dialogue"] in DIALOGUE


def test_three_talk_options_each_with_an_effect():
    opts = DIALOGUE["talk_morgan"]["lines"]
    assert len(opts) >= 3 and ENC["talk"]["option_count"] == 3
    rows = {r["option"]: r for r in ENEMY["act_responses"]}
    assert set(rows) == {0, 1, 2}
    for line in opts:
        assert len(line.strip('* "')) <= 26, line
    assert any(r.get("skip_turn") for r in rows.values()), "one ACT must make the enemy lose its turn"
    pools = [r["pattern_pool"] for r in rows.values() if "pattern_pool" in r]
    assert pools and all(p in PATTERNS for pool in pools for p in pool)
    assert any(r.get("attack_delta", 0) < 0 for r in rows.values())
    for r in rows.values():
        assert len(r["line"]) <= 28, r["line"]


def test_telegraph_line_fits_the_font():
    t = ENEMY["telegraph_line"]
    assert re.fullmatch(r"[A-Z ]{1,30}", t)


def test_win_and_loss_are_reachable_by_the_numbers():
    # FIGHT: worst bar press is 2 damage, best 12 (spec 07); the enemy dies in at most hp/2 blows, at least ceil(hp/12).
    assert -(-ENEMY["max_hp"] // 12) <= 4
    # TALK then SPARE: three talks at +20 mercy reach mercy_to_spare 60 and trust_to_spare 3.
    t = ENC["talk"]
    assert t["mercy_per_option"] * t["talks_to_spare"] >= t["mercy_to_spare"]
    assert ENEMY["trust_to_spare"] <= t["talks_to_spare"]
    # LOSE: player has 20 hp; the strongest hit (attack max) ends the run in a bounded number of hits.
    assert -(-20 // ENEMY["attack"]["max"]) <= 10


def test_every_pattern_the_officer_uses_has_a_telegraph_window():
    for pid in ENEMY["patterns"] + [p for r in ENEMY["act_responses"] for p in r.get("pattern_pool", [])]:
        assert PATTERNS[pid]["frames"][0]["at"] >= 12


def test_gml_hooks_are_wired():
    d, t = src(DIRECTOR), src(TEXT)
    assert "function pp_battle_act_apply" in d
    assert "pp_battle_act_apply(_battle, _battle.talk_cursor)" in t
    assert "skip_enemy_turn" in d and "hurt_flash" in d and "shake" in d
    assert d.count('pp_audio_play("hit")') == 1
    assert "telegraph_line" in d


def test_no_dashes_in_new_text():
    bad = ("\u2014", "\u2013")
    blob = json.dumps(ENEMY, ensure_ascii=False) + json.dumps(ENC, ensure_ascii=False) + json.dumps(
        [DIALOGUE[k] for k in DIALOGUE if "morgan" in k], ensure_ascii=False)
    assert not any(b in blob for b in bad)
