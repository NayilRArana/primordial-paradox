#!/usr/bin/env python3
"""make_storm_art.py: spr_pp_dither25, the 25 percent dither the Town Quay storm darkens the screen with (final scope item 8).

Spec 13 allows two dithers only, the 50 percent checker (spr_pp_dither, the dodge arena's dim) and 25 percent. The storm
look is a 25 percent ink dither over the world, never an alpha blend, so every pixel on screen stays one of the declared
colours. The sheet is a mask in the same contract as spr_pp_dither: pure white drawn pixels that draw_sprite_tiled_ext
tints to a role colour, every other pixel transparent. The drawn pixels are the ones with even x and even y, one in four.

Usage: python tools/art/make_storm_art.py [--root <repo>]
"""
from __future__ import annotations

import argparse
import json
import os

from PIL import Image

TILE = 16
NAME = "spr_pp_dither25"
OUT_DIR = os.path.join("game", "sprites_src", "title")


def tile_pixels():
    return {(x, y) for y in range(TILE) for x in range(TILE) if x % 2 == 0 and y % 2 == 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    args = parser.parse_args(argv)
    root = args.root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out = os.path.join(root, OUT_DIR)
    os.makedirs(out, exist_ok=True)
    drawn = tile_pixels()
    assert len(drawn) * 4 == TILE * TILE
    image = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    for (x, y) in drawn:
        image.putpixel((x, y), (255, 255, 255, 255))
    image.save(os.path.join(out, NAME + ".png"))
    meta = {
        "colours": {"mask": "#ffffff"},
        "fps": 0.0, "frame_h": TILE, "frame_w": TILE, "frames": 1, "kind": "mask", "layer": True, "name": NAME,
        "rule": ("a mask, not art: the drawn pixels are pure white so draw_sprite_tiled_ext tints them to exactly the role "
                 "colour that asks for them (the quay storm asks for ink), and the other pixels are transparent. One pixel "
                 "in four (even x, even y), spec 13's 25 percent dither, tiled from the frame origin: 256 / 16 and "
                 "240 / 16 are whole, so no partial cell lands at the frame edge."),
    }
    with open(os.path.join(out, NAME + ".json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(meta, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("wrote %s/%s.png and .json (%d of %d pixels drawn)" % (OUT_DIR, NAME, len(drawn), TILE * TILE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
