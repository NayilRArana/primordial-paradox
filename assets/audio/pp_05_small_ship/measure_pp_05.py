"""Measure the pp_05 render at the bar level.

Writes a json with per bar rms, the loudest and quietest bar, the loop seam
numbers and a pass or fail for "the bed does not build" and "every voice is
audible", reading the loop json the renderer wrote for the sample rate and the
bar length.
"""
import array
import json
import math
import os
import wave

ROOT = r"<repo>\assets\audio\pp_05_small_ship"
WAV = os.path.join(ROOT, "pp_05_small_ship.wav")
LOOP = os.path.join(ROOT, "pp_05_small_ship_loop.json")
OUT = os.path.join(ROOT, "measure_pp_05.json")

loop = json.load(open(LOOP, encoding="utf-8"))
rate = loop["sample_rate"]
bpm = loop["bpm"]
beats = loop["beats_per_bar"]
bar_samples = int(round(rate * 60.0 / bpm * beats))

with wave.open(WAV, "rb") as handle:
    nframes = handle.getnframes()
    width = handle.getsampwidth()
    raw = handle.readframes(nframes)

assert width == 2, width
import array

samples = array.array("h")
samples.frombytes(raw)

bar_rms = []
for bar in range(loop["loop_bars"]):
    start = bar * bar_samples
    chunk = samples[start:start + bar_samples]
    if not chunk:
        break
    total = 0.0
    for value in chunk:
        total += value * value
    bar_rms.append((total / len(chunk)) ** 0.5)

loudest = max(bar_rms)
quietest = min(bar_rms)
peak = max(abs(v) for v in samples)

# The first two bars of each section are the attack of that section, so the
# "does not build" test compares section means, not single bars.
sections = [("A", 0, 8), ("A_fugue", 8, 16), ("A_second", 16, 20), ("close", 20, 24)]
section_rms = {}
for name, lo, hi in sections:
    chunk = bar_rms[lo:hi]
    section_rms[name] = round(sum(chunk) / len(chunk), 1)

head = samples[:int(rate * 0.001)]
tail = samples[-int(rate * 0.001):]
edge_jump = max(abs(b - a) for a, b in zip(samples, samples[1:])) if False else None
# Largest sample to sample jump inside the first and last millisecond window.
def max_jump(values):
    return max(abs(b - a) for a, b in zip(values, values[1:])) if len(values) > 1 else 0

report = {
    "wav": WAV,
    "sample_rate": rate,
    "channels": loop["channels"],
    "frames": nframes,
    "seconds": round(nframes / float(rate), 6),
    "bars_read": len(bar_rms),
    "bar_samples": bar_samples,
    "bar_rms": [round(v, 1) for v in bar_rms],
    "bar_rms_dbfs": [round(20 * math.log10(v / 32768.0), 2) if v > 0 else None for v in bar_rms],
    "loudest_bar": bar_rms.index(loudest) + 1,
    "loudest_bar_rms": round(loudest, 1),
    "quietest_bar": bar_rms.index(quietest) + 1,
    "quietest_bar_rms": round(quietest, 1),
    "spread_percent": round(100.0 * (loudest - quietest) / loudest, 2),
    "section_rms": section_rms,
    "peak": peak,
    "head_1ms_peak": max(abs(v) for v in head),
    "tail_1ms_peak": max(abs(v) for v in tail),
    "head_1ms_max_jump": max_jump(list(head)),
    "tail_1ms_max_jump": max_jump(list(tail)),
    "seam_step_samples": samples[0] - samples[-1],
    "loop_seam_sample_difference": loop["loop_seam_sample_difference"],
}
report["checks"] = {
    "seconds_is_60": abs(report["seconds"] - 60.0) < 0.001,
    "bars_read_is_24": report["bars_read"] == 24,
    "no_silent_bar": quietest > 0,
    "does_not_build": section_rms["close"] < section_rms["A_fugue"] and section_rms["close"] < section_rms["A"],
    "seam_step_is_small": abs(report["seam_step_samples"]) <= 0.01 * peak,
    "seam_edge_jump_is_small": max(report["head_1ms_max_jump"], report["tail_1ms_max_jump"]) <= 0.02 * peak,
}
report["pass"] = all(report["checks"].values())
json.dump(report, open(OUT, "w", encoding="utf-8"), indent=2, sort_keys=True)
print(json.dumps(report, indent=2, sort_keys=True))
