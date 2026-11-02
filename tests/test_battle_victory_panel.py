"""Card t_855887d8: the victory panel a won fight ends on.

The first fight on the demo route stopped with no presentation: a bare paper rectangle with the outcome word on it,
drawn out of pp_app's battle draw, and nothing that said the fight was over. The panel is now the battle screen's own
window (pp_battle_window_b, the nine slice the enemy plate, the party panel and the command band draw) with a paper
field inside it, the title VICTORY, the outcome word the fight chose, and the one key that leaves.

What this file holds down, and why each one earns its place:

  1. THE PANEL IS THE DIRECTOR'S. pp_battle_draw_victory exists in pp_battle_director.gml, is called from the end of
     pp_battle_draw, and pp_app's battle draw no longer draws a panel of its own. A second panel left behind would be
     drawn over this one, which is how the white block lasted as long as it did.

  2. THE TRIGGER IS A WON FIGHT AND NOTHING ELSE. pp_battle_victory_shown is kill or spare, phase result or ended,
     not defeated, no scene handover. The words of that guard are read out of the GML and checked one by one,
     including the two that must be absent, so widening it (an interruption, a defeat, the pre result beat's
     dialogue) is a red test.

  3. THE GEOMETRY IS ONE ROW. The panel's rect and its three text rows are data/ui_layouts.json battle_b.victory,
     the same row tools/render_battle_visuals.py composes from and tools/capture_first_fight.py scores against, and
     the art tool that rewrites that file carries it too. Each of those is asserted, because a geometry that lives
     in two files drifts.

  4. THE PANEL IS COMPOSED AND SCORED. The frame is built here from the project's own sheets and palette roles at the
     GML's own draw calls (pinned text for text below), then handed to the capture verifier's own score_frame and
     is_victory_frame. That is the only form a fresh capture can take on this host: tools/idle_check.py refuses to
     open a game window while a desktop automation is resident, and no GameMaker build runs in this gate. The
     negative controls at the bottom remove the field, remove the prompt and put a six glyph word on a spare, so the
     score is a measurement and can fail.

Run: python -m pytest tests/test_battle_victory_panel.py -q
"""

from __future__ import annotations

import json
import os
import re

import pytest

PIL = pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

# Card TEST-CLASSIFY-33: importing tools/capture_first_fight.py binds ctypes.windll.user32 on Windows and raises
# elsewhere, so this file skips off Windows rather than passing there.
pytestmark = pytest.mark.windows_only

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRECTOR = os.path.join(ROOT, "game", "scripts", "pp_battle_director", "pp_battle_director.gml")
APP = os.path.join(ROOT, "game", "scripts", "pp_app", "pp_app.gml")
FONT_GML = os.path.join(ROOT, "game", "scripts", "pp_font", "pp_font.gml")
LAYOUT = os.path.join(ROOT, "data", "ui_layouts.json")
PALETTE = os.path.join(ROOT, "data", "palette.json")
NES_PALETTE = os.path.join(ROOT, "data", "nes_palette.json")
FONT = os.path.join(ROOT, "game", "sprites_src", "title", "spr_pp_font8.png")
WINDOW = os.path.join(ROOT, "game", "sprites_src", "title", "spr_pp_window.png")
ART_TOOL = os.path.join(ROOT, "tools", "art", "make_battle_actors.py")

CELL = 8
FRAME_W, FRAME_H = 256, 240
BORDER = 8


def read(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def code_only(text):
    """Drop comments: the rules below judge calls, and the card's own prose names them."""
    return "\n".join(line.split("//")[0] for line in text.splitlines())


def function_body(code, name):
    match = re.search(r"\bfunction\s+%s\s*\(" % re.escape(name), code)
    assert match is not None, "no function %s in the director" % name
    start = code.find("{", match.end())
    depth = 0
    for index in range(start, len(code)):
        if code[index] == "{":
            depth += 1
        elif code[index] == "}":
            depth -= 1
            if depth == 0:
                return code[start:index + 1]
    raise AssertionError("unbalanced braces in %s" % name)


def glyphs():
    """The sheet's glyph order, from pp_font_glyphs: the function the game looks a character up in."""
    match = re.search(r'function\s+pp_font_glyphs\s*\(\)\s*\{\s*return\s+"(.*?)";', read(FONT_GML), re.S)
    assert match is not None, "pp_font_glyphs no longer returns a literal string"
    return match.group(1).replace('\\"', '"')


def roles():
    """ink, paper and dim as the battle screen spends them: data/palette.json's role table."""
    palette = json.loads(read(PALETTE))
    names, colours = palette["roles"], palette["colours"]

    def rgb(role):
        text = colours[names[role]].lstrip("#")
        return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))

    return {role: rgb(role) for role in ("ink", "paper", "dim", "text")}


def panel_row():
    return json.loads(read(LAYOUT))["battle_b"]["victory"]


class Sheet:
    """The two sheets the panel is made of, pasted the way the GML pastes them."""

    def __init__(self):
        self.font = Image.open(FONT).convert("RGBA")
        self.window = Image.open(WINDOW).convert("RGBA")
        self.glyphs = glyphs()
        self.roles = roles()

    def frame(self):
        return Image.new("RGB", (FRAME_W, FRAME_H), self.roles["ink"])

    def field(self, im, x, y, w, h, role="paper"):
        im.paste(Image.new("RGB", (w, h), self.roles[role]), (x, y))

    def nine_slice(self, im, x, y, tiles_w, tiles_h):
        """pp_window_draw's own tile order: corners, edges, centre, from a 9 frame sheet of 8 x 8 tiles."""
        t = CELL
        for ty in range(tiles_h):
            for tx in range(tiles_w):
                if ty == 0:
                    sl = 0 if tx == 0 else (2 if tx == tiles_w - 1 else 1)
                elif ty == tiles_h - 1:
                    sl = 6 if tx == 0 else (8 if tx == tiles_w - 1 else 7)
                else:
                    sl = 3 if tx == 0 else (5 if tx == tiles_w - 1 else 4)
                tile = self.window.crop((sl * t, 0, sl * t + t, t))
                im.paste(tile, (x + tx * t, y + ty * t), tile)

    def text(self, im, s, x, y):
        for offset, ch in enumerate(s):
            index = self.glyphs.find(ch)
            assert index >= 0, "the sheet has no glyph for %r" % ch
            tile = self.font.crop((index * CELL, 0, index * CELL + CELL, CELL))
            im.paste(tile, (x + offset * CELL, y), tile)

    def centre(self, im, s, cx, y):
        self.text(im, s, cx - len(s) * CELL // 2, y)

    def victory(self, word, press=True, row=None, field=True, prompt=True):
        """pp_battle_draw_victory, draw for draw, from the layout row and the two sheets."""
        row = row or panel_row()
        im = self.frame()
        x, y = row["x"], row["y"]
        x2, y2 = row["x"] + row["w"] * CELL - 1, row["y"] + row["h"] * CELL - 1
        self.nine_slice(im, x, y, row["w"], row["h"])
        if field:
            self.field(im, x + BORDER, y + BORDER, x2 - BORDER - (x + BORDER) + 1, y2 - BORDER - (y + BORDER) + 1)
        self.field(im, x + 16, row["title_y"] + 9, row["w"] * CELL - 32, 1, "dim")
        cx = x + row["w"] * 4
        self.centre(im, "VICTORY", cx, row["title_y"])
        self.centre(im, word, cx, row["word_y"])
        if press and prompt:
            self.centre(im, "press Z", cx, row["press_y"])
        return im


# ---------------------------------------------------------------------------------------------------------------
# 1. The panel belongs to the director, and the old draw is gone.


def test_the_panel_is_drawn_by_the_director():
    code = code_only(read(DIRECTOR))
    assert "function pp_battle_draw_victory(" in code
    draw = function_body(code, "pp_battle_draw")
    assert "if (pp_battle_victory_shown(_battle)) pp_battle_draw_victory(_battle);" in draw, (
        "pp_battle_draw no longer draws the victory panel")
    # Drawn after the game over branch, so a lost fight's card is never painted over by a win panel.
    assert draw.index("pp_battle_draw_gameover(_battle)") < draw.index("pp_battle_draw_victory(_battle)")


def test_pp_app_no_longer_draws_a_panel_of_its_own():
    code = code_only(read(APP))
    assert "draw_rectangle(40, 100" not in code, "the old paper rectangle is still drawn from pp_app"
    assert "pp_battle_draw_victory" in code or "pp_battle_draw(_battle)" in code
    # The door is unchanged: the mode still waits for confirm and only once the fight has finished.
    battle = function_body(code, "pp_mode_battle")
    assert 'pp_pressed("confirm")' in battle
    assert "pp_battle_finished(_battle)" in battle


# ---------------------------------------------------------------------------------------------------------------
# 2. The trigger: a won fight, from its result beat to its end, and nothing else.


def test_the_panel_shows_only_on_a_won_fight():
    code = code_only(read(DIRECTOR))
    shown = function_body(code, "pp_battle_victory_shown")
    assert "_battle.result != PPResult.kill && _battle.result != PPResult.spare" in shown
    assert "if (_battle.defeated) return false;" in shown
    assert 'if (pp_battle_handoff_scene(_battle) != "") return false;' in shown
    assert "_battle.phase == PPBattlePhase.result || _battle.phase == PPBattlePhase.ended" in shown
    # The two words that must not appear: a defeat and an interruption are other cards' endings.
    assert "PPResult.interrupt" not in shown
    assert "PPBattlePhase.dodge" not in shown


def test_the_prompt_waits_for_the_fight_to_finish():
    """Before pp_battle_finished the mode refuses the press, so the prompt appears only once it can be taken."""
    code = code_only(read(DIRECTOR))
    draw = function_body(code, "pp_battle_draw_victory")
    assert 'if (pp_battle_finished(_battle)) pp_font_draw_centre("press Z"' in draw
    assert draw.count('pp_font_draw_centre("press Z"') == 1


# ---------------------------------------------------------------------------------------------------------------
# 3. One geometry row, and every reader of it carries the same numbers.


def test_the_layout_row_is_inside_the_frame_and_has_room_for_its_three_rows():
    row = panel_row()
    x1, y1 = row["x"], row["y"]
    x2, y2 = x1 + row["w"] * CELL - 1, y1 + row["h"] * CELL - 1
    assert 0 <= x1 < x2 < FRAME_W and 0 <= y1 < y2 < FRAME_H
    assert row["w"] >= 3 and row["h"] >= 3, "a nine slice needs three tiles a side"
    field_top, field_bottom = y1 + BORDER, y2 - BORDER
    for name in ("title_y", "word_y", "press_y"):
        assert field_top <= row[name] and row[name] + CELL - 1 <= field_bottom, "%s is outside the field" % name
    assert row["title_y"] < row["word_y"] < row["press_y"], "the three rows must be in reading order"
    # The field is the frame less its two 8 px borders, 176 px wide, the width the old pp_app panel was measured at.
    assert row["w"] * CELL - 2 * BORDER == 176
    # The rule under the title sits between the title's last row and the word's first, and touches neither.
    rule_y = row["title_y"] + 9
    assert row["title_y"] + CELL - 1 < rule_y < row["word_y"]


def test_the_art_tool_that_rewrites_the_layout_carries_the_same_row():
    """tools/art/make_battle_actors.py rebuilds battle_b; a row it does not carry would be dropped by the next run."""
    text = read(ART_TOOL)
    row = panel_row()
    wanted = ('"victory": {"x": %d, "y": %d, "w": %d, "h": %d, "title_y": %d, "word_y": %d, "press_y": %d}'
              % (row["x"], row["y"], row["w"], row["h"], row["title_y"], row["word_y"], row["press_y"]))
    assert wanted in text


def test_the_verifier_and_the_offline_renderer_read_that_row():
    """One geometry row, two readers: the verifier parses it, the renderer composes from it."""
    tool = code_only(read(os.path.join(ROOT, "tools", "capture_first_fight.py")))
    assert "def victory_panel():" in tool
    assert 'row = screen.get("victory") if isinstance(screen, dict) else None' in tool
    assert "panel = victory_panel()" in tool
    renderer = read(os.path.join(ROOT, "tools", "render_battle_visuals.py"))
    assert 'w = L["victory"]' in renderer


# ---------------------------------------------------------------------------------------------------------------
# 4. The composed panel, scored by the capture verifier itself.


def score(image):
    """Hand the composed frame to the verifier's own reader, the way a recorded frame reaches it."""
    import capture_first_fight as tool

    pixels = image.load()
    return tool.score_frame(pixels, tool.role_colours(), tool.menu_geometry(), tool.command_labels()), tool


@pytest.mark.parametrize("word", ["kill", "spare"])
def test_a_won_fight_composes_to_a_frame_the_verifier_calls_victory(word):
    scores, tool = score(Sheet().victory(word))
    assert scores["victory_panel_paper"] >= tool.VICTORY_PANEL_MIN, scores
    assert scores["victory_word_width"] >= tool.VICTORY_WORD_MIN, scores
    assert scores["victory_press_width"] >= tool.VICTORY_PRESS_MIN, scores
    assert tool.is_victory_frame(scores)


def test_the_spare_word_fits_the_band_the_talk_capture_asks_for():
    """capture_talk_fight's spare row is a word wider than `kill` and no wider than five glyphs."""
    import capture_talk_fight as talk

    scores, _tool = score(Sheet().victory("spare"))
    assert talk.SPARE_WORD_MIN <= scores["victory_word_width"] <= talk.SPARE_WORD_MAX


def test_the_panel_is_a_window_with_a_field_and_not_a_placeholder_rectangle():
    """The frame ring is the window sheet's own art; the field is the paper role; neither is one flat fill."""
    sheet = Sheet()
    row = panel_row()
    image = sheet.victory("kill")
    role_paper = sheet.roles["paper"]
    # The field is paper, all but the words and the rule.
    field_hit = 0
    field_total = 0
    for y in range(row["y"] + BORDER, row["y"] + row["h"] * CELL - BORDER):
        for x in range(row["x"] + BORDER, row["x"] + row["w"] * CELL - BORDER):
            field_total += 1
            if image.getpixel((x, y)) == role_paper:
                field_hit += 1
    assert field_total and field_hit / float(field_total) >= 0.85
    # The ring is not: the nine slice draws ink, paper and the sheet's third colour on it.
    ring = set()
    for x in range(row["x"], row["x"] + row["w"] * CELL):
        for y in (row["y"], row["y"] + CELL - 1, row["y"] + row["h"] * CELL - CELL, row["y"] + row["h"] * CELL - 1):
            ring.add(image.getpixel((x, y)))
    assert len(ring) >= 2, "the panel's edge is one flat colour, which is a rectangle and not a window"


def test_the_panel_draws_no_colour_the_hardware_cannot_output():
    """RULE 0: every pixel is a data/palette.json colour or a 2C02 output, and nothing is blended."""
    sheet = Sheet()
    allowed = set()
    for text in json.loads(read(PALETTE))["colours"]:
        text = text.lstrip("#")
        allowed.add(tuple(int(text[i:i + 2], 16) for i in (0, 2, 4)))
    nes = json.loads(read(NES_PALETTE))

    def walk(obj):
        if isinstance(obj, dict):
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)
        elif isinstance(obj, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", obj):
            text = obj.lstrip("#")
            allowed.add(tuple(int(text[i:i + 2], 16) for i in (0, 2, 4)))

    walk(nes)
    image = sheet.victory("kill")
    row = panel_row()
    outside = set()
    for y in range(row["y"], row["y"] + row["h"] * CELL):
        for x in range(row["x"], row["x"] + row["w"] * CELL):
            pixel = image.getpixel((x, y))
            if pixel not in allowed:
                outside.add(pixel)
    assert not outside, "the panel draws colours outside the palette: %r" % sorted(outside)[:4]


# ---------------------------------------------------------------------------------------------------------------
# The negative controls: the score above is a measurement, and these are the frames it must refuse.


def test_a_panel_with_no_field_is_not_a_paper_panel():
    scores, tool = score(Sheet().victory("kill", field=False))
    assert scores["victory_panel_paper"] < tool.VICTORY_PANEL_MIN
    assert not tool.is_victory_frame(scores)


def test_a_panel_with_no_prompt_is_not_the_panel_the_fight_ends_on():
    scores, tool = score(Sheet().victory("kill", prompt=False))
    assert scores["victory_press_width"] < tool.VICTORY_PRESS_MIN
    assert not tool.is_victory_frame(scores)


def test_a_six_glyph_word_is_not_a_spare():
    """The negative row the talk capture already names: VICTORY is 7 glyphs and must not read as `spare`."""
    import capture_talk_fight as talk

    scores, _tool = score(Sheet().victory("VICTORY"))
    assert not talk.is_spare_frame(scores)


def test_the_panel_moves_when_the_row_moves():
    """The verifier reads the row, so its bands follow the geometry instead of the numbers it used to carry."""
    import capture_first_fight as tool

    row = panel_row()
    moved = tool.victory_panel()
    assert moved["rect"] == (row["x"], row["y"], row["x"] + row["w"] * CELL - 1, row["y"] + row["h"] * CELL - 1)
    assert moved["field"] == (row["x"] + BORDER, row["y"] + BORDER,
                              row["x"] + row["w"] * CELL - BORDER - 1, row["y"] + row["h"] * CELL - BORDER - 1)
    assert (moved["title_y"], moved["word_y"], moved["press_y"]) == (row["title_y"], row["word_y"], row["press_y"])
    # And the frame composed at those numbers is the frame it scores.
    scores, _tool = score(Sheet().victory("kill"))
    assert scores["victory_word_width"] >= tool.VICTORY_WORD_MIN
