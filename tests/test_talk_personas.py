"""META-NPC-TALK: the live talk answers as three more characters, through the same bridge and the same rungs.

Card t_acae7c0a. The fight talk and the sailor's live box were cards W1 and W2; this file proves the three
persona scenes that follow them, and it proves them the way the rest of this suite does: from the files, with
no GameMaker run and no network.

Sources this file measures, never restates:

    data/talk_personas.json        the three cards: Konrad (S1), Urien (S2), the Town Quay bystander (S3)
    data/schemas/talk_personas.schema.json  the published shape check_data.py enforces
    data/talk/sailor_judge.json    the one system prompt, and the effects chat may move (none, end)
    data/talk_profanity.json       the guard's token list, the same one the fight talk uses
    data/talk_personas_bake.json   the recorded answers, written by tools/bake_personas.py
    data/ai_cache/bridge/          one file per recorded answer, what replay reads
    tools/ai_bridge.py             the door: build_task, answer_from_text, the ladder, the cache
    knowledge/SCENES-S1-S3.md      the voices the cards are written from

What is proven:

  1. the data: three personas, one per scene, fifteen bake lines each, a two sentence cap and one 6 s budget;
  2. the guards live on our side of the wire: banned words, banned marks and allowed moods are never sent to a
     model, and an answer carrying a banned word is refused rather than repaired;
  3. a persona answer is cut at two sentences, keeps its character (Konrad never shouts, the bystander never
     calms down) and is always drawable in two lines of 28;
  4. the ladder is the same ladder: a refused persona answer falls to the next rung, and every persona has a
     fallback line, so a scene answers with a dead bridge;
  5. the bake: fifteen rows per persona, calls_attempted above zero, every live row naming a cache file that
     holds the same words;
  6. replay with the network off answers all three personas from those rows, labelled replay with the origin
     of the rung that recorded them;
  7. the fight talk is untouched: the same payload that went down the fight path before still does, with four
     effects and three lines;
  8. the new files hold no long dash, no address and no key name, except on the line of a tool that defines
     the scan list whose job is to redact that key.

No test here makes a network call, writes a tracked file or needs a key.
"""

from __future__ import annotations

import json
import os
import re
import socket

import pytest

import ai_bridge
import bake_personas
import sync_data
import talk_guard

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSONAS = os.path.join(ROOT, "data", "talk_personas.json")
SCHEMA = os.path.join(ROOT, "data", "schemas", "talk_personas.schema.json")
REPORT = os.path.join(ROOT, "data", "talk_personas_bake.json")
CACHE = os.path.join(ROOT, "data", "ai_cache", "bridge")
SPEC_21 = os.path.join(ROOT, "specs", "21-live-talk.md")
SCENES = os.path.join(ROOT, "knowledge", "SCENES-S1-S3.md")

PERSONA_IDS = ("konrad", "urien", "quay_townsperson")
# The dock clerk answers inside the S5 cutscene (card t_330b12ce) so he carries a card like the three scene chats but
# no bake report block: the bake list is the three live chats, and adding him there would move a recorded report.
NYE_ID = "nye"
# Morgan at the quay gate answers inside the S4 cutscene (card t_21951674), the same way the clerk answers inside S5:
# his recorded turns are the npc/morgan rows of data/meta_bake.json, so he carries a card and no bake report block.
MORGAN_ID = "morgan"
ALL_IDS = PERSONA_IDS + (NYE_ID, MORGAN_ID)
# What the card asks for, in one place: three personas, fifteen answers each, two sentences, six seconds.
PER_PERSONA = 15
ANSWER_SENTENCES = 2
ANSWER_LINES = 2
ANSWER_CHARS = 28
BUDGET_S = 6.0
# The two environment names a report, a prompt or a cache file must never carry. Named here so the leak check
# has one list, and allowed on this line alone by the rule that check enforces on the tools.
KEY_NAMES = ("MODEL_API_KEY", "META_API_KEY")


def read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="module")
def doc():
    return read_json(PERSONAS)


@pytest.fixture(scope="module")
def rows(doc):
    return {str(row["id"]): row for row in doc["personas"]}


@pytest.fixture(scope="module")
def box(tmp_path_factory):
    """The door with a throwaway cache, so a test never writes a tracked file."""
    return ai_bridge.TalkJudge(cache=ai_bridge.Cache(str(tmp_path_factory.mktemp("persona-cache"))))


@pytest.fixture(scope="module")
def report():
    return read_json(REPORT)


def task_for(box, persona_id, line, **extra):
    payload = {"persona": persona_id, "player_text": line, "turn": 1, "mood": "guarded"}
    payload.update(extra)
    return ai_bridge.build_task(box.judge, box.cards, box.encounters, payload, personas=box.personas)


def answer(line, mood="warm", effect="none"):
    return json.dumps({"text": line if isinstance(line, list) else [line], "mood": mood,
                       "effect": effect, "hint": ""})


# ------------------------------------------------------------------ 1. the data


def test_the_data_is_the_published_shape(doc):
    """The schema check_data.py enforces is valid 2020-12 and the committed file passes it."""
    jsonschema = pytest.importorskip("jsonschema")
    schema = read_json(SCHEMA)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(doc)


def test_three_personas_one_per_scene(doc, rows):
    assert doc["kind"] == "talk_personas" and doc["format"] == 1
    assert tuple(sorted(rows)) == tuple(sorted(ALL_IDS)), "the file names the three scene chats and the dock clerk"
    assert [rows[pid]["scene"] for pid in PERSONA_IDS] == ["S1", "S2", "S3"], "one persona per scene, in order"
    places = [rows[pid]["place"] for pid in PERSONA_IDS]
    assert places == ["wessex_lane_montefiore", "southampton_high_street", "southampton_town_quay"], places
    # Card t_330b12ce: the clerk is the fourth card and stands in the dock office of the demo's S5, which the schema
    # allows for him alone (the S1 to S3 chats are the story beats from knowledge/SCENES-S1-S3.md).
    assert rows[NYE_ID]["scene"] == "S5" and rows[NYE_ID]["place"] == "quay_dock_office"
    assert rows[NYE_ID]["effects"] == ["none", "nudge", "soften", "setback"], (
        "a scene verdict has to be able to read persuaded, unmoved and angered, and the persona default is none/end")
    # Card t_21951674: Morgan is the fifth card, stands at the quay gate the demo's S4 shoots, and carries the same
    # widened effect list for the same reason: the box draws his verdict on the line, so all three words must be
    # reachable from a live answer. He is bake:false because bake_meta.py already baked his three npc turns.
    assert rows[MORGAN_ID]["scene"] == "S4" and rows[MORGAN_ID]["place"] == "southampton_town_quay"
    assert rows[MORGAN_ID]["bake"] is False, "Morgan's recorded turns are the npc/morgan rows, not a persona bake"
    assert rows[MORGAN_ID]["effects"] == ["none", "nudge", "soften", "setback"]
    assert "!" in rows[MORGAN_ID]["banned_marks"], "Morgan never raises his voice, which is a mark before a tone"


def test_every_persona_carries_the_answers_the_card_asks_for(rows):
    for pid in ALL_IDS:
        row = rows[pid]
        assert len(row["lines"]) >= PER_PERSONA, "%s carries fewer than %d bake lines" % (pid, PER_PERSONA)
        assert len(set(line.strip().lower() for line in row["lines"])) == len(row["lines"]), pid
        for line in row["lines"]:
            assert 1 <= len(line) <= 120, "%s: %r is outside the box's 120 characters" % (pid, line)
            assert all(32 <= ord(ch) < 127 for ch in line), "%s: %r is not printable ASCII" % (pid, line)
        assert len(row["fallback_pool"]) >= 3, "%s has no fourth rung" % pid


def test_the_answer_cap_and_the_budget_are_the_cards_numbers(doc):
    cap = doc["answer_cap"]
    assert (cap["sentences"], cap["lines"], cap["chars"]) == (ANSWER_SENTENCES, ANSWER_LINES, ANSWER_CHARS)
    assert doc["budget_s"] == int(BUDGET_S), "the persona talks share the fight talk's 6 second budget"
    assert ai_bridge.DEFAULT_TALK_TIMEOUT == BUDGET_S


def test_the_box_uses_the_budget_the_board_recorded(box, monkeypatch):
    """Demiurge decision 2026-10-27 (handoff t_3da6e753, recorded on the board): the whole request budget is 12 s when a
    Meta key is present and the 6 s default without one. tools/ai_bridge.py already says so; this pin follows it."""
    monkeypatch.delenv("PP_TALK_TIMEOUT", raising=False)
    assert ai_bridge.DEFAULT_TALK_TIMEOUT_KEY == 12.0
    assert ai_bridge.DEFAULT_TALK_TIMEOUT == BUDGET_S
    expected = ai_bridge.DEFAULT_TALK_TIMEOUT_KEY if ai_bridge.meta_key_present() else ai_bridge.DEFAULT_TALK_TIMEOUT
    assert box.budget == expected
    # The Meta rung may spend at most half the budget, so a persona turn can never be the slowest thing in a scene.
    assert box._share("meta", box.budget) <= box.budget - 0.6


def test_every_persona_names_the_shared_profanity_guard(doc):
    assert doc["profanity"] == "data/talk_profanity.json"
    assert len(talk_guard.load_tokens()) >= 20, "the guard's own floor, spec 19 section 7 layer D"


def test_the_persona_card_is_in_the_bundle_and_a_gml_module_names_it():
    """Card t_0fda85b8 wired the SAY IT YOURSELF box into the game, so the engine now reads the persona cards
    out of the bundle: pp_talk_persona.gml loads data/talk_personas.json for the name plate (the card's `name`
    field), which is why the file left NOT_RUNTIME. The earlier form of this test pinned the pre wiring state
    and failed on purpose the moment a GML module named the file; this form pins the wired state and fails the
    moment the file is silently dropped back out of the bundle or the reader is removed. The bake report stays
    out of the bundle for the same reason it always did."""
    assert "talk_personas.json" not in sync_data.NOT_RUNTIME, (
        "data/talk_personas.json left the bundle again: pp_talk_persona.gml reads it for the persona name plate")
    assert "talk_personas.json" in sync_data.source_files(), "sync_data no longer mirrors the persona cards"
    named = []
    for dirpath, _dirnames, filenames in os.walk(os.path.join(ROOT, "game")):
        for filename in filenames:
            if not filename.endswith(".gml"):
                continue
            with open(os.path.join(dirpath, filename), "r", encoding="utf-8-sig") as handle:
                if "talk_personas" in handle.read():
                    named.append(filename)
    assert named, (
        "no GML module reads the persona cards: the persona name plate has no source, so the file must not be mirrored")


def test_the_bake_report_is_not_in_the_bundle_either():
    """The report is a tool artifact: the game replays through the bridge's cache, never out of the bundle."""
    assert "talk_personas_bake.json" in sync_data.NOT_RUNTIME, (
        "the bake report is mirrored again: it is a tool report, not runtime data")
    assert "talk_personas_bake.json" not in sync_data.source_files(), "sync_data mirrors the bake report"


def test_the_voices_are_the_scenes_the_sheet_names(rows):
    """Each card is written from knowledge/SCENES-S1-S3.md, so the names and the places come from there."""
    with open(SCENES, "r", encoding="utf-8") as handle:
        sheet = handle.read()
    assert "Konrad (Kronos)" in sheet and "Urien, a jovial, unassuming old man (Ouranos)" in sheet
    assert "Town Quay" in sheet
    assert rows["konrad"]["name"] == "KONRAD"
    assert rows["urien"]["name"] == "URIEN"
    assert "kronos" in rows["konrad"]["aliases"], "the card names Kronos; the sheet adopted Konrad"
    for pid in PERSONA_IDS:
        assert rows[pid]["voice"] and len(rows[pid]["voice"]) <= 400


# ------------------------------------------------------------------ 2. the guards are ours, never the model's


def test_the_character_block_never_carries_a_ban(box, rows):
    """The prompt cannot leak what it never received, so no banned word, mark or mood list goes to a model."""
    for pid in PERSONA_IDS:
        task = task_for(box, pid, rows[pid]["lines"][0])
        block = task["messages"][1]["content"]
        character = json.loads(block.split("</character>")[0].replace("<character>", ""))
        for field in ("banned_words", "banned_marks", "mood_allowed"):
            assert field not in character, "%s sends %s to the model" % (pid, field)
        assert character["cannot_say"], "the lore limit still has to reach the model, as a category"
        for word in rows[pid]["banned_words"]:
            assert word not in block.upper(), "%s names the banned token %r in its own prompt" % (pid, word)
        assert task["guards"]["banned_words"] == tuple(rows[pid]["banned_words"])


def test_a_banned_word_refuses_the_whole_answer(box, rows):
    """Urien must never reveal who he is: a reply that says it is refused, not repaired."""
    task = task_for(box, "urien", "who are you")
    for text in ("I AM OURANOS.", "THE GODS ARE COMING.", "I WAS A TITAN."):
        with pytest.raises(ai_bridge.BadReply) as caught:
            ai_bridge.answer_from_text(answer([text]), box.judge, task)
        assert "persona_banned_word" in str(caught.value), text
    # A whole word match, so ordinary speech is not eaten: GOOD is not GOD.
    cleaned = ai_bridge.answer_from_text(answer(["GOOD RAIN. LOVELY."]), box.judge, task)
    assert cleaned["text"] == ["GOOD RAIN. LOVELY."]


def test_a_banned_word_falls_to_the_next_rung_rather_than_onto_the_screen(box, rows):
    """The ladder's own behaviour: a rung the guard refuses is labelled refused and the next one answers.

    The first rung is written the way the Meta rung is written, through answer_from_text, so the persona guard
    runs inside it and its BadReply is what the ladder catches. That is the live shape; a rung that returned a
    raw dict would skip the cleaning every real rung does.
    """
    calls = []

    def leaky(task, deadline):
        calls.append("meta")
        cleaned = ai_bridge.answer_from_text(answer(["I AM OURANOS."]), box.judge, task)
        return dict(cleaned, source="meta")

    def clean(task, deadline):
        calls.append("open-weights")
        cleaned = ai_bridge.answer_from_text(answer(["LOVELY RAIN."], mood="warm"), box.judge, task)
        return dict(cleaned, source="open-weights", origin="open-weights")

    ladder = ai_bridge.TalkJudge(cache=box.cache, sources=[("meta", leaky), ("open-weights", clean)])
    got = ladder.judge_talk({"persona": "urien", "player_text": rows["urien"]["lines"][0], "turn": 1})
    assert calls == ["meta", "open-weights"], "the refused rung has to hand the turn on"
    assert got["source"] == "open-weights", got
    assert got["reply"] == ["LOVELY RAIN."], got
    refused = [row for row in got["tried"] if row["rung"] == "meta"]
    assert refused and refused[0]["result"] == "refused", got["tried"]
    assert "persona_banned_word" in refused[0]["detail"], refused


def test_konrad_never_raises_his_voice(box, rows):
    """Polite and cutting is a punctuation rule before it is a tone rule."""
    task = task_for(box, "konrad", rows["konrad"]["lines"][-1])
    cleaned = ai_bridge.answer_from_text(answer(["AIM FOR A FIRST!", "USE THE DESK."], mood="calm"),
                                         box.judge, task)
    assert "!" not in " ".join(cleaned["text"]), cleaned
    assert cleaned["text"][0] == "AIM FOR A FIRST.", "a banned mark becomes a full stop, not a hole"
    assert "dropped_banned_mark" in cleaned["repaired"]


def test_an_answer_is_cut_at_two_sentences(box, rows):
    task = task_for(box, "urien", rows["urien"]["lines"][1])
    cleaned = ai_bridge.answer_from_text(
        answer(["LOVELY RAIN. TERRIBLE OVERHEADS.", "SO WAS MINE. TAKE TWO."], mood="warm"), box.judge, task)
    assert len(cleaned["text"]) <= ANSWER_LINES
    assert " ".join(cleaned["text"]).count(".") <= ANSWER_SENTENCES, cleaned
    assert "capped_sentences" in cleaned["repaired"], cleaned


def test_the_bystander_never_calms_down(box, rows):
    task = task_for(box, "quay_townsperson", rows["quay_townsperson"]["lines"][0])
    cleaned = ai_bridge.answer_from_text(answer(["IT IS ONLY WIND.", "DO NOT WORRY."], mood="calm"),
                                         box.judge, task)
    assert cleaned["mood"] == "rattled", "a calm bystander is out of character"
    assert "mood_mapped" in cleaned["repaired"]
    for mood in ("warm", "calm", "guarded"):
        cleaned = ai_bridge.answer_from_text(answer(["THE WIND HAS GONE MAD."], mood=mood), box.judge, task)
        assert cleaned["mood"] in ("rattled", "angry")


def test_an_out_of_scene_effect_is_refused(box, rows):
    """A chat moves no meter, so soften, nudge and setback are not effects a persona may pick."""
    task = task_for(box, "konrad", rows["konrad"]["lines"][0])
    assert task["allowed"] == ("none", "end")
    with pytest.raises(ai_bridge.BadReply):
        ai_bridge.answer_from_text(answer(["USE THE DESK."], effect="soften"), box.judge, task)


def test_the_shared_profanity_guard_still_runs_first(box, rows):
    """A persona card adds bans and never replaces the guard: a slur is refused whatever the card says."""
    tokens = talk_guard.load_tokens()
    word = sorted(tokens)[0]
    task = task_for(box, "quay_townsperson", rows["quay_townsperson"]["lines"][0])
    with pytest.raises(ai_bridge.BadReply) as caught:
        ai_bridge.answer_from_text(answer(["GET OFF THE QUAY, %s." % word.upper()]), box.judge, task)
    assert "profanity" in str(caught.value)


# ------------------------------------------------------------------ 3. the same door, the same ladder


def test_a_persona_is_a_chat_with_no_encounter(box, rows):
    """No fight id is needed: the persona names the place, the effects and the cap on its own."""
    task = task_for(box, "urien", rows["urien"]["lines"][0])
    scene = json.loads(task["messages"][1]["content"].split("<scene>")[1].split("</scene>")[0])
    assert scene["scene"] == "npc" and scene["npc"] == "urien"
    assert scene["place"] == "southampton_high_street"
    assert scene["allowed"] == ["none", "end"]
    assert task["schema"]["properties"]["text"]["maxItems"] == ANSWER_LINES
    assert task["limits"] == {"max_lines": ANSWER_LINES, "max_chars": ANSWER_CHARS}


def test_the_persona_reaches_the_door_three_ways(box, rows):
    """By its id, its alias, or by naming it as the npc, so a caller cannot silently fall back to a fight card."""
    line = "the bus is late again"
    by_id = task_for(box, "urien", line)
    by_alias = ai_bridge.build_task(box.judge, box.cards, box.encounters,
                                    {"persona": "old man", "player_text": line}, personas=box.personas)
    by_npc = ai_bridge.build_task(box.judge, box.cards, box.encounters,
                                  {"npc": "urien", "player_text": line}, personas=box.personas)
    assert by_id["key"] == by_alias["key"] == by_npc["key"], "the same request must be one cache key"
    assert by_id["persona"] == by_alias["persona"] == by_npc["persona"] == "urien"


def test_an_unknown_persona_is_refused_not_guessed(box):
    with pytest.raises(ai_bridge.ConfigError):
        ai_bridge.build_task(box.judge, box.cards, box.encounters,
                             {"persona": "had", "player_text": "hello"}, personas=box.personas)


def test_the_fight_path_is_unchanged(box):
    """The sailor fight keeps its four effects and three lines: a persona is an addition, not a rewrite."""
    task = ai_bridge.build_task(box.judge, box.cards, box.encounters,
                                {"npc": "navy_sailor", "player_text": "you have been on watch all night"})
    assert task["guards"] is None
    assert task["allowed"] == tuple(box.judge.effects) and "soften" in task["allowed"]
    assert task["limits"]["max_lines"] == box.judge.max_lines == 3
    assert task["scene"] == "fight" and task["persona"] == ""


def test_every_persona_answers_with_a_dead_bridge(box, rows, monkeypatch, tmp_path):
    """The fourth rung cannot fail: a persona scene answers with no key, no network and an empty cache.

    The network is shut inside the test and the cache folder is one this test owns. Measured on this PC
    2026-10-26: LM Studio answers on 127.0.0.1:51235, so the open weights rung is live whenever that server
    is, and a fixed folder inside data/ai_cache filled up with answers a timed out rung wrote after the
    ladder had already moved on. Both made this read a third rung answer while its docstring claimed the
    fourth. The socket guard is the same one test_replay_with_the_network_off_answers_all_three uses.
    """

    def no_socket(*args, **kwargs):
        raise AssertionError("the dead bridge test opened a socket")

    monkeypatch.setattr(socket, "socket", no_socket)
    monkeypatch.setattr(socket, "create_connection", no_socket)
    empty = ai_bridge.TalkJudge(cache=ai_bridge.Cache(str(tmp_path / "dead-bridge-cache")))
    for pid in PERSONA_IDS:
        answer_doc = empty.judge_talk({"persona": pid, "player_text": rows[pid]["lines"][0]})
        assert answer_doc["source"] == "fallback", pid
        assert answer_doc["reply"], pid
        assert all(len(line) <= ANSWER_CHARS for line in answer_doc["reply"]), answer_doc["reply"]


# ------------------------------------------------------------------ 4. the bake, and replay with the network off


def test_the_bake_was_a_live_bake_of_the_whole_set(report):
    """The card's check: the bake rows say calls_attempted greater than 0, and every persona is covered."""
    block = report["bake"]
    assert block["calls_attempted"] > 0, block
    assert block["mode"] == "live", block
    assert block["network"] is True
    assert block["model"] == "muse-spark-1.3", block
    assert block["answered"] >= len(PERSONA_IDS) * PER_PERSONA, block
    per = {row["id"]: row for row in report["coverage"]["per_persona"]}
    assert sorted(per) == sorted(PERSONA_IDS)
    for pid in PERSONA_IDS:
        assert per[pid]["rows"] == PER_PERSONA, per[pid]
        assert per[pid]["answered"] == PER_PERSONA, per[pid]
        assert per[pid]["calls_attempted"] > 0, per[pid]


def test_every_live_row_names_a_cache_file_that_holds_its_words(report):
    """A report cannot promise a replay the commit cannot serve."""
    live = [row for row in report["rows"] if row["transport"] == "live"]
    assert live, "no live row, so replay would answer from the fallback pool"
    for row in live:
        path = os.path.join(CACHE, "%s.json" % row["cache_key"])
        assert os.path.isfile(path), "%s has no cache file" % row["cache_key"]
        entry = read_json(path)
        assert entry["answer"]["text"] == row["text"], row["line"]
        assert entry["source"] == "meta" and entry["network"] is True
        assert entry["model"] == "muse-spark-1.3"


def test_no_recorded_answer_breaks_character(report, rows):
    """The card's must-not: no persona answer carries its own ban, a slash word, or more than two lines."""
    tokens = talk_guard.load_tokens()
    for row in report["rows"]:
        if not row["text"]:
            continue
        persona = rows[row["persona"]]
        assert len(row["text"]) <= ANSWER_LINES, row
        for line in row["text"]:
            assert len(line) <= ANSWER_CHARS, row
            assert line.isascii() and line.upper() == line, row
        hit = ai_bridge.banned_hit(row["text"], {"banned_words": tuple(persona["banned_words"])})
        assert not hit, "%s said %r in %r" % (row["persona"], hit, row["text"])
        assert not talk_guard.profane_hit(" ".join(row["text"]).lower(), tokens), row
        assert row["mood"] in persona["mood_allowed"], row
        for mark in persona["banned_marks"]:
            assert mark not in " ".join(row["text"]), row


def test_the_report_passes_its_own_check():
    assert bake_personas.check_file(REPORT) == 0


def test_the_check_can_fail(tmp_path, report, rows):
    """A check that cannot fail is a document. Two mutations, each refused."""
    broken = json.loads(json.dumps(report))
    for row in broken["rows"]:
        if row["text"]:
            row["text"] = ["I AM OURANOS."]
            break
    path = tmp_path / "report.json"
    path.write_text(json.dumps(broken), encoding="utf-8")
    assert bake_personas.check_file(str(path)) > 0, "a banned word has to be refused by --check"

    dropped = json.loads(json.dumps(report))
    dropped["rows"] = [row for row in dropped["rows"] if row["persona"] != "urien"]
    path.write_text(json.dumps(dropped), encoding="utf-8")
    assert bake_personas.check_file(str(path)) > 0, "a persona with no rows has to be refused"


def test_replay_with_the_network_off_answers_all_three(monkeypatch, report, rows):
    """The card's check: a replay run with the network off answers all three personas, from recorded rows."""
    monkeypatch.setenv("PP_AI_MODE", "replay")

    def no_socket(*args, **kwargs):
        raise AssertionError("replay opened a socket")

    monkeypatch.setattr(socket, "socket", no_socket)
    monkeypatch.setattr(socket, "create_connection", no_socket)
    box = ai_bridge.TalkJudge()
    assert [name for name, _rung in box.rungs()] == ["cache", "fallback"], "replay starts at the cache rung"
    for pid in PERSONA_IDS:
        row = next(row for row in report["rows"] if row["persona"] == pid and row["text"])
        got = box.judge_talk({"persona": pid, "player_text": row["line"], "turn": 1, "mood": "guarded"})
        assert got["source"] == "replay", got
        assert got["origin"] == "meta", got
        assert got["cached"] is True
        assert got["reply"] == row["text"], (pid, got["reply"], row["text"])


def test_replay_says_replay_and_never_reaches_a_model(report, rows, monkeypatch):
    """A line nobody recorded still answers, labelled fallback, and still opens nothing."""
    monkeypatch.setenv("PP_AI_MODE", "replay")
    box = ai_bridge.TalkJudge()
    got = box.judge_talk({"persona": "konrad", "player_text": "a line nobody recorded today", "turn": 1})
    assert got["source"] == "fallback", got
    assert got["reply"], "the fourth rung has to say something"


# ------------------------------------------------------------------ 5. the writing rules


def test_the_new_files_hold_no_long_dash_and_no_secret():
    """A key name may sit on the line that defines a scan list, and nowhere else in a file this card adds.

    The absolute version of this test refused `KEY_ENVS` in tools/ai_bridge.py, whose whole job there is to
    redact any key value that reaches a log or a cache file, so it has to name what it looks for. The rule is
    therefore split the way the risk actually splits: the data files this card adds hold no key name at all,
    and a tool may name one only on the line defining the scan list that exists to redact it. A key name in a
    docstring, a prompt, a report line or a log line still fails, which is the case worth catching.
    """
    dash_paths = (PERSONAS, SCHEMA, REPORT, os.path.join(ROOT, "tools", "bake_personas.py"),
                  os.path.join(ROOT, "tools", "ai_bridge.py"), os.path.abspath(__file__))
    data_paths = (PERSONAS, SCHEMA, REPORT)
    scan_list_markers = ("KEY_ENVS", "KEY_NAMES")
    for path in dash_paths:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        assert "\u2014" not in text and "\u2013" not in text, "%s holds a long dash" % os.path.basename(path)
        # An address may be the loopback bridge or the schema id this project cites, and nothing else: the card's
        # must-not is that player text goes nowhere but the Meta API (whose base is meta_client's own default) and
        # the local bridge, so a hardcoded third party endpoint is what this refuses.
        for match in re.finditer(r"https?://[^\s\"'<>)]*", text):
            url = match.group(0)
            host = url.split("//", 1)[1].split("/", 1)[0].split(":")[0]
            if url.startswith("https://json-schema.org/draft/2020-12/schema"):
                continue
            # The schema's own $id is a name, not an endpoint: primordial-paradox.local is the project's own
            # reserved namespace and does not resolve, so it can never be called.
            if host == "primordial-paradox.local":
                continue
            assert host in ("127.0.0.1", "localhost", "[::1]", "::1"), \
                "%s holds a URL that is not the loopback bridge: %s" % (os.path.basename(path), url)
        for number, line in enumerate(text.splitlines(), 1):
            for name in KEY_NAMES:
                if name not in line:
                    continue
                assert path not in data_paths, "%s names a key environment variable" % os.path.basename(path)
                assert any(marker in line for marker in scan_list_markers), (
                    "%s:%d names the key variable %s outside the scan list that exists to redact it"
                    % (os.path.basename(path), number, name))


def test_the_spec_names_the_three_personas():
    with open(SPEC_21, "r", encoding="utf-8") as handle:
        spec = handle.read()
    assert "## 11. Personas" in spec, "spec 21 owns the live talk and has to own the personas"
    for pid in ("konrad", "urien", "quay_townsperson"):
        assert "data/talk_personas.json" in spec
        assert pid in spec, "%s is missing from the spec" % pid
