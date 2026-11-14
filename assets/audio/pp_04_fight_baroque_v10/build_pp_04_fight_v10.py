"""build_pp_04_fight_v10.py: PP-04 fight take F, the answer bar rewritten inside the window.

Card AUTO-MUSIC-NEXT (t_9c3806a0), musician lane, 2026-11-14.

Take E (pp_04_fight_baroque_v8) measures 88 of 100 on tools/hook_score.py and loses
10 of those 12 points on two criteria that are both read off the two bar motif:

    contour           2.5 of 10   1 of 4 returns arch or pedal
    leaps per motif   4.0 of 8    2 leaps

The motif is the five pitch FIGHT_SUBJECT (76 74 72 71 71) at bars 1, 5, 9, 13 plus the
seven note answer fill in the bar after each statement. The subject is the project's
leitmotif and is kept byte for byte here. The three points are in the fill, which in take E
drops out of the subject's own five semitone window (E5 76 down to G#4 68) and adds a
second leap on the way (E5 76 down to B4 71).

Take F moves only the fill. Statements 1, 2 and 4 read E5 E5 D5 C5 B4 B4 B4 (76 76 74 72
71 71 71): the leap into E5 stays, every other interval is a step, the whole bar sits inside
71 to 76 so it reads pedal, and the held B4 lands on the same pitch the subject already
holds. Statement 3 keeps the score's own varied tail (71 72) so the third return is still a
return and not a copy: 75 percent the same as the first.

Nothing else moves: every other bar, every duration, every velocity, every drum figure and
every other channel is take E's, byte for byte.

Usage: python assets/audio/pp_04_fight_baroque_v10/build_pp_04_fight_v10.py
"""
from __future__ import annotations

import json
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TOOLS = os.path.join(REPO, "tools")
SLUG = "pp_04_fight_baroque_v10"
SRC = os.path.join(REPO, "assets", "audio", "pp_04_fight_baroque_v8",
                   "pp_04_fight_baroque_v8.mid")
MELODY_TRACK = "pulse 1"

PYTHON = os.path.join(REPO, ".venv", "Scripts", "python.exe")
if not os.path.exists(PYTHON):
    PYTHON = sys.executable

# The seven answer notes of the first statement: (tick, pitch in take E).
ANSWER = [(1920, 76), (2160, 72), (2400, 74), (2640, 76), (2880, 71), (3360, 68), (3600, 69)]
HOP = 7680                      # the four statements start four bars apart
TAKE_F = [76, 76, 74, 72, 71, 71, 71]
STATEMENTS = (0, 1, 3)          # statement 2 (index 2) keeps its varied tail

midi = os.path.join(HERE, SLUG + ".mid")
wav = os.path.join(HERE, SLUG + ".wav")
out_wav = os.path.join(HERE, SLUG + "_master.wav")
ogg = os.path.join(HERE, SLUG + ".ogg")
mp3 = os.path.join(HERE, SLUG + ".mp3")
TARGET_LUFS, CEILING_DBTP = -14.0, -1.0


def run(cmd):
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)


def read_varlen(data, pos):
    val = 0
    while True:
        b = data[pos]
        pos += 1
        val = (val << 7) | (b & 0x7F)
        if not b & 0x80:
            return val, pos


def track_chunks(data):
    if data[0:4] != b"MThd":
        raise SystemExit("not a MIDI file")
    pos = 8 + struct.unpack(">I", data[4:8])[0]
    while pos + 8 <= len(data):
        cid = bytes(data[pos:pos + 4])
        clen = struct.unpack(">I", data[pos + 4:pos + 8])[0]
        body = pos + 8
        if cid == b"MTrk":
            yield body, body + clen
        pos = body + clen


def name_of(data, start, end):
    pos, tick = start, 0
    while pos < end:
        delta, pos = read_varlen(data, pos)
        tick += delta
        if data[pos] == 0xFF:
            meta = data[pos + 1]
            ln, q = read_varlen(data, pos + 2)
            if meta == 0x03:
                return bytes(data[q:q + ln]).decode("latin-1")
            pos = q + ln
            if meta == 0x2F:
                return None
            continue
        status = data[pos]
        if status & 0x80:
            pos += 1
        else:
            status = 0x90
        kind = status & 0xF0
        pos += 1 if kind in (0xC0, 0xD0) else 2
    return None


def events(data, start, end):
    """[(tick, kind, pitch, velocity, pitch_byte_offset)]"""
    out = []
    pos, running, tick = start, None, 0
    while pos < end:
        delta, pos = read_varlen(data, pos)
        tick += delta
        if data[pos] == 0xFF:
            meta = data[pos + 1]
            ln, q = read_varlen(data, pos + 2)
            if meta == 0x2F:
                break
            pos = q + ln
            continue
        status = data[pos]
        if status & 0x80:
            pos += 1
            if status < 0xF0:
                running = status
        else:
            status = running
        kind = status & 0xF0
        if kind in (0xC0, 0xD0):
            pos += 1
            continue
        out.append((tick, kind, data[pos], data[pos + 1], pos))
        pos += 2
    return out


def melody_chunk(data):
    for start, end in track_chunks(data):
        if name_of(data, start, end) == MELODY_TRACK:
            return start, end
    raise SystemExit("no %r track in the source score" % MELODY_TRACK)


def write_take(src_path, out_path):
    """Patch the answer fill of statements 1, 2 and 4; leave every other byte alone."""
    data = bytearray(open(src_path, "rb").read())
    start, end = melody_chunk(data)
    evs = events(bytes(data), start, end)
    edits = []
    for k in STATEMENTS:
        for (tick, old), new in zip(ANSWER, TAKE_F):
            if new != old:
                edits.append((tick + HOP * k, old, new))
    hits, missing = [], []
    for tick, old, new in edits:
        ons = [e for e in evs if e[0] == tick and e[1] == 0x90 and e[2] == old and e[3] > 0]
        offs = [e for e in evs if ons and e[0] > ons[0][0] and e[2] == old
                and (e[1] == 0x80 or (e[1] == 0x90 and e[3] == 0))]
        if not ons or not offs:
            missing.append((tick, old, new))
            continue
        data[ons[0][4]] = new
        data[offs[0][4]] = new
        hits.append((tick, old, new))
    if missing:
        raise SystemExit("unpatched notes: %r" % (missing,))
    with open(out_path, "wb") as handle:
        handle.write(bytes(data))
    return hits


def loudness(path):
    out = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
               "-filter_complex", "ebur128=peak=true", "-f", "null", "-"]).stderr
    tail = out[out.rfind("Summary:"):]
    lufs = dbtp = None
    for line in tail.splitlines():
        line = line.strip()
        if line.startswith("I:") and lufs is None:
            lufs = float(line.split()[1])
        if line.startswith("Peak:") and dbtp is None:
            dbtp = float(line.split()[1])
    return {"integrated_lufs": lufs, "true_peak_dbtp": dbtp}


def master(src_wav):
    probe = run(["ffmpeg", "-hide_banner", "-nostats", "-i", src_wav,
                 "-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json",
                 "-f", "null", "-"]).stderr
    blob = probe[probe.rfind("{"):probe.rfind("}") + 1]
    first = json.loads(blob)
    filt = ("loudnorm=I=-14:TP=-1:LRA=11:measured_I=%s:measured_TP=%s:"
            "measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true:print_format=json"
            % (first["input_i"], first["input_tp"], first["input_lra"],
               first["input_thresh"], first["target_offset"]))
    run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", src_wav, "-af", filt,
         "-ar", "48000", out_wav])
    run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", out_wav,
         "-c:a", "libvorbis", "-q:a", "6", ogg])
    run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", out_wav,
         "-c:a", "libmp3lame", "-q:a", "2", mp3])


def main():
    hits = write_take(SRC, midi)
    print("patched %d note(s) into %s" % (len(hits), os.path.basename(midi)))
    # The delivered stream is rendered from the plain score, so the score on paper and the
    # score of the stream the game would play are the same number (take E's card learned
    # this the hard way with v7).
    render = run([PYTHON, os.path.join(TOOLS, "render_chip.py"), midi, wav,
                  "--loop-bars", "16",
                  "--hook-report", os.path.join(HERE, "hook_report.json"),
                  "--loop-json", os.path.join(HERE, SLUG + "_loop.json")])
    print(render.stdout[-2000:], render.stderr[-2000:])
    if render.returncode or not os.path.exists(wav):
        return 1
    before = loudness(wav)
    master(wav)
    delivered = loudness(ogg)

    # The humanize pass is kept beside the stream, not under it: it adds ornaments and grace
    # notes that move the motif finder off bars 1 to 2, and that costs 12 hook points. Both
    # numbers are written down here so the trade is visible rather than asserted.
    sys.path.insert(0, TOOLS)
    import humanize as humanize_mod
    human_bytes, human_report = humanize_mod.humanize_bytes(open(midi, "rb").read(), name=midi)
    human_midi = os.path.join(HERE, SLUG + "_humanized.mid")
    with open(human_midi, "wb") as handle:
        handle.write(human_bytes)
    human_wav = os.path.join(HERE, SLUG + "_humanized.wav")
    human_render = run([PYTHON, os.path.join(TOOLS, "render_chip.py"), human_midi, human_wav,
                        "--loop-bars", "16", "--no-mp3"])
    import hook_score
    plain_hook = hook_score.score_file(midi)
    human_hook = hook_score.score_file(human_midi)
    with open(os.path.join(HERE, "hook_report_humanized.json"), "w", encoding="utf-8",
              newline="\n") as handle:
        json.dump(human_hook, handle, indent=2, sort_keys=True)
        handle.write("\n")

    report = {
        "source_score": os.path.relpath(SRC, REPO),
        "rendered_from": os.path.basename(midi),
        "humanize": False,
        "humanize_note": ("the delivered stream is the plain score; take F's humanize pass is "
                          "beside it as %s, scoring %d of 100 against %d, because its ornaments "
                          "move the motif off bars 1 to 2"
                          % (os.path.basename(human_midi), human_hook["score"],
                             plain_hook["score"])),
        "hook_score": plain_hook["score"],
        "hook_score_humanized": human_hook["score"],
        "humanize_render_ok": human_render.returncode == 0,
        "humanize_report": human_report,
        "patched_notes": len(hits),
        "patched": hits,
        "render_stdout": render.stdout.strip().splitlines()[-6:],
        "loudness_before": before,
        "delivered_ogg": delivered,
        "target": {"integrated_lufs": TARGET_LUFS, "ceiling_dbtp": CEILING_DBTP},
        "files": [os.path.basename(p) for p in (midi, wav, out_wav, ogg, mp3)],
    }
    with open(os.path.join(HERE, "build_report.json"), "w", encoding="utf-8",
              newline="\n") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print("delivered %.2f LUFS / %.2f dBTP" %
          (delivered["integrated_lufs"], delivered["true_peak_dbtp"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
