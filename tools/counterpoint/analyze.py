"""Analyse a score's vertical intervals and print the counts, card t_c0597404 (M0).

    python tools/counterpoint/analyze.py assets/audio/pp_01_title_v7/pp_01_title_v7.mid
    python tools/counterpoint/analyze.py FILE --json out.json --limit 40
    python tools/counterpoint/analyze.py FILE --added-from OLDER.mid

--added-from names the previous version, so every clash that involves a note the newer build
ADDED is listed separately: that is the "what the injector added" column of the report.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import clash  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("midi")
    parser.add_argument("--json", default=None)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--added-from", default=None)
    parser.add_argument("--voices", default=None,
                        help="comma separated voices to judge against each other")
    parser.add_argument("--all", action="store_true", help="print every raw clash")
    args = parser.parse_args()

    score = clash.load_score(args.midi)
    voices = tuple(v.strip() for v in args.voices.split(",")) if args.voices else None
    events = clash.analyse(score, voices=voices)
    summary = clash.summarise(score, events)

    print("file   ", os.path.basename(args.midi))
    print("bars   ", score.bars, " bpm", round(score.tempo_bpm or 0, 2),
          " ticks/beat", score.ticks_per_beat, " bar", score.bar_ticks)
    print("voices ", ", ".join("%s(%d)" % (n, len(v)) for n, v in sorted(score.voices.items())))
    print("judged ", len(events), "dissonances")
    print()
    print("class            count")
    for name in clash.CLASSES:
        print("  %-14s %5d" % (name, summary["by_class"][name]))
    print()
    print("raw clash by pair")
    for key, count in sorted(summary["raw_by_pair"].items(), key=lambda kv: -kv[1]):
        print("  %-42s %4d" % (key, count))
    print()
    print("raw clashes per 8 bars")
    for block in range(1, summary["blocks_total"] + 1):
        count = summary["blocks"].get(block, 0)
        print("  blocks %2d (bars %2d-%2d) %3d %s"
              % (block, (block - 1) * 8 + 1, block * 8, count, "#" * min(count, 50)))
    print()
    print("raw clashes on a strong beat:", summary["strong_raw"])
    for event in summary["strong_raw_events"][:12]:
        print("   bar %2d beat %.2f %-14s %-4s / %-14s %-4s %-6s %s"
              % (event["bar"], event["beat"], event["low_voice"], event["low"],
                 event["high_voice"], event["high"], event["ic_name"], event["why"]))
    if summary["strong_raw"] > 12:
        print("   ... %d more" % (summary["strong_raw"] - 12))

    raws = [e for e in events if e["class"] == "raw clash"]
    if args.added_from:
        added = clash.added_notes(args.midi, args.added_from)
        for event in raws:
            event["added"] = any((event["voice"], event["tick"], clash.name_pitch(p))
                                 in added for p in (event["low"], event["high"]))
        hit = [e for e in raws if e["added"]]
        print()
        print("raw clashes that involve a note the newer build added: %d of %d" % (len(hit), len(raws)))
        for event in hit:
            print("   bar %2d beat %.2f %-14s %-4s / %-14s %-4s %-6s %s"
                  % (event["bar"], event["beat"], event["low_voice"], event["low"],
                     event["high_voice"], event["high"], event["ic_name"], event["why"]))

    print()
    shown = raws if args.all else raws[:args.limit]
    print("raw clashes, first %d of %d" % (len(shown), len(raws)))
    for event in shown:
        res = event["resolution"]
        first = res.get("subject") or res.get("attacker") or {}
        print("   bar %2d beat %.2f %-7s %-14s %-4s / %-14s %-4s %-6s -> %-4s %s"
              % (event["bar"], event["beat"], event["weight"], event["low_voice"],
                 event["low"], event["high_voice"], event["high"], event["ic_name"],
                 first.get("to", "-"), event["why"]))

    if args.json:
        payload = {
            "file": args.midi, "bars": score.bars, "key": score.key_name,
            "summary": {k: summary[k] for k in
                        ("by_class", "raw_by_pair", "blocks", "blocks_total",
                         "raw_total", "strong_raw", "dissonances")},
            "events": events,
        }
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1)
        print("json", args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
