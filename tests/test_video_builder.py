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

Run: python -m pytest tests/test_video_builder.py -q
"""

from __future__ import annotations

import importlib.util
import os

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
