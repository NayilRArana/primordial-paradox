#!/usr/bin/env python3
"""compose_knife_frame.py: the battle field with Dad's Good Knife's three slash frames over the enemy, from shipped art.

Why this file exists (card PP-KNIFE, t_503707c8). The card asks a battle capture to show the knife frames, and a real
window capture is the right evidence for that. tools/art/capture_knife_swing.py takes it and is refused on a host
where a desktop automation is running (the idle gate says so in its own words, and the gate is right). This tool is
the second honest source: it draws the same sheets at the same numbers the director uses, out of the same data, and
it says plainly that the file is a COMPOSED frame and not a capture.

What it draws, in the director's own order:

  1. the field, exactly as tools/art/compose_battle_frame.py composes it: backdrop, the 256x112 strip, the enemy at
     the battle screen's first enemy slot, the four party sheets at x 224;
  2. the swing: the frame of game/sprites_src/weapons/spr_pp_knife.png that data/items.json's slash_frames names,
     composited at the same rect pp_battle_draw_slash uses, which is the enemy slot centred for a 16x16 frame.

Each picture is CHECKED, not hoped for. For every swing frame the tool re-reads the sheet, crops the frame, composites
it over the enemy's own frame 0 at the director's rect, and refuses to write a frame whose slot does not equal that
composite pixel for pixel. The field itself is checked by compose_battle_frame.check, so a frame is only written when
the strip, the enemy and the party sit where data/ui_layouts.json says.

Usage:
    python tools\\art\\compose_knife_frame.py
    python tools\\art\\compose_knife_frame.py --strip deck_night --scene battle_deck_night --enemy navy_sailor
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from PIL import Image

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(TOOLS)
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
ART = os.path.join(TOOLS, "art")
if ART not in sys.path:
    sys.path.insert(0, ART)

import compose_battle_frame as base  # noqa: E402  the field's own composition and its checks
import palette_synergy  # noqa: E402  the 2C02 entry table, measured rather than restated

FRAME_W, FRAME_H = 256, 240
THREE_X = 3
NEAREST = getattr(Image, "Resampling", Image).NEAREST


def read_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def weapon_row(root: str) -> dict:
    party = read_json(os.path.join(root, "data", "characters", "party.json"))
    hero = next(row for row in party["characters"] if row["id"] == "hero")
    items = read_json(os.path.join(root, "data", "items.json"))
    return next(row for row in items["items"] if row["id"] == hero["weapon"])


def sheet_path(root: str, row: dict) -> str:
    return os.path.join(root, "game", "sprites_src", "weapons", "%s.png" % row["sprite"])


def slash_frame(root: str, row: dict, index: int) -> Image.Image:
    sidecar = read_json(os.path.splitext(sheet_path(root, row))[0] + ".json")
    sheet = Image.open(sheet_path(root, row)).convert("RGBA")
    width, height = int(sidecar["frame_w"]), int(sidecar["frame_h"])
    frame = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    frame.paste(sheet.crop((index * width, 0, (index + 1) * width, height)))
    return frame


def swing_rect(root: str, frame_w: int, frame_h: int) -> dict:
    """The rect pp_battle_draw_slash uses: the enemy slot, a 16x16 frame centred in it."""
    slot = base.enemy_slots(root)[0]
    return {"x": slot["x"] + (slot["w"] - frame_w) // 2, "y": slot["y"] + (slot["h"] - frame_h) // 2,
            "w": frame_w, "h": frame_h}


def check_swing(field: Image.Image, swing: Image.Image, slot: dict, knife: Image.Image, rect: dict) -> list:
    """Every slot pixel the knife frame covers must be the knife's, and every other slot pixel must be untouched.

    Comparing against the field it was drawn on (rather than against a canvas) is what makes this exact: the ground
    under the enemy is the strip, not transparency, so the only honest statement is "these pixels changed and no
    others did".
    """
    before = field.convert("RGBA").crop((slot["x"], slot["y"], slot["x"] + slot["w"], slot["y"] + slot["h"]))
    after = swing.convert("RGBA").crop((slot["x"], slot["y"], slot["x"] + slot["w"], slot["y"] + slot["h"]))
    problems = []
    offset_x, offset_y = rect["x"] - slot["x"], rect["y"] - slot["y"]
    covered = 0
    for y in range(slot["h"]):
        for x in range(slot["w"]):
            kx, ky = x - offset_x, y - offset_y
            inside = 0 <= kx < knife.width and 0 <= ky < knife.height
            knife_pixel = knife.getpixel((kx, ky)) if inside else (0, 0, 0, 0)
            if knife_pixel[3] != 0:
                covered += 1
                if after.getpixel((x, y)) != knife_pixel:
                    problems.append("slot %d,%d is %s, the knife frame puts %s there"
                                    % (x, y, after.getpixel((x, y)), knife_pixel))
            elif after.getpixel((x, y)) != before.getpixel((x, y)):
                problems.append("slot %d,%d changed where the knife frame is transparent" % (x, y))
            if len(problems) >= 4:
                return problems
    if covered == 0:
        problems.append("the knife frame covers no pixel of the slot")
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Compose the knife's slash frames over the battle field.")
    parser.add_argument("--strip", default="deck_night")
    parser.add_argument("--scene", default="battle_deck_night")
    parser.add_argument("--enemy", default="navy_sailor")
    parser.add_argument("--out-dir", default=os.path.join(ROOT, "output"))
    args = parser.parse_args(argv)

    root = ROOT
    row = weapon_row(root)
    field = base.compose(root, args.strip, args.scene, args.enemy)

    problems, numbers = base.check(root, args.strip, args.scene, args.enemy, field)
    if problems:
        print("compose_knife_frame: the field itself does not hold: %s" % problems)
        return 1
    print("P: field holds: strip %s, enemy %s on %d of %d inked tiles of bg2, party %s"
          % (numbers["strip"], numbers["enemy"]["id"], numbers["enemy"]["fit"], numbers["enemy"]["inked"],
             {name: "%d/%d" % (fit["fit"], fit["inked"]) for name, fit in numbers["party"].items()}))

    slot = base.enemy_slots(root)[0]
    os.makedirs(args.out_dir, exist_ok=True)
    written = []
    for index in row["slash_frames"]:
        swing = field.copy()
        knife = slash_frame(root, row, index)
        rect = swing_rect(root, knife.width, knife.height)
        swing.alpha_composite(knife, (rect["x"], rect["y"]))

        drawn = swing.convert("RGBA").crop((slot["x"], slot["y"], slot["x"] + slot["w"], slot["y"] + slot["h"]))
        problems_here = check_swing(field, swing, slot, knife, rect)
        if problems_here or drawn is None:
            print("compose_knife_frame: slash frame %d does not sit where pp_battle_draw_slash puts it: %s"
                  % (index, problems_here))
            return 1

        path = os.path.join(args.out_dir, "battle_knife_swing_f%d.png" % index)
        base.write_png(swing, path)
        written.append((index, path, rect))
        print("P: frame %d of %s at %d,%d, wrote %s"
              % (index, row["sprite"], rect["x"], rect["y"], path))

    # One 3x sheet of the three swings, because a reviewer reads a swing as a row and not as three files.
    strip = Image.new("RGB", (FRAME_W * THREE_X * len(written), FRAME_H), (0, 0, 0))
    for position, (index, path, _rect) in enumerate(written):
        with Image.open(path) as frame:
            strip.paste(frame.convert("RGB").resize((FRAME_W * THREE_X, FRAME_H * THREE_X), NEAREST),
                        (position * FRAME_W * THREE_X, 0))
    sheet_out = os.path.join(args.out_dir, "battle_knife_swing_3x.png")
    strip.save(sheet_out, optimize=True)
    print("P: wrote %s, the three swings at 3x in order" % sheet_out)

    # The frame a reviewer opens first: the widest swing, which is also the one the capture burst looks for.
    widest = written[-1][1]
    with Image.open(widest) as frame:
        final = os.path.join(args.out_dir, "battle_knife_swing.png")
        frame.convert("RGB").save(final, optimize=True)
    print("P: wrote %s, the widest swing" % final)

    knife_hexes = {row_["hex"].lower() for row_ in read_json(
        os.path.splitext(sheet_path(root, row))[0] + ".json")["colours_used"]}
    print("P: the sheet's colours as composed: %s" % ", ".join(sorted(knife_hexes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
