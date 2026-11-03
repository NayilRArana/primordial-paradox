#!/usr/bin/env python3
"""render_hero_zeus.py: offline before and after renders of the hero (card HERO-ZEUS). Never opens the game.

Writes output/hero_zeus_2026-11-02/: hero_8dir_before.png, hero_8dir_after.png (standing and walking, 3x), and one
overworld frame each of the quay and ship_small, before (old 16x16 zander_ow_v2) and after (zeus_ow_walk8, 8 px higher).
The frame mapping is read from zeus_ow_walk8.json and the same table the GML pp_world_dir8_index uses."""
from __future__ import annotations
import io, json, os, sys
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output", "hero_zeus_2026-11-02")
CH = os.path.join(ROOT, "game", "sprites_src", "chars")
T = 16
HERO8_DY = 0
VECTORS = {"down": (0, 1), "down_left": (-1, 1), "left": (-1, 0), "up_left": (-1, -1), "up": (0, -1), "up_right": (1, -1),
           "right": (1, 0), "down_right": (1, 1)}


def dir8_index(dx, dy):
    """Mirror of pp_world_dir8_index in pp_overworld.gml."""
    if dx == 0 and dy == 0:
        return 0
    if dx == 0:
        return 0 if dy > 0 else 4
    if dy == 0:
        return 2 if dx < 0 else 6
    if dx < 0:
        return 1 if dy > 0 else 3
    return 5 if dy < 0 else 7


def old_facing(dx, dy):
    """The 4 way rule of a diagonal held from the start: the horizontal half wins."""
    if dx != 0:
        return "right" if dx > 0 else "left"
    return "down" if dy > 0 else "up"


OLD_ROW = {"down": 0, "up": 1, "right": 2, "left": 3}


def frames(path, w, h):
    im = Image.open(path).convert("RGBA")
    return [im.crop((i * w, 0, i * w + w, h)) for i in range(im.width // w)]


OLD = frames(os.path.join(CH, "zander_ow_v2.png"), 16, 16)
NEW = frames(os.path.join(CH, "zeus_ow_walk8.png"), 16, 16)
meta = json.load(io.open(os.path.join(CH, "zeus_ow_walk8.json"), encoding="utf-8-sig"))
assert [k for k in VECTORS] == meta["directions"], "direction order differs from the sheet json"


def old_frame(dx, dy, step):
    return OLD[OLD_ROW[old_facing(dx, dy)] * 2 + step]


def new_frame(dx, dy, step):
    return NEW[dir8_index(dx, dy) * 2 + step]


def contact(pick, title, scale=3):
    cw, ch, pad, top = 16 * scale + 16, 16 * scale + 24, 6, 34
    im = Image.new("RGB", (cw * 8 + pad, top + (ch + 14) * 2 + pad), (70, 70, 80))
    d = ImageDraw.Draw(im)
    d.text((6, 4), title, fill=(255, 255, 255))
    for row, (label, step) in enumerate((("stand", 0), ("walk", 1))):
        for i, (name, (dx, dy)) in enumerate(VECTORS.items()):
            f = pick(dx, dy, step)
            x, y = pad + i * cw + 8, top + row * (ch + 14)
            tile_top = y + (ch - 16 * scale - 0)
            d.rectangle((x - 2, y - 2, x + 16 * scale + 1, y + ch - 8 + 1), outline=(110, 110, 125))
            big = f.resize((f.width * scale, f.height * scale), Image.NEAREST)
            im.paste(big, (x, y + (ch - 8) - big.height), big)
            fy = y + (ch - 8) - 1
            d.line((x - 4, fy, x + 16 * scale + 3, fy), fill=(255, 60, 60))   # the feet row, same for both
            d.text((x, y + ch - 6), "%s %s" % (name, label), fill=(230, 230, 230))
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    contact(old_frame, "BEFORE: zander_ow_v2 16x16, 4 directions (diagonal = horizontal half); red line = feet row").save(os.path.join(OUT, "hero_8dir_before.png"))
    contact(new_frame, "AFTER: zeus_ow_walk8 16x16, 8 directions; red line = same feet row (draw dy %d)" % HERO8_DY).save(os.path.join(OUT, "hero_8dir_after.png"))
    import render_quay_v2 as q
    import render_ship_rooms as s
    maps = {m["id"]: m for m in json.load(io.open(os.path.join(ROOT, "data", "maps", "all.json"), encoding="utf-8-sig"))["maps"]}
    sheet_q = Image.open(q.SHEET).convert("RGBA")
    quay = q.draw_v2(q.room_of(q.MAPS), sheet_q, q.load_json(q.CLASSES)["classes"])
    ship_sheet = Image.open(os.path.join(ROOT, "assets", "tiles", "ship_interior", "ship_interior_tiles.png")).convert("RGBA")
    ship = s.draw_after(maps["ship_small"], ship_sheet, s.load(os.path.join(ROOT, "data", "tile_classes_ship_interior.json"))["classes"])
    jobs = [("quay", quay, maps["southampton_town_quay"]["spawns"]["from_pier"], (1, 1)),
            ("quay", quay, maps["southampton_town_quay"]["spawns"]["from_pier"], (0, -1)),
            ("ship_small", ship, maps["ship_small"]["spawns"]["start"], (1, 0))]
    done = set()
    for name, base, sp, vec in jobs:
        for tag in ("before", "after"):
            im = base.copy()
            px, py = sp["x"] * T, sp["y"] * T
            if tag == "before":
                f = old_frame(vec[0], vec[1], 1)
                im.alpha_composite(f, (px, py))
            else:
                f = new_frame(vec[0], vec[1], 1)
                im.alpha_composite(f, (px, py + HERO8_DY))
            camx = max(0, min(px + 8 - 128, im.width - 256))
            camy = max(0, min(py + 8 - 120, im.height - 240))
            view = im.crop((camx, camy, camx + 256, camy + 240))
            view = view.resize((768, 720), Image.NEAREST).convert("RGB")
            ImageDraw.Draw(view).text((6, 4), "%s %s hero vector %s (offline render, camera on the hero)" % (tag.upper(), name, vec), fill=(255, 255, 0))
            view.save(os.path.join(OUT, "%s_%s_%s.png" % (name, "diag" if vec == (1, 1) else ("up" if vec == (0, -1) else "right"), tag)))
    print("rendered into", OUT)


if __name__ == "__main__":
    main()
