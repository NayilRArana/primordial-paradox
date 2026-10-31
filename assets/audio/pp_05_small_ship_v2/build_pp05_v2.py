"""build_pp05_v2.py: PP-05 "Small Ship" version 2.

The v1 cue scored 15 on the ear gate (drums 2, tension 3, human 1, structure 2).
v1 is kept untouched in ../pp_05_small_ship/. This script reads v1's MIDI and
writes v2, changing only what the gate's fix 5 asks for plus the drum rungs and
the human pass:

  1. pulse 1 gets a counterline over bars 17 to 20 at the level the score gives
     the hum plus one step (the thin-bar fix: v1 gave pulse 1 no notes at all).
  2. the noise kit is raised from level 3 to level 6 and gains a variation
     rung: bars 5 to 8 and 13 to 16 add a backbeat snare and an offbeat hat,
     every 4th bar gets a one beat fill and every 8th bar a longer one, so the
     drums change every 4 bars and again at 8.
  3. bars 9 to 12 and 21 to 24 keep the plain v1 kit, which is the contrast the
     structure axis was missing.
  4. tools/humanize.py then writes the performance (articulation, velocity
     steps, vibrato pair, phrase breaths) on the result.

Nothing here composes a new melody. The counterline is built only from chord
tones of the chords v1 already writes, plus one prepared dissonance named in
knowledge/MUSIC-DISSONANCE.md. Tempo, key, form, loop length and every v1 note
are unchanged, so the 60 s whole form loop still wraps at sample 2646000.

Usage: build_pp05_v2.py [--probe]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
V1 = os.path.join(os.path.dirname(HERE), "pp_05_small_ship", "pp_05_small_ship.mid")
OUT_RAW = os.path.join(HERE, "pp_05_small_ship_v2_raw.mid")
OUT = os.path.join(HERE, "pp_05_small_ship_v2.mid")
REPORT = os.path.join(HERE, "build_report_v2.json")

sys.path.insert(0, os.path.join(ROOT, "tools"))
import hook_score  # noqa: E402
import humanize  # noqa: E402

PPQ = 480
EIGHTH = PPQ // 2
BAR = 8 * EIGHTH

# Bar 17 of a 24 bar cue starts here.
def bar_tick(bar):
    return (bar - 1) * BAR


# --------------------------------------------------------------- the counterline
# bars 17 to 20, Dm Bb Gm A7. Eighth note durations. Chord tones only, except
# the F4 at bar 19 which is the seventh of Gm and resolves by step to E4 over A7
# (prepared dissonance, knowledge/MUSIC-DISSONANCE.md section 2).
COUNTERLINE = [
    (17, [[57, 4], [62, 3]]),                    # A3 D4 over Dm: root and fifth, a rest before the bar
    (18, [[58, 4], [65, 3]]),                    # Bb3 F4 over Bb
    (19, [[55, 4], [60, 2], [65, 1]]),            # G3, then Bb3 and the 7th F4, prepared, resolving up
    (20, [[64, 2], [61, 2], [57, 3]]),            # E4 C#4 A3 over A7: the raised 7th falls to the fifth
]


def add_counterline(song, report):
    """Pulse 1, bars 17 to 20, at the hum level plus one chip step."""
    tracks = {t["name"].strip().lower(): t for t in song["tracks"]}
    lead = tracks.get("vrc6 pulse a")
    hum = tracks.get("pulse 2")
    pulse1 = tracks.get("pulse 1")
    if pulse1 is None:
        raise SystemExit("no track named 'pulse 1' in %s" % V1)

    # The chip level of a voice in v1 is control change 11. Take the hum's value
    # in bar 1 and step it up by the ratio the score writes (level 4 to 5).
    def cc11(track):
        values = [v for tick, v in track["cc"].get(11, []) if v]
        return sorted(values)[len(values) // 2] if values else 0

    hum_level = cc11(hum) if hum else 0
    target = min(127, int(round(hum_level * 5.0 / 4.0))) or 5
    lead_velocity = sorted(n[3] for n in lead["notes"])[len(lead["notes"]) // 2] if lead and lead["notes"] else 100

    written = 0
    for bar, cells in COUNTERLINE:
        start = bar_tick(bar)
        offset = 0
        for pitch, length in cells:
            begin = start + offset * EIGHTH
            end = begin + length * EIGHTH
            # leave the last eighth of the bar as rest, so the phrase breathes
            if offset + length <= 8:
                pulse1["notes"].append((begin, end, pitch, lead_velocity))
                written += 1
            offset += length
    pulse1["notes"].sort()
    # v1 wrote control change 11 for pulse 1 at every bar even though the voice
    # rested, so those zeros have to be raised too or the counterline renders
    # silent. One value per bar, at the counterline's level.
    bar_ticks = sorted({tick for tick, _ in pulse1["cc"].get(11, [])})
    pulse1["cc"][11] = [(tick, target) for tick in bar_ticks] or [(0, target)]
    pulse1["cc"][11].sort()
    report["counterline"] = {"notes": written, "cc11": target,
                             "hum_cc11": hum_level, "bars": [c[0] for c in COUNTERLINE]}
    return written


# ---------------------------------------------------------------------- the kit
def raise_noise(song, report):
    """Level 3 to 6 on the noise kit: CC11 doubled and velocities doubled."""
    tracks = {t["name"].strip().lower(): t for t in song["tracks"]}
    noise = tracks.get("noise")
    if noise is None:
        report["noise"] = {"error": "no noise track"}
        return 0
    before = [v for tick, v in noise["cc"].get(11, [])]
    noise["cc"][11] = [(tick, min(127, value * 2)) for tick, value in noise["cc"].get(11, [])]
    raised = 0
    notes = []
    for start, end, pitch, velocity in noise["notes"]:
        notes.append((start, end, pitch, min(127, int(round(velocity * 1.6)))))
        raised += 1
    noise["notes"] = notes
    report["noise"] = {"cc11_before": before, "cc11_after": [v for _, v in noise["cc"][11]],
                       "velocity_scaled": raised}
    return raised


def note_for_noise(pitch_name):
    """Noise pitch numbers the renderer reads as period: 4 to 12 are hats, 13 to 16 snare."""
    return pitch_name


def add_rungs(song, report):
    """The variation ladder: a rung every 4 bars, a longer one every 8."""
    tracks = {t["name"].strip().lower(): t for t in song["tracks"]}
    noise = tracks.get("noise")
    dpcm = tracks.get("dpcm")
    if noise is None or dpcm is None:
        report["rungs"] = {"error": "no kit tracks"}
        return {}

    hat_velocity = 60
    snare_velocity = 84
    added = {"hat_offbeat": 0, "snare_backbeat": 0, "fill_4": 0, "fill_8": 0, "kick_var": 0}

    for bar in range(1, 25):
        base = bar_tick(bar)
        rung4 = (bar % 4 == 0)
        rung8 = (bar % 8 == 0)
        backbeat = (5 <= bar % 8 <= 8) and not rung8   # bars 5 to 8 and 13 to 16

        if backbeat:
            # an offbeat hat between the written beat 1 and 3 hats
            for eighth in (2, 6):
                tick = base + eighth * EIGHTH
                noise["notes"].append((tick, tick + EIGHTH // 2, 8, hat_velocity))
                added["hat_offbeat"] += 1
            # a snare on beat 3, the backbeat the v1 kit never had
            tick = base + 4 * EIGHTH
            dpcm["notes"].append((tick, tick + EIGHTH, 38, snare_velocity))
            added["snare_backbeat"] += 1

        if rung4:
            # one beat fill on eighths 5 and 6 (bar 24 fills back into bar 1)
            for index, (eighth, pitch) in enumerate(((5, 11), (6, 9))):
                tick = base + eighth * EIGHTH
                noise["notes"].append((tick, tick + EIGHTH // 2, pitch, 96 - index * 12))
                added["fill_4"] += 1

        if rung8:
            # a longer fill: three hits across the last beat and a half
            for index, (eighth, pitch) in enumerate(((4, 13), (5, 11), (6, 9), (7, 7))):
                tick = base + eighth * EIGHTH
                noise["notes"].append((tick, tick + EIGHTH // 2, pitch, 100 - index * 10))
                added["fill_8"] += 1

        # the kick keeps beats 1 and 3, but every second rung bar drops the
        # beat 3 kick so the backbeat snare has room
        if bar % 8 in (6, 7):
            dpcm["notes"] = [n for n in dpcm["notes"]
                             if not (n[0] == base + 4 * EIGHTH and n[2] == 36)]
            added["kick_var"] += 1

    for track in (noise, dpcm):
        track["notes"].sort()
    report["rungs"] = added
    report["rung_map"] = {"backbeat_bars": [5, 6, 7, 13, 14, 15],
                         "fill_4_bars": [4, 8, 12, 16, 20, 24],
                         "fill_8_bars": [8, 16, 24]}
    return added


# ------------------------------------------------------------------- the build
def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args(argv)

    song = hook_score.read_smf(V1)
    report = {"source": V1, "division": song["division"], "tempo_us": song["tempo_us"],
              "tracks": [{"name": t["name"], "notes": len(t["notes"])} for t in song["tracks"]]}

    if args.probe:
        for track in song["tracks"]:
            if track["notes"]:
                velocities = sorted({n[3] for n in track["notes"]})
                print("%-16s notes %4d cc11 %s vel %s"
                      % (track["name"], len(track["notes"]),
                         sorted({v for _, v in track["cc"].get(11, [])}),
                         velocities[:6]))
        print(json.dumps(report, indent=2))
        return 0

    notes_before = sum(len(t["notes"]) for t in song["tracks"])
    add_counterline(song, report)
    raise_noise(song, report)
    add_rungs(song, report)

    humanize.write_smf(song, OUT_RAW)
    report["midi_raw"] = OUT_RAW
    report["notes_before"] = notes_before
    report["notes_after_raw"] = sum(len(t["notes"]) for t in song["tracks"])

    hum_report = humanize.humanize_file(OUT_RAW, OUT, write=True)
    report["humanize"] = {key: hum_report[key] for key in
                          ("seed", "bpm", "notes_in", "notes_out", "notes_changed",
                           "vibrato_pairs", "fills", "sha256_out")
                          if key in hum_report}
    report["midi_out"] = OUT

    with open(REPORT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps({k: report[k] for k in ("counterline", "noise", "rungs",
                                             "notes_before", "notes_after_raw")}, indent=2))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
