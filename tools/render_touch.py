"""Render the touch overlay (spec 22) to output\android_touch\, so the overlay is proved by an image and not prose.

Mirrors the geometry and palette of game\scripts\pp_touch\pp_touch.gml at 256x240: the free layout on a mock deck
frame, and the text layout over a dialogue box, to show the controls clear the text (spec 22 rule 5).
"""

from __future__ import annotations

import json
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output", "android_touch")
W, H = 256, 240
ALPHA = 140  # 0.55 * 255, the PP_TOUCH_ALPHA the module draws with
WHITE = (248, 248, 248, 255)  # the sheet font white
RESAMPLE = getattr(Image, "Resampling", Image).NEAREST


def _palette():
    with open(os.path.join(ROOT, "data", "palette.json"), encoding="utf-8") as handle:
        data = json.load(handle)
    roles = data["roles"]
    colours = data["colours"]
    return {name: colours[roles[name]] for name in ("ink", "paper", "dim", "text", "window", "window_edge")}


def _rgba(hexstr, alpha=255):
    hexstr = hexstr.lstrip("#")
    return (int(hexstr[0:2], 16), int(hexstr[2:4], 16), int(hexstr[4:6], 16), alpha)


def _free():
    return {
        "pad": {"cx": 48, "cy": 190, "r": 28},
        "a": {"cx": 204, "cy": 198, "r": 24},
        "b": {"cx": 236, "cy": 174, "r": 16},
        "menu": {"cx": 236, "cy": 134, "r": 14},
    }


def _text():
    return {
        "pad": {"cx": 44, "cy": 56, "r": 24},
        "a": {"cx": 216, "cy": 128, "r": 22},
        "b": {"cx": 232, "cy": 88, "r": 16},
    }


def _deck_background(pal):
    """A mock deck frame, so the semi transparent controls sit over real game colours, not a flat field."""
    img = Image.new("RGBA", (W, H), _rgba(pal["window"]))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 150, W, H], fill=_rgba(pal["paper"]))
    for y in range(150, H, 18):
        draw.rectangle([0, y, W, y + 2], fill=_rgba(pal["dim"], 180))
    draw.rectangle([0, 100, W, 150], fill=_rgba(pal["window_edge"], 40))
    return img


def _dialogue_box(draw, pal):
    """The dialogue box the text layout must clear: paper fill, ink border, white glyphs (spec 05 fallback)."""
    draw.rectangle([8, 168, 248, 232], fill=_rgba(pal["paper"]))
    draw.rectangle([8, 168, 248, 232], outline=_rgba(pal["ink"]), width=1)
    for row, y in enumerate((176, 188, 200)):
        draw.rectangle([16, y, 40 + (row * 24), y + 6], fill=WHITE)


def _pad(draw, pal, c):
    ink = _rgba(pal["ink"], ALPHA)
    paper = _rgba(pal["paper"], ALPHA)
    text = _rgba(pal["text"], ALPHA)
    draw.ellipse([c["cx"] - c["r"], c["cy"] - c["r"], c["cx"] + c["r"], c["cy"] + c["r"]], fill=paper)
    draw.ellipse([c["cx"] - c["r"], c["cy"] - c["r"], c["cx"] + c["r"], c["cy"] + c["r"]], outline=ink)
    draw.line([c["cx"], c["cy"] - c["r"], c["cx"], c["cy"] + c["r"]], fill=text)
    draw.line([c["cx"] - c["r"], c["cy"], c["cx"] + c["r"], c["cy"]], fill=text)


def _button(draw, pal, c, label):
    ink = _rgba(pal["ink"], ALPHA)
    paper = _rgba(pal["paper"], ALPHA)
    draw.ellipse([c["cx"] - c["r"], c["cy"] - c["r"], c["cx"] + c["r"], c["cy"] + c["r"]], fill=paper)
    draw.ellipse([c["cx"] - c["r"], c["cy"] - c["r"], c["cx"] + c["r"], c["cy"] + c["r"]], outline=ink)
    draw.text((c["cx"], c["cy"]), label, fill=WHITE, anchor="mm")


def _menu_button(draw, pal, c):
    ink = _rgba(pal["ink"], ALPHA)
    paper = _rgba(pal["paper"], ALPHA)
    text = _rgba(pal["text"], ALPHA)
    draw.ellipse([c["cx"] - c["r"], c["cy"] - c["r"], c["cx"] + c["r"], c["cy"] + c["r"]], fill=paper)
    draw.ellipse([c["cx"] - c["r"], c["cy"] - c["r"], c["cx"] + c["r"], c["cy"] + c["r"]], outline=ink)
    for dy in (-4, 0, 4):
        draw.line([c["cx"] - 6, c["cy"] + dy, c["cx"] + 6, c["cy"] + dy], fill=text)


def _overlay(draw, pal, layout):
    _pad(draw, pal, layout["pad"])
    _button(draw, pal, layout["a"], "A")
    _button(draw, pal, layout["b"], "B")
    if "menu" in layout:
        _menu_button(draw, pal, layout["menu"])


def _save(img, name):
    path = os.path.join(OUT, name)
    img.save(path)
    up = img.resize((W * 3, H * 3), RESAMPLE)
    up.save(os.path.join(OUT, name.replace(".png", "_3x.png")))
    print(f"wrote {path} (+3x)")


def main():
    pal = _palette()
    os.makedirs(OUT, exist_ok=True)

    free = _deck_background(pal)
    _overlay(ImageDraw.Draw(free), pal, _free())
    _save(free, "touch_overlay_free.png")

    text_img = _deck_background(pal)
    draw = ImageDraw.Draw(text_img)
    _dialogue_box(draw, pal)
    _overlay(draw, pal, _text())
    _save(text_img, "touch_overlay_text.png")


if __name__ == "__main__":
    main()
