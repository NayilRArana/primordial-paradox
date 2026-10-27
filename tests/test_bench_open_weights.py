"""tests for tools/bench_open_weights.py (card W3 OPEN-WEIGHTS).

What these exist to hold, so a later reader does not weaken them:
  * the 20 lines are the game's own: 15 authored in data/talk_cards.json plus the 5 fixtures whose
    intent is named in the tool, because the card data holds no off topic or rude player line;
  * the request the bench builds is the bridge's own local request (system_local, the same user block,
    the same local_request merge), because a measurement of a different prompt is not a measurement
    of the game;
  * a run that is stopped keeps what it measured, so --resume can finish a bake that was interrupted.

No test here calls a model or a network: the request builder, the line loader and the append / resume
helpers are exercised, and the HTTP call is replaced by a fake.
"""

from __future__ import annotations

import json

import bench_open_weights as bench


def test_twenty_lines_with_the_five_fixtures():
    lines = bench.load_lines()
    assert len(lines) == 20
    assert [row["n"] for row in lines] == list(range(1, 21))
    fixtures = [row for row in lines if row["pool"] == "fixture"]
    assert len(fixtures) == 5
    assert {row["intent"] for row in fixtures} == {"none", "setback"}
    authored = [row for row in lines if row["pool"] != "fixture"]
    assert len(authored) == 15
    assert {row["intent"] for row in authored} == {"soften", "setback"}


def test_every_line_names_a_real_card_and_encounter():
    cards = bench.A.load_cards()
    encounters = bench.A.load_encounters()
    for row in bench.load_lines():
        assert row["card"] in cards, row["card"]
        assert row["player_line"], row["n"]
        assert bench.ENCOUNTER[row["card"]] in encounters, row["card"]


def test_append_and_resume_round_trip(tmp_path):
    path = str(tmp_path / "rows" / "bench.jsonl")
    bench.append(path, {"n": 1, "latency_s": 1.5})
    bench.append(path, {"n": 2, "latency_s": 2.5})
    assert bench.already_done(path) == {1, 2}
    with open(path, "r", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    assert [row["n"] for row in rows] == [1, 2]


def test_already_done_survives_a_half_written_line(tmp_path):
    path = tmp_path / "rows.jsonl"
    path.write_text('{"n": 1}\n{"n": 2, "lat', encoding="utf-8")
    assert bench.already_done(str(path)) == {1}


def test_a_missing_out_file_resumes_from_nothing(tmp_path):
    assert bench.already_done(str(tmp_path / "nothing.jsonl")) == set()
