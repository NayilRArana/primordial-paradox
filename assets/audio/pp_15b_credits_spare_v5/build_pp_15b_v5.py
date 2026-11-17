"""build_pp_15b_v5.py: PP-15b Mercy take E, the heard take put on the hook.

Card t_60dbe406 (AUTO-MUSIC-NEXT, musician), 2026-11-16.

Take D (pp_15b_credits_spare_v4) is untouched: this script only reads it. Take D scores 100 on the
plain score and 96 on its humanized sibling (its own doc calls that sibling "not recommended"), so
the open work on this cue is the heard take: with the humanize pass applied, the melody's best 2 bar
motif moves to bar 21 where only 45 percent of its intervals are steps (floor 65 percent).

What this script writes, into assets/audio/pp_15b_credits_spare_v5/:

    pp_15b_credits_spare_v5.mid            take D's score, byte for byte (sha256 checked)
    pp_15b_credits_spare_v5_humanized.mid  the heard take: take D's score through
                                           tools/humanize.py, plus a measured pitch repair
    pp_15b_credits_spare_v5.wav / .mp3/.ogg, _master.wav, _loop.json
    hook_report_v5*.json, humanize_report_v5.json, repair_report_v5.json, build_report.json

The repair is not hand written: the script tries every allowed semitone move of every melody note
inside the motif's returns, keeps only moves that raise the hook score and pass the counterpoint
gate, and stops at the first one that takes the heard take to 100.
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

SLUG = "pp_15b_credits_spare_v5"
SRC = os.path.join(REPO, "assets", "audio", "pp_15b_credits_spare_v4",
                   "pp_15b_credits_spare_v4.mid")
SRC_HUMAN = os.path.join(REPO, "assets", "audio", "pp_15b_credits_spare_v4",
                         "pp_15b_credits_spare_v4_humanized.mid")
MIDI = os.path.join(HERE, SLUG + ".mid")
HUMAN = os.path.join(HERE, SLUG + "_humanized.mid")
WAV = os.path.join(HERE, SLUG + ".wav")
MASTER = os.path.join(HERE, SLUG + "_master.wav")
OGG = os.path.join(HERE, SLUG + ".ogg")
MP3 = os.path.join(HERE, SLUG + ".mp3")
TMP = os.path.join(HERE, "_candidate.mid")
CUE_GATE = os.path.join(TOOLS, "counterpoint", "cue_gate.py")
DELTAS = (1, -1, 2, -2)
MAX_TRIALS = 220


def sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def run(argv):
    print("$", " ".join(argv))
    return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def score(path):
    return hook_score.score_file(path)


def gate(path):
    done = run([sys.executable, CUE_GATE, path])
    return {"exit": done.returncode,
            "stdout": (done.stdout or "").strip()[-600:],
            "stderr": (done.stderr or "").strip()[-600:]}


def loudness(path):
    probe = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                 "-af", "loudnorm=print_format=json", "-f", "null", "-"]).stderr
    blob = probe[probe.rfind("{"):probe.rfind("}") + 1]
    return json.loads(blob)


def dump(name, data):
    with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main():
    os.makedirs(HERE, exist_ok=True)
    shutil.copyfile(SRC, MIDI)
    src_sha = sha256(MIDI)
    print("score copied, sha256", src_sha)

    base = score(MIDI)
    dump("hook_report_v5.json", base)
    print("plain score: hook %d, %d bars, %d notes" % (base["score"], base["bars"], base["notes"]))

    # take D's own humanized sibling, measured again here as the "before" heard take
    before = score(SRC_HUMAN)
    print("take D heard (humanized): hook %d, weakest %s" % (before["score"], before["weakest"]["criterion"]))

    # candidate heard takes: the humanize pass at each ornament placement it offers
    candidates = []
    for label, pick in (("default", 0), ("second", 1), ("none", None)):
        out = os.path.join(HERE, "_cand_%s.mid" % label)
        rep = humanize.humanize_file(MIDI, out, ornament_pick=pick)
        scored = score(out)
        candidates.append({"label": label, "ornament_pick": str(pick), "path": out,
                           "score": scored["score"], "notes": scored["notes"],
                           "weakest": scored["weakest"]["criterion"],
                           "humanize": {k: rep[k] for k in ("grace_notes", "mordents", "fills",
                                                            "breaths", "vibrato_notes",
                                                            "notes_changed", "sha256_out")}})
        print("humanize %-8s hook %d, %d notes, weakest %s"
              % (label, scored["score"], scored["notes"], scored["weakest"]["criterion"]))
    candidates.sort(key=lambda row: -row["score"])
    best = candidates[0]
    print("best humanize placement: %s at %d" % (best["label"], best["score"]))

    # the repair: semitone moves on melody notes inside the motif returns, gate checked
    song = hook_score.read_smf(best["path"])
    melody = hook_score.pick_melody_track(song)
    report = score(best["path"])
    tpb = song["time_sig"][0] * song["division"]
    bars = []
    if report["motif"]:
        bars = [b - 1 for b in report["motif"]["occurrence_bars"]]
    inside = [i for i, note in enumerate(melody["notes"])
              if int(note[0] // tpb) in bars]
    print("melody %r: %d notes, %d inside the motif returns"
          % (melody["name"], len(melody["notes"]), len(inside)))

    best_score = report["score"]
    repair = {"applied": False, "trials": 0, "accepted": None, "history": []}
    if best_score < 100 and inside:
        original = list(melody["notes"])
        for index in inside:
            if repair["applied"]:
                break
            start, end, pitch, velocity = original[index]
            for delta in DELTAS:
                if repair["trials"] >= MAX_TRIALS:
                    break
                new_pitch = pitch + delta
                if not 36 <= new_pitch <= 96:
                    continue
                melody["notes"] = list(original)
                melody["notes"][index] = (start, end, new_pitch, velocity)
                humanize.write_smf(song, TMP)
                trial = score(TMP)
                repair["trials"] += 1
                repair["history"].append({"note": index, "bar": int(start // tpb) + 1,
                                          "from": pitch, "to": new_pitch,
                                          "score": trial["score"]})
                if trial["score"] < best_score:
                    continue
                if trial["score"] == best_score and best_score < 100:
                    continue
                got = gate(TMP)
                if got["exit"] != 0:
                    repair["history"][-1]["gate"] = "refused"
                    continue
                repair["applied"] = True
                repair["accepted"] = {"note": index, "bar": int(start // tpb) + 1,
                                      "from": pitch, "to": new_pitch,
                                      "score": trial["score"], "gate": got["stdout"]}
                shutil.copyfile(TMP, HUMAN)
                best_score = trial["score"]
                break
        melody["notes"] = list(original)
        if not repair["applied"]:
            shutil.copyfile(best["path"], HUMAN)
    else:
        shutil.copyfile(best["path"], HUMAN)
    dump("repair_report_v5.json", repair)
    print("repair: applied=%s, trials=%d, accepted=%s"
          % (repair["applied"], repair["trials"], repair["accepted"]))

    after = score(HUMAN)
    dump("hook_report_v5_humanized.json", after)
    print("heard take: hook %d, %d notes, weakest %s"
          % (after["score"], after["notes"], after["weakest"]["criterion"]))
    heard_gate = gate(HUMAN)

    # the render, master and delivered stream, the same chain take D used
    render = run([sys.executable, os.path.join(TOOLS, "render_chip.py"), HUMAN, WAV,
                  "--loop-bars", "32", "--loop-json", os.path.join(HERE, SLUG + "_loop.json")])
    print(render.stdout[-1200:], render.stderr[-1200:])
    if render.returncode or not os.path.exists(WAV):
        print("RENDER FAILED")
        return 1
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

    with open(os.path.join(HERE, SLUG + "_loop.json"), encoding="utf-8") as handle:
        loop = json.load(handle)

    facts = {
        "cue": "PP-15b Mercy",
        "score_midi": os.path.basename(MIDI),
        "score_sha256": src_sha,
        "heard_midi": os.path.basename(HUMAN),
        "heard_sha256": sha256(HUMAN),
        "before": {"take": "pp_15b_credits_spare_v4", "plain": base["score"],
                   "heard_hook": before["score"],
                   "heard_weakest": before["weakest"]["criterion"]},
        "after": {"heard_hook": after["score"], "heard_notes": after["notes"],
                  "heard_weakest": after["weakest"]["criterion"],
                  "heard_gate_exit": heard_gate["exit"]},
        "humanize_candidates": [{k: row[k] for k in ("label", "score", "notes", "weakest")}
                                for row in candidates],
        "repair": {"applied": repair["applied"], "trials": repair["trials"],
                   "accepted": repair["accepted"]},
        "loop": {"loop_bars": loop.get("loop_bars"),
                 "seam_sample_difference_first_second": loop.get("seam_sample_difference_first_second"),
                 "bpm": loop.get("bpm")},
        "delivered": {"integrated_lufs": delivered.get("input_i"),
                      "true_peak_dbtp": delivered.get("input_tp"),
                      "ogg_bytes": os.path.getsize(OGG),
                      "mp3_bytes": os.path.getsize(MP3),
                      "master_bytes": os.path.getsize(MASTER)},
    }
    dump("build_report.json", facts)
    print(json.dumps(facts, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
