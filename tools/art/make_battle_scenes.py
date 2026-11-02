#!/usr/bin/env python3
"""make_battle_scenes.py: draw the three battle scene backgrounds (256x168) for the 2026-11-01 battle screen redesign.

    bg_battle_quay_town    Southampton Town Quay at dusk (Morgan, the dock checkpoint)
    bg_battle_ship_deck    the ship's steel deck at night (the Navy sailor)
    bg_battle_ship_office  the officer's office aboard the ship (Percy Skye)

Procedural, original, deterministic. The quay houses are tiles of the project's own quay v2 set (game/sprites_src/env/
quay/quay_v2_tiles.png), so the battle and the overworld speak one visual language; everything else is painted here.
NES rules by construction: every pixel is a 2C02 entry, every 16x16 attribute area carries at most 3 colours besides
the shared backdrop 0F (cap_cells does the final reduction and the audit proves it), dither is checker or 25 percent.

Outputs
    game/sprites_src/bg/bg_battle_<name>.png + .json      the picture and its sidecar (kind battle_background)
    output/battle_visuals_2026-11-01/bg/<name>.png        1x and _3x for looking at

Usage:  python tools/art/make_battle_scenes.py
"""
from __future__ import annotations

import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from battle_art import *  # noqa: E402,F401,F403
import battle_art as B  # noqa: E402

W, H = 256, 168
OUT = os.path.join(ROOT, "output", "battle_visuals_2026-11-01", "bg")
BG_DIR = os.path.join(ROOT, "game", "sprites_src", "bg")


# ------------------------------------------------------------------------------------------------------ quay
def q_sky(c, hz):
    c.rect(0, 0, W - 1, hz - 1, K)
    c.dither(0, 8, W - 1, 17, VIO)
    c.rect(0, 18, W - 1, 29, VIO)
    c.dither(0, 30, W - 1, 37, PNK)
    c.rect(0, 38, W - 1, 45, PNK)
    c.dither25(0, 38, W - 1, 45, VIO)
    c.rect(0, 46, W - 1, 53, PNK)
    c.dither(0, 54, W - 1, 59, RED)
    c.rect(0, 60, W - 1, hz - 1, RED)
    rng = random.Random(5)
    for _ in range(46):
        c.put(rng.randrange(W), rng.randrange(1, 17), PNK)
    for x, y, n in ((10, 24, 24), (88, 20, 16), (150, 27, 28), (214, 22, 20), (60, 36, 14), (186, 41, 24), (24, 44, 18)):
        c.rect(x, y, x + n, y + 1, PNK)
        c.rect(x + 4, y + 2, x + n - 6, y + 2, PNK)


def q_galleon(c, x, wl):
    """A Mayflower style three master, a silhouette against the glow."""
    c.poly([(x, wl - 9), (x + 36, wl - 9), (x + 32, wl), (x + 7, wl), (x + 1, wl - 3)], K)
    c.rect(x + 25, wl - 15, x + 36, wl - 9, K)
    c.rect(x - 1, wl - 12, x + 7, wl - 9, K)
    c.line(x - 1, wl - 12, x - 11, wl - 18, K)
    for mx, top in ((x + 11, wl - 38), (x + 20, wl - 45), (x + 30, wl - 32)):
        c.rect(mx, top, mx + 1, wl - 9, K)
    c.rect(x + 4, wl - 34, x + 18, wl - 23, K)
    c.rect(x + 13, wl - 41, x + 28, wl - 25, K)
    c.rect(x + 24, wl - 29, x + 36, wl - 19, K)
    c.dither(x + 6, wl - 33, x + 17, wl - 24, PNK, 1)
    c.dither(x + 15, wl - 40, x + 27, wl - 26, PNK, 1)
    c.dither(x + 26, wl - 28, x + 35, wl - 20, PNK, 1)
    c.rect(x + 20, wl - 49, x + 24, wl - 47, RED)
    c.rect(x + 33, wl - 14, x + 34, wl - 12, RED)
    c.line(x + 11, wl - 38, x - 8, wl - 17, K)
    c.line(x + 30, wl - 32, x + 40, wl - 12, K)


def q_liner(c):
    """The big red funnel liner: black hull, stepped decks, three red funnels with black tops."""
    wl = 94
    c.poly([(150, 80), (255, 80), (255, wl), (172, wl)], K)
    c.rect(160, 88, 255, 89, RED)
    for x in range(178, 254, 7):
        c.put(x, 84, PNK)
    c.rect(176, 70, 255, 79, K)
    c.rect(190, 62, 255, 69, K)
    c.rect(204, 55, 238, 61, K)
    for x in range(180, 254, 5):
        c.put(x, 74, PNK)
    for x in range(194, 254, 5):
        c.put(x, 66, PNK)
    for fx in (196, 214, 232):
        c.rect(fx - 1, 28, fx + 12, 56, K)
        c.rect(fx, 31, fx + 11, 56, RED)
        c.rect(fx, 31, fx + 11, 36, K)
        c.rect(fx, 44, fx + 11, 46, PNK)
    c.rect(222, 14, 223, 55, K)
    c.line(222, 16, 186, 56, K)
    c.line(223, 16, 255, 60, K)
    c.rect(150, 96, 255, 103, K)


def q_water(c, hz, edge):
    c.rect(0, hz, W - 1, edge - 1, K)
    rng = random.Random(3)
    for y in range(hz, edge):
        d = (y - hz) / float(edge - hz)
        if d < 0.15:
            c.rect(0, y, W - 1, y, RED)
        elif d < 0.4:
            c.dither(0, y, W - 1, y, RED, y)
        elif d < 0.65:
            c.dither25(0, y, W - 1, y, VIO, y)
    for y in range(hz + 2, edge - 1, 2):
        col = RED if y < hz + 7 else (PNK if y < hz + 15 else VIO)
        for _ in range(9):
            x = rng.randrange(-6, W)
            c.rect(x, y, x + rng.randrange(3, 13), y, col)


def q_edge(c, edge, ground):
    c.rect(0, edge, W - 1, edge + 1, LGR)
    c.rect(0, edge + 2, W - 1, ground - 1, GRY)
    c.rect(0, edge + 2, W - 1, edge + 2, K)
    for x in range(0, W, 16):
        c.rect(x, edge + 3, x, ground - 1, K)
        c.rect(x + 8, edge + 6, x + 8, ground - 1, K)
    c.rect(0, edge + 5, W - 1, edge + 5, K)


def q_house(c, tiles, x, y, rows):
    for j, row in enumerate(rows):
        for i, name in enumerate(row):
            c.blit(tiles[name], x + i * 16, y + j * 16)


def q_lamp(c, x, ground):
    c.rect(x, 58, x + 1, ground + 4, K)
    c.rect(x - 1, ground + 4, x + 2, ground + 5, K)
    c.rect(x - 4, 46, x + 5, 58, K)
    c.rect(x - 2, 48, x + 3, 56, GLD)
    c.rect(x - 1, 49, x, 53, PGD)
    c.poly([(x - 5, 46), (x + 6, 46), (x + 1, 41)], K)
    c.dither25(x - 8, 44, x + 9, 60, GLD, 1)


def q_bollard(c, x, y):
    c.rect(x, y + 3, x + 8, y + 12, K)
    c.rect(x + 1, y + 4, x + 7, y + 11, GRY)
    c.rect(x + 1, y + 4, x + 2, y + 11, LGR)
    c.rect(x - 1, y, x + 9, y + 3, K)
    c.rect(x, y + 1, x + 8, y + 2, LGR)


def q_barrier(c):
    c.rect(214, 98, 221, 119, K)
    c.rect(215, 99, 220, 118, LGR)
    c.rect(215, 99, 216, 118, GRY)
    c.rect(222, 102, 255, 109, K)
    for i, x in enumerate(range(223, 256, 6)):
        c.rect(x, 103, min(x + 2, 255), 108, RED if i % 2 == 0 else LGR)
        c.rect(min(x + 3, 255), 103, min(x + 5, 255), 108, LGR if i % 2 == 0 else RED)
    c.rect(214, 120, 221, 121, K)


def paint_quay(tiles):
    hz, edge, ground = 64, 88, 96
    c = Canvas(W, H, K)
    q_sky(c, hz)
    q_galleon(c, 116, hz + 4)
    q_liner(c)
    q_water(c, hz, edge)
    q_edge(c, edge, ground)
    rng = random.Random(17)
    for ty in range(ground, H, 16):
        for tx in range(0, W, 16):
            r = rng.random()
            c.blit(tiles["paving" if r < 0.9 else "paving_drain"], tx, ty)
    q_house(c, tiles, 0, 32, [
        ["roof_ridge_a", "chimney_a", "roof_ridge_a", "roof_ridge_a"],
        ["roof_eave_a"] * 4,
        ["window_lit", "wall", "window_dark", "wall"],
        ["wall", "door", "wall", "window_lit"]])
    q_house(c, tiles, 64, 32, [
        ["roof_ridge_b", "chimney_b", "roof_ridge_b"],
        ["roof_eave_b"] * 3,
        ["wall", "window_lit", "wall"],
        ["awning", "door", "window_dark"]])
    c.poly([(121, 80), (143, 80), (139, 86), (125, 86)], K)
    c.rect(122, 79, 142, 79, PNK)
    c.rect(131, 66, 132, 79, K)
    c.poly([(132, 67), (132, 78), (140, 78)], K)
    q_lamp(c, 120, ground)
    q_bollard(c, 134, 78)
    q_bollard(c, 206, 78)
    q_barrier(c)
    return c, (GLD, PGD, RED, WHT)


# ------------------------------------------------------------------------------------------------------ deck
def paint_deck(tiles):
    c = Canvas(W, H, K)
    hz = 64
    rng = random.Random(11)
    c.dither(0, 24, W - 1, 35, BLU)
    c.rect(0, 36, W - 1, 55, BLU)
    c.dither(0, 48, W - 1, 55, BLB)
    c.rect(0, 56, W - 1, hz - 1, BLB)
    for _ in range(64):
        x, y = rng.randrange(W), rng.randrange(0, 44)
        if c.get(x, y) in (K, BLU):
            c.put(x, y, WHT)
    for x, y in ((24, 10), (150, 20), (206, 8), (60, 30), (236, 36)):
        for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            c.put(x + dx, y + dy, WHT)
    for x, y, n in ((8, 40, 30), (84, 46, 22), (170, 44, 34), (214, 52, 26)):
        c.rect(x, y, x + n, y, BLB)
    c.ellipse(116, 17, 8, 8, PGD)
    c.ellipse(120, 14, 7, 7, K)
    c.rect(0, hz, W - 1, 95, BLU)
    c.rect(0, hz, W - 1, hz, BLB)
    for y in range(hz + 2, 96, 3):
        for _ in range(8):
            x = rng.randrange(-8, W)
            c.rect(x, y, x + rng.randrange(4, 14), y, BLB)
    c.dither25(0, 84, W - 1, 95, K)
    for i, y in enumerate(range(hz + 2, 90, 3)):
        w = max(3, 13 - i)
        x = 116 - w // 2 + (1 if i % 2 else -1)
        c.rect(x, y, x + w, y, PGD)
    # rail along the open side (right of the superstructure)
    c.rect(96, 74, W - 1, 76, LGR)
    c.rect(96, 77, W - 1, 77, K)
    c.rect(96, 84, W - 1, 85, LGR)
    c.rect(96, 86, W - 1, 86, K)
    c.rect(96, 91, W - 1, 91, K)
    c.rect(96, 92, W - 1, 95, LGR)
    for px in range(100, 256, 20):
        c.rect(px, 74, px + 2, 95, LGR)
        c.rect(px + 3, 77, px + 3, 95, K)
        c.rect(px, 77, px, 95, K)
    # mast and rigging on the right
    c.rect(232, 40, 235, 95, GRY)
    c.rect(232, 40, 232, 95, LGR)
    c.rect(214, 52, 252, 53, LGR)
    c.rect(231, 37, 236, 41, GLD)
    c.line(233, 41, 198, 90, LGR)
    c.line(234, 41, 255, 88, LGR)
    # funnel (behind) and superstructure
    c.poly([(36, 6), (66, 6), (69, 36), (33, 36)], K)
    c.poly([(37, 7), (65, 7), (67, 36), (35, 36)], RED)
    c.rect(33, 2, 69, 8, K)
    c.rect(36, 18, 66, 22, WHT)
    c.rect(59, 9, 65, 35, DRD)
    c.rect(0, 36, 95, 95, K)
    c.rect(0, 37, 95, 95, GRY)
    c.rect(0, 37, 95, 38, LGR)
    c.rect(0, 39, 95, 39, K)
    for x in (24, 48, 72):
        c.rect(x, 40, x, 95, K)
        c.rect(x + 1, 40, x + 1, 95, LGR)
    for x in range(0, 96, 24):
        for y in (44, 90):
            c.put(x + 4, y, LGR)
            c.put(x + 19, y, LGR)
    for cx in (12, 36, 60):
        c.ellipse(cx, 56, 9, 9, K)
        c.ellipse(cx, 56, 8, 8, LGR)
        c.ellipse(cx, 56, 6, 6, K)
        c.ellipse(cx, 56, 5, 5, PGD)
        c.put(cx - 2, 53, WHT)
    for cx in (18, 46):
        for yy in range(-9, 10):
            for xx in range(-9, 10):
                d2 = xx * xx + yy * yy
                if d2 <= 81:
                    if d2 >= 64:
                        c.put(cx + xx, 82 + yy, K)
                    elif d2 >= 16:
                        c.put(cx + xx, 82 + yy, RED if (xx > 0) == (yy > 0) else WHT)
                    else:
                        c.put(cx + xx, 82 + yy, GRY)
    c.rect(70, 62, 92, 95, K)
    c.rect(72, 64, 90, 95, GRY)
    c.rect(72, 64, 73, 95, LGR)
    c.ellipse(81, 80, 5, 5, K)
    c.ellipse(81, 80, 4, 4, LGR)
    c.ellipse(81, 80, 1, 1, K)
    c.rect(72, 72, 90, 72, K)
    c.rect(66, 64, 69, 72, K)
    c.rect(67, 65, 68, 71, PGD)
    # deck plates
    c.rect(0, 96, W - 1, H - 1, GRY)
    c.rect(0, 96, W - 1, 96, K)
    c.rect(0, 97, W - 1, 97, LGR)
    for row, y0 in enumerate(range(98, H, 24)):
        c.rect(0, y0 + 22, W - 1, y0 + 22, K)
        c.rect(0, y0 + 23, W - 1, y0 + 23, LGR)
        for x in range(8 + (row % 2) * 24, W, 48):
            c.rect(x, y0, x, y0 + 21, K)
            c.rect(x + 1, y0, x + 1, y0 + 21, LGR)
            c.put(x + 4, y0 + 3, LGR)
            c.put(x + 4, y0 + 18, LGR)
            c.put(x - 4, y0 + 3, LGR)
            c.put(x - 4, y0 + 18, LGR)
    c.rect(0, 100, W - 1, 100, WHT)
    c.rect(110, 102, 124, 105, K)
    c.rect(111, 103, 123, 104, LGR)
    c.rect(112, 105, 122, 116, K)
    c.rect(113, 105, 121, 115, GRY)
    c.rect(113, 105, 115, 115, LGR)
    return c, (GLD, PGD, RED, WHT)


# ------------------------------------------------------------------------------------------------------ office
def paint_office(tiles):
    c = Canvas(W, H, K)
    # steel bulkhead with a pipe run under the ceiling
    c.rect(0, 8, W - 1, 71, GRY)
    c.rect(0, 0, W - 1, 7, K)
    c.rect(0, 2, W - 1, 5, GRY)
    c.rect(0, 2, W - 1, 2, LGR)
    for x in range(0, W, 32):
        c.rect(x, 8, x, 71, K)
        c.rect(x + 1, 8, x + 1, 71, LGR)
        for y in (12, 66):
            c.put(x + 5, y, LGR)
            c.put(x + 27, y, LGR)
    c.rect(0, 72, W - 1, 73, DGO)
    c.rect(0, 74, W - 1, 74, K)
    c.rect(0, 75, W - 1, 95, BRN)
    for x in range(0, W, 16):
        c.rect(x, 75, x, 95, K)
        c.rect(x + 1, 77, x + 1, 93, DGO)
    # floor: baseboard and carpet with a gold border and lozenges
    c.rect(0, 96, W - 1, 99, BRN)
    c.rect(0, 99, W - 1, 99, K)
    c.rect(0, 100, W - 1, H - 1, DRD)
    c.rect(0, 100, W - 1, 101, DGO)
    c.rect(0, 102, W - 1, 102, K)
    for kx in range(8, W, 32):
        c.poly([(kx, 112), (kx + 10, 105), (kx + 20, 112), (kx + 10, 119)], DGO)
        c.poly([(kx + 5, 112), (kx + 10, 108), (kx + 15, 112), (kx + 10, 116)], DRD)
    # porthole in a brass plate (grid aligned): sky over sea
    c.rect(16, 16, 63, 63, GLD)
    c.frame(16, 16, 63, 63, K)
    for rx, ry in ((19, 19), (59, 19), (19, 59), (59, 59)):
        c.put(rx, ry, K)
    c.ellipse(40, 40, 20, 20, K)
    for y in range(20, 61):
        for x in range(20, 61):
            if ((x - 40) ** 2 + (y - 40) ** 2) <= 19 * 19 + 19:
                c.put(x, y, LBL if y < 40 else AZU)
    for x, y in ((28, 48), (34, 52), (46, 47), (52, 54), (40, 58), (30, 44)):
        c.rect(x, y, x + 3, y, WHT)
    c.rect(24, 36, 30, 37, WHT)
    # lamp between porthole and flag
    c.rect(71, 8, 72, 21, K)
    c.poly([(64, 31), (79, 31), (76, 22), (67, 22)], K)
    c.poly([(65, 30), (78, 30), (75, 23), (68, 23)], DGO)
    c.rect(69, 31, 74, 33, PGD)
    c.dither25(60, 35, 83, 47, LGR, 1)
    # Royal Navy ensign (grid aligned 48x32): white field, red cross, union canton
    c.rect(78, 13, 129, 14, GLD)
    c.rect(80, 16, 127, 47, WHT)
    c.rect(80, 29, 127, 34, RED)
    c.rect(100, 16, 105, 47, RED)
    c.rect(80, 16, 99, 28, BLU)
    c.line(80, 16, 99, 28, WHT, 2)
    c.line(98, 16, 80, 28, WHT, 2)
    c.rect(88, 16, 90, 28, WHT)
    c.rect(80, 21, 99, 23, WHT)
    c.rect(89, 16, 89, 28, RED)
    c.rect(80, 22, 99, 22, RED)
    c.frame(80, 16, 127, 47, K)
    # brass clock and a framed chart pair, below the enemy plate band
    c.ellipse(152, 56, 8, 8, GLD)
    c.ellipse(152, 56, 6, 6, K)
    c.ellipse(152, 56, 5, 5, CRE)
    c.line(152, 56, 152, 52, K)
    c.line(152, 56, 155, 57, K)
    c.rect(130, 48, 143, 63, GLD)
    c.rect(132, 50, 141, 61, CRE)
    c.line(133, 59, 137, 52, BLU)
    c.line(137, 52, 140, 58, BLU)
    c.frame(130, 48, 143, 63, K)
    # wall chart on the right (grid aligned 48x32) with a grid, a coast and a compass rose
    c.rect(208, 48, 255, 79, BRN)
    c.rect(210, 50, 253, 77, CRE)
    for x in range(214, 253, 8):
        c.rect(x, 50, x, 77, BLU)
    for y in range(54, 77, 8):
        c.rect(210, y, 253, y, BLU)
    c.poly([(210, 70), (222, 64), (232, 68), (240, 60), (253, 62), (253, 77), (210, 77)], BLU)
    c.dither(212, 71, 250, 76, CRE, 0)
    c.rect(243, 52, 244, 58, RED)
    c.rect(241, 55, 246, 56, RED)
    c.frame(208, 48, 255, 79, K)
    # the desk, front on, against the wainscot
    c.rect(4, 62, 115, 62, ORG)
    c.rect(4, 63, 115, 66, DGO)
    c.rect(4, 67, 115, 67, K)
    c.rect(4, 68, 115, 95, DGO)
    c.rect(4, 68, 115, 69, ORG)
    for x0 in (8, 42, 76):
        c.rect(x0, 72, x0 + 30, 88, K)
        c.rect(x0 + 1, 73, x0 + 29, 87, DGO)
        c.rect(x0 + 13, 79, x0 + 17, 81, GLD)
    c.rect(4, 90, 115, 95, BRN)
    c.rect(20, 57, 44, 61, CRE)
    c.rect(20, 61, 44, 61, K)
    c.line(24, 58, 40, 58, K)
    c.rect(52, 55, 57, 61, K)
    c.rect(54, 52, 55, 56, CRE)
    c.rect(70, 59, 94, 61, GLD)
    c.rect(70, 61, 94, 61, K)
    c.rect(255 - 8, 90, 255, 95, BRN)
    return c, (GLD, PGD, RED, WHT)


SCENES = [
    ("quay_town", "Southampton Town Quay at dusk", paint_quay),
    ("ship_deck", "The ship's steel deck at night", paint_deck),
    ("ship_office", "The officer's office aboard the ship (Percy Skye)", paint_office),
]


def sidecar(name, title, a):
    used = colours_used(a)
    return {
        "format": 1,
        "kind": "battle_background",
        "name": "bg_battle_" + name,
        "title": title,
        "png": "bg_battle_%s.png" % name,
        "width": W,
        "height": H,
        "tile_size": 8,
        "attribute_area": 16,
        "grid": {"columns": W // 16, "rows": (H + 15) // 16},
        "palette_source": "data/nes_palette.json",
        "backdrop": {"index": 15, "hex": "#000000"},
        "colours": used,
        "hex": ["#%02x%02x%02x" % NES[i] for i in used],
        "frame": {"width": 256, "height": 240, "strip_y": 0,
                  "note": "the scene fills the upper 168 rows; the windows of the battle HUD draw over it"},
        "note": "Generated by tools/art/make_battle_scenes.py (2026-11-01 battle screen redesign). Do not hand edit.",
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    tiles = B.load_quay_tiles()
    report = []
    for name, title, fn in SCENES:
        c, protect = fn(tiles)
        a, fixed = B.cap_cells(c.a, protect=protect)
        worst, bad = B.audit_cells(a)
        used = colours_used(a)
        report.append("%-13s colours %2d  worst area %d  bad areas %d  remapped pixels %d" % (name, len(used), worst, len(bad), fixed))
        img = to_image(a).convert("RGB")
        png = os.path.join(BG_DIR, "bg_battle_%s.png" % name)
        img.save(png)
        with open(os.path.join(BG_DIR, "bg_battle_%s.json" % name), "w", encoding="utf-8", newline="\n") as handle:
            json.dump(sidecar(name, title, a), handle, indent=2)
            handle.write("\n")
        img.save(os.path.join(OUT, name + ".png"))
        img.resize((W * 3, H * 3), Image.NEAREST).save(os.path.join(OUT, name + "_3x.png"))
    print("\n".join(report))


if __name__ == "__main__":
    main()
