"""Card HERO-ZEUS: the hero is drawn with the style B zeus_ow_walk8 sheet in eight directions.

Only the picture changed: facing (4 way, the reach), the feet box, speed and camera are pinned by test_move_hold.py and
the demo tape. This file pins the 8 direction frame table (read from the GML itself), the sheet, and the feet row."""
import io, json, os, re

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GML = os.path.join(ROOT, "game", "scripts", "pp_overworld", "pp_overworld.gml")
CHARS = os.path.join(ROOT, "game", "sprites_src", "chars")
SRC = io.open(GML, encoding="utf-8-sig").read()

DIRS = ["down", "down_left", "left", "up_left", "up", "up_right", "right", "down_right"]
VECTORS = {"down": (0, 1), "down_left": (-1, 1), "left": (-1, 0), "up_left": (-1, -1), "up": (0, -1),
           "up_right": (1, -1), "right": (1, 0), "down_right": (1, 1)}


def body(name):
    start = SRC.index("function %s(" % name)
    depth, i = 0, SRC.index("{", start)
    for j in range(i, len(SRC)):
        depth += SRC[j] == "{"
        depth -= SRC[j] == "}"
        if depth == 0:
            return SRC[i + 1:j]
    raise AssertionError(name)


def gml_dir8():
    """Translate the (tiny, branch only) GML body of pp_world_dir8_index to Python and run it: the test measures the GML."""
    lines = []
    for raw in body("pp_world_dir8_index").strip().splitlines():
        t = raw.strip().replace("&&", " and ")
        t = t.rstrip(";")
        t = re.sub(r"return \((.+?)\) \? (\d+) : (\d+)$", r"return (\2 if (\1) else \3)", t)
        t = re.sub(r"^if \((.+?)\) return ", r"if \1: return ", t)
        lines.append("    " + t)
    ns = {}
    exec("def f(_dx, _dy):\n" + "\n".join(lines), ns)
    return ns["f"]


def test_eight_vectors_map_to_the_documented_direction_index():
    f = gml_dir8()
    for i, name in enumerate(DIRS):
        assert f(*VECTORS[name]) == i, (name, f(*VECTORS[name]))
    assert f(0, 0) == 0, "no vector draws as down"


def test_frame_is_direction_times_two_plus_step_and_standing_is_the_idle_frame():
    f = gml_dir8()
    frame_fn = body("pp_world_hero_frame8")
    assert "(_hero.walking == true) ? (_hero.walk_anim mod 2) : 0" in frame_fn, frame_fn
    assert "pp_world_hero_dir8(_hero) * 2 + _step" in frame_fn, frame_fn
    for i, name in enumerate(DIRS):
        for walking, anim in ((False, 0), (False, 1), (True, 0), (True, 1)):
            step = (anim % 2) if walking else 0
            assert f(*VECTORS[name]) * 2 + step == i * 2 + step
            if not walking:
                assert i * 2 + step == i * 2, "standing must be the idle frame of the last direction"


def test_the_drawn_direction_is_kept_while_standing_and_follows_the_move_vector():
    ff = body("pp_world_face_input")
    assert "_hero.dir_x = _wx;" in ff and "_hero.dir_y = _wy;" in ff, ff
    stop = body("pp_world_stop_walk")
    assert "dir_x" not in stop and "dir_y" not in stop, "standing must keep the last direction"
    d8 = body("pp_world_hero_dir8")
    for key in ('_hero.facing == "right"', '_hero.facing == "left"', '_hero.facing == "down"', '_hero.facing == "up"'):
        assert key in d8, "a scene turning the hero must win over a stale vector"
    assert "dir_x: 0," in body("pp_overworld_hero") and "dir_y: 1," in body("pp_overworld_hero")


def test_the_hero_draw_uses_the_style_b_sheet_with_the_feet_offset_and_keeps_the_old_fallback():
    assert '#macro PP_HERO_SHEET8 "zeus_ow_walk8"' in SRC
    assert '#macro PP_HERO_SHEET "zander_ow_v2"' in SRC, "the 16x16 fallback sheet macro is pinned"
    assert "#macro PP_HERO8_DY 0" in SRC
    draw = body("pp_overworld_draw_hero")
    assert "pp_art_draw(PP_HERO_SHEET8, pp_world_hero_frame8(_hero), _sx, _sy + PP_HERO8_DY" in draw, draw
    assert "pp_art_draw(PP_HERO_SHEET, _frame, _sx, _sy, PP_UNTINTED, 1)" in draw, "fallback lost"
    assert "var _sx = floor(_hero.px) - floor(_world.cam_x) + _ox;" in draw
    assert "var _sy = floor(_hero.py) - floor(_world.cam_y) + _oy;" in draw


def test_the_sheet_is_16_frames_of_16x16_in_the_json_order_and_feet_sit_on_the_tile_bottom():
    meta = json.load(io.open(os.path.join(CHARS, "zeus_ow_walk8.json"), encoding="utf-8-sig"))
    assert meta["directions"] == DIRS and meta["frames_per_direction"] == 2
    im = Image.open(os.path.join(CHARS, "zeus_ow_walk8.png")).convert("RGBA")
    assert im.size == (16 * 16, 16), "the hero is the sailors height (final scope item 3)"
    old = Image.open(os.path.join(CHARS, "zander_ow_v2.png")).convert("RGBA")
    assert old.size == (128, 16)
    for k in range(16):
        bbox = im.crop((k * 16, 0, k * 16 + 16, 16)).getchannel("A").getbbox()
        assert bbox[3] == 16 and bbox[1] == 0, "frame %d feet are not on the bottom row" % k
    for k in range(8):
        assert old.crop((k * 16, 0, k * 16 + 16, 16)).getchannel("A").getbbox()[3] == 16
    # parity: the hero and the sailor are the same height.
    assert Image.open(os.path.join(CHARS, "sailor_ow_v2.png")).size[1] == im.size[1] == 16
    manifest = json.load(io.open(os.path.join(ROOT, "game", "datafiles", "art", "title_manifest.json"), encoding="utf-8-sig"))
    row = [r for r in manifest["animations"] if r["name"] == "zeus_ow_walk8"][0]
    assert (row["frame_w"], row["frame_h"], row["frames"]) == (16, 16, 16)
