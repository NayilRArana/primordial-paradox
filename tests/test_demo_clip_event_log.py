"""The log a cut clip has to keep (card t_b24aa225, JUDGE-PANEL-2026-11-17 fix 3's S5 gap).

The events layer reads `PP audio: <cue> played` lines out of the JSON the recorder wrote beside each source
video, and S5 of the 180 s cut is `morgan_talk.mp4`: not a recording, a clip cut from the `story_good` run by
the 2026-11-04 session's own recorder script. Its log therefore never existed under its own name, and the
musician lane placed no blip there rather than invent one. `tools/demo_clip_event_log.py` moves that run's
stamps into the clip's clock.

What is pinned here, in order:

  1. the arithmetic: a stamp lands at the segment's clock plus its distance into the segment's SOUND, which is
     the recorder's own `audio_window`, not the segment's start;
  2. the honest drop: a sped segment's sound is the tail of the run, so a stamp before it was heard by nobody
     and is counted, never given a place;
  3. the refusals: a table that is not this clip, and a run that kept no log, both stop the write;
  4. the naming: the reader resolves the file beside the clip with no code change, and the file says it was
     derived, so it cannot be read as a log the game wrote live.

The last test reads the real capture folder when it is on disk: the delivered S5 log against the clip's own
duration and the run's log. It is skipped on a checkout that does not hold the captures.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import demo_clip_event_log as clip_log  # noqa: E402
import demo_music_bed as bed            # noqa: E402

CAPTURES = os.path.join(ROOT, "output", "demo_2026-11-04")
MORGAN = os.path.join(CAPTURES, "morgan_talk.mp4")
STORY_GOOD_LOG = os.path.join(CAPTURES, "story_good.events.json")


class FakeRecorder:
    """The recorder's surface this tool reads: its CLIPS table and its audio_window rule."""

    def __init__(self, clips, path=None):
        self.CLIPS = clips
        self.__file__ = path or os.path.join(ROOT, "output", "demo_2026-11-04", "recorder", "demo_cut.py")

    @staticmethod
    def audio_window(start, end, speed):
        duration = (end - start) / speed
        return end - duration, end


def rows(*triples):
    return [{"index": index, "start": start, "end": end, "speed": speed,
             "duration": round((end - start) / speed, 4),
             "audio": [round(end - (end - start) / speed, 4), round(end, 4)],
             "clip": [0.0, 0.0]}
            for index, (start, end, speed) in enumerate(triples)]


def test_a_stamp_lands_on_the_clip_clock_at_its_distance_into_the_segment():
    """At speed 1.0 the sound is the segment, so the rule is the cut's own: clock plus distance."""
    segments, total = clip_log.segment_rows(FakeRecorder({}), [(10.0, 14.0, 1.0), (20.0, 23.0, 1.0)])
    assert total == pytest.approx(7.0)
    assert [row["clip"] for row in segments] == [[0.0, 4.0], [4.0, 7.0]]
    kept, dropped, outside = clip_log.remap([(10.4, "PP audio: text_blip_a played"),
                                             (10.47, "PP audio: text_blip_a played"),
                                             (21.5, "PP audio: encounter_swoosh played"),
                                             (30.0, "PP audio: text_blip_a played")], segments)
    assert [round(at, 3) for at, _line, _stamp, _index in kept] == [0.4, 0.47, 5.5]
    assert dropped == [] and outside == 1, "the 30.0 s row belongs to a part of the run this clip does not show"


def test_a_sped_segment_keeps_the_sound_it_kept_and_drops_the_rest_by_count():
    """The recorder does not stretch sound: a 1.5x segment's sound is its last 2/3, so the head is dropped."""
    segments, total = clip_log.segment_rows(FakeRecorder({}), [(8.7, 11.7, 1.5)])
    assert total == pytest.approx(2.0)
    assert segments[0]["audio"] == [9.7, 11.7], "the picture runs 8.7 to 11.7 at 1.5x, the sound is its tail"
    kept, dropped, _outside = clip_log.remap([(8.9, "PP audio: text_blip_a played"),
                                              (9.7, "PP audio: text_blip_a played"),
                                              (11.5, "PP audio: text_blip_a played")], segments)
    assert [round(at, 3) for at, _line, _stamp, _index in kept] == [0.0, 1.8], \
        "9.70 s is the first second of the clip's sound and 11.50 s is 1.8 s into it"
    assert [(round(stamp, 2), index) for stamp, _line, index in dropped] == [(8.9, 0)], \
        "the 8.9 s blip was in the picture and not in the clip's sound, so it gets no place"


def test_the_write_is_refused_when_the_table_is_not_the_clip(tmp_path):
    """A table whose segments add to a different length than the file is a different take, so nothing is written."""
    folder = tmp_path / "demo_2026-11-04"
    folder.mkdir()
    (folder / "morgan_talk.mp4").write_bytes(b"")
    (folder / "story_good.events.json").write_text(
        json.dumps({"events": [[10.0, "PP audio: text_blip_a played"]]}), encoding="utf-8")
    module = FakeRecorder({"morgan_talk": ("story_good", [(10.0, 14.0, 1.0)])})
    with pytest.raises(clip_log.ClipLogError) as caught:
        clip_log.build(module, "morgan_talk", str(folder), seconds=30.0)
    assert "the table is not this clip" in str(caught.value)
    assert not (folder / "morgan_talk.events.json").exists(), "a refusal writes nothing"
    body, path = clip_log.build(module, "morgan_talk", str(folder), seconds=4.02)
    assert len(body["events"]) == 1 and path.endswith("morgan_talk.events.json")


def test_the_write_is_refused_when_the_run_kept_no_log(tmp_path):
    folder = tmp_path / "demo_2026-11-04"
    folder.mkdir()
    (folder / "morgan_talk.mp4").write_bytes(b"")
    module = FakeRecorder({"morgan_talk": ("story_good", [(10.0, 14.0, 1.0)])})
    with pytest.raises(clip_log.ClipLogError) as caught:
        clip_log.build(module, "morgan_talk", str(folder), seconds=4.0)
    assert "kept no log" in str(caught.value)


def test_the_file_says_it_was_derived_and_the_reader_finds_it_by_the_clip_s_name(tmp_path):
    """No change is needed in the events layer: the log sits beside the clip, named for it."""
    folder = tmp_path / "demo_2026-11-04"
    folder.mkdir()
    (folder / "morgan_talk.mp4").write_bytes(b"")
    (folder / "story_good.events.json").write_text(json.dumps({"events": [
        [10.4, "PP audio: text_blip_a played"],
        [10.5, "PP audio: text_blip_c played"],
        [12.0, "PP audio: encounter_swoosh played"]]}), encoding="utf-8")
    module = FakeRecorder({"morgan_talk": ("story_good", [(10.0, 14.0, 1.0)])})
    body, path = clip_log.build(module, "morgan_talk", str(folder), seconds=4.0)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(body, handle, indent=1)
    assert bed.event_log_for(str(folder / "morgan_talk.mp4")) == path
    assert clip_log.same(json.load(open(path, encoding="utf-8")), body), "the file it wrote reads back unchanged"
    with open(path, encoding="utf-8") as handle:
        written = json.load(handle)
    assert set(clip_log.RECORDER_KEYS) <= set(written), "the recorder's own keys, so a reader needs no change"
    assert written["derived"]["source_run"] == "story_good"
    assert written["derived"]["rule"].startswith("clip time =")
    assert written["derived"]["kept"] == 3 and written["derived"]["dropped_no_sound"] == 0
    # A stale file is caught rather than trusted: one stamp moved is enough.
    written["events"][0][0] = 0.0
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(written, handle, indent=1)
    assert not clip_log.same(written, body)


@pytest.mark.skipif(not (os.path.exists(MORGAN) and os.path.exists(STORY_GOOD_LOG)),
                    reason="the 2026-11-04 capture folder is not on this checkout")
def test_the_delivered_s5_log_matches_the_clip_and_its_run():
    """The real log, against ffprobe's own length for the clip the cut's S5 reads."""
    module = clip_log.load_table(clip_log.DEFAULT_RECORDER)
    body, path = clip_log.build(module, "morgan_talk", CAPTURES)
    assert os.path.exists(path), "the log beside the clip is the whole point: the events layer reads that name"
    assert body["name"] == "morgan_talk" and body["derived"]["source_run"] == "story_good"
    assert body["derived"]["clip_seconds"] == pytest.approx(clip_log.clip_seconds(MORGAN), abs=0.001)
    assert body["derived"]["segments_total_s"] == pytest.approx(
        sum(row["duration"] for row in body["derived"]["segments"]), abs=0.001)
    assert abs(body["derived"]["clip_seconds"] - body["derived"]["segments_total_s"]) <= clip_log.CLIP_TOLERANCE_S
    assert len(body["events"]) > 0
    stamps = [item[0] for item in body["events"]]
    assert stamps == sorted(stamps), "a log is read down its own clock"
    assert body["derived"]["dropped_no_sound"] > 0, "the 1.5x first segment leaves sound behind, and it is counted"
    assert all(item[1].startswith("PP") for item in body["events"]), "the recorder's lines, moved, not rewritten"
    # The clip's clock, not the run's: no row is stamped past the clip's own length.
    assert stamps[-1] < body["derived"]["clip_seconds"]


def test_the_cut_and_the_events_layer_resolve_a_source_s_log_by_the_same_rule(tmp_path):
    """Two readers, one rule: the cut's verify row must fail wherever the events layer would find nothing.

    The cut keeps its own copy of the naming rule (tools/demo_cut_180.py, `event_log_beside`) rather than
    importing the musician lane's mixing tool into a picture gate, so the two are pinned against each other
    here: same folder, named for the capture, `raw_` stripped, and nothing else.
    """
    import demo_cut_180 as cut

    folder = tmp_path / "demo_2026-11-04"
    folder.mkdir()
    (folder / "story_good.events.json").write_text("{}", encoding="utf-8")
    (folder / "morgan_talk.events.json").write_text("{}", encoding="utf-8")
    for source in ("raw_story_good.mkv", "story_good.mkv", "morgan_talk.mp4", "quay.mp4", "doors.mp4"):
        (folder / source).write_bytes(b"")
        mine = clip_log.os.path.basename(cut.event_log_beside(str(folder / source)) or "")
        theirs = clip_log.os.path.basename(bed.event_log_for(str(folder / source)) or "")
        assert mine == theirs, source
    assert cut.event_log_beside(str(folder / "quay.mp4")) is None, "a capture with no log resolves to nothing"
    assert cut.LOGGED_SHOTS == ("S4", "S5", "S6")
