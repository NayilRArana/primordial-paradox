"""Vertical interval classifier for the Primordial Paradox score, card t_c0597404 (M0).

Why this exists: the score carries a dissonance injector (data/dissonance_rules.json) and the
ear critic is a mix listener, so nothing in the pipeline asks whether a dissonance in the
written notes is PREPARED and RESOLVED. This module answers that question from the note data
alone, for every voice pair at every onset, and puts every dissonance into one of five bins.

  passing       a weak or offbeat position, the dissonant note entered and left by step in the
                same direction
  neighbour     a weak or offbeat position, the dissonant note entered by step and left by step
                back to the pitch it came from
  suspension    the dissonant note was already sounding at that pitch (a tie or a repeat), and
                it resolves down by step
  appoggiatura  on a strong beat, the dissonant note entered freely, and it resolves by step
  RAW CLASH     anything else, which is the class that reads as a wrong note

How a pair is judged, once per articulation:

  1. The two voices of a pair are unordered, so each (voice pair, instant, pitches) is one
     judgement, not two. Only the instants where at least one of the two voices attacks a
     note are judged, because that is what "at every onset" means.
  2. A note counts as sounding at an instant if it started at or before it (within a
     sixteenth of a beat) and it has not ended. The tolerance is there because the pad
     triads are rolled by 14 to 40 ticks, which is a strum of about 20 ms and not three
     separate harmonies.
  3. The dissonance set at that instant is every sounding pitch of one voice against every
     sounding pitch of the other; the interval classes decide.
  4. prepared = every note ATTACKED at the instant repeats or ties a pitch class that voice
     was already sounding. If a voice attacks a new pitch, it created the dissonance, so the
     dissonance is not prepared.
  5. resolution = the next articulation of either voice, which must arrive by the end of the
     dissonant note (plus a sixteenth), must move the dissonant note by one or two semitones,
     and must land on a pitch that is consonant against everything the other voice sounds at
     that moment, or against silence.

Consonance model, kept explicit because every count in the report depends on it:

  interval classes 0, 3, 4, 7, 8, 9 are consonant (unison, octave, third, fifth, sixth)
  interval classes 1, 2, 5, 6, 10, 11 are dissonant (second, seventh, tritone, fourth)
  a perfect fourth (class 5) counts as CONSONANT except when it is the interval above the
  lowest sounding note of the whole texture, where the classic rule applies: it is dissonant
  unless another voice puts a third or a sixth above that bass, which is the 6/4 case. A
  fourth between two upper voices is a chord member and is not counted, or the count becomes
  a count of triad spacings.

Metric weight, as a fraction of the score's 3/4 bar:

  strong  beat 1
  medium  beat 2
  weak    beat 3
  offbeat anything else (the eighth note positions between the beats)

Nothing here generates music. It measures, and every number is traceable to a (voice, start,
pitch) the caller can open in the MIDI file.

Usage:
    from clash import load_score, analyse, summarise
"""

from __future__ import annotations

import bisect
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(ROOT, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "tools"))

import hook_score  # noqa: E402

# Every pitched voice in the score. noise and dpcm carry drum ids, not pitches.
VOICES = ("vrc6 pulse a", "vrc6 pulse b", "vrc6 saw", "pulse 1", "pulse 2", "triangle")

# The three voices the card names. In this build they are the arpeggio, the echo and the
# bass; the melody sits on vrc6 pulse a, which the report states out loud.
CARD_TRIO = ("pulse 1", "pulse 2", "triangle")

# The three lines a counterpoint reader would name in this build.
LINES = ("vrc6 pulse a", "vrc6 pulse b", "triangle")

CONSONANT = frozenset((0, 3, 4, 7, 8, 9))
IC_NAMES = {0: "P8", 1: "m2", 2: "M2", 3: "m3", 4: "M3", 5: "P4",
            6: "TT", 7: "P5", 8: "m6", 9: "M6", 10: "m7", 11: "M7"}

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

A_MINOR = frozenset((9, 11, 0, 2, 4, 5, 7, 8))  # A B C D E F G, plus G# the leading tone

CLASSES = ("suspension", "appoggiatura", "passing", "neighbour", "anticipation", "raw clash")

TOLERANCE_DIVISIONS = 16  # a sixteenth of a beat


def pitch_name(value):
    return "%s%d" % (NOTE_NAMES[value % 12], value // 12 - 1)


def name_pitch(text):
    """'E5' back to a MIDI number, so a printed name can be matched against the note list."""
    name = text[:-1]
    octave = int(text[-1])
    return NOTE_NAMES.index(name) + 12 * (octave + 1)


def pitch_class(value):
    return value % 12


def interval_class(low, high):
    return (high - low) % 12


def snap(tick, grid):
    """Put an onset on the score's sixteenth grid. Measured 2026-10-26: every onset in
    pp_01_title_v7 sits within 19 ticks of that grid, and the pad's strum spreads one chord
    across 14 of them, so snapping merges a rolled triad without moving a rhythm."""
    return int(round(tick / float(grid))) * grid


class Voice(object):
    """One track, with the lookups the classifier needs."""

    def __init__(self, name, notes, tolerance):
        self.name = name
        self.notes = sorted(notes)
        self.starts = [n[0] for n in self.notes]
        self.tolerance = tolerance
        self.span = max((n[1] - n[0]) for n in self.notes) if self.notes else 0

    def __len__(self):
        return len(self.notes)

    def sounding(self, tick):
        """Pitches sounding at the tick. Chords overlap, so this returns every one."""
        out = []
        index = bisect.bisect_right(self.starts, tick + self.tolerance) - 1
        floor = tick - self.span - self.tolerance
        while index >= 0:
            start, end, pitch, velocity = self.notes[index]
            if start <= tick + self.tolerance and end > tick:
                out.append(self.notes[index])
            if start < floor:
                break
            index -= 1
        return sorted(out, key=lambda n: n[2])

    def sounding_before(self, tick):
        """Pitches sounding a moment before the tick, ties and the legato edge included."""
        out = []
        index = bisect.bisect_right(self.starts, tick) - 1
        floor = tick - self.span - self.tolerance
        while index >= 0:
            start, end, pitch, velocity = self.notes[index]
            if start < tick and end >= tick - self.tolerance:
                out.append(self.notes[index])
            if start < floor:
                break
            index -= 1
        return sorted(out, key=lambda n: n[2])

    def onsets(self):
        return sorted(set(self.starts))

    def at(self, tick):
        """Every note starting within the tolerance of the tick."""
        lo = bisect.bisect_left(self.starts, tick - self.tolerance)
        out = []
        while lo < len(self.notes) and self.notes[lo][0] <= tick + self.tolerance:
            out.append(self.notes[lo])
            lo += 1
        return out

    def previous(self, tick):
        index = bisect.bisect_left(self.starts, tick - self.tolerance) - 1
        return self.notes[index] if index >= 0 else None


class Score(object):
    def __init__(self, path, key_name="A minor"):
        self.path = path
        song = hook_score.read_smf(path)
        self._setup(song["division"], song["time_sig"], song["tempo_us"],
                    {track["name"].strip().lower(): track["notes"] for track in song["tracks"]},
                    key_name)

    @classmethod
    def from_notes(cls, notes_by_voice, division=480, time_sig=(3, 4),
                   tempo_us=476190, key_name="A minor", path=None):
        """The same object built from notes already in memory, for a repair pass that must
        measure a candidate edit without writing a MIDI file first."""
        score = cls.__new__(cls)
        score.path = path
        score._setup(division, time_sig, tempo_us, notes_by_voice, key_name)
        return score

    def _setup(self, division, time_sig, tempo_us, notes_by_voice, key_name):
        self.tempo_us = tempo_us
        self.division = division
        self.time_sig = time_sig
        beats_per_bar = self.time_sig[0]
        beat_unit = self.time_sig[1]
        self.ticks_per_beat = self.division * 4 // beat_unit
        self.bar_ticks = self.ticks_per_beat * beats_per_bar
        self.tolerance = self.ticks_per_beat // TOLERANCE_DIVISIONS
        self.grid = self.ticks_per_beat // 4  # a sixteenth
        self.voices = {}
        for name, notes in notes_by_voice.items():
            if name not in VOICES:
                continue
            snapped = [(snap(s, self.grid), e, p, v) for s, e, p, v in notes]
            self.voices[name] = Voice(name, snapped, self.tolerance)
        self.key_name = key_name
        self.key = A_MINOR
        self.bars = 0
        for voice in self.voices.values():
            if voice.notes:
                self.bars = max(self.bars, 1 + voice.notes[-1][0] // self.bar_ticks)
        self.tempo_bpm = 60_000_000.0 / self.tempo_us if self.tempo_us else None

    def bar_beat(self, tick):
        bar = tick // self.bar_ticks + 1
        beat = 1.0 + (tick % self.bar_ticks) / float(self.ticks_per_beat)
        return bar, beat

    def weight(self, tick):
        position = (tick % self.bar_ticks) / float(self.ticks_per_beat)
        for name, offset in (("strong", 0.0), ("medium", 1.0), ("weak", 2.0)):
            if abs(position - offset) < 0.02:
                return name
        return "offbeat"

    def eighth(self):
        return self.ticks_per_beat // 2


def load_score(path, key_name="A minor"):
    return Score(path, key_name)


def supported_fourth(score, name_a, name_b, low, tick):
    """Is a fourth above the bass consonant because another voice puts a third or sixth above it?"""
    for name, voice in score.voices.items():
        if name in (name_a, name_b):
            continue
        for start, end, pitch, velocity in voice.sounding(tick):
            if pitch <= low:
                continue
            if interval_class(low, pitch) in (3, 4, 8, 9):
                return name
    return None


def lowest_sounding(score, tick, name_a, name_b):
    """The lowest pitch of the whole texture at the tick, which is the bass for the 4th rule."""
    lowest = None
    for name in (name_a, name_b):
        for note in score.voices[name].sounding(tick):
            if lowest is None or note[2] < lowest:
                lowest = note[2]
    for name, voice in score.voices.items():
        if name in (name_a, name_b):
            continue
        for note in voice.sounding(tick):
            if lowest is None or note[2] < lowest:
                lowest = note[2]
    return lowest


def harmony(score, tick):
    """The pitch classes the accompaniment is sounding: the pad plus the bass.

    Both voices are read together because between them they state the chord in this build
    (the pad plays the triad, the triangle the root). A vertical interval whose two notes are
    BOTH members of that set is a chord member and is not a dissonance, whatever its size:
    a diminished fifth inside a diminished triad is the chord, not a clash. This is the one
    assumption the whole count rests on, so it is stated rather than buried.
    """
    out = set()
    for name in ("vrc6 saw", "triangle"):
        voice = score.voices.get(name)
        if not voice:
            continue
        for note in voice.sounding(tick):
            out.add(pitch_class(note[2]))
    return out


def is_dissonant(score, tick, name_a, name_b, pitch_a, pitch_b, bass):
    """The single test every count comes back to. Conventions are in the module docstring."""
    chord = harmony(score, tick)
    low, high = (pitch_a, pitch_b) if pitch_a <= pitch_b else (pitch_b, pitch_a)
    if pitch_class(low) in chord and pitch_class(high) in chord:
        return False
    ic = interval_class(low, high)
    if ic in CONSONANT:
        return False
    if ic == 5:
        if low != bass:
            return False
        if supported_fourth(score, name_a, name_b, low, tick):
            return False
    return True


def dissonant_combos(score, name_a, name_b, tick, notes_a, notes_b, bass):
    """Every dissonant pair of sounding pitches between two voices at one instant."""
    out = []
    for note_a in notes_a:
        for note_b in notes_b:
            if not is_dissonant(score, tick, name_a, name_b, note_a[2], note_b[2], bass):
                continue
            low, high = (note_a, note_b) if note_a[2] <= note_b[2] else (note_b, note_a)
            out.append({"low": low[2], "high": high[2],
                        "ic": interval_class(low[2], high[2]),
                        "ic_name": IC_NAMES[interval_class(low[2], high[2])],
                        "low_voice": name_a if low is note_a else name_b,
                        "high_voice": name_b if low is note_a else name_a})
    return out


def pair_ticks(score, name_a, name_b):
    ticks = set(score.voices[name_a].onsets())
    ticks.update(score.voices[name_b].onsets())
    return sorted(ticks)


def landing_ok(score, name_a, name_b, later, other_name, pitch):
    """A resolution lands on a chord member, or on something consonant with the clash partner."""
    chord = harmony(score, later)
    if pitch_class(pitch) in chord:
        return True, "chord tone"
    other_pitches = [n[2] for n in score.voices[other_name].sounding(later)]
    if not other_pitches:
        return True, "other voice silent"
    bass = lowest_sounding(score, later, name_a, name_b)
    for other in other_pitches:
        low, high = (pitch, other) if pitch <= other else (other, pitch)
        ic = interval_class(low, high)
        if ic in CONSONANT:
            continue
        if ic == 5 and (low != bass or supported_fourth(score, name_a, name_b, low, later)):
            continue
        return False, IC_NAMES[ic]
    return True, "consonant"


def step_to(voice, later, pitch):
    """The note a voice attacks at an instant, chosen as the one nearest a pitch."""
    new = voice.at(later)
    if not new:
        return None
    return min(new, key=lambda n: abs(n[2] - pitch))


def next_attack(score, voice_name, ticks, index, limit):
    """The first later articulation of one voice, inside the resolution window.

    A voice's resolution is its own next note, and another voice attacking in between does
    not deprive it of one. Reading only the pair's next instant is what made a held note look
    unresolved whenever the bass moved first.
    """
    voice = score.voices[voice_name]
    for tick in ticks[index + 1:]:
        if tick > limit:
            return None
        if voice.at(tick):
            return tick
    return None


def analyse_pair(score, name_a, name_b):
    """Every vertical interval this pair sounds, one judgement per interval per onset."""
    voice_a = score.voices[name_a]
    voice_b = score.voices[name_b]
    ticks = pair_ticks(score, name_a, name_b)
    events = []
    for index, tick in enumerate(ticks):
        notes_a = voice_a.sounding(tick)
        notes_b = voice_b.sounding(tick)
        if not notes_a or not notes_b:
            continue
        combos = dissonant_combos(score, name_a, name_b, tick, notes_a, notes_b,
                                  lowest_sounding(score, tick, name_a, name_b))
        if not combos:
            continue
        attacked = {}
        for name, voice in ((name_a, voice_a), (name_b, voice_b)):
            hit = voice.at(tick)
            if hit:
                attacked[name] = hit
        if not attacked:
            continue
        bar, beat = score.bar_beat(tick)
        weight = score.weight(tick)
        limit = max(max(n[1] for n in notes_a), max(n[1] for n in notes_b)) \
            + score.ticks_per_beat

        for combo in combos:
            low_voice, high_voice = combo["low_voice"], combo["high_voice"]
            attacked_low = low_voice in attacked
            attacked_high = high_voice in attacked
            if attacked_low and not attacked_high:
                # An upper voice held over a bass that moves: the suspension shape, and the held
                # part is the upper one.
                attacker, subject = low_voice, high_voice
            else:
                # Either the upper voice arrives over a held bass, or both arrive at once. In both
                # cases nothing is prepared: a bass that sits still while the soprano moves is a
                # pedal, not a suspension, and the upper voice is the line that has to resolve.
                attacker, subject = high_voice, None
            pitch_of = lambda owner: combo["low"] if owner == low_voice else combo["high"]
            event = {
                "bar": bar, "beat": round(beat, 2), "tick": tick,
                "pair": "%s | %s" % tuple(sorted((name_a, name_b))),
                "weight": weight, "low": pitch_name(combo["low"]),
                "high": pitch_name(combo["high"]), "ic_name": combo["ic_name"],
                "low_voice": low_voice, "high_voice": high_voice,
                "voice": attacker or low_voice,
                "ref": subject or (high_voice if attacker == low_voice else low_voice),
                "subject": subject, "attacker": attacker,
                "prepared": subject is not None,
                "resolution": {},
            }
            info = {}
            if subject:
                later = next_attack(score, subject, ticks, index, limit)
                if later is not None:
                    note = step_to(score.voices[subject], later, pitch_of(subject))
                    if note is not None:
                        step = note[2] - pitch_of(subject)
                        ok, why = landing_ok(score, name_a, name_b, later, attacker, note[2])
                        info["subject"] = {"voice": subject, "to": pitch_name(note[2]),
                                           "step": step, "ok": ok, "why": why,
                                           "bar": score.bar_beat(later)[0],
                                           "beat": round(score.bar_beat(later)[1], 2)}
            if attacker:
                later = next_attack(score, attacker, ticks, index, limit)
                if later is not None:
                    other = subject or (high_voice if attacker == low_voice else low_voice)
                    note = step_to(score.voices[attacker], later, pitch_of(attacker))
                    if note is not None:
                        step = note[2] - pitch_of(attacker)
                        ok, why = landing_ok(score, name_a, name_b, later, other, note[2])
                        info["attacker"] = {"voice": attacker, "to": pitch_name(note[2]),
                                            "step": step, "ok": ok, "why": why,
                                            "bar": score.bar_beat(later)[0],
                                            "beat": round(score.bar_beat(later)[1], 2)}
            event["resolution"] = info
            event["class"], event["why"] = classify_event(event, score, tick, info)
            events.append(event)
    return events


def entry_by_step(score, voice_name, tick):
    """Was the note this voice attacks at the tick reached by a step from its own last note?"""
    voice = score.voices.get(voice_name)
    if not voice:
        return None
    prev = voice.previous(tick)
    if not prev or (tick - prev[1]) > score.tolerance + score.eighth():
        return None
    for note in voice.at(tick):
        step = note[2] - prev[2]
        if abs(step) in (1, 2):
            return step
    return None


def implied(score, tick):
    """The triad the sounding bass implies in the key, thirds and fifths included.

    The pad is often two notes and the trio has no pad at all, so the chord the ear hears is
    usually wider than the notes actually sounding: a bass on E with nothing above it still
    means Em in this key. An anticipation has to be judged against that chord, because the
    device's own definition is "the next chord's third", not "a note the pad happens to double".
    """
    sounding = [note[2] for voice in score.voices.values() for note in voice.sounding(tick)]
    if not sounding:
        return set()
    root = min(sounding) % 12
    third = root + 3 if (root + 3) % 12 in score.key else root + 4
    return {root, third % 12, (root + 7) % 12}


def is_anticipation(score, event, tick):
    """A note that is a non-chord tone now and the next chord's tone an eighth later.

    The injector writes this deliberately (DIS-09: the next chord's third on the last eighth of
    the bar, held across the line where it becomes a chord tone). It is not a clash: the ear
    hears the resolution arrive with the chord. The test is therefore about the bar line, not
    about the note leaving by step.
    """
    bar_length = score.bar_ticks
    next_bar = ((tick // bar_length) + 1) * bar_length
    if next_bar - tick > score.ticks_per_beat // 2 + score.grid:
        return False
    coming = harmony(score, next_bar) | implied(score, next_bar)
    now = harmony(score, tick) | implied(score, tick)
    if not coming:
        return False
    for name, text in ((event["low_voice"], event["low"]), (event["high_voice"], event["high"])):
        pitch = name_pitch(text)
        if pitch % 12 in coming and pitch % 12 not in now:
            sounding = score.voices[name].at(tick) or []
            held = [note for note in sounding
                    if note[2] % 12 == pitch % 12 and note[1] >= next_bar - score.grid]
            if held:
                return True
    return False


def classify_event(event, score, tick, info):
    """The six bin verdict, with the reason it got there."""
    subject = event["subject"]
    attacker = event["attacker"]
    weight = event["weight"]
    sub = info.get("subject") or {}
    att = info.get("attacker") or {}
    if subject and sub.get("ok") and abs(sub.get("step") or 0) in (1, 2) and sub["step"] < 0:
        return "suspension", "held over at that pitch, resolves down a step"
    if weight == "strong" and attacker and att.get("ok") and abs(att.get("step") or 0) in (1, 2):
        return "appoggiatura", "downbeat, entered freely, resolves by step"
    if weight in ("weak", "offbeat", "medium") and attacker and att.get("ok") \
            and abs(att.get("step") or 0) in (1, 2):
        entry = entry_by_step(score, attacker, tick)
        if entry is not None:
            if att["step"] * entry > 0:
                return "passing", "weak beat, step in and step on"
            if att["step"] == -entry:
                return "neighbour", "weak beat, step in and step back"
            return "neighbour", "weak beat, step in and back by another step"
    if is_anticipation(score, event, tick):
        return "anticipation", "the next chord's tone, sounded early and a chord tone at the line"
    reasons = []
    if not subject:
        if attacker == event["high_voice"] and event["weight"] != "strong":
            reasons.append("the upper voice arrives over a held note")
        else:
            reasons.append("both voices attack a new pitch")
    if subject and not sub:
        reasons.append("held note never moves again")
    elif sub and not sub.get("ok") and abs(sub.get("step") or 0) not in (1, 2):
        reasons.append("held note leaves by a leap")
    elif sub and not sub.get("ok"):
        reasons.append("held note lands on %s" % sub.get("why"))
    if attacker and not att:
        reasons.append("attacking note never moves again")
    elif att and not att.get("ok") and abs(att.get("step") or 0) not in (1, 2):
        reasons.append("leaves by a leap")
    elif att and not att.get("ok"):
        reasons.append("lands on %s" % att.get("why"))
    if weight == "strong":
        reasons.append("on the downbeat")
    elif weight == "medium":
        reasons.append("on beat 2")
    return "raw clash", ", ".join(reasons) or "unclassified"


def analyse(score, voices=None, pairs=None):
    voices = voices or VOICES
    if pairs is None:
        pairs = [(a, b) for i, a in enumerate(voices) for b in voices[i + 1:]]
    events = []
    for name_a, name_b in pairs:
        if name_a not in score.voices or name_b not in score.voices:
            continue
        events.extend(analyse_pair(score, name_a, name_b))
    events.sort(key=lambda e: (e["tick"], e["pair"]))
    return events


def summarise(score, events, bars_per_block=8):
    by_class = {name: 0 for name in CLASSES}
    for event in events:
        by_class[event["class"]] += 1
    raw_by_pair = {}
    blocks = {}
    for event in events:
        if event["class"] != "raw clash":
            continue
        raw_by_pair[event["pair"]] = raw_by_pair.get(event["pair"], 0) + 1
        block = (event["bar"] - 1) // bars_per_block + 1
        blocks[block] = blocks.get(block, 0) + 1
    strong_raw = [e for e in events if e["class"] == "raw clash" and e["weight"] == "strong"]
    total_blocks = (score.bars + bars_per_block - 1) // bars_per_block
    return {
        "by_class": by_class,
        "raw_by_pair": raw_by_pair,
        "blocks": dict(sorted(blocks.items())),
        "blocks_total": total_blocks,
        "bars_per_block": bars_per_block,
        "raw_total": by_class["raw clash"],
        "strong_raw": len(strong_raw),
        "strong_raw_events": strong_raw,
        "dissonances": sum(by_class.values()),
    }


def cross_relations(score, window_bars=1):
    """A pitch class followed by a semitone neighbour of it in another voice.

    The false relation of the Baroque: one voice sounds a note, another sounds its chromatic
    alteration before or after it, and the ear cannot decide which is the key's note. Only
    counted where the two notes do not overlap and are at most one bar apart.
    """
    out = []
    names = sorted(score.voices)
    for i, name_a in enumerate(names):
        for name_b in names[i + 1:]:
            for start_a, end_a, pitch_a, velocity in score.voices[name_a].notes:
                for start_b, end_b, pitch_b, velocity_b in score.voices[name_b].notes:
                    if abs(start_b - start_a) > window_bars * score.bar_ticks:
                        continue
                    if start_a <= start_b < end_a or start_b <= start_a < end_b:
                        continue
                    if abs(pitch_a - pitch_b) % 12 != 1:
                        continue
                    out.append({
                        "bar": start_a // score.bar_ticks + 1,
                        "a": name_a, "a_pitch": pitch_name(pitch_a),
                        "b": name_b, "b_pitch": pitch_name(pitch_b),
                        "outside_key": [pitch_name(p) for p in (pitch_a, pitch_b)
                                        if pitch_class(p) not in score.key],
                    })
    return out


def out_of_key(score):
    """Every note whose pitch class is not in A minor, counted by voice and by pitch."""
    by_voice = {}
    by_pitch = {}
    examples = {}
    for name, voice in score.voices.items():
        for start, end, pitch, velocity in voice.notes:
            if pitch_class(pitch) in score.key:
                continue
            by_voice[name] = by_voice.get(name, 0) + 1
            key = pitch_name(pitch)[:-1]
            by_pitch[key] = by_pitch.get(key, 0) + 1
            examples.setdefault(key, []).append((name, start // score.bar_ticks + 1))
    return {"by_voice": by_voice, "by_pitch": by_pitch, "examples": examples}


def note_keys(score):
    keys = set()
    for name, voice in score.voices.items():
        for start, end, pitch, velocity in voice.notes:
            keys.add((name, start, pitch))
    return keys


def added_notes(new_path, old_path):
    """The (voice, start, pitch) triples the newer file has and the older one does not."""
    return note_keys(load_score(new_path)) - note_keys(load_score(old_path))
