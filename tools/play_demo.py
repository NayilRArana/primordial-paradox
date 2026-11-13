#!/usr/bin/env python3
"""play_demo.py: one command that plays a scripted run of the built game and records it to an mp4.

Why this file exists: the hackathon submission needs a video of real gameplay that can be re-recorded the
night before the deadline, by one command, without a person at the keyboard and without a new take each
time something in the title moves. So the run is data (data/demo/run_001.json: key presses on a 60 step a
second clock, the seeds the slice actually reaches, and the game's own log lines as the sync points), and
this tool is the player.

It is not a second capture harness. Every window and key primitive is the one tools/capture_title.py
already proved on this PC: the window is found by process image name (not by title), it is raised with the
foreground lock lifted, every key goes through the input queue because a GameMaker game reads key state and
a posted key is a dud, and the rectangle is checked for a covering window before recording and every second
while it records. What
this file adds is the script, the clock, the ffmpeg recording at 60 fps cut to a true 3x of the NES screen,
and a check that the result is a video of the game and not of a terminal.

The mp4 is 768x720, which is exactly 3x the 256x240 screen the game draws (measured: a 768x720 viewport at
[8, 31] inside a 784x759 window, tests/test_capture_title.py). The window rectangle is recorded as it is
and then cropped to the viewport that tools/nes_composite_check.py finds in a pre-roll frame, so the frame
is the game's own pixels and not the desktop's scaling of them. A frame of a terminal, of the desktop or of
a cover window has no such viewport and is refused.

Audio has exactly two honest answers and no third (card DEMO-AUDIO-CAPTURE). With a loopback capture device
or a virtual cable (a CABLE Output, a Stereo Mix, a virtual-audio-capturer) the game's own output is recorded
with the video, and the verify file's `audio_source` says "game". Without one, the track is rebuilt from the
game's own log: every "PP audio:" line the game writes is stamped with the second it arrived on the
recording's clock, and the same file the line names is placed at that second, at the gain the game plays it
at, with the game's own 30 step crossfade and its 6 dB intro duck. The verify file then says "reconstructed",
and the mp4's own comment says so in words. A take with neither is a failure and never a silent pass. The old
stand-in (one title theme looped over the whole film) is gone: a take recorded after 2026-10-30 may not carry
it. `--audio-devices` prints this host's ffmpeg device list and the one install a machine without a loopback
needs.

Pollution (card t_5d1a6ec4): the rectangle is asked who owns it every second while the recording runs, not
only before and after, and its pixels are read once a second as well. A foreign window found there stops the
run and marks the take POLLUTED, named by the process that owned the pixels; it is never reported as the art
lane's finding. A take checked from disk alone (`--check`) has no run log, so there the verdict comes from the
frames: a sampled frame with fewer than half its pixels on the 2C02 palette is not the game, because the game
resolves every colour through data/palette_ppu.json, and a frame between that floor and the 0.90 palette floor
is the art lane's. Measured on 2026-10-26: 33 frames of the game scored 0.9285 to 0.9939, the two covered
frames of the demo-box take scored 0.0024 and 0.0025.

A window that owns a sampled point once the recording has stopped is a NOTE beside the checks and never a
failure (card t_4da3eb20). It is asked before the window that was in front when the run started is restored,
because asking after that restore measures the window this tool itself raised; and the answer is evidence only,
because the owner samples taken during the recording are the verdict and the frames of the finished file are
the second net.

Usage:
    python tools\\play_demo.py                        play data\\demo\\run_002.json and record output\\demo\\run_002.mp4
                                                      (the 253.5 s three battle take, the QA take, card t_785b61f0; run_001.json is the
                                                      71 s walk take and is named with --script when it is wanted)
    python tools\\play_demo.py --shot-table full      the same take, played as the named shot table in
                                                      data\\demo\\shot_table.json: the table names its script, its six
                                                      shots and four sub-shots, the second each one runs from, and the
                                                      game's own log line each shot has to produce. The table's
                                                      durations have to sum to 180.00 s inside the table's own
                                                      tolerance (1.0 s), and the take is failed by name when a shot's
                                                      line never appears (card t_fb7e8271)
    python tools\\play_demo.py --shot-table full --dry-run
                                                      print the table's rows and its sum, without launching the game
    python tools\\play_demo.py --script data\\demo\\run_001.json --out output\\demo\\x.mp4
    python tools\\play_demo.py --check                re-check the mp4 the script names, without launching the game
    python tools\\play_demo.py --check --video P.mp4  check some other file the same way
    python tools\\play_demo.py --check --final --video P.mp4
                                                      the shipping question: a take with no verify file beside it
                                                      fails its audio check instead of measuring UNMEASURED
    python tools\\play_demo.py --dry-run              validate the script and print the timeline in seconds
    python tools\\play_demo.py --audio-devices        print the capture devices, the loopback and the install, no run

A take also writes <stem>_audio.m4a beside the mp4 when its track was rebuilt from the game's own log (card
DEMO-AUDIO-CAPTURE), and <stem>_cues.json: the beats of the shot table the game's own log named, the footstep
count, and which leg of the TALK path the take used. `--check` reads both, because a video file alone cannot say
that.

Event kinds (card PP-FREE-MOVE): `note` is a beat with no input, `key` is one press, and `hold` is a key that goes
down at `step`, stays down for `steps` and comes up. Since the overworld walks while a direction is HELD, a walk beat
on the map is a `hold`; a press moves the walker a couple of pixels and no further.

Exit codes:
    0  the recording passed every check, or --check passed, or --dry-run validated the script
    1  a check failed, or the script is malformed, or the game window never appeared
    3  the watchdog fired (the run overran)
    4  the idle gate refused to open a window: the user had input in the last three minutes (card CAPTURE-QUIET),
       or a desktop automation was driving the keyboard for the whole wait, or this host cannot draw at all, in
       which case the run is not measured and nothing is claimed about it

Quiet by default (card CAPTURE-QUIET, Nayil 2026-10-22): the game is started with PP_MUTE=1 so nothing plays, no
window opens unless the idle gate in tools\\idle_check.py sees three quiet minutes, and the window is moved off the
primary screen. --sound is for an audio proof, --show leaves the window where it is, --force is a human override.

The wait (card t_688422b1): the bare command asks the gate for up to IDLE_WAIT_S (900 s) instead of taking the first
refusal, so a night that finds the desktop busy holds its one attempt rather than recording nothing. That is patience
and not a way round the gate: while codex.exe or codex-computer-use-swift.exe is running the gate keeps refusing, wait
or no wait, because a window opened under a desktop automation is covered mid take. `--idle-wait 0` restores the old
skip at once, which is what a person who wants the attempt to fail fast should pass.

Portable import (card PINE-HONEST, 2026-10-24): the two modules this tool draws and launches with,
tools\\capture_title.py and tools\\pp_launch.py, import ctypes.wintypes at their own line 39 and line 41, which raises
on a host without the Windows path. Imported at the top of this file they killed it before it could say anything, and
that traceback, not a test result, is what 19 of the 21 Pine reds measured on 2026-10-24 were. Both are now imported
inside the function that uses them, and a host that cannot import them prints one line, "play_demo: unavailable on
this platform", and exits 4 (the harness's not-measured lane, EXIT_REFUSED) instead of passing
silently or going red.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS_DIR)
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import idle_check  # noqa: E402  EXIT_REFUSED = 4, the harness's not-measured lane, imported instead of restated
import receipts  # noqa: E402  card t_7450df91: the labels and the receipt ledger the verify file carries

# Card PINE-HONEST: the two modules this tool draws and launches with are imported inside the functions that use
# them, never here. tools/capture_title.py:39 and tools/pp_launch.py:41 each import ctypes.wintypes, which raises on a
# host without the Windows path (Pine is Linux), so a module level import turns "this host cannot draw" into a
# traceback with no exit code and no line for a reader. See capture_module(), launch_module() and unavailable().
EXIT_UNAVAILABLE = idle_check.EXIT_REFUSED
UNAVAILABLE_LINE = "play_demo: unavailable on this platform"

_capture_title = None
_pp_launch = None


class PlatformUnavailable(Exception):
    """This host cannot draw or focus a window, so nothing this tool measures exists here."""


def unavailable(error):
    """The one line a host without the drawing path prints, and the not-measured code that goes with it.

    4 is not a pass and not a red (tools/idle_check.py:48; capture_first_fight.py, capture_drive.py, capture_save.py
    and _save_load_probe.py already return it), so a runner reading it records "not measured" instead of scoring it.
    """
    print(UNAVAILABLE_LINE)
    print("  %s, so this run is not measured" % error)
    return EXIT_UNAVAILABLE


def can_draw():
    """True when this host can import the drawing path and has window primitives to draw with.

    The import is asked for first, so a host that cannot even import it raises PlatformUnavailable out to the caller
    and gets the same one line. Off Windows the module imports but there is no window to copy, which is what
    capture_title's own WINDOW_PRIMITIVES flag says; a version of capture_title without that flag is asked the
    platform question directly.
    """
    capture = capture_module()
    return bool(getattr(capture, "WINDOW_PRIMITIVES", sys.platform == "win32"))


def capture_module():
    """tools/capture_title.py, imported on first use. The proved window and key primitives, shared, never copied."""
    global _capture_title
    if _capture_title is None:
        try:
            import capture_title
        except Exception as error:  # the drawing path is all or nothing here, so every failure is the same answer
            raise PlatformUnavailable("capture_title could not be imported: %s" % error)
        _capture_title = capture_title
    return _capture_title


def launch_module():
    """tools/pp_launch.py, imported on first use: the launch policy, the idle gate, and the quiet window."""
    global _pp_launch
    if _pp_launch is None:
        try:
            import pp_launch
        except Exception as error:  # same answer as above: a launcher that cannot launch is not a launcher
            raise PlatformUnavailable("pp_launch could not be imported: %s" % error)
        _pp_launch = pp_launch
    return _pp_launch


# What this process may do with a window and with sound. main() replaces it from the flags; run_demo reads it.
LAUNCH = None


DEMO_DIR = os.path.join(ROOT, "data", "demo")
OUTPUT_DIR = os.path.join(ROOT, "output", "demo")
BUILD_DIR = os.path.join(ROOT, "build")
DEFAULT_SCRIPT = os.path.join(DEMO_DIR, "run_002.json")
MANIFEST = os.path.join(DEMO_DIR, "manifest.json")
# Card t_fb7e8271: the shot table as data. One file, one table per name, and every table names its script, its shots and
# the game's own log line each shot has to produce, so the take and the write-up cannot drift without a word here.
SHOT_TABLE = os.path.join(DEMO_DIR, "shot_table.json")
# The sum a table's own durations have to land inside. Not zero: S3 carries the drive list's 602 steps (10.03 s), and a
# recorded file's duration is measured from the container and never equals the plan to the frame.
SHOT_TABLE_TOLERANCE_S = 1.0
# Card t_e48b13a6: the two S6 win paths, selectable by name. A path is a shot table with a shorter name, so one flag
# plays the documented take and the table still names the script, the shots and the log lines the run has to produce.
PATH_TABLES = {"talk": "talk-win", "command": "command-win"}
PATH_WHY = {
    "talk": "TALK three times so the meter climbs to 60, then SPARE: the fight ends with no blow thrown",
    "command": "one Confirm on FIGHT against the deck hound's 2 hp: the fight ends in a single command",
}
# A shot row that carries any of these is refused: this take carries no narrator, no narration and no voice over.
# The captions DEMO-SCRIPT.md names are drawn by the edit (R44) and never by the recorder, and this list is what keeps
# a voice over from arriving here as a field somebody adds without noticing the rule.
NARRATION_KEYS = ("narrator", "narration", "narrator_text", "voiceover", "voice_over", "voice-over")

# Card t_688422b1 (judge panel 2026-10-31, fix 4): the nightly of 2026-10-30 recorded NO VIDEO, and the reason was
# not the route. play_demo asked the idle gate once, took the refusal, and the whole night was lost to a desktop
# automation that had the keyboard at that second. A take that needs a quiet desktop waits for the gate; it never
# defeats it. So the bare command now holds the launch for this long, asking every tools\idle_check.py POLL_S, and a
# quiet minute is taken the moment it arrives. 900 s is the longest a night can be held without spoiling the
# submission date: the gate's own three quiet minutes plus room for an automation to finish what it is doing. The gate
# still refuses while codex.exe or codex-computer-use-swift.exe runs, wait or no wait (tools\idle_check.py:201-217),
# so this buys patience and never a covered take; --idle-wait 0 asks for the old skip at once, and --force is still
# the human override.
IDLE_WAIT_S = 900.0

# The frames the run is checked on, as a share of the recording: the start, then every sixth. Sampling on
# fractions of the measured duration rather than on fixed seconds keeps the check valid for a longer script.
SAMPLE_FRACTIONS = (0.02, 0.18, 0.34, 0.5, 0.66, 0.84, 0.95)
# A frame of the game that is not a fade has a mean luma well above a black screen's. Measured on the
# 2026-10-21 title recording: the darkest non-fade sample was about 30, a black frame is under 4.
MIN_MEAN_LUMA = 8.0
# The share below which an off-palette frame is not the game drawn wrongly but not the game at all (card
# t_5d1a6ec4). The game resolves every colour it draws through data/palette_ppu.json (card RUNTIME-PALETTE), so
# a misdrawn colour costs the pixels it covers and the rest of the screen stays on the palette. Measured on
# 2026-10-26 over the seven sampled frames of the five takes on disk: the 33 frames of the game scored 0.9285
# to 0.9939, and the two frames a window covered (demo-box t=36.8 and t=48.5) scored 0.0024 and 0.0025. Half
# sits far from both populations, and it means what it says: if fewer than half the pixels are 2C02 colours,
# the screen is not the game's picture. Under this floor the report says "not the game", above it and under
# palette_share_min it stays the art lane's finding.
OFF_PALETTE_ART_MIN = 0.50
# The pollution watch that runs while the recording does (card t_5d1a6ec4). It asks Windows who owns the
# rectangle once a second, which is the attribution a finished file cannot give, and it keeps a downsampled
# signature of the pixels so a whole-screen jump is noticed even when the owner sample misses the cover.
# The jump threshold is measured on real frames: the game's own scene change (title frame to the black-backed
# room) read 0.896 and a window arriving over the game read 0.968, so a jump alone is never proof of a cover
# and never fails a take by itself. The owner sample is what marks a take polluted.
POLLUTION_POLL_S = 1.0
SIGNATURE_CELLS = (48, 45)
SIGNATURE_LEVEL = 24
SIGNATURE_JUMP = 0.80
# Two consecutive owner samples before the recording is stopped, so one poll during a focus handover does not
# kill an otherwise clean take.
POLLUTION_STOP_POLLS = 2
# How close a covering sample has to be to a sampled frame for the report to name that frame's owner. The
# watch polls once a second, so this is one poll either side of the frame's own timestamp.
POLLUTION_SAMPLE_WINDOW_S = 1.5
# A press this close to the previous one can land inside one game step, where the game reads it as the same
# press (the reason capture_title.py spaces its keys). The runner refuses a script that asks for less.
MIN_KEY_GAP_STEPS = 6
# Card DEMO-AUDIO-CAPTURE (2026-10-27): what the audio in a take is, in one field, and the two honest answers.
# A take that carries neither is a failure, so the old stand-in (one theme looped over the film) has no name here
# at all and no code path to reach it.
AUDIO_SOURCE_GAME = "game"
AUDIO_SOURCE_RECONSTRUCTED = "reconstructed"
AUDIO_SOURCE_NONE = "none"
AUDIO_SOURCES = (AUDIO_SOURCE_GAME, AUDIO_SOURCE_RECONSTRUCTED)
# The gains, crossfade and step length the game itself plays at, so a rebuilt track is at the game's levels and
# not at a mixer's idea of them (game/scripts/pp_audio/pp_audio.gml:42 to :51).
GAME_GAIN_MUSIC = 0.7
GAME_GAIN_SFX = 0.9
GAME_GAIN_BLIP_FACTOR = 0.5
GAME_FADE_STEPS = 30
GAME_STEP_MS = 16.6667
# A loopback device is sold under these names. The first four are the ones capture_title.pick_loopback_device
# already knows; the rest are the other names the same hardware and the OBS family install under.
LOOPBACK_HINTS = ("stereo mix", "cable output", "virtual-audio-capturer", "loopback", "voicemeeter", "vb-audio",
                  "what u hear", "wave out mix", "obs virtual", "screen-capture-recorder")
# The one install that turns this host's silence into a capture, printed when no loopback device is present.
LOOPBACK_INSTALL = ("audio install: install VB-Audio Virtual Cable (vb-audio.com/Cable) and set the game's output "
                    "to CABLE Input, so ffmpeg can record CABLE Output with the video; OBS Studio's Audio Output "
                    "Capture with the virtual audio device is the other way to the same device")
# The game writes one "PP audio:" line per cue it asks for, plays or leaves silent
# (game/scripts/pp_audio/pp_audio.gml), so the log is the account of what it played and when.
AUDIO_LOG_NEEDLE = "PP audio:"
# The PP_AUDIO_LOG debug door writes one of these a second; they are state, never a cue, so no rebuild counts them.
AUDIO_STATUS_NEEDLE = "PP audio status:"
AUDIO_LOG_POLL_S = 0.05
# A rebuilt track whose mean level is at or under this is silence, not audio: nothing on this card may pass a
# silent track off as the game's sound.
SILENT_TRACK_DB = -70.0
MUSIC_STREAM_RE = re.compile(r"^PP audio: title_theme streaming (\S+), instance")
MUSIC_CUE_RE = re.compile(r"^PP audio: music cue (\S+) streaming (\S+), instance")
MUSIC_MISSING_RE = re.compile(r"^PP audio: music cue (\S+) has no OGG yet")
MUSIC_STOP_RE = re.compile(r"^PP audio: (?:music|title_theme) stopping over")
SFX_PLAYED_RE = re.compile(r"^PP audio: ([a-z0-9_]+) played, instance")
DUCK_RE = re.compile(r"^PP audio: title_theme ducked (-?[\d.]+) dB")
UNDUCK_RE = re.compile(r"^PP audio: title_theme back to full after")
# The game pauses the music and stops every effect when the window loses focus, and resumes the music where it
# stopped when focus comes back (game/scripts/pp_audio/pp_audio.gml:415 to :434, the two lines pp_audio_focus
# writes). A rebuild that ignored these two lines would play music across a pause the game's own log records.
FOCUS_LOST_RE = re.compile(r"^PP audio: focus lost, music paused")
FOCUS_BACK_RE = re.compile(r"^PP audio: focus back, music resumed")
# Which reading of the pause line this rebuild uses, carried in the record. The line says "every effect stopped"
# and the same log can carry effect plays after it, so the reading is stated rather than chosen in silence:
# the pause stops what was ALREADY ringing at that instant (pp_audio_focus loops the live sfx instances and
# stops them), and an effect line the log prints afterwards is kept, because the game prints a play line when
# it starts a sound and a stopped sound cannot print one.
FOCUS_EFFECTS_READING = ("focus lost stops the effects that were already ringing at that instant, which the "
                         "reconstruction cuts there, and an effect the log records as played after the pause is "
                         "kept: the game prints a play line when it starts a sound, so that sound did play")
SFX_MANIFEST = os.path.join(ROOT, "game", "datafiles", "sfx", "sfx.json")
# Where the cue files the game names in its log actually live on this checkout: the build mirrors the delivered
# OGGs into game/datafiles/streams, and assets/audio holds the delivered originals.
STREAM_DIRS = (os.path.join(ROOT, "game", "datafiles", "streams"), os.path.join(ROOT, "assets", "audio"))

# The binary is found once, on first use, because finding it goes through capture_title (card PINE-HONEST). A host
# that reaches this line without the Windows path gets PlatformUnavailable from capture_module, not a traceback here.
FFMPEG = None


def ffmpeg_path():
    """The ffmpeg binary, found once. Empty string means it was looked for and is not there, which is a finding."""
    global FFMPEG
    if FFMPEG is None:
        FFMPEG = capture_module().find_ffmpeg()
    return FFMPEG


# ---------------------------------------------------------------------------------------------------------------------
# The script

def load_script(path):
    """Read and validate a demo script. A malformed script stops the run before the game is launched."""
    with open(path, "r", encoding="utf-8") as handle:
        script = json.load(handle)
    problems = validate_script(script)
    if problems:
        raise SystemExit("%s is not a valid demo script:\n  %s" % (path, "\n  ".join(problems)))
    return script


def validate_script(script):
    """Every rule a demo script has to satisfy, as a list of problems. Empty means the script is playable.

    The rules exist because each one is a way a recording has silently been wrong before: a key that is not
    a key the game reads, a step that goes backwards so the clock cannot be followed, a marker with no
    a fallback so a block buffered log hangs the run, a key gap the game cannot see, or a recording shorter
    than the submission needs.
    """
    cap = capture_module()  # the key table lives in capture_title, so the import is here and not at the top
    problems = []
    if not isinstance(script, dict):
        return ["the script is not a JSON object"]
    if script.get("version") != 1:
        problems.append("version must be 1, not %r" % (script.get("version"),))
    if not isinstance(script.get("name"), str) or not script.get("name"):
        problems.append("name must be a non empty string")

    clock = script.get("clock") or {}
    fps = clock.get("fps")
    if not isinstance(fps, int) or not 1 <= fps <= 240:
        problems.append("clock.fps must be an integer between 1 and 240, not %r" % (fps,))
        fps = 60
    max_steps = clock.get("max_steps")
    if not isinstance(max_steps, int) or max_steps <= 0:
        problems.append("clock.max_steps must be a positive integer, not %r" % (max_steps,))

    seeds = script.get("seeds") or {}
    if not isinstance(seeds, dict) or not seeds:
        problems.append("seeds must be a non empty object: a run with no pinned seed is not reproducible")
    else:
        for key, value in seeds.items():
            if key == "note":
                continue
            if not isinstance(value, int):
                problems.append("seeds.%s must be an integer, not %r" % (key, value))

    record = script.get("record") or {}
    if not isinstance(record, dict):
        problems.append("record must be an object")
        record = {}
    if not isinstance(record.get("min_seconds"), (int, float)) or record.get("min_seconds", 0) < 30:
        problems.append("record.min_seconds must be at least 30: the submission asks for 30 s of gameplay")
    if record.get("scale") != 3:
        problems.append("record.scale must be 3: the frame is 3x the 256x240 screen")
    if not isinstance(record.get("out"), str) or not record.get("out"):
        problems.append("record.out must be a path relative to the repository root")

    game = script.get("game") or {}
    for field in ("exe", "window_title"):
        if not isinstance(game.get(field), str) or not game.get(field):
            problems.append("game.%s must be a non empty string" % field)

    events = script.get("events")
    if not isinstance(events, list) or not events:
        problems.append("events must be a non empty list")
        return problems
    last_absolute = -1
    last_key_step = None
    busy_until = -1
    seen_ids = set()
    for index, event in enumerate(events):
        where = "events[%d]" % index
        if not isinstance(event, dict):
            problems.append("%s is not an object" % where)
            continue
        identifier = event.get("id")
        if not isinstance(identifier, str) or not identifier:
            problems.append("%s has no id" % where)
        elif identifier in seen_ids:
            problems.append("%s repeats the id %r" % (where, identifier))
        else:
            seen_ids.add(identifier)
        kind = event.get("kind")
        if kind not in ("key", "hold", "note"):
            problems.append("%s.kind must be key, hold or note, not %r" % (where, kind))
        if not isinstance(event.get("beat"), int):
            problems.append("%s.beat must be an integer beat number from the beat sheet" % where)
        if not isinstance(event.get("note"), str) or not event.get("note"):
            problems.append("%s.note is empty: every event says what it is for" % where)
        step = event.get("step")
        if not isinstance(step, int) or step < 0:
            problems.append("%s.step must be a non negative integer, not %r" % (where, step))
            step = None
        if event.get("marker") is not None:
            if step is None:
                # A marker without a step is a run that hangs when the log is block buffered, which it is
                # when the game's stdout is a file.
                problems.append("%s has a marker but no fallback step" % where)
            if not isinstance(event.get("marker"), str) or not event.get("marker"):
                problems.append("%s.marker must be a non empty string" % where)
            if not isinstance(event.get("marker_wait_s", 0), (int, float)) or event.get("marker_wait_s", 0) < 0:
                problems.append("%s.marker_wait_s must be a non negative number" % where)
            if not isinstance(event.get("marker_delay_steps", 0), int):
                problems.append("%s.marker_delay_steps must be an integer" % where)
        if step is not None:
            if step < last_absolute:
                problems.append("%s.step %d is before the previous event's step %d, so the clock goes backwards"
                                % (where, step, last_absolute))
            if step < busy_until:
                problems.append("%s.step %d lands inside the hold that runs until step %d, so it would fire while the "
                                "key is still down" % (where, step, busy_until))
            last_absolute = max(last_absolute, step)
        if kind == "key":
            key_name = event.get("key")
            if key_name not in cap.KEY_CODES:
                problems.append("%s.key %r is not one of %s"
                                % (where, key_name, ", ".join(sorted(cap.KEY_CODES))))
            elif step is not None:
                if last_key_step is not None and step - last_key_step < MIN_KEY_GAP_STEPS:
                    problems.append("%s.key at step %d is %d steps after the previous key, under the %d step gap "
                                    "the game needs to read two presses"
                                    % (where, step, step - last_key_step, MIN_KEY_GAP_STEPS))
                last_key_step = step
        if kind == "hold":
            # Card PP-FREE-MOVE: a held direction is what walks now, so a walk beat is a key that goes down, stays down
            # for `steps` and comes back up. The release is the moment the next press has to clear, which is why the
            # gap is measured from the END of the hold and not its start.
            key_name = event.get("key")
            if key_name not in cap.KEY_CODES:
                problems.append("%s.key %r is not one of %s"
                                % (where, key_name, ", ".join(sorted(cap.KEY_CODES))))
            hold_steps = event.get("steps")
            if not isinstance(hold_steps, int) or hold_steps <= 0:
                problems.append("%s.steps must be a positive integer, not %r" % (where, hold_steps))
            elif step is not None:
                if last_key_step is not None and step - last_key_step < MIN_KEY_GAP_STEPS:
                    problems.append("%s.hold at step %d starts %d steps after the previous key, under the %d step gap "
                                    "the game needs to read the release"
                                    % (where, step, step - last_key_step, MIN_KEY_GAP_STEPS))
                last_key_step = step + hold_steps
                busy_until = max(busy_until, step + hold_steps)
    return problems


def timeline(script):
    """The events with the second each one is due at, for --dry-run and for the report."""
    fps = script["clock"]["fps"]
    rows = []
    for event in script["events"]:
        rows.append({
            "id": event["id"],
            "beat": event["beat"],
            "kind": event["kind"],
            "key": event.get("key"),
            "steps": event.get("steps"),
            "second": round(event["step"] / float(fps), 3),
            "marker": event.get("marker"),
            "note": event["note"],
        })
    return rows


def planned_seconds(script):
    """How long the recording is meant to be: the end step, kept inside the clock's own limit."""
    fps = script["clock"]["fps"]
    end_step = (script.get("checks") or {}).get("end_step")
    if not isinstance(end_step, int):
        end_step = max(event["step"] for event in script["events"])
    end_step = min(end_step, script["clock"]["max_steps"])
    return end_step / float(fps)


# ---------------------------------------------------------------------------------------------------------------------
# The shot table as data (card t_fb7e8271)
#
# Why a table beside the script: the script says which keys go down and when. It cannot say that those keys are the six
# shots of knowledge/DEMO-SCRIPT.md, that the whole thing is 180.00 s, or that each shot has a line the game writes when
# it is on screen. That knowledge lived in a document and in a person's head, and a take that quietly lost S5 looked
# exactly like a take that had it. data/demo/shot_table.json is that knowledge as a file the recorder reads: a shot's
# seconds, its start and end step, and the BEAT_CUES name of the line the game's own log has to carry for it.

def load_shot_table(name, path=SHOT_TABLE):
    """The shot table called `name`, as a copy. Raises SystemExit naming the tables this checkout carries."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as error:
        raise SystemExit("the shot table %s could not be read: %s" % (path, error))
    except ValueError as error:
        raise SystemExit("the shot table %s is not JSON: %s" % (path, error))
    tables = data.get("tables") or {}
    if not isinstance(tables, dict) or not tables:
        raise SystemExit("%s carries no tables" % path)
    if name not in tables:
        raise SystemExit("%s carries no shot table %r: it carries %s"
                         % (path, name, ", ".join(sorted(tables)) or "none"))
    table = json.loads(json.dumps(tables[name]))  # a copy, so a caller cannot edit the file's own row in memory
    table.setdefault("name", name)
    if data.get("version") != 1:
        raise SystemExit("%s must be version 1, not %r" % (path, data.get("version")))
    return table


def shot_table_names(path=SHOT_TABLE):
    """The names this checkout's shot table file carries, for a help line or an error."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):  # gate: ok an unreadable table file has no names, and the error that names the path comes from load_shot_table.
        return []
    return sorted((data.get("tables") or {}).keys())


def shot_table_seconds(table):
    """The plan's own total: the sum of the shot rows' seconds, rounded to a millisecond."""
    return round(sum(float(shot.get("seconds") or 0.0) for shot in table.get("shots") or []), 3)


def shot_table_markers(table):
    """Every log line the table requires, from the shot rows and their sub-shots, in the order they are reached."""
    names = []
    for shot in table.get("shots") or []:
        for row in [shot] + list(shot.get("sub_shots") or []):
            for name in row.get("markers") or []:
                if name not in names:
                    names.append(name)
    return names


def narration_fields(value, where=""):
    """Every place in a table that carries a narrator, narration or voice over field, as 'where.key' strings."""
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in NARRATION_KEYS:
                found.append("%s.%s" % (where or "table", key))
            found += narration_fields(item, "%s.%s" % (where or "table", key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found += narration_fields(item, "%s[%d]" % (where or "table", index))
    return found


def validate_shot_table(table):
    """Every rule a shot table has to satisfy, as a list of problems. Empty means the table can be played.

    The rules are the ways a shot table has been wrong before: a plan that does not add up to the 180 s the card asks
    for, a row whose start does not meet the row above it so a second belongs to no shot or to two, a sub-shot whose
    seconds do not fill its parent, a marker that is not a row of BEAT_CUES so no log line could ever satisfy it, and a
    narrator field, which this take never carries.
    """
    problems = []
    if not isinstance(table, dict):
        return ["the table is not a JSON object"]
    fps = table.get("fps")
    if not isinstance(fps, int) or not 1 <= fps <= 240:
        problems.append("fps must be an integer between 1 and 240, not %r" % (fps,))
        fps = 60
    total = table.get("total_seconds")
    if not isinstance(total, (int, float)) or total <= 0:
        problems.append("total_seconds must be a positive number, not %r" % (total,))
        total = None
    tolerance = table.get("tolerance_seconds")
    if not isinstance(tolerance, (int, float)) or tolerance < 0:
        problems.append("tolerance_seconds must be zero or more, not %r" % (tolerance,))
        tolerance = None
    band = table.get("take_band_seconds")
    if not isinstance(band, list) or len(band) != 2 or not all(isinstance(v, (int, float)) for v in band):
        problems.append("take_band_seconds must be two numbers, the low and the high of the band a take may run in")
    elif band[0] >= band[1]:
        problems.append("take_band_seconds is %r, and its low is not under its high" % (band,))
    elif isinstance(total, (int, float)) and not band[0] <= total <= band[1]:
        problems.append("total_seconds %.2f is outside the take's own band %r" % (total, band))
    for where in narration_fields(table):
        problems.append("%s is a narrator field, and this take carries no narration: the captions belong to the edit, "
                        "not to the recorder" % where)

    shots = table.get("shots")
    if not isinstance(shots, list) or not shots:
        problems.append("shots must be a non empty list")
        return problems
    seen_ids = set()
    seen_markers = {}
    previous_end = None
    for index, shot in enumerate(shots):
        where = "shots[%d]" % index
        if not isinstance(shot, dict):
            problems.append("%s is not an object" % where)
            continue
        identifier = shot.get("id")
        if not isinstance(identifier, str) or not identifier:
            problems.append("%s has no id" % where)
        elif identifier in seen_ids:
            problems.append("%s repeats the id %r" % (where, identifier))
        else:
            seen_ids.add(identifier)
            where = "shots[%s]" % identifier
        seconds = shot.get("seconds")
        start, end = shot.get("start_step"), shot.get("end_step")
        if not isinstance(seconds, (int, float)) or seconds <= 0:
            problems.append("%s.seconds must be a positive number, not %r" % (where, seconds))
        if not isinstance(start, int) or start < 0:
            problems.append("%s.start_step must be a non negative integer, not %r" % (where, start))
            start = None
        if not isinstance(end, int) or end <= 0:
            problems.append("%s.end_step must be a positive integer, not %r" % (where, end))
            end = None
        if start is not None and previous_end is None and index == 0 and start != 0:
            problems.append("%s.start_step is %d and the first shot starts the take at step 0" % (where, start))
        if start is not None and previous_end is not None and start != previous_end:
            problems.append("%s.start_step is %d and the shot above it ends at %d, so the plan has a gap or an overlap"
                            % (where, start, previous_end))
        if start is not None and end is not None:
            if end <= start:
                problems.append("%s ends at step %d, not after its start %d" % (where, end, start))
            elif isinstance(seconds, (int, float)) and abs(seconds - (end - start) / float(fps)) > 0.02:
                problems.append("%s says %.3f s and its steps %d to %d are %.3f s at %d fps"
                                % (where, seconds, start, end, (end - start) / float(fps), fps))
            previous_end = end
        markers = shot.get("markers")
        own_markers = set()
        if not isinstance(markers, list) or not markers or not all(isinstance(name, str) and name for name in markers):
            problems.append("%s.markers must be a non empty list of shot table names, not %r" % (where, markers))
            markers = []
        else:
            own_markers = set(markers)
            for name in markers:
                if name in seen_markers and seen_markers[name] != identifier:
                    problems.append("%s repeats the log line %r, which shots[%s] already names"
                                    % (where, name, seen_markers[name]))
                else:
                    seen_markers[name] = identifier
                if name not in dict(BEAT_CUES):
                    problems.append("%s names %r and no row of play_demo.BEAT_CUES carries it, so no log line could "
                                    "ever satisfy this shot" % (where, name))
        sub_previous_end = None
        sub_seconds = 0.0
        sub_markers = set()
        for sub_index, sub in enumerate(shot.get("sub_shots") or []):
            sub_where = "%s.sub_shots[%d]" % (where, sub_index)
            if not isinstance(sub, dict):
                problems.append("%s is not an object" % sub_where)
                continue
            sub_start, sub_end = sub.get("start_step"), sub.get("end_step")
            sub_len = sub.get("seconds")
            if not isinstance(sub_len, (int, float)) or sub_len <= 0:
                problems.append("%s.seconds must be a positive number, not %r" % (sub_where, sub_len))
            else:
                sub_seconds += float(sub_len)
            sub_names = sub.get("markers")
            if not isinstance(sub_names, list) or not sub_names:
                problems.append("%s.markers must be a non empty list, not %r" % (sub_where, sub_names))
            else:
                # A sub-shot names the lines it is the one to produce, so its names are also its shot's names: the two
                # lists have to be the same set, and a name may not appear in two sub-shots or in two shots.
                for name in sub_names:
                    if name in sub_markers:
                        problems.append("%s repeats the log line %r, which another sub-shot of %s names"
                                        % (sub_where, name, where))
                    sub_markers.add(name)
                    if name not in own_markers:
                        problems.append("%s names %r and its shot's own markers do not carry it"
                                        % (sub_where, name))
                    if seen_markers.get(name) != identifier:
                        problems.append("%s names %r, which another shot already names" % (sub_where, name))
            if not isinstance(sub_start, int) or not isinstance(sub_end, int) or sub_end <= sub_start:
                problems.append("%s needs integer start_step and end_step with the end after the start" % sub_where)
                continue
            if sub_previous_end is None:
                if start is not None and sub_start != start:
                    problems.append("%s starts at %d and its shot starts at %d" % (sub_where, sub_start, start))
            elif sub_start != sub_previous_end:
                problems.append("%s starts at %d and the sub-shot above it ends at %d"
                                % (sub_where, sub_start, sub_previous_end))
            if end is not None and sub_end > end:
                problems.append("%s ends at %d, past its shot's end %d" % (sub_where, sub_end, end))
            sub_previous_end = sub_end
            if isinstance(sub_len, (int, float)) and abs(sub_len - (sub_end - sub_start) / float(fps)) > 0.02:
                problems.append("%s says %.3f s and its steps %d to %d are %.3f s at %d fps"
                                % (sub_where, sub_len, sub_start, sub_end,
                                   (sub_end - sub_start) / float(fps), fps))
        if sub_markers and sub_markers != own_markers:
            problems.append("%s's markers are %r and its sub-shots name %r: the two lists are one set"
                            % (where, sorted(own_markers), sorted(sub_markers)))
        if sub_previous_end is not None:
            if end is not None and sub_previous_end != end:
                problems.append("%s's sub-shots end at %d and the shot ends at %d, so a second of it belongs to no "
                                "sub-shot" % (where, sub_previous_end, end))
            if isinstance(seconds, (int, float)) and abs(sub_seconds - seconds) > 0.02:
                problems.append("%s's sub-shots sum to %.3f s and the shot is %.3f s"
                                % (where, sub_seconds, seconds))

    if previous_end is not None:
        end_step = table.get("end_step")
        if not isinstance(end_step, int) or end_step <= 0:
            problems.append("end_step must be a positive integer, not %r" % (end_step,))
        elif previous_end != end_step:
            problems.append("the shots end at step %d and the table's end_step is %d" % (previous_end, end_step))
        if isinstance(total, (int, float)) and isinstance(fps, int) and fps > 0:
            if abs(previous_end / float(fps) - total) > 0.02:
                problems.append("the shots end at %.3f s and the table's total_seconds is %.3f" %
                                (previous_end / float(fps), total))
    if isinstance(total, (int, float)) and tolerance is not None:
        plan = shot_table_seconds(table)
        if abs(plan - total) > tolerance:
            problems.append("the shots sum to %.3f s and the table says %.3f s, which is outside its own %.2f s "
                            "tolerance" % (plan, total, tolerance))

    required = table.get("required_beats")
    if not isinstance(required, list) or not required:
        problems.append("required_beats must be a non empty list of the log lines this table's take has to produce")
    else:
        missing = [name for name in shot_table_markers(table) if name not in required]
        extra = [name for name in required if name not in shot_table_markers(table)]
        if missing:
            problems.append("required_beats does not carry %r, which a shot row names" % (missing,))
        if extra:
            problems.append("required_beats carries %r, which no shot row names" % (extra,))
    return problems


def apply_shot_table(script, table):
    """The script with the table's own beats and end step, so play and check read one plan.

    The table is the plan the card asks for: its required log lines are the run's required beats and its end step is the
    run's end step. A script that disagrees is refused by validate_shot_table_script rather than half applied.
    """
    merged = json.loads(json.dumps(script))
    checks = merged.setdefault("checks", {})
    checks["required_beats"] = list(table.get("required_beats") or [])
    if isinstance(table.get("end_step"), int):
        checks["end_step"] = int(table["end_step"])
    merged["shot_table"] = {"name": table.get("name"), "script": table.get("script"),
                            "total_seconds": table.get("total_seconds"),
                            "tolerance_seconds": table.get("tolerance_seconds")}
    return merged


def validate_shot_table_script(table, script):
    """The rules that bind a table to the script it plays, as a list of problems."""
    problems = []
    planned = planned_seconds(script)
    total = table.get("total_seconds")
    tolerance = table.get("tolerance_seconds")
    if isinstance(total, (int, float)) and isinstance(tolerance, (int, float)):
        if abs(planned - total) > tolerance:
            problems.append("the script plans %.3f s and the shot table is %.3f s plus or minus %.2f s"
                            % (planned, total, tolerance))
    claimed = (script.get("checks") or {}).get("required_beats") or []
    table_beats = table.get("required_beats") or []
    dropped = [name for name in table_beats if name not in claimed]
    if dropped:
        problems.append("the shot table requires %r and the script's checks.required_beats does not carry them"
                        % (dropped,))
    return problems


def shot_table_rows(table, beats=None):
    """The table as rows for a report: the id, the second it starts, its length, and whether its line was written."""
    beats = beats or {}
    rows = []
    for shot in table.get("shots") or []:
        for row in [shot] + list(shot.get("sub_shots") or []):
            markers = row.get("markers") or []
            named = [name for name in markers if (beats.get(name) or {}).get("found")]
            rows.append({"id": row.get("id"), "start_step": row.get("start_step"), "end_step": row.get("end_step"),
                         "seconds": row.get("seconds"), "markers": markers, "named": named,
                         "found": bool(markers) and len(named) == len(markers),
                         "sub_shot": row is not shot})
    return rows


def print_shot_table(table, beats=None):
    """The table as one block of lines, for the run log and for --dry-run: the shot, its second, its length, its line."""
    rows = shot_table_rows(table, beats)
    band = table.get("take_band_seconds") or [table.get("total_seconds"), table.get("total_seconds")]
    print("shot table %r: %d rows, %.2f s (tolerance %.2f s, take band %.1f to %.1f s), script %s"
          % (table.get("name"), len(rows), shot_table_seconds(table), float(table.get("tolerance_seconds") or 0.0),
             float(band[0]), float(band[1]), table.get("script")))
    fps = float(table.get("fps") or 60)
    for row in rows:
        marks = ", ".join(row["markers"])
        state = ""
        if beats:
            state = " [%s]" % ("named" if row["found"] else "NEVER NAMED")
        print("  %-5s %7.2f s  %6.2f s from step %5d  %s%s"
              % (row["id"], (row["start_step"] or 0) / fps, float(row["seconds"] or 0.0), row["start_step"] or 0,
                 marks, state))


def shot_table_report(table, duration_s=None, beat_rows=None):
    """What the shot table says and what the game's log said about it, as one dict for the verify file."""
    rows = shot_table_rows(table, beat_rows)
    return {"name": table.get("name"), "script": table.get("script"),
            "total_seconds": table.get("total_seconds"), "tolerance_seconds": table.get("tolerance_seconds"),
            "sum_seconds": shot_table_seconds(table),
            "take_band_seconds": table.get("take_band_seconds"),
            "duration_s": None if duration_s is None else round(float(duration_s), 3),
            "narration": bool(narration_fields(table)), "shots": rows,
            "missing": [row["markers"] for row in rows if row["markers"] and not row["found"]]}


def shot_table_check(table, duration_s, beat_rows, gated=False):
    """The shot table's verdict on a finished take, as (ok, line).

    Two questions, and both are the card's: the plan adds up to 180 seconds inside the table's own tolerance, and the
    take runs inside the table's take band (170 to 190 s, the card's band); then every shot's log line was written by
    the game, so a take that lost S5 or the game over is failed by the shot's own name and not by a paragraph.
    """
    total = float(table.get("total_seconds") or 0.0)
    tolerance = float(table.get("tolerance_seconds") or 0.0)
    band = table.get("take_band_seconds")
    if not isinstance(band, list) or len(band) != 2:
        band = [total, total]
    low, high = float(band[0]), float(band[1])
    measured = None if duration_s is None else float(duration_s)
    plan = shot_table_seconds(table)
    rows = shot_table_rows(table, beat_rows)
    missing = []
    for row in rows:
        for name in row["markers"]:
            if name not in row["named"] and name not in missing:
                missing.append(name)
    problems = []
    notes = []
    if abs(plan - total) > tolerance:
        problems.append("the shots sum to %.3f s and the table is %.3f s, outside its %.2f s tolerance"
                        % (plan, total, tolerance))
    if measured is None:
        problems.append("the take's duration could not be read, so its place in the %.1f to %.1f s band is unknown"
                        % (low, high))
    elif not low <= measured <= high and gated:
        # A run whose events wait for the game (marker_wait_s) is as long as the game is slow: the band is reported,
        # it does not fail the take.
        notes.append("%.3f s of video is outside the %.1f to %.1f s band; this run waited for the game, so the band "
                     "is reported and not enforced" % (measured, low, high))
    elif not low <= measured <= high:
        problems.append("%.3f s of video is outside the %.1f to %.1f s band the shot table names"
                        % (measured, low, high))
    if missing:
        problems.append("the game's log never named %d of its lines: %s" % (len(missing), ", ".join(missing)))
    if problems:
        return False, ("FAIL the shot table %r is not met: %s"
                       % (table.get("name"), "; ".join(problems)))
    named = sum(len(row["named"]) for row in rows)
    if notes:
        return True, "PASS the shot table %r with a note: %s" % (table.get("name"), "; ".join(notes))
    return True, ("PASS the shot table %r: its %d rows sum to %.2f s inside the %.2f s tolerance and the take runs "
                  "%.2f s, inside the %.1f to %.1f s band; the game's own log named all %d of its lines"
                  % (table.get("name"), len(rows), plan, tolerance, measured or 0.0, low, high, named))


# ---------------------------------------------------------------------------------------------------------------------
# The replay

def read_marker(log_path, needle, need=1):
    """True when the game's own log already carries a line `need` times (a line two events share, such as the fight
    result of two fights, is only the second event's once it appears twice). Absent file means 'not yet'."""
    if not os.path.isfile(log_path):
        return False
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read().count(needle) >= need
    except OSError:  # gate: ok the game may hold the log open for writing on this platform; a marker that cannot be read is treated as absent and the step fallback takes over.
        return False


class Replay(object):
    """Walks the script on one clock, from the moment the recorder starts.

    The clock is steps at the script's fps counted from the recorder's start, so a step in this file is the
    same unit as a step in the game log, and a slow key press never shifts everything after it. A marker is
    an accelerator only: it can move an event earlier, and the event's own step is the fallback, so a block
    buffered log costs time rather than hanging the run.
    """

    def __init__(self, script, hwnd, log_path, send_key):
        self.script = script
        self.hwnd = hwnd
        self.log_path = log_path
        self.send_key = send_key
        self.fps = script["clock"]["fps"]
        self.started = None
        self.trace = []
        # Card ROUTE-STALL: steps the game ran behind the tape at a marker_wait_s event. Every later event moves by it.
        self.shift = 0
        # An event whose marker an earlier event already names needs one more occurrence in the log than that many.
        self.ordinal = {}
        seen = {}
        for event in script.get("events") or []:
            marker = event.get("marker")
            if marker:
                self.ordinal[event["id"]] = seen.get(marker, 0) + 1
                seen[marker] = seen.get(marker, 0) + 1

    def step_now(self):
        return int((time.monotonic() - self.started) * self.fps) - self.shift

    def record(self, event_id, kind, detail, step):
        # The rows carry the VIDEO clock (tape step plus the hold shift), the clock the recording and the game log run
        # on; the tape's own step stays beside it.
        video = step + self.shift
        row = {"id": event_id, "kind": kind, "detail": detail, "at_step": video, "tape_step": step,
               "at_second": round(video / float(self.fps), 3)}
        self.trace.append(row)
        print("  %-5s %-6s %-28s at %.1f s (step %d)" % (event_id, kind, detail[:28], video / float(self.fps), video))
        return row

    def wait_until(self, target_step, max_wait_s=60.0):
        """Sleep until the clock reaches target_step. Returns the step it actually reached."""
        deadline = time.monotonic() + max_wait_s
        while True:
            now = self.step_now()
            if now >= target_step:
                return now
            if time.monotonic() > deadline:
                raise SystemExit("the clock stopped advancing at step %d, %d steps short of %d"
                                 % (now, target_step - now, target_step))
            time.sleep(min(0.02, max(0.001, (target_step - now) / float(self.fps))))

    def wait_marker(self, needle, fallback_step, delay_steps, timeout_s, need=1):
        """Wait for a log line, then delay, but never past the event's own fallback step.

        Returns (step, seen). The marker only moves the event earlier than its fallback: if it has not
        appeared by the fallback step, the fallback is what the run uses and the verify file says so.
        """
        while self.step_now() < fallback_step:
            if read_marker(self.log_path, needle, need):
                return min(self.step_now() + delay_steps, fallback_step), True
            time.sleep(0.1)
        seen = read_marker(self.log_path, needle, need)
        return fallback_step, seen

    def wait_marker_hold(self, needle, fallback_step, delay_steps, wait_s, need=1):
        """Like wait_marker, but a game that is LATE holds the tape instead of being left behind.

        Seen before the fallback: the event moves earlier, as always. Not seen by the fallback: the tape waits up to
        wait_s more seconds for the line, then fires delay_steps after it and shifts the rest of the clock by the
        lateness, so a typed word or a menu press never lands before the box that reads it exists. Never seen: the
        fallback step is used and the caller says so. Returns (step, seen).
        """
        limit = fallback_step + int(wait_s * self.fps)
        while True:
            now = self.step_now()
            if read_marker(self.log_path, needle, need):
                target = now + delay_steps
                if target > fallback_step:
                    self.shift += target - fallback_step
                    return fallback_step, True
                return target, True
            if now >= limit:
                # Never seen: the tape still waited, so the keys after it keep their spacing instead of bursting.
                self.shift += max(0, now - fallback_step)
                return fallback_step, False
            time.sleep(0.1)

    def run(self, end_step, should_stop=None):
        cap = capture_module()  # the key codes, imported here so this class can exist on any host
        self.started = time.monotonic()
        failures = []
        stopped = False
        for event in self.script["events"]:
            if event["step"] > end_step:
                break
            if should_stop is not None and should_stop():
                # Card t_5d1a6ec4: a window is over the rectangle, so the rest of this take is not the game.
                # Stop rather than finish, and let the verdict say why.
                self.record("pollution-stop", "stop", "a window covered the game, stopping", self.step_now())
                stopped = True
                break
            if event.get("marker") and event.get("marker_wait_s"):
                target, seen = self.wait_marker_hold(event["marker"], event["step"],
                                                     int(event.get("marker_delay_steps", 0)),
                                                     float(event["marker_wait_s"]), self.ordinal[event["id"]])
                reached = self.wait_until(target)
                detail = ("marker %r %s" % (event["marker"], "seen" if seen else "not seen, step used"))
                self.record(event["id"], "marker", detail, reached)
                if not seen:
                    failures.append("%s: the log never carried %r within %.0f s of step %d"
                                    % (event["id"], event["marker"], float(event["marker_wait_s"]), event["step"]))
            elif event.get("marker"):
                target, seen = self.wait_marker(event["marker"], event["step"],
                                                int(event.get("marker_delay_steps", 0)), 30.0,
                                                self.ordinal[event["id"]])
                reached = self.wait_until(target)
                detail = ("marker %r %s" % (event["marker"], "seen" if seen else "not seen, step used"))
                self.record(event["id"], "marker", detail, reached)
                if not seen:
                    failures.append("%s: the log never carried %r, the step %d was used instead"
                                    % (event["id"], event["marker"], event["step"]))
            else:
                reached = self.wait_until(event["step"])
                late = reached - int(event["step"])
                if late > self.fps:
                    failures.append("%s fired %.1f s late" % (event["id"], late / float(self.fps)))
            if event["kind"] == "hold":
                # Card PP-FREE-MOVE: the overworld walks while a direction is HELD, so a walk beat is a key that goes
                # down, stays down on the clock and comes back up. A press moves him a couple of pixels and no further,
                # which is why the eight taps this beat used to be are one hold now. The focus is retaken before the
                # down, because a key sent to the wrong window is a recording of a game that never moved.
                ok, why = cap.ensure_key_focus(self.hwnd, attempts=2, settle=0.15)
                if not ok:
                    failures.append("%s: the game never took the keyboard focus for the hold (%s)" % (event["id"], why))
                    break
                cap.send_vk_down(cap.KEY_CODES[event["key"]])
                self.record(event["id"], "down", event["key"], self.step_now())
                # Card t_785b61f0: the hold lasts `steps` from where the key actually went down, not from the declared
                # step. A press that landed 24 steps late used to hold for 24 steps less, and a 40 step hold of cancel
                # that arrives late became 19 steps, under the 30 a scene needs to read it as a skip.
                end = self.step_now() + int(event["steps"])
                reached = self.wait_until(end)
                cap.send_vk_up(cap.KEY_CODES[event["key"]])
                self.record(event["id"], "up", event["key"], self.step_now())
                late = reached - end
                if late > self.fps:
                    failures.append("%s held the key until %.1f s late" % (event["id"], late / float(self.fps)))
            if event["kind"] == "key":
                # A press is only ever a real press: if the focus cannot be retaken the run stops, because a
                # posted key would produce a recording of a menu that never moved.
                try:
                    self.send_key(cap.KEY_CODES[event["key"]])
                except SystemExit as error:
                    failures.append("%s: %s" % (event["id"], error))
                    break
                self.record(event["id"], "key", event["key"], self.step_now())
        # The recording keeps running to the end step, so the last beat is held on screen. A run that was
        # stopped because a window covered the game does not hold anything: the rest of it is not the game.
        if not stopped:
            self.wait_until(end_step + 30)
        return failures


# ---------------------------------------------------------------------------------------------------------------------
# Recording

def pre_roll_viewport(hwnd, path):
    """Find the game's 3x viewport inside the window, on a frame taken before recording starts.

    The crop of the mp4 is this box. It is measured, not assumed: the same search
    tools/nes_composite_check.py --crop auto runs, so a window that is covered, a desktop, or a terminal has
    no such box and the recording is refused instead of writing a file that looks like a video.
    """
    cap = capture_module()
    rect = cap.get_window_rect(hwnd)
    if rect is None:
        return None, None, 0.0, "the window has no rectangle"
    ok, note = cap.capture_with_pil(rect, path)
    if not ok:
        return rect, None, 0.0, "the pre-roll capture failed: %s" % note
    box, score, why = cap.viewport_box_and_score(path)
    if box is None:
        return rect, None, score, "no legal 3x NES viewport in the pre-roll frame (%s), so it is not the game" % why
    return rect, box, score, "viewport %s at score %.3f" % (box, score)


RECORD_TAIL_S = 2.5


def record_bound_seconds(script, seconds, end_step=None):
    """The longest the recorder may run: the plan, the tail, and every second a marker_wait_s event may hold the tape.

    The recorder is stopped by hand once the replay ends, so this is only the safety stop, but it must not be shorter
    than a replay that waited for the game at every hold (a held tape runs past a bound of seconds + tail)."""
    held = 0.0
    for event in script.get("events") or []:
        if end_step is not None and event.get("step", 0) > end_step:
            continue
        if event.get("marker") and event.get("marker_wait_s"):
            held += float(event["marker_wait_s"])
    return float(seconds) + RECORD_TAIL_S + held


def stop_recorder(recorder, grace_s):
    """Let the recording run grace_s past the replay, then ask ffmpeg to finish the file with q on its stdin.
    Returns a note when the pipe was already gone, or "" when it took the q or had already exited."""
    time.sleep(grace_s)
    if recorder.poll() is not None or recorder.stdin is None:
        return ""
    try:
        recorder.stdin.write(b"q")
        recorder.stdin.flush()
        recorder.stdin.close()
    except OSError as error:
        return "the recorder stdin was gone before q (%s)" % error
    return ""


def start_recorder(rect, out_path, duration_s, fps, loopback):
    """Start ffmpeg on the window rectangle. Returns (process, log file handle, log path).

    gdigrab reads the screen, so the rectangle has to be the window's own and nothing may cover it. The
    output goes to a file and never to a pipe: a pipe nobody reads fills after about 64 KB and ffmpeg then
    blocks, which is how an earlier run of this harness stopped recording at 9 s of a 13 s file.
    """
    FFMPEG = ffmpeg_path()
    left, top, width, height = rect
    os.makedirs(BUILD_DIR, exist_ok=True)
    log_path = os.path.join(BUILD_DIR, "demo-ffmpeg.log")
    handle = open(log_path, "wb")
    arguments = [
        "-f", "gdigrab",
        "-framerate", str(fps),
        "-offset_x", str(left),
        "-offset_y", str(top),
        "-video_size", "%dx%d" % (width, height),
        "-i", "desktop",
        "-t", "%.2f" % duration_s,
        # libx264 needs even dimensions for yuv420p, and the window height is odd.
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-r", str(fps),
        "-c:v", "libx264",
        # ultrafast, because gdigrab hands the encoder a full frame 60 times a second and the slower presets
        # cannot keep up on this host: a slow encode means a file shorter than the run it was meant to hold.
        "-preset", "ultrafast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
    ]
    if loopback:
        arguments += ["-f", "dshow", "-i", "audio=%s" % loopback,
                      "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "160k"]
    arguments.append(out_path)
    process = subprocess.Popen([FFMPEG, "-hide_banner", "-y"] + arguments,
                               stdout=handle, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
    return process, handle, log_path


def dshow_devices(ffmpeg_path):
    """Every DirectShow capture device ffmpeg sees on this host, with the tool's own words about the rest.

    System audio in an ffmpeg capture on Windows needs a loopback style audio device: gdigrab reads pixels and
    has no audio input at all, so a host with no audio device records a silent picture no matter what the game
    plays. The raw lines are kept so the verify file can say what the machine actually offered.
    """
    result = subprocess.run([ffmpeg_path, "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
                            capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
    text = (result.stderr or "") + (result.stdout or "")
    devices = []
    notes = []
    raw = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "(video)" in stripped or "(audio)" in stripped:
            if '"' in stripped:
                name = stripped.split('"')[1]
                kind = "video" if "(video)" in stripped else "audio"
                devices.append((name, kind))
                raw.append(stripped[:200])
            continue
        if "Could not enumerate" in stripped or stripped.startswith("Error opening") or "dummy:" in stripped:
            notes.append(stripped[:200])
            raw.append(stripped[:200])
    return {"devices": devices, "notes": notes, "raw": raw}


def wasapi_demuxer(ffmpeg_path):
    """True when this ffmpeg build can open a WASAPI device itself.

    The Windows build installed here ships DirectShow and no WASAPI demuxer, so "no WASAPI loopback" is a fact
    about the binary and not only about the sound card: `ffmpeg -formats` lists dshow and no wasapi row, and
    `ffmpeg -h demuxer=wasapi` answers "Unknown format 'wasapi'". Measured 2026-10-27.
    """
    result = subprocess.run([ffmpeg_path, "-hide_banner", "-formats"], capture_output=True, text=True, timeout=60,
                            stdin=subprocess.DEVNULL)
    return "wasapi" in ((result.stdout or "") + (result.stderr or "")).lower()


def pick_game_audio_device(devices):
    """The audio device that carries the game's own output, or None. A microphone is never one of these."""
    for name, kind in devices:
        if kind == "audio" and any(hint in name.lower() for hint in LOOPBACK_HINTS):
            return name
    return None


def audio_device_report(ffmpeg_path):
    """This host's audio inputs in one dict: the dshow list, whether ffmpeg has WASAPI, and the device chosen."""
    found = dshow_devices(ffmpeg_path)
    chosen = pick_game_audio_device(found["devices"])
    return {"dshow": [{"name": name, "kind": kind} for name, kind in found["devices"]],
            "dshow_notes": found["notes"],
            "dshow_raw": found["raw"],
            "wasapi_demuxer": wasapi_demuxer(ffmpeg_path),
            "loopback": chosen,
            "install": None if chosen else LOOPBACK_INSTALL}


class LogAudioWatch(threading.Thread):
    """Stamp every "PP audio:" line the game writes with the second it arrived, on the recording's clock.

    The game's log carries no timestamps, so the moment a line was read is the only second it can honestly be
    placed at. Lines already in the file when the watch starts were written before the recording did (the
    title theme streams at boot, seconds before the window is found), so they are placed at 0.0 and flagged
    `before_recording` rather than guessed at.
    """

    def __init__(self, log_path, started_at, poll_s=AUDIO_LOG_POLL_S):
        threading.Thread.__init__(self, name="log-audio-watch", daemon=True)
        self.log_path = log_path
        self.started_at = started_at
        self.poll_s = poll_s
        self.rows = []
        self._stop_event = threading.Event()
        self._offset = 0
        self._tail = ""
        self._polled_once = False

    def run(self):
        while not self._stop_event.is_set():
            self.poll()
            self._stop_event.wait(self.poll_s)
        self.poll()

    def poll(self):
        """Read whatever is new in the log, split it into lines, and stamp the audio ones."""
        try:
            size = os.path.getsize(self.log_path)
        except OSError:
            return
        if size <= self._offset:
            return
        try:
            with open(self.log_path, "rb") as handle:
                handle.seek(self._offset)
                blob = handle.read(size - self._offset)
        except OSError:
            return
        self._offset += len(blob)
        text = self._tail + blob.decode("utf-8", "replace")
        lines = text.splitlines()
        if text and not text.endswith(("\n", "\r")):
            self._tail = lines.pop() if lines else text
        else:
            self._tail = ""
        for line in lines:
            if AUDIO_LOG_NEEDLE not in line or AUDIO_STATUS_NEEDLE in line:
                continue
            at = 0.0 if not self._polled_once else max(0.0, time.monotonic() - self.started_at)
            self.rows.append({"at": round(at, 3), "line": line.strip(), "before_recording": not self._polled_once})
        self._polled_once = True

    def stop(self):
        """Stop reading and return the stamped lines, whatever the run did."""
        self._stop_event.set()
        if self.is_alive():
            self.join(timeout=5)
        self.poll()
        return self.rows


def sfx_table():
    """The effect rows the build ships, id to (file, seconds), read from the manifest the game itself reads."""
    cached = getattr(sfx_table, "_rows", None)
    if cached is not None:
        return cached
    rows = {}
    try:
        with open(SFX_MANIFEST, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        for row in data.get("cues") or []:
            if not row.get("id") or not row.get("file"):
                continue
            rows[row["id"]] = (row["file"], float(row.get("seconds") or 0.0))
    except (OSError, ValueError, TypeError):
        rows = {}
    sfx_table._rows = rows
    return rows


def resolve_stream(named):
    """The cue file a log line names, found on this checkout. None when nothing of that name is here.

    The log names the file the way the game sees it (`streams/title_theme_v3_126.ogg`), which is not a path
    this repository has, so the leaf name is looked for in the two places the delivered OGGs actually live.
    """
    leaf = os.path.basename(str(named).replace("\\", "/"))
    if not leaf:
        return None
    for folder in STREAM_DIRS:
        candidate = os.path.join(folder, leaf)
        if os.path.isfile(candidate):
            return candidate
        if not os.path.isdir(folder):
            continue
        for root_dir, _dirs, files in os.walk(folder):
            if leaf in files:
                return os.path.join(root_dir, leaf)
    return None


def sfx_gain(cue_id):
    """The gain the game plays an effect at: the effect level, and half that for a text blip (pp_audio.gml)."""
    return GAME_GAIN_SFX * GAME_GAIN_BLIP_FACTOR if str(cue_id).startswith("text_blip") else GAME_GAIN_SFX


def audio_events(rows):
    """One event per audio line: what the game played, from which file, and at what gain.

    Returns (events, notes). A line this tool cannot place becomes a note and never an invented sound: the
    reconstruction reproduces the game's own sound, and where the game was silent it stays silent.

    Every row the watcher hands over ends as one of the three: an event (a placement), a `music_missing` event
    (a silent cue, because the game asked for a cue it could not start), or a note. Nothing is dropped in
    silence, so a take's own record can be read as a full account of its log (card DEMO-AUDIO-CAPTURE, review
    correction 2). The `PP audio status:` lines the PP_AUDIO_LOG door writes once a second are state, never a
    cue: they are counted and one note says so, instead of vanishing.
    """
    events = []
    notes = []
    effects = sfx_table()
    status_lines = 0
    for row in rows:
        line = str(row.get("line") or "")
        if AUDIO_STATUS_NEEDLE in line:
            status_lines += 1
            continue
        at = max(0.0, float(row.get("at") or 0.0))
        match = MUSIC_STREAM_RE.match(line)
        if match:
            path = resolve_stream(match.group(1))
            if path is None:
                notes.append("%.3f s: the log names %s and no file of that name is on this checkout"
                             % (at, match.group(1)))
                continue
            events.append({"kind": "music", "at": at, "cue": "title_theme", "file": path})
            continue
        match = MUSIC_CUE_RE.match(line)
        if match:
            path = resolve_stream(match.group(2))
            if path is None:
                notes.append("%.3f s: the log names %s for cue %s and no file of that name is on this checkout"
                             % (at, match.group(2), match.group(1)))
                continue
            events.append({"kind": "music", "at": at, "cue": match.group(1), "file": path})
            continue
        match = MUSIC_MISSING_RE.match(line)
        if match:
            events.append({"kind": "music_missing", "at": at, "cue": match.group(1)})
            continue
        if MUSIC_STOP_RE.match(line):
            events.append({"kind": "music_stop", "at": at})
            continue
        match = DUCK_RE.match(line)
        if match:
            try:
                db = float(match.group(1))
            except ValueError:
                notes.append("%.3f s: a duck line whose level could not be read: %s" % (at, line))
                continue
            events.append({"kind": "duck", "at": at, "db": db,
                           "gain": GAME_GAIN_MUSIC * 10.0 ** (-db / 20.0)})
            continue
        if UNDUCK_RE.match(line):
            events.append({"kind": "unduck", "at": at, "gain": GAME_GAIN_MUSIC})
            continue
        match = SFX_PLAYED_RE.match(line)
        if match:
            cue_id = match.group(1)
            if cue_id not in effects:
                notes.append("%.3f s: the log says %s played and the effect manifest has no row for it"
                             % (at, cue_id))
                continue
            file_name, length = effects[cue_id]
            path = os.path.join(os.path.dirname(SFX_MANIFEST), file_name)
            if not os.path.isfile(path):
                notes.append("%.3f s: the log says %s played and %s is not on this checkout" % (at, cue_id, file_name))
                continue
            events.append({"kind": "sfx", "at": at, "id": cue_id, "file": path, "seconds": length,
                           "gain": sfx_gain(cue_id)})
            continue
        if FOCUS_LOST_RE.match(line):
            events.append({"kind": "focus_lost", "at": at})
            continue
        if FOCUS_BACK_RE.match(line):
            events.append({"kind": "focus_back", "at": at})
            continue
        # A line of the family's own shape that none of the above places: it is a note, never silence with
        # no account of it. The log is the game's own account, so a shape the tool does not know is a gap in
        # the tool, and the record has to say so.
        notes.append("%.3f s: the log carries an audio line this tool has no shape for, so it placed nothing "
                     "for it: %s" % (at, line))
    if status_lines:
        notes.append("the game's own state report (mode, cue, gain, paused) is written %d time%s by the "
                     "PP_AUDIO_LOG door, once a second, and it places no sound"
                     % (status_lines, "" if status_lines == 1 else "s"))
    return events, notes


def music_gain_at(gains, moment, start):
    """The gain the game's own log puts the music at this second: the music level, or its intro duck."""
    level = GAME_GAIN_MUSIC
    for row in sorted(gains, key=lambda item: item["at"]):
        if start - 0.001 <= row["at"] <= moment:
            level = row["gain"]
    return round(level, 4)


def focus_windows(events, seconds):
    """The seconds the game's log says the music was paused: (lost, back) pairs, the last back clipped to the take.

    `pp_audio_focus` pauses the music and the theme when the window loses focus and resumes them where they
    stopped when it comes back (game/scripts/pp_audio/pp_audio.gml:415 to :434), so both lines are in the log
    of any take that lost focus. A pause with no matching resume runs to the end of the take.
    """
    windows = []
    lost = None
    for row in sorted(events, key=lambda item: item["at"]):
        if row["kind"] == "focus_lost" and lost is None:
            lost = float(row["at"])
        elif row["kind"] == "focus_back" and lost is not None:
            windows.append((lost, float(row["at"])))
            lost = None
    if lost is not None:
        windows.append((lost, float(seconds)))
    return windows


def log_audio_plan(events, seconds):
    """The track's segments: what the game played, from where, at what gain, between which seconds.

    Returns (segments, silent_cues). A music cue the game asked for and could not start is carried as a silent
    cue, so the rebuilt track is silent exactly where the game was: the reconstruction reproduces the game's
    sound, not the sound the game was supposed to make.

    The focus pause is part of the game's own sound. Where the log carries `focus lost, music paused`, the music
    stops there and carries no segment until the `focus back` second, and the piece after it starts at the
    second of the file the music had reached (`resumed where it stopped` is the log's own wording), which every
    music segment carries as its `offset`. An effect that was already ringing when the pause came is cut at the
    pause second, because `pp_audio_focus` stops the live instances; an effect the log records as played after
    the pause is kept, and `FOCUS_EFFECTS_READING` states that reading in the take's record.
    """
    fade = GAME_FADE_STEPS * GAME_STEP_MS / 1000.0
    starts = [row for row in events if row["kind"] == "music"]
    stops = [row["at"] for row in events if row["kind"] == "music_stop"]
    gains = [row for row in events if row["kind"] in ("duck", "unduck")]
    pauses = focus_windows(events, seconds)
    silent_cues = [{"at": round(row["at"], 3), "cue": row.get("cue"),
                    "why": "the game asked for this cue and its OGG is not where the game looks, so the game "
                           "played nothing here and neither does the reconstruction"}
                   for row in events if row["kind"] == "music_missing"]
    duck_moments = [row["at"] for row in gains]
    segments = []
    for index, row in enumerate(starts):
        start = max(0.0, float(row["at"]))
        stop = seconds if index + 1 >= len(starts) else float(starts[index + 1]["at"])
        for moment in stops:
            if start < moment < stop:
                stop = moment
        if stop - start <= 0.02:
            continue
        # The seconds this cue is really playing: the timeline minus the focus pauses, each stretch carrying the
        # second of the file that is playing when it begins. `played` is the music that has run so far, which is
        # where the game resumes from, and a resume is not the arrival second.
        stretches = []
        cursor = start
        played = 0.0
        for lost_at, back_at in pauses:
            if back_at <= start:
                continue
            if lost_at >= stop:
                break
            stretch_out = min(max(lost_at, start), stop)
            if stretch_out - cursor > 0.02:
                stretches.append((cursor, stretch_out, played))
                played += stretch_out - cursor
            cursor = max(cursor, min(back_at, stop))
            if cursor >= stop:
                break
        if stop - cursor > 0.02:
            stretches.append((cursor, stop, played))
        for stretch_index, (stretch_in, stretch_out, offset) in enumerate(stretches):
            edges = ([stretch_in] + sorted(moment for moment in duck_moments if stretch_in < moment < stretch_out)
                     + [stretch_out])
            for piece in range(len(edges) - 1):
                piece_in, piece_out = edges[piece], edges[piece + 1]
                if piece_out - piece_in <= 0.02:
                    continue
                first = stretch_index == 0 and piece == 0
                last = stretch_index == len(stretches) - 1 and piece == len(edges) - 2
                piece_offset = offset + (piece_in - stretch_in)
                if first:
                    why = "the game's own cue line, placed at the second it arrived"
                elif piece == 0:
                    paused_at = [window for window in pauses if window[0] <= piece_in][-1]
                    why = ("the game's own cue line, resumed %.3f s into the file: the log records the music "
                           "paused from %.3f s to %.3f s and 'resumed where it stopped'"
                           % (piece_offset, paused_at[0], paused_at[1]))
                else:
                    why = ("the game's own cue line, split at the gain change the log records at %.3f s"
                           % piece_in)
                segments.append({"kind": "music", "cue": row.get("cue") or os.path.basename(row["file"]),
                                 "file": row["file"], "in": round(piece_in, 3), "out": round(piece_out, 3),
                                 "offset": round(piece_offset, 3),
                                 "gain": music_gain_at(gains, piece_in, start), "loop": True,
                                 "fade_in": round(fade, 3) if first else 0.0,
                                 "fade_out": round(fade, 3) if last else 0.0,
                                 "why": why})
    for row in events:
        if row["kind"] != "sfx":
            continue
        at = max(0.0, float(row["at"]))
        if at >= seconds:
            continue
        length = float(row.get("seconds") or 0.0) or 1.0
        ends = min(seconds, at + length)
        cut = 0.0
        for lost_at, back_at in pauses:
            if at < lost_at <= ends:
                ends = lost_at
                cut = lost_at
                break
        if ends - at <= 0.02:
            continue
        segments.append({"kind": "sfx", "cue": row["id"], "file": row["file"], "in": round(at, 3),
                         "out": round(ends, 3), "offset": 0.0, "gain": row["gain"], "loop": False,
                         "fade_in": 0.0, "fade_out": 0.0,
                         "why": ("an effect the game played, cut at %.3f s where the log records the focus pause "
                                 "stopping every effect that was ringing" % cut) if cut else
                                "an effect the game played, placed at the second its log line arrived"})
    return segments, silent_cues


def filter_script_option(ffmpeg):
    """The option that reads a filtergraph from a file: -/filter_complex on ffmpeg 7 and later, where
    -filter_complex_script was removed, and -filter_complex_script before that."""
    try:
        text = subprocess.run([ffmpeg, "-version"], capture_output=True, text=True, timeout=30,
                              stdin=subprocess.DEVNULL).stdout or ""
        match = re.search(r"version\s+n?(\d+)", text)
        if match and int(match.group(1)) >= 7:
            return "-/filter_complex"
    except (OSError, subprocess.TimeoutExpired):  # gate: ok a probe that cannot answer takes the fallback below
        pass
    return "-filter_complex_script"


def render_log_audio(segments, seconds, out_path):
    """Build the track from the segments in one ffmpeg filtergraph, so the mixing is ffmpeg's and not a guess."""
    FFMPEG = ffmpeg_path()
    if not FFMPEG:
        return False, "ffmpeg was not found"
    arguments = ["-f", "lavfi", "-t", "%.3f" % seconds, "-i", "anullsrc=r=48000:cl=stereo"]
    # WinError 206: one -i per segment and the whole graph on the command line overflowed Windows' 32 KB limit once a
    # take carried hundreds of text blips. Now each distinct (file, loop) pair is ONE input that asplit fans out, and
    # the graph goes through a script file, so the command line no longer grows with the number of sounds.
    usable = []
    for segment in segments:
        length = float(segment["out"]) - max(0.0, float(segment["in"]))
        if length > 0.01:
            usable.append(segment)
    if not usable:
        return False, "no segment had a length to place"
    input_of = {}
    uses = {}
    for segment in usable:
        key = (segment["file"], bool(segment.get("loop")))
        if key not in input_of:
            input_of[key] = len(input_of) + 1
            if key[1]:
                arguments += ["-stream_loop", "-1", "-i", key[0]]
            else:
                arguments += ["-i", key[0]]
        uses[key] = uses.get(key, 0) + 1
    filters = []
    taken = {}
    for key, count in uses.items():
        n = input_of[key]
        if count == 1:
            filters.append("[%d:a]anull[i%d_0]" % (n, n))
        else:
            filters.append("[%d:a]asplit=%d%s" % (n, count, "".join("[i%d_%d]" % (n, k) for k in range(count))))
    labels = ["[0:a]"]
    index = 0
    for segment in usable:
        key = (segment["file"], bool(segment.get("loop")))
        n = input_of[key]
        k = taken.get(key, 0)
        taken[key] = k + 1
        seconds_in = max(0.0, float(segment["in"]))
        length = float(segment["out"]) - seconds_in
        # `offset` is the second of the file this piece starts at: 0 for a cue's first play, and the second the
        # music had reached for a piece that resumes after the game's focus pause ("resumed where it stopped").
        offset = max(0.0, float(segment.get("offset") or 0.0))
        index += 1
        chain = ["atrim=start=%.3f:end=%.3f" % (offset, offset + length), "asetpts=PTS-STARTPTS",
                 "volume=%.4f" % float(segment["gain"])]
        fade_in = min(float(segment.get("fade_in") or 0.0), length / 2.0)
        fade_out = min(float(segment.get("fade_out") or 0.0), length / 2.0)
        if fade_in > 0.01:
            chain.append("afade=t=in:st=0:d=%.3f" % fade_in)
        if fade_out > 0.01:
            chain.append("afade=t=out:st=%.3f:d=%.3f" % (length - fade_out, fade_out))
        chain.append("adelay=%d:all=1" % int(round(seconds_in * 1000.0)))
        filters.append("[i%d_%d]%s[r%d]" % (n, k, ",".join(chain), index))
        labels.append("[r%d]" % index)
    filters.append("%samix=inputs=%d:duration=first:normalize=0[out]" % ("".join(labels), len(labels)))
    script_path = os.path.splitext(out_path)[0] + "_filtergraph.txt"
    with open(script_path, "w", encoding="utf-8") as handle:
        handle.write(";\n".join(filters))
    arguments += [filter_script_option(FFMPEG), script_path, "-map", "[out]", "-c:a", "aac", "-b:a", "160k",
                  "-ar", "48000", "-ac", "2", "-t", "%.3f" % seconds, out_path]
    return capture_module().run_ffmpeg(FFMPEG, arguments, timeout=300)


def mean_volume_db(path):
    """ffmpeg's own volumedetect mean for a file, in dBFS, so a track of digital silence cannot pass as audio."""
    FFMPEG = ffmpeg_path()
    if not FFMPEG:
        return None
    try:
        result = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", path, "-af", "volumedetect",
                                 "-f", "null", "-"], capture_output=True, text=True, timeout=180,
                                stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return None
    for line in (result.stderr or "").splitlines():
        if "mean_volume:" in line:
            try:
                return float(line.split("mean_volume:")[1].strip().split()[0])
            except (IndexError, ValueError):
                return None
    return None


def reconstruct_audio(rows, seconds, out_path):
    """Build the take's track from the game's own log lines. Returns the dict the verify file carries."""
    events, notes = audio_events(rows)
    segments, silent_cues = log_audio_plan(events, seconds)
    pauses = focus_windows(events, seconds)
    info = {"source": AUDIO_SOURCE_NONE, "lines": len(rows), "notes": notes, "silent_cues": silent_cues,
            "segments": segments, "track": None}
    if pauses or any(row["kind"] in ("focus_lost", "focus_back") for row in events):
        # The log records a focus pause, so the record says what the rebuild did with it and which reading of
        # "every effect stopped" it used, instead of leaving a reader to assume the music played through.
        info["focus"] = {
            "pauses": [{"from": round(lost, 3), "to": round(back, 3)} for lost, back in pauses],
            "music": ("silent between each pause's seconds and resumed at the second of the file it had reached"
                      if pauses else "the log names a focus line but never a pause and a resume that pair, so no "
                                     "silence was cut"),
            "effects": FOCUS_EFFECTS_READING,
        }
    if not segments:
        info["why"] = "the log holds no audio line this tool could place, so there is nothing to rebuild"
        return info
    ok, note = render_log_audio(segments, seconds, out_path)
    if not ok:
        info["why"] = "the reconstruction did not render: %s" % note
        return info
    mean = mean_volume_db(out_path)
    info["mean_volume_db"] = None if mean is None else round(mean, 2)
    if mean is None or mean <= SILENT_TRACK_DB:
        info["why"] = ("the rebuilt track measures %s dB mean, which is silence, so it is not audio"
                       % ("unmeasured" if mean is None else "%.1f" % mean))
        return info
    music = [segment for segment in segments if segment["kind"] == "music"]
    info.update({"source": AUDIO_SOURCE_RECONSTRUCTED,
                 "track": out_path,
                 "first_music": None if not music else {"cue": music[0]["cue"],
                                                        "file": repo_relative(music[0]["file"]),
                                                        "at": music[0]["in"]},
                 "why": "%d segment%s from %d audio line%s in the game's log"
                        % (len(segments), "" if len(segments) == 1 else "s",
                           len(rows), "" if len(rows) == 1 else "s")})
    return info


def read_audio_record(video_path):
    """The audio record a take's own verify file holds, so --check can judge audio without the run that made it.

    A take recorded before card DEMO-AUDIO-CAPTURE carries a stand-in line and no `audio_source`; that file is
    read back as the stand-in it says it is, so checking it fails the audio check instead of passing quietly.
    """
    sibling = os.path.splitext(video_path)[0] + "_verify.json"
    if not os.path.isfile(sibling):
        return None
    try:
        with open(sibling, "r", encoding="utf-8") as handle:
            prior = json.load(handle)
    except (OSError, ValueError):
        return None
    detail = dict(prior.get("audio_detail") or {})
    if prior.get("audio_source"):
        detail["source"] = prior["audio_source"]
    if not detail.get("source") and "stand-in" in str(prior.get("audio") or "").lower():
        detail["source"] = "stand-in"
        detail["why"] = ("the verify file beside this take says its audio was a rendered stand-in rendered from a "
                         "theme file, not the game's own sound")
    return detail or None


def audio_summary(audio):
    """The one line the verify file carries in its `audio` field: what this take's sound is, in words."""
    audio = audio or {}
    source = audio.get("source")
    if source == AUDIO_SOURCE_GAME:
        return "game: the game's own output, recorded from %s with the video" % (audio.get("device") or "the loopback device")
    if source == AUDIO_SOURCE_RECONSTRUCTED:
        first = audio.get("first_music") or {}
        music = "" if not first else " (%s at %.2f s)" % (first.get("cue"), first.get("at") or 0.0)
        return ("reconstructed: %d segment%s placed from the game's own log, with the game's own files and gains%s, "
                "not a loopback capture"
                % (len(audio.get("segments") or []), "" if len(audio.get("segments") or []) == 1 else "s", music))
    if source == AUDIO_SOURCE_NONE:
        return "none: no loopback device and nothing in the log to rebuild, so this take has no game audio (%s)" % (
            audio.get("why") or "no reason recorded")
    return "unrecorded: this run has no account of where the audio came from"


def audio_check(audio, has_audio, final=False):
    """The audio verdict for a take, as (ok, line): game or reconstructed pass, and nothing else does.

    Card DEMO-AUDIO-CAPTURE: a final take may carry the game's own captured output, or a track rebuilt from
    the game's own log, and it may carry neither a stand-in nor silence. `audio is None` is the --check path,
    where a file on disk is read without the run that made it: then the answer is UNMEASURED, because no
    verdict is a different thing from a wrong one. `final=True` is the shipping question and it is stricter:
    a take that is about to be submitted has to name its audio, so a file with no record beside it FAILS
    rather than measuring UNMEASURED, which is the difference between "not measured" and "allowed to ship".
    """
    if audio is None:
        # No record of this take's audio at all: a file alone cannot say where its sound came from. The run path
        # always carries a record, so this shape is a video some other tool wrote, and saying "unmeasured" is
        # different from saying "wrong". A take this tool records always says game or reconstructed.
        if final:
            return False, ("FAIL this take carries no record of where its audio came from (no sibling verify "
                           "file), and a final take may not ship on a guess: record it with tools/play_demo.py, "
                           "which writes audio_source game or reconstructed into the verify file beside it")
        if has_audio:
            return True, ("UNMEASURED the file carries an audio stream and this run has no record of where it came "
                          "from: a take this tool records says game or reconstructed, and --check reads the sibling "
                          "verify file for that")
        return True, ("UNMEASURED the file carries no audio stream and this run has no record of where its sound came "
                      "from: a take this tool records says game or reconstructed, and --check reads the sibling "
                      "verify file for that")
    source = audio.get("source")
    if source == AUDIO_SOURCE_GAME:
        if not has_audio:
            return False, ("FAIL the take names the loopback device %r and the finished file carries no audio "
                           "stream, so none of the game's sound reached it" % (audio.get("device") or "?"))
        return True, ("PASS the audio is the game's own output, recorded from %r with the video"
                      % (audio.get("device") or "the loopback device"))
    if source == AUDIO_SOURCE_RECONSTRUCTED:
        first = audio.get("first_music") or {}
        where = "" if not first else ", and %s enters at %.2f s" % (first.get("cue"), first.get("at") or 0.0)
        if not has_audio:
            return False, ("FAIL the take is labelled reconstructed and the finished file carries no audio stream")
        return True, ("PASS the audio is reconstructed from the game's own log: %d cue placement%s with the game's "
                      "own files and gains%s. This is the game's sounds at the game's own steps, not a loopback "
                      "capture of the sound card"
                      % (len(audio.get("segments") or []),
                         "" if len(audio.get("segments") or []) == 1 else "s", where))
    return False, ("FAIL this take carries no game audio (%s). A final take may carry the game's own capture "
                   "(audio_source game) or a track rebuilt from the game's own log (audio_source reconstructed); "
                   "a stand-in or silence is neither. %s"
                   % ((audio.get("why") or "no reason recorded"), LOOPBACK_INSTALL))


def cut_and_scale(raw_path, viewport, script, out_path, audio_path, audio_comment=None, pix_fmt="yuv420p"):
    """Crop the raw window recording to the viewport and scale it to a true 3x of the 256x240 screen.

    `pix_fmt` is the encoder's pixel format and it defaults to the 4:2:0 every player decodes, which is what the demo
    takes and the talk take have always written. Card t_f3b7c557 found the one caller that must not: a verifier that
    measures whether every pixel of the picture is a colour the game's palette files name cannot survive chroma stored
    at a quarter of the luma resolution, because the battle screen's dim is a one pixel checker and 4:2:0 averages each
    pair into a colour the palette does not hold. tools/capture_first_fight.py passes "yuv444p" and keeps every
    threshold it had; no other caller changes.
    """
    cap = capture_module()
    FFMPEG = ffmpeg_path()
    record = script["record"]
    x, y, w, h = viewport
    width, height = int(record.get("width", 768)), int(record.get("height", 720))
    filters = ["crop=%d:%d:%d:%d" % (w, h, x, y), "scale=%d:%d:flags=neighbor" % (width, height)]
    arguments = ["-i", raw_path]
    if audio_path:
        arguments += ["-i", audio_path]
    arguments += ["-filter:v", ",".join(filters), "-r", str(record["fps"]),
                  "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", pix_fmt]
    if audio_path:
        # Card DEMO-AUDIO-CAPTURE: the mp4 says in its own words which of the two honest answers it carries, so a
        # viewer who reads the metadata is never told a rebuilt track is a capture of the sound card.
        arguments += ["-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "160k", "-shortest",
                      "-metadata", "comment=%s" % (audio_comment or "audio source is not recorded")]
    arguments.append(out_path)
    return cap.run_ffmpeg(FFMPEG, arguments, timeout=900)


# ---------------------------------------------------------------------------------------------------------------------
# The pollution watch, while the recording runs

def screen_signature(rect, grab=None):
    """A downsampled read of the screen rectangle, as a list of RGB triples, or None when the read fails.

    This is the cheap BitBlt read the card asks for: one grab a second, box filtered down to 48x45 cells, so
    the comparison between two samples is 2,160 subtractions and costs nothing next to the 60 fps capture.
    The grab is injected so the watch can be tested with no screen at all.
    """
    if grab is None:
        def default_grab(bbox):
            from PIL import ImageGrab
            return ImageGrab.grab(bbox=bbox, all_screens=True)
        grab = default_grab
    left, top, width, height = rect
    try:
        image = grab((left, top, left + width, top + height))
    except Exception:  # gate: ok a screen that cannot be read is a sample this poll does not have; owners still decide
        return None
    if image is None:
        return None
    try:
        small = image.convert("RGB").resize(SIGNATURE_CELLS, _signature_filter())
        return rgb_cells(small)
    except Exception:  # gate: ok the same, a sample that cannot be reduced is no evidence either way
        return None


def rgb_cells(image):
    """An image's pixels as a flat list of (r, g, b), row by row.

    Not getdata(): Pillow 12 deprecates it for removal in 14, and this list is the whole signature the watch compares.
    """
    pixels = image.load()
    return [pixels[x, y] for y in range(image.height) for x in range(image.width)]


def _signature_filter():
    """PIL's box filter, which averages a block instead of sampling one pixel of it."""
    from PIL import Image
    return Image.BOX


def signature_jump(before, after, level=SIGNATURE_LEVEL):
    """The share of cells whose colour moved by more than level in some channel, 0 to 1.

    Measured on real frames taken from the takes on disk (2026-10-26): the same window twelve seconds apart
    reads 0.000, the game's own scene change reads 0.896, and a window arriving over the game reads 0.968. So
    this number notices a whole-screen change and cannot, on its own, say who caused it.
    """
    if not before or not after or len(before) != len(after):
        return None
    changed = 0
    for left, right in zip(before, after):
        if max(abs(left[0] - right[0]), abs(left[1] - right[1]), abs(left[2] - right[2])) > level:
            changed += 1
    return changed / float(len(before))


def game_log_lines(path):
    """How many lines the game's own log carries right now, or 0 when it cannot be read yet."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return sum(1 for _line in handle)
    except OSError:  # gate: ok a log that is not there yet has no lines, which is what the count says
        return 0


# ---------------------------------------------------------------------------------------------------------------------
# The shot table's beats, read out of the game's own log (card t_785b61f0)
#
# Why a table here and not a paragraph in the verify report: a take is 180 s and a reader watching it should be able to
# ask one file whether the beats the write-up claims were on screen, and get an answer the game's own lines support. Each
# row is a beat of knowledge/DEMO-SCRIPT.md section 1 and the line the game writes when that beat starts. Nothing here
# reads the video: the beats are what the run did, and the frames are what the run looked like.
BEAT_CUES = (
    ("S1 title", "PP title: room rm_pp_title live"),
    ("S2 crawl", "PP title: intro started"),
    ("S3 drive", "PP: music PP-02 requested"),
    # Card t_a92c1007: this row used to name "PP scene: quay_gate_authority end at tile". The quay only story (commit
    # 28d407a2) deleted that scene: quay_gate_authority has zero hits in data/scenes, data/dialogue and game/scripts, so
    # the needle could never be satisfied and the S4 beat was unmeetable by construction. The rewritten S4 (knowledge/
    # DEMO-SCRIPT.md, 2026-11-12) opens on the wind gate, scene quay_bridge_wind on southampton_town_quay, so the beat
    # names the line that scene writes when it ends (pp_scene.gml:632).
    ("S4 gate", "PP scene: quay_bridge_wind end at tile"),
    # Card t_a92c1007: the line the walk's confirm writes when it reaches Morgan (pp_overworld.gml:1612). It is the one
    # assertion that says Right presses crossed the quay and the press that followed started the route's morgan step,
    # which is the panel's "the sprite crosses Town Quay" claim.
    ("S4 morgan talk", "PP dialogue: scene quay_morgan_encounter"),
    ("S4 morgan fight", "PP: command talk, turn 1, enemy morgan"),
    ("S5 office", "PP route: step gate handed to step office"),
    # Card t_1163ca72: the clerk's question, the player's typed line and the character's recorded answer. The line is
    # what proves the exchange reached the box rather than the beat's say pages.
    ("S5 office talk", "PP: talk scene answer, npc nye"),
    ("S5 boarding", "PP route: step office handed to step boarding"),
    ("S6 talk fight", "PP: talk pick, option 0, effect soften"),
    ("S6 hound fight", "PP: battle start tutorial_sailors"),
    ("S6 ship log save", "PP: ship's log"),
    ("S6 percy fight", "PP: command talk, turn 1, enemy percy"),
    ("S6 defeat", "PP: fight result defeat"),
    # Card t_fb7e8271: the two lines the take ends on. The game over card is drawn after the 12 step fade
    # (pp_battle_director.gml:1407) and CONTINUE is the press that puts the save back (:787), so a take that stops at
    # "defeat" and never reaches this screen is named as the missing shot and not as a mystery.
    ("S6 game over", "PP: game over frame"),
    ("S6 continue", "PP: game over, CONTINUE restored the last save"),
)
FOOTSTEP_NEEDLE = "footstep played"
LIVE_TALK_NEEDLE = "PP: talk live open, mode live"
REPLAY_TALK_NEEDLE = "PP: talk open, 3 options"


def beat_report(log_text):
    """One row a beat: whether the game's own log carried its line, and the line itself when it did."""
    rows = {}
    for name, needle in BEAT_CUES:
        line = ""
        if log_text:
            for candidate in log_text.splitlines():
                if needle in candidate:
                    line = candidate.strip()
                    break
        rows[name] = {"needle": needle, "found": bool(line), "line": line}
    return rows


def talk_report(log_text):
    """Which leg of the TALK path this take actually used, said from the game's own lines.

    The live leg is a socket to tools/ai_bridge.py and it prints `PP: talk live open, mode live`; the replay leg reads
    data/meta_bake.json and never opens one. The label is read from the log and never from the script's wish, so a take
    cannot say live because the script asked for it.
    """
    text = log_text or ""
    if LIVE_TALK_NEEDLE in text:
        return {"mode": "live", "evidence": LIVE_TALK_NEEDLE}
    if REPLAY_TALK_NEEDLE in text:
        return {"mode": "replay", "evidence": REPLAY_TALK_NEEDLE,
                "why": "the game opened the TALK panel and never wrote the live mode line, so the replies came from "
                       "the baked rows in data/meta_bake.json"}
    return {"mode": "not reached", "evidence": "",
            "why": "this take never opened the TALK panel, so it says nothing either way"}


def cues_path(video_path):
    """Where a take's beat and footstep rows are kept: beside the mp4, named from it."""
    stem, _extension = os.path.splitext(video_path)
    return stem + "_cues.json"


def write_cues(video_path, log_text, footsteps, trace, script, shot_table=None):
    """Write the sidecar a later `--check` reads, because a video file alone cannot name the beats that made it."""
    beats = beat_report(log_text)
    payload = {
        "video": video_path,
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "script": (repo_relative(script_path_used) if script_path_used else None),
        "beats": beats,
        "cues": {"footsteps": int(footsteps)},
        "talk": talk_report(log_text),
        "trace": trace,
    }
    # Card t_fb7e8271: the shot table's own rows go in the sidecar with the beats they were checked against, so a
    # `--check` on the file alone can say which shot the log named and which one it never named.
    if shot_table is not None:
        payload["shot_table"] = shot_table_report(shot_table, None, beats)
    with open(cues_path(video_path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    payload["sidecar"] = cues_path(video_path)
    return payload


def read_cues(video_path):
    """The sidecar written beside a take, or None when there is none (an older take, or a file copied on its own)."""
    path = cues_path(video_path)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):  # gate: ok a sidecar that cannot be read is treated as absent, and the check says so
        return None


class PollutionWatch(object):
    """Asks, once a second while the recording runs, who owns the rectangle and whether its pixels jumped.

    Why it exists (card t_5d1a6ec4): play_demo used to ask the coverage question before and after a recording
    and never during it, so a window raised over the game mid-run was recorded and then blamed on the art lane
    as "the game drawn off the 2C02 palette". The owner sample is the attribution a finished file cannot give.

    Two signals, and only one of them is a verdict:
      - a covering window: Windows says another window owns a sampled point of the rectangle. That marks the
        take polluted and names the process image, and after POLLUTION_STOP_POLLS consecutive samples the run
        is stopped rather than finished, because a file that is wrong for 12 s of its 73 is not a take;
      - a whole-screen jump: the signature moved by SIGNATURE_JUMP of its cells. This is recorded only when
        the game's own log did not grow during that poll (the card's wording: a jump the run's log does not
        explain), and it is evidence, never a failure, because the game's own scene change measures as a jump.
    """

    def __init__(self, hwnd, rect, owners_at, log_lines=None, grab=None,
                 clock=time.monotonic, poll_s=POLLUTION_POLL_S, stop_polls=POLLUTION_STOP_POLLS,
                 interval=None):
        self.hwnd = hwnd
        self.rect = rect
        self.owners_at = owners_at
        self.log_lines = log_lines or (lambda: 0)
        self.grab = grab
        self.clock = clock
        self.poll_s = float(interval if interval is not None else poll_s)
        self.stop_polls = int(stop_polls)
        self.samples = []
        self.started_at = None
        self.cover_polls = 0
        self.stop_requested = False
        self._previous = None
        self._previous_lines = None
        self._thread = None
        self._done = threading.Event()

    # -- one sample ------------------------------------------------------------------------------------------------
    def poll(self):
        """Take one sample and return it. Never raises: a sample that cannot be taken is one it does not have."""
        now = self.clock()
        at = 0.0 if self.started_at is None else now - self.started_at
        sample = {"at": round(at, 3)}
        lines = self.log_lines()
        try:
            covered, owners = self.owners_at()
        except Exception:  # gate: ok (a callable raised) an owner sample that cannot be taken is one it does not have
            covered, owners = [], []
        foreign = [row for row in covered if row[2]]
        if covered:
            who = sorted({"%s %r" % (image or "?", title) for _x, _y, image, title in covered})
            sample["cover"] = {"points": len(covered), "who": who,
                               "owners": sorted({image for _x, _y, image, _title in foreign})}
            self.cover_polls += 1
            if self.cover_polls >= self.stop_polls:
                self.stop_requested = True
        else:
            self.cover_polls = 0
        signature = screen_signature(self.rect, self.grab)
        if signature is not None and self._previous is not None:
            changed = signature_jump(self._previous, signature)
            if changed is not None and changed >= SIGNATURE_JUMP:
                sample["jump"] = {"changed": round(changed, 3),
                                  "explained_by_log": lines != self._previous_lines}
        if signature is not None:
            self._previous = signature
        self._previous_lines = lines
        self.samples.append(sample)
        return sample

    # -- the loop --------------------------------------------------------------------------------------------------
    def _loop(self):
        while not self._done.wait(self.poll_s):
            self.poll()

    def start(self):
        """Start sampling on its own thread, once a second, until stop() is called."""
        self.started_at = self.clock()
        self._previous = screen_signature(self.rect, self.grab)
        self._previous_lines = self.log_lines()
        self._thread = threading.Thread(target=self._loop, name="pollution-watch", daemon=True)
        self._thread.start()
        return self

    def stop(self, timeout=10.0):
        """Stop the thread and wait for it, so the evidence list is complete when it is read."""
        self._done.set()
        if self._thread is not None:
            self._thread.join(timeout)
            self._thread = None
        return self.evidence()

    # -- what it saw -----------------------------------------------------------------------------------------------
    def evidence(self):
        """The samples that are evidence: a covering window, or a jump the game's own log does not explain."""
        rows = []
        for sample in self.samples:
            if "cover" in sample:
                rows.append({"at": sample["at"], "kind": "cover", "points": sample["cover"]["points"],
                             "who": sample["cover"]["who"]})
            elif sample.get("jump") and not sample["jump"]["explained_by_log"]:
                rows.append({"at": sample["at"], "kind": "jump", "changed": sample["jump"]["changed"]})
        return rows

    def polluted(self):
        """True when a foreign window owned the rectangle at any sample: the one signal that is a verdict."""
        return any("cover" in sample for sample in self.samples)

    def cover_summary(self):
        """The owner images seen over the rectangle, for the one line that says why a take was stopped."""
        names = []
        for sample in self.samples:
            for name in sample.get("cover", {}).get("owners", []):
                if name not in names:
                    names.append(name)
        return ", ".join(names) or "a window this tool could not name"

    def first_cover_at(self):
        """The second of the first covering sample, or None."""
        for sample in self.samples:
            if "cover" in sample:
                return sample["at"]
        return None


# ---------------------------------------------------------------------------------------------------------------------
# Checks on the finished file

def cover_near(pollution, stamp, window=POLLUTION_SAMPLE_WINDOW_S):
    """The covering samples within window seconds of a sampled frame's timestamp, earliest first."""
    rows = []
    for row in pollution or []:
        if row.get("kind") != "cover":
            continue
        at = row.get("at")
        if isinstance(at, (int, float)) and abs(at - stamp) <= window:
            rows.append(row)
    return sorted(rows, key=lambda row: row.get("at", 0.0))


def frame_verdict(share, colours, min_colours, palette_min, art_min=OFF_PALETTE_ART_MIN):
    """One word for a sampled frame: game, blank, art, not the game, or unjudged.

    The split this card is about (t_5d1a6ec4). A frame is the game when enough of its pixels are 2C02 colours;
    a frame with too few colours to be a picture is blank; a frame that is off the palette is "art" when most of
    its pixels are still the game's own palette (a misdrawn colour costs what it covers), and "not the game"
    when under art_min of its pixels are palette colours at all, which no drawing mistake produces. A share that
    could not be measured is "unjudged": this tool does not guess, and the palette check fails on its own line.
    """
    if share is None:
        return "unjudged"
    if share >= palette_min and (colours or 0) >= min_colours:
        return "game"
    if (colours or 0) < min_colours:
        return "blank"
    return "not the game" if share < art_min else "art"


def palette_share(path, allowed, tolerance=12):
    """The share of a frame's pixels that sit on a legal 2C02 colour, allowing for video compression.

    The viewport search in tools/nes_composite_check.py asks for an exact palette colour, which is the right
    test on a PNG straight off the game's screen. It cannot be the test on an h264 frame: chroma is stored at
    a quarter of the luma resolution and the quantiser moves every sample a little, so a real recording of
    the title measured 18,923 colours and an exact share of 0.000 while the crawl frames, which are almost
    flat black, still measured 0.966. This measure keeps the promise the check exists for (the frame is the
    game's own picture, not a terminal's) without pretending a compressed frame is an uncompressed one: every
    pixel must land within `tolerance` of some palette entry, and the share of pixels that do is reported.
    """
    try:
        from PIL import Image
    except Exception:
        return None
    try:
        with Image.open(path) as image:
            counts = image.convert("RGB").getcolors(maxcolors=1 << 22)
    except Exception:
        return None
    if not counts:
        return None
    colours = list(allowed)
    total = 0
    hit = 0
    for count, pixel in counts:
        total += count
        for entry in colours:
            if (abs(pixel[0] - entry[0]) <= tolerance and abs(pixel[1] - entry[1]) <= tolerance
                    and abs(pixel[2] - entry[2]) <= tolerance):
                hit += count
                break
    if total == 0:
        return None
    return hit / float(total)


def palette_entries():
    """The legal 2C02 colours, through the same loader tools/nes_composite_check.py uses."""
    try:
        import nes_composite_check as ncc
        return list(ncc.load_palette(ncc.default_palette_path(ROOT))["allowed"])
    except Exception:  # gate: ok without the palette no frame can be judged, and the check says so instead of passing.
        return None


def frame_luma(path):
    """The mean luma of a frame, 0 to 255. A black rectangle scores under 4, a game scene far above."""
    try:
        from PIL import Image
    except Exception:
        return None
    try:
        with Image.open(path) as image:
            grey = image.convert("L")
            histogram = grey.histogram()
    except Exception:
        return None
    total = sum(histogram)
    if total == 0:
        return None
    weighted = sum(value * count for value, count in enumerate(histogram))
    return weighted / float(total)


def video_stream(ffprobe, path):
    """The first video stream's width, height, fps, codec and pixel format, or None.

    pix_fmt is asked for because a capture whose verifier measures colours has to say what the encoder kept: card
    t_f3b7c557 records the first fight at yuv444p, and the report names it so a 4:2:0 file is never mistaken for one.
    """
    if not ffprobe:
        return None
    try:
        result = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0",
                                 "-show_entries", "stream=width,height,r_frame_rate,codec_name,pix_fmt",
                                 "-of", "json", path],
                                capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
        data = json.loads(result.stdout or "{}")
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None
    streams = data.get("streams") or []
    return streams[0] if streams else None


def audio_stream(ffprobe, path):
    """True when the file carries an audio stream."""
    if not ffprobe:
        return False
    try:
        result = subprocess.run([ffprobe, "-v", "error", "-select_streams", "a",
                                 "-show_entries", "stream=codec_name", "-of", "json", path],
                                capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
        data = json.loads(result.stdout or "{}")
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return False
    return bool(data.get("streams"))


def verify_video(path, script, report_path=None, pollution=None, cues=None, audio=None, final=False, shot_table=None):
    """Check a finished mp4 against the script. Returns (ok, report).

    The four checks the card asks for, in the order a wrong recording shows up:
      1. the duration is at least record.min_seconds of real gameplay;
      2. the frame is the script's 3x of the 256x240 screen, at the script's fps;
      3. sampled frames are not black;
      4. sampled frames are the game and not a terminal: enough of them must sit on the legal 2C02 palette
         within the tolerance a compressed frame needs, and two samples must differ, so the scene moves.

    And the two this card added (t_5d1a6ec4):
      5. a frame that is off the palette is split by how far off it is. Under OFF_PALETTE_ART_MIN fewer than
         half its pixels are 2C02 colours, which no drawing mistake produces, so it is "not the game" and the
         take fails as polluted; between that floor and palette_share_min it stays the art lane's finding.
         SUMMARY text no longer sends the art lane to look at a frame that is a terminal window.
      6. `pollution` is what the run's pollution watch saw while recording (who owned the rectangle, and any
         unexplained whole-screen jump). A covered sample fails the take by name and stops the recording, so a
         window raised over the game mid-run is a polluted take and never an art finding. When the take is
         checked from disk alone (`--check`) there is no run log, so the check says UNMEASURED rather than
         pretending either way, and check 5 is what holds.

    The exact 3x viewport search (capture_title.viewport_box_and_score) is deliberately not run on these
    frames: it asks for exact palette colours, which is the right question on a PNG taken straight off the
    game's screen, and it is the pre-roll frame's job before the recording starts. On an h264 frame it
    returns 0.0 for a real frame of the game (measured on the 2026-10-22 run_001: the title frame scored 0.0
    with a palette share of 0.93), so using it here would only manufacture a contradiction.
    """
    cap = capture_module()
    FFMPEG = ffmpeg_path()
    report = {"video": path, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "checks": {}, "samples": [],
              "pollution": list(pollution or []), "polluted": bool(pollution)}
    record = script["record"]
    min_seconds = float(record["min_seconds"])
    width, height = int(record.get("width", 768)), int(record.get("height", 720))
    fps_wanted = int(record["fps"])
    checks = script.get("checks") or {}
    luma_min = float(checks.get("min_luma", MIN_MEAN_LUMA))
    min_colours = int(checks.get("min_distinct_colours", 6))
    diff_min = float(checks.get("frame_diff_min", 0.001))
    min_lit = int(checks.get("min_lit_frames", 4))

    if not FFMPEG:
        return False, {"error": "ffmpeg was not found"}
    ffprobe = cap.ffprobe_path(FFMPEG)
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        report["checks"]["file"] = "FAIL the file is missing or empty"
        return False, report
    report["bytes"] = os.path.getsize(path)
    report["checks"]["file"] = "PASS %d bytes" % report["bytes"]

    duration = cap.probe_duration(ffprobe, path)
    report["duration_s"] = duration
    if duration is None:
        report["checks"]["duration"] = "FAIL the duration could not be read"
        return False, report
    if duration < min_seconds:
        report["checks"]["duration"] = ("FAIL %.3f s of video, under the %.1f s the submission needs"
                                        % (duration, min_seconds))
        ok_duration = False
    else:
        report["checks"]["duration"] = "PASS %.3f s, at least %.1f s" % (duration, min_seconds)
        ok_duration = True

    stream = video_stream(ffprobe, path)
    report["stream"] = stream
    ok_stream = False
    if not stream:
        report["checks"]["stream"] = "FAIL no video stream could be read"
    else:
        measured = (int(stream.get("width", 0)), int(stream.get("height", 0)))
        numerator, _, denominator = str(stream.get("r_frame_rate", "0/1")).partition("/")
        try:
            measured_fps = float(numerator) / float(denominator or 1)
        except ValueError:
            measured_fps = 0.0
        report["fps"] = measured_fps
        if measured != (width, height):
            report["checks"]["stream"] = ("FAIL the frame is %dx%d, not the %dx%d the script asks for"
                                          % (measured[0], measured[1], width, height))
        elif measured_fps + 0.5 < fps_wanted:
            report["checks"]["stream"] = ("FAIL the frame rate is %.2f, under the %d the script asks for"
                                          % (measured_fps, fps_wanted))
        else:
            report["checks"]["stream"] = ("PASS %dx%d %s at %.2f fps"
                                          % (measured[0], measured[1], stream.get("codec_name"), measured_fps))
            ok_stream = True
    report["has_audio"] = audio_stream(ffprobe, path)
    # Card DEMO-AUDIO-CAPTURE: the take says where its sound came from, and only two answers pass. `audio` is the
    # dict the run built; it is None on the --check path, where a file on disk is read without the run that made it.
    ok_audio, audio_line = audio_check(audio, report["has_audio"], final=final)
    report["checks"]["audio"] = audio_line
    report["audio"] = audio_summary(audio)
    report["audio_source"] = (audio or {}).get("source")
    if final:
        # Card DEMO-AUDIO-CAPTURE: the verify file says this file was asked the shipping question, so a reader
        # can tell an UNMEASURED-only check from one that would have refused to ship.
        report["final_take"] = True
    if audio:
        detail = {}
        for key in ("device", "lines", "segments", "silent_cues", "notes", "track", "why", "mean_volume_db",
                    "first_music", "devices", "focus"):
            if audio.get(key) is not None:
                detail[key] = audio[key]
        track = detail.get("track")
        if track:
            detail["track"] = repo_relative(track)
        report["audio_detail"] = detail

    work = os.path.join(BUILD_DIR, "_demo_check")
    os.makedirs(work, exist_ok=True)
    allowed = palette_entries()
    palette_min = float(checks.get("palette_share_min", 0.90))
    palette_tolerance = int(checks.get("palette_tolerance", 12))
    min_on_palette = int(checks.get("min_on_palette_frames", 4))
    frames = []
    lit = 0
    on_palette = 0
    off_palette_rows = []
    foreign_rows = []
    for index, fraction in enumerate(SAMPLE_FRACTIONS):
        stamp = max(0.5, min(duration - 0.5, duration * fraction))
        frame_path = os.path.join(work, "frame_%d.png" % index)
        row = {"t": round(stamp, 3)}
        if not cap.extract_frame(FFMPEG, path, stamp, frame_path):
            row["frame"] = "missing"
            report["samples"].append(row)
            frames.append(None)
            continue
        luma = frame_luma(frame_path)
        colours = cap.distinct_colours(frame_path)
        share = palette_share(frame_path, allowed, palette_tolerance) if allowed else None
        row.update({"luma": None if luma is None else round(luma, 2),
                    "colours": colours,
                    "palette_share": None if share is None else round(share, 4)})
        if luma is not None and luma >= luma_min:
            lit += 1
        # One word for this frame, from measurements only (card t_5d1a6ec4). See frame_verdict.
        verdict = frame_verdict(share, colours, min_colours, palette_min)
        if verdict == "game":
            on_palette += 1
        else:
            # Why this frame is not counted as the game's picture, written into the row itself.
            row["verdict"] = verdict
            row["why"] = ("%s colours, under the %d a picture with content has"
                          % (colours, min_colours)) if (colours or 0) < min_colours else (
                "palette share %s, under the %.2f a frame of the game needs"
                % ("unmeasured" if share is None else "%.3f" % share, palette_min))
            if verdict == "not the game":
                # Under the floor, most of the screen is not a 2C02 colour at all, which no drawing mistake
                # produces: a window covered the rectangle. Named, and never the art lane's finding.
                covered = cover_near(pollution, stamp)
                if covered:
                    row["covered_by"] = covered[0]["who"]
                foreign_rows.append(row)
            elif verdict == "art":
                # Off the palette but mostly on it: the game's own picture with colors the NES cannot output.
                # This one is the art lane's, and it is named, never hidden.
                off_palette_rows.append(row)
        report["samples"].append(row)
        frames.append(frame_path)

    report["lit_frames"] = lit
    report["on_palette_frames"] = on_palette
    report["samples_taken"] = len([row for row in report["samples"] if "luma" in row])
    ok_lit = lit >= min_lit
    report["checks"]["not_black"] = ("PASS %d of %d sampled frames are lit (mean luma %.1f and up, %d needed)"
                                     % (lit, len(SAMPLE_FRACTIONS), luma_min, min_lit)) if ok_lit else \
                                    ("FAIL only %d of %d sampled frames are lit, %d needed"
                                     % (lit, len(SAMPLE_FRACTIONS), min_lit))
    # Every frame has to be a picture with real content; that is what rules out a black rectangle, a blank
    # window and a single colour desktop. Then enough of the frames have to be the game's own 2C02 picture to
    # rule out a recording of a terminal or of another window.
    ok_game = on_palette >= min_on_palette and all((row.get("colours") or 0) >= min_colours
                                                   for row in report["samples"] if "colours" in row)
    report["checks"]["not_a_terminal"] = (
        "PASS %d of %d sampled frames are the game's own picture: at least %.2f of their pixels sit on a legal "
        "2C02 colour within %d levels (the allowance a compressed frame needs) and every frame carries at least "
        "%d colours; a terminal or another window meets neither"
        % (on_palette, len(SAMPLE_FRACTIONS), palette_min, palette_tolerance, min_colours)) if ok_game else (
        "FAIL only %d of %d sampled frames are the game's own picture (%d needed): %s"
        % (on_palette, len(SAMPLE_FRACTIONS), min_on_palette,
           ", ".join("t=%.1f palette share %s, %s colours"
                     % (row["t"], row.get("palette_share"), row.get("colours")) for row in report["samples"]
                     if (row.get("palette_share") or 0) < palette_min) or "see the samples"))
    if off_palette_rows:
        report["findings"] = [
            "FINDING %d of %d sampled frames are the game drawn off the 2C02 palette: %s. These are the art "
            "lane's to look at: the frames carry most of their pixels on the palette, so they are the game's "
            "own picture with colours the NES cannot output, not a covering window. Palette share under %.2f "
            "means some pixels are colours the NES cannot output; under %.2f it would not be the game at all."
            % (len(off_palette_rows), len(SAMPLE_FRACTIONS),
               ", ".join("t=%.1f share %.3f" % (row["t"], row.get("palette_share") or 0.0)
                         for row in off_palette_rows), palette_min, OFF_PALETTE_ART_MIN)
        ]
    if foreign_rows:
        report.setdefault("findings", []).append(
            "POLLUTED %d of %d sampled frames are not the game: %s. Fewer than %.2f of their pixels are 2C02 "
            "colours, which no drawing mistake produces, so this is a window over the game rectangle and NOT an "
            "art finding: the take has to be re-recorded.%s"
            % (len(foreign_rows), len(SAMPLE_FRACTIONS),
               ", ".join("t=%.1f share %.3f%s" % (row["t"], row.get("palette_share") or 0.0,
                                                  "" if "covered_by" not in row
                                                  else " (covered by %s)" % " and ".join(row["covered_by"]))
                         for row in foreign_rows), OFF_PALETTE_ART_MIN,
               "" if pollution else " The run log for this take is not here, so the frames are the evidence."))

    # Who owned the rectangle while the recording ran (card t_5d1a6ec4). A cover is a verdict; a jump without
    # a game log line to explain it is only evidence, which is why it is reported and not failed.
    covers = [row for row in (pollution or []) if row.get("kind") == "cover"]
    jumps = [row for row in (pollution or []) if row.get("kind") == "jump"]
    if covers:
        report["checks"]["not_polluted"] = (
            "FAIL a window covered the game during the recording: %s. The take is polluted and is not an art "
            "finding; re-record it with nothing raised over the rectangle."
            % "; ".join("at t=%.1f %s owned a sampled point of the rectangle"
                        % (row.get("at", 0.0), " and ".join(row.get("who") or ["a window"])) for row in covers[:5]))
        ok_pollution = False
    elif foreign_rows:
        report["checks"]["not_polluted"] = (
            "FAIL %d of %d sampled frames are not the game's picture (%s): fewer than %.2f of their pixels are "
            "2C02 colours, which no drawing mistake produces, so the rectangle was not the game's own for the "
            "whole recording.%s"
            % (len(foreign_rows), len(SAMPLE_FRACTIONS),
               ", ".join("t=%.1f share %.3f" % (row["t"], row.get("palette_share") or 0.0) for row in foreign_rows),
               OFF_PALETTE_ART_MIN,
               "" if pollution is None
               else " The pollution watch did not catch the window, which is why the frames are the test."))
        ok_pollution = False
    elif pollution is None:
        report["checks"]["not_polluted"] = (
            "UNMEASURED no run log beside this take, so nothing here says who owned the rectangle while it was "
            "recorded; every sampled frame is the game's own picture, which is what this check can say from the "
            "file alone")
        ok_pollution = True
    else:
        report["checks"]["not_polluted"] = (
            "PASS the rectangle was the game's own for the whole recording: no covering window in any owner "
            "sample")
        ok_pollution = True
    if jumps:
        report["checks"]["jumps"] = (
            "NOTE %d unexplained whole screen jump%s while recording (%s). A jump is not proof of a cover: the "
            "game's own scene change measures the same way, so this line is evidence and the owner samples above "
            "are the verdict"
            % (len(jumps), "" if len(jumps) == 1 else "s",
               ", ".join("t=%.1f moved %.2f of the screen" % (row.get("at", 0.0), row.get("changed") or 0.0)
                         for row in jumps[:5])))

    differences = []
    for i in range(len(frames)):
        for j in range(i + 1, len(frames)):
            if frames[i] and frames[j]:
                ratio = cap.frames_differ(frames[i], frames[j])
                if ratio is not None:
                    differences.append(ratio)
    best = max(differences) if differences else None
    report["max_frame_diff"] = best
    ok_motion = best is not None and best >= diff_min
    report["checks"]["motion"] = ("PASS the largest difference between sampled frames is %.5f of the pixels, so "
                                 "the scene moves" % best) if ok_motion else (
        "FAIL the sampled frames do not differ (largest %s), so the recording is a still" % best)

    ok = bool(ok_duration and ok_stream and ok_lit and ok_game and ok_motion and ok_pollution and ok_audio)

    # The shot table's beats, and the footstep cues (card t_785b61f0). A 180 s take is not one picture, so the file
    # that judges it has to say which beats the game's own log named and how many footstep cues the walk played. Both
    # are read from the sidecar this tool writes beside the mp4 at record time, because a video file alone cannot name
    # them; a script that names required beats and has no sidecar FAILS here rather than passing unmeasured.
    required_beats = [str(name) for name in (checks.get("required_beats") or [])]
    required_footsteps = int(checks.get("required_footsteps") or 0)
    cue_rows = (cues or {})
    beat_rows = cue_rows.get("beats") or {}
    report["beats"] = beat_rows
    report["talk"] = cue_rows.get("talk") or talk_report(None)
    footsteps = int((cue_rows.get("cues") or {}).get("footsteps") or 0)
    report["cues"] = {"footsteps": footsteps, "required_footsteps": required_footsteps,
                      "sidecar": cues_path(path) if cues is not None else None}
    named = [name for name in required_beats if (beat_rows.get(name) or {}).get("found")]
    missing = [name for name in required_beats if name not in named]
    if required_beats and cues is None:
        report["checks"]["beats"] = (
            "FAIL no cue log beside this take (%s), so nothing here names the beats the %d the script requires were on "
            "screen: %s" % (os.path.basename(cues_path(path)), len(required_beats), ", ".join(required_beats)))
        ok_beats = False
    elif missing:
        report["checks"]["beats"] = (
            "FAIL %d of the %d beats the script requires were never named by the game's own log: %s. Found: %s"
            % (len(missing), len(required_beats), ", ".join(missing), ", ".join(named) or "none"))
        ok_beats = False
    else:
        report["checks"]["beats"] = (
            "PASS the game's own log names %d of the %d beats the shot table asks for: %s"
            % (len(named), len(required_beats), ", ".join(named)) if required_beats else
            "PASS the game's own log was read for the shot table's beats (%d of %d found)"
            % (len([name for name, _needle in BEAT_CUES if (beat_rows.get(name) or {}).get("found")]), len(BEAT_CUES)))
        ok_beats = True
    if footsteps < required_footsteps:
        report["checks"]["cues"] = (
            "FAIL the take carries %d footstep cues, and the script asks for at least %d"
            % (footsteps, required_footsteps))
        ok_cues = False
    else:
        report["checks"]["cues"] = (
            "PASS %d footstep cues in the take, at least the %d the script asks for" % (footsteps, required_footsteps))
        ok_cues = True
    ok = bool(ok and ok_beats and ok_cues)
    # Card t_fb7e8271: the shot table's own two questions, asked of the finished file. The plan adds up to 180 s inside
    # the table's tolerance, and the game's log named every shot's line, so a take that lost S5 or the game over is
    # failed by the name of the shot it lost instead of by a paragraph a reader has to interpret.
    if shot_table is not None:
        table_ok, table_line = shot_table_check(shot_table, duration, beat_rows, gated=any(e.get("marker_wait_s") for e in script["events"]))
        report["checks"]["shot_table"] = table_line
        report["shot_table"] = shot_table_report(shot_table, duration, beat_rows)
        ok = bool(ok and table_ok)
    report["ok"] = ok
    # Card t_7450df91 (RECEIPTS-LABELS): every Meta number this take's record carries is named with one of
    # three labels and one receipt in data/receipts/meta_receipts.jsonl, so a reader never meets a number
    # without a place to check it. tools/check_receipts.py re-reads the block and re-hashes each source.
    try:
        report["meta_numbers"] = receipts.meta_numbers()
    except receipts.ReceiptError as exc:
        # A build whose own Meta numbers cannot be vouched for says so in the file rather than printing a
        # number nobody can find; the receipts check then fails the take by name.
        report["meta_numbers"] = []
        report["meta_numbers_why"] = str(exc)
    # A jump is evidence and never a verdict (the game's own scene change measures as one), so only a cover or
    # a frame that is not the game's picture makes a take polluted.
    report["polluted"] = bool(covers) or bool(foreign_rows)
    if report_path:
        with open(report_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return ok, report


def post_recording_cover_note(covered):
    """The NOTE line for a window that owned a sampled point when the recording stopped, or None.

    Card t_4da3eb20: this reading is evidence and never a failure. The owner samples taken DURING the
    recording are the verdict (PollutionWatch) and the finished file's frames are the second net, so the same
    question asked once at the end cannot red a take. It used to append a failure, and that text reached
    tools/judge_panel.py as "Recorded failure in that run" on takes whose frames were all the game's.
    """
    if not covered:
        return None
    who = sorted({"%s %r" % (row[2] or "?", row[3]) for row in covered})
    return ("NOTE another window owned %d of the sampled points of the rectangle when the recording stopped "
            "(%s). This line is evidence and not a verdict: the owner samples taken during the recording and "
            "the frames of this file are what decide, so a take whose frames are all the game's still passes."
            % (len(covered), "; ".join(who)))


def print_report(report):
    for name in ("file", "duration", "stream", "audio", "not_black", "not_a_terminal", "not_polluted", "jumps",
                 "motion", "beats", "cues", "shot_table"):
        line = report["checks"].get(name)
        if line:
            print("  %s" % line)
    talk = report.get("talk") or {}
    if talk.get("mode"):
        print("  talk leg: %s%s" % (talk["mode"], "" if not talk.get("why") else " (%s)" % talk["why"]))
    meta = report.get("meta_numbers") or []
    for row in meta:
        print("  meta number: %s = %s (%s, receipt %s)"
              % (row.get("name"), row.get("value"), row.get("label"), row.get("receipt")))
    if report.get("meta_numbers_why"):
        print("  meta numbers: none labelled, %s" % report["meta_numbers_why"])
    for note in report.get("notes") or []:
        print("  %s" % note)
    for row in report.get("samples", []):
        print("  sample t=%.2f s: luma %s, %s colours, palette share %s%s"
              % (row["t"], row.get("luma"), row.get("colours"), row.get("palette_share"),
                 "" if "why" not in row else " (%s)" % row["why"]))
    for finding in report.get("findings", []):
        print("  %s" % finding)


# ---------------------------------------------------------------------------------------------------------------------
# The run

def repo_relative(path):
    """A path as the verify file records it: relative to the repo when it can be, absolute when it cannot.

    Card t_688422b1: `os.path.relpath` raises ValueError when the two paths are on different drives ("path is on mount
    'C:', start on mount 'D:'"), and every caller here is writing a line of evidence into a report, where a crash is
    worse than a long path. A take whose streams folder sits on another disk (a cache, a second drive), or a gate tree
    built in a temp folder while the repo lives on D:, must still be able to say where a file is. Separators become
    forward slashes so the same string reads the same on Pine, which is where the suite also runs.
    """
    try:
        return os.path.relpath(path, ROOT).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def out_path_for(script):
    """The mp4 path the script names, resolved under the repository root."""
    return os.path.join(ROOT, script["record"]["out"])


def out_stem(path):
    """The stem of the recording's own file name: run_002 for output/demo/run_002.mp4.

    The verify file and the stand-in track are named after the mp4, not after the script, so a re-recording
    written with --out cannot overwrite the verdict that belongs to the take already on disk.
    """
    return os.path.splitext(os.path.basename(path))[0]


def run_demo(script, keep_raw=False, shot_table=None):
    """Launch the built game, play the script, record it, cut it to 3x, then check the file."""
    # Card PINE-HONEST (t_84fe63ff): both modules come in on first use, and a host with no window primitives
    # refuses here, where a window would actually be opened, so --check and --dry-run still work where nothing can
    # be shown. 4 is the harness's not-measured code, so a reader sees "not measured" and never "passed".
    cap = capture_module()  # raises PlatformUnavailable when the drawing path cannot be imported at all
    pp_launch = launch_module()
    FFMPEG = ffmpeg_path()
    if not can_draw():
        print(UNAVAILABLE_LINE)
        print("  this host has no window primitives, so there is no window to record")
        return EXIT_UNAVAILABLE
    # Card CAPTURE-QUIET: the gate is asked before anything is opened or deleted, so a refused run leaves the last
    # good recording on disk and costs one log line.
    if not LAUNCH.gate("demo recording"):
        return pp_launch.EXIT_REFUSED
    if not FFMPEG:
        print("ffmpeg was not found in the winget package folder and is not on PATH")
        return 1
    ffprobe = cap.ffprobe_path(FFMPEG)
    print("ffmpeg: %s" % FFMPEG)
    print("ffprobe: %s" % (ffprobe or "not found, the duration check cannot run"))

    build = cap.newest_build()
    if build is None:
        print("no built game found under %s" % cap.GAME_OUTPUT_DIR)
        return 1
    exe_path, win_path = build
    print("build: %s" % exe_path)

    # Card DEMO-AUDIO-CAPTURE: what this host offers is printed and carried into the verify file, so a take made
    # on a machine with no loopback device says so in its own evidence and not only in a person's memory.
    devices = audio_device_report(FFMPEG)
    loopback = devices["loopback"]
    print("system audio: %s" % (loopback or "no loopback capture device on this host"))
    for row in devices["dshow"]:
        print("  dshow %s: %s" % (row["kind"], row["name"]))
    for note in devices["dshow_notes"]:
        print("  dshow: %s" % note)
    print("  ffmpeg wasapi demuxer: %s" % ("present" if devices["wasapi_demuxer"] else
                                           "absent in this build, so no WASAPI loopback can be opened"))
    if not loopback:
        print("  %s" % LOOPBACK_INSTALL)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = out_path_for(script)
    stem = out_stem(out_path)
    verify_path = os.path.join(OUTPUT_DIR, "%s_verify.json" % stem)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    raw_path = os.path.join(OUTPUT_DIR, "_%s_raw.mp4" % script["name"])
    for stale in (out_path, raw_path):
        if os.path.exists(stale):
            os.remove(stale)

    fps = script["clock"]["fps"]
    end_step = (script.get("checks") or {}).get("end_step") or max(event["step"] for event in script["events"])
    seconds = planned_seconds(script)
    print("plan: %d events over %.1f s on a %d fps clock" % (len(script["events"]), seconds, fps))
    if shot_table is not None:
        # Card t_fb7e8271: the table is printed before anything opens, so the run log says what the take is meant to
        # be shot by shot, and the verify file later says which of those lines the game's own log wrote.
        print_shot_table(shot_table)

    os.makedirs(BUILD_DIR, exist_ok=True)
    log_path = os.path.join(BUILD_DIR, "demo-game.log")
    launch_args = [part.replace("{win}", win_path) for part in script["game"]["launch_args"]]
    print("launching %s" % " ".join([exe_path] + launch_args))
    # Card CAPTURE-QUIET-IMPL: one call starts the game muted, without a console window, and prints the one PP: muted
    # line from this run's own log. The exit line comes from run.finish() in the finally below.
    extra = {}
    for part in script["game"].get("env", {}) or {}:
        extra[part] = script["game"]["env"][part]
    run = pp_launch.start_game(exe_path, win_path, log_path=log_path, policy=LAUNCH, label="demo recording",
                               extra=extra or None)
    process = run.process
    # Card ROUTE-STALL: the replay may hold at every marker_wait_s event, so the harness watchdog allows the same budget the
    # recorder bound does (the 2026-11-02 19:47 run was killed at 493 s, which was the plan plus 240 s with no hold budget).
    # Card RECORDER-ORPHAN: the recorder starts after the watchdog, so the watchdog gets a one element holder and the
    # recorder is put into it below; when the watchdog fires it then stops the recorder too, so a kill can never leave
    # ffmpeg recording the desktop after the harness is gone.
    recorder_holder: list = [None]
    cap.start_watchdog(process, int(record_bound_seconds(script, seconds)) + 240, recorder=recorder_holder)
    failures = []
    recorder = None
    recorder_log = None
    watch = None
    log_audio = None
    try:
        match = cap.find_window(
            lambda hwnd, pid, title, visible, rect: visible and title.lower().startswith(
                script["game"]["window_title"].lower()),
            timeout_s=cap.GAME_WINDOW_TIMEOUT_S)
        if match is None:
            print("the game window did not appear within %.0f s" % cap.GAME_WINDOW_TIMEOUT_S)
            return 1
        hwnd = match[0]
        # Card CAPTURE-QUIET: the window is moved off the primary screen unless --show was given, so the recording
        # happens on a screen Nayil is not looking at.
        LAUNCH.place(hwnd, cap.get_window_rect(hwnd))
        image_name = cap.process_image_name(match[1])
        if image_name.lower() != script["game"]["exe"].lower():
            print("the window belongs to %r, not to %s, so it is not the game window"
                  % (image_name, script["game"]["exe"]))
            return 1
        print("game window found: %r (hwnd %s, image %s)" % (match[2], hwnd, image_name))

        time.sleep(cap.GAME_SETTLE_S)
        previous = cap.bring_to_front(hwnd)
        cap.hold_on_top(hwnd)
        time.sleep(cap.FOREGROUND_SETTLE_S)
        placed = cap.get_window_rect(hwnd)
        if placed is None:
            print("the game window has no rectangle, cannot record it")
            return 1
        rect, coverage = cap.ensure_game_visible(hwnd, placed)
        print("coverage: %s" % coverage)
        if rect is None:
            print("FAIL another window covers the game, so the recording would show that window")
            return 1

        pre_roll = os.path.join(BUILD_DIR, "_demo_preroll.png")
        rect, viewport, score, note = pre_roll_viewport(hwnd, pre_roll)
        print("pre-roll: %s" % note)
        min_score = float((script.get("checks") or {}).get("nes_score_min", 0.90))
        if viewport is None or score < min_score:
            print("FAIL the window is not showing the game's own 3x screen (score %.3f, %.2f needed)"
                  % (score, min_score))
            return 1
        print("recording rectangle %d,%d %dx%d, crop %s then scale to 3x"
              % (rect[0], rect[1], rect[2], rect[3], viewport))

        focused, focus_note = cap.ensure_key_focus(hwnd)
        print("keyboard focus: %s" % focus_note)
        if not focused:
            print("FAIL the game never took the keyboard focus, so no key press would reach it")
            return 1

        def send_key(vk):
            """One real key press, with the focus retaken first. A posted key proves nothing."""
            for _attempt in range(4):
                if cap.game_has_focus(hwnd):
                    return cap.send_vk_focused(vk)
                ok, why = cap.ensure_key_focus(hwnd, attempts=2, settle=0.15)
                if not ok:
                    continue
            raise SystemExit("the game lost the keyboard focus and would not take it back (%s)" % why)

        record_bound = record_bound_seconds(script, seconds, end_step)
        record_seconds = record_bound
        # The recording's clock starts here: the log watch stamps each audio line with its distance from this
        # instant, so a rebuilt track is placed on the same clock the video runs on.
        audio_started_at = time.monotonic()
        recorder, recorder_log, recorder_log_path = start_recorder(rect, raw_path, record_seconds, fps, loopback)
        recorder_holder[0] = recorder
        print("recording up to %.1f s of the window to %s (stopped by hand %.1f s after the replay)"
              % (record_bound, raw_path, RECORD_TAIL_S))
        log_audio = LogAudioWatch(log_path, audio_started_at)
        log_audio.start()

        # Card t_5d1a6ec4: ask who owns the rectangle while it is being recorded, not only before and after.
        watch = PollutionWatch(hwnd, rect, owners_at=lambda: cap.cover_report(hwnd, rect),
                               log_lines=lambda: game_log_lines(log_path))
        watch.start()
        print("pollution watch: who owns the rectangle, and whether its pixels jump, every %.1f s"
              % POLLUTION_POLL_S)

        replay = Replay(script, hwnd, log_path, send_key)
        failures += replay.run(end_step, should_stop=lambda: watch.stop_requested)
        stopped_by_cover = watch.stop_requested
        pollution = watch.stop()
        if stopped_by_cover:
            failures.append("the recording was stopped at t=%.1f s because %s covered the game, so this take is "
                            "polluted and has to be re-recorded"
                            % (watch.first_cover_at() or 0.0, watch.cover_summary()))
            print("polluted: stopping the recorder, %s owns the rectangle" % watch.cover_summary())
            if recorder.poll() is None:
                recorder.terminate()

        # The replay is over: keep recording for the tail, then ask ffmpeg to finish the file. The length
        # reconstruct_audio and recorded_seconds use is what was actually recorded, never the upper bound.
        stop_note = stop_recorder(recorder, RECORD_TAIL_S - 0.5)
        if stop_note:
            failures.append(stop_note)
        record_seconds = min(record_bound, time.monotonic() - audio_started_at)
        try:
            recorder.wait(timeout=record_bound + 60)
        except subprocess.TimeoutExpired:
            recorder.terminate()
            try:
                recorder.wait(timeout=15)
            except subprocess.TimeoutExpired:
                recorder.kill()
            failures.append("ffmpeg did not stop after q and was terminated, so the file may be truncated")
        cap.release_on_top(hwnd)
        # The game's own account of its sound, stamped while the recording ran (card DEMO-AUDIO-CAPTURE).
        audio_rows = log_audio.stop() if log_audio is not None else []
        print("audio lines the game wrote: %d" % len(audio_rows))

        # Who owns the rectangle now that the recorder has stopped, asked BEFORE restore_foreground (card
        # t_4da3eb20). restore_foreground raises the window that was in front when this run started, so a
        # reading taken after it measures the window this tool itself put there and a clean take collected a
        # false line. The answer is a NOTE in the report and never a failure: the owner samples taken during
        # the recording are the verdict and the finished file's frames are the second net, while a failure
        # line here reached the judge panel as "Recorded failure in that run" on takes that were clean.
        covered, _owners = cap.cover_report(hwnd, rect)
        post_record_note = post_recording_cover_note(covered)
        cap.restore_foreground(previous)

        if recorder.returncode not in (0, None) and not stopped_by_cover:
            failures.append("ffmpeg exited with code %s, its log is %s" % (recorder.returncode, recorder_log_path))
            with open(recorder_log_path, "r", encoding="utf-8", errors="replace") as handle:
                print(handle.read()[-800:])
        if not os.path.isfile(raw_path) or os.path.getsize(raw_path) == 0:
            print("FAIL the raw recording is missing or empty")
            return 1

        # The game's own account of the run: a crash, and the two lines that prove the run reached the room.
        with open(log_path, "r", encoding="utf-8", errors="replace") as handle:
            log_text = handle.read()
        if "PP CRASH" in log_text:
            crash = [line for line in log_text.splitlines() if "PP CRASH" in line][0]
            failures.append("the game reported a crash: %s" % crash[:200])
        if "PP title: intro started" not in log_text:
            failures.append("the game never reported the intro starting, so NEW GAME did not take")
        footsteps = len([line for line in log_text.splitlines() if "footstep played" in line])
        print("footstep cues in the game log: %d" % footsteps)
        if footsteps == 0:
            failures.append("the game played no footstep cue, so the Right presses did not reach the walk")

        audio_path = None
        audio_comment = None
        audio_info = {"source": AUDIO_SOURCE_NONE, "device": loopback, "devices": devices,
                      "why": "no loopback device and no audio line in the log to rebuild from"}
        if loopback:
            audio_info = {"source": AUDIO_SOURCE_GAME, "device": loopback, "devices": devices}
            audio_comment = ("audio is the game's own output, recorded from the loopback device %s with the video"
                             % loopback)
            print("audio: the game's own output, recorded from %s with the video" % loopback)
        else:
            # Card DEMO-AUDIO-CAPTURE, second path: no capture device, so the track is rebuilt from the log the
            # game itself wrote, file by file, at the second each line arrived. It is labelled reconstructed.
            track_path = os.path.join(OUTPUT_DIR, "%s_audio.m4a" % stem)
            rebuilt = reconstruct_audio(audio_rows, record_seconds, track_path)
            rebuilt["devices"] = devices
            audio_info = rebuilt
            for note in rebuilt.get("notes") or []:
                print("audio note: %s" % note)
            for cue in rebuilt.get("silent_cues") or []:
                print("audio note: %.2f s cue %s was silent in the game, so it is silent here too"
                      % (cue.get("at") or 0.0, cue.get("cue")))
            if rebuilt["source"] == AUDIO_SOURCE_RECONSTRUCTED:
                audio_path = track_path
                first = rebuilt.get("first_music") or {}
                audio_comment = ("audio is reconstructed from the game's own log: %d cue placements at the seconds "
                                 "the game's own audio lines arrived, with the game's own files and gains, mean %s dB; "
                                 "it is not a capture of the sound card"
                                 % (len(rebuilt["segments"]), rebuilt.get("mean_volume_db")))
                print("audio: rebuilt %d segments from %d log lines, mean %s dB; %s enters at %.2f s: %s"
                      % (len(rebuilt["segments"]), len(audio_rows), rebuilt.get("mean_volume_db"),
                         first.get("cue"), first.get("at") or 0.0, track_path))
            else:
                print("FAIL no game audio: %s" % rebuilt.get("why"))

        made, note = cut_and_scale(raw_path, viewport, script, out_path, audio_path, audio_comment=audio_comment)
        if not made:
            print("FAIL the cut and scale did not run: %s" % note)
            return 1
        print("wrote %s" % out_path)

        # Card t_785b61f0: the beats and the footsteps go in a sidecar beside the mp4, written while the game's own log
        # is still in hand, so `--check` on the file alone can name the shot table's beats afterwards.
        cues = write_cues(out_path, log_text, footsteps, replay.trace, script, shot_table=shot_table)
        print("wrote %s" % cues)
        print("talk leg: %s" % json.dumps(talk_report(log_text), sort_keys=True))

        ok, report = verify_video(out_path, script, verify_path, pollution=pollution, cues=cues, audio=audio_info,
                                  shot_table=shot_table)
        report["script"] = repo_relative(script_path_used) if script_path_used else None
        report["run"] = {"trace": replay.trace, "failures": failures, "game_log": repo_relative(log_path),
                         "footsteps": footsteps, "planned_seconds": round(seconds, 3),
                         "recorded_seconds": round(record_seconds, 3)}
        # A cover seen once the recording had stopped is a NOTE beside the checks, never one of the six and
        # never an entry in run.failures (card t_4da3eb20: the judge panel reads that list as a defect record).
        if post_record_note:
            report.setdefault("notes", []).append(post_record_note)
        with open(verify_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print_report(report)
        for failure in failures:
            print("  note: %s" % failure)
        if report.get("polluted"):
            print("POLLUTED %s: a window was over the game rectangle, so this take is not the game's own "
                  "picture. It is a capture failure and not an art finding: re-record it." % out_path)
            return 1
        if not ok:
            print("FAIL %s did not pass its checks" % out_path)
            return 1
        print("PASS %s" % out_path)
        return 0
    finally:
        # The one exit line, and the game closed before the raw file is cleaned up (card CAPTURE-QUIET-IMPL).
        run.finish()
        if log_audio is not None:
            # The audio watch reads the game's log every 50 ms; it is stopped here whatever path the run took.
            try:
                log_audio.stop()
            except Exception:  # gate: ok best effort stop of the log reader during cleanup.
                pass
        if watch is not None:
            # A sampling thread is stopped before the run returns, whatever path it took, so no poll outlives it.
            try:
                watch.stop()
            except Exception:  # gate: ok best effort stop of the sampling thread during cleanup.
                pass
        if recorder is not None and recorder.poll() is None:
            recorder.kill()
        if recorder_log is not None:
            try:
                recorder_log.close()
            except Exception:  # gate: ok best effort cleanup of the ffmpeg log handle.
                pass
        if not keep_raw and os.path.isfile(raw_path) and os.path.isfile(out_path):
            try:
                os.remove(raw_path)
            except OSError:  # gate: ok the raw file is scratch; a failed delete costs disk and nothing else.
                pass


script_path_used = None


def main():
    global script_path_used
    global LAUNCH
    parser = argparse.ArgumentParser(description="Play a scripted run of the built game and record it.")
    # Card PINE-HONEST (t_84fe63ff): the launcher module is imported by launch_module(), so a host without the
    # Windows path answers with one line and the not-measured code instead of a traceback from the argument parser.
    try:
        pp_launch = launch_module()
    except PlatformUnavailable as error:
        return unavailable(error)
    # Card CAPTURE-QUIET: the same four launch flags every launching tool takes (tools\pp_launch.py). Card t_688422b1:
    # the wait is this tool's own default, so a bare `python tools\play_demo.py` on a busy desktop holds the launch
    # instead of spending the night's only attempt on one refusal.
    pp_launch.add_launch_flags(parser, default_wait=IDLE_WAIT_S)
    parser.add_argument("--script", default=None,
                        help="the demo script to play (default data\\demo\\run_002.json, the 253.5 s three battle take, the QA take; "
                             "with --shot-table the table names the script)")
    parser.add_argument("--shot-table", default=None, metavar="NAME",
                        help="play the shot table called NAME in data\\demo\\shot_table.json, so one command plays the "
                             "documented take: the table names its script, its shots and sub-shots, their seconds, "
                             "and the game's own log line each shot has to produce. `--shot-table full` is the 180 s "
                             "submission take through the dock office, the TALK fight, the ship's log save and the "
                             "game over")
    parser.add_argument("--out", default=None, help="override the mp4 path the script names")
    parser.add_argument("--path", default=None, metavar="NAME",
                        help="play one of the two S6 win paths by name: the hook card t_e48b13a6 asks for, one flag "
                             "and no manual input. `talk` is TALK three times so the meter climbs to 60, then SPARE, so "
                             "no blow is thrown; `command` is one Confirm on FIGHT that ends the deck hound at its 2 hp. "
                             "Each plays the shot table of the same path, so `--path talk` is `--shot-table talk-win`")
    parser.add_argument("--check", action="store_true",
                        help="check an existing mp4 against the script instead of playing the game")
    parser.add_argument("--video", default=None, help="with --check, the mp4 to check")
    parser.add_argument("--final", action="store_true",
                        help="with --check, ask the shipping question: a take with no record of where its audio "
                             "came from fails instead of measuring UNMEASURED")
    parser.add_argument("--dry-run", action="store_true",
                        help="validate the script and print its timeline in seconds, then stop")
    parser.add_argument("--keep-raw", action="store_true", help="keep the uncropped window recording")
    parser.add_argument("--audio-devices", action="store_true",
                        help="print this host's ffmpeg capture devices, whether it has a loopback, and the install "
                             "a machine without one needs, then stop")
    args = parser.parse_args()
    LAUNCH = pp_launch.policy_from_args(args)

    try:
        if args.audio_devices:
            # Card DEMO-AUDIO-CAPTURE: the device list is evidence, so it is printed from ffmpeg's own words and
            # never summarised from a document. Nothing here opens a window or records anything.
            FFMPEG = ffmpeg_path()
            if not FFMPEG:
                print("ffmpeg was not found in the winget package folder and is not on PATH")
                return 1
            print("ffmpeg: %s" % FFMPEG)
            report = audio_device_report(FFMPEG)
            for row in report["dshow"]:
                print("dshow %s: %s" % (row["kind"], row["name"]))
            for note in report["dshow_notes"]:
                print("dshow: %s" % note)
            print("ffmpeg wasapi demuxer: %s" % ("present" if report["wasapi_demuxer"] else "absent in this build"))
            print("loopback device for the game's own audio: %s" % (report["loopback"] or "none"))
            if report["install"]:
                print(report["install"])
            return 0

        # Card t_e48b13a6: the two S6 win paths are selectable by name. A path is a shot table with a shorter name,
        # so `--path talk` and `--shot-table talk-win` play the same documented take, and the table is what names the
        # script, the shots and the log lines the run has to produce.
        path_name = (args.path or "").strip().lower()
        if path_name:
            if path_name not in PATH_TABLES:
                print("no path called %r: the paths are %s"
                      % (args.path, ", ".join("%s (%s)" % (key, why) for key, why in sorted(PATH_WHY.items()))))
                return 2
            chosen = PATH_TABLES[path_name]
            if args.shot_table and args.shot_table != chosen:
                print("--path %s plays the shot table %r and --shot-table named %r: ask for one"
                      % (path_name, chosen, args.shot_table))
                return 2
            args.shot_table = chosen
            print("path %r: %s" % (path_name, PATH_WHY[path_name]))

        # Card t_fb7e8271: a named shot table is read first, because the table names the script it plays. The table is
        # validated before the game is launched, so a plan that does not add up to 180 s costs one line and not a take.
        table = None
        if args.shot_table:
            table = load_shot_table(args.shot_table)
            problems = validate_shot_table(table)
            if problems:
                print("the shot table %r in %s is not playable:" % (table.get("name"), repo_relative(SHOT_TABLE)))
                for problem in problems:
                    print("  %s" % problem)
                return 1
            print("shot table %r: %s" % (table.get("name"), table.get("title") or table.get("script")))

        script_path = args.script
        if script_path is None and table is not None and table.get("script"):
            script_path = os.path.join(ROOT, str(table["script"]))
        script_path_used = os.path.abspath(script_path or DEFAULT_SCRIPT)
        script = load_script(script_path_used)
        if table is not None:
            problems = validate_shot_table_script(table, script)
            if problems:
                print("the shot table %r does not match %s:"
                      % (table.get("name"), repo_relative(script_path_used)))
                for problem in problems:
                    print("  %s" % problem)
                return 1
            # The table's own beats and end step are the run's, so play and check read one plan and not two.
            script = apply_shot_table(script, table)
        if args.out:
            script = json.loads(json.dumps(script))
            script["record"]["out"] = args.out

        if args.dry_run:
            print("%s: %d events, %.1f s, %d fps, seeds %s"
                  % (script["name"], len(script["events"]), planned_seconds(script), script["clock"]["fps"],
                     json.dumps({key: value for key, value in script["seeds"].items() if key != "note"},
                                sort_keys=True)))
            if table is not None:
                print_shot_table(table)
            for row in timeline(script):
                print("  %6.2f s  beat %2d  %-4s %-8s %s" % (row["second"], row["beat"], row["kind"],
                                                            row["key"] or "", row["id"]))
            beats = sorted({row["beat"] for row in timeline(script)})
            print("beats covered by the script: %s" % ", ".join(str(beat) for beat in beats))
            if table is not None:
                print("shot table %r sums to %.2f s against %.2f s plus or minus %.2f s: %s"
                      % (table.get("name"), shot_table_seconds(table), float(table.get("total_seconds") or 0.0),
                         float(table.get("tolerance_seconds") or 0.0),
                         "inside" if abs(shot_table_seconds(table) - float(table.get("total_seconds") or 0.0))
                         <= float(table.get("tolerance_seconds") or 0.0) else "OUTSIDE"))
            return 0

        if args.check:
            path = os.path.abspath(args.video) if args.video else out_path_for(script)
            print("checking %s against %s" % (path, os.path.basename(script_path_used)))
            if args.final:
                # Card DEMO-AUDIO-CAPTURE: the shipping question. A cut with no verify file beside it cannot
                # answer "is this the game's audio", and a take that cannot answer does not ship.
                print("final take: a file with no record of its audio fails, it does not measure UNMEASURED")
            # The sidecar written at record time is what names the beats from the file alone (card t_785b61f0). A take
            # with none is checked, and the beats check says UNMEASURED in those words instead of passing.
            cues = read_cues(path)
            if cues is None:
                print("no cue log beside this take (%s), so the beats it was made of cannot be named from the file"
                      % os.path.basename(cues_path(path)))
            ok, report = verify_video(path, script, cues=cues, audio=read_audio_record(path), final=args.final,
                                      shot_table=table)
            print_report(report)
            return 0 if ok else 1

        return run_demo(script, keep_raw=args.keep_raw, shot_table=table)
    except PlatformUnavailable as error:
        # Anything that needed the drawing path and could not have it: --check on a host with no ffprobe path, a
        # dry run whose key table cannot be read. One line and 4, never a green and never a silent zero.
        return unavailable(error)


if __name__ == "__main__":
    sys.exit(main())
