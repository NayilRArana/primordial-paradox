#!/usr/bin/env python3
"""check_credits.py: prove data/credits.json parses, fits the font and runs for both variants (card CREDITS).

It mirrors game/scripts/pp_credits/pp_credits.gml in data: the same row layout, the same scroll end, the same
phase lengths. Checks: every printed character is a glyph of pp_font_glyphs(), every row is at most roll.max_chars
long, no dash characters, the Meta models are the ones the repo evidences (meta_bake.json and tools/models_used.py),
no bot or setup names, both variants have a closing block and a registered music cue, and the roll ends.

Usage:
    python tools/check_credits.py             check, print one line per variant, exit 1 on any problem
    python tools/check_credits.py --preview DIR   also write a tall PNG of each variant's roll into DIR
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDITS = os.path.join(ROOT, "data", "credits.json")
FONT_GML = os.path.join(ROOT, "game", "scripts", "pp_font", "pp_font.gml")
TITLE_GML = os.path.join(ROOT, "game", "scripts", "pp_title", "pp_title.gml")
FRAME_W, FRAME_H = 256, 240
STYLES = {"title", "heading", "text", "gap"}
VARIANTS = ("spare", "kill")
# Names of tools, bots and providers the credits must not reveal (the setup stays private).
BANNED = ("hermes", "demiurge", "claude", "anthropic", "codex", "openai", "gpt", "deepseek", "qwen", "opencode",
          "gemini", "kaggle", "colab", "raspberry", "kanban", "arananet", "orchestr", "manager", "worker", "lane")


def load(path=CREDITS):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def font_glyphs():
    with open(FONT_GML, "r", encoding="utf-8-sig") as handle:
        source = handle.read()
    body = re.search(r"function\s+pp_font_glyphs\s*\(\s*\)\s*\{(.*?)\n\}", source, re.S).group(1)
    raw = re.search(r'return\s+"((?:[^"\\]|\\.)*)"\s*;', body).group(1)
    return raw.replace('\\"', '"').replace("\\\\", "\\")


def title_copyright():
    with open(TITLE_GML, "r", encoding="utf-8-sig") as handle:
        return re.search(r'#macro PP_TITLE_COPY_TEXT "([^"]*)"', handle.read()).group(1)


def blocks(data, variant):
    roll = data["roll"]
    out = list(roll["sections"])
    closing = roll["variants"][variant].get("closing")
    if closing:
        out.append(closing)
    return out


def layout(data, variant):
    """Rows as (y, text, style) and the roll height, exactly as pp_credits_build_rows does."""
    roll = data["roll"]
    rows, y = [], 0
    for block in blocks(data, variant):
        if rows:
            y += roll["section_gap_rows"] * roll["line_h"]
        for row in block["rows"]:
            style = row.get("style", "text")
            if style == "gap":
                y += roll["line_h"]
                continue
            rows.append((y, row.get("text", ""), style))
            y += roll["head_h"] if style in ("heading", "title") else roll["line_h"]
    return rows, y


def timing(data, variant):
    """(scroll_end, total_steps) as the state machine runs: lead in, roll, hold, leave."""
    roll = data["roll"]
    rows, _height = layout(data, variant)
    scroll_end = max(0, FRAME_H + rows[-1][0] - 112)
    roll_steps = int(-(-scroll_end // roll["speed"]))
    return scroll_end, roll["lead_in_steps"] + roll_steps + roll["hold_steps"] + roll["leave_steps"]


def cue_ids():
    with open(os.path.join(ROOT, "data", "audio.json"), "r", encoding="utf-8") as handle:
        return {cue["id"] for cue in json.load(handle)["cues"]}


def evidenced_models():
    ids = set()
    with open(os.path.join(ROOT, "data", "meta_bake.json"), "r", encoding="utf-8") as handle:
        ids.add(json.load(handle)["bake"]["model"])
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import models_used
    ids.update(row["model"] for row in models_used.REGISTER)
    return ids


def check(data=None):
    data = data or load()
    problems = []
    roll = data.get("roll")
    if not isinstance(roll, dict):
        return ["roll is missing"]
    glyphs = set(font_glyphs())
    limit = roll["max_chars"]
    texts = []
    for variant in VARIANTS:
        if variant not in roll.get("variants", {}):
            problems.append("variant %s is missing" % variant)
            continue
        vrow = roll["variants"][variant]
        if not vrow.get("closing", {}).get("rows"):
            problems.append("variant %s has no closing rows" % variant)
        for key in ("music_cue", "music_fallback"):
            if vrow.get(key) not in cue_ids():
                problems.append("variant %s %s %r is not registered in data/audio.json" % (variant, key, vrow.get(key)))
        for block in blocks(data, variant):
            for row in block["rows"]:
                if row.get("style", "text") not in STYLES:
                    problems.append("bad style %r" % row.get("style"))
                texts.append(row.get("text", ""))
        rows, _h = layout(data, variant)
        _end, total = timing(data, variant)
        if not 1800 <= total <= 9000:
            problems.append("variant %s runs %d steps, outside 30 s to 150 s" % (variant, total))
    for text in set(texts):
        bad = sorted({c for c in text if c not in glyphs})
        if bad:
            problems.append("%r has characters with no glyph: %r" % (text, bad))
        if len(text) > limit:
            problems.append("%r is %d characters, the limit is %d" % (text, len(text), limit))
        if any(ch in text for ch in map(chr, (0x2012, 0x2013, 0x2014, 0x2015))):
            problems.append("%r holds a dash character" % text)
        low = text.lower()
        for word in BANNED:
            if word in low:
                problems.append("%r names %r, which the credits must not reveal" % (text, word))
    models = evidenced_models()
    shown = " ".join(texts)
    for entry in roll.get("models", []):
        if entry["model_id"] not in models:
            problems.append("model %s is not evidenced by meta_bake.json or models_used.py" % entry["model_id"])
        if entry["display"] != entry["model_id"].upper().replace("-", " "):
            problems.append("display %r is not derived from %s" % (entry["display"], entry["model_id"]))
        if entry["display"] not in shown:
            problems.append("model %s is declared but not on the roll" % entry["display"])
    for token in re.findall(r"\b(?:MUSE|SAM) [A-Z]*\s?\d+\.\d+", shown):
        if token not in {e["display"] for e in roll.get("models", [])}:
            problems.append("the roll prints a model name %r that is not in roll.models" % token)
    if title_copyright().lower().find("nayilinist") < 0 or "NAYILINIST" not in shown:
        problems.append("the roll does not name the author as the title screen does")
    return problems


def preview(data, variant, out_dir):
    from PIL import Image
    sheet = Image.open(os.path.join(ROOT, "game", "sprites_src", "title", "spr_pp_font8.png")).convert("RGBA")
    glyphs = font_glyphs()
    rows, height = layout(data, variant)
    img = Image.new("RGB", (FRAME_W, height + 40), (0, 0, 0))
    for y, text, style in rows:
        x0 = FRAME_W // 2 - (len(text) * 8) // 2
        for i, ch in enumerate(text):
            g = glyphs.find(ch)
            if g >= 0:
                img.paste(sheet.crop((g * 8, 0, g * 8 + 8, 8)), (x0 + i * 8, y + 20), sheet.crop((g * 8, 0, g * 8 + 8, 8)))
        half = min(120, len(text) * 4 + 8)
        rules = {"title": (-4, 11), "heading": (10,)}.get(style, ())
        for r in rules:
            for x in range(128 - half, 128 + half):
                img.putpixel((x, y + 20 + r), (0, 88, 0))
    path = os.path.join(out_dir, "credits_roll_%s.png" % variant)
    img.save(path)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", metavar="DIR")
    args = parser.parse_args()
    data = load()
    problems = check(data)
    for variant in VARIANTS:
        if variant in data["roll"].get("variants", {}):
            rows, height = layout(data, variant)
            end, total = timing(data, variant)
            print("%s: %d rows, height %d px, scroll end %d, %d steps (%.0f s)" % (variant, len(rows), height, end, total, total / 60))
            if args.preview:
                os.makedirs(args.preview, exist_ok=True)
                print("preview", preview(data, variant, args.preview))
    for problem in problems:
        print("FAIL", problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
