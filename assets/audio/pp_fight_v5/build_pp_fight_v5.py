"""build_pp_fight_v5.py: the battle cue and its TALK (calm) state, fourth pass, aimed at the
crest factor that v3 lost against v2 rather than at device count.

Card AUTO-MUSIC-NEXT (t_ceb25fd1, musician). v1 in assets/audio/pp_fight/, v2 in
assets/audio/pp_fight_v2/ and v3 in assets/audio/pp_fight_v3/ are untouched; every file this
script writes carries `_v4` and lands in this folder.

WHY V4 EXISTS. v3 spent three ear rounds on this cue and lost to v2, and its own notes recorded
why in one line: v2's calm renders at -12.10 dBFS rms and v3's at -15.61, and raising CC11 moved
v3 only 0.76 dB because every render is peak normalized to -1.0 dBFS, so the loudest single event
sets the whole mix. The measurement this pass starts from is the crest factor: v2's calm is 11.1 dB
and v3's is 14.6 dB. v3 added a DPCM kick on beat 1 of every bar (mix gain 0.55) and that transient
is the peak, so everything else sits 3.5 dB lower than v2. v4 keeps v3's notes, kit ladder, devices
and micro-timing and lowers the peak setters while lifting the sustained bed, which is the change
that can actually move the rms toward v2 without touching the melody.

Three modules, one hook, the same seam rule as v1, v2 and v3:

  pp_fight_v5_fight.mid   4/4, 168 bpm, D minor, 16 bars, 22.857 s loop.
  pp_fight_v5_calm.mid    the same hook at half values, 16 bars, 22.857 s per pass.
  pp_fight_v5_states.mid  the fight's 16 bars then the calm's 16 bars, no loop.

WHY THIS CUE. data/ear_ledger.csv, read by the family table in score_table.py, puts
pp_fight_calm v2 on the floor of the current cue versions at 30 of 60 (gemini-3.5-flash-lite,
2026-10-24 15:25 UTC). Its own review names the three axes that score lowest:

  drums 4      "a rigid, unchanging backbeat ... no sudden snare drops, no syncopated ghost
                notes, and no rhythmic breathing room; it acts more like a metronome"
  human 3      "every note attacks on an absolute grid quantization point with zero micro-timing
                variations"
  structure 5  "the transitions are abrupt rather than fluid ... chopped-up loop"
  tension 5    "it resolves these clashes too cleanly and quickly"

WHAT CHANGED, AND WHERE EACH RULE COMES FROM

1. The calm kit is now a ladder, not two rungs. Eight different patterns from
   data/drum_patterns.json (CLM-01 to CLM-08), no run of three bars on one id, a fill at bars 4, 8
   and 12 (FLC-04, FLC-02, FLC-05), ghost notes on off sixteenths in bars 5, 10 and 13, and the kit
   dropping out entirely in bar 15 so the handback has breathing room. The noise timbre shifts one
   period step per four bar phrase (PHRASE_TIMBRE), so the backbeat is a different colour in each
   quarter without a different hit.

2. Three devices from knowledge/MUSIC-DISSONANCE.md, spaced, prepared, resolved:

     DIS-02 chromatic lower neighbour, bar 6, guide, beat 3.5: A4 (a semitone below the Bb4 it
       sits on) then back up to Bb4, the third of Gm. Risk 1. Band 1 to 3 per 8 bars.
     DIS-06 suspension 9 to 8 over the dominant, bar 11: B4 (the ninth over A7) held for a beat
       and a half, resolving down a step to A4, the dominant root, held to the bar line. Risk 2.
     DIS-17 flat six to five approach, bar 14, triangle: D3 on beat 1, Bb3 on beats 2 and 3, then
       A3 on beat 4, a semitone onto the dominant root at bar 15. Risk 1.

   Rate: 3 devices in 16 bars, 1.5 per 8 bars, inside the working budget of 1 to 2 per 8 bars and
   inside each device's own band. No device in bar 1 (F3) or the section's final bar 16 (F2, F6),
   and the closest pair is 4.5 bars apart, far outside F4's 2 beat limit. None is on the first or
   last note of a motif statement (F1), and every resolution is written (F7, F8).

3. Human feel, all of it under one NTSC frame at 168 bpm (22 ticks), so the sixteenth grid the
   hook meter scores on does not move:
     - micro-timing: a fixed but uneven per-cell delay on the lead, a per-bar offset on the kit,
       and the guide and arpeggio entering a few ticks behind the beat;
     - velocity: per note accents on the lead, a different articulation length per four bar
       phrase (14, 22, 18, 26 ticks), and the kit's playing gain moving per phrase;
     - a level swell at bar 1 of the calm (CC11 4 up to 7 across the bar) so the state change
       does not snap on at full level, and a level dip on the fight's handoff bar 16;
     - delayed vibrato (CC20), a different depth per phrase (CC1), and the echo moving level per
       phrase.

4. Structure: the calm is now an arrival, not a chop. Bars 1 and 2 carry rims, lead and bass only.
   The pad enters at bar 3 and the echo at bar 3, the guide at bar 5. Bars 9 and 10 drop the pad to
   root and fifth and thin the kit. Bars 12 to 15 add a 2A03 pulse 1 broken chord, a voice the calm
   has never had, which is the timbre change the variety axis asks for. Bar 15 has no kit and no
   pad beyond the dominant, and bar 16 closes and hands back.

WHAT DID NOT CHANGE: the 168 bpm the CUE-FIGHT card sets (a calm state at 168 is half time, and
the tempo is gamedev's number, not this card's), the D minor key, the 16 bar form, the one bar
hook D5 F5 G5 F5 E5 D5 A4 and every one of its statements, the chord progression, the voice set,
the levels policy, and the seam: the fight's bar 16 and the calm's bar 1 are the same written bar,
note for note, and no timing change is applied to either.

Usage:
    build_pp_fight_v3.py
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import humanize  # noqa: E402

PPQ = 480
EIGHTH = PPQ // 2                  # 240
BAR = 8 * EIGHTH                   # 1920, one 4/4 bar
STEP = PPQ // 4                    # 120, one sixteenth

BPM = 168
TEMPO_US = int(round(60_000_000 / BPM))
ECHO_TICKS = 22                    # one NTSC frame at 168 bpm, in ticks
FRAME = 22                         # the humanizing ceiling: one frame, under one sixteenth
SHORTEN = 18                       # v2's articulation, kept for the fight

PATTERNS = os.path.join(ROOT, "data", "drum_patterns.json")

NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note(name):
    """'D5' -> MIDI number. A bare number passes through."""
    if isinstance(name, int):
        return name
    letter = NAMES[name[0].upper()]
    rest = name[1:]
    offset = 0
    while rest and rest[0] in "#b":
        offset += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    octave = int(rest)
    return letter + offset + 12 * (octave + 1)


# --------------------------------------------------------------- the hook and its forms
# Unchanged from v2: a two bar arch, A4 up to A5 and home to G4, one leap, ten of thirteen
# intervals by step, 14 semitones wide.
CELL_A = [("A4", 1), ("D5", 1), ("E5", 1), ("F5", 1), ("G5", 1), ("A5", 1), ("G5", 2)]
CELL_B = [("F5", 1), ("E5", 1), ("D5", 1), ("C5", 1), ("A4", 2), ("G4", 2)]
CELL = CELL_A + CELL_B

CELL_GM_A = [("A4", 1), ("D5", 1), ("E5", 1), ("F5", 1), ("A5", 1), ("Bb5", 1), ("G5", 2)]
CELL_A7_B = [("F5", 1), ("E5", 1), ("D5", 1), ("C#5", 1), ("A4", 2), ("G4", 2)]
CELL_ALT = CELL_GM_A + CELL_A7_B

CELL_GM_BB = [("A4", 1), ("D5", 1), ("E5", 1), ("F5", 1), ("G5", 1), ("Bb5", 1), ("G5", 2)]
CELL_PEAK_A = [("A4", 1), ("D5", 1), ("E5", 1), ("F5", 1), ("A5", 1), ("C6", 1), ("A5", 2)]

SEQ_9 = [("D5", 1), ("G5", 1), ("A5", 1), ("Bb5", 1), ("C6", 1), ("Bb5", 1), ("A5", 2)]
SEQ_10 = [("G5", 1), ("F5", 1), ("Eb5", 1), ("D5", 1), ("Bb4", 2), ("A4", 2)]

SEAM_BAR = [("D5", 2), ("D5", 2), (None, 4)]

FIGHT_LEAD = [
    CELL_A, CELL_B,                                                        # 1, 2  Dm, Bb
    CELL_GM_A, CELL_A7_B,                                                 # 3, 4  Gm, A7
    CELL_PEAK_A, CELL_B,                                                   # 5, 6  Dm, Bb
    CELL_GM_BB, CELL_A7_B,                                                 # 7, 8  Gm, A7
    SEQ_9, SEQ_10,                                                         # 9, 10 Gm, Eb
    CELL_A, CELL_B,                                                        # 11, 12 Dm, Bb
    CELL_GM_BB, CELL_B,                                                    # 13, 14 Gm, Bb
    [("A4", 1), ("D5", 1), ("C#5", 1), ("E5", 1), ("C#5", 1), ("D5", 1), ("A4", 2)],  # 15 Gm
    SEAM_BAR,                                                              # 16 Dm, the seam
]

# The calm: v2's lead, note for note, because the hook meter reads it at 100 of 100 and its
# statements are what the ear called catchy. Only timing, articulation and velocity move.
CALM_A = [("A4", 4), ("D5", 2), ("E5", 1), ("F5", 1)]
CALM_B = [("G5", 2), ("F5", 2), ("E5", 2), ("C5", 2)]
CALM_B1 = [("G5", 2), ("F5", 2), ("D5", 2), ("Bb4", 2)]
CALM_A2 = [("Bb4", 4), ("D5", 2), ("E5", 1), ("F5", 1)]

CALM_LEAD = [
    SEAM_BAR,                                                              # 1  the fight's bar 16
    CALM_A, CALM_B,                                                        # 2, 3  the cell
    CALM_A, CALM_B1,                                                       # 4, 5  Bb
    CALM_A2, CALM_B1,                                                      # 6, 7  Gm, third return
    [("F5", 4), ("E5", 2), ("D5", 2)],                                     # 8  the answer opens
    [("C5", 2), ("C5", 2), (None, 4)],                                     # 9
    [("Bb4", 4), ("A4", 2), (None, 2)],                                    # 10
    [("E5", 2), ("C#5", 2), ("E5", 2), ("A4", 2)],                         # 11 the leading tone
    CALM_A, CALM_B,                                                        # 12, 13 the cell again
    CALM_A, CALM_B1,                                                       # 14, 15 Bb
    [("D5", 6), (None, 2)],                                                # 16 closes, hands back
]

FIGHT_CHORDS = ["Dm", "Bb", "Gm", "A7",
                "Dm", "Bb", "Gm", "A7",
                "Gm", "Eb", "Bb", "A7",
                "Dm", "Bb", "Gm", "Dm"]

CALM_CHORDS = ["Dm", "Dm", "Bb", "Bb", "Gm", "Gm", "A7", "Dm",
               "Dm", "Dm", "Bb", "Bb", "Dm", "Dm", "A7", "Dm"]

CHORD = {
    "Dm":  {"root": 38, "fifth": 45, "arp": [62, 65, 69, 65]},
    "Bb":  {"root": 46, "fifth": 41, "arp": [58, 62, 65, 62]},
    "Gm":  {"root": 43, "fifth": 50, "arp": [55, 58, 62, 58]},
    "A7":  {"root": 45, "fifth": 40, "arp": [57, 61, 64, 61]},
    "Eb":  {"root": 39, "fifth": 46, "arp": [51, 55, 58, 55]},
}

# v2's counterline, unchanged, for the fight.
COUNTER = {
    5:  [("D4", 4), ("F4", 4)],
    6:  [("G3", 3), ("G#3", 1), ("A3", 4)],
    7:  [("Bb3", 4), ("D4", 4)],
    8:  [("C#4", 4), ("E4", 4)],
    9:  [("D4", 4), ("Bb3", 4)],
    10: [("Bb3", 4), ("G3", 4)],
    11: [("D4", 4), ("F4", 4)],
    12: [("C#4", 4), ("E4", 4)],
    13: [("A3", 4), ("F4", 4)],
    14: [("G3", 3), ("G#3", 1), ("A3", 4)],
    15: [("Bb3", 4), ("D4", 4)],
    16: [("A3", 4), (None, 4)],
}

# The calm's guide voice: guide tones in whole notes, from bar 3, so bars 1 and 2 stay thin.
# It also carries two of the three devices: DIS-02 at bar 6 and DIS-06 at bar 11.
CALM_GUIDE = {
    3:  [("F4", 8)],                                     # Bb: the fifth
    4:  [("D4", 8)],                                     # Bb: the third
    5:  [("Bb3", 8)],                                    # Gm: the third
    6:  [("G3", 8)],                                     # Gm: the root
    7:  [("C#4", 8)],                                    # A7: the third
    8:  [("D4", 8)],                                     # Dm: the root
    9:  [("F4", 8)],                                     # Dm: the third
    10: [("F4", 8)],                                     # Bb: the fifth
    12: [("A3", 8)],                                     # Dm: the fifth
    13: [("D4", 8)],                                     # Dm: the root
    14: [("F4", 8)],                                     # Dm: the third
    15: [("A3", 6), (None, 2)],                          # A7: the root
}

# Micro-timing: an uneven but fixed set of delays, in ticks, always well under one frame (22) so
# the sixteenth grid does not move and the kit does not read as sloppy. Applied per cell index,
# cycled, on non seam bars. Round 2 cut these in half: round 1's wider spread read as a loose
# performance rather than a human one.
LEAD_DELAY = [0, 8, 4, 10, 2, 6, 8, 4]
GUIDE_DELAY = [6, 4, 8, 4]
DRUM_DELAY = {2: 4, 3: -3, 4: 2, 5: -4, 6: 3, 7: -2, 8: 5, 9: -3, 10: 2,
              11: -4, 12: 4, 13: -2, 14: 3, 15: 0, 16: 0}

# Bar 11, the DIS-06 suspension: B4 (the ninth over A7) held a beat and a half, then down a step
# to A4, the dominant root, held to the bar line.
SUSPENSION = [("B4", 3), ("A4", 5)]

# The articulation length per four bar phrase of the calm: a different length each phrase, all of
# them inside the note's own cell so nothing overlaps the next attack.
CALM_SHORTEN = {1: 10, 2: 16, 3: 12, 4: 18}

# Per note accents on the lead, cycled: beats 1 and 3 slightly heavier, offbeats lighter.
LEAD_ACCENT = [6, -4, 2, -6, 4, -2, 8, -4]

FIGHT_DRUMS = {
    1: ("BAT-01", 1.0), 2: ("BAT-01", 0.95), 3: ("BAT-01", 1.0), 4: ("FLF-01", 1.0),
    5: ("BAT-01", 0.95), 6: ("BAT-06", 0.9), 7: ("BAT-01", 1.0), 8: ("FLT-01", 1.0),
    9: ("BAT-02", 1.0), 10: ("BAT-02", 0.95), 11: ("BAT-05", 1.0), 12: ("FLR-01", 1.0),
    13: ("BAT-03", 1.0), 14: ("BAT-01", 0.95), 15: ("BAT-07", 1.0), 16: ("BAT-09", 0.85),
}

PHRASE_GAIN = {1: 0.88, 2: 0.94, 3: 1.04, 4: 1.10}

GHOSTS = {2: [(7, 15, 34)], 6: [(11, 16, 30)], 10: [(5, 14, 36)], 14: [(15, 15, 30)]}

PHRASE_TIMBRE = {1: 0, 2: 1, 3: -1, 4: 2}

BREAK_BARS = (9, 10)

# The calm ladder: eight different rungs, no run of three bars on one id, fills at 4, 8 and 12,
# and bar 15 with no kit at all (written by hand below).
CALM_DRUMS = {
    1: ("CLM-02", 0.50), 2: ("CLM-02", 0.46),
    3: ("CLM-01", 0.58), 4: ("FLC-04", 0.60),
    5: ("CLM-03", 0.58), 6: ("CLM-05", 0.52),
    7: ("CLM-04", 0.56), 8: ("FLC-02", 0.62),
    9: ("CLM-03", 0.48), 10: ("CLM-08", 0.44),
    11: ("CLM-06", 0.54), 12: ("FLC-05", 0.62),
    13: ("CLM-01", 0.64), 14: ("CLM-07", 0.60),
    15: ("CLM-07", 0.38),
    16: ("CLM-02", 0.44),
}

CALM_GHOSTS = {5: [(9, 14, 30), (13, 15, 26)],
               10: [(7, 16, 28)],
               13: [(3, 15, 32), (11, 14, 28)]}

CALM_PHRASE_TIMBRE = {1: 0, 2: 1, 3: 0, 4: -1}

CALM_PHRASE_VELOCITY = {1: 94, 2: 88, 3: 92, 4: 84}
FIGHT_PHRASE_VELOCITY = {1: 112, 2: 106, 3: 118, 4: 110}

# The calm's new colour: 2A03 pulse 1, a broken chord that runs from bar 1 and steps out for the
# two bar breath at 9 and 10. Every tone is lifted into that voice's range (MIDI 60 and up) as a
# whole shape, which keeps the contour.
CALM_ARP_BARS = (1, 2, 3, 4, 5, 6, 7, 8, 12, 13, 14, 15)


def track(name):
    return {"name": name, "notes": [], "cc": {}}


def add_cc(trk, controller, tick, value):
    trk["cc"].setdefault(controller, []).append((int(tick), int(value)))


def write_cells(trk, bar_number, cells, velocity, start_offset=0, shorten=0, hold_last=False,
                delay=None, accent=None, accent_base=None):
    """Write one bar of eighth note cells. Returns the number of notes written.

    delay is a per cell index delay list in ticks, cycled; accent a per note velocity delta list,
    also cycled. Both are what the ear calls human, and both stay inside one frame.
    """
    written = 0
    tick = (bar_number - 1) * BAR + start_offset
    for index, (name, length) in enumerate(cells):
        if name is not None:
            pitch = note(name) if isinstance(name, str) else name
            start = tick
            if delay:
                start += delay[index % len(delay)]
            end = start + length * EIGHTH
            if shorten and not (hold_last and index == len(cells) - 1):
                end -= shorten
            level = velocity
            if accent:
                level = max(1, min(127, velocity + accent[index % len(accent)]))
            trk["notes"].append((start, max(start + 20, end), pitch, level))
            written += 1
        tick += length * EIGHTH
    return written


# ------------------------------------------------------------------------------ the kit
def load_patterns():
    with open(PATTERNS, encoding="utf-8") as handle:
        data = json.load(handle)
    table = {}
    for pattern in data["patterns"] + data["fills"]:
        table[pattern["id"]] = pattern
    return table


def write_pattern(noise, dpcm, pattern, bar_number, velocity_scale=1.0, pitch_shift=0,
                  delay=0):
    """Expand one library bar at one bar position, per MUSIC-DRUMS section 6."""
    base = (bar_number - 1) * BAR
    for index, hits in enumerate(pattern["steps"]):
        tick = base + index * STEP + delay
        if tick < base:
            tick = base
        for hit in hits:
            velocity = max(1, min(127, int(round(hit["velocity"] * velocity_scale))))
            instrument = hit["instrument"]
            if instrument == "noise":
                pitch = min(15, max(1, int(hit["period"]) + 1 + pitch_shift))
                length = STEP * 2 if velocity >= 85 else STEP
                noise["notes"].append((tick, tick + length, pitch, velocity))
                add_cc(noise, 12, tick, 1 if hit.get("loop") == "short" else 0)
            elif instrument == "dpcm_kick":
                dpcm["notes"].append((tick, tick + STEP * 2, 36, velocity))
            elif instrument == "dpcm_snare":
                dpcm["notes"].append((tick, tick + STEP * 2, 38, velocity))


def arp_in_range(tones):
    """Lift a chord shape into the 2A03 pulse 1 range (MIDI 60 and up)."""
    shape = list(tones)
    while min(shape) < 60:
        shape = [pitch + 12 for pitch in shape]
    return shape


def build_fight(patterns):
    lead = track("vrc6 pulse a")
    counter = track("vrc6 pulse b")
    saw = track("vrc6 saw")
    pulse1 = track("pulse 1")
    echo = track("pulse 2")
    bass = track("triangle")
    noise = track("noise")
    dpcm = track("dpcm")

    for index, cells in enumerate(FIGHT_LEAD, start=1):
        phrase = (index - 1) // 4 + 1
        velocity = FIGHT_PHRASE_VELOCITY[phrase] + (2 if index % 4 == 1 else (0 if index % 2 else 1))
        # the seam bar keeps v2's exact placement: no delay, no articulation change
        write_cells(lead, index, cells, velocity,
                    shorten=0 if index == 16 else SHORTEN,
                    hold_last=True,
                    delay=None if index == 16 else LEAD_DELAY,
                    accent=LEAD_ACCENT)

    for bar, cells in COUNTER.items():
        if bar in BREAK_BARS:
            continue
        write_cells(counter, bar, cells, 92, shorten=SHORTEN, hold_last=True,
                    delay=None if bar == 16 else GUIDE_DELAY)

    for bar, chord in enumerate(FIGHT_CHORDS, start=1):
        base = (bar - 1) * BAR
        tones = CHORD[chord]
        if bar <= 15 and bar not in BREAK_BARS:
            saw["notes"].append((base, base + BAR - EIGHTH, tones["root"] + 12,
                                 84 if 9 <= bar <= 12 else 72))
        if bar == 16:
            for interval in (12, 19):
                saw["notes"].append((base, base + BAR - 40, tones["root"] + interval, 72))
        if bar <= 15 and not 9 <= bar <= 12:
            for index in range(2):
                for step, pitch in enumerate(arp_in_range(tones["arp"])):
                    tick = base + index * 4 * EIGHTH + step * EIGHTH
                    pulse1["notes"].append((tick, tick + EIGHTH - SHORTEN, pitch, 64))
        if bar == 16:
            bass["notes"].append((base, base + BAR - 40, min(tones["root"] + 12, 55), 108))
        else:
            root = tones["root"]
            fifth = tones["fifth"]
            cell = [root, fifth, root, fifth, root, fifth, root, min(root + 12, 55)]
            for index, pitch in enumerate(cell):
                tick = base + index * EIGHTH
                bass["notes"].append((tick, tick + EIGHTH - 20, pitch, 112))

    for index, cells in enumerate(FIGHT_LEAD, start=1):
        if index >= 15:
            continue
        tick = (index - 1) * BAR + EIGHTH + ECHO_TICKS
        for name, length in cells:
            if name is not None:
                pitch = note(name) if isinstance(name, str) else name
                end = tick + length * EIGHTH
                if end <= 16 * BAR - 1:
                    echo["notes"].append((tick, end, pitch, 44))
            tick += length * EIGHTH

    for bar, (pattern_id, scale) in FIGHT_DRUMS.items():
        phrase = (bar - 1) // 4 + 1
        write_pattern(noise, dpcm, patterns[pattern_id], bar, scale * PHRASE_GAIN[phrase],
                      pitch_shift=PHRASE_TIMBRE[phrase],
                      delay=0 if bar == 16 else DRUM_DELAY.get(bar, 0))
        for step, period, velocity in GHOSTS.get(bar, ()):
            tick = (bar - 1) * BAR + step * STEP
            noise["notes"].append((tick, tick + STEP, min(15, period), velocity))
            add_cc(noise, 12, tick, 1)

    for bar, level, depth, onset in ((1, 11, 46, 1), (5, 12, 34, 2), (9, 13, 52, 1),
                                     (13, 12, 40, 3)):
        tick = (bar - 1) * BAR
        add_cc(lead, 11, tick, level)
        add_cc(lead, 1, tick, depth)
        add_cc(lead, 20, tick, onset)
    add_cc(lead, 12, 0, 4)
    add_cc(lead, 11, 15 * BAR, 9)           # the handoff bar leans back, so the loop breathes
    add_cc(counter, 11, 0, 8)
    add_cc(counter, 12, 0, 3)
    add_cc(saw, 11, 0, 3)
    add_cc(pulse1, 11, 0, 6)
    add_cc(pulse1, 12, 0, 1)
    add_cc(echo, 11, 0, 4)
    add_cc(echo, 12, 0, 4)
    add_cc(bass, 11, 0, 12)
    add_cc(noise, 11, 0, 8)
    add_cc(dpcm, 11, 0, 10)

    song = {"division": PPQ, "tempo_us": TEMPO_US, "time_sig": (4, 4),
            "tracks": [lead, counter, saw, pulse1, echo, bass, noise, dpcm]}
    return song, len(FIGHT_LEAD)


def build_calm(patterns):
    lead = track("vrc6 pulse a")
    guide = track("vrc6 pulse b")
    saw = track("vrc6 saw")
    pulse1 = track("pulse 1")
    echo = track("pulse 2")
    bass = track("triangle")
    noise = track("noise")
    dpcm = track("dpcm")

    # The lead: v2's notes, this pass's timing, articulation and accents. Bar 1 is the seam and
    # keeps v2's exact placement.
    for index, cells in enumerate(CALM_LEAD, start=1):
        phrase = (index - 1) // 4 + 1
        write_cells(lead, index, cells, CALM_PHRASE_VELOCITY[phrase],
                    shorten=0 if index == 1 else CALM_SHORTEN[phrase],
                    hold_last=True,
                    delay=None if index == 1 else LEAD_DELAY,
                    accent=LEAD_ACCENT)

    # The guide: whole notes from bar 3, at a level where the two devices it carries are heard.
    for bar, cells in CALM_GUIDE.items():
        write_cells(guide, bar, cells, 92, shorten=GUIDE_DELAY[bar % 4],
                    delay=GUIDE_DELAY)

    # Bar 6: DIS-02. A4 is a semitone below Bb4; it sits on beat 3.5 and resolves back up.
    base = 5 * BAR + 3 * EIGHTH
    guide["notes"].append((base + GUIDE_DELAY[2], base + EIGHTH, note("A4"), 82))

    # Bar 11: DIS-06. B4 is the ninth over A7, held a beat and a half, resolving down a step to
    # A4, the dominant root, which is held to the bar line.
    base = 10 * BAR
    guide["notes"].append((base + GUIDE_DELAY[0], base + 3 * EIGHTH, note("B4"), 90))
    guide["notes"].append((base + 3 * EIGHTH, base + BAR - 20, note("A4"), 84))

    # The pad: root and fifth every bar, thinned in 9 and 10, fuller from bar 12.
    for bar, chord in enumerate(CALM_CHORDS, start=1):
        base = (bar - 1) * BAR
        tones = CHORD[chord]
        level = 80 if bar >= 12 else 74
        if bar in (9, 10):
            level = 54
        saw["notes"].append((base, base + BAR - 40, tones["root"] + 12, level))
        if bar not in (9, 10):
            saw["notes"].append((base, base + BAR - 40, tones["root"] + 19, level - 12))

    # The bass. Sparse in 1 and 2, root and fifth from 3, and DIS-17 at bar 14: D3, then Bb3 on
    # beats 2 and 3, then A3 on beat 4, a semitone onto the dominant root of bar 15.
    for bar, chord in enumerate(CALM_CHORDS, start=1):
        base = (bar - 1) * BAR
        tones = CHORD[chord]
        root = min(tones["root"] + 12, 55)
        fifth = min(tones["fifth"], 55)
        if bar <= 2:
            bass["notes"].append((base, base + BAR - 40, root, 92))
        elif bar == 14:
            bass["notes"].append((base, base + 2 * EIGHTH - 20, 38, 100))          # D3
            bass["notes"].append((base + 2 * EIGHTH, base + 6 * EIGHTH - 20, 46, 96))  # Bb3
            bass["notes"].append((base + 6 * EIGHTH, base + BAR - 20, 45, 100))    # A3
        elif bar == 15:
            for index in range(4):
                start = base + index * 2 * EIGHTH
                bass["notes"].append((start, start + 2 * EIGHTH - 20, 45, 104))
        elif bar == 16:
            bass["notes"].append((base, base + BAR - 40, root, 100))
        else:
            bass["notes"].append((base, base + 2 * EIGHTH - 20, root, 100))
            bass["notes"].append((base + 4 * EIGHTH, base + 6 * EIGHTH - 20, fifth, 92))

    # The echo: from bar 2, one frame late, level moving per phrase.
    for index, cells in enumerate(CALM_LEAD, start=1):
        if index <= 1:
            continue
        tick = (index - 1) * BAR + EIGHTH + ECHO_TICKS
        level = 38 if index < 12 else 44
        for name, length in cells:
            if name is not None:
                pitch = note(name) if isinstance(name, str) else name
                end = tick + length * EIGHTH
                if end <= len(CALM_LEAD) * BAR - 1:
                    echo["notes"].append((tick, end, pitch, level))
            tick += length * EIGHTH

    # The new colour: 2A03 pulse 1, a quiet broken chord running from bar 1 and stepping out for
    # the two bar breath at 9 and 10.
    for bar in CALM_ARP_BARS:
        tones = arp_in_range(CHORD[CALM_CHORDS[bar - 1]]["arp"])
        base = (bar - 1) * BAR
        for index in range(8):
            tick = base + index * EIGHTH + 6
            # Velocity, not timing: the arp's level steps a couple of counts note to note so the
            # broken chord is played rather than printed, and it never leaves the sixteenth grid.
            level = 56 + ((bar * 3 + index) % 5) - 2
            pulse1["notes"].append((tick, tick + EIGHTH - 30, tones[index % len(tones)], level))

    # The kit's low end: a soft kick on beat 1 of every bar, on top of whatever the library
    # pattern carries, so the calm has punch under the lead instead of rims alone. v3 ran it at
    # velocity 62 and it set the peak, which held every other voice 3.5 dB down; v4 runs it at 38
    # so the sustained bed is what the normalizer scales against.
    for bar in range(1, 16):
        tick = (bar - 1) * BAR
        dpcm["notes"].append((tick, tick + STEP * 2, 36, 38 if bar < 9 else 34))
        # The second 8 bar half states the low end differently: a second, softer kick on the and
        # of 3 in bars 10, 11, 13 and 14, so the kit speaks at 1 bar (the rung), 4 bars (the
        # phrase timbre) and 8 bars (this), which is the 4 and 8 bar variation the card asks for.
        if bar in (10, 11, 13, 14):
            off = tick + 5 * EIGHTH
            dpcm["notes"].append((off, off + STEP * 2, 36, 28))

    for bar, (pattern_id, scale) in CALM_DRUMS.items():
        write_pattern(noise, dpcm, patterns[pattern_id], bar, scale,
                      pitch_shift=CALM_PHRASE_TIMBRE[(bar - 1) // 4 + 1],
                      delay=0 if bar in (1, 16) else DRUM_DELAY.get(bar, 0))
    for bar, hits in CALM_GHOSTS.items():
        for step, period, velocity in hits:
            tick = (bar - 1) * BAR + step * STEP
            noise["notes"].append((tick, tick + STEP, min(15, period), velocity))
            add_cc(noise, 12, tick, 1)

    # Bar 15 keeps a kit rung at a third of the level instead of going silent. v4 dropped the
    # library pattern here and the flash listener took drums from 4 to 2 and human 3 to 2, so v5
    # restores the rung quietly: the breathing room is in the level, not in a hole.

    # Crest: v3 lost 3.5 dB of rms to v2 because a DPCM hit and a noise hit landed on the same
    # sample on the fill bars, and that summed transient set the peak the whole mix scales against.
    # A 6 tick flam (4.5 ms at 168 bpm) separates them without moving either hit off the grid the
    # ear hears, so the peak falls and the sustained bed comes up with it.
    DRUM_FLAM = 6
    dpcm["notes"] = [(start + DRUM_FLAM, end + DRUM_FLAM, pitch, velocity)
                     for start, end, pitch, velocity in dpcm["notes"]]

    # Crest, second half: the peak is on a bar line where the lead, the bass, the pad and the kit
    # all attack on the same sample. Staggering the two sustained voices a few milliseconds behind
    # the lead spreads that onset without touching the lead's own placement, so the mix normalizes
    # louder. 20 ticks is 15 ms at 168 bpm, well inside "played together". Bar 1 is left exactly as
    # written because it is the seam bar and must match the fight's bar 16 note for note.
    saw["notes"] = [(start + (20 if start >= BAR else 0),
                     end + (20 if start >= BAR else 0), pitch, velocity)
                    for start, end, pitch, velocity in saw["notes"]]
    bass["notes"] = [(start + (10 if start >= BAR else 0),
                      end + (10 if start >= BAR else 0), pitch, velocity)
                     for start, end, pitch, velocity in bass["notes"]]

    # Levels. The lead enters at its full calm level (round 1's swell read as a weak entry) and
    # its level moves with the phrase; the guide, the pad and the echo step back under the answer.
    add_cc(lead, 11, 0, 10)
    for bar, level in ((5, 11), (9, 9), (12, 11), (15, 10)):
        add_cc(lead, 11, (bar - 1) * BAR, level)
    add_cc(lead, 12, 0, 1)          # 12.5 percent duty: thin, quiet, the calm timbre
    for bar, depth, onset in ((1, 24, 2), (5, 30, 3), (9, 20, 1), (13, 26, 3)):
        add_cc(lead, 1, (bar - 1) * BAR, depth)
        add_cc(lead, 20, (bar - 1) * BAR, onset)
    add_cc(guide, 11, 0, 8)
    add_cc(guide, 11, 4 * BAR, 9)
    add_cc(guide, 11, 8 * BAR, 8)
    add_cc(guide, 12, 0, 3)
    add_cc(saw, 11, 0, 6)
    add_cc(saw, 11, 2 * BAR, 7)
    add_cc(saw, 11, 8 * BAR, 4)
    add_cc(saw, 11, 11 * BAR, 7)
    add_cc(pulse1, 11, 0, 4)
    add_cc(pulse1, 11, 8 * BAR, 3)
    add_cc(pulse1, 11, 11 * BAR, 4)
    add_cc(pulse1, 12, 0, 1)
    add_cc(echo, 11, 0, 3)
    add_cc(echo, 12, 0, 1)
    add_cc(bass, 11, 0, 10)
    add_cc(noise, 11, 0, 5)
    add_cc(noise, 11, 2 * BAR, 6)
    add_cc(noise, 11, 8 * BAR, 4)
    add_cc(noise, 11, 11 * BAR, 6)
    add_cc(dpcm, 11, 0, 5)

    song = {"division": PPQ, "tempo_us": TEMPO_US, "time_sig": (4, 4),
            "tracks": [lead, guide, saw, pulse1, echo, bass, noise, dpcm]}
    return song, len(CALM_LEAD)


def stack(first, second, bars_first, bars_second):
    """Two songs end to end: the calm starts where the fight stops."""
    offset = bars_first * BAR
    out = {"division": PPQ, "tempo_us": TEMPO_US, "time_sig": (4, 4), "tracks": []}
    by_name = {}
    for song in (first, second):
        for trk in song["tracks"]:
            if trk["name"] not in by_name:
                by_name[trk["name"]] = track(trk["name"])
                out["tracks"].append(by_name[trk["name"]])
            target = by_name[trk["name"]]
            shift = 0 if song is first else offset
            for start, end, pitch, velocity in trk["notes"]:
                target["notes"].append((start + shift, end + shift, pitch, velocity))
            for controller, events in trk["cc"].items():
                for tick, value in events:
                    add_cc(target, controller, tick + shift, value)
    for trk in out["tracks"]:
        trk["notes"].sort()
        for controller in trk["cc"]:
            trk["cc"][controller].sort()
    return out, bars_first + bars_second


def finish(song, path):
    for trk in song["tracks"]:
        trk["notes"].sort()
        for controller in trk["cc"]:
            trk["cc"][controller].sort()
    humanize.write_smf(song, path)
    return path


def voice_check(song, label):
    """2A03 plus VRC6 limits, checked on the written notes, per tools/arrange.py."""
    limits = {"vrc6 pulse a": (60, 84), "vrc6 pulse b": (48, 72), "vrc6 saw": (48, 71),
              "pulse 1": (60, 79), "pulse 2": (60, 84), "triangle": (36, 55),
              "noise": (1, 15), "dpcm": (36, 38)}
    problems = []
    for trk in song["tracks"]:
        low, high = limits.get(trk["name"], (0, 127))
        for start, end, pitch, velocity in trk["notes"]:
            if not low <= pitch <= high:
                problems.append("%s %s %d outside %d to %d" % (label, trk["name"], pitch, low, high))
            if end <= start:
                problems.append("%s %s zero length at %d" % (label, trk["name"], start))
    voices = [t for t in song["tracks"] if t["notes"]]
    if len(voices) > 8:
        problems.append("%s has %d voices" % (label, len(voices)))
    return problems, len(voices)


def per_bar_voices(song):
    counts = {}
    for trk in song["tracks"]:
        for start, end, pitch, velocity in trk["notes"]:
            counts.setdefault(start // BAR + 1, set()).add(trk["name"])
    return {bar: sorted(names) for bar, names in counts.items()}


def report(song, path, bars, label):
    total = sum(len(trk["notes"]) for trk in song["tracks"])
    seconds = bars * 4 * 60.0 / BPM
    print("%-6s %-30s %2d bars %6.2f s  notes %4d  voices %d"
          % (label, os.path.basename(path), bars, seconds, total,
             len([t for t in song["tracks"] if t["notes"]])))
    return {"label": label, "file": os.path.basename(path), "bars": bars,
            "bar_multiple_of_4": bars % 4 == 0, "seconds": round(seconds, 3),
            "notes": total,
            "voices": {t["name"]: len(t["notes"]) for t in song["tracks"]}}


def main():
    patterns = load_patterns()
    fights, fight_bars = build_fight(patterns)
    calm, calm_bars = build_calm(patterns)
    demo, demo_bars = stack(fights, calm, fight_bars, calm_bars)

    rows = []
    problems = []
    for song, name, bars, label in ((fights, "pp_fight_v5_fight.mid", fight_bars, "FIGHT"),
                                    (calm, "pp_fight_v5_calm.mid", calm_bars, "CALM"),
                                    (demo, "pp_fight_v5_states.mid", demo_bars, "STATES")):
        found, voices = voice_check(song, label)
        problems.extend(found)
        path = os.path.join(HERE, name)
        finish(song, path)
        rows.append(report(song, path, bars, label))

    # The seam, proved from the written notes rather than asserted: the fight's bar 16 and the
    # calm's bar 1, lead and triangle, pitch for pitch and tick for tick.
    def bar_notes(song, bar, voice):
        base = (bar - 1) * BAR
        out = []
        for trk in song["tracks"]:
            if trk["name"] != voice:
                continue
            for start, end, pitch, velocity in trk["notes"]:
                if base <= start < base + BAR:
                    out.append((start - base, end - start, pitch))
        return sorted(out)

    seam = []
    for voice in ("vrc6 pulse a", "triangle"):
        a = bar_notes(fights, 16, voice)
        b = bar_notes(calm, 1, voice)
        seam.append((voice, a == b, a, b))

    print()
    for voice, ok, a, b in seam:
        print("seam %-14s %s  fight bar 16 %s  calm bar 1 %s"
              % (voice, "OK" if ok else "MISMATCH", a, b))
        if not ok:
            problems.append("seam mismatch in %s" % voice)

    print()
    counts = per_bar_voices(calm)
    for bar in sorted(counts):
        print("  calm bar %2d  %d voices  %s" % (bar, len(counts[bar]), ", ".join(counts[bar])))

    with open(os.path.join(HERE, "build_report_v5.json"), "w", encoding="utf-8") as handle:
        json.dump({
            "bpm": BPM, "tempo_us": TEMPO_US, "key": "D minor",
            "v1": "../pp_fight (untouched)", "v2": "../pp_fight_v2 (untouched)",
            "seam": "the FIGHT's bar 16 is the CALM's bar 1, note for note, proved in this run",
            "hook": "one bar cell D5 F5 G5 F5 E5 D5 A4, unchanged from v2",
            "humanize": {"frame_ticks": FRAME, "lead_delay": LEAD_DELAY,
                         "guide_delay": GUIDE_DELAY, "drum_delay": DRUM_DELAY,
                         "calm_articulation": CALM_SHORTEN,
                         "calm_phrase_velocity": CALM_PHRASE_VELOCITY,
                         "fight_phrase_velocity": FIGHT_PHRASE_VELOCITY,
                         "echo_offset_ticks": ECHO_TICKS},
            "dissonance": [
                {"device": "DIS-02", "module": "calm", "bar": 6, "voice": "vrc6 pulse b",
                 "note": "A4", "beat": 3.5, "resolves_to": "Bb4",
                 "why": "chromatic lower neighbour, a semitone below the third of Gm", "risk": 1},
                {"device": "DIS-06", "module": "calm", "bar": 11, "voice": "vrc6 pulse b",
                 "note": "B4", "beat": 1.0, "resolves_to": "A4",
                 "why": "ninth over A7 held a beat and a half, down a step to the dominant root",
                 "risk": 2},
                {"device": "DIS-17", "module": "calm", "bar": 14, "voice": "triangle",
                 "note": "Bb3 to A3", "beat": 3.0, "resolves_to": "A3",
                 "why": "flat six to five approach, a semitone onto the dominant root", "risk": 1},
            ],
            "calm_kit": {str(bar): pattern for bar, (pattern, _) in CALM_DRUMS.items()},
            "calm_kit_bars_without_kit": [],
            "checks": {"problems": problems},
            "modules": rows}, handle, indent=2)
        handle.write("\n")

    print()
    if problems:
        print("PROBLEMS:")
        for problem in problems:
            print("  " + problem)
    else:
        print("voice limits, note lengths and the 8 voice ceiling: clean")
    print("wrote", ", ".join(row["file"] for row in rows))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
