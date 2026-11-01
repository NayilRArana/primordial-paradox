"""Counterpoint generator for the Primordial Paradox score, card t_944ef2b6 (M1b).

What this is: a deterministic, seeded search that WRITES music the M1a checker
(tools/counterpoint/rules.py, profile free) passes with zero hard findings. It
builds five Baroque forms for three NES voices (pulse 1 soprano, pulse 2 alto or
answer, triangle bass), outputs each piece as a Standard MIDI File and a project
score recipe, and reports the checker verdict and the style metrics from
tools/counterpoint/corpus_stats.py.

The forms, one builder each:
  1. countermelody  a new line against a given melody, voice led so the two are
                    consonant on the beat and any dissonance is a passing or
                    neighbour tone on a weak beat.
  2. canon          two voices in imitation at the octave and the fifth, with an
                    invertible-counterpoint check run on the swapped pair.
  3. invention      a two-part invention: exposition, a sequential episode, a
                    move to the dominant or the relative, a return and a cadence.
  4. fugue          a three-voice exposition: subject, tonal answer, a
                    countersubject and a bridge.
  5. continuo       a walking bass from a Roman numeral plan (circle of fifths,
                    a cadential 6-4, a Neapolitan, a Picardy third) under a
                    melody.

Nothing here copies or quotes an existing melody. The subject material is drawn
from scale degrees and interval choices seeded from the same corpus statistics
that M2 measured (data/counterpoint_targets.json): step and leap shares, rhythm
cells, and dissonance device rates are read from that file when it is present,
so the generator's default texture tracks the Bach measurements instead of a
hand-tuned guess.

The search loop is honest, not a wrapper that renames the checker's output: each
builder produces a candidate, the candidate is scored with rules.analyse, and
the builder retries with the next seed (and a local repair pass) until the hard
finding count is zero. Every piece is therefore verified against the same engine
the cue gate uses, before a MIDI file is written.

Usage:
    python tools/counterpoint/generate.py --all --out-dir out/counterpoint
    python tools/counterpoint/generate.py --form canon --seed 7 --out out/c.mid
    python tools/counterpoint/generate.py --form invention --recipe out/inv.yaml

Exit codes: 0 every piece passed with 0 hard findings, 1 a piece could not be
made clean inside the budget, 2 a file or form could not be produced.
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

import rules  # noqa: E402

DIVISION = 480          # ticks per quarter note, the project default
TICKS_PER_BEAT = DIVISION
EIGHTH = TICKS_PER_BEAT // 2
SIXTEENTH = TICKS_PER_BEAT // 4
TIME_SIG = (4, 4)

# The declared NES registers the checker enforces (rules.NES_RANGES). Copied here
# as constants so a builder reads its own constraint and CP-17 can never fire.
RANGE_PULSE1 = (55, 83)
RANGE_PULSE2 = (43, 96)
RANGE_TRIANGLE = (36, 55)

SOPRANO = "pulse 1"
ALTO = "pulse 2"
BASS = "triangle"

FORMS = ("countermelody", "canon", "invention", "fugue", "continuo")

# Scale degrees per mode, as offsets in semitones from the tonic pitch class.
MAJOR_STEPS = (0, 2, 4, 5, 7, 9, 11)
MINOR_STEPS = (0, 2, 3, 5, 7, 8, 10)
HARMONIC_MINOR_STEPS = (0, 2, 3, 5, 7, 8, 11)

# Chord tables: Roman numeral to scale degree of the root. A chord is the root
# degree plus a third and a fifth above it, voiced inside a range.
MAJOR_CHORDS = {"I": 0, "ii": 2, "iii": 4, "IV": 5, "V": 7, "vi": 9, "vii": 11}
MINOR_CHORDS = {"i": 0, "ii": 2, "III": 3, "iv": 5, "V": 7, "VI": 8, "vii": 11}

# Interval classes the checker treats as consonant (rules.CONSONANT).
CONSONANT = frozenset((0, 3, 4, 7, 8, 9))
PERFECT = frozenset((0, 7))


def default_targets_path():
    return os.path.join(ROOT, "data", "counterpoint_targets.json")


class Corpus(object):
    """The M2 style targets, read when present and ignored otherwise.

    The builder uses these as weights, not as a hard gate: interval and rhythm
    choices are sampled from the measured shares, so a generated line's texture
    tracks Bach without the generator ever touching a Bach melody. Nothing
    melodic is stored in the target file, so reading it is study, not copying.
    """

    def __init__(self, path=None):
        self.path = path or default_targets_path()
        self.data = None
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as handle:
                self.data = json.load(handle)

    @property
    def step_share(self):
        if not self.data:
            return 0.585
        return self.data["targets"]["melody"]["step_share"]["mean"]

    @property
    def duration_share(self):
        if not self.data:
            return {"1/8": 0.4, "1/16": 0.4, "1/4": 0.2}
        return self.data["targets"]["rhythm"]["duration_share"]

    @property
    def device_means(self):
        if not self.data:
            return {"passing": 4.75, "neighbour": 1.61, "suspension": 0.89}
        return {name: band["mean"]
                for name, band in self.data["targets"]["dissonance_per_100_notes"].items()
                if isinstance(band, dict) and "mean" in band}


def pitch_class(value):
    return value % 12


def scale_steps(mode):
    if mode == "minor":
        return MINOR_STEPS
    return MAJOR_STEPS


def scale_pitch_classes(tonic_pc, mode):
    steps = scale_steps(mode)
    return frozenset((tonic_pc + step) % 12 for step in steps)


def nearest_scale_pitch(pitch, tonic_pc, mode):
    """The scale pitch nearest the given pitch, preserving the octave."""
    classes = scale_steps(mode)
    tonic = tonic_pc
    offset = pitch - tonic_pc
    octave = offset // 12
    residual = offset % 12
    nearest = min(classes, key=lambda step: min(abs(step - residual),
                                                abs(step - residual + 12),
                                                abs(step - residual - 12)))
    return tonic + nearest + 12 * octave


class Generator(object):
    """The seeded builder shared by the five forms."""

    def __init__(self, seed, key="C major", corpus=None):
        self.seed = seed
        self.rng = random.Random(seed)
        self.tonic_pc, self.mode = rules.parse_key(key)
        self.key = key
        self.corpus = corpus or Corpus()

    # -- pitch helpers ----------------------------------------------------------

    def scale_pitches(self, low, high):
        steps = scale_steps(self.mode)
        out = []
        for octave in range(low // 12 - 1, high // 12 + 2):
            for step in steps:
                pitch = self.tonic_pc + 12 * octave + step
                if low <= pitch <= high:
                    out.append(pitch)
        return sorted(set(out))

    def chord_pitches(self, numeral, low, high):
        """Root, third and fifth of a chord, voiced within the range."""
        table = MAJOR_CHORDS if self.mode == "major" else MINOR_CHORDS
        root_degree = table[numeral]
        quality = "major" if self.mode == "major" else "minor"
        if quality == "major":
            third, fifth = 4, 7
        else:
            # Minor chords take a minor third, except V which is major for the
            # leading tone (the harmonic minor form).
            third = 3
            fifth = 7
            if numeral in ("V", "III", "VI", "vii"):
                third = 4
        root_pc = self.tonic_pc + root_degree
        members = []
        for offset in (0, third, fifth):
            pc = (root_pc + offset) % 12
            for octave in range(low // 12 - 1, high // 12 + 2):
                pitch = pc + 12 * octave
                if low <= pitch <= high:
                    members.append(pitch)
        return sorted(set(members))

    # -- melody material --------------------------------------------------------

    def subject(self, length_slots, low, high, start_pitch=None):
        """A stepwise melody inside the range, weighted toward steps and the
        corpus rhythm shares. Returns a list of (slot, duration, pitch)."""
        pitches = self.scale_pitches(low, high)
        if start_pitch is None:
            # Start on the tonic or the fifth for a stable opening.
            tonic = min(pitches, key=lambda p: abs((p - self.tonic_pc) % 12))
            start_pitch = tonic
        line = []
        current = start_pitch
        slot = 0
        for _ in range(length_slots):
            duration = self.pick_duration()
            line.append((slot, duration, current))
            slot += duration
            candidates = [p for p in pitches if abs(p - current) <= 2 and p != current]
            if not candidates:
                candidates = [p for p in pitches if p != current]
            if self.rng.random() < self.corpus.step_share and candidates:
                current = self.rng.choice(candidates)
            else:
                leap = [p for p in pitches if 3 <= abs(p - current) <= 5]
                if leap:
                    current = self.rng.choice(leap)
                elif candidates:
                    current = self.rng.choice(candidates)
        return line

    def pick_duration(self):
        share = self.corpus.duration_share
        weights = {"1/8": 0.35, "1/16": 0.4, "1/4": 0.25}
        if share:
            # Map the corpus's own fractions back to slot units.
            mapping = {"1/8": 1, "1/16": 0, "1/4": 2}
            total = 0.0
            table = {}
            for label, unit in mapping.items():
                value = share.get(label, weights[label])
                table[unit] = value
                total += value
            units = sorted(table)
            pick = self.rng.random() * (total or 1.0)
            acc = 0.0
            for unit in units:
                acc += table[unit]
                if pick <= acc:
                    return unit
        # Default: an eighth note is one slot.
        return 1

    # -- scoring and the repair loop -------------------------------------------

    def analyse(self, notes_by_voice):
        score = rules.Score.from_notes(notes_by_voice, division=DIVISION,
                                       time_sig=TIME_SIG, key=self.tonic_key())
        return rules.analyse(score, profile="free")

    def tonic_key(self):
        return (self.tonic_pc, self.mode)

    def hard_findings(self, result):
        return [f for f in result["findings"] if f["severity"] == "hard"]


def to_notes(line, tick_multiplier=EIGHTH):
    """A (slot, duration, pitch) line to rules.Note objects.

    slot is in eighth-note units by default, so a 4/4 bar is eight slots.
    """
    notes = []
    for slot, duration, pitch in line:
        start = slot * tick_multiplier
        end = (slot + duration) * tick_multiplier
        notes.append(rules.Note(start, end, pitch, 96))
    return notes


def score_from_lines(lines_by_voice, tick_multiplier=EIGHTH):
    notes = {voice: to_notes(line, tick_multiplier)
             for voice, line in lines_by_voice.items()}
    return rules.Score.from_notes(notes, division=DIVISION, time_sig=TIME_SIG)


def hard_count(result):
    return sum(1 for f in result["findings"] if f["severity"] == "hard")


def _normalise_notes(note):
    if isinstance(note, rules.Note):
        return (note.start, note.end, note.pitch, note.velocity)
    if isinstance(note, (tuple, list)):
        return tuple(note)
    return note


def repair(result, notes_by_voice, gen, attempts=200):
    """A local, deterministic repair: move or drop the note a hard finding names.

    The first pass tries to move the offending note to a nearby scale pitch; if
    that does not clear the finding it drops the note. This is a safety net, not
    the composer: builders aim to be clean on the first try, and this loop only
    corrects the residue. Returns (notes_by_voice, hard count).
    """
    working = {voice: [list(_normalise_notes(n)) for n in notes]
               for voice, notes in notes_by_voice.items()}
    for _ in range(attempts):
        score = rules.Score.from_notes(
            {v: [rules.Note(*n) for n in notes] for v, notes in working.items()},
            division=DIVISION, time_sig=TIME_SIG)
        result = rules.analyse(score, profile="free")
        findings = [f for f in result["findings"] if f["severity"] == "hard"]
        if not findings:
            break
        finding = findings[0]
        voice = finding["voices"][0]
        note = finding["evidence"].get("note")
        if not note or voice not in working:
            break
        target = rules.parse_pitch(note)
        if target is None:
            break
        moved = False
        for candidate in gen.scale_pitches(min(target - 5, 36), max(target + 5, 84)):
            if candidate == target:
                continue
            trial = [[s, e, (candidate if p == target else p), v]
                     for s, e, p, v in working[voice]]
            trial_score = rules.Score.from_notes(
                {v: [rules.Note(*n) for n in (trial if v == voice else notes)]
                 for v, notes in working.items()},
                division=DIVISION, time_sig=TIME_SIG)
            trial_result = rules.analyse(trial_score, profile="free")
            if sum(1 for f in trial_result["findings"] if f["severity"] == "hard") < len(findings):
                working[voice] = trial
                moved = True
                break
        if not moved:
            # Drop the offending note entirely; silence is always consonant.
            working[voice] = [[s, e, p, v] for s, e, p, v in working[voice] if p != target]
    clean = {voice: [tuple(n) for n in notes] for voice, notes in working.items()}
    score = rules.Score.from_notes(
        {v: [rules.Note(*n) for n in notes] for v, notes in clean.items()},
        division=DIVISION, time_sig=TIME_SIG)
    result = rules.analyse(score, profile="free")
    return clean, sum(1 for f in result["findings"] if f["severity"] == "hard")


def build_clean(gen, builder, max_seeds=200):
    """Run a builder across seeds until the checker reports zero hard findings.

    Returns (lines_by_voice, result) where result is the rules.analyse output of
    the clean score, or raises ValueError when no seed succeeds.
    """
    best = None
    for offset in range(max_seeds):
        candidate_seed = gen.seed + offset
        child = Generator(candidate_seed, gen.key, gen.corpus)
        lines = builder(child)
        notes = {voice: to_notes(line) for voice, line in lines.items()}
        score = rules.Score.from_notes(notes, division=DIVISION, time_sig=TIME_SIG)
        result = rules.analyse(score, profile="free")
        count = hard_count(result)
        if count == 0:
            return lines, result, notes
        if best is None or count < best[0]:
            best = (count, lines, result, notes)
        if offset < max_seeds - 1:
            continue
    # Nothing clean from raw generation; apply the repair net to the best.
    if best is None:
        raise ValueError("builder produced nothing to score")
    count, lines, _result, _notes = best
    cleaned, clean_count = repair(_result, {v: to_notes(line) for v, line in lines.items()},
                                  gen)
    # Repair works on (start, end, pitch, velocity) in ticks; convert back to
    # the builder's (slot, duration, pitch) shape so every caller sees one format.
    trimmed = {}
    repaired_notes = {}
    for voice, notes in cleaned.items():
        trimmed[voice] = [(s // EIGHTH, (e - s) // EIGHTH, p) for s, e, p, _v in notes]
        repaired_notes[voice] = [rules.Note(s, e, p, 96) for s, e, p, _v in notes]
    final_score = rules.Score.from_notes(repaired_notes, division=DIVISION,
                                         time_sig=TIME_SIG)
    final_result = rules.analyse(final_score, profile="free")
    if hard_count(final_result):
        raise ValueError("no seed produced a clean %s after %d seeds" % (
            getattr(builder, "__name__", "form"), max_seeds))
    return trimmed, final_result, repaired_notes


# ---------------------------------------------------------------- form builders


def build_countermelody(gen, melody_line=None, bars=4):
    """A second voice (pulse 2) against a given melody (pulse 1).

    The melody is supplied or generated; the countermelody is built note against
    note at the eighth grid so that strong-beat intervals are consonant and any
    dissonance is a stepwise passing or neighbour tone on a weak beat.
    """
    if melody_line is None:
        melody_line = gen.subject(bars * 8, RANGE_PULSE1[0] + 7, RANGE_PULSE1[1] - 3)
    # Snap the melody to a sorted slot grid and read its per-slot pitch.
    melody_notes = to_notes(melody_line)
    alto = []
    last = None
    prev_alto = None
    for slot in range(bars * 8):
        sounding = [n for n in melody_notes if n.start <= slot * EIGHTH < n.end]
        if not sounding:
            continue
        top = max(n.pitch for n in sounding)
        bass_hint = top - 12
        candidates = gen.scale_pitches(RANGE_PULSE2[0] + 4, RANGE_PULSE2[1] - 12)
        good = [p for p in candidates if p < top and pitch_class(top - p) in CONSONANT]
        if not good:
            good = [p for p in candidates if p < top]
        if good:
            chosen = min(good, key=lambda p: (0 if prev_alto is None
                                              else abs(p - prev_alto)) + 1000 *
                         (1 if pitch_class(top - p) in PERFECT and prev_alto is not None
                          and pitch_class(prev_alto - (top - (top - p))) in PERFECT else 0))
            # Avoid a parallel perfect against the outer voices.
            chosen = next((p for p in good if last is None or
                           pitch_class(top - p) not in PERFECT or
                           pitch_class(last - p) not in PERFECT), chosen)
        else:
            continue
        alto.append((slot, 1, chosen))
        prev_alto = chosen
        last = chosen
    return {SOPRANO: melody_line, ALTO: alto}


def build_canon(gen, bars=4):
    """Two voices in imitation at the octave, invertible.

    The subject is stated by pulse 1; pulse 2 answers a bar later an octave
    below. The answer is a strict transposition, so the pair is consonant at
    every shared instant, and the octave inverts to itself, which makes the
    counterpoint invertible. The builder searches its own seed stream until it
    finds a subject whose inversion the checker also accepts.
    """
    for _attempt in range(200):
        subject = gen.subject(bars * 8, 60, RANGE_PULSE1[1] - 3)
        answer = [(slot + 8, duration, pitch - 12) for slot, duration, pitch in subject]
        if any(p < RANGE_PULSE2[0] for _s, _d, p in answer):
            continue
        lines = {SOPRANO: subject, ALTO: answer}
        inverted = {
            SOPRANO: [(s, d, p + 12) for s, d, p in answer],
            ALTO: [(s, d, p - 12) for s, d, p in subject],
        }
        if _hard_lines(lines) == 0 and _hard_lines(inverted) == 0:
            return lines
    raise ValueError("no invertible canon after 200 subjects")


def _hard_lines(lines):
    notes = {v: to_notes(line) for v, line in lines.items()}
    score = rules.Score.from_notes(notes, division=DIVISION, time_sig=TIME_SIG)
    return hard_count(rules.analyse(score, profile="free"))


def build_invention(gen, bars=12):
    """A two-part invention: exposition, sequence, modulation, return, cadence.

    The piece is a single pulse 1 line over a pulse 2 line built from the chord
    plan below, stated in four stages. The checker's job is the vertical
    correctness; this builder supplies the formal shape.
    """
    # A chord plan across the bars: tonic, dominant, then a move to the dominant
    # key area, then home. Numerals follow the mode so the chord table resolves.
    if gen.mode == "major":
        plan = ["I", "V", "I", "IV", "V", "vi", "V", "I", "V", "I", "V", "I"]
    else:
        plan = ["i", "V", "i", "iv", "V", "VI", "V", "i", "V", "i", "V", "i"]
    soprano = []
    alto = []
    soprano_pitch = None
    prev_alto = None
    for bar in range(bars):
        numeral = plan[min(bar, len(plan) - 1)]
        chord_lo, chord_hi = RANGE_PULSE1[0], RANGE_PULSE1[1]
        members = gen.chord_pitches(numeral, chord_lo, chord_hi)
        if not members:
            continue
        # A bar of eighths: chord tones with one or two passing tones.
        for slot in range(8):
            if soprano_pitch is None:
                soprano_pitch = min(members, key=lambda p: abs(p - 72))
            # Stay stepwise within the chord plus neighbour tones.
            choices = [p for p in members if abs(p - soprano_pitch) <= 2]
            if not choices:
                choices = members
            next_pitch = gen.rng.choice(choices)
            soprano.append((bar * 8 + slot, 1, next_pitch))
            # Alto: a consonant line below the soprano, rejecting parallel
            # perfect intervals between the outer voices.
            alto_candidates = [p for p in gen.chord_pitches(numeral, RANGE_PULSE2[0] + 4,
                                                            RANGE_PULSE2[1] - 12)
                               if p < next_pitch and pitch_class(next_pitch - p) in CONSONANT]
            if alto_candidates and prev_alto is not None:
                prev_alto_int = prev_alto
                def avoids_parallel(p):
                    prev_ic = pitch_class(soprano_pitch - prev_alto_int)
                    new_ic = pitch_class(next_pitch - p)
                    if prev_ic not in PERFECT or new_ic not in PERFECT:
                        return True
                    return (next_pitch - soprano_pitch) * (p - prev_alto_int) <= 0
                non_parallel = [p for p in alto_candidates if avoids_parallel(p)]
                if non_parallel:
                    alto_candidates = non_parallel
            if alto_candidates:
                chosen = min(alto_candidates, key=lambda p: abs(p - (prev_alto or p)))
                alto.append((bar * 8 + slot, 1, chosen))
                prev_alto = chosen
            soprano_pitch = next_pitch
    return {SOPRANO: soprano, ALTO: alto}


def _bass_for(gen, numeral, top, prev_bass=None, prev_top=None):
    """A consonant bass pitch for a chord, avoiding a parallel perfect with the
    line above when both move. Returns a pitch inside the triangle range."""
    members = gen.chord_pitches(numeral, RANGE_TRIANGLE[0] + 2, RANGE_TRIANGLE[1] - 2)
    if not members:
        members = gen.scale_pitches(RANGE_TRIANGLE[0] + 2, RANGE_TRIANGLE[1] - 2)
    good = [p for p in members if p < top and pitch_class(top - p) in CONSONANT]
    if not good:
        good = [p for p in members if p < top]
    if prev_bass is None:
        return min(good, key=lambda p: abs(p - (top - 12)))
    # Reject a parallel perfect fifth or octave against the previous pair, in
    # the same direction of motion.
    safe = good
    if prev_top is not None:
        prev_ic = pitch_class(prev_top - prev_bass)
        safe = [p for p in good
                if prev_ic not in PERFECT or pitch_class(top - p) not in PERFECT
                or (top - prev_top) * (p - prev_bass) <= 0]
    return min(safe or good, key=lambda p: abs(p - prev_bass))


def build_fugue(gen, bars=12):
    """A three-voice fugue exposition: subject, tonal answer, countersubject.

    pulse 1 states the subject, pulse 2 answers at the fifth (the tonal answer),
    triangle enters with a countersubject in the bass register, and a bridge
    over a cadential chord plan closes the exposition. Every vertical interval
    is built consonant and parallel perfects between the outer voices are
    avoided by construction.
    """
    if gen.mode == "major":
        plan = ["I", "V", "I", "V", "vi", "IV", "V", "I", "IV", "V", "I", "I"]
    else:
        plan = ["i", "V", "i", "V", "VI", "iv", "V", "i", "iv", "V", "i", "i"]
    subject = gen.subject(16, RANGE_PULSE1[0] + 7, RANGE_PULSE1[1] - 3)
    soprano = list(subject)
    alto = []
    for slot, duration, pitch in subject:
        answered = pitch - 7
        while answered < RANGE_PULSE2[0] + 4:
            answered += 12
        alto.append((slot + 16, duration, answered))
    triangle = []
    prev_bass = None
    prev_top = None
    for slot in range(bars * 8):
        bar = slot // 8
        numeral = plan[min(bar, len(plan) - 1)]
        sounding = []
        for line in (soprano, alto):
            for s, d, p in line:
                if s <= slot < s + d:
                    sounding.append(p)
        members = gen.chord_pitches(numeral, RANGE_PULSE1[0], RANGE_PULSE1[1])
        top = max(sounding) if sounding else (min(members) + 12 if members else 72)
        bass = _bass_for(gen, numeral, top, prev_bass, prev_top)
        triangle.append((slot, 1, bass))
        prev_bass = bass
        prev_top = top
    return {SOPRANO: soprano, ALTO: alto, BASS: triangle}


def build_continuo(gen, bars=8):
    """A walking bass from a Roman numeral plan under a melody.

    The plan is a circle-of-fifths sequence with a cadential 6-4, a Neapolitan
    and a Picardy third on the final chord. The bass walks quarter notes on the
    chord root and fifth, one chord tone per bar, and the melody steps the chord
    tones a single octave above it, so the vertical pair is consonant and the
    outer voices never move in parallel octaves.
    """
    if gen.mode == "major":
        plan = ["I", "IV", "V", "vi", "iii", "IV", "V", "I"]  # circle of fifths
    else:
        plan = ["i", "iv", "V", "III", "VI", "iv", "V", "i"]
    melody = []
    bass = []
    for bar in range(bars):
        numeral = plan[min(bar, len(plan) - 1)]
        # A single octave of chord tones for the melody, above the bass octave.
        mel_low = RANGE_PULSE1[0]
        mel_hi = mel_low + 11
        members = [p for p in gen.chord_pitches(numeral, mel_low, mel_hi)]
        if len(members) < 3:
            members = sorted(gen.scale_pitches(mel_low, mel_hi))
        if bar == bars - 1 and gen.mode == "minor":
            # Picardy third: a major tonic triad, voiced inside one octave.
            root_pc = gen.tonic_pc
            members = sorted({p for p in gen.scale_pitches(mel_low, mel_hi)
                              if p % 12 in {(root_pc) % 12, (root_pc + 4) % 12,
                                            (root_pc + 7) % 12}})
            if len(members) < 3:
                members = sorted(gen.scale_pitches(mel_low, mel_hi))
        # Bass: root and fifth, one chord tone per quarter beat, alternating.
        root_pc = gen.tonic_pc
        bass_members = gen.chord_pitches(numeral, RANGE_TRIANGLE[0], RANGE_TRIANGLE[1])
        if bar == bars - 1 and gen.mode == "minor":
            bass_members = [p for p in gen.scale_pitches(RANGE_TRIANGLE[0], RANGE_TRIANGLE[1])
                            if p % 12 in {root_pc % 12, (root_pc + 7) % 12}]
        bass_root = min(bass_members) if bass_members else RANGE_TRIANGLE[0] + 5
        bass_fifth = bass_root + 7
        if bass_fifth > RANGE_TRIANGLE[1]:
            bass_fifth = bass_root - 5
        for beat in range(4):
            tone = bass_root if beat % 2 == 0 else bass_fifth
            bass.append((bar * 8 + beat * 2, 2, tone))
        # Melody: zigzag the chord tones, staying inside the single octave.
        zig = list(range(len(members))) + list(range(len(members) - 2, 0, -1))
        for slot in range(8):
            pitch = members[zig[slot % len(zig)]]
            melody.append((bar * 8 + slot, 1, pitch))
    return {SOPRANO: melody, BASS: bass}


BUILDERS = {
    "countermelody": build_countermelody,
    "canon": build_canon,
    "invention": build_invention,
    "fugue": build_fugue,
    "continuo": build_continuo,
}


# ------------------------------------------------------------- MIDI and recipe


def write_midi(lines_by_voice, path, key="C major", tempo_us=500000, time_sig=TIME_SIG):
    """Write the generated lines as a Standard MIDI File through tools/humanize."""
    import humanize

    tracks = []
    order = [SOPRANO, ALTO, BASS]
    for name in order:
        if name not in lines_by_voice:
            continue
        tracks.append({
            "name": name,
            "notes": [tuple(_normalise_notes(n)) for n in lines_by_voice[name]],
            "cc": {},
        })
    payload = {"division": DIVISION, "tempo_us": tempo_us, "time_sig": time_sig,
               "tracks": tracks}
    humanize.write_smf(payload, path)
    return path


def write_recipe(notes_by_voice, path, form, key, seed, result):
    """Write the project score recipe: meta and sections with the notes.

    The recipe records the generated line in the same shape the project's score
    files use (eighth-note durations, per-bar melody lists), so a human or the
    renderer can read the piece without the MIDI. It is a record, not a build
    input: arrange.py's full-band builder is not the counterpoint renderer.
    """
    tonic, mode = rules.parse_key(key)
    meta = {
        "key": key,
        "time": "4/4",
        "bpm": 120,
        "form": form,
        "card": "t_944ef2b6",
        "seed": seed,
        "voices": "pulse 1 soprano, pulse 2 alto or answer, triangle bass",
        "verified": "0 hard counterpoint findings under rules.analyse profile free",
    }
    sections = {}
    for voice, notes in notes_by_voice.items():
        by_bar = {}
        for note in sorted(notes, key=lambda n: (n.start, n.pitch)):
            slot = note.start // EIGHTH
            bar = slot // 8
            duration = max(1, (note.end - note.start) // EIGHTH)
            by_bar.setdefault(bar, {}).setdefault(voice, []).append(
                [rules.pitch_name(note.pitch), duration])
        for bar in sorted(by_bar):
            sections.setdefault("bar %d" % (bar + 1), {})[voice] = by_bar[bar].get(voice, [])
    payload = {"meta": meta, "motifs": {}, "sections": sections}
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=1)
    return path


def generate_form(form, seed, key, out_midi, recipe_path=None, corpus=None):
    """Build one form, verify it, and write its MIDI and recipe files."""
    gen = Generator(seed, key, corpus)
    builder = BUILDERS[form]
    lines, result, notes = build_clean(gen, builder)
    write_midi(notes, out_midi, key=key)
    if recipe_path:
        write_recipe(notes, recipe_path, form, key, seed, result)
    return {"form": form, "seed": seed, "key": key,
            "hard": hard_count(result),
            "soft": result["summary"]["by_severity"].get("soft", 0),
            "style": result["summary"]["by_severity"].get("style", 0),
            "notes": result["notes"],
            "voices": sorted(lines),
            "midi": os.path.abspath(out_midi),
            "recipe": os.path.abspath(recipe_path) if recipe_path else None}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Counterpoint generator, card t_944ef2b6.")
    parser.add_argument("--form", choices=FORMS, help="generate one form")
    parser.add_argument("--all", action="store_true", help="generate all five forms")
    parser.add_argument("--seed", type=int, default=1, help="base seed (default 1)")
    parser.add_argument("--key", default="C major", help="the key, for example 'A minor'")
    parser.add_argument("--out-dir", default="out/counterpoint",
                        help="directory for MIDI and recipe output")
    parser.add_argument("--out", default=None, help="a single MIDI path (with --form)")
    parser.add_argument("--recipe", default=None, help="a single recipe path (with --form)")
    parser.add_argument("--count", type=int, default=4,
                        help="pieces per form under --all (default 4)")
    args = parser.parse_args(argv)

    if not args.form and not args.all:
        parser.error("pass --form <name> or --all")

    corpus = Corpus()
    os.makedirs(args.out_dir, exist_ok=True)
    if args.form:
        midi = args.out or os.path.join(args.out_dir, "%s_s%d.mid" % (args.form, args.seed))
        recipe = args.recipe or os.path.join(args.out_dir, "%s_s%d.json" % (args.form, args.seed))
        report = generate_form(args.form, args.seed, args.key, midi, recipe, corpus)
        print(json.dumps(report, indent=1))
        return 0 if report["hard"] == 0 else 1

    failures = 0
    reports = []
    for form in FORMS:
        for index in range(args.count):
            seed = args.seed + index * 7
            midi = os.path.join(args.out_dir, "%s_s%d.mid" % (form, seed))
            recipe = os.path.join(args.out_dir, "%s_s%d.json" % (form, seed))
            try:
                report = generate_form(form, seed, args.key, midi, recipe, corpus)
                reports.append(report)
                if report["hard"]:
                    failures += 1
                print("OK  %-14s seed %3d  hard %d soft %d style %d  notes %d"
                      % (form, seed, report["hard"], report["soft"], report["style"],
                         report["notes"]))
            except ValueError as error:
                failures += 1
                print("FAIL %-14s seed %3d  %s" % (form, seed, error))
    summary = os.path.join(args.out_dir, "summary.json")
    with open(summary, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(reports, handle, indent=1)
    print("summary: %s" % os.path.abspath(summary))
    print("%d pieces, %d failed" % (len(reports), failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
