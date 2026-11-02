"""Pins for the two S6 win paths (card t_e48b13a6).

What these hold down, and why each one earns its place:

  1. both paths are tables the recorder already knows how to play, so `--path talk` and `--path command` are one flag
     and no manual input: each table is in data/demo/shot_table.json, each passes tools/play_demo.py's own table
     validator, and each names a script that passes the same tool's script validator;
  2. each table's own arithmetic is its script's: the shots meet end to end, their seconds are their steps at 60 fps,
     the last shot ends on the script's checks.end_step, and the sum lands inside the table's tolerance;
  3. neither take carries a narrator: the take has no voice over, and the paths are no exception;
  4. the talking win talks the sailor's own count: three soften rows of 20 to the meter's 60, which is the encounter's
     talks_to_spare, mercy_per_option and mercy_to_spare and the sailor's own trust_to_spare, all read from data so a
     retune breaks the claim here instead of in a take nobody can rewind;
  5. the single command win is one press on a fight one blow must end: the deck hound's 2 hp against the game's own
     damage floor (PP_FIGHT_DAMAGE_MIN) and the party's multiplier, so "one command" is arithmetic and not a memory;
  6. both walks stop where the map says, on the ship's log doorway, and the scene's own move lands the hero on the
     save point, so the save neither needs a press the script has to guess nor a tile the map does not carry;
  7. the log's pages get exactly the presses the dialogue asks for and the take ends on the written page.

Run: python -m pytest tests/test_demo_paths.py -q
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
CONFIG_GML = os.path.join(ROOT, "game", "scripts", "pp_config", "pp_config.gml")
MAPS = os.path.join(ROOT, "data", "maps", "all.json")
ENEMIES = os.path.join(ROOT, "data", "enemies", "all.json")
ENCOUNTERS = os.path.join(ROOT, "data", "encounters", "all.json")
PARTY = os.path.join(ROOT, "data", "characters", "party.json")
SCENES = os.path.join(ROOT, "data", "scenes", "all.json")
DIALOGUE = os.path.join(ROOT, "data", "dialogue", "all.json")
BAKE = os.path.join(ROOT, "data", "meta_bake.json")
SHOT_TABLE = os.path.join(ROOT, "data", "demo", "shot_table.json")
PLAY_DEMO = os.path.join(ROOT, "tools", "play_demo.py")

DECK = "ship_small"
WATCH = "tutorial_sailors"
HOUND = "deck_hound"
SAILOR = "navy_sailor"
LOG_SCENE = "ship_log"
SAVE_TRIGGER = "deck_save"
LOG_DIALOGUE = "ship_log_open"
PATHS = ("talk-win", "command-win")


def load(path: str):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def load_module(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_tool(name: str):
    return load_module(os.path.join(TOOLS, name + ".py"), name + "_demo_paths")


def load_mirror():
    return load_module(os.path.join(ROOT, "tests", "test_fight_endings.py"), "fight_endings_mirror")


def deck() -> dict:
    for row in load(MAPS)["maps"]:
        if row.get("id") == DECK:
            return row
    raise AssertionError("data/maps/all.json carries no map called %r" % DECK)


def deck_trigger(trigger_id: str) -> dict:
    for row in deck().get("triggers", []):
        if row.get("id") == trigger_id:
            return row
    raise AssertionError("the deck carries no trigger called %r" % trigger_id)


def enemy(enemy_id: str) -> dict:
    for row in load(ENEMIES)["enemies"]:
        if row.get("id") == enemy_id:
            return row
    raise AssertionError("data/enemies/all.json carries no enemy called %r" % enemy_id)


def encounter(encounter_id: str) -> dict:
    for row in load(ENCOUNTERS)["encounters"]:
        if row.get("id") == encounter_id:
            return row
    raise AssertionError("data/encounters/all.json carries no encounter called %r" % encounter_id)


def scene(scene_id: str) -> dict:
    for row in load(SCENES)["scenes"]:
        if row.get("id") == scene_id:
            return row
    raise AssertionError("data/scenes/all.json carries no scene called %r" % scene_id)


def dialogue(dialogue_id: str) -> dict:
    for row in load(DIALOGUE)["dialogue"]:
        if row.get("id") == dialogue_id:
            return row
    raise AssertionError("data/dialogue/all.json carries no row called %r" % dialogue_id)


def script_of(table: dict) -> dict:
    return load(os.path.join(ROOT, table["script"]))


def table(name: str) -> dict:
    return load(SHOT_TABLE)["tables"][name]


def engine_macro(name: str) -> int:
    with open(CONFIG_GML, "r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.startswith("#macro %s " % name):
                return int(line.split()[2])
    raise AssertionError("game/scripts/pp_config/pp_config.gml carries no #macro %s" % name)


def walk_tile(holds, start, actors):
    """Where the shipped walker leaves the hero after these holds, from this tile."""
    walker = load_tool("walker_bot")
    map_row = deck()
    px, py = start[0] * walker.TILE, start[1] * walker.TILE
    for key, steps in holds:
        wx = {"left": -1, "right": 1}.get(key, 0)
        wy = {"up": -1, "down": 1}.get(key, 0)
        assert wx or wy, "%r is not a direction" % key
        for _step in range(steps):
            px, py, _moved, _hx, _hy = walker.free_step(map_row["collision"], px, py, wx, wy, actors=actors)
    return walker.tile_at(px, py)


def save_rows(script: dict):
    rows = [event for event in script["events"] if event["kind"] == "hold"]
    assert len(rows) >= 2, "the take holds no direction after the fight, so the hero never reaches the log"
    return rows[-2], rows[-1]


@pytest.mark.parametrize("name", PATHS)
def test_both_paths_are_tables_the_recorder_can_play(name):
    """A path is a shot table with a shorter name, so the hook is the table and the table is the plan."""
    demo = load_tool("play_demo")
    data = load(SHOT_TABLE)
    assert name in data["tables"], "data/demo/shot_table.json carries no table called %r" % name
    assert name in demo.PATH_TABLES.values(), (
        "tools/play_demo.py's PATH_TABLES does not name %r, so no --path reaches it" % name)
    loaded = demo.load_shot_table(name)
    assert demo.validate_shot_table(loaded) == [], (
        "the table %r is refused by tools/play_demo.py" % name)
    script = script_of(loaded)
    assert demo.validate_script(script) == [], (
        "%s is refused by tools/play_demo.py: %s" % (loaded["script"], demo.validate_script(script)))
    assert demo.validate_shot_table_script(loaded, script) == [], (
        "the table %r does not match %s" % (name, loaded["script"]))


@pytest.mark.parametrize("name", PATHS)
def test_each_path_table_adds_up_to_its_own_steps(name):
    demo = load_tool("play_demo")
    loaded = table(name)
    script = script_of(loaded)
    assert loaded["fps"] == 60 and script["clock"]["fps"] == 60
    assert loaded["end_step"] == script["checks"]["end_step"], (
        "the table's last step is %r and the script's is %r"
        % (loaded["end_step"], script["checks"]["end_step"]))
    total = float(loaded["total_seconds"])
    assert abs(loaded["end_step"] / 60.0 - total) <= 0.02, "the plan is %r and its steps are %.2f s" % (
        total, loaded["end_step"] / 60.0)
    assert abs(demo.shot_table_seconds(loaded) - total) <= float(loaded["tolerance_seconds"]), (
        "the shots sum to %.2f s against %.2f s" % (demo.shot_table_seconds(loaded), total))
    rows = loaded["shots"]
    for before, after in zip(rows, rows[1:]):
        assert before["end_step"] == after["start_step"], (
            "%s ends on %r and %s starts on %r" % (before["id"], before["end_step"], after["id"],
                                                   after["start_step"]))
        assert abs(before["seconds"] - (before["end_step"] - before["start_step"]) / 60.0) <= 0.02
    assert rows[0]["start_step"] == 0
    assert rows[-1]["end_step"] == loaded["end_step"]
    low, high = loaded["take_band_seconds"]
    assert low <= total <= high, "the take is %.2f s and its band is %r" % (total, loaded["take_band_seconds"])
    beats = sorted({marker for row in rows for marker in row["markers"]})
    assert beats == sorted(loaded["required_beats"]), (
        "the table's rows name %r and its required beats are %r" % (beats, loaded["required_beats"]))
    assert sorted(script["checks"]["required_beats"]) == sorted(loaded["required_beats"])


@pytest.mark.parametrize("name", PATHS)
def test_neither_path_carries_a_narrator(name):
    """The card's rule: no narration is required. The take stands on the game's own textbox and nothing else."""
    demo = load_tool("play_demo")
    loaded = table(name)
    text = json.dumps(loaded)
    for key in demo.NARRATION_KEYS:
        assert '"%s"' % key not in text, "the table %r carries a %r field" % (name, key)
    for path in (SHOT_TABLE, os.path.join(ROOT, loaded["script"])):
        with open(path, "r", encoding="utf-8") as handle:
            body = handle.read()
        for mark, label in (("\u2014", "em dash"), ("\u2013", "en dash")):
            assert mark not in body, "%s carries a %s" % (os.path.basename(path), label)


def test_the_talking_win_talks_the_sailors_own_count():
    """Three softens of 20 to the meter's 60 is the encounter's own arithmetic, so the spare is earned and not asserted."""
    watch = encounter(WATCH)
    talk = watch["talk"]
    sailor = enemy(SAILOR)
    assert talk["mercy_per_option"] == talk["mercy_to_spare"] / talk["talks_to_spare"], (
        "the encounter's mercy steps do not add up to its own spare line")
    assert talk["talks_to_spare"] == sailor["trust_to_spare"], (
        "the encounter asks for %r talks and the sailor spares at trust %r"
        % (talk["talks_to_spare"], sailor["trust_to_spare"]))
    # The panel's first row is the bake's option 1 on the enemy's own card, and it has to be the row that moves the meter.
    cards = [row for row in load(BAKE)["rows"] if row.get("enemy") == talk["card"]]
    first = [row for row in cards if row.get("option") == 1]
    assert len(first) == 1, "the bake carries %r rows for option 1 of %r" % (len(first), talk["card"])
    assert first[0]["effect"] == "soften", (
        "the panel's first row is %r, so three presses would not soften the meter" % first[0]["effect"])
    script = script_of(table("talk-win"))
    steps = [event for event in script["events"] if event.get("marker", "").startswith(", mercy")]
    assert len(steps) == talk["talks_to_spare"], (
        "the take presses the panel %r times and the encounter wants %r talks" % (len(steps), talk["talks_to_spare"]))
    meters = [int(event["marker"].split("mercy ")[1].split(",")[0]) for event in steps]
    assert meters == [talk["mercy_per_option"] * index for index in range(talk["talks_to_spare"])], (
        "the take waits on the meter readings %r, and the encounter steps it by %r" % (meters, talk["mercy_per_option"]))
    last = steps[-1]
    after = [event for event in script["events"] if event["step"] > last["step"] and event["kind"] == "key"]
    assert after, "nothing is pressed after the third talk, so the spare never happens"
    spare = after[0]
    assert spare["marker"].startswith("PP: battle menu, turn "), (
        "the press after the third talk waits on %r, which is not a command list" % spare["marker"])
    assert len({event["marker"] for event in steps}) == talk["talks_to_spare"], (
        "two talk presses wait on the same meter reading, so one of them lands on a board")


def test_the_single_command_win_is_one_press_on_a_fight_one_blow_ends():
    """The hound's 2 hp against the game's own damage floor: one FIGHT must end it, so the claim is arithmetic."""
    hound = enemy(HOUND)
    sailor = enemy(SAILOR)
    floor = engine_macro("PP_FIGHT_DAMAGE_MIN")
    multiplier = [row for row in load(PARTY)["characters"] if row.get("id") == "hero"][0]["power_multiplier"]
    assert floor * multiplier >= hound["max_hp"], (
        "one blow floors at %r damage and the hound carries %r hp" % (floor * multiplier, hound["max_hp"]))
    assert sailor["max_hp"] > floor * multiplier, (
        "the watch would also fall to one blow, so 'one command' would not be the hound's own claim")
    script = script_of(table("command-win"))
    events = script["events"]
    start = [event for event in events if event.get("marker") == "PP: battle start " + HOUND]
    assert len(start) == 1, "the take never waits on the hound's own battle start line"
    hound_menu = [event for event in events
                  if event.get("marker", "") == "enemy hp %d/%d" % (hound["max_hp"], hound["max_hp"])]
    assert len(hound_menu) == 1, (
        "the take does not wait on the hound's own command list (hp %d/%d)" % (hound["max_hp"], hound["max_hp"]))
    after = [event for event in events if event["step"] > start[0]["step"]]
    presses = [event for event in after if event["kind"] == "key" and event["key"] == "confirm"]
    hound_presses = [event for event in presses if event["step"] >= hound_menu[0]["step"] - 60]
    assert hound_presses, "the hound's fight gets no press at all"
    bar = [event for event in hound_presses if event.get("marker", "").startswith("PP: command fight")]
    assert bar == [], (
        "the take presses the timing bar in the hound's fight, so the win is not one command")
    assert hound_presses[0]["marker"] == "enemy hp %d/%d" % (hound["max_hp"], hound["max_hp"]), (
        "the first press in the hound's fight waits on %r" % hound_presses[0]["marker"])


@pytest.mark.parametrize("name", PATHS)
def test_both_walks_stop_on_the_log_doorway_and_the_scene_reaches_the_save(name):
    """The walk is simulated with the shipped walker, and the scene's own move is what puts the hero on the save tile.

    The tile the fight was won on is the trigger the script itself names, so this pin follows the take and not a copy of
    it. Card t_a790d0b1 (the map lane) rewrote data/maps/all.json on 2026-11-01 12:16:37 and dropped the deck's
    deck_hound and percy triggers in the working tree while HEAD still carries them; when this pin goes red for that
    reason it names the trigger and the file instead of failing as a mystery.
    """
    script = script_of(table(name))
    map_row = deck()
    left, up = save_rows(script)
    assert left["key"] == "left" and up["key"] == "up", (
        "the log walk holds %r then %r" % (left["key"], up["key"]))
    starts = [event["marker"].split("PP: battle start ")[1]
              for event in script["events"] if event.get("marker", "").startswith("PP: battle start ")]
    assert starts, "the take never waits on a fight's own start line"
    spawn_id = starts[-1]   # the fight the hero is left standing on, which is the last one the take opens
    carried = [row.get("id") for row in map_row.get("triggers", []) if row.get("kind") == "battle"]
    if name == "command-win":
        # Nayil's order (manager decision 2026-11-01): exactly three battles, no hound fight. The command take is walked
        # from the deck_hound fight, which no map carries any more, so the path is retired. It is pinned as retired: the
        # day a hound trigger comes back this goes red and says the command path can be played again.
        assert spawn_id == HOUND and spawn_id not in carried, (
            "the command take starts from %r and the deck carries %r: the retired path is playable again, or the take "
            "was rebuilt on another fight" % (spawn_id, carried))
        return
    assert spawn_id in carried, (
        "the take is walked from the %r fight and data/maps/all.json's %r carries the battle triggers %r: the map was "
        "rewritten under this take" % (spawn_id, DECK, carried))
    spawn = (deck_trigger(spawn_id)["x"], deck_trigger(spawn_id)["y"])
    doorway = (deck_trigger(LOG_SCENE)["x"], deck_trigger(LOG_SCENE)["y"])
    actors = tuple((row["x"], row["y"]) for row in map_row.get("actors", []))
    landed = walk_tile([(left["key"], left["steps"]), (up["key"], up["steps"])], spawn, actors)
    assert landed == doorway, (
        "the walk leaves the hero on %r and the log's doorway is %r" % (landed, doorway))
    # The scene starts the hero where the map's doorway is, walks it up its own tiles, and that is the save point.
    row = scene(LOG_SCENE)
    assert row.get("map") == DECK
    here = (row["start"]["x"], row["start"]["y"])
    for command in row["commands"]:
        if command.get("cmd") == "move" and command.get("actor") == "hero":
            dx = {"left": -1, "right": 1}.get(command.get("dir"), 0)
            dy = {"up": -1, "down": 1}.get(command.get("dir"), 0)
            here = (here[0] + dx * command["tiles"], here[1] + dy * command["tiles"])
    save = (deck_trigger(SAVE_TRIGGER)["x"], deck_trigger(SAVE_TRIGGER)["y"])
    assert here == save, (
        "the %r scene leaves the hero on %r and the save point is %r" % (LOG_SCENE, here, save))


def test_the_log_gets_a_press_for_each_thing_it_asks_for_and_none_after():
    pages = len(dialogue(LOG_DIALOGUE)["pages"])
    assert pages >= 1
    for name in PATHS:
        script = script_of(table(name))
        events = script["events"]
        doorway = [event for event in events
                   if event["kind"] == "key" and event.get("note", "").startswith("Confirm on the doorway")]
        assert len(doorway) == 1, "the take does not press the doorway exactly once in %r" % name
        presses = [event for event in events
                   if event["kind"] == "key" and event["step"] > doorway[0]["step"]]
        assert len(presses) == 2 * pages, (
            "the log has %r pages and the take presses %r times after the doorway" % (pages, len(presses)))
        tail = [event for event in events if event["step"] > presses[-1]["step"]]
        assert [event for event in tail if event["kind"] == "key"] == [], (
            "the take presses after the log's last page, so it ends on a menu instead of the written page")


def test_the_talking_win_wins_in_the_directors_own_mirror():
    """The repo already mirrors the spare gate headlessly (tests/test_fight_endings.py), driven from data.

    This is that mirror and not the engine, and the test says so: it proves the talk count the take presses is the count
    the director's own rule needs, and that the ending it reaches is the spare and not a refusal.
    """
    mirror = load_mirror()
    data = mirror.Data()
    watch = data.encounters[WATCH]
    fight = mirror.Fight(data, WATCH)
    for _talk in range(watch["talk"]["talks_to_spare"]):
        fight.talk()
    assert fight.trust == fight.enemy["trust_to_spare"], (
        "three talks leave the trust at %r and the sailor spares at %r" % (fight.trust, fight.enemy["trust_to_spare"]))
    assert fight.spare_allowed()
    kind, reference = fight.press_spare()
    assert kind == "spare", "%r talks did not earn the spare: %r" % (watch["talk"]["talks_to_spare"], (kind, reference))
    assert reference == watch["win_dialogue_spare"]
    assert fight.outcome == "spare"
    assert set(watch["flags_on_spare"]) <= fight.flags, (
        "the spare set %r and the encounter's flags are %r" % (fight.flags, watch["flags_on_spare"]))
    assert fight.counters["regulars_spared"] == 1 and fight.counters["regulars_killed"] == 0


def test_the_single_command_win_wins_in_the_directors_own_mirror():
    """One FIGHT at the bar's floor, on the deck hound, in the same headless mirror, ends the fight as a kill."""
    mirror = load_mirror()
    data = mirror.Data()
    hound_encounter = data.encounters[HOUND]
    fight = mirror.Fight(data, HOUND)
    damage = fight.fight(power=0)
    assert damage >= fight.enemy["max_hp"], (
        "the bar at power 0 does %r damage and the hound carries %r hp" % (damage, fight.enemy["max_hp"]))
    assert fight.outcome == "kill", "one command left the fight at %r" % (fight.outcome,)
    assert fight.exit == "down"
    assert set(hound_encounter["flags_on_kill"]) <= fight.flags, (
        "the kill set %r and the encounter's flags are %r" % (fight.flags, hound_encounter["flags_on_kill"]))
    assert fight.counters["regulars_killed"] == 1


def test_the_path_flag_plays_the_table_it_names():
    """The hook the card asks for: one flag, and the harness selects a path with no manual input."""
    demo = load_tool("play_demo")
    assert sorted(demo.PATH_TABLES) == ["command", "talk"]
    for flag, wanted in sorted(demo.PATH_TABLES.items()):
        run = subprocess.run([sys.executable, PLAY_DEMO, "--path", flag, "--dry-run"],
                             stdin=subprocess.DEVNULL, cwd=ROOT, capture_output=True, text=True, timeout=180)
        assert run.returncode == 0, "--path %s exited %r: %s" % (flag, run.returncode, run.stdout + run.stderr)
        assert "path %r" % flag in run.stdout
        assert "shot table %r" % wanted in run.stdout, (
            "--path %s did not reach the table %r: %s" % (flag, wanted, run.stdout))
    bad = subprocess.run([sys.executable, PLAY_DEMO, "--path", "nonesuch", "--dry-run"],
                         stdin=subprocess.DEVNULL, cwd=ROOT, capture_output=True, text=True, timeout=180)
    assert bad.returncode == 2, "an unknown path exited %r" % bad.returncode
    assert "no path called" in bad.stdout
    both = subprocess.run([sys.executable, PLAY_DEMO, "--path", "talk", "--shot-table", "command-win", "--dry-run"],
                          stdin=subprocess.DEVNULL, cwd=ROOT, capture_output=True, text=True, timeout=180)
    assert both.returncode == 2, "two different plans were accepted together"
