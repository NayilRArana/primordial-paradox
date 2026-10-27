"""build_pp01_v9.py: PP-01 "Title Theme" version 9, card t_c0597404 (M0).

Source is v7 (`assets/audio/pp_01_title_v7/pp_01_title_v7.mid`), the version the ear ranked
highest and the file Nayil called "a bit dissonant". Nothing in v7 is edited in place: this
script reads it and writes a new file in this folder.

What v9 is: v7 with its vertical intervals repaired. The melody (vrc6 pulse a) and the drums
(noise, dpcm) are v7's notes, unchanged, so every K, K2, Z, P, H and W statement sounds on the
same beat at the same pitch, and the hook's rhythm is untouched. Every other pitched voice may
move a pitch or drop a note where the clash analyser (tools/counterpoint/clash.py) found an
unprepared, unresolved dissonance. The repairs come from tools/counterpoint/repair.py, which
scores each candidate move by the number of dissonances it would form inside the note's own
span, and which refuses to leave a pad chord that is not a triad.

The two deliberate v7 devices are re-examined by the same rules rather than trusted:

  the DIS-09 anticipation at bar 36 (G4 on the last eighth) and the DIS-04 suspension at bars
  38 to 39 (E5 held into the B7 bar, D#5 on beat 2) are left where v7 put them, and the report
  records what the analyser calls them afterwards.

Form, tempo, metre, bar count and loop point are v7's: A minor, 3/4, 126 bpm, 52 bars, loop
from bar 5. The instrument registers are checked against the v7 build notes.

Usage: build_pp01_v9.py
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(AUDIO))
SRC = os.path.join(AUDIO, "pp_01_title_v7", "pp_01_title_v7.mid")
OUT = os.path.join(HERE, "pp_01_title_v9.mid")
REPORT = os.path.join(HERE, "build_report_v9.json")

sys.path.insert(0, os.path.join(ROOT, "tools", "counterpoint"))
import clash  # noqa: E402
import repair  # noqa: E402

FROZEN = ("vrc6 pulse a", "noise", "dpcm")

RANGES = repair.RANGES


def frozen_check(before, after):
    """Prove the hook and the drums are untouched, note for note."""
    out = {}
    for name in FROZEN:
        old = sorted(before.get(name, []))
        new = sorted(after.get(name, []))
        out[name] = {"notes_before": len(old), "notes_after": len(new), "identical": old == new}
    return out


def register_check(song):
    bad = []
    for name, notes in song.notes.items():
        if name not in RANGES:
            continue
        lo, hi = RANGES[name]
        for start, end, pitch, velocity in notes:
            if not (lo <= pitch <= hi):
                bad.append({"voice": name, "pitch": clash.pitch_name(pitch),
                            "bar": start // 1440 + 1})
    return bad


def device_slots(events, bars):
    """What the analyser calls the two slots v7's injector wrote."""
    wanted = {36: "DIS-09 anticipation", 39: "DIS-04 suspension"}
    out = []
    for event in events:
        if event["bar"] in wanted:
            out.append({"slot": wanted[event["bar"]], "bar": event["bar"],
                        "beat": event["beat"], "pair": event["pair"],
                        "low": event["low"], "high": event["high"],
                        "class": event["class"], "why": event["why"]})
    return out


def main():
    song = repair.Song(SRC)
    original = {name: list(notes) for name, notes in song.notes.items()}

    score_before = song.score()
    events_before = clash.analyse(score_before)
    summary_before = clash.summarise(score_before, events_before)

    history = []
    log, history = repair.repair(song, rounds=12, verbose=True)

    song.write(OUT)
    after = repair.Song(OUT)
    score_after = after.score()
    events_after = clash.analyse(score_after)
    summary_after = clash.summarise(score_after, events_after)

    report = {
        "source": SRC,
        "out": OUT,
        "key": "A minor",
        "time_sig": [3, 4],
        "tempo_bpm": round(after.tempo_us and 60_000_000.0 / after.tempo_us, 2),
        "bars": 52,
        "loop": "bar 5 for 48 bars",
        "frozen": frozen_check(original, after.notes),
        "before": {k: summary_before[k] for k in
                   ("by_class", "raw_total", "strong_raw", "dissonances")},
        "after": {k: summary_after[k] for k in
                  ("by_class", "raw_total", "strong_raw", "dissonances")},
        "rounds": history,
        "edits": len(log),
        "edits_by_voice": {},
        "rests": sum(1 for e in log if e["to"] == "rest"),
        "chord_rewrites": [e for e in log if "+" in e["to"]],
        "residual": [{"bar": e["bar"], "beat": e["beat"], "pair": e["pair"],
                      "low": e["low"], "high": e["high"], "why": e["why"]}
                     for e in events_after if e["class"] == "raw clash"],
        "devices_after": device_slots(events_after, 52),
        "registers": register_check(after),
        "tracks_out": {name: len(notes) for name, notes in sorted(after.notes.items())},
        "hook": {"before": 0, "after": 0},
    }
    for entry in log:
        report["edits_by_voice"][entry["voice"]] = \
            report["edits_by_voice"].get(entry["voice"], 0) + 1

    try:
        import hook_score
        report["hook"]["before"] = hook_score.score_file(SRC, track="vrc6 pulse a")["score"]
        report["hook"]["after"] = hook_score.score_file(OUT, track="vrc6 pulse a")["score"]
    except Exception as error:  # noqa: BLE001
        report["hook"]["error"] = str(error)

    with open(REPORT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")

    print()
    print("raw clashes      %d -> %d" % (summary_before["raw_total"], summary_after["raw_total"]))
    print("on a strong beat %d -> %d" % (summary_before["strong_raw"], summary_after["strong_raw"]))
    for key in clash.CLASSES:
        print("  %-14s %4d -> %4d" % (key, summary_before["by_class"][key],
                                      summary_after["by_class"][key]))
    print("edits", len(log), "rests", report["rests"],
          "chord rewrites", len(report["chord_rewrites"]))
    print("frozen:", {k: v["identical"] for k, v in report["frozen"].items()})
    print("registers out of range:", len(report["registers"]))
    print("hook score", report["hook"]["before"], "->", report["hook"]["after"])
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
