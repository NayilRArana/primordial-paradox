#!/usr/bin/env python3
"""quay_collision_audit.py: the Town Quay collision against what is drawn and against the hero's feet box (final scope item 2).

Reads data/maps/all.json (the room), data/tile_classes_quay_v2.json (what each glyph is) and the tile sheet
assets/tiles/quay_v2/quay_v2_tiles.png (what is really drawn), then lists:

  solid_walkable    a drawn solid tile (tree, wall, roof, window, water, fence, prop) whose collision is not 1
  open_blocked      a tile drawn as ground, a doorway or steps whose collision is 1 (a blocked tile that looks walkable)
  sparse_blocked    a blocked tile whose art covers under 35 percent of the cell (a lamp, a sign): the blocked square is
                    larger than the thing you see; informational, these are single props
  walkable_edge     a walkable tile on map row 0 (a 16 px figure standing there walks off the screen)
  story_tiles       any collision 2 tile (blocked only until a story flag: not allowed since the gate is gone)
  door_not_enterable a door tile that is blocked, or a walkable tile that is not ground, door, step or overhead

OVERHEAD names the two tiles that are drawn above the hero on purpose (crane jib and hook): walkable by design.

The hero numbers are read from the shipped GML, not retyped: the feet box (pp_config.gml) and the sprite height (the
sidecar of the hero sheet). overlap_north is how many pixels of the figure are drawn over the wall tile in front of it
when the feet touch it: sprite height minus feet height. The limit is half the figure.

Run: python tools/quay_collision_audit.py        (exit 1 when a list that must be empty is not)
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS = os.path.join(ROOT, "data", "maps", "all.json")
CLASSES = os.path.join(ROOT, "data", "tile_classes_quay_v2.json")
SHEET = os.path.join(ROOT, "assets", "tiles", "quay_v2", "quay_v2_tiles.png")
CONFIG = os.path.join(ROOT, "game", "scripts", "pp_config", "pp_config.gml")
HERO_JSON = os.path.join(ROOT, "game", "sprites_src", "chars", "zeus_ow_walk8.json")
ROOM_ID = "southampton_town_quay"
T = 16
OVERHEAD = {"J", "U"}
GROUND_NAMES = {"open_ground", "paving", "paving_alt", "paving_drain", "coping", "pier_plank_light", "pier_plank_dark",
                "step_light", "step_mid", "step_dark", "gangway", "door"}
SPARSE_LIMIT = 0.35


def read_json(path):
    with io.open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def macro(name):
    text = io.open(CONFIG, "r", encoding="utf-8-sig").read()
    return int(re.search(r"^#macro\s+%s\s+(\d+)\s*$" % name, text, re.M).group(1))


def room():
    return [m for m in read_json(MAPS)["maps"] if m["id"] == ROOM_ID][0]


def coverage(sheet, index):
    """Share of the 16x16 cell the art covers with opaque pixels."""
    x, y = (index % 16) * T, (index // 16) * T
    alpha = sheet.crop((x, y, x + T, y + T)).getchannel("A")
    return sum(1 for v in alpha.tobytes() if v > 0) / float(T * T)


def audit():
    classes = read_json(CLASSES)["classes"]
    sheet = Image.open(SHEET).convert("RGBA")
    cover = {ch: coverage(sheet, c["index"]) for ch, c in classes.items()}
    r = room()
    out = {k: [] for k in ("solid_walkable", "open_blocked", "sparse_blocked", "walkable_edge", "story_tiles",
                           "door_not_enterable")}
    for y, (tiles, coll) in enumerate(zip(r["tiles"], r["collision"])):
        for x, (ch, col) in enumerate(zip(tiles, coll)):
            c = classes[ch]
            if col == "2":
                out["story_tiles"].append((x, y, ch))
            drawn_solid = c["solid"] and not c["walkable"]
            drawn_open = c["name"] in GROUND_NAMES
            if drawn_solid and col != "1":
                out["solid_walkable"].append((x, y, ch, c["name"]))
            if drawn_open and col == "1" and y != 0:   # row 0 is the edge guard on purpose
                out["open_blocked"].append((x, y, ch, c["name"]))
            if col == "1" and drawn_solid and cover[ch] < SPARSE_LIMIT:
                out["sparse_blocked"].append((x, y, ch, c["name"], round(cover[ch], 2)))
            if col == "0" and not drawn_open and ch not in OVERHEAD:
                out["door_not_enterable"].append((x, y, ch, c["name"]))
            if y == 0 and col == "0":
                out["walkable_edge"].append((x, y, ch))
    sprite_h = read_json(HERO_JSON)["frame_h"]
    feet_h, feet_w = macro("PP_HERO_FEET_H"), macro("PP_HERO_FEET_W")
    out["hero"] = {"sprite_h": sprite_h, "feet_w": feet_w, "feet_h": feet_h, "overlap_north": sprite_h - feet_h,
                   "overlap_limit": sprite_h // 2}
    return out


MUST_BE_EMPTY = ("solid_walkable", "open_blocked", "story_tiles", "walkable_edge", "door_not_enterable")


def problems(result):
    bad = ["%s: %s" % (k, result[k][:6]) for k in MUST_BE_EMPTY if result[k]]
    hero = result["hero"]
    if hero["overlap_north"] > hero["overlap_limit"]:
        bad.append("hero overlaps the wall in front by %d px, limit %d" % (hero["overlap_north"], hero["overlap_limit"]))
    return bad


def main():
    result = audit()
    for key in MUST_BE_EMPTY + ("sparse_blocked",):
        print("%-18s %d" % (key, len(result[key])))
    print("hero", result["hero"])
    bad = problems(result)
    for line in bad:
        print("PROBLEM", line)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
