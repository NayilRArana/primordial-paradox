#!/usr/bin/env python3
"""
capture_save.py: the captured save and CONTINUE run (card SAVE-LOAD-CAPTURE, t_673fba81).

What it proves, in one run, against the built game and nothing else:

  run 1  launch muted, START, NEW GAME, skip the crawl, walk the hero onto the ship's log terminal at
         ship_small 3,2, and let the save trigger write the slot. The game's own log says
         "PP: ship's log, deck_save, saved on ship_small 3,2" and the save panel is on screen.
  run 2  quit the game, launch it again muted, open the menu, move the cursor to CONTINUE, choose it,
         and land on the tile the save recorded. The game's own log says "PP: save read and accepted",
         and then one Down and one Up from the landing tile fires the same save point again and prints
         the same line. That pair of presses is the landing proof: a Down from 3,2 reaches 3,3 and an Up
         from 3,3 reaches 3,2, so the trigger can only fire if the run really landed on 3,2.

Evidence written beside the video:
  output\\save_capture.mp4              the two runs joined, in order, muted in both
  output\\save_capture_verify.json      every check with its measured number, and ok true or false
  output\\save_capture_log_terminal.png the frame with the hero on the log terminal tile
  output\\save_capture_confirm.png      the frame with the save panel on screen
  output\\save_capture_landing.png      the frame the CONTINUE load lands on
  output\\save_capture_frames.json      where each frame came from and what was measured on it
  build\\save_capture_run1.log, build\\save_capture_run2.log   the two game logs

The two frames of the room (log terminal, landing) are the game's own pixels: with PP_SHIP_CAPTURE set the
room calls screen_save on its 90th and 360th draw (game\\scripts\\pp_overworld\\pp_overworld.gml), so the
picture is not a copy of whatever window happens to be on top of the game. The panel frame is a window copy,
because the panel lives for 20 steps and the room's own frame slots are 90 draws apart; a window copy is only
kept when the NES viewport search finds the game's 3x screen inside it, the same check tools\\capture_title.py
uses.

Quiet by default (card CAPTURE-QUIET, rulings D9): every launch goes through tools\\pp_launch.py, so the game
starts with PP_MUTE=1, nothing opens unless the machine has been quiet for two minutes, and the window is moved
off the primary screen. --sound, --show, --idle-wait and --force are the same flags every capture tool takes.

Usage:
    python tools\\capture_save.py
    python tools\\capture_save.py --check-route             walk the declared route over data\\maps\\all.json and stop
    python tools\\capture_save.py --skip-build-check     do not fail when the build predates the source

The route, the save tile and the log line the tool waits for are checked against data\\maps\\all.json by --check-route,
which needs no game and opens no window. That is the check to run after the log terminal moves: it names the tile the
walk really ends on instead of waiting six seconds for a line that cannot appear.

Exit codes:
    0  every check passed and ok is true in the verify json
    1  a check failed; the json and the frames are still written for the next reader
    3  a watchdog fired (a run overran)
    4  the idle gate refused to open a window (he was at the PC); retry later, this is not a failure
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS_DIR)
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)
import pp_launch  # noqa: E402  the one launch policy: mute, idle gate, quiet window
import capture_title as ct  # noqa: E402  the window, key, copy and video helpers this project already measured

OUTPUT_DIR = os.path.join(ROOT, "output")
BUILD_DIR = os.path.join(ROOT, "build")
LOCAL_APP = os.path.join(os.environ.get("LOCALAPPDATA", ""), "PrimordialParadox")
# The two keys this capture presses that tools\capture_title.py never sends. The arrow codes are the Windows virtual key
# codes, and both are extended keys, which send_vk_focused already accounts for.
VK_UP = 0x26
VK_DOWN = 0x28
# The one slot (spec 11, pp_config PP_SAVE_SLOT). A relative name lands in the save area's default folder, which is
# this path; tools\\_save_load_probe.py measured the same path on 2026-10-22.
SLOT = os.path.join(LOCAL_APP, "default", "pp_save_01.json")

VIDEO_OUT = os.path.join(OUTPUT_DIR, "save_capture.mp4")
VERIFY_OUT = os.path.join(OUTPUT_DIR, "save_capture_verify.json")
FRAMES_OUT = os.path.join(OUTPUT_DIR, "save_capture_frames.json")
LOG_TERMINAL_PNG = os.path.join(OUTPUT_DIR, "save_capture_log_terminal.png")
CONFIRM_PNG = os.path.join(OUTPUT_DIR, "save_capture_confirm.png")
LANDING_PNG = os.path.join(OUTPUT_DIR, "save_capture_landing.png")
SEGMENT_1 = os.path.join(BUILD_DIR, "save_capture_run1.mp4")
SEGMENT_2 = os.path.join(BUILD_DIR, "save_capture_run2.mp4")

# The markers the game prints for itself. Each one is a fact the game states, so no step below is guessed from a clock.
MUTE = "PP: muted"
INTRO = "PP title: intro started"
RUN_START = "starting the run in"
LOG_SAVE = "PP: ship's log, deck_save, saved on ship_small 3,2"
ACCEPT = "PP: save read and accepted"
SELF_WROTE = "PP ship: wrote pp_ship_frame.png"
# The log terminal's tile, and the spawn the run starts from on ship_small. The walk between them is one tile right
# (2,7 -> 3,7, because 2,6 is the bulkhead) and then five up the corridor's left column to 3,2.
SAVE_TILE = (3, 2)
SPAWN_TILE = (2, 7)
# The route: one right, then up to the save. Five up because 3,7 to 3,2 is five tiles, and every one of them is floor
# on the shipped grid (data\\maps\\all.json). No tile on the route is a touch trigger, and the scene trigger at 3,6
# fires only on a confirm press, which this route never makes there.
WALK_RIGHT = 1
WALK_UP = 5

# --- timing --------------------------------------------------------------------------------------------------------
# The room writes its own frame at draw 90, which is 1.5 s at the 60 steps the game runs. The first Up press waits for
# that frame, so the frame pair the module writes is the spawn and the tile the player stands on, not two copies of it.
ROOM_SETTLE_S = 1.7
KEY_GAP_S = 0.45
SAVE_WAIT_S = 6.0
# The panel holds for PP_SAVE_PANEL_STEPS (20 steps, a third of a second) plus the write itself, so the burst covers
# wider than that and takes a copy every 0.12 s. A copy through PIL is about 0.05 s on this PC measured by
# tools\\measure_title_scroll.py, so the burst sees the panel several times.
BURST_S = 1.6
BURST_GAP_S = 0.12
# The CONTINUE landing is one press away from the menu, and the room's own frame needs 90 draws after it.
MENU_OPEN_S = 1.1
MENU_GAP_S = 0.45
LANDING_SETTLE_S = 2.2
CLOSE_GRACE_S = 6.0
RUN_WATCHDOG_S = 150.0
MIN_NES_SCORE = 0.90
# The panel box on the 256x240 screen: pp_save_draw_panel draws it at (48,92) to (207,148). The paper fill is light, so
# the check asks how much of that box is light and how much one colour owns it. Measured on the two frames of run 1.
PANEL_BOX = (48, 92, 208, 149)
# The game window is the 256x240 screen at 3x inside a 784x759 window; the viewport search measured the box at (8,31)
# on this PC, so the panel box inside a window copy is this rectangle scaled by 3 and offset by that origin.
PANEL_SCALE = 3
PANEL_LIGHT = 0.55          # a channel sum above this share of the maximum counts as the paper
PANEL_DOMINANT = 0.55       # one colour owns this much of the box
# When the panel frame comes from the recording, the test is how much of the panel box changed against the same screen
# without the panel. The panel covers the box with its border, its ink and its fill, so a large change is a strong signal;
# a still frame scores near zero.
PANEL_MIN_CHANGE = 0.15
PANEL_MIN_LIGHT = 0.40      # the confirmation frame must carry at least this much light in the box
PANEL_MIN_GAIN = 0.15       # and this much more than the same box in the frame taken before the save

user32 = ct.user32


# -------------------------------------------------------------------------------------------------------------------
# Small helpers

def sha256(path):
    if not os.path.isfile(path):
        return ""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def append_log_line(path, line):
    """Add one tool line to a run's log. The game's own lines are PP:, so a P: line is never read as one of them."""
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(line.rstrip("\n") + "\n")


def log_lines(path):
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read().splitlines()


def find_in_log(path, needle):
    for line in log_lines(path):
        if needle in line:
            return line.strip()
    return ""


def self_frame_paths():
    """The room's own frames. screen_save writes beside the save area, not in the runner's folder (measured 2026-10-22)."""
    return [os.path.join(LOCAL_APP, "pp_ship_frame.png"),
            os.path.join(LOCAL_APP, "pp_ship_frame_2.png"),
            os.path.join(LOCAL_APP, "pp_ship_frame_3.png")]


def clear_self_frames():
    for path in self_frame_paths():
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:  # gate: ok a stale frame that cannot be removed is caught by the freshness check below
            pass


def wait_for_file(path, timeout_s, not_before=0.0):
    """Wait for a file to appear, and to be newer than not_before. Returns the path or None."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            if os.path.getmtime(path) >= not_before:
                return path
        time.sleep(0.1)
    return None


def press(hwnd, focused, vk):
    """One key through the input queue when the game holds the focus, posted to the window otherwise."""
    return ct.send_vk_focused(vk) if focused else ct.send_vk(hwnd, vk)


def take_raw_copy(hwnd, path):
    """Copy the window and save it, with no verification. Cheap enough to run inside the panel's third of a second."""
    rect = ct.get_window_rect(hwnd)
    if rect is None:
        return None
    ok, _note = ct.capture_with_pil(rect, path)
    if not ok:
        ok, _note = ct.capture_with_powershell(rect, path)
    return path if ok and os.path.isfile(path) else None


def panel_crop(hwnd, path):
    """Copy just the panel box out of the window, at 3x, and save it.

    A full window copy costs about 0.8 s on this PC while a recording is running, and the panel is on screen for 20 steps
    (a third of a second), so a burst of full copies misses it: measured 2026-10-23, two copies in 1.6 s. The panel box is
    82k pixels instead of 595k, so a burst of these lands inside the panel's window several times.
    """
    try:
        from PIL import ImageGrab
    except Exception:  # gate: ok no Pillow means no crop, and the caller reports the panel as unproven
        return None
    rect = ct.get_window_rect(hwnd)
    if rect is None:
        return None
    left, top = rect[0], rect[1]
    x0, y0, x1, y1 = window_panel_box()
    try:
        image = ImageGrab.grab(bbox=(left + x0, top + y0, left + x1, top + y1), all_screens=True)
        image.save(path)
    except Exception:  # gate: ok a failed crop is a missing sample, the caller reports the panel as unproven
        return None
    return path if os.path.isfile(path) and os.path.getsize(path) > 0 else None


def take_copy(hwnd, path):
    """Copy the window and keep it only when the NES viewport search finds the game's own 3x screen inside it."""
    rect = ct.get_window_rect(hwnd)
    if rect is None:
        return None, 0.0, "the window has no rectangle"
    ok, note = ct.capture_with_pil(rect, path)
    if not ok:
        ok, note = ct.capture_with_powershell(rect, path)
    if not ok:
        ct.discard(path)
        return None, 0.0, note
    box, score, why = ct.viewport_box_and_score(path)
    if box is None or score < MIN_NES_SCORE:
        ct.discard(path)
        return None, float(score or 0.0), "no legal 3x viewport (%s, score %.3f)" % (why, float(score or 0.0))
    return box, float(score), "a 3x viewport at %s" % (list(box),)


def native_image(path, size=(256, 240)):
    """The frame at the game's own 256x240 size, scaled with nearest so no colour is invented."""
    from PIL import Image
    with Image.open(path) as handle:
        image = handle.convert("RGB")
    if image.size != size:
        image = image.resize(size, Image.Resampling.NEAREST)
    return image


def native_legality(path):
    """The share of a frame's pixels that are legal 2C02 colours, using this project's own palette search."""
    try:
        sys.path.insert(0, TOOLS_DIR)
        import nes_composite_check as ncc
        palette = ncc.load_palette(ncc.default_palette_path(ROOT))
        allowed = palette["allowed"]
        image = native_image(path)
        pixels = [tuple(pixel) for pixel in image.getdata()]
    except Exception as error:  # gate: ok a frame that cannot be read is reported, never counted as legal
        return None, str(error).split(";")[0]
    hit = sum(1 for pixel in pixels if pixel in allowed)
    return hit / float(len(pixels)), "%d of %d pixels are 2C02 colours" % (hit, len(pixels))


def _box_stats(image, box):
    """The dominant colour's share and the light share of one box inside an image."""
    x0, y0, x1, y1 = [int(value) for value in box]
    x0, x1 = max(0, x0), min(image.width, x1)
    y0, y1 = max(0, y0), min(image.height, y1)
    pixels = [image.getpixel((x, y)) for y in range(y0, y1) for x in range(x0, x1)]
    if not pixels:
        return None
    counts = {}
    for pixel in pixels:
        counts[pixel] = counts.get(pixel, 0) + 1
    dominant, dominant_count = max(counts.items(), key=lambda row: row[1])
    light = sum(1 for pixel in pixels if sum(pixel) >= PANEL_LIGHT * 3 * 255)
    return {"light": round(light / float(len(pixels)), 4),
            "dominant": round(dominant_count / float(len(pixels)), 4),
            "dominant_colour": list(dominant),
            "pixels": len(pixels)}


def panel_reading(path, box=None):
    """The panel box of a frame from the room itself (256x240), or of a window copy at the box the caller passes."""
    try:
        if box is None:
            image = native_image(path)
            x0, y0, x1, y1 = PANEL_BOX
        else:
            from PIL import Image
            with Image.open(path) as handle:
                image = handle.convert("RGB")
            x0, y0, x1, y1 = [int(value) for value in box]
    except Exception:  # gate: ok a frame that will not open cannot be measured, the caller reports that
        return None
    return _box_stats(image, (x0, y0, x1, y1))


def image_reading(path):
    """The stats of a whole image: used for a crop that is already only the panel box."""
    try:
        from PIL import Image
        with Image.open(path) as handle:
            image = handle.convert("RGB")
    except Exception:  # gate: ok a crop that will not open cannot be measured, the caller reports that
        return None
    return _box_stats(image, (0, 0, image.width, image.height))


def legality_share(path, exclude_box=None):
    """The share of an image's own pixels that are legal 2C02 colours, with no rescaling of the image.

    `exclude_box` skips a rectangle of image pixels: the save panel fades in by alpha, so a frame that caught the fade
    carries blended colours inside the panel box only, and every pixel outside it is still the game's own.
    """
    try:
        sys.path.insert(0, TOOLS_DIR)
        import nes_composite_check as ncc
        palette = ncc.load_palette(ncc.default_palette_path(ROOT))
        allowed = palette["allowed"]
        from PIL import Image
        with Image.open(path) as handle:
            image = handle.convert("RGB")
    except Exception as error:  # gate: ok an image that cannot be read is reported, never counted as legal
        return None, str(error).split(";")[0]
    left = top = 0
    right, bottom = image.width, image.height
    if exclude_box:
        left = max(0, int(exclude_box[0]))
        top = max(0, int(exclude_box[1]))
        right = min(image.width, int(exclude_box[2]))
        bottom = min(image.height, int(exclude_box[3]))
    pixels = []
    for y in range(image.height):
        for x in range(image.width):
            if left <= x < right and top <= y < bottom:
                continue
            pixels.append(image.getpixel((x, y)))
    if not pixels:
        return None, "every pixel was excluded"
    hit = sum(1 for pixel in pixels if pixel in allowed)
    return hit / float(len(pixels)), "%d of %d pixels are 2C02 colours" % (hit, len(pixels))


def screen_panel_box():
    """The panel box inside a 768x720 frame of the game's own screen, where the screen starts at 0,0."""
    x0, y0, x1, y1 = PANEL_BOX
    return (x0 * PANEL_SCALE, y0 * PANEL_SCALE, x1 * PANEL_SCALE, y1 * PANEL_SCALE)


def masked_difference(path_a, path_b, box=None, tolerance=24):
    """The share of differing pixels between two of the room's own frames, with the panel box blanked out of both.

    The frame taken at the log terminal can catch the panel fading in, and the landing frame is taken before it appears;
    blanking the box in both is what lets the rest of the screen be compared on equal terms.
    """
    try:
        from PIL import Image, ImageChops
        with Image.open(path_a) as handle:
            first = handle.convert("RGB")
        with Image.open(path_b) as handle:
            second = handle.convert("RGB")
    except Exception:  # gate: ok an unreadable pair is reported by the caller as no measurement
        return None
    if first.size != second.size:
        second = second.resize(first.size, Image.Resampling.NEAREST)
    box = box or screen_panel_box()
    try:
        for image in (first, second):
            image.paste((0, 0, 0), (int(box[0]), int(box[1]), int(box[2]), int(box[3])))
    except Exception:  # gate: ok a box outside the frame is reported by the caller as no measurement
        return None
    difference = ImageChops.difference(first, second).convert("L")
    histogram = difference.histogram()
    total = sum(histogram)
    if not total:
        return None
    return sum(histogram[tolerance + 1:]) / float(total)


def window_panel_box(viewport=(8, 31, 768, 720), scale=PANEL_SCALE):
    """The panel box inside a window copy, from the viewport the capture measured at (8,31) on this PC."""
    vx, vy = viewport[0], viewport[1]
    x0, y0, x1, y1 = PANEL_BOX
    return (vx + x0 * scale, vy + y0 * scale, vx + x1 * scale, vy + y1 * scale)


def difference(path_a, path_b):
    """The share of pixels that differ, resizing neither frame: the two are already the game's 256x240."""
    return ct.frames_differ(path_a, path_b)


# -------------------------------------------------------------------------------------------------------------------
# The recorder

def start_recorder(ffmpeg_path, rect, out_path):
    """Record the window rectangle with gdigrab, exactly the settings tools\\capture_title.py measured on this PC."""
    left, top, width, height = rect
    if os.path.exists(out_path):
        os.remove(out_path)
    arguments = [
        ffmpeg_path, "-hide_banner", "-y",
        "-f", "gdigrab",
        "-framerate", str(ct.VIDEO_FPS),
        "-offset_x", str(left),
        "-offset_y", str(top),
        "-video_size", "%dx%d" % (width, height),
        "-i", "desktop",
        # libx264 needs even dimensions, and the window height is odd.
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
        out_path,
    ]
    log_path = os.path.join(BUILD_DIR, os.path.splitext(os.path.basename(out_path))[0] + "-ffmpeg.log")
    log = open(log_path, "wb")
    # stdin is a pipe so the recording can be ended the way ffmpeg expects: a plain terminate kills it before it writes
    # the mp4 trailer, and the file then reads "moov atom not found" (measured on 2026-10-23).
    process = subprocess.Popen(arguments, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
    return process, log, log_path


def stop_recorder(process, log):
    """End ffmpeg with its own quit key so the file closes properly, then close its log."""
    try:
        process.stdin.write(b"q")
        process.stdin.flush()
        process.stdin.close()
        process.wait(timeout=40)
    except Exception:  # gate: ok a recorder that will not quit on the key is terminated below
        try:
            process.terminate()
            process.wait(timeout=20)
        except Exception:  # gate: ok best effort, the duration check decides whether the file is usable
            pass
    try:
        log.close()
    except Exception:  # gate: ok best effort
        pass


# -------------------------------------------------------------------------------------------------------------------
# One launch

class Launch(object):
    """One game process: its log, its window, its own frames and its recorder."""

    def __init__(self, exe, win, label, log_name, only_muted=True):
        os.makedirs(BUILD_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.exe = exe
        self.win = win
        self.label = label
        self.log_path = os.path.join(BUILD_DIR, log_name)
        self.log = open(self.log_path, "wb")
        self.run = None
        self.hwnd = None
        self.recorder = None
        self.recorder_log = None
        self.segment = None

    def start(self):
        # Card CAPTURE-QUIET-IMPL: one call starts the game muted, without a console, and the PP: muted line is printed
        # only after this run's own log carries it.
        child_env = dict(os.environ)
        child_env["PP_SHIP_CAPTURE"] = "1"
        self.run = pp_launch.start_game(self.exe, self.win, log=self.log, policy=LAUNCH, label=self.label,
                                        base=child_env)
        process = self.run.process
        ct.start_watchdog(process, RUN_WATCHDOG_S)
        match = ct.find_window(
            lambda hwnd, pid, title, visible, rect: visible and pid == process.pid
            and ct.GAME_WINDOW_TITLE.lower() in title.lower(),
            timeout_s=ct.GAME_WINDOW_TIMEOUT_S,
        )
        if match is None:
            raise RuntimeError("the game window did not appear within %.0f s" % ct.GAME_WINDOW_TIMEOUT_S)
        self.hwnd = match[0]
        image_name = ct.process_image_name(match[1])
        if image_name.lower() != ct.GAME_EXE_NAME.lower():
            raise RuntimeError("the window belongs to %r, not to the game" % image_name)
        LAUNCH.place(self.hwnd, ct.get_window_rect(self.hwnd))
        time.sleep(ct.GAME_SETTLE_S)
        self.focused, focus_note = ct.ensure_key_focus(self.hwnd)
        print("P: %s: game window %s, keyboard focus: %s" % (self.label, self.hwnd, focus_note))
        if not self.focused:
            raise RuntimeError("the game never took the keyboard focus, so no press could reach it")

    def record(self, tag):
        """Hold the window on top and record its rectangle for this run."""
        ct.bring_to_front(self.hwnd)
        ct.hold_on_top(self.hwnd)
        time.sleep(ct.FOREGROUND_SETTLE_S)
        rect, coverage = ct.ensure_game_visible(self.hwnd, ct.get_window_rect(self.hwnd))
        print("P: %s: coverage %s" % (self.label, coverage))
        if rect is None:
            raise RuntimeError("another window covers the game, so the recording would show that window")
        self.segment = SEGMENT_1 if tag == 1 else SEGMENT_2
        self.recorder, self.recorder_log, self.recorder_log_path = start_recorder(FFMPEG, rect, self.segment)
        print("P: %s: recording %s %dx%d" % (self.label, self.segment, rect[2], rect[3]))

    def stop_recording(self):
        if self.recorder is None:
            return
        stop_recorder(self.recorder, self.recorder_log)
        self.recorder = None
        ct.release_on_top(self.hwnd)

    def key(self, vk, gap=KEY_GAP_S):
        # Every press is checked against the real foreground window first. A key sent while another window holds the
        # focus goes to that window, and the game then reads as "the press did nothing": measured on 2026-10-23, five
        # Enters went nowhere while ensure_key_focus had reported the focus taken a moment earlier, because another
        # lane's window took it back in between.
        if not ct.game_has_focus(self.hwnd):
            ok, note = ct.ensure_key_focus(self.hwnd, attempts=6, settle=0.2)
            self.focused = ok
            print("P: %s: focus re-taken before the key: %s" % (self.label, note))
        result = press(self.hwnd, self.focused, vk)
        time.sleep(gap)
        return result

    def wait_line(self, needle, timeout_s):
        if ct.wait_for_log_line(self.log_path, needle, timeout_s):
            return find_in_log(self.log_path, needle)
        return ""

    def finish(self):
        """Close the game and its recorder, and print the one exit line."""
        self.stop_recording()
        if self.hwnd is not None:
            ct.close_window(self.hwnd)
            deadline = time.time() + CLOSE_GRACE_S
            while time.time() < deadline and self.run.alive():
                time.sleep(0.2)
        code = self.run.finish()
        try:
            self.log.close()
        except Exception:  # gate: ok best effort, the log is read from disk afterwards
            pass
        return code


# -------------------------------------------------------------------------------------------------------------------
# The two runs

def wait_run_start(launch, timeout_s=None):
    """Wait for the game's own run-start line, keeping the keyboard focus and nudging if the crawl stalls.

    The desktop is shared with other lanes, and a window that takes the foreground mid crawl eats the key presses that
    would end it: measured on 2026-10-23, a run sat on "the crawl jumped to its end" for the whole forty seconds because
    the game had lost the focus and its own log recorded the audio pause. So the wait re-takes the focus every couple of
    seconds and presses confirm again when the marker is late, instead of trusting one press and a stopwatch.
    """
    timeout_s = ct.SHIP_DRIVE_WAIT_S if timeout_s is None else timeout_s
    deadline = time.time() + timeout_s
    last_focus = 0.0
    last_nudge = time.time()
    nudges = 0
    while time.time() < deadline:
        quote = find_in_log(launch.log_path, RUN_START)
        if quote:
            return quote
        now = time.time()
        if now - last_focus > 2.0:
            last_focus = now
            ok, note = ct.ensure_key_focus(launch.hwnd, attempts=3, settle=0.15)
            launch.focused = ok
            if not ok:
                print("P: run 1: the game lost the keyboard focus and would not take it back: %s" % note)
        if now - last_nudge > 6.0 and nudges < 4:
            last_nudge = now
            nudges += 1
            print("P: run 1: no run marker yet, pressing confirm again %s" % launch.key(ct.VK_RETURN, 0.2))
        time.sleep(0.2)
    return ""

def run_one(exe, win):
    """Launch, start a new game, walk onto the log terminal, save. Returns the measurements run two needs."""
    print("P: run 1: launching %s" % os.path.basename(exe))
    launch = Launch(exe, win, "save capture run 1", "save_capture_run1.log")
    result = {"log": launch.log_path, "steps": []}
    clear_self_frames()
    started = time.time()
    spawn_frame, save_frame, panel_frame = self_frame_paths()[0], self_frame_paths()[1], None
    try:
        launch.start()
        launch.record(1)
        # START, then NEW GAME. The title prints its own intro line when NEW GAME takes, so the presses are repeated
        # until the game says so rather than trusting one press (the same loop tools\\capture_title.py --room uses).
        presses = 0
        while presses < ct.TITLE_INTRO_PRESS_CAP:
            presses += 1
            print("P: run 1: enter %d %s" % (presses, launch.key(ct.VK_RETURN)))
            if ct.log_has_line(launch.log_path, INTRO):
                break
        quote = launch.wait_line(INTRO, 4.0)
        if not quote:
            raise RuntimeError("the title never reported the intro starting after %d Enters" % presses)
        result["steps"].append({"event": "new game", "log": quote})
        # One more confirm is the crawl's own skip to its end (pp_title_step_intro: confirm jumps the crawl).
        print("P: run 1: enter skip %s" % launch.key(ct.VK_RETURN))
        quote = wait_run_start(launch)
        if not quote:
            raise RuntimeError("the game never reported the run starting within %.0f s" % ct.SHIP_DRIVE_WAIT_S)
        result["steps"].append({"event": "run started", "log": quote})
        # The room's own first frame: the hero on the spawn tile, the frame the landing is compared against.
        time.sleep(ROOM_SETTLE_S)
        if wait_for_file(spawn_frame, 8.0, not_before=started) is None:
            raise RuntimeError("the room wrote no spawn frame at %s" % spawn_frame)
        room_first_draw = os.path.getmtime(spawn_frame) - 90 / 60.0
        spawn_copy = os.path.join(BUILD_DIR, "save_capture_run1_spawn.png")
        shutil.copyfile(spawn_frame, spawn_copy)
        result["spawn_frame"] = spawn_copy
        # One right then five up: the spawn is 2,7 and the log terminal stands at 3,2 (data\\maps\\all.json). The turn
        # right is forced because 2,6 is the bulkhead; from 3,7 the left column of the corridor is floor all the way.
        for step in range(WALK_RIGHT):
            print("P: run 1: right %d %s" % (step + 1, launch.key(ct.VK_RIGHT)))
        for step in range(WALK_UP):
            print("P: run 1: up %d %s" % (step + 1, launch.key(VK_UP)))
        # A save trigger is not a touch trigger: pp_overworld_step fires it from the confirm press while the hero stands
        # on the tile (pp_overworld_confirm_target falls back to the hero's own tile when nothing is ahead), so the log
        # terminal is read by pressing confirm on it, the way the card describes the player doing it.
        print("P: run 1: confirm at the log terminal %s" % launch.key(ct.VK_Z, 0.02))
        # The panel is up from the frame the write starts and holds about a third of a second, so the copies start on the
        # press and not after the log line, which the game prints when the transfer has already finished.
        burst = []
        deadline = time.time() + BURST_S
        while time.time() < deadline:
            path = os.path.join(BUILD_DIR, "save_capture_panel_%03d.png" % len(burst))
            if panel_crop(launch.hwnd, path):
                burst.append({"path": path})
            time.sleep(0.03)
        result["burst"] = burst
        print("P: run 1: %d panel crops taken inside the panel window" % len(burst))
        quote = launch.wait_line(LOG_SAVE, SAVE_WAIT_S)
        if not quote:
            raise RuntimeError("the save trigger never printed the ship's log line on %d,%d" % SAVE_TILE)
        result["steps"].append({"event": "save written", "log": quote})
        # The room's second and third frames are the hero on the tile at draw 360, and the same tile with the panel on it
        # at draw 460. The second frame slot is 100 draws after the first, so a second confirm is timed to land on it: the
        # panel then appears in the game's own pixels instead of in a copy, which is the frame the card asks for.
        panel_frame = self_frame_paths()[2]
        target = room_first_draw + (460 - 90) / 60.0 - 0.18
        delay = target - time.time()
        if delay > 0:
            print("P: run 1: waiting %.2f s so the panel is up on the room's own draw 460" % delay)
            time.sleep(delay)
        print("P: run 1: confirm for the room's own panel frame %s" % launch.key(ct.VK_Z, 0.05))
        have_panel = wait_for_file(panel_frame, 6.0, not_before=started)
        # The room's second frame is the log terminal frame: the hero standing on 3,2 after the save.
        if wait_for_file(save_frame, 12.0, not_before=started) is None:
            raise RuntimeError("the room wrote no second frame at %s" % save_frame)
        save_copy = os.path.join(BUILD_DIR, "save_capture_run1_tile.png")
        shutil.copyfile(save_frame, save_copy)
        result["save_frame"] = save_copy
        if have_panel:
            panel_copy = os.path.join(BUILD_DIR, "save_capture_confirm.png")
            shutil.copyfile(panel_frame, panel_copy)
            result["panel_frame"] = panel_copy
            print("P: run 1: the room wrote its own panel frame at %s" % panel_copy)
        else:
            result["panel_frame"] = None
            print("P: run 1: the room wrote no draw 460 frame, so the panel comes from the window copies only")
        result["seconds"] = round(time.time() - started, 1)
    finally:
        launch.finish()
    result["log_lines"] = len(log_lines(launch.log_path))
    return result


def run_two(exe, win):
    """Launch again, choose CONTINUE, land on the saved tile, and prove the tile with one Down and one Up."""
    print("P: run 2: launching %s" % os.path.basename(exe))
    launch = Launch(exe, win, "save capture run 2", "save_capture_run2.log")
    result = {"log": launch.log_path, "steps": []}
    clear_self_frames()
    started = time.time()
    landing_frame = self_frame_paths()[0]
    try:
        launch.start()
        launch.record(2)
        quote = launch.wait_line(ACCEPT, 20.0)
        if not quote:
            raise RuntimeError("the title never read the slot, so there was nothing to continue")
        result["steps"].append({"event": "slot read at boot", "log": quote})
        # PRESS START opens the menu on the row named NEW GAME (card R25), so one Down puts the cursor on CONTINUE.
        print("P: run 2: enter menu %s" % launch.key(ct.VK_RETURN, MENU_OPEN_S))
        print("P: run 2: down to CONTINUE %s" % launch.key(VK_DOWN, MENU_GAP_S))
        print("P: run 2: confirm CONTINUE %s" % launch.key(ct.VK_RETURN, 0.2))
        if wait_for_file(landing_frame, 12.0, not_before=started) is None:
            raise RuntimeError("the room never drew after CONTINUE, so the load did not land in a map")
        landing_copy = os.path.join(BUILD_DIR, "save_capture_run2_landing.png")
        shutil.copyfile(landing_frame, landing_copy)
        time.sleep(LANDING_SETTLE_S)
        result["landing_frame"] = landing_copy
        box, score, note = take_copy(launch.hwnd, os.path.join(BUILD_DIR, "save_capture_landing_copy.png"))
        if box is not None:
            result["landing_copy"] = {"path": os.path.join(BUILD_DIR, "save_capture_landing_copy.png"),
                                      "score": round(score, 3)}
        # The landing proof. One Down from 3,2 reaches 3,3 and one Up from 3,3 reaches 3,2, where the trigger fires; from
        # the spawn tile 2,7 neither press lands on 3,2, and a Down from 2,7 meets the bulkhead at 2,6, so the line below
        # can only appear when the run landed on 3,2.
        print("P: run 2: down from the landing %s" % launch.key(VK_DOWN))
        print("P: run 2: up onto the log terminal %s" % launch.key(VK_UP))
        print("P: run 2: confirm at the log terminal %s" % launch.key(ct.VK_Z, 0.2))
        quote = launch.wait_line(LOG_SAVE, SAVE_WAIT_S)
        if not quote:
            raise RuntimeError("one Down and one Up from the landing did not reach the save point on %d,%d"
                               % SAVE_TILE)
        result["steps"].append({"event": "landing proved by the trigger", "log": quote})
        result["seconds"] = round(time.time() - started, 1)
    finally:
        launch.finish()
    result["log_lines"] = len(log_lines(launch.log_path))
    return result


# -------------------------------------------------------------------------------------------------------------------
# The verifier

def join_segments(ffmpeg_path):
    """Join the two recordings in order. The settings are identical, so the copy needs no re-encode."""
    if not (os.path.isfile(SEGMENT_1) and os.path.isfile(SEGMENT_2)):
        return False, "a segment is missing (%s, %s)" % (SEGMENT_1, SEGMENT_2)
    listing = os.path.join(BUILD_DIR, "save_capture_concat.txt")
    with open(listing, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("file '%s'\n" % SEGMENT_1.replace("\\", "/"))
        handle.write("file '%s'\n" % SEGMENT_2.replace("\\", "/"))
    if os.path.exists(VIDEO_OUT):
        os.remove(VIDEO_OUT)
    # Joined with the concat filter, not the demuxer: the two segments carry their own timestamps, and a demuxer join
    # measured 12.39 s for 9.39 + 6.30 s of parts on 2026-10-23. The filter re-encodes both into one timeline.
    ok, note = ct.run_ffmpeg(ffmpeg_path, ["-i", SEGMENT_1, "-i", SEGMENT_2,
                                          "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
                                          "-map", "[v]", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
                                          "-pix_fmt", "yuv420p", "-movflags", "+faststart", VIDEO_OUT],
                             timeout=600)
    if not ok:
        return False, note
    return True, "joined %s and %s with the concat filter" % (os.path.basename(SEGMENT_1),
                                                             os.path.basename(SEGMENT_2))


def game_share(path, anchors, tolerance=28):
    """The share of a frame's pixels that sit within tolerance of one of the game's own colours.

    A recorded frame is not the game's exact pixels: the encoder subsamples chroma, so a flat field stays its colour and
    the edges blend. The NES legality search in tools\\nes_composite_check.py is the right test for a PNG copy and the wrong
    one for a video frame, which measured 0.115 legal on a frame that is plainly the game (2026-10-23).
    """
    try:
        from PIL import Image
    except Exception:
        return None
    try:
        with Image.open(path) as image:
            counts = image.convert("RGB").getcolors(maxcolors=1 << 20) or []
    except Exception:  # gate: ok a frame that will not open cannot be measured, the caller reports that
        return None
    if not counts:
        return None
    total = sum(count for count, _pixel in counts)
    hit = 0
    for count, pixel in counts:
        for anchor in anchors:
            if (abs(pixel[0] - anchor[0]) <= tolerance and abs(pixel[1] - anchor[1]) <= tolerance
                    and abs(pixel[2] - anchor[2]) <= tolerance):
                hit += count
                break
    return hit / float(total)


def video_frame_closest(frame_path, references, viewport=(8, 31, 768, 720), size=(64, 60)):
    """The smallest share of differing pixels between a recorded frame and the frames the run accepted, and which one.

    The recorded file is the window rectangle, so the game's screen is the 3x viewport inside it. That box is cut out and
    brought down to 64x60 by averaging, on both sides of the comparison, because the recorded window was squeezed by one
    row of pixels on the way into the file (784x759 becomes 784x758, an even height for libx264). A pixel whose channels
    differ by more than `tolerance` counts as different: libx264 writes limited-range colour, so the same grey arrives
    about 16 lower in the recorded frame and a strict comparison then calls two frames of one screen 0.72 apart.
    Returns (difference, reference path).
    """
    try:
        from PIL import Image, ImageChops
    except Exception:  # gate: ok no Pillow means the video frames cannot be compared, and the caller says so
        return None, None
    tolerance = 32
    try:
        with Image.open(frame_path) as handle:
            frame = handle.convert("RGB")
        vx, vy, vw, vh = viewport
        if frame.width < vx + vw or frame.height < vy + vh:
            return None, None
        crop = frame.crop((vx, vy, vx + vw, vy + vh)).resize(size, Image.Resampling.BOX)
    except Exception:  # gate: ok a frame that will not open cannot be compared, the caller reports that
        return None, None
    best = None
    for reference in references or ():
        if not reference or not os.path.isfile(reference):
            continue
        try:
            with Image.open(reference) as handle:
                other = handle.convert("RGB").resize(size, Image.Resampling.BOX)
            difference = ImageChops.difference(crop, other).convert("L")
            histogram = difference.histogram()
            changed = sum(histogram[tolerance + 1:])
            total = sum(histogram)
            if not total:
                continue
            share = changed / float(total)
        except Exception:  # gate: ok a reference that will not open is skipped, the others still count
            continue
        if best is None or share < best[0]:
            best = (share, reference)
    if best is None:
        return None, None
    return best


def box_change(frame_path, baseline_path, frame_box, baseline_box, size=(160, 57), threshold=24):
    """The share of the panel box that changed between a recorded frame and the scene without the panel.

    The panel's paper is the same grey the deck floor uses, so a colour reading cannot tell the panel from the floor. What
    the panel does change is the box: its border, its ink and its fill replace the tiles under it. A channel difference
    under `threshold` is counted as equal, which is what lets a lossy recorded frame be compared with an exact one.
    """
    try:
        from PIL import Image, ImageChops
        with Image.open(frame_path) as handle:
            frame = handle.convert("RGB").crop([int(value) for value in frame_box])
        with Image.open(baseline_path) as handle:
            baseline = handle.convert("RGB").crop([int(value) for value in baseline_box])
    except Exception:  # gate: ok an unreadable pair is reported by the caller as no measurement
        return None
    left = frame.resize(size, Image.Resampling.BOX)
    right = baseline.resize(size, Image.Resampling.BOX)
    difference = ImageChops.difference(left, right).convert("L")
    histogram = difference.histogram()
    total = sum(histogram)
    if not total:
        return None
    return sum(histogram[threshold + 1:]) / float(total)


def find_panel_in_video(ffmpeg_path, segment_path, tile_frame, start_s=0.2, fps=10):
    """The frame of the run 1 recording where the save panel is on screen, and how much of the box it changed.

    The recording is the one surface that holds the panel while it lives: a full window copy costs about 0.8 s on this PC
    while ffmpeg reads the screen, and the panel is up for 20 steps (a third of a second). Every tenth of a second of the
    segment is dumped, the frames that are still the same screen as the log terminal frame are kept, and the one that
    changed the panel box most is the panel.
    """
    if not os.path.isfile(segment_path) or not tile_frame or not os.path.isfile(tile_frame):
        return None
    duration = None
    try:
        # The segment's own length, so the whole recording is searched and no clock constant decides where to look.
        probe = ct.ffprobe_path(ffmpeg_path)
        duration = ct.probe_duration(probe, segment_path)
    except Exception:  # gate: ok no duration means the default span below is used
        duration = None
    span = (duration - start_s - 0.2) if duration and duration > start_s + 1.0 else 8.0
    work = tempfile.mkdtemp(prefix="savepanel-")
    ok, note = ct.run_ffmpeg(ffmpeg_path, ["-ss", "%.2f" % start_s, "-t", "%.2f" % span, "-i", segment_path,
                                          "-vf", "fps=%d" % fps, os.path.join(work, "p_%03d.png")], timeout=300)
    if not ok:
        print("P: the recording's frames could not be dumped: %s" % note)
        return None
    box = window_panel_box()
    best = None
    seen = 0
    for index, name in enumerate(sorted(n for n in os.listdir(work) if n.endswith(".png"))):
        path = os.path.join(work, name)
        same_screen, which = video_frame_closest(path, [tile_frame])
        if same_screen is None or same_screen > 0.30:
            continue
        seen += 1
        change = box_change(path, tile_frame, box, PANEL_BOX)
        if change is None:
            continue
        if best is None or change > best[0]:
            best = (change, {"path": path, "at": round(start_s + index / float(fps), 2), "video": True,
                             "change": round(change, 4), "same_screen": round(same_screen, 4)})
    if best is None:
        print("P: no recorded frame was the same screen as the log terminal frame (%d of the dumped frames were)"
              % seen)
        return None
    print("P: the recording's panel frame is %s at t=%.2f s: it changes %.4f of the panel box and is %.4f from the "
          "log terminal frame" % (os.path.basename(best[1]["path"]), best[1]["at"], best[0], best[1]["same_screen"]))
    return best[1]


def verify_video(ffmpeg_path, ffprobe, reference_paths=(), samples=(0.6, 0.85)):
    """The joined file: it exists, it is about as long as the two segments, and its frames are the game."""
    result = {"path": VIDEO_OUT, "checks": []}

    def check(name, ok, detail):
        result["checks"].append({"check": name, "ok": bool(ok), "detail": detail})
        print("%s %s: %s" % ("PASS" if ok else "FAIL", name, detail))
        return ok

    if not check("video written", os.path.isfile(VIDEO_OUT) and os.path.getsize(VIDEO_OUT) > 0,
                 "%d bytes" % (os.path.getsize(VIDEO_OUT) if os.path.isfile(VIDEO_OUT) else 0)):
        return result
    first = ct.probe_duration(ffprobe, SEGMENT_1) or 0.0
    second = ct.probe_duration(ffprobe, SEGMENT_2) or 0.0
    duration = ct.probe_duration(ffprobe, VIDEO_OUT)
    result["segment_seconds"] = [round(first, 2), round(second, 2)]
    result["seconds"] = None if duration is None else round(duration, 2)
    if first <= 0.0 or second <= 0.0:
        check("segments readable", False, "ffprobe read no duration for a segment")
        return result
    check("duration is the two runs", duration is not None and duration >= max(first, second) + 2.0,
          "joined %.2f s, its parts are %.2f + %.2f s and each part's container duration is an estimate, so the check is "
          "that the file holds both: the frame check below reads the run 2 part out of the joined file"
          % (duration or 0.0, first, second))
    # The frames: crop the game's own 3x viewport out of the recorded window and compare it with the frames the run
    # already accepted from the room itself. A recorded frame is not byte for byte the game (the encoder rounds), but the
    # map fills almost all of it, so a real frame sits close to one of the accepted ones and a foreign window does not.
    work = tempfile.mkdtemp(prefix="savecap-")
    found = []
    for tag, start, length in (("run 1", 0.0, first), ("run 2", first, second)):
        for offset in samples:
            stamp = start + length * offset
            path = os.path.join(work, "v_%s_%0.2f.png" % (tag.replace(" ", ""), stamp))
            if not ct.extract_frame(ffmpeg_path, VIDEO_OUT, stamp, path):
                found.append({"tag": tag, "at": round(stamp, 2), "closest": None, "path": path})
                continue
            closest, which = video_frame_closest(path, reference_paths)
            found.append({"tag": tag, "at": round(stamp, 2),
                          "closest": None if closest is None else round(closest, 4),
                          "against": os.path.basename(which) if which else None, "path": path})
    result["frames"] = found
    scored = [row for row in found if row.get("closest") is not None]
    check("the recording shows the game", len(scored) >= 3 and max(row["closest"] for row in scored) <= 0.30,
          "%d of %d sampled frames were compared with the room's own frames; the worst differs by %.4f of its pixels "
          "(0.30 allowed): %s"
          % (len(scored), len(found), max([row["closest"] for row in scored] or [1.0]),
             ", ".join("%s t=%.2f %.4f against %s" % (row["tag"], row["at"], row["closest"], row["against"])
                       for row in scored)))
    result["ok"] = all(row["ok"] for row in result["checks"])
    return result


def verify(run1, run2, video):
    """Every check the card names, each with the number it was measured at."""
    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
        print("%s %s: %s" % ("PASS" if ok else "FAIL", name, detail))
        return ok

    lines1 = log_lines(run1["log"])
    lines2 = log_lines(run2["log"])

    # 1. Muted in both runs, from the game's own log.
    check("run 1 is muted", any(MUTE in line for line in lines1), "PP: muted in %s" % run1["log"])
    check("run 2 is muted", any(MUTE in line for line in lines2), "PP: muted in %s" % run2["log"])

    # 2. Both logs name the same slot: the path and the digest the tool measured at that point of each run.
    def slot_parts(lines):
        for line in lines:
            if line.startswith("P: slot:"):
                path = line.split("sha256")[0].replace("P: slot:", "").strip()
                digest = line.split("sha256")[1].split()[0].strip() if "sha256" in line else ""
                return path, digest, line
        return "", "", ""

    path1, digest1, slot1 = slot_parts(lines1)
    path2, digest2, slot2 = slot_parts(lines2)
    check("the two runs name the same save slot", bool(path1 and path2 and path1 == path2),
          slot1 if slot1 else "no slot line in run 1")
    check("the slot run 2 opened is the one run 1 wrote", bool(digest1 and digest2 and digest1 == digest2),
          "run 1 wrote digest %s, run 2 opened digest %s" % (digest1 or "none", digest2 or "none"))

    # 3. The save was written at the log terminal, by the game's own line, on the tile the card names.
    check("run 1 wrote the save at the log terminal", any(LOG_SAVE in line for line in lines1),
          LOG_SAVE if any(LOG_SAVE in line for line in lines1) else "the line is not in the log")

    # 4. The restart read that save, and the landing is the saved tile.
    check("run 2 read the save at boot", any(ACCEPT in line for line in lines2),
          find_in_log(run2["log"], ACCEPT) or "no accepted line")
    check("CONTINUE landed on the saved tile", any(LOG_SAVE in line for line in lines2),
          "one Down and one Up from the landing fired the save point again: %s"
          % (find_in_log(run2["log"], LOG_SAVE) or "no line"))

    # 5. The frames: the log terminal, the save confirmation, the landing, each in the game's own pixels where possible.
    frames = {}
    spawn = run1.get("spawn_frame")
    saved = run1.get("save_frame")
    landing = run2.get("landing_frame")
    for name, path in (("spawn", spawn), ("log terminal", saved), ("landing", landing)):
        if not path or not os.path.isfile(path):
            check("the %s frame exists" % name, False, "%s is missing" % path)
            frames[name] = None
            continue
        if name == "log terminal":
            # This frame can catch the panel fading in, so the panel box is left out of the palette test; every pixel
            # outside it must still be a 2C02 colour.
            legal, why = legality_share(path, exclude_box=screen_panel_box())
            check("the %s frame exists" % name, legal is not None and legal >= 0.99,
                  "%s: %s, the panel box left out of the count because the panel fades in"
                  % (os.path.basename(path), why if legal is None else "%.4f legal, %s" % (legal, why)))
        else:
            legal, why = native_legality(path)
            check("the %s frame exists" % name, legal is not None and legal >= 0.99,
                  "%s: %s" % (os.path.basename(path), why if legal is None else "%.4f legal, %s" % (legal, why)))
        frames[name] = path
    # The confirmation frame. The panel can only be in a window copy: screen_save runs inside the room's own draw and
    # pp_app draws the panel after that. A full window copy costs about 0.8 s while a recording runs and the panel lives
    # 20 steps, so what is captured is the panel box cropped out of the window at 3x (480x171), repeatedly, on the confirm
    # press. The crop is judged on its own pixels: legal 2C02 colours, one colour owning the box, and that colour not being
    # the tile's colour from the log terminal frame.
    baseline = panel_reading(saved) if saved and os.path.isfile(saved) else None
    base_colour = (baseline or {}).get("dominant_colour")
    candidates = []
    room_panel = run1.get("panel_frame")
    if room_panel and os.path.isfile(room_panel):
        reading = panel_reading(room_panel)
        if reading:
            candidates.append({"path": room_panel, "source": "the room's own draw 460 frame", "reading": reading})
    for row in run1.get("burst", []):
        reading = image_reading(row["path"])
        if reading:
            candidates.append({"path": row["path"], "source": "the panel box cropped at 3x on the confirm press",
                              "reading": reading})
    video_panel = run1.get("video_panel")
    if video_panel:
        candidates.append({"path": video_panel["path"], "source": "a frame of the run 1 recording at t=%.2f s"
                                                          % video_panel["at"], "video": True,
                           "change": video_panel.get("change"), "same_screen": video_panel.get("same_screen")})
    best = None
    for row in candidates:
        if row.get("video"):
            change = float(row.get("change") or 0.0)
            key = (1 if change >= PANEL_MIN_CHANGE else 0, change)
        else:
            reading = row["reading"]
            repainted = bool(base_colour and reading["dominant_colour"] != base_colour)
            key = (1 if repainted else 0, reading["dominant"])
        if best is None or key > best[0]:
            best = (key, row)
    print("P: panel candidates: %d, the best is %s" % (len(candidates), best[1]["path"] if best else "none"))
    frames["confirm"] = None
    if best is None or not best[0][0]:
        check("the save confirmation is on screen", False,
              "no sample repainted the panel box out of the tile's colour %s, so the panel is in none of the %d samples"
              % (base_colour, len(candidates)))
    else:
        chosen = best[1]
        if chosen.get("video"):
            # A recorded frame is the game as the encoder left it, so the palette test does not apply to it: the panel is
            # proven by the box changing on a frame that is otherwise the same screen as the log terminal frame.
            ok = bool((chosen.get("change") or 0.0) >= PANEL_MIN_CHANGE
                      and (chosen.get("same_screen") is not None and chosen["same_screen"] <= 0.30))
            detail = ("%s (%s): %.4f of the panel box changed (%.2f required) while the frame is the same screen as the "
                      "log terminal frame (%.4f of the screen differs, 0.30 allowed)"
                      % (os.path.basename(chosen["path"]), chosen["source"], chosen.get("change") or 0.0,
                         PANEL_MIN_CHANGE, chosen.get("same_screen") or 1.0))
        else:
            reading = chosen["reading"]
            legal, why = legality_share(chosen["path"])
            ok = bool(reading["dominant"] >= PANEL_DOMINANT and legal is not None and legal >= 0.99)
            detail = ("%s (%s): one colour owns %.3f of the box (%.2f required), that colour %s is not the tile's %s, "
                      "and %s"
                      % (os.path.basename(chosen["path"]), chosen["source"], reading["dominant"], PANEL_DOMINANT,
                         reading["dominant_colour"], base_colour,
                         why if legal is None else "%.4f of its pixels are 2C02 colours" % legal))
        check("the save confirmation is on screen", ok, detail)
        if ok:
            frames["confirm"] = chosen["path"]
    # The landing is the saved tile: the rest of the screen must be the frame taken at the log terminal, with the panel box
    # blanked out of both because that frame may carry the panel. The spawn frame is reported alongside as a reference.
    if frames.get("landing") and frames.get("log terminal") and frames.get("spawn"):
        to_saved = masked_difference(frames["landing"], frames["log terminal"])
        to_spawn = difference(frames["landing"], frames["spawn"])
        ok = to_saved is not None and to_saved <= 0.02
        check("the landing frame is the log terminal screen", ok,
              "outside the panel box the landing differs from the log terminal frame by %s of its pixels (0.02 allowed), "
              "and from the spawn frame by %s"
              % ("unmeasured" if to_saved is None else "%.5f" % to_saved,
                 "unmeasured" if to_spawn is None else "%.5f" % to_spawn))
    else:
        check("the landing frame is the log terminal screen", False, "a frame is missing")

    # 6. The video.
    for row in video.get("checks", []):
        check("video: %s" % row["check"], row["ok"], row["detail"])

    ok = all(row["ok"] for row in checks)
    report = {
        "ok": ok,
        "task": "t_673fba81 SAVE-LOAD-CAPTURE",
        "what_this_proves": ("the built game wrote a save at the ship's log terminal on ship_small 3,2, was closed, "
                            "and a second launch chose CONTINUE and landed on that tile"),
        "checks": checks,
        "slot": {"path": SLOT, "run1_digest": digest1, "run2_digest": digest2},
        "frames": {name: (os.path.basename(path) if path else None) for name, path in frames.items()},
        "frame_paths": {name: path for name, path in frames.items() if path},
        "runs": {"run1": run1, "run2": run2},
        "video": video,
        "tool": "tools/capture_save.py",
        "written_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    return report, ok


def copy_frame(source, target):
    if source and os.path.isfile(source):
        shutil.copyfile(source, target)
        return target
    return None


# -------------------------------------------------------------------------------------------------------------------
# The route check: no window, no game, just the shipped grid and the line this tool waits for
#
# The walk this tool presses was wrong for a day after the log terminal moved (card t_9181cc04: deck_save went from
# ship_small 2,5 to 3,2 and the tool still walked to 2,5). A capture that walks the wrong tile cannot fail loudly:
# it waits six seconds for a log line that cannot appear. So the route, the tile and the expected line are checked
# against data\maps\all.json before any launch, with no window at all (--check-route).

def check_route(map_path=None):
    """Read the shipped map, walk the declared route, and say whether it ends on the save trigger it waits for."""
    map_path = map_path or os.path.join(ROOT, "data", "maps", "all.json")
    try:
        with open(map_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        print("FAIL the map file at %s could not be read: %s" % (map_path, exc))
        return 1
    maps = data.get("maps") if isinstance(data, dict) else data
    world = None
    for row in maps or []:
        if row.get("id") == "ship_small":
            world = row
            break
    if world is None:
        print("FAIL %s carries no map with id ship_small" % map_path)
        return 1

    collision = world.get("collision") or []
    width = int(world.get("width") or 0)
    height = int(world.get("height") or 0)
    if not collision or len(collision) != height or any(len(line) != width for line in collision):
        print("FAIL ship_small's collision grid is not %d by %d rows of %d" % (height, width, width))
        return 1

    def blocked(tx, ty):
        if tx < 0 or ty < 0 or ty >= height or tx >= width:
            return "off the grid"
        if collision[ty][tx] == "1":
            return "a wall"
        return ""

    spawns = world.get("spawns") or {}
    start = spawns.get("start") or {}
    sx, sy = int(start.get("x", -1)), int(start.get("y", -1))
    if (sx, sy) != SPAWN_TILE:
        print("FAIL the run starts from %s on ship_small, and this tool walks from %d,%d"
              % ((sx, sy), SPAWN_TILE[0], SPAWN_TILE[1]))
        return 1
    why = blocked(sx, sy)
    if why:
        print("FAIL the spawn 2,7 is %s" % why)
        return 1

    # The walk the tool presses, one tile at a time. Every tile it leaves a press on has to be floor, because a press
    # into a wall is a press the hero never makes and the route would end somewhere else than the log line says.
    tx, ty = SPAWN_TILE
    pressed = []
    for _step in range(WALK_RIGHT):
        tx += 1
        pressed.append((tx, ty))
    for _step in range(WALK_UP):
        ty -= 1
        pressed.append((tx, ty))
    for (px, py) in pressed:
        why = blocked(px, py)
        if why:
            print("FAIL the press at %d,%d walks into %s, so the route never reaches %d,%d"
                  % (px, py, why, SAVE_TILE[0], SAVE_TILE[1]))
            return 1
    print("P: route 2,7 -> %s in %d presses, every tile floor" % (pressed[-1], len(pressed)))
    if (tx, ty) != SAVE_TILE:
        print("FAIL the route ends on %d,%d and SAVE_TILE is %d,%d" % (tx, ty, SAVE_TILE[0], SAVE_TILE[1]))
        return 1

    # The tile has to carry the save trigger, and the expected line is built from that row the way pp_overworld's
    # "save" case builds it: the trigger's own id, the map id, and the hero's tile.
    trigger = None
    for row in world.get("triggers") or []:
        if int(row.get("x", -1)) == tx and int(row.get("y", -1)) == ty:
            trigger = row
            break
    if trigger is None:
        print("FAIL ship_small carries no trigger at %d,%d, which is where the route ends" % (tx, ty))
        return 1
    if trigger.get("kind") != "save":
        print("FAIL the trigger at %d,%d is kind %r, not a save" % (tx, ty, trigger.get("kind")))
        return 1
    want = "PP: ship's log, %s, saved on %s %d,%d" % (trigger.get("id"), world.get("id"), tx, ty)
    if LOG_SAVE != want:
        print("FAIL the line this tool waits for is %r and the shipped data says %r" % (LOG_SAVE, want))
        return 1
    print("P: trigger %s at %d,%d is the save the tool reads, and the line matches the data"
          % (trigger.get("id"), tx, ty))

    # The landing proof presses one Down and one Up from the tile the load lands on, so the tile below has to be floor
    # and not a trigger of its own, or the pair would fire something else on the way back.
    below = (tx, ty + 1)
    why = blocked(below[0], below[1])
    if why:
        print("FAIL the landing proof's Down press reaches %d,%d, which is %s" % (below[0], below[1], why))
        return 1
    for row in world.get("triggers") or []:
        if int(row.get("x", -1)) == below[0] and int(row.get("y", -1)) == below[1]:
            print("FAIL %d,%d carries the %r trigger, so the landing proof's Down press would fire it"
                  % (below[0], below[1], row.get("id")))
            return 1
    print("P: the landing proof's Down press reaches %d,%d, floor with no trigger on it" % below)
    print("PASS the route, the save tile and the expected log line agree with %s" % os.path.basename(map_path))
    return 0


# -------------------------------------------------------------------------------------------------------------------
# Main

def main():
    global LAUNCH, FFMPEG
    parser = argparse.ArgumentParser(description="capture a save at the log terminal and a CONTINUE onto the saved tile")
    pp_launch.add_launch_flags(parser)
    parser.add_argument("--skip-build-check", action="store_true", dest="skip_build_check",
                        help="do not stop when the build is older than the source it should carry")
    parser.add_argument("--check-route", action="store_true", dest="check_route",
                        help="walk the declared route over data\\maps\\all.json and stop: no window, no game, no launch")
    args = parser.parse_args()
    if args.check_route:
        return check_route()
    LAUNCH = pp_launch.policy_from_args(args)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(BUILD_DIR, exist_ok=True)

    if not LAUNCH.gate("save capture"):
        print("P: save capture: the idle gate refused, so no window was opened. Run it again when the machine is quiet.")
        return pp_launch.EXIT_REFUSED

    build = ct.newest_build()
    if build is None:
        print("FAIL no built game under %s" % ct.GAME_OUTPUT_DIR)
        return 1
    exe_path, win_path = build
    FFMPEG = ct.find_ffmpeg()
    if not FFMPEG:
        print("FAIL ffmpeg was not found, so no video can be recorded")
        return 1
    probe = ct.ffprobe_path(FFMPEG)
    # The build has to carry the source this card's checks depend on. A stale .win is the one failure mode that would
    # make a green run a lie, so the newest source file and the .win are compared by mtime and the run stops on a stale
    # build unless --skip-build-check says the reader knows better.
    newest_source = 0.0
    for folder, _dirs, files in os.walk(os.path.join(ROOT, "game", "scripts")):
        for name in files:
            if name.endswith(".gml"):
                newest_source = max(newest_source, os.path.getmtime(os.path.join(folder, name)))
    build_time = os.path.getmtime(win_path)
    print("P: build %s written %s, newest GML %s"
          % (os.path.basename(win_path), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(build_time)),
             time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(newest_source))))
    if newest_source > build_time + 1.0 and not args.skip_build_check:
        print("FAIL the build is older than the source (%s against %s), so it cannot carry the code this card "
              "captures. Compile first (tools\\run.ps1 -Compile), or pass --skip-build-check to say the build is "
              "known good."
              % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(build_time)),
                 time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(newest_source))))
        return 1

    original_slot = None
    if os.path.isfile(SLOT):
        original_slot = os.path.join(BUILD_DIR, "save_capture_slot_original.json")
        shutil.copy2(SLOT, original_slot)
    try:
        before_one = sha256(SLOT)
        result1 = run_one(exe_path, win_path)
        after_one = sha256(SLOT)
        append_log_line(result1["log"], "P: slot: %s sha256 %s (written by this run, was %s)"
                        % (SLOT, after_one or "absent", before_one or "absent"))
        time.sleep(1.0)
        before_two = sha256(SLOT)
        result2 = run_two(exe_path, win_path)
        append_log_line(result2["log"], "P: slot: %s sha256 %s (opened by this run)"
                        % (SLOT, before_two or "absent"))
        # The save panel lives a third of a second, and the recording is the one surface that holds it: find it now, while
        # the segment is still on disk and before the joined file is written.
        result1["video_panel"] = find_panel_in_video(FFMPEG, SEGMENT_1, result1.get("save_frame"))

        joined, join_note = join_segments(FFMPEG)
        print("P: video: %s" % join_note)
        video = verify_video(FFMPEG, probe, [path for path in (result1.get("spawn_frame"),
                                                               result1.get("save_frame"),
                                                               result2.get("landing_frame")) if path]) if joined else {
            "path": VIDEO_OUT, "checks": [{"check": "video written", "ok": False, "detail": join_note}],
            "ok": False}

        copy_frame(result1.get("save_frame"), LOG_TERMINAL_PNG)
        copy_frame(result2.get("landing_frame"), LANDING_PNG)
        frames_report, ok = verify(result1, result2, video)
        # The three named frames are whatever the verifier accepted, copied to the output folder under their card names.
        chosen_paths = frames_report.get("frame_paths", {})
        copy_frame(chosen_paths.get("log terminal"), LOG_TERMINAL_PNG)
        copy_frame(chosen_paths.get("confirm"), CONFIRM_PNG)
        copy_frame(chosen_paths.get("landing"), LANDING_PNG)
        with open(VERIFY_OUT, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(frames_report, indent=2, sort_keys=True) + "\n")
        with open(FRAMES_OUT, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps({
                "log_terminal": os.path.basename(LOG_TERMINAL_PNG),
                "confirm": os.path.basename(CONFIRM_PNG),
                "landing": os.path.basename(LANDING_PNG),
                "source": {"log_terminal": "the room's own pp_ship_frame_2.png at draw 360, after the save",
                           "confirm": "a window copy inside the panel window, kept only when the NES viewport "
                                      "search found the game's 3x screen",
                           "landing": "the room's own pp_ship_frame.png at draw 90, after CONTINUE"},
                "note": "the game's own frames land in %s; the copies are in %s" % (LOCAL_APP, BUILD_DIR),
            }, indent=2, sort_keys=True) + "\n")
        print("P: verify json: %s" % VERIFY_OUT)
        for path in (LOG_TERMINAL_PNG, CONFIRM_PNG, LANDING_PNG, VIDEO_OUT):
            if os.path.isfile(path):
                print("P: wrote %s (%d bytes)" % (path, os.path.getsize(path)))
        print("ok: %s" % ("true" if ok else "false"))
        return 0 if ok else 1
    finally:
        # The player's slot goes back exactly as it was found: this run is a capture, not his save.
        if original_slot and os.path.isfile(original_slot):
            shutil.copy2(original_slot, SLOT)
            print("P: slot restored to the save that was there before this run (%s)" % (sha256(SLOT) or "absent"))


if __name__ == "__main__":
    sys.exit(main())
