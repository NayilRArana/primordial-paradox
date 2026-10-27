#!/usr/bin/env python3
"""TS2-ART-B: the v2 night title world for "The Long Night Road", on the NES background rule.

Contract: PLAN-V2-2026-10-21.md section 2, specs\\14-title-screen-drive.md and its night addendum, and
data\\title.json (the layer table the game reads at runtime). Everything here is original and clean room:
the drawing is computed from numbers in this repository, no reference to, copy of or trace of any existing
game's art is read, and nothing outside this repository is used except the font sheet this project owns.

The rule this file exists to satisfy: on the cartridge a background is a grid of 16x16 attribute areas,
and each area draws from three colours plus one shared backdrop colour. Every layer here is built to
that rule, and tools\\art\\nes_bg.py checks it with code that never looks at how the drawing was made.

What this writes, all deterministic (no clock, no window, no network):
  game\\sprites_src\\title\\title_L1_sky.png     512x120, 2 frames (star twinkle variant)
  game\\sprites_src\\title\\title_L2_clouds.png  512x120, 1 frame
  game\\sprites_src\\title\\title_L3_downs.png   512x48,  1 frame (chalk downs, chalk cutting, cathedral)
  game\\sprites_src\\title\\title_L4_fields.png  512x56,  1 frame (fields and hedgerows)
  game\\sprites_src\\title\\title_L5_verge.png   512x92,  1 frame (hedge, dry stone wall, poles)
  game\\sprites_src\\title\\title_L6_road.png    512x44,  1 frame (tarmac, lane markings)
  game\\sprites_src\\title\\title_L7_fg.png      512x44,  1 frame (foreground grass and fence posts)
  game\\sprites_src\\title\\spr_title_sign.png   96x24,  4 frames (Basingstoke and Winchester over Southampton 55, 43, 30, 20)
  game\\sprites_src\\title\\spr_title_cone.png   90x40,  1 frame (headlight cone overlay)
  game\\sprites_src\\title\\title_BG_bigben.png  256x240, 1 frame (the opening shot, Big Ben at night)
  the same eight strips again with the flash palette applied, as *_flash.png
  data\\title.json and data\\title_flash.json, the layer table and the flash palette
  output\\ts2_world_preview.png     the composed 256x240 night frame at 3x (768x720)
  output\\ts2_bigben_preview.png    the Big Ben opening shot at 3x (768x720)
  output\\ts2_world_manifest.json  sizes, sha256 and the colour count of every file

THE PALETTE, and why it is this small
  Every layer draws from one set of fourteen master palette entries, so the whole drive fits in the
  sixteen colours the title room is allowed (spec 13). The list is below and nothing else may enter a
  file. Each layer names one of them as its shared backdrop, which is the colour every 16x16 area of
  that layer is allowed to use in addition to its own three.

  INK        0  #0b0b0f  outlines, road grain, hedge shadow
  ASPHALT    1  #1c1c24  the tarmac
  DIM        3  #4a4a58  dim stars, the chalk crest, the wall's top course
  BRIGHT     5  #c8c8d4  the moon, the chalk cutting, the lane markings, the sign lettering
  SKY_DEEP   6  #081420  the top of the night sky
  SKY_MID    7  #0d2b3a  the middle of the night sky
  SKY_LOW    8  #11485c  the sky above the downs
  GREEN_DEEP 25 #232a12  the far field floor, the oak canopies
  GREEN_MID  26 #3a4420  the hedge mass, the wall gaps
  GREEN_LIT  27 #55632f  the lit field parcels, the sign face
  GREEN_PALE 29 #adbc74  the nearest verge grass
  STONE_DEEP 30 #14110f  the cathedral silhouette
  STONE_MID  32 #3b3226  the dry stone wall
  GOLD       41 #e8c65a  the lit windows

  The flash palette is the same colours one step up each hue ramp of the master palette, so a lightning
  flash lifts the dark tones without touching the hue. It lives in data\\title_flash.json.

THE LAYERS, back to front, and what each one is for
  L1 sky     512x120 at screen y 0    three night bands, the moon, the stars, and two constellations
  L2 clouds  512x120 at screen y 0    thin night cloud bands
  L3 downs   512x48  at screen y 92   the chalk downs, the Twyford Down chalk cutting, Winchester
                                    Cathedral far off, and the chalk horse
  L4 fields  512x56  at screen y 128  patchwork fields, hedgerows, oaks
  L5 verge   512x92  at screen y 120  the hedge, the dry stone wall, the telegraph poles, the sign posts
  L6 road    512x44  at screen y 196  the tarmac with its lane markings
  L7 fg      512x44  at screen y 196  the near grass and the fence posts that pass in front of the car

  The sign is a sprite, not part of the verge, because the miles count down: spr_title_sign carries the
  four variants and the game draws it over the posts. The headlight cone is a sprite for the same
  reason the road scrolls: a cone baked into the 512 px tile would repeat every 512 px.

The Big Ben opening shot is a single 256x240 background, not a scrolling layer: the camera pans down
from the clock face to the car leaving London, and the pan is a camera move over one picture.

Usage:
    python tools/art/make_title_world.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PALETTE_PATH = os.path.join(ROOT, "data", "palette.json")
SPRITE_DIR = os.path.join(ROOT, "game", "sprites_src", "title")
OUT_DIR = os.path.join(ROOT, "output")
FONT_PATH = os.path.join(SPRITE_DIR, "spr_pp_font8.png")
DATA_DIR = os.path.join(ROOT, "data")

W = 512
SCREEN_W = 256
SCREEN_H = 240
TRANSPARENT = 255

# -----------------------------------------------------------------------------------------------------------------
# The palette. Index into data/palette.json.
# -----------------------------------------------------------------------------------------------------------------

INK = 0          # #0b0b0f
ASPHALT = 1      # #1c1c24
DIM = 3          # #4a4a58
BRIGHT = 5       # #c8c8d4
SKY_DEEP = 6     # #081420
SKY_MID = 7      # #0d2b3a
SKY_LOW = 8      # #11485c
GREEN_DEEP = 25  # #232a12
GREEN_MID = 26   # #3a4420
GREEN_LIT = 27   # #55632f
GREEN_PALE = 29  # #adbc74
STONE_DEEP = 30  # #14110f
STONE_MID = 32   # #3b3226
GOLD = 41        # #e8c65a

SCENE_COLOURS = [INK, ASPHALT, DIM, BRIGHT, SKY_DEEP, SKY_MID, SKY_LOW,
                 GREEN_DEEP, GREEN_MID, GREEN_LIT, GREEN_PALE, STONE_DEEP, STONE_MID, GOLD]

# The shared backdrop of each layer: the colour every 16x16 area of that layer may use in addition to
# its own three. It is the dominant colour of the layer, which is what makes it a backdrop.
LAYER_BACKDROP = {
    "title_L1_sky": SKY_DEEP,
    "title_L2_clouds": SKY_DEEP,
    "title_L3_downs": SKY_DEEP,
    "title_L4_fields": GREEN_DEEP,
    "title_L5_verge": GREEN_MID,
    "title_L6_road": ASPHALT,
    "title_L7_fg": INK,
    "title_BG_bigben": SKY_DEEP,
}

# The order the solver keeps colours in when an area has to lose one: an accent that carries meaning
# survives, a texture tone does not.
LAYER_PRIORITY = {
    "title_L1_sky": [BRIGHT, DIM, SKY_LOW, SKY_MID, SKY_DEEP],
    "title_L2_clouds": [DIM, SKY_DEEP, SKY_MID],
    "title_L3_downs": [BRIGHT, STONE_DEEP, DIM, SKY_DEEP],
    "title_L4_fields": [INK, GREEN_LIT, GREEN_MID, GREEN_DEEP],
    "title_L5_verge": [GREEN_LIT, STONE_MID, DIM, GREEN_MID, GREEN_PALE],
    "title_L6_road": [BRIGHT, GREEN_MID, ASPHALT, INK],
    "title_L7_fg": [GREEN_DEEP, INK],
    "title_BG_bigben": [BRIGHT, GOLD, STONE_DEEP, SKY_LOW, SKY_MID, SKY_DEEP],
}

# -----------------------------------------------------------------------------------------------------------------
# Palette helpers.
# -----------------------------------------------------------------------------------------------------------------

def load_palette():
    with open(PALETTE_PATH, "r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    colours = []
    for entry in data["colours"]:
        value = entry.lstrip("#")
        colours.append((int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)))
    return colours


PALETTE = load_palette()


def hue_of(index: int) -> int:
    """Which of the nine hue ramps a master palette index belongs to."""
    return index // 6


def level_of(index: int) -> int:
    """Where an index sits in its hue ramp, 0 (darkest) to 5 (lightest)."""
    return index % 6


def flash_index(index: int) -> int:
    """One step up the same hue ramp. The top of a ramp is already the lightest the master palette has,
    so it stays where it is: a flash lifts the dark tones and leaves the bright ones alone."""
    level = level_of(index)
    if level >= 5:
        return index
    return hue_of(index) * 6 + level + 1


def flash_map(indices) -> dict:
    """The flash palette: every colour in use, one step up its own hue ramp."""
    return {index: flash_index(index) for index in sorted(set(indices))}


# -----------------------------------------------------------------------------------------------------------------
# The font. The project's own 8x8 sheet when it exists, a built in 5x7 fallback otherwise.
# -----------------------------------------------------------------------------------------------------------------

FONT_ORDER = " !',-.0123456789:?ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GLYPH_W = 5
GLYPH_H = 7
GLYPH_GAP = 1

FALLBACK_FONT = {
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    "'": ["..#..", "..#..", ".....", ".....", ".....", ".....", "....."],
    ",": [".....", ".....", ".....", ".....", ".....", "..#..", ".#..."],
    "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    ".": [".....", ".....", ".....", ".....", ".....", "..#..", "..#.."],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    ":": [".....", "..#..", ".....", ".....", ".....", "..#..", "....."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
}


def load_glyphs():
    """Return {character: 7 rows of 5 booleans}, plus the name of the source it came from."""
    if os.path.isfile(FONT_PATH):
        with Image.open(FONT_PATH) as handle:
            image = handle.convert("RGBA")
        pixels = image.load()
        width, height = image.size
        cell = 8
        if width == len(FONT_ORDER) * cell and height == cell:
            glyphs = {}
            for index, character in enumerate(FONT_ORDER):
                rows = []
                for y in range(GLYPH_H):
                    rows.append([pixels[index * cell + 1 + x, y][3] > 0 for x in range(GLYPH_W)])
                glyphs[character] = rows
            return glyphs, "spr_pp_font8.png"
    glyphs = {}
    for character, rows in FALLBACK_FONT.items():
        glyphs[character] = [[cell == "#" for cell in row] for row in rows]
    return glyphs, "the built in 5x7 fallback"


GLYPHS, FONT_SOURCE = load_glyphs()


def text_width(text, advance=GLYPH_W + GLYPH_GAP):
    if not text:
        return 0
    return len(text) * advance - GLYPH_GAP


# -----------------------------------------------------------------------------------------------------------------
# A tile is a grid of palette indices. x wraps, so every drawing call is seamless by construction.
# -----------------------------------------------------------------------------------------------------------------

class Tile:
    def __init__(self, width, height, fill=TRANSPARENT):
        self.w = width
        self.h = height
        self.px = bytearray([fill]) * (width * height)

    def put(self, x, y, colour):
        if 0 <= y < self.h:
            self.px[y * self.w + (x % self.w)] = colour

    def get(self, x, y):
        if 0 <= y < self.h:
            return self.px[y * self.w + (x % self.w)]
        return TRANSPARENT

    def rect(self, x0, y0, x1, y1, colour):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, colour)

    def hline(self, x0, x1, y, colour):
        for x in range(x0, x1 + 1):
            self.put(x, y, colour)

    def column(self, x, y0, y1, colour):
        for y in range(y0, y1 + 1):
            self.put(x, y, colour)

    def band(self, y0, y1, colour):
        for y in range(y0, y1 + 1):
            for x in range(self.w):
                self.px[y * self.w + x] = colour

    def disc(self, cx, cy, radius, colour):
        r2 = radius * radius
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                    self.put(x, y, colour)

    def poly(self, points, colour):
        ys = [p[1] for p in points]
        top = int(math.floor(min(ys)))
        bottom = int(math.ceil(max(ys)))
        count = len(points)
        for y in range(top, bottom + 1):
            crossings = []
            for i in range(count):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % count]
                if y1 == y2:
                    continue
                if min(y1, y2) <= y < max(y1, y2):
                    t = (y - y1) / float(y2 - y1)
                    crossings.append(x1 + t * (x2 - x1))
            crossings.sort()
            for i in range(0, len(crossings) - 1, 2):
                xa = int(math.floor(crossings[i]))
                xb = int(math.ceil(crossings[i + 1]))
                for x in range(xa, xb + 1):
                    self.put(x, y, colour)

    def text(self, x, y, message, colour):
        cursor = x
        for character in message.upper():
            glyph = GLYPHS.get(character)
            if glyph is None:
                cursor += GLYPH_W + GLYPH_GAP
                continue
            for ry in range(GLYPH_H):
                for rx in range(GLYPH_W):
                    if glyph[ry][rx]:
                        self.put(cursor + rx, y + ry, colour)
            cursor += GLYPH_W + GLYPH_GAP
        return cursor

    def patch(self, x, y, rows, mapping):
        for ry, row in enumerate(rows):
            for rx, character in enumerate(row):
                colour = mapping.get(character)
                if colour is not None:
                    self.put(x + rx, y + ry, colour)

    def image(self):
        buf = bytearray(self.w * self.h * 4)
        i = 0
        for value in self.px:
            if value == TRANSPARENT:
                i += 4
                continue
            r, g, b = PALETTE[value]
            buf[i] = r
            buf[i + 1] = g
            buf[i + 2] = b
            buf[i + 3] = 255
            i += 4
        return Image.frombytes("RGBA", (self.w, self.h), bytes(buf))

    def colours_used(self):
        return sorted(set(v for v in self.px if v != TRANSPARENT))

    def remap(self, mapping):
        """A copy of this tile with every colour replaced through a mapping."""
        out = Tile(self.w, self.h)
        for index, value in enumerate(self.px):
            if value == TRANSPARENT:
                out.px[index] = TRANSPARENT
            else:
                out.px[index] = mapping.get(value, value)
        return out


# -----------------------------------------------------------------------------------------------------------------
# L1: the night sky. Three bands, the moon, the stars, and two constellations that can be traced.
# -----------------------------------------------------------------------------------------------------------------

# The bands sit on 16 px boundaries, so a 16x16 area never carries two band colours.
#
# Direction B (card ART-B-OPENING) lights the frame from the top left, and ART-STYLE section 2 counts it as
# "every light pixel that has a mid tone below it or to its right". A ramp that gets brighter toward the
# bottom of the screen is therefore wrong by that row even though a night sky painted that way looks
# natural, and measured 2026-10-27 the sky was the largest single offender in the card's set: 4097 pairs
# correct against 4585 wrong. So the ramp runs bright at the zenith (SKY_LOW) down to SKY_DEEP, the darkest
# band, at the horizon. Same three colours, so the frame's 16 colour budget does not move.
SKY_BANDS = [
    (0, 47, SKY_LOW),
    (48, 79, SKY_MID),
    (80, 119, SKY_DEEP),
]


def sky_band(y):
    """The band colour at row y, read off SKY_BANDS so the moon's bite and the field cannot disagree."""
    for y0, y1, colour in SKY_BANDS:
        if y0 <= y <= y1:
            return colour
    return SKY_BANDS[-1][2]

MOON_CX, MOON_CY, MOON_R = 176, 30, 11

# The sickle: a crescent of stars, the harvest blade the title is named for. Points are (x, y) in the
# strip, and the shape is an arc, so a player can trace it with a finger.
SICKLE_POINTS = [
    (330, 18), (338, 16), (346, 17), (352, 21), (355, 27), (354, 34), (349, 40),
    (342, 43), (334, 43), (327, 40), (323, 34), (323, 27), (326, 21),
]

# The thunderbolt: a zigzag, drawn with the same dim star colour so it is a constellation and not a
# stroke of paint.
BOLT_POINTS = [
    (58, 52), (66, 58), (60, 64), (70, 70), (64, 76), (74, 82), (68, 88), (78, 94),
]


def build_sky():
    """The night sky: three bands, a moon with craters, a star field, and two constellations.

    Every 16x16 area carries one band colour, the dim star colour and the bright star colour, which is
    three, so the area rule holds without the solver having to touch anything.
    """
    tile = Tile(W, 120)
    for y0, y1, colour in SKY_BANDS:
        tile.band(y0, y1, colour)

    # The far stars: one dim pixel each.
    rng = random.Random(1101)
    for _ in range(190):
        x = rng.randrange(256) if rng.random() < 0.7 else rng.randrange(W)
        y = rng.randrange(2, 92)
        tile.put(x, y, DIM)

    # The near stars: a bright pixel, some of them a small cross.
    rng = random.Random(2202)
    twinklers = []
    for _ in range(46):
        x = rng.randrange(256) if rng.random() < 0.7 else rng.randrange(W)
        y = rng.randrange(2, 88)
        colour = BRIGHT if rng.random() < 0.45 else DIM
        tile.put(x, y, colour)
        if rng.random() < 0.25:
            tile.put(x - 1, y, colour)
            tile.put(x + 1, y, colour)
            tile.put(x, y - 1, colour)
            tile.put(x, y + 1, colour)
        twinklers.append((x, y))

    # The two constellations. They are drawn in the dim colour, so they read as faint, and every point
    # is a single pixel with a neighbour, which is what makes a constellation traceable.
    for points in (SICKLE_POINTS, BOLT_POINTS):
        for x, y in points:
            tile.put(x, y, DIM)
            tile.put(x + 1, y, DIM)

    # The moon: a bright disc with a dim crater, and the lower left bitten out so it reads as a shape.
    tile.disc(MOON_CX, MOON_CY, MOON_R, BRIGHT)
    for dx, dy, radius in ((4, -3, 3), (-3, 2, 2), (1, 5, 2)):
        tile.disc(MOON_CX + dx, MOON_CY + dy, radius, DIM)
    for y in range(MOON_CY - MOON_R, MOON_CY + MOON_R + 1):
        for x in range(MOON_CX, MOON_CX + MOON_R + 1):
            if (x - MOON_CX) ** 2 + (y - MOON_CY) ** 2 > (MOON_R - 2) ** 2:
                if (x - MOON_CX) ** 2 + (y - MOON_CY) ** 2 <= MOON_R * MOON_R:
                    tile.put(x, y, DIM)
    for y in range(MOON_CY - MOON_R + 3, MOON_CY + MOON_R - 1):
        for x in range(MOON_CX - MOON_R + 3, MOON_CX):
            if (x - MOON_CX) ** 2 + (y - MOON_CY) ** 2 <= (MOON_R - 3) ** 2:
                band = sky_band(y)
                tile.put(x, y, band)

    # Nothing is drawn over the moon, and no star sits in the tower's column on the Big Ben shot.
    for y in range(MOON_CY - MOON_R - 2, MOON_CY + MOON_R + 3):
        for x in range(MOON_CX - MOON_R - 2, MOON_CX + MOON_R + 3):
            if (x - MOON_CX) ** 2 + (y - MOON_CY) ** 2 <= (MOON_R + 1) ** 2:
                if tile.get(x, y) in (DIM, BRIGHT):
                    band = sky_band(y)
                    tile.put(x, y, band)

    # The twinkle frame: a deterministic subset of the near stars changes level. The moon does not move.
    frame_one = Tile(W, 120)
    frame_one.px[:] = tile.px
    for index, (x, y) in enumerate(twinklers):
        current = frame_one.get(x, y)
        if current == BRIGHT:
            new = DIM
        elif index % 3 == 0:
            new = DIM
        else:
            new = BRIGHT
        frame_one.put(x, y, new)
    return [tile, frame_one]


# -----------------------------------------------------------------------------------------------------------------
# L2: the night clouds.
# -----------------------------------------------------------------------------------------------------------------

def build_clouds():
    """Thin cloud bands, one colour, drawn fully inside the tile so the wrap never cuts a cloud."""
    tile = Tile(W, 120)
    clouds = [
        (56, 22, 46, 6), (150, 60, 40, 5), (232, 18, 58, 7),
        (330, 66, 44, 5), (398, 32, 50, 6), (470, 64, 38, 5),
    ]
    for cx, cy, half, thick in clouds:
        for step in range(-half, half + 1):
            frac = 1.0 - abs(step) / float(half)
            height = int(round(thick * math.sqrt(max(0.0, frac))))
            if height <= 0:
                continue
            x = cx + step
            for dy in range(height):
                y = cy - height // 2 + dy
                tile.put(x, y, SKY_DEEP)
    # No separate crown row. Direction B (card ART-B-OPENING) drew one in DIM and then in BRIGHT, and neither
    # ships as drawn: the cloud sits in bands 1 and 2, whose palette is bg0 ($12 $00 $28), so the band pass
    # snaps any other light tone to $00 grey, and $00 is a row 0 entry: in a fade twin it falls to black in one
    # step while the body under it only drops one row. Measured 2026-10-27: title_L2_clouds_fade1 read 473
    # correct against 545 wrong with the DIM crown and the same with the BRIGHT one. The polish pass already
    # rims the body's top boundary with $12, which is brighter than the body and fades on the same row as it.
    return [tile]


# -----------------------------------------------------------------------------------------------------------------
# L3: the chalk downs, the Twyford Down chalk cutting, and Winchester Cathedral far off.
# -----------------------------------------------------------------------------------------------------------------

CHALK_HORSE = [
    "            ###   ",
    "           ## #   ",
    "          ##  ##  ",
    "  #####  ##      ",
    " ###########      ",
    "############      ",
    "###########  #    ",
    " ####  ####       ",
    "  ##    ##       ",
    " ##      ##      ",
    "###       ##     ",
]

# The cathedral sits far off on the horizon: a long nave and a square tower, in silhouette.
CATHEDRAL_X = 400
CATHEDRAL_NAVE_TOP = 13
CATHEDRAL_TOWER_TOP = 2
CATHEDRAL_TOWER_W = 13
CATHEDRAL_NAVE_W = 52
CATHEDRAL_BASE = 22


def build_downs():
    """The far chalk downs.

    The layer is 48 px tall and sits at screen y 92, so the ridge line is at screen y 100 to 112 and
    the cathedral stands clear of the field band that starts at screen y 128.

    Colours: the deep sky is the backdrop, so an area may add the dim crest, the bright chalk and the
    cathedral silhouette, which is three.
    """
    tile = Tile(W, 48)

    def ridge(x):
        return 14 + 3 * math.sin(2.0 * math.pi * x / float(W)) \
                 + 2 * math.sin(2.0 * math.pi * 2 * x / float(W) + 1.1)

    tops = [int(round(ridge(x))) for x in range(W)]
    for x in range(W):
        tile.column(x, tops[x], 47, SKY_DEEP)
        # The crest is BRIGHT and not DIM for the same reason the cloud crown is: a $00 crest falls to black in
        # one fade step while the body under it only drops a row, so the lit line ends up darker than the
        # down it lights. Measured 2026-10-27: title_L3_downs_fade1 read 568 correct against 573 wrong with
        # the DIM crest and title_L3_downs read 1117 against 254. Chalk is white, so the ridge reads as chalk.
        tile.put(x, tops[x], BRIGHT)

    # The chalk cutting of Twyford Down: a bright scar across the face of the down, with the dim
    # shadow under its lip. It is the feature the road is named for, so it is drawn on the skyline.
    cut_start, cut_end = 232, 300
    for x in range(cut_start, cut_end + 1):
        depth = 5 + int(2 * math.sin((x - cut_start) * math.pi / 18.0))
        for dy in range(depth):
            y = tops[x] + 1 + dy
            tile.put(x, y, BRIGHT)
        tile.put(x, tops[x] + 1 + depth, DIM)

    # The chalk horse, cut into the face of the down at x 148.
    horse_x = 148
    horse_top = max(tops[horse_x + column] for column in range(15)) + 1
    tile.patch(horse_x, horse_top, CHALK_HORSE, {"#": BRIGHT})
    for column in range(15):
        x = horse_x + column
        for y in range(horse_top, 47):
            if tile.get(x, y) == BRIGHT:
                tile.put(x, y + 1, DIM)
                break

    # Winchester Cathedral, far off: a long nave, a square tower and a low crossing. A silhouette, so
    # one colour, and it stands on the ridge so it reads against the sky.
    base = CATHEDRAL_BASE
    nave_left = CATHEDRAL_X
    nave_right = CATHEDRAL_X + CATHEDRAL_NAVE_W
    tile.rect(nave_left, CATHEDRAL_NAVE_TOP, nave_right, base, STONE_DEEP)
    tile.rect(nave_left, CATHEDRAL_NAVE_TOP, nave_right, CATHEDRAL_NAVE_TOP, STONE_DEEP)
    tower_left = nave_right - CATHEDRAL_TOWER_W
    tile.rect(tower_left, CATHEDRAL_TOWER_TOP, nave_right, base, STONE_DEEP)
    # The pitched roof of the nave, and a low spirelet on the tower.
    tile.poly([(nave_left, CATHEDRAL_NAVE_TOP), (nave_left + 14, CATHEDRAL_NAVE_TOP - 5),
               (nave_left + 28, CATHEDRAL_NAVE_TOP), (nave_left + 28, CATHEDRAL_NAVE_TOP + 1),
               (nave_left + 14, CATHEDRAL_NAVE_TOP - 4), (nave_left, CATHEDRAL_NAVE_TOP + 1)], STONE_DEEP)
    tile.rect(tower_left + 4, CATHEDRAL_TOWER_TOP - 4, tower_left + 8, CATHEDRAL_TOWER_TOP, STONE_DEEP)
    # The crossing: a low block between the nave and the tower.
    tile.rect(nave_left + 20, CATHEDRAL_NAVE_TOP + 4, nave_left + 34, base, STONE_DEEP)
    return [tile]


# -----------------------------------------------------------------------------------------------------------------
# L4: the fields and hedgerows.
# -----------------------------------------------------------------------------------------------------------------

FIELD_BOUNDARIES = [0, 64, 128, 192, 256, 320, 384, 448, 512]
FIELD_COLOURS = [GREEN_LIT, GREEN_MID, GREEN_LIT, GREEN_MID, GREEN_LIT, GREEN_MID, GREEN_LIT, GREEN_MID]
FIELD_OFFSETS = [0, 3, 6, 2, 5, 8, 1, 4]


def field_top(x, index):
    """The top edge of field parcel `index` at column x.

    Each parcel gets its own phase and its own harmonics, so no two tops run parallel and the band
    reads as a patchwork rather than a row of flat slabs. The wave is periodic in 512, so the wrap
    edge looks like any other boundary.
    """
    offset = FIELD_OFFSETS[index % len(FIELD_OFFSETS)]
    phase = 0.7 * index
    wave = (2.0 * math.sin(2.0 * math.pi * x / float(W) + phase)
            + 1.4 * math.sin(2.0 * math.pi * 2 * x / float(W) + phase * 1.7)
            + 0.9 * math.sin(2.0 * math.pi * 3 * x / float(W) + phase * 0.6))
    return max(0, min(20, int(round(2 + offset * 0.6 + wave))))


def build_fields():
    """Patchwork fields with hedgerow lines between them, and oaks standing in the fields.

    The deep green is the backdrop, so an area may add the lit parcel, the mid parcel and the ink
    hedgerow, which is three.
    """
    tile = Tile(W, 56)
    tile.rect(0, 0, W - 1, 55, GREEN_DEEP)

    for index in range(len(FIELD_COLOURS)):
        colour = FIELD_COLOURS[index]
        other = GREEN_MID if colour == GREEN_LIT else GREEN_LIT
        x0 = FIELD_BOUNDARIES[index]
        x1 = FIELD_BOUNDARIES[index + 1]
        for x in range(x0, x1):
            top = field_top(x, index)
            for y in range(top, 32):
                tile.put(x, y, colour)
            # The hedgerow along the top edge of every parcel.
            tile.put(x, top, INK)
            tile.put(x, top + 1, INK)
            # Furrow rows: a 50 percent dither of the neighbouring green.
            for y in range(top + 3, 32, 4):
                if (x + y) % 2 == 0 and tile.get(x, y) == colour:
                    tile.put(x, y, other)

    # The hedgerow lines between the parcels, including across the wrap edge.
    for index in range(1, len(FIELD_BOUNDARIES) - 1):
        x = FIELD_BOUNDARIES[index]
        for y in range(2, 32):
            tile.put(x, y, INK)
            tile.put(x - 1, y, INK)
    for y in range(2, 32):
        tile.put(0, y, INK)
        tile.put(W - 1, y, INK)

    # Two oaks, standing in the fields. A canopy in the deep green and a trunk in the ink.
    for ox in (100, 352):
        tile.rect(ox, 18, ox + 1, 31, INK)
        tile.disc(ox, 14, 6, GREEN_DEEP)
        tile.disc(ox - 4, 17, 4, GREEN_DEEP)
        tile.disc(ox + 4, 17, 4, GREEN_DEEP)
    return [tile]


# -----------------------------------------------------------------------------------------------------------------
# L5: the near verge.
# -----------------------------------------------------------------------------------------------------------------

SIGN_X = 30
SIGN_Y = 26
SIGN_W = 96
SIGN_H = 24
SIGN_POSTS = (SIGN_X + 8, SIGN_X + SIGN_W - 14)


def build_verge():
    """The near verge: the hedge, the dry stone wall, the telegraph poles and the sign posts.

    The mid green is the backdrop, so an area may add the lit crest, the stone wall and the pale
    grass, which is three.
    """
    tile = Tile(W, 92)

    def hedge_top(x):
        return 40 + 3 * math.sin(2.0 * math.pi * x / float(W)) \
                    + 2 * math.sin(2.0 * math.pi * 2 * x / float(W) + 0.7)

    for x in range(W):
        top = int(round(hedge_top(x)))
        tile.column(x, top, 59, GREEN_MID)
        tile.put(x, top, GREEN_LIT)
        if x % 4 == 0:
            tile.put(x, top + 1, GREEN_LIT)

    # The verge grass between the wall and the road. This is the nearest band, so it is the brightest
    # green in the scene, and that is what makes the depth read at a glance.
    tile.rect(0, 74, W - 1, 91, GREEN_PALE)
    for x in range(0, W, 3):
        tile.put(x, 76 + (x % 5), GREEN_LIT)
    for x in range(0, W, 7):
        tile.put(x, 82 + (x % 3), GREEN_LIT)

    # The dry stone wall: staggered blocks with gaps, a dim top course and no mortar colour, so the
    # blocks and the gaps are the only two tones here.
    for block in range(4):
        rng = random.Random(5505 + block)
        x = block * 128
        while x < (block + 1) * 128:
            width = rng.choice([12, 14, 16])
            tile.rect(x, 64, x + width - 1, 73, STONE_MID)
            x += width
    for x in range(0, W, 12):
        tile.put(x, 64 + (x % 3), DIM)

    # Telegraph poles, two per tile, in front of the hedge. They are the ground band's dark green, not the backdrop:
    # a black pole was the one thing in the fields' rows that did not travel with the fields, and the scroll
    # measurement followed it at the verge's speed instead of reading the fields (card t_a1170172).
    for pole_x in (60, 236):
        tile.rect(pole_x, 0, pole_x + 2, 59, GREEN_MID)
        tile.rect(pole_x - 5, 2, pole_x + 7, 3, GREEN_MID)
        tile.rect(pole_x - 5, 6, pole_x + 7, 7, GREEN_MID)
        for x in range(pole_x - 5, pole_x + 8):
            tile.put(x, 1, DIM)
            tile.put(x, 5, DIM)

    # The sign posts. The plate itself is a sprite, because the miles count down on it. The posts are the ground
    # band's dark green rather than the backdrop black: nothing in the title's ground half is drawn in the backdrop,
    # which is the clear, and a black post here was 126 pixels the scroll measurement followed at the verge's speed
    # instead of the fields' (card t_a1170172).
    for post_x in SIGN_POSTS:
        tile.rect(post_x, SIGN_Y + SIGN_H, post_x + 3, 63, GREEN_MID)
    return [tile]


# -----------------------------------------------------------------------------------------------------------------
# L6: the road.
# -----------------------------------------------------------------------------------------------------------------

def build_road():
    """A two lane road with its lane markings.

    The tarmac is the backdrop, so an area may add the bright markings, the dim edge line and the
    green shoulder, which is three.

    Direction B (card ART-B-OPENING) makes two changes here, and both are measured rather than felt. The
    curated palette hands the tarmac $0F black, so nothing may sit below the tarmac and be brighter: any
    band under it counts as a light pixel under a dark one, which ART-STYLE section 2 counts wrong. That is
    why the near verge is not drawn on this strip any more (the foreground layer is the near grass) and why
    the moonlit edge of the far verge is the top row of the strip instead of a line under it. And the chip
    speckle is DIM rather than INK, because the lightning frame lifts every entry a row and the two palettes
    are not ordered the same way: measured 2026-10-27 the ink chips alone put title_L6_road_flash at 5597
    correct against 6435 wrong.
    """
    tile = Tile(W, 44)
    tile.hline(0, W - 1, 0, DIM)          # the lit outer edge of the far verge, against the sky
    tile.rect(0, 1, W - 1, 4, GREEN_MID)  # the verge's own body
    tile.rect(0, 5, W - 1, 40, ASPHALT)
    for y in range(5, 41):
        for x in range(W):
            if ((x % 32) + 2 * (y % 8)) % 13 == 0:
                tile.put(x, y, DIM)
    # The dashed centre line and the continuous edge lines.
    for x in range(0, W, 16):
        tile.rect(x, 12, x + 8, 13, BRIGHT)
    tile.hline(0, W - 1, 6, BRIGHT)
    tile.hline(0, W - 1, 38, BRIGHT)
    tile.rect(0, 41, W - 1, 43, ASPHALT)
    return [tile]


# -----------------------------------------------------------------------------------------------------------------
# L7: the foreground.
# -----------------------------------------------------------------------------------------------------------------

def build_fg():
    """The near grass and the fence posts, which pass in front of the car.

    Direction B (card ART-B-OPENING): the grass is GREEN_DEEP and not INK, and that is a palette fact rather
    than a taste. tools/art/nes_snap.py hands ink $0C and asphalt $0F, so an ink drawing ships as a teal body
    with a BLACK rim on its top edge: the pass had put the light on the wrong side of the material, and
    measured 2026-10-27 the strip read 157 correct light pairs against 655 wrong. GREEN_DEEP ships as $0B and
    its rim as GREEN_MID $0A, so the lit row is brighter than the body it sits on and the strip is correct
    wherever the pass shades it. The posts keep the ground band's mid green for the same reason the sign posts
    do: the backdrop is the clear, not a paint.
    """
    tile = Tile(W, 44)
    for block in range(4):
        rng = random.Random(6606 + block)
        for _ in range(7):
            x = block * 128 + rng.randrange(128)
            blades = rng.randrange(3, 7)
            for blade in range(blades):
                bx = x + blade * 2 - blades
                height = rng.randrange(6, 13)
                for dy in range(height):
                    tile.put(bx + dy // 4, 43 - dy, GREEN_DEEP)

    # The fence posts that pass in front of the car, in the ground band's dark green for the same reason the sign
    # posts are: the backdrop is the clear, not a paint.
    for post_x in (36, 164, 292, 420):
        tile.rect(post_x, 8, post_x + 3, 43, GREEN_MID)
        tile.put(post_x + 3, 8, DIM)
        tile.put(post_x + 3, 20, DIM)
        tile.put(post_x + 3, 34, DIM)
    tile.rect(0, 42, W - 1, 43, GREEN_DEEP)
    return [tile]


# -----------------------------------------------------------------------------------------------------------------
# The sign sprite: a green UK motorway sign, and the miles counting down.
# -----------------------------------------------------------------------------------------------------------------

# Four fixed signs along the real drive from Big Ben to Southampton Docks (OSRM on OpenStreetMap, 2026-10-22):
# 84.7 road miles via A4, M4, M25, M3 (53 miles), M27, A33. The route passes Basingstoke at mile 50.0 and
# Winchester at mile 67.2. The signs stand at miles 30, 42, 55 and 65 from Big Ben, so each shows the miles left
# to the next city and to Southampton. A sign never changes while it is on screen; the next one has smaller
# numbers. UK signs list the destination and the miles, with no unit.
SIGN_TEXTS = [(("BASINGSTOKE", "20"), ("SOUTHAMPTON", "55")),
              (("BASINGSTOKE", "8"), ("SOUTHAMPTON", "43")),
              (("WINCHESTER", "12"), ("SOUTHAMPTON", "30")),
              (("WINCHESTER", "2"), ("SOUTHAMPTON", "20"))]


def sign_plate(top_line, bottom_line):
    """One motorway sign: a green face, a bright border and bright lettering.

    A UK motorway sign is green with white lettering, and this is the same shape: a rounded border, the
    destination on the top line and the distance on the bottom one.
    """
    tile = Tile(SIGN_W, SIGN_H)
    tile.rect(0, 0, SIGN_W - 1, SIGN_H - 1, BRIGHT)
    tile.rect(1, 1, SIGN_W - 2, SIGN_H - 2, GREEN_LIT)
    tile.rect(2, 2, SIGN_W - 3, SIGN_H - 3, GREEN_LIT)
    for y, (name, miles) in ((4, top_line), (13, bottom_line)):
        tile.text(5, y, name, BRIGHT)
        tile.text(SIGN_W - 5 - text_width(miles), y, miles, BRIGHT)
    return tile


def build_signs():
    return [sign_plate(top, bottom) for top, bottom in SIGN_TEXTS]


# -----------------------------------------------------------------------------------------------------------------
# The headlight cone.
# -----------------------------------------------------------------------------------------------------------------

CONE_W = 90
CONE_H = 40


def build_cone():
    """The headlight cone, an overlay the game draws at the car x.

    The beam starts narrow at the lamp and opens onto the road ahead. The dither is dense enough that
    the lit road reads at 1x and the road texture still shows through it.
    """
    tile = Tile(CONE_W, CONE_H)
    for x in range(CONE_W):
        spread = 1 + int((x * 15) / float(CONE_W))
        centre = 18 + int((x * 9) / float(CONE_W))
        for y in range(centre - spread, centre + spread + 1):
            if not (0 <= y < CONE_H):
                continue
            if abs(y - centre) <= max(1, spread - 4):
                tile.put(x, y, BRIGHT)
            elif (x + y) % 2 == 0:
                tile.put(x, y, BRIGHT)
    tile.disc(4, 18, 4, BRIGHT)
    for x in range(6, 22):
        spread = 1 + int((x * 15) / float(CONE_W))
        centre = 18 + int((x * 9) / float(CONE_W))
        for y in range(centre - spread, centre + spread + 1):
            if 0 <= y < CONE_H and abs(y - centre) <= max(1, spread - 5):
                tile.put(x, y, BRIGHT)
    return [tile]


# -----------------------------------------------------------------------------------------------------------------
# The Big Ben opening shot: one 256x240 background.
# -----------------------------------------------------------------------------------------------------------------

BB_W = 256
BB_H = 240
OPENING_NAME = "title_BG_bigben"
TOWER_LEFT = 108
TOWER_RIGHT = 148
TOWER_TOP = 28
TOWER_BASE = 150
CLOCK_CX, CLOCK_CY, CLOCK_R = 128, 66, 15


def build_bigben():
    """Big Ben at night, drawn as one picture for the opening pan.

    The camera pans down from the clock face to the car leaving London, so the tower fills the upper
    half, the Palace runs along the horizon and the road runs off the bottom of the frame.

    Colours: the deep sky is the backdrop, so an area may add the moon and the stars, or the tower
    and its gold clock face, which is three.
    """
    tile = Tile(BB_W, BB_H)
    for y0, y1, colour in ((0, 15, SKY_DEEP), (16, 47, SKY_MID), (48, BB_H - 1, SKY_LOW)):
        tile.band(y0, y1, colour)

    # The moon, high and to the left, and a scatter of stars that keep clear of the tower.
    tile.disc(38, 30, 9, BRIGHT)
    for dx, dy, radius in ((3, -2, 2), (-2, 2, 2)):
        tile.disc(38 + dx, 30 + dy, radius, DIM)
    rng = random.Random(4242)
    for _ in range(90):
        x = rng.randrange(BB_W)
        y = rng.randrange(1, 120)
        if TOWER_LEFT - 8 <= x <= TOWER_RIGHT + 8:
            continue
        tile.put(x, y, DIM if rng.random() < 0.8 else BRIGHT)

    # The Palace of Westminster along the horizon: a run of gables and a few spirelets.
    for x in range(0, BB_W, 24):
        top = 150 - (4 if x % 48 == 0 else 0)
        tile.rect(x, top, x + 23, 186, STONE_DEEP)
        if x % 48 == 0:
            tile.rect(x + 9, top - 12, x + 14, top, STONE_DEEP)
    tile.rect(0, 186, BB_W - 1, 196, STONE_DEEP)

    # The tower: a square shaft with corner turrets, a belfry, the clock face and the spire.
    tile.rect(TOWER_LEFT, TOWER_TOP, TOWER_RIGHT, TOWER_BASE, STONE_DEEP)
    for corner in (TOWER_LEFT, TOWER_RIGHT - 5):
        tile.rect(corner, TOWER_TOP - 8, corner + 5, TOWER_TOP, STONE_DEEP)
    # The belfry arches.
    for dx in (6, 17, 28):
        tile.rect(TOWER_LEFT + dx, TOWER_TOP + 4, TOWER_LEFT + dx + 7, TOWER_TOP + 20, SKY_DEEP)
    # The clock face, gold, with the hands in the silhouette colour.
    tile.disc(CLOCK_CX, CLOCK_CY, CLOCK_R, GOLD)
    tile.disc(CLOCK_CX, CLOCK_CY, CLOCK_R - 1, GOLD)
    tile.rect(CLOCK_CX, CLOCK_CY - 8, CLOCK_CX, CLOCK_CY, STONE_DEEP)
    tile.rect(CLOCK_CX, CLOCK_CY, CLOCK_CX + 6, CLOCK_CY, STONE_DEEP)
    # The spire above the belfry.
    tile.poly([(TOWER_LEFT - 4, TOWER_TOP - 8), (TOWER_RIGHT + 3, TOWER_TOP - 8),
               (TOWER_LEFT + 8, 2), (TOWER_LEFT + 14, 2)], STONE_DEEP)
    tile.rect(TOWER_LEFT + 9, 0, TOWER_LEFT + 13, 4, STONE_DEEP)

    # The road, running off the bottom of the frame, where the car leaves.
    tile.rect(0, 196, BB_W - 1, BB_H - 1, ASPHALT)
    for y in range(197, BB_H):
        for x in range(BB_W):
            if ((x % 32) + 2 * (y % 8)) % 13 == 0:
                tile.put(x, y, INK)
    for x in range(0, BB_W, 16):
        tile.rect(x, 214, x + 8, 215, BRIGHT)
    return [tile]


# -----------------------------------------------------------------------------------------------------------------
# The layer table and the assembly.
# -----------------------------------------------------------------------------------------------------------------

LAYERS = [
    {"name": "title_L1_sky", "builder": build_sky, "width": W, "height": 120, "frames": 2, "fps": 2,
     "y": 0, "speed": 0.0},
    {"name": "title_L2_clouds", "builder": build_clouds, "width": W, "height": 120, "frames": 1, "fps": 0,
     "y": 0, "speed": 0.05},
    # Every band sits on a 16 pixel boundary, because that is the only alignment where a strip's own attribute
    # areas and the areas of the composed screen are the same areas. At y 92 the downs band began 12 rows into an
    # area, so one 16x16 block of the strip carried pixels from two screen areas and no single palette could
    # satisfy both: the strip failed, and so did the frame. 96, 128, 128 and 192 are the same picture moved by at
    # most eight pixels onto the PPU's grid (measured 2026-10-22: title_L5_verge 8 areas, title_L6_road 32 areas,
    # and the composed frame 44 areas, all of them at a misaligned band edge).
    {"name": "title_L3_downs", "builder": build_downs, "width": W, "height": 48, "frames": 1, "fps": 0,
     "y": 96, "speed": 0.15},
    {"name": "title_L4_fields", "builder": build_fields, "width": W, "height": 56, "frames": 1, "fps": 0,
     "y": 128, "speed": 0.35},
    {"name": "title_L5_verge", "builder": build_verge, "width": W, "height": 96, "design_height": 92,
     "frames": 1, "fps": 0, "y": 128, "speed": 0.7},
    {"name": "title_L6_road", "builder": build_road, "width": W, "height": 48, "design_height": 44,
     "frames": 1, "fps": 0, "y": 192, "speed": 1.0},
    {"name": "title_L7_fg", "builder": build_fg, "width": W, "height": 48, "design_height": 44,
     "frames": 1, "fps": 0, "y": 192, "speed": 1.3},
    {"name": "title_BG_bigben", "builder": build_bigben, "width": BB_W, "height": BB_H, "frames": 1,
     "fps": 0, "y": 0, "speed": 0.0},
]

SPRITES = [
    {"name": "spr_title_sign", "builder": build_signs, "width": SIGN_W, "height": SIGN_H, "frames": 4,
     "fps": 0},
    {"name": "spr_title_cone", "builder": build_cone, "width": CONE_W, "height": CONE_H, "frames": 1,
     "fps": 0},
]


def strip_image(tiles):
    width = tiles[0].w
    height = tiles[0].h
    strip = Image.new("RGBA", (width * len(tiles), height), (0, 0, 0, 0))
    for index, tile in enumerate(tiles):
        strip.paste(tile.image(), (index * width, 0))
    return strip


def pad_to_grid(image, transparent=False):
    """Grow an image to a whole number of 8x8 tiles.

    The PPU can only draw whole tiles, so a strip 44 or 92 pixels tall cannot exist on the cartridge and
    the checker fails it on the grid rule. A background grows by repeating its own last row and column,
    which keeps the picture continuous and opaque (a background has no transparency); a sprite grows with
    transparent pixels, because a sprite tile's entry 0 is transparent.
    """
    width, height = image.size
    new_w = (width + 7) // 8 * 8
    new_h = (height + 7) // 8 * 8
    if (new_w, new_h) == (width, height):
        return image
    out = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
    out.paste(image, (0, 0))
    if transparent:
        return out
    source = image.load()
    pixels = out.load()
    for y in range(height, new_h):
        for x in range(width):
            pixels[x, y] = source[x, height - 1]
    for x in range(width, new_w):
        for y in range(new_h):
            pixels[x, y] = pixels[width - 1, y]
    return out


def save_png(image, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path, format="PNG", optimize=False)


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def seam_metric(image):
    """Outlier test for the wrap edge, on pixels rather than indices. A strip is seamless when the step
    from its last column back to its first is no worse than the sharpest step the image already contains
    internally."""
    pixels = image.load()

    def delta(a, b):
        if a[3] == 0 and b[3] == 0:
            return 0
        if a[3] == 0 or b[3] == 0:
            return 255
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))

    interior_max = 0
    for y in range(image.height):
        for x in range(image.width - 1):
            interior_max = max(interior_max, delta(pixels[x, y], pixels[x + 1, y]))

    wrap_max = 0
    for y in range(image.height):
        wrap_max = max(wrap_max, delta(pixels[image.width - 1, y], pixels[0, y]))
    return wrap_max, interior_max


def guard_strip(path):
    """Run the dither rule on one shipped strip, frame by frame, and write it back only when it changed.

    The frame width comes from the strip's own sidecar, because a checker must not be counted across the
    seam between two frames of a strip: the two frames are different pictures drawn side by side.
    Returns the number of pixels changed.
    """
    sidecar = os.path.splitext(path)[0] + ".json"
    width = None
    if os.path.isfile(sidecar):
        with open(sidecar, "r", encoding="utf-8-sig") as handle:
            meta = json.load(handle)
        width = meta.get("frame_w")
    with Image.open(path) as handle:
        strip = handle.convert("RGBA")
    if not width:
        width = strip.width
    art_dir = os.path.dirname(os.path.abspath(__file__))
    if art_dir not in sys.path:
        sys.path.insert(0, art_dir)
    import style_b
    frames = strip.width // width
    out = strip.copy()
    changed = 0
    for index in range(frames):
        box = (index * width, 0, (index + 1) * width, strip.height)
        fixed, moved = style_b.flatten_self(strip.crop(box))
        if moved:
            out.paste(fixed, (box[0], 0))
            changed += moved
    if changed:
        save_png(out, path)
    return changed


def strip_images(images):
    """One animation strip out of the per frame images, in order."""
    width = images[0].width
    height = images[0].height
    strip = Image.new("RGBA", (width * len(images), height), (0, 0, 0, 0))
    for index, image in enumerate(images):
        strip.paste(image, (index * width, 0))
    return strip


def image_colours(image, index_of):
    """The master palette indices this image actually draws with. Transparent pixels are not counted."""
    used = set()
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            index = index_of.get((r, g, b))
            if index is not None:
                used.add(index)
    return used


def flash_image(image, index_of, colours, mapping):
    """The same picture with every colour one step up its own hue ramp: the lightning frame."""
    out = image.copy()
    pixels = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            index = index_of.get((r, g, b))
            if index is None:
                continue
            pixels[x, y] = colours[mapping.get(index, index)] + (255,)
    return out


def enforce_opening(image, root, spec):
    """Put the opening shot onto four background palettes.

    The opening shot is one still frame, drawn from its own colours: measured 2026-10-22 it needs five background
    palettes, one more than the PPU has, so no arrangement of its areas is legal even though every area is. The
    frame is a separate screen from the drive (the drive is under it and visible only after the pan), so its
    palettes do not have to be the drive's: what it needs is four that fit ITS picture. tools/nes_enforce.py picks
    the four palettes that misrepresent the fewest pixels, snaps every pixel to the nearest legal entry, and
    returns the frame the NES would show after the same conversion. The chosen backdrop goes into the sidecar, so
    the audit measures the areas against the backdrop the frame actually uses instead of guessing one.
    """
    import nes_composite_check
    import nes_enforce
    palette = nes_composite_check.load_palette(nes_composite_check.default_palette_path(root))
    result = nes_enforce.enforce(image, palette)
    spec["frame_backdrop"] = result["backdrop"]
    spec["opening_palettes"] = result["palettes"]
    print("opening shot: %d background palettes onto the PPU's four, backdrop %s, %d attempt(s)"
          % (len(result["palettes"]), result["backdrop"], result["attempts"]))
    return result["frame"]


def compose(layers, camera_x, cone_at=None, cone_image=None, sign_index=0, sign_image=None):
    """One 256x240 frame; each layer shifted by its own scroll speed."""
    frame = Image.new("RGBA", (SCREEN_W, SCREEN_H), (0, 0, 0, 255))
    for spec in layers:
        image = spec["frames"][0]
        offset = int(round(camera_x * spec["speed"])) % W
        strip = Image.new("RGBA", (W * 2, image.height), (0, 0, 0, 0))
        strip.paste(image, (0, 0))
        strip.paste(image, (W, 0))
        window = strip.crop((offset, 0, offset + SCREEN_W, image.height))
        frame.alpha_composite(window, (0, spec["y"]))
    if sign_image is not None:
        verge = next(spec for spec in layers if spec["name"] == "title_L5_verge")
        offset = int(round(camera_x * verge["speed"])) % W
        for shift in (-W, 0, W):
            x = SIGN_X - offset + shift
            if -SIGN_W < x < SCREEN_W:
                frame.alpha_composite(sign_image, (x, verge["y"] + SIGN_Y))
    if cone_at is not None and cone_image is not None:
        frame.alpha_composite(cone_image, (cone_at, 200))
    return frame


def rebuild_flash(root: str) -> int:
    """Rewrite the *_flash strips from the layer PNGs as they are on disk right now.

    The flash strips are the same picture one rung up the 2C02 ladder, and they are derived data: if the base
    strip is repainted afterwards, the flash is a picture of a palette the base no longer uses. That is what
    happened when tools/art/scene_palette.py enforced the layers after this generator had already lifted them
    (measured 2026-10-22: title_L1_sky_flash drew entries [0,16,33,34,48] while the enforced sky's lift is
    [0,16,28,33,34,48], so tests/test_make_title_world.py correctly failed). Reading the base back off disk and
    lifting it here means the two can never disagree, whatever order the tools ran in.
    """
    sys.path.insert(0, os.path.join(root, "tools", "art"))
    sys.path.insert(0, os.path.join(root, "tools"))
    import nes_snap

    snap = nes_snap.Snap(root)
    master_index_of = {}
    for index, rgb in enumerate(snap.master):
        if snap.usable[index] and rgb not in master_index_of:
            master_index_of[rgb] = index
    for index, rgb in enumerate(snap.master):
        master_index_of.setdefault(rgb, index)

    with open(os.path.join(root, "data", "title.json"), "r", encoding="utf-8-sig") as handle:
        table = json.load(handle)
    names = [row["name"] for row in table["layers"]]
    names += [row["name"] for row in table.get("backgrounds", [])]
    for key in ("sign", "cone"):
        if table.get(key, {}).get("name"):
            names.append(table[key]["name"])

    bases = {}
    for name in names:
        png = os.path.join(root, "game", "sprites_src", "title", name + ".png")
        meta_path = os.path.join(root, "game", "sprites_src", "title", name + ".json")
        if not (os.path.isfile(png) and os.path.isfile(meta_path)):
            continue
        with Image.open(png) as handle:
            bases[name] = handle.convert("RGBA").copy()

    used = set()
    for image in bases.values():
        for r, g, b, a in image.getdata():
            if a:
                entry = master_index_of.get((r, g, b))
                if entry is not None:
                    used.add(entry)
    flash = nes_snap.flash_map(used)

    written = 0
    for name, base in bases.items():
        meta_path = os.path.join(root, "game", "sprites_src", "title", name + ".json")
        with open(meta_path, "r", encoding="utf-8-sig") as handle:
            meta = json.load(handle)
        transparent = 0 if meta.get("kind") == "sprite" else 0
        lifted = nes_snap.flash_image(base, master_index_of, snap.master, flash, transparent=transparent)
        out = os.path.join(root, "game", "sprites_src", "title", name + "_flash.png")
        lifted.save(out, "PNG")
        sidecar = dict(meta)
        sidecar["name"] = name + "_flash"
        with open(os.path.join(root, "game", "sprites_src", "title", name + "_flash.json"), "w",
                  encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(sidecar, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        written += 1

    flash_path = os.path.join(root, "data", "title_flash.json")
    if os.path.isfile(flash_path):
        with open(flash_path, "r", encoding="utf-8-sig") as handle:
            flash_data = json.load(handle)
        flash_data["palette"] = {str(index): value for index, value in flash.items()}
        with open(flash_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(flash_data, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=ROOT)
    parser.add_argument("--no-scene-pass", action="store_true",
                        help="draw only; skip the scene palette pass at the end (used when the whole art pass is "
                             "redrawn and the scene is solved once, after every strip and sprite exists)")
    args = parser.parse_args()

    sys.path.insert(0, os.path.join(args.root, "tools", "art"))
    sys.path.insert(0, os.path.join(args.root, "tools"))
    import nes_bg
    import nes_snap
    import style_b

    colours, index_of = nes_bg.load_palette(args.root)

    # The strips are drawn in the project palette and written in the master palette. nes_snap holds the
    # curated table and the reason for it; what lands on disk is what the PPU can show.
    snap = nes_snap.Snap(args.root)
    # A usable entry wins over a forbidden duplicate: the master palette repeats black eight times and
    # only $0F may be drawn with, so a naive rgb-to-entry table would file black under $3F and the area
    # check would then read the backdrop as a colour of its own.
    master_index_of = {}
    for index, rgb in enumerate(snap.master):
        if snap.usable[index] and rgb not in master_index_of:
            master_index_of[rgb] = index
    for index, rgb in enumerate(snap.master):
        master_index_of.setdefault(rgb, index)

    records = []
    colour_report = []
    seam_report = []
    built = {}

    def emit(spec, images, suffix="", transparent=False):
        # The last step before disk: every pixel onto a real 2C02 output. The strips are drawn in the
        # project palette, which is pleasant to paint with but is not what the PPU can show, so what is
        # written, and what the validator and the runtime see, is the snapped picture.
        images = [snap.image(pad_to_grid(image, transparent)) for image in images]
        if suffix:
            spec["snapped_flash"] = images
        else:
            spec["snapped"] = images
        name = spec["name"] + suffix
        strip = strip_images(images)
        path = os.path.join(SPRITE_DIR, name + ".png")
        save_png(strip, path)
        meta = {
            "name": name,
            "frame_w": images[0].width,
            "frame_h": images[0].height,
            "frames": len(images),
            "fps": spec["fps"],
        }
        if spec.get("frame_backdrop"):
            # The opening shot is measured on its own, so it declares the backdrop its four palettes are built
            # around. Without it the checker guesses the most common colour, and a night sky with a black sky and
            # a black tower shadow can outvote it.
            meta["backdrop"] = spec["frame_backdrop"]
        save_json(os.path.join(SPRITE_DIR, name + ".json"), meta)
        used = set()
        for image in images:
            used.update(image_colours(image, master_index_of))
        colour_report.append((name, sorted(used), suffix != ""))
        seam_report.append((name,) + seam_metric(images[0]))
        records.append(path)
        return path

    # ---- the layers, solved onto the NES background rule -------------------------------------------------
    for spec in LAYERS:
        tiles = spec["builder"]()
        # The builder draws the design height; the table's `height` is the height that ships, which is that
        # design height rounded up to whole 8x8 tiles. Title.json promises the shipped one, so the screen
        # and the strip cannot disagree by the padding rows.
        design_height = spec.get("design_height", spec["height"])
        for tile in tiles:
            if tile.w != spec["width"] or tile.h != design_height:
                raise SystemExit("%s: built %dx%d, the table says %dx%d"
                                 % (spec["name"], tile.w, tile.h, spec["width"], design_height))
        backdrop = LAYER_BACKDROP[spec["name"]]
        priority = LAYER_PRIORITY[spec["name"]]
        # Direction B (card ART-B-OPENING): the polish pass runs on the DRAWING and before the 16x16 solver,
        # so the solver's three colours per area are spent on the tones the pass placed. Section 4 of
        # knowledge/ART-STYLE.md is what the pass implements, tools/art/style_b.py is where it lives, and the
        # numbers it moved are printed below and carried in the manifest, so the change is measured and not
        # asserted.
        style_b_report = [style_b.measure(tiles[0].w, tiles[0].h, tiles[0].px)]
        for tile in tiles:
            tile.px = style_b.apply(tile.w, tile.h, tile.px)
        style_b_report.append(style_b.measure(tiles[0].w, tiles[0].h, tiles[0].px))
        spec["style_b"] = style_b_report
        # The solver runs on the pixel image, because the rule is about pixels, not about indices. What it
        # returns is what gets written: the strip on disk is the solved strip, never the raw drawing.
        solved = []
        changed = 0
        for tile in tiles:
            image = tile.image()
            image, moved = nes_bg.reduce_areas(image, index_of, colours,
                                               backdrop=backdrop, limit=3, priority=priority)
            changed += moved
            solved.append(image)
        # Direction B, second half (card ART-B-OPENING): the solver can merge a fourth tone down into a 2x2
        # checker that the pass itself never drew, and ART-STYLE section 2 counts those. So the shipped
        # strip is compared against the SAME drawing solved WITHOUT the pass, and every checker pixel is
        # put back to the tone that drawing always had. Measured on 2026-10-27 against HEAD: title_BG_bigben
        # went 0 -> 156 checker patches in the strip while the pass reported none.
        plain = []
        for tile in spec["builder"]():
            image = tile.image()
            image, _moved = nes_bg.reduce_areas(image, index_of, colours,
                                                backdrop=backdrop, limit=3, priority=priority)
            plain.append(image)
        restored = 0
        for index, image in enumerate(solved):
            solved[index], took = style_b.flatten_image(image, plain[index])
            restored += took
        spec["dither_restored"] = restored
        spec["frames"] = solved
        spec["tiles"] = tiles
        spec["solver_changes"] = changed
        if spec["name"] == OPENING_NAME:
            solved = [enforce_opening(solved[0], args.root, spec)]
        emit(spec, solved)
        built[spec["name"]] = spec

    # The sign and the cone are sprites, so the 8x8 rule applies and not the 16x16 one.
    for spec in SPRITES:
        tiles = spec["builder"]()
        for tile in tiles:
            if tile.w != spec["width"] or tile.h != spec["height"]:
                raise SystemExit("%s: built %dx%d, the table says %dx%d"
                                 % (spec["name"], tile.w, tile.h, spec["width"], spec["height"]))
        spec["tiles"] = tiles
        # Direction B is applied to the background layers and NOT to these two sprites. A sprite holds its
        # own three entry row on the PPU and no backdrop, so a pass that adds a tone to the sign or the
        # cone spends a fourth entry that no row holds, and tools/check_scene_palettes.py says so:
        # measured on 2026-10-26, "spr_title_sign has 96 group(s) whose colours fit none of the four
        # sprite palettes". The sign and the cone stay as drawn; their outline and their three tones are
        # a sprite palette job with its own card, not a background job with a generic pass.
        spec["style_b"] = [style_b.measure(tiles[0].w, tiles[0].h, tiles[0].px)]
        spec["style_b"].append(spec["style_b"][0])
        images = [tile.image() for tile in tiles]
        spec["frames"] = images
        emit(spec, images, transparent=True)
        built[spec["name"]] = spec

    # ---- the flash palette, and the strips drawn with it ------------------------------------------------
    # The flash happens in master space, because that is where the PPU's own ladder lives: every entry in
    # use climbs one rung ($0C to $1C, $02 to $12), so the alternate palette is a real palette swap and
    # not a brightening the chip could not do.
    used_colours = sorted(set(i for _name, used, is_flash in colour_report if not is_flash for i in used))
    flash = nes_snap.flash_map(used_colours)
    for spec in LAYERS:
        emit(spec, [nes_snap.flash_image(image, master_index_of, snap.master, flash)
                    for image in spec["snapped"]], suffix="_flash")
    for spec in SPRITES:
        emit(spec, [nes_snap.flash_image(image, master_index_of, snap.master, flash)
                    for image in spec["snapped"]], suffix="_flash", transparent=True)

    # ---- the data files ----------------------------------------------------------------------------------
    # The seven scrolling layers and the one still background are two different things to the screen: the
    # drive scrolls the layers, the opening shot is a single picture the camera pans over. Keeping them in
    # separate lists is what stops the runtime drawing Big Ben on top of the drive.
    scrolling = [spec for spec in LAYERS if spec["name"] != OPENING_NAME]
    title_data = {
        "format": 1,
        "kind": "title",
        "layers": [
            {"name": spec["name"], "y": spec["y"], "speed": spec["speed"], "role": "background",
             "backdrop": snap.master_index(LAYER_BACKDROP[spec["name"]]), "frames": len(spec["frames"])}
            for spec in scrolling
        ],
        "backgrounds": [
            {"name": spec["name"], "role": "background",
             "backdrop": snap.master_index(LAYER_BACKDROP[spec["name"]]),
             "frames": len(spec["frames"])}
            for spec in LAYERS if spec["name"] == OPENING_NAME
        ],
        "sign": {"name": "spr_title_sign", "x": SIGN_X, "y": SIGN_Y, "frames": len(SIGN_TEXTS)},
        "cone": {"name": "spr_title_cone", "x": 140, "y": 200},
        "opening": {"name": OPENING_NAME, "width": BB_W, "height": BB_H},
        "flash": {"name": "title_flash", "file": "title_flash.json", "frames": 2},
        "palette_space": "2C02 entry numbers (data/nes_palette.json); every pixel on disk is one of these",
    }
    save_json(os.path.join(DATA_DIR, "title.json"), title_data)

    flash_data = {
        "format": 1,
        "kind": "title_flash",
        "frames": 2,
        "note": "one rung up the 2C02 ladder per entry ($0C to $1C, $02 to $12, black $0F to grey $00); "
                "the game swaps the whole scene to these entries for two frames",
        "palette_space": "2C02 entry numbers (data/nes_palette.json)",
        "palette": {str(index): value for index, value in flash.items()},
        "layers": [spec["name"] + "_flash" for spec in LAYERS],
    }
    save_json(os.path.join(DATA_DIR, "title_flash.json"), flash_data)

    # ---- the previews -----------------------------------------------------------------------------------
    layer_specs = []
    for spec in LAYERS:
        if spec["name"] == OPENING_NAME:
            continue
        layer_specs.append({"name": spec["name"], "y": spec["y"], "speed": spec["speed"],
                            "frames": spec["snapped"]})
    sign_image = built["spr_title_sign"]["snapped"][0]
    cone_image = built["spr_title_cone"]["snapped"][0]
    preview = compose(layer_specs, camera_x=0.0, cone_at=140, cone_image=cone_image,
                      sign_image=sign_image)
    preview_path = os.path.join(OUT_DIR, "ts2_world_preview.png")
    save_png(preview.resize((SCREEN_W * 3, SCREEN_H * 3), Image.NEAREST), preview_path)
    records.append(preview_path)

    bigben = built["title_BG_bigben"]["snapped"][0]
    bigben_path = os.path.join(OUT_DIR, "ts2_bigben_preview.png")
    save_png(bigben.resize((BB_W * 3, BB_H * 3), Image.NEAREST), bigben_path)
    records.append(bigben_path)

    # ---- the checks --------------------------------------------------------------------------------------
    problems = []
    room_colours = set()
    flash_room_colours = set()
    for name, used, is_flash in colour_report:
        (flash_room_colours if is_flash else room_colours).update(used)
        for index in used:
            if index >= len(snap.master):
                problems.append("%s uses entry %02X, outside the 2C02 palette" % (name, index))
    # The budget is per screen state, because the palette is reloaded for the flash: a frame is drawn
    # from the night palette or from the flash palette, never from both at once.
    for label, seen in (("the night frame", room_colours), ("the flash frame", flash_room_colours)):
        if len(seen) > 16:
            problems.append("%s uses %d colours, the limit is 16" % (label, len(seen)))
    if flash_room_colours != set(flash.values()):
        problems.append("the flash strips draw %s but the flash palette says %s"
                        % (sorted(flash_room_colours), sorted(set(flash.values()))))
    for name, wrap_max, interior_max in seam_report:
        if wrap_max > interior_max:
            problems.append("%s wrap step %d is sharper than its own interior max %d"
                            % (name, wrap_max, interior_max))

    # The background rule, checked with the checker and not with the solver, on the pixels that ship.
    # The flash frames are held to it too, against the flash backdrop, because the cartridge draws them
    # from a reloaded palette whose backdrop is the lifted entry.
    for spec in LAYERS:
        backdrop = snap.master_index(LAYER_BACKDROP[spec["name"]])
        flash_backdrop = nes_snap.flash_step(backdrop)
        for index, image in enumerate(spec["snapped"]):
            bad = nes_bg.check_areas(image, master_index_of, backdrop)
            for cx, cy, found in bad:
                problems.append("%s frame %d area %d,%d carries %d colours %s"
                                % (spec["name"], index, cx, cy, len(found), found))
        for index, image in enumerate(spec["snapped_flash"]):
            flash_bad = nes_bg.check_areas(image, master_index_of, flash_backdrop)
            for cx, cy, found in flash_bad:
                problems.append("%s flash frame %d area %d,%d carries %d colours %s"
                                % (spec["name"], index, cx, cy, len(found), found))

    manifest = {
        "spec": "PLAN-V2-2026-10-21.md section 2, specs/14-title-screen-drive.md, data/title.json",
        "generator": "tools/art/make_title_world.py",
        "font_source": FONT_SOURCE,
        "frame": [SCREEN_W, SCREEN_H],
        "car_x": [76, 140],
        "cone_at": 140,
        "sign": {"x": SIGN_X, "y": SIGN_Y, "frames": len(SIGN_TEXTS)},
        "room_colours": sorted(room_colours),
        "flash_room_colours": sorted(flash_room_colours),
        "palette_space": "2C02 entry numbers (data/nes_palette.json)",
        "flash_palette": flash,
        "backdrop_master": {spec["name"]: snap.master_index(LAYER_BACKDROP[spec["name"]])
                            for spec in LAYERS},
        "snap_table": {str(source): target for source, target in sorted(snap.table.items())},
        "compose": [{"name": spec["name"], "y": spec["y"], "height": spec["height"],
                     "speed": spec["speed"]} for spec in LAYERS],
        "solver_changes": {spec["name"]: spec["solver_changes"] for spec in LAYERS},
        "style_b": {spec["name"]: {"before": spec["style_b"][0], "after": spec["style_b"][1]}
                    for spec in list(LAYERS) + list(SPRITES)},
        "style_b_pass": "tools/art/style_b.py, direction B of knowledge/ART-STYLE.md section 4",
        "files": [],
    }
    for path in records:
        manifest["files"].append({
            "name": os.path.basename(path),
            "bytes": os.path.getsize(path),
            "sha256": sha256(path),
        })
    manifest_path = os.path.join(OUT_DIR, "ts2_world_manifest.json")
    save_json(manifest_path, manifest)

    print("TS2-ART-B: the v2 night title world")
    print("font source: %s" % FONT_SOURCE)
    for name, used, is_flash in colour_report:
        print("  %-26s %2d palette colours: %s" % (name, len(used), used))
    print("title art colours: %d of 16 in the night frame, %d of 16 in the flash frame"
          % (len(room_colours), len(flash_room_colours)))
    print("solver changes per layer (pixels the 16x16 rule moved):")
    for spec in LAYERS:
        print("  %-22s %d" % (spec["name"], spec["solver_changes"]))
    print("checker pixels put back by the dither guard (strip against the same drawing solved without the pass):")
    for spec in LAYERS:
        print("  %-22s %d" % (spec["name"], spec.get("dither_restored", 0)))
    print("direction B pass (three tone areas before -> after, rim lights with a mid tone below or right):")
    for spec in list(LAYERS) + list(SPRITES):
        before, after = spec["style_b"]
        print("  %-22s areas 3 tones %3d -> %3d of %3d   rims %d/%d -> %d/%d   dither %d -> %d"
              % (spec["name"], before["areas_with_three_tones"], after["areas_with_three_tones"],
                 after["areas"], before["lit_correct"], before["lit_correct"] + before["lit_wrong"],
                 after["lit_correct"], after["lit_correct"] + after["lit_wrong"],
                 before["dither_patches"], after["dither_patches"]))
    print("seam check (wrap max step, interior max step):")
    for name, wrap_max, interior_max in seam_report:
        print("  %-22s %4d %4d" % (name, wrap_max, interior_max))
    print("flash palette (2C02 entries, one rung up):")
    for index, value in flash.items():
        print("  $%02X -> $%02X  #%02x%02x%02x -> #%02x%02x%02x"
              % (index, value, *snap.master[index], *snap.master[value]))
    print("files:")
    for path in records + [manifest_path]:
        print("  %s  %s  %d bytes" % (sha256(path)[:16],
                                      os.path.relpath(path, ROOT).replace("\\", "/"),
                                      os.path.getsize(path)))
    if problems:
        for problem in problems:
            print("FAIL: " + problem)
        return 1
    print("checks: colour budget ok, seam ok, 16x16 background rule ok")
    # The scene palette pass runs last, after the strips are on disk, because it measures the whole
    # composed screen: four background palettes of three entries each, one palette per 16x16 area. A
    # layer that passes on its own can still break the frame, which is exactly what happened on
    # 2026-10-21, so the frame is what this last step solves for. data/palettes/scene_title.json holds
    # the budget; scene_palette.py enforces it; tools/nes_composite_check.py checks the pixels after.
    import scene_palette
    if args.no_scene_pass:
        return 0
    report = scene_palette.apply_title(args.root)
    print("scene palettes: %d pixels rewritten into the four background palettes (pass 1), %d (pass 2)"
          % (report["passes"][0]["pixels_moved"], report["passes"][1]["pixels_moved"]))
    # Card t_a1170172: the flash twin is now the same picture lifted inside the band palette, so the flash table has
    # to be read back off the strips that shipped rather than off the 2C02 ladder it was written from. Anything else
    # is a table that describes a swap the game does not make.
    # Card t_a1170172: the flash table is no longer computed here. title_bands.apply, which runs inside the scene
    # pass above and writes the flash twins, also writes data/title_flash.json from the two sheets of every strip,
    # because the lift is per band and one table over entries cannot describe it. The file written earlier in this
    # function is the placeholder until that pass runs.
    print("flash table: read back off the strips by the band pass (title_bands.apply)")
    # Card ART-B-OPENING, the last half of the dither guard. Everything above runs AFTER the direction B
    # pass: the scene palette pass rewrites pixels into the four background palettes and the band lift
    # writes the flash twins, and a colour merge in either can land as a 2x2 checker that neither the pass
    # nor the solver drew. So the section 2 rule is measured on the strips that SHIP, and every checker
    # pixel is set to its own 2x2 partner, which is a tone the same 16x16 area already spends. Sprite
    # sheets are not touched: the cone's hatch (299 patches in HEAD) and the sign's dither (68) are drawn
    # on purpose and are not this card's assets.
    flattened = {}
    for spec in LAYERS:
        for name in (spec["name"], spec["name"] + "_flash"):
            path = os.path.join(SPRITE_DIR, name + ".png")
            if not os.path.isfile(path):
                continue
            moved = guard_strip(path)
            if moved:
                flattened[name] = moved
    print("dither guard on the shipped strips (checker pixels set to their own partner): %s"
          % (", ".join("%s %d" % (item, count) for item, count in sorted(flattened.items())) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
