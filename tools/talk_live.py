#!/usr/bin/env python3
"""talk_live.py: a Python mirror of the live TALK state machine in game\\scripts\\pp_talk_live.

Why a mirror and not a GameMaker run. This repository has no GameMaker on the machine the gate runs on (that is the
same reason tests\\test_first_fight.py, tests\\test_talk_baked.py and tools\\check_data.py all compute their claims from
the files rather than from a build). A feature whose whole point is a three second interactive sequence still has to
be provable, so the machine is written twice: once in GML for the game and once here, and the two are held together
mechanically. tests\\test_talk_live.py parses the stage names, the constants and the strings out of the GML and fails
if this file and the game disagree, so the copy cannot drift quietly.

What is mirrored, and what is honestly not:

    mirrored        the stage machine (entry, listen, wait), the line rules (the sheet's alphabet, one space per run,
                    the character cap), the grid navigation and its two commands, the submit rules (empty refused,
                    three tries then closed), the answer contract (verdict, will_delta, reply lines, source), the
                    meter arithmetic and its clamp, the replay lookup and the deterministic miss, the timeout.
    NOT mirrored    the socket. Nothing here opens one, in any mode. The live leg is proved in GML by inspection of
                    one function and in tools\\ai_bridge.py by its own suite; a mirror that could reach the network
                    would be a second client, which is the thing this file must never become.

Usage, from another tool or a test:
    from talk_live import LiveTalk, load_data, load_tape
    box = LiveTalk(data, tape, enemy="navy_sailor", mercy=0)
    box.open()
    box.type_line("You have been on watch all night.")
    box.submit()
    box.step()                      # the thinking beat
    box.step(); box.step()          # the recorded answer lands
    box.will                        # 20
"""

from __future__ import annotations

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULTS = {
    "chars_max": 120,
    "cols": 28,
    "rows_shown": 2,
    "shown_max": 60,
    "tries_max": 3,
    "timeout_steps": 780,
    "blink_steps": 30,
    "dots_step_steps": 15,
    "grid_cols": 11,
    "grid_rows": 4,
    "prompt": "SAY IT YOURSELF",
    "hint_keys": "TYPE  ENTER SEND  ESC BACK",
    "hint_grid": "D PAD MOVE  A TYPE  B DEL  START SEND",
    "hint_voice": "HOLD F5 TO SPEAK",
    "hint_wait": "THE SAILOR CONSIDERS IT",
    "tries_note": "That is enough talking.",
    "empty_note": "Say something first.",
    "will_max": 100,
    "will_label": "MERCY",
    "host": "127.0.0.1",
    "port": 8791,
    "talk_path": "/talk",
    "hear_path": "/hear",
    "mode_default": "replay",
}

# The stage names, in one tuple, which tests\\test_talk_live.py also finds in the GML's switch.
STAGES = ("entry", "listen", "wait")

# The answer contract tools/ai_bridge.py documents. A field outside this set is not read by anything here, the same
# way pp_talk_live_answer_clean reads three fields and a label.
ANSWER_FIELDS = ("verdict", "will_delta", "reply", "source", "mood", "latency_ms", "cached", "origin")
VERDICTS = ("persuaded", "unmoved", "angered")


def _path(rel, root=ROOT):
    return os.path.join(root, *rel.split("/"))


def load_json(rel, root=ROOT):
    with open(_path(rel, root), "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_data(root=ROOT):
    """data/talk_live.json, flattened to the fields the machine reads, with the GML's own defaults behind them."""
    doc = load_json("data/talk_live.json", root)
    out = dict(DEFAULTS)
    bridge = doc.get("bridge") or {}
    limits = doc.get("limits") or {}
    timings = doc.get("timings") or {}
    grid = doc.get("grid") or {}
    strings = doc.get("strings") or {}
    mode = doc.get("mode") or {}
    will = doc.get("will") or {}
    voice = doc.get("voice") or {}

    out["host"] = bridge.get("host", out["host"])
    out["port"] = bridge.get("port", out["port"])
    out["talk_path"] = bridge.get("talk_path", out["talk_path"])
    out["hear_path"] = bridge.get("hear_path", out["hear_path"])
    out["mode_default"] = mode.get("default", out["mode_default"])

    out["chars_max"] = limits.get("chars_max", out["chars_max"])
    out["cols"] = limits.get("cols_per_row", out["cols"])
    out["rows_shown"] = limits.get("chars_shown_rows", out["rows_shown"])
    out["shown_max"] = limits.get("shown_max", out["shown_max"])
    out["tries_max"] = limits.get("tries_max", out["tries_max"])

    out["timeout_steps"] = timings.get("timeout_steps", out["timeout_steps"])
    out["blink_steps"] = timings.get("cursor_blink_steps", out["blink_steps"])
    out["dots_step_steps"] = timings.get("dots_step_steps", out["dots_step_steps"])

    out["grid_cols"] = grid.get("cols", out["grid_cols"])
    out["grid_rows"] = grid.get("rows", out["grid_rows"])
    out["grid"] = list(grid.get("cells") or [])

    for key in ("prompt", "hint_keys", "hint_grid", "hint_voice", "hint_wait", "tries_note", "empty_note"):
        out[key] = strings.get(key, out[key])

    out["will_max"] = will.get("max", out["will_max"])
    out["will_label"] = will.get("label", out["will_label"])
    out["voice"] = voice
    out["doc"] = doc
    return out


def load_tape(root=ROOT):
    return load_json("data/talk_live_tape.json", root)


def font_glyphs(root=ROOT):
    """The sheet's alphabet, read out of pp_font.gml's own string so the test cannot pass against a stale copy."""
    with open(_path("game/scripts/pp_font/pp_font.gml", root), "r", encoding="utf-8") as handle:
        text = handle.read()
    match = re.search(r'function pp_font_glyphs\(\)\s*\{\s*return\s*"((?:[^"\\]|\\.)*)"\s*;', text)
    if not match:
        raise SystemExit("pp_font.gml: pp_font_glyphs() not found, so the alphabet cannot be measured")
    raw = match.group(1)
    return raw.replace('\\"', '"').replace("\\\\", "\\")


def normalise(text):
    """The tape's key: lower case, single spaces, no surrounding punctuation (the same rule as pp_talk_normalise)."""
    out = " ".join(str(text).strip().lower().split())
    while out:
        if out[0] in " .,:;!?'\"*":
            out = out[1:]
        else:
            break
    return out


def scrub(text, data, glyphs=None):
    """Everything a line must survive before it is a request: the sheet's alphabet and one space per run."""
    glyphs = font_glyphs() if glyphs is None else glyphs
    kept = "".join(ch for ch in str(text) if ch in glyphs)
    kept = " ".join(kept.split())
    return kept[: data["chars_max"]]


def rows_for(text, data):
    """The two row window, scrolled to the end of the line, cut at a space where there is one near the edge."""
    cols = data["cols"]
    cap = cols * max(1, data["rows_shown"])
    tail = text[-cap:] if len(text) > cap else text
    out = []
    rest = tail
    while len(rest) > cols:
        cut = _cut(rest, cols)
        out.append(cut)
        rest = rest[len(cut):]
        if rest.startswith(" "):
            rest = rest[1:]
    out.append(rest)
    while len(out) > max(1, data["rows_shown"]):
        out.pop(0)
    return out


def _cut(text, cols):
    """pp_talk_cut: cut to a column count at the last space, so a word is never split."""
    if len(text) <= cols:
        return text
    head = text[:cols]
    space = head.rfind(" ")
    return head[:space] if space > 0 else head


def verdict_effect(verdict):
    if verdict == "persuaded":
        return "soften"
    if verdict == "angered":
        return "setback"
    return "none"


def verdict_mood(verdict):
    if verdict == "persuaded":
        return "warm"
    if verdict == "angered":
        return "angry"
    return "guarded"


def answer_clean(doc, data, glyphs=None, miss=None):
    """One answer, checked the way pp_talk_live_answer_clean checks it. None means the whole answer is refused."""
    if not isinstance(doc, dict):
        return None
    if not isinstance(doc.get("will_delta"), int) or isinstance(doc.get("will_delta"), bool):
        return None
    verdict = doc.get("verdict")
    if verdict not in VERDICTS:
        verdict = "unmoved"
    reply = []
    for line in doc.get("reply") or []:
        if len(reply) >= 4:
            break
        line = str(line).strip()
        if not line:
            continue
        glyphs = font_glyphs() if glyphs is None else glyphs
        if any(ch not in glyphs for ch in line):
            continue
        if len(line) > 28:
            line = _cut(line, 28)
        reply.append(line)
    source = str(doc.get("source") or "unknown")
    if not reply:
        if miss is None:
            return None
        reply = list(miss.get("reply") or [])
        source = "fallback"
    return {
        "verdict": verdict,
        "will_delta": max(-20, min(20, int(doc["will_delta"]))),
        "mood": doc.get("mood") if doc.get("mood") in ("calm", "guarded", "rattled", "warm", "angry")
        else verdict_mood(verdict),
        "reply": reply,
        "source": source,
    }


def tape_lookup(tape, enemy, line):
    """The recorded answer for this line and enemy, or the miss row. Never returns None."""
    key = normalise(line)
    for row in tape.get("exchanges") or []:
        if row.get("enemy") != enemy:
            continue
        if normalise(row.get("line", "")) == key:
            return row.get("answer")
    return tape.get("miss") or {
        "verdict": "unmoved", "will_delta": 0, "reply": ["YOU ARE NOT ON", "THE LIST."],
        "source": "fallback", "mood": "guarded", "latency_ms": 0,
    }


class LiveTalk:
    """The box. Every mutation here has a line-for-line counterpart in pp_talk_live.gml, named in the docstring."""

    def __init__(self, data, tape, enemy="navy_sailor", mercy=0, mode=None):
        self.data = data
        self.tape = tape
        self.enemy = enemy
        self.will = max(0, min(100, mercy))
        self.mode = mode or data["mode_default"]
        self.stage = ""
        self.text = ""
        self.grid_mode = "keys"
        self.grid = 0
        self.tries = 0
        self.steps = 0
        self.source = ""
        self.verdict = "none"
        self.delta = 0
        self.reply = []
        self.note = ""
        self.missed = False
        self.sent = []          # every line that reached the "bridge", so a test can count them
        self.would_send = False
        self.deferred = None
        self.deferred_steps = 0

    # -- the box ---------------------------------------------------------
    def tries_left(self):
        return max(0, self.data["tries_max"] - self.tries)

    def open(self):
        """pp_talk_live_open. False when the tries are spent, with the note the game shows."""
        if self.tries_left() <= 0:
            self.note = self.data["tries_note"]
            return False
        self.stage = "entry"
        self.text = ""
        self.grid_mode = "keys"
        self.grid = self.index_of("END")
        self.steps = 0
        self.note = ""
        return True

    def close(self):
        """pp_talk_live_close."""
        self.stage = ""
        self.text = ""
        self.deferred = None
        self.deferred_steps = 0

    def type_line(self, text):
        """The characters one at a time, through the same filter pp_talk_live_typed applies."""
        glyphs = font_glyphs()
        for ch in text:
            if ch not in glyphs:
                continue
            if len(self.text) >= self.data["chars_max"]:
                break
            self.text += ch
        return self.text

    def delete(self):
        """pp_talk_live_delete."""
        if not self.text:
            return False
        self.text = self.text[:-1]
        return True

    def record(self, steps):
        """The voice key goes down: pp_talk_live_step_listen's listen stage, counting the steps it was held.

        The count is what the floor is measured against, which is the whole reason the stage exists: a brush past the
        key must never become a request. Nothing here reads a microphone; the steps and the transcript are the tape's.
        """
        if self.stage != "entry":
            return False
        self.stage = "listen"
        self.voice_steps = max(0, int(steps))
        return True

    def voice_release(self, transcript=None):
        """The voice key comes up: under the floor the take is refused with the note, at or over it the transcript lands.

        pp_talk_live_send_hear assigns the buffer (`_battle.live_text = _hear`), so a take replaces the line rather
        than appending to it, and the player edits it in the same box the keyboard fills.
        """
        if self.stage != "listen":
            return False
        steps = getattr(self, "voice_steps", 0)
        self.stage = "entry"
        if steps < int(self.data["voice"].get("hold_steps_min", 15)) or not transcript:
            self.note = self.data["empty_note"]
            return False
        self.text = ""
        self.type_line(transcript)
        return True

    def submit(self):
        """pp_talk_live_submit. False when the line is empty or the box is not open."""
        if self.stage not in ("entry",):
            return False
        line = scrub(self.text, self.data)
        if not line:
            self.note = self.data["empty_note"]
            return False
        self.text = line
        self.tries += 1
        self.steps = 0
        self.stage = "wait"
        self.note = ""
        self.sent.append(line)
        # The mirror never opens a socket in any mode, and it says so in one place instead of pretending to be a
        # second client. In replay (the game's default) this flag stays False, which is the thing the test measures.
        self.would_send = (self.mode == "live")
        if self.mode == "live":
            self.stage = "wait"
            self.deferred = None
            return True
        answer = tape_lookup(self.tape, self.enemy, line)
        wait = 6
        if isinstance(answer, dict) and isinstance(answer.get("latency_ms"), int):
            wait = max(6, min(120, round(answer["latency_ms"] / 1000 * 60)))
        self.deferred = answer
        self.deferred_steps = wait
        return True

    # -- the grid --------------------------------------------------------
    def index_of(self, cell):
        try:
            return list(self.data["grid"]).index(cell)
        except ValueError:
            return -1

    def cell(self):
        grid = self.data["grid"]
        if not grid:
            return ""
        return grid[max(0, min(self.grid, len(grid) - 1))]

    def grid_move(self, dx=0, dy=0):
        """pp_talk_live_step_grid's cursor: wrap on both axes, clamped to the last cell."""
        grid = self.data["grid"]
        if not grid:
            return self.grid
        cols = max(1, self.data["grid_cols"])
        rows = max(1, self.data["grid_rows"])
        col = (self.grid % cols + dx + cols) % cols
        row = (self.grid // cols + dy + rows) % rows
        nxt = row * cols + col
        self.grid = min(nxt, len(grid) - 1)
        return self.grid

    def grid_press(self):
        """One confirm on the grid: DEL deletes, END submits, anything else types that cell."""
        cell = self.cell()
        if cell == "DEL":
            return self.delete()
        if cell == "END":
            return self.submit()
        return bool(self.type_line(cell))

    # -- the answer ------------------------------------------------------
    def step(self):
        """One step of the wait stage: the deferred answer lands, or the timeout's fallback does."""
        if self.stage != "wait":
            return None
        self.steps += 1
        if self.deferred is not None:
            if self.steps >= self.deferred_steps:
                answer = self.deferred
                self.deferred = None
                self.deferred_steps = 0
                return self.apply(answer, via="replay")
            return None
        if self.steps >= self.data["timeout_steps"]:
            self.missed = True
            return self.apply(tape_lookup(self.tape, self.enemy, "\x00 never recorded"), via="timeout")
        return None

    def apply(self, doc, via="replay"):
        """pp_talk_live_answer: validate, clamp, move the meter, hand the reply on. The only state change."""
        answer = answer_clean(doc, self.data, miss=self.tape.get("miss"))
        if answer is None:
            answer = answer_clean(self.tape.get("miss"), self.data)
            via = "fallback"
        if answer is None:
            self.close()
            return None
        before = self.will
        self.will = max(0, min(self.data["will_max"], before + answer["will_delta"]))
        self.delta = self.will - before
        self.verdict = answer["verdict"]
        self.source = answer["source"]
        self.reply = list(answer["reply"])
        self.stage = ""
        self.via = via
        return answer

    def dots(self):
        """pp_talk_live_dots: one, two then three dots, never a spinner."""
        n = min(3, 1 + max(0, self.steps) // max(1, self.data["dots_step_steps"]))
        return "*" + " ." * n

    def view_rows(self):
        return rows_for(self.text, self.data)
