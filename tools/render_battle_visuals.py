#!/usr/bin/env python3
"""render_battle_visuals.py: compose the 2026-11-01 battle screen offline, from the same files the game draws.

The game window is never opened. This script reads the geometry from data/ui_layouts.json (screen "battle_b", the
one the director reads), the scene strips, the big enemy sheets, the party's battle sheets, the window, font and
cursor sheets and the HUD swatch atlas, and stacks them in the director's own draw order into 256x240 PNGs.

    output/battle_visuals_2026-11-01/morgan.png         Morgan at Southampton Town Quay (menu state)
    output/battle_visuals_2026-11-01/navy_deck.png      the Navy sailor on the ship's deck
    output/battle_visuals_2026-11-01/percy_office.png   Percy Skye in his office
    ... each with a _3x.png (768x720), plus morgan_message.png (a message box open) and morgan_hit.png (hit frame).

Usage:  python tools/render_battle_visuals.py
"""
from __future__ import annotations

import json
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output", "battle_visuals_2026-11-01")
if os.environ.get("PP_BATTLE_OUT"):
    OUT = os.path.abspath(os.environ["PP_BATTLE_OUT"])
GLYPHS = " !\"'()*,-./0123456789:?ABCDEFGHIJKLMNOPQRSTUVWXYZ[]abcdefghijklmnopqrstuvwxyz"
DISSOLVE_STEPS = 78
COMMANDS = ("FIGHT", "POWER", "TALK", "SPARE", "ITEM")


def load(*parts):
    return Image.open(os.path.join(ROOT, *parts)).convert("RGBA")


def data(*parts):
    path = os.path.join(ROOT, *parts)
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


class Renderer:
    def __init__(self):
        self.L = data("data", "ui_layouts.json")["battle_b"]
        self.win = load("game", "sprites_src", "title", "spr_pp_window.png")
        self.font = load("game", "sprites_src", "title", "spr_pp_font8.png")
        self.cur = load("game", "sprites_src", "title", "spr_pp_menu_cursor.png")
        self.hud = load("game", "sprites_src", "bg", "bg_battle_hud.png")
        self.im = None
        # Card t_855887d8: the victory panel's field is the paper role, the same one pp_battle_draw_victory fills
        # from pp_role_colour("paper"). The renderer reads it from data/palette.json rather than typing a colour, so
        # a palette edit moves this picture with the game.
        self.roles = self._roles()

    def _roles(self):
        pal = data("data", "palette.json")
        names, colours = pal["roles"], pal["colours"]

        def rgb(role):
            text = colours[names[role]].lstrip("#")
            return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))

        return {role: rgb(role) for role in ("ink", "paper", "dim")}

    def field(self, x, y, w, h, role="paper"):
        """A flat rectangle in one role colour, which is how the panel's field and its rule are drawn."""
        self.im.paste(Image.new("RGB", (w, h), self.roles[role]), (x, y))


    def window(self, x, y, tw, th):
        for ty in range(th):
            for tx in range(tw):
                if ty == 0:
                    sl = 0 if tx == 0 else (2 if tx == tw - 1 else 1)
                elif ty == th - 1:
                    sl = 6 if tx == 0 else (8 if tx == tw - 1 else 7)
                else:
                    sl = 3 if tx == 0 else (5 if tx == tw - 1 else 4)
                tile = self.win.crop((sl * 8, 0, sl * 8 + 8, 8))
                self.im.paste(tile, (x + tx * 8, y + ty * 8), tile)

    def text(self, s, x, y):
        for ch in s:
            g = GLYPHS.find(ch)
            if g >= 0:
                tile = self.font.crop((g * 8, 0, g * 8 + 8, 8))
                self.im.paste(tile, (x, y), tile)
            x += 8

    def centre(self, s, cx, y):
        self.text(s, int(cx - len(s) * 4), y)

    def swatch(self, key, x, y, w, h):
        if w <= 0 or h <= 0:
            return
        col = self.hud.getpixel((self.L["swatches"][key] * 16 + 8, 8))
        self.im.paste(Image.new("RGBA", (w, h), col), (x, y))

    def bar(self, x, y, w, h, frac, fill, hi):
        self.swatch("grey", x, y, w, h)
        self.swatch("k", x + 1, y + 1, w - 2, h - 2)
        n = int((w - 2) * frac)
        if frac > 0 and n < 1:
            n = 1
        self.swatch(fill, x + 1, y + 1, n, h - 2)
        self.swatch(hi, x + 1, y + 1, n, 1)

    def dissolve(self, frame, x0, y0, steps):
        """The kill's disintegration, the same arithmetic as pp_battle_draw_dissolve in the director."""
        b, life = 4, DISSOLVE_STEPS - 40
        cols, rows = frame.width // b, frame.height // b
        for by in range(rows):
            for bx in range(cols):
                delay = (bx * 37 + by * 91) % 40
                tt = steps - delay
                dx = dy = 0
                if tt > 0:
                    if tt >= life:
                        continue
                    speed = 0.35 + ((bx * 13 + by * 7) % 5) * 0.12
                    dx = int((bx - cols * 0.5) * tt * 0.09 // 1) + ((bx + by) % 3 - 1)
                    dy = -int(tt * speed // 1)
                    k = (bx + by + steps) % 4
                    if tt > life * 0.8 and k != 0:
                        continue
                    if tt > life * 0.5 and k % 2 == 1:
                        continue
                blk = frame.crop((bx * b, by * b, bx * b + b, by * b + b))
                self.im.paste(blk, (x0 + bx * b + dx, y0 + by * b + dy), blk)

    def party(self):
        """The party column the director draws: the legacy battle screen's `party` rows, in the file's own order.
        `member` is the sheet id lowered; `name` is the word printed under the portrait (ZANDER, KONRAD, HADRIAN)."""
        screens = data("data", "ui_layouts.json")["screens"]
        rows = [s for s in screens if s.get("name") == "battle"][0]["party"]
        return [(r["member"].lower(), r.get("name", r["member"].upper())) for r in rows]

    def compose(self, c):
        L = self.L
        self.im = Image.new("RGBA", (256, 240), (0, 0, 0, 255))
        self.im.paste(load("game", "sprites_src", "bg", "bg_battle_%s.png" % c["scene"]), (0, 0))
        e = L["enemy"]
        sheet = load("game", "sprites_src", "enemies", "%s%s.png" % (c["enemy"], e["suffix"]))
        fw, fh = e["frame_w"], e["frame_h"]
        frame = sheet.crop((c.get("frame", 0) * fw, 0, c.get("frame", 0) * fw + fw, fh))
        if c.get("dissolve") is None:
            self.im.paste(frame, (e["cx"] - fw // 2, e["feet"] - (fh - 1)), frame)
        elif c["dissolve"] < DISSOLVE_STEPS:
            self.dissolve(sheet.crop((0, 0, fw, fh)), e["cx"] - fw // 2, e["feet"] - (fh - 1), c["dissolve"])

        p = L["plate"]
        self.window(p["x"], p["y"], p["w"], p["h"])
        self.centre(c["name"], p["x"] + p["w"] * 4, p["name_y"])
        frac = c["hp"] / float(max(1, c["hp_max"]))
        self.text("HP %d/%d" % (c["hp"], c["hp_max"]), p["label_x"], p["hp_y"])
        self.bar(p["bar_x"], p["hp_y"] + 1, p["bar_w"], p["bar_h"], frac, "hp" if frac > 0.3 else "low",
                 "hp_hi" if frac > 0.3 else "low_hi")
        self.text("MERCY", p["label_x"], p["mercy_y"])
        self.bar(p["bar_x"], p["mercy_y"] + 1, p["bar_w"], p["bar_h"], c["mercy"] / 100.0, "mercy", "mercy_hi")

        q = L["panel"]
        self.window(q["x"], q["y"], q["w"], q["h"])
        for i, (pid, label) in enumerate(self.party()):
            sheet = load("game", "sprites_src", "chars", "%s_battle.png" % pid)
            fi = c.get("attack_frame", 2) if c.get("striker") == i else 0
            f0 = sheet.crop((fi * 24, 0, fi * 24 + 24, 32))
            px = q["party_x"] + i * q["party_step"]
            self.im.paste(f0, (px, q["party_y"]), f0)
            self.centre(label, px + q["name_dx"], q["name_y"])
        self.swatch("grey", q["rule_x"], q["party_y"] + 1, 1, 30)
        if c.get("turn") is not None:
            ax = q["party_x"] + c["turn"] * q["party_step"] + 12
            for r in range(6):
                self.swatch("gold", ax - (11 - r * 2) // 2, q["party_y"] - 14 + r, 11 - r * 2, 1)
            label = self.party()[c["turn"]][1] + "'S TURN"
            tiles = max(3, min(32, len(label) + 2))
            self.window((256 - tiles * 8) // 2, 8, tiles, 3)
            self.text(label, (256 - tiles * 8) // 2 + 8, 12)
        if c.get("strike"):
            name, fr = c["strike"]
            sw = load("game", "sprites_src", "weapons", name + ".png")
            fwid = sw.height
            ov = sw.crop((fr * fwid, 0, fr * fwid + fwid, fwid))
            self.im.paste(ov, (e["cx"] - fwid // 2, e["feet"] - fh // 2 - fwid // 2), ov)
        self.text("HP %d/%d" % (c["php"], c["php_max"]), q["stat_x"], q["hp_y"])
        self.bar(q["stat_x"], q["hp_bar_y"], q["bar_w"], q["bar_h"], c["php"] / float(c["php_max"]), "hp", "hp_hi")
        self.text("WILL %d/%d" % (c["will"], c["will_max"]), q["stat_x"], q["will_y"])
        self.bar(q["stat_x"], q["will_bar_y"], q["bar_w"], q["bar_h"], c["will"] / float(c["will_max"]), "will", "will_hi")

        m = L["command"]
        self.window(m["x"], m["y"], m["w"], m["h"])
        if not c.get("message"):
            for i, label in enumerate(COMMANDS):
                x, y = 24 + (i % 2) * 104, 178 + (i // 2) * 14
                self.text(label, x, y)
                if i == c.get("cursor", 0):
                    self.im.paste(self.cur.crop((0, 0, 8, 8)), (x - 12, y), self.cur.crop((0, 0, 8, 8)))
            if c.get("held"):
                self.text("HELD: " + c["held"], 16, 220)
        else:
            g = L["message"]
            self.window(g["x"], g["y"], g["w"], g["h"])
            for j, line in enumerate(c["message"]):
                self.text(line, 16, 16 + j * 10)

        # Card t_855887d8: the victory panel, drawn last and from the same row pp_battle_draw_victory reads. The nine
        # slice frame first, the paper field inside its 8 pixel border, the dim rule under the title, then the three
        # words: VICTORY, the outcome the fight chose, and the prompt (only once the fight is finished).
        v = c.get("victory")
        if v:
            w = L["victory"]
            self.window(w["x"], w["y"], w["w"], w["h"])
            self.field(w["x"] + 8, w["y"] + 8, w["w"] * 8 - 16, w["h"] * 8 - 16, "paper")
            self.field(w["x"] + 16, w["title_y"] + 9, w["w"] * 8 - 32, 1, "dim")
            cx = w["x"] + w["w"] * 4
            self.centre("VICTORY", cx, w["title_y"])
            self.centre(v["word"], cx, w["word_y"])
            if v.get("press"):
                self.centre("press Z", cx, w["press_y"])
        return self.im.convert("RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    enemies = {e["id"]: e for e in data("data", "enemies", "all.json").get("enemies", [])}
    items = data("data", "items.json")
    held = ""
    rows = items.get("items", []) if isinstance(items, dict) else []
    for row in rows:
        if row.get("id") == "master_bolt":
            held = str(row.get("name", ""))

    def row(eid, fallback_name, fallback_hp):
        e = enemies.get(eid, {})
        return str(e.get("name", fallback_name)), int(e.get("max_hp", fallback_hp))

    common = dict(php=20, php_max=20, will=3, will_max=3, mercy=0, cursor=0, held=held)
    cases = []
    for out, scene, eid, nm, hp in (("morgan", "quay_town", "morgan", "Morgan", 24),
                                    ("navy_deck", "ship_deck", "navy_sailor", "Navy Sailor", 15),
                                    ("percy_office", "ship_office", "percy", "Percy Skye", 120)):
        name, mx = row(eid, nm, hp)
        cases.append(dict(common, out=out, scene=scene, enemy=eid, name=name, hp=mx, hp_max=mx))
    r = Renderer()
    for c in cases:
        im = r.compose(c)
        im.save(os.path.join(OUT, c["out"] + ".png"))
        im.resize((768, 720), Image.NEAREST).save(os.path.join(OUT, c["out"] + "_3x.png"))
    m = dict(cases[0], out="morgan_message", message=["* Morgan checks his clipboard.", "* You are not on the list."])
    r.compose(m).save(os.path.join(OUT, "morgan_message.png"))
    h = dict(cases[2], out="percy_hit", frame=2, hp=70, mercy=40, php=14, cursor=2)
    r.compose(h).save(os.path.join(OUT, "percy_hit.png"))
    # Card t_855887d8: the deck fight won, with the victory panel over the field. The word is the outcome the fight
    # writes for a kill (pp_battle_outcome), so this is the panel a won FIGHT path ends on.
    v = dict(cases[1], out="navy_deck_victory", hp=0, victory={"word": "kill", "press": True})
    im = r.compose(v)
    im.save(os.path.join(OUT, "navy_deck_victory.png"))
    im.resize((768, 720), Image.NEAREST).save(os.path.join(OUT, "navy_deck_victory_3x.png"))
    # FINAL-SCOPE 2026-11-03: the Percy fight on the quay, the weapon strikes and the kill's disintegration.
    pq = dict(cases[2], out="percy_quay", scene="quay_town", name="PERCY")
    r.compose(pq).save(os.path.join(OUT, "percy_quay.png"))
    mq = dict(cases[0], out="morgan_name", name="CAPTAIN MORGAN")
    r.compose(mq).save(os.path.join(OUT, "morgan_name.png"))
    for n in (0, 1, 2):
        r.compose(dict(mq, out="turn_%d" % n, turn=n, hp=17, mercy=70)).save(os.path.join(OUT, "turn_%d.png" % n))
    for who, wname, idx in (("zander", "spr_pp_master_bolt", 0), ("konrad", "spr_pp_adamantine_scythe", 1),
                            ("hadrian", "spr_pp_bident", 2)):
        s = dict(mq, out="strike_" + who, strike=(wname, 2), striker=idx, attack_frame=3, frame=2,
                 message=["* swing"], held="")
        r.compose(s).save(os.path.join(OUT, "strike_%s.png" % who))
    for n in (0, 14, 30, 46, 62):
        d = dict(mq, out="dissolve_%02d" % n, dissolve=n, hp=0)
        r.compose(d).save(os.path.join(OUT, "dissolve_%02d.png" % n))
    print("rendered:", ", ".join(c["out"] for c in cases), ", navy_deck_victory")


if __name__ == "__main__":
    main()
