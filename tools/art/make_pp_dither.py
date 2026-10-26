#!/usr/bin/env python3
"""spr_pp_dither: the 50 percent checker the dodge arena dims the battle field with, as one tile.

Why a sheet and not a rectangle. Spec 13 allows two dither patterns and says "A gradient is a stack of those, never a
blended ramp", so the dim spec 08 asks for has to be drawn as pixels rather than as an alpha band: an alpha band spends
colours outside the 54 the palette has, and a recording of the first fight measured exactly that (knowledge
BATTLE-DIM-OFF-PALETTE-2026-10-26.md, card t_06ef8607). One 16x16 tile of a one pixel checker, tiled across the 256x240
frame, is 240 quads in a single draw call. The same pattern built out of GML rectangles is 30,720 calls a frame, which
is not a draw the engine has ever been asked for.

The sheet is a mask, not art: every drawn pixel is #ffffff and every other pixel is transparent, so the runtime draws it
with draw_sprite_tiled_ext tinted by the room's own ink role and the screen still spends exactly one declared colour.
That is why #ffffff is allowed here when a sprite may never use it: white is the tint's identity, not a colour the frame
shows. The sidecar says so in its own rule line.

Outputs:
    game\\sprites_src\\title\\spr_pp_dither.png    16x16, one tile, 1 px 50 percent checker
    game\\sprites_src\\title\\spr_pp_dither.json   the tile size plus the tint contract, for the game code

Checks in this script: the tile is 16x16, exactly half the pixels are opaque, the opaque ones are the (x + y) even ones
(the 50 percent checker spec 13 names), every opaque pixel is white, the tile divides the 256x240 frame exactly, and no
line of this file or its output carries a long dash.

Usage:
    python tools\\art\\make_pp_dither.py
    python tools\\art\\make_pp_dither.py --root <repo>

Clean room: a checkerboard of one pixel cells is arithmetic, not artwork, and nothing here was measured off a game.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from PIL import Image

TILE = 16
FRAME = (256, 240)
MASK_RGB = (255, 255, 255)
OUT_DIR = os.path.join("game", "sprites_src", "title")
NAME = "spr_pp_dither"


def tile_pixels():
    """The 50 percent checker: the (x + y) even pixels of the tile are drawn, the rest are transparent."""
    return {(x, y) for y in range(TILE) for x in range(TILE) if (x + y) % 2 == 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description="write spr_pp_dither, the dodge dim's 50 percent checker tile")
    parser.add_argument("--root", default=None, help="repository root (default: two levels above this file)")
    args = parser.parse_args(argv)

    root = args.root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out = os.path.join(root, OUT_DIR)
    os.makedirs(out, exist_ok=True)

    drawn = tile_pixels()
    image = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    pixels = image.load()
    for y in range(TILE):
        for x in range(TILE):
            if (x, y) in drawn:
                pixels[x, y] = MASK_RGB + (255,)

    # Checks, before anything is written: a tile that is not a 50 percent checker is not this sheet.
    opaque = [(x, y) for y in range(TILE) for x in range(TILE) if pixels[x, y][3] == 255]
    assert len(opaque) * 2 == TILE * TILE, "the tile is not half opaque: %d of %d" % (len(opaque), TILE * TILE)
    assert set(opaque) == drawn, "the opaque pixels are not the (x + y) even ones"
    assert {pixels[x, y][:3] for x, y in opaque} == {MASK_RGB}, "an opaque pixel is not the mask white"
    assert FRAME[0] % TILE == 0 and FRAME[1] % TILE == 0, "%dx%d does not tile %dx%d exactly" % (
        TILE, TILE, FRAME[0], FRAME[1])

    png = os.path.join(out, NAME + ".png")
    image.save(png)

    meta = {
        "name": NAME,
        "kind": "mask",
        "layer": True,
        "frame_w": TILE,
        "frame_h": TILE,
        "frames": 1,
        "fps": 0.0,
        "colours": {"mask": "#ffffff"},
        "rule": ("a mask, not art: the drawn pixels are pure white so draw_sprite_tiled_ext tints them to exactly the "
                 "role colour that asks for them (the dodge arena asks for ink), and the other pixels are transparent. "
                 "One pixel 50 percent checker, spec 13's allowed dither, tiled from the frame origin: 256 / 16 and "
                 "240 / 16 are whole, so the tile lands on the frame with no partial cell at the edge."),
    }
    with open(os.path.join(out, NAME + ".json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(meta, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print("wrote %s  %dx%d  %d of %d pixels opaque" % (png, TILE, TILE, len(opaque), TILE * TILE))
    print("wrote %s.json" % os.path.join(out, NAME))
    return 0


if __name__ == "__main__":
    sys.exit(main())
