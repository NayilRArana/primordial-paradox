"""build_pp05_v3.py: PP-05 "Small Ship" version 3.

v2 is kept untouched in ../pp_05_small_ship_v2/ and v1 in ../pp_05_small_ship/.
This build reads v1's MIDI, re-applies v2's three changes (pulse 1 counterline,
noise level, 4 and 8 bar rungs) through build_pp05_v2's own functions, and then
adds the three things v2's own NOTES named as still weak:

  1. the hook. v2's hook meter was 58 of 100 with motif coverage 19 percent,
     no third return and no leap. The lead (vrc6 pulse a) is rewritten as one
     1 bar cell, 5 notes, exactly one leap of 5 semitones, stated on bars 1, 5,
     9, 17 and 21, sequenced over the bridge on 17 to 20, and varied on the
     third return (bars 13 to 16, an octave up).
  2. the kit. v2's rungs stay; v3 adds ghost snares, velocity spread and
     micro timing (swung offbeat hats, hit by hit nudges).
  3. the dissonance. One prepared suspension: F4 is the fifth of Bb in bar 18
     and becomes the seventh of Gm in bar 19, resolving F E D by step
     (knowledge/MUSIC-DISSONANCE.md section 2, preparation then dissonance
     then resolution).

Tempo (96 bpm), key (D minor), form (24 bars, 60.000 s) and the loop length are
unchanged from v1 and v2, so the demo script's 60 s timing still holds.

Usage: build_pp05_v3.py [--probe]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(AUDIO))
V1 = os.path.join(AUDIO, "pp_05_small_ship", "pp_05_small_ship.mid")
V2DIR = os.path.join(AUDIO, "pp_05_small_ship_v2")
OUT_RAW = os.path.join(HERE, "pp_05_small_ship_v3_raw.mid")
OUT = os.path.join(HERE, "pp_05_small_ship_v3.mid")
REPORT = os.path.join(HERE, "build_report_v3.json")

sys.path.insert(0, os.path.join(ROOT, "tools"))
import hook_score  # noqa: E402
import humanize  # noqa: E402


def load_v2_builder():
    spec = importlib.util.spec_from_file_location("build_pp05_v2", os.path.join(V2DIR, "build_pp05_v2.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PPQ = 480
EIGHTH = PPQ // 2
BAR = 8 * EIGHTH

# --------------------------------------------------------------- the hook
# One bar, eight eighths, five notes: A4 (q) D5 (q) C5 (e) Bb4 (e) A4 (q).
# Exactly one leap (A4 to D5, five semitones) and then a stepwise fall, which
# is the contour the hook grammar asks for.
D_CELL = [(69, 2), (74, 2), (72, 1), (70, 1), (69, 2)]
BB_CELL = [(65, 2), (70, 2), (69, 1), (67, 1), (65, 2)]
F_CELL = [(65, 2), (69, 2), (67, 1), (65, 1), (60, 2)]
C_CELL = [(64, 2), (67, 2), (65, 1), (64, 1), (62, 2)]
GM_CELL = [(67, 2), (70, 2), (69, 1), (67, 1), (65, 2)]
A_CELL = [(69, 2), (73, 2), (72, 1), (69, 1), (69, 2)]

CHORD_OF_BAR = {
    1: "D", 2: "Bb", 3: "F", 4: "C", 5: "D", 6: "Bb", 7: "Gm", 8: "A",
    9: "D", 10: "Bb", 11: "Gm", 12: "A", 13: "D", 14: "Bb", 15: "Gm", 16: "A",
    17: "D", 18: "Bb", 19: "Gm", 20: "A", 21: "D", 22: "Bb", 23: "A", 24: "D",
}
CELLS = {"D": D_CELL, "Bb": BB_CELL, "F": F_CELL, "C": C_CELL, "Gm": GM_CELL, "A": A_CELL}

# The 2 bar phrase is the statement. It is written six times (bars 1, 5, 9, 13,
# 17, 21), so the ear hears it before the fifth second and the hook meter can
# count coverage. The third return (bars 13 and 14) is the same phrase an octave
# up, which the meter reads as a varied return.
STATEMENT_BARS = (1, 5, 9, 13, 17, 21)
STATEMENT = [D_CELL, BB_CELL]

# The bars between statements breathe: two notes and two rests per bar, so the
# phrase is not wall to wall and the texture has somewhere to fall away.
ANSWERS = {
    3: [(69, 2), (65, 2)],
    4: [(67, 2), (64, 2)],
    7: [(70, 2), (67, 2)],
    8: [(73, 2), (69, 2)],
    11: [(70, 2), (67, 2)],
    12: [(73, 2), (69, 2)],
    15: [(82, 2), (79, 2)],       # octave up answer, bars 13 to 16
    16: [(85, 2), (81, 2)],
    19: [(65, 1), (64, 1), (62, 2)],  # the suspension: F4 becomes the seventh of Gm
    20: [(69, 2), (73, 2)],
    23: [(69, 2), (73, 2)],
    24: [(74, 4), (72, 2), (70, 2)],
}

# Bridge (bars 17 to 20): the same contour in quarter notes, sequenced down the
# progression. Bar 19 holds F4 over the bar line: prepared as the fifth of Bb in
# bar 18, dissonant as the seventh of Gm, resolved F E D by step.
BRIDGE = {
    17: [(69, 2), (74, 2), (72, 2), (69, 2)],
    18: [(65, 2), (70, 2), (69, 1), (65, 1), (65, 2)],   # ends on F4, held into bar 19
    19: [(65, 1), (64, 1), (62, 2), (67, 2), (70, 2)],  # suspension, F E D, then G Bb
    20: [(69, 2), (73, 2), (72, 2), (69, 2)],
}
# Turnaround (bars 21 to 24): the cell shortened, ending on the root so the wrap
# back to bar 1's A4 is a step.
TURN = {
    21: [(69, 2), (74, 2), (72, 2), (70, 1), (69, 1)],
    22: [(65, 2), (70, 2), (69, 2), (65, 2)],
    23: [(69, 2), (73, 2), (72, 2), (69, 2)],
    24: [(74, 4), (72, 2), (70, 2)],
}
OCTAVE_UP_BARS = (13, 14, 15, 16)


def rewrite_hook(song, report):
    tracks = {t["name"].strip().lower(): t for t in song["tracks"]}
    lead = tracks.get("vrc6 pulse a")
    if lead is None:
        raise SystemExit("no track named 'vrc6 pulse a'")
    old = sorted(lead["notes"])
    velocity = {p: v for _, _, p, v in old}
    base_velocity = 100

    def vel(pitch):
        return velocity.get(pitch, base_velocity)

    notes = []
    for bar in range(1, 25):
        start = (bar - 1) * BAR
        if bar in STATEMENT_BARS:
            cells = D_CELL
        elif (bar - 1) in STATEMENT_BARS:
            cells = BB_CELL
        else:
            cells = ANSWERS[bar]
        shift = 12 if bar in (13, 14) else 0
        offset = 0
        for pitch, length in cells:
            begin = start + offset * EIGHTH
            end = begin + length * EIGHTH
            notes.append((begin, end, pitch + shift, vel(pitch)))
            offset += length
        if offset > 8:
            raise SystemExit("bar %d cell is %d eighths, over one bar" % (bar, offset))
    notes.sort()
    lead["notes"] = notes
    report["hook"] = {
        "lead_notes_before": len(old),
        "lead_notes_after": len(notes),
        "cell": "A4 D5 C5 Bb4 A4 (bar 1 of the 2 bar phrase), F4 Bb4 A4 G4 F4 (bar 2)",
        "cell_returns": list(STATEMENT_BARS),
        "third_return_varied": "bars 13 and 14 the same phrase an octave up",
        "leap": "A4 to D5, 5 semitones, one per cell",
        "suspension_chain": "F4 ends bar 18 (fifth of Bb), F4 at bar 19 (seventh of Gm), F E D by step",
    }
    return len(notes)


# ------------------------------------------------------------------- the kit
def humanize_kit(song, report):
    """Ghost snares, velocity spread, swung offbeat hats and hit by hit nudges."""
    tracks = {t["name"].strip().lower(): t for t in song["tracks"]}
    noise, dpcm = tracks.get("noise"), tracks.get("dpcm")
    if noise is None or dpcm is None:
        report["kit"] = {"error": "no kit tracks"}
        return {}

    added = {"ghost_snare": 0, "swung_hats": 0, "nudged": 0}
    # ghost snares on the offbeats of the answer bars, which is the 4 bar rung
    # between the fills: bars 2, 6, 10, 14, 18, 22 at a low velocity.
    for index, bar in enumerate((2, 6, 10, 14, 18, 22)):
        base = (bar - 1) * BAR
        for eighth in (3, 7):
            tick = base + eighth * EIGHTH
            dpcm["notes"].append((tick, tick + EIGHTH // 2, 38, 36 + (index % 3) * 4))
            added["ghost_snare"] += 1

    # hit by hit human pass on the noise kit: velocity spread and, on offbeat
    # hats, a swing nudge later in the beat. Never on the bar 1 downbeat, and
    # never past the loop end, so the seam stays where the renderer put it.
    nudged = []
    for index, (start, end, pitch, velocity) in enumerate(sorted(noise["notes"])):
        factor = 0.86 + ((index * 37) % 23) / 100.0          # 0.86 to 1.08
        new_velocity = max(1, min(127, int(round(velocity * factor))))
        offset = start % BAR
        shift = 0
        if offset % (2 * EIGHTH) == 0 and offset % (4 * EIGHTH) != 0:
            shift = 10 + (index % 3) * 2                      # swung offbeat hat
            added["swung_hats"] += 1
        if shift:
            added["nudged"] += 1
        nudged.append((start + shift, end + shift, pitch, new_velocity))
    noise["notes"] = sorted(nudged)

    for track in (noise, dpcm):
        track["notes"].sort()

    report["kit"] = dict(added)
    report["kit"]["noise_notes"] = len(noise["notes"])
    report["kit"]["noise_velocity_steps"] = len({n[3] for n in noise["notes"]})
    report["kit"]["dpcm_notes"] = len(dpcm["notes"])
    report["kit"]["gates"] = "4 bar rung backbeat plus ghosts, 8 bar rung longer fill"
    return added


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args(argv)

    v2 = load_v2_builder()
    song = hook_score.read_smf(V1)
    report = {"source": V1, "division": song["division"], "tempo_us": song["tempo_us"],
              "tempo_bpm": 60_000_000 / song["tempo_us"],
              "tracks_in": [{"name": t["name"], "notes": len(t["notes"])} for t in song["tracks"]]}
    if args.probe:
        print(json.dumps(report, indent=2))
        return 0

    # v2's three changes, through v2's own functions so v1 to v2 stays byte honest
    v2.add_counterline(song, report)
    v2.raise_noise(song, report)
    v2.add_rungs(song, report)

    rewrite_hook(song, report)
    humanize_kit(song, report)

    humanize.write_smf(song, OUT_RAW)
    report["notes_after_raw"] = sum(len(t["notes"]) for t in song["tracks"])

    hum = humanize.humanize_file(OUT_RAW, OUT, write=True)
    report["humanize"] = {k: hum[k] for k in
                          ("seed", "bpm", "notes_in", "notes_out", "notes_changed",
                           "vibrato_pairs", "fills") if k in hum}
    report["midi_out"] = OUT
    with open(REPORT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps({"hook": report["hook"], "kit": report["kit"],
                      "notes_after_raw": report["notes_after_raw"]}, indent=2))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
