"""Pins for card t_5d1a6ec4, second half: the idle gate names a desktop automation instead of blaming Nayil.

Measured on this host on 2026-10-26: codex.exe and codex-computer-use-swift.exe drove the desktop all session,
took focus and input every 90 to 110 s, and since tools/idle_check.py measures input through GetLastInputInfo,
four re-records were refused with "input 9 s ago" and no way to see that the input was the automation's own.
These tests hold down the three answers that fix has to keep apart:
  1. an automation is running: refuse, say which process, and say the input is not his (never allow on the
     strength of the automation's own silence);
  2. no automation is running: the tick decides, exactly as before;
  3. the process list cannot be read: one line saying so, and the tick still decides (an unreadable list is
     not a pass and not a licence).

Run: python -m pytest tests/test_idle_gate_automation.py -q
"""

from __future__ import annotations

import importlib.util
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

MIN_IDLE = 180.0


def load(name: str):
    path = os.path.join(TOOLS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_running_automation_is_refused_by_name_and_never_read_as_the_user():
    idle_check = load("idle_check")
    lines = []
    allowed, idle = idle_check.check(idle_read=lambda: 900.0, min_idle=MIN_IDLE, say=lines.append,
                                     automation_read=lambda: ["codex.exe"])
    text = " ".join(lines)
    assert allowed is False, "a desktop automation's own silence must never open a window"
    assert idle == 900.0
    assert "REFUSED" in text
    assert "codex.exe" in text
    assert "not Nayil" in text, text
    assert "Stop it" in text, text


def test_the_automation_reason_wins_over_the_recent_input_the_automation_produced():
    """The card's own symptom: input 9 s ago, no way to see that the input was not his."""
    idle_check = load("idle_check")
    lines = []
    allowed, _idle = idle_check.check(idle_read=lambda: 9.0, min_idle=MIN_IDLE, say=lines.append,
                                      automation_read=lambda: ["codex-computer-use-swift.exe"],
                                      wait_s=0.0)
    text = " ".join(lines)
    assert allowed is False
    assert "codex-computer-use-swift.exe" in text
    assert "SKIPPED" not in text, text


def test_with_no_automation_the_tick_decides_as_before():
    idle_check = load("idle_check")
    lines = []
    allowed, idle = idle_check.check(idle_read=lambda: 600.0, min_idle=MIN_IDLE, say=lines.append,
                                     automation_read=lambda: ())
    assert allowed is True and idle == 600.0
    assert "allows the launch" in " ".join(lines)


def test_an_unreadable_process_list_says_so_and_leaves_the_tick_deciding():
    idle_check = load("idle_check")
    lines = []
    allowed, _idle = idle_check.check(idle_read=lambda: 600.0, min_idle=MIN_IDLE, say=lines.append,
                                      automation_read=lambda: None)
    text = " ".join(lines)
    assert allowed is True
    assert "cannot read this host's process list" in text, text


def test_a_wait_does_not_outlive_a_running_automation():
    idle_check = load("idle_check")
    ticks = {"t": 0.0}
    lines = []
    allowed, _idle = idle_check.check(idle_read=lambda: 900.0, min_idle=MIN_IDLE, wait_s=60.0, poll_s=20.0,
                                      clock=lambda: ticks["t"],
                                      sleep=lambda seconds: ticks.__setitem__("t", ticks["t"] + seconds),
                                      say=lines.append, automation_read=lambda: ["codex.exe"])
    assert allowed is False
    assert ticks["t"] == pytest.approx(60.0), "the wait has to end at its own deadline"
    assert "codex.exe" in " ".join(lines)


def test_the_running_automation_list_finds_both_images_and_keeps_the_long_name():
    idle_check = load("idle_check")
    running = ["system", "explorer.exe", "codex.exe", "codex-computer-use-swift.exe", "primordialparadox.exe"]
    found = idle_check.automation_running(lister=lambda: running)
    assert found == ["codex-computer-use-swift.exe", "codex.exe"], found
    assert idle_check.automation_running(lister=lambda: ["explorer.exe"]) == []


def test_the_environment_extends_the_automation_list(monkeypatch):
    idle_check = load("idle_check")
    monkeypatch.setenv(idle_check.AUTOMATION_ENV, "my-bot.exe, another-bot")
    found = idle_check.automation_running(lister=lambda: ["my-bot.exe", "another-bot.exe", "explorer.exe"])
    assert found == ["another-bot.exe", "my-bot.exe"], found
    assert "my-bot.exe" in idle_check.automation_images()


def test_the_process_namer_normalises_the_exe_suffix_and_case():
    idle_check = load("idle_check")
    assert idle_check.normalise_image("CODEX.EXE") == "codex"
    assert idle_check.normalise_image("codex") == "codex"
    assert idle_check.normalise_image("") == ""


def test_the_selftest_table_carries_the_automation_rows():
    idle_check = load("idle_check")
    lines = []
    assert idle_check.selftest(say=lines.append) == 0
    text = "\n".join(lines)
    assert "a desktop automation is driving" in text, text
    assert "a process list that cannot be read still decides by the tick" in text, text
    assert "10 of 10 decisions right" in text, text


def test_the_gate_does_not_widen_the_refusal_code():
    """A refusal is still 4, the harness's not-measured lane, and never the watchdog's 3."""
    idle_check = load("idle_check")
    assert idle_check.EXIT_REFUSED == 4


def test_the_card_is_named_where_the_next_reader_will_look():
    idle_check = load("idle_check")
    with open(os.path.join(TOOLS, "idle_check.py"), "r", encoding="utf-8") as handle:
        text = handle.read()
    assert "t_5d1a6ec4" in text
    assert idle_check.AUTOMATION_ENV in text
    assert "tasklist" in text
