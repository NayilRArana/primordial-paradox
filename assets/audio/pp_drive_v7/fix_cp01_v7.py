#!/usr/bin/env python3
"""pp_drive_v7: close the one CP-01 the v6 pass could not reach, by moving a sustaining accompaniment note.

Card t_16784440 (AUTO-MUSIC-NEXT, musician), 2026-11-14. Source: assets/audio/pp_drive_v6/pp_drive_v6.mid.
The melody voice (vrc6 pulse a) is never touched. Every accompaniment note onset stays where it is
except the one note that is split so it can change pitch under the sustained chord.

The judge is the project's own engine (tools/counterpoint/rules.py, load_score + analyse), not a
reimplementation: a candidate is accepted only when CP-01 + CP-09 falls and the hard count does not rise.

Usage: python fix_cp01_v7.py                         # dry run, prints the winner
       python fix_cp01_v7.py --write                 # writes assets/audio/pp_drive_v7/
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time

REPO = r"<repo>"
CP = os.path.join(REPO, "tools", "counterpoint")
for p in (CP, os.path.join(REPO, "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

import repair as clash_repair  # noqa: E402
import rules  # noqa: E402

SRC = os.path.join(REPO, "assets", "audio", "pp_drive_v6", "pp_drive_v6.mid")
OUT_DIR = os.path.join(REPO, "assets", "audio", "pp_drive_v7")
HOOK = "vrc6 pulse a"
# A minor with the raised leading tone, the key the v6 repair pass was told to stay in.
KEY_PCS = {9, 11, 0, 2, 4, 5, 7, 8}
BAR, BEAT = 81, 1.0
# The voices the v6 notes call "the repair at bar 81 belongs to pulse 1/pulse 2", plus the
# inner voices; sorted by how little the move disturbs the texture (sustain first).
MOVABLE = ("pulse 2", "pulse 1", "vrc6 pulse b", "triangle", "vrc6 saw")


def measure(path):
    score = rules.load_score(path)
    result = rules.analyse(score, profile="free")
    by_rule = result["summary"]["by_rule"]
    return {
        "cp01": by_rule.get("CP-01", 0),
        "cp09": by_rule.get("CP-09", 0),
        "hard": result["summary"]["by_severity"]["hard"],
        "open": by_rule.get("CP-01", 0) + by_rule.get("CP-09", 0),
    }


def main():
    write = "--write" in sys.argv
    forced = None
    if "--force-pitch" in sys.argv:
        forced = sys.argv[sys.argv.index("--force-pitch") + 1].strip().upper()
    song = clash_repair.Song(SRC)
    ss = song.score()
    tick = int(round((BAR - 1) * ss.bar_ticks + (BEAT - 1.0) * ss.ticks_per_beat))
    tmpdir = tempfile.mkdtemp(prefix="pp_cp01_")
    probe = os.path.join(tmpdir, "probe.mid")
    song.write(probe)
    t0 = time.time()
    base = measure(probe)
    print("base: CP-01 %d CP-09 %d hard %d  (one analyse takes %.1f s)"
          % (base["cp01"], base["cp09"], base["hard"], time.time() - t0))

    targets = []
    for name in MOVABLE:
        if name not in song.notes:
            continue
        for i, (start, end, pitch, vel) in enumerate(song.notes[name]):
            if start <= tick < end:
                targets.append((name, i, start, end, pitch))
    if not targets:
        print("no accompaniment note sounds at bar %d beat %s" % (BAR, BEAT))
        return 1

    best = None
    for name, i, start, end, pitch in targets:
        for delta in (1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 7, -7):
            cand = pitch + delta
            if cand < 40 or cand > 88 or cand % 12 not in KEY_PCS:
                continue
            if forced and rules.pitch_name(cand).strip().upper() != forced:
                continue
            # Mode A: the whole note takes the new pitch (only when it attacks here).
            # Mode B: the note is split at the tick and only the rest under the clash moves.
            modes = []
            if start == tick:
                modes.append(("whole", [(start, end, cand, vel)]))
            if start < tick and tick < end:
                modes.append(("split", [(start, tick, pitch, vel), (tick, end, cand, vel)]))
            for mode, replacement in modes:
                original = song.notes[name][i]
                song.notes[name][i:i + 1] = replacement
                song.write(probe)
                got = measure(probe)
                song.notes[name][i:i + len(replacement)] = [original]
                key = (got["open"], got["hard"], abs(delta), mode != "split")
                print("  %-14s %s %+d (%s) -> CP-01 %d CP-09 %d hard %d"
                      % (name, rules.pitch_name(pitch), delta, mode,
                         got["cp01"], got["cp09"], got["hard"]))
                if best is None or key < best[0]:
                    best = (key, name, i, mode, replacement, got, delta)

    if best is None:
        print("no candidate found")
        return 1
    key, name, i, mode, replacement, got, delta = best
    print("best: %s %s in mode %s -> CP-01 %d CP-09 %d hard %d"
          % (name, rules.pitch_name(replacement[-1][2]), mode, got["cp01"], got["cp09"], got["hard"]))
    if key[0] >= base["open"] and key[1] >= base["hard"]:
        print("no candidate improves the counts; nothing written")
        return 1
    if not write:
        print("dry run only; pass --write to save")
        return 0

    os.makedirs(OUT_DIR, exist_ok=True)
    original = song.notes[name][i] if mode == "whole" else song.notes[name][i]
    song.notes[name][i:i + 1] = replacement
    out = os.path.join(OUT_DIR, "pp_drive_v7.mid")
    song.write(out)
    after = measure(out)
    # Melody frozen: every hook note identical, pitch and timing.
    a = clash_repair.Song(SRC)
    b = clash_repair.Song(out)
    hook_same = a.notes[HOOK] == b.notes[HOOK]
    print("wrote %s (%d bytes)" % (out, os.path.getsize(out)))
    print("after: CP-01 %d CP-09 %d hard %d" % (after["cp01"], after["cp09"], after["hard"]))
    print("hook voice identical: %s (%d notes)" % (hook_same, len(b.notes[HOOK])))
    report = {
        "card": "t_16784440",
        "source": SRC,
        "out": out,
        "target": {"bar": BAR, "beat": BEAT, "tick": tick},
        "before": base,
        "after": after,
        "edit": {"voice": name, "mode": mode,
                 "from": rules.pitch_name(original[2]),
                 "to": rules.pitch_name(replacement[-1][2]),
                 "delta": delta,
                 "note_before": list(original), "notes_after": [list(r) for r in replacement]},
        "hook_voice_identical": hook_same,
        "hook_notes": len(b.notes[HOOK]),
        "seconds": ss.ticks_per_beat,
    }
    with open(os.path.join(OUT_DIR, "cp01_fix_report_v7.json"), "w", encoding="utf-8") as h:
        json.dump(report, h, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
