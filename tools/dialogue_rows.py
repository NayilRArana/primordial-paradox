#!/usr/bin/env python3
"""dialogue_rows.py: pp_dialogue_rows in Python, so a face without GameMaker can measure the wrap.

Card t_f81723d0 (TEXT-BOX-FIX). The defect this mirrors: the GML builder grouped a source line into words and wrote
the word items onto the row with nothing between them, so the box printed `Youarenotonthelist` for `You are not on the
list`. Every screen that draws through pp_dialogue_draw had it, and so did the baked NPC conversation
(pp_talk_npc_open), which is the recorded talk path.

What this module is. A row for row translation of the two passes in `game/scripts/pp_dialogue/pp_dialogue.gml`, with the
row kept as a PLAIN STRING (`words` are character strings, and one space character stands for the space item the GML
pushes), because the question a caller asks of it is which characters reach the screen. The GML's hold items
({ch: "", wait: N}) print nothing and are not modelled. The width is read from the same macro the engine wraps with
(PP_TEXT_CHARS in pp_config.gml), so a mirror can never disagree with the box about how many characters fit.

The two functions are the pair the proof needs:

    rows(text)                  the builder as it now stands: one space between two words that share a row, and the
                                fit test counting it, so a row is never one column wider than the box.
    rows_without_the_space(...)  the defect as it stood: the control. A measure that cannot report this one is not
                                measuring the space, so every caller is expected to run it and refuse a clean result.

A row that breaks at a space does not carry that space: the break IS the space, and a trailing space item would widen
the row without printing anything a reader could see. A row that breaks inside a word longer than a row carries no space
either, because the split is not a break at a space. Both facts are why the audit walks the rows positionally instead of
joining them with nothing between them.

Provenance: written from `game/scripts/pp_dialogue/pp_dialogue.gml` (`function pp_dialogue_rows`) and the box's own
constants in pp_config.gml. Nothing here is read from any other game.
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_GML = os.path.join(ROOT, "game", "scripts", "pp_config", "pp_config.gml")


def box_chars():
    """PP_TEXT_CHARS, the number of 8 px columns the box's text area holds, read from the macro the engine wraps with."""
    with open(CONFIG_GML, "r", encoding="utf-8-sig") as handle:
        values = dict(re.findall(r"^#macro\s+(PP_TEXT_[A-Z_]+)\s+(\d+)\s*$", handle.read(), re.MULTILINE))
    return int(values["PP_TEXT_CHARS"])


def _words(text):
    words = []
    current = ""
    for ch in text:
        if ch == " ":
            if current:
                words.append(current)
                current = ""
        else:
            current += ch
    if current:
        words.append(current)
    return words


def rows(text, chars=None):
    """pp_dialogue_rows over one source line: group into words, then greedy fill with one space between two words."""
    if chars is None:
        chars = box_chars()
    out = []
    row = ""
    for word in _words(text):
        if len(word) > chars:
            # A word that cannot fit on a row at all is split and reported. One space still goes between it and the
            # word before it when there is room for one, which is the row's own last column back.
            position = 0
            room = chars - len(row)
            if row:
                if room <= 1:
                    out.append(row)
                    row = ""
                    room = chars
                else:
                    row += " "
                    room -= 1
            while position < len(word):
                if room <= 0:
                    out.append(row)
                    row = ""
                    room = chars
                while position < len(word) and room > 0:
                    row += word[position]
                    position += 1
                    room -= 1
        else:
            if row and len(row) + 1 + len(word) > chars:
                out.append(row)
                row = ""
            if row:
                row += " "
            row += word
    if row:
        out.append(row)
    if not out:
        out.append("")
    return out


def rows_without_the_space(text, chars=None):
    """The defect itself: the same builder with the space push removed. A caller's measure must refuse this."""
    if chars is None:
        chars = box_chars()
    out = []
    row = ""
    for word in _words(text):
        if row and len(row) + len(word) > chars:
            out.append(row)
            row = ""
        row += word
    if row:
        out.append(row)
    return out or [""]


def faults(line, wrapped, chars=None):
    """Every way `wrapped` fails to read as `line`, as readable strings. Empty means the wrap is sound.

    Positional, on purpose: row 0 opens at column 0, each later row opens where the last ended (one column on when the
    break fell on a space, the same column when a word was split), and the walk has to consume the whole line.
    """
    if chars is None:
        chars = box_chars()
    out = []
    expected = re.sub(r" +", " ", line).strip()
    position = 0
    placed = True
    for index, row in enumerate(wrapped):
        if not expected.startswith(row, position):
            out.append("%r row %d does not follow the line at column %d: %r" % (line, index, position, row))
            placed = False
            break
        position += len(row)
        if index < len(wrapped) - 1 and position < len(expected) and expected[position] == " ":
            position += 1
    if placed and position != len(expected):
        out.append("%r reads back as %r, %d of %d characters placed"
                   % (line, " | ".join(wrapped), position, len(expected)))
    for index, row in enumerate(wrapped):
        if len(row) > chars:
            out.append("%r row %d is %d characters, the box holds %d" % (line, index, len(row), chars))
        if row != row.strip():
            out.append("%r row %d starts or ends with a space: %r" % (line, index, row))
        if "  " in row:
            out.append("%r row %d holds two spaces in a row: %r" % (line, index, row))
    return out
