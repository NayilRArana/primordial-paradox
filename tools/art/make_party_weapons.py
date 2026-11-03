#!/usr/bin/env python3
"""make_party_weapons.py: redraw ONLY the four party battle sheets so each figure holds its weapon (FINAL-SCOPE D2).

ZANDER the master bolt, KONRAD an adamantine scythe, HADRIAN the bident and the dark helm, PERCY the trident. The
drawing, the reserved hero triples and the tile carrier all come from make_characters.py; this entry point exists so
the overworld sheets that tool also writes (owned by another lane) are never touched.

Usage:  python tools/art/make_party_weapons.py [--dump]
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_characters as mc  # noqa: E402

PARTY = ("zander", "konrad", "hadrian", "percy")


def main(argv=None):
    root = mc.REPO_ROOT
    mc.REPO_ROOT = root
    with open(os.path.join(root, "data", "nes_palette.json"), "r", encoding="utf-8") as handle:
        palette = json.load(handle)
    out_dir = os.path.join(root, "game", "sprites_src", "chars")
    notes = []
    for spec in mc.character_specs():
        if spec["name"] not in PARTY:
            continue
        frames, _carried = mc.party_battle_sheet(spec)
        image = mc.sheet_image(frames, mc.party_hexes(palette, spec["name"]), mc.BATTLE_W, mc.BATTLE_H)
        mc.check_with_nes_check(image, spec["name"] + "_battle")
        mc.check_party_triple(image, spec["name"] + "_battle")
        mc.write_sheet(out_dir, spec["name"] + "_battle", image, mc.BATTLE_W, mc.BATTLE_H, mc.BATTLE_FPS, notes)
    for name, width, height, count, digest in notes:
        print("%-16s %dx%d %d frames sha %s" % (name, width, height, count, digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
