"""Tests for tools/check_runtime_palette.py: the shipped table passes, and every way of cheating it fails.

Why a test and not a review note: the card (t_54db4d0f) turns 54 design colours into 2C02 entries, and the only
evidence that the result is still a palette and not a pile of near blacks is a check. Each row below breaks exactly
one property in a private copy of data\\ and asserts the tool names it, so the tool cannot rot into a script that
prints PASS while ink and paper are the same entry.
"""

from __future__ import annotations

import json
import os

import pytest

import check_runtime_palette as tool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGN_COLOURS = 54


@pytest.fixture()
def tree(data_root):
    """A private root with data\\ copied and the one GML file the check reads put beside it."""
    script = data_root / "game" / "scripts" / "pp_data" / "pp_data.gml"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text('var _table = pp_data_json("palette_ppu.json");\n', encoding="utf-8")
    return data_root


def read(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write(path, payload):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def table_of(root):
    return read(os.path.join(str(root), "data", "palette_ppu.json"))


def run(root):
    return tool.check(str(root))


def test_the_shipped_tree_resolves_every_design_colour():
    problems, rows, counts = run(ROOT)
    assert problems == []
    assert counts["colours"] == DESIGN_COLOURS
    assert counts["mapped"] == DESIGN_COLOURS
    assert counts["legal"] == DESIGN_COLOURS
    assert counts["runtime_reads"] is True
    assert counts["distinct_entries"] > 4, "the table collapsed everything onto a handful of entries"
    assert all(row["legal"] for row in rows)


def test_the_table_keys_are_exactly_the_design_indices():
    mapping = table_of(ROOT)["mapping"]
    assert sorted(int(key) for key in mapping) == list(range(DESIGN_COLOURS))


def test_the_runtime_names_the_table():
    body = open(os.path.join(ROOT, tool.RUNTIME), "r", encoding="utf-8", errors="ignore").read()
    assert "palette_ppu.json" in body
    assert "nes_palette.json" in body, "the runtime resolves through the 2C02 master, not around it"


def test_a_missing_mapping_fails_and_counts_the_gap(tree):
    payload = table_of(tree)
    del payload["mapping"]["17"]
    write(os.path.join(str(tree), "data", "palette_ppu.json"), payload)

    problems, rows, counts = run(tree)
    assert counts["off"] == 1
    assert rows[17]["legal"] is False
    assert "no entry in data/palette_ppu.json" in rows[17]["why"]
    assert tool.main(["--root", str(tree), "--quiet"]) == 1


def test_an_unusable_entry_is_refused(tree):
    payload = table_of(tree)
    payload["mapping"]["0"] = 13  # $0D, the forbidden entry
    write(os.path.join(str(tree), "data", "palette_ppu.json"), payload)

    problems, rows, counts = run(tree)
    assert counts["off"] == 1
    assert rows[0]["legal"] is False
    assert "unusable" in rows[0]["why"]


def test_an_entry_outside_the_master_is_refused(tree):
    payload = table_of(tree)
    payload["mapping"]["0"] = 99
    write(os.path.join(str(tree), "data", "palette_ppu.json"), payload)

    problems, rows, counts = run(tree)
    assert counts["off"] == 1
    assert "not in data/nes_palette.json" in rows[0]["why"]


def test_a_family_that_runs_backwards_is_refused(tree):
    payload = table_of(tree)
    payload["mapping"]["25"], payload["mapping"]["27"] = payload["mapping"]["27"], payload["mapping"]["25"]
    write(os.path.join(str(tree), "data", "palette_ppu.json"), payload)

    problems, _rows, _counts = run(tree)
    assert any("ramp runs backwards" in problem for problem in problems), problems


def test_the_window_roles_may_not_collapse(tree):
    payload = table_of(tree)
    payload["mapping"]["1"] = payload["mapping"]["0"]  # paper becomes ink
    write(os.path.join(str(tree), "data", "palette_ppu.json"), payload)

    problems, _rows, _counts = run(tree)
    assert any("both resolve to the same entry" in problem for problem in problems), problems


def test_a_shadow_that_draws_nothing_is_refused(tree):
    payload = table_of(tree)
    payload["mapping"]["2"] = payload["mapping"]["1"]  # window_shadow becomes paper
    write(os.path.join(str(tree), "data", "palette_ppu.json"), payload)

    problems, _rows, _counts = run(tree)
    assert any("window_shadow" in problem and "draws nothing" in problem for problem in problems), problems


def test_a_room_set_may_not_collapse_a_family(tree):
    payload = table_of(tree)
    payload["mapping"]["10"] = payload["mapping"]["8"]  # sea_4 becomes sea_2, and deck_day spends both
    write(os.path.join(str(tree), "data", "palette_ppu.json"), payload)

    problems, _rows, _counts = run(tree)
    assert any("room palette set 'deck_day'" in problem for problem in problems), problems


def test_a_runtime_that_never_names_the_table_fails(tree):
    script = tree / "game" / "scripts" / "pp_data" / "pp_data.gml"
    script.write_text('var _table = pp_data_json("palette.json");\n', encoding="utf-8")

    problems, _rows, counts = run(tree)
    assert counts["runtime_reads"] is False
    assert any("never names palette_ppu.json" in problem for problem in problems), problems


def test_a_missing_table_fails(tree):
    os.remove(os.path.join(str(tree), "data", "palette_ppu.json"))

    problems, _rows, counts = run(tree)
    assert any("is missing" in problem for problem in problems), problems
    assert counts["off"] == DESIGN_COLOURS
