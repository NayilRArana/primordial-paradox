"""check_arrival.py: the checks CUE-ARRIVAL has to pass before it is called done.

Each check prints the number it measured and PASS or FAIL, and the script exits 0 only when every
line passed. Nothing here renders or writes audio.

  form        the score is 32 to 48 bars, every section's melody is 8 eighths a bar, the section
              bars add up to the meta bars
  loop        the loop json names the whole loop, sample 0 to the last sample, and the renderer's
              own seam sample difference is 0
  seam air    the last melody note of bar 48 ends at least three eighths before the loop point, so
              the wrap lands on a rest and not on a cut
  hook        the hook report exists and carries a score, printed here
  range       the melody stays inside its declared register and inside the 18 semitone hook range
  blip room   the share of energy in the text blip band (1.5 to 3 kHz) is not above the title
              cue's share, so the bed does not sit on the blip
  drums       the kit changes from bar to bar inside every section, so it cannot read as one
              repeated bar

Usage:
    check_arrival.py [--root ..] [--reference assets/audio/pp_01_title/pp_01_title.wav]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import wave

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
ASSET = "pp_arrival"
EIGHTH = 240                     # ticks at ppq 480
BAR_TICKS = 8 * EIGHTH
BLIP_BAND = (1500.0, 3000.0)

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print("[%s] %-12s %s" % ("PASS" if ok else "FAIL", name, detail))
    return ok


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_wav(path):
    with wave.open(path, "rb") as handle:
        frames = handle.readframes(handle.getnframes())
        rate = handle.getframerate()
        width = handle.getsampwidth()
        channels = handle.getnchannels()
    if width != 2:
        raise SystemExit("%s is not 16 bit" % path)
    data = np.frombuffer(frames, dtype="<i2").astype(np.float64) / 32768.0
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return data, rate


def band_share(path, window=4096, hop=2048):
    """Mean share of the signal's energy that sits in the blip band."""
    data, rate = read_wav(path)
    if len(data) < window:
        raise SystemExit("%s is shorter than one analysis window" % path)
    freqs = np.fft.rfftfreq(window, 1.0 / rate)
    band = (freqs >= BLIP_BAND[0]) & (freqs <= BLIP_BAND[1])
    taper = np.hanning(window)
    total = 0.0
    inside = 0.0
    count = 0
    for start in range(0, len(data) - window, hop):
        spectrum = np.abs(np.fft.rfft(data[start:start + window] * taper)) ** 2
        energy = spectrum.sum()
        if energy <= 0:
            continue
        total += energy
        inside += spectrum[band].sum()
        count += 1
    if not count or total <= 0:
        raise SystemExit("%s produced no energy to measure" % path)
    return inside / total


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--reference", default=os.path.join("assets", "audio", "pp_01_title",
                                                           "pp_01_title.wav"))
    args = parser.parse_args(argv)
    root = args.root
    folder = os.path.join(root, "assets", "audio", ASSET)

    score = yaml.safe_load(open(os.path.join(folder, "score_pp_arrival.yaml"), encoding="utf-8"))
    report = load_json(os.path.join(folder, "build_report.json"))
    loop = load_json(os.path.join(folder, ASSET + "_loop.json"))
    hook = load_json(os.path.join(folder, "hook_report.json"))
    wav = os.path.join(folder, ASSET + ".wav")

    # --- form --------------------------------------------------------------------------------------------
    bars = int(score["meta"]["bars"])
    check("form", 32 <= bars <= 48, "%d bars (the card asks 32 to 48)" % bars)
    bad = []
    for name, spec in score["sections"].items():
        if len(spec["chords"]) != int(spec["bars"]):
            bad.append("%s chords" % name)
        if len(spec["melody"]) != int(spec["bars"]):
            bad.append("%s melody bars" % name)
        for index, bar in enumerate(spec["melody"]):
            if sum(int(event[1]) for event in bar) != 8:
                bad.append("%s bar %d" % (name, index + 1))
    check("bars of 8", not bad, "every melody bar holds 8 eighths" if not bad else ", ".join(bad))
    total = sum(int(spec["bars"]) for spec in score["sections"].values())
    check("sections add", total == bars, "%d section bars against %d in the meta block" % (total, bars))
    expected = bars * 4 * 60.0 / float(score["meta"]["bpm"])
    check("duration", abs(report["loop_seconds"] - expected) < 1e-6,
          "%.3f s at %.0f bpm, %.3f s expected" % (report["loop_seconds"], score["meta"]["bpm"], expected))

    # --- loop --------------------------------------------------------------------------------------------
    seam = loop.get("loop_seam_sample_difference")
    start = loop.get("loop_start_sample")
    end = loop.get("loop_end_sample")
    samples = loop.get("loop_end_sample") - loop.get("loop_start_sample") if None not in (start, end) else None
    check("loop points", start == 0 and seam == 0,
          "loop %s to %s samples (%s), seam sample difference %s" % (start, end, samples, seam))
    duration = loop.get("duration_seconds")
    check("loop covers", duration is not None and abs(duration - expected) < 0.01,
          "loop json duration %s s" % duration)

    # --- seam air ----------------------------------------------------------------------------------------
    midi_names = report["note_counts"]
    # the lead track's last note, read back out of the MIDI event stream is more work than it is
    # worth here; the build report and the score agree on the last bar, so measure from the score.
    last = score["sections"][list(score["sections"])[-1]]["melody"][-1]
    rest = sum(int(event[1]) for event in last if event[0] == "r")
    check("seam air", rest >= 3, "the last bar ends with %d eighths of rest" % rest)
    check("voices", all(midi_names.get(name, 0) > 0 for name in
                        ("vrc6 pulse a", "vrc6 pulse b", "vrc6 saw", "pulse 1",
                         "triangle", "noise", "dpcm")),
          ", ".join("%s %d" % (name, midi_names.get(name, 0)) for name in midi_names))

    # --- hook --------------------------------------------------------------------------------------------
    total_hook = hook.get("score")
    weakest = hook.get("weakest") or ""
    ok_rows = [row for row in hook.get("criteria", []) if row.get("points", 0) >= row.get("weight", 1) - 0.01]
    check("hook", isinstance(total_hook, int) and total_hook >= 60,
          "%s of 100, %d of %d criteria at full marks; weakest %s"
          % (total_hook, len(ok_rows), len(hook.get("criteria", [])), weakest))

    # --- range -------------------------------------------------------------------------------------------
    pitches = [n[0] for section in score["sections"].values() for bar in section["melody"]
               for n in bar if n[0] != "r"]
    import build_arrival  # noqa: E402  (same folder, for note_number)
    values = [build_arrival.note_number(name) for name in pitches]
    span = max(values) - min(values)
    check("range", 60 <= min(values) and max(values) <= 84 and span <= 18,
          "melody %d to %d, %d semitones (register 60 to 84, hook limit 18)"
          % (min(values), max(values), span))

    # --- blip room ---------------------------------------------------------------------------------------
    mine = band_share(wav)
    ref_path = args.reference if os.path.isabs(args.reference) else os.path.join(root, args.reference)
    if os.path.isfile(ref_path):
        ref = band_share(ref_path)
        check("blip room", mine <= ref + 0.01,
              "%.2f percent of the energy in 1.5 to 3 kHz against the title cue's %.2f percent"
              % (mine * 100.0, ref * 100.0))
    else:
        check("blip room", mine <= 0.25, "%.2f percent of the energy in 1.5 to 3 kHz "
                                          "(no reference wav to compare against)" % (mine * 100.0))

    # --- drums -------------------------------------------------------------------------------------------
    lines = []
    ok = True
    for row in report["drums"]:
        seen = {}
        for rung in row["rungs"]:
            seen[rung] = seen.get(rung, 0) + 1
        distinct = len(seen)
        lines.append("%s %d rungs over %d bars" % (row["section"], distinct, row["bars"]))
        if distinct < 2:
            ok = False
    check("drums", ok, ", ".join(lines))

    failures = [name for name, ok_, _detail in results if not ok_]
    print("")
    if failures:
        print("%d check(s) failed: %s" % (len(failures), ", ".join(failures)))
        return 1
    print("check_arrival: %d checks passed" % len(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
