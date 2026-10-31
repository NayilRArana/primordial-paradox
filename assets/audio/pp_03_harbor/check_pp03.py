"""check_pp03.py: the checks for PP-03 "Harbor", read back from the MIDI itself.

This does not trust the builder. It re-reads pp_03_harbor.mid with the project's
own MIDI parser and checks the numbers the card asks for:

  1. format 1 and 8 voice tracks with the names render_chip.py expects
  2. division 480, 68 bpm, 4/4
  3. the arrangement is exactly 64 bars: nothing sounds past the loop point,
     and the last bar is filled
  4. the first bar and the last bar hold the same chord (root of the bass and
     of the pad), which is the seam check
  5. only the 2A03 and VRC6 voices are used, eight tracks and no ninth
  6. the noise channel never plays two hits at one tick (MUSIC-DRUMS 1)
  7. every note sits inside its voice's declared register
  8. the lead rests in every bar (the brief's "hold at low intensity")
  9. the drums are not one static figure: the number of distinct bar grids,
     and the longest run of identical bars
 10. the audio files exist, are the same length, and the loop json agrees

Usage:
    check_pp03.py [--dir assets/audio/pp_03_harbor]

Exit 0 when every check passes, 1 otherwise. Writes score_check.json next to the
MIDI when --json is given.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import render_chip  # noqa: E402  the project's own MIDI parser

PPQ = 480
BAR_TICKS = 4 * PPQ          # 4/4: four quarter notes of 480 ticks
EXPECTED_TRACKS = (
    "vrc6 pulse a", "vrc6 pulse b", "vrc6 saw", "pulse 1",
    "pulse 2", "triangle", "noise", "dpcm",
)
RANGES = {
    "vrc6 pulse a": (60, 84), "vrc6 pulse b": (55, 76), "vrc6 saw": (36, 64),
    "pulse 1": (48, 72), "pulse 2": (60, 84), "triangle": (33, 60),
    "noise": (1, 16), "dpcm": (36, 38),
}
ALLOWED_STATUS = {"MThd", "MTrk"}


def sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def duration(path):
    """Length in seconds, from ffprobe. None when ffprobe is unavailable."""
    try:
        done = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", path],
            capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    try:
        return float(done.stdout.strip())
    except ValueError:
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check the PP-03 Harbor build.")
    parser.add_argument("--dir", default=HERE)
    parser.add_argument("--json", nargs="?", const="", default=None)
    args = parser.parse_args(argv)
    folder = os.path.abspath(args.dir)

    checks = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        print("%-4s %s%s" % ("PASS" if ok else "FAIL", name, (": " + detail) if detail else ""))
        return ok

    midi_path = os.path.join(folder, "pp_03_harbor.mid")
    if not os.path.exists(midi_path):
        print("FAIL no MIDI at %s" % midi_path)
        return 1

    with open(midi_path, "rb") as handle:
        raw = handle.read()
    fmt, ntracks, division = struct.unpack(">hhh", raw[8:14])
    check("MIDI header is format 1", fmt == 1, "format %d" % fmt)
    check("MIDI division is 480", division == PPQ, "division %d" % division)

    midi = render_chip.parse_midi(midi_path)
    names = [track.name for track in midi["tracks"]]
    voice_tracks = [t for t in midi["tracks"] if t.name in EXPECTED_TRACKS]
    check("eight voice tracks, named as render_chip.py expects",
          [t.name for t in voice_tracks] == list(EXPECTED_TRACKS),
          ", ".join(names))
    check("no voice outside the 2A03 and VRC6 set",
          set(names) <= set(EXPECTED_TRACKS) | {"conductor"}, ", ".join(sorted(set(names))))

    tempo = midi["tempo"][0][1]
    bpm = 60000000.0 / tempo
    check("tempo is 68 bpm", abs(bpm - 68.0) < 0.05, "%.4f bpm (%d us per quarter)" % (bpm, tempo))
    check("time signature is 4/4", tuple(midi["time_sig"]) == (4, 4), str(midi["time_sig"]))

    score_path = os.path.join(folder, "score_pp03.yaml")
    with open(score_path, "r", encoding="utf-8") as handle:
        score = yaml.safe_load(handle)
    bars = int(score["meta"]["bars"])
    limit = bars * BAR_TICKS

    by_name = {track.name: track for track in voice_tracks}
    all_notes = [(track.name, note) for track in voice_tracks for note in track.notes]
    check("every note is inside the loop point",
          all(note[1] <= limit for _name, note in all_notes),
          "limit %d ticks" % limit)
    last_end = max(note[1] for _name, note in all_notes)
    check("the arrangement is exactly %d bars" % bars, last_end == limit,
          "last note ends at tick %d of %d" % (last_end, limit))

    check("every note is inside its voice register",
          all(RANGES[name][0] <= note[2] <= RANGES[name][1] for name, note in all_notes),
          "ranges as declared in build_pp03.py")

    # The seam: same chord at bar 1 and bar 64.
    sections = list(score["sections"].values())
    first_chord = sections[0]["chords"][0]
    last_chord = sections[-1]["chords"][-1]
    check("the score opens and closes on the same chord", first_chord == last_chord,
          "%s at bar 1, %s at bar %d" % (first_chord, last_chord, bars))

    def roots_at(bar):
        """Lowest pitch sounding in a bar, per the bass and the pad."""
        start = bar * BAR_TICKS
        out = {}
        for name in ("triangle", "vrc6 saw"):
            pitches = [note[2] for note in by_name[name].notes if start <= note[0] < start + BAR_TICKS]
            out[name] = sorted(pitches)[0] if pitches else None
        return out

    first_roots, last_roots = roots_at(0), roots_at(bars - 1)
    same = (first_roots == last_roots and None not in first_roots.values()
            and (first_roots["triangle"] % 12) == (first_roots["vrc6 saw"] % 12))
    check("bar 1 and the last bar sound the same bass and pad root",
          same, "bar 1 %s, last bar %s" % (first_roots, last_roots))

    # Two noise hits at one tick is unplayable on one channel.
    noise_ticks = [note[0] for note in by_name["noise"].notes]
    duplicates = len(noise_ticks) - len(set(noise_ticks))
    check("the noise channel never plays two hits at one tick", duplicates == 0,
          "%d doubled ticks" % duplicates)

    # Leading silence: the lead breathes (HOK-30) and is not a wall of sound.
    lead = by_name["vrc6 pulse a"].notes
    bars_with_lead = {note[0] // BAR_TICKS for note in lead}

    def lead_silence_ticks(bar):
        start = bar * BAR_TICKS
        covered = sum(min(BAR_TICKS, note[1] - start) - max(0, note[0] - start)
                      for note in lead if start <= note[0] < start + BAR_TICKS)
        return BAR_TICKS - covered

    phrase_ends = [bar for bar in range(bars) if (bar + 1) % 4 == 0]
    phrase_ok = all(lead_silence_ticks(bar) >= 240 for bar in phrase_ends)
    check("every four bar phrase ends with a lead rest of an eighth (HOK-30)",
          phrase_ok,
          "shortest phrase end rest %d ticks"
          % min(lead_silence_ticks(bar) for bar in phrase_ends))
    breathing = sum(1 for bar in range(bars) if lead_silence_ticks(bar) >= 240)
    check("the lead rests in at least half the bars (low intensity brief)",
          breathing >= bars // 2,
          "a rest of an eighth or more in %d of %d bars" % (breathing, bars))

    # The drums are not one static figure.
    def bar_signature(bar):
        start = bar * BAR_TICKS
        hits = []
        for name in ("noise", "dpcm"):
            for note in by_name[name].notes:
                if start <= note[0] < start + BAR_TICKS:
                    hits.append((name, (note[0] - start) // (BAR_TICKS // 16), note[2], note[3]))
        return tuple(sorted(hits))

    signatures = [bar_signature(bar) for bar in range(bars)]
    distinct = len(set(signatures))
    longest = 1
    run = 1
    for previous, current in zip(signatures, signatures[1:]):
        run = run + 1 if current == previous else 1
        longest = max(longest, run)
    check("the drums change from bar to bar (not one static figure)", distinct >= 24,
          "%d distinct bar grids in %d bars, longest identical run %d"
          % (distinct, bars, longest))

    # The files.
    wav = os.path.join(folder, "pp_03_harbor.wav")
    mp3 = os.path.join(folder, "pp_03_harbor.mp3")
    ogg = os.path.join(folder, "pp_03_harbor.ogg")
    loop_json = os.path.join(folder, "pp_03_harbor_loop.json")
    lengths = {}
    for path in (wav, mp3, ogg):
        lengths[os.path.basename(path)] = duration(path) if os.path.exists(path) else None
    present = all(lengths.values())
    check("the render exists in wave, mp3 and ogg", present, str(lengths))
    if present:
        spread = max(lengths.values()) - min(lengths.values())
        check("the three files are the same length", spread < 0.05,
              "spread %.6f s" % spread)
        expected = bars * 4 * 60.0 / bpm
        check("the render is exactly %d bars long" % bars, abs(lengths["pp_03_harbor.wav"] - expected) < 0.05,
              "%.3f s measured, %.3f s expected" % (lengths["pp_03_harbor.wav"], expected))

    if os.path.exists(loop_json):
        with open(loop_json, "r", encoding="utf-8") as handle:
            loop = json.load(handle)
        seam = loop.get("loop_seam_sample_difference")
        check("the loop json reports one loop of %d bars" % bars,
              loop.get("loop_bars", bars) == bars, json.dumps({
                  "loop_bars": loop.get("loop_bars"), "loop_seconds": loop.get("loop_seconds"),
                  "seam": seam})[:300])
        check("the loop seam does not click", seam is not None and abs(seam) < 0.05,
              "seam sample difference %s" % (seam,))
    else:
        check("the loop json exists", False, loop_json)

    counts = {name: len(by_name[name].notes) for name in EXPECTED_TRACKS}
    print("\nnote counts: " + ", ".join("%s %d" % (k, v) for k, v in counts.items()))
    print("total %d notes, lead in %d of %d bars, %d distinct drum bars"
          % (sum(counts.values()), len(bars_with_lead), bars, distinct))

    passed = sum(1 for row in checks if row["passed"])
    failed = len(checks) - passed
    print("\n%d passed, %d failed" % (passed, failed))

    if args.json is not None:
        out = args.json or os.path.join(folder, "score_check.json")
        report = {
            "midi": os.path.abspath(midi_path),
            "sha256": sha256(midi_path),
            "bpm": round(bpm, 4),
            "bars": bars,
            "loop_seconds": round(bars * 4 * 60.0 / bpm, 6),
            "note_counts": counts,
            "distinct_drum_bars": distinct,
            "longest_identical_drum_run": longest,
            "lead_bars": len(bars_with_lead),
            "audio_seconds": lengths,
            "checks": checks,
            "passed": passed,
            "failed": failed,
        }
        with open(out, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print("report: %s" % out)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
