"""FV-4 proof harness: turn the soundness argument into a measurement (card t_11f7f43f). SUPERSEDED 2026-11-01: see the note at the end of this file.

The solver (smt_counterpoint.py) claims that every grid it can produce passes rules.py with
zero hard and zero soft findings in both the free and strict profiles, because each
constraint block is at least as strict as the matching checker method. This file turns that
claim into measurements:

  1. SAMPLE: solve many textures across keys, voicings, bars and forms, run the REAL Checker
     over every one of them, and fail on the first hard or soft finding. This is the
     soundness direction: any finding is a counterexample (a grid the solver emitted that the
     checker rejects), reported with the trace so it can be fixed.

  2. ROUND-TRIP: a solved texture is written through the project MIDI writer and re-read from
     the file, then re-checked, so what plays is what was proved.

  3. MUTATE: skip each rule block in turn and search for a model the full checker faults. A
     block that yields a violation when removed is load-bearing. Because z3 returns an
     arbitrary clean model, absence of a violation is not proof of weakness, so a block that
     never binds is reported as a warning to investigate, not a hard failure.

The ear-critic comparison against the current generator is a separate concern (Gemini needs
GEMINI_API_KEY and a rendered audio file) and is driven from the CLI, not here.

Usage:
    python tools/counterpoint/fv4_proof.py              run sample + mutate + roundtrip
    python tools/counterpoint/fv4_proof.py --quick       a small sample, fast
    python tools/counterpoint/fv4_proof.py --sample-only
    python tools/counterpoint/fv4_proof.py --mutate-only
    python tools/counterpoint/fv4_proof.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rules  # noqa: E402
import smt_counterpoint as smt  # noqa: E402


# ---------------------------------------------------------------------------
# Sample plan
# ---------------------------------------------------------------------------

# (form, bars, voices, key, mode, melody). Keys cover C major, a sharp key and a minor key
# so the scale-tone and leading-tone machinery is exercised, not just C. Sampled with
# seed=None: one clean solve each, and the seed pins only subtract solutions, so an
# unseeded model already exercises the full constraint set.
SAMPLE_GRID = [
    ("species", 2, 2, "C", "major", None),
    ("species", 4, 2, "C", "major", None),
    ("species", 4, 2, "G", "major", None),
    ("species", 4, 2, "A", "minor", None),
    ("species", 8, 2, "C", "major", None),
    ("species", 4, 3, "C", "major", None),
    ("invention", 4, 2, "C", "major", None),
    ("invention", 4, 2, "G", "major", None),
    ("canon", 4, 2, "C", "major", None),
    ("countermelody", 4, 2, "C", "major", ("D5", "F5", "A5", "D5", "C5", "A5", "G5", "A5",
                                             "D5", "E5", "F5", "A5", "G5", "F5", "E5", "C5")),
]

# A couple of seeded solves on a short texture, to show the seed-bias path is also clean.
# Kept short and few because each seeded note re-checks the solver.
SEEDED_GRID = [
    ("species", 2, 2, "C", "major", None, 1),
    ("species", 2, 2, "A", "minor", None, 2),
]

QUICK_GRID = [
    ("species", 2, 2, "C", "major", None),
    ("species", 4, 2, "A", "minor", None),
    ("invention", 4, 2, "C", "major", None),
    ("canon", 4, 2, "C", "major", None),
]

MUTABLE_BLOCKS = smt.RULE_BLOCKS
MUTATE_SOLVES = 4  # non-deterministic solves per skipped block, searching for a violation


def _spec(tonic_name, mode, voices):
    voices = (["pulse 1", "triangle"] if voices == 2
              else ["pulse 1", "pulse 2", "triangle"])
    tonic = rules.parse_pitch(tonic_name + "4") % 12
    return smt.CounterpointSpec(tonic=tonic, mode=mode, voices=voices)


def _melody_pitches(names):
    return [rules.parse_pitch(n) for n in names]


def _solve(spec, form, melody, seed=None, timeout_ms=120000, skip=()):
    return smt.build_texture(spec, form=form, seed=seed, melody=melody,
                             timeout_ms=timeout_ms, skip=skip)


def _sample(grid, seeded, timeout_ms):
    """Solve every entry and check it with the real checker. Returns a report dict."""
    rows = []
    failures = []
    jobs = [(f, b, v, k, m, mel, None) for (f, b, v, k, m, mel) in grid]
    jobs += [(f, b, v, k, m, mel, sd) for (f, b, v, k, m, mel, sd) in seeded]
    for form, bars, voices, key, mode, melody_names, seed in jobs:
        spec = _spec(key, mode, voices)
        melody = _melody_pitches(melody_names) if melody_names else None
        t0 = time.time()
        result = _solve(spec, form, melody, seed=seed, timeout_ms=timeout_ms)
        elapsed = time.time() - t0
        if result is None:
            rows.append({"form": form, "bars": bars, "voices": voices, "key": key,
                         "mode": mode, "seed": seed, "solved": False,
                         "verdict": "UNSAT", "seconds": round(elapsed, 2)})
            failures.append("UNSAT %s %s bars=%d seed=%s" % (form, key, bars, seed))
            continue
        proof = smt.check_clean(result)
        rows.append({"form": form, "bars": bars, "voices": voices, "key": key,
                     "mode": mode, "seed": seed, "solved": True,
                     "verdict": proof["verdict"], "seconds": round(elapsed, 2),
                     "hard": proof["profiles"]["strict"]["hard"],
                     "soft": proof["profiles"]["strict"]["soft"]})
        if proof["verdict"] != "CLEAN":
            findings = proof["profiles"]["strict"]["findings"]
            failures.append(
                "REFUTED %s %s bars=%d seed=%s: %s"
                % (form, key, bars, seed,
                   "; ".join("%s %s" % (f.get("rule"), f.get("message"))
                             for f in findings[:3])))
    return {"rows": rows, "failures": failures,
            "solved": sum(1 for r in rows if r["solved"]),
            "clean": sum(1 for r in rows if r.get("verdict") == "CLEAN")}


def _mutate(grid, timeout_ms):
    """Skip each block in turn and search for a checker violation (block binds)."""
    rows = []
    warnings = []
    for form, bars, voices, key, mode, melody_names in grid:
        spec = _spec(key, mode, voices)
        melody = _melody_pitches(melody_names) if melody_names else None
        applicable = [b for b in MUTABLE_BLOCKS if b not in
                      _inert_blocks(form, spec, melody)]
        for block in applicable:
            found_violation = False
            outcomes = []
            for _ in range(MUTATE_SOLVES):
                result = _solve(spec, form, melody, seed=None, timeout_ms=timeout_ms,
                                skip=(block,))
                if result is None:
                    outcomes.append("UNSAT")
                    continue
                proof = smt.check_clean(result)
                outcomes.append(proof["verdict"])
                if proof["verdict"] != "CLEAN":
                    found_violation = True
                    break
            verdict = "BINDS" if found_violation else \
                ("INERT" if all(o == "CLEAN" for o in outcomes) else "UNPROVEN")
            rows.append({"form": form, "bars": bars, "key": key, "block": block,
                         "outcome": verdict, "solves": outcomes})
            if verdict == "INERT":
                warnings.append(
                    "INERT %s %s bars=%d: skipping %s never yields a violation in %d solves"
                    % (form, key, bars, block, MUTATE_SOLVES))
    return {"rows": rows, "warnings": warnings}


def _inert_blocks(form, spec, melody):
    """Rule blocks that cannot bind for this configuration, so mutation is meaningless."""
    inert = set()
    if len(spec.voices) < 3:
        inert.add("spacing")
    if form != "invention":
        inert.add("motif")
    if melody is not None and len(spec.voices) == 2:
        # leading and seventh only apply to a free middle voice: the bass and the fixed
        # melody voice are both skipped, and with two voices there is no third to judge
        inert.add("leading")
        inert.add("seventh")
    return inert


def _roundtrip(grid, timeout_ms):
    """Write each solved texture to a MIDI file and re-check from the file."""
    rows = []
    failures = []
    for form, bars, voices, key, mode, melody_names in grid[:4]:
        spec = _spec(key, mode, voices)
        melody = _melody_pitches(melody_names) if melody_names else None
        result = _solve(spec, form, melody, seed=None, timeout_ms=timeout_ms)
        if result is None:
            rows.append({"form": form, "key": key, "outcome": "UNSAT"})
            continue
        handle, path = tempfile.mkstemp(suffix=".mid")
        os.close(handle)
        try:
            rt = smt.write_midi(result, path)
            rows.append({"form": form, "key": key, "outcome": "ROUNDTRIP",
                         "hard": rt["roundtrip_hard"], "soft": rt["roundtrip_soft"]})
            if rt["roundtrip_hard"] or rt["roundtrip_soft"]:
                failures.append("ROUNDTRIP-REFUTED %s %s: hard %d soft %d"
                                % (form, key, rt["roundtrip_hard"], rt["roundtrip_soft"]))
        finally:
            try:
                os.remove(path)
            except OSError as exc:
                print("fv4_proof: could not remove temp MIDI %s: %s" % (path, exc),
                      file=sys.stderr)
    return {"rows": rows, "failures": failures}


def run(quick=False, timeout_ms=120000, sample_only=False, mutate_only=False):
    grid = QUICK_GRID if quick else SAMPLE_GRID
    seeded = [] if quick else SEEDED_GRID
    out = {"sample": None, "mutate": None, "roundtrip": None,
           "failures": [], "warnings": []}
    if not mutate_only:
        out["sample"] = _sample(grid, seeded, timeout_ms)
        out["failures"].extend("sample: " + f for f in out["sample"]["failures"])
        out["roundtrip"] = _roundtrip(grid, timeout_ms)
        out["failures"].extend("roundtrip: " + f for f in out["roundtrip"]["failures"])
    if not sample_only:
        out["mutate"] = _mutate(grid, timeout_ms)
        out["warnings"].extend("mutate: " + w for w in out["mutate"]["warnings"])
    out["ok"] = not out["failures"]
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="FV-4 counterpoint proof harness")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--sample-only", action="store_true")
    parser.add_argument("--mutate-only", action="store_true")
    parser.add_argument("--timeout", type=int, default=120000)
    parser.add_argument("--json", dest="json_out", default=None)
    args = parser.parse_args(argv)

    report = run(quick=args.quick, timeout_ms=args.timeout,
                 sample_only=args.sample_only, mutate_only=args.mutate_only)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)

    if report["sample"]:
        s = report["sample"]
        print("SAMPLE: %d solved, %d CLEAN, %d refuted"
              % (s["solved"], s["clean"], len(s["failures"])))
        for r in s["rows"]:
            print("  %-13s %-2s %dv bars=%d seed=%s -> %s (%.1fs)"
                  % (r["form"], r["key"], r["voices"], r["bars"], r["seed"],
                     r["verdict"], r.get("seconds", 0.0)))
    if report["roundtrip"]:
        rt = report["roundtrip"]
        print("ROUND-TRIP: %d rows, %d refuted"
              % (len(rt["rows"]), len(rt["failures"])))
        for r in rt["rows"]:
            print("  %-13s %-2s -> %s hard=%s soft=%s"
                  % (r["form"], r["key"], r["outcome"],
                     r.get("hard", "-"), r.get("soft", "-")))
    if report["mutate"]:
        m = report["mutate"]
        binds = [r for r in m["rows"] if r["outcome"] == "BINDS"]
        print("MUTATE: %d blocks, %d bind (violation appears when skipped)"
              % (len(m["rows"]), len(binds)))
        for r in m["rows"]:
            print("  %-13s %-2s skip=%-8s -> %s %s"
                  % (r["form"], r["key"], r["block"], r["outcome"], r["solves"]))

    print("\n%s: %s" % ("PASS" if report["ok"] else "FAIL",
                        "no counterexample" if report["ok"]
                        else "%d counterexample(s)" % len(report["failures"])))
    for f in report["failures"]:
        print("  " + f)
    for w in report["warnings"]:
        print("  warn: " + w)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())


# SUPERSEDED 2026-11-01 (card t_11f7f43f). This harness measures `smt_counterpoint.py`, the first
# encoder, not the model that landed. The live equivalents are `counterpoint_z3.py
# --worked-examples` (appendix A row by row), `tools/counterpoint/fv4_ear_critic.py` (generator
# against generator) and the two committed suites. It is committed because `formal/FV-4-rules.md`
# section 8 names it as the FV-4 mutation harness, so a reader can run what the document cites.
# Last measured: `--quick`, PASS, no counterexample (sample clean, round-trip 0 refuted, mutate
# 24 bind, and the inert blocks are overlap, cadence and motif, none a correctness rule).

