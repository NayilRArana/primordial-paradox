#!/usr/bin/env python3
"""fight_tour.py: prove the three battles end to end in the REAL compiled game (card BATTLE-PROOF, 2026-11-02).

The game side is the debug door PP_FIGHT_TOUR in game\\scripts\\pp_overworld\\pp_overworld.gml: after the title it starts each
fight through pp_overworld_start_encounter and plays it to a real end twice, SPARE then KILL, by holding the same logical
actions a player holds. This driver launches the build copy once per encounter (the room differs, so PP_WARP differs), gets
the game through the title with Enter, waits for the game's own `PP fight tour: done` line, copies the game's own frames
(screen_save, 768x720) out of the game's save folder, cuts them to 256x240 and writes output\\battle_proof_2026-11-02\\REPORT.md
and a contact sheet.

The launch goes through pp_launch.launch, so it is muted, quiet (no console), and gated: tools\\idle_check.py refuses to open a
window while the machine is in use or a desktop automation is running. A refusal prints the gate's own text and exits with
EXIT_REFUSED; there is no force flag here on purpose.

Usage:
    python tools\\fight_tour.py --exe D:\\Temp\\fight_tour_verify\\PrimordialParadox.exe --win D:\\Temp\\fight_tour_verify\\PrimordialParadox.win
    python tools\\fight_tour.py --parse-only path\\to\\game.log      (read a log, print the outcome table, open nothing)
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import sys
import time

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

OUT_DIR = os.path.join(ROOT, "output", "battle_proof_2026-11-02")
FRAME_DIR = os.path.join(OUT_DIR, "frames")
SELF_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "PrimordialParadox")
ENCOUNTERS = ("morgan_gate", "tutorial_sailors", "percy")
ROOMS = {"morgan_gate": "southampton_town_quay", "tutorial_sailors": "ship_small", "percy": "ship_cabin"}
STEPS = ("intro", "menu", "talk", "hit", "ending")

# The two line shapes the game writes (pp_fight_tour_result and the per step state line).
RESULT_RE = re.compile(r"PP fight tour: (\w+) path=(spare|kill) result=(\w+) turns=(-?\d+)")
STATE_RE = re.compile(r"PP fight tour: (\w+) (spare|kill) state=(.*)")
SHOT_RE = re.compile(r"PP fight tour: shot (pp_fight_\w+\.png)")
DONE_NEEDLE = "PP fight tour: done"
ABORT_NEEDLES = ("state=aborted", "state=stalled", "state=never_entered_battle")
EXPECTED = {"spare": "spared", "kill": "won"}


def parse_fight_log(text):
    """Read the game's log text. Returns {"runs": [...], "states": [...], "shots": [...], "done": bool, "aborted": bool}.

    A run is {"id", "path", "result", "turns"}; a state is {"id", "path", "state"}. Anything else in the log is ignored.
    """
    runs, states, shots = [], [], []
    for line in text.splitlines():
        found = RESULT_RE.search(line)
        if found:
            runs.append({"id": found.group(1), "path": found.group(2), "result": found.group(3), "turns": int(found.group(4))})
            continue
        found = SHOT_RE.search(line)
        if found:
            shots.append(found.group(1))
            continue
        found = STATE_RE.search(line)
        if found:
            states.append({"id": found.group(1), "path": found.group(2), "state": found.group(3).strip()})
    return {
        "runs": runs,
        "states": states,
        "shots": shots,
        "done": DONE_NEEDLE in text,
        "aborted": any(needle in text for needle in ABORT_NEEDLES),
    }


def run_verdict(run):
    """PASS when the run ended the way its path promises (spare -> spared, kill -> won); else the finding."""
    want = EXPECTED.get(run["path"])
    return "PASS" if run["result"] == want else "FINDING (%s, wanted %s)" % (run["result"], want)


def native_frame(src, dst):
    """Cut the 256x240 game screen out of a 768x720 screen_save (every third pixel, no filter)."""
    from PIL import Image
    image = Image.open(src).convert("RGB")
    if image.width % 256 or image.height % 240:
        return False
    factor = max(1, image.width // 256)
    image.resize((image.width // factor, image.height // factor), Image.Resampling.NEAREST).save(dst, "PNG")
    return True


def contact_sheet(frames, dst):
    """One PNG: a row per run, a column per step, each cell a 256x240 frame."""
    from PIL import Image, ImageDraw
    runs = sorted({(f["id"], f["path"]) for f in frames})
    if not runs:
        return False
    sheet = Image.new("RGB", (len(STEPS) * 260, len(runs) * 262), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    for row, (enc, path) in enumerate(runs):
        for col, step in enumerate(STEPS):
            name = "pp_fight_%s_%s_%s.png" % (enc, path, step)
            full = os.path.join(FRAME_DIR, name)
            if os.path.exists(full):
                sheet.paste(Image.open(full).convert("RGB"), (col * 260 + 2, row * 262 + 20))
            draw.text((col * 260 + 4, row * 262 + 4), "%s %s %s" % (enc, path, step), fill=(220, 220, 220))
    sheet.save(dst, "PNG")
    return True


def write_report(runs, frames, notes, path, states=()):
    lines = ["# Battle proof report (real game build)", "",
             "Source: the game's own `PP fight tour:` log lines and its own screen_save frames. No simulator is involved.", "",
             "| encounter | path | result | turns | verdict |", "|---|---|---|---|---|"]
    for run in runs:
        lines.append("| %s | %s | %s | %d | %s |" % (run["id"], run["path"], run["result"], run["turns"], run_verdict(run)))
    if not runs:
        lines.append("| (none) | | | | NO RUN COMPLETED |")
    back = {(st["id"], st["path"]) for st in states if st["state"] == "back_in_world"}
    ending = {(f["id"], f["path"]) for f in frames if f["name"].endswith("_ending.png")}
    lines += ["", "## Per run: ending frame and return to the world", "", "| encounter | path | ending frame | back_in_world |", "|---|---|---|---|"]
    for run in runs:
        key = (run["id"], run["path"])
        lines.append("| %s | %s | %s | %s |" % (run["id"], run["path"], "yes" if key in ending else "NO", "yes" if key in back else "NO"))
    lines += ["", "## Frames (256x240, cut from the game's 768x720 screen_save)", ""]
    for frame in sorted(frames, key=lambda f: f["name"]):
        lines.append("- frames/%s" % frame["name"])
    lines += ["", "Contact sheet: contact_sheet.png", "", "## Notes", ""]
    lines += ["- " + note for note in notes] or ["- none"]
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------------------------------------------
# The window side. Windows only; imported lazily so the parser and the report run anywhere (and in the test).

def _win():
    import ctypes
    user32 = ctypes.windll.user32

    def hwnd():
        return user32.FindWindowW(None, "Primordial Paradox")

    def key(vk):
        user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.08)
        user32.keybd_event(vk, 0, 2, 0)

    def focus():
        h = hwnd()
        if not h:
            return False
        user32.keybd_event(0x12, 0, 0, 0)
        user32.keybd_event(0x12, 0, 2, 0)
        user32.ShowWindow(h, 9)
        user32.SetForegroundWindow(h)
        time.sleep(0.4)
        return True
    return key, focus


def log_text(path):
    try:
        with open(path, "rb") as handle:
            return handle.read().decode("utf-8", "replace")
    except OSError:
        return ""


def play_one(enc, args, say=print):
    """One launch for one encounter. Returns (parsed log, exit code); a refused gate returns (None, EXIT_REFUSED)."""
    import pp_launch
    key, focus = _win()
    log = os.path.join(OUT_DIR, "game_%s.log" % enc)
    os.makedirs(OUT_DIR, exist_ok=True)
    for old in glob.glob(os.path.join(SELF_DIR, "pp_fight_*.png")):
        try:
            os.remove(old)
        except OSError:  # gate: ok a stale frame that cannot be removed is overwritten by the same name later
            pass
    policy = pp_launch.Policy(show=False, sound=False, wait_s=args.idle_wait)
    extra = {"PP_WARP": ROOMS[enc], "PP_FIGHT_TOUR": enc, "PP_ROUTE_HOLD": "drive"}
    run, code = pp_launch.launch(args.exe, args.win, label="fight tour " + enc, policy=policy, log_path=log, extra=extra, say=say)
    if run is None:
        return None, code
    try:
        t0 = time.time()
        while time.time() - t0 < 25 and "title_theme streaming" not in log_text(log):
            time.sleep(1)
        presses = 0
        while presses < 8 and "PP fight tour: begin" not in log_text(log):
            focus()
            key(0x0D)
            presses += 1
            time.sleep(2.0)
        deadline = time.time() + args.timeout
        while time.time() < deadline:
            text = log_text(log)
            parsed = parse_fight_log(text)
            if parsed["done"] or parsed["aborted"]:
                break
            time.sleep(2)
    finally:
        run.finish("fight tour " + enc)
    time.sleep(1)
    return parse_fight_log(log_text(log)), 0


def collect_frames(enc, names):
    """Copy the game's own frames out of its save folder and cut each to 256x240. Returns [{"id","name"}]."""
    os.makedirs(FRAME_DIR, exist_ok=True)
    got = []
    for name in sorted(set(names)):
        src = os.path.join(SELF_DIR, name)
        if not os.path.exists(src):
            continue
        shutil.copyfile(src, os.path.join(FRAME_DIR, "raw_" + name))
        if native_frame(src, os.path.join(FRAME_DIR, name)):
            m = re.match(r"pp_fight_(\w+?)_(spare|kill)_(\w+)\.png", name)
            got.append({"id": m.group(1) if m else enc, "path": m.group(2) if m else "", "name": name})
    return got


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--exe", default=r"D:\Temp\fight_tour_verify\PrimordialParadox.exe")
    parser.add_argument("--win", default=r"D:\Temp\fight_tour_verify\PrimordialParadox.win")
    parser.add_argument("--only", default="", help="one encounter id instead of all three")
    parser.add_argument("--timeout", type=float, default=1500.0, help="seconds to wait per launch for the done line")
    parser.add_argument("--idle-wait", type=float, default=0.0, help="seconds to poll the idle gate before giving up")
    parser.add_argument("--parse-only", default="", help="a game log to read; prints the table and opens nothing")
    args = parser.parse_args(argv)

    if args.parse_only:
        parsed = parse_fight_log(log_text(args.parse_only))
        for run in parsed["runs"]:
            print("%s %s %s turns=%d %s" % (run["id"], run["path"], run["result"], run["turns"], run_verdict(run)))
        return 0

    import pp_launch
    runs, frames, notes, states = [], [], [], []
    for enc in ([args.only] if args.only else list(ENCOUNTERS)):
        parsed, code = play_one(enc, args)
        if parsed is None:
            notes.append("REFUSED by the launch gate before %s; no window was opened (exit %s)." % (enc, code))
            write_report(runs, frames, notes, os.path.join(OUT_DIR, "REPORT.md"), states)
            return code if code else pp_launch.EXIT_REFUSED
        runs += parsed["runs"]
        states += parsed["states"]
        frames += collect_frames(enc, parsed["shots"])
        if not parsed["done"]:
            tail = [s for s in parsed["states"] if s["id"] == enc][-1:]
            notes.append("%s did not reach the done line: last state %s" % (enc, tail[0]["state"] if tail else "none"))
    contact_sheet(frames, os.path.join(OUT_DIR, "contact_sheet.png"))
    write_report(runs, frames, notes, os.path.join(OUT_DIR, "REPORT.md"), states)
    bad = [r for r in runs if run_verdict(r) != "PASS"]
    print("fight tour: %d runs, %d findings; report %s" % (len(runs), len(bad) + len(notes), os.path.join(OUT_DIR, "REPORT.md")))
    return 0 if runs and not bad and not notes else 1


if __name__ == "__main__":
    sys.exit(main())
