"""build_pp01_v7.py: PP-01 "Title Theme" version 7, card AUTO-MUSIC-NEXT (t_61d9e8a2).

Source is v6 (`assets/audio/pp_01_title_v6/pp_01_title_v6.mid`), the newest build of this cue and
the floor of the hook meter at 83 of 100. Nothing in v6 is edited in place: this script reads it
and writes a new file in this folder.

What v7 adds, and nothing else. The lead's motif cells (K, K2, Z, P, H, W) are v6's notes, untouched,
so every leitmotif statement still sounds where it did:

  1. DIS-09 anticipation, risk 1, at the end of B (bar 36): the last eighth becomes G4, and G is a
     chord tone of the Em that arrives on the next downbeat, so the device resolves by harmony, not
     by a pitch change. One device in the B section, inside the 1 to 2 per 8 bars budget of
     knowledge/MUSIC-DISSONANCE.md section 4.
  2. DIS-04 suspension 4 to 3, risk 1, at the trio's Em to B7 change (bars 38 to 39): vrc6 pulse b,
     which is silent through the trio in v6, holds E5 (a chord tone of the Em bar) across the bar
     line into the B7 bar, where E is the fourth above B, and resolves down a semitone to D#5 on
     beat 2. The lead keeps its own P statement; the resolution pitch is the score's own D#5.
  3. The kit gains a 16 bar rung on top of v6's 2, 4 and 8 bar rungs: bars 16 and 32 drop the hats
     for one bar and keep a half time kick and snare, so the ear hears a change at every second
     8 bar phrase. Ghost snares (velocity 38 to 46) go under the B section's backbeat, and the four
     bars before a section change end on a three hit tom fill instead of a single open hat.
  4. The human pass is the same one v6 used (render_chip --humanize, seed 20261021), so the
     comparison between v6 and v7 is the notes, not the amount of humanization.

Key, tempo, metre, bar count, loop point and every other voice are v6's: A minor, 3/4, 126 bpm,
52 bars, loop from bar 5 to bar 52.

Usage: build_pp01_v7.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(AUDIO))
SRC = os.path.join(AUDIO, "pp_01_title_v6", "pp_01_title_v6.mid")
OUT = os.path.join(HERE, "pp_01_title_v7.mid")
REPORT = os.path.join(HERE, "build_report_v7.json")

sys.path.insert(0, os.path.join(ROOT, "tools"))
import hook_score  # noqa: E402
import humanize  # noqa: E402

PPQ = 480
EIGHTH = PPQ // 2
BAR = 6 * EIGHTH
BARS = 52

NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def pitch_name(value):
    return "%s%d" % (NOTES[value % 12], value // 12 - 1)


def at(bar, eighth):
    return (bar - 1) * BAR + int(round(eighth * EIGHTH))


def tracks(song):
    return {t["name"].strip().lower(): t for t in song["tracks"]}


def add_anticipation(song, report):
    """DIS-09: G4 on the last eighth of bar 36, the bar before the trio's Em."""
    lead = tracks(song)["vrc6 pulse a"]
    lead["notes"].append((at(36, 5), at(36, 6), 67, 96))
    lead["notes"] = sorted(lead["notes"])
    report["devices"].append({
        "id": "DIS-09", "risk": 1, "voice": "vrc6 pulse a",
        "bar": 36, "beat": 3, "eighth": 5, "pitch": pitch_name(67),
        "resolution": {"bar": 37, "beat": 1, "pitch": "Em chord tone, G"},
        "trigger": "last eighth of the bar before the trio's Em, G is the third of that chord",
        "budget": "B section: 1 device in 8 bars, inside 1 to 2",
    })


def add_suspension(song, report):
    """DIS-04: vrc6 pulse b holds E5 from bar 38 into the B7 bar and resolves to D#5 on beat 2."""
    pulse_b = tracks(song)["vrc6 pulse b"]
    before = len(pulse_b["notes"])
    # the voice is silent in bars 37 to 40 in v6; prove that before writing anything
    busy = [n for n in pulse_b["notes"]
            if 37 * BAR <= n[0] < 41 * BAR]
    if busy:
        raise SystemExit("vrc6 pulse b is not silent in the trio: %r" % busy[:4])
    pulse_b["notes"].extend([
        (at(38, 0), at(39, 2), 76, 74),          # E5: chord tone of Em, held across the bar line
        (at(39, 2), at(39, 4), 75, 78),          # D#5: the third of B7, one semitone down
    ])
    pulse_b["notes"] = sorted(pulse_b["notes"])
    report["devices"].append({
        "id": "DIS-04", "risk": 1, "voice": "vrc6 pulse b",
        "bar": 39, "beat": 1, "pitch": pitch_name(76),
        "preparation": {"bar": 38, "pitch": pitch_name(76), "why": "the fourth above the new bass B"},
        "resolution": {"bar": 39, "beat": 2, "pitch": pitch_name(75)},
        "trigger": "Em to B7 at the trio, prepared in the bar before",
        "uses": "vrc6 pulse b, silent in the trio in v6, so no motif statement is rewritten",
        "budget": "trio: 1 device in 8 bars, inside 1 to 2",
        "notes_before": before, "notes_after": len(pulse_b["notes"]),
    })


def extend_kit(song, report):
    """The 16 bar rung, the ghost snares and the pre-section tom fill on top of v6's kit."""
    t = tracks(song)
    noise, dpcm = t["noise"], t["dpcm"]
    HAT, OPEN_HAT, SNARE, TOM_HI, TOM_MID, TOM_LO, KICK = 12, 10, 38, 8, 6, 4, 36

    def hit(track, bar, step, pitch, velocity, length=60):
        start = at(bar, step)
        track["notes"].append((start, start + length, pitch, velocity))

    before = {"noise": len(noise["notes"]), "dpcm": len(dpcm["notes"])}

    # 16 bar rung: the hats drop out and the bar goes half time.
    for bar in (16, 32):
        noise["notes"] = [n for n in noise["notes"]
                          if not (at(bar, 0) <= n[0] < at(bar + 1, 0))]
        noise["notes"].extend([])
        hit(noise, bar, 4, SNARE, 104)                     # beat 3, the half time backbeat
        hit(noise, bar, 5, HAT, 40)
        hit(dpcm, bar, 0, KICK, 108)
        hit(dpcm, bar, 3, KICK, 84)

    # Ghost snares under the B section's backbeat, on the "and" of beat 2.
    for bar in range(21, 29):
        if bar % 2 == 0:
            hit(noise, bar, 3, SNARE, 42)
    for bar in range(29, 37):
        if bar % 2 == 1:
            hit(noise, bar, 3, SNARE, 40)

    # The bar before a section change ends on a three hit tom fill.
    for bar in (12, 20, 28, 36):
        for index, (step, pitch) in enumerate(((4, TOM_HI), (4.5, TOM_MID), (5, TOM_LO))):
            hit(noise, bar, step, pitch, 78 - 4 * index)

    # keep every track ordered and inside the cue
    end = BARS * BAR
    for track in (noise, dpcm):
        track["notes"] = sorted((max(0, s), min(end, max(s + 30, e)), p, v)
                                for s, e, p, v in track["notes"] if s < end)

    report["kit"] = {
        "noise_before": before["noise"], "noise_after": len(noise["notes"]),
        "dpcm_before": before["dpcm"], "dpcm_after": len(dpcm["notes"]),
        "rungs": "2 bar (hat density), 4 bar (open hat fill, second kick), 8 bar (five hit tom run, "
                 "crash into 13, 21, 29, 37, 45), 16 bar (bars 16 and 32 go half time with no hats), "
                 "ghost snares in B, three hit tom fill before bars 13, 21, 29, 37",
    }


def main():
    song = hook_score.read_smf(SRC)
    report = {
        "source": SRC,
        "tempo_bpm": 60_000_000 / song["tempo_us"],
        "time_sig": list(song["time_sig"]),
        "loop": "bar 5 for 48 bars",
        "tracks_in": [{"name": t["name"], "notes": len(t["notes"])} for t in song["tracks"]],
        "devices": [],
    }
    before = hook_score.score_file(SRC, track="vrc6 pulse a")
    report["hook_before"] = {"score": before["score"], "weakest": before["weakest"]}
    add_anticipation(song, report)
    add_suspension(song, report)
    extend_kit(song, report)
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
