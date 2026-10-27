"""Tests for tools/make_architecture_diagram.py: one list of draw operations, two files, two proofs.

Card t_7b18be6f (PUB-1). The picture is the page a judge reads in ten seconds, and it makes three
claims that can be wrong without looking wrong: every card names a real file, the vector file and
the raster file come from the same operations, and two runs write byte identical bytes. Each claim
gets a test, plus a negative control for each check so a check that always says yes cannot pass.

The raster test reads the width and height out of the PNG header rather than trusting the call, and
the reproducibility test replaces one build with a deliberately unstable one, so "byte identical
twice" is proven to be a measurement rather than a constant.
"""

from __future__ import annotations

import hashlib
import json
import os
import re

import pytest

import make_architecture_diagram as mad

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


# --------------------------------------------------------------------------- the picture


def test_scene_has_the_four_bands_and_one_box_per_column():
    data = mad.scene(ROOT)
    for key in ("nodes", "stages", "calls", "stores"):
        assert key in data
        assert len(data[key]) == len(mad.GEOM[key])
        for card in data[key]:
            assert card["id"]
            assert card["title"]
            assert card["lines"]


def test_scene_reads_the_model_state_from_the_files():
    """The badges come from data/, so a picture cannot claim a live call the cache does not hold.

    The backend vocabulary is not pinned here: the cache records "meta" for real Meta calls beside
    "mock", and the tool's rule is "a non mock answer is live". Pinning the set made this test fail
    the day the first real call landed, so what is asserted instead is the rule itself, measured
    against whatever the folder holds, plus the store card reporting the same counts the reader
    found (a picture and a reader cannot disagree about the same folder).
    """
    data = mad.scene(ROOT)
    cache = mad.cache_state(ROOT)
    for card in data["calls"]:
        for line in card["lines"]:
            assert line  # every call box says something about what answered
    assert sum(cache["backends"].values()) == cache["entries"]
    live = sum(count for backend, count in cache["backends"].items() if backend != "mock")
    assert sum(cache["live_models"].values()) == live
    store = [card for card in data["stores"] if card["id"] == "s2"][0]
    assert "{} recorded answer(s)".format(cache["entries"]) in store["lines"][0]
    assert "live entries: {}".format(live) in store["lines"][1]


def test_badge_follows_the_cache_and_not_the_model_name(tmp_path):
    """The negative control for the badge: one model reads MOCKED, then LIVE, then NOT CALLED."""
    root = fixture_tree(tmp_path)
    cache_dir = root / "data" / "ai_cache"
    (cache_dir / "a.json").write_text(json.dumps({"backend": "mock", "model": "muse-spark-1.3"}), encoding="utf-8")
    assert mad.badge_for(mad.cache_state(str(root)), "muse-spark-1.3")[0] == "MOCKED"
    (cache_dir / "b.json").write_text(json.dumps({"backend": "meta", "model": "muse-spark-1.3"}), encoding="utf-8")
    cache = mad.cache_state(str(root))
    assert mad.badge_for(cache, "muse-spark-1.3")[0] == "LIVE"
    assert mad.badge_for(cache, "muse-image-1.0")[0] == "NOT CALLED"


def test_ops_are_primitives_and_stay_inside_the_canvas():
    ops = mad.ops_for(mad.scene(ROOT))
    kinds = {op[0] for op in ops}
    assert kinds <= {"rect", "text", "arrow"}
    assert kinds == {"rect", "text", "arrow"}
    for op in ops:
        if op[0] == "rect":
            _, x, y, w, h, _fill, _stroke, _sw = op
            assert 0 <= x <= mad.W and 0 <= y <= mad.H
            assert x + w <= mad.W + 1 and y + h <= mad.H + 1
        elif op[0] == "text":
            _, x, y, _text, size, _colour, anchor, _bold = op
            assert 0 <= x <= mad.W and 0 <= y <= mad.H
            assert size > 0
            assert anchor in ("start", "middle", "end")


def test_columns_lay_out_left_to_right_without_overlapping():
    boxes = mad.columns(5, 340, 190)
    assert len(boxes) == 5
    for left, right in zip(boxes, boxes[1:]):
        assert left["x"] < right["x"]
        assert left["x"] + left["w"] <= right["x"]
    assert boxes[0]["x"] == 40
    assert max(b["x"] + b["w"] for b in boxes) <= mad.W


def test_wrap_breaks_on_spaces_and_leaves_a_long_token_whole():
    assert mad.wrap("one two three four", 7) == ["one two", "three", "four"]
    assert mad.wrap("averylongtoken", 3) == ["averylongtoken"]
    assert mad.wrap("", 10) == []


# --------------------------------------------------------------------------- the two files


def test_render_svg_is_the_same_string_twice_and_carries_no_local_path():
    ops = mad.ops_for(mad.scene(ROOT))
    first = mad.render_svg(ops)
    second = mad.render_svg(ops)
    assert first == second
    assert first.startswith("<svg")
    assert first.rstrip().endswith("</svg>")
    assert ROOT not in first
    assert "C:\\" not in first
    assert "<workspace>" not in first


def test_render_svg_escapes_text_that_looks_like_markup():
    svg = mad.render_svg([("text", 10, 20, "a < b & c", 12, mad.INK, "start", False)])
    assert "&lt;" in svg and "&amp;" in svg
    assert "a < b & c" not in svg


def test_render_png_writes_a_png_of_the_claimed_size():
    png = mad.render_png(mad.ops_for(mad.scene(ROOT)))
    assert png.startswith(PNG_MAGIC)
    width = int.from_bytes(png[16:20], "big")
    height = int.from_bytes(png[20:24], "big")
    assert (width, height) == (mad.W, mad.H)


def test_write_files_writes_both_files_and_prints_their_hash(tmp_path, capsys):
    svg_path, png_path = mad.write_files(str(tmp_path / "docs"), ROOT)
    assert os.path.getsize(svg_path) > 0
    assert os.path.getsize(png_path) > 0
    with open(png_path, "rb") as fh:
        assert fh.read(8) == PNG_MAGIC
    out = capsys.readouterr().out
    assert "architecture.svg" in out and "architecture.png" in out
    assert hashlib.sha256(open(png_path, "rb").read()).hexdigest()[:16] in out


# --------------------------------------------------------------------------- the two checks


def test_named_paths_finds_a_path_inside_a_card_line():
    data = {"nodes": [{"lines": ["tools\\run.ps1 and knowledge\\PINE-SUITE-2026-10-24.md"]}],
            "stages": [], "calls": [], "stores": []}
    assert mad.named_paths(data) == ["tools\\run.ps1", "knowledge\\PINE-SUITE-2026-10-24.md"]


def test_named_paths_dedupes_across_cards():
    data = {"nodes": [{"lines": ["tools\\run.ps1"]}],
            "stages": [{"lines": ["tools/run.ps1"]}], "calls": [], "stores": []}
    assert len(mad.named_paths(data)) == 1


def test_check_modules_passes_on_the_real_tree(capsys):
    assert mad.check_modules(ROOT, quiet=True) == 0
    assert "0 missing" in capsys.readouterr().out


def fixture_tree(tmp_path):
    """The smallest tree scene() can read, so a named path is provably absent."""
    root = tmp_path / "tree"
    (root / "data" / "ai_cache").mkdir(parents=True)
    (root / "data" / "meta_bake.json").write_text(
        json.dumps({"bake": {"live": 0, "fallback": 0, "model": "mock"}, "rows": []}), encoding="utf-8")
    return root


def test_check_modules_names_a_path_that_is_not_there(tmp_path, capsys):
    """The negative control: an empty tree names files the picture claims, and the check says so.

    The counts are taken from the picture rather than pinned, so adding a card to the diagram does not
    break this test while the property it checks (every named path absent, every absence reported) holds.
    """
    root = fixture_tree(tmp_path)
    want = len(mad.named_paths(mad.scene(str(root))))
    assert mad.check_modules(str(root), quiet=False) == 1
    out = capsys.readouterr().out
    assert "MISSING" in out
    assert out
    assert "tools\\run.ps1" in out
    found = re.search(r"(\d+) named path\(s\), (\d+) exist, (\d+) missing", out)
    assert found, out
    named, exist, missing = (int(part) for part in found.groups())
    assert named == want
    assert exist + missing == named
    assert exist == 1, "the fixture tree holds exactly one of them"
    assert "data\\meta_bake.json" in out


def test_the_real_picture_names_only_paths_that_exist(capsys):
    """The public picture may not point at a file the export cannot carry."""
    assert mad.check_modules(ROOT, quiet=False) == 0
    out = capsys.readouterr().out
    assert "0 missing" in out
    assert "MISSING" not in out


def test_check_reproducible_passes_on_the_real_tree(capsys):
    assert mad.check_reproducible(ROOT) == 0
    assert "byte identical twice: yes" in capsys.readouterr().out


def test_check_reproducible_fails_two_builds_that_differ(monkeypatch, tmp_path, capsys):
    """The negative control for the reproducibility proof: an unstable build must be refused."""
    calls = {"n": 0}

    def unstable(root=ROOT):
        calls["n"] += 1
        tag = str(calls["n"]).encode()
        return b"<svg>" + tag, b"png" + tag

    monkeypatch.setattr(mad, "build_bytes", unstable)
    assert mad.check_reproducible(str(fixture_tree(tmp_path))) == 1
    assert "byte identical twice: NO" in capsys.readouterr().out


def test_main_writes_the_pair_then_runs_both_checks(tmp_path, capsys):
    out_dir = str(tmp_path / "docs")
    assert mad.main(["--out-dir", out_dir, "--root", ROOT, "--quiet"]) == 0
    assert os.path.exists(os.path.join(out_dir, "architecture.svg"))
    assert os.path.exists(os.path.join(out_dir, "architecture.png"))
    assert mad.main(["--check-modules", "--root", ROOT, "--quiet"]) == 0
    assert mad.main(["--check-reproducible", "--root", ROOT]) == 0


def test_main_returns_one_when_a_check_fails(tmp_path, capsys):
    assert mad.main(["--check-modules", "--root", str(fixture_tree(tmp_path)), "--quiet"]) == 1
    capsys.readouterr()


def test_a_render_that_needs_pillow_says_so(monkeypatch):
    """The raster half is optional tooling; a missing Pillow must be an ImportError, not a blank file."""
    monkeypatch.setitem(__import__("sys").modules, "PIL", None)
    with pytest.raises(ImportError):
        mad.render_png([("rect", 0, 0, 4, 4, mad.BG, None, 0)])
