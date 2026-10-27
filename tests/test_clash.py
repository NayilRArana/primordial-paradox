"""The counterpoint rules, pinned: what counts as a device and what counts as a raw clash.

Card t_c0597404. `tools/counterpoint/clash.py` is a judgement call from start to finish, so the
judgements are frozen here as small four to eight note scores rather than as prose: a fifth is
consonant, a fourth above an upper voice is not counted, a fourth above the bass needs a third or a
sixth over it, a prepared note that resolves down is a suspension, a note that arrives an eighth
early and is the next chord's tone is an anticipation, and a semitone entered by a leap is a raw
clash. The last test pins the whole score's numbers, so a rule change cannot move v7's count quietly.
"""

from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COUNTERPOINT = os.path.join(ROOT, "tools", "counterpoint")
if COUNTERPOINT not in sys.path:
    sys.path.insert(0, COUNTERPOINT)

import clash  # noqa: E402

BEAT = 480
BAR = BEAT * 3


def score(notes_by_voice):
    return clash.Score.from_notes(notes_by_voice, division=480, time_sig=(3, 4))


def raws(events):
    return [e for e in events if e["class"] == "raw clash"]


def classes_at(events, bar, beat):
    return [e["class"] for e in events if e["bar"] == bar and abs(e["beat"] - beat) < 0.01]


def test_pitch_name_and_interval_class():
    assert clash.pitch_name(69) == "A4"
    assert clash.pitch_name(60) == "C4"
    assert clash.interval_class(60, 67) == 7
    assert clash.interval_class(60, 61) == 1


def test_snap_merges_a_rolled_chord_onto_the_grid():
    grid = 120
    assert clash.snap(47506, grid) == 47520
    assert clash.snap(48186, grid) == 48240


def test_a_fifth_is_consonant():
    # A minor, bass A2 with E4 over it: nothing to judge.
    events = clash.analyse(score({
        "triangle": [(0, BAR, 45, 96)],
        "vrc6 saw": [(0, BAR, 52, 80), (0, BAR, 57, 80)],
        "vrc6 pulse a": [(0, BAR, 69, 96)],
    }))
    assert events == []


def test_a_fourth_between_upper_voices_is_a_chord_member_not_a_clash():
    # C4 under F4 is a fourth, but the bass is A1, so it is the third of F under an A pedal and the
    # rule must not count it twice over.
    events = clash.analyse(score({
        "triangle": [(0, BAR, 33, 96)],
        "vrc6 saw": [(0, BAR, 60, 80)],
        "pulse 1": [(0, BAR, 65, 80)],
    }))
    counted = [e for e in events if {e["low_voice"], e["high_voice"]} == {"vrc6 saw", "pulse 1"}]
    assert counted == []


def test_a_fourth_above_the_bass_needs_a_third_or_sixth_over_it():
    # D3 with G4: a fourth above the lowest sounding note, and nothing puts a third or sixth over D.
    unsupported = clash.analyse(score({
        "triangle": [(0, BAR, 50, 96)],
        "vrc6 pulse a": [(0, BAR, 67, 96)],
    }))
    assert [e for e in unsupported if e["ic_name"] == "P4"]
    supported = clash.analyse(score({
        "triangle": [(0, BAR, 50, 96)],
        "vrc6 saw": [(0, BAR, 53, 80)],
        "vrc6 pulse a": [(0, BAR, 67, 96)],
    }))
    assert [e for e in supported if e["ic_name"] == "P4"] == []


def test_a_prepared_note_that_resolves_down_by_step_is_a_suspension():
    # Bar 1 is F major, so F4 is a chord tone. Bar 2 has C in the bass with E3 and G3 over it, so the
    # held F4 is a second above that third and has to fall to E4. The F4 is one tied note across the
    # line, because a re-articulation would not be prepared at all.
    events = clash.analyse(score({
        "triangle": [(0, BAR, 41, 96), (BAR, 2 * BAR, 48, 96)],
        "vrc6 saw": [(0, BAR, 57, 80), (0, BAR, 60, 80),
                     (BAR, 2 * BAR, 52, 80), (BAR, 2 * BAR, 55, 80)],
        "vrc6 pulse b": [(0, BAR + BEAT, 65, 90), (BAR + BEAT, 2 * BAR, 64, 90)],
    }))
    assert "suspension" in classes_at(events, 2, 1.0)


def test_a_tone_sounded_early_and_held_across_the_bar_line_is_an_anticipation():
    # Bar 1 sits on A with no G anywhere; the melody sounds G4 on the last eighth and holds it into
    # bar 2, where the bass is G. That is the DIS-09 shape, and it is not a clash.
    events = clash.analyse(score({
        "triangle": [(0, BAR, 45, 96), (BAR, 2 * BAR, 43, 96)],
        "vrc6 saw": [(0, BAR, 48, 80), (0, BAR, 52, 80),
                     (BAR, 2 * BAR, 47, 80), (BAR, 2 * BAR, 50, 80)],
        "vrc6 pulse a": [(0, BAR, 69, 96), (1200, BAR, 67, 96)],
    }))
    assert "anticipation" in classes_at(events, 1, 3.5)


def test_a_semitone_entered_by_a_leap_is_a_raw_clash():
    # C major under a B4 that leaps to D5 instead of resolving: an unprepared major seventh.
    events = clash.analyse(score({
        "triangle": [(0, BAR, 48, 96)],
        "vrc6 saw": [(0, BAR, 52, 80), (0, BAR, 55, 80)],
        "vrc6 pulse a": [(0, BEAT, 71, 96), (BEAT, BAR, 74, 96)],
    }))
    hits = raws(events)
    assert hits, "the major seventh against the bass has to be counted"
    assert hits[0]["bar"] == 1
    assert hits[0]["ic_name"] == "M7"


def test_the_harmony_is_read_from_the_pad_and_the_bass_together():
    at_zero = score({
        "triangle": [(0, BAR, 45, 96)],
        "vrc6 saw": [(0, BAR, 48, 80)],
    })
    assert clash.harmony(at_zero, 0) == {9, 0}


@pytest.mark.skipif(not os.path.exists(os.path.join(
    ROOT, "assets", "audio", "pp_01_title_v7", "pp_01_title_v7.mid")), reason="v7 not present")
def test_v7_keeps_the_numbers_the_report_states():
    """The pin. Every claim in knowledge/TITLE-DISSONANCE-2026-10-26.md starts from these."""
    path = os.path.join(ROOT, "assets", "audio", "pp_01_title_v7", "pp_01_title_v7.mid")
    song = clash.load_score(path)
    summary = clash.summarise(song, clash.analyse(song))
    assert summary["by_class"]["raw clash"] == 196
    assert summary["strong_raw"] == 30
    assert summary["by_class"]["suspension"] == 25
    assert summary["by_class"]["anticipation"] == 19
    assert summary["dissonances"] == 312


@pytest.mark.skipif(not os.path.exists(os.path.join(
    ROOT, "assets", "audio", "pp_01_title_v7", "pp_01_title_v7.mid")), reason="v7 not present")
def test_the_card_scope_three_voice_count():
    path = os.path.join(ROOT, "assets", "audio", "pp_01_title_v7", "pp_01_title_v7.mid")
    song = clash.load_score(path)
    summary = clash.summarise(song, clash.analyse(song, voices=("pulse 1", "pulse 2", "triangle")))
    assert summary["by_class"]["raw clash"] == 26
    assert summary["strong_raw"] == 8
