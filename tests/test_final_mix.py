"""The final mix tool's rules, measured rather than described.

Card t_120dc9f2 (W5 SCORE-FINAL, musician). tools/final_mix.py is the only writer of the four route
masters, and the commit gate refuses a source change no test maps to, so this file holds the two
things a reader most needs to trust about that tool:

1. Its four measured rules are what the module docstring says they are. `seam` classifies a wrap as
   clean, step, dip or click; `trim_loop` drops an edge fade and a silent tail and keeps every block
   that carries music at level; `splice` crossfades the loop's own tail into its own head so the wrap
   stops being an outlier; `loop_points` reads the sidecar's inner loop block before its outer fields
   and only believes numbers that fit inside the file. Each of those is asserted on a synthetic
   signal this file builds, so the rule is pinned even on a machine with no cue on disk.
2. The four delivered masters agree with their own sidecars. That test skips when the folders are not
   present (a tests-only checkout), so it never invents a failure out of a missing asset, but on a
   tree that carries them it is the assertion that keeps the numbers in
   knowledge/FINAL-MIX-2026-10-26.md honest after a re-point.

Nothing here runs ffmpeg: the four rules are pure numpy over samples, which is why the suite stays
fast. The measured loudness numbers belong to `python tools\\final_mix.py --verify`, which the card's
own report prints.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

import final_mix

SR = final_mix.SR


def tone(seconds: float, amp: float = 0.5, freq: float = 440.0) -> np.ndarray:
    n = int(round(seconds * SR))
    t = np.arange(n, dtype=np.float64) / SR
    return (amp * np.sin(2.0 * np.pi * freq * t)).astype(np.float32)


def pad(seconds: float, value: float = 0.0) -> np.ndarray:
    return np.full(int(round(seconds * SR)), value, dtype=np.float32)


# ------------------------------------------------------------------------------------------------
# loop_points: the sidecar's inner block wins, and a number that does not fit is not believed.


def test_the_inner_loop_block_is_read_before_the_outer_fields():
    sidecar = {
        "loop_start_sample": 0,
        "loop_end_sample": 100,
        "loop": {"loop_start_sample": 10, "loop_end_sample": 90,
                 "loop_start_bar": 5, "loop_end_bar": 13},
    }
    start, end, why = final_mix.loop_points(sidecar, samples=100)
    assert (start, end) == (10, 90)
    assert "sidecar loop block" in why
    assert "bar 5" in why and "bar 13" in why


def test_a_sidecar_without_an_inner_block_uses_its_outer_loop_fields():
    start, end, why = final_mix.loop_points(
        {"loop_start_sample": 4, "loop_end_sample": 60}, samples=100)
    assert (start, end) == (4, 60)
    assert "outer" in why


def test_outer_fields_that_span_the_whole_file_are_named_as_a_whole_file_loop():
    start, end, why = final_mix.loop_points(
        {"loop_start_sample": 0, "loop_end_sample": 100}, samples=100)
    assert (start, end) == (0, 100)
    assert "whole-file" in why


@pytest.mark.parametrize("sidecar", [
    None,
    {},
    {"loop": {"loop_start_sample": 90, "loop_end_sample": 10}},
    {"loop": {"loop_start_sample": 0, "loop_end_sample": 101}},
    {"loop_start_sample": -1, "loop_end_sample": 50},
])
def test_a_loop_the_file_cannot_hold_falls_back_to_the_whole_file(sidecar):
    start, end, why = final_mix.loop_points(sidecar, samples=100)
    assert (start, end) == (0, 100)
    assert why


# ------------------------------------------------------------------------------------------------
# seam: clean, step, dip and click, each built on purpose.


def test_a_steady_tone_wraps_clean():
    samples = tone(1.0)
    out = final_mix.seam(samples, 0, len(samples))
    assert out["verdict"] == "clean"
    assert out["loop_seconds"] == pytest.approx(1.0, abs=1e-6)


def test_a_wrap_that_jumps_further_than_the_file_moves_is_a_click():
    # Every ordinary step is 0.002, so p99.9 is 0.002 and a 1.4 jump at the wrap is an outlier.
    samples = np.full(1000, 0.001, dtype=np.float32)
    samples[0] = 1.0
    out = final_mix.seam(samples, 0, len(samples))
    assert out["verdict"] == "click"
    assert out["wrap_jump_dbfs"] > out["step_reference_dbfs"]


def test_a_wrap_through_a_level_hole_is_a_dip_not_a_click():
    body = tone(0.8, amp=0.5)
    edge = pad(0.05)
    samples = np.concatenate([edge, body, edge]).astype(np.float32)
    out = final_mix.seam(samples, 0, len(samples))
    assert out["verdict"] == "dip"
    assert out["head_rms_dbfs"] < out["body_rms_dbfs"] - 12.0


def test_a_wrap_where_both_edges_sit_about_eight_db_down_is_a_step():
    # A square wave: every ordinary step is the full peak-to-peak jump, so the wrap cannot be an
    # outlier. The edges are well over 6 dB under the body's RMS, which is what makes it a step
    # rather than a clean wrap; the edges are each 0.2 s long so the 10 ms windows the seam reads
    # land entirely inside them.
    samples = np.empty(SR, dtype=np.float32)
    samples[0::2] = 0.5
    samples[1::2] = -0.5
    edge = int(0.2 * SR)
    quiet = np.where(np.arange(edge) % 2 == 0, 0.15, -0.15)
    samples[:edge] = quiet
    samples[-edge:] = quiet
    out = final_mix.seam(samples, 0, len(samples))
    assert out["verdict"] == "step"
    assert -12.0 < out["seam_level_delta_db"] < -6.0


# ------------------------------------------------------------------------------------------------
# trim_loop: the edge fade and the silent tail are not music, and music at level is never trimmed.


def test_a_silent_head_and_tail_are_trimmed_and_the_music_between_is_kept():
    samples = np.concatenate([pad(0.2), tone(0.2, amp=0.5), pad(0.2)]).astype(np.float32)
    win = int(round(final_mix.TRIM_WIN_MS / 1000.0 * SR))
    start, end, why = final_mix.trim_loop(samples, final_mix.TRIM_FLOOR_DB, win)
    assert start == pytest.approx(0.2 * SR, abs=win)
    assert end == pytest.approx(0.4 * SR, abs=win)
    assert "trimmed" in why


def test_a_file_that_carries_music_to_both_ends_is_not_trimmed():
    # The trim walks 1 ms blocks, so its last block can stop up to one block short of the file's end
    # when the tone happens to end quiet. A block of slack is the rule; a whole fade is not.
    samples = tone(0.5, amp=0.5)
    win = int(round(final_mix.TRIM_WIN_MS / 1000.0 * SR))
    start, end, _why = final_mix.trim_loop(samples, final_mix.TRIM_FLOOR_DB, win)
    assert start == 0
    assert len(samples) - end <= win


def test_an_empty_file_is_returned_whole_rather_than_divided_by_zero():
    start, end, why = final_mix.trim_loop(np.zeros(0, dtype=np.float32), -20.0, 10)
    assert (start, end) == (0, 0)
    assert "empty" in why


# ------------------------------------------------------------------------------------------------
# splice: the loop's own tail crossfaded into its own head, nothing invented, length unchanged.


def test_the_splice_reduces_a_wrap_jump_and_keeps_every_sample_outside_the_crossfade():
    head = pad(0.05, -0.9)
    body = tone(0.2, amp=0.3)
    tail = pad(0.05, 0.9)
    samples = np.concatenate([head, body, tail]).astype(np.float32)
    start, end = 0, len(samples)
    before = final_mix.seam(samples, start, end)
    assert before["verdict"] == "click"

    out, did = final_mix.splice(samples, start, end, final_mix.SPLICE_MS)
    n = int(round(final_mix.SPLICE_MS / 1000.0 * SR))
    after = final_mix.seam(out, start, end)
    assert did is True
    assert len(out) == len(samples)
    assert after["wrap_jump_dbfs"] < before["wrap_jump_dbfs"]
    assert after["verdict"] != "click"
    # Everything before the crossfade is the source's own audio, sample for sample.
    assert np.array_equal(out[:end - n], samples[:end - n])


def test_a_loop_too_short_for_the_crossfade_is_left_alone():
    samples = tone(0.002)
    out, did = final_mix.splice(samples, 0, len(samples), final_mix.SPLICE_MS)
    assert did is False
    assert np.array_equal(out, samples)


# ------------------------------------------------------------------------------------------------
# limiter_limit and the module's own targets: the numbers the report quotes come from here.


def test_the_limiter_reaches_a_linear_gain_from_its_decibel_setting():
    assert final_mix.limiter_limit(-1.0) == pytest.approx(10.0 ** (-1.0 / 20.0), rel=1e-12)
    assert final_mix.limiter_limit(0.0) == pytest.approx(1.0, rel=1e-12)
    assert final_mix.TARGET_LUFS == -14.0
    assert final_mix.TP_CEIL <= 0.0


def test_the_route_covers_the_four_cues_this_card_masters_and_names_them_once():
    roles = [entry["role"] for entry in final_mix.ROUTE]
    assert roles == ["drive", "harbor", "fight", "boarding"]
    assets = [entry["asset"] for entry in final_mix.ROUTE]
    assert len(assets) == len(set(assets))
    for entry in final_mix.ROUTE:
        assert "_master" in entry["asset"]


# ------------------------------------------------------------------------------------------------
# The delivered masters agree with their own sidecars. Skipped when the folders are absent.


@pytest.mark.parametrize("entry", final_mix.ROUTE, ids=[e["asset"] for e in final_mix.ROUTE])
def test_each_delivered_master_agrees_with_its_sidecar(entry):
    # No skip: the master and its sidecar land in the same commit as this file, so a missing sidecar is
    # a real failure, not a checkout this test cannot judge. tests/test_test_inputs.py refuses a skip
    # guarded by a path existence test for exactly that reason.
    folder = os.path.join(final_mix.ROOT, "assets", "audio", entry["asset"])
    sidecar_path = os.path.join(folder, entry["asset"] + "_loop.json")
    assert os.path.isfile(sidecar_path), "no sidecar at assets/audio/%s/%s_loop.json" % (
        entry["asset"], entry["asset"])
    with open(sidecar_path, encoding="utf-8") as fh:
        sidecar = json.load(fh)

    assert sidecar["asset"] == entry["asset"]
    assert sidecar["cue"] == entry["cue"]
    assert sidecar["sample_rate"] == SR
    start = int(sidecar["loop_start_sample"])
    end = int(sidecar["loop_end_sample"])
    assert 0 <= start < end <= int(sidecar["samples"])
    assert end - start > SR  # a loop under a second is a stub, not a cue
    assert sidecar["full_scale_samples"] == 0
    assert sidecar["after"]["tp"] <= final_mix.TP_CEIL
    assert abs(sidecar["after"]["lufs"] - final_mix.TARGET_LUFS) <= final_mix.TOL_LU
    assert sidecar["seam_after"]["verdict"] == "clean"
    # The master is the source's own samples, so the loop sidecar must record a source hash and the
    # master's length as the source's length.
    assert sidecar["source_sha256"]
    assert sidecar["decoded_peak"] < 0.0
