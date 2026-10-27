"""tests for tools/ai_bridge.py (card W1 PP-BRIDGE).

What these tests are for, so a later reader does not weaken them:
  * every rung of the ladder, and the order it is tried in, because the card's whole promise is that a talk
    turn always gets an answer and the answer says where it came from;
  * the deadline, because a stalled model is the failure mode the budget exists for;
  * the box's two hard limits, 3 lines of 28 characters, because a reply outside them cannot be drawn;
  * the cache label, because PP_AI_MODE=replay is only honest if a replayed answer says it was replayed;
  * the loopback bind and the "no key in a body" rule, which are the two "must not" lines of the card.

No test here touches a network, a model or the real cache directory: the ladder takes injected rungs, the
cache is a tmp_path, and the HTTP tests bind an ephemeral loopback port.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import socket
import threading
import time
from urllib import request as urlrequest

import pytest

import ai_bridge

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "specs", "19-llm-talk.md")


# ------------------------------------------------------------------ fixtures and helpers

@pytest.fixture()
def cache_dir(tmp_path, monkeypatch):
    folder = str(tmp_path / "bridge_cache")
    monkeypatch.setenv("PP_BRIDGE_CACHE", folder)
    return folder


@pytest.fixture()
def judge():
    return ai_bridge.Judge()


@pytest.fixture()
def talk(cache_dir, judge, monkeypatch):
    monkeypatch.delenv("PP_LOCAL_MODEL", raising=False)
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    monkeypatch.delenv("META_API_KEY", raising=False)
    monkeypatch.setenv("PP_AI_MODE", "record")
    # Isolate the open-weights bake too, so a committed data/ai_bake_open/replies.json never changes what
    # these tests assert about the recorded-cache and fallback rungs.
    monkeypatch.setenv("PP_BAKE_FILE", os.path.join(os.path.dirname(cache_dir), "no_bake.json"))
    return ai_bridge.TalkJudge(cache=ai_bridge.Cache(cache_dir), judge=judge)


def rung(effect="soften", text=("GO ON THEN.",), mood="calm", **extra):
    """A rung that always answers. Fed into TalkJudge(sources=[...]) so no model is needed."""
    def call(task, deadline):
        answer = {"effect": effect, "text": list(text), "mood": mood}
        answer.update(extra)
        return answer
    return call


def unavailable(reason="not here"):
    def call(task, deadline):
        raise ai_bridge.SourceUnavailable(reason)
    return call


def slow(seconds=2.0):
    def call(task, deadline):
        time.sleep(seconds)
        return {"effect": "soften", "text": ["TOO LATE."], "mood": "calm"}
    return call


def seed_answer(talk, payload, source="meta", text=("THE HATCH IS THAT WAY.",), effect="soften"):
    task = ai_bridge.build_task(talk.judge, talk.cards, talk.encounters, payload)
    talk.cache.write(task["key"], "talk", source,
                     {"effect": effect, "text": list(text), "mood": "calm"}, task, model="test")
    return task


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class StubHearer:
    """A /hear that answers without faster-whisper, so the HTTP tests stay fast and offline."""

    model = "stub"
    interpreter = "stub"
    _last_error = ""

    def __init__(self, transcript="GO ON THEN"):
        self.transcript = transcript

    def transcribe(self, wav):
        if not (wav[:4] == b"RIFF" and wav[8:12] == b"WAVE"):
            raise ai_bridge.BadRequest("the body is not a wav file (no RIFF/WAVE header)")
        return self.transcript, "stub", False, 1

    def stop(self):
        return None


def post(port, path, body, content_type="application/json"):
    data = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
    req = urlrequest.Request("http://127.0.0.1:%d%s" % (port, path), data=data,
                             headers={"Content-Type": content_type})
    try:
        with urlrequest.urlopen(req, timeout=20) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urlrequest.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8") or "{}")


# ------------------------------------------------------------------ the prompt is one file, checked against the spec

def test_the_judge_prompt_is_the_spec_block_verbatim(judge):
    with open(SPEC, encoding="utf-8") as handle:
        spec = handle.read()
    start = spec.index("You are the voice of PRIMORDIAL PARADOX")
    end = spec.index("Return only the JSON object.", start) + len("Return only the JSON object.")
    assert judge.system == spec[start:end], (
        "data/talk/sailor_judge.json's system text has drifted from specs/19-llm-talk.md section 3: the "
        "prompt must have one home, and the data file is a verified copy of it")


def test_the_judge_file_carries_the_verdict_rows_the_bridge_needs(judge):
    for effect, delta in (("soften", 20), ("nudge", 5), ("none", 0), ("setback", -10)):
        verdict, value = judge.verdict_for(effect)
        assert value == delta
        assert verdict in ai_bridge.VERDICTS
    assert "spare" not in judge.verdicts, "an effect named spare must never be a thing the model can pick"


def test_the_judge_limits_are_three_lines_of_28(judge):
    assert judge.max_lines == 3
    assert judge.max_chars == 28


# ------------------------------------------------------------------ the ladder

def test_the_ladder_order_and_the_replay_shortcut(talk, monkeypatch):
    assert [name for name, _ in talk.rungs()] == ["meta", "open-weights", "cache", "fallback"]
    monkeypatch.setenv("PP_AI_MODE", "replay")
    assert [name for name, _ in talk.rungs()] == ["cache", "fallback"], (
        "PP_AI_MODE=replay must never call a model: the demo plays offline")


def test_meta_answers_first_and_its_effect_sets_the_will_delta(talk):
    talk._injected = [("meta", rung(effect="soften", text=("GO ON THEN.", "BRIDGE IS THAT WAY.")))]
    answer = talk.judge_talk({"player_text": "you have been on watch all night"})
    assert answer["source"] == "meta"
    assert answer["verdict"] == "persuaded"
    assert answer["will_delta"] == 20
    assert answer["reply"] == ["GO ON THEN.", "BRIDGE IS THAT WAY."]


def test_the_local_model_answers_when_meta_cannot(talk):
    talk._injected = [("meta", unavailable("no key")),
                      ("open-weights", rung(effect="none", text=("THE LIST DOES NOT CARE.",)))]
    answer = talk.judge_talk({"player_text": "please let me pass"})
    assert answer["source"] == "open-weights"
    assert answer["verdict"] == "unmoved"
    assert answer["will_delta"] == 0
    assert answer["tried"][0] == {"rung": "meta", "result": "unavailable", "detail": "no key"}


class _StubResponse:
    """urlopen's response, stood in for, so a request body can be read without a model server."""

    def __init__(self, body):
        self._body = body.encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def capture_local_request(monkeypatch, content=None):
    """Patch the local rung's HTTP call and hand back the JSON body it was about to send."""
    seen = {}
    reply = content or json.dumps({"text": ["GO ON THEN."], "mood": "calm", "effect": "soften", "hint": ""})
    answer = json.dumps({"choices": [{"message": {"content": reply}}]})

    def fake_urlopen(request, timeout=None):
        seen["payload"] = json.loads(request.data.decode("utf-8"))
        return _StubResponse(answer)

    monkeypatch.setattr(ai_bridge.urlrequest, "urlopen", fake_urlopen)
    return seen


def test_documentation_keys_are_told_apart_from_request_fields():
    for key in ("note", "NOTE", "comments", "doc", "why", "_note", "  ", ""):
        assert ai_bridge.is_request_field(key) is False, "%r is documentation, not a request field" % key
    for key in ("max_tokens", "temperature", "top_p", "stop", "seed", "repeat_penalty"):
        assert ai_bridge.is_request_field(key) is True, "%r is a real request field" % key


def test_a_note_in_local_request_is_never_sent_to_the_model_server(talk, monkeypatch):
    """LM Studio answers HTTP 400 to an unknown field, so documentation in the judge file must not reach the body.

    Measured on this PC 2026-10-26: the judge file carried a plain "note" inside local_request, it was merged into
    the request, and the open weights rung read as broken (HTTP 400) while the endpoint answered a clean body in
    22 s. The tunable beside it must still be merged, which is what the second assertion holds.
    """
    talk.judge.local_request = {"max_tokens": 99, "note": "a note", "_note": "another", "comment": "a third"}
    seen = capture_local_request(monkeypatch)
    task = ai_bridge.build_task(talk.judge, talk.cards, talk.encounters,
                               {"player_text": "please let me pass"})
    answer = talk._rung_local(task, time.monotonic() + 6.0)
    payload = seen["payload"]
    for key in ("note", "_note", "comment"):
        assert key not in payload, "%r is documentation and must not be sent to the model server" % key
    assert payload["max_tokens"] == 99, "a real tunable in local_request must still be merged"
    assert set(payload) == {"model", "messages", "temperature", "max_tokens", "stream"}, (
        "the local body carries only fields the OpenAI compatible schema defines")
    assert answer["source"] == "open-weights"


def test_a_decided_effect_is_the_only_thing_that_moves_the_bar(talk):
    talk._injected = [("meta", rung(effect="setback", text=("SAY THAT AGAIN.",)))]
    answer = talk.judge_talk({"player_text": "you are a useless old man"})
    assert (answer["verdict"], answer["will_delta"]) == ("angered", -10)


def test_a_recorded_answer_comes_back_labelled_replay_with_its_origin(talk, monkeypatch):
    payload = {"player_text": "the bridge will hear about this"}
    seed_answer(talk, payload, source="meta")
    monkeypatch.setenv("PP_LOCAL_URL", "http://127.0.0.1:%d/v1" % free_port())
    talk._injected = [("meta", unavailable("no key")), ("open-weights", unavailable("no endpoint")),
                      ("cache", talk._rung_cache), ("fallback", talk._rung_fallback)]
    answer = talk.judge_talk(payload)
    assert answer["source"] == "replay", "a cached answer must say replay, not the rung that recorded it"
    assert answer["origin"] == "meta"
    assert answer["cached"] is True
    assert answer["reply"] == ["THE HATCH IS THAT WAY."]
    assert answer["verdict"] == "persuaded"


def test_the_fallback_answers_when_everything_else_fails_and_says_so(talk, monkeypatch):
    monkeypatch.setenv("PP_LOCAL_URL", "http://127.0.0.1:%d/v1" % free_port())
    talk._injected = [("meta", unavailable("no key")), ("open-weights", unavailable("no endpoint")),
                      ("cache", talk._rung_cache), ("fallback", talk._rung_fallback)]
    answer = talk.judge_talk({"player_text": "something nobody recorded"})
    assert answer["source"] == "fallback"
    assert answer["verdict"] == "unmoved"
    assert answer["will_delta"] == 0
    assert answer["reply"], "the fallback must never answer with an empty box"
    assert all(len(line) <= 28 for line in answer["reply"])


def test_a_rung_that_overruns_the_budget_is_abandoned(talk):
    talk.budget = 0.3
    talk._injected = [("meta", slow(2.0)), ("fallback", talk._rung_fallback)]
    started = time.monotonic()
    answer = talk.judge_talk({"player_text": "a line that makes the model hang"})
    elapsed = time.monotonic() - started
    assert answer["source"] == "fallback"
    assert elapsed < 1.2, "a 0.3 s budget must not wait 2 s for a stalled rung (took %.2f s)" % elapsed
    assert answer["tried"][0]["result"] == "timeout"


def test_a_spent_budget_still_ends_in_an_answer_not_an_exception(talk):
    """Measured 2026-10-26 on this PC: with a 6 s budget, a cold local model spent its whole share, the loop
    then skipped the file rungs as no_budget, and judge_talk raised BridgeError, so a player's turn got no
    answer at all. The card's promise is that a turn always answers, so the fallback must run even with the
    clock gone: it reads one file and wraps one line."""
    talk.budget = 0.0
    talk._injected = [("open-weights", rung(effect="soften", text=("NEVER REACHED.",))),
                      ("cache", talk._rung_cache), ("fallback", talk._rung_fallback)]
    started = time.monotonic()
    answer = talk.judge_talk({"player_text": "a line nobody recorded"})
    assert time.monotonic() - started < 1.0, "a file rung must not wait on a budget that is already gone"
    assert answer["source"] == "fallback"
    assert answer["reply"]
    assert answer["tried"][0] == {"rung": "open-weights", "result": "no_budget"}, (
        "a model rung with no budget left must say so instead of being called")


def test_a_refused_reply_falls_to_the_next_rung(talk):
    def refuses(task, deadline):
        raise ai_bridge.BadReply("refusal_phrase:as an ai")
    talk._injected = [("meta", refuses), ("open-weights", rung(effect="nudge", text=("FAIR ENOUGH.",)))]
    answer = talk.judge_talk({"player_text": "hello sailor"})
    assert answer["source"] == "open-weights"
    assert answer["will_delta"] == 5
    assert answer["tried"][0]["result"] == "refused"


def test_an_unknown_encounter_is_a_bad_request_not_a_guess(talk):
    with pytest.raises(ai_bridge.BadRequest):
        talk.judge_talk({"encounter_id": "not_a_room", "player_text": "hello"})
    with pytest.raises(ai_bridge.BadRequest):
        talk.judge_talk({"player_text": "   "})


def test_the_encounter_row_supplies_the_card_and_the_fallback(talk):
    task = ai_bridge.build_task(talk.judge, talk.cards, talk.encounters,
                                {"encounter_id": "deck_hound", "player_text": "easy now"})
    assert task["npc"] == "deck_hound"
    assert task["fallback_pool"], "the hound's fallback pool must be read from data/encounters/all.json"


# ------------------------------------------------------------------ the box's limits

def test_a_line_over_28_is_cut_at_a_space_never_mid_word():
    lines, repairs = ai_bridge.clean_lines(["THE WATCH IS LONG AND THE NIGHT IS LONG TOO"],
                                          3, 28, "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,:!?'()")
    assert len(lines) == 1
    assert len(lines[0]) <= 28
    assert lines[0].split()[-1] in "THE WATCH IS LONG AND THE NIGHT IS LONG TOO".split()
    assert "truncated" in repairs


def test_more_lines_than_the_box_holds_are_dropped():
    lines, repairs = ai_bridge.clean_lines(["ONE.", "TWO.", "THREE.", "FOUR."], 3, 28,
                                          "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,:!?'()")
    assert lines == ["ONE.", "TWO.", "THREE."]
    assert "dropped_extra_lines" in repairs


def test_lowercase_and_undrawable_characters_are_repaired_not_shipped():
    lines, repairs = ai_bridge.clean_lines(["go on *then* _now_"], 3, 28,
                                          "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,:!?'()")
    assert lines == ["GO ON THEN NOW"]
    assert "uppercased" in repairs and "dropped_chars" in repairs


def test_the_narration_marker_the_model_must_not_write_is_stripped():
    lines, repairs = ai_bridge.clean_lines(["* IT LETS YOU NEAR THE ROPE."], 3, 28,
                                          "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,:!?'()")
    assert lines == ["IT LETS YOU NEAR THE ROPE."]
    assert "dropped_narration_marker" in repairs


def test_a_reply_the_box_cannot_hold_is_refused_not_emptied():
    with pytest.raises(ai_bridge.BadReply):
        ai_bridge.clean_lines(["***"], 3, 28, "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,:!?'()")


def test_a_model_answer_that_mixes_quote_styles_is_repaired_not_refused(judge, talk):
    """Measured 2026-10-26 on this PC: microsoft_phi-4-mini-instruct answered a judge task with its first
    array item in double quotes and the next two in single quotes, which strict JSON refuses and which is
    otherwise a usable answer. The repair must keep the strings and the effect, not invent either."""
    task = ai_bridge.build_task(judge, talk.cards, talk.encounters,
                                {"player_text": "the captain is a fool and you know it"})
    body = ('{"text":["I DON\'T CARE FOR FOOLS. TRY", \'THE BRIDGE NEEDS ME.\', \'ORDERS ARE ORDERS.\'], '
            '"mood":"guarded","effect":"soften","hint":"TRY THE WATCH"}')
    answer = ai_bridge.answer_from_text(body, judge, task)
    assert answer["text"] == ["I DON'T CARE FOR FOOLS. TRY", "THE BRIDGE NEEDS ME.", "ORDERS ARE ORDERS."]
    assert answer["effect"] == "soften"
    assert answer["mood"] == "guarded"


def test_text_that_is_no_object_even_as_a_python_literal_is_still_refused():
    for bad in ("the sailor shrugs and says nothing", "{text: GO ON THEN}", "{\"text\": "):
        with pytest.raises(ai_bridge.BadReply):
            ai_bridge.parse_json_object(bad)


def test_a_refusal_phrase_or_a_link_or_a_digit_run_is_refused(judge, talk):
    payload = {"player_text": "hello sailor"}
    task = ai_bridge.build_task(judge, talk.cards, talk.encounters, payload)
    for bad in ('{"text": ["AS AN AI I CANNOT"]}', '{"text": ["SEE WWW.EXAMPLE.COM"]}',
                '{"text": ["LINE 123"]}'):
        with pytest.raises(ai_bridge.BadReply):
            ai_bridge.answer_from_text(bad, judge, task)


def test_a_profanity_token_refuses_the_whole_reply(judge, talk):
    guard = pytest.importorskip("talk_guard")
    tokens = guard.load_tokens()
    word = max(tokens, key=len)
    payload = {"player_text": "hello sailor"}
    task = ai_bridge.build_task(judge, talk.cards, talk.encounters, payload)
    body = json.dumps({"text": ["YOU %s." % word.upper()], "mood": "angry",
                       "effect": "setback", "hint": ""})
    with pytest.raises(ai_bridge.BadReply):
        ai_bridge.answer_from_text(body, judge, task)


def test_the_schema_is_built_from_the_judge_file_and_refuses_a_bad_answer(judge, talk):
    task = ai_bridge.build_task(judge, talk.cards, talk.encounters, {"player_text": "hello sailor"})
    schema = task["schema"]
    assert schema["properties"]["text"]["maxItems"] == judge.max_lines
    assert schema["properties"]["text"]["items"]["maxLength"] == judge.max_chars
    assert schema["properties"]["effect"]["enum"] == list(judge.effects)
    assert schema["additionalProperties"] is False

    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.Draft202012Validator.check_schema(schema)
    good = {"text": ["GO ON THEN."], "mood": "calm", "effect": "soften", "hint": "THE WATCH"}
    jsonschema.validate(good, schema)
    for bad in ({"text": ["lower case"], "mood": "calm", "effect": "soften", "hint": ""},
                {"text": ["X" * 29], "mood": "calm", "effect": "soften", "hint": ""},
                {"text": ["OK."], "mood": "calm", "effect": "spare", "hint": ""},
                {"text": ["OK."], "mood": "calm", "effect": "soften", "hint": "", "extra": 1}):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(bad, schema)


def test_the_fallback_line_is_wrapped_not_cut(talk):
    task = ai_bridge.build_task(talk.judge, talk.cards, talk.encounters,
                                {"encounter_id": "tutorial_sailors", "player_text": "hello"})
    answer = talk._rung_fallback(task, time.monotonic() + 5)
    assert all(len(line) <= 28 for line in answer["text"])
    assert answer["text"] != ["THE WATCH IS LONG. THAT IS"], (
        "wrapping must keep the end of the line, not truncate it away")


def test_a_cut_never_leaves_a_dangling_article_at_the_end_of_a_line(judge):
    # Measured on a real cache entry: the model wrote a 32 character line, the cut at the last space before 28
    # characters left "I DON'T CARE IF IT'S A", and the box drew a line ending on "A".
    lines, repairs = ai_bridge.clean_lines(["I DON'T CARE IF IT'S A STOWAWAY"], 3, 28, judge.alphabet)
    assert lines == ["I DON'T CARE IF IT'S"]
    assert "truncated" in repairs
    assert all(len(line) <= 28 for line in lines)


def test_a_complete_line_keeps_its_last_word_even_when_that_word_is_short(judge):
    lines, repairs = ai_bridge.clean_lines(["SMOKE. I'LL GET YOU ONE."], 3, 28, judge.alphabet)
    assert lines == ["SMOKE. I'LL GET YOU ONE."]
    assert repairs == []


# ------------------------------------------------------------------ the cache

def test_the_cache_entry_is_labelled_with_its_source_and_kind(cache_dir, talk):
    payload = {"player_text": "a line worth recording"}
    task = seed_answer(talk, payload, source="meta")
    entry = json.load(open(os.path.join(cache_dir, task["key"] + ".json"), encoding="utf-8"))
    assert entry["kind"] == "talk"
    assert entry["source"] == "meta"
    assert entry["network"] is False
    assert entry["answer"]["text"] == ["THE HATCH IS THAT WAY."]
    assert "player_text" not in json.dumps(entry["request"]), (
        "the cache must not keep the player's words, only a digest of them")


def test_a_key_in_the_environment_never_reaches_a_body_or_a_cache_file(cache_dir, talk, monkeypatch):
    # Not shaped like a real vendor key on purpose: the repo's staged leak scan flags anything that is, and this
    # test only needs a value that would be obvious if it escaped.
    secret = "pp-test-value-0123456789abcdef"
    monkeypatch.setenv("MODEL_API_KEY", secret)

    def leaks(task, deadline):
        raise ai_bridge.SourceUnavailable("the server said no to %s" % secret)

    talk._injected = [("meta", leaks), ("fallback", talk._rung_fallback)]
    answer = talk.judge_talk({"player_text": "hello sailor"})
    assert secret not in json.dumps(answer)
    for name in os.listdir(cache_dir) if os.path.isdir(cache_dir) else []:
        with open(os.path.join(cache_dir, name), encoding="utf-8") as handle:
            assert secret not in handle.read()


# ------------------------------------------------------------------ the door

@pytest.fixture()
def server(talk):
    talk._injected = [("meta", rung(effect="soften", text=("GO ON THEN.", "BRIDGE IS THAT WAY.")))]
    hearer = StubHearer()
    srv = ai_bridge.serve(talk, hearer, port=0)
    thread = threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    try:
        yield srv
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=5)


def test_the_door_binds_loopback_only(server):
    assert server.server_address[0] == "127.0.0.1"


def test_health_and_talk_over_http(server):
    port = server.server_address[1]
    with urlrequest.urlopen("http://127.0.0.1:%d/health" % port, timeout=10) as response:
        health = json.loads(response.read().decode("utf-8"))
    assert health["ok"] is True
    assert health["judge"]["max_lines"] == 3
    assert health["bind"].startswith("127.0.0.1:")

    status, answer = post(port, "/talk", {"player_text": "you have been on watch all night"})
    assert status == 200
    assert answer["source"] == "meta"
    assert answer["will_delta"] == 20
    assert answer["reply"] == ["GO ON THEN.", "BRIDGE IS THAT WAY."]


def test_a_bad_body_is_a_400_and_a_bad_route_a_404(server):
    port = server.server_address[1]
    assert post(port, "/talk", b"not json")[0] == 400
    assert post(port, "/talk", {"player_text": ""})[0] == 400
    assert post(port, "/nope", {})[0] == 404


def test_a_non_loopback_bind_is_refused(talk, monkeypatch):
    monkeypatch.setenv("PP_BRIDGE_HOST", "0.0.0.0")
    with pytest.raises(ai_bridge.ConfigError):
        ai_bridge.serve(talk, StubHearer(), port=0)


def test_hear_answers_with_a_transcript(server):
    port = server.server_address[1]
    wav = b"RIFF" + b"\x00\x00\x00\x00" + b"WAVE" + b"fmt " + b"\x00" * 40
    status, answer = post(port, "/hear", wav, content_type="audio/wav")
    assert status == 200
    assert answer["transcript"] == "GO ON THEN"
    assert answer["source"] == "whisper"


def test_hear_refuses_a_body_that_is_not_a_wav(server):
    status, answer = post(server.server_address[1], "/hear", b"hello", content_type="audio/wav")
    assert status == 400


def test_hear_is_unavailable_rather_than_silent_when_no_interpreter_has_whisper(monkeypatch, cache_dir):
    hearer = ai_bridge.Hearer(cache=ai_bridge.Cache(cache_dir), interpreter="")
    monkeypatch.setenv("PP_WHISPER_PYTHON", "")
    monkeypatch.setattr(hearer, "find_interpreter", lambda: "")
    wav = b"RIFF" + b"\x00\x00\x00\x00" + b"WAVE" + b"\x00" * 32
    with pytest.raises(ai_bridge.SourceUnavailable) as error:
        hearer.transcribe(wav)
    assert "faster_whisper" in str(error.value)


def test_a_recorded_transcript_is_served_from_the_cache_without_a_worker(cache_dir):
    hearer = ai_bridge.Hearer(cache=ai_bridge.Cache(cache_dir), interpreter="")
    wav = b"RIFF" + b"\x00\x00\x00\x00" + b"WAVE" + b"\x00" * 32
    key = hashlib.sha256(str(base64.b64encode(wav)).encode("utf-8")).hexdigest()
    ai_bridge.Cache(cache_dir).write(key, "hear", "whisper", {"transcript": "THE WATCH IS LONG."},
                                     {"kind": "hear"}, model="tiny")
    transcript, model, cached, ms = hearer.transcribe(wav)
    assert transcript == "THE WATCH IS LONG."
    assert cached is True
    assert model == "tiny"
    hearer.stop()


# ------------------------------------------------------------------ must not

def test_the_local_endpoint_must_be_on_this_machine(talk, monkeypatch):
    monkeypatch.setenv("PP_LOCAL_URL", "http://192.0.2.10:51235/v1")
    task = ai_bridge.build_task(talk.judge, talk.cards, talk.encounters, {"player_text": "hello"})
    with pytest.raises(ai_bridge.SourceUnavailable) as error:
        talk._rung_local(task, time.monotonic() + 5)
    assert "loopback" in str(error.value)


def test_nothing_in_the_module_binds_a_wide_address():
    with open(os.path.join(ROOT, "tools", "ai_bridge.py"), encoding="utf-8") as handle:
        text = handle.read()
    assert "0.0.0.0" not in text.replace("0.0.0.0 must", ""), (
        "ai_bridge must bind 127.0.0.1 only; a wildcard address would expose the door to the network")
    assert re.search(r"LOOPBACK_HOST = \"127\.0\.0\.1\"", text)


def test_the_meta_rung_restores_the_timeout_knobs_it_borrows(talk, monkeypatch):
    """The door shortens the client's HTTP timeout for one talk turn; it must give the old values back."""
    monkeypatch.setenv("PP_META_TIMEOUT", "99")
    monkeypatch.setenv("PP_META_MAX_RETRIES", "7")
    seen = {}

    class FakeMeta:
        KEY_ENVS = ("MODEL_API_KEY", "META_API_KEY")

        @staticmethod
        def backend_name():
            return "meta"

        @staticmethod
        def key_present():
            return True

        @staticmethod
        def model_for(role="chat"):
            return "muse-spark-1.3"

        @staticmethod
        def chat(messages, json_schema=None, transport=None):
            seen["timeout"] = os.environ.get("PP_META_TIMEOUT")
            seen["retries"] = os.environ.get("PP_META_MAX_RETRIES")
            raise RuntimeError("the server refused the call")

    import sys
    monkeypatch.setitem(sys.modules, "meta_client", FakeMeta)
    task = ai_bridge.build_task(talk.judge, talk.cards, talk.encounters, {"player_text": "hello"})
    with pytest.raises(ai_bridge.SourceUnavailable):
        talk._rung_meta(task, time.monotonic() + 5)
    assert seen["timeout"] not in (None, "99"), "the meta call must run under the talk budget, not 99 s"
    assert seen["retries"] == "0", "a talk turn may not retry three times inside one budget"
    assert os.environ["PP_META_TIMEOUT"] == "99"
    assert os.environ["PP_META_MAX_RETRIES"] == "7"


# ------------------------------------------------------------------ the selftest shows its rungs

def test_the_ladder_report_uses_a_line_the_cache_can_answer(talk):
    """A report that cannot reach the replay rung is not a check of the replay rung.

    Measured on this PC 2026-10-26: --selftest printed `cache unavailable: no recorded answer for this line`
    while data/ai_cache/bridge held 91 answers, because the line it always asked about was recorded under an
    earlier judge version and the key had moved. The report now picks a line the cache answers.
    """
    payload = {"encounter_id": "tutorial_sailors", "npc": "navy_sailor",
               "player_text": ai_bridge.SELFTEST_LINES[2]}
    seed_answer(talk, payload, source="open-weights", text=("MOVE ALONG.",), effect="setback")
    assert ai_bridge._selftest_line(talk) == ai_bridge.SELFTEST_LINES[2]

    rows = {row["rung"]: row for row in ai_bridge._ladder_report(talk, talk.cache,
                                                                line=ai_bridge.SELFTEST_LINES[2])}
    assert rows["cache"]["result"] == "answered"
    assert rows["fallback"]["result"] == "answered", "the last rung must answer even when a file rung did"


def test_the_ladder_report_falls_back_to_the_first_line_when_nothing_is_recorded(talk):
    """An empty cache has to report a full ladder rather than fail on its own line choice."""
    assert ai_bridge._selftest_line(talk) == ai_bridge.SELFTEST_LINES[0]
    rows = ai_bridge._ladder_report(talk, talk.cache)
    assert [row["rung"] for row in rows] == ["meta", "open-weights", "cache", "fallback"]


def test_the_selftest_warms_the_local_model_before_it_runs_the_ladder(talk, monkeypatch, capsys):
    """A cold model is why the local rung reads `unavailable` on a healthy machine; the run must load it first.

    Measured on this PC 2026-10-26: an unloaded model took 11 to 85 s for the first call, and while the load
    was aborted LM Studio answered 400, which the 5.6 s rung share cannot outlast. Here warm_local is replaced
    and the ladder is injected, so the test stays offline.
    """
    monkeypatch.delenv("PP_AI_MODE", raising=False)
    calls = []

    def fake_warm(budget=120.0):
        calls.append(budget)
        return {"model": "test-model", "url": "http://127.0.0.1:51235/v1", "ms": 12}

    line = ai_bridge.SELFTEST_LINES[0]
    seed_answer(talk, {"encounter_id": "tutorial_sailors", "npc": "navy_sailor", "player_text": line})
    talk._injected = [("cache", talk._rung_cache), ("fallback", talk._rung_fallback)]
    monkeypatch.setattr(talk, "warm_local", fake_warm)
    code = ai_bridge.selftest(talk=talk, wav_path="")
    out = capsys.readouterr().out
    assert calls, "the selftest never warmed the local model"
    assert "WARM UP" in out and "test-model loaded in 12 ms" in out
    assert "source=replay" in out, "the injected ladder answered from the recording, so the run is not a failure"
    assert code == 0


def test_a_replay_selftest_does_not_touch_the_model(talk, monkeypatch, capsys):
    """PP_AI_MODE=replay is the offline demo path: it must not warm or wait on a model server."""
    monkeypatch.setenv("PP_AI_MODE", "replay")

    def refuse(budget=120.0):
        raise AssertionError("replay mode must not load a model")

    monkeypatch.setattr(talk, "warm_local", refuse)
    code = ai_bridge.selftest(talk=talk, wav_path="")
    assert "WARM UP" not in capsys.readouterr().out
    assert code in (0, 1), "replay with an empty cache answers from the encounter fallback, which is a failure"


# ------------------------------------------------------------------ the open-weights bake (card t_354f4e8a)

def test_classify_intent_uses_the_cards_own_keywords():
    sailor = ai_bridge.load_cards()["navy_sailor"]
    assert ai_bridge.classify_intent(sailor, "you look wrecked") == "weak"
    assert ai_bridge.classify_intent(sailor, "the bridge will hear about this") == "strong"
    assert ai_bridge.classify_intent(sailor, "nothing much to say") == "neutral"
    # A short keyword must not fire inside a longer word: "sea" is a weak keyword for navy_sailor, but
    # "season" is a different word.
    assert ai_bridge.classify_intent(sailor, "the season is changing") == "neutral"


def test_a_baked_reply_serves_offline_when_meta_and_cache_miss(cache_dir, judge, monkeypatch, tmp_path):
    """The bake is the offline rung's second source: Meta and the recorded cache both miss, the bake answers."""
    bake_file = tmp_path / "bake.json"
    bake_file.write_text(json.dumps({
        "format": 1,
        "kind": "bake_open",
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "cards": {
            "navy_sailor": {
                "neutral": [{"text": ["STATE YOUR BUSINESS."], "mood": "guarded", "effect": "none"}],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setenv("PP_BAKE_FILE", str(bake_file))
    monkeypatch.setenv("PP_AI_MODE", "record")
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    monkeypatch.delenv("META_API_KEY", raising=False)
    monkeypatch.delenv("PP_LOCAL_MODEL", raising=False)
    talk = ai_bridge.TalkJudge(cache=ai_bridge.Cache(cache_dir), judge=judge)
    talk._injected = [("meta", unavailable("no key")), ("open-weights", unavailable("no endpoint")),
                      ("cache", talk._rung_cache), ("fallback", talk._rung_fallback)]
    answer = talk.judge_talk({"player_text": "nothing much to say"})
    assert answer["source"] == "replay"
    assert answer["origin"] == "bake", "a baked reply must say it came from the bake, not a live recording"
    assert answer["cached"] is True
    assert answer["reply"] == ["STATE YOUR BUSINESS."]
    assert answer["model"] == "Qwen/Qwen2.5-7B-Instruct"


def test_a_recorded_cache_answer_still_wins_over_the_bake(talk, monkeypatch, tmp_path):
    """An exact-line recorded answer is served before any bake lookup, so the ladder order is unchanged."""
    bake_file = tmp_path / "bake.json"
    bake_file.write_text(json.dumps({
        "cards": {"navy_sailor": {"neutral": [{"text": ["BAKED LINE."], "mood": "guarded",
                                               "effect": "none"}]}},
    }), encoding="utf-8")
    monkeypatch.setenv("PP_BAKE_FILE", str(bake_file))
    payload = {"player_text": "nothing much to say"}
    seed_answer(talk, payload, source="meta", text=("RECORDED LINE.",), effect="soften")
    talk._injected = [("meta", unavailable("no key")), ("open-weights", unavailable("no endpoint")),
                      ("cache", talk._rung_cache), ("fallback", talk._rung_fallback)]
    answer = talk.judge_talk(payload)
    assert answer["origin"] == "meta", "the recorded exact-line answer must beat the bake"
    assert answer["reply"] == ["RECORDED LINE."]


