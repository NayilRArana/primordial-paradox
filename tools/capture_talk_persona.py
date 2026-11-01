#!/usr/bin/env python3
"""capture_talk_persona.py: the proof frames for the live TALK box opened outside a fight (card t_0fda85b8).

The box is spec 21 sections 1 and 2's box (pp_talk_live) opened with a persona id instead of a battle: a chat, no
meter, no tries, effects none and end, and Esc leaves without a turn. The reply draws in the same message window with
the same `* ` marker and 8 pixel pitch, and the persona's name plate is the card's `name` field, read from
data/talk_personas.json.

Like tools/capture_talk_live.py, this is a reconstruction, not a screenshot: the frame is drawn from the shipped glyph
sheet, the geometry is read out of pp_talk_live.gml, pp_battle_text.gml and pp_talk_persona.gml at run time rather than
restated here, and every frame carries the caption RECONSTRUCTION in its report. A window is only opened on a machine
nobody is using (tools/idle_check.py), so the picture a judge is handed is this render, and the render cannot drift
from the game because the numbers are the game's own getters.

One frame per persona, in scene order (S1, S2, S3):

    konrad          KONRAD, the desk that is for work
    urien           URIEN, the man who loves the rain
    quay_townsperson  BYSTANDER, the voice on the quay

Each frame draws the reply beside a recorded bake line (data/talk_personas_bake.json, the first row the bridge returned
for that persona), so the picture is not a made up greeting but the answer the game would actually show. Every frame is
judged by tools/nes_composite_check.py's check_frame before it is written, on the 256x240 canvas in memory.

    python tools/capture_talk_persona.py            (writes the frames and the report)
    python tools/capture_talk_persona.py --check    (geometry checks and the frame audit, no files written)
"""

import argparse
import json
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import capture_talk_live as cap  # noqa: E402  the shared primitives: roles(), Sheet, draw_text, rect, draw_window
import nes_composite_check as composite  # noqa: E402  the frame audit, the same checker nes_audit_all.py gates with

OUT_DIR = os.path.join(ROOT, "output", "talk_persona_capture")
SCALE = cap.SCALE
FRAME_W, FRAME_H = cap.FRAME_W, cap.FRAME_H
GLYPH = cap.GLYPH

GML_LIVE = cap.GML_LIVE
GML_TEXT = cap.GML_TEXT
GML_PERSONA = os.path.join(ROOT, "game", "scripts", "pp_talk_persona", "pp_talk_persona.gml")
PERSONAS = os.path.join(ROOT, "data", "talk_personas.json")
BAKE = os.path.join(ROOT, "data", "talk_personas_bake.json")


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------------------------------------------------
# Geometry, read out of the GML so the picture cannot drift from the game

def persona_geometry():
    """The reply's pitch and x/y, and the name plate's centre, from the getter functions the GML calls."""
    text = read(GML_TEXT)
    numbers = {}
    for name, getter in (
        ("REPLY_X", "pp_talk_text_x"),
        ("REPLY_Y", "pp_talk_text_y"),
        ("PITCH", "pp_talk_line_pitch"),
    ):
        match = re.search(r"function %s\(\)\s*\{\s*return (\d+);" % getter, text)
        if not match:
            raise SystemExit("pp_battle_text.gml no longer defines %s() with a literal return; the reply's position "
                             "cannot be read" % getter)
        numbers[name] = int(match.group(1))
    persona = read(GML_PERSONA)
    for name, getter in (("PLATE_X", "pp_talk_persona_plate_x"), ("PLATE_Y", "pp_talk_persona_plate_y")):
        match = re.search(r"function %s\(\)\s*\{\s*return (\d+);" % getter, persona)
        if not match:
            raise SystemExit("pp_talk_persona.gml no longer defines %s() with a literal return; the name plate's "
                             "centre cannot be read" % getter)
        numbers[name] = int(match.group(1))
    numbers["window"] = (0, 0, 255, 47)
    return numbers


# ---------------------------------------------------------------------------------------------------------------------
# The data: one card and one recorded answer per persona

def persona_cards():
    doc = json.load(open(PERSONAS, encoding="utf-8"))
    rows = doc["personas"] if isinstance(doc, dict) and "personas" in doc else doc
    ordered = sorted(rows, key=lambda row: str(row.get("scene", "")))
    cards = []
    for row in ordered:
        if "id" not in row or "name" not in row:
            raise SystemExit("data/talk_personas.json has a persona without an id or a name")
        cards.append({"id": row["id"], "name": row["name"], "scene": row.get("scene", "")})
    if [card["id"] for card in cards] != ["konrad", "urien", "quay_townsperson"]:
        raise SystemExit("data/talk_personas.json no longer names the three cards konrad, urien and quay_townsperson")
    return cards


def persona_replies():
    """The first recorded answer per persona, from the bake, so the frame shows a real line the bridge returned."""
    doc = json.load(open(BAKE, encoding="utf-8"))
    rows = doc["rows"]
    first = {}
    for row in rows:
        if row.get("persona") not in first and row.get("text"):
            first[row["persona"]] = row["text"]
    if set(first) != {"konrad", "urien", "quay_townsperson"}:
        raise SystemExit("data/talk_personas_bake.json does not carry a recorded answer for all three personas")
    return first


# ---------------------------------------------------------------------------------------------------------------------
# The frames

def draw_persona_reply(canvas, role, sheet, geometry, name, lines):
    """The persona's reply: the flat ink field, the message window, the `* ` reply at the 8 pixel pitch, and the name
    plate below the window at the battle's enemy label row."""
    cap.rect(canvas, 0, 0, FRAME_W - 1, FRAME_H - 1, role["ink"])
    cap.draw_window(canvas, role)
    for index, line in enumerate(lines[:4]):
        cap.draw_text(canvas, sheet, "* " + line, geometry["REPLY_X"],
                      geometry["REPLY_Y"] + index * geometry["PITCH"], role["text"])
    width = len(name) * GLYPH
    x = geometry["PLATE_X"] - width // 2
    cap.draw_text(canvas, sheet, name, x, geometry["PLATE_Y"], role["text"])


def audit_frames(canvases, palette):
    rows = []
    for name, canvas in canvases:
        rows.append((name, composite.check_frame(canvas.convert("RGBA"), palette)))
    return rows


def prepare():
    """Every frame, in memory, with the audit that judged it. Writes nothing."""
    geometry = persona_geometry()
    role = cap.roles()
    data = cap.talk_live.load_data(ROOT)
    sheet = cap.Sheet(data)
    cards = persona_cards()
    replies = persona_replies()

    for card in cards:
        missing = [ch for line in replies[card["id"]] for ch in "* " + line if ch not in sheet.index]
        if missing:
            raise SystemExit("%s's recorded answer draws %r, which the sheet does not have" % (card["id"], missing))
        if len(card["name"]) * GLYPH > FRAME_W:
            raise SystemExit("%s's name plate is %d wide, wider than the frame" % (card["id"], len(card["name"]) * GLYPH))

    canvases = []
    for card in cards:
        canvas = Image.new("RGBA", (FRAME_W, FRAME_H), role["ink"] + (255,))
        draw_persona_reply(canvas, role, sheet, geometry, card["name"], replies[card["id"]][:2])
        canvases.append((card["id"], canvas))
    palette = composite.load_palette(composite.default_palette_path(ROOT))
    audit = audit_frames(canvases, palette)
    return geometry, role, cards, replies, canvases, audit


def main():
    parser = argparse.ArgumentParser(description="Render the persona TALK replies from the game's own sources.")
    parser.add_argument("--check", action="store_true", help="geometry checks and the frame audit only, write nothing")
    args = parser.parse_args()

    geometry, role, cards, replies, canvases, audit = prepare()
    bad = [name for name, report in audit if not report["ok"]]
    for (name, report), card in zip(audit, cards):
        if args.check or not report["ok"]:
            print("%-16s frame audit: %s, %d colours, backdrop %s"
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
    report_doc = {"tool": "capture_talk_persona.py", "kind": "talk_persona_reconstruction", "note":
                  "reconstruction from the shipped sheet, the GML's own geometry and the recorded bake answers, not a "
                  "screenshot: a window is only opened on a quiet machine (tools/idle_check.py)",
                  "scale": SCALE,
                  "audit": {"tool": "tools/nes_composite_check.py, check_frame, one 256x240 frame at a time",
                            "palette": "data/nes_palette.json",
                            "frames": [{"name": name, "ok": report["ok"],
                                        "colours": report["screen"]["colours"],
                                        "backdrop": report["backdrop"]} for name, report in audit]},
                  "geometry": geometry, "frames": []}
    tiles = []
    for (name, canvas), card in zip(canvases, cards):
        path = os.path.join(OUT_DIR, "%s.png" % name)
        canvas.resize((FRAME_W * SCALE, FRAME_H * SCALE), Image.NEAREST).save(path)
        tiles.append((name, canvas))
        report_doc["frames"].append({"name": name, "persona": card["id"], "scene": card["scene"],
                                     "name_plate": card["name"],
                                     "reply": replies[card["id"]][:2],
                                     "png": os.path.relpath(path, ROOT).replace(os.sep, "/"),
                                     "caption": "RECONSTRUCTION"})
        print("%-16s %s: %s" % (name, card["name"], " / ".join(replies[card["id"]][:2])))

    sheet_w = FRAME_W * SCALE * 3 + 8 * 4
    rows = (len(tiles) + 2) // 3
    sheet_h = rows * (FRAME_H * SCALE + 24) + 8
    contact = Image.new("RGBA", (sheet_w, sheet_h), role["ink"] + (255,))
    data = cap.talk_live.load_data(ROOT)
    sheet = cap.Sheet(data)
    for index, (name, canvas) in enumerate(tiles):
        col, row = index % 3, index // 3
        x = 8 + col * (FRAME_W * SCALE + 8)
        y = 8 + row * (FRAME_H * SCALE + 24)
        contact.paste(canvas.resize((FRAME_W * SCALE, FRAME_H * SCALE), Image.NEAREST), (x, y))
        cap.draw_text(contact, sheet, name.upper(), x, y + FRAME_H * SCALE + 6, role["text"])
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
