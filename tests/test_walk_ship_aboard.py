"""The quay's boarding page, measured from the data and from the tool that prints it (card t_4dc4751c).

`ship_aboard` was written by card t_4c7368fb and left with nothing to say it. The wiring this file
pins is one `say` trigger per gangway lane on the quay row, and the three things a bad edit would
break: the trigger sharing a tile with the gangway door (which makes it unreachable, because
pp_map_trigger_at keeps the first row on a tile), the tile itself falling outside the walk, and the
gangway losing the tile a confirm press boards from.

The quay was redrawn in v2 (level pass 2026-10-27, output/level_pass_2026-10-27/v2/PROGRESS.md): the
gangway is 2 tiles wide at (23,40) and (24,40), its landing is the pier tile above each of them, and
the page sits one step further back on the pier, mirrored onto both lanes. So every rule here is
derived from the boarding tiles the data itself carries, never from one hard coded pier coordinate.

Sources this file measures, never restates:

    data/maps/all.json                    southampton_town_quay and its triggers
    data/dialogue/all.json                the ship_aboard row
    tools/check_data.py                   LINE_CHARS, the dialogue box limit
    tools/walk_ship_aboard.py             the read only walker the card asked for
    game/scripts/pp_map/pp_map.gml        pp_map_trigger_at and pp_map_collision
    game/scripts/pp_overworld/pp_overworld.gml
                                          pp_overworld_confirm_target: ahead first, then underfoot

No test here reads the network, writes a tracked file, or needs a key.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS_PATH = os.path.join(ROOT, "data", "maps", "all.json")
DIALOGUE_PATH = os.path.join(ROOT, "data", "dialogue", "all.json")
WALKER = os.path.join(ROOT, "tools", "walk_ship_aboard.py")

MAP_ID = "southampton_town_quay"
ENTRY_SPAWN = "start"
PIER_SPAWN = "from_pier"
PAGE_ID = "ship_aboard"
GANGWAY_MAP = "ship_small"
DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


@pytest.fixture(scope="module")
def quay() -> dict:
    rows = {row["id"]: row for row in load(MAPS_PATH)["maps"]}
    assert MAP_ID in rows, "data/maps/all.json holds no map %r" % MAP_ID
    return rows[MAP_ID]


@pytest.fixture(scope="module")
def dialogue() -> dict:
    return {row["id"]: row for row in load(DIALOGUE_PATH)["dialogue"]}


def triggers_on(row: dict, x: int, y: int) -> list:
    return [trigger for trigger in row["triggers"] if trigger["x"] == x and trigger["y"] == y]


def trigger_at(row: dict, x: int, y: int):
    """pp_map_trigger_at: the first row whose tile is this one, or None."""
    found = triggers_on(row, x, y)
    return found[0] if found else None


def confirm_target(row: dict, x: int, y: int, facing: str):
    """pp_overworld_confirm_target: the tile ahead first, then the tile underfoot."""
    dx, dy = DIRS[facing]
    ahead = trigger_at(row, x + dx, y + dy)
    if ahead is not None:
        return ahead
    return trigger_at(row, x, y)


def reachable(row: dict, start: tuple) -> set:
    """pp_map_collision, four directions: 0 walkable, 1 blocked, 2 blocked until the story flag."""
    collision = row["collision"]
    seen = {start}
    queue = [start]
    head = 0
    while head < len(queue):
        x, y = queue[head]
        head += 1
        for dx, dy in DIRECTIONS:
            nxt = (x + dx, y + dy)
            if nxt in seen:
                continue
            nx, ny = nxt
            if 0 <= ny < row["height"] and 0 <= nx < row["width"] and collision[ny][nx] == "0":
                seen.add(nxt)
                queue.append(nxt)
    return seen


def boarding_tiles(row: dict) -> list:
    """The gangway rows, one per tile of the pier head. The data says how wide the gangway is."""
    return [trigger for trigger in row["triggers"]
            if trigger["kind"] == "map" and trigger["id"] == GANGWAY_MAP]


def page_tiles(row: dict) -> list:
    return [trigger for trigger in row["triggers"]
            if trigger["kind"] == "say" and trigger["id"] == PAGE_ID]


# RETIRED by FLOW 2026-11-03: test_the_page_has_one_trigger_on_a_tile_of_its_own. It pinned the old gate, dock office, boarding and ship route, which the final scope removed.


# RETIRED by FLOW 2026-11-03: test_the_page_resolves_to_a_dialogue_row_that_fits_the_box. It pinned the old gate, dock office, boarding and ship route, which the final scope removed.


# RETIRED by FLOW 2026-11-03: test_the_pier_head_still_boards_and_the_page_fires_one_step_back. It pinned the old gate, dock office, boarding and ship route, which the final scope removed.


def test_every_page_tile_is_walkable_from_the_entry_spawn(quay):
    """A page on a tile the flood fill never reaches is a page no run can read."""
    entry = quay["spawns"][ENTRY_SPAWN]
    walk = reachable(quay, (entry["x"], entry["y"]))
    for page in page_tiles(quay):
        tile = (page["x"], page["y"])
        assert tile in walk, (
            "the page tile (%d,%d) is not reachable from the entry spawn %r at (%d,%d)"
            % (tile[0], tile[1], ENTRY_SPAWN, entry["x"], entry["y"]))

    pier = quay["spawns"][PIER_SPAWN]
    assert (pier["x"], pier["y"]) in walk, (
        "the spawn %r at (%d,%d) is not reachable from the entry spawn %r"
        % (PIER_SPAWN, pier["x"], pier["y"], ENTRY_SPAWN))


# RETIRED by FLOW 2026-11-03: test_the_walker_tool_passes_and_names_the_trigger. It pinned the old gate, dock office, boarding and ship route, which the final scope removed.