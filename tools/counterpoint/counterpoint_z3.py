"""FV-4b: every counterpoint rule in formal/FV-4-rules.md as a named Z3 assertion (card t_89d80b48).

Where FV-4's first encoder (`smt_counterpoint.py`) imported the M1a engine and solved music, this
module takes the opposite design decision on purpose: it is PURE. It imports nothing but the
standard library and z3, reads no file, touches no score, and has no import-time side effects, so
the rule set can be exercised, mutated and compared against the checker offline, on any machine,
without the repo, the venv's tool path or `rules.py` being importable. The rule predicates, the
interval sets and the NES range table are restated here as data, copied from
`Shared/projects/arananet/manager/formal/FV-4-rules.md` (sections 2, 4 and 5), which in turn was
read off `tools/counterpoint/rules.py`.

THE MODEL

A texture is a grid of integer pitches: `voices x positions`, one note per voice per position,
homorhythmic, no rests and no held notes. Each voice has one z3.Int per position, bounded by that
voice's NES register (CP-17), optionally restricted to the pitch classes of a key. Positions are
beats of a declared metre, so `accent(t)` is `rules.accent_positions` verbatim.

EVERY ASSERTION IS NAMED AFTER ITS RULE

`build_constraints()` returns `Constraint`s whose name begins with the rule id, e.g.

    CP-09:parallel perfects (pulse 1+triangle) @t=1
    CP-17:range triangle @t=0
    CP-15:spacing (pulse 1+pulse 2) @t=3
    PIN:pulse 1 @t=0

`solve()` asserts each one with `assert_and_track`, turns the model's unsat core into the list of
rules that blocked the line, and `describe_core()` renders that core as text. A failure therefore
says which rule refused the line, not a bare unsat.

RULE COVERAGE (what this module does and does not claim)

  CP-01 encoded   no dissonance on a strong or medium beat (first-species consonance, stricter
                  than the checker, which lets a stepwise accented dissonance pass as CP-06).
  CP-02 encoded   on a weak beat a dissonance must be a strict passing or neighbour tone; the
                  fallthrough branch of device_for never fires.
  CP-04 not modellable on this grid: it needs a note HELD into a dissonance, and the grid has one
                  attack per voice per position, so `held(n,t)` is never true and the predicate is
                  vacuously satisfied. `WORKED_EXAMPLES` records the doc's suspension case as
                  not_modelled rather than pretending to solve it.
  CP-05 not modellable, same reason (it is a label on a suspension).
  CP-06 encoded by exclusion: an accented dissonance is forbidden outright, so no appoggiatura.
  CP-07 encoded by exclusion: a weak dissonance entered by leap is not passing or neighbour.
  CP-08 encoded by exclusion: the returning-neighbour branch is the only stepwise opposite-sign
                  step pattern allowed.
  CP-09 encoded   parallel perfects, on every pair by default (stricter than the checker's outer
                  pair; `pairs="outer"` reproduces the checker exactly).
  CP-10 encoded   hidden perfects, predicate taken from the CODE: `ic1 != ic2`, not the doc's
                  `ic1 not in PERF`. The doc's line 259-260 overstates the condition and its own
                  appendix A row for the hidden fifth (ic1 = 0 into ic2 = 7) contradicts it; the
                  code and the appendix agree, so this module follows them.
  CP-11 encoded   leading tone over a dominant bass holds or rises a semitone; needs a key.
  CP-12 encoded   a raw 10 or 11 above the bass falls by step or never arrives.
  CP-13 encoded   p_upper >= p_lower on adjacent rank pairs, the exact negation of the fault.
  CP-14 encoded   the lower voice does not rise above the upper's previous pitch nor the upper
                  fall below the lower's previous pitch, adjacent rank pairs, from position 1.
  CP-15 encoded   adjacent gap at most 12, the pair above the bass at most 19, three voices up
                  only, because the checker has no two-voice spacing rule.
  CP-16 encoded   a leap larger than a fourth may not be followed by a same-direction leap larger
                  than a step, the checker's thresholds verbatim.
  CP-17 encoded   the variable bounds ARE the register, asserted per voice per position so the
                  core names the voice.
  CP-03  absent from the checker and from here; the id is a historical gap, keep it.

WHAT IT DOES NOT DO

No cadence, motif, seed bias or contrary-motion preference: those are aesthetic, they only remove
solutions, and M1b's seeded search owns them. No rate budget (the gate's per-rule Bach budget is a
calibration, not a rule). No leap cap and no melodic tritone rule: the checker has neither, so
claiming one here would make the encoder and the gate two different rule sets.

USAGE

    python tools/counterpoint/counterpoint_z3.py --canon --positions 8 --key "C major"
    python tools/counterpoint/counterpoint_z3.py --voices "pulse 1,triangle" --positions 4 \\
        --pin "pulse 1=72 74" --pin "triangle=48 50"
    python tools/counterpoint/counterpoint_z3.py --worked-examples

Every run prints JSON: status, model, the unsat core and the rules in it, assertion count, time.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import z3

# ------------------------------------------------------------------ the rule data (FV-4 sec. 5)

NES_RANGES = {
    "vrc6 pulse a": (55, 96),
    "vrc6 pulse b": (45, 84),
    "vrc6 saw": (43, 67),
    "pulse 1": (55, 83),
    "pulse 2": (43, 96),
    "triangle": (36, 55),
}
DEFAULT_RANGE = (33, 96)   # A1 to C7

VOICE_ALIASES = {
    "pulse1": "pulse 1", "pulse 1": "pulse 1", "pulse_1": "pulse 1", "p1": "pulse 1",
    "pulse2": "pulse 2", "pulse 2": "pulse 2", "pulse_2": "pulse 2", "p2": "pulse 2",
    "tri": "triangle", "train": "triangle", "triangle": "triangle", "tri.": "triangle",
    "vrc6pulsea": "vrc6 pulse a", "vrc6 pulse a": "vrc6 pulse a",
    "vrc6pulseb": "vrc6 pulse b", "vrc6 pulse b": "vrc6 pulse b",
    "vrc6saw": "vrc6 saw", "vrc6 saw": "vrc6 saw",
}

CONSONANT = frozenset((0, 3, 4, 7, 8, 9))
PERFECT = frozenset((0, 7))
DISSONANT = frozenset((1, 2, 5, 6, 10, 11))
DISSONANT_OFF_BASS = frozenset((1, 2, 6, 10, 11))   # 5 is judged by name, as is_dissonant does

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
KEY_NAMES = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")
LETTERS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
MAJOR_SCALE = (0, 2, 4, 5, 7, 9, 11)
MINOR_SCALE = (0, 2, 3, 5, 7, 8, 10)

RULE_TITLES = {
    "CP-01": "dissonance on an accented beat",
    "CP-02": "weak-beat dissonance with no device",
    "CP-04": "suspension not resolved down by step",
    "CP-05": "suspension figure outside the canonical set",
    "CP-06": "appoggiatura",
    "CP-07": "passing tone entered or left by leap",
    "CP-08": "neighbour tone that does not return",
    "CP-09": "parallel perfect fifth or octave",
    "CP-10": "hidden (direct) perfect fifth or octave",
    "CP-11": "leading tone not resolved up to the tonic",
    "CP-12": "chordal seventh not resolved down by step",
    "CP-13": "voice crossing",
    "CP-14": "voice overlap",
    "CP-15": "spacing wider than an octave between upper voices",
    "CP-16": "two leaps in the same direction",
    "CP-17": "note outside the voice's NES range",
}

MOTION_PAIR_SCOPES = ("all", "outer")


# ------------------------------------------------------------------ pitch and metre helpers

def pitch_name(value):
    """A MIDI number as a name, 'C4' for 60."""
    return "%s%d" % (NOTE_NAMES[int(value) % 12], int(value) // 12 - 1)


def parse_pitch(text):
    """'Bb5', 'F#4' or a bare MIDI number such as '72' to a MIDI number."""
    text = str(text).strip()
    if text.lstrip("-").isdigit():
        return int(text)
    letter = text[0].upper()
    if letter not in LETTERS:
        raise ValueError("cannot read the pitch %r" % text)
    pitch = LETTERS[letter]
    index = 1
    while index < len(text) and text[index] in "#b":
        pitch += 1 if text[index] == "#" else -1
        index += 1
    return pitch + 12 * (int(text[index:]) + 1)


def normalise_voice(name):
    """A track name as the voice name the chip tables use."""
    text = " ".join(str(name or "").strip().lower().split())
    return VOICE_ALIASES.get(text, text)


def accent_positions(beats):
    """Which beats of a bar are strong and which are medium, rules.accent_positions verbatim."""
    if beats and beats % 3 == 0 and beats > 3:
        return {0}, {beats // 3, 2 * beats // 3}
    if beats == 4:
        return {0}, {2}
    return {0}, set()


def accent_of(position, beats=4):
    """The metric weight of a position: strong, medium or weak (never offbeat on this grid)."""
    strong, medium = accent_positions(beats)
    beat = position % beats
    if beat in strong:
        return "strong"
    if beat in medium:
        return "medium"
    return "weak"


def key_pitch_classes(key):
    """The pitch classes of (tonic, mode), minor including the raised leading tone."""
    tonic, mode = key
    steps = set(MAJOR_SCALE if mode == "major" else MINOR_SCALE)
    if mode == "minor":
        steps.add(11)
    return sorted({(int(tonic) + step) % 12 for step in steps})


# ------------------------------------------------------------------ the problem

class Constraint(object):
    """One named assertion: the rule it comes from, where it applies, and the z3 expression."""

    __slots__ = ("name", "rule", "detail", "expr")

    def __init__(self, rule, detail, expr):
        self.rule = rule
        self.detail = detail
        self.name = "%s:%s" % (rule, detail)
        self.expr = expr

    def __repr__(self):
        return "Constraint(%r)" % self.name


class Texture(object):
    """Voices, positions, metre, key, and the grid a caller pins before solving.

    voices: names in rank order, top line first, as the checker's Score.rank would order them.
    positions: how many attacked notes per voice (beats of the metre).
    key: (tonic pitch class, mode) or None. CP-11 needs it; None switches CP-11 off.
    pins: {(voice, position): pitch}, the problem statement rather than a rule.
    """

    def __init__(self, voices, positions, beats=4, key=(0, "major"), pins=None, label=None):
        self.voices = [normalise_voice(v) for v in voices]
        if len(set(self.voices)) != len(self.voices):
            raise ValueError("a voice appears twice: %r" % (self.voices,))
        self.positions = int(positions)
        if self.positions < 1:
            raise ValueError("a texture needs at least one position")
        self.beats = int(beats)
        if self.beats < 1:
            raise ValueError("a bar needs at least one beat")
        self.key = key
        self.label = label
        self.pins = {}
        for (voice, position), pitch in (pins or {}).items():
            self.pin(voice, position, pitch)
        self._vars = {}

    # -- construction helpers -----------------------------------------------------------

    def pin(self, voice, position, pitch):
        """Fix one note of the grid to a pitch, the way a worked example states its case."""
        name = normalise_voice(voice)
        if name not in self.voices:
            self.voices.append(name)
        position = int(position)
        if not 0 <= position < self.positions:
            raise ValueError("position %d is outside 0..%d" % (position, self.positions - 1))
        self.pins[(name, position)] = int(pitch)

    def bounds(self, voice):
        """The declared NES register of a voice, the CP-17 bound."""
        return NES_RANGES.get(voice, DEFAULT_RANGE)

    def var(self, voice, position):
        """The z3 Int for one note of the grid."""
        key = (voice, position)
        if key not in self._vars:
            token = "".join(c if c.isalnum() else "_" for c in voice)
            self._vars[key] = z3.Int("p_%s_%d" % (token, position))
        return self._vars[key]

    def as_dict(self):
        return {"label": self.label, "voices": list(self.voices), "positions": self.positions,
                "beats": self.beats, "key": self.key,
                "pins": {"%s@%d" % k: v for k, v in sorted(self.pins.items())}}

    # -- vertical vocabulary ------------------------------------------------------------

    def bass_at(self, position):
        """The lowest sounding pitch at a position, Score.bass_at as a z3 term."""
        first = self.voices[0]
        lowest = self.var(first, position)
        for name in self.voices[1:]:
            pitch = self.var(name, position)
            lowest = z3.If(pitch < lowest, pitch, lowest)
        return lowest

    def _low_high(self, voice_a, voice_b, position):
        """The two pitches of a pair in (low, high) order, as z3 terms."""
        a = self.var(voice_a, position)
        b = self.var(voice_b, position)
        return z3.If(a <= b, a, b), z3.If(a <= b, b, a)

    def dissonant(self, voice_a, voice_b, position):
        """Checker.is_dissonant for one pair at one position, in the chord-assumption form.

        Consonance is judged on the interval class. A fourth IS dissonant when it is a simple
        fourth directly above the bass (the checker forgives it only for a 6/4, which this model
        forbids outright, so forbidding all of them is never weaker). A raw 10 or 11 above the bass
        is a chordal seventh, consonant, and CP-12 judges it. Everything else follows the class.
        """
        low, high = self._low_high(voice_a, voice_b, position)
        raw = high - low
        ic = raw % 12
        above_bass = low == self.bass_at(position)
        simple_fourth = z3.And(ic == 5, raw == 5, above_bass)
        plain = z3.Or(*[ic == value for value in DISSONANT_OFF_BASS])
        chordal = z3.And(z3.Or(raw == 10, raw == 11), above_bass)
        return z3.Or(simple_fourth, z3.And(plain, z3.Not(chordal)))

    def device(self, voice, position):
        """The strict passing or neighbour reading of the note attacked at a position.

        These are the two device_for branches that pass silently: same-direction steps of a second
        or less, or a step out that returns to where the note came from. Signs are compared as
        booleans, so the expression stays linear and z3 solves it fast.
        """
        pitch = self.var(voice, position)
        step_in = pitch - self.var(voice, position - 1)
        step_out = self.var(voice, position + 1) - pitch
        stepwise_in = z3.Or(*[step_in == value for value in (-2, -1, 1, 2)])
        stepwise_out = z3.Or(*[step_out == value for value in (-2, -1, 1, 2)])
        same_direction = z3.Or(z3.And(step_in > 0, step_out > 0),
                               z3.And(step_in < 0, step_out < 0))
        passing = z3.And(stepwise_in, stepwise_out, same_direction)
        neighbour = z3.And(stepwise_in, stepwise_out,
                           self.var(voice, position + 1) == self.var(voice, position - 1))
        return z3.Or(passing, neighbour)

    def ordered_pairs(self, scope="all"):
        """The voice pairs the motion rules look at: every pair, or the checker's outer pair."""
        pairs = []
        for index, upper in enumerate(self.voices):
            for lower in self.voices[index + 1:]:
                pairs.append((upper, lower))
        if scope == "outer" and len(self.voices) >= 2:
            return [(self.voices[0], self.voices[-1])]
        if scope not in MOTION_PAIR_SCOPES:
            raise ValueError("pairs must be one of %r" % (MOTION_PAIR_SCOPES,))
        return pairs

    def adjacent_pairs(self):
        """Rank-adjacent voice pairs, which is the checker's scope for CP-13, CP-14 and CP-15."""
        return [(self.voices[index], self.voices[index + 1])
                for index in range(len(self.voices) - 1)]


# ------------------------------------------------------------------ the encoder

def build_constraints(texture, skip=(), scale_only=False, pairs="all"):
    """Translate every predicate of FV-4-rules.md into named z3 assertions.

    Returns the assertions in rule order. `skip` names rule ids to leave out, which is how the
    mutation test proves a block binds. `pairs` chooses the CP-09 and CP-10 scope: "all" is the
    FV-4 broadening (section 6.1), "outer" is the checker's own scope.
    """
    skipped = set(skip or ())
    out = []

    def add(rule, detail, expr):
        if rule not in skipped:
            out.append(Constraint(rule, detail, expr))

    # the problem statement, not a rule
    for (voice, position), pitch in sorted(texture.pins.items()):
        out.append(Constraint("PIN", "%s @t=%d" % (voice, position),
                              texture.var(voice, position) == int(pitch)))

    # CP-17: the bounds ARE the register, asserted per note so the core names the voice
    for voice in texture.voices:
        low, high = texture.bounds(voice)
        for position in range(texture.positions):
            var = texture.var(voice, position)
            add("CP-17", "range %s @t=%d" % (voice, position),
                z3.And(var >= low, var <= high))

    # a model restriction, not a copied rule (FV-4 section 6.9): key membership when asked for
    if scale_only and texture.key is not None:
        classes = key_pitch_classes(texture.key)
        for voice in texture.voices:
            for position in range(texture.positions):
                var = texture.var(voice, position)
                out.append(Constraint("KEY", "scale %s @t=%d" % (voice, position),
                                      z3.Or(*[var % 12 == pc for pc in classes])))

    # CP-13: the upper voice never sounds below the lower one, the fault's exact negation
    for upper, lower in texture.adjacent_pairs():
        for position in range(texture.positions):
            add("CP-13", "crossing %s+%s @t=%d" % (upper, lower, position),
                texture.var(upper, position) >= texture.var(lower, position))

    # CP-14: no overlap against where each voice was one position earlier
    for upper, lower in texture.adjacent_pairs():
        for position in range(1, texture.positions):
            add("CP-14", "overlap %s+%s @t=%d" % (upper, lower, position),
                z3.And(texture.var(lower, position) <= texture.var(upper, position - 1),
                       texture.var(upper, position) >= texture.var(lower, position - 1)))

    # CP-15: at most an octave, 19 above the bass, and only from three voices up
    if len(texture.voices) >= 3:
        for index, (upper, lower) in enumerate(texture.adjacent_pairs()):
            limit = 12 if index + 2 < len(texture.voices) else 19
            for position in range(texture.positions):
                add("CP-15", "spacing %s+%s @t=%d" % (upper, lower, position),
                    texture.var(upper, position) - texture.var(lower, position) <= limit)

    # CP-09 parallel perfects, CP-10 hidden perfects: between consecutive positions
    for upper, lower in texture.ordered_pairs(scope=pairs):
        for position in range(texture.positions - 1):
            move_up = texture.var(upper, position + 1) - texture.var(upper, position)
            move_dn = texture.var(lower, position + 1) - texture.var(lower, position)
            ic1 = (texture.var(upper, position) - texture.var(lower, position)) % 12
            ic2 = (texture.var(upper, position + 1) - texture.var(lower, position + 1)) % 12
            both_move = z3.And(move_up != 0, move_dn != 0)
            same_direction = z3.Or(z3.And(move_up > 0, move_dn > 0),
                                   z3.And(move_up < 0, move_dn < 0))
            into_perfect = z3.Or(*[ic2 == value for value in PERFECT])
            outer = "outer " if pairs == "outer" else ""
            add("CP-09", "%sparallel %s+%s @t=%d" % (outer, upper, lower, position + 1),
                z3.Not(z3.And(both_move, same_direction, into_perfect, ic1 == ic2)))
            # the rule as the CHECKER writes it: a different interval class into a perfect, with
            # the voice that is higher at the first instant leaping. The doc says `ic1 not in
            # PERF`; the code says `ic1 != ic2`, and the doc's own appendix row agrees with the
            # code (a double octave into a fifth is a hidden fifth). Follow the code.
            upper_move = z3.If(texture.var(upper, position) > texture.var(lower, position),
                               move_up, move_dn)
            add("CP-10", "%shidden %s+%s @t=%d" % (outer, upper, lower, position + 1),
                z3.Not(z3.And(both_move, same_direction, into_perfect, ic1 != ic2,
                              z3.Or(upper_move > 2, upper_move < -2))))

    # CP-01 and CP-02: the vertical block. Accented positions are consonant outright (stricter
    # than the checker, which would pass an appoggiatura), and a weak position may carry a
    # dissonance only as a strict passing or neighbour tone. The two ends of the texture have no
    # incoming or outgoing step, so a device is impossible there and the checker faults them.
    for position in range(texture.positions):
        accented = accent_of(position, texture.beats) in ("strong", "medium")
        edge = position == 0 or position == texture.positions - 1
        for index, upper in enumerate(texture.voices):
            for lower in texture.voices[index + 1:]:
                dissonant = texture.dissonant(upper, lower, position)
                if accented:
                    add("CP-01", "no accented dissonance %s+%s @t=%d"
                        % (upper, lower, position), z3.Not(dissonant))
                elif edge:
                    add("CP-02", "no edge dissonance %s+%s @t=%d"
                        % (upper, lower, position), z3.Not(dissonant))
                else:
                    add("CP-02", "device %s+%s @t=%d" % (upper, lower, position),
                        z3.Implies(dissonant,
                                   z3.Or(texture.device(upper, position),
                                         texture.device(lower, position))))

    # CP-11: a leading tone over a dominant bass holds or rises a semitone. Needs a key.
    if texture.key is not None:
        tonic = int(texture.key[0]) % 12
        leading = (tonic - 1) % 12
        dominant = (tonic + 7) % 12
        for voice in texture.voices:
            for position in range(texture.positions - 1):
                current = texture.var(voice, position)
                following = texture.var(voice, position + 1)
                fires = z3.And(current % 12 == leading,
                               texture.bass_at(position) % 12 == dominant)
                add("CP-11", "leading tone %s @t=%d" % (voice, position),
                    z3.Implies(fires, z3.Or(following == current, following == current + 1)))

    # CP-12: a chordal seventh above the bass falls by step or never arrives
    for voice in texture.voices:
        for position in range(texture.positions - 1):
            current = texture.var(voice, position)
            gap = current - texture.bass_at(position)
            add("CP-12", "seventh %s @t=%d" % (voice, position),
                z3.Implies(z3.Or(gap == 10, gap == 11),
                           z3.Or(texture.var(voice, position + 1) == current - 1,
                                 texture.var(voice, position + 1) == current - 2)))

    # CP-16: two leaps in the same direction, the checker's thresholds
    for voice in texture.voices:
        for position in range(texture.positions - 2):
            first = texture.var(voice, position + 1) - texture.var(voice, position)
            second = texture.var(voice, position + 2) - texture.var(voice, position + 1)
            leap = z3.Or(first > 5, first < -5)
            again = z3.Or(second > 2, second < -2)
            same_way = z3.Or(z3.And(first > 0, second > 0), z3.And(first < 0, second < 0))
            add("CP-16", "leaps %s @t=%d" % (voice, position),
                z3.Implies(z3.And(leap, again), z3.Not(same_way)))

    return out


# ------------------------------------------------------------------ the solver

def _rule_of(name):
    """The rule id a tracked assertion name belongs to."""
    return name.split(":", 1)[0]


GIVEN = ("PIN", "CANON")   # problem statement, never dropped when the core is minimised


def _minimise(constraints, timeout_ms):
    """Shrink an unsat set to an irreducible one, so the core names the rules that actually bind.

    Z3's unsat core is a subset, not a minimum: a 6 assertion problem can come back with a core
    that also lists a rule that happens to be unstated in a trivially unsat branch. Deletion is
    cheap here (each re-check is milliseconds on this grid) and it turns "the core contains CP-01"
    into "CP-01 is what blocked the line". Given notes are never dropped, so the report keeps the
    input that was refused. Returns the kept constraints.
    """
    current = list(constraints)
    index = 0
    while index < len(current):
        candidate = current[index]
        if candidate.rule in GIVEN:
            index += 1
            continue
        trial = current[:index] + current[index + 1:]
        solver = z3.Solver()
        solver.set("timeout", int(timeout_ms))
        for constraint in trial:
            solver.add(constraint.expr)
        if solver.check() == z3.unsat:
            current = trial
        else:
            index += 1
    return current


def _solver_for(constraints, timeout_ms, track):
    """A solver over a constraint list, with or without unsat-core tracking.

    Tracking costs real time (the tracker booleans and core extraction turn a 3.6 s SAT solve
    into a 30 s one on three voices), so tracking is only paid for when a problem is UNSAT and
    the core is what the caller needs.
    """
    solver = z3.Solver()
    solver.set("timeout", int(timeout_ms))
    if track:
        solver.set(unsat_core=True)
    for constraint in constraints:
        if track:
            solver.assert_and_track(constraint.expr, constraint.name)
        else:
            solver.add(constraint.expr)
    return solver


def solve(texture, timeout_ms=30000, skip=(), scale_only=False, pairs="all", minimise_core=True,
          minimise_limit=400):
    """Solve one texture and report either the model or the rules that blocked it.

    The result is JSON-able: status, the grid, the unsat core with one entry per blocked
    assertion, `core_rules` (the rule ids the core names, PIN excluded) and the wall time.
    A SAT problem is solved without core tracking; an UNSAT one is re-solved with it, then the
    core is reduced to an irreducible set so `core_rules` names the rules that actually bind.
    """
    constraints = build_constraints(texture, skip=skip, scale_only=scale_only, pairs=pairs)
    started = time.perf_counter()
    solver = _solver_for(constraints, timeout_ms, track=False)
    status = solver.check()
    result = {
        "texture": texture.as_dict(),
        "status": str(status),
        "assertions": len(constraints),
        "rules_asserted": sorted({constraint.rule for constraint in constraints}),
        "skipped": sorted(skip or ()),
        "pairs": pairs,
        "elapsed_s": round(time.perf_counter() - started, 4),
        "core_minimised": False,
        "model": None,
        "model_names": None,
        "core": [],
        "core_rules": [],
    }
    if status == z3.sat:
        model = solver.model()
        grid = {}
        for voice in texture.voices:
            row = [model.evaluate(texture.var(voice, position),
                                  model_completion=True).as_long()
                   for position in range(texture.positions)]
            grid[voice] = row
        result["model"] = grid
        result["model_names"] = {voice: [pitch_name(p) for p in row]
                                 for voice, row in grid.items()}
    elif status == z3.unsat:
        tracked = _solver_for(constraints, timeout_ms, track=True)
        if tracked.check() != z3.unsat:      # a timeout on the second pass loses the core only
            result["status"] = "unknown"
            result["reason"] = "core extraction timed out after an unsat first pass"
            return result
        names = {str(name) for name in tracked.unsat_core()}
        if minimise_core and len(constraints) <= minimise_limit:
            kept = _minimise(constraints, timeout_ms)
            names = {constraint.name for constraint in kept}
            result["core_minimised"] = True
        result["core"] = sorted(names)
        result["core_rules"] = sorted({_rule_of(name) for name in result["core"]}
                                      - {"PIN", "CANON"})
        result["elapsed_s"] = round(time.perf_counter() - started, 4)
    else:
        result["reason"] = solver.reason_unknown()
    return result


def describe_core(core):
    """The unsat core as readable lines: which rule refused, and on which pair or voice."""
    lines = []
    for name in core:
        rule = _rule_of(name)
        detail = name.split(":", 1)[1] if ":" in name else ""
        if rule == "PIN":
            lines.append("given note %s" % detail.strip())
            continue
        lines.append("%s %s: %s" % (rule, RULE_TITLES.get(rule, "?"), detail.strip()))
    return lines


# ------------------------------------------------------------------ worked examples

class WorkedExample(object):
    """One case from FV-4-rules.md appendix A, restated as a grid this module can solve.

    `checker_rules` is what the appendix MEASURED for the case (the rules the checker reports),
    and a pass means the module's core is non-empty, every rule it names is one the checker also
    reports for that case, and it names at least one of `expect_rules`. A pinned grid usually
    breaks several rules at once, so an irreducible core picks whichever one survives deletion;
    naming a rule the checker does NOT report would be a false accusation and fails the case.
    `expect` "sat" means no rule fires, "not_modelled" means the case needs a held note.
    """

    __slots__ = ("case", "doc_expectation", "voices", "pitches", "key", "expect",
                 "expect_rules", "checker_rules", "stricter", "note")

    def __init__(self, case, doc_expectation, voices, pitches, expect, expect_rules=(),
                 checker_rules=(), key=(0, "major"), stricter=False, note=""):
        self.case = case
        self.doc_expectation = doc_expectation
        self.voices = voices
        self.pitches = pitches
        self.key = key
        self.expect = expect
        self.expect_rules = tuple(expect_rules)
        self.checker_rules = tuple(checker_rules)
        self.stricter = stricter
        self.note = note

    def texture(self):
        positions = max(len(row) for row in self.pitches.values())
        pins = {}
        for voice, row in self.pitches.items():
            for position, pitch in enumerate(row):
                pins[(voice, position)] = pitch
        return Texture(self.voices, positions, beats=4, key=self.key, pins=pins,
                       label=self.case)

    def judge(self, result):
        """Did this module answer the case the way the doc requires? Returns (pass, why)."""
        if result["status"] != "unsat":
            return False, "expected unsat, got %s" % result["status"]
        core = set(result["core_rules"])
        if not core:
            return False, "unsat but the core names no rule"
        extra = core - set(self.checker_rules)
        if extra:
            return False, "core names rules the checker does not report here: %s" % sorted(extra)
        if not core & set(self.expect_rules):
            return False, "core %s names none of %s" % (sorted(core), list(self.expect_rules))
        return True, ""


WORKED_EXAMPLES = (
    WorkedExample("outer parallel octaves", "CP-09 hard",
                  ("pulse 1", "triangle"),
                  {"pulse 1": (72, 74), "triangle": (48, 50)},
                  "unsat", ("CP-09",), ("CP-09",)),
    WorkedExample("inner parallel fifths", "no CP-09 (outer scope only)",
                  ("pulse 1", "pulse 2", "triangle"),
                  {"pulse 1": (67, 69), "pulse 2": (60, 62), "triangle": (43, 50)},
                  "unsat", ("CP-09",), ("CP-09",), stricter=True,
                  note="stricter than the checker on purpose, FV-4 section 6.1: every pair is "
                       "checked, so the inner parallel fifth the checker cannot see is refused "
                       "here. With pairs='outer' this same case comes back SAT, which is the "
                       "parity check against the checker's outer scope."),
    WorkedExample("hidden fifth, upper leaps a fourth", "CP-10 soft",
                  ("pulse 1", "triangle"),
                  {"pulse 1": (67, 72), "triangle": (43, 53)},
                  "unsat", ("CP-10",), ("CP-10",),
                  note="ic1 is 0, a double octave, into ic2 7. The doc's 'ic1 not in PERF' "
                       "clause would refuse this case; the code's 'ic1 != ic2' and the appendix "
                       "both fire it. The module follows the code."),
    WorkedExample("spacing 15, three voices", "CP-15 soft",
                  ("pulse 1", "pulse 2", "triangle"),
                  {"pulse 1": (81,), "pulse 2": (66,), "triangle": (54,)},
                  "unsat", ("CP-15",), ("CP-15",)),
    WorkedExample("spacing 15, two voices", "no CP-15 (three voices up)",
                  ("pulse 1", "triangle"),
                  {"pulse 1": (81,), "triangle": (54,)},
                  "sat"),
    WorkedExample("pulse 1 at 90", "CP-17 hard",
                  ("pulse 1", "triangle"),
                  {"pulse 1": (90,), "triangle": (42,)},
                  "unsat", ("CP-17",), ("CP-17",)),
    WorkedExample("triangle at 60", "CP-17 hard",
                  ("pulse 1", "triangle"),
                  {"pulse 1": (60,), "triangle": (60,)},
                  "unsat", ("CP-17",), ("CP-17",)),
    WorkedExample("two leaps the same way", "CP-16 style, plus CP-01",
                  ("pulse 1", "triangle"),
                  {"pulse 1": (60, 68, 76), "triangle": (41,)},
                  "unsat", ("CP-16",), ("CP-01", "CP-16"),
                  note="the third beat is also dissonant against the pedal, which is the CP-01 "
                       "the appendix reports, so either rule may be the one that binds."),
    WorkedExample("leading tone over the dominant", "CP-11 soft, plus CP-02",
                  ("pulse 1", "triangle"),
                  {"pulse 1": (71, 69), "triangle": (43,)},
                  "unsat", ("CP-11",), ("CP-02", "CP-11"),
                  note="the resolution to A4 is a weak-beat dissonance with no outgoing step, so "
                       "CP-02 is real here too, exactly as the appendix measured."),
    WorkedExample("chordal seventh rising", "CP-12 soft",
                  ("pulse 1", "triangle"),
                  {"pulse 1": (58, 60), "triangle": (48,)},
                  "unsat", ("CP-12",), ("CP-12",)),
    WorkedExample("unprepared seventh on beat 1", "CP-01 hard",
                  ("pulse 1", "triangle"),
                  {"pulse 1": (71,), "triangle": (48,)},
                  "unsat", ("CP-01",), ("CP-01",)),
    WorkedExample("crossing", "CP-13 soft, with CP-14",
                  ("pulse 1", "pulse 2"),
                  {"pulse 1": (80, 64), "pulse 2": (72, 67)},
                  "unsat", ("CP-13", "CP-14"), ("CP-13", "CP-14")),
    WorkedExample("overlap", "CP-14 soft, with CP-10 and CP-12",
                  ("pulse 1", "pulse 2"),
                  {"pulse 1": (60, 72), "pulse 2": (50, 65)},
                  "unsat", ("CP-14", "CP-12"), ("CP-10", "CP-12", "CP-14")),
    WorkedExample("prepared suspension rising", "CP-04 hard",
                  ("pulse 1", "triangle"),
                  {"pulse 1": (72, 74), "triangle": (48, 49)},
                  "not_modelled",
                  note="the suspension needs pulse 1 to HOLD 72 while the bass moves to D3, and "
                       "this grid has one attack per voice per position, so held(n,t) is never "
                       "true and CP-04 is vacuous rather than violated. The grid form of the "
                       "case is a different, weaker test and is not reported as a pass."),
)


def run_worked_examples(pairs="all", timeout_ms=30000):
    """Solve every worked example and report whether this module met its own expectation."""
    rows = []
    for example in WORKED_EXAMPLES:
        if example.expect == "not_modelled":
            rows.append({"case": example.case, "doc": example.doc_expectation,
                         "expected": "not_modelled", "measured": "not_modelled",
                         "pass": None, "core_rules": [], "stricter": example.stricter,
                         "note": example.note})
            continue
        result = solve(example.texture(), timeout_ms=timeout_ms, pairs=pairs)
        measured = result["status"]
        if example.expect == "sat":
            ok, why = measured == "sat", "" if measured == "sat" else "expected sat"
        else:
            ok, why = example.judge(result)
        rows.append({"case": example.case, "doc": example.doc_expectation,
                     "expected": example.expect, "measured": measured,
                     "expected_rules": list(example.expect_rules),
                     "checker_rules": list(example.checker_rules),
                     "stricter": example.stricter,
                     "core_rules": result["core_rules"], "core": result["core"],
                     "elapsed_s": result["elapsed_s"], "pass": ok,
                     "why": why or None, "note": example.note})
    passed = sum(1 for row in rows if row["pass"] is True)
    failed = [row for row in rows if row["pass"] is False]
    return {"pairs": pairs, "cases": len(rows), "passed": passed,
            "skipped_not_modelled": sum(1 for row in rows if row["pass"] is None),
            "failed": failed, "rows": rows,
            "verdict": "PASS" if not failed else "FAIL"}


# ------------------------------------------------------------------ the thin CLI

def canon_spec(voices, positions, beats=4, key=(0, "major"), delay=1, interval=7):
    """A small canon: the top voice restates the bass line `delay` positions later, transposed.

    The imitation is a hard equality, so a canon that no clean texture can carry comes back UNSAT
    with the rules that blocked it, which is a result and not a failure.
    """
    return {"voices": list(voices), "positions": int(positions), "beats": int(beats),
            "key": key, "delay": int(delay), "interval": int(interval)}


def solve_canon(spec, timeout_ms=30000, skip=(), scale_only=False, pairs="all"):
    """Build the canon texture (imitation as tracked equalities) and solve it."""
    voices = [normalise_voice(v) for v in spec["voices"]]
    texture = Texture(voices, spec["positions"], beats=spec["beats"], key=spec["key"],
                      label="canon")
    constraints = build_constraints(texture, skip=skip, scale_only=scale_only, pairs=pairs)
    top, bass = voices[0], voices[-1]
    for position in range(spec["delay"], texture.positions):
        constraints.append(Constraint(
            "CANON", "%s imitates %s @t=%d" % (top, bass, position),
            texture.var(top, position) == texture.var(bass, position - spec["delay"])
            + spec["interval"]))
    solver = _solver_for(constraints, 0, track=False)
    solver.set("timeout", int(timeout_ms))
    started = time.perf_counter()
    status = solver.check()
    out = {"spec": spec, "status": str(status), "assertions": len(constraints),
           "elapsed_s": round(time.perf_counter() - started, 4), "model": None,
           "model_names": None, "core": [], "core_rules": []}
    if status == z3.sat:
        model = solver.model()
        grid = {voice: [model.evaluate(texture.var(voice, position),
                                       model_completion=True).as_long()
                        for position in range(texture.positions)]
                for voice in texture.voices}
        out["model"] = grid
        out["model_names"] = {voice: [pitch_name(p) for p in row] for voice, row in grid.items()}
    elif status == z3.unsat:
        tracked = _solver_for(constraints, timeout_ms, track=True)
        if tracked.check() != z3.unsat:
            out["status"] = "unknown"
            out["reason"] = "core extraction timed out after an unsat first pass"
            return out
        out["core"] = sorted(str(name) for name in tracked.unsat_core())
        out["core_rules"] = sorted({_rule_of(name) for name in out["core"]}
                                  - {"PIN", "CANON"})
        out["elapsed_s"] = round(time.perf_counter() - started, 4)
    else:
        out["reason"] = solver.reason_unknown()
    return out


def _parse_key(text):
    """'C major', 'A minor' or 'none' to (tonic, mode) or None."""
    if text is None:
        return None
    text = str(text).strip()
    if text.lower() in ("none", "off", ""):
        return None
    parts = text.replace("_", " ").split()
    tonic = parse_pitch(parts[0] + "4") % 12
    mode = "minor" if len(parts) > 1 and parts[1].lower().startswith("min") else "major"
    return tonic, mode


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="FV-4b: FV-4 counterpoint rules as named Z3 assertions (card t_89d80b48)")
    parser.add_argument("--voices", default="pulse 1,triangle",
                        help="comma separated, rank order top first")
    parser.add_argument("--positions", type=int, default=8)
    parser.add_argument("--beats", type=int, default=4)
    parser.add_argument("--key", default="C major", help="'C major', 'A minor' or 'none'")
    parser.add_argument("--canon", action="store_true", help="add the canon imitation equalities")
    parser.add_argument("--delay", type=int, default=1)
    parser.add_argument("--interval", type=int, default=7)
    parser.add_argument("--pin", action="append", default=[],
                        help='"pulse 1=72 74", one voice per flag')
    parser.add_argument("--skip", action="append", default=[], help="rule id to leave out")
    parser.add_argument("--scale-only", action="store_true",
                        help="restrict every note to the key's pitch classes")
    parser.add_argument("--pairs", default="all", choices=MOTION_PAIR_SCOPES)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--worked-examples", action="store_true",
                        help="solve every appendix A case and print the comparison")
    parser.add_argument("--json", dest="json_out", default=None, help="also write the JSON here")
    args = parser.parse_args(argv)

    if args.worked_examples:
        payload = run_worked_examples(pairs=args.pairs, timeout_ms=args.timeout_ms)
    elif args.canon:
        spec = canon_spec(args.voices.split(","), args.positions, beats=args.beats,
                          key=_parse_key(args.key), delay=args.delay, interval=args.interval)
        payload = solve_canon(spec, timeout_ms=args.timeout_ms, skip=args.skip,
                              scale_only=args.scale_only, pairs=args.pairs)
    else:
        voices = [name for name in args.voices.split(",") if name.strip()]
        texture = Texture(voices, args.positions, beats=args.beats, key=_parse_key(args.key))
        for flag in args.pin:
            voice, _, pitches = flag.partition("=")
            for position, token in enumerate(pitches.split()):
                texture.pin(voice.strip(), position, parse_pitch(token))
        payload = solve(texture, timeout_ms=args.timeout_ms, skip=args.skip,
                        scale_only=args.scale_only, pairs=args.pairs)

    text = json.dumps(payload, indent=2)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    print(text)
    if args.worked_examples:
        return 0 if payload["verdict"] == "PASS" else 1
    return 0 if payload["status"] == "sat" else (3 if payload["status"] == "unknown" else 2)


if __name__ == "__main__":
    sys.exit(main())
