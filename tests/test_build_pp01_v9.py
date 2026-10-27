"""The v9 build script: what it must keep, and what its report has to prove.

Card t_c0597404. `assets/audio/pp_01_title_v9/build_pp01_v9.py` reads v7 and writes a new file. The
test does not re-run the 52 bar build (the gate must stay fast); it pins the two promises the build
makes and then reads the shipped report to check they held: the melody and the drums are frozen, and
the repaired score has no raw clash on a downbeat.
"""

from __future__ import annotations

import importlib.util
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

BUILD = os.path.join(ROOT, "assets", "audio", "pp_01_title_v9", "build_pp01_v9.py")
REPORT = os.path.join(ROOT, "assets", "audio", "pp_01_title_v9", "build_report_v9.json")


def load_build():
    spec = importlib.util.spec_from_file_location("build_pp01_v9", BUILD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(not os.path.exists(BUILD), reason="the v9 build script is not in this checkout")
def test_the_frozen_set_is_the_melody_and_the_drums():
    build = load_build()
    assert build.FROZEN == ("vrc6 pulse a", "noise", "dpcm")
    assert build.repair.HOOK == "vrc6 pulse a"


@pytest.mark.skipif(not os.path.exists(BUILD), reason="the v9 build script is not in this checkout")
def test_it_reads_v7_and_writes_somewhere_else():
    build = load_build()
    assert build.SRC.endswith(os.path.join("pp_01_title_v7", "pp_01_title_v7.mid"))
    assert build.OUT.endswith(os.path.join("pp_01_title_v9", "pp_01_title_v9.mid"))
    assert os.path.dirname(build.SRC) != os.path.dirname(build.OUT)


@pytest.mark.skipif(not os.path.exists(REPORT), reason="v9 has not been built in this checkout")
def test_the_shipped_report_proves_the_two_promises():
    report = json.load(open(REPORT, encoding="utf-8"))
    for voice, entry in report["frozen"].items():
        assert entry["identical"] is True, voice
    assert report["after"]["strong_raw"] == 0
    assert report["after"]["raw_total"] == 2
    assert report["before"]["raw_total"] > 150
    assert report["hook"]["before"] == report["hook"]["after"] == 83
    assert report["registers"] == []
    assert report["edits"] > 0


@pytest.mark.skipif(not os.path.exists(REPORT), reason="v9 has not been built in this checkout")
def test_the_rounds_never_go_backwards_on_the_strong_beat_count():
    report = json.load(open(REPORT, encoding="utf-8"))
    rounds = report["rounds"]
    assert rounds[0]["strong"] >= rounds[-1]["strong"]
    assert rounds[-1]["raw"] <= rounds[0]["raw"]
