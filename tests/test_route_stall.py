"""Card ROUTE-STALL (2026-11-02): the demo route stalled in the real game at the dock office talk box.

The data level tests were green because nobody ran the whole route in the game. These tests pin what a log can show:
every plan marker has a message site in the GML and sits in route order, the typed word waits for the box that reads
it, and the audio rebuild neither counts the PP_AUDIO_LOG status lines nor puts its graph on the command line.
"""
from __future__ import annotations

import glob
import importlib.util
import json
import os
import re
import threading
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")


def load_play_demo():
    spec = importlib.util.spec_from_file_location("play_demo_stall", os.path.join(TOOLS, "play_demo.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(*parts):
    with open(os.path.join(ROOT, *parts), "r", encoding="utf-8") as handle:
        return json.load(handle)


def gml_text():
    out = []
    for path in (glob.glob(os.path.join(ROOT, "game", "scripts", "**", "*.gml"), recursive=True)
                 + glob.glob(os.path.join(ROOT, "game", "objects", "**", "*.gml"), recursive=True)):
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            out.append(handle.read())
    return "\n".join(out)


SCRIPT = read_json("data", "demo", "run_002.json")
EVENTS = SCRIPT["events"]


def marker_index(text):
    for index, event in enumerate(EVENTS):
        if event.get("marker") == text:
            return index
    raise AssertionError("run_002 carries no marker %r" % text)


# Each marker shape the tape names and the GML literals whose concatenation can print it.
SITES = [
    (r"^PP title: room rm_pp_title live$", ["PP title: room "]),
    (r"^PP title: intro started$", ["PP title: intro started"]),
    (r"^PP: music PP-\d+ requested$", ['"PP: music "', '" requested"']),
    (r"^PP scene: \w+ skipped$", ['"PP scene: "', '" skipped']),
    (r"^PP: battle start \w+$", ['"PP: battle start "']),
    (r"^PP: fight result \w+$", ['"PP: fight result "']),
    (r"^PP route: step \w+ handed to step \w+$", ['"PP route: "', '" handed to step "']),
    (r"^PP: talk scene open, npc \w+$", ['"PP: talk scene open, npc "']),
    (r"^PP scene: branch to \w+ on flag \w+$", ['"PP scene: branch to "', '" on flag "']),
    (r"^PP: battle menu, turn \d, cursor \d$", ['"PP: battle menu, turn "', '", cursor "']),
    (r"^PP: talk scene answer, npc \w+$", ['"PP: talk scene answer, npc "']),
    (r"^PP scene: \w+ talk done with \w+$", ['" talk done with "']),
    (r"^PP: ship's log$", ["\"PP: ship's log"]),
]


def test_every_run_marker_has_a_message_site_in_the_gml():
    text = gml_text()
    names = {e["marker"] for e in EVENTS if e.get("marker")}
    assert names
    for name in sorted(names):
        for pattern, literals in SITES:
            if re.match(pattern, name):
                for literal in literals:
                    assert literal in text, "marker %r has no GML message site (%s missing)" % (name, literal)
                break
        else:
            raise AssertionError("no site rule for run marker %r: add its GML literal to SITES" % name)


def test_route_markers_follow_the_slice_route_in_order():
    data = read_json("data", "slice.json")
    steps = data.get("steps")
    if steps is None:
        steps = (data.get("route") or {}).get("steps") or []
    rows = {row["id"]: row for row in steps}
    assert {"gate", "office", "boarding", "fight"} <= set(rows), sorted(rows)
    for event in EVENTS:
        match = re.match(r"^PP route: step (\w+) handed to step (\w+)$", event.get("marker") or "")
        if match:
            assert rows[match.group(1)]["next"] == match.group(2), event["marker"]
    order = ["PP route: step gate handed to step office", "PP: talk scene open, npc nye",
             "PP route: step office handed to step boarding", "PP: battle start tutorial_sailors",
             "PP: ship's log"]
    indexes = [marker_index(name) for name in order]
    indexes.append([i for i, e in enumerate(EVENTS) if e["id"] == "p01"][0])
    assert indexes == sorted(indexes), "route markers are out of route order: %s" % indexes
    steps_at = [EVENTS[i]["step"] for i in indexes]
    assert steps_at == sorted(steps_at)
    blob = ""
    for path in glob.glob(os.path.join(ROOT, "data", "encounters", "*.json")):
        with open(path, "r", encoding="utf-8") as handle:
            blob += handle.read()
    for encounter in ("tutorial_sailors", "percy", "morgan_gate"):
        assert '"%s"' % encounter in blob, encounter


def test_the_typed_word_waits_for_the_box_that_reads_it():
    open_index = marker_index("PP: talk scene open, npc nye")
    typed = [i for i, e in enumerate(EVENTS)
             if e["kind"] == "key" and e["key"] in ("p", "e", "r", "c", "y") and 6300 <= e["step"] <= 6500]
    assert typed, "the tape no longer types the word"
    assert open_index <= typed[0], "the word is typed before the box-open marker"
    event = EVENTS[open_index]
    assert event["kind"] == "key" and event.get("marker_wait_s", 0) >= 10, \
        "the first typed letter must hold for the box (marker_wait_s), or a late box eats the word"
    for name in ("PP route: step office handed to step boarding", "PP: battle start tutorial_sailors"):
        assert EVENTS[marker_index(name)].get("marker_wait_s", 0) >= 10, name


def test_a_late_game_holds_the_tape_and_shifts_the_rest(tmp_path):
    demo = load_play_demo()
    log = tmp_path / "game.log"
    log.write_text("", encoding="utf-8")
    replay = demo.Replay({"clock": {"fps": 60}, "events": []}, 0, str(log), lambda vk: None)
    replay.started = time.monotonic()
    threading.Timer(0.6, lambda: log.write_text("PP: box open\n", encoding="utf-8")).start()
    step, seen = replay.wait_marker_hold("PP: box open", 6, 3, 5.0)
    assert seen and step == 6 and replay.shift >= 20, (step, seen, replay.shift)
    missing = replay.wait_marker_hold("PP: never", 0, 0, 0.2)
    assert missing[1] is False


def test_status_lines_are_not_audio_rows_and_a_long_take_stays_off_the_command_line(tmp_path):
    demo = load_play_demo()
    status = "PP audio status: mode=overworld room=x cue=PP-03 instance=1 playing=1 gain=0.70 master=1 paused=0"
    events, notes = demo.audio_events([{"at": 1.0, "line": status}])
    assert events == []
    ffmpeg = demo.ffmpeg_path()
    sfx = glob.glob(os.path.join(ROOT, "assets", "audio", "**", "*.ogg"), recursive=True)
    if not ffmpeg or not sfx:
        pytest.skip("no ffmpeg or no tracked OGG on this host")
    segments = [{"kind": "sfx", "file": sfx[0], "in": 0.1 * k, "out": 0.1 * k + 0.05, "gain": 0.5, "loop": False}
                for k in range(900)]
    out = str(tmp_path / "long.m4a")
    seen = {}
    cap = demo.capture_module()
    real = cap.run_ffmpeg

    def spy(exe, arguments, timeout=300):
        seen["length"] = sum(len(a) + 1 for a in arguments)
        seen["args"] = list(arguments)
        return real(exe, arguments, timeout=timeout)

    cap.run_ffmpeg = spy
    try:
        ok, note = demo.render_log_audio(segments, 95.0, out)
    finally:
        cap.run_ffmpeg = real
    assert ("-filter_complex_script" in seen["args"] or "-/filter_complex" in seen["args"])
    assert "-filter_complex" not in seen["args"]
    assert seen["length"] < 4000, seen["length"]
    assert ok, note


# ---------------------------------------------------------------------------------------------------------------------
# Review findings F1 to F5 (2026-11-02)

def make_replay(demo, tmp_path, events, text=""):
    log = tmp_path / "game.log"
    log.write_text(text, encoding="utf-8")
    sent = []
    replay = demo.Replay({"clock": {"fps": 60}, "events": events}, 0, str(log),
                         lambda vk: sent.append(time.monotonic()))
    return replay, log, sent


def key_event(identifier, step, marker=None, wait=None, delay=0):
    event = {"id": identifier, "step": step, "kind": "key", "key": "z", "note": "test press"}
    if marker:
        event["marker"] = marker
        event["marker_delay_steps"] = delay
    if wait:
        event["marker_wait_s"] = wait
    return event


def test_run_honours_marker_wait_s_at_the_call_site(tmp_path):
    demo = load_play_demo()
    replay, log, sent = make_replay(demo, tmp_path, [key_event("a", 6, "PP: box open", 5), key_event("b", 12)])
    threading.Timer(1.0, lambda: log.write_text("PP: box open\n", encoding="utf-8")).start()
    start = time.monotonic()
    failures = replay.run(12)
    assert failures == []
    assert sent[0] - start >= 0.9, "the press fired before the box line existed"
    assert replay.shift >= 40, replay.shift
    assert sent[1] - sent[0] < 0.6, "the next press keeps its original spacing after the hold"


def test_the_timeout_path_shifts_the_clock_and_still_reports_unseen(tmp_path):
    demo = load_play_demo()
    replay, log, sent = make_replay(demo, tmp_path, [key_event("a", 6, "PP: never", 0.5), key_event("b", 12)])
    failures = replay.run(12)
    assert any("never carried" in line for line in failures)
    assert replay.shift >= 20, replay.shift
    assert [row for row in replay.trace if row["id"] == "a"][0]["detail"].endswith("not seen, step used")


def test_a_marker_already_in_the_log_returns_at_once_without_a_shift(tmp_path):
    demo = load_play_demo()
    replay, log, sent = make_replay(demo, tmp_path, [], "PP: box open\n")
    replay.started = time.monotonic()
    step, seen = replay.wait_marker_hold("PP: box open", 600, 3, 5.0)
    assert seen and step < 600 and replay.shift == 0


def test_a_repeated_marker_needs_one_more_line_per_earlier_event(tmp_path):
    demo = load_play_demo()
    events = [key_event("m", 6, "PP: fight result spare", 2), key_event("p", 12, "PP: fight result spare", 2)]
    replay, log, sent = make_replay(demo, tmp_path, events, "PP: fight result spare\n")
    assert replay.ordinal == {"m": 1, "p": 2}
    replay.started = time.monotonic()
    assert replay.wait_marker_hold("PP: fight result spare", 600, 0, 5.0, replay.ordinal["m"])[1] is True
    held = replay.wait_marker_hold("PP: fight result spare", 3, 0, 0.3, replay.ordinal["p"])
    assert held[1] is False, "the second fight must not be satisfied by the first fight's line"
    log.write_text("PP: fight result spare\nPP: fight result spare\n", encoding="utf-8")
    assert demo.read_marker(str(log), "PP: fight result spare", 2) is True


def test_the_recorder_bound_covers_every_hold_and_the_tail():
    demo = load_play_demo()
    script = {"events": [key_event("a", 6, "A", 25), key_event("b", 12, "B", 10), key_event("c", 18)]}
    assert demo.record_bound_seconds(script, 253.5) == pytest.approx(253.5 + 2.5 + 35)
    assert demo.record_bound_seconds(script, 253.5, end_step=8) == pytest.approx(253.5 + 2.5 + 25)
    real = demo.record_bound_seconds(SCRIPT, 253.5)
    assert real >= 253.5 + 2.5 + 6 * 25


def test_the_trace_carries_the_video_clock_and_the_tape_step(tmp_path):
    demo = load_play_demo()
    replay, log, sent = make_replay(demo, tmp_path, [])
    replay.started = time.monotonic()
    replay.shift = 90
    row = replay.record("x", "key", "z", 30)
    assert row["at_step"] == 120 and row["tape_step"] == 30 and row["at_second"] == 2.0


# ---------------------------------------------------------------------------------------------------------------------
# Part 2: the tape is state driven

GATES = {  # event id: the line the game prints before the event may fire (the phase's first event)
    "r007": "PP: music PP-02 requested", "r010": "PP route: step drive handed to step arrival",
    "m01": "PP: battle menu, turn 0, cursor 0", "m08": "PP: battle menu, turn 1, cursor 2",
    "m12": "PP: battle menu, turn 2, cursor 2", "m16": "PP: battle menu, turn 3, cursor 2",
    "m18": "PP: fight result spare", "r027": "PP route: step gate handed to step office",
    "t2201a": "PP: talk scene open, npc nye", "t2208": "PP: talk scene answer, npc nye",
    "t2209": "PP scene: quay_dock_office_play talk done with nye",
    "r040": "PP route: step office handed to step boarding", "r045": "PP: battle start tutorial_sailors",
    "r046": "PP: battle menu, turn 0, cursor 0", "r049b": "PP: battle menu, turn 1, cursor 2",
    "r051b": "PP: battle menu, turn 2, cursor 2", "r054": "PP: battle menu, turn 3, cursor 2",
    "r056": "PP: fight result spare", "r076": "PP: ship's log", "p01": "PP: battle menu, turn 0, cursor 0",
    "p06": "PP: battle menu, turn 1, cursor 2", "p08": "PP: battle menu, turn 2, cursor 2",
    "p10": "PP: battle menu, turn 3, cursor 2", "p12": "PP: fight result spare",
}


def test_every_phase_and_fight_turn_group_is_gated_on_a_line_the_game_prints():
    by = {e["id"]: e for e in EVENTS}
    for identifier, line in GATES.items():
        event = by[identifier]
        assert event.get("marker") == line, identifier
        assert event.get("marker_wait_s", 0) >= 60, "%s must wait for the game (60 s or more)" % identifier
    demo = load_play_demo()
    replay = demo.Replay(SCRIPT, 0, "x", lambda vk: None)
    assert replay.ordinal["r046"] == 2 and replay.ordinal["p01"] == 3, "one first-turn menu per fight"
    assert replay.ordinal["p12"] == 3 and replay.ordinal["m18"] == 1
    assert "PP: battle start morgan_gate" not in {e.get("marker") for e in EVENTS}, "scene fights print no such line"
    # 2026-11-02 19:47 real run: these two lines are printed only AFTER the event that was gated on them (the confirm that
    # fires the gate scene prints the music line and the branch line comes after the choice), so a gate there deadlocks.
    assert by["r013b"].get("marker") is None, "the confirm that fires the gate scene cannot wait for the scene"
    assert "PP: music PP-03 requested" not in {e.get("marker") for e in EVENTS}, "printed by the gate scene, not on arrival"
    assert "PP scene: branch to quay_gate_authority on flag gate_authority" not in {e.get("marker") for e in EVENTS}


def test_the_name_box_is_cleared_before_the_word_is_typed():
    ids = [e["id"] for e in EVENTS]
    keys = [EVENTS[ids.index(i)]["key"] for i in ("t2201a", "t2201b", "t2201c")]
    assert keys == ["backspace"] * 3
    assert ids.index("t2201c") < ids.index("t2202")
    assert ids.index("t2201") < ids.index("t2201a"), "the safety press comes before the gate, never after the box"
    assert "backspace" in load_play_demo().capture_module().KEY_CODES
    steps = [e["step"] for e in EVENTS]
    assert steps == sorted(steps)


def test_a_slow_game_never_gets_a_key_before_its_gate(tmp_path):
    demo = load_play_demo()
    log = tmp_path / "game.log"
    log.write_text("", encoding="utf-8")
    events = [key_event("a", 6, "PP: one", 20), key_event("b", 12), key_event("c", 18, "PP: two", 20),
              key_event("d", 24), key_event("e", 30, "PP: two", 20), key_event("f", 36)]
    order = []
    replay = demo.Replay({"clock": {"fps": 60}, "events": events}, 0, str(log),
                         lambda vk: order.append(time.monotonic()))
    wrote = {}

    def write(text, name):
        with open(str(log), "a", encoding="utf-8") as handle:
            handle.write(text)
        wrote[name] = time.monotonic()

    for delay, text, name in ((1.2, "PP: one\n", "one"), (2.6, "PP: two\n", "two1"), (4.0, "PP: two\n", "two2")):
        threading.Timer(delay, write, args=(text, name)).start()
    failures = replay.run(36)
    assert failures == [], failures
    assert len(order) == 6
    assert order[0] >= wrote["one"], "a fired before the first line"
    assert order[2] >= wrote["two1"], "c fired before the second line"
    assert order[4] >= wrote["two2"], "e (the second event with the same marker) fired on the first line's copy"
    assert order[1] - order[0] < 0.5 and order[3] - order[2] < 0.5, "the spacing after a gate is the tape's own"
    assert replay.trace[-1]["at_second"] > 4.0


def test_the_gated_duration_band_is_reported_and_does_not_fail():
    demo = load_play_demo()
    table = demo.load_shot_table("full")
    rows = {name: {"needle": "n", "found": True, "line": "l"} for name, _needle in demo.BEAT_CUES}
    ok, line = demo.shot_table_check(table, 400.0, rows, gated=True)
    assert ok and "not enforced" in line, line
    ok, line = demo.shot_table_check(table, 400.0, rows, gated=False)
    assert not ok and "outside" in line


# what GML can print for each beat of the take (the static part of the needle)
BEAT_SITES = {
    "S1 title": '"PP title: room "', "S2 crawl": '"PP title: intro started', "S3 drive": '"PP: music "',
    "S4 gate": '" end at tile "', "S4 morgan fight": '"PP: command "', "S5 office": '" handed to step "',
    "S5 office talk": '"PP: talk scene answer, npc "', "S5 boarding": '" handed to step "',
    "S6 talk fight": '"PP: talk pick, option "', "S6 hound fight": '"PP: battle start "',
    "S6 ship log save": "\"PP: ship's log", "S6 percy fight": '"PP: command "',
    "S6 defeat": '"PP: fight result "', "S6 game over": '"PP: game over frame',
    "S6 continue": '"PP: game over, CONTINUE restored',
}


def test_the_beat_needles_are_lines_the_gml_can_print():
    demo = load_play_demo()
    text = gml_text()
    names = [name for name, _needle in demo.BEAT_CUES]
    assert sorted(names) == sorted(BEAT_SITES), "a beat has no GML site rule"
    for name, _needle in demo.BEAT_CUES:
        assert BEAT_SITES[name] in text, "%s: %s is not in the GML" % (name, BEAT_SITES[name])
    needles = dict(demo.BEAT_CUES)
    assert "quay_gate_checkpoint" not in needles["S4 gate"] and "quay_gate_authority" in needles["S4 gate"]
    assert "morgan_gate" not in needles["S4 morgan fight"] and "deck_hound" not in needles["S6 hound fight"]
    assert needles["S4 morgan fight"].startswith("PP: command talk, turn 1, enemy ")


def test_the_meter_log_tail_skips_the_old_run_and_follows_a_truncation(tmp_path):
    spec = importlib.util.spec_from_file_location("audio_meter_stall", os.path.join(TOOLS, "audio_meter.py"))
    meter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(meter)
    key = meter.LOG_KEYS[0]
    path = tmp_path / "game.log"
    path.write_text("%s old one\n%s old two\n" % (key, key), encoding="utf-8")
    tail = meter.LogTail(str(path))
    assert tail.poll() == [], "the previous run's lines must not be replayed"
    with open(str(path), "a", encoding="utf-8") as handle:
        handle.write("%s new a\n" % key)
    assert tail.poll() == ["%s new a" % key]
    path.write_text("%s fresh\n" % key, encoding="utf-8")
    assert tail.poll() == ["%s fresh" % key], "a truncated log is a new run, read from 0"
    later = meter.LogTail(str(tmp_path / "later.log"))
    (tmp_path / "later.log").write_text("%s first\n" % key, encoding="utf-8")
    assert later.poll() == ["%s first" % key]
