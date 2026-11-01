"""FV-4: the M1a counterpoint rules as Z3 constraints, so generated lines are proven rule clean. SUPERSEDED 2026-11-01: see the note at the end of this file.

Formal-verification plan (manager, 2026-10-26), layer 4, card t_11f7f43f: make the Baroque
engine's line generation an SMT problem, "so every generated invention or canon is proven
rule clean". The constraints here are the rules of tools/counterpoint/rules.py (M1a,
t_836dbb1a) read off the Checker class method by method, including the soft rules, so one
encoding is clean under BOTH the free and the strict profile.

THE MODEL

A texture is a grid of pitches: every voice attacks one note on every beat of 4/4
(homorhythmic, no rests), in one declared key, each solved pitch a tone of that scale (minor
includes the raised leading tone) inside the voice's NES_RANGES window. Voices are given in
rank order (top first) and a strict order constraint holds at every beat, so the mean-pitch
rank rules.py computes can never disagree with the construction. Homorhythm makes every note
freshly attacked, which is what lets the device rules become quantifier-free integer
constraints on three consecutive beats.

RULE MAPPING (each block cites the rules.py method it mirrors)

  vertical   Checker.check_vertical + device_for: a freshly attacked note dissonant against
             any sounding voice on a strong or medium beat is a hard finding (CP-01) unless
             it leaves by step, which is an appoggiatura, soft in strict (CP-06). We forbid
             dissonance outright there: stricter than free, equal to strict, sound in both.
             On a weak beat a dissonant pair may stand only when one of its notes is a
             strict passing tone (step in, step out, same direction) or a strict neighbour
             (steps back to where it came from): the two device_for branches that pass
             silently. Escape (CP-18) and appoggiatura (CP-06) are forbidden outright:
             stricter. The fourth above the bass is forbidden outright: the checker faults
             an unsupported one (six_four_supported) and forgives a supported one, so
             forbidding all of them is never weaker. Raw 10/11 above the bass are chordal
             sevenths, consonant to the checker and judged by the seventh block, exactly as
             is_dissonant treats them.
  parallel   CP-09, Checker.judge_motion: both voices move, same direction, equal interval
             class in {0, 7}. The checker faults the outer pair; we forbid it on every
             pair: stricter, so three-voice textures come out with clean inner parts too.
  hidden     CP-10, judge_motion: into a perfect by similar motion, entering interval
             different, upper voice leaps beyond 2 semitones. Same broadening to all pairs.
             Soft in free, hard in strict, so it must be enforced to be clean in strict.
  leading    CP-11, Checker.check_leading_tone: a note with the leading-tone pitch class
             whose sounding bass carries the dominant pitch class must repeat or rise one
             semitone (the checker lets step 0 and step +1 to the tonic pass; a diatonic
             semitone up from the leading tone is always the tonic).
  seventh    CP-12, Checker.check_sevenths: a raw 10 or 11 above the sounding bass leaves
             down one or two semitones at its next beat, or never arrives.
  crossing   CP-13, check_spacing_and_crossing: unreachable by construction, since adjacent
             voices keep a positive margin at every beat, which also pins the mean rank.
  overlap    CP-14, check_overlap: the lower voice never rises above where the upper voice
             just was and the upper never falls below where the lower just was, on adjacent
             rank pairs, the checker's exact scope.
  spacing    CP-15, check_spacing_and_crossing: adjacent gap at most 12 except the pair
             above the bass which gets 19, the checker's own limits, enforced only from
             three voices up because the checker has no spacing rule for two.
  leaps      CP-16, Checker.check_leaps: a leap larger than a fourth may not be followed by
             a same-direction leap larger than a step; the checker's thresholds verbatim.
  range      CP-17, Checker.check_range: the variable bounds ARE NES_RANGES intersected
             with the scale tones, so no solution can leave the chip register.

  cadence    and motif and imitation are aesthetic extra constraints: they only remove
             solutions, so they can never make the proof unsound.

WHAT SOUNDNESS MEANS HERE AND HOW IT IS TESTED

Any grid this solver can produce passes rules.py with zero hard AND zero soft findings in
both profiles, because every block above is at least as strict as the matching checker
method (argued line by line) and the aesthetic blocks only subtract. fv4_proof.py turns the
argument into a measurement: it samples solver models over seeds, keys, voicings, bars and
forms, runs the real Checker over every one of them, and fails on the first finding. It then
mutates: every rule block skipped in turn must let a violation appear, which catches a block
written so weakly it never binds. A solved texture is also round-tripped through the project
MIDI writer and re-checked from the file, so what plays is what was proved.

Each constraint block can be switched off by name for the mutation test via skip=(...).

Usage:
    python tools/counterpoint/smt_counterpoint.py --form species --bars 8 --seed 3 --out FILE.mid
    python tools/counterpoint/smt_counterpoint.py --form invention --bars 8 --seed 7 --json OUT.json
    python tools/counterpoint/smt_counterpoint.py --form canon --bars 8 --seed 5
    python tools/counterpoint/smt_counterpoint.py --form countermelody \
        --melody "D5 F5 A5 D5 C5 A5 G5 A5" --bars 2
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import z3

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import rules  # noqa: E402  the M1a engine, single source of truth for every rule below

TICKS_PER_BEAT = 480
BEATS = 4                              # 4/4: rules.accent_positions(4) -> strong {0}, medium {2}
DISSONANT_IC = (1, 2, 6, 10, 11)       # rules.DISSONANT without 5, which is judged by name

RULE_BLOCKS = ("vertical", "parallel", "hidden", "leading", "seventh", "overlap",
               "spacing", "leaps", "cadence", "motif")

# The invention head from the plan (M1b): scale degrees 0 1 2 3, restated two degrees up,
# then free to the cadence. One key, quarter-note grid: the exposition idea without the
# modulation machinery, which the search can extend later.
HEAD_MOTIF = (0, 1, 2, 3)


class CounterpointSpec(object):
    """Key, voices and bar count for one SMT problem."""

    def __init__(self, tonic=0, mode="major", voices=("pulse 1", "triangle"), bars=4):
        self.tonic = int(tonic) % 12
        self.mode = mode
        self.voices = list(voices)              # rank order, top first
        self.bars = int(bars)
        self.T = self.bars * BEATS
        steps = set(rules.MAJOR_SCALE if mode == "major" else rules.MINOR_SCALE)
        if mode == "minor":
            steps.add(11)                       # raised leading tone, harmonic flavour
        self.steps = sorted(steps)
        # absolute pitch classes of the key, tonic transposed in: A minor keeps A, G major
        # keeps F#, which rules.scale_of would too. The raised leading tone (minor only) is
        # the tonic-1 pitch class, which is what steps.add(11) becomes after transposition.
        self.pcs = sorted({(self.tonic + s) % 12 for s in steps})

    def scale_ok(self, p):
        """Constraint (or test for an int): p is a tone of the key, any octave."""
        if isinstance(p, int):
            return p % 12 in self.pcs
        return z3.Or(*[p % 12 == pc for pc in self.pcs])

    def degree_pitch(self, degree):
        """The pitch of a scale degree, as a concrete MIDI number in the top register.

        Anchored at the tonic pitch class in MIDI octave 4 (C4 = 60), then stepped by the
        mode scale and wrapped by octave. The invention head motif pins the top voice with
        these, so they must be real in-range pitches, not bare pitch classes."""
        octave, index = divmod(degree, len(self.steps))
        tonic_pitch = 12 * 5 + self.tonic          # MIDI octave 4: C4 = 60
        return tonic_pitch + 12 * octave + self.steps[index]

    def window(self, voice):
        """The scale tones inside the voice's NES range, (lowest, highest)."""
        low, high = rules.NES_RANGES.get(voice, rules.DEFAULT_RANGE)
        inside = [n for n in range(low, high + 1) if n % 12 in self.pcs]
        if not inside:
            raise ValueError("no tone of %s fits inside %s's NES range"
                             % (rules.key_name((self.tonic, self.mode)), voice))
        return inside[0], inside[-1]

    def pitches_in_window(self, voice, pc):
        low, high = self.window(voice)
        return [n for n in range(low, high + 1) if n % 12 == pc]

    def accent(self, t):
        pos = t % BEATS
        if pos == 0:
            return "strong"
        if pos == 2:
            return "medium"
        return "weak"


def _pair_dissonant(pu, pl, bass_pair):
    """Mirror of Checker.is_dissonant for one sounding pair, given pu > pl at this instant.

    bass_pair says whether pl is the sounding bass, which is where both chord assumptions
    live: raw 10/11 above the bass is a chordal seventh (consonant; judged by CP-12), and a
    simple fourth above the bass is the clash the checker faults unless a 6/4 supports it,
    which we forbid outright. Everything else follows the interval class, with 5 consonant
    off the bass exactly as is_dissonant returns False for it there.
    """
    raw = pu - pl
    ic = raw % 12
    plain = z3.Or(*[ic == pc for pc in DISSONANT_IC])
    if bass_pair:
        chordal = z3.Or(raw == 10, raw == 11)
        return z3.Or(z3.And(plain, z3.Not(chordal)), raw == 5)
    return plain


def build_texture(spec, form="species", seed=None, melody=None, canon_interval=7,
                  canon_delay=2, timeout_ms=180000, skip=()):
    """Solve one texture. Returns a result dict with the pitch grid, or None when not SAT.

    species        all voices free, every rule, dominant-to-tonic bass cadence.
    invention      species plus the top voice stating HEAD_MOTIF in beats 0 to 3 and its
                   restatement two degrees up in beats 4 to 7.
    canon          the top voice strictly imitates the bass from beat canon_delay on, at
                   canon_interval semitones; the beats before the entry are free.
    countermelody  melody (pitch per beat) fixes the top voice; the solver writes the rest.

    skip: names from RULE_BLOCKS; those constraint blocks are not added (mutation testing).
    """
    skipped = set(skip or ())
    # Plain Solver, not Optimize: z3 5.3.2's Optimize/add_soft hangs even on a trivial grid,
    # so the seed bias and the contrary-motion preference (musicality only, never correctness)
    # are applied as greedy pins after the hard solve below instead of soft constraints. A pin
    # is an equality added to the hard set, so it only subtracts solutions and cannot touch
    # the soundness argument.
    solver = z3.Solver()
    T = spec.T
    pitches = {}
    for name in spec.voices:
        lo, hi = spec.window(name)
        var = [z3.Int("%s_%d" % (name.replace(" ", "_"), t)) for t in range(T)]
        for t in range(T):
            solver.add(var[t] >= lo, var[t] <= hi)          # CP-17, by construction
            solver.add(spec.scale_ok(var[t]))
        pitches[name] = var

    top, bass = spec.voices[0], spec.voices[-1]
    melody_voice = None
    # positions already fixed to specific pitches by a hard constraint (melody, motif, canon,
    # cadence); the seed batch below must not re-pin these or it would conflict and fall back
    # to z3's non-deterministic base model.
    pinned = set()
    if melody is not None:
        melody_voice = top
        for t in range(T):
            solver.add(pitches[melody_voice][t] == int(melody[t]))
            pinned.add((melody_voice, t))

    # CP-13 by construction: a positive adjacent margin pins the rank at every beat
    for i in range(len(spec.voices) - 1):
        up, dn = spec.voices[i], spec.voices[i + 1]
        for t in range(T):
            solver.add(pitches[up][t] >= pitches[dn][t] + 1)

    # CP-14 overlap, adjacent rank pairs, from beat 1 (the checker needs a previous note)
    if "overlap" not in skipped:
        for i in range(len(spec.voices) - 1):
            up, dn = spec.voices[i], spec.voices[i + 1]
            for t in range(1, T):
                solver.add(pitches[dn][t] <= pitches[up][t - 1])
                solver.add(pitches[up][t] >= pitches[dn][t - 1])

    # CP-15 spacing, adjacent rank pairs, three voices up only (two voices have no limit)
    if "spacing" not in skipped and len(spec.voices) >= 3:
        for i in range(len(spec.voices) - 1):
            up, dn = spec.voices[i], spec.voices[i + 1]
            limit = 12 if i + 2 < len(spec.voices) else 19
            for t in range(T):
                solver.add(pitches[up][t] - pitches[dn][t] <= limit)

    if form == "canon":
        for t in range(canon_delay, T):
            solver.add(pitches[top][t] == pitches[bass][t - canon_delay] + canon_interval)
            pinned.add((top, t))
    if form == "invention" and melody is None and "motif" not in skipped:
        for i, deg in enumerate(HEAD_MOTIF):
            solver.add(pitches[top][i] == spec.degree_pitch(deg))
            pinned.add((top, i))
        for i, deg in enumerate(HEAD_MOTIF):
            solver.add(pitches[top][4 + i] == spec.degree_pitch(deg + 2))
            pinned.add((top, 4 + i))

    # cadence: bass dominant two beats out, tonic on the last beat
    if "cadence" not in skipped and (melody is None or bass != melody_voice):
        ton = spec.pitches_in_window(bass, spec.tonic)
        dom = spec.pitches_in_window(bass, (spec.tonic + 7) % 12)
        if ton and dom:
            solver.add(z3.Or(*[pitches[bass][T - 1] == p for p in ton]))
            solver.add(z3.Or(*[pitches[bass][T - 2] == p for p in dom]))
            pinned.add((bass, T - 1))
            pinned.add((bass, T - 2))

    def device(name, t):
        """The strict passing or neighbour reading of the note attacked at beat t, the two
        device_for branches that pass silently (their contours read the same three notes).
        Sign booleans instead of products: the same test, linear, and z3 solves it fast."""
        step_in = pitches[name][t] - pitches[name][t - 1]
        step_out = pitches[name][t + 1] - pitches[name][t]
        sin_p, sin_m = z3.Bool("sinp_%s_%d" % (name.replace(" ", "_"), t)), \
            z3.Bool("sinm_%s_%d" % (name.replace(" ", "_"), t))
        sout_p, sout_m = z3.Bool("soutp_%s_%d" % (name.replace(" ", "_"), t)), \
            z3.Bool("soutm_%s_%d" % (name.replace(" ", "_"), t))
        solver.add(z3.And(sin_p == (step_in > 0), sin_m == (step_in < 0),
                          sout_p == (step_out > 0), sout_m == (step_out < 0)))
        sin = z3.Or(*[step_in == s for s in (-2, -1, 1, 2)])
        sout = z3.Or(*[step_out == s for s in (-2, -1, 1, 2)])
        passing = z3.And(sin, sout, z3.Or(z3.And(sin_p, sout_p), z3.And(sin_m, sout_m)))
        neighbour = z3.And(sin, sout, step_in + step_out == 0)
        return z3.Or(passing, neighbour)

    # vertical: CP-01/CP-02 (and, by ruling out appoggiatura and escape, CP-06 and CP-18)
    if "vertical" not in skipped:
        for t in range(T):
            strong = spec.accent(t) in ("strong", "medium")
            edge = (t == 0 or t == T - 1)      # no contour at the ends: devices impossible,
            for i in range(len(spec.voices)):  #   and the checker faults these outright
                for j in range(i + 1, len(spec.voices)):
                    up, dn = spec.voices[i], spec.voices[j]
                    dissonant = _pair_dissonant(pitches[up][t], pitches[dn][t], dn == bass)
                    if strong or edge:
                        solver.add(z3.Not(dissonant))
                    else:
                        solver.add(z3.Implies(dissonant,
                                              z3.Or(device(up, t), device(dn, t))))

    # CP-09 and CP-10 between consecutive instants, every pair
    if "parallel" not in skipped or "hidden" not in skipped:
        for t in range(T - 1):
            for i in range(len(spec.voices)):
                for j in range(i + 1, len(spec.voices)):
                    up, dn = spec.voices[i], spec.voices[j]
                    mu = pitches[up][t + 1] - pitches[up][t]
                    md = pitches[dn][t + 1] - pitches[dn][t]
                    ic1 = (pitches[up][t] - pitches[dn][t]) % 12
                    ic2 = (pitches[up][t + 1] - pitches[dn][t + 1]) % 12
                    both_move = z3.And(mu != 0, md != 0)
                    same_dir = z3.Or(z3.And(mu > 0, md > 0), z3.And(mu < 0, md < 0))
                    perfect2 = z3.Or(ic2 == 0, ic2 == 7)
                    if "parallel" not in skipped:
                        solver.add(z3.Not(z3.And(both_move, same_dir, perfect2, ic1 == ic2)))
                    if "hidden" not in skipped:
                        solver.add(z3.Not(z3.And(both_move, same_dir, perfect2, ic1 != ic2,
                                                 z3.Or(mu > 2, mu < -2))))

    # CP-11 leading tone over the dominant bass (a fixed melody line is not re-solved; its
    # own notes stay as given and the checker, not the solver, judges them)
    if "leading" not in skipped:
        lt = (spec.tonic - 1) % 12
        dom_pc = (spec.tonic + 7) % 12
        for name in spec.voices:
            if name in (bass, melody_voice):
                continue
            for t in range(T - 1):
                cur, nxt = pitches[name][t], pitches[name][t + 1]
                fire = z3.And(cur % 12 == lt, pitches[bass][t] % 12 == dom_pc)
                solver.add(z3.Implies(fire, z3.Or(nxt == cur, nxt == cur + 1)))

    # CP-12 chordal seventh above the bass resolves down by step
    if "seventh" not in skipped:
        for name in spec.voices:
            if name in (bass, melody_voice):
                continue
            for t in range(T - 1):
                cur, nxt = pitches[name][t], pitches[name][t + 1]
                gap = cur - pitches[bass][t]
                solver.add(z3.Implies(z3.Or(gap == 10, gap == 11),
                                      z3.Or(nxt == cur - 1, nxt == cur - 2)))

    # CP-16 two same-direction leaps, the checker's thresholds verbatim
    if "leaps" not in skipped:
        for name in spec.voices:
            if name == melody_voice:
                continue
            for t in range(T - 2):
                d1 = pitches[name][t + 1] - pitches[name][t]
                d2 = pitches[name][t + 2] - pitches[name][t + 1]
                big = z3.Or(d1 > 5, d1 < -5)
                again = z3.Or(d2 > 2, d2 < -2)
                same = z3.Or(z3.And(d1 > 0, d2 > 0), z3.And(d1 < 0, d2 < 0))
                solver.add(z3.Implies(z3.And(big, again), z3.Not(same)))

    # Musicality, not correctness: a seed bias, applied as greedy pins after the hard solve.
    # Each free note is offered a seed-chosen scale tone and the pin is kept only when the
    # problem stays SAT, so a pin never makes a legal texture unsolvable. The seed therefore
    # picks which of the many clean textures comes out; it is a bias, not a proof ingredient.
    # Deterministic output is not a FV-4 requirement (that is M1b's seeded search), so a note
    # whose seed tone conflicts is left free rather than swept over every legal tone, which
    # keeps the solve fast. Plain Solver with incremental checks: z3 5.3.2's Optimize/add_soft
    # hangs, this does not.
    solver.set(timeout=timeout_ms)
    if solver.check() != z3.sat:
        return None

    def pin(constraint):
        solver.push()
        solver.add(constraint)
        ok = solver.check() == z3.sat
        solver.pop()
        if ok:
            solver.add(constraint)
        return ok

    if seed is not None:
        h = hashlib.sha256(("fv4:%s:%s:%d:%d" % (form, rules.key_name((spec.tonic, spec.mode)),
                                                 spec.bars, seed)).encode()).digest()
        for vi, name in enumerate(spec.voices):
            lo, hi = spec.window(name)
            legal = [n for n in range(lo, hi + 1) if n % 12 in spec.pcs]
            for t in range(T):
                if (name, t) in pinned:
                    continue
                offset = h[(vi * 31 + t) % len(h)] % len(legal)
                pin(pitches[name][t] == legal[offset])

    # adding a pin invalidates the previous model, so a final check re-materialises one
    if seed is not None:
        assert solver.check() == z3.sat
    model = solver.model()
    grid = {name: [model.evaluate(p).as_long() for p in pitches[name]] for name in spec.voices}
    return {"form": form, "key": rules.key_name((spec.tonic, spec.mode)),
            "tonic": spec.tonic, "mode": spec.mode, "voices": spec.voices,
            "bars": spec.bars, "beats": BEATS, "grid": grid, "seed": seed,
            "skip": sorted(skipped) or None,
            "canon_interval": canon_interval if form == "canon" else None,
            "canon_delay": canon_delay if form == "canon" else None}


def grid_to_score(result):
    """Rebuild the texture as a rules.py Score: one note per beat, so the Checker reads
    exactly what the solver solved (Part.at needs end > tick, resolutions a following note)."""
    parts = {}
    for name, grid in result["grid"].items():
        parts[name] = [(t * TICKS_PER_BEAT, (t + 1) * TICKS_PER_BEAT, p, 96)
                       for t, p in enumerate(grid)]
    return rules.Score.from_notes(parts, division=TICKS_PER_BEAT,
                                  time_sig=(result.get("beats", BEATS), 4),
                                  tempo_us=500000,
                                  key=(result["tonic"], result["mode"]),
                                  path="smt:%s" % result["form"])


def check_clean(result, profiles=("free", "strict")):
    """Run the REAL checker over the solved grid; a finding at hard or soft level refutes."""
    score = grid_to_score(result)
    out = {}
    for profile in profiles:
        report = rules.analyse(score, profile=profile)
        out[profile] = {"hard": report["summary"]["by_severity"]["hard"],
                        "soft": report["summary"]["by_severity"]["soft"],
                        "style": report["summary"]["by_severity"]["style"],
                        "findings": [f for f in report["findings"]
                                     if f["severity"] in ("hard", "soft")]}
    verdict = all(row["hard"] == 0 and row["soft"] == 0 for row in out.values())
    return {"verdict": "CLEAN" if verdict else "REFUTED", "profiles": out}


def write_midi(result, path):
    """Write the texture as a format-1 SMF with the project's own writer, then re-check the
    file round-tripped, so what plays is what was proved."""
    import humanize
    tracks = [{"name": "meta", "notes": [], "cc": {}}]
    for name, grid in result["grid"].items():
        tracks.append({"name": name,
                       "notes": [(t * TICKS_PER_BEAT, (t + 1) * TICKS_PER_BEAT - 40, p, 96)
                                 for t, p in enumerate(grid)],
                       "cc": {}})
    song = {"tracks": tracks, "division": TICKS_PER_BEAT, "time_sig": (BEATS, 4),
            "tempo_us": 500000, "name": "fv4_%s" % result["form"]}
    humanize.write_smf(song, path)
    reloaded = rules.Score.from_smf(path, key=(result["tonic"], result["mode"]))
    report = rules.analyse(reloaded, profile="strict")
    return {"path": path,
            "roundtrip_hard": report["summary"]["by_severity"]["hard"],
            "roundtrip_soft": report["summary"]["by_severity"]["soft"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description="FV-4 Z3 counterpoint solver (card t_11f7f43f)")
    parser.add_argument("--form", default="species",
                        choices=("species", "invention", "canon", "countermelody"))
    parser.add_argument("--bars", type=int, default=4)
    parser.add_argument("--key", default="C", help="tonic letter, C to B")
    parser.add_argument("--mode", default="major", choices=("major", "minor"))
    parser.add_argument("--voices", default="2", choices=("2", "3"),
                        help="2: pulse 1 over triangle; 3: add pulse 2 between them")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--melody", default=None,
                        help="pitches, one per beat, for --form countermelody")
    parser.add_argument("--canon-interval", type=int, default=7)
    parser.add_argument("--canon-delay", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=180000)
    parser.add_argument("--out", default=None, help="write a .mid here")
    parser.add_argument("--json", dest="json_out", default=None)
    args = parser.parse_args(argv)

    voices = (["pulse 1", "triangle"] if args.voices == "2"
              else ["pulse 1", "pulse 2", "triangle"])
    spec = CounterpointSpec(tonic=rules.parse_pitch(args.key + "4") % 12, mode=args.mode,
                            voices=voices, bars=args.bars)
    melody = None
    if args.form == "countermelody":
        if not args.melody:
            parser.error("--melody is required for --form countermelody")
        melody = [rules.parse_pitch(x) for x in args.melody.split()]
        if len(melody) != spec.T:
            parser.error("--melody must give exactly %d notes (%d bars x %d beats)"
                         % (spec.T, args.bars, BEATS))
        lo, hi = spec.window(voices[0])
        bad = [rules.pitch_name(p) for p in melody if not lo <= p <= hi]
        if bad:
            parser.error("melody notes outside %s's NES window: %s" % (voices[0], " ".join(bad)))
    result = build_texture(spec, form=args.form, seed=args.seed, melody=melody,
                           canon_interval=args.canon_interval, canon_delay=args.canon_delay,
                           timeout_ms=args.timeout)
    if result is None:
        print("UNSAT: no texture exists for this problem inside the timeout")
        return 3
    proof = check_clean(result)
    if args.out:
        result["midi"] = write_midi(result, args.out)
    payload = dict(result)
    payload["proof"] = proof
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
    print("form %s, %s, %d bars, %s: %s" % (result["form"], result["key"], result["bars"],
                                            "+".join(result["voices"]), proof["verdict"]))
    for name, grid in result["grid"].items():
        print("  %-9s %s" % (name, " ".join(rules.pitch_name(p) for p in grid)))
    for profile, row in proof["profiles"].items():
        print("  checker %s: hard %d, soft %d, style %d"
              % (profile, row["hard"], row["soft"], row["style"]))
    if args.out:
        rt = result["midi"]
        print("  wrote %s (re-read from file: hard %d, soft %d)"
              % (rt["path"], rt["roundtrip_hard"], rt["roundtrip_soft"]))
    return 0 if proof["verdict"] == "CLEAN" else 2


if __name__ == "__main__":
    sys.exit(main())


# SUPERSEDED 2026-11-01 (card t_11f7f43f). This encoder imports the M1a engine and solves a
# homorhythmic grid. The FV-4 model that landed is `counterpoint_z3.py` (card t_89d80b48): pure,
# one named Z3 assertion per rule, unsat cores that name the rule that blocked the line, a 39
# test suite of its own and an independent 49 test adversarial suite. This file is committed
# because `formal/FV-4-rules.md` cites it BY LINE for its FV-4 status columns, which is also why
# the note sits at the end and not in the docstring: any line added above would break those
# citations. Nothing imports it. Its own slice, `tests/test_counterpoint_smt.py`, passed 14 of
# 14 in 68.55 s on CitadelArana 2026-11-01.

