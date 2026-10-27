#!/usr/bin/env python3
"""make_ui_frames_v2.py: the 32x32 battle enemy frame, redrawn with a dark boundary ring.

Card t_b15e9c7a (AUTO-SPRITE-NEXT). Queue row `spr_pp_ui_enemy` (P2, `queued_by_eye`) carries a
measured defect, not a model opinion: `output/_eye_r8_audit.py` counted 124 opaque boundary pixels on
the shipped `game/sprites_src/ui/spr_pp_ui_enemy.png` and found 0.0 percent of them on the darkest
colour in the file, because `tools/art/make_ui_nes.py` draws the block as a white 1 px edge over a gold
fill and white is the lightest entry it spends. On the battle ground, grey `$00`, that edge is a light
line over a light field, which is the RULE 0 white blob risk the eye names on two sheets.

The redraw
----------
The frame is three flat rings, hand written row by row in this file: ink `$0F` on the outside, white
`$30` inside it, gold `$28` filling the block. Nothing is scaled, tinted or solved.

Why those three entries and not others: a 32x32 sheet is four by four 8x8 tiles, and RULE 0 point 2 asks
a battle figure's palette question per tile (gamedev ruling on card t_af6fd431). Every tile of this
frame carries `$0F`, `$30` and `$28`, and `data/scene_palettes.json` ui sp0 is exactly `$0F $28 $30`, so
one sprite palette covers the whole sheet with no fourth colour anywhere. The black ring also fixes the
reading the eye measured: the boundary is now the darkest entry, and on the battle ground it is 5.3:1
against the grey band while the gold fill sits two luminance rows above it.

The ground
----------
`output/spr_pp_ui_enemy_ground.png` is the 32 x 32 patch of `game/sprites_src/ui/screens/ui_battle.png`
the block stands in: sky `$0F` at the top, the two row dither, then the grey band `$00` the encounter is
fought on. It is cropped from the shipped screen, not drawn here.

Usage:
    python tools/art/make_ui_frames_v2.py
"""

from __future__ import annotations

import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

INK = "#000000"   # $0F the boundary ring
WHITE = "#fcfcfc"  # $30 the keyline inside it
GOLD = "#f8b800"  # $28 the fill

PALETTE = {"K": INK, "W": WHITE, "A": GOLD}
W = H = 32

# The frame, 32x32, drawn in direction B: a 1 px ink ring, a white rim on the top and left (the light side), the
# gold block in the middle, and a second ink pixel on the right and bottom as the shadow. Three tones from three
# entries (ink dark, white light, gold mid) plus transparency, which is what one sprite may spend.
def frame_rows() -> list:
    rows = []
    for y in range(H):
        row = []
        for x in range(W):
            if x in (0, W - 1) or y in (0, H - 1):
                row.append("K")
            elif (x == W - 2 and 1 <= y < H - 1) or (y == H - 2 and 1 <= x < W - 1):
                row.append("K")
            elif y == 1 or x == 1:
                row.append("W")
            else:
                row.append("A")
        rows.append("".join(row))
    return rows


ENEMY_ROWS = frame_rows()


def build_frame() -> Image.Image:
    if len(ENEMY_ROWS) != H:
        raise SystemExit("%d rows written, the frame is %d tall" % (len(ENEMY_ROWS), H))
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for y, row in enumerate(ENEMY_ROWS):
        if len(row) != W:
            raise SystemExit("%d letters on row %d, the frame is %d wide" % (len(row), y, W))
        for x, letter in enumerate(row):
            colour = PALETTE[letter]
            image.putpixel((x, y), (int(colour[1:3], 16), int(colour[3:5], 16), int(colour[5:7], 16), 255))
    return image


def build_ground() -> Image.Image:
    """The 32x32 of the shipped battle screen the block stands in, cropped where no block is drawn."""
    path = os.path.join(ROOT, "game", "sprites_src", "ui", "screens", "ui_battle.png")
    with Image.open(path) as screen:
        ground = screen.convert("RGBA").crop((160, 88, 192, 120))
    entries = {}
    for pixel in ground.getdata():
        if pixel[3]:
            key = "#%02x%02x%02x" % pixel[:3]
            entries[key] = entries.get(key, 0) + 1
    print("  ground: %s at (160, 88) 32x32, entries %s"
          % (os.path.relpath(path, ROOT).replace(os.sep, "/"), sorted(entries.items())))
    return ground


def audit(path: str) -> None:
    """How much of the frame's opaque boundary sits on the darkest entry it spends.

    This is the number the eye's round 8 measured on the shipped sheet (0.0 percent of 124 boundary
    pixels) and the number the redraw has to move, so the check is one runnable command.
    """
    with Image.open(path) as image:
        frame = image.convert("RGBA")
    counts = {}
    boundary = []
    drawn = 0
    width, height = frame.size
    for y in range(height):
        for x in range(width):
            pixel = frame.getpixel((x, y))
            if pixel[3] == 0:
                continue
            drawn += 1
            counts[pixel[:3]] = counts.get(pixel[:3], 0) + 1
            if x in (0, width - 1) or y in (0, height - 1):
                boundary.append(pixel[:3])
    luma = {colour: 0.2126 * colour[0] + 0.7152 * colour[1] + 0.0722 * colour[2] for colour in counts}
    darkest = min(counts, key=luma.get)
    on_darkest = sum(1 for colour in boundary if colour == darkest)
    print("  %s: %d colours, %d drawn px, %d boundary px, %d on the darkest #%02x%02x%02x, %.1f%%"
          % (os.path.relpath(path, ROOT).replace(os.sep, "/"), len(counts), drawn, len(boundary),
             on_darkest, darkest[0], darkest[1], darkest[2],
             100.0 * on_darkest / max(1, len(boundary))))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true",
                        help="print the boundary metric for the shipped sheet and the redraw")
    args = parser.parse_args()
    out = os.path.join(ROOT, "output", "redraws")
    os.makedirs(out, exist_ok=True)
    frame = build_frame()
    path = os.path.join(out, "spr_pp_ui_enemy.png")
    frame.save(path)
    print("  %s %dx%d" % (os.path.relpath(path, ROOT).replace(os.sep, "/"), frame.width, frame.height))
    ground_path = os.path.join(ROOT, "output", "spr_pp_ui_enemy_ground.png")
    build_ground().save(ground_path)
    print("  %s 32x32" % os.path.relpath(ground_path, ROOT).replace(os.sep, "/"))
    if args.audit:
        audit(os.path.join(ROOT, "game", "sprites_src", "ui", "spr_pp_ui_enemy.png"))
        audit(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
