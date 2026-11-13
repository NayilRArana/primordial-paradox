"""Pins for the shot table take (card t_785b61f0), 253.5 s since the three battle design (Nayil's order).

What these hold down, and why each one earns its place:

  1. the deck carries the two fight triggers the shot table needs and no others: the hound, whose 2 hp is what makes a
     single FIGHT a win, and the deck watch's second figure, which is the only defeat a 20 hp party reaches inside the
     shot (Percy's attack is 4 to 6, the sailor's and the hound's are 2);
  2. the hound is the fight the one command win is claimed on, read from data/enemies/all.json and not from this file,
     so a change to its hp cannot leave the claim standing on a fight that a single FIGHT would no longer end;
  3. the dock office is a route step between the gate and the boarding, and the scene it names is the one the office
     map carries, so the S5 beat is on the route and not only on a map nobody walks to;
  4. data/demo/run_002.json is 253.5 s, passes tools/play_demo.py's own validator, names the beats it claims, and
     every key it presses is a key the game reads, so the submission take cannot drift from the shot table quietly;
  5. every event in run_002 stands on a beat of the 32 beat sheet, and the beats it names are the sheet's own numbers,
     which is what makes verify.json's beat rows checkable against knowledge/DEMO-SCRIPT.md;
  6. data/demo/shot_table.json is the plan the recorder reads (card t_fb7e8271): six shots and six sub-shots whose
     seconds sum to 253.50 inside the table's own tolerance, whose steps meet end to end, whose log lines are the
     script's required beats, and which carry no narrator, because the take has no voice over.

Update, 2026-11-01 (three battle demo): items 1 and 2 above describe the take before the change. Now the deck carries
ONE fight trigger (the deck watch), Morgan is chained inside the three gate branch scenes, Percy starts from the
office scene on the cabin map, the hound is data only, and the take is 253.5 s (15,210 steps, band 243.5 to 263.5)
with Morgan, the deck watch and Percy, and no defeat or game over. The names of the tests that held the old shape
are kept, so each pin keeps its history; the bodies say what they hold now.

Update, 2026-11-01 (Nayil's order, manager decision): exactly three battles, Morgan, one Navy sailor and Percy in his
office, and every fight ends by spare or 0 HP, so there is no forced defeat and no hound fight. Card t_866814e6 had
made `full` a 180 s take around a deck hound fight and a forced defeat door (deck_collapse at 7,4 in Percy's office);
that design was overridden by Nayil's order and both triggers are gone. `full` is the 253.5 s three battle take
again (15,210 steps, band 243.5 to 263.5, data/demo/run_002.json, which is also the QA take). The shot table tooling
needs every table's shots to meet end to end from step 0, so it cannot select a 180 s highlights subset of this
take; that recut is left to the demo card with run_002.json as its source. The hound and deck_collapse rows stay in
the data (the director's forced_defeat read is inert engine support) and nothing starts them, which the pins hold.

Run: python -m pytest tests/test_demo_shots.py -q
"""

from __future__ import annotations

import importlib.util
import json
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
CONFIG_GML = os.path.join(ROOT, "game", "scripts", "pp_config", "pp_config.gml")
MAPS = os.path.join(ROOT, "data", "maps", "all.json")
ENEMIES = os.path.join(ROOT, "data", "enemies", "all.json")
ENCOUNTERS = os.path.join(ROOT, "data", "encounters", "all.json")
SLICE = os.path.join(ROOT, "data", "slice.json")
SCRIPT = os.path.join(ROOT, "data", "demo", "run_002.json")
SHOT_TABLE = os.path.join(ROOT, "data", "demo", "shot_table.json")
PACING = os.path.join(ROOT, "data", "mechanics", "pacing_recipes.json")

DECK = "ship_small"
HOUND = "deck_hound"
WATCH = "tutorial_sailors"
DEFEAT = "percy"
COLLAPSE = "deck_collapse"
OFFICE_STEP = "office"
OFFICE_SCENE = "quay_dock_office_play"
OFFICE_MAP = "quay_dock_office"
SECONDS = 253.5
TAKE_BAND = [243.5, 263.5]
END_STEP = 15210
MORGAN = "morgan_gate"
GATE_SCENES = ("quay_gate_truth", "quay_gate_bluff", "quay_gate_authority")
PERCY_SCENE = "percy_lore_stop"
SCENES = os.path.join(ROOT, "data", "scenes", "all.json")


def load(path: str):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def rows(path: str, key: str) -> dict:
    return {row["id"]: row for row in load(path)[key]}


def load_tool(name: str):
    path = os.path.join(TOOLS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def deck():
    return rows(MAPS, "maps")[DECK]


def battles():
    return [trigger for trigger in deck()["triggers"] if trigger.get("kind") == "battle"]


# ---------------------------------------------------------------------------------------------------------------------
# 1. the two triggers the shot table needs

def test_the_deck_carries_only_the_deck_watch_and_percys_office_no_fight_door():
    """Nayil's order (manager decision 2026-11-01): exactly three battles, and every fight ends by spare or 0 HP.

    The deck carries ONE battle trigger, the deck watch at (4,7), once. The hound's trigger at (6,7) and the forced
    defeat door deck_collapse at (7,4) in Percy's office, both added by card t_866814e6 for a 180 s take, are gone
    again: no hound fight, no forced defeat. Percy is not a deck fight and his office carries no battle trigger either,
    because his fight starts from the scene percy_lore_stop (the next pin).
    """
    by_id = {trigger["id"]: trigger for trigger in battles()}
    assert sorted(by_id) == [WATCH], "the deck carries fight triggers %s; the only deck fight is the deck watch" % sorted(by_id)
    assert (by_id[WATCH]["x"], by_id[WATCH]["y"]) == (4, 7), (
        "the deck watch is at %s, the walk meets it at 4,7" % ((by_id[WATCH]["x"], by_id[WATCH]["y"]),))
    assert by_id[WATCH].get("once") is True, "the deck watch trigger is not once, so a second pass fights it again"
    assert HOUND not in by_id and DEFEAT not in by_id, "the hound or Percy is a deck fight again: %s" % sorted(by_id)

    cabin = rows(MAPS, "maps")["ship_cabin"]
    doors = [trigger["id"] for trigger in cabin["triggers"] if trigger.get("kind") == "battle"]
    assert doors == [], (
        "Percy's office carries battle trigger(s) %s; his fight starts from the scene %s and a forced defeat door "
        "(%s) is not part of the design" % (doors, PERCY_SCENE, COLLAPSE))


# RETIRED by FLOW 2026-11-03: test_the_three_fights_start_from_their_own_doors_and_nothing_starts_the_hound. It pinned the old gate, dock office, boarding and ship route, which the final scope removed.


def test_the_forced_defeat_is_the_row_whose_field_the_director_reads():
    """Inert engine support: since Nayil's order nothing starts a forced defeat (no trigger or scene reaches the row).

    Card t_866814e6 added one data field and six lines of the director so a 180 s take could film a defeat.

    Percy's own fight does not lose: its 20 hp walk-off is a story flag, so a take that wants the game over frame and
    CONTINUE has nothing to land on. The row carries forced_defeat, and the pin is two sided: the row has it, and the
    director's intro step reads it before it draws anything, guarded by variable_struct_exists so a row without the
    field reaches the step it always did.
    """
    encounter = rows(ENCOUNTERS, "encounters")[COLLAPSE]
    assert encounter.get("forced_defeat") is True, "the forced defeat row does not carry forced_defeat"
    assert encounter["lose_dialogue"] == "battle_lose", (
        "the forced defeat plays %r over the lose text; R27's defeat path reads battle_lose" % encounter["lose_dialogue"])
    assert encounter["flags_on_kill"] == [] and encounter["flags_on_spare"] == [], (
        "a fight that cannot be won must not move the story's flags: %s / %s"
        % (encounter["flags_on_kill"], encounter["flags_on_spare"]))
    assert encounter["pacing"]["turns"] == 0, (
        "the forced defeat names %r turns, so the beat does not end on the fight's first step"
        % encounter["pacing"]["turns"])
    assert encounter["pacing"]["band_seconds"][0] <= encounter["pacing"]["seconds"] <= encounter["pacing"]["band_seconds"][1], (
        "the row's %.1f s sits outside its own band %s" % (encounter["pacing"]["seconds"], encounter["pacing"]["band_seconds"]))

    director = os.path.join(ROOT, "game", "scripts", "pp_battle_director", "pp_battle_director.gml")
    with open(director, "r", encoding="utf-8-sig") as handle:
        text = handle.read()
    body = text.split("function pp_battle_step_intro(_battle) {", 1)
    assert len(body) == 2, "pp_battle_step_intro is gone, so nothing reads forced_defeat"
    intro = body[1].split("\n}", 1)[0]
    assert "variable_struct_exists(_battle.encounter, \"forced_defeat\")" in intro, (
        "the intro step reads forced_defeat without the struct guard, so every other encounter's first step would "
        "throw on a variable that is not there")
    assert "pp_battle_enter_result(_battle)" in intro, (
        "the intro step does not hand a forced defeat to pp_battle_enter_result, so the defeat would have no game over")


def test_the_hound_is_the_two_hit_point_fight_the_single_command_claim_rests_on():
    hound = rows(ENEMIES, "enemies")[HOUND]
    assert hound["max_hp"] == 2, (
        "the deck hound has %d hp; the single command win is claimed on a FIGHT that cannot roll under 2 (spec 07 "
        "damage 2 to 12), so this claim is only true while the hound is 2 hp" % hound["max_hp"])
    encounter = rows(ENCOUNTERS, "encounters")[HOUND]
    assert encounter["enemies"] == [HOUND], encounter["enemies"]
    assert encounter["beat"] == 23, (
        "the hound's encounter row names beat %r, and the shot table puts the one command win on beat 23"
        % encounter["beat"])


def test_the_defeat_is_the_only_fight_whose_attack_can_end_a_run_inside_the_shot():
    """Percy hits for 3 to 5 and the party has 20 hp; the other two enemies hit for 2 and would take ten turns."""
    enemies = rows(ENEMIES, "enemies")
    encounters = rows(ENCOUNTERS, "encounters")
    attacks = {name: int((enemies[encounters[name]["enemies"][0]].get("attack") or {}).get("max") or 0)
               for name in (WATCH, HOUND, DEFEAT)}
    assert attacks[DEFEAT] > max(attacks[WATCH], attacks[HOUND]), (
        "the defeat is fought against %r, and its hit does not land harder than the other two: %s. A 20 hp party is "
        "ten hits from a 2 damage enemy, which is not a defeat the shot has time for" % (DEFEAT, attacks))


# ---------------------------------------------------------------------------------------------------------------------
# 2. the office is on the route

# RETIRED by FLOW 2026-11-03: test_the_office_is_a_route_step_between_the_gate_and_the_boarding. It pinned the old gate, dock office, boarding and ship route, which the final scope removed.


def test_the_office_scene_says_the_two_pages_the_pass_arrives_on():
    scenes = load(os.path.join(ROOT, "data", "scenes", "all.json"))["scenes"]
    play = [row for row in scenes if row["id"] == OFFICE_SCENE][0]
    says = [command.get("id") for command in play["commands"] if command.get("cmd") == "say"]
    assert says == ["quay_dock_office", "quay_dock_office_pass"], (
        "the office scene says %r; the pass page is what the S5 claim is evidence for" % (says,))


# ---------------------------------------------------------------------------------------------------------------------
# 3. the take itself

@pytest.mark.windows_only
def test_the_shot_table_script_passes_the_players_own_validator():
    demo = load_tool("play_demo")
    problems = demo.validate_script(load(SCRIPT))
    assert problems == [], "data/demo/run_002.json is refused by tools/play_demo.py: %s" % problems


@pytest.mark.windows_only
def test_the_shot_table_script_is_the_three_battle_take_in_seconds():
    demo = load_tool("play_demo")
    data = load(SCRIPT)
    assert data["clock"]["fps"] == 60
    seconds = demo.planned_seconds(data)
    assert seconds == SECONDS, "the take is %.2f s, and the shot table is %.2f" % (seconds, SECONDS)
    assert data["record"]["min_seconds"] == TAKE_BAND[0], (
        "the recording floor is %r; the take band is %r s" % (data["record"]["min_seconds"], TAKE_BAND))
    assert data["record"]["width"] == 768 and data["record"]["height"] == 720
    assert data["record"]["scale"] == 3


@pytest.mark.windows_only
def test_the_take_names_the_beats_it_has_to_show_and_the_recorder_knows_all_of_them():
    demo = load_tool("play_demo")
    data = load(SCRIPT)
    wanted = data["checks"]["required_beats"]
    known = {name for name, _needle in demo.BEAT_CUES}
    unknown = sorted(set(wanted) - known)
    assert unknown == [], (
        "%r are required by the take and are not rows of play_demo.BEAT_CUES, so the check would fail for a reason "
        "that is this file's" % unknown)
    assert {"S4 gate", "S4 morgan fight", "S5 office", "S5 office talk", "S5 boarding", "S6 talk fight",
            "S6 ship log save", "S6 percy fight"} <= set(wanted), (
        "the three battle take's own beats are not all in its required_beats: %s" % sorted(wanted))
    assert not ({"S6 hound fight", "S6 defeat", "S6 game over", "S6 continue"} & set(wanted)), (
        "the take asks for a hound fight or a defeat, which Nayil's order removed: %s" % sorted(wanted))
    assert data["checks"]["required_footsteps"] >= 1


@pytest.mark.windows_only
def test_the_take_does_not_hold_a_route_step_because_it_plays_the_route():
    data = load(SCRIPT)
    env = data["game"].get("env") or {}
    assert "PP_ROUTE_HOLD" not in env, (
        "the take sets PP_ROUTE_HOLD, so the route is held and the gate, the office and the boarding it claims are "
        "not the ones the route would take")


def test_every_event_stands_on_a_beat_of_the_beat_sheet():
    beats = {row["n"]: row for row in load(PACING)["beat_sheet"]["beats"]}
    data = load(SCRIPT)
    unknown = sorted({event["beat"] for event in data["events"]} - set(beats))
    assert unknown == [], "the take uses beats %r, which the beat sheet does not carry" % unknown


def test_the_notes_in_the_take_carry_no_long_dash():
    """Nayil's rule: no em dash and no en dash, anywhere. The notes are the longest prose in the file."""
    with open(SCRIPT, "r", encoding="utf-8") as handle:
        text = handle.read()
    for mark, name in (("\u2014", "em dash"), ("\u2013", "en dash"), ("\u2012", "figure dash")):
        assert mark not in text, "data/demo/run_002.json carries a %s" % name


# ---------------------------------------------------------------------------------------------------------------------
# 4. the two legs the 07:46 take was missing: the walk to the checkpoint, and a press for every page

QUAY = "southampton_town_quay"
GATE_TRIGGER = "quay_gate_checkpoint"
DIALOGUES = os.path.join(ROOT, "data", "dialogue", "all.json")
TILE_STEPS = 8  # PP_TILE 16 at PP_WALK_SPEED 120 / 60, so one tile is eight held steps


def quay():
    return rows(MAPS, "maps")[QUAY]


def gate_trigger_tile():
    trigger = [row for row in quay()["triggers"] if row.get("id") == GATE_TRIGGER]
    assert trigger, "the quay carries no %r trigger, so S4's gate has no door" % GATE_TRIGGER
    return (trigger[0]["x"], trigger[0]["y"])


def arrival_spawn():
    step = {row["id"]: row for row in load(SLICE)["route"]["steps"]}["arrival"]
    spawn = step.get("spawn") or "start"
    return (quay()["spawns"][spawn]["x"], quay()["spawns"][spawn]["y"])


def walk_legs(spawn, goal):
    """The shortest tile path over the map's own collision rows, as (direction, tiles) legs."""
    collision = quay()["collision"]
    width, height = quay()["width"], quay()["height"]

    def open_tile(x, y):
        return 0 <= x < width and 0 <= y < height and collision[y][x] == "0"

    previous = {spawn: None}
    queue = [spawn]
    while queue:
        here = queue.pop(0)
        if here == goal:
            break
        for dx, dy, name in ((0, -1, "up"), (0, 1, "down"), (-1, 0, "left"), (1, 0, "right")):
            there = (here[0] + dx, here[1] + dy)
            if there in previous or not open_tile(*there):
                continue
            previous[there] = (here, name)
            queue.append(there)
    assert goal in previous, "the checkpoint tile is not reachable on foot from the arrival spawn"
    legs = []
    here = goal
    while previous[here] is not None:
        before, name = previous[here]
        legs.append(name)
        here = before
    legs.reverse()
    runs = []
    for name in legs:
        if runs and runs[-1][0] == name:
            runs[-1][1] += 1
        else:
            runs.append([name, 1])
    return [(name, count) for name, count in runs]


# RETIRED by FLOW 2026-11-03: test_the_arrival_walk_stops_on_the_gate_trigger_because_a_scene_trigger_fires_on_confirm. It pinned the old gate, dock office, boarding and ship route, which the final scope removed.


# RETIRED by FLOW 2026-11-03: test_the_gate_the_office_and_the_gangway_get_a_press_for_every_page. It pinned the old gate, dock office, boarding and ship route, which the final scope removed.


def engine_macro(name: str) -> int:
    """A #macro from pp_config.gml as the engine defines it, so this file cannot wish a number."""
    with open(CONFIG_GML, "r", encoding="utf-8-sig") as handle:
        text = handle.read()
    match = re.search(r"^#macro\s+%s\s+\(?(\d+)" % name, text, re.MULTILINE)
    assert match, "%s is not a #macro in pp_config.gml" % name
    return int(match.group(1))


def camera_x(px: float, map_row: dict) -> float:
    """pp_overworld's camera: the hero is held in the middle of a PP_FRAME_W frame, clamped to the map."""
    frame_w = engine_macro("PP_FRAME_W")
    tile = engine_macro("PP_TILE")
    return max(0.0, min(px + tile * 0.5 - frame_w * 0.5, max(0.0, map_row["width"] * tile - frame_w)))


# RETIRED by FLOW 2026-11-03: test_the_arrival_walk_moves_every_step_and_scrolls_the_field. It pinned the old gate, dock office, boarding and ship route, which the final scope removed.


# ---------------------------------------------------------------------------------------------------------------------
# 5. the shot table as data (card t_fb7e8271): the plan says 253.5 (three battles), means it, and names the lines it needs

def shot_table(name: str = "full") -> dict:
    return load(SHOT_TABLE)["tables"][name]


def shot_rows(table: dict) -> list:
    """Every row of a table, the shots and then each shot's own sub-shots, in the order they are reached."""
    rows = []
    for shot in table["shots"]:
        rows.append(shot)
        rows.extend(shot.get("sub_shots") or [])
    return rows


def test_the_shot_table_adds_up_to_the_three_battle_take():
    table = shot_table()
    assert [shot["id"] for shot in table["shots"]] == ["S1", "S2", "S3", "S4", "S5", "S6"], (
        "the table no longer carries the six shots of knowledge/DEMO-SCRIPT.md section 1: %s"
        % [shot["id"] for shot in table["shots"]])
    total = round(sum(float(shot["seconds"]) for shot in table["shots"]), 3)
    assert abs(total - table["total_seconds"]) <= table["tolerance_seconds"], (
        "the shots sum to %.3f s and the table says %.3f s plus or minus %.2f"
        % (total, table["total_seconds"], table["tolerance_seconds"]))
    assert table["total_seconds"] == SECONDS, "the take is %s seconds, not %r" % (SECONDS, table["total_seconds"],)
    assert table["end_step"] == END_STEP, "%s s at 60 fps is %d steps, not %r" % (SECONDS, END_STEP, table["end_step"])
    assert table["take_band_seconds"] == TAKE_BAND, (
        "the take band is %r s (253.5 s plus or minus 10) and the table names %r"
        % (TAKE_BAND, table["take_band_seconds"]))


def test_the_shot_table_rows_meet_end_to_end_and_their_seconds_are_their_steps():
    table = shot_table()
    fps = float(table["fps"])
    for shot in table["shots"]:
        previous = shot["start_step"]
        for row in shot.get("sub_shots") or []:
            assert row["start_step"] == previous, (
                "%s starts at step %d and the row above it ends at %d" % (row["id"], row["start_step"], previous))
            previous = row["end_step"]
            assert abs(row["seconds"] - (row["end_step"] - row["start_step"]) / fps) <= 0.02, (
                "%s says %.3f s and its steps are %.3f s" % (row["id"], row["seconds"],
                                                             (row["end_step"] - row["start_step"]) / fps))
        if shot.get("sub_shots"):
            assert previous == shot["end_step"], (
                "%s's sub-shots end at %d and the shot ends at %d" % (shot["id"], previous, shot["end_step"]))
            sub_total = round(sum(float(row["seconds"]) for row in shot["sub_shots"]), 3)
            assert abs(sub_total - shot["seconds"]) <= 0.02, (
                "%s's sub-shots sum to %.3f s and the shot is %.3f s" % (shot["id"], sub_total, shot["seconds"]))
    for above, below in zip(table["shots"], table["shots"][1:]):
        assert below["start_step"] == above["end_step"], (
            "%s starts at step %d and %s ends at %d" % (below["id"], below["start_step"], above["id"],
                                                        above["end_step"]))
    assert table["shots"][0]["start_step"] == 0, "the table starts the take at step 0"
    assert table["shots"][-1]["end_step"] == table["end_step"], "the last shot ends the take"


def test_the_shot_table_carries_the_dock_the_three_fights_and_the_save():
    required = set(shot_table()["required_beats"])
    for name in ("S4 gate", "S4 morgan fight", "S5 office", "S5 boarding", "S6 talk fight", "S6 ship log save",
                 "S6 percy fight"):
        assert name in required, (
            "the card asks for the shot %r and the table's required_beats do not name it: %s" % (name, sorted(required)))
    script = set(load(SCRIPT)["checks"]["required_beats"])
    for name in ("S4 morgan fight", "S6 percy fight", "S6 ship log save"):
        assert name in script, (
            "the script's own required_beats do not ask for %r, so a take that never fought or never wrote the save "
            "would pass" % name)


def test_the_full_table_is_the_three_battle_take_and_the_180_s_hound_take_is_retired():
    """Nayil's order (manager decision 2026-11-01) overrode card t_866814e6's design.

    `full` is the 253.5 s take with Morgan at the gate, the deck watch and Percy in his office, played from
    data/demo/run_002.json (the QA take). The 180 s take that card built around a deck hound fight and a forced defeat
    is retired: neither the shot table nor the take may name a hound fight or a defeat. The tooling cannot select a
    180 s subset of this take (every table's shots have to meet end to end from step 0), so the 180 s highlights recut
    is left to the demo card with run_002.json as its source.
    """
    tables = load(SHOT_TABLE)["tables"]
    assert "full-three" not in tables, "the pre-merge table name came back: %s" % sorted(tables)
    table = shot_table()
    assert table["script"] == "data/demo/run_002.json", table["script"]
    assert table["total_seconds"] == SECONDS and table["end_step"] == END_STEP and table["take_band_seconds"] == TAKE_BAND
    required = set(table["required_beats"])
    for name in ("S4 morgan fight", "S6 percy fight"):
        assert name in required, "%r left the three battle take: %s" % (name, sorted(required))
    for name in ("S6 hound fight", "S6 defeat", "S6 game over", "S6 continue"):
        assert name not in required, "the take asks for %r, which Nayil's order removed" % name
    script = load(SCRIPT)
    assert sorted(table["required_beats"]) == sorted(script["checks"]["required_beats"]), (
        "the full table and data/demo/run_002.json ask for different lines")
    markers = [event.get("marker", "") for event in script["events"]]
    for needle in ("PP: battle start deck_hound", "PP: fight result defeat", "PP: game over frame"):
        assert needle not in markers, "the take waits on %r, a hound fight or a defeat the design no longer has" % needle
    assert not os.path.exists(os.path.join(ROOT, "data", "demo", "run_three.json")), (
        "data/demo/run_three.json is back: the three battle take is run_002.json now, and a second copy drifts")


def test_the_shot_table_and_the_script_ask_for_the_same_log_lines():
    table = shot_table()
    assert sorted(table["required_beats"]) == sorted(load(SCRIPT)["checks"]["required_beats"]), (
        "the table requires %s and the script requires %s"
        % (sorted(table["required_beats"]), sorted(load(SCRIPT)["checks"]["required_beats"])))


def test_the_shot_table_plays_the_script_it_names():
    table = shot_table()
    assert table["script"] == "data/demo/run_002.json", (
        "the table plays %r and the submission take is data/demo/run_002.json" % (table["script"],))
    assert os.path.isfile(os.path.join(ROOT, table["script"])), "%s is not on this checkout" % table["script"]


def test_the_shot_table_carries_no_narrator_and_the_take_has_no_voice_over():
    data = load(SHOT_TABLE)
    assert data["narration"]["used"] is False, (
        "the file says the take carries narration: this take has no voice over and the captions belong to the edit")
    for row in shot_rows(shot_table()):
        for key in row:
            assert key.lower() not in ("narrator", "narration", "narrator_text", "voiceover", "voice_over"), (
                "%s carries a %r field, so the take would grow a voice over quietly" % (row.get("id"), key))


def test_the_script_ends_on_percys_ending_scene_and_the_end_card():
    events = load(SCRIPT)["events"]
    by_id = {event["id"]: event for event in events}
    for name in ("p90", "p91", "p92", "p93"):
        assert by_id[name]["kind"] == "key" and by_id[name]["key"] == "confirm", (
            "%s is not a confirm press through the ending scene and the end card" % name)
    assert events[-1]["id"] == "p94" and events[-1]["kind"] == "note", (
        "the take does not end on the note that says the demo is over")
    assert events[-1]["step"] <= END_STEP, (
        "the last beat is at step %d, past the %d the take ends on" % (events[-1]["step"], END_STEP))
    assert END_STEP - events[-1]["step"] <= 420, (
        "the take holds %.1f s after its last beat, and a still frame longer than seven seconds reads as a hang"
        % ((END_STEP - events[-1]["step"]) / 60.0))


def test_the_command_that_plays_the_table_is_documented():
    with open(os.path.join(TOOLS, "play_demo.py"), "r", encoding="utf-8") as handle:
        text = handle.read()
    assert "--shot-table full" in text, "the documented command is not in tools/play_demo.py's own usage block"
    assert 'parser.add_argument("--shot-table"' in text, "the recorder has no --shot-table flag"
    assert "shot_table.json" in text, "the recorder's own words never name the table file it reads"


@pytest.mark.windows_only
def test_the_shot_table_passes_the_recorders_own_validator():
    demo = load_tool("play_demo")
    table = demo.load_shot_table("full")
    assert demo.validate_shot_table(table) == [], (
        "data/demo/shot_table.json's full table is refused by tools/play_demo.py: %s"
        % demo.validate_shot_table(table))
    assert demo.validate_shot_table_script(table, load(SCRIPT)) == [], (
        "the table and data/demo/run_002.json disagree: %s" % demo.validate_shot_table_script(table, load(SCRIPT)))
    assert abs(demo.shot_table_seconds(table) - SECONDS) <= table["tolerance_seconds"]


@pytest.mark.windows_only
def test_the_recorder_knows_every_log_line_the_shot_table_names():
    demo = load_tool("play_demo")
    known = {name for name, _needle in demo.BEAT_CUES}
    table = demo.load_shot_table("full")
    unknown = sorted(set(demo.shot_table_markers(table)) - known)
    assert unknown == [], "%r are named by the shot table and are not rows of play_demo.BEAT_CUES" % (unknown,)


@pytest.mark.windows_only
def test_the_recorder_refuses_a_table_that_does_not_add_up_or_names_a_line_nobody_writes():
    demo = load_tool("play_demo")
    table = demo.load_shot_table("full")

    short = json.loads(json.dumps(table))
    short["total_seconds"] = 170.0
    problems = demo.validate_shot_table(short)
    assert any("tolerance" in problem or "total_seconds" in problem for problem in problems), problems

    wrong_line = json.loads(json.dumps(table))
    wrong_line["shots"][0]["markers"] = ["S7 unicorn"]
    problems = demo.validate_shot_table(wrong_line)
    assert any("BEAT_CUES" in problem for problem in problems), problems

    gap = json.loads(json.dumps(table))
    gap["shots"][2]["start_step"] = gap["shots"][2]["start_step"] + 6
    problems = demo.validate_shot_table(gap)
    assert any("gap or an overlap" in problem for problem in problems), problems

    narrated = json.loads(json.dumps(table))
    narrated["shots"][0]["narrator"] = "a voice over the title"
    problems = demo.validate_shot_table(narrated)
    assert any("narrator" in problem for problem in problems), problems


@pytest.mark.windows_only
def test_a_take_that_never_reached_the_percy_fight_is_failed_by_its_own_name():
    demo = load_tool("play_demo")
    table = demo.load_shot_table("full")
    beats = {name: {"found": True} for name in table["required_beats"]}
    ok, line = demo.shot_table_check(table, 254.0, beats)
    assert ok, line
    assert re.search(r"253\.(49|50)", line), line
    beats["S6 percy fight"] = {"found": False}
    ok, line = demo.shot_table_check(table, 254.0, beats)
    assert not ok, "a take that never reached Percy's fight passed the shot table: %s" % line
    assert "S6 percy fight" in line, line
    # And a take outside the card's band fails on the duration, whatever its log named.
    ok, line = demo.shot_table_check(table, 120.0, {name: {"found": True} for name in table["required_beats"]})
    assert not ok and "band" in line, line


# ---------------------------------------------------------------------------------------------------------------------
# 7. card t_a92c1007: the arrival leg walks up to Morgan, its footsteps are counted, and the press starts his scene
#
# The judge panel's S4 symptom was "three identical still frames": the walk ran, but the confirm fired a trigger the
# quay only story (commit 28d407a2) had already deleted, so the take stood still on an empty tile. These pins hold the
# two halves of the fix: the leg ends where the route's morgan step can be started by a press, and the walk that gets
# there spends real distance, which is what the game turns into footstep cues.

ARRIVAL_HOLDS = ("r011", "r011b", "r012")


def arrival_hold_rows():
    script = load(SCRIPT)
    by_id = {event["id"]: event for event in script["events"]}
    return [(by_id[event_id]["key"], by_id[event_id]["steps"]) for event_id in ARRIVAL_HOLDS]


def test_the_arrival_leg_ends_beside_morgan_and_the_press_that_follows_starts_his_scene():
    """The held directions land the feet on (7,9), one tile east of Morgan, facing him.

    The map is read, not trusted: Morgan's tile comes out of data/maps/all.json, and the scene named on him has to be
    the route's own morgan step, or the press would open a scene the route does not carry.
    """
    holds = arrival_hold_rows()
    assert holds == [("down", 69), ("up", 5), ("left", 136)], (
        "the arrival leg is %r; the pinned recipe is down 69, up 5, left 136 onto (7,9)" % (holds,))

    quay_map = rows(MAPS, "maps")[QUAY]
    morgan_row = [actor for actor in quay_map["actors"] if actor.get("id") == "morgan"]
    assert morgan_row, "the quay carries no morgan actor, so S4 has nobody to walk up to"
    morgan = morgan_row[0]
    assert (morgan["x"], morgan["y"]) == (6, 9), "morgan moved to %r, so the walk's end tile moved with him" % (
        (morgan["x"], morgan["y"]),)
    assert morgan.get("scene") == "quay_morgan_encounter", (
        "morgan's scene is %r, not the route's morgan step" % (morgan.get("scene"),))

    script = load(SCRIPT)
    by_id = {event["id"]: event for event in script["events"]}
    press = by_id["r013b"]
    assert press["kind"] == "key" and press["key"] == "confirm", (
        "the event that follows the leg is %r, so nothing presses to start the scene" % (press.get("kind"),))


def test_the_arrival_leg_moves_every_step_and_earns_its_footstep_cues():
    """The walk is simulated with the shipped constants against the shipped map, actors included.

    Every held step has to move: a leg that is blocked for a tenth of its steps still ends on the right tile with
    fewer pixels walked, and fewer pixels walked is fewer footstep cues. The cue count is the distance divided by
    PP_FOOTSTEP_PX, read from pp_config.gml, so this file cannot wish the floor it asks for.
    """
    bot = load_tool("walker_bot")
    tile = engine_macro("PP_TILE")
    footstep_px = engine_macro("PP_FOOTSTEP_PX")
    reach_px = engine_macro("PP_REACH")

    quay_map = rows(MAPS, "maps")[QUAY]
    collision = quay_map["collision"]
    actors = {(actor["x"], actor["y"]) for actor in quay_map["actors"]}
    spawn = quay_map["spawns"]["start"]

    px, py = float(spawn["x"] * tile), float(spawn["y"] * tile)
    held = moved = 0
    walked = 0.0
    for key, steps in arrival_hold_rows():
        wx, wy = {"down": (0, 1), "up": (0, -1), "left": (-1, 0), "right": (1, 0)}[key]
        for _ in range(steps):
            px, py, distance, _hit_x, _hit_y = bot.free_step(collision, px, py, wx, wy, actors)
            held += 1
            if distance > 0:
                moved += 1
                walked += distance

    assert moved == held, "%d of the leg's %d held steps did not move the feet" % (held - moved, held)
    assert (px, py) == (112.0, 144.0), "the leg ends at px %r, not (112.0, 144.0)" % ((px, py),)
    assert bot.tile_at(px, py) == (7, 9), "the leg ends on tile %r, not (7,9)" % (bot.tile_at(px, py),)

    cues = int(walked // footstep_px)
    assert cues == 26, "the leg walks %r px, which is %d footstep cues and not the 26 the receipt measured" % (
        walked, cues)
    assert cues >= 24, "a walk this long that plays %d footstep cues is a silent walk" % cues

    # The press has to reach Morgan. pp_world_reach_box extends PP_REACH px off the feet box, and
    # pp_overworld_actor_ahead asks whether that rectangle overlaps the actor's own feet box.
    feet = bot.feet_box(px, py)
    reach = (feet[0] - reach_px, feet[1], feet[0] - 1, feet[3])
    morgan_feet = bot.feet_box(6 * tile, 9 * tile)
    overlap = reach[0] <= morgan_feet[2] and reach[2] >= morgan_feet[0] and reach[1] <= morgan_feet[3] \
        and reach[3] >= morgan_feet[1]
    assert overlap, "the reach box %r misses Morgan's feet box %r, so the confirm finds nobody" % (reach, morgan_feet)


def test_the_recorder_names_the_line_the_walk_writes_when_it_reaches_morgan():
    """play_demo.BEAT_CUES: the S4 rows point at lines this build actually writes.

    The S4 gate row named quay_gate_authority, a scene the quay only story deleted; a needle with no emitter can
    never be satisfied, so the beat was unmeetable by construction. Both rows are checked against the GML that writes
    them, and the morgan row against the scene the map's actor carries.
    """
    demo = load_tool("play_demo")
    cues = dict(demo.BEAT_CUES)
    assert cues["S4 gate"] == "PP scene: quay_bridge_wind end at tile", cues["S4 gate"]
    assert cues["S4 morgan talk"] == "PP dialogue: scene quay_morgan_encounter", cues["S4 morgan talk"]

    sources = {}
    for module in ("pp_scene", "pp_overworld"):
        with open(os.path.join(ROOT, "game", "scripts", module, module + ".gml"), "r", encoding="utf-8-sig") as fh:
            sources[module] = fh.read()
    assert '"PP scene: " + string(_sc.id) + " end at tile "' in sources["pp_scene"], (
        "pp_scene no longer writes the line the S4 gate row asks for")
    assert '"PP dialogue: scene " + string(_actor.scene)' in sources["pp_overworld"], (
        "pp_overworld no longer writes the line the S4 morgan row asks for")

    scenes = {row["id"] for row in load(SCENES)["scenes"]}
    assert "quay_bridge_wind" in scenes, "the S4 gate scene is not in data/scenes/all.json"
    assert "quay_morgan_encounter" in scenes, "the S4 morgan scene is not in data/scenes/all.json"
    assert "quay_gate_authority" not in scenes, (
        "quay_gate_authority is back in the scenes file; check whether the S4 row should name it again")


def test_the_gate_leg_presses_the_talk_box_and_no_deleted_choice():
    """The presses after Morgan's say pages, read against the scene the build actually starts.

    quay_morgan_encounter is face, face, sfx, flash, say quay_morgan_pre, talk, wait 20, battle morgan_gate
    (data/scenes/all.json), so the leg needs two presses for each say page and then exactly ONE press to close the
    talk box answer. It used to carry seven more: a No pass. / Crew list. choice and a four press bluff reply, all of
    them pages of quay_gate_checkpoint, which the quay only story deleted. This pin holds the count to the scene's own
    pages and holds the closing press to the answer's own log line, so a take cannot aim at a box the build cannot
    open and cannot fire into the battle before the answer lands.
    """
    script = load(SCRIPT)
    events = script["events"]
    by_id = {event["id"]: event for event in events}

    scenes = {row["id"]: row for row in load(SCENES)["scenes"]}
    commands = scenes["quay_morgan_encounter"]["commands"]
    talk = [command for command in commands if command["cmd"] == "talk"]
    assert len(talk) == 1 and talk[0]["npc"] == "morgan", (
        "quay_morgan_encounter no longer carries the one talk command this leg presses into: %r" % (commands,))
    order = [command["cmd"] for command in commands]
    assert order.index("wait") < order.index("battle"), (
        "the talk box is no longer followed by the wait before the battle: %r" % (order,))

    dialogue = {row["id"]: row for row in load(os.path.join(ROOT, "data", "dialogue", "all.json"))["dialogue"]}
    pages = len(dialogue["quay_morgan_pre"]["pages"])

    start_step = by_id["r013b"]["step"]
    battle_step = by_id["m01"]["step"]
    inside = [event for event in events if start_step < event["step"] < battle_step]

    page_presses = [event for event in inside if event["kind"] == "key" and event["step"] < by_id["r020"]["step"]]
    assert len(page_presses) == 2 * pages, (
        "the leg presses %d times for a %d page say, and two presses a page is %d"
        % (len(page_presses), pages, 2 * pages))

    close = [event for event in inside if event["step"] >= by_id["r020"]["step"]]
    assert len(close) == 1, "the leg still presses %d times after the say pages: %r" % (
        len(close), [event["id"] for event in close])
    press = close[0]
    assert press["kind"] == "key" and press["key"] == "confirm", press
    assert press["marker"] == "PP: talk scene answer, npc " + talk[0]["npc"], (
        "the closing press waits on %r, not on the answer's own line" % (press.get("marker"),))
    assert press["marker_delay_steps"] > 0, "the press fires on the answer's own step with no settle delay"
    assert press["marker_wait_s"] >= script["talk"]["timeout_s"], (
        "marker_wait_s %r is shorter than the script's own talk timeout %r, so a live answer would be pressed past"
        % (press["marker_wait_s"], script["talk"]["timeout_s"]))

    with open(os.path.join(ROOT, "game", "scripts", "pp_talk_persona", "pp_talk_persona.gml"),
              "r", encoding="utf-8-sig") as handle:
        persona = handle.read()
    assert '"PP: talk scene answer, npc " + _state.scene_npc' in persona, (
        "pp_talk_persona no longer writes the line the closing press waits on")

    retired = [event["id"] for event in events
               if event["id"] != press["id"]
               and ("Crew list" in event["note"] or "bluff reply" in event["note"] or "the choice page" in event["note"])]
    assert not retired, (
        "the leg still presses the deleted gate pages in %r; quay_gate_checkpoint is not in the build" % (retired,))
