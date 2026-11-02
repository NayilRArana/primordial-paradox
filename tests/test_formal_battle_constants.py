"""The battle spec's constants against the game's data (card t_1b355b57).

The TLA+ module manager/formal/BattlePhases.tla carries no number of its own: every constant
that shapes a fight is set in a .cfg file, and every one of those values is a fact of the game's
data. This test reads the .cfg files back and fails when one of them stops matching

    data/enemies/all.json, data/encounters/all.json, data/characters/party.json,
    data/items.json, data/powers.json, game/scripts/pp_config/pp_config.gml

so a fight that is rebalanced in data and not in the spec cannot pass silently. It also holds the
two variant modules to the faithful one: BattlePhasesBroken.tla must differ from BattlePhases.tla
in the ResultOut block and nowhere else, and BattlePhasesUnguardedSpare.tla in the two spare gate
lines and nowhere else.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT.parent / "arananet" / "manager" / "formal"
BATTLE = FORMAL / "battle"

CONFIG_LINE = re.compile(r"^(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.+?)\s*$")


def _read_json(relative: str) -> dict:
    with open(ROOT / relative, encoding="utf-8") as handle:
        return json.load(handle)


def _by_id(rows, wanted: str, kind: str) -> dict:
    for row in rows:
        if row.get("id") == wanted:
            return row
    raise AssertionError("no " + kind + " with id " + wanted + " in the data")


def _config(path: Path) -> dict:
    """The CONSTANTS section of a TLC .cfg as {name: python value}."""
    values = {}
    inside = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.upper().startswith("CONSTANTS"):
            inside = True
            continue
        if not line or line.startswith("\\*"):
            continue
        if inside:
            match = CONFIG_LINE.match(line)
            if not match:
                inside = False
                continue
            values[match.group("key")] = _value(match.group("value"))
    assert values, "no constants found in " + str(path)
    return values


def _value(text: str):
    if text == "TRUE":
        return True
    if text == "FALSE":
        return False
    if text.startswith('"') and text.endswith('"'):
        return text[1:-1]
    return int(text)


def _macros() -> dict:
    """The #macro numbers of pp_config.gml, by name."""
    text = (ROOT / "game" / "scripts" / "pp_config" / "pp_config.gml").read_text(
        encoding="utf-8")
    found = {}
    for match in re.finditer(r"^#macro\s+(PP_[A-Z0-9_]+)\s+([0-9]+)\s*$", text, re.M):
        found[match.group(1)] = int(match.group(2))
    return found


def _enum(name: str) -> list:
    """The member names of a GML enum, in order."""
    text = (ROOT / "game" / "scripts" / "pp_config" / "pp_config.gml").read_text(
        encoding="utf-8")
    match = re.search(r"enum\s+" + name + r"\s*\{(.*?)\}", text, re.S)
    assert match, "enum " + name + " not found in pp_config.gml"
    body = re.sub(r"//[^\n]*", "", match.group(1))
    return re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*=", body)


def _expected(encounter_id: str) -> dict:
    encounters = _read_json("data/encounters/all.json")["encounters"]
    enemies = _read_json("data/enemies/all.json")["enemies"]
    party = _read_json("data/characters/party.json")["characters"]
    items = _read_json("data/items.json")["items"]
    powers = _read_json("data/powers.json")["powers"]
    macro = _macros()

    encounter = _by_id(encounters, encounter_id, "encounter")
    assert len(encounter["enemies"]) == 1, "the model is one enemy per fight"
    enemy = _by_id(enemies, encounter["enemies"][0], "enemy")
    hero = _by_id(party, "hero", "party member")

    # The attack band the fight can actually roll: the row's own, widened by every phase row
    # (pp_battle_enemy_phase_sync reads a phase's attack into the range in force).
    bands = [(enemy["attack"]["min"], enemy["attack"]["max"])]
    for phase in enemy.get("phases", []):
        if "attack" in phase:
            bands.append((phase["attack"]["min"], phase["attack"]["max"]))

    salve = _by_id(items, "salve", "item")
    tide_step = _by_id(powers, "tide_step", "power")
    start = {row["id"]: row["count"] for row in hero.get("starting_items", [])}

    interrupt = enemy.get("interrupt") or {}
    return {
        "Encounter": encounter_id,
        "EnemyID": enemy["id"],
        "EnemyMaxHP": enemy["max_hp"],
        "EnemyAtkMin": min(band[0] for band in bands),
        "EnemyAtkMax": max(band[1] for band in bands),
        "TrustToSpare": enemy["trust_to_spare"],
        "SpareHPPercent": enemy["spare_hp_percent"],
        "InterruptHPPercent": interrupt.get("hp_at_or_below", 0),
        "TrustPerTalk": encounter["trust_per_talk"],
        "HasTalk": "talk_dialogue" in enemy,
        "ForcedDefeat": bool(encounter.get("forced_defeat", False)),
        "PartyMaxHP": hero["max_hp"],
        "ItemCount": start.get("salve", 0),
        "ItemHeal": salve["heal"],
        "PowerCost": tide_step["cost"],
        "PowerDamage": tide_step["power"],
        "WillMax": hero["will_max"],
        "FightMaxHit": round(macro["PP_FIGHT_DAMAGE_MAX"] * hero["power_multiplier"]),
    }


def _cfgs() -> list:
    paths = sorted(BATTLE.glob("*.cfg"))
    assert paths, "no .cfg files in " + str(BATTLE)
    return paths


def test_every_config_is_an_instance_of_the_three_rescoped_fights():
    names = {path.name for path in _cfgs()}
    for encounter in ("morgan_gate", "tutorial_sailors", "percy"):
        assert "BattlePhases." + encounter + ".cfg" in names
        assert "BattlePhases." + encounter + ".term.cfg" in names
    assert "BattlePhases.deck_collapse.cfg" in names
    for witness in ("spare", "kill", "defeat", "interrupt"):
        assert "BattlePhases.witness_" + witness + ".cfg" in names


def test_constants_match_the_data():
    for path in _cfgs():
        values = _config(path)
        expected = _expected(values["Encounter"])
        for key, wanted in expected.items():
            assert values[key] == wanted, (
                path.name + ": " + key + " is " + repr(values[key])
                + " in the spec but " + repr(wanted) + " in the data")


def test_the_model_only_constants_are_declared():
    for path in _cfgs():
        values = _config(path)
        for key in ("MaxTurn", "IntroSteps", "MessageReads", "BarReads", "DecisivePlayer"):
            assert key in values, path.name + " is missing " + key
        assert isinstance(values["DecisivePlayer"], bool)


def test_the_safety_and_termination_instances_differ_only_in_the_player():
    for encounter in ("morgan_gate", "tutorial_sailors", "percy"):
        safety = _config(BATTLE / ("BattlePhases." + encounter + ".cfg"))
        term = _config(BATTLE / ("BattlePhases." + encounter + ".term.cfg"))
        assert safety.pop("DecisivePlayer") is False
        assert term.pop("DecisivePlayer") is True
        assert safety == term, (
            "the safety and termination instances of " + encounter + " disagree on a constant")


def test_forced_defeat_follows_the_encounter_row():
    percy = _config(BATTLE / "BattlePhases.percy.cfg")
    collapse = _config(BATTLE / "BattlePhases.deck_collapse.cfg")
    assert collapse["ForcedDefeat"] is True
    assert percy["ForcedDefeat"] is False


def test_the_interrupt_names_a_flag_the_data_carries():
    enemies = _read_json("data/enemies/all.json")["enemies"]
    flags = set(_read_json("data/flags.json")["flags"])
    for path in _cfgs():
        values = _config(path)
        if values["InterruptHPPercent"] == 0:
            continue
        enemy = _by_id(enemies, values["EnemyID"], "enemy")
        unless = enemy["interrupt"]["unless_flag"]
        assert values["FlagMetPrometheus"] is False, "the model runs with the flag unset"
        assert unless == "met_prometheus", "the spec's flag constant is named after the data"
        assert unless in flags, "the interrupt's unless_flag is not a real flag"


def test_the_phases_are_the_phase_enum():
    text = (FORMAL / "BattlePhases.tla").read_text(encoding="utf-8")
    match = re.search(r"^Phases == \{(.*?)\}", text, re.M | re.S)
    assert match, "the Phases set is not declared"
    modelled = set(re.findall(r'"([a-z_]+)"', match.group(1)))
    game = set(_enum("PPBattlePhase"))
    # the model adds one name: gameover, the screen a defeat hands the frame to (the director
    # holds the result phase with defeated = TRUE instead of leaving it)
    assert modelled == game | {"gameover"}, (modelled, game)


def test_the_results_are_the_result_enum():
    text = (FORMAL / "BattlePhases.tla").read_text(encoding="utf-8")
    match = re.search(r"^Results == \{(.*?)\}", text, re.M | re.S)
    assert match
    modelled = set(re.findall(r'"([a-z_]+)"', match.group(1)))
    assert modelled == set(_enum("PPResult"))


def test_every_command_of_the_enum_has_its_menu_action():
    text = (FORMAL / "BattlePhases.tla").read_text(encoding="utf-8")
    for command in _enum("PPCommand"):
        action = "Menu" + command[0].upper() + command[1:]
        assert re.search(r"^" + action + r" ==", text, re.M), (
            "PPCommand." + command + " has no " + action + " action")


def _block(text: str, begin: str, end: str):
    i = text.index(begin)
    j = text.index(end)
    return text[:i], text[i:j + len(end)], text[j + len(end):]


def test_the_broken_variant_differs_only_in_the_result_exit():
    faithful = (FORMAL / "BattlePhases.tla").read_text(encoding="utf-8")
    broken = (FORMAL / "BattlePhasesBroken.tla").read_text(encoding="utf-8")
    assert " MODULE BattlePhasesBroken " in broken
    faithful = faithful.replace(" MODULE BattlePhases ", " MODULE BattlePhasesBroken ", 1)
    before, block, after = _block(faithful, "\\* ==== BEGIN RESULTOUT ====",
                                  "\\* ==== END RESULTOUT ====")
    assert "ResultOut ==" in block
    new_before, new_block, new_after = _block(broken, "\\* ==== BEGIN RESULTOUT ====",
                                              "\\* ==== END RESULTOUT ====")
    assert before == new_before and after == new_after, (
        "BattlePhasesBroken.tla changed something outside the ResultOut block")
    assert re.search(r"^ResultOut ==\s*$", new_block, re.M)
    assert re.search(r"^\s+FALSE\s*$", new_block, re.M), "the broken ResultOut is not FALSE"


def test_the_unguarded_variant_differs_only_in_the_spare_gate():
    faithful = (FORMAL / "BattlePhases.tla").read_text(encoding="utf-8")
    unguarded = (FORMAL / "BattlePhasesUnguardedSpare.tla").read_text(encoding="utf-8")
    assert " MODULE BattlePhasesUnguardedSpare " in unguarded
    faithful = faithful.replace(" MODULE BattlePhases ",
                                " MODULE BattlePhasesUnguardedSpare ", 1)
    before, block, after = _block(faithful, "\\* ==== BEGIN MENUSPARE ====",
                                  "\\* ==== END MENUSPARE ====")
    new_before, new_block, new_after = _block(unguarded, "\\* ==== BEGIN MENUSPARE ====",
                                              "\\* ==== END MENUSPARE ====")
    assert before == new_before and after == new_after, (
        "BattlePhasesUnguardedSpare.tla changed something outside the MenuSpare block")
    assert "/\\ SpareAllowed \\/ InterruptReady" in block
    assert "/\\ SpareAllowed \\/ InterruptReady" not in new_block, "the gate was not removed"
    assert "/\\ IF TRUE" in new_block, "the spare branch is not taken unconditionally"


def test_the_logs_show_every_check_ran():
    """The four kinds of run, each with the outcome the card asks for."""
    logs = FORMAL / "battle" / "logs"
    if not logs.exists():
        pytest.skip("no TLC logs: run projects/arananet/manager/formal/battle/run_tlc.py")
    expect_no_error = ["morgan_gate.safety", "morgan_gate.term", "tutorial_sailors.safety",
                       "tutorial_sailors.term", "percy.safety", "percy.term",
                       "deck_collapse.safety"]
    for name in expect_no_error:
        text = (logs / (name + ".log")).read_text(encoding="utf-8", errors="replace")
        assert "Model checking completed. No error has been found." in text, (
            name + " did not pass")
    for name, invariant in [("witness_spare", "WitnessSpare"),
                            ("witness_kill", "WitnessKill"),
                            ("witness_defeat", "WitnessDefeat"),
                            ("witness_interrupt", "WitnessInterrupt"),
                            ("broken", "NoDeadlock"),
                            ("unguarded_spare", "SpareOnlyWhenConditionsMet")]:
        text = (logs / (name + ".log")).read_text(encoding="utf-8", errors="replace")
        assert "Invariant " + invariant + " is violated." in text, (
            name + " was expected to violate " + invariant)
    text = (logs / "broken.term.log").read_text(encoding="utf-8", errors="replace")
    assert "Temporal properties were violated." in text, "the broken variant passed Termination"
