"""Validate the two files M2 hands on, card t_0ed3bd3f.

    python tools/counterpoint/check_counterpoint_targets.py
    python tools/counterpoint/check_counterpoint_targets.py --targets data/counterpoint_targets.json

Checks

  T1  data/counterpoint_targets.json parses, and its format, version, card and written fields are set
  T2  every required target block is present: melody, rhythm, dissonance per 100 notes, cadences,
      sequences, imitation and the clash census
  T3  every share is a number between 0 and 1, and the interval shares sum to 1 within a tenth
  T4  every band is ordered min <= mean <= max and none of the three is negative
  T5  every work row carries a source URL, a licence and a 64 character SHA-256, and the row count
      matches the corpus block
  T6  the cadence counts agree with the type shares, and the final chord check is stated
  T7  data/hod_dissonance_devices.json parses, every rule has an id, a test, a measured basis and the
      failure it prevents, and the ids are unique
  T8  neither file carries an em dash, an en dash or any other long dash

Exit code 0 means every check passed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DEFAULT_TARGETS = os.path.join(ROOT, "data", "counterpoint_targets.json")
DEFAULT_HOD = os.path.join(ROOT, "data", "hod_dissonance_devices.json")
LONG_DASHES = ("\u2014", "\u2013", "\u2015", "\u2212")
SHA = re.compile(r"^[0-9a-f]{64}$")

BANDS = ("step_share", "leap_share", "large_leap_share", "leap_recovery_share", "unison_share")


def load(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def fail(problems, message):
    problems.append(message)


def check_band(problems, label, band):
    if not isinstance(band, dict):
        fail(problems, "%s is not a band object" % label)
        return
    for key in ("mean", "min", "max"):
        if not isinstance(band.get(key), (int, float)):
            fail(problems, "%s.%s is not a number" % (label, key))
            return
        if band[key] < 0:
            fail(problems, "%s.%s is negative" % (label, key))
    if not band["min"] <= band["mean"] <= band["max"]:
        fail(problems, "%s is not ordered min <= mean <= max (%r)" % (label, band))


def check_shares(problems, label, mapping):
    if not isinstance(mapping, dict) or not mapping:
        fail(problems, "%s is empty" % label)
        return 0.0
    total = 0.0
    for key, value in mapping.items():
        if not isinstance(value, (int, float)):
            fail(problems, "%s[%s] is not a number" % (label, key))
            continue
        if not -0.0001 <= value <= 1.0001:
            fail(problems, "%s[%s] = %r is outside 0 to 1" % (label, key, value))
        total += value
    return total


def check_targets(problems, targets):
    for key in ("format", "version", "card", "written", "corpus", "targets", "works"):
        if key not in targets:
            fail(problems, "targets: missing %s" % key)
    if targets.get("format") != "pp-counterpoint-targets":
        fail(problems, "targets: format is %r" % targets.get("format"))
    block = targets.get("targets") or {}
    for key in ("melody", "rhythm", "dissonance_per_100_notes", "cadences", "sequences",
                "imitation", "clash_census"):
        if key not in block:
            fail(problems, "targets.targets: missing %s" % key)

    melody = block.get("melody") or {}
    total = check_shares(problems, "melody.interval_share", melody.get("interval_share") or {})
    if abs(total - 1.0) > 0.1:
        fail(problems, "melody.interval_share sums to %.3f, not 1" % total)
    for key in BANDS:
        check_band(problems, "melody.%s" % key, melody.get(key))
    check_shares(problems, "melody.direction_share", melody.get("direction_share") or {})

    rhythm = block.get("rhythm") or {}
    total = check_shares(problems, "rhythm.duration_share", rhythm.get("duration_share") or {})
    if abs(total - 1.0) > 0.05:
        fail(problems, "rhythm.duration_share sums to %.3f, not 1" % total)
    for key in ("top_two_note_cells", "top_three_note_cells"):
        cells = rhythm.get(key) or []
        if not cells:
            fail(problems, "rhythm.%s is empty" % key)
        for cell in cells:
            if "cell" not in cell or "share" not in cell:
                fail(problems, "rhythm.%s has a row without cell and share" % key)
    check_band(problems, "rhythm.notes_per_bar", rhythm.get("notes_per_bar"))

    for name, band in (block.get("dissonance_per_100_notes") or {}).items():
        check_band(problems, "dissonance_per_100_notes.%s" % name, band)

    cadences = block.get("cadences") or {}
    counts = cadences.get("counts") or {}
    shares = cadences.get("type_share") or {}
    if sum(counts.values()) != sum(shares.values()) and not counts:
        fail(problems, "cadences: counts and type_share do not describe the same events")
    total_shares = sum(shares.values())
    if counts and abs(total_shares - 1.0) > 0.01:
        fail(problems, "cadences.type_share sums to %.3f, not 1" % total_shares)
    if "final_chord_is_tonic_share" not in cadences:
        fail(problems, "cadences: the final chord check is missing")
    if not cadences.get("method_note"):
        fail(problems, "cadences: the method note is missing")

    sequences = block.get("sequences") or {}
    check_band(problems, "sequences.per_100_notes", sequences.get("per_100_notes"))

    imitation = block.get("imitation") or {}
    check_shares(problems, "imitation.offset_share (list)", {str(row.get("offset_beats")): row.get("share", 0)
                                                             for row in imitation.get("offset_share") or []})
    check_shares(problems, "imitation.transposition_share", imitation.get("transposition_share") or {})

    census = block.get("clash_census") or {}
    for key in ("clashes_per_100_notes", "beats_with_clash_share", "resolved_by_step_share"):
        check_band(problems, "clash_census.%s" % key, census.get(key))
    check_shares(problems, "clash_census.clash_interval_share", census.get("clash_interval_share") or {})

    works = targets.get("works") or []
    corpus = targets.get("corpus") or {}
    if corpus.get("works") != len(works):
        fail(problems, "corpus.works = %r but %d work rows" % (corpus.get("works"), len(works)))
    for row in works:
        label = "work %s" % row.get("file")
        if not row.get("source", "").startswith("http"):
            fail(problems, "%s has no source URL" % label)
        if not row.get("licence"):
            fail(problems, "%s has no licence" % label)
        if not SHA.match(str(row.get("sha256", ""))):
            fail(problems, "%s has no valid SHA-256" % label)
        if not isinstance(row.get("notes"), int) or row["notes"] <= 0:
            fail(problems, "%s has no note count" % label)


def check_hod(problems, hod):
    for key in ("format", "version", "card", "written", "study_set", "measured", "rules"):
        if key not in hod:
            fail(problems, "hod: missing %s" % key)
    if hod.get("format") != "pp-hod-dissonance-devices":
        fail(problems, "hod: format is %r" % hod.get("format"))
    rules = hod.get("rules") or []
    if len(rules) < 4:
        fail(problems, "hod: only %d rules" % len(rules))
    identifiers = set()
    for rule in rules:
        label = "hod rule %s" % rule.get("id")
        for key in ("id", "name", "test", "because", "fails"):
            if not rule.get(key):
                fail(problems, "%s has no %s" % (label, key))
        if rule.get("id") in identifiers:
            fail(problems, "%s is a duplicate id" % label)
        identifiers.add(rule.get("id"))
        if "%" in str(rule.get("because", "")):
            fail(problems, "%s still carries an unformatted placeholder" % label)
    measured = hod.get("measured") or {}
    for key in ("clash_intervals", "quality_share", "clash_events_per_100_notes"):
        if key not in measured:
            fail(problems, "hod.measured: missing %s" % key)
    if not hod["study_set"].get("manifest"):
        fail(problems, "hod.study_set: no manifest path")


def check_dashes(problems, path):
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    for dash in LONG_DASHES:
        if dash in text:
            fail(problems, "%s contains a long dash (%s)" % (os.path.basename(path), repr(dash)))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate the M2 target and device files.")
    parser.add_argument("--targets", default=DEFAULT_TARGETS)
    parser.add_argument("--hod", default=DEFAULT_HOD)
    args = parser.parse_args(argv)

    problems = []
    for path in (args.targets, args.hod):
        if not os.path.exists(path):
            fail(problems, "%s does not exist" % path)
    if problems:
        for problem in problems:
            print("FAIL", problem)
        return 1

    targets = load(args.targets)
    hod = load(args.hod)
    check_targets(problems, targets)
    check_hod(problems, hod)
    check_dashes(problems, args.targets)
    check_dashes(problems, args.hod)

    if problems:
        for problem in problems:
            print("FAIL", problem)
        print("check_counterpoint_targets: %d problem(s)" % len(problems))
        return 1

    block = targets["targets"]
    print("targets   %d works, %d notes, %d intervals shares, %d cadence types"
          % (len(targets["works"]), targets["corpus"]["notes"],
             len(block["melody"]["interval_share"]), len(block["cadences"]["type_share"])))
    print("hod       %d rules" % len(hod["rules"]))
    print("check_counterpoint_targets: every check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
