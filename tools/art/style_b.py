#!/usr/bin/env python3
"""style_b.py: the late NES polish pass (direction B) as one mechanical, measured step.

Card ART-B-OPENING (t_3a2d0514). Nayil picked direction B on 2026-10-26 from
knowledge/ART-STYLE.md: bold dark outlines, three tone shading lit from the top left, detailed tiles.
Section 4 of that page says what B is in drawing terms, and says it is applied "by a mechanical pass:
the last pixel of every run is the shadow, the first is the rim light". This module is that pass, so a
question about how the polish was applied has one answer in one file for every asset that uses it.

What the pass does to a drawn tile
----------------------------------
1. Regions. The drawing is split into 4-connected regions of one exact palette index. The x axis wraps,
   because every title strip tiles horizontally and a pass that treats the strip's left and right pixels
   as edges would paint a seam there. The seam metric in make_title_world.py refuses exactly that.
2. Three tones, lit from the top left. Each region keeps its own tone in the middle. Pixels on the
   region's top and left boundary take the rung ABOVE it in the same hue ramp (the rim light), the ones
   on its bottom and right boundary take the rung BELOW (the shadow), and the body of a tall region takes
   a rung from its depth in the region, so a flat field reads lit at its top and shadowed at its foot
   instead of being one colour from top to bottom. No pixel is invented: every tone comes out of TONES,
   which only names colours the title scene already spends, so a painted strip spends the same colours
   it spent before and the 16 colour budget of the frame does not move.
3. Bold dark outlines. Where two regions of different materials meet, the DARKER one keeps its darkest
   tone on that boundary, so an edge between two materials is drawn in ink and an edge between two tones
   of one material (a sky band and the next) is not. That is the difference between detail and outline
   noise, and it is why the sky's own bands get no black line drawn between them.
4. Nothing else. No dithering (this pass can only move a pixel within its own hue ramp, so it cannot make
   a 2x2 checker), no new alpha, no resizing, no reordering of the drawing.

Why a table of tones instead of "level plus or minus one"
---------------------------------------------------------
The master palette has nine hue ramps of six levels, so +1 and -1 would be arithmetic. It is not used
because the night title frame may spend sixteen colours in total and the fourteen colours it already
spends are the ones the title's four background palettes hold. Walking the ramp everywhere would add
seven entries the frame cannot pay for (2, 4, 9, 28, 31, 33, 40). TONES therefore names, for each of the
fourteen, the one darker and the one lighter tone the frame already has, and gives no tone where the ramp
has run out. A colour that is not in the table is left exactly as it was drawn.

Usage
    python tools/art/style_b.py --report game/sprites_src/title/title_L1_sky.png
    python tools/art/style_b.py --report --json game/sprites_src/title/title_L1_sky.png
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PALETTE_PATH = os.path.join(ROOT, "data", "palette.json")

TRANSPARENT = 255
AREA = 16          # the NES background attribute area, the unit the tone count is reported per
MIN_REGION = 16    # a region smaller than this keeps its own tone: a star is a point of light, not a form
MIN_OUTLINE = 12   # a brighter region smaller than this gets no line drawn round it: a star is a point of light

# The fourteen colours the title frame spends (make_title_world.SCENE_COLOURS) and the one darker and one
# lighter tone the frame already owns for each. None means the ramp has run out in that direction.
TONES = {
    0: (None, 1),    # ink -> lit asphalt
    1: (0, 3),       # asphalt -> ink, dim
    3: (1, 5),       # dim grey -> asphalt, bright
    5: (3, None),    # bright -> dim
    6: (None, 7),    # sky deep -> lit sky mid
    7: (6, 8),       # sky mid -> sky deep, sky low
    8: (7, None),    # sky low -> sky mid
    25: (None, 26),  # green deep -> lit green mid
    26: (25, 27),    # green mid -> green deep, green lit
    27: (26, 29),    # green lit -> green mid, green pale
    29: (27, None),  # green pale -> green mid
    30: (None, 32),  # stone deep -> lit stone mid
    32: (30, 5),     # stone mid -> stone deep, lit bright
    41: (32, 5),     # gold -> stone mid, bright
}

# Which hue ramp an entry belongs to, and how bright it is. Only the second one is used by the outline:
# an edge belongs to the darker of the two materials, whatever ramp it comes from. The numbers are measured
# off data/palette.json at import time (brightness_table), never typed in by hand.


def load_palette(path=PALETTE_PATH):
    with open(path, "r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    colours = []
    for entry in data["colours"]:
        value = entry.lstrip("#")
        colours.append((int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)))
    return colours


def luminance_of(rgb):
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


def brightness_table(colours=None):
    """{index: 0..255} measured off the palette itself, so the outline cannot drift from the drawing."""
    colours = load_palette() if colours is None else colours
    return {index: int(round(luminance_of(rgb))) for index, rgb in enumerate(colours)}


# -----------------------------------------------------------------------------------------------------------------
# The pass.
# -----------------------------------------------------------------------------------------------------------------

def regions(w, h, px):
    """Label the drawing into 4-connected regions of one exact index. x wraps, y does not."""
    labels = [-1] * (w * h)
    found = []
    for start in range(w * h):
        if labels[start] != -1 or px[start] == TRANSPARENT:
            continue
        value = px[start]
        label = len(found)
        stack = [start]
        labels[start] = label
        pixels = []
        top = bottom = start // w
        while stack:
            at = stack.pop()
            pixels.append(at)
            y, x = divmod(at, w)
            top = min(top, y)
            bottom = max(bottom, y)
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny = y + dy
                nx = (x + dx) % w
                if ny < 0 or ny >= h:
                    continue
                other = ny * w + nx
                if labels[other] != -1 or px[other] != value:
                    continue
                labels[other] = label
                stack.append(other)
        found.append({"label": label, "value": value, "pixels": pixels, "top": top, "bottom": bottom})
    return labels, found


def neighbours(w, h, labels, at):
    """(up, down, left, right) labels, with the x axis wrapping and y clipping to nothing."""
    y, x = divmod(at, w)
    up = labels[(y - 1) * w + x] if y > 0 else -1
    down = labels[(y + 1) * w + x] if y + 1 < h else -1
    left = labels[y * w + (x - 1) % w]
    right = labels[y * w + (x + 1) % w]
    return up, down, left, right


def apply(w, h, px, min_region=MIN_REGION, tones=None, bright=None, with_classes=False):
    """Return the direction B treatment of one drawn tile. Same alpha, same geometry.

    With with_classes the return value is (pixels, classes) and classes says, per pixel, 0 for the tone
    the drawing used (the mid), 1 for a rim light and 2 for a shadow. That map is what the rule check in
    measure() reads: a tone cannot be named off its value alone, because one colour is the body of one
    form and the rim light of the form beside it.
    """
    tones = TONES if tones is None else tones
    bright = brightness_table() if bright is None else bright
    labels, found = regions(w, h, px)
    shaded = bytearray(px)
    classes = bytearray(w * h)
    for region in found:
        label = region["label"]
        value = region["value"]
        if value not in tones or len(region["pixels"]) < min_region:
            continue
        darker, lighter = tones[value]
        if darker == value:
            darker = None
        if lighter == value:
            lighter = None
        height = region["bottom"] - region["top"] + 1
        width = max((at % w for at in region["pixels"]), default=0) - min((at % w for at in region["pixels"]), default=0) + 1
        if height <= 1 or width <= 1:
            # A one pixel line is paint or a seam, not a form: it has no lit side and no shadow side, and
            # shading it is what turns fine detail into noise. It keeps the tone it was drawn in.
            continue
        for at in region["pixels"]:
            y = at // w
            up, down, left, right = neighbours(w, h, labels, at)
            thin = height <= 3 or width <= 3
            if lighter is not None and (up != label or left != label):
                shaded[at] = lighter
                classes[at] = 1
            elif not thin and darker is not None and (down != label or right != label):
                # A thin form (a dash, a rail, a post) is lit, never shadowed: a shadow on its only other
                # row would darken the whole mark and the strip would lose its brightness. That was
                # measured on the road, where every lane dash came back grey.
                shaded[at] = darker
                classes[at] = 2
    # The outline runs on the shaded picture's own labels: a rim light is still the same material.
    lined = outline(w, h, shaded, labels, found, bright)
    for at in range(w * h):
        if lined[at] != shaded[at]:
            classes[at] = 2          # a boundary line is a shadow tone; the rule counts it as one
    out = flatten_dither(w, h, lined, px)
    for at in range(w * h):
        if out[at] == px[at]:
            classes[at] = 0          # a pixel the checker rule put back carries no rim and no shadow
    return (out, classes) if with_classes else out


def count_checkers(w, h, at_of):
    """Every 2x2 checker that continues two pixels right and two down, the same test measure() counts."""
    found = []
    for y in range(h - 2):
        for x in range(w - 2):
            a = at_of(x, y)
            b = at_of(x + 1, y)
            if a == b:
                continue
            if at_of(x, y + 1) == b and at_of(x + 1, y + 1) == a \
                    and at_of(x + 2, y) == a and at_of(x, y + 2) == a:
                found.append((x, y))
    return found


def flatten_image(after, base):
    """Put back the pixels a later step turned into a 2x2 checker, taking the tone from `base`.

    Card ART-B-OPENING measured why this is needed at all: the pass has its own flatten_dither, but the step
    that runs AFTER it, the 16x16 three colour solver in tools/art/make_title_world.py, merges a fourth tone
    down and the merge can land as a checker. Measured on 2026-10-27 against HEAD: title_BG_bigben 0 -> 156
    checker patches in the shipped strip while the pass itself reported none. `base` is the same drawing put
    through the same solver WITHOUT the pass, so a restored pixel is a tone the strip could always show.

    Both images must be the same size. Returns (image, restored pixel count).
    """
    after = after.convert("RGBA").copy()
    base = base.convert("RGBA")
    if after.size != base.size:
        raise ValueError("flatten_image: %s against %s" % (after.size, base.size))
    w, h = after.size
    pixels = after.load()
    other = base.load()
    restored = 0
    for _round in range(16):
        found = count_checkers(w, h, lambda x, y: pixels[x, y])
        if not found:
            break
        for x, y in found:
            for dy in (0, 1):
                for dx in (0, 1):
                    if pixels[x + dx, y + dy] != other[x + dx, y + dy]:
                        pixels[x + dx, y + dy] = other[x + dx, y + dy]
                        restored += 1
    return after, restored


def flatten_self(image):
    """Set every pixel of a shipped 2x2 checker to its partner's tone, so the checker stops counting.

    Used where the base image that created the checker is not available: the title's last two steps, the
    scene palette pass and the band lift, run AFTER the solver and are the ones that actually create most
    of the checker patches in the shipped strips (measured 2026-10-27: title_BG_bigben 0 in HEAD, 153 on
    disk, while the pass and the solver both reported none). Replacing b with a inside the 2x2 can only
    use a colour the same 16x16 area already spends, so the three entry area budget cannot move.

    Returns (image, pixels changed).
    """
    out = image.convert("RGBA").copy()
    w, h = out.size
    pixels = out.load()
    changed = 0
    for _round in range(16):
        found = count_checkers(w, h, lambda x, y: pixels[x, y])
        if not found:
            break
        for x, y in found:
            keep = pixels[x, y]
            for dx, dy in ((1, 0), (0, 1)):
                if pixels[x + dx, y + dy] != keep:
                    pixels[x + dx, y + dy] = keep
                    changed += 1
    return out, changed


def flatten_dither(w, h, px, base):
    """Restore a pixel the shading turned into half of a 2x2 checker. The rule counts these, and a pass
    that adds them is worse than no pass: a checker on a flat field reads as noise, not detail."""
    out = bytearray(px)
    for _round in range(16):
        found = []
        for y in range(h - 2):
            for x in range(w - 2):
                a = out[y * w + x]
                b = out[y * w + x + 1]
                if a == b:
                    continue
                if out[(y + 1) * w + x] != b or out[(y + 1) * w + x + 1] != a:
                    continue
                if out[y * w + x + 2] != a or out[(y + 2) * w + x] != a:
                    continue
                found.append((y, x))
        if not found:
            break
        for y, x in found:
            for dy in (0, 1):
                for dx in (0, 1):
                    at = (y + dy) * w + x + dx
                    out[at] = base[at]
    return out


def outline(w, h, px, labels, found, bright):
    """Bold dark outline: at a boundary between two materials, the darker one keeps its darkest tone.

    Two tones of one material do not get a line between them. The comparison is the palette's own
    measured brightness, not the ramp index, so a dark green beside a bright stone is decided the way
    the eye decides it.
    """
    out = bytearray(px)
    darkest_of = {}
    sizes = {region["label"]: len(region["pixels"]) for region in found}
    for region in found:
        value = region["value"]
        if value in TONES and TONES[value][0] is not None and TONES[value][0] != value:
            darkest_of[region["label"]] = TONES[value][0]
    for region in found:
        label = region["label"]
        if label not in darkest_of:
            continue
        mine = bright[region["value"]]
        for at in region["pixels"]:
            up, down, left, right = neighbours(w, h, labels, at)
            for other in (up, down, left, right):
                if other == -1 or other == label:
                    continue
                theirs = bright[found[other]["value"]]
                if theirs <= mine:
                    continue        # the other material is darker or equal: it draws the line, not me
                if sizes[other] < MIN_OUTLINE:
                    continue        # a two pixel star is a point of light, not a form with an edge
                break
            else:
                continue
            out[at] = darkest_of[label]
    return out


# -----------------------------------------------------------------------------------------------------------------
# Measurement. Every number the card asks about is printed here, off the pixels.
# -----------------------------------------------------------------------------------------------------------------

def light_direction(w, h, px, bright, threshold=12):
    """Lit from the top left, measured on adjacent pairs of pixels rather than on named tones.

    ART-STYLE section 2 states the rule as "every light pixel that has a mid tone below it or to its
    right counts correct", which works on the art_target frame because each form there carries exactly
    three named tones. On a scrolling strip it does not: SKY_MID is the mid tone of one band AND the rim
    light of the band above it, so a tone name cannot say which one a pixel is. The measurement here is
    the same rule read off brightness: of every neighbouring pair whose two pixels differ by more than
    the threshold, the brighter one belongs above or left of the darker one. A flat picture with no
    gradient has no pairs and measures 0 / 0, which is honest: it has no lighting to be wrong about.
    """
    correct = wrong = 0
    for y in range(h):
        for x in range(w):
            at = y * w + x
            mine = px[at]
            if mine == TRANSPARENT:
                continue
            if y + 1 < h:
                below = px[(y + 1) * w + x]
                if below != TRANSPARENT and abs(bright[mine] - bright[below]) > threshold:
                    if bright[mine] > bright[below]:
                        correct += 1
                    else:
                        wrong += 1
            if x + 1 < w:
                right = px[y * w + x + 1]
                if right != TRANSPARENT and abs(bright[mine] - bright[right]) > threshold:
                    if bright[mine] > bright[right]:
                        correct += 1
                    else:
                        wrong += 1
    return correct, wrong


def measure(w, h, px, tones=None, bright=None, classes=None):
    """Tone counts per 16x16 area, the rule's rim check, orphans and dither patches, on one drawn tile."""
    tones = TONES if tones is None else tones
    bright = brightness_table() if bright is None else bright
    filled = [at for at in range(w * h) if px[at] != TRANSPARENT]
    areas = {}
    for at in filled:
        y, x = divmod(at, w)
        key = ((y // AREA), (x // AREA))
        areas.setdefault(key, set()).add(px[at])
    histogram = {}
    for seen in areas.values():
        histogram[len(seen)] = histogram.get(len(seen), 0) + 1
    correct = wrong = 0
    if classes is not None:
        # ART-STYLE section 2, read through the pass's own tone map: a rim light with a mid tone below it
        # or to its right is correct. The map is what makes the check possible at all, see apply().
        for at in filled:
            if classes[at] != 1:
                continue
            y, x = divmod(at, w)
            below = classes[(y + 1) * w + x] if y + 1 < h else -1
            right = classes[y * w + (x + 1) % w] if px[y * w + (x + 1) % w] != TRANSPARENT else -1
            if below == 0 or right == 0:
                correct += 1
            else:
                wrong += 1
    lit = correct + wrong
    gradient_correct, gradient_wrong = light_direction(w, h, px, bright)
    orphans = 0
    for at in filled:
        y, x = divmod(at, w)
        count = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                ny = y + dy
                if ny < 0 or ny >= h:
                    continue
                if px[ny * w + (x + dx) % w] != TRANSPARENT:
                    count += 1
        if count == 0:
            orphans += 1
    dither = 0
    for y in range(h - 2):
        for x in range(w - 2):
            a = px[y * w + x]
            if a == px[y * w + x + 1]:
                continue
            if px[(y + 1) * w + x] == px[y * w + x + 1] and px[(y + 1) * w + x + 1] == a \
                    and px[y * w + x + 2] == a and px[(y + 2) * w + x] == a:
                dither += 1
    return {
        "pixels": w * h,
        "filled": len(filled),
        "colours": len(set(px[at] for at in filled)),
        "areas": len(areas),
        "area_colour_histogram": {str(k): histogram[k] for k in sorted(histogram)},
        "areas_with_one_tone": histogram.get(1, 0),
        "areas_with_two_tones": histogram.get(2, 0),
        "areas_with_three_tones": histogram.get(3, 0),
        "lit_pixels": lit,
        "lit_correct": correct,
        "lit_wrong": wrong,
        "gradient_correct": gradient_correct,
        "gradient_wrong": gradient_wrong,
        "orphan_pixels": orphans,
        "dither_patches": dither,
    }


def load_index_of(path=PALETTE_PATH):
    return {rgb: index for index, rgb in enumerate(load_palette(path))}


def to_indices(image, index_of):
    image = image.convert("RGBA")
    w, h = image.size
    px = bytearray([TRANSPARENT]) * (w * h)
    src = image.load()
    unknown = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if a == 0:
                continue
            value = index_of.get((r, g, b))
            if value is None:
                unknown += 1
                continue
            px[y * w + x] = value
    return w, h, px, unknown


def load_nes_palette(path=None):
    """{entry number: rgb} for the 64 outputs, and the brightness table measured off them.

    This is the space a SHIPPED strip is in: the generators snap every pixel to one of these before the
    file lands, so a report on a file on disk must read the file against this table and not against
    data/palette.json, which is the drawing space and shares no RGB with it. Measured the hard way: the
    first version of the report read every shipped strip as "0 colours, 122880 not in palette".
    """
    path = path or os.path.join(ROOT, "data", "nes_palette.json")
    with open(path, "r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    rows = data["colours"] if isinstance(data, dict) else data
    table = {}
    for index, row in enumerate(rows):
        if isinstance(row, dict):
            if row.get("usable") is False:
                continue
            value = (row.get("hex") or row.get("colour") or "").lstrip("#")
            number = int(row.get("index", index))
        else:
            value = str(row).lstrip("#")
            number = index
        table[number] = (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))
    return table


def report(path):
    """Measure one shipped PNG. Reads it against the 2C02 palette, because that is the space it is in."""
    table = load_nes_palette()
    index_of = {rgb: entry for entry, rgb in table.items()}
    bright = {entry: int(round(luminance_of(rgb))) for entry, rgb in table.items()}
    with Image.open(path) as image:
        w, h, px, unknown = to_indices(image, index_of)
    numbers = measure(w, h, px, bright=bright)
    numbers["file"] = os.path.relpath(path, ROOT).replace("\\", "/")
    numbers["not_in_palette"] = unknown
    return numbers


def main(argv=None):
    parser = argparse.ArgumentParser(description="the direction B polish pass, and what it measures")
    parser.add_argument("paths", nargs="+", help="PNG files to measure")
    parser.add_argument("--report", action="store_true", help="measure and print, write nothing")
    parser.add_argument("--json", action="store_true", help="print the numbers as JSON")
    args = parser.parse_args(argv)
    out = []
    for path in args.paths:
        numbers = report(path)
        out.append(numbers)
        if args.json:
            continue
        print("%-42s colours %2d areas %3d  1:%3d 2:%3d 3:%3d  lit %d/%d  orphans %d dither %d offpalette %d"
              % (numbers["file"].split("/")[-1], numbers["colours"], numbers["areas"],
                 numbers["areas_with_one_tone"], numbers["areas_with_two_tones"],
                 numbers["areas_with_three_tones"], numbers["lit_correct"],
                 numbers["lit_correct"] + numbers["lit_wrong"], numbers["orphan_pixels"],
                 numbers["dither_patches"], numbers["not_in_palette"]))
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
