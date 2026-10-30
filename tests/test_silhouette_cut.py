"""Tests for tools/silhouette_cut.py (card META-MODEL-BREADTH).

The cut is the one place where a Meta model's answer becomes a game asset, so the tests hold it to
the answer rather than to a picture: every opaque pixel must be a pixel the mask set, and the cut's
alpha bounding box must sit inside the box the same response returned. The end to end test replays
the committed live entry with the network off, so it fails if the decoder, the placer or the PNG
writer drifts from the recorded ground truth.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
import zlib

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import meta_client  # noqa: E402
import silhouette_cut  # noqa: E402

SOURCE = os.path.join(ROOT, "knowledge", "silhouette_cut", "source_concept_sdxl.png")
CUT = os.path.join(ROOT, "knowledge", "silhouette_cut", "ship_cut.png")
RECEIPT = os.path.join(ROOT, "knowledge", "silhouette_cut", "ship_cut_receipt.json")
ENTRY = os.path.join(
    ROOT, "data", "ai_cache",
    "33101a9973cd1398980b986c5479e95d4b17fea3327a24f529df0a9b405dec5b.json")


@pytest.fixture(autouse=True)
def replay_only(monkeypatch):
    """Every call in this file reads the committed cache and never opens a socket."""
    monkeypatch.setenv("PP_AI_MODE", "replay")
    monkeypatch.delenv("PP_AI_BACKEND", raising=False)


def test_the_cut_carries_exactly_the_mask_the_model_sent(tmp_path):
    """End to end on the recorded live answer: same pixels, same extent, same size as the box."""
    out = tmp_path / "cut.png"
    result = silhouette_cut.cut(SOURCE, "ship", out_path=str(out))
    assert result["ok"] is True, result.get("checks")
    assert result["model"] == "sam-3.1"
    assert result["cache_entry"].endswith(os.path.basename(ENTRY))
    width, height, rows = silhouette_cut.read_png(str(out))
    assert (width, height) == (256, 240)
    pixels = silhouette_cut.alpha_count(rows)
    chosen = [item for item in result["objects"]
              if item["object_id"] == result["chosen_object"]][0]
    assert pixels == chosen["set_pixels"] > 0, (
        "the cut holds %d opaque pixels, the mask has %d set" % (pixels, chosen["set_pixels"]))
    box = chosen["box"]
    bbox = silhouette_cut.alpha_bbox(rows)
    assert bbox == [box[0], box[1], box[0] + chosen["mask_size"][0] - 1,
                    box[1] + chosen["mask_size"][1] - 1], (
        "the cut's alpha bbox %r is not the mask's extent inside the box %r" % (bbox, box))


def test_the_committed_cut_and_receipt_agree_with_each_other():
    result = silhouette_cut.check_receipt(RECEIPT)
    assert result["ok"] is True, result["problems"]
    with open(RECEIPT, encoding="utf-8") as handle:
        receipt = json.load(handle)
    with open(CUT, "rb") as handle:
        assert hashlib.sha256(handle.read()).hexdigest() == receipt["cut"]["sha256"]
    assert receipt["cut"]["path"].endswith("ship_cut.png")


def test_a_cut_that_does_not_match_its_receipt_fails_the_check(tmp_path):
    with open(RECEIPT, encoding="utf-8") as handle:
        receipt = json.load(handle)
    with open(CUT, "rb") as handle:
        data = bytearray(handle.read())
    data[-1] ^= 0xFF
    broken_cut = tmp_path / "ship_cut.png"
    broken_cut.write_bytes(bytes(data))
    broken_receipt = tmp_path / "ship_cut_receipt.json"
    receipt["cut"]["path"] = os.path.relpath(broken_cut, ROOT).replace(os.sep, "/")
    broken_receipt.write_text(json.dumps(receipt), encoding="utf-8")
    result = silhouette_cut.check_receipt(str(broken_receipt))
    assert result["ok"] is False
    assert any("not the one the receipt names" in problem or "bbox" in problem
               or "opaque" in problem for problem in result["problems"]), result["problems"]


def test_zero_records_is_a_refusal_not_a_full_frame_cut(tmp_path, monkeypatch):
    """sam-3.1 documents zero matches as valid, so nothing is written and the tool says so."""
    source = tmp_path / "concept.png"
    width, height = 8, 8
    rows = [[(20, 30, 40, 255)] * width for _ in range(height)]
    silhouette_cut.write_png_rgba(str(source), width, height, rows)
    cache = tmp_path / "ai_cache"
    cache.mkdir()
    monkeypatch.setenv("PP_AI_CACHE", str(cache))
    with open(source, "rb") as handle:
        raw = handle.read()
    echo = {"model": "sam-3.1", "prompt": "character",
            "image_sha256": hashlib.sha256(raw).hexdigest(), "image_bytes": len(raw),
            "mask_encoding": "one_bit"}
    entry_path = meta_client.receipt_path("segment", "sam-3.1", echo)
    with open(entry_path, "w", encoding="utf-8") as handle:
        json.dump({"key": os.path.splitext(os.path.basename(entry_path))[0], "kind": "segment",
                   "backend": "meta", "model": "sam-3.1", "mode": "record",
                   "recorded_at": "2026-10-27T00:50:58Z", "network": True,
                   "request": echo,
                   "response": {"text": "<0f>", "boxes": [], "masks": [], "objects": []}},
                  handle)
    out = tmp_path / "should_not_exist.png"
    result = silhouette_cut.cut(str(source), "character", out_path=str(out))
    assert result["ok"] is False
    assert "zero records" in result["why"]
    assert not out.exists(), "a refusal must not leave a cut behind"


def test_the_reader_refuses_a_png_it_cannot_read_exactly(tmp_path):
    def chunk(tag, body):
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))

    deep = tmp_path / "deep16.png"
    deep.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 16, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(b"\x00" * 40)) + chunk(b"IEND", b""))
    with pytest.raises(silhouette_cut.PngError) as caught:
        silhouette_cut.read_png(str(deep))
    assert "16 bit" in str(caught.value)

    interlaced = tmp_path / "interlaced.png"
    interlaced.write_bytes(b"\x89PNG\r\n\x1a\n"
                           + chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 1))
                           + chunk(b"IDAT", zlib.compress(b"\x00" * 40)) + chunk(b"IEND", b""))
    with pytest.raises(silhouette_cut.PngError) as caught:
        silhouette_cut.read_png(str(interlaced))
    assert "interlaced" in str(caught.value)


def test_an_rgba_png_round_trips_through_this_reader(tmp_path):
    rows = [[(1, 2, 3, 0), (4, 5, 6, 255)], [(7, 8, 9, 128), (10, 11, 12, 255)]]
    path = tmp_path / "small.png"
    silhouette_cut.write_png_rgba(str(path), 2, 2, rows)
    width, height, read_rows = silhouette_cut.read_png(str(path))
    assert (width, height) == (2, 2)
    assert read_rows == rows
    assert silhouette_cut.alpha_count(read_rows) == 3
    assert silhouette_cut.alpha_bbox(read_rows) == [0, 0, 1, 1]
