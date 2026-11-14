"""Tests for tools/review_gate.py: the picture review checklist, and the full colour frame it refuses.

Card t_d29d8161 (judge-panel fix 5, 2026-11-14). The card asks for a code review checklist in the
repository that rejects full colour frames and requires the palette and sprite limits. A page alone
would be a promise, so the page names this tool and the tool is what the tests hold:

1. a legal 256 by 240 frame passes every rule that applies, and a frame whose pixels are not PPU
   outputs is refused with the words the checklist uses;
2. a rule that applies but cannot be measured is not a pass: the sprite budget without a mask exits 1,
   and the reviewer's own no-sprites claim is the way past it;
3. the page is held to the tree by tools/check_readme.py, so a path or a command named there cannot age
   into a dead instruction;
4. the block tools/readme_badges.py writes carries the bridge section and the checklist, read from the
   module it names rather than typed.
"""

from __future__ import annotations

import json
import os

import pytest
from PIL import Image

import check_readme
import readme_badges
import review_gate

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKLIST = os.path.join(ROOT, "docs", "REVIEW-CHECKLIST.md")
FRAME = (256, 240)


def palette_colours(limit: int = 4) -> list:
    """Usable PPU colours, read the way the gate reads them, so a palette edit moves the fixture too."""
    composite = review_gate.load_tool("nes_composite_check_fixture", "nes_composite_check.py")
    palette = composite.load_palette(composite.default_palette_path(ROOT))
    return list(palette["allowed"])[:limit]


def write_legal_frame(path) -> None:
    """One legal frame: 16 by 16 areas of one PPU colour each, four colours across the picture."""
    colours = palette_colours()
    image = Image.new("RGBA", FRAME, colours[0] + (255,))
    pixels = image.load()
    for by in range(0, FRAME[1], 16):
        for bx in range(0, FRAME[0], 16):
            colour = colours[((bx // 16) + (by // 16)) % len(colours)]
            for y in range(by, by + 16):
                for x in range(bx, bx + 16):
                    pixels[x, y] = colour + (255,)
    image.save(path)


def write_full_colour_frame(path) -> None:
    """A frame a filter would make: thousands of colours, almost none of them a PPU output."""
    image = Image.new("RGBA", FRAME)
    pixels = image.load()
    for y in range(FRAME[1]):
        for x in range(FRAME[0]):
            pixels[x, y] = ((x * 7) % 256, (y * 11) % 256, (x + y) % 256, 255)
    image.save(path)


# --------------------------------------------------------------------------- the gate's verdicts


def test_a_legal_frame_passes_every_rule_that_applies(tmp_path, capsys):
    path = tmp_path / "frame.png"
    write_legal_frame(path)
    assert review_gate.main([str(path), "--no-sprites"]) == 0
    out = capsys.readouterr().out
    assert "review_gate: PASS" in out
    assert "R2 PASS" in out and "R8 PASS" in out


def test_a_full_colour_frame_is_refused_and_named(tmp_path, capsys):
    """The card's own sentence: the checklist rejects full colour frames. This is that reject."""
    path = tmp_path / "photo.png"
    write_full_colour_frame(path)
    assert review_gate.main([str(path), "--no-sprites"]) == 1
    out = capsys.readouterr().out
    assert "R2 REJECT" in out
    assert "full colour frame" in out
    assert "review_gate: REJECT" in out


def test_the_sprite_budget_without_evidence_is_not_a_pass(tmp_path, capsys):
    """A skip is never a pass: the rules that need a mask exit 1 instead of going quiet."""
    path = tmp_path / "frame.png"
    write_legal_frame(path)
    assert review_gate.main([str(path)]) == 1
    out = capsys.readouterr().out
    assert "R5 NOT MEASURED" in out and "R7 NOT MEASURED" in out
    assert "review_gate: NOT MEASURED" in out


def test_an_unreadable_picture_is_a_bad_argument_not_a_reject(tmp_path):
    assert review_gate.main([str(tmp_path / "nope.png")]) == 2


def test_a_still_with_no_legal_viewport_is_refused_at_r2(tmp_path, capsys):
    """The h264 still case: a resampled capture holds no 768 by 720 box of PPU colours, so R2 rejects it."""
    path = tmp_path / "still.png"
    image = Image.new("RGBA", (768, 736))
    pixels = image.load()
    for y in range(736):
        for x in range(768):
            pixels[x, y] = ((x * 5) % 256, (y * 3) % 256, (x + y) % 256, 255)
    image.save(path)
    assert review_gate.main([str(path), "--type", "frame", "--no-sprites"]) == 1
    out = capsys.readouterr().out
    assert "R2 REJECT" in out and "full colour frame" in out
    assert "no part of this picture is a frame the chip could draw" in out


def test_a_frame_flag_on_a_small_picture_is_a_bad_argument(tmp_path):
    """Smaller than one 3x frame is a mismatch between the flag and the file, not an art failure."""
    path = tmp_path / "small.png"
    write_legal_frame(path)
    assert review_gate.main([str(path), "--type", "frame", "--crop", "3"]) == 2


def test_a_layer_is_classified_by_its_size_and_a_sheet_by_its_flag(tmp_path):
    assert review_gate.classify(256, 240, "auto") == "frame"
    assert review_gate.classify(768, 720, "auto") == "frame"
    assert review_gate.classify(128, 32, "auto") == "background"
    assert review_gate.classify(256, 240, "sprite") == "sprite"


def test_overall_lets_a_reject_outrank_a_skip():
    pass_row = {"verdict": review_gate.PASS}
    skip_row = {"verdict": review_gate.NOT_MEASURED}
    reject_row = {"verdict": review_gate.REJECT}
    assert review_gate.overall([pass_row, skip_row]) == review_gate.NOT_MEASURED
    assert review_gate.overall([pass_row, skip_row, reject_row]) == review_gate.REJECT


def write_legal_sheet(path) -> None:
    """One legal sprite sheet: two 8 by 8 tiles, two PPU colours, transparency nowhere needed."""
    colours = palette_colours()
    image = Image.new("RGBA", (16, 8), colours[0] + (255,))
    image.putpixel((0, 0), colours[1] + (255,))
    image.save(path)


def test_every_row_carries_its_checklist_id(tmp_path):
    """R1 to R8 on every input: the tool's rows and the page's table use the same ids."""
    frame = tmp_path / "frame.png"
    write_legal_frame(frame)
    sheet = tmp_path / "sheet.png"
    write_legal_sheet(sheet)
    for path, kind in ((frame, "frame"), (sheet, "sprite")):
        result = review_gate.gate(str(path), kind)
        assert [item["id"] for item in result["rows"]] == [rule[0] for rule in review_gate.RULES]
        assert all(item["note"] for item in result["rows"])


# --------------------------------------------------------------------------- the page


def test_the_checklist_passes_the_readme_checker():
    """Its paths resolve and its commands name files on disk, so a moved tool fails here."""
    assert check_readme.main(["--readme", CHECKLIST]) == 0


def test_the_checklist_names_the_gate_and_every_rule():
    text = open(CHECKLIST, encoding="utf-8").read()
    assert "tools/review_gate.py" in text
    for rule in review_gate.RULES:
        assert "| %s |" % rule[0] in text, rule[0]
    assert "full colour frame" in text


# --------------------------------------------------------------------------- the README block


def test_the_readme_block_carries_the_bridge_section_and_the_checklist():
    block = readme_badges.build_block([{"slug": "check_data", "label": "check_data",
                                        "command": "python tools/check_data.py", "exit": 0,
                                        "status": "PASS", "seconds": 0.1}], ROOT)
    assert "## The local AI bridge, in this repo" in block
    for rel in (readme_badges.BRIDGE_SERVER, readme_badges.BRIDGE_META, readme_badges.BRIDGE_JUDGE,
                readme_badges.BRIDGE_CACHE, readme_badges.BRIDGE_PROBE, readme_badges.BRIDGE_BUILD,
                readme_badges.BRIDGE_DOC, readme_badges.REVIEW_CHECKLIST, readme_badges.REVIEW_GATE):
        assert "`%s`" % rel in block, rel
    for command in ("python tools/ai_bridge.py --selftest", "python tools/talk_scene_probe.py --offline",
                    "python tools/ai_bridge.py --serve --warm"):
        assert command in block, command


def test_the_bridge_section_reads_the_host_port_and_rungs_from_the_module():
    host = readme_badges.read_value(ROOT, readme_badges.BRIDGE_SERVER, "LOOPBACK_HOST")
    port = readme_badges.read_value(ROOT, readme_badges.BRIDGE_SERVER, "DEFAULT_PORT")
    rungs = readme_badges.read_names(ROOT, readme_badges.BRIDGE_SERVER, "SOURCES")
    assert host == "127.0.0.1" and port == "8791"
    assert rungs == ["meta", "open-weights", "replay", "fallback"]
    block = readme_badges.build_block([], ROOT)
    assert "`127.0.0.1` on port 8791" in block
    assert "one of meta, open-weights, replay, fallback" in block


def test_a_missing_bridge_module_reads_as_missing_and_unread(tmp_path):
    block = readme_badges.build_block([], str(tmp_path))
    assert "(MISSING on this tree)" in block
    assert "unread" in block
    assert readme_badges.read_value(str(tmp_path), readme_badges.BRIDGE_SERVER, "DEFAULT_PORT") is None


# --------------------------------------------------------------------------- the shipped README


def test_the_shipped_readme_carries_both_sections():
    text = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    block = readme_badges.find_block(text)
    assert block is not None
    assert "## NES limits, enforced in code" in block
    assert "## The local AI bridge, in this repo" in block
    assert "`docs/REVIEW-CHECKLIST.md`" in block
    assert "`tools/review_gate.py`" in block
