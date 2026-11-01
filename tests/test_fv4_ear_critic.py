"""Tests for the FV-4 ear critic comparison harness (card t_c58b790f).

These pin the harness's own arithmetic and its matched-input promise, not the musical verdict:
the verdict lives in manager/formal/FV-4-ear-critic.md with its raw numbers. Fast by design: the
only solver call is one eight-position texture.
"""

from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CP = os.path.join(ROOT, "tools", "counterpoint")
for path in (CP, os.path.join(ROOT, "tools")):
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    import fv4_ear_critic as harness  # noqa: E402
    import generate  # noqa: E402
except ModuleNotFoundError as error:  # pragma: no cover - the gate tree has no M1b baseline
    pytest.skip(
        "harness dependency missing (%s): tools/counterpoint/generate.py is the M1b baseline "
        "(card t_944ef2b6) and is not in git at HEAD, so a tree built from HEAD plus this card's "
        "files cannot run the comparison. In the live tree the file is present and all tests run."
        % error, allow_module_level=True)


def test_subject_is_deterministic_and_one_pitch_per_position():
    first = harness.subject_for_seed(7)
    second = harness.subject_for_seed(7)
    assert first == second
    assert len(first) == harness.POSITIONS
    assert [slot for slot, _duration, _pitch in first] == list(range(harness.POSITIONS))
    assert all(duration == 1 for _slot, duration, _pitch in first)
    pitches = [pitch for _slot, _duration, pitch in first]
    assert min(pitches) >= 64 and max(pitches) <= 79
    # A different seed must not hand the two engines the same spec by accident.
    assert harness.subject_for_seed(8) != first


def test_contour_stats_separates_steps_leaps_and_repeats():
    line = [(0, 1, 60), (1, 1, 62), (2, 1, 62), (3, 1, 67), (4, 1, 60)]
    stats = harness.contour_stats(line)
    assert stats["notes"] == 5
    assert stats["range"] == 7
    assert stats["max_leap"] == 7
    assert stats["repeat_share"] == pytest.approx(0.25)
    assert stats["step_share"] == pytest.approx(0.25)
    assert stats["leap_share"] == pytest.approx(0.5)
    assert stats["mean_abs_interval"] == pytest.approx(3.5)
    assert stats["distinct_pitches"] == 3


def test_contour_stats_on_a_flat_line_does_not_divide_by_zero():
    stats = harness.contour_stats([(0, 1, 60)])
    assert stats["notes"] == 1
    assert stats["leap_share"] == 0.0
    assert stats["longest_run"] == 0


def test_rule_block_names_the_parallel_fifth_it_measures():
    # Pulse 1 and pulse 2 a perfect fifth apart, moving in parallel: CP-09 by construction.
    lines = {"pulse 1": [(slot, 1, 72 + slot) for slot in range(4)],
             "pulse 2": [(slot, 1, 65 + slot) for slot in range(4)]}
    block = harness.rule_block(lines, "free")
    assert block["by_severity"].get("hard", 0) >= 1
    assert block["by_rule"].get("CP-09", 0) >= 1
    assert block["bars"] == 1


def test_solve_texture_honours_its_pins():
    pins = {"pulse 1": [(0, 1, 72), (1, 1, 74), (2, 1, 76), (3, 1, 77)]}
    result = harness.solve_texture(pins=pins, positions=8, timeout_ms=30000)
    assert result["status"] == "sat"
    assert result["model"]["pulse 1"][:4] == [72, 74, 76, 77]
    assert len(result["model"]["pulse 2"]) == 8


def test_guided_budget_caps_the_generated_voice_only():
    pins = {"pulse 1": [(0, 1, 72), (1, 1, 74), (2, 1, 76), (3, 1, 77)]}
    result = harness.solve_texture(pins=pins, positions=8, guided=True, max_leap=3,
                                   timeout_ms=60000)
    assert result["status"] == "sat"
    alto = result["model"]["pulse 2"]
    for a, b in zip(alto, alto[1:]):
        assert abs(b - a) <= 3
    # The pinned subject keeps its own leaps: the budget is not applied to the spec.
    assert result["model"]["pulse 1"] == [72, 74, 76, 77, result["model"]["pulse 1"][4],
                                          result["model"]["pulse 1"][5],
                                          result["model"]["pulse 1"][6],
                                          result["model"]["pulse 1"][7]]


def test_clash_dose_uses_the_ear_loop_formula(monkeypatch):
    fake = {"raw_total": 10, "strong_raw": 4, "by_class": {}, "bars": 2}

    class FakeScore(object):
        bars = 2

    monkeypatch.setattr(harness.clash, "load_score", lambda path, key_name=None: FakeScore())
    monkeypatch.setattr(harness.clash, "analyse", lambda score: [])
    monkeypatch.setattr(harness.clash, "summarise", lambda score, events: dict(fake))
    block = harness.clash_block("unused.mid")
    # (4 + 0.1 * (10 - 4)) / 2 bars = 2.3 per bar
    assert block["dose_per_bar"] == pytest.approx(2.3)


def test_mean_variance_reports_n_so_a_small_sample_is_visible():
    assert harness.mean_variance([]) == {"n": 0, "mean": None, "variance": None}
    assert harness.mean_variance([5.0]) == {"n": 1, "mean": 5.0, "variance": 0.0}
    stats = harness.mean_variance([1.0, 3.0])
    assert stats["n"] == 2 and stats["mean"] == 2.0 and stats["variance"] == 2.0


def test_smf_lines_use_the_grid_both_engines_build_on():
    lines = {"pulse 1": [(0, 1, 72), (1, 2, 74)], "pulse 2": [(0, 1, 60)]}
    smf = harness.to_smf_lines(lines)
    assert smf["pulse 1"][0] == (0, generate.EIGHTH, 72, 96)
    assert smf["pulse 1"][1] == (generate.EIGHTH, 3 * generate.EIGHTH, 74, 96)
