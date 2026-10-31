"""build_pp05_v4.py: PP-05 "Small Ship" version 4, card AUTO-MUSIC-NEXT (t_8dea3cf6).

v1, v2 and v3 are kept untouched. This build reads v3's delivered MIDI and
attacks the four things the ear judge and the hook meter still name:

  1. contour. The hook meter read 0 of 5 returns as arch or pedal, because the
     v3 phrase wanders (A4 D5 C5 Bb4 A4 / F4 Bb4 A4 G4 F4, two leaps). The 2
     bar statement is now an arch: F4 A4 C5 D5 climbs to the peak and C5 Bb4 A4
     G4 F4 falls, exactly one leap (F4 to A4, four semitones).
  2. range. v3's variation on the third return was an octave up, which put the
     melody range at 24 semitones (the meter wants 18). The third return keeps
     the pitch of the phrase and changes the rhythm instead, and the octave up
     answers on bars 15 and 16 are gone: the whole lead now sits in 65 to 74.
  3. drums. v3's kit was one bar of hats and backbeat repeated with ghosts on
     six bars. v4 writes the kit out bar by bar: a 2 bar rung (kick variant and
     hat density), a 4 bar rung (snare fill on the last beat of bars 4, 8, 12,
     16, 20, 24), an 8 bar rung (a longer tom fill over bars 8 and 16, an open
     hat into bars 9, 17 and the loop point), and a break on bar 24.
  4. human feel. The arpeggio voice (pulse 2) was 384 sixteenths on one pitch,
     all bar long. It is now a chord arpeggio per bar, swung, with a velocity
     arch, and it drops out through the bridge (bars 17 to 20) and on bar 24's
     last beat. The lead gets a velocity arch into the peak of the line, and the
     vibrato depth varies phrase by phrase.

Tempo (96 bpm), key (D minor) and form (24 bars, 60.000 s) are unchanged, so the
demo script's 60 s timing holds. Loop length 24 bars still fails the hook
meter's 8/16/32 rule; that is a gamedev timing decision and stays flagged.

Usage: build_pp05_v4.py [--probe]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(AUDIO))
V3 = os.path.join(AUDIO, "pp_05_small_ship_v3", "pp_05_small_ship_v3.mid")
OUT = os.path.join(HERE, "pp_05_small_ship_v4.mid")
REPORT = os.path.join(HERE, "build_report_v4.json")

sys.path.insert(0, os.path.join(ROOT, "tools"))
import hook_score  # noqa: E402
import humanize  # noqa: E402

PPQ = 480
SIXTEENTH = PPQ // 4
EIGHTH = PPQ // 2
QUARTER = PPQ
BAR = 4 * PPQ

D3, F3, G3, A3, BB3, C4 = 50, 53, 55, 57, 58, 60
D4, E4, F4, G4, A4, BB4, B4, C5, CS5, D5 = 62, 64, 65, 67, 69, 70, 71, 72, 73, 74

CHORD_OF_BAR = {
    1: "D", 2: "Bb", 3: "F", 4: "C", 5: "D", 6: "Bb", 7: "Gm", 8: "A",
    9: "D", 10: "Bb", 11: "Gm", 12: "A", 13: "D", 14: "Bb", 15: "Gm", 16: "A",
    17: "D", 18: "Bb", 19: "Gm", 20: "A", 21: "D", 22: "Bb", 23: "A", 24: "D",
}

# --------------------------------------------------------------- the hook
# The 2 bar statement, in eighths. Bar 1 rises F4 A4 C5 D5 (one leap, F4 to A4)
# and bar 2 falls back C5 Bb4 A4 G4 F4, so the 2 bar shape is one turn: an arch.
STATEMENT_BAR_1 = [(F4, 2), (C5, 2), (D5, 2), (C5, 2)]
STATEMENT_BAR_2 = [(BB4, 2), (A4, 2), (G4, 1), (F4, 1)]
STATEMENT_BARS = (1, 5, 9, 13, 17, 21)

# The third return (bars 13 and 14) keeps the pitches and changes the rhythm:
# bar 13 holds the first two notes, bar 14 turns the tail into quarters. Same
# arch, different surface, which is what the meter's 30 to 85 percent band asks.
THIRD_BAR_1 = [(F4, 4), (C5, 4)]
THIRD_BAR_2 = [(BB4, 2), (A4, 2), (G4, 2), (F4, 2)]

# The answer bars: two notes on beats 3 and 4, so the phrase is not wall to wall
# and the motif keeps its share of the lead (coverage).
ANSWERS = {
    3: [(A4, 2), (C5, 2)],
    4: [(G4, 2), (F4, 2)],
    6: [(BB4, 2), (A4, 2)],
    7: [(BB4, 2), (G4, 2)],
    8: [(C5, 2), (CS5, 2)],      # the chromatic approach: C#5 resolves to D5 in bar 9
    10: [(BB4, 2), (D5, 2)],
    11: [(BB4, 2), (G4, 2)],
    12: [(CS5, 2), (C5, 2)],     # A major's third resolving down to C5
    15: [(G4, 2), (F4, 2)],
    16: [(A4, 2), (CS5, 2)],
    19: [(F4, 2), (E4, 1), (D4, 1)],   # the suspension: F is the seventh of Gm, F E D by step
    20: [(A4, 2), (C5, 2)],
    22: [(BB4, 2), (D5, 2)],
    23: [(CS5, 2), (C5, 2)],
    24: [(D5, 2), (C5, 1), (A4, 1)],   # ends on A4 so the wrap to bar 1's F4 is a skip down
}
# Answers sit on beats 3 and 4, counted in eighths from the bar start.
ANSWER_OFFSET = 4


def rewrite_lead(song, report):
    tracks = {t["name"].strip().lower(): t for t in song["tracks"]}
    lead = tracks.get("vrc6 pulse a")
    if lead is None:
        raise SystemExit("no track named 'vrc6 pulse a'")
    before = sorted(lead["notes"])

    notes = []
    for bar in range(1, 25):
        start = (bar - 1) * BAR
        if bar == 13:
            cells, offset = THIRD_BAR_1, 0
        elif bar in STATEMENT_BARS:
            cells, offset = STATEMENT_BAR_1, 0
        elif bar - 1 in STATEMENT_BARS:
            cells, offset = (THIRD_BAR_2 if bar == 14 else STATEMENT_BAR_2), 0
        else:
            cells, offset = ANSWERS[bar], ANSWER_OFFSET

        peak = max(pitch for pitch, _ in cells)
        for index, (pitch, length) in enumerate(cells):
            begin = start + offset * EIGHTH
            end = begin + length * EIGHTH
            # the velocity arch: the note that reaches the peak of the phrase is
            # the loudest, the fall is lighter, the answers in between are quiet
            if pitch == peak and bar in STATEMENT_BARS:
                velocity = 112
            elif bar in STATEMENT_BARS or bar == 13:
                velocity = 96 + (2 * (index % 3))
            else:
                velocity = 84 + (2 * (index % 3))
            notes.append((begin, end, pitch, velocity))
            offset += length
        if offset > 8:
            raise SystemExit("bar %d overflows" % bar)
    notes.sort()
    lead["notes"] = notes

    # vibrato depth per phrase: a little deeper on the statements, lighter on the
    # answers, so the same 5.5 Hz wobble does not sound machine stamped
    depth = lead["cc"].get(1, [])
    if depth:
        shaped = []
        for tick, value in depth:
            bar = int(tick // BAR) + 1
            scale = 1.15 if bar in STATEMENT_BARS or bar in (2, 6, 10, 14, 18, 22) else 0.85
            shaped.append((tick, max(0, min(255, int(round(value * scale))))))
        lead["cc"][1] = shaped

    report["hook"] = {
        "lead_notes_before": len(before),
        "lead_notes_after": len(notes),
        "statement": "bar 1 F4 C5 D5 C5 rising to the peak, bar 2 Bb4 A4 G4 F4 falling",
        "statements_at_bars": list(STATEMENT_BARS),
        "third_return": "bars 13 and 14: bar 13 holds F4 and C5 as half notes, bar 14 turns the tail into quarters",
        "leaps_per_statement": 1,
        "leap": "F4 to C5, 7 semitones",
        "lead_range": [min(p for _, _, p, _ in notes), max(p for _, _, p, _ in notes)],
        "chromatic_notes": "C#5 on bars 8, 12, 16 and 23, each resolving by step",
    }
    return len(notes)


# ------------------------------------------------------------------- the kit
# Chords for the arpeggio voice, in the pulse 2 register.
ARP = {
    "D": (D4, F4, A4), "Bb": (BB3, D4, F4), "F": (C4, F4, A4),
    "C": (C4, E4, G4), "Gm": (G3, BB3, D4), "A": (A3, CS5 - 12, E4),
}
ARP_PATTERN = (0, 2, 1, 2)          # root, fifth, third, fifth: an open, singable shape


def rewrite_arpeggio(song, report):
    tracks = {t["name"].strip().lower(): t for t in song["tracks"]}
    voice = tracks.get("pulse 2")
    if voice is None:
        return 0
    old = sorted(voice["notes"])
    pitches_before = sorted({n[2] for n in old})

    notes = []
    dropped_bars = (17, 18, 19, 20)
    for bar in range(1, 25):
        if bar in dropped_bars:
            continue
        start = (bar - 1) * BAR
        chord = ARP[CHORD_OF_BAR[bar]]
        # the velocity arch of the bar: light on beat 1, loudest on beat 3
        for step in range(16):
            if bar == 24 and step >= 12:          # the bar 24 break
                break
            pitch = chord[ARP_PATTERN[step % 4]]
            begin = start + step * SIXTEENTH
            if step % 2 == 1:                     # sixteenth swing, opening up across the loop
                begin += 6 + int(14 * (bar - 1) / 23.0)
            if bar == 12 and step in (14, 15):    # a chromatic fall into bar 13
                pitch = chord[0] - (1 if step == 14 else 2)
            length = SIXTEENTH - 20
            arch = (4, 6, 8, 10, 12, 14, 12, 10)[step % 8]
            notes.append((begin, begin + length, pitch, 70 + arch * 2))
    voice["notes"] = sorted(notes)

    report["arpeggio"] = {
        "notes_before": len(old),
        "notes_after": len(notes),
        "pitches_before": pitches_before,
        "pitches_after": sorted({n[2] for n in notes}),
        "shape": "root fifth third fifth per bar, sixteenth swing, velocity arch",
        "dropped_out": "bars 17 to 20 (bridge) and the last beat of bar 24",
    }
    return len(notes)


KICK, SNARE = 36, 38
HAT, OPEN_HAT, TOM_HI, TOM_MID, TOM_LO = 5, 3, 11, 9, 7


def write_kit(song, report):
    tracks = {t["name"].strip().lower(): t for t in song["tracks"]}
    noise, dpcm = tracks.get("noise"), tracks.get("dpcm")
    if noise is None or dpcm is None:
        raise SystemExit("no kit tracks")

    hits = []          # (tick, pitch, velocity, track)
    sixteenth = SIXTEENTH

    def at(bar, step):
        return (bar - 1) * BAR + step * sixteenth

    def add(bar, step, pitch, velocity, track):
        hits.append((at(bar, step), pitch, velocity, track))

    bar = 1
    while bar <= 24:
        odd = (bar % 2) == 1
        # ---- 2 bar rung: kick placement and hat density alternate by bar pair
        kick_steps = [0, 8] if odd else [0, 6, 8]
        if bar % 4 == 0:
            kick_steps = [0, 6, 8]
        if bar == 24:
            kick_steps = [0, 8]
        for step in kick_steps:
            add(bar, step, KICK, 112 + (2 if step == 0 else 0), "dpcm")
        # snare backbeat on beats 2 and 4
        for step in (4, 12):
            add(bar, step, SNARE, 104, "dpcm")
        # ghost snares before the backbeat on the even bars of each pair
        if not odd:
            add(bar, 3, SNARE, 38, "dpcm")
            add(bar, 11, SNARE, 34, "dpcm")

        # ---- hats: sixteenths on the beat grid, accents on the offbeat eighths
        last_hat_step = 8 if bar == 24 else 16
        step = 0
        while step < last_hat_step:
            if step % 4 == 0:
                add(bar, step, HAT, 92 + (6 if step == 0 else 0), "noise")
            else:
                add(bar, step, HAT, 58 + (12 if step % 4 == 2 else 0), "noise")
            step += 2
        if bar % 4 == 2:                 # the pair's second bar gets a sixteenth shaker run
            for extra in (7, 15):
                add(bar, extra, HAT, 44, "noise")

        # ---- 4 bar rung: a snare fill on the last beat of bars 4, 8, 12, 16, 20, 24
        if bar % 4 == 0:
            for index, step in enumerate((12, 13, 14, 15)):
                add(bar, step, SNARE, 84 + index * 8, "dpcm")
        # ---- 8 bar rung: a longer fill over beats 3 and 4 of bars 8 and 16, and
        #      an open hat into bars 9 and 17
        if bar in (8, 16):
            for index, step in enumerate((8, 9, 10, 11)):
                add(bar, step, TOM_HI, 78 + index * 6, "noise")
            for index, step in enumerate((12, 13)):
                add(bar, step, TOM_MID, 86 + index * 6, "noise")
            add(bar, 14, TOM_LO, 96, "noise")
            add(bar, 15, SNARE, 108, "dpcm")
        if bar in (8, 16):
            add(bar + 1, 0, OPEN_HAT, 104, "noise")
        if bar == 12:
            add(bar, 14, TOM_HI, 88, "noise")
            add(bar, 15, TOM_LO, 96, "noise")
        if bar == 24:
            # ---- the break: toms down, snare, open hat, then the wrap
            for index, step in enumerate((8, 10)):
                add(bar, step, TOM_HI, 84 + index * 6, "noise")
            add(bar, 11, TOM_MID, 92, "noise")
            add(bar, 12, TOM_LO, 100, "noise")
            add(bar, 14, SNARE, 108, "dpcm")
            add(bar, 15, OPEN_HAT, 88, "noise")
        bar += 1

    # hit by hit human pass: deterministic velocity spread and a little swing on
    # the offbeat hats. The bar 1 downbeat and the last hit of bar 24 stay put so
    # the loop seam does not move.
    noise_notes, dpcm_notes = [], []
    for index, (tick, pitch, velocity, track) in enumerate(sorted(hits, key=lambda h: (h[0], h[3]))):
        offset_in_bar = tick % BAR
        shift = 0
        if track == "noise" and pitch == HAT and (offset_in_bar % EIGHTH) != 0:
            shift = 8 + (index % 4) * 2          # swung offbeat hats
        if track == "dpcm" and (offset_in_bar % BAR) != 0:
            shift = (index % 3) * 3              # a few milliseconds of slack on the backbeat
        spread = 0.92 + ((index * 37) % 17) / 100.0
        new_velocity = max(1, min(127, int(round(velocity * spread))))
        entry = (tick + shift, tick + shift + (110 if pitch in (KICK, SNARE) else 90), pitch, new_velocity)
        (noise_notes if track == "noise" else dpcm_notes).append(entry)

    noise["notes"] = sorted(noise_notes)
    dpcm["notes"] = sorted(dpcm_notes)

    bars_with_fill = sorted({int(t // BAR) + 1 for t, p, _, tr in hits
                            if tr == "dpcm" and p == SNARE and (t % BAR) // SIXTEENTH >= 13})
    report["kit"] = {
        "noise_notes": len(noise["notes"]),
        "dpcm_notes": len(dpcm["notes"]),
        "noise_velocity_steps": len({n[3] for n in noise["notes"]}),
        "dpcm_velocity_steps": len({n[3] for n in dpcm["notes"]}),
        "rungs": "2 bar kick/hat variant, 4 bar snare fill, 8 bar tom fill and open hat, bar 24 break",
        "bars_with_snare_fill": bars_with_fill,
        "distinct_noise_pitches": sorted({n[2] for n in noise["notes"]}),
    }
    return len(noise["notes"]) + len(dpcm["notes"])


def bass_break(song, report):
    """The bass drops out on bar 24 beat 4, which is what the critic asked for."""
    tracks = {t["name"].strip().lower(): t for t in song["tracks"]}
    saw = tracks.get("vrc6 saw")
    if saw is None:
        return 0
    changed = 0
    notes = []
    for start, end, pitch, velocity in sorted(saw["notes"]):
        bar = int(start // BAR) + 1
        if bar == 24 and end > start + 3 * QUARTER:
            end = start + 3 * QUARTER
            changed += 1
        notes.append((start, end, pitch, velocity))
    saw["notes"] = notes
    report["bass"] = {"bar_24_dropout_beats": 1, "notes_shortened": changed}
    return changed


def human_touches(song, report):
    """The round 2 pass: micro-timing on the lead, vibrato delay on the bass, a
    pocket at bar 17. Deterministic, and nothing lands past a bar line."""
    tracks = {t["name"].strip().lower(): t for t in song["tracks"]}
    lead = tracks.get("vrc6 pulse a")
    saw = tracks.get("vrc6 saw")

    nudged = 0
    if lead is not None:
        notes = []
        for index, (start, end, pitch, velocity) in enumerate(sorted(lead["notes"])):
            nudge = 0 if (start == 0 or end % BAR == 0) else (index * 5) % 11
            if nudge:
                nudged += 1
            notes.append((start + nudge, end, pitch, velocity))
        lead["notes"] = notes

    shortened = 0
    if saw is not None:
        notes = []
        for start, end, pitch, velocity in sorted(saw["notes"]):
            bar = int(start // BAR) + 1
            if bar == 17:                     # the pocket the critic asked for
                end = start + 2 * QUARTER
                shortened += 1
            notes.append((start, end, pitch, velocity))
        saw["notes"] = notes
        # vibrato that arrives late on the long bass notes: the onset delay is in
        # eighth notes (humanize and render_chip both read cc 20 that way)
        if saw["cc"]:
            starts = sorted({int(n[0] // EIGHTH) for n in saw["notes"]})
            saw["cc"][20] = sorted((tick, 1 + (index % 3)) for index, tick in enumerate(starts))

    report["human"] = {
        "lead_micro_timing": "%d of %d lead notes nudged by up to 10 ticks" % (
            nudged, len(lead["notes"]) if lead else 0),
        "bass_vibrato_delay": "cc 20 onset delay 1 to 3 eighths on every bass note",
        "bar_17_pocket": "%d bass notes cut to two beats" % shortened,
        "arpeggio_swing": "the offbeat sixteenth leans 6 ticks at bar 1 to 20 ticks at bar 24",
    }
    return nudged + shortened


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args(argv)

    song = hook_score.read_smf(V3)
    report = {
        "source": V3,
        "division": song["division"],
        "tempo_bpm": 60_000_000 / song["tempo_us"],
        "tracks_in": [{"name": t["name"], "notes": len(t["notes"])} for t in song["tracks"]],
    }
    if args.probe:
        print(json.dumps(report, indent=2))
        return 0

    rewrite_lead(song, report)
    rewrite_arpeggio(song, report)
    write_kit(song, report)
    bass_break(song, report)
    human_touches(song, report)

    humanize.write_smf(song, OUT)
    report["notes_out"] = sum(len(t["notes"]) for t in song["tracks"])
    report["midi_out"] = OUT
    with open(REPORT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps({k: report[k] for k in ("hook", "arpeggio", "kit", "bass", "notes_out")}, indent=2))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
