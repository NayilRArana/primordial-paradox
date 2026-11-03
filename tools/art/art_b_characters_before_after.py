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
    ("ZEUS", "HEAD:" + CHARS + "/zander_ow_v2.png", (16, 16), "zeus_ow_walk8.png", (16, 16)),
    ("KRONOS", "HEAD:" + CHARS + "/konrad_ow_v2.png", (16, 16), "kronos_ow24.png", (16, 24)),
    ("LT. PERCY", "HEAD:" + CHARS + "/percy_ow_v2.png", (16, 16), "percy_ow24.png", (16, 24)),
    ("PERCY MAN 1", "HEAD:" + CHARS + "/sailor_ow_v2.png", (16, 16), "percy_man_1_ow24.png", (16, 24)),
    ("PERCY MAN 2", "HEAD:" + CHARS + "/sailor_ow_v2.png", (16, 16), "percy_man_2_ow24.png", (16, 24)),
    ("PERCY MAN 3", "HEAD:" + CHARS + "/sailor_ow_v2.png", (16, 16), "percy_man_3_ow24.png", (16, 24)),
    ("OURANOS", "disk:output/art_candidates_r18/cast/kept/ouranos_ow_t2i_seed141_cell.png", (16, 24),
     "ouranos_ow24.png", (16, 24)),
]

DIRECTIONS = ("down", "down_left", "left", "up_left", "up", "up_right", "right", "down_right")

# Card t_760a7325. The R18 row kept two candidates; the pack's OURANOS row shows the rank 2 one (seed 141), so a
# per asset comparison has to be able to show the rank 1 one (seed 142) as its own frame. Using a candidate is only
# allowed by the card "if one is genuinely better", and a score is how that gets decided rather than a memory.
R18_CANDIDATES = {
    "OURANOS": [
        ("R18 seed141 (rank 2, the pack's before)",
         "disk:output/art_candidates_r18/cast/kept/ouranos_ow_t2i_seed141_cell.png", (16, 24)),
        ("R18 seed142 (rank 1)",
         "disk:output/art_candidates_r18/cast/cells/ouranos_ow_t2i_seed142_cell.png", (16, 24)),
    ],
}

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


def find_row(label):
    for row in ROWS:
        if row[0] == label:
            return row
    raise SystemExit("no ROWS entry labelled %r; the labels are %s" % (label, ", ".join(r[0] for r in ROWS)))


def per_asset_sheet(label, scale):
    """One character, before and after, at 3x with a 1x copy under each: the per asset sheet the card asks for.

    The scale is 3 because the card names 3x, and the 1x copy is under every 3x because a 3x copy can flatter a
    drawing that disappears at the size the game actually runs it. The rank 1 R18 candidate sits in the middle
    column, so a reader can see the third option the card allows instead of reading a claim about it.
    """
    _label, before_path, before_cell, after_name, after_cell = find_row(label)
    columns = [("BEFORE", load(before_path, before_cell))]
    columns += [(text, load(path, cell)) for text, path, cell in R18_CANDIDATES.get(label, [])]
    columns.append(("AFTER", load(after_name, after_cell)))
    cell_w, cell_h = 16 * scale, 24 * scale
    margin, gap, header_h, label_h = 8, 16, 10, 8
    width = margin * 2 + len(columns) * cell_w + (len(columns) - 1) * gap
    height = margin * 2 + header_h + cell_h + label_h + cell_h + label_h
    canvas = Image.new("RGBA", (width, height), BACKDROP)
    draw = ImageDraw.Draw(canvas)
    for index, (text, image) in enumerate(columns):
        x = margin + index * (cell_w + gap)
        label_text(draw, text[:24], x, margin, 1, INK)
        top = margin + header_h
        canvas.alpha_composite(image.resize((cell_w, cell_h), Image.NEAREST), (x, top))
        label_text(draw, "3X", x, top + cell_h + 1, 1, INK)
        small_top = top + cell_h + label_h
        canvas.alpha_composite(image.convert("RGBA"), (x, small_top))
        label_text(draw, "1X", x, small_top + 24, 1, INK)
    path = os.path.join(OUT_DIR, "%s_before_after_3x.png" % label.lower().replace(" ", "_").replace(".", ""))
    canvas.save(path, "PNG")
    return path, [text for text, _image in columns]


def per_asset_frame(label, side, scale_max=4):
    """One 256 x 240 frame holding one figure at 1x, 2x, 3x and 4x, labelled, for the eye critic.

    The pack's frames hold seven figures at 3x and the critic scored a roster there. This is the same question asked
    of one character: the 1x copy is the shipping truth and the three larger ones are there so the critic can name
    what it thinks it can see. Nothing is upsampled with any filter, so the palette it is asked about is the art's.
    """
    _label, before_path, before_cell, after_name, after_cell = find_row(label)
    if side == "before":
        image = load(before_path, before_cell)
    elif side.startswith("r18"):
        candidates = {text.split()[1]: (path, cell) for text, path, cell in R18_CANDIDATES.get(label, [])}
        key = side.replace("r18_", "")
        image = load(*candidates[key])
    else:
        image = load(after_name, after_cell)
    width, height = 256, 240
    canvas = Image.new("RGBA", (width, height), BACKDROP)
    draw = ImageDraw.Draw(canvas)
    scales = [1, 2, 3, scale_max]
    total = sum(16 * s for s in scales) + 12 * (len(scales) - 1)
    x = (width - total) // 2
    for s in scales:
        cell = image.resize((16 * s, 24 * s), Image.NEAREST)
        base = height - 40
        canvas.alpha_composite(cell, (x, base - cell.height))
        label_text(draw, "%dX" % s, x, base + 4, 1, INK)
        x += cell.width + 12
    label_text(draw, FRAME_SHORT.get(label, label)[:16], (width - 8 * min(16, len(label))) // 2, 16, 2, INK)
    path = os.path.join(OUT_DIR, "%s_%s_frame_256x240.png"
                        % (label.lower().replace(" ", "_").replace(".", ""), side))
    canvas.save(path, "PNG")
    return path


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    scale = 3
    if "--scale" in argv:
        scale = int(argv[argv.index("--scale") + 1])
    os.makedirs(OUT_DIR, exist_ok=True)
    if "--asset" in argv:
        label = argv[argv.index("--asset") + 1].upper()
        sheet, columns = per_asset_sheet(label, scale)
        print("%s sheet %dx: %s" % (label, scale, os.path.relpath(sheet, ROOT)))
        print("  columns: " + " | ".join(columns))
        for side in ["before"] + ["r18_" + text.split()[1] for text, _p, _c in R18_CANDIDATES.get(label, [])
                                  ] + ["after"]:
            print("  frame:      " + os.path.relpath(per_asset_frame(label, side, scale_max=scale + 1), ROOT))
        return 0
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
