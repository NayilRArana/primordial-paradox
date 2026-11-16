"""The voice over, pinned to the script that owns its words.

Why this file exists: card t_5876de50 adds a narrator to the 180 s cut, one paragraph per shot, so the
judge panel's own complaint ("no title menu or narrator explains the claims", knowledge/JUDGE-PANEL-2026-11-14.md)
is answered by the deliverable and not by a note about the deliverable. The words live in
knowledge/DEMO-SCRIPT.md section 12; data/demo/narration.json is the machine copy the track is built from.
This file reads the two back against each other and against the shot clocks.

What is proved:

  1. every shot of the cut has exactly one narration paragraph, in shot order, and nothing else;
  2. each paragraph is section 12's paragraph, word for word, and each window is section 12's window;
  3. every window sits inside its own shot's clock in data/slice.json, so the narrator never talks over the
     next shot's picture;
  4. the windows do not overlap each other;
  5. no paragraph carries a long dash, which the project forbids in text it ships;
  6. {judge} is the only placeholder, and it is spoken as the DEFAULT_MODELS chat id, so no model name is
     typed into the narration anywhere;
  7. each row names a clip under output/demo/narration whose name is the shot's own, so a clip cannot be
     shipped under another shot's name.

No network, no engine and no audio is played here: this file reads JSON and Markdown.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

NARRATION = os.path.join(ROOT, "data", "demo", "narration.json")
SCRIPT = os.path.join(ROOT, "knowledge", "DEMO-SCRIPT.md")
SLICE = os.path.join(ROOT, "data", "slice.json")
META_CLIENT = os.path.join(TOOLS, "meta_client.py")

SHOT_IDS = ("S1", "S2", "S3", "S4", "S5", "S6")
LONG_DASHES = ("\u2013", "\u2014", "\u2012", "\u2015")
ROW = re.compile(r"^\|\s*(S\d)\s*\|")


def _read(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def _load(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def narration():
    return _load(NARRATION)


def narration_rows():
    return narration().get("rows") or []


def clock_pair(text):
    """"0:04.20 to 0:15.90" as two floats."""
    left, right = [part.strip() for part in text.split(" to ")]
    return [_seconds(left), _seconds(right)]


def _seconds(text):
    minutes, seconds = text.split(":")
    return int(minutes) * 60 + float(seconds)


def section_twelve():
    """Section 12's table, parsed: shot, window, words and claim, in the order the script lists them."""
    lines = _read(SCRIPT).splitlines()
    start = next((index for index, line in enumerate(lines) if line.startswith("## 12.")), None)
    assert start is not None, "knowledge/DEMO-SCRIPT.md has no '## 12.' section"
    rows = {}
    for line in lines[start:]:
        match = ROW.match(line)
        if not match:
            if line.startswith("## ") and not line.startswith("## 12."):
                break
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows[cells[0]] = {"window": clock_pair(cells[1]), "words": cells[2], "claim": cells[3]}
    return rows


def slice_rows():
    body = _load(SLICE).get("shots") or {}
    return {row["id"]: row for row in body.get("rows") or []}


def meta_models():
    spec = importlib.util.spec_from_file_location("meta_client", META_CLIENT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DEFAULT_MODELS


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS, name + ".py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCRIPT_ROWS = section_twelve()
ROWS = narration_rows()


def test_one_paragraph_per_shot_in_shot_order():
    ids = [row.get("shot") for row in ROWS]
    assert ids == list(SHOT_IDS), "data/demo/narration.json names %r, and the cut's shots are %r" % (
        ids, list(SHOT_IDS))
    assert sorted(SCRIPT_ROWS) == list(SHOT_IDS), "section 12's table names %r" % sorted(SCRIPT_ROWS)


def test_each_paragraph_is_the_scripts_own_words():
    problems = []
    for row in ROWS:
        wanted = SCRIPT_ROWS.get(row["shot"])
        if wanted is None:
            problems.append("%s: section 12 has no row for it" % row["shot"])
            continue
        if row.get("words") != wanted["words"]:
            problems.append("%s:\n  narration.json: %r\n  the script:     %r"
                            % (row["shot"], row.get("words"), wanted["words"]))
        if [float(value) for value in row.get("window") or []] != wanted["window"]:
            problems.append("%s: narration.json windows %r, the script windows %r"
                            % (row["shot"], row.get("window"), wanted["window"]))
        if row.get("claim") != wanted["claim"]:
            problems.append("%s: the claim column drifted from section 12" % row["shot"])
    assert problems == [], "\n".join(problems)


def test_every_window_sits_inside_its_own_shot():
    shots = slice_rows()
    problems = []
    for row in ROWS:
        shot = shots.get(row["shot"])
        if shot is None:
            problems.append("%s: data/slice.json has no such shot" % row["shot"])
            continue
        start, end = [_seconds(part) for part in shot["clock"]]
        lo, hi = [float(value) for value in row["window"]]
        if lo < start or hi > end:
            problems.append("%s: the narrator runs %r and the shot is %r" % (row["shot"], [lo, hi], shot["clock"]))
    assert problems == [], "\n".join(problems)


def test_the_windows_do_not_overlap():
    ordered = sorted([float(row["window"][0]), float(row["window"][1])] for row in ROWS)
    for (_, prev_hi), (lo, _) in zip(ordered, ordered[1:]):
        assert prev_hi <= lo, "two narration windows overlap at %.2f s" % lo


def test_no_paragraph_carries_a_long_dash():
    for row in ROWS:
        for dash in LONG_DASHES:
            assert dash not in row.get("words", ""), "%s's paragraph carries %r" % (row["shot"], dash)


def test_the_judge_is_spoken_from_the_models_table():
    models = meta_models()
    voiceover = load_tool("demo_voiceover")
    assert voiceover.spoken_model(models["chat"]) == "Muse Spark 1.3", \
        "the spoken form of %r is not what the narrator says" % models["chat"]
    # Only S5 names the judge, and it does it through the placeholder rather than a typed id.
    holders = [row["shot"] for row in ROWS if "{judge}" in row.get("words", "")]
    assert holders == ["S5"], "the {judge} placeholder is in %r" % holders
    assert holders, "no row names the judge"
    spoken = [voiceover.spoken_words(row) for row in ROWS]
    assert all("{judge}" not in line for line in spoken), "a placeholder survived into the spoken line"
    assert "Muse Spark 1.3" in spoken[SHOT_IDS.index("S5")], "the judge is not spoken in S5"


def test_each_row_names_its_own_clip():
    clip_dir = narration().get("clip_dir") or ""
    assert clip_dir.replace("\\", "/").startswith("output/demo/narration"), \
        "the clips are not written under output/demo/narration: %r" % clip_dir
    problems = []
    for row in ROWS:
        wanted = "%s/%s.wav" % (clip_dir.replace("\\", "/"), row["shot"])
        got = (row.get("file") or "").replace("\\", "/")
        if got != wanted:
            problems.append("%s: the clip is %r, and the shot's own name is %r" % (row["shot"], got, wanted))
    assert problems == [], "\n".join(problems)
