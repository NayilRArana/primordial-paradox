#!/usr/bin/env python3
"""make_ui_party_v2.py: the 24x32 party member frame, redrawn so its outer ring is the dark entry.

Card t_09e10c47 (AUTO-SPRITE-NEXT). Queue row `spr_pp_ui_party` (P2, `queued_by_eye`) carries a
measured defect, not a model opinion: `output/_eye_r8_audit.py` counted 108 opaque boundary pixels
on the shipped `game/sprites_src/ui/spr_pp_ui_party.png` and found 0.0 percent of them on the
darkest colour in the file, because `tools/art/make_ui_nes.py` draws the block as a white 1 px edge
over a grey body and white is the lightest entry it spends. A block whose only edge is the lightest
entry it owns has no edge at all on a light field, which is the RULE 0 white blob risk.

The redraw
----------
The card is four flat rings, hand written row by row in this file: grey `$00` on the outside, white
`$30` inside it, grey `$00` for the body, and the member marker redrawn in gold `$28` as a small
shoulders-and-head silhouette instead of the blank 4x4 square the shipped sheet carries. Nothing is
scaled, tinted or solved, and no entry is added: the file still spends grey, white and gold.

Why those three entries and not others
--------------------------------------
`data/ui_layouts.json` check C15 fixes this block's palette as "party block palette (grey, white,
gold) differs from enemy (gold, white)", and `data/palettes/scene_ui.json` sp1 is exactly that
triple: `$00 $30 $28`. So the ring is drawn in the darkest of the three the spec allows rather than
in a fourth, and every 8x8 tile of the sheet stays inside sp1 with no palette move anywhere.

The ground
----------
`output/spr_pp_ui_party_ground.png` is the 24 x 32 patch of `game/sprites_src/ui/screens/ui_battle.png`
at the party column's own rows, taken from columns 200 to 223 where no block is drawn: the sky band,
one entry, `$0F` on all 768 pixels. The four party slots in `data/ui_layouts.json` sit at x 28 tiles,
y 4, 8, 12 and 16, and the screen bakes a placeholder block into each of them, so the patch is the
same band read just left of the column instead of under a baked block.

Usage:
    python tools/art/make_ui_party_v2.py            build the redraw and the ground, print the row
    python tools/art/make_ui_party_v2.py --audit    also print the boundary metric on both sheets
"""

from __future__ import annotations

import argparse
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

W, H = 24, 32

GREY = "#7c7c7c"    # $00 the outer ring and the body, the darkest entry the block may spend
WHITE = "#fcfcfc"   # $30 the keyline inside the ring
GOLD = "#f8b800"    # $28 the member marker

PALETTE = {". ": None, "g": GREY, "w": WHITE, "o": GOLD}

# The body band is 20 wide: cols 2 to 21. The marker is the gold silhouette a member stands in for,
# head 4 wide on rows 8 to 11, a 2 px neck on row 12, shoulders widening on rows 13 to 16.
PERSON = {
    8: (10, 13),
    9: (10, 13),
    10: (10, 13),
    11: (10, 13),
    12: (11, 12),
    13: (9, 14),
    14: (9, 14),
    15: (8, 15),
    16: (8, 15),
}

PARTY_ROWS = []
for y in range(H):
    if y == 0 or y == H - 1:
        PARTY_ROWS.append("g" * W)
    elif y == 1 or y == H - 2:
        PARTY_ROWS.append("g" + "w" * (W - 2) + "g")
    else:
        row = ["g", "w"] + ["g"] * (W - 4) + ["w", "g"]
        if y in PERSON:
            start, end = PERSON[y]
            for x in range(start, end + 1):
                row[x] = "o"
        PARTY_ROWS.append("".join(row))


def build_frame() -> Image.Image:
    if len(PARTY_ROWS) != H:
        raise SystemExit("%d rows written, the frame is %d tall" % (len(PARTY_ROWS), H))
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for y, row in enumerate(PARTY_ROWS):
        if len(row) != W:
            raise SystemExit("%d letters on row %d, the frame is %d wide" % (len(row), y, W))
        for x, letter in enumerate(row):
            colour = PALETTE[letter]
            if colour is None:
                continue
            image.putpixel((x, y), (int(colour[1:3], 16), int(colour[3:5], 16), int(colour[5:7], 16), 255))
    return image


def build_ground() -> Image.Image:
    """The 24x32 of the shipped battle screen at the party slot's rows, where no block is drawn."""
    path = os.path.join(ROOT, "game", "sprites_src", "ui", "screens", "ui_battle.png")
    with Image.open(path) as screen:
        ground = screen.convert("RGBA").crop((200, 32, 224, 64))
    entries = {}
    for pixel in ground.getdata():
        if pixel[3]:
            key = "#%02x%02x%02x" % pixel[:3]
            entries[key] = entries.get(key, 0) + 1
    print("  ground: %s at 200,32 24x32, entries %s"
          % (os.path.relpath(path, ROOT).replace(os.sep, "/"), sorted(entries.items())))
    return ground


def audit(path: str) -> None:
    """How much of the frame's opaque boundary sits on the darkest entry it spends."""
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
    print("  %s: %dx%d, %d colours, %d drawn px, %d boundary px, %d on the darkest #%02x%02x%02x, %.1f%%"
          % (os.path.relpath(path, ROOT).replace(os.sep, "/"), width, height, len(counts), drawn,
             len(boundary), on_darkest, darkest[0], darkest[1], darkest[2],
             100.0 * on_darkest / max(1, len(boundary))))
    for colour, count in sorted(counts.items(), key=lambda item: -item[1]):
        print("    #%02x%02x%02x %4d px" % (colour[0], colour[1], colour[2], count))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true",
                        help="print the boundary metric for the shipped sheet and the redraw")
    args = parser.parse_args()
    out = os.path.join(ROOT, "output", "redraws")
    os.makedirs(out, exist_ok=True)
    frame = build_frame()
    path = os.path.join(out, "spr_pp_ui_party.png")
    frame.save(path)
    print("  %s %dx%d" % (os.path.relpath(path, ROOT).replace(os.sep, "/"), frame.width, frame.height))
    ground_path = os.path.join(ROOT, "output", "spr_pp_ui_party_ground.png")
    build_ground().save(ground_path)
    print("  %s %dx%d" % (os.path.relpath(ground_path, ROOT).replace(os.sep, "/"), W, H))
    if args.audit:
        audit(os.path.join(ROOT, "game", "sprites_src", "ui", "spr_pp_ui_party.png"))
        audit(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
