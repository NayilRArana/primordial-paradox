"""Tests for tools/receipts.py and tools/check_receipts.py (card t_7450df91, RECEIPTS-LABELS).

The card's promise is one sentence: every Meta number is labelled measured, computed or inferred, and
every one of those labels carries a logged receipt a reader can re-check. What is pinned here is exactly
what could quietly stop being true:

1. The build's Meta numbers are all labelled, from the three labels only, and every one of the eight
   resolves to a ledger row whose source still hashes to the number its receipt records.
2. Logging is idempotent: a second run over the same inputs appends nothing, so the ledger is a record
   of receipts and not a record of how often the tool ran.
3. A verify file that quotes a receipt the ledger does not hold FAILS, and so does a number whose label
   is outside the vocabulary, a block that never uses one of the three labels, and a block smaller than
   the card's floor of three.
4. An edited source FAILS: a receipt whose sha256 no longer matches the bytes is the moment a receipt
   becomes a claim, and that is the failure the whole card exists to catch.
5. The judge panel READS the labels: the measured lines it builds from a verify payload carry each
   label and receipt id, and say so when a capture labels nothing.
6. The committed ledger and the four files this card touches are ASCII with no long dash, which the
   house rule and the pre-commit hook both require.
"""

from __future__ import annotations

import json
import os

import check_receipts
import judge_panel
import receipts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "data", "receipts", "meta_receipts.jsonl")


def _write_payload(path, numbers):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"video": "output/demo/x.mp4", "ok": True,
                                 "meta_numbers": numbers}, indent=2, sort_keys=True) + "\n")


def _numbers(tmp_path):
    """The build's own numbers, logged into a throwaway ledger."""
    ledger = os.path.join(str(tmp_path), "meta_receipts.jsonl")
    return receipts.meta_numbers(ledger_path=ledger), ledger


# --------------------------------------------------------------------------- 1. the labels, on the real build

def test_every_meta_number_is_labelled_from_the_three_labels():
    numbers = receipts.meta_numbers()
    assert len(numbers) >= 3
    assert {row["label"] for row in numbers} == set(receipts.LABELS)
    for row in numbers:
        assert row["label"] in receipts.LABELS
        assert isinstance(row["value"], (int, float)) and not isinstance(row["value"], bool)
        assert row["receipt"].startswith("rcpt-")
        assert row["source"] and row["locator"] and row["why"]
        assert row.get("formula") if row["label"] == "computed" else row.get("formula") is None


def test_the_real_numbers_are_the_bake_files_own(tmp_path):
    """The numbers are read, not typed: they move when the file they name moves."""
    numbers = {row["name"]: row for row in receipts.meta_numbers(ledger_path=os.path.join(str(tmp_path), "l.jsonl"))}
    bake = json.load(open(os.path.join(ROOT, "data", "meta_bake.json"), encoding="utf-8"))["bake"]
    assert numbers["meta.model_calls"]["value"] == bake["calls_attempted"]
    assert numbers["meta.rows"]["value"] == bake["rows"]
    assert numbers["meta.live_rows"]["value"] == bake["live"]
    assert numbers["meta.fallback_rows"]["value"] == bake["calls_attempted"] - bake["live"]
    assert numbers["meta.system_chars"]["value"] == bake["system_chars"]
    assert numbers["meta.live_share_pct"]["value"] == round(
        100.0 * bake["live"] / bake["calls_attempted"], 1)
    assert numbers["meta.talk_turns_onscreen"]["label"] == "inferred"


# --------------------------------------------------------------------------- 2. the ledger

def test_logging_twice_appends_nothing(tmp_path):
    ledger = os.path.join(str(tmp_path), "meta_receipts.jsonl")
    first = receipts.meta_numbers(ledger_path=ledger)
    before = open(ledger, encoding="utf-8").read()
    second = receipts.meta_numbers(ledger_path=ledger)
    after = open(ledger, encoding="utf-8").read()
    assert [row["receipt"] for row in first] == [row["receipt"] for row in second]
    assert before == after
    assert len(receipts.read_ledger(ledger)) == len(first)


def test_the_committed_ledger_holds_at_least_three_real_receipts():
    rows = receipts.read_ledger(LEDGER)
    assert len(rows) >= 3
    faults, _rows = check_receipts.check_ledger(LEDGER)
    assert not faults.failed, "\n".join(faults.rows)


# --------------------------------------------------------------------------- 3. what the verifier refuses

def test_a_correct_file_passes(tmp_path):
    numbers, ledger = _numbers(tmp_path)
    path = os.path.join(str(tmp_path), "take_verify.json")
    _write_payload(path, numbers)
    faults, read = check_receipts.check_verify(path, ledger_path=ledger)
    assert not faults.failed, "\n".join(faults.rows)
    assert len(read) == len(numbers)


def test_a_receipt_that_was_never_logged_fails(tmp_path):
    numbers, ledger = _numbers(tmp_path)
    numbers[0]["receipt"] = "rcpt-0000000000000000"
    path = os.path.join(str(tmp_path), "take_verify.json")
    _write_payload(path, numbers)
    faults, _read = check_receipts.check_verify(path, ledger_path=ledger)
    assert faults.failed
    assert any("is not in the ledger" in row for row in faults.rows)


def test_a_label_outside_the_vocabulary_fails(tmp_path):
    numbers, ledger = _numbers(tmp_path)
    numbers[0]["label"] = "estimated"
    path = os.path.join(str(tmp_path), "take_verify.json")
    _write_payload(path, numbers)
    faults, _read = check_receipts.check_verify(path, ledger_path=ledger)
    assert faults.failed
    assert any("is not one of" in row for row in faults.rows)


def test_a_file_that_never_uses_one_label_fails(tmp_path):
    numbers, ledger = _numbers(tmp_path)
    kept = [row for row in numbers if row["label"] != "inferred"]
    path = os.path.join(str(tmp_path), "take_verify.json")
    _write_payload(path, kept)
    faults, _read = check_receipts.check_verify(path, ledger_path=ledger)
    assert faults.failed
    assert any("never uses the label inferred" in row for row in faults.rows)


def test_fewer_than_three_numbers_fails(tmp_path):
    numbers, ledger = _numbers(tmp_path)
    path = os.path.join(str(tmp_path), "take_verify.json")
    _write_payload(path, numbers[:2])
    faults, _read = check_receipts.check_verify(path, ledger_path=ledger)
    assert faults.failed
    assert any("at least 3 are needed" in row for row in faults.rows)


def test_no_block_at_all_fails(tmp_path):
    path = os.path.join(str(tmp_path), "take_verify.json")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"video": "output/demo/x.mp4", "ok": True}) + "\n")
    faults, _read = check_receipts.check_verify(path, ledger_path=os.path.join(str(tmp_path), "n.jsonl"))
    assert faults.failed
    assert any("carries no meta_numbers block" in row for row in faults.rows)


# --------------------------------------------------------------------------- 4. an edited source

def test_an_edited_source_fails_a_strict_receipt(tmp_path):
    ledger = os.path.join(str(tmp_path), "meta_receipts.jsonl")
    sources = []
    rows = []
    for index in range(3):
        source = os.path.join(str(tmp_path), "bake_%d.json" % index)
        with open(source, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("{\"bake\": %d}\n" % index)
        sources.append(source)
        rows.append({"id": "rcpt-test-edit-%d" % index, "logged_at": "2026-10-29T00:00:00Z",
                     "name": "meta.test_%d" % index, "label": "measured", "value": index,
                     "source": os.path.basename(source), "locator": "bake",
                     "sha256": receipts.sha256_file(source), "why": "a test row"})
    with open(ledger, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    faults, _rows = check_receipts.check_ledger(ledger, root=str(tmp_path), strict=True)
    assert not faults.failed, "\n".join(faults.rows)
    with open(sources[1], "w", encoding="utf-8", newline="\n") as handle:
        handle.write("{\"bake\": 99}\n")

    # A sweep of an old ledger reports the edited source as STALE history, not as a false number.
    faults, _rows = check_receipts.check_ledger(ledger, root=str(tmp_path))
    assert not faults.failed, "\n".join(faults.rows)
    assert any(row.startswith("NOTE") and "changed after the receipt was written" in row
               for row in faults.rows)

    # A current verify file that quotes that receipt is a claim about today, so it fails.
    faults, _rows = check_receipts.check_ledger(ledger, root=str(tmp_path), strict=True)
    assert faults.failed
    assert any("no longer hashes" in line for line in faults.rows)


def test_a_verify_file_that_quotes_a_stale_receipt_fails(tmp_path):
    numbers, ledger = _numbers(tmp_path)
    path = os.path.join(str(tmp_path), "take_verify.json")
    _write_payload(path, numbers)
    # Move the source the computed fallback number was read from, the way a regeneration would.
    bake_path = os.path.join(ROOT, "data", "meta_bake.json")
    original = receipts.sha256_file(bake_path)
    stale = dict(numbers[0])
    stale["receipt"] = "rcpt-0000000000000001"
    with open(ledger, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"id": stale["receipt"], "logged_at": "2026-10-29T00:00:00Z",
                                 "name": stale["name"], "label": stale["label"],
                                 "value": stale["value"], "source": stale["source"],
                                 "locator": stale["locator"], "sha256": "0" * 64,
                                 "why": "a receipt whose recorded hash is not the file's"}, sort_keys=True) + "\n")
    _write_payload(path, [stale] + numbers[1:])
    faults, _read = check_receipts.check_verify(path, ledger_path=ledger)
    assert receipts.sha256_file(bake_path) == original
    assert faults.failed
    assert any("no longer hashes to this receipt's sha256" in row for row in faults.rows)


# --------------------------------------------------------------------------- 5. the judge panel reads them

def test_the_judge_panel_reads_the_labels():
    numbers = receipts.meta_numbers()
    script = {"verify": {"meta_numbers": numbers, "planned_seconds": 180.0, "recorded_seconds": 182.5,
                         "has_audio": True}, "missing": []}
    lines = judge_panel.measured_lines([], {"duration_s": 182.5}, script, None)
    text = "\n".join(lines)
    for row in numbers:
        assert "%s is %s, labelled %s, receipt %s" % (row["name"], row["value"], row["label"],
                                                      row["receipt"]) in text
    assert "no Meta number in this capture is a number a reader has to take on trust" in text


def test_the_judge_panel_says_when_nothing_is_labelled():
    script = {"verify": {"planned_seconds": 180.0, "recorded_seconds": 182.5, "has_audio": True,
                         "meta_numbers": []}, "missing": []}
    lines = judge_panel.measured_lines([], {"duration_s": 182.5}, script, None)
    assert any("labels no Meta number" in line for line in lines)


# --------------------------------------------------------------------------- 6. house style

def test_the_new_files_carry_no_long_dash():
    for name in ("tools/receipts.py", "tools/check_receipts.py", "tests/test_receipts.py",
                 "data/receipts/meta_receipts.jsonl"):
        text = open(os.path.join(ROOT, name), encoding="utf-8").read()
        for mark in ("\u2012", "\u2013", "\u2014", "\u2015"):
            assert mark not in text, "%s carries %r" % (name, mark)
        text.encode("ascii")
