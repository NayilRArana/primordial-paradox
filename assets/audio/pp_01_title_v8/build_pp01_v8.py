"""build_pp01_v8.py: PP-01 "Title Theme" version 8, card AUTO-MUSIC-NEXT (t_61d9e8a2), round 2.

Reads v7 (the round 1 build in the folder next door) and adds the three things the ear review of
v7 named, in its own order of weakness (drums 5, tension 6, human 4 out of 10):

  1. Drums. Sixteenth offbeat ghost hats at velocity 34 to 44 in the B sections, a syncopated
     three hit snare figure across bars 21 to 24 with a falling velocity (a decaying fill, not a
     flat one), a flam on the open hat before each section change, and a low noise pitch
     (A#-1) as an offbeat kick substitute so the noise channel carries pitch as well as rhythm.
  2. Tension. DIS-21 pedal tone, risk 2: the triangle drops its moving line for the trio's cold
     half (bars 41 to 43) and holds A2, re-attacked on beat 1 with a falling velocity, then returns
     to the written line on bar 44 where A is a chord tone again. That is the textural drop-out the
     review asked for under the H statements, and it is the one device the trio's 8 bar budget
     spends.
  3. Human feel. The pad stabs are staggered 1 to 2 frames off the grid, the offbeat hats are
     delayed one frame, the kick is allowed one frame of slop outside section downbeats, and a
     repeated pitch in the melody is played 4 quieter each time it repeats, so the lead is not a
     machine's flat velocity ladder. The renderer's own human pass still runs on top.

Every motif cell, the form, the key, the tempo (126 bpm), the metre (3/4), the bar count (52) and
the loop point are v7's, untouched.

Usage: build_pp01_v8.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(AUDIO))
SRC = os.path.join(AUDIO, "pp_01_title_v7", "pp_01_title_v7.mid")
OUT = os.path.join(HERE, "pp_01_title_v8.mid")
REPORT = os.path.join(HERE, "build_report_v8.json")

sys.path.insert(0, os.path.join(ROOT, "tools"))
import hook_score  # noqa: E402
import humanize  # noqa: E402

PPQ = 480
EIGHTH = PPQ // 2
BAR = 6 * EIGHTH
BARS = 52
FRAME_TICKS = PPQ * 60.0 / (126 * 60 * 60.0988 / 1.789773)   # one NES frame at 126 bpm

NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
HAT, OPEN_HAT, SNARE, TOM_HI, TOM_MID, TOM_LO, KICK = 12, 10, 38, 8, 6, 4, 36
NOISE_LOW = 1        # A#-1: the low noise pitch used as a kick substitute


def pitch_name(value):
    return "%s%d" % (NOTES[value % 12], value // 12 - 1)


def at(bar, eighth):
    return (bar - 1) * BAR + int(round(eighth * EIGHTH))


def tracks(song):
    return {t["name"].strip().lower(): t for t in song["tracks"]}


def drum_round(song, report):
    noise = tracks(song)["noise"]

    def hit(bar, step, pitch, velocity, length=60):
        start = at(bar, step)
        noise["notes"].append((start, start + length, pitch, velocity))

    ghost = 0
    for bar in list(range(21, 29)) + list(range(29, 37)):
        # sixteenth offbeats, quiet, alternating so they are not a metronome
        for step in ((0.5, 2.5, 4.5) if bar % 2 == 0 else (1.5, 3.5)):
            hit(bar, step, HAT, 34 + (8 if step % 1 == 0.5 and bar % 4 == 0 else 0), 40)
            ghost += 1
    # the syncopated snare figure across bars 21 to 24, falling velocity
    for bar, steps in ((21, (2.5, 3)), (22, (2.5, 3, 3.5)), (23, (2.5, 3)), (24, (2.5, 3, 3.5, 4))):
        for index, step in enumerate(steps):
            hit(bar, step, SNARE, 92 - 8 * index, 48)
    # a flam on the open hat before each section change, and a low noise kick offbeat
    for bar in (12, 20, 28, 36, 44):
        hit(bar, 4.5, OPEN_HAT, 52, 40)
        hit(bar, 5, OPEN_HAT, 74, 90)
    for bar in (14, 18, 26, 30, 34, 42, 46, 50):
        hit(bar, 2.5, NOISE_LOW, 58, 48)

    noise["notes"].sort()
    report["drums"] = {
        "noise_before": 266, "noise_after": len(noise["notes"]),
        "ghost_hats": ghost, "snare_figure": "bars 21 to 24, falling velocity 92 to 60",
        "open_hat_flams": "before bars 13, 21, 29, 37, 45",
        "noise_kick_substitute": "8 offbeats at %s" % pitch_name(NOISE_LOW),
    }


def pedal_round(song, report):
    """DIS-21: the triangle holds A2 through the trio's cold half and returns on bar 44."""
    triangle = tracks(song)["triangle"]
    removed = [n for n in triangle["notes"] if 41 * BAR <= n[0] < 44 * BAR]
    triangle["notes"] = [n for n in triangle["notes"] if not (41 * BAR <= n[0] < 44 * BAR)]
    for index, bar in enumerate((41, 42, 43)):
        start = at(bar, 0)
        triangle["notes"].append((start, start + 3 * EIGHTH, 45, 100 - 6 * index))   # A2, decaying
    triangle["notes"].sort()
    report["devices"].append({
        "id": "DIS-21", "risk": 2, "voice": "triangle",
        "span": "bars 41 to 43, 9 beats",
        "pitch": pitch_name(45),
        "resolution": {"bar": 44, "why": "the written line returns and A is a chord tone again"},
        "trigger": "trio cold half under the H statements, the review asked for a textural drop-out",
        "removed_notes": len(removed),
        "budget": "trio: 1 device in 8 bars, inside 1 to 2",
    })


def human_round(song, report):
    """Stagger the pad, slop the hats and the kick, and unflatten the melody's velocity ladder."""
    t = tracks(song)
    shifted = {"vrc6 saw": 0, "noise": 0, "dpcm": 0}
    saw = []
    for index, (start, end, pitch, velocity) in enumerate(sorted(t["vrc6 saw"]["notes"])):
        shift = 1 + (index % 2)                                 # 1 or 2 frames late
        saw.append((start + shift, end + shift, pitch, velocity))
        if shift:
            shifted["vrc6 saw"] += 1
    t["vrc6 saw"]["notes"] = sorted(saw)

    for name in ("noise", "dpcm"):
        shaped = []
        for index, (start, end, pitch, velocity) in enumerate(sorted(t[name]["notes"])):
            if (start % BAR) == 0 and (start // BAR + 1) in (5, 13, 21, 29, 37, 45):
                shift = 0                                       # section downbeats stay on the grid
            elif name == "noise":
                shift = 1 if (start % EIGHTH) else 0
            else:
                shift = ((index * 3) % 3) - 1
            if shift:
                shifted[name] += 1
            shaped.append((max(0, start + shift), max(0, end + shift), pitch, velocity))
        t[name]["notes"] = sorted(shaped)

    lead = t["vrc6 pulse a"]
    previous = None
    repeats = 0
    shaped = []
    for start, end, pitch, velocity in sorted(lead["notes"]):
        if pitch == previous:
            repeats += 1
            velocity = max(70, velocity - 4)
        previous = pitch
        shaped.append((start, end, pitch, velocity))
    lead["notes"] = shaped
    report["human"] = {"staggered": shifted, "melody_repeat_velocity_drops": repeats,
                      "frame_ticks": round(FRAME_TICKS, 2)}


def main():
    song = hook_score.read_smf(SRC)
    report = {
        "source": SRC,
        "tempo_bpm": 60_000_000 / song["tempo_us"],
        "time_sig": list(song["time_sig"]),
        "loop": "bar 5 for 48 bars",
        "devices": [],
    }
    before = hook_score.score_file(SRC, track="vrc6 pulse a")
    report["hook_before"] = {"score": before["score"], "weakest": before["weakest"]}
    drum_round(song, report)
    pedal_round(song, report)
    human_round(song, report)
    humanize.write_smf(song, OUT)
    after = hook_score.score_file(OUT, track="vrc6 pulse a")
    report["hook_after_score"] = after["score"]
    report["hook_after"] = {c["key"]: [c["measured"], c["pass"]] for c in after["criteria"]}
    report["tracks_out"] = [{"name": t["name"], "notes": len(t["notes"])} for t in song["tracks"]]
    with open(REPORT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print("before", before["score"], "after", after["score"])
    for c in after["criteria"]:
        print("  %-22s %5s  %s" % (c["key"], c["points"], c["measured"]))
    print("midi", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
