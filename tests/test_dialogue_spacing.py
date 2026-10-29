"""TEXT-BOX-FIX: the box keeps the space between two words.

The defect (card t_f81723d0): pp_dialogue_rows split a source line into words and then concatenated the words with
nothing between them, so the box printed `Youarenotonthelist` for `You are not on the list`. Every screen that draws
through pp_dialogue_draw had it, and so did the baked NPC conversation (pp_talk_npc_open builds its pages with the same
function), which is the recorded talk path.

What this file can honestly prove from pytest: the source text and a faithful mirror of the row builder. GameMaker is
not callable from the Python suite (the same limit tests/test_text_reveal.py and tests/test_dialogue_v2.py state), so
the mirror lives in tools/dialogue_rows.py, reads its width from the same PP_TEXT_CHARS macro the engine wraps with, and
is the SAME module tools/capture_talk_box_spacing.py draws its frames through, so the picture and the suite cannot
drift apart. This file does four things:

1. THE SOURCE. It reads pp_dialogue_rows' own body and fails unless the space item is pushed between two words and the
   fit test counts it, so a rewrite that drops the space again fails here by name instead of on a screen.
2. THE MIRROR, MEASURED ON THE REAL LINES. It runs the mirror over every drawable line in data/dialogue/all.json,
   data/meta_bake.json (the recorded talk lines) and data/talk_cards.json. For each line the rows are walked
   positionally: row 0 opens at column 0, each later row opens where the last ended (one column on when the break fell
   on a space, the same column when a word was split), and the whole line is consumed; no row is wider than the box's
   28 columns and no row starts, ends or doubles a space.
3. THE AUDITOR IS NOT VACUOUS. The same audit is fed a mirror without the space push (the defect itself) and must
   report it, so a passing run means the audit looked at something.
4. THE CRAWL IS OUT OF REACH. pp_title builds its units with pp_text_items and never calls pp_dialogue_rows, so this
   fix cannot move a character of the intro crawl.
"""

from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from dialogue_rows import box_chars, faults, rows, rows_without_the_space  # noqa: E402

CONFIG_GML = os.path.join("game", "scripts", "pp_config", "pp_config.gml")
DIALOGUE_GML = os.path.join("game", "scripts", "pp_dialogue", "pp_dialogue.gml")
BATTLE_GML = os.path.join("game", "scripts", "pp_battle_text", "pp_battle_text.gml")
TITLE_GML = os.path.join("game", "scripts", "pp_title", "pp_title.gml")
FONT_GML = os.path.join("game", "scripts", "pp_font", "pp_font.gml")
DIALOGUE_JSON = os.path.join("data", "dialogue", "all.json")
META_BAKE_JSON = os.path.join("data", "meta_bake.json")
TALK_CARDS_JSON = os.path.join("data", "talk_cards.json")


def read(relative):
    with open(os.path.join(ROOT, relative), "r", encoding="utf-8-sig") as handle:
        return handle.read()


def code_of(relative):
    """The file with its comments removed, so prose that names a construct is not read as the construct."""
    lines = []
    for line in read(relative).split("\n"):
        cut = line.find("//")
        lines.append(line if cut == -1 else line[:cut])
    return "\n".join(lines)


def function_body(code, name):
    match = re.search(r"^function\s+%s\s*\(" % re.escape(name), code, re.MULTILINE)
    if match is None:
        return ""
    start = code.index("{", match.end())
    depth = 0
    for index in range(start, len(code)):
        if code[index] == "{":
            depth += 1
        elif code[index] == "}":
            depth -= 1
            if depth == 0:
                return code[start:index + 1]
    raise AssertionError("unbalanced body for %s" % name)


def glyphs():
    body = re.search(r"function\s+pp_font_glyphs\s*\(\s*\)\s*\{(.*?)\n\}", read(FONT_GML), re.S)
    literal = re.search(r'return\s+"((?:[^"\\]|\\.)*)"\s*;', body.group(1))
    raw = literal.group(1)
    out = []
    index = 0
    while index < len(raw):
        if raw[index] == "\\" and index + 1 < len(raw):
            out.append(raw[index + 1])
            index += 2
            continue
        out.append(raw[index])
        index += 1
    return out


# ---------------------------------------------------------------------------------------------------------------
# The corpus: every drawable line the three data files carry.


def _walk(node, found):
    if isinstance(node, dict):
        for value in node.values():
            _walk(value, found)
    elif isinstance(node, list):
        for value in node:
            _walk(value, found)
    elif isinstance(node, str):
        found.append(node)


def drawable_lines():
    """Every string in the three files that the sheet can draw and that holds a space, deduplicated in file order."""
    allowed = set(glyphs())
    found = []
    for relative in (DIALOGUE_JSON, META_BAKE_JSON, TALK_CARDS_JSON):
        with open(os.path.join(ROOT, relative), "r", encoding="utf-8-sig") as handle:
            _walk(json.load(handle), found)
    out = []
    seen = set()
    for text in found:
        if " " not in text or len(text) > 200:
            continue
        if any(ch not in allowed for ch in text):
            continue
        if text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


# ---------------------------------------------------------------------------------------------------------------
# 1. The source.


def test_the_row_builder_pushes_the_space_between_words():
    """The defect and the fix, in the one body that owns the row: a space item, and a fit test that counts it."""
    body = function_body(code_of(DIALOGUE_GML), "pp_dialogue_rows")
    assert body, "pp_dialogue_rows is not in %s" % DIALOGUE_GML

    pushes = re.findall(r'array_push\(\s*_row\s*,\s*\{\s*ch:\s*" "\s*,[^}]*\}\s*\)', body)
    assert len(pushes) >= 2, (
        "pp_dialogue_rows pushes no space item onto the row (%d found), so two words share a row with nothing "
        "between them: the box prints Youarenotonthelist" % len(pushes))
    # Two sites: the ordinary word branch and the split of a word longer than a row. Both need the separator.
    assert "array_length(_row) + 1 + _wlen > PP_TEXT_CHARS" in body, (
        "the fit test does not count the space it pushes, so a row can be one column wider than the box")
    assert "if (array_length(_row) > 0) array_push(_row" in body, (
        "the space must not be pushed onto an empty row: that is a leading space, which the box never draws")


def test_the_mirror_reads_the_width_from_the_engine_macro():
    """One number for the wrap width: the mirror reads PP_TEXT_CHARS, the macro pp_dialogue_rows counts against."""
    macro = re.search(r"^#macro\s+PP_TEXT_CHARS\s+(\d+)\s*$", read(CONFIG_GML), re.MULTILINE)
    assert macro is not None, "PP_TEXT_CHARS is not in %s" % CONFIG_GML
    assert int(macro.group(1)) == box_chars()


def test_the_crawl_does_not_go_through_the_row_builder():
    """The intro crawl is a layout over pp_text_items, so the box's wrap cannot move a character of it."""
    title = code_of(TITLE_GML)
    assert "pp_dialogue_rows" not in title, "the crawl must not be wrapped by the dialogue box"
    body = function_body(title, "pp_title_crawl_new")
    assert "pp_text_items(" in body, "the crawl builds its units with the one parser"
    # The crawl keeps the source line beside its items, so a space is a unit like any other, drawn at the same pitch
    # as a letter: nothing about the box's wrap can reach it.
    assert "text: _row.text" in body, "the crawl must carry the source line it was built from"


def test_the_recorded_talk_path_is_this_row_builder():
    """The baked NPC conversation draws through pp_dialogue_rows, which is why the talk box had the defect too."""
    body = function_body(code_of(BATTLE_GML), "pp_talk_npc_open")
    assert "pp_dialogue_rows(" in body, "the baked talk conversation must keep drawing through the box's rows"


# ---------------------------------------------------------------------------------------------------------------
# 2. The mirror, over the real lines.


def test_no_line_loses_a_space():
    lines = drawable_lines()
    assert len(lines) > 50, "the corpus is %d lines, which is too few to measure anything" % len(lines)
    offenders = []
    for line in lines:
        offenders.extend(faults(line, rows(line)))
    assert offenders == [], "%d fault(s), first three: %s" % (len(offenders), offenders[:3])


def test_the_card_line_reads_as_written():
    """The exact line the card names: one row, spaces intact, inside the box."""
    line = "You are not on the list."
    assert rows(line) == [line]


def test_a_long_line_breaks_at_a_space_and_keeps_it():
    """More words than a row holds still read in order, with one space at every break and none but at the breaks."""
    line = "* The deck tilts and the mop does not, and the sailor checks his ticket twice."
    wrapped = rows(line)
    assert len(wrapped) > 1, wrapped
    for row in wrapped:
        assert not row.startswith(" ") and not row.endswith(" "), wrapped
    # Every break here falls on a space, so the space put back at each break rebuilds the line exactly.
    assert " ".join(wrapped) == line, wrapped
    assert faults(line, wrapped) == [], wrapped


def test_a_word_longer_than_a_row_is_split_without_a_space():
    """The split of a word too long for a row is not a break at a space, so nothing may be added there."""
    line = "antidisestablishmentarianismism and the rest"
    wrapped = rows(line)
    assert len(wrapped) > 1, wrapped
    assert wrapped[0] == line[:box_chars()], wrapped
    assert faults(line, wrapped) == [], wrapped


# ---------------------------------------------------------------------------------------------------------------
# 3. The auditor catches the defect.


def test_the_audit_catches_the_dropped_space():
    line = "You are not on the list."
    assert rows_without_the_space(line) == ["Youarenotonthelist."]
    reported = faults(line, rows_without_the_space(line))
    assert reported, "the audit passed a line with no spaces in it, so it is not measuring the defect"
    assert "Youarenotonthelist" in reported[0]
