#!/usr/bin/env python3
"""audio_route_report.py: the game's log plus the meter's CSV, as one table of what the player would hear, scene by scene.

Card MUSIC-REAL (2026-11-02). Inputs:
  - the game log of a run started with PP_AUDIO_LOG set (build\\demo-game.log for tools\\play_demo.py): one line a second,
    "PP audio status: mode=<..> room=<..> cue=<id> instance=<n> playing=<0|1> gain=<..> master=<..> paused=<0|1>";
  - the meter CSV from tools\\audio_meter.py (the Windows session peak of PrimordialParadox.exe, every 500 ms).
Clocks: when the meter ran with --log, its <name>_log.csv carries each game log line stamped with the meter's own clock and
this tool uses it (resolution 500 ms). Without it, the status lines are the clock: they are written once a second, the last
one is taken to be written at the last meter sample, and the others sit one second apart before it. That estimate can be a
second or two off at the ends of a segment, and a segment's verdict reads the whole segment, so it does not move a verdict.

A segment is one run of status lines with the same (mode, room, cue); the title and the crawl are one segment each only if the
cue or room changes, so the table reads as the player's route. Columns: scene or room (with the fight id when a "PP audio:
fight" line named one), cue, playing (yes when the engine reported the instance playing, unpaused, on most of the
segment's lines), peak dB (the highest meter sample in the segment), seconds above -50 dBFS, verdict.
Verdicts:
  AUDIBLE     the meter was above -50 dBFS for at least 5 seconds in total inside the segment (the bar the card sets);
  SILENT      the game says a cue is playing and the meter does not: the defect this tool exists to catch;
  NO_CUE      the game itself holds no music in this segment (cue=none);
  TOO_SHORT   the segment lasted under 5 seconds, so the bar cannot be met and nothing is claimed;
  NO_METER    the segment has no meter samples (the meter was not running, or the game had no audio session).
The exit code is 0 when no segment is SILENT or NO_CUE and at least one is AUDIBLE, else 1; 2 for unreadable input.

Usage:
    python tools\\audio_route_report.py --log build\\demo-game.log --meter output\\music_real_2026-11-02\\meter.csv
    python tools\\audio_route_report.py --log build\\demo-game.log --meter meter.csv --events meter_log.csv --out report.md
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys

BAR_DB = -50.0
BAR_SECONDS = 5.0
STATUS = re.compile(
    r"PP audio status: mode=(?P<mode>\S+) room=(?P<room>\S+) cue=(?P<cue>\S+) instance=(?P<inst>-?\d+) "
    r"playing=(?P<playing>\d) gain=(?P<gain>\S+) master=(?P<master>\S+) paused=(?P<paused>\d)")
FIGHT = re.compile(r"PP audio: fight (?P<id>\S*) asked")


def read_meter(path):
    """[(epoch, session_found, dbfs)] from the meter CSV."""
    rows = []
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            try:
                rows.append((float(row["epoch_s"]), int(row["session"]), float(row["peak_dbfs"])))
            except (KeyError, ValueError):
                continue
    return rows


def read_events(path):
    """[(epoch, line)] from the meter's --log sidecar."""
    rows = []
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            try:
                rows.append((float(row["epoch_s"]), row["line"]))
            except (KeyError, ValueError):
                continue
    return rows


def read_log(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return [line.rstrip("\r\n") for line in handle]


def status_points(log_lines, events, meter):
    """[(time, fields dict, fight id)] for every status line, on the meter's clock."""
    if events:
        stamped = [(t, line) for t, line in events]
    else:
        lines = [line for line in log_lines if "PP audio status:" in line or "PP audio: fight" in line]
        count = sum(1 for line in lines if "PP audio status:" in line)
        end = meter[-1][0] if meter else 0.0
        stamped = []
        seen = 0
        for line in lines:
            if "PP audio status:" in line:
                stamped.append((end - (count - 1 - seen) * 1.0, line))
                seen += 1
            else:
                stamped.append((end - (count - seen) * 1.0, line))
    points = []
    fight = ""
    for moment, line in stamped:
        found = FIGHT.search(line)
        if found:
            fight = found.group("id")
            continue
        match = STATUS.search(line)
        if not match:
            continue
        fields = match.groupdict()
        if fields["mode"] != "battle":
            fight = ""
        points.append((moment, fields, fight if fields["mode"] == "battle" else ""))
    return points


def segments(points):
    """Runs of equal (mode, room, cue): [{key, start, end, lines, playing_lines}]."""
    out = []
    for moment, fields, fight in points:
        label = fields["room"] + (" / fight " + fight if fight else "")
        key = (fields["mode"], label, fields["cue"])
        live = fields["playing"] == "1" and fields["paused"] == "0" and int(fields["inst"]) > -1
        if out and out[-1]["key"] == key:
            out[-1]["end"] = moment
            out[-1]["lines"] += 1
            out[-1]["playing_lines"] += 1 if live else 0
        else:
            out.append({"key": key, "start": moment, "end": moment, "lines": 1, "playing_lines": 1 if live else 0})
    # A status line covers the second after it, so a segment lasts until the next one starts.
    for index, seg in enumerate(out):
        seg["stop"] = out[index + 1]["start"] if index + 1 < len(out) else seg["end"] + 1.0
    return out


def judge(seg, meter):
    samples = [(t, found, db) for t, found, db in meter if seg["start"] <= t < seg["stop"]]
    duration = seg["stop"] - seg["start"]
    mode, room, cue = seg["key"]
    playing = seg["playing_lines"] * 2 > seg["lines"]
    peak = max((db for _t, found, db in samples if found), default=None)
    above = 0.5 * sum(1 for _t, found, db in samples if found and db > BAR_DB)
    if cue == "none":
        verdict = "NO_CUE"
    elif duration < BAR_SECONDS:
        verdict = "TOO_SHORT"
    elif not any(found for _t, found, _db in samples):
        verdict = "NO_METER"
    elif above >= BAR_SECONDS:
        verdict = "AUDIBLE"
    else:
        verdict = "SILENT"
    return {"room": room, "mode": mode, "cue": cue, "playing": "yes" if playing else "no", "peak": peak,
            "above": above, "duration": duration, "verdict": verdict}


def table(rows):
    head = "| scene or room | mode | cue | playing | peak dBFS | s above -50 | length s | verdict |"
    rule = "|---|---|---|---|---|---|---|---|"
    body = []
    for row in rows:
        peak = "n/a" if row["peak"] is None else "%.1f" % row["peak"]
        body.append("| %s | %s | %s | %s | %s | %.1f | %.0f | %s |" % (
            row["room"], row["mode"], row["cue"], row["playing"], peak, row["above"], row["duration"], row["verdict"]))
    return "\n".join([head, rule] + body)


def build(log_path, meter_path, events_path=None):
    meter = read_meter(meter_path)
    events = read_events(events_path) if events_path else None
    if events is None:
        guess = os.path.splitext(meter_path)[0] + "_log.csv"
        if os.path.isfile(guess):
            events = read_events(guess)
    points = status_points(read_log(log_path), events, meter)
    return [judge(seg, meter) for seg in segments(points)], bool(events)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Scene by scene audibility table from a game log and a meter CSV")
    parser.add_argument("--log", required=True)
    parser.add_argument("--meter", required=True)
    parser.add_argument("--events", default=None)
    parser.add_argument("--out", default=None, help="also write the table here")
    args = parser.parse_args(argv)
    try:
        rows, stamped = build(args.log, args.meter, args.events)
    except OSError as error:
        print("audio_route_report: cannot read an input: %s" % error)
        return 2
    if not rows:
        print("audio_route_report: the log has no 'PP audio status' lines; was the game started with PP_AUDIO_LOG set?")
        return 2
    text = table(rows)
    clock = "log lines stamped by the meter (500 ms)" if stamped else "estimated from the status lines (1 s apart, ends at the last meter sample)"
    text += "\n\nclock: %s; bar: above %.0f dBFS for %.0f s in total inside the segment\n" % (clock, BAR_DB, BAR_SECONDS)
    print(text)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
    verdicts = [row["verdict"] for row in rows]
    bad = any(v in ("SILENT", "NO_CUE") for v in verdicts)
    return 0 if ("AUDIBLE" in verdicts and not bad) else 1


if __name__ == "__main__":
    sys.exit(main())
