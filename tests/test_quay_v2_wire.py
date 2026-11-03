"""The Town Quay v2 wiring: the game draws the v2 sheet with a table generated from data/tile_classes_quay_v2.json (card WIRE-V2).

The v2 alphabet reuses v1 letters for other tiles ("W" is a wall in v2 and water in v1), so a room drawn with the wrong
table does not fail loudly, it just draws the wrong picture. These tests pin the three things that can drift apart:
the GML rows against the class file, the room's collision grid against the same class file, and the sheet's way into
the build (the room's own `tileset`, the art sidecar and the one Included File entry in the yyp).
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

TABLE_GML = os.path.join(ROOT, "game", "scripts", "pp_map_tile", "pp_map_tile.gml")
MAP_GML = os.path.join(ROOT, "game", "scripts", "pp_map", "pp_map.gml")
YYP = os.path.join(ROOT, "game", "PrimordialParadox.yyp")
CLASSES = os.path.join(ROOT, "data", "tile_classes_quay_v2.json")
MAPS = os.path.join(ROOT, "data", "maps", "all.json")
SHEET = os.path.join(ROOT, "assets", "tiles", "quay_v2", "quay_v2_tiles.png")
SHEET_COPY = os.path.join(ROOT, "game", "sprites_src", "env", "quay", "quay_v2_tiles.png")
ROOM_ID = "southampton_town_quay"
PLANES = {"PP_TILE_PLANE_GROUND": "ground", "PP_TILE_PLANE_PROPS": "props", "PP_TILE_PLANE_ABOVE": "above"}
ROW = re.compile(r'\{\s*ch:\s*(?P<ch>"[^"]*"|chr\(\d+\))\s*,\s*gid:\s*(?P<gid>\d+)\s*,\s*plane:\s*(?P<plane>PP_TILE_PLANE_\w+)\s*,'
                 r'\s*group:\s*"(?P<group>[^"]*)"\s*,\s*under:\s*(?P<under>-?\d+)\s*\}')


def read(path):
    with io.open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def code(path):
    return "\n".join(line.split("//")[0] for line in read(path).splitlines())


def body(path, name):
    source = code(path)
    start = source.find("function %s(" % name)
    assert start >= 0, "%s does not define %s()" % (os.path.basename(path), name)
    return source[start:source.find("\n}", start)]


def classes():
    return json.loads(read(CLASSES))["classes"]


def gml_rows():
    rows = {}
    for match in ROW.finditer(body(TABLE_GML, "pp_map_tile_rows_quay_v2")):
        raw = match.group("ch")
        ch = chr(int(raw[4:-1])) if raw.startswith("chr(") else raw[1:-1]
        rows[ch] = (int(match.group("gid")), PLANES[match.group("plane")], int(match.group("under")))
    return rows


def rooms():
    return {m["id"]: m for m in json.loads(read(MAPS))["maps"]}


def test_every_class_has_exactly_the_row_the_class_file_gives():
    rows = gml_rows()
    cls = classes()
    assert set(rows) == set(cls), "rows and classes differ: %s" % sorted(set(rows) ^ set(cls))
    wrong = ["%r draws gid %d on %s, the class file says %d on %s" % (ch, rows[ch][0], rows[ch][1], c["index"], c["plane"])
             for ch, c in cls.items() if rows[ch][0] != c["index"] or rows[ch][1] != c["plane"]]
    assert wrong == [], "\n".join(wrong)


def test_only_translucent_tiles_lay_the_paving_first():
    from PIL import Image
    sheet = Image.open(SHEET).convert("RGBA")
    cls = classes()
    pave = cls[":"]["index"]
    wrong = []
    for ch, (gid, _plane, under) in gml_rows().items():
        x, y = (gid % 16) * 16, (gid // 16) * 16
        translucent = sheet.crop((x, y, x + 16, y + 16)).getchannel("A").getextrema()[0] < 255
        if under != (pave if translucent else -1):
            wrong.append("%r (%s): under %d but translucent is %s" % (ch, cls[ch]["name"], under, translucent))
    assert wrong == [], "\n".join(wrong)


def test_the_quay_names_its_sheet_and_no_other_room_does():
    named = [rid for rid, room in rooms().items() if room.get("tileset") == "quay_v2_tiles"]
    assert named == [ROOM_ID], "rooms naming quay_v2_tiles: %s" % named


def test_the_game_picks_the_set_by_the_rooms_tileset_and_not_by_its_palette():
    assert "PP_TILE_SHEET_QUAY_V2" in body(MAP_GML, "pp_map_tile_set")
    assert "quay_v2" not in body(TABLE_GML, "pp_map_tile_set_for_room"), "the v2 set must not hang off a room palette id"
    assert "return PP_TILE_SET_SHIP;" in body(TABLE_GML, "pp_map_tile_set_for_room"), "every other room keeps the ship set"


def test_collision_is_the_class_file_cell_by_cell():
    cls = classes()
    room = rooms()[ROOM_ID]
    bad = []
    barriers = []
    for y, (tiles, collision) in enumerate(zip(room["tiles"], room["collision"])):
        for x, (ch, col) in enumerate(zip(tiles, collision)):
            c = cls[ch]
            if col == "2":
                barriers.append((x, y))
                continue
            want = "0" if (c["walkable"] or not c["solid"]) else "1"
            if y == 0:
                want = "1"   # final scope 2026-11-03: row 0 is the map edge guard
            if col != want:
                bad.append("(%d,%d) %r %s: collision %s, class says %s" % (x, y, ch, c["name"], col, want))
    assert bad == [], "\n".join(bad[:12])
    assert barriers == [], "the gate is gone, so no tile is story blocked any more, found %s" % barriers


def test_the_door_tile_is_the_only_trigger_class_and_every_door_has_its_trigger():
    cls = classes()
    assert [ch for ch, c in cls.items() if c["trigger"]] == ["D"]
    room = rooms()[ROOM_ID]
    at = {(t["x"], t["y"]) for t in room["triggers"]}
    doors = [(x, y) for y, row in enumerate(room["tiles"]) for x, ch in enumerate(row) if ch == "D"]
    missing = [d for d in doors if d not in at]
    assert missing == [], "doors without a trigger: %s" % missing


def test_the_sheet_reaches_the_build():
    import sync_art
    sidecar = json.loads(read(os.path.join(ROOT, "game", "sprites_src", "env", "quay", "quay_v2_tiles.json")))
    assert (sidecar["name"], sidecar["kind"], sidecar["columns"], sidecar["frames"]) == ("quay_v2_tiles", "tileset", 16, len(classes()))
    entry = [e for e in sync_art.source_entries() if e["name"] == "quay_v2_tiles"]
    assert len(entry) == 1 and entry[0]["columns"] == 16 and entry[0]["file"] == "quay_v2_tiles.png"
    same = hashlib.sha256(open(SHEET, "rb").read()).digest() == hashlib.sha256(open(SHEET_COPY, "rb").read()).digest()
    assert same, "game/sprites_src/env/quay/quay_v2_tiles.png is not the sheet in assets/tiles/quay_v2"


def test_the_yyp_lists_the_sheet_once_between_quay_tiles_and_rogue_wave():
    names = re.findall(r'"name": "([^"]+\.png)",\s*\n\s*"resourceType": "GMIncludedFile"', read(YYP))
    assert names.count("quay_v2_tiles.png") == 1
    i = names.index("quay_v2_tiles.png")
    assert names[i - 1] == "quay_tiles.png" and names[i + 1] == "rogue_wave.png"
