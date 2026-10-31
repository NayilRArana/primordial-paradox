"""build_pp_fight.py: CUE-FIGHT, the battle cue and its TALK (calm) state.

Two modules, one hook. Clean room: every note here is written for this card.

  pp_fight_fight.mid   4/4, 168 bpm, D minor, 16 bars (four 4 bar phrases), 22.86 s loop.
  pp_fight_calm.mid    the same hook at half time, 8 bars, 22.86 s per pass, loops while
                       the TALK menu is open.
  pp_fight_states.mid  the fight's 16 bars then the calm's 8 bars, no loop: the call and
                       response, rendered so the junction can be heard.

THE SEAM. The fight's last bar (bar 16) and the calm's first bar are the same two bars of
material: the lead plays D5 D5 F5 as half time quarters and the triangle holds one D3, with
the kit dropping to rims. Entering the calm therefore repeats the bar that was just playing,
and leaving it (calm bar 8 opens on the fifth, the fight opens on D5) lands on the hook's
first note. No new material at the boundary, so there is nothing to pop.

THE HOOK (4 bars, bars 1 to 4, 19 notes, A4 to G5, one leap larger than a fourth at the same
bar 3 downbeat every statement, one note outside D minor in the phrase, the C# leading tone
in bar 4). It is stated, repeated with a changed ending (bar 8), sequenced up a fourth into
G minor (bars 9 to 12), then restated and cut into the seam bar (13 to 16).

Drums come from data/drum_patterns.json by id, expanded with the mapping in
knowledge/MUSIC-DRUMS.md section 6: noise period p is MIDI note p + 1, dpcm_kick is 36,
dpcm_snare is 38, a short loop hit sets CC12 to 1 at that tick. The variation ladder is the
one in section 4 of that file: fill at bar 4, drop the kick at 6, fill at 8, the sixteenth
kick section at 9 to 12, unison stomp at 15, rims before the loop at 16 on the fight; a rim
pulse then two strikes per two bars on the calm, which is rung 0 and rung 1 only.

Levels are control change 11 in chip steps 0 to 15, as tools/render_chip.py reads them. Duty
is control change 12, vibrato depth control change 1 and vibrato onset control change 20 in
eighths. The echo voice is one frame late (22 ticks at this tempo) and one chip step quiet.

Usage:
    build_pp_fight.py
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


def r():
    return None


# --------------------------------------------------------------- the hook and its forms
# One bar is eight eighth note slots. A cell is (pitch name or None for a rest, eighths).

HOOK_HEAD = [("D5", 1), ("D5", 1), (None, 2), ("F5", 2), ("E5", 1), ("D5", 1)]
HOOK_SECOND = [("C5", 1), ("C5", 1), (None, 2), ("Bb4", 2), ("A4", 2)]
HOOK_THIRD = [("F5", 1), ("F5", 1), (None, 2), ("G5", 2), ("F5", 1), ("E5", 1)]
HOOK_CLOSE = [("D5", 1), ("C#5", 1), ("E5", 1), ("C#5", 1), ("D5", 4)]

# The seam bar: the head's opening, in the calm's half time. This exact bar is the fight's
# bar 16 and the calm's bar 1, so the state change repeats the bar that was already playing.
SEAM_BAR = [("D5", 2), ("D5", 2), (None, 4)]

FIGHT_LEAD = [
    HOOK_HEAD, HOOK_SECOND, HOOK_THIRD, HOOK_CLOSE,                       # 1 to 4, the statement
    HOOK_HEAD, HOOK_SECOND, HOOK_THIRD,                                    # 5 to 7, the repeat
    [("E5", 1), ("F5", 1), ("G5", 2), ("A5", 2), (None, 2)],               # 8, opened, changed ending
    [("G5", 1), ("G5", 1), (None, 2), ("Bb5", 2), ("A5", 1), ("G5", 1)],   # 9, sequenced up a fourth
    [("F5", 1), ("F5", 1), (None, 2), ("Eb5", 2), ("D5", 2)],              # 10
    [("Bb5", 1), ("Bb5", 1), (None, 2), ("C6", 2), ("Bb5", 1), ("A5", 1)], # 11
    [("G5", 1), ("F5", 1), ("E5", 1), ("C#5", 1), ("D5", 2), (None, 2)],   # 12, walks home
    HOOK_HEAD, HOOK_SECOND,                                                # 13, 14
    [("D5", 1), ("D5", 1), (None, 1), ("F5", 2), ("E5", 1), ("D5", 1), ("C5", 1)],  # 15, varied head
    SEAM_BAR,                                                             # 16, the seam
]

CALM_LEAD = [
    SEAM_BAR,                                                             # 1, the fight's bar 16
    [("F5", 4), ("E5", 2), ("D5", 2)],                                     # 2
    [("C5", 2), ("C5", 2), (None, 4)],                                     # 3
    [("Bb4", 4), ("A4", 2), (None, 2)],                                    # 4
    [("F5", 2), ("F5", 2), (None, 4)],                                     # 5
    [("G5", 4), ("F5", 2), ("E5", 2)],                                     # 6, the arch peaks
    [("E5", 2), ("C#5", 2), ("E5", 2), ("A4", 2)],                          # 7
    [("D5", 6), (None, 2)],                                                 # 8, closes, hands back
    SEAM_BAR,                                                             # 9, the statement again
    [("F5", 4), ("E5", 2), ("D5", 2)],                                     # 10
    [("C5", 2), ("C5", 2), (None, 4)],                                     # 11
    [("Bb4", 4), ("A4", 2), (None, 2)],                                    # 12
    [("D5", 2), ("D5", 2), (None, 2), ("F5", 2)],                           # 13, the head, varied
    [("E5", 4), ("D5", 2), (None, 2)],                                     # 14, the head's fall
    [("E5", 2), ("C#5", 2), ("E5", 2), ("A4", 2)],                          # 15
    [("D5", 6), (None, 2)],                                                 # 16, closed, loops
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

# The counterline, fight bars 9 to 16: guide tones in half notes, always under the lead.
COUNTER = {
    9:  [("D4", 4), ("Bb3", 4)],
    10: [("Bb3", 4), ("G3", 4)],
    11: [("D4", 4), ("F4", 4)],
    12: [("C#4", 4), ("E4", 4)],
    13: [("A3", 4), ("F4", 4)],
    14: [("D4", 4), ("F4", 4)],
    15: [("Bb3", 4), ("D4", 4)],
    16: [("A3", 4), (None, 4)],
}


def track(name):
    return {"name": name, "notes": [], "cc": {}}


def add_cc(trk, controller, tick, value):
    trk["cc"].setdefault(controller, []).append((int(tick), int(value)))


def write_cells(trk, bar_number, cells, velocity, level=None, start_offset=0):
    """Write one bar of eighth note cells. Returns the number of notes written."""
    written = 0
    tick = (bar_number - 1) * BAR + start_offset
    for name, length in cells:
        if name is not None:
            pitch = note(name) if isinstance(name, str) else name
            trk["notes"].append((tick, tick + length * EIGHTH, pitch, velocity))
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


def write_pattern(noise, dpcm, pattern, bar_number, velocity_scale=1.0, level_note=None):
    """Expand one library bar at one bar position, per MUSIC-DRUMS section 6."""
    base = (bar_number - 1) * BAR
    for index, hits in enumerate(pattern["steps"]):
        tick = base + index * STEP
        for hit in hits:
            velocity = max(1, min(127, int(round(hit["velocity"] * velocity_scale))))
            instrument = hit["instrument"]
            if instrument == "noise":
                pitch = min(16, max(1, int(hit["period"]) + 1))
                length = STEP * 2 if velocity >= 85 else STEP
                noise["notes"].append((tick, tick + length, pitch, velocity))
                # CC12 on the noise channel is the loop bit: 1 is short (metallic) mode.
                add_cc(noise, 12, tick, 1 if hit.get("loop") == "short" else 0)
            elif instrument == "dpcm_kick":
                dpcm["notes"].append((tick, tick + STEP * 2, 36, velocity))
            elif instrument == "dpcm_snare":
                dpcm["notes"].append((tick, tick + STEP * 2, 38, velocity))
    return len(noise["notes"])


FIGHT_DRUMS = {
    1: ("BAT-01", 1.0), 2: ("BAT-01", 0.95), 3: ("BAT-01", 1.0), 4: ("FLF-01", 1.0),
    5: ("BAT-01", 0.95), 6: ("BAT-06", 0.9), 7: ("BAT-01", 1.0), 8: ("FLT-01", 1.0),
    9: ("BAT-02", 1.0), 10: ("BAT-02", 0.95), 11: ("BAT-05", 1.0), 12: ("FLR-01", 1.0),
    13: ("BAT-01", 1.0), 14: ("BAT-01", 0.95), 15: ("BAT-07", 1.0), 16: ("BAT-09", 0.85),
}

CALM_DRUMS = {
    1: ("CLM-02", 0.55), 2: ("CLM-02", 0.5), 3: ("CLM-07", 0.55), 4: ("CLM-02", 0.45),
    5: ("CLM-02", 0.55), 6: ("CLM-07", 0.5), 7: ("CLM-02", 0.45), 8: ("CLM-07", 0.55),
    9: ("CLM-02", 0.5), 10: ("CLM-02", 0.45), 11: ("CLM-07", 0.55), 12: ("CLM-02", 0.5),
    13: ("CLM-07", 0.5), 14: ("CLM-02", 0.45), 15: ("CLM-07", 0.55), 16: ("CLM-02", 0.4),
}


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
        velocity = 112 if index % 4 == 1 else (104 if index % 2 else 108)
        write_cells(lead, index, cells, velocity)

    for bar, cells in COUNTER.items():
        write_cells(counter, bar, cells, 92)

    # The chord bed: sustained root on the saw, a broken chord on pulse 1, the ostinato bass.
    for bar, chord in enumerate(FIGHT_CHORDS, start=1):
        base = (bar - 1) * BAR
        tones = CHORD[chord]
        if bar <= 15:
            saw["notes"].append((base, base + BAR - EIGHTH, tones["root"] + 12,
                                 84 if 9 <= bar <= 12 else 72))
        if bar == 16:
            # the drop bar keeps the pad, at bar length, so the calm's pad is the same notes
            for interval in (12, 19):
                saw["notes"].append((base, base + BAR - 40, tones["root"] + interval, 72))
        if bar <= 15 and not 9 <= bar <= 12:
            for index in range(2):
                for pitch in tones["arp"]:
                    tick = base + index * 4 * EIGHTH + (tones["arp"].index(pitch)) * EIGHTH
                    pulse1["notes"].append((tick, tick + EIGHTH, pitch, 64))
        if bar == 16:
            # one held root, the same bass note the calm opens on
            bass["notes"].append((base, base + BAR - 40, tones["root"] + 12, 108))
        else:
            root = tones["root"] + 12
            fifth = tones["fifth"] + 12
            cell = [root, fifth, root, fifth, root, fifth, root, root + 12]
            for index, pitch in enumerate(cell):
                tick = base + index * EIGHTH
                bass["notes"].append((tick, tick + EIGHTH - 20, pitch, 112))

    # The echo: the lead one eighth late, one chip step quiet, one frame off the grid. It
    # stops at bar 14 so the drop bar is clean and the calm's first bar has no echo in it.
    for index, cells in enumerate(FIGHT_LEAD, start=1):
        if index >= 15:
            continue
        shift = (index - 1) * BAR + EIGHTH + ECHO_TICKS
        tick = shift
        for name, length in cells:
            if name is not None:
                pitch = note(name) if isinstance(name, str) else name
                end = tick + length * EIGHTH
                if end <= 16 * BAR - 1:
                    echo["notes"].append((tick, end, pitch, 44))
            tick += length * EIGHTH

    for bar, (pattern_id, scale) in FIGHT_DRUMS.items():
        write_pattern(noise, dpcm, patterns[pattern_id], bar, scale)

    # Levels in chip steps 0 to 15, duty in VRC6 steps 0 to 7.
    add_cc(lead, 11, 0, 12)
    add_cc(lead, 12, 0, 4)
    add_cc(lead, 1, 0, 46)
    add_cc(lead, 20, 0, 1)
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
        write_cells(lead, index, cells, 96 if index % 2 else 92)

    for bar, chord in enumerate(CALM_CHORDS, start=1):
        base = (bar - 1) * BAR
        tones = CHORD[chord]
        # a pad and a pedal, both re-attacked every bar at bar length: the same shape the
        # fight's drop bar uses, so the state change replaces nothing
        if bar % 2 == 1:
            saw["notes"].append((base, base + BAR - 40, tones["root"] + 12, 70))
            saw["notes"].append((base, base + BAR - 40, tones["root"] + 19, 56))
        bass["notes"].append((base, base + BAR - 40, tones["root"] + 12, 100))

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

    add_cc(lead, 11, 0, 7)
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
    print("%-6s %-28s %2d bars (%d x 4) %6.2f s  notes %4d  voices %d"
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
    for song, name, bars, label in ((fights, "pp_fight_fight.mid", fight_bars, "FIGHT"),
                                    (calm, "pp_fight_calm.mid", calm_bars, "CALM"),
                                    (demo, "pp_fight_states.mid", demo_bars, "STATES")):
        path = os.path.join(HERE, name)
        finish(song, path)
        rows.append(report(song, path, bars, label))

    with open(os.path.join(HERE, "build_report.json"), "w", encoding="utf-8") as handle:
        json.dump({"bpm": BPM, "tempo_us": TEMPO_US, "key": "D minor",
                   "seam": "the FIGHT's bar 16 is the CALM's bar 1, note for note",
                   "modules": rows}, handle, indent=2)
    print("\nseam: FIGHT bar 16 == CALM bar 1 (lead and triangle), by construction")
    print("wrote", ", ".join(row["file"] for row in rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
