"""The M4 cue gate: no raw clash and no parallel perfect interval lands unmarked.

Card t_aa3ab04e. One cue, one question, answered by the M1a checker (``tools/counterpoint/check.py``,
engine ``rules.py``) and by the clash counter M0 built (``tools/counterpoint/clash.py``):

  G1  zero CP-01 findings, which is a dissonance on a strong beat that is neither prepared nor
      resolved, the thing that reads as a wrong note
  G2  zero CP-09 findings, which is a parallel perfect fifth or octave between the outer voices

Three ways a spot may stay:

  intentional  the cue's own data marks the spot in ``assets/audio/<asset>/intentional.json`` with a
               reason of at least 20 characters, so a chosen clash carries its argument with it
  grandfathered ``data/cue_ear_approvals.json`` names a cue Nayil's ear already approved, with the
               date and what he said; the counts are still printed, they are just not a block
  legacy       ``data/cue_gate_baseline.json`` holds the counts measured when the gate was introduced,
               so a cue older than the gate is reported with its numbers and never called clean

A legacy cue that gets WORSE than its baseline is refused, so the baseline is a floor and not an
amnesty. A cue that cannot be measured is UNMEASURED, which is never the same thing as a pass.

Usage:
    python tools/counterpoint/cue_gate.py assets/audio/pp_05_small_ship_v6/pp_05_small_ship_v6.mid
    python tools/counterpoint/cue_gate.py CUE --json out.json --quiet
    python tools/counterpoint/cue_gate.py CUE --no-baseline      treat the cue as new

Exit codes: 0 pass or grandfathered or legacy, 1 refused, 2 unmeasured.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import check  # noqa: E402  the M1a report and its Bach budget verdict
import clash  # noqa: E402  the M0 clash counter, the number the diagnosis is built on
import rules  # noqa: E402  the engine both of them run on

BASELINE_REL = "data/cue_gate_baseline.json"
APPROVALS_REL = "data/cue_ear_approvals.json"
GATED_RULES = ("CP-01", "CP-09")
REASON_MIN = 20
BEAT_TOLERANCE = 0.05
COUNTERS = ("cp01", "cp09", "raw_clash", "strong_raw")


def rel_path(path, root=ROOT):
    """A path relative to the project root, with forward slashes.

    A path on another drive cannot be made relative to the root: ntpath.relpath raises ValueError
    across mounts, which on Windows is any absolute path on C: while the tree is on D:. The same
    text, forward slashed, is returned instead, so a comparison against a relative path simply does
    not match and no run crashes on the machine the tool is started from.
    """
    try:
        return os.path.relpath(os.path.abspath(path), root).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def load_json(path):
    """Read a JSON file, or None when it is absent or unreadable."""
    if not path or not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def is_score_file(path):
    """Inside the counterpoint checker's reach: a .mid or a project score .yaml."""
    name = os.path.basename(str(path)).lower()
    return name.endswith(".mid") or (name.startswith("score_") and name.endswith((".yaml", ".yml")))


# ------------------------------------------------------------------ measuring one cue

def measure(score_path, root=ROOT):
    """Run the M1a checker and, for a MIDI file, the clash counter. Raises ValueError."""
    try:
        score = rules.load_score(score_path)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        raise ValueError("cannot read %s: %s" % (rel_path(score_path, root), error))
    if not score.parts or score.notes_total < 2:
        raise ValueError("%s holds %d pitched note(s), nothing to judge"
                         % (rel_path(score_path, root), score.notes_total))
    result = rules.analyse(score, profile="free")
    calibration = check.load_calibration(check.DEFAULT_CALIBRATION)
    state, _over = check.verdict_of(result, "hard", calibration)
    counts = result["summary"]["by_rule"]
    facts = {
        "path": rel_path(score_path, root),
        "file": os.path.abspath(score_path),
        "notes": result["notes"],
        "bars": result["bars"],
        "key": "%s (%s)" % (result["key"], result["key_source"]),
        "voices": [voice["name"] for voice in result["voices"]],
        "outer_voices": list(result["outer_voices"]),
        "cp01": [f for f in result["findings"] if f["rule"] == "CP-01"],
        "cp09": [f for f in result["findings"] if f["rule"] == "CP-09"],
        "by_rule": {rule: counts.get(rule, 0) for rule in rules.RULES},
        "by_severity": dict(result["summary"]["by_severity"]),
        "m1a_verdict": state,
        "clash": None,
    }
    if str(score_path).lower().endswith(".mid"):
        try:
            counter = clash.load_score(score_path)
            summary = clash.summarise(counter, clash.analyse(counter))
        except (OSError, ValueError, KeyError):
            summary = None
        if summary:
            facts["clash"] = {"raw_total": summary["raw_total"],
                              "strong_raw": summary["strong_raw"],
                              "by_class": dict(summary["by_class"])}
    return facts


def counts_of(facts):
    """The four numbers the gate compares: the two rules, and M0's raw clash count."""
    return {
        "cp01": len(facts["cp01"]),
        "cp09": len(facts["cp09"]),
        "raw_clash": (facts["clash"] or {}).get("raw_total"),
        "strong_raw": (facts["clash"] or {}).get("strong_raw"),
    }


# ------------------------------------------------------------------ the cue's own data

def intentional_path(score_path):
    """The file a cue marks its intentional clashes in: assets/audio/<asset>/intentional.json."""
    return os.path.join(os.path.dirname(os.path.abspath(score_path)), "intentional.json")


def read_waivers(score_path):
    """(waivers, problems) from the cue's intentional.json. A waiver must carry its reason."""
    path = intentional_path(score_path)
    data = load_json(path)
    if data is None:
        return [], []
    entries = data.get("intentional") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return [], ["%s: needs an 'intentional' array" % rel_path(path)]
    waivers, problems = [], []
    for index, entry in enumerate(entries):
        where = "%s.intentional[%d]" % (rel_path(path), index)
        if not isinstance(entry, dict):
            problems.append("%s: not an object" % where)
            continue
        rule = entry.get("rule")
        if rule not in GATED_RULES:
            problems.append("%s: rule %r is not one of %s" % (where, rule, ", ".join(GATED_RULES)))
            continue
        if not isinstance(entry.get("bar"), int):
            problems.append("%s: bar must be an integer bar number" % where)
            continue
        beat = entry.get("beat")
        if beat is not None and not isinstance(beat, (int, float)):
            problems.append("%s: beat must be a number or absent" % where)
            continue
        reason = entry.get("reason")
        if not isinstance(reason, str) or len(reason.strip()) < REASON_MIN:
            problems.append("%s: the reason must be at least %d characters, so the mark says why"
                            % (where, REASON_MIN))
            continue
        waivers.append({"rule": rule, "bar": entry["bar"], "beat": beat,
                        "reason": reason.strip(), "approved_by": entry.get("approved_by"),
                        "where": where})
    return waivers, problems


def apply_waivers(facts, waivers):
    """Split the gated findings into (kept, waived). A waiver that matches nothing is stale."""
    kept = {"CP-01": [], "CP-09": []}
    waived, used = [], set()
    for rule in GATED_RULES:
        for finding in facts["cp01" if rule == "CP-01" else "cp09"]:
            hit = None
            for index, waiver in enumerate(waivers):
                if waiver["rule"] != rule or waiver["bar"] != finding["bar"]:
                    continue
                if waiver["beat"] is not None and abs(waiver["beat"] - finding["beat"]) > BEAT_TOLERANCE:
                    continue
                if index in used:
                    continue
                hit = index
                break
            if hit is None:
                kept[rule].append(finding)
                continue
            used.add(hit)
            waived.append({"finding": finding, "waiver": waivers[hit]})
    stale = [waiver for index, waiver in enumerate(waivers) if index not in used]
    return kept, waived, stale


def approval_entry(score_path, root=ROOT):
    """The grandfather row naming this file, or None."""
    data = load_json(os.path.join(root, APPROVALS_REL))
    if not isinstance(data, dict):
        return None
    here = rel_path(score_path, root)
    for entry in data.get("entries") or []:
        named = entry.get("path")
        if not isinstance(named, str) or not named.strip():
            # A row that names nothing cannot name this cue; it is skipped rather than turned into
            # a path relative to whatever directory the gate happened to be started from.
            continue
        # An entry is written relative to the project root, so it is resolved against the root and
        # not against the process's current directory: this gate is run from anywhere.
        if rel_path(os.path.join(root, named), root) == here or named.replace("\\", "/") == here:
            return entry
    return None


def baseline_entry(score_path, root=ROOT):
    """The measured-at-introduction row for this file, or None."""
    data = load_json(os.path.join(root, BASELINE_REL))
    if not isinstance(data, dict):
        return None
    entries = data.get("entries") or {}
    return entries.get(rel_path(score_path, root))


# ------------------------------------------------------------------ the verdict

def judge(facts, score_path, root=ROOT, use_baseline=True):
    """The gate's verdict on one measured cue, with every reason it reached it."""
    waivers, waiver_problems = read_waivers(score_path)
    kept, waived, stale = apply_waivers(facts, waivers)
    counts = counts_of(facts)
    open_counts = {"CP-01": len(kept["CP-01"]), "CP-09": len(kept["CP-09"])}
    approval = approval_entry(score_path, root)
    base = baseline_entry(score_path, root) if use_baseline else None

    verdict = {"path": facts["path"], "clean_rules": open_counts == {"CP-01": 0, "CP-09": 0},
               "open": kept, "waived": waived, "stale_waivers": stale,
               "waiver_problems": waiver_problems, "counts": counts,
               "approval": approval, "baseline": base}
    if waiver_problems:
        verdict["state"] = "REFUSED"
        verdict["why"] = "the cue's own mark file is malformed, so no spot in it can be trusted"
        return verdict
    if stale:
        verdict["state"] = "REFUSED"
        verdict["why"] = ("%d intentional mark(s) match no finding any more, so the mark is stale"
                          % len(stale))
        return verdict
    if verdict["clean_rules"]:
        verdict["state"] = "PASS"
        verdict["why"] = ("0 raw clashes on a strong beat and 0 parallel perfect fifths or octaves "
                          "between the outer voices")
        return verdict
    if approval:
        verdict["state"] = "GRANDFATHERED"
        said = approval.get("verdict")
        verdict["why"] = ("%s on %s%s, so it is noted rather than blocked"
                          % (approval.get("approved_by", "a human ear"), approval.get("date", "?"),
                             ", verdict %r" % said if said else ""))
        return verdict
    if base:
        worse = [name for name in COUNTERS
                 if counts.get(name) is not None and base.get(name) is not None
                 and counts[name] > base[name]]
        if worse:
            verdict["state"] = "REFUSED"
            verdict["why"] = ("worse than the gate's own baseline: %s"
                              % ", ".join("%s %s to %s" % (name, base[name], counts[name])
                                          for name in worse))
            return verdict
        verdict["state"] = "LEGACY"
        verdict["why"] = ("predates the gate and has not got worse than its measured baseline "
                          "(%s), so it is reported with its numbers, not called clean"
                          % ", ".join("%s %s" % (name, base.get(name)) for name in COUNTERS))
        return verdict
    verdict["state"] = "REFUSED"
    verdict["why"] = ("a new cue must land with no raw clash on a strong beat and no parallel "
                      "perfect interval between the outer voices")
    return verdict


def gate(score_path, root=ROOT, use_baseline=True):
    """Measure and judge one cue. Returns (facts, verdict); facts is None when unmeasurable."""
    try:
        facts = measure(score_path, root)
    except (ValueError, OSError, KeyError) as error:
        return None, {"path": rel_path(score_path, root), "state": "UNMEASURED",
                      "why": str(error), "counts": {}, "open": {}, "waived": [],
                      "stale_waivers": [], "waiver_problems": [], "approval": None,
                      "baseline": None}
    return facts, judge(facts, score_path, root, use_baseline)


# ------------------------------------------------------------------ the report

def finding_line(finding):
    """One gated finding as a line a reader can open the MIDI and check."""
    evidence = finding.get("evidence") or {}
    where = "bar %d beat %s" % (finding["bar"], finding["beat"])
    detail = finding["detail"][:80]
    if evidence.get("from") and evidence.get("to"):
        detail = "%s [%s -> %s]" % (detail, evidence["from"], evidence["to"])
    elif evidence.get("interval"):
        detail = "%s [interval %s]" % (detail, evidence["interval"])
    return "  %s %-22s %s" % (finding["rule"], where, detail)


def render(facts, verdict, limit=8):
    """The readable report: what was read, what stayed, and what stops it."""
    lines = ["cue gate: %s" % verdict["path"]]
    if facts is None:
        lines.append("state: UNMEASURED   %s" % verdict["why"])
        lines.append("an unmeasured cue is not a pass")
        return "\n".join(lines)
    counts = verdict["counts"]
    clash_count = "not counted (no MIDI to count)" if facts["clash"] is None else \
        "%d raw, %d on a strong beat" % (counts["raw_clash"], counts["strong_raw"])
    lines += [
        "  %d notes, %d bars, key %s, outer voices %s" % (facts["notes"], facts["bars"], facts["key"],
                                                          " + ".join(facts["outer_voices"])),
        "  M1a verdict %s (hard %d, soft %d, style %d); clash count %s"
        % (facts["m1a_verdict"], facts["by_severity"]["hard"], facts["by_severity"]["soft"],
           facts["by_severity"]["style"], clash_count),
        "  G1 CP-01 raw clashes on a strong beat: %d   G2 CP-09 parallel perfect intervals: %d"
        % (counts["cp01"], counts["cp09"]),
        "state: %s   %s" % (verdict["state"], verdict["why"]),
    ]
    for rule in GATED_RULES:
        rows = verdict["open"].get(rule) or []
        if not rows:
            continue
        lines.append("%s open (%d):" % (rule, len(rows)))
        for finding in (rows if limit <= 0 else rows[:limit]):
            lines.append(finding_line(finding))
        if limit > 0 and len(rows) > limit:
            lines.append("  ... %d more, see --json" % (len(rows) - limit))
    for item in verdict["waived"]:
        finding = item["finding"]
        lines.append("intentional: %s bar %d beat %s, %r"
                     % (finding["rule"], finding["bar"], finding["beat"], item["waiver"]["reason"]))
    for waiver in verdict["stale_waivers"]:
        lines.append("stale mark: %s rule %s bar %s matches no finding"
                     % (waiver["where"], waiver["rule"], waiver["bar"]))
    for problem in verdict["waiver_problems"]:
        lines.append("mark file: %s" % problem)
    return "\n".join(lines)


def state_code(state):
    """The exit code a state maps to. Only a refusal and a blind spot are non-zero."""
    return {"REFUSED": 1, "UNMEASURED": 2}.get(state, 0)


def scan(root=ROOT):
    """Every cue file under assets/audio that the checker can read, sorted."""
    found = []
    base = os.path.join(root, "assets", "audio")
    for folder, _dirs, files in os.walk(base):
        for name in files:
            path = os.path.join(folder, name)
            if is_score_file(path):
                found.append(path)
    return sorted(found, key=lambda path: rel_path(path, root))


def write_baseline(root=ROOT, written=None, quiet=False):
    """Measure every cue in the tree and write data/cue_gate_baseline.json.

    This is the file that lets the gate tell a cue older than itself from a new one, so it is written
    from measurement and never by hand. A cue that cannot be measured gets no row: an absent row
    means the gate has never read it, which is the honest state for a file it cannot read.
    """
    import datetime

    entries, unmeasured = {}, []
    for path in scan(root):
        try:
            facts = measure(path, root)
        except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
            unmeasured.append({"path": rel_path(path, root), "why": str(error)})
            if not quiet:
                print("unmeasured %s: %s" % (rel_path(path, root), error))
            continue
        counts = counts_of(facts)
        entries[facts["path"]] = dict(counts, notes=facts["notes"], bars=facts["bars"],
                                      m1a_verdict=facts["m1a_verdict"])
        if not quiet:
            print("%-4s cp01 %d cp09 %d raw %s %s"
                  % ("REFUSED" if counts["cp01"] or counts["cp09"] else "clean",
                     counts["cp01"], counts["cp09"], counts["raw_clash"], facts["path"]))
    data = {"format": "pp-cue-gate-baseline", "version": 1,
            "written": written or datetime.date.today().isoformat(),
            "card": "t_aa3ab04e",
            "note": ("Counts measured when the M4 cue gate was introduced. A cue in this file is "
                     "reported with its numbers and never called clean; a cue that gets worse than "
                     "its row is refused. A new cue must land clean."),
            "counters": list(COUNTERS),
            "entries": entries,
            "unmeasured": unmeasured}
    path = os.path.join(root, BASELINE_REL)
    folder = os.path.dirname(path)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=1, sort_keys=True)
        handle.write("\n")
    return path, data


def main(argv=None):
    """Read one cue, judge it, print the report, return the exit code."""
    parser = argparse.ArgumentParser(description="The M4 cue gate for one cue (card t_aa3ab04e).")
    parser.add_argument("score", nargs="?", help="a .mid file or a project score .yaml")
    parser.add_argument("--root", default=ROOT, help="the project root holding data/")
    parser.add_argument("--json", dest="json_path", default=None, help="write the result as JSON")
    parser.add_argument("--no-baseline", action="store_true",
                        help="treat the cue as new, ignoring data/cue_gate_baseline.json")
    parser.add_argument("--quiet", action="store_true", help="print the state line only")
    parser.add_argument("--limit", type=int, default=8, help="findings to print per rule, 0 for all")
    parser.add_argument("--write-baseline", action="store_true",
                        help="measure every cue under assets/audio and rewrite the baseline")
    parser.add_argument("--written", default=None, help="the date to stamp into a new baseline")
    args = parser.parse_args(argv)

    if args.write_baseline:
        path, data = write_baseline(args.root, written=args.written, quiet=args.quiet)
        print("%s: %d cues measured, %d unmeasured"
              % (rel_path(path, args.root), len(data["entries"]), len(data["unmeasured"])))
        return 0
    if not args.score:
        parser.error("a cue file is required unless --write-baseline is given")

    facts, verdict = gate(args.score, args.root, use_baseline=not args.no_baseline)
    if args.quiet:
        print("%s: %s" % (verdict["path"], verdict["state"]))
    else:
        print(render(facts, verdict, limit=args.limit))
    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as handle:
            json.dump({"facts": facts, "verdict": verdict}, handle, indent=1, sort_keys=True)
        if not args.quiet:
            print("\njson: %s" % os.path.abspath(args.json_path))
    return state_code(verdict["state"])


if __name__ == "__main__":
    sys.exit(main())
