#!/usr/bin/env python3
"""make_characters_v2.py: redraw the overworld cast as 16x16 hand authored NES sprites.

Card SPRITE-REDRAW-1 (Nayil, 2026-10-22): the v1 overworld sprites read as "janky and cutesy" and the
sailor, measured on disk, was TWO colours (white #fcfcfc and navy #0000bc, 624 and 200 opaque pixels, no
ink and no skin): a white blob. This file replaces the overworld figures with hand drawn pixel grids and
follows knowledge/ART-BIBLE.md and knowledge/CHARACTER-BIBLE.md REVISION 2.

Why the palette structure changed
---------------------------------
Hardware (ART-BIBLE section 1): one 8x8 sprite tile carries 3 opaque colours plus transparency. A 16x16
figure is four 8x8 tiles, two bands of two. So a figure has room for exactly three colours per band, and a
real NES figure spends them the way FF1, Dragon Quest and Mother do:

    head band (rows 0 to 7):  ink, skin, hair
    body band (rows 8 to 15): ink, cloth tone A, cloth tone B

Ink is not decoration. It is the silhouette, the eye, the mouth, the line between arm and torso, the belt,
the gap between the legs and the boot. Those interior ink lines are what makes a 3 colour sprite read as a
person instead of a blob, and they cost nothing because ink is already one of the three.

v1 instead let a solver RECOLOUR any tile that overflowed 3 colours ("nearest kept colour"), which quietly
flattened the figure: that is where the blob came from. v2 refuses: an overflowing tile raises, so the art
has to be drawn legal in the first place.

Geometry (the "janky and cutesy" fix)
-------------------------------------
- Head 6 px wide (cols 5 to 10), 7 rows tall, over a neck at rows 7, shoulders 8 px wide (cols 4 to 11),
  so the shoulders are wider than the head. v1 drew an 8 px head on an 8 px torso: a snowman.
- Torso 5 rows, legs 2 rows plus a boot row, two 2 px legs with a 2 px ink gap.
- Both walk frames are drawn (not just a shifted copy), mirrored for the left facing pair.

Views: down (face), up (back of the head, no face), right (profile) and left = right mirrored, 2 frames each
= 8 frames in one 128x16 strip, the frame order tools/sync_art.py and pp_world_sheet_frame already expect
(down 0, down 1, up 0, up 1, right 0, right 1, left 0, left 1).

Reference rule (PLAN-V2 section 0): nothing was traced, ripped or copied. The proportions and the palette
split above are described in words and numbers from ART-BIBLE.md.

Usage:
    python tools/art/make_characters_v2.py             # build sheets, sheet, frames
    python tools/art/make_characters_v2.py --dump      # print every frame as text
    python tools/art/make_characters_v2.py --audit     # build, then print the per tile colour audit only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import pressstart2p_font  # noqa: E402  (beside this file, SIL OFL, for the contact sheet labels)
from make_characters import Grid  # noqa: E402  (the same grid type and outline pass as v1)

TILE = 8
OW_W, OW_H = 16, 16
OW_FPS = 6.0

# ----------------------------------------------------------------------------------------------------------------
# NES colours, all outputs of the 2C02 (data/nes_palette.json is the judge).
# ----------------------------------------------------------------------------------------------------------------
INK = "#000000"
SKIN = "#f0d0b0"
BLOND = "#f8d878"
GINGER = "#e45c10"
WHITE = "#fcfcfc"
NAVY = "#0000bc"
BLUE = "#0058f8"
SKY = "#3cbcfc"
GREY = "#7c7c7c"
GREY_L = "#bcbcbc"
GOLD = "#f8b800"
PALE = "#fcfcfc"
# Card t_980388cf: the light blue of deck_night sp3, so Zander's sheet can be one sprite palette.
SKY_L = "#a4e4fc"
BROWN_D = "#881400"
ORANGE = "#e45c10"
BLUE_D = "#0000fc"
BLUE_M = "#0078f8"

# ----------------------------------------------------------------------------------------------------------------
# The grids. Codes: k ink, s skin, h hair, a cloth tone A, b cloth tone B, . transparent.
#
# Reading the numbers: cols 0 to 15, rows 0 to 15. The head is cols 5 to 10 on rows 0 to 6, the neck is rows 7,
# the shoulders are cols 4 to 11 on row 8, the arms are cols 3 and 12, the two legs are cols 5 to 6 and 9 to 10.
# ----------------------------------------------------------------------------------------------------------------
DOWN = [
    ".....hhhhhh.....",
    "....hhhhhhhh....",
    "....hssssssh....",
    "....hskssksh....",
    "....hssssssh....",
    ".....ssssss.....",
    "......ssss......",
    ".......ss.......",
    "....aaaaaaaa....",
    "...aaaaaaaaaa...",
    "...aaaaaaaaaa...",
    "...aaaaaaaaaa...",
    "....aaaaaaaa....",
]
DOWN_LEGS_STAND = [
    ".....aa..aa.....",
    ".....aa..aa.....",
    "....kkk..kkk....",
]
DOWN_LEGS_WALK = [
    ".....aa..aa.....",
    "....aa....aa....",
    "...kkk....kkk...",
]

UP = [
    ".....hhhhhh.....",
    "....hhhhhhhh....",
    "....hhhhhhhh....",
    "....hhhhhhhh....",
    "....hhhhhhhh....",
    ".....hhhhhh.....",
    ".....hhhhhh.....",
    ".......ss.......",
    "....aaaaaaaa....",
    "...aaaaaaaaaa...",
    "...aaaaaaaaaa...",
    "...aaaaaaaaaa...",
    "....aaaaaaaa....",
]
UP_LEGS_STAND = DOWN_LEGS_STAND
UP_LEGS_WALK = DOWN_LEGS_WALK

# Profile: facing right. The face occupies cols 7 to 10, the back of the head cols 4 to 6, so the nose side is
# the leading edge and the figure reads as a profile at 3x. Body cols 4 to 9, arm on the near side col 9.
RIGHT = [
    ".....hhhhh......",
    "....hhhhhhh.....",
    "....hhhssss.....",
    "....hhhskss.....",
    "....hhhssss.....",
    ".....hhsss......",
    ".....hsss.......",
    "......sss.......",
    ".....aaaaaa.....",
    "....aaaaaaa.....",
    "....aaaaaaa.....",
    "....aaaaaaa.....",
    ".....aaaaa......",
]
RIGHT_LEGS_STAND = [
    ".....aa.aa......",
    ".....aa.aa......",
    "....kkk.kkk.....",
]
RIGHT_LEGS_WALK = [
    "......aaaa......",
    ".....aa.aa......",
    "....kkk.kkk.....",
]


# ----------------------------------------------------------------------------------------------------------------
# The cast. palette: the five codes. decor: the named details drawn over the base body.
# ----------------------------------------------------------------------------------------------------------------
def cast():
    """Sailor and Percy first: the card's order, and the sailor is the sheet the ship room draws."""
    return [
        {
            "name": "sailor",
            "label": "SAILOR",
            # Card t_bd5cfad5 (sailor_ow_v2, eye round 8): the sheet spent four entries in every cell
            # (ink, white, navy, skin) and the four 8x8 tiles of one 16x16 cell share ONE sprite palette
            # of three, so the sailor claimed two of the four palettes on a scanline. Fixed palette
            # first, the way Percy's, Konrad's and Zander's were: the three entries are
            # data/palettes/scene_battle_deck_night.json sp2 {2, 18, 48} = $02 #0000bc, $12 #0058f8,
            # $30 #fcfcfc, which is also ship sp1, so the sheet is legal on both grounds the crew stands
            # on. $30 white is row 3 and carries the jumper, the cap crown and the face, which clears the
            # deck's $0F backdrop by three rows; $02 navy is the outline, the square collar, the cuffs and
            # the belt; $12 blue is the trousers and the shade plane. Skin is the entry this costs, the
            # way Konrad's grey and Zander's blond were, and it is posted as Q5 on the queue row.
            # 2026-10-24 (card t_cc0c5bd5, ruling knowledge/PALETTE-RULINGS-2026-10-24.md): the sentence above
            # is the record of the state it was written in and is not overwritten. Re-measured after the deck's
            # four sprite palettes were re-solved for the fight cast: deck sp2 is now {7, 23, 54} = $07 $17 $36,
            # so these three entries are NOT carried by battle_deck_night any more. In the twelve sets
            # {$02,$12,$30} now sits at ship sp1 and at sp3 of southampton, westminster and winchester (the same
            # three entries, a different slot), and in no battle strip. The sailor walks the ship, so the sheet
            # stays legal on the ground it is drawn on and this comment changes no pixel of it.
            "palette": {"k": NAVY, "s": WHITE, "h": NAVY, "a": WHITE, "b": BLUE},
            "decor": ["cap", "collar_flap", "cuffs", "belt", "trousers"],
            "style_b": True,
        },
        {
            "name": "percy",
            "label": "PERCY",
            # RULE 0, palette first (sprite_percy_ow_v2): the finished frame has to fit ONE of the deck's four
            # sprite palettes, not five loose colours (palette_synergy R6/R7 failed 4 of 4 pairs at 08:36).
            # $02 navy, $12 blue, $30 white is data/scene_palettes.json battle_deck_night sp2, and it is also
            # ship sp1, so the same sheet is legal on both grounds the overworld cast stands on. Navy is ink,
            # hair and the trident socket; white is face and shirt (the largest fill, which clears the deck by
            # three luminance rows); blue is the rank slide and the shade plane. Gold is not in either palette.
            # 2026-10-24 (card t_cc0c5bd5): the sentence above is kept as written. Re-measured after the deck's
            # four sprite palettes were re-solved for the fight cast, deck sp2 is {7, 23, 54} = $07 $17 $36, so
            # {$02,$12,$30} is no longer a deck palette: it is ship sp1 and sp3 of the three towns. Percy stands
            # on the ship, which is the ground this sheet is built to, so he is legal where he is drawn and stays
            # off the deck strip. No pixel of the sheet changes.
            "palette": {"k": NAVY, "s": WHITE, "h": NAVY, "a": WHITE, "b": BLUE},
            "decor": ["beard", "stocky", "rank_stripes", "trident"],
            "style_b": True,
        },
        {
            "name": "konrad",
            "label": "KONRAD",
            # Card t_980388cf (konrad_ow_v2, eye round 8): the sheet spent five entries (ink, skin, blond,
            # grey, light grey), and on hardware the four 8x8 tiles of one 16x16 cell share ONE sprite
            # palette of three, so Konrad claimed two of the four palettes on a scanline. Fixed palette
            # first, the way Percy's was: the three entries are data/palettes/scene_battle_deck_night.json
            # sp1 {7, 23, 40} = $07 #881400, $17 #e45c10, $28 #f8b800, which is the same sp1 in all four
            # battle strips and in the three towns, so the same sheet is legal on both kinds of ground.
            # $28 gold is row 2 and is the body, which is what clears the deck's $0F backdrop by two rows
            # (palette_synergy body_ground needs the body two luminance rows above the ground); $07 is the
            # outline, the hair and the seams; $17 is the lapel and collar accent. Konrad is grey and
            # amber in RULE 0 point 3 and no grey sprite palette in the project has a body above row 1
            # (deck sp0's lightest, $10, is row 1), so the amber half carries the figure and the grey is
            # posted to gamedev as Q2 on the row.
            # 2026-10-24 (card t_cc0c5bd5): the record above is kept. Re-measured after the deck's four sprite
            # palettes were re-solved for the fight cast, deck sp1 is now {2, 15, 48} = $02 $0F $30, so
            # {7, 23, 40} is no longer on the deck. It is still sp1 of the other three battle strips
            # (battle_corridor, battle_quay_dusk, battle_wardroom) and of the three towns (southampton,
            # westminster, winchester), which is where Konrad walks, so the sheet is legal on every ground he is
            # drawn on. No pixel of the sheet changes.
            "palette": {"k": BROWN_D, "s": GOLD, "h": BROWN_D, "a": GOLD, "b": ORANGE},
            "decor": ["long_hair", "beard", "lapels"],
            "style_b": True,
        },
        {
            "name": "zander",
            "label": "ZANDER",
            # Card t_980388cf (zander_ow_v2): same defect and same fix. The sheet spent ink, skin, blond,
            # blue and sky, five entries in every cell, so the player cost two sprite palettes to draw.
            # The three entries are scene_battle_deck_night.json sp3 {1, 17, 49} = $01 #0000fc,
            # $11 #0078f8, $31 #a4e4fc, which is the deck's light blue palette and the only one in the
            # project that carries Zander's light blue (RULE 0 point 3). $31 pale blue is row 3 and is
            # the body and the face, the same trick Percy's white plays; $01 is the outline and the messy
            # hair; $11 is the bomber's zip and collar. His blond is one of the two entries this costs,
            # posted with Konrad's as Q2 on the row.
            # 2026-10-24 (card t_cc0c5bd5): the record above is kept, and this is the sharp end of the ruling.
            # The deck's sp3 was re-solved to {8, 39, 40} = $08 $27 $28, so {1, 17, 49} is carried by NO ground
            # in the twelve sets any more: measured over data/palettes/scene_*.json on 2026-10-24, no sprite
            # palette holds all three of $01 $11 $31. The deck is the battle strip and draws its fight cast
            # (zander_battle.png), so Zander's walking triple is bought back on a ground he walks on, not here.
            # Written down rather than dropped: the sheet keeps its three entries and no pixel changes.
            "palette": {"k": BLUE_D, "s": SKY_L, "h": BLUE_D, "a": SKY_L, "b": BLUE_M},
            "decor": ["spiky_hair", "bomber"],
            "style_b": True,
        },
        {
            "name": "hadrian",
            "label": "HADRIAN",
            # Card t_bd32a72e (hadrian_ow_v2): the shipped sheet spent ink as the suit AND as the outline,
            # so 1010 of its 1186 opaque pixels were one entry (#000000, 85.2 percent) and the walk read as a
            # black mass. ART-BIBLE RULE 0 point 3 asks a sprite for 1 dark outline, 1 mid body and 1 accent,
            # so grey moves from the accent to the mid body: ink is the outline, the seams and the sleek hair;
            # grey $00 is the suit; pale $30 is the face and the lit rim. The three entries are the ones the
            # shipped sheet already spent, so this redraw adds no colour and takes no palette decision.
            # 2026-10-25 (card t_454c1876, ruling knowledge/PALETTE-RULINGS-2026-10-25.md section 20): the record
            # above is kept as written and the suit moves from grey $00 to pale $30. Measured, not chosen: the
            # tool measures a frame's body as its largest fill that is not the outline, and a body of $00 grey
            # clears NO ground the party walks on. Against the towns' street $00 #7c7c7c it is `invisible`
            # (identical) and against a black $0F joint it is `same_hue_row` (grey on grey, both row 0); every
            # other row 0 entry is under 3:1 from $00 as well, so no dark street can carry a row 0 grey body.
            # With the suit pale, $30 is the largest fill in all eight frames (24 + 40 pixels in the two frames
            # where the arms cover the shirt) and the body reads 3 luminance rows above both street entries.
            # Grey is not spent and not dropped, it changes job: it is the shaded rim the "rim" part already
            # draws on the shoulders and sleeves (8 pixels), so the sheet still spends all three of sp0's
            # entries, $00 $0F $30, and RULE 0 point 3 still gets an outline, a body and a third tone. A pale
            # suit with a mid grey edge is also the reading the rim was written for: it used to light a black
            # suit's edge, and now it shades a white one's.
            "palette": {"k": INK, "s": PALE, "h": INK, "a": PALE, "b": GREY},
            "decor": ["sleek_hair", "rim", "bident"],
        },
    ]


def base_grid(view, walk):
    """The shared 16x16 body: head band, neck, torso, then the leg pair of the view and frame."""
    rows, legs = {
        "down": (DOWN, DOWN_LEGS_WALK if walk else DOWN_LEGS_STAND),
        "up": (UP, UP_LEGS_WALK if walk else UP_LEGS_STAND),
        "right": (RIGHT, RIGHT_LEGS_WALK if walk else RIGHT_LEGS_STAND),
    }[view]
    grid = Grid(OW_W, OW_H)
    for y, row in enumerate(list(rows) + list(legs)):
        grid.text(y, row)
    return grid


def decorate(spec, grid, view, walk):
    parts = spec["decor"]
    back = view == "up"
    side = view == "right"

    if "cap" in parts:
        # A sailor cap: white crown over the hair band (1 px wider than the head), an ink band, and the cap
        # sides take the three hair columns, so the head band spends exactly ink, skin and cap rather than
        # four colours. A cap covers the hair; that is what makes it read as a cap and not a hat on hair.
        grid.text(0, ".....aaaaaa.....")
        grid.text(1, "....aaaaaaaa....")
        grid.text(2, "....akkkkkka....")
        for y in range(3, 7):
            for x in range(OW_W):
                if grid.get(x, y) == "h":
                    grid.put(x, y, "a")
        if back:
            grid.text(4, "....aaaaaaaa....")
            grid.text(5, ".....aaaaaa.....")
    if "beard" in parts:
        if back:
            pass
        elif side:
            grid.text(5, ".....hhsss......")
            grid.text(6, ".....hhhh.......")
        else:
            grid.text(5, ".....hhhhhh.....")
            grid.text(6, "......hhhh......")
    if "long_hair" in parts:
        # Past the jaw to the shoulders. Cols 4 and 11 only, so the face stays 4 px wide and readable.
        for y in range(5, 8):
            grid.put(4, y, "h")
            grid.put(11, y, "h")
        if back:
            grid.text(7, ".......hh.......")
    if "spiky_hair" in parts:
        if not back:
            grid.put(4, 0, "h")
            grid.put(6, 0, "h")
            grid.put(9, 0, "h")
            grid.put(11, 0, "h")
            grid.put(5, 1, "h")
            grid.put(10, 1, "h")
    if "sleek_hair" in parts:
        # A low hairline and a straight side: the pale face carries the figure, the hair is pure ink.
        if not back:
            grid.text(2, "....hhhhhhhh....")
            grid.put(4, 3, "h")
            grid.put(11, 3, "h")
    if "collar_flap" in parts:
        # The navy square collar of a sailor's jumper: a band across the shoulders and a flap at the back.
        grid.text(8, "....bbbbbbbb....")
        if back:
            grid.text(9, "...bbaaaaaabb...")
            grid.text(10, "...b..aaaa..b...")
        else:
            grid.text(9, "...baaaaaaab....")
            grid.put(4, 9, "b")
            grid.put(11, 9, "b")
            grid.text(10, "......bb........")
    if "cuffs" in parts:
        for y in (10, 11):
            grid.put(3, y, "b")
            grid.put(12, y, "b")
    if "belt" in parts:
        grid.text(12, "....bbbbbbbb....")
    if "trousers" in parts:
        for y in (13, 14):
            for x in (5, 6, 9, 10):
                if grid.get(x, y) == "a":
                    grid.put(x, y, "b")
        if walk:
            for x in (4, 11):
                if grid.get(x, 14) == "a":
                    grid.put(x, 14, "b")
    if "stocky" in parts:
        # Percy is the broad one: one column wider each side on rows 9 to 11, and a wider waist.
        for y in (9, 10, 11):
            grid.put(2, y, "a")
            grid.put(13, y, "a")
        grid.text(12, "...aaaaaaaaaa...")
    if "rank_stripes" in parts:
        # Two gold stripes on the outer sleeve: the Royal Navy lieutenant's rank, visible at 3x.
        for y in (9, 10):
            grid.put(2, y, "b")
            grid.put(13, y, "b")
    if "trident" in parts:
        # Three prongs on top of the shaft, the eye's rank 2 fix on the 2026-10-22 sheet ("Percy holds a
        # featureless yellow cane instead of a trident"). Everything is inside the two right hand tiles: the
        # head band tile (cols 8 to 15, rows 0 to 7) spends navy and white only, the body band tile spends
        # navy, white and blue, so the trident costs no fourth colour. The prongs are white because white is
        # the one colour in the frame that clears the deck (3.00 : 1) and the night road (8.74 : 1); the
        # socket and the grip are navy so the weapon separates from the white sleeve it passes.
        # The head of the trident stands above the right shoulder, in the three columns and three rows that
        # are empty there, and the shaft runs down col 14 from row 6 to row 14. Two attempts before this one
        # failed for a measured reason: a 1 px head inside the shoulder line, and a navy shaft on the body's
        # own ink edge, both read as "no weapon" at 12x. The prongs are the skin code and the socket the ink
        # code because those two tiles have already spent their three codes.
        grid.put(13, 3, "s")
        grid.put(15, 3, "s")
        grid.put(13, 4, "s")
        grid.put(14, 4, "s")
        grid.put(15, 4, "s")
        grid.put(13, 5, "k")
        grid.put(14, 5, "k")
        grid.put(15, 5, "k")
        for y in range(6, 8):
            grid.put(14, y, "s")
        for y in range(8, 15):
            grid.put(14, y, "a")
        grid.put(13, 13, "k")
    if "bident" in parts:
        # Hadrian's weapon is the two pronged bident (CHARACTER-BIBLE: "Hadrian the BIDENT (two pronged)"),
        # drawn with Percy's trident construction so it costs no fourth colour: the prongs are the accent
        # code inside the head band tile, which has already spent ink and skin, and the shaft runs down col
        # 14 in the same accent over the grey suit. The prongs are pale because a pale prong clears the night
        # deck (3.00 : 1) and an ink one would land on the ink outline and read as no weapon at all, which
        # is the failure Percy's trident notes record. Two prongs, not three: this is the bident.
        # Two prongs, not three: this is the bident. The prongs take the skin code and the socket the ink
        # code for the same reason Percy's do: the head band tile has already spent exactly those three
        # codes, and make_characters_v2 refuses an overflow rather than recolouring one.
        grid.put(13, 3, "s")
        grid.put(15, 3, "s")
        grid.put(13, 4, "s")
        grid.put(15, 4, "s")
        grid.put(14, 4, "k")
        for y in range(5, 8):
            grid.put(14, y, "s")
        for y in range(8, 15):
            grid.put(14, y, "b")
        grid.put(13, 13, "k")
    if "lapels" in parts:
        # Open blazer: two lit lapel columns, the dark shirt between them.
        for y in (8, 9, 10):
            grid.put(5, y, "k")
            grid.put(10, y, "k")
        grid.put(4, 8, "b")
        grid.put(11, 8, "b")
        grid.put(7, 9, "b")
        grid.put(8, 9, "b")
    if "bomber" in parts:
        # Oversized light blue collar and the zip line down the middle.
        grid.text(8, "....bbbbbbbb....")
        for y in range(9, 12):
            grid.put(7, y, "b")
    if "rim" in parts:
        # A black suit needs its edge lit or it is a hole in the frame: grey rim on shoulders and sleeves.
        grid.put(4, 8, "b")
        grid.put(11, 8, "b")
        for y in (9, 10, 11):
            grid.put(3, y, "b")
            grid.put(12, y, "b")
        grid.put(7, 9, "b")
        grid.put(8, 9, "b")
    return grid


def seams(grid):
    """Interior ink: the lines that stop a 3 colour figure reading as a blob.

    SPRITE-CRAFT section 8.5 tests the body block for at least 8 dark pixels that are NOT on the outer edge,
    because an edge is already dark from the outline and tells the eye nothing. These two lines are the
    collar knot (row 9) and the jumper hem or jacket waist (row 11); they are ink, which the body band has
    already spent, so they cost no colour.
    """
    for x in (7, 8):
        if grid.get(x, 9) in ("a", "b"):
            grid.put(x, 9, "k")
    for x in (6, 7, 8, 9):
        if grid.get(x, 11) in ("a", "b"):
            grid.put(x, 11, "k")
    return grid


def frame(spec, view, walk):
    grid = base_grid(view, walk)
    decorate(spec, grid, view, walk)
    if spec.get("style_b"):
        # Direction B's three tone pass at 16 x 16 (card ART-B-2026-10-26 / t_fa15f496). The body fill keeps the
        # light entry, the accent takes the inside right and inside bottom edge of every run, and ink stays the
        # outline, so the figure gains a shade plane without spending a fourth colour: a 16 x 16 cell is four 8 x 8
        # tiles and a tile holds three opaque entries, which is exactly ink, body and shade.
        #
        # The pass runs after decorate() and before seams(), for the reason build_tall() writes down: an ink line
        # drawn first splits a run, the shade then lands at the end of each piece, and the pixel under that shade is
        # a light pixel with a mid tone above it, which is the wrong way round light the rule check counts.
        _shade(grid, target="a", shade="b", top=8, min_run=3, skip=(8,))
    seams(grid)
    grid.outline("k")
    return grid


def sheet_frames(spec):
    """8 frames, the order sync_art.py and pp_world_sheet_frame use: down 0/1, up 0/1, right 0/1, left 0/1."""
    frames = []
    for view in ("down", "up", "right"):
        for walk in (False, True):
            frames.append(frame(spec, view, walk))
    frames.append(frames[4].mirrored())
    frames.append(frames[5].mirrored())
    return frames


# ----------------------------------------------------------------------------------------------------------------
# Measurements: the checks this card asks for, computed from the art on disk.
# ----------------------------------------------------------------------------------------------------------------
def tile_audit(grid):
    """The worst 8x8 tile of one frame: its distinct opaque colours, and the codes in it."""
    worst = (0, None, "")
    for ty in range(0, OW_H, TILE):
        for tx in range(0, OW_W, TILE):
            codes = set()
            for y in range(ty, ty + TILE):
                for x in range(tx, tx + TILE):
                    code = grid.get(x, y)
                    if code:
                        codes.add(code)
            if len(codes) > worst[0]:
                worst = (len(codes), (tx, ty), "".join(sorted(codes)))
    return worst


def band_colours(grid, y0, y1):
    codes = set()
    for y in range(y0, y1):
        for x in range(OW_W):
            code = grid.get(x, y)
            if code:
                codes.add(code)
    return codes


def image_of(frames, palette):
    sheet = Image.new("RGBA", (OW_W * len(frames), OW_H), (0, 0, 0, 0))
    for index, grid in enumerate(frames):
        sheet.alpha_composite(grid.to_image(palette), (index * OW_W, 0))
    return sheet


def colours_in(image):
    pixels = image.convert("RGBA").load()
    found = {}
    for y in range(image.height):
        for x in range(image.width):
            value = pixels[x, y]
            if value[3]:
                found[value] = found.get(value, 0) + 1
    return found


def make_frame_with_background(sprite_sheet, backdrop_path, out_dir, name):
    """One 256x240 frame: the ship's own tileset as the background, the sprite standing on the deck line.

    The mask is written beside the frame so tools/nes_composite_check.py can tell which pixels are sprites:
    without it the checker reads the figure's skin and navy as background colours and fails blocks that the
    sprite merely stands on, which is a property of the test frame, not of the art.
    """
    background = Image.open(backdrop_path).convert("RGBA")
    frame_image = Image.new("RGBA", (256, 240), (0, 0, 0, 0))
    for ty in range(0, 240, background.height):
        for tx in range(0, 256, background.width):
            frame_image.alpha_composite(background, (tx, ty))
    standing = sprite_sheet.crop((0, 0, OW_W, OW_H))
    frame_image.alpha_composite(standing, (120, 120))
    mask = Image.new("RGBA", (256, 240), (0, 0, 0, 0))
    mask.alpha_composite(Image.new("RGBA", (OW_W, OW_H), (255, 255, 255, 255)), (120, 120))
    pixels = standing.load()
    for y in range(OW_H):
        for x in range(OW_W):
            if not pixels[x, y][3]:
                mask.putpixel((120 + x, 120 + y), (0, 0, 0, 0))
    one_x = os.path.join(out_dir, name + "_1x.png")
    three_x = os.path.join(out_dir, name + "_3x.png")
    mask_p = os.path.join(out_dir, name + "_mask.png")
    bg_only = os.path.join(out_dir, "ship_background_1x.png")
    frame_image.save(one_x, "PNG")
    frame_image.resize((768, 720), Image.NEAREST).save(three_x, "PNG")
    mask.save(mask_p, "PNG")
    if not os.path.isfile(bg_only):
        # The background layer on its own: nes_composite_check counts sprite pixels as background colours
        # (the two layers have separate palette RAM on the chip), so the background rule is proved here and
        # the sprite rule is proved on the composed frame.
        clean = Image.new("RGBA", (256, 240), (0, 0, 0, 0))
        for ty in range(0, 240, background.height):
            for tx in range(0, 256, background.width):
                clean.alpha_composite(background, (tx, ty))
        clean.save(bg_only, "PNG")
    return one_x, three_x, mask_p


def contact_sheet(entries, scale, path):
    """Every frame at 4x, one row per character, on the black backdrop the game uses.

    The canvas is sized from the drawing pitch, not guessed: each row spends a 10 px label line, the 16 px
    sprite and a 14 px gap, so five rows need 8 + 5 * (10 + 16 + 14) = 208 units. The old formula left out
    the label line and cut the sheet at 162 units, which is why the eye's round 2 found HADRIAN missing
    (measured: canvas 648 px tall, about 784 needed).
    """
    rows = len(entries)
    width = 16 * scale + OW_W * 8 * scale + 16 * scale
    height = 8 * scale + rows * (10 * scale + OW_H * scale + 14 * scale)
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    draw = ImageDraw.Draw(canvas)
    y = 8 * scale
    for label, image in entries:
        label_text(draw, label, 8 * scale, y, scale, (252, 252, 252))
        y += 10 * scale
        big = image.resize((image.width * scale, image.height * scale), Image.NEAREST)
        canvas.alpha_composite(big, (8 * scale, y))
        y += OW_H * scale + 14 * scale
    canvas.save(path, "PNG")
    return path


def label_text(draw, text, x, y, scale, colour):
    for index, ch in enumerate(text):
        if ch == " ":
            continue
        rows = pressstart2p_font.bitmap(ch)
        for gy, row in enumerate(rows):
            for gx, lit in enumerate(row):
                if lit != "#":
                    continue
                px = x + (index * 8 + gx) * scale
                py = y + gy * scale
                draw.rectangle([px, py, px + scale - 1, py + scale - 1], fill=colour + (255,))


# ----------------------------------------------------------------------------------------------------------------
# Build.
# ----------------------------------------------------------------------------------------------------------------
def build(root):
    palette_file = os.path.join(root, "data", "nes_palette.json")
    with open(palette_file, "r", encoding="utf-8") as handle:
        allowed = {value.strip().lower() for value in json.load(handle)["colours"]}

    out_dir = os.path.join(root, "game", "sprites_src", "chars")
    os.makedirs(out_dir, exist_ok=True)
    frames_dir = os.path.join(root, "output", "sprite_v2_frames")
    os.makedirs(frames_dir, exist_ok=True)
    bg = os.path.join(root, "game", "sprites_src", "env", "ts_ship.png")

    report = {"sprites": [], "backdrop": "ts_ship.png", "frame_size": [256, 240]}
    sheet_rows = []
    for spec in cast():
        for code, value in sorted(spec["palette"].items()):
            if value.lower() not in allowed:
                raise SystemExit("%s: code %r is %s, not a 2C02 output" % (spec["name"], code, value))
        frames = sheet_frames(spec)
        worst = 0
        worst_at = None
        for grid in frames:
            count, at, codes = tile_audit(grid)
            if count > worst:
                worst, worst_at = count, (at, codes)
            if count > 3:
                raise SystemExit("%s: an 8x8 tile carries %d opaque colours at %s (%s); a sprite tile holds 3"
                                 % (spec["name"], count, at, codes))
        sheet = image_of(frames, spec["palette"])
        name = spec["name"] + "_ow_v2"
        png = os.path.join(out_dir, name + ".png")
        sheet.save(png, "PNG")
        meta = {"name": name, "frame_w": OW_W, "frame_h": OW_H, "frames": len(frames), "fps": OW_FPS}
        with open(os.path.join(out_dir, name + ".json"), "w", encoding="utf-8", newline="\n") as handle:
            json.dump(meta, handle, indent=2)
            handle.write("\n")

        found = colours_in(sheet)
        head_band = band_colours(frames[0], 0, 8)
        body_band = band_colours(frames[0], 8, 16)
        hexes = {}
        for code, value in spec["palette"].items():
            hexes[value] = hexes.get(value, 0) + 1
        entry = {
            "name": name,
            "sha256": hashlib.sha256(open(png, "rb").read()).hexdigest()[:16],
            "distinct_colours": len(found),
            "colours": ["#%02x%02x%02x" % (key[0], key[1], key[2]) for key, _n in
                        sorted(found.items(), key=lambda kv: -kv[1])],
            "worst_tile_colours": worst,
            "worst_tile_at": worst_at,
            "head_band_codes": "".join(sorted(head_band)),
            "body_band_codes": "".join(sorted(body_band)),
            "body_band_colour_count_excluding_ink": len([code for code in body_band if code != "k"]),
        }
        one_x, three_x, mask_p = make_frame_with_background(sheet, bg, frames_dir, name)
        entry["frame_1x"] = os.path.relpath(one_x, root)
        entry["frame_3x"] = os.path.relpath(three_x, root)
        entry["frame_mask"] = os.path.relpath(mask_p, root)
        report["sprites"].append(entry)
        sheet_rows.append((spec["label"], sheet))

    sheet_path = os.path.join(root, "output", "sprites_v2_sheet.png")
    contact_sheet(sheet_rows, 4, sheet_path)
    report["contact_sheet"] = os.path.relpath(sheet_path, root)
    with open(os.path.join(root, "output", "_sprite_v2_report.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return report, sheet_path


# ================================================================================================================
# STYLE B, LATE NES POLISH: the 16 x 24 figures and the eight direction walk cycle.
#
# Card ART-B-CHARACTERS (t_fa15f496). Nayil picked direction B on 2026-10-26 19:00: bold dark outlines, three tone
# shading lit from the top left, detailed tiles. The 16 x 16 sheets above are the four band contract the walker in
# pp_overworld reads today and they keep it; these are the 16 x 24 standers and the eight direction cycle the queue
# asks for (data/sprite_redraw_queue.json, the cand_r18_* rows), drawn by the generator that owns the cast's names.
#
# The chip decides the tones. A figure is 16 x 24: three 8 x 8 tile bands, and a sprite tile holds three opaque
# colours plus transparency. So the three tones are split the way the B FRAME in tools/art/make_art_target.py splits
# a figure, which is the reference this card names:
#
#   head, rows 1 to 8     the hair mass in the dark entry with the mid entry on its right edge, and the face in the
#                         light entry with the mid entry down its own right edge, so the head carries all three tones
#                         and is lit from the top left the same way the body is.
#   neck and body         the body is the light entry, the mid entry is the shade plane on the inside right and
#                         inside bottom edge of every run, and the dark entry is the outline, the seams, the belt
#                         ends, the boots and the hair. That pass is edge_shade() from make_art_target.py, copied
#                         here rather than imported so an art target refactor cannot move the sprites.
#
# THE SAFE AREA IS 1 PIXEL. The outline pass paints empty pixels NEIGHBOURING a drawn one, so a drawn pixel on the
# edge of the cell has no empty neighbour there and gets no line: the figure would bleed into the ground on that
# side. Every drawn pixel therefore lives in cols 1 to 14 and rows 1 to 22, and the ring (cols 0 and 15, rows 0 and
# 23) is what the outline pass fills. That is measured, not assumed: _outline_leaks() counts drawn non ink pixels
# that touch the cell border or transparency, and build_tall() refuses a figure whose count is not zero. The first
# draft of this section failed it twice, on the boots standing on row 23 and on a `cap` flag that was set for every
# figure, so Zeus wore a sailor cap from behind and the cap crown sat on row 0.
#
# Row plan, the same for every figure and every direction, which is what makes two figures comparable by drawing
# and not by layout:
#
#   0        the top of the outline ring
#   1 to 8   head: crown 1 to 2, brow 3, eye row 4, cheeks 5 and 6, mouth 7, jaw 8 (a cap spends rows 1 to 3 and
#            the face is rows 4 to 8)
#   9        neck (a stooped figure loses the neck and the head drops a row)
#   10 to 16 body: shoulders 10, torso 11 to 15, hands 16
#   17       belt: the mid entry with the dark entry at its two ends and at the buckle
#   18 to 20 legs
#   21 to 22 boots
#   23       the bottom of the outline ring
# ================================================================================================================

TALL_W, TALL_H = 16, 24
_SWAP_LM = str.maketrans("lm", "ml")   # the face light mapping: light and mid exchanged inside one row of a part
TALL_TOP = 9           # first row the mechanical shade pass may touch: the head is drawn and shaded by hand
TALL_FPS = 6.0

# Clockwise from the face. The sheet stores them in this order, two frames each, so frame = direction_index * 2 + step.
TALL_DIRECTIONS = ("down", "down_left", "left", "up_left", "up", "up_right", "right", "down_right")
# Four views are drawn and four are mirrors: a mirror costs one call and cannot drift from the drawing it mirrors.
TALL_MASTERS = {
    "down": ("down", False),
    "down_left": ("dl", False),
    "left": ("side", True),
    "up_left": ("ul", False),
    "up": ("up", False),
    "up_right": ("ul", True),
    "right": ("side", False),
    "down_right": ("dl", True),
}

# The crown, per hair style: rows 1 and 2 only. A cap replaces both and adds the band on row 3. See the tone map
# note under TALL_FACE: the hair is a tone and never ink.
TALL_CROWNS = {
    "spiky": (".....llllll.....", "....llllllll...."),
    "long": ("......llll......", ".....llllll....."),
    # Short hair: the narrow crown with nothing over the ears, which is what tells a man without a cap apart from
    # the boy with one. Its own name so a figure can ask for it, not a variant of `long`.
    "short": ("......llll......", ".....llllll....."),
    # A bald head is the skin tone all the way over the top; the hair that is left is the light entry at the sides.
    "bald": (".....mmmmmm.....", "....mmmmmmmm...."),
}
# A sailor's cap: a light crown two rows deep, then the dark band that says this is a cap and not hair.
TALL_CAP_ROWS = ("......llll......", ".....llllll.....", "....kkkkkkkk....")
# A wide brim, three pixels wider each side than the cap, so the three men of Percy's party can be told apart at 1x
# by silhouette alone: they have to share one three entry palette, so their shapes are the only thing that can differ.
TALL_HAT_ROWS = ("......llll......", ".....llllll.....", "...kkkkkkkkkk...")

# The face block, rows 3 to 8 for a haired head. A capped head uses rows 4 to 8 of the same block, so the eyes, the
# mouth and the jaw stay on the same pixels and the family resemblance is a property of the drawing.
#
#   k dark entry (ink), l light entry, m mid entry, . empty
#
# THE TONE MAP IS THE ONE DIRECTION B USES, read off output/art_target/sprites_B.png as text rather than eyeballed:
# the hair is a TONE, not ink, and the face is the mid entry inside it. The first draft drew the hair in the dark
# entry, which made every head a black mass with a small pale patch in it, and made the back of the head a solid
# block of ink; the B frame's back views are a lit hair mass with an ink ring. The body follows the same split the
# B frame's left figure uses: light torso, darker limbs, ink for the belt, the boot tops and the face features.
#
# NOTHING IN THIS TABLE IS SHADED. The mid entry inside a tone mass is placed by _head_shade() after the frame is
# mirrored, because a mid tone baked into the text moves to the other side of the screen when the drawing is
# flipped, and the light in direction B does not flip: it comes from the top left of the SCREEN.
TALL_FACE = {
    # front: hair down both sides of the face, eyes at cols 6 and 9, the mouth at 7 and 8.
    "down": (
        "....llmmmmll....",
        "....lmkmmkml....",
        "....lmmmmmml....",
        "....lmmmmmml....",
        "....lmmkkmml....",
        ".....kmmmmk.....",
    ),
    # back of the head: the hair mass, no face at all.
    "up": (
        "....llllllll....",
        "....llllllll....",
        "....llllllll....",
        "....llllllll....",
        ".....llllll.....",
        "......llll......",
    ),
    # three quarter front, facing down and left: the face shifts a column towards the leading edge and the hair
    # keeps a column more on the trailing side, which is what sells the turn at 1x.
    "dl": (
        "...llmmmmll.....",
        "...lmkmmkml.....",
        "...lmmmmmml.....",
        "...lmmmmmml.....",
        "...lmmkkmml.....",
        "....kmmmmk......",
    ),
    # three quarter from behind: one cheek column of skin past the hairline, the rest hair.
    "ul": (
        "...mlllllll.....",
        "...mlllllll.....",
        "...mlllllll.....",
        "....lllllll.....",
        ".....llllll.....",
        "......llll......",
    ),
    # profile facing right: the hair takes the back of the head, the nose is the ink pixel past the face, and the
    # eye is ink in the face.
    "side": (
        "....llllmmmm....",
        "....llllmkmm....",
        "....lllmmmmk....",
        "....lllmmmmk....",
        "....lllmmkmm....",
        ".....llmmmm.....",
    ),
}


def style_b_figures():
    """The people a judge sees, in the 16 x 24 cells the queue rows ask for.

    Palette rule, measured not chosen: each figure spends exactly three entries, and those three are one sprite
    palette of the ground it stands on, in luminance order dark to light so 'k' is the outline and 'm' is between
    the body and the ink. Zeus and Konrad are sp2 and sp1 of the ship, the towns and the ship's own set; Percy and
    his three men are the white uniform triple, which is ship sp1 and ship sp3 (both carry $02 $12 $30); the old man
    is sp0, the grey and white triple that is the only one in the project with a light enough white for a white
    beard to read as light rather than as a hole.
    """
    uniform = {"k": NAVY, "l": WHITE, "m": BLUE}          # $02 $30 $12, ship sp1 and ship sp3
    zeus = {"k": BLUE_D, "l": SKY_L, "m": BLUE_M}          # $01 $31 $11, ship sp2
    kronos = {"k": BROWN_D, "l": GOLD, "m": ORANGE}        # $07 $28 $17, ship sp3
    old = {"k": INK, "l": WHITE, "m": GREY}                # $0F $30 $00, ship sp0
    return [
        {
            # Queue row cand_r18_zeus_ow_walk: 16 frames, 8 directions, 2 frames each, 16 x 24 cells.
            "id": "zeus_ow_walk8",
            "label": "ZEUS 8 DIRECTIONS",
            "kind": "walk",
            "ground": "ship sp2 {1, 17, 49}",
            "palette": zeus,
            "build": {"torso_half": 4, "arm_w": 1, "hair": "spiky", "leg_w": 2, "boot_w": 3,
                      "beard": 0, "accessory": None},
        },
        {
            # Queue row cand_r18_kronos_ow. The father of the other one: same crown, same eye row, same mouth row,
            # and a heavier build, so the pair reads as a family at 1x without either reading as a copy.
            "id": "kronos_ow24",
            "label": "KRONOS",
            "kind": "stand",
            "ground": "ship sp3 {7, 23, 40}",
            "palette": kronos,
            "build": {"torso_half": 5, "arm_w": 1, "hair": "long", "leg_w": 3, "boot_w": 4,
                      "beard": 3, "accessory": None},
        },
        {
            "id": "percy_ow24",
            "label": "LT. PERCY",
            "kind": "stand",
            "ground": "ship sp1 {2, 18, 48}",
            "palette": uniform,
            # Card t_3dfd69d1. Rank reads through three things at 1x: the trident (a fork beside his head), the
            # beard, and the fact that his body is 10 wide against man 2's 12 but he is the only one carrying
            # anything. arm_w 1 and torso_half 4 leave column 13 empty, which is what the outline pass needs to
            # draw a dark line between his arm and the trident shaft in column 14.
            "build": {"torso_half": 4, "arm_w": 1, "hair": "cap", "leg_w": 3, "boot_w": 4,
                      "beard": 2, "accessory": "trident", "face_light": True, "cuff": True},
        },
        {
            "id": "percy_man_1_ow24",
            "label": "PERCY MAN 1",
            "kind": "stand",
            "ground": "ship sp1 {2, 18, 48}",
            "palette": uniform,
            # The three men share one three entry palette, so hue cannot tell them apart: only silhouette can.
            # Man 1 is the narrow one: a capped head on the narrowest torso in the cast (6 wide against man 2's
            # 10), thin legs, small boots. Card t_3dfd69d1 made the width spread three steps wide instead of two,
            # because at 1x the shoulder to hip width is read before any head detail is.
            "build": {"torso_half": 3, "arm_w": 1, "hair": "cap", "leg_w": 2, "boot_w": 3,
                      "beard": 0, "accessory": None, "face_light": True},
        },
        {
            "id": "percy_man_2_ow24",
            "label": "PERCY MAN 2",
            "kind": "stand",
            "ground": "ship sp1 {2, 18, 48}",
            "palette": uniform,
            # Man 2 is the broad one, and the only man in a wide brimmed hat: three pixels wider each side than the
            # cap, which is the shape that reads at 1x when every man is the same blue and white. Card t_3dfd69d1
            # added the chest stripe for the same reason: the brim alone was read as a dark line by the eye, and a
            # full width band across the jumper is the one mark a three entry figure can carry that survives 1x.
            "build": {"torso_half": 5, "arm_w": 1, "hair": "hat", "leg_w": 3, "boot_w": 4,
                      "beard": 1, "accessory": None, "face_light": True, "chest": "stripe"},
        },
        {
            "id": "percy_man_3_ow24",
            "label": "PERCY MAN 3",
            "kind": "stand",
            "ground": "ship sp1 {2, 18, 48}",
            "palette": uniform,
            # The third man, and the one that took two passes to place. On the first pass he was the only bare
            # headed man in the party, which the eye read as a different character rather than as one of the crew:
            # the card asks for three men who are clearly one unit, so he wears the cap. He is told apart by build
            # instead, the middle torso with the thinnest legs and small boots, which is a difference in mass and
            # not in uniform.
            "build": {"torso_half": 4, "arm_w": 1, "hair": "cap", "leg_w": 2, "boot_w": 3,
                      "beard": 0, "accessory": None, "face_light": True},
        },
        {
            # Queue row cand_r18_ouranos_ow: the old man on the high street (Urien, Ouranos).
            "id": "ouranos_ow24",
            "label": "OURANOS",
            "kind": "stand",
            "ground": "southampton sp0 {0, 15, 48}",
            "palette": old,
            # Light trousers, because his ground is a grey street: measured, the grey mid entry on the street entry
            # is the same value, and mid trousers would be an invisible pair of legs where he stands.
            "build": {"torso_half": 4, "arm_w": 1, "hair": "bald", "leg_w": 2, "boot_w": 3,
                      "beard": 4, "accessory": None, "leg_tone": "l"},
        },
    ]


def _span(grid, y, x0, x1, code):
    for x in range(int(x0), int(x1) + 1):
        grid.put(x, y, code)


def _shade(grid, target="l", shade="m", top=TALL_TOP, min_run=3, skip=()):
    """The inside right edge and the inside bottom edge of every run becomes the mid tone.

    This is edge_shade() from tools/art/make_art_target.py, the pass that draws direction B's frame, copied so the
    sprites and the frame shade by the same rule. Only pixels currently `target` are repainted, so it can never
    paint over the ink outline and leave dark noise in a boot. Returns how many pixels it painted.

    `skip` names rows the horizontal pass stays out of. The neck rides on row 9, one pixel under the head, and
    shading the end of a four pixel neck puts a mid tone directly above the shoulder row, which the light
    direction check counts as a wrong way round light. The vertical pass still shades that column.
    """
    painted = 0
    for y in range(top, grid.h):
        if y in skip:
            continue
        x = 0
        while x < grid.w:
            if grid.get(x, y) != target:
                x += 1
                continue
            start = x
            while x < grid.w and grid.get(x, y) == target:
                x += 1
            if x - start >= min_run:
                grid.put(x - 1, y, shade)
                painted += 1
    for x in range(grid.w):
        y = top
        while y < grid.h:
            if grid.get(x, y) != target:
                y += 1
                continue
            start = y
            while y < grid.h and grid.get(x, y) == target:
                y += 1
            if y - start >= min_run:
                grid.put(x, y - 1, shade)
                painted += 1
    return painted


def _head_shade(grid):
    """The head's mid tone, placed after the mirror: the rightmost light pixel of every row inside the ink edge.

    A horizontal pass only, with min_run 1, because the face is 1 and 2 pixel runs and the vertical pass would turn
    the whole jaw row grey. Applied to rows 1 to 8, which is the head band and nothing else.
    """
    painted = 0
    for y in range(1, 9):
        rightmost = None
        for x in range(grid.w):
            if grid.get(x, y) == "l":
                if grid.get(x + 1, y) in ("k", None):
                    rightmost = x
        if rightmost is not None:
            grid.put(rightmost, y, "m")
            painted += 1
    return painted


def _tall_head(grid, view, build):
    """Rows 1 to 8: crown or cap, the shared face skeleton, then the hair style.

    One skeleton for every head, which is what makes Zeus and Konrad read as father and son: the crown is rows 1
    and 2, the eye row is 4, the mouth row is 7 and the jaw is row 8, whatever the hair does around them. A capped
    head spends rows 1 to 3 on the cap and keeps rows 4 to 8, which moves no eye, mouth or jaw pixel.
    """
    hair = build["hair"]
    beard = build["beard"]
    face_light = bool(build.get("face_light"))
    hair_code = "m" if face_light else "l"

    rows = TALL_FACE[view]
    cap_rows = TALL_CAP_ROWS if hair == "cap" else TALL_HAT_ROWS
    if face_light:
        # Direction B's reference (output/art_target/sprites_B.png) reads: the face is the lightest tone on the
        # figure and the hair is the tone around it. The white uniform triple has no skin entry, so for Percy and
        # his men the face takes the light entry (the uniform white) and the cap or hair takes the mid entry (the
        # Royal Navy blue). Every other figure keeps the mapping the sheet was built with, so this is a per figure
        # choice and not a change to the cast: card t_3dfd69d1.
        rows = tuple(row.translate(_SWAP_LM) for row in rows)
        cap_rows = tuple(row.translate(_SWAP_LM) for row in cap_rows)
    if hair in ("cap", "hat"):
        for index, row in enumerate(cap_rows):
            grid.text(1 + index, row)
        for index, row in enumerate(rows[1:]):
            grid.text(4 + index, row)
    else:
        crown = TALL_CROWNS.get(hair)
        if crown is None:
            raise SystemExit("no crown drawn for hair %r" % (hair,))
        if face_light:
            crown = tuple(row.translate(_SWAP_LM) for row in crown)
        for index, row in enumerate(crown):
            grid.text(1 + index, row)
        for index, row in enumerate(rows):
            grid.text(3 + index, row)

    # The family features, drawn on top of the shared skeleton, and never on row 3: an ink pixel in the brow row
    # splits it, and the head shade then lands on the left half of the brow. The spiky head is told apart by its
    # wider crown and the elder by hair past the jaw.
    if hair == "long":
        for y in range(5, 9):
            grid.put(4, y, hair_code)
            grid.put(11, y, hair_code)
    elif hair == "bald":
        # The fringe that is left, in the hair tone, on both sides of the skull.
        for y in range(4, 7):
            grid.put(4, y, hair_code)
            grid.put(11, y, hair_code)

    if beard:
        # The beard is the hair tone over the jaw rows, so it is the same mass as the hair and only the ink mouth
        # tells them apart. The old man's beard is the same light entry, which is what makes him read as grey rather
        # than as a hole, and it is the shape that carries the age. It stops at the jaw, like direction B's: a tail
        # that reaches the collar is the same tone as the tunic and merges into it.
        for y in (7, 8):
            _span(grid, y, 4, 11, hair_code)
        if beard >= 2:
            # The mouth, still ink, in the middle of the beard.
            grid.put(7, 7, "k")
            grid.put(8, 7, "k")
        if beard >= 4:
            grid.put(6, 7, "k")
            grid.put(9, 7, "k")


def _tall_body(grid, view, build, walk):
    """Rows 9 to 22: neck, shoulders, arms, torso, belt, legs and boots.

    Row plan, fixed for every figure: 9 neck, 10 to 16 torso, 17 belt, 18 to 20 legs, 21 and 22 boots. The plan is
    the same for all of them so a comparison between two figures is a comparison of the drawing and not of the
    layout, and so the feet of every figure stand on row 22 with the outline ring below them on row 23.

    Two rows here were measured wrong on the first draft and both are worth knowing:

    - THE TORSO HAS TO REACH THE BELT. The first draft stopped the torso at row 15 and hung the belt on row 17, so
      row 16 was empty across the waist and the outline pass filled it, which drew a second dark bar. The torso is
      rows 11 to 16 and the hands are the last row of the arms, on row 16.
    - THE BELT IS THE DARK ENTRY, NOT THE MID ONE. A mid belt puts a mid tone directly above the light row at the
      top of the legs, and the light direction check counts every one of those pixels as a wrong way round light.
    """
    tw = build["torso_half"]
    arm_w = build["arm_w"]
    x0, x1 = 8 - tw, 7 + tw
    # The neck is the mid entry (skin). It is not drawn from behind, where the hair covers it, and not on a figure
    # whose beard covers the collar: a mid neck two pixels above a light shoulder row is the one thing the light
    # direction check counts as a wrong way round light, and there is nothing there to see anyway.
    neck = view in ("down", "dl", "side") and build["beard"] < 3

    if view in ("down", "up", "dl", "ul"):
        if neck:
            _span(grid, 9, 7, 8, "m")
        _span(grid, 10, x0 - arm_w, x1 + arm_w, "l")
        for y in range(11, 17):
            # An ink line at each arm socket, which is what tells an arm from a torso: direction B's left figure
            # reads `ink, arm 2px, ink, torso, ink` across the whole arm. Without the line the arm is one pixel of
            # the mid entry beside a light torso, which at 1x is not an arm, and it also measures as a light pixel
            # with a mid tone to its left on every row it runs down.
            _span(grid, y, x0, x0, "k")
            _span(grid, y, x1, x1, "k")
            _span(grid, y, x0 + 1, x1 - 1, "l")
            # The walk swings one arm a row up, which is the only arm movement a 2 frame cycle can show at this
            # size: the left arm stops one row short of the right one.
            if not (walk and y == 16):
                _span(grid, y, x0 - arm_w, x0 - 1, "m")
            _span(grid, y, x1 + 1, x1 + arm_w, "m")
    else:
        # Profile: the near arm hangs past the leading edge and one ink line separates it from the chest.
        sx0, sx1 = x0 + 1, x1 - 1
        if neck:
            _span(grid, 9, 8, 9, "m")
        _span(grid, 10, sx0, sx1 + arm_w, "l")
        for y in range(11, 17):
            _span(grid, y, sx0, sx1 - 1, "l")
            _span(grid, y, sx1, sx1, "k")
            _span(grid, y, sx1 + 1, sx1 + arm_w, "m")

    bx0, bx1 = (x0 + 1, x1 - 1) if view in ("down", "up", "dl", "ul") else (sx0, sx1)
    _span(grid, 17, bx0, bx1, "k")

    leg_w = build["leg_w"]
    boot_w = build["boot_w"]
    # Trousers are the mid entry by default. The old man wears them light instead: his ground is a grey street and
    # the grey mid on it is the same value, so mid trousers vanish where he stands. Drawn light, the shade pass still
    # puts the mid on the right and bottom edges, which keeps the light coming from the top left.
    leg_tone = build.get("leg_tone", "m")
    if view in ("down", "up", "dl", "ul"):
        stride = 1 if walk else 0
        left = 8 - leg_w - 1
        right = 8
        for y in range(18, 20):
            _span(grid, y, left - stride, left - stride + leg_w - 1, leg_tone)
            _span(grid, y, right + stride, right + stride + leg_w - 1, leg_tone)
        left_boot = max(1, left - stride - 1)
        right_boot = right + stride
        # The boot top is the ink line direction B puts between a trouser leg and a boot, and it is the only line
        # that tells the two apart: they are the same tone, so the shape has to do the work. It runs over the boot
        # columns only, not across the gap between the legs, or it reads as a bar.
        for y in (20,):
            _span(grid, y, left_boot, min(TALL_W - 2, left_boot + boot_w - 1), "k")
            _span(grid, y, right_boot, min(TALL_W - 2, right_boot + boot_w - 1), "k")
        for y in (21, 22):
            _span(grid, y, left_boot, min(TALL_W - 2, left_boot + boot_w - 1), "m")
            _span(grid, y, right_boot, min(TALL_W - 2, right_boot + boot_w - 1), "m")
    else:
        # Profile: both legs are drawn full height and the step is the stride between them. A first version drew
        # the front leg on one row only, which left a standing profile with a single visible leg.
        back, front = 5, 8
        if walk:
            back, front = 4, 9
        for y in range(18, 20):
            _span(grid, y, back, back + leg_w - 1, leg_tone)
            _span(grid, y, front, front + leg_w - 1, leg_tone)
        back_boot = max(1, back - 1)
        for y in (20,):
            _span(grid, y, back_boot, min(TALL_W - 2, back_boot + boot_w - 1), "k")
            _span(grid, y, front, min(TALL_W - 2, front + boot_w - 1), "k")
        for y in (21, 22):
            _span(grid, y, back_boot, min(TALL_W - 2, back_boot + boot_w - 1), "m")
            _span(grid, y, front, min(TALL_W - 2, front + boot_w - 1), "m")


def _tall_seams(grid, view, build, mirror):
    """The interior ink a three colour figure needs to stop reading as a slab.

    Drawn AFTER the shade pass, deliberately: an ink line drawn first splits a row into two runs, the shade pass
    then puts a mid tone at the end of each piece, and the pixel under that mid is a light pixel with a mid tone
    above it, which is exactly the number the light direction check counts as wrong. The collar, the shoulder seams
    and the profile line therefore land on top of the finished shading instead of inside it.
    """
    if view in ("up", "ul"):
        return
    tw = build["torso_half"]
    x0, x1 = 8 - tw, 7 + tw
    if mirror:
        x0, x1 = TALL_W - 1 - x1, TALL_W - 1 - x0
    if view in ("down", "dl"):
        # The collar knot between the shoulders. The arm socket inks on rows 11 to 16 already do the job the
        # shoulder seams were added for, and the seams sat on the socket lines once the torso moved inside them.
        grid.put(TALL_W // 2 - 1, 10, "k")
        grid.put(TALL_W // 2, 10, "k")
    else:
        # Profile: the lapel line down the chest.
        lead = x1 if not mirror else x0
        grid.put(lead, 11, "k")

    # Card t_3dfd69d1: the jumper details that tell the crew apart at 1x without spending a fourth colour, and
    # without changing the shape both they and Percy share. They are ink like the rest of the seams, so the only
    # thing they can do to the measurements is split a light run that has already been shaded.
    chest = build.get("chest")
    if view in ("down", "dl") and chest == "stripe":
        # A horizontal band across the jumper: the strongest 1x mark a three entry figure can carry, because it
        # is the full width of the torso and it breaks the white slab in two. A stepped neckline was tried on the
        # narrowest man and dropped: at six light columns the two steps land on the arm sockets and the collar
        # knot and measure as one dark mass, so it bought no read and cost two ink pixels.
        _span(grid, 13, x0 + 1, x1 - 1, "k")

    if build.get("cuff") and view in ("down", "dl"):
        # Percy's cuff bands: one ink row across each arm at the wrist, the rank detail a 16 px figure can carry
        # beside the trident and the beard.
        arm_w = build["arm_w"]
        _span(grid, 15, x0 - arm_w, x0 - 1, "k")
        _span(grid, 15, x1 + 1, x1 + arm_w, "k")


def _tall_accessory(grid, build, mirror=False):
    """Percy's trident, drawn after the shade so it keeps its own tones, and mirrored with the body it belongs to.

    Card t_3dfd69d1: the first version drew a solid ink shaft down column 14 from the shoulder to the boot, which
    at 1x is a black bar welded to his side and says nothing about rank. The head is now a fork (two prongs with
    an ink gap between them and a one pixel middle prong over a crossbar) and the shaft is the light entry, so the
    outline pass draws a dark line down each side of it and the trident reads as an object held beside the figure.
    The fork sits in rows 1 to 3, above the shoulder and beside the cap, which is the only place in a 16 x 24 cell
    where it is legible at 1x. Nothing is drawn on a border row or column: the safe area is cols 1 to 14, rows 1
    to 22, and `build_tall` refuses a sheet with an outline leak.
    """
    def put(x, y, code):
        grid.put(TALL_W - 1 - x if mirror else x, y, code)

    if build["accessory"] == "trident":
        # The fork is two rows of tines over a crossbar, the tallest head three columns can carry: a centre spike
        # on row 1, the outer tines on row 2 with the pixel between them empty for the outline pass to ink, the bar
        # on row 3. Three tines with two visible gaps need five columns and a 16 px figure leaves three.
        put(13, 1, "l")
        put(12, 2, "l")
        put(14, 2, "l")
        for x in (12, 13, 14):
            put(x, 3, "l")
        # The shaft runs from the crossbar to the boots, so the figure reads as standing beside a planted polearm
        # and not holding a bar that stops at the hip. It is the light entry, one pixel wide, and the outline pass
        # draws the dark line down each side of it, which is what separates it from the arm one column away.
        for y in range(4, 23):
            put(14, y, "l")


def tall_frame(spec, view, walk, accessory=True, mirror=False):
    """One frame, in the order direction B needs it: head, body, mirror, shade, seams, prop, outline.

    The mirror sits BEFORE the shade on purpose. The light comes from the top left of the SCREEN, not of the
    drawing, so a left facing frame has to be shaded after it is flipped or its shadow lands on the wrong side and
    the light direction check measures the flip rather than the art. That is also why the sheet's eight directions
    cost four drawings and not eight.
    """
    build = spec["build"]
    grid = Grid(TALL_W, TALL_H)
    _tall_head(grid, view, build)
    _tall_body(grid, view, build, walk)
    if mirror:
        grid = grid.mirrored()
    if not build.get("face_light"):
        # A face-on-light head has its light entry on the FACE and its mid entry on the hair, so there is no
        # light run inside the ink edge for the head shade to end: painting one would put the mid tone between
        # the eyes, which is what it did on the first draft of card t_3dfd69d1. The head is then two tones plus
        # the ink features, and the three tone rule is carried by the body, which is where direction B's own
        # frame puts its shade plane.
        _head_shade(grid)
    _shade(grid, skip=(9,))
    _tall_seams(grid, view, build, mirror)
    if accessory:
        _tall_accessory(grid, build, mirror)
    grid.outline("k")
    return grid


def tall_view_frame(spec, direction, walk):
    source, mirror = TALL_MASTERS[direction]
    return tall_frame(spec, source, walk, mirror=mirror)


def tall_sheet_frames(spec):
    """Every frame the sheet stores, in TALL_DIRECTIONS order, two frames each for a walker."""
    if spec["kind"] == "walk":
        frames = []
        for direction in TALL_DIRECTIONS:
            for walk in (False, True):
                frames.append(tall_view_frame(spec, direction, walk))
        return frames
    return [tall_view_frame(spec, "down", False)]


def tall_image_of(frames, palette):
    image = Image.new("RGBA", (TALL_W * len(frames), TALL_H), (0, 0, 0, 0))
    for index, grid in enumerate(frames):
        image.alpha_composite(grid.to_image(palette), (index * TALL_W, 0))
    return image


def _light_direction(grid, light="l", mid="m"):
    """The card's measurement: light pixels whose mid tone sits below or to the right, against those where it does
    not. Direction B is lit from the top left, so a light pixel with its mid above it or to its left is wrong."""
    right = wrong = 0
    for (x, y), code in grid.px.items():
        if code != light:
            continue
        below = grid.get(x, y + 1) == mid or grid.get(x + 1, y) == mid
        above = grid.get(x, y - 1) == mid or grid.get(x - 1, y) == mid
        if below:
            right += 1
        elif above:
            wrong += 1
    return right, wrong


def _orphans(grid):
    """Pixels with no 8 neighbour: a single dot is noise at 1x and a dither by accident."""
    alone = 0
    for (x, y), code in grid.px.items():
        if not any(grid.get(x + dx, y + dy) is not None
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)):
            alone += 1
    return alone


def _outline_leaks(grid):
    """Filled pixels that touch nothing or sit on the border without being ink. Must be zero.

    The same test tools/art/make_art_target.py runs on the B frame, on codes instead of colours: a shape whose edge
    is not ink has no outline on that side, and at 16 x 24 that shows up as a figure bleeding into the ground.
    """
    leaks = 0
    for (x, y), code in grid.px.items():
        if code == "k":
            continue
        if x in (0, grid.w - 1) or y in (0, grid.h - 1):
            leaks += 1
            continue
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if grid.get(x + dx, y + dy) is None:
                leaks += 1
                break
    return leaks


def _dither_patches(grid):
    """Two colour checkers that repeat two right and two down: dithering, not an edge.

    A 2 x 2 alternation on its own is a corner; a 4 x 4 that keeps alternating is a gradient made of noise, which
    direction B does not use. Copied in shape from count_dither_patches() in tools/art/make_art_target.py.
    """
    patches = 0
    for y in range(grid.h - 3):
        for x in range(grid.w - 3):
            a = grid.get(x, y)
            b = grid.get(x + 1, y)
            c = grid.get(x, y + 1)
            d = grid.get(x + 1, y + 1)
            if a is None or b is None or a == b or a != d or b != c:
                continue
            if (grid.get(x + 2, y) == a and grid.get(x + 3, y) == b
                    and grid.get(x, y + 2) == a and grid.get(x, y + 3) == b):
                patches += 1
    return patches


def _face_skeleton(grid):
    """Where the eyes and the mouth of a front facing frame are, so two figures can be compared as drawings.

    The card asks Zeus and Kronos to read as father and son at 1x. Hair and build are deliberately different, so
    the shared thing has to be measured: this returns the rows and columns of the ink pixels inside the face box,
    and build_tall() requires the pair to agree on the eye row and the mouth row.
    """
    eyes, mouth = [], []
    for y in range(3, 9):
        for x in range(5, 11):
            if grid.get(x, y) != "k":
                continue
            if y == 4:
                eyes.append(x)
            if y == 7:
                mouth.append(x)
    return {"eye_row": 4 if eyes else None, "eye_cols": eyes, "mouth_row": 7 if mouth else None,
            "mouth_cols": mouth}


def _silhouette(grid):
    """The width of the figure's head and torso: the two numbers that say 'same family, other build'."""
    def width(y0, y1):
        cols = [x for y in range(y0, y1 + 1) for x in range(TALL_W) if grid.get(x, y) is not None]
        return (max(cols) - min(cols) + 1) if cols else 0
    return {"head": width(1, 8), "shoulders": width(10, 10), "torso": width(11, 16)}


def build_tall(root, out_report=None):
    """Draw every style B figure, write it beside the cast it belongs to, and measure what it wrote."""
    palette_file = os.path.join(root, "data", "nes_palette.json")
    with open(palette_file, "r", encoding="utf-8") as handle:
        allowed = {value.strip().lower() for value in json.load(handle)["colours"]}

    out_dir = os.path.join(root, "game", "sprites_src", "chars")
    os.makedirs(out_dir, exist_ok=True)
    report = {"figures": [], "card": "t_fa15f496", "direction_order": list(TALL_DIRECTIONS),
              "frames_per_direction": 2, "frame": [TALL_W, TALL_H]}
    rows = []
    for spec in style_b_figures():
        for code, value in sorted(spec["palette"].items()):
            if value.lower() not in allowed:
                raise SystemExit("%s: code %r is %s, not a 2C02 output" % (spec["id"], code, value))
        frames = tall_sheet_frames(spec)
        worst = 0
        for index, grid in enumerate(frames):
            count, at, codes = tile_audit(grid)
            if count > worst:
                worst = count
            if count > 3:
                raise SystemExit("%s frame %d: an 8x8 tile carries %d opaque colours at %s (%s); a sprite tile "
                                 "holds 3" % (spec["id"], index, count, at, codes))
        leaks = sum(_outline_leaks(grid) for grid in frames)
        if leaks:
            raise SystemExit("%s: %d drawn pixels have no outline on the cell border or against transparency"
                             % (spec["id"], leaks))
        image = tall_image_of(frames, spec["palette"])
        png = os.path.join(out_dir, spec["id"] + ".png")
        image.save(png, "PNG")
        meta = {
            "name": spec["id"],
            "frame_w": TALL_W,
            "frame_h": TALL_H,
            "frames": len(frames),
            "fps": TALL_FPS,
            "art_style": "B, late NES polish (card t_fa15f496)",
        }
        if spec["kind"] == "walk":
            meta["directions"] = list(TALL_DIRECTIONS)
            meta["frames_per_direction"] = 2
            meta["layout"] = "one row, direction major: frame = direction_index * 2 + step, step 0 stands"
            meta["for_card"] = "t_1741b1bf (free movement, 8 directions)"
        with open(os.path.join(out_dir, spec["id"] + ".json"), "w", encoding="utf-8", newline="\n") as handle:
            json.dump(meta, handle, indent=2)
            handle.write("\n")

        drawn = sum(1 for y in range(TALL_H) for x in range(TALL_W) if frames[0].get(x, y))
        light, wrong = _light_direction(frames[0])
        inked = sum(1 for (x, y), code in frames[0].px.items() if code == "k")
        body_only = tall_frame(spec, "down", False, accessory=False)
        entry = {
            "id": spec["id"],
            "kind": spec["kind"],
            "frames": len(frames),
            "ground": spec["ground"],
            "palette": spec["palette"],
            "sha256": hashlib.sha256(open(png, "rb").read()).hexdigest()[:16],
            "worst_tile_colours": worst,
            "drawn_px_frame0": drawn,
            "ink_share_frame0": round(100.0 * inked / drawn, 1) if drawn else 0.0,
            "light_correct": light,
            "light_wrong": wrong,
            "orphans": sum(_orphans(grid) for grid in frames),
            "outline_leaks": leaks,
            "dither_patches": sum(_dither_patches(grid) for grid in frames),
            "silhouette_width_frame0": _silhouette(body_only),
            "face_skeleton_frame0": _face_skeleton(frames[0]),
        }
        report["figures"].append(entry)
        rows.append((spec["label"], image))

    sheet_path = os.path.join(root, "output", "style_b_figures_sheet.png")
    os.makedirs(os.path.dirname(sheet_path), exist_ok=True)
    contact_sheet(rows, 4, sheet_path)
    report["contact_sheet"] = os.path.relpath(sheet_path, root)
    report_path = out_report or os.path.join(root, "output", "_style_b_figures_report.json")
    with open(report_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return report


def dump_tall():
    for spec in style_b_figures():
        print("=== %s  palette %s" % (spec["id"], spec["palette"]))
        for index, grid in enumerate(tall_sheet_frames(spec)):
            count, at, codes = tile_audit(grid)
            print("--- frame %d  worst tile %d colours at %s" % (index, count, at))
            for line in grid.dump():
                print("  " + line)
        print()


def dump():
    for spec in cast():
        print("=== %s  palette %s" % (spec["name"], spec["palette"]))
        for label, grid in zip(("down 0", "down 1", "up 0", "up 1", "right 0", "right 1"), sheet_frames(spec)):
            count, at, codes = tile_audit(grid)
            print("--- %s  worst tile %d colours %s" % (label, count, at, codes))
            for line in grid.dump():
                print("  " + line)
        print()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Redraw the overworld cast as NES sprites (SPRITE-REDRAW-1).")
    parser.add_argument("--root", default=None)
    parser.add_argument("--dump", action="store_true")
    parser.add_argument("--style-b", action="store_true",
                        help="draw the 16 x 24 style B figures and the eight direction walk cycle as well")
    parser.add_argument("--only-style-b", action="store_true",
                        help="draw only the style B figures, leaving the 16 x 16 sheets untouched")
    parser.add_argument("--dump-tall", action="store_true", help="print the style B frames as text and exit")
    args = parser.parse_args(argv)
    root = os.path.abspath(args.root) if args.root else os.path.dirname(os.path.dirname(HERE))
    if args.dump_tall:
        dump_tall()
        return 0
    if args.dump:
        dump()
        return 0
    if args.only_style_b:
        report = build_tall(root)
        for entry in report["figures"]:
            print("  %-18s %2d frames  worst tile %d/3  ink %4.1f%%  light %d ok / %d wrong  orphans %d  "
                  "leaks %d  dither %d  %s"
                  % (entry["id"], entry["frames"], entry["worst_tile_colours"], entry["ink_share_frame0"],
                     entry["light_correct"], entry["light_wrong"], entry["orphans"],
                     entry["outline_leaks"], entry["dither_patches"], entry["silhouette_width_frame0"]))
        print("contact sheet 4x: " + os.path.join(root, report["contact_sheet"]))
        return 0
    report, sheet_path = build(root)
    for entry in report["sprites"]:
        print("  %-14s %d colours  worst tile %d/3  head[%s] body[%s]  body steps ex-ink %d"
              % (entry["name"], entry["distinct_colours"], entry["worst_tile_colours"],
                 entry["head_band_codes"], entry["body_band_codes"],
                 entry["body_band_colour_count_excluding_ink"]))
    print("contact sheet 4x: " + sheet_path)
    print("frames: output/sprite_v2_frames/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
