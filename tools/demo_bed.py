"""The demo video's stand-in audio bed, assembled from the game's own cue files.

Why this file exists
--------------------
The recording this project submits carries a stand-in track, because this PC reports no loopback
device and the game has nothing to record (knowledge/nodes/audio-routing.md section 3: no music cue
can reach the mixer yet). That stand-in was one title theme loop for the whole film, so a judge
heard one cue and the mp4's own comment had to say the audio was not the game's.

This tool builds a bed instead: the recording's own beat windows taken from its verify file and from
the run script that drove it, and one of the game's own delivered cues per window, at the game's own
gains and crossfade. Nothing is composed, nothing is recut, and no cue is re-rendered. The result is
the game's musical identity in the order the game would have played it, and the page that carries it
(knowledge/DEMO-BED-2026-10-26.md) can name each cue and its entry second.

The numbers, and where each one comes from
------------------------------------------
music gain 0.7          data/audio.json volume on every cue row, and the PP_AUDIO_GAIN_MUSIC macro
duck minus 6 dB         game/scripts/pp_title/pp_title.gml, the crawl's own duck, 0.7 * 10 ** (-0.3)
                        = 0.3508, knowledge/nodes/audio-routing.md section 4
crossfade 30 steps      PP_AUDIO_FADE_STEPS, 30 * 16.6667 ms = 500 ms, audio-routing.md section 5
cue per beat window     the beat's own map's "music" line in data/maps/all.json (ship_small PP-05),
                        and the title screen's own theme, which is PP-01's row in data/audio.json
room load               the trace's e08 marker step minus the run script's own marker_delay_steps,
                        then plus the app machine's PP_FADE_STEPS 12 (0.200 s) to the black frame
                        it swaps mode on, game/scripts/pp_app/pp_app.gml
48 kHz stereo 16 bit    the demo mux's own stream shape, knowledge/VIDEO-PLAN.md section 6
minus 16 LUFS, TP -1    knowledge/VIDEO-PLAN.md section 6, the loudness the edit mixes to

Why there is no drive cue
-------------------------
A take records the crawl and then the ship room, and nothing between them. rm_pp_drive is reachable
only with PP_DRIVE_ROOM set (data/demo/manifest.json), and the picture of demo-talk-2026-10-26.mp4 is
the crawl to 42.05 s, a 0.400 s fade, and the ship room from 42.48 s. So this bed carries no PP-02 and
the title's own 240 step drive is not a window here; a bed that put PP-02 over that second would be
scoring a shot no recording contains (card t_81178392).

What it refuses to do
---------------------
It reads data/audio.json and never writes it. It does not use a cue that is pending (delivered_file
null) or a cue whose wiring is under a gamedev ruling (PP-04, card t_279ef225), and it fails loudly
if the plan names one. It does not touch tools/play_demo.py, which owns the capture. It writes one
new file under output/demo/ and never overwrites a recording.

Usage:
    python tools\\demo_bed.py                    build the bed for the newest recording
    python tools\\demo_bed.py --check            re-read the wav and compare it to the recording
    python tools\\demo_bed.py --recording PATH   another recording
    python tools\\demo_bed.py --out PATH         another output path
    python tools\\demo_bed.py --plan             print the plan and the 32 beat accounting, write nothing
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_REL = "data/audio.json"
MANIFEST_REL = "data/demo/manifest.json"
MAPS_REL = "data/maps/all.json"
DEMO_DIR_REL = "output/demo"

SR = 48000
CHANNELS = 2
MUSIC_GAIN = 0.7
DUCK_DB = -6.0
FADE_S = 0.5
TARGET_LUFS = -16.0
TRUE_PEAK_CEIL = -1.0

# Cues a plan may not carry: PP-04's fight wiring is under a gamedev ruling (card t_279ef225).
FORBIDDEN_CUES = {"PP-04": "card t_279ef225, the fight wiring is under a gamedev ruling"}

# The three rhythm constants this bed runs on: two from the title's intro, one from the app's own fade.
FPS = 60
INTRO_PAN_STEPS = 180        # PP_TITLE_INTRO_PAN_STEPS, pp_title.gml
APP_FADE_STEPS = 12          # PP_FADE_STEPS, game/scripts/pp_config/pp_config.gml, one way of the fade
HANDOFF_EVENT = "e08"        # the game's own "intro finished, starting the run in rm_pp_ship" line

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


def repo(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def load_json(path: str) -> dict:
    with open(repo(path), encoding="utf-8") as fh:
        return json.load(fh)


def cues_by_id(audio: dict) -> dict:
    return {row["id"]: row for row in audio["cues"]}


def cue_file(cue: dict) -> str:
    """The delivered OGG a cue row names, or a refusal. No fallback guessing."""
    if cue.get("pending") or not cue.get("delivered_file"):
        raise SystemExit("demo_bed: cue %s is pending, so it cannot enter the bed" % cue["id"])
    path = repo(cue["delivered_file"])
    if not os.path.isfile(path):
        raise SystemExit("demo_bed: cue %s names %s, which is not on disk" % (cue["id"], cue["delivered_file"]))
    return path


def cue_for_map(maps: dict, map_id: str) -> str:
    """The cue a map's own music line names, so the bed's choice is the game's choice."""
    for row in maps["maps"]:
        if row.get("id") == map_id:
            return row["music"]
    raise SystemExit("demo_bed: data/maps/all.json holds no map %s" % map_id)


def newest_recording(demo_dir: str) -> str:
    """The newest mp4 in output/demo, by mtime, ignoring the backups folder."""
    picks = []
    for name in os.listdir(demo_dir):
        if name.endswith(".mp4"):
            path = os.path.join(demo_dir, name)
            picks.append((os.path.getmtime(path), path))
    if not picks:
        raise SystemExit("demo_bed: no mp4 under %s" % demo_dir)
    return sorted(picks)[-1][1]


def verify_for(recording: str) -> dict:
    stem = os.path.splitext(recording)[0]
    path = stem + "_verify.json"
    if not os.path.isfile(path):
        raise SystemExit("demo_bed: no verify file beside %s" % os.path.basename(recording))
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def measured_marks(verify: dict) -> dict:
    """The recording's own event seconds, from the capture's trace. Measured, never assumed."""
    marks = {}
    for row in verify.get("run", {}).get("trace", []):
        marks.setdefault(row["id"], float(row["at_second"]))
    for need in ("e02", "e04", "e08"):
        if need not in marks:
            raise SystemExit("demo_bed: the verify trace carries no %s, so a beat window is unknown" % need)
    return marks


def scripted_steps(run_script: dict) -> dict:
    """Step numbers from the run script's own notes, for the beats no key press marks."""
    return {row["id"]: int(row["step"]) for row in run_script.get("events", []) if "step" in row}


def trace_row(verify: dict, event_id: str) -> dict:
    for row in verify.get("run", {}).get("trace", []):
        if row["id"] == event_id:
            return row
    raise SystemExit("demo_bed: the verify trace carries no %s, so a beat window is unknown" % event_id)


def marker_delay_steps(script: dict, event_id: str) -> int:
    """The delay the run script adds after a marker line, data/demo/run_001.json."""
    for row in script.get("events", []):
        if row["id"] == event_id:
            return int(row.get("marker_delay_steps", 0))
    raise SystemExit("demo_bed: the run script carries no event %s, so the handoff second is unknown" % event_id)


def handoff_second(verify: dict, script: dict) -> float:
    """The second the title prints its handoff line, on the recording's own clock.

    The capture records a marker event at the step it read the line plus that script's own
    marker_delay_steps (run_001.json e08, 60), so the line's second is the recorded step minus the delay.
    A trace whose detail says the marker was never seen recorded the script's fallback step instead,
    which measures nothing, so this refuses rather than guesses.
    """
    row = trace_row(verify, HANDOFF_EVENT)
    if "not seen" in str(row.get("detail", "")):
        raise SystemExit("demo_bed: the verify trace did not see %s's marker, so the handoff second is unmeasured"
                         % HANDOFF_EVENT)
    delay = marker_delay_steps(script, HANDOFF_EVENT)
    return float(row["at_second"]) - delay / float(FPS)


def beat_windows(verify: dict, script: dict) -> list:
    """One row per beat the recording can show, in seconds on the recording's own clock.

    The capture writes at_second already on the recording's clock (a step index divided by 60, the
    game's room speed), so no offset correction is applied here.
    """
    marks = measured_marks(verify)
    steps = scripted_steps(script)
    duration = float(verify["duration_s"])

    b1 = 0.0
    b2 = marks["e02"]
    b3 = marks["e04"]
    b4 = b3 + INTRO_PAN_STEPS / FPS
    b5 = steps["e05"] / FPS
    b6 = steps["e06"] / FPS
    b7 = steps["e07"] / FPS
    handoff = handoff_second(verify, script)
    room_load = handoff + APP_FADE_STEPS / FPS
    return [
        {"beat": 1, "start": b1, "end": b2, "why": "the attract, up to the first Enter (trace e02)"},
        {"beat": 2, "start": b2, "end": b3, "why": "the menu and NEW GAME, up to the intro line (trace e04)"},
        {"beat": 3, "start": b3, "end": b4,
         "why": "the fade and the stars, the intro's own 180 step pan (pp_title.gml, PP_TITLE_INTRO_PAN_STEPS)"},
        {"beat": 4, "start": b4, "end": b5, "why": "crawl beats 1 to 2, from the run script's e05 step 1500"},
        {"beat": 5, "start": b5, "end": b6, "why": "crawl beats 3 to 4, from the run script's e06 step 1900"},
        {"beat": 6, "start": b6, "end": b7,
         "why": "crawl beats 5 to 6 and the hold, from the run script's e07 step 2340"},
        {"beat": 7, "start": b7, "end": room_load,
         "why": "the crawl's last card, the title's handoff line and its 12 step fade out; the picture swaps "
                "rooms at the app machine's black frame, and no recording shows a drive shot"},
        {"beat": 26, "start": room_load, "end": duration,
         "why": "rm_pp_ship on ship_small from the room load, the eight step walk and the sailor's box, to the "
                "end of the file"},
    ]


def plan(verify: dict, script: dict, audio: dict, maps: dict) -> tuple:
    """The segments: which cue, where it starts, where it ends, and the beats it carries."""
    cues = cues_by_id(audio)
    windows = beat_windows(verify, script)
    by_beat = {row["beat"]: row for row in windows}
    title_cue = "PP-01"
    ship_cue = cue_for_map(maps, "ship_small")
    handoff = handoff_second(verify, script)

    segments = [
        {"cue": title_cue, "source_offset": 0.0, "in": 0.0, "out": by_beat[3]["end"] + FADE_S,
         "gain_db": 0.0, "beats": [1, 2, 3],
         "why": "the title screen's own theme, at the music gain, from the file's start"},
        {"cue": title_cue, "source_offset": by_beat[3]["end"], "in": by_beat[3]["end"],
         "out": handoff + FADE_S, "gain_db": DUCK_DB, "beats": [4, 5, 6, 7],
         "why": "the same pass under the text crawl, ducked 6 dB as pp_title ducks it, to the handoff line"},
        {"cue": ship_cue, "source_offset": 0.0, "in": handoff, "out": by_beat[26]["end"],
         "gain_db": 0.0, "beats": [26],
         "why": "ship_small's own cue, entering on the handoff so the 0.500 s crossfade is at full gain on the "
                "room, to the end of the file"},
    ]
    for seg_row in segments:
        if seg_row["cue"] in FORBIDDEN_CUES:
            raise SystemExit("demo_bed: %s may not enter the bed: %s" % (seg_row["cue"], FORBIDDEN_CUES[seg_row["cue"]]))
        if seg_row["cue"] not in cues:
            raise SystemExit("demo_bed: data/audio.json names no cue %s" % seg_row["cue"])
        cue_file(cues[seg_row["cue"]])
    return segments, windows


def decode(path: str, workdir: str) -> np.ndarray:
    """One source to 48 kHz mono float, through ffmpeg. Every source is mono (ffprobe channels 1)."""
    out = os.path.join(workdir, hashlib.sha1(path.encode("utf-8")).hexdigest()[:12] + ".f32")
    cmd = [FFMPEG, "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", out]
    subprocess.run(cmd, check=True)
    return np.fromfile(out, dtype="<f4")


def equal_power_in(n: int) -> np.ndarray:
    return np.sin(0.5 * np.pi * np.linspace(0.0, 1.0, n, endpoint=False))


def equal_power_out(n: int) -> np.ndarray:
    return np.cos(0.5 * np.pi * np.linspace(0.0, 1.0, n, endpoint=False))


def render(segments: list, cues: dict, total_s: float, fades: list, workdir: str) -> np.ndarray:
    """Sum the segments on one timeline at the game's own gains."""
    n_total = int(round(total_s * SR))
    mix = np.zeros(n_total, dtype=np.float64)
    n_fade = int(round(FADE_S * SR))
    cache = {}
    for index, seg in enumerate(segments):
        path = cue_file(cues[seg["cue"]])
        if path not in cache:
            cache[path] = decode(path, workdir)
        src = cache[path]
        start = int(round(seg["in"] * SR))
        stop = int(round(seg["out"] * SR))
        n = stop - start
        offset = int(round(seg["source_offset"] * SR))
        if offset + n > len(src):
            raise SystemExit("demo_bed: %s is %0.3f s and the plan asks for %0.3f s from %0.3f s"
                             % (seg["cue"], len(src) / SR, n / SR, seg["source_offset"]))
        take = src[offset:offset + n].astype(np.float64)
        env = np.ones(n, dtype=np.float64)
        curve = fades[index]
        head = min(n_fade, n)
        tail = min(n_fade, n)
        if curve == "linear":
            env[:head] *= np.linspace(0.0, 1.0, head, endpoint=False)
            env[n - tail:] *= np.linspace(1.0, 0.0, tail, endpoint=False)
        else:
            env[:head] *= equal_power_in(head)
            env[n - tail:] *= equal_power_out(tail)
        gain = MUSIC_GAIN * (10.0 ** (seg["gain_db"] / 20.0))
        mix[start:stop] += take * env * gain
    return mix


def write_s16(path: str, mono: np.ndarray) -> None:
    """Stereo by duplication: every source is mono and the game's bus is mono, so there is nothing to pan."""
    clipped = int(np.count_nonzero(np.abs(mono) > 1.0))
    if clipped:
        raise SystemExit("demo_bed: the mix would clip at %d samples; nothing written" % clipped)
    inter = np.stack([mono, mono], axis=1)
    import wave
    with wave.open(path, "wb") as fh:
        fh.setnchannels(CHANNELS)
        fh.setsampwidth(2)
        fh.setframerate(SR)
        fh.writeframes((inter * 32767.0).astype("<i2").tobytes())


def measure_loudness(path: str) -> dict:
    """EBU R128 integrated loudness and true peak, from ffmpeg's own loudnorm meter."""
    cmd = [FFMPEG, "-v", "info", "-i", path, "-af", "loudnorm=print_format=json", "-f", "null", "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    blob = proc.stderr
    start = blob.rfind("{")
    end = blob.rfind("}")
    if start < 0 or end < 0:
        raise SystemExit("demo_bed: ffmpeg printed no loudnorm block")
    raw = json.loads(blob[start:end + 1])
    return {"input_i": float(raw["input_i"]), "input_tp": float(raw["input_tp"]),
            "input_lra": float(raw["input_lra"]), "input_thresh": float(raw["input_thresh"])}


def apply_gain(src: str, dst: str, gain_db: float) -> None:
    cmd = [FFMPEG, "-v", "error", "-y", "-i", src, "-af", "volume=%0.4fdB" % gain_db,
           "-ar", str(SR), "-ac", str(CHANNELS), "-c:a", "pcm_s16le", dst]
    subprocess.run(cmd, check=True)


def probe(path: str) -> dict:
    cmd = [FFPROBE, "-v", "error", "-show_entries",
           "format=duration,bit_rate:stream=codec_name,sample_rate,channels",
           "-of", "json", path]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def shown(path: str) -> str:
    """The path as printed: repo relative when it lives in the repo, absolute otherwise.

    --out may name a file on another drive (a scratch copy for a byte comparison), and os.path.relpath
    raises ValueError across drives on Windows, so the done line must not depend on it.
    """
    try:
        return os.path.relpath(path, ROOT).replace("\\", "/")
    except ValueError:
        return os.path.abspath(path).replace("\\", "/")


def date_in(name: str) -> str:
    found = re.findall(r"(\d{4}-\d{2}-\d{2})", os.path.basename(name))
    return found[-1] if found else "undated"


def accounting(windows: list, segments: list) -> list:
    """All 32 beats of the sheet, each one covered by a named segment or explicitly silent."""
    rows = []
    for beat in range(1, 33):
        window = next((w for w in windows if w["beat"] == beat), None)
        if window is None:
            rows.append({"beat": beat, "state": "silent", "segment": None})
            continue
        mid = 0.5 * (window["start"] + window["end"])
        hit = next((i for i, seg in enumerate(segments) if seg["in"] <= mid < seg["out"]), None)
        if hit is None:
            rows.append({"beat": beat, "state": "silent", "segment": None})
        else:
            rows.append({"beat": beat, "state": "covered", "segment": hit})
    return rows


def print_plan(segments, cues, windows, rows, recording, duration):
    print("P: recording %s, %0.3f s" % (os.path.basename(recording), duration))
    print("P: %d segments over %d cues" % (len(segments), len({s["cue"] for s in segments})))
    print("P: %-6s %-7s %-46s %7s %7s %6s %8s  %s"
          % ("seg", "cue", "source", "in", "out", "fade", "gain", "beats"))
    for index, seg in enumerate(segments):
        print("P: %-6d %-7s %-46s %7.3f %7.3f %6.3f %8s  %s"
              % (index + 1, seg["cue"], cues[seg["cue"]]["delivered_file"], seg["in"], seg["out"],
                 FADE_S, "%+0.1f dB" % seg["gain_db"], ",".join(str(b) for b in seg["beats"])))
    covered = [r for r in rows if r["state"] == "covered"]
    silent = [r for r in rows if r["state"] == "silent"]
    print("P: beats covered by a cue %d, explicitly silent %d, total %d"
          % (len(covered), len(silent), len(rows)))
    print("P: silent beats %s" % ",".join(str(r["beat"]) for r in silent))


def beat_table(windows, rows):
    print("P: beat windows on the recording's own clock")
    for window in windows:
        print("P: beat %-3d %7.3f to %7.3f  %s"
              % (window["beat"], window["start"], window["end"], window["why"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble the demo's stand-in audio bed from the game's cue files.")
    parser.add_argument("--recording", default=None, help="the mp4 to match; default the newest under output/demo")
    parser.add_argument("--out", default=None, help="the wav to write; default output/demo/audio-bed-<date>.wav")
    parser.add_argument("--check", action="store_true", help="re-read the wav and compare it to the recording")
    parser.add_argument("--plan", action="store_true", help="print the plan and the accounting, write nothing")
    args = parser.parse_args(argv)

    FFMPEG = shutil.which("ffmpeg")
    FFPROBE = shutil.which("ffprobe")
    if not FFMPEG or not FFPROBE:
        raise SystemExit("demo_bed: ffmpeg and ffprobe must be on PATH")

    audio = load_json(AUDIO_REL)
    manifest = load_json(MANIFEST_REL)
    maps = load_json(MAPS_REL)
    cues = cues_by_id(audio)
    recording = args.recording or newest_recording(repo(DEMO_DIR_REL))
    verify = verify_for(recording)
    script = load_json(manifest["script"])
    duration = float(verify["duration_s"])
    segments, windows = plan(verify, script, audio, maps)
    rows = accounting(windows, segments)
    fades = ["linear", "linear", "equal_power"]
    out = args.out or os.path.join(repo(DEMO_DIR_REL), "audio-bed-%s.wav" % date_in(recording))

    print_plan(segments, cues, windows, rows, recording, duration)
    if args.plan:
        beat_table(windows, rows)
        return 0

    if os.path.exists(out) and not args.check:
        raise SystemExit("demo_bed: %s already exists; every build is a new file, so name another --out" % out)

    if args.check:
        info = probe(out)
        got = float(info["format"]["duration"])
        stream = info["streams"][0]
        print("P: %s %s %s Hz %s ch, %0.3f s" % (os.path.basename(out), stream["codec_name"],
                                                 stream["sample_rate"], stream["channels"], got))
        delta = abs(got - duration)
        print("P: %s duration %0.3f s against the recording's %0.3f s, delta %0.3f s, %s"
              % ("PASS" if delta <= 0.1 else "FAIL", got, duration, delta,
                 "inside the 0.1 s the card allows" if delta <= 0.1 else "outside the 0.1 s the card allows"))
        return 0 if delta <= 0.1 else 1

    work = tempfile.mkdtemp(prefix="demo_bed_")
    try:
        mono = render(segments, cues, duration, fades, work)
        peak = float(np.max(np.abs(mono)))
        print("P: mix peak %+.2f dBFS before the loudness pass" % (20.0 * np.log10(max(peak, 1e-12))))
        raw = os.path.join(work, "mix.wav")
        write_s16(raw, mono)
        loud = measure_loudness(raw)
        gain = TARGET_LUFS - loud["input_i"]
        ceiling = TRUE_PEAK_CEIL - loud["input_tp"]
        if gain > ceiling:
            print("Q: the loudness gain would put the true peak at %+.2f dBTP, over the %+.1f the edit mixes to, so it is cut to the ceiling"
                  % (loud["input_tp"] + gain, TRUE_PEAK_CEIL))
            gain = ceiling
        print("P: measured %+.2f LUFS integrated, %+.2f dBTP, gain %+.2f dB" % (loud["input_i"], loud["input_tp"], gain))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        apply_gain(raw, out, gain)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    info = probe(out)
    got = float(info["format"]["duration"])
    stream = info["streams"][0]
    print("P: wrote %s, %s %s Hz %s ch, %d bytes"
          % (shown(out), stream["codec_name"], stream["sample_rate"],
             stream["channels"], os.path.getsize(out)))
    delta = abs(got - duration)
    print("P: %s duration %0.3f s against the recording's %0.3f s, delta %0.3f s"
          % ("PASS" if delta <= 0.1 else "FAIL", got, duration, delta))
    loud = measure_loudness(out)
    print("P: finished %+.2f LUFS integrated, %+.2f dBTP, sha256 %s"
          % (loud["input_i"], loud["input_tp"], sha256(out)))
    for cue_id in sorted({seg["cue"] for seg in segments}):
        path = cue_file(cues[cue_id])
        print("P: source %s %s sha256 %s" % (cue_id, cues[cue_id]["delivered_file"], sha256(path)))
        mirror = os.path.join(ROOT, "game", "datafiles", "streams", os.path.basename(path))
        if not os.path.isfile(mirror):
            continue
        try:
            same = sha256(mirror) == sha256(path)
        except OSError as error:
            # Another lane's build can hold the streams mirror open while it copies it. That lock says
            # nothing about this bed, which is already written, so it is reported rather than raised.
            print("Q: the mirror game/datafiles/streams/%s could not be read this run (%s), so the drift check "
                  "is not run for it" % (os.path.basename(path), error.__class__.__name__))
            continue
        print("P: %s mirror game/datafiles/streams/%s %s"
              % ("PASS" if same else "FAIL", os.path.basename(path),
                 "same bytes" if same else "DIFFERS from the delivered file"))
    return 0 if delta <= 0.1 else 1


if __name__ == "__main__":
    sys.exit(main())
