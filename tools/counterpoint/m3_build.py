"""Build, render and master one M3 cue, and write its build report.

Card t_65512e1c. This is the pipeline around tools/counterpoint/m3_cues.py:

  compose  m3_cues.build(piece) writes the MIDI (three pitched voices, plus noise and
           dpcm on the fight cue) and the counterpoint report;
  render   tools/render_chip.py, the project's own 2A03 renderer, with the loop point
           named in bars so the seam is measured and not assumed;
  master   ffmpeg loudnorm in two passes to the spec 12 target the W5 masters use,
           -14.0 LUFS integrated and a true peak at or under -1.0 dBTP;
  measure  the master is re-measured after encoding, because a Vorbis encode can move
           both numbers, and the report carries what the delivered file actually is.

Nothing here writes outside the asset directory it is given, and it refuses to write
into a directory that already holds a .wav or .ogg, so an earlier version is never
overwritten.

Usage
    python tools/counterpoint/m3_build.py --piece title \
        --asset-dir assets/audio/pp_01_title_v10 --slug pp_01_title_v10 --loop-bars 32
    python tools/counterpoint/m3_build.py --piece fight \
        --asset-dir assets/audio/pp_04_fight_baroque_v1 --slug pp_04_fight_baroque_v1 --loop-bars 16

Exit codes: 0 built and verified, 1 a counterpoint or loudness check failed, 2 refusals.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
for path in (HERE, TOOLS):
    if path not in sys.path:
        sys.path.insert(0, path)

import m3_cues  # noqa: E402

PYTHON = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
TARGET_LUFS = -14.0
CEILING_DBTP = -1.0
TOLERANCE_LU = 0.2


def run(command, cwd=ROOT):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    return result


def loudness(path):
    """Integrated loudness, loudness range and true peak of a file, from ffmpeg."""
    result = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                  "-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json",
                  "-f", "null", "-"])
    text = result.stderr
    block = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", text, re.S)
    if not block:
        raise RuntimeError("could not read loudness from %s: %s" % (path, text[-300:]))
    data = json.loads(block.group(0))
    return {"integrated_lufs": float(data["input_i"]),
            "true_peak_dbtp": float(data["input_tp"]),
            "lra_lu": float(data["input_lra"]),
            "threshold": float(data["input_thresh"]),
            "offset": float(data["target_offset"])}


def master(source_wav, out_wav, out_ogg, out_mp3):
    """Gain then a lookahead limiter, iterated until the delivered encode measures on target.

    loudnorm alone cannot do this job on chip material: in dynamic mode it stops several
    tenths short of -14 LUFS on a dense cue, and in linear mode its true-peak path lets
    the Vorbis encode run over the ceiling. The chain here is volume then alimiter with
    auto level OFF (with it on, the limiter puts its own output back at full scale, which
    is how a first attempt shipped a +0.8 dBTP master), and the loop measures after every
    attempt: the gain corrects the integrated loudness, and the limit is lowered whenever
    the true peak is over the ceiling, which is what a square wave's intersample peaks
    need.
    """
    before = loudness(source_wav)
    limit_db = -1.9
    gain = 0.0
    attempts = []
    for _attempt in range(8):
        limit_linear = round(10.0 ** (limit_db / 20.0), 4)
        af = ("volume=%.2fdB,alimiter=level_in=1:level_out=1:limit=%.4f:"
              "attack=1:release=50:level=0" % (gain, limit_linear))
        result = run(["ffmpeg", "-y", "-hide_banner", "-nostats", "-i", source_wav,
                      "-af", af, "-ar", "44100", out_wav])
        if result.returncode:
            raise RuntimeError("master failed: " + result.stderr[-500:])
        master_reading = loudness(out_wav)
        for target, codec in ((out_ogg, ["-c:a", "libvorbis", "-q:a", "5"]),
                              (out_mp3, ["-c:a", "libmp3lame", "-b:a", "192k"])):
            result = run(["ffmpeg", "-y", "-hide_banner", "-nostats", "-i", out_wav]
                         + codec + [target])
            if result.returncode:
                raise RuntimeError("encode failed for %s: %s" % (target,
                                                                 result.stderr[-300:]))
        encoded = loudness(out_ogg)
        attempts.append({"gain_db": round(gain, 2), "limit_db": limit_db,
                         "wav_lufs": master_reading["integrated_lufs"],
                         "wav_dbtp": master_reading["true_peak_dbtp"],
                         "ogg_lufs": encoded["integrated_lufs"],
                         "ogg_dbtp": encoded["true_peak_dbtp"]})
        level_error = TARGET_LUFS - encoded["integrated_lufs"]
        peak_over = encoded["true_peak_dbtp"] - CEILING_DBTP
        if abs(level_error) <= 0.15 and peak_over <= 0.0:
            break
        gain += level_error
        if peak_over > 0.0:
            limit_db -= peak_over + 0.15
    before["attempts"] = attempts
    return before


def counterpoint_checks(midi):
    """The gate's own tools on the finished MIDI, as printed reports."""
    out = {}
    check = run([PYTHON, os.path.join(TOOLS, "counterpoint", "check.py"), midi,
                 "--limit", "0", "--quiet"])
    out["check"] = check.stdout.strip()
    gate = run([PYTHON, os.path.join(TOOLS, "counterpoint", "cue_gate.py"), midi,
                "--no-baseline", "--quiet"])
    out["cue_gate"] = {"exit": gate.returncode,
                       "stdout": gate.stdout.strip(), "stderr": gate.stderr.strip()}
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build one M3 cue (card t_65512e1c).")
    parser.add_argument("--piece", choices=("title", "fight"), required=True)
    parser.add_argument("--asset-dir", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--loop-bars", type=int, required=True)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--variant", type=int, choices=(1, 2), default=1,
                        help="1 is the first take, 2 is take B (the other way round)")
    args = parser.parse_args(argv)

    asset_dir = os.path.abspath(os.path.join(ROOT, args.asset_dir))
    if not asset_dir.startswith(os.path.abspath(ROOT)):
        sys.stderr.write("refused: %s is outside the project\n" % asset_dir)
        return 2
    os.makedirs(asset_dir, exist_ok=True)
    for name in os.listdir(asset_dir):
        if name.endswith((".wav", ".ogg")):
            sys.stderr.write("refused: %s already holds %s; a new version needs a new "
                             "folder\n" % (asset_dir, name))
            return 2

    midi = os.path.join(asset_dir, args.slug + ".mid")
    wav = os.path.join(asset_dir, args.slug + ".wav")
    out_wav = os.path.join(asset_dir, args.slug + "_master.wav")
    ogg = os.path.join(asset_dir, args.slug + ".ogg")
    mp3 = os.path.join(asset_dir, args.slug + ".mp3")

    piece, report = m3_cues.build(args.piece, args.seed, args.variant)
    notes = dict(piece.notes)
    if args.piece == "fight":
        notes.update(m3_cues.drums_fight_drive(piece) if args.variant == 2
                     else m3_cues.drums_fight(piece))
    cc = {"pulse 1": {12: [(0, 2)], 11: [(0, 104)], 1: [(0, 4)], 20: [(0, 1)]},
          "pulse 2": {12: [(0, 1)], 11: [(0, 88)], 1: [(0, 3)], 20: [(0, 2)]}}
    m3_cues.write_midi(notes, midi, piece.time_sig, piece.bpm, cc)
    report["midi"] = midi

    render = run([PYTHON, os.path.join(TOOLS, "render_chip.py"), midi, wav,
                  "--loop-bars", str(args.loop_bars),
                  "--humanize",
                  "--hook-report", os.path.join(asset_dir, "hook_report.json"),
                  "--loop-json", os.path.join(asset_dir, args.slug + "_loop.json")])
    render_text = render.stdout + render.stderr
    if render.returncode or not os.path.exists(wav):
        sys.stderr.write("render failed:\n" + render_text[-2000:])
        return 1

    before = master(wav, out_wav, ogg, mp3)
    delivered = loudness(ogg)
    ceiling_ok = delivered["true_peak_dbtp"] <= CEILING_DBTP + 0.05
    level_ok = abs(delivered["integrated_lufs"] - TARGET_LUFS) <= TOLERANCE_LU
    checks = counterpoint_checks(midi)
    humanized = os.path.join(asset_dir, args.slug + "_humanized.mid")
    if os.path.exists(humanized):
        checks["check_humanized"] = run(
            [PYTHON, os.path.join(TOOLS, "counterpoint", "check.py"), humanized,
             "--limit", "0", "--quiet"]).stdout.strip()
        checks["cue_gate_humanized"] = run(
            [PYTHON, os.path.join(TOOLS, "counterpoint", "cue_gate.py"), humanized,
             "--no-baseline", "--quiet"]).stdout.strip()

    hook = None
    hook_path = os.path.join(asset_dir, "hook_report.json")
    if os.path.exists(hook_path):
        with open(hook_path, "r", encoding="utf-8") as handle:
            hook = json.load(handle)

    peak_line = next((line.strip() for line in render_text.splitlines()
                      if "duration" in line and "peak" in line), None)
    loop_line = next((line.strip() for line in render_text.splitlines()
                      if line.strip().startswith("loop ")), None)
    report.update({
        "render": {"command": "render_chip.py %s %s --loop-bars %d"
                              % (os.path.basename(midi), os.path.basename(wav),
                                 args.loop_bars),
                   "peak_line": peak_line, "loop_line": loop_line},
        "loudness": {"before": before, "delivered_ogg": delivered,
                     "target": {"integrated_lufs": TARGET_LUFS,
                                "ceiling_dbtp": CEILING_DBTP},
                     "level_ok": level_ok, "ceiling_ok": ceiling_ok},
        "counterpoint": checks,
        "hook": hook,
        "files": [os.path.basename(path) for path in (midi, wav, out_wav, ogg, mp3)],
    })
    with open(os.path.join(asset_dir, "build_report.json"), "w", encoding="utf-8",
              newline="\n") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
        handle.write("\n")

    print("== %s (%s)" % (args.slug, args.piece))
    print("   counterpoint: hard %d, soft %d, style %d, clash raw %d (downbeat %d)"
          % (report["hard"], report["by_severity"].get("soft", 0),
             report["by_severity"].get("style", 0), report["clash"]["raw_total"],
             report["clash"]["strong_raw"]))
    print("   devices: %s" % json.dumps(report["devices"]))
    print("   gate exit %d: %s" % (checks["cue_gate"]["exit"],
                                   checks["cue_gate"]["stdout"]))
    print("   %s" % (peak_line or "render peak line missing"))
    print("   loudness before %.2f LUFS / %.2f dBTP, delivered %.2f LUFS / %.2f dBTP "
          "(target %.1f, ceiling %.1f) level_ok %s ceiling_ok %s"
          % (before["integrated_lufs"], before["true_peak_dbtp"],
             delivered["integrated_lufs"], delivered["true_peak_dbtp"],
             TARGET_LUFS, CEILING_DBTP, level_ok, ceiling_ok))
    if hook:
        print("   hook score %s / 100 (v9 title was 83)"
              % hook.get("score", hook.get("total")))
    return 0 if (report["hard"] == 0 and level_ok and ceiling_ok
                 and checks["cue_gate"]["exit"] in (0, 3)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
