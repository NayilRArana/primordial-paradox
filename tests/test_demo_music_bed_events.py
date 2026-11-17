"""The text blips and the battle stingers the capture mix carries (JUDGE-PANEL-2026-11-17 fix 3, card t_f19fa5c3).

The panel asks that a judge hear "storm and UI sound through the 180 s video" and "see audio present in the
verify file". This file pins the three halves of that in the repository rather than in a listening session:

  1. the reading: the events are the game's own `PP audio: <cue> played` lines from each capture's log, the
     cue files are the musician lane's delivered effects, and the levels are the engine's own macros;
  2. the mapping: a log stamp lands on the cut's clock through that segment's in point, corrected by the shift
     the capture's own audio confirms, so a recut re-reads instead of drifting;
  3. the verify: an events layer that is missing, empty, or not mixed cannot pass the check the delivered file
     is measured with, and the cut's verify file says whether an audio stream is present at all.

Honest limit: nothing here decodes the delivered film. tools/demo_music_bed.py --verify reads the film itself,
and its report (output/demo/<cut>_music_verify.json) is the measurement the panel is shown.
"""

from __future__ import annotations

import json
import os
import shutil
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import demo_music_bed as bed  # noqa: E402
import demo_cut_180 as cut     # noqa: E402

SAMPLE = os.path.join(ROOT, "tests", "fixtures", "story_good.events.sample.json")


def test_the_log_beside_a_capture_is_derived_from_the_source_name(tmp_path):
    """`raw_story_good.mkv` was recorded as `story_good`: the raw_ prefix is the recorder's own."""
    folder = tmp_path / "demo_2026-11-04"
    folder.mkdir()
    (folder / "story_good.events.json").write_text("{}", encoding="utf-8")
    (folder / "raw_story_good.mkv").write_bytes(b"")
    found = bed.event_log_for(str(folder / "raw_story_good.mkv"))
    assert found and os.path.basename(found) == "story_good.events.json"
    (folder / "doors.events.json").write_text("{}", encoding="utf-8")
    assert os.path.basename(bed.event_log_for(str(folder / "doors.mp4"))) == "doors.events.json"
    # A capture that kept no log is not an error: the tool simply has no events there.
    assert bed.event_log_for(str(folder / "quay.mp4")) is None


def test_the_events_are_the_lines_the_game_wrote_when_it_played_them():
    """The excerpt holds every kind of line the log writes; only the played lines come back."""
    rows = bed.log_events(SAMPLE)
    cues = [cue for _stamp, cue in rows]
    assert cues == ["car_engine_loop", "text_blip_a", "text_blip_a", "text_blip_a",
                    "encounter_swoosh", "text_blip_c"]
    # A streaming line, a loaded line and a title line are all refused above; the cut's own filter then
    # drops car_engine_loop, which this layer does not carry.
    assert "title_theme" not in cues and "title" not in cues
    stamps = [stamp for stamp, _cue in rows]
    assert stamps == sorted(stamps)
    assert stamps[4] == 22.7, "the stinger the Morgan fight starts on, as the game stamped it"


def test_the_levels_are_the_engine_s_own_macros():
    macros = bed.gml_macros()
    assert macros == {"sfx": 0.9, "blip": 0.5}, "PP_AUDIO_GAIN_SFX and PP_AUDIO_GAIN_BLIP from pp_audio.gml"
    assert bed.event_gain("text_blip_a") == 0.45, "a blip is played at half the effect level (spec 12 rule 6)"
    assert bed.event_gain("encounter_swoosh") == 0.9
    assert bed.event_gain("text_blip_percy") == 0.45


def test_every_scheduled_cue_resolves_to_a_delivered_file():
    for cue in bed.EVENT_CUES:
        path = bed.event_file(cue)
        assert os.path.exists(path), path
        assert os.path.getsize(path) > 1000, "%s is too small to be a sound" % path


def test_a_cue_with_no_file_is_refused_rather_than_silenced():
    with pytest.raises(bed.BedError):
        bed.event_file("no_such_effect")


def test_a_log_stamp_lands_on_the_cut_clock_through_the_segment(tmp_path, monkeypatch):
    """A stamp 0.40 s into a segment lands 0.40 s into that segment's window on the cut's clock.

    The capture here is twelve seconds of silence, so nothing confirms the copy and each row falls back to
    the raw stamp with basis "log": that is the arithmetic a recut depends on, and it must not drift. The
    silence is read through this module's own two readers rather than encoded with ffmpeg, so the row holds
    on a machine where the suite has no encoder, and the real capture path is measured by the verify run.
    """
    import numpy as np

    folder = tmp_path / "capture"
    folder.mkdir()
    source = folder / "raw_story_good.mkv"
    source.write_bytes(b"")
    shutil.copyfile(SAMPLE, str(folder / "story_good.events.json"))
    monkeypatch.setattr(bed, "probe_duration", lambda _path: 12.0)
    monkeypatch.setattr(bed, "mono", lambda *_args, **_kwargs: np.zeros(12 * 16000, dtype=np.float32))
    verify = {"duration_s": 180.0,
              "segments": [{"shot": "S4", "source": str(source), "in": 8.5, "seconds": 1.0, "clock": 50.0}]}
    video = tmp_path / "slice.mp4"
    video.write_bytes(b"")
    (tmp_path / "slice_verify.json").write_text(json.dumps(verify), encoding="utf-8")
    events, info = bed.plan_events(str(video))
    assert [item["cue"] for item in events] == ["text_blip_a"] * 3, "the three blips inside 8.5 to 9.5 s"
    assert [item["at"] for item in events] == [50.4, 50.47, 50.56], "clock 50.0 + (stamp - in 8.5)"
    assert {item["shift_basis"] for item in events} == {"log"}, "a silent capture confirms nothing"
    assert {item["shift_ms"] for item in events} == {0.0}
    assert {item["gain"] for item in events} == {0.45}, "a blip plays at half the engine's effect level"
    assert info["events"] == 3 and info["per_cue"] == {"text_blip_a": 3}
    assert info["dropped"] == 2, "the 22.7 s stinger and Percy's 101.66 s blip fall outside this segment"


def test_the_layer_is_refused_when_no_capture_holds_an_event(tmp_path):
    """A cut whose sources kept no log has no events, and the tool says so instead of writing silence."""
    source = tmp_path / "quay.mp4"
    source.write_bytes(b"")
    verify = {"duration_s": 180.0,
              "segments": [{"shot": "S3", "source": str(source), "in": 0.0, "seconds": 2.0, "clock": 29.0}]}
    video = tmp_path / "quay_cut.mp4"
    video.write_bytes(b"")
    (tmp_path / "quay_cut_verify.json").write_text(json.dumps(verify), encoding="utf-8")
    with pytest.raises(bed.BedError):
        bed.plan_events(str(video))


def test_a_missing_or_empty_layer_fails_the_verify():
    """The two ways an events layer can be absent both fail, so the film cannot pass on the plan alone."""
    empty = bed.event_checks("film.mp4", "before.mp4", [], "events.wav")
    assert empty and empty[0]["ok"] is False, "no events planned is a failure, not a pass"
    missing = bed.event_checks("film.mp4", "before.mp4",
                               [{"shot": "S4", "cue": "text_blip_a", "at": 1.0,
                                 "file": "assets/audio/sfx/text_blip_a.ogg"}],
                               os.path.join(ROOT, "output", "demo", "no-such-layer.wav"))
    assert missing and missing[0]["ok"] is False
    assert "missing" in missing[0]["detail"]


def test_the_cut_reports_whether_its_audio_stream_is_present(monkeypatch):
    """The judge panel reads `has_audio` off the verify file, so the reading is pinned both ways.

    The two replies here are ffprobe's own shape: one audio stream, and none. The binary itself is exercised
    by the delivered file's verify run, not by a fixture this suite would have to encode.
    """
    from types import SimpleNamespace

    def reply(streams):
        return SimpleNamespace(stdout=json.dumps({"streams": streams}), returncode=0, stderr="")

    monkeypatch.setattr(cut.subprocess, "run", lambda *_a, **_k: reply([]))
    assert cut.audio_stream("no-audio.mp4") == {"has_audio": False}
    monkeypatch.setattr(cut.subprocess, "run",
                        lambda *_a, **_k: reply([{"codec_name": "aac", "sample_rate": "48000",
                                                  "channels": 2}]))
    assert cut.audio_stream("film.mp4") == {"has_audio": True, "codec": "aac",
                                            "sample_rate": 48000, "channels": 2}
    monkeypatch.setattr(cut.subprocess, "run", lambda *_a, **_k: SimpleNamespace(stdout="", returncode=1))
    assert cut.audio_stream("broken.mp4") == {"has_audio": False}, "an unreadable file is not an audio file"
