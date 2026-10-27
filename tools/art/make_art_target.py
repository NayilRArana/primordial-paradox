#!/usr/bin/env python3
"""make_art_target.py: one frame, three art directions, drawn to the hardware limits.

Card PP-ART-TARGET (t_0e56c7c7). Nayil, 2026-10-26: "I don't think the art style is of high enough
quality." The demo is 25 of 100 points and the first 10 seconds are art, so the choice of a style is
worth more than any single asset. This tool draws the SAME frame three ways so the choice is between
treatments of one picture, not between three compositions.

The frame
    Zeus (Zander Skye, 19) and Kronos (Konrad Skye, 40s) in the Montefiore halls room, the move-in
    room the intro cutscene opens in. 256x240, the PPU's own picture size. The room never moves
    between the three directions: same window, same door, same floor, same two figures at the same
    two positions. Only the drawing treatment changes.

    A  Earthbound Beginnings (Mother on the NES): big heads, simple shapes, warm wall.
    B  Late NES polish (Kirby's Adventure, Little Samson): bold dark outlines, three tone shading lit
       from the top left, detailed tiles.
    C  Undertale clarity in colour: very clean silhouettes, little shading, strong expressions.

The limits this tool enforces itself, before any checker sees the file
    1. 2C02 only. Every pixel is one of the 64 outputs in data/nes_palette.json, and never a forbidden
       entry (the $0D black and the duplicate blacks other than $0F).
    2. Four background palettes of three entries, plus the one shared backdrop ($0F). Each 16x16
       attribute area may only use the three entries of ITS palette plus the backdrop.
    3. Four sprite palettes of three entries, plus transparency. Each 8x16 OAM entry may only use the
       three entries of ONE of the four palettes; the figure is drawn so its row bands fall on the
       OAM grid, which is what makes that true rather than hoped for.
    4. 8x16 sprite objects, at most 8 per scanline and 64 per frame.
    5. At most 25 distinct colours in the frame.
    6. The cleanup rules the card names: a 1 pixel dark outline round every character, no orphan pixel,
       no dithering unless it is a deliberate pattern, light from the top left.

    A rule this tool cannot check is written as a measured number instead: the outline is drawn by a
    dilation pass, and the count of filled pixels that touch the background without being the outline
    colour is printed and must be zero.

Every shape here is generated from numbers in this file. No sprite, tile, palette or layout was taken
from any published game: the two reference directions are named for their drawing conventions (head
size, outline weight, shading steps, tile detail), and every pixel below is new.

Usage
    python tools/art/make_art_target.py                 draw A, B and C into output/art_target/
    python tools/art/make_art_target.py --style A       one direction only
    python tools/art/make_art_target.py --sheet         also build output/art_target/ART-TARGET-SHEET.png
    python tools/art/make_art_target.py --report        print the measured table and exit

Exit codes
    0  every frame was drawn and passed every rule in this file
    1  a rule failed (the offending area, OAM entry or colour is printed)
    2  an input could not be read
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PALETTE_PATH = os.path.join(ROOT, "data", "nes_palette.json")
FONT_PATH = os.path.join(ROOT, "assets", "fonts", "PressStart2P-Regular.ttf")
OUT_DIR = os.path.join(ROOT, "output", "art_target")

FRAME_W = 256
FRAME_H = 240
TILE = 8
AREA = 16
OAM_W = 8
OAM_H = 16
BACKDROP = 15
MAX_COLOURS = 25
MAX_SPRITES_PER_LINE = 8
MAX_SPRITES = 64

# -----------------------------------------------------------------------------------------------------------------
# The chip palette.


def load_palette(path=PALETTE_PATH):
    """Return (rgb_by_index, usable_indices, code_by_index) from data/nes_palette.json."""
    with open(path, "r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    rgb = {}
    code = {}
    usable = []
    for entry in data["entries"]:
        value = entry["hex"].lstrip("#")
        rgb[entry["index"]] = (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))
        code[entry["index"]] = entry["code"]
        if entry["usable"]:
            usable.append(entry["index"])
    return rgb, set(usable), code


RGB, USABLE, CODE = load_palette()
RGB_TO_INDEX = {}
for _index in sorted(USABLE):
    RGB_TO_INDEX.setdefault(RGB[_index], _index)

# -----------------------------------------------------------------------------------------------------------------
# The four background palettes and the four sprite palettes, per direction.
#
# A palette is a dict of three roles, so the drawing code never names a colour number twice. The wall is the one
# thing that differs in hue between the directions: A and C are a warm halls-room cream, B is the cold grey plaster
# the late-NES look wants under bold outlines. The characters keep their own four triples in all three directions,
# because the choice on the table is a treatment, not a redesign of two people.

BG_WARM = {"light": 32, "mid": 55, "dark": 39}      # $20 white, $37 cream, $27 light orange
BG_COLD = {"light": 32, "mid": 16, "dark": 0}       # $20 white, $10 grey, $00 grey
# The glass palette is the sky, never the frame: the frame is the pale entry, the lit sky the pale azure and the
# shaded sky the azure, so a pane can never read as an empty hole in the wall.
BG_GLASS = {"light": 49, "mid": 33, "dark": 48}     # $31 pale azure, $21 azure, $30 white frame
BG_FLOOR = {"light": 40, "mid": 24, "dark": 8}      # $28 pale gold, $18 olive, $08 dark brown
BG_FIX = {"light": 32, "mid": 16, "dark": 0}        # $20 white, $10 grey, $00 grey (door)

SPR_ZEUS_HEAD = (15, 54, 40)   # $0F ink, $36 skin, $28 gold blond hair
SPR_ZEUS_BODY = (15, 33, 2)    # $0F ink, $21 azure bomber, $02 navy jeans
SPR_KRONOS_HEAD = (15, 54, 56)  # $0F ink, $36 skin, $38 pale gold hair (blond, going white at the ends)
SPR_KRONOS_BODY = (15, 45, 16)  # $0F ink, $2D charcoal coat, $10 light grey shirt and collar

STYLES = {
    "A": {
        "key": "A",
        "name": "EARTHBOUND BEGINNINGS",
        "subtitle": "big heads, simple shapes, warm",
        "wall": BG_WARM,
        "glass": BG_GLASS,
        "floor": BG_FLOOR,
        "fix": BG_FIX,
        "edge": 2,             # chunky 2 px edges: every shape is read at a glance
        "shade_light": True,
        "shade_sprite": False,  # flat: ink, skin, hair and nothing between them
        "frame": 6,            # wide window frame
        "detail": "low",
        "zeus_body": "chibi",  # head half his height
        "tone": "two flat tones plus outline",
    },
    "B": {
        "key": "B",
        "name": "LATE NES POLISH",
        "subtitle": "bold outlines, three tone shading from the top left, detailed tiles",
        "wall": BG_COLD,
        "glass": BG_GLASS,
        "floor": BG_FLOOR,
        "fix": BG_FIX,
        "edge": 1,
        "shade_light": True,
        "shade_sprite": True,  # lit face and shadow face on every form
        "frame": 4,
        "detail": "high",
        "zeus_body": "tall",
        "tone": "three tones, lit from the top left",
    },
    "C": {
        "key": "C",
        "name": "UNDERTALE CLARITY",
        "subtitle": "clean silhouettes, little shading, strong expressions",
        "wall": BG_WARM,
        "glass": BG_GLASS,
        "floor": BG_FLOOR,
        "fix": BG_FIX,
        "edge": 1,
        "shade_light": False,  # no lit edge on furniture: flat blocks, hard lines only
        "shade_sprite": False,
        "frame": 3,
        "detail": "clean",
        "zeus_body": "tall",
        "tone": "flat, one accent line",
    },
}


class ArtError(Exception):
    """A rule in this file failed. The message names the place, so the fix is mechanical."""


# -----------------------------------------------------------------------------------------------------------------
# A canvas of palette indices.


class Canvas:
    def __init__(self, width, height):
        self.w = width
        self.h = height
        self.px = [[None] * width for _ in range(height)]

    def set(self, x, y, colour):
        if colour is None:
            return
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = colour

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return None

    def rect(self, x0, y0, x1, y1, colour):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for x in range(min(x0, x1), max(x0, x1) + 1):
                self.set(x, y, colour)

    def hline(self, x0, x1, y, colour):
        self.rect(x0, y, x1, y, colour)

    def vline(self, x, y0, y1, colour):
        self.rect(x, y0, x, y1, colour)

    def frame(self, x0, y0, x1, y1, colour, thickness=1):
        for i in range(thickness):
            self.hline(x0 + i, x1 - i, y0 + i, colour)
            self.hline(x0 + i, x1 - i, y1 - i, colour)
            self.vline(x0 + i, y0 + i, y1 - i, colour)
            self.vline(x1 - i, y0 + i, y1 - i, colour)

    def rows(self, cx, top, profile, colour):
        """A shape described by a half width per row. The head and the torso are both drawn this way."""
        for index, half in enumerate(profile):
            if half <= 0:
                continue
            self.hline(cx - half, cx + half, top + index, colour)

    def filled(self):
        return [(x, y, self.px[y][x]) for y in range(self.h) for x in range(self.w) if self.px[y][x] is not None]

    def colours(self):
        return Counter(pixel for _, _, pixel in self.filled())

    def outline(self, colour, diagonal=False):
        """Add a 1 px outline round everything already drawn.

        Dilation, so the outline is exactly one pixel and no filled pixel is ever left touching the
        background without it. Returns the number of pixels added.
        """
        steps = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if diagonal:
            steps += [(-1, -1), (1, -1), (-1, 1), (1, 1)]
        additions = []
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] is not None:
                    continue
                for dx, dy in steps:
                    if self.get(x + dx, y + dy) is not None:
                        additions.append((x, y))
                        break
        for x, y in additions:
            self.px[y][x] = colour
        return len(additions)

    def remove_orphans(self):
        """Drop any filled pixel with no filled 8 neighbour. Returns the pixels removed."""
        doomed = []
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] is None:
                    continue
                neighbours = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        if self.get(x + dx, y + dy) is not None:
                            neighbours += 1
                if neighbours == 0:
                    doomed.append((x, y))
        for x, y in doomed:
            self.px[y][x] = None
        return doomed

    def to_image(self):
        image = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        pixels = image.load()
        for y in range(self.h):
            for x in range(self.w):
                index = self.px[y][x]
                if index is None:
                    continue
                pixels[x, y] = RGB[index] + (255,)
        return image

    def paste_into(self, target, ox, oy):
        for y in range(self.h):
            for x in range(self.w):
                index = self.px[y][x]
                if index is None:
                    continue
                target.set(ox + x, oy + y, index)


# -----------------------------------------------------------------------------------------------------------------
# Background: the Montefiore halls room. One geometry, three treatments.


def lit_block(cv, x0, y0, x1, y1, pal, style, force_edge=None):
    """A block of furniture: mid fill, lit top and left edges, dark bottom and right edges.

    Direction C turns the lit edge off, which is the whole difference between "three tone shading" and
    "clean silhouette" on a piece of furniture.
    """
    edge = style["edge"] if force_edge is None else force_edge
    cv.rect(x0, y0, x1, y1, pal["mid"])
    for i in range(edge):
        if style["shade_light"]:
            cv.hline(x0 + i, x1 - i, y0 + i, pal["light"])
            cv.vline(x0 + i, y0 + i, y1 - i, pal["light"])
        cv.hline(x0 + i, x1 - i, y1 - i, pal["dark"])
        cv.vline(x1 - i, y0 + i, y1 - i, pal["dark"])


def draw_ceiling(cv, style):
    pal = style["wall"]
    cv.rect(0, 0, FRAME_W - 1, 7, pal["mid"])
    if style["key"] == "B":
        cv.rect(0, 0, FRAME_W - 1, 2, pal["light"])
        cv.hline(0, FRAME_W - 1, 3, pal["mid"])
        cv.hline(0, FRAME_W - 1, 7, pal["dark"])
    elif style["key"] == "C":
        cv.rect(0, 0, FRAME_W - 1, 1, pal["light"])
        cv.hline(0, FRAME_W - 1, 7, pal["dark"])
    else:
        cv.hline(0, FRAME_W - 1, 6, pal["dark"])
        cv.hline(0, FRAME_W - 1, 7, pal["dark"])


def draw_wall(cv, style):
    pal = style["wall"]
    cv.rect(0, 8, FRAME_W - 1, 143, pal["mid"])
    for row in range(144 // AREA):
        base = row * AREA
        if style["key"] == "B":
            cv.hline(0, FRAME_W - 1, base, pal["light"])
            cv.hline(0, FRAME_W - 1, base + AREA - 1, pal["dark"])
        else:
            cv.hline(0, FRAME_W - 1, base + AREA - 1, pal["dark"])
    if style["key"] == "B":
        # A deliberate plaster stipple on a fixed 16 px lattice, not a random dither: one pixel per area,
        # always on the same cell, so the wall reads as a surface rather than as noise.
        for ay in range(1, 7):
            for ax in range(16):
                cv.set(ax * AREA + 5, ay * AREA + 9, pal["dark"])
                cv.set(ax * AREA + 11, ay * AREA + 4, pal["mid"])
    # Dado rail: the horizontal band a halls room has at hip height.
    cv.rect(0, 112, FRAME_W - 1, 119, pal["light"])
    cv.hline(0, FRAME_W - 1, 120, pal["dark"])
    cv.hline(0, FRAME_W - 1, 121, pal["mid"])
    # Skirting board at the floor line.
    cv.rect(0, 136, FRAME_W - 1, 141, pal["light"])
    cv.hline(0, FRAME_W - 1, 142, pal["dark"])
    cv.hline(0, FRAME_W - 1, 143, pal["dark"])


def draw_window(cv, x0, y0, w, h, style):
    glass = style["glass"]
    frame = style["frame"]
    # Sky: the shaded entry everywhere, the lit entry in the upper left quadrant. Light from the top left.
    cv.rect(x0, y0, x0 + w - 1, y0 + h - 1, glass["mid"])
    cv.rect(x0 + frame, y0 + frame, x0 + w // 2 - 1, y0 + h // 2 - 1, glass["light"])
    if style["key"] == "B":
        # Rooftops standing on the bottom of the pane in the shared backdrop: a city read as shapes of
        # different heights, not as scattered dark specks floating in the sky.
        floor_y = y0 + h - frame - 1
        for left, width, height in ((6, 11, 9), (19, 7, 5), (28, 13, 12), (44, 8, 7), (54, 12, 10)):
            cv.rect(x0 + frame + left, floor_y - height, x0 + frame + left + width - 1, floor_y, BACKDROP)
        cv.rect(x0 + frame + 32, floor_y - 15, x0 + frame + 33, floor_y - 12, BACKDROP)   # chimney
        cv.set(x0 + frame + 34, floor_y - 6, glass["light"])                              # lit window
        cv.set(x0 + frame + 37, floor_y - 6, glass["light"])
    elif style["key"] == "C":
        # A horizon and two flat clouds: the outside world in three shapes and no shading.
        horizon = y0 + h - frame - 12
        cv.hline(x0 + frame, x0 + w - frame - 1, horizon, glass["light"])
        for cx, cw in ((x0 + frame + 7, 12), (x0 + frame + 30, 9)):
            cv.rect(cx, horizon - 8, cx + cw - 1, horizon - 7, glass["light"])
            cv.rect(cx + 3, horizon - 9, cx + cw - 4, horizon - 9, glass["light"])
    else:
        # Direction A: a low roofline, a hill and a sun, in the two sky tones only.
        horizon = y0 + h - frame - 10
        cv.hline(x0 + frame, x0 + w - frame - 1, horizon, glass["light"])
        cv.rect(x0 + frame + 6, horizon - 7, x0 + frame + 15, horizon, glass["light"])
        cv.rect(x0 + frame + 42, horizon - 5, x0 + frame + 56, horizon, glass["light"])
        cv.rect(x0 + frame + 20, horizon - 14, x0 + frame + 25, horizon - 9, glass["light"])
    # Frame, then the inner shadow on the right and bottom edges, which is what makes the light directional.
    cv.frame(x0, y0, x0 + w - 1, y0 + h - 1, glass["dark"], frame)
    for i in range(frame):
        cv.hline(x0 + frame, x0 + w - 1 - frame, y0 + h - 1 - i, glass["mid"] if i < 2 else glass["dark"])
        cv.vline(x0 + w - 1 - i, y0 + frame, y0 + h - 1 - frame, glass["mid"] if i < 2 else glass["dark"])
    mullion = 4 if style["key"] == "A" else 2
    mx = x0 + w // 2 - mullion // 2
    my = y0 + h // 2 - mullion // 2
    cv.rect(mx, y0 + frame, mx + mullion - 1, y0 + h - frame - 1, glass["dark"])
    cv.rect(x0 + frame, my, x0 + w - frame - 1, my + mullion - 1, glass["dark"])
    # Sill, flush with the frame so every pixel of it stays inside the window's own attribute areas, lit on
    # top and shadowed underneath.
    cv.rect(x0, y0 + h, x0 + w - 1, y0 + h + 5, glass["dark"])
    cv.hline(x0, x0 + w - 1, y0 + h + 6, glass["mid"])
    cv.hline(x0, x0 + w - 1, y0 + h + 7, glass["mid"])


def draw_door(cv, x0, y0, w, h, style):
    pal = style["fix"]
    key = style["key"]
    # The doorcase: a dark reveal round a lit architrave, so the door sits in the wall instead of being pasted
    # on it. It is drawn in the WALL palette, not the door palette, because the casing lives in the wall's
    # attribute areas and an area can only ever carry one palette.
    wall = style["wall"]
    cv.rect(x0 - 4, y0 - 6, x0 + w - 1, y0 + h - 1, wall["dark"])
    cv.rect(x0 - 3, y0 - 5, x0 + w - 1, y0 + h - 1, wall["light"])
    thickness = 3 if key != "B" else 4
    cv.rect(x0, y0, x0 + w - 1, y0 + h - 1, pal["dark"])
    cv.rect(x0 + thickness, y0 + thickness, x0 + w - 1 - thickness, y0 + h - 1, pal["mid"])
    inset = thickness + 5
    if key != "C":
        # Two recessed panels: a dark inner line, a lit top and left edge, and a shadow on the bottom edge.
        for top, bottom in ((y0 + 16, y0 + 44), (y0 + 54, y0 + h - 18)):
            cv.rect(x0 + inset, top, x0 + w - 1 - inset, bottom, pal["light"])
            cv.rect(x0 + inset + 1, top + 2, x0 + w - 2 - inset, bottom - 1, pal["mid"])
            cv.hline(x0 + inset, x0 + w - 1 - inset, bottom, pal["dark"])
    else:
        cv.hline(x0 + inset, x0 + w - 1 - inset, y0 + 46, pal["dark"])
    # A kickplate and a room number plate: the two things every halls door has, and the two that make it read
    # as a door rather than as a grey rectangle.
    cv.rect(x0 + thickness, y0 + h - 12, x0 + w - 1 - thickness, y0 + h - 3, pal["dark"])
    cv.rect(x0 + w // 2 - 5, y0 + 6, x0 + w // 2 + 4, y0 + 12, pal["light"])
    cv.hline(x0 + w // 2 - 3, x0 + w // 2 + 2, y0 + 9, pal["dark"])
    # Handle: a lit plate with a dark lever under it, at hip height on the opening side.
    cv.rect(x0 + w - 14, y0 + 52, x0 + w - 11, y0 + 56, pal["light"])
    cv.hline(x0 + w - 12, x0 + w - 8, y0 + 55, pal["dark"])
    # Threshold: a strip of floor across the doorway, so the door sits IN the room instead of standing on the
    # line where the wall meets the boards. Drawn in the floor palette because that is the palette the PPU
    # gives the attribute areas this strip falls in.
    floor = style["floor"]
    cv.rect(x0 - 4, 144, x0 + w + 3, 146, floor["mid"])
    cv.hline(x0 - 4, x0 + w + 3, 144, floor["light"])
    cv.hline(x0 - 4, x0 + w + 3, 146, floor["dark"])


def draw_clock(cv, x0, y0, style):
    """A wall clock: round face, dark rim, two hands. The one thing a student hall always has on the wall."""
    pal = style["wall"]
    cx, cy, radius = x0 + 8, y0 + 8, 6
    for y in range(-radius, radius + 1):
        for x in range(-radius, radius + 1):
            if x * x + y * y <= radius * radius:
                cv.set(cx + x, cy + y, pal["light"])
            elif x * x + y * y <= (radius + 1) * (radius + 1):
                cv.set(cx + x, cy + y, pal["dark"])
    cv.vline(cx, cy - 4, cy, pal["dark"])
    cv.hline(cx, cx + 3, cy, pal["dark"])


def draw_floor(cv, style):
    """Boards running across the room, each one lit along its far edge and dark along its near edge.

    Two earlier shapes failed here and both were measured, not guessed. Drawing a horizontal line and a
    vertical line at a fixed pitch on every row IS a brick bond, and the critics read the floor as masonry.
    Drawing the plank seams as a converging fan put dark and mid pixels on adjacent columns near the vanishing
    point, which `count_dither_patches` correctly called banding (12 patches in A alone).

    So the floor now has NO vertical line on it at all. A floor reads as a floor from three things and this
    draws exactly those: boards that get taller towards the viewer, a lit far edge on each board, and a dark
    near edge. Nothing on it can form a checkerboard, which is why the dither count can stay at zero.
    """
    pal = style["floor"]
    key = style["key"]
    top = 144
    cv.rect(0, top, FRAME_W - 1, FRAME_H - 1, pal["mid"])
    # The wall casts a shadow onto the boards, darkest under the skirting and gone two rows down. This is what
    # puts the floor BEHIND the wall instead of letting the two meet on one flat line.
    cv.hline(0, FRAME_W - 1, top, pal["dark"])
    cv.hline(0, FRAME_W - 1, top + 1, pal["dark"])
    # Board rows, growing taller towards the viewer, which is the whole perspective a NES floor needs.
    height = 4 if key != "A" else 6
    grow = 2 if key == "B" else (3 if key == "A" else 4)
    y = top + 2
    rows = []
    while y < FRAME_H - 2:
        rows.append((y, min(height, FRAME_H - 2 - y)))
        y += height
        height += grow
    for y, height in rows:
        near = min(FRAME_H - 3, y + height - 1)
        cv.hline(0, FRAME_W - 1, near, pal["dark"])          # the shadowed near edge of the board
        if style["shade_light"]:
            cv.hline(0, FRAME_W - 1, y, pal["light"])        # the lit far edge of the board
    if style["detail"] == "high":
        # A knot on a sparse lattice: a solid two by two, never a run of alternating pixels. Wood reads as wood
        # from a few knots, and two by two cannot be mistaken for a dither pattern because it does not alternate.
        for index, (y, height) in enumerate(rows):
            if index % 2 == 0:
                for x in range(14 + index * 9, FRAME_W - 8, 47):
                    if y + 3 < FRAME_H - 3:
                        cv.rect(x, y + 3, x + 1, y + 3, pal["dark"])
    # The bottom two rows go dark: the near edge of the room, which frames the floor and tells the eye that the
    # picture ends at the viewer's feet rather than continuing behind them.
    cv.hline(0, FRAME_W - 1, FRAME_H - 2, pal["dark"])
    cv.hline(0, FRAME_W - 1, FRAME_H - 1, pal["dark"])


def trapezoid(cv, y0, y1, top_half, bottom_half, cx, colour, only_empty=False):
    """Fill a horizontally symmetric trapezoid, so a rug can lie on a floor instead of hanging on a wall."""
    span = max(1, y1 - y0)
    for y in range(y0, y1 + 1):
        t = (y - y0) / float(span)
        half = int(round(top_half + (bottom_half - top_half) * t))
        for x in range(cx - half, cx + half + 1):
            if only_empty and cv.get(x, y) is not None:
                continue
            cv.set(x, y, colour)


def draw_rug(cv, style):
    """A rug in perspective: wider at the near edge, narrower at the far edge, with a border and a fringe."""
    pal = style["floor"]
    key = style["key"]
    cx = 128
    y0, y1 = 176, 223
    top_half, bottom_half = 38, 47
    trapezoid(cv, y0, y1, top_half, bottom_half, cx, pal["dark"])
    # Border ring in the light tone, then the field back in dark, which reads as a woven edge.
    border = 3 if key != "C" else 2
    trapezoid(cv, y0 + border, y1 - border, top_half - border, bottom_half - border, cx, pal["light"])
    trapezoid(cv, y0 + border + 2, y1 - border - 2,
              top_half - border - 3, bottom_half - border - 3, cx, pal["mid"])
    if key != "C":
        # A motif on a fixed lattice: four pixels per cell, the same cell all the way across. A pattern that
        # could be mistaken for noise is a pattern drawn wrong.
        for gy in range(y0 + 10, y1 - 6, 12):
            t = (gy - y0) / float(y1 - y0)
            half = int(top_half + (bottom_half - top_half) * t) - 8
            for gx in range(cx - half, cx + half - 2, 12):
                cv.rect(gx, gy, gx + 3, gy + 1, pal["light"])
    # Fringe on the near edge only: strands that hang off the wide end, which is the edge a viewer sees.
    for x in range(cx - bottom_half + 2, cx + bottom_half - 1, 4):
        cv.vline(x, y1 + 1, y1 + 3, pal["light"])


def draw_boxes(cv, style):
    pal = style["floor"]
    # Two cardboard cartons, stacked, waiting to be unpacked. Each has a lit lid, a dark seam under it, a tape
    # line down the middle, and a 1 px dark edge, which is what makes a box read as a box and not a slab.
    for x0, y0, x1, y1 in ((8, 168, 49, 207), (16, 144, 47, 167)):
        cv.rect(x0, y0, x1, y1, pal["mid"])
        cv.rect(x0 + 1, y0 + 1, x1 - 1, y0 + 6, pal["light"])
        cv.hline(x0 + 1, x1 - 1, y0 + 7, pal["dark"])
        cv.vline(x0, y0, y1, pal["dark"])
        cv.vline(x1, y0, y1, pal["dark"])
        cv.hline(x0, x1, y1, pal["dark"])
        cv.hline(x0, x1, y0, pal["light"])
        tape = (x0 + x1) // 2
        cv.vline(tape, y0 + 8, y1 - 1, pal["dark"])
        if style["key"] == "B":
            cv.vline(tape + 1, y0 + 8, y1 - 1, pal["light"])


def draw_chair(cv, style):
    """A wooden chair, drawn in the floor palette.

    A halls chair kept in the same palette as the boards is what lets it stand on the boards without spending a
    fifth background group. It is drawn as a FRAME with an open gap between the legs: filled as a block it read
    as an anonymous dark rectangle, which is what the critic called it.
    """
    pal = style["floor"]
    dark, mid, light = pal["dark"], pal["mid"], pal["light"]
    # Back frame: two uprights joined by a top rail and two slats, open in between.
    cv.rect(206, 170, 208, 196, mid)
    cv.rect(221, 170, 223, 196, mid)
    cv.rect(206, 170, 223, 172, mid)
    cv.hline(206, 223, 178, mid)
    cv.hline(206, 223, 185, mid)
    cv.hline(206, 223, 170, light)
    cv.vline(206, 170, 196, light)
    cv.vline(223, 172, 196, dark)
    # Seat: a slab that overhangs the legs, which is what makes it read as a seat and not a shelf.
    cv.rect(202, 196, 227, 202, mid)
    cv.hline(202, 227, 196, light)
    cv.hline(202, 227, 202, dark)
    # Legs, two pixels, with daylight between them.
    cv.rect(204, 203, 206, 216, mid)
    cv.rect(223, 203, 225, 216, mid)
    cv.vline(204, 203, 216, light)
    cv.vline(225, 203, 216, dark)
    cv.hline(204, 206, 216, dark)
    cv.hline(223, 225, 216, dark)


def draw_room(style):
    cv = Canvas(FRAME_W, FRAME_H)
    draw_ceiling(cv, style)
    draw_wall(cv, style)
    draw_floor(cv, style)
    draw_window(cv, 16, 32, 80, 72, style)
    draw_window(cv, 160, 32, 80, 72, style)
    # The clock sits above the door, inside the single 16x16 wall attribute area at (6, 1): it is drawn in the
    # wall palette, so it is only legal where that palette owns the whole area. Moved to y 32 it entered a glass
    # area, and moved left it entered the window, and the area check caught both.
    draw_clock(cv, 96, 16, style)
    draw_door(cv, 112, 48, 48, 96, style)
    draw_rug(cv, style)
    draw_boxes(cv, style)
    draw_chair(cv, style)
    return cv


# -----------------------------------------------------------------------------------------------------------------
# Characters. Every figure is a whole number of 16 px OAM row bands, because the band IS where a sprite palette
# ends: one 8x16 OAM entry may carry three colours and no more.

ZEUS_H = 32
KRONOS_H = 48
ZEUS_H_TALL = 40


LEGEND = ".oshdmcl"


def half(pairs, width=24, name=""):
    """One left half of a figure, written as (symbol, count) pairs, mirrored onto itself.

    A front facing idle sprite is symmetric, so it is drawn once and mirrored. Writing the half as counted
    pairs rather than as a run-length string means the counts are numbers the reader can add up, and the
    width check below is the only place a row can go wrong: a half that is not exactly twelve pixels raises
    instead of quietly shifting the figure off centre.
    """
    cells = []
    for symbol, count in pairs:
        if symbol not in LEGEND:
            raise ArtError("%s: unknown symbol %r" % (name, symbol))
        if count < 0:
            raise ArtError("%s: negative count %r" % (name, count))
        cells.extend([symbol] * count)
    if len(cells) != width // 2:
        raise ArtError("%s: half row is %d px wide, needs %d: %r" % (name, len(cells), width // 2, pairs))
    return cells + list(reversed(cells))


def band_half(rows, height, width=24, name=""):
    """A strip of mirrored halves. Every finished row is exactly `width` pixels, by construction."""
    if len(rows) != height:
        raise ArtError("%s has %d rows, needs %d" % (name, len(rows), height))
    return [half(row, width, name) for row in rows]



# Every figure is drawn as a LEFT HALF of twelve pixels and mirrored, because a front facing idle sprite is
# symmetric. That kills two whole classes of bug at once: a row that is one pixel off centre, and a face whose
# eyes do not line up. Column 11 is the pixel just left of centre, so a half that ends in a filled pixel always
# meets its own mirror and the head cannot open a seam down the middle.
#
#   o ink     s skin     h hair     m shirt     d jeans     c coat     l shirt grey
#
# The shapes follow knowledge/CHARACTER-BIBLE.md, and the first pass failed on exactly those rules:
#
#   1. Konrad is NOT white haired. The bible says long BLOND hair streaked with white and grey, 40s, a neat
#      close beard. Drawn in $20 white he read as an old woman, which is what the first critic said. He is $38
#      pale gold, the light end of blond, with the beard carried by ink edges against peach skin.
#   2. A pale hair mass on a pale face needs ink between them, or the face is one pale mask.
#   3. Two by two eyes, not single pixels. One pixel is a dot; four pixels is an eye that can hold a direction.
#   4. Shoulders wider than the head in the tall directions, and arms held off the torso by a one pixel seam
#      that ends in a hand wider than the arm. A strip the colour of the shirt reads as the shirt.
#   5. Feet are two rows tall and wider than the leg, so the figure stands instead of standing on pegs.
#
# Heights: Zeus is 32 px in A (head half of him: the Mother proportion) and 40 px in B and C. Konrad is 32 px in
# A and 48 px in B and C. Every figure is a whole number of 16 px OAM bands in its own canvas.

# -----------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------
# Zander Skye (Zeus), 19: messy blond hair, oversized light blue bomber, navy jeans.

ZEUS_HEAD_A = band_half([
    [(".", 12)],
    [( ".", 5), ("h", 7)],
    [( ".", 4), ("h", 8)],
    [( ".", 4), ("h", 8)],
    [( ".", 4), ("h", 3), ("s", 5)],
    [( ".", 4), ("h", 2), ("s", 6)],
    [( ".", 4), ("h", 1), ("s", 2), ("o", 3), ("s", 2)],
    [( ".", 4), ("h", 1), ("s", 2), ("o", 3), ("s", 2)],
    [( ".", 4), ("h", 1), ("s", 6), ("o", 1)],
    [( ".", 4), ("h", 1), ("s", 7)],
    [( ".", 4), ("h", 1), ("s", 6), ("o", 1)],
    [( ".", 5), ("o", 1), ("s", 6)],
    [( ".", 6), ("o", 1), ("s", 5)],
    [( ".", 7), ("o", 1), ("s", 4)],
    [( ".", 8), ("o", 1), ("s", 3)],
    [( ".", 9), ("s", 3)],
], 16, name="ZEUS_HEAD_A")

ZEUS_BODY_A = band_half([
    [( ".", 6), ("m", 6)],
    [( ".", 5), ("m", 2), ("o", 1), ("m", 4)],
    [( ".", 5), ("m", 2), ("o", 1), ("m", 4)],
    [( ".", 5), ("m", 2), ("o", 1), ("m", 4)],
    [( ".", 4), ("d", 3), ("o", 1), ("m", 4)],
    [( ".", 4), ("d", 3), ("o", 1), ("m", 4)],
    [( ".", 5), ("m", 2), ("o", 1), ("m", 4)],
    [( ".", 5), ("m", 2), ("o", 1), ("m", 4)],
    [( ".", 6), ("o", 6)],
    [( ".", 6), ("d", 6)],
    [( ".", 6), ("d", 5), ("o", 1)],
    [( ".", 6), ("d", 5), ("o", 1)],
    [( ".", 6), ("d", 5), ("o", 1)],
    [( ".", 5), ("o", 6), (".", 1)],
    [( ".", 5), ("o", 6), (".", 1)],
    [(".", 12)],
], 16, name="ZEUS_BODY_A")

# B and C: a fourteen row head over a thirty two row body, so the head is under a third of him.
# The nose and the mouth are separated by a row of cheek. Without that row a two row face reads as a
# moustache, which is exactly what the eye critic called the nineteen year old.
ZEUS_HEAD = band_half([
    [(".", 12)],
    [(".", 12)],
    [( ".", 6), ("h", 6)],
    [( ".", 5), ("h", 7)],
    [( ".", 5), ("h", 2), ("s", 5)],
    [( ".", 5), ("h", 1), ("s", 6)],
    [( ".", 5), ("h", 1), ("s", 2), ("o", 2), ("s", 2)],
    [( ".", 5), ("h", 1), ("s", 2), ("o", 2), ("s", 2)],
    [( ".", 5), ("h", 1), ("s", 6)],
    [( ".", 5), ("h", 1), ("s", 5), ("o", 1)],
    [( ".", 5), ("h", 1), ("s", 6)],
    [( ".", 5), ("h", 1), ("s", 4), ("o", 2)],
    [( ".", 6), ("s", 6)],
    [( ".", 7), ("s", 5)],
    [( ".", 8), ("o", 1), ("s", 3)],
    [( ".", 9), ("s", 3)],
], 16, name="ZEUS_HEAD")

ZEUS_BODY_TALL = band_half([
    [( ".", 4), ("m", 8)],
    [( ".", 3), ("m", 2), ("o", 1), ("m", 6)],
    [( ".", 3), ("m", 2), ("o", 1), ("m", 6)],
    [( ".", 3), ("m", 2), ("o", 1), ("m", 6)],
    [( ".", 2), ("d", 2), ("o", 1), ("m", 7)],
    [( ".", 2), ("d", 2), ("o", 1), ("m", 7)],
    [( ".", 3), ("m", 2), ("o", 1), ("m", 6)],
    [( ".", 3), ("m", 2), ("o", 1), ("m", 6)],
    [( ".", 4), ("o", 8)],
    [( ".", 4), ("d", 8)],
    [( ".", 4), ("d", 6), ("o", 2)],
    [( ".", 4), ("d", 6), ("o", 2)],
    [( ".", 4), ("d", 6), ("o", 2)],
    [( ".", 4), ("d", 6), ("o", 2)],
    [( ".", 4), ("d", 6), ("o", 2)],
    [( ".", 4), ("d", 6), ("o", 2)],
], 16, name="ZEUS_BODY_TALL")

ZEUS_LEGS_TALL = band_half([
    [( ".", 4), ("d", 6), ("o", 2)],
    [( ".", 4), ("d", 6), ("o", 2)],
    [( ".", 4), ("d", 6), ("o", 2)],
    [( ".", 3), ("o", 7), (".", 2)],
    [( ".", 3), ("o", 7), (".", 2)],
    [(".", 12)],
    [(".", 12)],
    [(".", 12)],
], 8, name="ZEUS_LEGS_TALL")

# -----------------------------------------------------------------------------------------------------------------
# Konrad Skye (Kronos), 40s: blond hair gone pale at the temples, neat close beard, charcoal overcoat, grey shirt.
#
# The beard is carried by an ink jaw line, not by tone: the head band has no fourth colour, so the only way to
# separate a beard from a blonde face is a dark line across the jaw, which is also how a beard is drawn on the NES.

KRONOS_HEAD_A = band_half([
    [(".", 12)],
    [( ".", 5), ("h", 7)],
    [( ".", 4), ("h", 8)],
    [( ".", 4), ("h", 8)],
    [( ".", 4), ("h", 3), ("s", 5)],
    [( ".", 4), ("h", 2), ("s", 6)],
    [( ".", 4), ("h", 1), ("s", 2), ("o", 3), ("s", 2)],
    [( ".", 4), ("h", 1), ("s", 2), ("o", 3), ("s", 2)],
    [( ".", 4), ("h", 1), ("s", 7)],
    [( ".", 5), ("h", 1), ("s", 2), ("h", 2), ("o", 2)],
    [( ".", 5), ("o", 7)],
    [( ".", 5), ("h", 1), ("o", 1), ("h", 5)],
    [( ".", 5), ("h", 2), ("o", 1), ("h", 4)],
    [( ".", 6), ("o", 1), ("h", 5)],
    [( ".", 7), ("h", 5)],
    [(".", 12)],
], 16, name="KRONOS_HEAD_A")

KRONOS_HEAD = band_half([
    [(".", 12)],
    [( ".", 6), ("h", 6)],
    [( ".", 5), ("h", 7)],
    [( ".", 4), ("h", 8)],
    [( ".", 4), ("h", 3), ("s", 5)],
    [( ".", 4), ("h", 2), ("s", 6)],
    [( ".", 4), ("h", 2), ("s", 2), ("o", 2), ("s", 2)],
    [( ".", 4), ("h", 2), ("s", 2), ("o", 2), ("s", 2)],
    [( ".", 4), ("h", 2), ("s", 6)],
    [( ".", 4), ("h", 2), ("s", 5), ("o", 1)],
    [( ".", 5), ("h", 1), ("s", 2), ("h", 2), ("o", 2)],
    [( ".", 5), ("o", 7)],
    [( ".", 4), ("h", 2), ("o", 1), ("h", 5)],
    [( ".", 4), ("h", 3), ("o", 1), ("h", 4)],
    [( ".", 5), ("h", 1), ("o", 1), ("h", 5)],
    [( ".", 6), ("o", 1), ("h", 5)],
], 16, name="KRONOS_HEAD")

# The coat. The first two attempts read as armour, and the critic named why: a rectangle with a light patch in
# the middle is a breastplate. A coat is read from one thing above all, a FRONT OPENING that runs from the
# throat to the hem, so that line is drawn on every row below the collar. The collar is a V that is WIDE at
# the throat and closes upward, with a dark tie down the middle of the shirt. No buttons, no chest panel.
KRONOS_BODY_UPPER = band_half([
    [( ".", 3), ("c", 9)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 7)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 3), ("o", 1), ("l", 1), ("o", 2)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 4), ("o", 1), ("l", 1), ("o", 1)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 6), ("o", 1)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 6), ("o", 1)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 6), ("o", 1)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 6), ("o", 1)],
    [( ".", 1), ("l", 2), ("o", 1), ("c", 8)],
    [( ".", 1), ("l", 2), ("o", 1), ("c", 8)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 7)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 6), ("o", 1)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 6), ("o", 1)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 6), ("o", 1)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 6), ("o", 1)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 6), ("o", 1)],
], 16, name="KRONOS_BODY_UPPER")

KRONOS_BODY_A = band_half([
    [( ".", 3), ("c", 9)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 7)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 3), ("o", 1), ("l", 1), ("o", 2)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 4), ("o", 1), ("l", 1), ("o", 1)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 6), ("o", 1)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 6), ("o", 1)],
    [( ".", 1), ("l", 2), ("o", 1), ("c", 8)],
    [( ".", 1), ("l", 2), ("o", 1), ("c", 8)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 7)],
    [( ".", 1), ("c", 10), ("o", 1)],
    [( ".", 1), ("o", 11)],
    [( ".", 5), ("c", 5), ("o", 2)],
    [( ".", 5), ("c", 5), ("o", 2)],
    [( ".", 5), ("o", 6), (".", 1)],
    [( ".", 5), ("o", 6), (".", 1)],
    [(".", 12)],
], 16, name="KRONOS_BODY_A")

KRONOS_BODY_LOWER = band_half([
    [( ".", 2), ("c", 2), ("o", 1), ("c", 6), ("o", 1)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 6), ("o", 1)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 6), ("o", 1)],
    [( ".", 2), ("c", 2), ("o", 1), ("c", 6), ("o", 1)],
    [( ".", 1), ("c", 10), ("o", 1)],
    [( ".", 1), ("o", 11)],
    [( ".", 5), ("c", 5), ("o", 2)],
    [( ".", 5), ("c", 5), ("o", 2)],
    [( ".", 5), ("c", 5), ("o", 2)],
    [( ".", 5), ("c", 5), ("o", 2)],
    [( ".", 5), ("o", 6), (".", 1)],
    [( ".", 5), ("o", 6), (".", 1)],
    [( ".", 7), ("o", 4), (".", 1)],
    [(".", 12)],
    [(".", 12)],
    [(".", 12)],
], 16, name="KRONOS_BODY_LOWER")


def edge_shade(cv, target, shade, min_run=3, top=0):
    """Paint the inside right edge and the inside bottom edge of a form in its dark tone.

    This is the three tone rule of direction B, applied mechanically: the light is at the top left, so the
    last pixel of a horizontal run and the last pixel of a vertical run are the shadow.

    Only pixels that are currently `target` are repainted. That matters: an earlier version shaded the last
    pixel of any run, which meant it painted over the black outline and left stray dark pixels in the shoes
    and in one arm. Shading that overwrites ink is not shading, it is noise.
    """
    painted = 0
    for y in range(top, cv.h):
        x = 0
        while x < cv.w:
            if cv.px[y][x] != target:
                x += 1
                continue
            start = x
            while x < cv.w and cv.px[y][x] == target:
                x += 1
            if x - start >= min_run:
                cv.px[y][x - 1] = shade
                painted += 1
    for x in range(cv.w):
        y = top
        while y < cv.h:
            if cv.px[y][x] != target:
                y += 1
                continue
            start = y
            while y < cv.h and cv.px[y][x] == target:
                y += 1
            if y - start >= min_run:
                cv.px[y - 1][x] = shade
                painted += 1
    return painted


def edge_lit(cv, target, light, min_run=4, top=0):
    """The opposite corner: the first pixel of a long run gets the light tone. Only direction B spends it."""
    painted = 0
    for y in range(top, cv.h):
        x = 0
        while x < cv.w:
            if cv.px[y][x] != target:
                x += 1
                continue
            start = x
            while x < cv.w and cv.px[y][x] == target:
                x += 1
            if x - start >= min_run:
                cv.px[y][start] = light
                painted += 1
    return painted


def draw_rows(cv, grid, legend, top, left=0, flatten=None):
    """Paint a grid onto a canvas. Symbols map to palette entries; flatten turns one symbol into another."""
    flatten = flatten or {}
    for y, row in enumerate(grid):
        for x, symbol in enumerate(row):
            if symbol == ".":
                continue
            cv.set(left + x, top + y, legend[flatten.get(symbol, symbol)])


def zeus_height(style):
    """Direction A is chibi, so its Zeus is a whole OAM band shorter. B and C share a taller figure."""
    return ZEUS_H if style["zeus_body"] == "chibi" else ZEUS_H_TALL


def draw_zeus(style):
    key = style["key"]
    height = zeus_height(style)
    cv = Canvas(24, height)
    outline, skin, hair = SPR_ZEUS_HEAD
    _, shirt, jeans = SPR_ZEUS_BODY
    chibi = style["zeus_body"] == "chibi"
    head = ZEUS_HEAD_A if chibi else ZEUS_HEAD
    draw_rows(cv, head, {"o": outline, "s": skin, "h": hair}, 0)
    body_legend = {"o": outline, "m": shirt, "d": jeans}
    if chibi:
        draw_rows(cv, ZEUS_BODY_A, body_legend, 16)
    else:
        draw_rows(cv, ZEUS_BODY_TALL, body_legend, 16)
        draw_rows(cv, ZEUS_LEGS_TALL, body_legend, 32)
    if style["shade_sprite"]:
        # Three tones on the shirt: the jeans navy is the shirt's shadow, which is exactly the budget of a
        # three colour sprite palette. The head band is left flat, because its palette has no fourth colour
        # to spend on a cheek.
        edge_shade(cv, shirt, jeans, min_run=3, top=16)
    added = cv.outline(outline)
    removed = cv.remove_orphans()
    return cv, added, len(removed)


def draw_kronos(style):
    key = style["key"]
    chibi = style["zeus_body"] == "chibi"
    cv = Canvas(24, ZEUS_H if chibi else KRONOS_H)
    outline, skin, hair = SPR_KRONOS_HEAD
    _, coat, light = SPR_KRONOS_BODY
    head = KRONOS_HEAD_A if chibi else KRONOS_HEAD
    draw_rows(cv, head, {"o": outline, "s": skin, "h": hair}, 0)
    legend = {"o": outline, "c": coat, "l": light}
    draw_rows(cv, KRONOS_BODY_A if chibi else KRONOS_BODY_UPPER, legend, 16)
    if not chibi:
        draw_rows(cv, KRONOS_BODY_LOWER, legend, 32)
    if style["shade_sprite"]:
        # Coat: the ink is the shadow tone and the shirt grey is the rim light, applied at the ends of runs so
        # the light always reads as coming from the top left.
        edge_shade(cv, coat, outline, min_run=4, top=16)
        # The rim light starts below the hands. Applied from row 16 it lit the first pixel of the coat beside
        # each hand, and a light pixel next to a light hand across one ink pixel merged the two into a blob.
        edge_lit(cv, coat, light, min_run=6, top=30)
    added = cv.outline(outline)
    removed = cv.remove_orphans()
    return cv, added, len(removed)


# -----------------------------------------------------------------------------------------------------------------
# Sprites, OAM boxes and the composite.


def oam_boxes(x0, y0, width, height):
    """The 8x16 OAM entries that cover a figure, each with the palette triple it is allowed to use.

    The row count is rounded UP, because a 40 px figure is two and a half OAM bands: floor division would
    leave the bottom eight pixels of the sprite outside every entry, so those pixels were never measured.
    """
    rows_needed = (height + OAM_H - 1) // OAM_H
    boxes = []
    for row in range(rows_needed):
        for column in range(width // OAM_W):
            boxes.append({"x": x0 + column * OAM_W, "y": y0 + row * OAM_H, "w": OAM_W, "h": OAM_H})
    return boxes


def content_bottom(cv):
    """The last row of a figure that has a pixel on it, so the figure can be stood ON a floor line exactly."""
    for y in range(cv.h - 1, -1, -1):
        for x in range(cv.w):
            if cv.px[y][x] is not None:
                return y
    return cv.h - 1


def used_boxes(cv, boxes):
    """The OAM entries that actually draw a pixel of this figure. An empty band is not a sprite object."""
    live = []
    for entry in boxes:
        for y in range(entry["y"], entry["y"] + entry["h"]):
            for x in range(entry["x"], entry["x"] + entry["w"]):
                if 0 <= x < cv.w and 0 <= y < cv.h and cv.px[y][x] is not None:
                    live.append(entry)
                    break
            else:
                continue
            break
    return live


def figure_colours(cv):
    return {pixel for pixel in cv.colours()}


def composite(background, figures):
    cv = Canvas(FRAME_W, FRAME_H)
    for y in range(FRAME_H):
        for x in range(FRAME_W):
            cv.px[y][x] = background.px[y][x]
    for figure, ox, oy in figures:
        figure.paste_into(cv, ox, oy)
    return cv


# -----------------------------------------------------------------------------------------------------------------
# The rules, measured.


def check_background_areas(cv, style):
    """Each 16x16 area may use only its three palette entries plus the shared backdrop."""
    palettes = {
        "wall": style["wall"],
        "glass": style["glass"],
        "floor": style["floor"],
        "fix": style["fix"],
    }
    allowed = {name: {role: value for role, value in pal.items()}.values() for name, pal in palettes.items()}
    allowed = {name: set(values) | {BACKDROP} for name, values in allowed.items()}
    # Which palette each area is drawn in, from the same numbers the room was drawn from.
    role_of = area_roles(style)
    failures = []
    for ay in range(FRAME_H // AREA):
        for ax in range(FRAME_W // AREA):
            name = role_of[(ax, ay)]
            seen = set()
            for y in range(ay * AREA, ay * AREA + AREA):
                for x in range(ax * AREA, ax * AREA + AREA):
                    index = cv.px[y][x]
                    if index is not None:
                        seen.add(index)
            extra = seen - allowed[name]
            if extra:
                failures.append({"area": [ax, ay], "palette": name,
                                 "colours": sorted(seen), "outside": sorted(extra)})
    return failures


def area_roles(style):
    """The palette each 16x16 area is drawn in. One table, used by the drawing and by the check."""
    roles = {}
    for ay in range(FRAME_H // AREA):
        for ax in range(FRAME_W // AREA):
            roles[(ax, ay)] = "wall"
    for ax in range(1, 6):
        for ay in range(2, 7):
            roles[(ax, ay)] = "glass"
    for ax in range(10, 15):
        for ay in range(2, 7):
            roles[(ax, ay)] = "glass"
    for ax in range(7, 10):
        for ay in range(3, 9):
            roles[(ax, ay)] = "fix"
    for ay in range(9, 15):
        for ax in range(16):
            roles[(ax, ay)] = "floor"
    # The poster and the door frame reach into areas that a single role has to cover: the poster is paper
    # (wall palette) and the sill of each window is glass over a wall area, so those stay wall and glass.
    return roles


def check_oam(cv, boxes, triples):
    """Every OAM entry carries at most three colours, and they are one of the four sprite triples.

    An entry may hang past the bottom of the canvas (a 40 px figure needs three 16 px bands, so the last band
    is half covered); the part outside the canvas simply draws nothing and is not counted either way.
    """
    failures = []
    for entry in boxes:
        seen = set()
        for y in range(entry["y"], entry["y"] + entry["h"]):
            if not 0 <= y < cv.h:
                continue
            for x in range(entry["x"], entry["x"] + entry["w"]):
                if not 0 <= x < cv.w:
                    continue
                index = cv.px[y][x]
                if index is not None:
                    seen.add(index)
        if not seen:
            continue
        entry["colours"] = sorted(seen)
        fits = [name for name, triple in triples.items() if seen <= set(triple)]
        if len(seen) > 3:
            failures.append({"box": entry, "reason": "more than 3 colours", "colours": sorted(seen)})
        elif not fits:
            failures.append({"box": entry, "reason": "no palette holds these colours", "colours": sorted(seen)})
        else:
            entry["palette"] = fits[0]
    return failures


def count_scanline_sprites(boxes, sprite_height=OAM_H):
    """The most OAM entries that cover any one scanline."""
    lines = [0] * FRAME_H
    for entry in boxes:
        for y in range(entry["y"], entry["y"] + sprite_height):
            if 0 <= y < FRAME_H:
                lines[y] += 1
    return max(lines) if lines else 0


def check_light_direction(cv, light_colours, mid_colours):
    """Does the light sit on the top and left of the mid tones, or on the bottom and right?

    For every light pixel, a mid tone directly BELOW it means the light strip is on top of the form, and a
    mid tone to its RIGHT means the light strip stands on the left flank. Those two are the correct reading
    when the light comes from the top left. A mid tone ABOVE or to the LEFT is the opposite convention.
    A light pixel that meets another light pixel, the outline, or nothing is not counted either way.
    """
    correct = 0
    wrong = 0
    for y in range(cv.h):
        for x in range(cv.w):
            if cv.px[y][x] not in light_colours:
                continue
            if cv.get(x, y + 1) in mid_colours:
                correct += 1
            if cv.get(x + 1, y) in mid_colours:
                correct += 1
            if cv.get(x, y - 1) in mid_colours:
                wrong += 1
            if cv.get(x - 1, y) in mid_colours:
                wrong += 1
    return correct, wrong


def check_outline(cv, outline_colour):
    """Filled pixels that touch transparency without being the outline colour. Must be zero.

    A border pixel that is not the outline colour is counted too: the outline has nowhere to be drawn there,
    so the figure has no edge on that side.
    """
    leaks = 0
    for y in range(cv.h):
        for x in range(cv.w):
            index = cv.px[y][x]
            if index is None or index == outline_colour:
                continue
            if x in (0, cv.w - 1) or y in (0, cv.h - 1):
                leaks += 1
                continue
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                if cv.px[y + dy][x + dx] is None:
                    leaks += 1
                    break
    return leaks


def count_dither_patches(image):
    """Checkerboard regions, as opposed to a line, a stipple or a joint.

    A 2x2 checker on its own is not dithering: the corner where a board joint meets a board edge makes one,
    and so does the end of any 1 px line. Dithering is a checkerboard REPEATED, so a patch only counts when
    the same alternation continues two pixels right and two pixels down, which is a 4x4 checker at least.
    """
    pixels = image.load()
    patches = 0
    for y in range(image.height - 3):
        for x in range(image.width - 3):
            a = pixels[x, y][:3]
            b = pixels[x + 1, y][:3]
            c = pixels[x, y + 1][:3]
            d = pixels[x + 1, y + 1][:3]
            if not (a == d and b == c and a != b):
                continue
            if pixels[x + 2, y][:3] == a and pixels[x + 3, y][:3] == b and \
               pixels[x, y + 2][:3] == a and pixels[x, y + 3][:3] == b:
                patches += 1
    return patches


# -----------------------------------------------------------------------------------------------------------------
# One direction.


def build(style):
    background = draw_room(style)
    zeus, zeus_added, zeus_orphans = draw_zeus(style)
    kronos, kronos_added, kronos_orphans = draw_kronos(style)
    zeus_h = zeus_height(style)
    kronos_h = ZEUS_H if style["zeus_body"] == "chibi" else KRONOS_H
    # Both figures stand ON the same floor line, y 215. The offset comes from the figure's own lowest pixel, not
    # from its canvas height: a 40 px canvas whose boots end on row 36 must not be stood up by 40.
    floor_line = 215
    zeus_at = (88, floor_line - content_bottom(zeus))
    kronos_at = (136, floor_line - content_bottom(kronos))
    figures = [(zeus, zeus_at[0], zeus_at[1]), (kronos, kronos_at[0], kronos_at[1])]
    # A contact shadow under each figure. Without it a sprite floats a pixel above the boards, which is the
    # single cheapest fix to make a character look stood in a room instead of pasted on one.
    shadow = style["floor"]["dark"]
    for left in (zeus_at[0], kronos_at[0]):
        background.rect(left + 2, floor_line + 1, left + 21, floor_line + 1, shadow)
        background.rect(left + 5, floor_line + 2, left + 18, floor_line + 2, shadow)
        background.rect(left + 8, floor_line + 3, left + 15, floor_line + 3, shadow)
    frame = composite(background, figures)
    boxes = oam_boxes(zeus_at[0], zeus_at[1], 24, zeus_h) + oam_boxes(kronos_at[0], kronos_at[1], 24, kronos_h)
    # The rules are measured on the sprite LAYER: an OAM entry is judged by the pixels it draws, and the
    # background showing through a transparent sprite pixel is not one of its colours.
    zeus_local = oam_boxes(0, 0, 24, zeus_h)
    kronos_local = oam_boxes(0, 0, 24, kronos_h)
    local = zeus_local + kronos_local
    triples = {
        "sp0_zeus_head": SPR_ZEUS_HEAD,
        "sp1_zeus_body": SPR_ZEUS_BODY,
        "sp2_kronos_head": SPR_KRONOS_HEAD,
        "sp3_kronos_body": SPR_KRONOS_BODY,
    }
    report = {
        "style": style["key"],
        "name": style["name"],
        "subtitle": style["subtitle"],
        "size": [FRAME_W, FRAME_H],
        "background_palettes": {
            "wall": style["wall"], "glass": style["glass"], "floor": style["floor"], "fix": style["fix"],
            "backdrop": BACKDROP,
        },
        "sprite_palettes": {name: list(triple) for name, triple in triples.items()},
        "figures": {
            "zeus": {"at": list(zeus_at), "size": [24, zeus_h], "outline_pixels": zeus_added,
                     "orphans_removed": zeus_orphans, "oam_entries": len(used_boxes(zeus, zeus_local))},
            "kronos": {"at": list(kronos_at), "size": [24, kronos_h], "outline_pixels": kronos_added,
                       "orphans_removed": kronos_orphans, "oam_entries": len(used_boxes(kronos, kronos_local))},
        },
        "boxes": boxes,
    }
    failures = []
    failures += [{"rule": "background area", **item} for item in check_background_areas(background, style)]
    zeus_failures = check_oam(zeus, zeus_local, triples)
    kronos_failures = check_oam(kronos, kronos_local, triples)
    failures += [{"rule": "oam entry", "figure": "zeus", **item} for item in zeus_failures]
    failures += [{"rule": "oam entry", "figure": "kronos", **item} for item in kronos_failures]
    report["oam_palettes"] = {
        "zeus": [entry.get("palette") for entry in zeus_local],
        "kronos": [entry.get("palette") for entry in kronos_local],
    }

    distinct = sorted(frame.colours())
    report["distinct_colours"] = len(distinct)
    report["distinct_colour_indices"] = distinct
    if len(distinct) > MAX_COLOURS:
        failures.append({"rule": "colour count", "measured": len(distinct), "limit": MAX_COLOURS})

    per_line = count_scanline_sprites(boxes)
    report["max_sprites_per_scanline"] = per_line
    report["sprite_objects"] = len([entry for entry in local if entry.get("colours")])
    if per_line > MAX_SPRITES_PER_LINE:
        failures.append({"rule": "sprites per scanline", "measured": per_line, "limit": MAX_SPRITES_PER_LINE})
    if len(boxes) > MAX_SPRITES:
        failures.append({"rule": "sprite objects", "measured": len(boxes), "limit": MAX_SPRITES})

    leaks = check_outline(zeus, SPR_ZEUS_HEAD[0]) + check_outline(kronos, SPR_KRONOS_HEAD[0])
    report["outline_leaks"] = leaks
    if leaks:
        failures.append({"rule": "outline", "measured": leaks, "limit": 0})

    light = style["wall"]["light"]
    floors = style["floor"]["light"]
    up_left, down_right = check_light_direction(background, {light, floors},
                                                {style["wall"]["mid"], style["floor"]["mid"]})
    report["light_up_left"] = up_left
    report["light_down_right"] = down_right
    if up_left < down_right:
        failures.append({"rule": "light direction", "up_left": up_left, "down_right": down_right})

    image = frame.to_image()
    patches = count_dither_patches(image)
    report["dither_patches"] = patches
    if patches:
        failures.append({"rule": "dithering", "measured": patches, "limit": 0})

    off_palette = sorted({pixel[:3] for pixel in image.getdata() if pixel[3] and pixel[:3] not in RGB_TO_INDEX})
    report["off_palette"] = off_palette
    if off_palette:
        failures.append({"rule": "2C02 palette", "colours": off_palette})

    report["failures"] = failures
    report["ok"] = not failures
    return frame, background, zeus, kronos, boxes, report


# -----------------------------------------------------------------------------------------------------------------
# Outputs.


def write_direction(style, out_dir=OUT_DIR):
    frame, background, zeus, kronos, boxes, report = build(style)
    key = style["key"]
    os.makedirs(out_dir, exist_ok=True)
    frame_path = os.path.join(out_dir, "frame_%s_256x240.png" % key)
    bg_path = os.path.join(out_dir, "bg_%s_256x240.png" % key)
    sheet_path = os.path.join(out_dir, "sprites_%s.png" % key)
    list_path = os.path.join(out_dir, "frame_%s_sprites.json" % key)
    frame.to_image().save(frame_path)
    background.to_image().save(bg_path)
    sheet = Image.new("RGBA", (56, KRONOS_H), (0, 0, 0, 0))
    sheet.alpha_composite(zeus.to_image(), (0, KRONOS_H - zeus.h))
    sheet.alpha_composite(kronos.to_image(), (32, 0))
    sheet.save(sheet_path)
    with open(list_path, "w", encoding="utf-8") as handle:
        json.dump({"sprites": [{"x": entry["x"], "y": entry["y"], "w": entry["w"], "h": entry["h"]}
                               for entry in boxes]}, handle, indent=1)
    report["files"] = {"frame": frame_path, "background": bg_path, "sprites": sheet_path,
                       "sprite_list": list_path}
    return report


def load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError as error:
        raise ArtError("cannot read the font at %s: %s" % (FONT_PATH, error))


def wrap_lines(text, limit):
    """Break text into lines of at most `limit` characters, on word boundaries.

    The subtitle has to wrap: Press Start 2P is monospaced at the point size, so a 68 character subtitle at
    16 px is 1088 px wide inside a 768 px cell. Unwrapped it ran into the next cell, which is what the first
    sheet did.
    """
    lines = []
    current = ""
    for word in text.split():
        candidate = word if not current else current + " " + word
        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def build_sheet(reports, out_path=os.path.join(OUT_DIR, "ART-TARGET-SHEET.png")):
    """A, B and C side by side at 3x, with each frame again at 1x beneath it, every one labelled."""
    scale = 3
    cell_w = FRAME_W * scale
    gutter = 32
    width = cell_w * 3 + gutter * 4
    header = 152          # title, subtitle, then three lines of direction description
    label_h = 24
    band_h = FRAME_H * scale + label_h
    foot = 96
    height = header + band_h + label_h + FRAME_H + 48 + foot
    sheet = Image.new("RGB", (width, height), (16, 16, 24))
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(32)
    label_font = load_font(16)
    small_font = load_font(16)
    draw.text((gutter, 28), "PRIMORDIAL PARADOX  ART TARGET", font=title_font, fill=(248, 248, 248))
    draw.text((gutter, 72), "ONE FRAME, THREE DIRECTIONS, 256x240 AT 3X AND AT 1X",
              font=small_font, fill=(164, 164, 200))
    per_line = 44
    for index, report in enumerate(reports):
        x = gutter + index * (cell_w + gutter)
        frame = Image.open(report["files"]["frame"]).convert("RGB")
        big = frame.resize((cell_w, FRAME_H * scale), Image.NEAREST)
        sheet.paste(big, (x, header + label_h))
        label = "%s  %s" % (report["style"], report["name"])
        draw.text((x, header - 48), label, font=label_font, fill=(248, 216, 120))
        for line_index, line in enumerate(wrap_lines(report["subtitle"], per_line)):
            draw.text((x, header - 24 + line_index * 18), line, font=small_font, fill=(200, 200, 220))
        y = header + band_h + label_h + 24
        sheet.paste(frame, (x, y))
        draw.text((x + FRAME_W + 16, y + 8), "%s AT 1X" % report["style"], font=label_font,
                  fill=(140, 140, 170))
        draw.text((x + FRAME_W + 16, y + 32), "%d COLOURS" % report["distinct_colours"],
                  font=small_font, fill=(140, 140, 170))
        draw.text((x + FRAME_W + 16, y + 56), "OAM %d" % report["sprite_objects"],
                  font=small_font, fill=(140, 140, 170))
    note = "EVERY PIXEL NEW. NES LIMITS: 4 BG + 4 SPR PALETTES, 8X16 SPRITES, 8 PER SCANLINE. PICK A, B OR C."
    draw.text((gutter, height - 64), note, font=small_font, fill=(120, 200, 160))
    sheet.save(out_path)
    return out_path


def print_report(reports):
    print("%-2s %-26s %4s %4s %5s %6s %6s %5s %s" %
          ("ID", "NAME", "COLS", "OAM", "LINE", "OUTLN", "LEAK", "DITH", "VERDICT"))
    for report in reports:
        print("%-2s %-26s %4d %4d %5d %6d %6d %5d %s" % (
            report["style"], report["name"], report["distinct_colours"],
            report["sprite_objects"], report["max_sprites_per_scanline"],
            report["figures"]["zeus"]["outline_pixels"] + report["figures"]["kronos"]["outline_pixels"],
            report["outline_leaks"], report["dither_patches"],
            "PASS" if report["ok"] else "FAIL"))
        for failure in report["failures"]:
            print("   FAIL %s: %s" % (failure.get("rule"), json.dumps(failure, sort_keys=True)[:300]))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Draw the pantheon frame in three art directions.")
    parser.add_argument("--style", choices=sorted(STYLES), default=None, help="one direction; default all three")
    parser.add_argument("--out", default=OUT_DIR, help="output directory (default output/art_target)")
    parser.add_argument("--sheet", action="store_true", help="build ART-TARGET-SHEET.png from all three")
    parser.add_argument("--report", action="store_true", help="print the measured table and write no art")
    parser.add_argument("--json", dest="json_path", default=None, help="write the measurements as JSON")
    args = parser.parse_args(argv)

    keys = [args.style] if args.style else sorted(STYLES)
    reports = []
    try:
        for key in keys:
            if args.report:
                _, _, _, _, _, report = build(STYLES[key])
            else:
                report = write_direction(STYLES[key], args.out)
            reports.append(report)
        if args.sheet:
            path = build_sheet(reports, os.path.join(args.out, "ART-TARGET-SHEET.png"))
            print("sheet: %s" % path)
    except ArtError as error:
        print("art target: %s" % error)
        return 2
    print_report(reports)
    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as handle:
            json.dump(reports, handle, indent=1)
    return 0 if all(report["ok"] for report in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
