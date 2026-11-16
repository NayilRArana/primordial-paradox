#!/usr/bin/env python3
"""demo_voiceover.py: the narration track for the 180.00 s demo cut, spoken and placed per shot.

Why this file exists
    The judge panel of 2026-11-14 (knowledge/JUDGE-PANEL-2026-11-14.md, 35.0 of 100) judged six still frames
    and wrote that the demo had "no title menu or narrator explains the claims". Card t_5876de50 asks for a
    voice over explaining each claim. The words are knowledge/DEMO-SCRIPT.md section 12, one paragraph per
    shot; this tool is what turns them into audio and lays them on the cut's clock.

What it does, and what it refuses to do
    --synth    speaks each row with the machine's own offline SAPI5 voice and writes the six clips. The model
               id is not typed anywhere in the track: the words carry {judge}, and this tool substitutes the
               spoken form of tools/meta_client.py DEFAULT_MODELS["chat"], so a rename there changes what is
               said. Nothing is fetched from the network: the edge TTS endpoint answered 403 on this machine,
               and a voice that needs the network is a voice the offline build cannot carry.
    --check    measures every clip against its window and refuses one that is too long. A clip is sped up or
               clipped here? Never: the words are wrong and the words get shorter, so a change to the picture
               cannot silently ship a sentence that runs over the next shot.
    --track    lays the measured clips on a 180.00 s silent bed at the windows section 12 gives, and writes
               one 48 kHz stereo wav for the cut to mix under the game's own sound.

The words are the document's, not this file's
    `tests/test_demo_narration.py` reads section 12 of knowledge/DEMO-SCRIPT.md back against
    data/demo/narration.json, so the paragraph a booth reader sees and the paragraph this tool speaks are one
    string. This file types no line of narration.

Usage
    python tools\\demo_voiceover.py --status
    python tools\\demo_voiceover.py --synth
    python tools\\demo_voiceover.py --check
    python tools\\demo_voiceover.py --track output\\demo\\narration\\track.wav

Exit codes
    0  the status printed, the clips written, every clip fits its window, or the track was written
    1  a clip is missing, a window is empty, a clip does not fit, the voice is not installed, or ffmpeg failed
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

NARRATION_PATH = os.path.join(ROOT, "data", "demo", "narration.json")
META_CLIENT = os.path.join(TOOLS, "meta_client.py")

SAMPLE_RATE = 48000
TOTAL_S = 180.0
# How close to the end of its window a clip may run. A tenth of a second is the ffmpeg frame grid plus the
# room a breath needs; a clip that lands closer than this is refused, because the next shot's caption starts
# on the boundary and the two would talk over each other.
TAIL_MARGIN_S = 0.15
LONG_DASHES = ("\u2014", "\u2013", "\u2012", "\u2015")


class VoiceError(Exception):
    """The track cannot be built honestly: a clip is missing, long, or the voice is not installed."""


def load(path=None):
    path = path or NARRATION_PATH
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def rows(path=None):
    return load(path).get("rows") or []


def judge_model():
    """The talk model's id, from tools/meta_client.py DEFAULT_MODELS, never typed here."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("meta_client", META_CLIENT)
    if spec is None or spec.loader is None:
        raise VoiceError("cannot load %s for the judge's model id" % META_CLIENT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    models = getattr(module, "DEFAULT_MODELS", {})
    if not models.get("chat"):
        raise VoiceError("tools/meta_client.py DEFAULT_MODELS has no chat model to speak")
    return models["chat"]


def spoken_model(model_id):
    """The spoken form of a model id: muse-spark-1.3 is said "Muse Spark 1.3"."""
    parts = [part for part in re.split(r"[-_]", model_id) if part]
    return " ".join(part[:1].upper() + part[1:] for part in parts)


def spoken_words(row):
    """The row's words with {judge} spoken, and a refusal if a long dash slipped into the script."""
    words = str(row.get("words") or "").strip()
    if not words:
        raise VoiceError("%s has no words to speak" % row.get("shot"))
    words = words.replace("{judge}", spoken_model(judge_model()))
    for dash in LONG_DASHES:
        if dash in words:
            raise VoiceError("%s's words carry a long dash" % row.get("shot"))
    return words


def window(row):
    """The row's [start, end] window, refused when it is empty, reversed, or past the cut."""
    pair = row.get("window")
    if not isinstance(pair, list) or len(pair) != 2:
        raise VoiceError("%s's window is %r, not two seconds" % (row.get("shot"), pair))
    lo, hi = float(pair[0]), float(pair[1])
    if not 0.0 <= lo < hi <= TOTAL_S:
        raise VoiceError("%s's window %r is not inside the cut" % (row.get("shot"), pair))
    return lo, hi


def clip_path(row):
    return os.path.join(ROOT, row["file"])


def probe_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise VoiceError("ffprobe could not read %s: %s" % (path, result.stderr.strip()[-300:]))
    try:
        return float(result.stdout.strip())
    except ValueError:
        raise VoiceError("ffprobe returned no duration for %s" % path)


def synth_one(row, voice_name, rate, out):
    """Speak one row into a wav with the machine's SAPI5 voice. Windows only, and offline."""
    try:
        import win32com.client
    except ImportError:
        raise VoiceError("pywin32 is not installed, so the SAPI5 voice cannot be reached on this machine")
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    tokens = speaker.GetVoices()
    chosen = None
    for index in range(tokens.Count):
        token = tokens.Item(index)
        if token.GetDescription().strip() == voice_name.strip():
            chosen = token
            break
    if chosen is None:
        names = [tokens.Item(index).GetDescription() for index in range(tokens.Count)]
        raise VoiceError("the voice %r is not installed; this machine has %r" % (voice_name, names))
    speaker.Voice = chosen
    speaker.Rate = int(rate)
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    stream.Open(out, 3, False)      # 3 = SSFMCreateForWrite
    speaker.AudioOutputStream = stream
    speaker.Speak(spoken_words(row))
    stream.Close()
    return out


def synth(force=False):
    body = load()
    voice_name = body.get("voice") or ""
    rate = body.get("rate", 0)
    os.makedirs(os.path.join(ROOT, body.get("clip_dir") or "output/demo/narration"), exist_ok=True)
    written = []
    for row in body.get("rows") or []:
        window(row)     # refused here, before anything is spoken
        spoken_words(row)
        out = clip_path(row)
        if os.path.exists(out) and not force:
            written.append({"shot": row["shot"], "file": row["file"], "seconds": round(probe_duration(out), 3),
                            "reused": True})
            continue
        synth_one(row, voice_name, rate, out)
        written.append({"shot": row["shot"], "file": row["file"], "seconds": round(probe_duration(out), 3),
                        "reused": False})
    return written


def check():
    """Every clip exists and fits its window, as a list of measured rows. Refuses the first that does not."""
    problems = []
    measured = []
    for row in rows():
        lo, hi = window(row)
        room = hi - lo
        path = clip_path(row)
        if not os.path.exists(path):
            problems.append("%s: %s is missing, so run --synth" % (row["shot"], row["file"]))
            continue
        seconds = probe_duration(path)
        fits = seconds <= room - TAIL_MARGIN_S
        if not fits:
            problems.append("%s: the clip is %.2f s and its window %s holds %.2f s, so %s's words are too "
                            "long and the words get shorter" % (row["shot"], seconds, [lo, hi], room, row["shot"]))
        measured.append({"shot": row["shot"], "window": [lo, hi], "room_seconds": round(room, 3),
                         "clip_seconds": round(seconds, 3), "fits": fits, "file": row["file"],
                         "words": spoken_words(row)})
    if problems:
        raise VoiceError("; ".join(problems))
    return measured


def build_track(out, measured):
    """One 180.00 s 48 kHz stereo wav: each measured clip delayed to its window's start, silence elsewhere."""
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    inputs = ["-f", "lavfi", "-t", "%.3f" % TOTAL_S,
              "-i", "anullsrc=channel_layout=stereo:sample_rate=%d" % SAMPLE_RATE]
    for row in measured:
        inputs += ["-i", os.path.join(ROOT, row["file"])]
    graph = []
    labels = []
    for index, row in enumerate(measured):
        start_ms = int(round(row["window"][0] * 1000))
        label = "n%d" % index
        graph.append("[%d:a]aresample=%d,aformat=sample_fmts=s16:channel_layouts=stereo,"
                     "adelay=%d|%d[%s]" % (index + 1, SAMPLE_RATE, start_ms, start_ms, label))
        labels.append("[%s]" % label)
    graph.append("[0:a]%samix=inputs=%d:duration=first:normalize=0[aout]"
                 % ("".join(labels), len(measured) + 1))
    command = ["ffmpeg", "-hide_banner", "-v", "error", "-y", *inputs,
               "-filter_complex", ";".join(graph), "-map", "[aout]",
               "-ac", "2", "-ar", str(SAMPLE_RATE), "-t", "%.3f" % TOTAL_S, out]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise VoiceError("ffmpeg could not build the narration track: %s" % result.stderr.strip()[-800:])
    seconds = probe_duration(out)
    if abs(seconds - TOTAL_S) > 0.05:
        raise VoiceError("the narration track is %.3f s, not 180.00" % seconds)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="speak and place the demo's narration track")
    parser.add_argument("--status", action="store_true", help="print the rows, their windows and whether a clip exists")
    parser.add_argument("--synth", action="store_true", help="speak every row into its clip file")
    parser.add_argument("--check", action="store_true", help="measure every clip against its window")
    parser.add_argument("--track", help="write the 180.00 s narration track to this wav")
    parser.add_argument("--force", action="store_true", help="--synth again over clips that already exist")
    args = parser.parse_args(argv)

    try:
        if args.status:
            body = load()
            print(json.dumps({
                "source": body.get("source"),
                "voice": body.get("voice"),
                "judge": judge_model(),
                "judge_spoken": spoken_model(judge_model()),
                "rows": [{"shot": row["shot"], "window": window(row), "file": row["file"],
                          "exists": os.path.exists(clip_path(row)),
                          "words": spoken_words(row)} for row in rows()],
            }, indent=1))
            return 0
        if args.synth:
            for item in synth(force=args.force):
                print("%s  %s  %.2f s%s" % (item["shot"], item["file"], item["seconds"],
                                            "  (reused)" if item["reused"] else ""))
            return 0
        if args.check:
            for row in check():
                print("%s  window %s  room %.2f s  clip %.2f s  %s"
                      % (row["shot"], row["window"], row["room_seconds"], row["clip_seconds"],
                         "PASS" if row["fits"] else "FAIL"))
            return 0
        if args.track:
            measured = check()
            build_track(args.track, measured)
            print("PASS  %s written, %d clips, %.3f s" % (args.track, len(measured), probe_duration(args.track)))
            return 0
    except VoiceError as error:
        print("REFUSED  %s" % error)
        return 1
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
