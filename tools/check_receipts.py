#!/usr/bin/env python3
"""check_receipts.py: fail the build when a Meta number cannot be found.

Card t_7450df91 (RECEIPTS-LABELS). The card's practice, borrowed from two teams in the channel: every
number labelled measured, computed or inferred, "no mystery numbers" (Xava quoting Quetzal, 2026-10-26),
and "a verifier that fails the build if any quote or number can't be found" (Mario Vilnius, Operacija
Dvina, 2026-10-26). This is that verifier for the Meta numbers a take's verify file carries.

What it refuses, one line per fault, all of them at once rather than the first one
    - a verify file with no `meta_numbers` block, or one shorter than three numbers;
    - a number labelled with anything outside the three labels;
    - a number whose receipt id is not in data/receipts/meta_receipts.jsonl;
    - a receipt whose name, label or value disagrees with the number that quotes it;
    - a receipt whose source file is gone;
    - a receipt a CURRENT verify file quotes whose source no longer hashes to the recorded sha256, which is
      how a receipt stops being a receipt and starts being a claim. (The ledger sweep over old receipts
      reports the same finding as a NOTE and asks for a re-issue, because the ledger is history: a
      regenerated bake makes yesterday's receipt stale, not false. tools\\receipts.py re-issues on the
      next run by itself.)
    - a file that does not show all three labels, or a ledger holding fewer than three receipts.

Usage
    python tools\\check_receipts.py                                  newest output\\demo\\*_verify.json
    python tools\\check_receipts.py --verify PATH --ledger PATH
    python tools\\check_receipts.py --counts                          ledger counts only

Exit codes: 0 every number is labelled and every receipt resolves, 1 a fault by name, 2 bad argument.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(ROOT, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "tools"))

import receipts  # noqa: E402  the vocabulary, the ledger reader and the two hash functions

LABELS = receipts.LABELS
MIN_RECEIPTS = 3


class Faults:
    """The lines this run prints, and whether any of them is a failure."""

    def __init__(self):
        self.rows = []
        self.failed = False

    def ok(self, text):
        self.rows.append("PASS %s" % text)

    def fail(self, text):
        self.failed = True
        self.rows.append("FAIL %s" % text)

    def note(self, text):
        self.rows.append("NOTE %s" % text)


def newest_verify(root=ROOT):
    """The newest verify file under output/demo, by modification time."""
    found = glob.glob(os.path.join(root, "output", "demo", "*_verify.json"))
    if not found:
        return None
    return max(found, key=os.path.getmtime)


def _same_number(left, right):
    try:
        return abs(float(left) - float(right)) <= 1e-6 * max(1.0, abs(float(right)))
    except (TypeError, ValueError):
        return False


def _resolve_source(source, root=ROOT):
    """A receipt's source as a path on disk, and whether it is a directory tree."""
    if not isinstance(source, str) or not source.strip():
        return None, False
    is_tree = source.endswith("/")
    relative = source.rstrip("/")
    path = os.path.normpath(os.path.join(root, relative.replace("/", os.sep)))
    if not path.startswith(os.path.normpath(root)):
        return None, is_tree
    return path, is_tree


def _hash_source(row, root=ROOT):
    """(digest, problem) for a receipt's source, where problem is a sentence or None."""
    path, is_tree = _resolve_source(row.get("source"), root=root)
    if path is None:
        return None, "source %r is not a path inside the repository" % (row.get("source"),)
    if not os.path.exists(path):
        return None, "source %s does not exist" % row.get("source")
    digest = receipts.sha256_tree(path) if is_tree else receipts.sha256_file(path)
    return digest, None


def check_ledger(ledger_path=receipts.LEDGER_PATH, root=ROOT, faults=None, strict=False):
    """Every logged receipt against the file it names. Returns (faults, rows).

    A ledger is history: a receipt whose source has changed since it was written is STALE, and the tool says
    so as a NOTE, because the answer is to re-issue it (tools\\receipts.py does that by itself on the next
    run) and not to rewrite the past. `strict=True` turns the same finding into a failure, which is what
    check_verify asks of a receipt a CURRENT verify file quotes: that claim has to be true today.
    """
    faults = faults if faults is not None else Faults()
    rows = receipts.read_ledger(ledger_path)
    if len(rows) < MIN_RECEIPTS:
        faults.fail("%s holds %d receipt%s, and at least %d are needed"
                    % (receipts._rel(ledger_path), len(rows), "" if len(rows) == 1 else "s", MIN_RECEIPTS))
    good = stale = 0
    for receipt_id in sorted(rows):
        row = rows[receipt_id]
        problems = []
        if row.get("label") not in LABELS:
            problems.append("label %r is not one of %s" % (row.get("label"), ", ".join(LABELS)))
        if not isinstance(row.get("value"), (int, float)) or isinstance(row.get("value"), bool):
            problems.append("value %r is not a number" % (row.get("value"),))
        digest, problem = _hash_source(row, root=root)
        if problem:
            problems.append(problem)
        elif digest != row.get("sha256"):
            if strict:
                problems.append("source %s no longer hashes to the recorded sha256" % row.get("source"))
            else:
                stale += 1
        if problems:
            faults.fail("%s (%s): %s" % (receipt_id, row.get("name"), "; ".join(problems)))
        elif digest == row.get("sha256"):
            good += 1
    if good:
        faults.ok("%d of the %d logged receipt%s re-hash against their own source"
                  % (good, len(rows), "" if len(rows) == 1 else "s"))
    if stale and not strict:
        faults.note("%d receipt%s name a source that changed after the receipt was written; re-run "
                    "tools\\receipts.py to re-issue %s"
                    % (stale, "" if stale == 1 else "s", "it" if stale == 1 else "them"))
    return faults, rows


def check_verify(verify_path, ledger_path=receipts.LEDGER_PATH, root=ROOT):
    """The verify file's numbers against the ledger. Returns (faults, numbers)."""
    faults = Faults()
    try:
        with open(verify_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError) as exc:
        faults.fail("%s cannot be read as JSON: %s" % (receipts._rel(verify_path), exc))
        return faults, []
    numbers = payload.get("meta_numbers")
    if not isinstance(numbers, list) or not numbers:
        faults.fail("%s carries no meta_numbers block, so none of its Meta numbers is labelled"
                    % receipts._rel(verify_path))
        return faults, []
    if len(numbers) < MIN_RECEIPTS:
        faults.fail("%s labels %d Meta number%s, and at least %d are needed"
                    % (receipts._rel(verify_path), len(numbers), "" if len(numbers) == 1 else "s",
                       MIN_RECEIPTS))

    _ledger_faults, rows = check_ledger(ledger_path, root=root)
    seen_labels = set()
    quoted = set()
    for index, row in enumerate(numbers):
        where = "meta_numbers[%d]" % index
        if not isinstance(row, dict):
            faults.fail("%s is not an object" % where)
            continue
        name = row.get("name") or where
        problems = []
        label = row.get("label")
        if label not in LABELS:
            problems.append("label %r is not one of %s" % (label, ", ".join(LABELS)))
        else:
            seen_labels.add(label)
        if not isinstance(row.get("value"), (int, float)) or isinstance(row.get("value"), bool):
            problems.append("value %r is not a number" % (row.get("value"),))
        receipt_id = row.get("receipt")
        if not isinstance(receipt_id, str) or not receipt_id:
            problems.append("no receipt id, so the number is a claim")
            logged = None
        else:
            quoted.add(receipt_id)
            logged = rows.get(receipt_id)
            if logged is None:
                problems.append("receipt %s is not in the ledger" % receipt_id)
        if logged:
            if logged.get("name") != name:
                problems.append("the ledger calls this number %r" % (logged.get("name"),))
            if logged.get("label") != label:
                problems.append("the ledger labels it %r" % (logged.get("label"),))
            if not _same_number(logged.get("value"), row.get("value")):
                problems.append("the ledger records the value %r" % (logged.get("value"),))
            digest, problem = _hash_source(logged, root=root)
            if problem:
                problems.append(problem)
            elif digest != logged.get("sha256"):
                problems.append("source %s no longer hashes to this receipt's sha256, so the number cannot "
                                "be found in it today" % logged.get("source"))
        if problems:
            faults.fail("%s: %s" % (name, "; ".join(problems)))
        else:
            origin = "%s %s" % (logged.get("source"), logged.get("locator")) if logged else "no receipt"
            faults.ok("%s = %s (%s, receipt %s) from %s"
                      % (name, row.get("value"), label, receipt_id, origin))
    missing = [label for label in LABELS if label not in seen_labels]
    if missing:
        faults.fail("%s never uses the label%s %s, so the vocabulary is not the one the card asks for"
                    % (receipts._rel(verify_path), "" if len(missing) == 1 else "s", ", ".join(missing)))
    else:
        faults.ok("all three labels appear: %s" % ", ".join(LABELS))
    if len(quoted) < MIN_RECEIPTS:
        faults.fail("%s quotes %d distinct receipt%s, and at least %d are needed"
                    % (receipts._rel(verify_path), len(quoted), "" if len(quoted) == 1 else "s",
                       MIN_RECEIPTS))
    return faults, numbers


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify that every Meta number is labelled and receipted.")
    parser.add_argument("--verify", default=None, help="the verify file to read (default: newest take)")
    parser.add_argument("--ledger", default=receipts.LEDGER_PATH)
    parser.add_argument("--counts", action="store_true", help="print the ledger counts and exit")
    args = parser.parse_args(argv)

    if args.counts:
        faults, rows = check_ledger(args.ledger)
        for line in faults.rows:
            print(line)
        return 1 if faults.failed else 0

    verify_path = args.verify or newest_verify()
    if not verify_path:
        print("FAIL no verify file under output/demo, so there is nothing to check")
        return 1
    faults, numbers = check_verify(verify_path, ledger_path=args.ledger)
    ledger_faults, rows = check_ledger(args.ledger)
    for line in ledger_faults.rows:
        faults.rows.insert(0, line)
    faults.failed = faults.failed or ledger_faults.failed
    for line in faults.rows:
        print(line)
    print("%s: %d Meta number%s, %d quoted receipt%s, %d logged"
          % (receipts._rel(verify_path), len(numbers), "" if len(numbers) == 1 else "s",
             len({row.get("receipt") for row in numbers if isinstance(row, dict)}),
             "" if len(numbers) == 1 else "s", len(rows)))
    return 1 if faults.failed else 0


if __name__ == "__main__":
    sys.exit(main())
