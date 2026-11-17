#!/usr/bin/env python3
"""check_nes_limits.py: the 256x240 and at most 16 colours limit, measured on the tree a build ships.

Why this exists
---------------
Judge panel 2026-11-17 fix 5 (card t_1b404055). The title card tells a judge that the build obeys "NES
LIMITS: 256x240, AT MOST 16 COLOURS", and a sentence on a card is not a measurement. This tool measures
both numbers on the tree, at build time, on a machine with no GameMaker installed:

  frame        the engine's own macros in game/scripts/pp_config/pp_config.gml (PP_FRAME_W, PP_FRAME_H)
               and every room under game/rooms (its roomSettings Width and Height) must hold 256 by 240.
               Two authorities on purpose: a macro a room disagrees with is a frame that changes when the
               room loads.
  title frame  the title screen is composed from the strips on disk at the y offsets data/title.json
               writes, by tools/art/scene_palette.py's compose_frame(), which is the art lane's single
               authority for how a frame is built. It must come out 256 by 240.
  colours      the colours the title screen can show are the union of the colours the composed frame
               draws and the colours data/palettes/scene_title.json declares: one backdrop, four background
               palettes of three, four sprite palettes of three. The card's claim is that this union is at
               most 16, so that is the number measured and printed, never a count typed into a caption.

What passing means, in four parts, so the check cannot go green by absence:

  1. pp_config.gml is readable and its two frame macros hold 256 and 240.
  2. every room's roomSettings hold 256 by 240, and the tree carries at least one room.
  3. the composed title frame is 256 by 240.
  4. the title screen's colour union is at most 16, counted from the composed pixels and the declared
     scene palette.

The numbers below the verdict are printed on a pass and on a failure, because a red run that says only
"FAIL" does not say how big the job is.

Usage
    python tools\\check_nes_limits.py
    python tools\\check_nes_limits.py --root <repo> --json output\\nes_limits.json

Exit codes
    0  every part holds, and the line it prints carries the measured frame and colour count
    1  any part fails, each failure on its own line

Related: tools\\check_data.py prints this tool's verdict in its own output (the repo check log a judge
reads), and tools\\video_builder.py draws the same verdict as the PASS badge beside the card's NES LIMITS
line, both by calling measure() and not by restating a number.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TOOLS_DIR, "art"))

import scene_palette  # noqa: E402  (the art lane's single authority for how a title frame is composed)

FRAME_W, FRAME_H = 256, 240
COLOUR_LIMIT = 16
CONFIG = os.path.join("game", "scripts", "pp_config", "pp_config.gml")
ROOMS = os.path.join("game", "rooms")
SCENE = "title"
MACRO_NAMES = ("PP_FRAME_W", "PP_FRAME_H")


class LimitError(Exception):
    """The tree cannot be measured: a file this check reads is missing, unreadable or malformed."""


def config_frame(root: str) -> tuple[int, int]:
    """(width, height) from pp_config.gml's own frame macros, the constants every module reads.

    Read with a pattern rather than imported, because the macros are GML: a checker that guessed the
    frame from a Python constant would measure itself instead of the engine.
    """
    path = os.path.join(root, CONFIG)
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            text = handle.read()
    except OSError as error:
        raise LimitError("cannot read %s for the frame macros: %s" % (path, error))
    frame = {}
    for name in MACRO_NAMES:
        match = re.search(r"#macro\s+%s\s+(\d+)\b" % name, text)
        if match is None:
            raise LimitError("%s has no '#macro %s <number>', so the frame cannot be read" % (path, name))
        frame[name] = int(match.group(1))
    return frame["PP_FRAME_W"], frame["PP_FRAME_H"]


def room_frames(root: str) -> dict:
    """{room name: (width, height)} from every room's roomSettings under game/rooms.

    A room is the frame the player sees, so a room that disagrees with the macros is the failure this
    part exists for. No room at all is refused rather than passed: an empty glob is not a pass.
    """
    frames = {}
    pattern = os.path.join(root, ROOMS, "*", "*.yy")
    for path in sorted(glob.glob(pattern)):
        try:
            with open(path, "r", encoding="utf-8-sig") as handle:
                body = json.load(handle)
        except (OSError, ValueError) as error:
            raise LimitError("cannot read %s for its room size: %s" % (path, error))
        settings = body.get("roomSettings") or {}
        width, height = settings.get("Width"), settings.get("Height")
        if not isinstance(width, int) or not isinstance(height, int):
            raise LimitError("%s roomSettings holds Width %r and Height %r, not two integers"
                             % (path, width, height))
        frames[body.get("name") or os.path.basename(path)] = (width, height)
    if not frames:
        raise LimitError("no room is written under %s, so no frame can be measured" % os.path.join(root, ROOMS))
    return frames


def title_screen(root: str) -> tuple[int, int, set]:
    """(width, height, colours) of the title screen: the composed frame plus the scene's declared palette.

    The pixels are measured from the frame tools/art/scene_palette.py composes out of the strips on disk,
    and the declared half is the backdrop and the eight palettes data/palettes/scene_title.json writes.
    The union is the set of colours that can reach the screen, which is what the 16 colour claim is about;
    a frame alone would miss the sprite colours a running game can still draw.
    """
    destination = os.path.join(tempfile.mkdtemp(prefix="pp_nes_limits_"), "title.png")
    try:
        scene_palette.compose_frame(root, destination)
    except (OSError, KeyError, ValueError) as error:
        raise LimitError("cannot compose the title frame from this tree: %s" % error)
    try:
        with Image.open(destination) as handle:
            image = handle.convert("RGBA")
        size = image.size
        counted = image.getcolors(maxcolors=1 << 20) or []
    except OSError as error:
        raise LimitError("cannot read the composed title frame %s: %s" % (destination, error))
    # A transparent pixel is not a colour on screen: the backdrop shows through it, and the backdrop is
    # declared below, so it is counted once from the scene and never twice from the hole.
    drawn = {pixel[:3] for _count, pixel in counted if pixel[3] > 0}
    try:
        scene = scene_palette.load_scene(root, SCENE)
    except (OSError, KeyError, ValueError, SystemExit) as error:
        raise LimitError("cannot read the %r scene palette for this tree: %s" % (SCENE, error))
    declared = {scene.rgb(entry) for entry in scene.bg_colours() | scene.sprite_colours() | {scene.backdrop}}
    return size[0], size[1], drawn | declared


def measure(root: str | None = None) -> dict:
    """The measured verdict: the frame, every room, the title frame, the colour count and the failures.

    A breach is a failure string, not an exception, so a caller can print all of them at once. An
    unreadable input raises LimitError, because "could not read the file" and "the file breaks the limit"
    are different jobs for whoever has to fix it.
    """
    root = root or ROOT
    failures = []
    frame = config_frame(root)
    if frame != (FRAME_W, FRAME_H):
        failures.append("%s holds PP_FRAME_W %d and PP_FRAME_H %d, not %dx%d"
                        % (CONFIG, frame[0], frame[1], FRAME_W, FRAME_H))
    rooms = room_frames(root)
    for name, size in sorted(rooms.items()):
        if size != (FRAME_W, FRAME_H):
            failures.append("room %s is %dx%d, not %dx%d" % (name, size[0], size[1], FRAME_W, FRAME_H))
    width, height, colours = title_screen(root)
    if (width, height) != (FRAME_W, FRAME_H):
        failures.append("the composed title frame is %dx%d, not %dx%d" % (width, height, FRAME_W, FRAME_H))
    if len(colours) > COLOUR_LIMIT:
        failures.append("the title screen can show %d colours (%s), and the limit is %d"
                        % (len(colours), ", ".join("#%02x%02x%02x" % rgb for rgb in sorted(colours)),
                           COLOUR_LIMIT))
    return {
        "pass": not failures,
        "root": root,
        "frame": [width, height],
        "config_frame": list(frame),
        "rooms": {name: list(size) for name, size in sorted(rooms.items())},
        "limit": COLOUR_LIMIT,
        "colours": len(colours),
        "colour_list": ["#%02x%02x%02x" % rgb for rgb in sorted(colours)],
        "failures": failures,
    }


def check(root: str | None = None) -> list:
    """The failures as plain strings, for a gate that collects them beside its own (tools/check_data.py)."""
    try:
        return measure(root)["failures"]
    except LimitError as error:
        return [str(error)]


def verdict_line(result: dict) -> str:
    """One line: PASS with the two measured numbers, or FAIL with every breach.

    The badge on the title card says PASS and nothing else, so the line a judge finds in the check log
    starts with the same word. The numbers follow it, so the word is a measurement and not a mood.
    """
    if result["pass"]:
        return "PASS %dx%d, %d colours on the title screen (limit %d)" % (
            result["frame"][0], result["frame"][1], result["colours"], result["limit"])
    return "FAIL " + "; ".join(result["failures"])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="measure the 256x240, at most 16 colours limit on this tree")
    parser.add_argument("--root", default=ROOT, help="repo root to measure (default: the one above tools/)")
    parser.add_argument("--json", default=None, help="write the measurement to this file")
    args = parser.parse_args(argv)

    try:
        result = measure(args.root)
    except LimitError as error:
        print("FAIL " + str(error))
        return 1
    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
    if result["pass"]:
        print("check_nes_limits: " + verdict_line(result))
        print("  rooms %d at %dx%d; the composed title frame draws %s"
              % (len(result["rooms"]), FRAME_W, FRAME_H, ", ".join(result["colour_list"])))
        return 0
    for line in result["failures"]:
        print("FAIL " + line)
    return 1


if __name__ == "__main__":
    sys.exit(main())
