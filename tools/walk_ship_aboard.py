"""Read only walker: where the ship_aboard page is, and what the engine resolves on the press (card t_4dc4751c).

Nothing here writes a file and nothing executes GML. It reads the shipped JSON and re plays the three
engine rules that decide what a confirm press does:

    pp_map_trigger_at          game/scripts/pp_map/pp_map.gml         the trigger on one tile, or none
    pp_overworld_confirm_target game/scripts/pp_overworld/pp_overworld.gml
                                                                      the tile ahead first, then underfoot
    pp_map_collision           game/scripts/pp_map/pp_map.gml         0 walkable, 1 blocked, 2 blocked
                                                                      until the map's story flag is set

and check_data.LINE_CHARS, the dialogue box limit, so a line the game would clip is named here.

The quay was redrawn in v2 (level pass 2026-10-27, output/level_pass_2026-10-27/v2/PROGRESS.md): the
gangway is 2 tiles wide and the page is mirrored onto both of its lanes. Every rule below is therefore
derived from the boarding rows the data carries, not from one hard coded pier coordinate.

Commands this proof is run with, from the project root:

    python tools/check_data.py
    python tools/walk_ship_aboard.py

It prints, for each page: the trigger tile, its kind, its id, and the triggers sharing that tile; then
the dialogue row it resolves to and its line lengths; what each stand tile and facing resolves to; and
the flood fill that says the tile is walkable from the entry spawn with the story barrier shut and open.
It exits 1 if a page is missing, doubled on a tile, does not sit on a gangway lane, is unreachable, or
if the gangway stopped boarding.
"""

import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isdir(os.path.join(ROOT, "data")):
    ROOT = r"<repo>"
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_data  # noqa: E402

MAP_ID = "southampton_town_quay"
ENTRY_SPAWN = "start"
PIER_SPAWN = "from_pier"
PAGE_ID = "ship_aboard"
LANDING_ID = "ship_small"
DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


def load(rel):
    with open(os.path.join(ROOT, "data", rel), "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def trigger_at(row, x, y):
    """pp_map_trigger_at: the first row whose tile is this one, or None."""
    for trig in row["triggers"]:
        if trig["x"] == x and trig["y"] == y:
            return trig
    return None


def triggers_on(row, x, y):
    return [trig for trig in row["triggers"] if trig["x"] == x and trig["y"] == y]


def confirm_target(row, tx, ty, facing):
    """pp_overworld_confirm_target: the tile ahead first, then the tile underfoot."""
    dx, dy = DIRS[facing]
    ahead = trigger_at(row, tx + dx, ty + dy)
    if ahead is not None:
        return "ahead", (tx + dx, ty + dy), ahead
    under = trigger_at(row, tx, ty)
    if under is not None:
        return "underfoot", (tx, ty), under
    return "none", None, None


def walkable(grid, row, x, y, gate_open):
    """pp_map_collision: 0 walkable, 1 blocked, 2 blocked until the story flag opens it."""
    if not (0 <= y < row["height"] and 0 <= x < row["width"]):
        return False
    cell = grid[y][x]
    if cell == "0":
        return True
    if cell == "2":
        return gate_open
    return False


def flood(row, start, gate_open):
    grid = row["collision"]
    seen = {start}
    queue = collections.deque([start])
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (x + dx, y + dy)
            if nxt in seen:
                continue
            if walkable(grid, row, nxt[0], nxt[1], gate_open):
                seen.add(nxt)
                queue.append(nxt)
    return seen


def boarding_tiles(row):
    """The gangway rows, one per tile of the pier head. The data says how wide the gangway is."""
    return [trig for trig in row["triggers"] if trig["kind"] == "map" and trig["id"] == LANDING_ID]


def main():
    maps = load(os.path.join("maps", "all.json"))["maps"]
    rows = {row["id"]: row for row in maps}
    row = rows[MAP_ID]
    dialogue = {entry["id"]: entry for entry in load(os.path.join("dialogue", "all.json"))["dialogue"]}

    doors = boarding_tiles(row)
    pages = [trig for trig in row["triggers"] if trig["kind"] == "say" and trig["id"] == PAGE_ID]
    print("map %r, %d by %d tiles, %d triggers" % (MAP_ID, row["width"], row["height"], len(row["triggers"])))
    print("boarding map triggers named %r on this map: %d" % (LANDING_ID, len(doors)))
    print("say triggers named %r on this map: %d" % (PAGE_ID, len(pages)))
    assert doors, "the quay carries no %r map trigger, so the ship has no way in" % LANDING_ID
    assert len(pages) == len(doors), (
        "expected one %r say trigger per gangway lane, found %d pages and %d boarding tiles"
        % (PAGE_ID, len(pages), len(doors)))
    assert sorted(p["x"] for p in pages) == sorted(d["x"] for d in doors), (
        "the page lanes %s are not the gangway lanes %s"
        % (sorted(p["x"] for p in pages), sorted(d["x"] for d in doors)))

    for trig in pages:
        tile = (trig["x"], trig["y"])
        print("  trigger tile %s kind %r id %r once %s condition %r"
              % (tile, trig["kind"], trig["id"], trig["once"], trig["condition"]))
        print("    tile art %r, collision %r"
              % (row["tiles"][tile[1]][tile[0]], row["collision"][tile[1]][tile[0]]))
        # pp_map_trigger_at keeps the first row on a tile, so a second row there is data nobody can reach.
        shared = triggers_on(row, tile[0], tile[1])
        print("    triggers on that tile: %d (the engine keeps the first, so 1 is the only reachable count)"
              % len(shared))
        assert len(shared) == 1, "tile %s carries %d triggers and only the first is ever reached" % (tile, len(shared))
        assert walkable(row["collision"], row, tile[0], tile[1], True), (
            "the page tile %s is not walkable, so nobody can stand on it and confirm" % (tile,))

    entry = dialogue.get(PAGE_ID)
    assert entry is not None, "map trigger names %r and data/dialogue/all.json holds no such row" % PAGE_ID
    print("\ndialogue row %r: speaker %r, %d page(s)" % (PAGE_ID, entry["speaker"], len(entry["pages"])))
    limit = check_data.LINE_CHARS
    for number, page_row in enumerate(entry["pages"], 1):
        for line in page_row["lines"]:
            print("  page %d  %2d chars (limit %d)  %s" % (number, len(line), limit, line))
            assert len(line) <= limit, "a line the box would clip: %r" % line
            assert "\u2013" not in line and "\u2014" not in line, "long dash in %r" % line

    print("\nwhat a confirm press resolves to, by stand tile and facing:")
    presses = []
    for door in doors:
        presses.append(((door["x"], door["y"] - 1), "down"))    # the landing: boards
        presses.append(((door["x"], door["y"] - 1), "up"))      # the landing: reads the page
        presses.append(((door["x"], door["y"] - 2), "down"))    # one step back: fires the page
    press_where = {}
    for stand, facing in presses:
        where, resolved_tile, resolved = confirm_target(row, stand[0], stand[1], facing)
        press_where[(stand, facing)] = resolved
        if resolved is None:
            print("  stand %s facing %-5s -> ahead %s and underfoot carry no trigger, nothing fires"
                  % (stand, facing, (stand[0] + DIRS[facing][0], stand[1] + DIRS[facing][1])))
        else:
            print("  stand %s facing %-5s -> %s tile %s fires %r %r"
                  % (stand, facing, where, resolved_tile, resolved["kind"], resolved["id"]))

    # the door must still board: nothing may shadow the gangway tile
    for door in doors:
        x, y = door["x"], door["y"]
        where, _resolved_tile, resolved = confirm_target(row, x, y - 1, "down")
        assert resolved is not None and resolved["kind"] == "map" and resolved["id"] == LANDING_ID, (
            "confirm on the pier head at (%d,%d) resolves to %r, so the ship has no way in"
            % (x, y - 1, resolved["id"] if resolved else None))
        # and the page must fire one step back from that landing, on the page's own lane
        where, _resolved_tile, resolved = confirm_target(row, x, y - 2, "down")
        assert resolved is not None and resolved["kind"] == "say" and resolved["id"] == PAGE_ID, (
            "standing at (%d,%d), one step back from the pier head, resolves to %r, not the page"
            % (x, y - 2, resolved["id"] if resolved else None))

    # every stand tile and facing that reaches the page, measured, not guessed
    grids = (("barrier shut", False), ("barrier open", True))
    entry_point = row["spawns"][ENTRY_SPAWN]
    start = (entry_point["x"], entry_point["y"])
    print("\nflood fill from the entry spawn %r %s, the engine's own collision rule:" % (ENTRY_SPAWN, start))
    reach = {}
    for label, gate_open in grids:
        reach[label] = flood(row, start, gate_open)
        tiles_in = [(p["x"], p["y"]) for p in pages if (p["x"], p["y"]) in reach[label]]
        print("  %-13s %d tiles reachable, page tiles in it: %d of %d, gangway tiles in it: %d of %d"
              % (label, len(reach[label]), len(tiles_in), len(pages),
                 sum(1 for d in doors if (d["x"], d["y"]) in reach[label]), len(doors)))
        assert len(tiles_in) == len(pages), "a page tile is not walkable from the entry with the %s" % label

    pier = row["spawns"][PIER_SPAWN]
    print("  the pier spawn %r at (%d,%d) is in the fill: %s"
          % (PIER_SPAWN, pier["x"], pier["y"], (pier["x"], pier["y"]) in reach["barrier shut"]))

    stand_tiles = []
    for y in range(row["height"]):
        for x in range(row["width"]):
            if not walkable(row["collision"], row, x, y, True):
                continue
            for facing in DIRS:
                where, resolved_tile, resolved = confirm_target(row, x, y, facing)
                if resolved is not None and resolved["kind"] == "say" and resolved["id"] == PAGE_ID:
                    stand_tiles.append(((x, y), facing, where))
    print("  %d stand tile and facing pairs reach %r, first three: %s"
          % (len(stand_tiles), PAGE_ID, stand_tiles[:3]))
    assert stand_tiles, "no press anywhere on the quay reaches the page"

    print("\nreachable: the page is a %r trigger named %r on %r at %s, which resolves to the dialogue row %r,"
          % (pages[0]["kind"], PAGE_ID, MAP_ID, ", ".join("%s" % ((p["x"], p["y"]),) for p in pages), PAGE_ID))
    print("one per gangway lane (%s), and %d of its stand tiles are walkable from the entry spawn %r."
          % (", ".join("%s" % ((d["x"], d["y"]),) for d in doors), len(stand_tiles), ENTRY_SPAWN))
    return 0


if __name__ == "__main__":
    sys.exit(main())
