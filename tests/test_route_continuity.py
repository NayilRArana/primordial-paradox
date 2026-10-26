"""The demo route, followed by a player (card t_009836b9).

Why this file exists: the route in data/slice.json was walked by the PP_SLICE harness and by nothing else, and a real
launch took the crawl's handoff to the drive and then stopped, because the only reader of a row's `next` sat behind
`pp_slice_walk_enabled()`. So the game played a 10,680 step drive, handed control back on drive_m4_corridor (a map with
no trigger and no exit), and the first fight could not be reached at all. The four checks here are the ones that would
have caught it, each read from a file that already owns the fact:

  1. the chain the fix relies on, row by row, in data/slice.json and the two maps and one scene file it names;
  2. the runner tells the route when a scene starts and when it ends, and the overworld is the one place that lets a
     finished scene go, so every way a scene can end reaches the route;
  3. a route step whose next is the fight hands nothing to a mode, because a player starts that fight through the
     map's own battle trigger and that is what prints `PP: battle start`;
  4. the drive's skip, its row flag and its key, and the corridor's own way out.

No test here runs GameMaker, reads the network or writes a tracked file.
"""

from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SLICE_PATH = os.path.join(ROOT, "data", "slice.json")
SCENES_PATH = os.path.join(ROOT, "data", "scenes", "all.json")
MAPS_PATH = os.path.join(ROOT, "data", "maps", "all.json")
SCENE_GML = os.path.join(ROOT, "game", "scripts", "pp_scene", "pp_scene.gml")
APP_GML = os.path.join(ROOT, "game", "scripts", "pp_app", "pp_app.gml")
OVERWORLD_GML = os.path.join(ROOT, "game", "scripts", "pp_overworld", "pp_overworld.gml")
CAPTURE_TOOL = os.path.join(ROOT, "tools", "capture_first_fight.py")

DRIVE_MAP = "drive_m4_corridor"
QUAY_MAP = "southampton_town_quay"
SHIP_MAP = "ship_small"
DRIVE_SCENE = "drive_to_southampton"
GATE_SCENE = "quay_gate_checkpoint"
BOARDING_SCENE = "ship_boarding"
FIRST_FIGHT = "tutorial_sailors"


def load(path: str):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def rows(path: str, collection: str) -> dict:
    return {row["id"]: row for row in load(path)[collection]}


def route() -> dict:
    return {step["id"]: step for step in load(SLICE_PATH)["route"]["steps"]}


# ---------------------------------------------------------------------------------------------------------------
# 1. The chain a player walks: crawl, drive, arrival, gate, boarding, fight.

def test_the_route_chain_reaches_the_first_fight_through_the_maps_own_trigger():
    steps = route()
    assert steps["crawl"]["next"] == "drive"
    assert steps["drive"]["kind"] == "scene" and steps["drive"]["scene"] == DRIVE_SCENE
    assert steps["drive"]["next"] == "arrival"

    maps = rows(MAPS_PATH, "maps")
    scenes = rows(SCENES_PATH, "scenes")
    assert scenes[DRIVE_SCENE]["map"] == DRIVE_MAP
    assert steps["arrival"]["kind"] == "map" and steps["arrival"]["map"] == QUAY_MAP
    assert steps["arrival"]["next"] == "gate"

    gate_triggers = [trigger for trigger in maps[QUAY_MAP]["triggers"]
                     if trigger.get("kind") == "scene" and trigger.get("id") == GATE_SCENE]
    assert gate_triggers, "southampton_town_quay carries no %r scene trigger, so the arrival has no gate" % GATE_SCENE
    assert steps["gate"]["kind"] == "scene" and steps["gate"]["scene"] == GATE_SCENE
    assert steps["gate"]["next"] == "boarding"

    assert scenes[BOARDING_SCENE]["map"] == SHIP_MAP
    assert steps["boarding"]["kind"] == "scene" and steps["boarding"]["scene"] == BOARDING_SCENE
    assert steps["boarding"]["next"] == "fight"

    # The route's fight step is a row the player completes from the map, so the map has to carry the trigger, and that
    # trigger has to be the one the route names.
    assert steps["fight"]["kind"] == "battle" and steps["fight"]["encounter"] == FIRST_FIGHT
    battle_triggers = [trigger for trigger in maps[SHIP_MAP]["triggers"]
                       if trigger.get("kind") == "battle" and trigger.get("id") == FIRST_FIGHT]
    assert battle_triggers, "the deck carries no %r battle trigger, so the route's fight step has nothing to start it" % (
        FIRST_FIGHT)


def test_the_boarding_scene_ends_next_to_the_first_fights_trigger():
    """The boarding scene's last move puts the hero one tile from the trigger, so one confirm starts the fight."""
    scenes = rows(SCENES_PATH, "scenes")
    boarding = scenes[BOARDING_SCENE]
    maps = rows(MAPS_PATH, "maps")
    trigger = next(trigger for trigger in maps[SHIP_MAP]["triggers"]
                   if trigger.get("kind") == "battle" and trigger.get("id") == FIRST_FIGHT)

    x, y = boarding["start"]["x"], boarding["start"]["y"]
    for command in boarding["commands"]:
        if command.get("cmd") != "move" or command.get("actor", "hero") != "hero":
            continue
        delta = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}[command["dir"]]
        x += delta[0] * command.get("tiles", 1)
        y += delta[1] * command.get("tiles", 1)
    assert abs(x - trigger["x"]) + abs(y - trigger["y"]) == 1, (
        "the boarding scene ends on %d,%d and the fight trigger is at %d,%d, so the hero is not one confirm away"
        % (x, y, trigger["x"], trigger["y"]))


# ---------------------------------------------------------------------------------------------------------------
# 2. The runner tells the route, and one place lets a finished scene go.

def gml_function(text: str, name: str) -> str:
    start = text.find("function %s(" % name)
    assert start >= 0, "the GML carries no function %r" % name
    depth = 0
    index = text.find("{", start)
    body_start = index
    while index < len(text):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[body_start:index + 1]
        index += 1
    raise AssertionError("function %r never closes" % name)


def test_the_runner_tells_the_route_which_scene_took_the_screen():
    take = gml_function(read(SCENE_GML), "pp_scene_take_scene")
    assert "pp_route_scene_started(" in take, (
        "adopting a scene no longer tells the route, so a route scene's end moves nothing")
    assert "variable_struct_exists(_row, \"skippable\")" in take, (
        "the runner no longer reads the row's skippable flag, so the drive's skip is dead")


def test_the_one_place_that_drops_a_finished_scene_tells_the_route():
    step = gml_function(read(OVERWORLD_GML), "pp_overworld_step")
    assert "_world.scene = undefined;" in step, "the overworld no longer drops a finished runner"
    drop = step[step.find("if (!pp_scene_running(_world.scene)) {"):]
    drop = drop[:drop.find("return;")]
    assert "pp_route_scene_finished(" in drop, (
        "the route is not told when a scene ends, so the drive would hand control back and stop again")
    assert drop.index("var _ended_scene = _world.scene;") < drop.index("_world.scene = undefined;"), (
        "the runner is dropped before it is read, so the route cannot tell which scene ended")


def test_a_finished_scene_hands_to_its_rows_next_and_the_fight_waits_for_the_map():
    take_next = gml_function(read(APP_GML), "pp_route_take_next")
    assert "pp_slice_next_id(" in take_next, "the route's next edge is not read, so no row advances"
    assert "pp_slice_handoff(" in take_next, "the handoff door the walk uses is bypassed"
    battle = take_next[take_next.find("PPSliceKind.battle"):]
    assert "return true;" in battle, "the battle branch does not stop the route"
    assert "pp_slice_handoff(" not in battle[:battle.find("return true;")], (
        "a battle step is handed to a mode, so the player never walks into the fight the map authors")


# ---------------------------------------------------------------------------------------------------------------
# 3. The drive's skip and the corridor's way out.

def test_the_drive_is_the_one_scene_that_asks_to_be_skippable():
    scenes = rows(SCENES_PATH, "scenes")
    skippable = [scene_id for scene_id, row in scenes.items() if row.get("skippable") is True]
    assert skippable == [DRIVE_SCENE], (
        "the scenes that can be skipped are %r; the drive is a 178 s opening and the only one that asks" % skippable)

    scene_text = read(SCENE_GML)
    assert re.search(r"#macro\s+PP_SCENE_SKIP_HOLD\s+\d+", scene_text), (
        "pp_scene defines no hold length for the skip")
    step = gml_function(scene_text, "pp_scene_step")
    assert 'pp_action("cancel")' in step, "the skip does not read the cancel action the input table gives the player"
    assert 'pp_pressed("debug_' not in step, "the skip reads a debug key"


def test_the_corridor_carries_its_own_way_out():
    maps = rows(MAPS_PATH, "maps")
    corridor = maps[DRIVE_MAP]
    exits = [trigger for trigger in corridor["triggers"] if trigger.get("kind") == "map"]
    assert len(exits) == 1, "drive_m4_corridor carries %d map exits, and a corridor with none has no way out" % len(
        exits)
    exit_row = exits[0]
    assert exit_row["id"] == QUAY_MAP, "the corridor's exit leads to %r, not the quay the drive arrives at" % (
        exit_row["id"])
    spawns = maps[QUAY_MAP]["spawns"]
    assert exit_row["spawn"] in spawns, "the exit names the spawn %r, which the quay does not carry" % (
        exit_row["spawn"])
    point = spawns[exit_row["spawn"]]
    assert maps[QUAY_MAP]["collision"][point["y"]][point["x"]] == "0", (
        "the exit lands on a blocked tile of the quay")
    assert corridor["collision"][exit_row["y"]][exit_row["x"]] == "0", (
        "the corridor's exit sits on a tile the hero can never stand on")


def test_the_capture_walks_the_route_with_a_players_keys():
    tool = read(CAPTURE_TOOL)
    # The module docstring and the comments are prose about the tool. What must not name PP_SLICE is the code that
    # runs, because an environment flag would make the proof the walk and not a player.
    body = tool.split('"""', 2)[2]
    code = "\n".join(line for line in body.splitlines() if not line.lstrip().startswith("#"))
    assert "PP_SLICE" not in code, (
        "the capture's own code names PP_SLICE, so the proof path would be the walk")
    assert 'cancel*' in code, "the capture does not use the drive's own skip, so it would have to wait 178 s"
    assert '"z"' in code and '"down"' in code, "the capture does not press the keys the route needs"
    for debug_key in ("debug_warp", "debug_step", "debug_flags", '"f1"', '"f2"', '"f3"'):
        assert debug_key not in code, "the capture's code sends the debug key %r" % debug_key


def test_a_scene_that_walks_the_hero_turns_him():
    """A rail move used to leave the facing where the last press put it, so the confirm read the tile behind."""
    start_move = gml_function(read(OVERWORLD_GML), "pp_world_start_move")
    assert "PP scene" in start_move or "facing" in start_move, (
        "pp_world_start_move does not set the hero's facing, so a scene's rail move leaves him looking the wrong way")
    assert '_hero.facing = (_sx > 0) ? "right" : "left"' in start_move, (
        "a horizontal rail move no longer turns the hero right or left")
    assert '_hero.facing = (_sy > 0) ? "down" : "up"' in start_move, (
        "a vertical rail move no longer turns the hero down or up")


if __name__ == "__main__":
    sys.exit(__import__("pytest").main([os.path.abspath(__file__), "-q"]))
