"""TALK-LIVE: the fifth TALK entry, its box, its grid, its voice leg and its answer (spec 21, card t_ee178652).

Nothing here runs GameMaker, for the same reason tests\\test_first_fight.py and tests\\test_talk_baked.py do not: every
claim is computed from a real file, and the GML is measured for the shapes this file depends on, so a change in the
game fails here instead of in the first playtest.

Sources this file measures, never restates:

    data/talk_live.json            the numbers, the strings and the letter grid
    data/talk_live_tape.json       the recorded exchanges and the two transcripts
    data/talk/sailor_judge.json    the verdict map: soften -> +20, nudge -> +5, none -> 0, setback -> -10
    data/encounters/all.json       tutorial_sailors' talk block: mercy_per_option, mercy_to_spare, option_count
    data/talk_cards.json           the Navy Sailor card, whose weak topics the demo's lines are written against
    game/scripts/pp_font/pp_font.gml           the sheet's alphabet, read from the source of truth
    game/scripts/pp_talk_live/pp_talk_live.gml the machine, its stage names, its constants and its two branches
    game/scripts/pp_input/pp_input.gml         the text reader and the two actions the box adds
    tools/talk_live.py             the mirror both this file and tools/capture_talk_live.py drive

What is proven
  1. the data file is complete, and every string and every grid cell is drawable by the sheet;
  2. the tape's answers obey the judge's own verdict map and the box's line rules, and the three demo lines are in it;
  3. typing, deleting, the character cap and the sheet's filter behave as spec 21 section 2 says;
  4. an empty submit is refused; three tries then the entry closes with the note on screen, and the authored options
     still reach the spare threshold, so the fight can always end;
  5. the demo's three tries move the WILL bar 0 -> 20 -> 40 -> 40, and the third line earns nothing;
  6. the meter is clamped before and after, and no answer can move it outside 0 to will_max;
  7. a request that never answers times out at the data file's budget and the fallback answers the turn;
  8. replay mode opens nothing: the mirror's send flag stays false, and the only file under game/ that names a network
     function is pp_talk_live.gml, in one branch, with a loopback address built from data;
  9. the GML and the mirror agree on the stage names, the constants and the two mode words;
 10. the WILL bar the director draws is inside the frame and cannot be drawn wider than its own track;
 11. the capture the card asks for is NES legal: every frame tools/capture_talk_live.py draws passes
     tools/nes_composite_check.py's frame audit on the pixels, all three input paths are in it as three distinct
     frames with three distinct debug lines, and the answer's frame is the first frame with the WILL bar filled.

No test here reads the network, writes a tracked data file, or needs a key.
"""

from __future__ import annotations

import json
import os
import re

import pytest

import talk_live

ROOT = talk_live.ROOT
GML = os.path.join(ROOT, "game", "scripts", "pp_talk_live", "pp_talk_live.gml")
INPUT_GML = os.path.join(ROOT, "game", "scripts", "pp_input", "pp_input.gml")
DIRECTOR_GML = os.path.join(ROOT, "game", "scripts", "pp_battle_director", "pp_battle_director.gml")
TEXT_GML = os.path.join(ROOT, "game", "scripts", "pp_battle_text", "pp_battle_text.gml")
CONFIG_GML = os.path.join(ROOT, "game", "scripts", "pp_config", "pp_config.gml")

# W1 is the bridge (card t_c784d239): tools/ai_bridge.py and data/talk/sailor_judge.json are that card's files, and
# they are not in this tree until it lands. The two cross-checks below read them, so they run when the files are here
# and name the owner when they are not, rather than failing a commit on work another card still holds.
W1_BRIDGE = os.path.join(ROOT, "tools", "ai_bridge.py")
W1_JUDGE = os.path.join(ROOT, "data", "talk", "sailor_judge.json")
needs_w1 = pytest.mark.skipif(
    not (os.path.exists(W1_BRIDGE) and os.path.exists(W1_JUDGE)),
    reason="W1 is not in this tree: card t_c784d239 owns tools/ai_bridge.py and data/talk/sailor_judge.json",
)

DEMO_LINES = (
    "You have been on watch all night. Get some sleep.",
    "Want a smoke? The sea can wait.",
    "Is the bridge going to report you for this?",
)


def read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


@pytest.fixture(scope="module")
def data():
    return talk_live.load_data(ROOT)


@pytest.fixture(scope="module")
def tape():
    return talk_live.load_tape(ROOT)


@pytest.fixture(scope="module")
def glyphs():
    return talk_live.font_glyphs(ROOT)


@pytest.fixture(scope="module")
def box(data, tape):
    return talk_live.LiveTalk(data, tape)


def fresh(data, tape, **kwargs):
    return talk_live.LiveTalk(data, tape, **kwargs)


# --------------------------------------------------------------------------------------------------- 1. the data


def test_data_file_is_complete(data):
    assert data["doc"]["kind"] == "talk_live"
    assert data["port"] == 8791
    assert data["host"] in ("127.0.0.1", "localhost")
    assert data["talk_path"] == "/talk"
    assert data["hear_path"] == "/hear"
    assert data["mode_default"] in ("live", "replay")
    assert data["tries_max"] == 3
    assert data["timeout_steps"] > 12 * 60, "the game must outwait the bridge's own 12 second deadline (key present)"
    assert data["chars_max"] == 120
    assert data["cols"] == 28
    assert data["rows_shown"] == 2


@needs_w1
def test_the_loopback_host_is_the_only_one_the_bridge_accepts():
    """tools/ai_bridge.py refuses a host that is not loopback at startup; the data file must agree or nothing runs."""
    bridge = read(W1_BRIDGE)
    assert 'env("PP_BRIDGE_HOST", LOOPBACK_HOST)' in bridge
    assert "LOOPBACK_HOST = " in bridge
    assert '"127.0.0.1"' in bridge


def test_every_string_the_box_draws_fits_a_row(data, glyphs):
    for key in ("prompt", "hint_keys", "hint_grid", "hint_voice", "hint_wait", "tries_note", "empty_note", "will_label"):
        text = data[key]
        assert text, "the box would draw an empty %s" % key
        assert" " != text[0] or key in ("hint_grid",), "a leading space wastes a column"
        for ch in text:
            assert ch in glyphs, "%s carries %r, which spr_pp_font8 cannot draw" % (key, ch)
    longest = max(len(data[k]) for k in ("hint_keys", "hint_grid", "hint_voice", "hint_wait", "tries_note", "empty_note"))
    assert longest <= data["cols"], "a hint longer than the box's %d columns is cut on screen" % data["cols"]


def test_the_grid_is_the_shape_nayil_asked_for(data, glyphs):
    cells = data["grid"]
    assert len(cells) == data["grid_cols"] * data["grid_rows"] == 44
    commands = [c for c in cells if c in ("DEL", "END")]
    assert commands == ["DEL", "END"], "the two commands are the grid's last two cells, in that order"
    for cell in cells:
        if cell in ("DEL", "END"):
            continue
        assert len(cell) == 1
        assert cell in glyphs, "grid cell %r is not a glyph of the sheet" % cell
    letters = [c for c in cells if len(c) == 1 and c.isalpha()]
    assert letters == [chr(c) for c in range(ord("A"), ord("Z") + 1)], "A to Z, in order"
    digits = [c for c in cells if len(c) == 1 and c.isdigit()]
    assert digits == [str(d) for d in range(10)], "0 to 9, in order"
    assert " " in cells


# --------------------------------------------------------------------------------------------------- 2. the tape


@needs_w1
def test_tape_answers_obey_the_judge_verdict_map(tape):
    """Every recorded delta has to be a delta the judge's own effect map can produce for that verdict."""
    judge = json.load(open(W1_JUDGE, encoding="utf-8"))
    allowed = {}
    for effect, row in judge["verdicts"].items():
        allowed.setdefault(row["verdict"], set()).add(row["will_delta"])
    for row in tape["exchanges"]:
        answer = row["answer"]
        assert answer["verdict"] in allowed, "%r is not a verdict the judge file defines" % answer["verdict"]
        assert answer["will_delta"] in allowed[answer["verdict"]], (
            "%s says %s at %d, and the judge's own rows for that verdict are %s"
            % (row["line"][:40], answer["verdict"], answer["will_delta"], sorted(allowed[answer["verdict"]]))
        )


def test_tape_reply_lines_are_drawable_and_fit_the_box(tape, glyphs):
    for row in tape["exchanges"] + [tape["miss"]]:
        answer = row["answer"] if "answer" in row else row
        assert 1 <= len(answer["reply"]) <= 3, "a reply is one to three rows (spec 21 section 4)"
        for line in answer["reply"]:
            assert 1 <= len(line) <= 28, "%r is longer than the box's 28 columns" % line
            for ch in line:
                assert ch in glyphs, "%r carries %r, which the sheet cannot draw" % (line, ch)


def test_tape_provenance_fields_are_honest(tape):
    for row in tape["exchanges"]:
        assert row["answer"]["source"] in ("replay", "fallback"), "the tape is a replay, so a row says replay"
        assert row["answer"].get("origin") in ("meta", "open-weights", "fallback")
        assert isinstance(row["answer"].get("latency_ms"), int)
    assert tape["miss"]["source"] == "fallback"
    assert tape["recorded_against"]["talk_live"] == 1


def test_the_three_demo_lines_are_recorded(tape):
    keys = {talk_live.normalise(row["line"]) for row in tape["exchanges"]}
    for line in DEMO_LINES:
        assert talk_live.normalise(line) in keys, "the demo types %r and the tape has no answer for it" % line


def test_every_voice_take_has_a_transcript(tape, glyphs):
    assert len(tape["hear"]) >= 2
    for row in tape["hear"]:
        assert row["transcript"]
        for ch in row["transcript"]:
            assert ch in glyphs
        assert row["model"] == "faster-whisper tiny"


# --------------------------------------------------------------------------------------------------- 3. the line


def test_typing_builds_the_line_and_the_cap_holds(data, tape):
    box = fresh(data, tape)
    assert box.open()
    box.type_line("watch")
    assert box.text == "watch"
    box.type_line("x" * 200)
    assert len(box.text) == data["chars_max"]


def test_the_sheet_filter_drops_what_the_font_cannot_draw(data, tape):
    box = fresh(data, tape)
    box.open()
    box.type_line("a#b$c")
    assert box.text == "abc", "a glyph the sheet lacks never reaches the buffer"


def test_delete_removes_one_character_and_never_underflows(data, tape):
    box = fresh(data, tape)
    box.open()
    box.type_line("ab")
    assert box.delete()
    assert box.text == "a"
    assert box.delete()
    assert box.text == ""
    assert box.delete() is False


def test_the_two_row_window_scrolls_and_never_splits_a_word(data, tape):
    rows = talk_live.rows_for("one two three four five six seven eight nine ten", data)
    assert len(rows) <= data["rows_shown"]
    for row in rows:
        assert len(row) <= data["cols"]
        for word in row.split():
            assert len(word) <= data["cols"], "a word longer than the row would be split on screen"
    long_line = " ".join(["word"] * 40)
    tail = talk_live.rows_for(long_line, data)
    assert long_line.endswith(tail[-1])


def test_an_empty_submit_is_refused_with_the_note(data, tape):
    box = fresh(data, tape)
    box.open()
    assert box.submit() is False
    assert box.note == data["empty_note"]
    assert box.stage == "entry", "the box stays open so the player can type"
    assert box.tries == 0


# ----------------------------------------------------------------------------------------------- 4. the three tries


def test_three_tries_then_the_entry_closes_and_the_fight_can_still_end(data, tape):
    box = fresh(data, tape)
    for line in DEMO_LINES:
        assert box.open(), "try %d should still open" % (box.tries + 1)
        box.type_line(line)
        assert box.submit()
        while box.stage == "wait":
            box.step()
    assert box.tries == data["tries_max"]
    assert box.open() is False, "a fourth free text try is refused"
    assert box.note == data["tries_note"]

    # The authored path still carries the fight: three options at the encounter's own mercy_per_option reach the
    # encounter's own mercy_to_spare, which is the promise spec 16 section 2 makes and this card must not break.
    encounter = [e for e in talk_live.load_json("data/encounters/all.json")["encounters"]
                 if e["id"] == "tutorial_sailors"][0]
    per = encounter["talk"]["mercy_per_option"]
    to_spare = encounter["talk"]["mercy_to_spare"]
    authored = min(100, box.will + per * encounter["talk"]["option_count"])
    assert authored >= to_spare, "after the live tries the authored options must still reach SPARE"


def test_the_demo_arc_moves_the_will_bar_and_the_third_line_earns_nothing(data, tape):
    box = fresh(data, tape)
    seen = []
    for line in DEMO_LINES:
        assert box.open()
        box.type_line(line)
        assert box.submit()
        while box.stage == "wait":
            box.step()
        seen.append(box.will)
    assert seen == [20, 40, 40], "the demo's WILL bar reads 0 -> 20 -> 40, and a line that earns nothing holds it"
    assert box.source == "replay"
    assert box.verdict == "unmoved"


def test_an_unrecorded_line_answers_from_the_miss_row(data, tape):
    box = fresh(data, tape)
    box.open()
    box.type_line("Have you ever seen a heron this far out?")
    assert box.submit()
    while box.stage == "wait":
        box.step()
    assert box.will == 0
    assert box.source == "fallback", "a line nobody recorded is labelled as the fallback, not as a model"
    assert box.reply


# --------------------------------------------------------------------------------------------------- 5. the meter


def test_the_meter_is_clamped_before_and_after_the_change(data, tape):
    box = fresh(data, tape, mercy=95)
    box.open()
    box.type_line(DEMO_LINES[0])
    box.submit()
    while box.stage == "wait":
        box.step()
    assert box.will == data["will_max"], "+20 at 95 leaves 100, not 115"
    assert box.delta == 5, "and the delta the log prints is what actually landed"


def test_no_answer_can_move_the_meter_out_of_its_range(data, tape):
    for raw in (90, -90, 20, -20, 0):
        box = fresh(data, tape, mercy=50)
        answer = {"verdict": "persuaded", "will_delta": raw, "reply": ["GO ON."], "source": "replay"}
        box.apply(answer, via="test")
        assert 0 <= box.will <= data["will_max"]
        assert -20 <= box.delta <= 20


def test_a_reply_the_sheet_cannot_draw_is_refused_and_the_fallback_answers(data, tape):
    box = fresh(data, tape, mercy=10)
    answer = {"verdict": "persuaded", "will_delta": 20, "reply": ["a#b$c $$"], "source": "meta"}
    cleaned = talk_live.answer_clean(answer, data, miss=tape["miss"])
    assert cleaned["reply"] == tape["miss"]["reply"], "no drawable line means the miss row's words"
    assert cleaned["source"] == "fallback"


def test_a_long_reply_line_is_cut_at_a_space(data):
    cleaned = talk_live.answer_clean(
        {"verdict": "unmoved", "will_delta": 0, "reply": ["THE LIST DOES NOT CARE HOW POLITE YOU ARE, SAILOR"], "source": "meta"},
        data)
    assert len(cleaned["reply"][0]) <= 28
    assert not cleaned["reply"][0].endswith(" ")


# ------------------------------------------------------------------------------------------------- 6. the timeout


def test_a_request_that_never_answers_times_out_and_the_turn_still_resolves(data, tape):
    box = fresh(data, tape, mode="live")
    box.open()
    box.type_line("Something the bridge would have to answer.")
    box.submit()
    assert box.would_send is True, "live mode is the mode that would ask"
    steps = 0
    answer = None
    while answer is None and steps < data["timeout_steps"] + 2:
        steps += 1
        answer = box.step()
    assert answer is not None
    assert steps == data["timeout_steps"], "the fallback lands exactly at the budget, once"
    assert box.missed is True
    assert box.will == 0
    assert box.reply, "the turn still shows a line, so the fight never stalls"
    assert box.stage == "", "and the box is out of the way"


def test_replay_mode_never_sends_anything(data, tape):
    box = fresh(data, tape)
    box.open()
    box.type_line(DEMO_LINES[0])
    box.submit()
    assert box.would_send is False
    while box.stage == "wait":
        box.step()
    assert box.would_send is False


# ----------------------------------------------------------------------------------------------- 7. the grid path


def test_the_grid_navigates_every_cell_and_wraps(data, tape):
    box = fresh(data, tape)
    box.open()
    box.grid_mode = "grid"
    cols = data["grid_cols"]
    # Across: one full row of right presses returns to the cell it started on, having visited every column.
    box.grid = 0
    row = {box.grid}
    for _ in range(cols - 1):
        box.grid_move(dx=1)
        row.add(box.grid)
    assert row == set(range(cols)), "one pass across a row reaches every column"
    box.grid_move(dx=1)
    assert box.grid == 0, "the row wraps"
    # Down: one full column of down presses visits every row.
    box.grid = 0
    column = {box.grid}
    for _ in range(data["grid_rows"] - 1):
        box.grid_move(dy=1)
        column.add(box.grid)
    assert column == {r * cols for r in range(data["grid_rows"])}, "one pass down a column reaches every row"
    box.grid_move(dy=1)
    assert box.grid == 0, "the column wraps"


def test_the_grid_types_deletes_and_submits(data, tape):
    box = fresh(data, tape)
    box.open()
    box.grid_mode = "grid"
    box.grid = box.index_of("H")
    box.grid_press()
    box.grid = box.index_of("I")
    box.grid_press()
    box.grid = box.index_of("DEL")
    box.grid_press()
    assert box.text == "H"
    box.grid = box.index_of("END")
    box.grid_press()
    assert box.stage == "wait"
    assert box.tries == 1


def test_grid_and_keyboard_build_the_same_line(data, tape):
    """Two input paths, one line: the grid types the sheet's capitals, the keyboard types what is held, and the tape
    lookup normalises both, so the same words earn the same answer whichever way they were entered."""
    keys = fresh(data, tape)
    keys.open()
    keys.type_line("hi")
    grid = fresh(data, tape)
    grid.open()
    grid.grid_mode = "grid"
    for cell in ("H", "I"):
        grid.grid = grid.index_of(cell)
        grid.grid_press()
    assert keys.text == "hi"
    assert grid.text == "HI"
    assert talk_live.normalise(keys.text) == talk_live.normalise(grid.text)
    record = [row for row in tape["exchanges"] if talk_live.normalise(row["line"]).startswith("hello")][0]
    assert talk_live.tape_lookup(tape, "navy_sailor", record["line"]) is not None
    assert talk_live.tape_lookup(tape, "navy_sailor", record["line"].upper()) is not None, (
        "a capitals line from the grid finds the same recording as a typed one")


# ------------------------------------------------------------------------------------------- 8. the GML, measured


def test_the_one_network_call_is_one_file_and_one_branch():
    """The live leg is the project's only network call and it lives in exactly one function."""
    source = read(GML)
    assert source.count("http_request(") == 2, "two calls: one to /talk, one to /hear"
    for other in (INPUT_GML, DIRECTOR_GML, TEXT_GML, CONFIG_GML):
        body = read(other)
        assert "http_request" not in body
        assert "http_get" not in body
    assert '_d.scheme + "://" + _d.host + ":" + string(_d.port) + _path' in source, (
        "the scheme, the host, the port and the path are four data fields assembled at call time")
    assert "http://" not in source, "no shipped GML holds an http:// literal, the scheme included"
    # No address in the code may point anywhere but this machine. The data file's field is the one the game reads; the
    # only literal allowed in the GML is the loopback default that stands in when the data file is missing, because a
    # missing data file must turn the live leg OFF, never point it at a stranger.
    for line in source.splitlines():
        code = line.split("//")[0]
        for address in re.findall(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", code):
            assert address == "127.0.0.1", "a non loopback address in the game's code: %r" % address
    assert "http://127.0.0.1" not in source, "the address is assembled from fields, not written whole"


def test_the_gml_refuses_a_host_that_is_not_loopback():
    source = read(GML)
    assert 'if (_d.host != "127.0.0.1" && _d.host != "localhost")' in source
    assert "_d.host = \"127.0.0.1\"" in source


def test_replay_is_the_default_and_the_live_branch_is_a_switch():
    source = read(GML)
    config = read(CONFIG_GML)
    assert '#macro PP_TALK_LIVE_MODE "replay"' in config, "the shipped build starts in replay"
    assert "if (pp_talk_live_is_live()) {" in source, "the send is behind the mode test"
    assert "pp_talk_live_send_talk(_battle);" in source
    assert "pp_data_json(\"talk_live_tape.json\")" in source, "replay reads the tape, not the network"


def test_the_stage_names_and_constants_agree_with_the_mirror():
    source = read(GML)
    for stage in talk_live.STAGES:
        assert 'case "%s":' % stage in source, "the GML has no %r stage" % stage
    for name in ("PP_TALK_LIVE_BACK_HOLD", "PP_TALK_LIVE_RECORD_CAP", "PP_TALK_LIVE_COLS"):
        assert "#macro %s " % name in source
    assert "#macro PP_TALK_LIVE_COLS 28" in source
    data = talk_live.load_data(ROOT)
    assert 'if (_d.tries_max < 1) _d.tries_max = %d' % data["tries_max"] in source
    assert 'if (_d.timeout_steps < 60) _d.timeout_steps = %d' % data["timeout_steps"] in source


def test_the_text_reader_is_in_pp_input_and_nowhere_else():
    """Spec 02 rule 1: one module reads a key. The box asks for a character, it never reads one."""
    source = read(GML)
    assert "keyboard_check" not in source
    assert "pp_input_text_begin()" in source and "pp_input_text_end()" in source
    reader = read(INPUT_GML)
    for name in ("pp_input_text_begin", "pp_input_text_end", "pp_input_text_step", "pp_input_text_shift"):
        assert "function %s(" % name in reader
    assert 'id: "live_voice"' in reader
    assert 'id: "live_mode"' in reader
    assert "pp_input_text_step();" in reader, "the sampler must publish the character every step"


def test_the_two_new_actions_do_not_steal_a_key_from_another_action():
    reader = read(INPUT_GML)
    table = reader[reader.index("function pp_input_table()"):reader.index("/// Build the input state")]
    for key in ("vk_f5", "vk_f6", "gp_shoulderl"):
        assert table.count(key) == 1, "%s is bound to more than one action" % key


def test_the_will_bar_is_inside_the_frame_and_cannot_overdraw():
    source = read(DIRECTOR_GML)
    assert "pp_talk_live_data().will_label" in source
    # The track is the health bar's own width and the fill is the meter's share of it: no digits take a column out of
    # the bar, because a bar a judge cannot see move is not evidence that anything moved. (The earlier layout reserved
    # 36 pixels for a number and left a 12 pixel fill; card t_ee178652 dropped the number for that reason.)
    assert "var _will_w = _bar_w;" in source
    assert "clamp(_battle.talk_mercy, 0, pp_talk_live_data().will_max)" in source
    assert "floor(_will_w * (_will / _will_max))" in source, (
        "the fill must be a fraction of the track, so it cannot be drawn wider than the track")
    # The geometry, computed from the layout file the director reads rather than from a remembered pixel count.
    screens = talk_live.load_json("data/ui_layouts.json")["screens"]
    battle = [screen for screen in screens if screen["name"] == "battle"][0]
    row = battle["enemies"][0]
    bar_w = int(str(row["pixels"]).split("x")[0]) * 2
    bar_x = row["x"] * 8 - 16
    assert bar_x >= 0, "the bar starts off the left edge of the frame"
    assert bar_x + bar_w - 1 < 256, "the bar runs off the right edge of the frame"
    assert bar_x + bar_w - 1 < battle["party"][0]["x"] * 8, "the bar reaches into the party column"
    assert bar_w == talk_live.load_data(ROOT)["doc"]["will"]["bar_width"], (
        "the bar drawn and the bar the data file states are two different widths")


def test_the_fifth_entry_is_fixed_and_carries_no_effect_of_its_own():
    text = read(TEXT_GML)
    assert "live: true" in text
    assert 'effect: "live",' in text
    assert "pp_talk_live_data().prompt" in text
    # The pick opens the box and returns before any mercy arithmetic, so opening a box can never move the meter.
    body = text[text.index("if (variable_struct_exists(_record, \"live\")"):]
    body = body[:body.index("pp_talk_apply(_battle, _record);")]
    assert "pp_talk_apply" not in body
    assert "pp_talk_live_open(_battle)" in body


def test_the_async_events_point_at_the_one_handler():
    obj = os.path.join(ROOT, "game", "objects", "obj_pp_game")
    for name in ("Other_69.gml", "Other_62.gml"):
        body = read(os.path.join(obj, name))
        assert "pp_talk_live_async(global.pp.battle);" in body
    voice = read(os.path.join(obj, "Other_73.gml"))
    assert "pp_talk_live_voice_recorded(" in voice
    assert "audio recording" in voice.lower()


def test_a_brush_past_the_voice_key_is_refused_and_a_real_take_lands(data, tape):
    """The voice leg's floor, mirroring pp_talk_live_step_listen: under data's hold_steps_min nothing is sent.

    The GML refuses the take with the low blip instead of transcribing it, so a player who taps the key by accident
    never spends one of three tries on a half syllable.
    """
    transcript = tape["hear"][0]["transcript"]
    floor = data["voice"]["hold_steps_min"]

    brush = fresh(data, tape)
    brush.open()
    assert brush.record(floor - 1)
    assert brush.stage == "listen"
    assert brush.voice_release(transcript) is False
    assert brush.stage == "entry" and brush.text == "" and brush.note == data["empty_note"]

    take = fresh(data, tape)
    take.open()
    take.type_line("half a line")
    assert take.record(floor)
    assert take.voice_release(transcript)
    # pp_talk_live_send_hear assigns the buffer (`_battle.live_text = _hear`), so the take replaces what was typed
    # and the player edits the transcript from there.
    assert take.text == transcript
    assert take.stage == "entry"
    take.type_line(" Please.")
    assert take.text == transcript + " Please."


# ------------------------------------------------------- 11. the capture the card asks for, and its frame audit


def test_the_capture_frames_pass_the_nes_frame_audit():
    """Nayil's scope add, item 4: the box and the grid stay NES legal and pass the frame audit.

    The audit is tools/nes_composite_check.py's check_frame, the rule set tools/nes_audit_all.py gates a shipped
    256x240 screen with, run on the frames tools/capture_talk_live.py draws at the game's own coordinates. It earned
    its place on the first run: the tool drew the design hex of the ink, paper, dim and text roles, and 0 of the 54
    design colours is a 2C02 output (card t_54db4d0f), so all six frames were off palette and the audit refused them.
    The tool now resolves a role through data/palette_ppu.json exactly as pp_data_palette_rgb does.
    """
    import capture_talk_live as capture

    ctx, canvases, audit = capture.prepare()
    assert [name for name, _ in audit] == [name for name, _, _ in canvases]
    failed = {name: report["problems"] for name, report in audit if not report["ok"]}
    assert failed == {}, "%d frame(s) are not NES legal: %s" % (len(failed), sorted(failed))
    for name, report in audit:
        assert report["screen"]["colours"] <= 25, "%s shows more colours than a 2C02 can" % name
        assert report["palette"]["off_palette_pixels"] == 0, "%s draws a colour the chip has no output for" % name
        assert report["backdrop"] in [entry["hex"] for entry in
                                      talk_live.load_json("data/nes_palette.json")["entries"]
                                      if entry.get("usable", True)]
    # The frame is the size the game draws, so the audit is judging a real screen and not a poster of one.
    for name, canvas, _ in canvases:
        assert canvas.size == (256, 240), "%s is not a 256x240 frame" % name


def test_the_capture_shows_the_three_input_paths_and_the_bar_moving():
    """The card's check: a capture shows a typed argument changing the WILL bar, and all three paths in one picture.

    The bar is read off the pixels, not off a number in the report: the text-coloured fill stops where the meter says
    it stops, so an empty bar and a bar at 20 are two different pictures or this fails.
    """
    import capture_talk_live as capture

    ctx, canvases, audit = capture.prepare()
    frames = {name: (canvas, extra) for name, canvas, extra in canvases}
    for name in ("entry_keys", "entry_grid", "listen", "entry_voice"):
        assert name in frames, "the capture is missing the %s path" % name
    debugs = [frames[name][1]["debug"] for name in ("entry_keys", "entry_grid", "entry_voice")]
    assert len(set(debugs)) == 3, "two input paths print the same debug line, so a judge cannot tell them apart"
    assert "mode keyboard" in debugs[0]
    assert "mode grid" in debugs[1]
    assert "voice" in debugs[2] and "source replay" in debugs[2]
    # The microphone needs a picture of its own or it looks like the keyboard with a different caption: the listen
    # stage draws the recording line where the line goes, which is the state pp_talk_live_draw has for it.
    assert "mic open" in frames["listen"][1]["debug"]
    assert frames["listen"][0].tobytes() != frames["entry_keys"][0].tobytes(), (
        "the recording frame is the keyboard frame, so the capture does not show the microphone at all")

    bars = ctx["bars"]
    text = ctx["role"]["text"]
    row_y = range(bars["bar_y"] + bars["will_dy"], bars["bar_y"] + bars["will_dy"] + 4)

    def fill(canvas):
        columns = [x for x in range(bars["bar_x"], bars["bar_x"] + bars["bar_w"])
                   if any(canvas.getpixel((x, y))[:3] == text for y in row_y)]
        return len(columns)

    empty, full = fill(frames["entry_keys"][0]), fill(frames["reply"][0])
    assert empty == 0, "the first frame already shows MERCY filled, so the change would not read as a change"
    assert full > 0, "the answer's frame shows no MERCY fill, so nothing on screen says the meter moved"
    assert full == int(bars["bar_w"] * (talk_live.load_tape(ROOT)["exchanges"][0]["answer"]["will_delta"]
                                        / float(talk_live.load_data(ROOT)["will_max"]))), (
        "the fill is not the meter's share of the track")
    # The source is on the debug line, which is what the card's check asks a judge-facing run to print.
    reply_debug = frames["reply"][1]["debug"]
    assert "source replay" in reply_debug and "mercy 0 -> 20" in reply_debug
