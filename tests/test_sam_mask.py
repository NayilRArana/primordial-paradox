"""Tests for tools/sam_mask.py, and for the sam-3.1 grammar tools/meta_client.py now reads.

Card SAM-SEGMENT-LIVE. The recorded line below is a real answer from the live API, captured
2026-10-26 on the desktop node for the noun phrase "ship" on a 256x240 concept frame. It is
embedded rather than read from data/ai_cache so the test keeps its ground truth if the cache is
re-recorded, and so the suite never needs the network or a key.

The rest of the file is offline: the fixture payload was produced by Meta's own encoder
(meta_sam_parser._mask_codec._encode_raster) for a 6x4 raster, so a decoder that drifts from the
wire format fails here instead of at review time.
"""

from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import meta_client  # noqa: E402
import sam_mask  # noqa: E402

# The answer the live API sent for "ship", verbatim, one line, two objects.
RECORDED_LINE = "<0f>0<|box;x1=144;y1=105;x2=219;y2=163;w=256;h=240|><|mask;x=0;y=0;data=59,76,!!!!!aHl$xNvS=##'bsn4pd`EVWgJA[?3y^1v^[DqHh5[*okotDM$1r5erPlr`mbvF?gDINKJ5kmro9|>,1<|box;x1=35;y1=39;x2=92;y2=144;w=256;h=240|><|mask;x=0;y=0;data=106,58,!!!!#=EI+e!^oOH3m'b1Sn{=^ZUAiHqD35iOR[.2*]4j27?^Af?gP=#JxWfkQGK$IF8MX[v&%&A]f$:{W.zT#jVYtCPf&s2Zo0VhydN7/y&O?AI7TA.j:nI3LhuS{X1'{_P/D&_sG[)6T!!|>\n"

# A 6x4 mask built by Meta's encoder: a 3x3 block with a tail below it.
FIXTURE_PAYLOAD = "!!!!!)Hl)NMQxcU"
FIXTURE_WIDTH, FIXTURE_HEIGHT = 6, 4
FIXTURE_BITS = [
    0, 0, 0, 0, 0, 0,
    0, 1, 1, 1, 0, 0,
    0, 1, 1, 1, 0, 0,
    0, 0, 1, 0, 0, 0,
]


def fixture_record(box=(2, 3, 7, 6), frame=(12, 10)):
    return {"object_id": 0, "box": list(box), "frame": list(frame),
             "mask": {"height": FIXTURE_HEIGHT, "width": FIXTURE_WIDTH,
                       "encoding": "one_bit", "payload": FIXTURE_PAYLOAD}}


# ---------------------------------------------------------------- the decoder

def test_decode_one_bit_matches_the_encoder_fixture():
    raster = sam_mask.decode_one_bit(FIXTURE_PAYLOAD, FIXTURE_WIDTH, FIXTURE_HEIGHT)
    assert list(raster) == FIXTURE_BITS
    assert sam_mask.bbox(raster, FIXTURE_WIDTH, FIXTURE_HEIGHT) == [1, 1, 3, 3]


def test_decode_one_bit_refuses_a_payload_without_its_marker():
    with pytest.raises(sam_mask.MaskPayloadError) as caught:
        sam_mask.decode_one_bit("~" + FIXTURE_PAYLOAD[1:], FIXTURE_WIDTH, FIXTURE_HEIGHT)
    assert "starts with '!'" in str(caught.value)


def test_decode_one_bit_refuses_a_truncated_payload():
    with pytest.raises(sam_mask.MaskPayloadError):
        sam_mask.decode_one_bit(FIXTURE_PAYLOAD[:-4], FIXTURE_WIDTH, FIXTURE_HEIGHT)


def test_decode_mask_refuses_the_lossless_encoding_instead_of_guessing():
    with pytest.raises(sam_mask.MaskPayloadError) as caught:
        sam_mask.decode_mask({"height": 4, "width": 6, "encoding": "lossless",
                              "payload": "~" + FIXTURE_PAYLOAD[1:]})
    assert "one_bit" in str(caught.value)


# ---------------------------------------------------------------- the grammar

def test_parse_records_reads_the_recorded_answer():
    records = sam_mask.parse_records(RECORDED_LINE)
    assert [record["object_id"] for record in records] == [0, 1]
    assert [record["box"] for record in records] == [[144, 105, 219, 163], [35, 39, 92, 144]]
    assert [record["frame"] for record in records] == [[256, 240], [256, 240]]
    assert [(record["mask"]["width"], record["mask"]["height"]) for record in records] == [(76, 59), (58, 106)]
    assert [record["mask"]["encoding"] for record in records] == ["one_bit", "one_bit"]
    assert all(record["mask"]["payload"].startswith("!") for record in records)


def test_every_recorded_mask_is_the_size_of_its_own_box():
    for record in sam_mask.parse_records(RECORDED_LINE):
        x1, y1, x2, y2 = record["box"]
        assert record["mask"]["width"] == x2 - x1 + 1
        assert record["mask"]["height"] == y2 - y1 + 1


def test_meta_client_and_sam_mask_read_the_same_records():
    """Two parsers of one grammar drift unless a test holds them together."""
    assert meta_client.segmentation_records(RECORDED_LINE) == sam_mask.parse_records(
        RECORDED_LINE)


def test_segmentation_records_ignores_a_line_it_cannot_read():
    assert meta_client.segmentation_records("<0f>") == []
    assert sam_mask.parse_records("") == []


# ---------------------------------------------------------------- the render

def test_render_mask_writes_a_png_whose_bbox_is_the_box(tmp_path):
    """The fixture mask does not touch its own edges, so the PNG bbox is the translated mask.

    The identity that always has to hold is png bbox == box origin + in-mask bbox; the box the
    response sent is the mask's extent, and a mask that fills it (both recorded ones do) makes
    the two equal.
    """
    record = fixture_record()
    out = str(tmp_path / "mask.png")
    result = sam_mask.render_mask(record, out)
    assert result["mask_size"] == [6, 4]
    assert result["box_size"] == [6, 4]
    assert result["mask_size_matches_box"] is True
    assert result["mask_bbox_in_mask"] == [1, 1, 3, 3]
    assert result["png_bbox"] == [3, 4, 5, 6]
    assert result["bbox_is_the_translated_mask"] is True
    assert result["bbox_within_box"] is True
    assert result["bbox_matches_box"] is False, (
        "the tight bbox of a mask that leaves its own edge empty is smaller than the box")
    assert result["set_pixels"] == sum(FIXTURE_BITS)

    width, height, rows = sam_mask.read_png_grey(out)
    assert (width, height) == (12, 10)
    lit = [(x, y) for y, row in enumerate(rows) for x, value in enumerate(row) if value]
    assert min(x for x, _ in lit) == 3 and max(x for x, _ in lit) == 5
    assert min(y for _, y in lit) == 4 and max(y for _, y in lit) == 6
    assert len(lit) == sum(FIXTURE_BITS)


def test_render_mask_places_every_set_pixel_inside_the_canvas(tmp_path):
    record = fixture_record(box=(9, 7, 14, 10), frame=(12, 10))
    result = sam_mask.render_mask(record, str(tmp_path / "edge.png"))
    assert result["frame"] == [12, 10]
    assert result["png_bbox"] == [10, 8, 11, 9], (
        "pixels past the frame edge are dropped, and the bbox says so instead of claiming the box")
    assert result["bbox_within_box"] is True
    assert result["bbox_is_the_translated_mask"] is False


# ---------------------------------------------------------------- the recorded artifact

def test_the_recorded_answer_renders_a_mask_for_each_object(tmp_path):
    records = sam_mask.parse_records(RECORDED_LINE)
    assert len(records) == 2
    for record in records:
        result = sam_mask.render_mask(record, str(tmp_path / ("obj%d.png" % record["object_id"])))
        assert result["bbox_matches_box"] is True
        assert result["frame"] == [256, 240]
        assert result["set_pixels"] > 0
        assert result["png_bbox"] == record["box"]
