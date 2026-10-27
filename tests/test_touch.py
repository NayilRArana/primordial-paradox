"""Tests for the touch overlay (spec 22): the source pins and the pad direction logic.

The overlay is proven at the source level the same way test_project.py proves the rest of the game: read the
module, pin what it maps to, and mirror the one piece of real arithmetic (the pad sector to a walk vector) in
Python, so a wrong sector cannot slip through.
"""

from __future__ import annotations

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOUCH = os.path.join(ROOT, "game", "scripts", "pp_touch", "pp_touch.gml")
INPUT = os.path.join(ROOT, "game", "scripts", "pp_input", "pp_input.gml")
APP = os.path.join(ROOT, "game", "scripts", "pp_app", "pp_app.gml")
CONFIG = os.path.join(ROOT, "game", "scripts", "pp_config", "pp_config.gml")

TOUCH_ACTIONS = ("confirm", "cancel", "menu", "up", "down", "left", "right")


def _read(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def _box_top():
    """The dialogue box top (PP_BOX_Y), read from the config so the test follows the value, not a copy."""
    match = re.search(r"#macro PP_BOX_Y (\d+)", _read(CONFIG))
    assert match, "PP_BOX_Y macro not found in pp_config"
    return int(match.group(1))


def test_touch_maps_only_to_the_seven_actions():
    text = _read(TOUCH)
    written = set(re.findall(r'held\[\$ "([a-z_]+)"\]', text))
    assert written == set(TOUCH_ACTIONS)


def test_touch_enabled_is_touch_targets_only():
    text = _read(TOUCH)
    match = re.search(r"function pp_touch_platform\(\)\s*\{\s*(.*?)\s*\}", text, re.S)
    assert match, "pp_touch_platform not found"
    body = match.group(1)
    for target in ("os_android", "os_operagx", "os_browser"):
        assert target in body
    assert "os_windows" not in body


def test_touch_never_over_dialogue_text():
    text = _read(TOUCH)
    match = re.search(r"function pp_touch_layout_text\(\)\s*\{\s*return \{(.*?)\};", text, re.S)
    assert match, "pp_touch_layout_text not found"
    circles = re.findall(r"\{ cx: (\d+),\s*cy: (\d+),\s*r: (\d+) \}", match.group(1))
    assert circles, "no controls found in the text layout"
    box_top = _box_top()
    for cx, cy, r in circles:
        cy, r = int(cy), int(r)
        assert cy + r <= box_top, f"text-layout control at cy={cy} r={r} reaches y={cy + r}, over the box"


def test_touch_wired_into_input_and_app():
    inp = _read(INPUT)
    app = _read(APP)
    assert "pp_touch_sample()" in inp
    assert "pp_touch_held(" in inp
    assert "pp_touch_init()" in app
    assert "pp_touch_draw()" in app


def test_pad_eight_directions_match_free_movement():
    text = _read(TOUCH)
    expr = {}
    for action in ("up", "down", "left", "right"):
        match = re.search(r'_held\[\$ "' + action + r'"\]\s*=\s*\((.+?)\);', text, re.S)
        assert match, f"no sector expression for {action}"
        expr[action] = match.group(1).replace("||", " or ").replace("&&", " and ")

    vectors = {}
    for sector in range(8):
        env = {"_s": sector}
        vectors[sector] = tuple(
            1 if eval(expr[a], {}, env) else 0 for a in ("up", "down", "left", "right")
        )

    expected = {
        0: (0, 0, 0, 1),   # right
        1: (1, 0, 0, 1),   # up right
        2: (1, 0, 0, 0),   # up
        3: (1, 0, 1, 0),   # up left
        4: (0, 0, 1, 0),   # left
        5: (0, 1, 1, 0),   # down left
        6: (0, 1, 0, 0),   # down
        7: (0, 1, 0, 1),   # down right
    }
    assert vectors == expected
    assert len(set(vectors.values())) == 8


def test_touch_draw_uses_palette_and_alpha():
    text = _read(TOUCH)
    assert "draw_set_alpha(PP_TOUCH_ALPHA)" in text
    assert "pp_role_colour(" in text
    assert "pp_touch_text_open()" in text
    assert "pp_font_draw(" in text
