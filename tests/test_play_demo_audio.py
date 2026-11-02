"""Pins for card DEMO-AUDIO-CAPTURE: a take's audio is the game's, and the verify file says which of the two it is.

What these tests hold down, and why each one earns its place:
  1. the field has exactly two values a final take may carry (game, reconstructed) and the old stand-in has no
     name and no code path in the tool, so it cannot come back by accident;
  2. the verdict really is a gate: a take labelled game or reconstructed passes and a take labelled none, a
     stand-in, or game with no audio stream in the file fails, and a file checked from disk with no record of
     its origin is UNMEASURED rather than a pass;
  3. the game's own log lines become the cues the game named, at the game's own gains (music 0.7, an effect 0.9,
     a text blip 0.45, a 6 dB duck 0.3508), and a line the tool cannot place becomes a note rather than a sound;
  4. a music cue the game asked for and could not start stays silent in the reconstruction, because the
     reconstruction reproduces the game's sound and not the sound the game was supposed to make;
  5. the track really renders: ffmpeg builds it from the same delivered files the game plays, the result is not
     silence (ffmpeg's own volumedetect mean), and the reconstruction reports its own first music second.

The cue files the game names at run time live under game/datafiles/, which .gitignore line 5 keeps out of every
commit, so the `delivered` fixture points the tool's two file tables at copies of tracked OGGs instead: a test
that read the real mirrors would pass on a machine that has built the game and fail in the gate's clean tree.

The mp4 itself is not muxed here: `python tools\\play_demo.py` does that, and a test that needs a game window
belongs to the capture harness and not to the suite (the same rule tests/test_play_demo.py states).

Run: python -m pytest tests/test_play_demo_audio.py -q
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

# Two delivered OGGs that ARE in the commit (data/audio.json names both), used as the cue files a log line names.
TITLE_OGG = os.path.join(ROOT, "assets", "audio", "pp_01_title", "pp_01_title.ogg")
SHIP_OGG = os.path.join(ROOT, "assets", "audio", "pp_05_small_ship", "pp_05_small_ship.ogg")

TITLE = "PP audio: title_theme streaming streams/title_theme_v3_126.ogg, instance 400001, gain 0.70"
# The bus logs the folder it opens, which is PP_AUDIO_MUSIC_DIR = streams/ (pp_audio.gml, card t_0c7a0a03):
# sync_art.mirror_streams copies each render there under its own basename, so this is the line a real run prints.
CUE = "PP audio: music cue PP-05 streaming streams/pp_05_small_ship.ogg, instance 400010, priority 10, fade 30 steps"
MISSING = "PP audio: music cue PP-07 has no OGG yet, expected streams/pp_07_prometheus_explains.ogg, placeholder true"
# The duck line the game prints for a 6 dB duck depth: the printed gain is the two-decimal GML string of
# 0.7 * 10^(-6/20) = 0.3508. The parser ignores the printed gain and re-derives it from the dB depth, so the
# gain assertions below use the full value, not this rounded string.
DUCK = "PP audio: title_theme ducked 6 dB, gain 0.35"
UNDUCK = "PP audio: title_theme back to full after 6 dB"
FOOTSTEP = "PP audio: footstep played, instance 400008"
BLIP = "PP audio: text_blip_a played, instance 400020"
STOP = "PP audio: music stopping over 30 steps"
# The two lines pp_audio_focus writes (game/scripts/pp_audio/pp_audio.gml:415 to :434). The pause line is the
# game's own account of the music stopping and every ringing effect being stopped; the resume line says the
# music came back where it stopped.
FOCUS_LOST = "PP audio: focus lost, music paused (cue and theme) and every effect stopped"
FOCUS_BACK = "PP audio: focus back, music resumed where it stopped"


def load_tool(name: str):
    path = os.path.join(TOOLS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# The tool loads tools/capture_title.py, which binds ctypes.windll at module level, so loading it on a host
# without the Windows path raises before any assertion runs: the same reason tests/test_play_demo.py marks its
# loader tests windows_only.
@pytest.fixture(scope="module")
def demo():
    return load_tool("play_demo")


@pytest.fixture
def delivered(demo, tmp_path, monkeypatch):
    """The tool's two file tables, pointed at copies of tracked OGGs and a one-row effect manifest.

    Nothing here is copied from game/datafiles/, which is gitignored: these are the same delivered audio bytes
    under the names the game's log prints, so the parser, the plan and the render measure the same way in a clean
    tree and on this host.
    """
    for path in (TITLE_OGG, SHIP_OGG):
        if not os.path.isfile(path):
            pytest.skip("%s is not on this checkout" % os.path.relpath(path, ROOT))
    streams = tmp_path / "streams"
    sfx = tmp_path / "sfx"
    streams.mkdir()
    sfx.mkdir()
    shutil.copyfile(TITLE_OGG, streams / "title_theme_v3_126.ogg")
    shutil.copyfile(TITLE_OGG, sfx / "footstep.ogg")
    shutil.copyfile(TITLE_OGG, sfx / "text_blip_a.ogg")
    # One effect long enough to still be ringing when the game's focus pause arrives, so the cut at the pause
    # second can be measured and not only asserted on a field.
    shutil.copyfile(TITLE_OGG, sfx / "long_ring.ogg")
    manifest = sfx / "sfx.json"
    manifest.write_text(json.dumps({"cues": [
        {"id": "footstep", "file": "footstep.ogg", "seconds": 0.5},
        {"id": "text_blip_a", "file": "text_blip_a.ogg", "seconds": 0.5},
        {"id": "long_ring", "file": "long_ring.ogg", "seconds": 4.0},
    ]}), encoding="utf-8")
    # The second STREAM_DIRS entry is the real assets folder, so the PP-05 line resolves against the tracked
    # file the way it does for real: the build's streams folder first, then the delivered originals.
    monkeypatch.setattr(demo, "STREAM_DIRS", (str(streams), os.path.join(ROOT, "assets", "audio")))
    monkeypatch.setattr(demo, "SFX_MANIFEST", str(manifest))
    if hasattr(demo.sfx_table, "_rows"):
        delattr(demo.sfx_table, "_rows")
    yield {"streams": streams, "sfx": sfx}
    if hasattr(demo.sfx_table, "_rows"):
        delattr(demo.sfx_table, "_rows")


def rows(*lines, step=1.0):
    """Log rows in the shape LogAudioWatch produces: the second a line arrived and the line itself."""
    return [{"at": round(index * step, 3), "line": line, "before_recording": index == 0}
            for index, line in enumerate(lines)]


# ---------------------------------------------------------------------------------------------------------------------
# 1: the field, and the code path that must not exist

@pytest.mark.windows_only
def test_the_two_honest_sources_and_no_stand_in_path_in_the_tool(demo):
    assert demo.AUDIO_SOURCES == ("game", "reconstructed"), "a final take may carry game or reconstructed audio"
    assert demo.AUDIO_SOURCE_NONE == "none" and demo.AUDIO_SOURCE_NONE not in demo.AUDIO_SOURCES
    assert not hasattr(demo, "render_stand_in_audio"), "the stand-in renderer must not exist on this tool"
    assert not hasattr(demo, "newest_theme"), "the stand-in track's source finder must not exist either"
    assert demo.LOOPBACK_INSTALL.startswith("audio install:") and "CABLE Output" in demo.LOOPBACK_INSTALL


# ---------------------------------------------------------------------------------------------------------------------
# 2: the verdict a take's verify file rests on

@pytest.mark.windows_only
def test_a_game_or_reconstructed_label_passes_and_nothing_else_does(demo):
    ok, line = demo.audio_check({"source": "game", "device": "CABLE Output"}, True)
    assert ok and line.startswith("PASS") and "CABLE Output" in line
    ok, line = demo.audio_check({"source": "reconstructed", "segments": [1, 2, 3],
                                 "first_music": {"cue": "title_theme", "at": 0.0}}, True)
    assert ok and line.startswith("PASS") and "title_theme enters at 0.00 s" in line
    for audio in ({"source": "none", "why": "no device and no log"}, {"source": "stand-in"},
                  {"source": "rendered"}, {}):
        ok, line = demo.audio_check(audio, True)
        assert not ok, "%r must not pass the audio check" % (audio,)
        assert line.startswith("FAIL") and "audio install:" in line
    ok, line = demo.audio_check({"source": "game", "device": "CABLE Output"}, False)
    assert not ok and "no audio stream" in line, "a game label over a silent file is a failure, not a pass"


@pytest.mark.windows_only
def test_a_check_from_disk_is_unmeasured_either_way_and_never_a_verdict(demo):
    """A file alone cannot say where its sound came from, so both answers are UNMEASURED and neither is a pass."""
    for has_audio in (True, False):
        ok, line = demo.audio_check(None, has_audio)
        assert ok and line.startswith("UNMEASURED"), line
        assert "sibling verify" in line
    # The run path is where the strictness lives: a record that is not game or reconstructed always fails.
    ok, line = demo.audio_check({"source": demo.AUDIO_SOURCE_NONE, "why": "probe"}, False)
    assert not ok and line.startswith("FAIL")


@pytest.mark.windows_only
def test_a_final_take_with_no_audio_record_fails_instead_of_measuring(demo):
    """The shipping question: a cut with no verify file beside it cannot answer, so it does not ship.

    `--check` on its own is a measurement and UNMEASURED is the honest answer for a file with no record. A take
    that is about to be submitted is a different question, and the difference between "not measured" and
    "allowed to ship" is the whole reason this card exists: output/demo/DEMO-CUT-V3.mp4, the cut that would be
    submitted, has no verify file at all (knowledge/READINESS-2026-10-26-R2.md).
    """
    for has_audio in (True, False):
        ok, line = demo.audio_check(None, has_audio, final=True)
        assert not ok, "a final take with no record of its audio may not pass"
        assert line.startswith("FAIL") and "no record" in line and "final take" in line, line
        # Without --final the same file still measures UNMEASURED and says so: the two questions stay distinct.
        ok_plain, plain = demo.audio_check(None, has_audio)
        assert ok_plain and plain.startswith("UNMEASURED")
    ok, line = demo.audio_check({"source": "reconstructed", "segments": [1], "first_music": {"cue": "x", "at": 0.0}},
                                True, final=True)
    assert ok and line.startswith("PASS"), "a labelled take still passes when the shipping question is asked"


@pytest.mark.windows_only
def test_check_final_asks_the_verifier_for_the_shipping_answer(demo, tmp_path, monkeypatch):
    """--final is wired to the verifier, so the flag is not a help string nobody reads.

    The script is supplied rather than read from disk on purpose: `DEFAULT_SCRIPT` names
    `data/demo/run_002.json`, that file is in the shared index but not in HEAD (measured 2026-10-27 18:26,
    `git ls-tree -r HEAD --name-only projects/primordial-paradox/data/demo` lists only `manifest.json` and
    `run_001.json`), and a test that trusted the default would go red in the gate's clean tree for a reason
    that has nothing to do with this flag.
    """
    seen = {}
    report = {"checks": {}, "has_audio": True, "audio_source": None}
    script = {"name": "pinned", "events": [{"step": 0, "beat": 1, "kind": "note", "id": "x"}],
              "clock": {"fps": 60}, "seeds": {}, "game": {}}

    def fake_verify(path, script, report_path=None, pollution=None, cues=None, audio=None, final=False,
                    shot_table=None):
        seen.update({"final": final, "audio": audio, "path": path, "shot_table": shot_table})
        return True, dict(report)

    monkeypatch.setattr(demo, "verify_video", fake_verify)
    monkeypatch.setattr(demo, "print_report", lambda report: None)
    monkeypatch.setattr(demo, "load_script", lambda path: script)
    take = tmp_path / "take.mp4"
    take.write_bytes(b"")
    monkeypatch.setattr(sys, "argv", ["play_demo.py", "--check", "--video", str(take)])
    assert demo.main() == 0
    assert seen["final"] is False and seen["audio"] is None, "without --final the question is the plain one"
    monkeypatch.setattr(sys, "argv", ["play_demo.py", "--check", "--final", "--video", str(take)])
    assert demo.main() == 0
    assert seen["final"] is True, "--final has to reach the verifier, or the shipping gate is a comment"


# ---------------------------------------------------------------------------------------------------------------------
# 3 and 4: the log lines, the gains, and what the game did not play

@pytest.mark.windows_only
def test_the_game_log_lines_become_the_cues_the_game_named(demo, delivered):
    events, notes = demo.audio_events(rows(TITLE, CUE, MISSING, DUCK, UNDUCK, FOOTSTEP, BLIP, STOP))
    assert notes == [], "every one of these lines is a shape the tool knows: %s" % notes
    kinds = [row["kind"] for row in events]
    assert kinds == ["music", "music", "music_missing", "duck", "unduck", "sfx", "sfx", "music_stop"], kinds
    music = [row for row in events if row["kind"] == "music"]
    assert [row["cue"] for row in music] == ["title_theme", "PP-05"]
    assert all(os.path.isfile(row["file"]) for row in music), "each music event names a file that is on disk"
    assert music[0]["file"].endswith("title_theme_v3_126.ogg")
    assert music[1]["file"].endswith("pp_05_small_ship.ogg")
    duck = [row for row in events if row["kind"] == "duck"][0]
    assert abs(duck["gain"] - 0.7 * 10 ** (-6 / 20.0)) < 1e-6, "the duck is the game's own 0.7 times a 6 dB duck depth"
    unduck = [row for row in events if row["kind"] == "unduck"][0]
    assert unduck["gain"] == demo.GAME_GAIN_MUSIC
    effects = {row["id"]: row["gain"] for row in events if row["kind"] == "sfx"}
    assert effects["footstep"] == demo.GAME_GAIN_SFX
    assert abs(effects["text_blip_a"] - demo.GAME_GAIN_SFX * demo.GAME_GAIN_BLIP_FACTOR) < 1e-9


@pytest.mark.windows_only
def test_a_line_the_tool_cannot_place_is_a_note_and_never_a_sound(demo, delivered):
    events, notes = demo.audio_events(rows("PP audio: mystery_chime played, instance 400099"))
    assert events == [], "an effect with no row in the manifest is not invented"
    assert notes and "mystery_chime" in notes[0]
    events, notes = demo.audio_events(rows("PP audio: title_theme streaming streams/not_a_theme.ogg, instance 1"))
    assert events == [] and notes and "not_a_theme.ogg" in notes[0]


@pytest.mark.windows_only
def test_a_cue_the_game_could_not_start_stays_silent_in_the_reconstruction(demo, delivered):
    events, _notes = demo.audio_events(rows(TITLE, MISSING))
    segments, silent = demo.log_audio_plan(events, 12.0)
    assert [row["cue"] for row in silent] == ["PP-07"]
    assert all(row["cue"] != "PP-07" for row in segments), "the reconstruction may not play what the game did not"
    assert "neither does the reconstruction" in silent[0]["why"]


@pytest.mark.windows_only
def test_the_plan_splits_the_music_at_the_games_own_duck(demo, delivered):
    events, _notes = demo.audio_events(rows(TITLE, DUCK, UNDUCK, STOP, step=10.0))
    segments, _silent = demo.log_audio_plan(events, 40.0)
    music = [row for row in segments if row["kind"] == "music"]
    assert len(music) == 3, "one music start, two gain changes: three pieces, not a guess at a ramp"
    assert [round(row["in"], 3) for row in music] == [0.0, 10.0, 20.0]
    assert music[0]["gain"] == demo.GAME_GAIN_MUSIC
    # The ducked gain is 0.7 * 10^(-6/20) = 0.3508, derived here rather than typed from memory; the plan carries
    # it rounded to four decimals.
    ducked = round(0.7 * 10 ** (-6 / 20.0), 4)
    assert abs(music[1]["gain"] - 0.7 * 10 ** (-6 / 20.0)) < 1e-3
    assert music[1]["gain"] == ducked
    assert music[2]["gain"] == demo.GAME_GAIN_MUSIC
    assert music[0]["fade_in"] > 0 and music[-1]["fade_out"] > 0, "the game's own crossfade at the edges only"
    assert music[1]["fade_in"] == 0.0 and music[1]["fade_out"] == 0.0, "a duck is instant in the game"


# ---------------------------------------------------------------------------------------------------------------------
# 5: the rebuild itself

@pytest.mark.windows_only
def test_a_log_with_nothing_to_place_is_a_failure_and_not_silence(demo, tmp_path):
    info = demo.reconstruct_audio([], 5.0, str(tmp_path / "nothing.m4a"))
    assert info["source"] == demo.AUDIO_SOURCE_NONE
    assert info["why"] and not os.path.exists(str(tmp_path / "nothing.m4a"))


@pytest.mark.windows_only
def test_the_rebuilt_track_really_renders_and_is_not_silence(demo, delivered, tmp_path):
    ffmpeg = demo.ffmpeg_path()
    if not ffmpeg:
        pytest.skip("ffmpeg is not installed on this host, so the rebuild cannot be measured here")
    out = str(tmp_path / "track.m4a")
    info = demo.reconstruct_audio(rows(TITLE, FOOTSTEP, BLIP, step=0.5), 4.0, out)
    assert info["source"] == "reconstructed", info.get("why")
    assert os.path.getsize(out) > 0
    assert info["mean_volume_db"] is not None and info["mean_volume_db"] > demo.SILENT_TRACK_DB
    assert info["first_music"]["cue"] == "title_theme" and info["first_music"]["at"] == 0.0
    # stdin is DEFINED, never inherited: on this host a parent with no valid standard input handle makes the
    # spawn itself raise OSError [WinError 6], measured in 2 of 5 identical runs (card t_668201ec, and
    # tests/conftest.py repeats the reason at its git probe). That is what made this test red once in the gate.
    probe = subprocess.run([demo.capture_module().ffprobe_path(ffmpeg),
                            "-v", "error", "-show_entries", "stream=codec_name,channels,sample_rate",
                            "-of", "json", out], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    streams = json.loads(probe.stdout or "{}").get("streams") or []
    assert streams and streams[0]["codec_name"] == "aac"
    assert streams[0]["sample_rate"] == "48000" and streams[0]["channels"] == 2, streams[0]


# ---------------------------------------------------------------------------------------------------------------------
# 6: the game's focus pause is part of the game's own sound (review round 1, correction 1)
#
# `pp_audio_focus` pauses the music and stops every ringing effect when the window loses focus, and resumes the
# music where it stopped when focus returns (game/scripts/pp_audio/pp_audio.gml:415 to :434, and
# knowledge/EVENT-LOG-AUDIO-MAP-2026-11-01.json maps focus_lost to music_pause and focus_back to music_resume).
# A rebuild that played through that pause would reproduce a sound the game never made.

@pytest.mark.windows_only
def test_the_rebuild_is_silent_where_the_log_records_the_focus_pause(demo, delivered):
    events, notes = demo.audio_events(rows(TITLE, FOCUS_LOST, FOCUS_BACK, step=10.0))
    assert notes == [], notes
    assert [row["kind"] for row in events] == ["music", "focus_lost", "focus_back"]
    assert demo.focus_windows(events, 40.0) == [(10.0, 20.0)]
    segments, _silent = demo.log_audio_plan(events, 40.0)
    music = [row for row in segments if row["kind"] == "music"]
    assert [(row["in"], row["out"]) for row in music] == [(0.0, 10.0), (20.0, 40.0)], \
        "no music segment may sit inside the pause the log records"
    # "resumed where it stopped" is the log's own wording: the piece after the pause starts at the playing time
    # the music had reached, which is neither 0 nor the second the resume line happened to arrive (20.0).
    assert music[1]["offset"] == 10.0, music[1]
    assert music[1]["offset"] != music[1]["in"]
    assert "resumed 10.000 s into the file" in music[1]["why"], music[1]["why"]
    assert music[0]["fade_in"] > 0 and music[0]["fade_out"] == 0.0, \
        "the game pauses dead: a piece that ends at the pause carries no fade out"
    assert music[1]["fade_in"] == 0.0, "the game resumes dead: no fade in after the pause"
    assert music[1]["fade_out"] > 0, "the game's own crossfade at the end of the cue only"


@pytest.mark.windows_only
def test_an_effect_ringing_when_the_pause_came_is_cut_there_and_a_later_one_is_kept(demo, delivered):
    ring = "PP audio: long_ring played, instance 400030"
    log = [{"at": at, "line": line, "before_recording": index == 0}
           for index, (at, line) in enumerate(((0.0, TITLE), (8.0, ring), (10.0, FOCUS_LOST),
                                               (30.0, FOCUS_BACK), (32.0, ring)))]
    events, notes = demo.audio_events(log)
    assert notes == [], notes
    segments, _silent = demo.log_audio_plan(events, 40.0)
    effects = [row for row in segments if row["kind"] == "sfx"]
    assert [(row["in"], row["out"]) for row in effects] == [(8.0, 10.0), (32.0, 36.0)], \
        "the effect that was ringing is cut at the pause, and the one the log prints after it is kept whole"
    assert "cut at 10.000 s" in effects[0]["why"], effects[0]["why"]


@pytest.mark.windows_only
def test_the_focus_reading_is_stated_in_the_record_and_not_chosen_in_silence(demo, delivered):
    reading = demo.FOCUS_EFFECTS_READING
    assert "already ringing" in reading, reading
    assert "kept" in reading, "the record has to say what happened to an effect line printed after the pause"
    assert "play line" in reading, "and why that reading follows from the log itself"


# ---------------------------------------------------------------------------------------------------------------------
# 7: every audio line is accounted for (review round 1, correction 2)

@pytest.mark.windows_only
def test_every_audio_line_ends_as_a_placement_a_silent_cue_or_a_note(demo, delivered):
    status = ("PP audio status: mode=title room=rm_pp_title cue=title_theme instance=400001 playing=1 "
              "gain=0.70 master=1 paused=0")
    unknown = "PP audio: a shape this tool has never seen"
    log = rows(TITLE, status, unknown, MISSING, FOCUS_LOST, FOCUS_BACK)
    events, notes = demo.audio_events(log)
    accounted = len(events) + len(notes)
    assert accounted == len(log), (
        "%d of the %d audio rows were left with no account of them: %d events and %d notes"
        % (len(log) - accounted, len(log), len(events), len(notes)))
    kinds = [row["kind"] for row in events]
    assert "music" in kinds and "music_missing" in kinds and "focus_lost" in kinds and "focus_back" in kinds, kinds
    assert any("no shape for" in note and "a shape this tool has never seen" in note for note in notes), notes
    assert any("state report" in note and "1 time" in note for note in notes), notes


# ---------------------------------------------------------------------------------------------------------------------
# 8: the rendered track is silent in the pause and sounds again after it

def window_mean_db(demo, path, start, seconds):
    """ffmpeg's own volumedetect mean over one window of the track, so a silence is measured and not assumed."""
    ffmpeg = demo.ffmpeg_path()
    result = subprocess.run([ffmpeg, "-hide_banner", "-nostats", "-ss", "%.3f" % start, "-t", "%.3f" % seconds,
                             "-i", path, "-af", "volumedetect", "-f", "null", "-"],
                            capture_output=True, text=True, stdin=subprocess.DEVNULL)
    for line in (result.stderr or "").splitlines():
        if "mean_volume:" in line:
            return float(line.split("mean_volume:")[1].strip().split()[0])
    return None


@pytest.mark.windows_only
def test_the_rendered_track_is_silent_in_the_pause_and_sounds_after_it(demo, delivered, tmp_path):
    ffmpeg = demo.ffmpeg_path()
    if not ffmpeg:
        pytest.skip("ffmpeg is not installed on this host, so the rebuild cannot be measured here")
    log = [{"at": at, "line": line, "before_recording": index == 0}
           for index, (at, line) in enumerate(((0.0, TITLE), (10.0, FOCUS_LOST), (20.0, FOCUS_BACK)))]
    out = str(tmp_path / "paused.m4a")
    info = demo.reconstruct_audio(log, 30.0, out)
    assert info["source"] == "reconstructed", info.get("why")
    assert info["focus"]["pauses"] == [{"from": 10.0, "to": 20.0}], info.get("focus")
    assert info["focus"]["effects"] == demo.FOCUS_EFFECTS_READING
    before = window_mean_db(demo, out, 1.0, 3.0)
    inside = window_mean_db(demo, out, 12.0, 5.0)
    after = window_mean_db(demo, out, 22.0, 3.0)
    assert before is not None and before > demo.SILENT_TRACK_DB, "the music sounds before the pause: %s dB" % before
    assert inside is not None and inside <= demo.SILENT_TRACK_DB, \
        "the pause the game recorded measures %s dB, which is not silence" % inside
    assert after is not None and after > demo.SILENT_TRACK_DB, "the music comes back after the pause: %s dB" % after
