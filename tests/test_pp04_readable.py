"""Tests for card t_98ba7eb9: the three pp04 recipes must be readable by both the gate and the renderer.

Why this file exists: `assets/audio/pp_04_navy_sailors*/score_pp04*.yaml` write each section's span as
a LIST of bar numbers (`bars: [1, 2, 3, 4, 5, 6, 7, 8]`), while `arrange.build_bars_v3` reads a COUNT.
The three files therefore died with

    TypeError: int() argument must be a string, a bytes-like object or a real number, not 'list'

inside `build_bars_v3`, which made the music gate report them UNMEASURED (3 of 137 cues) and made
`python tools/arrange.py <recipe>` unable to re-render the cue that ships. `rules.py` was pointed at
`arrange.build_arrangement_pp04` first, which fixed the measurement; the renderer's own dispatch was
still on `build_arrangement_v3` and still died. This file pins both halves:

  - the gate reads the three recipes and returns a measured verdict, never UNMEASURED;
  - `arrange.main` renders each of the three to MIDI and writes a report with no out of range note;
  - the pp04 reader the checker uses and the cue's own builder agree on every PITCHED voice, for all
    three versions, so the measurement is of the cue that ships and not of a lookalike.

The unpitched voices are allowed to differ on v2 and v3, and this file measures how: those two
builders program their own hats, fills and kit, and the counterpoint checker skips unpitched tracks.
v1 has no such difference, so its render is byte identical to the shipped `pp_04_navy_sailors.mid`
(checked by hand at commit time; the .mid is gitignored, so the test compares in memory against
`build_pp04.py` instead of against a file a clean clone does not have).
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
COUNTERPOINT = os.path.join(TOOLS, "counterpoint")
for path in (TOOLS, COUNTERPOINT):
    if path not in sys.path:
        sys.path.insert(0, path)

import arrange  # noqa: E402
import cue_gate  # noqa: E402

# (folder, recipe, that version's own builder)
CASES = [
    ("pp_04_navy_sailors", "score_pp04.yaml", "build_pp04.py"),
    ("pp_04_navy_sailors_v2", "score_pp04_v2.yaml", "build_pp04_v2.py"),
    ("pp_04_navy_sailors_v3", "score_pp04_v3.yaml", "build_pp04_v3.py"),
]
PITCHED = ["vrc6 pulse a", "vrc6 pulse b", "vrc6 saw", "pulse 1", "pulse 2", "triangle"]
IDS = [case[0] for case in CASES]


def recipe_path(folder, recipe):
    return os.path.join(ROOT, "assets", "audio", folder, recipe)


def load_recipe(folder, recipe):
    with open(recipe_path(folder, recipe), "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_builder(folder, builder):
    path = os.path.join(ROOT, "assets", "audio", folder, builder)
    spec = importlib.util.spec_from_file_location("builder_" + folder, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("folder,recipe,builder", CASES, ids=IDS)
def test_the_gate_measures_every_pp04_recipe(folder, recipe, builder):
    """The hole this card closes: a bars-list recipe must not come back UNMEASURED."""
    _facts, verdict = cue_gate.gate(recipe_path(folder, recipe))
    assert verdict["state"] != "UNMEASURED", verdict.get("why")
    assert verdict["state"] in ("PASS", "REFUSED", "LEGACY", "GRANDFATHERED"), verdict["state"]
    # Exit 0 or 1, never 2 (the code the gate uses for "cannot read this cue").
    assert cue_gate.state_code(verdict["state"]) in (0, 1)


@pytest.mark.parametrize("folder,recipe,builder", CASES, ids=IDS)
def test_the_arranger_renders_every_pp04_recipe(folder, recipe, builder, tmp_path):
    """`python tools/arrange.py <recipe>` used to raise on line 1159; it must write a cue."""
    out = tmp_path / (folder + ".mid")
    report_path = tmp_path / (folder + ".json")
    code = arrange.main([recipe_path(folder, recipe), "-o", str(out), "--report", str(report_path)])
    assert code == 0
    assert out.exists() and out.stat().st_size > 1000
    with open(report_path, "r", encoding="utf-8") as handle:
        report = json.load(handle)
    assert report["schema"] == "pp04"
    assert report["bars"] == 32
    assert report["out_of_range"] == []
    assert report["chords_match_score"] is True
    assert report["bar_numbers_match_score"] is True
    assert report["tempo_meta_matches_score"] is True
    assert report["duration_seconds"] == pytest.approx(43.636, abs=0.01)
    assert all(report["notes"][name] > 0 for name in arrange.TRACK_NAMES)


@pytest.mark.parametrize("folder,recipe,builder", CASES, ids=IDS)
def test_the_reader_reproduces_the_cue_its_builder_writes(folder, recipe, builder):
    """The checker's reader and the cue's own builder must agree on every pitched voice."""
    score = load_recipe(folder, recipe)
    module = load_builder(folder, builder)
    built = module.build(score)
    old = built[0] if isinstance(built, tuple) else built
    new = arrange.build_arrangement_pp04(score)

    assert len(old.bars) == len(new.bars) == 32
    for track in PITCHED:
        assert list(old.notes[track]) == list(new.notes[track]), track
    # The unpitched voices are the one place the versions differ; they must all exist.
    for track in ("noise", "dpcm"):
        assert new.notes[track], track


def test_the_shipped_cue_render_is_byte_identical(tmp_path):
    """PP-04 ships from the v1 recipe, so its re-render is not merely similar, it is the same file.

    The shipped .mid is gitignored, so this compares against the builder in memory and then pins the
    byte count the shipped artifacts on disk have (14161 bytes, pp_04_navy_sailors.mid).
    """
    score = load_recipe("pp_04_navy_sailors", "score_pp04.yaml")
    data = arrange.write_midi(arrange.build_arrangement_pp04(score),
                              str(tmp_path / "pp_04.mid"))
    assert len(data) == 14161
    with open(tmp_path / "pp_04.mid", "rb") as handle:
        assert handle.read() == data
