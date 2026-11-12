#!/usr/bin/env python3
"""make_dialogue_busts.py: draw the 48x48 four colour dialogue busts, one hand authored grid each.

Card t_4d6b0f4b (DIALOGUE-PORTRAIT). Its parent card t_01432e14 removed a portrait frame from spec 05 because no
speaker carried a bust and `pp_dialogue_draw` drew one anyway; this card is where the bust comes back, and the card
says plainly "do not start this until the sprite exists". So the sprite exists first, in this file, before any GML
learns to draw it.

Geometry, from specs/05-dialogue.md and knowledge/GAMEDEV-DECISIONS-2026-10-23.md D10 point 3
-------------------------------------------------------------------------------------------------
- 48x48 pixels, standing on the dialogue box's top edge at (16, 120). The box is at y 168, so a 48 pixel bust that
  starts at y 120 ends at y 167 and touches the box without covering one pixel of it.
- One pixel frame, drawn INTO the sheet rather than by a rectangle at run time: the box's draw path is one sheet and
  one call, and a frame the engine paints is a second thing that can disagree with the art.
- At most 4 colours from data/nes_palette.json, and at most 3 opaque in any 8x8 tile, because a sprite tile carries 3
  opaque colours plus transparency (ART-BIBLE 1.1 row 16). Each bust here spends exactly 3 entries, two of them shared
  with the scene's row, and the audit below proves no tile spends more than 3.
- 48x48 is 36 sprite tiles, 6 to a scanline, inside the PPU's 8 sprites per scanline and 64 in OAM (ART-BIBLE 1.1
  rows 18 and 19). That arithmetic, and the box's 8 pixel padding, is why the bust is 48 and not 64.

The three entries, and why the middle is transparent
----------------------------------------------------
    accent one per bust: the hair or helmet, and the frame
    skin   one per bust
    ink    $0F, the canonical black: the silhouette and every feature

A bust used to fill its own interior with $02, the dialogue window's navy, so that the figure read on the box's
colour instead of on the room behind it. knowledge/PALETTE-RULINGS-2026-11-12.md section 3.1 ruled that out and
measured why: $02 is a BACKGROUND entry, the fill data/palettes/scene_ui.json bg0 ($02 $30 $00) carries on every
16x16 area the dialogue window covers, so a portrait that paints it as sprite pixels spends one of its three sprite
entries on the box. It also cost the ui scene a row: with the panel drawn the three sheets between them needed five
sprite rows while the scene has four, and with the panel out they need two, {0F 30 36} for the guard and Percy and
{0F 28 36} for Prometheus (the two rows scene_ui.json sp2 and sp3 now carry).

So every $02 pixel is transparent. The figure is ink line art over the pixels behind it: the face is the one
filled mass, the shoulders are an ink outline with a lapel line, and the hair or helmet is the accent. That is a 3
opaque colour figure, which is exactly what one sprite tile can carry. The bust stands on the box's top edge and
covers none of it (pp_dialogue_draw on card t_4d6b0f4b), so what shows inside the frame is the room the box stands
in, which is the ground this sheet is judged against: section 3.2 measured that crop at $0F on 2112 of the 2304
pixels, $00 on 176, and $20 on the 16 the capture itself owns.

How these were drawn
--------------------
The left half of each sheet is drawn, then mirrored onto the right, so a face cannot be lopsided by a one pixel typo
and the silhouette is symmetric about the axis between x 23 and x 24. Every shape is a number in this file: the face
is 18 pixels wide on rows 9 to 30, the jaw steps in one pixel a row over rows 27 to 30, the eye is a 3x3 ink block at
x 18..20 with a 6 pixel bridge across both halves, the neck is 8 wide, and the shoulders are a trapezoid from row 35
to row 46. The ink outline is not hand listed: `outline()` recolours every pixel of a mass that touches a different
colour, which is the same 1 pixel silhouette rule tools/art/make_characters_v2.py uses.

The three busts answer the three speakers in data/dialogue/all.json that a portrait earns: the gate guard, Percy
(Poseidon) and Prometheus. Nothing was traced, ripped or resampled from any game; the proportions follow
knowledge/ART-BIBLE.md and knowledge/CHARACTER-BIBLE.md.

Usage
    python tools/art/make_dialogue_busts.py            build every bust, print the measured row
    python tools/art/make_dialogue_busts.py --dump     build, then print each frame as ASCII, numbered
    python tools/art/make_dialogue_busts.py --audit    build, then print the per tile colour audit
"""

from __future__ import annotations

import argparse
import json
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT_DIR = os.path.join(ROOT, "game", "sprites_src", "chars")
PALETTE_JSON = os.path.join(ROOT, "data", "nes_palette.json")

SIZE = 48
TILE = 8
HALF = 23  # the last left half column; the mirror axis is between 23 and 24
FPS = 1.0

# The role names a grid cell may hold. The three entries a bust may spend are named by role here and resolved to NES
# codes below, which is the only place in this file where a palette entry number is written.
ACCENT = "accent"
SKIN = "skin"
INK = "ink"

# $02, the dialogue window's fill. A bust must paint NONE of it: the panel is the box's, drawn behind the bust as
# background (knowledge/PALETTE-RULINGS-2026-11-12.md section 3.1), and the audit below refuses a sheet that spends it.
PANEL_CODE = "$02"
INK_CODE = "$0F"     # #000000, the canonical black (ART-BIBLE 1.3)

# role -> NES entry, per bust. Three entries each, no more.
BUSTS = {
    "guard": {
        "accent": "$30",  # #fcfcfc: the harbour watch's white helmet, and its frame
        "skin": "$36",    # #f0d0b0, the pale skin the cast sheet already uses
        "note": "the checkpoint sentry: a white watch helmet over a navy tunic, one white collar tab each side",
    },
    "percy": {
        "accent": "$30",
        "skin": "$36",
        "note": "Poseidon before the fight: white hair and a full white beard, his robe the same navy as the box",
    },
    "prometheus": {
        "accent": "$28",  # #f8b800 gold: the flame hair, the collar band, and the frame, which is the fire
        "skin": "$36",    # #f0d0b0, the same pale skin the guard and Percy spend: $37 is in no scene sprite
                          # palette, so at $37 this bust could not belong to any scene palette at all (t_a61c01b7)
        "note": "the reincarnation: gold flame hair and a gold collar band, his robe the box's own navy",
    },
}


class Grid:
    """A 48x48 grid of role names, transparent where nothing is drawn."""

    def __init__(self, size=SIZE):
        self.size = size
        self.cells = [[None for _ in range(size)] for _ in range(size)]

    def set(self, x, y, role):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.cells[y][x] = role

    def get(self, x, y):
        if 0 <= x < self.size and 0 <= y < self.size:
            return self.cells[y][x]
        return None

    def hline(self, x0, x1, y, role):
        for x in range(x0, x1 + 1):
            self.set(x, y, role)

    def vline(self, x, y0, y1, role):
        for y in range(y0, y1 + 1):
            self.set(x, y, role)

    def rect(self, x0, y0, x1, y1, role):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, role)

    def frame_rect(self, x0, y0, x1, y1, role):
        self.hline(x0, x1, y0, role)
        self.hline(x0, x1, y1, role)
        self.vline(x0, y0, y1, role)
        self.vline(x1, y0, y1, role)

    def mirror_x(self):
        """Copy the left half onto the right, so a face cannot be lopsided by a one pixel typo."""
        for y in range(self.size):
            for x in range(self.size // 2):
                self.cells[y][self.size - 1 - x] = self.cells[y][x]

    def count(self, role):
        return sum(1 for row in self.cells for cell in row if cell == role)

    def dump(self, legend):
        lines = []
        for index, row in enumerate(self.cells):
            lines.append("%02d %s" % (index, "".join(legend[cell] if cell else "." for cell in row)))
        return lines


def outline(grid, fill):
    """Recolour every `fill` pixel that touches a different colour with ink: the 1 pixel silhouette, done by rule.

    This is what makes a 3 colour figure read as a figure: the ink edge is already one of the three colours, so the
    silhouette costs nothing extra, and it is applied after the mass and before the features.
    """
    edges = []
    for y in range(grid.size):
        for x in range(grid.size):
            if grid.get(x, y) != fill:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                # The mirror axis is not an edge: the right half does not exist yet while the left half is outlined,
                # and treating it as empty would paint a two pixel seam down the middle of every face.
                if dx > 0 and x == HALF:
                    continue
                neighbour = grid.get(x + dx, y + dy)
                if neighbour is not fill and neighbour != INK:
                    edges.append((x, y))
                    break
    for x, y in edges:
        grid.set(x, y, INK)


def draw_face(grid):
    """The head every bust shares, drawn as the left half only: 18 pixels wide across both halves."""
    rows = [
        (9, 18), (10, 16),
        (11, 15), (12, 15), (13, 15), (14, 15), (15, 15), (16, 15), (17, 15), (18, 15),
        (19, 15), (20, 15), (21, 15), (22, 15), (23, 15), (24, 15), (25, 15), (26, 15),
        (27, 15), (28, 16), (29, 17), (30, 18),
    ]
    for y, x0 in rows:
        grid.hline(x0, HALF, y, SKIN)
    # Neck: 8 pixels wide across both halves, rows 31 to 34, under the chin.
    grid.rect(20, 31, HALF, 34, SKIN)
    outline(grid, SKIN)

    # Eye: a 3x3 ink block at x 18..20 rows 18..20, so the bridge is 6 pixels across both halves.
    grid.rect(18, 18, 20, 20, INK)
    # Brow: one ink row over the eye with a row of skin between, the outer end one row up so it reads as a brow.
    grid.hline(17, 21, 16, INK)
    grid.set(16, 15, INK)
    # Nose: one column on the left half, two pixels across once mirrored, from the eye line to above the mouth.
    grid.vline(HALF, 20, 23, INK)
    # Mouth: a line from x 19 to the axis, the corner one row up, so it reads as a mouth and not a slot.
    grid.hline(19, HALF, 27, INK)
    grid.set(19, 26, INK)


def draw_shoulders(grid):
    """The bust half: an ink shoulder line over the room behind it, with one lapel line inside it.

    The robe is not painted. It is the pixels behind the bust, framed by ink, which is how a 3 opaque colour figure
    pays for a body without spending a fourth entry: the shape is stated by ink, the same way the face's silhouette
    is (knowledge/PALETTE-RULINGS-2026-11-12.md section 3.1).
    """
    for y in range(35, SIZE - 1):
        half = 10 + (y - 35)
        if half > 20:
            half = 20
        # The shoulder contour is 2 px wide, not 1 (card t_ca9ad5b3): a one pixel 45 degree line is the exact
        # shape ART-STYLE section 2's dither count flags, and it measured 31 patches per portrait, which is
        # why the three busts read red while the pass itself added nothing. Direction B asks for bold dark
        # outlines, so the contour gains the inner pixel; the count is re-measured with tools/art/style_b.py.
        grid.set(HALF - half, y, INK)
        grid.set(HALF - half + 1, y, INK)
        if y >= 37:
            grid.set(HALF - half + 2, y, INK)
    # Top of the shoulders: an ink line from the outer edge in to the neck, so the neck is not floating.
    grid.hline(HALF - 10, 19, 35, INK)
    grid.hline(19, HALF, 34, INK)


def draw_frame(grid):
    """The 1 pixel frame the geometry asks for, drawn into the sheet so the engine draws no second thing."""
    grid.frame_rect(0, 0, SIZE - 1, SIZE - 1, ACCENT)


def guard_grid():
    g = Grid()
    draw_face(g)
    draw_shoulders(g)
    # Watch helmet: the accent over the skull on rows 5 to 13, one pixel wider than the face, peaked at the crown.
    g.hline(19, HALF, 5, ACCENT)
    g.hline(16, HALF, 6, ACCENT)
    for y in range(7, 14):
        g.hline(14, HALF, y, ACCENT)
    outline(g, ACCENT)
    # Brim: 11 pixels each side of the axis, one row of accent over an ink line, so the cap has a visor.
    g.hline(13, HALF, 14, ACCENT)
    g.hline(13, HALF, 15, INK)
    # Duty collar: one white tab each side, on the shoulder, below the neck.
    g.rect(13, 41, 16, 43, ACCENT)
    return g


def percy_grid():
    """Percy (Poseidon): a swept head of white hair and a forked beard, on a high collar.

    Card AUTO-SPRITE-NEXT (t_255c054d) redrew this bust because the queue row's own defect is
    one_construction_for_three_faces: guard, Percy and Prometheus were the same mirrored head with a different
    hair mass, and the eye read all three as one drawing. The four entries are unchanged ($02 panel, $0F ink,
    $36 skin, $30 accent); what changes is the construction, and three of its parts are drawn AFTER the mirror,
    on one side only, so the head cannot be a mirrored clone:
      1. the hair sweeps to the LEFT (percy_marks), where the guard's helmet and Prometheus's flame are both
         symmetric about the axis;
      2. the beard forks with one tongue left of the axis, so the jaw line is not a mirror of itself;
      3. the trident is a weapon in the frame (percy_marks), which no other bust carries.
    """
    g = Grid()
    draw_face(g)
    draw_shoulders(g)
    # Hair: a rounded crown one row higher and one pixel wider than the guard's helmet, then a short sideburn
    # that stops above the brow so the forehead is visible and the mass reads as hair, not as a cap.
    g.hline(19, HALF, 4, ACCENT)
    g.hline(16, HALF, 5, ACCENT)
    for y in range(6, 9):
        g.hline(14, HALF, y, ACCENT)
    g.hline(13, HALF, 9, ACCENT)
    g.hline(13, 20, 10, ACCENT)
    g.hline(13, 15, 11, ACCENT)
    g.hline(13, 14, 12, ACCENT)
    outline(g, ACCENT)
    # Brow: a white row over the ink brow at row 16, so the face reads as an old god and not the guard.
    g.hline(16, 20, 14, ACCENT)
    # Beard: from the jaw down to the chest, narrowing at row 33 and flaring into a fork at rows 36 to 39, which
    # is a different silhouette from the guard's bare jaw and from Prometheus's collar band.
    beard = [(28, 17), (29, 16), (30, 15), (31, 15), (32, 16), (33, 17), (34, 18), (35, 19),
             (36, 20), (37, 21), (38, 21), (39, 21)]
    for y, x0 in beard:
        g.hline(x0, HALF, y, ACCENT)
    outline(g, ACCENT)
    # Strands: two short ink marks, kept off the beard's outer edge so the outline pass cannot eat them.
    g.hline(17, 18, 32, INK)
    g.hline(19, 20, 35, INK)
    return g


def percy_marks(g):
    """Percy's three asymmetric marks, drawn AFTER the mirror so the head is not a mirrored construction.

    The queue row's named defect (one_construction_for_three_faces) is that all three busts were built from one
    mirrored head. A mirrored drawing cannot be un-mirrored by changing its hair colour, so these are placed on
    one side of the axis only, the same way prometheus_licks() breaks the fire's symmetry.

    Every stroke here is two pixels thick on purpose: outline() recolours every pixel of a mass that touches a
    different colour, so a one pixel stroke is recoloured entirely and leaves no white core at all.
    """
    # 1. The fringe: lowered over the brow, which no other bust has, and the first of the marks that survive the
    #    mirror as a single mass on the left of the axis. Kept clear of the trident's ink columns at x 11 by
    #    starting at x 13, so the weapon and the head read as two shapes.
    g.hline(13, 15, 12, ACCENT)
    g.hline(13, 14, 13, ACCENT)
    outline(g, ACCENT)
    # 2. The beard's fork: one tongue left of the axis only, rows 37 to 39, over the collar line.
    g.hline(15, 17, 37, ACCENT)
    g.hline(15, 16, 38, ACCENT)
    g.hline(15, 15, 39, ACCENT)
    outline(g, ACCENT)
    # 3. The trident, held upright on the left of the frame, rows 2 to 34: three prongs over a crossbar and a
    #    two pixel shaft. The white edges and the ink beside them are drawn explicitly rather than left to
    #    outline(), because a two pixel shaft has a panel neighbour on each side and would be recoloured whole.
    #    It clears the shoulder contour at rows 41+ and the face at x 15+ by construction.
    for x in (5, 8):                       # the shaft's ink edges
        g.vline(x, 6, 34, INK)
    for x in (6, 7):                       # the shaft's two white columns
        g.vline(x, 6, 34, ACCENT)
    g.hline(3, 10, 6, INK)                 # the crossbar's ink underside
    g.hline(3, 10, 5, ACCENT)              # the crossbar
    for x in (3, 4, 6, 7, 9, 10):          # three prongs, two pixels each, rows 2 to 4
        g.vline(x, 2, 4, ACCENT)
    for x in (2, 5, 8, 11):                # ink between and beside the prongs
        g.vline(x, 2, 4, INK)
    g.hline(3, 10, 1, INK)                 # the prong tips' ink cap
    g.hline(6, 7, 35, INK)                 # the butt of the shaft, so it ends on a line


def prometheus_grid():
    g = Grid()
    draw_face(g)
    draw_shoulders(g)
    # Flame hair: ONE continuous mass, rows 3 to 11, stepped at the left temple, so the silhouette reads as fire
    # and not as a cap. Card t_a61c01b7 removed the two notches and the three interior ink strokes the shipped
    # draft cut into this mass: measured, they broke the gold into separate specks, so the shape the ink edge was
    # drawing round was no longer one mass. That is the row's named defect, pale_hair_mass_without_an_outline.
    g.hline(13, HALF, 11, ACCENT)
    for y in (7, 8, 9, 10):
        g.hline(13, HALF, y, ACCENT)
    g.hline(14, HALF, 6, ACCENT)
    g.hline(15, HALF, 5, ACCENT)
    g.hline(17, HALF, 4, ACCENT)
    g.hline(19, HALF, 3, ACCENT)
    # The temple: one pixel narrower than the mass, rows 12 and 13, the hairline over the eye.
    g.hline(13, 15, 12, ACCENT)
    g.hline(13, 14, 13, ACCENT)
    outline(g, ACCENT)
    # The collar band: TWO gold rows with an ink row above and below, so the outline pass cannot eat it. The shipped
    # draft had one gold row 41 with panel on both sides, which outline() recolours entirely, so the sheet carried
    # no second gold mass at all.
    g.hline(13, HALF, 40, ACCENT)
    g.hline(13, HALF, 41, ACCENT)
    g.hline(13, HALF, 39, INK)
    g.hline(13, HALF, 42, INK)
    return g


BUILDERS = {
    "guard": guard_grid,
    "percy": percy_grid,
    "prometheus": prometheus_grid,
}


def palette_hex(root=PALETTE_JSON):
    with open(root, "r", encoding="utf-8-sig") as handle:
        document = json.load(handle)
    return {entry["code"]: entry["hex"] for entry in document["entries"]}


def rgba(hex_colour):
    value = hex_colour.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), 255)


def prometheus_licks(g):
    """Two tongues above the mirrored mass, off centre, so the hair reads as fire rather than as a gold crown.

    Everything else on this sheet is drawn as a left half and mirrored, which is what keeps a face from going lopsided
    by one pixel. Fire is the one thing that must NOT be symmetric: a symmetric three tip mass above a face is a crown,
    which is what the first draft looked like at 6x. The tongues and the notches below are placed after the mirror, on
    the right of the axis only.
    """
    # Tongue one, four pixels above the mass's top edge, and tongue two taller and further right. Both start clear of
    # the frame's inner row by one panel pixel, because an ink outline that touches the frame reads as a stray line.
    # One lick above the mass, right of the axis only, so the fire is not a symmetric crown. Three gold pixels on
    # row 2 and four on row 1 step up from the mass's top edge, and one pixel is cut out of the mass beside them so
    # the lick separates from the rest of the fire. Card t_a61c01b7 replaced the shipped pair of tongues and the
    # three notches they needed with this single lick, which the outline pass edges without cutting the mass open.
    g.hline(26, 29, 2, ACCENT)
    g.hline(27, 29, 1, ACCENT)
    g.set(25, 2, None)                     # the cut that separates the lick: nothing, not a colour
    outline(g, ACCENT)


def shade_pass(grid, min_run=6):
    """Direction B's shadow: the last pixel of every long run of a mass becomes ink.

    This is the same mechanical rule tools/art/make_art_target.py's `edge_shade` applies to the reference frame
    for direction B: the light comes from the top left, so the right end of a horizontal run and the bottom end
    of a vertical run are the shadow. It is applied to the finished, mirrored grid, so the axis seam cannot be
    shaded by accident, and it spends no new entry: the shadow is the ink the silhouette already uses, which is
    what lets a three entry bust carry three tones (ink, the mass, and the room behind it).

    Runs shorter than `min_run` are left alone: a two pixel shadow on a two pixel mass is a smudge, not shading.
    """
    for role in (SKIN, ACCENT):
        for y in range(1, SIZE - 1):
            x = 1
            while x < SIZE - 1:
                if grid.get(x, y) != role:
                    x += 1
                    continue
                start = x
                while x < SIZE - 1 and grid.get(x, y) == role:
                    x += 1
                if x - start >= min_run:
                    grid.set(x - 1, y, INK)
        for x in range(1, SIZE - 1):
            y = 1
            while y < SIZE - 1:
                if grid.get(x, y) != role:
                    y += 1
                    continue
                start = y
                while y < SIZE - 1 and grid.get(x, y) == role:
                    y += 1
                if y - start >= min_run:
                    grid.set(x, y - 1, INK)


def build(name):
    """One bust as a Grid: left half drawn, mirrored, the one asymmetric detail, the shadow, frame last."""
    grid = BUILDERS[name]()
    grid.mirror_x()
    if name == "prometheus":
        prometheus_licks(grid)
    if name == "percy":
        percy_marks(grid)
    shade_pass(grid)
    draw_frame(grid)
    return grid, BUSTS[name]


def audit(name, grid, pal, hexes):
    """Every rule the bust has to pass, as a list of problems. Empty means the sheet is legal."""
    problems = []
    roles = {ACCENT: pal["accent"], SKIN: pal["skin"], INK: INK_CODE}
    if len(set(roles.values())) > 4:
        problems.append("%s spends %d entries, a bust may spend 4" % (name, len(set(roles.values()))))
    for role, code in roles.items():
        if code not in hexes:
            problems.append("%s names %s for %s, which data/nes_palette.json does not carry" % (name, code, role))
    # The box's fill is not a sprite entry. A bust that paints $02 spends one of its three sprite colours on the
    # dialogue window, which is drawn behind it anyway (knowledge/PALETTE-RULINGS-2026-11-12.md section 3.1).
    if PANEL_CODE in set(roles.values()):
        problems.append("%s paints %s, the dialogue window's fill, which belongs to the box and not to the bust"
                        % (name, PANEL_CODE))

    # The frame: every pixel of the outermost ring, nothing missing.
    for x in range(SIZE):
        for y in (0, SIZE - 1):
            if grid.get(x, y) != ACCENT:
                problems.append("%s misses its frame at %d,%d" % (name, x, y))
    for y in range(SIZE):
        for x in (0, SIZE - 1):
            if grid.get(x, y) != ACCENT:
                problems.append("%s misses its frame at %d,%d" % (name, x, y))

    # The interior is transparent wherever the box shows through: this file used to refuse a transparent pixel
    # inside the frame, and knowledge/PALETTE-RULINGS-2026-11-12.md section 3.1 ruled the opposite, so the rule is
    # gone and the ink ring above plus the shoulder line below are what keep the figure from reading as a hole.

    # The tile budget: a sprite tile carries 3 opaque colours plus transparency.
    for ty in range(SIZE // TILE):
        for tx in range(SIZE // TILE):
            seen = set()
            for y in range(ty * TILE, ty * TILE + TILE):
                for x in range(tx * TILE, tx * TILE + TILE):
                    cell = grid.get(x, y)
                    if cell:
                        seen.add(cell)
            if len(seen) > 3:
                problems.append("%s tile %d,%d carries %d colours: %s"
                                % (name, tx, ty, len(seen), ", ".join(sorted(seen))))

    # A bust has to be a bust: a face, an accent mass over it, and a shoulder line on the last row of the frame.
    if grid.count(SKIN) < 150:
        problems.append("%s has %d skin pixels, which is not a face" % (name, grid.count(SKIN)))
    if grid.count(ACCENT) < 150:
        problems.append("%s has %d accent pixels, which is not hair or a helmet" % (name, grid.count(ACCENT)))
    if not any(grid.get(x, SIZE - 2) == INK for x in range(1, SIZE - 1)):
        problems.append("%s has no shoulder line on its last row, so it does not stand on the box" % name)
    return problems


def render(grid, pal, hexes):
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    pixels = image.load()
    codes = {ACCENT: pal["accent"], SKIN: pal["skin"], INK: INK_CODE}
    for y in range(SIZE):
        for x in range(SIZE):
            cell = grid.get(x, y)
            if cell:
                pixels[x, y] = rgba(hexes[codes[cell]])
    return image


def write(name, image):
    png = os.path.join(OUT_DIR, "spr_pp_portrait_%s.png" % name)
    meta = os.path.join(OUT_DIR, "spr_pp_portrait_%s.json" % name)
    image.save(png)
    sidecar = {
        "name": "spr_pp_portrait_%s" % name,
        "frame_w": SIZE,
        "frame_h": SIZE,
        "frames": 1,
        "fps": FPS,
    }
    with open(meta, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(sidecar, handle, indent=2)
        handle.write("\n")
    return png, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", action="store_true", help="print every frame as ASCII after building it")
    parser.add_argument("--audit", action="store_true", help="print the per tile audit after building it")
    args = parser.parse_args()

    hexes = palette_hex()
    legend = {ACCENT: "+", SKIN: "s", INK: "#"}
    os.makedirs(OUT_DIR, exist_ok=True)

    problems = []
    for name in sorted(BUILDERS):
        grid, pal = build(name)
        found = audit(name, grid, pal, hexes)
        problems.extend(found)
        image = render(grid, pal, hexes)
        png, meta = write(name, image)
        colours = sorted({hexes[c] for c in (pal["accent"], pal["skin"], INK_CODE)})
        print("%-11s %dx%d  %d colours  %s" % (name, image.width, image.height, len(colours),
                                              "ok" if not found else "%d problem(s)" % len(found)))
        print("            %s" % os.path.relpath(png, ROOT).replace(os.sep, "/"))
        print("            accent %s skin %s ink %s; no %s: the box paints that behind the bust"
              % (pal["accent"], pal["skin"], INK_CODE, PANEL_CODE))
        if args.dump:
            for line in grid.dump(legend):
                print("            " + line)
        if args.audit:
            for ty in range(SIZE // TILE):
                row = []
                for tx in range(SIZE // TILE):
                    seen = set()
                    for y in range(ty * TILE, ty * TILE + TILE):
                        for x in range(tx * TILE, tx * TILE + TILE):
                            cell = grid.get(x, y)
                            if cell:
                                seen.add(cell)
                    row.append(str(len(seen)))
                print("            tile row %d: colours per tile %s" % (ty, " ".join(row)))

    if problems:
        print("")
        for problem in problems:
            print("FAIL %s" % problem)
        return 1
    print("")
    print("every bust: 48x48, 3 entries, 1 pixel frame, at most 3 colours in any 8x8 tile, no $02")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
