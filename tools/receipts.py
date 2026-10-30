#!/usr/bin/env python3
"""receipts.py: every Meta number in a take's record, labelled and receipted.

Why this file exists
    Card t_7450df91 (RECEIPTS-LABELS). The submission's Technical depth and Demo trust rest on one
    promise: no mystery numbers (Quetzal's practice, relayed by Xava in #build-for-your-world on
    2026-10-26) and "a verifier that fails the build if any quote or number can't be found"
    (Operacija Dvina, relayed by Mario Vilnius the same day). A visitor, a judge and the judge panel
    all read `output/..._verify.json` beside a capture, so that is the file where a Meta number has
    to say where it came from. This module is the one place that decides which of the three labels a
    Meta number carries, and the one place that writes the receipt for it.

The three labels, and nothing else
    measured  the value is read out of a committed file, or counted from that file's own rows, and
              the receipt names the file, the locator inside it and the file's sha256. Anyone can
              re-read the same bytes and get the same number.
    computed  the value is arithmetic over numbers measured in this same ledger, and the receipt
              carries the formula as well as the source, so the sum can be checked by hand.
    inferred  no file records the value. It is read off a plan or a shot table, which is a reading
              and not a measurement, and the receipt says so in words.

    A number that is none of the three is not a number this project may print. tools\\check_receipts.py
    is the verifier: it re-reads every receipt in a verify file against the ledger, re-hashes each
    source, and exits 1 on the first number that cannot be found.

What is written, and where
    data\\receipts\\meta_receipts.jsonl   append only, one JSON object per line, one line per distinct
                                        (name, label, value, source, sha256). A second run over the
                                        same inputs appends nothing, so the file is a ledger and not
                                        a log of how often someone ran the tool.

Usage
    python tools\\receipts.py                     print the labelled numbers and the ledger state
    python tools\\receipts.py --write PATH        log the receipts, then add the `meta_numbers` block
                                                 to an existing verify file at PATH
    python tools\\receipts.py --ledger PATH       read and append to another ledger
    python tools\\receipts.py --json              print the labelled numbers as JSON

Exit codes
    0  the numbers were read (and logged, and written when asked)
    1  a source is missing or unreadable, so a receipt would have been invented
    2  bad argument
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER_PATH = os.path.join(ROOT, "data", "receipts", "meta_receipts.jsonl")
BAKE_PATH = os.path.join(ROOT, "data", "meta_bake.json")
SCRIPT_PATH = os.path.join(ROOT, "knowledge", "DEMO-SCRIPT.md")
BRIDGE_DIR = os.path.join(ROOT, "data", "ai_cache", "bridge")

LABELS = ("measured", "computed", "inferred")

# The shot table's three S6 TALK turns (knowledge/DEMO-SCRIPT.md section 4). The demo script is the only
# file that says how many turns a capture is planned to show, so the count for a finished take is inferred
# from it rather than measured off the video, and this constant is the locator the receipt carries.
TALK_TURN_TIMES = ("2:15.03", "2:18.53", "2:23.53")


class ReceiptError(Exception):
    """A number that could not be labelled from a real source, so nothing was written for it."""


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    """The sha256 of a file's bytes, or None when it cannot be read."""
    try:
        with open(path, "rb") as handle:
            return _sha256_bytes(handle.read())
    except OSError:
        return None


def sha256_tree(directory):
    """The sha256 of a directory's own manifest: one line per file, sorted, path then hash.

    A directory is not a file, so its receipt hashes a manifest of its contents instead. The manifest is
    built from sorted relative paths and each file's own sha256, so adding, removing or editing any one
    file changes the number and the receipt stops matching.
    """
    if not os.path.isdir(directory):
        return None
    rows = []
    for base, _dirs, names in os.walk(directory):
        for name in names:
            path = os.path.join(base, name)
            digest = sha256_file(path)
            if digest is None:
                return None
            rows.append("%s\t%s" % (os.path.relpath(path, directory).replace("\\", "/"), digest))
    if not rows:
        return None
    return _sha256_bytes(("\n".join(sorted(rows)) + "\n").encode("utf-8"))


def _rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as exc:
        raise ReceiptError("cannot read %s as JSON: %s" % (_rel(path), exc))


def _receipt_id(name, label, value, source, locator):
    """A stable id: the same number from the same place keeps the same receipt forever."""
    seed = "%s|%s|%s|%s|%s" % (name, label, value, source, locator)
    return "rcpt-" + _sha256_bytes(seed.encode("utf-8"))[:16]


def _number(name, value, label, source, locator, why, formula=None, sha=None):
    if label not in LABELS:
        raise ReceiptError("%s is labelled %r, and the three labels are %s"
                           % (name, label, ", ".join(LABELS)))
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReceiptError("%s carries %r, and a Meta number is a number" % (name, value))
    if not sha:
        raise ReceiptError("%s has no sha256 for %s, so its receipt would be an assertion" % (name, source))
    row = {"name": name, "value": value, "label": label, "source": source,
           "locator": locator, "why": why, "sha256": sha,
           "receipt": _receipt_id(name, label, value, source, locator)}
    if formula:
        row["formula"] = formula
    return row


def _bake_block(bake, key):
    block = bake.get("bake") or {}
    if key not in block:
        raise ReceiptError("data/meta_bake.json has no bake.%s, so no receipt can be written for it" % key)
    return block[key]


def meta_numbers(ledger_path=LEDGER_PATH, bake_path=BAKE_PATH, script_path=SCRIPT_PATH,
                 bridge_dir=BRIDGE_DIR):
    """Every Meta number this build can vouch for, each with a label and one logged receipt.

    The first seven describe the shipped build's Meta work and are answered from data/meta_bake.json and
    the bridge's own receipt files. The last describes a capture and is inferred from the shot table,
    because no file records how many TALK turns a finished video showed.
    """
    bake = _read_json(bake_path)
    bake_sha = sha256_file(bake_path)
    if not bake_sha:
        raise ReceiptError("cannot hash data/meta_bake.json, so no receipt can be written")
    bake_src = _rel(bake_path)

    calls = _bake_block(bake, "calls_attempted")
    rows = _bake_block(bake, "rows")
    live = _bake_block(bake, "live")
    fallback_stated = _bake_block(bake, "fallback")
    system_chars = _bake_block(bake, "system_chars")
    fallback_sum = int(calls) - int(live)
    if fallback_sum != int(fallback_stated):
        raise ReceiptError("data/meta_bake.json says %d fallback rows, and calls_attempted minus live is %d"
                           % (int(fallback_stated), fallback_sum))

    numbers = [
        _number("meta.model_calls", int(calls), "measured", bake_src, "bake.calls_attempted",
                "read straight out of the bake's own header, which tools/bake_meta.py writes",
                sha=bake_sha),
        _number("meta.rows", int(rows), "measured", bake_src, "bake.rows",
                "the count of answer rows the bake file carries", sha=bake_sha),
        _number("meta.live_rows", int(live), "measured", bake_src, "bake.live",
                "the rows the bake records as answered from the recorded cache", sha=bake_sha),
        _number("meta.fallback_rows", fallback_sum, "computed", bake_src,
                "bake.calls_attempted - bake.live, cross-checked against bake.fallback",
                "the calls that returned no live answer, so the hand written fallback stood in",
                formula="bake.calls_attempted - bake.live", sha=bake_sha),
        _number("meta.system_chars", int(system_chars), "measured", bake_src, "bake.system_chars",
                "the length of the system prompt the bake sent, counted by the baker", sha=bake_sha),
        _number("meta.live_share_pct", round(100.0 * float(live) / float(calls), 1) if calls else 0.0,
                "computed", bake_src, "bake.live / bake.calls_attempted",
                "the share of the build's Meta answers that came back from a recorded call, as a percentage",
                formula="bake.live / bake.calls_attempted * 100", sha=bake_sha),
    ]

    bridge_sha = sha256_tree(bridge_dir)
    if not bridge_sha:
        raise ReceiptError("no readable receipt file under data/ai_cache/bridge, so the call count has no source")
    bridge_files = 0
    for _base, _dirs, names in os.walk(bridge_dir):
        bridge_files += len(names)
    numbers.append(
        _number("meta.bridge_receipts", bridge_files, "measured", _rel(bridge_dir) + "/",
                "one file per logged bridge call, counted, and the manifest hashed",
                "how many model calls the local bridge kept a receipt for, which is what a receipt is",
                sha=bridge_sha))

    script_sha = sha256_file(script_path)
    if not script_sha:
        raise ReceiptError("cannot read knowledge/DEMO-SCRIPT.md, so the turn count has no source")
    numbers.append(
        _number("meta.talk_turns_onscreen", len(TALK_TURN_TIMES), "inferred", _rel(script_path),
                "section 4, the S6 rows at %s" % ", ".join(TALK_TURN_TIMES),
                "no file records the turns a finished capture showed, so the count is read off the shot "
                "table's own plan and is an inference about the video, not a measurement of it",
                sha=script_sha))

    _log(numbers, ledger_path)
    return numbers


def read_ledger(ledger_path=LEDGER_PATH):
    """Every receipt row already logged, in file order, keyed by id."""
    rows = {}
    if not os.path.exists(ledger_path):
        return rows
    with open(ledger_path, "r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise ReceiptError("%s line %d is not JSON: %s" % (_rel(ledger_path), number, exc))
            if not isinstance(row, dict) or not row.get("id"):
                raise ReceiptError("%s line %d carries no receipt id" % (_rel(ledger_path), number))
            rows[row["id"]] = row
    return rows


def _log(numbers, ledger_path=LEDGER_PATH):
    """Append one line per number that is not already in the ledger. Returns the ids appended."""
    existing = read_ledger(ledger_path)
    fresh = []
    for row in numbers:
        if row["receipt"] in existing:
            continue
        fresh.append({"id": row["receipt"], "logged_at": _utc_now(), "name": row["name"],
                      "label": row["label"], "value": row["value"], "source": row["source"],
                      "locator": row["locator"], "sha256": row["sha256"],
                      "why": row["why"], "formula": row.get("formula")})
    if not fresh:
        return []
    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
    with open(ledger_path, "a", encoding="utf-8", newline="\n") as handle:
        for row in fresh:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return [row["id"] for row in fresh]


def _utc_now():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_into(verify_path, numbers=None, ledger_path=LEDGER_PATH):
    """Add the labelled numbers to an existing verify file. Returns the payload written.

    The block is replaced, never merged, so a stale number cannot survive beside a fresh one.
    """
    try:
        with open(verify_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError) as exc:
        raise ReceiptError("cannot read %s as JSON: %s" % (_rel(verify_path), exc))
    if numbers is None:
        numbers = meta_numbers(ledger_path=ledger_path)
    payload["meta_numbers"] = numbers
    with open(verify_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def summary_lines(numbers, ledger_path=LEDGER_PATH):
    """One readable line per number, for a tool's own print and for tools/check_receipts.py."""
    lines = []
    for row in numbers:
        lines.append("%s = %s (%s, receipt %s) from %s %s"
                     % (row["name"], row["value"], row["label"], row["receipt"], row["source"],
                        row["locator"]))
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(description="Label every Meta number and log its receipt.")
    parser.add_argument("--write", default=None, metavar="VERIFY",
                        help="also write the meta_numbers block into this verify file")
    parser.add_argument("--ledger", default=LEDGER_PATH)
    parser.add_argument("--json", action="store_true", help="print the numbers as JSON")
    args = parser.parse_args(argv)

    try:
        numbers = meta_numbers(ledger_path=args.ledger)
        if args.write:
            write_into(args.write, numbers=numbers, ledger_path=args.ledger)
    except ReceiptError as exc:
        print("FAIL %s" % exc)
        return 1

    if args.json:
        print(json.dumps(numbers, indent=2, sort_keys=True))
    else:
        for line in summary_lines(numbers):
            print(line)
    logged = read_ledger(args.ledger)
    labels = {}
    for row in numbers:
        labels[row["label"]] = labels.get(row["label"], 0) + 1
    print("ledger %s: %d receipt%s logged; this build labels %s"
          % (_rel(args.ledger), len(logged), "" if len(logged) == 1 else "s",
             ", ".join("%d %s" % (labels[key], key) for key in LABELS if key in labels)))
    if args.write:
        print("wrote the meta_numbers block into %s" % _rel(args.write))
    return 0


if __name__ == "__main__":
    sys.exit(main())
