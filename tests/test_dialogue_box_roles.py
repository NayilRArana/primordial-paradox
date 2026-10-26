"""Tests for the dialogue box's chrome roles (card t_769b545d).

Measured on the 2026-10-26 take `output/demo/demo-talk-2026-10-26.mp4`: the first dialogue box ever opened on
`ship_small` (room palette `deck_day`) wrote `build/demo-game.log:163`

    PP: role accent is not in the room palette set deck_day, drawing it as PP_COLOUR_MISSING

because `pp_dialogue_draw` asked for `accent` for the choice cursor and for the page arrow, and `deck_day` declares
fourteen roles, none of them `accent`. The take still passed its six file checks and its picture floor (0.931 to 0.994
across seven samples) because magenta is one flat colour, so this was a look defect and not a capture failure: the
cursor and the arrow were the one thing on screen in a colour no palette set may declare.

The same class of ask sat in `pp_map_kind_colour`, which drew doors and hatches in `accent` on the build that has no
tile sheet. It never fired in the recording because `ts_ship` ships, so the tile path draws sprites untinted and the
rectangle path never ran; it is fixed here so the class is gone rather than the one site.

What is pinned here is the rule, not the picture:

  test_the_box_asks_only_for_roles_every_set_carries        no role the room's set cannot resolve, ever again
  test_the_cursor_and_the_arrow_spend_the_brightest_role    the chrome takes `text`, measured as the brightest shared
  test_the_map_fallback_asks_only_for_roles_every_set_carries   door and hatch draw as well as the box does
  test_the_spec_and_the_code_tell_the_same_story            spec 05's amended bullet and this code cannot drift apart

Honest limit: none of this renders a frame. The appearance is proven by a fresh `tools/play_demo.py` take whose log
carries no `PP: role` line and whose picture floor stays at or above 0.90.
"""

from __future__ import annotations

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIALOGUE = "game/scripts/pp_dialogue/pp_dialogue.gml"
MAP = "game/scripts/pp_map/pp_map.gml"
SPEC = "specs/05-dialogue.md"

# The roles the box's chrome spends, and the only roles every set in data/room_palettes.json carries plus the plate's
# own ink. Named here so a change that adds a fourth role to the box has to come through this file.
BOX_ROLES = {"ink", "paper", "text"}


def read(relative: str) -> str:
    with open(os.path.join(ROOT, *relative.split("/")), "r", encoding="utf-8-sig") as handle:
        return handle.read()


def read_json(relative: str):
    return json.loads(read(relative))


def gml_code_only(text: str) -> str:
    """Strip comments, so the rules are judged on code and a comment that names a role is not a call."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return "\n".join(line.split("//")[0] for line in text.splitlines())


def function_body(code: str, name: str) -> str:
    """The body of one GML function, by matching braces from its opening brace."""
    match = re.search(r"\bfunction\s+%s\s*\(" % re.escape(name), code)
    if not match:
        return ""
    start = code.find("{", match.end())
    depth = 0
    for index in range(start, len(code)):
        if code[index] == "{":
            depth += 1
        elif code[index] == "}":
            depth -= 1
            if depth == 0:
                return code[start:index + 1]
    return ""


def role_calls(code: str) -> set:
    """Every role name the module resolves through pp_role_colour."""
    return set(re.findall(r'pp_role_colour\s*\(\s*"([a-z0-9_]+)"\s*\)', code))


def luminance(hexv: str) -> float:
    raw = hexv.lstrip("#")
    channels = []
    for index in (0, 2, 4):
        c = int(raw[index:index + 2], 16) / 255.0
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def universal_roles() -> set:
    """The roles every palette set in data/room_palettes.json declares."""
    sets = [set(room_set["roles"]) for room_set in read_json("data/room_palettes.json")["sets"]]
    return set.intersection(*sets)


def test_the_box_asks_only_for_roles_every_set_carries():
    code = gml_code_only(read(DIALOGUE))
    asked = role_calls(code)
    assert asked == BOX_ROLES, "the box asks for %s, and this file pins %s" % (sorted(asked), sorted(BOX_ROLES))
    missing = sorted(asked - universal_roles())
    assert missing == [], ("the box asks for %s, which not every room palette set declares: a role a set does not "
                           "carry draws PP_COLOUR_MISSING magenta" % ", ".join(missing))
    assert "accent" not in code, "accent is back in the box, and deck_day, ship_cabin and lower_deck do not declare it"


def test_the_cursor_and_the_arrow_spend_the_brightest_role():
    code = gml_code_only(read(DIALOGUE))
    body = function_body(code, "pp_dialogue_draw")
    assert body, "pp_dialogue_draw is gone"

    # The choice cursor: from the cursor test to the row loop's end, which is where the arrow block starts.
    assert "_c == _d.cursor" in body, "the choice cursor block is gone"
    cursor = body[body.index("_c == _d.cursor"):body.index("PP_ARROW_ON + PP_ARROW_OFF")]
    assert 'pp_role_colour("text")' in cursor, "the choice cursor is not drawn in the shared text role"
    assert "accent" not in cursor, "the choice cursor asks for accent again"

    arrow = body[body.index("PP_ARROW_ON + PP_ARROW_OFF"):]
    assert 'pp_role_colour("text")' in arrow, "the page arrow is not drawn in the shared text role"
    assert "accent" not in arrow, "the page arrow asks for accent again"

    # "brightest" is measured, not asserted by taste: text outranks every other role the sets share.
    palette = read_json("data/palette.json")
    roles, colours = palette["roles"], palette["colours"]
    ranked = sorted(((luminance(colours[roles[name]]), name) for name in universal_roles()), reverse=True)
    assert ranked[0][1] == "text", "the brightest role every set carries is %r, not text" % ranked[0][1]
    for dimmer in ("dim", "paper", "ink"):
        assert luminance(colours[roles["text"]]) > luminance(colours[roles[dimmer]]), \
            "text is not brighter than %r" % dimmer


def test_the_map_fallback_asks_only_for_roles_every_set_carries():
    code = gml_code_only(read(MAP))
    body = function_body(code, "pp_map_kind_colour")
    assert body, "pp_map_kind_colour is gone"
    assert "accent" not in body, "door and hatch ask for accent again, which only the ui set declares"
    assert body.count('pp_role_colour("text")') == 2, "door and hatch do not both draw in the shared text role"
    assert 'pp_role_colour("paper")' in body and 'pp_role_colour("dim")' in body, \
        "floor and wall no longer draw in the roles they took"
    missing = sorted(role_calls(code) - universal_roles())
    assert missing == [], ("the map asks for %s, which not every room palette set declares" % ", ".join(missing))


def test_the_spec_and_the_code_tell_the_same_story():
    spec = " ".join(read(SPEC).split())
    assert "Palette roles: the box and its chrome spend three roles and no others" in spec, \
        "spec 05 does not state the roles the box spends"
    for role in sorted(BOX_ROLES):
        assert "`%s`" % role in spec, "spec 05 does not name the %r role the box spends" % role
    assert "PP_COLOUR_MISSING magenta" in spec, "spec 05 does not record what the accent ask drew instead"
    assert "t_769b545d" in spec, "spec 05 does not name the card that amended it"
    assert "accent" in spec and "only the `ui` set declares" in spec, \
        "spec 05 does not record which role the cursor and the arrow used to ask for"
