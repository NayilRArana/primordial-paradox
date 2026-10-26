"""Tests for the drive film's palette roles (card t_415541ee).

Measured on the source before this file existed, against the set the drive map names. The night drive is `drive_night`
(`data/maps/all.json`, room `drive_m4_corridor`), and that set declares thirteen roles:

    ink, paper, dim, text, grey_1, grey_3, grey_5, moss_1, moss_2, moss_3, moss_5, stone_2, gold_5

`pp_drive.gml` asked for eleven, and seven of them are not in the set: `accent`, `window`, `window_edge`,
`window_shadow`, `marker`, `marker_trail` and `hazard`. `pp_role_colour` answers a role the set does not declare with
PP_COLOUR_MISSING (255, 0, 255) and logs

    PP: role accent is not in the room palette set drive_night, drawing it as PP_COLOUR_MISSING

once per role per set, so a draw of the film under `drive_night` is seven magenta bands and seven log lines. The build\\_
drive_roles_probe_pre_fix.json this card measured with prints that lookup, role by role.

The measured reason nobody saw it: the room asked for the `ui` set, which declares all eleven, so every earlier capture
drew a picture that cannot be the picture the shipped drive plays. The room now asks for `drive_night`, the set the map
names, and the module spends only the four roles every set carries.

What is pinned here is the rule, not the picture:

  test_the_drive_asks_only_for_roles_every_set_carries   no role the room's set cannot resolve, ever again
  test_the_seven_roles_no_set_carries_are_gone           the card's defect, named, cannot come back by a one line edit
  test_the_room_draws_in_the_set_the_drive_map_names     the capture proves the set the shipped scene draws in
  test_the_marks_that_must_read_spend_the_brightest_role  lane paint, the headlight pool and lamps take `text`
  test_the_captured_frames_carry_no_missing_colour       the game's own twelve frames, sampled for PP_COLOUR_MISSING

Honest limit: none of this renders a frame. The appearance is proven by a `tools/capture_drive.py` run whose log carries
no `PP: role` line and whose twelve frames measure at or above the 0.90 picture floor; that run needs the idle gate open
and did not happen in this pass (a desktop automation held the gate shut), so the floor stays unmeasured here.
"""

from __future__ import annotations

import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVE = "game/scripts/pp_drive/pp_drive.gml"
MAPS = "data/maps/all.json"
ROOM = "drive_m4_corridor"
MISSING_RGB = (255, 0, 255)

# The roles the film spends, and the only roles every set in data/room_palettes.json declares. Named here so a change
# that adds a fifth role to the drive has to come through this file.
DRIVE_ROLES = {"ink", "paper", "dim", "text"}

# The seven roles the film asked for that no palette set carries, from the measurement above. `accent` is the one the
# card was raised on; the other six are the same defect and were found by resolving the whole module rather than the
# six sites the card named.
FOREIGN_ROLES = ("accent", "window", "window_edge", "window_shadow", "marker", "marker_trail", "hazard")


def read(relative: str) -> str:
    with open(os.path.join(ROOT, *relative.split("/")), "r", encoding="utf-8-sig") as handle:
        return handle.read()


def read_json(relative: str):
    return json.loads(read(relative))


def gml_code_only(text: str) -> str:
    """Strip comments, so the rules are judged on code and a comment that names a role is not a call."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return "\n".join(line.split("//")[0] for line in text.splitlines())


def role_calls(code: str) -> set:
    """Every role name the module resolves through pp_role_colour."""
    return set(re.findall(r'pp_role_colour\s*\(\s*"([a-z0-9_]+)"\s*\)', code))


def band_roles(code: str, known) -> set:
    """Every role name the module hands to pp_drive_band, which resolves it through pp_role_colour one line down."""
    return set(re.findall(r'pp_drive_band\s*\([^;]*?"([a-z0-9_]+)"\s*\)', code)) & set(known)


def universal_roles() -> set:
    """The roles every palette set in data/room_palettes.json declares."""
    sets = [set(room_set["roles"]) for room_set in read_json("data/room_palettes.json")["sets"]]
    return set.intersection(*sets)


def luminance(hexv: str) -> float:
    raw = hexv.lstrip("#")
    channels = []
    for index in (0, 2, 4):
        c = int(raw[index:index + 2], 16) / 255.0
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def role_colours() -> dict:
    palette = read_json("data/palette.json")
    roles, colours = palette["roles"], palette["colours"]
    return {name: colours[roles[name]] for name in roles}


def test_the_drive_asks_only_for_roles_every_set_carries():
    code = gml_code_only(read(DRIVE))
    known = role_colours()
    asked = role_calls(code) | band_roles(code, known)
    assert asked == DRIVE_ROLES, "the drive asks for %s, and this file pins %s" % (sorted(asked), sorted(DRIVE_ROLES))
    missing = sorted(asked - universal_roles())
    assert missing == [], ("the drive asks for %s, which not every room palette set declares: a role a set does not "
                           "carry draws PP_COLOUR_MISSING magenta" % ", ".join(missing))


def test_the_seven_roles_no_set_carries_are_gone():
    code = gml_code_only(read(DRIVE))
    back = ['"%s"' % name for name in FOREIGN_ROLES if '"%s"' % name in code]
    assert back == [], ("the drive asks for %s again; drive_night declares none of them" % ", ".join(back))
    # And the set the drive draws in still cannot answer them, so this test is about the module and not about taste.
    sets = {room_set["id"]: set(room_set["roles"]) for room_set in read_json("data/room_palettes.json")["sets"]}
    unanswerable = sorted(name for name in FOREIGN_ROLES if name not in sets["drive_night"])
    assert len(unanswerable) == len(FOREIGN_ROLES), \
        "drive_night now declares %s, so the fix this file pins has been overtaken" % sorted(
            set(FOREIGN_ROLES) - set(unanswerable))


def test_the_room_draws_in_the_set_the_drive_map_names():
    code = gml_code_only(read(DRIVE))
    match = re.search(r'#macro\s+PP_DRIVE_PALETTE\s+"([a-z0-9_]+)"', code)
    assert match, "PP_DRIVE_PALETTE is gone, so the room no longer says which set it draws in"
    room = None
    for entry in read_json(MAPS)["maps"]:
        if entry.get("id") == ROOM:
            room = entry
            break
    assert room, "the drive map %r is gone from data/maps/all.json" % ROOM
    assert match.group(1) == room["room_palette"], (
        "the drive room draws in %r and the map names %r: the capture would prove a picture the shipped scene never "
        "draws" % (match.group(1), room["room_palette"]))


def test_the_marks_that_must_read_spend_the_brightest_role():
    code = gml_code_only(read(DRIVE))
    headlight = code[code.index("function pp_drive_headlight"):code.index("function pp_drive_gantry_sign")]
    assert headlight.count('"text"') >= 2, "the headlight pool is not drawn in the shared text role"
    assert '"dim"' in headlight, "the beam trail behind the pool no longer steps down to dim"
    road = code[code.index("function pp_drive_road"):code.index("function pp_drive_car")]
    assert '"text"' in road and "marker" not in road, "the lane dashes are not drawn in the shared text role"

    # "brightest" is measured, not asserted by taste: text outranks every other role the sets share.
    colours = role_colours()
    ranked = sorted(((luminance(colours[name]), name) for name in universal_roles()), reverse=True)
    assert ranked[0][1] == "text", "the brightest role every set carries is %r, not text" % ranked[0][1]
    for dimmer in ("dim", "paper", "ink"):
        assert luminance(colours["text"]) > luminance(colours[dimmer]), "text is not brighter than %r" % dimmer


def test_the_captured_frames_carry_no_missing_colour():
    """The twelve frames the room writes from inside its own draw (tools/capture_drive.py), sampled for magenta.

    A capture is the only thing that proves the picture, and these are the committed frames it wrote. Zero
    PP_COLOUR_MISSING pixels is the floor of that proof: it does not say the picture is good, only that the palette
    answered every ask.
    """
    from PIL import Image

    frames = sorted(glob.glob(os.path.join(ROOT, "output", "drive", "pp_drive_shot_[0-9][0-9].png")))
    assert len(frames) == 12, "the drive's twelve captured frames are not all committed: %d found" % len(frames)
    hot = {}
    for path in frames:
        with Image.open(path) as image:
            counts = image.convert("RGB").getcolors(maxcolors=1 << 22) or []
        magenta = sum(count for count, pixel in counts if pixel == MISSING_RGB)
        if magenta:
            hot[os.path.basename(path)] = magenta
    assert hot == {}, "PP_COLOUR_MISSING magenta in the drive's own frames: %s" % hot
