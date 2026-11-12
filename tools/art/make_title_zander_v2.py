#!/usr/bin/env python3
"""make_title_zander_v2.py: Zander's title bust, hand authored in title sp1's three entries.

Card t_8cc3afaa (ZANDER-BUST), from gamedev card t_8df7aab4 and the ruling in
`knowledge/PALETTE-RULINGS-2026-11-12.md` section 2.5.

Why the shipped sheet had to be redrawn
---------------------------------------
`game/sprites_src/title/spr_title_zander.png` is 128x16 with five entries (`$0F $00 $02 $10 $28`).
A 16x16 frame is read WHOLE by palette_synergy R6 (RULE 0, amendment on card t_af6fd431), so the whole
frame has to live in one sprite palette of three, and no title sprite row carries five entries. Measured
on the masked rear window pane it was 16 failing pairs: 8 `sprite_tile` and 8 `palette_count`, one per
frame. That is a redraw, and the redraw needed a row and a named body, which section 2.5 of the ruling
supplies.

The row, the body, and what is NOT spent
----------------------------------------
Title sp1 is `$09 $00 $20` and it is the only row that carries the road sign's 144 tiles, so it is the
row this bust takes and the sign is not touched:

  `$09` #007800  dark green  the 1 px outline, the eyes, the mouth, the jaw and the jacket's hard edges
  `$00` #7c7c7c  grey        the mid: hair shade, the fringe, the neck shadow, the jacket placket
  `$20` #f8f8f8  white       the body: skin, hair, the bomber. It is the frame's largest fill.

The body is `$20` because of the glass, measured in section 2.5: on `$0C` the candidates read `$20`
10.55:1, `$10` 5.90:1, `$00` 2.68:1, `$09` 1.97:1, `$28` 6.32:1, `$0C` 1.00:1, `$0B` 1.28:1, and of
sp1's three only `$20` clears 3:1 and sits two luminance rows away. `$00` as the body fails at 2.68:1
with no row gap.

He is NOT in his reserved hero triple, and that is the ruling, not a compromise of this drawing.
`hero_palettes.zander` is `$0F $21 $31` and no title sprite row carries it; re-solving sp1 to it
uncovers all 144 tiles of `spr_title_sign.png`, which nothing else carries. So the title bust is grey
and white with a dark green outline, and the light blue bomber waits for a card that repaints the sign.
`$36` skin and `$02` are spent nowhere: neither is in any title sprite row. `$21` and `$31` are not
spent either, for the reason above.

Geometry and craft
------------------
- 16x16 frame, 12x12 art at frame (2, 4): the placement `make_title_car.FRAMES` gave the bust, so the
  face still lands in the window band rows 8 to 15 and nothing moves on screen.
- SP-021: one pixel of `$09` around the whole silhouette, because the bust is drawn behind the car's
  glass, and the outline is a different hue family from the teal glass.
- SP-012: the eyes are 2 px each, with a 2 px white bridge between them.
- SP-010: a face in 6 rows, with the jaw read off the grey neck shadow under the chin.
- SP-042 to SP-044 (ordinary modern clothes, Mother style): the bomber is the largest single shape and
  is drawn in the row's body entry, its shading and its placket in the mid, its seams and the hem in the
  outline. The costume is CHARACTER-BIBLE 3: Zander, 19, messy blond, earbuds, an oversized bomber.
  SP-042's own "light tone under 30 percent" is an inference written for a four-tone cell and cannot
  hold here: RULE 0 point 2 leaves this frame exactly one body entry and it has to be the largest fill,
  so the drawing puts the light on the clothes and the mid on the shade, which is the opposite split of
  the same rule and is the only one the three entries allow.
- Frames 1 and 3 are the idle bob (the same drawing one pixel down). Frames 4 to 7 are the turn to
  speak: the head slides one pixel towards the driver on his right and the mouth opens a pixel at a
  time, so the "..." bubble lands on a mouth that is already open.

The ground
----------
`build_ground()` writes output/spr_title_zander_ground.png, the pane the bust would be drawn over. The
car body is not ground (`knowledge/PALETTE-RULINGS-2026-11-12.md` D1, card t_8df7aab4): the car is drawn
OVER the bust, so the pillars, the roof edge and the moonlight glint are covered, not stood on, and the
crop masks every non-glass pixel to transparent. The crop arithmetic is `make_title_bust_v2.build_ground`,
reused rather than copied: Zander is the passenger and sits in the REAR window, x 11 to 25, rows 8 to 15,
which is the pane that function measures, and this file asserts the pane it read is that one.

Usage:
    python tools/art/make_title_zander_v2.py          # write the sheet and its ground
    python tools/art/make_title_zander_v2.py --dump   # print the frames as text as well
"""

from __future__ import annotations

import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

ROOT = os.path.dirname(os.path.dirname(HERE))
CLEAR = (0, 0, 0, 0)

# Title sp1, data/palettes/scene_title.json. The index is the truth: $09, $00, $20.
OUTLINE = "#007800"  # $09 dark green, the 1 px ring, the eyes, the mouth, the jacket seams
MID = "#7c7c7c"      # $00 grey, the hair shade, the fringe, the neck shadow, the placket
BODY = "#f8f8f8"     # $20 white, the body: skin, hair and the bomber

PALETTE = {"K": OUTLINE, "G": MID, "W": BODY, ".": CLEAR, " ": CLEAR}

FRAME_W, FRAME_H = 16, 16
ART_W, ART_H = 12, 12
ART_X, ART_Y = 2, 4

# Zander Skye, 19. The head is 10 px wide in rows 0 to 8 and the bomber is 12 wide in rows 9 to 11, so
# the shoulders taper out past the head and the bust reads as a person and not as a rounded block. The
# face is 8 px wide (art columns 2 to 9) with a white margin either side of the eyes, because an eye
# that runs straight into the outline reads as a notch and not as an eye.
#
# Twelve characters per row or the build stops: a face row that is trimmed silently loses an eye.
ZANDER_ROWS = [
    "   KKKKKK   ",   # 0 the crown, outline over the black glass
    "  KWWGGWWK  ",   # 1 the hair poking up, one grey streak in the tufts
    " KWWWWGWWWK ",   # 2 the hair over the crown
    " KGWGGWWGGK ",   # 3 the hair past the ear, and the earbud in the middle entry at the temple
    " KWGGGGGGWK ",   # 4 the fringe, the mid entry in shadow across the brow
    " KWWWWWWWWK ",   # 5 the forehead
    " KWKKWWKKWK ",   # 6 two 2 px eyes, each with a white pixel before the outline
    " KWWWKKWWWK ",   # 7 the 2 px mouth, centred under the nose
    " KGWWWWWWGK ",   # 8 the chin, with the jaw shadow in the mid entry
    " KGGWWWWGGK ",   # 9 the bomber's collar, open at the neck
    "KWWWGGGWWWWK",  # 10 the bomber, the zip placket in the mid entry
    "KKKKKKKKKKKK",   # 11 the hem, and the outline along the bottom
]


def build_frame(index: int) -> Image.Image:
    """One 16x16 frame of the bust, drawn from the 12x12 grid above."""
    rows = [list(row) for row in ZANDER_ROWS]
    if len(rows) != ART_H:
        raise SystemExit("%d bust rows, the art is %d tall" % (len(rows), ART_H))
    if index >= 4:
        # The head comes round towards the driver, who is on his right: rows 0 to 8 slide one column,
        # so the face turns and the bomber does not. The mouth opens a pixel at a time under the nose,
        # in the outline entry, so the "..." bubble lands on a mouth that is already open.
        for line in range(0, 9):
            rows[line] = ["."] + rows[line][:-1]
        turn = index - 4
        mouth = {0: (6, 7), 1: (5, 7), 2: (5, 8), 3: (5, 9)}[turn]
        for column in range(mouth[0], mouth[1] + 1):
            rows[7][column] = "K"

    image = Image.new("RGBA", (FRAME_W, FRAME_H), CLEAR)
    for dy, row in enumerate(rows):
        if len(row) != ART_W:
            raise SystemExit("%d characters on bust row %d, the art is %d wide: %r"
                             % (len(row), dy, ART_W, "".join(row)))
        for dx, letter in enumerate(row):
            if letter not in PALETTE:
                raise SystemExit("unknown letter %r on bust row %d" % (letter, dy))
            colour = PALETTE[letter]
            if colour is CLEAR:
                continue
            image.putpixel((ART_X + dx, ART_Y + dy),
                           (int(colour[1:3], 16), int(colour[3:5], 16), int(colour[5:7], 16), 255))
    if index in (1, 3):
        # The idle bob: the same drawing one pixel down. The hem is stamped back onto the bottom row
        # afterwards, because a shifted drawing loses its last row off the frame and SP-021 wants the
        # outline all the way round the silhouette in every frame, not only in the ones that fit.
        lowered = Image.new("RGBA", (FRAME_W, FRAME_H), CLEAR)
        lowered.alpha_composite(image, (0, 1))
        red, green, blue, alpha = (int(OUTLINE[1:3], 16), int(OUTLINE[3:5], 16),
                                   int(OUTLINE[5:7], 16), 255)
        for column in range(ART_X, ART_X + ART_W):
            lowered.putpixel((column, ART_Y + ART_H - 1), (red, green, blue, alpha))
        return lowered
    return image


def build_frames() -> list[Image.Image]:
    """The eight frames at their shipping size and position, which is what make_title_car.py lands."""
    return [build_frame(index) for index in range(8)]


def build_sheet() -> Image.Image:
    """The eight frames as one 128x16 strip, the sheet layout the queue row names."""
    frames = build_frames()
    sheet = Image.new("RGBA", (FRAME_W * len(frames), FRAME_H), CLEAR)
    for index, frame in enumerate(frames):
        sheet.alpha_composite(frame, (index * FRAME_W, 0))
    return sheet


def build_ground() -> Image.Image:
    """The 16x16 of composed title the bust would be drawn over: the car's rear window pane.

    The crop and the mask are `make_title_bust_v2.build_ground`, which is the function card t_8df7aab4
    ruled D1 on: the car body is drawn over the bust, so it is masked out and the ground is the glass
    alone. Zander is the passenger, at the car placement `spr_title_zander (14, 4)` that
    `tools/art/make_title_car.py` publishes, which is the REAR window, x 11 to 25, rows 8 to 15; the
    assertion below is what makes this file's claim about which window it read checkable.
    """
    import make_title_bust_v2 as bust

    ground = bust.build_ground()
    entries = sorted({"#%02x%02x%02x" % pixel[:3] for pixel in ground.getdata() if pixel[3]})
    glass = ["#004058"]
    if entries != glass:
        raise SystemExit("the pane carries %s, not the glass alone %s: the mask did not run" % (entries, glass))
    if ground.width != 15 or ground.height != 8:
        raise SystemExit("the pane measured %dx%d, the rear window is 15x8 (x 11 to 25, rows 8 to 15)"
                         % (ground.width, ground.height))
    return ground


def audit(frames: list[Image.Image]) -> list[dict]:
    """Per frame: drawn pixels, the entries, and the largest fill. This is what the queue row records."""
    records = []
    for index, frame in enumerate(frames):
        counts: dict[str, int] = {}
        for pixel in frame.getdata():
            if pixel[3] == 0:
                continue
            key = "#%02x%02x%02x" % pixel[:3]
            counts[key] = counts.get(key, 0) + 1
        drawn = sum(counts.values())
        largest = max(counts, key=counts.get)
        worst = 0
        for ty in range(0, FRAME_H, 8):
            for tx in range(0, FRAME_W, 8):
                tile = set()
                for y in range(ty, ty + 8):
                    for x in range(tx, tx + 8):
                        pixel = frame.getpixel((x, y))
                        if pixel[3]:
                            tile.add(pixel[:3])
                worst = max(worst, len(tile))
        records.append({"frame": index, "drawn": drawn, "entries": counts, "largest": largest,
                        "largest_px": counts[largest],
                        "largest_pct": 100.0 * counts[largest] / drawn if drawn else 0.0,
                        "worst_tile": worst})
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", action="store_true", help="print every frame as text")
    args = parser.parse_args()

    out = os.path.join(ROOT, "output", "redraws")
    os.makedirs(out, exist_ok=True)
    sheet = build_sheet()
    path = os.path.join(out, "spr_title_zander.png")
    sheet.save(path, "PNG")
    print("  output/redraws/spr_title_zander.png %dx%d, 8 frames of 16x16" % (sheet.width, sheet.height))

    for record in audit(build_frames()):
        print("  frame %d: %d drawn px, entries %s, largest %s %d px (%.1f%%), worst 8x8 tile %d colour(s)"
              % (record["frame"], record["drawn"],
                 " ".join("%s %d" % (key, value) for key, value in sorted(record["entries"].items())),
                 record["largest"], record["largest_px"], record["largest_pct"], record["worst_tile"]))
        if record["largest"] != BODY:
            raise SystemExit("frame %d: the largest fill is %s, RULE 0 point 2 needs the body %s"
                             % (record["frame"], record["largest"], BODY))

    ground = build_ground()
    ground_path = os.path.join(ROOT, "output", "spr_title_zander_ground.png")
    ground.save(ground_path, "PNG")
    print("  output/spr_title_zander_ground.png %dx%d (the rear window, x 11 to 25, rows 8 to 15)"
          % (ground.width, ground.height))

    if args.dump:
        for index in range(8):
            print("frame %d" % index)
            frame = sheet.crop((index * FRAME_W, 0, (index + 1) * FRAME_W, FRAME_H))
            for y in range(FRAME_H):
                line = ""
                for x in range(FRAME_W):
                    pixel = frame.getpixel((x, y))
                    line += "." if pixel[3] == 0 else {OUTLINE: "K", MID: "G", BODY: "W"}[
                        "#%02x%02x%02x" % pixel[:3]]
                print("    " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
