"""limit_master_v6.py: hit -14 LUFS with a true peak ceiling of -1 dBTP on PP-06 take F.

The same fixed gain plus look-ahead limiter shape take E of PP-15b used, walked until the delivered
OGG lands inside -14.2 to -13.8 LUFS with a true peak at or under -1.0 dBTP.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SLUG = "pp_06_percy_possessed_v6"
WAV = os.path.join(HERE, SLUG + ".wav")
MASTER = os.path.join(HERE, SLUG + "_master.wav")
OGG = os.path.join(HERE, SLUG + ".ogg")
MP3 = os.path.join(HERE, SLUG + ".mp3")


def run(argv):
    return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def loudness(path):
    probe = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                 "-af", "loudnorm=print_format=json", "-f", "null", "-"]).stderr
    blob = probe[probe.rfind("{"):probe.rfind("}") + 1]
    return json.loads(blob)


def build(gain_db, limit_db):
    limit = 10 ** (limit_db / 20.0)
    filt = "volume=%.2fdB,alimiter=level=disabled:limit=%.5f:attack=5:release=80" % (
        gain_db, limit)
    run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", WAV, "-af", filt,
         "-ar", "48000", "-c:a", "pcm_s16le", MASTER])
    run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", MASTER,
         "-c:a", "libvorbis", "-q:a", "6", OGG])
    return loudness(OGG)


def main():
    gain = 2.5
    history = []
    best = None
    for _ in range(6):
        got = build(gain, -2.6)
        lufs, tp = float(got["input_i"]), float(got["input_tp"])
        history.append({"gain_db": round(gain, 2), "lufs": lufs, "tp": tp})
        print("gain %.2f dB -> %.2f LUFS, %.2f dBTP" % (gain, lufs, tp))
        best = (gain, lufs, tp)
        if -14.2 <= lufs <= -13.8 and tp <= -1.0:
            break
        gain += (-14.0 - lufs)
        if tp > -1.0:
            gain -= (tp + 1.1)
    run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", MASTER,
         "-c:a", "libmp3lame", "-q:a", "2", MP3])
    out = {"history": history,
           "final": {"gain_db": round(best[0], 2), "lufs": best[1], "tp": best[2]},
           "master_bytes": os.path.getsize(MASTER), "ogg_bytes": os.path.getsize(OGG),
           "mp3_bytes": os.path.getsize(MP3)}
    with open(os.path.join(HERE, "master_report_v6.json"), "w", encoding="utf-8",
              newline="\n") as handle:
        json.dump(out, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
