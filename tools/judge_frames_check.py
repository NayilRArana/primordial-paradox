#!/usr/bin/env python3
"""judge_frames_check.py: measure the six judged frames so a good video cannot quietly regress.

Card t_4512b33a (JUDGE-FRAME-TEST, testing lane, 2026-10-27). The judge panel looks at six
evenly spaced stills from the newest nightly and scores them; that sample is the only look the
video gets, and it is taken by a tool that reports what it sees but never refuses a video. This
tool is the check the panel is not: it samples the same six frame times, plus the three the
three minute cut adds, plus the two frames that carry the bake row, and it asserts with measured
numbers, so a blank frame, a missing receipt or a frozen tail stops the run instead of scoring
quietly.

WHAT IT ASSERTS, and where each number comes from

1. No frame is one colour over 90 percent of the picture. The share is
   `eye_critic.measure_image()`'s `largest_colour_share`, the same measure the panel quotes in
   `knowledge/JUDGE-PANEL-2026-10-26.md` line 33 ("2 of 6 sampled frames are one colour over 90
   percent (18.4 s, 30.6 s)"), so this check and the panel's sentence can never disagree about
   what "blank" means. 90 percent is that card's own threshold and is not tuned here.

2. The S5 and S6 frames carry the bake row. Three measurements, in order of how hard they are to
   fake: the plate's `paper` colour covers at least 55 percent of the plate rect the overlay tool
   computed (a plate that was never drawn leaves game art there, measured 0.5 percent on a clean
   frame against 77 percent on a rendered one); every line box the plan placed holds ink; and the
   model name string, rasterised with the video's own caption font, matches the pixels inside the
   `BAKE MODEL <model>` line box with an intersection over union of at least 0.50.

3. The last three sampled frames differ from each other. Two frames differ when at least 1 percent
   of their pixels move by more than 8 levels in any channel. On the 2026-10-26 capture the three
   end frames are the same picture (0.0084, 0.0084 and 0.0000), which is the regression this row
   exists to catch.

WHERE THE FRAME TIMES COME FROM
    The six panel times, 6.1, 18.4, 30.6, 42.9, 55.1 and 67.4 s, are `tools/judge_panel.py`'s
    own count=6 sample of the 73.483 s capture, quoted verbatim from
    `knowledge/JUDGE-PANEL-2026-10-26.md` line 11. The 100, 130 and 160 s times are added only
    when the capture is the judged length (`knowledge/DEMO-SCRIPT.md` section 2: three minutes),
    which is read as 180 s give or take the 20 s the panel already allows. Because a 180 s cut is
    sampled evenly by the panel at 15, 45, 75 s and so on, the report states what the panel's own
    six times would be for the capture it measured, so the two tools cannot drift apart silently.

    The bake row does not live at any of those nine times: `tools/demo_overlay.py` draws it at
    S5 83.40 to 87.40 s and S6 135.03, 138.53 and 143.53 s (its `SHOT_WINDOWS`, read from
    `knowledge/DEMO-SCRIPT.md` sections 4 and 5). So the two receipt frames are sampled at the
    shot's own clock, the middle of the S5 window and the first S6 bake time, with the small
    probe offsets listed in PROBE_OFFSETS because the S6 windows are instants and a frame
    boundary can fall on one. The offset that matched is printed; a capture that never reaches
    the window fails with both times named, which is what happens to the 73.483 s capture today.

WHAT IT DOES NOT DO
    No model is called and nothing goes on the network: every number here is read from pixels the
    ffmpeg on PATH wrote to disk. No recommendation is written and no card is created.

Usage
    python tools/judge_frames_check.py                 check the newest output/demo/nightly-*.mp4
    python tools/judge_frames_check.py --video X.mp4   check a named capture
    python tools/judge_frames_check.py --no-log        do not append a row to DEMO-NIGHTLY.md
    python tools/judge_frames_check.py --out DIR       where the sampled PNGs are written
    python tools/judge_frames_check.py --json X.json   write the measured report here
    python tools/judge_frames_check.py --self-test     build two synthetic captures (one good,
                                                       one with two blank frames and no plate) and
                                                       prove this tool passes the first and fails
                                                       the second with the times named

Exit codes
    0 every check held on every frame, 1 at least one check failed and each failure names its
    frame times, 2 there is nothing to check (no video, or ffprobe cannot read it), which is not
    a pass.

Sources
    the six judged frame times and the two blank ones  knowledge/JUDGE-PANEL-2026-10-26.md lines 11, 33
    the 90 percent blank threshold                  card t_4512b33a body
    the sample formula and the ffmpeg call           tools/judge_panel.py, sample_frames()
    the plate geometry, the palette roles, the font  tools/demo_overlay.py, plan() and FONT_PATH
    the overlay clocks                               tools/demo_overlay.py SHOT_WINDOWS (sections 4 and 5)
    the three minute judged length                   knowledge/DEMO-SCRIPT.md section 2
    the largest colour share measure                 tools/eye_critic.py, measure_image()
"""

from __future__ import annotations

import argparse
import datetime
import glob
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS_DIR)
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import demo_overlay  # noqa: E402  the plate geometry, the palette roles and the caption font
import eye_critic  # noqa: E402  the largest colour share the judge panel already quotes
import judge_panel  # noqa: E402  the newest nightly, the ffprobe read and the ffmpeg call

FRAME_DIR = os.path.join(ROOT, "output", "judge_frames")
NIGHTLY_LOG = os.path.join(ROOT, "knowledge", "DEMO-NIGHTLY.md")

# The six times the judge panel sampled the 2026-10-26 capture at, quoted from
# knowledge/JUDGE-PANEL-2026-10-26.md line 11. They are this tool's baseline sample because they are
# the frames a judge has actually been shown.
SAMPLE_TIMES = (6.1, 18.4, 30.6, 42.9, 55.1, 67.4)
# The three the three minute cut adds (card t_4512b33a body). 100, 130 and 160 s are the tail of a
# 180 s cut; they say nothing about a 73 s capture, so they are skipped there and the skip is stated.
EXTENDED_TIMES = (100.0, 130.0, 160.0)
DEMO_SECONDS = 180          # knowledge/DEMO-SCRIPT.md section 2: three minutes, 10,800 steps
LENGTH_TOLERANCE_S = 20     # judge_panel.measured_lines() already accepts this tolerance

BLANK_SHARE = 0.90          # card t_4512b33a: "no frame over 90 percent one colour"
DIFFER_MIN = 8              # a channel moving by more than 8 levels is a change, not encoder drift
DIFFER_SHARE = 0.01         # and it has to cover 1 percent of the frame to count as a new picture

# The plate and the ink. paper is data/palette.json's role for the plate fill (28, 28, 36) and text
# is (200, 200, 212), so a paper tolerance of 24 sits far from the ink and an ink threshold of 40
# sits far from an encoder's ringing around a flat fill.
PAPER_TOL = 24
INK_MIN = 40
PLATE_PAPER_SHARE = 0.55    # measured: 0.7728 on a rendered plate, 0.0050 on the clean frame under it
LINE_INK_SHARE = 0.002      # a line box with less ink than this drew nothing
ATLAS_IOU_MIN = 0.50        # measured on a rendered line: well above the noise, see --self-test
ATLAS_PAD = 3               # the atlas match may sit this many pixels off the planned box

# The two shots whose frames must carry the receipt, and which clock in SHOT_WINDOWS is used. The
# first window of each key is the one sampled.
RECEIPT_SHOTS = (("S5", "bake"), ("S6", "bake"))
# The S6 bake windows are instants (135.03, 135.03), so a single -ss can land on either side of a
# cut. These offsets are probed in order and the one that matched is reported; the first probe that
# finds a plate wins, and a shot with no plate at any offset fails.
PROBE_OFFSETS = (0.0, 0.5, -0.5, 1.0, -1.0, 1.5, -1.5)

MODEL_LINE_PREFIX = "BAKE MODEL "


class FrameCheckError(RuntimeError):
    """Nothing could be measured. The message is safe to print and says what was missing."""


# ---------------------------------------------------------------------------------------------------------------------
# Which frames, and taking them


def panel_times(duration):
    """The judge panel's own six sample times for a capture of this length, and both time sets.

    Returned separately from this tool's list because they differ on purpose: the panel samples
    evenly over whatever it is given, and this tool samples the six times a judge has already been
    shown. Stating both is what stops the two tools' ideas of "the judged frames" from drifting.
    """
    if not duration:
        return []
    return [round(duration * (index + 0.5) / 6.0, 3) for index in range(6)]


def sample_plan(duration):
    """The times to sample, each with its reason, and the ones skipped with theirs.

    A time past the end of the capture is skipped, not failed: a 73 s capture cannot hold a frame
    at 100 s, and calling that a failed check would make every short capture red for the wrong
    reason. A time before the end is always sampled, and the checks that follow decide it.
    """
    taken, skipped = [], []
    for index, at in enumerate(SAMPLE_TIMES, start=1):
        row = {"label": "panel %d of 6" % index, "at_s": at}
        if duration and at < duration - 0.05:
            taken.append(row)
        else:
            skipped.append(dict(row, reason="the capture ends at %.3f s, before this time" % (duration or 0.0)))
    near_length = bool(duration) and duration >= DEMO_SECONDS - LENGTH_TOLERANCE_S
    for at in EXTENDED_TIMES:
        row = {"label": "cut tail %.0f s" % at, "at_s": at}
        if not near_length:
            skipped.append(dict(row, reason="only sampled once the capture is the judged %d s "
                                           "length (this one is %.3f s)" % (DEMO_SECONDS, duration or 0.0)))
        elif at < duration - 0.05:
            taken.append(row)
        else:
            skipped.append(dict(row, reason="the capture ends at %.3f s, before this time" % duration))
    return taken, skipped


def _ffmpeg():
    found = shutil.which("ffmpeg")
    if not found:
        raise FrameCheckError("ffmpeg is not on PATH, so no frame can be taken and nothing is checked")
    return found


def take_frame(video, at, path):
    """One frame, decoded exactly at `at`, written to `path`.

    The same call `judge_panel.sample_frames()` makes, argument for argument: `-ss` after `-i` so the
    frame is the one at that timestamp and not the nearest keyframe, and one frame only.
    """
    ffmpeg = _ffmpeg()
    result = subprocess.run(
        [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
         "-i", video, "-ss", "%.3f" % at, "-frames:v", "1", path],
        capture_output=True, encoding="utf-8", errors="replace", timeout=300)
    if result.returncode != 0 or not os.path.exists(path):
        raise FrameCheckError("ffmpeg could not take the frame at %.3f s from %s: %s"
                              % (at, os.path.basename(video), (result.stderr or "").strip()[:200]))
    return path


def load_rgb(path):
    """The frame as an RGB array in the overlay's own 768x720 space.

    The overlay's rects are computed for the 3x screen (`demo_overlay.SCALE`). A capture at another
    size is resized onto that grid, and the resize is reported, because a plate measured in the
    wrong grid would be tested against rects that do not describe it.
    """
    with Image.open(str(path)) as handle:
        handle.load()
        image = handle.convert("RGB")
    resized = False
    if image.size != (demo_overlay.FRAME_W, demo_overlay.FRAME_H):
        image = image.resize((demo_overlay.FRAME_W, demo_overlay.FRAME_H), Image.LANCZOS)
        resized = True
    return np.asarray(image).astype(np.int16), resized


# ---------------------------------------------------------------------------------------------------------------------
# The checks


def blank_row(path, facts):
    """One sampled frame as a row: its colour share, and whether that reads as a blank picture."""
    share = facts.get("largest_colour_share")
    return {"path": path, "colours": facts.get("colours"), "largest_colour_share": share,
            "blank": (share is not None and share >= BLANK_SHARE)}


def atlas_mask(text, size):
    """The pixel pattern `text` draws in the video's caption font, as an ink mask and its offset.

    Drawn at (0, 0) with the default anchor, which is exactly how `demo_overlay.render()` draws every
    plate line (`draw.text((line["box"][0], line["box"][1]), ...)`), so the mask and the frame can be
    compared pixel for pixel. This is the font atlas for this check: the same
    `assets/fonts/PressStart2P-Regular.ttf` the captions are burned in with, at the same size.

    The canvas is deliberately taller than one glyph row so nothing is clipped, and the mask is
    cropped back to its own ink before it is returned: a mask that kept the blank rows under the
    text would reach into the plate's next line, count that line's pixels as missing from the mask
    and report an intersection over union of 0.46 for a line that matches at 0.98.
    """
    font = demo_overlay.load_font(size)
    width = len(text) * size + size
    canvas = Image.new("L", (width, size * 3), 0)
    ImageDraw.Draw(canvas).text((0, 0), text, font=font, fill=255)
    full = np.asarray(canvas) > 127
    rows = np.nonzero(full.sum(axis=1))[0]
    columns = np.nonzero(full.sum(axis=0))[0]
    if not len(rows) or not len(columns):
        return full[:size, :width], (0, 0)
    return (full[rows.min():rows.max() + 1, columns.min():columns.max() + 1],
            (int(columns.min()), int(rows.min())))


def best_iou(mask, frame, x0, y0, paper, pad=ATLAS_PAD):
    """The best intersection over union of `mask` against the frame near (x0, y0), and where it sat.

    The search is `pad` pixels in each direction, because a box computed from the plan and a frame
    decoded from h264 can disagree by a pixel or two at a cut. A frame with no plate has almost no
    ink to match, so the best IoU of the search is near zero and the caller's threshold rejects it.
    """
    height, width = mask.shape
    y_from, x_from = max(0, y0 - pad), max(0, x0 - pad)
    region = frame[y_from:y0 + height + pad, x_from:x0 + width + pad]
    if region.size == 0:
        return 0.0, (0, 0)
    ink = np.abs(region - paper).max(axis=2) > INK_MIN
    best, where = 0.0, (0, 0)
    for dy in range(-pad, pad + 1):
        for dx in range(-pad, pad + 1):
            oy, ox = y0 + dy - y_from, x0 + dx - x_from
            if oy < 0 or ox < 0 or oy + height > ink.shape[0] or ox + width > ink.shape[1]:
                continue
            window = ink[oy:oy + height, ox:ox + width]
            union = int(np.logical_or(mask, window).sum())
            if not union:
                continue
            iou = int(np.logical_and(mask, window).sum()) / float(union)
            if iou > best:
                best, where = float(iou), (dy, dx)
    return round(best, 4), where


def plate_facts(frame, plan, model, palette):
    """What the plate's own rect holds: the paper share, the ink per line, and the model name.

    Every rect comes from `demo_overlay.plan()`, which is the geometry the drawing used, so the
    measurement and the render cannot disagree about where a line sits.
    """
    paper = np.array(palette["paper"], dtype=np.int16)
    x0, y0, x1, y1 = plan["plate"]
    crop = frame[y0:y1, x0:x1]
    paper_share = float((np.abs(crop - paper).max(axis=2) <= PAPER_TOL).mean()) if crop.size else 0.0

    lines = []
    model_line = None
    for line in plan["lines"]:
        bx0, by0, bx1, by1 = line["box"]
        band = frame[by0:by1, bx0:bx1]
        ink = np.abs(band - paper).max(axis=2) > INK_MIN
        share = float(ink.mean()) if ink.size else 0.0
        lines.append({"tier": line["tier"], "text": line["source_text"][:60],
                      "ink_share": round(share, 4), "ink_pixels": int(ink.sum())})
        if model_line is None and str(line["source_text"]).startswith(MODEL_LINE_PREFIX):
            model_line = line

    atlas = {"text": None, "iou": None, "offset": None}
    if model_line is not None:
        wanted = MODEL_LINE_PREFIX + str(model)
        mask, (mask_x, mask_y) = atlas_mask(wanted, model_line["size"])
        iou, where = best_iou(mask, frame, model_line["box"][0] + mask_x,
                              model_line["box"][1] + mask_y, paper)
        atlas = {"text": wanted, "iou": iou, "offset": [int(where[0]), int(where[1])],
                 "mask_pixels": int(mask.sum())}
    return {"paper_share": round(paper_share, 4), "lines": lines, "model_line": atlas,
            "plate": list(plan["plate"])}


def shot_frames(video, duration, folder, palette, bake, index, ffmpeg_path=None):
    """The S5 and S6 frames, sampled at their own clock, with the receipt measured on each.

    Returns (rows, failures). A row is a frame the tool managed to take; a failure is a sentence
    naming the shot, its window and the time, and it is what a capture that never reaches the shot
    produces: the 73.483 s capture ends 10 s before the S5 window opens.
    """
    rows, failures = [], []
    model = str((bake.get("bake") or {}).get("model") or "")
    for shot, kind in RECEIPT_SHOTS:
        windows = (demo_overlay.SHOT_WINDOWS.get(shot) or {}).get(kind) or ()
        if not windows:
            failures.append("%s: tools/demo_overlay.py names no %s window for this shot, so there is "
                            "no clock to sample" % (shot, kind))
            continue
        start, end = windows[0]
        base = (start + end) / 2.0 if end > start else start
        label = "%s bake window %.3f to %.3f s, sampled at %.3f s" % (shot, start, end, base)
        if duration and base >= duration - 0.05:
            failures.append("%s: no frame exists at %.3f s because the capture ends at %.3f s, so the "
                            "bake row is not on screen anywhere in this video"
                            % (shot, base, duration))
            continue
        try:
            plan = demo_overlay.plan(shot, bake, index, allow_fallback=True)
        except demo_overlay.OverlayError as exc:
            failures.append("%s: the plate layout cannot be computed, so the receipt cannot be "
                            "measured: %s" % (shot, exc))
            continue
        matched = None
        tried = []
        for offset in PROBE_OFFSETS:
            at = base + offset
            if at < 0 or (duration and at >= duration - 0.05):
                continue
            path = os.path.join(folder, "%s_%s_%06.3f.png" % (os.path.splitext(os.path.basename(video))[0],
                                                              shot, at))
            take_frame(video, at, path)
            frame, resized = load_rgb(path)
            facts = plate_facts(frame, plan, model, palette)
            record = dict(facts, at_s=round(at, 3), offset_s=offset, path=path, shot=shot,
                          resized=resized)
            tried.append(record)
            if facts["paper_share"] >= PLATE_PAPER_SHARE:
                matched = record
                break
        if matched is None:
            best = max(tried, key=lambda row: row["paper_share"]) if tried else None
            failures.append(
                "%s: no bake row plate at %s: the paper colour covers %s of the plate rect %s and it "
                "must cover %.0f percent. The %d time(s) probed were %s."
                % (shot, label,
                   ("%.4f" % best["paper_share"]) if best else "nothing",
                   best["plate"] if best else "none",
                   PLATE_PAPER_SHARE * 100, len(tried),
                   ", ".join("%.3f s" % row["at_s"] for row in tried) or "none inside the capture"))
            rows.extend(tried)
            continue
        rows.extend(tried)
        # The plate is there: now the lines and the model name inside it.
        thin = [row for row in matched["lines"] if row["ink_share"] < LINE_INK_SHARE]
        if thin:
            failures.append("%s at %.3f s: the plate is drawn but %d of its %d line boxes are empty "
                            "(%s), so the row is a plate with no receipt on it"
                            % (shot, matched["at_s"], len(thin), len(matched["lines"]),
                               ", ".join("%r at ink %.4f" % (row["text"][:24], row["ink_share"])
                                         for row in thin[:4])))
        atlas = matched["model_line"]
        if atlas["iou"] is None:
            failures.append("%s at %.3f s: the plate has no %r line, so the model name is not on "
                            "screen" % (shot, matched["at_s"], MODEL_LINE_PREFIX.strip()))
        elif atlas["iou"] < ATLAS_IOU_MIN:
            failures.append("%s at %.3f s: the model name %r does not match the frame in the caption "
                            "font at that line box (intersection over union %.4f, needs %.2f)"
                            % (shot, matched["at_s"], atlas["text"], atlas["iou"], ATLAS_IOU_MIN))
    return rows, failures


def difference_rows(frames):
    """How much each of the last three sampled frames differs from the others.

    The last three, in the order they were sampled, because that is what the card asks: a tail that
    holds one picture looks fine in any single frame and is dead on screen.
    """
    tail = frames[-3:]
    rows = []
    for first in range(len(tail)):
        for second in range(first + 1, len(tail)):
            a = np.asarray(Image.open(tail[first]["path"]).convert("RGB")).astype(np.int16)
            b = np.asarray(Image.open(tail[second]["path"]).convert("RGB")).astype(np.int16)
            if a.shape != b.shape:
                share = 1.0
            else:
                share = float((np.abs(a - b).max(axis=2) > DIFFER_MIN).mean())
            rows.append({"pair": "%.1f s and %.1f s" % (tail[first]["at_s"], tail[second]["at_s"]),
                         "differ_share": round(share, 4), "ok": share >= DIFFER_SHARE})
    return rows


# ---------------------------------------------------------------------------------------------------------------------
# The run


def check(video, folder=None, log=False, log_path=None):
    """Sample, measure, and return the report. Raises FrameCheckError only when nothing can be read."""
    folder = folder or FRAME_DIR
    if not os.path.isdir(folder):
        os.makedirs(folder)
    info = judge_panel.probe_video(video)
    duration = info.get("duration_s")
    if not duration:
        raise FrameCheckError("ffprobe reported no duration for %s, so no frame time can be chosen"
                              % os.path.basename(video))
    palette = demo_overlay.load_palette()
    bake, index = demo_overlay.load_bake()

    taken, skipped = sample_plan(duration)
    frames, failures = [], []
    for row in taken:
        path = os.path.join(folder, "%s_t%06.3f.png" % (os.path.splitext(os.path.basename(video))[0],
                                                        row["at_s"]))
        take_frame(video, row["at_s"], path)
        facts = eye_critic.measure_image(path)
        if facts.get("largest_colour_share") is None:
            raise FrameCheckError("the frame at %.3f s was written but its pixels could not be "
                                  "measured: %s" % (row["at_s"], facts.get("error")))
        frames.append(dict(row, **blank_row(path, facts)))

    blanks = [row for row in frames if row["blank"]]
    if blanks:
        failures.append(
            "blank: %d of the %d sampled frames are one colour over %.0f percent: %s"
            % (len(blanks), len(frames), BLANK_SHARE * 100,
               ", ".join("%.1f s at %.3f" % (row["at_s"], row["largest_colour_share"]) for row in blanks)))

    shots, shot_failures = shot_frames(video, duration, folder, palette, bake, index)
    failures.extend(shot_failures)

    diffs = difference_rows(frames) if len(frames) >= 3 else []
    still = [row for row in diffs if not row["ok"]]
    if still:
        failures.append(
            "frames differ: %d of the %d pairs in the last three samples are the same picture "
            "(%s), and each pair must differ in %.2f of its pixels"
            % (len(still), len(diffs),
               "; ".join("%s differ in %.4f" % (row["pair"], row["differ_share"]) for row in still),
               DIFFER_SHARE))

    report = {
        "tool": "tools/judge_frames_check.py",
        "at": eye_critic.utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "video": video,
        "duration_s": duration,
        "width": info.get("width"), "height": info.get("height"), "fps": info.get("fps"),
        "sample_times_s": [row["at_s"] for row in frames],
        "skipped_samples": skipped,
        "panel_six_times_s": panel_times(duration),
        "frames": frames,
        "receipt_shots": shots,
        "difference": diffs,
        "difference_measured": len(frames) >= 3,
        "model": str((bake.get("bake") or {}).get("model") or ""),
        "failures": failures,
        "ok": not failures,
        "exit": 0 if not failures else 1,
    }
    if log:
        report["nightly_row"] = append_nightly_row(report, log_path or NIGHTLY_LOG)
    return report


def render_report(report):
    """The report as the lines a person reads, measured first and verdict last."""
    lines = ["judge frames: %s" % os.path.relpath(report["video"], ROOT).replace("\\", "/"),
             "duration %.3f s, %s x %s at %s fps, model on the plate %r"
             % (report["duration_s"], report["width"], report["height"], report["fps"], report["model"]),
             "sampled %d frame(s) at %s"
             % (len(report["frames"]), ", ".join("%.1f s" % row["at_s"] for row in report["frames"]))]
    for row in report["skipped_samples"]:
        lines.append("not sampled: %.1f s (%s)" % (row["at_s"], row["reason"]))
    lines.append("blank check, one colour share per frame (over %.0f percent fails):"
                 % (BLANK_SHARE * 100))
    for row in report["frames"]:
        lines.append("  %6.1f s  share %.3f  colours %6s  %s"
                     % (row["at_s"], row["largest_colour_share"], row["colours"],
                        "BLANK" if row["blank"] else "picture"))
    if report["receipt_shots"]:
        lines.append("bake row check, paper share and model name match:")
        for row in report["receipt_shots"]:
            atlas = row["model_line"]
            lines.append("  %-6s at %7.3f s (offset %+.1f)  paper %.4f  model %r iou %s at offset %s"
                         % (row.get("shot"), row["at_s"], row["offset_s"],
                            row["paper_share"], atlas.get("text"), atlas.get("iou"), atlas.get("offset")))
    if report["difference"]:
        lines.append("last three samples, share of pixels that moved (under %.2f fails):" % DIFFER_SHARE)
        for row in report["difference"]:
            lines.append("  %-22s %.4f  %s" % (row["pair"], row["differ_share"],
                                               "differs" if row["ok"] else "SAME PICTURE"))
    else:
        lines.append("the last three samples were not compared: this capture gives %d sampled frame(s) "
                     "and the check needs three" % len(report["frames"]))
    if report["panel_six_times_s"]:
        lines.append("for reference, judge_panel's own six times on this capture would be: %s"
                     % ", ".join("%.1f s" % at for at in report["panel_six_times_s"]))
    if report["failures"]:
        lines.append("VERDICT FAIL, %d finding(s):" % len(report["failures"]))
        lines.extend("  - %s" % text for text in report["failures"])
    else:
        lines.append("VERDICT PASS: every sampled frame has picture, both receipt frames carry the bake "
                     "row and the model name, and the last three differ.")
    return "\n".join(lines)


def nightly_row(report):
    """One DEMO-NIGHTLY.md row: the date, the tool, the video, then each check with its verdict."""
    date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    video = os.path.relpath(report["video"], ROOT).replace("\\", "/")
    verdict = "PASS" if report["ok"] else "FAIL"
    detail = []
    blanks = [row for row in report["frames"] if row["blank"]]
    detail.append("%d sampled at %s s, %d blank%s"
                  % (len(report["frames"]), " ".join("%.1f" % row["at_s"] for row in report["frames"]),
                     len(blanks),
                     (" (%s)" % ", ".join("%.1f s %.3f" % (row["at_s"], row["largest_colour_share"])
                                          for row in blanks)) if blanks else ""))
    detail.append("bake row: %d frame(s) measured, %d failure(s)"
                  % (len(report["receipt_shots"]),
                     len([text for text in report["failures"] if text.startswith(("S5", "S6"))])))
    if report["difference"]:
        detail.append("last three differ %s"
                      % " ".join("%.4f" % row["differ_share"] for row in report["difference"]))
    else:
        detail.append("last three not compared (%d sampled)" % len(report["frames"]))
    row = "%s | judge-frames | %s | JUDGE-FRAMES %s (exit %d, %s)" % (
        date, video, verdict, report["exit"], "; ".join(detail))
    if report["failures"]:
        row += " | " + " | ".join(_plain(text) for text in report["failures"])
    return row


def _plain(text):
    fixed = str(text)
    for dash in ("\u2014", "\u2013", "\u2012", "\u2015", "\u2212"):
        fixed = fixed.replace(dash, "-")
    return " ".join(fixed.split())


def append_nightly_row(report, path=None):
    """Append this run's row to the nightly log, and return the row that was written.

    The log's own header says one line per nightly run, and a check that writes no row is a check
    nobody reads the next morning. One consequence is stated here because it is not obvious:
    `tools/judge_panel.py` quotes the LAST line of this file as "the nightly log's own last row" in
    every panel it writes, so a judge-frames row becomes what the next panel sees. That is the
    honest order (the newest measurement is the newest line) and the row names its own tool, so the
    panel prints it as what it is rather than as the capture row.
    """
    path = path or NIGHTLY_LOG
    row = _plain(nightly_row(report))
    folder = os.path.dirname(os.path.abspath(path))
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(row + "\n")
    return row


# ---------------------------------------------------------------------------------------------------------------------
# Self test: two synthetic captures, one that must pass and one that must fail


def synthetic_source():
    """A 768x720 base picture to hang the overlay on, with no dependency on a capture.

    Preferred is a real lit frame from `output/judge_frames` when one is there, because the encoder
    then sees the same kind of picture the check will meet in the gate. When there is none, the base
    is built from `data/palette.json`'s own colours in blocks, which is enough picture to be neither
    blank nor flat and uses nothing this repository does not carry. The plate's `paper` colour is
    left out of those blocks, so a base frame cannot pass for a drawn plate and the self test's
    broken capture really has no bake row on it.
    """
    candidates = sorted(glob.glob(os.path.join(FRAME_DIR, "*_f0*.png")))
    for path in candidates:
        with Image.open(path) as handle:
            image = handle.convert("RGB")
        facts = eye_critic.measure_image(path)
        share = facts.get("largest_colour_share")
        if share is not None and share < BLANK_SHARE:
            return (image.resize((demo_overlay.FRAME_W, demo_overlay.FRAME_H)),
                    "output/judge_frames/" + os.path.basename(path))
    palette = demo_overlay.load_palette()
    paper = np.array(palette["paper"], dtype=np.int16)
    colours = [value for value in palette.values()
               if int(np.abs(np.array(value, dtype=np.int16) - paper).max()) > PAPER_TOL]
    image = Image.new("RGB", (demo_overlay.FRAME_W, demo_overlay.FRAME_H), colours[0])
    draw = ImageDraw.Draw(image)
    for row in range(0, demo_overlay.FRAME_H, 60):
        for column in range(0, demo_overlay.FRAME_W, 60):
            draw.rectangle([column, row, column + 59, row + 59],
                           fill=colours[(row // 60 * 7 + column // 60) % len(colours)])
    return image, "data/palette.json colour blocks"


def build_capture(folder, seconds, blank_at=(), receipt_at=None, base=None, source_note=""):
    """Write a synthetic capture one frame per second, with the overlay where it is asked for.

    One frame per second keeps a self test short: the checks only ever sample named timestamps, so a
    low frame rate cannot change a verdict, and ffprobe still reports the duration that decides
    whether the three tail times are sampled at all.
    """
    base = base or synthetic_source()[0]
    palette = demo_overlay.load_palette()
    bake, index = demo_overlay.load_bake()
    receipt_at = receipt_at or {}
    frames = os.path.join(folder, "frames")
    if not os.path.isdir(frames):
        os.makedirs(frames)
    for second in range(seconds):
        image = base.copy()
        draw = ImageDraw.Draw(image)
        # A marker that moves every second, so two sampled seconds are two pictures and the "do they
        # differ" check has something real to measure instead of passing on encoder noise.
        x = 40 + (second * 37) % (demo_overlay.FRAME_W - 220)
        draw.rectangle([x, demo_overlay.FRAME_H - 150, x + 170, demo_overlay.FRAME_H - 30],
                       fill=palette["text"])
        if second in blank_at:
            image = Image.new("RGB", (demo_overlay.FRAME_W, demo_overlay.FRAME_H), (0, 0, 0))
        else:
            for shot, (first, last) in receipt_at.items():
                if first <= second <= last:
                    image, _plan = demo_overlay.render(
                        image, shot, bake, index, allow_fallback=True)
                    break
        image.save(os.path.join(frames, "%04d.png" % second))
    video = os.path.join(folder, "capture.mp4")
    ffmpeg = _ffmpeg()
    result = subprocess.run(
        [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
         "-framerate", "1", "-i", os.path.join(frames, "%04d.png"),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "1", video],
        capture_output=True, encoding="utf-8", errors="replace", timeout=600)
    if result.returncode != 0:
        raise FrameCheckError("ffmpeg could not build the self test capture: %s"
                              % (result.stderr or "").strip()[:300])
    return video, source_note


def self_test(folder=None, log=False, log_path=None):
    """Prove both directions: a capture that holds every condition is a PASS, a broken one names it.

    The good capture carries the S5 plate over its window and the S6 plate over its first bake time,
    a moving marker so the tail frames differ, and no blank frame. The broken one is the same
    capture with two frames blacked out at the 18.4 s and 30.6 s sample times and cut short of the
    S5 window, which is the shape of the 2026-10-26 failure this card was written from.
    """
    root = folder or os.path.join(ROOT, "output", "_judge_frames_selftest")
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(root)
    base, note = synthetic_source()
    s5 = demo_overlay.SHOT_WINDOWS["S5"]["bake"][0]
    s6 = demo_overlay.SHOT_WINDOWS["S6"]["bake"][0][0]
    good_seconds = int(s6) + 4
    good_video, _ = build_capture(
        os.path.join(root, "good"), good_seconds,
        receipt_at={"S5": (int(s5[0]) - 1, int(s5[1]) + 1), "S6": (int(s6) - 1, int(s6) + 2)},
        base=base, source_note=note)
    good = check(good_video, folder=os.path.join(root, "good_frames"), log=False)
    print(render_report(good))
    if not good["ok"]:
        raise FrameCheckError("self test FAILED: the capture built to hold every condition came back "
                              "FAIL (%s)" % "; ".join(good["failures"]))

    broken_video, _ = build_capture(
        os.path.join(root, "broken"), 70,
        # Blank the three seconds around each sample time, not one frame: at a frame rate of one a
        # second, an exact -ss can land on either side of a boundary, and the fixture's job is to put
        # a black frame where the tool will look, not to test which frame ffmpeg rounds to.
        blank_at=sorted({second for at in (18.4, 30.6) for second in range(int(at) - 1, int(at) + 2)}),
        base=base, source_note=note)
    broken = check(broken_video, folder=os.path.join(root, "broken_frames"), log=False)
    print()
    print(render_report(broken))
    wanted = ("18.4 s", "30.6 s", "no frame exists at")
    missing = [piece for piece in wanted if not any(piece in text for text in broken["failures"])]
    if broken["ok"] or missing:
        raise FrameCheckError("self test FAILED: the broken capture should fail naming %s, it said %s"
                              % (", ".join(wanted), broken["failures"]))
    print()
    print("self test PASS: the good capture on %s measured ok, the broken one failed naming 18.4 s, "
          "30.6 s and the missing S5 and S6 windows" % note)
    return {"good": good, "broken": broken}


# ---------------------------------------------------------------------------------------------------------------------
# Main


def build_parser():
    parser = argparse.ArgumentParser(
        description="Sample the judged frames and assert the picture and the bake row are really there.")
    parser.add_argument("--video", default=None,
                        help="the capture to check (default: the newest output/demo/nightly-*.mp4)")
    parser.add_argument("--out", default=None, help="where the sampled PNGs are written")
    parser.add_argument("--json", default=None, help="write the measured report to this file")
    parser.add_argument("--log", dest="log", action="store_true", default=True,
                        help="append a row to knowledge/DEMO-NIGHTLY.md (the default)")
    parser.add_argument("--no-log", dest="log", action="store_false",
                        help="do not touch knowledge/DEMO-NIGHTLY.md")
    parser.add_argument("--log-path", default=None, help="write the nightly row here instead")
    parser.add_argument("--self-test", action="store_true",
                        help="build a good and a broken capture and prove pass and fail")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.self_test:
        try:
            self_test(log=args.log, log_path=args.log_path)
        except (FrameCheckError, demo_overlay.OverlayError) as exc:
            print("self test FAILED: %s" % exc)
            return 2
        return 0

    video = args.video or judge_panel.newest_nightly()
    if not video:
        print("no nightly capture under %s: nothing to check, and that is not a pass"
              % os.path.relpath(judge_panel.DEMO_DIR, ROOT))
        return 2
    if not os.path.exists(video):
        print("no such video: %s" % video)
        return 2
    try:
        report = check(video, folder=args.out, log=args.log, log_path=args.log_path)
    except (FrameCheckError, demo_overlay.OverlayError) as exc:
        print("cannot check: %s" % exc)
        return 2
    print(render_report(report))
    if args.json:
        folder = os.path.dirname(os.path.abspath(args.json))
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
        with open(args.json, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, indent=1, sort_keys=True)
        print("report: %s" % os.path.relpath(args.json, ROOT).replace("\\", "/"))
    if args.log:
        print("nightly row: %s" % os.path.relpath(args.log_path or NIGHTLY_LOG, ROOT).replace("\\", "/"))
    return report["exit"]


if __name__ == "__main__":
    sys.exit(main())
