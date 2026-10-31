#!/usr/bin/env python3
"""make_title_cone_v2.py: spr_title_cone, the headlight cone overlay, redrawn with a stepped falloff.

Card t_b825be3e (AUTO-SPRITE-NEXT). The queue row `spr_title_cone` (P1) names one defect that is
still open on the shipped sheet: it is one flat entry. Measured on game/sprites_src/title/
spr_title_cone.png on 2026-10-23: 96x40, one frame, ONE colour, $20 #f8f8f8 on all 1246 drawn
pixels, 0 off palette, nes_check PASS. The row's craft rule SP-034 says a light cone is three
stepped entries, never one flat grey, and the row's palette_roles give the three: $28 gold at the
lamp, $10 light grey at the mid, $00 grey at the far end, and no ink, because a beam is light, not
an object.

What this writes (deterministic: no clock, no randomness, no window, no network):

  output/redraws/spr_title_cone.png      96 x 40, 1 frame, entries $28 / $10 / $00
  output/spr_title_cone_ground.png       96 x 40, the road the cone is drawn over

The two are written together because the row cannot be judged without both: a layer reads or it
does not read against the pixels under it (ART-BIBLE RULE 0), and palette_synergy needs that ground.

Nothing here writes the shipped tree. game/sprites_src/title/spr_title_cone.png belongs to
tools/art/make_title_world.py build_cone(), and whether the shipped sheet moves from one flat $20
to these three entries is a gamedev call, posted as Q: on the queue row (the band palette under the
cone is bg3, which carries no light mid entry).

HOW THE BEAM IS AUTHORED

The 96 x 40 frame is twelve 8 x 8 tiles across and five down, and the beam is written as a
character grid: one letter per pixel, "." for transparent, the letters looked up in a palette of
data/nes_palette.json entries only. The grid is authored from three tables written out by hand,
because a 96 x 40 wedge cannot be typed as 40 lines of 96 characters without a reader losing the
shape:

  CONE_HALF     the half height of the beam in pixels at each of the twelve tile columns, narrow at
                the lamp and opening with distance. Hand written, one number per column.
  CONE_CENTRE   the row the beam is centred on, one number per column, so it drifts down as the road
                recedes, the way the shipped build_cone() drifts it.
  CONE_BAND     which of the three entries each column spends: gold at the lamp, light grey at the
                mid, grey at the far end. Four columns each, so the falloff is three steps and every
                8 x 8 tile holds exactly one entry.

The fill rule inside a column is written out in cone_grid() and is the only code here: an edge row
is dithered A.A.A.A. so the beam's edge reads as light rather than as a solid slab, everything
inside the core is solid, and everything outside is transparent. No pixel is copied, scaled,
recoloured or traced from any other game's art.

Usage:
    python tools/art/make_title_cone_v2.py
"""

from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLEAR = (0, 0, 0, 0)

# 2C02 entries, named, so no reader has to decode a hex twice.
# The hardware context this row is drawn inside, quoted from the page data/nes_palette.json cites:
# "Backgrounds and sprites each have 4 palettes of 4 colors, located at $3F00-$3F1F in VRAM." That is
# why the beam's three steps have to be spent one per tile column and not four per tile, and why the
# falloff is three entries and stops: sp0 $0F $00 $28 and sp2 $0C $10 $20 are the two of the title's
# four sprite palettes that carry any of them. (source: https://www.nesdev.org/wiki/PPU_palettes)
GOLD = "#f8b800"     # $28, at the lamp
GREY_L = "#bcbcbc"   # $10, the mid beam
GREY = "#7c7c7c"     # $00, the far end
INK = "#000000"      # $0F, the title's backdrop, only ever the ground's own colour here

CONE_W = 96
CONE_H = 40
TILE = 8
COLUMNS = CONE_W // TILE      # 12
ROWS = CONE_H // TILE         # 5

# Hand written: the beam's half height, in pixels, at each tile column. 2 px at the lamp, 13 at the
# far end, so the beam opens 11 px over 96 px of road.
CONE_HALF = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

# Hand written: the row the beam is centred on, per tile column, drifting down with the road.
CONE_CENTRE = [18, 19, 20, 20, 21, 22, 23, 23, 24, 25, 26, 26]

# Hand written: the entry each tile column spends. Four columns per step, so a step is 32 px of
# road and the falloff is visible at 1x without a fourth entry.
CONE_BAND = ["A"] * 4 + ["B"] * 4 + ["C"] * 4

LETTERS = {"A": GOLD, "B": GREY_L, "C": GREY}


def cone_grid():
    """The 96 x 40 character grid: "A" gold, "B" light grey, "C" grey, "." transparent.

    Per column: the core (half height minus two) is solid, the outer two rows on each side are
    dithered so the beam's edge is a light step and not a slab, and the rest is transparent.
    """
    rows = []
    for y in range(CONE_H):
        line = []
        for column in range(COLUMNS):
            letter = CONE_BAND[column]
            half = CONE_HALF[column]
            centre = CONE_CENTRE[column]
            distance = abs(y - centre)
            for x_in_tile in range(TILE):
                if distance <= max(1, half - 2):
                    line.append(letter)
                elif distance <= half:
                    x = column * TILE + x_in_tile
                    line.append(letter if (x + y) % 2 == 0 else ".")
                else:
                    line.append(".")
        rows.append("".join(line))
    for index, row in enumerate(rows):
        if len(row) != CONE_W:
            raise SystemExit("row %d is %d characters, the frame is %d wide" % (index, len(row), CONE_W))
    return rows


def grid_image(rows):
    """The character grid as an RGBA image. Nothing is drawn that is not a letter in the grid."""
    image = Image.new("RGBA", (CONE_W, CONE_H), CLEAR)
    pixels = image.load()
    for y, row in enumerate(rows):
        for x, letter in enumerate(row):
            if letter == ".":
                continue
            hexs = LETTERS[letter]
            pixels[x, y] = (int(hexs[1:3], 16), int(hexs[3:5], 16), int(hexs[5:7], 16), 255)
    return image


def build_ground(root):
    """The 96 x 40 of road the cone is composited over, rebuilt from the shipped title layers.

    The reader is the runtime's: data/title.json lists the scrolling layers with their y and their
    scroll speed, tools/art/compose_title_preview.py draws them at camera x, and the cone goes in at
    title.json's own cone.x, cone.y (140, 200). At camera 0 every speed term is 0, so the ground is
    the layer stack itself, cropped at the cone's placement with the cone left out. That is the same
    reading the menu cursor's ground got on card t_ae4bbd15: the composed title under the sprite,
    with the sprite removed, so palette_synergy measures the pixels the beam really falls on.
    """
    with open(os.path.join(root, "data", "title.json"), "r", encoding="utf-8-sig") as handle:
        title = json.load(handle)
    cone_x, cone_y = int(title["cone"]["x"]), int(title["cone"]["y"])
    frame = Image.new("RGBA", (256, 240), (0, 0, 0, 255))
    used = []
    for layer in title["layers"]:
        path = os.path.join(root, "game", "sprites_src", "title", layer["name"] + ".png")
        if not os.path.isfile(path):
            raise SystemExit("a title layer is missing: %s" % path)
        with Image.open(path) as handle:
            strip = handle.convert("RGBA").copy()
        offset = int(round(0.0 * layer["speed"])) % strip.width
        doubled = Image.new("RGBA", (strip.width * 2, strip.height), CLEAR)
        doubled.paste(strip, (0, 0))
        doubled.paste(strip, (strip.width, 0))
        frame.alpha_composite(doubled.crop((offset, 0, offset + 256, strip.height)), (0, layer["y"]))
        used.append(layer["name"])
    ground = frame.crop((cone_x, cone_y, cone_x + CONE_W, cone_y + CONE_H))
    return ground, (cone_x, cone_y), used


def audit(image, rows):
    """The row's numbers in words: entries, the worst 8 x 8 tile, and how much of the frame is drawn."""
    counts = {}
    for y, row in enumerate(rows):
        for x, letter in enumerate(row):
            if letter == ".":
                continue
            counts[letter] = counts.get(letter, 0) + 1
    worst, worst_at = 0, None
    for top in range(0, CONE_H, TILE):
        for left in range(0, CONE_W, TILE):
            seen = set()
            for y in range(top, top + TILE):
                for x in range(left, left + TILE):
                    letter = rows[y][x]
                    if letter != ".":
                        seen.add(letter)
            if len(seen) > worst:
                worst, worst_at = len(seen), (left // TILE, top // TILE)
    drawn = sum(counts.values())
    print("  spr_title_cone %dx%d  %d tiles  entries %s  drawn %d px  worst tile %d %s"
          % (CONE_W, CONE_H, COLUMNS * ROWS,
             " ".join("%s=%d" % (LETTERS[k], v) for k, v in sorted(counts.items())),
             drawn, worst, worst_at))
    return counts, worst, drawn


def main() -> int:
    out = os.path.join(ROOT, "output", "redraws")
    os.makedirs(out, exist_ok=True)

    rows = cone_grid()
    image = grid_image(rows)
    path = os.path.join(out, "spr_title_cone.png")
    image.save(path, "PNG")
    counts, worst, drawn = audit(image, rows)

    ground, at, layers = build_ground(ROOT)
    ground_path = os.path.join(ROOT, "output", "spr_title_cone_ground.png")
    ground.save(ground_path, "PNG")
    print("  ground %dx%d at %d,%d from %d title layers: %s"
          % (ground.width, ground.height, at[0], at[1], len(layers), os.path.basename(ground_path)))
    print("  wrote %s" % os.path.relpath(path, ROOT).replace(os.sep, "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
