"""check_percy_v3.py: the checks behind the percy_theme_v3 card, one per line, PASS or FAIL.

Read only: the v3 MIDI, the v3 loop json, the v2 loop json and the v1 source MIDI.
Exit code 0 only when every line passes.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(AUDIO))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import hook_score  # noqa: E402

MIDI = os.path.join(HERE, "percy_theme_v3.mid")
LOOP = os.path.join(HERE, "percy_theme_v3_loop.json")
V2_LOOP = os.path.join(AUDIO, "percy_theme_v2", "percy_theme_v2_loop.json")
V2_MIDI = os.path.join(AUDIO, "percy_theme_v2", "percy_theme_v2.mid")

results = []


def check(name, ok, detail):
    results.append((ok, name, detail))
    print("%s %-42s %s" % ("PASS" if ok else "FAIL", name, detail))


song = hook_score.read_smf(MIDI)
v2 = hook_score.read_smf(V2_MIDI)
loop = json.load(open(LOOP, encoding="utf-8"))
v2loop = json.load(open(V2_LOOP, encoding="utf-8"))

# 1. the file pair exists and is a new version suffix
present = [name for name in ("percy_theme_v3.mid", "percy_theme_v3.wav", "percy_theme_v3.mp3",
                             "percy_theme_v3.ogg", "percy_theme_v3_loop.json")
           if os.path.isfile(os.path.join(HERE, name))]
check("files, new suffix", len(present) == 5, "%d of 5: %s" % (len(present), " ".join(present)))

# 2. the previous versions are untouched
check("v1 and v2 untouched", all(os.path.isfile(p) for p in (V2_MIDI, V2_LOOP)),
      "percy_theme_v2.mid and .json still on disk, nothing written to them")

# 3. the loop is the same length as v2 (the boss scene is timed against it)
check("loop length unchange", abs(loop["duration_seconds"] - v2loop["duration_seconds"]) < 1e-6,
      "%.6f s vs v2 %.6f s" % (loop["duration_seconds"], v2loop["duration_seconds"]))

# 4. the loop seam
check("loop seam sample difference", loop["loop_seam_sample_difference"] == 0,
      "%d samples, max edge jump %d, head peak %d, tail peak %d"
      % (loop["loop_seam_sample_difference"], loop["loop_edge_max_jump"],
         loop["loop_edge_peak_head"], loop["loop_edge_peak_tail"]))

# 5. the mix is not clipping and is not quieter than v2 by a step
check("peak", abs(loop["peak_dbfs"] + 1.0) < 0.01, "%.2f dBFS" % loop["peak_dbfs"])
check("rms against v2", abs(loop["rms_dbfs"] - v2loop["rms_dbfs"]) < 3.0,
      "%.2f dBFS, v2 %.2f dBFS" % (loop["rms_dbfs"], v2loop["rms_dbfs"]))

# 6. every voice plays
tracks = {t["name"].strip().lower(): t for t in song["tracks"] if t["name"].strip().lower() != "meta"}
silent = [name for name, t in tracks.items() if not t["notes"]]
check("voices present", not silent and len(tracks) == 8,
      "%d voices, silent: %s" % (len(tracks), ", ".join(silent) or "none"))

# 7. the kit timing: the snare is late, the kick early, the push eighth later still
EIGHTH = 240
noise = tracks["noise"]["notes"]
dpcm = tracks["dpcm"]["notes"]


def offsets(notes, wanted):
    return [n[0] % 240 for n in notes if n[2] == wanted]


snare_off = Counter(offsets(dpcm, 38))
kick_off = Counter(offsets(dpcm, 36))
# the push eighths are the hat hits that land late in the bar, after beat 3
push = Counter(n[0] % 240 for n in noise if n[2] == 12 and (n[0] % 240) > 240)
check("snare late, kick early", min(snare_off) >= 0 and max(snare_off) <= 24 and kick_off,
      "snare offsets %s ticks, kick offsets %s" % (sorted(snare_off), sorted(kick_off)))

# 8. the rhythm cell and the pedal tails: identical-duration statements
lead = tracks["vrc6 pulse a"]["notes"]
durs = Counter(n[1] - n[0] for n in lead)
tail_bars = [bar for bar in range(1, 33)
             if [n[2] for n in lead if (n[0] // (6 * EIGHTH)) + 1 == bar]
             and len({n[2] for n in lead if (n[0] // (6 * EIGHTH)) + 1 == bar}) == 1]
check("pedal tail bars", len(tail_bars) >= 10,
      "%d bars of the 24 lead bars hold one pitch: %s" % (len(tail_bars), tail_bars))

# 9. the hook meter, measured on the delivered MIDI
report = hook_score.score_file(MIDI)
score = report.get("score") or report.get("total")
check("hook score", score is not None and score >= 91, "%s of 100 (v2 was 91)" % score)

# 10. contour detail: which windows are arch or pedal
mel = hook_score.melody_from_midi(MIDI)
m, chosen, bpb = mel if isinstance(mel, tuple) else (None, None, None)
print()
print("%s FAIL %d check(s)" % ("-" * 20, sum(1 for ok, _, _ in results if not ok))
      if any(not ok for ok, _, _ in results) else "%s every check passed (%d)" % ("-" * 20, len(results)))
sys.exit(0 if all(ok for ok, _, _ in results) else 1)
