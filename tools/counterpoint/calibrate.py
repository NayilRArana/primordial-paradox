"""Calibrate the free Baroque profile on public-domain Bach, card t_836dbb1a.

    python tools/counterpoint/calibrate.py --corpus "<workspace>/corpora/bach-counterpoint/midi"
    python tools/counterpoint/calibrate.py --corpus DIR --out tools/counterpoint/calibration.json \
        --report knowledge/COUNTERPOINT-CALIBRATION-2026-10-26.md

What it does, in order:

  1. reads tools/counterpoint/corpus.json, which records the source URL, the licence and the SHA-256
     of every calibration input, and refuses to measure a file whose digest differs from the record
     or whose licence is missing. The MIDI files are never copied into this repository.
  2. runs the free Baroque profile over each work and counts violations per 100 notes.
  3. writes calibration.json: the per-work table, the mean and the maximum of every rule, and the
     budget a new cue has to stay inside.
  4. writes the readable table.

The budget rule, in one line: twice the highest rate Bach commits, and 0.25 per 100 notes for a rule
Bach never commits, because one slip in a four hundred note cue should not read the same as a texture
built out of parallel fifths. Both numbers are printed in the report so a reader can disagree.

Nothing here judges Bach as wrong. The corpus is two-part by construction (fifteen inventions and
five chorale settings), so the numbers say what a two-voice Baroque texture looks like to this
checker; they are the yardstick, not the target.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rules  # noqa: E402

DEFAULT_CORPUS = r"<workspace>/corpora/bach-counterpoint/midi"
DEFAULT_MANIFEST = os.path.join(HERE, "corpus.json")
DEFAULT_OUT = os.path.join(HERE, "calibration.json")
ZERO_BUDGET = 0.25     # per 100 notes, for a rule the corpus never violates
BUDGET_MULTIPLIER = 2.0


def digest(path):
    """The SHA-256 of a file, as the manifest records it."""
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def verify(corpus_dir, manifest):
    """Every manifest row that is present on disk, verified; anything else is a hard error."""
    works, missing = [], []
    for work in manifest["works"]:
        path = os.path.join(corpus_dir, work["file"])
        if not os.path.exists(path):
            missing.append(work["file"])
            continue
        if digest(path) != work["sha256"]:
            raise SystemExit("calibrate: %s does not match the SHA-256 in corpus.json; the file "
                             "was changed or is not the one the licence covers" % work["file"])
        if not work.get("licence"):
            raise SystemExit("calibrate: %s has no licence recorded in corpus.json" % work["file"])
        works.append((path, work))
    if missing:
        raise SystemExit("calibrate: %d calibration file(s) absent from %s: %s"
                         % (len(missing), corpus_dir, ", ".join(sorted(missing)[:6])))
    return works


def measure(works):
    """Run the free profile over every work and return one row per work."""
    rows = []
    for path, work in works:
        score = rules.load_score(path)
        result = rules.analyse(score, profile="free")
        rows.append({
            "file": work["file"],
            "catalogue": work.get("catalogue"),
            "title": work.get("title"),
            "licence": work.get("licence"),
            "source": work.get("source"),
            "sha256": work.get("sha256"),
            "voices": [voice["name"] for voice in result["voices"]],
            "notes": result["notes"],
            "bars": result["bars"],
            "time_signature": result["time_signature"],
            "key_detected": result["key_detected"],
            "by_rule": result["summary"]["by_rule"],
            "rates_per_100_notes": result["summary"]["rates_per_100_notes"],
            "by_severity": result["summary"]["by_severity"],
            "devices": result["devices"],
            "judged": result["judged"],
        })
    return rows


def thresholds(rows):
    """The budget per rule: twice the corpus maximum, or the zero budget for a rule never broken."""
    summary = {}
    for rule, meta in rules.RULES.items():
        rates = [row["rates_per_100_notes"].get(rule, 0.0) for row in rows]
        counts = [row["by_rule"].get(rule, 0) for row in rows]
        highest = max(rates) if rates else 0.0
        mean = sum(rates) / float(len(rates)) if rates else 0.0
        budget = round(highest * BUDGET_MULTIPLIER, 2) if highest > 0 else ZERO_BUDGET
        summary[rule] = {
            "title": meta["title"],
            "severity_free": meta["severity"]["free"],
            "mean_per_100_notes": round(mean, 3),
            "max_per_100_notes": round(highest, 3),
            "total_violations": sum(counts),
            "works_with_any": sum(1 for count in counts if count),
            "budget_per_100_notes": budget,
        }
    return summary


def calibration_block(manifest, rows, summary, corpus_dir):
    """The JSON that check.py reads, and the evidence behind every number in it."""
    notes = sum(row["notes"] for row in rows)
    return {
        "format": "pp-counterpoint-calibration",
        "version": 1,
        "card": "t_836dbb1a",
        "profile": "free",
        "written": "2026-10-26",
        "corpus": {
            "description": "Bach: 15 two-part inventions (BWV 772 to 786) and 5 chorale settings, "
                           "public domain, from the Mutopia Project",
            "manifest": "tools/counterpoint/corpus.json",
            "directory": corpus_dir,
            "in_repository": False,
            "works": len(rows),
            "notes": notes,
            "licences": sorted({row["licence"] for row in rows}),
            "sources": sorted({row["source"] for row in rows}),
        },
        "method": ("every work read as a two-voice score, free Baroque profile, violations counted "
                   "per 100 notes; budget = 2 x the corpus maximum, or 0.25 when the corpus maximum "
                   "is 0"),
        "thresholds": {"per_100_notes": {rule: item["budget_per_100_notes"]
                                         for rule, item in summary.items()}},
        "summary": summary,
        "works": rows,
    }


def report_text(calibration, manifest):
    """The readable calibration table."""
    corpus = calibration["corpus"]
    lines = []
    lines.append("# Counterpoint calibration: the free Baroque profile measured on Bach")
    lines.append("")
    lines.append("Card t_836dbb1a, written 2026-10-26 by the audit lane. The machine readable twin is")
    lines.append("`tools/counterpoint/calibration.json`, the corpus record is")
    lines.append("`tools/counterpoint/corpus.json`, and the engine is `tools/counterpoint/rules.py`.")
    lines.append("")
    lines.append("## What was measured")
    lines.append("")
    licences = sorted({row["licence"] for row in calibration["works"]})
    counts = {}
    for row in calibration["works"]:
        counts[row["licence"]] = counts.get(row["licence"], 0) + 1
    summary = ", ".join("%d under %s" % (counts[name], name) for name in licences)
    lines.append("%d Bach works, %d notes: %s. The MIDI files are NOT in this repository:"
                 % (corpus["works"], corpus["notes"], summary))
    lines.append("they live in `%s`, and the manifest records each source URL, the licence as the"
                 % corpus["directory"])
    lines.append("source states it, and the SHA-256 that was measured. Nothing melodic is copied here;")
    lines.append("the numbers are counts of rule violations.")
    lines.append("")
    lines.append("The key in the last column is detected from note durations by `detect_key()`, not read")
    lines.append("from the file, and it is printed so a reader can disagree with it by name.")
    lines.append("")
    lines.append("| work | catalogue | licence | notes | bars | key detected |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for row in calibration["works"]:
        lines.append("| %s | %s | %s | %d | %d | %s |"
                     % (row["title"], row["catalogue"], row["licence"], row["notes"], row["bars"],
                        row["key_detected"]))
    lines.append("")
    lines.append("## The table")
    lines.append("")
    lines.append("Rates are violations per 100 notes across the whole corpus work. `works` is how many")
    lines.append("of the %d works show the rule at least once." % corpus["works"])
    lines.append("")
    lines.append("| rule | what it catches | severity (free) | mean | max | works | budget |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for rule in sorted(calibration["summary"]):
        item = calibration["summary"][rule]
        lines.append("| %s | %s | %s | %.2f | %.2f | %d | %.2f |"
                     % (rule, item["title"], item["severity_free"], item["mean_per_100_notes"],
                        item["max_per_100_notes"], item["works_with_any"],
                        item["budget_per_100_notes"]))
    lines.append("")
    lines.append("## The budget rule")
    lines.append("")
    lines.append("`budget = 2 x the highest rate any work shows`, and `%.2f` per 100 notes for a rule "
                 "Bach never" % ZERO_BUDGET)
    lines.append("breaks. The second number exists because a rule with a corpus maximum of zero would")
    lines.append("otherwise forbid a single slip in a four hundred note cue, which is not what the")
    lines.append("numbers can support: the corpus is two voices and a cue is five or six, and a rule")
    lines.append("that needs a chord to be judged cannot fire the same way in both.")
    lines.append("")
    lines.append("## How to use it")
    lines.append("")
    lines.append("    python tools/counterpoint/check.py CUE.mid            # compares with this table")
    lines.append("    python tools/counterpoint/calibrate.py --corpus DIR    # rebuild this table")
    lines.append("")
    lines.append("`check.py` compares each rule with its own budget and fails only when a rule is over it.")
    lines.append("A cue over budget on one rule is not automatically wrong; it is a cue whose texture")
    lines.append("does something this corpus does not, and the report names the bar, the beat and the")
    lines.append("notes so the musician lane can decide whether it was intended.")
    lines.append("")
    lines.append("## What this cannot do")
    lines.append("")
    lines.append("- There are no chord symbols. Consonance is judged from the interval classes plus two")
    lines.append("  exceptions (a fourth above the bass is consonant in a 6/4 chord; a real seventh above")
    lines.append("  the bass is a chordal seventh), so a note that is a chord tone in a rich cue can be")
    lines.append("  read as a dissonance. The cue report is a list to read, not a verdict to obey.")
    lines.append("- The corpus is two voices and a six voice cue is not. Parallells and hidden perfects are")
    lines.append("  therefore restricted to the outer voices, as the card says, because inner voices in a")
    lines.append("  chip texture double each other on purpose.")
    lines.append("- A held note that is the bass is treated as a pedal and is not asked to resolve; the")
    lines.append("  moving voices carry the finding. Without that exception every bass pedal note became a")
    lines.append("  failed suspension and the finding named the wrong voice: a long bass note that the")
    lines.append("  upper voices move against was reported as a suspension the bass failed to resolve.")
    lines.append("- CP-15 and CP-17 never fire here: two-part keyboard music has no upper-voice spacing and")
    lines.append("  no NES register. Their budget is the floor below, and they are measured on the cue.")
    lines.append("- Each pair of notes is judged once, at the instant it first becomes dissonant, so a")
    lines.append("  dissonance that later changes its role is not re-judged. A held note that was already")
    lines.append("  dissonant when it began is judged at that attack, which is why there is no separate")
    lines.append("  rule for an unprepared suspension: unprepared is what CP-01 and CP-02 already say.")
    return "\n".join(lines) + "\n"


def main(argv=None):
    """Measure the corpus, write the JSON and the report."""
    parser = argparse.ArgumentParser(description="Calibrate the counterpoint checker on Bach corpus.")
    parser.add_argument("--corpus", default=DEFAULT_CORPUS, help="folder holding the manifest files")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, help="the corpus record")
    parser.add_argument("--out", default=DEFAULT_OUT, help="the calibration JSON to write")
    parser.add_argument("--report", default=None, help="the markdown report to write")
    args = parser.parse_args(argv)

    with open(args.manifest, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    works = verify(args.corpus, manifest)
    rows = measure(works)
    summary = thresholds(rows)
    calibration = calibration_block(manifest, rows, summary, args.corpus)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(calibration, handle, indent=1)
    print("calibrate: %d works, %d notes, wrote %s"
          % (len(rows), calibration["corpus"]["notes"], args.out))
    for rule in sorted(summary):
        item = summary[rule]
        print("  %-6s %-55s max %5.2f  budget %5.2f  works %d"
              % (rule, item["title"][:55], item["max_per_100_notes"], item["budget_per_100_notes"],
                 item["works_with_any"]))
    if args.report:
        with open(args.report, "w", encoding="utf-8") as handle:
            handle.write(report_text(calibration, manifest))
        print("calibrate: wrote %s" % args.report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
