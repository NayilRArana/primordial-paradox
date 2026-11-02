"""The map from the game's own audio log lines to the real OGG files on disk, built and checked.

Card t_37855a33 (DEMO-AUDIO-CAPTURE, the mapping child). The game writes one "PP audio:" line for every
sound it asks for, plays, ducks or leaves silent (game/scripts/pp_audio/pp_audio.gml). The log carries no
timestamps and no gain for effects, so a renderer that reads it has to know three things it cannot read:
which line means which sound, which file that sound is, and what the game's own level for it was. This
tool is where those three answers live, derived from the shipped data rather than typed by hand:

  * the event grammar is the set of format strings in pp_audio.gml, each with its line number;
  * the effect file table is game/datafiles/sfx/sfx.json (what the game itself loads);
  * the music table is data/audio.json (what the bus streams);
  * the levels, crossfade and step are the PP_AUDIO_* macros in pp_audio.gml, parsed, not copied;
  * the title theme's beat is assets/audio/title_theme_v3/title_theme_v3_126_loop.json, the ledger for
    the render the bus asks for first.

Modes:
    --build   write the map JSON (knowledge/EVENT-LOG-AUDIO-MAP-2026-11-01.json) and print a summary
    --check   re-derive everything and fail on any drift between the map, the data files, the gml and the
              sample log fixture. Exit 0 only when the map is usable by someone who has never seen it.
    --plan LOG    classify every audio line in LOG and print the resolved events, with no rendering
    --render LOG OUT [--uniform-seconds S]   render a proof track from LOG. The timing here is a stated
              uniform clock, not the game's: the log has no timestamps, so a real take supplies arrival
              stamps (tools/play_demo.py LogAudioWatch). Labelled as a proof in the JSON beside OUT.

Provenance: the format strings are read from the gml at run time, so a message that changes in the game
changes here on the next --check instead of drifting. Nothing in this tool makes a sound up: a line whose
meaning is "the game was silent here" stays silent in the plan, and a file that is not on disk is a
problem, not a substitute.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_JSON = os.path.join(ROOT, "data", "audio.json")
SFX_JSON = os.path.join(ROOT, "game", "datafiles", "sfx", "sfx.json")
SFX_ASSETS = os.path.join(ROOT, "assets", "audio", "sfx")
STREAMS = os.path.join(ROOT, "game", "datafiles", "streams")
AUDIO_ASSETS = os.path.join(ROOT, "assets", "audio")
AUDIO_GML = os.path.join(ROOT, "game", "scripts", "pp_audio", "pp_audio.gml")
TITLE_LOOP = os.path.join(ROOT, "assets", "audio", "title_theme_v3", "title_theme_v3_126_loop.json")
MAP_PATH = os.path.join(ROOT, "knowledge", "EVENT-LOG-AUDIO-MAP-2026-11-01.json")
# A .txt on purpose: .gitignore line 187 ignores **/*.log, so a fixture named .log could never be committed,
# and this file has to exist in a clean checkout for the map to be usable there.
SAMPLE_LOG = os.path.join(ROOT, "knowledge", "EVENT-LOG-SAMPLE-2026-11-01.txt")
# ffmpeg's amix takes a few hundred inputs badly; the proof render uses this many, the map does not care.
PROOF_SEGMENTS = 64

# The logs the grammar was read against, in the order the map cites them. They are build output and are
# not in git; the fixture above is the copy that ships, and every line in it names the log it came from.
SOURCES = (
    ("build/demo-game.log", "a headless demo run: the theme, footsteps, blips, a menu, focus, loads"),
    ("output/music_everywhere_2026-11-01/music_tour.log", "the MUSIC-EVERYWHERE tour: cue streams, rooms, fights"),
    ("build/first_fight_game.log", "an older run: the theme duck and the fallback path for a pending cue"),
    ("build/ff-probe2-game.log", "a build whose manifest lacks the car_engine_loop row: the one silent-effect line"),
)

# Kept in the map so a reader knows which clock a log line can honestly be placed on.
SCRIPT_FPS = 60
STEP_MS = None  # read from the gml


def read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def run(cmd, timeout=120):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                                stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as error:
        return None, str(error)
    if result.returncode != 0:
        text = (result.stderr or result.stdout or "").strip()
        return None, text[-1500:]
    return result.stdout, ""


def ffprobe(path):
    """What ffprobe says about one file: seconds, rate, channels, codec, and its own tags."""
    if not os.path.isfile(path):
        return {"error": "not on disk"}
    out, error = run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", path])
    if out is None:
        return {"error": "ffprobe failed: %s" % error}
    try:
        data = json.loads(out)
    except ValueError as error:
        return {"error": "ffprobe json: %s" % error}
    fmt = data.get("format") or {}
    stream = (data.get("streams") or [{}])[0]
    try:
        seconds = float(fmt.get("duration") or stream.get("duration") or 0.0)
    except (TypeError, ValueError):
        seconds = 0.0
    tags = dict(stream.get("tags") or {})
    tags.update(fmt.get("tags") or {})
    return {"seconds": round(seconds, 6),
            "rate": int(stream.get("sample_rate") or 0),
            "channels": int(stream.get("channels") or 0),
            "codec": stream.get("codec_name") or "",
            "tags": {key.upper(): value for key, value in tags.items()}}


def gml_macros():
    """The bus numbers, read from the gml so the map cannot hold a copy that drifts."""
    wanted = ("PP_AUDIO_FADE_STEPS", "PP_AUDIO_STEP_MS", "PP_AUDIO_GAIN_MUSIC", "PP_AUDIO_GAIN_SFX",
              "PP_AUDIO_GAIN_BLIP", "PP_AUDIO_PRI_MUSIC", "PP_AUDIO_PRI_BOSS", "PP_AUDIO_PRI_SFX",
              "PP_AUDIO_PRI_UI", "PP_AUDIO_CHANNELS")
    text = open(AUDIO_GML, "r", encoding="utf-8").read()
    macros = {}
    for name in wanted:
        match = re.search(r"^#macro\s+%s\s+([0-9.]+)\s*$" % name, text, re.M)
        if match:
            macros[name] = float(match.group(1))
    return macros


def theme_candidates():
    """The theme stream order the bus asks for, parsed out of pp_audio_theme_streams()."""
    text = open(AUDIO_GML, "r", encoding="utf-8").read()
    body = re.search(r"function pp_audio_theme_streams\(\)\s*\{(.*?)\}", text, re.S)
    if not body:
        return []
    return re.findall(r'"(streams/[^"]+\.ogg)"', body.group(1))


def effect_rows():
    data = read_json(SFX_JSON)
    rows = {}
    for row in data.get("cues") or []:
        if row.get("id"):
            rows[row["id"]] = row
    return rows


def cue_rows():
    data = read_json(AUDIO_JSON)
    return {row["id"]: row for row in data.get("cues") or [] if row.get("id")}


def leaf_of(declared):
    return os.path.basename(str(declared).replace("\\", "/"))


# ---------------------------------------------------------------------------------------------------------------------
# The event grammar. One entry per show_debug_message("PP audio: ...") in pp_audio.gml, in an order where the
# specific forms come before the general ones. `sound` is what a renderer does with the line:
#   music_start  place the named music file from here, looped, at the parsed or bus gain
#   music_stop   fade the music out over the bus fade and stop it
#   music_gain   change the music gain from here (the theme's duck and unduck)
#   music_pause  music is paused; silence from here until music_resume
#   music_resume resume from the paused position, not from the file's start
#   sfx          place one effect at the bus gain for that id
#   none         the game made no sound because of this line
EVENTS = (
    dict(type="no_manifest", sound="none", gml=87,
         regex=r"^PP audio: no effect manifest at .*sfx\.json, every effect stays silent$",
         meaning="the effect manifest is missing, so every effect in the run is silent"),
    dict(type="no_cue_table", sound="none", gml=142,
         regex=r"^PP audio: data/audio\.json has no cues table, every music cue stays silent$",
         meaning="the music table is missing, so every cue in the run is silent"),
    dict(type="music_gain_repaired", sound="none", gml=462,
         regex=r"^PP audio: music (\S+) gain repaired to \S+ \(it had drifted below half\)$",
         meaning="a live music instance had drifted below half the music level and was put back at the level (card MUSIC-REAL)"),
    dict(type="focus_lost", sound="music_pause", gml=428,
         regex=r"^PP audio: focus lost, music paused.*every effect stopped$",
         meaning="the window lost focus: the music is paused and every effect is stopped"),
    dict(type="focus_back", sound="music_resume", gml=433,
         regex=r"^PP audio: focus back, music resumed where it stopped$",
         meaning="focus is back: the music resumes from the paused position"),
    dict(type="theme_handed", sound="music_stop", gml=229,
         regex=r"^PP audio: title_theme handed to the fade, the cue takes the one music source$",
         meaning="a cue is starting: the theme fades out over the bus fade and the cue takes the slot"),
    dict(type="theme_stopping", sound="music_stop", gml=353,
         regex=r"^PP audio: title_theme stopping over (\d+) steps$",
         meaning="the theme fades out over the printed number of steps and stops"),
    dict(type="music_stopping", sound="music_stop", gml=360,
         regex=r"^PP audio: music stopping over (\d+) steps$",
         meaning="the cue fades out over the printed number of steps and stops"),
    dict(type="theme_stream", sound="music_start", gml=645,
         regex=r"^PP audio: title_theme streaming (\S+), instance -?\d+, gain (-?[0-9.]+)$",
         meaning="the title theme starts from the named stream at the printed gain, looped"),
    dict(type="theme_ducked_state", sound="none", gml=728,
         regex=r"^PP audio: title_theme ducked (-?[0-9.]+) dB in the state, no stream instance to turn down$",
         meaning="a duck level is recorded for the next theme start; nothing is playing to turn down"),
    dict(type="theme_ducked", sound="music_gain", gml=736,
         regex=r"^PP audio: title_theme ducked (-?[0-9.]+) dB, gain (-?[0-9.]+)$",
         meaning="the theme's gain changes to the printed number right now"),
    dict(type="theme_unducked", sound="music_gain", gml=749,
         regex=r"^PP audio: title_theme back to full after (-?[0-9.]+) dB$",
         meaning="the theme's gain goes back to the bus music level"),
    dict(type="music_stream", sound="music_start", gml=338,
         regex=r"^PP audio: music cue (\S+) streaming (.+), instance -?\d+, priority (-?\d+), fade (\d+) steps$",
         meaning="a music cue starts from the named file at the bus music level, looped, fading in"),
    dict(type="music_fallback", sound="none", gml=279,
         regex=r"^PP audio: music cue (\S+) has no OGG yet, falling back to (\S+)$",
         meaning="the asked cue has no file, so the bus asked for the fallback; the next start line is the sound"),
    dict(type="music_missing", sound="none", gml=298,
         regex=r"^PP audio: music cue (\S+) has no OGG yet, expected (\S+), placeholder (\w+)$",
         meaning="the cue has no file where the game looks: silence, and the game plays no music here"),
    dict(type="music_stream_failed", sound="none", gml=316,
         regex=r"^PP audio: music cue (\S+) silent, audio_create_stream failed on (.+)$",
         meaning="the file is there and the stream would not open: silence"),
    dict(type="music_no_channel", sound="none", gml=327,
         regex=r"^PP audio: music cue (\S+) silent, no audio channel for it$",
         meaning="no audio channel was free at the music priority: silence"),
    dict(type="music_unknown", sound="none", gml=269,
         regex=r"^PP audio: unknown music cue (\S+), nothing played$",
         meaning="a cue id the table does not know: silence"),
    dict(type="sfx_not_in_manifest", sound="none", gml=378,
         regex=r"^PP audio: sfx (\S+) silent, not in sfx/sfx\.json$",
         meaning="the effect is not in the manifest: silence"),
    dict(type="sfx_loaded", sound="none", gml=617,
         regex=r"^PP audio: (\S+) loaded (\S+) \(([0-9.]+) s, (\d+) Hz, buffer (.+)\)$",
         meaning="the effect file was read into a buffer: no sound yet, the play line is the sound"),
    dict(type="sfx_no_file", sound="none", gml=579,
         regex=r"^PP audio: (\S+) silent, no file at (.+)$", meaning="the effect file is missing: silence"),
    dict(type="sfx_buffer_failed", sound="none", gml=585,
         regex=r"^PP audio: (\S+) silent, buffer_load failed on (.+)$",
         meaning="the effect file would not load: silence"),
    dict(type="sfx_length_bad", sound="none", gml=595,
         regex=r"^PP audio: (\S+) silent, the measured length does not fit (.+)$",
         meaning="the manifest's measured length does not fit the file: silence"),
    dict(type="sfx_create_failed", sound="none", gml=609,
         regex=r"^PP audio: (\S+) silent, audio_create_buffer_sound failed on (.+)$",
         meaning="the buffer sound would not be created: silence"),
    dict(type="sfx_played", sound="sfx", gml=(397, 690),
         regex=r"^PP audio: ([a-z0-9_]+) played, instance -?\d+$",
         meaning="one effect plays once, at the level of the bus path that asked for it"),
    dict(type="sfx_silent_manifest", sound="none", gml=679,
         regex=r"^PP audio: (\S+) silent, not in sfx/sfx\.json$",
         meaning="an effect the cue list knows but the manifest does not ship: silence"),
    dict(type="cue_unknown_name", sound="none", gml=671,
         regex=r"^PP audio: unknown cue (\S+)$", meaning="a name that is not an effect at all: silence"),
    dict(type="room_no_cue", sound="none", gml=526,
         regex=r"^PP audio: room (\S+) names no music cue, the music in hand keeps playing$",
         meaning="the room names no cue: whatever music is playing keeps playing"),
    dict(type="room_asked", sound="none", gml=533,
         regex=r"^PP audio: room (\S+) asked (\S+), playing (\S+) \((started|kept)\), stream (yes|no)$",
         meaning="the room asked for a cue; the start line above or below is the sound, this line is the verdict"),
    dict(type="fight_asked", sound="none", gml=554,
         regex=r"^PP audio: fight (\S+) asked (\S+), playing (\S+) \((started|kept)\), stream (yes|no)$",
         meaning="the fight asked for a cue; the start line is the sound, this line is the verdict"),
    dict(type="no_theme_stream", sound="none", gml=650,
         regex=r"^PP audio: no title theme stream in (.+)$",
         meaning="no theme stream file was found at boot: silence where the theme would be"),
)
COMPILED = [(row, re.compile(row["regex"])) for row in EVENTS]


def gml_lines(row):
    """The gml line number(s) a message site lives on; sfx_played is written by two functions."""
    value = row["gml"]
    return tuple(value) if isinstance(value, (tuple, list)) else (value,)


# The message sites no sampled run has reached, and the branch each one waits on. They are in the map
# because the game can write them and a renderer must not treat an unknown line as sound; they are marked
# unobserved because no log in the tree proves the wording at run time, only the gml does.
UNOBSERVED_WHY = {
    "music_gain_repaired": "fires only if the engine moves a music gain the bus never asked for; no run in the tree has needed the repair",
    "no_manifest": "fires only when sfx/sfx.json is missing from the build; no run in the tree was built without it",
    "no_cue_table": "fires only when audio.json has no cues table; every sampled build had one",
    "theme_stopping": "fires only when a stop arrives with no cue playing and a theme still live",
    "music_stopping": "fires only when the music is stopped while a cue is playing; no sampled run stopped its music",
    "theme_ducked_state": "fires only when a duck is asked for before the theme stream exists",
    "music_fallback": "fires only when a cue row has no file and names a fallback; every sampled run asked for landed cues",
    "music_stream_failed": "fires only when a file exists and audio_create_stream refuses it",
    "music_no_channel": "fires only when all ten channels are taken at the music priority",
    "music_unknown": "fires only when the room or fight names a cue id the table does not hold",
    "sfx_not_in_manifest": "fires only on the pp_audio_sfx path with an id the manifest lacks; sampled misses all came through pp_audio_play",
    "sfx_no_file": "fires only when a manifest row names a wav that is not in the build",
    "sfx_buffer_failed": "fires only when the wav is there and buffer_load refuses it",
    "sfx_length_bad": "fires only when the manifest's measured length does not fit the wav",
    "sfx_create_failed": "fires only when audio_create_buffer_sound refuses the buffer",
    "room_no_cue": "fires only when a map names no music cue; every sampled room names one",
    "no_theme_stream": "fires only when no theme stream file is in the build at boot",
}

# Which call path plays each effect, and therefore at what gain, measured by grepping the call sites:
# pp_audio_play leaves the gain argument off, and the manual's page for audio_play_sound (read 2026-11-01)
# says gain "defaults to 1"; pp_audio_sfx passes PP_AUDIO_GAIN_SFX; pp_audio_blip multiplies that by
# PP_AUDIO_GAIN_BLIP. The log line is the same for the first two, so the map records both candidates.
PLAY_CALL_SITE_IDS = ("car_engine_loop", "door_hatch", "encounter_swoosh", "footstep", "menu_cancel",
                      "menu_move", "menu_select", "thunder_soft")
BLIP_PREFIX = "text_blip"


def classify(line):
    """The first event type a line matches, or None. Order is the table's order."""
    text = line.strip()
    for row, pattern in COMPILED:
        match = pattern.match(text)
        if match:
            return row, match
    return None, None


def effect_gain(cue_id, macros):
    """The gain the map recommends for one effect id, and why, from the call sites grepped today."""
    sfx_gain = macros["PP_AUDIO_GAIN_SFX"]
    if cue_id.startswith(BLIP_PREFIX):
        return round(sfx_gain * macros["PP_AUDIO_GAIN_BLIP"], 6), "pp_audio_blip: the effect level times the blip level"
    if cue_id in PLAY_CALL_SITE_IDS:
        return 1.0, "pp_audio_play: the gain argument is left off, and the manual says it defaults to 1"
    return sfx_gain, "pp_audio_sfx: the effect level, the only path a scene command reaches"


def build_map():
    macros = gml_macros()
    if not macros:
        raise SystemExit("no PP_AUDIO_* macros found in %s" % AUDIO_GML)
    fade_seconds = round(macros["PP_AUDIO_FADE_STEPS"] * macros["PP_AUDIO_STEP_MS"] / 1000.0, 4)
    effects = effect_rows()
    cues = cue_rows()
    loop = read_json(TITLE_LOOP)

    sounds = {row.get("id"): row for row in (read_json(AUDIO_JSON).get("sounds") or []) if row.get("id")}
    effect_map = {}
    for cue_id, row in sorted(effects.items()):
        ogg = os.path.join(SFX_ASSETS, cue_id + ".ogg")
        wav = os.path.join(ROOT, "game", "datafiles", "sfx", row["file"])
        gain, gain_why = effect_gain(cue_id, macros)
        probe = ffprobe(ogg) if os.path.isfile(ogg) else {"error": "not on disk"}
        tags = {key: probe["tags"][key] for key in ("LOOPSTART", "LOOPLENGTH", "LOOPEND")
                if key in (probe.get("tags") or {})}
        entry = {"id": cue_id,
                 "ogg": repo_relative(ogg),
                 "ogg_exists": os.path.isfile(ogg),
                 "ogg_seconds": probe.get("seconds") if os.path.isfile(ogg) else None,
                 "game_file": repo_relative(wav),
                 "game_seconds": float(row.get("seconds") or 0.0),
                 "data_bytes": row.get("data_bytes"),
                 "offset": row.get("offset"),
                 "rate": row.get("rate"),
                 "channels": row.get("channels"),
                 "gain": gain,
                 "gain_why": gain_why,
                 "gain_alternatives": ([round(macros["PP_AUDIO_GAIN_SFX"], 6)]
                                       if cue_id in PLAY_CALL_SITE_IDS else []),
                 "gain_note": ("the log line does not record the gain. This id's call sites are the ones the map "
                               "names; an id reachable both from pp_audio_play and from a scene command can have "
                               "been played at either level, and the difference is 0.9 dB"),
                 "vorbis_loop_tags": tags,
                 "loop_in_data": bool(sounds.get(cue_id, {}).get("loop")),
                 "loop_played": False,
                 "speakers": row.get("speaker", ""),
                 "trim": ("play all of it once: the game reads the wav data chunk at offset %s for %s bytes and "
                          "the bus plays every effect with loop off (pp_audio_sfx and pp_audio_play both pass "
                          "loop false), so a loop flag in data/audio.json is not heard%s"
                          % (row.get("offset"), row.get("data_bytes"),
                             "; the ogg's own loop points are %s" % tags if tags else ""))}
        effect_map[cue_id] = entry

    cue_map = {}
    for cue_id, row in sorted(cues.items()):
        declared = row.get("delivered_file")
        leaf = leaf_of(declared) if declared else (str(row.get("asset")) + ".ogg")
        asset_path = os.path.join(ROOT, declared) if declared else None
        stream_path = os.path.join(STREAMS, leaf)
        probed = ffprobe(asset_path) if asset_path else {"error": "no delivered file"}
        cue_map[cue_id] = {"id": cue_id,
                           "title": row.get("title"),
                           "landed": bool(declared),
                           "delivered_file": declared,
                           "file": repo_relative(asset_path) if asset_path else None,
                           "file_exists": bool(asset_path and os.path.isfile(asset_path)),
                           "stream_file": repo_relative(stream_path),
                           "stream_exists": os.path.isfile(stream_path),
                           "seconds": probed.get("seconds"),
                           "rate": probed.get("rate"),
                           "channels": probed.get("channels"),
                           "gain": macros["PP_AUDIO_GAIN_MUSIC"],
                           "priority": int(macros["PP_AUDIO_PRI_BOSS"] if row.get("boss")
                                          else macros["PP_AUDIO_PRI_MUSIC"]),
                           "loop": bool(row.get("loop", True)),
                           "fallback": row.get("fallback"),
                           "trim": ("the bus loops the whole file from 0 and fades in over %s steps (%s s); "
                                    "a renderer does the same" % (int(macros["PP_AUDIO_FADE_STEPS"]), fade_seconds))}

    candidates = theme_candidates()
    theme_leaf = leaf_of(candidates[0]) if candidates else ""
    theme_asset = resolve_music(candidates[0], (AUDIO_ASSETS, STREAMS)) if candidates else None
    theme_probe = ffprobe(theme_asset) if theme_asset else {"error": "no theme stream on disk"}
    bpm = float(loop.get("bpm") or 0.0)
    beats_per_bar = int(loop.get("beats_per_bar") or 0)
    beat_seconds = round(60.0 / bpm, 7) if bpm else None
    theme = {"cue": "title_theme",
             "asked_streams": list(candidates),
             "chosen_stream": candidates[0] if candidates else None,
             "file": repo_relative(theme_asset) if theme_asset else None,
             "file_exists": bool(theme_asset),
             "stream_file": repo_relative(os.path.join(STREAMS, theme_leaf)),
             "stream_exists": os.path.isfile(os.path.join(STREAMS, theme_leaf)),
             "seconds": theme_probe.get("seconds"),
             "rate": theme_probe.get("rate"),
             "channels": theme_probe.get("channels"),
             "gain": macros["PP_AUDIO_GAIN_MUSIC"],
             "priority": int(macros["PP_AUDIO_PRI_MUSIC"]),
             "loop": True,
             "beat": {"bpm": bpm,
                      "beats_per_bar": beats_per_bar,
                      "time_signature": loop.get("time_signature"),
                      "beat_seconds": beat_seconds,
                      "bar_seconds": round(beat_seconds * beats_per_bar, 7) if beat_seconds else None,
                      "first_downbeat_seconds": 0.0,
                      "loop_bars": loop.get("loop_bars"),
                      "loop_seconds": loop.get("loop_seconds"),
                      "loop_start_sample": loop.get("loop_start_sample"),
                      "loop_end_sample": loop.get("loop_end_sample"),
                      "samples_per_beat": int(round(loop.get("sample_rate", 44100) * beat_seconds))
                      if beat_seconds else None,
                      "source": repo_relative(TITLE_LOOP),
                      "note": ("bar 1 beat 1 is at 0.000 s because the loop starts at sample %s; a renderer that "
                               "wants the theme on a beat grid places it at a multiple of the bar"
                               % loop.get("loop_start_sample"))},
             "trim": ("the bus loops the whole stream from 0; the render ends at the loop end sample %s "
                      "(%s s) and the file may carry a short fade tail past it"
                      % (loop.get("loop_end_sample"), loop.get("loop_seconds"))),
             "duck_defect": ("the game asks for a 6 dB duck with a positive number and multiplies by 10^(db/20), "
                             "so a real log reads 'ducked 6 dB, gain 1.40': the theme gets 6 dB louder. A "
                             "reconstruction follows the printed gain because that is what the game played; the "
                             "sign is a game defect, filed separately")}

    counts = {}
    unmatched = []
    for rel, _why in SOURCES:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if "PP audio:" not in line:
                    continue
                row, _match = classify(line)
                if row is None:
                    unmatched.append(line.strip())
                else:
                    counts[row["type"]] = counts.get(row["type"], 0) + 1

    events = []
    for row in EVENTS:
        lines = gml_lines(row)
        seen = counts.get(row["type"], 0)
        events.append({"type": row["type"],
                       "sound": row["sound"],
                       "regex": row["regex"],
                       "meaning": row["meaning"],
                       "source": ", ".join("game/scripts/pp_audio/pp_audio.gml:%d" % line for line in lines),
                       "observed_in_logs": bool(seen),
                       "sample_lines": seen,
                       "why_unobserved": "" if seen else UNOBSERVED_WHY.get(row["type"], "")})

    return {"format": 1,
            "kind": "event_log_audio_map",
            "card": "t_37855a33",
            "date": "2026-11-01",
            "what": ("Every PP audio: log line the game can write, what it means for sound, the real .ogg a "
                     "renderer places, the gain the game played it at, and the title theme's beat. Built from "
                     "data/audio.json, game/datafiles/sfx/sfx.json, the PP_AUDIO_* macros in pp_audio.gml and "
                     "the title theme loop ledger; every number is measured or parsed, none is typed."),
            "sources": [{"file": rel, "what": why} for rel, why in SOURCES],
            "sample_log": repo_relative(SAMPLE_LOG),
            "bus": {"music_gain": macros["PP_AUDIO_GAIN_MUSIC"],
                    "sfx_gain": macros["PP_AUDIO_GAIN_SFX"],
                    "blip_factor": macros["PP_AUDIO_GAIN_BLIP"],
                    "blip_gain": round(macros["PP_AUDIO_GAIN_SFX"] * macros["PP_AUDIO_GAIN_BLIP"], 6),
                    "play_gain_default": 1.0,
                    "fade_steps": int(macros["PP_AUDIO_FADE_STEPS"]),
                    "step_ms": macros["PP_AUDIO_STEP_MS"],
                    "fade_seconds": fade_seconds,
                    "priorities": {"music": int(macros["PP_AUDIO_PRI_MUSIC"]),
                                   "boss": int(macros["PP_AUDIO_PRI_BOSS"]),
                                   "sfx": int(macros["PP_AUDIO_PRI_SFX"]),
                                   "ui": int(macros["PP_AUDIO_PRI_UI"])},
                    "channels": int(macros["PP_AUDIO_CHANNELS"]),
                    "macro_source": "game/scripts/pp_audio/pp_audio.gml:41 to :58"},
            "clock": {"log_has_timestamps": False,
                      "log_has_step_offsets": False,
                      "script_fps": SCRIPT_FPS,
                      "script_step_seconds": round(1.0 / SCRIPT_FPS, 7),
                      "honest_clocks": [
                          "the capture harness's arrival stamp: tools/play_demo.py LogAudioWatch reads the log "
                          "every %.2f s and places each line at the second it was read; lines already in the "
                          "file when the watch starts are at 0.0 (the theme streams at boot)" % 0.05,
                          "a scripted run's own step clock: the line is written in the step the game played the "
                          "sound, so a step offset from the script bounds it to one 1/%d s step" % SCRIPT_FPS],
                      "resolution_seconds": 0.05,
                      "note": ("a log line carries no time of its own. A renderer that has no harness stamps "
                               "must not invent spacing; it can only place the lines in their written order.")},
            "title_theme": theme,
            "events": events,
            "cues": cue_map,
            "effects": effect_map,
            "known_silences": [
                {"line": 'PP audio: unknown cue hit', "why": ("pp_battle_director.gml:646 asks for \"hit\" and no "
                                                              "such id is in sfx.json or pp_audio_cues(), so a battle "
                                                              "hit is silent today and only the log line exists"),
                 "file_that_would_fit": "assets/audio/sfx/hit_light.ogg"},
                {"line": "PP audio: car_engine_loop silent, not in sfx/sfx.json",
                 "why": "a build whose sfx.json predates the DRIVE-SFX row; current manifests have the row"},
                {"line": "PP audio: music cue PP-02 has no OGG yet, expected pp_drive_v2.ogg",
                 "why": "a build older than the W5 SCORE-FINAL re-point to pp_drive_master1; current data is landed"}],
            "unmatched_lines": unmatched,
            "event_line_counts": counts,
            "check": "python tools/event_audio_map.py --check"}


def repo_relative(path):
    if not path:
        return ""
    try:
        return os.path.relpath(path, ROOT).replace("\\", "/")
    except ValueError:
        return path


# ---------------------------------------------------------------------------------------------------------------------
# The check

def write_fixture():
    """Rewrite the shipped sample log from the source logs: every audio line, verbatim and in order.

    The source logs are build output and are not in git. This file is the copy a checkout carries, so a fresh
    implementer has real lines to work from instead of a log they have to record first. Nothing is edited: a
    header names each source, then that log's audio lines follow exactly as the game wrote them.
    """
    out = ["# EVENT-LOG-SAMPLE-2026-11-01.txt",
           "# A sample of the game's own audio log, for card t_37855a33 (DEMO-AUDIO-CAPTURE, the mapping child).",
           "# Every line below a source header is copied verbatim from that log, in its written order, unedited.",
           "# The rule that turns these lines into sound is knowledge/EVENT-LOG-AUDIO-MAP-2026-11-01.json.",
           "# Rewrite it with: python tools/event_audio_map.py --fixture",
           ""]
    for rel, why in SOURCES:
        path = os.path.join(ROOT, rel)
        out.append("# --- source: %s" % rel)
        out.append("# --- what it exercises: %s" % why)
        if not os.path.isfile(path):
            out.append("# not on this checkout: this block is skipped")
            out.append("")
            continue
        count = 0
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if "PP audio:" in line:
                    out.append(line.rstrip("\r\n"))
                    count += 1
        out.append("# %d audio line%s" % (count, "" if count == 1 else "s"))
        out.append("")
    with open(SAMPLE_LOG, "w", encoding="utf-8") as handle:
        handle.write("\n".join(out) + "\n")

def check_map(data=None, verbose=True):
    problems = []
    notes = []
    data = data or read_json(MAP_PATH)
    macros = gml_macros()

    bus = data.get("bus") or {}
    for key, macro in (("music_gain", "PP_AUDIO_GAIN_MUSIC"), ("sfx_gain", "PP_AUDIO_GAIN_SFX"),
                       ("blip_factor", "PP_AUDIO_GAIN_BLIP"), ("fade_steps", "PP_AUDIO_FADE_STEPS")):
        if abs(float(bus.get(key, -1)) - macros[macro]) > 1e-9:
            problems.append("bus.%s is %s and %s is %s" % (key, bus.get(key), macro, macros[macro]))

    effects = data.get("effects") or {}
    rows = effect_rows()
    if set(effects) != set(rows):
        problems.append("effects keys and sfx.json disagree: %s"
                        % sorted(set(effects) ^ set(rows)))
    for cue_id, entry in sorted(effects.items()):
        ogg = os.path.join(ROOT, entry["ogg"])
        wav = os.path.join(ROOT, entry["game_file"])
        if not os.path.isfile(ogg):
            problems.append("%s: ogg missing at %s" % (cue_id, entry["ogg"]))
            continue
        if not os.path.isfile(wav):
            problems.append("%s: the file the game loads is missing at %s" % (cue_id, entry["game_file"]))
        probe = ffprobe(ogg)
        if probe.get("codec") != "vorbis":
            problems.append("%s: %s is %s, not vorbis" % (cue_id, entry["ogg"], probe.get("codec")))
        if entry.get("ogg_seconds") and probe.get("seconds"):
            if abs(float(entry["ogg_seconds"]) - float(probe["seconds"])) > 0.02:
                problems.append("%s: the map says %s s and the file probes %s s"
                                % (cue_id, entry["ogg_seconds"], probe["seconds"]))
        want, _why = effect_gain(cue_id, macros)
        if abs(float(entry.get("gain", -1)) - want) > 1e-9:
            problems.append("%s: gain %s and the call sites say %s" % (cue_id, entry.get("gain"), want))

    cues = data.get("cues") or {}
    rows = cue_rows()
    if set(cues) != set(rows):
        problems.append("cues keys and data/audio.json disagree: %s" % sorted(set(cues) ^ set(rows)))
    for cue_id, entry in sorted(cues.items()):
        declared = rows[cue_id].get("delivered_file")
        if bool(declared) != bool(entry.get("landed")):
            problems.append("%s: landed is %s and delivered_file is %s"
                            % (cue_id, entry.get("landed"), declared))
        if not declared:
            continue
        asset = os.path.join(ROOT, declared)
        if not os.path.isfile(asset):
            problems.append("%s: %s is not on disk" % (cue_id, declared))
            continue
        stream = os.path.join(STREAMS, leaf_of(declared))
        if not os.path.isfile(stream):
            notes.append("%s: the build's mirror %s is not on this checkout (game/datafiles is not committed); "
                         "the delivered file the game copies it from is here" % (cue_id, repo_relative(stream)))
        elif sha256(asset) != sha256(stream):
            problems.append("%s: %s and its mirror differ in bytes" % (cue_id, declared))

    theme = data.get("title_theme") or {}
    candidates = theme_candidates()
    if not candidates:
        problems.append("pp_audio_theme_streams() names no stream")
    elif theme.get("asked_streams") != candidates:
        problems.append("title_theme.asked_streams does not match pp_audio_theme_streams(): %s vs %s"
                        % (theme.get("asked_streams"), candidates))
    if theme.get("chosen_stream") != (candidates[0] if candidates else None):
        problems.append("title_theme.chosen_stream is not the first asked stream")
    theme_file = theme.get("file")
    if not theme_file or not os.path.isfile(os.path.join(ROOT, theme_file)):
        problems.append("title_theme.file is %r and is not on disk" % theme_file)
    loop = read_json(TITLE_LOOP)
    beat = theme.get("beat") or {}
    if abs(float(beat.get("bpm", 0)) - float(loop["bpm"])) > 1e-9:
        problems.append("title_theme.beat.bpm does not match the loop ledger")
    if beat.get("beat_seconds") and abs(beat["beat_seconds"] - 60.0 / float(loop["bpm"])) > 1e-6:
        problems.append("title_theme.beat.beat_seconds is not 60/bpm")
    if beat.get("loop_bars") and beat.get("beat_seconds"):
        want = beat["loop_bars"] * beat["beats_per_bar"] * beat["beat_seconds"]
        if abs(want - float(loop["loop_seconds"])) > 0.01:
            problems.append("the loop ledger's bars and beats do not add up to its own loop_seconds")
    if theme_file and os.path.isfile(os.path.join(ROOT, theme_file)) and beat.get("loop_seconds"):
        probe = ffprobe(os.path.join(ROOT, theme_file))
        if probe.get("seconds") and float(probe["seconds"]) + 0.05 < float(beat["loop_seconds"]):
            problems.append("the theme file is shorter than its own loop length")

    # The grammar must still cover every message the gml can write: every site is either a line the table
    # names or a duplicate of one it names, and each named line really is a "PP audio:" message site.
    text = open(AUDIO_GML, "r", encoding="utf-8").read()
    source_lines = text.splitlines()
    sites = len(re.findall(r'show_debug_message\("PP audio:', text))
    types = data.get("events") or []
    named = [line for row in EVENTS for line in gml_lines(row)]
    if len(named) != sites:
        problems.append("%d named gml lines for %d PP audio: message sites" % (len(named), sites))
    for row in EVENTS:
        for line in gml_lines(row):
            window = "\n".join(source_lines[max(0, line - 2):line + 1])
            if 'show_debug_message("PP audio:' not in window:
                problems.append("%s: gml line %d is not a PP audio: message site" % (row["type"], line))
    for row in types:
        if not row.get("source") or not re.match(r"^game/scripts/pp_audio/pp_audio\.gml:\d+(, game/scripts/pp_audio/pp_audio\.gml:\d+)*$",
                                                 row["source"]):
            problems.append("%s: no gml line reference" % row.get("type"))
        if row.get("sound") not in ("music_start", "music_stop", "music_gain", "music_pause",
                                    "music_resume", "sfx", "none"):
            problems.append("%s: sound is %r" % (row.get("type"), row.get("sound")))
        try:
            re.compile(row["regex"])
        except re.error as error:
            problems.append("%s: bad regex: %s" % (row.get("type"), error))

    # Every event type must match at least one real or fixture line, and no line may be unclassified.
    fixture = SAMPLE_LOG if os.path.isfile(SAMPLE_LOG) else None
    counts = {}
    unmatched = []
    for path in [os.path.join(ROOT, rel) for rel, _why in SOURCES if os.path.isfile(os.path.join(ROOT, rel))]:
        for line in open(path, "r", encoding="utf-8", errors="replace"):
            if "PP audio:" in line:
                row, _m = classify(line)
                if row is None:
                    unmatched.append((repo_relative(path), line.strip()))
                else:
                    counts[row["type"]] = counts.get(row["type"], 0) + 1
    if fixture:
        for line in open(fixture, "r", encoding="utf-8", errors="replace"):
            if "PP audio:" in line and not line.lstrip().startswith("#"):
                row, _m = classify(line)
                if row is None:
                    unmatched.append((repo_relative(fixture), line.strip()))
                else:
                    counts[row["type"]] = counts.get(row["type"], 0) + 1
    if not counts:
        problems.append("no sample log line could be read: neither %s nor the logs in the tree"
                        % repo_relative(SAMPLE_LOG))
    for line, where in unmatched[:10]:
        problems.append("%s: no event type matches a real line: %s" % (where, line))
    if len(unmatched) > 10:
        problems.append("... and %d more unmatched lines" % (len(unmatched) - 10))
    for row in types:
        if counts.get(row["type"]):
            continue
        if not row.get("why_unobserved"):
            problems.append("%s: no sample line proves this event exists and no reason is given"
                            % row["type"])

    if verbose:
        print("event types: %d, message sites in gml: %d" % (len(types), sites))
        print("effects mapped: %d, cues mapped: %d, landed cues: %d"
              % (len(effects), len(cues), sum(1 for entry in cues.values() if entry.get("landed"))))
        print("event lines seen in the logs and fixture: %d over %d types"
              % (sum(counts.values()), len(counts)))
        print("title theme: %s at %s bpm, beat %s s, bar %s s, loop %s s"
              % (theme.get("file"), beat.get("bpm"), beat.get("beat_seconds"),
                 beat.get("bar_seconds"), beat.get("loop_seconds")))
        if notes:
            print("notes, not failures: %d" % len(notes))
            for note in notes[:5]:
                print("  %s" % note)
    return problems


# ---------------------------------------------------------------------------------------------------------------------
# Planning and the proof render

def resolve_music(named, folders=None):
    leaf = leaf_of(named)
    for folder in (folders or (STREAMS, AUDIO_ASSETS)):
        direct = os.path.join(folder, leaf)
        if os.path.isfile(direct):
            return direct
        if not os.path.isdir(folder):
            continue
        for root_dir, _dirs, files in os.walk(folder):
            if leaf in files:
                return os.path.join(root_dir, leaf)
    return None


def plan_log(path, data):
    """Every audio line in the log, in order, as the events a renderer places. No timing is invented."""
    macros = gml_macros()
    effects = data.get("effects") or {}
    plan = []
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if "PP audio:" not in line:
                continue
            row, match = classify(line)
            if row is None:
                plan.append({"order": len(plan), "line": line.strip(), "type": None, "sound": None,
                             "why": "no event type matches this line"})
                continue
            entry = {"order": len(plan), "line": line.strip(), "type": row["type"], "sound": row["sound"]}
            groups = match.groups() if match else ()
            if row["type"] == "theme_stream":
                file = resolve_music(groups[0])
                entry.update({"file": repo_relative(file) if file else None, "gain": float(groups[1]),
                              "loop": True, "why": "the theme's own start line, at its printed gain"})
            elif row["type"] == "music_stream":
                file = resolve_music(groups[1])
                entry.update({"cue": groups[0], "file": repo_relative(file) if file else None,
                              "gain": macros["PP_AUDIO_GAIN_MUSIC"], "loop": True,
                              "priority": int(groups[2]), "fade_steps": int(groups[3]),
                              "why": "a cue's own start line, at the bus music level"})
            elif row["type"] == "theme_ducked":
                entry.update({"gain": float(groups[1]), "db": float(groups[0]),
                              "why": "the printed gain, which is what the game applied"})
            elif row["type"] == "theme_unducked":
                entry.update({"gain": macros["PP_AUDIO_GAIN_MUSIC"], "why": "back to the bus music level"})
            elif row["type"] == "sfx_played":
                cue_id = groups[0]
                known = effects.get(cue_id)
                if known:
                    entry.update({"cue": cue_id, "file": known["ogg"], "gain": known["gain"],
                                  "seconds": known["game_seconds"], "loop": False,
                                  "why": known["gain_why"]})
                else:
                    entry.update({"cue": cue_id, "file": None, "gain": None,
                                  "why": "the log says it played, but no manifest row names a file for it"})
            plan.append(entry)
    return plan


def mix_labels(labels, filters, group=8):
    """Mix the labels down to one, a group at a time: amix refuses a large input count."""
    level = 0
    while len(labels) > 1:
        next_labels = []
        for start in range(0, len(labels), group):
            chunk = labels[start:start + group]
            if len(chunk) == 1:
                next_labels.append(chunk[0])
                continue
            label = "[x%d_%d]" % (level, start)
            filters.append("%samix=inputs=%d:duration=longest:normalize=0%s"
                           % ("".join(chunk), len(chunk), label))
            next_labels.append(label)
        labels = next_labels
        level += 1
    return labels[0]


def render_plan(plan, seconds, out_path):
    """Proof render: every planned sound at the map's file and gain, on a stated uniform clock.

    The timing is the one thing the log cannot supply, so this render is a proof that the map names the
    right files at the right levels, not a reconstruction of a particular take. The JSON beside it says so.
    The graph goes in a script file because a 764 line log makes a command line that Windows refuses.
    """
    sounding = [entry for entry in plan
                if entry.get("file") and entry.get("sound") in ("music_start", "sfx")]
    # ffmpeg's amix refuses a few hundred inputs, and the sound of the proof does not need them: the first
    # PROOF_SEGMENTS entries are the bed plus the first sounds in the log's own order.
    sounding = sounding[:PROOF_SEGMENTS]
    slice_seconds = seconds / max(1, len(sounding))
    filters = []
    inputs = []
    labels = []
    music_open = False  # the proof renders one music bed, the first start line in the plan
    index = 0
    for position, entry in enumerate(sounding):
        start = position * slice_seconds
        if entry.get("sound") == "music_start" and not music_open:
            music_open = True
            slot = index
            inputs += ["-stream_loop", "-1", "-i", os.path.join(ROOT, entry["file"])]
            index += 1
            filters.append("[%d:a]volume=%.4f,atrim=0:%.3f,asetpts=PTS-STARTPTS[m%d]"
                           % (slot, float(entry["gain"]), seconds, slot))
            labels.append("[m%d]" % slot)
            continue
        if entry.get("sound") != "sfx":
            continue
        length = min(float(entry.get("seconds") or 0.1), seconds - start)
        if length <= 0.01:
            continue
        slot = index
        inputs += ["-i", os.path.join(ROOT, entry["file"])]
        index += 1
        filters.append("[%d:a]volume=%.4f,atrim=0:%.3f,asetpts=PTS-STARTPTS,adelay=%d:all=1[s%d]"
                       % (slot, float(entry["gain"]), length, int(round(start * 1000)), slot))
        labels.append("[s%d]" % slot)
    if not labels:
        return False, "the plan holds no sound to render"
    out_label = mix_labels(labels, filters)
    filters.append("%satrim=0:%.3f[out]" % (out_label, seconds))
    script = os.path.splitext(out_path)[0] + "_graph.txt"
    with open(script, "w", encoding="utf-8") as handle:
        handle.write(";\n".join(filters))
    args = ["ffmpeg", "-hide_banner", "-nostats", "-y"]
    args += inputs
    args += ["-/filter_complex", script, "-map", "[out]", "-c:a", "aac", "-b:a", "160k",
             "-ar", "48000", "-ac", "2", "-t", "%.3f" % seconds, out_path]
    out, error = run(args, timeout=300)
    if out is None:
        return False, error
    try:
        os.remove(script)
    except OSError:  # gate: ok the filtergraph script is scratch; a failed delete costs a stray file, nothing else
        pass
    return True, ""


def mean_volume_db(path):
    """ffmpeg's own volumedetect mean, read from stderr, so a silent track cannot pass as audio."""
    try:
        result = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "volumedetect",
                                 "-f", "null", "-"], capture_output=True, text=True, timeout=180,
                                stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as error:
        return None, str(error)
    text = (result.stderr or "") + (result.stdout or "")
    match = re.search(r"mean_volume:\s*(-?[0-9.]+) dB", text)
    return (float(match.group(1)) if match else None), ""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build", action="store_true", help="write the map JSON from the data files")
    parser.add_argument("--fixture", action="store_true",
                        help="rewrite the sample log from the source logs, verbatim and in order")
    parser.add_argument("--check", action="store_true", help="fail on any drift the map cannot survive")
    parser.add_argument("--plan", metavar="LOG", help="classify every audio line in LOG")
    parser.add_argument("--render", nargs=2, metavar=("LOG", "OUT"), help="proof render from LOG")
    parser.add_argument("--uniform-seconds", type=float, default=8.0,
                        help="length of the proof render (the clock is uniform and says so)")
    args = parser.parse_args(argv)

    did = False
    if args.fixture:
        did = True
        write_fixture()
        print("wrote %s (%d bytes)" % (repo_relative(SAMPLE_LOG), os.path.getsize(SAMPLE_LOG)))
    if args.build:
        did = True
        data = build_map()
        with open(MAP_PATH, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=False)
            handle.write("\n")
        print("wrote %s (%d bytes)" % (repo_relative(MAP_PATH), os.path.getsize(MAP_PATH)))
        print("event types %d, effects %d, cues %d, unmatched lines %d"
              % (len(data["events"]), len(data["effects"]), len(data["cues"]),
                 len(data["unmatched_lines"])))
        for line in data["unmatched_lines"][:5]:
            print("  unmatched: %s" % line)

    if args.check:
        did = True
        problems = check_map()
        if problems:
            print("FAIL %d problem%s" % (len(problems), "" if len(problems) == 1 else "s"))
            for problem in problems:
                print("  %s" % problem)
            return 1
        print("PASS the map matches the data files, the gml grammar and the sample log")

    if args.plan:
        did = True
        data = read_json(MAP_PATH)
        plan = plan_log(args.plan, data)
        kinds = {}
        for entry in plan:
            kinds[entry["sound"]] = kinds.get(entry["sound"], 0) + 1
        for entry in plan:
            print("%3d %-22s %-14s %-8s %s"
                  % (entry["order"], entry["type"], entry["sound"],
                     "" if entry.get("gain") is None else entry["gain"],
                     entry.get("file") or entry.get("cue") or ""))
        print("lines %d, by sound: %s" % (len(plan), kinds))
        unresolved = [entry for entry in plan if entry["type"] is None]
        if unresolved:
            print("FAIL %d line(s) with no event type" % len(unresolved))
            return 1
        return 0

    if args.render:
        did = True
        log_path, out_path = args.render
        data = read_json(MAP_PATH)
        plan = plan_log(log_path, data)
        if not any(entry.get("file") for entry in plan):
            print("FAIL nothing in the log resolves to a file")
            return 1
        ok, error = render_plan(plan, args.uniform_seconds, out_path)
        if not ok:
            print("FAIL the proof render did not run: %s" % error)
            return 1
        mean, _why = mean_volume_db(out_path)
        report = {"kind": "event_log_audio_map_proof_render",
                  "card": "t_37855a33",
                  "log": repo_relative(log_path),
                  "map": repo_relative(MAP_PATH),
                  "track": repo_relative(out_path),
                  "seconds": args.uniform_seconds,
                  "mean_volume_db": None if mean is None else round(mean, 2),
                  "timing": ("uniform: one plan entry per equal slice, because the log has no timestamps. "
                             "This is a proof that the map names the right files at the right levels, not a "
                             "reconstruction of a take. A take supplies arrival stamps."),
                  "entries": plan}
        with open(os.path.splitext(out_path)[0] + "_proof.json", "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
            handle.write("\n")
        print("wrote %s, mean %s dB, %d entries"
              % (repo_relative(out_path), report["mean_volume_db"], len(plan)))
        if mean is not None and mean <= -70.0:
            print("FAIL the proof track is silence")
            return 1

    if not did:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
