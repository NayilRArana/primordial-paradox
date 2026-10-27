"""Measure an open weights model on the game's 20 talk lines, through the game's own prompt.

The prompt is built by tools/ai_bridge.py itself (build_task), with the judge file's system_local
text and the same local_request the bridge merges into its payload, so a number here is the number
the game would get from that endpoint.

Every line is appended to the out file as one JSON object as soon as it lands, so a run that is
stopped keeps what it measured. Pass --resume to skip the lines already in the file.

    python tools/bench_open_weights.py --endpoint http://127.0.0.1:8931/v1 --model local \
        --out output/open_weights/rows.jsonl --resume

Card W3, lane research-assistant, 2026-10-26. The measurements this produced are in
knowledge/OPEN-WEIGHTS-2026-10-26.md.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import ai_bridge as A  # noqa: E402

FIXTURE_LINES = [
    ("deck_hound", "off topic", "none", "do you know the way to the galley"),
    ("deck_hound", "plain rudeness", "setback", "stupid animal, get out of my way"),
    ("navy_sailor", "off topic", "none", "what time does the galley open"),
    ("navy_sailor", "plain rudeness", "setback", "you are a waste of a uniform"),
    ("navy_sailor", "kind but unmoving", "none", "i hope your night gets better"),
]

ENCOUNTER = {"navy_sailor": "tutorial_sailors", "deck_hound": "deck_hound"}


def load_lines(root=ROOT):
    """15 lines the cards author (weak topics land, strong topics set back) plus 5 with a named intent."""
    cards = A.load_cards(root)
    rows = []
    for card_id in ("deck_hound", "navy_sailor"):
        card = cards[card_id]
        for pool, intent in (("weak_topics", "soften"), ("strong_topics", "setback")):
            for topic in card.get(pool) or []:
                for example in topic.get("examples") or []:
                    rows.append({"card": card_id, "topic": topic.get("topic", ""), "pool": pool,
                                 "intent": intent, "player_line": " ".join(str(example).split())})
    for card_id, topic, intent, line in FIXTURE_LINES:
        rows.append({"card": card_id, "topic": topic, "pool": "fixture", "intent": intent,
                     "player_line": line})
    for index, row in enumerate(rows, start=1):
        row["n"] = index
    return rows


def post(endpoint, payload, timeout):
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(endpoint.rstrip("/") + "/chat/completions", data=body,
                                     headers={"Content-Type": "application/json"})
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8", "replace")
    return json.loads(raw), time.monotonic() - started


def append(path, record):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def already_done(path):
    done = set()
    if not os.path.exists(path):
        return done
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                done.add(json.loads(line)["n"])
            except (ValueError, KeyError):
                continue
    return done


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8931/v1")
    parser.add_argument("--model", default="local")
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--max-tokens", type=int, default=0,
                        help="0 uses the judge file's local_request max_tokens")
    parser.add_argument("--kwargs", default="",
                        help='chat_template_kwargs, e.g. {"reasoning_strength":"low"}')
    parser.add_argument("--prefill", default="",
                        help="text put on a final assistant turn so a reasoning model answers inside the JSON")
    parser.add_argument("--tag", default="")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    judge = A.Judge()
    cards = A.load_cards()
    encounters = A.load_encounters()
    rows = load_lines()[:args.limit]
    done = already_done(args.out) if args.resume else set()
    print("judge version", judge.version, "lines", len(rows), "already done", sorted(done))

    for row in rows:
        if row["n"] in done:
            print("%2d skip" % row["n"])
            continue
        task = A.build_task(judge, cards, encounters,
                            {"encounter_id": ENCOUNTER[row["card"]], "npc": row["card"],
                             "player_text": row["player_line"], "will": 0, "mood": "guarded"})
        payload = {"model": args.model, "messages": list(task["messages_local"]),
                   "temperature": 0.0, "max_tokens": 140, "stream": False}
        if args.prefill:
            payload["messages"] = list(task["messages_local"]) + [
                {"role": "assistant", "content": args.prefill}]
        for key, value in (judge.local_request or {}).items():
            payload[key] = value
        if args.max_tokens:
            payload["max_tokens"] = args.max_tokens
        if args.kwargs:
            payload["chat_template_kwargs"] = json.loads(args.kwargs)

        record = {"n": row["n"], "card": row["card"], "topic": row["topic"], "pool": row["pool"],
                  "intent": row["intent"], "player_line": row["player_line"],
                  "endpoint": args.endpoint, "model": args.model, "tag": args.tag,
                  "prefill": args.prefill,
                  "prompt_chars": sum(len(m["content"]) for m in payload["messages"]),
                  "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        try:
            data, elapsed = post(args.endpoint, payload, args.timeout)
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")[:300]
            record.update({"ok": False, "error": "HTTP %s: %s" % (error.code, detail),
                           "latency_s": None})
            print("%2d HTTP ERROR %s %s" % (row["n"], error.code, detail[:120]))
            append(args.out, record)
            continue
        except Exception as error:  # noqa: BLE001 - a failed line is recorded, not raised
            record.update({"ok": False, "error": "%s: %s" % (type(error).__name__, error),
                           "latency_s": None})
            print("%2d ERROR %s" % (row["n"], record["error"][:140]))
            append(args.out, record)
            continue

        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        continuation = (message.get("content") or "").strip()
        content = (args.prefill + continuation).strip() if args.prefill else continuation
        usage = data.get("usage") or {}
        record.update({"latency_s": round(elapsed, 3), "finish_reason": choice.get("finish_reason"),
                       "usage": usage, "content": content[:1500],
                       "continuation": continuation[:400],
                       "reasoning_chars": len(message.get("reasoning_content") or "")})

        parsed = None
        used = content
        parse_error = ""
        for candidate in ([continuation, content] if args.prefill else [content]):
            try:
                parsed = A.parse_json_object(candidate)
                used = candidate
                break
            except A.BadReply as error:
                parse_error = str(error)
        if parsed is None:
            record.update({"ok": False, "error": "unparseable: %s" % parse_error})
        else:
            raw_text = parsed.get("text")
            raw_lines = raw_text if isinstance(raw_text, list) else []
            record.update({
                "parsed": {key: parsed.get(key) for key in ("effect", "mood", "hint")},
                "raw_line_count": len(raw_lines),
                "raw_longest": max((len(str(item)) for item in raw_lines), default=0),
                "raw_all_caps": all(str(item) == str(item).upper() for item in raw_lines),
                "parsed_from": "continuation" if used is continuation else "prefill+continuation",
            })
            try:
                answer = A.answer_from_text(used, judge, task)
                record.update({"ok": True, "answer": answer,
                               "agrees": answer["effect"] == row["intent"],
                               "lines": len(answer["text"]),
                               "longest_line": max((len(x) for x in answer["text"]), default=0)})
            except A.BadReply as error:
                record.update({"ok": False, "error": str(error)})
        append(args.out, record)
        print("%2d %-8s want %-8s %6.1fs tok=%s lines=%s max=%s %s %s" % (
            row["n"], (record.get("parsed") or {}).get("effect"), row["intent"], elapsed,
            usage.get("completion_tokens"), record.get("raw_line_count"),
            record.get("raw_longest"), "AGREE" if record.get("agrees") else "differs",
            record.get("error") or ""))
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
