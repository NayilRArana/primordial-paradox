"""Pins for card t_33648c51 (judge panel 2026-11-17, fix 1): a stopped take is still a file, and the delivered file
opens, reads 180 s and carries sound.

Why each test earns its place:
  1. the recorder asks ffmpeg for a fragmented mp4, because the 2026-11-16 take was 210501680 bytes with no moov atom
     after the worker's own 1500 s bound killed the harness, and no player, cutter or judge could open it;
  2. that flag does what it says, measured rather than asserted: a recording this host kills with TerminateProcess
     is still readable with it, and the same recording without it is not. That is the whole defect in two files;
  3. the finalise step writes the index at the head of the file and copies the take's own frames, so the delivered
     mp4 opens and plays from its first second instead of after a player has read all of it;
  4. the finalise refuses, in words, a take that has no index at all, because that file cannot be repaired and saying
     so costs one line while pretending repairs nothing;
  5. the delivery check is a gate: 180.0 s plus or minus 0.05 s and an audio stream that is not silence pass, and a
     duration that reads something else fails. That is the check the panel asked for, on the file it will open.

Run: python -m pytest tests/test_nightly_export.py -q
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")


def load_tool(name: str):
    path = os.path.join(TOOLS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def demo():
    """tools/play_demo.py, which imports tools/capture_title.py; that module binds ctypes.windll, so every test
    here is marked windows_only for the reason tests/test_play_demo.py states at its own loader."""
    return load_tool("play_demo")


@pytest.fixture(scope="module")
def ffmpeg(demo):
    path = demo.ffmpeg_path()
    if not path:
        pytest.skip("ffmpeg is not installed on this host, so no take can be recorded or measured here")
    return path


def record(demo, ffmpeg, path, seconds=30.0, audio=True, movflags=None, kill_after=None):
    """Record a synthetic window stand-in with the recorder's own encoder settings.

    testsrc2 and a sine wave stand in for the game window; what is measured is the container, which is what the
    2026-11-16 failure was about. `kill_after` is TerminateProcess, which is what the worker's own timeout did to the
    harness: ffmpeg gets no chance to finish the file.
    """
    command = [ffmpeg, "-hide_banner", "-v", "error", "-y",
               "-f", "lavfi", "-i", "testsrc2=size=320x240:rate=60"]
    if audio:
        command += ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000"]
    command += ["-t", "%.2f" % seconds, "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p"]
    if audio:
        command += ["-c:a", "aac", "-b:a", "96k"]
    if movflags:
        command += ["-movflags", movflags]
    command.append(path)
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if kill_after is None:
        _out, err = process.communicate(timeout=180)
        assert process.returncode == 0, (err or b"").decode("utf-8", "replace")[-600:]
    else:
        time.sleep(kill_after)
        assert process.poll() is None, ("the encoder finished before the kill, so nothing was interrupted and this "
                                        "test would prove nothing: ask for a longer take")
        process.kill()
        process.communicate(timeout=120)
    return path


def measured_duration(demo, ffmpeg, path):
    ffprobe = demo.capture_module().ffprobe_path(ffmpeg)
    return demo.capture_module().probe_duration(ffprobe, path)


# ---------------------------------------------------------------------------------------------------------------------
# 1: the recorder's own answer

@pytest.mark.windows_only
def test_the_recorder_asks_ffmpeg_for_a_fragmented_mp4(demo):
    arguments = demo.recorder_arguments((0, 0, 784, 759), "out.mp4", 30.0, 60, None)
    assert demo.FRAGMENTED_MOVFLAGS == "+frag_keyframe+empty_moov+default_base_moof"
    assert "-movflags" in arguments, "the recorder writes a plain mp4, so a kill leaves no moov atom at all"
    assert arguments[arguments.index("-movflags") + 1] == demo.FRAGMENTED_MOVFLAGS
    assert arguments.index("-movflags") < arguments.index("out.mp4"), "the flag belongs to the output, not the input"
    # The rectangle and the encoder settings the take has always used are untouched by this card.
    assert arguments[:2] == ["-f", "gdigrab"] and "-offset_x" in arguments and "-video_size" in arguments
    assert arguments[arguments.index("-c:v") + 1] == "libx264"
    # A caller that wants the old single index at the end can still ask for it, and the delivered file never does.
    plain = demo.recorder_arguments((0, 0, 784, 759), "out.mp4", 30.0, 60, None, fragmented=False)
    assert "-movflags" not in plain
    assert demo.FASTSTART_MOVFLAGS == "+faststart"


# ---------------------------------------------------------------------------------------------------------------------
# 2: the defect itself, measured

@pytest.mark.windows_only
def test_a_recording_the_host_kills_is_readable_when_it_was_fragmented(demo, ffmpeg, tmp_path):
    fragmented = str(tmp_path / "killed_fragmented.mp4")
    record(demo, ffmpeg, fragmented, seconds=900.0, movflags=demo.FRAGMENTED_MOVFLAGS, kill_after=2.0)
    assert os.path.getsize(fragmented) > 0
    assert demo.has_index(fragmented), "a fragmented take lost its index when it was killed, which is the defect back"
    duration = measured_duration(demo, ffmpeg, fragmented)
    assert duration is not None and duration > 0.2, duration

    plain = str(tmp_path / "killed_plain.mp4")
    record(demo, ffmpeg, plain, seconds=900.0, movflags=None, kill_after=2.0)
    assert not demo.has_index(plain), "a plain mp4 that was killed kept an index, so this test proves nothing"
    assert measured_duration(demo, ffmpeg, plain) is None, "ffprobe read a plain killed take, so this test proves nothing"


# ---------------------------------------------------------------------------------------------------------------------
# 3: the finalise step

@pytest.mark.windows_only
def test_the_finalise_writes_the_index_at_the_head_and_copies_the_takes_own_frames(demo, ffmpeg, tmp_path):
    source = record(demo, ffmpeg, str(tmp_path / "take.mp4"), seconds=3.0)
    assert not demo.index_at_head(source), "a plain mp4 already has its index at the head, so this test proves nothing"
    source_duration = measured_duration(demo, ffmpeg, source)
    out = str(tmp_path / "nightly.mp4")
    ok, note = demo.finalize_recording(source, out)
    assert ok, note
    assert demo.index_at_head(out), note
    assert measured_duration(demo, ffmpeg, out) == pytest.approx(source_duration, abs=0.05), "the remux changed the length"
    ffprobe = demo.capture_module().ffprobe_path(ffmpeg)
    assert demo.audio_stream(ffprobe, out), "the remux dropped the audio stream"
    assert not [name for name in os.listdir(str(tmp_path)) if name.endswith(".part.mp4")], "the partial file was left"


@pytest.mark.windows_only
def test_a_fragmented_take_that_finished_is_finalised_the_way_the_run_finalises_it(demo, ffmpeg, tmp_path):
    """The recorder writes fragmented, so the run's own finalise reads a fragmented file every night, not a plain one."""
    source = record(demo, ffmpeg, str(tmp_path / "fragmented.mp4"), seconds=3.0,
                    movflags=demo.FRAGMENTED_MOVFLAGS)
    assert demo.has_index(source), "a finished fragmented take has no index, so the run could never finalise one"
    source_duration = measured_duration(demo, ffmpeg, source)
    out = str(tmp_path / "nightly.mp4")
    ok, note = demo.finalize_recording(source, out)
    assert ok, note
    assert demo.index_at_head(out), note
    assert measured_duration(demo, ffmpeg, out) == pytest.approx(source_duration, abs=0.05)


# ---------------------------------------------------------------------------------------------------------------------
# 4: a take that cannot be repaired says so

@pytest.mark.windows_only
def test_the_finalise_refuses_a_take_with_no_index_and_says_it_has_to_be_rerecorded(demo, ffmpeg, tmp_path):
    killed = str(tmp_path / "killed_plain.mp4")
    record(demo, ffmpeg, killed, seconds=900.0, movflags=None, kill_after=2.0)
    assert not demo.has_index(killed)
    out = str(tmp_path / "never.mp4")
    ok, note = demo.finalize_recording(killed, out)
    assert not ok
    assert "no index" in note and "re-recorded" in note, note
    assert not os.path.exists(out), "a refused finalise must not leave a file that looks delivered"
    ok, note = demo.finalize_recording(str(tmp_path / "absent.mp4"), out)
    assert not ok and "no take" in note, note


# ---------------------------------------------------------------------------------------------------------------------
# 5: the delivery gate the panel asked for

@pytest.mark.windows_only
def test_the_delivery_check_holds_a_file_to_its_duration_and_its_sound(demo, ffmpeg, tmp_path):
    take = record(demo, ffmpeg, str(tmp_path / "take.mp4"), seconds=2.0)
    out = str(tmp_path / "delivered.mp4")
    ok, note = demo.finalize_recording(take, out)
    assert ok, note
    ffprobe = demo.capture_module().ffprobe_path(ffmpeg)
    duration = measured_duration(demo, ffmpeg, out)
    rows = {name: (passed, detail) for name, passed, detail in
            demo.playback_checks(ffprobe, out, target_seconds=duration, tolerance=0.05, decode=True)}
    assert rows["opens"][0] and rows["duration"][0] and rows["audio"][0], rows
    assert rows["not_silent"][0], rows["not_silent"]
    assert rows["faststart"][0], rows["faststart"]
    assert rows["decodes"][0], rows["decodes"]

    wrong = {name: (passed, detail) for name, passed, detail in
             demo.playback_checks(ffprobe, out, target_seconds=180.0, tolerance=0.05)}
    assert not wrong["duration"][0], "a %.3f s file passed the 180.0 s gate" % duration
    assert "180.000" in wrong["duration"][1]


@pytest.mark.windows_only
def test_the_delivery_check_fails_a_silent_or_soundless_file(demo, ffmpeg, tmp_path):
    silent = record(demo, ffmpeg, str(tmp_path / "silent.mp4"), seconds=2.0, audio=False)
    out = str(tmp_path / "delivered.mp4")
    ok, note = demo.finalize_recording(silent, out)
    assert ok, note
    ffprobe = demo.capture_module().ffprobe_path(ffmpeg)
    rows = {name: passed for name, passed, _detail in demo.playback_checks(ffprobe, out, target_seconds=2.0)}
    assert not rows["audio"], "a file with no audio stream passed the audio check"


@pytest.mark.windows_only
def test_the_delivery_check_fails_a_take_that_carries_no_index(demo, ffmpeg, tmp_path):
    killed = str(tmp_path / "killed_plain.mp4")
    record(demo, ffmpeg, killed, seconds=900.0, movflags=None, kill_after=2.0)
    ffprobe = demo.capture_module().ffprobe_path(ffmpeg)
    rows = {name: passed for name, passed, _detail in demo.playback_checks(ffprobe, killed, target_seconds=180.0)}
    assert not rows["opens"], "a take with no index passed the opens check"
    assert not rows["audio"], "a take with no index passed the audio check"


# ---------------------------------------------------------------------------------------------------------------------
# 6: the export writes its evidence

@pytest.mark.windows_only
def test_the_export_writes_a_verify_file_naming_the_take_and_its_checks(demo, ffmpeg, tmp_path):
    take = record(demo, ffmpeg, str(tmp_path / "take.mp4"), seconds=2.0)
    out = str(tmp_path / "nightly-2026-11-16.mp4")
    duration = measured_duration(demo, ffmpeg, take)
    code = demo.finalize_take(take, out, target_seconds=duration, tolerance=0.05, decode=True,
                              source_note="built by the test from testsrc2")
    assert code == 0
    report = json.load(open(out[: -len(".mp4")] + "_verify.json", "r", encoding="utf-8"))
    assert report["video"].endswith("nightly-2026-11-16.mp4")
    assert report["source"]["path"].endswith("take.mp4")
    assert report["source"]["carried_an_index"] is True
    assert report["source"]["note"] == "built by the test from testsrc2"
    assert report["finalised"]["index_at_head"] is True
    names = [row["name"] for row in report["checks"]]
    assert names[:4] == ["opens", "duration", "audio", "not_silent"], names
    assert all(row["ok"] for row in report["checks"]), report["checks"]


@pytest.mark.windows_only
def test_the_export_returns_red_for_a_take_the_gate_refuses(demo, ffmpeg, tmp_path):
    take = record(demo, ffmpeg, str(tmp_path / "take.mp4"), seconds=2.0)
    out = str(tmp_path / "nightly-2026-11-16.mp4")
    code = demo.finalize_take(take, out, target_seconds=180.0, tolerance=0.05, decode=False)
    assert code == 1, "a 2 s take passed a 180.0 s delivery gate"
    assert os.path.isfile(out), "the finalised file is still a file; it is the gate that says it is not the delivery"


# ---------------------------------------------------------------------------------------------------------------------
# 7: the replay stops when the tape is spent, so the harness always reaches its finalise, its cut and its verify

@pytest.mark.windows_only
def test_the_replay_stops_when_the_recorder_bound_is_spent_and_says_which_stop_it_was(demo, tmp_path):
    """On 2026-11-16 the replay outlived the recorder's -t and the worker's own 1500 s bound killed the harness mid
    take, so the crop, the audio rebuild and the verify never ran. The stop is now the tape's own, and it is named."""
    script = {"name": "tape", "clock": {"fps": 60},
              "events": [{"id": "r001", "kind": "note", "step": 60},
                         {"id": "r002", "kind": "note", "step": 120}]}
    replay = demo.Replay(script, hwnd=0, log_path=str(tmp_path / "game.log"), send_key=lambda vk: None)
    failures = replay.run(120, should_stop=lambda: True,
                          stop_reason=lambda: ("tape-stop", "the recorder's own 256.0 s bound was spent"))
    assert failures == []
    assert len(replay.trace) == 1, "the replay played events after the tape was spent: %s" % replay.trace
    assert replay.trace[0]["id"] == "tape-stop" and replay.trace[0]["kind"] == "stop"
    assert "256.0 s bound" in replay.trace[0]["detail"]
    # A caller that passes no reason keeps the pollution wording, which is the stop that existed before this card.
    plain = demo.Replay(script, hwnd=0, log_path=str(tmp_path / "game.log"), send_key=lambda vk: None)
    plain.run(120, should_stop=lambda: True)
    assert plain.trace[-1]["id"] == "pollution-stop"

