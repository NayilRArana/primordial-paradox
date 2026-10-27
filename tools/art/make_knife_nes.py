#!/usr/bin/env python3
"""make_knife_nes.py: Dad's Good Knife, one 16x16 icon and three slash frames, drawn from numbers in this file.

What it makes, all deterministic (no randomness, no image input, so a rerun writes the same bytes):

    game\\sprites_src\\weapons\\spr_pp_knife.png    64x16  four 16x16 frames, one row
    game\\sprites_src\\weapons\\spr_pp_knife.json   the sidecar tools\\sync_art.py mirrors into the build:
                                                  name, frame size, frame count, fps, the sprite palette
                                                  the sheet wears and one row per frame
    output\\knife_frames_4x.png                    every frame at 4x with its name and its step, for reading

Why four frames and not one. Card PP-KNIFE (t_503707c8) asks for the icon that a menu draws plus two or three
slash frames the battle screen draws while the swing is in the air. They live in ONE sheet because a sheet is one
sprite palette: the icon and the swing are the same knife, so they must never be able to drift into two colours.
Frame 0 is the icon; frames 1, 2 and 3 are the slash, in the order the director shows them.

The drawing is art direction B, "late NES polish" (bold outlines, three tone shading, detailed), which Nayil picked
on 2026-10-26 from the three directions in knowledge\\ART-STYLE.md (card PP-ART-TARGET, t_0e56c7c7). B's rule is
that every form is lit from the top left by a mechanical pass: the first pixel of a run is the rim light and the
last is the shadow. So every frame here is drawn as a flat mask of the shape and then given its three tones by
style_b(), which also puts the bold ink outline around the silhouette that the direction is named for. The pass, not
the artist, decides which tone lands where, which is what makes the icon and the three slash frames one object.

The palette is Zander's own reserved hero triple, [15, 33, 49] ($0F black outline, $21 blue body, $31 pale blue
accent) from data\\scene_palettes.json's hero_palettes. Two reasons, and both are measured rather than liked:

  1. The four battle strips declare party_cast (data\\scene_palettes.json), so on a battle screen the four sprite
     palettes ARE the four reserved hero triples (ruling 7.1, knowledge\\PALETTE-RULINGS-2026-10-25.md). A sheet
     painted in Zander's triple is carried by the strip the tutorial fight draws on without spending a fifth
     palette the chip does not have.
  2. The swing is drawn over the deck's bg2 cells ($00 grey, $30 white, $02 navy). Zander's $31 pale blue
     separates from all three by brightness row, where Konrad's grey body would vanish into the deck's own grey.
     tools\\palette_synergy.py measures the frame against the strip and is the check that settles it.

NES rules obeyed, and where they come from (NESdev wiki "PPU palettes" and "PPU OAM", read 2026-10-21):

    - a 16x16 frame is four 8x8 sprite tiles, and one sprite palette is 3 colours plus transparent entry 0, so
      every 8x8 tile here carries at most 3 opaque colours. This sheet spends exactly 3 opaque colours total;
    - black is $0F only, never the forbidden $0D;
    - flat colour, no gradient, no anti aliasing, no dithering: bold ink outline around the silhouette, one pale
      rim on the top left edge, one body tone between them and ink again on the bottom right edge. At 16x16 a 2 px
      checker reads as noise;
    - the rim is what makes the shape survive on any backdrop, which is why every drawing sits inside 1..14.6 in
      a 16 unit design space and the rim is added outside it.

Clean room (PLAN-V2 section 0): every shape is a primitive written in this file (thick segment, disc, rectangle).
No game art was downloaded, ripped, traced or measured. The only references are the hardware rules above and the
character bible's description of the knife as an ordinary kitchen knife from the family flat.

Usage:
    python tools\\art\\make_knife_nes.py
    python tools\\art\\make_knife_nes.py --root <repo>
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FRAME = 16
FRAMES = 4
PREVIEW_SCALE = 4
NEAREST = getattr(Image, "Resampling", Image).NEAREST

# 2C02 entries, never hex literals in the drawing code. These three ARE data/scene_palettes.json's
# hero_palettes.zander row: outline $0F, body $21, accent $31.
OUTLINE = 15   # $0F, the canonical black
BODY = 33      # $21, light blue, the blade's steel and the handle
LIGHT = 49     # $31, pale blue, the cutting edge and the swing's bright core
HEX = {15: "#000000", 33: "#3cbcfc", 49: "#a4e4fc"}

# Design space is 16 units for a 16 pixel frame: one design unit is one pixel, sampled at pixel centres.
FRAME_NAMES = ("icon", "slash_1", "slash_2", "slash_3")
# The swing's circle. One centre, one radius and one start angle for all three slash frames, so the three are one
# swipe growing along its arc instead of three streaks that happen to point the same way. The centre sits at the
# frame's lower right corner, which is where the arm holding the knife turns from, and radius 12 gives the trail about
# 1.6 px of curvature across the 16 px frame: enough to read as a swing, not so much that it reads as a banana.
# The sweep runs 195 to 255 degrees, up out of the lower left where the arm is.
ARC_CX, ARC_CY, ARC_R = 15.0, 15.0, 12.0
ARC_START, ARC_END = 195.0, 255.0
# Art direction B (late NES polish, picked by Nayil on 2026-10-26): every form is an ink outline, a pale rim on its
# top left edge, the body tone in the middle and ink again on its bottom right edge. The notes say what each frame
# is, so a reader can tell which of the three tones is doing the work.
FRAME_NOTES = (
    "knife at rest, on the diagonal: a kitchen knife with a straight spine up its top left, the belly curving away "
    "under it inked as the shadow side, two pale pixels where the spine catches the light, a short bolster and a "
    "plain handle at the lower left with no guard on it, which is what makes it a dad's knife and not a dagger",
    "the swing starts: the first third of a crescent, pale along its outer edge and inked along its inner one, "
    "coming up from the lower left where the arm is",
    "the swing is halfway: the same crescent past the middle of the arc, body tone showing between the rim and the "
    "shadow, so it reads as a blade travelling and not as a line",
    "the swing lands: the crescent reaches the far end of the arc and a three tone chip sits where it stops, which "
    "is the hit and not a splash",
)


# ---------------------------------------------------------------------------------------------------------------
# Rasterising. Every frame is a dict keyed by (x, y) holding one of the three entries.

def blank():
    return {}


def put(px, x, y, colour):
    if 0 <= x < FRAME and 0 <= y < FRAME:
        px[(x, y)] = colour


def disc(px, cx, cy, radius, colour):
    for y in range(FRAME):
        for x in range(FRAME):
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= radius * radius:
                put(px, x, y, colour)


def style_b(px):
    """The three tone pass of art direction B: bold ink outline, pale rim, body, ink again.

    Nayil picked B on 2026-10-26 (card PP-ART-TARGET, knowledge\\ART-STYLE.md section 4): "bold outlines, three
    tone shading, detailed tiles", lit from the top left by a mechanical pass where the first pixel of a run is the
    rim light and the last is the shadow. So a form is drawn here as a flat mask and this pass gives it the three
    tones, which is why no builder below picks a colour: the drawing says what shape it is and this says what the
    light does to it. A mask thinner than four pixels would lose its body tone to its own rim and shadow, so every
    builder keeps its stroke at four pixels or wider.
    """
    mask = set(px)
    out = {}
    # Ink outside the silhouette, four neighbours: the bold outline the direction is named for.
    for (x, y) in mask:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in mask and 0 <= n[0] < FRAME and 0 <= n[1] < FRAME:
                out[n] = OUTLINE
    for point in mask:
        out[point] = BODY
    # Rim light on the top left edge.
    for (x, y) in mask:
        if (x - 1, y) not in mask or (x, y - 1) not in mask:
            out[(x, y)] = LIGHT
    # Shadow last, so the bottom right edge is ink and a thin form reads as an outlined stroke.
    for (x, y) in mask:
        if (x + 1, y) not in mask or (x, y + 1) not in mask:
            out[(x, y)] = OUTLINE
    return out


# ---------------------------------------------------------------------------------------------------------------
# The four frames. Each builder draws a flat mask; style_b gives it the direction's three tones.

# The icon is laid out as a mask rather than assembled from primitives, because at 16x16 the shape IS the art: the
# eye reads a knife by its spine, its point and the seam where the blade meets the handle, and those are three pixels
# each. '#' is the flat shape; style_b gives it the direction's three tones and the ink outline afterwards. It is
# still drawn here by hand from the character bible's description of an ordinary kitchen knife from the family flat,
# not traced, sampled or measured from any picture.
ICON_MASK = (
    "................",   # 0
    ".........##.....",   # 1   the point, on the edge side, so the shape is a knife and not a spearhead
    "........####....",   # 2
    ".......#####....",   # 3
    "......######....",   # 4   the spine is the straight left column from here down
    "......#######...",   # 5   the belly bulges out on the right, six rows below the point
    "......#######...",   # 6
    "......#######...",   # 7
    "......######....",   # 8
    "......#####.....",   # 9   and curves back in to meet the heel
    ".....#######....",   # 10  the bolster, one row wider than the blade on both sides: the seam
    ".......###......",   # 11  handle, one pixel narrower than the blade
    ".......###......",   # 12
    ".......###......",   # 13
    ".......###......",   # 14  the pommel end
    "................",   # 15
)


def frame_icon():
    px = blank()
    for y, row in enumerate(ICON_MASK):
        for x, cell in enumerate(row):
            if cell == "#":
                put(px, x, y, BODY)
    return style_b(px)


def tapered_arc(px, cx, cy, radius, start_deg, end_deg, max_thickness, colour):
    """A swipe: discs stamped along a circle, thick in the middle and thin at both ends.

    Angles are degrees from +x and y grows downward, so 200 to 251 is the sweep up out of the lower left toward the
    upper right, which is the way a right-handed swing travels before it crosses the enemy.

    Two things were measured on this card before the shape was settled (2026-10-26). A constant thickness crescent
    reads to the eye as a solid object, "a banana or a boomerang", because a motion trail that is the same width at
    both ends has no direction in it. And a straight streak reads fine but its end cap is a stray tail. So the
    thickness follows sin(pi t): a point at each end, widest in the middle, and no cap for the eye to misread. All
    three slash frames ride the same circle and start at the same angle, so the swing is one swipe growing.
    """
    sweep = end_deg - start_deg
    steps = max(2, int(round(abs(sweep))))
    for index in range(steps + 1):
        t = index / float(steps)
        angle = start_deg + sweep * t
        thickness = max(0.55, max_thickness * math.sin(math.pi * t) ** 0.55)
        radians = angle * math.pi / 180.0
        disc(px, cx + radius * math.cos(radians), cy + radius * math.sin(radians), thickness, colour)


def frame_slash_1():
    px = blank()
    tapered_arc(px, ARC_CX, ARC_CY, ARC_R, ARC_START, 222.0, 1.7, BODY)
    return style_b(px)


def frame_slash_2():
    px = blank()
    tapered_arc(px, ARC_CX, ARC_CY, ARC_R, ARC_START, 238.0, 1.9, BODY)
    return style_b(px)


def frame_slash_3():
    px = blank()
    tapered_arc(px, ARC_CX, ARC_CY, ARC_R, ARC_START, ARC_END, 2.3, BODY)
    # The chip where the swing stops: one disc past the swipe's far end, so the hit is the same blur the swing is made
    # of and not a splash of anything.
    radians = ARC_END * math.pi / 180.0
    disc(px, ARC_CX + ARC_R * math.cos(radians), ARC_CY + ARC_R * math.sin(radians), 1.15, BODY)
    return style_b(px)


BUILDERS = (frame_icon, frame_slash_1, frame_slash_2, frame_slash_3)


def render(index):
    """One frame as a FRAME x FRAME RGBA array of 2C02 hex values, transparent elsewhere."""
    px = BUILDERS[index]()
    image = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for (x, y), colour in px.items():
        draw.point((x, y), fill=HEX[colour] + "ff")
    return image


def sheet():
    out = Image.new("RGBA", (FRAME * FRAMES, FRAME), (0, 0, 0, 0))
    for index in range(FRAMES):
        out.paste(render(index), (index * FRAME, 0))
    return out


# ---------------------------------------------------------------------------------------------------------------
# Facts about what was drawn, computed from the pixels so the sidecar cannot claim something the art does not do.

def frame_facts(index):
    image = render(index)
    pixels = image.load()
    opaque = {}
    for y in range(FRAME):
        for x in range(FRAME):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            key = "#%02x%02x%02x" % (r, g, b)
            opaque[(x, y)] = key
    hexes = set(opaque.values())
    entries = sorted(entry for entry, rgb in HEX.items() if rgb in hexes)
    tiles = []
    for ty in range(FRAME // 8):
        for tx in range(FRAME // 8):
            here = set()
            for y in range(ty * 8, ty * 8 + 8):
                for x in range(tx * 8, tx * 8 + 8):
                    if (x, y) in opaque:
                        here.add(opaque[(x, y)])
            tiles.append({
                "tile_x": tx,
                "tile_y": ty,
                "colours": len(here),
                "hex": sorted(here),
            })
    xs = [p[0] for p in opaque]
    ys = [p[1] for p in opaque]
    return {
        "index": index,
        "name": FRAME_NAMES[index],
        "x": index * FRAME,
        "y": 0,
        "w": FRAME,
        "h": FRAME,
        "tiles_w": FRAME // 8,
        "tiles_h": FRAME // 8,
        "sprite_objects": (FRAME // 8) * (FRAME // 8),
        "sprite_palette": "zander",
        "colours": {"outline": OUTLINE, "body": BODY, "accent": LIGHT},
        "hex": {"outline": HEX[OUTLINE], "body": HEX[BODY], "accent": HEX[LIGHT]},
        "opaque_pixels": len(opaque),
        "colour_count": len(entries),
        "bounds": {"x1": min(xs), "y1": min(ys), "x2": max(xs), "y2": max(ys)} if xs else None,
        "tiles": tiles,
        "note": FRAME_NOTES[index],
    }


def hex_for(colour):
    return HEX[colour]


# ---------------------------------------------------------------------------------------------------------------
# Writing.

def write_preview(path, sheet_image):
    scale = PREVIEW_SCALE
    width = FRAME * FRAMES * scale
    height = FRAME * scale + 18
    out = Image.new("RGB", (width, height), (0x00, 0x00, 0x00))
    enlarged = sheet_image.resize((FRAME * FRAMES * scale, FRAME * scale), NEAREST)
    background = Image.new("RGBA", (FRAME * FRAMES * scale, FRAME * scale), (0x7c, 0x7c, 0x7c, 255))
    background.alpha_composite(enlarged)
    out.paste(background.convert("RGB"), (0, 0))
    draw = ImageDraw.Draw(out)
    try:
        font = ImageFont.load_default()
    except Exception:  # pragma: no cover  a PIL without its default font is not a reason to lose the sheet
        font = None
    for index in range(FRAMES):
        label = "%d %s" % (index, FRAME_NAMES[index])
        draw.text((index * FRAME * scale + 2, FRAME * scale + 3), label, fill=(0xff, 0xff, 0xff), font=font)
    out.save(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build the Dad's Good Knife sheet.")
    parser.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        help="repository root (default: two folders above this file)")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root)
    folder = os.path.join(root, "game", "sprites_src", "weapons")
    os.makedirs(folder, exist_ok=True)
    os.makedirs(os.path.join(root, "output"), exist_ok=True)

    sheet_image = sheet()
    png_path = os.path.join(folder, "spr_pp_knife.png")
    sheet_image.save(png_path)

    facts = [frame_facts(index) for index in range(FRAMES)]
    sidecar = {
        "format": 1,
        "kind": "weapon_frames",
        "name": "spr_pp_knife",
        "title": "Dad's Good Knife: one 16x16 icon and three slash frames",
        "size": "%dx%d" % (FRAME * FRAMES, FRAME),
        "frame_w": FRAME,
        "frame_h": FRAME,
        "frames": FRAMES,
        "fps": 8.0,
        "grid": {"cols": FRAMES, "rows": 1, "cell_w": FRAME, "cell_h": FRAME,
                 "sheet_w": FRAME * FRAMES, "sheet_h": FRAME},
        "transparent": True,
        "layer": True,
        "layer_note": "the sheet is an OVERLAY, not a figure standing on ground: frame 0 is the icon a menu draws on "
                      "its paper, and frames 1 to 3 are the swing drawn over the enemy slot while the message plays. "
                      "tools/palette_synergy.py therefore asks R1b (ink or body clears 3:1 on the ground under it) "
                      "and not R1's feet-on-ground row gap.",
        "sprite_palette_count": 1,
        "sprite_palettes_used": ["zander"],
        "sprite_palette_note": "Zander's own reserved hero triple from data/scene_palettes.json hero_palettes: "
                               "$0F outline, $21 body, $31 accent. One palette for the icon and the swing, so the "
                               "knife can never drift into two colours, and a battle strip that declares party_cast "
                               "already carries it.",
        "sprite_objects_per_frame": 4,
        "max_sprite_objects_if_all_frames_on_screen": FRAMES * 4,
        "frame_roles": {"icon": 0, "slash_frames": [1, 2, 3]},
        "colour_count": 3,
        "colours_used": [
            {"index": OUTLINE, "hex": HEX[OUTLINE], "role": "outline", "usable": True},
            {"index": BODY, "hex": HEX[BODY], "role": "body", "usable": True},
            {"index": LIGHT, "hex": HEX[LIGHT], "role": "accent", "usable": True},
        ],
        "rule": "sprite art: at most 3 opaque colours plus transparency on any 8x8 tile; entry 0 of a sprite "
                "palette is transparency; black is $0F; no gradient, no anti aliasing, no dithering",
        "built_by": "tools\\art\\make_knife_nes.py",
        "frames_detail": facts,
    }
    json_path = os.path.join(folder, "spr_pp_knife.json")
    with open(json_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(sidecar, fh, indent=2)
        fh.write("\n")

    preview_path = os.path.join(root, "output", "knife_frames_4x.png")
    write_preview(preview_path, sheet_image)

    print("wrote %s" % os.path.relpath(png_path, root))
    print("wrote %s" % os.path.relpath(json_path, root))
    print("wrote %s" % os.path.relpath(preview_path, root))
    for fact in facts:
        print("  frame %d %-8s %d colours, tiles %s, bounds %s"
              % (fact["index"], fact["name"], fact["colour_count"],
                 "%d/%d/%d/%d" % tuple(t["colours"] for t in fact["tiles"]), fact["bounds"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
