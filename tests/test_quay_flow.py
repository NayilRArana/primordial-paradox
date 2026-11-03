"""FLOW (2026-11-03): the final route, title, crawl, Town Quay, Captain Morgan, Percy, credits, proved from data and GML text.

Nothing here runs GameMaker. Every check reads a committed file. What is proven:

  1. the route is title, crawl, quay, morgan, percy and nothing else, and no step, trigger, actor or scene reachable
     from it leaves the Town Quay (no drive, gate, dock office, boarding or ship);
  2. Captain Morgan and Percy stand on walkable tiles, the hero reaches a tile next to each, and the bridge cannot be
     entered without crossing a wind trigger that only fires while Morgan is unresolved;
  3. every new scene parses against the checker's command set, ends on `end`, and the Percy outcome scenes call the
     credits with both variants; the fights set the outcome flags and the flags are known to the save;
  4. the GML carries the D7 log lines, the killed actor filter, the credits call and the new game map.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import deque

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import check_data  # noqa: E402

QUAY = "southampton_town_quay"
OLD_SCENES = {"quay_gate_checkpoint", "quay_gate_truth", "quay_gate_bluff", "quay_gate_authority", "quay_yard_walk",
              "quay_dock_office_play", "ship_boarding", "ship_log", "drive_to_southampton", "percy_lore_stop",
              "percy_rematch", "prometheus_interrupt", "navy_aftermath", "navy_aftermath_kill"}


def _load(*parts):
    with open(os.path.join(ROOT, *parts), "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _text(*parts):
    with open(os.path.join(ROOT, *parts), "r", encoding="utf-8-sig", newline="") as handle:
        return handle.read()


SLICE = _load("data", "slice.json")
STEPS = {s["id"]: s for s in SLICE["route"]["steps"]}
SCENES = {s["id"]: s for s in _load("data", "scenes", "all.json")["scenes"]}
MAPS = {m["id"]: m for m in _load("data", "maps", "all.json")["maps"]}
DIALOGUE = {d["id"]: d for d in _load("data", "dialogue", "all.json")["dialogue"]}
ENCOUNTERS = {e["id"]: e for e in _load("data", "encounters", "all.json")["encounters"]}
FLAGS = set(_load("data", "flags.json")["flags"])
Q = MAPS[QUAY]
ACTORS = {a["id"]: a for a in Q["actors"]}


def walk_chain():
    order, step = [], SLICE["route"]["first"]
    while step and step not in order:
        order.append(step)
        step = STEPS[step].get("next", "")
    return order


def walkable(x, y):
    return 0 <= y < len(Q["collision"]) and 0 <= x < len(Q["collision"][y]) and Q["collision"][y][x] == "0"


def flood(start, blocked=()):
    seen, queue = {start}, deque([start])
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in seen or n in blocked or not walkable(*n):
                continue
            seen.add(n)
            queue.append(n)
    return seen


def reach_tiles(actor):
    """Walkable tiles one step from the actor, the tiles the hero stands on to talk."""
    return [(actor["x"] + dx, actor["y"] + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if walkable(actor["x"] + dx, actor["y"] + dy)]


# ------------------------------------------------------------------------------------------------ 1. the route


def test_the_route_is_title_crawl_quay_morgan_percy():
    assert walk_chain() == ["title", "crawl", "quay", "morgan", "percy"]
    assert STEPS["quay"]["kind"] == "map" and STEPS["quay"]["map"] == QUAY
    assert STEPS["morgan"]["scene"] == "quay_morgan_encounter" and STEPS["percy"]["scene"] == "quay_percy_encounter"
    assert STEPS["morgan"].get("player") and STEPS["percy"].get("player")
    assert SLICE["map"] == QUAY and SLICE["spawn"] in Q["spawns"]


def test_the_header_scene_and_encounter_resolve():
    assert SLICE["scene"] in SCENES and SLICE["encounter"] in ENCOUNTERS


def test_nothing_reachable_from_the_route_leaves_the_quay():
    seeds = {STEPS[s]["scene"] for s in STEPS if STEPS[s].get("scene")} | {SLICE["scene"]}
    seeds |= {t["id"] for t in Q["triggers"] if t["kind"] == "scene"}
    seeds |= {a["scene"] for a in Q["actors"] if a.get("scene")}
    seen, todo = set(), list(seeds)
    while todo:
        sid = todo.pop()
        if sid in seen:
            continue
        seen.add(sid)
        for cmd in SCENES[sid]["commands"]:
            if cmd["cmd"] == "branch":
                todo.append(cmd["scene"])
    assert not (seen & OLD_SCENES), sorted(seen & OLD_SCENES)
    assert {SCENES[s]["map"] for s in seen} == {QUAY}
    for t in Q["triggers"]:
        assert t["kind"] != "map", "the quay has a door to %s" % t["id"]
    for sid in seen:
        for cmd in SCENES[sid]["commands"]:
            if cmd["cmd"] == "battle":
                assert cmd["id"] in ("morgan_gate", "percy"), cmd


def test_new_game_opens_on_the_quay():
    config = _text("game", "scripts", "pp_config", "pp_config.gml")
    assert '#macro PP_NEW_GAME_MAP "%s"' % QUAY in config


# ------------------------------------------------------------------------------------------------ 2. the people


@pytest.mark.parametrize("actor_id", ["morgan", "percy"])
def test_an_actor_stands_on_a_walkable_tile_the_hero_can_reach(actor_id):
    actor = ACTORS[actor_id]
    assert walkable(actor["x"], actor["y"])
    start = Q["spawns"][SLICE["spawn"]]
    reachable = flood((start["x"], start["y"]), blocked={(a["x"], a["y"]) for a in Q["actors"]})
    tiles = [t for t in reach_tiles(actor) if t in reachable]
    assert tiles, "no talking tile next to %s is reachable from the start" % actor_id
    scene = SCENES[actor["scene"]]
    assert (scene["start"]["x"], scene["start"]["y"]) in reach_tiles(actor)


def test_morgan_is_top_left_and_percy_is_on_the_bridge():
    assert ACTORS["morgan"]["x"] <= 10 and ACTORS["morgan"]["y"] <= 14
    pier = [x for x in range(len(Q["collision"][34])) if Q["collision"][34][x] == "0"]
    assert ACTORS["percy"]["x"] in pier and ACTORS["percy"]["y"] >= 33


def test_the_bridge_is_shut_by_the_wind_until_morgan_is_resolved():
    wind = [t for t in Q["triggers"] if t["id"] == "quay_bridge_wind"]
    assert wind and all(t.get("touch") is True and t["kind"] == "scene" and t["condition"] == "!morgan_resolved"
                        for t in wind)
    wind_tiles = {(t["x"], t["y"]) for t in wind}
    start = Q["spawns"][SLICE["spawn"]]
    reachable = flood((start["x"], start["y"]), blocked=wind_tiles)
    percy = ACTORS["percy"]
    assert not [t for t in reach_tiles(percy) if t in reachable], "the hero reaches Percy without the wind"
    open_world = flood((start["x"], start["y"]))
    assert [t for t in reach_tiles(percy) if t in open_world], "Percy is not reachable at all"
    # the wind scene pushes the hero back up the bridge
    scene = SCENES["quay_bridge_wind"]
    assert (scene["start"]["x"], scene["start"]["y"]) in wind_tiles
    assert [c for c in scene["commands"] if c["cmd"] == "move" and c["dir"] == "up"]


def test_no_two_triggers_share_a_tile_and_no_trigger_sits_on_a_blocked_tile():
    seen = set()
    for t in Q["triggers"]:
        key = (t["x"], t["y"])
        assert key not in seen
        seen.add(key)
        if t["kind"] in ("scene", "save"):
            assert walkable(*key), t


# ------------------------------------------------------------------------------------------------ 3. the scenes


FLOW_SCENES = ["quay_arrival", "quay_morgan_encounter", "quay_morgan_spare", "quay_morgan_kill", "quay_bridge_wind",
               "quay_percy_encounter", "quay_percy_spare", "quay_percy_kill"]


@pytest.mark.parametrize("scene_id", FLOW_SCENES)
def test_a_flow_scene_parses_and_ends(scene_id):
    scene = SCENES[scene_id]
    assert scene["map"] == QUAY
    commands = scene["commands"]
    assert commands[-1]["cmd"] == "end"
    for cmd in commands:
        assert cmd["cmd"] in check_data.SCENE_COMMANDS
        if cmd["cmd"] == "say":
            assert cmd["id"] in DIALOGUE


def test_check_data_accepts_the_data():
    assert check_data.check(ROOT) == []


def test_the_fights_branch_to_both_outcomes_and_percy_ends_in_credits():
    for scene_id, enemy in (("quay_morgan_encounter", "morgan"), ("quay_percy_encounter", "percy")):
        cmds = SCENES[scene_id]["commands"]
        assert [c["id"] for c in cmds if c["cmd"] == "battle"] == [{"morgan": "morgan_gate", "percy": "percy"}[enemy]]
        branches = {c["flag"]: c["scene"] for c in cmds if c["cmd"] == "branch"}
        assert set(branches) == {enemy + "_killed", enemy + "_spared"}
    variants = {}
    for scene_id, variant in (("quay_percy_spare", "spare"), ("quay_percy_kill", "kill")):
        found = [c["variant"] for c in SCENES[scene_id]["commands"] if c["cmd"] == "credits"]
        assert found == [variant]
        variants[variant] = scene_id
    assert set(variants) == {"spare", "kill"}
    # Morgan's outcome scenes do not roll credits
    for scene_id in ("quay_morgan_spare", "quay_morgan_kill"):
        assert not [c for c in SCENES[scene_id]["commands"] if c["cmd"] == "credits"]


def test_recruiting_percy_is_a_message_and_a_flag():
    commands = SCENES["quay_percy_spare"]["commands"]
    assert {"cmd": "setflag", "name": "percy_recruited"} in commands
    lines = [line for page in DIALOGUE["quay_percy_after_spare"]["pages"] for line in page["lines"]]
    assert "* PERCY JOINS THE PARTY!" in lines


def test_the_encounters_set_the_outcome_flags():
    for enc, who in (("morgan_gate", "morgan"), ("percy", "percy")):
        row = ENCOUNTERS[enc]
        assert who + "_killed" in row["flags_on_kill"] and who + "_spared" in row["flags_on_spare"]
    assert "morgan_resolved" in ENCOUNTERS["morgan_gate"]["flags_on_kill"]
    assert "morgan_resolved" in ENCOUNTERS["morgan_gate"]["flags_on_spare"]


def test_every_flag_the_flow_uses_is_known_to_the_save():
    used = {"morgan_killed", "morgan_spared", "morgan_resolved", "percy_killed", "percy_spared", "percy_recruited"}
    assert used <= FLAGS
    for actor in ACTORS.values():
        assert actor["done_flag"] in FLAGS and actor["gone_flag"] in FLAGS


def test_the_new_text_fits_the_box_and_has_no_dashes():
    ids = [d for d in DIALOGUE if d.startswith("quay_morgan_") or d.startswith("quay_percy_") or d == "quay_bridge_wind"]
    assert len(ids) >= 14
    for dialogue_id in ids:
        pages = DIALOGUE[dialogue_id]["pages"]
        assert 1 <= len(pages) <= 3
        for page in pages:
            assert 1 <= len(page["lines"]) <= 3
            for line in page["lines"]:
                assert len(line) <= 28, line
                assert chr(0x2014) not in line and chr(0x2013) not in line, line


def test_the_gate_dialogue_is_gone_and_the_quay_has_no_gate_office_or_boarding_trigger():
    assert not [t for t in Q["triggers"] if t["id"].startswith("quay_gate") or t["id"] in ("ship_aboard", "quay_yard_walk")]
    for line_id in ("quay_gate_checkpoint", "quay_gate_choice", "quay_gate_truth", "quay_gate_bluff",
                    "quay_gate_authority"):
        assert line_id not in DIALOGUE, line_id


# ------------------------------------------------------------------------------------------------ 4. the GML


def test_the_gml_prints_the_d7_lines_and_filters_the_killed():
    overworld = _text("game", "scripts", "pp_overworld", "pp_overworld.gml")
    assert '"PP: encounter start "' in overworld and '"PP: encounter result "' in overworld
    credits_path = os.path.join(ROOT, "game", "scripts", "pp_credits", "pp_credits.gml")
    if os.path.isfile(credits_path):
        assert '"PP: credits start spare"' in _text("game", "scripts", "pp_credits", "pp_credits.gml")
        assert '"PP: credits start kill"' in _text("game", "scripts", "pp_credits", "pp_credits.gml")
    assert "pp_overworld_actor_new(_a)" in overworld and "gone_flag" in overworld
    scene = _text("game", "scripts", "pp_scene", "pp_scene.gml")
    assert "pp_overworld_actor_new(_a)" in scene and 'case "credits":' in scene
    assert "pp_flow_credits_start(_credits_variant)" in scene
    app = _text("game", "scripts", "pp_app", "pp_app.gml")
    assert "pp_flow_encounter_start(_params.encounter_id)" in app


def test_the_credits_door_exists_or_the_flow_falls_back_to_the_title():
    overworld = _text("game", "scripts", "pp_overworld", "pp_overworld.gml")
    assert 'asset_get_index("pp_credits_start")' in overworld and "back to the title" in overworld
    path = os.path.join(ROOT, "game", "scripts", "pp_credits", "pp_credits.gml")
    if os.path.isfile(path):
        assert re.search(r"function\s+pp_credits_start\s*\(\s*_variant", _text("game", "scripts", "pp_credits", "pp_credits.gml"))


def test_the_state_is_derived_from_the_saved_flags():
    overworld = _text("game", "scripts", "pp_overworld", "pp_overworld.gml")
    assert 'string(_id) + "_killed"' in overworld and 'string(_id) + "_spared"' in overworld
    save = _text("game", "scripts", "pp_save", "pp_save.gml")
    assert "pp_save_flag_allowed" in save and "global.pp_data.flags.flags" in save
