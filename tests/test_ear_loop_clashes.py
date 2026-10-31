"""Tests for the ear loop's clash term (card t_aa3ab04e).

The loop `tools/ear_loop.py` scores a cue on the judge's six rubric lines and then multiplies that
total by the share its own measured clashes leave standing:

    dose  = (strong + WEAK_CLASH_SHARE * (raw - strong)) / bars
    share = max(0, 1 - dose / CLASH_DOSE_PER_BAR)
    final = critic_total * share

What these tests pin is the property the card asks for, that a critic score cannot rise while
clashes do, plus the two states that must never pass for clean: a cue whose score file could not be
read, and a row that was never measured at all.
"""

from __future__ import annotations

import os
import sys

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (TOOLS, os.path.join(TOOLS, "tools", "counterpoint")):
    if path not in sys.path:
        sys.path.insert(0, path)

import ear_loop  # noqa: E402  (needs the paths above)

TOTAL = len(ear_loop.ALL_DIMENSIONS) * 7          # a critic total of 42, every line at 7
SAME_SCORES = {dimension: 7 for dimension in ear_loop.ALL_DIMENSIONS}
BEAT = 480                                        # ticks per quarter note in the cue written below


def measured(raw, strong, bars):
    """The shape ear_loop.measured_clash returns, without touching a file."""
    return {"score": "cue.mid", "state": "LEGACY", "cp01": 0, "cp09": 0,
            "raw": raw, "strong": strong, "bars": bars, "notes": 100}


def test_a_clean_cue_keeps_its_whole_critic_score():
    """No clashes, no cut: the judge's number stands as given."""
    assert ear_loop.final_score(SAME_SCORES, measured(0, 0, 32)) == TOTAL


def test_the_same_critic_score_falls_as_the_clashes_rise():
    """The card's rule: the final score cannot rise while the clash count does."""
    finals = [ear_loop.final_score(SAME_SCORES, measured(raw, strong, 40))
              for raw, strong in ((0, 0), (4, 2), (8, 4), (40, 20), (80, 40))]
    assert finals == sorted(finals, reverse=True)
    assert finals[0] > finals[1] > finals[2] > finals[3] > finals[4]


def test_a_clash_on_a_strong_beat_costs_more_than_one_off_it():
    """A strong-beat clash is the one that reads as a wrong note, so it weighs more."""
    strong = ear_loop.final_score(SAME_SCORES, measured(10, 10, 40))
    weak = ear_loop.final_score(SAME_SCORES, measured(10, 0, 40))
    assert strong < weak


def test_a_higher_critic_total_cannot_outrank_a_cleaner_cue():
    """v7 and v8 in one assertion: the judge's favourite loses to a cue with no clashes at all."""
    judge_favourite = ear_loop.final_score(SAME_SCORES, measured(196, 30, 52))
    quieter_judge = {dimension: 6 for dimension in ear_loop.ALL_DIMENSIONS}
    clean = ear_loop.final_score(quieter_judge, measured(0, 0, 52))
    assert clean > judge_favourite
    assert judge_favourite < 0.25 * TOTAL, "the measured scale must bite on a cue like v7"


def test_the_dose_is_the_scale_that_is_documented():
    """One weighted clash per bar takes the whole score: the constants are the arithmetic."""
    full = ear_loop.final_score(SAME_SCORES, measured(40, 40, 40))
    none = ear_loop.final_score(SAME_SCORES, measured(0, 0, 40))
    assert full == 0.0
    assert none == TOTAL


def test_a_row_that_was_never_measured_has_no_final_score():
    """An uncounted cue is not a clean one: no count means no final, not a full score."""
    assert ear_loop.final_score(SAME_SCORES, None) is None
    assert ear_loop.final_score(SAME_SCORES, measured(5, 1, 0)) is None
    assert ear_loop.final_score({}, measured(0, 0, 32)) is None


def test_an_unmeasured_row_never_ranks_above_a_measured_one():
    """Ranking puts every measured row first, whatever its final, and the unmeasured last."""
    rows = [{"cue": "unread", "final": None},
            {"cue": "clean", "final": 42.0},
            {"cue": "clashing", "final": 2.0}]
    assert [row["cue"] for row in ear_loop.rank_rows(rows)] == ["clean", "clashing", "unread"]


def test_measured_clash_reads_the_gate_on_a_real_cue(tmp_path):
    """The wiring, not the arithmetic: a real file is read by the real gate.

    The cue is written here rather than named from assets/audio, because scores are not tracked in
    this repo (card t_836dbb1a: no MIDI is in the tree), so a test that named one would pass in a
    working copy and fail in the tree the commit gate materialises. The file is a bare clash on a
    strong beat, which is the shape the counter must see: one pulse on a dissonant note against a held
    bass, with nothing preparing it.
    """
    import humanize

    song = {"division": BEAT, "tempo_us": 500000, "time_sig": (4, 4),
            "tracks": [{"name": "pulse 1", "cc": {},
                        "notes": [(0, BEAT, 58, 96), (BEAT, 4 * BEAT, 62, 96)]},
                       {"name": "triangle", "cc": {}, "notes": [(0, 4 * BEAT, 53, 96)]}]}
    path = os.path.join(str(tmp_path), "cue.mid")
    humanize.write_smf(song, path)

    facts, why = ear_loop.measured_clash(path)
    assert facts is not None, why
    assert isinstance(facts["raw"], int) and facts["bars"] > 0
    assert facts["raw"] >= 1, "the bare clash this cue carries has to reach the counter's total"


def test_a_cue_with_no_score_file_is_reported_with_its_reason():
    """The loop can be asked about a cue it has no score for; that must be a stated hole."""
    facts, why = ear_loop.measured_clash("")
    assert facts is None
    assert "no score file" in why
