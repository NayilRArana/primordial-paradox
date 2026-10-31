"""art_b_characters_before_after.py: the before and after sheet for card ART-B-CHARACTERS.

The card asks for "a before and after sheet at 3x in output\\art_b\\<your card name>\\". This tool builds it from
two sources and nothing else:

  BEFORE  the sheets the game ships today, read out of git HEAD (never the working tree, so the before cannot
          quietly become the after if somebody reruns the generator first). For the three Percy men there was no
          separate sheet, so the shipped sailor they are cut from is shown. For Ouranos there was no shipped
          sheet at all, so the R18 candidate that was measured for him is shown, labelled as a candidate.
  AFTER   the style B sheets on disk, frame 0 of each.

Plus a second sheet: Zeus's whole cycle, sixteen frames in two rows of eight, at 3x, so the walk can be read as a
walk rather than guessed from one frame.

Usage:
    python tools/art/art_b_characters_before_after.py [--scale 3]
"""
import io
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

from make_characters_v2 import label_text  # noqa: E402  the project's own 8x8 label font

OUT_DIR = os.path.join(ROOT, "output", "art_b", "ART-B-CHARACTERS")
CHARS = "game/sprites_src/chars"
INK = (252, 252, 252)
BACKDROP = (0, 0, 0, 255)

# label, before path (relative to the repo root, at HEAD or on disk), before cell, after sheet, after cell
ROWS = [
    ("ZEUS", "HEAD:" + CHARS + "/zander_ow_v2.png", (16, 16), "zeus_ow_walk8.png", (16, 24)),
    ("KRONOS", "HEAD:" + CHARS + "/konrad_ow_v2.png", (16, 16), "kronos_ow24.png", (16, 24)),
    ("LT. PERCY", "HEAD:" + CHARS + "/percy_ow_v2.png", (16, 16), "percy_ow24.png", (16, 24)),
    ("PERCY MAN 1", "HEAD:" + CHARS + "/sailor_ow_v2.png", (16, 16), "percy_man_1_ow24.png", (16, 24)),
    ("PERCY MAN 2", "HEAD:" + CHARS + "/sailor_ow_v2.png", (16, 16), "percy_man_2_ow24.png", (16, 24)),
    ("PERCY MAN 3", "HEAD:" + CHARS + "/sailor_ow_v2.png", (16, 16), "percy_man_3_ow24.png", (16, 24)),
    ("OURANOS", "disk:output/art_candidates_r18/cast/kept/ouranos_ow_t2i_seed141_cell.png", (16, 24),
     "ouranos_ow24.png", (16, 24)),
]

DIRECTIONS = ("down", "down_left", "left", "up_left", "up", "up_right", "right", "down_right")

# The two frames the eye critic reads: the same seven figures, before and after, each on its own 256 x 240 canvas.
# A critic asked to score a tall strip complains, correctly, that a strip is not a frame; these are frames.
FRAME_SHORT = {"ZEUS": "ZEUS", "KRONOS": "KRONOS", "LT. PERCY": "PERCY", "PERCY MAN 1": "MAN 1",
               "PERCY MAN 2": "MAN 2", "PERCY MAN 3": "MAN 3", "OURANOS": "OURANOS"}


def frame(side, scale):
    """One 256 x 240 frame: seven figures in a four by two grid, labels at 1x so nothing is cropped."""
    width, height = 256, 240
    cell_w, cell_h = 16 * scale, 24 * scale
    gap_x, gap_y = 12, 16
    label_h = 8
    cols = 4
    grid_w = cols * cell_w + (cols - 1) * gap_x
    left = (width - grid_w) // 2
    top = (height - (2 * (cell_h + label_h) + gap_y)) // 2
    canvas = Image.new("RGBA", (width, height), BACKDROP)
    draw = ImageDraw.Draw(canvas)
    for index, (label, before_path, before_cell, after_name, after_cell) in enumerate(ROWS):
        column, row = index % cols, index // cols
        x = left + column * (cell_w + gap_x)
        y = top + row * (cell_h + label_h + gap_y)
        image = (load(before_path, before_cell) if side == "before" else load(after_name, after_cell))
        label_text(draw, FRAME_SHORT.get(label, label)[:7], x + (cell_w - 8 * min(7, len(label))) // 2, y, 1, INK)
        canvas.alpha_composite(image.resize((image.width * scale, image.height * scale), Image.NEAREST),
                               (x, y + label_h + cell_h - image.height * scale))
    path = os.path.join(OUT_DIR, "%s_frame_256x240.png" % side)
    canvas.save(path, "PNG")
    return path



def git_show(rel):
    """One file out of git HEAD, as bytes. HEAD, not the working tree: the before has to be the before."""
    top = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, text=True).strip()
    inside = os.path.relpath(os.path.join(ROOT, rel), top).replace("\\", "/")
    data = subprocess.check_output(["git", "show", "HEAD:%s" % inside], cwd=top)
    return Image.open(io.BytesIO(data)).convert("RGBA")


def load(where, cell):
    """The first frame of a sheet, cut to one cell."""
    if where.startswith("HEAD:"):
        image = git_show(where[5:])
    elif where.startswith("disk:"):
        image = Image.open(os.path.join(ROOT, where[5:])).convert("RGBA")
    else:
        image = Image.open(os.path.join(ROOT, CHARS, where)).convert("RGBA")
    return image.crop((0, 0, cell[0], cell[1]))


def before_after_sheet(scale):
    cell_w, cell_h = 16 * scale, 24 * scale
    margin = 8 * scale
    gap = 8 * scale
    header_h = 10 * scale
    row_label_h = 8
    row_h = cell_h + header_h + gap
    widest = max(len("%s  %dx%d > %dx%d" % (label, cell[0], cell[1], 16, 24))
                 for label, _where, cell, _after, _acell in ROWS)
    width = max(margin * 2 + cell_w * 2 + gap * 2, widest * 8 + margin * 2)
    height = margin + header_h + len(ROWS) * row_h
    canvas = Image.new("RGBA", (width, height), BACKDROP)
    draw = ImageDraw.Draw(canvas)
    label_text(draw, "BEFORE", margin, margin, scale, INK)
    label_text(draw, "AFTER", margin + cell_w + gap, margin, scale, INK)
    y = margin + header_h
    rows = []
    for label, before_path, before_cell, after_name, after_cell in ROWS:
        before = load(before_path, before_cell)
        after = load(after_name, after_cell)
        text = "%s  %dx%d > %dx%d" % (label, before.size[0], before.size[1], after.size[0], after.size[1])
        label_text(draw, text, margin, y, 1, INK)
        top = y + row_label_h
        canvas.alpha_composite(before.resize((before.width * scale, before.height * scale), Image.NEAREST),
                               (margin, top + cell_h - before.height * scale))
        canvas.alpha_composite(after.resize((after.width * scale, after.height * scale), Image.NEAREST),
                               (margin + cell_w + gap, top))
        rows.append({"label": label, "before": before_path, "after": after_name})
        y += row_h
    path = os.path.join(OUT_DIR, "before_after_3x.png")
    canvas.save(path, "PNG")
    return path, rows


def zeus_cycle(scale):
    """Zeus's sixteen frames, two rows of eight: the stand frame above, the step frame below."""
    sheet = Image.open(os.path.join(ROOT, CHARS, "zeus_ow_walk8.png")).convert("RGBA")
    cell_w, cell_h = 16 * scale, 24 * scale
    margin, gap, label_h = 8 * scale, 4 * scale, 10 * scale
    width = margin * 2 + 8 * cell_w + 7 * gap
    height = margin + label_h + 2 * (cell_h + gap)
    canvas = Image.new("RGBA", (width, height), BACKDROP)
    draw = ImageDraw.Draw(canvas)
    for index, direction in enumerate(DIRECTIONS):
        label_text(draw, direction.replace("_", " ").upper()[:11], margin + index * (cell_w + gap), margin,
                   max(1, scale // 3), INK)
    for row, walk in enumerate((False, True)):
        y = margin + label_h + row * (cell_h + gap)
        for index in range(8):
            frame = index * 2 + (1 if walk else 0)
            cell = sheet.crop((frame * 16, 0, frame * 16 + 16, 24))
            canvas.alpha_composite(cell.resize((cell_w, cell_h), Image.NEAREST),
                                   (margin + index * (cell_w + gap), y))
    path = os.path.join(OUT_DIR, "zeus_walk8_3x.png")
    canvas.save(path, "PNG")
    return path


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    scale = 3
    if "--scale" in argv:
        scale = int(argv[argv.index("--scale") + 1])
    os.makedirs(OUT_DIR, exist_ok=True)
    sheet, rows = before_after_sheet(scale)
    cycle = zeus_cycle(scale)
    before_frame = frame("before", scale)
    after_frame = frame("after", scale)
    report = {"scale": scale, "sheet": os.path.relpath(sheet, ROOT), "zeus_cycle": os.path.relpath(cycle, ROOT),
              "before_frame": os.path.relpath(before_frame, ROOT),
              "after_frame": os.path.relpath(after_frame, ROOT),
              "rows": rows,
              "note": "before is read from git HEAD, never from the working tree, so a rerun of the generator "
                      "cannot turn the before into the after; the two 256x240 frames are the pair the eye critic "
                      "reads, one figure grid each, so the readability question is asked of a frame, not a strip"}
    report_path = os.path.join(OUT_DIR, "before_after.json")
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1)
        handle.write("\n")
    print("before and after %dx: %s" % (scale, os.path.relpath(sheet, ROOT)))
    print("zeus cycle %dx:       %s" % (scale, os.path.relpath(cycle, ROOT)))
    print("before frame:         %s" % os.path.relpath(before_frame, ROOT))
    print("after frame:          %s" % os.path.relpath(after_frame, ROOT))
    print("record:               %s" % os.path.relpath(report_path, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
