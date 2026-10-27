"""The report driver: it has to read a file, print the table and exit 0, including --json.

Card t_c0597404. `tools/counterpoint/analyze.py` is what every number in
knowledge/TITLE-DISSONANCE-2026-10-26.md was read from, so the test drives the CLI the way a person
does rather than calling its helpers: argv in, exit code and printed lines out.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
COUNTERPOINT = os.path.join(TOOLS, "counterpoint")
for path in (TOOLS, COUNTERPOINT):
    if path not in sys.path:
        sys.path.insert(0, path)

import analyze  # noqa: E402
import humanize  # noqa: E402

BEAT = 480
BAR = BEAT * 3


@pytest.fixture()
def clashy(tmp_path):
    """Two bars with one deliberate major seventh on the downbeat of bar 1."""
    payload = {"division": 480, "tempo_us": 476190, "time_sig": (3, 4), "tracks": [
        {"name": "triangle", "notes": [(0, BAR, 48, 96), (BAR, 2 * BAR, 45, 96)], "cc": []},
        {"name": "vrc6 saw", "notes": [(0, BAR, 52, 80), (0, BAR, 55, 80),
                                       (BAR, 2 * BAR, 48, 80), (BAR, 2 * BAR, 52, 80)], "cc": []},
        {"name": "vrc6 pulse a", "notes": [(BEAT, BAR, 71, 96), (BAR + BEAT, 2 * BAR, 74, 96)],
         "cc": []},
    ]}
    path = str(tmp_path / "clashy.mid")
    humanize.write_smf(payload, path)
    return path


def run(monkeypatch, argv, capsys):
    monkeypatch.setattr(sys, "argv", ["analyze.py"] + argv)
    assert analyze.main() == 0
    return capsys.readouterr().out


def test_the_report_prints_the_class_table(monkeypatch, capsys, clashy):
    out = run(monkeypatch, [clashy], capsys)
    assert "class" in out
    for name in ("suspension", "appoggiatura", "passing", "neighbour", "anticipation", "raw clash"):
        assert name in out
    assert "raw clashes per 8 bars" in out
    assert "raw clashes on a strong beat" in out


def test_json_mode_writes_every_event(monkeypatch, capsys, clashy, tmp_path):
    target = tmp_path / "out.json"
    out = run(monkeypatch, [clashy, "--json", str(target), "--limit", "0"], capsys)
    assert "json" in out
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["bars"] >= 2
    assert payload["summary"]["raw_total"] >= 1
    assert payload["events"], "every judged event has to be in the file, not only the raw ones"
    assert all("class" in event for event in payload["events"])


def test_a_voice_subset_judges_only_those_voices(monkeypatch, capsys, clashy):
    out = run(monkeypatch, [clashy, "--voices", "pulse 1,pulse 2,triangle"], capsys)
    assert "judged" in out
    assert "vrc6" not in out.split("raw clash by pair")[-1].split("raw clashes per 8 bars")[0]


def test_all_prints_every_raw_clash(monkeypatch, capsys, clashy):
    limited = run(monkeypatch, [clashy, "--limit", "1"], capsys)
    everything = run(monkeypatch, [clashy, "--all"], capsys)
    assert len(everything) >= len(limited)
