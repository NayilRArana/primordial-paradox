"""The art target: three directions for one frame, measured, and the doc that explains the pick.

Card PP-ART-TARGET (t_0e56c7c7). The frame the card asks for is the Montefiore halls room with Zeus and
Kronos in it, and the deliverable is not one picture: it is three treatments of the SAME room, a sheet that
puts them side by side, and a document that tells whoever redraws the assets what the pick changes.

What this test measures, and why each one needs a machine rather than an eye:

    the rules        every cleanup rule the card lists is a number in the report (outline leaks, orphan
                     pixels, dither patches, off palette, light direction), and a green report with a red
                     rule would be exactly the kind of claim nobody can check by looking at a PNG
    the NES limits   the built background and sprite sheets are put through tools/nes_check.py with the
                     frame's own backdrop, which is the project's independent checker and not the tool
                     grading its own homework
    the sheet        the contact sheet is built from the three reports and lands at 3x with room for the
                     three columns, so the artefact the manager opens exists and is not a 1x frame
    the doc          every tools/art file knowledge/ART-STYLE.md names exists, the doc carries no long
                     dash (house rule), and it still names the three helpers that keep it true

No test here reads the network, spends a Gemini call, writes a tracked file, or needs GameMaker. The build
goes to pytest's tmp_path, never to output/art_target, so running the suite cannot change the sheet the demo
manager is looking at.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "art", "make_art_target.py")
NES_CHECK = os.path.join(ROOT, "tools", "nes_check.py")
DOC = os.path.join(ROOT, "knowledge", "ART-STYLE.md")

STYLES = ("A", "B", "C")
BACKDROP = "#000000"
LONG_DASHES = ("\u2013", "\u2014", "\u2015")
HELPERS = ("art_target_score.py", "art_target_table.py", "art_target_doc_check.py")


def run_python(argv):
    # stdin is explicit because tests/test_spawn_handles.py requires it: a child that inherits the parent's
    # stdin handle dies with WinError 6 when the suite's stdout is redirected to a log, which is how the gate
    # runs it. DEVNULL costs nothing here, none of these commands read input.
    return subprocess.run([sys.executable] + argv, cwd=ROOT, capture_output=True, text=True,
                          stdin=subprocess.DEVNULL)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """One build of all three directions, in a throwaway directory, shared by the tests below."""
    out = tmp_path_factory.mktemp("art_target")
    report_path = out / "report.json"
    result = run_python([TOOL, "--sheet", "--out", str(out), "--json", str(report_path)])
    assert result.returncode == 0, "make_art_target failed:\n%s\n%s" % (result.stdout, result.stderr)
    with open(str(report_path), "r", encoding="utf-8") as handle:
        reports = json.load(handle)
    return {"out": out, "result": result, "reports": reports}


def test_report_covers_all_three_directions(built):
    assert [report["style"] for report in built["reports"]] == list(STYLES)
    for report in built["reports"]:
        assert report["ok"] is True, "direction %s failed a rule: %s" % (report["style"], report["failures"])
        assert report["size"] == [256, 240]
        # 4 background palettes of 3 entries plus a shared backdrop, and the same for sprites.
        assert len(report["background_palettes"]) == 5
        assert len(report["sprite_palettes"]) == 4
        assert all(len(entries) == 3 for entries in report["sprite_palettes"].values())


def test_every_cleanup_rule_is_zero(built):
    """The card's rules, as numbers: no leaks, no orphans, no dither, no off palette colour."""
    for report in built["reports"]:
        style = report["style"]
        assert report["outline_leaks"] == 0, "%s leaks the outline" % style
        assert report["dither_patches"] == 0, "%s dithers" % style
        assert report["off_palette"] == [], "%s spends a colour the 2C02 cannot output" % style
        for figure in ("zeus", "kronos"):
            assert report["figures"][figure]["orphans_removed"] == 0, "%s %s had orphans" % (style, figure)
            assert report["figures"][figure]["outline_pixels"] > 0
        # Light from the top left: the correct-to-wrong ratio has to stay on the right side of 1.
        assert report["light_up_left"] > report["light_down_right"], "%s is lit from the wrong corner" % style


def test_nes_limits_hold_under_the_project_checker(built):
    """64 OAM entries, 8 sprites on a scanline, and the attribute areas, measured by tools/nes_check.py."""
    for report in built["reports"]:
        style = report["style"]
        assert report["sprite_objects"] <= 64, "%s needs %d OAM entries" % (style, report["sprite_objects"])
        assert report["max_sprites_per_scanline"] <= 8, "%s puts %d sprites on one scanline" % (
            style, report["max_sprites_per_scanline"])
        background = report["files"]["background"]
        sprites = report["files"]["sprites"]
        assert os.path.isfile(background) and os.path.isfile(sprites)
        for path, kind in ((background, "background"), (sprites, "sprite")):
            argv = [NES_CHECK, path, "--type", kind, "--quiet"]
            if kind == "background":
                # The frame's own backdrop. nes_check guesses the most common colour otherwise, which is
                # a floor tone here, and that guess flags B's window areas for a palette they do not use.
                argv += ["--backdrop", BACKDROP]
            result = run_python(argv)
            assert result.returncode == 0, "nes_check refused %s %s:\n%s" % (kind, style, result.stdout)


def test_sheet_is_a_sheet(built):
    sheet = os.path.join(str(built["out"]), "ART-TARGET-SHEET.png")
    assert os.path.isfile(sheet), "no sheet was written"
    assert "sheet:" in built["result"].stdout
    from PIL import Image
    with Image.open(sheet) as image:
        width, height = image.size
    # Three 256 px frames at 3x plus a gutter on each side, and taller than one 3x band.
    assert width >= 3 * 256 * 3 + 4 * 16, "the sheet is only %d px wide" % width
    assert height > 240 * 3, "the sheet never puts the 1x frames under the 3x band"


def test_doc_names_real_tools_and_has_no_long_dash():
    with open(DOC, "r", encoding="utf-8") as handle:
        text = handle.read()
    assert not [dash for dash in LONG_DASHES if dash in text], "knowledge/ART-STYLE.md carries a long dash"
    art_dir = os.path.join(ROOT, "tools", "art")
    named = sorted(set(re.findall(r"`tools/art/([A-Za-z0-9_]+\.py)`", text)))
    assert named, "the doc names no tool"
    missing = [item for item in named if not os.path.isfile(os.path.join(art_dir, item))]
    assert missing == [], "knowledge/ART-STYLE.md names tools that do not exist: %s" % missing
    # The three helpers that keep the doc's numbers and claims reproducible have to stay named, or the
    # next reader cannot re-take a score or re-run a check.
    for helper in HELPERS:
        assert helper in named, "the doc stopped naming tools/art/%s" % helper
