#!/usr/bin/env python3
"""art_b_percy_before_after.py: the before and after sheet for card t_3dfd69d1, Lt. Percy and his three men.

The card asks for "a before and after sheet at 3x in output\\art_b\\ART-B-CHARACTERS\\". This builds it from two
sources and nothing else:

  BEFORE  the sheets the game ships today, read out of git HEAD (never the working tree, so the before cannot
          quietly become the after if somebody reruns the generator first). Percy has his own shipped sheet,
          percy_ow_v2.png. The three men have none: the game ships one sailor sheet, sailor_ow_v2.png, and all
          three men are drawn from it, so that is the before for each of them.
  AFTER   the style B sheets on disk, frame 0 of each, 16 x 24.

Two more files come out beside it, because the card's eye critic reads FRAMES and not strips:

  percy_before_256x240.png   the four shipped figures on one 256 x 240 canvas, 4x nearest
  percy_after_256x240.png    the four style B figures on the same canvas at the same scale and positions

The 4x scale keeps every pixel on the 2C02 palette (nearest neighbour, no resampling), so a critic's opinion of
the frame can be checked against a measurement of the same file.

`output/` is ignored by this repository, so the sheet is also copied to docs/art-b-percy-before-after-3x.png,
which is tracked, and that is the copy a reader of the repository can open.

Usage:
    python tools/art/art_b_percy_before_after.py [--scale 3]
"""
import json
import os
import shutil
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

from art_b_characters_before_after import git_show, label_text  # noqa: E402  the same HEAD reader and font
from make_characters_v2 import TALL_H, TALL_W  # noqa: E402  the cell the after art is drawn in

OUT_DIR = os.path.join(ROOT, "output", "art_b", "ART-B-CHARACTERS")
TRACKED_SHEET = os.path.join(ROOT, "docs", "art-b-percy-before-after-3x.png")
CHARS = "game/sprites_src/chars"
INK = (252, 252, 252)
BACKDROP = (0, 0, 0, 255)

# label, before file at HEAD, before cell, after file on disk, after cell
ROWS = [
    ("LT. PERCY", "percy_ow_v2.png", (16, 16), "percy_ow24.png", (TALL_W, TALL_H)),
    ("PERCY MAN 1", "sailor_ow_v2.png", (16, 16), "percy_man_1_ow24.png", (TALL_W, TALL_H)),
    ("PERCY MAN 2", "sailor_ow_v2.png", (16, 16), "percy_man_2_ow24.png", (TALL_W, TALL_H)),
    ("PERCY MAN 3", "sailor_ow_v2.png", (16, 16), "percy_man_3_ow24.png", (TALL_W, TALL_H)),
]
SHORT = {"LT. PERCY": "PERCY", "PERCY MAN 1": "MAN 1", "PERCY MAN 2": "MAN 2", "PERCY MAN 3": "MAN 3"}


def load(where, cell, from_head):
    """One cell: frame 0 of the named sheet, out of git HEAD or off the disk."""
    if from_head:
        image = git_show(os.path.join(CHARS, where))
    else:
        image = Image.open(os.path.join(ROOT, CHARS, where)).convert("RGBA")
    return image.crop((0, 0, cell[0], cell[1]))


def before_after_sheet(scale):
    cell_w, cell_h = TALL_W * scale, TALL_H * scale
    margin, gap, header_h, label_h = 8 * scale, 8 * scale, 10 * scale, 8
    row_h = cell_h + label_h + gap
    widest = max(len("%s  %dx%d > %dx%d" % (label, cell[0], cell[1], TALL_W, TALL_H))
                 for label, _b, cell, _a, _acell in ROWS)
    width = max(margin * 2 + 2 * cell_w + gap * 2 + gap, widest * 8 + margin * 2)
    height = margin + header_h + len(ROWS) * row_h
    canvas = Image.new("RGBA", (width, height), BACKDROP)
    draw = ImageDraw.Draw(canvas)
    head_scale = max(1, scale // 3)
    for column, word in enumerate(("BEFORE", "AFTER")):
        x = margin + column * (cell_w + gap)
        label_text(draw, word, x + (cell_w - 8 * len(word) * head_scale) // 2, margin, head_scale, INK)
    y = margin + header_h
    rows = []
    for label, before_name, before_cell, after_name, after_cell in ROWS:
        before = load(before_name, before_cell, True)
        after = load(after_name, after_cell, False)
        text = "%s  %dx%d > %dx%d" % (label, before.size[0], before.size[1], after.size[0], after.size[1])
        label_text(draw, text, margin, y, 1, INK)
        top = y + label_h
        # Both columns are bottom aligned and the before is centred in the 24 row cell: a 16 px figure and a 24 px
        # figure standing on the same ground line is the comparison the card is asking for.
        canvas.alpha_composite(before.resize((before.width * scale, before.height * scale), Image.NEAREST),
                               (margin + (cell_w - before.width * scale) // 2, top + cell_h - before.height * scale))
        canvas.alpha_composite(after.resize((after.width * scale, after.height * scale), Image.NEAREST),
                               (margin + cell_w + gap, top + cell_h - after.height * scale))
        rows.append({"label": label, "before": "HEAD:" + before_name, "after": after_name})
        y += row_h
    path = os.path.join(OUT_DIR, "percy_before_after_3x.png")
    canvas.save(path, "PNG")
    return path, rows


def critic_frame(side, scale):
    """The four figures on one 256 x 240 canvas at 4x: the frame the eye critic scores."""
    width, height = 256, 240
    cell_w, cell_h = TALL_W * scale, TALL_H * scale
    gap_x, gap_y = 10, 12
    label_h = 8
    cols = 4
    grid_w = cols * cell_w + (cols - 1) * gap_x
    left = (width - grid_w) // 2
    top = (height - (cell_h + label_h)) // 2
    canvas = Image.new("RGBA", (width, height), BACKDROP)
    draw = ImageDraw.Draw(canvas)
    for index, (label, before_name, before_cell, after_name, after_cell) in enumerate(ROWS):
        cell = load(before_name, before_cell, True) if side == "before" else load(after_name, after_cell, False)
        x = left + index * (cell_w + gap_x)
        label_text(draw, SHORT[label][:7], x + (cell_w - 8 * min(7, len(SHORT[label]))) // 2, top, 1, INK)
        canvas.alpha_composite(cell.resize((cell.width * scale, cell.height * scale), Image.NEAREST),
                               (x + (cell_w - cell.width * scale) // 2, top + label_h + cell_h - cell.height * scale))
    path = os.path.join(OUT_DIR, "percy_%s_256x240.png" % side)
    canvas.save(path, "PNG")
    return path


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    scale = 3
    if "--scale" in argv:
        scale = int(argv[argv.index("--scale") + 1])
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(TRACKED_SHEET), exist_ok=True)
    sheet, rows = before_after_sheet(scale)
    shutil.copyfile(sheet, TRACKED_SHEET)
    before = critic_frame("before", 4)
    after = critic_frame("after", 4)
    report = {
        "card": "t_3dfd69d1",
        "scale": scale,
        "sheet": os.path.relpath(sheet, ROOT),
        "tracked_sheet": os.path.relpath(TRACKED_SHEET, ROOT),
        "before_frame": os.path.relpath(before, ROOT),
        "after_frame": os.path.relpath(after, ROOT),
        "rows": rows,
        "note": "before is read from git HEAD, never from the working tree, so a rerun of the generator cannot "
                "turn the before into the after; the three men share the one sailor sheet the game ships, which "
                "is the sheet they are drawn from",
    }
    with open(os.path.join(OUT_DIR, "percy_before_after.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=1)
        handle.write("\n")
    print("sheet %dx:      %s" % (scale, os.path.relpath(sheet, ROOT)))
    print("tracked copy:   %s" % os.path.relpath(TRACKED_SHEET, ROOT))
    print("before frame:   %s" % os.path.relpath(before, ROOT))
    print("after frame:    %s" % os.path.relpath(after, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
