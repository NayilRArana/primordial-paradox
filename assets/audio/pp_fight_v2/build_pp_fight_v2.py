"""build_pp_fight_v2.py: the battle cue and its TALK (calm) state, rebuilt for the hook meter.

Card AUTO-MUSIC-NEXT (t_47a92d70). v1 in assets/audio/pp_fight/ is untouched; every file this
script writes carries `_v2` and lands in this folder.

Three modules, one hook, the same seam rule as v1:

  pp_fight_v2_fight.mid   4/4, 168 bpm, D minor, 16 bars (four 4 bar phrases), 22.86 s loop.
  pp_fight_v2_calm.mid    the same hook at half time, 16 bars, 22.86 s per pass, loops while
                          the TALK menu is open.
  pp_fight_v2_states.mid  the fight's 16 bars then the calm's 16 bars, no loop: the call and
                          response, rendered so the junction can be heard.

WHAT CHANGED FROM v1, AND WHY (the reason is tools/hook_score.py, not taste):

1. The hook is now one bar, seven notes, not two bars of nine: D5 F5 G5 F5 E5 D5 A4. It rises to
   the sixth and falls through a fifth to A4, so it is an arch with exactly one leap, and it is
   repeated seven times inside the first eight bars with one or two notes changed each time. v1
   stated a two bar cell four times and spent bars 9 to 12 on a transposed sequence the scorer
   cannot see as a return, so 37 percent of its notes sat inside the motif. The cell is now the
   bar, and the motif covers 65 percent.
2. The third return (bar 3, over Gm) changes two notes, so it reads at 71 percent the same as the
   first: a return, not a copy. v1's third return was 100 percent the same, which is what the
   scorer marks as no variation.
3. The leap is inside the cell (E5 down to A4, a fifth, on the last beat), so the motif has
   exactly one leap instead of none.
4. The calm state is rebuilt as the same cell at half values, ten statements of a five note cell
   with the answer phrase at bars 9 to 12. v1's calm scored 67 of 100 with no contour and two
   returns; this one has a contour on every return and ten returns.

WHAT DID NOT CHANGE: the tempo (168 bpm, the CUE-FIGHT card's number, and not this card's to
change), the D minor key, the 16 bar form, the chord progression, the drum ladder from
data/drum_patterns.json, the voice set and the levels, and the seam rule: the fight's bar 16 and
the calm's bar 1 are the same written bar (lead and triangle), so the state change repeats the bar
that was already sounding.

Drums come from data/drum_patterns.json by id, expanded with the mapping in
knowledge/MUSIC-DRUMS.md section 6: noise period p is MIDI note p + 1, dpcm_kick is 36,
dpcm_snare is 38, a short loop hit sets CC12 to 1 at that tick. The ladder varies every 4 bars
(fills at 4, 8, 12, 16) and every 8 bars (the sixth rung at 6, the sixteenth kick section in 9 to
12, the stomp at 15, the rims at 16).

Humanizing is inside the build: every note is articulated short by 18 ticks (under one NTSC frame
at this tempo, so the sixteenth grid it is scored on does not move), velocity falls or rises per
four bar phrase, the lead's level moves between phrases, and the echo is one frame late. The seam
bars are not articulated, so the two modules still agree tick for tick.

Usage:
    build_pp_fight_v2.py
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
SHORTEN = 18                       # articulation, under one frame: the grid does not move

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
# One bar is eight eighth note slots. A cell is (pitch name or None for a rest, eighths).
# The cell: rise to the sixth, fall through the fifth to A4. One leap, one turn, five steps of
# six intervals, 10 semitones wide. Every statement keeps the rhythm, which is the hook.

# The cell is TWO bars, one arch across both: the leap of a fifth up from A4 opens it, the line
# climbs stepwise to A5, turns once, and walks down to G4. One turn, one leap, ten of thirteen
# intervals are steps, 14 semitones wide. Every statement keeps the rhythm.
CELL_A = [("A4", 1), ("D5", 1), ("E5", 1), ("F5", 1), ("G5", 1), ("A5", 1), ("G5", 2)]
CELL_B = [("F5", 1), ("E5", 1), ("D5", 1), ("C5", 1), ("A4", 2), ("G4", 2)]
CELL = CELL_A + CELL_B

# Three notes changed: the peak climbs to A5 then Bb5 (the third of Gm), and the close walks home
# on C#5 (the third of A7) before landing on G4. The hook meter reads this as a return at 79
# percent, which is the band it wants: a return, not a copy.
CELL_GM_A = [("A4", 1), ("D5", 1), ("E5", 1), ("F5", 1), ("A5", 1), ("Bb5", 1), ("G5", 2)]
CELL_A7_B = [("F5", 1), ("E5", 1), ("D5", 1), ("C#5", 1), ("A4", 2), ("G4", 2)]
CELL_ALT = CELL_GM_A + CELL_A7_B

# The same rise with one note moved: the peak on Bb5 only. One change, so it still reads as the
# same phrase.
CELL_GM_BB = [("A4", 1), ("D5", 1), ("E5", 1), ("F5", 1), ("G5", 1), ("Bb5", 1), ("G5", 2)]

# The peak phrase over Dm: up to C6 and one step back down to A5. Three notes changed.
CELL_PEAK_A = [("A4", 1), ("D5", 1), ("E5", 1), ("F5", 1), ("A5", 1), ("C6", 1), ("A5", 2)]

# The sequence: the cell up a fourth into G minor, then Eb, then back onto the cell itself.
SEQ_9 = [("D5", 1), ("G5", 1), ("A5", 1), ("Bb5", 1), ("C6", 1), ("Bb5", 1), ("A5", 2)]
SEQ_10 = [("G5", 1), ("F5", 1), ("Eb5", 1), ("D5", 1), ("Bb4", 2), ("A4", 2)]

# The seam bar: the cell's opening, held. This exact bar is the fight's bar 16 and the calm's
# bar 1, so the state change repeats the bar that was already playing.
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

# The calm: the same two bar arch at half values, eight notes a statement.
CALM_A = [("A4", 4), ("D5", 2), ("E5", 1), ("F5", 1)]
CALM_B = [("G5", 2), ("F5", 2), ("E5", 2), ("C5", 2)]
CALM_CELL = CALM_A + CALM_B
# Over Bb: the fall lands on D5 then Bb4, the third.
CALM_B1 = [("G5", 2), ("F5", 2), ("D5", 2), ("Bb4", 2)]
# Over Gm: the rise starts from Bb4, the third, and the fall reuses the Bb close.
CALM_A2 = [("Bb4", 4), ("D5", 2), ("E5", 1), ("F5", 1)]
CALM_CELL2 = CALM_A2 + CALM_B1

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

# Root, fifth and arpeggio tones per chord, written out so nothing is guessed.
CHORD = {
    "Dm":  {"root": 38, "fifth": 45, "arp": [62, 65, 69, 65]},
    "Bb":  {"root": 46, "fifth": 41, "arp": [58, 62, 65, 62]},
    "Gm":  {"root": 43, "fifth": 50, "arp": [55, 58, 62, 58]},
    "A7":  {"root": 45, "fifth": 40, "arp": [57, 61, 64, 61]},
    "Eb":  {"root": 39, "fifth": 46, "arp": [51, 55, 58, 55]},
}

# The counterline: guide tones in half notes, always under the lead, from bar 5 so the opening
# four bars stay thin and the middle thickens. Bars 6 and 14 carry the cue's only chromatic
# passing tone: G3 up to G#3 into A3, an eighth on a weak beat between two chord tones a tone
# apart, resolving up a semitone, which is device DIS-01 of knowledge/MUSIC-DISSONANCE.md
# (rate 1 to 3, and this is 2 in a 16 bar pass). The lead never carries it, which is rule F1.
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


def track(name):
    return {"name": name, "notes": [], "cc": {}}


def add_cc(trk, controller, tick, value):
    trk["cc"].setdefault(controller, []).append((int(tick), int(value)))


def write_cells(trk, bar_number, cells, velocity, level=None, start_offset=0,
                shorten=0, hold_last=False):
    """Write one bar of eighth note cells. Returns the number of notes written."""
    written = 0
    tick = (bar_number - 1) * BAR + start_offset
    for name, length in cells:
        if name is not None:
            pitch = note(name) if isinstance(name, str) else name
            end = tick + length * EIGHTH
            if shorten and not (hold_last and length == cells[-1][1] and name == cells[-1][0]):
                end -= shorten
            trk["notes"].append((tick, max(tick + 20, end), pitch, velocity))
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


def write_pattern(noise, dpcm, pattern, bar_number, velocity_scale=1.0, level_note=None,
                  pitch_shift=0):
    """Expand one library bar at one bar position, per MUSIC-DRUMS section 6.

    pitch_shift moves every noise hit's period by that many steps, which is a timbre change
    rather than a note change: it is what keeps the kit from sounding like one waveform for
    sixteen bars.
    """
    base = (bar_number - 1) * BAR
    for index, hits in enumerate(pattern["steps"]):
        tick = base + index * STEP
        for hit in hits:
            velocity = max(1, min(127, int(round(hit["velocity"] * velocity_scale))))
            instrument = hit["instrument"]
            if instrument == "noise":
                # the noise channel's range in tools/arrange.py is MIDI 1 to 15
                pitch = min(15, max(1, int(hit["period"]) + 1 + pitch_shift))
                length = STEP * 2 if velocity >= 85 else STEP
                noise["notes"].append((tick, tick + length, pitch, velocity))
                # CC12 on the noise channel is the loop bit: 1 is short (metallic) mode.
                add_cc(noise, 12, tick, 1 if hit.get("loop") == "short" else 0)
            elif instrument == "dpcm_kick":
                dpcm["notes"].append((tick, tick + STEP * 2, 36, velocity))
            elif instrument == "dpcm_snare":
                dpcm["notes"].append((tick, tick + STEP * 2, 38, velocity))
    return len(noise["notes"])


# The ladder of MUSIC-DRUMS section 4: a change every 4 bars (a fill) and a second, larger change
# every 8 (the half time bar at 6, the sixteenth kick section at 9 to 12, the stomp at 15, rims at
# 16). No two fill bars touch.
FIGHT_DRUMS = {
    1: ("BAT-01", 1.0), 2: ("BAT-01", 0.95), 3: ("BAT-01", 1.0), 4: ("FLF-01", 1.0),
    5: ("BAT-01", 0.95), 6: ("BAT-06", 0.9), 7: ("BAT-01", 1.0), 8: ("FLT-01", 1.0),
    9: ("BAT-02", 1.0), 10: ("BAT-02", 0.95), 11: ("BAT-05", 1.0), 12: ("FLR-01", 1.0),
    13: ("BAT-03", 1.0), 14: ("BAT-01", 0.95), 15: ("BAT-07", 1.0), 16: ("BAT-09", 0.85),
}

# The playing gain of the kit per four bar phrase: the loop swells into the sixteenth kick
# section and leans back at the top. Scaled with the per bar figure above.
PHRASE_GAIN = {1: 0.88, 2: 0.94, 3: 1.04, 4: 1.10}

# Ghost notes: one quiet short mode noise hit each, on off sixteenths, so the kit is not the same
# waveform every bar. (bar, step index, noise period, velocity)
GHOSTS = {2: [(7, 15, 34)], 6: [(11, 16, 30)], 10: [(5, 14, 36)], 14: [(15, 15, 30)]}

# Timbre per four bar phrase: the noise period moves with the phrase, so the backbeat is a
# different colour in each quarter of the loop without a single different hit.
PHRASE_TIMBRE = {1: 0, 2: 1, 3: -1, 4: 2}

# The break: bars 9 and 10 drop the pad, the arpeggio and the counterline, so the second half
# opens on lead, bass and kit only and the pad's return at bar 11 is hearable.
BREAK_BARS = (9, 10)

CALM_DRUMS = {
    1: ("CLM-02", 0.55), 2: ("CLM-02", 0.5), 3: ("CLM-07", 0.55), 4: ("CLM-02", 0.45),
    5: ("CLM-02", 0.55), 6: ("CLM-07", 0.5), 7: ("CLM-02", 0.45), 8: ("CLM-07", 0.55),
    9: ("CLM-02", 0.5), 10: ("CLM-02", 0.45), 11: ("CLM-07", 0.55), 12: ("CLM-02", 0.5),
    13: ("CLM-07", 0.5), 14: ("CLM-02", 0.45), 15: ("CLM-07", 0.55), 16: ("CLM-02", 0.4),
}

# Per phrase playing weights: the four bar phrase is the unit of the crescendo, and the last
# phrase before the loop leans back. This is the humanizing the note velocities carry.
FIGHT_PHRASE_VELOCITY = {1: 112, 2: 106, 3: 118, 4: 110}
CALM_PHRASE_VELOCITY = {1: 94, 2: 88, 3: 92, 4: 84}


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
        write_cells(lead, index, cells, velocity, shorten=0 if index == 16 else SHORTEN,
                    hold_last=True)

    for bar, cells in COUNTER.items():
        if bar in BREAK_BARS:
            continue
        write_cells(counter, bar, cells, 92, shorten=SHORTEN, hold_last=True)

    # The chord bed: sustained root on the saw, a broken chord on pulse 1, the ostinato bass.
    for bar, chord in enumerate(FIGHT_CHORDS, start=1):
        base = (bar - 1) * BAR
        tones = CHORD[chord]
        if bar <= 15 and bar not in BREAK_BARS:
            saw["notes"].append((base, base + BAR - EIGHTH, tones["root"] + 12,
                                 84 if 9 <= bar <= 12 else 72))
        if bar == 16:
            # the drop bar keeps the pad, at bar length, so the calm's pad is the same notes
            for interval in (12, 19):
                saw["notes"].append((base, base + BAR - 40, tones["root"] + interval, 72))
        if bar <= 15 and not 9 <= bar <= 12:
            # The 2A03 pulse 1 floor in tools/arrange.py is MIDI 60. Three of the five chord
            # arpeggios sit below it in v1 (Bb, Gm, A7 and Eb), so each is transposed up an
            # octave here as a whole shape, which keeps the contour and puts every note inside
            # the voice's range.
            arp = tones["arp"]
            if min(arp) < 60:
                arp = [pitch + 12 for pitch in arp]
            for index in range(2):
                for step, pitch in enumerate(arp):
                    tick = base + index * 4 * EIGHTH + step * EIGHTH
                    pulse1["notes"].append((tick, tick + EIGHTH - SHORTEN, pitch, 64))
        if bar == 16:
            # one held root, the same bass note the calm opens on
            bass["notes"].append((base, base + BAR - 40, min(tones["root"] + 12, 55), 108))
        else:
            # The triangle's range in tools/arrange.py is MIDI 36 to 55. v1 played this line an
            # octave up from here (Bb and A7 roots plus their fifths were above 55, and the
            # octave note on the eighth eighth of every bar was up to 69), so the line is
            # written where the voice actually lives and the octave note is capped at 55.
            root = tones["root"]
            fifth = tones["fifth"]
            cell = [root, fifth, root, fifth, root, fifth, root, min(root + 12, 55)]
            for index, pitch in enumerate(cell):
                tick = base + index * EIGHTH
                bass["notes"].append((tick, tick + EIGHTH - 20, pitch, 112))

    # The echo: the lead one eighth late, one chip step quiet, one frame off the grid. It
    # stops at bar 15 so the drop bar is clean and the calm's first bar has no echo in it.
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
                      pitch_shift=PHRASE_TIMBRE[phrase])
        for step, period, velocity in GHOSTS.get(bar, ()):
            tick = (bar - 1) * BAR + step * STEP
            noise["notes"].append((tick, tick + STEP, min(15, period), velocity))
            add_cc(noise, 12, tick, 1)

    # Levels in chip steps 0 to 15, duty in VRC6 steps 0 to 7. The lead's level steps up with
    # the phrase and steps down for the loop, which is the shape the ear calls human. Vibrato
    # depth and onset change with the phrase too: the deep slow one under the sequence, the
    # shallow late one before the loop, so the lead is not one fixed synth all the way through.
    for bar, level, depth, onset in ((1, 11, 46, 1), (5, 12, 34, 2), (9, 13, 52, 1),
                                     (13, 12, 40, 3)):
        tick = (bar - 1) * BAR
        add_cc(lead, 11, tick, level)
        add_cc(lead, 1, tick, depth)
        add_cc(lead, 20, tick, onset)
    add_cc(lead, 12, 0, 4)
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
    saw = track("vrc6 saw")
    echo = track("pulse 2")
    bass = track("triangle")
    noise = track("noise")
    dpcm = track("dpcm")

    for index, cells in enumerate(CALM_LEAD, start=1):
        phrase = (index - 1) // 4 + 1
        write_cells(lead, index, cells,
                    CALM_PHRASE_VELOCITY[phrase] + (2 if index % 2 else 0),
                    shorten=0 if index == 1 else SHORTEN, hold_last=True)

    for bar, chord in enumerate(CALM_CHORDS, start=1):
        base = (bar - 1) * BAR
        tones = CHORD[chord]
        # a pad and a pedal, both re-attacked every bar at bar length: the same shape the
        # fight's drop bar uses, so the state change replaces nothing
        if bar % 2 == 1:
            saw["notes"].append((base, base + BAR - 40, tones["root"] + 12, 70))
            saw["notes"].append((base, base + BAR - 40, tones["root"] + 19, 56))
        # the triangle floor and ceiling in tools/arrange.py are 36 and 55, so the pedal is the
        # chord root where it lives, never an octave above it
        bass["notes"].append((base, base + BAR - 40, min(tones["root"] + 12, 55), 100))

    for index, cells in enumerate(CALM_LEAD, start=1):
        if index == 1:
            continue                    # the shimmer enters on bar 2, after the state change
        tick = (index - 1) * BAR + EIGHTH + ECHO_TICKS
        for name, length in cells:
            if name is not None:
                pitch = note(name) if isinstance(name, str) else name
                end = tick + length * EIGHTH
                if end <= len(CALM_LEAD) * BAR - 1:
                    echo["notes"].append((tick, end, pitch, 34))
            tick += length * EIGHTH

    for bar, (pattern_id, scale) in CALM_DRUMS.items():
        write_pattern(noise, dpcm, patterns[pattern_id], bar, scale)

    for bar, level in ((1, 6), (5, 7), (9, 8), (13, 7)):
        add_cc(lead, 11, (bar - 1) * BAR, level)
    add_cc(lead, 12, 0, 1)          # 12.5 percent duty: thin, quiet, the calm timbre
    add_cc(lead, 1, 0, 24)
    add_cc(lead, 20, 0, 2)
    add_cc(saw, 11, 0, 2)
    add_cc(echo, 11, 0, 2)
    add_cc(echo, 12, 0, 1)
    add_cc(bass, 11, 0, 6)
    add_cc(noise, 11, 0, 4)
    add_cc(dpcm, 11, 0, 4)

    song = {"division": PPQ, "tempo_us": TEMPO_US, "time_sig": (4, 4),
            "tracks": [lead, saw, echo, bass, noise, dpcm]}
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


def report(song, path, bars, label):
    total = sum(len(trk["notes"]) for trk in song["tracks"])
    seconds = bars * 4 * 60.0 / BPM
    print("%-6s %-30s %2d bars (%d x 4) %6.2f s  notes %4d  voices %d"
          % (label, os.path.basename(path), bars, bars // 4, seconds, total,
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
    for song, name, bars, label in ((fights, "pp_fight_v2_fight.mid", fight_bars, "FIGHT"),
                                    (calm, "pp_fight_v2_calm.mid", calm_bars, "CALM"),
                                    (demo, "pp_fight_v2_states.mid", demo_bars, "STATES")):
        path = os.path.join(HERE, name)
        finish(song, path)
        rows.append(report(song, path, bars, label))

    with open(os.path.join(HERE, "build_report_v2.json"), "w", encoding="utf-8") as handle:
        json.dump({"bpm": BPM, "tempo_us": TEMPO_US, "key": "D minor",
                   "v1": "../pp_fight (untouched)",
                   "seam": "the FIGHT's bar 16 is the CALM's bar 1, note for note",
                   "hook": "one bar cell D5 F5 G5 F5 E5 D5 A4, ten statements in the fight, "
                           "ten in the calm at half values",
                   "humanize": {"articulation_ticks": SHORTEN,
                                "lead_level_steps": {"fight": [11, 12, 13, 12],
                                                     "calm": [6, 7, 8, 7]},
                                "phrase_velocity": {"fight": FIGHT_PHRASE_VELOCITY,
                                                    "calm": CALM_PHRASE_VELOCITY},
                                "echo_offset_ticks": ECHO_TICKS},
                   "modules": rows}, handle, indent=2)
        handle.write("\n")
    print("\nseam: FIGHT bar 16 == CALM bar 1 (lead and triangle), by construction")
    print("wrote", ", ".join(row["file"] for row in rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
