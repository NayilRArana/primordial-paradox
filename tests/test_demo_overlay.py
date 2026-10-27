"""The S5 and S6 overlay, measured: the bake row is in the pixels, and the words are the file's own.

What these tests hold down, and why each one earns its place:
  1. THE WORDS ARE NOT TYPED HERE. Every model, time, mode and hash drawn on screen is read back out of
     the bake file at test time and compared with what the tool put in the line. A rename or a re-bake
     that changes those values changes the drawing, and a value the file does not hold cannot appear;
  2. A MISSING ROW OR FIELD STOPS THE SHOT. Section 4 rule 1 of knowledge/DEMO-SCRIPT.md says a row that
     is missing means the shot is not recordable, so the four ways a row can be wrong are all refused
     rather than drawn;
  3. A FALLBACK ROW IS NOT A RECEIPT. The last bake recorded one of the three TALK rows as a hand
     written fallback because the model's answer was refused. Drawn as a live receipt it would claim a
     model answered when it did not, so the tool refuses it, and `--allow-fallback` draws it with the
     source word on the line instead;
  4. THE FRAME TEST FINDS THE ROW. `check_frame` is run on a real render of each shot and every check it
     makes has to pass: plate pixels, ink on each bake line, far less ink when the lines are blanked,
     no ink outside a line box, and a badge;
  5. THE TEXT BOXES STAY THE GAME'S OWN PIXELS. The dialogue box at (8, 168) 240x64 and the battle
     window at (0, 0) 256x48 are compared byte for byte against the source frame, and the plate is asked
     to refuse a layout that would touch either;
  6. THE DEAD BADGE IS ONLY DRAWN WHEN THE FILE SAYS DEAD, and the network line says the same thing the
     file's own `offline` and `network` fields say, in both states.

Run: python -m pytest tests/test_demo_overlay.py -q
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os

import pytest

from PIL import Image, ImageChops, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
SCRIPT = os.path.join(ROOT, "knowledge", "DEMO-SCRIPT.md")
BAKE = os.path.join(ROOT, "data", "meta_bake.json")
LONG_DASHES = ("\u2014", "\u2013", "\u2012", "\u2015")
FALLBACK_ROWS = ("fight/navy_sailor/1", "fight/navy_sailor/2", "fight/navy_sailor/3")


def load_tool(name: str):
    path = os.path.join(TOOLS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def overlay():
    return load_tool("demo_overlay")


def real_bake():
    with open(BAKE, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def script_text():
    with open(SCRIPT, "r", encoding="utf-8") as handle:
        return handle.read()


def write_bake(path, data):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=1)
    return path


@pytest.fixture()
def live_bake_file(tmp_path, overlay):
    """The real bake file, with the three TALK rows marked live, in a throwaway directory.

    This is a test fixture and it never touches data/meta_bake.json: it exists so the S6 drawing and the
    frame test can be measured on a bake that holds three live answers. The tool's own refusal of a
    fallback row is pinned separately, against the file's real state.
    """
    data = copy.deepcopy(real_bake())
    for row in data["rows"]:
        if row["id"] in FALLBACK_ROWS:
            row["source"] = "live"
            row["network"] = True
            row["reason"] = ""
    return write_bake(tmp_path / "live_bake.json", data)


@pytest.fixture()
def offline_bake_file(tmp_path, live_bake_file, overlay):
    data = real_bake()
    for row in data["rows"]:
        if row["id"] in FALLBACK_ROWS:
            row["source"] = "live"
            row["network"] = True
            row["reason"] = ""
    data["bake"]["offline"] = True
    data["bake"]["network"] = False
    return write_bake(tmp_path / "offline_bake.json", data)


@pytest.fixture()
def frame_file(tmp_path, overlay):
    """A 768x720 frame with a few blocks of colour, so a plate drawn on it is measurable."""
    image = Image.new("RGB", (overlay.FRAME_W, overlay.FRAME_H), (26, 111, 130))
    draw = ImageDraw.Draw(image)
    for step in range(12):
        draw.rectangle((8, 20 + step * 40, 760, 40 + step * 40), fill=(13, 43, 58))
        draw.rectangle((40 + step * 56, 60 + step * 40, 60 + step * 56, 90 + step * 40), fill=(216, 165, 92))
    path = tmp_path / "frame.png"
    image.save(path)
    return str(path)


def render_shot(overlay, shot, bake_path, frame_path, out_path, **kwargs):
    bake, index = overlay.load_bake(bake_path)
    image, layout = overlay.render(frame_path, shot, bake, index, **kwargs)
    image.save(out_path)
    return layout


# 1. The words are the file's own


def test_caption_is_read_from_the_script(overlay):
    text = script_text()
    for shot in ("S5", "S6"):
        caption = overlay.shot_caption(shot)
        assert caption in text, "the %s caption the tool draws is not in DEMO-SCRIPT.md" % shot
        assert overlay.shot_caption(shot) == caption


def test_every_drawn_value_comes_out_of_the_bake_file(overlay, live_bake_file):
    bake, index = overlay.load_bake(live_bake_file)
    block = bake["bake"]
    hashes = {row["request_hash"] for row in bake["rows"]}
    for shot in ("S5", "S6"):
        lines = overlay.overlay_lines(shot, bake, index)
        text = "\n".join(line for _, line in lines)
        assert block["model"] in text, "%s does not print the model the file records" % shot
        assert block["created_at"] in text, "%s does not print the time the file records" % shot
        assert "MODE %s" % block["mode"] in text
        printed = [line.split(" ", 1)[1] for tier, line in lines if tier == "hash"]
        for line in printed:
            value = line.split(" ", 1)[1] if line.startswith(("T1", "T2", "T3")) else line.replace("HASH ", "")
            assert value in hashes, "the drawn hash %r is not a request_hash in the bake file" % value


def test_no_long_dash_in_any_drawn_line_or_in_the_tool(overlay, live_bake_file):
    bake, index = overlay.load_bake(live_bake_file)
    for shot in ("S5", "S6"):
        for _, text in overlay.overlay_lines(shot, bake, index):
            for dash in LONG_DASHES:
                assert dash not in text
    with open(os.path.join(TOOLS, "demo_overlay.py"), "r", encoding="utf-8") as handle:
        source = handle.read()
    for dash in LONG_DASHES:
        assert dash not in source, "tools/demo_overlay.py carries a long dash"


# 2. A missing row or field stops the shot


def test_a_row_the_file_does_not_hold_is_refused(overlay, tmp_path):
    data = real_bake()
    data["rows"] = [row for row in data["rows"] if row["id"] != "npc/nye/turn_1"]
    path = write_bake(tmp_path / "no_nye.json", data)
    bake, index = overlay.load_bake(path)
    with pytest.raises(overlay.OverlayError) as error:
        overlay.overlay_lines("S5", bake, index)
    assert "npc/nye/turn_1" in str(error.value)


@pytest.mark.parametrize("field", ("model", "created_at", "request_hash", "source", "network"))
def test_a_row_field_that_is_missing_is_refused(overlay, tmp_path, field):
    data = real_bake()
    for row in data["rows"]:
        if row["id"] == "npc/nye/turn_1":
            row.pop(field, None)
    path = write_bake(tmp_path / ("no_%s.json" % field), data)
    bake, index = overlay.load_bake(path)
    with pytest.raises(overlay.OverlayError) as error:
        overlay.overlay_lines("S5", bake, index)
    assert field in str(error.value)


def test_a_bake_with_no_bake_block_is_refused(overlay, tmp_path):
    data = real_bake()
    data.pop("bake", None)
    path = write_bake(tmp_path / "no_block.json", data)
    with pytest.raises(overlay.OverlayError) as error:
        overlay.load_bake(path)
    assert "bake block" in str(error.value)


# 3. A fallback row is not a receipt


def test_a_fallback_row_is_refused_unless_it_is_labelled(overlay, tmp_path):
    data = real_bake()
    for row in data["rows"]:
        if row["id"] == "fight/navy_sailor/1":
            row["source"] = "fallback"
            row["network"] = False
    path = write_bake(tmp_path / "fallback.json", data)
    bake, index = overlay.load_bake(path)
    with pytest.raises(overlay.OverlayError) as error:
        overlay.overlay_lines("S6", bake, index)
    assert "not a live Meta answer" in str(error.value)
    lines = overlay.overlay_lines("S6", bake, index, allow_fallback=True)
    text = "\n".join(line for _, line in lines)
    assert "T1 SOURCE fallback, NOT A LIVE ANSWER" in text


def test_the_real_bake_file_is_asked_for_a_live_answer_on_the_talk_shot(overlay):
    """The S6 shot is recordable only if the file holds live answers for the three TALK rows.

    This is the honest state check: if the current bake has a fallback row, the tool must refuse and
    the reason must name that row. When the bake is redone with live answers the same call renders, so
    the test asserts the behaviour and the file's own values, not one fixed outcome.
    """
    bake, index = overlay.load_bake(BAKE)
    live = [row["id"] for row in bake["rows"] if row["id"] in FALLBACK_ROWS and row["source"] == "live" and row["network"] is True]
    if len(live) == len(FALLBACK_ROWS):
        lines = overlay.overlay_lines("S6", bake, index)
        assert any(tier == "badge" for tier, _ in lines)
    else:
        with pytest.raises(overlay.OverlayError) as error:
            overlay.overlay_lines("S6", bake, index)
        assert "not a live Meta answer" in str(error.value)


# 4 and 5. The frame test, and the text boxes


def test_s5_frame_test_passes_and_the_dialogue_box_is_untouched(overlay, frame_file, tmp_path):
    out = str(tmp_path / "s5.png")
    layout = render_shot(overlay, "S5", BAKE, frame_file, out)
    bake, index = overlay.load_bake(BAKE)
    report = overlay.check_frame(frame_file, out, "S5", bake, index)
    assert report["ok"], [item for item in report["checks"] if not item["ok"]]
    source = Image.open(frame_file).convert("RGB")
    rendered = Image.open(out).convert("RGB")
    box = overlay.scale_rect(overlay.DIALOGUE_BOX)
    assert ImageChops.difference(source.crop(box), rendered.crop(box)).getbbox() is None
    assert not overlay.intersects(layout["plate"], box)
    inked = [item for item in report["checks"] if item["name"].startswith("ink on the bake line")]
    assert len(inked) == 4, "S5 draws four bake lines: model, time, row and hash"


def test_s6_frame_test_passes_and_the_battle_window_is_untouched(overlay, live_bake_file, frame_file, tmp_path):
    out = str(tmp_path / "s6.png")
    layout = render_shot(overlay, "S6", live_bake_file, frame_file, out)
    bake, index = overlay.load_bake(live_bake_file)
    report = overlay.check_frame(frame_file, out, "S6", bake, index)
    assert report["ok"], [item for item in report["checks"] if not item["ok"]]
    source = Image.open(frame_file).convert("RGB")
    rendered = Image.open(out).convert("RGB")
    for rect in (overlay.BATTLE_BOX, (0, overlay.BATTLE_MENU_TOP, 256, 240 - overlay.BATTLE_MENU_TOP)):
        box = overlay.scale_rect(rect)
        assert ImageChops.difference(source.crop(box), rendered.crop(box)).getbbox() is None
        assert not overlay.intersects(layout["plate"], box)
    assert layout["badge"] is not None


def test_a_plate_that_would_cover_a_text_box_is_refused(overlay):
    tall = [overlay.line_height("detail")] * 60
    with pytest.raises(overlay.OverlayError) as error:
        overlay.plate_rect("S6", tall, below=False)
    assert "does not fit" in str(error.value) or "would cover" in str(error.value)


def test_a_frame_that_is_not_the_three_x_screen_is_refused(overlay, tmp_path):
    small = Image.new("RGB", (256, 240), (0, 0, 0))
    path = str(tmp_path / "small.png")
    small.save(path)
    bake, index = overlay.load_bake(BAKE)
    with pytest.raises(overlay.OverlayError) as error:
        overlay.render(path, "S5", bake, index)
    assert "768x720" in str(error.value)


# 6. The network line follows the file


def test_the_badge_and_the_network_line_follow_the_file(overlay, live_bake_file, offline_bake_file, frame_file, tmp_path):
    live_bake, live_index = overlay.load_bake(live_bake_file)
    offline_bake, offline_index = overlay.load_bake(offline_bake_file)
    live_lines = overlay.overlay_lines("S6", live_bake, live_index)
    offline_lines = overlay.overlay_lines("S6", offline_bake, offline_index)
    live_text = " ".join(text for _, text in live_lines)
    offline_text = " ".join(text for _, text in offline_lines)
    assert "NETWORK LIVE" in live_text and "NETWORK OFF" not in live_text
    assert "NETWORK OFF" in offline_text and "NETWORK LIVE" not in offline_text
    assert "NETWORK UP AT BAKE TIME." in live_text
    assert "NETWORK DEAD SINCE THE FIRST FRAME." in offline_text

    colours = overlay.load_palette()
    live_out = str(tmp_path / "live.png")
    offline_out = str(tmp_path / "offline.png")
    live_layout = render_shot(overlay, "S6", live_bake_file, frame_file, live_out)
    offline_layout = render_shot(overlay, "S6", offline_bake_file, frame_file, offline_out)
    live_image = Image.open(live_out).convert("RGB")
    offline_image = Image.open(offline_out).convert("RGB")
    assert overlay.count_colour(live_image, live_layout["badge"]["rect"], colours["warn"]) > 100
    assert overlay.count_colour(live_image, live_layout["badge"]["rect"], colours["hazard"]) == 0
    assert overlay.count_colour(offline_image, offline_layout["badge"]["rect"], colours["hazard"]) > 100


def test_the_runs_below_the_frame_leave_the_frame_alone(overlay, frame_file, tmp_path):
    out = str(tmp_path / "below.png")
    render_shot(overlay, "S5", BAKE, frame_file, out, below=True)
    source = Image.open(frame_file).convert("RGB")
    rendered = Image.open(out).convert("RGB")
    assert rendered.size[0] == overlay.FRAME_W
    assert rendered.size[1] > overlay.FRAME_H
    top = rendered.crop((0, 0, overlay.FRAME_W, overlay.FRAME_H))
    assert ImageChops.difference(source, top).getbbox() is None


# The clocks


def test_the_clocks_match_the_script(overlay):
    text = script_text()
    assert "1:23.4 to 1:27.4" in text
    assert "2:15.03, 2:18.53, 2:23.53" in text
    assert "2:34.40 to 2:38.40" in text
    s5 = overlay.SHOT_WINDOWS["S5"]["bake"][0]
    assert s5 == (83.4, 87.4)
    s6 = overlay.SHOT_WINDOWS["S6"]["bake"]
    assert s6 == ((135.03, 135.03), (138.53, 138.53), (143.53, 143.53))
    assert overlay.SHOT_WINDOWS["S6"]["network"] == ((154.4, 158.4),)


def test_the_cli_prints_the_rows_and_exits_zero(overlay, capsys):
    assert overlay.main(["--shot", "S5", "--rows"]) == 0
    printed = capsys.readouterr().out
    payload = json.loads(printed)
    assert payload["shot"] == "S5"
    assert payload["rows"] == ["npc/nye/turn_1"]
    assert any(line["tier"] == "hash" for line in payload["lines"])
