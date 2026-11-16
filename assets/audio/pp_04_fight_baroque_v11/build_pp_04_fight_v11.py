"""PP-04 fight, take G (pp_04_fight_baroque_v11): the heard stream carries the humanize pass.

Card t_1064983c (AUTO-MUSIC-NEXT, musician), 2026-11-16.

Take F (pp_04_fight_baroque_v10) is untouched: this script only reads it. What it writes:

    pp_04_fight_baroque_v11.mid              take F's score, byte for byte
    pp_04_fight_baroque_v11_humanized.mid    the same score through tools/humanize.py, ornament
                                             placement "none" (round 3 of 4)
    pp_04_fight_baroque_v11.wav / .mp3       the render of the humanized take
    pp_04_fight_baroque_v11_master.wav       -14 LUFS / -1 dBTP master of that render
    pp_04_fight_baroque_v11.ogg              the delivered stream, from the master
    pp_04_fight_baroque_v11_loop.json        seam and level measurements
    hook_report_v11.json                     the score grid
    hook_report_v11_humanized.json           the heard grid
    humanize_report_v11.json                 what the pass applied
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TOOLS = os.path.join(REPO, "tools")
sys.path.insert(0, TOOLS)
import hook_score  # noqa: E402
import humanize  # noqa: E402

SLUG = "pp_04_fight_baroque_v11"
SRC = os.path.join(REPO, "assets", "audio", "pp_04_fight_baroque_v10",
                   "pp_04_fight_baroque_v10.mid")
SRC_SHA = "301158ed2ff98c9f921d97b811954839189e8f41316bf4a5b32c0b98d90a7cac"
MIDI = os.path.join(HERE, SLUG + ".mid")
HUMAN = os.path.join(HERE, SLUG + "_humanized.mid")
WAV = os.path.join(HERE, SLUG + ".wav")
MASTER = os.path.join(HERE, SLUG + "_master.wav")
OGG = os.path.join(HERE, SLUG + ".ogg")
MP3 = os.path.join(HERE, SLUG + ".mp3")


def sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def run(argv):
    print("$", " ".join(argv))
    return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def loudness(path):
    probe = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                 "-af", "loudnorm=print_format=json", "-f", "null", "-"]).stderr
    blob = probe[probe.rfind("{"):probe.rfind("}") + 1]
    return json.loads(blob)


def main():
    # 1. the score: take F's own bytes, nothing rewritten
    shutil.copyfile(SRC, MIDI)
    assert sha256(MIDI) == SRC_SHA, "the copied score is not take F's score"
    print("score copied, sha256", SRC_SHA)

    # 2. the heard take: the humanize pass with the ornament placed nowhere
    report = humanize.humanize_file(MIDI, HUMAN, ornament_pick=None)
    with open(os.path.join(HERE, "humanize_report_v11.json"), "w", encoding="utf-8",
              newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("humanize: notes %d, ornaments %d/%d, fills %d, sha256 %s"
          % (report["notes_out"], report["grace_notes"], report["mordents"],
             report["fills"], report["sha256_out"]))

    # 3. both scores, one grid each
    for target, out in ((MIDI, "hook_report_v11.json"),
                        (HUMAN, "hook_report_v11_humanized.json")):
        scored = hook_score.score_file(target)
        with open(os.path.join(HERE, out), "w", encoding="utf-8", newline="\n") as handle:
            json.dump(scored, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print("%-28s hook %d / 100, melody %d notes"
              % (os.path.basename(target), scored["score"], scored["notes"]))

    # 4. the render: from the humanized take, 16 bar loop, same renderer as take F
    render = run([sys.executable, os.path.join(TOOLS, "render_chip.py"), HUMAN, WAV,
                  "--loop-bars", "16",
                  "--loop-json", os.path.join(HERE, SLUG + "_loop.json")])
    print(render.stdout[-1500:], render.stderr[-1500:])
    if render.returncode or not os.path.exists(WAV):
        return 1

    # 5. the master and the delivered stream, the same chain take F used
    first = loudness(WAV)
    filt = ("loudnorm=I=-14:TP=-1:LRA=11:measured_I=%s:measured_TP=%s:"
            "measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true:print_format=json"
            % (first["input_i"], first["input_tp"], first["input_lra"],
               first["input_thresh"], first["target_offset"]))
    run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", WAV, "-af", filt,
         "-ar", "48000", "-c:a", "pcm_s16le", MASTER])
    run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", MASTER,
         "-c:a", "libvorbis", "-q:a", "6", OGG])
    run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", MASTER,
         "-c:a", "libmp3lame", "-q:a", "2", MP3])
    delivered = loudness(OGG)

    facts = {
        "score": os.path.basename(MIDI),
        "score_sha256": SRC_SHA,
        "humanized": os.path.basename(HUMAN),
        "humanized_sha256": sha256(HUMAN),
        "rendered_from": os.path.basename(HUMAN),
        "wav": {"bytes": os.path.getsize(WAV)},
        "master_wav": {"bytes": os.path.getsize(MASTER),
                       "integrated_lufs": delivered.get("input_i"),
                       "true_peak_dbtp": delivered.get("input_tp")},
        "ogg_bytes": os.path.getsize(OGG),
        "mp3_bytes": os.path.getsize(MP3),
        "humanize": {"ornament_pick": "none", "notes_out": report["notes_out"],
                     "grace_notes": report["grace_notes"],
                     "mordents": report["mordents"], "fills": report["fills"],
                     "notes_changed": report["notes_changed"],
                     "breaths": report["breaths"],
                     "vibrato_notes": report["vibrato_notes"],
                     "envelope_points": report["envelope_points"]},
        "delivered_loudness": {"integrated_lufs": delivered.get("input_i"),
                               "true_peak_dbtp": delivered.get("input_tp")},
    }
    with open(os.path.join(HERE, "build_report.json"), "w", encoding="utf-8",
              newline="\n") as handle:
        json.dump(facts, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(facts, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
