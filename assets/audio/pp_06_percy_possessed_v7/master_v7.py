"""master_v7.py: bring PP-06 take G to the lane's shipping target with a true peak ceiling.

House chain (tools/final_mix.py): fixed gain, then a 5 ms attack look-ahead limiter; the shipping
ceiling is -0.5 dBTP because a Vorbis decode overshoots its sample peak by about 0.8 dB. The walk
below tries a small grid and keeps the first pass that stays under -0.5 dBTP.
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SLUG = "pp_06_percy_possessed_v7"
WAV = os.path.join(HERE, SLUG + ".wav")
MASTER = os.path.join(HERE, SLUG + "_master.wav")
OGG = os.path.join(HERE, SLUG + ".ogg")
MP3 = os.path.join(HERE, SLUG + ".mp3")
TARGET_LUFS = -14.0
TP_CEIL = -0.5


def run(argv):
    return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def loudness(path):
    probe = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                 "-af", "loudnorm=print_format=json", "-f", "null", "-"]).stderr
    return json.loads(probe[probe.rfind("{"):probe.rfind("}") + 1])


def build(gain_db, limit_db, write=True):
    limit = 10 ** (limit_db / 20.0)
    filt = "volume=%.2fdB,alimiter=level=disabled:limit=%.5f:attack=5:release=80" % (
        gain_db, limit)
    master = MASTER if write else MASTER + ".probe.wav"
    ogg = OGG if write else OGG + ".probe.ogg"
    run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", WAV, "-af", filt,
         "-ar", "44100", "-c:a", "pcm_s16le", master])
    run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", master,
         "-c:a", "libvorbis", "-q:a", "6", ogg])
    return loudness(ogg)


def main():
    base = loudness(WAV)
    print("source", base["input_i"], "LUFS", base["input_tp"], "dBTP")
    gain0 = TARGET_LUFS - float(base["input_i"])
    table = []
    best = None
    for step in range(8):
        gain = gain0 - 0.1 * step
        row = None
        for limit_db in (-1.0, -1.6, -2.2):
            meas = build(gain, limit_db, write=False)
            row = {"gain_db": round(gain, 2), "limit_db": limit_db,
                   "lufs": float(meas["input_i"]), "tp": float(meas["input_tp"]),
                   "lra": float(meas["input_lra"])}
            table.append(row)
            if row["tp"] <= TP_CEIL:
                break
        print(row)
        if row["tp"] <= TP_CEIL:
            best = row
            break
    if best is None:
        raise SystemExit("master_v7: no pass got under %.1f dBTP" % TP_CEIL)
    final = build(best["gain_db"], best["limit_db"], write=True)
    run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", MASTER,
         "-c:a", "libmp3lame", "-b:a", "192k", MP3])
    for stray in (MASTER + ".probe.wav", OGG + ".probe.ogg"):
        if os.path.exists(stray):
            os.remove(stray)
    report = {"slug": SLUG, "source": WAV, "master": MASTER, "ogg": OGG, "mp3": MP3,
              "chosen": best, "passes": table, "final": {
                  "lufs": float(final["input_i"]), "tp": float(final["input_tp"]),
                  "lra": float(final["input_lra"])}}
    with open(os.path.join(HERE, "master_report_v7.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1)
    print("final", report["final"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
