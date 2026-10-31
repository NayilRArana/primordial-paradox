#!/usr/bin/env python3
"""make_title_wheel_v2.py: the road wheel, four hand authored rotation frames in the two entries bg3 carries.

Card t_f9a18f00 (AUTO-SPRITE-NEXT). The queue row `spr_title_wheel` (P1, the road wheel, 4 frames) is the
highest priority row that is not done once the two P1 busts are set aside: `spr_title_konrad` and
`spr_title_zander` are both held open by the same Q for gamedev (knowledge/PALETTE-RULINGS-2026-10-25.md
section 2, the car's glass pane holds $0C on 103 px and $20 on 14 px, and no entry of any title sprite
palette separates from both), so no redraw of either can clear RULE 0 point 2 and the wheel is next.

What the shipped sheet gets wrong
---------------------------------
Measured on `game/sprites_src/title/spr_title_wheel.png` on 2026-10-26: 64x16, 4 frames of 16x16, three
entries `$0B` #005800 135 px (44.4 percent), `$0C` #004058 and `$20` #f8f8f8, 304 drawn pixels, 0 off
palette, nes_check PASS. The palette is legal and the drawing is not: the tyre is `$0B` DARK GREEN, so the
wheel is a green disc on grass-green paint, and the only thing that says "wheel" is a hub dot. The row's
own defect text says it: the retired 40x10 copy "had a rim the same colour as the tyre", and the shipped
copy inherits that fault in the two entries the band can carry.

The ground
----------
ART-BIBLE 1.4 with RULE 0 on this row: "the tyre is drawn on the road band". The wheel is a FIGURE
(knowledge/PALETTE-RULINGS-2026-10-25.md section 2: "one ground, the car's arch, one surface"), so RULE 0
point 2 is asked of it against the road it stands on. Measured from the shipped `title_L6_road.png` at the
wheel's own placement (the game's `PP_TITLE_CAR_X`/`PP_TITLE_CAR_Y` macros, the frame at car-local (6, 19)
so the 10x10 art keeps the (9, 22) the row's geometry names and its tyre bottoms out on row 31, and the
layer's own y from `data/title.json`): the 16x16 the frame covers is `$0F` 234 px (91.4 percent) and `$0C`
22 px (8.6 percent), the second being the strip's grain. One surface, two entries. build_ground() writes
that crop to `output/spr_title_wheel_ground.png` so the check is asked the real question.

Why these two entries and not the row's five
--------------------------------------------
`palette_roles` lists `$0F` tyre, `$10` rim and `$20` hub, and `data/palettes/scene_title.json` puts
`spr_title_wheel` in band `bg3`, which is `$0C $0B $20`: a sheet painted by `tools/art/title_bands.py` into
bg3 can only ship those three, which is exactly how the shipped sheet came to be `$0B`/`$0C`/`$20` after
`make_title_car.py` drew it in ten legend entries. That is the same arithmetic that took the exhaust puff's
`$10` body to `$20` (PALETTE-RULINGS-2026-10-25.md section 4), so this tool draws in the shipping pair from
the start and never asks a pass to recolour it:

  `$0C` #004058  the tyre and its outline, the darkest entry bg3 carries
  `$20` #f8f8f8  the rim, the spokes and the hub, which is what makes the rotation visible

`$0B` is deliberately unspent: it is a dark green, it is the fault this redraw removes, and R6 asks the
whole 16x16 frame to live in ONE sprite palette, which `$0C` and `$20` do in sp2 (`$0C $10 $20`) and sp3
(`$0C $0B $20`). RULE 0 point 3's accent line stays a palette_roles question for gamedev, recorded in the
queue row as a Q rather than spent here.

Contrast, measured after the fact by `tools/palette_synergy.py`
---------------------------------------------------------------
The frame's body is the most common entry that is not the darkest, which is `$20`, and it is asked against
both ground entries: `$20` on `$0F` is 2 luminance rows apart and on `$0C` 2 rows apart, so R1 clears on
the row instrument on both without needing the 3:1 one. The tyre `$0C` on the `$0F` tarmac is 1.91:1 and
would be refused as a body, which is why the drawing carries a 1 px `$20` rim inside the tyre: the wheel is
told from the road by its rim, never by its tyre.

Craft
-----
- SP-021: one pixel of `$0C` around the whole silhouette.
- SP-049: a wheel that does not rotate reads as a hole. The four frames are four different spoke
  drawings (+ , x, three spoke, + offset one row), not one drawing bobbed.
- 10x10 art in a 16x16 frame at (3, 3), the placement `make_title_car.FRAMES` gives the name, so the art
  sits exactly where the old drawing sat and nothing moves on screen.

Usage:
    python tools/art/make_title_wheel_v2.py          # write the sheet and its ground
    python tools/art/make_title_wheel_v2.py --dump   # print the four frames as text as well
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

ROOT = os.path.dirname(os.path.dirname(HERE))
CLEAR = (0, 0, 0, 0)

TEAL = "#004058"   # $0C dark teal, the tyre and the outline
WHITE = "#f8f8f8"  # $20 rim, spokes, hub

PALETTE = {"T": TEAL, "W": WHITE, ".": CLEAR, " ": CLEAR}

FRAME_W, FRAME_H = 16, 16
ART_W, ART_H = 10, 10
ART_X, ART_Y = 3, 3

# Four rotation frames, ten rows of ten. The tyre is one pixel of T, the rim one pixel of W inside it,
# and the white in the middle is the spokes; what changes from frame to frame is the spoke drawing,
# which is the only thing that can show a rotation at this size.
WHEEL_FRAMES = [
    [   # frame 0: the thick cross, spokes up, down, left and right
        "..TTTTTT..",
        ".TWWWWWWT.",
        "TWTTTTTTWT",
        "TWTWTTWTWT",
        "TWTWWWWTWT",
        "TWTWWWWTWT",
        "TWTWTTWTWT",
        "TWTTTTTTWT",
        ".TWWWWWWT.",
        "..TTTTTT..",
    ],
    [   # frame 1: the diagonals, the same rim, the spokes quarter turned
        "..TTTTTT..",
        ".TWWWWWWT.",
        "TWWTTTTWWT",
        "TWTWTTWTWT",
        "TWTTWWTTWT",
        "TWTTWWTTWT",
        "TWTWTTWTWT",
        "TWWTTTTWWT",
        ".TWWWWWWT.",
        "..TTTTTT..",
    ],
    [   # frame 2: three spokes, so the rim carries a readable gap that moves
        "..TTTTTT..",
        ".TWWWWWWT.",
        "TWTTWWTTWT",
        "TWTTWWTTWT",
        "TWWTTTTWWT",
        "TWWTTTTWWT",
        "TWTTTTTTWT",
        "TWTWTTWTWT",
        ".TWWWWWWT.",
        "..TTTTTT..",
    ],
    [   # frame 3: the cross again, one row up, which reads as the same spokes caught between
        "..TTTTTT..",
        ".TWWWWWWT.",
        "TWTTTTTTWT",
        "TWTWWWWTWT",
        "TWTWWWWTWT",
        "TWTWTTWTWT",
        "TWTWTTWTWT",
        "TWTTTTTTWT",
        ".TWWWWWWT.",
        "..TTTTTT..",
    ],
]


def build_frame(index: int) -> Image.Image:
    """One 16x16 frame, the 10x10 grid above pasted at the placement the row's geometry names."""
    rows = WHEEL_FRAMES[index]
    if len(rows) != ART_H:
        raise SystemExit("frame %d has %d rows, the art is %d tall" % (index, len(rows), ART_H))
    image = Image.new("RGBA", (FRAME_W, FRAME_H), CLEAR)
    for dy, row in enumerate(rows):
        if len(row) != ART_W:
            raise SystemExit("%d characters on frame %d row %d, the art is %d wide: %r"
                             % (len(row), index, dy, ART_W, row))
        for dx, letter in enumerate(row):
            if letter not in PALETTE:
                raise SystemExit("unknown letter %r on frame %d row %d" % (letter, index, dy))
            colour = PALETTE[letter]
            if colour is CLEAR:
                continue
            image.putpixel((ART_X + dx, ART_Y + dy),
                           (int(colour[1:3], 16), int(colour[3:5], 16), int(colour[5:7], 16), 255))
    return image


def build_sheet() -> Image.Image:
    """The four frames as one 64x16 strip, the sheet layout the queue row names."""
    sheet = Image.new("RGBA", (FRAME_W * len(WHEEL_FRAMES), FRAME_H), CLEAR)
    for index in range(len(WHEEL_FRAMES)):
        sheet.alpha_composite(build_frame(index), (index * FRAME_W, 0))
    return sheet


def build_ground() -> Image.Image:
    """The 16x16 of road the wheel is drawn over, at the wheel's own placement.

    Nothing is invented: the crop comes from the shipped title_L6_road.png at the x and y the game's own
    macros and data/title.json give, so the ground is the file the title draws, not a colour picked to
    pass the check.
    """
    with open(os.path.join(ROOT, "data", "title.json"), encoding="utf-8") as handle:
        title = json.load(handle)
    layers = title.get("layers") or title.get("title_layers") or []
    road = [layer for layer in layers if layer.get("name") == "title_L6_road"]
    if not road:
        raise SystemExit("data/title.json has no title_L6_road layer, the wheel's ground cannot be read")
    road_y = int(road[0]["y"])

    import compose_title_preview as composer
    macros = composer.read_game_macros(ROOT)
    car_x = int(macros.get("PP_TITLE_CAR_X", 0))
    car_y = int(macros.get("PP_TITLE_CAR_Y", 0))
    # make_title_car.WHEEL_PLACE puts the 10x10 art at car-local (9, 22); a 16x16 frame carrying the art
    # at (3, 3) therefore sits at car-local (6, 19), which keeps the tyre bottom on row 31.
    frame_x = car_x + 9 - ART_X
    frame_y = car_y + 22 - ART_Y
    road_path = os.path.join(ROOT, "game", "sprites_src", "title", "title_L6_road.png")
    with Image.open(road_path) as image:
        strip = image.convert("RGBA").copy()
    box = (frame_x, frame_y - road_y, frame_x + FRAME_W, frame_y - road_y + FRAME_H)
    ground = strip.crop(box)
    if ground.width != FRAME_W or ground.height != FRAME_H:
        raise SystemExit("the road crop is %dx%d, not the 16x16 frame" % (ground.width, ground.height))
    counts = {}
    for pixel in ground.convert("RGBA").getdata():
        if pixel[3]:
            counts[pixel[:3]] = counts.get(pixel[:3], 0) + 1
    total = sum(counts.values()) or 1
    print("  ground: %s at strip (%d, %d), car at (%d, %d), wheel frame at (%d, %d)"
          % (os.path.relpath(road_path, ROOT).replace(os.sep, "/"), box[0], box[1], car_x, car_y,
             frame_x, frame_y))
    print("  ground entries: " + ", ".join("#%02x%02x%02x %.1f%%" % (rgb[0], rgb[1], rgb[2], 100.0 * n / total)
                                           for rgb, n in sorted(counts.items(), key=lambda kv: -kv[1])))
    return ground


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", action="store_true", help="print the four frames as text")
    args = parser.parse_args()

    out = os.path.join(ROOT, "output", "redraws")
    os.makedirs(out, exist_ok=True)
    sheet = build_sheet()
    path = os.path.join(out, "spr_title_wheel.png")
    sheet.save(path)
    print("  %s %dx%d, %d frames of %dx%d"
          % (os.path.relpath(path, ROOT).replace(os.sep, "/"), sheet.width, sheet.height,
             len(WHEEL_FRAMES), FRAME_W, FRAME_H))
    counts = {}
    for pixel in sheet.getdata():
        if pixel[3]:
            counts[pixel[:3]] = counts.get(pixel[:3], 0) + 1
    print("  entries: " + ", ".join("#%02x%02x%02x %d px" % (rgb[0], rgb[1], rgb[2], n)
                                    for rgb, n in sorted(counts.items(), key=lambda kv: -kv[1])))

    ground = build_ground()
    ground_path = os.path.join(ROOT, "output", "spr_title_wheel_ground.png")
    ground.save(ground_path)
    print("  %s %dx%d" % (os.path.relpath(ground_path, ROOT).replace(os.sep, "/"),
                          ground.width, ground.height))

    if args.dump:
        for index in range(len(WHEEL_FRAMES)):
            print("frame %d" % index)
            frame = sheet.crop((index * FRAME_W, 0, (index + 1) * FRAME_W, FRAME_H))
            for y in range(FRAME_H):
                line = ""
                for x in range(FRAME_W):
                    pixel = frame.getpixel((x, y))
                    line += "." if pixel[3] == 0 else {TEAL: "T", WHITE: "W"}["#%02x%02x%02x" % pixel[:3]]
                print("    " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
