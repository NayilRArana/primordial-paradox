"""THE DOCKSIDE EXCHANGE: the S5 office beat takes a typed line and answers it in the box (card t_1163ca72).

The card asks for one beat of the demo to stop being read only: at the dock office the player approaches the clerk,
says his name, and the character answers with the model's verdict on that line. This file proves that beat from the
files, with no GameMaker run, no network and no key, the way the rest of the suite does.

Sources this file measures, never restates:

    data/scenes/all.json        the office scene's command list, in order
    data/meta_bake.json         the recorded turns the box answers with (npc/nye/turn_1 to turn_3)
    game/scripts/pp_scene/pp_scene.gml          the `talk` command and the step that owns the exchange
    game/scripts/pp_talk_persona/pp_talk_persona.gml   pp_talk_scene_*: the box, the turn, the verdict, the draw
    game/scripts/pp_talk_live/pp_talk_live.gml  the entry box and pp_talk_live_effect_verdict
    game/scripts/pp_app/pp_app.gml              the overworld draw that calls the overlay
    data/demo/run_002.json      the take's presses around the exchange
    tools/capture_title.py      the key table the recorder can send

What is proven:

  1. the beat's shape: the office scene walks the hero to the counter, says the clerk's line, takes the player's
     line, says the pass line and ends, in that order;
  2. the words are recorded, not fetched: the answer path reads the bake and calls no network, and it logs the
     verdict with its source;
  3. the verdict map is the inverse of the one the fight talk already uses, so one table decides both directions;
  4. the box is the dialogue box: pp_window_draw, the plate on the top border, the sheet's own font, no draw_text;
  5. the player's line is kept on the state and never logged, never sent, never saved;
  6. the take can press it: every key the exchange needs is one the recorder can send, in an order the tape
     validator accepts;
  7. the beat cannot strand: a scene whose npc has no recorded turn reports and walks on, and cancel closes the box;
  8. the self test can play it headless.
"""

from __future__ import annotations

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENES = os.path.join(ROOT, "data", "scenes", "all.json")
BAKE = os.path.join(ROOT, "data", "meta_bake.json")
MAPS = os.path.join(ROOT, "data", "maps", "all.json")
SCRIPT = os.path.join(ROOT, "data", "demo", "run_002.json")
SCENE_GML = os.path.join(ROOT, "game", "scripts", "pp_scene", "pp_scene.gml")
PERSONA_GML = os.path.join(ROOT, "game", "scripts", "pp_talk_persona", "pp_talk_persona.gml")
LIVE_GML = os.path.join(ROOT, "game", "scripts", "pp_talk_live", "pp_talk_live.gml")
APP_GML = os.path.join(ROOT, "game", "scripts", "pp_app", "pp_app.gml")
CAPTURE = os.path.join(ROOT, "tools", "capture_title.py")

OFFICE = "quay_dock_office_play"
NPC = "nye"
PLATE = "NYE"


def load(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def read_text(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def gml_function(text, name):
    """The body of one GML function, from its `function name(` to the closing brace at column 0."""
    start = text.find("function %s(" % name)
    assert start >= 0, "%s is not defined" % name
    end = text.find("\n}", start)
    assert end > start, "%s has no closing brace at column 0" % name
    return text[start:end + 2]


def office_scene():
    for row in load(SCENES)["scenes"]:
        if row["id"] == OFFICE:
            return row
    raise AssertionError("the office scene %r is gone" % OFFICE)


def test_the_office_beat_walks_up_says_takes_the_line_and_ends():
    """The card's order: player approaches, the clerk speaks, the player's speech is captured, the pass, the end."""
    commands = office_scene()["commands"]
    shape = [command["cmd"] for command in commands]
    assert shape == ["move", "face", "say", "talk", "say", "end"], (
        "the office beat is %r; the card asks for the hero to walk up, the clerk's line, the player's line, the "
        "pass and the end, in that order" % (shape,))
    assert commands[0]["dir"] == "up" and commands[0]["tiles"] >= 1, (
        "the beat must walk the hero toward the counter before it speaks")
    talk = commands[3]
    assert talk["npc"] == NPC, "the exchange is not with %r, it is with %r" % (NPC, talk["npc"])
    assert talk["plate"] == PLATE, "the box draws the wrong plate: %r" % (talk["plate"],)


def test_the_clerk_the_beat_speaks_to_is_standing_on_the_office_map():
    """The checker proves this too; pinning it here keeps the beat and the room from drifting apart."""
    scene = office_scene()
    maps = {row["id"]: row for row in load(MAPS)["maps"]}
    assert scene["map"] in maps, "the office scene's map %r is not in data/maps/all.json" % (scene["map"],)
    map_row = maps[scene["map"]]
    actors = {actor["id"] for actor in map_row.get("actors") or []}
    assert NPC in actors, "%r is not one of %r's actors: %r" % (NPC, scene["map"], sorted(actors))
    width, height = map_row["width"], map_row["height"]
    assert 0 <= scene["start"]["x"] < width and 0 <= scene["start"]["y"] < height, (
        "the beat starts outside the map, so the walk to the counter is not the walk the map draws")


# ------------------------------------------------------------------ the gate beat (card t_21951674)

GATE = "quay_morgan_encounter"
GATE_NPC = "morgan"
GATE_PLATE = "MORGAN"


def gate_scene():
    for row in load(SCENES)["scenes"]:
        if row["id"] == GATE:
            return row
    raise AssertionError("the gate scene %r is gone" % GATE)


def test_the_gate_beat_asks_the_player_line_before_the_fight():
    """Card t_21951674: Morgan's beat carries one exchange, and it stands between his words and the fight.

    The panel's fix is that a judge sees the player's line judged on screen at the gate, not only in the office, so
    the beat has to carry a `talk` with a line already written and the battle has to come after it.
    """
    commands = gate_scene()["commands"]
    shape = [command["cmd"] for command in commands]
    assert "talk" in shape, "the gate beat never asks the bridge: %r" % (shape,)
    index = shape.index("talk")
    assert shape.index("battle") > index, "the exchange plays after the fight opens, so nobody sees it"
    talk = commands[index]
    assert talk["npc"] == GATE_NPC, "the exchange is not with %r, it is with %r" % (GATE_NPC, talk["npc"])
    assert talk["plate"] == GATE_PLATE, "the box draws the wrong plate: %r" % (talk["plate"],)
    line = talk.get("line", "")
    assert line.strip(), "the gate exchange has no line, so it would wait on a keyboard nobody is at"
    assert len(line) <= 120 and all(32 <= ord(ch) < 127 for ch in line), (
        "the line is outside the box: %r" % (line,))


def test_the_gate_exchange_speaks_to_a_character_standing_on_the_quay():
    scene = gate_scene()
    maps = {row["id"]: row for row in load(MAPS)["maps"]}
    map_row = maps[scene["map"]]
    actors = {actor["id"] for actor in map_row.get("actors") or []}
    assert GATE_NPC in actors, "%r is not one of %r's actors: %r" % (GATE_NPC, scene["map"], sorted(actors))


def test_the_gate_line_is_asked_through_the_boxs_own_call():
    """The authored line travels the typed line's road: pp_talk_scene_ask, which is pp_talk_scene_submit underneath.

    A second send written for cutscenes would be a second path with its own gating, its own timeout and its own
    label, so the pin is that the command's line reaches the one call the box already owns.
    """
    body = gml_function(read_text(SCENE_GML), "pp_scene_command_start")
    talk = body[body.index('case "talk":'):body.index('case "setflag":')]
    assert 'variable_struct_exists(_cmd, "line")' in talk, "the runner never reads the command's line"
    assert "pp_talk_scene_ask(_talk, _cmd.line)" in talk, (
        "the authored line is not handed to the box's own send")
    ask = gml_function(read_text(PERSONA_GML), "pp_talk_scene_ask")
    assert "pp_talk_scene_submit(_state)" in ask, "the one call no longer routes to the one send"


def test_the_line_being_judged_stays_on_screen_while_it_is_weighed():
    """The answer rows and the verdict are drawn after the send; the line itself used to vanish with the entry box."""
    body = gml_function(read_text(PERSONA_GML), "pp_talk_scene_draw_entry")
    wait = body[body.index('live_stage == "wait"'):]
    assert "pp_talk_live_rows(string_upper(_state.live_text))" in wait, (
        "the wait stage draws no line, so a take cannot show what the model was judging")
    assert "pp_talk_live_dots(" in wait, "the thinking dots left the wait stage"


def test_the_answer_comes_from_the_bake_and_opens_no_network():
    persona = read_text(PERSONA_GML)
    body = gml_function(persona, "pp_talk_scene_submit")
    # The rows are read once, when the exchange is built, and the send only picks the turn out of them.
    assert "pp_talk_npc_rows(" in gml_function(persona, "pp_talk_scene_new"), (
        "the exchange is not filled from the recorded turns")
    assert "_state.scene_rows[" in body, "the answer path does not read the recorded turns"
    # Card t_330b12ce: the send has two paths now, and the branch is the whole guarantee. Live mode asks the same
    # local bridge the fight talk asks; every other mode, which is the demo and every test, is the recorded turn and
    # reaches for nothing. So the assertion moved from "the function never names a socket" to the shape that makes
    # that true: one gate, one call, and the bake read after it.
    live = body.index("pp_talk_live_is_live()")
    send = body.index("pp_talk_live_send_talk(_state);")
    bake = body.index("_state.scene_rows[")
    assert live < send < bake, (
        "the scene's network call is not gated ahead of the recorded turn: live %d, send %d, bake %d"
        % (live, send, bake))
    tail = body[bake:]
    for forbidden in ("pp_talk_live_send_talk", "pp_talk_live_send_hear", "pp_ai_", "http_", "url_"):
        assert forbidden not in tail, (
            "the replay path calls %s: a cutscene with no bridge may never wait on a socket" % forbidden)
    assert body.count("pp_talk_live_send_talk(") == 1, "the scene names the send more than once, so a path is ungated"
    assert 'source: "bake"' in body, "the answer does not say where its words came from"


def test_a_scene_send_is_answered_by_its_own_reader():
    """Card t_330b12ce: the scene's answer path is pp_talk_scene_answer, reached from pp_talk_live_answer."""
    persona = read_text(PERSONA_GML)
    for name in ("pp_talk_scene_request", "pp_talk_scene_answer", "pp_talk_scene_answer_clean",
                 "pp_talk_scene_async", "pp_talk_scene_verdict_line", "pp_talk_scene_rows"):
        assert "function %s(" % name in persona, "%s is missing, so the scene leg has no reader" % name
    live = gml_function(read_text(LIVE_GML), "pp_talk_live_answer")
    assert "pp_talk_scene_answer(_battle, _doc, _via)" in live, (
        "an answer for a scene state is routed to the persona or the fight reader instead")
    ask = gml_function(read_text(LIVE_GML), "pp_talk_live_request")
    assert "pp_talk_scene_request(_battle)" in ask, "a scene state's request body is not built by the scene path"


def test_the_log_carries_the_verdict_and_the_length_but_never_the_line():
    body = gml_function(read_text(PERSONA_GML), "pp_talk_scene_submit")
    assert 'array_push(_state.scene_said, _line);' in body, (
        "the player's line is no longer kept on the scene's own state")
    log_lines = re.findall(r'show_debug_message\((.*?)\);', body, re.S)
    assert log_lines, "the answer path writes no log, so a take cannot prove the exchange happened"
    for entry in log_lines:
        # A length is allowed, the words are not: take the one permitted expression out and nothing may name the line.
        stripped = entry.replace("string_length(_line)", "")
        assert "_line" not in stripped, "a log line prints the player's words: %r" % entry
        assert "string_length(_line)" in entry or "scene_npc" in entry, (
            "a log line neither names the npc nor measures the line: %r" % entry)


def test_the_turn_advances_and_a_send_past_the_last_turn_repeats_it():
    body = gml_function(read_text(PERSONA_GML), "pp_talk_scene_submit")
    assert "min(_state.scene_turn, array_length(_state.scene_rows) - 1)" in body, (
        "the turn index is not clamped, so a fourth send would read past the bake")
    assert "_state.scene_turn += 1;" in body, "the turn never advances, so every send gets turn one"


def test_the_verdict_map_is_the_inverse_of_the_fights_own_table():
    live = read_text(LIVE_GML)
    effect_body = gml_function(live, "pp_talk_live_verdict_effect")
    inverse_body = gml_function(live, "pp_talk_live_effect_verdict")
    # The fight's table: persuaded is a soften on a full row, angered a setback, unmoved nothing.
    assert '"soften"' in effect_body and '"persuaded"' in effect_body, "the fight's table lost soften"
    assert '"setback"' in effect_body and '"angered"' in effect_body, "the fight's table lost setback"
    # The box's table must answer the same way round, or a reply and its verdict disagree on screen.
    flat = re.sub(r"\s+", " ", inverse_body)
    assert 'case "soften": return "persuaded"' in flat, "soften no longer reads persuaded"
    assert 'case "nudge": return "persuaded"' in flat, "nudge no longer reads persuaded"
    assert 'case "setback": return "angered"' in flat, "setback no longer reads angered"
    assert 'return "unmoved"' in flat, "the inverse map has no default"


def test_the_verdict_table_agrees_with_the_judges_own_map():
    """One table decides a verdict in data. The box must read it the same way the receipt and the overlay do."""
    judge = load(os.path.join(ROOT, "data", "talk", "sailor_judge.json"))
    verdicts = judge["verdicts"]
    assert set(verdicts) == {"soften", "nudge", "none", "setback", "end"}, (
        "the judge's effect map changed: %r" % sorted(verdicts))
    body = gml_function(read_text(LIVE_GML), "pp_talk_live_effect_verdict")
    flat = re.sub(r"\s+", " ", body)
    cases = dict(re.findall(r'case "(\w+)": return "(\w+)";', flat))
    returns = re.findall(r'return "(\w+)";', flat)
    assert returns, "the inverse map returns nothing"
    default = returns[-1]
    for effect, row in verdicts.items():
        got = cases.get(effect, default)
        assert got == row["verdict"], (
            "effect %r reads %r in the box and %r in data/talk/sailor_judge.json" % (effect, got, row["verdict"]))


def test_the_verdict_line_reads_both_shapes_the_field_holds():
    """A scene send stores the verdict word; pp_talk_live_state_init seeds the effect name "none". Both must read."""
    text = read_text(PERSONA_GML)
    word = gml_function(text, "pp_talk_scene_verdict_word")
    assert 'case "persuaded": return "persuaded";' in word, "a verdict word is not passed through"
    assert "pp_talk_live_effect_verdict(_v)" in word, (
        "an effect name is not run through the map, so the row would print NYE IS NONE.")
    line = gml_function(text, "pp_talk_scene_verdict_line")
    assert "pp_talk_scene_verdict_word(" in line, "the verdict row does not use the normalised word"


def test_the_box_is_the_dialogue_window_and_draws_with_the_sheets_own_font():
    text = read_text(PERSONA_GML)
    body = gml_function(text, "pp_talk_scene_draw")
    assert "pp_window_draw(" in body, "the exchange draws its own box instead of the game's window"
    assert "PP_PLATE_X" in body and "PP_BOX_Y" in body, "the plate is not drawn on the window's top border"
    assert "pp_talk_scene_verdict_line(" in body, "the verdict is never drawn"
    assert "draw_text(" not in body and "draw_text(" not in gml_function(text, "pp_talk_scene_draw_entry"), (
        "the box draws with the GameMaker default font (the project has no font resource)")
    for name in ("pp_talk_scene_draw", "pp_talk_scene_draw_entry"):
        assert "pp_font_draw" in gml_function(text, name), "%s does not use the 8x8 sheet" % name


def test_the_verdict_line_is_drawable_on_the_sheet():
    """The sheet is one row of 8x8 frames: the letters, the space and the period are what a row may carry."""
    body = gml_function(read_text(PERSONA_GML), "pp_talk_scene_verdict_line")
    assert "string_upper(" in body, "the verdict is drawn in a case the box does not use"
    assert 'return "* " + string(_state.scene_plate)' in body, "the verdict line lost the character's name"
    sheet = gml_function(read_text(os.path.join(ROOT, "game", "scripts", "pp_font", "pp_font.gml")),
                         "pp_font_glyphs")
    literal = re.search(r'return (".*?");', sheet, re.S)
    assert literal, "pp_font_glyphs no longer returns a sheet string"
    set_of_glyphs = literal.group(1)[1:-1].encode().decode("unicode_escape")
    for char in "* " + PLATE + "ISUNMOVEDANGERPERSUAD.":
        assert char in set_of_glyphs, "the sheet cannot draw %r, so the verdict row would print a hole" % char


def test_the_beat_cannot_strand_a_scene():
    scene_text = read_text(SCENE_GML)
    start = gml_function(scene_text, "pp_scene_command_start")
    assert 'case "talk":' in start, "the runner has no talk case"
    talk_case = start[start.find('case "talk":'):start.find('case "setflag":')]
    assert talk_case.count("pp_scene_advance(_sc, _world);") >= 2, (
        "the talk case has no path that walks on when it cannot open, so a bad npc would freeze the scene")
    assert '_sc.state = "talk";' in talk_case, "the talk case does not hand the box to the step"
    persona = read_text(PERSONA_GML)
    abandon = gml_function(persona, "pp_talk_scene_abandon")
    assert "_state.finished = true;" in abandon, "cancel does not close the exchange, so Esc cannot leave it"
    assert "pp_talk_live_close(_state);" in abandon, "cancel does not put the text field down"


def test_the_self_test_plays_it_without_a_keyboard():
    body = gml_function(read_text(PERSONA_GML), "pp_talk_scene_autoplay")
    assert "PP_TALK_SCENE_SELFTEST_LINE" in body, "the autoplay says no line, so the self test would sit in the box"
    assert "pp_talk_scene_submit(_state);" in body, "the autoplay never sends"
    assert "_state.finished = true;" in body, "the autoplay never closes the answer"
    runner = gml_function(read_text(SCENE_GML), "pp_scene_step")
    assert "pp_talk_scene_autoplay(_sc.talk);" in runner, "the step does not route the self test to the autoplay"


def test_the_overworld_draw_calls_the_scenes_overlay():
    body = read_text(APP_GML)
    assert "pp_scene_draw_overlay(global.pp.world);" in body, (
        "the overworld draw never draws the scene's box, so the exchange renders nowhere")
    overlay = gml_function(read_text(SCENE_GML), "pp_scene_draw_overlay")
    assert "pp_talk_scene_draw(_sc.talk);" in overlay, "the overlay does not draw the exchange"


def test_the_take_says_the_line_with_keys_the_recorder_can_send():
    """The exchange is only on screen if the tape can press it: letters, the send, and a press to close."""
    script = load(SCRIPT)
    events = script["events"]
    office = [event for event in events if event.get("beat") == 22]
    assert office, "beat 22 carries no events"
    keys = [event.get("key") for event in office if event.get("kind") == "key"]
    assert "enter" in keys, "the take never sends a line"
    letters = [key for key in keys if isinstance(key, str) and len(key) == 1 and key.isalpha()]
    assert len(letters) >= 3, "the take types %r, which is not a line" % (letters,)
    # The send has to come after the letters and before the closes, or the box is still in its typing stage.
    steps = [(event["step"], event.get("key")) for event in office if event.get("kind") == "key"]
    send_at = [step for step, key in steps if key == "enter"]
    last_letter_at = max(step for step, key in steps if isinstance(key, str) and len(key) == 1 and key.isalpha())
    assert last_letter_at < send_at[0], "the take sends before the name is typed"
    capture = read_text(CAPTURE)
    table = capture[capture.find("KEY_CODES = {"):]
    table = table[:table.find("}\n") + 2]
    for key in set(keys):
        if key in ("enter", "confirm", "cancel", "up", "down", "left", "right", "escape", "space"):
            continue
        assert '"%s"' % key in table or "KEY_CODES[_letter]" in capture, (
            "the recorder cannot send %r, so the take would type nothing" % key)
    assert "KEY_CODES[_letter] = ord(_letter.upper())" in capture, (
        "the recorder's letter row is gone, so a typed line cannot be recorded")


def test_the_recorder_reads_letters_as_the_game_reads_them():
    """A letter key is the VK of the upper case letter; pp_input reads the case from the shift key, not the VK."""
    capture = read_text(CAPTURE)
    assert 'for _letter in "abcdefghijklmnopqrstuvwxyz":' in capture, "the letter row was removed"
    assert "KEY_CODES[_letter] = ord(_letter.upper())" in capture, (
        "the letter key is not the upper case VK, so SendInput would post a key the game does not read")


def test_the_recorded_turns_the_box_reads_exist_and_are_drawable():
    rows = [row for row in load(BAKE)["rows"] if row.get("id", "").startswith("npc/%s/" % NPC)]
    assert len(rows) >= 1, "the bake carries no turn for %r, so the beat would open on nothing" % NPC
    for row in rows:
        assert row.get("scene") == "npc", "%s is not an npc row" % row["id"]
        assert isinstance(row.get("text"), list) and row["text"], "%s has no reply rows" % row["id"]
        assert len(row["text"]) <= 2, "%s carries more rows than the box draws" % row["id"]
        for line in row["text"]:
            assert len(line) <= 28, "%s has a line longer than the box: %r" % (row["id"], line)
        effect = row.get("effect")
        assert effect in ("none", "soften", "nudge", "setback", "end"), (
            "%s carries an effect the verdict map does not know: %r" % (row["id"], effect))
        assert row.get("hint"), "%s carries no hint, so the model's guidance has nothing to draw" % row["id"]


def test_the_new_files_hold_no_long_dash():
    for path in (SCENES, PERSONA_GML, SCENE_GML, LIVE_GML, APP_GML, CAPTURE, SCRIPT):
        text = read_text(path)
        for mark in ("\u2014", "\u2013"):
            assert mark not in text, "%s carries a long dash" % os.path.basename(path)
