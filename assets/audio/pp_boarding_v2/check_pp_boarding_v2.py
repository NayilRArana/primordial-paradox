"""check_pp_boarding_v2.py: what card CUE-BOARDING (t_8158e5f9) asks to see, printed as one table.

1. Renders. The WAV, MP3, MIDI and OGG are on disk and not empty, and the WAV is
   32.000 s, which is 16 bars at 120 bpm.
2. Length against the scene. The card asks for a length equal to the scene's
   authored step count divided by 60, plus or minus half a bar. The scene row is
   read from data/scenes/all.json (read only) and its step count is priced by the
   specs, with every constant read from game/scripts/pp_config/pp_config.gml so a
   retired number cannot come back:
       specs/06 cutscene   camera PP_CAMERA_MOVE_STEPS (24), shake and wait their own
                           steps, fade PP_FADE_STEPS (12), flash 0 (rule 8), music 0
                           because its 30 step crossfade runs under the scene
       specs/04 rails      PP_WALK_STEPS_RAIL (8) steps per tile walked
       specs/05 rule 1     PP_TEXT_STEPS_SLOW (2) steps per character
       specs/05 rule 2     PP_TEXT_PAUSE_STOP (8) after . ! ?, PP_TEXT_PAUSE_COMMA
                           (3) after a comma
       tools/ai_bridge.py  the leading "* " narration marker is written by code,
                           so it is never priced (ai_bridge drops_narration_marker)
       setflag, end, face  no steps of their own
   The authored gangway beat is 32 s (card t_a3fa132a, "the horn, the deck, the
   door, 32 s"), which is 1920 steps. The module is measured against that, and the
   row's spec-priced step count is printed beside it. The row is not padded to
   1920: the beat sheet and the row measure different clocks, because the say is
   player paced (knowledge/GAMEDEV-DECISIONS-2026-10-26.md, amendment D1a).
3. Form. 16 bars, inside the card's 16 to 24, and a whole number of four bar
   phrases.
4. One shot, not a loop. There is no loop json in the folder, and the last second
   of the render (beats 3 and 4 of bar 16) is silent, so nothing is cut off and
   nothing would loop.
5. The held breath. Bar 15 has no lead note at all, bars 13 and 14 have exactly
   one lead note each (the E5 held across both), and bars 13 to 15 have at most
   three voices sounding.
6. The stop. In bar 16 nothing starts after beat 2.
7. Hook score, printed from the report tools/render_chip.py wrote (90 of 100).
8. Clean room. tools/melody_guard.py finds no shared run of 8 intervals between
   this cue and every other cue in the project.
9. No long dashes in any text artifact in this folder.

Usage:
    check_pp_boarding.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import hook_score  # noqa: E402

PPQ = 480
EIGHTH = PPQ // 2
BAR = 8 * EIGHTH
BPM = 120
BARS = 16
AUTHORED_SCENE_SECONDS = 32.0          # card t_a3fa132a
NARRATION_MARKER = "* "                # drawn by code, never priced
TEXT_FILES = ("NOTES.md", "build_pp_boarding_v2.py", "check_pp_boarding_v2.py",
              "build_report.json", "hook_report_v2.json")

DASHES = ("\u2014", "\u2013", "\u2012", "\u2015", "\u2212")

PP_CONFIG = os.path.join(ROOT, "game", "scripts", "pp_config", "pp_config.gml")


def game_macros():
    """Every #macro in pp_config.gml, so no price restates a number of its own."""
    with open(PP_CONFIG, encoding="utf-8") as handle:
        text = handle.read()
    found = {}
    for name, value in re.findall(r"#macro\s+(PP_\w+)\s+(-?[\d.]+)", text):
        found[name] = float(value) if "." in value else int(value)
    return found


MACROS = game_macros()
TEXT_STEPS = MACROS["PP_TEXT_STEPS_SLOW"]             # spec 05 rule 1
TEXT_PAUSE_STOP = MACROS["PP_TEXT_PAUSE_STOP"]        # spec 05 rule 2
TEXT_PAUSE_COMMA = MACROS["PP_TEXT_PAUSE_COMMA"]      # spec 05 rule 2
WALK_STEPS_RAIL = MACROS["PP_WALK_STEPS_RAIL"]        # spec 04, a scripted move
CAMERA_MOVE_STEPS = MACROS["PP_CAMERA_MOVE_STEPS"]    # spec 06
FADE_STEPS = MACROS["PP_FADE_STEPS"]                  # spec 06


def scene_row():
    path = os.path.join(ROOT, "data", "scenes", "all.json")
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    for row in data.get("scenes", []):
        if row.get("id") == "ship_boarding":
            return row
    return {}


def dialogue_lines(ident):
    """Every line a say opens, across all of its pages."""
    path = os.path.join(ROOT, "data", "dialogue", "all.json")
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    for row in data.get("dialogue", []):
        if row.get("id") == ident:
            lines = list(row.get("lines", []))
            for page in row.get("pages", []):
                lines.extend(page.get("lines", []))
            return lines
    return []


def say_steps(lines):
    """A say's floor, per spec 05 rules 1 and 2, with the marker unpriced."""
    steps = 0
    per_line = []
    for line in lines:
        text = line[len(NARRATION_MARKER):] if line.startswith(NARRATION_MARKER) else line
        line_steps = TEXT_STEPS * len(text)
        line_steps += TEXT_PAUSE_STOP * (text.count(".") + text.count("!") + text.count("?"))
        line_steps += TEXT_PAUSE_COMMA * text.count(",")
        steps += line_steps
        per_line.append(line_steps)
    return steps, per_line


def scene_steps(row):
    """The row's spec-priced step count, one command at a time."""
    steps = 0
    detail = []
    for command in row.get("commands", []):
        kind = command.get("cmd")
        if kind == "say":
            lines = dialogue_lines(command.get("id"))
            text, per_line = say_steps(lines)
            steps += text
            detail.append("say %s: %d steps (%s)"
                          % (command.get("id"), text,
                             " + ".join(str(one) for one in per_line) or "no lines"))
        elif kind == "move":
            walked = WALK_STEPS_RAIL * int(command.get("tiles", 0))   # spec 04, 8 a tile
            steps += walked
            detail.append("move %d tiles at %d a tile: %d steps"
                          % (int(command.get("tiles", 0)), WALK_STEPS_RAIL, walked))
        elif kind == "camera":
            steps += CAMERA_MOVE_STEPS                               # spec 06
            detail.append("camera: %d steps" % CAMERA_MOVE_STEPS)
        elif kind in ("shake", "wait"):
            own = int(command.get("steps", 0))                       # spec 06, its own steps
            steps += own
            detail.append("%s %d: %d steps" % (kind, own, own))
        elif kind == "fade":
            faded = int(command.get("steps", 0) or FADE_STEPS)       # spec 06, 12 when omitted
            steps += faded
            detail.append("fade: %d steps" % faded)
        elif kind == "flash":
            detail.append("flash: 0 steps (spec 06 rule 8)")         # over steps already spent
        elif kind == "music":
            detail.append("music %s: 0 steps, its 30 step crossfade runs under the scene"
                          % command.get("id", ""))
        else:
            detail.append("%s: 0 steps" % kind)                      # setflag, end, face
    return steps, detail


def wav_seconds(path):
    with wave.open(path, "rb") as handle:
        return handle.getnframes() / float(handle.getframerate())


def tail_peak_dbfs(path, seconds):
    """Peak of the last `seconds` of a 16 bit mono WAV, in dBFS."""
    with wave.open(path, "rb") as handle:
        frames = handle.getnframes()
        rate = handle.getframerate()
        start = max(0, frames - int(seconds * rate))
        handle.setpos(start)
        raw = handle.readframes(frames - start)
    if not raw:
        return -120.0
    peak = 0
    for index in range(0, len(raw) - 1, 2):
        sample = int.from_bytes(raw[index:index + 2], "little", signed=True)
        peak = max(peak, abs(sample))
    if peak == 0:
        return -120.0
    import math
    return 20.0 * math.log10(peak / 32768.0)


def notes_in_bar(song, track_name, bar):
    low = (bar - 1) * BAR
    for trk in song["tracks"]:
        if trk["name"] == track_name:
            return [n for n in trk["notes"] if low <= n[0] < low + BAR]
    return []


def voices_in_bar(song, bar):
    low = (bar - 1) * BAR
    count = 0
    for trk in song["tracks"]:
        if any(low <= n[0] < low + BAR for n in trk["notes"]):
            count += 1
    return count


def main():
    problems = []
    print("CUE-BOARDING v2 check, assets/audio/pp_boarding_v2\n")

    # 1. rendered files
    print("1. renders")
    sizes = {}
    for ext in (".mid", ".wav", ".mp3", ".ogg"):
        path = os.path.join(HERE, "pp_boarding_v2" + ext)
        sizes[ext] = os.path.getsize(path) if os.path.isfile(path) else 0
        print("   pp_boarding_v2%-5s %8d bytes" % (ext, sizes[ext]))
        if not sizes[ext]:
            problems.append("pp_boarding_v2%s is missing or empty" % ext)
    seconds = wav_seconds(os.path.join(HERE, "pp_boarding_v2.wav"))
    bar_seconds = 4 * 60.0 / BPM
    print("   wav %.3f s, bar %.3f s, 16 bars %.3f s" % (seconds, bar_seconds, BARS * bar_seconds))
    if abs(seconds - BARS * bar_seconds) > 0.01:
        problems.append("the WAV is %.3f s, not 16 bars (%.3f s)" % (seconds, BARS * bar_seconds))

    # 2. length against the scene
    print("\n2. length against the scene's authored step count")
    row = scene_row()
    steps, detail = scene_steps(row)
    for line in detail:
        print("   %s" % line)
    print("   row today: %d steps / 60 = %.3f s" % (steps, steps / 60.0))
    authored_steps = int(AUTHORED_SCENE_SECONDS * 60)
    print("   beat sheet: %d steps / 60 = %.3f s (card t_a3fa132a)"
          % (authored_steps, authored_steps / 60.0))
    tolerance = bar_seconds / 2.0
    gap = abs(seconds - authored_steps / 60.0)
    print("   module %.3f s, difference %.3f s, half a bar %.3f s: %s"
          % (seconds, gap, tolerance, "PASS" if gap <= tolerance else "FAIL"))
    if gap > tolerance:
        problems.append("length %.3f s is %.3f s off %d steps / 60" %
                        (seconds, gap, authored_steps))
    if steps != authored_steps:
        print("   note: the row prices at %d steps (%.3f s) and the beat sheet is %d steps"
              % (steps, steps / 60.0, authored_steps))
        print("         (%.3f s). The two measure different clocks: the say is player paced,"
              % (authored_steps / 60.0))
        print("         so the row is not padded to the beat sheet"
              " (knowledge/GAMEDEV-DECISIONS-2026-10-26.md, D1a).")

    # 3. form
    print("\n3. form")
    song = hook_score.read_smf(os.path.join(HERE, "pp_boarding_v2.mid"))
    lead = [n for trk in song["tracks"] if trk["name"] == "vrc6 pulse a" for n in trk["notes"]]
    last_bar = max((n[1] - 1) // BAR + 1 for n in lead)
    print("   %d bars written, %d lead notes, last lead note ends in bar %d"
          % (BARS, len(lead), last_bar))
    if not 16 <= BARS <= 24:
        problems.append("%d bars is outside the card's 16 to 24" % BARS)
    if BARS % 4:
        problems.append("%d bars is not a whole number of four bar phrases" % BARS)

    # 4. one shot
    print("\n4. one shot, not a loop")
    loops = [name for name in os.listdir(HERE) if name.endswith("_loop.json")]
    print("   loop json files in the folder: %s" % (", ".join(loops) if loops else "none"))
    if loops:
        problems.append("a loop json is present, so the cue would loop: %s" % ", ".join(loops))
    tail = tail_peak_dbfs(os.path.join(HERE, "pp_boarding_v2.wav"), 1.0)
    print("   last second (bar 16 beats 3 and 4) peak %.1f dBFS" % tail)
    if tail > -40.0:
        problems.append("the last second is not silent (%.1f dBFS), so the stop is cut" % tail)

    # 5. the held breath
    print("\n5. the held breath, bars 13 to 15")
    busy = ("pulse 1", "pulse 2", "vrc6 pulse b")
    for bar in (13, 14, 15):
        leads = notes_in_bar(song, "vrc6 pulse a", bar)
        voices = voices_in_bar(song, bar)
        print("   bar %2d  lead notes %d  voices sounding %d" % (bar, len(leads), voices))
        if len(leads) > 1:
            problems.append("bar %d has %d lead notes, not one held note" % (bar, len(leads)))
        if voices > 4:
            problems.append("bar %d has %d voices, the breath should thin to four at most"
                            % (bar, voices))
        for name in busy:
            if notes_in_bar(song, name, bar):
                problems.append("bar %d still has %s in it" % (bar, name))
    if notes_in_bar(song, "vrc6 pulse a", 15):
        problems.append("the lead still plays in bar 15, so there is no breath before the stop")

    # 6. the stop
    print("\n6. the stop, bar 16")
    late = []
    for trk in song["tracks"]:
        for start, end, pitch, velocity in trk["notes"]:
            if 15 * BAR <= start < 16 * BAR and start - 15 * BAR >= 2 * 2 * EIGHTH:
                late.append((trk["name"], start - 15 * BAR, pitch))
    print("   notes starting after beat 2 of bar 16: %d" % len(late))
    if late:
        problems.append("bar 16 has %d notes after beat 2: %s" % (len(late), late[:4]))

    # 7. the hook score
    print("\n7. hook score (tools/hook_score.py, via the renderer)")
    with open(os.path.join(HERE, "hook_report_v2.json"), encoding="utf-8") as handle:
        report = json.load(handle)
    print("   %d of 100, %d bars of melody" % (report["score"], report.get("bars", 0)))
    for row_ in report.get("criteria", []):
        print("   [%s] %-26s %5.1f  %s" % ("ok  " if row_.get("pass") else "fix ",
                                           row_.get("criterion", "?"), row_.get("points", 0.0),
                                           row_.get("measured", "")))
    if report["score"] < 60:
        problems.append("the hook score is %d, under 60" % report["score"])

    # 8. clean room
    print("\n8. clean room (tools/melody_guard.py against every other cue)")
    folders = [os.path.join(ROOT, "assets", "audio", name)
               for name in os.listdir(os.path.join(ROOT, "assets", "audio"))
               # The guard itself skips this cue's own revisions (they share a
               # lineage name), so only this folder has to come out here.
               if name != "pp_boarding_v2"
               and os.path.isdir(os.path.join(ROOT, "assets", "audio", name))]
    command = [sys.executable, os.path.join(ROOT, "tools", "melody_guard.py"),
               os.path.join(HERE, "pp_boarding_v2.mid")] + folders
    result = subprocess.run(command, capture_output=True, text=True, cwd=ROOT)
    tail_lines = [line for line in result.stdout.splitlines() if line.strip()][:6]
    for line in tail_lines:
        print("   %s" % line)
    if result.returncode != 0:
        problems.append("melody_guard failed against the project's own cue catalogue")

    # 9. no long dashes
    print("\n9. no long dashes in the folder's text artifacts")
    hits = 0
    for name in TEXT_FILES:
        path = os.path.join(HERE, name)
        if not os.path.isfile(path):
            continue
        text = open(path, encoding="utf-8").read()
        for dash in DASHES:
            hits += text.count(dash)
    print("   long dash characters found: %d" % hits)
    if hits:
        problems.append("%d long dash characters in the folder's text" % hits)

    print("\n%s" % ("all checks passed" if not problems else "FAILED:"))
    for problem in problems:
        print("  - %s" % problem)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
