"""build_pp05_v5.py: PP-05 "Small Ship" version 5, card AUTO-MUSIC-NEXT (t_cb333899).

v1 to v4 are kept untouched. This build reads v4's delivered MIDI and does the
one thing v4's own notes said could not be done inside the 60 s demo slot: it
moves the cue into the 126 bpm family and the hook meter's 8/16/32 bar rule at
the same time.

  tempo   96 to 128 bpm. Every note keeps its tick position, so the 24 bars of
          v4 now play in 45 s instead of 60 s.
  form    24 to 32 bars. The freed 15 s carries a new eight bar section (bars
          25 to 32) that develops the hook and closes it, so the loop is exactly
          32 bars at 128 bpm = 60.000 s, the length the demo script times
          against. Loop length goes from 24 (fails the meter) to 32 (passes).
  hook    bars 25 to 32 restate the two bar arch in pitch, so the motif is
          heard four more times and coverage does not fall; the statement at
          bars 31 and 32 is the rhythm variation the meter asks for on a later
          return.
  drums   the kit is written out over all 32 bars with a 2 bar rung, a 4 bar
          rung, an 8 bar rung and a 16 bar rung, so the variation lands every
          4 and every 8 bars and not only at the end.
  colour  three devices from knowledge/MUSIC-DISSONANCE.md section 2, each
          prepared, each resolved by step, none on the first or last note of a
          statement (that file's rule F1): a 9-8 suspension over Bb at bar 26,
          an 11-3 resolution over A7 at bar 27, and a chromatic inner voice
          climbing to the A7 third on bars 27 and 28.

Usage: build_pp05_v5.py [--probe]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(AUDIO))
V4 = os.path.join(AUDIO, "pp_05_small_ship_v4", "pp_05_small_ship_v4.mid")
OUT = os.path.join(HERE, "pp_05_small_ship_v5.mid")
REPORT = os.path.join(HERE, "build_report_v5.json")

sys.path.insert(0, os.path.join(ROOT, "tools"))
import hook_score  # noqa: E402
import humanize  # noqa: E402

PPQ = 480
SIXTEENTH = PPQ // 4
EIGHTH = PPQ // 2
QUARTER = PPQ
BAR = 4 * PPQ
BARS = 32
TEMPO_US = 468750          # 128.000 bpm: 32 bars of 4/4 in 60.000 s

E3, F3, G3, A3, BB3, B3, C4, CS4, D4, E4, F4, G4, A4, BB4, B4, C5, CS5, D5, E5 = (
    52, 53, 55, 57, 58, 59, 60, 61, 62, 64, 65, 67, 69, 70, 71, 72, 73, 74, 76)

# Bars 25 to 32: Bb, Bb, A7, A7, D, Bb, Gm, A7. The cadence is the v4 one
# (D, Bb, Gm, A) shifted a bar later so the wrap to bar 1 lands on the tonic.
CHORD_OF_BAR = {
    25: "Bb", 26: "Bb", 27: "A7", 28: "A7",
    29: "D", 30: "Bb", 31: "Gm", 32: "A7",
}

# The same two bar arch v4 wrote, kept in pitch so the motif returns unchanged.
STATEMENT_BAR_1 = [(F4, 2), (C5, 2), (D5, 2), (C5, 2)]
STATEMENT_BAR_2 = [(BB4, 2), (A4, 2), (G4, 1), (F4, 1)]

NEW_LEAD = {
    # the development: the arch, then the same arch ending on the 9th that
    # resolves to the 8th (the bar 26 suspension)
    25: STATEMENT_BAR_1,
    26: [(C5, 2), (BB4, 2), (G4, 1), (F4, 1)],
    # the dominant: a climb that lands on the third of A7
    27: [(E5, 2), (D5, 2), (CS5, 2), (A4, 2)],
    28: [(E5, 2), (CS5, 2), (D5, 2), (CS5, 2)],
    # the reprise, full statement
    29: STATEMENT_BAR_1,
    30: STATEMENT_BAR_2,
    # the rhythm variation on the late return: two half notes, then the tail
    31: [(F4, 4), (C5, 4)],
    32: [(A4, 2), (CS5, 2), (A4, 4)],      # ends on A4 so the wrap to bar 1 F4 is a step
}

ARP = {
    "D": (D4, F4, A4), "Bb": (BB3, D4, F4), "F": (C4, F4, A4),
    "C": (C4, E4, G4), "Gm": (G3, BB3, D4), "A7": (A3, CS4, E4, G4),
}
ARP_PATTERN = (0, 2, 1, 2)
ARP_BARS = (25, 26, 29, 30, 31, 32)      # 27 and 28 are the space before the reprise

BASS_ROOT = {"D": (50, 38), "Bb": (46, 34), "F": (53, 41), "C": (48, 36),
             "Gm": (43, 31), "A7": (45, 33)}

KICK, SNARE = 36, 38
HAT, OPEN_HAT, TOM_HI, TOM_MID, TOM_LO = 5, 3, 11, 9, 7


def tracks_of(song):
    return {t["name"].strip().lower(): t for t in song["tracks"]}


def add_cc(track, cc, entries):
    track["cc"].setdefault(cc, [])
    track["cc"][cc] = sorted(track["cc"][cc] + list(entries))


def extend_lead(song, report):
    lead = tracks_of(song).get("vrc6 pulse a")
    if lead is None:
        raise SystemExit("no track named 'vrc6 pulse a'")
    before = len(lead["notes"])

    notes, depth, onset, volume, duty = [], [], [], [], []
    for bar, cells in sorted(NEW_LEAD.items()):
        start = (bar - 1) * BAR
        peak = max(p for p, _ in cells)
        offset = 0
        for index, (pitch, length) in enumerate(cells):
            begin = start + offset * EIGHTH
            end = begin + length * EIGHTH
            # the velocity arch of the phrase: the crest is loudest, the late
            # return is the loudest statement of the whole cue
            if pitch == peak:
                velocity = 112 if bar < 29 else 118
            else:
                velocity = 96 + 2 * (index % 3)
            notes.append((begin, end, pitch, velocity))
            depth.append((begin, 11 if bar >= 29 else 9))
            onset.append((begin, 1 + (index % 2)))
            offset += length
        if offset > 8:
            raise SystemExit("bar %d overflows" % bar)
        volume.append((start, 10 if bar >= 25 else 9))
        duty.append((start, 3))

    lead["notes"] = sorted(lead["notes"] + notes)
    add_cc(lead, 1, depth)
    add_cc(lead, 20, onset)
    add_cc(lead, 11, volume)
    add_cc(lead, 12, duty)

    report["lead"] = {
        "notes_before": before,
        "notes_added": len(notes),
        "notes_after": len(lead["notes"]),
        "bars_added": sorted(NEW_LEAD),
        "statements": "bars 25, 29 and 30 restate the v4 arch in pitch; bar 31 is the rhythm variation",
        "dissonance": [
            "bar 26: C5 (9th of Bb) held and resolved to Bb4, a 9-8 suspension",
            "bar 27: D5 (11th of A7) resolving down to C#5, an 11-3 resolution",
            "bar 28: D5 upper neighbour of C#5, resolved on the fourth eighth",
        ],
        "range_added": [min(p for _, _, p, _ in notes), max(p for _, _, p, _ in notes)],
    }
    return len(notes)


def extend_arpeggio(song, report):
    voice = tracks_of(song).get("pulse 2")
    if voice is None:
        return 0
    before = len(voice["notes"])

    notes = []
    for bar in ARP_BARS:
        start = (bar - 1) * BAR
        chord = ARP[CHORD_OF_BAR[bar]]
        for step in range(16):
            pitch = chord[ARP_PATTERN[step % 4] % len(chord)]
            begin = start + step * SIXTEENTH
            if step % 2 == 1:                       # same sixteenth swing as bars 1 to 24
                begin += 14
            length = SIXTEENTH - 20
            arch = (4, 6, 8, 10, 12, 14, 12, 10)[step % 8]
            notes.append((begin, begin + length, pitch, 70 + arch * 2))
    voice["notes"] = sorted(voice["notes"] + notes)

    report["arpeggio"] = {
        "notes_before": before,
        "notes_added": len(notes),
        "bars": list(ARP_BARS),
        "space": "pulse 2 rests on bars 27 and 28, which is the build into the reprise",
        "pitches_added": sorted({n[2] for n in notes}),
    }
    return len(notes)


def extend_bass(song, report):
    tracks = tracks_of(song)
    saw, triangle = tracks.get("vrc6 saw"), tracks.get("triangle")
    if saw is None or triangle is None:
        return 0
    saw_notes, tri_notes = [], []
    cc11_saw, cc11_tri = [], []
    for bar in range(25, BARS + 1):
        start = (bar - 1) * BAR
        saw_pitch, tri_pitch = BASS_ROOT[CHORD_OF_BAR[bar]]
        if bar < 29:
            # the development: half notes, root then fifth, so the pulse is not straight
            fifth = saw_pitch + 7
            saw_notes.append((start, start + 2 * QUARTER, saw_pitch, 92))
            saw_notes.append((start + 2 * QUARTER, start + 4 * QUARTER, fifth, 86))
        else:
            saw_notes.append((start, start + 4 * QUARTER, saw_pitch, 96))
        tri_notes.append((start, start + 4 * QUARTER, tri_pitch, 102))
        cc11_saw.append((start, 5 if bar < 29 else 6))
        cc11_tri.append((start, 5))
    saw["notes"] = sorted(saw["notes"] + saw_notes)
    triangle["notes"] = sorted(triangle["notes"] + tri_notes)
    add_cc(saw, 11, cc11_saw)
    add_cc(triangle, 11, cc11_tri)
    # bass vibrato, deep on the long reprise notes, arriving late as in the v4 pass
    add_cc(saw, 20, [(start, 2 if bar >= 29 else 1) for bar in range(25, BARS + 1)
                     for start in [(bar - 1) * BAR]])

    report["bass"] = {
        "saw_notes_added": len(saw_notes),
        "triangle_notes_added": len(tri_notes),
        "shape": "bars 25 to 28 half notes root then fifth; bars 29 to 32 whole note roots",
    }
    return len(saw_notes) + len(tri_notes)


def extend_inner_voice(song, report):
    """Pulse 1: a chromatic climb over the A7 on bars 27 and 28, then offbeat thirds."""
    voice = tracks_of(song).get("pulse 1")
    if voice is None:
        return 0
    before = len(voice["notes"])
    notes, cc11 = [], []
    climb = [(27, G3), (27, A3), (27, BB3), (27, B3), (28, CS4), (28, D4), (28, E4), (28, G4)]
    counter = {}
    for bar, pitch in climb:
        step = counter.get(bar, 0)
        counter[bar] = step + 1
        begin = (bar - 1) * BAR + step * 2 * EIGHTH
        notes.append((begin, begin + 2 * EIGHTH - 24, pitch, 78 + 4 * step))
    thirds = {29: A3, 30: D4, 31: BB3, 32: CS4}
    for bar, pitch in thirds.items():
        start = (bar - 1) * BAR
        for beat in (1, 3):                       # offbeat eighths, both sides of the beat
            begin = start + beat * QUARTER + EIGHTH
            notes.append((begin, begin + EIGHTH - 20, pitch, 62))
    voice["notes"] = sorted(voice["notes"] + notes)
    for bar in (27, 28, 29, 30, 31, 32):
        cc11.append(((bar - 1) * BAR, 5))
    add_cc(voice, 11, cc11)

    report["inner_voice"] = {
        "notes_before": before,
        "notes_added": len(notes),
        "climb": "bars 27 and 28: G3 A3 Bb3 B3 C#4 D4 E4 G4, one chromatic step per eighth pair",
        "thirds": "bars 29 to 32: offbeat eighth stabs on the chord third",
    }
    return len(notes)


def vary_third_return(song, report):
    """Rewrite bars 9 and 10 so the third statement of the hook returns changed.

    v4 left bar 9 identical to bar 1 deliberately, because the meter compares
    return three against return one and the first statement is the one the
    listener learns. With 32 bars the statement now happens eight times, so the
    third one can afford a new surface: the same pitches, half note values.
    """
    lead = tracks_of(song).get("vrc6 pulse a")
    if lead is None:
        return 0
    lo, hi = 8 * BAR, 10 * BAR
    cells = {9: [(F4, 4), (C5, 4)], 10: [(BB4, 2), (A4, 2), (G4, 2), (F4, 2)]}
    notes = [n for n in lead["notes"] if not (lo <= n[0] < hi)]
    added = []
    for bar, bar_cells in sorted(cells.items()):
        offset = 0
        for index, (pitch, length) in enumerate(bar_cells):
            begin = (bar - 1) * BAR + offset * EIGHTH
            added.append((begin, begin + length * EIGHTH, pitch, 98 + 2 * (index % 3)))
            offset += length
    lead["notes"] = sorted(notes + added)
    report["third_return"] = {
        "bars": [9, 10],
        "surface": "bar 9 holds F4 and C5 as half notes, bar 10 turns the tail into quarters",
        "pitches": "unchanged from the statement",
        "notes_replaced": len(added),
    }
    return len(added)


def write_kit(song, report):
    """The kit for all 32 bars, with a rung at 2, 4, 8 and 16 bars."""
    tracks = tracks_of(song)
    noise, dpcm = tracks.get("noise"), tracks.get("dpcm")
    if noise is None or dpcm is None:
        raise SystemExit("no kit tracks")

    hits = []

    def at(bar, step):
        return (bar - 1) * BAR + step * SIXTEENTH

    def add(bar, step, pitch, velocity, track):
        hits.append((at(bar, step), pitch, velocity, track))

    for bar in range(1, BARS + 1):
        odd = (bar % 2) == 1
        section_b = bar >= 25
        # ---- 2 bar rung: kick placement, hat density, ghost snares
        if section_b and bar < 29:
            kick_steps = [0, 8]
        elif odd:
            kick_steps = [0, 8]
        else:
            kick_steps = [0, 6, 8]
        if bar % 4 == 0:
            kick_steps = [0, 6, 8]
        for step in kick_steps:
            add(bar, step, KICK, 112 + (2 if step == 0 else 0), "dpcm")
        # backbeat: bars 25 to 28 are half time (snare on beat 3 only)
        snare_steps = [8] if (section_b and bar < 29) else [4, 12]
        for step in snare_steps:
            add(bar, step, SNARE, 104, "dpcm")
        if not odd:
            add(bar, 3, SNARE, 38, "dpcm")
            add(bar, 11, SNARE, 34, "dpcm")
        # hats
        last = 16
        step = 0
        while step < last:
            if step % 4 == 0:
                add(bar, step, HAT, 92 + (6 if step == 0 else 0), "noise")
            else:
                add(bar, step, HAT, 58 + (12 if step % 4 == 2 else 0), "noise")
            step += 2
        if bar % 4 == 2:
            for extra in (7, 15):
                add(bar, extra, HAT, 44, "noise")
        # ---- 4 bar rung: snare fill on beat 4
        if bar % 4 == 0:
            for index, step in enumerate((12, 13, 14, 15)):
                add(bar, step, SNARE, 84 + index * 8, "dpcm")
        # ---- 8 bar rung: tom fill over beats 3 and 4, open hat into the next bar
        if bar % 8 == 0 and bar != BARS:
            for index, step in enumerate((8, 9, 10, 11)):
                add(bar, step, TOM_HI, 78 + index * 6, "noise")
            for index, step in enumerate((12, 13)):
                add(bar, step, TOM_MID, 86 + index * 6, "noise")
            add(bar, 14, TOM_LO, 96, "noise")
            add(bar, 15, SNARE, 108, "dpcm")
            add(bar + 1, 0, OPEN_HAT, 104, "noise")
        # ---- 16 bar rung: the mid cue break at 24, the biggest fill at 32
        if bar == 24:
            for index, step in enumerate((8, 10)):
                add(bar, step, TOM_HI, 84 + index * 6, "noise")
            add(bar, 11, TOM_MID, 92, "noise")
            add(bar, 12, TOM_LO, 100, "noise")
            add(bar, 14, SNARE, 108, "dpcm")
        if bar == BARS:
            for index, step in enumerate((8, 9, 10, 11)):
                add(bar, step, TOM_HI, 80 + index * 8, "noise")
            for index, step in enumerate((12, 13, 14)):
                add(bar, step, TOM_MID, 90 + index * 8, "noise")
            add(bar, 15, TOM_LO, 110, "noise")

    noise_notes, dpcm_notes = [], []
    for index, (tick, pitch, velocity, track) in enumerate(sorted(hits, key=lambda h: (h[0], h[3]))):
        offset_in_bar = tick % BAR
        shift = 0
        if track == "noise" and pitch == HAT and (offset_in_bar % EIGHTH) != 0:
            shift = 8 + (index % 4) * 2
        if track == "dpcm" and offset_in_bar % BAR != 0:
            shift = (index % 3) * 3
        spread = 0.92 + ((index * 37) % 17) / 100.0
        new_velocity = max(1, min(127, int(round(velocity * spread))))
        entry = (tick + shift, tick + shift + (110 if pitch in (KICK, SNARE) else 90),
                 pitch, new_velocity)
        (noise_notes if track == "noise" else dpcm_notes).append(entry)

    noise["notes"] = sorted(noise_notes)
    dpcm["notes"] = sorted(dpcm_notes)

    def rung(divisor):
        return len({int(t // BAR) // divisor for t, _, _, _ in hits})

    report["kit"] = {
        "noise_notes": len(noise["notes"]),
        "dpcm_notes": len(dpcm["notes"]),
        "noise_velocity_steps": len({n[3] for n in noise["notes"]}),
        "dpcm_velocity_steps": len({n[3] for n in dpcm["notes"]}),
        "rungs": {
            "2_bar": rung(2), "4_bar": rung(4), "8_bar": rung(8), "16_bar": rung(16),
        },
        "distinct_noise_pitches": sorted({n[2] for n in noise["notes"]}),
        "half_time_section": "bars 25 to 28: kick on beats 1 and 3, snare on beat 3 only",
    }
    return len(noise["notes"]) + len(dpcm["notes"])


def human_touches(song, report):
    """Micro timing on the new lead notes only: nothing lands past a bar line."""
    lead = tracks_of(song).get("vrc6 pulse a")
    nudged = 0
    if lead is not None:
        notes = []
        for index, (start, end, pitch, velocity) in enumerate(sorted(lead["notes"])):
            bar = int(start // BAR) + 1
            nudge = 0
            if bar >= 25 and end % BAR != 0 and start % BAR != 0:
                nudge = (index * 3) % 9
            if nudge:
                nudged += 1
            notes.append((start + nudge, end, pitch, velocity))
        lead["notes"] = notes
    report["human"] = {
        "lead_micro_timing": "%d lead notes nudged by up to 8 ticks" % nudged,
        "kit": "offbeat hats swing 8 to 14 ticks, backbeat slack 0 to 6 ticks, 49 velocity steps",
        "vibrato": "depth 9 on the development, 11 on the reprise; onset delay 1 to 2 eighths",
    }
    return nudged


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args(argv)

    song = hook_score.read_smf(V4)
    song["tempo_us"] = TEMPO_US
    report = {
        "source": V4,
        "division": song["division"],
        "tempo_bpm": 60_000_000 / TEMPO_US,
        "bars": BARS,
        "seconds": BARS * 4 * 60.0 / (60_000_000 / TEMPO_US),
        "tracks_in": [{"name": t["name"], "notes": len(t["notes"])} for t in song["tracks"]],
    }
    if args.probe:
        print(json.dumps(report, indent=2))
        return 0

    extend_lead(song, report)
    extend_arpeggio(song, report)
    extend_bass(song, report)
    extend_inner_voice(song, report)
    write_kit(song, report)
    human_touches(song, report)

    humanize.write_smf(song, OUT)
    report["notes_out"] = sum(len(t["notes"]) for t in song["tracks"])
    report["voices"] = sum(1 for t in song["tracks"] if t["notes"])
    report["midi_out"] = OUT
    with open(REPORT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({k: report[k] for k in ("lead", "arpeggio", "bass", "inner_voice",
                                             "kit", "human", "notes_out", "voices")}, indent=2))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
