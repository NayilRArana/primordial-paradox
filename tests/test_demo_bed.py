"""Pins for the demo bed's beat table (card t_81178392): the bed follows the picture, not a game constant.

What these tests hold down, and why each one earns its place:
  1. the title's handoff second is the trace's marker step MINUS the run script's own marker_delay_steps, so the
     1.000 s delay the capture adds can never become a picture second again;
  2. the room load is that handoff plus the app machine's PP_FADE_STEPS 12, so the ship cue enters on the frame
     the mode swaps on and not on the second the marker was read;
  3. the drive cue cannot come back into this bed: no segment names the drive map's cue, beat 6 ends on the run
     script's own e07 hold, and beat 7 runs to the room load instead of a 240 step drive subtracted from e08;
  4. a trace that never saw the marker is refused rather than measured from the script's fallback step, because
     that step is the script's own number and measures nothing;
  5. the 32 beat accounting still covers 8 beats and calls the other 24 silent, so the table stays complete.

The recording's own verify file is deliberately not read here: output/ is gitignored, so a test that needed it
would fail in the gate's tree, which is built from the index. The two fixtures below are that file's shape and
carry its measured numbers (demo-talk-2026-10-26: e02 at 10.067 s, e04 at 11.567 s, e08 at 43.167 s).

Run: python -m pytest tests/test_demo_bed.py -q
"""

from __future__ import annotations

import importlib.util
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
FPS = 60
DURATION_S = 73.5


def load_tool(name: str):
    path = os.path.join(TOOLS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(marker_second: float = 43.167, detail: str = "marker 'starting the run in' seen") -> dict:
    """One recording's verify file, in the shape tools/play_demo.py writes."""
    return {
        "duration_s": DURATION_S,
        "run": {
            "trace": [
                {"id": "e02", "kind": "key", "detail": "enter", "at_second": 10.067, "at_step": 604},
                {"id": "e04", "kind": "marker", "detail": "marker 'PP title: intro started' seen",
                 "at_second": 11.567, "at_step": 694},
                {"id": "e08", "kind": "marker", "detail": detail,
                 "at_second": marker_second, "at_step": int(round(marker_second * FPS))},
            ]
        },
    }


def script(marker_delay_steps: int = 60) -> dict:
    """The run script's own events, in the shape data/demo/run_001.json writes."""
    return {
        "events": [
            {"id": "e02", "step": 600, "kind": "key"},
            {"id": "e05", "step": 1500, "kind": "note"},
            {"id": "e06", "step": 1900, "kind": "note"},
            {"id": "e07", "step": 2340, "kind": "note"},
            {"id": "e08", "step": 3300, "kind": "note", "marker": "starting the run in",
             "marker_delay_steps": marker_delay_steps},
        ]
    }


def planned():
    bed = load_tool("demo_bed")
    audio = bed.load_json(bed.AUDIO_REL)
    maps = bed.load_json(bed.MAPS_REL)
    segments, windows = bed.plan(verify(), script(), audio, maps)
    return bed, audio, maps, segments, windows


def test_the_handoff_is_the_line_and_not_the_recorded_step():
    bed = load_tool("demo_bed")
    # 43.167 is the step the capture read the line on, plus the script's 60 step delay
    assert bed.handoff_second(verify(), script()) == pytest.approx(43.167 - 60 / FPS)
    # with no delay in the script the same trace reads 1.000 s later, so the number is read and not typed
    assert bed.handoff_second(verify(), script(marker_delay_steps=0)) == pytest.approx(43.167)


def test_the_room_load_is_the_black_frame_after_the_handoff():
    bed = load_tool("demo_bed")
    windows = bed.beat_windows(verify(), script())
    by_beat = {row["beat"]: row for row in windows}
    handoff = 43.167 - 60 / FPS
    # the app machine swaps mode at the black frame, PP_FADE_STEPS 12 after the title hands over
    assert by_beat[26]["start"] == pytest.approx(handoff + 12 / FPS)
    # beat 6 ends on the run script's own hold, and beat 7 starts there, with no subtracted drive
    assert by_beat[7]["start"] == pytest.approx(2340 / FPS)
    assert by_beat[6]["end"] == pytest.approx(by_beat[7]["start"])
    assert by_beat[7]["end"] == pytest.approx(by_beat[26]["start"])
    assert by_beat[26]["end"] == pytest.approx(DURATION_S)


def test_no_segment_carries_the_drive_cue():
    bed, audio, maps, segments, windows = planned()
    cue_ids = [seg["cue"] for seg in segments]
    assert cue_ids == ["PP-01", "PP-01", "PP-05"]
    assert bed.cue_for_map(maps, "drive_m4_corridor") not in cue_ids
    # the ship cue enters on the handoff, so its 0.500 s crossfade is at full gain on the room itself
    handoff = bed.handoff_second(verify(), script())
    assert segments[-1]["in"] == pytest.approx(handoff)
    # the ducked pass hands over at the same second, which is where pp_title calls pp_audio_unduck
    assert segments[1]["out"] == pytest.approx(segments[-1]["in"] + bed.FADE_S)
    # the bed is still exactly as long as the recording
    assert segments[-1]["out"] == pytest.approx(DURATION_S)
    # and the two boundaries are in order, so no segment is a backwards read
    assert segments[0]["in"] < segments[1]["in"] < segments[2]["in"]


def test_a_marker_the_trace_never_saw_is_refused():
    bed = load_tool("demo_bed")
    unseen = verify(detail="marker 'starting the run in' not seen, step used")
    with pytest.raises(SystemExit):
        bed.handoff_second(unseen, script())


def test_all_32_beats_stay_accounted_for():
    bed, audio, maps, segments, windows = planned()
    rows = bed.accounting(windows, segments)
    assert len(rows) == 32
    covered = [row["beat"] for row in rows if row["state"] == "covered"]
    assert covered == [1, 2, 3, 4, 5, 6, 7, 26]
    assert len([row for row in rows if row["state"] == "silent"]) == 24
