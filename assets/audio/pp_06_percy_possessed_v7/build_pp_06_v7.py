"""build_pp_06_v7.py: PP-06 take G, the 48 bar form the cue row and the gamedev spec name.

Card t_2adbbc6e (AUTO-MUSIC-NEXT, musician lane), 2026-11-16.

Input is take F, assets/audio/pp_06_percy_possessed_v6/pp_06_percy_possessed_v6.mid, which is
32 bars (38.4 s). The shipped stream, assets/audio/pp_06_percy_possessed/pp_06_percy_possessed.ogg,
is 48 bars (57.6 s) and data/audio.json records that 48 bar form for the cue ("E minor then G minor,
3/4, 150 bpm, 48 bars (57.6 s)"). Every take since D shortened the cue to 32 bars, which is why none
of them can be adopted: the hook meter pays loop length for 8, 16 or 32 bars, and the spec asks for 48.

This script keeps take F's music and appends one of three 16 bar reprises, so the cue is 48 bars again
and the meter still has a real loop to score (48 is a multiple of 16, so loop length earns half).
Nothing is composed from outside: every note written here is a note take F already plays.

Three candidates are written and scored, and the best is kept:
    _cand_open    bars 1 to 16 again at the end (rounded form)
    _cand_second  bars 17 to 32 again at the end (continued development)
    _cand_varied  bars 1 to 16 again, with the reprise's last melody note lifted a step

Usage: python build_pp_06_v7.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "tools"))

import hook_score  # noqa: E402
import humanize  # noqa: E402

SRC = os.path.join(REPO, "assets", "audio", "pp_06_percy_possessed_v6",
                   "pp_06_percy_possessed_v6.mid")
SOURCE_BARS = 32
ADD_BARS = 16


def shift_copy(song, first_bar, last_bar, add_bars, pitch_lift=None, melody_track="vrc6 pulse a"):
    bar_ticks = song["division"] * song["time_sig"][0]
    lo = first_bar * bar_ticks
    hi = last_bar * bar_ticks
    out = {"division": song["division"], "tempo_us": song["tempo_us"],
           "time_sig": song["time_sig"], "tracks": []}
    for track in song["tracks"]:
        notes = list(track["notes"])
        added = []
        for start, end, pitch, velocity in track["notes"]:
            if lo <= start < hi:
                new_pitch = pitch
                if pitch_lift and track["name"] == melody_track:
                    new_pitch = pitch + pitch_lift
                added.append((start + add_bars * bar_ticks, end + add_bars * bar_ticks,
                              new_pitch, velocity))
        cc = {}
        for controller, events in track["cc"].items():
            kept = list(events)
            kept += [(tick + add_bars * bar_ticks, value) for tick, value in events
                     if lo <= tick < hi]
            cc[controller] = sorted(kept)
        out["tracks"].append({"name": track["name"], "notes": notes + added, "cc": cc})
    return out


def main():
    song = hook_score.read_smf(SRC)
    candidates = {
        "_cand_open": (0, ADD_BARS, None),
        "_cand_second": (ADD_BARS, SOURCE_BARS, None),
        "_cand_varied": (0, ADD_BARS, 2),
    }
    scored = {}
    for name, (first, last, lift) in candidates.items():
        built = shift_copy(song, first, last, SOURCE_BARS, pitch_lift=lift)
        path = os.path.join(HERE, name + ".mid")
        humanize.write_smf(built, path)
        report = hook_score.score_file(path)
        scored[name] = {"path": path, "score": report["score"], "bars": report["bars"],
                        "weakest": report["weakest"]}
        print(name, "score", report["score"], "bars", report["bars"],
              "weakest", report["weakest"]["key"], round(report["weakest"]["points"], 2))
    best = max(scored.items(), key=lambda item: item[1]["score"])
    print("best:", best[0], best[1]["score"])
    with open(os.path.join(HERE, "candidates_v7.json"), "w", encoding="utf-8") as handle:
        json.dump({"source": SRC, "chosen": best[0], "candidates": scored}, handle, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
