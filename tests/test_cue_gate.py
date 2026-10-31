"""Tests for the M4 cue gate (card t_aa3ab04e): a raw clash is refused, a prepared one passes.

The gate is `tools/counterpoint/cue_gate.py`, and it reads a real file: the checker reads the SMF,
the M0 clash counter reads the same events, and the verdict is the two rules the card names (CP-01,
a dissonance on a strong beat that is neither prepared nor resolved, and CP-09, a parallel perfect
fifth or octave between the outer voices). So the tests write small MIDI files into a temporary
project root and gate them, rather than testing the arithmetic in isolation: a bug in the file
reader or in the clash counter is a red here too.

The two cases the card asks for are `test_a_raw_clash_on_a_strong_beat_is_refused` and
`test_a_prepared_suspension_passes`. The rest pin the three ways a spot may stay (an intentional mark
with a reason, a cue Nayil's ear already approved, a measured baseline) and the one state that is
never a pass (a cue the gate cannot measure).
"""

from __future__ import annotations

import json
import os
import sys

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COUNTERPOINT = os.path.join(TOOLS, "tools", "counterpoint")
for path in (TOOLS, COUNTERPOINT):
    if path not in sys.path:
        sys.path.insert(0, path)

import cue_gate  # noqa: E402  (needs the paths above)
import humanize  # noqa: E402

BEAT = 480
PULSE1 = "pulse 1"
TRIANGLE = "triangle"

# The two cases below, as notes: (start tick, end tick, pitch, velocity).
# Bare clash: Bb3 on the downbeat against F3, leaving by a leap from beat 2. A perfect fourth above
# the bass with nothing under it is dissonant in this engine, it is attacked on a strong beat, and
# nothing prepares it.
RAW_CLASH = {
    PULSE1: [(0, BEAT, 58, 96), (BEAT, 4 * BEAT, 62, 96)],
    TRIANGLE: [(0, 4 * BEAT, 53, 96)],
}
# Prepared suspension: G4 sounds against C3 (a fifth, consonant), the bass then moves to F3 so the
# held G4 is dissonant, and G4 resolves down by step to F4 over the same bass: a 9 to 8 suspension.
SUSPENSION = {
    PULSE1: [(0, 2 * BEAT, 67, 96), (2 * BEAT, 4 * BEAT, 65, 96)],
    TRIANGLE: [(0, BEAT, 48, 96), (BEAT, 2 * BEAT, 53, 96), (2 * BEAT, 4 * BEAT, 53, 96)],
}


def cue_file(folder, name, voices):
    """Write one two-voice cue as a Standard MIDI File and return its path."""
    song = {"division": BEAT, "tempo_us": 500000, "time_sig": (4, 4),
            "tracks": [{"name": voice, "notes": notes, "cc": {}} for voice, notes in voices.items()]}
    path = os.path.join(str(folder), name)
    humanize.write_smf(song, path)
    return path


def judged(tmp_path, voices, name="cue.mid", root=None):
    """Gate one cue built in the temporary tree. Returns (facts, verdict)."""
    path = cue_file(tmp_path, name, voices)
    return cue_gate.gate(path, root=root or str(tmp_path))


def test_a_raw_clash_on_a_strong_beat_is_refused(tmp_path):
    """The card's first check: a cue with a raw clash does not land."""
    facts, verdict = judged(tmp_path, RAW_CLASH)
    assert verdict["state"] == "REFUSED"
    assert verdict["counts"]["cp01"] >= 1
    assert verdict["open"]["CP-01"]
    assert verdict["counts"]["raw_clash"] >= 1
    assert cue_gate.state_code(verdict["state"]) == 1
    finding = verdict["open"]["CP-01"][0]
    assert finding["bar"] == 1
    assert "is dissonant against triangle on a strong beat" in finding["detail"]


def test_a_prepared_suspension_passes(tmp_path):
    """The card's second check: the same kind of dissonance, prepared and resolved, passes."""
    facts, verdict = judged(tmp_path, SUSPENSION)
    assert verdict["counts"]["cp01"] == 0
    assert verdict["counts"]["cp09"] == 0
    assert verdict["counts"]["strong_raw"] == 0
    assert verdict["state"] == "PASS"
    assert cue_gate.state_code(verdict["state"]) == 0


def test_a_clash_the_cue_marks_intentional_with_a_reason_passes(tmp_path):
    """A chosen clash may stay, but only with a reason of its own written beside the cue."""
    cue_file(tmp_path, "cue.mid", RAW_CLASH)
    with open(os.path.join(str(tmp_path), "intentional.json"), "w", encoding="utf-8") as handle:
        json.dump({"intentional": [{"rule": "CP-01", "bar": 1, "beat": 1,
                                    "reason": "the accented F is the harbour bell, resolved by the "
                                              "bass in the next bar on purpose"}]}, handle)
    facts, verdict = cue_gate.gate(os.path.join(str(tmp_path), "cue.mid"), root=str(tmp_path))
    assert verdict["state"] == "PASS"
    assert len(verdict["waived"]) == 1
    assert verdict["waived"][0]["finding"]["rule"] == "CP-01"


def test_a_mark_without_a_real_reason_is_refused(tmp_path):
    """A mark that only says 'on purpose' is not an argument, so the gate refuses the cue."""
    cue_file(tmp_path, "cue.mid", RAW_CLASH)
    with open(os.path.join(str(tmp_path), "intentional.json"), "w", encoding="utf-8") as handle:
        json.dump({"intentional": [{"rule": "CP-01", "bar": 1, "beat": 1, "reason": "on purpose"}]},
                  handle)
    facts, verdict = cue_gate.gate(os.path.join(str(tmp_path), "cue.mid"), root=str(tmp_path))
    assert verdict["state"] == "REFUSED"
    assert any("at least 20 characters" in problem for problem in verdict["waiver_problems"])


def test_a_stale_mark_is_refused(tmp_path):
    """A mark that matches no finding any more means the cue moved out from under its own marks."""
    cue_file(tmp_path, "cue.mid", RAW_CLASH)
    with open(os.path.join(str(tmp_path), "intentional.json"), "w", encoding="utf-8") as handle:
        json.dump({"intentional": [{"rule": "CP-01", "bar": 9, "beat": 1,
                                    "reason": "this mark was written for a bar the cue no longer has"}]},
                  handle)
    facts, verdict = cue_gate.gate(os.path.join(str(tmp_path), "cue.mid"), root=str(tmp_path))
    assert verdict["state"] == "REFUSED"
    assert verdict["stale_waivers"]


def test_a_cue_nayils_ear_approved_is_grandfathered_with_a_note(tmp_path):
    """The card's must not: a cue the ear already approved is noted, not blocked."""
    cue_file(tmp_path, "cue.mid", RAW_CLASH)
    os.makedirs(os.path.join(str(tmp_path), "data"))
    with open(os.path.join(str(tmp_path), "data", "cue_ear_approvals.json"), "w",
              encoding="utf-8") as handle:
        json.dump({"entries": [{"path": "cue.mid", "approved_by": "Nayil", "date": "2026-10-26",
                                "verdict": "a bit dissonant"}]}, handle)
    facts, verdict = cue_gate.gate(os.path.join(str(tmp_path), "cue.mid"), root=str(tmp_path))
    assert verdict["state"] == "GRANDFATHERED"
    assert "a bit dissonant" in verdict["why"]
    assert cue_gate.state_code(verdict["state"]) == 0
    assert verdict["counts"]["cp01"] >= 1, "the counts are still printed, they are just not a block"


def test_an_approval_row_resolves_against_the_root_not_the_caller_directory(tmp_path, monkeypatch):
    """The gate is run from anywhere, so an entry's relative path is read against the root."""
    root = tmp_path / "tree"
    root.mkdir()
    (root / "data").mkdir()
    cue_file(root, "cue.mid", RAW_CLASH)
    with open(os.path.join(str(root), "data", "cue_ear_approvals.json"), "w",
              encoding="utf-8") as handle:
        json.dump({"entries": [{"path": "cue.mid", "approved_by": "Nayil", "date": "2026-10-26",
                                "verdict": "a bit dissonant"}]}, handle)
    monkeypatch.chdir(str(tmp_path))
    facts, verdict = cue_gate.gate(os.path.join(str(root), "cue.mid"), root=str(root))
    assert verdict["state"] == "GRANDFATHERED"


def test_an_approval_row_that_names_nothing_or_another_drive_does_not_crash(tmp_path):
    """A malformed row is skipped: a name on another mount used to raise inside relpath."""
    cue_file(tmp_path, "cue.mid", RAW_CLASH)
    os.makedirs(os.path.join(str(tmp_path), "data"))
    with open(os.path.join(str(tmp_path), "data", "cue_ear_approvals.json"), "w",
              encoding="utf-8") as handle:
        json.dump({"entries": [{"path": "", "approved_by": "nobody"},
                               {"path": "Z:/elsewhere/cue.mid", "approved_by": "nobody"},
                               {"approved_by": "a row with no path at all"}]}, handle)
    facts, verdict = cue_gate.gate(os.path.join(str(tmp_path), "cue.mid"), root=str(tmp_path))
    assert verdict["state"] == "REFUSED"


def test_a_cue_worse_than_its_baseline_is_refused(tmp_path):
    """The baseline is a floor and not an amnesty: a legacy cue that gets worse is refused."""
    cue_file(tmp_path, "cue.mid", RAW_CLASH)
    os.makedirs(os.path.join(str(tmp_path), "data"))
    with open(os.path.join(str(tmp_path), "data", "cue_gate_baseline.json"), "w",
              encoding="utf-8") as handle:
        json.dump({"entries": {"cue.mid": {"cp01": 0, "cp09": 0, "raw_clash": 0,
                                           "strong_raw": 0}}}, handle)
    facts, verdict = cue_gate.gate(os.path.join(str(tmp_path), "cue.mid"), root=str(tmp_path))
    assert verdict["state"] == "REFUSED"
    assert "worse than the gate's own baseline" in verdict["why"]


def test_a_cue_the_gate_cannot_read_is_unmeasured_and_not_a_pass(tmp_path):
    """An unreadable cue is a hole in the gate, so it exits 2 rather than 0."""
    missing = os.path.join(str(tmp_path), "not_a_cue.mid")
    facts, verdict = cue_gate.gate(missing, root=str(tmp_path))
    assert facts is None
    assert verdict["state"] == "UNMEASURED"
    assert cue_gate.state_code(verdict["state"]) == 2
    assert "cannot read" in verdict["why"]
