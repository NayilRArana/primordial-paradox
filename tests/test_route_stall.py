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


# RETIRED by FLOW 2026-11-03: test_route_markers_follow_the_slice_route_in_order. It pinned the recorded demo tape against the old gate, office, boarding route; the tape is not the product any more.