#!/usr/bin/env python3
"""make_title_bust_v2.py: Konrad's title bust, hand authored in the three entries the scene carries.

Card t_b15e9c7a (AUTO-SPRITE-NEXT). The queue row `spr_title_konrad` (P1, the driver bust) is the
highest priority row that is not done. Its `palette_roles` block lists five entries, `$0F` ink,
`$28` gold, `$36` skin, `$10` tweed light and `$07` tweed dark, and no title sprite palette carries
`$36` or `$07`: `data/scene_palettes.json` gives the title sp0 `$0F $00 $28`, sp1 `$09 $00 $20`,
sp2 `$0C $10 $20`, sp3 `$0C $0B $20`. ART-BIBLE RULE 0 point 3 settles it anyway: "the hero palettes
are reserved and reused (Konrad grey and amber)", and `data/scene_palettes.json` hero_palettes.konrad
is `$0F $00 $28` exactly. So Konrad's bust is drawn in grey and amber, not in skin, and the `$36`
line stays a question for gamedev rather than something a redraw can spend.

Why the shipped sheet needs the redraw
--------------------------------------
`tools/art/make_title_car.py` draws the bust with legend letters that name ten different 2C02 entries
(skin `$11`, skin shade `$10`, tweed `$1F`, `$20`, blond `$28`, `$2A`), and `tools/art/title_bands.py`
then maps every pixel into the band palette, which can only hold three. Measured on the shipped
`game/sprites_src/title/spr_title_konrad.png`: 828 drawn pixels in three entries, `$28` 391 px (47.2
percent), `$00` and `$0F` the rest. Every skin tone, every tweed tone and the blazer collapse into the
same three, which is why the face reads as a gold head. A 16x16 frame is read whole by palette_synergy
R6 (RULE 0, amendment on card t_af6fd431), so the frame can only ever live in ONE sprite palette, and
the answer is to draw legal in the first place instead of letting a pass flatten the drawing.

Geometry, from knowledge/ART-BIBLE.md and the craft rules on the row
--------------------------------------------------------------------
- 16x16 frame, 12x12 art at frame (2, 4), the placement make_title_car.py FRAMES gives the bust, so the
  face still lands in the window band rows 8 to 15 and nothing moves on screen.
- SP-010: a face needs skin, an eye and a jaw line in 6 rows. Here the face is rows 4 to 7 (grey `$00`),
  the eyes are 2 px each (SP-012) with a grey bridge, the mouth is 2 px of ink under a grey chin, and
  the jaw is the ink line at row 7.
- SP-021: one pixel of ink `$0F` around the whole silhouette, so the head separates from the black glass
  it is drawn behind.
- Konrad's tell (CHARACTER-BIBLE) is the wristwatch, so frames 5 to 7 bring the forearm up one row a
  frame with the watch face in amber `$28` on the wrist; frames 1 and 3 are the idle bob.

The ground
----------
The bust is no longer drawn by the title (`game/scripts/pp_title/pp_title.gml` line 601: the exterior
only, no faces), so its ground is the window it would sit in: the car's own glass opening at the car's
placement, cropped from a composed title frame. build_ground() writes that 16 x 16 crop to
output/spr_title_konrad_ground.png so palette_synergy is asked the real question.

Usage:
    python tools/art/make_title_bust_v2.py            # write the sheet and its ground
    python tools/art/make_title_bust_v2.py --dump     # print the frames as text as well
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

# The three entries of title sp0, which are also hero_palettes.konrad in data/scene_palettes.json.
INK = "#000000"   # $0F outline, eyes, mouth, blazer, jaw line
GREY = "#7c7c7c"  # $00 face, beard, shirt, hair streaks
GOLD = "#f8b800"  # $28 hair, watch face

PALETTE = {"K": INK, "G": GREY, "A": GOLD, ".": CLEAR, " ": CLEAR}

FRAME_W, FRAME_H = 16, 16
ART_W, ART_H = 12, 12
ART_X, ART_Y = 2, 4

# Konrad Skye, 47. Rows 0 to 7 are the head, rows 8 to 11 the shoulders inside the window. Twelve
# characters per row or the build stops: a face row that is trimmed silently loses an eye.
KONRAD_ROWS = [
    "   KKKKKK   ",   # 0 the crown, ink over the black glass
    "  KAAAAAAK  ",   # 1 the blond hair
    " KAAGAAAGAK ",   # 2 the hair with its grey streaks
    " KKAAAAAAKK ",   # 3 the hair falling past the temples
    " KGKKKKKKGK ",   # 4 the hairline, ink across the forehead
    "  KAAAAAAK  ",   # 5 the forehead and the face, lit amber by the headlight
    "  KKKGKKGK  ",   # 6 two 2 px ink eyes with a grey bridge between them
    "  KGGKKGGK  ",   # 7 the nose, the mouth and the ink jaw line
    " KKKKGGKKKK ",   # 8 the collar, the grey of the open shirt
    " KKKGGGGKKK ",   # 9 the shirt and the ink of the blazer
    " KKKGKKGKKK ",   # 10 the lanyard, two ink strands
    " KKKGGGGKKK ",   # 11 the hem of the blazer
]


def build_frame(index: int) -> Image.Image:
    """One 16x16 frame of the bust, drawn from the 12x12 grid above."""
    rows = [list(row) for row in KONRAD_ROWS]
    if index >= 4:
        # The eyes come round to the road: 3,4 and 6,7 become 4,5 and 7,8.
        rows[6] = list("  KGKKGKKK  ")
    if index >= 5:
        # The forearm comes up the right edge, one row a frame, the amber watch on the wrist.
        hand = {5: 10, 6: 9, 7: 8}[index]
        rows[hand][8] = "G"
        rows[hand][9] = "A"
        for below in range(hand + 1, 12):
            rows[below][9] = "K"
            if below != hand + 1:
                rows[below][8] = "K"

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
    shifted = index in (1, 3)
    if shifted:
        # The idle bob: the same drawing one pixel down, never a second drawing.
        lifted = Image.new("RGBA", (FRAME_W, FRAME_H), CLEAR)
        lifted.alpha_composite(image, (0, 1))
        return lifted
    return image


def build_sheet() -> Image.Image:
    """The eight frames as one 128x16 strip, the sheet layout the queue row names."""
    frames = [build_frame(index) for index in range(8)]
    sheet = Image.new("RGBA", (FRAME_W * 8, FRAME_H), CLEAR)
    for index, frame in enumerate(frames):
        sheet.alpha_composite(frame, (index * FRAME_W, 0))
    return sheet


def build_ground() -> Image.Image:
    """The 16x16 of composed title the bust would be drawn over: the car's glass opening.

    The car sheet draws its glass in ink, and compose_title_preview.window_openings() reads those
    columns, so the crop is the opening the bust fills at the car's own placement from the game's
    PP_TITLE macros. Nothing is invented: the pixels come from the composer's frame.
    """
    import compose_title_preview as composer

    palette = composer.load_palette(ROOT)
    colours = {"ink": palette[0], "paper": palette[5], "gold": palette[41], "stone": palette[35]}
    sprite_dir = os.path.join(ROOT, "game", "sprites_src", "title")
    art = composer.TitleArt(sprite_dir)
    art.need("title_L1_sky", "title_L2_clouds", "title_L3_downs", "title_L4_fields", "title_L5_verge",
             "title_L6_road", "title_L7_fg", "spr_title_car", "spr_pp_title_logo", "spr_pp_font8",
             "spr_pp_menu_cursor")
    scene = composer.Scene(art, ROOT)
    frame = composer.compose_frame(scene, 0.0, 0.0, colours)

    car = art.frame("spr_title_car", 0)
    macros = composer.read_game_macros(ROOT)
    car_x = int(macros.get("PP_TITLE_CAR_X", 0))
    car_y = int(macros.get("PP_TITLE_CAR_Y", 0))
    # The v2 car draws its glass in its own dark teal, not in ink, so the composer's ink based window
    # reader finds nothing: the glass colour is measured off the car sheet first (the most common entry
    # in the middle rows), then the same reader is asked for the pane in that colour.
    counts = {}
    for y in range(car.height // 4, car.height // 2):
        for x in range(car.width):
            pixel = car.getpixel((x, y))
            if pixel[3]:
                counts[pixel[:3]] = counts.get(pixel[:3], 0) + 1
    glass = max(counts, key=counts.get) + (255,)
    top, bottom = composer.window_band(car, glass)
    openings = composer.window_openings(car, glass)
    if not openings:
        raise SystemExit("no glass pane in the car sheet, the bust ground cannot be read")
    x0, x1 = openings[0]
    # The pane, not the whole 16x16 box: the head is 12 wide and 8 rows tall and the window is the
    # 11 x 8 it fills, while the pillars and the roof are the car body, which is drawn OVER the bust
    # and is therefore not ground. Measured, so the next reader can see the box that was read.
    ground = car.crop((x0, top, x1 + 1, bottom + 1)).convert("RGBA")
    # Card t_8df7aab4 (gamedev, 2026-11-12): the car body is NOT ground, and the mask below is what
    # makes that true in the file rather than in this docstring. `tools/art/title_car_v2.py` paints the
    # pillars, the roof edge and the one diagonal moonlight glint in BODY ($20), the car's largest fill,
    # and the car is drawn after the bust, so no bust pixel ever sits on a $20 pixel: those pixels are
    # covered, not stood on. The docstring above said as much; the crop did not, and the stale $20 made the
    # pane read as TWO grounds ($0C 103 px, $20 14 px in the rear window; $0C 132 px, $20 4 px in the
    # front one) where no entry of the title's four sprite rows clears 3:1 on both ends of the pair.
    # Masking every non-glass pixel is not a rule relaxation: `palette_synergy.ground_pixels()` skips
    # alpha 0 by design, so the ground set becomes the glass and the question becomes the real one.
    glass_rgb = (glass[0], glass[1], glass[2])
    pixels = ground.load()
    masked = 0
    for y in range(ground.height):
        for x in range(ground.width):
            r, g, b, a = pixels[x, y]
            if a and (r, g, b) != glass_rgb:
                pixels[x, y] = CLEAR
                masked += 1
    print("  ground: %d car-body pixel(s) masked to transparent, the glass is the ground" % masked)
    entries = sorted({"#%02x%02x%02x" % pixel[:3] for pixel in ground.getdata() if pixel[3]})
    print("  ground: car at (%d, %d), glass pane x %d..%d rows %d..%d, %dx%d, entries %s"
          % (car_x, car_y, x0, x1, top, bottom, ground.width, ground.height, entries))
    return ground


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", action="store_true", help="print every frame as text")
    args = parser.parse_args()

    out = os.path.join(ROOT, "output", "redraws")
    os.makedirs(out, exist_ok=True)
    sheet = build_sheet()
    path = os.path.join(out, "spr_title_konrad.png")
    sheet.save(path)
    print("  %s %dx%d" % (os.path.relpath(path, ROOT).replace(os.sep, "/"), sheet.width, sheet.height))

    ground = build_ground()
    ground_path = os.path.join(ROOT, "output", "spr_title_konrad_ground.png")
    ground.save(ground_path)
    print("  %s %dx%d" % (os.path.relpath(ground_path, ROOT).replace(os.sep, "/"),
                          ground.width, ground.height))

    if args.dump:
        for index in range(8):
            print("frame %d" % index)
            frame = sheet.crop((index * FRAME_W, 0, (index + 1) * FRAME_W, FRAME_H))
            for y in range(FRAME_H):
                line = ""
                for x in range(FRAME_W):
                    pixel = frame.getpixel((x, y))
                    line += "." if pixel[3] == 0 else {INK: "K", GREY: "G", GOLD: "A"}[
                        "#%02x%02x%02x" % pixel[:3]]
                print("    " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
