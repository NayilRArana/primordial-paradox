"""The two checks an interval count cannot see: notes outside the key, and cross relations.

Card t_c0597404. `tools/counterpoint/keycheck.py` reports them; these tests pin what each word means,
so a later lane cannot quietly widen "outside the key" to include G#, which this score uses on purpose
as the leading tone.
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
import keycheck  # noqa: E402

BEAT = 480
BAR = BEAT * 3


def score(notes):
    return clash.Score.from_notes(notes, division=480, time_sig=(3, 4))


def test_the_leading_tone_is_inside_the_key_and_a_raised_fourth_is_not():
    inside = score({"vrc6 pulse a": [(0, BAR, 68, 96)]})  # G#4
    assert keycheck.out_of_key(inside) == []
    outside = score({"vrc6 pulse a": [(0, BAR, 66, 96)]})  # F#4
    found = keycheck.out_of_key(outside)
    assert len(found) == 1
    assert found[0]["pitch"] == "F#4"
    assert found[0]["bar"] == 1


def test_a_semitone_between_two_voices_is_a_cross_relation_and_is_reported_with_a_bar():
    crossing = score({
        "triangle": [(0, BAR, 55, 96)],       # G3
        "vrc6 saw": [(0, BAR, 56, 80)],       # G#3, one semitone away
    })
    found = keycheck.cross_relations(crossing)
    assert found, "G against G# in two voices has to be reported"
    assert found[0]["bar"] == 1
    assert {found[0]["low_voice"], found[0]["high_voice"]} == {"triangle", "vrc6 saw"}


def test_a_far_apart_semitone_pair_is_counted_only_when_asked_for():
    # A G2 under a G#4: a semitone by pitch class, two octaves apart in fact.
    spread = score({
        "triangle": [(0, BAR, 43, 96)],       # G2
        "vrc6 pulse a": [(0, BAR, 68, 96)],   # G#4
    })
    assert keycheck.cross_relations(spread) == []
    assert len(keycheck.cross_relations(spread, within_octave=False)) >= 1


def test_a_consonant_pair_is_never_a_cross_relation():
    clean = score({
        "triangle": [(0, BAR, 45, 96)],
        "vrc6 saw": [(0, BAR, 57, 80)],
    })
    assert keycheck.cross_relations(clean) == []


@pytest.mark.skipif(not os.path.exists(os.path.join(
    ROOT, "assets", "audio", "pp_01_title_v7", "pp_01_title_v7.mid")), reason="v7 not present")
def test_v7_keeps_the_counts_the_report_states():
    song = clash.load_score(os.path.join(ROOT, "assets", "audio", "pp_01_title_v7",
                                         "pp_01_title_v7.mid"))
    assert len(keycheck.out_of_key(song)) == 17
    assert len(keycheck.cross_relations(song)) == 64
