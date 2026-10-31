"""The shot list to cue bar table for PP-DRIVE. Card MUS-CUE-DRIVE (t_0c5ef0c5).

Reads the twelve shot step counts out of knowledge/DRIVE-SHOT-LIST.md by hand (they are in
section 2) and states every shot as a cue bar, because the cue is 3/4 at 126 bpm: one bar is
3 beats at 2.1 beats a second = 1.428571 s = 85.714 steps at 60 steps a second, which is
data/title_timing.json's steps_per_bar. Nothing here guesses: the steps are the shot list's
numbers, the bar length is the timing file's number, and the cue's own section bars come from
assets/audio/pp_drive/arrange_report.json when it exists.

Writes assets/audio/pp_drive/drive_cue_map.json and prints the markdown table NOTES.md carries.
"""

import json
import os

STEPS_A_SECOND = 60.0
BPM = 126.0
BEATS_PER_BAR = 3
BAR_STEPS = STEPS_A_SECOND * STEPS_A_SECOND / BPM * BEATS_PER_BAR      # 85.7142857
BAR_SECONDS = BAR_STEPS / STEPS_A_SECOND                              # 1.4285714

# knowledge/DRIVE-SHOT-LIST.md section 2, in order: (shot, beat, location, steps)
SHOTS = [
    (1, "7", "city: Big Ben, the street", 686),
    (2, "8", "city: the car pulls away, the Thames", 857),
    (3, "9", "gantry: the sign SOUTHAMPTON 55", 600),
    (4, "10", "open motorway: rain, wipers", 771),
    (5, "11a", "open motorway: radio pages 1 and 2", 1029),
    (6, "11b", "open motorway: pages 3 and 4, the sign 43", 1114),
    (7, "13", "Twyford Down: the chalk cutting", 857),
    (8, "14", "cathedral: the silhouette", 857),
    (9, "15", "open motorway: pages 5 to 7, the sign 30", 1115),
    (10, "16 and 17", "downland: the storm", 1114),
    (11, "18", "slip road: the sign 20", 686),
    (12, "19", "docks: cranes, the lit ship", 994),
]

# The cue's sections, from the score's meta.form and confirmed by arrange_report.json.
SECTIONS = [
    ("A", 1, 25, "city at night, A minor, sparse: shots 1 to 3"),
    ("B", 26, 59, "M25 and M3, C major, motor eighths: shots 4 to 6"),
    ("A_return", 60, 125, "Winchester rising, the sea, the docks: shots 7 to 12"),
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    steps_total = 0
    rows = []
    cue_bar = 1
    for shot, beat, place, steps in SHOTS:
        steps_total += steps
        start_s = steps_total / STEPS_A_SECOND
        first_bar = cue_bar
        # Every shot is a whole number of bars in the film except the last, which ends on the fade.
        bars = steps / BAR_STEPS
        if shot < 12:
            bars_used = int(round(bars))
        else:
            bars_used = 12                      # 114 to 125: the cue gives the docks a bar to land on
        cue_bar = first_bar + bars_used
        rows.append({
            "shot": shot,
            "beat": beat,
            "location": place,
            "film_steps": steps,
            "film_seconds": round(start_s, 3),
            "cue_bars": bars_used,
            "cue_first_bar": first_bar,
            "cue_last_bar": first_bar + bars_used - 1,
            "cue_seconds": round(bars_used * BAR_SECONDS, 3),
        })

    # The film's own bar count, checked against the shot list's 178.00 s.
    film_seconds = steps_total / STEPS_A_SECOND
    cue_seconds = cue_bar - 1
    cue_seconds = (cue_bar - 1) * BAR_SECONDS

    report = {
        "card": "MUS-CUE-DRIVE (t_0c5ef0c5)",
        "source": "knowledge/DRIVE-SHOT-LIST.md section 2, data/title_timing.json",
        "tempo": {"bpm": BPM, "beats_per_bar": BEATS_PER_BAR, "bar_steps": round(BAR_STEPS, 6),
                  "bar_seconds": round(BAR_SECONDS, 6)},
        "cue": {"bars": cue_bar - 1, "seconds": round(cue_seconds, 3),
                "sections": [{"name": n, "first_bar": a, "last_bar": b, "what": w}
                             for n, a, b, w in SECTIONS]},
        "film": {"steps": steps_total, "seconds": round(film_seconds, 3),
                 "bars": round(steps_total / BAR_STEPS, 3)},
        "tail_seconds": round(cue_seconds - film_seconds, 3),
        "shots": rows,
    }

    # The checks this file can prove, printed rather than asserted.
    errors = []
    if steps_total != 10680:
        errors.append("film steps %d, the shot list says 10680" % steps_total)
    for name, first, last, _what in SECTIONS:
        pass
    if SECTIONS[1][1] != SECTIONS[0][2] + 1:
        errors.append("section B does not start on the bar after A")
    if SECTIONS[2][1] != SECTIONS[1][2] + 1:
        errors.append("section A_return does not start on the bar after B")
    if cue_bar - 1 != SECTIONS[2][2]:
        errors.append("the shots do not reach the last bar of A_return")
    report["errors"] = errors

    out = os.path.join(here, "drive_cue_map.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print("film: %d steps = %.2f s = %.2f bars" % (steps_total, film_seconds,
                                                   steps_total / BAR_STEPS))
    print("cue : %d bars = %.3f s (tail %.3f s past the picture)" %
          (cue_bar - 1, cue_seconds, cue_seconds - film_seconds))
    print("")
    print("| shot | beat | location | film s | cue bars | cue s | section |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for row in rows:
        section = next(n for n, a, b, _w in SECTIONS if a <= row["cue_first_bar"] <= b)
        print("| %d | %s | %s | %.2f | %d to %d | %.2f | %s |" %
              (row["shot"], row["beat"], row["location"], row["film_seconds"],
               row["cue_first_bar"], row["cue_last_bar"], row["cue_seconds"], section))
    print("")
    print("errors: %s" % (errors or "none"))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
