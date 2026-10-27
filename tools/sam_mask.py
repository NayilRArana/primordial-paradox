"""sam_mask.py: decode a sam-3.1 mask payload into a raster, and render it as a PNG (card SAM-SEGMENT-LIVE).

Why this file exists
====================
tools\\meta_client.py records the answer sam-3.1 sends, but that answer is not an image: it is
special token text carrying, per object, a box and a mask written in an arithmetic coded form.
The text alone is not a silhouette, so the recorded call needs this decoder to become one.

The wire format, from https://dev.meta.ai/docs/sam/reading-segmentation (read 2026-10-26)
=========================================================================================
    line    ::= FRAME record ("," record)*
    FRAME   ::= "<" INT "f>"
    record  ::= OBJECT_ID box mask
    box     ::= "<|box;x1=INT;y1=INT;x2=INT;y2=INT;w=INT;h=INT|>"    x2 and y2 inclusive,
                                                                     w and h the source media size
    mask    ::= "<|mask;x=0;y=0;data=H,W,ENC PAYLOAD|>"               H rows then W columns,
                                                                     ENC "!" is one_bit, "~" is lossless
    PAYLOAD ::= base85 of the coded raster; the payload itself may hold "!" or "~", so only the
                character immediately after "H,W," is the marker

The mask raster is the size of the box it belongs to: a 76 x 59 box carries a 76 x 59 mask, and
the mask's pixel (0, 0) is the box's (x1, y1). That is what lets a rendered mask be checked
against the box the same response returned, rather than trusted.

The one_bit codec
=================
A byte oriented range coder (32 bit low and range, an initial 4 byte code) drives one bit per
pixel through a 12 bit neighbourhood context: the two pixels to the left, the five in the row
above, and the five in the row above that, inside a raster padded by two pixels on every side.
Each of the 4096 contexts keeps a zero count and a one count, both starting at 1 and growing by
14 per hit, halved with a floor of 1 once they reach 4096. The coded bytes are base85, length
prefixed: five characters carry the byte count, then five characters per four bytes, and a tail
of (remainder + 1) characters for the last remainder bytes.

This is a port of the reference decoder in Meta's `meta_sam_parser` package (`_mask_codec.py`),
reduced to one_bit and to the standard library, because tools here are stdlib only. Its output
is checked byte for byte against that package for the recorded masks; see --verify-against.

What it does not do
===================
It does not invent pixels: a payload that fails a structural check raises MaskPayloadError and
nothing is written. It does not decode the lossless "~" encoding; it says so and stops.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import struct
import sys
import zlib

# The base85 alphabet: every printable ASCII character except the seven the grammar reserves.
_EXCLUDED = frozenset({'\"', "\\", ",", ";", "<", ">", "|"})
ALPHABET = "".join(chr(code) for code in range(0x21, 0x7F) if chr(code) not in _EXCLUDED)
RADIX = 85
LENGTH_PREFIX = 5
CODES = {character: index for index, character in enumerate(ALPHABET)}

_PADDING = 2
_CONTEXTS = 1 << 12
_INCREMENT = 14
_COUNT_LIMIT = 4096
_TOP = 1 << 24
_BOTTOM = 1 << 16
_MASK_8 = 0xFF
_MASK_32 = 0xFFFFFFFF

BOX_PATTERN = re.compile(r"<\|box;x1=(\d+);y1=(\d+);x2=(\d+);y2=(\d+);w=(\d+);h=(\d+)\|>")
MASK_PATTERN = re.compile(r"<\|mask;x=0;y=0;data=(\d+),(\d+),([~!])([^<>|]*)\|>")
RECORD_PATTERN = re.compile(r"(\d+)(<\|box;[^|]*\|>)(<\|mask;[^|]*\|>)")


class MaskPayloadError(ValueError):
    """The payload cannot be decoded into a raster, so no raster was produced."""


def _u32(value):
    return value & _MASK_32


def _digit(character):
    try:
        return CODES[character]
    except KeyError:
        raise MaskPayloadError("mask payload holds a character outside the base85 alphabet: %r"
                               % character)


def base85_decode(text):
    """The bytes a length prefixed base85 payload stands for."""
    if len(text) < LENGTH_PREFIX:
        raise MaskPayloadError("mask payload is missing its length prefix")
    length = 0
    for character in text[:LENGTH_PREFIX]:
        length = length * RADIX + _digit(character)
    remainder = length % 4
    expected = LENGTH_PREFIX + (length // 4) * 5 + (0 if remainder == 0 else remainder + 1)
    if len(text) != expected:
        raise MaskPayloadError("mask payload is %d characters, its prefix asks for %d"
                               % (len(text), expected))
    out = bytearray(length)
    source = LENGTH_PREFIX
    destination = 0
    full = length - remainder
    while destination < full:
        value = 0
        for index in range(5):
            value = value * RADIX + _digit(text[source + index])
        if value > _MASK_32:
            raise MaskPayloadError("mask payload holds an out of range group")
        source += 5
        out[destination] = (value >> 24) & _MASK_8
        out[destination + 1] = (value >> 16) & _MASK_8
        out[destination + 2] = (value >> 8) & _MASK_8
        out[destination + 3] = value & _MASK_8
        destination += 4
    if remainder:
        value = 0
        for index in range(5):
            value = value * RADIX + (_digit(text[source + index]) if index < remainder + 1
                                     else RADIX - 1)
        if value > _MASK_32:
            raise MaskPayloadError("mask payload holds an out of range tail")
        for index in range(remainder):
            out[destination + index] = (value >> (24 - index * 8)) & _MASK_8
    return bytes(out)


class RangeDecoder(object):
    """The 32 bit range decoder the one_bit stream is read with."""

    __slots__ = ("_code", "_input", "_low", "_position", "_range", "_scaled")

    def __init__(self, data):
        if len(data) < 4:
            raise MaskPayloadError("mask payload is short of its four byte code")
        self._input = data
        self._position = 0
        self._low = 0
        self._range = _MASK_32
        self._code = 0
        self._scaled = 0
        for _ in range(4):
            self._code = _u32((self._code << 8) | self._read())

    def _read(self):
        if self._position >= len(self._input):
            raise MaskPayloadError("mask payload ended before the raster was finished")
        value = self._input[self._position]
        self._position += 1
        return value

    def frequency(self, total):
        self._scaled = self._range // total
        if self._scaled == 0:
            raise MaskPayloadError("mask payload reached an invalid coding state")
        value = _u32(self._code - self._low) // self._scaled
        return total - 1 if value >= total else value

    def decode(self, cumulative, frequency):
        self._low = _u32(self._low + self._scaled * cumulative)
        self._range = self._scaled * frequency
        while True:
            if _u32(self._low ^ _u32(self._low + self._range)) < _TOP:
                pass
            elif self._range < _BOTTOM:
                self._range = _u32(-self._low) & (_BOTTOM - 1)
            else:
                break
            self._code = _u32((self._code << 8) | self._read())
            self._low = _u32(self._low << 8)
            self._range = _u32(self._range << 8)


def _context_at(padded, position, above, two_above):
    return (padded[position - 1]
            | (padded[position - 2] << 1)
            | (padded[above - 2] << 2)
            | (padded[above - 1] << 3)
            | (padded[above] << 4)
            | (padded[above + 1] << 5)
            | (padded[above + 2] << 6)
            | (padded[two_above - 2] << 7)
            | (padded[two_above - 1] << 8)
            | (padded[two_above] << 9)
            | (padded[two_above + 1] << 10)
            | (padded[two_above + 2] << 11))


def decode_one_bit(payload, width, height):
    """Row major bytes of 0 and 1, `width * height` of them, for a one_bit payload."""
    if not isinstance(payload, str) or not payload.startswith("!"):
        raise MaskPayloadError("a one_bit payload starts with '!', got %r"
                               % (str(payload)[:1] or ""))
    width = int(width)
    height = int(height)
    if width <= 0 or height <= 0:
        raise MaskPayloadError("mask size must be positive, got %dx%d" % (width, height))
    data = base85_decode(payload[1:])
    decoder = RangeDecoder(data)
    counts = [1] * (_CONTEXTS * 2)
    padded_width = width + 2 * _PADDING
    padded = bytearray(padded_width * (height + _PADDING))
    out = bytearray(width * height)
    for y in range(height):
        row = (y + _PADDING) * padded_width + _PADDING
        for x in range(width):
            position = row + x
            context = _context_at(padded, position, position - padded_width,
                                 position - 2 * padded_width)
            offset = context << 1
            zero = counts[offset]
            one = counts[offset + 1]
            value = decoder.frequency(zero + one)
            if value < zero:
                bit = 0
                decoder.decode(0, zero)
            else:
                bit = 1
                decoder.decode(zero, one)
            padded[position] = bit
            out[y * width + x] = bit
            total = zero + one
            counts[offset + bit] += _INCREMENT
            if total + _INCREMENT >= _COUNT_LIMIT:
                counts[offset] = (counts[offset] >> 1) or 1
                counts[offset + 1] = (counts[offset + 1] >> 1) or 1
    return bytes(out)


def decode_mask(mask):
    """Rows of 0 and 1 for one mask record, whatever encoding it names."""
    encoding = mask.get("encoding")
    if encoding == "lossless":
        raise MaskPayloadError("this tool decodes one_bit masks only; the answer carries the "
                               "lossless '~' encoding, so ask the API for mask_encoding one_bit")
    if encoding != "one_bit":
        raise MaskPayloadError("unknown mask encoding %r" % (encoding,))
    return decode_one_bit(mask.get("payload"), mask.get("width"), mask.get("height"))


def parse_records(text):
    """The records in one sam-3.1 line, in source order, as plain dicts."""
    records = []
    for object_id, box_token, mask_token in RECORD_PATTERN.findall(str(text or "")):
        box_hit = BOX_PATTERN.search(box_token)
        mask_hit = MASK_PATTERN.search(mask_token)
        if not box_hit or not mask_hit:
            continue
        x1, y1, x2, y2, frame_w, frame_h = (int(value) for value in box_hit.groups())
        mask_h, mask_w, marker, payload = mask_hit.groups()
        records.append({
            "object_id": int(object_id),
            "box": [x1, y1, x2, y2],
            "frame": [frame_w, frame_h],
            "mask": {"height": int(mask_h), "width": int(mask_w),
                     "encoding": "one_bit" if marker == "!" else "lossless",
                     "payload": marker + payload},
        })
    return records


def bbox(raster, width, height):
    """The tightest [x1, y1, x2, y2] holding every set pixel, inclusive, or None when empty."""
    x1 = y1 = None
    x2 = y2 = -1
    for index, value in enumerate(raster):
        if not value:
            continue
        x = index % width
        y = index // width
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


# ---------------------------------------------------------------- PNG, standard library only

def write_png(path, width, height, grey):
    """An 8 bit grey PNG: `grey` is one byte per pixel, row major, 0 or 255."""
    rows = []
    for y in range(height):
        rows.append(b"\x00" + bytes(grey[y * width:(y + 1) * width]))
    raw = b"".join(rows)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                     + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    return os.path.abspath(path)


def read_png_grey(path):
    """(width, height, rows as lists of ints) for an 8 bit grey PNG this module wrote."""
    with open(path, "rb") as handle:
        data = handle.read()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise MaskPayloadError("%s is not a PNG" % path)
    position = 8
    width = height = None
    colour_type = None
    compressed = b""
    while position < len(data):
        length = struct.unpack(">I", data[position:position + 4])[0]
        tag = data[position + 4:position + 8]
        body = data[position + 8:position + 8 + length]
        position += 12 + length
        if tag == b"IHDR":
            width, height, _depth, colour_type = struct.unpack(">IIBB", body[:10])
        elif tag == b"IDAT":
            compressed += body
        elif tag == b"IEND":
            break
    if colour_type != 0:
        raise MaskPayloadError("%s is not the 8 bit grey mask this tool writes" % path)
    if not width or not height:
        raise MaskPayloadError("%s has no readable IHDR" % path)
    raw = zlib.decompress(compressed)
    rows = []
    stride = width
    for y in range(height):
        start = y * (stride + 1)
        if raw[start] != 0:
            raise MaskPayloadError("%s uses a PNG filter this reader does not handle" % path)
        rows.append(list(raw[start + 1:start + 1 + stride]))
    return width, height, rows


def render_mask(record, out_path, frame=None, value=255):
    """Draw one record's mask at its box position on a full frame canvas, and return the numbers.

    The canvas is the source media size the box reports (w x h), unless `frame` overrides it.
    A pixel is `value` where the mask is set and 0 elsewhere, so the PNG's own bounding box can
    be compared with the box the API sent.
    """
    mask = record["mask"]
    raster = decode_mask(mask)
    width, height = mask["width"], mask["height"]
    frame_w, frame_h = frame or record.get("frame") or (width, height)
    frame_w, frame_h = int(frame_w), int(frame_h)
    x1, y1 = record["box"][0], record["box"][1]
    canvas = bytearray(frame_w * frame_h)
    for y in range(height):
        target_y = y1 + y
        if target_y < 0 or target_y >= frame_h:
            continue
        row = y * width
        for x in range(width):
            if not raster[row + x]:
                continue
            target_x = x1 + x
            if 0 <= target_x < frame_w:
                canvas[target_y * frame_w + target_x] = value
    path = write_png(out_path, frame_w, frame_h, canvas)
    inside = bbox(raster, width, height)
    placed = bbox(canvas, frame_w, frame_h)
    placed_box = None if placed is None else [placed[0], placed[1], placed[2], placed[3]]
    expected = [x1, y1, x1 + width - 1, y1 + height - 1]
    # The mask raster is the size of its box, so the box is the mask's extent by construction.
    # Where the mask does not touch all four of its own edges, the tight bbox of the PNG is
    # smaller than the box, and the translation of the in-mask bbox is the identity that has to
    # hold either way. Both are reported so neither number can be read as the other.
    translated = None if inside is None else [x1 + inside[0], y1 + inside[1],
                                              x1 + inside[2], y1 + inside[3]]
    return {
        "path": path,
        "frame": [frame_w, frame_h],
        "mask_size": [width, height],
        "set_pixels": sum(1 for value_ in raster if value_),
        "mask_bbox_in_mask": inside,
        "png_bbox": placed_box,
        "box_from_response": record["box"],
        "box_size": [record["box"][2] - record["box"][0] + 1,
                     record["box"][3] - record["box"][1] + 1],
        "expected_bbox": expected,
        "mask_size_matches_box": [width, height] == [expected[2] - expected[0] + 1,
                                                     expected[3] - expected[1] + 1],
        "bbox_is_the_translated_mask": placed_box == translated,
        "bbox_within_box": placed_box is None or (
            placed_box[0] >= expected[0] and placed_box[1] >= expected[1]
            and placed_box[2] <= expected[2] and placed_box[3] <= expected[3]),
        "bbox_matches_box": placed_box == expected,
    }


def verify_against(reference_module, text):
    """Compare this decoder's rasters with another implementation's, mask by mask."""
    from types import SimpleNamespace

    rows = []
    for record in parse_records(text):
        mask = record["mask"]
        mine = decode_mask(mask)
        theirs = reference_module.decode_mask_to_raster(
            reference_module.SegmentationMask(encoding=mask["encoding"],
                                              payload=mask["payload"],
                                              width=mask["width"], height=mask["height"]))
        rows.append({"object_id": record["object_id"],
                     "raster_bytes": len(mine),
                     "equal": bytes(theirs) == mine,
                     "set_pixels": sum(1 for value in mine if value)})
    return rows


def records_from_cache_entry(path):
    """The records of a recorded segment entry, read from the cache file rather than the network.

    The entry written by tools\\meta_client.py carries the records under response\\objects, and
    that parse is the owner of the grammar. The text is parsed here only for an entry recorded
    before that field existed.
    """
    with open(path, "r", encoding="utf-8") as handle:
        entry = json.load(handle)
    response = entry.get("response") or {}
    records = response.get("objects")
    if not isinstance(records, list) or not records:
        records = parse_records(response.get("text"))
    return entry, records


def main(argv=None):
    parser = argparse.ArgumentParser(description="Decode and render a recorded sam-3.1 mask.")
    parser.add_argument("cache_entry", nargs="?",
                        help="a data\\ai_cache\\<sha256>.json holding a segment answer")
    parser.add_argument("--out", default=None, help="PNG path for the first record's mask")
    parser.add_argument("--object", type=int, default=None, help="object id to render")
    parser.add_argument("--verify-against", default=None,
                        help="path to a checkout of Meta's meta_sam_parser package to compare with")
    parser.add_argument("--json", action="store_true", help="print the numbers as JSON")
    args = parser.parse_args(argv)
    if not args.cache_entry:
        parser.print_help()
        return 0
    entry, records = records_from_cache_entry(args.cache_entry)
    print("entry   : %s (backend %s, model %s, network %s, recorded %s)"
          % (os.path.basename(args.cache_entry), entry.get("backend"), entry.get("model"),
             entry.get("network"), entry.get("recorded_at")))
    print("records : %d" % len(records))
    if args.verify_against:
        sys.path.insert(0, args.verify_against)
        import meta_sam_parser

        for row in verify_against(meta_sam_parser, (entry.get("response") or {}).get("text")):
            print("verify  : object %d raster %d bytes equal to meta_sam_parser: %s (%d set)"
                  % (row["object_id"], row["raster_bytes"], row["equal"], row["set_pixels"]))
    if not records:
        print("this entry holds no mask record: nothing to render")
        return 1
    chosen = records
    if args.object is not None:
        chosen = [r for r in records if r["object_id"] == args.object]
    out = args.out or os.path.join(os.path.dirname(os.path.abspath(args.cache_entry)),
                                   "%s_mask.png" % os.path.splitext(
                                       os.path.basename(args.cache_entry))[0])
    results = []
    for record in chosen:
        path = out if len(chosen) == 1 else out.replace(".png", "_obj%d.png"
                                                        % record["object_id"])
        results.append(render_mask(record, path))
    for result in results:
        print("render  : %s" % result["path"])
        print("  mask %dx%d, box size %dx%d, mask size matches box: %s"
              % (result["mask_size"][0], result["mask_size"][1], result["box_size"][0],
                 result["box_size"][1], result["mask_size_matches_box"]))
        print("  set pixels                      : %d" % result["set_pixels"])
        print("  png bbox (x1 y1 x2 y2, inclusive): %r" % (result["png_bbox"],))
        print("  box the response returned       : %r" % (result["box_from_response"],))
        print("  bbox inside the mask, translated: %s"
              % (result["bbox_is_the_translated_mask"],))
        print("  bbox within the box             : %s" % (result["bbox_within_box"],))
        print("  bbox equals the box             : %s" % (result["bbox_matches_box"],))
    if args.json:
        print(json.dumps(results, indent=2))
    return 0 if all(r["bbox_matches_box"] and r["mask_size_matches_box"]
                    and r["bbox_is_the_translated_mask"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
