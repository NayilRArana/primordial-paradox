"""The restyled ship rooms (SHIP-RESTYLE, 2026-11-02): ship_small and ship_cabin pinned to their layouts, the new sheet, the
GML rows and the identical collision. A visual restyle changes tiles, tile_legend and tileset only."""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import make_ship_interior as msi  # noqa: E402
import prove_ship_collision as proof  # noqa: E402

TABLE_GML = os.path.join(ROOT, "game", "scripts", "pp_map_tile", "pp_map_tile.gml")
MAP_GML = os.path.join(ROOT, "game", "scripts", "pp_map", "pp_map.gml")
YYP = os.path.join(ROOT, "game", "PrimordialParadox.yyp")
ROOMS = ("ship_small", "ship_cabin")
ROW = re.compile(r'\{\s*ch:\s*"(?P<ch>[^"]*)"\s*,\s*gid:\s*(?P<gid>\d+)\s*,\s*plane:\s*PP_TILE_PLANE_GROUND\s*,\s*group:\s*""\s*,\s*under:\s*-1\s*\}')


def read(path):
    with io.open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def maps():
    return {m["id"]: m for m in json.loads(read(os.path.join(ROOT, "data", "maps", "all.json")))["maps"]}


def classes():
    return json.loads(read(msi.CLASSES))["classes"]


def test_the_committed_rooms_are_the_layouts_stamped_with_the_table():
    built = msi.build_rooms(msi.build_table())
    have = maps()
    for rid in ROOMS:
        assert have[rid] == built[rid], "%s is not the stamp of its layout: run python tools/make_ship_interior.py" % rid


def test_collision_triggers_spawns_actors_and_size_are_identical_to_head():
    cur = proof.rooms(os.path.join(ROOT, "data", "maps", "all.json"))
    base = json.loads(read(msi.BASE))["rooms"]
    for rid in ROOMS:
        assert proof.diffs(base[rid], cur[rid]) == [], "%s changed beyond its tiles" % rid
    assert len(cur["ship_small"]["triggers"]) == 7 and len(cur["ship_cabin"]["triggers"]) == 3


def test_a_glyph_is_solid_exactly_where_the_collision_is_one():
    cls = classes()
    for rid, room in maps().items():
        if rid not in ROOMS:
            continue
        for y, (tiles, col) in enumerate(zip(room["tiles"], room["collision"])):
            for x, (ch, c) in enumerate(zip(tiles, str(col))):
                assert cls[ch]["solid"] == (c == "1"), "%s (%d,%d) %r solid=%s collision %s" % (rid, x, y, ch, cls[ch]["solid"], c)


def test_the_sheet_is_nes_clean_and_matches_the_generator():
    from PIL import Image
    sheet = Image.open(msi.SHEET).convert("RGBA")
    rows = msi.build_table()
    fresh, used, _ = msi.make_sheet(rows)
    assert list(sheet.getdata()) == list(fresh.getdata()), "ship_interior_tiles.png is not what the generator draws"
    assert len(used) <= 25
    nes = {tuple(c) for c in msi.NES}
    for i in range(len(rows)):
        tile = sheet.crop(((i % 16) * 16, (i // 16) * 16, (i % 16) * 16 + 16, (i // 16) * 16 + 16))
        cols = {p[:3] for p in tile.getdata()}
        assert all(c in nes for c in cols), "tile %d uses a colour that is not a 2C02 output" % i
        assert len(cols - {(0, 0, 0)}) <= 3, "tile %d (%s) has more than 3 colours besides the backdrop" % (i, rows[i][1])
        assert tile.getchannel("A").getextrema()[0] == 255, "tile %d is not opaque" % i
    assert open(msi.SHEET, "rb").read() == open(msi.COPY, "rb").read()


def test_the_gml_rows_are_the_class_file():
    src = read(TABLE_GML)
    body = src[src.index(msi.BEGIN):src.index(msi.END)]
    rows = {m.group("ch"): int(m.group("gid")) for m in ROW.finditer(body)}
    cls = classes()
    assert set(rows) == set(cls)
    assert all(rows[g] == c["index"] for g, c in cls.items())
    for name in ("PP_TILE_SET_SHIP_INTERIOR", "PP_TILE_SHEET_SHIP_INTERIOR", "PP_TILE_COLUMNS_SHIP_INTERIOR"):
        assert name in src
    assert "pp_map_tile_rows_ship_interior()" in src.split("function pp_map_tile_build")[1]
    assert "PP_TILE_SHEET_SHIP_INTERIOR" in read(MAP_GML).split("function pp_map_tile_set(")[1].split("\n}")[0]


def test_only_the_two_ship_rooms_name_the_sheet_and_it_reaches_the_build():
    named = sorted(rid for rid, m in maps().items() if m.get("tileset") == "ship_interior_tiles")
    assert named == sorted(ROOMS)
    import sync_art
    side = json.loads(read(msi.SIDECAR))
    assert (side["name"], side["kind"], side["columns"], side["frames"]) == ("ship_interior_tiles", "tileset", 16, len(classes()))
    entry = [e for e in sync_art.source_entries() if e["name"] == "ship_interior_tiles"]
    assert len(entry) == 1 and entry[0]["columns"] == 16
    names = re.findall(r'"name": "([^"]+\.png)",\s*\n\s*"resourceType": "GMIncludedFile"', read(YYP))
    assert names.count("ship_interior_tiles.png") == 1


def test_every_door_and_hatch_glyph_sits_on_a_trigger():
    cls = classes()
    for rid in ROOMS:
        room = maps()[rid]
        at = {(t["x"], t["y"]) for t in room["triggers"]}
        for y, row in enumerate(room["tiles"]):
            for x, ch in enumerate(row):
                if cls[ch]["trigger"] and ch != "D":
                    assert (x, y) in at, "%s door glyph %r at (%d,%d) has no trigger" % (rid, ch, x, y)
