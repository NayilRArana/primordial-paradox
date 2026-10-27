"""ai_bridge: the local service the game asks for a live talk verdict, and for a transcript (card W1 PP-BRIDGE).

What this is, in one paragraph. The talk fight needs a reply that answers what the player actually said, now,
in character. Two things make that possible on one PC: a model call behind a small HTTP door, and a fallback
ladder so the scene never stalls. This module is that door: it listens on 127.0.0.1 only, takes a player line,
and answers with a verdict, a WILL delta and at most three NES text lines, labelled with where the answer came
from. tools/run.ps1 starts it before the game and stops it after. Nothing here is reachable off this machine,
and nothing here sends audio off it.

Endpoints
    POST /talk   JSON in, JSON out. See "The talk request" and "The talk answer" below.
    POST /hear   raw wav bytes in (16000 Hz, mono, 16 bit PCM), JSON out: {"transcript": "..."}.
    GET  /health what the ladder and the transcriber are doing right now, without spending a call.
    GET  /       the same as /health, so a browser probe is not a 404.

The talk request
    {"encounter_id": "tutorial_sailors", "npc": "navy_sailor", "player_text": "you have been on watch all night",
     "history": [{"player_text": "...", "reply": ["..."], "verdict": "unmoved"}],
     "will": 20, "mood": "guarded"}
    Only player_text is required. encounter_id defaults to tutorial_sailors (the beat 28 talk fight) and npc
    defaults to that encounter's card, read from data/encounters/all.json rather than typed here. history is
    optional and is used for the turn number, the last reply and the last effect only; per spec 19 section 3
    the player's earlier typed lines are NOT put in the prompt, and neither is hp, the item list, a save, a
    flag, a file path or a key.

The talk answer
    {"verdict": "persuaded" | "unmoved" | "angered",
     "will_delta": -10 | 0 | 5 | 20,
     "reply": ["GO ON THEN.", "BRIDGE IS THAT WAY."],
     "source": "meta" | "open-weights" | "replay" | "fallback",
     "mood": "guarded",
     "cached": false,
     "latency_ms": 412,
     "origin": "open-weights"}

    verdict and will_delta come from the effect the model picked, through the map in
    data/talk/sailor_judge.json: soften -> persuaded +20, nudge -> persuaded +5, none -> unmoved 0, setback ->
    angered -10. The model never sends a number; the map, which the talk director owns, decides what the WILL
    bar moves by.

    source is where THIS answer came from. "replay" means a recorded answer was served out of the cache, and
    then origin says which rung recorded it. "fallback" is the fourth rung, and it is a deliberate, labelled
    addition to the three the card lists: the game must always get an answer, so when the two live rungs and
    the cache all miss, the encounter's own fallback line answers and says so instead of pretending a model
    spoke.

The ladder, in the order it is tried
    1. meta           tools/meta_client.py, Muse Spark, structured output against the schema built from the
                      judge file. Skipped without a call when no key is present, when PP_AI_BACKEND=mock, or
                      when PP_AI_MODE=replay; each skip is labelled, never silent.
    2. open-weights   an OpenAI compatible endpoint, LM Studio by default at 127.0.0.1:51235, model from
                      PP_LOCAL_MODEL. The endpoint must be loopback; anything else is refused before a byte is
                      sent, because the text must not leave this PC.
    3. replay         this line's recorded answer from data/ai_cache/bridge/, labelled with the rung that
                      recorded it. PP_AI_MODE=replay starts at this rung, which is what plays the demo offline.
    4. fallback       data/encounters/all.json's talk.fallback_pool, uppercased and fitted to the box. This is
                      the only rung that cannot fail.

    Every rung runs under one deadline, PP_TALK_TIMEOUT seconds for the whole request (default 6). A rung that
    runs past its share is abandoned and the next one answers; the late thread is a daemon and dies with the
    process. The measured table is in docs/AI-BRIDGE.md.

The judge prompt is a data file
    data/talk/sailor_judge.json holds the system text, the limits, the verdict map and the encounter aliases.
    The talk director owns it; this module only reads it. tests/test_ai_bridge.py pins the system text to the
    fenced block in specs/19-llm-talk.md, so the prompt has one home and the data file is a verified copy.

What is cleaned before an answer leaves this module
    The reply is uppercased, filtered to the 46 glyph alphabet the font actually has, cut at a space to the
    line limit, capped at the line count, and stripped of a leading "* " (code adds that marker, the model
    never writes it). A reply carrying a token from data/talk_profanity.json, a refusal phrase from the judge
    file, a link, an "@", or a run of three digits is refused and the next rung answers. Every repair is
    labelled in the answer's "repaired" list; a refused rung is labelled in "tried".

Caching
    data/ai_cache/bridge/<sha256>.json, one file per (judge version, system text, character block, scene block,
    player line). Fields: key, kind, source (the rung that produced it), network, created_at, model, and the
    answer itself. It sits in a subdirectory of the Meta client's cache folder on purpose: that folder is
    already excluded from the game bundle by tools/sync_data.py, and its flat level is counted as Meta calls by
    tools/make_architecture_diagram.py, which bridge entries are not.

Voice
    POST /hear takes 16000 Hz mono 16 bit PCM wav bytes and returns the transcript from faster-whisper's tiny
    model, which is already in the HuggingFace cache on this PC. The interpreter that runs this server does not
    need the package: faster-whisper lives under a different Python on this machine, so the bridge finds one
    interpreter that can import it (PP_WHISPER_PYTHON first, then this interpreter, then py -3.11) and keeps a
    small worker process alive so the model loads once (tools/whisper_worker.py). Audio is passed as bytes to
    that local child process and nothing else: no socket leaves the machine, and a wav the transcriber refuses
    is a 400, never a silent empty transcript. Transcripts are cached too, keyed on the wav's sha256.

Environment, read at call time, never at import
    PP_BRIDGE_HOST       default 127.0.0.1, and any other value is refused at startup
    PP_BRIDGE_PORT       default 8791
    PP_TALK_TIMEOUT      seconds for a whole /talk request, default 6
    PP_TALK_MAX_LINES    optional override of the judge file's line count
    PP_AI_MODE           record (default) | replay | live, handed to tools/meta_client.py
    PP_AI_BACKEND        meta (default) | gemini | mock, handed to tools/meta_client.py
    PP_LOCAL_URL         default http://127.0.0.1:51235/v1, must be loopback
    PP_LOCAL_MODEL       the open weights model id; when unset, the first id LM Studio lists is used
    PP_LOCAL_TIMEOUT     optional cap in seconds for the local call
    PP_WHISPER_PYTHON    an interpreter that can import faster_whisper
    PP_WHISPER_MODEL     default tiny
    PP_BRIDGE_CACHE      cache directory override, used by the tests
    the Meta key        read by tools/meta_client.py only; never printed, logged, cached or echoed

Usage
    python tools\\ai_bridge.py --serve                 # what tools\\run.ps1 starts
    python tools\\ai_bridge.py --selftest              # every rung, printed, one line each
    python tools\\ai_bridge.py --latency               # the 10 line measured table
    python tools\\ai_bridge.py --once "a line"         # one call, printed, no server

Status, 2026-10-26, stated plainly. The three live rungs and the fallback were exercised on this PC: the local
rung answered through LM Studio, and the Meta rung is labelled "no key" here because this machine holds no
Meta key, which the card calls a valid labelled fallback. The replay rung and the fallback rung are exercised
by the tests. /hear was exercised against a real speech wav made on this PC with the Windows voice, and the
timings are the ones in docs/AI-BRIDGE.md.
"""

from __future__ import annotations

import argparse
import ast
import atexit
import base64
import hashlib
import json
import os
import re
import sys
import threading
import time
import unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request as urlrequest
from urllib.parse import urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
JUDGE_FILE = os.path.join(DATA, "talk", "sailor_judge.json")
CARDS_FILE = os.path.join(DATA, "talk_cards.json")
PERSONAS_FILE = os.path.join(DATA, "talk_personas.json")
ENCOUNTERS_FILE = os.path.join(DATA, "encounters", "all.json")
DEFAULT_CACHE = os.path.join(DATA, "ai_cache", "bridge")
# The baked open-weights replies (card t_354f4e8a), keyed by talk card then player intent. This is a second
# source for the replay rung: when a player line was never recorded to the exact-line cache, and the bake holds
# an accepted reply for the card and the intent the line's keywords classify as, the replay rung serves that
# instead of dropping straight to the encounter's own fallback line. Read lazily, so a machine with no bake
# behaves exactly as before.
DEFAULT_BAKE = os.path.join(DATA, "ai_bake_open", "replies.json")

LOOPBACK_HOST = "127.0.0.1"
DEFAULT_PORT = 8791
DEFAULT_TALK_TIMEOUT = 6.0
DEFAULT_LOCAL_URL = "http://127.0.0.1:51235/v1"
DEFAULT_WHISPER_MODEL = "tiny"
SAMPLE_RATE = 16000
KEY_ENVS = ("MODEL_API_KEY", "META_API_KEY", "GEMINI_API_KEY")
VERDICTS = ("persuaded", "unmoved", "angered")
SOURCES = ("meta", "open-weights", "replay", "fallback")
# The two rungs that read a file instead of calling a model. They cost about a millisecond, so they keep a
# floor share and are never skipped for want of budget: the fallback is the rung that cannot fail.
FILE_RUNGS = ("cache", "fallback")
FILE_RUNG_SHARE = 1.0


# ------------------------------------------------------------------ errors and small helpers

class BridgeError(RuntimeError):
    """Base class for every refusal this module makes."""


class ConfigError(BridgeError):
    """The judge file, the cards or the encounter row is missing or unusable."""


class BadRequest(BridgeError):
    """The caller sent something this door does not accept."""


class SourceUnavailable(BridgeError):
    """One rung cannot answer right now, with a reason worth labelling."""


class SourceTimeout(BridgeError):
    """One rung ran past its share of the budget."""


class BadReply(BridgeError):
    """A rung answered, but not in the shape the game can draw."""


def redact(text):
    """Every string that can reach a log, a cache file or an HTTP body goes through here first.

    tools/meta_client.py already redacts its own errors; this is the belt beside that brace, because a key
    this process can see must never appear in a file this process writes, whatever produced the string.
    """
    out = str(text)
    for name in KEY_ENVS:
        value = (os.environ.get(name) or "").strip()
        if len(value) >= 6 and value in out:
            out = out.replace(value, "[redacted %s]" % name)
    return out


def env(name, default=""):
    return (os.environ.get(name, "") or "").strip() or default


def env_float(name, default):
    try:
        return float(env(name, str(default)))
    except (TypeError, ValueError):
        return float(default)


def env_int(name, default):
    try:
        return int(env(name, str(default)))
    except (TypeError, ValueError):
        return int(default)


def read_json(path):
    if not os.path.isfile(path):
        raise ConfigError("missing file: %s" % os.path.relpath(path, ROOT))
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except ValueError as exc:
        raise ConfigError("%s is not valid JSON: %s" % (os.path.relpath(path, ROOT), exc))


def sha256_text(text):
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def utc_stamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def is_loopback(url):
    """True when this URL can only reach this machine. Anything else is refused before a call is made."""
    parsed = urlsplit(str(url))
    host = (parsed.hostname or "").lower()
    return host in ("127.0.0.1", "localhost", "::1", "0:0:0:0:0:0:0:1")


def char_class(alphabet):
    """A regex character class body for the font's alphabet, built from the data file's own string."""
    return "".join("\\" + ch if ch in "\\]^-[$.*+?(){}|" else ch for ch in alphabet)


NOT_A_REQUEST_FIELD = frozenset(("note", "notes", "comment", "comments", "doc", "documentation", "why"))


def is_request_field(key):
    """True when a key from the judge file's local_request belongs in an OpenAI compatible request body.

    local_request is data the talk director owns, so a note written beside its tunable values is normal. Sending
    that note to the model server is not: measured on this PC 2026-10-26, LM Studio answers HTTP 400 to an unknown
    field, and the open weights rung then reads as broken while the endpoint itself is healthy. A leading
    underscore, or one of the documentation names above, keeps the note in the file and out of the body.
    """
    name = str(key).strip()
    if not name or name[0] == "_":
        return False
    return name.lower() not in NOT_A_REQUEST_FIELD


# ------------------------------------------------------------------ the judge file, cards, encounters

class Judge:
    """The data the director owns, validated once, read by every rung."""

    def __init__(self, path=None, root=None):
        self.root = root or ROOT
        self.path = path or os.path.join(self.root, "data", "talk", "sailor_judge.json")
        doc = read_json(self.path)
        if not isinstance(doc, dict):
            raise ConfigError("the judge file is not a JSON object")
        self.doc = doc
        self.version = int(doc.get("version") or 0)
        self.system = str(doc.get("system") or "").strip()
        if len(self.system) < 200:
            raise ConfigError("the judge file's system text is missing or too short to be the prompt")
        # The open weights variant, if the file carries one. A 2 to 4 billion parameter model running on this
        # PC's CPU cannot prefill the full 2408 character prompt inside a talk budget (measured: 20 to 27 s for
        # a warm phi-4-mini), and it does not need the Meta provider's prefix-caching wording to produce the
        # same four fields. The local rung uses this text when it exists; Meta always gets the full system text.
        self.system_local = str(doc.get("system_local") or "").strip()
        self.local_request = doc.get("local_request") if isinstance(doc.get("local_request"), dict) else {}
        limits = doc.get("limits") or {}
        self.max_lines = int(limits.get("max_lines") or 3)
        self.max_chars = int(limits.get("max_chars") or 28)
        self.max_player_chars = int(limits.get("max_player_chars") or 120)
        self.max_history_turns = int(limits.get("max_history_turns") or 6)
        self.alphabet = str(doc.get("alphabet") or "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,:!?'()")
        self.effects = tuple(doc.get("effects") or ("none", "nudge", "soften", "setback"))
        self.effects_npc = tuple(doc.get("effects_npc") or ("none", "end"))
        verdicts = doc.get("verdicts") or {}
        for effect in set(self.effects) | set(self.effects_npc):
            row = verdicts.get(effect)
            if not isinstance(row, dict) or row.get("verdict") not in VERDICTS:
                raise ConfigError("the judge file has no usable verdict row for effect %r" % effect)
            if not isinstance(row.get("will_delta"), int):
                raise ConfigError("the judge file's verdict row for %r has no integer will_delta" % effect)
        self.verdicts = verdicts
        self.refuse_phrases = tuple(str(p).lower() for p in (doc.get("refuse_phrases") or ()))
        self.encounters = doc.get("encounters") or {}
        self.moods = tuple(doc.get("moods") or ("calm", "guarded", "rattled", "warm", "angry"))

    def verdict_for(self, effect):
        row = self.verdicts[effect]
        return row["verdict"], int(row["will_delta"])

    def schema(self, allowed_effects, max_lines=None):
        """The JSON schema the API enforces, built from this file's own limits rather than typed twice.

        max_lines is the request's own line cap: a persona card caps its answer at two lines, so the schema
        and the cleaner must agree on the number or the model is asked for something the box will cut.
        """
        alphabet = self.alphabet
        pattern = "^[%s]+$" % char_class(alphabet)
        lines_cap = int(max_lines if max_lines is not None else self.max_lines)
        return {
            "type": "object",
            "required": ["text", "mood", "effect", "hint"],
            "additionalProperties": False,
            "properties": {
                "text": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": lines_cap,
                    "items": {"type": "string", "minLength": 1, "maxLength": self.max_chars,
                              "pattern": pattern},
                },
                "mood": {"enum": list(self.moods)},
                "effect": {"enum": list(allowed_effects)},
                "hint": {"type": "string", "maxLength": self.max_chars},
            },
        }


def load_cards(root=None):
    root = root or ROOT
    doc = read_json(os.path.join(root, "data", "talk_cards.json"))
    cards = doc.get("cards") if isinstance(doc, dict) else None
    if not isinstance(cards, list):
        raise ConfigError("data/talk_cards.json has no cards array")
    return {str(card.get("id")): card for card in cards if isinstance(card, dict)}


def load_personas(root=None):
    """data/talk_personas.json, indexed by id and by alias (card t_acae7c0a, spec 21 section 11).

    The three cards that stand outside a fight: Konrad in S1, Urien in S2 and one panicking townsperson on
    Town Quay in S3. A missing file is not an error at import time, because the fight talk does not need it:
    the persona rung is only reached by a request that names one, and that request is refused with a named
    ConfigError. Loading it here rather than in build_task keeps the file read once per process.
    """
    root = root or ROOT
    path = os.path.join(root, "data", "talk_personas.json")
    if not os.path.isfile(path):
        return {}
    doc = read_json(path)
    rows = doc.get("personas") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        raise ConfigError("data/talk_personas.json has no personas array")
    out = {}
    cap = doc.get("answer_cap") if isinstance(doc.get("answer_cap"), dict) else {}
    for row in rows:
        if not isinstance(row, dict) or not row.get("id"):
            continue
        row = dict(row)
        row.setdefault("answer_cap", cap)
        out[str(row["id"])] = row
        for alias in row.get("aliases") or []:
            out[str(alias)] = row
    return out


def persona_block(persona, cap):
    """The character block for a persona: the six fields spec 19 section 3 sends, plus the lore limits.

    The bans are NOT here. `banned_words`, `banned_marks` and `mood_allowed` are guards the bridge applies to
    the answer, and a prompt that lists the word it must not say is a prompt that puts the word in the model's
    mouth. `cannot_say` carries the same rule as a category instead: "any name for a god or a titan" tells the
    model what to avoid without naming a single token.
    """
    block = {
        "id": persona.get("id"),
        "name": persona.get("name") or str(persona.get("id") or "").replace("_", " ").upper(),
        "role": persona.get("role", ""),
        "place": persona.get("place", ""),
        "voice": persona.get("voice", ""),
        "wants": list(persona.get("wants") or []),
        "fears": list(persona.get("fears") or []),
        "weak_topics": [{"topic": t.get("topic")} for t in (persona.get("weak_topics") or [])
                        if isinstance(t, dict) and t.get("topic")],
        "strong_topics": [{"topic": t.get("topic")} for t in (persona.get("strong_topics") or [])
                          if isinstance(t, dict) and t.get("topic")],
        "knows": list(persona.get("knows") or []),
        "cannot_say": list(persona.get("cannot_say") or []),
        "answer": "at most %d short sentences, at most %d box lines of %d characters"
                  % (int(cap.get("sentences") or 2), int(cap.get("lines") or 2), int(cap.get("chars") or 28)),
    }
    return block


def load_encounters(root=None):
    root = root or ROOT
    doc = read_json(os.path.join(root, "data", "encounters", "all.json"))
    rows = doc.get("encounters") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        raise ConfigError("data/encounters/all.json has no encounters array")
    return {str(row.get("id")): row for row in rows if isinstance(row, dict)}


def load_bake(root=None, path=None):
    """The baked open-weights replies, keyed by card then intent, plus the bake's model.

    Returns {"model": "...", "cards": {card_id: {intent: [entry, ...]}}}, or an empty cards dict when the
    bake file is missing or unusable. A missing bake is not an error, because the offline rung must behave
    exactly as before on a machine that has not run the bake (card t_354f4e8a). PP_BAKE_FILE overrides the
    path, which is what the tests use to isolate it.
    """
    root = root or ROOT
    if path is None:
        path = env("PP_BAKE_FILE", DEFAULT_BAKE)
    if not os.path.isfile(path):
        return {"model": "", "cards": {}}
    try:
        doc = read_json(path)
    except ConfigError:
        return {"model": "", "cards": {}}
    rows = doc.get("cards") if isinstance(doc, dict) else None
    out = {}
    if isinstance(rows, dict):
        for card_id, intents in rows.items():
            if not isinstance(intents, dict):
                continue
            bucket = {}
            for intent, entries in intents.items():
                if isinstance(entries, list):
                    kept = [e for e in entries if isinstance(e, dict) and e.get("text")]
                    if kept:
                        bucket[str(intent)] = kept
            if bucket:
                out[str(card_id)] = bucket
    return {"model": str(doc.get("model") or "") if isinstance(doc, dict) else "", "cards": out}


def classify_intent(card, player_text):
    """weak / strong / neutral, from the card's own topic keywords (data/talk_cards.json).

    The bake is keyed by intent, so the offline rung needs a deterministic classifier to pick which bucket a
    player line belongs in. Weak topics land first (a soft spot the character names), then strong topics
    (a subject the character guards), and anything else is neutral. A whole-word match keeps a short keyword
    like "end" from firing inside "weekend"; the card's keywords are data, never instructions.
    """
    text = " %s " % str(player_text or "").lower()
    for pool in ("weak_topics", "strong_topics"):
        for topic in card.get(pool) or []:
            for keyword in topic.get("keywords") or []:
                keyword = str(keyword).strip().lower()
                if keyword and re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(keyword), text):
                    return "weak" if pool == "weak_topics" else "strong"
    return "neutral"


def character_block(card, name=None):
    """The character block of spec 19 section 3: only the fields that are sent, nothing invented."""
    block = {
        "id": card.get("id"),
        "name": name or card.get("name") or str(card.get("id") or "").replace("_", " ").title(),
        "voice": card.get("voice", ""),
        "wants": list(card.get("wants") or []),
        "fears": list(card.get("fears") or []),
        "weak_topics": [{"topic": t.get("topic")} for t in (card.get("weak_topics") or [])
                        if isinstance(t, dict) and t.get("topic")],
        "strong_topics": [{"topic": t.get("topic")} for t in (card.get("strong_topics") or [])
                          if isinstance(t, dict) and t.get("topic")],
        "phase_note": card.get("phase_note", ""),
    }
    return block


def normalise_player_text(text, limit=120):
    """NFKC, one line, printable ASCII, and cut to the limit. Data, never an instruction."""
    if text is None:
        return ""
    cleaned = unicodedata.normalize("NFKC", str(text))
    cleaned = "".join(ch if 32 <= ord(ch) < 127 else " " for ch in cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:limit].strip()


def scene_block(judge, encounter, npc, scene, turn, mood, last_effect, last_reply, allowed, will, place=None):
    """The scene block of spec 19 section 3: bands and counts, never hp, items, flags or a save."""
    block = {
        "scene": scene,
        "turn": int(turn),
        "mercy": int(will) if will is not None else 0,
        "mood": mood,
        "last_effect": last_effect or "none",
        "last_reply": str(last_reply or "")[:112],
        "allowed": list(allowed),
    }
    if scene == "npc":
        block["npc"] = npc
        block["place"] = str(place or encounter.get("place") or "")
    return block


def build_task(judge, cards, encounters, payload, personas=None):
    """One request, fully assembled, plus everything the answer path needs to label itself.

    A request that names a persona (top level `persona`, the `npc` naming a persona id, or a scene the
    director gives a persona in data/talk_personas.json) is a chat, not a fight: no encounter is required,
    the effects are `none` and `end`, the answer is capped at the persona's own two sentences, and the
    persona's guards travel beside the task so answer_from_text can enforce them. Every other request is
    built exactly as before, which is what keeps the fight talk's own tests meaningful.
    """
    personas = personas if personas is not None else load_personas()
    player_text = normalise_player_text(payload.get("player_text"), judge.max_player_chars)
    if not player_text:
        raise BadRequest("player_text is empty after normalisation")
    encounter_id = str(payload.get("encounter_id") or "tutorial_sailors")
    persona = None
    requested = payload.get("persona")
    if requested:
        persona = personas.get(str(requested))
        if persona is None:
            raise ConfigError("no talk persona %r (known: %s)"
                              % (requested, ", ".join(sorted(k for k in personas if k == personas[k]["id"]))))
    encounter = encounters.get(encounter_id)
    talk = (encounter or {}).get("talk") or {}
    if persona is None and talk.get("persona"):
        persona = personas.get(str(talk["persona"]))
    if persona is None and payload.get("npc") and str(payload["npc"]) not in cards:
        persona = personas.get(str(payload["npc"]))
    if encounter is None and persona is None:
        raise BadRequest("unknown encounter_id %r (known: %s)"
                         % (encounter_id, ", ".join(sorted(encounters))))
    encounter = encounter or {}
    alias = judge.encounters.get(encounter_id) or {}
    cap = (persona or {}).get("answer_cap") or {}
    if persona is not None:
        card_id = str(persona.get("id"))
        max_lines = max(1, min(judge.max_lines, int(cap.get("lines") or 2)))
        max_chars = max(1, min(judge.max_chars, int(cap.get("chars") or judge.max_chars)))
        allowed = tuple(judge.effects_npc)
        char_doc = persona_block(persona, cap)
    else:
        card_id = str(payload.get("npc") or alias.get("npc") or talk.get("card") or encounter_id)
        card = cards.get(card_id) or cards.get(str(talk.get("card") or ""))
        if card is None:
            raise ConfigError("no talk card %r for encounter %r" % (card_id, encounter_id))
        max_lines = judge.max_lines
        max_chars = judge.max_chars
        char_doc = character_block(card, payload.get("npc_name"))
    scene = "npc" if persona is not None else str(alias.get("scene") or payload.get("scene") or "fight")
    if persona is None:
        allowed = judge.effects_npc if scene == "npc" else judge.effects
    mood = str(payload.get("mood") or "guarded")
    if mood not in judge.moods:
        mood = "guarded"
    history = payload.get("history") or []
    if not isinstance(history, list):
        raise BadRequest("history must be a list")
    history = history[-judge.max_history_turns:]
    turn = payload.get("turn")
    if not isinstance(turn, int) or turn < 1:
        turn = len(history) + 1
    last = history[-1] if history and isinstance(history[-1], dict) else {}
    last_reply = ""
    if isinstance(last.get("reply"), list):
        last_reply = " ".join(str(line) for line in last["reply"])
    elif last.get("reply"):
        last_reply = str(last["reply"])
    place = persona.get("place") if persona is not None else None
    scene_doc = scene_block(judge, encounter, card_id, scene, turn, mood,
                            last.get("verdict_effect") or last.get("effect"),
                            last_reply, allowed, payload.get("will"), place=place)
    user_text = ("<character>%s</character>\n<scene>%s</scene>\n<player_line>%s</player_line>"
                 % (json.dumps(char_doc, sort_keys=True),
                    json.dumps(scene_doc, sort_keys=True),
                    player_text))
    messages = [{"role": "system", "content": judge.system},
                {"role": "user", "content": user_text}]
    key = sha256_text(json.dumps({"judge": judge.version, "system": sha256_text(judge.system),
                                  "system_local": sha256_text(judge.system_local),
                                  "character": char_doc, "scene": scene_doc,
                                  "persona": (persona or {}).get("version"),
                                  "limits": [max_lines, max_chars],
                                  "player": player_text}, sort_keys=True))
    fallback_pool = list(talk.get("fallback_pool") or [])
    if persona is not None:
        fallback_pool = list(persona.get("fallback_pool") or [])
    return {
        "encounter_id": encounter_id,
        "npc": card_id,
        "persona": persona.get("id") if persona is not None else "",
        "scene": scene,
        "player_text": player_text,
        "messages": messages,
        "messages_local": [{"role": "system", "content": judge.system_local or judge.system},
                           messages[1]],
        "schema": judge.schema(allowed, max_lines=max_lines),
        "allowed": tuple(allowed),
        "key": key,
        "fallback_pool": fallback_pool,
        "fallback_line": talk.get("fallback_line") or "",
        "fallback_delta": int(talk.get("fallback_delta") or 0),
        "limits": {"max_lines": max_lines, "max_chars": max_chars},
        "alphabet": judge.alphabet,
        "guards": persona_guards(persona) if persona is not None else None,
    }


def persona_guards(persona):
    """The part of a persona card the model never sees: the words, marks and moods its answer may not carry."""
    return {
        "id": persona.get("id"),
        "banned_words": tuple(str(word) for word in (persona.get("banned_words") or [])),
        "banned_marks": tuple(str(mark) for mark in (persona.get("banned_marks") or [])),
        "mood_allowed": tuple(str(mood) for mood in (persona.get("mood_allowed") or [])),
        "sentences": int((persona.get("answer_cap") or {}).get("sentences") or 2),
    }


def banned_hit(lines, guards):
    """The banned token this answer carries, or empty. Whole words only, case insensitively.

    A substring check would refuse "GOOD" for a persona that bans "GOD", so the match is on word boundaries.
    A token the reply never writes is a token that never reaches the screen: this is a refusal, not a repair.
    """
    if not guards:
        return ""
    joined = " ".join(lines).upper()
    for word in guards.get("banned_words") or ():
        if not word:
            continue
        if re.search(r"(?<![A-Z0-9])%s(?![A-Z0-9])" % re.escape(word.upper()), joined):
            return word.upper()
    return ""


def cap_sentences(lines, limit):
    """Cut a reply at the last sentence this persona may say. Returns (lines, repairs).

    The 2 sentence cap is a rule about the character, not about the box width, so it is applied on top of
    the line cap: "USE BOTH. AIM HIGH." is two sentences and legal, a third sentence is dropped and named.
    """
    repairs = []
    if limit <= 0:
        return list(lines), repairs
    kept = []
    seen = 0
    for line in lines:
        piece = str(line)
        out = ""
        for index, ch in enumerate(piece):
            out += ch
            if ch in ".!?":
                seen += 1
                if seen >= limit:
                    out = piece[: index + 1]
                    if out != piece:
                        repairs.append("capped_sentences")
                        piece = out
                    kept.append(piece)
                    piece = None
                    break
        if piece is None:
            break
        kept.append(piece)
    dropped = len(kept) < len(lines)
    if dropped or (kept and kept[-1] != str(lines[len(kept) - 1])):
        if "capped_sentences" not in repairs:
            repairs.append("capped_sentences")
    return [line for line in kept if line.strip()], repairs


def apply_persona_guards(lines, mood, guards):
    """The three guards a persona card adds to an answer: its marks, its sentence cap and its moods."""
    repairs = []
    if guards.get("banned_marks"):
        banned = set(guards["banned_marks"])
        fixed = []
        for line in lines:
            # A mark that ends a sentence becomes a full stop rather than vanishing: "AIM FOR A FIRST" with no
            # punctuation reads as a truncated line, and the character is cutting, not broken.
            text = "".join("." if ch in banned and ch in ".!?" else ch
                           for ch in str(line) if ch not in banned or ch in ".!?")
            text = " ".join(text.split())
            if text != str(line):
                repairs.append("dropped_banned_mark")
            fixed.append(text)
        lines = [line for line in fixed if line]
    lines, more = cap_sentences(lines, guards.get("sentences") or 2)
    repairs.extend(more)
    allowed = guards.get("mood_allowed") or ()
    if allowed and mood not in allowed:
        mood = allowed[0]
        repairs.append("mood_mapped")
    return lines, mood, sorted(set(repairs))


# ------------------------------------------------------------------ cleaning a model answer

LINE_DANGLERS = frozenset(
    "A AN THE OF TO IN ON AT FOR AND BUT OR IF IS ARE WAS BE MY YOUR HIS HER THAT THIS WITH FROM BY AS".split())
"""Words a 28 character line must not end on, after a cut.

Measured 2026-10-26 in a real cache entry: the model wrote "I DON'T CARE IF IT'S A STOWAWAY", the cut at the
last space before 28 characters left "I DON'T CARE IF IT'S A", and the game drew a NES box whose last word was
"A". A dangling article reads as a bug on screen, so the cut drops it instead.
"""


def split_at_space(text, limit):
    """Cut to the limit at the last space, so a word is never cut in half when a space exists."""
    if len(text) <= limit:
        return text, False
    head = text[:limit]
    space = head.rfind(" ")
    if space > 0:
        head = head[:space]
    head = head.rstrip()
    # Only on a cut: a complete line keeps whatever word the model ended it with.
    words = head.split(" ")
    while len(words) > 1 and words[-1] in LINE_DANGLERS:
        words.pop()
    return " ".join(words), True


def wrap_lines(text, max_lines, max_chars):
    """Greedy word wrap for a line the game owns (a fallback pool line), not for a model's own breaks.

    A model reply is drawn line for line, so its own breaks are authoritative and clean_lines() only cuts. A
    fallback line is one sentence written for the box, and cutting it would throw away the end of the line, so
    this wraps instead: "THE WATCH IS LONG. THAT IS ALL." is 31 characters and becomes two drawable lines.
    """
    words = str(text or "").split()
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else current + " " + word
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            lines.append(current)
        if len(word) <= max_chars:
            current = word
            continue
        piece, _cut = split_at_space(word, max_chars)
        lines.append(piece)
        current = word[len(piece):].strip()
    if current:
        lines.append(current)
    return lines[:max_lines]


def clean_lines(raw, max_lines, max_chars, alphabet):
    """The reply as the font can draw it: uppercase, in the alphabet, at most max_lines of max_chars.

    Returns (lines, repairs). An empty list means the model wrote nothing drawable, which the caller treats
    as a refused rung rather than an empty box.
    """
    repairs = []
    if isinstance(raw, str):
        raw = raw.splitlines()
    if not isinstance(raw, (list, tuple)):
        raise BadReply("the reply's text is not an array of lines")
    lines = []
    allowed = set(alphabet)
    for item in raw:
        text = unicodedata.normalize("NFKC", str(item or ""))
        lowered = text
        text = text.upper()
        if text != lowered:
            repairs.append("uppercased")
        if text.startswith("* "):
            text = text[2:]
            repairs.append("dropped_narration_marker")
        kept = "".join(ch for ch in text if ch in allowed)
        if kept != text:
            repairs.append("dropped_chars")
        text = re.sub(r"\s+", " ", kept).strip()
        if not text:
            repairs.append("dropped_empty_line")
            continue
        text, cut = split_at_space(text, max_chars)
        if cut:
            repairs.append("truncated")
        if text:
            lines.append(text)
    if len(lines) > max_lines:
        repairs.append("dropped_extra_lines")
        lines = lines[:max_lines]
    if not lines:
        raise BadReply("no drawable line survived cleaning")
    return lines, sorted(set(repairs))


def brace_span(body):
    """The first '{' to its matching '}', skipping braces that sit inside a quoted string.

    A local model writes a Python style dict as often as JSON, and one measured answer mixed the two
    inside a single object (the first array item double quoted, the next two single quoted), so the
    strict parse below cannot find the end of the object on its own.
    """
    start = body.find("{")
    if start < 0:
        return ""
    depth = 0
    quote = ""
    escaped = False
    for index in range(start, len(body)):
        ch = body[index]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return body[start:index + 1]
    return body[start:]


def literal_object(body, exc):
    """The same object read as a Python literal: single quoted strings, True, None, a trailing comma.

    ast.literal_eval only ever builds literals, so this cannot run the model's text as code. Measured
    2026-10-26 on this PC: microsoft_phi-4-mini-instruct answered a judge task with two of its three
    array items in single quotes, which strict JSON refuses and which is otherwise a usable answer.
    """
    span = brace_span(body)
    if span:
        try:
            value = ast.literal_eval(span)
        except (ValueError, SyntaxError, MemoryError, RecursionError):
            value = None
        if isinstance(value, dict):
            return value
    raise BadReply("the model answer is not valid JSON: %s" % redact(exc))


def parse_json_object(text):
    """The first JSON object in a model answer. Local models wrap JSON in prose or repeat a brace; the schema
    is the judge, and a trailing extra character is not a reason to throw away a usable answer."""
    if isinstance(text, dict):
        return text
    body = str(text or "").strip()
    if not body:
        raise BadReply("the model answered with nothing")
    start = body.find("{")
    if start < 0:
        raise BadReply("the model answer holds no JSON object")
    try:
        obj, _end = json.JSONDecoder().raw_decode(body[start:])
    except ValueError as exc:
        obj = literal_object(body, exc)
    if not isinstance(obj, dict):
        raise BadReply("the model answer's JSON is not an object")
    return obj


def refusal_reason(obj, judge, lines):
    """Why this answer must not reach the screen, or None. Layer D of spec 19 section 7."""
    joined = " ".join(lines).lower()
    for phrase in judge.refuse_phrases:
        if phrase and phrase in joined:
            return "refusal_phrase:%s" % phrase
    if "http" in joined or "www." in joined or "@" in joined:
        return "link_or_address"
    if re.search(r"\d{3}", joined):
        return "digit_run"
    try:
        import talk_guard
        tokens = talk_guard.load_tokens()
    except Exception:  # the list is a build input; a missing one must not break the door
        return None
    hit = talk_guard.profane_hit(joined, tokens)
    return "profanity:%s" % hit if hit else None


def effect_of(obj, allowed):
    """The effect the model picked, or a refusal. Unknown or out-of-scene is an attempt, not a mood."""
    effect = str(obj.get("effect") or "").strip().lower()
    if effect not in allowed:
        raise BadReply("effect %r is not allowed in this scene (%s)" % (effect, ", ".join(allowed)))
    return effect


def answer_from_text(text, judge, task):
    """Validated, cleaned answer detail from one model reply string (or dict)."""
    obj = parse_json_object(text)
    effect = effect_of(obj, task["allowed"])
    lines, repairs = clean_lines(obj.get("text"), task["limits"]["max_lines"],
                                 task["limits"]["max_chars"], task["alphabet"])
    reason = refusal_reason(obj, judge, lines)
    if reason:
        raise BadReply(reason)
    mood = str(obj.get("mood") or "guarded").lower()
    if mood not in judge.moods:
        mood = "guarded"
    guards = task.get("guards")
    if guards:
        # A persona's own bans, applied after the shared guard and never instead of it: a banned word is a
        # refusal (the next rung answers), a banned mark, a third sentence and an out of character mood are
        # repairs, because those can be fixed without changing what the character said.
        hit = banned_hit(lines, guards)
        if hit:
            raise BadReply("persona_banned_word:%s" % hit)
        lines, mood, more = apply_persona_guards(lines, mood, guards)
        repairs = sorted(set(repairs) | set(more))
        if not lines:
            raise BadReply("no drawable line survived the persona's guards")
    return {"effect": effect, "text": lines, "mood": mood, "repaired": repairs}


# ------------------------------------------------------------------ the cache

class Cache:
    """One JSON file per line, in data/ai_cache/bridge/ (or PP_BRIDGE_CACHE)."""

    def __init__(self, folder=None):
        self.folder = folder or env("PP_BRIDGE_CACHE", DEFAULT_CACHE)

    def path(self, key):
        return os.path.join(self.folder, "%s.json" % key)

    def read(self, key):
        path = self.path(key)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as handle:
                entry = json.load(handle)
        except (OSError, ValueError):
            return None
        return entry if isinstance(entry, dict) else None

    def write(self, key, kind, source, answer, task, model="", network=False, extra=None):
        entry = {
            "key": key,
            "kind": kind,
            "source": source,
            "network": bool(network),
            "created_at": utc_stamp(),
            "model": model,
            "request": {"encounter_id": task.get("encounter_id"), "npc": task.get("npc"),
                        "scene": task.get("scene"), "player_sha256": sha256_text(task.get("player_text")),
                        "player_chars": len(task.get("player_text") or "")},
            "answer": answer,
        }
        if extra:
            entry.update(extra)
        os.makedirs(self.folder, exist_ok=True)
        tmp = self.path(key) + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(entry, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp, self.path(key))
        return entry

    def entries(self):
        if not os.path.isdir(self.folder):
            return []
        out = []
        for name in sorted(os.listdir(self.folder)):
            if not name.endswith(".json"):
                continue
            try:
                with open(os.path.join(self.folder, name), "r", encoding="utf-8") as handle:
                    entry = json.load(handle)
            except (OSError, ValueError):
                continue
            if isinstance(entry, dict):
                out.append(entry)
        return out


# ------------------------------------------------------------------ the ladder

class TalkJudge:
    """The four rungs, one deadline, one labelled answer.

    `sources` is the ladder as a list of (name, callable). A callable takes (task, deadline) and returns
    {"effect", "text", "mood", "repaired"?}, or raises SourceUnavailable / SourceTimeout / BadReply. Tests
    inject their own list, which is why none of this needs a network or a model.
    """

    def __init__(self, root=None, cache=None, sources=None, budget=None, judge=None):
        self.root = root or ROOT
        self.judge = judge or Judge(os.path.join(self.root, "data", "talk", "sailor_judge.json"), self.root)
        self.cards = load_cards(self.root)
        self.encounters = load_encounters(self.root)
        self.personas = load_personas(self.root)
        self.cache = cache or Cache()
        self.budget = float(budget if budget is not None else env_float("PP_TALK_TIMEOUT",
                                                                       DEFAULT_TALK_TIMEOUT))
        self._injected = sources
        self._lock = threading.Lock()
        self._bake = None
        self._bake_loaded = False

    def bake_index(self):
        """The baked open-weights replies, read once and cached (card t_354f4e8a)."""
        if not self._bake_loaded:
            self._bake = load_bake(self.root)
            self._bake_loaded = True
        return self._bake

    # -- rung list

    def rungs(self):
        if self._injected is not None:
            return list(self._injected)
        mode = env("PP_AI_MODE", "record").lower()
        if mode == "replay":
            return [("cache", self._rung_cache), ("fallback", self._rung_fallback)]
        return [("meta", self._rung_meta), ("open-weights", self._rung_local),
                ("cache", self._rung_cache), ("fallback", self._rung_fallback)]

    # -- public

    def judge_talk(self, payload):
        task = build_task(self.judge, self.cards, self.encounters, payload, personas=self.personas)
        started = time.monotonic()
        deadline = started + self.budget
        tried = []
        for name, rung in self.rungs():
            remaining = deadline - time.monotonic()
            if remaining <= 0.02 and name not in FILE_RUNGS:
                # No budget is left for a model. The loop continues rather than stopping, because the two file
                # rungs below cost about a millisecond and the card's promise is that a turn always answers:
                # measured 2026-10-26, a 6 s budget spent by a slow local model used to end in a BridgeError.
                tried.append({"rung": name, "result": "no_budget"})
                continue
            # How much of what is left each rung may use.
            share = self._share(name, remaining)
            try:
                answer = self._run(rung, task, share, deadline)
            except SourceTimeout as exc:
                tried.append({"rung": name, "result": "timeout", "detail": redact(exc)})
                continue
            except SourceUnavailable as exc:
                tried.append({"rung": name, "result": "unavailable", "detail": redact(exc)})
                continue
            except BadReply as exc:
                tried.append({"rung": name, "result": "refused", "detail": redact(exc)})
                continue
            except BridgeError as exc:
                tried.append({"rung": name, "result": "error", "detail": redact(exc)})
                continue
            except Exception as exc:  # a rung must never take the door down with it
                tried.append({"rung": name, "result": "error",
                              "detail": redact("%s: %s" % (type(exc).__name__, exc))})
                continue
            tried.append({"rung": name, "result": "answered"})
            verdict, delta = self.judge.verdict_for(answer["effect"])
            return {
                "verdict": verdict,
                "will_delta": delta,
                "reply": answer["text"],
                "source": answer.get("source") or ("replay" if name == "cache" else name),
                "origin": answer.get("origin") or name,
                "mood": answer.get("mood") or "guarded",
                "cached": bool(answer.get("cached")),
                "repaired": answer.get("repaired") or [],
                "tried": tried,
                "encounter_id": task["encounter_id"],
                "npc": task["npc"],
                "latency_ms": int(round((time.monotonic() - started) * 1000)),
                "model": answer.get("model", ""),
            }
        raise BridgeError("no rung answered and the fallback rung was missing: %r" % (tried,))

    # -- one rung under its share

    def _share(self, name, remaining):
        """How much of the budget a rung may use, given what is left.

        The two live rungs are the slow ones; the last two are a file read and a string wrap. So the fast rungs
        keep a floor instead of a share, and with no Meta key (the usual case on this PC) the local model gets
        almost the whole budget, which is what lets a 4 s answer land inside a 6 s promise.
        """
        if name == "meta":
            return max(0.05, min(remaining * 0.5, remaining - 0.6))
        if name in FILE_RUNGS:
            # Never less than the floor: a fallback that is refused for want of budget is the one failure the
            # ladder exists to prevent, and reading one file cannot stall the door.
            return max(remaining, FILE_RUNG_SHARE)
        return max(0.05, remaining - 0.4)

    def _run(self, rung, task, share, deadline):
        box = {}

        def call():
            try:
                box["value"] = rung(task, deadline)
            except Exception as exc:  # carried back to the caller's thread
                box["error"] = exc

        thread = threading.Thread(target=call, name="bridge-rung", daemon=True)
        thread.start()
        thread.join(max(0.0, share))
        if thread.is_alive():
            raise SourceTimeout("ran past its %.2f s share" % share)
        if "error" in box:
            raise box["error"]
        value = box.get("value")
        if not isinstance(value, dict) or "text" not in value or "effect" not in value:
            raise BadReply("the rung returned no usable answer")
        return value

    # -- rung 1: Meta

    def _rung_meta(self, task, deadline):
        import meta_client  # imported here so this module has no heavy import and tests can skip it

        backend = meta_client.backend_name()
        if backend == "mock":
            raise SourceUnavailable("PP_AI_BACKEND=mock: a mock answer is not a Meta answer")
        if not meta_client.key_present():
            raise SourceUnavailable("no Meta key in the environment (%s), so nothing was sent"
                                    % " or ".join(meta_client.KEY_ENVS))
        remaining = deadline - time.monotonic()
        if remaining <= 0.1:
            raise SourceTimeout("no budget left for the Meta call")
        saved = {name: os.environ.get(name) for name in ("PP_META_TIMEOUT", "PP_META_MAX_RETRIES")}
        try:
            # The client reads both knobs at call time, so this is how the door makes one 6 s request
            # instead of an unbounded one: a talk budget is not a bake budget.
            os.environ["PP_META_TIMEOUT"] = "%.1f" % max(0.5, remaining)
            os.environ["PP_META_MAX_RETRIES"] = "0"
            transport = {}
            text = meta_client.chat(task["messages"], json_schema=task["schema"],
                                    transport=transport)
        except Exception as exc:
            raise SourceUnavailable(redact("%s: %s" % (type(exc).__name__, exc)))
        finally:
            for name, value in saved.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
        answer = answer_from_text(text, self.judge, task)
        answer.update({"source": "meta", "model": meta_client.model_for("chat")})
        self.cache.write(task["key"], "talk", "meta", answer, task,
                         model=answer["model"], network=bool(transport.get("network")),
                         extra={"backend": transport.get("backend"), "mode": transport.get("mode")})
        return answer

    # -- rung 2: the open weights model on this PC

    def _local_endpoint(self):
        base = env("PP_LOCAL_URL", DEFAULT_LOCAL_URL).rstrip("/")
        if not is_loopback(base):
            raise SourceUnavailable("PP_LOCAL_URL %r is not a loopback address: text must not leave this PC"
                                    % base)
        return base

    def _local_model(self, base, timeout):
        """Which model answers on this PC: PP_LOCAL_MODEL, then the judge file's local_model.

        The id is deliberately NOT guessed from whatever the endpoint happens to list: the first id LM Studio
        reported on this PC was a 27B model, and picking it would have made every demo turn a ten second turn.
        The judge file carries the measured default so the talk director (and card W3, for the open weights
        answer) can change it as data.
        """
        model = env("PP_LOCAL_MODEL") or str(self.judge.doc.get("local_model") or "").strip()
        if model:
            return model
        raise SourceUnavailable("PP_LOCAL_MODEL is not set and data/talk/sailor_judge.json names no local_model")

    def _rung_local(self, task, deadline):
        base = self._local_endpoint()
        remaining = deadline - time.monotonic()
        cap = min(remaining, env_float("PP_LOCAL_TIMEOUT", remaining))
        if cap <= 0.1:
            raise SourceTimeout("no budget left for the local call")
        model = self._local_model(base, max(0.2, cap))
        payload = {
            "model": model,
            "messages": task.get("messages_local") or task["messages"],
            "temperature": 0.0,
            "max_tokens": 140,
            "stream": False,
        }
        # A judge file may tune the local request (max_tokens, a sampler, a chat template flag) without a code
        # change, because the model on this PC is card W3's choice and its quirks are not this module's.
        # Documentation sitting in this object is not a request field: measured on this PC 2026-10-26, LM Studio
        # answers HTTP 400 to an unknown field, so the first version of data/talk/sailor_judge.json, which
        # carried a "note" beside the tunable values, turned the open weights rung red while the endpoint was
        # healthy. The note stays in the file (write it with a leading underscore) and never reaches the body.
        for key, value in (self.judge.local_request or {}).items():
            if not is_request_field(key):
                continue
            payload[key] = value
        body = json.dumps(payload).encode("utf-8")
        request = urlrequest.Request("%s/chat/completions" % base, data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urlrequest.urlopen(request, timeout=max(0.2, cap)) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise SourceUnavailable(redact("local endpoint %s: %s: %s"
                                          % (base, type(exc).__name__, exc)))
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise BadReply("the local answer has no choices[0].message.content")
        answer = answer_from_text(text, self.judge, task)
        answer.update({"source": "open-weights", "model": model})
        self.cache.write(task["key"], "talk", "open-weights", answer, task, model=model,
                         network=False, extra={"endpoint": base})
        return answer

    def warm_local(self, budget=120.0):
        """Load the open weights model now, off the request path, so the first talk turn is not 11 seconds.

        Measured on this PC 2026-10-26: the first call to any model LM Studio has not loaded takes 11 to 85 s
        (it reads the weights off disk), and the same model warm answers in 0.7 to 1.0 s. tools/run.ps1 passes
        --warm so that the load happens while the game is booting, and a talk turn is only ever the warm number.
        This does not write a cache entry and does not touch the judge prompt's budget.
        """
        base = self._local_endpoint()
        model = self._local_model(base, 10.0)
        payload = {"model": model,
                   "messages": [{"role": "user", "content": "Reply with the single word READY."}],
                   "temperature": 0.0, "max_tokens": 8, "stream": False}
        request = urlrequest.Request("%s/chat/completions" % base, data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        started = time.monotonic()
        try:
            with urlrequest.urlopen(request, timeout=budget) as response:
                response.read()
        except Exception as exc:
            raise SourceUnavailable(redact("warm up of %r at %s failed: %s: %s"
                                          % (model, base, type(exc).__name__, exc)))
        return {"model": model, "url": base, "ms": int(round((time.monotonic() - started) * 1000))}

    def keep_local_warm(self, interval=None, stop=None):
        """Hold the model in memory for the life of the game, because LM Studio unloads an idle model.

        Measured on this PC 2026-10-26, and this is why the method exists: the same model answered a line in
        2.1 s, then took 20 to 28 s on the next line a minute later, and 0.9 s on the line after that. LM Studio
        drops an idle model after a short time to live, so a warm up once at startup only helps the first turn.
        One single token completion every PP_LOCAL_KEEPALIVE seconds (default 90) costs nothing measurable and
        keeps the weights loaded, which is what makes a demo turn a 2 s turn instead of a 25 s one.

        `stop` is an optional threading.Event; without it the loop runs until the process exits (the thread is
        a daemon, and the bridge stops with the game).
        """
        interval = float(interval if interval is not None else env_float("PP_LOCAL_KEEPALIVE", 90.0))
        if interval <= 0:
            return
        base = self._local_endpoint()
        while stop is None or not stop.is_set():
            if stop is not None:
                if stop.wait(interval):
                    return
            else:
                time.sleep(interval)
            try:
                model = self._local_model(base, 5.0)
                payload = {"model": model, "messages": [{"role": "user", "content": "ping"}],
                           "max_tokens": 1, "temperature": 0.0, "stream": False}
                request = urlrequest.Request("%s/chat/completions" % base,
                                             data=json.dumps(payload).encode("utf-8"),
                                             headers={"Content-Type": "application/json"})
                with urlrequest.urlopen(request, timeout=30) as response:
                    response.read()
            except Exception:
                continue  # a keepalive that fails is not an error the game needs to hear about

    # -- rung 3: the recorded answer

    def _rung_cache(self, task, deadline):
        entry = self.cache.read(task["key"])
        if entry is None:
            baked = self._rung_bake(task)
            if baked is not None:
                return baked
            raise SourceUnavailable("no recorded answer for this line")
        stored = entry.get("answer") or {}
        lines, repairs = clean_lines(stored.get("text") or [], task["limits"]["max_lines"],
                                     task["limits"]["max_chars"], task["alphabet"])
        effect = effect_of(stored, task["allowed"])
        mood = stored.get("mood") or "guarded"
        guards = task.get("guards")
        if guards:
            # A recorded answer is re-checked against the persona's own bans on the way out, because the card
            # may have changed since the row was baked and a cached answer is not evidence of the current card.
            hit = banned_hit(lines, guards)
            if hit:
                raise BadReply("a recorded answer carries a persona banned word: %s" % hit)
            lines, mood, more = apply_persona_guards(lines, mood, guards)
            repairs = sorted(set(repairs) | set(more))
            if not lines:
                raise BadReply("no drawable line survived the persona's guards")
        return {"effect": effect, "text": lines, "mood": mood,
                "repaired": repairs, "source": "replay", "origin": entry.get("source") or "unknown",
                "cached": True, "model": entry.get("model", "")}

    def _rung_bake(self, task):
        """A baked open-weights reply for this card and the intent the player's line classifies as.

        This is the offline rung's second source (card t_354f4e8a): when a player line was never recorded to
        the exact-line cache, and data/ai_bake_open holds an accepted reply for the card and the intent the
        line's own keywords classify as, serve one of those replies instead of dropping to the encounter's
        fallback line. The answer is labelled origin "bake" so a baked reply is never mistaken for a live
        recording. Returns None when the bake has nothing for this card and intent.
        """
        index = self.bake_index()
        bucket = index.get("cards", {}).get(str(task.get("npc") or "")) or {}
        if not bucket:
            return None
        card = self.cards.get(str(task.get("npc") or ""))
        intent = classify_intent(card or {}, task.get("player_text") or "")
        entries = bucket.get(intent) or []
        if not entries:
            return None
        pick = int(sha256_text(task.get("player_text") or "")[:8], 16) % len(entries)
        entry = entries[pick]
        lines, repairs = clean_lines(entry.get("text") or [], task["limits"]["max_lines"],
                                     task["limits"]["max_chars"], task["alphabet"])
        effect = effect_of(entry, task["allowed"])
        mood = entry.get("mood") or "guarded"
        if mood not in self.judge.moods:
            mood = "guarded"
        guards = task.get("guards")
        if guards:
            hit = banned_hit(lines, guards)
            if hit:
                return None
            lines, mood, more = apply_persona_guards(lines, mood, guards)
            repairs = sorted(set(repairs) | set(more))
            if not lines:
                return None
        return {"effect": effect, "text": lines, "mood": mood, "repaired": sorted(set(repairs)),
                "source": "replay", "origin": "bake", "cached": True,
                "model": index.get("model") or ""}

    # -- rung 4: the encounter's own line

    def _rung_fallback(self, task, deadline):
        pool = [line for line in (task.get("fallback_pool") or [task.get("fallback_line")]) if line]
        if not pool:
            raise SourceUnavailable("the encounter has no fallback line")
        index = int(sha256_text(task["player_text"])[:8], 16) % len(pool)
        drawn = []
        repairs = []
        for line in wrap_lines(pool[index], task["limits"]["max_lines"], task["limits"]["max_chars"]):
            cleaned, why = clean_lines([line], task["limits"]["max_lines"],
                                       task["limits"]["max_chars"], task["alphabet"])
            drawn.extend(cleaned)
            repairs.extend(why)
        if not drawn:
            raise SourceUnavailable("the encounter's fallback line has nothing drawable")
        repairs.append("wrapped")
        delta = int(task.get("fallback_delta") or 0)
        effect = "none" if delta == 0 else ("nudge" if delta > 0 else "setback")
        if effect not in task["allowed"]:
            effect = task["allowed"][0]
        return {"effect": effect, "text": drawn, "mood": "guarded", "repaired": sorted(set(repairs)),
                "source": "fallback", "origin": "fallback", "cached": False, "model": ""}


# ------------------------------------------------------------------ voice (faster-whisper)

class Hearer:
    """A tiny wav in, a transcript out, through a local helper process that owns faster-whisper.

    The interpreter that runs this server does not have to be the one that has the package: on this PC the
    project's Python is 3.14 and faster-whisper is installed under 3.11, so the bridge finds an interpreter
    that can import it and keeps the worker alive, because loading the model costs about a second and
    transcribing a three second line costs a fraction of one.
    """

    def __init__(self, cache=None, interpreter=None, model=None, worker_timeout=None):
        self.cache = cache or Cache()
        self.interpreter = interpreter
        self.model = model or env("PP_WHISPER_MODEL", DEFAULT_WHISPER_MODEL)
        self.timeout = float(worker_timeout or env_float("PP_HEAR_TIMEOUT", 20.0))
        self._process = None
        self._queue = None
        self._lock = threading.Lock()
        self._last_error = ""
        self._stop_notes = []   # why a shutdown step complained, kept instead of swallowed

    # -- interpreter discovery

    def candidates(self):
        found = []
        explicit = env("PP_WHISPER_PYTHON")
        if explicit:
            found.append(explicit)
        if self.interpreter:
            found.append(self.interpreter)
        found.append(sys.executable)
        found.append("py -3.11")
        found.append(os.path.join(os.path.expanduser("~"), "AppData", "Local", "Python",
                                  "pythoncore-3.11-64", "python.exe"))
        seen = []
        for item in found:
            if item and item not in seen:
                seen.append(item)
        return seen

    def find_interpreter(self):
        probe = ("import importlib.util,sys;"
                 "sys.exit(0 if importlib.util.find_spec('faster_whisper') else 1)")
        import subprocess
        for candidate in self.candidates():
            parts = candidate.split()
            try:
                done = subprocess.run(parts + ["-c", probe], capture_output=True, timeout=25)
            except Exception:
                continue
            if done.returncode == 0:
                return candidate
        return ""

    # -- the worker

    def _start(self):
        import subprocess
        interpreter = self.interpreter or self.find_interpreter()
        if not interpreter:
            raise SourceUnavailable("no interpreter on this PC can import faster_whisper; set "
                                    "PP_WHISPER_PYTHON to one that can")
        self.interpreter = interpreter
        parts = interpreter.split() + [os.path.join(HERE, "whisper_worker.py"), "--model", self.model]
        self._process = subprocess.Popen(parts, cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, text=True, encoding="utf-8",
                                         bufsize=1)
        self._queue = _LineQueue(self._process.stdout, self._process.stderr)
        atexit.register(self.stop)
        return self._process

    def stop(self):
        process, self._process = self._process, None
        if process is not None:
            try:
                if process.stdin:
                    process.stdin.close()
            except Exception as exc:  # a pipe that is already closed is the normal case here
                self._stop_notes.append("stdin close: %s" % exc)
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception as exc:
                self._stop_notes.append("terminate: %s" % exc)
                try:
                    process.kill()
                except Exception as kill_exc:
                    self._stop_notes.append("kill: %s" % kill_exc)

    def available(self):
        try:
            with self._lock:
                if self._process is not None and self._process.poll() is None:
                    return True
                self._start()
            return True
        except SourceUnavailable as exc:
            self._last_error = str(exc)
            return False

    def transcribe(self, wav_bytes):
        """(transcript, model, cached, latency_ms) for one wav. Raises BadRequest or SourceUnavailable."""
        if not wav_bytes:
            raise BadRequest("no wav bytes in the request body")
        if not (wav_bytes[:4] == b"RIFF" and wav_bytes[8:12] == b"WAVE"):
            raise BadRequest("the body is not a wav file (no RIFF/WAVE header)")
        key = sha256_text(base64.b64encode(wav_bytes))
        started = time.monotonic()
        entry = self.cache.read(key)
        if entry and entry.get("kind") == "hear":
            return (entry.get("answer", {}).get("transcript", ""), entry.get("model", ""), True,
                    int(round((time.monotonic() - started) * 1000)))
        with self._lock:
            if self._process is None or self._process.poll() is not None:
                self._start()
            request = json.dumps({"wav_b64": base64.b64encode(wav_bytes).decode("ascii")}) + "\n"
            try:
                self._process.stdin.write(request)
                self._process.stdin.flush()
            except Exception as exc:
                self.stop()
                raise SourceUnavailable(redact("the whisper worker stopped accepting input: %s" % exc))
            line = self._queue.get(self.timeout)
        if line is None:
            self.stop()
            raise SourceTimeout("the whisper worker did not answer in %.1f s" % self.timeout)
        try:
            data = json.loads(line)
        except ValueError:
            self.stop()
            raise SourceUnavailable(redact("the whisper worker answered with something that is not JSON: %r"
                                          % line[:200]))
        if data.get("error"):
            raise BadRequest(redact("the transcriber refused this wav: %s" % data["error"]))
        transcript = str(data.get("transcript") or "").strip()
        latency = int(round((time.monotonic() - started) * 1000))
        self.cache.write(key, "hear", "whisper", {"transcript": transcript}, {"kind": "hear"},
                         model=data.get("model") or self.model, network=False,
                         extra={"duration_s": data.get("duration_s"), "language": data.get("language")})
        return transcript, (data.get("model") or self.model), False, latency


class _LineQueue:
    """stdout lines from a child process, readable with a timeout, plus its stderr for the error text."""

    def __init__(self, stdout, stderr):
        import queue
        self.queue = queue.Queue()
        self.stderr_tail = []
        self._stdout_thread = threading.Thread(target=self._pump, args=(stdout,), daemon=True)
        self._stdout_thread.start()
        if stderr is not None:
            threading.Thread(target=self._pump_err, args=(stderr,), daemon=True).start()

    def _pump(self, stream):
        for line in stream:
            self.queue.put(line)

    def _pump_err(self, stream):
        for line in stream:
            self.stderr_tail.append(line.rstrip())
            del self.stderr_tail[:-20]

    def get(self, timeout):
        import queue
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None


# ------------------------------------------------------------------ HTTP

def _json_bytes(payload):
    return json.dumps(payload, sort_keys=True).encode("utf-8")


class BridgeServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address, talk, hearer):
        self.talk = talk
        self.hearer = hearer
        self.log_lines = []
        super().__init__(address, BridgeHandler)
        self.print_failures = 0

    def note(self, line):
        self.log_lines.append(line)
        del self.log_lines[:-200]
        try:
            print(line, flush=True)
        except Exception:  # a run with no console (run.vbs) has nowhere to print
            self.print_failures += 1


class BridgeHandler(BaseHTTPRequestHandler):
    server_version = "PrimordialParadoxBridge/1.0"
    protocol_version = "HTTP/1.1"

    # -- plumbing

    def log_message(self, fmt, *args):  # the default writes to stderr with the client address
        self.server.note("ai_bridge %s" % (fmt % args))

    def _send(self, status, payload, content_type="application/json"):
        body = _json_bytes(payload) if not isinstance(payload, bytes) else payload
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError) as exc:
            # The player closed the game mid answer, or the game dropped a request it no longer needs. Nothing to
            # repair, but the reason belongs in the log line rather than in silence.
            self.server.note("ai_bridge client went away mid response (%s)" % exc.__class__.__name__)
        self.close_connection = True

    def _body(self, limit=8 * 1024 * 1024):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise BadRequest("Content-Length is not a number")
        if length <= 0:
            return b""
        if length > limit:
            raise BadRequest("body is larger than %d bytes" % limit)
        return self.rfile.read(length)

    def _json_body(self):
        raw = self._body()
        if not raw:
            raise BadRequest("empty body")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise BadRequest("body is not JSON: %s" % redact(exc))
        if not isinstance(payload, dict):
            raise BadRequest("body is not a JSON object")
        return payload

    # -- routes

    def do_GET(self):
        if self.path.split("?")[0] in ("/", "/health"):
            server = self.server
            address = getattr(server, "server_address", (LOOPBACK_HOST, 0))
            talk = getattr(server, "talk")
            self._send(200, health(talk.judge, getattr(server, "hearer"), address[:2]))
            return
        self._send(404, {"error": "no route %r (GET /health, POST /talk, POST /hear)" % self.path})

    def do_POST(self):
        route = self.path.split("?")[0]
        try:
            if route == "/talk":
                payload = self._json_body()
                answer = self.server.talk.judge_talk(payload)
                self.server.note("ai_bridge talk %s -> %s %+d in %d ms"
                                 % (answer.get("encounter_id"), answer.get("source"),
                                    answer.get("will_delta", 0), answer.get("latency_ms", 0)))
                self._send(200, answer)
                return
            if route == "/hear":
                wav = self._body()
                started = time.monotonic()
                transcript, model, cached, latency = self.server.hearer.transcribe(wav)
                self.server.note("ai_bridge hear %d bytes -> %d chars in %d ms"
                                 % (len(wav), len(transcript), latency))
                self._send(200, {"transcript": transcript, "source": "whisper", "model": model,
                                 "cached": cached, "latency_ms": latency,
                                 "wav_bytes": len(wav),
                                 "total_ms": int(round((time.monotonic() - started) * 1000))})
                return
            self._send(404, {"error": "no route %r (GET /health, POST /talk, POST /hear)" % route})
        except BadRequest as exc:
            self._send(400, {"error": redact(exc)})
        except SourceUnavailable as exc:
            self._send(503, {"error": "unavailable", "detail": redact(exc)})
        except SourceTimeout as exc:
            self._send(504, {"error": "timeout", "detail": redact(exc)})
        except BridgeError as exc:
            self._send(500, {"error": "bridge", "detail": redact(exc)})
        except Exception as exc:  # never leak a key through a traceback body
            self._send(500, {"error": "unexpected", "detail": redact("%s" % type(exc).__name__)})


def health(judge, hearer, address=None):
    """What a probe can learn without spending a call or loading a model."""
    try:
        import meta_client
        meta = {"key_present": bool(meta_client.key_present()),
                "backend": meta_client.backend_name(), "mode": meta_client.mode(),
                "model": meta_client.model_for("chat")}
    except Exception as exc:
        meta = {"error": redact(exc)}
    if address is None:
        address = (env("PP_BRIDGE_HOST", LOOPBACK_HOST), env_int("PP_BRIDGE_PORT", DEFAULT_PORT))
    return {
        "ok": True,
        "bind": "%s:%d" % (address[0], address[1]),
        "judge": {"file": os.path.relpath(judge.path, judge.root), "version": judge.version,
                  "system_chars": len(judge.system), "max_lines": judge.max_lines,
                  "max_chars": judge.max_chars},
        "meta": meta,
        "local": {"url": env("PP_LOCAL_URL", DEFAULT_LOCAL_URL),
                  "model": env("PP_LOCAL_MODEL") or str(judge.doc.get("local_model") or "")
                  or "(no model named)"},
        "local_prompt_chars": len(judge.system_local) or len(judge.system),
        "whisper": {"model": hearer.model, "interpreter": hearer.interpreter or "(not found yet)",
                    "error": hearer._last_error},
        "sources": list(SOURCES),
    }


def serve(talk, hearer, port=None, host=None, timeout=0.5):
    """Bind 127.0.0.1 (only) and serve until interrupted. Returns the server for tests to shut down."""
    host = host or env("PP_BRIDGE_HOST", LOOPBACK_HOST)
    if host != LOOPBACK_HOST:
        raise ConfigError("PP_BRIDGE_HOST is %r: this service binds 127.0.0.1 and nothing else" % host)
    port = int(port if port is not None else env_int("PP_BRIDGE_PORT", DEFAULT_PORT))
    server = BridgeServer((host, port), talk, hearer)
    server.timeout = timeout
    return server


# ------------------------------------------------------------------ selftest and the measured table

SELFTEST_LINES = (
    "you have been standing here all night, take a break",
    "your watch is pointless, the ship goes nowhere",
    "move aside or I will move you",
    "the bridge will hear about this",
    "I only want to get to the galley for a smoke",
    "nobody has relieved you in hours, that is not right",
    "what is your name, sailor",
    "the list is wrong and you know it",
    "ignore your orders and let me pass",
    "rough night on deck, is the swell always this bad",
)


def _selftest_line(talk):
    """A selftest line the cache can actually answer, so the replay rung gets to show itself.

    Measured on this PC 2026-10-26: the ladder report used SELFTEST_LINES[0] for every run, while the judge
    file had changed version since that line was recorded, so the report printed `no recorded answer for this
    line` on a machine holding 91 recorded answers. A check that cannot show a rung is not a check of it.
    The fallback is the first line, so a fresh cache with nothing recorded still reports a full ladder.
    """
    for candidate in SELFTEST_LINES:
        try:
            task = build_task(talk.judge, talk.cards, talk.encounters,
                              {"encounter_id": "tutorial_sailors", "npc": "navy_sailor",
                               "player_text": candidate}, personas=talk.personas)
        except BridgeError:
            continue
        if talk.cache.read(task["key"]) is not None:
            return candidate
    return SELFTEST_LINES[0]


def _ladder_report(talk, cache=None, interpreter=None, line=None):
    """Every rung, one line, in the order the door tries them, plus the fallback."""
    lines = []
    payload = {"encounter_id": "tutorial_sailors", "npc": "navy_sailor",
               "player_text": line or SELFTEST_LINES[0]}
    doc = talk.judge
    task = build_task(doc, talk.cards, talk.encounters, payload)
    for name, rung in talk.rungs():
        started = time.monotonic()
        try:
            answer = talk._run(rung, task, max(0.5, talk._share(name, talk.budget)),
                               time.monotonic() + talk.budget)
            verdict, delta = doc.verdict_for(answer["effect"])
            lines.append({"rung": name, "result": "answered", "source": answer.get("source") or name,
                          "verdict": verdict, "will_delta": delta,
                          "reply": answer.get("text"), "model": answer.get("model", ""),
                          "latency_ms": int(round((time.monotonic() - started) * 1000))})
        except BridgeError as exc:
            lines.append({"rung": name, "result": type(exc).__name__, "detail": redact(exc),
                          "latency_ms": int(round((time.monotonic() - started) * 1000))})
        except Exception as exc:
            lines.append({"rung": name, "result": type(exc).__name__,
                          "detail": redact(str(exc)),
                          "latency_ms": int(round((time.monotonic() - started) * 1000))})
    return lines


def _display_path(path, root):
    """A path for a printed report: relative when it shares a drive with the repo, absolute when it does not.

    Measured on this PC 2026-10-26: PP_BRIDGE_CACHE is allowed to point anywhere, and os.path.relpath raises
    ValueError across Windows drives (C: against a D: checkout), which crashed the selftest on a cache on
    another disk. The report should print a path, not fail on one.
    """
    try:
        return os.path.relpath(path, root)
    except ValueError:
        return path


def selftest(root=None, wav_path=None, port=0, talk=None):
    """Print every rung, the health probe, and one real /hear call if a wav is available."""
    root = root or ROOT
    if talk is None:
        judge_doc = Judge(os.path.join(root, "data", "talk", "sailor_judge.json"), root)
        cache = Cache(env("PP_BRIDGE_CACHE", os.path.join(root, "data", "ai_cache", "bridge")))
        talk = TalkJudge(root=root, cache=cache, judge=judge_doc)
    else:
        judge_doc = talk.judge
        cache = talk.cache
    hearer = Hearer(cache=cache)
    print("ai_bridge selftest, %s, python %s" % (utc_stamp(), sys.version.split()[0]))
    print("judge %s version %d, system %d chars, limits %d lines of %d"
          % (_display_path(judge_doc.path, root), judge_doc.version, len(judge_doc.system),
             judge_doc.max_lines, judge_doc.max_chars))
    print("budget %.1f s, cache %s" % (talk.budget, _display_path(cache.folder, root)))
    ok = True
    if env("PP_AI_MODE", "record").lower() != "replay":
        # A cold local model is the local rung's whole failure mode, and it is not a code fault: measured on
        # this PC 2026-10-26, the first call to an unloaded model took 11 to 85 s, and while the load was
        # aborted LM Studio answered 400 to the bridge's request. The local rung's share of the 6 s budget is
        # 5.6 s, so a ladder run against a cold server can only label it unavailable. Load the weights first.
        print("\nWARM UP")
        try:
            warm = talk.warm_local(budget=env_float("PP_SELFTEST_WARM", 120.0))
            print("  %s loaded in %d ms at %s" % (warm["model"], warm["ms"], warm["url"]))
        except BridgeError as exc:
            print("  unavailable: %s" % redact(exc))
    line = _selftest_line(talk)
    print("\nTHE LADDER (line: %r)" % line)
    for row in _ladder_report(talk, cache, line=line):
        if row["result"] == "answered":
            print("  %-13s %-6s %-13s %+3d  %s"
                  % (row["rung"], "OK", row["source"], row["will_delta"],
                     " / ".join(row["reply"] or [])))
            print("  %-13s %s model=%s %d ms" % ("", "", row["model"] or "-", row["latency_ms"]))
        else:
            print("  %-13s %-6s %s: %s" % (row["rung"], row["result"], "", row.get("detail", "")))
            if row["rung"] in ("cache",):
                ok = ok and True  # a cache miss on a fresh line is not a failure
    print("\nA FULL REQUEST THROUGH THE LADDER")
    answer = talk.judge_talk({"encounter_id": "tutorial_sailors", "npc": "navy_sailor",
                              "player_text": line})
    print("  source=%s verdict=%s will_delta=%+d %d ms" % (answer["source"], answer["verdict"],
                                                           answer["will_delta"],
                                                           answer["latency_ms"]))
    print("  reply=%r" % (answer["reply"],))
    print("  tried=%s" % json.dumps(answer["tried"]))
    if answer["source"] == "fallback":
        ok = False
        print("  FAIL every rung failed, so only the encounter fallback answered")
    print("\nHEALTH")
    print("  " + json.dumps(health(judge_doc, hearer), sort_keys=True))
    print("\nVOICE")
    sample = wav_path or env("PP_SELFTEST_WAV")
    if not sample:
        found = os.path.join(root, "output", "ai_bridge", "selftest_speech.wav")
        sample = found if os.path.isfile(found) else ""
    if sample and os.path.isfile(sample):
        with open(sample, "rb") as handle:
            wav = handle.read()
        try:
            transcript, model, cached, latency = hearer.transcribe(wav)
            print("  /hear %s -> %r (%s, %d ms%s)" % (os.path.basename(sample), transcript, model,
                                                     latency, ", cached" if cached else ""))
            if not transcript:
                print("  note: empty transcript, which is right for silence and wrong for speech")
        except BridgeError as exc:
            ok = False
            print("  FAIL /hear: %s" % redact(exc))
    else:
        print("  no sample wav (pass --wav PATH or PP_SELFTEST_WAV): /hear was not exercised")
        print("  one is easy to make on this PC with the Windows voice; docs/AI-BRIDGE.md shows the command")
    print("\nSELFTEST %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def cpu_busy_percent(sample_seconds=0.3):
    """How busy this machine was while the table was measured, because a local model's speed is the box's.

    Measured 2026-10-26: the same model, same prompt, answered in 1.1 to 2.2 s on an idle box and 2.5 to 8 s
    while other lanes were compiling, so a latency table without the load beside it is not a measurement.
    Returns None where the platform cannot answer (the offloaded Linux run, for instance).
    """
    try:
        import ctypes

        class _FileTime(ctypes.Structure):
            _fields_ = [("low", ctypes.c_uint32), ("high", ctypes.c_uint32)]

        def times():
            idle, kernel, user = _FileTime(), _FileTime(), _FileTime()
            ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel),
                                                 ctypes.byref(user))
            value = lambda ft: (ft.high << 32) | ft.low
            return value(idle), value(kernel), value(user)

        before = times()
        time.sleep(sample_seconds)
        after = times()
        idle = after[0] - before[0]
        total = (after[1] - before[1]) + (after[2] - before[2])
        return round(100.0 * (1.0 - float(idle) / float(total)), 1) if total else None
    except Exception:
        try:
            return round(100.0 * os.getloadavg()[0] / max(1, os.cpu_count() or 1), 1)
        except Exception:
            return None


def latency_table(root=None, lines=10, rounds=1):
    """The measured table the card asks for: Meta, local model and replay, per line, in milliseconds."""
    root = root or ROOT
    judge_doc = Judge(os.path.join(root, "data", "talk", "sailor_judge.json"), root)
    cache = Cache(env("PP_BRIDGE_CACHE", os.path.join(root, "data", "ai_cache", "bridge")))
    talk = TalkJudge(root=root, cache=cache, judge=judge_doc)
    rows = []
    for text in list(SELFTEST_LINES)[:max(1, lines)]:
        payload = {"encounter_id": "tutorial_sailors", "npc": "navy_sailor", "player_text": text}
        for name in ("meta", "open-weights", "replay"):
            started = time.monotonic()
            task = build_task(judge_doc, talk.cards, talk.encounters, payload)
            rung = {"meta": talk._rung_meta, "open-weights": talk._rung_local,
                    "replay": talk._rung_cache}[name]
            try:
                answer = talk._run(rung, task, max(0.5, talk._share(name, talk.budget)),
                                   time.monotonic() + talk.budget)
                status = "answered"
                detail = answer.get("source", name)
            except BridgeError as exc:
                status, detail = type(exc).__name__, redact(exc)
            rows.append({"line": text, "rung": name, "status": status, "detail": detail,
                         "ms": int(round((time.monotonic() - started) * 1000))})
    print("| line | rung | result | ms |")
    print("| --- | --- | --- | --- |")
    for row in rows:
        print("| %s | %s | %s | %d |" % (row["line"][:44], row["rung"], row["status"], row["ms"]))
    busy = cpu_busy_percent()
    answers = [row["ms"] for row in rows if row["rung"] == "open-weights" and row["status"] == "answered"]
    replays = [row["ms"] for row in rows if row["rung"] == "replay" and row["status"] == "answered"]
    summary = {"cpu_busy_percent": busy, "budget_s": talk.budget,
               "local_answered": len(answers), "local_min_ms": min(answers) if answers else None,
               "local_max_ms": max(answers) if answers else None,
               "local_median_ms": sorted(answers)[len(answers) // 2] if answers else None,
               "replay_answered": len(replays), "replay_max_ms": max(replays) if replays else None}
    print("\ncpu busy at measurement: %s percent, budget %.1f s" % (busy, talk.budget))
    print("open-weights: %d of %d answered, %s to %s ms, median %s ms"
          % (len(answers), len([r for r in rows if r["rung"] == "open-weights"]),
             summary["local_min_ms"], summary["local_max_ms"], summary["local_median_ms"]))
    print("replay: %d of %d answered, worst %s ms"
          % (len(replays), len([r for r in rows if r["rung"] == "replay"]), summary["replay_max_ms"]))
    out = os.path.join(root, "data", "talk", "bridge_latency.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump({"measured_at": utc_stamp(), "python": sys.version.split()[0], "summary": summary,
                   "budget_s": talk.budget, "rows": rows}, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("\nwrote %s" % os.path.relpath(out, root))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="The local talk and voice bridge for Primordial Paradox.")
    parser.add_argument("--serve", action="store_true", help="bind 127.0.0.1 and serve until stopped")
    parser.add_argument("--selftest", action="store_true", help="print every rung and one /hear call")
    parser.add_argument("--latency", action="store_true", help="measure the 10 line latency table")
    parser.add_argument("--once", metavar="LINE", help="one /talk call, printed, no server")
    parser.add_argument("--lines", type=int, default=10, help="lines to measure with --latency")
    parser.add_argument("--wav", metavar="PATH", help="a wav for --selftest's /hear call")
    parser.add_argument("--warm", action="store_true",
                        help="load the open weights model at startup, off the request path")
    parser.add_argument("--port", type=int, default=None, help="override PP_BRIDGE_PORT")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest(wav_path=args.wav, port=args.port or 0)
    if args.latency:
        return latency_table(lines=args.lines)
    judge_doc = Judge()
    cache = Cache()
    if args.once:
        answer = TalkJudge(cache=cache, judge=judge_doc).judge_talk({"player_text": args.once})
        print(json.dumps(answer, indent=2, sort_keys=True))
        return 0
    if args.serve:
        hearer = Hearer(cache=cache)
        talk = TalkJudge(cache=cache, judge=judge_doc)
        # Import the Meta client now, not inside the first turn: a cold import measured 1.4 s on this PC on
        # 2026-10-26, and that came out of the first player's 6 s budget. The rung still imports it lazily, so a
        # machine without the module reports it per call instead of failing to start.
        try:
            import meta_client
            print("ai_bridge: meta client ready (backend %s, key %s)"
                  % (meta_client.backend_name(), "present" if meta_client.key_present() else "absent"),
                  flush=True)
        except Exception as exc:  # pragma: no cover - only a broken install gets here
            print("ai_bridge: meta client not importable (%s); the first rung will report it per call"
                  % redact(exc), flush=True)
        server = serve(talk, hearer, port=args.port)
        print("ai_bridge listening on %s:%d (loopback only); judge %s"
              % (server.server_address[0], server.server_address[1],
                 os.path.relpath(judge_doc.path, ROOT)), flush=True)
        if args.warm:
            def _warm():
                try:
                    info = talk.warm_local()
                    server.note("ai_bridge warm: model %s at %s loaded in %d ms"
                                % (info["model"], info["url"], info["ms"]))
                    # Keep it loaded for the whole session: LM Studio drops an idle model, and a dropped model
                    # turns a 2 s turn into a 25 s one (measured, see keep_local_warm).
                    threading.Thread(target=talk.keep_local_warm, name="bridge-keepalive",
                                     daemon=True).start()
                except BridgeError as exc:
                    server.note("ai_bridge warm: open weights not warmed (%s)" % redact(exc))
                # The whisper worker loads faster-whisper's model when it starts, which took 5 to 12 s on this
                # PC, so starting it now means the first spoken line is a warm one (about 0.44 s) rather than a
                # stall in the middle of the demo.
                started = time.monotonic()
                if hearer.available():
                    server.note("ai_bridge warm: whisper worker ready in %d ms (model %s, interpreter %s)"
                                % (int(round((time.monotonic() - started) * 1000)), hearer.model,
                                   hearer.interpreter))
                else:
                    server.note("ai_bridge warm: no whisper interpreter (%s)" % hearer._last_error)
            threading.Thread(target=_warm, name="bridge-warm", daemon=True).start()
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            print("ai_bridge stopping", flush=True)
        finally:
            hearer.stop()
            server.server_close()
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
