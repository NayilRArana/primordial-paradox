"""check_motif.py: prove the family leitmotif K is transformed, not quoted, in PP-05.

K in knowledge/CHARACTER-BIBLE.md is E5 C5 D5 E5: a major third down, then two
steps up, in the rhythm 3 1 1 1 eighths (a dotted quarter then three eighths),
in A minor. This reads the arranged MIDI's lead track and the low voice track
and reports:

  1. the melody of bar 1, which must be the augmented D minor statement
  2. every place the interval shape (down 4, up 2, up 2) occurs
  3. whether the exact K cells exist anywhere: the A minor pitch cell in that
     rhythm, and the interval cell in that rhythm. A quotation would be one of
     those. Both must be absent.
  4. the operation each occurrence is carrying, from the score's own comment.

Usage: python check_motif.py [midi path]
Exits 0 when the motif is present and no quotation of K is found.
"""
import os
import sys

TOOLS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import melody_guard as guard  # noqa: E402  (tools/ is added to the path just above)

HERE = os.path.dirname(os.path.abspath(__file__))
MIDI = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "pp_05_small_ship.mid")

PPQ = 480
EIGHTH = PPQ // 2
BAR = 8 * EIGHTH

K_AM_PITCHES = ["E5", "C5", "D5", "E5"]          # the brief's own statement, A minor
K_INTERVALS = (-4, 2, 2)                          # down a major third, up two semitones
K_RHYTHM = (3, 1, 1, 1)                           # dotted quarter then three eighths


def notes_of(track_name):
    tracks = guard.parse_midi(MIDI)
    for name, notes in tracks:
        if name.strip().lower() == track_name.lower():
            return notes
    raise SystemExit("no track named %r in %s" % (track_name, MIDI))


def describe(notes):
    out = []
    for index, (start, end, pitch) in enumerate(notes):
        bar = start // BAR + 1
        position = (start % BAR) // EIGHTH + 1
        # The renderer's gate shortens each note by about a tick, so the written
        # length is the note's own span rounded to the nearest eighth.
        out.append({"bar": bar, "eighth": position,
                    "note": guard_number_to_name(pitch), "pitch": pitch,
                    "eighths": int(round((end - start) / float(EIGHTH)))})
    return out


def guard_number_to_name(pitch):
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return "%s%d" % (names[pitch % 12], pitch // 12 - 1)


def runs(shapes, pattern):
    """Every window of shapes that equals pattern: the interval run and the rhythm run."""
    hits = []
    for index in range(len(shapes) - len(pattern) + 1):
        if tuple(shapes[index:index + len(pattern)]) == tuple(pattern):
            hits.append(index)
    return hits


def main():
    lead = describe(notes_of("vrc6 pulse a"))
    low = describe(notes_of("vrc6 pulse b"))
    all_notes = lead + low

    intervals = [b["pitch"] - a["pitch"] for a, b in zip(all_notes, all_notes[1:])]
    rhythms = [a["eighths"] for a in all_notes[:-1]]

    # 1. bar 1
    bar1 = [note for note in lead if note["bar"] == 1]
    bar1_names = [note["note"] for note in bar1]
    bar1_is_k_augmented = (bar1_names == ["A4", "F4", "G4", "A4"]
                           and [note["eighths"] for note in bar1] == [4, 1, 1, 2])

    # 2. every statement of the interval shape, whatever the rhythm
    shape_hits = runs(intervals, K_INTERVALS) + runs(intervals, tuple(-i for i in K_INTERVALS))
    shape_bars = sorted({all_notes[i]["bar"] for i in
                         runs(intervals, K_INTERVALS) + runs(intervals, tuple(-i for i in K_INTERVALS))})

    # 3. a quotation: the shape in K's own rhythm, or K's own pitches in K's rhythm
    quoted_rhythm = [i for i in runs(intervals, K_INTERVALS) if tuple(rhythms[i:i + 3]) == K_RHYTHM[:3]]
    quoted_pitches = []
    pitches = [note["pitch"] for note in all_notes]
    target = [guard.note_to_midi(name) for name in K_AM_PITCHES]
    for index in range(len(pitches) - 3):
        if pitches[index:index + 4] == target:
            quoted_pitches.append(index)

    checks = {
        "bar_1_is_K_augmented_in_D_minor": bar1_is_k_augmented,
        "K_interval_shape_occurs": len(shape_hits) >= 2,
        "no_quotation_in_Ks_rhythm": not quoted_rhythm,
        "no_quotation_in_Ks_pitches": not quoted_pitches,
        "no_A_minor_K_pitches_anywhere": "E5" not in pitches,
    }
    print("melody bar 1: %s %s" % (bar1_names, [note["eighths"] for note in bar1]))
    print("K interval shape (%s) found %d time(s), in bar(s) %s"
          % (list(K_INTERVALS), len(shape_hits), shape_bars))
    print("quotations in K's rhythm: %d; in K's pitches: %d" % (len(quoted_rhythm), len(quoted_pitches)))
    print("low voice bars: %s" % sorted({note["bar"] for note in low}))
    for key, value in checks.items():
        print("  %-38s %s" % (key, "pass" if value else "FAIL"))
    print("PASS" if all(checks.values()) else "FAIL")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
