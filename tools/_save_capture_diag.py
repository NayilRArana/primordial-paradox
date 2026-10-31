"""Find where the game's 256x240 screen sits inside a recorded window frame, by brute force.

Not part of the capture: a measurement tool, like tools/_fade_probe.py, used to set the constant that
tools/capture_save.py compares frames at. It crops 768x720 boxes at every offset in a small grid, brings each down to
64x60 by averaging, and reports the offsets whose pixels differ least from a frame of the room itself.
"""

import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

from PIL import Image, ImageChops  # noqa: E402


def compare(frame, reference, size=(64, 60)):
    crop = frame.resize(size, Image.Resampling.BOX)
    other = reference.resize(size, Image.Resampling.BOX)
    difference = ImageChops.difference(crop, other).convert("L")
    histogram = difference.histogram()
    return sum(histogram[1:]) / float(sum(histogram))


def main():
    if len(sys.argv) < 3:
        print("usage: _save_capture_diag.py <video frame png> <reference png>")
        return 2
    frame_path, reference_path = sys.argv[1], sys.argv[2]
    with Image.open(frame_path) as handle:
        frame = handle.convert("RGB")
    with Image.open(reference_path) as handle:
        reference = handle.convert("RGB")
    print("frame %dx%d, reference %dx%d" % (frame.width, frame.height, reference.width, reference.height))
    results = []
    for top in range(0, 40):
        for left in range(0, 17):
            box = (left, top, left + 768, top + 720)
            if box[2] > frame.width or box[3] > frame.height:
                continue
            results.append((compare(frame.crop(box), reference), left, top))
    results.sort()
    for share, left, top in results[:8]:
        print("offset %2d,%2d  differs by %.5f" % (left, top, share))
    return 0


if __name__ == "__main__":
    sys.exit(main())
