"""tests for tools/judge_frames_check.py: the sampled times, the plate measure, and both verdicts.

Card t_4512b33a (JUDGE-FRAME-TEST). What is worth pinning here is everything that could let this
check pass a video it should have stopped:

  1. the six sampled times are the ones a judge has already been shown: 6.1, 18.4, 30.6, 42.9,
     55.1 and 67.4 s, which are `tools/judge_panel.py`'s own count=6 sample of the 73.483 s capture
     and are quoted in `knowledge/JUDGE-PANEL-2026-10-26.md` line 11;
  2. the three tail times (100, 130, 160 s) belong to a three minute cut and are skipped, with the
     reason stated, on a capture that is not that length;
  3. the caption font atlas matches a line `tools/demo_overlay.py` really drew (measured 0.98) and
     refuses a frame where no plate was drawn (measured 0.12), so the model name check cannot pass
     on game art;
  4. the paper share of a plate rect separates a drawn plate from the frame underneath it;
  5. the last three samples are called the same picture when they are, and differ when they do;
  6. on the real newest nightly the tool reaches a definite verdict and every finding names its
     frame times, because a failure a reader cannot locate is the failure this card was written for;
  7. the tool passes a capture built to hold every condition and fails one built to break two of
     them, which is the only proof that a PASS is reachable at all.

Tests 1 to 5 and 7 need no capture: they build their own pictures from `data/palette.json` and
`tools/demo_overlay.py`, so they run in a clean worktree where `output\\` is absent. Test 6 skips,
with the reason printed, when there is no nightly capture or no ffmpeg, because `output\\` is
gitignored and the gate on the Pine hosts may not carry ffmpeg. Test 7 is the slow one: it writes
about 210 synthetic frames and encodes two captures, around 25 s on the Windows host.
"""

from __future__ import annotations

import os
import shutil
import sys

import numpy as np
import pytest
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import demo_overlay  # noqa: E402
import judge_frames_check as jfc  # noqa: E402
import judge_panel  # noqa: E402

NIGHTLY_2026_10_26 = "nightly-2026-10-26.mp4"
TIME_IN_TEXT = r"\d+\.\d+ s"


# --------------------------------------------------------------------------- the times


def test_panel_times_reproduce_the_quoted_six():
    """The six times are not invented here: they are the panel's own sample of the 73.483 s capture.

    `judge_panel` keeps three decimals and prints one (`knowledge/JUDGE-PANEL-2026-10-26.md` line 11
    reads "6.1 s, 18.4 s, ..."), so the comparison is made at the one decimal the panel wrote.
    """
    assert [round(at, 1) for at in jfc.panel_times(73.483)] == [6.1, 18.4, 30.6, 42.9, 55.1, 67.4]
    assert jfc.SAMPLE_TIMES == (6.1, 18.4, 30.6, 42.9, 55.1, 67.4)


def test_sample_plan_skips_the_tail_times_on_a_short_capture():
    """100, 130 and 160 s are a three minute cut's frames and say nothing about a 73 s capture."""
    taken, skipped = jfc.sample_plan(73.483)
    assert [row["at_s"] for row in taken] == [6.1, 18.4, 30.6, 42.9, 55.1, 67.4]
    assert [row["at_s"] for row in skipped] == [100.0, 130.0, 160.0]
    assert all("180" in row["reason"] for row in skipped)


def test_sample_plan_adds_the_tail_times_at_the_judged_length():
    """At the judged length the three tail times are sampled, and each is labelled with its second."""
    taken, skipped = jfc.sample_plan(180.0)
    assert [row["at_s"] for row in taken] == [6.1, 18.4, 30.6, 42.9, 55.1, 67.4, 100.0, 130.0, 160.0]
    assert skipped == []


def test_sample_plan_never_samples_past_the_end():
    """A time after the last frame is skipped, never sampled: ffmpeg would hand back the last frame."""
    taken, skipped = jfc.sample_plan(165.0)
    assert 160.0 in [row["at_s"] for row in taken]
    taken, skipped = jfc.sample_plan(150.0)
    assert [row["at_s"] for row in skipped if row["at_s"] == 160.0]


# --------------------------------------------------------------------------- the plate and the atlas


def _base_frame():
    """A 768x720 picture with no plate on it, built from the palette the overlay itself uses.

    The plate's own `paper` colour is left out of the blocks on purpose: a base frame painted in it
    would put paper pixels under the plate rect and could not serve as the "no plate here" control
    this file measures against.
    """
    palette = demo_overlay.load_palette()
    paper = np.array(palette["paper"], dtype=np.int16)
    colours = [value for value in palette.values()
               if int(np.abs(np.array(value, dtype=np.int16) - paper).max()) > jfc.PAPER_TOL]
    image = Image.new("RGB", (demo_overlay.FRAME_W, demo_overlay.FRAME_H), colours[0])
    draw = ImageDraw.Draw(image)
    for row in range(0, demo_overlay.FRAME_H, 60):
        for column in range(0, demo_overlay.FRAME_W, 60):
            draw.rectangle([column, row, column + 59, row + 59],
                           fill=colours[(row // 60 * 5 + column // 60) % len(colours)])
    return image


def _rendered_plate(shot="S5"):
    bake, index = demo_overlay.load_bake()
    palette = demo_overlay.load_palette()
    image, plan = demo_overlay.render(_base_frame(), shot, bake, index, allow_fallback=True)
    model = str((bake.get("bake") or {}).get("model") or "")
    return np.asarray(image).astype(np.int16), plan, palette, model


def test_paper_share_separates_a_drawn_plate_from_the_frame_under_it():
    """Measured 0.77 on a rendered plate and 0.005 on the clean frame at the same rect."""
    frame, plan, palette, model = _rendered_plate("S5")
    drawn = jfc.plate_facts(frame, plan, model, palette)
    clean = jfc.plate_facts(np.asarray(_base_frame()).astype(np.int16), plan, model, palette)
    assert drawn["paper_share"] >= jfc.PLATE_PAPER_SHARE
    assert clean["paper_share"] < 0.10
    assert all(row["ink_share"] > 0 for row in drawn["lines"])


def test_atlas_matches_the_line_the_overlay_drew_and_refuses_a_frame_without_it():
    """The model name string is found at 0.98 where it was drawn, and at about 0.1 where it was not."""
    frame, plan, palette, model = _rendered_plate("S5")
    drawn = jfc.plate_facts(frame, plan, model, palette)
    assert drawn["model_line"]["text"] == "BAKE MODEL " + model
    assert drawn["model_line"]["iou"] >= 0.90
    clean = jfc.plate_facts(np.asarray(_base_frame()).astype(np.int16), plan, model, palette)
    assert clean["model_line"]["iou"] < jfc.ATLAS_IOU_MIN


def test_atlas_mask_is_the_glyph_ink_only():
    """A mask that kept its blank rows would reach into the line below and score a match at 0.46."""
    mask, (x, y) = jfc.atlas_mask("BAKE MODEL x", 12)
    assert mask.sum() > 0
    assert mask.shape[0] <= 12 + 1          # one glyph row, not the three row canvas
    assert (x, y) == (0, 0)


# --------------------------------------------------------------------------- the tail


def _frame_file(folder, name, colour=None, seed=0):
    image = _base_frame()
    draw = ImageDraw.Draw(image)
    draw.rectangle([40 + seed * 60, 40, 140 + seed * 60, 140], fill=(255, 255, 255))
    if colour:
        image = Image.new("RGB", image.size, colour)
    path = os.path.join(str(folder), name)
    image.save(path)
    return path


def test_difference_rows_call_identical_frames_the_same_picture(tmp_path):
    same_a = _frame_file(tmp_path, "a.png", seed=1)
    same_b = _frame_file(tmp_path, "b.png", seed=1)
    other = _frame_file(tmp_path, "c.png", seed=4)
    frames = [{"at_s": 42.9, "path": same_a}, {"at_s": 55.1, "path": same_b},
              {"at_s": 67.4, "path": other}]
    rows = jfc.difference_rows(frames)
    assert len(rows) == 3
    by_pair = {row["pair"]: row for row in rows}
    assert by_pair["42.9 s and 55.1 s"]["differ_share"] == 0.0
    assert by_pair["42.9 s and 55.1 s"]["ok"] is False
    assert by_pair["55.1 s and 67.4 s"]["ok"] is True


# --------------------------------------------------------------------------- the real capture


def test_the_newest_nightly_reaches_a_verdict_and_names_its_frame_times():
    """A finding a reader cannot locate is the failure this card exists to stop."""
    video = judge_panel.newest_nightly()
    if not video or not os.path.exists(video):
        pytest.skip("no nightly capture under output/demo, and output/ is gitignored")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg or ffprobe is not on PATH, so no frame can be taken")
    report = jfc.check(video, folder=os.path.join(ROOT, "output", "_judge_frames_test"), log=False)
    assert report["duration_s"]
    assert len(report["frames"]) >= 6
    assert all(row["largest_colour_share"] is not None for row in report["frames"])
    assert report["ok"] in (True, False)
    for text in report["failures"]:
        assert " s" in text
        assert any(piece in text for piece in ("blank", "S5", "S6", "frames differ"))
    printed = jfc.render_report(report)
    assert "\u2014" not in printed and "\u2013" not in printed


def test_the_2026_10_26_capture_is_a_fail_with_the_two_blank_times():
    """The card's own check: this capture has two blank frames and no bake row, and both are named."""
    video = judge_panel.newest_nightly()
    if not video or os.path.basename(video) != NIGHTLY_2026_10_26:
        pytest.skip("the newest nightly is not the 2026-10-26 capture this check was written on")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg or ffprobe is not on PATH, so no frame can be taken")
    report = jfc.check(video, folder=os.path.join(ROOT, "output", "_judge_frames_test"), log=False)
    assert report["ok"] is False
    text = " ".join(report["failures"])
    assert "18.4 s" in text and "30.6 s" in text
    assert "S5" in text and "S6" in text


# --------------------------------------------------------------------------- the nightly row


def test_the_nightly_row_is_one_line_with_the_verdict(tmp_path):
    report = {"video": os.path.join(ROOT, "output", "demo", "x.mp4"), "ok": False, "exit": 1,
              "frames": [{"at_s": 6.1, "largest_colour_share": 0.2, "blank": False},
                         {"at_s": 18.4, "largest_colour_share": 1.0, "blank": True}],
              "receipt_shots": [], "difference": [{"pair": "a and b", "differ_share": 0.0, "ok": False}],
              "failures": ["blank: 1 of 2 sampled frames are one colour over 90 percent: 18.4 s at 1.000"]}
    path = tmp_path / "DEMO-NIGHTLY.md"
    row = jfc.append_nightly_row(report, str(path))
    assert "\n" not in row
    assert "judge-frames" in row and "JUDGE-FRAMES FAIL" in row
    assert path.read_text(encoding="utf-8").strip() == row
    assert "\u2014" not in row and "\u2013" not in row


# --------------------------------------------------------------------------- both directions


def test_self_test_passes_the_good_capture_and_fails_the_broken_one():
    """The only proof a PASS is reachable: a capture with every condition, and one with it broken."""
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg or ffprobe is not on PATH, so no capture can be built")
    folder = os.path.join(ROOT, "output", "_judge_frames_pytest")
    result = jfc.self_test(folder=folder)
    assert result["good"]["ok"] is True
    assert result["broken"]["ok"] is False
    text = " ".join(result["broken"]["failures"])
    assert "18.4 s" in text and "30.6 s" in text
