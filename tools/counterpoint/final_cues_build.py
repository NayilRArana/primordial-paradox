"""Build one final scope cue: compose, render loop-exact, master, encode, analyse, write the report.

    python tools/counterpoint/final_cues_build.py --cue storm --asset-dir assets/audio/pp_03_quay_storm

How the loop is made seamless (not just fading the edges): the body MIDI is repeated three times,
tools/render_chip.py renders the three passes as one continuous piece, and the MIDDLE pass is cut out.
Its end then flows into its own start exactly as an internal bar line does. The cut pass is compared
with the pass after it (max sample difference) to prove the render is periodic. Gain and the limiter
are applied to the three pass render before the cut, so they cannot disturb the seam.

Checks written to build_report.json: the counterpoint cue gate (CP-01 and CP-09 must be zero), the
declared key against the key found in the MIDI and in the decoded audio, the declared tempo against
the tempo found in the decoded audio, the loop seam on the decoded OGG (tools/final_mix.seam), and the
loudness (target -14 LUFS, true peak at or under -1 dBTP, mean level above -40 dB).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
for p in (HERE, TOOLS):
    if p not in sys.path:
        sys.path.insert(0, p)

import final_cues  # noqa: E402
import final_mix  # noqa: E402
import m3_build  # noqa: E402
import render_chip  # noqa: E402

SR = 44100
TARGET_LUFS = -14.0
CEILING = -1.0

KS_MAJ = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
KS_MIN = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def key_of_hist(hist):
    best = []
    h = np.asarray(hist, dtype=float)
    for tonic in range(12):
        for mode, prof in (("major", KS_MAJ), ("minor", KS_MIN)):
            rot = np.array([prof[(i - tonic) % 12] for i in range(12)])
            r = float(np.corrcoef(h, rot)[0, 1])
            best.append((r, "%s %s" % (NAMES[tonic], mode)))
    best.sort(reverse=True)
    return best[:3]


def midi_key(cue):
    hist = np.zeros(12)
    for t, ns in cue.notes.items():
        if t in ("noise", "dpcm"):
            continue
        for s, e, p, v in ns:
            hist[p % 12] += e - s
    return key_of_hist(hist)


def audio_key(x):
    n = 8192
    win = np.hanning(n)
    hist = np.zeros(12)
    freqs = np.fft.rfftfreq(n, 1.0 / SR)
    sel = (freqs >= 80) & (freqs <= 1500)
    pcs = (np.round(69 + 12 * np.log2(freqs[sel] / 440.0)).astype(int)) % 12
    for i in range(0, len(x) - n, 4096):
        mag = np.abs(np.fft.rfft(x[i:i + n] * win))[sel]
        hist += np.bincount(pcs, weights=np.sqrt(mag), minlength=12)
    return key_of_hist(hist)


def audio_tempo(x, beats, expect_bpm):
    """Bar period from the autocorrelation of the low band (kick) onset flux; falls back to full band."""
    hop = 256
    n = 1024
    win = np.hanning(n)
    frames = (len(x) - n) // hop
    idx = np.arange(n)[None, :] + hop * np.arange(frames)[:, None]
    spec = np.abs(np.fft.rfft(x[idx] * win, axis=1))
    f = np.fft.rfftfreq(n, 1.0 / SR)
    out = {}
    for label, lo, hi in (("kick_band", 40, 150), ("full_band", 100, 8000)):
        band = np.log1p(30 * spec[:, (f >= lo) & (f <= hi)].sum(axis=1))
        flux = np.maximum(0, np.diff(band))
        flux = flux - flux.mean()
        ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
        ac = ac / ac[0]
        bar_lag = beats * 60.0 / expect_bpm * SR / hop
        lo_l, hi_l = int(bar_lag * 0.9), int(bar_lag * 1.1)
        k = lo_l + int(np.argmax(ac[lo_l:hi_l]))
        if 0 < k < len(ac) - 1:
            a, b, c = ac[k - 1], ac[k], ac[k + 1]
            d = (a - c) / (2 * (a - 2 * b + c)) if (a - 2 * b + c) != 0 else 0.0
        else:
            d = 0.0
        lag_s = (k + d) * hop / SR
        out[label] = {"bar_seconds": round(lag_s, 4), "bpm": round(beats * 60.0 / lag_s, 2),
                      "peak_autocorr": round(float(ac[k]), 3)}
    return out


def decode(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype="<f4").astype(np.float64)


def write_wav(path, x):
    d = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as h:
        h.setnchannels(1)
        h.setsampwidth(2)
        h.setframerate(SR)
        h.writeframes(d.tobytes())


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def volume_mean(path):
    r = run(["ffmpeg", "-hide_banner", "-i", path, "-af", "volumedetect", "-f", "null", "-"])
    for line in r.stderr.splitlines():
        if "mean_volume" in line:
            return float(line.split("mean_volume:")[1].split("dB")[0])
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cue", required=True)
    ap.add_argument("--asset-dir", required=True)
    args = ap.parse_args(argv)
    cue = final_cues.CUES[args.cue]()
    adir = os.path.abspath(os.path.join(ROOT, args.asset_dir))
    os.makedirs(adir, exist_ok=True)
    for name in os.listdir(adir):
        if name.endswith((".ogg", ".wav")):
            sys.stderr.write("refused: %s already holds %s\n" % (adir, name))
            return 2
    slug = cue.slug
    body_mid = os.path.join(adir, slug + ".mid")
    three_mid = os.path.join(adir, slug + "_x3.mid")
    with open(body_mid, "wb") as h:
        h.write(cue.midi_bytes(1))
    with open(three_mid, "wb") as h:
        h.write(cue.midi_bytes(3))
    report = {"slug": slug, "title": cue.title, "declared_key": cue.key, "bpm": cue.bpm,
              "beats_per_bar": cue.beats, "bars": cue.bars,
              "notes": {t: len(n) for t, n in cue.notes.items()}}

    gate = run([sys.executable, os.path.join(HERE, "cue_gate.py"), body_mid, "--no-baseline", "--quiet"])
    report["cue_gate"] = {"exit": gate.returncode, "stdout": gate.stdout.strip()[-400:]}
    gate_full = run([sys.executable, os.path.join(HERE, "cue_gate.py"), body_mid, "--no-baseline"])
    report["cue_gate_summary"] = [l.strip() for l in gate_full.stdout.splitlines() if "G1" in l or "state" in l]
    report["midi_key_top3"] = [(round(r, 3), k) for r, k in midi_key(cue)]

    # render the three passes as one piece
    raw3 = os.path.join(adir, slug + "_x3_raw.wav")
    rep = render_chip.render_file(three_mid, raw3, None, None, None, normalize=True, force_v2=True)
    x3 = np.frombuffer(open(raw3, "rb").read()[44:], dtype="<i2").astype(np.float64) / 32768.0
    body_samples = int(round(cue.bars * cue.beats * 60.0 / cue.bpm * SR))
    report["loop_samples"] = body_samples
    os.remove(raw3)
    if len(x3) < 3 * body_samples:
        x3 = np.concatenate([x3, np.zeros(3 * body_samples - len(x3))])
    b = x3[body_samples:2 * body_samples]
    c = x3[2 * body_samples:3 * body_samples]
    k = min(SR, body_samples)
    report["periodicity_max_abs_diff_first_second"] = round(float(np.max(np.abs(b[:k] - c[:k]))), 6)
    report["periodicity_max_abs_diff_whole"] = round(float(np.max(np.abs(b[:-300] - c[:-300]))), 6)
    dd = b[:-300] - c[:-300]
    report["periodicity_rms_diff_db"] = round(20 * float(np.log10(max(np.sqrt(np.mean(dd * dd)), 1e-9))), 2)
    report["periodicity_share_samples_differing"] = round(float(np.mean(np.abs(dd) > 0.01)), 5)

    # master: gain then limiter on the three pass signal, cut the middle, encode, measure, iterate
    src3 = os.path.join(adir, slug + "_x3.wav")
    write_wav(src3, x3)
    out_wav = os.path.join(adir, slug + "_master.wav")
    ogg = os.path.join(adir, slug + ".ogg")
    mp3 = os.path.join(adir, slug + ".mp3")
    m3 = os.path.join(adir, slug + "_m3.wav")
    gain, limit_db, attempts = 0.0, -1.9, []
    for _ in range(10):
        lim = round(10.0 ** (limit_db / 20.0), 4)
        af = "volume=%.2fdB,alimiter=level_in=1:level_out=1:limit=%.4f:attack=1:release=50:level=0" % (gain, lim)
        r = run(["ffmpeg", "-y", "-hide_banner", "-nostats", "-i", src3, "-af", af, "-ar", str(SR), m3])
        if r.returncode:
            raise RuntimeError(r.stderr[-400:])
        y = np.frombuffer(open(m3, "rb").read()[44:], dtype="<i2").astype(np.float64) / 32768.0
        write_wav(out_wav, y[body_samples:2 * body_samples])
        run(["ffmpeg", "-y", "-hide_banner", "-nostats", "-i", out_wav, "-c:a", "libvorbis", "-q:a", "5", ogg])
        got = m3_build.loudness(ogg)
        attempts.append({"gain_db": round(gain, 2), "limit_db": round(limit_db, 2),
                         "lufs": got["integrated_lufs"], "dbtp": got["true_peak_dbtp"]})
        err = TARGET_LUFS - got["integrated_lufs"]
        over = got["true_peak_dbtp"] - CEILING
        if abs(err) <= 0.15 and over <= 0:
            break
        gain += err
        if over > 0:
            limit_db -= over + 0.15
    run(["ffmpeg", "-y", "-hide_banner", "-nostats", "-i", out_wav, "-c:a", "libmp3lame", "-b:a", "192k", mp3])
    os.remove(m3)
    os.remove(src3)
    os.remove(three_mid)
    report["master_attempts"] = attempts

    d = decode(ogg)
    report["delivered"] = {"loudness": m3_build.loudness(ogg), "mean_volume_db": volume_mean(ogg),
                           "samples": int(len(d)), "seconds": round(len(d) / SR, 4)}
    report["seam"] = final_mix.seam(d.astype(np.float32), 0, len(d))
    report["audio_key_top3"] = [(round(r, 3), k_) for r, k_ in audio_key(d)]
    report["audio_tempo"] = audio_tempo(d, cue.beats, cue.bpm)
    loop = {"kind": "cue", "asset": slug, "sample_rate": SR, "channels": 1, "bpm": cue.bpm,
            "beats_per_bar": cue.beats, "loop_bars": cue.bars, "loop_start_sample": 0,
            "loop_end_sample": int(len(d)), "loop_seconds": round(len(d) / SR, 6),
            "seam_sample_difference_first_second": report["periodicity_max_abs_diff_first_second"],
            "method": "three pass render, middle pass cut"}
    with open(os.path.join(adir, slug + "_loop.json"), "w", encoding="utf-8", newline="\n") as h:
        json.dump(loop, h, indent=2)
        h.write("\n")
    with open(os.path.join(adir, "build_report.json"), "w", encoding="utf-8", newline="\n") as h:
        json.dump(report, h, indent=1, sort_keys=True)
        h.write("\n")
    dl = report["delivered"]["loudness"]
    print("%s: gate %s | midi key %s | audio key %s" % (slug, report["cue_gate"]["exit"],
          report["midi_key_top3"][0][1], report["audio_key_top3"][0][1]))
    print("  tempo audio %s vs %s | seam %s (jump %s dBFS, delta %s dB)" % (
        {k_: float(v["bpm"]) for k_, v in report["audio_tempo"].items()}, cue.bpm, report["seam"]["verdict"],
        report["seam"]["wrap_jump_dbfs"], report["seam"]["seam_level_delta_db"]))
    print("  %.2f LUFS %.2f dBTP mean %.1f dB | %.3f s | periodic rms diff %s dB" % (
        dl["integrated_lufs"], dl["true_peak_dbtp"], report["delivered"]["mean_volume_db"],
        report["delivered"]["seconds"], report["periodicity_rms_diff_db"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
