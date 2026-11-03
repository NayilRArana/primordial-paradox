"""Pins for the four final scope cues (2026-11-03, MUSIC role).

The cues are built by tools/counterpoint/final_cues_build.py, which writes build_report.json beside
each stream. What is pinned: the row in data/audio.json names the stream, the stream is on disk and
mirrored, the counterpoint cue gate passed, the declared key and tempo agree with what was measured in
the decoded audio, the loop seam is clean, and the level is on the project's target. Nothing here
claims how it sounds; nobody has listened.
"""

from __future__ import annotations

import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CUES = {
    "PP-03": ("pp_03_quay_storm", "A minor", 160, 4, 48),
    "PP-06": ("pp_06_percy_possessed", "E minor", 150, 3, 48),
    "PP-15a": ("pp_15a_credits_kill", "A minor", 72, 4, 24),
    "PP-15b": ("pp_15b_credits_spare", "A major", 144, 4, 32),
}


def _rows():
    with open(os.path.join(ROOT, "data", "audio.json"), encoding="utf-8") as h:
        return {r["id"]: r for r in json.load(h)["cues"]}


def _report(asset):
    with open(os.path.join(ROOT, "assets", "audio", asset, "build_report.json"), encoding="utf-8") as h:
        return json.load(h)


@pytest.mark.parametrize("cue", sorted(CUES))
def test_the_row_names_a_stream_that_is_on_disk_and_mirrored(cue):
    asset = CUES[cue][0]
    row = _rows()[cue]
    assert row["asset"] == asset and row["pending"] is False and row["loop"] is True
    assert row["delivered_file"] == "assets/audio/%s/%s.ogg" % (asset, asset)
    assert os.path.isfile(os.path.join(ROOT, row["delivered_file"]))
    assert os.path.isfile(os.path.join(ROOT, "game", "datafiles", "streams", asset + ".ogg"))


@pytest.mark.parametrize("cue", sorted(CUES))
def test_the_counterpoint_gate_passed_with_nothing_open(cue):
    rep = _report(CUES[cue][0])
    assert rep["cue_gate"]["exit"] == 0
    assert any("G1 CP-01 raw clashes on a strong beat: 0" in line and "CP-09 parallel perfect intervals: 0" in line
               for line in rep["cue_gate_summary"])


@pytest.mark.parametrize("cue", sorted(CUES))
def test_declared_tempo_and_length_agree_with_the_decoded_audio(cue):
    asset, _key, bpm, beats, bars = CUES[cue]
    rep = _report(asset)
    assert rep["bpm"] == bpm and rep["beats_per_bar"] == beats and rep["bars"] == bars
    assert abs(rep["delivered"]["seconds"] - bars * beats * 60.0 / bpm) < 0.05
    for band, got in rep["audio_tempo"].items():
        assert abs(got["bpm"] - bpm) / bpm < 0.01, (band, got)


@pytest.mark.parametrize("cue", sorted(CUES))
def test_the_key_found_in_the_audio_is_the_declared_key(cue):
    asset, key, *_ = CUES[cue]
    rep = _report(asset)
    assert rep["declared_key"] == key
    tops = [name for _score, name in rep["audio_key_top3"]]
    relative = {"A minor": "C major", "E minor": "G major", "A major": "F# minor"}[key]
    assert tops[0] in (key, relative), (tops, key)
    # The storm and the credits are tonally plain, so their top reading must be the declared key itself.
    if cue != "PP-06":
        assert tops[0] == key


@pytest.mark.parametrize("cue", sorted(CUES))
def test_the_loop_seam_is_clean_and_the_level_is_on_target(cue):
    rep = _report(CUES[cue][0])
    assert rep["seam"]["verdict"] == "clean", rep["seam"]
    got = rep["delivered"]
    assert abs(got["loudness"]["integrated_lufs"] + 14.0) <= 0.2
    assert got["loudness"]["true_peak_dbtp"] <= -1.0 + 0.05
    assert got["mean_volume_db"] > -40.0


def test_the_old_quay_theme_is_still_registered_under_a_new_id():
    rows = _rows()
    assert rows["PP-18"]["asset"] == "pp_03_harbor_master1" and rows["PP-18"]["pending"] is False
    for pending in ("PP-08", "PP-09", "PP-12", "PP-13"):
        assert rows[pending]["fallback"] == "PP-18"


def test_percy_keeps_the_boss_priority_and_the_room_keeps_its_slot():
    rows = _rows()
    assert rows["PP-06"]["boss"] is True
    with open(os.path.join(ROOT, "data", "maps", "all.json"), encoding="utf-8") as h:
        maps = {m["id"]: m for m in json.load(h)["maps"]}
    assert maps["southampton_town_quay"]["music"] == "PP-03"
