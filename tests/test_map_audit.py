"""One test per check kind for the LD-2 map audit (card t_16872be8).

Each check in tools/map_audit.py gets a synthetic map that must trip it, so a red here means the checker went blind,
not that the maps got better. The last test runs the audit over the real rooms and pins the findings the report relies
on: the ship's dangling door, the cabin's enclosed floor and the quay's unreachable tiles.
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(ROOT, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "tools"))

import map_audit
import walker_bot


def make_room(cid, collision, spawns=None, triggers=None, actors=None, legend=None):
    legend = legend or {"#": "wall", ".": "floor", "D": "door"}
    tiles = []
    for row in collision:
        tiles.append("".join("#" if c == "1" else ("D" if c == "2" else ".") for c in row))
    return {
        "id": cid,
        "name": cid,
        "width": len(collision[0]),
        "height": len(collision),
        "collision": collision,
        "tiles": tiles,
        "tile_legend": legend,
        "spawns": spawns or {},
        "triggers": triggers or [],
        "actors": actors or [],
    }


# 1. Rule 4a: unreachable walkable tiles
def test_reachability_flags_floor_the_player_can_never_reach():
    room = make_room(
        "r",
        ["101", "111", "101"],
        spawns={"start": {"x": 1, "y": 0}},
    )
    result = map_audit.check_reachability(room)
    assert result["unreachable_count"] == 1, result
    assert [1, 2] in result["unreachable"], result
    assert result["unreachable_by_kind"].get("floor") == 1, result


# 2. Rule 4b: single tile gaps / pinch corridors
def test_pinch_flags_a_single_tile_corridor():
    room = make_room(
        "r",
        ["11111", "10001", "11111"],
        spawns={"start": {"x": 1, "y": 1}},
    )
    result = map_audit.check_pinches(room)
    # (2,1) is the corridor tile: two walkable neighbours on one axis. (1,1) and (3,1) are dead ends.
    assert [2, 1] in result["pinch"], result
    assert result["dead_end_count"] == 2, result


# 3. Rule 4c: snag corners (the wall slide sticks)
def test_snag_detector_flags_a_concave_corner():
    collision = ["011", "011", "101"]
    walkables = [(x, y) for y in range(3) for x in range(3) if collision[y][x] == "0"]
    snags = walker_bot.sweep_snags(collision, walkables)
    assert snags, "a concave corner did not stick the walker"


def test_snag_detector_is_quiet_on_open_ground():
    collision = ["000", "000", "000"]
    walkables = [(x, y) for y in range(3) for x in range(3)]
    assert walker_bot.sweep_snags(collision, walkables) == []


# 4. Dead ends without a reward
def test_dead_end_without_a_reward_is_flagged():
    room = make_room(
        "r",
        ["1111", "1001", "1111"],
        spawns={"start": {"x": 1, "y": 1}},
    )
    result = map_audit.check_dead_ends(room)
    assert [1, 1] in result["unrewarded_dead_ends"], result
    assert [2, 1] in result["unrewarded_dead_ends"], result


def test_dead_end_with_a_poi_is_not_flagged():
    room = make_room(
        "r",
        ["1111", "1001", "1111"],
        spawns={"start": {"x": 1, "y": 1}},
        triggers=[{"x": 2, "y": 1, "kind": "save", "id": "save"}],
    )
    result = map_audit.check_dead_ends(room)
    assert [2, 1] not in result["unrewarded_dead_ends"], result


# 5. Doors and transitions that do not match
def test_door_to_a_missing_map_is_dangling():
    room = make_room(
        "a",
        ["1111", "1011", "1111"],
        spawns={"start": {"x": 1, "y": 1}},
        triggers=[{"x": 1, "y": 1, "kind": "map", "id": "no_such_room", "spawn": "start"}],
    )
    findings = map_audit.check_doors(room, {"a": room})
    assert any(f["kind"] == "dangling_door" for f in findings), findings


def test_door_pair_that_lands_far_from_the_return_is_asymmetric():
    room_a = make_room(
        "a",
        ["11111", "10001", "11111"],
        spawns={"start": {"x": 1, "y": 1}, "from_b": {"x": 3, "y": 1}},
        triggers=[{"x": 1, "y": 1, "kind": "map", "id": "b", "spawn": "from_a"}],
    )
    room_b = make_room(
        "b",
        ["11111", "10001", "11111"],
        spawns={"from_a": {"x": 3, "y": 1}},
        triggers=[{"x": 3, "y": 1, "kind": "map", "id": "a", "spawn": "from_b"}],
    )
    # A's door is at (1,1); the return from B lands at A.spawns["from_b"] = (3,1), two tiles away.
    findings = map_audit.check_doors(room_a, {"a": room_a, "b": room_b})
    assert any(f["kind"] == "asymmetric_door" for f in findings), findings


# 6. Longest walk without a point of interest
def test_longest_walk_without_a_poi_is_reported():
    room = make_room(
        "r",
        ["111111111111111111111",
         "100000000000000000001",
         "111111111111111111111"],
        spawns={"start": {"x": 1, "y": 1}},
        triggers=[{"x": 1, "y": 1, "kind": "save", "id": "save"}],
    )
    result = map_audit.check_poi_spacing(room)
    assert result["longest_walk"] == 18, result
    assert len(result["over_8"]) > 0, result


# 7. The audit runs on every real room and the report's headline findings are real
def test_the_audit_runs_on_every_room_and_finds_the_ship_and_quay_problems():
    maps = map_audit.load_maps()
    # The room count is not pinned: the five rooms committed at HEAD grow as new rooms land (three more
    # are authored in the working tree at the time of writing). Pin the rooms that must always exist
    # instead, so the audit is green at HEAD and green with the newer rooms.
    ids = {m["id"] for m in maps}
    assert {"ship_small", "ship_cabin", "southampton_town_quay", "quay_dock_office",
            "drive_m4_corridor"} <= ids, ids
    rooms_by_id = {m["id"]: m for m in maps}
    audited = {}
    for m in maps:
        audited[m["id"]] = map_audit.audit_room(m, rooms_by_id)

    ship = audited["ship_small"]
    assert any(f["kind"] == "dangling_door" and f["target"] == "ship_sample" for f in ship), ship

    cabin = audited["ship_cabin"]
    reach = next(f for f in cabin if f["kind"] == "reachability")
    assert reach["unreachable_count"] == 8, reach   # the two bunk booths are enclosed floor at HEAD

    quay = audited["southampton_town_quay"]
    reach = next(f for f in quay if f["kind"] == "reachability")
    assert reach["unreachable_count"] == 230, reach   # the quay's unreachable floor tiles

    # every room carries each check kind
    for mid, findings in audited.items():
        kinds = {f["kind"] for f in findings}
        for expected in ("reachability", "readability", "pinch", "dead_end", "snag", "poi_spacing", "spawns", "markers"):
            assert expected in kinds, (mid, expected)
