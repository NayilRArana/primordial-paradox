"""The demo's six shots, carried by data/slice.json and pinned to the script that owns their shape.

Why this file exists: card t_39c1f4df asks for six shots S1 to S6 totalling 180 seconds, one caption per
shot, in data/slice.json, and the judge panel measured a 73.483 s cut against them. The route alone cannot
say how long the demo is or what is written over it, so the slice now carries the shape as well, and this
file keeps that copy honest against the document that owns the words.

Sources this file measures, never restates:

    data/slice.json                     the shots table, its totals, and the route steps each shot names
    knowledge/DEMO-SCRIPT.md            section 1's table: the clock, the seconds, the steps, the route step
                                        column; and each section 3 caption, read by its own reader
    tools/demo_overlay.py               shot_caption, imported and not copied, so the caption on the frame
                                        and the caption in the data are read by one function

What is proved:

  1. the slice carries six shots, S1 to S6 in order, and nothing else;
  2. each shot's seconds, steps and route steps are the ones section 1's table names;
  3. the six seconds add to the declared 180.00 and the six step counts to 10,800, and each row's own
     steps value is its seconds times the declared rate;
  4. the clocks are contiguous from 0:00.00 to 3:00.00, so no shot is a gap and none overlaps;
  5. each shot's caption is the script's own words, verbatim, read out of the script by demo_overlay;
  6. every route step a shot names resolves in the route, so a shot cannot point at a step nobody wrote;
  7. no caption carries a long dash, which the project forbids in text it ships;
  8. the 5.00 s title card is a row of the slice, held inside S1 without changing S1's scripted 16.00 s, and
     the words it draws name the game, the Meta talk model the tools/meta_client.py table holds, and the
     NES limits it obeys (card t_5876de50, the 2026-11-14 panel's fix 1; card t_379273cc, the 2026-11-15
     panel's fix 1, which raised the hold from four seconds to five).

No test here runs GameMaker, reads the network or writes a tracked file.
"""

from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import demo_overlay  # noqa: E402  the caption reader the video builder draws with

SLICE_PATH = os.path.join(ROOT, "data", "slice.json")
SCRIPT_PATH = os.path.join(ROOT, "knowledge", "DEMO-SCRIPT.md")

SHOT_IDS = ("S1", "S2", "S3", "S4", "S5", "S6")
TOTAL_SECONDS = 180.0
TOTAL_STEPS = 10800
LONG_DASHES = ("\u2013", "\u2014", "\u2012", "\u2015")

SHOT_ROW = re.compile(r"^\|\s*(S\d)\s*\|")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def _load(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def section_one_rows() -> dict:
    """Section 1's six rows, parsed: clock, seconds, steps and the route steps its column names."""
    lines = _read(SCRIPT_PATH).splitlines()
    start = next(index for index, line in enumerate(lines) if line.startswith("## 1."))
    end = next(index for index, line in enumerate(lines[start + 1:], start + 1) if line.startswith("## 2."))
    rows = {}
    for line in lines[start:end]:
        match = SHOT_ROW.match(line)
        if not match:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        shot = cells[0]
        clock = [part.strip() for part in cells[1].split(" to ")]
        rows[shot] = {
            "clock": clock,
            "seconds": float(cells[2].replace(",", "")),
            "steps": int(cells[3].replace(",", "")),
            "route_steps": re.findall(r"`([a-z_]+)`", cells[4]),
        }
    return rows


def shots() -> dict:
    body = _load(SLICE_PATH).get("shots") or {}
    return body


def rows() -> list:
    return shots().get("rows") or []


SCRIPT = section_one_rows()
ROWS = rows()


def test_the_slice_carries_six_shots_in_order():
    ids = [row.get("id") for row in ROWS]
    assert ids == list(SHOT_IDS), "data/slice.json shots[].id is %r, and the script's six shots are %r" % (
        ids, list(SHOT_IDS))
    assert len(SCRIPT) == len(SHOT_IDS), "knowledge/DEMO-SCRIPT.md section 1 parsed %d rows, not six: %r" % (
        len(SCRIPT), sorted(SCRIPT))


def test_each_shot_is_the_length_the_script_gives_it():
    problems = []
    for row in ROWS:
        shot = row.get("id")
        wanted = SCRIPT.get(shot)
        if wanted is None:
            problems.append("%s: the script's section 1 has no row for it" % shot)
            continue
        if row.get("seconds") != wanted["seconds"]:
            problems.append("%s: the slice says %r s, the script says %r s" % (shot, row.get("seconds"), wanted["seconds"]))
        if row.get("steps") != wanted["steps"]:
            problems.append("%s: the slice says %r steps, the script says %r" % (shot, row.get("steps"), wanted["steps"]))
        if list(row.get("route_steps") or []) != wanted["route_steps"]:
            problems.append("%s: the slice names route steps %r, the script names %r"
                            % (shot, row.get("route_steps"), wanted["route_steps"]))
        if list(row.get("clock") or []) != wanted["clock"]:
            problems.append("%s: the slice clocks %r, the script clocks %r"
                            % (shot, row.get("clock"), wanted["clock"]))
    assert problems == [], "\n".join(problems)


def test_the_six_shots_add_up_to_the_declared_total():
    body = shots()
    seconds = sum(row["seconds"] for row in ROWS)
    steps = sum(row["steps"] for row in ROWS)
    assert abs(seconds - TOTAL_SECONDS) < 1e-9, "the shots add to %r s, not 180.00" % seconds
    assert steps == TOTAL_STEPS, "the shots add to %d steps, not 10,800" % steps
    assert abs(body.get("total_seconds", -1) - TOTAL_SECONDS) < 1e-9, \
        "the table declares total_seconds %r" % body.get("total_seconds")
    assert body.get("total_steps") == TOTAL_STEPS, "the table declares total_steps %r" % body.get("total_steps")

    rate = body.get("steps_per_second")
    assert rate == 60, "the table declares %r steps a second, and the game runs 60" % rate
    for row in ROWS:
        assert row["steps"] == int(round(row["seconds"] * rate)), \
            "%s: %r s at %r steps a second is %r steps, the row says %r" % (
                row["id"], row["seconds"], rate, int(round(row["seconds"] * rate)), row["steps"])


def test_the_clocks_are_contiguous_from_zero_to_three_minutes():
    clock = 0.0
    problems = []
    for row in ROWS:
        start = clock_seconds(row["clock"][0])
        end = clock_seconds(row["clock"][1])
        if abs(start - clock) > 1e-9:
            problems.append("%s starts at %.2f s and the shot before it ends at %.2f s" % (row["id"], start, clock))
        if abs((end - start) - row["seconds"]) > 1e-9:
            problems.append("%s clocks %.2f s of picture and says %r s" % (row["id"], end - start, row["seconds"]))
        clock = end
    if abs(clock - TOTAL_SECONDS) > 1e-9:
        problems.append("the last shot ends at %.2f s, not 180.00" % clock)
    assert problems == [], "\n".join(problems)


def clock_seconds(text: str) -> float:
    minutes, seconds = text.split(":")
    return int(minutes) * 60 + float(seconds)


def test_each_shot_caption_is_the_scripts_own_words():
    problems = []
    for row in ROWS:
        wanted = demo_overlay.shot_caption(row["id"], SCRIPT_PATH)
        if row.get("caption") != wanted:
            problems.append("%s:\n  data/slice.json: %r\n  the script:     %r"
                            % (row["id"], row.get("caption"), wanted))
    assert problems == [], "\n".join(problems)


def test_no_caption_carries_a_long_dash():
    for row in ROWS:
        for dash in LONG_DASHES:
            assert dash not in row.get("caption", ""), "%s's caption carries %r" % (row["id"], dash)


def test_every_route_step_a_shot_names_is_in_the_route():
    route = _load(SLICE_PATH).get("route") or {}
    known = {step.get("id") for step in route.get("steps") or []}
    problems = []
    for row in ROWS:
        for step_id in row.get("route_steps") or []:
            if step_id not in known:
                problems.append("%s names the route step %r, and the route does not carry it (%r)"
                                % (row["id"], step_id, sorted(known)))
    assert problems == [], "\n".join(problems)
    assert ROWS, "the slice carries no shot rows at all"


# ---------------------------------------------------------------------------------------------------------
# The 16.00 s title card (card t_5876de50 asked for four; card t_379273cc, judge panel 2026-11-15 fix 1,
# raised the hold to five; card t_b231fe46, judge panel 2026-11-16 fix 3, raised it to S1's whole 16.00 s
# because the only S1 footage on disk measures as blue bands at 15.0 s). A judge will see a readable title in
# the first 16 seconds. The card is data, so these pins read it as data and hold it to the drawing the cut burns.

def title_card() -> dict:
    return shots().get("title_card") or {}


def test_the_slice_carries_a_sixteen_second_title_card():
    card = title_card()
    assert card, "data/slice.json shots.title_card is missing, so no card is held"
    assert card.get("clock") == ["0:00.00", "0:16.00"], "the card clocks %r" % (card.get("clock"),)
    assert card.get("seconds") == 16.0, "the card is %r s and the card asks for S1's whole shot" % (card.get("seconds"),)
    rate = shots().get("steps_per_second")
    assert card.get("steps") == int(round(card["seconds"] * rate)), \
        "the card says %r steps at %r a second" % (card.get("steps"), rate)
    assert card.get("held_by") == "S1", "the card is held by %r" % (card.get("held_by"),)
    assert card.get("picture_seconds") == 0.0, \
        "the card covers its shot, so no picture seconds are left under it (%r)" % (card.get("picture_seconds"),)


def test_the_card_is_held_inside_s1_and_s1_keeps_its_scripted_length():
    card = title_card()
    first = ROWS[0]
    assert first["id"] == card.get("held_by"), "the first shot is %r" % first["id"]
    assert first.get("title_card_seconds") == card.get("seconds"), \
        "S1 rows the card at %r s and the card is %r s" % (first.get("title_card_seconds"), card.get("seconds"))
    assert first["clock"][0] == card["clock"][0], "S1 starts at %r and the card starts at %r" % (
        first["clock"][0], card["clock"][0])
    assert clock_seconds(card["clock"][1]) <= clock_seconds(first["clock"][1]), \
        "the card ends at %r, past S1's %r" % (card["clock"][1], first["clock"][1])
    assert first["seconds"] == card["seconds"] + card.get("picture_seconds", -1), \
        "S1 is %r s, and the card plus the picture under it is %r s" % (
            first["seconds"], card["seconds"] + card.get("picture_seconds", -1))
    assert first["seconds"] == SCRIPT["S1"]["seconds"], "S1 left its scripted length"


def test_the_card_names_the_game_and_the_meta_talk_judge():
    import importlib.util

    spec = importlib.util.spec_from_file_location("video_builder", os.path.join(TOOLS_DIR, "video_builder.py"))
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)

    card = title_card()
    drawn = list(builder.title_card_lines())
    names = card.get("names") or []
    assert names, "the slice's card names nothing"
    assert names[0] == drawn[0], "the slice calls the game %r and the card draws %r" % (names[0], drawn[0])

    models = builder._load_meta_default_models()
    role = card.get("judge_role")
    assert role in models, "the card's judge_role is %r and DEFAULT_MODELS has %r" % (role, sorted(models))
    assert any(models[role].upper() in line.upper() for line in drawn), \
        "the card does not draw the %r model %r" % (role, models[role])
    assert builder.title_card_seconds() == card["seconds"], \
        "the builder holds the card %r s and the slice says %r s" % (builder.title_card_seconds(), card["seconds"])
    assert os.path.exists(os.path.join(ROOT, card.get("drawn_by") or "")), \
        "the slice's drawn_by %r is not a file" % (card.get("drawn_by"),)


def test_the_card_names_the_nes_limits_it_obeys():
    """The panel's fix 1 asks for the game and the talk judge INSIDE NES limits, so the limits are pinned too."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("video_builder", os.path.join(TOOLS_DIR, "video_builder.py"))
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)

    drawn = [line.upper() for line in builder.title_card_lines()]
    assert any("256X240" in line for line in drawn), "the card does not name the 256x240 screen"
    assert any("16 COLOURS" in line for line in drawn), "the card does not name the 16 colour limit"
    named = " ".join(title_card().get("names") or []).upper()
    assert "NES LIMITS" in named, "the slice's card names no NES limit: %r" % (title_card().get("names"),)


def test_the_card_names_a_route_step_the_route_carries():
    route = _load(SLICE_PATH).get("route") or {}
    known = {step.get("id") for step in route.get("steps") or []}
    for step_id in title_card().get("route_steps") or []:
        assert step_id in known, "the card names route step %r, and the route does not carry it" % (step_id,)
