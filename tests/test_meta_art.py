"""The Meta art runner: style B prompts, one price source, a hard budget, and the refusals before any call.

Card META-ART-1 (t_9332fe42). tools/meta_art.py is the path that asks Muse Image for a concept and SAM 3.1
for a cut, then hands the result to the project's own NES conversion and gates. A tool that spends money
per call needs its cheap invariants measured by machine, not by reading the file:

    the style     Nayil picked direction B on 2026-10-26, so every asset prompt must still carry the
                  words knowledge/ART-STYLE.md section 4 uses for B; a prompt that drifts back to A or C
                  is a silent re-decision nobody made
    the price     one source, meta_spend_ledger.PER_IMAGE and PER_SEGMENT, and a spend row says MEASURED
                  when the response reported a cost and LIST when it did not
    the budget    a plan over --budget and a plan over --max-calls are refused BEFORE anything is sent,
                  which is the only reason a ceiling means anything
    the refund    with no key in the process, the tool exits 3 and sends nothing
    the name      the spend row carries the card, not whatever task happened to be in the environment

Everything here runs IN PROCESS and writes nothing, anywhere. That is deliberate: the commit gate traces
writes back to the tree it is testing, so a test that spawns the tool as a child and lets it write to
pytest's tmp_path is a test the gate cannot vouch for. The parts that do write (concept, cut, NES frame,
evidence, sheet) are exercised by the offline mock run recorded on the card, which leaves its evidence in
output/meta_art_proof/mock_chain and output/meta_art_proof/gate_sensitivity.json rather than in a test.
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "meta_art.py")
LEDGER = os.path.join(ROOT, "tools", "meta_spend_ledger.py")

LONG_DASHES = ("\u2013", "\u2014", "\u2015")
STYLE_B_WORDS = ("bold black 1 pixel outlines", "three tone shading lit from the top left",
                 "detailed tiles on a 16x16 grid")
PER_IMAGE = 0.01
PER_SEGMENT = 0.0025
UNCREATED = os.path.join(ROOT, "output", "meta_art_never_written_by_a_test")


def runner():
    """Import the tool inside the test, so collection never runs its imports for the whole suite."""
    for path in (os.path.join(ROOT, "tools"), os.path.join(ROOT, "tools", "art")):
        if path not in sys.path:
            sys.path.insert(0, path)
    import meta_art  # noqa: PLC0415 (intentional: see the module docstring)
    return meta_art


def assert_nothing_was_written():
    if not os.path.exists(UNCREATED):
        return
    leftovers = os.listdir(UNCREATED)
    raise AssertionError("a refused run wrote %r under %s" % (leftovers, UNCREATED))


def test_the_slice_assets_are_the_three_the_card_names_and_all_ask_for_direction_b():
    meta_art = runner()
    assert meta_art.STYLE == "B"
    assert set(meta_art.ASSETS) == {"title_backdrop", "quay_night", "ship_deck"}
    for asset, spec in meta_art.ASSETS.items():
        for words in STYLE_B_WORDS:
            assert words in spec["prompt"], "%s prompt is missing %r" % (asset, words)
        assert "no text" in spec["prompt"], asset
        assert spec["noun"] and spec["scene"], asset


def test_projected_cost_uses_the_ledger_prices_and_not_its_own():
    meta_art = runner()
    import meta_spend_ledger  # noqa: PLC0415
    assert meta_art.projected_cost(0) == 0.0
    expected = 3 * (meta_spend_ledger.PER_IMAGE + meta_spend_ledger.PER_SEGMENT)
    assert abs(meta_art.projected_cost(3) - expected) < 1e-12
    # Six candidates on each of the three slice assets is 36 calls, about 23 cents of the 25 USD ceiling.
    assert 0.2 < meta_art.projected_cost(18) < 0.25


def test_the_price_constants_are_the_ledgers_own_numbers():
    ledger = open(LEDGER, "r", encoding="utf-8").read()
    assert "PER_IMAGE = %s" % PER_IMAGE in ledger
    assert "PER_SEGMENT = %s" % PER_SEGMENT in ledger


def test_a_spend_row_says_whether_the_cost_was_measured_or_listed():
    meta_art = runner()
    listed = meta_art.spend_line("image", "muse-image-1.0",
                                 {"backend": "meta", "mode": "record", "usage": {}}, "c1")
    assert listed["basis"] == "LIST"
    assert listed["cost"] == "cost_usd=%s" % PER_IMAGE
    measured = meta_art.spend_line("image", "muse-image-1.0",
                                   {"backend": "meta", "mode": "record",
                                    "usage": {"cost_usd": 0.02}}, "c1")
    assert measured["basis"] == "MEASURED"
    assert measured["cost"] == "cost_usd=0.02"
    segment = meta_art.spend_line("segment", "sam-3.1",
                                  {"backend": "meta", "mode": "record", "usage": {}}, "c1")
    assert segment["basis"] == "LIST"
    assert segment["cost"] == "cost_usd=%s" % PER_SEGMENT


def test_a_plan_over_the_budget_is_refused_before_anything_is_sent(monkeypatch):
    meta_art = runner()
    monkeypatch.setenv("PP_AI_BACKEND", "mock")
    code = meta_art.main(["--seeds", "1", "--budget", "0.001", "--out", UNCREATED])
    assert code == 2
    assert_nothing_was_written()


def test_a_plan_over_max_calls_is_refused_before_anything_is_sent(monkeypatch):
    meta_art = runner()
    monkeypatch.setenv("PP_AI_BACKEND", "mock")
    code = meta_art.main(["--seeds", "6", "--max-calls", "4", "--out", UNCREATED])
    assert code == 2
    assert_nothing_was_written()


def test_a_dry_run_sends_nothing_and_writes_nothing(monkeypatch):
    meta_art = runner()
    monkeypatch.setenv("PP_AI_BACKEND", "mock")
    code = meta_art.main(["--dry-run", "--out", UNCREATED])
    assert code == 0
    assert_nothing_was_written()


def test_no_key_means_exit_three_and_no_call(monkeypatch):
    meta_art = runner()
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    monkeypatch.delenv("META_API_KEY", raising=False)
    monkeypatch.setattr(meta_art.meta_client, "describe",
                        lambda role: {"backend": "meta", "mode": "record", "key_present": False,
                                      "key_env": "MODEL_API_KEY then META_API_KEY",
                                      "cache_dir": os.path.join(ROOT, "data", "ai_cache"),
                                      "cache_entries": 0})
    code = meta_art.main(["--seeds", "1", "--out", UNCREATED])
    assert code == 3
    assert_nothing_was_written()


def test_the_tool_carries_no_long_dash():
    text = open(TOOL, "r", encoding="utf-8").read()
    for dash in LONG_DASHES:
        assert dash not in text, "long dash %r in tools/meta_art.py" % dash
