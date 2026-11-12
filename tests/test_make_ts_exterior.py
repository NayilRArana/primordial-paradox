"""Tests for the sidecar tools/art/make_ts_exterior.py writes (card t_668c1cae).

What these pin, and why each one is a measurement rather than a matter of taste:

1. The `rule` line counts the groups the sidecar itself declares. It said "5 background palettes of
   3 entries" while the file declared six (`bg0_stone` .. `bg5_plant`), because the number was a
   literal and `bg5_plant` was added after it was written. The text is now generated from
   `len(palettes)` and states the ruling (knowledge/PALETTE-RULINGS-2026-11-12.md section 5): the
   atlas is a POOL of groups, a scene spends at most 4 background palettes of 3 entries in one frame,
   and a 16x16 tile carries at most 3 colours besides the shared backdrop `$0F`.
2. The count is DERIVED, not typed, and this is the row that says so out loud: with a seventh group
   in `PALETTES` the line says seven, and it says six again once that group is gone. A literal would
   pass row 1 today and fail the moment a group is added, which is exactly what happened before.
3. The committed sidecars are what the generator writes today. The scratch root is seeded with the
   only input the generator reads (data/nes_palette.json), which is the same seeding the other art
   generators' tests use, so a regeneration that drifts shows up as a red row rather than as a stale
   line nobody measures.

The comparison is on newline-normalised bytes rather than raw bytes: json.dump writes "\n" through a
text-mode handle, so the committed file carries CRLF on this Windows host and a build of the same
code on Pine carries LF. The payload is what this row is about, not the line ending of the machine
that wrote it.

The build is one sheet of 64 tiles, so the whole file costs well under a second.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "tools", "art")
if ART not in sys.path:
    sys.path.insert(0, ART)

import make_ts_exterior as gen  # noqa: E402

ENV = os.path.join("game", "sprites_src", "env")
SIDECARS = ("ts_exterior.json", "ts_exterior_tiled.json")
RULE = "NES: a POOL of groups, %d background palettes of 3 entries, a scene spends at most 4 of them in one frame, " \
       "a 16x16 tile carries at most 3 colours besides the shared backdrop $0F; the three composed town frames " \
       "measure 8 distinct colour sets covered by 3 palettes of the 4 allowed"


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def payload(path: str) -> bytes:
    """The file's bytes with one line ending, so a CRLF host and an LF host agree on everything else."""
    with open(path, "rb") as handle:
        return handle.read().replace(b"\r\n", b"\n")


def build_in(root: str) -> None:
    """Build into a scratch root the way the repository builds, seeded with the one input it reads."""
    palette = os.path.join(ROOT, "data", "nes_palette.json")
    assert os.path.isfile(palette), "the repository is missing the generator's own input: %s" % palette
    os.makedirs(os.path.join(root, "data"), exist_ok=True)
    shutil.copyfile(palette, os.path.join(root, "data", "nes_palette.json"))
    with contextlib.redirect_stdout(io.StringIO()):
        assert gen.main(["--root", root]) == 0


# ------------------------------------------------------------------- 1. the text says what the file declares

def test_the_rule_line_counts_the_groups_the_sidecar_declares():
    meta = load(os.path.join(ROOT, ENV, "ts_exterior.json"))
    declared = len(meta["palettes"])
    assert declared == len(gen.PALETTES), (
        "the sidecar declares %d groups and the generator holds %d" % (declared, len(gen.PALETTES)))
    assert meta["rule"] == RULE % declared, meta["rule"]
    assert "5 background palettes" not in meta["rule"], (
        "the stale count is back: %s" % meta["rule"])


def test_the_rule_line_states_the_ruling_and_not_a_scene_budget():
    """A pool may hold more groups than a frame can spend, and the text has to say so."""
    rule = load(os.path.join(ROOT, ENV, "ts_exterior.json"))["rule"]
    assert "POOL" in rule, rule
    assert "a scene spends at most 4 of them in one frame" in rule, rule
    assert "at most 3 colours besides the shared backdrop $0F" in rule, rule


# ------------------------------------------------------------------- 2. the count is derived, not typed

def test_the_count_follows_palettes_rather_than_a_literal():
    entries = gen.load_palette(ROOT)
    today = gen.build_metadata([], entries)["rule"]
    gen.PALETTES["bg9_probe"] = {"M": 0, "L": 16, "W": 48}
    try:
        grown = gen.build_metadata([], entries)["rule"]
    finally:
        del gen.PALETTES["bg9_probe"]
    assert "7 background palettes" in grown, grown
    assert grown != today, "the rule text ignored a seventh group, so its count is a literal"
    assert gen.build_metadata([], entries)["rule"] == today, "the probe did not restore the group count"


# ------------------------------------------------------------------- 3. the committed sidecars are current

def test_a_scratch_build_reproduces_the_committed_sidecars(tmp_path):
    root = str(tmp_path / "rebuild")
    build_in(root)
    for name in SIDECARS:
        committed = os.path.join(ROOT, ENV, name)
        assert os.path.isfile(committed), "run tools/art/make_ts_exterior.py: %s is missing" % committed
        assert payload(committed) == payload(os.path.join(root, ENV, name)), (
            "%s differs from a fresh build, so the committed sidecar is stale" % name)


def test_the_tiled_sidecar_carries_the_same_rule_line():
    plain = load(os.path.join(ROOT, ENV, "ts_exterior.json"))["rule"]
    tiled = load(os.path.join(ROOT, ENV, "ts_exterior_tiled.json"))["rule"]
    assert tiled == plain, "the tiled sidecar still quotes an older rule line"
