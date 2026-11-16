#!/usr/bin/env python3
"""video_builder.py: the video builder. It burns in the six shot captions and the opening title card.

Why this file exists
    Judge panel fix 4 (card t_e42a6944): a judge has to understand the claim of each shot without being
    told what to see. The six captions in knowledge/DEMO-SCRIPT.md say, in one line each, what a shot is
    evidence for, and an opening title card states the premise, which Meta model is the judge, and which
    NES hardware limits the build obeys. This tool burns those in, in the same caption font the rest of the
    video uses, so the deliverable carries its own explanation.

What it draws, and where the words come from
    Title card: the title attract scene before the take, dimmed under the caption font. The words state
    the premise (Kronos and Zeus reincarnated on the M3, every line judged by a Meta model inside a NES
    text box), the Meta model judge (muse-spark-1.3 for the TALK lines, muse-image-1.0 and sam-3.1 for the
    art and segmentation, read from tools/meta_client.py's DEFAULT_MODELS) and the NES hardware limits
    (one 256x240 screen, at most 16 colours on screen at once, no network call and no key in the build).
    The model ids are read from tools/meta_client.py at draw time, never typed here, so a rename there
    cannot strand a wrong name here, and the S1 cold boot caption is read from knowledge/DEMO-SCRIPT.md.
    Captions: the six shot captions, verbatim, read out of knowledge/DEMO-SCRIPT.md by
    tools/demo_overlay.py's shot_caption (the same reader the bake overlay uses), so the two tools cannot
    drift apart on a caption's wording.

The placement rule, as code
    A caption is drawn in a letterbox band added BELOW the 768x720 frame, never over a game pixel. This is
    knowledge/DEMO-SCRIPT.md section 4 rule 2 taken literally: the frame stays the game's own pixels. The
    band is 64 pixels tall and every caption is forced to fit two lines at the caption size; a caption that
    needs more lines is refused rather than clipped or shrunk.

The windows, as code
    The caption in and out seconds are the caption range column of knowledge/VIDEO-PLAN.md section 3, on
    the 180.00 s clock the demo script plans. The tool burns at those windows whatever source it is given;
    whether the take actually shows that scene at that second is the recorder's card (fix 1 and fix 3), not
    this one.

Usage
    python tools\\video_builder.py --plan
    python tools\\video_builder.py --title-card OUT.png
    python tools\\video_builder.py --captions DIR
    python tools\\video_builder.py --burn --source IN.mp4 --out OUT.mp4

Exit codes
    0  the plan printed, or the frames written, or the burn finished
    1  a caption or title line carries a long dash, a caption will not fit the band, a model id is missing,
       or ffmpeg failed
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import demo_overlay  # noqa: E402  (its shot_caption and palette reader)

FONT_PATH = os.path.join(ROOT, "assets", "fonts", "PressStart2P-Regular.ttf")
META_CLIENT = os.path.join(TOOLS, "meta_client.py")
# The title card's own shape is data: data/slice.json shots.title_card holds the clock, the seconds and
# the models' role, so the five second hold the judge panel asked for is a row the suite can read rather
# than a number typed into this tool twice (card t_5876de50 asked for four, card t_379273cc raised it).
SLICE_PATH = os.path.join(ROOT, "data", "slice.json")

# The game frame is 3x the 256x240 screen (tools/play_demo.py, header). The caption band is added below
# it, so no caption ever covers a game pixel.
SCALE = 3
FRAME_W, FRAME_H = 256 * SCALE, 240 * SCALE
BAND_H = 64
FULL_W, FULL_H = FRAME_W, FRAME_H + BAND_H

CAPTION_SIZE = 12
LINE_GAP = 6
TITLE_SIZE = 28
BODY_SIZE = 16
MARGIN = 8

# Caption in and out seconds, the caption range column of knowledge/VIDEO-PLAN.md section 3.
CAPTION_WINDOWS = {
    "S1": (1.00, 14.20),
    "S2": (16.60, 27.00),
    "S3": (29.40, 35.00),
    "S4": (39.60, 45.00),
    "S5": (79.60, 83.30),
    "S6": (113.03, 117.00),
}
SHOTS = ("S1", "S2", "S3", "S4", "S5", "S6")

# The card's length is not a constant here: it is data/slice.json shots.title_card.seconds, read by
# title_card_seconds(), so the slice is the one place a hold is written down.

# The title card shows the title attract scene (S1, 0:00 to 0:16 on the demo clock) as its backdrop, so a
# judge sees the game and not a black frame. The frame is sampled here: after the logo's 4 bar shimmer
# (5.80 s) and before the lightning (11.60 s), so the logo is up and the menu is not open yet.
TITLE_ATTRACT_T = 6.0
TITLE_DIM = 0.5          # how far the attract frame is pulled toward black under the text
TITLE_BLANK = 40         # vertical gap a blank title line occupies
TITLE_LINE_AFTER = 22    # vertical advance after a drawn title line

LONG_DASHES = ("\u2014", "\u2013", "\u2012", "\u2015")


class BuilderError(Exception):
    """The builder cannot draw or burn honestly. The message names what is missing or oversized."""


def _load_meta_default_models():
    """The Meta model ids from tools/meta_client.py DEFAULT_MODELS, read at call time, never typed here."""
    spec = importlib.util.spec_from_file_location("meta_client", META_CLIENT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    models = getattr(module, "DEFAULT_MODELS", None)
    if not isinstance(models, dict):
        raise BuilderError("tools/meta_client.py has no DEFAULT_MODELS, so the title card cannot name them")
    return models


def title_card_lines(models=None):
    """The opening title card's lines: the premise, the Meta model judge, then the NES hardware limits.

    The premise is the demo's own claim (knowledge/DEMO-SCRIPT.md S2: Kronos and Zeus reincarnated on the
    M3, and S5: a Meta model judges the line inside a NES text box). The model ids are the values of
    DEFAULT_MODELS, so a rename in meta_client.py changes the card and nothing is typed here. A missing
    model id refuses the card rather than drawing a blank.
    """
    models = models or _load_meta_default_models()
    for role in ("chat", "image", "segment"):
        if not models.get(role):
            raise BuilderError("DEFAULT_MODELS has no %r model, so the title card cannot name it" % role)
    lines = (
        "PRIMORDIAL PARADOX",
        "",
        "KRONOS AND ZEUS, REINCARNATED ON THE M3",
        "EVERY LINE IS JUDGED BY A META MODEL",
        "INSIDE AN NES TEXT BOX",
        "",
        "THE JUDGE: %s (TALK)" % models["chat"],
        "%s (ART)  %s (SEGMENT)" % (models["image"], models["segment"]),
        "",
        "NES LIMITS: 256x240, AT MOST 16 COLOURS",
        "NO NETWORK CALL, NO KEY IN THE BUILD",
    )
    for line in lines:
        for dash in LONG_DASHES:
            if dash in line:
                raise BuilderError("the title card line %r carries a long dash" % line)
    return lines


def title_card_shape(path=None):
    """The card's held seconds, clock and the models' role, read out of data/slice.json shots.title_card.

    The judge panel's fix 1 asks for a five second card (card t_379273cc; the 2026-11-14 panel asked for
    four, card t_5876de50); that number is a row of the slice, so the cut, the test and this tool read one
    value. A slice without the block is refused: a card whose length nobody wrote down is a card that can
    drift from the shot table.
    """
    path = path or SLICE_PATH
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            body = json.load(handle)
    except (OSError, ValueError) as error:
        raise BuilderError("cannot read %s for the title card's shape: %s" % (path, error))
    card = (body.get("shots") or {}).get("title_card")
    if not isinstance(card, dict):
        raise BuilderError("%s shots.title_card is missing, so no card can be timed" % path)
    seconds = card.get("seconds")
    if not isinstance(seconds, (int, float)) or seconds <= 0:
        raise BuilderError("%s shots.title_card.seconds is %r, not a positive number" % (path, seconds))
    clock = card.get("clock")
    if not isinstance(clock, list) or len(clock) != 2:
        raise BuilderError("%s shots.title_card.clock is %r, not two clock strings" % (path, clock))
    return card


def title_card_seconds(path=None):
    """How long the card is held, in seconds, as data/slice.json records it."""
    return float(title_card_shape(path)["seconds"])


def _overlay_layout():
    """The card's lines as rectangles in the overlay: text, pixel size, x, y, width, height, top to bottom."""
    lines = title_card_lines()
    title_font = _font(TITLE_SIZE)
    body_font = _font(BODY_SIZE)
    block = _title_block_height(lines)
    y = (FRAME_H - block) / 2
    out = []
    for index, line in enumerate(lines):
        if not line:
            y += TITLE_BLANK
            continue
        size = TITLE_SIZE if index == 0 else BODY_SIZE
        font = title_font if index == 0 else body_font
        width = font.getlength(line)
        out.append({"line": line, "size": size, "x": (FRAME_W - width) / 2, "y": y,
                    "width": width, "height": size})
        y += size + TITLE_LINE_AFTER
    return out


def title_line_boxes():
    """Each drawn line's pixel rectangle, rounded outward, so a frame test can count ink inside it.

    The cut's verify rows measure white pixels in these rectangles on the delivered frames, at a second the
    card is up and at a second after it: that is how "the title is in the first seconds" becomes a number
    instead of a claim.
    """
    boxes = []
    for item in _overlay_layout():
        x0 = int(item["x"]) - 2
        y0 = int(item["y"]) - 2
        x1 = int(item["x"] + item["width"]) + 3
        y1 = int(item["y"] + item["height"]) + 3
        boxes.append({"line": item["line"], "box": [max(0, x0), max(0, y0),
                                                   min(FRAME_W, x1), min(FRAME_H, y1)]})
    return boxes


def render_title_overlay(path):
    """A FRAME_W x FRAME_H RGBA overlay: the card's text over a half-black dim, for a live picture.

    This is the card the cut burns over S1's own attract loop (card t_5876de50): the dim is a translucent
    black layer, so the game keeps playing underneath and no second of picture is frozen, and the band
    below stays the caption band video_builder renders separately. The words are title_card_lines(), so
    the game's name and the Meta judge's model id come from the same reader the still card uses.
    """
    image = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, int(round(255 * TITLE_DIM))))
    draw = ImageDraw.Draw(image)
    for item in _overlay_layout():
        font = _font(item["size"])
        draw.text((item["x"], item["y"]), item["line"], font=font, fill=(255, 255, 255, 255))
    image.save(path)
    return path


def shot_caption(shot):
    """The shot's caption, verbatim, read out of knowledge/DEMO-SCRIPT.md by the bake overlay's reader."""
    return demo_overlay.shot_caption(shot)


def cold_boot_caption():
    """The S1 caption, verbatim: the cold boot claim the title card pairs with the attract scene."""
    return shot_caption("S1")


def _font(size):
    if not os.path.exists(FONT_PATH):
        raise BuilderError("%s is missing, so the builder cannot use the video's caption font" % FONT_PATH)
    return ImageFont.truetype(FONT_PATH, size)


def _wrap(text, size, width):
    """Greedy word wrap to a pixel width. PressStart2P advances one pixel per point (measured in
    demo_overlay.py), so this is arithmetic, but the width is measured with the font anyway so a longer
    advance cannot silently clip."""
    font = _font(size)
    limit = width
    words = text.split()
    out, current = [], ""
    for word in words:
        candidate = word if not current else current + " " + word
        if font.getlength(candidate) <= limit:
            current = candidate
        else:
            if current:
                out.append(current)
            current = word
    if current:
        out.append(current)
    return out


def _title_block_height(lines):
    """The vertical extent of the title text block, so it can be centred in the scene area."""
    height = 0
    for index, line in enumerate(lines):
        if not line:
            height += TITLE_BLANK
        else:
            height += (TITLE_SIZE if index == 0 else BODY_SIZE) + TITLE_LINE_AFTER
    return height


def _draw_caption_in_band(draw, caption):
    """Draw a caption in the bottom 64 px band, wrapped and centred at the caption size.

    The band is the same height and the same font as the caption bands burned over the source take, so the
    cold boot caption on the title card sits exactly where the S1 caption will sit once the take begins.
    """
    usable = FULL_W - 2 * MARGIN
    lines = _wrap(caption, CAPTION_SIZE, usable)
    if len(lines) > 2:
        raise BuilderError("the cold boot caption is %d lines and the band holds 2" % len(lines))
    font = _font(CAPTION_SIZE)
    line_h = CAPTION_SIZE + LINE_GAP
    block_h = len(lines) * line_h
    y = FRAME_H + (BAND_H - block_h) / 2
    for line in lines:
        width = font.getlength(line)
        draw.text(((FULL_W - width) / 2, y), line, font=font, fill=(255, 255, 255))
        y += line_h


def render_title_card(path, background=None):
    """A FULL_W x FULL_H title card: the title attract scene (or black) with the premise, the judge and
    the NES limits over it, and the S1 cold boot caption in the band below.

    `background` is a 768x720 image of the title attract scene. When given, it is dimmed toward black so
    the white caption font stays readable over it; when absent the card falls back to a black frame and
    the same text, so --title-card and the tests render without a source take.
    """
    lines = title_card_lines()
    image = Image.new("RGB", (FULL_W, FULL_H), (0, 0, 0))
    if background is not None:
        scene = Image.open(background).convert("RGB").resize((FRAME_W, FRAME_H))
        scene = Image.blend(scene, Image.new("RGB", scene.size, (0, 0, 0)), TITLE_DIM)
        image.paste(scene, (0, 0))
    draw = ImageDraw.Draw(image)
    title_font = _font(TITLE_SIZE)
    body_font = _font(BODY_SIZE)
    # The lines sit centred in the scene area, title first and body lines after.
    block = _title_block_height(lines)
    y = (FRAME_H - block) / 2
    for index, line in enumerate(lines):
        if not line:
            y += TITLE_BLANK
            continue
        font = title_font if index == 0 else body_font
        width = font.getlength(line)
        draw.text(((FULL_W - width) / 2, y), line, font=font, fill=(255, 255, 255))
        y += (TITLE_SIZE if index == 0 else BODY_SIZE) + TITLE_LINE_AFTER
    _draw_caption_in_band(draw, cold_boot_caption())
    image.save(path)
    return path


def render_caption_band(shot, path):
    """A transparent FULL_W x BAND_H band holding the shot's caption, centred, at the caption size.

    A caption that needs more than two lines at the caption size is refused: the line is wrong, not the
    font, and shrinking would break the shared caption font rule.
    """
    caption = shot_caption(shot)
    usable = FULL_W - 2 * MARGIN
    lines = _wrap(caption, CAPTION_SIZE, usable)
    if len(lines) > 2:
        raise BuilderError(
            "the %s caption is %d lines at size %d and the band holds 2; the line is wrong, not the font"
            % (shot, len(lines), CAPTION_SIZE)
        )
    image = Image.new("RGBA", (FULL_W, BAND_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = _font(CAPTION_SIZE)
    line_h = CAPTION_SIZE + LINE_GAP
    block_h = len(lines) * line_h
    y = (BAND_H - block_h) / 2
    for line in lines:
        width = font.getlength(line)
        draw.text(((FULL_W - width) / 2, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_h
    image.save(path)
    return path


def _probe_duration(source):
    """The source's duration in seconds, from ffprobe, or a refusal if it cannot be measured."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", source],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise BuilderError("ffprobe could not read %s: %s" % (source, result.stderr.strip()))
    try:
        return float(result.stdout.strip())
    except ValueError:
        raise BuilderError("ffprobe returned no duration for %s" % source)


def _extract_attract_frame(source, out_path, t=TITLE_ATTRACT_T):
    """One 768x720 frame of the title attract scene from the source take, for the title card backdrop.

    The frame is sampled at t seconds (6.0: after the logo's shimmer, before the lightning and the menu),
    so the card shows the game's own attract loop and never a foreign frame. A missing frame refuses the
    card rather than drawing the text over black and claiming it is the scene.
    """
    command = [
        "ffmpeg", "-y", "-v", "error",
        "-ss", str(t), "-i", source,
        "-frames:v", "1",
        "-vf", "scale=%d:%d" % (FRAME_W, FRAME_H),
        out_path,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0 or not os.path.exists(out_path):
        raise BuilderError("ffmpeg could not extract the title attract frame at %ss: %s"
                           % (t, result.stderr.strip()))
    return out_path


def build(source, out, title_png, caption_pngs):
    """Assemble the title card plus the caption-banded take into one mp4, and return the ffmpeg call."""
    duration = _probe_duration(source)
    card_seconds = title_card_seconds()
    if card_seconds <= 0:
        raise BuilderError("the title card duration must be positive")

    inputs = ["-loop", "1", "-framerate", "60", "-t", str(card_seconds), "-i", title_png, "-i", source]
    for png in caption_pngs:
        inputs += ["-loop", "1", "-framerate", "60", "-t", str(duration), "-i", png]

    # Stream indices: 0 title, 1 source, 2..7 the six caption bands.
    graph = ["[1:v]pad=%d:%d:0:0:color=black[base]" % (FULL_W, FULL_H)]
    prev = "base"
    for index, (shot, _win) in enumerate(zip(SHOTS, caption_pngs)):
        lo, hi = CAPTION_WINDOWS[shot]
        out_label = "c%d" % index
        graph.append(
            "[%s][%d:v]overlay=0:%d:enable='between(t,%.3f,%.3f)'[%s]"
            % (prev, 2 + index, FRAME_H, lo, hi, out_label)
        )
        prev = out_label
    graph.append("[0:v]format=yuv420p[title]")
    graph.append("[title][%s]concat=n=2:v=1:a=0[vout]" % prev)
    graph.append("[1:a]aresample=async=1,adelay=%d|%d[aout]" % (int(card_seconds * 1000), int(card_seconds * 1000)))

    command = [
        "ffmpeg", "-y", "-hide_banner", "-v", "error",
        *inputs,
        "-filter_complex", ";".join(graph),
        "-map", "[vout]", "-map", "[aout]",
        "-r", "60", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        out,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise BuilderError("ffmpeg failed: %s" % result.stderr.strip())
    return command


def main(argv=None):
    parser = argparse.ArgumentParser(description="the video builder: burn in the six captions and the title card")
    parser.add_argument("--plan", action="store_true", help="print the title card and the six caption windows")
    parser.add_argument("--title-card", help="render the opening title card to this PNG")
    parser.add_argument("--title-overlay", help="render the card as an RGBA overlay for a live picture to this PNG")
    parser.add_argument("--captions", help="render the six caption band PNGs into this directory")
    parser.add_argument("--burn", action="store_true", help="assemble the title card and the banded take")
    parser.add_argument("--source", help="--burn: the source take (768x720 mp4)")
    parser.add_argument("--out", help="--burn: the output mp4")
    parser.add_argument("--workdir", default=None, help="--burn: scratch dir for the rendered frames (default: the output dir)")
    args = parser.parse_args(argv)

    if args.plan:
        models = _load_meta_default_models()
        card = title_card_shape()
        print(json.dumps({
            "title_card": list(title_card_lines(models)),
            "title_card_clock": card.get("clock"),
            "title_card_seconds": card.get("seconds"),
            "font": FONT_PATH,
            "frame": [FULL_W, FULL_H],
            "band_height": BAND_H,
            "captions": [
                {"shot": shot, "window": list(CAPTION_WINDOWS[shot]), "caption": shot_caption(shot)}
                for shot in SHOTS
            ],
        }, indent=1))
        return 0

    try:
        if args.title_card:
            render_title_card(args.title_card)
            print("PASS  title card written to %s" % args.title_card)
            return 0
        if args.title_overlay:
            render_title_overlay(args.title_overlay)
            print("PASS  title overlay written to %s (%s s)" % (args.title_overlay, title_card_seconds()))
            return 0
        if args.captions:
            os.makedirs(args.captions, exist_ok=True)
            for shot in SHOTS:
                render_caption_band(shot, os.path.join(args.captions, "caption_%s.png" % shot))
            print("PASS  %d caption bands written to %s" % (len(SHOTS), args.captions))
            return 0
        if args.burn:
            if not (args.source and args.out):
                raise BuilderError("--burn needs --source and --out")
            out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
            workdir = args.workdir or out_dir
            os.makedirs(workdir, exist_ok=True)
            attract_png = os.path.join(workdir, "title_attract.png")
            _extract_attract_frame(args.source, attract_png)
            title_png = os.path.join(workdir, "title_card.png")
            render_title_card(title_png, background=attract_png)
            caption_pngs = []
            for shot in SHOTS:
                png = os.path.join(workdir, "caption_%s.png" % shot)
                render_caption_band(shot, png)
                caption_pngs.append(png)
            build(args.source, args.out, title_png, caption_pngs)
            print("PASS  %s written (title card + %d captions burned in)" % (args.out, len(SHOTS)))
            return 0
    except BuilderError as error:
        print("REFUSED  %s" % error)
        return 1
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
