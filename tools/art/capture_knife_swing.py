#!/usr/bin/env python3
"""capture_knife_swing.py: a real frame of the running game showing Dad's Good Knife, in the tutorial fight.

Why this file exists (card PP-KNIFE, t_503707c8). The card's check is "a battle capture shows the knife frames", and
a composed picture is not a capture. This tool drives the built game and takes the frames a player would see:

  1. the MENU frame, where the band's bottom line reads `HELD: Dad's Good Knife`, which is the menu text the card
     asks for and the only place a player reads the name before the swing;
  2. three SWING frames, taken in a burst across the 18 steps (0.3 s at 60 fps) the slash is on screen after a
     FIGHT lands, because one frame at one instant would be a guess at which of the three slash frames is up.

It walks the route with a player's own keys, on tools/capture_first_fight.py's measured schedule rather than a
schedule retyped here: Enter three times for the title menu, NEW GAME and the crawl, a hold of cancel to skip the
drive (a 178 s cutscene the game gives a player a skip for), the arrival walk to the gate, the gate's and the
boarding scene's page turns, and one confirm on the deck that starts encounter tutorial_sailors. No environment
flag is set, so the run is one a player could have played. A posted key is a dud in GameMaker (capture_title.py
measured that on 2026-10-21), so every press goes through capture_title.send_vk_focused with the focus taken first.

The player's keys are the correction of this tool's first approach, and the reason is measured. A PP_SLICE walk of
the same route printed step 3 of 9, the drive, and sat on it for 240 s with no frame taken (2026-10-27), because a
slice walk never presses the drive's own skip and the drive is longer than any wait this tool would hold. The route
a player walks and the route data/slice.json names are the same route; only the presses differ.

The frames are MEASURED, not hoped for. Each swing frame is counted for pixels of the sheet's own two non-black
entries, $21 #3cbcfc and $31 #a4e4fc, inside the enemy slot data/ui_layouts.json declares; the deck strip's own
palettes carry neither, and the party column sits at x 224, outside that slot, so a count above zero in there is
the swing and nothing else. The best frame is written as output/battle_knife_swing.png and every count is printed.

Rules it obeys (tools/pp_launch.py, ruling D9): muted, no window while the machine is not quiet, off the primary
screen, one launch, and the window is closed on request.

Usage:
    python tools\\art\\capture_knife_swing.py
    python tools\\art\\capture_knife_swing.py --idle-wait 220 --out-dir output
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

from PIL import Image

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(TOOLS)
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import capture_first_fight as first_fight  # noqa: E402  the player's route to the first fight, read not copied
import capture_title as cap  # noqa: E402  the window, screen copy, focus and viewport primitives
import play_demo  # noqa: E402  the pre-roll viewport search the recorder uses
import pp_launch  # noqa: E402  the launch policy every automatic launch goes through

SCALE = 3
WINDOW_TIMEOUT_S = 40.0
SETTLE_S = 2.5        # the same settle capture_first_fight.py waits, so the route's own seconds line up
MENU_SETTLE_S = 4.0
DRIVE_SKIP_S = first_fight.DRIVE_SKIP_S  # the last press that is on the measured clock, the drive's own skip
ROUTE_TIMEOUT_S = 120.0   # after the drive, the walk to the fight is driven by the route's own step
ROUTE_START_GAP_S = 1.2   # a title, crawl or drive press: one keypress a phase
ROUTE_WALK_GAP_S = 0.45   # one map tile a press
ROUTE_PAGE_GAP_S = 0.7    # one dialogue page a press
BURST_S = (0.06, 0.16, 0.26)  # inside the 18 steps the slash is drawn
LAYOUT = os.path.join(ROOT, "data", "ui_layouts.json")
VK_Z = 0x5A


def build():
    found = cap.newest_build()
    if found is None:
        raise SystemExit("no built game under %s: build it first" % cap.GAME_OUTPUT_DIR)
    return found


def enemy_slot():
    """The first enemy slot of the battle screen, as the director resolves it: the layout's tile rect times 8."""
    with open(LAYOUT, "r", encoding="utf-8") as handle:
        layout = json.load(handle)
    for screen in layout["screens"]:
        if screen["name"] == "battle":
            row = screen["enemies"][0]
            w, h = (int(part) for part in row["pixels"].split("x"))
            return {"x": row["x"] * 8, "y": row["y"] * 8, "w": w, "h": h}
    raise SystemExit("data/ui_layouts.json has no battle screen")


def swing_pixels(image, slot, colours):
    """How many pixels of the frame inside the enemy slot wear one of the knife's non-black entries."""
    count = 0
    pixels = image.load()
    for y in range(slot["y"], min(slot["y"] + slot["h"], image.height)):
        for x in range(slot["x"], min(slot["x"] + slot["w"], image.width)):
            if pixels[x, y] in colours:
                count += 1
    return count


def knife_colours():
    """The two non-black entries of the sheet, read from its sidecar rather than typed here."""
    with open(os.path.join(ROOT, "game", "sprites_src", "weapons", "spr_pp_knife.json"), "r", encoding="utf-8") as fh:
        sidecar = json.load(fh)
    out = set()
    for row in sidecar["colours_used"]:
        if row["role"] == "outline":
            continue
        text = row["hex"].lstrip("#")
        out.add((int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)))
    return out


def grab(hwnd, box, path):
    """One 1x frame of the game's viewport, cut out of the game's window.

    box is the viewport INSIDE a window capture, which is what capture_title.viewport_box_and_score returns, so the
    window's own rectangle is added before the screen is read. Measured 2026-10-27: passing the box straight to a
    screen copy reads whatever sits at those coordinates on the desktop, and on this machine that was a privacy blind
    over the primary monitor, so every frame of a run came back as the blind instead of the game.
    """
    rect = cap.get_window_rect(hwnd)
    if rect is None:
        return None, "the window has no rectangle"
    ok, how = cap.capture_with_pil((rect[0] + box[0], rect[1] + box[1], box[2], box[3]), path)
    if not ok:
        return None, how
    image = Image.open(path).convert("RGB")
    if image.size != (256 * SCALE, 240 * SCALE):
        return None, "the copy is %dx%d, not the 768x720 viewport" % image.size
    return image.resize((256, 240), Image.NEAREST), "ok"


def press(hwnd, name, code):
    if not cap.game_has_focus(hwnd):
        ok, note = cap.ensure_key_focus(hwnd, attempts=4)
        if not ok:
            return "not sent (%s)" % note
    return cap.send_vk_focused(code)


# The route to the first fight, walked with the keys a player has. The schedule itself is capture_first_fight.py's
# EVENTS, imported rather than retyped: that module reads the arrival walk out of the maps' own spawn and trigger
# tiles, and tests/test_route_continuity.py already holds it to a player's keys with no environment flag. What this
# tool adds is the stop line: every press up to and including the confirm that starts the fight, and nothing after it,
# because the frames this tool wants are the board, the menu row and the swing, not the fight's result.
ROUTE_STOP_KEY = "FIGHT_FIRST_S"
ATTEMPTS = 8          # confirms on the battle board before the tool gives up on the swing
PRESS_GAP_S = 2.4     # capture_first_fight.py's measured spacing between this fight's own phase advances


def route_events():
    """The player's presses up to the fight's first confirm, from capture_first_fight.py itself."""
    stop = getattr(first_fight, ROUTE_STOP_KEY)
    return [(at_s, action) for at_s, action in first_fight.EVENTS if at_s <= stop]


def route_step(log_path=None):
    """The route step the game itself says it is on, read from the engine's own `PP route:` lines.

    The engine writes them to the same log the launch redirects its output to, so this needs no slice run and no
    environment flag: the route is the one data/slice.json declares, and the game announces every handoff.
    """
    path = log_path or os.path.join(ROOT, "build", "knife_swing_game.log")
    step = ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if "PP route: step " not in line:
                    continue
                tail = line.split("handed to step ", 1)
                step = (tail[1] if len(tail) == 2 else line.split("PP route: step ", 1)[1]).split(" ")[0].strip()
    except FileNotFoundError:
        return ""
    return step


def walk_to_the_fight(hwnd, say=print):
    """Send the route's presses, and let the game's own route step decide the next one.

    The first four presses are on capture_first_fight.py's clock because they are the ones whose timing was measured
    on this build: the title, NEW GAME, the crawl skip and the drive skip. Everything after the drive is driven by
    state, not by a stopwatch. Measured 2026-10-27: the fixed schedule walked the arrival map at its own times and
    stopped six presses in, so the hero never reached the gate, and every later press landed on a map. Reading
    `PP route:` out of the engine's log removes that whole class of slip.

    Returns the step the game ended on.
    """
    events = route_events()
    walk_keys = [action for _at_s, action in events if action in ("down", "left", "up", "right")]
    timed = [(at_s, action) for at_s, action in events if at_s <= DRIVE_SKIP_S]
    started = time.monotonic()
    for at_s, action in timed:
        now = time.monotonic() - started
        if now < at_s:
            time.sleep(at_s - now)
        key, star, seconds = action.partition("*")
        code = cap.KEY_CODES[key]
        if star:
            result = first_fight.hold(hwnd, key, code, float(seconds))
        else:
            result = first_fight.press(hwnd, key, code)
        say("P: %.1f s %s %s" % (at_s, action, result))

    deadline = time.time() + ROUTE_TIMEOUT_S
    step = route_step()
    pending = list(walk_keys)
    last = 0.0
    flip = False
    while time.time() < deadline:
        step = route_step()
        if step == "fight":
            say("P: the route is on its fight step, so the presses stop here")
            return step
        if step == "arrival":
            gap = ROUTE_WALK_GAP_S
        elif step in ("gate", "boarding"):
            gap = ROUTE_PAGE_GAP_S
        else:
            gap = ROUTE_START_GAP_S
        # The action is chosen only when a press is actually due. Choosing it every poll popped a walk key every
        # quarter second while presses were going out every 0.45 s, so six of the twelve keys were swallowed and the
        # hero stopped short of the gate (measured 2026-10-27 on the run before this one).
        if time.time() - last >= gap:
            if step == "arrival":
                action = pending.pop(0) if pending else "confirm"
            elif step == "drive":
                action = "cancel"
            elif step in ("gate", "boarding"):
                action = "confirm"
            else:
                # No route line yet, which is the title, the crawl, or the drive before it announces its handoff:
                # confirm moves the title and the crawl, and cancel is the drive's own skip, so both go out in turn.
                flip = not flip
                action = "cancel" if flip else "confirm"
            if action == "cancel":
                result = first_fight.hold(hwnd, "cancel", cap.KEY_CODES["cancel"], 0.6)
            else:
                result = first_fight.press(hwnd, action, cap.KEY_CODES[action])
            say("P: step %r, pressed %s: %s" % (step or "<none>", action, result))
            last = time.time()
        time.sleep(0.25)
    return step


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Capture the running game's knife menu row and swing frames.")
    parser.add_argument("--wait", type=float, default=300.0,
                        help="seconds the whole launch may run before the watchdog ends it")
    parser.add_argument("--out-dir", default=os.path.join(ROOT, "output"))
    pp_launch.add_launch_flags(parser, default_wait=0.0)
    args = parser.parse_args(argv)

    policy = pp_launch.policy_from_args(args)
    policy.min_idle = 120.0
    if not policy.gate("knife swing capture"):
        return pp_launch.EXIT_REFUSED

    exe_path, win_path = build()
    env = policy.env()
    log_path = os.path.join(ROOT, "build", "knife_swing_game.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    game_log = open(log_path, "wb")
    print("P: launching %s -game %s with a player's keys and no environment flag" % (exe_path, win_path))
    process = subprocess.Popen([exe_path, "-game", win_path], cwd=os.path.dirname(exe_path),
                               stdin=subprocess.DEVNULL, stdout=game_log, stderr=subprocess.STDOUT, env=env)
    cap.start_watchdog(process, args.wait + 180.0)
    hwnd = None
    try:
        match = cap.find_window(
            lambda hwnd, pid, title, visible, rect: visible and pid == process.pid
            and cap.GAME_WINDOW_TITLE.lower() in title.lower(),
            timeout_s=WINDOW_TIMEOUT_S)
        if match is None:
            print("P: the game window did not appear within %.0f s" % WINDOW_TIMEOUT_S)
            return 1
        hwnd = match[0]
        policy.place(hwnd, cap.get_window_rect(hwnd))
        time.sleep(SETTLE_S)

        # A screen copy shows whatever is on top of the rectangle, not the window it asked for. Measured 2026-10-27:
        # a run's every frame came back as another application's dashboard, because the game sat at 1920,0 behind a
        # window already there on the second monitor. So the window is held on top and the rectangle is checked for
        # coverage before any frame is taken, with capture_title.py's own two functions and no third rule here.
        cap.hold_on_top(hwnd)
        rect, coverage = cap.ensure_game_visible(hwnd, cap.get_window_rect(hwnd))
        print("P: window coverage: %s" % coverage)
        if rect is None:
            print("P: every placement of the game window stays covered, so no copy would be the game")
            return 1

        # The viewport is found before the walk, not after it, because the walk's own seconds start from here and
        # capture_first_fight.py starts its clock in the same place: window found, settled, pre-roll read.
        rect, box, score, note = play_demo.pre_roll_viewport(
            hwnd, os.path.join(ROOT, "build", "knife_swing_preroll.png"))
        if box is None:
            print("P: the frame is not the game's viewport: %s" % note)
            return 1
        print("P: viewport %s in the window, score %.3f" % (str(box), score))

        step = walk_to_the_fight(hwnd)
        print("P: the route ended on step %r" % step)
        time.sleep(MENU_SETTLE_S)

        slot = enemy_slot()
        colours = knife_colours()
        print("P: enemy slot %s, counting %s" % (slot, sorted(colours)))

        menu_path = os.path.join(args.out_dir, "battle_knife_menu.png")
        os.makedirs(args.out_dir, exist_ok=True)
        menu, how = grab(hwnd, box, os.path.join(ROOT, "build", "knife_swing_menu_3x.png"))
        if menu is None:
            print("P: the menu frame copy failed: %s" % how)
            return 1
        menu.save(menu_path)
        print("P: wrote %s (the menu frame, %d knife pixels in the slot)"
              % (menu_path, swing_pixels(menu, slot, colours)))

        # The board opens by itself once the trigger fires, and the intro plays before the command band, so one press
        # at one fixed moment is a guess at which phase it lands in. Each attempt sends one confirm and then takes the
        # burst inside the 18 steps the slash is drawn (0.3 s at 60 fps, PP_SLASH_FRAME_STEPS 6 across three frames),
        # and the attempt whose burst counts the sheet's own colours in the enemy slot is the one that caught the
        # swing. The first attempt is the FIGHT cell, the second the power lock, and the gap between them is the one
        # capture_first_fight.py measured for this fight. The menu row is re-read before every press and the last copy
        # is the command band the swing came from.
        shots = []
        for attempt in range(1, ATTEMPTS + 1):
            band, how = grab(hwnd, box, os.path.join(ROOT, "build", "knife_swing_menu_3x.png"))
            if band is not None:
                band.save(menu_path)
            print("P: attempt %d confirm press: %s" % (attempt, press(hwnd, "confirm", VK_Z)))
            started = time.time()
            for index, offset in enumerate(BURST_S, start=1):
                wait = offset - (time.time() - started)
                if wait > 0:
                    time.sleep(wait)
                path = os.path.join(ROOT, "build", "knife_swing_%d_3x.png" % index)
                frame, how = grab(hwnd, box, path)
                if frame is None:
                    print("P: attempt %d frame %d copy failed: %s" % (attempt, index, how))
                    continue
                out = os.path.join(args.out_dir, "battle_knife_swing_%d.png" % index)
                frame.save(out)
                count = swing_pixels(frame, slot, colours)
                shots.append((count, out))
                print("P: attempt %d frame %d at %.2f s: %d knife pixels in the slot, wrote %s"
                      % (attempt, index, offset, count, out))
            if any(count > 0 for count, _ in shots):
                print("P: attempt %d's burst carries the swing, so no further press is sent" % attempt)
                break
            time.sleep(PRESS_GAP_S)

        if not shots:
            print("P: no swing frame was copied, so there is nothing to show")
            return 1
        best_count, best_path = max(shots)
        best = Image.open(best_path).convert("RGB")
        final = os.path.join(args.out_dir, "battle_knife_swing.png")
        best.save(final)
        print("P: wrote %s, the best of %d burst frames" % (final, len(shots)))
        if best_count <= 0:
            print("P: no frame carried the sheet's colours in the enemy slot, so the swing was NOT captured")
            return 1
        return 0
    finally:
        if hwnd is not None:
            cap.release_on_top(hwnd)
            cap.close_window(hwnd)
        deadline = time.time() + 6.0
        while time.time() < deadline and process.poll() is None:
            time.sleep(0.2)
        if process.poll() is None:
            print("P: the game did not close on request, terminating it")
            cap.kill_tree(process)
        else:
            print("P: the game closed on request (exit code %s)" % process.returncode)


if __name__ == "__main__":
    sys.exit(main())
