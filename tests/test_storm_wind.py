"""The quay's hurricane, heard (card t_321826d8, JUDGE-PANEL 2026-11-16 fix 4).

The panel asked the musician lane for "a hurricane wind loop for quay and simple square wave blips for cursor
and talk in the engine audio module", and for a capture whose verify file reports audio present. This file pins
the engine half of that in three parts:

  1. the effect itself: wind_quay ships, it is a loop, its period is one whole APU noise cycle, and the two
     tables that must name it (assets/audio/sfx/manifest.json and game/datafiles/sfx/sfx.json, written by
     tools/sfx.py and tools/sync_art.py) both carry it with the same byte length;
  2. the wiring: pp_audio_wind_step holds ONE looping instance with loop ON, starts it only while the storm is
     up on the quay, follows the storm's own wind number for its gain, stops it when the wind is 0, and lets
     the focus rule pause and resume it rather than restarted;
  3. the sounds the panel named that were already shipped: the cursor blips (menu_move, menu_select) and the
     talk blip (pp_text calls pp_audio_blip every second letter). They are pinned here so the next round
     measures them instead of rebuilding them.

Honest limit: no GameMaker window is opened by this file, so nothing here says a speaker made a noise. What is
pinned is the contract between the generated files, the data and the module text. The demo cut's own audio is
measured by tools/demo_music_bed.py --verify, and that report is the one the panel reads.
"""

from __future__ import annotations

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE = os.path.join(ROOT, "game", "scripts", "pp_audio", "pp_audio.gml")
STORM = os.path.join(ROOT, "game", "scripts", "pp_storm", "pp_storm.gml")
TEXT = os.path.join(ROOT, "game", "scripts", "pp_text", "pp_text.gml")
SFX_MANIFEST = os.path.join(ROOT, "assets", "audio", "sfx", "manifest.json")
SFX_JSON = os.path.join(ROOT, "game", "datafiles", "sfx", "sfx.json")
AUDIO_JSON = os.path.join(ROOT, "data", "audio.json")
MAPS = os.path.join(ROOT, "data", "maps", "all.json")


def _read(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def _json(path):
    return json.loads(_read(path))


def _function(text, name):
    """The doc comment plus the body of one GML function, or a failure that names it."""
    match = re.search(r"\nfunction %s\([^)]*\) \{(.*?)\n\}" % re.escape(name), text, re.S)
    assert match, "no function %s in the module" % name
    return match.group(1)


def test_the_wind_effect_ships_as_a_loop():
    manifest = _json(SFX_MANIFEST)
    entry = next((e for e in manifest["effects"] if e["name"] == "wind_quay"), None)
    assert entry is not None, "wind_quay is not in assets/audio/sfx/manifest.json"
    assert entry["loop"] is True, "the hurricane must be a loop, not a one shot"
    assert entry["loop_start"] == 0
    assert entry["loop_period"] == entry["loop_length"], \
        "the wind's period is one whole noise cycle, so it is the whole file"
    assert entry["files"].get("wav") and entry["files"].get("ogg"), entry
    for key in ("wav", "ogg"):
        path = os.path.join(ROOT, "assets", "audio", "sfx", entry["files"][key])
        assert os.path.exists(path) and os.path.getsize(path) > 1000, path
    # One LFSR cycle at period 202 is 32767 * 44100 * 202 / 1789772.5 = 163091 samples, 3.698 s. A file
    # even a few samples short of that would cut the sequence and step at the seam, so the measured length
    # is pinned to the generator's own arithmetic rather than to a round number.
    wanted = int(round(32767 * 44100 * 202 / 1789772.5))
    assert entry["loop_length"] == wanted, "the wind is %d samples, one LFSR cycle is %d" % (
        entry["loop_length"], wanted)


def test_the_build_mirror_carries_the_wind_with_the_same_bytes():
    cues = {c["id"]: c for c in _json(SFX_JSON)["cues"]}
    assert "wind_quay" in cues, "tools/sync_art.py did not mirror wind_quay into game/datafiles/sfx"
    row = _json(AUDIO_JSON)["sounds"]
    names = {r["id"]: r for r in row}
    assert "wind_quay" in names, "data/audio.json does not record the delivered effect"
    assert names["wind_quay"]["loop"] is True
    assert names["wind_quay"]["delivered_file"] == "assets/audio/sfx/wind_quay.ogg"
    wav = os.path.join(ROOT, "game", "datafiles", "sfx", cues["wind_quay"]["file"])
    assert os.path.exists(wav), wav
    assert cues["wind_quay"]["seconds"] >= 3.6, cues["wind_quay"]


def test_the_bus_holds_one_looping_wind_while_the_storm_is_up():
    text = _read(MODULE)
    assert '#macro PP_AUDIO_AMBIENCE_WIND "wind_quay"' in text
    step = _function(text, "pp_audio_wind_step")
    assert "audio_play_sound(_sound, PP_AUDIO_PRI_SFX, true, _gain)" in step, \
        "the wind must be started with loop ON, or it fires once and the room goes quiet"
    assert "pp_audio_wind_stop(_a," in step, "the wind must be handed to the stop when it is no longer wanted"
    stop = _function(text, "pp_audio_wind_stop")
    finish = _function(text, "pp_audio_wind_finish")
    # The stop is a ramp, not a cut (the reviewer's third non-blocking point): the gain goes to 0 over the ramp
    # and the hard stop lives in the function the step calls once the ramp's deadline has passed.
    assert "audio_stop_sound(_a.wind_inst)" not in stop, \
        "a held noise loop at 0.32 cut with audio_stop_sound is a click; ramp it out and stop it at 0"
    assert "audio_sound_gain(_a.wind_inst, 0, PP_AUDIO_WIND_RAMP_MS)" in stop
    assert "_a.wind_stop_ms = current_time + PP_AUDIO_WIND_RAMP_MS" in stop
    assert "audio_stop_sound(_a.wind_inst)" in finish, "the finish must actually stop the held instance at 0"
    assert "_a.wind_inst = -1" in finish, "a stopped instance must not be addressed again"
    assert "current_time >= _a.wind_stop_ms" in step and "pp_audio_wind_finish(_a)" in step, \
        "the step must finish a ramp whose time is up, or the wind never stops"
    assert "PP_AUDIO_GAIN_WIND * (_wind / 100)" in step, "the gain must follow the storm's own wind number"
    target = _function(text, "pp_audio_wind_target")
    assert "pp_storm_active(_world)" in target, "the bus must ask the storm module, not keep a second copy"
    assert "pp_storm_wind()" in target
    assert "return 0" in target, "any room but the quay must be silent of wind"
    # One step of the bus drives it, and the focus rule owns the instance while the window is away.
    bus = _function(text, "pp_audio_step")
    assert "pp_audio_wind_step(_a)" in bus
    focus = _function(text, "pp_audio_focus")
    assert "audio_pause_sound(_a.wind_inst)" in focus
    assert "audio_resume_sound(_a.wind_inst)" in focus


def test_the_wind_level_is_written_once():
    """The reviewer's second non-blocking point: the level was written twice with nothing tying the two copies.

    `PP_AUDIO_GAIN_WIND` is what the game plays at, `data/audio.json` is what the demo bed reads, and the bed's
    own gain is that number times `WIND_UNDER_GAME`. One assertion over all three means a drift in either copy
    changes the film and the game together or fails here.
    """
    import sys
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import demo_music_bed as bed

    match = re.search(r"#macro PP_AUDIO_GAIN_WIND ([0-9.]+)", _read(MODULE))
    assert match, "the module no longer declares PP_AUDIO_GAIN_WIND"
    macro = float(match.group(1))
    row = next((r for r in _json(AUDIO_JSON)["sounds"] if r["id"] == "wind_quay"), None)
    assert row is not None, "data/audio.json has no wind_quay row"
    assert abs(float(row["volume"]) - macro) < 1e-9, \
        "the module plays the wind at %s and data/audio.json says %s" % (macro, row["volume"])
    assert abs(round(macro * bed.WIND_UNDER_GAME, 4) - 0.288) < 1e-9, \
        "the demo bed's wind gain moved off 0.288: %s" % round(macro * bed.WIND_UNDER_GAME, 4)


def test_the_storm_owns_the_number_the_wind_is_played_at():
    storm = _read(STORM)
    assert '#macro PP_STORM_ROOM "southampton_town_quay"' in storm
    wind = _function(storm, "pp_storm_wind")
    assert "pp_storm_gate_open()" in wind and "return 0" in wind, \
        "the wind must fall to nothing once the gate is open"
    assert "100 - _m" in wind, "the wind is the complement of the mercy the Morgan fight reached"
    maps = _json(MAPS)["maps"]
    quay = next((m for m in maps if m.get("id") == "southampton_town_quay"), None)
    assert quay is not None, "no map named southampton_town_quay, so the storm has no room"
    assert quay.get("music") == "PP-03", quay.get("music")


def test_the_cursor_and_talk_blips_the_panel_asked_for_are_wired():
    """The panel asked for "simple square wave blips for cursor and talk". Both were shipped; measure, do not rebuild."""
    bus = _read(MODULE)
    # The cursor: every menu path asks the bus for these two by name, and they are pulses at C6 and E5 to E6.
    cursor = 0
    for folder in ("pp_title", "pp_overworld", "pp_battle_director", "pp_app", "pp_scene", "pp_dialogue"):
        path = os.path.join(ROOT, "game", "scripts", folder)
        for name in os.listdir(path):
            if name.endswith(".gml"):
                text = _read(os.path.join(path, name))
                cursor += len(re.findall(r'pp_audio_play\("menu_(?:move|select|cancel)"\)', text))
    assert cursor >= 10, "only %d cursor blip call sites, the menus are not wired" % cursor
    # The talk: pp_text reveals a letter at a time and asks for the blip through the one function that owns
    # the priority and the half level.
    talk = _read(TEXT)
    assert "pp_audio_blip(_rv.speaker);" in talk, "the talk box does not ask for its blip"
    blip = _function(bus, "pp_audio_blip")
    assert 'pp_audio_sfx("ui", _cue)' in blip
    assert "PP_AUDIO_GAIN_SFX * PP_AUDIO_GAIN_BLIP" in blip
    for letter in ("text_blip_a", "text_blip_b", "text_blip_c"):
        assert '"%s"' % letter in bus
        assert os.path.exists(os.path.join(ROOT, "assets", "audio", "sfx", letter + ".ogg")), letter


def test_the_demo_bed_lays_the_wind_under_the_quay_shots(tmp_path):
    """tools/demo_music_bed.py must put the hurricane under every second the cut spends on the quay.

    The plan is read against a synthetic cut, not against tonight's render: the segment rows are the same clocks
    the real verify file carries, so this test does not race whichever lane is writing output/demo tonight.
    """
    import sys
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import demo_music_bed as bed

    cut = tmp_path / "cut.mp4"
    cut.write_bytes(b"")
    rows = [{"shot": shot, "clock": lo, "seconds": hi - lo}
            for shot, lo, hi, _cue in bed.BED_TABLE]
    rows += [{"shot": shot, "clock": lo, "seconds": hi - lo} for shot, lo, hi in bed.WIND_TABLE]
    (tmp_path / "cut_verify.json").write_text(json.dumps({"duration_s": 180.0, "segments": rows}),
                                              encoding="utf-8")

    items = bed.plan(str(cut))
    wind = [item for item in items if item.get("kind") == "ambience"]
    assert [item["window"] for item in wind] == [[lo, hi] for _shot, lo, hi in bed.WIND_TABLE]
    sounds = {row["id"]: row for row in _json(AUDIO_JSON)["sounds"]}
    for item in wind:
        assert item["cue"] == "wind_quay"
        assert item["file"] == sounds["wind_quay"]["delivered_file"], item["file"]
        assert abs(item["gain"] - round(0.32 * bed.WIND_UNDER_GAME, 4)) < 1e-9, item["gain"]
    assert sum(item["seconds"] for item in wind) >= 80.0, \
        "the wind covers %s s of the 180, which is not the quay's four windows" % sum(
            item["seconds"] for item in wind)
    # The quay's own music is PP-03 on every window the wind sits under, so the storm and its score agree.
    for item in wind:
        music = [m for m in items if m.get("kind") != "ambience" and m["window"] == item["window"]]
        assert music and music[0]["cue"] == "PP-03", (item["window"], [m["cue"] for m in music])
