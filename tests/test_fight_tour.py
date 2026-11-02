"""Fight tour door (card BATTLE-PROOF, 2026-11-02).

What is pinned, at source level (no GameMaker window is opened by this file):
  - The PP_FIGHT_TOUR door is inert when the variable is unset: the flag is read once through the macro, turned on only by a
    non-empty value, and every entry point (think, held, shot) leaves on its first statement when the flag is off. The two
    hooks outside pp_overworld.gml (pp_input_sample and pp_app_draw) are single calls to those entry points.
  - The tour starts a fight through pp_overworld_start_encounter (the map trigger's entry) and no battle file knows the door.
  - The driver's log parser reads the exact line shapes the GML writes, and the driver has no force flag.
Honest limit: that the fights really finish is proved by the real run in output\\battle_proof_2026-11-02\\REPORT.md, not here.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import fight_tour  # noqa: E402


def _text(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as handle:
        return handle.read()


def _function(text, name):
    found = re.search(r"function " + re.escape(name) + r"\(", text)
    assert found, name
    start = text.index("{", found.end())
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise AssertionError("unbalanced " + name)


OVERWORLD = _text("game", "scripts", "pp_overworld", "pp_overworld.gml")


def test_the_door_is_read_once_through_the_macro_and_defaults_off():
    assert '#macro PP_FIGHT_TOUR "PP_" + "FIGHT_TOUR"' in OVERWORLD
    body = _function(OVERWORLD, "pp_fight_tour_on")
    assert body.count("environment_get_variable(PP_FIGHT_TOUR)") == 1
    assert 'global.pp_ft_on = (_v != "")' in body
    assert "if (!variable_global_exists(\"pp_ft_on\"))" in body
    assert "return global.pp_ft_on;" in body


def test_every_entry_point_leaves_first_when_the_door_is_closed():
    for name, closed in (("pp_fight_tour_think", "return;"), ("pp_fight_tour_shot", "return;"), ("pp_fight_tour_held", "return false;")):
        body = _function(OVERWORLD, name)
        first = [line.strip() for line in body.splitlines() if line.strip() and line.strip() != "{"][0]
        assert first == "if (!pp_fight_tour_on()) " + closed, (name, first)


def test_the_two_hooks_are_single_calls_and_nothing_else_reads_the_door():
    sample = _function(_text("game", "scripts", "pp_input", "pp_input.gml"), "pp_input_sample")
    assert sample.count("pp_fight_tour_think();") == 1
    assert sample.count("if (!_down && pp_fight_tour_held(_keys[i])) _down = true;") == 1
    draw = _function(_text("game", "scripts", "pp_app", "pp_app.gml"), "pp_app_draw")
    assert draw.count("pp_fight_tour_shot();") == 1
    for rel in (("pp_battle_director", "pp_battle_director.gml"), ("pp_battle_commands", "pp_battle_commands.gml"),
                ("pp_battle_text", "pp_battle_text.gml"), ("pp_dodge_arena", "pp_dodge_arena.gml")):
        assert "pp_fight_tour" not in _text("game", "scripts", *rel), rel
    assert "PP_FIGHT_TOUR" not in _text("data", "encounters", "all.json")


def test_the_tour_starts_fights_through_the_trigger_entry_and_spares_by_talk_then_spare():
    think = _function(OVERWORLD, "pp_fight_tour_think")
    assert "pp_overworld_start_encounter(_w, _job.id);" in think
    assert "pp_command_state(_b, PPCommand.spare).enabled" in think
    assert "PPCommand.talk" in think and "PPCommand.power" in think
    for path in ('"spare"', '"kill"'):
        assert path in _function(OVERWORLD, "pp_fight_tour_on")
    result = _function(OVERWORLD, "pp_fight_tour_result")
    assert '" path=" + _job.path + " result=" + _result + " turns="' in result


SAMPLE_LOG = """\
PP: muted, PP_MUTE=1
PP fight tour: begin, map ship_small, jobs 2
PP fight tour: tutorial_sailors spare state=start
PP fight tour: tutorial_sailors spare state=menu turn=0 enemy_hp=30 party_hp=20 trust=0
PP fight tour: shot pp_fight_tutorial_sailors_spare_menu.png
PP fight tour: tutorial_sailors path=spare result=spared turns=4
PP fight tour: tutorial_sailors path=kill result=lost turns=9
PP fight tour: percy path=kill result=stuck turns=-1
PP fight tour: percy kill state=stalled in menu turn=2 enemy_hp=40 party_hp=12 trust=0
PP fight tour: done, jobs 2
"""


def test_the_driver_parser_reads_the_game_line_format():
    parsed = fight_tour.parse_fight_log(SAMPLE_LOG)
    assert parsed["runs"] == [
        {"id": "tutorial_sailors", "path": "spare", "result": "spared", "turns": 4},
        {"id": "tutorial_sailors", "path": "kill", "result": "lost", "turns": 9},
        {"id": "percy", "path": "kill", "result": "stuck", "turns": -1},
    ]
    assert parsed["states"][0] == {"id": "tutorial_sailors", "path": "spare", "state": "start"}
    assert parsed["shots"] == ["pp_fight_tutorial_sailors_spare_menu.png"]
    assert parsed["done"] is True and parsed["aborted"] is True
    assert [fight_tour.run_verdict(r) for r in parsed["runs"]][0] == "PASS"
    assert fight_tour.run_verdict(parsed["runs"][1]).startswith("FINDING")
    assert fight_tour.parse_fight_log("nothing here\n") == {"runs": [], "states": [], "shots": [], "done": False, "aborted": False}


def test_the_driver_has_no_force_flag_and_goes_through_the_gated_launcher():
    source = _text("tools", "fight_tour.py")
    assert "--force" not in source and "force=" not in source
    assert "pp_launch.launch(" in source
    assert set(fight_tour.ROOMS) == set(fight_tour.ENCOUNTERS)


def test_the_ended_phase_uses_the_tours_own_counter_because_the_battle_stops_stepping():
    """pp_mode_battle returns before pp_battle_step once pp_battle_finished, so phase_steps freezes in `ended`."""
    think = _function(OVERWORLD, "pp_fight_tour_think")
    ended = think[think.index("case PPBattlePhase.ended:"):]
    assert "_t.key_steps == 10" in ended and "_t.key_steps > 40" in ended
    assert "phase_steps" not in ended


def test_the_report_lists_ending_frames_and_back_in_world_per_run(tmp_path):
    parsed = fight_tour.parse_fight_log(SAMPLE_LOG + "PP fight tour: percy kill state=back_in_world\n")
    frames = [{"id": "percy", "path": "kill", "name": "pp_fight_percy_kill_ending.png"}]
    out = tmp_path / "REPORT.md"
    fight_tour.write_report(parsed["runs"], frames, [], str(out), parsed["states"])
    text = out.read_text(encoding="utf-8")
    assert "| percy | kill | yes | yes |" in text and "| tutorial_sailors | spare | NO | NO |" in text
