"""Tests for card t_836dbb1a (M1a): the counterpoint rules engine and the checker's verdict.

Every rule gets a textbook case that must fire and a neighbour of that case that must not, so a
rule cannot be satisfied by widening it until it fires on everything. The scores are built in
memory from note lists, one voice per line, so the arithmetic of bar, beat and interval in each
test is visible in the test rather than in a fixture file.

The verdict tests are separate: they check the gate, not the rules. A cue passes when every rule is
inside the Bach budget for its severity and fails when one rule is over it, which is the whole
point of calibrating against the corpus.
"""

from __future__ import annotations

import os
import sys

import pytest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COUNTERPOINT = os.path.join(TOOLS, "tools", "counterpoint")
for path in (COUNTERPOINT,):
    if path not in sys.path:
        sys.path.insert(0, path)

import check  # noqa: E402  (needs the tools/counterpoint path above)
import rules  # noqa: E402

BEAT = 480


def voice(*entries):
    """Turn (pitch, start beat, length in beats) into rules.Note objects."""
    notes = []
    for pitch, start, length in entries:
        notes.append(rules.Note(int(start * BEAT), int((start + length) * BEAT), pitch, 96))
    return notes


def score_of(**voices):
    """A score from voice name to note entries, in C major unless a test says otherwise."""
    key = voices.pop("key", "C major")
    time_sig = voices.pop("time_sig", (4, 4))
    parts = {name: notes for name, notes in voices.items()}
    return rules.Score(parts, division=BEAT, time_sig=time_sig, key=rules.parse_key(key))


def found(score, rule, profile="free"):
    """The findings for one rule, in order."""
    result = rules.analyse(score, profile=profile)
    return [f for f in result["findings"] if f["rule"] == rule]


# -- the interval arithmetic the rules stand on --------------------------------------------


def test_interval_numbers_are_counted_the_way_a_textbook_counts_them():
    assert [rules.interval_number(n) for n in (0, 2, 4, 5, 7, 9, 12, 14, 21)] == [1, 2, 3, 4, 5, 6, 8, 9, 13]
    assert rules.simple_number(9) == 2      # a ninth above the bass is a second
    assert rules.simple_number(10) == 3     # and a tenth is a third
    assert rules.simple_number(12) == 5
    assert rules.simple_number(8) == 8      # the octave is not reduced


def test_a_fourth_above_the_bass_is_dissonant_unless_a_sixth_or_third_supports_it():
    bare = score_of(upper=voice((65, 0, 1)), lower=voice((60, 0, 1)))
    supported = score_of(upper=voice((65, 0, 1)), middle=voice((69, 0, 1)), lower=voice((60, 0, 1)))
    assert rules.six_four_supported(bare.sounding(0), 60) is False
    assert rules.six_four_supported(supported.sounding(0), 60) is True


def test_the_metric_weight_of_a_beat_is_read_from_the_metre():
    four = score_of(upper=voice((67, 0, 4)), lower=voice((60, 0, 4)))
    three = score_of(upper=voice((67, 0, 3)), lower=voice((60, 0, 3)), time_sig=(3, 4))
    assert [four.accent(tick) for tick in (0, BEAT, 2 * BEAT, 3 * BEAT, BEAT // 2)] == [
        "strong", "weak", "medium", "weak", "offbeat"]
    assert [three.accent(tick) for tick in (0, BEAT, 2 * BEAT)] == ["strong", "weak", "weak"]


# -- the dissonance rules ------------------------------------------------------------------


def test_cp01_an_accented_dissonance_that_leaves_by_leap_is_a_finding():
    failing = score_of(upper=voice((65, 0, 1), (69, 1, 3)), lower=voice((60, 0, 4)))
    passing = score_of(upper=voice((69, 0, 1), (72, 1, 3)), lower=voice((60, 0, 4)))
    assert [f["detail"] for f in found(failing, "CP-01")] == [
        "F4 is dissonant against lower on a strong beat and leaves to A4, not by step"]
    assert found(passing, "CP-01") == []


def test_cp02_a_weak_dissonance_that_repeats_instead_of_moving_on_is_a_finding():
    failing = score_of(upper=voice((64, 0.5, 0.5), (65, 1, 0.5), (65, 1.5, 0.5)),
                       lower=voice((60, 0, 4)))
    passing = score_of(upper=voice((64, 0.5, 0.5), (65, 1, 0.5), (67, 1.5, 0.5)),
                       lower=voice((60, 0, 4)))
    assert [f["rule"] for f in found(failing, "CP-02")][0] == "CP-02"
    assert "is repeated rather than resolved" in found(failing, "CP-02")[0]["detail"]
    assert found(passing, "CP-02") == []


def test_cp04_a_prepared_held_note_that_does_not_resolve_down_by_step_is_a_finding():
    failing = score_of(upper=voice((72, 0, 2), (76, 2, 2)), lower=voice((57, 0, 1), (58, 1, 3)))
    passing = score_of(upper=voice((72, 0, 2), (71, 2, 2)), lower=voice((57, 0, 1), (58, 1, 3)))
    hits = found(failing, "CP-04")
    assert len(hits) == 1
    assert hits[0]["evidence"]["prepared"] is True
    assert hits[0]["evidence"]["step_out"] == 4
    assert found(passing, "CP-04") == []


def test_cp05_a_suspension_figure_outside_the_textbook_set_is_a_style_note():
    failing = score_of(upper=voice((74, 0, 2), (73, 2, 2)), lower=voice((65, 0, 1), (60, 1, 3)))
    passing = score_of(upper=voice((74, 0, 2), (72, 2, 2)), lower=voice((65, 0, 1), (60, 1, 3)))
    hits = found(failing, "CP-05")
    assert len(hits) == 1 and hits[0]["severity"] == "style"
    assert hits[0]["evidence"]["figure"] == "9-9"
    assert not rules.figure_is_canonical("9-9")
    assert rules.figure_is_canonical("9-8")       # the compound form of 2-8
    assert rules.figure_is_canonical("14-13")     # the compound form of 7-6
    assert found(passing, "CP-05") == []


def test_cp06_an_appoggiatura_is_a_style_note_and_a_passing_tone_is_not():
    failing = score_of(upper=voice((69, 0, 1), (65, 1, 1), (64, 2, 2)), lower=voice((60, 0, 4)))
    passing = score_of(upper=voice((69, 0, 1), (67, 1, 0.5), (65, 1.5, 0.5), (64, 2, 2)),
                       lower=voice((60, 0, 4)))
    hits = found(failing, "CP-06")
    assert len(hits) == 1 and hits[0]["severity"] == "style"
    assert "enters by leap" in hits[0]["detail"]
    assert found(passing, "CP-06") == []


def test_cp07_a_dissonance_entered_and_left_by_leap_is_a_hard_finding():
    failing = score_of(upper=voice((69, 0, 1), (66, 1, 1), (72, 2, 2)), lower=voice((60, 0, 4)))
    passing = score_of(upper=voice((69, 0, 1), (66, 1, 1), (67, 2, 2)), lower=voice((60, 0, 4)))
    hits = found(failing, "CP-07")
    assert len(hits) == 1 and hits[0]["severity"] == "hard"
    assert found(passing, "CP-07") == []


def test_cp08_a_stepwise_dissonance_that_turns_away_instead_of_back_is_a_finding():
    failing = score_of(upper=voice((64, 0, 1), (65, 1, 1), (63, 2, 2)), lower=voice((60, 0, 4)))
    passing = score_of(upper=voice((64, 0, 1), (65, 1, 1), (64, 2, 2)), lower=voice((60, 0, 4)))
    assert [f["rule"] for f in found(failing, "CP-08")] == ["CP-08"]
    assert found(passing, "CP-08") == []


# -- the perfect-interval rules -------------------------------------------------------------


def test_cp09_parallel_fifths_between_the_outer_voices_are_a_finding():
    failing = score_of(upper=voice((55, 0, 1), (57, 1, 1)), lower=voice((48, 0, 1), (50, 1, 1)))
    passing = score_of(upper=voice((55, 0, 1), (59, 1, 1)), lower=voice((48, 0, 1), (50, 1, 1)))
    hits = found(failing, "CP-09")
    assert len(hits) == 1
    assert "parallel fifths" in hits[0]["detail"]
    assert found(passing, "CP-09") == []


def test_cp09_ignores_parallells_between_inner_voices_which_the_card_scopes_out():
    score = score_of(soprano=voice((72, 0, 2)),
                     alto=voice((55, 0, 1), (57, 1, 1)),
                     bass=voice((48, 0, 1), (50, 1, 1)))
    assert found(score, "CP-09") == []


def test_cp10_a_hidden_octave_with_the_upper_voice_leaping_is_a_finding():
    failing = score_of(upper=voice((62, 0, 1), (65, 1, 1)), lower=voice((48, 0, 1), (53, 1, 1)))
    passing = score_of(upper=voice((59, 0, 1), (60, 1, 1)), lower=voice((48, 0, 1), (53, 1, 1)))
    hits = found(failing, "CP-10")
    assert len(hits) == 1
    assert "hidden octave" in hits[0]["detail"]
    assert found(passing, "CP-10") == []


# -- the line rules -------------------------------------------------------------------------


def test_cp11_a_leading_tone_over_the_dominant_bass_must_rise_to_the_tonic():
    failing = score_of(upper=voice((71, 0, 2), (69, 2, 2)), lower=voice((55, 0, 4)))
    passing = score_of(upper=voice((71, 0, 2), (72, 2, 2)), lower=voice((55, 0, 4)))
    assert [f["rule"] for f in found(failing, "CP-11")] == ["CP-11"]
    assert found(passing, "CP-11") == []


def test_cp12_a_chordal_seventh_must_fall_by_step():
    failing = score_of(upper=voice((70, 0, 2), (74, 2, 2)), lower=voice((60, 0, 4)))
    passing = score_of(upper=voice((70, 0, 2), (69, 2, 2)), lower=voice((60, 0, 4)))
    assert [f["rule"] for f in found(failing, "CP-12")] == ["CP-12"]
    assert found(passing, "CP-12") == []


def test_cp16_two_leaps_in_the_same_direction_are_a_style_note():
    failing = score_of(upper=voice((60, 0, 1), (67, 1, 1), (76, 2, 2)), lower=voice((48, 0, 4)))
    passing = score_of(upper=voice((60, 0, 1), (67, 1, 1), (65, 2, 2)), lower=voice((48, 0, 4)))
    hits = found(failing, "CP-16")
    assert len(hits) == 1 and hits[0]["severity"] == "style"
    assert found(passing, "CP-16") == []


def test_cp17_a_note_outside_the_nes_range_of_its_voice_is_a_finding():
    failing = score_of(triangle=voice((60, 0, 4)), upper=voice((72, 0, 4)))
    passing = score_of(triangle=voice((48, 0, 4)), upper=voice((72, 0, 4)))
    assert [f["rule"] for f in found(failing, "CP-17")] == ["CP-17"]
    assert found(passing, "CP-17") == []


def test_cp18_an_escape_tone_is_recorded_as_a_style_note():
    failing = score_of(upper=voice((67, 0, 1), (65, 1, 1), (72, 2, 2)), lower=voice((60, 0, 4)))
    passing = score_of(upper=voice((67, 0, 1), (65, 1, 1), (64, 2, 2)), lower=voice((60, 0, 4)))
    hits = found(failing, "CP-18")
    assert len(hits) == 1 and hits[0]["severity"] == "style"
    assert found(passing, "CP-18") == []


# -- crossing, overlap and spacing ----------------------------------------------------------


def test_cp13_and_cp14_crossing_is_not_overlap():
    crossing = score_of(upper=voice((69, 0, 1), (55, 1, 1)), lower=voice((60, 0, 2)))
    overlapping = score_of(upper=voice((69, 0, 1), (55, 1, 1)), lower=voice((60, 0, 1), (48, 1, 1)))
    clean = score_of(upper=voice((69, 0, 1), (71, 1, 1)), lower=voice((60, 0, 1), (48, 1, 1)))
    assert [f["rule"] for f in found(crossing, "CP-13")] == ["CP-13"]
    assert found(overlapping, "CP-14") != [] and found(overlapping, "CP-13") == []
    assert found(clean, "CP-13") == [] and found(clean, "CP-14") == []


def test_cp15_upper_voices_more_than_an_octave_apart_are_a_finding():
    failing = score_of(soprano=voice((84, 0, 4)), alto=voice((60, 0, 4)), bass=voice((48, 0, 4)))
    passing = score_of(soprano=voice((67, 0, 4)), alto=voice((60, 0, 4)), bass=voice((48, 0, 4)))
    assert [f["rule"] for f in found(failing, "CP-15")] == ["CP-15"]
    assert found(passing, "CP-15") == []


# -- the verdict, which is the gate ---------------------------------------------------------


def fake_result(rates, profile="free"):
    """A minimal analyse() result with the rates a test wants to put in front of the gate."""
    return {
        "profile": profile,
        "summary": {"by_severity": {"hard": sum(rates.values()), "soft": 0, "style": 0},
                    "rates_per_100_notes": rates},
    }


CALIBRATION = {"thresholds": {"per_100_notes": {"CP-01": 2.0, "CP-02": 1.0, "CP-07": 3.0}},
               "corpus": {"description": "a test corpus"}}


def test_the_gate_passes_when_every_rule_is_inside_its_own_budget():
    result = fake_result({"CP-01": 1.9, "CP-02": 1.0, "CP-07": 0.0})
    state, fails = check.verdict_of(result, "hard", CALIBRATION)
    assert (state, fails) == ("PASS", False)
    assert "within the Bach budget" in check.calibration_note(result, CALIBRATION)


def test_the_gate_fails_when_one_rule_is_over_budget_even_if_the_others_are_quiet():
    result = fake_result({"CP-01": 0.0, "CP-02": 2.0, "CP-07": 0.0})
    state, fails = check.verdict_of(result, "hard", CALIBRATION)
    assert (state, fails) == ("FAIL", True)
    assert "CP-02 2.00 vs 1.00" in check.calibration_note(result, CALIBRATION)


def test_without_a_calibration_any_hard_finding_fails_the_run():
    result = fake_result({"CP-01": 0.1})
    assert check.verdict_of(result, "hard", None) == ("FAIL", True)
    assert "not read" in check.calibration_note(result, None)


def test_an_empty_result_passes_whatever_the_calibration_says():
    empty = {"profile": "free", "summary": {"by_severity": {}, "rates_per_100_notes": {}}}
    assert check.verdict_of(empty, "hard", CALIBRATION) == ("PASS", False)


def test_a_cue_full_of_parallel_fifths_fails_the_gate():
    """The gate has to be able to fail: eight parallel fifths in sixteen notes is fifty per hundred."""
    calibration_path = os.path.join(COUNTERPOINT, "calibration.json")
    assert os.path.exists(calibration_path), "run tools/counterpoint/calibrate.py first"
    upper, lower = [], []
    for step in range(8):
        upper.append((55 + step, step, 1))
        lower.append((48 + step, step, 1))
    score = score_of(upper=voice(*upper), lower=voice(*lower))
    result = rules.analyse(score, profile="free")
    assert len([f for f in result["findings"] if f["rule"] == "CP-09"]) >= 7
    table = check.load_calibration(calibration_path)
    state, fails = check.verdict_of(result, "hard", table)
    assert (state, fails) == ("FAIL", True)
    assert "CP-09" in check.calibration_note(result, table)


# -- the calibration table is the one the corpus produced -----------------------------------


def test_the_calibration_table_covers_every_rule_at_several_works():
    path = os.path.join(COUNTERPOINT, "calibration.json")
    assert os.path.exists(path), "run tools/counterpoint/calibrate.py --report <md> first"
    table = check.load_calibration(path)
    assert table is not None
    for rule in rules.RULES:
        assert rule in table["thresholds"]["per_100_notes"], rule
    assert table["corpus"]["works"] >= 10
    assert "Bach" in table["corpus"]["description"]


def test_the_shipped_report_and_table_agree_on_the_budgets():
    table_path = os.path.join(COUNTERPOINT, "calibration.json")
    report_path = os.path.join(TOOLS, "knowledge", "COUNTERPOINT-CALIBRATION-2026-10-26.md")
    assert os.path.exists(table_path), "run tools/counterpoint/calibrate.py --report <md> first"
    assert os.path.exists(report_path), "run tools/counterpoint/calibrate.py --report <md> first"
    table = check.load_calibration(table_path)
    with open(report_path, "r", encoding="utf-8-sig") as handle:
        report = handle.read()
    for rule, budget in table["thresholds"]["per_100_notes"].items():
        assert rule in report
        assert ("%.2f" % budget) in report, rule
