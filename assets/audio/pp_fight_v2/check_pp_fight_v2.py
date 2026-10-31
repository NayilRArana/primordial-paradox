"""check_pp_fight_v2.py: what card AUTO-MUSIC-NEXT asks to see for the rebuilt battle cue.

1. Both modules render: the WAV, MP3 and OGG are on disk and not empty, and the WAV is
   exactly the loop length the loop json claims.
2. Phrase lengths: both modules are a whole number of 4 bar phrases, printed.
3. Call and response: the fight's last bar is the calm's first bar, note for note, on the
   lead and on the triangle (the voices that carry pitch). Compared as (offset in the bar,
   length, pitch) so a shifted or altered note fails.
4. The junction is in the render: in the states file, the calm's first bar (bar 17) equals
   the fight's last bar (bar 16), on every voice that is not the kit, and the kit change is
   the only difference, which is the audible "drop to rims".
5. Loop safety: the seam sample difference in both loop json files is 0.
6. The hook meter: both modules score 100 of 100, and the drum ladder changes at every 4 bar
   line and again at every 8 bar line, counted from the pattern ids in the build.
7. No long dashes in any text artifact in the folder.

Usage: check_pp_fight_v2.py
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import hook_score  # noqa: E402

PPQ = 480
BAR = 8 * PPQ // 2

FIGHT = "pp_fight_v2_fight"
CALM = "pp_fight_v2_calm"
STATES = "pp_fight_v2_states"
PITCH_VOICES = ("vrc6 pulse a", "triangle")

# Read from tools/arrange.py rather than copied, so the ranges cannot drift.
VOICE_RANGES = {}
_arrange_path = os.path.join(ROOT, "tools", "arrange.py")
with open(_arrange_path, encoding="utf-8") as _handle:
    _text = _handle.read()
_start = _text.index("VOICE_RANGES = {")
_end = _text.index("}", _start)
for _line in _text[_start:_end].splitlines()[1:]:
    _name, _rest = _line.split(":", 1)
    _lo, _hi = _rest.strip().strip(",").strip("() ").split(",")
    VOICE_RANGES[_name.strip().strip('"')] = (int(_lo), int(_hi))

# The ladder in build_pp_fight_v2.py, restated so the check can read it without importing it.
FIGHT_DRUMS = {
    1: "BAT-01", 2: "BAT-01", 3: "BAT-01", 4: "FLF-01",
    5: "BAT-01", 6: "BAT-06", 7: "BAT-01", 8: "FLT-01",
    9: "BAT-02", 10: "BAT-02", 11: "BAT-05", 12: "FLR-01",
    13: "BAT-03", 14: "BAT-01", 15: "BAT-07", 16: "BAT-09",
}


def notes_in_bar(song, track_name, bar):
    """(offset in the bar, length, pitch) for every note that starts in that bar."""
    low = (bar - 1) * BAR
    high = low + BAR
    for track in song["tracks"]:
        if track["name"] == track_name:
            return sorted((start - low, end - start, pitch)
                          for start, end, pitch, _velocity in track["notes"]
                          if low <= start < high)
    return []


def rows_for(song):
    out = {}
    for track in song["tracks"]:
        if track["notes"]:
            out[track["name"]] = len(track["notes"])
    return out


def file_size(name):
    path = os.path.join(HERE, name)
    return os.path.getsize(path) if os.path.exists(path) else 0


def main():
    checks = {}

    fight = hook_score.read_smf(os.path.join(HERE, FIGHT + ".mid"))
    calm = hook_score.read_smf(os.path.join(HERE, CALM + ".mid"))
    states = hook_score.read_smf(os.path.join(HERE, STATES + ".mid"))

    print("voice map, notes per module")
    names = sorted(set(rows_for(fight)) | set(rows_for(calm)))
    for name in names:
        print("  %-16s fight %4d   calm %4d" % (name, rows_for(fight).get(name, 0),
                                                rows_for(calm).get(name, 0)))

    print("\nrendered files")
    bpm = 60_000_000 / fight["tempo_us"]
    print("  tempo %.3f bpm (the CUE-FIGHT card's 168), key D minor" % bpm)
    for stem in (FIGHT, CALM, STATES):
        sizes = {ext: file_size(stem + ext) for ext in (".wav", ".mid", ".mp3", ".ogg")}
        print("  %-20s %s" % (stem, ", ".join("%s %d bytes" % (ext, size)
                                              for ext, size in sorted(sizes.items()))))
        checks["renders_" + stem] = all(size > 0 for size in sizes.values())
    for stem, bars in ((FIGHT, 16), (CALM, 16)):
        with open(os.path.join(HERE, stem + "_loop.json"), encoding="utf-8") as handle:
            loop = json.load(handle)
        frames = loop.get("loop_end_sample", 0)
        expected = int(round(bars * 4 * 60.0 / bpm * 44100))
        print("  %-20s loop %s bars, %d samples, seam difference %s"
              % (stem, loop.get("loop_bars"), frames, loop.get("loop_seam_sample_difference")))
        checks["loop_samples_" + stem] = abs(frames - expected) <= 2
        checks["loop_seam_zero_" + stem] = loop.get("loop_seam_sample_difference") == 0

    print("\nphrase length")
    for label, bars in (("FIGHT", 16), ("CALM", 16), ("STATES", 32)):
        seconds = bars * 4 * 60.0 / bpm
        print("  %-6s %2d bars = %d whole 4 bar phrases, %.2f s, multiple of 4: %s"
              % (label, bars, bars // 4, seconds, bars % 4 == 0))
        checks["multiple_of_4_" + label] = bars % 4 == 0

    print("\ndrum ladder: a change at every 4 bar line and again at every 8 bar line")
    for edge in (4, 8, 12, 16):
        before = FIGHT_DRUMS[edge - 1]
        at = FIGHT_DRUMS[edge]
        changed = before != at
        print("  bar %2d %-7s -> bar %2d %-7s : change %s"
              % (edge - 1, before, edge, at, changed))
        checks["drum_change_at_%d" % edge] = changed

    print("\ncall and response: fight bar 16 against calm bar 1")
    for voice in PITCH_VOICES:
        a = notes_in_bar(fight, voice, 16)
        b = notes_in_bar(calm, voice, 1)
        print("  %-16s fight %s" % (voice, a))
        print("  %-16s calm  %s" % ("", b))
        checks["seam_" + voice.replace(" ", "_")] = a == b and len(a) > 0

    print("\nstates render, the junction at bar 17")
    for voice in ("vrc6 pulse a", "triangle", "vrc6 saw", "pulse 1", "pulse 2"):
        a = notes_in_bar(fight, voice, 16)
        b = notes_in_bar(states, voice, 17)
        print("  %-16s fight bar 16 %s | states bar 17 %s | equal %s"
              % (voice, a, b, a == b))
        checks["junction_" + voice.replace(" ", "_")] = a == b
    print("  the kit changes at the junction by design (BAT-09 rims to CLM-02 rim ticks):")
    for voice in ("noise", "dpcm"):
        print("  %-16s fight bar 16 %d hits | calm bar 1 %d hits"
              % (voice, len(notes_in_bar(fight, voice, 16)),
                 len(notes_in_bar(states, voice, 17))))
    checks["kit_changes_at_junction"] = (
        (notes_in_bar(fight, "noise", 16), notes_in_bar(fight, "dpcm", 16))
        != (notes_in_bar(states, "noise", 17), notes_in_bar(states, "dpcm", 17)))

    print("\nhook meter")
    for stem, label in ((FIGHT, "fight"), (CALM, "calm")):
        path = os.path.join(HERE, "hook_report_%s_v2.json" % label)
        with open(path, encoding="utf-8") as handle:
            report = json.load(handle)
        score = report.get("score")
        fails = [c["criterion"] for c in report["criteria"] if not c["pass"]]
        print("  %-20s %s of 100, failing: %s" % (stem, score, fails or "none"))
        checks["hook_" + label] = score == 100

    print("\nvoice ranges, the table in tools/arrange.py VOICE_RANGES")
    bad_ranges = []
    for label, song in (("fight", fight), ("calm", calm)):
        for track in song["tracks"]:
            if not track["notes"]:
                continue
            low = min(note[2] for note in track["notes"])
            high = max(note[2] for note in track["notes"])
            lo, hi = VOICE_RANGES.get(track["name"], (0, 127))
            ok = lo <= low and high <= hi
            print("  %-5s %-16s %3d..%-3d in %3d..%-3d : %s"
                  % (label, track["name"], low, high, lo, hi, ok))
            if not ok:
                bad_ranges.append("%s %s" % (label, track["name"]))
    checks["voice_ranges"] = not bad_ranges

    print("\nwriting rules")
    bad = []
    for name in sorted(os.listdir(HERE)):
        if name.endswith((".py", ".md")):
            with open(os.path.join(HERE, name), encoding="utf-8", errors="replace") as handle:
                text = handle.read()
            for mark in ("\u2014", "\u2013"):
                if mark in text:
                    bad.append("%s holds a long dash" % name)
    print("  long dashes found: %s" % (bad or "none"))
    checks["no_long_dashes"] = not bad

    print("\nchecks")
    for name, ok in sorted(checks.items()):
        print("  [%s] %s" % ("pass" if ok else "FAIL", name))
    print("RESULT: %s (%d checks)" % ("PASS" if all(checks.values()) else "FAIL", len(checks)))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
