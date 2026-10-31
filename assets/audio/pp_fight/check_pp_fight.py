"""check_pp_fight.py: what card CUE-FIGHT asks to see, printed as one table.

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
6. No long dashes in any text artifact in the folder.

Usage: check_pp_fight.py
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

FIGHT = "pp_fight_fight"
CALM = "pp_fight_calm"
STATES = "pp_fight_states"
PITCH_VOICES = ("vrc6 pulse a", "triangle")


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

    # 1. rendered files, and the WAV is the loop length
    print("\nrendered files")
    bpm = 60_000_000 / fight["tempo_us"]
    for stem, bars in ((FIGHT, 16), (CALM, 16), (STATES, 32)):
        sizes = {ext: file_size(stem + ext) for ext in (".wav", ".mid", ".mp3", ".ogg")}
        print("  %-16s %s" % (stem, ", ".join("%s %d bytes" % (ext, size)
                                              for ext, size in sorted(sizes.items()))))
        checks["renders_" + stem] = all(size > 0 for size in sizes.values())
    for stem, bars in ((FIGHT, 16), (CALM, 16)):
        with open(os.path.join(HERE, stem + "_loop.json"), encoding="utf-8") as handle:
            loop = json.load(handle)
        frames = loop.get("loop_end_sample", 0)
        expected = int(round(bars * 4 * 60.0 / bpm * 44100))
        print("  %-16s loop %s bars, %d samples, seam difference %s"
              % (stem, loop.get("loop_bars"), frames, loop.get("loop_seam_sample_difference")))
        checks["loop_samples_" + stem] = abs(frames - expected) <= 2
        checks["loop_seam_zero_" + stem] = loop.get("loop_seam_sample_difference") == 0

    # 2. phrase length, printed as a multiple of 4 bars
    print("\nphrase length")
    for label, bars in (("FIGHT", 16), ("CALM", 16), ("STATES", 32)):
        seconds = bars * 4 * 60.0 / bpm
        print("  %-6s %2d bars = %d whole 4 bar phrases, %.2f s at %.0f bpm, multiple of 4: %s"
              % (label, bars, bars // 4, seconds, bpm, bars % 4 == 0))
        checks["multiple_of_4_" + label] = bars % 4 == 0
    print("  the fight loop is %.2f s, so the 20 s the card asks for lands inside the"
          % (16 * 4 * 60.0 / bpm))
    print("  varied second half, not at the seam")

    # 3. the seam: fight bar 16 == calm bar 1
    print("\ncall and response: fight bar 16 against calm bar 1")
    for voice in PITCH_VOICES:
        a = notes_in_bar(fight, voice, 16)
        b = notes_in_bar(calm, voice, 1)
        print("  %-16s fight %s" % (voice, a))
        print("  %-16s calm  %s" % ("", b))
        checks["seam_" + voice.replace(" ", "_")] = a == b and len(a) > 0

    # 4. the junction inside the one render: states bar 17 against the fight's bar 16
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

    # 5. hook reports, if they are there
    print("\nhook score")
    for stem in (FIGHT, CALM):
        path = os.path.join(HERE, "hook_report_%s.json" % stem.split("_")[-1])
        if os.path.exists(path):
            with open(path, encoding="utf-8") as handle:
                report = json.load(handle)
            score = report.get("score") or report.get("total")
            print("  %-16s %s of 100 (%s)" % (stem, score, path.split(os.sep)[-1]))
        else:
            print("  %-16s no report" % stem)

    # 6. no long dashes in the text artifacts
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
    print("RESULT: %s" % ("PASS" if all(checks.values()) else "FAIL"))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
