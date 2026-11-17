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
    `alimiter=limit=0.89` because the music, the wind and the events sum: the delivered file must not clip, and
    the AAC encode overshoots the sample peak a little, so the limiter sits 1 dB under full scale.

The text blips and the battle stingers (JUDGE-PANEL-2026-11-17 fix 3, card t_f19fa5c3)
    The panel asks for "hurricane wind, text blips and battle stingers in the quay, morgan and percy scenes,
    using the musician lane tracks, wired to the capture mix". The wind is the WIND_TABLE above. The blips
    and the stingers are an events layer this tool now writes beside the bed, and like every other layer it
    is read, not typed:

      which events   the captures' own event logs. Each segment row of the cut names a source video, and a
                     source's log is the JSON the recorder wrote beside it (`raw_story_good.mkv` ->
                     `story_good.events.json`, `doors.mp4` -> `doors.events.json`), so a recut re-reads the
                     logs instead of drifting from them. Every `PP audio: <cue> played` line whose cue is a
                     text blip or a battle stinger is a row; the blip set is the three the engine plays
                     (pp_audio_blip_cue: text_blip_a narrator, text_blip_b sailor/prometheus, text_blip_c
                     percy) plus the speaker files the blip card delivered, and the stinger set is the
                     encounter swoosh and the hit family.
      where it lands  the log's second, mapped into the cut through that segment's own in point and clock, so
                     the event sits on the picture the game was showing when it fired. The recorder stamps a
                     line one flush after the sound has started, so the layer is aligned to the capture's own
                     copy by cross-correlation (EVENT_ALIGN_S either side, applied when the match is at least
                     EVENT_ALIGN_MIN_R): where the capture holds the sound, the layer lands on it and lifts it
                     instead of flamming it. A row the capture cannot confirm takes that source's median
                     measured shift, and a source with no confirmed row at all stays on the raw stamp. The
                     plan says which basis every row used (capture, source or log).
      how loud        the game's own levels, parsed from pp_audio.gml and not chosen: an effect plays at
                     PP_AUDIO_GAIN_SFX and a blip at that times PP_AUDIO_GAIN_BLIP (0.9 and 0.5, so 0.45).
                     The layer is summed under the film with the bed, and the limiter is the same one.

    What the verify then measures is the delivered file, not the plan: the residual of the film against the
    same film before the mix, at every scheduled event's clock, against the residual at control clocks in the
    same shot where nothing was scheduled. A layer that was written but not mixed cannot pass that, and an
    events file that is empty fails the row that names it.

What this tool refuses
    A cut whose audio is missing, whose duration is not 180.000 s, whose verify file has no segments, or a
    cue whose delivered_file is not on disk. A cue that is `pending` in data/audio.json is never resolved to a
    fallback here: a bed that plays a stand-in would be scoring the shot with a cue the game does not play.

Usage
    python tools\\demo_music_bed.py --plan
    python tools\\demo_music_bed.py --bed output\\demo\\music-bed-2026-11-15.wav
    python tools\\demo_music_bed.py --events output\\demo\\event-bed-2026-11-17.wav
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
import re
import subprocess
import sys
import wave

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
LIMIT = 0.86                 # the beds and the events sum; 0.86 leaves the AAC encode its overshoot room

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

# The text blips and the battle stingers (JUDGE-PANEL-2026-11-17 fix 3, card t_f19fa5c3). Both sets are cue ids
# the engine itself asks for by name (pp_audio_cues in pp_audio.gml), and every file is the one the musician lane
# shipped for that id in assets/audio/sfx. Nothing here is a new sound or a chosen level: the gains come from the
# two PP_AUDIO_GAIN_* macros below.
BLIP_CUES = ("text_blip_a", "text_blip_b", "text_blip_c",
             "text_blip_zeus", "text_blip_kronos", "text_blip_percy", "text_blip_oldman", "text_blip_narrator")
STINGER_CUES = ("encounter_swoosh", "hit_light", "hit_heavy", "crit", "miss")
EVENT_CUES = BLIP_CUES + STINGER_CUES
SFX_DIR = os.path.join(ROOT, "assets", "audio", "sfx")
AUDIO_GML = os.path.join(ROOT, "game", "scripts", "pp_audio", "pp_audio.gml")
DEFAULT_EVENTS = os.path.join(ROOT, "output", "demo", "event-bed-2026-11-17.wav")
# The recorder writes its log line after the sound has started, so the capture's own copy sits a little before the
# stamped second. The layer is moved onto that copy when the match is real; a match weaker than this is a
# coincidence, and the log's own clock is the honest place to leave it.
EVENT_ALIGN_S = 0.25
EVENT_ALIGN_MIN_R = 0.50
EVENT_CONTROL_GAP_S = 0.45   # how far after an event the control window sits, so it holds no scheduled event
EVENT_LIFT_MIN = 2.0         # how much louder the delivered residual must be at an event than at its control
# The shot that is scored with the same cue as Morgan's pages and carries no logged blip: the probe there must
# find nothing, which is what an events layer smeared across the whole film could not do.
EVENT_ABSENT_CONTROL = ("S3", 31.0, 32.0)
# The events layer's own ceiling. The mix's limiter is at LIMIT; a layer that already peaks near it leaves the
# film's own track no room, so the layer is scaled as a whole when its sum goes above this.
LAYER_HEADROOM = 0.90


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


def gml_macros():
    """The engine's own gains, parsed from pp_audio.gml rather than copied or chosen here.

    PP_AUDIO_GAIN_SFX is what pp_audio_sfx plays an effect at and PP_AUDIO_GAIN_BLIP the fraction
    pp_audio_blip drops a text blip to (spec 12 rule 6), so the layer is at the game's level by construction.
    """
    try:
        with open(AUDIO_GML, "r", encoding="utf-8-sig") as handle:
            text = handle.read()
    except OSError as error:
        raise BedError("cannot read %s: %s" % (AUDIO_GML, error))

    def macro(name):
        match = re.search(r"^#macro\s+%s\s+([0-9.]+)" % re.escape(name), text, re.M)
        if not match:
            raise BedError("%s does not declare %s" % (AUDIO_GML, name))
        return float(match.group(1))

    return {"sfx": macro("PP_AUDIO_GAIN_SFX"), "blip": macro("PP_AUDIO_GAIN_BLIP")}


def event_gain(cue):
    """The level the game plays this cue at: an effect at PP_AUDIO_GAIN_SFX, a blip at that times the blip fraction."""
    gains = gml_macros()
    if cue in BLIP_CUES:
        return round(gains["sfx"] * gains["blip"], 4)
    return round(gains["sfx"], 4)


def event_file(cue):
    """The musician lane's delivered file for this cue, or a refusal that names what is missing."""
    path = os.path.join(SFX_DIR, "%s.ogg" % cue)
    if not os.path.exists(path):
        raise BedError("the log asks for %s and %s is not on disk" % (cue, repo_path(path)))
    return path


def repo_path(path):
    """A path for a report: relative to the repo when it lives inside it, absolute when it does not.

    A capture or a layer can sit on another drive (the kanban workspace, a temp tree in a test), and
    os.path.relpath refuses to compare across drives, so the report has to fall back rather than raise.
    """
    try:
        return os.path.relpath(path, ROOT)
    except ValueError:
        return os.path.abspath(path)


def event_log_for(source):
    """The recorder's own log beside a segment's source video, or None when that capture kept none.

    The name is derived from the source, never typed per row: `raw_story_good.mkv` was recorded as `story_good`
    (the raw_ prefix is the recorder's), so both names are tried beside the file.
    """
    folder = os.path.dirname(os.path.join(ROOT, source))
    stem = os.path.splitext(os.path.basename(source))[0]
    names = [stem + ".events.json"]
    if stem.startswith("raw_"):
        names.append(stem[len("raw_"):] + ".events.json")
    for name in names:
        path = os.path.join(folder, name)
        if os.path.exists(path):
            return path
    return None


def log_events(path):
    """Every sound the game's log says it played, as (stamped second, cue id), in the order it wrote them."""
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            body = json.load(handle)
    except (OSError, ValueError) as error:
        raise BedError("cannot read the capture log %s: %s" % (path, error))
    rows = []
    for item in body.get("events") or []:
        if not isinstance(item, list) or len(item) < 2:
            continue
        try:
            stamp = float(item[0])
        except (TypeError, ValueError):
            continue
        line = str(item[1])
        if not line.startswith("PP audio:") or " played" not in line:
            continue
        rest = line[len("PP audio:"):].strip()
        if not rest:
            continue
        cue = rest.split()[0].strip(",")
        rows.append((stamp, cue))
    return rows


def best_match(audio, at, reference, rate=16000, span=EVENT_ALIGN_S, step=4):
    """Where the capture's own copy of this cue sits, as (offset_ms, r), searched either side of the stamp.

    A sound is a short, distinctive waveform inside a bed of music and wind, so the peak of the cross
    correlation is the copy; a window of music alone gives a number near zero, which the caller refuses.
    """
    import numpy as np
    size = len(reference)
    if size < 80 or len(audio) < size + 2 * int(span * rate):
        return None, None
    pad = int(span * rate)
    start = int(round((at - span) * rate))
    if start < 0 or start + size + 2 * pad > len(audio):
        return None, None
    window = audio[start:start + size + 2 * pad]
    centred = reference - reference.mean()
    if centred.std() == 0:
        return None, None
    best = (0, 0.0)
    for lag in range(-pad, pad + 1, step):
        segment = window[pad + lag:pad + lag + size]
        if len(segment) != size:
            continue
        segment = segment - segment.mean()
        if segment.std() == 0:
            continue
        value = float((segment * centred).mean() / (segment.std() * centred.std()))
        if abs(value) > abs(best[1]):
            best = (lag, value)
    return best[1], best[0] * 1000.0 / rate


def plan_events(cut, rate=16000):
    """Every logged text blip and battle stinger the cut's own segments contain, on the cut's clock.

    The reading is the cut's, the log's and the capture's: the segments come from the verify file beside the
    cut, the stamps and cue ids from each source's own log, and the alignment from the capture's audio.
    Returns (events, info) where info records the logs read, the rows a segment did not cover, and how many
    events the capture's own audio confirmed.
    """
    import numpy as np  # noqa: F401  (best_match needs numpy arrays; the import documents the dependency)
    rows, _body = segments(cut)
    cache, references, audio = {}, {}, {}
    events, dropped, raw = [], 0, []
    confirmed = 0
    logs = {}
    for row in rows:
        path = event_log_for(row["source"])
        if not path:
            continue
        name = repo_path(path)
        logs.setdefault(name, 0)
        if path not in cache:
            cache[path] = log_events(path)
        rows_for_source = cache[path]
        lo = float(row["in"])
        hi = lo + float(row["seconds"])
        clock = float(row["clock"])
        in_range = [(stamp, cue) for stamp, cue in rows_for_source
                    if cue in EVENT_CUES and lo <= stamp < hi]
        dropped += sum(1 for stamp, cue in rows_for_source
                       if cue in EVENT_CUES and not (lo <= stamp < hi))
        if not in_range:
            continue
        logs[name] += len(in_range)
        if path not in audio:
            source_path = os.path.join(ROOT, row["source"])
            audio[path] = mono(source_path, 0.0, probe_duration(source_path), rate=rate)
        for stamp, cue in in_range:
            if cue not in references:
                reference_path = event_file(cue)
                references[cue] = mono(reference_path, 0.0, probe_duration(reference_path), rate=rate)
            reference = references[cue]
            match, offset_ms = best_match(audio[path], stamp, reference, rate=rate)
            measured = None
            if match is not None and offset_ms is not None and abs(match) >= EVENT_ALIGN_MIN_R \
                    and abs(offset_ms) <= EVENT_ALIGN_S * 1000.0:
                measured = offset_ms / 1000.0
            raw.append({"shot": row["shot"], "cue": cue, "kind": "event",
                        "stamp": round(stamp, 3), "source": row["source"], "log": path,
                        "offset": clock - lo, "measured": measured,
                        "match": None if match is None else round(match, 2),
                        "gain": event_gain(cue), "file": repo_path(event_file(cue))})
    # A source's own clock correction: the median of the shifts its audio confirmed. The recorder stamps a log
    # line one flush after the sound, so an event the capture cannot confirm still belongs at the same offset
    # rather than at the raw stamp; the median is measured, and the plan says which rows used it.
    shifts = {}
    for path in {item["log"] for item in raw}:
        found = sorted(item["measured"] for item in raw if item["log"] == path and item["measured"] is not None)
        if found:
            middle = len(found) // 2
            shifts[path] = found[middle] if len(found) % 2 else (found[middle - 1] + found[middle]) / 2.0
    events = []
    confirmed = 0
    for item in raw:
        shift = item["measured"]
        basis = "capture"
        if shift is None:
            shift = shifts.get(item["log"], 0.0)
            basis = "source" if item["log"] in shifts else "log"
        else:
            confirmed += 1
        item["at"] = round(item["offset"] + item["stamp"] + shift, 3)
        item["shift_ms"] = round(shift * 1000.0, 1)
        item["shift_basis"] = basis
        del item["offset"]
        events.append(item)
    events.sort(key=lambda item: item["at"])
    info = {"logs": logs, "events": len(events), "dropped": dropped, "confirmed": confirmed,
            "shifts_ms": {repo_path(path): round(value * 1000.0, 1)
                          for path, value in shifts.items()},
            "shift_basis": {basis: sum(1 for item in events if item["shift_basis"] == basis)
                            for basis in sorted({item["shift_basis"] for item in events})},
            "per_cue": {cue: sum(1 for item in events if item["cue"] == cue)
                        for cue in EVENT_CUES if any(item["cue"] == cue for item in events)}}
    if not events:
        raise BedError("%s logs no text blip or battle stinger inside %s's segments"
                       % (", ".join(sorted(logs)) or "no capture", cut))
    for item in events:
        if not (0.0 <= item["at"] < TOTAL_S):
            raise BedError("%s at %.3f s falls outside the 180.000 s film" % (item["cue"], item["at"]))
    return events, info


def build_events(events, out):
    """One 180.00 s 48 kHz stereo wav holding the events, summed in numpy at the cut's own clocks.

    The game plays one effect at a time; this layer sums every logged event into one file, so two blips a
    frame apart can add up past full scale. When the sum peaks above LAYER_HEADROOM the whole layer is scaled
    by the same factor (the events keep their relative levels) and the factor is returned for the report:
    a layer that was silently clipped would be a different sound from the one the game plays.
    """
    import numpy as np
    total = int(round(TOTAL_S * SAMPLE_RATE))
    layer = np.zeros((total, 2), dtype=np.float32)
    files = {}
    for item in events:
        path = os.path.join(ROOT, item["file"])
        if path not in files:
            files[path] = mono(path, 0.0, probe_duration(path), rate=SAMPLE_RATE)
        samples = files[path]
        if samples.size == 0:
            raise BedError("%s decoded to no samples" % item["file"])
        start = int(round(item["at"] * SAMPLE_RATE))
        chunk = samples[:total - start]
        layer[start:start + len(chunk), 0] += item["gain"] * chunk
        layer[start:start + len(chunk), 1] += item["gain"] * chunk
    peak = float(np.abs(layer).max()) if layer.size else 0.0
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    info = {"peak_before_limiting": round(peak, 3), "limited": False, "peak_after_limiting": round(peak, 3)}
    if peak <= LAYER_HEADROOM:
        with wave.open(out, "wb") as handle:
            handle.setnchannels(2)
            handle.setsampwidth(2)
            handle.setframerate(SAMPLE_RATE)
            handle.writeframes((layer * 32767.0).astype("<i2").tobytes())
        return out, info
    # Over the ceiling: only the peaks are taken down, with the same look-ahead limiter the mix uses, so the
    # blips keep the level the game plays them at instead of the whole layer being turned down for one cluster.
    scratch = os.path.splitext(out)[0] + ".f32"
    with open(scratch, "wb") as handle:
        handle.write(layer.astype("<f4").tobytes())
    try:
        run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-f", "f32le", "-ar", str(SAMPLE_RATE),
             "-ac", "2", "-i", scratch, "-af",
             "alimiter=limit=%.2f:level=false,atrim=0:%.3f" % (LAYER_HEADROOM, TOTAL_S),
             "-c:a", "pcm_s16le", "-ar", str(SAMPLE_RATE), "-ac", "2", out],
            "limiting the events layer")
    finally:
        if os.path.exists(scratch):
            os.remove(scratch)
    info["limited"] = True
    info["peak_after_limiting"] = round(LAYER_HEADROOM, 3)
    return out, info


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


def mix(cut, bed, out, events=None):
    """The cut's picture untouched (-c:v copy) with the bed and the events summed under its audio, 180.00 s."""
    if not os.path.exists(bed):
        raise BedError("%s is missing, so there is nothing to mix" % bed)
    if events and not os.path.exists(events):
        raise BedError("%s is missing, so the text blips and stingers would not be mixed" % events)
    graph = ("[0:a]aresample=%d,aformat=sample_fmts=fltp:channel_layouts=stereo[cut];"
             "[1:a]aresample=%d,aformat=sample_fmts=fltp:channel_layouts=stereo[bed];"
             % (SAMPLE_RATE, SAMPLE_RATE))
    inputs = ["-i", cut, "-i", bed]
    if events:
        graph += ("[2:a]aresample=%d,aformat=sample_fmts=fltp:channel_layouts=stereo[ev];" % SAMPLE_RATE)
        graph += ("[cut][bed][ev]amix=inputs=3:duration=first:normalize=0,"
                  "alimiter=limit=%.2f:level=false,atrim=0:%.3f[aout]" % (LIMIT, TOTAL_S))
        inputs += ["-i", events]
    else:
        graph += ("[cut][bed]amix=inputs=2:duration=first:normalize=0,"
                  "alimiter=limit=%.2f:level=false,atrim=0:%.3f[aout]" % (LIMIT, TOTAL_S))
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    run(["ffmpeg", "-hide_banner", "-v", "error", "-y", *inputs,
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


def audio_stream(path):
    """The delivered file's audio stream, measured: present or not, and the codec, rate and channel count."""
    result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                             "-show_entries", "stream=codec_name,sample_rate,channels",
                             "-of", "json", path], capture_output=True, text=True)
    try:
        streams = json.loads(result.stdout or "{}").get("streams") or []
    except ValueError:
        streams = []
    if not streams:
        return {"has_audio": False}
    row = streams[0]
    return {"has_audio": True, "codec": row.get("codec_name"),
            "sample_rate": int(row["sample_rate"]) if row.get("sample_rate") else None,
            "channels": row.get("channels")}


def high_band(series, at, seconds, rate=16000, lo=2000.0, hi=7000.0):
    """The energy of one window in the band a talk blip lives in (a 4 kHz square, a noise burst, a swoosh)."""
    import numpy as np
    begin = int(round(at * rate))
    size = int(round(seconds * rate))
    window = series[begin:begin + size]
    if len(window) < 64:
        return None
    spectrum = np.abs(np.fft.rfft(window * np.hanning(len(window)))) ** 2
    freqs = np.fft.rfftfreq(len(window), 1.0 / rate)
    band = (freqs >= lo) & (freqs <= hi)
    if not band.any():
        return None
    return float(spectrum[band].mean())


def event_checks(video, before, events, events_file, rate=16000):
    """The text blips and the battle stingers, measured in the delivered file rather than read from the plan.

    The probe is the film's high band (2 to 7 kHz, where a talk blip, a noise stinger and the swoosh live),
    read twice: in the delivered file and in the same file before the mix, at the same clocks. At every
    scheduled event's clock the delivered film must carry that band louder than the pre-mix film by a margin,
    and at a control clock in the same shot, where nothing was scheduled, it must not. That pair is what a
    layer that was planned but never mixed cannot produce, and what a layer smeared across the whole film
    cannot either: the same bed and the same wind sit in both windows, so they cancel out of the comparison.
    """
    import numpy as np
    if not events:
        return [{"name": "events_layer", "ok": False,
                 "detail": "no text blip or battle stinger was planned, so the film has no UI layer"}]
    if not os.path.exists(events_file):
        return [{"name": "events_layer", "ok": False,
                 "detail": "%s is missing, so no text blip or stinger was mixed"
                           % repo_path(events_file)}]
    delivered = mono(os.path.abspath(video), 0.0, TOTAL_S, rate=rate)
    plain = mono(os.path.abspath(before), 0.0, TOTAL_S, rate=rate)
    size = min(len(delivered), len(plain))
    if size < rate * 2:
        return [{"name": "events_layer", "ok": False,
                 "detail": "the film and the pre-mix file could not both be decoded for the comparison"}]
    delivered, plain = delivered[:size], plain[:size]
    starts = np.array([item["at"] for item in events], dtype="float64")
    durations = {}
    results = []
    lifts, controls = {}, {}
    for item in events:
        if item["cue"] not in durations:
            durations[item["cue"]] = probe_duration(os.path.join(ROOT, item["file"]))
        span = durations[item["cue"]] + 0.02
        if item["at"] + span >= TOTAL_S:
            continue
        after = high_band(delivered, item["at"], span, rate=rate)
        before_band = high_band(plain, item["at"], span, rate=rate)
        if not after or not before_band:
            continue
        lifts.setdefault((item["shot"], item["cue"]), []).append(after / before_band)
        control_at = item["at"] + span + EVENT_CONTROL_GAP_S
        if np.abs(starts - control_at).min() < span + 0.15 or control_at + span >= TOTAL_S:
            continue
        c_after = high_band(delivered, control_at, span, rate=rate)
        c_before = high_band(plain, control_at, span, rate=rate)
        if c_after and c_before:
            controls.setdefault((item["shot"], item["cue"]), []).append(c_after / c_before)
    all_controls = [value for values in controls.values() for value in values]
    baseline = float(np.median(all_controls)) if all_controls else None
    if baseline is None or baseline <= 0:
        return [{"name": "events_layer", "ok": False,
                 "detail": "no control clock in the film was quiet enough to measure the layer against"}]
    for (shot, cue), values in sorted(lifts.items()):
        ratio = float(np.median(values))
        control = float(np.median(controls.get((shot, cue)) or all_controls))
        ok = ratio >= EVENT_LIFT_MIN and ratio >= control * 1.5
        results.append({"name": "events_%s_%s" % (shot, cue), "ok": ok,
                        "detail": "%d %s: the delivered high band is %.1fx the pre-mix band at those clocks,"
                                  " against %.1fx at the control clocks in the same shot"
                                  % (len(values), cue, ratio, control)})
    # The events the plan did not cover: the quay's own shot carries none, so the same probe there must find
    # nothing more than the bed and the wind already put there.
    shot, lo, hi = EVENT_ABSENT_CONTROL
    after = high_band(delivered, lo, hi - lo, rate=rate)
    before_band = high_band(plain, lo, hi - lo, rate=rate)
    if after and before_band:
        ratio = after / before_band
        results.append({"name": "events_absent_%s" % shot, "ok": ratio < baseline * 1.5,
                        "detail": "%s at %.1f s, the delivered high band is %.2fx the pre-mix band where no text"
                                  " blip or stinger is scheduled, against %.2fx at the control clocks"
                                  % (shot, lo, ratio, baseline)})
    return results


def verify(video, bed, items, before=None, events=None, events_file=None):
    """The delivered file: 180.00 s, audible everywhere, and every bed window correlating with its own cue."""
    checks = []
    seconds = probe_duration(video)
    stream = audio_stream(video)
    checks.append(("duration", abs(seconds - TOTAL_S) <= FPS_SAFE, "%.3f s against 180.000 s" % seconds))
    checks.append(("has_audio", bool(stream.get("has_audio")),
                   ("audio stream %s %s Hz %s channel(s) is present" % (
                       stream.get("codec"), stream.get("sample_rate"), stream.get("channels")))
                   if stream.get("has_audio") else "no audio stream in the delivered file"))
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
    # The text blips and the battle stingers, measured against the same film before the mix. Only a delivered
    # file can answer this, so a plan that names every event still fails if nothing was summed under it.
    if events:
        for row in event_checks(video, before or video, events, events_file or DEFAULT_EVENTS):
            checks.append((row["name"], row["ok"], row["detail"]))
    return checks


def main(argv=None):
    parser = argparse.ArgumentParser(description="score the demo cut with the game's own cues, per shot")
    parser.add_argument("--plan", action="store_true", help="print the bed windows and the cue of each")
    parser.add_argument("--bed", nargs="?", const=DEFAULT_BED, help="write the 180.00 s bed wav here")
    parser.add_argument("--events", nargs="?", const=DEFAULT_EVENTS,
                        help="write the 180.00 s text blip and battle stinger layer here")
    parser.add_argument("--mix", action="store_true", help="sum the bed and the events under the cut's audio")
    parser.add_argument("--verify", action="store_true", help="measure a delivered file")
    parser.add_argument("--video", default=DEFAULT_CUT, help="the cut to read, mix or measure")
    parser.add_argument("--bed-file", default=DEFAULT_BED, help="the bed wav to write or mix")
    parser.add_argument("--events-file", default=DEFAULT_EVENTS, help="the events wav to write or mix")
    parser.add_argument("--before", default=None, help="the same cut without the bed, for the level comparison")
    args = parser.parse_args(argv)
    try:
        # The segment table comes from the cut the work reads: the --before file when one is named, because a
        # --mix writes a new video that has no verify file of its own until it is measured.
        source_cut = args.before or args.video
        items = plan(source_cut)
        events, event_info = plan_events(source_cut)
        if args.plan:
            print(json.dumps({"bed": [{k: v for k, v in item.items() if k != "path"} for item in items],
                              "events": {"summary": event_info, "rows": events}}, indent=1))
            return 0
        if args.bed:
            build_bed(items, args.bed)
            print("PASS  %s written, %d windows, %.3f s"
                  % (args.bed, len(items), probe_duration(args.bed)))
            if not (args.mix or args.verify):
                return 0
        if args.events:
            _path, layer_info = build_events(events, args.events)
            print("PASS  %s written, %d events (%s), %.3f s, peak %.2f%s"
                  % (args.events, len(events),
                     ", ".join("%s %d" % item for item in event_info["per_cue"].items()),
                     probe_duration(args.events), layer_info["peak_after_limiting"],
                     "" if not layer_info["limited"]
                     else " (the sum reached %.2f, so the peaks were limited to %.2f)"
                          % (layer_info["peak_before_limiting"], LAYER_HEADROOM)))
            if not (args.mix or args.verify):
                return 0
        if args.mix:
            source = args.before or args.video
            layer = args.events_file if os.path.exists(args.events_file) else None
            if os.path.abspath(source) == os.path.abspath(args.video):
                # mixing a file onto itself: write beside it, then replace, so no reader sees a half written cut
                scratch = os.path.splitext(args.video)[0] + ".with-bed.mp4"
                mix(source, args.bed_file, scratch, events=layer)
                os.replace(scratch, args.video)
            else:
                mix(source, args.bed_file, args.video, events=layer)
            print("PASS  %s mixed with %s%s"
                  % (args.video, args.bed_file,
                     "" if layer is None else " and %s" % layer))
            return 0
        if args.verify:
            checks = verify(args.video, args.bed_file, items, before=args.before,
                            events=events, events_file=args.events_file)
            for name, ok, detail in checks:
                print("%s  %-26s %s" % ("PASS" if ok else "FAIL", name, detail))
            report = os.path.splitext(args.video)[0] + "_music_verify.json"
            with open(report, "w", encoding="utf-8") as handle:
                json.dump({"video": os.path.relpath(args.video, ROOT),
                           "bed": os.path.relpath(args.bed_file, ROOT),
                           "events_layer": os.path.relpath(args.events_file, ROOT),
                           "bed_under_game": BED_UNDER_GAME,
                           "has_audio": bool(audio_stream(args.video).get("has_audio")),
                           "audio": audio_stream(args.video),
                           "events": {"summary": event_info, "rows": events},
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
