#!/usr/bin/env python3
"""make_quay_town.py: the Town Quay v2 room, stamped from an ASCII layout (card LD-4, 2026-10-27).

The design is the text file tools/quay_town_layout.txt: 48 x 45 glyphs of knowledge/MAP-STYLE-GUIDE.md Part A, started from
Appendix A and edited by hand. This script turns it into the room southampton_town_quay in data/maps/all.json:

  1. read the grid and the @ lines (spawns, actor, triggers, story barrier, plaza box, OSM links, fight spot);
  2. dress it: a roof palette per building (A and B alternate along a street), tree variants, step and plank ramps, water bands,
     paving variation that never lets a run grow past the guide's limits;
  3. write tiles (one glyph per tile, the alphabet of data/tile_classes_quay_v2.json), collision, spawns, triggers, actors;
  4. splice the room into all.json as text, so every other room stays byte for byte;
  5. write the v2 block of data/maps/LEVEL-PROVENANCE.json (OSM link, anchors, changes against Appendix A).

Run:  python tools/make_quay_town.py            write data/maps/all.json and the provenance
      python tools/make_quay_town.py --diff     print the cell changes against Appendix A, change nothing
      python tools/make_quay_town.py --dry      build and self check, change nothing

OSM data only (ODbL, openstreetmap.org/copyright); no Google data. Nothing is copied from any game: every tile is drawn by
tools/make_quay_tiles.py.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYOUT = os.path.join(ROOT, "tools", "quay_town_layout.txt")
GUIDE = os.path.join(ROOT, "knowledge", "MAP-STYLE-GUIDE.md")
CLASSES = os.path.join(ROOT, "data", "tile_classes_quay_v2.json")
MAPS = os.path.join(ROOT, "data", "maps", "all.json")
PROVENANCE = os.path.join(ROOT, "data", "maps", "LEVEL-PROVENANCE.json")
OSM_BASE = os.path.join(ROOT, "data", "maps", "osm", "southampton_town_quay_base.json")
ROOM_ID = "southampton_town_quay"
WIDTH, HEIGHT = 48, 45
LANTERN = "Λ"

# Building glyphs (signs inside a building's box belong to it; a freestanding signboard does not).
ROOF_GLYPHS = set("^rQqCE+" + LANTERN)
WALL_GLYPHS = set("WVPwxGtkAD")
STRUCT = ROOF_GLYPHS | WALL_GLYPHS

WATER_NAMES = {"water_mid", "water_deep", "water_foam"}
BUILDING_NAMES = {"roof_ridge_a", "roof_eave_a", "roof_ridge_b", "roof_eave_b", "chimney_a", "chimney_b", "wall",
                  "wall_boards", "pilaster", "window_lit", "window_dark", "awning", "gable_clock", "ticket_window",
                  "finial", "band_stripe", "quay_wall_face", "pier_rail", "hull", "deck_plank", "cabin", "mast",
                  "funnel", "bow", "crane_mast", "crane_base", "lighthouse_gallery"}


# --------------------------------------------------------------------------------------------------------------------
# reading

def read_text(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def load_classes():
    return json.loads(read_text(CLASSES))["classes"]


def parse_layout(text):
    """The grid rows and the @ lines. A comment line starts with '# ' (a grid row can start with the glyph '#')."""
    grid, dirs = [], []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        if line == "#" or line.startswith("# "):
            continue
        if line.startswith("@"):
            dirs.append(line[1:].split())
            continue
        grid.append(line)
    return grid, dirs


def parse_directives(dirs):
    out = {"spawns": {}, "actors": [], "triggers": [], "barriers": [], "plaza": None, "osm": [], "fightspots": []}
    for t in dirs:
        op = t[0]
        if op == "spawn":
            out["spawns"][t[1]] = {"x": int(t[2]), "y": int(t[3])}
        elif op == "actor":
            out["actors"].append({"id": t[1], "x": int(t[2]), "y": int(t[3]), "facing": t[4], "kind": t[5],
                                  "dialogue": t[6]})
        elif op == "trigger":
            row = {"x": int(t[1]), "y": int(t[2]), "kind": t[3], "id": t[4]}
            opts = dict(o.split("=", 1) for o in t[5:])
            if "spawn" in opts:
                row["spawn"] = opts["spawn"]
            row["once"] = opts.get("once", "false") == "true"
            row["condition"] = opts.get("condition", "")
            if "marker_kind" in opts:
                row["marker_kind"] = opts["marker_kind"]
            out["triggers"].append(row)
        elif op == "barrier":
            out["barriers"].append((int(t[1]), int(t[2]), t[3]))
        elif op == "plaza":
            out["plaza"] = tuple(int(v) for v in t[1:5])
        elif op == "osm":
            out["osm"].append({"door": (int(t[1]), int(t[2])), "archetype": t[3], "osm": (int(t[4]), int(t[5])),
                               "name": " ".join(t[6:])})
        elif op == "fightspot":
            out["fightspots"].append({"id": t[1], "x": int(t[2]), "y": int(t[3])})
        else:
            raise ValueError("unknown directive @%s" % op)
    return out


def load_layout(path=LAYOUT):
    grid, dirs = parse_layout(read_text(path))
    if len(grid) != HEIGHT or any(len(r) != WIDTH for r in grid):
        raise ValueError("layout must be %d rows of %d glyphs, got %d rows, widths %s"
                         % (HEIGHT, WIDTH, len(grid), sorted({len(r) for r in grid})))
    return grid, parse_directives(dirs)


def appendix_a_rows():
    """Appendix A of the style guide, one string of 48 glyphs per row."""
    text = read_text(GUIDE)
    start = text.index("# APPENDIX A.")
    rows = []
    for line in text[start:].splitlines():
        m = re.match(r"^(\d\d)  (\S{48})$", line)
        if m:
            rows.append(m.group(2))
        if len(rows) == HEIGHT:
            break
    return rows


def diff_against_appendix(grid):
    base = appendix_a_rows()
    changes = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if base[y][x] != grid[y][x]:
                changes.append((x, y, base[y][x], grid[y][x]))
    return changes


# --------------------------------------------------------------------------------------------------------------------
# buildings (also used by tests/test_map_style.py)

def buildings(rows):
    """Each building: connected structure glyphs (4 connected) plus the signs inside the box. Returns dicts."""
    h, w = len(rows), len(rows[0])
    seen = set()
    out = []
    for y in range(h):
        for x in range(w):
            if (x, y) in seen or rows[y][x] not in STRUCT:
                continue
            stack, cells = [(x, y)], []
            seen.add((x, y))
            while stack:
                cx, cy = stack.pop()
                cells.append((cx, cy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and rows[ny][nx] in STRUCT:
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            if all(rows[cy][cx] == "A" for (cx, cy) in cells):
                continue                      # an awning on its own is a market stall (A19), not a building
            xs = [c[0] for c in cells]
            ys = [c[1] for c in cells]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            cellset = set(cells)
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    if rows[yy][xx] == "S":
                        cellset.add((xx, yy))
            out.append({"x0": x0, "x1": x1, "y0": y0, "y1": y1, "cells": cellset})
    out.sort(key=lambda b: (b["y1"], b["x0"]))
    return out


# --------------------------------------------------------------------------------------------------------------------
# dressing

def hashf(x, y, salt=0):
    n = (x * 374761393 + y * 668265263 + salt * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    n ^= n >> 16
    return (n & 0xFFFF) / 65535.0


def _run_back(grid, x, y, glyph, dx, dy):
    n = 0
    cx, cy = x + dx, y + dy
    while 0 <= cx < len(grid[0]) and 0 <= cy < len(grid) and grid[cy][cx] == glyph and n < 20:
        n += 1
        cx += dx
        cy += dy
    return n


def scatter(grid, base, alt, density, max_run, skip, salt):
    """Swap some base tiles for alt: at the seeded density, and always before a run would pass max_run."""
    for y in range(len(grid)):
        for x in range(len(grid[0])):
            if grid[y][x] != base or skip(x, y):
                continue
            left = _run_back(grid, x, y, base, -1, 0)
            up = _run_back(grid, x, y, base, 0, -1)
            if left + 1 > max_run or up + 1 > max_run or hashf(x, y, salt) < density:
                grid[y][x] = alt


def dress(rows, plaza=None):
    """Final glyph grid: roof palettes, tree variants, step and plank ramps, water bands, paving variation."""
    grid = [list(r) for r in rows]
    h, w = len(grid), len(grid[0])
    # roof palette B (slate) on every second building of a street band (the door row groups the band)
    bands = {}
    for b in buildings(rows):
        bands.setdefault(b["y1"], []).append(b)
    for key in sorted(bands):
        for i, b in enumerate(sorted(bands[key], key=lambda b: b["x0"])):
            if i % 2 == 1:
                for (x, y) in b["cells"]:
                    grid[y][x] = {"^": "Q", "r": "q", "C": "E"}.get(grid[y][x], grid[y][x])
    for y in range(h):
        for x in range(w):
            if grid[y][x] == "T":
                grid[y][x] = "TYZ"[(x + 2 * y) % 3]
            elif grid[y][x] == "p":
                grid[y][x] = "p" if y % 2 == 0 else "j"
    # steps: light, mid, dark down a column
    for x in range(w):
        run = 0
        for y in range(h):
            if rows[y][x] == "s":
                grid[y][x] = "seu"[min(run, 2)]
                run += 1
            else:
                run = 0
    # water: foam row under the quay face, deep from row 38, seeded foam flecks so no run passes 7
    for y in range(h):
        for x in range(w):
            if grid[y][x] == "~":
                if y > 0 and rows[y - 1][x] == "#":
                    grid[y][x] = "-"
                elif y >= 38:
                    grid[y][x] = "_"
    # water: regular foam flecks (a skewed lattice, not a scatter) so the sea reads as waves; run limit as a backstop
    for y in range(h):
        for x in range(w):
            if grid[y][x] == "~" and (x + 2 * y + 1) % 7 == 0:
                grid[y][x] = "-"
            elif grid[y][x] == "_" and (x + 4 * y) % 9 == 0:
                grid[y][x] = "-"
    nowhere = lambda x, y: False
    scatter(grid, "~", "-", 0.0, 7, nowhere, 3)
    scatter(grid, "_", "-", 0.0, 8, nowhere, 4)
    # paving: the plaza box keeps its own pattern; everywhere else a skewed lattice of alt stones (an orderly bond)
    def in_plaza(x, y):
        return bool(plaza) and plaza[0] <= x <= plaza[2] and plaza[1] <= y <= plaza[3]
    for y in range(h):
        for x in range(w):
            if grid[y][x] == ":" and not in_plaza(x, y) and (x + 2 * y) % 7 == 0:
                grid[y][x] = ","
    scatter(grid, ":", ",", 0.0, 6, in_plaza, 5)
    return ["".join(r) for r in grid]


# --------------------------------------------------------------------------------------------------------------------
# room data

def kind_of(name, cls):
    if name in WATER_NAMES:
        return "water"
    if name == "door":
        return "door"
    if cls["walkable"]:
        return "floor"
    if name in BUILDING_NAMES:
        return "wall"
    return "prop"


def collision_char(cls):
    return "0" if (cls["walkable"] or not cls["solid"]) else "1"


def build_room(base_room, grid, d, classes):
    dressed = dress(grid, d["plaza"])
    tiles = [list(r) for r in dressed]
    collision = [[collision_char(classes[ch]) for ch in row] for row in tiles]
    for (x, y, glyph) in d["barriers"]:
        tiles[y][x] = glyph
        collision[y][x] = "2"
    tiles = ["".join(r) for r in tiles]
    collision = ["".join(r) for r in collision]
    used = sorted(set("".join(tiles)), key=lambda ch: classes[ch]["index"])
    missing = [ch for ch in used if ch not in classes]
    if missing:
        raise ValueError("glyphs not in tile_classes_quay_v2.json: %s" % missing)
    legend = {ch: kind_of(classes[ch]["name"], classes[ch]) for ch in used}
    room = {}
    for key, value in base_room.items():
        room[key] = value
    room["width"], room["height"] = WIDTH, HEIGHT
    room["tile_legend"] = legend
    room["tileset"] = "quay_v2_tiles"   # card WIRE-V2: the game picks the v2 tile table from this field
    room["tiles"] = tiles
    room["collision"] = collision
    room["spawns"] = d["spawns"]
    room["triggers"] = d["triggers"]
    room["actors"] = d["actors"]
    problems = layout_problems(grid, tiles, collision, d)
    return room, dressed, problems


def layout_problems(grid, tiles, collision, d):
    """Hard errors only (the style findings live in tests/test_map_style.py)."""
    problems = []
    trig_at = {(t["x"], t["y"]) for t in d["triggers"]}
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == "D" and (x, y) not in trig_at:
                problems.append("door at (%d,%d) has no @trigger" % (x, y))
    for t in d["triggers"]:
        if collision[t["y"]][t["x"]] != "0":
            problems.append("trigger %s at (%d,%d) is on collision %s" % (t["id"], t["x"], t["y"], collision[t["y"]][t["x"]]))
    for name, s in d["spawns"].items():
        if collision[s["y"]][s["x"]] != "0":
            problems.append("spawn %s at (%d,%d) is blocked" % (name, s["x"], s["y"]))
        touching = [t["id"] for t in d["triggers"] if (t["x"], t["y"]) == (s["x"], s["y"])
                    and t["kind"] in ("map", "say", "battle", "marker")]
        if touching:   # a scene trigger fires on confirm, so the gate spawn may stand on its own checkpoint (as in v1)
            problems.append("spawn %s at (%d,%d) stands on a touch trigger %s" % (name, s["x"], s["y"], touching))
    for a in d["actors"]:
        if collision[a["y"]][a["x"]] != "0":
            problems.append("actor %s at (%d,%d) is blocked" % (a["id"], a["x"], a["y"]))
    return problems


# --------------------------------------------------------------------------------------------------------------------
# writing all.json without touching any other room

def render_room(room, nl, ensure_ascii):
    text = json.dumps(room, indent=2, ensure_ascii=ensure_ascii)
    return (nl + "    ").join(text.split("\n"))


def splice_room(text, room_id, room):
    nl = "\r\n" if "\r\n" in text else "\n"
    pat = re.compile(r'^    \{\r?\n      "id": "%s",' % re.escape(room_id), re.M)
    m = pat.search(text)
    if not m:
        raise SystemExit("room %s not found in all.json" % room_id)
    start = text.index("{", m.start())
    old, end = json.JSONDecoder().raw_decode(text, start)
    span = text[start:end]
    ensure_ascii = True
    exact = False
    for candidate in (True, False):
        if render_room(old, nl, candidate) == span:
            ensure_ascii, exact = candidate, True
            break
    if not exact:
        print("note: the old room text is not reproduced exactly by json.dumps(indent=2); formatting of this room may differ")
    new_span = render_room(room, nl, ensure_ascii)
    return text[:start] + new_span + text[end:], exact


def write_maps(room):
    with io.open(MAPS, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    before = json.loads(text)
    new_text, exact = splice_room(text, ROOM_ID, room)
    after = json.loads(new_text)
    ids_before = [m["id"] for m in before["maps"]]
    ids_after = [m["id"] for m in after["maps"]]
    assert ids_before == ids_after, "room order changed"
    for a, b in zip(before["maps"], after["maps"]):
        if a["id"] != ROOM_ID:
            assert a == b, "room %s changed" % a["id"]
    with io.open(MAPS, "w", encoding="utf-8", newline="") as handle:
        handle.write(new_text)
    return exact


# --------------------------------------------------------------------------------------------------------------------
# provenance

def osm_link(d):
    base = json.loads(read_text(OSM_BASE))
    bw, bh = base["width"], base["height"]
    rows = []
    for item in d["osm"]:
        ox, oy = item["osm"]
        cx = round(ox * (WIDTH - 1) / (bw - 1))
        cy = round(oy * (HEIGHT - 1) / (bh - 1))
        dx, dy = item["door"]
        rows.append({"name": item["name"], "archetype": item["archetype"], "osm_door_tile": [ox, oy],
                     "osm_compressed_tile": [cx, cy], "layout_door_tile": [dx, dy],
                     "distance_tiles": abs(cx - dx) + abs(cy - dy)})
    return {"osm_frame": [bw, bh], "layout_frame": [WIDTH, HEIGHT], "compression": "x * 47 / 52, y * 44 / 55, rounded",
            "landmarks": rows}


def write_provenance(d, changes):
    prov = json.loads(read_text(PROVENANCE))
    if "doors" in prov and "v1_osm_doors" not in prov:
        prov["v1_osm_doors"] = prov.pop("doors")
    if "landmarks" in prov and "v1_osm_landmarks" not in prov:
        prov["v1_osm_landmarks"] = prov.pop("landmarks")
    prov["extract"] = ("data/maps/osm/southampton_town_quay_base.json (the OSM traced room, 53 by 56 at 8 m a tile) is the "
                       "source of street order and landmark order; the v2 room redraws it from the style guide (Part D)")
    prov["design_notes"] = ("v2 (2026-10-27): street graph order, landmark order and names kept from OSM; every building is a "
                            "clean archetype, streets are widened to the standard classes, the shore is one straight quay "
                            "with a pier, steps and a gangway. The layout is tools/quay_town_layout.txt, started from "
                            "Appendix A of knowledge/MAP-STYLE-GUIDE.md.")
    prov["v2"] = {
        "layout": "tools/quay_town_layout.txt",
        "generator": "tools/make_quay_town.py",
        "tiles": "assets/tiles/quay_v2/quay_v2_tiles.png with data/tile_classes_quay_v2.json (glyph = tile character)",
        "streets": ("arrival street 4 wide runs north to south into the north lane (3 wide, east to west); a 4 wide gate passage "
                    "and two 4 wide alleys carry the lane down to the quay road (4 wide, along the water); the forecourt, the "
                    "coping and the pier follow, as in the OSM order road, terminal, quay, pier"),
        "osm_link": osm_link(d),
        "dropped_to_props": ["Canute's Palace", "The Watergate Ruin", "Old Bowling Green", "Red Jet ticket office (the terminal's ticket windows)"],
        "landmark_roles": {"St Julians Chapel": "the chapel A8 at the head of the arrival street (door 29,7)",
                           "God's House Tower": "the tower A7 at the west end of the quay (door 3,28)",
                           "Town Quay pier": "the boarding pier A10 on the axis x22..24", "Red Funnel Terminal 1": "the terminal A5"},
        "anchors": {"spawns": d["spawns"],
                    "dock_office_door": [t for t in d["triggers"] if t["id"] == "quay_dock_office"][0],
                    "boarding_triggers": [t for t in d["triggers"] if t["id"] == "ship_small"],
                    "fight_spots": d["fightspots"]},
        "changes_against_appendix_a": len(changes),
    }
    with io.open(PROVENANCE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(prov, indent=2, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------------------------------------------------

def build_all():
    grid, d = load_layout()
    classes = load_classes()
    data = json.loads(read_text(MAPS))
    base = [m for m in data["maps"] if m["id"] == ROOM_ID][0]
    room, dressed, problems = build_room(base, grid, d, classes)
    return {"grid": grid, "directives": d, "classes": classes, "room": room, "dressed": dressed, "problems": problems}


def main(argv):
    grid, d = load_layout()
    changes = diff_against_appendix(grid)
    if "--diff" in argv:
        by_row = {}
        for (x, y, a, b) in changes:
            by_row.setdefault(y, []).append("%d:%s>%s" % (x, a, b))
        for y in sorted(by_row):
            print("y%02d %s" % (y, " ".join(by_row[y])))
        print("%d cells differ from Appendix A" % len(changes))
        return 0
    built = build_all()
    for p in built["problems"]:
        print("PROBLEM:", p)
    if built["problems"]:
        return 1
    if "--dry" in argv:
        print("dry run ok: %d tiles, %d triggers" % (WIDTH * HEIGHT, len(built["room"]["triggers"])))
        return 0
    exact = write_maps(built["room"])
    write_provenance(d, changes)
    print("wrote %s (room %s %dx%d, %d triggers, format exact=%s) and %s"
          % (os.path.relpath(MAPS, ROOT), ROOM_ID, WIDTH, HEIGHT, len(built["room"]["triggers"]), exact,
             os.path.relpath(PROVENANCE, ROOT)))
    print("%d cells differ from Appendix A" % len(changes))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
