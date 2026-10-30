"""Tests for tools/models_used.py and the MODELS-USED page it writes (card META-MODEL-BREADTH).

The card's check is that the page lists each model, its call and a receipt. These tests make that
check mechanical: the committed page must be exactly what the register renders, every row's
receipt must exist and must itself say the same model and kind, and the two rows that are offline
must be printed as offline rather than as a live answer.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import meta_client  # noqa: E402
import models_used  # noqa: E402


def test_the_committed_page_is_what_the_register_renders():
    """The page a judge reads cannot drift from the receipts without this failing."""
    rows = models_used.rows()
    assert models_used.problems_from(rows) == [], models_used.problems_from(rows)
    with open(models_used.OUT, encoding="utf-8") as handle:
        committed = handle.read()
    assert committed == models_used.render(rows), (
        "knowledge/MODELS-USED.md is out of date; run python tools/models_used.py")


def test_every_row_names_a_receipt_that_says_the_same_model_and_kind():
    rows = models_used.rows()
    assert len(rows) >= 4, "the card asks for four Meta models or more, the register has %d" % len(rows)
    seen = set()
    for row in rows:
        assert row.get("missing") is not True, "%s has no receipt" % row["model"]
        assert row["entry_model"] == row["model"], (
            "the row says %s, its receipt says %s" % (row["model"], row["entry_model"]))
        assert row["entry_kind"] == row["kind"]
        assert row["entry_backend"] in ("meta", "mock"), row["entry_backend"]
        assert isinstance(row["entry_network"], bool)
        with open(os.path.join(ROOT, row["receipt_path"]), "rb") as handle:
            assert hashlib.sha256(handle.read()).hexdigest() == row["receipt_sha256"]
        seen.add(row["model"])
    assert "muse-spark-1.3" in seen and "sam-3.1" in seen
    assert "meta-models/muse-spark-open-1026" in seen, "the open weights rung is not in the table"
    assert "muse-voice-transcribe-1.0" in seen, "Muse Voice Transcribe is not in the table"


def test_the_two_cited_models_are_labelled_offline_and_the_page_says_so():
    rows = {row["model"]: row for row in models_used.rows()}
    offline = [row for row in rows.values() if not row["entry_network"]]
    assert offline, "no offline row, so the page would be claiming live answers it may not have"
    for row in offline:
        assert row["entry_backend"] == "mock"
        assert row["model"] in ("meta-models/muse-spark-open-1026",
                                "muse-voice-transcribe-1.0"), (
            "%s is offline but is not one of the two cited models" % row["model"])
    page = models_used.render(list(rows.values()))
    assert "offline" in page
    assert "does not claim a live answer from Muse Spark Open or Muse Voice Transcribe" in page
    for row in offline:
        assert row["receipt_path"] in page
        assert "network false" in page


def test_the_cut_row_points_at_a_cut_that_exists_and_matches_its_receipt():
    row = [row for row in models_used.rows() if row["model"] == "sam-3.1"][0]
    assert row["cut_receipt"] == "knowledge/silhouette_cut/ship_cut_receipt.json"
    assert row["cut_present"] is True
    with open(os.path.join(ROOT, row["cut_receipt"]), encoding="utf-8") as handle:
        receipt = json.load(handle)
    assert receipt["model"] == "sam-3.1" and receipt["network"] is True
    assert receipt["cut"]["sha256"] == row["cut_sha256"]
    assert receipt["checks"]["alpha_pixels_equal_mask_set_pixels"] is True


def test_every_row_pins_its_receipt_instead_of_taking_whatever_is_newest():
    """A row that resolves at run time is how the commit gate caught a receipt that was not in HEAD."""
    for spec in models_used.REGISTER:
        assert spec.get("receipt"), (
            "%s %s has no pinned receipt, so the page would depend on the working cache"
            % (spec["kind"], spec["model"]))
        assert spec["receipt"].endswith(".json") and len(spec["receipt"]) == 69


def test_a_receipt_that_exists_but_is_not_committed_is_reported(tmp_path):
    """The gate's own failure mode: present on disk, absent from the commit a checkout would see."""
    stray = tmp_path / ("0" * 64 + ".json")
    stray.write_text("{}", encoding="utf-8")
    rows = [{"receipt_path": os.path.relpath(stray, models_used.ROOT).replace(os.sep, "/")}]
    problems = models_used.tracked_problems(rows)
    assert problems and "not in the commit" in problems[0], problems
    assert models_used.tracked_problems([{"receipt_path": None}]) == []


def test_a_page_that_disagrees_with_the_receipts_fails_the_check(tmp_path, monkeypatch, capsys):
    stale = tmp_path / "MODELS-USED.md"
    stale.write_text("# something a human typed\n", encoding="utf-8")
    monkeypatch.setattr(models_used, "OUT", str(stale))
    assert models_used.main(["--check"]) == 1
    assert "out of date" in capsys.readouterr().out


def test_a_missing_receipt_is_reported_rather_than_printed_as_evidence(monkeypatch):
    registers = list(models_used.REGISTER)
    broken = dict(registers[3])
    broken["receipt"] = "0" * 64 + ".json"
    registers[3] = broken
    monkeypatch.setattr(models_used, "REGISTER", tuple(registers))
    rows = models_used.rows()
    problems = models_used.problems_from(rows)
    assert any("no receipt" in problem for problem in problems), problems


def test_transcribe_makes_a_receipt_that_replays_offline(tmp_path, monkeypatch):
    """The Meta voice rung: record with the mock backend, then replay it with no network."""
    monkeypatch.setenv("PP_AI_CACHE", str(tmp_path / "ai_cache"))
    monkeypatch.setenv("PP_AI_BACKEND", "mock")
    monkeypatch.setenv("PP_AI_MODE", "record")
    wav = models_used.make_voice_sample(str(tmp_path / "line.wav"), seconds=0.1)
    with open(wav, "rb") as handle:
        raw = handle.read()
    first = meta_client.transcribe(wav)
    assert first["kind"] == "transcribe"
    assert first["model"] == "muse-voice-transcribe-1.0"
    assert first["text"].startswith("mock transcript")
    entry_path = meta_client.receipt_path(
        "transcribe", first["model"],
        {"model": first["model"], "audio_format": "wav", "audio_bytes": len(raw),
         "audio_sha256": hashlib.sha256(raw).hexdigest()})
    assert os.path.exists(entry_path)

    monkeypatch.setenv("PP_AI_MODE", "replay")
    again = meta_client.transcribe(wav)
    assert again["text"] == first["text"]
    assert again["cached"] is True
    with open(entry_path, encoding="utf-8") as handle:
        entry = json.load(handle)
    assert entry["kind"] == "transcribe"
    assert entry["network"] is False
    assert entry["request"]["audio_bytes"] == len(raw)
    assert "base64" not in json.dumps(entry["request"]), (
        "the receipt must not carry the audio bytes, only their size and digest")


def test_the_open_weights_id_is_reachable_through_the_client():
    """The table names an id, the client must actually ask for that id."""
    assert meta_client.model_for("open") == "meta-models/muse-spark-open-1026"
    assert meta_client.model_for("voice") == "muse-voice-transcribe-1.0"
    described = meta_client.describe("open")
    assert described["models"]["open"] == "meta-models/muse-spark-open-1026"
    assert "transcribe" in described["capabilities"]
