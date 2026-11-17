"""remaster_v5.py: put the take D chain's -14 LUFS / -1 dBTP delivery on take E.

The first master of take E came out at -0.23 dBTP on the OGG, over the -1 dBTP ceiling, because the
linear loudnorm pass targeted -1.0 and the codecs put a little back. This script redoes the master
from the same WAV with a target of -1.6 dBTP, measures the delivered OGG, and if the ceiling is
still broken lowers the true peak target again, up to four attempts.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SLUG = "pp_15b_credits_spare_v5"
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


def main():
    first = loudness(WAV)
    attempts = []
    for tp_target in (-1.6, -2.1, -2.6, -3.1):
        filt = ("loudnorm=I=-14:TP=%.1f:LRA=11:measured_I=%s:measured_TP=%s:"
                "measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true:print_format=json"
                % (tp_target, first["input_i"], first["input_tp"], first["input_lra"],
                   first["input_thresh"], first["target_offset"]))
        run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", WAV, "-af", filt,
             "-ar", "48000", "-c:a", "pcm_s16le", MASTER])
        run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", MASTER,
             "-c:a", "libvorbis", "-q:a", "6", OGG])
        got = loudness(OGG)
        attempts.append({"tp_target": tp_target, "lufs": got["input_i"], "tp": got["input_tp"]})
        print("tp target %.1f -> OGG %.2f LUFS, %.2f dBTP" % (tp_target, float(got["input_i"]),
                                                              float(got["input_tp"])))
        if float(got["input_tp"]) <= -1.0 and float(got["input_i"]) <= -13.5:
            break
    run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", MASTER,
         "-c:a", "libmp3lame", "-q:a", "2", MP3])
    out = {"attempts": attempts, "master_bytes": os.path.getsize(MASTER),
           "ogg_bytes": os.path.getsize(OGG), "mp3_bytes": os.path.getsize(MP3)}
    with open(os.path.join(HERE, "master_report_v5.json"), "w", encoding="utf-8",
              newline="\n") as handle:
        json.dump(out, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
