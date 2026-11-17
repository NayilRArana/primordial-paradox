#!/usr/bin/env python3
"""demo_clip_event_log.py: give a cut clip the event log of the run it was cut from (card t_b24aa225).

Why this file exists
    The 180 s cut's S5 (78.000 to 110.000 s) is `output/demo_2026-11-04/morgan_talk.mp4`, and that file is
    not a recording: it is a clip assembled by the 2026-11-04 session's own recorder script
    (`output/demo_2026-11-04/recorder/demo_cut.py`, its CLIPS["morgan_talk"] row) out of the `story_good`
    run. Four segments of that run, one of them sped to 1.5x for the picture, concatenated.

    So `morgan_talk.events.json` has never existed, and the musician lane's events layer
    (tools/demo_music_bed.py, JUDGE-PANEL-2026-11-17 fix 3) reads a log by the source video's own name. That
    lane placed no text blip in S5 and would not invent one, which is correct: the stamps are not missing,
    they are in `story_good.events.json`, in the run's clock rather than the clip's.

    This tool moves them. It does not decide anything: the segment table comes from the recorder script that
    made the clip, the stamps and the cue names come from the run's log verbatim, and the only arithmetic is
    the recorder's own, reproduced below and checked against the clip on disk before anything is written.

The two clocks, and why this is not a stretch
    `make_clip` in the recorder trims the picture from `a + LAG` to `b + LAG` and plays it at `sp`, so a
    segment lasts `(b - a) / sp` seconds on screen. The sound is never time stretched: for the same segment
    it takes the LAST `(b - a) / sp` seconds of the run's audio, at normal speed (its `audio_window`). The
    clip's own sound therefore begins at run time `b - (b - a) / sp`, not at `a`, and a log stamp inside a
    sped segment but before that point was heard by nobody: the clip dropped that stretch of sound while
    keeping the picture. Those rows are counted and reported, not invented a place.

        clip time = (sum of the segment durations before this one) + (stamp - audio window start)

    LAG cancels out of it: the recorder adds the same lag to the picture trim and the audio trim, so the two
    stay together inside a clip whatever it measured on the night.

    At speed 1.0 the audio window is the segment itself and the rule is the cut's own: a stamp 0.40 s into
    the segment lands 0.40 s into that segment's window on the clip's clock.

What the file says about itself
    The body keeps the recorder's own shape (`name`, `events` as `[second, line]` pairs, `audio_fmt`,
    `peak`) so a reader that knows the format needs no change, and it is written without a BOM and with the
    stamps at the recorder's two decimal places. It also carries a `derived` block naming the run's log, the
    segment table, the rule and the rows the clip's sound does not hold, so no reader can mistake this for a
    log the game wrote live. A live log has no `derived` key.

What it refuses
    A clip whose computed length disagrees with the file on disk (the table and the clip must be the same
    take), a run whose log is not beside it, a clip the recorder's table does not name, and a table row with
    a speed of zero. It writes nothing when it refuses.

Usage
    python tools\\demo_clip_event_log.py --clip morgan_talk          write <clip>.events.json beside the clip
    python tools\\demo_clip_event_log.py --clip morgan_talk --check  write nothing: exit 1 if it would change
    python tools\\demo_clip_event_log.py --all --check               every clip the table names

Exit codes
    0  the log written, the file on disk already right, or the plan printed
    1  a refusal, or --check found a file that is missing or stale
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPTURES = os.path.join(ROOT, "output", "demo_2026-11-04")
DEFAULT_RECORDER = os.path.join(CAPTURES, "recorder", "demo_cut.py")

# The clip's length on disk against the sum of its segments. The recorder rounds every segment to whole
# frames at 60 fps, so a four segment clip can run a frame or two long (morgan_talk: 34.134 s computed,
# 34.158 s on disk). Anything past this is a different table, not rounding.
CLIP_TOLERANCE_S = 0.15

RECORDER_KEYS = ("name", "events", "audio_fmt", "peak")


class ClipLogError(Exception):
    """The log cannot be derived honestly: the table, the clip and the run's log do not describe one take."""


def load_table(recorder):
    """The recorder's own CLIPS table and its audio_window rule, imported from the script that made the clip.

    The table is the clip's authority. Typing it here again would let the two disagree, and the arithmetic
    below would then move stamps through a cut nobody made.
    """
    if not os.path.exists(recorder):
        raise ClipLogError("the recorder script is not on disk: %s" % recorder)
    spec = importlib.util.spec_from_file_location("pp_demo_cut_recorder", recorder)
    if spec is None or spec.loader is None:
        raise ClipLogError("cannot import %s as a module" % recorder)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("CLIPS", "audio_window"):
        if not hasattr(module, name):
            raise ClipLogError("%s carries no %s, so it is not the recorder this tool reads" % (recorder, name))
    return module


def segment_rows(module, segments):
    """One row per segment: the run window, the speed, and where its picture and its sound land.

    `audio` is the run window the clip's sound actually holds, straight from the recorder's own
    `audio_window`. `clip` is the clock the segment begins at on the clip, which is the sum of the
    durations before it: picture and sound last the same time, so one clock serves both.
    """
    rows = []
    at = 0.0
    for index, (start, end, speed) in enumerate(segments):
        if speed <= 0:
            raise ClipLogError("segment %d plays at speed %s: the clip has no length for it" % (index, speed))
        if end <= start:
            raise ClipLogError("segment %d runs %.3f to %.3f: it has no length" % (index, start, end))
        duration = (end - start) / speed
        audio_start, audio_end = module.audio_window(start, end, speed)
        rows.append({"index": index, "start": round(start, 3), "end": round(end, 3), "speed": speed,
                     "duration": round(duration, 4), "audio": [round(audio_start, 4), round(audio_end, 4)],
                     "clip": [round(at, 4), round(at + duration, 4)]})
        at += duration
    return rows, at


def read_log(path):
    """Every stamped line the run's log holds, in its own order, as (second, line)."""
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            body = json.load(handle)
    except (OSError, ValueError) as error:
        raise ClipLogError("cannot read the run's log %s: %s" % (path, error))
    rows = []
    for item in body.get("events") or []:
        if not isinstance(item, list) or len(item) < 2:
            continue
        try:
            stamp = float(item[0])
        except (TypeError, ValueError):
            continue
        rows.append((stamp, str(item[1])))
    return rows


def remap(rows, segments):
    """The run's log in the clip's clock: (kept, dropped, outside).

    A row is kept when its stamp falls in a segment's audio window, and lands at that segment's clock plus
    its distance into the window. `dropped` counts the rows inside a segment but outside its audio window,
    which is the stretch of sound the recorder left behind (only a sped segment has one). `outside` counts
    the rows in no segment at all: another part of the run, which this clip does not show.
    """
    kept, dropped, outside = [], [], 0
    for stamp, line in rows:
        placed = False
        for row in segments:
            if row["start"] <= stamp < row["end"]:
                placed = True
                low, high = row["audio"]
                if low <= stamp < high:
                    kept.append((round(row["clip"][0] + (stamp - low), 2), line, stamp, row["index"]))
                elif stamp < low:
                    dropped.append((stamp, line, row["index"]))
                break
        if not placed:
            outside += 1
    return kept, dropped, outside


def clip_seconds(path):
    """The clip's own length, from ffprobe. The file is the take; the table only says how it was cut."""
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise ClipLogError("ffprobe cannot read %s: %s" % (path, result.stderr.strip()[-300:]))
    try:
        return float(result.stdout.strip().splitlines()[0])
    except (IndexError, ValueError):
        raise ClipLogError("ffprobe printed no duration for %s" % path)


def build(module, name, folder, seconds=None):
    """The log body for one clip, or ClipLogError when the table, the clip and the log disagree."""
    table = getattr(module, "CLIPS")
    if name not in table:
        raise ClipLogError("%s names no clip %r" % (os.path.basename(DEFAULT_RECORDER), name))
    run, segments = table[name]
    clip_path = os.path.join(folder, name + ".mp4")
    if not os.path.exists(clip_path):
        raise ClipLogError("%s is not on disk, so there is no clip to give a clock" % clip_path)
    log_path = os.path.join(folder, run + ".events.json")
    if not os.path.exists(log_path):
        raise ClipLogError("%s is not on disk: the run that was cut has kept no log to move" % log_path)
    rows, computed = segment_rows(module, segments)
    measured = clip_seconds(clip_path) if seconds is None else seconds
    if abs(measured - computed) > CLIP_TOLERANCE_S:
        raise ClipLogError("%s runs %.3f s but the table's segments add to %.3f s: the table is not this clip"
                           % (clip_path, measured, computed))
    kept, dropped, outside = remap(read_log(log_path), rows)
    if not kept:
        raise ClipLogError("%s holds none of %s's log lines inside its own sound" % (name, run))
    body = {"name": name, "events": [[at, line] for at, line, _stamp, _index in kept],
            "audio_fmt": None, "peak": None,
            "derived": {
                "why": "this clip was cut from %s, not recorded: its log is that run's log in the clip's clock" % run,
                "source_log": os.path.relpath(log_path, ROOT) if log_path.startswith(ROOT) else log_path,
                "source_run": run,
                "recorder": os.path.relpath(os.path.abspath(module.__file__), ROOT),
                "rule": "clip time = the segment's own clock + (stamp - audio window start); the sound is the"
                        " segment's last (end - start) / speed seconds at normal speed, so a sped segment's"
                        " earlier stamps are heard by nobody and are dropped",
                "segments": rows,
                "kept": len(kept), "dropped_no_sound": len(dropped), "outside_the_clip": outside,
                "dropped_stamps": [{"run_s": round(stamp, 3), "segment": index, "line": line[:120]}
                                   for stamp, line, index in dropped[:40]],
                "clip_seconds": round(measured, 3), "segments_total_s": round(computed, 4)}
            }
    return body, os.path.join(folder, name + ".events.json")


def same(disk, body):
    """Whether the file on disk already says what this run would write, ignoring the key order."""
    if disk.get("events") != body.get("events"):
        return False
    for key in RECORDER_KEYS:
        if key == "events":
            continue
        if disk.get(key) != body.get(key):
            return False
    return disk.get("derived") == body.get("derived")


def main(argv=None):
    parser = argparse.ArgumentParser(description="give a cut clip the event log of the run it was cut from")
    parser.add_argument("--clip", help="the clip's name in the recorder's table, e.g. morgan_talk")
    parser.add_argument("--all", action="store_true", help="every clip the recorder's table names")
    parser.add_argument("--check", action="store_true", help="write nothing: exit 1 when the file is stale")
    parser.add_argument("--plan", action="store_true", help="print the derived log and write nothing")
    parser.add_argument("--folder", default=CAPTURES, help="the capture folder holding the clips and their logs")
    parser.add_argument("--recorder", default=DEFAULT_RECORDER, help="the recorder script that made the clips")
    args = parser.parse_args(argv)
    try:
        module = load_table(args.recorder)
        names = list(getattr(module, "CLIPS")) if args.all else ([args.clip] if args.clip else [])
        if not names:
            parser.print_help()
            return 1
        status = 0
        for name in names:
            try:
                body, path = build(module, name, args.folder)
            except ClipLogError as error:
                # --all walks a table that also holds clips whose run kept no log; --clip is a refusal.
                if args.all and not args.clip:
                    print("SKIP  %s: %s" % (name, error))
                    continue
                raise
            if args.plan:
                print(json.dumps(body, indent=1))
                continue
            on_disk = None
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as handle:
                    on_disk = json.load(handle)
            if args.check:
                if on_disk is None:
                    print("STALE  %s is missing: %d rows belong in it" % (path, len(body["events"])))
                    status = 1
                elif not same(on_disk, body):
                    print("STALE  %s does not match the clip's segments and the run's log" % path)
                    status = 1
                else:
                    print("PASS  %s is current: %d rows, %d dropped (no sound in the clip)"
                          % (path, len(body["events"]), body["derived"]["dropped_no_sound"]))
                continue
            if on_disk is not None and same(on_disk, body):
                print("PASS  %s already says this: %d rows, %d dropped" % (
                    path, len(body["events"]), body["derived"]["dropped_no_sound"]))
                continue
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(body, handle, indent=1)
            print("PASS  %s written, %d rows from %s, %d dropped (the clip's sound does not hold them),"
                  " %.3f s clip"
                  % (path, len(body["events"]), body["derived"]["source_log"],
                     body["derived"]["dropped_no_sound"], body["derived"]["clip_seconds"]))
        return status
    except ClipLogError as error:
        print("REFUSED  %s" % error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
