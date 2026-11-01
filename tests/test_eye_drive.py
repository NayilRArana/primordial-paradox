"""tests for tools/eye_drive.py: the twelve shot sampler, the PPU numbers, and the model chain.

Card GEMINI-EYE-DRIVE (t_4bf72d3b). Three things are worth pinning, because each one is a way the
report could quietly become fiction:

  1. the sample is one frame per shot, at 256x240, and a missing capture is a FAILED shot rather
     than a skipped row (the card asks for twelve verdicts);
  2. the legality numbers come from the project's own checker, so a frame the checker fails cannot
     be reported as legal because a model liked it;
  3. the model chain moves to the next model on a per-day quota refusal instead of failing the run,
     proved against a fake transport that answers the real 429 body.

WHERE THE TWELVE FRAMES COME FROM, and why they are committed (decision taken 2026-10-24, card
t_d2c52f15). The input is output/drive/pp_drive_shot_01.png to _12.png, 768x720 captures that the
game writes from inside its own draw; only a GameMaker run produces them, so this test cannot make
them and must not pretend to. They are therefore committed, un-ignored by name in .gitignore and
listed one by one in tools/check_test_inputs.py FIXTURES, which is what makes a clean checkout
measure twelve real frames instead of reporting twelve failed shots. The alternative, a skip or a
note saying the row only runs on a capture machine, was refused: a row that cannot run where the
suite runs is the same silent pass this project already forbids in check_test_inputs.py. Nothing
in the assertions below was relaxed to allow this; the frames are the test's input, not a preview.
"""

from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import eye_drive  # noqa: E402
import nes_composite_check as nes  # noqa: E402


@pytest.fixture(scope="module")
def palette():
    return nes.load_palette(eye_drive.PALETTE_PATH)


@pytest.fixture(scope="module")
def rows():
    return eye_drive.sample_frames()


def assert_the_captures_are_here(rows):
    """Fail with the cause named, not with the traceback an open() or the sampler raises.

    eye_drive.sample_frames() turns output\\drive\\pp_drive_shot_01.png to _12.png into the 256x240
    copies under output\\drive_frames\\, and the rows that measure or review a frame read those
    copies. Only a GameMaker run makes a capture, so on a tree that lacks them no frame is written
    and the red arrives as `FileNotFoundError: .../drive_frames/drive_shot_01.png` from Image.open
    or as eye_drive.self_test's `run the sampler first` EyeError. Neither one says where the file
    was meant to come from, which is how a by-product dependency hides (card t_4321ea51).
    Whatever is absent here is named, and nothing is skipped: the row still fails.
    """
    missing = [row["n"] for row in rows if not row.get("capture")]
    assert not missing, (
        "shots %s have no capture under output/drive/, so sample_frames() wrote no frame to measure. "
        "The input is output/drive/pp_drive_shot_01.png to _12.png, twelve 768x720 captures that only "
        "a GameMaker run makes; they are un-ignored by name in .gitignore, listed in "
        "tools/check_test_inputs.py FIXTURES and committed by card t_d2c52f15, and pine_offload.py "
        "OUTPUT_KEEP_PREFIXES carries output/drive/ and output/drive_frames/ so Pine has them too. "
        "A tree without them is a capture run away from green, not a code failure." % missing)


def test_one_frame_per_shot_and_twelve_of_them(rows):
    assert len(rows) == 12
    assert [row["n"] for row in rows] == list(range(1, 13))
    missing = [row for row in rows if row.get("error")]
    assert not missing, "shots without a captured frame: %s" % [row["n"] for row in missing]
    for row in rows:
        assert os.path.exists(row["frame"]), row["frame"]
        assert row["capture"]["source_size"] == [768, 720]
        assert row["capture"]["scale"] == 3
        with open(row["frame"], "rb") as handle:
            assert handle.read(8) == b"\x89PNG\r\n\x1a\n"


def test_every_shot_row_carries_the_shot_list_description(rows):
    for row in rows:
        assert row["shows"], "shot %d has no description from DRIVE-SHOT-LIST" % row["n"]
        assert row["location"]
    # The four gantry signs, from DRIVE-SHOT-LIST section 5.
    signs = {row["n"]: row["sign"] for row in rows if row["sign"]}
    assert signs == {3: "55", 6: "43", 9: "30", 11: "20"}


def test_measurement_reports_colours_and_attribute_areas(rows, palette):
    assert_the_captures_are_here(rows)
    for row in rows[:3]:
        measured = eye_drive.measure(row, palette)
        assert measured["size"] == [256, 240]
        assert measured["colours"] >= 1
        assert measured["off_palette_colours"] >= 0
        assert measured["attribute_areas_over"] >= 0
        assert isinstance(measured["legal"], bool)
        # The two halves must agree: a frame with a colour the PPU cannot output is not legal.
        if measured["off_palette_colours"]:
            assert measured["legal"] is False, "an off-palette frame cannot pass legality"


def test_measure_never_asks_pillow_for_a_table_bigger_than_the_frame(tmp_path, palette, monkeypatch):
    """eye_drive.measure is the half of a shot's verdict that is quoted as measured, so pin its ask.

    Pillow sizes the table behind getcolors() from maxcolors rather than from the picture, so the
    fixed `getcolors(1 << 24)` this tool used until card t_fb343601 asked for 16,777,216 entries on
    every 256x240 frame: +521.0 MB of peak working set against +10.0 MB for the bounded call,
    measured on CitadelArana 2026-10-30 (539.1 MB on 2026-10-27), and a MemoryError from
    PIL/Image.py on a box with less free memory (cards t_f4d1c2d1 and t_83a4acad). The same wrap
    proves the answer did not change: every pixel of this frame holds its own colour, so the count
    is the frame's pixel count either way.
    """
    from PIL import Image

    path = tmp_path / "frame.png"
    frame = Image.new("RGB", (256, 240))
    for y in range(240):
        for x in range(256):
            frame.putpixel((x, y), (x, y, (x * y) % 256))
    frame.save(str(path), "PNG")
    asks = []
    original = Image.Image.getcolors

    def watched(self, maxcolors=256):
        asks.append((self.width * self.height, maxcolors))
        return original(self, maxcolors)

    monkeypatch.setattr(Image.Image, "getcolors", watched)
    measured = eye_drive.measure({"n": 1, "frame": str(path)}, palette)
    assert asks, "no getcolors call reached Pillow, so this row proved nothing"
    for capacity, maxcolors in asks:
        assert maxcolors <= capacity, (
            "getcolors asked for %d entries on a %d pixel frame" % (maxcolors, capacity))
    assert measured["colours"] == 256 * 240, measured["colours"]


def test_verdict_cannot_pass_on_a_legal_failure():
    measured = {"legal": False, "colours": 8, "off_palette_colours": 8}
    good_review = {"scores": {"nes": 9, "readability": 9, "charm": 9}}
    verdict = eye_drive.verdict_for({"n": 1}, measured, good_review)
    assert verdict["legality"] == "FAIL"
    assert verdict["art"] == "PASS"
    assert verdict["overall"] == "FAIL", "a model score must never rescue an illegal frame"


def test_verdict_bands_and_the_unjudged_case():
    legal = {"legal": True}
    assert eye_drive.verdict_for({"n": 1}, legal, {"scores": {"nes": 8, "readability": 7,
                                                              "charm": 6}})["overall"] == "PASS"
    assert eye_drive.verdict_for({"n": 1}, legal, {"scores": {"nes": 6, "readability": 7,
                                                              "charm": 6}})["overall"] == "REVISE"
    assert eye_drive.verdict_for({"n": 1}, legal, {"scores": {"nes": 4, "readability": 7,
                                                              "charm": 6}})["overall"] == "FAIL"
    assert eye_drive.verdict_for({"n": 1}, legal, None)["overall"] == "NOT JUDGED"


def test_model_chain_falls_back_on_a_per_day_quota_refusal(tmp_path, rows):
    """The behaviour the report claims, driven with the API's own per-day 429 body."""
    os.environ.setdefault("PP_EYE_MAX_PER_MINUTE", "20")
    # self_test reviews output\drive_frames\drive_shot_01.png, which it does not create itself:
    # the `rows` fixture above is what samples it. Name the missing input instead of letting the
    # sampler's own guard raise first (card t_4321ea51).
    assert_the_captures_are_here(rows)
    result = eye_drive.self_test(str(tmp_path / "selftest"))
    assert result["refused"] == eye_drive.MODEL_CHAIN[0]
    assert result["answered"] == eye_drive.MODEL_CHAIN[1]
    assert "quota refusal" in result["verdict"]


def test_the_quota_body_names_a_per_day_limit():
    """The self test is only honest if its 429 is the daily shape eye_critic refuses to retry."""
    assert eye_critic_daily_quota(eye_drive.QUOTA_BODY)


def eye_critic_daily_quota(body):
    sys.path.insert(0, TOOLS)
    import eye_critic
    return eye_critic._daily_quota(body) and "PerDay" in body
