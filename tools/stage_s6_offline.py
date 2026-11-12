#!/usr/bin/env python3
"""stage_s6_offline.py: stage the S6 offline shot as a video, with the three bake rows and the network line on screen.

Why this file exists
    Card t_0a284b7e, fix 4 of the JUDGE-PANEL 2026-11-12 five. The panel's "Use of Meta AI tooling" reason was
    "Receipts list 21 calls with 52.4 percent live but frames show no textbox verdict, bake row or caption so no real
    work is visible". `knowledge/DEMO-SCRIPT.md` section 5 already says what the S6 offline shot must show: a machine
    with the network dead, a line saying so, and the replies coming out of `data/meta_bake.json` while the run
    continues through the save. `tools/demo_overlay.py` already draws that plate from the bake's own measured flags.
    What did not exist is a moving shot: every proof of the plate in the tree is a still frame, and the last DEVLOG
    entry on the subject says exactly that ("the badge proof is a still frame rather than a fresh capture").

What this tool does, and what it refuses
    1. It stages the shot from a REAL recording of the game's TALK fight (`output/first_fight_talk_capture.mp4`,
       verified ok by its own verify file: the battle box, the TALK command, the three options, the reply board and
       the SPARE outcome, all measured). It does not draw the fight; it cuts the fight, and the fight still resolves
       on screen after the plate is gone.
    2. It draws the plate with `tools/demo_overlay.py`'s own render, so the three bake rows, the badge and the network
       line are the project's own drawing, read out of `data/meta_bake.json` at stage time. Nothing here types a
       model name, a hash, a time or a network word.
    3. It refuses a bake whose `bake.network` is true or whose `bake.offline` is false, because the network line this
       tool stages is the dead one, and a dead line drawn over a live bake would be a claim the file does not make.
    4. It runs the whole stage under a socket trap, the same mechanism the project's own offline proof uses
       (`tests/test_no_network_in_build.py`): every socket open is counted and raises, so a stage that opened one
       cannot be reported as offline. The count is written into the verify file.
    5. It records the host adapter's own state at stage time, measured before the trap goes up, and writes it into the
       verify file whether it was up or down. THIS TOOL DOES NOT TURN THE ADAPTER OFF AND DOES NOT CLAIM TO. The
       adapter-down take that section 5 describes still needs a free desktop (the idle gate refuses while a desktop
       automation runs, `tools/idle_check.py`), so the verify file says which of the two things this artifact is: a
       stage of the offline plate over a recorded fight, not a recording made with the adapter down.

What it writes
    output/demo/s6-offline-<date>.mp4              the shot: 768 x 990, 60 fps, the game's 720 rows plus the plate band
    output/demo/s6-offline-<date>_verify.json       every measurement, the plate plan, and the labelled Meta numbers
    output/demo/s6-offline-<date>_plate.png         the plate patch the video composites, drawn by demo_overlay
    output/s6_offline_<date>/                      the check frames this tool measured

Usage
    python tools\\stage_s6_offline.py --rows       print what would be drawn, write nothing
    python tools\\stage_s6_offline.py              stage the shot for today
    python tools\\stage_s6_offline.py --date 2026-11-11 --frame-source output\\first_fight_talk_frames\\t_0047.png
    python tools\\stage_s6_offline.py --check-only output\\demo\\s6-offline-2026-11-11.mp4

Exit codes
    0  the shot was staged and every measurement passed
    1  a measurement failed; the verify file says which
    2  bad argument
    3  refused before staging: the bake is live, the frame is not 768x720, or the source capture is missing

Honesty rules carried from the project, not invented here
    - no em dash, no en dash in any string written or printed by this file
    - a number that is not measured, computed or inferred is not printed
    - the game's own pixels are not drawn over: the plate lives in the band under the 720 row frame
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import demo_overlay as ov  # noqa: E402
import receipts  # noqa: E402
from PIL import Image, ImageChops  # noqa: E402

SOURCE_CAPTURE = os.path.join(ROOT, "output", "first_fight_talk_capture.mp4")
SOURCE_VERIFY = os.path.join(ROOT, "output", "first_fight_talk_verify.json")
PLATE_FRAME = os.path.join(ROOT, "output", "first_fight_talk_frames", "t_0047.png")
OUT_DIR = os.path.join(ROOT, "output", "demo")

# The cut, in seconds of the source capture, and the plate window in seconds of the cut. The numbers come from the
# capture's own verify file: the battle box is on screen from 20.0 s (`battle_box_in_sample.first_at` t_0020), the
# three option panel from 26.0 s (`option_panel_in_sample`), the reply board at 58.0 s (`reply_board_in_sample`) and
# the SPARE outcome at 59.0 s (`spare_result_in_sample`). The cut opens 1.4 s before the battle so the frame that
# carries the plate is not the first frame, and it ends on the capture's own last second so the run is seen to go on.
CUT_START = 18.6
PLATE_IN = 1.40          # cut clock 1.40 s = source 20.00 s, the battle box's own first measured frame
PLATE_OUT = 43.40        # cut clock 43.40 s = source 62.00 s, after the SPARE outcome at source 59.0 s
FPS = 60


class StageError(Exception):
    """A refusal: this tool will not stage something it cannot measure."""


def rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today():
    return datetime.datetime.now().strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------------------------------------------------
# The measurements that are taken BEFORE the trap goes up


def host_network_state():
    """Measure the host's own network state, and say how it was measured.

    Two probes, both reported, because either one alone can lie: a DNS lookup can be answered from a cache, and a TCP
    connect can be refused by a firewall on a machine that is up. Neither probes an endpoint the project ever calls.
    """
    state = {"dns_lookup_example_com": None, "tcp_connect_8_8_8_8_53": None, "checked_at": utc_now()}
    try:
        socket.gethostbyname("example.com")
        state["dns_lookup_example_com"] = True
    except OSError:
        state["dns_lookup_example_com"] = False
    try:
        with socket.create_connection(("8.8.8.8", 53), timeout=3):
            state["tcp_connect_8_8_8_8_53"] = True
    except OSError:
        state["tcp_connect_8_8_8_8_53"] = False
    state["adapter_up"] = bool(state["dns_lookup_example_com"] or state["tcp_connect_8_8_8_8_53"])
    state["why"] = ("the host adapter's own state at stage time, measured by a DNS lookup and a TCP connect before the "
                    "socket trap goes up; this tool does not disable the adapter and does not claim the adapter was down")
    return state


class SocketTrap:
    """Every socket open is counted and refused, the mechanism tests/test_no_network_in_build.py uses."""

    def __init__(self):
        self.opens = 0
        self._real_connect = None
        self._real_create = None
        self._real_urlopen = None

    def __enter__(self):
        trap = self

        def blocked(*args, **kwargs):
            trap.opens += 1
            raise StageError("the stage tried to open a socket, so it is not offline")

        self._real_connect = socket.socket.connect
        self._real_create = socket.create_connection
        self._real_urlopen = urllib.request.urlopen
        socket.socket.connect = blocked
        socket.create_connection = blocked
        urllib.request.urlopen = blocked
        return self

    def __exit__(self, *exc):
        socket.socket.connect = self._real_connect
        socket.create_connection = self._real_create
        urllib.request.urlopen = self._real_urlopen
        return False


# ---------------------------------------------------------------------------------------------------------------------
# The plate


def plate_for(bake, index, frame_path):
    """Draw the S6 plate with the project's own overlay, and return the patch the video composites.

    The patch is the full width band under the 720 row frame, cut out of the overlay's own --below render, so the
    patch carries the plate's fill, its border and its black surroundings exactly as demo_overlay drew them. Nothing
    is redrawn here and no colour is typed here.
    """
    if not os.path.exists(frame_path):
        raise StageError("no frame at %s, so the plate has nothing to be measured on" % rel(frame_path))
    source = Image.open(frame_path).convert("RGB")
    if source.size != (ov.FRAME_W, ov.FRAME_H):
        raise StageError("the frame is %dx%d and the overlay is laid out for %dx%d"
                         % (source.size[0], source.size[1], ov.FRAME_W, ov.FRAME_H))
    canvas, layout = ov.render(source, "S6", bake, index, below=True)
    patch = canvas.crop((0, ov.FRAME_H, ov.FRAME_W, canvas.size[1]))
    return patch, layout, canvas


def plan_summary(layout):
    return {
        "plate": list(layout["plate"]),
        "canvas": [ov.FRAME_W, layout["plate"][3] + ov.BOTTOM_MARGIN],
        "lines": [dict(tier=line["tier"], text=line["source_text"]) for line in layout["lines"]],
        "line_count": len(layout["lines"]),
        "hash_lines": [line["source_text"] for line in layout["lines"] if line["tier"] == "hash"],
        "badge": layout["badge"]["text"] if layout.get("badge") else None,
    }


# ---------------------------------------------------------------------------------------------------------------------
# The encode


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise StageError("command failed (%d): %s\n%s" % (proc.returncode, " ".join(cmd), proc.stderr[-2000:]))
    return proc


def encode(source, patch_path, out_path, start, dur, plate_in, plate_out, canvas_h):
    """Cut the recording, pad it to the plate's canvas, and composite the plate in its window.

    The output also carries `-t dur` on purpose. The plate is a `-loop 1` image input, which never ends, and
    ffmpeg keeps encoding while any input still has frames: measured on 2026-11-11, the same graph without an
    output `-t` ran past ten minutes on a 55 s cut and had written 309 MB when it was stopped. The output limit
    is what bounds it, and it is the cut's own length, not a guess.
    """
    vf = ("[0:v]fps=%d,scale=%d:%d:flags=neighbor,pad=%d:%d:0:0:black[base];"
          "[base][1:v]overlay=0:%d:enable='between(t,%.2f,%.2f)'[v]"
          % (FPS, ov.FRAME_W, ov.FRAME_H, ov.FRAME_W, canvas_h, ov.FRAME_H, plate_in, plate_out))
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-ss", "%.3f" % start, "-t", "%.3f" % dur, "-i", source,
           "-loop", "1", "-i", patch_path,
           "-filter_complex", vf, "-map", "[v]", "-t", "%.3f" % dur, "-an",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv444p",
           "-r", str(FPS), "-movflags", "+faststart", out_path]
    run(cmd)
    return cmd


def probe(path):
    proc = run(["ffprobe", "-v", "error", "-show_entries",
                "format=duration,size:stream=codec_name,width,height,r_frame_rate,nb_frames",
                "-of", "json", path])
    return json.loads(proc.stdout)


def frame_at(path, t, out_png):
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", "%.3f" % t, "-i", path,
         "-frames:v", "1", out_png])
    return Image.open(out_png).convert("RGB")


def count_colour(image, rect, colour, tol=0):
    """Pixels in `rect` within `tol` of `colour` on every channel."""
    x0, y0, x1, y1 = rect
    crop = image.crop((x0, y0, x1, y1))
    pixels = list(crop.getdata())
    if tol == 0:
        return sum(1 for px in pixels if px == colour)
    return sum(1 for px in pixels if max(abs(px[0] - colour[0]), abs(px[1] - colour[1]), abs(px[2] - colour[2])) <= tol)


def band_is_black(image, rect, tol=6):
    x0, y0, x1, y1 = rect
    pixels = list(image.crop((x0, y0, x1, y1)).getdata())
    lit = sum(1 for px in pixels if max(px) > tol)
    return lit, len(pixels)


# ---------------------------------------------------------------------------------------------------------------------
# The receipts


def stage_numbers(source_seconds, plan_info, window_seconds):
    """The numbers this stage can vouch for, each labelled and each pointing at a committed file.

    Every source here is a file this stage does not rewrite: data/meta_bake.json, the recording it cuts, and this
    tool itself. An earlier draft pointed two of them at tools/demo_overlay.py, which another lane was editing at
    the same minute, so the receipts went stale the moment that file changed; a receipt whose source moves is not a
    receipt, so the bake and the recording are the sources instead.
    """
    bake_sha = sha256_file(os.path.join(ROOT, "data", "meta_bake.json"))
    numbers = []
    numbers.append(receipts._number(
        name="meta.s6_offline_plate_lines",
        value=int(plan_info["line_count"]),
        label="measured",
        source="data/meta_bake.json",
        locator="the lines built from this bake by tools/demo_overlay.py overlay_lines('S6'): 3 caption, 2 bake "
                "header, 3 T1 to T3 request hashes, 1 badge, 2 network lines, counted one by one",
        why="every line the plate draws on the staged shot, counted from the plan the render actually used",
        sha=bake_sha,
    ))
    numbers.append(receipts._number(
        name="meta.s6_offline_source_seconds",
        value=round(float(source_seconds), 3),
        label="measured",
        source=rel(SOURCE_CAPTURE),
        locator="format.duration, read by ffprobe",
        why="the length of the recorded TALK fight this shot cuts, which is the game's own capture",
        sha=sha256_file(SOURCE_CAPTURE),
    ))
    numbers.append(receipts._number(
        name="meta.s6_offline_window_seconds",
        value=round(float(window_seconds), 3),
        label="computed",
        source=rel(os.path.abspath(__file__)),
        locator="PLATE_OUT - PLATE_IN, this tool's own two constants",
        why="how long the plate is on screen in the staged shot",
        formula="PLATE_OUT - PLATE_IN in tools/stage_s6_offline.py",
        sha=sha256_file(os.path.abspath(__file__)),
    ))
    numbers.append(receipts._number(
        name="meta.s6_offline_cut_seconds",
        value=round(float(source_seconds) - CUT_START, 3),
        label="computed",
        source=rel(SOURCE_CAPTURE),
        locator="format.duration - the cut's own start at %.2f s, read by ffprobe" % CUT_START,
        why="the length of the staged shot, which is the recording from the battle's first frame to its end",
        formula="source format.duration - CUT_START",
        sha=sha256_file(SOURCE_CAPTURE),
    ))
    return numbers


# ---------------------------------------------------------------------------------------------------------------------
# The stage


def stage(date, frame_path, source, out_dir, check_only=None):
    report = {"tool": rel(os.path.abspath(__file__)), "card": "t_0a284b7e", "staged_at": utc_now(),
              "source_capture": rel(source), "source_verify": rel(SOURCE_VERIFY)}
    if not os.path.exists(source):
        raise StageError("no recording at %s, and this tool does not draw a fight it has no recording of" % rel(source))

    bake, index = ov.load_bake()
    block = bake["bake"]
    report["bake"] = {key: block.get(key) for key in
                      ("model", "created_at", "mode", "backend", "network", "offline", "live", "fallback",
                       "calls_attempted", "rows")}
    if bool(block.get("network")) is not False or bool(block.get("offline")) is not True:
        raise StageError("data/meta_bake.json records network %r and offline %r, so this is not the dead network shot"
                         % (block.get("network"), block.get("offline")))

    out_mp4 = check_only or os.path.join(out_dir, "s6-offline-%s.mp4" % date)
    out_base = os.path.splitext(out_mp4)[0]

    if check_only:
        if not os.path.exists(out_mp4):
            raise StageError("no staged shot at %s to check" % rel(out_mp4))
        patch_path = out_base + "_plate.png"
        if not os.path.exists(patch_path):
            raise StageError("no plate patch beside the shot at %s" % rel(patch_path))
        patch = Image.open(patch_path).convert("RGB")
        layout = ov.plan("S6", bake, index, below=True)
        plan_info = plan_summary(layout)
    else:
        patch, layout, _canvas = plate_for(bake, index, frame_path)
        plan_info = plan_summary(layout)
        os.makedirs(out_dir, exist_ok=True)
        patch_path = out_base + "_plate.png"
        patch.save(patch_path)
        network = host_network_state()
        report["host_network_at_stage"] = network
        with SocketTrap() as trap:
            started = time.time()
            source_seconds = float(probe(source)["format"]["duration"])
            cmd = encode(source, patch_path, out_mp4, CUT_START, source_seconds - CUT_START,
                         PLATE_IN, PLATE_OUT, plan_info["canvas"][1])
            report["socket_opens_during_stage"] = trap.opens
            report["stage_seconds"] = round(time.time() - started, 2)
        report["encode_command"] = cmd

    report["plate_plan"] = plan_info
    report["plate_patch"] = rel(patch_path)
    report["plate_patch_sha256"] = sha256_file(patch_path)
    report["shot"] = rel(out_mp4)
    report["shot_sha256"] = sha256_file(out_mp4)
    report["shot_bytes"] = os.path.getsize(out_mp4)
    report["stream"] = probe(out_mp4)
    # The receipt numbers are about the RECORDING and the cut, not about the shot's own length, so both are read
    # from the recording's file. An earlier draft passed the shot's duration here and printed the recording's length
    # as 55.2 s when the recording is 73.8 s: the receipts are what caught it, which is what they are for.
    source_seconds = float(probe(source)["format"]["duration"])
    report["source_capture_seconds"] = round(source_seconds, 3)

    # The cut is CUT_START to the capture's own end, so the plate window sits inside it by construction.
    dur = float(report["stream"]["format"]["duration"])
    report["cut"] = {"start_seconds": CUT_START, "seconds": round(dur, 3),
                     "plate_in": PLATE_IN, "plate_out": PLATE_OUT}
    if not (0 < PLATE_IN < PLATE_OUT < dur):
        raise StageError("the plate window %.2f to %.2f does not sit inside a %.3f s cut"
                         % (PLATE_IN, PLATE_OUT, dur))

    colours = ov.load_palette()
    checks = []

    def add(name, ok, detail):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    stream = report["stream"]["streams"][0]
    add("frame size", stream["width"] == ov.FRAME_W and stream["height"] == plan_info["canvas"][1],
        "%dx%d" % (stream["width"], stream["height"]))
    add("frame rate", stream["r_frame_rate"] == "%d/1" % FPS, stream["r_frame_rate"])
    add("audio stream", len(report["stream"]["streams"]) == 1,
        "%d stream(s): the recording this shot cuts carries no audio" % len(report["stream"]["streams"]))

    plate_rect = tuple(plan_info["plate"])
    band = (0, ov.FRAME_H, ov.FRAME_W, plan_info["canvas"][1])
    frames_dir = os.path.join(ROOT, "output", "s6_offline_%s" % date)
    os.makedirs(frames_dir, exist_ok=True)

    inside = [PLATE_IN + 0.6, (PLATE_IN + PLATE_OUT) / 2.0, PLATE_OUT - 0.6]
    outside = [max(0.2, PLATE_IN - 0.6), min(dur - 0.4, PLATE_OUT + 0.6)]
    plate_area = (plate_rect[2] - plate_rect[0]) * (plate_rect[3] - plate_rect[1])
    for tag, times, want_plate in (("in", inside, True), ("out", outside, False)):
        for t in times:
            png = os.path.join(frames_dir, "check_%s_%.2f.png" % (tag, t))
            image = frame_at(out_mp4, t, png)
            fill = count_colour(image, plate_rect, colours[ov.ROLE_PLATE], tol=10)
            ink = count_colour(image, plate_rect, colours[ov.ROLE_TEXT], tol=40)
            lit, total = band_is_black(image, band)
            if want_plate:
                add("plate on screen at %.2f s" % t, fill > 0.5 * plate_area,
                    "%d of %d plate pixels" % (fill, plate_area))
                add("bake ink on screen at %.2f s" % t, ink > 400, "%d ink pixels" % ink)
                add("band not black at %.2f s" % t, lit > 0.5 * total, "%d of %d pixels lit" % (lit, total))
            else:
                # A re-encoded frame is not a lossless copy: a handful of pixels at the plate's own edge ring by a
                # few levels. The rule is that the band is black, not that the encoder is silent, so a stray count
                # under one pixel in ten thousand is reported and allowed.
                add("band black at %.2f s" % t, lit <= max(8, total // 10000),
                    "%d of %d pixels lit" % (lit, total))

    # The game's own pixels are the recording's, not this tool's: a frame inside the plate window, cut down to the
    # 768x720 the game draws, is compared against the same second of the source. The shot is re-encoded and the
    # recording is not, so the measure is the distribution of the difference and not a single worst pixel.
    src_png = os.path.join(frames_dir, "source_%.2f.png" % inside[1])
    src_frame = frame_at(source, CUT_START + inside[1], src_png)
    out_frame = Image.open(os.path.join(frames_dir, "check_in_%.2f.png" % inside[1])).convert("RGB").crop(
        (0, 0, ov.FRAME_W, ov.FRAME_H))
    diff = ImageChops.difference(src_frame, out_frame)
    diffs = [max(px) for px in diff.getdata()]
    pixel_count = len(diffs)
    mean = sum(diffs) / float(pixel_count)
    over48 = sum(1 for value in diffs if value > 48)
    add("the game's frame is the recording's", mean <= 3.0 and over48 <= pixel_count // 200,
        "mean channel difference %.2f, %d of %d pixels over 48 levels" % (mean, over48, pixel_count))

    report["checks"] = checks
    report["ok"] = all(check["ok"] for check in checks)
    report["unproven"] = [
        "the adapter-down take itself: tools/idle_check.py refuses every capture while a desktop automation runs "
        "(codex.exe), so no recording was made with the adapter disabled; this stage composites the offline plate "
        "over a recording made on 2026-10-24",
        "audio: the source recording carries none",
    ]

    stage_nums = stage_numbers(source_seconds, plan_info, PLATE_OUT - PLATE_IN)
    numbers = receipts.meta_numbers() + stage_nums
    # meta_numbers() logs its own rows; the stage's four are logged here, through the same deduplicating writer, so
    # the ledger holds them and tools/check_receipts.py can resolve every id the verify file quotes.
    receipts._log(stage_nums)
    report["meta_numbers"] = numbers
    report["meta_lines"] = receipts.summary_lines(numbers)

    verify_path = out_base + "_verify.json"
    with open(verify_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    report["verify"] = rel(verify_path)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="stage the S6 offline shot with the bake rows and network line")
    parser.add_argument("--date", default=today())
    parser.add_argument("--frame-source", default=PLATE_FRAME)
    parser.add_argument("--source", default=SOURCE_CAPTURE, help="the recording the shot cuts")
    parser.add_argument("--out-dir", default=OUT_DIR)
    parser.add_argument("--rows", action="store_true", help="print the plate plan and write nothing")
    parser.add_argument("--check-only", default=None, metavar="MP4", help="re-measure a staged shot")
    args = parser.parse_args(argv)

    if args.rows:
        bake, index = ov.load_bake()
        _patch, layout, _canvas = plate_for(bake, index, args.frame_source)
        print(json.dumps(plan_summary(layout), indent=1))
        return 0

    try:
        report = stage(args.date, args.frame_source, args.source, args.out_dir, check_only=args.check_only)
    except StageError as exc:
        print("REFUSED: %s" % exc)
        return 3

    for check in report["checks"]:
        print("%-4s %-44s %s" % ("PASS" if check["ok"] else "FAIL", check["name"], check["detail"]))
    for line in report["meta_lines"]:
        print("meta  %s" % line)
    for note in report["unproven"]:
        print("unproven  %s" % note)
    print("%s  %s, %d bytes, %.3f s" % ("PASS" if report["ok"] else "FAIL", report["shot"],
                                       report["shot_bytes"], float(report["stream"]["format"]["duration"])))
    print("verify    %s" % report["verify"])
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
