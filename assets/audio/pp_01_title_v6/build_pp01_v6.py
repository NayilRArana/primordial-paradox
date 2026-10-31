"""build_pp01_v6.py: PP-01 "Title Theme" version 6, card AUTO-MUSIC-NEXT (t_9b5ccc92).

The v5 master (`assets/audio/pp_01_title/`, landed by land_asset.py on 2026-10-22 19:10) is
untouched. It is the floor of the hook meter: 59 of 100, the lowest of the ten cues, with
motif coverage, contour, loop length and the third return all under half. The ear has it at
31 of 60 on `gemini-3.5-flash-lite` (data/ear_ledger.csv, 2026-10-23T02:05:36Z), also low.

What this build changes, and nothing else:

  1. The lead (vrc6 pulse a) is rewritten as twelve statements of the score's own two bar
     phrase: K, the Kronos family call, then K2, its answer. Both cells are `score_v5.yaml`'s
     notes, not new material. Statement 3 is opened up (the tail becomes a quarter) so the
     phrase returns changed, and the W bell still ends each four bar phrase.
  2. Only the lead and the kit are rewritten. Pulse 1 arpeggios, pulse 2 echo, vrc6 pulse b
     thirds, vrc6 saw oom pah and the triangle bass are v5's notes, untouched.
  3. The kit (noise + dpcm) is written bar by bar: a 2 bar rung (hat density), a 4 bar rung
     (fill on the last beat), an 8 bar rung (tom run and a crash on the next downbeat), and
     the trio's cold half keeps one kick and no hats.
  4. The octave transposition in A prime and B prime is dropped, because it pushed the melody
     range past the grammar's 19 semitones and split the motif into two unrelated octaves.
     The variation is carried by the thirds on vrc6 pulse b, which are v5's.

Key, time, tempo, bar count and the loop point are v5's: A minor, 3/4, 126 bpm, 52 bars, loop
from bar 5 to bar 52. 126 bpm is the card's "126 bpm family" line and the score's own tempo.

Usage: build_pp01_v6.py [--probe]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(AUDIO))
SRC = os.path.join(AUDIO, "pp_01_title", "pp_01_title.mid")
OUT = os.path.join(HERE, "pp_01_title_v6.mid")
REPORT = os.path.join(HERE, "build_report_v6.json")

sys.path.insert(0, os.path.join(ROOT, "tools"))
import hook_score  # noqa: E402
import humanize  # noqa: E402

PPQ = 480
EIGHTH = PPQ // 2
BAR = 6 * EIGHTH                 # 3/4
BARS = 52
LOOP_START_BAR = 5               # score_v5.yaml: loop_start_section A
LOOP_BARS = 48

# ---------------------------------------------------------------- the score's cells
K = [(76, 3), (72, 1), (74, 1), (76, 1)]            # E5 dotted quarter, C5 D5 E5: the family call
K2 = [(71, 3), (68, 1), (69, 1), (71, 1)]           # B4, G#4 A4 B4 over the dominant: the answer
K_OPEN = [(76, 3), (72, 1), (74, 2)]                # statement 3, the tail opened
K2_OPEN = [(71, 3), (68, 1), (69, 2)]
W_DOM = [(71, 6)]                                   # the bell on the dominant
W_TON = [(69, 6)]                                   # the bell on the tonic
INTRO3 = [(76, 3), (74, 1), (72, 1), (71, 1)]       # v5 intro pickup, kept
INTRO4 = [(71, 6)]

# A (bars 5 to 12): four statements of K + K2, the third one opened, cadence on the dominant.
A_SECTION = [K, K2, K, W_DOM, K_OPEN, K2_OPEN, K, W_TON]

# B (21 to 28) and the trio (37 to 44): v5's notes, bar for bar, so Z, P and H still sound.
B_SECTION = [
    [(67, 2), (72, 2), (76, 2)],                    # Z, rising arpeggio in C
    [(74, 3), (71, 3)],
    [(67, 2), (72, 2), (76, 2)],                    # Z again
    [(74, 4), (71, 2)],
    [(77, 3), (81, 3)],
    [(79, 3), (76, 3)],
    [(71, 3), (68, 3)],
    [(71, 4), None],                                # dominant, a two eighth rest
]
TRIO_SECTION = [
    [(64, 2), (67, 2), (71, 2)],                    # P, the tide rises
    [(76, 3), (74, 1), (71, 2)],                    # P, crest and fall
    [(71, 2), (75, 2), (78, 2)],                    # P over B7, tension
    [(76, 6)],                                      # W, the sea settles
    [(74, 2), (73, 2), None],                       # H, first prong and its gap
    [(69, 2), (68, 2), None],                       # H, second prong, a fourth lower
    [(71, 3), (68, 3)],
    [(71, 4), None],
]

# (first bar, section cells)
SECTIONS = [
    (1, [None, None, INTRO3, INTRO4]),
    (5, A_SECTION),
    (13, A_SECTION),                                # A prime: the same notes, thirds on pulse b
    (21, B_SECTION),
    (29, B_SECTION),                                # B prime: the same notes
    (37, TRIO_SECTION),
    (45, A_SECTION[:-1] + [W_DOM]),                 # A return, last bar on the dominant
]


def lead_notes():
    notes = []
    for first_bar, cells in SECTIONS:
        for index, cell in enumerate(cells):
            if not cell:
                continue
            bar = first_bar + index
            start = (bar - 1) * BAR
            cursor = 0
            for entry in cell:
                if entry is None:                      # a written rest, two eighths
                    cursor += 2
                    continue
                pitch, length = entry
                begin = start + cursor * EIGHTH
                cursor += length
                notes.append((begin, start + cursor * EIGHTH, pitch, 100))
    return notes


def rewrite_lead(song, report):
    tracks = {t["name"].strip().lower(): t for t in song["tracks"]}
    lead = tracks["vrc6 pulse a"]
    before = list(lead["notes"])
    notes = []
    for begin, end, pitch, _ in lead_notes():
        # velocity arch inside each statement: the first note of a cell is the accented one
        slot = begin % BAR
        if slot == 0:
            velocity = 108
        elif pitch >= 79:
            velocity = 104
        else:
            velocity = 94 + (begin // EIGHTH) % 5
        notes.append((begin, end, pitch, velocity))
    lead["notes"] = notes
    report["lead"] = {
        "before_notes": len(before),
        "after_notes": len(notes),
        "before_range_semitones": (max(n[2] for n in before) - min(n[2] for n in before)) if before else 0,
        "after_range_semitones": max(n[2] for n in notes) - min(n[2] for n in notes),
        "statements": 12,
    }
    return lead


# ---------------------------------------------------------------- the kit
HAT, OPEN_HAT, SNARE, TOM_HI, TOM_MID, TOM_LO = 12, 10, 38, 8, 6, 4
KICK = 36


def write_kit(song, report):
    tracks = {t["name"].strip().lower(): t for t in song["tracks"]}
    noise, dpcm = tracks["noise"], tracks["dpcm"]
    before = {"noise": len(noise["notes"]), "dpcm": len(dpcm["notes"])}
    noise["notes"], dpcm["notes"] = [], []

    def hit(track, bar, step, pitch, velocity, length=60):
        start = (bar - 1) * BAR + int(round(step * EIGHTH))
        track["notes"].append((start, start + length, pitch, velocity))

    for bar in range(1, BARS + 1):
        rung2 = bar % 2 == 0
        rung4 = bar % 4 == 0
        rung8 = bar % 8 == 0
        if bar <= 4:
            if bar == 4:
                hit(dpcm, bar, 4, KICK, 92)                # pickup into A
            continue
        if 41 <= bar <= 44:                                # trio, cold half, server hum
            hit(dpcm, bar, 0, KICK, 86 if not rung2 else 80)
            continue
        if 37 <= bar <= 40:                                # trio, sea half: washes, no backbeat
            for step in (1, 3, 5) if not rung2 else (0, 1, 2, 3, 4, 5):
                hit(noise, bar, step, HAT, 44 + (6 if step in (1, 5) else 0))
            hit(dpcm, bar, 0, KICK, 96)
            if rung4:
                hit(noise, bar, 5, OPEN_HAT, 58)
            if rung8:
                for index, step in enumerate((3, 3.5, 4, 4.5)):
                    hit(noise, bar, step, (TOM_HI, TOM_MID, TOM_LO, TOM_LO)[index], 70 - 4 * index)
            continue
        light = 21 <= bar <= 28                            # B: brighter, hats on every beat
        steps = (0, 2, 4) if not rung2 else (0, 1, 2, 3, 4, 5)
        for step in steps:
            accent = 12 if step in (0, 2, 4) else 0
            hit(noise, bar, step, HAT, (56 if light else 52) + accent)
        hit(dpcm, bar, 0, KICK, 104 if bar % 8 in (5, 1) else 98)
        if bar % 4 == 3:
            hit(dpcm, bar, 2, KICK, 88)                    # the 4 bar rung: a second kick
        if not light:
            hit(dpcm, bar, 4, SNARE, 100 if not rung2 else 94)
        if light and bar % 2 == 1:
            hit(noise, bar, 4, SNARE, 96)
        if rung4:
            for step in (4, 4.5, 5):
                hit(noise, bar, step, OPEN_HAT, 68)
            hit(dpcm, bar, 5, SNARE, 90)
        if rung8:
            for index, step in enumerate((3, 3.5, 4, 4.5, 5)):
                hit(noise, bar, step, (TOM_HI, TOM_HI, TOM_MID, TOM_LO, TOM_LO)[index],
                    74 - 3 * index)
        if bar in (12, 20, 28, 36):
            hit(noise, bar, 5, OPEN_HAT, 76)               # into the next section
        if bar in (13, 21, 29, 37, 45):
            hit(noise, bar, 0, OPEN_HAT, 84)               # crash on the section downbeat
    for track, seed in ((noise, 5), (dpcm, 9)):
        shaped = []
        for index, (start, end, pitch, velocity) in enumerate(sorted(track["notes"])):
            shift = ((index * seed) % 5) - 2
            if (start // EIGHTH) % 6 == 0:
                shift = 0                                  # downbeats stay on the grid
            shaped.append((max(0, start + shift), max(0, end + shift), pitch,
                           max(30, min(127, velocity + ((index * seed) % 7) - 3))))
        track["notes"] = sorted(shaped)
    report["kit"] = {
        "noise_before": before["noise"], "noise_after": len(noise["notes"]),
        "dpcm_before": before["dpcm"], "dpcm_after": len(dpcm["notes"]),
        "noise_pitches": sorted({n[2] for n in noise["notes"]}),
        "rungs": "2 bar (hat density), 4 bar (open hat fill and a second kick on every 4th bar), "
                 "8 bar (five hit tom run, crash into 13, 21, 29, 37, 45), trio cold half one kick and no hats",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args(argv)
    song = hook_score.read_smf(SRC)
    report = {
        "source": SRC,
        "division": song["division"],
        "tempo_bpm": 60_000_000 / song["tempo_us"],
        "time_sig": list(song["time_sig"]),
        "loop": "bar %d for %d bars" % (LOOP_START_BAR, LOOP_BARS),
        "tracks_in": [{"name": t["name"], "notes": len(t["notes"])} for t in song["tracks"]],
    }
    before = hook_score.score_file(SRC, track="vrc6 pulse a")
    report["hook_before"] = {k: before[k] for k in ("score", "weakest")}
    rewrite_lead(song, report)
    write_kit(song, report)
    humanize.write_smf(song, OUT)
    after = hook_score.score_file(OUT, track="vrc6 pulse a")
    report["hook_after"] = {c["key"]: [c["measured"], c["pass"]] for c in after["criteria"]}
    report["hook_after_score"] = after["score"]
    report["midi_out"] = OUT
    with open(REPORT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print("before", before["score"], [c["key"] for c in before["criteria"] if not c["pass"]])
    print("after ", after["score"])
    for c in after["criteria"]:
        print("  %-22s %3s %s" % (c["key"], c["points"], c["measured"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
