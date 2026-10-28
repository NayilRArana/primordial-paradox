"""Counterpoint rules as code, for the Primordial Paradox score, card t_836dbb1a (M1a).

Why this exists: the cue carries a dissonance injector and the ear critic is a mix listener, so
nothing in the pipeline asks whether a dissonance in the written notes is PREPARED and RESOLVED, or
whether two voices move into a perfect interval in parallel. The plan
(knowledge/COUNTERPOINT-PLAN-2026-10-26.md) says the fix is a symbolic check, because a critic that
scores the mix cannot hear a wrong note that is only wrong against the other line. This module is
that check. It measures a score; it never writes one.

WHAT IT READS

  a Standard MIDI File (track names become the voices), or
  a project score recipe (assets/audio/<cue>/score_*.yaml), resolved to per-voice notes by
  tools/arrange.py, so the checker and the renderer read the same notes.

Voices are split by name: pulse 1, pulse 2, triangle, the VRC6 parts, plus any extra pitched part.
A part whose name is not a known chip voice is kept as an extra part rather than dropped, so a
two-part Bach invention or a four-part chorale reads as two or four voices. A note list, a part that
is a chord at one instant (the pad) collapses to its top note: counterpoint is about lines, and the
line of a chord is its top.

HOW A DISSONANCE IS JUDGED

The one rule that decides whether a clash is a mistake or a device: it has to be prepared and
resolved, or it has to be a stepwise nonchord tone. Each dissonance is judged ONCE, at the instant
it first sounds, and both of its notes are asked to explain it, because the voice that moves creates
the clash while the voice that holds is the one a suspension is about. Each note is put into one of
these states, and only a state that fails its own test becomes a finding:

  suspension    the note was already sounding and was CONSONANT when it began, sits as a dissonance
                now, and leaves DOWN BY STEP. The figure above the bass is named: 4-3, 7-6, 9-8,
                2-3 when the bass is the suspended voice, in compound form too (11-10, 14-13). An
                unusual figure is a style note, not a fault, because the preparation and the
                resolution are what the ear needs.
  pedal         the note was already sounding AND it is the bass. A held bass note is not asked to
                resolve: the voices moving against it carry the finding. Without this, every pedal
                note read as a suspension the bass had failed to resolve.
  held          the note was already sounding and was ALREADY dissonant when it began. That clash
                was judged at its own attack, so this instant adds nothing; it is not a pass.
  appoggiatura  attacked on an accented beat, leaves by step. Allowed in the free profile, a soft
                fault in strict species.
  passing       attacked on a weak beat or offbeat, entered by step, left by step the same way.
  neighbour     attacked on a weak beat or offbeat, entered by step, left by step back to where it
                came from.
  escape        attacked, entered by step, left by leap. A real device, recorded as a style note
                because in this style it is worth knowing where the line jumps out of a step.
  otherwise     unprepared, unresolved, or both, which is the class that reads as a wrong note. It
                is a hard finding on an accented beat and a hard finding on a weak beat.

Parallel and hidden perfect intervals are judged between the OUTER voices only, as the card says:
inside a six voice chip texture the inner parts double each other on purpose, and a rule that
counts those measures the arrangement, not the counterpoint.

Two chord assumptions are explicit because there are no chord symbols in a MIDI file:

  a perfect fourth is consonant when it is not above the bass, and when it is above the bass it is
  consonant only if another voice puts a third or a sixth above that bass note (the 6/4 case);
  a seventh above the bass is read as a chordal seventh, which is legal when it resolves down by
  step, and is checked by CP-12 instead of being counted as a raw clash.

PROFILES

  free      free Baroque practice, calibrated on Bach (tools/counterpoint/calibration.json).
  strict    species counterpoint (Fux): appoggiaturas, hidden perfect intervals, voice crossing and
            wide spacing are faults rather than style notes.

Every finding carries a rule id, a severity, a bar, a beat, the voices and the notes, so a reader can
open the bar in the MIDI file and see the two notes the engine is naming. Severity is a property of
the (rule, profile) pair, and the tables are in RULES so a reader can see them without running it.

Usage:
    from rules import load_score, analyse
    result = analyse(load_score("assets/audio/pp_01_title_v7/pp_01_title_v7.mid"), profile="free")
"""

from __future__ import annotations

import bisect
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import hook_score  # noqa: E402

PROFILES = ("free", "strict")
PROFILE_ALIASES = {"free": "free", "baroque": "free", "gothic": "free", "hod": "free",
                   "strict": "strict", "species": "strict", "fux": "strict"}

# ---------------------------------------------------------------- pitch basics

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
KEY_NAMES = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")
LETTERS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
INTERVALS = {0: "P1", 1: "m2", 2: "M2", 3: "m3", 4: "M3", 5: "P4", 6: "TT",
             7: "P5", 8: "m6", 9: "M6", 10: "m7", 11: "M7"}

# Consonance model, stated once and used by every rule.
CONSONANT = frozenset((0, 3, 4, 7, 8, 9))
PERFECT = frozenset((0, 7))
DISSONANT = frozenset((1, 2, 5, 6, 10, 11))

# Species practice calls a diminished fifth and an augmented fourth dissonant even inside a triad.
# The free profile does not, because a diminished triad is a chord and not a clash.

MAJOR_SCALE = (0, 2, 4, 5, 7, 9, 11)
MINOR_SCALE = (0, 2, 3, 5, 7, 8, 10)
MODE_SCALES = {"major": MAJOR_SCALE, "minor": MINOR_SCALE}
KEY_ALIASES = {"": "major", "maj": "major", "major": "major",
               "min": "minor", "m": "minor", "minor": "minor"}

# The declared register of every NES voice, taken from tools/arrange.py's two tables
# (VOICE_RANGES and V3_VOICE_RANGES) and widened to their union so the checker does not fault a
# note the renderer accepts in another section. An unnamed part (a Bach invention, a chorale staff)
# gets the whole chip span instead.
NES_RANGES = {
    "vrc6 pulse a": (55, 96),
    "vrc6 pulse b": (45, 84),
    "vrc6 saw": (43, 67),
    "pulse 1": (55, 83),
    "pulse 2": (43, 96),
    "triangle": (36, 55),
}
DEFAULT_RANGE = (33, 96)   # A1 to C7: the span a 2A03 pulse timer reaches at 1789773 Hz

# Names the project uses, normalised so "pulse1", "Pulse 1" and "pulse 1" are one voice.
VOICE_ALIASES = {
    "pulse1": "pulse 1", "pulse 1": "pulse 1", "pulse_1": "pulse 1", "p1": "pulse 1",
    "pulse2": "pulse 2", "pulse 2": "pulse 2", "pulse_2": "pulse 2", "p2": "pulse 2",
    "tri": "triangle", "triangle": "triangle", "tri.": "triangle",
    "vrc6pulsea": "vrc6 pulse a", "vrc6 pulse a": "vrc6 pulse a", "vrc6_pulse_a": "vrc6 pulse a",
    "vrc6pulseb": "vrc6 pulse b", "vrc6 pulse b": "vrc6 pulse b", "vrc6_pulse_b": "vrc6 pulse b",
    "vrc6saw": "vrc6 saw", "vrc6 saw": "vrc6 saw", "vrc6_saw": "vrc6 saw",
}
UNPITCHED = frozenset(("noise", "dpcm", "control track", "meta", "conductor"))

# The rules, with the severity each one carries in each profile. A rule is a stable id so a report,
# a ledger row or a gate can name it without quoting prose.
RULES = {
    "CP-01": {"title": "dissonance on an accented beat, unprepared or unresolved",
              "severity": {"free": "hard", "strict": "hard"}},
    "CP-02": {"title": "dissonance on a weak beat that is not a passing or neighbour tone",
              "severity": {"free": "hard", "strict": "hard"}},
    "CP-04": {"title": "suspension not resolved down by step",
              "severity": {"free": "hard", "strict": "hard"}},
    "CP-05": {"title": "suspension figure outside 4-3, 7-6, 9-8, 2-3",
              "severity": {"free": "style", "strict": "style"}},
    "CP-06": {"title": "appoggiatura",
              "severity": {"free": "style", "strict": "soft"}},
    "CP-07": {"title": "passing tone entered or left by leap",
              "severity": {"free": "hard", "strict": "hard"}},
    "CP-08": {"title": "neighbour tone that does not return",
              "severity": {"free": "soft", "strict": "hard"}},
    "CP-09": {"title": "parallel perfect fifth or octave",
              "severity": {"free": "hard", "strict": "hard"}},
    "CP-10": {"title": "hidden (direct) perfect fifth or octave",
              "severity": {"free": "soft", "strict": "hard"}},
    "CP-11": {"title": "leading tone not resolved up to the tonic",
              "severity": {"free": "soft", "strict": "hard"}},
    "CP-12": {"title": "chordal seventh not resolved down by step",
              "severity": {"free": "soft", "strict": "hard"}},
    "CP-13": {"title": "voice crossing",
              "severity": {"free": "soft", "strict": "hard"}},
    "CP-14": {"title": "voice overlap",
              "severity": {"free": "soft", "strict": "soft"}},
    "CP-15": {"title": "spacing wider than an octave between upper voices",
              "severity": {"free": "soft", "strict": "hard"}},
    "CP-16": {"title": "two leaps in the same direction (an unshaped line)",
              "severity": {"free": "style", "strict": "soft"}},
    "CP-17": {"title": "note outside the voice's NES range",
              "severity": {"free": "hard", "strict": "hard"}},
    "CP-18": {"title": "escape tone (a stepwise dissonance left by leap)",
              "severity": {"free": "style", "strict": "style"}},
}
SEVERITY_ORDER = {"hard": 0, "soft": 1, "style": 2}
DEVICES = ("suspension", "appoggiatura", "passing", "neighbour", "escape")
# Devices that explain a dissonance outright. An appoggiatura explains one too, but always leaves a
# style note, which is why it is not in this set: "appoggiaturas sparingly" is a rule with a count.
EXPLAINING = frozenset(("suspension", "passing", "neighbour", "escape"))
# The two rules that record a device as a style note rather than a fault: an unusual suspension
# figure, and an escape tone. Everything else in RULES is either a device that passes silently or a
# fault, and the difference is what makes the report readable.
STYLE_DEVICE_RULES = frozenset(("CP-05", "CP-18"))

TOLERANCE_DIVISIONS = 16   # a sixteenth of a beat, the tolerance clash.py uses for the same score
MERGE_DIVISIONS = 8        # onsets closer than this are one instant


def pitch_name(value):
    """A MIDI number as a name, 'C4' for 60."""
    return "%s%d" % (NOTE_NAMES[value % 12], value // 12 - 1)


def parse_pitch(text):
    """'Bb5', 'F#4' or 'r' back to a MIDI number; a rest returns None."""
    text = str(text).strip()
    if text.lower() in ("r", "rest", "-"):
        return None
    letter = text[0].upper()
    if letter not in LETTERS:
        raise ValueError("cannot read the pitch %r" % text)
    pitch = LETTERS[letter]
    index = 1
    while index < len(text) and text[index] in "#b":
        pitch += 1 if text[index] == "#" else -1
        index += 1
    octave = int(text[index:])
    return pitch + 12 * (octave + 1)


def interval_class(low, high):
    """The interval class of two pitches, 0 to 11."""
    return (high - low) % 12


def interval_name(low, high):
    """The name of the interval between two pitches, compound intervals included."""
    return INTERVALS[(high - low) % 12] if high - low < 12 else \
        "%s (+%d)" % (INTERVALS[(high - low) % 12], (high - low) // 12)


def parse_key(text):
    """'A minor' or 'C major' as (tonic pitch class, mode). None reads as C major."""
    if text is None:
        return 0, "major"
    parts = str(text).replace("_", " ").split()
    tonic_text = parts[0]
    tonic = parse_pitch(tonic_text + "4") % 12
    mode = KEY_ALIASES.get(" ".join(parts[1:]).lower(), "major")
    return tonic, mode


def scale_of(key):
    """The pitch classes of a key, as a set."""
    tonic, mode = key
    return {(tonic + step) % 12 for step in MODE_SCALES[mode]}


def detect_key(histogram):
    """The key whose scale best explains the note durations.

    histogram maps pitch class to total duration. Each candidate key scores the duration it explains
    minus twice the duration it does not, plus a bonus for the tonic and the fifth, which are the two
    pitch classes a tonal piece repeats most. A tie goes to the key with the louder tonic triad.
    Kept deliberately simple and printed in the report, so a reader can disagree with it by name.
    """
    best = None
    total = sum(histogram.values()) or 1
    for tonic in range(12):
        for mode in ("major", "minor"):
            scale = scale_of((tonic, mode))
            inside = sum(d for pc, d in histogram.items() if pc in scale)
            outside = total - inside
            score = inside - 2.0 * outside
            score += 0.5 * histogram.get(tonic, 0) + 0.25 * histogram.get((tonic + 7) % 12, 0)
            if (tonic, mode) == (0, "major"):
                score -= 1e-6   # C major loses a tie, so silence does not read as a key
            if best is None or score > best[0]:
                best = (score, tonic, mode)
    return best[1], best[2]


def key_name(key):
    """(9, 'minor') as 'A minor', with the flat spelling for the black keys.

    D# major and A# major are how the pitch classes spell themselves, but the corpus is tonal music
    where those keys are written Eb and Bb, and a report that calls BWV 776 D# major is wrong in the
    one place a musician reads first.
    """
    return "%s %s" % (KEY_NAMES[key[0]], key[1])


# ---------------------------------------------------------------- the score model

class Note(object):
    """One note: where it starts, where it ends, its pitch and its velocity, in ticks."""

    __slots__ = ("start", "end", "pitch", "velocity")

    def __init__(self, start, end, pitch, velocity=100):
        self.start = int(start)
        self.end = int(end)
        self.pitch = int(pitch)
        self.velocity = int(velocity)

    @property
    def length(self):
        return self.end - self.start

    def __repr__(self):
        return "Note(%d, %d, %s)" % (self.start, self.end, pitch_name(self.pitch))


class Part(object):
    """One voice, as a monophonic line.

    A part that sounds more than one pitch at an onset (the pad) is collapsed to the top note of
    that onset, and the count is kept, so the report can say how much of the part was a chord. The
    line is what the counterpoint rules read: a chord has no single melodic position.
    """

    def __init__(self, name, notes, tolerance):
        self.name = name
        self.tolerance = tolerance
        self.notes = sorted((n for n in notes if n.length > 0), key=lambda n: (n.start, n.pitch))
        self.chord_slots = 0
        self.line = self._collapse()
        self.starts = [n.start for n in self.line]
        self.span = max((n.length for n in self.line), default=0)
        pitches = [n.pitch for n in self.line]
        self.low = min(pitches) if pitches else None
        self.high = max(pitches) if pitches else None
        self.mean = (sum(pitches) / float(len(pitches))) if pitches else None

    def __len__(self):
        return len(self.line)

    def _collapse(self):
        merged = []
        group = []
        for note in self.notes:
            if group and note.start - group[0].start < self.tolerance:
                group.append(note)
                continue
            if group:
                merged.append(self._merge(group))
            group = [note]
        if group:
            merged.append(self._merge(group))
        return merged

    def _merge(self, group):
        if len(group) > 1:
            self.chord_slots += 1
        top = max(group, key=lambda n: n.pitch)
        end = max(n.end for n in group)
        return Note(group[0].start, end, top.pitch, top.velocity)

    def at(self, tick):
        """The line note sounding at the tick, or None."""
        index = bisect.bisect_right(self.starts, tick + self.tolerance) - 1
        floor = tick - self.span - self.tolerance
        while index >= 0:
            note = self.line[index]
            if note.start <= tick + self.tolerance and note.end > tick:
                return note
            if note.start < floor:
                break
            index -= 1
        return None

    def attacked(self, tick):
        """The line note that begins at the tick, or None."""
        index = bisect.bisect_left(self.starts, tick - self.tolerance)
        if index < len(self.line) and self.line[index].start <= tick + self.tolerance:
            return self.line[index]
        return None

    def previous_before(self, tick):
        """The line note that ended most recently before the tick."""
        index = bisect.bisect_left(self.starts, tick - self.tolerance) - 1
        return self.line[index] if index >= 0 else None

    def next_after(self, tick):
        """The line note that begins at or after the tick."""
        index = bisect.bisect_left(self.starts, tick - self.tolerance)
        return self.line[index] if index < len(self.line) else None

    def resolutions(self, note):
        """The next line note this note can resolve to: the first one that starts after it."""
        index = bisect.bisect_right(self.starts, note.start + self.tolerance)
        return self.line[index] if index < len(self.line) else None


class Score(object):
    """A score with its voices, its metre, its key and the lookups every rule needs."""

    def __init__(self, parts, division=480, time_sig=(4, 4), tempo_us=500000, key=None,
                 path=None, key_declared=False):
        self.path = path
        self.division = int(division)
        self.time_sig = (int(time_sig[0]), int(time_sig[1]))
        self.tempo_us = int(tempo_us or 500000)
        beats, unit = self.time_sig
        self.ticks_per_beat = max(1, self.division * 4 // unit)
        self.bar_ticks = self.ticks_per_beat * beats
        self.tolerance = max(1, self.ticks_per_beat // TOLERANCE_DIVISIONS)
        self.merge = max(1, self.ticks_per_beat // MERGE_DIVISIONS)
        self.parts = {}
        for name, notes in parts.items():
            part = Part(name, notes, self.tolerance)
            if part.line:
                self.parts[name] = part
        self.notes_total = sum(len(part.line) for part in self.parts.values())
        self.bars = 1
        for part in self.parts.values():
            self.bars = max(self.bars, 1 + part.line[-1].start // self.bar_ticks)
        histogram = {}
        for part in self.parts.values():
            for note in part.line:
                histogram[note.pitch % 12] = histogram.get(note.pitch % 12, 0) + note.length
        self.key_detected = detect_key(histogram)
        self.key_declared = key_declared
        self.key = key if key is not None else self.key_detected

    # -- construction ---------------------------------------------------------------------

    @classmethod
    def from_smf(cls, path, key=None):
        """Read a Standard MIDI File; track names become voice names."""
        song = hook_score.read_smf(path)
        parts = {}
        for track in song["tracks"]:
            name = normalise_voice(track["name"])
            if name in UNPITCHED or not track["notes"]:
                continue
            while name in parts:   # two tracks with the same name are two parts, not one
                name += " 2"
            notes = [Note(start, end, pitch, velocity)
                     for start, end, pitch, velocity in track["notes"]]
            parts[name] = notes
        return cls(parts, song["division"], song["time_sig"] or (4, 4), song["tempo_us"],
                   key=key, path=path, key_declared=key is not None)

    @classmethod
    def from_notes(cls, notes_by_voice, division=480, time_sig=(4, 4), tempo_us=500000,
                   key=None, path=None):
        """Build a score from note lists, which is how the unit tests state a textbook case."""
        parts = {}
        for name, notes in notes_by_voice.items():
            parts[name] = [n if isinstance(n, Note) else Note(*n) for n in notes]
        return cls(parts, division, time_sig, tempo_us, key=key, path=path,
                   key_declared=key is not None)

    @classmethod
    def from_recipe(cls, path, key=None):
        """Read a project score recipe through tools/arrange.py, which is what the renderer reads.

        The score file holds the melody and a chord plan; arrange.py turns those into the eight voice
        lines. Reading the same function means the checker cannot disagree with the renderer about
        which note is in which voice.
        """
        import arrange

        score = arrange.load_score(path)
        meta = score.get("meta") or {}
        version_3 = isinstance(score.get("sections"), dict)
        profile = meta.get("profile")
        if version_3 and profile == "percy":
            arrangement = arrange.build_arrangement_percy(score)
        elif version_3 and profile == "hadrian":
            arrangement = arrange.build_arrangement_hadrian(score)
        elif version_3:
            arrangement = arrange.build_arrangement_v3(score)
        else:
            arrangement = arrange.build_arrangement(score)
        parts = {}
        for name in arrange.TRACK_NAMES:
            if name in UNPITCHED:
                continue
            parts[name] = [Note(start, start + length, pitch, velocity)
                           for start, length, pitch, velocity in arrangement.notes[name]]
        time_sig = parse_time_signature(str(meta.get("time") or "4/4"))
        declared = key if key is not None else meta.get("key")
        tonic = parse_key(declared) if declared else None
        # ticks_per_bar is (beats * ticks_per_beat), so the division follows from the metre.
        division = arrangement.ticks_per_bar * time_sig[1] // (4 * time_sig[0])
        return cls(parts, division, time_sig,
                   int(60_000_000 / float(meta.get("bpm") or 120)),
                   key=tonic, path=path, key_declared=declared is not None)

    # -- time -----------------------------------------------------------------------------

    def bar_beat(self, tick):
        """(bar, beat) with the bar counted from 1 and the beat as a float from 1."""
        return tick // self.bar_ticks + 1, 1.0 + (tick % self.bar_ticks) / float(self.ticks_per_beat)

    def accent(self, tick):
        """The metric weight of a tick: strong, medium, weak or offbeat."""
        position = (tick % self.bar_ticks) / float(self.ticks_per_beat)
        beats = self.time_sig[0]
        if abs(position - round(position)) > 0.02:
            return "offbeat"
        beat = int(round(position))
        strong, medium = accent_positions(beats)
        if beat in strong:
            return "strong"
        if beat in medium:
            return "medium"
        return "weak"

    def instants(self):
        """Every tick where at least one voice attacks a line note, merged to the score's grid."""
        ticks = []
        for part in self.parts.values():
            ticks.extend(part.starts)
        ticks.sort()
        merged = []
        for tick in ticks:
            if merged and tick - merged[-1] < self.merge:
                continue
            merged.append(tick)
        return merged

    def sounding(self, tick):
        """{voice: line note} for every voice sounding at the tick."""
        out = {}
        for name, part in self.parts.items():
            note = part.at(tick)
            if note is not None:
                out[name] = note
        return out

    def bass_at(self, sounding):
        """The lowest sounding pitch, which the chord assumptions measure from."""
        return min(note.pitch for note in sounding.values()) if sounding else None

    def rank(self):
        """The voice names ordered from the top line down, by mean pitch."""
        return sorted(self.parts, key=lambda name: -self.parts[name].mean)

    def outer(self):
        """The two outer voices, (top, bottom)."""
        order = self.rank()
        return (order[0], order[-1]) if len(order) >= 2 else (order[0] if order else None, None)

    def range_of(self, name):
        """The declared range of a voice: the chip table for a chip voice, the chip span otherwise."""
        return NES_RANGES.get(name, DEFAULT_RANGE)


def accent_positions(beats):
    """Which beats are strong and which are medium, for a bar of this many beats."""
    if beats and beats % 3 == 0 and beats > 3:
        return {0}, {beats // 3, 2 * beats // 3}
    if beats == 4:
        return {0}, {2}
    if beats == 2:
        return {0}, set()
    return {0}, set()


def simple_number(number):
    """A compound interval number reduced to its simple form: 9 is a 2nd, 10 a 3rd, 12 a 5th.

    The figure is printed with the real numbers, because 9-8 says more than 2-8 does. This reduction
    is only for recognising the textbook set, so that 9-8, 2-8 and 16-15 are the same rule.
    """
    while number > 8:
        number -= 7
    return number


CANONICAL_FIGURES = frozenset(("4-3", "7-6", "2-8", "2-3"))


def figure_is_canonical(figure):
    """Is this suspension figure one of the four the card names, in simple or compound form?

    4-3 and 7-6 are the two the textbooks give first, 9-8 is the compound form of 2-8, and the bass
    suspension is 2-3 (a ninth to a tenth, or a second to a third). Anything else is a style note.
    """
    if not figure or "-" not in figure:
        return True   # an unnamed figure is not evidence of an unusual one
    before, after = figure.split("-")
    try:
        pair = "%d-%d" % (simple_number(int(before)), simple_number(int(after)))
    except ValueError:
        return True
    return pair in CANONICAL_FIGURES


def six_four_supported(sounding, bass_pitch):
    """Is a fourth above the bass part of a 6/4 chord, because a third or sixth sits above it."""
    for note in sounding.values():
        if note.pitch <= bass_pitch:
            continue
        if interval_class(bass_pitch, note.pitch) in (3, 4, 8, 9):
            return True
    return False


def interval_number(semitones):
    """The interval number of a distance: 5 semitones is a 4th, 14 is a 9th, 12 is an 8ve."""
    table = {0: 1, 1: 2, 2: 2, 3: 3, 4: 3, 5: 4, 6: 5, 7: 5, 8: 6, 9: 6,
             10: 7, 11: 7, 12: 8, 13: 9, 14: 9, 15: 10, 16: 10, 17: 11, 18: 11,
             19: 12, 20: 13, 21: 13, 22: 14, 23: 14}
    if semitones in table:
        return table[semitones]
    octaves, rest = divmod(semitones, 12)
    return table.get(rest, 2) + 7 * octaves


def normalise_voice(name):
    """A track name as the voice name the rules and the chip tables use."""
    text = " ".join(str(name or "").strip().lower().split())
    return VOICE_ALIASES.get(text, text)


def parse_time_signature(text):
    """'3/4' as (3, 4)."""
    parts = str(text).split("/")
    if len(parts) != 2:
        return 4, 4
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return 4, 4


def load_score(path, key=None):
    """Read a MIDI file or a project score recipe, by extension."""
    extension = os.path.splitext(str(path))[1].lower()
    if extension in (".mid", ".midi", ".smf"):
        return Score.from_smf(path, key=key)
    if extension in (".yaml", ".yml"):
        return Score.from_recipe(path, key=key)
    raise ValueError("cannot read %s: expected a .mid, .midi or score .yaml" % path)


# ---------------------------------------------------------------- the checker

class Checker(object):
    """Runs every rule over one score and returns findings with their evidence."""

    def __init__(self, score, profile="free"):
        self.score = score
        self.profile = PROFILE_ALIASES.get(str(profile).lower(), "free")
        self.findings = []
        self.seventh_seen = set()
        self.pair_seen = set()
        self.reported = set()
        self.devices = {name: 0 for name in DEVICES}
        self.judged = {"dissonances": 0, "accented": 0, "unaccented": 0, "prepared": 0,
                       "unprepared": 0, "resolved": 0}

    # -- reporting ------------------------------------------------------------------------

    def severity(self, rule, name=None):
        """The severity a rule carries in this profile."""
        table = RULES[rule]["severity"]
        return table[self.profile]

    def add(self, rule, tick, voices, detail, evidence=None, severity=None):
        """Record one finding."""
        bar, beat = self.score.bar_beat(tick)
        self.findings.append({
            "rule": rule,
            "title": RULES[rule]["title"],
            "severity": severity or self.severity(rule),
            "bar": bar, "beat": round(beat, 3), "tick": tick,
            "voices": list(voices),
            "detail": detail,
            "evidence": evidence or {},
        })

    # -- run ------------------------------------------------------------------------------

    def run(self):
        """Every rule, in the order that reads best: vertical first, then the lines."""
        instants = self.score.instants()
        self.check_vertical(instants)
        self.check_motion(instants)
        for name in self.score.parts:
            self.check_leading_tone(name)
            self.check_leaps(name)
            self.check_range(name)
        self.check_spacing_and_crossing(instants)
        self.findings.sort(key=lambda f: (f["tick"], SEVERITY_ORDER[f["severity"]], f["rule"]))
        return self.findings

    # -- the vertical rules ---------------------------------------------------------------

    def check_vertical(self, instants):
        """Consonance, and every dissonance either explained by a device or recorded as a finding."""
        for tick in instants:
            sounding = self.score.sounding(tick)
            if len(sounding) < 2:
                continue
            bass = self.score.bass_at(sounding)
            self.check_sevenths(sounding, bass, tick)
            for pair in self.dissonant_pairs(sounding, bass, tick):
                key = (pair["low_voice"], sounding[pair["low_voice"]].start,
                       pair["high_voice"], sounding[pair["high_voice"]].start)
                if key in self.pair_seen:
                    continue
                self.pair_seen.add(key)
                self.judge_pair(tick, pair, sounding, bass)

    def attacked_at(self, note, tick):
        """Was this note attacked at the tick, or carried over."""
        return abs(note.start - tick) <= self.score.tolerance

    def dissonant_pairs(self, sounding, bass, tick):
        """Every pair of sounding voices whose interval is dissonant under the chord assumptions."""
        names = sorted(sounding)
        out = []
        for index, name_a in enumerate(names):
            for name_b in names[index + 1:]:
                note_a, note_b = sounding[name_a], sounding[name_b]
                low, high = (note_a, note_b) if note_a.pitch <= note_b.pitch else (note_b, note_a)
                ic = interval_class(low.pitch, high.pitch)
                if not self.is_dissonant(sounding, low, high):
                    continue
                out.append({"low_voice": name_a if low is note_a else name_b,
                            "high_voice": name_b if low is note_a else name_a,
                            "low": low.pitch, "high": high.pitch, "ic": ic,
                            "note_start": max(note_a.start, note_b.start),
                            "notes": (note_a, note_b)})
        return out

    def is_dissonant(self, sounding, low_note, high_note):
        """The chord assumptions of the module docstring, in one place.

        Consonance is judged on the interval class, so a compound interval behaves like its simple
        form. The two chord exceptions need the real distance: only a SIMPLE fourth above the bass
        takes part in the 6/4 test, and only a real seventh (10 or 11 semitones above the bass) is a
        chordal seventh. A ninth above the bass is a ninth and is judged as a dissonance.
        """
        raw = high_note.pitch - low_note.pitch
        ic = raw % 12
        above_bass = low_note.pitch == min(n.pitch for n in sounding.values())
        if ic in CONSONANT:
            return False
        if ic == 5:
            if not above_bass or raw != 5:
                return False
            return not six_four_supported(sounding, low_note.pitch)
        if raw in (10, 11) and above_bass:
            return False   # a chordal seventh, which CP-12 judges
        return True

    def judge_pair(self, tick, pair, sounding, bass):
        """One dissonance: explained when either note is a device, otherwise recorded once.

        Judging both notes is what makes a suspension work: the dissonance is created by the voice
        that MOVES, but the note that has to resolve is the one that HELD. The old single-subject
        reading always named the moving voice and so never found a suspension at all.
        """
        low_voice, high_voice = pair["low_voice"], pair["high_voice"]
        results = [self.device_for(tick, low_voice, sounding[low_voice], sounding, bass),
                   self.device_for(tick, high_voice, sounding[high_voice], sounding, bass)]
        accent = self.score.accent(tick)
        self.judged["dissonances"] += 1
        self.judged["accented" if accent in ("strong", "medium") else "unaccented"] += 1
        if any(result["held"] for result in results):
            self.judged["prepared"] += 1
        else:
            self.judged["unprepared"] += 1
        if any(result["following"] is not None for result in results):
            self.judged["resolved"] += 1

        wanted = [r for r in results if r["device"] in EXPLAINING and not r["rule"]]
        if wanted:
            for result in wanted:
                self.devices[result["device"]] = self.devices.get(result["device"], 0) + 1
            return
        styled = [r for r in results if r["rule"] in STYLE_DEVICE_RULES]
        if styled:
            for result in styled:
                self.devices[result["device"]] = self.devices.get(result["device"], 0) + 1
            self.report(styled[0], tick, pair, sounding)
            return
        appoggiatura = [r for r in results if r["device"] == "appoggiatura"]
        if appoggiatura:
            for result in appoggiatura:
                self.devices["appoggiatura"] += 1
            self.report(appoggiatura[0], tick, pair, sounding)
            return
        findings = [r for r in results if r["rule"]]
        if not findings:
            return
        suspended = [r for r in findings if r["rule"] == "CP-04"]
        if suspended:
            chosen = suspended[0]
            other = [r for r in results if r is not chosen][0]
            chosen["detail"] += "; the other voice's %s %s" % (
                pitch_name(other["note"].pitch),
                "is a %s" % other["device"] if other["device"] else
                ("fails to explain it (%s)" % other["rule"] if other["rule"] else "is held"))
            self.report(chosen, tick, pair, sounding, partner=other)
            return
        attacked = [r for r in findings if r["attacked"]]
        if len(attacked) > 1:
            # Two fresh notes clash: the upper one is the convention for the note that must give
            # way, and it is also the one the ear hears as the dissonance.
            attacked.sort(key=lambda r: -r["note"].pitch)
        self.report((attacked or findings)[0], tick, pair, sounding)

    def device_for(self, tick, name, note, sounding, bass):
        """What one note of a dissonant pair is doing: a device, a device with a style note, or none."""
        part = self.score.parts[name]
        previous = part.previous_before(note.start)
        following = part.resolutions(note)
        step_in = (note.pitch - previous.pitch) if previous is not None else None
        step_out = (following.pitch - note.pitch) if following is not None else None
        accent = self.score.accent(tick)
        held = not self.attacked_at(note, tick)
        result = {"voice": name, "note": note, "held": held, "attacked": not held,
                  "device": None, "rule": None, "detail": "", "severity": None,
                  "step_in": step_in, "step_out": step_out, "accent": accent,
                  "following": following, "figure": None, "prepared": None}
        other = ", ".join(sorted(other_name for other_name in sounding if other_name != name))

        if held:
            result["prepared"] = self.was_consonant(name, note, self.score.sounding(note.start))
            if note.pitch == bass:
                # A held bass note is a pedal. The dissonances against it belong to the voices that
                # move, which is how a pedal point is written and how Bach writes it: the bass is
                # not asked to resolve anywhere.
                result["device"] = "pedal"
                return result
            if not result["prepared"]:
                # A held note that was dissonant when it began owes nothing separately: that
                # dissonance was judged, and reported, at the note's own attack. Nothing here says
                # the note is fine; it says this instant is not a new dissonance.
                result["device"] = "held"
                return result
            result["figure"] = self.suspension_figure(name, note, following, sounding, bass)
            if step_out is not None and step_out in (-2, -1):
                result["device"] = "suspension"
                if result["figure"] and not figure_is_canonical(result["figure"]):
                    result.update(rule="CP-05",
                                  detail="prepared %s resolves down by step, figure %s"
                                         % (pitch_name(note.pitch), result["figure"]))
                return result
            result.update(device="suspension", rule="CP-04",
                          detail="prepared %s does not resolve down by step (%s)"
                                 % (pitch_name(note.pitch),
                                    "no resolution" if following is None
                                    else "to %s" % pitch_name(following.pitch)))
            return result

        stepwise_in = step_in is not None and abs(step_in) in (1, 2)
        stepwise_out = following is not None and abs(step_out) in (1, 2)
        repeated = following is not None and step_out == 0
        if accent in ("strong", "medium"):
            if stepwise_out:
                result.update(device="appoggiatura", rule="CP-06",
                              detail="accented %s enters freely and resolves to %s by step"
                                     % (pitch_name(note.pitch), pitch_name(following.pitch)))
                return result
            result.update(rule="CP-01",
                          detail="%s is dissonant against %s on a %s beat and %s"
                                 % (pitch_name(note.pitch), other, accent,
                                    "has no resolution" if following is None else
                                    "leaves to %s, not by step" % pitch_name(following.pitch)))
            return result

        if stepwise_in and stepwise_out:
            if step_in * step_out > 0:
                result["device"] = "passing"
                return result
            if following.pitch == previous.pitch:
                result["device"] = "neighbour"
                return result
            result.update(rule="CP-08",
                          detail="stepwise %s leaves to %s instead of back to %s"
                                 % (pitch_name(note.pitch), pitch_name(following.pitch),
                                    pitch_name(previous.pitch)))
            return result
        if stepwise_in and following is not None and abs(step_out) > 2:
            result.update(device="escape", rule="CP-18",
                          detail="stepwise %s leaves by leap to %s"
                                 % (pitch_name(note.pitch), pitch_name(following.pitch)))
            return result
        if step_in is not None and abs(step_in) > 2 and stepwise_out:
            result.update(device="appoggiatura", rule="CP-06",
                          detail="unaccented %s enters by leap from %s and resolves to %s by step"
                                 % (pitch_name(note.pitch), pitch_name(previous.pitch),
                                    pitch_name(following.pitch)))
            return result
        if repeated:
            result.update(rule="CP-02",
                          detail="weak-beat dissonance %s is repeated rather than resolved"
                                 % pitch_name(note.pitch))
            return result
        if step_in is not None and abs(step_in) > 2:
            result.update(rule="CP-07",
                          detail="weak-beat dissonance %s enters by leap from %s and %s"
                                 % (pitch_name(note.pitch), pitch_name(previous.pitch),
                                    "has no resolution" if following is None else
                                    "leaves to %s, not by step" % pitch_name(following.pitch)))
            return result
        result.update(rule="CP-02",
                      detail="weak-beat dissonance %s is neither passing nor neighbour (%s)"
                             % (pitch_name(note.pitch), "unresolved" if following is None else
                                "leaves to %s" % pitch_name(following.pitch)))
        return result

    def report(self, result, tick, pair, sounding, partner=None):
        """Record one finding, once per rule, voice and note."""
        note = result["note"]
        key = (result["rule"], result["voice"], note.start)
        if key in self.reported:
            return
        self.reported.add(key)
        evidence = {
            "low": pitch_name(pair["low"]), "high": pitch_name(pair["high"]),
            "interval": INTERVALS[pair["ic"]],
            "pair": "%s + %s" % (pair["low_voice"], pair["high_voice"]),
            "note": pitch_name(note.pitch), "voice": result["voice"],
            "accent": result["accent"], "prepared": result["prepared"],
            "resolves": None if result["following"] is None
            else pitch_name(result["following"].pitch),
            "step_in": result["step_in"], "step_out": result["step_out"],
        }
        if result["figure"]:
            evidence["figure"] = result["figure"]
        if partner is not None:
            evidence["partner"] = {
                "voice": partner["voice"], "note": pitch_name(partner["note"].pitch),
                "device": partner["device"], "rule": partner["rule"],
                "step_in": partner["step_in"], "step_out": partner["step_out"]}
        self.add(result["rule"], tick, [result["voice"]], result["detail"], evidence,
                 severity=result["severity"])

    def was_consonant(self, name, note, sounding):
        """Was this note, when it began, consonant against everything else sounding then.

        A note that began with nothing else sounding was not prepared by anything: the clash comes
        later, when another voice enters against it, and the entering voice is the one that has to
        explain itself. Reading silence as a consonance turned every pedal note into a suspension.
        """
        others = {other: n for other, n in sounding.items() if other != name}
        if not others:
            return False
        for other_note in others.values():
            low, high = sorted((note, other_note), key=lambda n: n.pitch)
            if self.is_dissonant(sounding, low, high):
                return False
        return True

    def suspension_figure(self, subject, note, following, sounding, bass):
        """The textbook name of the suspension: the interval number above the bass now, and after.

        A bass suspension reads 2-3: the bass holds, the second above it becomes a third when the
        bass steps down. An upper-voice suspension reads 4-3, 7-6 or 9-8 by the same measure. A held
        note that is not the bass keeps the name of the interval it makes with the bass. When the
        held note is the bass and the interval above it is not a second, the figure has no name and
        None is returned, rather than a number that reads as nonsense.
        """
        if bass is None or following is None:
            return None
        following_sounding = self.score.sounding(following.start)
        if note.pitch == bass:
            above = [n.pitch for other, n in following_sounding.items()
                     if other != subject and n.pitch > note.pitch]
            if not above:
                return None
            above = sorted(above)[0]
            before = interval_number(above - note.pitch)
            if before not in (2, 9):
                return None
            after = interval_number(above - following.pitch) if following.pitch < note.pitch \
                else interval_number(following.pitch - above)
            return "%d-%d" % (before, after)
        before = interval_number(note.pitch - bass)
        new_bass = min([n.pitch for n in following_sounding.values()] or [bass])
        if new_bass != bass:
            return None   # the figure is named against a held bass; if the bass moves it has no name
        after = interval_number(following.pitch - bass)
        return "%d-%d" % (before, after)

    def check_sevenths(self, sounding, bass, tick):
        """A seventh above the bass must resolve down by step (CP-12)."""
        if bass is None:
            return
        for name, note in sounding.items():
            key = (name, note.start)
            if key in self.seventh_seen:
                continue
            if note.pitch - bass not in (10, 11):
                continue
            following = self.score.parts[name].resolutions(note)
            if following is None:
                continue
            self.seventh_seen.add(key)
            step = following.pitch - note.pitch
            if step in (-2, -1):
                continue
            self.add("CP-12", tick, [name],
                     "the seventh %s over %s moves to %s instead of down by step"
                     % (pitch_name(note.pitch), pitch_name(bass), pitch_name(following.pitch)),
                     {"voice": name, "seventh": pitch_name(note.pitch), "bass": pitch_name(bass),
                      "to": pitch_name(following.pitch), "step": step})

    # -- the motion rules -----------------------------------------------------------------

    def check_motion(self, instants):
        """Parallel and hidden perfect intervals, between every pair and named for the outer two."""
        order = self.score.rank()
        if len(order) < 2:
            return
        outer = set(self.score.outer())
        for index in range(len(instants) - 1):
            tick_a, tick_b = instants[index], instants[index + 1]
            if tick_b - tick_a > self.score.bar_ticks:
                continue
            sounding_a = self.score.sounding(tick_a)
            sounding_b = self.score.sounding(tick_b)
            names = [n for n in order if n in sounding_a and n in sounding_b]
            for i, name_a in enumerate(names):
                for name_b in names[i + 1:]:
                    self.judge_motion(tick_a, tick_b, name_a, name_b, sounding_a, sounding_b,
                                      outer)

    def judge_motion(self, tick_a, tick_b, name_a, name_b, sounding_a, sounding_b, outer):
        """One voice pair, one pair of instants: parallel, hidden, or neither."""
        a1, a2 = sounding_a[name_a], sounding_b[name_a]
        b1, b2 = sounding_a[name_b], sounding_b[name_b]
        move_a = a2.pitch - a1.pitch
        move_b = b2.pitch - b1.pitch
        if move_a == 0 or move_b == 0:
            return
        ic1 = interval_class(min(a1.pitch, b1.pitch), max(a1.pitch, b1.pitch))
        ic2 = interval_class(min(a2.pitch, b2.pitch), max(a2.pitch, b2.pitch))
        same_direction = (move_a > 0) == (move_b > 0)
        evidence = {
            "pair": "%s + %s" % (name_a, name_b),
            "from": "%s + %s (%s)" % (pitch_name(a1.pitch), pitch_name(b1.pitch), INTERVALS[ic1]),
            "to": "%s + %s (%s)" % (pitch_name(a2.pitch), pitch_name(b2.pitch), INTERVALS[ic2]),
            "motion": "similar" if same_direction else "contrary",
            "outer": set((name_a, name_b)) == outer,
        }
        if same_direction and ic1 == ic2 and ic1 in PERFECT and a2.pitch != a1.pitch:
            if set((name_a, name_b)) != outer:
                return   # parallels are scoped to the outer voices, as the card says
            what = "fifth" if ic1 == 7 else "octave"
            self.add("CP-09", tick_b, [name_a, name_b],
                     "parallel %ss: %s moves %+d and %s moves %+d, between the outer voices"
                     % (what, name_a, move_a, name_b, move_b), evidence)
            return
        if same_direction and ic2 in PERFECT and ic1 != ic2 and set((name_a, name_b)) == outer:
            upper_move = (a2.pitch - a1.pitch) if a1.pitch > b1.pitch else (b2.pitch - b1.pitch)
            if abs(upper_move) > 2:
                what = "fifth" if ic2 == 7 else "octave"
                self.add("CP-10", tick_b, [name_a, name_b],
                         "hidden %s by similar motion between the outer voices, upper line leaps %+d"
                         % (what, upper_move), evidence)

    # -- the line rules -------------------------------------------------------------------

    def check_leading_tone(self, name):
        """The leading tone is left up to the tonic when it is the third of the dominant (CP-11).

        The rule as the textbooks state it is conditional: the leading tone must rise when it is the
        third of a dominant harmony in an outer voice. In a file with no chord symbols the test for
        that harmony is the bass: the leading tone resolves up when the dominant is in the bass. A
        leading tone anywhere else (a passing note in a descending line, for instance) owes nothing,
        and Bach leaves it downwards constantly, which is why the unconditional test measured ten
        violations per hundred notes on the inventions and meant nothing.
        """
        tonic, _mode = self.score.key
        dominant = (tonic + 7) % 12
        leading = (tonic - 1) % 12
        part = self.score.parts[name]
        outer = name in set(self.score.outer())
        for note in part.line:
            if note.pitch % 12 != leading:
                continue
            sounding = self.score.sounding(note.start)
            bass = self.score.bass_at(sounding)
            if bass is None or bass % 12 != dominant:
                continue
            following = part.resolutions(note)
            if following is None:
                continue
            step = following.pitch - note.pitch
            if step == 0:
                continue   # the note is repeated, so it has not been left yet
            if step == 1 and following.pitch % 12 == tonic:
                continue
            severity = self.severity("CP-11")
            if not outer and self.profile == "free":
                severity = "soft"
            self.add("CP-11", note.start, [name],
                     "the leading tone %s over the dominant leaves to %s (%+d), not up to %s"
                     % (pitch_name(note.pitch), pitch_name(following.pitch), step,
                        pitch_name(note.pitch + 1)),
                     {"voice": name, "leading": pitch_name(note.pitch), "bass": pitch_name(bass),
                      "to": pitch_name(following.pitch), "step": step, "outer": outer},
                     severity=severity)

    def check_leaps(self, name):
        """Two leaps in the same direction: the line has no shape (CP-16).

        Four candidate readings were measured on the corpus (tools/counterpoint/calibrate.py and the
        table in knowledge/COUNTERPOINT-CALIBRATION-2026-10-26.md): every leap not followed by a
        step fires 22.5 times per hundred notes on Bach, a sixth or larger 13.1, an octave 11.8, and
        this one, a leap larger than a fourth followed by another leap the same way, 3.4 at its
        worst and 0.7 on average. Only the last one distinguishes a shaped line from an unshaped
        one, so it is the rule.
        """
        part = self.score.parts[name]
        line = part.line
        for index, note in enumerate(line[:-2]):
            following = line[index + 1]
            leap = following.pitch - note.pitch
            if abs(leap) <= 5:
                continue
            second = line[index + 2].pitch - following.pitch
            if abs(second) <= 2 or (second > 0) != (leap > 0):
                continue
            self.add("CP-16", note.start, [name],
                     "a leap of %+d semitones from %s to %s is followed by another leap %+d the "
                     "same way, to %s"
                     % (leap, pitch_name(note.pitch), pitch_name(following.pitch), second,
                        pitch_name(line[index + 2].pitch)),
                     {"voice": name, "from": pitch_name(note.pitch),
                      "to": pitch_name(following.pitch), "leap": leap, "second": second})

    def check_range(self, name):
        """Every note inside the voice's declared NES range (CP-17)."""
        low, high = self.score.range_of(name)
        part = self.score.parts[name]
        for note in part.line:
            if low <= note.pitch <= high:
                continue
            self.add("CP-17", note.start, [name],
                     "%s is outside %s's range %s to %s"
                     % (pitch_name(note.pitch), name, pitch_name(low), pitch_name(high)),
                     {"voice": name, "pitch": pitch_name(note.pitch),
                      "range": [pitch_name(low), pitch_name(high)]})

    def check_spacing_and_crossing(self, instants):
        """Crossing (CP-13), overlap (CP-14) and spacing (CP-15) between adjacent voices."""
        order = self.score.rank()
        if len(order) < 2:
            return
        spaced = len(order) >= 3   # two voices have no spacing rule: any gap is a legal doubling
        reported = set()
        for tick in instants:
            sounding = self.score.sounding(tick)
            for index in range(len(order) - 1):
                upper_name, lower_name = order[index], order[index + 1]
                if upper_name not in sounding or lower_name not in sounding:
                    continue
                upper, lower = sounding[upper_name], sounding[lower_name]
                key = ("CP-13", upper_name, lower_name)
                if upper.pitch < lower.pitch and key not in reported:
                    reported.add(key)
                    self.add("CP-13", tick, [upper_name, lower_name],
                             "%s (%s) sounds below %s (%s)"
                             % (upper_name, pitch_name(upper.pitch), lower_name,
                                pitch_name(lower.pitch)),
                             {"pair": "%s + %s" % (upper_name, lower_name)})
                self.check_overlap(tick, upper_name, lower_name, upper, lower, reported)
                if not spaced:
                    continue
                gap = upper.pitch - lower.pitch
                limit = 12 if index + 2 < len(order) else 19
                key = ("CP-15", upper_name, lower_name)
                if gap > limit and key not in reported:
                    reported.add(key)
                    self.add("CP-15", tick, [upper_name, lower_name],
                             "%s to %s is %d semitones apart, more than %d"
                             % (lower_name, upper_name, gap, limit),
                             {"pair": "%s + %s" % (upper_name, lower_name), "gap": gap})


    def check_overlap(self, tick, upper_name, lower_name, upper, lower, reported):
        """The lower voice must not rise above where the upper voice just was, or the reverse."""
        upper_part = self.score.parts[upper_name]
        lower_part = self.score.parts[lower_name]
        before_upper = upper_part.previous_before(upper.start)
        before_lower = lower_part.previous_before(lower.start)
        key = ("CP-14", upper_name, lower_name)
        if key in reported or before_upper is None or before_lower is None:
            return
        if lower.pitch > before_upper.pitch:
            reported.add(key)
            self.add("CP-14", tick, [upper_name, lower_name],
                     "%s rises to %s, above where %s just was (%s)"
                     % (lower_name, pitch_name(lower.pitch), upper_name,
                        pitch_name(before_upper.pitch)),
                     {"pair": "%s + %s" % (upper_name, lower_name)})
            return
        if before_lower is not None and upper.pitch < before_lower.pitch:
            reported.add(key)
            self.add("CP-14", tick, [upper_name, lower_name],
                     "%s falls to %s, below where %s just was (%s)"
                     % (upper_name, pitch_name(upper.pitch), lower_name,
                        pitch_name(before_lower.pitch)),
                     {"pair": "%s + %s" % (upper_name, lower_name)})


def summarise(score, findings):
    """Counts per rule and per severity, plus the rates the calibration table is built from."""
    by_rule = {rule: 0 for rule in RULES}
    by_severity = {"hard": 0, "soft": 0, "style": 0}
    for finding in findings:
        by_rule[finding["rule"]] += 1
        by_severity[finding["severity"]] += 1
    notes = max(1, score.notes_total)
    rates = {rule: round(100.0 * count / notes, 3) for rule, count in by_rule.items()}
    return {"by_rule": by_rule, "by_severity": by_severity, "rates_per_100_notes": rates}


def analyse(score, profile="free"):
    """Run the checker and return the JSON-able result: findings, summary and what was measured."""
    checker = Checker(score, profile=profile)
    findings = checker.run()
    summary = summarise(score, findings)
    order = score.rank()
    voices = []
    for name in order:
        part = score.parts[name]
        low, high = score.range_of(name)
        voices.append({
            "name": name, "notes": len(part.line), "chord_slots": part.chord_slots,
            "range": [pitch_name(part.low), pitch_name(part.high)],
            "declared_range": [pitch_name(low), pitch_name(high)],
        })
    return {
        "format": "pp-counterpoint", "version": 1, "card": "t_836dbb1a",
        "path": score.path,
        "profile": checker.profile,
        "time_signature": "%d/%d" % score.time_sig,
        "bars": score.bars,
        "key": key_name(score.key),
        "key_source": "declared" if score.key_declared else "detected",
        "key_detected": key_name(score.key_detected),
        "notes": score.notes_total,
        "voices": voices,
        "outer_voices": list(score.outer()),
        "devices": checker.devices,
        "judged": checker.judged,
        "summary": summary,
        "findings": findings,
    }
