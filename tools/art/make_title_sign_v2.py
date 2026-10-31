#!/usr/bin/env python3
"""make_title_sign_v2.py: spr_title_sign, the distance road sign, redrawn with its ink edge.

Card t_d8fd83fd (AUTO-SPRITE-NEXT). The queue row `spr_title_sign` (P1) is the next row that is
neither done nor blocked by an open question. Two things on it are still open on the shipped sheet,
measured on game/sprites_src/title/spr_title_sign.png on 2026-10-25:

  1. the plate has no ink edge. Its outermost pixel row and column are the bright border $20, so the
     sign is a white ring laid straight onto the verge. The row's craft rule SP-025 asks for the
     outline on the side the ground is, and the frame's darkest entry covers 0 of its 384 edge pixels.
  2. the row's palette_roles name $0F ink, $30 white letters, $09 green border and $0B green shade,
     and the title scene carries none of them for this sheet: data/palettes/scene_title.json gives
     spr_title_sign sp1, which is [$09, $00, $20]. The shipped sheet spends $09 and $20 and the row's
     four entries are unreachable.

So the redraw is drawn inside sp1 and nowhere else: $00 grey is the ink edge, $20 white is the
keyline and the lettering, $09 green is the face and the field behind it. Nothing above three
entries in any 8 x 8 tile, outline on the outside, letters at 3x legible, and the plate reads against
the verge it stands in because its body ($20) clears the verge's three colours by contrast
(R1b overlay_contrast).

HOW THE PLATE IS AUTHORED

The 96 x 24 frame is twelve 8 x 8 tiles across and three down, and the plate is a nine slice, the way
tools/art/make_title_rows_v2.py authors the dialogue window: nine hand written 8 x 8 character
grids (corner, edge, fill) stamped into the frame. One character per pixel, "." transparent, the
letters looked up in a table of data/nes_palette.json entries only. Nothing is scaled, recoloured,
copied or traced.

The lettering is NOT hand drawn: the two lines of every frame are the project's own 5 x 7 glyph table
(the one tools/art/make_title_world.py loads and the shipped sign already draws with), stamped in
$20. Hand drawing eleven letterforms per line would be a second font against the font contract, the
same reason tools/art/make_font_row_v2.py draws its row from the licensed rasteriser.

What this writes (deterministic: no clock, no randomness, no window, no network):

  output/redraws/spr_title_sign.png   384 x 24, 4 frames, entries $00 / $09 / $20
  output/spr_title_sign_ground.png     96 x 24, the verge the sign is drawn over

Nothing here writes the shipped tree. game/sprites_src/title/spr_title_sign.png belongs to
tools/art/make_title_world.py sign_plate(), and whether the shipped sheet moves to this plate is a
gamedev call, posted as Q: on the queue row.

Usage:
    python tools/art/make_title_sign_v2.py
"""

from __future__ import annotations

import json
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools", "art"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import make_title_world as world  # noqa: E402  the project's own glyph table and sign texts

CLEAR = (0, 0, 0, 0)

# 2C02 entries, named once. This is title sp1 exactly: data/palettes/scene_title.json gives
# spr_title_sign sp1 [$09, $00, $20], so three is not a budget this drawing chose, it is the only set
# the scene carries for the name.
INK = "I"      # $00 #7c7c7c  the ink edge, the outline SP-025 asks for on the ground side
WHITE = "B"    # $20 #f8f8f8  the keyline just inside it, and the lettering
GREEN = "G"    # $09 #007800  the face, which is also the colour of the verge behind it
COLOURS = {INK: "#7c7c7c", WHITE: "#f8f8f8", GREEN: "#007800"}

SIGN_W = 96
SIGN_H = 24
TILE = 8
COLUMNS = SIGN_W // TILE   # 12
ROWS = SIGN_H // TILE      # 3
FRAMES = 4

# Hand written nine slice, 8 x 8 grids. Read them as a plate: one pixel of ink on the outside, one
# pixel of white keyline inside it, green face inside that. Corners carry both edges, edge tiles one,
# the fill tile none.
CORNER_TL = ["IIIIIIII",
             "IBBBBBBB",
             "IBGGGGGG",
             "IBGGGGGG",
             "IBGGGGGG",
             "IBGGGGGG",
             "IBGGGGGG",
             "IBGGGGGG"]
EDGE_TOP = ["IIIIIIII",
            "BBBBBBBB",
            "GGGGGGGG",
            "GGGGGGGG",
            "GGGGGGGG",
            "GGGGGGGG",
            "GGGGGGGG",
            "GGGGGGGG"]
EDGE_LEFT = ["IBGGGGGG",
             "IBGGGGGG",
             "IBGGGGGG",
             "IBGGGGGG",
             "IBGGGGGG",
             "IBGGGGGG",
             "IBGGGGGG",
             "IBGGGGGG"]
FILL = ["GGGGGGGG"] * 8

CORNER_TR = [row[::-1] for row in CORNER_TL]
EDGE_RIGHT = [row[::-1] for row in EDGE_LEFT]
CORNER_BL = CORNER_TL[::-1]
CORNER_BR = [row[::-1] for row in CORNER_BL]
EDGE_BOTTOM = EDGE_TOP[::-1]

# The tiles the frame is stamped from, row major, 12 across and 3 down. Hand written, one tile per
# entry, so the plate's shape is readable without decoding a loop.
PLATE = [
    [CORNER_TL] + [EDGE_TOP] * (COLUMNS - 2) + [CORNER_TR],
    [EDGE_LEFT] + [FILL] * (COLUMNS - 2) + [EDGE_RIGHT],
    [CORNER_BL] + [EDGE_BOTTOM] * (COLUMNS - 2) + [CORNER_BR],
]

# The two lines of the plate, from the tool that owns the name, so the count down the drive cannot
# drift from the game's own table: BASINGSTOKE 20 over SOUTHAMPTON 55, then 8 and 43, then
# WINCHESTER 12 over SOUTHAMPTON 30, then 2 and 20.
TEXTS = world.SIGN_TEXTS

# Where the lettering sits, by hand: two 7 px lines on a green face that runs from row 2 to row 21,
# so each line has 2 px of face above it and 2 px below the block of both.
LINE_Y = (4, 13)
TEXT_X = 5          # 5 px in from the frame's left edge: 2 px of face, the keyline, the ink edge
TEXT_RIGHT = SIGN_W - 5   # the miles are right aligned on this column


def plate_rows():
    """The 96 x 24 character grid of the bare plate, from the nine slice."""
    rows = []
    for band in PLATE:
        for y in range(TILE):
            line = []
            for tile in band:
                line.append(tile[y])
            rows.append("".join(line))
    for index, row in enumerate(rows):
        if len(row) != SIGN_W:
            raise SystemExit("plate row %d is %d characters, the frame is %d wide" % (index, len(row), SIGN_W))
    if len(rows) != SIGN_H:
        raise SystemExit("the plate is %d rows, the frame is %d" % (len(rows), SIGN_H))
    return rows


def stamp_text(rows, x, y, message, ink=WHITE):
    """Write one line of the project's own 5 x 7 glyphs into the grid, one pixel per cell."""
    cursor = x
    for character in message.upper():
        glyph = world.GLYPHS.get(character)
        if glyph is None:
            raise SystemExit("the plate uses %r, which the project's glyph table does not have" % character)
        for ry in range(world.GLYPH_H):
            for rx in range(world.GLYPH_W):
                if glyph[ry][rx]:
                    grid_x = cursor + rx
                    grid_y = y + ry
                    if not (0 <= grid_x < SIGN_W and 0 <= grid_y < SIGN_H):
                        raise SystemExit("a glyph at %r does not fit the frame" % message)
                    line = list(rows[grid_y])
                    line[grid_x] = ink
                    rows[grid_y] = "".join(line)
        cursor += world.GLYPH_W + world.GLYPH_GAP
    return rows


def frame_rows(index):
    """One frame: the plate, then the destination on the top line and the miles on the bottom one."""
    rows = plate_rows()
    (top_name, top_miles), (bottom_name, bottom_miles) = TEXTS[index]
    rows = stamp_text(rows, TEXT_X, LINE_Y[0], top_name)
    rows = stamp_text(rows, TEXT_RIGHT - world.text_width(top_miles), LINE_Y[0], top_miles)
    rows = stamp_text(rows, TEXT_X, LINE_Y[1], bottom_name)
    rows = stamp_text(rows, TEXT_RIGHT - world.text_width(bottom_miles), LINE_Y[1], bottom_miles)
    return rows


def rows_image(rows):
    """The character grid as an RGBA image. Nothing is drawn that is not a character in the grid."""
    image = Image.new("RGBA", (SIGN_W, SIGN_H), CLEAR)
    pixels = image.load()
    for y, row in enumerate(rows):
        for x, letter in enumerate(row):
            if letter == ".":
                continue
            hexs = COLOURS[letter]
            pixels[x, y] = (int(hexs[1:3], 16), int(hexs[3:5], 16), int(hexs[5:7], 16), 255)
    return image


def build_ground(root):
    """The 96 x 24 of verge the sign is composited over, rebuilt from the shipped title layers.

    The reader is the runtime's: data/title.json lists the scrolling layers with their y and speed,
    and the composer draws the sign at title.json's own sign.x, sign.y, which is relative to the
    verge layer's y (tools/art/make_title_world.py compose()). At camera 0 every speed term is 0, so
    the ground is the layer stack itself, cropped at the sign's placement with the sign left out.
    That is the reading the menu cursor and the cone got on cards t_ae4bbd15 and t_b825be3e: the
    composed title under the sprite, so the check measures the pixels the plate is really laid on.
    """
    with open(os.path.join(root, "data", "title.json"), "r", encoding="utf-8-sig") as handle:
        title = json.load(handle)
    frame = Image.new("RGBA", (256, 240), (0, 0, 0, 255))
    used = []
    for layer in title["layers"]:
        path = os.path.join(root, "game", "sprites_src", "title", layer["name"] + ".png")
        if not os.path.isfile(path):
            raise SystemExit("a title layer is missing: %s" % path)
        with Image.open(path) as handle:
            strip_image = handle.convert("RGBA").copy()
        strip = Image.new("RGBA", (strip_image.width * 2, strip_image.height), CLEAR)
        strip.paste(strip_image, (0, 0))
        strip.paste(strip_image, (strip_image.width, 0))
        frame.alpha_composite(strip.crop((0, 0, 256, strip_image.height)), (0, layer["y"]))
        used.append(layer["name"])
    verge = next(layer for layer in title["layers"] if layer["name"] == "title_L5_verge")
    x = int(title["sign"]["x"])
    y = int(verge["y"]) + int(title["sign"]["y"])
    return frame.crop((x, y, x + SIGN_W, y + SIGN_H)), (x, y), used


def audit(images, rows_per_frame):
    """The row's numbers in words: entries, the worst 8 x 8 tile, drawn px and the ink edge."""
    counts = {}
    for rows in rows_per_frame:
        for row in rows:
            for letter in row:
                if letter != ".":
                    counts[letter] = counts.get(letter, 0) + 1
    worst, worst_at = 0, None
    for rows in rows_per_frame:
        for top in range(0, SIGN_H, TILE):
            for left in range(0, SIGN_W, TILE):
                seen = set()
                for y in range(top, top + TILE):
                    for x in range(left, left + TILE):
                        if rows[y][x] != ".":
                            seen.add(rows[y][x])
                if len(seen) > worst:
                    worst, worst_at = len(seen), (left // TILE, top // TILE)
    darkest = min(COLOURS, key=lambda letter: _luma(COLOURS[letter]))
    edge = []
    for rows in rows_per_frame:
        edge_pixels = [(x, 0) for x in range(SIGN_W)] + [(x, SIGN_H - 1) for x in range(SIGN_W)]
        edge_pixels += [(0, y) for y in range(1, SIGN_H - 1)] + [(SIGN_W - 1, y) for y in range(1, SIGN_H - 1)]
        edge += [rows[y][x] for x, y in edge_pixels]
    ink_edge = sum(1 for letter in edge if letter == INK)
    drawn = sum(counts.values())
    print("  spr_title_sign %dx%d per frame, %d frames, %d tiles per frame" % (SIGN_W, SIGN_H, FRAMES,
                                                                             COLUMNS * ROWS))
    print("  entries %s, drawn %d px over %d frames, worst 8x8 tile %d opaque colours %s"
          % (" ".join("%s=%d" % (COLOURS[k], v) for k, v in sorted(counts.items())), drawn, FRAMES,
             worst, worst_at))
    print("  outline edge: %d of %d outer boundary pixels are the plate's ink $00 (the darkest entry the"
          " checker reads is %s, because #007800 measures under #7c7c7c on the 2C02 table)"
          % (ink_edge, len(edge), COLOURS[darkest]))
    return counts, worst, drawn, ink_edge, len(edge)


def _luma(hexs):
    """The 2C02 luminance of an entry, read from the project's own contrast tool."""
    import contrast_check
    return contrast_check.luminance(tuple(int(hexs[i:i + 2], 16) for i in (1, 3, 5)))


def main() -> int:
    out = os.path.join(ROOT, "output", "redraws")
    os.makedirs(out, exist_ok=True)

    rows_per_frame = [frame_rows(index) for index in range(FRAMES)]
    images = [rows_image(rows) for rows in rows_per_frame]
    sheet = Image.new("RGBA", (SIGN_W * FRAMES, SIGN_H), CLEAR)
    for index, image in enumerate(images):
        sheet.alpha_composite(image, (index * SIGN_W, 0))
    path = os.path.join(out, "spr_title_sign.png")
    sheet.save(path, "PNG")
    counts, worst, drawn, ink_edge, edge_total = audit(images, rows_per_frame)

    ground, at, layers = build_ground(ROOT)
    ground_path = os.path.join(ROOT, "output", "spr_title_sign_ground.png")
    ground.save(ground_path, "PNG")
    ground_counts = {}
    for pixel in ground.convert("RGB").getdata():
        ground_counts[pixel] = ground_counts.get(pixel, 0) + 1
    print("  ground %dx%d at %d,%d from %d title layers: %s"
          % (ground.width, ground.height, at[0], at[1], len(layers), os.path.basename(ground_path)))
    print("  ground entries %s" % " ".join("#%02x%02x%02x=%d" % (k[0], k[1], k[2], v)
                                           for k, v in sorted(ground_counts.items(), key=lambda kv: -kv[1])))
    print("  wrote %s" % os.path.relpath(path, ROOT).replace(os.sep, "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
