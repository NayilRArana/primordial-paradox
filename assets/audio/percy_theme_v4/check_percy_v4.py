"""check_percy_v4.py: the checks behind the percy_theme_v4 card, one per line, PASS or FAIL.

Read only: the v4 MIDI, the v4 loop json, the v2 and v3 loop jsons. Exit code 0 only when every
line passes.
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

MIDI = os.path.join(HERE, "percy_theme_v4.mid")
LOOP = os.path.join(HERE, "percy_theme_v4_loop.json")
V2_LOOP = os.path.join(AUDIO, "percy_theme_v2", "percy_theme_v2_loop.json")
V3_LOOP = os.path.join(AUDIO, "percy_theme_v3", "percy_theme_v3_loop.json")
V3_MIDI = os.path.join(AUDIO, "percy_theme_v3", "percy_theme_v3.mid")

results = []


def check(name, ok, detail):
    results.append((ok, name, detail))
    print("%s %-40s %s" % ("PASS" if ok else "FAIL", name, detail))


song = hook_score.read_smf(MIDI)
v3 = hook_score.read_smf(V3_MIDI)
loop = json.load(open(LOOP, encoding="utf-8"))
v2loop = json.load(open(V2_LOOP, encoding="utf-8"))
v3loop = json.load(open(V3_LOOP, encoding="utf-8"))

present = [name for name in ("percy_theme_v4.mid", "percy_theme_v4.wav", "percy_theme_v4.mp3",
                             "percy_theme_v4.ogg", "percy_theme_v4_loop.json")
           if os.path.isfile(os.path.join(HERE, name))]
check("files, new suffix", len(present) == 5, "%d of 5: %s" % (len(present), " ".join(present)))

check("v1, v2, v3 untouched", all(os.path.isfile(p) for p in (V2_LOOP, V3_LOOP, V3_MIDI)),
      "percy_theme_v2 and percy_theme_v3 still on disk, nothing written to them")

check("loop length unchanged", abs(loop["duration_seconds"] - v2loop["duration_seconds"]) < 1e-6,
      "%.6f s, v2 %.6f s, v3 %.6f s"
      % (loop["duration_seconds"], v2loop["duration_seconds"], v3loop["duration_seconds"]))

check("loop seam sample difference", loop["loop_seam_sample_difference"] == 0,
      "%d samples, max edge jump %d, head peak %d, tail peak %d"
      % (loop["loop_seam_sample_difference"], loop["loop_edge_max_jump"],
         loop["loop_edge_peak_head"], loop["loop_edge_peak_tail"]))

check("peak", abs(loop["peak_dbfs"] + 1.0) < 0.01, "%.2f dBFS" % loop["peak_dbfs"])
check("rms against v2", abs(loop["rms_dbfs"] - v2loop["rms_dbfs"]) < 3.0,
      "%.2f dBFS, v2 %.2f dBFS" % (loop["rms_dbfs"], v2loop["rms_dbfs"]))

tracks = {t["name"].strip().lower(): t for t in song["tracks"]
          if t["name"].strip().lower() != "meta"}
silent = [name for name, t in tracks.items() if not t["notes"]]
check("voices present", not silent and len(tracks) == 8,
      "%d voices, silent: %s" % (len(tracks), ", ".join(silent) or "none"))

dpcm = tracks["dpcm"]["notes"]
snare = [n for n in dpcm if n[2] == 38]
quiet = [n for n in snare if n[3] <= 56]
flam = [n for n in snare if (n[0] % 1440) in (940, 941, 942, 943)]
check("ghost notes in the kit", len(quiet) >= 8,
      "%d of %d snare hits at 56 velocity or below (ghosts), %d flam grace hits"
      % (len(quiet), len(snare), len(flam)))

offsets = Counter(n[0] % 240 for n in dpcm)
check("snare late, kick early", 10 in offsets,
      "dpcm onset offsets mod 240: %s ticks" % sorted(offsets))

lead = tracks["vrc6 pulse a"]["notes"]
tail_bars = [bar for bar in range(1, 33)
             if [n for n in lead if (n[0] // 1440) + 1 == bar]
             and len({n[2] for n in lead if (n[0] // 1440) + 1 == bar}) == 1]
check("pedal tail bars", len(tail_bars) >= 10,
      "%d lead bars hold one pitch: %s" % (len(tail_bars), tail_bars))

report = hook_score.score_file(MIDI)
score = report.get("score") or report.get("total")
v3report = hook_score.score_file(V3_MIDI)
v3score = v3report.get("score") or v3report.get("total")
check("hook meter", score is not None and score >= 91,
      "%s of 100, v3 %s, v2 91" % (score, v3score))

print()
bad = sum(1 for ok, _, _ in results if not ok)
print(("%d check(s) failed" % bad) if bad else "every check passed (%d)" % len(results))
sys.exit(0 if bad == 0 else 1)
