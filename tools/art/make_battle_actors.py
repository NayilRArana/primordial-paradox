#!/usr/bin/env python3
"""make_battle_actors.py: the big battle sprites (Morgan, the Navy sailor, Percy Skye), the HUD swatch atlas and the
battle_b layout row, for the 2026-11-01 battle screen redesign.

    game/sprites_src/enemies/morgan_big.png       64x80, 3 frames: idle0, idle1, hit   (Royal Navy dock checkpoint man)
    game/sprites_src/enemies/navy_sailor_big.png  64x80, 3 frames                      (deck watch, with a mop)
    game/sprites_src/enemies/percy_big.png        64x80, 3 frames                      (Lieutenant Percy Skye, 23)
    game/sprites_src/bg/bg_battle_hud.png         12 flat 16x16 swatches the HUD bars are cut from
    data/ui_layouts.json                          top level key "battle_b" (one geometry for the GML and the offline renderer)

Style: chunky 2C02 pixel figures, 1 pixel black outline added by code around the silhouette, no gradients, at most 3
opaque colours per 8x8 tile (cap_tiles), original drawing. The hit frame leans the figure back, squeezes the eyes and
adds impact sparks; the idle pair is a one pixel breath.

Usage:  python tools/art/make_battle_actors.py
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from battle_art import *  # noqa: E402,F401,F403
import battle_art as B  # noqa: E402

FW, FH = 64, 80
ENEMY_DIR = os.path.join(ROOT, "game", "sprites_src", "enemies")
BG_DIR = os.path.join(ROOT, "game", "sprites_src", "bg")
OUT = os.path.join(ROOT, "output", "battle_visuals_2026-11-01", "actors")


def head(c, s, hurt):
    sk = s["skin"]
    c.rect(28, 40, 36, 46, sk)
    c.ellipse(32, 29, 14, 12, sk)
    c.rect(17, 28, 18, 33, sk)
    c.rect(46, 28, 47, 33, sk)
    if s.get("hair"):
        c.rect(18, 24, 19, 33, s["hair"])
        c.rect(45, 24, 46, 33, s["hair"])
    c.ellipse(32, 18, 17, 9, s["cap"])
    c.rect(15, s["band_y0"], 49, s["band_y1"], s["band"])
    c.rect(13, s["band_y1"] + 1, 51, s["band_y1"] + 3, s["peak"])
    if s.get("badge"):
        c.rect(30, s["band_y0"], 34, s["band_y1"], s["badge"])
    c.rect(14, s["band_y1"] + 4, 50, s["band_y1"] + 4, K)
    if hurt:
        for (x, y) in ((24, 32), (25, 33), (26, 34), (25, 35), (24, 36), (40, 32), (39, 33), (38, 34), (39, 35), (40, 36)):
            c.put(x, y, K)
        c.ellipse(32, 39, 3, 2, K)
    else:
        c.rect(24, 32, 26, 35, K)
        c.rect(38, 32, 40, 35, K)
        c.rect(23, 30, 27, 30, K)
        c.rect(37, 30, 41, 30, K)
        c.rect(31, 36, 32, 37, K)
        c.rect(29, 40, 35, 40, K)


def morgan(pose):
    s = dict(skin=CRE, cap=WHT, band=K, band_y0=21, band_y1=24, peak=K, hair=None, badge=None)
    c = Canvas(FW, FH, T)
    c.rect(19, 66, 30, 77, BLU)
    c.rect(34, 66, 45, 77, BLU)
    c.rect(17, 75, 30, 79, K)
    c.rect(34, 75, 47, 79, K)
    c.rect(15, 49, 49, 68, BLU)
    c.ellipse(32, 49, 17, 5, BLU)
    c.rect(7, 50, 14, 67, BLU)
    c.rect(7, 64, 14, 66, WHT)
    c.ellipse(10, 69, 4, 3, CRE)
    c.rect(50, 50, 57, 62, BLU)
    head(c, s, pose == "hit")
    c.rect(26, 37, 38, 38, K)
    c.poly([(25, 47), (39, 47), (32, 58)], WHT)
    for bx in (25, 37):
        c.rect(bx, 60, bx + 2, 62, WHT)
        c.rect(bx, 65, bx + 2, 67, WHT)
    c.rect(15, 68, 49, 68, K)
    c.rect(52, 42, 62, 60, CRE)
    c.frame(52, 42, 62, 60, K)
    c.rect(55, 40, 59, 43, BRN)
    for y in (47, 51, 55):
        c.rect(54, y, 60, y, K)
    c.ellipse(53, 60, 3, 3, CRE)
    return c.a


def sailor(pose):
    s = dict(skin=CRE, cap=WHT, band=K, band_y0=22, band_y1=23, peak=WHT, hair=None, badge=None)
    c = Canvas(FW, FH, T)
    c.rect(18, 66, 31, 77, WHT)
    c.rect(33, 66, 46, 77, WHT)
    c.rect(16, 75, 31, 79, K)
    c.rect(33, 75, 48, 79, K)
    c.rect(15, 49, 49, 68, WHT)
    c.ellipse(32, 49, 17, 5, WHT)
    c.poly([(15, 49), (49, 49), (45, 60), (32, 66), (19, 60)], BLU)
    c.poly([(26, 49), (38, 49), (32, 59)], CRE)
    c.line(17, 51, 30, 62, WHT)
    c.line(47, 51, 34, 62, WHT)
    c.poly([(29, 58), (35, 58), (32, 64)], BLU)
    c.rect(7, 50, 14, 67, WHT)
    c.rect(7, 63, 14, 65, BLU)
    c.ellipse(10, 69, 4, 3, CRE)
    c.rect(50, 50, 57, 60, WHT)
    c.rect(50, 57, 57, 58, BLU)
    c.rect(55, 18, 56, 76, BRN)
    head(c, s, pose == "hit")
    c.ellipse(55, 58, 3, 3, CRE)
    c.ellipse(56, 74, 7, 5, WHT)
    for x in (52, 56, 60):
        c.rect(x, 72, x, 78, K)
    return c.a


def percy(pose):
    s = dict(skin=CRE, cap=WHT, band=K, band_y0=21, band_y1=24, peak=K, hair=BRN, badge=GLD)
    c = Canvas(FW, FH, T)
    c.rect(19, 66, 30, 77, BLU)
    c.rect(34, 66, 45, 77, BLU)
    c.rect(17, 75, 30, 79, K)
    c.rect(34, 75, 47, 79, K)
    c.rect(14, 49, 50, 68, BLU)
    c.ellipse(32, 49, 18, 5, BLU)
    c.rect(6, 50, 13, 67, BLU)
    c.rect(6, 62, 13, 63, GLD)
    c.rect(6, 65, 13, 66, GLD)
    c.ellipse(9, 69, 4, 3, WHT)
    c.rect(51, 50, 58, 62, BLU)
    c.rect(51, 58, 58, 59, GLD)
    c.line(14, 62, 6, 77, BRN, 2)
    c.rect(11, 58, 18, 60, GLD)
    head(c, s, pose == "hit")
    c.poly([(25, 47), (39, 47), (32, 57)], WHT)
    c.rect(31, 50, 33, 58, K)
    c.line(26, 47, 22, 60, K)
    c.line(38, 47, 42, 60, K)
    for bx in (23, 40):
        c.rect(bx, 60, bx + 2, 62, GLD)
        c.rect(bx, 65, bx + 2, 67, GLD)
    c.rect(9, 48, 19, 51, GLD)
    c.rect(45, 48, 55, 51, GLD)
    c.rect(14, 68, 50, 68, K)
    c.line(56, 61, 62, 38, BRN, 3)
    c.rect(59, 46, 62, 47, GLD)
    c.rect(60, 36, 63, 39, GLD)
    c.ellipse(56, 62, 3, 3, WHT)
    return c.a


def bob(f):
    b = np.full_like(f, T)
    b[1:67] = f[0:66]
    b[67:] = f[67:]
    return b


def shear(f, k=5):
    out = np.full_like(f, T)
    for y in range(FH):
        dx = int(round(k * (FH - 1 - y) / float(FH - 1)))
        if dx > 0:
            out[y, dx:] = f[y, :FW - dx]
        else:
            out[y] = f[y]
    return out


def spark(a, x, y):
    for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-2, 0), (2, 0), (0, -2), (0, 2)):
        if 0 <= x + dx < FW and 0 <= y + dy < FH and a[y + dy, x + dx] == T:
            a[y + dy, x + dx] = WHT


def frames(builder):
    out = []
    f0 = builder("idle")
    for i, f in enumerate((f0, bob(f0), shear(builder("hit")))):
        a = B.outline(f)
        if i == 2:
            for (x, y) in ((54, 12), (59, 24), (6, 14), (3, 26), (57, 38)):
                spark(a, x, y)
        a, _ = B.cap_tiles(a)
        out.append(a)
    return out


ENEMIES = (
    ("morgan", "Morgan, Royal Navy dock checkpoint man: white cap, navy coat, clipboard", morgan),
    ("navy_sailor", "Navy Sailor on deck watch: dixie cap, sailor collar, mop", sailor),
    ("percy", "Lieutenant Percy Skye, 23, Royal Navy: officer's cap, gold buttons and cuffs, spyglass, sabre", percy),
)


def build_enemies():
    os.makedirs(OUT, exist_ok=True)
    report = []
    sheets = []
    for name, note, builder in ENEMIES:
        fr = frames(builder)
        sheet = np.full((FH, FW * 3), T, dtype=np.uint8)
        for i, f in enumerate(fr):
            sheet[:, i * FW:(i + 1) * FW] = f
        bad = B.audit_tiles(sheet)
        used = colours_used(sheet)
        report.append("%-12s colours %s  tile violations %d" % (name, ["%02X" % u for u in used], len(bad)))
        img = to_image(sheet)
        img.save(os.path.join(ENEMY_DIR, name + "_big.png"))
        side = {
            "name": name + "_big", "frame_w": FW, "frame_h": FH, "frames": 3, "fps": 2.0,
            "frame_names": ["idle0", "idle1", "hit"], "hit_frame": 2, "anchor": "bottom_centre",
            "palette_entries": used, "sprite": name, "note": note + ". Generated by tools/art/make_battle_actors.py."}
        with open(os.path.join(ENEMY_DIR, name + "_big.json"), "w", encoding="utf-8", newline="\n") as handle:
            json.dump(side, handle, indent=2)
            handle.write("\n")
        sheets.append(img)
    contact = Image.new("RGBA", (FW * 3 * 3 + 20, FH * 3 * 3 + 20), (60, 60, 70, 255))
    for r, img in enumerate(sheets):
        big = img.resize((img.width * 3, img.height * 3), Image.NEAREST)
        contact.alpha_composite(big, (4, 4 + r * (FH * 3 + 4)))
    contact.convert("RGB").save(os.path.join(OUT, "enemies_3x.png"))
    return report


HUD_SWATCHES = [K, GRY, 0x1A, 0x2A, RED, 0x26, AZU, LBL, PNK, 0x35, GLD, WHT]


def build_hud():
    a = np.zeros((16, 16 * len(HUD_SWATCHES)), dtype=np.uint8)
    for i, col in enumerate(HUD_SWATCHES):
        a[:, i * 16:(i + 1) * 16] = col
    to_image(a).convert("RGB").save(os.path.join(BG_DIR, "bg_battle_hud.png"))
    side = {"name": "bg_battle_hud", "kind": "ui_atlas", "frame_w": 16, "frame_h": 16, "frames": len(HUD_SWATCHES),
            "fps": 0.0, "backdrop": {"index": 15, "hex": "#000000"},
            "swatches": ["k", "grey", "hp", "hp_hi", "low", "low_hi", "will", "will_hi", "mercy", "mercy_hi", "gold", "white"],
            "entries": HUD_SWATCHES,
            "note": "flat 16x16 cells; the director cuts one pixel out of a cell and stretches it, so a bar is exact art colour."}
    with open(os.path.join(BG_DIR, "bg_battle_hud.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(side, handle, indent=2)
        handle.write("\n")


LAYOUT_B = {
    "name": "battle_b",
    "note": "NES style B battle screen, 2026-11-01. The one geometry for pp_battle_director.gml and tools/render_battle_visuals.py.",
    "scene": {"x": 0, "y": 0, "w": 256, "h": 168},
    "enemy": {"cx": 168, "feet": 112, "frame_w": 64, "frame_h": 80, "suffix": "_big"},
    "plate": {"x": 128, "y": 8, "w": 15, "h": 4, "name_y": 12, "hp_y": 21, "mercy_y": 29,
              "label_x": 136, "bar_x": 184, "bar_w": 56, "bar_h": 6},
    "panel": {"x": 8, "y": 120, "w": 30, "h": 5, "party_x": 16, "party_step": 30, "party_y": 124, "rule_x": 136,
              "stat_x": 144, "hp_y": 124, "hp_bar_y": 133, "will_y": 141, "will_bar_y": 150, "bar_w": 96, "bar_h": 6},
    "message": {"x": 0, "y": 0, "w": 32, "h": 6},
    "command": {"x": 8, "y": 168, "w": 30, "h": 8},
    "timing": {"x": 40, "y": 8, "w": 22, "h": 4, "bar_x": 56, "bar_y": 17, "bar_w": 160, "bar_h": 7},
    "victory": {"x": 32, "y": 88, "w": 24, "h": 8, "title_y": 100, "word_y": 112, "press_y": 126},
    "swatches": {"sprite": "bg_battle_hud", "cell": 16, "k": 0, "grey": 1, "hp": 2, "hp_hi": 3, "low": 4, "low_hi": 5,
                 "will": 6, "will_hi": 7, "mercy": 8, "mercy_hi": 9, "gold": 10, "white": 11},
}


def _span(text, pos):
    """The (start, end) of the screens-array object that contains pos, found with a string aware bracket walk."""
    i = text.index('"screens"')
    j = text.index("[", i)
    depth, in_str, esc, start = 0, False, False, None
    for k in range(j, len(text)):
        ch = text[k]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            depth += 1
            if ch == "{" and depth == 2:
                start = k
        elif ch in "}]":
            if ch == "}" and depth == 2 and start is not None and start <= pos <= k:
                return start, k + 1
            depth -= 1
            if depth == 0:
                return None
    return None


def _match_brace(text, start):
    """Index of the } that closes the { at start, string aware."""
    depth, in_str, esc = 0, False, False
    for k in range(start, len(text)):
        ch = text[k]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return k
    raise ValueError("unbalanced braces")


def write_layout():
    """Put LAYOUT_B in data/ui_layouts.json as the top level key battle_b. It is not a fourth entry of "screens",
    because the UI gate (tools/check_ui_nes.py) counts exactly three screens. Idempotent."""
    path = os.path.join(ROOT, "data", "ui_layouts.json")
    with open(path, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    text = text.replace("\r\n", "\n")
    # 1. drop an earlier battle_b screen entry (the first version of this card put it inside "screens")
    pos = text.find('"name": "battle_b"')
    if pos >= 0:
        start = text.rfind("{", 0, pos)
        end = _match_brace(text, start)
        tail = re.match(r",?\s*", text[end + 1:])
        text = text[:start] + text[end + 1 + tail.end():]
    # 2. drop an earlier top level key
    pos = text.find('"battle_b": {')
    if pos >= 0:
        start = text.index("{", pos)
        end = _match_brace(text, start)
        cut = text.rfind(",", 0, pos)
        text = text[:cut] + text[end + 1:]
    # 3. add the key before the closing brace of the file
    idx = text.rstrip().rfind("}")
    head = text[:idx].rstrip()
    block = json.dumps(LAYOUT_B, indent=2).replace("\n", "\n  ")
    text = head + ',\n  "battle_b": ' + block + "\n" + text[idx:]
    json.loads(text)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text.replace("\n", nl))


def main():
    for line in build_enemies():
        print(line)
    build_hud()
    write_layout()
    print("hud atlas and ui_layouts battle_b written")


if __name__ == "__main__":
    main()
