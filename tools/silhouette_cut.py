#!/usr/bin/env python3
"""silhouette_cut.py: turn a recorded sam-3.1 answer into a cut out PNG (card META-MODEL-BREADTH).

What it does
============
The demo's fourth Meta model use is a silhouette cut: one image, one noun phrase, and the object
the model segmented comes back as a PNG with an alpha channel, ready to drop on a plate. The
model's answer is not an image (it is the token grammar sam-3.1 returns, decoded by
tools\\sam_mask.py), and the cut is not a guess: every pixel that is opaque is a pixel the mask the
model sent has set, placed at the box the same answer returned.

    python tools\\silhouette_cut.py --image output\\art_audit_2026-10-26\\frames\\concept_sdxl.png \\
        --prompt ship --out knowledge\\silhouette_cut\\ship_cut.png

The call goes through tools\\meta_client.py, so it is cached, keyed and replayed exactly like every
other Meta call in this repository: PP_AI_MODE=replay (the default here) reads a committed entry
and never opens a socket, and an entry that is missing is a CacheMiss rather than a fresh call.

What it refuses
===============
- An answer with zero records. Zero is a documented valid outcome for sam-3.1, so a cut is not
  written and the tool says the model found no object, instead of writing a full frame cut.
- A mask whose decoded size is not its box's size, or a cut whose alpha bounding box escapes the
  box. Either means the decoder and the answer disagree, and a cut that is not the model's mask is
  worse than no cut.
- A PNG this reader cannot read exactly (palette, 16 bit, interlaced). It says which, and stops.

The receipt
===========
Beside the cut, a JSON receipt is written with the entry it came from and the entry's own sha256,
the source image and its sha256, the prompt, every object's numbers, and the check above. The
MODELS-USED page reads that receipt, so the claim "SAM 3.1 cut this" is never a sentence in a
markdown file with nothing behind it.

Exit codes: 0 the cut was written and its check passed, 1 no cut (zero records, or a check failed),
2 bad arguments or an unreadable input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import meta_client  # noqa: E402
import sam_mask  # noqa: E402


class PngError(ValueError):
    """A PNG this reader will not guess about."""


# ------------------------------------------------------------------ PNG, standard library only

_CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}


def read_png(path):
    """(width, height, rows of RGBA tuples) for an 8 bit non interlaced PNG."""
    with open(path, "rb") as handle:
        data = handle.read()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise PngError("%s is not a PNG" % path)
    position = 8
    width = height = depth = colour = interlace = None
    compressed = b""
    while position < len(data):
        if position + 8 > len(data):
            raise PngError("%s ends inside a chunk header" % path)
        length = struct.unpack(">I", data[position:position + 4])[0]
        tag = data[position + 4:position + 8]
        body = data[position + 8:position + 8 + length]
        position += 12 + length
        if tag == b"IHDR":
            width, height, depth, colour, _comp, _filt, interlace = struct.unpack(">IIBBBBB", body)
        elif tag == b"IDAT":
            compressed += body
        elif tag == b"IEND":
            break
    if not width or not height:
        raise PngError("%s has no readable IHDR" % path)
    if depth != 8:
        raise PngError("%s is %d bit; this reader handles 8 bit only" % (path, depth))
    if colour not in _CHANNELS:
        raise PngError("%s has colour type %r (palette or unknown); this reader handles "
                       "grey, grey+alpha, RGB and RGBA only" % (path, colour))
    if interlace:
        raise PngError("%s is interlaced; this reader handles progressive rows only" % path)
    channels = _CHANNELS[colour]
    raw = zlib.decompress(compressed)
    stride = width * channels
    if len(raw) != (stride + 1) * height:
        raise PngError("%s holds %d bytes of pixels, expected %d"
                       % (path, len(raw), (stride + 1) * height))
    rows = []
    previous = bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        kind = raw[start]
        line = bytearray(raw[start + 1:start + 1 + stride])
        if kind == 0:
            pass
        elif kind == 1:
            for index in range(channels, stride):
                line[index] = (line[index] + line[index - channels]) & 0xFF
        elif kind == 2:
            for index in range(stride):
                line[index] = (line[index] + previous[index]) & 0xFF
        elif kind == 3:
            for index in range(stride):
                left = line[index - channels] if index >= channels else 0
                line[index] = (line[index] + ((left + previous[index]) >> 1)) & 0xFF
        elif kind == 4:
            for index in range(stride):
                left = line[index - channels] if index >= channels else 0
                up = previous[index]
                upleft = previous[index - channels] if index >= channels else 0
                estimate = left + up - upleft
                pa, pb, pc = abs(estimate - left), abs(estimate - up), abs(estimate - upleft)
                nearest = left if (pa <= pb and pa <= pc) else (up if pb <= pc else upleft)
                line[index] = (line[index] + nearest) & 0xFF
        else:
            raise PngError("%s row %d uses PNG filter %d, which does not exist"
                           % (path, y, kind))
        previous = line
        rgba = []
        for x in range(width):
            base = x * channels
            if channels == 1:
                value = line[base]
                rgba.append((value, value, value, 255))
            elif channels == 2:
                value = line[base]
                rgba.append((value, value, value, line[base + 1]))
            elif channels == 3:
                rgba.append((line[base], line[base + 1], line[base + 2], 255))
            else:
                rgba.append((line[base], line[base + 1], line[base + 2], line[base + 3]))
        rows.append(rgba)
    return width, height, rows


def write_png_rgba(path, width, height, rows):
    """An 8 bit RGBA PNG, filter 0 on every row, with rows as sequences of 4 tuples."""
    raw = b"".join(b"\x00" + b"".join(bytes(pixel) for pixel in row) for row in rows)

    def chunk(tag, body):
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                     + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    return os.path.abspath(path)


def alpha_bbox(rows):
    """The tightest [x1, y1, x2, y2] over every pixel with a non zero alpha, or None."""
    x1 = y1 = None
    x2 = y2 = -1
    for y, row in enumerate(rows):
        for x, pixel in enumerate(row):
            if not pixel[3]:
                continue
            if x1 is None or x < x1:
                x1 = x
            if y1 is None or y < y1:
                y1 = y
            if x > x2:
                x2 = x
            if y > y2:
                y2 = y
    if x1 is None:
        return None
    return [x1, y1, x2, y2]


def alpha_count(rows):
    return sum(1 for row in rows for pixel in row if pixel[3])


# ------------------------------------------------------------------ the cut

def records_from_answer(answer):
    """The mask records of a segment answer, through the owner of the grammar."""
    records = answer.get("objects")
    if not isinstance(records, list) or not records:
        records = sam_mask.parse_records(answer.get("text"))
    return records


def place_mask(record, frame_width, frame_height):
    """The mask raster and the frame sized alpha plane it paints, in source pixels."""
    mask = record["mask"]
    raster = sam_mask.decode_mask(mask)
    mask_width, mask_height = int(mask["width"]), int(mask["height"])
    x1, y1 = int(record["box"][0]), int(record["box"][1])
    plane = bytearray(frame_width * frame_height)
    for y in range(mask_height):
        target_y = y1 + y
        if target_y < 0 or target_y >= frame_height:
            continue
        row = y * mask_width
        for x in range(mask_width):
            if not raster[row + x]:
                continue
            target_x = x1 + x
            if 0 <= target_x < frame_width:
                plane[target_y * frame_width + target_x] = 1
    return raster, plane, [mask_width, mask_height]


def cut(image_path, prompt, out_path=None, object_id=None, sleep=None):
    """Segment one object out of one image and write the cut, its receipt, and the numbers."""
    source_width, source_height, source_rows = read_png(image_path)
    answer = meta_client.segment(image_path, prompt, sleep=sleep)
    records = records_from_answer(answer)
    if not records:
        return {"ok": False, "why": "the model returned zero records for %r on %s; no cut was "
                                    "written (zero matches is a documented valid outcome)"
                                    % (prompt, image_path),
                "model": answer.get("model"), "backend": answer.get("backend"),
                "network": answer.get("network"), "records": 0}
    model = answer.get("model") or meta_client.model_for("segment")
    with open(image_path, "rb") as handle:
        image_bytes = handle.read()
    entry_path = meta_client.receipt_path(
        "segment", model,
        {"model": model, "prompt": str(prompt),
         "image_sha256": hashlib.sha256(image_bytes).hexdigest(),
         "image_bytes": len(image_bytes), "mask_encoding": "one_bit"})
    details = []
    for record in records:
        raster, plane, mask_size = place_mask(record, source_width, source_height)
        details.append({"record": record, "plane": plane, "mask_size": mask_size,
                        "set_pixels": sum(1 for value in raster if value)})
    if object_id is None:
        chosen = max(details, key=lambda item: item["set_pixels"])
    else:
        matches = [item for item in details
                   if int(item["record"].get("object_id", -1)) == int(object_id)]
        if not matches:
            return {"ok": False, "why": "the answer has no object %r (it has %s)"
                                        % (object_id, [item["record"].get("object_id")
                                                       for item in details]),
                    "records": len(details)}
        chosen = matches[0]
    plane = chosen["plane"]
    rows = []
    for y in range(source_height):
        row = []
        base = y * source_width
        for x in range(source_width):
            red, green, blue, alpha = source_rows[y][x]
            row.append((red, green, blue, alpha if plane[base + x] else 0))
        rows.append(row)
    out_path = out_path or os.path.join(meta_client.ROOT, "output", "silhouette_cut",
                                        "%s_cut.png" % str(prompt).replace(" ", "_"))
    written = write_png_rgba(out_path, source_width, source_height, rows)
    bbox = alpha_bbox(rows)
    pixels = alpha_count(rows)
    box = chosen["record"]["box"]
    expected = [box[0], box[1], box[0] + chosen["mask_size"][0] - 1,
                box[1] + chosen["mask_size"][1] - 1]
    checks = {
        "mask_size_is_box_size": chosen["mask_size"] == [box[2] - box[0] + 1,
                                                         box[3] - box[1] + 1],
        "alpha_pixels_equal_mask_set_pixels": pixels == chosen["set_pixels"],
        "bbox_within_box": bbox is not None and bbox[0] >= box[0] and bbox[1] >= box[1]
        and bbox[2] <= box[2] and bbox[3] <= box[3],
        "bbox_within_frame": bbox is not None and bbox[0] >= 0 and bbox[1] >= 0
        and bbox[2] < source_width and bbox[3] < source_height,
    }
    with open(image_path, "rb") as handle:
        source_sha = hashlib.sha256(handle.read()).hexdigest()
    with open(written, "rb") as handle:
        cut_bytes = handle.read()
    entry = {}
    if os.path.exists(entry_path):
        with open(entry_path, "r", encoding="utf-8") as handle:
            entry = json.load(handle)
    receipt = {
        "what": "SAM 3.1 silhouette cut",
        "prompt": str(prompt),
        "model": answer.get("model"),
        "backend": answer.get("backend"),
        "mode": answer.get("mode"),
        "network": entry.get("network"),
        "recorded_at": entry.get("recorded_at"),
        "cache_entry": os.path.relpath(entry_path, meta_client.ROOT).replace(os.sep, "/"),
        "objects": [{"object_id": item["record"].get("object_id"),
                     "box": item["record"]["box"],
                     "mask_size": item["mask_size"],
                     "set_pixels": item["set_pixels"]} for item in details],
        "chosen_object": chosen["record"].get("object_id"),
        "source": {"path": os.path.relpath(os.path.abspath(image_path),
                                           meta_client.ROOT).replace(os.sep, "/"),
                   "sha256": source_sha,
                   "bytes": os.path.getsize(image_path),
                   "width": source_width, "height": source_height},
        "cut": {"path": os.path.relpath(written, meta_client.ROOT).replace(os.sep, "/"),
                "sha256": hashlib.sha256(cut_bytes).hexdigest(),
                "bytes": len(cut_bytes),
                "width": source_width, "height": source_height,
                "alpha_pixels": pixels,
                "alpha_bbox": bbox,
                "box_from_response": list(box),
                "mask_extent": expected},
        "checks": checks,
        "ok": all(checks.values()),
    }
    receipt_path = os.path.splitext(written)[0] + "_receipt.json"
    with open(receipt_path, "w", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
    receipt["receipt_path"] = receipt_path
    return receipt


def check_receipt(receipt_path):
    """Re-read a receipt and re-verify it against the files on disk, not against its own claims."""
    with open(receipt_path, "r", encoding="utf-8") as handle:
        receipt = json.load(handle)
    root = meta_client.ROOT
    problems = []
    source = os.path.join(root, receipt["source"]["path"].replace("/", os.sep))
    cut_file = os.path.join(root, receipt["cut"]["path"].replace("/", os.sep))
    entry_file = os.path.join(root, receipt["cache_entry"].replace("/", os.sep))
    for label, path in (("source", source), ("cut", cut_file), ("cache entry", entry_file)):
        if not os.path.exists(path):
            problems.append("the %s is not on disk: %s" % (label, path))
    if problems:
        return {"ok": False, "problems": problems, "receipt": receipt}
    with open(source, "rb") as handle:
        if hashlib.sha256(handle.read()).hexdigest() != receipt["source"]["sha256"]:
            problems.append("the source image is not the one the receipt names")
    with open(cut_file, "rb") as handle:
        if hashlib.sha256(handle.read()).hexdigest() != receipt["cut"]["sha256"]:
            problems.append("the cut PNG is not the one the receipt names")
    with open(entry_file, "r", encoding="utf-8") as handle:
        entry = json.load(handle)
    with open(entry_file, "rb") as handle:
        entry_sha = hashlib.sha256(handle.read()).hexdigest()
    if entry.get("model") != receipt["model"]:
        problems.append("the cache entry's model is %r, the receipt says %r"
                        % (entry.get("model"), receipt["model"]))
    if entry.get("kind") != "segment":
        problems.append("the cache entry is kind %r, not segment" % (entry.get("kind"),))
    if entry.get("network") != receipt["network"]:
        problems.append("the cache entry says network %r, the receipt says %r"
                        % (entry.get("network"), receipt["network"]))
    if entry.get("recorded_at") != receipt["recorded_at"]:
        problems.append("the cache entry was recorded at %r, the receipt says %r"
                        % (entry.get("recorded_at"), receipt["recorded_at"]))
    width, height, rows = read_png(cut_file)
    if [width, height] != [receipt["cut"]["width"], receipt["cut"]["height"]]:
        problems.append("the cut is %dx%d, the receipt says %dx%d"
                        % (width, height, receipt["cut"]["width"], receipt["cut"]["height"]))
    pixels = alpha_count(rows)
    if pixels != receipt["cut"]["alpha_pixels"]:
        problems.append("the cut holds %d opaque pixels, the receipt says %d"
                        % (pixels, receipt["cut"]["alpha_pixels"]))
    chosen = [item for item in receipt["objects"]
              if item["object_id"] == receipt["chosen_object"]]
    if chosen and pixels != chosen[0]["set_pixels"]:
        problems.append("the cut holds %d opaque pixels, the mask it names has %d set"
                        % (pixels, chosen[0]["set_pixels"]))
    bbox = alpha_bbox(rows)
    if bbox != receipt["cut"]["alpha_bbox"]:
        problems.append("the cut's alpha bbox is %r, the receipt says %r"
                        % (bbox, receipt["cut"]["alpha_bbox"]))
    return {"ok": not problems, "problems": problems, "receipt": receipt,
            "cache_entry_sha256": entry_sha}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Cut one object out of an image with sam-3.1.")
    parser.add_argument("--image", help="the source PNG")
    parser.add_argument("--prompt", help="one noun phrase, e.g. ship")
    parser.add_argument("--out", default=None, help="where to write the cut PNG")
    parser.add_argument("--object", type=int, default=None,
                        help="object id to cut (default: the largest mask)")
    parser.add_argument("--check", default=None,
                        help="re-verify an existing receipt instead of cutting")
    parser.add_argument("--json", action="store_true", help="print the numbers as JSON")
    args = parser.parse_args(argv)

    if args.check:
        result = check_receipt(args.check)
        if args.json:
            print(json.dumps({key: value for key, value in result.items() if key != "receipt"},
                             indent=2, sort_keys=True))
        else:
            for problem in result["problems"]:
                print("FAIL  %s" % problem)
            print("recorded entry sha256: %s" % result.get("cache_entry_sha256"))
            print("check: %s" % ("PASS" if result["ok"] else "FAIL"))
        return 0 if result["ok"] else 1

    if not args.image or not args.prompt:
        parser.print_help()
        return 2
    try:
        result = cut(args.image, args.prompt, out_path=args.out, object_id=args.object)
    except (meta_client.MetaError, sam_mask.MaskPayloadError, PngError) as exc:
        print("refused: %s" % exc)
        return 2
    if args.json:
        print(json.dumps({key: value for key, value in result.items() if key != "receipt_path"},
                         indent=2, sort_keys=True))
    if not result.get("ok"):
        print("no cut: %s" % (result.get("why") or "a check failed"))
        for name, passed in (result.get("checks") or {}).items():
            print("  %-34s %s" % (name, "PASS" if passed else "FAIL"))
        return 1
    receipt = result
    print("model   : %s (backend %s, network %s, recorded %s)"
          % (receipt["model"], receipt["backend"], receipt["network"], receipt["recorded_at"]))
    print("entry   : %s" % receipt["cache_entry"])
    print("source  : %s %dx%d sha256 %s"
          % (receipt["source"]["path"], receipt["source"]["width"], receipt["source"]["height"],
             receipt["source"]["sha256"][:16]))
    print("objects : %s" % ", ".join("#%s %s" % (item["object_id"], item["set_pixels"])
                                     for item in receipt["objects"]))
    print("chosen  : object %s, %d opaque pixels, alpha bbox %r, mask extent %r"
          % (receipt["chosen_object"], receipt["cut"]["alpha_pixels"],
             receipt["cut"]["alpha_bbox"], receipt["cut"]["mask_extent"]))
    for name, passed in sorted(receipt["checks"].items()):
        print("  %-34s %s" % (name, "PASS" if passed else "FAIL"))
    print("cut     : %s" % receipt["cut"]["path"])
    print("receipt : %s" % receipt["receipt_path"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
