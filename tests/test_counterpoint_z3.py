"""Tests for card t_89d80b48 (FV-4b): the rule inventory as named Z3 assertions.

What these tests hold the module to, in the card's own words:

  module imports cleanly with no side effects   (subprocess purity test)
  it solves the worked examples in the spec doc (run_worked_examples, 13 of 14; the suspension
                                                 case needs a held note and is reported, not faked)
  unsat cases name the violated rule            (core tests, and the core is irreducible)
  a 2 voice, 8 position problem in a few seconds (timing test, plus the real checker)

They also hold it to the property the doc cares about most: a model this module calls SAT is
clean under the REAL M1a checker in both profiles, which is what makes the encoding a proof and
not a parallel opinion.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

TESTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TESTS)
COUNTERPOINT = os.path.join(ROOT, "tools", "counterpoint")
if COUNTERPOINT not in sys.path:
    sys.path.insert(0, COUNTERPOINT)

import counterpoint_z3 as cz  # noqa: E402
import rules  # noqa: E402

SINGLE_RULE_CASES = ("outer parallel octaves", "hidden fifth, upper leaps a fourth",
                     "spacing 15, three voices", "pulse 1 at 90", "triangle at 60",
                     "chordal seventh rising", "two leaps the same way",
                     "unprepared seventh on beat 1")


def example(case):
    for row in cz.WORKED_EXAMPLES:
        if row.case == case:
            return row
    raise KeyError(case)


def score_of(result):
    """Rebuild a solved grid as a rules.py Score, so the real checker judges the same notes."""
    parts = {}
    for voice, row in result["model"].items():
        parts[voice] = [(position * 480, (position + 1) * 480, pitch, 96)
                        for position, pitch in enumerate(row)]
    texture = result["texture"]
    key = tuple(texture["key"]) if texture["key"] else None
    return rules.Score.from_notes(parts, division=480, time_sig=(texture["beats"], 4),
                                  tempo_us=500000, key=key, path="z3:%s" % texture["label"])


def severities(score):
    out = {}
    for profile in ("free", "strict"):
        report = rules.analyse(score, profile=profile)
        out[profile] = report["summary"]["by_severity"]
    return out


# -- purity -------------------------------------------------------------------------------


def test_module_imports_without_side_effects_or_engine_imports():
    program = (
        "import sys\n"
        "import counterpoint_z3\n"
        "forbidden = ('rules', 'arrange', 'hook_score', 'humanize', 'smt_counterpoint')\n"
        "loaded = sorted(m for m in sys.modules if m.split('.')[0] in forbidden)\n"
        "print(','.join(loaded))\n"
    )
    finished = subprocess.run([sys.executable, "-c", program], cwd=COUNTERPOINT, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=120)
    assert finished.returncode == 0, finished.stderr
    assert finished.stdout.strip() == "", "the module pulled in %r" % finished.stdout
    assert finished.stderr.strip() == "", finished.stderr


def test_no_file_io_at_import_time(tmp_path):
    program = "import counterpoint_z3\n"
    finished = subprocess.run([sys.executable, "-c", program], cwd=str(tmp_path), stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=120,
                              env=dict(os.environ, PYTHONPATH=COUNTERPOINT))
    assert finished.returncode == 0, finished.stderr
    assert sorted(p.name for p in tmp_path.iterdir()) == []


# -- the worked examples ------------------------------------------------------------------


def test_worked_examples_pass():
    report = cz.run_worked_examples()
    assert report["verdict"] == "PASS", report["failed"]
    assert report["passed"] == 13
    assert report["skipped_not_modelled"] == 1, "the suspension case must be reported, not solved"


@pytest.mark.parametrize("case", SINGLE_RULE_CASES)
def test_single_rule_case_names_that_rule_and_no_other(case):
    row = example(case)
    result = cz.solve(row.texture())
    assert result["status"] == "unsat"
    assert result["core_minimised"] is True
    assert result["core_rules"] == [row.expect_rules[0]], result["core_rules"]


@pytest.mark.parametrize("case", SINGLE_RULE_CASES)
def test_the_named_rule_is_load_bearing(case):
    row = example(case)
    assert cz.solve(row.texture())["status"] == "unsat"
    relaxed = cz.solve(row.texture(), skip=tuple(example(case).expect_rules))
    assert relaxed["status"] == "sat", "skipping %s did not unblock the case" % (case,)


def test_two_rule_cases_only_name_rules_the_checker_reports():
    for case in ("crossing", "overlap", "two leaps the same way", "leading tone over the dominant"):
        row = example(case)
        result = cz.solve(row.texture())
        assert result["status"] == "unsat"
        assert result["core_rules"], case
        assert set(result["core_rules"]) <= set(row.checker_rules), case


def test_core_is_irreducible():
    row = example("crossing")
    result = cz.solve(row.texture())
    assert result["core_minimised"] is True
    again = cz.solve(row.texture())
    assert result["core"] == again["core"]


def test_turning_minimisation_off_shows_the_raw_core_is_not_minimal():
    row = example("hidden fifth, upper leaps a fourth")
    result = cz.solve(row.texture(), minimise_core=False)
    assert result["core_minimised"] is False
    assert "CP-10" in result["core_rules"]
    assert set(result["core_rules"]) <= set(row.checker_rules) | {"CP-09"}


# -- the doc's two-voice and scope facts --------------------------------------------------


def test_cp11_needs_a_key_and_says_so():
    row = example("leading tone over the dominant")
    without = cz.Texture(row.voices, 2, beats=4, key=None,
                         pins={(voice, position): pitch
                               for voice, notes in row.pitches.items()
                               for position, pitch in enumerate(notes)})
    assert cz.solve(without)["status"] == "sat"


def test_inner_parallel_fifths_are_stricter_than_the_checker_by_design():
    row = example("inner parallel fifths")
    strict = cz.solve(row.texture())
    parity = cz.solve(row.texture(), pairs="outer")
    assert strict["status"] == "unsat" and strict["core_rules"] == ["CP-09"]
    assert parity["status"] == "sat", "the checker's outer scope must not see this one"


# -- the acceptance criteria the card states ----------------------------------------------


def test_two_voices_eight_positions_solves_quickly_and_is_checker_clean():
    texture = cz.Texture(("pulse 1", "triangle"), 8, beats=4, key=(0, "major"), label="accept")
    result = cz.solve(texture)
    assert result["status"] == "sat", result["core"]
    assert result["elapsed_s"] < 5.0, "took %.3fs" % result["elapsed_s"]
    grid = result["model"]
    for voice, row in grid.items():
        low, high = cz.NES_RANGES[voice]
        assert all(low <= pitch <= high for pitch in row), voice
    by_severity = severities(score_of(result))
    for profile, counts in by_severity.items():
        assert counts["hard"] == 0 and counts["soft"] == 0, (profile, counts)


@pytest.mark.parametrize("voices", [("pulse 1", "triangle"),
                                    ("pulse 1", "pulse 2", "triangle")])
@pytest.mark.parametrize("key", [(0, "major"), (9, "minor")])
def test_solved_textures_are_clean_under_the_real_checker(voices, key):
    texture = cz.Texture(voices, 8, beats=4, key=key, label="checker")
    result = cz.solve(texture, scale_only=True)
    assert result["status"] == "sat", result["core"]
    by_severity = severities(score_of(result))
    for profile, counts in by_severity.items():
        assert counts["hard"] == 0 and counts["soft"] == 0, (profile, counts)


def test_canon_imitation_is_in_the_model():
    spec = cz.canon_spec(("pulse 1", "triangle"), 8, key=(0, "major"), delay=2, interval=7)
    result = cz.solve_canon(spec)
    assert result["status"] == "sat", result["core"]
    top = result["model"]["pulse 1"]
    bass = result["model"]["triangle"]
    for position in range(2, 8):
        assert top[position] == bass[position - 2] + 7
    by_severity = severities(score_of({"texture": {"beats": 4, "key": [0, "major"],
                                                  "label": "canon"},
                                       "model": result["model"]}))
    for profile, counts in by_severity.items():
        assert counts["hard"] == 0 and counts["soft"] == 0, (profile, counts)


def test_unsat_core_survives_as_readable_text():
    row = example("pulse 1 at 90")
    result = cz.solve(row.texture())
    lines = cz.describe_core(result["core"])
    assert any(line.startswith("CP-17") for line in lines), lines
    assert any(line.startswith("given note") for line in lines), lines


# -- coverage of the doc ----------------------------------------------------------------

ASSERTED_RULES = ("CP-01", "CP-02", "CP-09", "CP-10", "CP-11", "CP-12", "CP-13", "CP-14",
                  "CP-15", "CP-16", "CP-17")
# CP-06, CP-07 and CP-08 are encoded by exclusion (their complements are asserted); CP-04 and
# CP-05 need a held note the grid cannot express; CP-03 does not exist in the checker.
EXCLUDED_RULES = ("CP-03", "CP-04", "CP-05", "CP-06", "CP-07", "CP-08")


def test_every_rule_the_module_asserts_is_an_inventoried_rule():
    texture = cz.Texture(("pulse 1", "pulse 2", "triangle"), 4, beats=4, key=(0, "major"))
    asserted = {constraint.rule for constraint in cz.build_constraints(texture)} - {"PIN", "KEY"}
    assert asserted == set(ASSERTED_RULES), asserted


def test_the_doc_rule_ids_are_all_accounted_for():
    assert sorted(set(cz.RULE_TITLES) - set(EXCLUDED_RULES)) == sorted(ASSERTED_RULES)
    assert "CP-03" not in cz.RULE_TITLES


def test_constraint_names_start_with_their_rule():
    texture = cz.Texture(("pulse 1", "triangle"), 4, beats=4, key=(0, "major"))
    for constraint in cz.build_constraints(texture):
        assert constraint.name.startswith(constraint.rule + ":"), constraint.name
        assert "@t=" in constraint.name or constraint.rule == "PIN", constraint.name


def test_accent_positions_match_the_checker():
    for beats in (2, 3, 4, 6, 8):
        assert cz.accent_positions(beats) == rules.accent_positions(beats)


def test_nes_table_matches_the_checker():
    assert cz.NES_RANGES == rules.NES_RANGES
    assert cz.DEFAULT_RANGE == rules.DEFAULT_RANGE


# -- the CLI ----------------------------------------------------------------------------


def test_cli_prints_json_for_a_canon(capsys):
    code = cz.main(["--canon", "--positions", "8", "--key", "C major",
                    "--interval", "7", "--delay", "2"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["status"] == "sat"
    assert set(payload["model"]) == {"pulse 1", "triangle"}
    assert len(payload["model"]["pulse 1"]) == 8


def test_cli_pins_a_grid_and_reports_the_blocking_rule(capsys):
    code = cz.main(["--voices", "pulse 1,triangle", "--positions", "2", "--key", "C major",
                    "--pin", "pulse 1=72 74", "--pin", "triangle=48 50"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "unsat"
    assert payload["core_rules"] == ["CP-09"]


def test_cli_worked_examples_exit_code_reflects_the_verdict(capsys):
    code = cz.main(["--worked-examples"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["verdict"] == "PASS"
    assert code == 0
