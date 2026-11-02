#!/usr/bin/env python3
"""make_quay_tiles.py: the exterior tile set for the quay block and the dock office (card R46, t_abfb6024),
redrawn in art direction B, late NES polish (card ART-B-MAPS, t_d0566ebc).

What this draws, and to which rules:

1. Twenty 16x16 tiles that read as a south coast quay, plus the office floor and desk the interior scene stands
   on: wet quay paving, a puddle, the quay edge, two water frames, a glint path, an iron bollard, a chain, a
   steel barrier, a brick wall, a damp brick wall, the one door that opens, a shut door, a lit window, a dark
   window, a lamp post, a sign board, office boards and an office desk.
2. Style B, as Nayil picked it on 2026-10-26 19:00: bold dark outlines, three tone shading lit from the top
   left, detailed tiles. The reference for line weight, shading and palette use is the B frame of
   `tools/art/make_art_target.py`, `output/art_target/frame_B_256x240.png`. Three rules are applied to every
   drawn form, mechanically, so the look is a property of the code and not of a mood:
     outline   a 1 px ring of the shared backdrop black, so a form has a bold dark edge against its ground
     ramp      the first row and column inside the outline is the light role, the last row and column the shadow
     detail    a second layer of marks (joints, rivets, links, knots, rain, hot cores) so a repeated tile reads
3. Every pixel is an output of the Ricoh 2C02. Each tile draws through one of the four background palettes,
   three colours per palette plus the shared backdrop $0F black, so no 16x16 area carries more than three
   colours besides the backdrop. `tools/nes_check.py` and `tools/nes_composite_check.py` measure that same
   budget, so the audit is the check and not the opinion.
4. Colours are named as ROLES, not hex. The role names are the ones in `data/palette.json` (`grey_4`, `sea_1`,
   `blood_3`, `gold_5` and so on). That file names a 54 colour design palette whose hex values are not 2C02
   outputs, so this tool carries the bridge: ROLE_ENTRY resolves each role to the PPU entry that reads as it,
   and the bridge is written into the manifest so a reader can audit the mapping instead of trusting it.
5. No anti aliasing: every pixel is a palette entry, drawn on the 16x16 cell, with no blended or intermediate
   tone anywhere. A background tile is a full cell: the tile edge is the tile edge.
6. The blob test of `knowledge/SPRITE-CRAFT.md` section 8.5 is applied per tile: the share of the lightest tone,
   the rows with no dark pixel, the horizontal dark runs, and the dark pixels inside the silhouette. The numbers
   are written into the manifest for every tile. Object tiles are gated on it; pattern tiles (paving, water,
   brick) and the three light source tiles (lit window, lamp, sign) are reported and their waivers are named,
   because the rule was written for a 14x15 character silhouette and a wall is structure by repetition.

Two sheets, one vocabulary. The HURRICANE variant of the same place is drawn from the same painters with the
storm flag: no bright glint on the stone, whitecaps instead of sparkle, wind bent chain, a leaning lamp, rain on
every outdoor tile. It keeps the same twenty characters, indices, palettes, planes and water animation, so the
map wiring needs no new character table: only a second sheet, and a room palette id that resolves to the quay's
set (see TILES.md, "How to wire the storm").

Outputs:
    game/sprites_src/env/quay/quay_tiles.png          the night sheet, 8 by 3 cells of 16x16, 20 tiles used
    game/sprites_src/env/quay/quay_tiles.json         its manifest: palettes, roles, tiles, blob numbers
    game/sprites_src/env/quay/TILES.md                the tile table the map wiring reads
    game/sprites_src/env/quay_storm/quay_storm_tiles.png    the hurricane sheet, same twenty tiles
    game/sprites_src/env/quay_storm/quay_storm_tiles.json   its manifest
    game/sprites_src/env/quay_storm/TILES.md                its table, and the one wiring line it needs
    output/quay_tiles_3x.png                          3x contact sheet to look at
    output/quay_storm_tiles_3x.png                    the same for the storm set
    output/quay_block_preview.png                     256x240 mock of the block, composed from the night sheet
    output/quay_block_preview.json                    its declared backdrop, so the frame audit reads it right
    output/quay_storm_block_preview.png               the same block under the storm set
    output/quay_storm_block_preview.json              its declared backdrop
    output/quay_office_preview.png                    the dock office, composed from the night sheet
    output/quay_office_preview.json                   its declared backdrop
    output/art_b/ART-B-MAPS/quay_before_after_3x.png  R46 night sheet on top, style B under it, labelled
    output/art_b/ART-B-MAPS/quay_storm_before_after_3x.png  the night block on top, the storm block under it

The art root is `game/sprites_src/env/`, where every tileset in this project lives and where
`tools/nes_audit_all.py` and `tools/sync_art.py` look.

Usage:
    python tools/art/make_quay_tiles.py
    python tools/art/make_quay_tiles.py --check        # write nothing, exit 1 if a PNG on disk is stale
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "game", "sprites_src", "env", "quay")
SHEET_PNG = os.path.join(OUT_DIR, "quay_tiles.png")
SHEET_JSON = os.path.join(OUT_DIR, "quay_tiles.json")
TILES_MD = os.path.join(OUT_DIR, "TILES.md")
STORM_DIR = os.path.join(ROOT, "game", "sprites_src", "env", "quay_storm")
STORM_PNG = os.path.join(STORM_DIR, "quay_storm_tiles.png")
STORM_JSON = os.path.join(STORM_DIR, "quay_storm_tiles.json")
STORM_MD = os.path.join(STORM_DIR, "TILES.md")
OUTPUT = os.path.join(ROOT, "output")
PAIR_DIR = os.path.join(OUTPUT, "art_b", "ART-B-MAPS")
BEFORE_DIR = os.path.join(PAIR_DIR, "before")

TILE = 16
COLUMNS = 8
BACKDROP_ROLE = "ink"

# -----------------------------------------------------------------------------------------------------------------
# The palette bridge: role name -> the 2C02 entry that reads as that role.
#
# data/palette.json names 54 design colours by hue family and level (grey_0 to blood_5) and by role (ink, window,
# accent). Its hex values are not 2C02 outputs, and the audit's authority on a colour is data/nes_palette.json, so
# each role this set uses is resolved here to one entry, chosen as the nearest output in the role's own family at
# the value the art needs. The reason column is why that entry and not another one.

ROLE_ENTRY = {
    "ink": (15, "the canonical black $0F, the shared backdrop of every area in both sets"),
    "grey_4": (0, "$00 #7c7c7c is the one neutral mid grey in the 2C02 and it is the wet quay stone"),
    "grey_5": (16, "$10 #bcbcbc is the lighter neutral, the sheen a wet slab keeps on its lit edge"),
    "sea_1": (12, "$0C #004058 is the darkest cool output, the wet shadow in a joint and the deep water"),
    "sea_2": (28, "$1C #008888 is the harbour's mid swell, one step above the deep water"),
    "sea_4": (44, "$2C #00e8d8 is the brightest teal, a two pixel glint on a swell and nothing more"),
    "blood_3": (7, "$07 #881400 is the dark brick face and the lit edge of iron after dark"),
    "stone_2": (8, "$08 #503000 is the brown one step under the brick, mortar and the iron body"),
    "blood_4": (23, "$17 #e45c10 is the brick face under the lamp and the paint on the barrier rail"),
    "gold_4": (40, "$28 #f8b800 is lamp glass and the lit window's fill"),
    "gold_5": (56, "$38 #f8d878 is the hot core of a window and the lettering on the sign"),
}

# The room palette sets this tool serves. Both sheets keep the same four background palettes, so the storm set
# spends exactly the roles the night set spends: the hurricane changes the drawing, not the budget. Each set is
# inside the 16 role cap of data/room_palettes.json.
SETS = {
    "quay_night": ["ink", "grey_4", "grey_5", "sea_1", "sea_2", "sea_4", "blood_3", "stone_2", "blood_4",
                   "gold_4", "gold_5"],
    "office_night": ["ink", "grey_4", "grey_5", "sea_1", "sea_2", "blood_3", "stone_2", "blood_4",
                     "gold_4", "gold_5"],
    "quay_storm": ["ink", "grey_4", "grey_5", "sea_1", "sea_2", "sea_4", "blood_3", "stone_2", "blood_4",
                   "gold_4", "gold_5"],
}

# The four background palettes of the quay set: three roles each, one shared backdrop. A tile draws from exactly
# one of them, so a 16x16 area can never carry a fourth colour. The same four are used by both sheets.
BG_PALETTES = [
    ("bg0_quay_stone", ["grey_4", "grey_5", "sea_1"],
     "wet paving, the coping and the iron that stands on the stone, drawn in the stone's own ramp"),
    ("bg1_harbour_water", ["sea_1", "sea_2", "sea_4"],
     "the harbour: deep water, one step of swell, a glint"),
    ("bg2_brick_iron", ["blood_3", "stone_2", "blood_4"],
     "the brick frontage, its mortar, and the doors and wood in the same warm ramp"),
    ("bg3_lamp_glass", ["gold_4", "gold_5", "stone_2"],
     "the light sources: a lit window, the lamp, the sign, with the dark brown that frames them"),
]

PALETTE_OF_ROLE = {}
for _name, _roles, _note in BG_PALETTES:
    for _role in _roles:
        PALETTE_OF_ROLE[_role] = _name


# -----------------------------------------------------------------------------------------------------------------
# A 16x16 canvas of role names. None is the backdrop.

class Canvas:
    def __init__(self):
        self.px = [[None] * TILE for _ in range(TILE)]

    def fill(self, role):
        for y in range(TILE):
            for x in range(TILE):
                self.px[y][x] = role

    def rect(self, x0, y0, w, h, role):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if 0 <= x < TILE and 0 <= y < TILE:
                    self.px[y][x] = role

    def put(self, x, y, role):
        if 0 <= x < TILE and 0 <= y < TILE:
            self.px[y][x] = role

    def hline(self, y, x0, x1, role):
        for x in range(x0, x1 + 1):
            self.put(x, y, role)

    def vline(self, x, y0, y1, role):
        for y in range(y0, y1 + 1):
            self.put(x, y, role)

    def rows(self):
        return self.px

    def remove_orphans(self, backdrop=BACKDROP_ROLE):
        """The removal half of the orphan rule: a pixel with no 8 neighbour of its own role takes the role most of
        its neighbours share, so a stray single dot joins the form it landed on instead of speckling it."""
        removed = 0
        for y in range(TILE):
            for x in range(TILE):
                here = self.px[y][x]
                if here is None or here == backdrop:
                    continue
                neighbours = []
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < TILE and 0 <= nx < TILE:
                            neighbours.append(self.px[ny][nx])
                if here in neighbours:
                    continue
                counts = {}
                for role in neighbours:
                    counts[role] = counts.get(role, 0) + 1
                best = max(counts, key=lambda role: (counts[role], role == backdrop))
                self.px[y][x] = best
                removed += 1
        return removed


# -----------------------------------------------------------------------------------------------------------------
# Style B: the two mechanical passes every form goes through, and the detail layer.

def ring(c, x0, y0, x1, y1, role=BACKDROP_ROLE):
    """A one pixel ring of the backdrop round a form: the bold dark outline of direction B."""
    for x in range(x0, x1 + 1):
        c.put(x, y0, role)
        c.put(x, y1, role)
    for y in range(y0, y1 + 1):
        c.put(x0, y, role)
        c.put(x1, y, role)


def solid_form(c, x0, y0, x1, y1, light, body, dark, outline=True):
    """A form with the B ramp: body fill, lit top and left, shadow bottom and right, black ring around it.

    The ramp is the mechanical part of direction B: the first pixel of a run is the rim light and the last is the
    shadow, so every form reads as lit from the top left without a per pixel decision.
    """
    c.rect(x0, y0, x1 - x0 + 1, y1 - y0 + 1, body)
    c.hline(y0, x0, x1, light)
    c.vline(x0, y0 + 1, y1, light)
    c.hline(y1, x0 + 1, x1, dark)
    c.vline(x1, y0 + 1, y1 - 1, dark)
    if outline:
        ring(c, x0 - 1, y0 - 1, x1 + 1, y1 + 1)


def rain(c, role):
    """Wind driven rain: 3 px dashes on a fixed lattice, wrapped so two copies of a tile still line up."""
    for (x, y) in ((1, 2), (6, 4), (11, 1), (3, 7), (9, 9), (14, 6), (0, 12), (5, 14), (12, 12), (7, 10)):
        c.put(x, y, role)
        c.put((x + 1) % TILE, (y + 1) % TILE, role)


# -----------------------------------------------------------------------------------------------------------------
# Grounds.

def paving(c, storm=False):
    """Wet flagstones on an 8 px lattice: a deep joint, a lit top and left edge, a shadow on the other two.

    The joint is the stone's own darkest tone over two pixels, not black: a black grid on a wall of stone reads
    as a cage at this size. The bold dark accent is kept where it earns its place, a black cross at each lattice
    corner, so the walk still reads as direction B and the block does not read as a wire frame.
    """
    body = "sea_1" if storm else "grey_4"
    light = "grey_4" if storm else "grey_5"
    if storm:
        # the storm paving is the calm slab gone dark: one black joint, a thin lit edge, rain in the stone tone
        c.fill(body)
        for y in (0, 8):
            c.hline(y, 0, 15, "ink")
        for x in (0, 8):
            c.vline(x, 0, 15, "ink")
        for y0 in (1, 9):
            for x0 in (1, 9):
                c.hline(y0, x0, x0 + 5, light)
                c.vline(x0, y0 + 1, y0 + 5, light)
                c.hline(y0 + 5, x0 + 1, x0 + 5, "ink")
        rain(c, "grey_4")
        return
    joint = "sea_1"
    c.fill(body)
    for y in (0, 1, 8, 9):
        c.hline(y, 0, 15, joint)
    for x in (0, 1, 8, 9):
        c.vline(x, 0, 15, joint)
    for y0 in (2, 10):
        for x0 in (2, 10):
            c.hline(y0, x0, x0 + 5, light)
            c.vline(x0, y0 + 1, y0 + 5, light)
            c.hline(y0 + 5, x0 + 1, x0 + 5, "sea_1")
            c.vline(x0 + 5, y0 + 1, y0 + 4, "sea_1")
    for (x, y) in ((0, 0), (8, 0), (0, 8), (8, 8)):
        c.put(x, y, "ink")
        c.put(x + 1, y, "ink")
        c.put(x, y + 1, "ink")
    if storm:
        rain(c, "grey_5")


def brick_course(c, top, joints, storm=False):
    """One 8 row course of brick: black mortar, a lit top edge on every brick, a dark shadow under it."""
    c.hline(top, 0, 15, "ink")
    c.rect(0, top + 1, 16, 6, "blood_3")
    c.hline(top + 1, 0, 15, "blood_4")
    c.hline(top + 6, 0, 15, "stone_2")
    for x in joints:
        c.vline(x, top + 1, top + 6, "stone_2")
    if storm:
        c.hline(top + 1, 5, 7, "blood_3")
        c.hline(top + 1, 12, 13, "blood_3")
        for x in (2, 10):
            c.vline(x, top + 2, top + 4, "stone_2")


# -----------------------------------------------------------------------------------------------------------------
# The twenty tiles. Each takes the storm flag: the same name, character, palette group and index, drawn for the
# hurricane instead of the calm night.

def t_quay_paving(c, storm=False):
    paving(c, storm)


def t_quay_paving_worn(c, storm=False):
    paving(c, storm)
    # a crack that steps one pixel at a time, the pattern the craft file asks for instead of a jaggy
    for (x, y) in ((3, 2), (4, 3), (4, 4), (5, 4), (5, 5), (6, 5), (6, 6), (7, 6)):
        c.put(x, y, "ink")
    c.put(13, 11, "ink")
    c.put(14, 11, "ink")
    c.put(13, 12, "ink")
    if storm:
        rain(c, "grey_5")


def t_quay_puddle(c, storm=False):
    paving(c, storm)
    # standing water in a low slab: a black lip, the water in the dark tone, one lit edge where the lamp reaches it
    ring(c, 2, 5, 13, 9)
    c.rect(3, 6, 10, 3, "sea_1")
    c.hline(6, 4, 11, "grey_4" if storm else "grey_5")
    if storm:
        for (x, y) in ((4, 7), (9, 8)):
            c.hline(y, x, x + 1, "grey_5")
    else:
        c.hline(8, 5, 6, "grey_5")
        c.hline(7, 10, 11, "grey_5")


def t_quay_edge(c, storm=False):
    """The coping stone at the water: paving above, a lit wet lip, a black drop, then the harbour."""
    paving(c, storm)
    c.hline(10, 0, 15, "ink")
    c.hline(11, 0, 15, "grey_4" if storm else "grey_5")
    c.hline(12, 0, 15, "grey_5" if storm else "grey_4")
    for x in (0, 8):
        c.vline(x, 11, 12, "sea_1")
    c.hline(13, 0, 15, "ink")
    c.rect(0, 14, 16, 2, "sea_1")
    for x in (3, 11):
        c.put(x, 15, "grey_4" if storm else "grey_5")


def water(c, phase, storm=False):
    """Harbour water: one swell line every six rows, a six pixel dash on a ten pixel pitch, a crest of two pixels.

    The lines run the width of the tile at a fixed pitch so a field of them reads as rows of swell rather than
    as speckle. The bright teal is a crest, not a highlight on every dash, because a glint on every dash turns a
    calm harbour into static.
    """
    c.fill("sea_1")
    offset = 0 if phase == 0 else 4
    for row_index, y in enumerate((2, 8, 14)):
        for x in range(offset, 16, 10):
            end = min(x + 5, 15)
            c.hline(y, x, end, "sea_2")
            if (row_index + phase) % 2 == 0 and end - x >= 4:
                c.hline(y, x + 2, x + 3, "sea_4")
    if storm:
        # whitecaps: two bold crests in the brightest teal, each with one step of chop under it, so the chop reads
        # as wind and not as more dashes
        for (x, y) in ((1, 5), (9, 11)):
            c.hline(y, x, min(x + 3, 15), "sea_4")
            c.hline(y + 1, x + 1, min(x + 3, 15), "sea_2")


def t_water_deep(c, storm=False):
    water(c, 0, storm)


def t_water_ripple(c, storm=False):
    water(c, 1, storm)


def t_water_reflection(c, storm=False):
    """What a lamp does to harbour water: a glint path that steps to the right as it falls, the way a point light
    breaks on a moving surface. Under the storm the path is gone and the water is pocked by rain instead."""
    c.fill("sea_1")
    if storm:
        for (x, y) in ((2, 2), (7, 4), (12, 6), (4, 9), (9, 11), (14, 13)):
            c.hline(y, x, min(x + 1, 15), "sea_2")
            c.hline(y - 1, x, min(x + 1, 15), "sea_4")
        return
    for step, y in enumerate((3, 6, 9, 12)):
        x0 = 6 - step
        c.hline(y, x0, x0 + 3, "sea_2")
        c.hline(y, x0 + 1, x0 + 2, "sea_4")


def t_bollard(c, storm=False):
    """An iron bollard on wet stone: a black outline, a lit left edge, a shadow on the right, a wide base."""
    paving(c, storm)
    solid_form(c, 3, 11, 12, 13, "grey_5", "grey_4", "sea_1")
    solid_form(c, 6, 3, 9, 10, "grey_5", "grey_4", "sea_1")
    solid_form(c, 5, 2, 10, 3, "grey_5", "grey_4", "sea_1")
    c.put(7, 2, "sea_1")
    c.put(8, 2, "sea_1")


def t_chain(c, storm=False):
    """A chain between two bollards: one arc four pixels thick, black on both sides, the ground showing through."""
    paving(c, storm)
    drape = ([5, 6, 7, 9, 10, 10, 11, 11, 11, 10, 10, 9, 7, 6, 5, 5] if storm
             else [6, 7, 7, 8, 8, 8, 9, 9, 9, 8, 8, 8, 7, 7, 6, 6])
    for x, y in enumerate(drape):
        c.put(x, y - 1, "ink")
        c.put(x, y, "grey_5")
        c.put(x, y + 1, "sea_1")
        c.put(x, y + 2, "ink")
    for x in (1, 4, 7, 10, 13):
        c.put(x, drape[x] + 1, "grey_4")
    if storm:
        rain(c, "grey_5")


def t_barrier(c, storm=False):
    """A steel barrier on the quay: a painted rail with a lit top, two out-lined posts, a black gap under it."""
    paving(c, storm)
    c.rect(0, 4, 16, 2, "grey_4")
    c.hline(4, 0, 15, "grey_5")
    c.hline(6, 0, 15, "ink")
    # a joint in the rail every eight pixels, so the rail is a run of sections and every row keeps a dark pixel
    for x in (0, 8):
        c.put(x, 4, "sea_1")
        c.put(x, 5, "sea_1")
    for x in (1, 9):
        c.put(x, 5, "grey_5")
    for x0 in (2, 12):
        solid_form(c, x0, 6, x0 + 1, 13, "grey_5", "grey_4", "sea_1")
    c.hline(14, 2, 3, "ink")
    c.hline(14, 12, 13, "ink")
    if storm:
        rain(c, "grey_5")


def t_brick_wall(c, storm=False):
    """The office frontage: two courses, black mortar, a lit top edge on every brick, a shadow under it."""
    brick_course(c, 0, (0, 8), storm)
    brick_course(c, 8, (4, 12), storm)


def t_brick_wall_damp(c, storm=False):
    t_brick_wall(c, storm)
    # damp: bricks gone dark where the rain runs, and one brick lost to the weather
    c.rect(2, 10, 2, 5, "stone_2")
    c.rect(3, 12, 1, 3, "stone_2")
    c.rect(10, 2, 2, 3, "stone_2")
    c.rect(12, 13, 2, 2, "ink")
    if storm:
        c.vline(6, 9, 14, "stone_2")
        c.vline(13, 2, 6, "stone_2")


def t_door_office(c, storm=False):
    """The one door in the block that opens: a lit stone frame, a warm leaf, the handle catching the lamp."""
    t_brick_wall(c, storm)
    solid_form(c, 2, 2, 13, 14, "blood_4", "stone_2", "blood_3")
    solid_form(c, 4, 4, 11, 13, "blood_4", "blood_3", "stone_2")
    c.hline(9, 6, 10, "stone_2")
    c.put(10, 8, "blood_4")
    c.put(10, 9, "blood_4")
    c.hline(15, 2, 13, "ink")


def t_door_shut(c, storm=False):
    """A shut door: the same frame, boarded across, no handle light."""
    t_brick_wall(c, storm)
    solid_form(c, 2, 2, 13, 14, "blood_4", "stone_2", "blood_3")
    solid_form(c, 4, 4, 11, 13, "blood_4", "blood_3", "stone_2")
    c.hline(6, 5, 10, "stone_2")
    c.hline(11, 5, 10, "stone_2")
    c.put(5, 7, "ink")
    c.put(10, 7, "ink")
    c.put(5, 12, "ink")
    c.put(10, 12, "ink")
    c.hline(15, 2, 13, "ink")


def t_window_lit(c, storm=False):
    """A lit window: a dark frame, the room in gold, the hot core at the top left, a black sill line."""
    c.fill("ink")
    c.rect(1, 1, 14, 12, "stone_2")
    c.rect(3, 3, 10, 8, "gold_4")
    c.rect(4, 3, 5, 3, "gold_5")
    c.vline(8, 3, 10, "stone_2")
    c.hline(7, 3, 12, "stone_2")
    c.hline(13, 1, 14, "stone_2")
    c.hline(14, 1, 14, "ink")
    c.hline(15, 0, 15, "ink")
    if storm:
        c.rect(9, 9, 3, 1, "stone_2")


def t_window_dark(c, storm=False):
    """The same window with nobody home: a dark frame, glass in the dark ramp, one grudging sheen."""
    c.fill("ink")
    c.rect(1, 1, 14, 12, "stone_2")
    c.rect(2, 2, 12, 10, "blood_3")
    c.vline(8, 2, 11, "stone_2")
    c.hline(7, 2, 13, "stone_2")
    c.hline(1, 1, 14, "blood_4")
    c.vline(1, 2, 12, "blood_4")
    c.put(3, 3, "blood_4")
    c.hline(13, 1, 14, "stone_2")
    c.hline(14, 1, 14, "ink")
    c.hline(15, 0, 15, "ink")


def t_lamp_base(c, storm=False):
    """A lamp post and the pool it throws: the only tile whose bright fill is the point."""
    c.fill("ink")
    lean = 1 if storm else 0
    # the post: a lit left edge, a dark body, a bold black line on either side
    c.rect(6, 1, 4, 7, "stone_2")
    c.vline(6, 1, 7, "gold_4")
    c.vline(5, 1, 7, "ink")
    c.vline(10, 1, 7, "ink")
    # the lamp head, leaning into the wind when the storm flag is set
    c.rect(6 + lean, 8, 4, 1, "stone_2")
    c.rect(6 + lean, 9, 4, 1, "gold_5")
    c.rect(5 + lean, 10, 6, 1, "gold_4")
    ring(c, 5 + lean, 8, 10 + lean, 11)
    # the pool on the paving: a lit bar, then a wider one, broken by the stone joints
    c.hline(12, 4, 11, "gold_4")
    c.hline(13, 2, 13, "gold_4")
    c.hline(14, 5, 10, "gold_5")
    for x in (5, 8, 11):
        c.put(x, 13, "ink")
    c.hline(15, 0, 15, "gold_4")


def t_sign_board(c, storm=False):
    """A harbour sign: a dark board, gold face, two rows of lettering. No words at 16 px, only dashes."""
    c.fill("ink")
    c.rect(1, 2, 14, 9, "stone_2")
    c.rect(2, 3, 12, 7, "gold_4")
    for x in (4, 6, 8, 10):
        c.vline(x, 5, 6, "gold_5")
    for x in (4, 6, 8, 10):
        c.vline(x, 8, 9, "gold_5")
    c.rect(4, 11, 1, 4, "stone_2")
    c.rect(11, 11, 1, 4, "stone_2")
    c.vline(3, 11, 14, "ink")
    c.vline(5, 11, 14, "ink")
    c.vline(10, 11, 14, "ink")
    c.vline(12, 11, 14, "ink")


def t_office_floor(c, storm=False):
    """Boards: a black joint every eight rows, a lit top edge on every board, nail heads where the joist is."""
    c.fill("blood_3")
    for y in (0, 8):
        c.hline(y, 0, 15, "ink")
    for x in (0, 8):
        c.vline(x, 0, 15, "ink")
    for y0 in (1, 9):
        for x0 in (1, 9):
            c.hline(y0, x0, x0 + 6, "blood_4")
            c.hline(y0 + 6, x0 + 1, x0 + 6, "stone_2")
    for (x, y) in ((4, 3), (12, 3), (6, 5), (10, 5), (4, 11), (12, 11), (6, 13), (10, 13)):
        c.rect(x, y, 2, 2, "stone_2")


def t_office_desk(c, storm=False):
    """A desk on boards, seen from the front: a lit top, a dark panel, an outlined drawer, legs in shadow."""
    t_office_floor(c, storm)
    solid_form(c, 1, 3, 14, 13, "blood_4", "blood_3", "stone_2")
    c.hline(6, 2, 13, "stone_2")
    ring(c, 3, 8, 8, 11)
    c.put(10, 9, "blood_4")
    c.put(10, 10, "blood_4")


# name, character for the map, palette, painter, gate on the blob test, note
TILES = [
    ("quay_paving", ".", "bg0_quay_stone", t_quay_paving, False,
     "wet flagstone on a bold black joint, a lit top and left edge per slab, the ground of every walk"),
    ("quay_paving_worn", ",", "bg0_quay_stone", t_quay_paving_worn, False,
     "the same stone with a stepped black crack, so a long walk is not one tile repeated"),
    ("quay_puddle", "~", "bg0_quay_stone", t_quay_puddle, False,
     "standing water in a low slab: a black lip, one lit edge, two glints"),
    ("quay_edge", "q", "bg0_quay_stone", t_quay_edge, False,
     "the coping at the water, a lit lip and a black drop, the tile that ends the stone honestly"),
    ("water_deep", "w", "bg1_harbour_water", t_water_deep, False,
     "harbour water, frame 1 of 2"),
    ("water_ripple", "W", "bg1_harbour_water", t_water_ripple, False,
     "harbour water, frame 2 of 2: the swell moves three pixels and the glints swap sides"),
    ("water_reflection", "R", "bg1_harbour_water", t_water_reflection, False,
     "the lamp's glint path on the water, broken into dashes so the water answers the light"),
    ("bollard", "B", "bg0_quay_stone", t_bollard, True,
     "iron bollard on wet stone: a black outline, a lit left edge, a shadow on the right"),
    ("chain", "c", "bg0_quay_stone", t_chain, True,
     "a chain draped between two bollards: one arc with a black shadow under it, the ground showing through"),
    ("barrier", "b", "bg0_quay_stone", t_barrier, True,
     "steel barrier across the quay mouth: a lit rail top, two outlined posts"),
    ("brick_wall", "#", "bg2_brick_iron", t_brick_wall, False,
     "the office frontage: two courses, black mortar, a lit top edge per brick"),
    ("brick_wall_damp", "=", "bg2_brick_iron", t_brick_wall_damp, False,
     "the same wall with bricks gone dark where the rain runs"),
    ("door_office", "D", "bg2_brick_iron", t_door_office, True,
     "the one door in the block that opens: a lit frame, a handle catching the lamp"),
    ("door_shut", "d", "bg2_brick_iron", t_door_shut, True,
     "a shut door, boarded, no handle light: seven of these teach the rule"),
    ("window_lit", "o", "bg3_lamp_glass", t_window_lit, False,
     "a lit window: the room in gold with the hot core at the top left, waived from the light share rule"),
    ("window_dark", "O", "bg2_brick_iron", t_window_dark, True,
     "the same window with nobody home, glass in the dark ramp"),
    ("lamp_base", "L", "bg3_lamp_glass", t_lamp_base, False,
     "a lamp post and the pool it throws on the stone, waived: it is a light"),
    ("sign_board", "S", "bg3_lamp_glass", t_sign_board, False,
     "a harbour sign board, lettering as dashes, waived: it is a light"),
    ("office_floor", "f", "bg2_brick_iron", t_office_floor, False,
     "the dock office boards, a black joint and a lit edge per board"),
    ("office_desk", "k", "bg2_brick_iron", t_office_desk, True,
     "the office desk Nye works behind, drawn on its own boards"),
]


# The role that carries a tile's structure, named per tile rather than guessed: the blob test asks for a "dark"
# tone, and on a tile that tone is the material's darkest role (iron, frame, joint), with the backdrop counted as
# dark too because a background tile's black is the same black the outline rule means.
DARK_ROLE = {
    "bollard": "sea_1",
    "chain": "sea_1",
    "barrier": "sea_1",
    "door_office": "stone_2",
    "door_shut": "stone_2",
    "window_dark": "stone_2",
    "office_desk": "stone_2",
}


# -----------------------------------------------------------------------------------------------------------------
# The mocks: 256x240 composed only from tiles in this sheet.

BLOCK = {
    "default": ["#", "#", "#", "#", "#", "#", ".", ".", ".", ".", "q", "w", "w", "w", "w"],
    "cells": {
        (2, 1): "o", (9, 1): "o", (13, 1): "O",
        (1, 3): "O", (4, 3): "S", (12, 2): "=", (12, 3): "O",
        (3, 5): "d", (7, 5): "D", (11, 5): "O",
        (6, 6): "~", (13, 6): "L",
        (3, 7): "B", (10, 7): "B", (1, 7): ",",
        (6, 8): "b", (2, 9): "~",
        (3, 12): "W", (8, 11): "W", (12, 13): "W", (6, 13): "W",
        (13, 11): "R", (13, 12): "R", (14, 13): "R",
    },
    "row_cells": {7: [(x, "c") for x in range(4, 10)]},
}

OFFICE = {
    "default": ["f"] * 15,
    "cells": {
        (3, 3): "k", (4, 3): "k", (5, 3): "k",
        (10, 8): "k", (11, 8): "k",
        (13, 1): "L", (1, 10): "D", (8, 12): "O",
        (6, 5): "k",
    },
    "row_cells": {},
}


def compose(layout, storm=False):
    sheet = Image.new("RGBA", (256, 240), (0, 0, 0, 255))
    by_char = {char: painter for (name, char, _p, painter, _g, _n) in TILES}
    for y in range(15):
        for x in range(16):
            name_key = layout["cells"].get((x, y))
            if name_key is None:
                for (cx, cval) in layout["row_cells"].get(y, []):
                    if cx == x:
                        name_key = cval
            if name_key is None:
                name_key = layout["default"][y]
            tile = render_tile(by_char[name_key], storm)
            sheet.paste(tile, (x * TILE, y * TILE))
    return sheet


# -----------------------------------------------------------------------------------------------------------------
# Render and measure.

def load_colours():
    with open(os.path.join(ROOT, "data", "nes_palette.json"), "r", encoding="utf-8-sig") as handle:
        nes = json.load(handle)
    with open(os.path.join(ROOT, "data", "palette.json"), "r", encoding="utf-8-sig") as handle:
        design = json.load(handle)
    entries = {item["index"]: item for item in nes["entries"]}
    ppu_hex = {item["hex"].lower() for item in nes["entries"] if item.get("usable")}
    for role, (index, _why) in ROLE_ENTRY.items():
        if role not in design["roles"]:
            raise SystemExit("%s is not a role in data/palette.json" % role)
        entry = entries[index]
        if not entry.get("usable"):
            raise SystemExit("%s resolves to %s, which is not a usable entry" % (role, entry["code"]))
        if entry["hex"].lower() not in ppu_hex:
            raise SystemExit("%s resolves to %s, which is not a 2C02 output" % (role, entry["hex"]))
    return design, entries


COLOUR = {}


def build_colour_map(entries):
    for role, (index, _why) in ROLE_ENTRY.items():
        hex_value = entries[index]["hex"].lower()
        text = hex_value.lstrip("#")
        COLOUR[role] = (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16), 255)


def render_tile(painter_or_name, storm=False):
    if isinstance(painter_or_name, Image.Image):
        return painter_or_name
    if isinstance(painter_or_name, Canvas):
        canvas = painter_or_name
    else:
        canvas = Canvas()
        canvas.fill(BACKDROP_ROLE)
        painter_or_name(canvas, storm)
    image = Image.new("RGBA", (TILE, TILE), COLOUR[BACKDROP_ROLE])
    pixels = image.load()
    for y in range(TILE):
        for x in range(TILE):
            role = canvas.rows()[y][x] or BACKDROP_ROLE
            pixels[x, y] = COLOUR[role]
    return image


def luminance(rgb):
    def channel(value):
        value = value / 255.0
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4
    return 0.2126 * channel(rgb[0]) + 0.7152 * channel(rgb[1]) + 0.0722 * channel(rgb[2])


def blob_numbers(canvas, dark_roles=None):
    """The four numbers of SPRITE-CRAFT section 8.5, measured on the tile."""
    used = {}
    for y in range(TILE):
        for x in range(TILE):
            role = canvas.rows()[y][x] or BACKDROP_ROLE
            used[role] = used.get(role, 0) + 1
    drawn = sum(used.values())
    ordered = sorted(used, key=lambda role: luminance(COLOUR[role]))
    light = ordered[-1]
    dark_roles = set(dark_roles or ()) | {ordered[0], BACKDROP_ROLE}

    def is_dark(role):
        return role in dark_roles

    light_share = round(100.0 * used[light] / drawn, 1) if drawn else 0.0
    rows_without_dark = 0
    for y in range(TILE):
        if all(not is_dark(canvas.rows()[y][x] or BACKDROP_ROLE) for x in range(TILE)):
            rows_without_dark += 1
    runs = 0
    for y in range(TILE):
        inside = False
        for x in range(TILE):
            here = is_dark(canvas.rows()[y][x] or BACKDROP_ROLE)
            if here and not inside:
                runs += 1
            inside = here
    interior = 0
    for y in range(1, TILE - 1):
        for x in range(1, TILE - 1):
            if is_dark(canvas.rows()[y][x] or BACKDROP_ROLE):
                interior += 1
    return {
        "colours": len(used),
        "roles": sorted(used),
        "dark_roles": sorted(dark_roles),
        "lightest_role": light,
        "lightest_share_percent": light_share,
        "rows_without_dark": rows_without_dark,
        "horizontal_dark_runs": runs,
        "interior_dark_pixels": interior,
    }


def blob_verdict(numbers, gated):
    if not gated:
        return "reported only: a pattern or a light source, not a character silhouette"
    failures = []
    if numbers["lightest_share_percent"] >= 30.0:
        failures.append("lightest tone is %.1f percent, the ceiling is 30" % numbers["lightest_share_percent"])
    if numbers["rows_without_dark"] != 0:
        failures.append("%d row(s) carry no dark pixel" % numbers["rows_without_dark"])
    if numbers["horizontal_dark_runs"] < 3:
        failures.append("%d horizontal dark run(s), the floor is 3" % numbers["horizontal_dark_runs"])
    if numbers["interior_dark_pixels"] < 8:
        failures.append("%d interior dark pixel(s), the floor is 8" % numbers["interior_dark_pixels"])
    return "pass" if not failures else "FAIL: " + "; ".join(failures)


def sheet_measures(sheet, rendered):
    """The rule measurements of ART-STYLE.md section 2, taken on the sheet that ships.

    Orphans and dithering are read from the pixels. The light ratio is read tile by tile against that tile's own
    palette sorted by luminance, because the quay's four palettes are hue ramps and their written order is not
    brightness order. Off palette is zero by construction: every pixel came out of ROLE_ENTRY, and
    tools/nes_audit_all.py re-checks it against data/nes_palette.json.
    """
    pixels = sheet.load()
    width, height = sheet.size
    orphans = 0
    for y in range(height):
        for x in range(width):
            here = pixels[x, y]
            if here == COLOUR[BACKDROP_ROLE]:
                continue
            same = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height and pixels[nx, ny] == here:
                        same += 1
            if same == 0:
                orphans += 1

    dither = 0
    for y in range(height - 3):
        for x in range(width - 3):
            def p(dx, dy):
                return pixels[x + dx, y + dy]
            if (p(0, 0) != p(1, 0) and p(0, 0) == p(1, 1) and p(1, 0) == p(0, 1)
                    and p(2, 0) == p(0, 0) and p(3, 0) == p(1, 0)
                    and p(0, 2) == p(0, 0) and p(0, 3) == p(1, 0)):
                dither += 1

    correct = 0
    wrong = 0
    for position, tile in enumerate(rendered):
        roles = [role for (name, proles, _note) in BG_PALETTES if name == tile["palette"] for role in proles]
        ramp = sorted(roles, key=lambda role: luminance(COLOUR[role]))
        mid, light = ramp[len(ramp) // 2], ramp[-1]
        ox = (position % COLUMNS) * TILE
        oy = (position // COLUMNS) * TILE
        for y in range(oy, oy + TILE):
            for x in range(ox, ox + TILE):
                if pixels[x, y] != COLOUR[light]:
                    continue
                below = pixels[x, y + 1] if y + 1 < oy + TILE else None
                right = pixels[x + 1, y] if x + 1 < ox + TILE else None
                above = pixels[x, y - 1] if y - 1 >= oy else None
                left = pixels[x - 1, y] if x - 1 >= ox else None
                if below == COLOUR[mid] or right == COLOUR[mid]:
                    correct += 1
                elif above == COLOUR[mid] or left == COLOUR[mid]:
                    wrong += 1

    return {
        "orphan_pixels": orphans,
        "dither_patches": dither,
        "light_direction_correct": correct,
        "light_direction_wrong": wrong,
        "light_direction_ratio": round(correct / float(wrong), 2) if wrong else None,
        "off_palette_pixels": 0,
    }


# -----------------------------------------------------------------------------------------------------------------

def build(storm=False):
    design, entries = load_colours()
    build_colour_map(entries)

    rendered = []
    for (name, char, palette, painter, gated, note) in TILES:
        canvas = Canvas()
        canvas.fill(BACKDROP_ROLE)
        painter(canvas, storm)
        orphans_removed = canvas.remove_orphans()
        roles = sorted({role for row in canvas.rows() for role in row if role})
        allowed = {role for (pname, proles, _n) in BG_PALETTES if pname == palette for role in proles}
        outside = [role for role in roles if role not in allowed and role != BACKDROP_ROLE]
        if outside:
            raise SystemExit("%s draws %s outside %s" % (name, outside, palette))
        numbers = blob_numbers(canvas, [DARK_ROLE[name]] if name in DARK_ROLE else None)
        rendered.append({
            "name": name,
            "character": char,
            "palette": palette,
            "roles": roles,
            "note": note,
            "blob": numbers,
            "blob_verdict": blob_verdict(numbers, gated),
            "blob_gated": gated,
            "orphans_removed": orphans_removed,
            "image": render_tile(canvas),
            "canvas": canvas,
        })

    sheet = Image.new("RGBA", (COLUMNS * TILE, ((len(rendered) + COLUMNS - 1) // COLUMNS) * TILE),
                      COLOUR[BACKDROP_ROLE])
    for position, tile in enumerate(rendered):
        sheet.paste(tile["image"], ((position % COLUMNS) * TILE, (position // COLUMNS) * TILE))
    return rendered, sheet


def palette_json():
    return [
        {
            "name": name,
            "roles": roles,
            "entries": [ROLE_ENTRY[role][0] for role in roles],
            "hex": [None for _ in roles],
            "note": note,
        }
        for (name, roles, note) in BG_PALETTES
    ]


def manifest(rendered, sheet, storm=False):
    palettes = palette_json()
    for palette in palettes:
        palette["hex"] = ["#%02x%02x%02x" % COLOUR[role][:3] for role in palette["roles"]]
    name = "quay_storm_tiles" if storm else "quay_tiles"
    return {
        "format": 1,
        "kind": "tileset",
        "name": name,
        "image": name + ".png",
        "card": ("ART-B-MAPS (t_d0566ebc): the R46 set (t_abfb6024) redrawn in style B, "
                 + ("hurricane variant" if storm else "night")),
        "style": ("B, late NES polish: bold dark outlines, three tone shading lit from the top left, detailed "
                  "tiles"),
        "variant": "storm" if storm else "night",
        "columns": COLUMNS,
        "rows": (len(rendered) + COLUMNS - 1) // COLUMNS,
        "frames": len(rendered),
        "frame_w": TILE,
        "frame_h": TILE,
        "imagewidth": sheet.width,
        "imageheight": sheet.height,
        "tilecount": len(rendered),
        "tile_size": TILE,
        "margin": 0,
        "spacing": 0,
        "backdrop": {"entry": ROLE_ENTRY["ink"][0], "hex": "#000000"},
        "rule": ("NES: 1 shared backdrop $0F, 4 background palettes of 3 entries, a 16x16 area carries at most 3 "
                 "colours besides the backdrop, at most 25 colours on screen; every pixel is a 2C02 output"),
        "roles": {
            role: {"entry": entry, "hex": "#%02x%02x%02x" % COLOUR[role][:3], "why": why,
                   "palette_json_index": None}
            for role, (entry, why) in sorted(ROLE_ENTRY.items())
        },
        "sets": {
            set_name: {"roles": roles, "note": "append to data/room_palettes.json as a set with this id"}
            for set_name, roles in SETS.items()
        },
        "palettes": palettes,
        "tiles": [
            {
                "index": position,
                "name": tile["name"],
                "character": tile["character"],
                "palette": tile["palette"],
                "roles": tile["roles"],
                "note": tile["note"],
                "blob": tile["blob"],
                "blob_gated": tile["blob_gated"],
                "blob_verdict": tile["blob_verdict"],
            }
            for position, tile in enumerate(rendered)
        ],
        "animation": [
            {"name": "water", "frames": ["water_deep", "water_ripple"], "hold_frames": 24,
             "note": ("the sea is the only thing on the quay that moves; two frames, one step of swell"
                      + (", drawn as chop and whitecaps under the storm" if storm else ""))}
        ],
        "mocks": (["output/quay_storm_block_preview.png"] if storm
                  else ["output/quay_block_preview.png", "output/quay_office_preview.png"]),
    }


def tiles_markdown(rendered, manifest_data, storm=False):
    lines = []
    add = lines.append
    title = "QUAY STORM TILES" if storm else "QUAY TILES"
    add("# %s: the tile table the map wiring reads" % title)
    add("")
    add("Drawn by `tools/art/make_quay_tiles.py`. Card R46 (t_abfb6024) drew the vocabulary; card ART-B-MAPS "
        "(t_d0566ebc) redrew every tile in art direction B, late NES polish: bold dark outlines, three tone "
        "shading lit from the top left, detailed tiles. Do not edit by hand: rerun the tool.")
    add("")
    add("The sheet is `%s`, %d by %d, %d cells of 16 x 16, %d tiles used. The manifest beside it "
        "(`%s`) is the machine readable copy of this table."
        % (manifest_data["image"], manifest_data["imagewidth"], manifest_data["imageheight"],
           manifest_data["columns"] * manifest_data["rows"], manifest_data["frames"], manifest_data["name"] + ".json"))
    add("")
    if storm:
        add("This sheet carries the SAME twenty names, characters, indices, palette groups and water animation as "
            "the night sheet. It is the hurricane variant of the same place, not a second vocabulary: the map row "
            "`southampton_town_quay_storm` copies the surveyed grid of `southampton_town_quay` character for "
            "character and only names a different sheet and a different room palette.")
        add("")
    add("Colours are ROLES from `data/palette.json`, not hex. The role resolves to one Ricoh 2C02 entry, because "
        "the audit's authority on a colour is `data/nes_palette.json` and the design palette's hexes are not 2C02 "
        "outputs. The bridge is the table below, and it is written in the manifest too.")
    add("")
    add("| role | 2C02 entry | hex | why that entry |")
    add("|---|---|---|---|")
    for role, (entry, why) in sorted(ROLE_ENTRY.items(), key=lambda item: ROLE_ENTRY[item[0]][0]):
        add("| `%s` | $%02X | %s | %s |" % (role, entry, "#%02x%02x%02x" % COLOUR[role][:3], why))
    add("")
    add("## The room palette sets")
    add("")
    for name, roles in SETS.items():
        add("- **%s** (%d roles, cap 16): %s" % (name, len(roles), ", ".join("`%s`" % role for role in roles)))
    add("")
    add("## The four background palettes")
    add("")
    add("| palette | roles | 2C02 entries | what it draws |")
    add("|---|---|---|---|")
    for (name, roles, note) in BG_PALETTES:
        add("| `%s` | %s | %s | %s |" % (name, ", ".join("`%s`" % role for role in roles),
                                         ", ".join("$%02X" % ROLE_ENTRY[role][0] for role in roles), note))
    add("")
    add("## The rules of ART-STYLE.md section 2, measured on this sheet")
    add("")
    rules = manifest_data.get("rules") or {}
    add("| rule | measurement on the shipped sheet |")
    add("|---|---|")
    add("| no orphan pixels | %s |" % rules.get("orphan_pixels"))
    add("| no dithering unless deliberate | %s patch(es) |" % rules.get("dither_patches"))
    add("| light from the top left | %s correct / %s wrong (ratio %s) |"
        % (rules.get("light_direction_correct"), rules.get("light_direction_wrong"),
           rules.get("light_direction_ratio")))
    add("| 2C02 only | %s off palette pixel(s), and tools/nes_audit_all.py re-checks every entry |"
        % rules.get("off_palette_pixels"))
    add("| at most 3 colours besides the backdrop in a 16 x 16 area | enforced while drawing: a tile that leaves "
        "its palette raises |")
    add("")
    add("## The tiles")
    add("")
    add("| # | name | char | palette | roles | blob test | what it is |")
    add("|---|---|---|---|---|---|---|")
    for position, tile in enumerate(rendered):
        numbers = tile["blob"]
        add("| %d | `%s` | `%s` | `%s` | %s | %s | %s |"
            % (position, tile["name"], tile["character"], tile["palette"],
               " ".join("`%s`" % role for role in tile["roles"]),
               ("%s (light %.0f%%, %d rows no dark, %d runs, %d inner dark)"
                % ("PASS" if tile["blob_verdict"] == "pass" else
                   ("n/a" if not tile["blob_gated"] else "FAIL"),
                   numbers["lightest_share_percent"], numbers["rows_without_dark"],
                   numbers["horizontal_dark_runs"], numbers["interior_dark_pixels"])),
               tile["note"]))
    add("")
    add("## How to wire it")
    add("")
    add("1. Every tile is 16 x 16 and index i in the sheet is `floor(i / 8)` rows down and `i % 8` cells across.")
    add("2. A tile draws from exactly one background palette, so a 16 x 16 attribute area can never carry a "
        "fourth colour. Give the area the palette named in the table and no other.")
    add("3. `water_deep` and `water_ripple` are the two frames of one animation; hold each for about 24 game "
        "frames, which is the slow swell the night quay wants and not a flicker.")
    add("4. Objects stand ON their own ground: `bollard`, `chain` and `barrier` include the paving they sit on, "
        "and `door_office`, `door_shut` and the windows include the brick around them, so a map can place them "
        "without a transparent layer.")
    add("5. The office pair (`office_floor`, `office_desk`) is the same warm ramp, so the interior scene uses the "
        "office night set and needs no fifth palette.")
    if storm:
        add("6. **The one line the storm map needs.** `pp_map_tile_set_for_room` in "
            "`game/scripts/pp_map_tile/pp_map_tile.gml` turns a room palette id into a tile table. The storm map "
            "row names `room_palette: quay_storm` so the room draws in the storm set, so that function needs "
            "`if (_id == \"quay_storm\") return PP_TILE_SET_QUAY;` beside the quay_night and office_night lines. "
            "The tile table, the planes and the water animation are then the quay's own, and only the sheet "
            "differs, because the map row names `tileset: quay_storm_tiles`.")
        add("7. The sheet has to reach the build: `tools/sync_art.py` now reads `game/sprites_src/env/quay_storm/` "
            "(alongside env/quay, env/halls and env/street), so `pp_art_has(\"quay_storm_tiles\")` is true after a "
            "sync and the map row's `tileset` is the set the game draws. Without that folder in its source list the "
            "game falls back to flat colour for this room.")
    add("")
    add("## What this set does not do")
    add("")
    add("1. **The light does not spill across tile edges.** A tile carries three colours plus the backdrop, so the "
        "lamp's pool is inside its own cell.")
    add("2. **There is no building wall above three courses.** The block's upper floors are the same brick tile "
        "repeated; a window sill course and a roofline are the next two tiles this set needs.")
    add("3. **Nothing here is a sprite.** These are background tiles on the 16 x 16 attribute grid: characters, "
        "the clerk and the sailor stand on them and obey the sprite rules in SPRITE-CRAFT, not these.")
    add("")
    return "\n".join(lines)


def write_png(path, image):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path)


def write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write("\n")


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def contact_sheet(sheet):
    resample = getattr(Image, "NEAREST", None) or Image.Resampling.NEAREST
    return sheet.resize((sheet.width * 3, sheet.height * 3), resample)


def before_after(before_path, after_image, out_path, title, before_label, after_label, scale=3):
    """One labelled sheet: the before picture on top, the after picture under it, both at 3x."""
    if not os.path.isfile(before_path):
        print("make_quay_tiles: no before picture at %s, the pair sheet is skipped"
              % os.path.relpath(before_path, ROOT))
        return False
    resample = getattr(Image, "NEAREST", None) or Image.Resampling.NEAREST
    before = Image.open(before_path).convert("RGBA")
    after = after_image.convert("RGBA")
    width = max(before.width, after.width) * scale
    band = 12
    height = (before.height + after.height) * scale + band * 2
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    draw = ImageDraw.Draw(canvas)
    canvas.paste(before.resize((before.width * scale, before.height * scale), resample), (0, band))
    canvas.paste(after.resize((after.width * scale, after.height * scale), resample),
                 (0, band + before.height * scale + band))
    draw.text((2, 1), "%s: %s" % (title, before_label), fill=(248, 216, 120, 255))
    draw.text((2, band + before.height * scale + 1), "%s: %s" % (title, after_label),
              fill=(248, 216, 120, 255))
    write_png(out_path, canvas)
    return True


def frame_note(path, name, card):
    write_json(path, {
        "format": 1,
        "kind": "frame_note",
        "frame": name,
        "card": card,
        "backdrop": {"entry": ROLE_ENTRY["ink"][0], "hex": "#000000"},
        "note": ("a 256x240 mock composed only from the quay tile sheet, so the frame audit measures the "
                 "same art the map will use"),
    })


def stale(path, image):
    if not os.path.isfile(path):
        return True
    with open(path, "rb") as handle:
        on_disk = hashlib.sha256(handle.read()).hexdigest()
    buffer = os.path.join(OUTPUT, "_quay_tiles_stale_probe.png")
    os.makedirs(OUTPUT, exist_ok=True)
    image.save(buffer)
    with open(buffer, "rb") as handle:
        fresh = hashlib.sha256(handle.read()).hexdigest()
    os.remove(buffer)
    return on_disk != fresh


def main(argv=None):
    parser = argparse.ArgumentParser(description="Draw the quay tile set, night and hurricane, in style B.")
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 if a PNG on disk is stale")
    args = parser.parse_args(argv)

    rendered, sheet = build(False)
    storm_rendered, storm_sheet = build(True)

    if args.check:
        bad = [path for path, image in ((SHEET_PNG, sheet), (STORM_PNG, storm_sheet)) if stale(path, image)]
        if bad:
            print("make_quay_tiles: STALE %s" % ", ".join(os.path.relpath(path, ROOT) for path in bad))
            return 1
        print("make_quay_tiles: both sheets are fresh")
        return 0

    for sheet_png, sheet_json, tiles_md, tiles, image, is_storm in (
            (SHEET_PNG, SHEET_JSON, TILES_MD, rendered, sheet, False),
            (STORM_PNG, STORM_JSON, STORM_MD, storm_rendered, storm_sheet, True)):
        payload = manifest(tiles, image, is_storm)
        payload["rules"] = sheet_measures(image, tiles)
        write_png(sheet_png, image)
        write_json(sheet_json, payload)
        write_text(tiles_md, tiles_markdown(tiles, payload, is_storm) + "\n")

    write_png(os.path.join(OUTPUT, "quay_tiles_3x.png"), contact_sheet(sheet))
    write_png(os.path.join(OUTPUT, "quay_storm_tiles_3x.png"), contact_sheet(storm_sheet))

    for name, layout, is_storm in (("quay_block", BLOCK, False), ("quay_office", OFFICE, False),
                                   ("quay_storm_block", BLOCK, True)):
        frame = compose(layout, is_storm)
        write_png(os.path.join(OUTPUT, "%s_preview.png" % name), frame)
        frame_note(os.path.join(OUTPUT, "%s_preview.json" % name), "%s_preview.png" % name,
                   "ART-B-MAPS (t_d0566ebc)")

    before_after(os.path.join(BEFORE_DIR, "quay_tiles_before.png"), sheet,
                 os.path.join(PAIR_DIR, "quay_before_after_3x.png"),
                 "Town Quay tiles", "R46 (before)", "style B (after)")
    before_after(os.path.join(BEFORE_DIR, "quay_block_before.png"), compose(BLOCK, False),
                 os.path.join(PAIR_DIR, "quay_before_after_frame_3x.png"),
                 "Town Quay block", "R46 frame (before)", "style B frame (after)")
    before_after(os.path.join(BEFORE_DIR, "quay_block_before.png"), compose(BLOCK, True),
                 os.path.join(PAIR_DIR, "quay_storm_before_after_3x.png"),
                 "Town Quay hurricane block", "calm block (before, no storm art existed)",
                 "storm block in style B (after)")

    for label, tiles, image in (("night", rendered, sheet), ("storm", storm_rendered, storm_sheet)):
        gated = [tile for tile in tiles if tile["blob_gated"]]
        failing = [tile for tile in gated if tile["blob_verdict"] != "pass"]
        colours = len({COLOUR[role] for role in ROLE_ENTRY})
        rules = sheet_measures(image, tiles)
        print("make_quay_tiles %s: %d tiles, %d colours, sheet %dx%d" % (label, len(tiles), colours,
                                                                         image.width, image.height))
        print("  blob test: %d gated tile(s), %d pass, %d fail" % (len(gated), len(gated) - len(failing),
                                                                   len(failing)))
        print("  rules: orphans %d, dither %d, light %d/%d, off palette %d"
              % (rules["orphan_pixels"], rules["dither_patches"], rules["light_direction_correct"],
                 rules["light_direction_wrong"], rules["off_palette_pixels"]))
        for tile in failing:
            print("    FAIL %s: %s" % (tile["name"], tile["blob_verdict"]))
    print("  sheets: %s, %s" % (os.path.relpath(SHEET_PNG, ROOT).replace(os.sep, "/"),
                                os.path.relpath(STORM_PNG, ROOT).replace(os.sep, "/")))
    print("  tables: %s, %s" % (os.path.relpath(TILES_MD, ROOT).replace(os.sep, "/"),
                                os.path.relpath(STORM_MD, ROOT).replace(os.sep, "/")))
    failing = [tile for tiles in (rendered, storm_rendered) for tile in tiles
               if tile["blob_gated"] and tile["blob_verdict"] != "pass"]
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
