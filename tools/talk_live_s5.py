#!/usr/bin/env python3
"""talk_live_s5.py: ask the local bridge for S5's three verdicts, and write down what it said.

Why this file exists
    Shot S5 of the 180 s cut is Captain Morgan's fight, and the claim it carries is knowledge/DEMO-SCRIPT.md
    section 4's: "the person judging your line is a Meta model answering inside a NES text box". Until this
    tool existed the box drew the three effects data/meta_bake.json holds, and those three rows are
    `source: fallback` hand written lines, which the overlay prints as exactly that. The judge panel of
    2026-11-17 (fix 2) asked for the verdict to come from the bridge at the moment the shot is drawn. This
    tool is that call: it asks tools/ai_bridge.py's own TalkJudge for the three turns of S5, in order, with
    the history and the MERCY the take had, and it writes the answers down with the labels the bridge put
    on them.

    Nothing in this file decides a verdict. Every word in the record is a field of the bridge's answer.
    data/meta_bake.json is read for one thing only: the effect each turn's row records, so a reader can see
    whether the live answer agrees with the take. The bake is the fallback the game itself uses when the
    bridge is down, and it is the fallback this record names when the bridge answers nothing.

What is written
    output/demo/talk_live_s5.json

        Not data/demo/: every JSON under data/ is a build input, tests/test_no_network_in_build.py refuses an
        endpoint and a key name in the build, and this record names the endpoint it asked and the rungs it
        tried. It is a cut artifact, so it lives with the cut's other products, and the drawing falls back to
        data/meta_bake.json when it is absent (measured: tools/check_project.py refused the file under data/,
        test_the_build_holds_no_endpoint_no_key_and_no_live_call named it twice).

        header   format, kind, version, owner, card, when (UTC), judge version, the endpoint asked, the
                 rungs the bridge tried for every turn, `live` (true only when every turn was answered by a
                 live rung: meta or open-weights), and a sentence saying what the file is
        turns    one row per turn: the player's line as data/dialogue/all.json's talk_morgan holds it, the
                 bake row that answers that turn, the effect the row records and the MERCY it moves, the
                 MERCY before the turn, the bridge's whole answer (verdict, effect, will_delta, reply,
                 source, origin, model, cached, latency_ms, tried), and `agrees` (the live effect is the
                 effect the take moved)

    A file that says `live: false` is a record of a bridge that had no live rung to answer with, which on a
    machine with no Meta key and no local model is the honest state and not a failure to hide.

Usage
    python tools\\talk_live_s5.py                  ask the bridge, write the record
    python tools\\talk_live_s5.py --check          print the table, write nothing
    python tools\\talk_live_s5.py --require-live   exit 3 unless every turn came from a live rung
    python tools\\talk_live_s5.py --require-agree  exit 4 unless every live effect is the take's own effect
    python tools\\talk_live_s5.py --read           print the record already on disk, ask nothing

Exit codes
    0  the record was written, or the table was printed, or the file on disk was read
    1  a source file is missing or carries no row this tool needs, so a record would have been invented
    2  bad argument
    3  --require-live and at least one turn was not answered by a live rung
    4  --require-agree and at least one live effect is not the effect the take moved
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

ENCOUNTERS_PATH = os.path.join(ROOT, "data", "encounters", "all.json")
DIALOGUE_PATH = os.path.join(ROOT, "data", "dialogue", "all.json")
BAKE_PATH = os.path.join(ROOT, "data", "meta_bake.json")
JUDGE_PATH = os.path.join(ROOT, "data", "talk", "sailor_judge.json")
OUT_PATH = os.path.join(ROOT, "output", "demo", "talk_live_s5.json")

ENCOUNTER_ID = "morgan_gate"
NPC = "morgan"
OPTIONS_ID = "talk_morgan"
TURN_ROWS = ("fight/morgan/1", "fight/morgan/2", "fight/morgan/3")
LIVE_SOURCES = ("meta", "open-weights")


class RecordError(Exception):
    """The record cannot be written honestly: a source row is missing or does not say what it must."""


def read_json(path):
    if not os.path.isfile(path):
        raise RecordError("%s does not exist, so there is nothing to ask or record" % path)
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


def player_lines(path=DIALOGUE_PATH, options_id=OPTIONS_ID):
    """The three lines the player picks in S5, as the dialogue row holds them, without the marker and quotes.

    The row is the game's own: `* "May I see the form?"` is what the panel draws, so the line that goes to the
    bridge is the same words with the narration marker and the quotes taken off, and nothing is retyped here.
    """
    data = read_json(path)
    # The file names its list by kind: data/dialogue/all.json's own key is "dialogue" (format 1, kind dialogues),
    # and a copy that names it something else is read the same way rather than refused on a key name.
    entries = None
    if isinstance(data, dict):
        for key in ("dialogue", "entries", "rows"):
            if isinstance(data.get(key), list):
                entries = data[key]
                break
    if not isinstance(entries, list):
        raise RecordError("%s holds no dialogue list" % rel(path))
    for row in entries:
        if not isinstance(row, dict) or row.get("id") != options_id:
            continue
        lines = row.get("lines")
        if not isinstance(lines, list) or not lines:
            raise RecordError("%s's row %r holds no lines" % (rel(path), options_id))
        out = []
        for line in lines:
            text = str(line).strip()
            if text.startswith("* "):
                text = text[2:]
            text = text.strip()
            if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
                text = text[1:-1]
            if not text:
                raise RecordError("%s's row %r carries an empty line" % (rel(path), options_id))
            out.append(text)
        return out
    raise RecordError("%s holds no dialogue row %r, and S5's three lines are that row's" % (rel(path), options_id))


def encounter_talk(path=ENCOUNTERS_PATH, encounter_id=ENCOUNTER_ID):
    """The encounter's own mercy table and talk block: what the take moves, and what the bridge is told."""
    data = read_json(path)
    rows = data.get("encounters") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise RecordError("%s holds no encounters list" % rel(path))
    for row in rows:
        if not isinstance(row, dict) or row.get("id") != encounter_id:
            continue
        talk = row.get("talk")
        if not isinstance(talk, dict):
            raise RecordError("%s's encounter %r carries no talk block, so no talk turn is judged"
                              % (rel(path), encounter_id))
        mercy = row.get("talk_mercy")
        if not isinstance(mercy, dict):
            raise RecordError("%s's encounter %r carries no talk_mercy table, so a turn moves no known number"
                              % (rel(path), encounter_id))
        return row, talk, mercy
    raise RecordError("%s holds no encounter %r" % (rel(path), encounter_id))


def bake_rows(path=BAKE_PATH, row_ids=TURN_ROWS):
    """The three rows the take drew: their recorded effect, the text the box showed, and the request hash."""
    data = read_json(path)
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise RecordError("%s holds no rows list" % rel(path))
    index = {row.get("id"): row for row in rows if isinstance(row, dict) and row.get("id")}
    out = []
    for row_id in row_ids:
        row = index.get(row_id)
        if row is None:
            raise RecordError("%s holds no row %r, and S5's turns are those rows" % (rel(path), row_id))
        effect = row.get("effect")
        if not isinstance(effect, str) or not effect:
            raise RecordError("%s's row %r carries no effect, so the take's own verdict is unknown"
                              % (rel(path), row_id))
        out.append(row)
    return out


def judge_version(path=JUDGE_PATH):
    data = read_json(path)
    version = data.get("version") if isinstance(data, dict) else None
    if not isinstance(version, int):
        raise RecordError("%s carries no integer version, so a recorded answer cannot name its prompt"
                          % rel(path))
    return version


def ask(turns, will_before):
    """One bridge call per turn, in order, with the history the bridge keys its turn number on."""
    import ai_bridge

    talk = ai_bridge.TalkJudge()
    history = []
    answers = []
    for index, turn in enumerate(turns):
        payload = {
            "encounter_id": ENCOUNTER_ID,
            "npc": NPC,
            "player_text": turn["player_text"],
            "history": history,
            "will": will_before[index],
            "mood": "guarded",
        }
        answer = talk.judge_talk(payload)
        if not isinstance(answer, dict):
            raise RecordError("the bridge answered turn %d with %r, and a record needs an answer"
                              % (index + 1, answer))
        for field in ("verdict", "will_delta", "reply", "source"):
            if field not in answer:
                raise RecordError("the bridge's answer for turn %d carries no %r field" % (index + 1, field))
        answers.append(answer)
        history.append({"player_text": turn["player_text"], "reply": answer.get("reply") or [],
                        "verdict": answer.get("verdict")})
    return answers, [name for name, _ in talk.rungs()], talk.budget


def build_record(turns, will_before, will_after, answers, rungs, budget, judge, endpoint):
    rows = []
    for index, turn in enumerate(turns):
        answer = answers[index]
        effect = answer.get("effect")
        rows.append({
            "turn": index + 1,
            "row": turn["row"],
            "player_text": turn["player_text"],
            "recorded_effect": turn["effect"],
            "recorded_mercy": turn["mercy"],
            "will_before": will_before[index],
            "will_after": will_after[index],
            "recorded_reply": turn["text"],
            "answer": {
                "verdict": answer.get("verdict"),
                "effect": effect,
                "will_delta": answer.get("will_delta"),
                "reply": answer.get("reply") or [],
                "source": answer.get("source"),
                "origin": answer.get("origin"),
                "mood": answer.get("mood"),
                "model": answer.get("model") or "",
                "cached": bool(answer.get("cached")),
                "latency_ms": answer.get("latency_ms"),
                "tried": answer.get("tried") or [],
            },
            "agrees": bool(effect) and effect == turn["effect"],
        })
    live = all(row["answer"]["source"] in LIVE_SOURCES for row in rows)
    return {
        "format": 1,
        "kind": "talk_live_s5",
        "version": 1,
        "owner": "gamedev",
        "card": "judge panel 2026-11-17, fix 2 (the S5 verdict comes from the bridge at draw time)",
        "rule": (
            "Every word in a turn's answer is a field of tools/ai_bridge.py's own /talk answer for that line, "
            "asked in order with the history and the MERCY the take had. Nothing here types a verdict. "
            "data/meta_bake.json is read for the effect each turn's row records, so `agrees` says whether the "
            "live answer is the effect the take moved, and the bake is the game's own fallback when the bridge "
            "has no live rung to answer with. Rewrite this file by running the tool, never by hand."),
        "when": utc_stamp(),
        "judge_version": judge,
        "endpoint": endpoint,
        "budget_seconds": budget,
        "rungs": rungs,
        "live": live,
        "note": (
            "live is true only when every turn was answered by meta or open-weights. replay and fallback are "
            "labelled exactly as the bridge labels them, because an answer read back from a cache or written "
            "by the encounter is not a model answering now."),
        "turns": rows,
    }


def utc_stamp():
    import datetime

    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def table(record):
    """The record as lines, for --check and --read: one line per turn and one for the file's own state."""
    lines = ["%s  live %s  judge v%s  endpoint %s"
             % (record.get("when", "?"), "yes" if record.get("live") else "no",
                record.get("judge_version", "?"), record.get("endpoint", "?"))]
    for row in record.get("turns") or []:
        answer = row.get("answer") or {}
        lines.append("turn %d  %-24r  take %-8s live %-8s %-10s %5s ms  agrees %s"
                     % (row.get("turn"), row.get("player_text"), row.get("recorded_effect"),
                        answer.get("effect") or "(none)", answer.get("source") or "?",
                        answer.get("latency_ms"), "yes" if row.get("agrees") else "no"))
    return lines


def will_chain(rows, mercy):
    """The MERCY before and after each turn, from the effects the take's own rows record."""
    before = []
    after = []
    value = 0
    for row in rows:
        effect = row["effect"]
        if effect not in mercy:
            raise RecordError("row %r's effect %r is not a key of the encounter's talk_mercy table"
                              % (row.get("id"), effect))
        before.append(value)
        value = max(0, min(100, value + int(mercy[effect])))
        after.append(value)
    return before, after


def main(argv=None):
    parser = argparse.ArgumentParser(description="ask the local bridge for S5's three verdicts and record them")
    parser.add_argument("--out", default=OUT_PATH, help="where the record is written")
    parser.add_argument("--check", action="store_true", help="ask the bridge, print the table, write nothing")
    parser.add_argument("--read", action="store_true", help="print the record on disk and ask nothing")
    parser.add_argument("--require-live", action="store_true",
                        help="exit 3 unless every turn was answered by a live rung")
    parser.add_argument("--require-agree", action="store_true",
                        help="exit 4 unless every live effect is the effect the take moved")
    args = parser.parse_args(argv)

    if args.read:
        record = read_json(args.out)
        for line in table(record):
            print(line)
        return 0

    lines = player_lines()
    rows = bake_rows()
    if len(lines) != len(rows):
        raise RecordError("data/dialogue/all.json's %r holds %d lines and S5 has %d bake rows, so the record "
                          "cannot say which line answers which turn" % (OPTIONS_ID, len(lines), len(rows)))
    _encounter, talk, mercy = encounter_talk()
    if talk.get("options_dialogue") != OPTIONS_ID:
        raise RecordError("the encounter's talk block names options_dialogue %r and this tool reads %r"
                          % (talk.get("options_dialogue"), OPTIONS_ID))
    turns = []
    for line, row in zip(lines, rows):
        turns.append({"player_text": line, "row": row["id"], "effect": row["effect"],
                      "text": row.get("text") or [], "mercy": mercy[row["effect"]]})
    before, after = will_chain(rows, mercy)
    answers, rungs, budget = ask(turns, before)
    endpoint = os.environ.get("PP_LOCAL_URL") or "http://127.0.0.1:51235/v1"
    record = build_record(turns, before, after, answers, rungs, budget, judge_version(), endpoint)
    for line in table(record):
        print(line)

    if not args.check:
        out_dir = os.path.dirname(os.path.abspath(args.out))
        if out_dir and not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print("wrote %s" % rel(args.out))

    if args.require_live and not record["live"]:
        print("REFUSED  not every turn was answered by a live rung")
        return 3
    if args.require_agree and not all(row["agrees"] for row in record["turns"]):
        print("REFUSED  a live effect is not the effect the take moved")
        return 4
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RecordError as error:
        print("REFUSED  %s" % error)
        sys.exit(1)
