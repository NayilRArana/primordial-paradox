"""FV-4 ear critic comparison: the Z3 generator against M1b on matched specs (card t_c58b790f).

Why this exists: FV-4 (t_11f7f43f) turns the Baroque engine's line generation into an SMT
problem, and the card asks one question about it, which a proof harness cannot answer: is the
Z3 output musically at least as good as what M1b (tools/counterpoint/generate.py, t_944ef2b6)
already ships? This harness builds matched pairs, scores every piece with the same instruments,
and prints the table the report is written from.

What a "matched pair" means here, and why
    M1b is a seeded random search: one integer seed selects everything it writes. The Z3 solver
    in tools/counterpoint/counterpoint_z3.py has no seed stream; its output is a function of the
    spec it is given (its own spec says so). So the only way to hold the input identical across
    both engines is to make the seed CHOOSE the spec and then hand that same spec to each engine:

    arm fixed-subject  the seed builds a 32 eighth-note subject on pulse 1 (scale steps, seeded),
                       and each engine writes the second voice against it. M1b uses
                       build_countermelody(melody_line=subject); Z3 pins pulse 1 to the subject
                       and solves for pulse 2. Both pieces therefore carry the same soprano, so
                       every difference measured on the counter-line is the generator's.
    arm free-invention the seed only picks the index. M1b builds build_invention(bars=4) from
                       build_clean; Z3 solves a free two-voice texture of the same size and key.
                       These are not the same notes, so this arm compares distributions.
    arm canon          same as free-invention for build_canon(bars=4) against a free Z3 canon at
                       the octave a bar later (delay 8 positions, interval 12), which is the
                       geometry M1b's own answer uses.

Instruments, the same for both engines
    rules.analyse   the M1a checker (tools/counterpoint/rules.py), profiles free and strict, so
                    the finding count per 100 bars and the failing rule ids come from the engine
                    the cue gate uses, not from this harness.
    clash           the M0 vertical classifier (tools/counterpoint/clash.py): raw clashes and
                    strong-beat raw clashes, and the ear loop's own dose formula.
    hook_score      the memory score of a melody (tools/hook_score.py), 0 to 100 with reasons.
    contour         leaps, steps, repeats, direction changes and range, computed here, because
                    nothing in the tree measures whether a generated line moves like music.
    ear_critic      tools/ear_critic.py is the Gemini listener named in the card. It needs
                    GEMINI_API_KEY and a rendered audio file; this harness reports its key state
                    (--ear-check) and never invents a score for it.

Usage
    python tools/counterpoint/fv4_ear_critic.py --ear-check
    python tools/counterpoint/fv4_ear_critic.py --all
    python tools/counterpoint/fv4_ear_critic.py --arm fixed-subject --seeds 1 2 3 --guided
    python tools/counterpoint/fv4_ear_critic.py --all --json out/fv4_ear/scores.json

Exit codes: 0 every arm measured, 2 an arm could not be produced, 3 the ear critic could not be
called (reported separately from 0 so a caller never reads 0 as "the critic agreed").
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
for path in (HERE, TOOLS):
    if path not in sys.path:
        sys.path.insert(0, path)

import clash  # noqa: E402
import counterpoint_z3 as z3cp  # noqa: E402
import ear_critic  # noqa: E402
import generate  # noqa: E402
import hook_score  # noqa: E402
import rules  # noqa: E402

SOPRANO = generate.SOPRANO
ALTO = generate.ALTO
KEY = "C major"
KEY_TUPLE = (0, "major")
POSITIONS = 32          # four 4/4 bars of eighth notes, the grid both engines build on
DEFAULT_SEEDS = (1, 2, 3, 5, 8, 13)
ARMS = ("fixed-subject", "free-invention", "canon")
WEAK_CLASH_SHARE = 0.1  # ear_loop.py's weight for a clash off the strong beat
MAX_LEAP_DEFAULT = 4    # the guided variant's melodic budget, in semitones


# ----------------------------------------------------------------- spec building

def subject_for_seed(seed, positions=POSITIONS, low=64, high=79):
    """A seeded subject on the eighth grid: scale steps, one pitch per position.

    generate.Generator.subject() writes durations from the corpus shares, including sixteenths on
    the same slot, which the Z3 texture (one pitch per grid position) cannot carry. The seed's
    pitch walk is kept and the rhythm is flattened to eighths so both engines see one line.
    """
    gen = generate.Generator(seed, KEY)
    pool = [p for p in gen.scale_pitches(low, high)]
    rng = random.Random(1000 + int(seed))
    pitch = min(pool, key=lambda p: abs(p - 72))
    line = []
    for slot in range(positions):
        line.append((slot, 1, pitch))
        stepwise = [p for p in pool if 1 <= abs(p - pitch) <= 2]
        if stepwise and rng.random() < 0.75:
            pitch = rng.choice(stepwise)
        elif stepwise:
            pitch = rng.choice([p for p in pool if 3 <= abs(p - pitch) <= 5] or stepwise)
    return line


def lines_from_model(result):
    """The solver's model as M1b's line shape: [(slot, duration, pitch)] per voice."""
    out = {}
    for voice, row in result["model"].items():
        out[voice] = [(slot, 1, pitch) for slot, pitch in enumerate(row)]
    return out


def solve_texture(pins=None, positions=POSITIONS, voices=(SOPRANO, ALTO), timeout_ms=120000,
                  guided=False, max_leap=MAX_LEAP_DEFAULT):
    """One Z3 solve on the shared grid, optionally with the guided melodic budget.

    guided adds two rules the plain model does not carry: no leap wider than max_leap semitones
    between adjacent positions, and no more than two leaps in the same direction in a row. It is
    the fix this harness measures, so it lives here and not in counterpoint_z3.py, which stays the
    pure encoding of the FV-4 rule spec.
    """
    texture = z3cp.Texture(list(voices), positions, beats=4, key=KEY_TUPLE)
    for voice, line in (pins or {}).items():
        for slot, _duration, pitch in line:
            if slot < positions:
                texture.pin(voice, slot, pitch)
    constraints = z3cp.build_constraints(texture, scale_only=True)
    if guided:
        # Only the generated voices carry the melodic budget. A pinned voice is the spec: the
        # subject comes from M1b's own builder, leaps included, and must not be second-guessed.
        guided_voices = [voice for voice in texture.voices if voice not in (pins or {})]
        for voice in guided_voices:
            for slot in range(1, positions):
                constraints.append(z3cp.Constraint(
                    "GUIDED", "%s leap <= %d @t=%d" % (voice, max_leap, slot),
                    abs(texture.var(voice, slot) - texture.var(voice, slot - 1)) <= max_leap))
            for slot in range(2, positions):
                a = texture.var(voice, slot) - texture.var(voice, slot - 1)
                b = texture.var(voice, slot - 1) - texture.var(voice, slot - 2)
                constraints.append(z3cp.Constraint(
                    "GUIDED", "%s no third leap the same way @t=%d" % (voice, slot),
                    z3cp.z3.Or(abs(a) <= 2, abs(b) <= 2, a * b <= 0)))
    solver = z3cp._solver_for(constraints, int(timeout_ms), track=False)
    solver.set("timeout", int(timeout_ms))
    started = z3cp.time.perf_counter()
    status = solver.check()
    payload = {"status": str(status), "assertions": len(constraints), "model": None,
               "core_rules": [], "elapsed_s": round(z3cp.time.perf_counter() - started, 4)}
    if status == z3cp.z3.sat:
        model = solver.model()
        payload["model"] = {
            voice: [model.evaluate(texture.var(voice, slot), model_completion=True).as_long()
                    for slot in range(positions)]
            for voice in texture.voices}
    if status == z3cp.z3.unknown:
        payload["reason"] = solver.reason_unknown()
    return payload


def solve_canon(positions=POSITIONS, timeout_ms=120000, guided=False):
    """A free two-voice canon at the octave a bar later, optionally contour guided."""
    texture = z3cp.Texture([SOPRANO, ALTO], positions, beats=4, key=KEY_TUPLE)
    constraints = z3cp.build_constraints(texture, scale_only=True)
    for slot in range(8, positions):
        constraints.append(z3cp.Constraint(
            "CANON", "%s imitates %s @t=%d" % (SOPRANO, ALTO, slot),
            texture.var(SOPRANO, slot) == texture.var(ALTO, slot - 8) + 12))
    if guided:
        for voice in texture.voices:
            for slot in range(1, positions):
                constraints.append(z3cp.Constraint(
                    "GUIDED", "%s leap <= %d @t=%d" % (voice, MAX_LEAP_DEFAULT, slot),
                    abs(texture.var(voice, slot) - texture.var(voice, slot - 1))
                    <= MAX_LEAP_DEFAULT))
    solver = z3cp._solver_for(constraints, int(timeout_ms), track=False)
    solver.set("timeout", int(timeout_ms))
    started = z3cp.time.perf_counter()
    status = solver.check()
    payload = {"status": str(status), "assertions": len(constraints), "model": None,
               "elapsed_s": round(z3cp.time.perf_counter() - started, 4)}
    if status == z3cp.z3.sat:
        model = solver.model()
        payload["model"] = {
            voice: [model.evaluate(texture.var(voice, slot), model_completion=True).as_long()
                    for slot in range(positions)]
            for voice in texture.voices}
    if status == z3cp.z3.unknown:
        payload["reason"] = solver.reason_unknown()
    return payload


# -------------------------------------------------------------------- measuring

def contour_stats(line):
    """How a line moves: leaps, steps, repeats, direction and range."""
    pitches = [pitch for _slot, _duration, pitch in line]
    intervals = [b - a for a, b in zip(pitches, pitches[1:])]
    if not intervals:
        return {"notes": len(pitches), "range": 0, "mean_abs_interval": 0.0, "max_leap": 0,
                "leap_share": 0.0, "step_share": 0.0, "repeat_share": 0.0,
                "distinct_pitches": len(set(pitches)), "direction_changes": 0,
                "longest_run": 0}
    leaps = [i for i in intervals if abs(i) > 2]
    steps = [i for i in intervals if 0 < abs(i) <= 2]
    repeats = [i for i in intervals if i == 0]
    moves = [i for i in intervals if i != 0]
    direction_changes = 0
    for a, b in zip(moves, moves[1:]):
        if (a > 0) != (b > 0):
            direction_changes += 1
    longest = 1
    run = 1
    for a, b in zip(moves, moves[1:]):
        if (a > 0) == (b > 0):
            run += 1
            longest = max(longest, run)
        else:
            run = 1
    return {
        "notes": len(pitches),
        "range": max(pitches) - min(pitches),
        "mean_abs_interval": round(sum(abs(i) for i in intervals) / float(len(intervals)), 3),
        "max_leap": max(abs(i) for i in intervals),
        "leap_share": round(len(leaps) / float(len(intervals)), 3),
        "step_share": round(len(steps) / float(len(intervals)), 3),
        "repeat_share": round(len(repeats) / float(len(intervals)), 3),
        "distinct_pitches": len(set(pitches)),
        "direction_changes": direction_changes,
        "longest_run": longest,
    }


def rule_block(lines, profile):
    """rules.analyse on the lines, with the counts the report quotes."""
    notes = {voice: generate.to_notes(line) for voice, line in lines.items()}
    score = rules.Score.from_notes(notes, division=generate.DIVISION,
                                   time_sig=generate.TIME_SIG, key=KEY_TUPLE)
    result = rules.analyse(score, profile=profile)
    summary = result["summary"]
    bars = max(1, result["bars"])
    by_rule = dict(summary["by_rule"])
    by_severity = dict(summary["by_severity"])
    findings = result["findings"]
    return {
        "bars": bars,
        "notes": result["notes"],
        "by_severity": by_severity,
        "by_rule": by_rule,
        "per_100_bars": {name: round(100.0 * count / bars, 2)
                         for name, count in by_severity.items()},
        "findings": [{"rule": f["rule"], "severity": f["severity"], "bar": f["bar"],
                      "beat": f["beat"], "voices": f.get("voices"),
                      "detail": f.get("detail")} for f in findings[:40]],
        "finding_count": len(findings),
    }


def clash_block(midi_path):
    """The M0 classifier's raw and strong-beat raw clash counts, plus the ear loop's dose."""
    score = clash.load_score(midi_path, key_name=KEY)
    events = clash.analyse(score)
    summary = clash.summarise(score, events)
    bars = max(1, score.bars)
    raw = summary["raw_total"]
    strong = summary["strong_raw"]
    dose = (strong + WEAK_CLASH_SHARE * (raw - strong)) / float(bars)
    return {"raw": raw, "strong": strong, "bars": bars, "dose_per_bar": round(dose, 4),
            "by_class": summary["by_class"]}


def hook_block(line, path):
    """hook_score on one line, through its melody JSON reader."""
    payload = {"name": os.path.basename(path).rsplit(".", 1)[0],
               "beats_per_bar": 4, "ppq": generate.DIVISION,
               "notes": [{"start": slot * 0.5, "dur": duration * 0.5, "pitch": pitch}
                         for slot, duration, pitch in line]}
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    report = hook_score.score_melody_json(path)
    return {"total": report["score"],
            "criteria": {item["key"]: item["points"] for item in report["criteria"]}}


def to_smf_lines(lines):
    """M1b's (slot, duration, pitch) lines as the tick tuples humanize.write_smf reads."""
    return {voice: [(slot * generate.EIGHTH, (slot + duration) * generate.EIGHTH, pitch, 96)
                    for slot, duration, pitch in line]
            for voice, line in lines.items()}


def measure_piece(name, lines, out_dir):
    """Every instrument on one piece, with its MIDI, recipe and melody JSONs on disk."""
    os.makedirs(out_dir, exist_ok=True)
    midi_path = os.path.join(out_dir, name + ".mid")
    generate.write_midi(to_smf_lines(lines), midi_path, key=KEY)
    record = {"name": name, "lines": {voice: [list(n) for n in line]
                                      for voice, line in lines.items()},
              "midi": os.path.abspath(midi_path),
              "free": rule_block(lines, "free"),
              "strict": rule_block(lines, "strict"),
              "clash": clash_block(midi_path),
              "contour": {}, "hook": {}}
    for voice, line in lines.items():
        slug = voice.replace(" ", "_")
        record["contour"][voice] = contour_stats(line)
        record["hook"][voice] = hook_block(line, os.path.join(out_dir, "%s_%s.json" % (name, slug)))
    return record


# ----------------------------------------------------------------------- engines

def m1b_pieces(arm, seeds, out_dir):
    """M1b's own output for each seed.

    For the free arms the shipped path is build_clean (search until the checker passes), so that
    is what runs. The fixed-subject arm has no clean seed to find: M1b's countermelody builder
    writes a consonant note against the given soprano but never checks the dissonance rules, so
    build_clean refuses after 200 seeds and the raw builder output is the measurement. The refusal
    is recorded per seed rather than hidden.
    """
    corpus = generate.Corpus()
    pieces = []
    for seed in seeds:
        gen = generate.Generator(seed, KEY, corpus)
        note = "raw"
        if arm == "fixed-subject":
            subject = subject_for_seed(seed)
            builder = lambda g: generate.build_countermelody(g, melody_line=subject,
                                                             bars=POSITIONS // 8)
            try:
                lines, _result, _notes = generate.build_clean(gen, builder)
                note = "build_clean"
            except ValueError:
                lines = builder(gen)
                note = "build_clean refused; raw builder"
        elif arm == "free-invention":
            try:
                lines, _result, _notes = generate.build_clean(
                    gen, lambda g: generate.build_invention(g, bars=4))
                note = "build_clean"
            except ValueError:
                lines = generate.build_invention(gen, bars=4)
                note = "build_clean refused; raw builder"
        elif arm == "canon":
            try:
                lines, _result, _notes = generate.build_clean(
                    gen, lambda g: generate.build_canon(g, bars=4))
                note = "build_clean"
            except ValueError:
                lines = generate.build_canon(gen, bars=4)
                note = "build_clean refused; raw builder"
        else:
            raise ValueError("unknown arm %r" % (arm,))
        pieces.append(("m1b/%s/s%d" % (arm, seed), lines, note))
    return pieces


def z3_pieces(arm, seeds, out_dir, guided=False):
    """The Z3 path for each seed's spec, and the solver's own verdict per piece."""
    pieces = []
    for seed in seeds:
        if arm == "fixed-subject":
            subject = subject_for_seed(seed)
            result = solve_texture({SOPRANO: subject}, guided=guided)
        elif arm == "free-invention":
            result = solve_texture(guided=guided)
        elif arm == "canon":
            result = solve_canon(guided=guided)
        else:
            raise ValueError("unknown arm %r" % (arm,))
        if result["status"] != "sat":
            print("SKIP z3%s %s seed %d came back %s" % ("-guided" if guided else "", arm,
                                                         seed, result["status"]))
            continue
        tag = "z3g" if guided else "z3"
        pieces.append(("%s/%s/s%d" % (tag, arm, seed), lines_from_model(result),
                       "z3 sat, %.2fs" % result.get("elapsed_s", 0.0) if "elapsed_s" in result
                       else "z3 sat"))
    return pieces


# --------------------------------------------------------------------- reporting

def mean_variance(values):
    values = list(values)
    if not values:
        return {"n": 0, "mean": None, "variance": None}
    return {"n": len(values), "mean": round(statistics.mean(values), 3),
            "variance": round(statistics.variance(values), 3) if len(values) > 1 else 0.0}


def summarise(records):
    """Per engine and arm: violations per 100 bars, critic proxies with their variance."""
    buckets = {}
    for record in records:
        engine = record["name"].split("/")[0]
        arm = record["name"].split("/")[1]
        group = buckets.setdefault((engine, arm), [])
        group.append(record)
    table = []
    for (engine, arm), group in sorted(buckets.items()):
        bars = sum(r["free"]["bars"] for r in group) or 1
        row = {
            "engine": engine, "arm": arm, "pieces": len(group),
            "bars": bars,
            "hard_free": sum(r["free"]["by_severity"].get("hard", 0) for r in group),
            "soft_free": sum(r["free"]["by_severity"].get("soft", 0) for r in group),
            "hard_strict": sum(r["strict"]["by_severity"].get("hard", 0) for r in group),
            "soft_strict": sum(r["strict"].get("by_severity", {}).get("soft", 0) for r in group),
            "style_strict": sum(r["strict"].get("by_severity", {}).get("style", 0) for r in group),
            "raw_clash": sum(r["clash"]["raw"] for r in group),
            "strong_clash": sum(r["clash"]["strong"] for r in group),
            "hook": mean_variance(r["hook"][SOPRANO]["total"] for r in group),
            "hook_alto": mean_variance(r["hook"][ALTO]["total"] for r in group),
            "clash_dose": mean_variance(r["clash"]["dose_per_bar"] for r in group),
            "leap_share_alto": mean_variance(r["contour"][ALTO]["leap_share"] for r in group),
            "mean_abs_interval_alto": mean_variance(
                r["contour"][ALTO]["mean_abs_interval"] for r in group),
            "repeat_share_alto": mean_variance(r["contour"][ALTO]["repeat_share"] for r in group),
            "range_alto": mean_variance(r["contour"][ALTO]["range"] for r in group),
            "longest_run_alto": mean_variance(r["contour"][ALTO]["longest_run"] for r in group),
        }
        for key in ("hard_free", "soft_free", "hard_strict", "soft_strict", "style_strict",
                    "raw_clash", "strong_clash"):
            row[key + "_per_100_bars"] = round(100.0 * row[key] / bars, 2)
        table.append(row)
    return table


def worst_offenders(records, limit=6):
    """The pieces with the most findings under the strict profile, with the rule ids named."""
    ranked = sorted(
        records,
        key=lambda r: (-r["strict"]["by_severity"].get("hard", 0),
                       -r["strict"].get("finding_count", 0),
                       -r["clash"]["raw"]))
    out = []
    for record in ranked[:limit]:
        by_rule = record["strict"]["by_rule"]
        out.append({
            "name": record["name"],
            "hard_strict": record["strict"]["by_severity"].get("hard", 0),
            "soft_strict": record["strict"].get("by_severity", {}).get("soft", 0),
            "rules": sorted(by_rule.items(), key=lambda item: -item[1])[:4],
            "raw_clash": record["clash"]["raw"],
            "leap_share_alto": record["contour"][ALTO]["leap_share"],
        })
    return out


def ear_check():
    """The Gemini ear critic's key state, without sending anything."""
    key = ear_critic.__dict__.get("key_present")
    present = bool(key and key())
    print("ear_critic key_present: %s" % ("yes" if present else "no"))
    print("ear_critic model: %s" % ear_critic.model_name())
    print("rubric prompt bytes: %d" % len(ear_critic.rubric_prompt()))
    return present


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="FV-4 ear critic: Z3 constrained generation against M1b (card t_c58b790f)")
    parser.add_argument("--arm", choices=ARMS, action="append", default=None,
                        help="arm to run (repeatable); default --all")
    parser.add_argument("--all", action="store_true", help="all three arms")
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument("--out-dir", default=os.path.join("out", "fv4_ear_critic"))
    parser.add_argument("--json", dest="json_out", default=None)
    parser.add_argument("--guided", action="store_true",
                        help="also run the guided (contour budget) Z3 variant as the fix demo")
    parser.add_argument("--ear-check", action="store_true",
                        help="only report the Gemini ear critic's key state and exit")
    parser.add_argument("--timeout-ms", type=int, default=120000)
    args = parser.parse_args(argv)

    if args.ear_check:
        return 0 if ear_check() else 3

    arms = args.arm or (list(ARMS) if args.all or not args.arm else [])
    if not arms:
        parser.error("pass --arm <name>, --all or --ear-check")

    out_root = os.path.join(ROOT, args.out_dir)
    os.makedirs(out_root, exist_ok=True)
    records = []
    failures = []
    for arm in arms:
        for name, lines, note in m1b_pieces(arm, args.seeds, out_root):
            try:
                record = measure_piece(name, lines, os.path.join(out_root, arm))
                record["note"] = note
                records.append(record)
            except ValueError as error:
                failures.append("%s: %s" % (name, error))
                print("FAIL %s: %s" % (name, error))
        for name, lines, note in z3_pieces(arm, args.seeds, out_root):
            try:
                record = measure_piece(name, lines, os.path.join(out_root, arm))
                record["note"] = note
                records.append(record)
            except ValueError as error:
                failures.append("%s: %s" % (name, error))
                print("FAIL %s: %s" % (name, error))
        if args.guided:
            for name, lines, note in z3_pieces(arm, args.seeds, out_root, guided=True):
                try:
                    record = measure_piece(name, lines, os.path.join(out_root, arm))
                    record["note"] = note
                    records.append(record)
                except ValueError as error:
                    failures.append("%s: %s" % (name, error))
                    print("FAIL %s: %s" % (name, error))

    table = summarise(records)
    payload = {"card": "t_c58b790f", "seeds": args.seeds, "positions": POSITIONS, "key": KEY,
               "arms": arms, "guided": bool(args.guided), "table": table,
               "worst": worst_offenders(records), "records": records, "failures": failures}
    print("%-4s %-15s %3s %6s %6s %6s %6s %8s %8s %8s %8s %8s" % (
        "eng", "arm", "n", "hardF", "softF", "hardS", "softS", "hard/100", "hookS", "hookA",
        "leapA", "clash/bar"))
    for row in table:
        print("%-4s %-15s %3d %6d %6d %6d %6d %8.2f %8s %8s %8s %8s" % (
            row["engine"], row["arm"], row["pieces"], row["hard_free"], row["soft_free"],
            row["hard_strict"], row["soft_strict"], row["hard_strict_per_100_bars"],
            row["hook"]["mean"], row["hook_alto"]["mean"], row["leap_share_alto"]["mean"],
            row["clash_dose"]["mean"]))
    if args.json_out:
        target = args.json_out if os.path.isabs(args.json_out) else os.path.join(ROOT, args.json_out)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1)
        print("json: %s" % target)
    return 0 if not failures else 2


if __name__ == "__main__":
    sys.exit(main())
