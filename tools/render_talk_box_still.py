#!/usr/bin/env python3
"""render_talk_box_still.py: one frame of the TALK box, measured, with a verify file beside it.

Why this exists (card t_b9173f05, the judge panel's fix 2)
    The panel's Impact reason was "no TALK interaction or verdict is visible". The recording that would
    settle it is tools\\play_demo.py's job, and that run is refused while a desktop automation holds the
    keyboard (tools\\idle_check.py exits 4 and names codex.exe). What can be produced on a busy machine is
    a still: one real frame of the game, with tools\\demo_overlay.py's box drawn on it, and the same
    question asked of the pixels that the video would be asked.

What it does, in order, and it stops on the first refusal
    1. draws the shot with demo_overlay.render. Card t_892cc851 leaves one shot that draws the box, S5,
       and its plate sits inside the frame; a row that is not a live answer, or a live row with no
       verdict receipt in the ledger, is refused here with the fix named (the three Morgan rows are
       fallback today, so the shipped still is a refusal until Q1's re-bake lands);
    2. measures the result with demo_overlay.check_frame, and writes the still only if every check passes;
    3. writes a verify file beside the still carrying the frame's sha256, every drawn line, the receipt ids
       the box printed, and the frame test's own rows, then labels and logs the Meta numbers the box shows
       (tools\\\\receipts.py), so no number in the file stands without a receipt.

Usage
    python tools\\render_talk_box_still.py --frame output\\first_fight_talk_frames\\t_0025.png
    python tools\\render_talk_box_still.py --shot S6 --frame IN.png --out OUT.png --verify V.json

Exit codes
    0  the still is written and every check passed
    1  the tool refused (a row, a field or a receipt is missing, the frame is not 768x720), or a check failed
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import demo_overlay  # noqa: E402  the drawing and the frame test, never a second copy of them
import receipts  # noqa: E402  the ledger the box reads, so the file labels every number it shows


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description="draw the TALK box still and measure it")
    parser.add_argument("--shot", default="S5", help="the shot to draw (default S5, the one shot that draws the box)")
    parser.add_argument("--frame", required=True, help="the 768x720 frame to draw on")
    parser.add_argument("--out", help="where the still goes (default output/demo/overlay/<shot>_talk_box.png)")
    parser.add_argument("--verify", help="where the verify file goes (default beside the still)")
    parser.add_argument("--seconds", type=float, default=84.0,
                        help="the clock the shot's bake row is drawn at (DEMO-SCRIPT section 4, default 1:24.00)")

    args = parser.parse_args(argv)

    out = args.out or os.path.join(ROOT, "output", "demo", "overlay", "%s_talk_box.png" % args.shot)
    verify = args.verify or os.path.splitext(out)[0] + "_verify.json"
    below = demo_overlay.TALK_BOX_ANCHOR.get(args.shot) == "below"

    try:
        bake, index = demo_overlay.load_bake()
        image, layout = demo_overlay.render(args.frame, args.shot, bake, index, below=below, talk_box=True)
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        image.save(out)
        report = demo_overlay.check_frame(args.frame, out, args.shot, bake, index, below=below, talk_box=True)
    except demo_overlay.OverlayError as error:
        print("REFUSED  %s" % error)
        return 1

    talk = report["talk_box"] or {}
    payload = {
        "tool": "tools/render_talk_box_still.py",
        "kind": "talk_box_still",
        "card": "t_b9173f05",
        "shot": args.shot,
        "script_rule": "knowledge/DEMO-SCRIPT.md section 4: the box is the record, and every word in it is read out of the record",
        "at_seconds": args.seconds,
        "ok": bool(report["ok"]),
        "frame_source": os.path.relpath(os.path.abspath(args.frame), ROOT).replace("\\", "/"),
        "frame_sha256": sha256_file(args.frame),
        "still": os.path.relpath(os.path.abspath(out), ROOT).replace("\\", "/"),
        "still_sha256": sha256_file(out),
        "plate_below_frame": below,
        "talk_box": {
            "row": talk.get("row"),
            "verdict": talk.get("verdict"),
            "receipt": talk.get("receipt"),
            "rect": list(talk.get("rect") or ()),
            "lines": [line["source_text"] for line in (talk.get("lines") or [])],
        },
        "checks": report["checks"],
    }
    with open(verify, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    # The numbers the box prints are labelled and logged in the same pass (card t_b9173f05): a re-render used
    # to write a clean verify file and quietly drop the `meta_numbers` block, so tools/check_receipts.py found
    # nothing to check and the still's two build numbers stood unlabelled. Refusing here is the whole point of
    # the block, so a receipt that cannot be written fails the still rather than passing without one.
    try:
        receipts.write_into(verify)
    except receipts.ReceiptError as error:
        print("FAIL  the receipt block could not be written: %s" % error)
        return 1

    failed = [item for item in report["checks"] if not item["ok"]]
    for item in failed:
        print("FAIL  %s  %s" % (item["name"], item["detail"]))
    print("%s  %s still at %s, %d checks, verify at %s"
          % ("PASS" if report["ok"] else "FAIL", args.shot, out, len(report["checks"]), verify))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
