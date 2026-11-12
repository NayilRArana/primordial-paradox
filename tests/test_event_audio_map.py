"""Pins for card t_37855a33: the event log audio map names real files, and nothing in it is a guess.

What these tests hold down, and why each one earns its place:
  1. every message site the audio bus can write has a row in the map, the row points at the gml line that
     writes it, and the row's regex compiles; a message added to pp_audio.gml without a map row fails here
     instead of quietly becoming an unrenderable line;
  2. every real audio line in the shipped sample log classifies as exactly one row, so a renderer has no
     line it must guess at, and each row says whether it makes sound, stops it, changes its gain or is silence;
  3. the file table is the game's own data: the effect ids are sfx.json's cues, the cue ids are
     data/audio.json's rows, and every landed cue's delivered OGG and every effect's OGG are on disk;
  4. the title theme's beat adds up: 126 bpm over a 3/4 bar, 52 bars, and the ledger's own loop length;
  5. planning the sample log either resolves every sound line to a file that exists, or names the reason it
     cannot (a stream no landed cue row streams any more, or a file this checkout does not carry), so a
     fresh implementer can render from it without inventing a name.

No ffprobe and no game/datafiles here: the suite runs in a clean export, where game/datafiles is not
committed (the same reason tests/test_play_demo_audio.py builds its own copies). The measured durations live
in the map and are re-measured by `python tools/event_audio_map.py --check` on a machine that has the files.

Run: python -m pytest tests/test_event_audio_map.py -q
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

MAP_PATH = os.path.join(ROOT, "knowledge", "EVENT-LOG-AUDIO-MAP-2026-11-01.json")
SAMPLE_LOG = os.path.join(ROOT, "knowledge", "EVENT-LOG-SAMPLE-2026-11-01.txt")
AUDIO_JSON = os.path.join(ROOT, "data", "audio.json")
SFX_JSON = os.path.join(ROOT, "game", "datafiles", "sfx", "sfx.json")
AUDIO_GML = os.path.join(ROOT, "game", "scripts", "pp_audio", "pp_audio.gml")

# The two reasons a sound line in the sample log may resolve to no file: the stream is a retired name no
# landed cue row in data/audio.json streams any more, or the file is simply not in this checkout. Both are
# stated in the plan beside the line, so a renderer reads a reason and never guesses at a file.
MISSING_KINDS = ("retired_stream", "not_in_checkout")


def load_tool(name: str):
    path = os.path.join(TOOLS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def tool():
    return load_tool("event_audio_map")


@pytest.fixture(scope="module")
def the_map():
    with open(MAP_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="module")
def sample_lines():
    with open(SAMPLE_LOG, "r", encoding="utf-8") as handle:
        return [line.rstrip("\n") for line in handle
                if "PP audio:" in line and not line.lstrip().startswith("#")]


class TestTheGrammar:
    def test_every_message_site_in_the_bus_has_a_row(self, the_map):
        text = open(AUDIO_GML, "r", encoding="utf-8").read()
        sites = len(re.findall(r'show_debug_message\("PP audio:', text))
        named = [line for row in the_map["events"] for line in
                 [int(part) for part in re.findall(r"pp_audio\.gml:(\d+)", row["source"])]]
        assert len(named) == sites, "a PP audio: message site exists with no row in the map"

    def test_each_row_points_at_a_real_message_site(self, the_map):
        source = open(AUDIO_GML, "r", encoding="utf-8").read().splitlines()
        for row in the_map["events"]:
            lines = [int(part) for part in re.findall(r"pp_audio\.gml:(\d+)", row["source"])]
            assert lines, "%s names no gml line" % row["type"]
            for line in lines:
                window = "\n".join(source[max(0, line - 2):line + 1])
                assert 'show_debug_message("PP audio:' in window, \
                    "%s points at gml line %d, which writes no PP audio line" % (row["type"], line)

    def test_every_regex_compiles_and_is_unique(self, the_map):
        patterns = [row["regex"] for row in the_map["events"]]
        for row in the_map["events"]:
            re.compile(row["regex"])
        assert len(patterns) == len(set(patterns)), "two event rows share one pattern, so one can never win"

    def test_every_row_says_what_a_renderer_does(self, the_map):
        allowed = {"music_start", "music_stop", "music_gain", "music_pause", "music_resume", "sfx", "none"}
        for row in the_map["events"]:
            assert row["sound"] in allowed, "%s has sound %r" % (row["type"], row["sound"])
            assert row["meaning"], "%s has no meaning" % row["type"]

    def test_a_line_maps_to_one_row_and_the_sample_has_no_orphans(self, tool, sample_lines):
        assert sample_lines, "the sample log carries no PP audio line"
        types = set()
        for line in sample_lines:
            row, match = tool.classify(line)
            assert row is not None, "no event type matches a real line: %s" % line
            assert match is not None
            types.add(row["type"])
        # The fixture is the proof that these branches are worded as the map says; the rest say so in the gml.
        assert len(types) >= 12, "the fixture exercises only %d event types" % len(types)

    def test_an_unobserved_row_gives_a_reason(self, the_map, sample_lines):
        counts = the_map["event_line_counts"]
        for row in the_map["events"]:
            if counts.get(row["type"]):
                assert row["observed_in_logs"] is True
                continue
            assert row["why_unobserved"], "%s has no sample line and no reason" % row["type"]


class TestTheFiles:
    def test_the_effect_ids_are_the_games_manifest(self, the_map):
        with open(SFX_JSON, "r", encoding="utf-8") as handle:
            manifest = {row["id"] for row in json.load(handle)["cues"]}
        assert set(the_map["effects"]) == manifest

    def test_every_effect_ogg_is_on_disk_and_has_a_gain(self, the_map):
        for cue_id, row in the_map["effects"].items():
            path = os.path.join(ROOT, row["ogg"])
            assert os.path.isfile(path), "%s names %s, which is not in the tree" % (cue_id, row["ogg"])
            assert row["ogg"].startswith("assets/audio/sfx/"), "%s does not point at the delivered ogg" % cue_id
            assert row["gain"] in (0.45, 0.9, 1.0), "%s has gain %r" % (cue_id, row["gain"])
            assert row["gain_why"], "%s has a gain with no reason" % cue_id

    def test_the_blips_are_the_half_level_ones(self, the_map):
        for cue_id, row in the_map["effects"].items():
            if cue_id.startswith("text_blip"):
                assert row["gain"] == 0.45, "%s is a blip at %r, not the bus's 0.9 times the 0.5 blip level" \
                    % (cue_id, row["gain"])

    def test_the_cue_ids_are_the_games_ledger(self, the_map):
        with open(AUDIO_JSON, "r", encoding="utf-8") as handle:
            ledger = {row["id"]: row for row in json.load(handle)["cues"]}
        assert set(the_map["cues"]) == set(ledger)
        for cue_id, row in the_map["cues"].items():
            assert row["landed"] == bool(ledger[cue_id].get("delivered_file")), \
                "%s disagrees with data/audio.json about being landed" % cue_id
            if row["landed"]:
                assert os.path.isfile(os.path.join(ROOT, row["file"])), \
                    "%s says landed and %s is not on disk" % (cue_id, row["file"])
            else:
                assert row["fallback"], "%s is pending with no fallback" % cue_id

    def test_a_pending_cue_falls_back_to_a_landed_one(self, the_map):
        for cue_id, row in the_map["cues"].items():
            if row["landed"]:
                continue
            seen = set()
            target = row["fallback"]
            while target and target not in seen:
                seen.add(target)
                entry = the_map["cues"].get(target)
                assert entry is not None, "%s falls back to %s, which is not a cue" % (cue_id, target)
                if entry["landed"]:
                    break
                target = entry["fallback"]
            else:
                pytest.fail("%s falls back through %s and never reaches a landed cue" % (cue_id, sorted(seen)))


class TestTheTitleTheme:
    def test_the_beat_adds_up(self, the_map):
        beat = the_map["title_theme"]["beat"]
        assert abs(beat["beat_seconds"] - 60.0 / beat["bpm"]) < 1e-6
        assert abs(beat["bar_seconds"] - beat["beats_per_bar"] * beat["beat_seconds"]) < 1e-6
        loop_seconds = beat["loop_bars"] * beat["beats_per_bar"] * beat["beat_seconds"]
        assert abs(loop_seconds - beat["loop_seconds"]) < 0.01, \
            "the loop ledger's bars and beats do not add up to its own loop_seconds"

    def test_the_theme_is_the_first_stream_the_bus_asks_for(self, the_map, tool):
        assert the_map["title_theme"]["asked_streams"] == tool.theme_candidates()
        assert the_map["title_theme"]["chosen_stream"] == the_map["title_theme"]["asked_streams"][0]

    def test_the_theme_file_is_on_disk(self, the_map):
        assert os.path.isfile(os.path.join(ROOT, the_map["title_theme"]["file"]))

    def test_the_duck_is_recorded_as_the_game_actually_plays_it(self, the_map):
        text = the_map["title_theme"]["duck_defect"]
        assert "gain 1.40" in text, "the map must record the measured duck line, not the intended one"
        assert "10^(db/20)" in text or "10^(db / 20)" in text


class TestThePlan:
    def test_the_sample_log_plans_without_a_guess(self, tool, the_map, sample_lines):
        plan = tool.plan_log(SAMPLE_LOG, the_map)
        assert len(plan) == len(sample_lines)
        assert [entry for entry in plan if entry["type"] is None] == []
        sounds = [entry for entry in plan if entry["sound"] in ("music_start", "sfx")]
        assert sounds, "the plan holds no sound at all"
        for entry in sounds:
            if not entry.get("file"):
                # A line this checkout cannot answer must say so and say why. A renderer reading the plan
                # has to know the line is not placeable, not that the game chose silence there.
                assert entry.get("missing") in MISSING_KINDS, \
                    "%s resolved to no file and no reason: %s" % (entry["cue"], entry["line"])
                assert entry.get("why"), "%s is missing for no stated reason" % entry["cue"]
                continue
            assert os.path.isfile(os.path.join(ROOT, entry["file"])), \
                "%s resolved to %s, which is not on disk" % (entry["cue"], entry["file"])

    def test_a_stream_no_ledger_row_names_is_recorded_as_retired(self, tool, the_map):
        # The sample log is copied from a build dated before 2026-11-03, when PP-06 still streamed the old
        # percy_theme.ogg. That file exists on the machine that wrote the log, so resolving it from disk
        # was green there and red on every checkout: the plan must name the retirement instead.
        registered = tool.registered_stream_leaves(the_map)
        plan = tool.plan_log(SAMPLE_LOG, the_map)
        retired = [entry for entry in plan if entry.get("missing") == "retired_stream"]
        assert retired, "the sample log carries the PP-06 line that predates the cue's current file"
        for entry in retired:
            assert entry["stream"].startswith("streams/"), "%s is not repo-relative" % entry["stream"]
            assert entry["stream"].split("/")[-1] not in registered, \
                "a line was called retired although a landed cue still streams %s" % entry["stream"]
            assert entry["registered_stream"], "%s must name what the cue streams today" % entry["cue"]
            assert entry["registered_stream"] != entry["stream"], \
                "%s retired a stream that is still the cue's own" % entry["cue"]
        assert sorted(entry["cue"] for entry in retired) == ["PP-06"], \
            "the fixture's only pre-ledger stream is PP-06's percy_theme line"

    def test_the_plan_carries_no_host_path(self, tool, the_map):
        # The log lines hold D:\ paths from the machine that wrote them, and `line` keeps them verbatim
        # because it quotes the log. Every path the plan RESOLVES must be repo-relative: no other machine
        # has those paths, and the row that read one was red for exactly that.
        plan = tool.plan_log(SAMPLE_LOG, the_map)
        resolved = [{key: value for key, value in entry.items() if key != "line"} for entry in plan]
        text = json.dumps(resolved)
        assert not re.search(r"[A-Za-z]:[\\/]", text), "the plan resolves a host path: %s" % text[:400]
        for entry in plan:
            for key in ("file", "stream", "registered_stream"):
                value = entry.get(key)
                if value:
                    assert not os.path.isabs(str(value).replace("\\", "/")) and not re.match(r"[A-Za-z]:", str(value)), \
                        "%s resolves to the host path %r" % (key, value)

    def test_a_music_line_takes_the_bus_music_level(self, tool, the_map):
        plan = tool.plan_log(SAMPLE_LOG, the_map)
        music = [entry for entry in plan if entry["sound"] == "music_start"]
        assert music
        for entry in music:
            if entry["type"] == "theme_stream":
                assert entry["gain"] == 0.7, "the theme starts at the printed gain"
            else:
                assert entry["gain"] == 0.7, "a cue starts at the bus music level"

    def test_a_silent_line_stays_silent(self, tool, the_map):
        plan = tool.plan_log(SAMPLE_LOG, the_map)
        missing = [entry for entry in plan if entry["type"] == "music_missing"]
        assert missing, "the fixture should carry the pending-cue line"
        for entry in missing:
            assert entry["sound"] == "none"
            assert not entry.get("file")
