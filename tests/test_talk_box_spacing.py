"""TEXT-BOX-FIX, the pixels half: the capture's read back, held to what the card promises.

Card t_f81723d0. tools/capture_talk_box_spacing.py draws the talk box at the game's own numbers and then READS the
frame back, 8 by 8 cell, against the glyph sheet's own frames, so the characters on screen are measured rather than
assumed. This file runs that measure in the suite, so the tool cannot rot into a picture nobody checks.

What it asserts, and why each one is worth a row:

1. The measure is not vacuous. The frame drawn from the defect (rows_without_the_space) must read back as
   `Youarenotonthelist.`, with no space cells in it, and its audit must report the dropped space. A green run means the
   read back can see a missing space, which is the only thing that makes the fixed frame's clean audit mean anything.
2. The fixed frame reads back as the card's line, and the audit is clean.
3. The recorded talk answer and the intro crawl's rows read back with their spaces and audit clean, so the two paths the
   card names are covered by the same measure.
4. Every cell of every clean frame matched a real glyph frame: a read back holding a `?` would mean the sheet and the
   measurement disagreed, and a picture drawn from a cell nobody can name is not evidence.

The interpreter note: this file needs Pillow, which the repository's suite interpreter
(<home>/AppData/Local/Python/bin/python.exe, the command the gate prints) has and projects/primordial-paradox/
.venv does not. tests/test_talk_live.py has the same requirement for the same reason.
"""

from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

pytest.importorskip("PIL", reason="the capture draws with Pillow")

import capture_talk_box_spacing as capture  # noqa: E402


def frames():
    """Every frame the tool renders, built once: the four renders are a few hundred milliseconds in total."""
    config = capture.preview.read_macros(ROOT)
    font_sheet = capture.Image.open(os.path.join(ROOT, capture.preview.FONT_PNG)).convert("RGBA")
    window_sheet = capture.Image.open(os.path.join(ROOT, capture.preview.WINDOW_PNG)).convert("RGBA")
    glyphs = capture.preview.read_glyphs(ROOT)
    ink = capture.preview.ink_colour(font_sheet)
    masks, _ambiguous = capture.glyph_masks(font_sheet, glyphs)
    return capture.render(config, capture.title_macros(), font_sheet, window_sheet, glyphs, ink, masks)


def test_the_read_back_sees_the_defect():
    """The control: a frame with no spaces in it must read back with no spaces, and the audit must say so."""
    defect = frames()["defect"]
    assert defect["readback"] == ["Youarenotonthelist."], defect["readback"]
    assert " " not in defect["readback"][0], defect["readback"]
    assert defect["audit"], "the audit passed a frame with no spaces in it, so it measures nothing"


def test_the_fixed_frame_reads_back_as_the_card_line():
    fixed = frames()["fixed"]
    assert fixed["readback"] == [capture.CARD_LINE], fixed["readback"]
    assert fixed["audit"] == [], fixed["audit"]


def test_the_recorded_talk_path_and_the_crawl_read_back_with_their_spaces():
    rendered = frames()
    for name in ("recorded", "crawlline"):
        frame = rendered[name]
        assert frame["audit"] == [], "%s: %s" % (name, frame["audit"])
        assert frame["unknown_cells"] == [], "%s: a cell matched no glyph frame: %s" % (name, frame["unknown_cells"])
        assert any(" " in row.strip() for row in frame["readback"] if row.strip()), (
            "%s read back with no gap between words: %s" % (name, frame["readback"]))


def test_every_cell_of_the_clean_frames_names_a_glyph():
    rendered = frames()
    for name in ("fixed", "recorded", "crawlline"):
        assert "?" not in "".join(rendered[name]["readback"]), rendered[name]["readback"]


def test_the_tool_promises_what_the_frames_show():
    """The tool's own verdict function, run on its own frames: the shape the card's check reads."""
    assert capture.expectations(frames()) == []
