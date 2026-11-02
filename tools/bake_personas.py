#!/usr/bin/env python3
"""bake_personas: write the recorded answers for the three persona scenes ahead of time (card t_acae7c0a).

Why this tool exists, in one paragraph. The live talk outside a fight is the same door as the fight talk: a
line the player types goes to tools/ai_bridge.py, the bridge asks a model, and the answer comes back capped and
labelled. A demo laptop may have no key and no network, so the answers a judge sees have to be recorded first,
by this tool, through the same bridge and the same rungs. It sends every bake line of every persona in
data/talk_personas.json through the bridge's Meta rung (muse-spark-1.3 by default), which writes one
data/ai_cache/bridge/<sha256>.json per line as it goes, and it writes data/talk_personas_bake.json beside the
report the fight bake already keeps. Replay then answers all three personas with the network off.

The bake's deadline is not the game's deadline, and the difference is the whole reason this tool exists.
Measured on this PC 2026-10-26, muse-spark-1.3 answered a persona line in 5.4 s and 7.0 s, with the slowest
answer needing more than 15 s, and the game's own budget for a turn is 6 s (`data/talk_personas.json`'s
`budget_s`, `PP_TALK_TIMEOUT`, the bridge's default). A live Meta answer therefore cannot be relied on inside a
scene, which is exactly why the demo replays a baked answer. The recording may wait longer (45 s by default,
`--budget` to change it) because that waiting happened once, today; the report records both numbers as
`budget_s` and `live_budget_s` so nobody has to guess which one a row was made under.

What the report says, and what it refuses to say
================================================
The `bake` block is counted from the calls this run made, not from the environment:

    mode live      at least one line came back as a validated answer from a live call
    mode offline   no line did, whatever the environment allowed, and every row says why

`calls_attempted` counts calls actually made (a retry is a second call and is counted twice), `answered`
counts validated answers written as rows with text, and `fallback` counts the lines this run could not answer.
A row never claims a live call it did not make: a failed row carries its own `reason` and an empty `text`, and
a replayed row says `mode: replay` in its `transport` field.

Three modes, and none of them blocks the build
==============================================
    python tools\\bake_personas.py             # try the live call for every line, fall back per line
    python tools\\bake_personas.py --offline   # make no call at all, write the offline report
    python tools\\bake_personas.py --check     # re-read the file and refuse anything off contract

The key is read from the environment by tools/meta_client.py, never here and never printed. This file holds no
endpoint and no credential, and --check refuses the report if it finds a URL or a key name in it.

What --check refuses
====================
    1. a persona missing from the report, or fewer than fifteen rows for one, or a row for a persona the
       data file does not carry;
    2. a row whose text is over two lines of 28 characters, or holds a character the box cannot draw;
    3. a row whose text carries a token from the persona's own banned_words, or from
       data/talk_profanity.json, or a link, an address or a run of three digits;
    4. a live row whose recorded cache entry is missing, or whose cache entry holds different text, so a
       report can never promise a replay the commit cannot serve;
    5. a bake block that claims more than its rows did: live with calls_attempted 0, or offline with live rows;
    6. a key name, an endpoint or a URL anywhere in the file.

Usage
    python tools\\bake_personas.py
    python tools\\bake_personas.py --check
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import ai_bridge  # noqa: E402  the same door the game talks to
import talk_guard  # noqa: E402  the same profanity guard the fight talk uses

REPORT = os.path.join(ROOT, "data", "talk_personas_bake.json")
PERSONAS = os.path.join(ROOT, "data", "talk_personas.json")
PER_PERSONA = 15
# The bake's own deadline. The game's turn keeps data/talk_personas.json's 6 s; a recording may wait longer,
# because the waiting happened once, today, and not during a scene.
BAKE_BUDGET_S = 45.0
SUFFIXES = (".py", ".json", ".md")
# The names this report must never hold. They are written out here because a scan list has to name what it
# hunts for; tests/test_talk_personas.py allows a key name on the line that defines the scan list and nowhere
# else in a tool, so this constant is the one place in this file where the strings may appear.
KEY_ENVS = ("MODEL_API_KEY", "META_API_KEY")
KEY_NAMES = KEY_ENVS + ("GEMINI_API_KEY", "PP_AI_", "Bearer ")


def utc_stamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_key_from_user_environment():
    """Put the Windows user environment's Meta key into os.environ, without printing it.

    The same reader tools/judge_panel.py and tools/eye_drive.py carry. A worker shell is often spawned
    before setx reaches it, so the variable is missing here while the bake that wrote this report had it.
    HKCU\\Environment is the environment, not a key file, and the value never leaves this function except
    into os.environ, where tools/meta_client.py is the only reader.
    """
    for name in KEY_ENVS:
        if os.environ.get(name, "").strip():
            return "environment"
    try:
        import winreg
    except ImportError:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as handle:
            index = 0
            while True:
                try:
                    name, value, kind = winreg.EnumValue(handle, index)
                except OSError:
                    break
                index += 1
                if name.upper() not in KEY_ENVS:
                    continue
                if kind == winreg.REG_EXPAND_SZ and "%" in str(value):
                    value = os.path.expandvars(value)
                value = str(value or "").strip()
                if value:
                    os.environ[name.upper()] = value
                    return "user environment"
    except OSError:
        return None
    return None


def read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_doc(path=PERSONAS):
    doc = read_json(path)
    rows = doc.get("personas") if isinstance(doc, dict) else None
    if not isinstance(rows, list) or not rows:
        raise SystemExit("data/talk_personas.json has no personas array, so there is nothing to bake")
    return doc, rows


def plan(doc, rows):
    """Every (persona, line) the report must carry, in file order. Fifteen lines per persona, no more, no fewer."""
    cap = int(doc.get("answer_cap", {}).get("lines") or 2)
    units = []
    for row in rows:
        lines = [str(line).strip() for line in (row.get("lines") or []) if str(line).strip()]
        if len(lines) < PER_PERSONA:
            raise SystemExit("persona %r carries %d bake lines, and the card asks for %d"
                             % (row.get("id"), len(lines), PER_PERSONA))
        for line in lines[:PER_PERSONA]:
            units.append({"persona": str(row["id"]), "scene": row.get("scene"), "line": line})
    return units, cap


def make_box(cache=None, budget=None):
    """The bridge's own judge, with ONLY the Meta rung armed, so every row's provenance is one rung.

    The budget here is the BAKE's, not the game's. A recorded answer has already spent its latency on the bake
    day, so a recording may wait 20 seconds for a reply; a turn in a scene keeps the 6 second deadline in
    data/talk_personas.json, and this tool does not change it. Measured on this PC 2026-10-26: muse-spark-1.3
    answered a persona line in 5.4 s and 7.0 s, so the game's own 6 s deadline cannot carry a live Meta answer
    at all, and the live persona turn in a build is served by the cache. That is what the bake is for.
    """
    box = ai_bridge.TalkJudge(cache=cache or ai_bridge.Cache(),
                              budget=budget or BAKE_BUDGET_S)
    box._injected = [("meta", box._rung_meta)]
    return box


def bake_payload(box, persona_id, line, turn=1):
    return {"persona": persona_id, "player_text": line, "turn": turn, "mood": "guarded"}


def bake_live(box, units, attempts=2):
    """Send every line through the Meta rung. One retry per line, because a timeout is not a refusal."""
    started = time.monotonic()
    rows = []
    calls = 0
    answered = 0
    for unit in units:
        row = dict(unit, transport="live", text=[], effect="", mood="", repaired=[], model="", cache_key="",
                   latency_ms=0, reason="", calls_attempted=0)
        last = ""
        for attempt in range(1, attempts + 1):
            calls += 1
            row["calls_attempted"] = attempt
            payload = bake_payload(box, unit["persona"], unit["line"])
            try:
                answer = box.judge_talk(payload)
            except Exception as exc:  # a dead rung is a labelled row, never a crash mid bake
                last = "%s: %s" % (type(exc).__name__, ai_bridge.redact(str(exc)))
                continue
            # The key is deterministic, so the row can name the cache file replay will read without the door
            # having to return it. build_task is pure: same payload, same file, same key.
            task = ai_bridge.build_task(box.judge, box.cards, box.encounters, payload, personas=box.personas)
            entry = box.cache.read(task["key"]) or {}
            stored = entry.get("answer") or {}
            row.update({
                "text": [str(line) for line in (answer.get("reply") or [])],
                "effect": stored.get("effect") or "",
                "mood": answer.get("mood") or "",
                "model": answer.get("model") or "",
                "repaired": [str(name) for name in (stored.get("repaired") or [])],
                "cache_key": task["key"],
                "latency_ms": int(answer.get("latency_ms") or 0),
                "transport": "live" if entry.get("network") else "cached",
                "reason": "",
            })
            last = ""
            answered += 1
            break
        if last:
            row["reason"] = last
        rows.append(row)
        shown = " / ".join(str(line) for line in (row["text"] or []))
        print("  %-16s %-46s %s" % (unit["persona"], unit["line"][:46], ("ok " + shown) if shown else "no answer"))
    return rows, calls, answered, int(round((time.monotonic() - started) * 1000))


def bake_offline(doc, units, cap):
    """No call, no cache write. The rows say so, and each carries the persona's own fallback line, which is
    the answer a replay with an empty cache gives."""
    personas = {str(row["id"]): row for row in doc.get("personas") or []}
    rows = []
    for unit in units:
        persona = personas[unit["persona"]]
        pool = [str(line) for line in (persona.get("fallback_pool") or [])]
        index = int(ai_bridge.sha256_text(unit["line"])[:8], 16) % max(1, len(pool))
        rows.append(dict(unit, transport="offline", text=[pool[index]] if pool else [],
                         mood=(persona.get("mood_allowed") or ["guarded"])[0], effect="none", model="",
                         repaired=["offline_fallback"], cache_key="", latency_ms=0,
                         reason="no call: --offline", calls_attempted=0))
    return rows, 0, 0, 0


def bake_block(rows, calls, answered, elapsed_ms, budget=None):
    live = sum(1 for row in rows if row["transport"] == "live" and row["text"])
    cached = sum(1 for row in rows if row["transport"] == "cached" and row["text"])
    failed = len(rows) - answered
    network = live > 0
    mode = "live" if network else ("replay" if cached else "offline")
    if mode == "live":
        note = ("live: %d of %d lines are answers from the Meta client, each one validated through the bridge "
                "before it was written" % (answered, len(rows)))
        if cached:
            note += ", and %d of those were read back from the recorded cache" % cached
        if failed:
            note += "; the other %d line(s) had no answer and replay falls to the persona's own line" % failed
    elif mode == "replay":
        note = ("cached: %d of %d lines are answers read back from the recorded cache, so no request left "
                "this machine" % (answered, len(rows)))
    else:
        note = ("offline: %d call(s) were made and no line came back as a validated answer, so every row is "
                "the persona's own fallback line" % calls if calls else
                "offline: no call was made (--offline), so every row is the persona's own fallback line")
    return {
        "created_at": utc_stamp(),
        "mode": mode,
        "network": network,
        "model": ai_bridge.env("PP_META_MODEL") or "muse-spark-1.3",
        "budget_s": float(budget if budget is not None else BAKE_BUDGET_S),
        "live_budget_s": ai_bridge.DEFAULT_TALK_TIMEOUT,
        "calls_attempted": calls,
        "answered": answered,
        "fallback": failed,
        "rows": len(rows),
        "elapsed_ms": elapsed_ms,
        "note": note,
    }


def build_document(doc, rows, block):
    per = {}
    for row in rows:
        entry = per.setdefault(row["persona"], {"id": row["persona"], "scene": row.get("scene"),
                                                "rows": 0, "answered": 0, "calls_attempted": 0})
        entry["rows"] += 1
        entry["answered"] += 1 if row["text"] else 0
        entry["calls_attempted"] += int(row.get("calls_attempted") or 0)
    return {
        "format": 1,
        "kind": "talk_personas_bake",
        "owner": "gamedev",
        "card": "t_acae7c0a (META-NPC-TALK)",
        "rule": ("Written by tools/bake_personas.py only, never by hand. Every row is one bake line of one "
                 "persona sent through tools/ai_bridge.py's Meta rung, and the answer beside it is the answer "
                 "that rung returned, after the same cleaning and the same guards the live path applies. A row "
                 "with no text says why, and a row with text names the cache file that replays it."),
        "personas_file": "data/talk_personas.json",
        "personas_version": doc.get("version"),
        "cache": "data/ai_cache/bridge",
        "bake": block,
        "coverage": {"personas": len(per), "per_persona": sorted(per.values(), key=lambda row: row["id"])},
        "rows": rows,
    }


# ------------------------------------------------------------------ checking the report


def drawable(text, alphabet, max_lines, max_chars):
    """Why this text cannot be drawn in the box, or empty. The same rules the bridge cleans to."""
    if not isinstance(text, list) or not 1 <= len(text) <= max_lines:
        return "text is not 1 to %d lines" % max_lines
    allowed = set(alphabet)
    for line in text:
        if not isinstance(line, str) or not line:
            return "an empty line"
        if len(line) > max_chars:
            return "%r is over %d characters" % (line, max_chars)
        if any(ch not in allowed for ch in line):
            return "%r holds a character the box cannot draw" % line
    return ""


def check_file(path=REPORT, root=ROOT):
    """Re-read the report and refuse anything off contract. Returns the number of problems."""
    problems = []
    if not os.path.isfile(path):
        print("talk persona bake: missing %s, so replay has nothing to serve outside the fallback" % path)
        return 1
    doc = read_json(path)
    if doc.get("kind") != "talk_personas_bake":
        problems.append("kind is %r, not talk_personas_bake" % doc.get("kind"))
    source, personas = load_doc(os.path.join(root, "data", "talk_personas.json"))
    cap = source.get("answer_cap") or {}
    max_lines = int(cap.get("lines") or 2)
    max_chars = int(cap.get("chars") or 28)
    judge = ai_bridge.Judge(os.path.join(root, "data", "talk", "sailor_judge.json"), root)
    alphabet = judge.alphabet
    tokens = talk_guard.load_tokens()
    by_id = {str(row["id"]): row for row in personas}

    rows = doc.get("rows") or []
    per = {}
    seen = set()
    for index, row in enumerate(rows):
        persona = by_id.get(str(row.get("persona")))
        if persona is None:
            problems.append("row %d names persona %r, which the data file does not carry" % (index, row.get("persona")))
            continue
        key = (row.get("persona"), str(row.get("line") or "").strip().lower())
        if key in seen:
            problems.append("row %d repeats the line %r for %s" % (index, row.get("line"), row.get("persona")))
        seen.add(key)
        per[row["persona"]] = per.get(row["persona"], 0) + 1
        text = row.get("text") or []
        if not text:
            if not row.get("reason"):
                problems.append("row %d has no text and no reason" % index)
            continue
        why = drawable(text, alphabet, max_lines, max_chars)
        if why:
            problems.append("row %d: %s" % (index, why))
            continue
        hit = ai_bridge.banned_hit(text, {"banned_words": tuple(persona.get("banned_words") or ())})
        if hit:
            problems.append("row %d: %r is a banned word for %s" % (index, hit, row["persona"]))
        joined = " ".join(text).lower()
        profane = talk_guard.profane_hit(joined, tokens)
        if profane:
            problems.append("row %d carries the profanity token %r" % (index, profane))
        if "http" in joined or "www." in joined or "@" in joined or re.search(r"\d{3}", joined):
            problems.append("row %d carries a link, an address or a digit run" % index)
        if row.get("transport") == "live":
            key_name = str(row.get("cache_key") or "")
            entry_path = os.path.join(root, "data", "ai_cache", "bridge", "%s.json" % key_name)
            if not key_name:
                problems.append("row %d is labelled live and names no cache file" % index)
            elif not os.path.isfile(entry_path):
                problems.append("row %d is labelled live and its cache file is missing: %s.json" % (index, key_name))
            else:
                entry = read_json(entry_path)
                stored = (entry.get("answer") or {}).get("text") or []
                if [str(line) for line in stored] != [str(line) for line in text]:
                    problems.append("row %d and its cache file hold different text" % index)

    for persona_id in by_id:
        card = by_id[persona_id]
        if card.get("bake") is False:
            # Card t_330b12ce: a card may say it is not part of the baked list. The dock clerk answers inside the S5
            # cutscene through the scene's own path, so his lines are not pre-recorded here and are not missing.
            if per.get(persona_id, 0):
                problems.append("persona %s is marked bake false and still carries %d rows"
                                % (persona_id, per.get(persona_id, 0)))
            continue
        count = per.get(persona_id, 0)
        if count < PER_PERSONA:
            problems.append("persona %s has %d rows and the card asks for %d" % (persona_id, count, PER_PERSONA))

    block = doc.get("bake") or {}
    if not isinstance(block.get("calls_attempted"), int) or block["calls_attempted"] < 0:
        problems.append("the bake block has no calls_attempted count")
    live_rows = [row for row in rows if row.get("text") and row.get("transport") == "live"]
    if block.get("mode") == "live" and not live_rows:
        problems.append("the bake block claims live over zero live rows")
    if block.get("mode") == "live" and int(block.get("calls_attempted") or 0) <= 0:
        problems.append("the bake block claims live with calls_attempted 0")
    if block.get("mode") == "offline" and live_rows:
        problems.append("the bake block claims offline over %d live rows" % len(live_rows))
    if block.get("mode") == "live" and block.get("network") is not True:
        problems.append("the bake block claims live with network false")
    if block.get("mode") == "offline" and block.get("network") is not False:
        problems.append("the bake block claims offline with network true")
    if block.get("live_budget_s") != ai_bridge.DEFAULT_TALK_TIMEOUT:
        problems.append("the bake block's live_budget_s is not the game's own %s s deadline"
                        % ai_bridge.DEFAULT_TALK_TIMEOUT)

    blob = json.dumps(doc)
    for name in KEY_NAMES:
        if name in blob:
            problems.append("the report names a key environment variable: %s" % name)
    if re.search(r"https?://", blob):
        problems.append("the report holds a URL")

    for problem in problems:
        print("talk persona bake: %s" % problem)
    print("talk persona bake check: %d rows, %d problems, %d live, calls_attempted %s, mode %s"
          % (len(rows), len(problems), len(live_rows), block.get("calls_attempted"), block.get("mode")))
    return len(problems)


def run(offline=False, cache=None, budget=None):
    doc, rows = load_doc()
    units, cap = plan(doc, rows)
    budget = float(budget if budget is not None else BAKE_BUDGET_S)
    if not offline:
        print("talk persona bake: meta key from %s (value never printed)"
              % (load_key_from_user_environment() or "nowhere, so every row will say why"))
    box = make_box(cache=cache, budget=budget)
    tokens = talk_guard.load_tokens()  # a missing or short list stops the bake loudly (spec 19 layer D)
    if len(tokens) < 20:
        raise SystemExit("data/talk_profanity.json holds fewer than 20 tokens, so the guard cannot run")
    if offline:
        baked, calls, answered, elapsed = bake_offline(doc, units, cap)
    else:
        baked, calls, answered, elapsed = bake_live(box, units)
    block = bake_block(baked, calls, answered, elapsed, budget)
    document = build_document(doc, baked, block)
    with open(REPORT, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, indent=2, sort_keys=False)
        handle.write("\n")
    print("talk persona bake: %d rows, %d personas, mode %s, calls_attempted %d, answered %d, %.1f s"
          % (len(baked), len(document["coverage"]["per_persona"]), block["mode"], calls, answered, elapsed / 1000.0))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bake the persona talk answers through the bridge.")
    parser.add_argument("--offline", action="store_true", help="make no call, write the offline report")
    parser.add_argument("--check", action="store_true", help="re-read the report and refuse anything off contract")
    parser.add_argument("--budget", type=float, default=BAKE_BUDGET_S,
                        help="seconds the bake waits per call (the game's own turn keeps 6)")
    args = parser.parse_args(argv)
    if args.check:
        return 0 if check_file() == 0 else 1
    return run(offline=args.offline, budget=args.budget)


if __name__ == "__main__":
    raise SystemExit(main())
