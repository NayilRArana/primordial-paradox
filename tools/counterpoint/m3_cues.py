"""M3 Baroque cues: a two-part invention on the Primordial Paradox leitmotif, and a
three-voice fugue exposition for the fight, both built under the M1a checker.

Card t_65512e1c (M3 BAROQUE-CUES). Plan: knowledge/COUNTERPOINT-PLAN-2026-10-26.md.
The generator M1b built (tools/counterpoint/generate.py) writes its own subjects; this
module is the other half of the plan: it takes an EXISTING melody (the project's own
leitmotif, read out of pp_01_title_v7.mid track "vrc6 pulse a") and builds Baroque
counterpoint around it without changing a single note of it.

What it makes
-------------
title v10  A minor, 3/4, 126 bpm, 32 bars. Two-part invention with a triangle continuo:
           pulse 1 states the leitmotif, pulse 2 answers it an octave below, each statement
           carries a generated countersubject in the other voice (and the pair is measured
           again with the voices swapped, which is the invertibility test the plan asks
           for), the episodes sequence the leitmotif head, and the triangle walks the
           continuo. The leitmotif is stated four times and never altered: every note of
           it is marked fixed and the repair pass may not touch it.
fight      A minor, 4/4, 168 bpm, 16 bars. Three-voice fugue exposition with driving
           rhythm: subject on pulse 1, tonal answer a fifth below on pulse 2 (one chromatic
           note adjusted, the classic tonal answer), the subject in the triangle two
           octaves down, countersubjects over each entry, an episode on the head, a second
           round of entries and a cadence. Noise hats on the off-beat eighth and a dpcm
           kick/snare carry the drive; the checker ignores unpitched voices.

How correctness is obtained (not asserted)
------------------------------------------
1. Every free pitch is chosen only among pitches that are consonant at every onset inside
   its own span against every other sounding voice, that do not make a parallel perfect
   interval, and that neither cross nor crowd the neighbouring voice.
2. The result is then measured by the same engine the cue gate uses,
   rules.analyse(score, profile="free"), and by the clash counter, clash.analyse.
3. If the measure is not clean, a repair pass moves or rests only FREE notes (a fixed
   leitmotif note is never touched), re-measuring after each edit. The build fails loudly
   rather than reporting a piece that did not measure clean.

Usage
    python tools/counterpoint/m3_cues.py --piece title --midi out/title_v10.mid
    python tools/counterpoint/m3_cues.py --piece fight --out-dir out/m3
    python tools/counterpoint/m3_cues.py --both --out-dir out/m3

TWO TAKES PER CUE (card t_65512e1c asks for the two best of each, picked by Nayil's ear)
---------------------------------------------------------------------------------------
--variant 2 is take B, and it is a different piece, not a reseed: the voices swap roles
(the lower voice states the subject first), the harmony plan is different, and the
continuo and the drums move differently. Take B keeps the tempo each cue is ruled to
(data/title_timing.json pins the title at 126 bpm; gamedev ruling D3 keeps the fight at
168 bpm so a state cut lands on a bar line), because a candidate that moved either would
break the game timing rather than the music.
    python tools/counterpoint/m3_cues.py --piece title --variant 2 --out-dir out/m3

Exit codes: 0 every piece measured clean, 1 a piece did not, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
for path in (HERE, TOOLS):
    if path not in sys.path:
        sys.path.insert(0, path)

import clash  # noqa: E402
import rules  # noqa: E402

DIVISION = 480
KEY_NAME = "A minor"
SCALE_PCS = frozenset((9, 11, 0, 2, 4, 5, 7))   # A natural minor
LEADING_PC = 8                                   # G#, the raised seventh the cadences use
CONSONANT = frozenset((0, 3, 4, 7, 8, 9))
PERFECT = frozenset((0, 7))

# Chord shapes as pitch classes, in A minor.
CHORDS = {
    "i": (9, 0, 4),
    "V": (4, 8, 11),
    "V7": (4, 8, 11, 2),
    "III": (0, 4, 7),
    "iv": (2, 5, 9),
    "VI": (5, 9, 0),
    "VII": (7, 11, 2),
    "ii": (11, 2, 5),
}

# The order numerals are preferred in when two fit the fixed line equally well. It is a
# progression taste, not a rule: the checker's verdict does not depend on it.
PREFERENCE = ("i", "V", "iv", "III", "VI", "VII", "ii", "V7")

RANGES = {
    "pulse 1": (57, 81),    # A3 to A5, inside the checker's declared 55 to 83
    "pulse 2": (55, 76),    # G3 to E5, inside 43 to 96
    "triangle": (36, 52),   # C2 to E3, inside 36 to 55
}
ORDER = ("pulse 1", "pulse 2", "triangle")

# The leitmotif, as read from pp_01_title_v7.mid bars 3 to 6 (track "vrc6 pulse a"):
# (bar index from the first bar of the motif, slot in eighths, length in eighths, pitch).
LEITMOTIF = (
    (0, 0, 3, 76), (0, 3, 1, 74), (0, 4, 1, 72), (0, 5, 1, 71),
    (1, 0, 6, 71),
    (2, 0, 3, 76), (2, 3, 1, 72), (2, 4, 1, 74), (2, 5, 1, 76),
    (3, 0, 3, 71), (3, 3, 1, 68), (3, 4, 1, 69), (3, 5, 1, 71),
)
V7_MIDI = os.path.join(ROOT, "assets", "audio", "pp_01_title_v7", "pp_01_title_v7.mid")
V7_TRACK = "vrc6 pulse a"
V7_FIRST_BAR = 3   # one-based bar in v7 where the leitmotif starts


# --------------------------------------------------------------------- utilities


def in_key(pitch):
    pc = pitch % 12
    return pc in SCALE_PCS or pc == LEADING_PC


def key_pitches(low, high):
    return [p for p in range(low, high + 1) if in_key(p)]


def consonant(a, b):
    return abs(a - b) % 12 in CONSONANT


def pitch_name(value):
    return rules.pitch_name(value)


# ------------------------------------------------------------------ the leitmotif


def leitmotif_from_v7():
    """The leitmotif, read out of v7 rather than retyped, with the read checked.

    A mismatch with the constant below is reported, not repaired: a silent difference
    between the score and the motif the piece quotes is exactly the kind of drift this
    card exists to stop.
    """
    import hook_score

    if not os.path.exists(V7_MIDI):
        return LEITMOTIF, {"source": "constant", "reason": "v7 midi not present"}
    song = hook_score.read_smf(V7_MIDI)
    division = song["division"]
    bar_ticks = division * 3   # v7 is in 3/4
    track = None
    for candidate in song["tracks"]:
        if candidate["name"].strip().lower() == V7_TRACK:
            track = candidate
            break
    if track is None:
        return LEITMOTIF, {"source": "constant", "reason": "no %s track in v7" % V7_TRACK}
    start = (V7_FIRST_BAR - 1) * bar_ticks
    stop = start + 4 * bar_ticks
    eighth = division // 2
    cell = []
    for note_start, note_end, pitch, _velocity in sorted(track["notes"]):
        if not (start <= note_start < stop):
            continue
        offset = note_start - start
        cell.append((offset // bar_ticks, (offset % bar_ticks) // eighth,
                     max(1, (note_end - note_start) // eighth), pitch))
    cell = tuple(sorted(cell))
    provenance = {"source": "v7 midi", "track": V7_TRACK, "first_bar": V7_FIRST_BAR,
                  "notes": len(cell), "matches_constant": cell == LEITMOTIF}
    return (cell if cell else LEITMOTIF), provenance


def head_of(cell, steps=0):
    """The first bar of the leitmotif, moved by diatonic steps inside A minor."""
    out = []
    for _bar, slot, length, pitch in [n for n in cell if n[0] == 0]:
        moved = pitch
        for _step in range(abs(steps)):
            moved = moved + 1 if steps > 0 else moved - 1
            while not in_key(moved):
                moved = moved + 1 if steps > 0 else moved - 1
        out.append((0, slot, length, moved))
    return tuple(out)


def close_of(head):
    """The pitch a head phrase rests on: its own third note, held (as the motif does)."""
    return head[2][3]


def natural_below(pitch):
    """The next pitch down inside A natural minor (never the raised seventh)."""
    moved = pitch - 1
    while moved % 12 not in SCALE_PCS:
        moved -= 1
    return moved


# ------------------------------------------------------------------- the analysis


def analyse_notes(notes, time_sig, tempo_us):
    """The M1a engine and the clash counter on an in-memory note set."""
    rules_score = rules.Score.from_notes(
        {voice: [rules.Note(*n) for n in note_list] for voice, note_list in notes.items()},
        division=DIVISION, time_sig=time_sig, tempo_us=tempo_us,
        key=rules.parse_key(KEY_NAME))
    result = rules.analyse(rules_score, profile="free")
    clash_score = clash.Score.from_notes(notes, DIVISION, time_sig, tempo_us,
                                         key_name=KEY_NAME)
    events = clash.analyse(clash_score)
    summary = clash.summarise(clash_score, events)
    return result, summary, events


def hard_findings(result):
    return [f for f in result["findings"] if f["severity"] == "hard"]


def rule_counts(result):
    counts = {}
    for finding in result["findings"]:
        counts[finding["rule"]] = counts.get(finding["rule"], 0) + 1
    return dict(sorted(counts.items()))


# ---------------------------------------------------------------- the note set


class Piece(object):
    """A bar-based sketch: fixed material per voice, then generated free voices."""

    def __init__(self, name, beats, bpm, bars, seed=1):
        self.name = name
        self.beats = beats
        self.bpm = bpm
        self.bars = bars
        self.bar_ticks = beats * DIVISION
        self.ticks_per_eighth = DIVISION // 2
        self.eighths = (beats * DIVISION) // self.ticks_per_eighth
        self.tempo_us = int(round(60_000_000.0 / bpm))
        self.time_sig = (beats, 4)
        self.seed = seed
        self.rng = random.Random(seed)
        self.notes = {name: [] for name in ORDER}
        self.fixed = {name: set() for name in ORDER}
        self.numerals = [None] * bars

    # -- placement ------------------------------------------------------------

    def put(self, voice, bar, slot, length, pitch, fixed=False, velocity=100):
        start = bar * self.bar_ticks + slot * self.ticks_per_eighth
        end = start + length * self.ticks_per_eighth
        self.notes[voice].append((start, end, pitch, velocity))
        if fixed:
            self.fixed[voice].add((start, pitch))

    def put_cell(self, voice, cell, bar_offset, semitones=0, fixed=True, velocity=100):
        for bar, slot, length, pitch in cell:
            self.put(voice, bar_offset + bar, slot, length, pitch + semitones,
                     fixed=fixed, velocity=velocity)

    # -- sounding -------------------------------------------------------------

    def sounding(self, voice, tick):
        out = []
        for start, end, pitch, _velocity in self.notes[voice]:
            if start <= tick and end > tick:
                out.append((start, pitch))
        return out

    def other_voices(self, voice):
        return [name for name in ORDER if name != voice]

    def instants(self, voice, start, end):
        """The onsets a candidate note must answer for: its own, plus every other
        voice's onset inside its span."""
        out = {start}
        for other in self.other_voices(voice):
            for note_start, _note_end, _pitch, _velocity in self.notes[other]:
                if start < note_start < end:
                    out.add(note_start)
        return sorted(out)

    def violations(self, voice, pitch, start, end):
        """Every reason this pitch is refused outright, as one short string or None."""
        range_low, range_high = RANGES[voice]
        if not (range_low <= pitch <= range_high):
            return "range"
        if not in_key(pitch):
            return "key"
        for instant in self.instants(voice, start, end):
            for other in self.other_voices(voice):
                for _note_start, other_pitch in self.sounding(other, instant):
                    if not consonant(pitch, other_pitch):
                        return "dissonant against %s %s" % (other, pitch_name(other_pitch))
        index = ORDER.index(voice)
        if index > 0:
            above = ORDER[index - 1]
            limit = 19 if voice == "triangle" else 12
            for instant in self.instants(voice, start, end):
                for _note_start, other_pitch in self.sounding(above, instant):
                    if pitch > other_pitch:
                        return "crosses %s" % above
                    if other_pitch - pitch > limit:
                        return "spacing to %s" % above
        if index < len(ORDER) - 1:
            below = ORDER[index + 1]
            for instant in self.instants(voice, start, end):
                for _note_start, other_pitch in self.sounding(below, instant):
                    if pitch < other_pitch:
                        return "below %s" % below
        return None

    def previous_note(self, voice, start):
        best = None
        for note in self.notes[voice]:
            if note[0] < start and (best is None or note[0] > best[0]):
                best = note
        return (best[0], best[2]) if best else None

    def parallel_perfect(self, voice, pitch, start):
        """True when this move would make a parallel fifth or octave with another voice."""
        previous = self.previous_note(voice, start)
        if previous is None:
            return False
        prev_start, prev_pitch = previous
        for other in self.other_voices(voice):
            before = self.sounding(other, prev_start)
            after = self.sounding(other, start)
            if not before or not after:
                continue
            prev_other = min(before, key=lambda item: abs(item[1] - prev_pitch))[1]
            now_other = min(after, key=lambda item: abs(item[1] - pitch))[1]
            if abs(prev_pitch - prev_other) % 12 not in PERFECT:
                continue
            if abs(pitch - now_other) % 12 not in PERFECT:
                continue
            if (pitch - prev_pitch) * (now_other - prev_other) > 0:
                return True
        return False

    # -- chords ---------------------------------------------------------------

    def fit_numerals(self, hint):
        """Choose each bar's chord: the one whose triad best fits the fixed notes."""
        table = {}
        for bar in range(self.bars):
            start = bar * self.bar_ticks
            stop = start + self.bar_ticks
            fixed = []
            for voice in ORDER:
                for note_start, _end, pitch, _velocity in self.notes[voice]:
                    if start <= note_start < stop and (note_start, pitch) in self.fixed[voice]:
                        weight = 3.0 if note_start % self.bar_ticks == 0 else 1.0
                        if note_start % DIVISION == 0:
                            weight += 1.0
                        fixed.append((pitch, weight))
            ranked = []
            for numeral in PREFERENCE:
                pcs = set(CHORDS[numeral])
                cost = 0.0
                for pitch, weight in fixed:
                    pc = pitch % 12
                    if pc in pcs:
                        continue
                    if (pc - 1) % 12 in pcs or (pc + 1) % 12 in pcs:
                        cost += 1.0 * weight
                    else:
                        cost += 3.0 * weight
                if hint and bar < len(hint) and numeral != hint[bar]:
                    # The planned progression is the plan; the fit only nudges a bar whose
                    # fixed notes are strongly foreign to the planned chord.
                    cost += 6.0
                ranked.append((cost, PREFERENCE.index(numeral), numeral))
            ranked.sort()
            self.numerals[bar] = ranked[0][2]
            table[bar + 1] = {"chosen": ranked[0][2],
                              "next": [(numeral, round(cost, 2))
                                       for cost, _order, numeral in ranked[1:3]]}
        return table


# ------------------------------------------------------------- free voice search


def pick_pitch(piece, voice, start, length, numeral, bass_voice=False, accented=False):
    """The best legal pitch for a free note, or None when nothing is legal."""
    end = start + length
    previous = piece.previous_note(voice, start)
    prev_pitch = previous[1] if previous else None
    chord_pcs = set(CHORDS[numeral])
    root_pc = CHORDS[numeral][0]
    centered = (RANGES[voice][0] + RANGES[voice][1]) / 2.0
    options = []
    for pitch in key_pitches(*RANGES[voice]):
        # The raised seventh belongs to the continuo, which states it on the dominant;
        # an upper line that took it would owe an upward resolution the search cannot
        # always pay, so it is not offered to the free upper voices.
        if not bass_voice and pitch % 12 == LEADING_PC:
            continue
        if piece.violations(voice, pitch, start, end):
            continue
        if piece.parallel_perfect(voice, pitch, start):
            continue
        cost = 0.0
        if prev_pitch is not None:
            step = abs(pitch - prev_pitch)
            if step == 0:
                cost += 1.1
            elif step <= 2:
                cost += 0.0
            elif step <= 4:
                cost += 0.5
            else:
                cost += 1.2 * (step - 4) + 0.9
        if pitch % 12 not in chord_pcs:
            cost += 1.6
        if accented and pitch % 12 not in chord_pcs:
            cost += 1.0
        cost += 0.05 * abs(pitch - centered)
        if bass_voice:
            if accented:
                cost += 0.0 if pitch % 12 == root_pc else 1.4
            cost += 1.6 if prev_pitch is not None and abs(pitch - prev_pitch) > 7 else 0.0
        cost += piece.rng.uniform(0.0, 0.25)
        options.append((cost, pitch))
    if not options:
        return None
    options.sort()
    return options[0][1]


def between_pitch(low, high):
    """The one in-key pitch strictly between two pitches a third apart, or None."""
    if not 2 < abs(high - low) <= 4:
        return None
    for pitch in range(min(low, high) + 1, max(low, high)):
        if in_key(pitch):
            return pitch
    return None


def fill_voice(piece, voice, first_bar, last_bar, structural_slots, bass_voice=False,
               passing=True):
    """Fill one voice across a bar range: structural notes on the beat grid first.

    structural_slots are the eighth-note slots that carry a chosen (consonant) pitch.
    The slots between them get a passing tone only when the two structural pitches are a
    third apart, which is the textbook weak-beat passing tone; every insertion is
    measured and kept only when the checker still reports no hard finding.
    """
    structural_slots = sorted(structural_slots)
    placed = 0
    for bar in range(first_bar, last_bar + 1):
        numeral = piece.numerals[bar] or "i"
        for slot in structural_slots:
            start = bar * piece.bar_ticks + slot * piece.ticks_per_eighth
            if piece.sounding(voice, start):
                continue
            pitch = pick_pitch(piece, voice, start, piece.ticks_per_eighth, numeral,
                               bass_voice=bass_voice, accented=(slot == 0))
            if pitch is None:
                continue
            piece.notes[voice].append((start, start + piece.ticks_per_eighth, pitch,
                                       108 if bass_voice else 100))
            placed += 1
    inserted = 0
    if passing:
        for bar in range(first_bar, last_bar + 1):
            for slot in range(piece.eighths):
                if slot in structural_slots:
                    continue
                start = bar * piece.bar_ticks + slot * piece.ticks_per_eighth
                if piece.sounding(voice, start):
                    continue
                before = piece.previous_note(voice, start)
                nxt = None
                for note in piece.notes[voice]:
                    if note[0] == start + piece.ticks_per_eighth:
                        nxt = note[2]
                        break
                if before is None or nxt is None:
                    continue
                candidate = between_pitch(before[1], nxt)
                if candidate is None:
                    continue
                piece.notes[voice].append((start, start + piece.ticks_per_eighth, candidate,
                                           92 if bass_voice else 86))
                result, _summary, _events = analyse_notes(piece.notes, piece.time_sig,
                                                          piece.tempo_us)
                if hard_findings(result):
                    piece.notes[voice] = [n for n in piece.notes[voice] if n[0] != start]
                else:
                    inserted += 1
    return placed, inserted



# --------------------------------------------------------------------- repair


def locate(piece, voice, bar, beat):
    tick = (bar - 1) * piece.bar_ticks + int(round((beat - 1) * DIVISION))
    best = None
    for index, note in enumerate(piece.notes[voice]):
        if abs(note[0] - tick) <= piece.ticks_per_eighth // 2:
            best = index
            break
    return best


def repair(piece, movable, rounds=60):
    """Move or rest a FREE note to clear each hard finding, re-measuring each time."""
    log = []
    for _round in range(rounds):
        result, _summary, _events = analyse_notes(piece.notes, piece.time_sig, piece.tempo_us)
        hard = hard_findings(result)
        if not hard:
            break
        finding = hard[0]
        voice = None
        index = None
        for candidate_voice in finding["voices"]:
            if candidate_voice not in movable:
                continue
            candidate_index = locate(piece, candidate_voice, finding["bar"], finding["beat"])
            if candidate_index is None:
                continue
            note_start, _note_end, note_pitch, _velocity = piece.notes[candidate_voice][candidate_index]
            if (note_start, note_pitch) in piece.fixed[candidate_voice]:
                continue
            voice, index = candidate_voice, candidate_index
            break
        if voice is None:
            break
        start, end, pitch, velocity = piece.notes[voice][index]
        best = None
        for candidate in key_pitches(*RANGES[voice]):
            if candidate == pitch:
                continue
            piece.notes[voice][index] = (start, end, candidate, velocity)
            trial, _s, _e = analyse_notes(piece.notes, piece.time_sig, piece.tempo_us)
            count = len(hard_findings(trial))
            if count < len(hard):
                best = (count, candidate)
                break
        if best is None:
            log.append({"voice": voice, "bar": finding["bar"], "beat": finding["beat"],
                        "action": "rest", "rule": finding["rule"]})
            del piece.notes[voice][index]
            continue
        piece.notes[voice][index] = (start, end, best[1], velocity)
        log.append({"voice": voice, "bar": finding["bar"], "beat": finding["beat"],
                    "action": "move", "rule": finding["rule"],
                    "from": pitch_name(pitch), "to": pitch_name(best[1])})
    result, summary, events = analyse_notes(piece.notes, piece.time_sig, piece.tempo_us)
    return log, result, summary, events


def polish(piece, movable, rounds=8):
    """Reduce soft and style findings by moving free notes, never adding a hard one.

    The gate only counts hard findings, so this pass is quality work: a hidden fifth or a
    spacing complaint still sounds amateur, and the mover can usually fix it without
    touching the harmony. Each round walks every finding once; a finding it cannot fix
    without a hard finding is left as it is.
    """
    log = []
    for _round in range(rounds):
        result, _summary, _events = analyse_notes(piece.notes, piece.time_sig, piece.tempo_us)
        hard = len(hard_findings(result))
        soft = [f for f in result["findings"] if f["severity"] != "hard"]
        if not soft:
            break
        touched = 0
        for finding in soft:
            target = None
            for candidate_voice in finding["voices"]:
                if candidate_voice not in movable:
                    continue
                candidate_index = locate(piece, candidate_voice, finding["bar"], finding["beat"])
                if candidate_index is None:
                    continue
                note_start, _e, note_pitch, _v = piece.notes[candidate_voice][candidate_index]
                if (note_start, note_pitch) in piece.fixed[candidate_voice]:
                    continue
                target = (candidate_voice, candidate_index)
                break
            if target is None:
                continue
            voice, index = target
            start, end, pitch, velocity = piece.notes[voice][index]
            best = None
            for candidate in key_pitches(*RANGES[voice]):
                if candidate == pitch:
                    continue
                piece.notes[voice][index] = (start, end, candidate, velocity)
                trial, _s, _e = analyse_notes(piece.notes, piece.time_sig, piece.tempo_us)
                if len(hard_findings(trial)) <= hard and \
                        len(trial["findings"]) < len(result["findings"]):
                    best = candidate
                    break
            if best is None:
                piece.notes[voice][index] = (start, end, pitch, velocity)
                continue
            piece.notes[voice][index] = (start, end, best, velocity)
            touched += 1
            log.append({"voice": voice, "bar": finding["bar"], "beat": finding["beat"],
                        "rule": finding["rule"], "from": pitch_name(pitch),
                        "to": pitch_name(best)})
        if touched == 0:
            break
    result, summary, events = analyse_notes(piece.notes, piece.time_sig, piece.tempo_us)
    return log, result, summary, events


def swap_check(piece, first_bar, last_bar):
    """Measure the same two upper voices with their registers exchanged.

    This is the invertible-counterpoint test: the pair must still be clean when the
    upper line takes the lower register and the lower line takes the upper one.
    """
    low = first_bar * piece.bar_ticks
    high = (last_bar + 1) * piece.bar_ticks
    swapped = {name: list(notes) for name, notes in piece.notes.items()}
    swapped["pulse 1"] = []
    swapped["pulse 2"] = []
    for start, end, pitch, velocity in piece.notes["pulse 1"]:
        if low <= start < high:
            swapped["pulse 2"].append((start, end, pitch - 12, velocity))
        else:
            swapped["pulse 1"].append((start, end, pitch, velocity))
    for start, end, pitch, velocity in piece.notes["pulse 2"]:
        if low <= start < high:
            swapped["pulse 1"].append((start, end, pitch + 12, velocity))
        else:
            swapped["pulse 2"].append((start, end, pitch, velocity))
    result, summary, _events = analyse_notes(swapped, piece.time_sig, piece.tempo_us)
    return {"bars": [first_bar + 1, last_bar + 1],
            "hard": len(hard_findings(result)),
            "rules": rule_counts(result),
            "clash_raw": summary["raw_total"],
            "clash_strong": summary["strong_raw"]}


# ------------------------------------------------------------------- the pieces


def title_piece(seed=1, cell=LEITMOTIF):
    piece = Piece("PP-01 title v10", 3, 126, 32, seed=seed)
    head_1 = head_of(cell, 1)     # F E D C
    head_2 = head_of(cell, -2)    # C B A G
    head_3 = head_of(cell, 2)     # G F E D
    head_4 = head_of(cell, 0)     # E D C B, the head itself

    # Four statements of the leitmotif. Fixed: no repair may move one note of them.
    piece.put_cell("pulse 1", cell, 0, velocity=110)                    # 1-4 subject
    piece.put_cell("pulse 2", cell, 4, semitones=-12, velocity=100)     # 5-8 answer
    piece.put_cell("pulse 1", cell, 12, velocity=110)                   # 13-16 subject
    piece.put_cell("pulse 2", cell, 16, semitones=-12, velocity=100)    # 17-20 answer
    piece.put_cell("pulse 1", cell, 24, velocity=112)                   # 25-28 subject

    # Episodes: the head sequenced, which is how an invention fills the gaps.
    for bar_index, head in ((8, head_1), (10, head_2), (20, head_3), (22, head_4)):
        for _bar, slot, length, pitch in head:
            piece.put("pulse 1", bar_index, slot, length, pitch, fixed=True, velocity=104)
        piece.put("pulse 1", bar_index + 1, 0, 5, close_of(head), fixed=True, velocity=102)
        piece.put("pulse 1", bar_index + 1, 5, 1, natural_below(close_of(head)),
                  fixed=True, velocity=96)

    # Cadence: the head once more, then an authentic close on the tonic.
    cadence = ((28, 0, 3, 72), (28, 3, 1, 71), (28, 4, 1, 68), (28, 5, 1, 69),
               (29, 0, 6, 69),
               (30, 0, 1, 76), (30, 1, 1, 74), (30, 2, 1, 72), (30, 3, 3, 71),
               (31, 0, 6, 69))
    for bar, slot, length, pitch in cadence:
        piece.put("pulse 1", bar, slot, length, pitch, fixed=True, velocity=110)

    hint = ["i", "V", "i", "V",
            "i", "i", "iv", "V",
            "VI", "VI", "i", "i",
            "i", "V", "i", "V",
            "i", "i", "iv", "V",
            "III", "III", "i", "i",
            "i", "V", "i", "V",
            "V", "i", "i", "i"]
    chords = piece.fit_numerals(hint)

    # Countersubjects first, then the continuo under them: the bass is the voice that
    # has to fit everything else, so it is chosen last.
    fill_voice(piece, "pulse 2", 0, 3, [0, 2, 4])
    fill_voice(piece, "pulse 1", 4, 7, [0, 2, 4])
    fill_voice(piece, "pulse 2", 8, 11, [0, 2, 4])
    fill_voice(piece, "pulse 2", 12, 15, [0, 2, 4])
    fill_voice(piece, "pulse 1", 16, 19, [0, 2, 4])
    fill_voice(piece, "pulse 2", 20, 23, [0, 2, 4])
    fill_voice(piece, "pulse 2", 24, 27, [0, 2, 4])
    fill_voice(piece, "pulse 2", 28, 31, [0, 2, 4])
    fill_voice(piece, "triangle", 0, 31, [0, 2, 4], bass_voice=True)
    return piece, chords


FIGHT_SUBJECT = ((0, 0, 1, 76), (0, 1, 1, 74), (0, 2, 1, 72), (0, 3, 1, 71), (0, 4, 4, 71),
                 (1, 0, 1, 76), (1, 1, 1, 72), (1, 2, 1, 74), (1, 3, 1, 76),
                 (1, 4, 2, 71), (1, 6, 1, 68), (1, 7, 1, 69))


def fight_answer():
    """The same line a fifth below, with the one chromatic note lowered (C# to C)."""
    out = []
    for bar, slot, length, pitch in FIGHT_SUBJECT:
        moved = pitch - 7
        if moved % 12 == 1:   # C#, the leading tone of D, lowered for the tonal answer
            moved -= 1
        out.append((bar, slot, length, moved))
    return tuple(out)


def fight_piece(seed=1, cell=LEITMOTIF):
    piece = Piece("PP-04 fight cue, Baroque exposition", 4, 168, 16, seed=seed)
    answer = fight_answer()

    piece.put_cell("pulse 1", FIGHT_SUBJECT, 0, velocity=112)               # 1-2 subject
    piece.put_cell("pulse 2", answer, 2, velocity=104)                      # 3-4 answer
    piece.put_cell("triangle", FIGHT_SUBJECT, 4, semitones=-24, velocity=112)  # 5-6 subject
    piece.put_cell("pulse 1", FIGHT_SUBJECT, 8, velocity=112)               # 9-10 subject
    piece.put_cell("pulse 2", answer, 10, velocity=104)                     # 11-12 answer
    piece.put_cell("triangle", FIGHT_SUBJECT, 12, semitones=-24, velocity=112)  # 13-14

    # Cadence: the head, then a held dominant that falls to the tonic so the loop starts
    # on a downbeat instead of cutting a phrase.
    for bar, slot, length, pitch in ((14, 0, 1, 76), (14, 1, 1, 74), (14, 2, 1, 72),
                                     (14, 3, 1, 71), (14, 4, 4, 71),
                                     (15, 0, 3, 71), (15, 3, 3, 69)):
        piece.put("pulse 1", bar, slot, length, pitch, fixed=True, velocity=110)

    hint = ["i", "i", "i", "i", "i", "i", "V", "V",
            "i", "i", "i", "i", "iv", "iv", "V", "i"]
    chords = piece.fit_numerals(hint)

    # Upper voices first, then the driving continuo under them.
    fill_voice(piece, "pulse 2", 0, 1, [0, 2, 4, 6])
    fill_voice(piece, "pulse 1", 2, 3, [0, 2, 4, 6])
    fill_voice(piece, "pulse 2", 4, 5, [0, 2, 4, 6])
    fill_voice(piece, "pulse 1", 4, 5, [0, 2, 4, 6])
    fill_voice(piece, "pulse 1", 6, 7, [0, 2, 4, 6])
    fill_voice(piece, "pulse 2", 6, 7, [0, 2, 4, 6])
    fill_voice(piece, "pulse 2", 8, 9, [0, 2, 4, 6])
    fill_voice(piece, "pulse 1", 10, 11, [0, 2, 4, 6])
    fill_voice(piece, "pulse 1", 12, 13, [0, 2, 4, 6])
    fill_voice(piece, "pulse 2", 12, 13, [0, 2, 4, 6])
    fill_voice(piece, "pulse 2", 14, 15, [0, 2, 4, 6])
    fill_voice(piece, "triangle", 0, 3, [0, 2, 4, 6], bass_voice=True)
    fill_voice(piece, "triangle", 6, 7, [0, 2, 4, 6], bass_voice=True)
    fill_voice(piece, "triangle", 8, 11, [0, 2, 4, 6], bass_voice=True)
    fill_voice(piece, "triangle", 14, 15, [0, 2, 4, 6], bass_voice=True)
    return piece, chords


# ---------------------------------------------- take B: the other way round
#
# The card asks for two candidates of each cue so the pick is Nayil's ear and not the
# engine's first idea. Take B is not a reseed of take A: the roles are swapped, the
# tempo and the harmony plan are different, and the continuo moves in a different
# rhythm, so the two takes can be judged against each other. Every note of the
# leitmotif is still the leitmotif, fixed, and measured.


def title_piece_b(seed=1, cell=LEITMOTIF):
    """Title take B: a fugato in which the LOWER voice states the subject first.

    A minor, 3/4, 126 bpm, 32 bars. Pulse 2 states the subject an octave below, pulse 1
    answers above it, the triangle enters with the head as a third voice, and the
    continuo walks every eighth instead of three beats per bar. The middlegame is a
    circle of fifths (i VII III VI ii V i), which is the sequence the plan asks for and
    the first take does not use.

    126 bpm is not a choice this take makes: data/title_timing.json is the source of
    truth for the title's timing and the game's title animation reads it, so a candidate
    that changed the tempo would move the car bob and the lane dashes with it.
    """
    piece = Piece("PP-01 title v11 (fugato, the lower voice leads)", 3, 126, 32, seed=seed)
    head_1 = head_of(cell, 1)     # F E D C
    head_2 = head_of(cell, -2)    # C B A G

    # Entries: the subject in the alto first, then the answer above it, twice; then the
    # head in the triangle, which is the third entry a fugato wants.
    piece.put_cell("pulse 2", cell, 0, semitones=-12, velocity=104)     # 1-4 subject
    piece.put_cell("pulse 1", cell, 4, velocity=112)                    # 5-8 answer
    piece.put_cell("pulse 2", cell, 12, semitones=-12, velocity=104)    # 13-16 subject
    piece.put_cell("pulse 1", cell, 16, velocity=112)                   # 17-20 answer
    piece.put_cell("triangle", head_of(cell, 0), 20, semitones=-24, velocity=104)  # 21
    piece.put_cell("pulse 1", cell, 24, velocity=114)                   # 25-28 subject

    # Episodes: the head sequenced in the soprano, as in the first take, but only two
    # pairs, because the third entry and the cadence take the other four bars.
    for bar_index, head in ((8, head_1), (10, head_2)):
        for _bar, slot, length, pitch in head:
            piece.put("pulse 1", bar_index, slot, length, pitch, fixed=True, velocity=104)
        piece.put("pulse 1", bar_index + 1, 0, 5, close_of(head), fixed=True, velocity=102)
        piece.put("pulse 1", bar_index + 1, 5, 1, natural_below(close_of(head)),
                  fixed=True, velocity=96)

    # Cadence: the head once more, then an authentic close on the tonic.
    cadence = ((28, 0, 3, 72), (28, 3, 1, 71), (28, 4, 1, 68), (28, 5, 1, 69),
               (29, 0, 6, 69),
               (30, 0, 1, 76), (30, 1, 1, 74), (30, 2, 1, 72), (30, 3, 3, 71),
               (31, 0, 6, 69))
    for bar, slot, length, pitch in cadence:
        piece.put("pulse 1", bar, slot, length, pitch, fixed=True, velocity=110)

    # i V i V | i i iv V | i VII III VI | ii V i i | i iv VII III | VI ii V i |
    # i i i i | V i V i. The circle of fifths sits in bars 13 to 24.
    hint = ["i", "V", "i", "V",
            "i", "i", "iv", "V",
            "i", "VII", "III", "VI",
            "ii", "V", "i", "i",
            "i", "iv", "VII", "III",
            "VI", "ii", "V", "i",
            "i", "i", "i", "i",
            "V", "i", "V", "i"]
    chords = piece.fit_numerals(hint)

    # Countersubjects around each entry, then the walking continuo under everything.
    fill_voice(piece, "pulse 1", 0, 3, [0, 2, 4])
    fill_voice(piece, "pulse 2", 4, 7, [0, 2, 4])
    fill_voice(piece, "pulse 1", 8, 11, [0, 2, 4])
    fill_voice(piece, "pulse 1", 12, 15, [0, 2, 4])
    fill_voice(piece, "pulse 2", 16, 19, [0, 2, 4])
    fill_voice(piece, "pulse 1", 20, 23, [0, 2, 4])
    fill_voice(piece, "pulse 2", 20, 23, [0, 2, 4])
    fill_voice(piece, "pulse 2", 24, 27, [0, 2, 4])
    fill_voice(piece, "pulse 2", 28, 31, [0, 2, 4])
    fill_voice(piece, "pulse 1", 28, 31, [0, 2, 4])
    fill_voice(piece, "triangle", 0, 31, [0, 1, 2, 3, 4, 5], bass_voice=True,
               passing=False)
    return piece, chords


def fight_piece_b(seed=1, cell=LEITMOTIF):
    """Fight take B: the exposition starts in the bass, and the drive is a backbeat.

    A minor, 4/4, 168 bpm, 16 bars, the tempo gamedev ruling D3 keeps for this cue so a
    state cut lands on a bar line. The triangle states the subject two octaves down,
    pulse 1 takes the answer above it, pulse 2 takes the answer in the middle; the
    return statements answer at the fifth; the episode in bars 7 and 8 walks a circle of
    fifths in the bass; the cadence leans on a cadential six-four in the triangle before
    the tonic. Hats on every eighth and a backbeat snare, where take A had off-beat hats
    and a beat-2 snare.
    """
    piece = Piece("PP-04 fight cue, Baroque exposition, the bass enters first", 4, 168,
                  16, seed=seed)
    answer = fight_answer()

    piece.put_cell("triangle", FIGHT_SUBJECT, 0, semitones=-24, velocity=116)  # 1-2 bass
    piece.put_cell("pulse 1", FIGHT_SUBJECT, 2, velocity=112)                  # 3-4
    piece.put_cell("pulse 2", FIGHT_SUBJECT, 4, semitones=-12, velocity=104)   # 5-6
    piece.put_cell("triangle", FIGHT_SUBJECT, 8, semitones=-24, velocity=116)  # 9-10
    piece.put_cell("pulse 1", answer, 10, semitones=12, velocity=110)          # 11-12
    piece.put_cell("pulse 2", answer, 12, velocity=104)                        # 13-14

    # Cadence: the head in the soprano over a cadential six-four in the bass, falling to
    # the tonic so the loop starts on a downbeat.
    for bar, slot, length, pitch in ((14, 0, 1, 76), (14, 1, 1, 74), (14, 2, 1, 72),
                                     (14, 3, 1, 71), (14, 4, 4, 71),
                                     (15, 0, 3, 71), (15, 3, 3, 69)):
        piece.put("pulse 1", bar, slot, length, pitch, fixed=True, velocity=112)
    piece.put("triangle", 14, 0, 4, 40, fixed=True, velocity=110)   # E, the six-four
    piece.put("triangle", 15, 0, 8, 45, fixed=True, velocity=112)   # A, the resolution

    # i i | i i | i iv | VII III | VI ii | V i | i i | V i
    hint = ["i", "i", "i", "i",
            "i", "i", "iv", "VII",
            "III", "VI", "ii", "V",
            "i", "i", "V", "i"]
    chords = piece.fit_numerals(hint)

    fill_voice(piece, "pulse 1", 0, 1, [0, 2, 4, 6])
    fill_voice(piece, "pulse 2", 0, 1, [0, 2, 4, 6])
    fill_voice(piece, "pulse 2", 2, 3, [0, 2, 4, 6])
    fill_voice(piece, "pulse 1", 4, 5, [0, 2, 4, 6])
    fill_voice(piece, "pulse 1", 6, 7, [0, 2, 4, 6])
    fill_voice(piece, "pulse 2", 6, 7, [0, 2, 4, 6])
    fill_voice(piece, "pulse 1", 8, 9, [0, 2, 4, 6])
    fill_voice(piece, "pulse 2", 8, 9, [0, 2, 4, 6])
    fill_voice(piece, "pulse 2", 10, 11, [0, 2, 4, 6])
    fill_voice(piece, "pulse 1", 12, 13, [0, 2, 4, 6])
    fill_voice(piece, "pulse 2", 14, 15, [0, 2, 4, 6])
    fill_voice(piece, "triangle", 0, 15, [0, 2, 4, 6], bass_voice=True)
    return piece, chords


# --------------------------------------------------------------------- drums


def drums_fight(piece):
    """Noise hats on the off-beat eighth and a dpcm kick/snare: the drive, not a melody."""
    hits = {"noise": [], "dpcm": []}
    for bar in range(piece.bars):
        start = bar * piece.bar_ticks
        for slot in range(1, piece.eighths, 2):
            tick = start + slot * piece.ticks_per_eighth
            hits["noise"].append((tick, tick + 60, 42, 72))
        for beat, pitch, velocity in ((0, 36, 118), (2, 38, 104), (3, 36, 100)):
            tick = start + beat * DIVISION
            hits["dpcm"].append((tick, tick + DIVISION // 2, pitch, velocity))
    return hits


def drums_fight_drive(piece):
    """Take B's drive: hats on every eighth and a backbeat, where take A had off-beats.

    A closed hat on every eighth pushes harder than one on the off-beats only, and the
    snare on 2 and 4 instead of every second beat is the backbeat a fight cue wants.
    """
    hits = {"noise": [], "dpcm": []}
    for bar in range(piece.bars):
        start = bar * piece.bar_ticks
        for slot in range(piece.eighths):
            tick = start + slot * piece.ticks_per_eighth
            velocity = 66 if slot % 2 == 0 else 78
            hits["noise"].append((tick, tick + 55, 42, velocity))
        for beat, pitch, velocity in ((0, 36, 118), (1, 38, 108), (2, 36, 104),
                                      (3, 38, 108)):
            tick = start + beat * DIVISION
            hits["dpcm"].append((tick, tick + DIVISION // 2, pitch, velocity))
    return hits


# --------------------------------------------------------------- MIDI and report


def write_midi(notes, path, time_sig, bpm, cc_by_voice=None):
    import humanize

    tracks = []
    for name in ("pulse 1", "pulse 2", "triangle", "noise", "dpcm"):
        if name not in notes or not notes[name]:
            continue
        tracks.append({"name": name,
                       "notes": [tuple(n) for n in sorted(notes[name])],
                       "cc": (cc_by_voice or {}).get(name, {})})
    payload = {"division": DIVISION,
               "tempo_us": int(round(60_000_000.0 / bpm)),
               "time_sig": time_sig,
               "tracks": tracks}
    humanize.write_smf(payload, path)
    return path


def motif_check(notes, voice, bar_ticks, semitones=0, cell=LEITMOTIF, bar_offset=0):
    """Every leitmotif note present, on its own tick, at its own pitch.

    bar_offset is where the statement starts: the first take states the leitmotif at
    bar 1, the second take lets the lower voice state it first and the soprano answer
    at bar 5, so the check has to be told which bar it is measuring.
    """
    eighth = DIVISION // 2
    starts = {(note[0], note[2]) for note in notes[voice]}
    missing = []
    for bar, slot, _length, pitch in cell:
        tick = (bar + bar_offset) * bar_ticks + slot * eighth
        if (tick, pitch + semitones) not in starts:
            missing.append((bar + 1, slot, pitch_name(pitch + semitones)))
    return {"voice": voice, "present": len(cell) - len(missing), "of": len(cell),
            "missing": missing}


def motif_sequence_check(notes, voice, cell, semitones=0):
    """The motif's pitch sequence appears in this voice, in order, consecutively.

    Used where the statement is rhythmically compressed (the fight cue), so the tick
    positions differ from the waltz but the line must still be the same notes.
    """
    wanted = [pitch + semitones for _bar, _slot, _length, pitch in cell]
    line = [note[2] for note in sorted(notes[voice])]
    hits = 0
    for start in range(0, max(0, len(line) - len(wanted) + 1)):
        window = line[start:start + len(wanted)]
        if window == wanted:
            hits += 1
    return {"voice": voice, "present": hits > 0, "statements": hits,
            "line": [pitch_name(p) for p in wanted]}


def build(kind, seed=1, variant=1):
    """Compose one cue and measure it. variant 1 is the first take, 2 is take B."""
    cell, provenance = leitmotif_from_v7()
    if kind == "title":
        if variant == 2:
            piece, chords = title_piece_b(seed=seed, cell=cell)
            swap = swap_check(piece, 4, 7)
        else:
            piece, chords = title_piece(seed=seed, cell=cell)
            swap = swap_check(piece, 0, 3)
    else:
        if variant == 2:
            piece, chords = fight_piece_b(seed=seed, cell=cell)
        else:
            piece, chords = fight_piece(seed=seed, cell=cell)
        swap = None
    movable = ("pulse 2", "pulse 1", "triangle")
    log, result, summary, _events = repair(piece, movable)
    polish_log, result, summary, _events = polish(piece, movable)
    notes = piece.notes
    motif = None
    motif_b = None
    if kind == "title":
        if variant == 2:
            # The lower voice states the subject first; the soprano answer starts at bar 5.
            motif = motif_check(notes, "pulse 2", piece.bar_ticks, semitones=-12)
            motif_b = motif_check(notes, "pulse 1", piece.bar_ticks, bar_offset=4)
        else:
            motif = motif_check(notes, "pulse 1", piece.bar_ticks)
    else:
        motif = motif_sequence_check(notes, "pulse 1", FIGHT_SUBJECT)
    report = {
        "piece": piece.name,
        "seed": seed,
        "variant": variant,
        "key": KEY_NAME,
        "tempo_bpm": piece.bpm,
        "time_sig": "%d/4" % piece.beats,
        "bars": piece.bars,
        "leitmotif": provenance,
        "numerals": piece.numerals,
        "chord_fit": chords,
        "notes_per_voice": {voice: len(note_list) for voice, note_list in notes.items()},
        "notes": sum(len(note_list) for note_list in notes.values()),
        "hard": len(hard_findings(result)),
        "by_severity": result["summary"]["by_severity"],
        "rules": rule_counts(result),
        "rates_per_100_notes": result["summary"]["rates_per_100_notes"],
        "repairs": log,
        "polish": polish_log,
        "clash": {key: summary[key] for key in ("by_class", "raw_total", "strong_raw",
                                                "dissonances")},
        "motif_pulse1": motif,
        "swap_check": swap,
        "devices": result["devices"],
        "voices": result["voices"],
    }
    if kind == "title" and variant == 2:
        report["motif_pulse1_answer"] = motif_b
        report["motif_triangle"] = motif_check(notes, "triangle", piece.bar_ticks,
                                               semitones=-24, cell=head_of(cell, 0),
                                               bar_offset=20)
    if kind == "fight":
        report["motif_answer"] = motif_sequence_check(notes, "pulse 2", fight_answer())
        report["motif_bass"] = motif_sequence_check(notes, "triangle", FIGHT_SUBJECT,
                                                    semitones=-24)
    return piece, report


def main(argv=None):
    parser = argparse.ArgumentParser(description="M3 Baroque cues (card t_65512e1c).")
    parser.add_argument("--piece", choices=("title", "fight"), default=None)
    parser.add_argument("--both", action="store_true")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--variant", type=int, choices=(1, 2), default=1,
                        help="1 is the first take, 2 is take B (the other way round)")
    parser.add_argument("--midi", default=None)
    parser.add_argument("--report", default=None)
    parser.add_argument("--out-dir", default=os.path.join(ROOT, "out", "m3"))
    args = parser.parse_args(argv)
    if not args.piece and not args.both:
        parser.error("pass --piece title|fight or --both")

    kinds = ("title", "fight") if args.both else (args.piece,)
    status = 0
    os.makedirs(args.out_dir, exist_ok=True)
    for kind in kinds:
        piece, report = build(kind, args.seed, args.variant)
        notes = piece.notes
        if kind == "fight":
            notes = dict(notes)
            notes.update(drums_fight_drive(piece) if args.variant == 2
                         else drums_fight(piece))
        midi = args.midi if (args.midi and len(kinds) == 1) else os.path.join(
            args.out_dir, "%s_v10.mid" % kind)
        cc = {"pulse 1": {12: [(0, 2)], 11: [(0, 104)]},   # 50 percent duty, lead level
              "pulse 2": {12: [(0, 1)], 11: [(0, 88)]}}    # 25 percent duty, quieter
        write_midi(notes, midi, piece.time_sig, piece.bpm, cc)
        report["midi"] = os.path.abspath(midi)
        json_path = args.report if (args.report and len(kinds) == 1) else os.path.join(
            args.out_dir, "%s_v10.json" % kind)
        with open(json_path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, indent=1, sort_keys=True)
            handle.write("\n")
        print("%-6s hard %d  soft %d  style %d  clashes %d (downbeat %d)  notes %d"
              % (kind, report["hard"], report["by_severity"].get("soft", 0),
                 report["by_severity"].get("style", 0), report["clash"]["raw_total"],
                 report["clash"]["strong_raw"], report["notes"]))
        print("       motif %s  repairs %d  swap %s  midi %s"
              % (json.dumps({k: v for k, v in report["motif_pulse1"].items()
                             if k != "missing"}),
                 len(report["repairs"]),
                 report["swap_check"]["hard"] if report["swap_check"] else "n/a", midi))
        if report["hard"]:
            status = 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
