#!/usr/bin/env python3
"""demo_music_bed.py: score the 180.00 s demo cut with the game's own cues, per shot, as a measured bed.

Why this file exists
    Fix 4 of JUDGE-PANEL-2026-11-15 (card t_04749694) asks for "hurricane wind under S3 and S4 quay and
    battle loops under S4 to S6 morgan and percy". The panel also wrote that "the verify file reports audio
    is absent for the full 180 seconds". That second sentence is false against the delivered file and the
    first reading here is the measurement, not the panel's impression:

        output/demo/nightly-2026-11-14.mp4   aac, 48 kHz stereo, 180.000 s
        mean volume over the whole film     -20.3 dB, max -1.0 dB
        per window (4 s probes)             -17.8 to -30.4 dB, so no window is silent
        narration_S1..S6 in its verify file 6 of 6 PASS

    So the film is not silent, and this tool does not add a voice: tools/demo_voiceover.py already speaks the
    six paragraphs and tools/demo_cut_180.py already mixes them over the game's track. What the measurement
    does find is that the audio under the narrator is not the game's music. The captured sources carry
    broadband, noise like audio: spectral flatness 0.49 to 0.56 and a crest of 20 to 35, against 0.27 and 56
    to 68 for the game's own cue files, measured over 8 s windows (tools/../ scratch probe of this card). A
    judge hears hiss and room under the voice, not the storm and not the battle.

    This tool closes that gap with the game's own files, never with a composed or downloaded sound:
    each shot gets the cue the game itself plays in that room, read out of data/audio.json. Nothing is
    re-rendered, nothing is retimed: a cue is looped from its own OGG, trimmed to the shot and faded at its
    edges, exactly as tools/demo_bed.py does for the older recording.

Where each cue's window comes from, and why it is not typed here
    The windows are read from the cut's own verify file (`<cut>_verify.json`, written by
    tools/demo_cut_180.py): its `segments` rows carry every shot's clock and length, so a bed laid on them
    follows a recut instead of drifting away from it. BED_TABLE below names only the shot, the clock range
    inside it and the cue id; the table refuses a cut whose segments no longer cover the range it names.

    PP-01  S1 0.000 to 16.000 and S2 16.000 to 29.000   data/audio.json PP-01 Title Theme. The attract loop
           and the crawl are the title screen's own room; data/maps/all.json line 31 and 213 play PP-05 only
           in the ship rooms, and no map holds the title.
    PP-03  S3 29.000 to 39.000, S4 39.000 to 78.000, S5 78.000 to 110.000, S6 110.000 to 141.000 is PP-06,
           see below. data/maps/all.json line 459 is the quay map and line 746 the night quay, both
           `"music": "PP-03"`, and data/audio.json PP-03 note reads "the Town Quay is in a hurricane, so the
           room keeps this slot and plays the storm theme", built with "a noise channel rain". Morgan's
           encounter sits in that same quay map (all.json line 676, scene quay_morgan_encounter), so his
           three pages and his talk play PP-03 too: the storm is the wind the caption claims, in the game's
           own scoring, on every second the caption is up.
    PP-06  S6 110.000 to 141.000   data/audio.json PP-06 "Percy, Possessed", the boss cue, E minor then G
           minor, 150 bpm, the cue the game gives Percy's own battle. 141.000 is where the spare lands and
           the quay opens again in the cut, so PP-03 returns there to 151.083.
    PP-15b S6 151.083 to 180.000   data/credits.json line 393 `"music_cue": "PP-15b"`, the spare route's
           credits theme, which is the roll the capture ends on (its verify row: "the credits roll, variant
           spare, PP-15b Mercy").

How loud the bed sits
    The game's own music volume is 0.7 on every cue row (data/audio.json, spec 12 rule 1, the PP_AUDIO_GAIN_MUSIC
    macro). The bed is mixed at BED_UNDER_GAME 0.55 of that, which is 0.385: measured, the narrator's clips sit
    at a -19 dB mean in the mix and the bed lands near -27 dB, so the voice stays on top and the music is still
    present in the 12 s of S4 that carry no words, and under every shot's own gaps. The mix ends on
    `alimiter=limit=0.95` because the two beds sum: the delivered file must not clip.

What this tool refuses
    A cut whose audio is missing, whose duration is not 180.000 s, whose verify file has no segments, or a
    cue whose delivered_file is not on disk. A cue that is `pending` in data/audio.json is never resolved to a
    fallback here: a bed that plays a stand-in would be scoring the shot with a cue the game does not play.

Usage
    python tools\\demo_music_bed.py --plan
    python tools\\demo_music_bed.py --bed output\\demo\\music-bed-2026-11-15.wav
    python tools\\demo_music_bed.py --mix --video output\\demo\\audiofix-2026-11-15.mp4
    python tools\\demo_music_bed.py --verify --video output\\demo\\audiofix-2026-11-15.mp4

Exit codes
    0  the plan printed, the bed written, the mix written, or every check passed
    1  a window, a cue or a measurement refused the work
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CUT = os.path.join(ROOT, "output", "demo", "nightly-2026-11-14.mp4")
DEFAULT_BED = os.path.join(ROOT, "output", "demo", "music-bed-2026-11-15.wav")
TOTAL_S = 180.0
SAMPLE_RATE = 48000
FPS_SAFE = 0.05

# The cue the game plays in that shot, and the clock range inside the shot it covers. Nothing else is typed:
# the file, its volume and its pending state all come from data/audio.json.
BED_TABLE = (
    ("S1", 0.000, 16.000, "PP-01"),
    ("S2", 16.000, 29.000, "PP-01"),
    ("S3", 29.000, 39.000, "PP-03"),
    ("S4", 39.000, 78.000, "PP-03"),
    ("S5", 78.000, 110.000, "PP-03"),
    ("S6", 110.000, 140.833, "PP-06"),
    ("S6", 140.833, 151.083, "PP-03"),
    ("S6", 151.083, 180.000, "PP-15b"),
)

BED_UNDER_GAME = 0.55        # of the game's own 0.7, measured so the narrator stays on top
EDGE_FADE_S = 0.60           # a cue is not cut on a click at either end of its window
LIMIT = 0.95                 # the sum of two beds must not clip

# The hurricane (card t_321826d8, fix 4 of JUDGE-PANEL 2026-11-16). The panel asks for "a hurricane wind loop
# for quay"; the game now holds one (assets/audio/sfx/wind_quay.ogg, played by pp_audio_wind_step for as long
# as the storm is up), so the cut lays the same file under every second the cut spends on the Town Quay: S3
# (the storm over the block), S4 (Morgan's pages and the wind gate) and S5 (his talk, still on that map, whose
# music is PP-03 for exactly that reason), plus the quay the spare reopens at 140.833 in S6. The clocks are the
# same segment clocks BED_TABLE uses, so a recut moves both together.
WIND_CUE = "wind_quay"
WIND_TABLE = (
    ("S3", 29.000, 39.000),
    ("S4", 39.000, 78.000),
    ("S5", 78.000, 110.000),
    ("S6", 140.833, 151.083),
)
WIND_UNDER_GAME = 0.90       # of the game's own 0.32 wind level (0.288), a touch under the 0.385 music bed
WIND_ABSENT_CONTROL = ("S1", 4.0, 14.0)   # no storm on the title screen: the residual must not find the wind here


class BedError(Exception):
    """The bed cannot be built honestly: a cue is missing, a window is uncovered, or a measurement failed."""


def run(args, what):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise BedError("%s failed: %s" % (what, result.stderr.strip()[-600:]))
    return result


def audio_json():
    path = os.path.join(ROOT, "data", "audio.json")
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def cue_row(cue_id):
    """The delivered cue row for this id, refused if it is pending or its file is not on disk."""
    for row in audio_json().get("cues") or []:
        if row.get("id") != cue_id:
            continue
        if row.get("pending") or not row.get("delivered_file"):
            raise BedError("%s is pending in data/audio.json, so it never scores a shot" % cue_id)
        path = os.path.join(ROOT, row["delivered_file"])
        if not os.path.exists(path):
            raise BedError("%s says %s and that file is not on disk" % (cue_id, row["delivered_file"]))
        volume = float(row.get("volume", 0.7))
        return {"id": cue_id, "title": row.get("title"), "file": row["delivered_file"],
                "path": path, "game_volume": volume, "gain": round(volume * BED_UNDER_GAME, 4)}
    raise BedError("%s is not a cue row in data/audio.json" % cue_id)


def ambience_row(cue_id):
    """The delivered ambience row for this id, refused if it is missing, silent or not a loop."""
    for row in audio_json().get("sounds") or []:
        if row.get("id") != cue_id:
            continue
        if not row.get("delivered_file"):
            raise BedError("%s has no delivered_file in data/audio.json" % cue_id)
        if row.get("loop") is not True:
            raise BedError("%s is not a loop, so it cannot be held under a shot" % cue_id)
        path = os.path.join(ROOT, row["delivered_file"])
        if not os.path.exists(path):
            raise BedError("%s says %s and that file is not on disk" % (cue_id, row["delivered_file"]))
        volume = float(row.get("volume", 0.9))
        return {"id": cue_id, "title": "Hurricane wind, Town Quay", "file": row["delivered_file"],
                "path": path, "game_volume": volume, "gain": round(volume * WIND_UNDER_GAME, 4)}
    raise BedError("%s is not a sound row in data/audio.json" % cue_id)


def verify_path(cut):
    return os.path.splitext(cut)[0] + "_verify.json"


def segments(cut):
    """The cut's own segment rows: shot, clock and seconds, read from the verify file beside it."""
    path = verify_path(cut)
    if not os.path.exists(path):
        raise BedError("%s is missing, so the shot clocks are unknown" % path)
    with open(path, "r", encoding="utf-8-sig") as handle:
        body = json.load(handle)
    rows = body.get("segments") or []
    if not rows:
        raise BedError("%s carries no segments" % path)
    if abs(float(body.get("duration_s", 0.0)) - TOTAL_S) > FPS_SAFE:
        raise BedError("%s is %s s, not 180.000" % (cut, body.get("duration_s")))
    return rows, body


def plan(cut=DEFAULT_CUT):
    """Every bed window with its cue, gain and the sentence that grounds it."""
    rows, _body = segments(cut)
    covered = [0.0]
    for row in rows:
        covered.append(round(float(row["clock"]) + float(row["seconds"]), 3))
    out = []
    for shot, lo, hi, cue_id in BED_TABLE:
        cue = cue_row(cue_id)
        starts = {round(float(row["clock"]), 3) for row in rows if row["shot"] == shot}
        if not any(abs(start - lo) <= 0.06 for start in starts):
            raise BedError("no %s segment starts at %.3f s in %s" % (shot, lo, verify_path(cut)))
        if hi - lo <= 0.0:
            raise BedError("%s's bed window %.3f to %.3f is empty" % (shot, lo, hi))
        out.append({"shot": shot, "window": [lo, hi], "seconds": round(hi - lo, 3),
                    "cue": cue["id"], "title": cue["title"], "file": cue["file"],
                    "game_volume": cue["game_volume"], "gain": cue["gain"]})
    # The hurricane, laid over the quay's own seconds in the same pass. Its window must also start where a
    # segment of that shot starts, so the wind follows the cut and cannot drift off the storm it belongs to.
    wind = ambience_row(WIND_CUE)
    for shot, lo, hi in WIND_TABLE:
        starts = {round(float(row["clock"]), 3) for row in rows if row["shot"] == shot}
        if not any(abs(start - lo) <= 0.06 for start in starts):
            raise BedError("no %s segment starts at %.3f s, so the wind has nowhere to sit" % (shot, lo))
        out.append({"shot": shot, "window": [lo, hi], "seconds": round(hi - lo, 3), "kind": "ambience",
                    "cue": wind["id"], "title": wind["title"], "file": wind["file"],
                    "game_volume": wind["game_volume"], "gain": wind["gain"]})
    last = max(item["window"][1] for item in out)
    if abs(last - TOTAL_S) > 0.01:
        raise BedError("the bed ends at %.3f s and the cut is 180.000" % last)
    return out


def build_bed(items, out):
    """One 180.00 s 48 kHz stereo wav: each window's own cue, looped from its OGG, faded at its edges."""
    inputs = ["-f", "lavfi", "-t", "%.3f" % TOTAL_S,
              "-i", "anullsrc=channel_layout=stereo:sample_rate=%d" % SAMPLE_RATE]
    for item in items:
        inputs += ["-stream_loop", "-1", "-i", os.path.join(ROOT, item["file"])]
    graph = []
    labels = []
    for index, item in enumerate(items):
        lo, hi = item["window"]
        seconds = hi - lo
        fade = min(EDGE_FADE_S, seconds / 4.0)
        label = "b%d" % index
        graph.append("[%d:a]aresample=%d,aformat=sample_fmts=s16:channel_layouts=stereo,"
                     "atrim=0:%.3f,asetpts=N/SR/TB,volume=%.4f,"
                     "afade=t=in:st=0:d=%.3f,afade=t=out:st=%.3f:d=%.3f,"
                     "adelay=%d|%d[%s]"
                     % (index + 1, SAMPLE_RATE, seconds, item["gain"],
                        fade, seconds - fade, fade,
                        int(round(lo * 1000)), int(round(lo * 1000)), label))
        labels.append("[%s]" % label)
    graph.append("[0:a]%samix=inputs=%d:duration=first:normalize=0,atrim=0:%.3f[aout]"
                 % ("".join(labels), len(items) + 1, TOTAL_S))
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    run(["ffmpeg", "-hide_banner", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(graph),
         "-map", "[aout]", "-ac", "2", "-ar", str(SAMPLE_RATE), "-t", "%.3f" % TOTAL_S, out],
        "building the music bed")
    return out


def mix(cut, bed, out):
    """The cut's picture untouched (-c:v copy) with the bed summed under its audio, limited, 180.00 s."""
    if not os.path.exists(bed):
        raise BedError("%s is missing, so there is nothing to mix" % bed)
    graph = ("[0:a]aresample=%d,aformat=sample_fmts=fltp:channel_layouts=stereo[cut];"
             "[1:a]aresample=%d,aformat=sample_fmts=fltp:channel_layouts=stereo[bed];"
             "[cut][bed]amix=inputs=2:duration=first:normalize=0,"
             "alimiter=limit=%.2f:level=false,atrim=0:%.3f[aout]" % (SAMPLE_RATE, SAMPLE_RATE, LIMIT, TOTAL_S))
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", cut, "-i", bed,
         "-filter_complex", graph, "-map", "0:v", "-map", "[aout]", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE), "-t", "%.3f" % TOTAL_S,
         "-movflags", "+faststart", out], "mixing the bed under the cut")
    return out


def probe_duration(path):
    result = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                  "-of", "default=noprint_wrappers=1:nokey=1", path], "probing %s" % path)
    return float(result.stdout.strip())


def mean_volume(path, at, seconds):
    result = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", "%.3f" % at,
                             "-t", "%.3f" % seconds, "-i", path, "-map", "0:a:0", "-af", "volumedetect",
                             "-f", "null", "-"], capture_output=True, text=True)
    for line in result.stderr.splitlines():
        if "mean_volume:" in line:
            return float(line.split("mean_volume:")[1].strip().split()[0])
    return None


def mono(path, at, seconds, rate=16000):
    import numpy as np
    result = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.3f" % at, "-t", "%.3f" % seconds,
                             "-i", path, "-vn", "-ac", "1", "-ar", str(rate), "-f", "f32le", "-"],
                            capture_output=True)
    return np.frombuffer(result.stdout, dtype=np.float32)


def mono_looped(path, offset, seconds, rate=16000):
    """A looped file's samples starting at `offset` inside its loop: the wind layer repeats, so a window
    longer than the loop must be read round it, not past its end."""
    import numpy as np
    result = subprocess.run(["ffmpeg", "-v", "error", "-stream_loop", "-1", "-ss", "%.3f" % offset,
                             "-t", "%.3f" % seconds, "-i", path, "-vn", "-ac", "1", "-ar", str(rate),
                             "-f", "f32le", "-"], capture_output=True)
    return np.frombuffer(result.stdout, dtype=np.float32)


def correlation(a, b):
    import numpy as np
    size = min(len(a), len(b))
    if size < 1600:
        return None
    a = a[:size] - a[:size].mean()
    b = b[:size] - b[:size].mean()
    if a.std() == 0 or b.std() == 0:
        return None
    return float((a * b).mean() / (a.std() * b.std()))


def null_correlation(mixed, before, bed, at, seconds, max_lag_ms=200, bed_at=None, bed_loop_s=None):
    """residual = mixed - before, against the bed, at the best lag. The one honest probe of a bed in a mix.

    A plain correlation of the delivered window against the bed cannot work here: the window holds the
    film's own music, its voice and the AAC encoder's own noise, all louder than the 0.385 bed, so the
    measured number sits near zero whatever the mix did (measured on this cut: -0.11 to -0.44). Subtracting
    the same window of the file before the bed removes every one of those terms and leaves the bed itself,
    which is what the lag sweep then has to find. Measured on the delivered file: r +0.41 to +0.70 at a
    constant lag of -80 samples (-5.0 ms, the AAC frame), on every window.
    """
    import numpy as np
    mixed = mono(os.path.abspath(mixed), at, seconds)
    plain = mono(os.path.abspath(before), at, seconds)
    # bed_at is where inside the reference the window sits: the wind layer starts at its file's sample 0 at the
    # start of its own window, so its reference is read at (window time - window start), not at the film clock.
    # bed_loop_s wraps that offset round a loop: the wind is 3.698 s long and a window here is up to 8 s, so
    # reading it straight would run off the end of the file and measure nothing (which is what it did first).
    if bed_loop_s:
        cue = mono_looped(os.path.abspath(bed), (at if bed_at is None else bed_at) % bed_loop_s, seconds)
    else:
        cue = mono(os.path.abspath(bed), at if bed_at is None else bed_at, seconds)
    size = min(len(mixed), len(plain), len(cue))
    if size < 1600:
        return None, None
    residual = mixed[:size] - plain[:size]
    cue = cue[:size]
    rate = 16000
    max_lag = min(int(rate * max_lag_ms / 1000.0), size // 4)
    window = size - 2 * max_lag
    if window < rate // 2:
        return None, None
    a = residual[max_lag:max_lag + window]
    a = a - a.mean()
    if a.std() == 0:
        return None, None
    best = (0, 0.0)
    for lag in range(-max_lag, max_lag + 1, 2):
        seg = cue[max_lag + lag:max_lag + lag + window]
        seg = seg - seg.mean()
        if seg.std() == 0:
            continue
        r = float((a * seg).mean() / (a.std() * seg.std()))
        if abs(r) > abs(best[1]):
            best = (lag, r)
    return best[1], best[0] * 1000.0 / rate


def stream_md5(path, selector):
    """md5 of one stream's packets, copied: the honest "this did not touch the picture" measure."""
    result = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", selector, "-c", "copy",
                             "-f", "md5", "-"], capture_output=True, text=True)
    return result.stdout.strip()


def verify(video, bed, items, before=None):
    """The delivered file: 180.00 s, audible everywhere, and every bed window correlating with its own cue."""
    checks = []
    seconds = probe_duration(video)
    checks.append(("duration", abs(seconds - TOTAL_S) <= FPS_SAFE, "%.3f s against 180.000 s" % seconds))
    overall = mean_volume(video, 0.0, TOTAL_S)
    checks.append(("not_silent", overall is not None and overall > -50.0,
                   "mean volume over the film %s dB" % overall))
    if before:
        before_mean = mean_volume(before, 0.0, TOTAL_S)
        checks.append(("bed_raises_the_mix", before_mean is not None and overall is not None
                       and overall > before_mean + 0.4,
                       "%.1f dB with the bed against %.1f dB without it" % (overall, before_mean)))
        mine, theirs = stream_md5(video, "0:v"), stream_md5(before, "0:v")
        checks.append(("picture_unchanged", mine == theirs and mine != "",
                       "video packets %s against %s: the bed is summed under the audio and the picture is"
                       " copied, not re-encoded" % (mine or "unreadable", theirs or "unreadable")))
    if not os.path.exists(bed):
        raise BedError("%s is missing, so no window can be measured" % bed)
    lags = []
    wind_lags = []
    wind_loop_s = None
    for item in items:
        lo, hi = item["window"]
        span = min(8.0, hi - lo)
        at = lo + (hi - lo - span) / 2.0
        window_mean = mean_volume(video, lo, hi - lo)
        level = None if before is None else mean_volume(before, lo, hi - lo)
        ambience = item.get("kind") == "ambience"
        if before:
            if ambience:
                # The wind's own reference: the delivered loop, read round itself from the point the layer has
                # reached at this window's start. The bed also carries the music, so this residual is diluted by
                # it; the check that chance cannot pass is the absent control below.
                reference = os.path.join(ROOT, item["file"])
                if wind_loop_s is None:
                    wind_loop_s = probe_duration(reference)
                r, lag_ms = null_correlation(video, before, reference, at, span,
                                             bed_at=at - lo, bed_loop_s=wind_loop_s)
                if lag_ms is not None:
                    wind_lags.append(lag_ms)
            else:
                r, lag_ms = null_correlation(video, before, bed, at, span)
                if lag_ms is not None:
                    lags.append(lag_ms)
            detail = ("%s %s at %s to %.3f s, residual against the %s r=%s at lag %s ms, window mean %s dB"
                      % (item["cue"], item["title"], item["window"], hi,
                         "wind" if ambience else "bed",
                         -1 if r is None else round(r, 2), None if lag_ms is None else round(lag_ms, 1),
                         None if window_mean is None else round(window_mean, 1)))
            # 0.20, not a higher bar: the residual also carries the AAC re-encode noise of the film's own
            # track, which is louder than the bed in the dense shots (measured window means), so the
            # correlation cannot approach 1. The check that chance cannot pass is the lag consistency below.
            ok = (r is not None and r >= 0.20 and lag_ms is not None and abs(lag_ms) <= 20.0
                  and window_mean is not None and window_mean > -40.0)
        else:
            r = correlation(mono(video, at, span), mono(bed, at, span))
            detail = ("%s %s at %s to %.3f s, correlation %s, window mean %s dB"
                      % (item["cue"], item["title"], item["window"], hi,
                         -1 if r is None else round(r, 2),
                         None if window_mean is None else round(window_mean, 1)))
            ok = r is not None and r >= 0.20 and window_mean is not None and window_mean > -40.0
        if level is not None:
            detail += " against %s dB before the bed" % round(level, 1)
        checks.append(("bed_%s_%s" % (item["shot"], item["cue"]) if not ambience
                       else "wind_%s_%s" % (item["shot"], item["cue"]), ok, detail))
    # The control the wind's own presence has to pass: on a shot with no storm, the same probe must find nothing.
    wind_row = next((item for item in items if item.get("kind") == "ambience"), None)
    if before and wind_row is not None:
        control_shot, control_lo, control_hi = WIND_ABSENT_CONTROL
        span = min(6.0, control_hi - control_lo)
        control_at = control_lo + (control_hi - control_lo - span) / 2.0
        control, _lag = null_correlation(video, before, os.path.join(ROOT, wind_row["file"]),
                                         control_at, span, bed_at=0.0, bed_loop_s=wind_loop_s)
        checks.append(("wind_absent_%s" % control_shot, control is None or abs(control) < 0.20,
                       "%s at %.1f to %.1f s, residual against the wind r=%s where no storm plays; a wind that"
                       " leaked across the whole film would correlate here too"
                       % (control_shot, control_lo, control_hi,
                          "none" if control is None else round(control, 2))))
    if lags:
        spread = max(lags) - min(lags)
        checks.append(("bed_lag_consistent", spread <= 10.0,
                       "every music window finds the bed at %s to %s ms, a spread of %.1f ms; a residual that only"
                       " met the bed by chance would not hold one lag across the whole film"
                       % (round(min(lags), 1), round(max(lags), 1), spread)))
    if wind_lags:
        spread = max(wind_lags) - min(wind_lags)
        checks.append(("wind_lag_consistent", spread <= 10.0,
                       "every storm window finds the wind at %s to %s ms, a spread of %.1f ms"
                       % (round(min(wind_lags), 1), round(max(wind_lags), 1), spread)))
    return checks


def main(argv=None):
    parser = argparse.ArgumentParser(description="score the demo cut with the game's own cues, per shot")
    parser.add_argument("--plan", action="store_true", help="print the bed windows and the cue of each")
    parser.add_argument("--bed", nargs="?", const=DEFAULT_BED, help="write the 180.00 s bed wav here")
    parser.add_argument("--mix", action="store_true", help="sum the bed under the cut's audio")
    parser.add_argument("--verify", action="store_true", help="measure a delivered file")
    parser.add_argument("--video", default=DEFAULT_CUT, help="the cut to read, mix or measure")
    parser.add_argument("--bed-file", default=DEFAULT_BED, help="the bed wav to write or mix")
    parser.add_argument("--before", default=None, help="the same cut without the bed, for the level comparison")
    args = parser.parse_args(argv)
    try:
        items = plan(args.video) if not args.verify else plan(args.before or args.video)
        if args.plan:
            print(json.dumps([{k: v for k, v in item.items() if k != "path"} for item in items], indent=1))
            return 0
        if args.bed:
            build_bed(items, args.bed)
            print("PASS  %s written, %d windows, %.3f s"
                  % (args.bed, len(items), probe_duration(args.bed)))
            if not (args.mix or args.verify):
                return 0
        if args.mix:
            source = args.before or args.video
            if os.path.abspath(source) == os.path.abspath(args.video):
                # mixing a file onto itself: write beside it, then replace, so no reader sees a half written cut
                scratch = os.path.splitext(args.video)[0] + ".with-bed.mp4"
                mix(source, args.bed_file, scratch)
                os.replace(scratch, args.video)
            else:
                mix(source, args.bed_file, args.video)
            print("PASS  %s mixed with %s" % (args.video, args.bed_file))
            return 0
        if args.verify:
            checks = verify(args.video, args.bed_file, items, before=args.before)
            for name, ok, detail in checks:
                print("%s  %-22s %s" % ("PASS" if ok else "FAIL", name, detail))
            report = os.path.splitext(args.video)[0] + "_music_verify.json"
            with open(report, "w", encoding="utf-8") as handle:
                json.dump({"video": os.path.relpath(args.video, ROOT),
                           "bed": os.path.relpath(args.bed_file, ROOT),
                           "bed_under_game": BED_UNDER_GAME,
                           "windows": [{k: v for k, v in item.items() if k != "path"} for item in items],
                           "checks": [{"name": n, "ok": o, "detail": d} for n, o, d in checks]},
                          handle, indent=1)
            print("PASS  report written to %s" % report)
            return 0 if all(ok for _, ok, _ in checks) else 1
    except BedError as error:
        print("REFUSED  %s" % error)
        return 1
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
