#!/usr/bin/env python3
"""make_quay_tiles.py: the v2 Town Quay tile vocabulary (card LD-4, 2026-10-27), original art, drawn by this script.

Every glyph of knowledge/MAP-STYLE-GUIDE.md (Part A legend and Appendix A) becomes one 16 x 16 tile. Nothing is copied
from any game or sprite sheet: every tile is rectangles, lines and a seeded position hash, drawn in code.

Palette discipline (guide B9): four hue families (stone ground, roof, wall, water) plus ONE accent (orange) that only
doors, signs, steps, tickets and the gangway use. Window glow is the warm pale yellow, the only other warm colour.
Roof has two colours (rust A, slate B) that alternate per building.

Every colour is a Ricoh 2C02 OUTPUT, not a blended one (data/nes_palette.json is the authority), every 16 x 16 area
carries at most three colours besides the shared $0F backdrop, and the whole sheet spends at most 25 colours, which is
what tools/nes_check.py measures and what tools/nes_audit_all.py gates on. The painters below therefore name a ROLE
("s2", "ra1", "w3"), and FALLBACK says which role a tile gives up first when a painter wants a fourth colour in one
area: a roof with three tones and a timber joint cannot hold both inside one attribute cell, so the least used tone
folds into its own family's next step until the tile is inside the budget. `verify()` refuses to write a sheet that
breaks any of the three rules.

Outputs
  assets/tiles/quay_v2/quay_v2_tiles.png   the sheet, 16 columns, tile i at column i % 16, row i // 16
  game/sprites_src/env/quay/quay_v2_tiles.png  the same bytes, the copy the art mirror reads
  data/tile_classes_quay_v2.json           per glyph: index, name, solid, walkable, trigger, plane
  output/level_pass_2026-10-27/v2/tile_sheet.png   labelled sheet (3x) for a human to look at
Usage: python tools/make_quay_tiles.py            (deterministic; --check compares the committed sheet)
"""
from __future__ import annotations

import io
import json
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEET = os.path.join(ROOT, "assets", "tiles", "quay_v2", "quay_v2_tiles.png")
COPY = os.path.join(ROOT, "game", "sprites_src", "env", "quay", "quay_v2_tiles.png")
CLASSES = os.path.join(ROOT, "data", "tile_classes_quay_v2.json")
NES_PALETTE = os.path.join(ROOT, "data", "nes_palette.json")
LABELLED = os.path.join(ROOT, "output", "level_pass_2026-10-27", "v2", "tile_sheet.png")
COLUMNS = 16
T = 16
# One attribute cell is 16 x 16, one background palette is three entries plus the one shared backdrop, so the audit's
# per area budget is 3 besides that backdrop. 25 is tools/nes_check.py's MAX_COLOURS_ON_SCREEN.
PER_AREA_COLOURS = 3
MAX_SHEET_COLOURS = 25
BACKDROP = "ink"

# role -> the 2C02 output it is drawn in. The 2C02 is the authority (data/nes_palette.json), so the semantic colour
# each painter wants is resolved here to one real PPU entry, and the comment says which entry and why.
C = {
    # $0F #000000: the shared backdrop of every area, and the outline every form carries.
    "ink": (0x00, 0x00, 0x00),
    # stone ground family. The 2C02 has only two neutral mid greys plus black, so stone is three values: $10 lit
    # slab, $00 the wet face, $0C the cool dark that reads as the shadow in a joint.
    "s1": (0xbc, 0xbc, 0xbc), "s2": (0x7c, 0x7c, 0x7c), "s3": (0x00, 0x40, 0x58),
    "s4": (0x00, 0x00, 0x00), "s5": (0x00, 0x00, 0x00),
    # roofs: A rust ($26 lit / $16 face / $06 shade), B slate ($22 / $12 / $02).
    "ra1": (0xf8, 0x78, 0x58), "ra2": (0xf8, 0x38, 0x00), "ra3": (0xa8, 0x10, 0x00),
    "rb1": (0x68, 0x88, 0xfc), "rb2": (0x00, 0x58, 0xf8), "rb3": (0x00, 0x00, 0xbc),
    # walls: warm plaster, one family, $36 cream / $38 sand / $18 tan / $08 umber.
    "w1": (0xf0, 0xd0, 0xb0), "w2": (0xf8, 0xd8, 0x78), "w3": (0xac, 0x7c, 0x00), "w4": (0x50, 0x30, 0x00),
    # water family: $31 pale swell / $11 harbour blue / $0C deep / black trough, $20 white foam.
    "a1": (0xa4, 0xe4, 0xfc), "a2": (0x00, 0x78, 0xf8), "a3": (0x00, 0x40, 0x58), "a4": (0x00, 0x00, 0x00),
    "foam": (0xf8, 0xf8, 0xf8),
    # timber ($18 plank / $07 cut / $08 shade) and iron (the two neutral greys).
    "t1": (0xac, 0x7c, 0x00), "t2": (0x88, 0x14, 0x00), "t3": (0x50, 0x30, 0x00),
    "i1": (0xbc, 0xbc, 0xbc), "i2": (0x7c, 0x7c, 0x7c),
    # accent (reserved: doors, signs, steps, tickets, gangway): $27 orange, $17 burnt.
    "ac": (0xfc, 0xa0, 0x44), "ac2": (0xe4, 0x5c, 0x10),
    # window glow: $37 pale warm, $38 the hotter core.
    "glow": (0xfc, 0xe0, 0xa8), "glow2": (0xf8, 0xd8, 0x78),
    # trees: the teal end of the water family, $1C / $0A / $0B.
    "g1": (0x00, 0x88, 0x88), "g2": (0x00, 0x68, 0x00), "g3": (0x00, 0x58, 0x00),
}

# Where a role goes when its tile is over the per area budget. Each step stays inside the same family and lands on the
# material's next darker tone, so a fold costs a shading step and never turns stone into timber. Every chain ends at
# the backdrop, which is what makes a 4th or 5th colour impossible rather than merely unlikely.
FALLBACK = {
    "s1": "s2", "s2": "s3", "s3": "s4", "s4": "s5", "s5": "ink",
    "ra1": "ra2", "ra2": "ra3", "ra3": "ink",
    "rb1": "rb2", "rb2": "rb3", "rb3": "ink",
    "w1": "w2", "w2": "w3", "w3": "w4", "w4": "ink",
    "a1": "a2", "a2": "a3", "a3": "a4", "a4": "ink", "foam": "a1",
    "t1": "t2", "t2": "t3", "t3": "ink",
    "i1": "i2", "i2": "ink",
    "ac": "ac2", "ac2": "ink",
    "glow": "glow2", "glow2": "w2",
    "g1": "g2", "g2": "g3", "g3": "ink",
    "ink": "ink",
}


def h(x, y, salt=0):
    return ((x * 73856093) ^ (y * 19349663) ^ (salt * 83492791)) % 100


class Tile:
    def __init__(self, bg=None):
        self.im = Image.new("RGBA", (T, T), (0, 0, 0, 0))
        # The role grid, not the pixels, is the drawing: a fold rewrites roles and then repaints, so the sheet is
        # always exactly the roles the painters asked for after the area budget was applied.
        self.roles = [[None] * T for _ in range(T)]
        if bg:
            self.rect(0, 0, 15, 15, bg)

    def px(self, x, y, c):
        if 0 <= x < T and 0 <= y < T:
            self.roles[y][x] = c
            self.im.putpixel((x, y), C[c] + (255,))

    def repaint(self):
        """Redraw the pixels from the role grid."""
        for y in range(T):
            for x in range(T):
                c = self.roles[y][x]
                self.im.putpixel((x, y), (0, 0, 0, 0) if c is None else C[c] + (255,))

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c)

    def hline(self, x0, x1, y, c):
        self.rect(x0, y, x1, y, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, y0, x, y1, c)

    def box(self, x0, y0, x1, y1, fill, line="ink"):
        self.rect(x0, y0, x1, y1, line)
        self.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill)


# ---------------------------------------------------------------------------------------------------------------------
# painters, one per tile

def paving(seed, light=True):
    t = Tile("s1" if light else "s2")
    for y in range(T):
        for x in range(T):
            if y % 8 == 0 or x % 8 == (0 if (y // 8) % 2 == 0 else 4):
                t.px(x, y, "s2" if light else "s3")
    for i in range(5):
        t.px(h(i, seed, 1) % 15, h(seed, i, 2) % 15, "s3" if light else "s4")
    return t


def paving_drain():
    t = paving(7)
    t.rect(5, 5, 10, 10, "s4")
    for x in (6, 8, 10 - 1):
        t.vline(x, 6, 9, "s5")
    return t


def ground():
    t = Tile("s3")
    for i in range(14):
        t.px(h(i, 3, 5) % 16, h(i, 9, 6) % 16, "s4")
    for i in range(6):
        t.px(h(i, 4, 7) % 16, h(i, 8, 8) % 16, "s2")
    return t


def roof(kind, ridge):
    a = ("ra1", "ra2", "ra3") if kind == "A" else ("rb1", "rb2", "rb3")
    t = Tile(a[1])
    if ridge:
        t.rect(0, 0, 15, 5, a[0])
        t.hline(0, 15, 6, a[2])
        t.hline(0, 15, 7, "ink")
        for x in range(0, 16, 4):
            t.vline(x + 1, 8, 15, a[2])
        t.hline(0, 15, 12, a[2])
        t.hline(0, 15, 15, a[2])
        t.hline(0, 15, 0, a[1])
    else:
        t.rect(0, 0, 15, 15, a[1])
        t.hline(0, 15, 0, a[0])
        for r, off in ((4, 0), (9, 4)):
            t.hline(0, 15, r, a[2])
            for x in range(off, 16, 8):
                t.vline(x, r - 4 if r > 4 else 0, r, a[2])
        t.hline(0, 15, 14, a[2])
        t.hline(0, 15, 15, "ink")
    return t


def chimney(kind):
    t = roof(kind, True)
    t.rect(5, 0, 10, 8, "t3")
    t.rect(6, 1, 9, 7, "w4")
    t.hline(5, 10, 0, "ink")
    t.hline(6, 9, 3, "t3")
    t.hline(6, 9, 6, "t3")
    return t


def wall(variant=0):
    t = Tile("w1")
    for y in range(T):
        t.px(0, y, "w2")
    t.hline(0, 15, 15, "w3")
    t.hline(0, 15, 14, "w2")
    for x in range(1, 16, 5):
        t.px(x + h(x, variant, 3) % 3, 4 + variant, "w2")
        t.px(x + 2, 9, "w2")
    if variant == 1:  # vertical boards
        for x in range(0, 16, 4):
            t.vline(x, 0, 13, "w3")
        t.rect(0, 0, 15, 0, "w2")
    return t


def pilaster():
    t = wall(0)
    t.rect(5, 0, 10, 15, "w3")
    t.rect(6, 0, 9, 15, "w2")
    t.vline(10, 0, 15, "w4")
    return t


def window(lit=True):
    t = wall(0)
    t.rect(3, 2, 12, 12, "ink")
    t.rect(4, 3, 11, 11, "glow" if lit else "i2")
    t.vline(7, 3, 11, "w4")
    t.vline(8, 3, 11, "w4")
    t.hline(4, 11, 7, "w4")
    t.rect(4, 3, 6, 5, "glow2" if lit else "i1") if False else None
    t.hline(2, 13, 13, "w3")
    return t


def door():
    t = wall(0)
    t.rect(3, 0, 12, 15, "ink")
    t.rect(4, 1, 11, 15, "ac")
    t.rect(4, 1, 5, 15, "ac2")
    t.hline(4, 11, 1, "ac2")
    t.rect(7, 4, 10, 8, "ac2")
    t.px(9, 11, "ink")
    t.px(10, 11, "glow")
    return t


def sign():
    t = wall(0)
    t.rect(2, 3, 13, 12, "ink")
    t.rect(3, 4, 12, 11, "ac")
    t.hline(3, 12, 4, "glow")
    for x in (5, 7, 9, 11):
        t.vline(x, 6, 9, "ink")
    t.hline(5, 11, 7, "ink") if False else None
    return t


def awning():
    t = Tile("w2")
    for x in range(T):
        c = "ra1" if (x // 4) % 2 == 0 else "w1"
        t.rect(x, 0, x, 9, c)
    t.hline(0, 15, 9, "ink")
    for x in range(0, 16, 4):
        t.rect(x, 10, x + 1, 11, "ra1" if (x // 4) % 2 == 0 else "w1")
        t.hline(x, x + 1, 12, "ink")
    t.hline(0, 15, 13, "w3")
    t.hline(0, 15, 14, "w4")
    return t


def gable():
    t = wall(0)
    t.rect(2, 1, 13, 14, "ink")
    t.rect(3, 2, 12, 13, "w1")
    for (x, y) in ((4, 3), (11, 3), (4, 12), (11, 12)):
        t.px(x, y, "w3")
    t.rect(5, 4, 10, 11, "ink")
    t.rect(6, 5, 9, 10, "glow")
    t.vline(7, 5, 10, "ink")
    t.hline(6, 9, 7, "ink")
    return t


def ticket():
    t = wall(0)
    t.rect(2, 3, 13, 12, "ink")
    t.rect(3, 4, 12, 11, "glow")
    t.hline(3, 12, 9, "ac")
    t.hline(3, 12, 10, "ac2")
    t.vline(7, 4, 8, "ink")
    return t


def finial():
    t = roof("A", True)
    t.rect(7, 0, 8, 6, "w1")
    t.rect(5, 2, 10, 3, "w1")
    t.vline(6, 0, 6, "ink") if False else None
    return t


def band():
    t = wall(0)
    t.rect(0, 3, 15, 12, "ra1")
    t.hline(0, 15, 3, "ra2")
    t.hline(0, 15, 12, "ra3")
    t.rect(0, 6, 15, 8, "w1")
    return t


def coping():
    t = Tile("s1")
    t.hline(0, 15, 0, "s2")
    t.rect(0, 9, 15, 15, "s3")
    t.hline(0, 15, 9, "s2")
    t.hline(0, 15, 15, "ink")
    for x in range(0, 16, 8):
        t.vline(x + 3, 10, 14, "s4")
    t.hline(0, 15, 8, "s2")
    return t


def quay_face():
    t = Tile("s4")
    for y in range(0, 16, 5):
        t.hline(0, 15, y, "s5")
        for x in range(((y // 5) % 2) * 4, 16, 8):
            t.vline(x, y, y + 4, "s5")
    t.rect(0, 12, 15, 15, "a3")
    t.hline(0, 15, 12, "foam")
    for x in range(0, 16, 4):
        t.px(x + 1, 13, "a1")
    return t


def water(frame):
    base = ("a2", "a3", "a4")[frame % 3]
    t = Tile(base)
    hi = ("a1", "a2", "a3")[frame % 3]
    for x in range(T):
        for y in range(T):
            if (x + 2 * y + frame * 3) % 11 == 0 and h(x, y, 9) % 3 == 0:
                t.px(x, y, hi)
    return t


def foam_water():
    t = water(0)
    for x in range(T):
        t.px(x, 0, "foam")
        if x % 3 != 0:
            t.px(x, 1, "foam")
    return t


def plank(dark):
    t = Tile("t1" if not dark else "t2")
    t.hline(0, 15, 0, "t3")
    t.hline(0, 15, 15, "t3")
    for x in (2, 9):
        t.px(x, 3, "t3")
        t.px(x + 4, 11, "t3")
    t.vline(0, 0, 15, "t3")
    t.vline(15, 0, 15, "t3")
    return t


def rail_post():
    t = water(1)
    t.rect(6, 0, 9, 15, "ink")
    t.rect(7, 0, 8, 15, "i1")
    t.hline(6, 9, 0, "i2")
    return t


def bollard():
    t = paving(3)
    t.rect(4, 4, 11, 13, "ink")
    t.rect(5, 5, 10, 12, "i2")
    t.rect(5, 5, 6, 12, "i1")
    t.rect(3, 3, 12, 5, "ink")
    t.rect(4, 4, 11, 4, "i1")
    return t


def step(n):
    c = ("ac", "ac2", "t3")[n]
    t = Tile("s3")
    t.rect(0, 2, 15, 13, "ink")
    t.rect(0, 3, 15, 12, c)
    t.hline(0, 15, 3, "glow" if n == 0 else c)
    return t


def lamp_head():
    t = paving(5)
    t.rect(5, 1, 10, 9, "ink")
    t.rect(6, 2, 9, 8, "glow")
    t.rect(6, 2, 7, 4, "foam")
    t.rect(4, 0, 11, 1, "ink")
    t.rect(7, 9, 8, 15, "ink")
    return t


def lamp_pole():
    t = paving(5)
    t.rect(6, 0, 9, 15, "ink")
    t.rect(7, 0, 8, 12, "i1")
    t.rect(4, 12, 11, 15, "ink")
    t.rect(5, 13, 10, 14, "i2")
    return t


def bench():
    t = paving(9)
    t.rect(1, 6, 14, 10, "ink")
    t.rect(2, 7, 13, 9, "t1")
    t.hline(2, 13, 7, "t1")
    t.rect(1, 3, 14, 4, "ink")
    t.rect(2, 3, 13, 3, "t1")
    t.rect(2, 11, 3, 14, "ink")
    t.rect(12, 11, 13, 14, "ink")
    return t


def counter():
    t = Tile("t2")
    t.rect(0, 0, 15, 15, "ink")
    t.rect(1, 1, 14, 14, "t1")
    t.hline(1, 14, 1, "w1")
    t.hline(1, 14, 2, "t2")
    t.rect(3, 6, 5, 9, "ra1")
    t.rect(7, 6, 9, 9, "glow2")
    t.rect(11, 6, 13, 9, "g1")
    t.hline(1, 14, 12, "t3")
    return t


def crate():
    t = paving(11)
    t.rect(1, 2, 14, 14, "ink")
    t.rect(2, 3, 13, 13, "t1")
    t.rect(2, 3, 13, 4, "w2")
    for d in range(2, 13):
        t.px(2 + (d - 2) * 11 // 11, 3 + (d - 2) * 10 // 11, "t3")
    t.hline(2, 13, 8, "t3")
    return t


def barrel():
    t = paving(13)
    t.rect(3, 1, 12, 14, "ink")
    t.rect(4, 2, 11, 13, "t2")
    t.rect(4, 2, 6, 13, "t1")
    t.hline(4, 11, 5, "i2")
    t.hline(4, 11, 10, "i2")
    t.hline(4, 11, 2, "t3")
    return t


def container(side):
    t = Tile("rb2")
    t.rect(0, 1, 15, 14, "ink")
    t.rect(0, 2, 15, 13, "rb2" if side != 1 else "g2")
    for x in range(1 + side, 16, 3):
        t.vline(x, 3, 12, "rb3" if side != 1 else "g3")
    t.hline(0, 15, 2, "rb1" if side != 1 else "g1")
    return t


def tarp():
    t = paving(15)
    t.rect(1, 3, 14, 13, "ink")
    t.rect(2, 4, 13, 12, "g2")
    t.hline(3, 12, 6, "g3")
    t.hline(4, 11, 9, "g3")
    t.rect(3, 5, 6, 5, "g1")
    return t


def fence_rail():
    t = ground()
    t.rect(0, 5, 15, 8, "ink")
    t.rect(0, 6, 15, 7, "t1")
    t.hline(0, 15, 6, "w2")
    t.rect(0, 11, 15, 12, "ink")
    t.hline(0, 15, 11, "t1") if False else None
    return t


def fence_post():
    t = ground()
    t.rect(5, 1, 10, 15, "ink")
    t.rect(6, 2, 9, 14, "t1")
    t.vline(6, 2, 14, "w2")
    t.rect(5, 0, 10, 1, "ink")
    t.rect(0, 5, 15, 8, "ink")
    t.rect(0, 6, 15, 7, "t2")
    t.rect(6, 5, 9, 8, "t1")
    return t


def tree(var):
    t = ground()
    t.rect(6, 11, 9, 15, "ink")
    t.rect(7, 11, 8, 15, "t2")
    cx = (8, 7, 9)[var % 3]
    for y in range(0, 13):
        for x in range(16):
            dx, dy = x - cx, y - 6
            if dx * dx / 55.0 + dy * dy / 33.0 <= 1.0:
                t.px(x, y, "g2")
            if dx * dx / 45.0 + dy * dy / 24.0 <= 1.0 and (x + y) % 5 != 0:
                t.px(x, y, "g1" if (x + y * 2 + var) % 4 else "g2")
    for y in range(0, 13):
        for x in range(16):
            dx, dy = x - cx, y - 6
            d = dx * dx / 55.0 + dy * dy / 33.0
            if 0.82 <= d <= 1.0:
                t.px(x, y, "g3")
    return t


def centrepiece():
    t = paving(17)
    t.rect(2, 12, 13, 15, "ink")
    t.rect(3, 12, 12, 14, "s2")
    t.rect(5, 8, 10, 11, "ink")
    t.rect(6, 8, 9, 11, "s3")
    t.rect(6, 1, 9, 8, "ink")
    t.rect(7, 2, 8, 7, "i1")
    t.rect(4, 3, 11, 4, "ink")
    t.rect(5, 3, 10, 3, "i1")
    return t


def hull(kind):
    t = water(0)
    t.rect(0, 2, 15, 12, "ink")
    t.rect(0, 3, 15, 11, "rb3")
    t.hline(0, 15, 3, "rb2")
    t.rect(0, 9, 15, 11, "ra3")
    t.hline(0, 15, 8, "ink")
    for x in range(2, 15, 4):
        t.px(x, 6, "glow2")
    t.hline(0, 15, 13, "foam")
    return t


def bow():
    t = water(0)
    for y in range(2, 13):
        w = 15 - max(0, (y - 5)) * 2 if y > 5 else 15
        w = max(5, 15 - (abs(y - 6)) * 2)
        t.rect(0, y, w, y, "ink")
        if y > 2 and y < 12:
            t.rect(0, y, max(0, w - 1), y, "rb3")
    t.hline(0, 12, 13, "foam")
    return t


def deck():
    t = Tile("t2")
    t.rect(0, 0, 15, 15, "t2")
    t.hline(0, 15, 0, "ink")
    for y in (4, 8, 12):
        t.hline(0, 15, y, "t3")
    for x in (3, 11):
        t.px(x, 2, "t3")
        t.px(x + 2, 6, "t3")
    return t


def cabin():
    t = deck()
    t.rect(1, 1, 14, 14, "ink")
    t.rect(2, 2, 13, 13, "w2")
    t.rect(3, 4, 6, 8, "ink")
    t.rect(4, 5, 5, 7, "glow")
    t.rect(9, 4, 12, 8, "ink")
    t.rect(10, 5, 11, 7, "glow")
    t.hline(2, 13, 11, "w3")
    return t


def mast():
    t = water(2)
    t.rect(7, 0, 8, 15, "ink")
    t.vline(7, 0, 15, "t1")
    t.rect(3, 4, 12, 5, "ink")
    t.hline(4, 11, 4, "t1")
    return t


def funnel():
    t = deck()
    t.rect(4, 0, 11, 14, "ink")
    t.rect(5, 1, 10, 13, "ra2")
    t.rect(5, 1, 6, 13, "ra1")
    t.hline(5, 10, 5, "w1")
    t.hline(5, 10, 6, "w1")
    return t


def gangway():
    t = Tile("ac")
    t.rect(0, 0, 15, 15, "ac")
    for y in range(1, 16, 3):
        t.hline(0, 15, y, "ac2")
    t.vline(0, 0, 15, "ink")
    t.vline(15, 0, 15, "ink")
    t.vline(1, 0, 15, "i1")
    t.vline(14, 0, 15, "i1")
    return t


def crane_mast():
    t = paving(21)
    t.rect(5, 0, 10, 15, "ink")
    t.rect(6, 0, 9, 15, "ra2")
    for y in range(0, 16, 4):
        t.hline(6, 9, y, "ra3")
        t.px(7 + (y // 4) % 2, y + 2, "ra1")
    return t


def crane_jib():
    t = Tile()
    t.rect(0, 3, 15, 6, "ink")
    t.rect(0, 4, 15, 5, "ra2")
    for x in range(0, 16, 4):
        t.px(x, 4, "ra1")
        t.px(x + 2, 5, "ra3")
    return t


def crane_hook():
    t = Tile()
    t.rect(0, 3, 9, 6, "ink")
    t.rect(0, 4, 9, 5, "ra2")
    t.vline(10, 4, 11, "ink")
    t.rect(8, 11, 12, 13, "ink")
    t.rect(9, 12, 11, 12, "i1")
    return t


def crane_base():
    t = paving(23)
    t.rect(0, 0, 15, 15, "ink")
    t.rect(1, 1, 14, 14, "ra2")
    t.rect(1, 1, 14, 3, "ra1")
    t.hline(1, 14, 8, "ra3")
    t.rect(4, 5, 11, 7, "ink")
    t.rect(5, 6, 10, 6, "glow2")
    return t


def lighthouse_gallery():
    t = paving(25)
    t.rect(2, 10, 13, 12, "ink")
    t.rect(3, 11, 12, 11, "i1")
    t.rect(5, 2, 10, 9, "ink")
    t.rect(6, 3, 9, 8, "glow")
    return t


# glyph -> (name, painter, solid, walkable, trigger, plane)
def table():
    g = []

    def add(ch, name, painter, solid, walkable, trigger=False, plane="ground"):
        g.append((ch, name, painter, solid, walkable, trigger, plane))

    # buildings (roof A rust, roof B slate)
    add("^", "roof_ridge_a", lambda: roof("A", True), True, False)
    add("r", "roof_eave_a", lambda: roof("A", False), True, False)
    add("Q", "roof_ridge_b", lambda: roof("B", True), True, False)
    add("q", "roof_eave_b", lambda: roof("B", False), True, False)
    add("C", "chimney_a", lambda: chimney("A"), True, False)
    add("E", "chimney_b", lambda: chimney("B"), True, False)
    add("W", "wall", lambda: wall(0), True, False)
    add("V", "wall_boards", lambda: wall(1), True, False)
    add("P", "pilaster", pilaster, True, False)
    add("w", "window_lit", lambda: window(True), True, False)
    add("x", "window_dark", lambda: window(False), True, False)
    add("D", "door", door, False, True, True, "props")
    add("S", "sign_board", sign, True, False, False, "above")
    add("A", "awning", awning, True, False)
    add("G", "gable_clock", gable, True, False)
    add("t", "ticket_window", ticket, True, False)
    add("+", "finial", finial, True, False)
    add("k", "band_stripe", band, True, False)
    # ground
    add(".", "open_ground", ground, False, True)
    add(":", "paving", lambda: paving(1), False, True)
    add(",", "paving_alt", lambda: paving(2, False), False, True)
    add(";", "paving_drain", paving_drain, False, True)
    add("T", "tree_canopy_a", lambda: tree(0), True, False, False, "above")
    add("Y", "tree_canopy_b", lambda: tree(1), True, False, False, "above")
    add("Z", "tree_canopy_c", lambda: tree(2), True, False, False, "above")
    add("f", "fence_rail", fence_rail, True, False)
    add("F", "fence_post", fence_post, True, False)
    add("*", "plaza_centrepiece", centrepiece, True, False)
    # water side
    add("~", "water_mid", lambda: water(0), True, False)
    add("_", "water_deep", lambda: water(1), True, False)
    add("-", "water_foam", foam_water, True, False)
    add("=", "coping", coping, False, True)
    add("#", "quay_wall_face", quay_face, True, False)
    add("p", "pier_plank_light", lambda: plank(False), False, True)
    add("j", "pier_plank_dark", lambda: plank(True), False, True)
    add("b", "bollard", bollard, True, False, False, "props")
    add("s", "step_light", lambda: step(0), False, True)
    add("e", "step_mid", lambda: step(1), False, True)
    add("u", "step_dark", lambda: step(2), False, True)
    add("|", "pier_rail", rail_post, True, False)
    add("L", "lamp_head", lamp_head, True, False, False, "above")
    add("l", "lamp_pole", lamp_pole, True, False)
    add("h", "bench", bench, True, False, False, "props")
    add("v", "market_counter", counter, True, False, False, "props")
    # cargo
    add("o", "crate", crate, True, False, False, "props")
    add("O", "barrel", barrel, True, False, False, "props")
    add("X", "container_blue", lambda: container(0), True, False, False, "props")
    add("I", "container_green", lambda: container(1), True, False, False, "props")
    add("n", "tarp_pile", tarp, True, False, False, "props")
    # vessels
    add("H", "hull", lambda: hull(0), True, False)
    add("d", "deck_plank", deck, True, False)
    add("c", "cabin", cabin, True, False)
    add("m", "mast", mast, True, False)
    add("N", "funnel", funnel, True, False)
    add(">", "bow", bow, True, False)
    add("g", "gangway", gangway, False, True, False, "props")
    # crane and lighthouse
    add("M", "crane_mast", crane_mast, True, False)
    add("J", "crane_jib", crane_jib, False, False, False, "above")
    add("U", "crane_hook", crane_hook, False, False, False, "above")
    add("K", "crane_base", crane_base, True, False)
    add("Λ", "lighthouse_gallery", lighthouse_gallery, True, False)
    return g


def legalise(t):
    """Fold the least used tone into its family's next step until the area is inside PER_AREA_COLOURS.

    A 16 x 16 attribute area is one background palette: the shared backdrop plus three entries. A painter that names
    four materials in one tile (a roof over a timber joint, a lit window in a plastered wall) is asking for more than
    the PPU gives, so the tone with the fewest pixels goes to FALLBACK[role] and the tile is recounted. The fold is by
    pixel count with the role name as the tie break, so the same painters always produce the same sheet.
    """
    while True:
        counts = {}
        for row in t.roles:
            for c in row:
                if c is None or c == BACKDROP:
                    continue
                counts[c] = counts.get(c, 0) + 1
        if len(counts) <= PER_AREA_COLOURS:
            break
        role = min(counts, key=lambda name: (counts[name], name))
        target = FALLBACK[role]
        for row in t.roles:
            for x in range(T):
                if row[x] == role:
                    row[x] = target
    t.repaint()
    return t


def allowed_colours():
    """Every usable 2C02 output, read from data/nes_palette.json (the same file the audit measures against)."""
    with io.open(NES_PALETTE, "r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    out = set()
    for entry in payload["entries"]:
        if not entry.get("usable", True):
            continue
        text = entry["hex"].lstrip("#")
        out.add((int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)))
    return out


def verify(sheet):
    """Refuse to write a sheet that breaks the palette, the per area budget or the colour count. Returns problems."""
    allowed = allowed_colours()
    backdrop = C[BACKDROP]
    problems = []
    seen = set()
    pixels = sheet.load()
    for y in range(sheet.height):
        for x in range(sheet.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            seen.add((r, g, b))
            if (r, g, b) not in allowed:
                problems.append("pixel %d,%d is #%02x%02x%02x, not a 2C02 output" % (x, y, r, g, b))
    if len(seen) > MAX_SHEET_COLOURS:
        problems.append("the sheet spends %d colours, the cap is %d" % (len(seen), MAX_SHEET_COLOURS))
    for ty in range(0, sheet.height, T):
        for tx in range(0, sheet.width, T):
            cell = set()
            for y in range(ty, ty + T):
                for x in range(tx, tx + T):
                    r, g, b, a = pixels[x, y]
                    if a and (r, g, b) != backdrop:
                        cell.add((r, g, b))
            if len(cell) > PER_AREA_COLOURS:
                problems.append("area %d,%d carries %d colours besides the backdrop: %s"
                                % (tx, ty, len(cell), sorted("#%02x%02x%02x" % rgb for rgb in cell)))
    return problems


def build():
    g = table()
    rows = (len(g) + COLUMNS - 1) // COLUMNS
    sheet = Image.new("RGBA", (COLUMNS * T, rows * T), (0, 0, 0, 0))
    classes = {}
    tiles = []
    for i, (ch, name, painter, solid, walkable, trigger, plane) in enumerate(g):
        t = legalise(painter())
        tiles.append((ch, name, t.im))
        sheet.paste(t.im, ((i % COLUMNS) * T, (i // COLUMNS) * T))
        classes[ch] = {"index": i, "name": name, "solid": solid, "walkable": walkable, "trigger": trigger,
                       "plane": plane}
    return sheet, classes, tiles


def labelled(tiles):
    scale = 3
    cols = 8
    cw, chh = T * scale + 36, T * scale + 26
    rows = (len(tiles) + cols - 1) // cols
    im = Image.new("RGB", (cols * cw, rows * chh), (36, 36, 44))
    d = ImageDraw.Draw(im)
    for i, (ch, name, t) in enumerate(tiles):
        x, y = (i % cols) * cw + 18, (i // cols) * chh + 4
        bg = Image.new("RGBA", (T, T), (92, 92, 110, 255))
        bg.alpha_composite(t)
        im.paste(bg.resize((T * scale, T * scale), Image.NEAREST).convert("RGB"), (x, y))
        d.text((x - 12, y + 18), ch if ch.isascii() else "Lh", fill=(255, 255, 255))
        d.text((x - 14, y + T * scale + 3), name[:15], fill=(200, 200, 210))
    return im


def main():
    sheet, classes, tiles = build()
    problems = verify(sheet)
    if "--check" in sys.argv:
        stale = []
        for path in (SHEET, COPY):
            if not os.path.isfile(path):
                stale.append("%s is missing" % os.path.relpath(path, ROOT))
                continue
            old = Image.open(path).convert("RGBA")
            if old.size != sheet.size or list(old.getdata()) != list(sheet.getdata()):
                stale.append("%s DIFFERS" % os.path.relpath(path, ROOT).replace(os.sep, "/"))
        if problems:
            for problem in problems:
                print("make_quay_tiles: " + problem)
        print("make_quay_tiles: %s" % ("; ".join(stale) if stale else "both committed sheets match"))
        return 1 if (stale or problems) else 0
    if problems:
        for problem in problems:
            print("make_quay_tiles: REFUSED " + problem)
        return 1
    for p in (SHEET, COPY, CLASSES, LABELLED):
        os.makedirs(os.path.dirname(p), exist_ok=True)
    sheet.save(SHEET)
    sheet.save(COPY)
    with io.open(CLASSES, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"format": 1, "kind": "tile_classes", "name": "quay_v2", "sheet": "assets/tiles/quay_v2/quay_v2_tiles.png",
                   "columns": COLUMNS, "tile_size": T, "classes": classes}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    labelled(tiles).save(LABELLED)
    print("make_quay_tiles: %d tiles, %d colours, every area inside %d besides the backdrop"
          % (len(tiles), len({(r, g, b) for r, g, b, a in sheet.getdata() if a}), PER_AREA_COLOURS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
