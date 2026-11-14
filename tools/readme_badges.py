#!/usr/bin/env python3
"""readme_badges.py: the README's badge block, written by rerunning the gates it claims.

Card t_4f984c7b (SUB-KIT-FINAL), checklist item 5's companion. A badge a human types is a claim
about a moment that has already passed, and a judge has no way to tell last night's green from
this morning's red. So no badge here is typed: the block lives between two markers in README.md,
this tool runs every gate named in it, renders one SVG badge per gate into docs/badges/, and
rewrites only what sits between the markers. Text and picture come from the same run, which is
what makes a stale badge impossible rather than unlikely.

The four gates are the ones the submission checklist tells a reader to run:

    python tools\\check_data.py            the data files load and agree
    python tools\\check_cleanroom.py       no study reference, no foreign name, no foreign phrase
    python tools\\nes_audit_all.py         every asset and frame against the picture chip's limits
    python tools\\play_demo.py --check     the recorded take is the game, long enough and in step

A gate that exits 0 is PASS. Anything else is FAIL, and the badge says so: a red badge in the
block is a fact about the tree, not an error in the tool, and that is the whole point of writing
the block from a run instead of from memory. The output carries no timestamp and no absolute
path, so two runs on an unchanged tree write byte identical files, and `--verify` can compare the
README against a fresh run by plain equality.

Usage
    python tools\\readme_badges.py --write     run the gates, write docs\\badges\\*.svg and the README block
    python tools\\readme_badges.py --verify    run the gates and refuse when the README block is stale
    python tools\\readme_badges.py --list      print the gates and their commands, run nothing

Exit codes: 0 the block and the badges match this run, or were just written; 1 a gate disagrees
with the README, a badge file is missing or disagrees, or a marker is absent; 2 bad argument.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "README.md")
BADGE_DIR = "docs/badges"

# The tracked reference Meta art run (card t_c398ddd1) and the local run folder it is copied from.
# Both are named in the block because tests/test_check_readme.py holds the page to them: one must be
# exempt from the on disk path check for a stated reason, the other must be in the tree.
REFERENCE_DIR = "knowledge/meta_art_reference/title_backdrop_c1"
RUN_DIR = "output/meta_art/title_backdrop/c1"
REFERENCE_ANSWER = "cached_response.json"
# Used only when this tool is pointed at a tree that does not hold the tracked run, which is a test
# fixture. On the real tree the timestamp is read from the tracked answer, and
# tests/test_check_readme.py reads the same field and fails when the page and the file disagree.
REFERENCE_RECORDED_AT = "2026-10-27T08:58:17Z"

START = "<!-- README-BADGES:START -->"
END = "<!-- README-BADGES:END -->"

# The NES limits section (card t_cd5212b6, judge-panel fix 5). The panel asked for a page that shows
# where the hardware limits are enforced in code, and the page may not carry a hand typed claim: the
# prose is stamped by tools/readme_meta.py and a hand edit fails its check. So this region, which the
# stamp masks out, carries the section, and every number in it is read out of the file it names and
# every path is resolved against the tree. A renamed module or a changed constant rewrites this text
# on the next `--write`, and `--verify` refuses a page that still says the old thing.
ENGINE_LIMITS = "game/scripts/pp_config/pp_config.gml"
ENGINE_ROLE = "game/scripts/pp_look/pp_look.gml"
ENGINE_COLOUR = "game/scripts/pp_data/pp_data.gml"
PALETTE_PPU = "data/palette_ppu.json"
PALETTE_MASTER = "data/nes_palette.json"
CHECKER_ASSET = "tools/nes_check.py"
CHECKER_FRAME = "tools/nes_composite_check.py"
CHECKER_ALL = "tools/nes_audit_all.py"
CHECKER_RUNTIME = "tools/check_runtime_palette.py"
CLEANROOM_REVIEW = "knowledge/CLEANROOM-REVIEW.md"
GEOGRAPHY_CARD = "data/maps/real_places.json"
LIMIT_MACROS = ("PP_FRAME_W", "PP_FRAME_H", "PP_ARENA_W", "PP_ARENA_H", "PP_MARKER_SIZE",
                "PP_ARENA_CAP_STEPS")
LIMIT_CONSTANTS = (
    (CHECKER_ASSET, ("TILE", "AREA", "MAX_COLOURS_ON_SCREEN")),
    (CHECKER_FRAME, ("MAX_BG_PALETTES", "MAX_SPRITE_PALETTES", "MAX_SPRITES_PER_LINE", "MAX_SPRITES")),
)

# The local AI bridge section (judge-panel fix 5, 2026-11-14). The panel asked for the bridge files and
# their build steps on the page a judge reads, beside the limits, so a reader can open the service and
# the gate in this checkout instead of trusting a still frame from the demo video. Same rule as the
# limits section: every path is resolved against the tree, the bind address, the port and the rung
# names are read out of the module, and a renamed file shows up as missing rather than as a dead link.
BRIDGE_SERVER = "tools/ai_bridge.py"
BRIDGE_META = "tools/meta_client.py"
BRIDGE_JUDGE = "data/talk/sailor_judge.json"
BRIDGE_CACHE = "data/ai_cache/bridge"
BRIDGE_PROBE = "tools/talk_scene_probe.py"
BRIDGE_BUILD = "tools/run.ps1"
BRIDGE_DOC = "docs/AI-BRIDGE.md"
REVIEW_CHECKLIST = "docs/REVIEW-CHECKLIST.md"
REVIEW_GATE = "tools/review_gate.py"

GREY = (60, 63, 74)
PASS_C = (60, 150, 92)
FAIL_C = (186, 68, 68)
INK = (255, 255, 255)

DEFAULT_TIMEOUT = 900

# The gates, in the order the checklist runs them. The arguments are a repository relative tool
# and its own arguments, so the README line is printable and the same list is what gets executed.
GATES = [
    {"slug": "check_data", "tool": "tools/check_data.py", "args": [], "label": "check_data"},
    {"slug": "check_cleanroom", "tool": "tools/check_cleanroom.py", "args": [], "label": "check_cleanroom"},
    {"slug": "nes_audit_all", "tool": "tools/nes_audit_all.py", "args": [], "label": "nes_audit_all"},
    {"slug": "play_demo_check", "tool": "tools/play_demo.py", "args": ["--check"], "label": "play_demo --check"},
]


def command_text(gate):
    return " ".join(["python", gate["tool"]] + gate["args"])


def status_of(exit_code):
    if exit_code is None:
        return "TIMEOUT"
    return "PASS" if exit_code == 0 else "FAIL"


def run_gate(gate, root=ROOT, timeout=DEFAULT_TIMEOUT, python=None):
    """Run one gate and keep only what the block needs: its exit code and how long it took."""
    runner = python or sys.executable
    command = [runner, os.path.join(root, gate["tool"].replace("/", os.sep))] + list(gate["args"])
    started = time.time()
    try:
        # stdin=DEVNULL for the same reason check_readme gives: this tool is run by a commit gate
        # and by pytest, and an inherited handle is not a valid one there. Measured on the sibling
        # tool on 2026-10-26; a child that cannot start reads exactly like a failing gate.
        proc = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=timeout,
                              stdin=subprocess.DEVNULL)
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        exit_code = None
    except OSError:
        exit_code = None
    return {
        "slug": gate["slug"],
        "label": gate["label"],
        "command": command_text(gate),
        "exit": exit_code,
        "status": status_of(exit_code),
        "seconds": round(time.time() - started, 1),
    }


def run_all(root=ROOT, timeout=DEFAULT_TIMEOUT, python=None):
    return [run_gate(gate, root, timeout, python) for gate in GATES]


def render_badge(label, status):
    """One flat SVG badge: the gate name on the left, its verdict on the right.

    No timestamp and no absolute path: the file is a picture of this run's verdict, and the date
    of that run is the commit that carries it. Keeping it free of both is what lets `--verify`
    compare bytes instead of guessing what may legitimately differ.
    """
    colour = PASS_C if status == "PASS" else FAIL_C
    left = 8 + 7 * len(label)
    right = 14 + 7 * len(status)
    width = left + right
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" viewBox="0 0 {w} 20" '
        'font-family="Consolas, \'DejaVu Sans Mono\', monospace" font-size="11">'
        '<rect width="{left}" height="20" fill="rgb({gr},{gg},{gb})"/>'
        '<rect x="{left}" width="{right}" height="20" fill="rgb({r},{g0},{b})"/>'
        '<text x="4" y="14" fill="rgb({ir},{ig},{ib})">{label}</text>'
        '<text x="{tx}" y="14" fill="rgb({ir},{ig},{ib})">{status}</text>'
        "</svg>\n"
    ).format(
        w=width, left=left, right=right, tx=left + 7,
        gr=GREY[0], gg=GREY[1], gb=GREY[2],
        r=colour[0], g0=colour[1], b=colour[2],
        ir=INK[0], ig=INK[1], ib=INK[2],
        label=_esc(label), status=_esc(status),
    )


def _esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def badge_path(slug):
    """The badge's address in the README. Always forward slashes, whatever the host separator is.

    os.path.join would write docs\\badges\\check_data.svg on this machine, which check_readme accepts
    (it normalises) and markdown does not (a backslash is an escape), so the picture would be a link
    that never renders on the page a judge reads.
    """
    return BADGE_DIR + "/" + slug + ".svg"


def reference_recorded_at(root=ROOT):
    """When the tracked reference answer was recorded, read from the file, not from memory."""
    path = os.path.join(root, REFERENCE_DIR.replace("/", os.sep), REFERENCE_ANSWER)
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh).get("recorded_at") or REFERENCE_RECORDED_AT
    except (OSError, ValueError):
        return REFERENCE_RECORDED_AT


def read_macro(root, rel, name):
    """The number a GML `#macro` holds, or None when the file or the macro is not there.

    Read, never remembered: the frame size on the page is the frame size the engine compiles with.
    """
    path = os.path.join(root, rel.replace("/", os.sep))
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                parts = line.split()
                if len(parts) >= 3 and parts[0] == "#macro" and parts[1] == name and parts[2].isdigit():
                    return int(parts[2])
    except OSError:
        return None
    return None


def read_constant(root, rel, name):
    """The number a Python module assigns to a module level name, or None. Same reason as read_macro."""
    path = os.path.join(root, rel.replace("/", os.sep))
    pattern = re.compile(r"^%s\s*=\s*(\d+)\s*$" % re.escape(name))
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                match = pattern.match(line)
                if match:
                    return int(match.group(1))
    except OSError:
        return None
    return None


def named(root, rel):
    """A repository path in a code span, with a visible marker when the tree does not hold it.

    The marker sits outside the code span on purpose: tools/check_readme.py only resolves a code span,
    so a path that has gone missing shows up in both readers, the sentence and that checker.
    """
    exists = os.path.exists(os.path.join(root, rel.replace("/", os.sep)))
    return "`%s`%s" % (rel, "" if exists else " (MISSING on this tree)")


def _num(value):
    return "unread" if value is None else str(value)


def limits_section(root=ROOT):
    """The NES limits section, from the files it names. Card t_cd5212b6, judge-panel fix 5.

    Every value here is read out of the module that enforces it, and every path is resolved against the
    tree, so the section is a measurement of this checkout and not a description of one.
    """
    frame_w = read_macro(root, ENGINE_LIMITS, "PP_FRAME_W")
    frame_h = read_macro(root, ENGINE_LIMITS, "PP_FRAME_H")
    arena_w = read_macro(root, ENGINE_LIMITS, "PP_ARENA_W")
    arena_h = read_macro(root, ENGINE_LIMITS, "PP_ARENA_H")
    marker = read_macro(root, ENGINE_LIMITS, "PP_MARKER_SIZE")
    cap = read_macro(root, ENGINE_LIMITS, "PP_ARENA_CAP_STEPS")
    tile = read_constant(root, CHECKER_ASSET, "TILE")
    area = read_constant(root, CHECKER_ASSET, "AREA")
    colours = read_constant(root, CHECKER_ASSET, "MAX_COLOURS_ON_SCREEN")
    bg_palettes = read_constant(root, CHECKER_FRAME, "MAX_BG_PALETTES")
    sprite_palettes = read_constant(root, CHECKER_FRAME, "MAX_SPRITE_PALETTES")
    per_line = read_constant(root, CHECKER_FRAME, "MAX_SPRITES_PER_LINE")
    oam = read_constant(root, CHECKER_FRAME, "MAX_SPRITES")

    return [
        "",
        "## NES limits, enforced in code",
        "",
        "The 8 bit look is a hardware budget, not a filter. The chip draws %s by %s pixels out of %s by %s "
        "pixel tiles and %s by %s pixel attribute areas, and shows at most %s colours at once. Every number "
        "below is read out of the file it names when this section is written, so the page cannot drift "
        "away from the code." % (_num(frame_w), _num(frame_h), _num(tile), _num(tile), _num(area),
                                 _num(area), _num(colours)),
        "",
        "What the engine enforces while the game runs:",
        "",
        "* %s holds the frame at PP_FRAME_W %s by PP_FRAME_H %s, the dodge arena at PP_ARENA_W %s by "
        "PP_ARENA_H %s, the %s pixel marker and the PP_ARENA_CAP_STEPS %s cap, and no magic number lives "
        "outside that file and `data/`."
        % (named(root, ENGINE_LIMITS), _num(frame_w), _num(frame_h), _num(arena_w), _num(arena_h),
           _num(marker), _num(cap)),
        "* %s resolves a colour role only inside the palette set the room declares. A role the set does not "
        "carry draws as PP_COLOUR_MISSING and is logged, because a fallback to the master palette would "
        "spend a colour past the 16 a screen may hold."
        % named(root, ENGINE_ROLE),
        "* %s turns a palette index into a drawing colour through %s and returns PP_COLOUR_MISSING for an "
        "index that is out of range, so a colour drawn at run time is a Ricoh 2C02 output and never a design "
        "colour." % (named(root, ENGINE_COLOUR), named(root, PALETTE_PPU)),
        "",
        "What the checkers prove, over the pixels:",
        "",
        "* %s checks one sheet or one layer: every pixel is an output of the chip, the image cuts into %s "
        "pixel tiles, a sprite tile carries 3 opaque colours, an attribute area carries 3 plus the shared "
        "backdrop, and the image stays at or under %s colours. It reads its palette from %s."
        % (named(root, CHECKER_ASSET), _num(tile), _num(colours), named(root, PALETTE_MASTER)),
        "* %s checks one finished 256 by 240 frame with both layers together: %s background palettes and %s "
        "sprite palettes as a set cover, %s sprites on any scanline, %s in OAM, %s colours."
        % (named(root, CHECKER_FRAME), _num(bg_palettes), _num(sprite_palettes), _num(per_line), _num(oam),
           _num(colours)),
        "* %s runs both over every art source and every 256 by 240 frame, and fails on a gated file. Its "
        "last run on this tree is the nes_audit_all row above." % named(root, CHECKER_ALL),
        "* %s covers what no picture can: the flat rectangles and glyphs the game draws at run time, resolved "
        "through the palette table above." % named(root, CHECKER_RUNTIME),
        "",
        "How to check it yourself:",
        "",
        "```sh",
        "python tools/check_data.py",
        "python tools/check_cleanroom.py",
        "python tools/nes_audit_all.py --quiet",
        "python tools/readme_badges.py --verify",
        "```",
        "",
        "Exit 0 means pass, and nothing else does. check_data holds every data file to its schema, its "
        "ranges and its references, and simulates every bullet recipe with the engine's own rules. "
        "check_cleanroom refuses a study path, a foreign name, a foreign phrase and a module with no review "
        "row in %s. Its one exemption is generated geography: a card such as %s carries OpenStreetMap road "
        "and water names, and only those name lists are exempt, on evidence inside the file, with the count "
        "printed on every run." % (named(root, CLEANROOM_REVIEW), named(root, GEOGRAPHY_CARD)),
    ]


def read_value(root, rel, name):
    """The right hand side of a module level assignment, or None. For the bridge's host, port and rung names.

    Limits are numbers, so read_macro and read_constant cover them with a digit pattern. The bridge
    states a string and a tuple as well, and the page quotes them, so this reader returns the value
    text with surrounding quotes stripped and leaves the type alone: a missing file or name answers
    None, which the caller prints as unread instead of guessing.
    """
    path = os.path.join(root, rel.replace("/", os.sep))
    pattern = re.compile(r"^%s\s*=\s*(.+?)\s*$" % re.escape(name))
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                match = pattern.match(line)
                if match:
                    return match.group(1).strip().strip("\"").strip("'")
    except OSError:
        return None
    return None


def read_names(root, rel, name):
    """The quoted strings inside one assignment, in order. The bridge's ladder is a tuple of rung names."""
    value = read_value(root, rel, name)
    if not value:
        return []
    return re.findall(r"\"([^\"]+)\"", value)


def bridge_section(root=ROOT):
    """The local AI bridge section, from the module it names. Judge-panel fix 5, 2026-11-14.

    The panel could not see a repository and marked technical depth down on a capture alone, so the
    page has to carry the service, its files and the commands that start it. Numbers and names are
    read from tools/ai_bridge.py; a path that has moved is printed as MISSING, so a broken section
    is a visible finding rather than a sentence that reads well and points nowhere.
    """
    host = read_value(root, BRIDGE_SERVER, "LOOPBACK_HOST") or "unread"
    port = read_value(root, BRIDGE_SERVER, "DEFAULT_PORT") or "unread"
    rungs = read_names(root, BRIDGE_SERVER, "SOURCES")
    rung_text = ", ".join(rungs) if rungs else "unread"
    return [
        "",
        "## The local AI bridge, in this repo",
        "",
        "The verdict in the TALK box comes from a service on this machine, and its wiring is in this "
        "tree rather than in a recording. Every path below is resolved against this checkout when this "
        "section is written:",
        "",
        "* %s is the whole server: Python standard library only, bound to `%s` on port %s, one deadline "
        "per request. Its ladder is tried in order, and every answer carries the rung that gave it, one "
        "of %s." % (named(root, BRIDGE_SERVER), host, port, rung_text),
        "* %s is the Meta rung: structured output against the schema built from the judge file, and no "
        "key means the rung is labelled unavailable and nothing is sent." % named(root, BRIDGE_META),
        "* %s holds the system text, the line limits, the verdict map and the local model id, so the "
        "model picks a word and the data file decides the WILL number." % named(root, BRIDGE_JUDGE),
        "* %s holds the recorded answers the replay rung serves, which is the path the demo plays with "
        "the network off." % named(root, BRIDGE_CACHE),
        "* %s makes the two real calls by hand and prints the rows the dialogue box would draw, and it "
        "refuses any host that is not loopback before it sends a byte." % named(root, BRIDGE_PROBE),
        "* %s starts the bridge, checks the data, builds the project, launches the game and stops the "
        "bridge when the window closes." % named(root, BRIDGE_BUILD),
        "* %s is the long page: the ladder rung by rung, what was measured on this PC, and what is not "
        "proven." % named(root, BRIDGE_DOC),
        "* %s is the picture review gate: a reviewer rejects a full colour frame and requires the "
        "palette and sprite limits above, and %s is the one command that runs it over a file."
        % (named(root, REVIEW_CHECKLIST), named(root, REVIEW_GATE)),
        "",
        "Build and start, from the repository root:",
        "",
        "```sh",
        "python tools/ai_bridge.py --selftest",
        "python tools/talk_scene_probe.py --offline",
        "python tools/ai_bridge.py --serve --warm",
        "powershell -NoProfile -ExecutionPolicy Bypass -File tools/run.ps1",
        "```",
        "",
        "`--selftest` prints one line per rung without spending a Meta call; `--offline` opens no socket "
        "at all; `--serve --warm` is the server the last line starts; and `tools/run.ps1` is the whole "
        "build, from the data checks through Igor to the running game. `PP_AI_MODE=replay` starts the "
        "ladder at the recorded rung, which is why the demo plays with no network and no model loaded.",
    ]


def build_block(results, root=ROOT):
    """The README region, from a run. Only what the run measured goes in it.

    Card t_f3399639: this region is the half of the page a gate owns, and tools/readme_meta.py masks
    it out of its body stamp, so the model that writes the sentences cannot drop the measurements
    and this tool cannot touch the sentences. Everything a test in tests/test_check_readme.py reads
    out of the page lives here: the four commands, the exempt run folder, and the tracked
    reference run with the timestamp its own answer carries.

    Card t_cd5212b6: the NES limits section reads the tree it is built against (the frame macros, the
    checker constants, the module paths), so the block is a statement about one root. Build it with
    the same root you verify or write, or the comparison measures a different tree than the page.
    """
    lines = [
        START,
        "",
        "## Checks on this tree",
        "",
        "These are the four commands the submission checklist tells a reader to run. No badge here is "
        "typed by hand: `python tools/readme_badges.py --write` runs every gate, renders one picture "
        "per gate from that run, and rewrites this section, and `--verify` refuses a page that "
        "disagrees with the tree. A red badge is a gate that is failing today, and it is left red on "
        "purpose.",
        "",
        "| gate | badge | command | result |",
        "| --- | --- | --- | --- |",
    ]
    for result in results:
        lines.append("| %s | ![%s](%s) | `%s` | %s |" % (
            result["label"], result["label"], badge_path(result["slug"]),
            result["command"], result["status"]))
    # The limits section sits under the table because the table is the verdict and the section is the
    # proof: a reader who doubts a row scrolls nine lines instead of leaving the page (card t_cd5212b6).
    lines += limits_section(root)
    # The bridge section follows the limits: the same page carries the service whose verdict the TALK
    # box shows, with the module read for its host and port (judge-panel fix 5, 2026-11-14).
    lines += bridge_section(root)
    lines += [
        "",
        "The reference Meta art run is the title backdrop. Its small files are tracked in `%s`, so a "
        "fresh clone holds the same evidence without running anything, and the same run is written to "
        "`%s`, a local folder git ignores, which is why that one path is exempt from the on disk "
        "check. The tracked answer in it, `%s`, says network true and was recorded %s."
        % (REFERENCE_DIR, RUN_DIR, REFERENCE_ANSWER, reference_recorded_at(root)),
        "",
        "The prose on this page is written by `muse-spark-1.3` through `tools/readme_meta.py`; the "
        "table above, the limits section, the bridge section and the badges are written by "
        "`python tools/readme_badges.py --write`. Each tool keeps out of the other's region of the file.",
        END,
    ]
    return "\n".join(lines)


def find_block(text):
    """The region between the markers, markers included, or None when either one is missing."""
    if START not in text or END not in text:
        return None
    start = text.index(START)
    end = text.index(END, start) + len(END)
    return text[start:end]


def parse_block(block):
    """Rows out of a block: label, command and the verdict the table claims."""
    rows = []
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("| ") or line.startswith("| gate ") or line.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        rows.append({"label": cells[0], "command": cells[2].strip("`"), "status": cells[3]})
    return rows


def replace_block(text, block):
    current = find_block(text)
    if current is None:
        return None
    return text.replace(current, block, 1)


def write_badges(results, root=ROOT):
    folder = os.path.join(root, BADGE_DIR.replace("/", os.sep))
    os.makedirs(folder, exist_ok=True)
    written = []
    for result in results:
        path = os.path.join(folder, result["slug"] + ".svg")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render_badge(result["label"], result["status"]))
        written.append(path)
    return written


def check_badges(results, root=ROOT):
    """Every badge file on disk must be the picture this run would draw."""
    problems = []
    for result in results:
        path = os.path.join(root, BADGE_DIR.replace("/", os.sep), result["slug"] + ".svg")
        if not os.path.exists(path):
            problems.append("%s is missing" % badge_path(result["slug"]))
            continue
        with open(path, encoding="utf-8") as fh:
            have = fh.read()
        want = render_badge(result["label"], result["status"])
        if have != want:
            problems.append("%s does not match this run" % badge_path(result["slug"]))
    return problems


def print_results(results):
    for result in results:
        print("   %-6s %-22s exit %-5s %6.1f s  %s" % (
            result["status"], result["label"],
            "none" if result["exit"] is None else str(result["exit"]),
            result["seconds"], result["command"]))
    passed = sum(1 for result in results if result["status"] == "PASS")
    print("readme_badges: %d gate(s), %d PASS, %d not PASS" % (len(results), passed, len(results) - passed))


def verify(root=ROOT, results=None, timeout=DEFAULT_TIMEOUT):
    path = os.path.join(root, "README.md")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    block = find_block(text)
    if block is None:
        print("readme_badges: README.md carries no %s / %s pair, so there is nothing to verify" % (START, END))
        return 1
    results = results if results is not None else run_all(root, timeout)
    problems = check_badges(results, root)
    want = build_block(results, root)
    have = block
    # Whole region, not just the table rows: the exempt run folder and the reference run pointer are
    # sentences inside the same region, and a stale one of those is the failure this tool exists for.
    if have.strip() != want.strip():
        print("readme_badges: the README block is stale")
        by_label = {row["label"]: row for row in parse_block(want)}
        for row in parse_block(have):
            current = by_label.get(row["label"])
            if current is None:
                print("   gone     %-22s the gate is no longer in the block" % row["label"])
            elif current["status"] != row["status"]:
                print("   %-8s %-22s README says %s, this run says %s" % (
                    "STALE", row["label"], row["status"], current["status"]))
        if parse_block(have) == parse_block(want):
            print("   the table's verdicts agree, so the text around it is what moved")
    for problem in problems:
        print("readme_badges: %s" % problem)
    if have.strip() != want.strip() or problems:
        return 1
    print("readme_badges: the README block and every badge match this run")
    return 0


def write(root=ROOT, results=None, timeout=DEFAULT_TIMEOUT):
    path = os.path.join(root, "README.md")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if find_block(text) is None:
        print("readme_badges: README.md has no %s / %s pair to replace; add the two markers first" % (START, END))
        return 1
    results = results if results is not None else run_all(root, timeout)
    for result in results:
        print("   %-6s %-22s exit %s" % (
            result["status"], result["label"], "none" if result["exit"] is None else result["exit"]))
    written = write_badges(results, root)
    updated = replace_block(text, build_block(results, root))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(updated)
    print("readme_badges: wrote %d badge file(s) and the README block" % len(written))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Rewrite the README badge block by rerunning its gates.")
    parser.add_argument("--root", default=ROOT, help="repository root (default: this file's parent)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="per gate, in seconds")
    parser.add_argument("--write", action="store_true", help="run the gates, write the badges and the block")
    parser.add_argument("--verify", action="store_true", help="run the gates and refuse a stale block")
    parser.add_argument("--list", action="store_true", help="print the gates and run nothing")
    args = parser.parse_args(argv)

    if args.list:
        for gate in GATES:
            print("   %-22s %s" % (gate["label"], command_text(gate)))
        return 0
    chosen = [flag for flag, on in (("write", args.write), ("verify", args.verify)) if on]
    if len(chosen) != 1:
        print("readme_badges: pass exactly one of --write, --verify or --list")
        return 2

    if args.write:
        return write(args.root, timeout=args.timeout)
    results = run_all(args.root, args.timeout)
    print_results(results)
    return verify(args.root, results=results)


if __name__ == "__main__":
    sys.exit(main())
