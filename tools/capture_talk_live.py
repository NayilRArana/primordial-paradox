#!/usr/bin/env python3
"""capture_talk_live.py: the proof frames for the live TALK entry (card t_ee178652, label W2 LIVE-TALK).

What this is, and what it is not. GameMaker LTS2026 IS installed on this PC (runtime-2026.0.0.23 under
C:/ProgramData/GameMakerStudio2-LTS2026/Cache/runtimes, measured 2026-10-26) and the project compiles:
tools/integration_build.py prints BUILD PASS. What this tool is not is a screenshot: a window can only be opened on a
machine nobody is using (tools/idle_check.py refuses while the keyboard is busy, card CAPTURE-QUIET, and card
t_ee178652's own rules forbid opening one while Nayil is at the PC), and the real recording is tools/play_demo.py's
job on a quiet machine. So this renders the box from the same three sources the game renders it from, at the same
pixel coordinates the GML uses:

    the frame the GML draws        the geometry is read out of pp_talk_live.gml, pp_battle_director.gml and
                                   pp_battle_text.gml at run time, not restated here
    the glyphs the game draws      game/datafiles/art/spr_pp_font8.png, the shipped 8x8 sheet, 77 frames
    the state the game is in       tools/talk_live.py, the Python mirror of the GML state machine

So the picture is a reconstruction, and it is labelled as one: every frame carries the caption RECONSTRUCTION in its
report entry, the report names the GML lines each coordinate came from, and nothing here is presented as a
screenshot of a run. A real capture is capture_talk_fight.py's job on a machine with a runtime.

The frames, one per state the card names:

    1 entry_keys   the box open, a typed line, the cursor, tries 3/3
    2 entry_grid   the letter grid up, a cell selected, the buffer behind it
    3 entry_voice  a transcript in the buffer, after a hold on the voice key
    4 wait_dots    the thinking beat, two dots up, the budget running
    5 reply        the sailor's answer in the message window and the MERCY bar moved to 20
    6 refused      three tries spent: the fifth entry stays on the panel with the note under it, MERCY at 40

Output: output/talk_live_capture/<frame>.png at 3x, one contact sheet, and capture.json with the debug line each
frame's state would have printed and the provenance of every constant it drew with.

Every frame is judged by the frame audit before it is written: tools/nes_composite_check.py's check_frame, the rule
set tools/nes_audit_all.py gates a shipped 256x240 screen with, run on the 256x240 canvas in memory. A frame that draws
a colour the 2C02 has no output for, needs more than four background palettes, or puts more than 25 colours on screen
is refused and no file is saved, because a capture that is not NES legal is not evidence of anything. The roles it
draws with are resolved through data/palette_ppu.json the way pp_data_palette_rgb resolves them; the first run of this
audit caught the tool drawing the design hexes instead, which made all six frames off palette. tests/test_talk_live.py
audits the same pixels through prepare(), so the picture and the suite cannot drift apart.

    python tools/capture_talk_live.py            (writes the frames and the report)
    python tools/capture_talk_live.py --check    (geometry checks and the frame audit, no files written)
"""

import argparse
import json
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import talk_live  # noqa: E402  the mirror of the GML state machine, shared not copied
import nes_composite_check as composite  # noqa: E402  the frame audit, the same checker nes_audit_all.py gates with

OUT_DIR = os.path.join(ROOT, "output", "talk_live_capture")
SCALE = 3
FRAME_W, FRAME_H = 256, 240
GLYPH = 8

GML_LIVE = os.path.join(ROOT, "game", "scripts", "pp_talk_live", "pp_talk_live.gml")
GML_DIRECTOR = os.path.join(ROOT, "game", "scripts", "pp_battle_director", "pp_battle_director.gml")
GML_TEXT = os.path.join(ROOT, "game", "scripts", "pp_battle_text", "pp_battle_text.gml")
SHEET = os.path.join(ROOT, "game", "datafiles", "art", "spr_pp_font8.png")


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------------------------------------------------
# Geometry, read out of the GML so the picture cannot drift from the game

def box_geometry():
    """The box's nine numbers, from the getter functions pp_talk_live_draw and its two helpers call."""
    source = read(GML_LIVE)
    wanted = {
        "PP_TALK_LIVE_BOX_X": "pp_talk_live_box_x",
        "PP_TALK_LIVE_PROMPT_Y": "pp_talk_live_prompt_y",
        "PP_TALK_LIVE_ROWS_Y": "pp_talk_live_rows_y",
        "PP_TALK_LIVE_ROW_PITCH": "pp_talk_live_row_pitch",
        "PP_TALK_LIVE_HINT_Y": "pp_talk_live_hint_y",
        "PP_TALK_LIVE_GRID_Y": "pp_talk_live_grid_y",
        "PP_TALK_LIVE_GRID_PITCH": "pp_talk_live_grid_pitch",
    }
    numbers = {}
    for name, getter in wanted.items():
        match = re.search(r"function %s\(\)\s*\{\s*return (\d+);" % getter, source)
        if not match:
            raise SystemExit("pp_talk_live.gml no longer defines %s() with a literal return; the box's geometry "
                             "cannot be read" % getter)
        numbers[name] = int(match.group(1))
    if "#macro PP_TALK_LIVE_COLS 28" not in source:
        raise SystemExit("the box's 28 column width is gone from pp_talk_live.gml")
    numbers["cols"] = 28
    numbers["PP_TALK_LIVE_GRID_COLS"] = 0  # filled from data by the caller, the grid width is a data value
    numbers["window"] = (0, 0, 255, 47)
    return numbers


def panel_geometry():
    """The talk panel's row pitch, first row and cursor marks, from the draw call in pp_battle_text.gml."""
    source = read(GML_TEXT)
    body = source[source.index("function pp_talk_draw_options("):]
    body = body[: body.index("\nfunction ")]
    match = re.search(r"var _y = PP_MENU_TOP \+ (\d+) \+ i \* (\d+);", body)
    if not match:
        raise SystemExit("pp_talk_draw_options no longer draws its rows at PP_MENU_TOP + n + i * pitch; the panel "
                         "rows are unknown")
    if "PP_MENU_TOP" not in source:
        raise SystemExit("PP_MENU_TOP is gone from pp_battle_text.gml")
    menu_top = re.search(r"#macro PP_MENU_TOP (\d+)", read(os.path.join(ROOT, "game", "scripts", "pp_config",
                                                                       "pp_config.gml")))
    if not menu_top:
        raise SystemExit("PP_MENU_TOP is no longer a macro in pp_config.gml")
    return {"y0": int(menu_top.group(1)) + int(match.group(1)), "pitch": int(match.group(2)),
            "label_x": 24, "cursor_x": (14, 20), "band": (8, int(menu_top.group(1)), 248, 232)}


def bars_geometry():
    """The enemy health bar and the MERCY bar's rows: the slot from data/ui_layouts.json, the offsets from the GML."""
    source = read(GML_DIRECTOR)
    for needle, why in (
        ("var _bar_w = _enemy_slot.w * 2;", "the bar's width"),
        ("var _bar_x = _enemy_slot.x - 16;", "the bar's left edge"),
        ("var _bar_y = _enemy_slot.y + _enemy_slot.h + 4;", "the bar's row"),
        ("pp_font_draw(pp_talk_live_data().will_label, _bar_x, _bar_y + 12, 1);", "the MERCY label's row"),
        ("var _will_y = _bar_y + 20;", "the MERCY bar's row"),
        ("var _will_w = _bar_w;", "the MERCY bar's width"),
    ):
        if needle not in source:
            raise SystemExit("pp_battle_director.gml no longer contains %r, so %s would be drawn from a guess"
                             % (needle, why))
    layouts = json.load(open(os.path.join(ROOT, "data", "ui_layouts.json"), encoding="utf-8"))
    battle = next((screen for screen in layouts["screens"] if screen.get("name") == "battle"), None)
    if battle is None:
        raise SystemExit("data/ui_layouts.json no longer describes a battle screen")
    rows = battle.get("enemies") or []
    if not rows:
        raise SystemExit("data/ui_layouts.json's battle screen no longer has an enemy slot")
    # pp_battle_enemy_slot: the first enemy row, tile coords times 8, its size from the `pixels` field.
    size = [int(part) for part in str(rows[0]["pixels"]).split("x")]
    slot = {"x": rows[0]["x"] * 8, "y": rows[0]["y"] * 8, "w": size[0], "h": size[1]}
    return {"bar_y": slot["y"] + slot["h"] + 4, "bar_x": slot["x"] - 16, "bar_w": slot["w"] * 2,
            "label_dy": 12, "will_dy": 20, "slot": slot}


def roles():
    """The four battle roles' RGB, resolved the way the runtime resolves them.

    data/palette.json's 54 are design colours and 0 of them is a Ricoh 2C02 output (card t_54db4d0f), so the game never
    draws one: pp_data_palette_rgb walks role -> design index -> data/palette_ppu.json's mapping -> the entry's hex in
    data/nes_palette.json, and only entries flagged usable are reachable. This does the same walk for the same reason.
    Drawing the design hex here put four off-palette colours in every frame and the frame audit refused all six, which
    is exactly the bug this tool exists to show rather than hide.
    """
    palette = json.load(open(os.path.join(ROOT, "data", "palette.json"), encoding="utf-8"))
    table = json.load(open(os.path.join(ROOT, "data", "palette_ppu.json"), encoding="utf-8"))
    master = json.load(open(os.path.join(ROOT, "data", "nes_palette.json"), encoding="utf-8"))
    rooms = json.load(open(os.path.join(ROOT, "data", "room_palettes.json"), encoding="utf-8"))
    names = palette["roles"]
    mapping = table["mapping"]
    entry_hex = {str(entry["index"]): entry["hex"] for entry in master["entries"] if entry.get("usable", True)}

    def rgb(role):
        target = mapping.get(str(names[role]))
        if isinstance(target, dict):
            target = target.get("entry", target.get("index"))
        if target is None or str(target) not in entry_hex:
            raise SystemExit("data/palette_ppu.json leaves the %s role with no usable 2C02 entry" % role)
        text = entry_hex[str(target)].lstrip("#")
        return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))

    deck = next((entry for entry in rooms["sets"] if entry.get("id") == "deck_day"), None)
    if deck is None:
        raise SystemExit("data/room_palettes.json has no deck_day set, so the battle roles cannot be read")
    return {role: rgb(role) for role in ("ink", "paper", "dim", "text")}


# ---------------------------------------------------------------------------------------------------------------------
# The sheet and the drawing primitives, the same three the game's pp_font_draw spends

class Sheet:
    def __init__(self, data):
        self.image = Image.open(SHEET).convert("RGBA")
        self.w, self.h = self.image.size
        self.order = talk_live.font_glyphs(ROOT)
        self.index = {char: i for i, char in enumerate(self.order)}
        if len(self.order) * GLYPH != self.w:
            raise SystemExit("pp_font_gml names %d glyphs and the sheet is %d wide, so the sheet and the alphabet "
                             "disagree" % (len(self.order), self.w))

    def frame(self, char):
        slot = self.index.get(char)
        if slot is None:
            return None
        left = slot * GLYPH
        if left + GLYPH > self.w:
            return None
        return self.image.crop((left, 0, left + GLYPH, GLYPH))


def draw_text(canvas, sheet, text, x, y, colour):
    """pp_font_draw: one 8x8 cell per character, the sheet's own ink, no kerning, no tint."""
    for i, char in enumerate(text):
        glyph = sheet.frame(char)
        if glyph is None:
            continue
        cell = Image.new("RGBA", (GLYPH, GLYPH), (0, 0, 0, 0))
        ink = Image.new("RGBA", (GLYPH, GLYPH), colour + (255,))
        mask = glyph.split()[-1]
        ink.putalpha(mask)
        cell.paste(ink, (0, 0), ink)
        canvas.paste(cell, (x + i * GLYPH, y), cell)


def rect(canvas, x1, y1, x2, y2, colour):
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            if 0 <= x < canvas.width and 0 <= y < canvas.height:
                canvas.putpixel((x, y), colour + (255,))


def new_frame(role):
    canvas = Image.new("RGBA", (FRAME_W, FRAME_H), role["ink"] + (255,))
    # The two slots the screen cares about, as plain boxes: the picture is about the box, not the sailor's sprite.
    rect(canvas, 24, 64, 56, 96, role["dim"])       # enemy slot, data/ui_layouts.json
    rect(canvas, 224, 128, 248, 160, role["dim"])   # party block
    return canvas


def draw_window(canvas, role):
    """The battle message window: paper fill, dim two pixel border, x 0 to 255, y 0 to 47."""
    rect(canvas, 0, 0, 255, 47, role["paper"])
    for edge in ((0, 0, 255, 1), (0, 46, 255, 47), (0, 0, 1, 47), (254, 0, 255, 47)):
        rect(canvas, *edge, role["dim"])


def draw_band(canvas, role):
    """The command band, x 8 to 248, y 168 to 232, as pp_battle_draw_menu draws it."""
    rect(canvas, 8, 168, 247, 231, role["paper"])
    for edge in ((8, 168, 247, 169), (8, 230, 247, 231), (8, 168, 9, 231), (246, 168, 247, 231)):
        rect(canvas, *edge, role["dim"])


def draw_bars(canvas, role, sheet, box, bars, mercy, mercy_max, hp_frac):
    rect(canvas, bars["bar_x"], bars["bar_y"], bars["bar_x"] + int(bars["bar_w"] * hp_frac), bars["bar_y"] + 3,
         role["text"])
    draw_text(canvas, sheet, "MERCY", bars["bar_x"], bars["bar_y"] + bars["label_dy"], role["text"])
    y = bars["bar_y"] + bars["will_dy"]
    rect(canvas, bars["bar_x"], y, bars["bar_x"] + bars["bar_w"] - 1, y + 3, role["dim"])
    filled = int(bars["bar_w"] * (max(0, min(mercy, mercy_max)) / float(mercy_max)))
    if filled > 0:
        rect(canvas, bars["bar_x"], y, bars["bar_x"] + filled - 1, y + 3, role["text"])
    return y


def draw_box(canvas, role, sheet, box, machine, dots="", listen=False):
    """The live entry box: prompt row, two rows of the line, the hint, then the grid when it is up."""
    draw_window(canvas, role)
    prompt = machine.data["prompt"]
    draw_text(canvas, sheet, "* " + prompt, box["PP_TALK_LIVE_BOX_X"], box["PP_TALK_LIVE_PROMPT_Y"], role["text"])
    left = machine.tries_left()
    count = "%d/%d" % (left, machine.data["tries_max"])
    draw_text(canvas, sheet, count, 256 - 8 - len(count) * GLYPH, box["PP_TALK_LIVE_PROMPT_Y"], role["text"])

    if listen:
        # pp_talk_live_draw's "listen" case, and the one picture the other two paths cannot produce: the recording
        # line in the text rows and the enemy's patience as the hint. Drawing the keyboard hint here would make the
        # microphone look like the keyboard, which is the one thing the demo must not do.
        draw_text(canvas, sheet, machine.data["hint_voice"], box["PP_TALK_LIVE_BOX_X"],
                  box["PP_TALK_LIVE_ROWS_Y"], role["text"])
        draw_text(canvas, sheet, machine.data["hint_wait"], box["PP_TALK_LIVE_BOX_X"],
                  box["PP_TALK_LIVE_HINT_Y"], role["dim"])
        return

    if dots:
        # pp_talk_live_dots: one dot per 15 steps, three at most, the same string the GML returns.
        draw_text(canvas, sheet, dots, box["PP_TALK_LIVE_BOX_X"], box["PP_TALK_LIVE_ROWS_Y"], role["text"])
        draw_text(canvas, sheet, machine.data["hint_wait"], box["PP_TALK_LIVE_BOX_X"],
                  box["PP_TALK_LIVE_HINT_Y"], role["dim"])
        return

    rows = machine.view_rows()
    if machine.grid_mode != "grid":
        for index, row in enumerate(rows[:2]):
            draw_text(canvas, sheet, row, box["PP_TALK_LIVE_BOX_X"],
                      box["PP_TALK_LIVE_ROWS_Y"] + index * box["PP_TALK_LIVE_ROW_PITCH"], role["text"])

    if machine.grid_mode != "grid":
        draw_text(canvas, sheet, machine.data["hint_keys"], box["PP_TALK_LIVE_BOX_X"],
                  box["PP_TALK_LIVE_HINT_Y"], role["dim"])
    # In grid mode nothing is drawn on the message row: pp_talk_live_grid_y moved the grid down one row off the
    # prompt, its four rows now own 10, 18, 26 and 34, and pp_talk_live_draw_grid no longer draws a tail line or
    # the controls hint because there is no row left to draw them on.

    if machine.grid_mode == "grid":
        cols = box["PP_TALK_LIVE_GRID_COLS"]
        for i, cell in enumerate(machine.data["grid"]):
            x = box["PP_TALK_LIVE_BOX_X"] + (i % cols) * box["PP_TALK_LIVE_GRID_PITCH"]
            y = box["PP_TALK_LIVE_GRID_Y"] + (i // cols) * box["PP_TALK_LIVE_ROW_PITCH"]
            if y + GLYPH > 46:
                break
            draw_text(canvas, sheet, "%s" % cell, x, y, role["text"])
        i = machine.grid
        x = box["PP_TALK_LIVE_BOX_X"] + (i % cols) * box["PP_TALK_LIVE_GRID_PITCH"]
        y = box["PP_TALK_LIVE_GRID_Y"] + (i // cols) * box["PP_TALK_LIVE_ROW_PITCH"]
        rect(canvas, x, y + 8, x + 15, y + 8, role["text"])
    else:
        # Six pixels of rule under the next character's cell: the sheet has no underscore, spec 21 section 1 rule 3.
        cols, shown = box["cols"], machine.data["rows_shown"]
        row = min(shown - 1, len(machine.text) // cols)
        col = len(machine.text) % cols
        x = box["PP_TALK_LIVE_BOX_X"] + col * GLYPH
        y = box["PP_TALK_LIVE_ROWS_Y"] + row * box["PP_TALK_LIVE_ROW_PITCH"] + GLYPH
        y = min(y, box["PP_TALK_LIVE_HINT_Y"] - 2)
        rect(canvas, x, y, x + 5, y, role["text"])


def draw_reply(canvas, role, sheet, machine):
    """The sailor's answer in the same window, with the `* ` marker every reply carries (spec 19)."""
    draw_window(canvas, role)
    box = box_geometry()
    for index, line in enumerate(machine.reply[:3]):
        draw_text(canvas, sheet, "* " + line, box["PP_TALK_LIVE_BOX_X"],
                  box["PP_TALK_LIVE_ROWS_Y"] + index * box["PP_TALK_LIVE_ROW_PITCH"], role["text"])


def draw_panel(canvas, role, sheet, panel, rows, note, prompt=""):
    """The TALK panel: the prompt and any note in the message window, the authored rows and the fifth entry below.

    The note goes in the window, not under the panel: at PP_MENU_TOP + 4 * pitch + 2 the line lands on y 230 and its
    glyph bottoms at 237, over the band's border at 231, which the first render of this tool caught.
    """
    draw_window(canvas, role)
    if prompt:
        draw_text(canvas, sheet, "* " + prompt, 8, 0, role["text"])
    if note:
        draw_text(canvas, sheet, "* " + note, 8, 12, role["dim"])
    draw_band(canvas, role)
    for index, label in enumerate(rows):
        y = panel["y0"] + index * panel["pitch"]
        if index == len(rows) - 1:
            rect(canvas, panel["label_x"], y - 3, 240, y - 3, role["dim"])
        draw_text(canvas, sheet, label, panel["label_x"], y, role["text"])


def panel_rows(data, machine, ctx):
    """The four rows the panel draws: the enemy's talk lines, then the fifth entry (spec 16 amendment)."""
    rows = []
    for line in ctx["talk_lines"][:3]:
        clean = line
        for prefix in ('* "', "* ", '"'):
            if clean.startswith(prefix):
                clean = clean[len(prefix):]
        clean = clean.rstrip('"')
        rows.append(talk_live._cut(clean, 28))
    rows.append(data["prompt"])
    return rows


# ---------------------------------------------------------------------------------------------------------------------
# The six states, driven through the mirror so the numbers are the machine's

def build_frames(data, tape):
    frames = []
    demo = [row["line"] for row in tape["exchanges"] if row.get("enemy") == "navy_sailor"][:3]
    if len(demo) < 3:
        raise SystemExit("data/talk_live_tape.json has %d sailor exchanges, and the demo needs three" % len(demo))
    transcript = tape["hear"][0]["transcript"]

    # 1 the keyboard
    keys = talk_live.LiveTalk(data, tape)
    keys.open()
    typed = keys.type_line(demo[0])
    frames.append(("entry_keys", keys, dict(mercy=0, note=None, dots="", reply=False, panel=False,
                                            debug="PP: talk live entry, mode keyboard, %d of %d characters, "
                                                  "tries left %d"
                                                  % (len(typed), data["chars_max"], keys.tries_left()))))

    # 2 the grid
    grid = talk_live.LiveTalk(data, tape)
    grid.open()
    grid.grid_mode = "grid"
    grid.text = talk_live.scrub(demo[0], data)[: data["cols"]]
    grid.grid = grid.index_of("T")
    frames.append(("entry_grid", grid, dict(mercy=0, note=None, dots="", reply=False, panel=False,
                                            debug="PP: talk live entry, mode grid, cell %d of %d (%r), buffer %d "
                                                  "characters, tries left %d"
                                                  % (grid.grid, len(data["grid"]), grid.cell(), len(grid.text),
                                                     grid.tries_left()))))

    # 3 the microphone open: the listen stage, which is the one picture no other path can produce
    listen = talk_live.LiveTalk(data, tape)
    listen.open()
    listen.record(int(tape["hear"][0]["wav_seconds"] * 60))
    frames.append(("listen", listen, dict(mercy=0, note=None, dots="", reply=False, panel=False, listen=True,
                                          debug="PP: talk live listen, %d steps held, mic open, box open, "
                                                "tries left %d"
                                                % (listen.voice_steps, listen.tries_left()))))

    # 4 the voice leg, its transcript in the same buffer
    voice = talk_live.LiveTalk(data, tape)
    voice.open()
    voice.record(int(tape["hear"][0]["wav_seconds"] * 60))
    voice.voice_release(transcript)
    frames.append(("entry_voice", voice, dict(mercy=0, note=None, dots="", reply=False, panel=False,
                                              debug="PP: talk live voice, %s steps recorded, transcript %d "
                                                    "characters, source replay"
                                                    % (int(tape["hear"][0]["wav_seconds"] * 60), len(voice.text)))))

    # 5 the thinking beat
    wait = talk_live.LiveTalk(data, tape)
    wait.open()
    wait.type_line(demo[0])
    wait.submit()
    for _ in range(data["dots_step_steps"] * 2 + 3):
        wait.step()
    frames.append(("wait_dots", wait, dict(mercy=0, note=None, dots=wait.dots(), reply=False, panel=False,
                                           debug="PP: talk live wait, %d of %d steps, dots %r, box closed"
                                                 % (wait.steps, data["timeout_steps"], wait.dots()))))

    # 6 the answer, and the meter moving
    answered = talk_live.LiveTalk(data, tape)
    answered.open()
    answered.type_line(demo[0])
    answered.submit()
    for _ in range(data["timeout_steps"] + 1):
        answered.step()
    frames.append(("reply", answered, dict(mercy=answered.will, note=None, dots="", reply=True, panel=False,
                                           debug="PP: talk live answer, source %s via %s, verdict %s, will_delta %d, "
                                                 "mercy %d -> %d, turn 2, try 1, lines %d"
                                                 % (answered.source, answered.via, answered.verdict,
                                                    answered.delta, answered.will - answered.delta, answered.will,
                                                    len(answered.reply)))))

    # 7 three tries spent, the authored rows still carry the fight
    spent = talk_live.LiveTalk(data, tape)
    for line in demo:
        if not spent.open():
            break
        spent.type_line(line)
        spent.submit()
        for _ in range(data["timeout_steps"] + 1):
            spent.step()
    refused = not spent.open()
    frames.append(("refused", spent, dict(mercy=spent.will, note=data["tries_note"] if refused else None,
                                          dots="", reply=False, panel=True,
                                          debug="PP: talk live refused, tries %d of %d spent, note %r, authored "
                                                "options still available, mercy %d"
                                                % (spent.tries, data["tries_max"], spent.note, spent.will))))
    return frames


def render(name, machine, extra, ctx):
    canvas = new_frame(ctx["role"])
    if extra["panel"]:
        draw_panel(canvas, ctx["role"], ctx["sheet"], ctx["panel"],
                   panel_rows(machine.data, machine, ctx), extra["note"], prompt=machine.data["prompt"])
    elif extra["reply"]:
        draw_reply(canvas, ctx["role"], ctx["sheet"], machine)
    else:
        draw_box(canvas, ctx["role"], ctx["sheet"], ctx["box"], machine, dots=extra["dots"],
                 listen=extra.get("listen", False))
    draw_bars(canvas, ctx["role"], ctx["sheet"], ctx["box"], ctx["bars"], extra["mercy"],
              machine.data["will_max"], 0.75)
    return canvas


def talk_lines():
    """The three authored rows the panel shows: the enemy's talk_dialogue set, read through its own data files."""
    enemies = json.load(open(os.path.join(ROOT, "data", "enemies", "all.json"), encoding="utf-8"))
    rows = enemies["enemies"] if isinstance(enemies, dict) and "enemies" in enemies else enemies
    card = next((row for row in rows if row.get("id") == "navy_sailor"), None)
    if card is None or "talk_dialogue" not in card:
        raise SystemExit("data/enemies/all.json no longer gives navy_sailor a talk_dialogue set")
    dialogue = json.load(open(os.path.join(ROOT, "data", "dialogue", "all.json"), encoding="utf-8"))
    sets = dialogue["dialogue"] if isinstance(dialogue, dict) and "dialogue" in dialogue else dialogue
    entry = next((row for row in sets if row.get("id") == card["talk_dialogue"]), None)
    if entry is None:
        raise SystemExit("data/dialogue/all.json has no set called %r" % card["talk_dialogue"])
    return entry["lines"]


def verify_frame(canvas, role, name, band=True):
    """The borders the frame must not have printed over, checked on the pixels themselves.

    The first render of this tool put the refusal note under the panel at y 230 and its glyph bottoms reached 237, over
    the band's border. A coordinate check passed; the pixels did not. So the border rows and columns are sampled here,
    and a label drawn over one is a refused frame rather than a note in a log.
    """
    dim = role["dim"] + (255,)
    problems = []
    if band:
        for y in (230, 231):
            for x in range(8, 248):
                if canvas.getpixel((x, y)) != dim:
                    problems.append("%s: the band's border at y %d is painted at x %d" % (name, y, x))
                    break
    for y in (46, 47):
        for x in range(2, 254):
            if canvas.getpixel((x, y)) != dim:
                problems.append("%s: the window's border at y %d is painted at x %d" % (name, y, x))
                break
    for x in (0, 1, 254, 255):
        for y in range(2, 46):
            if canvas.getpixel((x, y)) != dim:
                problems.append("%s: the window's side border at x %d is painted at y %d" % (name, x, y))
                break
    if problems:
        for problem in problems:
            print("REFUSED " + problem)
        raise SystemExit("%s paints over a border" % name)


def audit_frames(canvases, palette):
    """The NES frame audit, on the pixels this tool draws.

    verify_frame() speaks about the borders this tool printed over once already. This speaks about whether the picture
    is a picture a 2C02 could put on a television at all: every visible pixel an output the chip has, every 16x16
    attribute area inside three colours plus the shared backdrop, at most four background palettes and 25 colours on
    the screen. It is the same checker tools/nes_audit_all.py gates a shipped 256x240 screen with
    (tools/nes_composite_check.py, check_frame), called on the frame in memory instead of on a file, so a capture that
    breaks a rule fails here instead of in a judge's eye. A 256x240 frame is the `frame` scope of that audit; this is
    the only place the project can run it before a window exists.

    Returns one (name, report) row per canvas. `report["ok"]` false means the frame is not NES legal.
    """
    rows = []
    for name, canvas in canvases:
        rows.append((name, composite.check_frame(canvas.convert("RGBA"), palette)))
    return rows


def context(data):
    """The geometry the frames are drawn from, read out of the GML and the data files at run time."""
    ctx = {"box": box_geometry(), "panel": panel_geometry(), "bars": bars_geometry(), "role": roles(),
           "sheet": Sheet(data), "talk_lines": talk_lines()}
    ctx["box"]["PP_TALK_LIVE_GRID_COLS"] = data["grid_cols"]
    return ctx


def prepare(data=None, tape=None):
    """Every frame this tool draws, in memory, with the audit that judged it. Writes nothing.

    main() writes what this returns and tests/test_talk_live.py audits the same pixels through the same call, so the
    picture a judge is handed and the picture the suite measures cannot drift apart.

    Returns (ctx, canvases, audit): ctx is the geometry, canvases a list of (name, canvas, extra), audit a list of
    (name, report) from audit_frames.
    """
    if data is None:
        data = talk_live.load_data(ROOT)
    if tape is None:
        tape = talk_live.load_tape(ROOT)
    ctx = context(data)

    # The checks a picture cannot make for itself. Every one of these is a way the frame could be legal but the game
    # be broken, so they run before a pixel is drawn.
    problems = []
    for key in ("prompt", "hint_keys", "hint_grid", "hint_voice", "hint_wait", "tries_note", "empty_note"):
        text = data[key]
        if len(text) > ctx["box"]["cols"]:
            problems.append("%s is %d characters, wider than the box's %d columns"
                            % (key, len(text), ctx["box"]["cols"]))
        missing = [c for c in text if c not in ctx["sheet"].index]
        if missing:
            problems.append("%s draws %r, which the sheet does not have" % (key, missing))
    grid = data["grid"]
    if len(grid) != 44:
        problems.append("the grid is %d cells, not 44" % len(grid))
    for cell in grid:
        if cell in ("DEL", "END"):
            continue
        if cell not in ctx["sheet"].index:
            problems.append("a grid cell draws %r, which the sheet does not have" % cell)
    last = ctx["panel"]["y0"] + 3 * ctx["panel"]["pitch"] + GLYPH
    if last > 232:
        problems.append("the panel's fourth row ends at y %d, over the band's border at 232" % last)
    if ctx["bars"]["bar_y"] + ctx["bars"]["will_dy"] + 4 > 168:
        problems.append("the MERCY bar ends below y 168, under the command band")

    # The grid against the prompt row, which is the bug the ENTRY GRID frame showed: the grid's first row started
    # on the prompt's own row and the two printed over each other. Both numbers come out of pp_talk_live.gml, and
    # both are measured here rather than trusted.
    box = ctx["box"]
    grid_top = box["PP_TALK_LIVE_GRID_Y"]
    prompt_bottom = box["PP_TALK_LIVE_PROMPT_Y"] + GLYPH
    if grid_top < prompt_bottom:
        problems.append("the grid's first row starts at y %d, over the prompt row that ends at y %d"
                        % (grid_top, prompt_bottom))
    rows = (len(grid) + data["grid_cols"] - 1) // data["grid_cols"]
    grid_bottom = grid_top + (rows - 1) * box["PP_TALK_LIVE_ROW_PITCH"] + GLYPH
    if grid_bottom > 46:
        problems.append("the grid's last row ends at y %d, over the window's border at y 46" % grid_bottom)
    if problems:
        for problem in problems:
            print("REFUSED " + problem)
        raise SystemExit("%d geometry problem(s)" % len(problems))

    # Render first, then judge the pixels. A frame that fails the NES audit is never saved as evidence.
    canvases = []
    for name, machine, extra in build_frames(data, tape):
        canvas = render(name, machine, extra, ctx)
        verify_frame(canvas, ctx["role"], name, band=extra["panel"])
        canvases.append((name, canvas, extra))
    palette = composite.load_palette(composite.default_palette_path(ROOT))
    audit = audit_frames([(name, canvas) for name, canvas, _ in canvases], palette)
    return ctx, canvases, audit


def main():
    parser = argparse.ArgumentParser(description="Render the live TALK entry's states from the game's own sources.")
    parser.add_argument("--check", action="store_true", help="geometry and frame audit only, write nothing")
    args = parser.parse_args()

    ctx, canvases, audit = prepare()
    grid = ctx["box"]["cols"]
    if args.check:
        print("geometry ok: %d strings, %d grid cells, panel rows at %d, %d, %d, %d, MERCY bar at y %d"
              % (7, len(talk_live.load_data(ROOT)["grid"]), ctx["panel"]["y0"],
                 ctx["panel"]["y0"] + ctx["panel"]["pitch"],
                 ctx["panel"]["y0"] + 2 * ctx["panel"]["pitch"], ctx["panel"]["y0"] + 3 * ctx["panel"]["pitch"],
                 ctx["bars"]["bar_y"] + ctx["bars"]["will_dy"]))
    bad = [name for name, report in audit if not report["ok"]]
    for name, report in audit:
        if args.check or not report["ok"]:
            print("%-12s frame audit: %s, %d colours, backdrop %s"
                  % (name, "PASS" if report["ok"] else "FAIL %d problem(s)" % len(report["problems"]),
                     report["screen"]["colours"], report["backdrop"]))
        for problem in report["problems"]:
            print("  [%s] %s" % (problem["rule"], problem["detail"]))
    if bad:
        raise SystemExit("%d frame(s) are not NES legal: %s" % (len(bad), ", ".join(bad)))
    if args.check:
        print("frame audit ok: %d of %d frames legal on a 2C02 (tools/nes_composite_check.py check_frame)"
              % (len(audit), len(canvases)))
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    report_doc = {"tool": "capture_talk_live.py", "kind": "talk_live_reconstruction", "note":
                  "reconstruction from the shipped sheet, the GML's own geometry and the Python mirror of the state "
                  "machine, not a screenshot: the project compiles (tools/integration_build.py, BUILD PASS) but a "
                  "window is only opened on a quiet machine (tools/idle_check.py), and the real recording is "
                  "tools/play_demo.py",
                  "scale": SCALE,
                  "audit": {"tool": "tools/nes_composite_check.py, check_frame, one 256x240 frame at a time",
                            "palette": "data/nes_palette.json",
                            "frames": [{"name": name, "ok": report["ok"],
                                        "colours": report["screen"]["colours"],
                                        "backdrop": report["backdrop"]} for name, report in audit]},
                  "geometry": {"box": ctx["box"], "panel": ctx["panel"], "bars": ctx["bars"]}, "frames": []}
    tiles = []
    for name, canvas, extra in canvases:
        path = os.path.join(OUT_DIR, "%s.png" % name)
        canvas.resize((FRAME_W * SCALE, FRAME_H * SCALE), Image.NEAREST).save(path)
        tiles.append((name, canvas))
        report_doc["frames"].append({"name": name,
                                     "png": os.path.relpath(path, ROOT).replace(os.sep, "/"),
                                     "debug": extra["debug"], "caption": "RECONSTRUCTION"})
        print("%-12s %s" % (name, extra["debug"]))

    sheet_w = FRAME_W * SCALE * 3 + 8 * 4
    rows = (len(tiles) + 2) // 3
    sheet_h = rows * (FRAME_H * SCALE + 24) + 8
    contact = Image.new("RGBA", (sheet_w, sheet_h), ctx["role"]["ink"] + (255,))
    for index, (name, canvas) in enumerate(tiles):
        col, row = index % 3, index // 3
        x = 8 + col * (FRAME_W * SCALE + 8)
        y = 8 + row * (FRAME_H * SCALE + 24)
        contact.paste(canvas.resize((FRAME_W * SCALE, FRAME_H * SCALE), Image.NEAREST), (x, y))
        draw_text(contact, ctx["sheet"], name.upper(), x, y + FRAME_H * SCALE + 6, ctx["role"]["text"])
    sheet_path = os.path.join(OUT_DIR, "contact_sheet.png")
    contact.save(sheet_path)
    report_doc["contact_sheet"] = os.path.relpath(sheet_path, ROOT).replace(os.sep, "/")

    report_path = os.path.join(OUT_DIR, "capture.json")
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report_doc, fh, indent=2)
        fh.write("\n")
    print("wrote %d frames, %s and %s" % (len(tiles), report_doc["contact_sheet"],
                                          os.path.relpath(report_path, ROOT).replace(os.sep, "/")))


if __name__ == "__main__":
    main()
