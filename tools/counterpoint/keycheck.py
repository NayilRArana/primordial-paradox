"""Key and cross relation checks for one score, card t_c0597404 (M0).

    python tools/counterpoint/keycheck.py FILE [FILE ...]

Two questions the clash analyser does not answer, because they are about the key rather than about
one vertical interval:

  notes outside the key   a pitch class the A minor scale does not hold. G# is in this scale on
                          purpose (the leading tone of the harmonic form), so it is not reported.
  cross relations         two voices sounding chromatic neighbours of each other (G in one part and
                          G# in another). Baroque practice hears this as a wrong note even when each
                          part is right on its own, and the injector can create it by writing one
                          voice without looking at the others.

Both are reported with the bar and beat so a fix can be aimed.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import clash  # noqa: E402

SCALE = clash.A_MINOR


def ticks_of(score):
    seen = set()
    for voice in score.voices.values():
        for note in voice.notes:
            seen.add(note[0])
    return sorted(seen)


def out_of_key(score):
    out = []
    for name, voice in sorted(score.voices.items()):
        for start, end, pitch, velocity in voice.notes:
            if pitch % 12 not in SCALE:
                bar, beat = score.bar_beat(start)
                out.append({"voice": name, "bar": bar, "beat": round(beat, 2),
                            "pitch": clash.pitch_name(pitch)})
    return out


def cross_relations(score, within_octave=True):
    """Chromatic neighbour pairs between voices.

    within_octave keeps only pairs close enough to be heard as one clash: a G2 under a G#3 is a
    semitone by pitch class but a ninth apart in fact, and the ear forgives that far more than it
    forgives a G4 against a G#4. Both counts are reported so the choice is visible rather than
    hidden in the filter.
    """
    out = []
    names = sorted(score.voices)
    for tick in ticks_of(score):
        sounding = {name: [n[2] for n in score.voices[name].sounding(tick)] for name in names}
        for i, name_a in enumerate(names):
            for name_b in names[i + 1:]:
                for pitch_a in sounding[name_a]:
                    for pitch_b in sounding[name_b]:
                        gap = abs(pitch_a % 12 - pitch_b % 12)
                        if gap != 1:
                            continue
                        if within_octave and abs(pitch_a - pitch_b) > 12:
                            continue
                        bar, beat = score.bar_beat(tick)
                        out.append({"bar": bar, "beat": round(beat, 2),
                                    "low_voice": name_a, "low": clash.pitch_name(pitch_a),
                                    "high_voice": name_b, "high": clash.pitch_name(pitch_b),
                                    "span": abs(pitch_a - pitch_b)})
    return out


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: keycheck.py FILE [FILE ...]")
        return 2
    for path in argv:
        score = clash.load_score(path)
        outside = out_of_key(score)
        crossings = cross_relations(score)
        all_crossings = cross_relations(score, within_octave=False)
        print("file", os.path.basename(path))
        print("  notes outside the key:", len(outside))
        for row in outside[:10]:
            print("    bar %2d beat %.2f %-14s %s" % (row["bar"], row["beat"], row["voice"],
                                                      row["pitch"]))
        if len(outside) > 10:
            print("    ... %d more" % (len(outside) - 10))
        print("  cross relations, within an octave:", len(crossings),
              " (any span: %d)" % len(all_crossings))
        for row in crossings[:12]:
            print("    bar %2d beat %.2f %-14s %-4s / %-14s %-4s"
                  % (row["bar"], row["beat"], row["low_voice"], row["low"],
                     row["high_voice"], row["high"]))
        if len(crossings) > 12:
            print("    ... %d more" % (len(crossings) - 12))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
