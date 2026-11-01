"""Pins for the demo kit (card DEMO-KIT): the script is playable, and the manifest tells the truth about it.

What these tests hold down, and why each one earns its place:
  1. data/demo/run_001.json passes tools/play_demo.py's own validator, so the file the command reads is the
     file the validator accepts, and not a file that only looks right in an editor;
  2. the clock is honest: every step is a real step at the script's fps, the end step is inside the clock's
     own limit, and the planned recording is at least the 30 s the submission asks for;
  3. the manifest and the script cannot drift: every beat the manifest calls covered or partial is a beat the
     script actually plays, every event in the script is claimed by exactly one beat row, and every row the
     manifest calls not_reachable says why;
  4. the validator really refuses the four faults a script can have and still look plausible: a key the game
     does not read, a clock that goes backwards, a marker with no fallback (a run that hangs on a block
     buffered log), and a recording shorter than the submission needs;
  5. the finished-video check is a gate and not a print: a missing or empty file fails, and a black frame is
     measured as black. The mp4 itself is checked by `python tools\\play_demo.py --check`, which is not run
     here because ffmpeg and a screen are not guaranteed on the machine that runs the tests.

Run: python -m pytest tests/test_play_demo.py -q
"""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
SCRIPT = os.path.join(ROOT, "data", "demo", "run_001.json")
MANIFEST = os.path.join(ROOT, "data", "demo", "manifest.json")
BEAT_SHEET_TOTAL_S = 900


def load_tool(name: str):
    path = os.path.join(TOOLS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def script():
    return read_json(SCRIPT)


def manifest():
    return read_json(MANIFEST)


# Card TEST-CLASSIFY-33: the eight tests below call load_tool("play_demo"), and tools/play_demo.py
# imports capture_title, which binds ctypes.windll at module level, so the import raises on Linux and
# the test never reaches its assertion. They are marked windows_only for the reason in that loader.
@pytest.mark.windows_only
def test_the_script_the_command_reads_passes_its_own_validator():
    demo = load_tool("play_demo")
    problems = demo.validate_script(script())
    assert problems == [], "data/demo/run_001.json is refused by tools/play_demo.py: %s" % problems


@pytest.mark.windows_only
def test_the_clock_is_steps_at_sixty_a_second_and_covers_at_least_thirty_seconds():
    demo = load_tool("play_demo")
    data = script()
    fps = data["clock"]["fps"]
    assert fps == 60, "the clock is the game's own step rate: 60 a second, not %s" % fps
    seconds = demo.planned_seconds(data)
    assert seconds >= data["record"]["min_seconds"] >= 30
    end_step = data["checks"]["end_step"]
    assert seconds == end_step / float(fps)
    assert end_step <= data["clock"]["max_steps"], "the end step is past the clock's own limit"
    assert seconds == 71.0, "the run is 71 s: a change to it changes the submission, so it is pinned here"


def test_every_step_is_a_whole_step_and_the_steps_only_move_forward():
    data = script()
    steps = [event["step"] for event in data["events"]]
    assert steps == sorted(steps), "the events are not in clock order"
    assert steps[0] == 0, "the recording starts on the first event"
    assert all(isinstance(step, int) for step in steps)


def test_the_seeds_are_pinned_and_the_one_this_slice_reaches_is_named():
    data = script()
    seeds = data["seeds"]
    assert seeds["title_flash"] == 20261021, "PP_TITLE_FLASH_SEED is the attract's stream and is pinned"
    assert "note" in seeds and "PP_TITLE_FLASH_SEED" in seeds["note"]
    assert "not reached" in seeds["note"], "the seed note says which streams this run does not reach"


def test_the_manifest_has_all_thirty_two_beats_once_each():
    data = manifest()
    beats = [row["beat"] for row in data["beats"]]
    assert beats == list(range(1, 33)), "the beat sheet has 32 beats and the manifest must list each once"
    for row in data["beats"]:
        assert row["state"] in ("covered", "partial", "not_reachable"), row
        assert isinstance(row["title"], str) and row["title"], row
        assert isinstance(row["authored_s"], int) and row["authored_s"] > 0, row
    assert sum(row["authored_s"] for row in data["beats"]) == BEAT_SHEET_TOTAL_S


def test_the_manifest_summary_matches_its_own_rows():
    data = manifest()
    summary = data["summary"]
    for state in ("covered", "partial", "not_reachable"):
        expected = [row["beat"] for row in data["beats"] if row["state"] == state]
        assert summary[state] == expected, "%s in the summary does not match the rows" % state
    assert set(summary["covered"]) | set(summary["partial"]) | set(summary["not_reachable"]) == set(range(1, 33))


def test_no_beats_the_script_plays_are_missing_from_the_manifest():
    """The script's beats and the manifest's covered and partial beats are the same set, in both directions."""
    played = {event["beat"] for event in script()["events"]}
    claimed = set(manifest()["summary"]["covered"]) | set(manifest()["summary"]["partial"])
    assert played == claimed, ("the script plays beats %s but the manifest claims %s"
                               % (sorted(played), sorted(claimed)))


def test_every_event_is_claimed_by_a_beat_row_and_every_claim_names_a_real_event():
    """Every event is claimed, and a claim is never a stretch: an event belongs to one beat, or to two
    neighbours when it is the press that ends one beat and starts the next (e02 ends the attract and opens
    the menu, so it is honestly both)."""
    data = manifest()
    event_ids = {event["id"] for event in script()["events"]}
    claims = {}
    for row in data["beats"]:
        for identifier in row.get("events", []):
            assert identifier in event_ids, "beat %d claims %s, which is not in the script" % (row["beat"], identifier)
            claims.setdefault(identifier, []).append(row["beat"])
    assert set(claims) == event_ids, "these events are played but no beat row claims them: %s" % sorted(event_ids - set(claims))
    for identifier, beats in claims.items():
        assert len(beats) <= 2, "%s is claimed by %d beats: %s" % (identifier, len(beats), beats)
        if len(beats) == 2:
            assert beats[1] - beats[0] == 1, "%s is claimed by beats %s, which are not neighbours" % (identifier, beats)


def test_a_covered_or_partial_beat_carries_the_evidence_for_it():
    for row in manifest()["beats"]:
        if row["state"] in ("covered", "partial"):
            assert row.get("events"), "beat %d is %s but names no event" % (row["beat"], row["state"])
            assert isinstance(row.get("evidence"), str) and row["evidence"], "beat %d has no evidence" % row["beat"]


def test_the_unreachable_beats_say_why_and_the_count_is_stated():
    data = manifest()
    assert isinstance(data.get("not_reachable_why"), str) and "rm_pp_ship" in data["not_reachable_why"]
    assert len(data["summary"]["not_reachable"]) == 24, "24 of the 32 beats cannot be reached in this build"
    assert "must not be described as a 15 minute run" in data["summary"]["note"]


def test_the_command_is_the_one_in_the_manifest():
    assert "play_demo.py" in manifest()["command"]
    assert manifest()["script"] == "data/demo/run_001.json"


@pytest.mark.windows_only
def test_the_validator_refuses_a_key_the_game_does_not_read():
    demo = load_tool("play_demo")
    data = script()
    data["events"][1]["key"] = "enter-primed"
    problems = demo.validate_script(data)
    assert any("is not one of" in problem for problem in problems), problems


@pytest.mark.windows_only
def test_the_validator_refuses_a_clock_that_goes_backwards():
    demo = load_tool("play_demo")
    data = script()
    data["events"][2]["step"] = 10
    problems = demo.validate_script(data)
    assert any("backwards" in problem for problem in problems), problems


@pytest.mark.windows_only
def test_the_validator_refuses_a_marker_with_no_fallback_step():
    demo = load_tool("play_demo")
    data = script()
    del data["events"][3]["step"]
    problems = demo.validate_script(data)
    assert any("no fallback step" in problem for problem in problems), problems


@pytest.mark.windows_only
def test_the_validator_refuses_a_recording_under_thirty_seconds():
    demo = load_tool("play_demo")
    data = script()
    data["record"]["min_seconds"] = 12
    problems = demo.validate_script(data)
    assert any("at least 30" in problem for problem in problems), problems


@pytest.mark.windows_only
def test_the_video_check_fails_a_missing_file_instead_of_printing_a_pass():
    """The gate the submission rests on: no file, no pass. It runs before ffmpeg is ever asked for anything."""
    demo = load_tool("play_demo")
    scratch = tempfile.mkdtemp(prefix="pp_demo_")
    missing = os.path.join(scratch, "nothing_here.mp4")
    ok, report = demo.verify_video(missing, script())
    assert ok is False
    assert "FAIL the file is missing or empty" in report["checks"]["file"]


@pytest.mark.windows_only
def test_the_verify_file_is_named_after_the_mp4_and_not_after_the_script():
    """A re-recording written with --out must not overwrite the verdict of the take already on disk.

    run_002.mp4 wrote run_001_verify.json before this pin, so the file that described the good take was
    replaced by the verdict on the new one and the two could not be told apart.
    """
    demo = load_tool("play_demo")
    assert demo.out_stem(os.path.join("output", "demo", "run_002.mp4")) == "run_002"
    assert demo.out_stem("output/demo/run_001.mp4") == "run_001"
    assert demo.out_stem(os.path.join("D:" + os.sep, "repo", "output", "demo", "run_002.mp4")) == "run_002"


@pytest.mark.windows_only
def test_a_black_frame_measures_as_black_and_a_game_frame_does_not():
    from PIL import Image

    demo = load_tool("play_demo")
    scratch = tempfile.mkdtemp(prefix="pp_demo_")
    black = os.path.join(scratch, "black.png")
    Image.new("RGB", (768, 720), (0, 0, 0)).save(black, "PNG")
    assert demo.frame_luma(black) == 0.0
    bright = os.path.join(scratch, "bright.png")
    Image.new("RGB", (768, 720), (0, 120, 248)).save(bright, "PNG")
    assert demo.frame_luma(bright) > demo.MIN_MEAN_LUMA


# ---------------------------------------------------------------------------------------------------------------------
# Card t_688422b1 (judge panel 2026-10-31, fix 4): the take has to reach the end of its own clock, and the night it is
# recorded on has to hold the launch instead of spending it on one idle gate refusal.


@pytest.mark.windows_only
def test_the_submission_take_waits_for_the_gate_instead_of_taking_the_first_refusal():
    """900 s of patience is the fix for the NO VIDEO night, and it may never be shorter than the gate's own quiet.

    tools/idle_check.py allows a launch after MIN_IDLE_S of no input, so a wait below that number could only ever run
    out before a quiet minute existed. The wait is also not a way around the gate: the automation check refuses
    whatever this number is, so the test pins the number that buys patience and nothing else.
    """
    demo = load_tool("play_demo")
    idle = load_tool("idle_check")
    assert demo.IDLE_WAIT_S == 900.0, "the submission take's wait changed: %r s" % (demo.IDLE_WAIT_S,)
    assert demo.IDLE_WAIT_S >= idle.MIN_IDLE_S, (
        "a %r s wait cannot outlast the %r s of quiet the gate asks for" % (demo.IDLE_WAIT_S, idle.MIN_IDLE_S))
    # The bare command's own default, not a flag the caller has to remember: the nightly runs the command with no
    # arguments, and that is the call that lost 2026-10-30.
    text = open(os.path.join(TOOLS, "play_demo.py"), "r", encoding="utf-8").read()
    assert "add_launch_flags(parser, default_wait=IDLE_WAIT_S)" in text


@pytest.mark.windows_only
def test_a_path_on_another_drive_is_recorded_instead_of_raising():
    """The verify file records where a file is; `os.path.relpath` raises across drives, and that crashed a take.

    Card t_688422b1: tests/test_play_demo_audio.py::test_the_rebuilt_track_really_renders_and_is_not_silence writes its
    streams folder under the system temp, so the rebuilt track's first music file sits on C: while this repo is on D:,
    and the audio record raised `ValueError: path is on mount 'C:', start on mount 'D:'` inside a report writer. Four
    call sites did their own relpath; they all go through repo_relative now, and a path it cannot relativise is
    recorded in full rather than crashing the take.
    """
    demo = load_tool("play_demo")
    inside = demo.repo_relative(os.path.join(demo.ROOT, "data", "demo", "run_002.json"))
    assert inside == "data/demo/run_002.json", "a path inside the repo is not recorded relative to it: %r" % (inside,)
    foreign = demo.repo_relative(os.path.join("C:" + os.sep, "Users", "naran", "streams", "title_theme_v3_126.ogg"))
    assert "\\" not in foreign, "the recorded path kept Windows separators: %r" % (foreign,)
    assert foreign.endswith("title_theme_v3_126.ogg"), "the recorded path lost its file: %r" % (foreign,)


@pytest.mark.windows_only
def test_a_beat_the_game_never_names_does_not_end_the_take_early():
    """A marker is an accelerator, never a stop (card t_688422b1: "without early stop").

    The judged take of 2026-10-26 was 73.483 s against a 180 s plan. That number came from a 71 s script, but the
    property that matters here is separate and worth a pin: a beat whose log line never arrives costs the beat's own
    step and a line in the verify file, and the recording still runs to the end step with the last beat held on
    screen. Only a covering window stops a take early.
    """
    demo = load_tool("play_demo")
    scratch = tempfile.mkdtemp(prefix="pp_demo_")
    log_path = os.path.join(scratch, "game.log")
    with open(log_path, "w", encoding="utf-8") as handle:
        handle.write("PP: something else entirely\n")
    script = {"clock": {"fps": 60},
              "events": [{"id": "r001", "kind": "note", "step": 0},
                         {"id": "r002", "kind": "note", "step": 6, "marker": "PP scene: never written"}]}
    player = demo.Replay(script, 0, log_path, lambda *args, **kwargs: None)
    started = time.monotonic()
    failures = player.run(60)
    elapsed = time.monotonic() - started
    # The clock is what "without early stop" means: 1.0 s of end step plus the 30 step hold of the last beat, and the
    # run does not return before the hold is over. A run that stopped at the beat would return at about 0.1 s.
    assert elapsed >= 1.4, "the take stopped at %.2f s, before the 1.0 s end step and its 30 step hold" % elapsed
    assert any("never carried" in failure for failure in failures), (
        "a beat the game never named passed silently: %r" % (failures,))
    assert [row["id"] for row in player.trace] == ["r002"], (
        "a missing marker changed what was played: %r" % (player.trace,))
    assert player.trace[0]["at_step"] >= 6, "the beat fired before its own step: %r" % (player.trace[0],)
