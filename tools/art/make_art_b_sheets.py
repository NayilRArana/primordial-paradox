#!/usr/bin/env python3
"""make_art_b_sheets.py: the before and after sheets for the direction B opening redraw (card ART-B-OPENING).

What this is for
----------------
The card requires, for every asset it redraws, "a before and after sheet at 3x in output/art_b/<card>". A
sheet is only worth reading if the BEFORE half is really the art that was committed, so the before strips
are not a saved copy: they are read out of git, `git show HEAD:<path>`, at the moment the sheet is built.
The after half is read off the working tree. Nothing here draws art; it composes what the generators wrote.

Three sheets are written, one per queue row of knowledge/ART-STYLE.md section 7 that this card owns:

    title_before_after_3x.png   rows 1 and 3: the composed night frame, seven layers, sign and cone
    crawl_before_after_3x.png   row 2: the star twinkle, its three 8x8 frames
    drive_before_after_3x.png   row 3: the drive tile sheet, 24 tiles of 16x16

Before on top, after below, and a magenta rule between them, the same convention the art_target sheet uses.

Usage
    python tools/art/make_art_b_sheets.py
    python tools/art/make_art_b_sheets.py --json output/art_b/ART-B-OPENING/sheets.json
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "output", "art_b", "ART-B-OPENING")
TITLE = os.path.join("game", "sprites_src", "title")
DRIVE_SHEET = os.path.join("assets", "tiles", "drive", "drive_tiles.png")
SCALE = 3
RULE = (255, 0, 255)

sys.path.insert(0, os.path.join(ROOT, "tools", "art"))
import make_title_world  # noqa: E402


def repo_prefix():
    """The path from the repository root down to this project, e.g. "projects/primordial-paradox/".

    The repository is the Shared root, not this project, so `git show HEAD:<path>` takes a path from the
    Shared root. Measured the hard way: without this prefix every path came back "does not exist in HEAD"
    and the before half of the sheet was an empty frame.
    """
    result = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"], capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit("make_art_b_sheets: not a git checkout: %s" % result.stderr.strip())
    return result.stdout.strip()


PREFIX = None


def committed(relative):
    """One file exactly as HEAD has it, or None when HEAD has never carried it."""
    global PREFIX
    if PREFIX is None:
        PREFIX = repo_prefix()
    path = PREFIX + relative.replace("\\", "/")
    result = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + path], capture_output=True)
    if result.returncode != 0 or not result.stdout:
        return None
    return Image.open(io.BytesIO(result.stdout)).convert("RGBA")


def on_disk(relative):
    path = os.path.join(ROOT, relative)
    if not os.path.isfile(path):
        return None
    with Image.open(path) as image:
        return image.convert("RGBA")


def stack(before, after, path, labels):
    """Before over after at 3x, with a magenta rule between them and one label per half."""
    width = max(before.width, after.width)
    height = before.height + after.height + 2
    sheet = Image.new("RGB", (width, height), RULE)
    sheet.paste(before.convert("RGB"), (0, 0))
    sheet.paste(after.convert("RGB"), (0, before.height + 2))
    sheet = sheet.resize((width * SCALE, height * SCALE), Image.NEAREST)
    draw = ImageDraw.Draw(sheet)
    draw.text((4, 2), labels[0], fill=(255, 0, 255))
    draw.text((4, before.height * SCALE + 4), labels[1], fill=(255, 0, 255))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sheet.save(path)
    return path


def layer_table():
    with open(os.path.join(ROOT, "data", "title.json"), "r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return {row["name"]: row for row in data["layers"]}, data["sign"], data["cone"]


def frame_of(source, name, frame_index=0):
    """One layer's frame from either source: a path lookup on disk, or a git read for HEAD."""
    relative = os.path.join(TITLE, name + ".png").replace("\\", "/")
    image = (committed(relative) if source == "head" else on_disk(relative))
    if image is None:
        return None
    count = max(1, image.width // (image.height or 1))
    width = image.width // count
    return image.crop((frame_index * width, 0, frame_index * width + width, image.height))


def compose(source):
    layers, sign, cone = layer_table()
    specs = []
    for name, row in layers.items():
        image = frame_of(source, name)
        if image is not None:
            specs.append({"name": name, "y": row["y"], "speed": row["speed"], "frames": [image]})
    sign_image = frame_of(source, sign["name"], 0)
    cone_image = frame_of(source, cone["name"], 0)
    return make_title_world.compose(specs, camera_x=0.0, cone_at=cone["x"], cone_image=cone_image,
                                    sign_image=sign_image)


def sprite_sheet(source, name):
    relative = os.path.join(TITLE, name + ".png").replace("\\", "/")
    image = committed(relative) if source == "head" else on_disk(relative)
    if image is None:
        return None
    frames = max(1, image.width // image.height)
    width = image.width // frames
    out = Image.new("RGB", (image.width, image.height), (0, 0, 0))
    for index in range(frames):
        cell = image.crop((index * width, 0, (index + 1) * width, image.height))
        out.paste(cell.convert("RGB"), (index * width, 0), cell)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="write the before and after sheets for ART-B-OPENING")
    parser.add_argument("--json", help="write the sheet paths and their measurements here")
    args = parser.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)
    written = []

    before = compose("head")
    after = compose("disk")
    if before is None or after is None:
        raise SystemExit("make_art_b_sheets: the frame could not be composed from both halves")
    before.convert("RGBA").save(os.path.join(OUT, "title_before_256x240.png"))
    after.convert("RGBA").save(os.path.join(OUT, "title_after_256x240.png"))
    written.append(stack(before, after, os.path.join(OUT, "title_before_after_3x.png"),
                         ("BEFORE: HEAD, the night frame as committed", "AFTER: direction B")))

    before_star = sprite_sheet("head", "spr_title_star")
    after_star = sprite_sheet("disk", "spr_title_star")
    if before_star is not None and after_star is not None:
        written.append(stack(before_star, after_star, os.path.join(OUT, "crawl_before_after_3x.png"),
                             ("BEFORE: HEAD, the star twinkle", "AFTER: direction B")))

    before_drive = committed(DRIVE_SHEET)
    after_drive = on_disk(DRIVE_SHEET)
    if before_drive is not None and after_drive is not None:
        written.append(stack(before_drive, after_drive, os.path.join(OUT, "drive_before_after_3x.png"),
                             ("BEFORE: HEAD, the drive tile sheet", "AFTER: direction B")))

    payload = {"format": 1, "kind": "art_b_opening_sheets", "card": "ART-B-OPENING (t_3a2d0514)",
               "direction": "B, late NES polish", "scale": SCALE, "sheets": []}
    for path in written:
        with Image.open(path) as image:
            payload["sheets"].append({"file": os.path.relpath(path, ROOT).replace("\\", "/"),
                                      "pixels": list(image.size)})
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
    for path in written:
        print("sheet %s" % os.path.relpath(path, ROOT).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
