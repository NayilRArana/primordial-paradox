#!/usr/bin/env python3
"""make_god_weapons.py: the four signature weapon swing sheets (FINAL-SCOPE D2, 2026-11-03).

    game/sprites_src/weapons/spr_pp_master_bolt.png         ZANDER, 4 frames of 32x32 (frame 0 icon, 1 to 3 the strike)
    game/sprites_src/weapons/spr_pp_adamantine_scythe.png   KONRAD
    game/sprites_src/weapons/spr_pp_bident.png              HADRIAN
    game/sprites_src/weapons/spr_pp_trident.png             PERCY

Each sheet wears its owner's reserved hero triple from data/scene_palettes.json (ink $0F, body, accent), exactly three
opaque colours, so it is legal on a battle strip that carries the four hero palettes. Same contract as spr_pp_knife:
the sheet is an overlay the battle director draws over the enemy while the FIGHT message plays.

Usage:  python tools/art/make_god_weapons.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import battle_art as B  # noqa: E402
from battle_art import Canvas, T, K  # noqa: E402

W = 32
OUT = os.path.join(B.ROOT, "game", "sprites_src", "weapons")
TRIPLES = {"zander": (0x21, 0x31), "konrad": (0x27, 0x00), "hadrian": (0x23, 0x03), "percy": (0x12, 0x28)}


def bolt(c, body, acc, size, spark):
    seg = [(24, 2), (13, 13), (20, 15), (8, 29)]
    n = max(1, int(len(seg) * size))
    for i in range(min(n, len(seg) - 1) if size < 1 else len(seg) - 1):
        (x0, y0), (x1, y1) = seg[i], seg[i + 1]
        c.line(x0, y0, x1, y1, body, 4)
        c.line(x0 + 1, y0, x1 + 1, y1, acc, 2)
    if spark:
        for x, y in ((6, 28), (10, 30), (4, 24), (12, 29), (26, 6), (28, 10)):
            c.put(x, y, acc)


def scythe(c, body, acc, t):
    # a crescent: points along an arc whose sweep grows with t (0..1)
    import math
    cx, cy, r = 6, 26, 20
    start = -80
    end = start + int(110 * t)
    for a in range(start, end + 1, 2):
        x = cx + r * math.cos(math.radians(a))
        y = cy + r * math.sin(math.radians(a))
        c.rect(int(x) - 1, int(y) - 1, int(x) + 1, int(y) + 1, acc)
        x2 = cx + (r - 4) * math.cos(math.radians(a))
        y2 = cy + (r - 4) * math.sin(math.radians(a))
        c.put(int(x2), int(y2), body)
    if t >= 0.6:
        for x, y in ((28, 20), (29, 14), (26, 24)):
            c.put(x, y, body)


def prongs(c, body, acc, reach, n, spark):
    ys = (10, 21) if n == 2 else (8, 16, 24)
    for y in ys:
        c.line(2, 16, 2 + reach, y, acc, 2)
        c.rect(2 + reach - 1, y - 1, 2 + reach + 1, y + 1, body)
    c.line(0, 16, 2 + reach // 2, 16, body, 3)
    if spark:
        for x, y in ((28, 4), (30, 15), (27, 28), (29, 22)):
            c.put(x, y, acc)
            c.put(x - 1, y, body)


def icon(c, body, acc, kind):
    if kind == "bolt":
        c.line(20, 6, 12, 15, acc, 2)
        c.line(12, 15, 18, 17, acc, 2)
        c.line(18, 17, 10, 27, acc, 2)
    elif kind == "scythe":
        c.line(8, 28, 22, 6, acc, 2)
        c.line(22, 6, 28, 8, body, 2)
        c.line(28, 8, 27, 13, acc, 2)
    else:
        n = 2 if kind == "bident" else 3
        c.line(16, 28, 16, 8, acc, 2)
        for dx in ((-5, 5) if n == 2 else (-6, 0, 6)):
            c.line(16 + dx, 8, 16 + dx, 3, body, 2)
        c.line(10, 8, 22, 8, body, 2)


def build(kind, owner, name):
    body, acc = TRIPLES[owner]
    frames = []
    for i in range(4):
        c = Canvas(W, W, T)
        if i == 0:
            icon(c, body, acc, kind)
        elif kind == "bolt":
            bolt(c, body, acc, (0.5, 1.0, 1.0)[i - 1], i == 3)
        elif kind == "scythe":
            scythe(c, body, acc, (0.35, 0.8, 1.0)[i - 1])
        elif kind == "bident":
            prongs(c, body, acc, (14, 26, 18)[i - 1], 2, i == 2)
        else:
            prongs(c, body, acc, (14, 26, 18)[i - 1], 3, i == 2)
        a = B.outline(c.a, K)
        a, _ = B.cap_tiles(a)
        frames.append(a)
    import numpy as np
    sheet = np.full((W, W * 4), T, dtype=np.uint8)
    for i, f in enumerate(frames):
        sheet[:, i * W:(i + 1) * W] = f
    used = B.colours_used(sheet)
    assert set(used) <= {K, body, acc}, (name, used)
    assert not B.audit_tiles(sheet), name
    B.to_image(sheet).save(os.path.join(OUT, name + ".png"))
    side = {"format": 1, "kind": "weapon_frames", "name": name, "size": "%dx%d" % (W * 4, W),
            "frame_w": W, "frame_h": W, "frames": 4, "fps": 8.0, "transparent": True, "layer": True,
            "frame_roles": {"icon": 0, "slash_frames": [1, 2, 3]}, "colour_count": 3,
            "sprite_palettes_used": [owner],
            "colours_used": [{"index": u, "role": r} for u, r in zip(sorted(used), ("ink", "body", "accent")[:len(used)])],
            "note": "FINAL-SCOPE D2. Overlay in %s's reserved hero triple. Built by tools/art/make_god_weapons.py." % owner}
    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(side, handle, indent=2)
        handle.write("\n")
    return sheet


def main():
    for kind, owner, name in (("bolt", "zander", "spr_pp_master_bolt"), ("scythe", "konrad", "spr_pp_adamantine_scythe"),
                              ("bident", "hadrian", "spr_pp_bident"), ("trident", "percy", "spr_pp_trident")):
        build(kind, owner, name)
        print("wrote", name)


if __name__ == "__main__":
    main()
