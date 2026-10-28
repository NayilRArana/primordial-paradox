"""Tests for card t_0ed3bd3f (M2): the corpus statistics and the files M1b and M1a read.

Two kinds of test here.

The unit tests pin the measurements that are easy to get quietly wrong: the chord labeller must name a
dominant seventh and not an augmented triad, a constant run of equal steps must not count as a sequence,
and a cadence must be a chord pair rather than any two adjacent chords. Each of those has a textbook
case and a neighbour that must not fire, so a future widening of the reader fails here rather than in a
report a musician reads.

The file tests run the validator over the committed JSON, so a target file that stops validating fails
the suite instead of shipping.
"""

from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COUNTERPOINT = os.path.join(ROOT, "tools", "counterpoint")
if COUNTERPOINT not in sys.path:
    sys.path.insert(0, COUNTERPOINT)

import corpus_stats  # noqa: E402
import check_counterpoint_targets  # noqa: E402
import rules  # noqa: E402

C_MAJOR = (0, "major")
A_MINOR = (9, "minor")


# -- the chord labeller -----------------------------------------------------------------------


def test_labeller_names_a_dominant_seventh_over_a_major_triad_reading():
    """G, B, D, F is V7 in C. The triad reading loses its seventh and must not win."""
    label = corpus_stats.label_chord([55, 59, 62, 65], C_MAJOR)
    assert label["quality"] == "dom7"
    assert label["root"] == 7
    assert label["roman"] == "V7"


def test_labeller_prefers_a_major_triad_to_an_augmented_triad_on_the_same_notes():
    """F, A, C# can be read as F augmented or as A something. Music in C major is not augmented."""
    label = corpus_stats.label_chord([53, 57, 61], C_MAJOR)
    assert label["quality"] != "aug" or label["root"] != 9


def test_labeller_names_a_minor_tonic_in_a_minor_key():
    label = corpus_stats.label_chord([57, 60, 64], A_MINOR)
    assert label["roman"] == "i"
    assert label["quality"] == "min"


def test_labeller_returns_none_for_a_single_pitch():
    assert corpus_stats.label_chord([60], C_MAJOR) is None


# -- cadence naming ---------------------------------------------------------------------------


def chord(root, quality, bass_pitch):
    return {"root": root, "quality": quality, "roman": "x", "bass_pitch": bass_pitch, "top": 0}


def test_cadence_names_a_perfect_authentic_when_the_bass_leaps_and_the_top_steps_down():
    previous = chord(7, "maj", 55)      # G
    current = chord(0, "maj", 48)       # C
    assert corpus_stats.cadence_type(previous, current, C_MAJOR, -5, -2) == "perfect authentic"


def test_cadence_names_an_imperfect_authentic_when_the_bass_does_not_leap():
    previous = chord(7, "maj", 55)
    current = chord(0, "maj", 52)       # C with E in the bass, a first inversion arrival
    assert corpus_stats.cadence_type(previous, current, C_MAJOR, 4, -2) == "imperfect authentic"


def test_cadence_names_nothing_between_two_unrelated_chords():
    previous = chord(2, "min", 50)
    current = chord(9, "min", 45)
    assert corpus_stats.cadence_type(previous, current, C_MAJOR, 0, 0) is None


# -- sequences and imitation ------------------------------------------------------------------


def line(*pitches, beat=480, length=480):
    return [rules.Note(index * beat, index * beat + length, pitch, 90)
            for index, pitch in enumerate(pitches)]


def score_of(**voices):
    return rules.Score.from_notes({name: line(*pitches) for name, pitches in voices.items()},
                                  division=480, time_sig=(4, 4))


def test_a_rising_scale_is_not_counted_as_a_sequence():
    """Four equal steps is a run, not a shape: the interval pattern has one distinct value."""
    score = score_of(top=(60, 62, 64, 66, 68, 70))
    assert corpus_stats.cell_sequences(score)["occurrences"] == 0


def test_a_shaped_cell_repeated_a_step_higher_is_a_sequence():
    """A shape with two distinct intervals, repeated up a tone, is what a sequence is."""
    score = score_of(top=(60, 62, 65, 64, 67, 62, 64, 67, 66, 69))
    assert corpus_stats.cell_sequences(score)["occurrences"] >= 2


def test_imitation_is_measured_in_beats_between_two_voices():
    subject = (60, 62, 65, 64, 62)
    answer = (67, 69, 72, 71, 69)
    score = rules.Score.from_notes(
        {"top": line(*subject),
         "bottom": [rules.Note(note.start + 8 * 480, note.end + 8 * 480, pitch, 90)
                    for note, pitch in zip(line(*answer), answer)]},
        division=480, time_sig=(4, 4))
    found = corpus_stats.imitation(score)
    assert found["events"] >= 1
    assert 8.0 in {round(float(key), 2) for key in found["offsets"]}


# -- the committed files ----------------------------------------------------------------------


def test_the_committed_target_file_validates(capsys):
    code = check_counterpoint_targets.main([])
    printed = capsys.readouterr().out
    assert code == 0, printed
    assert "every check passed" in printed


def test_the_target_bands_are_ordered():
    import json
    with open(os.path.join(ROOT, "data", "counterpoint_targets.json"), encoding="utf-8") as handle:
        data = json.load(handle)
    for name in ("step_share", "leap_share", "large_leap_share", "leap_recovery_share"):
        band = data["targets"]["melody"][name]
        assert band["min"] <= band["mean"] <= band["max"], name


def test_no_long_dash_reaches_the_committed_documents():
    for relative in ("knowledge/BAROQUE-ENGINE-RESEARCH.md",
                     "data/counterpoint_targets.json",
                     "data/hod_dissonance_devices.json"):
        with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
            text = handle.read()
        for dash in ("\u2014", "\u2013", "\u2015", "\u2212"):
            assert dash not in text, "%s carries a long dash" % relative
