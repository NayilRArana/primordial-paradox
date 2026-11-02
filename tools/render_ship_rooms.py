#!/usr/bin/env python3
"""render_ship_rooms.py: offline renders of ship_small, ship_cabin and quay_dock_office, before and after the ship restyle.

--before  draws the committed (old) look: ship rooms from game/sprites_src/env/ts_ship.png (the ship table of
          pp_map_tile.gml), the dock office from the v1 quay sheet with the office floor. Writes output/ship_restyle_2026-11-02/before/.
--after   draws the rooms in data/maps/all.json with the new sheet assets/tiles/ship_interior/ship_interior_tiles.png and
          data/tile_classes_ship_interior.json, then writes the before/after contact sheet.
Offline only; never opens the game.
"""
from __future__ import annotations
import io, json, os, re, sys
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTD = os.path.join(ROOT, "output", "ship_restyle_2026-11-02")
T = 16
ROOMS = ("ship_small", "ship_cabin", "quay_dock_office")
SHIP_OLD = {"#": 8, ".": 2, "D": 13, "H": 13, "C": 21, "P": 18, "G": 3}


def load(p):
    with io.open(p, encoding="utf-8-sig") as f:
        return json.load(f)


def rooms_of(path):
    return {m["id"]: m for m in load(path)["maps"]}


def crop(sheet, cols, i):
    x, y = (i % cols) * T, (i // cols) * T
    return sheet.crop((x, y, x + T, y + T))


def draw_grid(room, pick):
    w, h = room["width"], room["height"]
    im = Image.new("RGBA", (w * T, h * T), (15, 15, 20, 255))
    for y, row in enumerate(room["tiles"]):
        for x, ch in enumerate(row):
            t = pick(ch)
            if t is not None:
                im.alpha_composite(t, (x * T, y * T))
    return im


def draw_before(room):
    rid = room["id"]
    if rid == "quay_dock_office":
        sheet = Image.open(os.path.join(ROOT, "game", "sprites_src", "env", "quay", "quay_tiles.png")).convert("RGBA")
        gml = io.open(os.path.join(ROOT, "game", "scripts", "pp_map_tile", "pp_map_tile.gml"), encoding="utf-8-sig").read()
        table = {m.group(1): int(m.group(2)) for m in re.finditer(r'\{ ch: "(.)", gid: (\d+),', gml.split("pp_map_tile_rows_ship")[0])}
        table["."] = 18
        return draw_grid(room, lambda ch: crop(sheet, 8, table[ch]) if ch in table else None)
    sheet = Image.open(os.path.join(ROOT, "game", "sprites_src", "env", "ts_ship.png")).convert("RGBA")
    return draw_grid(room, lambda ch: crop(sheet, 16, SHIP_OLD[ch]))


def draw_after(room, sheet, classes):
    return draw_grid(room, lambda ch: crop(sheet, 16, classes[ch]["index"]))


def labelled(im, text, scale):
    im = im.resize((im.width * scale, im.height * scale), Image.NEAREST).convert("RGB")
    out = Image.new("RGB", (im.width, im.height + 18), (30, 30, 30))
    out.paste(im, (0, 18))
    ImageDraw.Draw(out).text((4, 3), text, fill=(255, 255, 255))
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--before"
    cur = rooms_of(os.path.join(ROOT, "data", "maps", "all.json"))
    if mode == "--before":
        base = os.path.join(ROOT, "data", "ship_restyle_baseline.json")
        src = rooms_of(os.path.join(ROOT, "data", "maps", "all.json")) if not os.path.exists(base) else None
        os.makedirs(os.path.join(OUTD, "before"), exist_ok=True)
        old = load(base)["rooms"] if os.path.exists(base) else None
        for rid in ROOMS:
            room = old[rid] if old else src[rid]
            draw_before(room).resize((room["width"] * T * 3, room["height"] * T * 3), Image.NEAREST).convert("RGB").save(os.path.join(OUTD, "before", rid + "_before.png"))
        print("before rendered")
        return 0
    sheet = Image.open(os.path.join(ROOT, "assets", "tiles", "ship_interior", "ship_interior_tiles.png")).convert("RGBA")
    classes = load(os.path.join(ROOT, "data", "tile_classes_ship_interior.json"))["classes"]
    base = load(os.path.join(ROOT, "data", "ship_restyle_baseline.json"))["rooms"]
    panels = []
    for rid in ("ship_small", "ship_cabin"):
        a = draw_after(cur[rid], sheet, classes)
        a.resize((a.width * 3, a.height * 3), Image.NEAREST).convert("RGB").save(os.path.join(OUTD, "after", rid + "_after.png"))
        b = draw_before(base[rid])
        panels.append((rid, b, a))
    W = sum(max(b.width, 0) + a.width for _, b, a in panels[:1]) * 2 + 24
    rows = []
    for rid, b, a in panels:
        lb, la = labelled(b, "BEFORE " + rid, 2), labelled(a, "AFTER " + rid, 2)
        pair = Image.new("RGB", (lb.width + la.width + 8, max(lb.height, la.height)), (60, 60, 60))
        pair.paste(lb, (0, 0)); pair.paste(la, (lb.width + 8, 0)); rows.append(pair)
    H = sum(r.height + 6 for r in rows); Wd = max(r.width for r in rows)
    sheet_im = Image.new("RGB", (Wd, H), (60, 60, 60)); y = 0
    for r in rows:
        sheet_im.paste(r, (0, y)); y += r.height + 6
    sheet_im.save(os.path.join(OUTD, "after", "contact_sheet.png"))
    print("after rendered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
