"""Build knowledge/META-SPEND.md from the live entries in data/ai_cache (card t_5031b766).

Prices are the documented list prices (arananet/meta-hackathon/HACKATHON-BRIEF.md section 3.2,
read 2026-10-21, itself from https://dev.meta.ai/docs/pricing-rate-limits):
    muse-spark-1.3  1.25 USD per 1M fresh input tokens, 0.15 per 1M cached input, 4.25 per 1M output
    muse-image-1.0  0.01 USD per generated or edited image, flat
    sam-3.1         2.50 USD per 1,000 images, i.e. 0.0025 per call

Only entries whose own record says network true are counted: a replay or a mock answer costs
nothing. Nothing here reads the key, and nothing here opens a network connection.

Usage:
    python tools/meta_spend_ledger.py                 # rewrites knowledge/META-SPEND.md
    python tools/meta_spend_ledger.py --out X.md      # writes elsewhere, for a comparison run
    python tools/meta_spend_ledger.py --check         # exit 1 when the page is out of date
"""
import argparse
import datetime
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "ai_cache")
OUT = os.path.join(ROOT, "knowledge", "META-SPEND.md")
CEILING_USD = 40.0
# The first command this card ran, from its own log, so the page can separate the live work that
# was already recorded from the live work this card did. A cache entry names no lane, so the split
# is a time window and is labelled as one.
CARD_START = "2026-10-27T01:43:26Z"

FRESH_IN = 1.25 / 1_000_000
CACHED_IN = 0.15 / 1_000_000
OUTPUT = 4.25 / 1_000_000
PER_IMAGE = 0.01
PER_SEGMENT = 0.0025


def rows_from_cache():
    rows = []
    names = sorted(name for name in os.listdir(CACHE) if name.endswith(".json"))
    for name in names:
        with open(os.path.join(CACHE, name), "r", encoding="utf-8") as handle:
            entry = json.load(handle)
        if not entry.get("network"):
            continue
        usage = (entry.get("response") or {}).get("usage") or {}
        prompt = int(usage.get("prompt_tokens") or 0)
        cached = int((usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0)
        out_tokens = int(usage.get("completion_tokens") or 0)
        kind = entry.get("kind")
        images = 1 if kind in ("image", "edit") else 0
        segments = 1 if kind == "segment" else 0
        cost = ((prompt - cached) * FRESH_IN + cached * CACHED_IN + out_tokens * OUTPUT
                + images * PER_IMAGE + segments * PER_SEGMENT)
        at = entry.get("recorded_at") or ""
        rows.append({"at": at, "kind": kind, "model": entry.get("model"),
                     "fresh": prompt - cached, "cached": cached, "out": out_tokens,
                     "images": images, "segments": segments, "usd": cost,
                     "window": "B" if at >= CARD_START else "A"})
    rows.sort(key=lambda row: row["at"])
    return rows, len(names)


def render(rows, total_entries, stamp):
    total = sum(row["usd"] for row in rows)
    mine = sum(row["usd"] for row in rows if row["window"] == "B")
    earlier = total - mine
    live_kinds = defaultdict(int)
    summary = defaultdict(lambda: {"calls": 0, "fresh": 0, "cached": 0, "out": 0, "images": 0,
                                   "segments": 0, "usd": 0.0})
    for row in rows:
        live_kinds[row["kind"]] += 1
        slot = summary[(row["window"], row["kind"], row["model"])]
        slot["calls"] += 1
        slot["fresh"] += row["fresh"]
        slot["cached"] += row["cached"]
        slot["out"] += row["out"]
        slot["images"] += row["images"]
        slot["segments"] += row["segments"]
        slot["usd"] += row["usd"]

    lines = []
    lines.append("# Meta spend, measured (card t_5031b766)")
    lines.append("")
    lines.append("Every live Meta Model API call recorded in `data/ai_cache`, priced at the documented "
                 "list price. This page is generated from the cache by "
                 "`tools/meta_spend_ledger.py`; a replayed or mock answer is not in it, because it "
                 "cost nothing and crossed no network.")
    lines.append("")
    lines.append("Generated %s from %d live cache entries (%s to %s). The cache also holds %d mock "
                 "entries, which are not counted."
                 % (stamp, len(rows), rows[0]["at"] if rows else "-", rows[-1]["at"] if rows else "-",
                    total_entries - len(rows)))
    lines.append("")
    lines.append("## 1. Prices used, and where they come from")
    lines.append("")
    lines.append("`arananet/meta-hackathon/HACKATHON-BRIEF.md` section 3.2, read 2026-10-21 from "
                 "https://dev.meta.ai/docs/pricing-rate-limits and repeated on the model pages:")
    lines.append("")
    lines.append("| model | unit | price |")
    lines.append("| --- | --- | --- |")
    lines.append("| muse-spark-1.3 | fresh input tokens | 1.25 USD per 1M |")
    lines.append("| muse-spark-1.3 | cached input tokens | 0.15 USD per 1M |")
    lines.append("| muse-spark-1.3 | output tokens | 4.25 USD per 1M |")
    lines.append("| muse-image-1.0 | generated or edited image | 0.01 USD per image, flat |")
    lines.append("| sam-3.1 | image segmentation | 2.50 USD per 1,000 images (0.0025 each) |")
    lines.append("")
    lines.append("The token counts are the API's own `usage` object as it was stored with each "
                 "answer, so the arithmetic below is over measured tokens, not an estimate from "
                 "character counts. The reasoning tokens Muse Spark reports are already inside "
                 "`completion_tokens` and are billed at the output rate.")
    lines.append("")
    lines.append("## 2. The total")
    lines.append("")
    lines.append("| window | live calls | cost, USD |")
    lines.append("| --- | --- | --- |")
    lines.append("| A: live work recorded before this worker's first command (%s to just before %s) "
                 "| %d | %.4f |" % (rows[0]["at"] if rows else "-", CARD_START,
                                     len([r for r in rows if r["window"] == "A"]), earlier))
    lines.append("| B: everything recorded from %s to now | %d | %.4f |"
                 % (CARD_START, len([r for r in rows if r["window"] == "B"]), mine))
    lines.append("| **all live calls in the cache** | **%d** | **%.4f** |" % (len(rows), total))
    lines.append("")
    lines.append("A cache entry records the model, the request and the answer, and not which process "
                 "or lane asked for it, so window B is a time window and not an attribution: it holds "
                 "this worker's own calls and any other run that was live in the same minutes. The "
                 "number that is exact is the total.")
    lines.append("")
    lines.append("The card's ceiling is %.2f USD of measured spend. Measured: **%.4f USD**, which is "
                 "%.2f percent of the ceiling. The cost inside window B (this worker's own calls plus "
                 "any other live run in the same minutes) is %.4f USD."
                 % (CEILING_USD, total, 100.0 * total / CEILING_USD, mine))
    lines.append("")
    lines.append("## 3. By kind and model")
    lines.append("")
    lines.append("| window | kind | model | calls | fresh in | cached in | out | images | cost, USD |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for key in sorted(summary):
        slot = summary[key]
        lines.append("| %s | %s | %s | %d | %d | %d | %d | %d | %.4f |"
                     % (key[0], key[1], key[2], slot["calls"], slot["fresh"], slot["cached"],
                        slot["out"], slot["images"], slot["usd"]))
    lines.append("")
    lines.append("Live calls per kind, the number the card asks the cache to show is greater than "
                 "zero for: %s."
                 % ", ".join("%s %d" % (kind, live_kinds[kind]) for kind in sorted(live_kinds)))
    lines.append("")
    lines.append("## 4. Every live call, in the order it was made")
    lines.append("")
    lines.append("| recorded_at | kind | model | fresh in | cached in | out | USD |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for row in rows:
        lines.append("| %s | %s | %s | %d | %d | %d | %.5f |"
                     % (row["at"], row["kind"], row["model"], row["fresh"], row["cached"],
                        row["out"], row["usd"]))
    lines.append("")
    lines.append("## 5. What this page does not claim")
    lines.append("")
    lines.append("- It is a list price calculation over recorded token counts, not a copy of a bill. "
                 "Meta's invoice is the authority; if the two disagree, the invoice wins.")
    lines.append("- The hackathon credit grant (150 USD, `HACKATHON-BRIEF.md` section 3 and the waiver) "
                 "is unconfirmed for this team, so this spend is charged against whatever payment "
                 "method the account holds until that changes.")
    lines.append("- No figure here includes the account's own charges outside this repository, or the "
                 "manager's 2026-10-26 smoke call, which was recorded in "
                 "`arananet/meta-hackathon/META-SMOKE-2026-10-26.txt`, not in this cache.")
    lines.append("")
    return "\n".join(lines), total, mine, earlier


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=OUT)
    parser.add_argument("--check", action="store_true",
                        help="compare the recorded totals with the page on disk and change nothing")
    args = parser.parse_args()

    rows, total_entries = rows_from_cache()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    page, total, mine, earlier = render(rows, total_entries, stamp)

    if args.check:
        on_disk = open(args.out, "r", encoding="utf-8").read() if os.path.exists(args.out) else ""
        want = "**%d** | **%.4f**" % (len(rows), total)
        ok = want in on_disk
        print("live entries: %d, measured total USD %.4f" % (len(rows), total))
        print("page carries that total: %s" % ("YES" if ok else "NO"))
        return 0 if ok else 1

    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(page)
    print("wrote %s" % args.out)
    print("live calls: %d, total USD %.4f, this worker %.4f, earlier %.4f"
          % (len(rows), total, mine, earlier))
    return 0


if __name__ == "__main__":
    sys.exit(main())
