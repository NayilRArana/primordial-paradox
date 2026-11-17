"""The video builder, measured: the six captions are the script's own words and the title card names the build.

What these tests hold down:
  1. THE SIX CAPTIONS ARE VERBATIM. Every caption the builder burns is read out of
     knowledge/DEMO-SCRIPT.md by the bake overlay's own reader, and it must match the script's
     'Caption, verbatim:' line for that shot, so the caption cannot be reworded or hand typed.
  2. THE TITLE CARD NAMES THE REAL MODELS. The model ids on the card are the values of
     tools/meta_client.py DEFAULT_MODELS, so a rename there is reflected here and no id is typed.
  3. THE TITLE CARD NAMES THE HARDWARE LIMITS. It says 256x240, at most 16 colours, and no network or
     key, which are the limits the demo claims (spec 13 and spec 19 decision D5).
  4. NO LONG DASH IN A CAPTION OR TITLE LINE. The project forbids U+2013, U+2014, U+2015 in delivered
     text, and the builder refuses one rather than drawing it.
  5. THE CAPTION FITS THE BAND. Every caption is two lines or fewer at the caption size, or the builder
     refuses instead of clipping or shrinking the shared caption font.
  6. THE RENDERED FRAMES CARRY INK. The title card and each caption band, when rendered, hold white
     pixels, and the caption band never exceeds the band height.
  7. THE PASS BADGE IS A MEASUREMENT. Beside the NES LIMITS line the card draws the verdict
     tools/check_nes_limits.py measures on this tree, its box is to the right of that line and inside the
     frame, its ink is on the rendered picture, and a failing check refuses the card instead of drawing
     PASS over a build that breaks the limit (judge panel 2026-11-17 fix 5, card t_1b404055).

Run: python -m pytest tests/test_video_builder.py -q
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess

import pytest

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
SCRIPT = os.path.join(ROOT, "knowledge", "DEMO-SCRIPT.md")
LONG_DASHES = ("\u2014", "\u2013", "\u2012", "\u2015")


def load_tool(name):
    path = os.path.join(TOOLS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def builder():
    return load_tool("video_builder")


@pytest.fixture(scope="module")
def script_text():
    with open(SCRIPT, "r", encoding="utf-8") as handle:
        return handle.read()


def _caption_in_script(shot, script):
    """The exact 'Caption, verbatim: `...`' text for the shot, parsed out of DEMO-SCRIPT.md."""
    lines = script.splitlines()
    heading = None
    for index, line in enumerate(lines):
        if line.startswith("### %s," % shot):
            heading = index
            break
    assert heading is not None, "DEMO-SCRIPT.md has no '### %s,' section" % shot
    for line in lines[heading + 1:]:
        if line.startswith("### ") or line.startswith("## "):
            break
        if line.startswith("Caption, verbatim:"):
            start = line.find("`")
            end = line.rfind("`")
            assert start >= 0 and end > start
            return line[start + 1:end]
    raise AssertionError("DEMO-SCRIPT.md's %s section has no 'Caption, verbatim:' line" % shot)


def test_six_captions_are_verbatim(builder, script_text):
    for shot in builder.SHOTS:
        caption = builder.shot_caption(shot)
        assert caption == _caption_in_script(shot, script_text), "%s caption drifted from DEMO-SCRIPT.md" % shot
        assert caption, "%s caption is empty" % shot
    assert len(builder.SHOTS) == 6


def test_caption_windows_are_inside_the_shot_clock(builder):
    for shot, (lo, hi) in builder.CAPTION_WINDOWS.items():
        assert 0.0 <= lo < hi, "%s window is empty or reversed" % shot
    # The six windows are ordered and non overlapping on the 180.00 s clock.
    ordered = [builder.CAPTION_WINDOWS[shot] for shot in builder.SHOTS]
    for (_, prev_hi), (lo, _) in zip(ordered, ordered[1:]):
        assert prev_hi <= lo, "caption windows overlap or run backwards"


def test_title_card_names_the_models_and_limits(builder):
    models = builder._load_meta_default_models()
    lines = builder.title_card_lines(models)
    raw = " ".join(lines)
    text = raw.upper()
    assert models["chat"].upper() in text, "the chat model id is not on the title card"
    assert models["image"].upper() in text, "the image model id is not on the title card"
    assert models["segment"].upper() in text, "the segment model id is not on the title card"
    assert "256x240" in raw, "the title card does not state the 256x240 screen"
    assert "16 COLOURS" in text, "the title card does not state the 16 colour limit"
    assert "NO NETWORK CALL" in text and "NO KEY" in text, "the title card does not state the offline build"


def test_title_card_states_the_premise_and_judge(builder):
    raw = " ".join(builder.title_card_lines())
    text = raw.upper()
    assert "KRONOS AND ZEUS" in text, "the premise (Kronos and Zeus) is not on the title card"
    assert "REINCARNATED" in text, "the premise's reincarnation claim is not on the title card"
    assert "META MODEL" in text, "the title card does not say a Meta model judges every line"
    assert "JUDGE" in text, "the Meta model judge is not named on the title card"


def test_title_card_uses_the_cold_boot_caption(builder):
    caption = builder.cold_boot_caption()
    assert caption == "Cold boot to menu takes 14 seconds. CONTINUE is dim, because nothing is saved yet."
    for dash in LONG_DASHES:
        assert dash not in caption, "the cold boot caption carries a long dash"


def test_title_card_states_the_controls(builder):
    """Card t_b231fe46: the opening has to say how the game is played, or it states what it is and not how."""
    raw = " ".join(builder.title_card_lines()).upper()
    assert "CONTROLS" in raw, "the title card does not name the controls"
    for key in ("ARROWS MOVE", "Z CONFIRM", "X CANCEL", "TAB START"):
        assert key in raw, "the title card does not state %r" % key


def test_title_card_draws_the_boot_menu_with_continue_dim(builder):
    """The card draws the game's four rows and marks CONTINUE off, which is what the caption's 'dim' claims."""
    assert builder.title_menu_rows() == ["NEW GAME", "CONTINUE", "SETTINGS", "QUIT"], builder.title_menu_rows()
    assert builder.title_menu_dim_row() == "CONTINUE", builder.title_menu_dim_row()
    rows = builder.title_menu_boxes()
    assert [row["label"] for row in rows] == builder.title_menu_rows()
    dim = [row["label"] for row in rows if row["dim"]]
    assert dim == ["CONTINUE"], "the marked off rows are %r" % (dim,)


def test_the_whole_card_fits_inside_the_game_frame(builder):
    """A card that does not fit is a clipped card, so the block is measured before a pixel is drawn."""
    geometry = builder._card_geometry()
    assert geometry["height"] <= builder.FRAME_H - 2 * builder.MARGIN, \
        "the card is %d px tall and the frame holds %d" % (geometry["height"], builder.FRAME_H - 2 * builder.MARGIN)
    for item in geometry["lines"] + geometry["caption"]:
        assert item["x"] >= 0 and item["x"] + item["width"] <= builder.FRAME_W, \
            "the card line %r runs outside the frame" % item["line"]
        assert item["y"] >= 0 and item["y"] + item["height"] <= builder.FRAME_H, \
            "the card line %r runs off the bottom of the frame" % item["line"]


def test_the_overlay_is_opaque_and_carries_the_menu(builder, tmp_path):
    """The cut burns this over S1's picture (card t_b231fe46): at alpha 255 none of that picture survives."""
    png = str(tmp_path / "overlay.png")
    builder.render_title_overlay(png)
    image = Image.open(png).convert("RGBA")
    assert image.size == (builder.FRAME_W, builder.FRAME_H)
    assert {pixel[3] for pixel in image.getdata()} == {255}, "the overlay is not opaque, so the old picture shows"
    law = image.convert("L")
    bright = {row["label"]: sum(1 for pixel in law.crop(tuple(row["box"])).getdata() if pixel >= 200)
              for row in builder.title_menu_boxes()}
    assert bright["NEW GAME"] >= 30, "NEW GAME drew no ink: %r" % (bright,)
    assert bright["CONTINUE"] <= max(5, int(0.1 * bright["NEW GAME"])), \
        "CONTINUE is not the dim row: %r" % (bright,)


def test_no_long_dash_anywhere(builder):
    for shot in builder.SHOTS:
        caption = builder.shot_caption(shot)
        for dash in LONG_DASHES:
            assert dash not in caption, "%s caption carries a long dash" % shot
    for line in builder.title_card_lines():
        for dash in LONG_DASHES:
            assert dash not in line, "a title card line carries a long dash"


def test_every_caption_fits_the_band(builder):
    usable = builder.FULL_W - 2 * builder.MARGIN
    for shot in builder.SHOTS:
        lines = builder._wrap(builder.shot_caption(shot), builder.CAPTION_SIZE, usable)
        assert len(lines) <= 2, "%s caption needs %d lines, the band holds 2" % (shot, len(lines))


def test_rendered_frames_carry_ink(builder, tmp_path):
    title_png = str(tmp_path / "title.png")
    builder.render_title_card(title_png)
    title = Image.open(title_png).convert("RGB")
    assert title.size == (builder.FULL_W, builder.FULL_H)
    white = sum(1 for pixel in title.getdata() if pixel == (255, 255, 255))
    assert white > 0, "the title card drew no white pixels"

    # The cold boot caption sits in the band below the scene, so that band must hold white ink too.
    band = title.crop((0, builder.FRAME_H, builder.FULL_W, builder.FULL_H))
    band_white = sum(1 for pixel in band.getdata() if pixel == (255, 255, 255))
    assert band_white > 0, "the title card's caption band drew no cold boot caption ink"

    for shot in builder.SHOTS:
        png = str(tmp_path / ("caption_%s.png" % shot))
        builder.render_caption_band(shot, png)
        band = Image.open(png)
        assert band.size == (builder.FULL_W, builder.BAND_H)
        alpha = sum(1 for pixel in band.getdata() if pixel[3] > 0)
        assert alpha > 0, "%s caption band drew no ink" % shot


def test_title_card_accepts_an_attract_background(builder, tmp_path):
    background = str(tmp_path / "attract.png")
    Image.new("RGB", (builder.FRAME_W, builder.FRAME_H), (10, 20, 30)).save(background)
    title_png = str(tmp_path / "title_bg.png")
    builder.render_title_card(title_png, background=background)
    title = Image.open(title_png).convert("RGB")
    assert title.size == (builder.FULL_W, builder.FULL_H)
    # The scene area is dimmed toward black, not replaced by it, so the attract frame is actually used.
    top = title.getpixel((0, 0))
    assert top != (0, 0, 0), "the title card did not use the attract background"
    white = sum(1 for pixel in title.getdata() if pixel == (255, 255, 255))
    assert white > 0, "the title card over an attract frame drew no white text"


def test_the_badge_is_the_measured_verdict_beside_the_nes_limits_line(builder):
    """Fix 5 (card t_1b404055): the card states the limit and the badge states that the build was measured
    against it. The numbers on the badge are tools/check_nes_limits.py's, read at draw time, never typed."""
    import check_nes_limits

    badge = builder.title_badge_box()
    measured = check_nes_limits.measure(builder.ROOT)
    assert badge["text"] == "PASS", badge
    assert badge["colours"] == measured["colours"], "the badge prints a count the check did not measure"
    assert badge["limit"] == check_nes_limits.COLOUR_LIMIT == 16
    assert measured["pass"], measured["failures"]

    line = next(item for item in builder._card_geometry()["lines"] if item["line"] == builder.NES_LIMITS_LINE)
    x0, y0, x1, y1 = badge["box"]
    assert x0 >= line["x"] + line["width"], "the badge does not sit to the right of the NES LIMITS line"
    assert y0 < line["y"] + line["height"] and y1 > line["y"], "the badge is not on the NES LIMITS line's band"
    assert x0 >= 0 and x1 <= builder.FRAME_W and y0 >= 0 and y1 <= builder.FRAME_H, badge["box"]


def test_the_badge_ink_is_on_the_rendered_card(builder, tmp_path):
    """A box in the layout is not a word on the picture: the badge's own rectangle is counted on the render."""
    png = str(tmp_path / "overlay_badge.png")
    builder.render_title_overlay(png)
    picture = Image.open(png).convert("L")
    ink = sum(1 for pixel in picture.crop(tuple(builder.title_badge_box()["box"])).getdata() if pixel >= 200)
    assert ink >= 100, "the PASS badge drew %d white pixels in its box" % ink


def test_a_failing_check_refuses_the_card(builder, monkeypatch, tmp_path):
    """A card cannot print PASS over a build that breaks the limit: the builder refuses instead."""
    import check_nes_limits

    failing = {"pass": False, "failures": ["the title screen can show 17 colours, and the limit is 16"],
               "frame": [256, 240], "colours": 17, "limit": 16, "colour_list": []}
    monkeypatch.setattr(check_nes_limits, "measure", lambda root=None: failing)
    builder._VERDICTS.clear()
    try:
        with pytest.raises(builder.BuilderError) as refused:
            builder.render_title_overlay(str(tmp_path / "no_badge.png"))
        assert "NES limits check fails" in str(refused.value)
    finally:
        builder._VERDICTS.clear()


def test_the_badge_survives_the_encoder_on_a_delivered_frame(builder, tmp_path):
    """A judge sees the badge on an mp4 frame, not on a render, so the card is encoded and the frame decoded.

    Fix 5 (card t_1b404055) asks for the badge on the title card in S1, and S1 is a delivered h264 file. A
    box in the layout proves nothing about that file, so the card is encoded at the cut's own size and the
    ink is counted inside the badge's rectangle on the decoded frame at 1.0 s.
    """
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg is not on PATH, so no frame can be encoded")
    card = str(tmp_path / "card.png")
    builder.render_title_card(card)
    video = str(tmp_path / "card.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "60", "-t", "2",
                    "-i", card, "-r", "60", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                    "-pix_fmt", "yuv420p", video], check=True, stdin=subprocess.DEVNULL, timeout=180)
    frame = str(tmp_path / "frame_1s.png")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "1.0", "-i", video, "-frames:v", "1", frame],
                   check=True, stdin=subprocess.DEVNULL, timeout=180)
    picture = Image.open(frame).convert("L")
    assert picture.size == (builder.FULL_W, builder.FULL_H), picture.size
    ink = sum(1 for pixel in picture.crop(tuple(builder.title_badge_box()["box"])).getdata() if pixel >= 200)
    assert ink >= 100, "the decoded frame carries %d white pixels in the badge's box" % ink
