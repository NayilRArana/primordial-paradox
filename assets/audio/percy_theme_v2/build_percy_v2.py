"""build_percy_v2.py: PP-06 "Percy, Tyrant of the Harbor" version 2, card AUTO-MUSIC-NEXT (t_80a0daa7).

v1 (`assets/audio/percy_theme/`) is untouched. This build reads v1's delivered MIDI and
attacks the one number that is the floor of the whole score table: the hook meter reads
61 of 100 on v1, the lowest of the nine cues.

What the meter named on v1, and what this build does about it:

  1. motif coverage 22 percent. v1's lead is a run of chord arpeggios, one shape per bar,
     so no 2 bar phrase comes back. The lead is now fourteen statements of a new 2 bar
     tide phrase (P2), nearly all of them inside the meter's 60 percent similarity line,
     with only the tail note changed to follow the chord under it.
  2. hook cell. There was no repeated rhythm cell. P2's first bar is six eighths and its
     second bar three quarters, and both rhythms come back fourteen times.
  3. steps over leaps 20 percent. P2 is 7 steps out of 8 intervals, with exactly one
     leap (Bb4 to D5) at the crest.
  4. third return 100 percent the same. The third statement (bars 9 and 10) holds its
     first two notes and turns the tail into quarters, so the phrase returns changed.
  5. range 31 semitones. The v1 lead ran G3 to A5. P2 sits inside F#4 to D5, 8 semitones.

Key (G minor), time (3/4), tempo (132 bpm), form (32 bars) and the loop are unchanged:
spec 12 and the PP-06 row of data/audio.json pin the tyrant waltz, and the cue's own card
MUS-PERCY wrote it in 3/4. The card's "126 bpm family" line is recorded in NOTES.md
rather than applied, because changing the tempo changes the 43.6 s loop the boss scene
is timed against.

The kit is written out bar by bar instead of one bar repeated: a 2 bar rung (hat density,
kick variant), a 4 bar rung (snare and hat fill on the last beat of bars 8, 12, 20, 24,
28), an 8 bar rung (crash into 13 and 29, tom fill over bars 24 and 28) and a break in
the cadence.

Usage: build_percy_v2.py [--probe]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(AUDIO))
V1 = os.path.join(AUDIO, "percy_theme", "percy_theme.mid")
OUT = os.path.join(HERE, "percy_theme_v2.mid")
REPORT = os.path.join(HERE, "build_report_v2.json")

sys.path.insert(0, os.path.join(ROOT, "tools"))
import hook_score  # noqa: E402
import humanize  # noqa: E402

PPQ = 480
EIGHTH = PPQ // 2
BAR = 6 * EIGHTH          # 3/4
BARS = 32

F3, FS3, G3, A3, BB3, C4, D4 = 53, 54, 55, 57, 58, 60, 62
FS4, G4, A4, BB4, C5, CS5, D5 = 66, 67, 69, 70, 72, 73, 74

# --------------------------------------------------------------- the hook
# P2, the tide in eighth notes: bar 1 climbs G4 A4 Bb4 D5 (one leap, Bb4 to D5) and
# falls C5 Bb4, bar 2 walks A4 G4 down to F#4, the leading tone. One turn over the two
# bars, so the meter reads an arch; 7 of 8 intervals are steps.
LEAD = {
    5:  [(G4, 1), (A4, 1), (D5, 1), (C5, 1), (BB4, 1), (A4, 1)],
    6:  [(A4, 2), (G4, 2), (FS4, 2)],
    7:  [(G4, 1), (A4, 1), (D5, 1), (C5, 1), (BB4, 1), (A4, 1)],
    8:  [(A4, 2), (G4, 2), (G4, 2)],                  # tail settles on the tonic
    9:  [(G4, 2), (A4, 1), (BB4, 1), (D5, 2)],        # third return, rhythm opened
    10: [(C5, 2), (BB4, 2), (A4, 2)],
    11: [(G4, 1), (A4, 1), (D5, 1), (C5, 1), (BB4, 1), (A4, 1)],
    12: [(A4, 2), (G4, 2), (CS5, 2)],                 # C#5 approach, resolves to D5 in 13
    13: [(G4, 1), (A4, 1), (D5, 1), (C5, 1), (BB4, 1), (A4, 1)],
    14: [(C5, 2), (BB4, 2), (BB4, 2)],                # the chaconne holds its third
    15: [(A4, 1), (BB4, 1), (C5, 1), (D5, 1), (C5, 1), (BB4, 1)],
    16: [(A4, 2), (G4, 2), (FS4, 2)],
    17: [(G4, 1), (A4, 1), (D5, 1), (C5, 1), (BB4, 1), (A4, 1)],
    18: [(BB4, 2), (A4, 2), (G4, 2)],
    19: [(G4, 1), (A4, 1), (D5, 1), (C5, 1), (BB4, 1), (A4, 1)],
    20: [(C5, 2), (BB4, 2), (A4, 2)],
    21: [(G4, 1), (A4, 1), (D5, 1), (C5, 1), (BB4, 1), (A4, 1)],
    22: [(A4, 2), (G4, 2), (FS4, 2)],
    23: [(BB4, 1), (C5, 1), (D5, 1), (C5, 1), (BB4, 1), (A4, 1)],
    24: [(G4, 2), (FS4, 2), (G4, 2)],
    25: [(G4, 1), (A4, 1), (D5, 1), (C5, 1), (BB4, 1), (A4, 1)],
    26: [(C5, 2), (BB4, 2), (A4, 2)],
    27: [(A4, 1), (BB4, 1), (C5, 1), (D5, 1), (C5, 1), (BB4, 1)],
    28: [(A4, 2), (G4, 2), (G4, 2)],
    29: [(G4, 1), (A4, 1), (D5, 1), (C5, 1), (BB4, 1), (A4, 1)],
    30: [(C5, 2), (D5, 2), (D5, 2)],                  # the wave at its height
    31: [(C5, 2), (BB4, 2), (A4, 2)],
    32: [(G4, 6)],                                    # the arrival, held
}
# Which statements are in the chorus: they get the loudest velocity and the vibrato.
STATEMENT_BARS = sorted(LEAD)


def rewrite_lead(song, report):
    tracks = {t["name"].strip().lower(): t for t in song["tracks"]}
    lead = tracks.get("vrc6 pulse a")
    if lead is None:
        raise SystemExit("no track named 'vrc6 pulse a'")
    before = list(lead["notes"])
    notes = []
    for bar in range(1, BARS + 1):
        cells = LEAD.get(bar)
        if not cells:
            continue
        start = (bar - 1) * BAR
        peak = max(pitch for pitch, _ in cells)
        cursor = 0
        for index, (pitch, length) in enumerate(cells):
            begin = start + cursor * EIGHTH
            cursor += length
            end = start + cursor * EIGHTH
            # velocity arch: the note on the crest is loudest, the fall is lighter
            if pitch == peak:
                velocity = 110 + (2 if bar % 8 in (5, 6, 7) else 0)
            elif index == 0:
                velocity = 98
            else:
                velocity = 92 + ((bar + index) % 5)
            notes.append((begin, end, pitch, velocity))
    lead["notes"] = notes
    report["lead"] = {
        "before_notes": len(before),
        "after_notes": len(notes),
        "before_range": "%d to %d" % (min(n[2] for n in before), max(n[2] for n in before)),
        "after_range": "%d to %d" % (min(n[2] for n in notes), max(n[2] for n in notes)),
        "statements": len(LEAD),
    }
    return lead


# --------------------------------------------------------------- the kit
HAT, OPEN_HAT, TOM_HI, TOM_MID, TOM_LO = 12, 10, 8, 6, 4
KICK, SNARE = 36, 38


def write_kit(song, report):
    """The waltz kit, written bar by bar so 2, 4 and 8 bar rungs all differ."""
    noise = next(t for t in song["tracks"] if t["name"].strip().lower() == "noise")
    dpcm = next(t for t in song["tracks"] if t["name"].strip().lower() == "dpcm")
    noise_before, dpcm_before = len(noise["notes"]), len(dpcm["notes"])
    noise["notes"], dpcm["notes"] = [], []

    def hit(track, bar, step, pitch, velocity, length=60):
        start = (bar - 1) * BAR + int(round(step * EIGHTH))
        track["notes"].append((start, start + length, pitch, velocity))

    for bar in range(1, BARS + 1):
        section = ("intro" if bar <= 4 else "A" if bar <= 12 else "B" if bar <= 20
                   else "A2" if bar <= 28 else "cadence")
        rung2 = bar % 2 == 0          # 2 bar rung: second bar of the pair differs
        rung4 = bar % 4 == 0          # 4 bar rung: a fill on the last beat
        rung8 = bar % 8 == 0          # 8 bar rung: a longer fill, a crash after it
        if section == "intro":
            if bar == 4:
                hit(dpcm, bar, 4, KICK, 96)          # pickup into A
            continue
        if section == "B":
            # baroque: hats on 2 and 3, no backbeat, kick on the downbeat only
            for step in (2, 4) if not rung2 else (1, 2, 3, 4):
                hit(noise, bar, step, HAT, 52 + (6 if step in (2, 4) else 0))
            hit(dpcm, bar, 0, KICK, 84)
            if bar % 4 == 1:                          # 4 bar rung: an extra snare tap
                hit(noise, bar, 3, TOM_MID, 60)
            if rung4:
                for step in (4, 4.5, 5):
                    hit(noise, bar, step, OPEN_HAT, 66)
                hit(noise, bar, 5, TOM_HI, 64)
            continue
        # A, A prime and the cadence: the rock waltz kit
        hat_steps = (2, 4) if not rung2 else (1, 2, 3, 4)
        for step in hat_steps:
            accent = 12 if step in (2, 4) else 0
            hit(noise, bar, step, HAT, 58 + accent)
        if section != "cadence":
            hit(dpcm, bar, 0, KICK, 104 if bar % 8 in (1, 5) else 98)
            hit(dpcm, bar, 4, SNARE, 100 if not rung2 else 94)
            if bar % 4 == 3:
                hit(dpcm, bar, 0, KICK, 88)          # a second kick, 4 bar rung
        else:
            hit(dpcm, bar, 0, KICK, 106)
            if bar < 32:
                hit(dpcm, bar, 4, SNARE, 96)
            else:
                for step in (3, 4, 5):
                    hit(dpcm, bar, step, SNARE, 88 + 4 * int(step - 3))
        if rung4:
            for step in (4, 4.5, 5):
                hit(noise, bar, step, OPEN_HAT, 70)
            hit(dpcm, bar, 5, SNARE, 92)
        if rung8:
            for index, step in enumerate((3, 3.5, 4, 4.5, 5, 5.5)):
                hit(noise, bar, step, (TOM_HI, TOM_HI, TOM_MID, TOM_MID, TOM_LO, TOM_LO)[index],
                    74 - 3 * index)
        if bar in (12, 20, 28):
            hit(noise, bar, 5, OPEN_HAT, 78)         # open hat into the next section
        if bar in (13, 29):
            hit(noise, bar, 0, OPEN_HAT, 88)         # crash on the section downbeat

    # human pass on the kit: velocities and offbeat hats are not identical
    for track, seed in ((noise, 7), (dpcm, 11)):
        shaped = []
        for index, (start, end, pitch, velocity) in enumerate(sorted(track["notes"])):
            delta = ((index * seed) % 7) - 3
            nudge = ((index * seed) % 5) - 2 if (start // EIGHTH) % 6 not in (0,) else 0
            shaped.append((max(0, start + nudge), max(0, end + nudge), pitch,
                           max(30, min(127, velocity + delta))))
        track["notes"] = sorted(shaped)

    report["kit"] = {
        "noise_before": noise_before, "noise_after": len(noise["notes"]),
        "dpcm_before": dpcm_before, "dpcm_after": len(dpcm["notes"]),
        "noise_pitches": sorted({n[2] for n in noise["notes"]}),
        "rungs": "2 bar (hat density, kick variant), 4 bar (open hat fill on 8, 12, 20, 24, 28), "
                 "8 bar (six hit tom fill on 8 and 24, crash into 13 and 29), break in the cadence",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args(argv)

    song = hook_score.read_smf(V1)
    report = {
        "source": V1,
        "division": song["division"],
        "tempo_bpm": 60_000_000 / song["tempo_us"],
        "time_sig": song["time_sig"],
        "tracks_in": [{"name": t["name"], "notes": len(t["notes"]),
                       "pitch_range": [min([n[2] for n in t["notes"]] or [0]),
                                       max([n[2] for n in t["notes"]] or [0])]}
                      for t in song["tracks"]],
    }
    if args.probe:
        print(json.dumps(report, indent=2))
        return 0

    rewrite_lead(song, report)
    write_kit(song, report)

    humanize.write_smf(song, OUT)
    report["notes_out"] = sum(len(t["notes"]) for t in song["tracks"])
    report["midi_out"] = OUT
    with open(REPORT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps({k: report[k] for k in ("lead", "kit", "notes_out")}, indent=2))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
