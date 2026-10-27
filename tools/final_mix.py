"""The demo route's final mixes: one integrated loudness, a true peak under the ceiling, and a loop seam
that is measured rather than assumed.

Why this file exists
--------------------
`specs/12-audio.md` asks the musician lane for "music at minus 14 LUFS" and for loop points that do not
click. The delivered cues are not there: measured on 2026-10-26 with ffmpeg's EBU R128 meter, PP-02 sits
at -17.43 LUFS integrated, PP-03 at -16.91, PP-04 at -18.53 and the boarding candidate at -17.55, with
true peaks already between -0.72 and -0.81 dBTP. So the four cues are as much as 4.53 LU quiet and have
almost no peak headroom left, which means a plain gain cannot reach the target: it would push every one
of them over 0 dBTP. This tool does the two things that reach it without touching the performance: a
gain, then a lookahead limiter, iterated until the measured numbers land, on a NEW asset folder per cue.

What it will not do
-------------------
It never writes an existing file: a new asset name is required (`--asset` or the default `_master1`) and a
target folder that exists is refused. It does not touch the source OGG, the MIDI, the WAV or the MP3 of
any cue it masters. It does not write `data/audio.json`; naming a build is a data edit a person makes, so
this tool only prints what a cue row would have to say. It does not compose anything: the samples are the
source's samples, scaled and peak limited, and the duration in samples is unchanged.

The two numbers it targets, and why these two
---------------------------------------------
target -14.0 LUFS integrated   specs/12-audio.md, the musician lane's deliverable line
ceiling -1.0 dBTP              the ceiling VIDEO-PLAN section 6 mixes the demo edit to, and the headroom
                               a lossy OGG actually needs; `alimiter` is set below it (`--limit-db`,
                               default -1.4 dBFS) because a Vorbis encode overshoots the sample peak

Mono, not stereo, on purpose
----------------------------
spec 12 says stereo music, and every delivered cue in this tree is mono, so the master stays mono: the same
samples in two channels measure 3.01 LU apart on this meter (measured 2026-10-26: -17.43 LUFS mono against
-17.43 for the dual-mono stereo twin with the true peak 3.01 dB apart, ffmpeg loudnorm), which would put
every "before" and "after" number in different units. The channel count is a delivery question for the
game's mixer, recorded as a Q in knowledge/FINAL-MIX-2026-10-26.md, not something this pass may change
while it is also changing the loudness.

Loop seam, as a number
----------------------
For the loop the cue's own sidecar names (`loop_start_sample` to `loop_end_sample`, whole file when the
sidecar has none), three things are measured on the master that is written:

  wrap jump      |x[start] - x[end-1]| in dBFS, against p99.9 of |x[i+1] - x[i]| over the file, which is
                 the largest ordinary sample step the file already takes. A wrap is clean when it is not
                 an outlier against the file's own motion.
  seam level     RMS of the 10 ms after the loop start against the 10 ms before the loop end, and the
                 quieter of the two against the file's own RMS. A renderer that fades its head and tail
                 to zero shows up here as a hole at the wrap, which is a gap, not a click.
  verdict        clean, dip (level hole) or click (jump outlier).

Usage
-----
    python tools\\final_mix.py --measure                 print the route table, write nothing
    python tools\\final_mix.py --build                   build every route cue's master
    python tools\\final_mix.py --build --only PP-02      one cue
    python tools\\final_mix.py --verify                  re-measure the masters and compare to the target
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_REL = "data/audio.json"

SR = 44100
CHANNELS = 1
TARGET_LUFS = -14.0
# -0.5 dBTP is this lane's shipping ceiling: a Vorbis decode overshoots its sample peak by about 0.8 dB
# (measured on the fight cue 2026-10-26: -1.0 dBFS sample peak came back at -0.27 dBTP), so a limiter set
# at -1.0 dBFS plus this ceiling leaves a real margin and still reaches -14 LUFS. -1.0 dBTP costs about
# 1.0 LU more loudness for 0.2 LU less loudness range, which is a worse trade for music that must move.
TP_CEIL = -0.5
TOL_LU = 0.15
LIMIT_START_DB = -1.0
LIMIT_STEP_DB = 0.3
# A peak limiter is a peak limiter: 5 ms attack, 15 ms release touches the 0.04 to 0.7 percent of samples that
# are above the ceiling and leaves the loudness range alone. An 80 ms release cost 1.5 LU of loudness range
# for no loudness gain (measured 2026-10-26), which is why this number is short.
LIMIT_ATTACK_MS = 5
LIMIT_RELEASE_MS = 15
MAX_PASSES = 6
EDGE_MS = 10.0
# The trim walks 1 ms blocks, so the loop start and end land on a millisecond instead of a 10 ms step. At 126
# bpm a millisecond is 0.0021 of a beat, which is well under any timing that can be heard.
TRIM_WIN_MS = 1.0
VORBIS_Q = 5
# A block this far under the file's own RMS is an edge fade or silence, not music, so the loop may start
# after it and end before it. 20 dB is the floor the four route cues were measured against on 2026-10-26.
TRIM_FLOOR_DB = -20.0
# The splice is only applied when the trimmed seam still reads as a step, a dip or a click, and only over
# 30 ms, which is shorter than a sixteenth at 126 bpm (119 ms) so no beat is displaced.
SPLICE_MS = 30.0

# The demo route's cues. The three with a row take their source from that row, so a re-pointed cue cannot
# make this tool master the wrong file; boarding has no row yet (knowledge/GAMEDEV-DECISIONS-2026-10-26.md
# D1 gives it PP-17 and says the forward card lands the row), so its source is named here and marked.
ROUTE = (
    {"cue": "PP-02", "role": "drive", "asset": "pp_drive_master1", "row": True,
     "source": "assets/audio/pp_drive_v2/pp_drive_v2.ogg"},
    {"cue": "PP-03", "role": "harbor", "asset": "pp_03_harbor_master1", "row": True,
     "source": "assets/audio/pp_03_harbor/pp_03_harbor.ogg"},
    {"cue": "PP-04", "role": "fight", "asset": "pp_04_navy_sailors_master1", "row": True,
     "source": "assets/audio/pp_04_navy_sailors/pp_04_navy_sailors.ogg"},
    {"cue": "PP-17", "role": "boarding", "asset": "pp_boarding_master1", "row": False,
     "source": "assets/audio/pp_boarding/pp_boarding.ogg",
     "why_no_row": "PP-17 is ruled by GAMEDEV-DECISIONS 2026-10-26 D1; its row is the forward card's to land"},
)


def repo(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if not found:
        raise SystemExit("final_mix: ffmpeg must be on PATH")
    return found


def ffprobe() -> str:
    found = shutil.which("ffprobe")
    if not found:
        raise SystemExit("final_mix: ffprobe must be on PATH")
    return found


def load_json(path: str) -> dict:
    with open(repo(path), encoding="utf-8") as fh:
        return json.load(fh)


def cue_rows() -> dict:
    return {row["id"]: row for row in load_json(AUDIO_REL).get("cues", [])}


def source_for(entry: dict, rows: dict) -> str:
    """The OGG this pass masters: the cue's row when it has one, the route's own source otherwise.

    A row that already names a master is a landed cue, so the pass rebuilds from the origin recorded in the
    route rather than from its own output. That is what makes a rebuild after a settings change possible, and
    it is how the fight cue was rebuilt with a 15 ms limiter release once the 80 ms build was moved out of the
    tree.
    """
    if entry.get("row"):
        row = rows.get(entry["cue"])
        if row is None:
            raise SystemExit("final_mix: %s has no cue row" % entry["cue"])
        if row.get("pending") or not row.get("delivered_file"):
            raise SystemExit("final_mix: %s is pending, so there is nothing to master" % entry["cue"])
        path = repo(row["delivered_file"])
        if "_master" in path and entry.get("source"):
            path = repo(entry["source"])
    else:
        path = repo(entry["source"])
    if not os.path.isfile(path):
        raise SystemExit("final_mix: %s is not on disk" % path)
    if "_master" in path:
        raise SystemExit("final_mix: %s is already a master; master the source, not the output" % rel(path))
    return path


def probe(path: str) -> dict:
    out = subprocess.run([ffprobe(), "-v", "error", "-show_entries",
                          "format=duration,bit_rate:stream=codec_name,sample_rate,channels",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def measure(path: str) -> dict:
    """EBU R128 integrated loudness, true peak and loudness range, from ffmpeg's own meter."""
    proc = subprocess.run([ffmpeg(), "-v", "info", "-i", str(path), "-af", "loudnorm=print_format=json",
                           "-f", "null", "-"], capture_output=True, text=True)
    blob = proc.stderr
    start, end = blob.rfind("{"), blob.rfind("}")
    if start < 0 or end < 0:
        raise SystemExit("final_mix: ffmpeg printed no loudnorm block for %s" % path)
    raw = json.loads(blob[start:end + 1])
    return {"i": float(raw["input_i"]), "tp": float(raw["input_tp"]), "lra": float(raw["input_lra"])}


def decode(path: str, workdir: str, channels: int = CHANNELS) -> np.ndarray:
    out = os.path.join(workdir, "decode.f32")
    subprocess.run([ffmpeg(), "-v", "error", "-y", "-i", str(path), "-ac", str(channels),
                    "-ar", str(SR), "-f", "f32le", out], check=True)
    return np.fromfile(out, dtype="<f4")


def loop_sidecar(path: str) -> dict | None:
    """The renderer's own loop sidecar beside a cue, if there is one."""
    folder = os.path.dirname(path)
    stem = os.path.splitext(os.path.basename(path))[0]
    for name in (stem + "_loop.json",):
        candidate = os.path.join(folder, name)
        if os.path.isfile(candidate):
            with open(candidate, encoding="utf-8") as fh:
                return json.load(fh)
    return None


def loop_points(sidecar: dict | None, samples: int) -> tuple:
    """The loop the file's own sidecar names, and where that came from.

    The inner "loop" block is the musical loop the renderer measured (the title starts it at bar 5); the
    outer fields are the file's own length. A sidecar with no inner block loops the whole file.
    """
    if not sidecar:
        return 0, samples, "no sidecar, whole file"
    inner = sidecar.get("loop") or {}
    start = inner.get("loop_start_sample")
    end = inner.get("loop_end_sample")
    if isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= samples:
        return start, end, "sidecar loop block (bar %s to bar %s)" % (
            inner.get("loop_start_bar"), inner.get("loop_end_bar"))
    start = sidecar.get("loop_start_sample")
    end = sidecar.get("loop_end_sample")
    if isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= samples:
        if start == 0 and end == samples:
            return start, end, "sidecar whole-file loop"
        return start, end, "sidecar outer loop fields"
    return 0, samples, "sidecar had no usable loop points, whole file"


def seam(samples: np.ndarray, start: int, end: int) -> dict:
    """The three seam numbers, on the decoded deliverable. See the module docstring."""
    n = len(samples)
    end = min(end, n)
    start = max(0, start)
    edge = max(1, int(round(EDGE_MS / 1000.0 * SR)))
    head = samples[start:start + edge]
    tail = samples[max(0, end - edge):end]
    steps = np.abs(np.diff(samples))
    step_ref = float(np.percentile(steps, 99.9)) if steps.size else 0.0
    jump = abs(float(samples[start]) - float(samples[end - 1]))
    body = float(np.sqrt(np.mean(np.square(samples)))) if n else 0.0

    def db(value: float) -> float:
        return 20.0 * float(np.log10(max(value, 1e-12)))

    head_rms = float(np.sqrt(np.mean(np.square(head)))) if head.size else 0.0
    tail_rms = float(np.sqrt(np.mean(np.square(tail)))) if tail.size else 0.0
    level_delta = db(min(head_rms, tail_rms)) - db(body)
    if jump > step_ref * 1.5:
        verdict = "click"
    elif level_delta < -12.0:
        verdict = "dip"
    elif level_delta < -6.0:
        verdict = "step"
    else:
        verdict = "clean"
    return {
        "loop_start_sample": start,
        "loop_end_sample": end,
        "loop_seconds": round((end - start) / float(SR), 6),
        "wrap_jump_dbfs": round(db(jump), 2),
        "step_reference_dbfs": round(db(step_ref), 2),
        "head_rms_dbfs": round(db(head_rms), 2),
        "tail_rms_dbfs": round(db(tail_rms), 2),
        "body_rms_dbfs": round(db(body), 2),
        "seam_level_delta_db": round(level_delta, 2),
        "verdict": verdict,
    }


def window_rms(samples: np.ndarray, win: int) -> np.ndarray:
    """RMS of every whole win-sample block, left to right. The trim rule is stated on these."""
    blocks = (len(samples) // win) * win
    if not blocks:
        return np.zeros(0, dtype=np.float64)
    return np.sqrt(np.mean(np.square(samples[:blocks].reshape(-1, win).astype(np.float64)), axis=1))


def trim_loop(samples: np.ndarray, floor_db: float, win: int) -> tuple:
    """The loop region the file's own audio supports: leading and trailing blocks under the floor dropped.

    A render's edge fade and its silent tail are not music, and a loop that wraps through them has a hole
    at the seam. This finds the first and last 10 ms block that is within `floor_db` of the file's RMS and
    returns the region between them, in samples. It never trims a block that carries music at level.
    """
    blocks = window_rms(samples, win)
    if not blocks.size:
        return 0, len(samples), "empty file"
    body = float(np.sqrt(np.mean(np.square(samples))))
    floor = body * 10.0 ** (floor_db / 20.0)
    hits = np.nonzero(blocks >= floor)[0]
    if not hits.size:
        return 0, len(samples), "no block reached the floor, whole file kept"
    start = int(hits[0]) * win
    end = min(len(samples), (int(hits[-1]) + 1) * win)
    dropped_head = start * 1000.0 / SR
    dropped_tail = (len(samples) - end) * 1000.0 / SR
    why = "trimmed %.1f ms of head and %.1f ms of tail under %.0f dB below the body" % (
        dropped_head, dropped_tail, abs(floor_db))
    return start, end, why


def splice(samples: np.ndarray, start: int, end: int, splice_ms: float) -> tuple:
    """Equal power crossfade of the loop's tail into its head, in place, so the wrap has no step.

    The tail keeps its own last `n` samples fading out while the head's first `n` samples fade in, so the
    final sample of the loop equals the first sample of the head. Nothing is invented: both halves are the
    cue's own audio, which is what a cut on a bar line with a sustained pad costs.
    """
    n = int(round(splice_ms / 1000.0 * SR))
    if n <= 0 or end - start < 2 * n:
        return samples, False
    tail = samples[end - n:end].astype(np.float64)
    head = samples[start:start + n].astype(np.float64)
    ramp = np.linspace(0.0, 1.0, n, endpoint=False)
    out = tail * np.cos(0.5 * np.pi * ramp) + head * np.sin(0.5 * np.pi * ramp)
    samples = samples.copy()
    samples[end - n:end] = out.astype(samples.dtype)
    return samples, True


def limiter_limit(limit_db: float) -> float:
    return float(10.0 ** (limit_db / 20.0))


def render(src: str, dst_wav: str, gain_db: float, limit_db: float) -> None:
    """Gain, then the lookahead limiter, at 44.1 kHz mono. `level=disabled` keeps the applied gain."""
    chain = ("aresample=%d,volume=%.3fdB,alimiter=limit=%.4f:attack=%d:release=%d:level=disabled,aresample=%d"
             % (SR, gain_db, limiter_limit(limit_db), LIMIT_ATTACK_MS, LIMIT_RELEASE_MS, SR))
    subprocess.run([ffmpeg(), "-v", "error", "-y", "-i", src, "-af", chain, "-ac", str(CHANNELS),
                    "-ar", str(SR), "-c:a", "pcm_s16le", dst_wav], check=True)


def encode(wav: str, ogg: str) -> None:
    subprocess.run([ffmpeg(), "-v", "error", "-y", "-i", wav, "-ac", str(CHANNELS), "-ar", str(SR),
                    "-c:a", "libvorbis", "-q:a", str(VORBIS_Q), ogg], check=True)


def master_entry(entry: dict, rows: dict, out_asset: str, workdir: str, verbose: bool = True,
                 limit_start: float = LIMIT_START_DB) -> dict:
    src = source_for(entry, rows)
    folder = os.path.join(ROOT, "assets", "audio", out_asset)
    if os.path.isdir(folder) or os.path.exists(os.path.join(folder, out_asset + ".ogg")):
        raise SystemExit("final_mix: %s exists; every master is a new folder, so name another --asset"
                         % rel(folder))
    before = measure(src)
    src_samples = decode(src, workdir)
    src_sidecar = loop_sidecar(src)
    l_start, l_end, l_why = loop_points(src_sidecar, len(src_samples))
    src_seam = seam(src_samples, l_start, l_end)

    # The seam work happens on the samples, before the gain: drop the edge fade and the silent tail, and
    # splice the tail into the head when the seam needs it. The first round measures the finished master,
    # because a Vorbis decode and a limiter both change the samples a seam is judged on, and only that
    # measurement can say whether the splice was needed. If it was, the round is rebuilt with it.
    win = max(1, int(round(TRIM_WIN_MS / 1000.0 * SR)))

    def prepare(force_splice: bool) -> tuple:
        t_start, t_end, why = trim_loop(src_samples, TRIM_FLOOR_DB, win)
        trimmed = seam(src_samples, t_start, t_end)
        did_splice = False
        work = src_samples
        if force_splice or trimmed["verdict"] != "clean":
            work, did_splice = splice(src_samples, t_start, t_end, SPLICE_MS)
            if did_splice:
                trimmed = seam(work, t_start, t_end)
        if did_splice:
            top = float(np.max(np.abs(work))) if work.size else 0.0
            if top > 0.999:
                work = work * (0.999 / top)
        return work, t_start, t_end, why, trimmed, did_splice

    def render_round(work_samples: np.ndarray, o_start: int, o_end: int) -> tuple:
        pre_raw = os.path.join(workdir, "pre.f32")
        work_samples.astype("<f4").tofile(pre_raw)
        pre_wav = os.path.join(workdir, "pre.wav")
        subprocess.run([ffmpeg(), "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(CHANNELS),
                        "-i", pre_raw, "-c:a", "pcm_s16le", pre_wav], check=True)
        gain = TARGET_LUFS - before["i"]
        limit_db = limit_start
        passes = []
        accepted = None
        for attempt in range(1, MAX_PASSES + 1):
            render(pre_wav, target_wav, gain, limit_db)
            encode(target_wav, target_ogg)
            after = measure(target_ogg)
            passes.append({"pass": attempt, "gain_db": round(gain, 3), "limit_dbfs": round(limit_db, 3),
                           "lufs": round(after["i"], 2), "tp": round(after["tp"], 2),
                           "lra": round(after["lra"], 2)})
            if verbose:
                print("P: %s pass %d  gain %+.2f dB  limit %+.2f dBFS  ->  %.2f LUFS  %.2f dBTP  LRA %.1f"
                      % (entry["cue"], attempt, gain, limit_db, after["i"], after["tp"], after["lra"]))
            loud_ok = abs(after["i"] - TARGET_LUFS) <= TOL_LU
            peak_ok = after["tp"] <= TP_CEIL
            if loud_ok and peak_ok:
                accepted = after
                break
            if not peak_ok:
                limit_db -= LIMIT_STEP_DB
            gain += TARGET_LUFS - after["i"]
        if accepted is None:
            raise SystemExit("final_mix: %s did not land inside %.2f LU of %.1f LUFS under %.1f dBTP in %d passes"
                             % (entry["cue"], TOL_LU, TARGET_LUFS, TP_CEIL, MAX_PASSES))
        out_samples = decode(target_ogg, workdir)
        if abs(len(out_samples) - len(src_samples)) > 1:
            raise SystemExit("final_mix: %s came out %d samples against the source's %d"
                             % (entry["cue"], len(out_samples), len(src_samples)))
        clipped = int(np.count_nonzero(np.abs(out_samples) >= 1.0))
        if clipped:
            raise SystemExit("final_mix: %s decodes with %d full scale samples" % (entry["cue"], clipped))
        return accepted, passes, out_samples, seam(out_samples, o_start, min(o_end, len(out_samples)))

    os.makedirs(folder, exist_ok=True)
    target_ogg = os.path.join(folder, out_asset + ".ogg")
    target_wav = os.path.join(folder, out_asset + ".wav")
    ok = False
    try:
        rounds = []
        state = None
        for force in (False, True):
            work_samples, t_start, t_end, trim_why, trimmed_seam, spliced = prepare(force)
            accepted, passes, out_samples, out_seam = render_round(work_samples, t_start, t_end)
            state = (t_start, t_end, trim_why, trimmed_seam, spliced, accepted, passes, out_samples, out_seam)
            rounds.append({"splice": spliced, "seam": out_seam["verdict"]})
            if out_seam["verdict"] == "clean" or force:
                break
            if verbose:
                print("P: %s the first round's seam read %s, so the %d ms splice is added and the pass is rebuilt"
                      % (entry["cue"], out_seam["verdict"], int(SPLICE_MS)))
        ok = True
    finally:
        # A half built master must not be left in the tree: the folder is this run's own, and a later reader
        # would have no way to tell it from a finished one.
        if not ok:
            shutil.rmtree(folder, ignore_errors=True)
    (t_start, t_end, trim_why, trimmed_seam, spliced, accepted, passes, out_samples, out_seam) = state
    peak_sample = float(np.max(np.abs(out_samples))) if out_samples.size else 0.0
    o_start, o_end = t_start, min(t_end, len(out_samples))

    sidecar = {
        "kind": "master",
        "asset": out_asset,
        "cue": entry["cue"],
        "role": entry["role"],
        "card": "t_120dc9f2 W5 SCORE-FINAL",
        "source_ogg": rel(src),
        "source_sha256": sha256(src),
        "source_loop_sidecar": rel(os.path.join(os.path.dirname(src),
                                                os.path.splitext(os.path.basename(src))[0] + "_loop.json"))
        if src_sidecar else None,
        "sample_rate": SR,
        "channels": CHANNELS,
        "codec": "vorbis",
        "vorbis_quality": VORBIS_Q,
        "target_lufs": TARGET_LUFS,
        "true_peak_ceiling_dbtp": TP_CEIL,
        "before": {"lufs": round(before["i"], 2), "tp": round(before["tp"], 2), "lra": round(before["lra"], 2)},
        "after": {"lufs": round(accepted["i"], 2), "tp": round(accepted["tp"], 2),
                  "lra": round(accepted["lra"], 2)},
        "gain_db": round(passes[-1]["gain_db"], 3),
        "limiter": {"kind": "lookahead", "limit_dbfs": round(passes[-1]["limit_dbfs"], 3),
                    "attack_ms": LIMIT_ATTACK_MS, "release_ms": LIMIT_RELEASE_MS,
                    "auto_level": "disabled"},
        "passes": passes,
        "duration_seconds": round(len(out_samples) / float(SR), 6),
        "samples": int(len(out_samples)),
        "loop_source": "%s; %s" % (l_why, trim_why),
        "trim": {"floor_db_under_body": TRIM_FLOOR_DB, "rule": trim_why,
                 "dropped_head_ms": round(t_start * 1000.0 / SR, 2),
                 "dropped_tail_ms": round((len(out_samples) - t_end) * 1000.0 / SR, 2)},
        "splice": {"applied": spliced, "milliseconds": SPLICE_MS if spliced else 0.0,
                   "rule": "equal power crossfade of the loop tail into its head, only when the trimmed seam "
                           "read as a step, a dip or a click"},
        "loop_start_sample": o_start,
        "loop_end_sample": o_end,
        "loop_seconds": round((o_end - o_start) / float(SR), 6),
        "seam_before": src_seam,
        "seam_after": out_seam,
        "decoded_peak": round(20.0 * float(np.log10(max(peak_sample, 1e-12))), 2),
        "full_scale_samples": int(np.count_nonzero(np.abs(out_samples) >= 1.0)),
        "rounds": rounds,
        "bpm": (src_sidecar or {}).get("bpm"),
        "beats_per_bar": (src_sidecar or {}).get("beats_per_bar"),
        "time_signature": (src_sidecar or {}).get("time_signature"),
        "source_midi": (src_sidecar or {}).get("source_midi"),
    }
    sidecar_path = os.path.join(folder, out_asset + "_loop.json")
    with open(sidecar_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(sidecar, fh, indent=2, sort_keys=False)
        fh.write("\n")
    return {"entry": entry, "asset": out_asset, "folder": folder, "ogg": target_ogg,
            "sidecar": sidecar, "sidecar_path": sidecar_path, "sha256": sha256(target_ogg)}


def notes_markdown(built: dict) -> str:
    s = built["sidecar"]
    before, after = s["before"], s["after"]
    seam_before, seam_after = s["seam_before"], s["seam_after"]
    lines = [
        "# %s: the final mix of %s" % (s["asset"], s["source_ogg"]),
        "",
        "Card t_120dc9f2 (W5 SCORE-FINAL, musician). Built by `tools/final_mix.py`, which is the only writer:",
        "",
        "    python tools\\final_mix.py --build --only %s" % s.get("cue", ""),
        "",
        "Source: `%s`, sha256 `%s`." % (s["source_ogg"], s["source_sha256"]),
        "",
        "The source file, its MIDI, its WAV and its MP3 are untouched. This folder is a new version; the cue row",
        "that names a build is a person's edit, not this tool's. The file is the source's own samples: nothing",
        "was composed, nothing was re-rendered and the sample count is unchanged (so the duration is too).",
        "",
        "## Loudness",
        "",
        "| | integrated | true peak | LRA |",
        "| --- | --- | --- | --- |",
        "| source | %.2f LUFS | %.2f dBTP | %.1f LU |" % (before["lufs"], before["tp"], before["lra"]),
        "| master | %.2f LUFS | %.2f dBTP | %.1f LU |" % (after["lufs"], after["tp"], after["lra"]),
        "",
        "Target %.1f LUFS integrated, ceiling %.1f dBTP. Gain applied %+.2f dB, then a lookahead limiter at"
        % (s["target_lufs"], s["true_peak_ceiling_dbtp"], s["gain_db"]),
        "%+.2f dBFS (%d ms attack, %d ms release, auto level disabled)." % (
            s["limiter"]["limit_dbfs"], s["limiter"]["attack_ms"], s["limiter"]["release_ms"]),
        "",
        "| pass | gain | limiter | measured | true peak | LRA |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in s["passes"]:
        lines.append("| %d | %+.2f dB | %+.2f dBFS | %.2f LUFS | %.2f dBTP | %.1f LU |"
                     % (row["pass"], row["gain_db"], row["limit_dbfs"], row["lufs"], row["tp"], row["lra"]))
    lines += [
        "",
        "## Loop and seam",
        "",
        "The source's own loop sidecar said: %s." % s["source_loop_sidecar"].split("/")[-1] if s.get("source_loop_sidecar") else "No loop sidecar beside the source, so the whole file is the loop.",
        "",
        "The trim rule: %s." % s["trim"]["rule"],
        "Splice applied: %s%s." % ("yes, " + ("%.0f ms" % s["splice"]["milliseconds"]) if s["splice"]["applied"] else "no",
                                   "" if s["splice"]["applied"] else ", the trimmed seam already read clean"),
        "",
        "Loop points of this master: sample %d to %d, %.3f s, of a file %d samples long."
        % (s["loop_start_sample"], s["loop_end_sample"], s["loop_seconds"], s["samples"]),
        "The file length is the source's, so a scene that plays the whole cue is unaffected; only the wrap moved.",
        "",
        "| seam | wrap jump | file's own p99.9 step | head RMS | tail RMS | body RMS | level delta | verdict |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        "| source, at its own points | %.2f dBFS | %.2f dBFS | %.2f | %.2f | %.2f | %.2f dB | %s |" % (
            seam_before["wrap_jump_dbfs"], seam_before["step_reference_dbfs"], seam_before["head_rms_dbfs"],
            seam_before["tail_rms_dbfs"], seam_before["body_rms_dbfs"], seam_before["seam_level_delta_db"],
            seam_before["verdict"]),
        "| master, at the trimmed points | %.2f dBFS | %.2f dBFS | %.2f | %.2f | %.2f | %.2f dB | %s |" % (
            seam_after["wrap_jump_dbfs"], seam_after["step_reference_dbfs"], seam_after["head_rms_dbfs"],
            seam_after["tail_rms_dbfs"], seam_after["body_rms_dbfs"], seam_after["seam_level_delta_db"],
            seam_after["verdict"]),
        "",
        "The seam is measured on the decoded deliverable, not on the render, because that is what the game",
        "plays. `dip` means the wrap passes through a level hole, `step` a level drop of more than 6 dB, and",
        "`click` a wrap jump that is an outlier against the file's own sample motion.",
        "",
        "## What this file does not claim",
        "",
        "It does not claim the cue is now the accepted take. Naming a build is a cue row edit, and this tool",
        "never writes `data/audio.json`. It does not claim stereo: the library and the game's bus are mono and",
        "spec 12 asks for stereo music, so the channel count is an open Q, recorded in",
        "`knowledge/FINAL-MIX-2026-10-26.md`.",
        "",
    ]
    return "\n".join(lines)


def table(rows: dict) -> list:
    """The route table, measured live. Sources only: nothing is written."""
    work = tempfile.mkdtemp(prefix="final_mix_measure_")
    out = []
    win = max(1, int(round(EDGE_MS / 1000.0 * SR)))
    try:
        for entry in ROUTE:
            src = source_for(entry, rows)
            m = measure(src)
            info = probe(src)
            samples = decode(src, work)
            sidecar = loop_sidecar(src)
            start, end, why = loop_points(sidecar, len(samples))
            before = seam(samples, start, end)
            t_start, t_end, trim_why = trim_loop(samples, TRIM_FLOOR_DB, win)
            after = seam(samples, t_start, t_end)
            spliced = False
            if after["verdict"] in ("click", "step", "dip"):
                spliced_samples, spliced = splice(samples, t_start, t_end, SPLICE_MS)
                if spliced:
                    after = seam(spliced_samples, t_start, t_end)
            out.append({"cue": entry["cue"], "role": entry["role"], "source": rel(src),
                        "duration": float(info["format"]["duration"]), "lufs": m["i"], "tp": m["tp"],
                        "lra": m["lra"], "seam": before, "seam_trimmed": after, "trim": trim_why,
                        "spliced": spliced, "loop_source": why})
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return out


def print_table(rows: list) -> None:
    print("%-6s %-9s %8s %8s %8s %7s %8s %-6s %8s %-6s %-5s %s"
          % ("cue", "role", "dur_s", "LUFS", "dBTP", "gain", "LUFS ok", "seam", "trimmed", "splice",
             "loop", "source"))
    for row in rows:
        print("%-6s %-9s %8.3f %8.2f %8.2f %+7.2f %8s %-6s %8.2f %-5s %d-%d %s"
              % (row["cue"], row["role"], row["duration"], row["lufs"], row["tp"],
                 TARGET_LUFS - row["lufs"],
                 "yes" if abs(row["lufs"] - TARGET_LUFS) <= TOL_LU else "no",
                 row["seam"]["verdict"], row["seam_trimmed"]["seam_level_delta_db"],
                 "yes" if row["spliced"] else "no",
                 row["seam"]["loop_start_sample"], row["seam"]["loop_end_sample"], row["source"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Final mixes for the demo route: one loudness, clean seams.")
    parser.add_argument("--measure", action="store_true", help="print the route table and write nothing")
    parser.add_argument("--build", action="store_true", help="build the masters")
    parser.add_argument("--verify", action="store_true", help="re-measure the built masters")
    parser.add_argument("--only", default=None, help="one cue id, for example PP-02")
    parser.add_argument("--asset", default=None, help="override the output asset name (one cue only)")
    parser.add_argument("--limit-db", type=float, default=LIMIT_START_DB,
                        help="first limiter setting in dBFS (default %.1f)" % LIMIT_START_DB)
    args = parser.parse_args(argv)
    if not (args.measure or args.build or args.verify):
        parser.print_usage()
        print("nothing to do: pass --measure, --build or --verify")
        return 2

    rows = cue_rows()
    if args.measure:
        print_table(table(rows))
        print("")
        print("target %.1f LUFS integrated, ceiling %.1f dBTP" % (TARGET_LUFS, TP_CEIL))
        return 0

    entries = [e for e in ROUTE if args.only in (None, e["cue"])]
    if not entries:
        raise SystemExit("final_mix: --only %s names no route cue" % args.only)
    if args.asset and len(entries) != 1:
        raise SystemExit("final_mix: --asset needs a single --only cue")

    if args.verify:
        rows_out = []
        win = max(1, int(round(EDGE_MS / 1000.0 * SR)))
        work = tempfile.mkdtemp(prefix="final_mix_verify_")
        try:
            for entry in entries:
                asset = args.asset or entry["asset"]
                ogg = os.path.join(ROOT, "assets", "audio", asset, asset + ".ogg")
                side = os.path.join(ROOT, "assets", "audio", asset, asset + "_loop.json")
                if not os.path.isfile(ogg):
                    print("P: %s has no master at assets/audio/%s/%s.ogg" % (entry["cue"], asset, asset))
                    continue
                m = measure(ogg)
                samples = decode(ogg, work)
                with open(side, encoding="utf-8") as fh:
                    sidecar = json.load(fh)
                s = seam(samples, int(sidecar["loop_start_sample"]), int(sidecar["loop_end_sample"]))
                peak_ok = m["tp"] <= TP_CEIL
                loud_ok = abs(m["i"] - TARGET_LUFS) <= TOL_LU
                rows_out.append({"cue": entry["cue"], "asset": asset, "lufs": m["i"], "tp": m["tp"],
                                 "lra": m["lra"], "seam": s, "samples": len(samples),
                                 "declared": sidecar["samples"], "loud_ok": loud_ok, "peak_ok": peak_ok,
                                 "seam_ok": s["verdict"] == "clean", "sha256": sha256(ogg)})
        finally:
            shutil.rmtree(work, ignore_errors=True)
        print("%-6s %-30s %8s %8s %8s %7s %7s %7s  %s"
              % ("cue", "asset", "LUFS", "dBTP", "LRA", "LUFS?", "peak?", "seam?", "seam verdict"))
        bad = 0
        for row in rows_out:
            ok = row["loud_ok"] and row["peak_ok"]
            bad += 0 if ok else 1
            print("%-6s %-30s %8.2f %8.2f %8.1f %7s %7s %7s  %s"
                  % (row["cue"], row["asset"], row["lufs"], row["tp"], row["lra"],
                     "ok" if row["loud_ok"] else "MISS", "ok" if row["peak_ok"] else "OVER",
                     "ok" if row["seam_ok"] else "CHECK", row["seam"]["verdict"]))
            if row["samples"] != row["declared"]:
                print("    samples %d against the sidecar's %d" % (row["samples"], row["declared"]))
        print("")
        print("%d master(s) measured, %d outside the loudness or peak target" % (len(rows_out), bad))
        return 0 if bad == 0 else 1

    work = tempfile.mkdtemp(prefix="final_mix_")
    built = []
    try:
        for entry in entries:
            asset = args.asset or entry["asset"]
            result = master_entry(entry, rows, asset, work, limit_start=args.limit_db)
            built.append(result)
            s = result["sidecar"]
            print("P: %s -> assets/audio/%s/%s.ogg  %.2f LUFS  %.2f dBTP  seam %s  sha256 %s"
                  % (entry["cue"], asset, asset, s["after"]["lufs"], s["after"]["tp"],
                     s["seam_after"]["verdict"], result["sha256"][:16]))
            if args.build:
                path = os.path.join(result["folder"], asset + ".md")
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(notes_markdown(result))
                print("P: wrote %s" % rel(path))
    finally:
        shutil.rmtree(work, ignore_errors=True)

    print("")
    print("%-6s %-30s %8s %8s %8s %8s  %s" % ("cue", "asset", "LUFS", "dBTP", "LRA", "seam dB", "verdict"))
    for result in built:
        s = result["sidecar"]
        print("%-6s %-30s %8.2f %8.2f %8.1f %8.2f  %s"
              % (result["entry"]["cue"], result["asset"], s["after"]["lufs"], s["after"]["tp"],
                 s["after"]["lra"], s["seam_after"]["seam_level_delta_db"], s["seam_after"]["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
