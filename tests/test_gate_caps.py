"""The gate that decides whether this project's work can land must be sized from measurements.

Card GATE-CAP-PP (t_e7d53c94), 2026-10-27. Twice now a primordial-paradox commit has been refused
by a time cap rather than by a failure: the suite grew past the number and the gate measured
nothing, which is the one outcome a gate must never produce, because "nothing was measured" then
blocks every honest change in the project. The rule that replaced the judgement call is arithmetic
and it is written in projects/arananet/manager/guard/suite_config.json: a cap is at least 1.5x the
worst honest measurement on THAT path, and no higher.

A rule in a prose note is a rule nobody runs, so these rows run it: every cap the primordial-paradox
entry declares is checked against the measurement recorded beside it, and the staged path is checked
to run the mapped selection rather than the whole suite. The numbers themselves live in the config,
next to the cap they justify, because a test that invented its own copy of them would be a second
source of truth and the first one to go stale.

The config is the manager tree's, so a checkout of this project alone has nothing to read, and every
row FAILS there naming the path (card t_5f0a896e). It used to skip, which is the shape this project
already paid for once: a row that reports healthy while it read nothing is indistinguishable from one
that checked a cap. tools/check_test_inputs.py rule 1 forbids a skip guarded by a path existence test
for exactly that reason, so the guard's verdict is a red with the missing path in it.
"""

from __future__ import annotations

import json
import math
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(ROOT))
CONFIG = os.path.join(REPO, "projects", "arananet", "manager", "guard", "suite_config.json")

# The cap rule, quoted from _cap_note_2026_10_26: "cap = 1.5x the worst honest measurement on THAT
# path and no higher". Kept here as the number the rows multiply by, so a future raise of the factor
# is a visible edit and not a quiet one.
CAP_MULTIPLIER = 1.5


def project_entry():
    """(the config, the primordial-paradox entry); fails naming the path when the manager tree is absent.

    The rule this file runs is written in the manager tree, so a checkout that lacks that tree cannot
    run it. Following it is a red that names the path, not a skip: card t_5f0a896e, and rule 1 in
    tools/check_test_inputs.py, both exist because a skip here reports healthy while reading nothing.
    """
    if not os.path.exists(CONFIG):
        pytest.fail(
            "the gate's suite_config.json is not in this tree (%s). The cap numbers this file checks "
            "live in the manager tree, so these rows cannot reach a verdict without it; run the suite "
            "from a checkout of <workspace>/Shared." % CONFIG)
    with open(CONFIG, encoding="utf-8") as handle:
        config = json.load(handle)
    for entry in config.get("projects", []):
        if entry.get("name") == "primordial-paradox":
            return config, entry
    pytest.fail("suite_config.json carries no primordial-paradox entry (%s), so no cap is declared "
                "for this project and nothing can be checked" % CONFIG)


def measurements(entry):
    """Every recorded measurement, as {path_name: seconds}, from the dated keys in the entry.

    A measurement is a dated key whose value is an object of {name: seconds}, which is how the cap
    arithmetic has been written down since 2026-10-26: `measured_2026_10_27` holds one number per
    path a cap is declared for. Numbers that are not seconds (a command, a sentence, a count of
    tests) are ignored rather than coerced, so a note can sit beside a number without breaking it.
    """
    found = {}
    for key, value in entry.items():
        if not key.startswith("measured_"):
            continue
        if not isinstance(value, dict):
            continue
        for name, seconds in value.items():
            if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
                continue
            if seconds <= 0:
                continue
            found[name] = float(seconds)
    return found


def test_the_staged_path_runs_the_mapped_selection_and_not_the_whole_suite():
    """A commit must not wait on 1900 tests. Card VC-3: the mapped arguments ARE the selection.

    The trailing `tests` argument was the whole suite; leaving it in place while adding a budget
    would have produced a 60 s cap that the full suite can never meet, i.e. every commit deferred
    and nothing measured, which is the failure this card exists to end.
    """
    _config, entry = project_entry()
    fast_cmd = entry.get("fast_cmd")
    assert fast_cmd, "the primordial-paradox entry declares no fast_cmd, so nothing can run"
    assert not (fast_cmd and fast_cmd[-1] == "tests"), (
        "fast_cmd still ends with 'tests', so the staged run is the whole suite and the commit "
        "budget can only ever be exceeded: %r" % (fast_cmd,))


def test_the_commit_budget_is_a_minute_or_less():
    """Nayil's target is a commit gate under a minute (card VC-3), and the nightly is the catcher."""
    _config, entry = project_entry()
    budget = entry.get("commit_budget_s")
    assert budget is not None, (
        "no commit_budget_s, so a staged run is capped by the full-suite number and blocks the "
        "commit instead of deferring it")
    assert 0 < float(budget) <= 60, "commit_budget_s is %s, over the 60 s target" % (budget,)


def test_a_deferred_commit_is_deferred_rather_than_failed():
    """on_timeout fail plus a 60 s budget is the same block again; the staged path must defer.

    The full-suite path (push and nightly) keeps on_timeout fail, and that is deliberate: a full run
    that never finished measured nothing. The staged path is a selection under a budget, so
    exceeding the budget is a fact about the budget, not about the commit.
    """
    config, entry = project_entry()
    assert entry.get("commit_budget_s") is not None
    note = entry.get("_on_timeout_note", "")
    assert "defer" in note.lower() or config.get("on_timeout") == "defer", (
        "the staged path declares a commit budget but nothing says what a budget hit means; the "
        "_on_timeout_note must name the deferral")


def test_every_cap_in_use_is_at_least_one_and_a_half_times_its_measurement():
    """The cap rule, run instead of quoted: cap >= 1.5 * the recorded worst on the same path.

    A cap that is under this line refuses an honest change on a busy day, which is what happened on
    2026-10-26 (two commits cut at 600 s) and again on 2026-10-27 (a gate killed by lane_commit's
    own budget before it could print a verdict). A cap far above it turns a hang into a hang that
    eats an afternoon, which is why the rule says "and no higher" as well.
    """
    _config, entry = project_entry()
    recorded = measurements(entry)
    caps = {
        "fast_time_cap_s": "live_tree",
        "staged_time_cap_s": "staged_tree",
        "full_timeout_s": "full_suite",
    }
    checked = 0
    for cap_key, measurement_key in caps.items():
        if entry.get(cap_key) is None:
            continue
        assert measurement_key in recorded, (
            "%s is %s with no %r measurement recorded beside it: a cap with no number behind it is "
            "a guess, and this card exists because a guess cut two honest commits"
            % (cap_key, entry[cap_key], measurement_key))
        cap = float(entry[cap_key])
        need = CAP_MULTIPLIER * recorded[measurement_key]
        assert cap >= math.floor(need), (
            "%s is %s s but %r measures %s s, so the rule wants at least %s s"
            % (cap_key, cap, measurement_key, recorded[measurement_key], math.floor(need)))
        checked += 1
    assert checked, "no cap was checked against a measurement, so this row proved nothing"


def test_the_recorded_measurement_names_the_command_that_produced_it():
    """A number without its command is not a measurement (the standard the gate log holds itself to)."""
    _config, entry = project_entry()
    dates = [key for key in entry if key.startswith("measured_") and isinstance(entry[key], dict)]
    assert dates, "the entry carries no dated measurement object, so no cap can be re-derived"
    for key in dates:
        block = entry[key]
        assert block, "%s is empty; an empty measurement justifies nothing" % key
        command = block.get("_command")
        assert isinstance(command, str) and "pytest" in command, (
            "%s records numbers but not the command that produced them, so nobody can re-measure "
            "the same thing: got %r" % (key, command))
