"""Repair a score's raw clashes by moving the accompaniment, never the hook, card t_c0597404.

The M0 card asks for a v9 that "turns every raw clash into a prepared and resolved device or a
consonance". This is the repairing half of that promise: the melody (vrc6 pulse a) is frozen
note for note and beat for beat, and every other pitched voice may move a pitch until the pair
it forms at that instant is no longer a raw clash.

What counts as a fix, in the order the search tries it:

  1. the smallest pitch move for the voice that made the clash, drawn from the key (A minor
     with the raised leading tone G#), so the line keeps its shape and its register;
  2. the move is scored by the number of dissonant intervals it forms anywhere inside its own
     span, not only at the clash, so a fix cannot push the problem one sixteenth later;
  3. when no pitch works, the note is dropped, because a silence is always consonant and a
     doubled part that cannot be made consonant is better absent than wrong.

The pass is greedy and it runs to a fixed number of rounds, then reports what is left. It never
claims a clean score: every remaining raw clash is printed with its bar and beat.

Usage:
    python tools/counterpoint/repair.py --source A.mid --out B.mid --report r.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import clash  # noqa: E402

# The line the card freezes. Its notes and their rhythm are the hook and the leitmotif.
HOOK = "vrc6 pulse a"

# Register limits per voice: the span v7 itself uses, which is inside each instrument's own
# range (build notes section 6: melody 64 to 81, pad 43 to 64, bass 36 to 52).
RANGES = {
    "vrc6 pulse a": (64, 81),
    "vrc6 pulse b": (45, 84),
    "vrc6 saw": (43, 64),
    "pulse 1": (55, 74),
    "pulse 2": (62, 81),
    "triangle": (36, 52),
}

# Which voice is moved first when a clash has more than one movable member. The two melodic
# lines carry the clash the ear hears, so they move before the arpeggio, and the arpeggio
# moves before the pad. The bass is not on the list at all: it states the chord, and moving
# it to cure an interval replaces the harmony instead of voicing it. That is a decision, and
# the residue after a repair run is where it shows.
PREFERENCE = ("vrc6 pulse b", "pulse 2", "pulse 1", "vrc6 saw", "triangle")

TRIADS = []
for _root in range(12):
    for _shape in ((0, 3, 7), (0, 4, 7), (0, 3, 6)):
        TRIADS.append(frozenset(((_root + s) % 12) for s in _shape))


def key_pitches(lo, hi):
    """Every pitch of A minor with the raised leading tone, inside a register."""
    return [p for p in range(lo, hi + 1) if (p % 12) in clash.A_MINOR]


class Song(object):
    """Editable note sets, one list per voice, keyed to the original file's ticks."""

    def __init__(self, path):
        song = clash.hook_score.read_smf(path)
        self.division = song["division"]
        self.time_sig = song["time_sig"]
        self.tempo_us = song["tempo_us"]
        self.tracks = [(t["name"].strip().lower(), t["cc"]) for t in song["tracks"]]
        self.notes = {}
        self.cc = {}
        for track in song["tracks"]:
            name = track["name"].strip().lower()
            self.notes[name] = [tuple(n) for n in track["notes"]]
            self.cc[name] = track["cc"]
        self.path = path

    def score(self):
        return clash.Score.from_notes(self.notes, self.division, self.time_sig,
                                      self.tempo_us, path=self.path)

    def index(self):
        """(voice, snapped start, pitch) -> position in that voice's list."""
        if getattr(self, "_index", None) is not None:
            return self._index
        out = {}
        grid = self.division // 4
        for name, notes in self.notes.items():
            for i, (start, end, pitch, velocity) in enumerate(notes):
                out[(name, clash.snap(start, grid), pitch)] = i
        self._index = out
        return out

    def dirty(self):
        self._index = None

    def note_position(self, voice_name, tick, pitch):
        """The note of this voice sounding at the tick at this pitch, held or attacked."""
        grid = self.division // 4
        snapped_tick = clash.snap(tick, grid)
        exact = self.index().get((voice_name, snapped_tick, pitch))
        if exact is not None:
            return exact
        for i, (start, end, note_pitch, velocity) in enumerate(self.notes.get(voice_name, [])):
            if note_pitch != pitch:
                continue
            if start <= tick + grid // 2 and end > tick:
                return i
        return None

    def write(self, path):
        sys.path.insert(0, os.path.join(HERE, ".."))
        import humanize
        payload = {"division": self.division, "tempo_us": self.tempo_us,
                   "time_sig": self.time_sig, "tracks": []}
        for name, cc in self.tracks:
            payload["tracks"].append({"name": name,
                                      "notes": [n for n in self.notes.get(name, [])],
                                      "cc": cc})
        humanize.write_smf(payload, path)
        return path


def instants(score, voice_name, start, end):
    """The instants inside a note's span where another voice attacks, plus its own onset."""
    out = [start]
    for name, voice in score.voices.items():
        if name == voice_name:
            continue
        for tick in voice.onsets():
            if start < tick < end:
                out.append(tick)
    return sorted(set(out))


def badness(score, voice_name, pitch, start, end):
    """Dissonant intervals a candidate pitch would form inside the note's own span."""
    total = 0
    for tick in instants(score, voice_name, start, end):
        others = [(name, voice.sounding(tick)) for name, voice in score.voices.items()
                  if name != voice_name]
        sounding = [pitch] + [note[2] for _, notes in others for note in notes]
        bass = min(sounding) if sounding else pitch
        for name, notes in others:
            for note in notes:
                if clash.is_dissonant(score, tick, voice_name, name, pitch, note[2], bass):
                    total += 1
    return total


def clash_free(score, voice_name, pitch, start, end):
    return badness(score, voice_name, pitch, start, end) == 0


def candidates(voice_name, pitch):
    """Key pitches near the one being replaced, nearest first."""
    lo, hi = RANGES.get(voice_name, (36, 84))
    options = [p for p in key_pitches(lo, hi) if p != pitch]
    options.sort(key=lambda p: (abs(p - pitch), p))
    return options[:10]


def pad_group(song, start):
    """The pad notes that begin at the same instant, which are one voicing of one chord."""
    grid = song.division // 4
    key = clash.snap(start, grid)
    out = []
    for i, (note_start, end, pitch, velocity) in enumerate(song.notes["vrc6 saw"]):
        if clash.snap(note_start, grid) == key:
            out.append(i)
    return out


def pad_group_ok(song, group, replace_position, new_pitch):
    """Does the voicing stay a triad when one of its notes moves?"""
    scale = clash.A_MINOR
    classes = set()
    for i in group:
        pitch = new_pitch if i == replace_position else song.notes["vrc6 saw"][i][2]
        classes.add(pitch % 12)
    if len(classes) < 2:
        return False
    for triad in TRIADS:
        if classes <= set(triad) and all(pc in scale for pc in triad):
            return True
    return False


DIATONIC = []
for _root in sorted(clash.A_MINOR):
    for _shape in ((0, 3, 7), (0, 4, 7), (0, 3, 6)):
        _set = frozenset((_root + s) % 12 for s in _shape)
        if set(_set) <= set(clash.A_MINOR) and _set not in DIATONIC:
            DIATONIC.append(_set)


def pad_rewrites(song, group, melody_pitch_classes):
    """Whole-chord alternatives for one pad onset group.

    The pad states the harmony, so a fix that moves one of its notes has to leave a triad
    behind. When no single note works, the chord is re-voiced instead: any diatonic triad that
    contains every melody pitch sounding over it, voiced as near the old notes as possible.
    """
    originals = [song.notes["vrc6 saw"][i][2] for i in group]
    need = set(melody_pitch_classes)
    out = []
    for triad in DIATONIC:
        if not need <= set(triad):
            continue
        pitches = []
        for original in originals:
            options = [pc + 12 * octave for pc in triad for octave in range(2, 6)]
            options = [p for p in options if RANGES["vrc6 saw"][0] <= p <= RANGES["vrc6 saw"][1]]
            if not options:
                break
            pitches.append(min(options, key=lambda p: abs(p - original)))
        if len(pitches) == len(originals) and len(set(pitches)) == len(pitches):
            out.append(pitches)
    return out


def group_badness(score, group_positions, pitches, spans, voice_name="vrc6 saw"):
    """Dissonances the whole voicing would form inside its own span."""
    total = 0
    for tick in spans:
        others = [(name, voice.sounding(tick)) for name, voice in score.voices.items()
                  if name != voice_name]
        sounding = list(pitches) + [note[2] for _, notes in others for note in notes]
        bass = min(sounding) if sounding else min(pitches)
        for pitch in pitches:
            for name, notes in others:
                for note in notes:
                    if clash.is_dissonant(score, tick, voice_name, name, pitch, note[2], bass):
                        total += 1
    return total


def rewrite_pad(song, score, event, log):
    """Re-voice the pad chord under a clash that a single note cannot fix."""
    position = song.note_position("vrc6 saw", event["tick"], clash.name_pitch(
        event["low"] if event["low_voice"] == "vrc6 saw" else event["high"]))
    if position is None:
        return False
    start, end, pitch, velocity = song.notes["vrc6 saw"][position]
    group = pad_group(song, start)
    melody = [n[2] for n in score.voices[HOOK].sounding(event["tick"])] if HOOK in score.voices else []
    if not melody:
        return False
    spans = instants(score, "vrc6 saw", start, max(end, max(
        song.notes["vrc6 saw"][i][1] for i in group)))
    current = group_badness(score, group, [song.notes["vrc6 saw"][i][2] for i in group], spans)
    best = None
    for pitches in pad_rewrites(song, group, [p % 12 for p in melody]):
        value = group_badness(score, group, pitches, spans)
        movement = sum(abs(a - b) for a, b in zip(pitches,
                                                  [song.notes["vrc6 saw"][i][2] for i in group]))
        key = (value, movement)
        if best is None or key < best[0]:
            best = (key, pitches)
    if best is None or best[0][0] >= current:
        return False
    before = [clash.pitch_name(song.notes["vrc6 saw"][i][2]) for i in group]
    for i, new_pitch in zip(group, best[1]):
        s, e, p, v = song.notes["vrc6 saw"][i]
        song.notes["vrc6 saw"][i] = (s, e, new_pitch, v)
    song.dirty()
    log.append({"bar": event["bar"], "beat": event["beat"], "voice": "vrc6 saw",
                "from": "+".join(before),
                "to": "+".join(clash.pitch_name(p) for p in best[1]),
                "why": "whole chord re-voiced: a single note could not keep it a triad"})
    return True


def fix_event(song, score, event, movable, log):
    """Try to remove one raw clash. Returns True when an edit was applied."""
    tick = event["tick"]
    voices = {event["low_voice"]: clash.name_pitch(event["low"]),
              event["high_voice"]: clash.name_pitch(event["high"])}
    best = None
    for voice_name, pitch in sorted(voices.items()):
        if voice_name not in movable or voice_name == HOOK:
            continue
        rank = PREFERENCE.index(voice_name) if voice_name in PREFERENCE else 9
        position = song.note_position(voice_name, tick, pitch)
        if position is None:
            continue
        start, end, _, velocity = song.notes[voice_name][position]
        current = badness(score, voice_name, pitch, start, end)
        allowed = None
        if voice_name == "triangle":
            # The bass may only move to a pitch class the pad is already sounding or the
            # melody is sounding at that instant, so a last resort edit voices the chord
            # instead of replacing it.
            allowed = set()
            for note in score.voices.get("vrc6 saw").sounding(tick) if score.voices.get("vrc6 saw") else []:
                allowed.add(note[2] % 12)
            for note in score.voices[HOOK].sounding(tick) if HOOK in score.voices else []:
                allowed.add(note[2] % 12)
            allowed.discard(pitch % 12)
        for candidate in candidates(voice_name, pitch):
            if allowed is not None and (candidate % 12) not in allowed:
                continue
            if voice_name == "vrc6 saw" and not pad_group_ok(
                    song, pad_group(song, start), position, candidate):
                continue
            score_value = badness(score, voice_name, candidate, start, end)
            key = (score_value, rank, abs(candidate - pitch))
            if best is None or key < best[0]:
                best = (key, voice_name, position, candidate, current)
    if best is None or best[0][0] >= best[4]:
        # No single note improves things. The pad gets one more try as a whole chord,
        # because moving one note of a triad can only leave a non-chord behind.
        if "vrc6 saw" in (event["low_voice"], event["high_voice"]):
            if rewrite_pad(song, score, event, log):
                return True
        if best is None or best[4] == 0:
            return False
        key, voice_name, position, candidate, current = best
        start, end, pitch, velocity = song.notes[voice_name][position]
        del song.notes[voice_name][position]
        song.dirty()
        log.append({"bar": event["bar"], "beat": event["beat"], "voice": voice_name,
                    "from": clash.pitch_name(pitch), "to": "rest",
                    "why": "no pitch inside the key removes the clash"})
        return True
    key, voice_name, position, candidate, current = best
    start, end, pitch, velocity = song.notes[voice_name][position]
    song.notes[voice_name][position] = (start, end, candidate, velocity)
    song.dirty()
    log.append({"bar": event["bar"], "beat": event["beat"], "voice": voice_name,
                "from": clash.pitch_name(pitch), "to": clash.pitch_name(candidate),
                "dissonances": current, "after": key[0]})
    return True


def repair(song, rounds=6, movable=None, verbose=True):
    movable = movable or tuple(v for v in clash.VOICES if v != HOOK)
    log = []
    history = []
    for round_index in range(1, rounds + 1):
        score = song.score()
        events = clash.analyse(score)
        raws = [e for e in events if e["class"] == "raw clash"]
        strong = sum(1 for e in raws if e["weight"] == "strong")
        history.append({"round": round_index, "raw": len(raws), "strong": strong})
        if verbose:
            print("round %d: %d raw clashes, %d on a strong beat" % (round_index, len(raws), strong))
        if not raws:
            break
        edits = 0
        real = 0
        for event in sorted(raws, key=lambda e: (e["weight"] != "strong", e["tick"])):
            edits += 1
            if fix_event(song, score, event, movable, log):
                real += 1
            if edits % 25 == 0:
                score = song.score()
        if verbose:
            print("  applied %d edits" % real)
        if real == 0:
            break
    return log, history


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--report", default=None)
    parser.add_argument("--rounds", type=int, default=6)
    args = parser.parse_args()

    song = Song(args.source)
    before = clash.analyse(song.score())
    summary_before = clash.summarise(song.score(), before)
    log, history = repair(song, rounds=args.rounds)
    after_score = song.score()
    after = clash.analyse(after_score)
    summary_after = clash.summarise(after_score, after)

    song.write(args.out)
    print("wrote", args.out)
    print("raw clashes %d -> %d, strong %d -> %d"
          % (summary_before["raw_total"], summary_after["raw_total"],
             summary_before["strong_raw"], summary_after["strong_raw"]))
    for key in clash.CLASSES:
        print("  %-14s %4d -> %4d" % (key, summary_before["by_class"][key],
                                      summary_after["by_class"][key]))
    if args.report:
        with open(args.report, "w", encoding="utf-8") as handle:
            json.dump({"source": args.source, "out": args.out, "history": history,
                       "edits": log,
                       "before": {k: summary_before[k] for k in
                                  ("by_class", "raw_total", "strong_raw")},
                       "after": {k: summary_after[k] for k in
                                 ("by_class", "raw_total", "strong_raw")}}, handle, indent=1)
        print("report", args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
