"""Report counterpoint violations in a cue, with bar, beat and the two notes involved, card t_836dbb1a.

    python tools/counterpoint/check.py assets/audio/pp_01_title_v7/pp_01_title_v7.mid
    python tools/counterpoint/check.py assets/audio/baroque_demo/score_baroque_demo.yaml
    python tools/counterpoint/check.py CUE.mid --profile strict --json out.json
    python tools/counterpoint/check.py CUE.mid --limit 0 --fail-on soft

The engine is tools/counterpoint/rules.py; this file is the reader: it prints the report, writes the
JSON and compares the measured rate against the Bach calibration in tools/counterpoint/calibration.json.

Exit codes:
    0  no finding at or above the level named by --fail-on (default: hard)
    1  at least one finding at that level
    2  the file could not be measured at all, which is never the same thing as a pass
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rules  # noqa: E402

DEFAULT_CALIBRATION = os.path.join(HERE, "calibration.json")
LEVELS = ("hard", "soft", "style")


def load_calibration(path):
    """The Bach calibration table, or None when the file is absent."""
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def rate_against_budget(result, calibration, level):
    """Each rule's measured rate against its own Bach budget, for the rules at one level.

    Returns a list of (rule, measured, allowed) sorted worst first, or None when there is no
    calibration to compare with. The comparison is per rule on purpose: summing the budgets lets a
    cue that is twice the allowance on one rule hide behind being quiet on another, and the rule
    that is out of line is the only actionable fact in the report.
    """
    if not calibration:
        return None
    budget = calibration.get("thresholds", {}).get("per_100_notes", {})
    if not budget:
        return None
    rates = result["summary"]["rates_per_100_notes"]
    rows = []
    for rule, value in rules.RULES.items():
        if value["severity"][result["profile"]] != level:
            continue
        rows.append((rule, rates.get(rule, 0.0), budget.get(rule, 0.0)))
    rows.sort(key=lambda row: (-(row[1] / row[2] if row[2] else (float("inf") if row[1] else 0.0)),
                               row[0]))
    return rows


def verdict_of(result, level="hard", calibration=None):
    """FAIL when any rule at this level is measurably worse than the Bach budget allows.

    With a calibration in hand the budget is the gate, which is what the profile was calibrated
    for: a cue written as freely as Bach's worst chorale prelude passes, and a cue that is twice
    as loose on any single rule fails. Without one, any finding at this level is enough, and the
    report says the calibration was missing rather than pretending to a threshold it does not have.
    """
    order = {"hard": 0, "soft": 1, "style": 2}
    counts = result["summary"]["by_severity"]
    present = [name for name in LEVELS if counts.get(name)]
    if not present:
        return "PASS", False
    rows = rate_against_budget(result, calibration, level)
    if rows is None:
        worst = min(present, key=lambda name: order[name])
        return ("FAIL" if order[worst] <= order[level] else "PASS"), order[worst] <= order[level]
    over = [row for row in rows if row[1] > row[2]]
    return ("FAIL" if over else "PASS"), bool(over)


def calibration_note(result, calibration, level="hard"):
    """One line naming the rules that exceed the Bach budget, or the closest one, or why not."""
    if not calibration:
        return "calibration: not read (no calibration.json beside this tool)"
    rows = rate_against_budget(result, calibration, level)
    if rows is None:
        return "calibration: present but holds no thresholds"
    over = [row for row in rows if row[1] > row[2]]
    if over:
        shown = "; ".join("%s %.2f vs %.2f" % (rule, measured, allowed)
                          for rule, measured, allowed in over[:3])
        return "calibration: %d %s rule(s) over the Bach budget (%s)%s" % (
            len(over), level, shown,
            " and %d more" % (len(over) - 3) if len(over) > 3 else "")
    rule, measured, allowed = rows[0]
    return ("calibration: every %s rule within the Bach budget (closest %s %.2f vs %.2f), corpus %s"
            % (level, rule, measured, allowed,
               calibration.get("corpus", {}).get("description", "unnamed")))


def format_finding(finding):
    """One finding as a single line a reader can check against the MIDI file."""
    evidence = finding.get("evidence") or {}
    detail = finding["detail"]
    if evidence.get("from") and evidence.get("to"):
        detail = "%s: %s -> %s" % (detail, evidence["from"], evidence["to"])
    elif evidence.get("interval"):
        detail = "%s (interval %s)" % (detail, evidence["interval"])
    return "  bar %-3d beat %-6.2f %-6s %-46s %s" % (
        finding["bar"], finding["beat"], finding["rule"],
        rules.RULES[finding["rule"]]["title"], detail)


def render(result, calibration=None, limit=20, level="hard"):
    """The readable report: what was read, what was judged, then the findings by severity."""
    lines = []
    lines.append("counterpoint check: %s" % (result["path"] or "<in memory>"))
    lines.append("profile: %s (%s)   metre: %s   bars: %d   key: %s (%s)"
                 % (result["profile"],
                    "free Baroque" if result["profile"] == "free" else "strict species",
                    result["time_signature"], result["bars"], result["key"],
                    "declared" if result["key_source"] == "declared"
                    else "detected, %s" % result["key_detected"]))
    lines.append("")
    lines.append("voices, top to bottom (%d notes in total)" % result["notes"])
    for voice in result["voices"]:
        role = ""
        if voice["name"] == result["outer_voices"][0]:
            role = "  soprano"
        elif len(result["outer_voices"]) > 1 and voice["name"] == result["outer_voices"][1]:
            role = "  bass"
        lines.append("  %-14s %4d notes  %-4s to %-4s  declared %-4s to %-4s%s"
                     % (voice["name"], voice["notes"], voice["range"][0], voice["range"][1],
                        voice["declared_range"][0], voice["declared_range"][1], role))
    judged = result["judged"]
    lines.append("")
    lines.append("judged: %d dissonant notes (%d accented, %d weak); %d held from before, %d attacked"
                 % (judged["dissonances"], judged["accented"], judged["unaccented"],
                    judged["prepared"], judged["unprepared"]))
    lines.append("devices: " + ", ".join("%s %d" % (name, count)
                                         for name, count in sorted(result["devices"].items())))
    state, fails = verdict_of(result, level, calibration)
    counts = result["summary"]["by_severity"]
    lines.append("")
    lines.append("verdict: %s   hard %d, soft %d, style %d   (fails at --fail-on %s)"
                 % (state, counts.get("hard", 0), counts.get("soft", 0), counts.get("style", 0),
                    level))
    lines.append(calibration_note(result, calibration, level))

    for severity in LEVELS:
        rows = [f for f in result["findings"] if f["severity"] == severity]
        if not rows:
            continue
        lines.append("")
        lines.append("%s (%d)" % (severity, len(rows)))
        shown = rows if limit <= 0 else rows[:limit]
        for finding in shown:
            lines.append(format_finding(finding))
        if len(shown) < len(rows):
            lines.append("  ... %d more %s, see --json" % (len(rows) - len(shown), severity))
    if not result["findings"]:
        lines.append("")
        lines.append("no findings")
    return "\n".join(lines)


def main(argv=None):
    """Read one cue, measure it, print the report."""
    parser = argparse.ArgumentParser(description="Counterpoint check for one cue (card t_836dbb1a).")
    parser.add_argument("score", help="a .mid file or a project score .yaml")
    parser.add_argument("--profile", default="free",
                        help="free (free Baroque, default) or strict (species counterpoint)")
    parser.add_argument("--key", default=None,
                        help="the key, for example 'A minor'; detected from the notes when omitted")
    parser.add_argument("--json", dest="json_path", default=None, help="write the full result")
    parser.add_argument("--calibration", default=DEFAULT_CALIBRATION,
                        help="the Bach calibration table (default: calibration.json beside this tool)")
    parser.add_argument("--limit", type=int, default=20,
                        help="how many findings to print per severity (0 prints all)")
    parser.add_argument("--fail-on", default="hard", choices=LEVELS,
                        help="the severity that makes the exit code 1 (default: hard)")
    parser.add_argument("--quiet", action="store_true", help="print only the verdict line")
    args = parser.parse_args(argv)

    try:
        score = rules.load_score(args.score, key=rules.parse_key(args.key) if args.key else None)
    except (ValueError, OSError) as error:
        sys.stderr.write("counterpoint: cannot measure %s: %s\n" % (args.score, error))
        return 2
    if not score.parts or score.notes_total < 2:
        sys.stderr.write("counterpoint: %s holds %d pitched note(s), nothing to judge\n"
                         % (args.score, score.notes_total))
        return 2

    result = rules.analyse(score, profile=args.profile)
    calibration = load_calibration(args.calibration)
    state, _fails = verdict_of(result, args.fail_on, calibration)
    result["verdict"] = state
    result["calibration"] = None
    if calibration:
        rates = result["summary"]["rates_per_100_notes"]
        result["calibration"] = {
            "corpus": calibration.get("corpus", {}),
            "thresholds": calibration.get("thresholds", {}).get("per_100_notes", {}),
            "measured": rates,
        }

    if args.quiet:
        counts = result["summary"]["by_severity"]
        print("%s: %s hard %d, soft %d, style %d"
              % (args.score, state, counts.get("hard", 0), counts.get("soft", 0),
                 counts.get("style", 0)))
    else:
        print(render(result, calibration, limit=args.limit, level=args.fail_on))
    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=1, sort_keys=True)
        if not args.quiet:
            print("")
            print("json: %s" % os.path.abspath(args.json_path))
    return 0 if state == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
