#!/usr/bin/env python3
"""demo_overlay.py: the S5 caption overlay, with the Meta bake row and the network line.

Why this file exists
    The submission's strongest claim is that a Meta model answers the player inside a NES text box
    (knowledge/DEMO-SCRIPT.md section 4). A picture of a text box does not carry that claim on its own:
    what carries it is the bake row printed beside the shot, read out of `data/meta_bake.json`, which is
    the only record the game itself trusts (spec 19 section 2 and decision D5). This tool is that row,
    drawn in the same font as the rest of the video, for the one shot that proves it: S5, the three TALK
    replies to Captain Morgan on the quay (the card t_892cc851 rewrite, knowledge/DEMO-SCRIPT.md section
    4, after the ruling in knowledge/DEMO-AUTHORITY-RULING-2026-11-12.md retired the dock office and the
    deck watch that the two older shots were drawn from).

What it draws, and where the words come from
    S5, 1:23.4, 1:31.0 and 1:38.0 (sections 4 and 5): the shot's caption, then one bake header, then the
    row that answers at that clock. Reply 1's window prints `model` on the header and the row's own
    `request_hash`; replies 2 and 3 print their own, different hashes, which is what proves three calls
    at three scene states and not one line reused. A window that draws one row takes `rows=` with that
    one row id, so each of the three clocks carries its own receipt and no window prints the other two.
    S5, 1:41.00 to 1:44.00 (section 5): the network line says the adapter has been dead since the first
    frame and that the replies shown came from `data/meta_bake.json`. When the bake in the file records a
    live network the same drawing has a live network line instead, because a line that always says
    "dead" would be a claim the file does not make. The network window is drawn with `rows=()`, because
    the line is chosen from the file's own flags and needs no bake row under it.
    S5, with `--talk-box` (card t_2ef3aa6f): the NES window itself, 240x48 in game space, holding the row's
    own reply lines, the verdict its effect earns and the WILL that moved, and the id of the ledger receipt
    for that verdict printed small at the bottom. The box hangs in the band between the caption plate and
    the dialogue box, so the game's own window stays the game's pixels and the frame test proves it.
    S5, with `--receipt-plates` (card t_29a8e5e1, the judge panel's fix 4): three small plates hang above
    the dialogue box, one per Meta number the panel asked to see on screen, meta.model_calls (21),
    meta.live_rows (11) and meta.live_share_pct (52.4), each carrying the id of the receipt in
    data/receipts/meta_receipts.jsonl that backs it. The numbers are read out of the bake header and the
    ids out of the ledger, and the two are checked against each other at draw time, so a plate prints the
    number the record holds and the receipt for that number, never a number and a receipt that disagree.
    The network line is not new: every S5 drawing already carries the badge and the two lines chosen from
    the bake's own `offline` and `network` flags, so the strip is what fix 4 adds to that picture.
    S6 draws nothing here, and that is a decision the script made: Percy's encounter carries no `talk`
    block, so no bake row answers in his fight, the six `fight/percy` rows are `fallback` and are never
    read, and a receipt plate over his shot would be a claim about a call the game does not make
    (knowledge/DEMO-SCRIPT.md section 4, last paragraph).

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
    python tools\\demo_overlay.py --shot S5 --rows --talk-box
    python tools\\demo_overlay.py --shot S5 --rows --receipt-plates
    python tools\\demo_overlay.py --shot S5 --frame output\\judge_frames\\x_f05.png --out output\\demo\\overlay\\S5.png --talk-box
    python tools\\demo_overlay.py --shot S5 --frame IN.png --out OUT.png --receipt-plates
    python tools\\demo_overlay.py --check --shot S5 --source IN.png --frame OUT.png --receipt-plates
    python tools\\demo_overlay.py --check --shot S5 --source IN.png --frame OUT.png --talk-box
    python tools\\demo_overlay.py --shot S5 --frame IN.png --out OUT.png --below
    python tools\\demo_overlay.py --check --shot S5 --source IN.png --frame OUT.png --below
    python tools\\demo_overlay.py --times --shot S5 --at 84.0

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
# rows section 4 names: the three `fight` rows for Captain Morgan's TALK turns on the quay, which is the
# fight that is on the route. Card t_892cc851 moved them here: the old ids were `npc/nye/turn_1` for S5
# and the three `fight/navy_sailor` rows for S6, and both of those scenes (the dock office, the deck
# watch) are off the route the build walks, so a plate drawn from them would be a receipt for a scene
# the demo does not show. S6 is gone entirely: `percy` carries no `talk` block, so no bake row answers
# in his fight (knowledge/DEMO-SCRIPT.md section 4). A list that names a row the bake does not hold is
# an OverlayError.
SHOT_ROWS = {
    "S5": ("fight/morgan/1", "fight/morgan/2", "fight/morgan/3"),
}
SHOT_ANCHOR = {"S5": "top"}

# The clocks section 4 and section 5 put each overlay at, in seconds, so a caller can ask whether a
# given frame falls inside a window instead of eyeballing the edit, and so a plate can be drawn with
# `rows=` holding the one row that answers at that clock.
SHOT_WINDOWS = {
    "S5": {"bake": ((83.40, 87.40), (91.00, 95.00), (98.00, 101.00)),   # 1:23.4, 1:31.0, 1:38.0
           "network": ((101.00, 104.00),),                             # 1:41.00 to 1:44.00
           # Card t_746512f4: the verdict window, which is on for the whole shot. This is the clock
           # tools/demo_cut_180.py composites at, and tools/judge_frames_check.py samples inside, so the
           # two tools read one number instead of two that agree by hand.
           "verdict": ((78.00, 110.00),)},                             # 1:18.00 to 1:50.00
}

# The NES TALK box (card t_2ef3aa6f). S5's own claim in knowledge/DEMO-SCRIPT.md section 4 is "the person
# judging your line is a Meta model answering inside a NES text box", proved "by Nye's page and its
# data/meta_bake.json row on screen, in a box whose four lines are 28 columns". So this is a second drawing
# on that one shot: a NES window that holds the row's own reply lines, the verdict the effect map puts on
# them, and the receipt id of the number that verdict moved, printed small.
#
# Three rules hold it honest, and they are the same three the plate keeps:
#   1. every word in the box is read out of the record at draw time: the reply lines out of the bake row's
#      `text`, the verdict word out of data/talk/sailor_judge.json "verdicts", the receipt id out of
#      data/receipts/meta_receipts.jsonl, where tools/receipts.py --row wrote it. Nothing here types one.
#   2. the id printed is never computed on the fly and hoped to exist: the box refuses to draw until that
#      exact receipt is in the ledger, because an id that is not a logged receipt is a claim, not a receipt.
#   3. the box never covers the game's own window: it is placed in the band between S5's caption plate and
#      the dialogue box at (8, 168), and a frame test compares that dialogue box byte for byte with the
#      source, so the game's own pixels stay the game's.
JUDGE_PATH = os.path.join(ROOT, "data", "talk", "sailor_judge.json")
LEDGER_PATH = os.path.join(ROOT, "data", "receipts", "meta_receipts.jsonl")
# Card t_b9173f05 drew the box on S6 as well, because the panel's fix 2 was that a player's line is
# judged on the fight shot. Card t_892cc851 retires that: the fight shot is Percy's now, his encounter
# carries no `talk` block, and the six `fight/percy` rows are `fallback`, so there is no row a box could
# honestly print. The box stays on S5, where the three Morgan rows answer.
TALK_BOX_SHOTS = ("S5",)
# Where the box hangs from. S5 hangs it under its caption plate, in the band above the dialogue box.
TALK_BOX_ANCHOR = {"S5": "plate"}

# The two build numbers the panel asked to keep on screen beside the verdict, by the name each one carries
# in data/receipts/meta_receipts.jsonl. The ids are never typed here: they are looked up in the ledger.
BAKE_RECEIPT_NAMES = ("meta.model_calls", "meta.system_chars")

# The three receipt plates of card t_29a8e5e1 (judge panel 2026-11-13, fix 4). The script's S5 row says the
# shot draws "one caption, three bake receipts, the network line", and the panel's measured facts name two
# of the three numbers by hand: model_calls 21 and live_share_pct 52.4. The third is the numerator those two
# are made of, live_rows, so the three read as one arithmetic claim rather than three unrelated figures.
# Each name is the ledger's own `name` field, each value is read from the bake header at draw time, and each
# id is looked up in data/receipts/meta_receipts.jsonl, so a plate cannot print a number the file does not
# hold or a receipt that backs a different number.
RECEIPT_PLATE_NAMES = ("meta.model_calls", "meta.live_rows", "meta.live_share_pct")
RECEIPT_PLATE_SHOTS = ("S5",)   # the one shot whose claim is a Meta model in a NES box, so the one strip
RECEIPT_PLATE_X = 24      # the caption plate's own left edge, so the three small plates line up with it
RECEIPT_PLATE_PAD = 8     # inside each small plate
RECEIPT_PLATE_GAP = 6     # between the stacked plates
RECEIPT_GAP = 8           # between the lowest plate and the top of the dialogue box
TALK_BOX_X, TALK_BOX_W = 8, 240     # 256x240 game space, the same 240 wide window spec 05 draws
TALK_BOX_GAP = 8                    # frame pixels between the caption plate and the box
TALK_COLS = 28                      # spec 19 section 5: the box holds 28 columns per line
TALK_LINES_MAX = 3                  # the reply is 1 to 3 lines, so a row with more is not drawn
TALK_PAD_TOP = 4                    # measured 2026-11-01: a 10 pt glyph's top pixel sits 1 px above the
                                    # y it is drawn at, so the box keeps this much headroom and no ink is
                                    # ever drawn outside the line box it belongs to

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

# Which palette role the verdict word is drawn in: the map's three words are persuaded, unmoved and
# angered (data/talk/sailor_judge.json "verdicts"), so the box reads at a glance and says what the bar did.
ROLE_OF_VERDICT = {"persuaded": ROLE_LIVE, "unmoved": ROLE_TEXT, "angered": ROLE_DEAD}

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


def overlay_lines(shot, bake, index, receipt=None, caption=None, allow_fallback=False, rows=None):
    """Every line the plate draws, as (tier, text) pairs, built only from the record.

    `tier` decides the font size and, in the frame test, which lines are bake pixels and which are the
    shot's caption. A value carrying a long dash is refused here rather than drawn. `rows` names the bake
    rows this drawing carries: None means every row the shot declares, an empty tuple draws none (which is
    what the network window needs), and a one element tuple gives the window that one reply's receipt.
    """
    if shot not in SHOT_ROWS:
        raise OverlayError("%r is not an overlay shot; the one is %s" % (shot, " and ".join(sorted(SHOT_ROWS))))
    block = bake["bake"]
    caption = caption if caption is not None else shot_caption(shot)
    usable = PLATE_W - 2 * PLATE_PAD

    wanted = SHOT_ROWS[shot] if rows is None else tuple(rows)
    chosen = [bake_row(index, row_id, allow_fallback=allow_fallback) for row_id in wanted]

    lines = [("caption", piece) for piece in wrap(caption, CAPTION_SIZE, usable)]
    lines.append(("detail", "BAKE MODEL %s  MODE %s  BACKEND %s" % (block["model"], block["mode"], block["backend"])))
    lines.append(("detail", "BAKE TIME %s  ROWS %s live %s" % (block["created_at"], block.get("rows", 0), block.get("live", 0))))

    for row in chosen:
        lines.append(("detail", "ROW %s  SOURCE %s" % (row["id"], row["source"])))
        lines.append(("hash", "HASH %s" % row["request_hash"]))
        if row["source"] != "live" or row["network"] is not True:
            # Only reachable with allow_fallback: the line says a fallback was drawn, so the frame never
            # reads as a receipt for an answer the model refused.
            lines.append(("detail", "ROW %s IS SOURCE %s, NOT A LIVE ANSWER" % (row["id"], row["source"])))

    if (SHOT_WINDOWS.get(shot) or {}).get("network"):
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
    """The network line of section 5, for the state the bake actually recorded.

    Card t_9b689430 (judge panel 2026-11-15, fix 2): the network line names the model and, when a run
    measured one, the wire time, so the one shot whose whole claim is a Meta answer carries the two
    facts a judge asks for at the point the claim is made. The time is the same `latency_ms` the
    receipt plates print, read from the same header, so the two drawings cannot disagree, and a replay
    bake prints LATENCY NOT MEASURED rather than a number it did not spend.
    """
    dead = bool(block.get("offline")) or not bool(block.get("network"))
    measured = block.get("latency_ms")
    time_text = "LATENCY NOT MEASURED" if measured is None else "LATENCY %d MS" % int(measured)
    model_text = "MODEL %s %s" % (str(block.get("model") or "").upper(), time_text)
    if dead:
        return (
            "NETWORK DEAD SINCE THE FIRST FRAME.",
            "THESE REPLIES CAME FROM data/meta_bake.json.",
            model_text,
        )
    return (
        "NETWORK UP AT BAKE TIME.",
        "THESE REPLIES CAME FROM %s OVER THE NETWORK." % block.get("backend"),
        model_text,
    )


# ---------------------------------------------------------------------------------------------------------------------
# The NES TALK box: the row's words, its verdict, and the receipt that backs it


def load_verdicts(path=JUDGE_PATH):
    """data/talk/sailor_judge.json's effect map: effect name to (verdict word, WILL delta).

    The map is the director's, not this tool's: spec 19 section 6 and the file's own `verdict_source` say
    the model picks an effect and this map, never the model, decides what the bar moves by. A map that is
    missing an entry the drawn row needs stops the box, because a verdict this tool invented is not one.
    """
    data = read_json(path)
    verdicts = data.get("verdicts")
    if not isinstance(verdicts, dict) or not verdicts:
        raise OverlayError("%s has no verdicts block, so the box has no verdict to print" % path)
    for effect, entry in verdicts.items():
        if not isinstance(entry, dict) or "verdict" not in entry or "will_delta" not in entry:
            raise OverlayError("%s: the verdict for effect %r has no 'verdict' and 'will_delta'" % (path, effect))
        if not isinstance(entry["verdict"], str) or not entry["verdict"]:
            raise OverlayError("%s: the verdict for effect %r is not a word" % (path, effect))
    return verdicts


def load_ledger(path=LEDGER_PATH):
    """Every receipt already logged, keyed by id. An empty ledger is an empty dict, not an error."""
    rows = {}
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise OverlayError("%s line %d is not JSON: %s" % (path, number, exc))
            if isinstance(row, dict) and row.get("id"):
                rows[row["id"]] = row
    return rows


def row_receipt_id(row, ledger=None):
    """The logged receipt for this row's verdict, or a refusal naming the command that writes one.

    The id is built by tools/receipts.py's own function and then looked up in the ledger, in that order:
    the box prints an id only if the ledger really holds it (rule 2 at the top of this file). A row whose
    receipt has not been logged yet refuses, and the message says exactly what to run.
    """
    tools_dir = os.path.join(ROOT, "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    import receipts  # the ledger's own vocabulary; imported here so this tool never re-derives an id

    try:
        numbers = receipts.row_numbers([row["id"]])
    except receipts.ReceiptError as error:
        raise OverlayError("no verdict receipt can be written for row %r: %s" % (row["id"], error))
    receipt = numbers[0]["receipt"]
    ledger = load_ledger() if ledger is None else ledger
    if receipt not in ledger:
        raise OverlayError(
            "row %r's verdict receipt %s is not in data/receipts/meta_receipts.jsonl and the box prints no "
            "other id: run `python tools\\receipts.py --row %s` first" % (row["id"], receipt, row["id"])
        )
    return receipt


def ledger_number(name, value, ledger=None):
    """The logged receipt for a named Meta number, read out of the ledger and checked against the file.

    Card t_b9173f05. The panel asked for the bake row and its receipt (rcpt-a505930564032c7c, the call
    count) to stay on screen beside the 2408 char system prompt summary, so the box has to print both
    numbers *and* the ids that back them. Two refusals keep that honest and neither of them types an id:
    a name with no line in the ledger stops the box, and a ledger line whose own `value` is not the number
    the bake now holds stops it too, because a receipt for 21 calls is not a receipt for 22.
    """
    ledger = load_ledger() if ledger is None else ledger
    matches = [row for row in ledger.values() if row.get("name") == name]
    if not matches:
        raise OverlayError(
            "data/receipts/meta_receipts.jsonl holds no %s receipt, so the box prints none: run "
            "`python tools\\receipts.py` first" % name
        )
    row = max(matches, key=lambda item: str(item.get("logged_at") or ""))
    if row.get("value") != value:
        raise OverlayError(
            "the ledger's newest %s receipt %s is for %r and the bake now says %r, so the two do not back "
            "the same number: run `python tools\\receipts.py` to log the current one"
            % (name, row.get("id"), row.get("value"), value)
        )
    return row["id"]


def bake_receipt_numbers(block):
    """The three Meta numbers the receipt plates print, read out of the bake header.

    Card t_29a8e5e1. Each one is a number tools/receipts.py writes a receipt for, so the plate prints a
    number that already has a receipt to point at: the calls the bake attempted, the rows that came back
    from the recorded cache, and the share of the calls that did. The share is rounded to one decimal the
    same way receipts.py rounds it (round(100.0 * live / calls, 1)), because two roundings of one quotient
    would be two numbers, and the ledger receipts only one of them.
    """
    for field in ("calls_attempted", "live"):
        if field not in block:
            raise OverlayError(
                "the bake block has no %r, and the receipt plates print it rather than a blank" % field
            )
    calls, live = int(block["calls_attempted"]), int(block["live"])
    if calls <= 0:
        raise OverlayError(
            "the bake block says %d calls attempted, and a live share of no calls is not a number" % calls
        )
    return {
        "meta.model_calls": calls,
        "meta.live_rows": live,
        "meta.live_share_pct": round(100.0 * float(live) / float(calls), 1),
    }


def receipt_number_text(name, value):
    """The number as a plate prints it: the ledger's own value, with a percent sign on the share.

    No thousands separator, no rounding of its own and no unit the ledger does not carry, so the words on
    the plate and the `value` of the receipt that backs them are the same number written twice.
    """
    piece = ("%g" % value) if isinstance(value, float) else str(int(value))
    return piece + "%" if name.endswith("_pct") else piece


def meta_receipt_plates(block, ledger=None):
    """The three small plates' words and ids, or a refusal naming the number that does not add up.

    Two refusals, and both keep the strip a receipt rather than a caption: a name the ledger holds no line
    for stops the drawing (nothing can be printed without an id to point at), and a ledger line whose own
    `value` is not the number the bake header now holds stops it too, because a receipt for 21 calls is not
    a receipt for 22. Both come out of ledger_number(), which is the one place that reads the ledger for a
    named number, so this strip and the NES box cannot disagree about what a receipt says.
    """
    ledger = load_ledger() if ledger is None else ledger
    numbers = bake_receipt_numbers(block)
    plates = []
    for index, name in enumerate(RECEIPT_PLATE_NAMES):
        value = numbers[name]
        receipt = ledger_number(name, value, ledger=ledger)
        text = "%s %s" % (name.upper(), receipt_number_text(name, value))
        # Card t_9b689430 (judge panel 2026-11-15, fix 2): the panel read the three receipts and found
        # no model named on any of them. The strip has 22 px of band above it before it meets the caption
        # plate, measured by the frame test, and a third line is 16 px plus padding, so a new line under
        # the number is refused by receipt_strip. The model therefore rides on the first plate's own line,
        # where it costs no height, and the wire time rides on the network line, which has room. There is
        # no measured time in the shipped bake to print here: see receipt_model_line.
        model = str(block.get("model") or "").upper()
        if not model:
            raise OverlayError("the bake block names no model, and the receipt plate prints the model name")
        if index == 0:
            text = "%s %s" % (text, model)
        plates.append(dict(
            name=name,
            value=value,
            text=text,
            receipt=receipt,
            model_line="",
        ))
    return plates


def receipt_model_line(block):
    """The model name on every receipt plate, and the wire time when the bake measured one.

    The panel's fix 2 asks for the model name and the latency on the three bake receipts. The model is
    in the bake header, so it is printed always. The latency is not: `tools/bake_meta.py` records a
    `latency_ms` on a row only when that row's answer crossed the wire, and a median in the header only
    when at least one did, so a replay bake (the shipped one) has no time to print and says so in words
    rather than printing a number no file holds. That is this project's standing rule: a number that is
    not measured, computed or inferred from a named file is not a number it may print.
    """
    model = str(block.get("model") or "")
    if not model:
        raise OverlayError("the bake block names no model, and the receipt plates print the model name")
    measured = block.get("latency_ms")
    if measured is None:
        tail = "LATENCY NOT MEASURED"
    else:
        tail = "LATENCY %d MS" % int(measured)
        if int(measured) <= 0:
            raise OverlayError("the bake block says %r ms, and a wire time of no milliseconds is not a "
                               "time" % measured)
    return "MODEL %s %s" % (model.upper(), tail)


def wrap_columns(text, cols):
    """Greedy word wrap to a column count, because the NES box counts glyphs and not pixels.

    The talk box checks every line against TALK_COLS, so a line the player typed (up to 120 characters)
    has to be broken before it reaches the box rather than drawn over the window edge. A single word
    longer than the window is hard split, which is what a typewriter does and what the box can draw.
    """
    words = str(text).split()
    lines, current = [], ""
    for word in words:
        while len(word) > cols:
            if current:
                lines.append(current)
                current = ""
            lines.append(word[:cols])
            word = word[cols:]
        candidate = word if not current else current + " " + word
        if len(candidate) <= cols:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    if not lines:
        lines = [""]
    return lines


def talk_box_lines(shot, row, verdicts, receipt, allow_fallback=False, block=None):
    """The box's lines, as (tier, text, palette role) triples, every one read out of the record.

    The reply lines are the row's own `text` array, drawn exactly as it is held and refused if any line is
    over the box's 28 columns or the row carries more lines than the box draws. The verdict line is the
    map's word for the row's own effect plus the WILL it moved. A row that is not a live answer owns up to
    it on its own line, so the box can be drawn for a layout check without ever reading as a receipt.
    """
    if shot not in TALK_BOX_SHOTS:
        raise OverlayError(
            "the NES talk box is drawn on %s, the shot whose script claim is the box; %r is not one of them"
            % (" and ".join(TALK_BOX_SHOTS), shot)
        )
    text = row.get("text")
    if not isinstance(text, list) or not text:
        raise OverlayError("row %r has no 'text' array, and the box draws the row's own words" % row["id"])
    if len(text) > TALK_LINES_MAX:
        raise OverlayError("row %r holds %d reply lines and the box draws %d" % (row["id"], len(text), TALK_LINES_MAX))
    effect = row.get("effect")
    entry = verdicts.get(effect) if isinstance(effect, str) else None
    if entry is None:
        raise OverlayError("row %r carries effect %r and the verdict map has no entry for it" % (row["id"], effect))
    if entry["verdict"] not in ROLE_OF_VERDICT:
        raise OverlayError("the verdict word %r has no palette role, so the box cannot colour it" % entry["verdict"])

    lines = [("hash", "RECEIPT DRAWN FROM data/meta_bake.json", ROLE_TEXT)]
    # The line the player typed is the thing being judged, so on a fight row it is the first thing the box
    # says. It is drawn exactly as the row records it, wrapped to the window's own 28 columns, and never
    # re-cased: the NES font is the game's business, the record's wording is the row's.
    player = row.get("player_line")
    if isinstance(player, str) and player.strip():
        for piece in wrap_columns(player.strip(), TALK_COLS):
            lines.append(("detail", piece, ROLE_TEXT))
    for piece in text:
        if not isinstance(piece, str) or not piece:
            raise OverlayError("row %r holds a reply line that is not a word: %r" % (row["id"], piece))
        if len(piece) > TALK_COLS:
            raise OverlayError("row %r's line %r is %d columns and the box holds %d"
                               % (row["id"], piece, len(piece), TALK_COLS))
        lines.append(("caption", piece, ROLE_TEXT))

    delta = entry["will_delta"]
    sign = "+" if isinstance(delta, (int, float)) and delta > 0 else ""
    lines.append(("caption", "VERDICT %s, WILL %s%s" % (entry["verdict"].upper(), sign, delta),
                  ROLE_OF_VERDICT[entry["verdict"]]))

    live = row.get("source") == "live" and row.get("network") is True
    if not live and not allow_fallback:
        raise OverlayError(
            "row %r is not a live answer (source %r, network %r), so its verdict is not a receipt; "
            "--allow-fallback draws it labelled as a fallback for a layout check only"
            % (row["id"], row.get("source"), row.get("network"))
        )
    if not live:
        lines.append(("detail", "FALLBACK, NOT A LIVE ANSWER", ROLE_DEAD))
    lines.append(("hash", "%s ROW %s %s" % (receipt, row["id"], "LIVE" if live else "FALLBACK"), ROLE_TEXT))

    # Card t_b9173f05: on a fight row the box also carries the two build numbers the panel asked to keep
    # visible, each with the ledger receipt that backs it. Both values are the bake header's own, the
    # system prompt length is cross-checked against the row's own request (a box that printed one length
    # for the header and another for the row would be two claims), and the ids come out of the ledger.
    if row.get("scene") == "fight":
        if not isinstance(block, dict) or "calls_attempted" not in block or "system_chars" not in block:
            raise OverlayError(
                "row %r is a fight row and the box prints its build receipts, but no bake header with "
                "calls_attempted and system_chars was handed to it" % row["id"]
            )
        request = row.get("request") if isinstance(row.get("request"), dict) else {}
        if request.get("system_chars") != block["system_chars"]:
            raise OverlayError(
                "the bake header says the system prompt is %r chars and row %r's own request says %r, so "
                "the two do not describe one prompt"
                % (block["system_chars"], row["id"], request.get("system_chars"))
            )
        calls_name, chars_name = BAKE_RECEIPT_NAMES
        calls_receipt = ledger_number(calls_name, block["calls_attempted"])
        chars_receipt = ledger_number(chars_name, block["system_chars"])
        lines.append(("hash", "BAKE CALLS %s RECEIPT %s" % (block["calls_attempted"], calls_receipt), ROLE_TEXT))
        lines.append(("hash", "SYSTEM PROMPT %s CHARS RECEIPT %s" % (block["system_chars"], chars_receipt),
                      ROLE_TEXT))

    usable = TALK_BOX_W * SCALE - 2 * PLATE_PAD
    for tier, piece, _role in lines:
        for dash in LONG_DASHES:
            if dash in piece:
                raise OverlayError("the talk box line %r carries a long dash" % piece)
        size = TIER_SIZE[tier]
        if len(piece) * size > usable:
            raise OverlayError("the talk box line %r is %d px wide and the box holds %d"
                               % (piece, len(piece) * size, usable))
    return lines


def talk_box_rect(shot, plate, heights):
    """Where the box hangs: in the band between the caption plate and the game's own window, or a refusal."""
    total = 2 * PLATE_PAD + TALK_PAD_TOP + sum(heights)
    anchor = TALK_BOX_ANCHOR.get(shot, "plate")
    if anchor == "below":
        # S6 (card t_b9173f05): the box is stacked under the frame, below the plate, so neither the
        # battle stage nor either of the game's text boxes is covered. It is refused unless the plate is
        # itself below the frame, because stacking the box on the plate inside the frame would put it
        # back over the game's pixels.
        if plate[1] <= FRAME_H:
            raise OverlayError(
                "%s's talk box is drawn under the frame, so the shot has to be drawn with --below as well"
                % shot
            )
        x = PLATE_X
        top = plate[3] + TALK_BOX_GAP
        return (x, top, PLATE_X + PLATE_W, top + total)
    x = TALK_BOX_X * SCALE
    right = x + TALK_BOX_W * SCALE
    if SHOT_ANCHOR[shot] == "top":
        top = plate[3] + TALK_BOX_GAP
        rect = (x, top, right, top + total)
    else:
        top = plate[1] - TALK_BOX_GAP - total
        rect = (x, top, right, top + total)
    if intersects(rect, plate):
        raise OverlayError("%s's talk box at %r would cover the caption plate at %r" % (shot, rect, plate))
    if rect[1] < 0 or rect[3] > FRAME_H:
        raise OverlayError("%s's talk box needs %d px and does not fit in the %dx%d frame"
                           % (shot, total, FRAME_W, FRAME_H))
    for name, forbidden in FORBIDDEN[shot]:
        box = scale_rect(forbidden)
        if intersects(rect, box):
            raise OverlayError("%s's talk box at %r would cover the %s at %r" % (shot, rect, name, box))
    return rect


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


def sub_rects(rect, hole):
    """The rectangles of `rect` that lie outside `hole`, at most four.

    Used where one region has to be measured and another drawing already sits over part of it: the battle HUD
    bands are compared with the source frame in exactly the pieces the caption plate does not cover, so the
    measurement is about the verdict window and not about a plate that was there before it.
    """
    x0, y0, x1, y1 = rect
    hx0, hy0, hx1, hy1 = hole
    pieces = []
    if hy0 > y0:
        pieces.append((x0, y0, x1, min(hy0, y1)))
    if hy1 < y1:
        pieces.append((x0, max(hy1, y0), x1, y1))
    top, bottom = max(y0, hy0), min(y1, hy1)
    if bottom > top:
        if hx0 > x0:
            pieces.append((x0, top, min(hx0, x1), bottom))
        if hx1 < x1:
            pieces.append((max(hx1, x0), top, x1, bottom))
    return [piece for piece in pieces if piece[2] > piece[0] and piece[3] > piece[1]]


def receipt_strip(shot, plates, caption_plate, talk=None, blank=False):
    """The three small plates, stacked and bottom aligned above the dialogue box, or a refusal.

    Card t_29a8e5e1. Each plate is two lines: the ledger's own name for the number with the number on it,
    then the id of the receipt that backs it, both at the hash tier and both inside the plate's own
    padding. The stack is measured from the dialogue box upwards, so "above the dialogue box" is arithmetic
    rather than a hope, and it is refused when it would touch the dialogue box, the caption plate, the NES
    talk box, or the edge of the frame. Refusing is the right answer for the talk box collision: S5's band
    between the plate and the dialogue box holds one of the two drawings, not both, and this tool will not
    put a receipt over the record it is receipting.
    """
    if shot not in RECEIPT_PLATE_SHOTS:
        raise OverlayError(
            "the Meta receipt plates are drawn on %s, the shot whose claim they receipt; %r is not one of them"
            % (" and ".join(RECEIPT_PLATE_SHOTS), shot)
        )
    built = []
    for item in plates:
        words = (("detail", item["text"]),
                 ("hash", item.get("model_line") or ""),
                 ("hash", "RECEIPT %s" % item["receipt"]))
        words = tuple(pair for pair in words if pair[1])
        for _tier, text in words:
            for dash in LONG_DASHES:
                if dash in text:
                    raise OverlayError("the receipt plate line %r carries a long dash" % text)
            if len(text) * TIER_SIZE[_tier] > FRAME_W - 2 * RECEIPT_PLATE_X - 2 * RECEIPT_PLATE_PAD:
                raise OverlayError(
                    "the receipt plate line %r is %d px wide and the frame holds %d"
                    % (text, len(text) * TIER_SIZE[_tier], FRAME_W - 2 * RECEIPT_PLATE_X - 2 * RECEIPT_PLATE_PAD)
                )
        width = max(len(text) * TIER_SIZE[tier] for tier, text in words) + 2 * RECEIPT_PLATE_PAD
        height = sum(line_height(tier) for tier, _ in words) + 2 * RECEIPT_PLATE_PAD
        built.append(dict(item=item, words=words, width=width, height=height))

    total = sum(part["height"] for part in built) + RECEIPT_PLATE_GAP * (len(built) - 1)
    bottom = DIALOGUE_BOX[1] * SCALE - RECEIPT_GAP
    top = bottom - total
    if top < 0:
        raise OverlayError(
            "the %d receipt plates need %d px above the dialogue box, and only %d are between the top of the "
            "frame and it" % (len(built), total, bottom)
        )

    drawn = []
    y = top
    for part in built:
        rect = (RECEIPT_PLATE_X, y, RECEIPT_PLATE_X + part["width"], y + part["height"])
        name = part["item"]["name"]
        if intersects(rect, scale_rect(DIALOGUE_BOX)):
            raise OverlayError("the receipt plate %s at %r would cover the dialogue box at %r"
                               % (name, rect, scale_rect(DIALOGUE_BOX)))
        if intersects(rect, caption_plate):
            raise OverlayError("the receipt plate %s at %r would cover the caption plate at %r"
                               % (name, rect, caption_plate))
        if talk is not None and intersects(rect, talk):
            raise OverlayError(
                "the receipt plate %s at %r would cover the NES talk box at %r; S5's band holds one of the "
                "two, so draw the box or the receipt strip and not both" % (name, rect, talk)
            )
        for _other_name, forbidden in FORBIDDEN[shot]:
            if intersects(rect, scale_rect(forbidden)):
                raise OverlayError("the receipt plate %s at %r would cover the %s" % (name, rect, _other_name))
        lines = []
        line_y = y + RECEIPT_PLATE_PAD
        for tier, text in part["words"]:
            height = line_height(tier)
            lines.append(dict(tier=tier, text=("" if blank else text), source_text=text,
                              box=(rect[0] + RECEIPT_PLATE_PAD, line_y, rect[2] - RECEIPT_PLATE_PAD,
                                   line_y + height),
                              size=TIER_SIZE[tier], blank=blank))
            line_y += height
        drawn.append(dict(name=name, value=part["item"]["value"], receipt=part["item"]["receipt"],
                          text=part["item"]["text"], rect=rect, lines=lines))
        y += part["height"] + RECEIPT_PLATE_GAP
    return drawn


# ---------------------------------------------------------------------------------------------------------------------
# The S5 verdict window (card t_746512f4, the judge panel's fix 2 of 2026-11-16)
#
# The panel's sentence was exact: "no S5 bake receipts or network line is visible". Nothing was missing from the
# drawing: the receipts strip ran 1:23.4 to 1:44.0 and the network badge 1:41.0 to 1:44.0, and a sampler that takes
# one frame every thirty seconds lands outside every one of those windows, which is why six stills showed none of
# it. This window is the same facts in one NES box that is on the screen for the whole shot, 1:18.00 to 1:50.00.
#
# What it holds, and where every word comes from:
#   1. the model, by the display name data/credits.json already prints to a player, joined on the bake header's own
#      model id. Nothing here types a model name, which is the same join pp_talk_judge_label makes in GML;
#   2. the decision, as the three S5 bake rows record it (their `effect` fields, checked against data/talk/
#      sailor_judge.json's verdict map). The sentence is chosen from the rows' own `source` and `network` fields, so
#      a rebake that makes those rows live answers changes the sentence instead of leaving a fallback label over a
#      live answer, and a row that is not a live answer is called what it is;
#   3. the three bake receipts of card t_29a8e5e1, each the ledger's own name, the header's own value and the id of
#      the receipt in data/receipts/meta_receipts.jsonl that backs that value;
#   4. the network line, from the bake's own `offline` and `network` flags.
#
# Where it sits. S5 is Captain Morgan's fight, and the battle screen's own HUD owns three bands (read out of
# data/ui_layouts.json's battle_b row, the same row pp_battle_director draws and tools/render_battle_visuals.py
# renders): the enemy plate with the HP and MERCY bars from y 56 to 88, the party panel with the party line from
# y 116 to 164, and the command band from y 168. The free strip between the plate and the panel is 28 rows, and the
# window takes it plus the plate's own bottom 4 rows of border, where no number is drawn: the HP bar and the MERCY
# bar both end at y 83. The frame test compares the plate's stat rows and the whole party panel byte for byte with
# the source frame, so the window cannot creep over a number the card says has to stay visible behind it.
CREDITS_PATH = os.path.join(ROOT, "data", "credits.json")
UI_LAYOUTS_PATH = os.path.join(ROOT, "data", "ui_layouts.json")
VERDICT_BOX_SHOTS = ("S5",)
VERDICT_BOX_X, VERDICT_BOX_W = 8, 240    # game space: the same 240 wide window spec 05 draws
VERDICT_BOX_PAD = 3                      # frame pixels inside the border, so no glyph touches it
VERDICT_PLATE_KEEP = 4                   # game rows of the enemy window's bottom border the box may sit over
# The pitch of each line in frame pixels: one caption sized line for the model, then hash sized lines. A 10 pt glyph
# puts its top pixel one row above the y it is drawn at (measured 2026-11-01), so the box keeps that row for every
# line it draws and the last line still stops inside the border.
VERDICT_PITCH = {"caption": 18, "hash": 13}


def battle_hud_rects(path=UI_LAYOUTS_PATH):
    """The two battle HUD areas the verdict window must leave alone, in 256x240 game space.

    Both come out of data/ui_layouts.json's battle_b row rather than being typed here, because that row is the one
    geometry the director draws and the offline battle renderer draws, so a layout that moves the plate or the panel
    moves this window with it instead of leaving it over the party line.
    """
    data = read_json(path)
    row = data.get("battle_b") if isinstance(data, dict) else None
    if not isinstance(row, dict):
        raise OverlayError("%s has no battle_b row, so the verdict window has no HUD to keep clear of" % path)
    for key in ("plate", "panel"):
        part = row.get(key)
        if not isinstance(part, dict):
            raise OverlayError("%s's battle_b row has no %r window, and the verdict window is placed against it"
                               % (path, key))
        for field in ("x", "y", "w", "h"):
            if field not in part:
                raise OverlayError("%s's battle_b %s needs an x, y, w and h in 8 pixel tiles" % (path, key))
    plate, panel = row["plate"], row["panel"]
    plate_stats = (plate["x"], plate["y"], plate["w"] * 8, plate["h"] * 8 - VERDICT_PLATE_KEEP)
    panel_rect = (panel["x"], panel["y"], panel["w"] * 8, panel["h"] * 8)
    return (("the enemy plate's HP and MERCY bars", plate_stats),
            ("the party panel and its party line", panel_rect))


def verdict_box_band():
    """The game space strip the verdict window occupies: from the plate's last stat row to the party panel's top."""
    keep = battle_hud_rects()
    _plate_name, plate = keep[0]
    _panel_name, panel = keep[1]
    top = plate[1] + plate[3]
    bottom = panel[1]
    if bottom - top < 8:
        raise OverlayError(
            "the battle HUD leaves %d rows between the enemy plate and the party panel, and the verdict window "
            "cannot be drawn there" % (bottom - top))
    return (VERDICT_BOX_X, top, VERDICT_BOX_W, bottom - top)


def verdict_model_name(block, path=CREDITS_PATH):
    """The display name data/credits.json prints to a player for the bake's own model id, or a refusal."""
    model = block.get("model") if isinstance(block, dict) else None
    if not isinstance(model, str) or not model:
        raise OverlayError("the bake header names no model, so the verdict window has no name to print")
    data = read_json(path)
    roll = data.get("roll") if isinstance(data, dict) else None
    models = roll.get("models") if isinstance(roll, dict) else None
    if not isinstance(models, list) or not models:
        raise OverlayError("%s has no roll.models table, and the window takes the model name from there" % path)
    for row in models:
        if isinstance(row, dict) and row.get("model_id") == model:
            display = row.get("display")
            if not isinstance(display, str) or not display:
                raise OverlayError("%s's roll.models row for %r carries no display name" % (path, model))
            return display
    raise OverlayError("%s prints no display name for the bake's model %r, so the window cannot name it"
                       % (path, model))


def verdict_decision_line(rows, verdicts):
    """The decision the record holds for S5's turns, worded for how those turns were actually answered.

    Every effect is looked up in the judge map, so a row carrying an effect the map does not hold stops the window:
    an effect the director would refuse is not a decision that can be printed. When every row is a live answer the
    sentence says the model decided it; when any row is not, the sentence says what the file holds instead, because
    the model did not answer that turn and a label that said it had would be a claim about a call never made.
    """
    effects = []
    for row in rows:
        effect = row.get("effect")
        entry = verdicts.get(effect) if isinstance(effect, str) else None
        if entry is None:
            raise OverlayError("row %r carries effect %r and the verdict map has no entry for it"
                               % (row.get("id"), effect))
        effects.append(str(effect).upper())
    decided = ", ".join(effects)
    live = all(row.get("source") == "live" and row.get("network") is True for row in rows)
    if live:
        return "MODEL DECIDED " + decided
    return "RECORDED EFFECTS " + decided + ". FALLBACK, NOT LIVE."


def verdict_receipt_lines(block, ledger=None):
    """The three bake receipts as one line each: the ledger's name, the header's value, the receipt's own id."""
    ledger = load_ledger() if ledger is None else ledger
    numbers = bake_receipt_numbers(block)
    lines = []
    for name in RECEIPT_PLATE_NAMES:
        value = numbers[name]
        receipt = ledger_number(name, value, ledger=ledger)
        lines.append("%s %s RECEIPT %s" % (name.upper(), receipt_number_text(name, value), receipt))
    return lines


def verdict_network_line(block):
    """The network line of section 5 in one row, for the state the bake actually recorded."""
    dead = bool(block.get("offline")) or not bool(block.get("network"))
    if dead:
        return "NETWORK DEAD SINCE THE FIRST FRAME. REPLIES FROM data/meta_bake.json."
    backend = block.get("backend")
    if not isinstance(backend, str) or not backend:
        raise OverlayError("the bake says its network was up and names no backend, so the line cannot say where "
                           "the replies came from")
    return "NETWORK UP AT BAKE TIME. REPLIES CAME FROM %s." % backend


def verdict_window(bake, index, blank=False):
    """The window's rect and its lines, or a refusal naming what does not fit or does not come out of the record."""
    if not isinstance(bake, dict) or not isinstance(bake.get("bake"), dict):
        raise OverlayError("the bake file has no bake header, so the verdict window has nothing to print")
    block = bake["bake"]
    # allow_fallback is read as the row's own `source` word, not as a licence to draw a receipt for a call the
    # model never made: verdict_decision_line prints "MODEL DECIDED" only when every row is a live answer and
    # says what the file holds otherwise. The plate above the window keeps the strict reading.
    rows = [bake_row(index, row_id, allow_fallback=True) for row_id in SHOT_ROWS["S5"]]
    verdicts = load_verdicts()
    words = [(CAPTION_SIZE, verdict_model_name(block), ROLE_LIVE),
             (HASH_SIZE, verdict_decision_line(rows, verdicts), ROLE_TEXT)]
    for piece in verdict_receipt_lines(block):
        words.append((HASH_SIZE, piece, ROLE_TEXT))
    words.append((HASH_SIZE, verdict_network_line(block), ROLE_DEAD))

    rect = scale_rect(verdict_box_band())
    usable = (rect[2] - rect[0]) - 2 * PLATE_BORDER - 2 * VERDICT_BOX_PAD
    content_top = rect[1] + PLATE_BORDER
    content_bottom = rect[3] - PLATE_BORDER
    placed = []
    y = content_top
    for size, text, role in words:
        for dash in LONG_DASHES:
            if dash in text:
                raise OverlayError("the verdict window line %r carries a long dash" % text)
        if len(text) * size > usable:
            raise OverlayError("the verdict window line %r is %d px wide and the window holds %d"
                               % (text, len(text) * size, usable))
        # A 10 pt glyph's top pixel sits one row above the y it is drawn at; a caption sized glyph sits on it.
        ink_top = y - (1 if size <= DETAIL_SIZE else 0)
        ink_bottom = y + size
        placed.append(dict(size=size, text=("" if blank else text), source_text=text, role=role,
                           box=(rect[0] + PLATE_BORDER + VERDICT_BOX_PAD, ink_top,
                                rect[2] - PLATE_BORDER - VERDICT_BOX_PAD, ink_bottom)))
        y += VERDICT_PITCH["caption" if size >= CAPTION_SIZE else "hash"]
    if placed[0]["box"][1] < content_top or placed[-1]["box"][3] > content_bottom:
        raise OverlayError(
            "the verdict window's %d lines end at y %d and the window's own border starts at y %d, so they do not "
            "fit between the battle HUD's two bands" % (len(placed), placed[-1]["box"][3], content_bottom))
    for name, forbidden in FORBIDDEN["S5"]:
        if intersects(rect, scale_rect(forbidden)):
            raise OverlayError("the verdict window at %r would cover the %s at %r"
                               % (rect, name, scale_rect(forbidden)))
    for name, game_rect in battle_hud_rects():
        if intersects(rect, scale_rect(game_rect)):
            raise OverlayError("the verdict window at %r would cover %s at %r"
                               % (rect, name, scale_rect(game_rect)))
    return dict(rect=rect, lines=placed)


def plan(shot, bake, index, receipt=None, below=False, caption=None, blank=False, allow_fallback=False,
         talk_box=False, rows=None, receipt_plates=False, verdict_box=False) -> dict:
    """The layout of one render: the plate, every line with its box, the badge, and the NES talk box.

    Returned as a dict so the frame test measures the same geometry the drawing used instead of
    recomputing it and hoping the two agree.
    """
    lines = overlay_lines(shot, bake, index, receipt=receipt, caption=caption, allow_fallback=allow_fallback,
                          rows=rows)

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

    box = None
    if talk_box:
        rows = [bake_row(index, row_id, allow_fallback=allow_fallback) for row_id in SHOT_ROWS[shot]]
        verdicts = load_verdicts()
        boxed_row = rows[0]
        receipt_id = row_receipt_id(boxed_row)
        box_lines = talk_box_lines(shot, boxed_row, verdicts, receipt_id, allow_fallback=allow_fallback,
                                   block=bake.get("bake"))
        box_rect = talk_box_rect(shot, plate, [line_height(tier) for tier, _, _ in box_lines])
        box_y = box_rect[1] + PLATE_PAD + TALK_PAD_TOP
        boxed = []
        for index, (tier, text, role) in enumerate(box_lines):
            height = line_height(tier)
            # The first line's box reaches up into the reserved headroom, because a 10 pt glyph's top
            # pixel sits above the y it is drawn at. The box is the measured area; text_xy is where the
            # glyph is drawn, so the frame test can insist every pixel is inside a box it owns.
            top = box_y - (TALK_PAD_TOP if index == 0 else 0)
            line_box = (box_rect[0] + PLATE_PAD, top, box_rect[2] - PLATE_PAD, box_y + height)
            boxed.append(dict(tier=tier, text=("" if blank else text), source_text=text, box=line_box,
                              text_xy=(line_box[0], box_y), size=TIER_SIZE[tier], role=role, blank=blank))
            box_y += height
        box = dict(rect=box_rect, lines=boxed, receipt=receipt_id, row=boxed_row["id"],
                   verdict=verdicts[boxed_row["effect"]]["verdict"])
    strip = None
    if receipt_plates:
        strip = receipt_strip(shot, meta_receipt_plates(bake.get("bake") or {}), plate,
                              talk=(box["rect"] if box else None), blank=blank)
    verdict = None
    if verdict_box:
        if shot not in VERDICT_BOX_SHOTS:
            raise OverlayError(
                "the verdict window is drawn on %s, the shot whose claim it receipts; %r is not one of them"
                % (" and ".join(VERDICT_BOX_SHOTS), shot))
        verdict = verdict_window(bake, index, blank=blank)
    return dict(shot=shot, plate=plate, lines=placed, badge=badge, below=below, talk_box=box,
                receipt_plates=strip, verdict_box=verdict)


# ---------------------------------------------------------------------------------------------------------------------
# Drawing


def load_font(size):
    if not os.path.exists(FONT_PATH):
        raise OverlayError("%s is missing, so the overlay cannot use the video's caption font" % FONT_PATH)
    return ImageFont.truetype(FONT_PATH, size)


def render(source, shot, bake, index, receipt=None, below=False, caption=None, blank=False, allow_fallback=False,
           talk_box=False, rows=None, receipt_plates=False, verdict_box=False):
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
                  allow_fallback=allow_fallback, talk_box=talk_box, rows=rows,
                  receipt_plates=receipt_plates, verdict_box=verdict_box)
    bottom = layout["plate"][3]
    if layout.get("talk_box"):
        # S6's box is stacked under the plate, so the canvas has to reach past both of them.
        bottom = max(bottom, layout["talk_box"]["rect"][3])
    strip = layout.get("receipt_plates")
    if isinstance(strip, list) and strip:
        # The strip is bottom aligned above the dialogue box, so its last plate is the lowest one drawn.
        bottom = max(bottom, strip[-1]["rect"][3])
    canvas_h = bottom + BOTTOM_MARGIN if below else FRAME_H
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
    box = layout.get("talk_box")
    if box:
        draw.rectangle(box["rect"], fill=colours[ROLE_PLATE], outline=colours[ROLE_BORDER], width=PLATE_BORDER)
        for line in box["lines"]:
            if not line["text"]:
                continue
            at = line.get("text_xy") or (line["box"][0], line["box"][1])
            draw.text((at[0], at[1]), line["text"], font=load_font(line["size"]),
                      fill=colours[line["role"]])
    # The three Meta receipt plates, drawn last so they are the last thing on the frame: each is its own
    # small window in the same paper and ink roles, holding the number and the id of the receipt behind it.
    for part in layout.get("receipt_plates") or []:
        draw.rectangle(part["rect"], fill=colours[ROLE_PLATE], outline=colours[ROLE_BORDER], width=PLATE_BORDER)
        for line in part["lines"]:
            if not line["text"]:
                continue
            draw.text((line["box"][0], line["box"][1]), line["text"], font=load_font(line["size"]),
                      fill=colours[ROLE_TEXT])
    # The S5 verdict window (card t_746512f4): one NES window in the strip of battle frame the HUD leaves free,
    # holding the model, the decision and the three receipts that back it, and the network line.
    verdict = layout.get("verdict_box")
    if verdict:
        # PIL draws an inclusive rectangle, and every rectangle this tool plans is exclusive of its far edge, so
        # the far corner is pulled in by one: without it the window's last row lands on the party panel's first
        # row and the frame test reads the party line as covered.
        vrect = verdict["rect"]
        draw.rectangle((vrect[0], vrect[1], vrect[2] - 1, vrect[3] - 1), fill=colours[ROLE_PLATE],
                       outline=colours[ROLE_BORDER], width=PLATE_BORDER)
        for line in verdict["lines"]:
            if not line["text"]:
                continue
            draw.text((line["box"][0], line["box"][1]), line["text"], font=load_font(line["size"]),
                      fill=colours[line["role"]])
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


def changed_outside(source, rendered, plates):
    """True when any pixel outside the drawn rectangles differs between the two frames.

    `plates` is one rectangle or a list of them: the plate and, on S5, the NES talk box are both drawn by
    this tool, so both are blanked before the difference is read. Everything else is the game's.
    """
    rects = [plates] if isinstance(plates[0], int) else list(plates)
    diff = ImageChops.difference(source, rendered)
    draw = ImageDraw.Draw(diff)
    for plate in rects:
        # A rectangle is clamped to the image, and one that falls outside it entirely (S6's plate and its
        # talk box are drawn below the frame) is skipped: it cannot have changed a pixel of this image.
        x0 = max(0, min(source.size[0], plate[0] - 1))
        y0 = max(0, min(source.size[1], plate[1] - 1))
        x1 = max(0, min(source.size[0], plate[2] + 1))
        y1 = max(0, min(source.size[1], plate[3] + 1))
        if x1 > x0 and y1 > y0:
            draw.rectangle((x0, y0, x1, y1), fill=(0, 0, 0))
    return diff.getbbox() is not None


def check_frame(source_path, rendered_path, shot, bake, index, receipt=None, below=False, caption=None,
                allow_fallback=False, talk_box=False, rows=None, receipt_plates=False, verdict_box=False):

    """Measure a rendered frame, and return a report a reader can act on. `ok` is the verdict."""
    source = Image.open(source_path).convert("RGB")
    rendered = Image.open(rendered_path).convert("RGB")
    colours = load_palette()
    # Card t_b9173f05: S6 draws its plate under the frame (--below), so the rendered file is taller than
    # the game's own screen. Everything that is compared with the source, or has to stay the game's
    # pixels, is read from this crop; only the plate, which lives below the frame, is measured on the full
    # canvas. Before this the difference against a taller render raised instead of measuring.
    frame_view = rendered.crop((0, 0, source.size[0], source.size[1]))
    _, layout = render(source, shot, bake, index, receipt=receipt, below=below, caption=caption,
                       allow_fallback=allow_fallback, talk_box=talk_box, rows=rows,
                       receipt_plates=receipt_plates, verdict_box=verdict_box)
    control, _ = render(source, shot, bake, index, receipt=receipt, below=below, caption=caption, blank=True,
                        allow_fallback=allow_fallback, talk_box=talk_box, rows=rows,
                        receipt_plates=receipt_plates, verdict_box=verdict_box)

    plate = layout["plate"]
    box = layout.get("talk_box")
    checks = []

    def add(name, ok, detail):
        checks.append(dict(name=name, ok=bool(ok), detail=detail))

    size_ok = rendered.size[0] == FRAME_W and (rendered.size[1] >= FRAME_H if below else rendered.size[1] == FRAME_H)
    add("frame size", size_ok, "%dx%d%s" % (rendered.size[0], rendered.size[1], ", plate below the frame" if below else ""))
    add("plate drawn", count_colour(rendered, plate, colours[ROLE_PLATE]) > 0.5 * (plate[2] - plate[0]) * (plate[3] - plate[1]),
        "%d plate pixels" % count_colour(rendered, plate, colours[ROLE_PLATE]))
    verdict = layout.get("verdict_box")
    drawn = [plate, box["rect"]] if box else [plate]
    if verdict:
        drawn = drawn + [verdict["rect"]]
    strip = layout.get("receipt_plates") or []
    drawn = drawn + [part["rect"] for part in strip]
    add("nothing outside the drawn rectangles changed", not changed_outside(source, frame_view, drawn),
        "diff outside %r" % (drawn,))

    for name, rect in FORBIDDEN[shot]:
        box = scale_rect(rect)
        identical = ImageChops.difference(source.crop(box), frame_view.crop(box)).getbbox() is None
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

    # Card t_29a8e5e1: the three small plates, measured one at a time. Each has to be a real window (its own
    # paper over half its area), carry ink on both of its lines that the blanked control does not have, print
    # an id the ledger holds, and sit clear of the dialogue box and the caption plate. The dialogue box is
    # also compared byte for byte above, so a plate that reached into the game's window fails that check
    # rather than passing quietly here.
    ledger = load_ledger()
    for part in strip:
        arect = part["rect"]
        add("receipt plate %s drawn" % part["name"],
            count_colour(rendered, arect, colours[ROLE_PLATE]) > 0.5 * (arect[2] - arect[0]) * (arect[3] - arect[1]),
            "%d plate pixels at %r" % (count_colour(rendered, arect, colours[ROLE_PLATE]), arect))
        part_ink = 0
        part_blank = 0
        for line in part["lines"]:
            ink = count_colour(rendered, line["box"], colours[ROLE_TEXT])
            blank_ink = count_colour(control, line["box"], colours[ROLE_TEXT])
            part_ink += ink
            part_blank += blank_ink
            add("ink on the receipt line %r" % line["source_text"][:28],
                ink >= 20 * max(1, len(line["source_text"]) // 20),
                "%d ink pixels, %d when the line is blanked" % (ink, blank_ink))
        add("the receipt plate %s is what put ink there" % part["name"], part_ink > 3 * max(1, part_blank),
            "%d ink pixels against %d blanked" % (part_ink, part_blank))
        naming = [line for line in part["lines"] if part["receipt"] in line["source_text"]]
        add("the receipt id %s is printed on its own plate" % part["receipt"],
            bool(naming) and count_colour(rendered, naming[0]["box"], colours[ROLE_TEXT]) > 0
            and part["receipt"] in ledger,
            "%s on the %s plate, %s in data/receipts/meta_receipts.jsonl"
            % (part["receipt"], part["name"], "logged" if part["receipt"] in ledger else "NOT logged"))
        add("the receipt plate %s clears the dialogue box and the caption plate" % part["name"],
            not intersects(arect, scale_rect(DIALOGUE_BOX)) and not intersects(arect, plate),
            "plate %r, dialogue box %r" % (arect, scale_rect(DIALOGUE_BOX)))

    # Card t_746512f4: the S5 verdict window, measured. It has to be a real window, carry ink on every line it
    # claims, name the model the credits print, print the three ledger ids and the number each one backs, and
    # leave the battle HUD's two bands byte for byte as the source frame drew them, which is the card's own
    # "keep the HP and MERCY bars and party line visible" written as a measurement rather than a promise.
    if verdict:
        vrect = verdict["rect"]
        add("verdict window drawn",
            count_colour(rendered, vrect, colours[ROLE_PLATE]) > 0.5 * (vrect[2] - vrect[0]) * (vrect[3] - vrect[1]),
            "%d window pixels at %r" % (count_colour(rendered, vrect, colours[ROLE_PLATE]), vrect))
        naming = [line for line in verdict["lines"] if line["role"] == ROLE_LIVE]
        model_text = naming[0]["source_text"] if naming else ""
        add("the window names the bake's model as the credits print it",
            bool(model_text) and model_text == verdict_model_name(bake["bake"])
            and count_colour(rendered, naming[0]["box"], colours[ROLE_LIVE]) > 0,
            "%r on the caption line, %d ink pixels"
            % (model_text, count_colour(rendered, naming[0]["box"], colours[ROLE_LIVE])))
        line_ink = 0
        line_blank = 0
        for line in verdict["lines"]:
            ink = count_colour(rendered, line["box"], colours[line["role"]])
            blank_ink = count_colour(control, line["box"], colours[line["role"]])
            line_ink += ink
            line_blank += blank_ink
            add("ink on the verdict line %r" % line["source_text"][:28],
                ink >= 20 * max(1, len(line["source_text"]) // 20),
                "%d %s pixels, %d when the line is blanked" % (ink, line["role"], blank_ink))
        add("the verdict lines are what put ink there", line_ink > 3 * max(1, line_blank),
            "%d ink pixels against %d blanked" % (line_ink, line_blank))
        ledger = load_ledger()
        numbers = bake_receipt_numbers(bake["bake"])
        for name in RECEIPT_PLATE_NAMES:
            receipt = ledger_number(name, numbers[name], ledger=ledger)
            carrying = [line for line in verdict["lines"] if receipt in line["source_text"]]
            add("the receipt %s is printed with its number" % receipt,
                bool(carrying) and count_colour(rendered, carrying[0]["box"], colours[ROLE_TEXT]) > 0
                and receipt in ledger,
                "%s on the line %r, %s in the ledger"
                % (receipt, carrying[0]["source_text"] if carrying else "",
                   "logged" if receipt in ledger else "NOT logged"))
        add("the network line says what the bake's own flags say",
            any(line["source_text"] == verdict_network_line(bake["bake"]) for line in verdict["lines"]),
            verdict_network_line(bake["bake"]))
        for hud_name, game_rect in battle_hud_rects():
            hud = scale_rect(game_rect)
            add("the verdict window clears %s" % hud_name, not intersects(verdict["rect"], hud),
                "window %r, HUD %r" % (verdict["rect"], hud))
            # The same frame without the window: any pixel of the HUD band that differs between the two is a
            # pixel this window changed, which is the one thing the card says must not happen.
            plain, _ = render(source, shot, bake, index, receipt=receipt, below=below, caption=caption,
                              allow_fallback=allow_fallback, talk_box=talk_box, rows=rows,
                              receipt_plates=receipt_plates, verdict_box=False)
            same = ImageChops.difference(plain.crop(hud), frame_view.crop(hud)).getbbox() is None
            add("battle HUD untouched: %s" % hud_name, same,
                "%r, compared with the same frame drawn without the window" % (hud,))

    talk = layout.get("talk_box")
    receipt_ink = 0
    if talk:
        rect = talk["rect"]
        add("talk box drawn", count_colour(rendered, rect, colours[ROLE_PLATE]) > 0.5 * (rect[2] - rect[0]) * (rect[3] - rect[1]),
            "%d box pixels at %r" % (count_colour(rendered, rect, colours[ROLE_PLATE]), rect))
        for line in talk["lines"]:
            ink = count_colour(rendered, line["box"], colours[line["role"]])
            blank_ink = count_colour(control, line["box"], colours[line["role"]])
            add("ink on the box line %r" % line["source_text"][:28],
                ink >= 20 * max(1, len(line["source_text"]) // 20),
                "%d %s pixels, %d when the line is blanked" % (ink, line["role"], blank_ink))
            if talk["receipt"] in line["source_text"]:
                receipt_ink = ink
        add("the receipt id is printed on a line of its own", receipt_ink > 0,
            "%s: %d ink pixels" % (talk["receipt"], receipt_ink))
        # The reserved band is the union of the line boxes, and the first one already reaches up into the
        # headroom a 10 pt glyph's top pixel needs. Ink anywhere else in the window means a line overflowed
        # its allocation, which is what a clipped or spilling caption looks like in a still frame.
        span = (talk["lines"][0]["box"][0], talk["lines"][0]["box"][1],
                talk["lines"][-1]["box"][2], talk["lines"][-1]["box"][3])
        # Every role the box draws, counted in the band and again inside the line boxes. The boxes are
        # counted for all the roles and not just their own, because a 10 pt glyph's top pixel sits one row
        # above the line it belongs to (TALK_PAD_TOP) and that row can land inside the box above it, whose
        # own role is a different colour. Counting only each box's own role read those rows as ink outside
        # every box on the S6 box, where a verdict line sits above three receipt lines.
        role_colours = [colours[role] for role in set(line["role"] for line in talk["lines"])]
        band_ink = 0
        for colour in role_colours:
            band_ink += count_colour(rendered, span, colour)
        inside = 0
        for line in talk["lines"]:
            for colour in role_colours:
                inside += count_colour(rendered, line["box"], colour)
        add("no box text outside the lines' reserved band", band_ink == inside,
            "%d ink pixels in the band %r, %d inside a line box" % (band_ink, span, inside))

    return dict(ok=all(item["ok"] for item in checks), checks=checks, plate=plate, shot=shot,
                talk_box=talk, receipt_plates=strip, verdict_box=verdict)


# ---------------------------------------------------------------------------------------------------------------------
# CLI


def main(argv=None):
    parser = argparse.ArgumentParser(description="the S5 caption overlay with the Meta bake row")
    parser.add_argument("--shot", choices=sorted(SHOT_ROWS), help="S5 (Morgan's three TALK replies on the quay)")
    parser.add_argument("--frame", help="the frame to draw on, or the rendered frame to check")
    parser.add_argument("--source", help="--check: the clean frame the render started from")
    parser.add_argument("--out", help="where the rendered frame is written")
    parser.add_argument("--below", action="store_true", help="draw the plate under the frame instead of inside it")
    parser.add_argument("--only", default=None,
                        help="comma separated bake row ids this drawing carries, or an empty string for none "
                             "(the network window draws no row); default: every row the shot declares")
    parser.add_argument("--rows", action="store_true", help="print the lines this shot draws, as JSON, and draw nothing")
    parser.add_argument("--layout", action="store_true",
                        help="print the plate and line boxes as JSON, so another tool can look for the row")
    parser.add_argument("--check", action="store_true", help="measure a rendered frame against its source")
    parser.add_argument("--times", action="store_true", help="print the clocks this shot's overlays run at")
    parser.add_argument("--at", type=float, help="--times: report whether this second falls inside a window")
    parser.add_argument("--allow-fallback", action="store_true",
                        help="draw a row the bake recorded as a fallback, labelled as one; a layout check only")
    parser.add_argument("--talk-box", action="store_true",
                        help="also draw the NES talk box: the row's reply lines, its verdict and its receipt id")
    parser.add_argument("--receipt-plates", action="store_true",
                        help="also draw the three small Meta receipt plates above the dialogue box: "
                             "model_calls, live_rows and live_share_pct, each with its ledger receipt id")
    parser.add_argument("--verdict-box", action="store_true",
                        help="also draw the S5 verdict window: the credits' model name, the decision the bake "
                             "records, the three bake receipts and the network line, in the strip of battle "
                             "frame between the enemy plate and the party panel")
    parser.add_argument("--bake", default=BAKE_PATH, help="the bake file to read (never edited by this tool)")
    args = parser.parse_args(argv)

    if not args.shot:
        print(__doc__)
        return 1
    only = None if args.only is None else tuple(piece.strip() for piece in args.only.split(",") if piece.strip())
    try:
        bake, index = load_bake(args.bake)
        if args.rows:
            lines = overlay_lines(args.shot, bake, index, allow_fallback=args.allow_fallback, rows=only)
            payload = {
                "shot": args.shot,
                "bake_file": args.bake,
                "plate_anchor": SHOT_ANCHOR[args.shot],
                "rows": list(SHOT_ROWS[args.shot] if only is None else only),
                "lines": [{"tier": tier, "text": text} for tier, text in lines],
            }
            if args.talk_box:
                layout = plan(args.shot, bake, index, below=args.below, allow_fallback=args.allow_fallback,
                              talk_box=True, rows=only)
                payload["talk_box"] = {
                    "rect": layout["talk_box"]["rect"],
                    "receipt": layout["talk_box"]["receipt"],
                    "verdict": layout["talk_box"]["verdict"],
                    "row": layout["talk_box"]["row"],
                    "lines": [{"tier": line["tier"], "role": line["role"], "text": line["source_text"]}
                              for line in layout["talk_box"]["lines"]],
                }
            if args.receipt_plates:
                layout = plan(args.shot, bake, index, below=args.below, allow_fallback=args.allow_fallback,
                              talk_box=args.talk_box, rows=only, receipt_plates=True)
                payload["receipt_plates"] = [
                    {"name": part["name"], "value": part["value"], "receipt": part["receipt"],
                     "rect": list(part["rect"]),
                     "lines": [{"tier": line["tier"], "text": line["source_text"]} for line in part["lines"]]}
                    for part in layout["receipt_plates"]
                ]
            if args.verdict_box:
                layout = plan(args.shot, bake, index, below=args.below, allow_fallback=args.allow_fallback,
                              talk_box=args.talk_box, rows=only, receipt_plates=args.receipt_plates,
                              verdict_box=True)
                payload["verdict_box"] = {
                    "rect": layout["verdict_box"]["rect"],
                    "lines": [{"size": line["size"], "role": line["role"], "text": line["source_text"]}
                              for line in layout["verdict_box"]["lines"]],
                }
            print(json.dumps(payload, indent=1))
            return 0
        if args.layout:
            layout = plan(args.shot, bake, index, below=args.below, allow_fallback=args.allow_fallback,
                          talk_box=args.talk_box, rows=only, receipt_plates=args.receipt_plates,
                          verdict_box=args.verdict_box)
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
                    "talk_box": layout["talk_box"],
                    "receipt_plates": layout["receipt_plates"],
                    "verdict_box": layout["verdict_box"],
                    "hud_kept": [{"what": name, "rect": scale_rect(rect)} for name, rect in battle_hud_rects()],
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
                                 below=args.below, allow_fallback=args.allow_fallback, talk_box=args.talk_box,
                                 rows=only, receipt_plates=args.receipt_plates, verdict_box=args.verdict_box)
            for item in report["checks"]:
                print("%s  %s  %s" % ("PASS" if item["ok"] else "FAIL", item["name"], item["detail"]))
            print("%s  %s frame at %s" % ("PASS" if report["ok"] else "FAIL", args.shot, args.frame))
            return 0 if report["ok"] else 1
        if not (args.frame and args.out):
            raise OverlayError("a render needs --frame and --out")
        image, layout = render(args.frame, args.shot, bake, index, below=args.below,
                               allow_fallback=args.allow_fallback, talk_box=args.talk_box, rows=only,
                               receipt_plates=args.receipt_plates, verdict_box=args.verdict_box)
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
