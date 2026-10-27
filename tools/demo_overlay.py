#!/usr/bin/env python3
"""demo_overlay.py: the S5 and S6 caption overlay, with the Meta bake row and the network line.

Why this file exists
    The submission's strongest claim is that a Meta model answers the player inside a NES text box
    (knowledge/DEMO-SCRIPT.md section 4). A picture of a text box does not carry that claim on its own:
    what carries it is the bake row printed beside the shot, read out of `data/meta_bake.json`, which is
    the only record the game itself trusts (spec 19 section 2 and decision D5). This tool is that row,
    drawn in the same font as the rest of the video, for the two shots that prove it: S5 (the dock office,
    Nye's page) and S6 (the TALK fight and the offline shot).

What it draws, and where the words come from
    S5, Meta shot 1, 1:23.4 to 1:27.4 (section 4): the shot's caption, then `model`, `mode`, `backend`,
    `created_at`, the row id and its `request_hash`, all read from the `npc` row for Nye.
    S6, Meta shot 2, 2:15.03, 2:18.53 and 2:23.53: the shot's caption, one bake header, then one line per
    TALK turn (`model` on the header, a different `request_hash` on each of the three rows, which is what
    proves three calls at three scene states and not one line reused), then the network line.
    S6, 2:34.40 to 2:38.40 (section 5): the network line says the adapter has been dead since the first
    frame and that the replies shown came from `data/meta_bake.json`. When the bake in the file records a
    live network the same drawing has a live network line instead, because a line that always says "dead"
    would be a claim the file does not make.

The three rules from section 4, as code
    1. EVERY BAKE VALUE IS PRINTED EXACTLY AS THE FILE HOLDS IT. No reformatting, no re-casing, no
       rounding. A row, or a field of a row, that is missing is an OverlayError: the booth stops, which is
       better than a receipt that lies. Nothing in this file types a model name, a time or a hash.
    2. THE OVERLAY NEVER COVERS A TEXT BOX. Two boxes exist and both are drawn from the game's own
       geometry, not from a guess: the dialogue box at (8, 168) 240x64 (specs/05-dialogue.md line 10) and
       the battle window at (0, 0) 256x48 plus the command menu from y 168 (game/scripts/
       pp_battle_director/pp_battle_director.gml lines 949 to 952, specs/07-battle-director.md line 47).
       All four numbers are in 256x240 game space and are multiplied by the frame's own 3, so a shot's
       plate is placed above or below them and a plate that would touch one is refused.
    3. THE FRAME STAYS THE GAME'S PIXELS. The default plate sits inside the 768x720 frame, which is the
       2026-10-27 card's rule ("inside the 768x720 frame, never over the text box"). `--below` draws the
       plate on an extended 768x(720+band) canvas instead, which is section 4 rule 2 taken literally and
       is what a burn-in for the booth wants when the game's art has to stay uncovered.

The frame test
    `--check` is the test the judge panel's S5 and S6 frames are read by, and it is a measurement, not a
    print. It re-renders the same shot from the same source, then measures four things: the plate really
    changed pixels inside its own rectangle, ink of the caption colour exists on every bake line, the
    same render with the bake lines blanked has far fewer ink pixels on exactly those lines (so the
    pixels found are the row's own words and not the plate's edge), and every text box rectangle is
    byte identical to the source frame. Outside the plate, nothing may change at all.

Usage
    python tools\\demo_overlay.py --shot S5 --rows
    python tools\\demo_overlay.py --shot S5 --frame output\\judge_frames\\x_f05.png --out output\\demo\\overlay\\S5.png
    python tools\\demo_overlay.py --shot S6 --frame IN.png --out OUT.png --below
    python tools\\demo_overlay.py --check --shot S6 --source IN.png --frame OUT.png
    python tools\\demo_overlay.py --times --shot S6 --at 138.0

Exit codes
    0  the render was written, or --rows printed, or --check passed
    1  the overlay refused to draw (a row or field is missing, the frame is not 768x720, the plate would
       cover a text box, a value carries a long dash), or a check failed

Fonts and colours: the caption font is `assets/fonts/PressStart2P-Regular.ttf`, the font the video's
captions are burned in with (the same file the cut builder binds to `$FONT`). The plate, its border and
the badge take their colours from `data/palette.json` roles, so nothing here invents a colour either.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(ROOT, "assets", "fonts", "PressStart2P-Regular.ttf")
PALETTE_PATH = os.path.join(ROOT, "data", "palette.json")
BAKE_PATH = os.path.join(ROOT, "data", "meta_bake.json")
SCRIPT_PATH = os.path.join(ROOT, "knowledge", "DEMO-SCRIPT.md")
RECEIPT_DIR = os.path.join(ROOT, "data", "ai_cache", "bridge")

# The recording is 3x the 256x240 screen (tools/play_demo.py, header). Every game space number below is
# multiplied by this, once, in render(), so the two spaces cannot drift apart in the middle of the file.
SCALE = 3
FRAME_W, FRAME_H = 256 * SCALE, 240 * SCALE

# Text boxes, in 256x240 game space, with the file and line each number comes from.
DIALOGUE_BOX = (8, 168, 240, 64)   # specs/05-dialogue.md line 10: box 240x64 at (8, 168)
BATTLE_BOX = (0, 0, 256, 48)       # pp_battle_director.gml: pp_battle_text_box_x1 .. y2
BATTLE_MENU_TOP = 168              # specs/07-battle-director.md line 47 (PP_MENU_TOP)

# Which rectangle each shot must leave alone. S5 is an overworld page, so its box is the bottom one. S6
# is the battle, whose message window is the top 48 rows and whose command menu starts at y 168, so both
# of those are refused and the plate lives in the band between them.
FORBIDDEN = {
    "S5": (("dialogue box (specs/05-dialogue.md line 10)", DIALOGUE_BOX),),
    "S6": (
        ("battle text window (pp_battle_director.gml text box y2)", BATTLE_BOX),
        ("battle command menu (specs/07-battle-director.md line 47)", (0, BATTLE_MENU_TOP, 256, 240 - BATTLE_MENU_TOP)),
    ),
}

# Where a shot's plate hangs, and which rows of data/meta_bake.json each shot prints. The ids are the
# rows section 4 names: the `npc` chat row for Nye at her first turn, and the three `fight` rows for the
# deck watch at turns 1, 2 and 3. A list that names a row the bake does not hold is an OverlayError.
SHOT_ROWS = {
    "S5": ("npc/nye/turn_1",),
    "S6": ("fight/navy_sailor/1", "fight/navy_sailor/2", "fight/navy_sailor/3"),
}
SHOT_ANCHOR = {"S5": "top", "S6": "bottom"}

# The clocks section 4 and section 5 put each overlay at, in seconds, so a caller can ask whether a
# given frame falls inside a window instead of eyeballing the edit.
SHOT_WINDOWS = {
    "S5": {"bake": ((83.40, 87.40),)},                        # 1:23.4 to 1:27.4
    "S6": {"bake": ((135.03, 135.03), (138.53, 138.53), (143.53, 143.53)),   # 2:15.03, 2:18.53, 2:23.53
           "network": ((154.40, 158.40),)},                   # 2:34.40 to 2:38.40
}

# Text tiers. PressStart2P advances exactly one pixel per point, measured 2026-10-27 with
# font.getbbox() at 8, 10, 12, 16 and 24 points, so a line's width is len(text) * size and the fit of
# every drawn line is arithmetic rather than a hope.
CAPTION_SIZE = 16
DETAIL_SIZE = 12
HASH_SIZE = 10
LINE_GAP = 6
TIER_SIZE = {"caption": CAPTION_SIZE, "detail": DETAIL_SIZE, "hash": HASH_SIZE}
BADGE_H = 2 * DETAIL_SIZE + LINE_GAP

PLATE_X = 24
PLATE_W = FRAME_W - 2 * PLATE_X
PLATE_PAD = 12
PLATE_BORDER = 2 * SCALE   # the game's own 2 pixel window frame, at 3x
TOP_MARGIN = 12
BOTTOM_MARGIN = 12

# Colours, by palette role (data/palette.json "roles"). Nothing else is used.
ROLE_PLATE = "paper"
ROLE_BORDER = "ink"
ROLE_TEXT = "text"
ROLE_DEAD = "hazard"
ROLE_LIVE = "warn"

LONG_DASHES = ("\u2014", "\u2013", "\u2012", "\u2015")


class OverlayError(Exception):
    """The overlay cannot be drawn honestly. The message names what is missing or colliding."""


# ---------------------------------------------------------------------------------------------------------------------
# Reading the record


def read_json(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def load_palette(path=PALETTE_PATH):
    """The palette's colours by role name, as RGB tuples. A role the overlay needs and cannot find stops it."""
    data = read_json(path)
    colours = []
    for value in data["colours"]:
        value = value.lstrip("#")
        colours.append((int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)))
    roles = {}
    for role in (ROLE_PLATE, ROLE_BORDER, ROLE_TEXT, ROLE_DEAD, ROLE_LIVE):
        if role not in data.get("roles", {}):
            raise OverlayError("data/palette.json has no %r role, so the overlay has no colour for it" % role)
        roles[role] = colours[data["roles"][role]]
    return roles


def load_bake(path=BAKE_PATH):
    """data/meta_bake.json, validated enough that a row used on screen cannot be half a row.

    The file's own rule (its first field) says tools/bake_meta.py writes it and the game reads it and
    nothing else. This tool is a reader too, so it checks the shape it reads rather than trusting it.
    """
    bake = read_json(path)
    if bake.get("format") != 1:
        raise OverlayError("%s is not format 1, so this reader does not know its shape" % path)
    if bake.get("kind") != "meta_bake":
        raise OverlayError("%s is not a meta_bake file" % path)
    block = bake.get("bake")
    if not isinstance(block, dict):
        raise OverlayError("%s has no bake block, so there is no model, time or mode to print" % path)
    for field in ("model", "created_at", "mode", "backend", "network", "offline"):
        if field not in block:
            raise OverlayError("%s's bake block has no %r field, and the overlay will not invent one" % (path, field))
    rows = bake.get("rows")
    if not isinstance(rows, list) or not rows:
        raise OverlayError("%s holds no rows, so no bake row can be printed" % path)
    index = {}
    for row in rows:
        if not isinstance(row, dict) or not row.get("id"):
            raise OverlayError("%s holds a row with no id" % path)
        index[row["id"]] = row
    return bake, index


def bake_row(bake_index, row_id, allow_fallback=False):
    """One row, with the fields the overlay prints, or a refusal naming what is wrong with it.

    Two refusals, and both exist so the judged shot cannot carry a claim the file does not make:
    a missing field stops the shot (section 4 rule 1), and a row that is not a live Meta answer stops it
    too, because this overlay's whole job is to prove a model answered. A `fallback` row is the hand
    written line the bake used when the model's answer was refused; printing it as the receipt would be
    the receipt that lies. `allow_fallback` draws such a row with its own source word on the line
    instead, which is for a layout check and never for the judged shot.
    """
    if row_id not in bake_index:
        raise OverlayError(
            "data/meta_bake.json holds no row %r, so this shot is not recordable (section 4 rule 1)" % row_id
        )
    row = bake_index[row_id]
    for field in ("model", "created_at", "request_hash", "source"):
        if not row.get(field):
            raise OverlayError("row %r has no %r field, and the overlay prints it rather than a blank" % (row_id, field))
    if "network" not in row:
        raise OverlayError("row %r has no 'network' field, and the overlay prints it rather than a blank" % row_id)
    live = row["source"] == "live" and row["network"] is True
    if not live and not allow_fallback:
        raise OverlayError(
            "row %r is not a live Meta answer (source %r, network %r, reason %r), so this shot is not "
            "recordable until the bake holds a live answer for it (section 4 rule 1)"
            % (row_id, row["source"], row["network"], row.get("reason", ""))
        )
    return row


def receipt_for(row, directory=RECEIPT_DIR):
    """The bridge receipt that backs this row, or None.

    tools/ai_bridge.py writes one file per live answer to data/ai_cache/bridge/<sha256>.json holding
    `model`, `source`, `network`, `mode`, `created_at` and the request (npc or encounter). It is keyed on
    the bridge's own composition, not on the bake's `request_hash`, so the match here is the honest one
    that exists: same model, same character, newest first. A receipt is evidence, never the source of a
    printed value; the printed model and time are always the bake row's own.
    """
    if not os.path.isdir(directory):
        return None
    wanted_npc = str(row.get("npc") or row.get("enemy") or row.get("card") or "")
    best = None
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json"):
            continue
        try:
            receipt = read_json(os.path.join(directory, name))
        except (ValueError, OSError):
            continue
        if receipt.get("model") != row.get("model"):
            continue
        request = receipt.get("request") or {}
        if wanted_npc and str(request.get("npc") or "") != wanted_npc:
            continue
        stamp = str(receipt.get("created_at") or "")
        if best is None or stamp > str(best.get("created_at") or ""):
            best = dict(receipt, file=name)
    return best


def shot_caption(shot, path=SCRIPT_PATH):
    """The shot's caption, verbatim, out of knowledge/DEMO-SCRIPT.md.

    The words belong to whoever authors the script, so they are read there instead of being copied into
    this file. A section whose caption line is missing or carries a long dash stops the overlay.
    """
    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    heading = None
    for index, line in enumerate(lines):
        if line.startswith("### %s," % shot):
            heading = index
            break
    if heading is None:
        raise OverlayError("%s has no '### %s,' section, so this shot has no caption to draw" % (path, shot))
    for line in lines[heading + 1:]:
        if line.startswith("### ") or line.startswith("## "):
            break
        if line.startswith("Caption, verbatim:"):
            start = line.find("`")
            end = line.rfind("`")
            if start < 0 or end <= start:
                raise OverlayError("%s: the caption line for %s is not in backticks" % (path, shot))
            caption = line[start + 1:end]
            for dash in LONG_DASHES:
                if dash in caption:
                    raise OverlayError("%s: the caption for %s carries a long dash" % (path, shot))
            return caption
    raise OverlayError("%s: the %s section has no 'Caption, verbatim:' line" % (path, shot))


# ---------------------------------------------------------------------------------------------------------------------
# The lines the overlay draws


def wrap(text, size, width):
    """Greedy word wrap to a pixel width, for a font whose advance is one pixel per point."""
    limit = max(1, width // size)
    words = text.split()
    out, current = [], ""
    for word in words:
        candidate = word if not current else current + " " + word
        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                out.append(current)
            current = word
    if current:
        out.append(current)
    return out


def overlay_lines(shot, bake, index, receipt=None, caption=None, allow_fallback=False):
    """Every line the plate draws, as (tier, text) pairs, built only from the record.

    `tier` decides the font size and, in the frame test, which lines are bake pixels and which are the
    shot's caption. A value carrying a long dash is refused here rather than drawn.
    """
    if shot not in SHOT_ROWS:
        raise OverlayError("%r is not an overlay shot; the two are S5 and S6" % shot)
    block = bake["bake"]
    caption = caption if caption is not None else shot_caption(shot)
    usable = PLATE_W - 2 * PLATE_PAD

    rows = [bake_row(index, row_id, allow_fallback=allow_fallback) for row_id in SHOT_ROWS[shot]]

    lines = [("caption", piece) for piece in wrap(caption, CAPTION_SIZE, usable)]
    lines.append(("detail", "BAKE MODEL %s  MODE %s  BACKEND %s" % (block["model"], block["mode"], block["backend"])))
    lines.append(("detail", "BAKE TIME %s  ROWS %s live %s" % (block["created_at"], block.get("rows", 0), block.get("live", 0))))

    if shot == "S5":
        row = rows[0]
        lines.append(("detail", "ROW %s  SOURCE %s" % (row["id"], row["source"])))
        lines.append(("hash", "HASH %s" % row["request_hash"]))
    else:
        for turn, row in enumerate(rows, start=1):
            lines.append(("hash", "T%d %s" % (turn, row["request_hash"])))
        for turn, row in enumerate(rows, start=1):
            if row["source"] != "live" or row["network"] is not True:
                # Only reachable with allow_fallback: the line says a fallback was drawn, so the frame
                # never reads as a receipt for an answer the model refused.
                lines.append(("detail", "T%d SOURCE %s, NOT A LIVE ANSWER" % (turn, row["source"])))
        lines.append(("badge", network_badge_text(block)))
        for piece in network_lines(block):
            lines.append(("detail", piece))

    for tier, text in lines:
        for dash in LONG_DASHES:
            if dash in text:
                raise OverlayError("the overlay line %r carries a long dash" % text)
        if tier == "hash" and len(text) * HASH_SIZE > usable:
            raise OverlayError("the hash line %r is %d px wide and the plate holds %d" % (text, len(text) * HASH_SIZE, usable))
    return lines


def network_badge_text(block):
    """The badge's two words, from the bake's own network and offline flags."""
    dead = bool(block.get("offline")) or not bool(block.get("network"))
    return "NETWORK OFF" if dead else "NETWORK LIVE"


def network_lines(block):
    """The network line of section 5, for the state the bake actually recorded."""
    dead = bool(block.get("offline")) or not bool(block.get("network"))
    if dead:
        return (
            "NETWORK DEAD SINCE THE FIRST FRAME.",
            "THESE REPLIES CAME FROM data/meta_bake.json.",
        )
    return (
        "NETWORK UP AT BAKE TIME.",
        "THESE REPLIES CAME FROM %s OVER THE NETWORK." % block.get("backend"),
    )


# ---------------------------------------------------------------------------------------------------------------------
# Geometry


def scale_rect(rect):
    x, y, w, h = rect
    return (x * SCALE, y * SCALE, (x + w) * SCALE, (y + h) * SCALE)


def line_height(tier):
    if tier == "badge":
        return BADGE_H + LINE_GAP
    return TIER_SIZE[tier] + LINE_GAP


def plate_rect(shot, heights, below):
    """Where the plate goes, and a refusal if it would touch a text box or leave the frame."""
    total = 2 * PLATE_PAD + sum(heights)
    if below:
        top = FRAME_H + TOP_MARGIN
        return (PLATE_X, top, PLATE_X + PLATE_W, top + total)
    if SHOT_ANCHOR[shot] == "top":
        top = TOP_MARGIN
    else:
        bottom = BATTLE_MENU_TOP * SCALE - BOTTOM_MARGIN
        top = bottom - total
    plate = (PLATE_X, top, PLATE_X + PLATE_W, top + total)
    if plate[1] < 0 or plate[3] > FRAME_H:
        raise OverlayError(
            "%s needs %d px of plate and does not fit in the 768x720 frame with the text boxes untouched"
            % (shot, total)
        )
    for name, rect in FORBIDDEN[shot]:
        box = scale_rect(rect)
        if intersects(plate, box):
            raise OverlayError("%s's plate at %r would cover the %s at %r" % (shot, plate, name, box))
    return plate


def intersects(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def plan(shot, bake, index, receipt=None, below=False, caption=None, blank=False, allow_fallback=False):
    """The layout of one render: the plate, every line with its box, and the badge.

    Returned as a dict so the frame test measures the same geometry the drawing used instead of
    recomputing it and hoping the two agree.
    """
    lines = overlay_lines(shot, bake, index, receipt=receipt, caption=caption, allow_fallback=allow_fallback)
    heights = [line_height(tier) for tier, _ in lines]
    plate = plate_rect(shot, heights, below)
    y = plate[1] + PLATE_PAD
    placed = []
    badge = None
    usable = PLATE_W - 2 * PLATE_PAD
    for tier, text in lines:
        height = line_height(tier)
        box = (plate[0] + PLATE_PAD, y, plate[0] + PLATE_PAD + usable, y + height)
        if tier == "badge":
            dead = text == "NETWORK OFF"
            rect = (box[0], box[1], box[0] + len(text) * DETAIL_SIZE + 2 * PLATE_PAD, box[1] + BADGE_H)
            badge = dict(box=box, rect=rect, text=text, dead=dead)
            placed.append(dict(tier=tier, text=text, source_text=text, box=box, rect=rect, size=DETAIL_SIZE,
                               blank=blank, dead=dead))
        else:
            drawn = "" if (blank and tier in ("detail", "hash")) else text
            placed.append(dict(tier=tier, text=drawn, source_text=text, box=box, size=TIER_SIZE[tier], blank=blank))
        y += height
    return dict(shot=shot, plate=plate, lines=placed, badge=badge, below=below)


# ---------------------------------------------------------------------------------------------------------------------
# Drawing


def load_font(size):
    if not os.path.exists(FONT_PATH):
        raise OverlayError("%s is missing, so the overlay cannot use the video's caption font" % FONT_PATH)
    return ImageFont.truetype(FONT_PATH, size)


def render(source, shot, bake, index, receipt=None, below=False, caption=None, blank=False, allow_fallback=False):
    """Draw one shot's overlay onto one frame. Returns (image, plan).

    `source` is an absolute path or an opened PIL image in RGB. A frame that is not the 3x screen is
    refused: an overlay drawn for 768x720 on any other size would sit over the wrong pixels.
    """
    if isinstance(source, Image.Image):
        base = source.convert("RGB")
    else:
        base = Image.open(source).convert("RGB")
    if base.size != (FRAME_W, FRAME_H):
        raise OverlayError(
            "the frame is %dx%d and the overlay is laid out for %dx%d, which is 3x the 256x240 screen"
            % (base.size[0], base.size[1], FRAME_W, FRAME_H)
        )
    layout = plan(shot, bake, index, receipt=receipt, below=below, caption=caption, blank=blank,
                  allow_fallback=allow_fallback)
    canvas_h = layout["plate"][3] + BOTTOM_MARGIN if below else FRAME_H
    canvas = Image.new("RGB", (FRAME_W, canvas_h), (0, 0, 0))
    canvas.paste(base, (0, 0))
    colours = load_palette()
    draw = ImageDraw.Draw(canvas)
    draw.rectangle(layout["plate"], fill=colours[ROLE_PLATE], outline=colours[ROLE_BORDER], width=PLATE_BORDER)
    for line in layout["lines"]:
        if line["tier"] == "badge":
            draw_badge(draw, line, colours)
            continue
        if not line["text"]:
            continue
        draw.text((line["box"][0], line["box"][1]), line["text"], font=load_font(line["size"]), fill=colours[ROLE_TEXT])
    return canvas, layout


def draw_badge(draw, line, colours):
    """The network badge: the dead state in the hazard role with a slash, the live state in the warn role."""
    rect = line["rect"]
    fill = colours[ROLE_DEAD] if line["dead"] else colours[ROLE_LIVE]
    draw.rectangle(rect, fill=fill, outline=colours[ROLE_BORDER], width=PLATE_BORDER)
    draw.text((rect[0] + PLATE_PAD, rect[1] + (BADGE_H - DETAIL_SIZE) // 2), line["text"],
              font=load_font(DETAIL_SIZE), fill=colours[ROLE_BORDER] if line["dead"] is False else colours[ROLE_PLATE])
    if line["dead"]:
        draw.line((rect[0] + PLATE_BORDER, rect[1] + PLATE_BORDER, rect[2] - PLATE_BORDER, rect[3] - PLATE_BORDER),
                  fill=colours[ROLE_BORDER], width=PLATE_BORDER)


# ---------------------------------------------------------------------------------------------------------------------
# The frame test


def count_colour(image, rect, colour):
    """How many pixels of the exact colour sit inside the rectangle (PIL returns (count, colour) pairs)."""
    region = image.crop(rect)
    found_colours = region.getcolors(maxcolors=1 << 22) or []
    for count, value in found_colours:
        if tuple(value) == tuple(colour):
            return count
    return 0


def changed_outside(source, rendered, plate):
    """True when any pixel outside the plate's own rectangle differs between the two frames."""
    diff = ImageChops.difference(source, rendered)
    box = (max(0, plate[0] - 1), max(0, plate[1] - 1), min(source.size[0], plate[2] + 1), min(source.size[1], plate[3] + 1))
    draw = ImageDraw.Draw(diff)
    draw.rectangle(box, fill=(0, 0, 0))
    return diff.getbbox() is not None


def check_frame(source_path, rendered_path, shot, bake, index, receipt=None, below=False, caption=None,
                allow_fallback=False):
    """Measure a rendered frame, and return a report a reader can act on. `ok` is the verdict."""
    source = Image.open(source_path).convert("RGB")
    rendered = Image.open(rendered_path).convert("RGB")
    colours = load_palette()
    _, layout = render(source, shot, bake, index, receipt=receipt, below=below, caption=caption,
                       allow_fallback=allow_fallback)
    control, _ = render(source, shot, bake, index, receipt=receipt, below=below, caption=caption, blank=True,
                        allow_fallback=allow_fallback)
    plate = layout["plate"]
    checks = []

    def add(name, ok, detail):
        checks.append(dict(name=name, ok=bool(ok), detail=detail))

    add("frame size", rendered.size == (FRAME_W, FRAME_H if not below else rendered.size[1]),
        "%dx%d" % rendered.size)
    add("plate drawn", count_colour(rendered, plate, colours[ROLE_PLATE]) > 0.5 * (plate[2] - plate[0]) * (plate[3] - plate[1]),
        "%d plate pixels" % count_colour(rendered, plate, colours[ROLE_PLATE]))
    add("nothing outside the plate changed", not changed_outside(source, rendered, plate),
        "diff outside %r" % (plate,))

    for name, rect in FORBIDDEN[shot]:
        box = scale_rect(rect)
        identical = ImageChops.difference(source.crop(box), rendered.crop(box)).getbbox() is None
        add("text box untouched: %s" % name, identical, "rect %r" % (box,))

    bake_ink = 0
    control_ink = 0
    for line in layout["lines"]:
        if line["tier"] not in ("detail", "hash"):
            continue
        ink = count_colour(rendered, line["box"], colours[ROLE_TEXT])
        blank_ink = count_colour(control, line["box"], colours[ROLE_TEXT])
        bake_ink += ink
        control_ink += blank_ink
        add("ink on the bake line %r" % line["source_text"][:28], ink >= 20 * max(1, len(line["source_text"]) // 20),
            "%d ink pixels, %d when the line is blanked" % (ink, blank_ink))
    add("the bake lines are what put ink there", bake_ink > 3 * max(1, control_ink),
        "%d ink pixels against %d blanked" % (bake_ink, control_ink))

    # A line that overflowed its own box would leave ink on the plate with no line to own it, which is
    # exactly what a clipped caption looks like in a still frame.
    interior = (plate[0] + PLATE_BORDER, plate[1] + PLATE_BORDER, plate[2] - PLATE_BORDER, plate[3] - PLATE_BORDER)
    total_ink = count_colour(rendered, interior, colours[ROLE_TEXT])
    boxed_ink = 0
    for line in layout["lines"]:
        if line["tier"] == "badge":
            continue
        boxed_ink += count_colour(rendered, line["box"], colours[ROLE_TEXT])
    add("no text outside its own line box", total_ink == boxed_ink,
        "%d ink pixels on the plate, %d inside a line box" % (total_ink, boxed_ink))

    badge = layout["badge"]
    if badge:
        role = ROLE_DEAD if badge["dead"] else ROLE_LIVE
        found = count_colour(rendered, badge["rect"], colours[role])
        add("network badge", found >= 100, "%s in the %s role: %d pixels" % (badge["text"], role, found))

    return dict(ok=all(item["ok"] for item in checks), checks=checks, plate=plate, shot=shot)


# ---------------------------------------------------------------------------------------------------------------------
# CLI


def main(argv=None):
    parser = argparse.ArgumentParser(description="the S5 and S6 caption overlay with the Meta bake row")
    parser.add_argument("--shot", choices=sorted(SHOT_ROWS), help="S5 (dock office) or S6 (TALK fight and offline shot)")
    parser.add_argument("--frame", help="the frame to draw on, or the rendered frame to check")
    parser.add_argument("--source", help="--check: the clean frame the render started from")
    parser.add_argument("--out", help="where the rendered frame is written")
    parser.add_argument("--below", action="store_true", help="draw the plate under the frame instead of inside it")
    parser.add_argument("--rows", action="store_true", help="print the lines this shot draws, as JSON, and draw nothing")
    parser.add_argument("--layout", action="store_true",
                        help="print the plate and line boxes as JSON, so another tool can look for the row")
    parser.add_argument("--check", action="store_true", help="measure a rendered frame against its source")
    parser.add_argument("--times", action="store_true", help="print the clocks this shot's overlays run at")
    parser.add_argument("--at", type=float, help="--times: report whether this second falls inside a window")
    parser.add_argument("--allow-fallback", action="store_true",
                        help="draw a row the bake recorded as a fallback, labelled as one; a layout check only")
    parser.add_argument("--bake", default=BAKE_PATH, help="the bake file to read (never edited by this tool)")
    args = parser.parse_args(argv)

    if not args.shot:
        print(__doc__)
        return 1
    try:
        bake, index = load_bake(args.bake)
        if args.rows:
            lines = overlay_lines(args.shot, bake, index, allow_fallback=args.allow_fallback)
            print(json.dumps(
                {
                    "shot": args.shot,
                    "bake_file": args.bake,
                    "plate_anchor": SHOT_ANCHOR[args.shot],
                    "rows": list(SHOT_ROWS[args.shot]),
                    "lines": [{"tier": tier, "text": text} for tier, text in lines],
                },
                indent=1,
            ))
            return 0
        if args.layout:
            layout = plan(args.shot, bake, index, below=args.below, allow_fallback=args.allow_fallback)
            print(json.dumps(
                {
                    "shot": args.shot,
                    "frame": [FRAME_W, FRAME_H],
                    "font": FONT_PATH,
                    "colours": {role: list(rgb) for role, rgb in load_palette().items()},
                    "plate": layout["plate"],
                    "lines": [{"tier": line["tier"], "text": line["source_text"], "box": line["box"],
                               "size": line["size"]} for line in layout["lines"]],
                    "badge": layout["badge"],
                    "forbidden": [{"what": name, "rect": scale_rect(rect)} for name, rect in FORBIDDEN[args.shot]],
                },
                indent=1,
                default=list,
            ))
            return 0
        if args.times:
            windows = SHOT_WINDOWS[args.shot]
            print(json.dumps({"shot": args.shot, "windows": windows}, indent=1))
            if args.at is not None:
                inside = [name for name, spans in windows.items() if any(lo <= args.at <= hi for lo, hi in spans)]
                print("%.2f s is inside: %s" % (args.at, ", ".join(inside) if inside else "no overlay window"))
            return 0
        if args.check:
            if not (args.source and args.frame):
                raise OverlayError("--check needs --source and --frame")
            report = check_frame(args.source, args.frame, args.shot, bake, index,
                                 allow_fallback=args.allow_fallback)
            for item in report["checks"]:
                print("%s  %s  %s" % ("PASS" if item["ok"] else "FAIL", item["name"], item["detail"]))
            print("%s  %s frame at %s" % ("PASS" if report["ok"] else "FAIL", args.shot, args.frame))
            return 0 if report["ok"] else 1
        if not (args.frame and args.out):
            raise OverlayError("a render needs --frame and --out")
        image, layout = render(args.frame, args.shot, bake, index, below=args.below,
                               allow_fallback=args.allow_fallback)
        out_dir = os.path.dirname(os.path.abspath(args.out))
        if out_dir and not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        image.save(args.out)
        print("%s  %s overlay written to %s, plate %r, %d lines"
              % ("PASS", args.shot, args.out, layout["plate"], len(layout["lines"])))
        return 0
    except OverlayError as error:
        print("REFUSED  %s" % error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
