#!/usr/bin/env python3
"""capture_talk_box_spacing.py: the talk box's words, read back off its own pixels.

Card t_f81723d0 (TEXT-BOX-FIX). The defect: pp_dialogue_rows grouped a source line into words and wrote the word items
onto the row with nothing between them, so the box printed `Youarenotonthelist` for `You are not on the list`.

WHAT THIS IS, AND WHAT IT IS NOT. It is not a screenshot. GameMaker is installed on this PC and a window can only be
opened on a machine nobody is using (tools/idle_check.py refuses while the keyboard or the desktop automation is busy,
and this card may not open one while Nayil is at the PC), so the picture here is a RECONSTRUCTION, the same honest
shape tools/capture_talk_live.py uses: every frame carries "reconstruction" in its report entry and names the GML
number each coordinate came from. A real take is tools/play_demo.py's job on a quiet machine.

What it reconstructs, from the game's own files and nothing else:

    the rows        tools/dialogue_rows.py, the mirror of pp_dialogue_rows, at PP_TEXT_CHARS (pp_config.gml)
    the box         pp_window_draw's 30 by 8 slices of game/sprites_src/title/spr_pp_window.png
    the glyphs      pp_font_draw's 8 px pitch over game/sprites_src/title/spr_pp_font8.png, frame order from
                    pp_font_glyphs() in pp_font.gml, one ink colour
    the place       PP_TEXT_X, PP_TEXT_Y, PP_TEXT_LINE_H, the PP_BOX_* rectangle and PP_FRAME_W/H, from pp_config.gml
    the crawl       pp_title_draw_crawl's own numbers: centred on PP_FRAME_W / 2 at PP_TITLE_INTRO_TEXT_Y, one row
                    every PP_TITLE_INTRO_LINE_H, from pp_title.gml
    the lines       the card's own line, the recorded talk answers in data/meta_bake.json (pp_talk_npc_open draws them
                    through the same builder), and the intro crawl's rows in data/intro_text.json

THE MEASUREMENT IS THE POINT. Each 8 by 8 cell of a row is compared, as an ink mask, against the sheet's frames, so the
frame is READ BACK character by character: an empty cell is a space, a cell matching a frame is that character, a cell
matching nothing is a fault. The verdict is then taken on the READ BACK, not on the mirror: the characters the pixels
carry go through the same positional audit tools/dialogue_rows.py applies to text (each row opens where the last ended,
the whole line is consumed, no row is wider than its area). So a clean report says, from pixels alone, that the spaces
are on screen where the line has them.

The frames, one per report entry:

    defect     the card's line through rows_without_the_space: the wrap as it stood. The read back MUST be
               `Youarenotonthelist.` and the audit MUST report the dropped space, or this measure measures nothing.
    fixed      the card's line through rows(): one row, the read back is the line, the audit is clean.
    recorded   a recorded talk answer in data/meta_bake.json that wraps to three rows or fewer: the recorded talk path.
    crawlline  the intro crawl's own rows, drawn the way pp_title_draw_crawl draws them. The crawl never wraps, so its
               read back is its source row, spaces included, at the same 8 px pitch as a letter.

Output: output/talk_box_spacing/<frame>.png at 3x, contact.png (the four frames on one sheet) and capture.json with each
frame's read back, audit and the provenance of every number it drew with. That directory is gitignored; the report is
the evidence, the PNGs are for eyes.

Usage:
    python tools/capture_talk_box_spacing.py            (writes the frames and the report)
    python tools/capture_talk_box_spacing.py --check    (measures, writes nothing)

Exit codes: 0 every frame reads and audits as the card says, 1 a frame does not, 2 an input is missing.

Provenance: written from `function pp_dialogue_rows`, `function pp_dialogue_draw` and `function pp_window_draw` in
game/scripts/pp_dialogue/pp_dialogue.gml, `function pp_font_draw` and `pp_font_draw_centre` in pp_font.gml,
`function pp_title_draw_crawl` in pp_title.gml, and the constants in pp_config.gml. It draws our sheet through our own
numbers and reads nothing outside this repository.
"""

import argparse
import json
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import dialogue_rows  # noqa: E402  the mirror of pp_dialogue_rows, shared with tests/test_dialogue_spacing.py
import preview_dialogue_box as preview  # noqa: E402  the box, its 9 slices and its 8 px glyph paste

OUT_DIR = os.path.join(ROOT, "output", "talk_box_spacing")
META_BAKE_JSON = os.path.join(ROOT, "data", "meta_bake.json")
INTRO_TEXT_JSON = os.path.join(ROOT, "data", "intro_text.json")
TITLE_GML = os.path.join(ROOT, "game", "scripts", "pp_title", "pp_title.gml")
SCALE = 3
CARD_LINE = "You are not on the list."
CRAWL_ROWS = 3


# ---------------------------------------------------------------------------------------------------------------
# Reading the sheet back: the ink mask of a cell is the character drawn there.


def glyph_masks(sheet, glyphs):
    """mask -> character for every frame of the sheet, plus the characters whose mask collides with another's."""
    masks = {}
    ambiguous = set()
    for index, char in enumerate(glyphs):
        frame = sheet.crop((index * 8, 0, index * 8 + 8, 8))
        alpha = frame.split()[3].load()
        mask = tuple(bool(alpha[x, y] > 0) for y in range(8) for x in range(8))
        if not any(mask):
            continue
        if mask in masks:
            ambiguous.add(masks[mask])
            ambiguous.add(char)
            continue
        masks[mask] = char
    return masks, ambiguous


def ink_mask(canvas, ink, x0, y0):
    """The ink of one 8 by 8 cell of the frame, as a mask on the glyph sheet's own ink colour."""
    pixels = canvas.load()
    return tuple(bool(pixels[x0 + x, y0 + y][:3] == tuple(ink[:3])) for y in range(8) for x in range(8))


def read_row(canvas, ink, masks, x0, y0, cells):
    """One row as it stands on the frame: a blank cell is a space, a cell matching a frame is that character."""
    text = ""
    unknown = []
    for index in range(cells):
        mask = ink_mask(canvas, ink, x0 + index * 8, y0)
        if not any(mask):
            text += " "
        elif mask in masks:
            text += masks[mask]
        else:
            text += "?"
            unknown.append(index)
    return text.rstrip(), unknown


def read_back(canvas, ink, masks, placed):
    """Every placed row of the frame, as the characters the pixels carry."""
    rows = []
    unknown = []
    for cell in placed:
        text, bad = read_row(canvas, ink, masks, cell["x0"], cell["y0"], cell["cells"])
        rows.append(text)
        unknown.extend((cell["row"], index) for index in bad)
    return rows, unknown


# ---------------------------------------------------------------------------------------------------------------
# The frames.


def box_frame(config, font_sheet, window_sheet, glyphs, wrapped):
    """pp_dialogue_draw's box with these rows in it: the 9 slice window, then one pp_font_draw per row."""
    canvas = Image.new("RGBA", (config["PP_FRAME_W"], config["PP_FRAME_H"]), (0, 0, 0, 255))
    preview.draw_window(canvas, window_sheet, config["PP_BOX_X"], config["PP_BOX_Y"],
                        config["PP_BOX_W"] // 8, config["PP_BOX_H"] // 8)
    placed = []
    for index, text in enumerate(wrapped):
        y = config["PP_TEXT_Y"] + index * config["PP_TEXT_LINE_H"]
        width, missing = preview.draw_text(canvas, font_sheet, glyphs, text, config["PP_TEXT_X"], y)
        placed.append({"row": index, "text": text, "cells": config["PP_TEXT_CHARS"], "missing": missing,
                       "x0": config["PP_TEXT_X"], "y0": y, "width": width})
    return canvas, placed


def crawl_frame(config, title_macros, font_sheet, glyphs, rows):
    """pp_title_draw_crawl for these rows: centred on the frame, one row every PP_TITLE_INTRO_LINE_H, no window."""
    canvas = Image.new("RGBA", (config["PP_FRAME_W"], config["PP_FRAME_H"]), (0, 0, 0, 255))
    placed = []
    for index, text in enumerate(rows):
        width = len(text) * 8
        # pp_font_draw_centre: _centre_x - floor(_w / 2), and _w is 8 px a glyph on the sheet.
        x0 = config["PP_FRAME_W"] // 2 - width // 2
        y = title_macros["PP_TITLE_INTRO_TEXT_Y"] + index * title_macros["PP_TITLE_INTRO_LINE_H"]
        drawn, missing = preview.draw_text(canvas, font_sheet, glyphs, text, x0, y)
        placed.append({"row": index, "text": text, "cells": len(text), "missing": missing,
                       "x0": x0, "y0": y, "width": drawn})
    return canvas, placed


def title_macros():
    """PP_TITLE_INTRO_TEXT_Y and PP_TITLE_INTRO_LINE_H, read from the macros pp_title_draw_crawl itself uses."""
    with open(TITLE_GML, "r", encoding="utf-8-sig") as handle:
        source = handle.read()
    out = {}
    for name in ("PP_TITLE_INTRO_TEXT_Y", "PP_TITLE_INTRO_LINE_H"):
        match = re.search(r"^#macro\s+%s\s+(\d+)\s*$" % name, source, re.MULTILINE)
        if match is None:
            raise SystemExit("%s is not in %s" % (name, TITLE_GML))
        out[name] = int(match.group(1))
    return out


# ---------------------------------------------------------------------------------------------------------------
# The lines each frame carries.


def recorded_answer(limit=3):
    """The longest recorded talk answer in data/meta_bake.json whose wrap fits the box's three rows."""
    with open(META_BAKE_JSON, "r", encoding="utf-8-sig") as handle:
        document = json.load(handle)
    best = None
    for row in document.get("rows", []):
        lines = row.get("text")
        if not isinstance(lines, list) or not lines or not str(row.get("id", "")).startswith("fight/"):
            continue
        joined = " ".join(str(line) for line in lines)
        if " " not in joined:
            continue
        wrapped = []
        for line in lines:
            wrapped.extend(dialogue_rows.rows(str(line)))
        if len(wrapped) > limit:
            continue
        if best is None or len(joined) > len(best[1]):
            best = (row["id"], joined, wrapped)
    if best is None:
        raise SystemExit("no recorded talk answer with a space in it fits the box in %s" % META_BAKE_JSON)
    return best


def crawl_lines():
    """The intro crawl's first rows, from data/intro_text.json's beats, in reading order."""
    if not os.path.isfile(INTRO_TEXT_JSON):
        raise SystemExit("%s is not there" % INTRO_TEXT_JSON)
    with open(INTRO_TEXT_JSON, "r", encoding="utf-8-sig") as handle:
        document = json.load(handle)
    beats = document.get("beats") if isinstance(document, dict) else document
    found = []
    for beat in beats or []:
        for line in beat if isinstance(beat, list) else [beat]:
            if isinstance(line, str) and line.strip():
                found.append(line)
    if not found:
        raise SystemExit("no crawl row in %s" % INTRO_TEXT_JSON)
    return found[:CRAWL_ROWS]


# ---------------------------------------------------------------------------------------------------------------
# The verdict, taken on the read back.


def render(config, macros, font_sheet, window_sheet, glyphs, ink, masks):
    frames = {}

    defect_rows = dialogue_rows.rows_without_the_space(CARD_LINE)
    canvas, placed = box_frame(config, font_sheet, window_sheet, glyphs, defect_rows)
    rows, unknown = read_back(canvas, ink, masks, placed)
    frames["defect"] = {"caption": "the wrap as it stood, card t_f81723d0's defect", "source": CARD_LINE,
                        "image": canvas, "placed": placed, "readback": rows, "unknown_cells": unknown,
                        "audit": dialogue_rows.faults(CARD_LINE, rows)}

    fixed_rows = dialogue_rows.rows(CARD_LINE)
    canvas, placed = box_frame(config, font_sheet, window_sheet, glyphs, fixed_rows)
    rows, unknown = read_back(canvas, ink, masks, placed)
    frames["fixed"] = {"caption": "the wrap after the fix, the card's own line", "source": CARD_LINE,
                       "image": canvas, "placed": placed, "readback": rows, "unknown_cells": unknown,
                       "audit": dialogue_rows.faults(CARD_LINE, rows)}

    row_id, joined, wrapped = recorded_answer()
    canvas, placed = box_frame(config, font_sheet, window_sheet, glyphs, wrapped)
    rows, unknown = read_back(canvas, ink, masks, placed)
    frames["recorded"] = {"caption": "a recorded talk answer, %s" % row_id, "source": joined,
                          "image": canvas, "placed": placed, "readback": rows, "unknown_cells": unknown,
                          "audit": dialogue_rows.faults(joined, rows)}

    crawl = crawl_lines()
    canvas, placed = crawl_frame(config, macros, font_sheet, glyphs, crawl)
    rows, unknown = read_back(canvas, ink, masks, placed)
    frames["crawlline"] = {"caption": "the intro crawl's rows, as pp_title_draw_crawl draws them", "source": crawl,
                           "image": canvas, "placed": placed, "readback": rows, "unknown_cells": unknown,
                           "audit": [fault for index, row in enumerate(rows)
                                     for fault in dialogue_rows.faults(crawl[index], [row])]}
    return frames


def expectations(frames):
    problems = []
    defect = frames["defect"]
    if defect["readback"] != ["Youarenotonthelist."]:
        problems.append("the defect frame reads %r, which is not the defect the card names" % defect["readback"])
    if not defect["audit"]:
        problems.append("the audit passed the defect frame, so it is not measuring the space")
    for name in ("fixed", "recorded", "crawlline"):
        frame = frames[name]
        if frame["unknown_cells"]:
            problems.append("%s frame: cell(s) matching no glyph frame: %s" % (name, frame["unknown_cells"]))
        if frame["audit"]:
            problems.append("%s frame: %s" % (name, "; ".join(frame["audit"])))
    if frames["fixed"]["readback"] != [CARD_LINE]:
        problems.append("the fixed frame reads %r, not %r" % (frames["fixed"]["readback"], [CARD_LINE]))
    if any(frame["unknown_cells"] for frame in frames.values()):
        pass  # already reported per frame above; the defect frame is allowed one only if the sheet lacks a glyph
    return problems


def provenance(config, macros):
    return {
        "reconstruction": True,
        "why": "no window may be opened on this PC while Nayil is at it; a real take is tools/play_demo.py's job",
        "rows": "tools/dialogue_rows.py, the mirror of pp_dialogue_rows",
        "box": "PP_BOX_X %d, PP_BOX_Y %d, PP_BOX_W %d, PP_BOX_H %d at PP_FRAME_W %d, PP_FRAME_H %d"
               % (config["PP_BOX_X"], config["PP_BOX_Y"], config["PP_BOX_W"], config["PP_BOX_H"],
                  config["PP_FRAME_W"], config["PP_FRAME_H"]),
        "text": "PP_TEXT_X %d, PP_TEXT_Y %d, PP_TEXT_LINE_H %d, PP_TEXT_CHARS %d"
                % (config["PP_TEXT_X"], config["PP_TEXT_Y"], config["PP_TEXT_LINE_H"], config["PP_TEXT_CHARS"]),
        "crawl": "PP_TITLE_INTRO_TEXT_Y %d, PP_TITLE_INTRO_LINE_H %d, centred on PP_FRAME_W / 2"
                 % (macros["PP_TITLE_INTRO_TEXT_Y"], macros["PP_TITLE_INTRO_LINE_H"]),
        "font": "game/sprites_src/title/spr_pp_font8.png, frame order from pp_font_glyphs(), one ink",
        "window": "game/sprites_src/title/spr_pp_window.png, 30 by 8 slices",
        "lines": "the card's line, data/meta_bake.json recorded answers, data/intro_text.json crawl rows",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="the talk box's spaces, measured on its own pixels")
    parser.add_argument("--check", action="store_true", help="measure and report, write no file")
    args = parser.parse_args(argv)

    config = preview.read_macros(ROOT)
    for key in ("PP_FRAME_W", "PP_FRAME_H", "PP_BOX_X", "PP_BOX_Y", "PP_BOX_W", "PP_BOX_H",
                "PP_TEXT_X", "PP_TEXT_Y", "PP_TEXT_LINE_H", "PP_TEXT_CHARS"):
        if key not in config:
            raise SystemExit("%s is not in %s" % (key, preview.CONFIG_GML))
    macros = title_macros()
    font_sheet = Image.open(os.path.join(ROOT, preview.FONT_PNG)).convert("RGBA")
    window_sheet = Image.open(os.path.join(ROOT, preview.WINDOW_PNG)).convert("RGBA")
    glyphs = preview.read_glyphs(ROOT)
    ink = preview.ink_colour(font_sheet)
    masks, ambiguous = glyph_masks(font_sheet, glyphs)
    if ambiguous:
        print("note: these glyphs share an ink mask, so a read back of them is ambiguous: %s"
              % "".join(sorted(ambiguous)))

    frames = render(config, macros, font_sheet, window_sheet, glyphs, ink, masks)
    problems = expectations(frames)

    report = {"reconstruction": True, "glyph_frames": len(glyphs), "glyph_masks": len(masks),
              "ambiguous_glyphs": "".join(sorted(ambiguous)), "ink_colour": [int(v) for v in ink],
              "provenance": provenance(config, macros),
              "frames": {name: {"caption": frame["caption"], "source": frame["source"],
                                "readback": frame["readback"], "audit": frame["audit"],
                                "unknown_cells": frame["unknown_cells"],
                                "missing_glyphs": [ch for cell in frame["placed"] for ch in cell["missing"]],
                                "placed": [{k: v for k, v in cell.items() if k != "missing"}
                                           for cell in frame["placed"]]}
                         for name, frame in frames.items()},
              "problems": problems}

    for name, frame in frames.items():
        print("%-10s read back: %s" % (name, " / ".join(frame["readback"])))
        print("%-10s audit: %s" % ("", frame["audit"] or "clean"))

    if not args.check:
        os.makedirs(OUT_DIR, exist_ok=True)
        order = ["defect", "fixed", "recorded", "crawlline"]
        for name in order:
            image = frames[name]["image"]
            image.resize((image.width * SCALE, image.height * SCALE), Image.NEAREST).save(
                os.path.join(OUT_DIR, "%s.png" % name))
        columns = 2
        rows_of_sheet = (len(order) + columns - 1) // columns
        sheet = Image.new("RGBA", (config["PP_FRAME_W"] * SCALE * columns,
                                   config["PP_FRAME_H"] * SCALE * rows_of_sheet), (0, 0, 0, 255))
        for index, name in enumerate(order):
            image = frames[name]["image"].resize((config["PP_FRAME_W"] * SCALE, config["PP_FRAME_H"] * SCALE),
                                                 Image.NEAREST)
            sheet.paste(image, ((index % columns) * config["PP_FRAME_W"] * SCALE,
                                (index // columns) * config["PP_FRAME_H"] * SCALE))
        sheet.save(os.path.join(OUT_DIR, "contact.png"))
        with open(os.path.join(OUT_DIR, "capture.json"), "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
        print("wrote %s" % OUT_DIR)

    if problems:
        print("FAIL")
        for problem in problems:
            print("  %s" % problem)
        return 1
    print("PASS: the fixed frame reads back as the line, the defect frame reads back without its spaces, "
          "and the crawl's rows read back unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
