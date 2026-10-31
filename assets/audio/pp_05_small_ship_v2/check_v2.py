"""check_v2.py: the checks the PP-05 v2 card asks for, printed as one table.

Reads the v1 and v2 MIDI files and the v2 loop record and proves:
  notes per voice, vibration events (control change 1 and 20), the last note end
  against bar 25 so the loop cannot carry a tail, the noise and pulse 1 levels,
  and the renderer's own loop record.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import hook_score  # noqa: E402

V1 = os.path.join(os.path.dirname(HERE), "pp_05_small_ship", "pp_05_small_ship.mid")
V2 = os.path.join(HERE, "pp_05_small_ship_v2.mid")
LOOP = os.path.join(HERE, "pp_05_small_ship_v2_loop.json")

PPQ = 480
BAR = 8 * PPQ // 2
END = 24 * BAR


def describe(path):
    song = hook_score.read_smf(path)
    rows = []
    for track in song["tracks"]:
        if not track["notes"] and not track["cc"]:
            continue
        vib = len(track["cc"].get(1, [])) + len(track["cc"].get(20, []))
        last = max((n[1] for n in track["notes"]), default=0)
        velocities = sorted({n[3] for n in track["notes"]})
        levels = sorted({v for _, v in track["cc"].get(11, [])})
        rows.append({"name": track["name"], "notes": len(track["notes"]),
                     "vibrato": vib, "last_end": last, "velocities": len(velocities),
                     "cc11": levels})
    return song, rows


def main():
    v1_song, v1 = describe(V1)
    v2_song, v2 = describe(V2)
    print("voice            v1 notes  v2 notes | v1 vib v2 vib | v2 last end | v2 vel steps | v2 cc11")
    names = [r["name"] for r in v2]
    for name in names:
        a = next((r for r in v1 if r["name"] == name), {"notes": 0, "vibrato": 0})
        b = next(r for r in v2 if r["name"] == name)
        print("%-16s %8d %9d | %6d %6d | %11d | %12d | %s"
              % (name, a["notes"], b["notes"], a["vibrato"], b["vibrato"],
                 b["last_end"], b["velocities"], b["cc11"]))
    total_before = sum(r["notes"] for r in v1)
    total_after = sum(r["notes"] for r in v2)
    vib_before = sum(r["vibrato"] for r in v1)
    vib_after = sum(r["vibrato"] for r in v2)
    tail = max(r["last_end"] for r in v2)
    print("\nnotes %d -> %d | vibrato events %d -> %d | last note end %d, bar 25 starts at %d"
          % (total_before, total_after, vib_before, vib_after, tail, END))
    print("tempo_us %d -> %d (unchanged: %s) | division %d"
          % (v1_song["tempo_us"], v2_song["tempo_us"],
             v1_song["tempo_us"] == v2_song["tempo_us"], v2_song["division"]))
    checks = {
        "pulse1_has_notes": next(r["notes"] for r in v2 if r["name"] == "pulse 1") > 0,
        "vibrato_written": vib_after > 0,
        "no_tail_past_bar_25": tail <= END,
        "tempo_unchanged": v1_song["tempo_us"] == v2_song["tempo_us"],
        "note_count_up": total_after > total_before,
    }
    with open(LOOP, encoding="utf-8") as handle:
        loop = json.load(handle)
    seam = loop.get("loop_seam_sample_difference")
    checks["loop_seam_zero"] = seam == 0
    print("loop json: %s" % json.dumps({k: loop[k] for k in loop if k in
                                        ("loop_bars", "loop_seconds", "loop_seam_sample_difference",
                                         "loop_start_sample", "loop_end_sample")}))
    for name, ok in checks.items():
        print("  [%s] %s" % ("pass" if ok else "FAIL", name))
    print("RESULT: %s" % ("PASS" if all(checks.values()) else "FAIL"))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
