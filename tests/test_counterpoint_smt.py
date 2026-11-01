"""Tests for card t_11f7f43f (FV-4): the Z3 counterpoint solver proves its output clean. SUPERSEDED 2026-11-01: see the note at the end of this file.

The solver in tools/counterpoint/smt_counterpoint.py turns the M1a counterpoint rules into
integer constraints over the NES ranges. These tests assert the two properties the card names:
(1) every solved texture is rule clean under the REAL M1a checker, in both profiles, and (2)
the constraint blocks are load bearing, so skipping one admits a violation the checker faults.
They are the fast, deterministic slice of what fv4_proof.py measures at length; each test names
the block it exercises so a regression points at the rule, not at the harness.
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

import rules  # noqa: E402
import smt_counterpoint as smt  # noqa: E402


def spec(voices=("pulse 1", "triangle"), tonic=0, mode="major", bars=4):
    return smt.CounterpointSpec(tonic=tonic, mode=mode, voices=list(voices), bars=bars)


# -- the core guarantee ----------------------------------------------------------------


@pytest.mark.parametrize("form", ["species", "invention", "canon"])
def test_every_form_solves_and_is_clean_in_both_profiles(form):
    result = smt.build_texture(spec(), form=form, timeout_ms=120000)
    assert result is not None, "no clean texture exists for %s" % form
    proof = smt.check_clean(result)
    assert proof["verdict"] == "CLEAN", "refuted in %s" % proof["profiles"]
    for profile in ("free", "strict"):
        row = proof["profiles"][profile]
        assert row["hard"] == 0 and row["soft"] == 0, \
            "form %s is not clean in the %s profile: %s" % (form, profile, row["findings"])


def test_three_voice_texture_is_clean_and_in_nes_range():
    result = smt.build_texture(spec(voices=("pulse 1", "pulse 2", "triangle")),
                               form="species", timeout_ms=120000)
    assert result is not None
    assert smt.check_clean(result)["verdict"] == "CLEAN"
    for name, grid in result["grid"].items():
        low, high = rules.NES_RANGES[name]
        assert all(low <= p <= high for p in grid), "%s leaves its NES range" % name


def test_countermelody_keeps_the_given_line_and_cleans_the_rest():
    melody = ("D5", "F5", "A5", "D5", "C5", "A5", "G5", "A5",
              "D5", "E5", "F5", "A5", "G5", "F5", "E5", "C5")
    pitches = [rules.parse_pitch(n) for n in melody]
    result = smt.build_texture(spec(bars=4), form="countermelody", melody=pitches,
                               timeout_ms=120000)
    assert result is not None
    assert result["grid"]["pulse 1"] == pitches, "the given melody was altered"
    assert smt.check_clean(result)["verdict"] == "CLEAN"


def test_seeded_output_is_clean():
    # The seed is a bias, not a determinism promise (that is M1b's seeded search), so the
    # guarantee worth asserting here is that the seeded path stays rule clean, not that two
    # runs agree. Two runs need not agree: z3 may return any model over the free notes.
    result = smt.build_texture(spec(bars=2), form="species", seed=3, timeout_ms=120000)
    assert result is not None
    assert smt.check_clean(result)["verdict"] == "CLEAN"


# -- the load bearing blocks (mutation) ------------------------------------------------


def _finds_violation(form, skip, voices=("pulse 1", "triangle"), attempts=3):
    """True when skipping one block lets the full checker fault the output at least once."""
    for _ in range(attempts):
        result = smt.build_texture(spec(voices=voices), form=form, skip=(skip,),
                                   timeout_ms=120000)
        if result is not None and smt.check_clean(result)["verdict"] != "CLEAN":
            return True
    return False


@pytest.mark.parametrize("block", ["vertical", "parallel", "hidden", "leading",
                                   "seventh", "leaps"])
def test_skipping_a_rule_block_admits_a_violation(block):
    # Each of these is a correctness rule the checker faults, so the solver without it must be
    # able to emit something unclean. Mutation is a search, not a proof, so a miss is a fail
    # here: the block is there to stop exactly this.
    assert _finds_violation("species", block), \
        "skipping %r never yields a violation; the block may not bind" % block


def test_parallel_block_specifically_stops_parallel_fifths():
    # The parallel constraint is the one the card names first. Without it, the checker's CP-09
    # should show up in some solve; assert the specific rule, not only a generic refutation.
    for _ in range(4):
        result = smt.build_texture(spec(), form="species", skip=("parallel",),
                                   timeout_ms=120000)
        if result is None:
            continue
        proof = smt.check_clean(result)
        rules_found = {f["rule"] for p in proof["profiles"].values() for f in p["findings"]}
        if "CP-09" in rules_found:
            return
    pytest.fail("skipping parallel never produced a CP-09 parallel-perfect finding")


# -- the round trip ---------------------------------------------------------------------


def test_a_solved_texture_round_trips_through_midi_clean(tmp_path):
    result = smt.build_texture(spec(), form="invention", timeout_ms=120000)
    assert result is not None
    midi_path = str(tmp_path / "invention.mid")
    rt = smt.write_midi(result, midi_path)
    assert os.path.exists(midi_path)
    assert rt["roundtrip_hard"] == 0 and rt["roundtrip_soft"] == 0


# SUPERSEDED 2026-11-01 (card t_11f7f43f). These tests cover `smt_counterpoint.py`, the first
# encoder. The landed model's suites are `tests/test_counterpoint_z3.py` and
# `tools/counterpoint/tests/test_counterpoint_z3_adversarial.py`. This file is committed because
# `formal/FV-4-rules.md` section 8 names it as the repo's fast test for the FV-4 harness and
# `FV4-RESULTS.md` reports its numbers. Measured on CitadelArana 2026-11-01: 14 passed in 68.55 s.

