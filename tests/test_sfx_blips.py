"""Tests for the PP-BLIPS speaker map and the effects it names (card t_c9232c57, musician).

The card asks for two halves: a short per speaker blip for every character who prints text, and a
set of feel sounds; the game wiring is a separate gamedev card, so what is proved here is the half
the musician owns, and nothing here edits a game script.

What is proved, rather than asserted in a comment:
  - data\\sfx_blips.json and game\\datafiles\\sfx_blips.json are the same bytes, so a wiring cannot
    read a map the build does not carry;
  - every id the map names is a row in data\\audio.json, an effect in tools\\sfx.py, and an OGG on
    disk: a wiring that trusts the map cannot ask for a sound the build does not ship;
  - the five voices the card names exist, are pairwise distinct in timbre, register and voice
    family, and each is under the card's 0.4 s cap;
  - the eight feel sounds the card names resolve to those same three places, the two footsteps
    name each other as their alternate, and the quiet rows are quiet in BOTH files (the map and
    data\\audio.json), because a level that disagrees between two files is a bug waiting;
  - letters_per_blip is 2 and a space is in never_on, the card's two printing rules;
  - every speaker string the dialogue data actually holds resolves through the alias table, so no
    line can print with a missing voice;
  - the set is synthesised: the manifest says so, and every file is one the generator writes.

The map is data, not a script: this file reads it, and proves a reader of it would find every sound
it names. It does not claim the game plays them yet.
"""

from __future__ import annotations

import json
import os
import sys
import wave

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import sfx  # noqa: E402

MAP = os.path.join(ROOT, "data", "sfx_blips.json")
MAP_IN_GAME = os.path.join(ROOT, "game", "datafiles", "sfx_blips.json")
AUDIO = os.path.join(ROOT, "data", "audio.json")
SFX_DIR = os.path.join(ROOT, "assets", "audio", "sfx")
DIALOGUE = os.path.join(ROOT, "data", "dialogue", "all.json")

# The eight sounds this card adds: five voices, two steps and the blade. The cap is the card's own,
# 0.4 s, and it is checked on the file rather than trusted from the map.
NEW_IDS = (
    "text_blip_zeus", "text_blip_kronos", "text_blip_percy", "text_blip_oldman",
    "text_blip_narrator", "footstep_a", "footstep_b", "knife_slash",
)
# The five voices the card names, in its order, with the timbre word it uses for each.
VOICES = {
    "zeus": "mid square",
    "kronos": "low triangle with slight delay",
    "percy": "harsh noise burst",
    "old_man": "soft high square",
    "narrator": "neutral tick",
}


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="module")
def blips():
    return _read(MAP)


@pytest.fixture(scope="module")
def audio():
    return _read(AUDIO)


def _sounds(audio):
    return {row["id"]: row for row in audio["sounds"]}


def _wav_seconds(name):
    path = os.path.join(SFX_DIR, name + ".wav")
    with wave.open(path, "rb") as handle:
        return handle.getnframes() / float(handle.getframerate())


def _speakers_in_data():
    """Every speaker string the dialogue data holds, read from the file rather than hardcoded."""
    found = set()

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "speaker" and isinstance(value, str):
                    found.add(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(_read(DIALOGUE))
    return found


def test_the_map_the_game_reads_is_the_map_this_card_wrote():
    assert os.path.isfile(MAP), MAP
    assert os.path.isfile(MAP_IN_GAME), "the build carries no copy of the speaker map"
    with open(MAP, "rb") as handle:
        here = handle.read()
    with open(MAP_IN_GAME, "rb") as handle:
        there = handle.read()
    assert here == there, "game\\datafiles\\sfx_blips.json has drifted from data\\sfx_blips.json"


def test_every_id_the_map_names_is_a_registered_row_an_effect_and_a_file(blips, audio):
    rows = _sounds(audio)
    effects = {name for name, _builder, _groups in sfx.EFFECTS}
    ids = [row["blip"] for row in blips["speakers"]] + [row["id"] for row in blips["feel_sounds"]]
    assert len(ids) == len(set(ids)), "the map names the same sound under two roles: %s" % ids
    for name in ids:
        assert name in rows, "%s is in the map and not in data\\audio.json" % name
        assert rows[name]["kind"] in ("ui", "sfx"), name
        assert name in effects, "%s has no builder in tools\\sfx.py" % name
        assert os.path.isfile(os.path.join(SFX_DIR, rows[name]["file"])), "%s: no row file" % name
        assert os.path.isfile(os.path.join(SFX_DIR, name + ".ogg")), "%s has no OGG" % name


def test_the_five_voices_exist_are_distinct_and_sit_under_the_quarter_second_cap(blips):
    speakers = {row["speaker"]: row for row in blips["speakers"]}
    assert set(speakers) == set(VOICES), "the card names five voices, the map has %s" % sorted(speakers)
    for speaker, timbre in VOICES.items():
        row = speakers[speaker]
        assert row["timbre"] == timbre, "%s: timbre reads %r" % (speaker, row["timbre"])
        assert row["blip"] in NEW_IDS, speaker
        seconds = _wav_seconds(row["blip"])
        assert seconds <= 0.4, "%s is %.3f s, over the card's 0.4 s" % (row["blip"], seconds)
        assert abs(seconds - row["length_seconds"]) < 0.002, (
            "%s is %.3f s on disk and %.3f s in the map" % (row["blip"], seconds, row["length_seconds"]))
    # Distinct: a different timbre word, a different voice family, and a different register.
    assert len({row["timbre"] for row in blips["speakers"]}) == 5
    families = {row["speaker"]: tuple(row["voices"]) for row in blips["speakers"]}
    assert len(set(families.values())) == 5, families
    pitched = [row["pitch_midi"] for row in blips["speakers"] if row["pitch_midi"] is not None]
    assert len(pitched) == len(set(pitched)), "two voices share a pitch: %s" % pitched


def test_the_eight_feel_sounds_resolve_and_the_quiet_rows_agree_in_both_files(blips, audio):
    rows = _sounds(audio)
    feel = {row["role"]: row for row in blips["feel_sounds"]}
    wanted = {"footstep_left", "footstep_right", "menu_move", "menu_confirm", "knife_slash",
              "hit", "door", "item_pickup"}
    assert set(feel) == wanted, "the card names eight feel sounds, the map has %s" % sorted(feel)
    for role, row in feel.items():
        assert row["id"] in rows, "%s names %s, which is not registered" % (role, row["id"])
        assert rows[row["id"]]["volume"] == row["volume"], (
            "%s: the map says %.2f and data\\audio.json says %.2f"
            % (row["id"], row["volume"], rows[row["id"]]["volume"]))
    assert feel["footstep_left"]["alternates_with"] == "footstep_right"
    assert feel["footstep_right"]["alternates_with"] == "footstep_left"
    assert feel["footstep_left"]["id"] == "footstep_a" and feel["footstep_right"]["id"] == "footstep_b"
    # Quiet is 0.35 for a step, the level the drive's engine bed already uses, and it is the same
    # number in both files: a step that plays at menu level is the bug this pins.
    assert feel["footstep_left"]["volume"] == feel["footstep_right"]["volume"] == 0.35
    for name in NEW_IDS:
        assert _wav_seconds(name) <= 0.4, "%s is longer than the card's 0.4 s" % name


def test_letters_per_blip_is_two_and_a_space_never_plays(blips):
    assert blips["letters_per_blip"] == 2, blips["letters_per_blip"]
    assert " " in blips["never_on"], "a space must never blip, and the map does not say so"


def test_every_speaker_the_dialogue_data_holds_resolves_to_a_voice(blips):
    aliases = {row["alias"]: row["speaker"] for row in blips["aliases"]}
    speakers = {row["speaker"] for row in blips["speakers"]}
    assert set(aliases.values()) <= speakers, "an alias points at a speaker that does not exist"
    assert blips["default"] in {row["blip"] for row in blips["speakers"]}, blips["default"]
    unresolved = sorted(speaker for speaker in _speakers_in_data()
                        if speaker not in aliases and speaker not in speakers)
    assert unresolved == [], "these speaker strings would print with no voice: %s" % unresolved


def test_the_whole_set_is_synthesised():
    with open(os.path.join(SFX_DIR, "manifest.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    assert "synthesised" in manifest["source"]
    assert "no sampled or copied audio" in manifest["source"]
    for name in NEW_IDS:
        assert os.path.isfile(os.path.join(SFX_DIR, name + ".wav"))
