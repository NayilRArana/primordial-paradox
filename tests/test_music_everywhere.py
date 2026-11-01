"""Music everywhere (card MUSIC-EVERYWHERE, 2026-11-01).

The defect these tests would have caught: data\\maps\\all.json gave every room a `music` cue and pp_map_load copied it onto the
map, but the only caller of pp_audio_music in the whole game was the scene `music` command, so music played on the title
screen and in a scene that happened to carry the command, and nowhere else. Nothing started a room's cue when the room
became the active one, nothing started a fight cue, and nothing restored the room cue after a fight.

What is pinned, and how:
  - DATA: every room in the runtime registry (data\\maps\\all.json plus the ship_sample.json that pp_data.gml appends) names a
    cue, and the cue resolves, by the same delivered_file / asset / fallback rules the bus uses, to an OGG that exists in
    assets\\audio, is mirrored into game\\datafiles\\streams and is listed as an Included File in the .yyp. A pending cue
    (PP-07 to PP-16) falls back to a landed cue, so no room and no fight is silent.
  - SOURCE (grep level, brace counted per function): every path that makes a room the active one calls pp_audio_room,
    the battle mode opens with pp_audio_battle, the way back from a fight asks for the room cue, a defeat stops the music,
    the title theme stops a playing cue, a scene's own music command still reaches pp_audio_music, and the PP_MUSIC_TOUR
    debug door drives the same two calls.
Honest limit: no GameMaker window was opened for these tests. They prove the wiring and the data; what a speaker plays is
proved by the headless tour whose command is in output\\music_everywhere_2026-11-01\\PROGRESS.md.
"""

from __future__ import annotations

import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "game", "scripts")
STREAMS = os.path.join(ROOT, "game", "datafiles", "streams")
MAX_HOPS = 8
BS = chr(92)


def _json(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as handle:
        return json.load(handle)


def _text(rel):
    with open(os.path.join(SCRIPTS, *rel.split("/")), encoding="utf-8") as handle:
        return handle.read()


def _mask(text):
    """The same text with string contents and // comments blanked, same length, so a brace in either cannot upset the count."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"' and text[j] != "\n":
                j += 1
            closed = j < n and text[j] == '"'
            out.append('"' + " " * (j - i - 1) + ('"' if closed else ""))
            i = j + 1 if closed else j
            continue
        if text[i:i + 2] == "//":
            j = text.find("\n", i)
            if j < 0:
                j = n
            out.append(" " * (j - i))
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _function(text, name):
    """(raw, code) of one GML function: its text with strings, and the same span with strings and comments blanked."""
    mask = _mask(text)
    found = re.search(r"function " + re.escape(name) + r"[(]", mask)
    assert found, "function %s is missing" % name
    start = mask.index("{", found.end())
    depth = 0
    for i in range(start, len(mask)):
        if mask[i] == "{":
            depth += 1
        elif mask[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1], mask[start:i + 1]
    raise AssertionError("function %s never closes" % name)


# ---------------------------------------------------------------------------------------------------------------
# DATA: the bus's own resolution rules, restated from pp_audio_music_file_name, pp_audio_music_paths and
# pp_audio_cue_resolve, so a data edit that leaves a room silent is a red test.

def _cue_rows():
    return {row["id"]: row for row in _json("data", "audio.json")["cues"]}


def _candidates(row):
    declared = row.get("delivered_file")
    first = str(row["asset"]) + ".ogg"
    if isinstance(declared, str) and declared:
        first = declared.replace(BS, "/").split("/")[-1]
    names = [first]
    if str(row["asset"]) + ".ogg" != first:
        names.append(str(row["asset"]) + ".ogg")
    return names


def _landed_name(row):
    for name in _candidates(row):
        if os.path.isfile(os.path.join(STREAMS, name)):
            return name
    return None


def _resolve(cue):
    """(cue that plays, OGG name) after following `fallback`, or (None, None)."""
    rows = _cue_rows()
    current = cue
    for _ in range(MAX_HOPS):
        row = rows.get(current)
        if row is None:
            return None, None
        name = _landed_name(row)
        if name:
            return current, name
        current = row.get("fallback")
        if not current:
            return None, None
    return None, None


def _rooms():
    rooms = list(_json("data", "maps", "all.json")["maps"])
    rooms += _json("data", "maps", "ship_sample.json")["maps"]
    return rooms


def _yyp_stream_files():
    with open(os.path.join(ROOT, "game", "PrimordialParadox.yyp"), encoding="utf-8") as handle:
        text = handle.read()
    names = set()
    for block in re.findall(r"[{][^{}]*[}]", text):
        path = re.search(r'"filePath":\s*"([^"]*)"', block)
        name = re.search(r'"name":\s*"([^"]*)"', block)
        if path and name and path.group(1) == "datafiles/streams":
            names.add(name.group(1))
    return names


def test_the_runtime_room_registry_is_all_json_plus_ship_sample():
    assert "maps/ship_sample.json" in _text("pp_data/pp_data.gml"), \
        "pp_data.gml no longer appends ship_sample.json, so _rooms() would test the wrong registry"
    ids = [room["id"] for room in _rooms()]
    assert len(ids) == len(set(ids)), "a room id appears twice: %s" % ids


def test_every_room_has_a_music_cue_that_resolves_to_an_ogg_in_the_build():
    yyp = _yyp_stream_files()
    for room in _rooms():
        where = "room %s" % room["id"]
        cue = room.get("music")
        assert isinstance(cue, str) and cue != "", "%s names no music cue, so it would be silent" % where
        assert cue in _cue_rows(), "%s names %s, which is not a row in data\\audio.json" % (where, cue)
        played, name = _resolve(cue)
        assert played is not None, "%s: %s resolves to no OGG (fallback chain ends without a file)" % (where, cue)
        source = glob.glob(os.path.join(ROOT, "assets", "audio", "**", name), recursive=True)
        assert source, "%s: %s is not under assets\\audio" % (where, name)
        assert os.path.isfile(os.path.join(STREAMS, name)), "%s: %s is not mirrored into game\\datafiles\\streams" % (where, name)
        assert name in yyp, "%s: %s is not an Included File in the .yyp (filePath datafiles/streams)" % (where, name)


def test_the_named_rooms_carry_the_cues_the_story_gave_them():
    cues = {room["id"]: room.get("music") for room in _rooms()}
    expected = {
        "southampton_town_quay": "PP-03",
        "quay_dock_office": "PP-03",
        "ship_small": "PP-05",
        "ship_cabin": "PP-05",
        "ship_sample": "PP-05",
        "drive_m4_corridor": "PP-02",
    }
    for room_id, cue in expected.items():
        assert room_id in cues, "room %s is gone from the registry" % room_id
        assert cues[room_id] == cue, "room %s carries %s, expected %s" % (room_id, cues[room_id], cue)


def test_pending_cues_fall_back_to_a_landed_cue_so_nothing_is_silent():
    rows = _cue_rows()
    pending = [cue for cue, row in rows.items() if row.get("pending")]
    for wanted in ("PP-07", "PP-08", "PP-09", "PP-10", "PP-11", "PP-12", "PP-13", "PP-14", "PP-15a", "PP-15b", "PP-16"):
        assert wanted in pending, "%s is expected to be a pending cue today; if it landed, drop it from this list" % wanted
    for cue in pending:
        played, name = _resolve(cue)
        assert played is not None and played != cue, "pending cue %s has no landed fallback" % cue
        assert not rows[played].get("pending"), "pending cue %s falls back to another pending cue %s" % (cue, played)


def test_every_encounter_names_a_fight_cue_that_resolves():
    rows = _cue_rows()
    fight_cue = re.search(r'#macro PP_AUDIO_FIGHT_CUE "([^"]+)"', _text("pp_audio/pp_audio.gml"))
    assert fight_cue, "PP_AUDIO_FIGHT_CUE is missing"
    assert _resolve(fight_cue.group(1))[0] == fight_cue.group(1), "the default fight cue must be a landed cue"
    for enc in _json("data", "encounters", "all.json")["encounters"]:
        cue = enc.get("music", fight_cue.group(1))
        assert cue in rows, "encounter %s names %s, not a row in audio.json" % (enc["id"], cue)
        assert _resolve(cue)[0] is not None, "encounter %s: cue %s resolves to no OGG" % (enc["id"], cue)
    percy = [enc for enc in _json("data", "encounters", "all.json")["encounters"] if enc["id"] == "percy"][0]
    assert rows[percy["music"]].get("boss") is True, "Percy's fight must keep the boss priority row"


# ---------------------------------------------------------------------------------------------------------------
# SOURCE: the wiring itself.

def test_the_bus_follows_fallback_before_it_decides_a_cue_is_already_playing():
    audio = _text("pp_audio/pp_audio.gml")
    _, resolver = _function(audio, "pp_audio_cue_resolve")
    assert '"fallback"' in _function(audio, "pp_audio_cue_resolve")[0], "the resolver does not read the fallback field"
    assert "pp_audio_cue_file(" in resolver
    _, music = _function(audio, "pp_audio_music")
    assert "pp_audio_cue_resolve(_cue)" in music
    assert music.index("pp_audio_cue_resolve(_cue)") < music.index("_a.music_cue == _cue"), \
        "the fallback must resolve before the already playing test, or two rooms on one stream restart it"
    assert "return true;" in music[music.index("_a.music_cue == _cue"):], "asking for the playing cue must not restart it"


def test_every_room_entry_path_asks_the_bus_for_the_room_cue():
    overworld = _text("pp_overworld/pp_overworld.gml")
    for name in ("pp_overworld_new", "pp_overworld_change_map"):
        assert "pp_audio_room(_map)" in _function(overworld, name)[1], "%s does not start the room cue" % name
    assert "pp_audio_room(_map)" in _function(_text("pp_scene/pp_scene.gml"), "pp_scene_world_place")[1]
    app = _text("pp_app/pp_app.gml")
    assert "pp_overworld_new(" in _function(app, "pp_mode_overworld")[1], "the mode no longer builds the world through pp_overworld_new"
    assert "pp_overworld_new(" in _function(_text("pp_save/pp_save.gml"), "pp_save_apply")[1], \
        "a load from a save no longer builds the world through pp_overworld_new, which is where its music starts"
    raw, code = _function(_text("pp_audio/pp_audio.gml"), "pp_audio_room")
    assert "pp_audio_music(_cue, PP_AUDIO_FADE_STEPS)" in code
    assert "_map.music" in code
    assert "PP audio: room " in raw and "asked " in raw and "playing " in raw, \
        "a room entry must log the room, the cue it asked for and the cue that is playing"
    assert "pp_audio_music(_cmd.id, PP_AUDIO_FADE_STEPS)" in _text("pp_scene/pp_scene.gml"), \
        "a scene's own music command no longer reaches the bus"


def test_the_fight_path_starts_the_encounter_cue_and_the_way_back_restores_the_room_cue():
    app = _text("pp_app/pp_app.gml")
    battle = _function(app, "pp_mode_battle")[1]
    assert "pp_audio_battle(_enc)" in battle, "the battle mode does not start the fight cue"
    overworld = _function(app, "pp_mode_overworld")[1]
    call = overworld.index("pp_audio_room(global.pp.world.map)")
    assert call < overworld.index("return;"), "the resumed branch must ask for the room cue before it returns"
    raw, code = _function(_text("pp_audio/pp_audio.gml"), "pp_audio_battle")
    assert "_enc.music" in code and "PP_AUDIO_FIGHT_CUE" in code, "the fight reads the encounter's cue and falls back to PP-04"
    assert "pp_audio_music(_cue, PP_AUDIO_FADE_STEPS)" in code
    assert "PP audio: fight " in raw


def test_a_defeat_stops_the_music_and_the_title_theme_takes_over_from_a_playing_cue():
    _, result = _function(_text("pp_battle_director/pp_battle_director.gml"), "pp_battle_enter_result")
    assert "_battle.defeated" in result and "pp_audio_music_stop()" in result
    assert result.index("pp_audio_music_stop()") < result.index("pp_battle_say("), "the stop belongs before the closing board is said"
    _, theme = _function(_text("pp_audio/pp_audio.gml"), "pp_audio_play_theme")
    assert "pp_audio_music_stop()" in theme, "the title theme would play over a room cue on the way back to the title"


def test_the_music_tour_debug_door_drives_the_same_two_calls_and_is_called_from_the_step():
    overworld = _text("pp_overworld/pp_overworld.gml")
    assert re.search(r'#macro PP_MUSIC_TOUR "PP_" [+] "MUSIC_TOUR"', overworld)
    tour = _function(overworld, "pp_overworld_music_tour")[1]
    assert "environment_get_variable(PP_MUSIC_TOUR)" in tour
    assert "pp_audio_room(" in tour and "pp_audio_battle(" in tour
    assert "pp_audio_music_stop" not in tour and "pp_save_" not in tour and "pp_map_load(" not in tour, \
        "the tour must stay a read of the data rows: no save, no map load"
    assert "pp_overworld_music_tour(_world)" in _function(overworld, "pp_overworld_step")[1]
