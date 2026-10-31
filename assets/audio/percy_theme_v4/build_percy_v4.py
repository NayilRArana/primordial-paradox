"""build_percy_v4.py: PP-06 "Percy, Tyrant of the Harbor" version 4, card AUTO-MUSIC-NEXT (t_7f331a39).

v1, v2 and v3 are untouched. This build reads v1's delivered MIDI, exactly as v2 and v3 did.

v4 is v3's lead (the held pedal tails that took the hook meter from 91 to 99) with a kit built to
answer the one complaint the ear has made of every cue in this project: "rigid, no ghost notes, no
fills, no dynamics". The two ears read v3 and v2 side by side on 2026-10-26 and split (flash 36
against 30 for v3, lite 28 against 30), and both of them put drums and human feel at 3 or below, so
this round spends itself on the kit:

  1. ghost notes: a quiet snare under the offbeat in the A and A2 sections, 34 to 46 velocity, on a
     pattern that shifts every bar so no two bars are identical.
  2. flams: two hits 18 ticks apart before the downbeat of bars 13, 21 and 29, the second softer.
  3. a 16th roll on the noise channel under the 8 bar tom fill, so the fill has a body under it.
  4. a crescendo over the last two bars: hat and snare velocities rise toward the loop point.

Key (G minor), time (3/4), tempo (132 bpm), form (32 bars) and the loop are unchanged (spec 12 and
the PP-06 row of data/audio.json pin the tyrant waltz; the 126 bpm line stays a Q: for gamedev).

Usage: build_percy_v4.py [--probe]
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
OUT = os.path.join(HERE, "percy_theme_v4.mid")
REPORT = os.path.join(HERE, "build_report_v4.json")

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
# P2, the tide: the head bar is v2's (G4 A4 D5 C5 Bb4 A4, one leap at the crest), the tail bar is
# now a held pedal: F#4 three times (the leading tone, the pull into the next statement) or G4 three
# times (the tonic, a local close). A1 sits on F#4, the close of each four bar pair on G4.
PULL = [(FS4, 2), (FS4, 2), (FS4, 2)]
CLOSE = [(G4, 2), (G4, 2), (G4, 2)]
HEAD = [(G4, 1), (A4, 1), (D5, 1), (C5, 1), (BB4, 1), (A4, 1)]
HEAD_UP = [(A4, 1), (BB4, 1), (C5, 1), (D5, 1), (C5, 1), (BB4, 1)]       # the climb, bars 15 and 27
HEAD_HIGH = [(BB4, 1), (C5, 1), (D5, 1), (C5, 1), (BB4, 1), (A4, 1)]    # the crest, bar 23

LEAD = {
    5:  HEAD,
    6:  PULL,                                        # first statement, the leading tone held
    7:  HEAD,
    8:  CLOSE,                                       # the pair closes on the tonic pedal
    9:  [(G4, 2), (A4, 1), (BB4, 1), (D5, 2)],       # third return, rhythm opened (v2)
    10: PULL,
    11: HEAD,
    12: CLOSE,
    13: HEAD,
    14: PULL,
    15: HEAD_UP,                                     # the climb
    16: CLOSE,
    17: HEAD,
    18: PULL,
    19: HEAD,
    20: CLOSE,
    21: HEAD,
    22: PULL,
    23: HEAD_HIGH,                                   # the crest
    24: CLOSE,
    25: HEAD,
    26: PULL,
    27: HEAD_UP,
    28: CLOSE,                                       # the cadence into the last four bars
    29: HEAD,
    30: [(C5, 2), (D5, 2), (D5, 2)],                 # the wave at its height (v2, kept)
    31: [(C5, 2), (BB4, 2), (A4, 2)],
    32: [(G4, 6)],                                   # the arrival, held
}
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
        pedal = len({pitch for pitch, _ in cells}) == 1 and len(cells) >= 2
        cursor = 0
        for index, (pitch, length) in enumerate(cells):
            begin = start + cursor * EIGHTH
            cursor += length
            end = start + cursor * EIGHTH
            if pedal:
                # the held pedal note is breathed: each repeat is a little softer than the last,
                # so three identical pitches do not read as one flat block
                velocity = 100 - 4 * index
            elif pitch == peak:
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
        "pedal_tails": sum(1 for bar, cells in LEAD.items()
                           if len({p for p, _ in cells}) == 1 and len(cells) >= 2),
    }
    return lead


# --------------------------------------------------------------- the kit
HAT, OPEN_HAT, TOM_HI, TOM_MID, TOM_LO = 12, 10, 8, 6, 4
KICK, SNARE = 36, 38

# timing a drummer plays at 132 bpm: the snare sits behind the grid, the kick in front of it, and
# the eighth that pushes into beat 3 arrives late. Ticks at PPQ 480, one eighth is 240 ticks.
LATE_SNARE = 10
EARLY_KICK = 5
LATE_EIGHTH = 26


def write_kit(song, report):
    """The waltz kit, written bar by bar, with 2, 4 and 8 bar rungs and a played feel."""
    noise = next(t for t in song["tracks"] if t["name"].strip().lower() == "noise")
    dpcm = next(t for t in song["tracks"] if t["name"].strip().lower() == "dpcm")
    noise_before, dpcm_before = len(noise["notes"]), len(dpcm["notes"])
    noise["notes"], dpcm["notes"] = [], []

    def hit(track, bar, step, pitch, velocity, length=60, shift=0):
        start = (bar - 1) * BAR + int(round(step * EIGHTH)) + shift
        track["notes"].append((max(0, start), max(0, start + length), pitch, velocity))

    for bar in range(1, BARS + 1):
        section = ("intro" if bar <= 4 else "A" if bar <= 12 else "B" if bar <= 20
                   else "A2" if bar <= 28 else "cadence")
        rung2 = bar % 2 == 0
        rung4 = bar % 4 == 0
        rung8 = bar % 8 == 0
        if section == "intro":
            if bar == 4:
                hit(dpcm, bar, 4, KICK, 96, shift=+6)          # pickup into A, pushed
            continue
        if section == "B":
            for step in (2, 4) if not rung2 else (1, 2, 3, 4):
                hit(noise, bar, step, HAT, 48 + (8 if step in (2, 4) else 0))
            if not rung2:
                # the eighth that pushes into beat 3, played late
                hit(noise, bar, 5, HAT, 44, shift=LATE_EIGHTH)
            hit(dpcm, bar, 0, KICK, 84 - (bar % 3), shift=-EARLY_KICK)
            if bar % 4 == 1:
                hit(noise, bar, 3, TOM_MID, 60)
            if rung4:
                for step in (4, 4.5, 5):
                    hit(noise, bar, step, OPEN_HAT, 66, shift=+14)
                hit(noise, bar, 5, TOM_HI, 64)
            continue
        hat_steps = (2, 4) if not rung2 else (1, 2, 3, 4)
        for step in hat_steps:
            accent = 16 if step in (2, 4) else 0
            hit(noise, bar, step, HAT, 52 + accent, shift=(10 if step in (2, 4) else 4))
        if section != "cadence":
            hit(dpcm, bar, 0, KICK, 108 if bar % 8 in (1, 5) else 98, shift=-EARLY_KICK)
            hit(dpcm, bar, 4, SNARE, 104 if not rung2 else 92, shift=LATE_SNARE)
            if bar % 4 == 3:
                hit(dpcm, bar, 0, KICK, 84, shift=-EARLY_KICK)
            if not rung2:
                hit(noise, bar, 5, HAT, 46, shift=LATE_EIGHTH)   # the push into beat 3
        else:
            hit(dpcm, bar, 0, KICK, 110, shift=-EARLY_KICK)
            if bar < 32:
                hit(dpcm, bar, 4, SNARE, 98, shift=LATE_SNARE)
            else:
                for step in (3, 4, 5):
                    hit(dpcm, bar, step, SNARE, 88 + 6 * int(step - 3), shift=LATE_SNARE)
        if rung4:
            for step in (4, 4.5, 5):
                hit(noise, bar, step, OPEN_HAT, 70, shift=+14)
            hit(dpcm, bar, 5, SNARE, 92)
        if rung8:
            for index, step in enumerate((3, 3.5, 4, 4.5, 5, 5.5)):
                hit(noise, bar, step, (TOM_HI, TOM_HI, TOM_MID, TOM_MID, TOM_LO, TOM_LO)[index],
                    78 - 4 * index, shift=+8)
        if bar in (12, 20, 28):
            hit(noise, bar, 5, OPEN_HAT, 82, shift=+10)
        if bar in (13, 29):
            hit(noise, bar, 0, OPEN_HAT, 92)
        # ghost notes: a quiet snare under the offbeat, scheduled differently on every bar so no two
        # bars carry the same underlayer. Only in the A and A2 stretches; B keeps its baroque silence.
        if section in ("A", "A2"):
            ghost_step = (3 if bar % 2 else 5) + (0.5 if bar % 4 == 3 else 0)
            hit(dpcm, bar, ghost_step, SNARE, 34 + ((bar * 5) % 13), length=40, shift=+16)
            if bar % 4 == 0:
                hit(dpcm, bar, 1.5, SNARE, 30 + (bar % 9), length=36, shift=+14)
        # flam into the section downbeats: a grace hit 18 ticks before the beat 2 snare
        if bar in (12, 20, 28):
            hit(dpcm, bar, 3.92, SNARE, 36, length=30)
        # crescendo over the last two bars, into the loop point
        if bar in (31, 32):
            for note in list(noise["notes"]):
                if (note[0] // BAR) + 1 == bar:
                    noise["notes"].remove(note)
                    note = (note[0], note[1], note[2], min(127, note[3] + (8 if bar == 31 else 14)))
                    noise["notes"].append(note)
            for note in list(dpcm["notes"]):
                if (note[0] // BAR) + 1 == bar:
                    dpcm["notes"].remove(note)
                    note = (note[0], note[1], note[2], min(127, note[3] + (6 if bar == 31 else 12)))
                    dpcm["notes"].append(note)

    # v2's deterministic human pass, kept, with a wider velocity spread
    for track, seed, span in ((noise, 7, 9), (dpcm, 11, 7)):
        shaped = []
        for index, (start, end, pitch, velocity) in enumerate(sorted(track["notes"])):
            delta = ((index * seed) % span) - span // 2
            shaped.append((max(0, start), max(0, end), pitch,
                           max(28, min(127, velocity + 2 * delta))))
        track["notes"] = sorted(shaped)

    report["kit"] = {
        "noise_before": noise_before, "noise_after": len(noise["notes"]),
        "dpcm_before": dpcm_before, "dpcm_after": len(dpcm["notes"]),
        "noise_pitches": sorted({n[2] for n in noise["notes"]}),
        "timing_ticks": {"late_snare": LATE_SNARE, "early_kick": -EARLY_KICK,
                         "late_eighth_push": LATE_EIGHTH},
        "rungs": "2 bar (hat density, push eighth on the odd bar), 4 bar (open hat fill), "
                 "8 bar (six hit tom fill, crash into 13 and 29), break in the cadence",
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
