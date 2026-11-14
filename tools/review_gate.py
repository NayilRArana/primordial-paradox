#!/usr/bin/env python3
"""review_gate.py: the picture review gate, and the one command that stops a full colour frame.

Card t_d29d8161, judge-panel fix 5 of 2026-11-14. The panel marked technical depth down on an h264
capture alone, so the repository now carries the checklist a reviewer applies to any picture that
goes into this game (docs/REVIEW-CHECKLIST.md) and this tool, which is what makes the checklist a
gate instead of a paragraph. The rules are not restated here: the two checkers that already hold
every shipped asset and frame are imported and called, so a picture passes this gate exactly when it
passes `tools/nes_check.py` and `tools/nes_composite_check.py`.

What it refuses, in the panel's own words. A full colour frame is any picture whose pixels are not
PPU outputs, and that is R2: a photograph, a 32 bit screenshot with smoothing, or a capture whose
viewport was resampled all fail it, whatever they look like. On top of that it requires the palette
and sprite limits: 3 colours plus the backdrop per 16 by 16 area (R3), 4 background palettes (R4),
3 opaque colours per sprite tile (R5), 4 sprite palettes (R6), 8 sprites on a scanline and 64 in OAM
(R7), and 25 colours on screen (R8).

Three verdicts, and a skip is never one of them. PASS is the checker's own empty problem list;
REJECT carries every offending block, tile, sprite or colour the checker named; NOT MEASURED is a
rule that applies to this input but that this invocation cannot see. The sprite rules need to know
which pixels belong to sprites, which no photograph can say, so a frame without --sprite-mask or
--sprites leaves R5 to R7 NOT MEASURED and the gate exits 1. --no-sprites is the reviewer stating
on the record that the picture carries no sprites, and it is the only way those three pass without
evidence. NA is used only where the rule does not apply to the input at all (a background plate has
no sprites to count).

Usage
    python tools\\review_gate.py output\\title_run_1.png --no-sprites
    python tools\\review_gate.py frame.png --sprite-mask mask.png --sprite-height 16
    python tools\\review_gate.py frame.png --sprites sprites.json --json output\\review.json
    python tools\\review_gate.py game\\sprites_src\\percy\\spr_percy.png --type sprite
    python tools\\review_gate.py layer.png --type background --backdrop "#000000"

Exit codes: 0 every applicable rule passes, 1 a rule rejects or a rule that applies is not measured,
2 the picture or an argument cannot be read.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys

from PIL import Image

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
FRAME_W = 256
FRAME_H = 240

# The checklist, in the order a reviewer reads it. The ids are the ids docs/REVIEW-CHECKLIST.md uses,
# so the tool's output and the page a judge reads cannot drift apart.
RULES = (
    ("R1", "readable, on the 8 by 8 grid"),
    ("R2", "every pixel is a usable PPU colour (a full colour frame is refused)"),
    ("R3", "3 colours besides the backdrop in every 16 by 16 area"),
    ("R4", "4 background palettes in the frame"),
    ("R5", "3 opaque colours per sprite tile"),
    ("R6", "4 sprite palettes in the frame"),
    ("R7", "8 sprites on any scanline, 64 in OAM"),
    ("R8", "25 colours on screen"),
)

PASS = "PASS"
REJECT = "REJECT"
NOT_MEASURED = "NOT MEASURED"
NA = "NA"


def load_tool(name: str, filename: str):
    """The checker module itself, loaded by path the way tools/nes_audit_all.py loads it.

    A second copy of the pixel rules is exactly the failure this gate exists to prevent, so there is
    none: the rule text, the limits and the arithmetic all come from the shipped checker.
    """
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS, filename))
    if spec is None or spec.loader is None:
        raise ValueError("cannot load %s" % filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def classify(width: int, height: int, requested: str) -> str:
    """frame for a 256 by 240 picture or its 3x capture, else the layer kind the reviewer asked for.

    The 3x case is here because a window capture of this game is 768 by 720, and reading it as a
    background layer would judge the upscale instead of the frame: tools/nes_composite_check.py
    downsamples it by nearest, which is the only honest way back to the chip.
    """
    if requested != "auto":
        return requested
    if (width, height) in ((FRAME_W, FRAME_H), (FRAME_W * 3, FRAME_H * 3)):
        return "frame"
    return "background"


def row(rule_id: str, verdict: str, note: str, problems=None) -> dict:
    return {"id": rule_id, "verdict": verdict, "note": note, "problems": problems or []}


def not_measured(rule_id: str, why: str) -> dict:
    return row(rule_id, NOT_MEASURED, why)


def by_rule(problems, *names) -> list:
    return [problem for problem in problems if problem.get("rule") in names]


def verdict_for(problems, passed_note: str, rejected_note: str) -> dict:
    return row("", PASS if not problems else REJECT, passed_note if not problems else rejected_note,
               problems)


def frame_rows(picture: str, palette: dict, backdrop, mask, sprite_list, sprite_height: int,
               crop: str, no_sprites: bool, composite) -> dict:
    frame, info = composite.load_frame(picture, palette["allowed"], crop)
    sprites = None
    if mask or sprite_list:
        sprites = composite.load_sprites(frame, mask, sprite_list, sprite_height, crop=info)["sprites"]
    report = composite.check_frame(frame, palette, backdrop, sprites)
    cancelled = report["palette"]["problems"]
    background = report["background"]["problems"]
    screen = report["screen"]["problems"]
    sprite_problems = report["sprite"]["problems"] if "sprite" in report else []

    rows = [
        row("R1", PASS, "read %d by %d, which is the NES frame" % (frame.width, frame.height)),
        row("R2", PASS if not cancelled else REJECT,
            "every pixel is a PPU output" if not cancelled else
            "full colour frame: %d pixel(s) in %d colour(s) the PPU cannot output"
            % (report["palette"]["off_palette_pixels"], report["palette"]["off_palette_colours"]),
            cancelled),
        verdict_for(by_rule(background, "background_area"),
                    "every 16 by 16 area carries 3 colours besides the backdrop",
                    "a 16 by 16 area carries more than 3 colours besides the backdrop"),
        verdict_for(by_rule(background, "background_palettes"),
                    "the frame's areas fit 4 background palettes",
                    "the frame needs more than 4 background palettes"),
        verdict_for(by_rule(sprite_problems, "sprite_colours"),
                    "every sprite carries 3 colours plus transparency",
                    "a sprite carries more than 3 opaque colours"),
        verdict_for(by_rule(sprite_problems, "sprite_palettes"),
                    "the frame's sprites fit 4 sprite palettes",
                    "the frame needs more than 4 sprite palettes"),
        verdict_for(by_rule(sprite_problems, "sprites_per_scanline", "sprite_count"),
                    "no scanline carries more than 8 sprites and OAM holds at most 64",
                    "a scanline or OAM is over the sprite budget"),
        verdict_for(by_rule(screen, "screen_colours"),
                    "the frame shows at most 25 colours",
                    "the frame shows more than 25 colours"),
    ]
    rows = [row(RULES[index][0], item["verdict"], item["note"], item["problems"])
            for index, item in enumerate(rows)]
    if sprites is None:
        why = ("reviewer states the picture carries no sprites" if no_sprites else
               "no sprite evidence: pass --sprite-mask or --sprites, or --no-sprites to claim none")
        state = PASS if no_sprites else NOT_MEASURED
        rows[4] = row("R5", state, why)
        rows[5] = row("R6", state, why)
        rows[6] = row("R7", state, why)
    return {"path": picture, "kind": "frame", "size": [frame.width, frame.height], "rows": rows,
            "report": report, "frame": info}


def asset_rows(picture: str, kind: str, palette: dict, backdrop, checker) -> dict:
    image = checker.load_image(picture)
    report = checker.check(image, kind, palette, backdrop)
    problems = report["problems"]

    if kind == "sprite":
        rows = [
            row("R1", PASS if not by_rule(problems, "grid") else REJECT,
                "on the 8 by 8 grid" if not by_rule(problems, "grid") else "the image is not a multiple of 8",
                by_rule(problems, "grid")),
            row("R2", PASS if not by_rule(problems, "palette") else REJECT,
                "every pixel is a PPU output" if not by_rule(problems, "palette") else
                "full colour layer: %d colour(s) the PPU cannot output"
                % len(by_rule(problems, "palette")),
                by_rule(problems, "palette")),
            row("R3", NA, "a sprite sheet is judged by tile, not by 16 by 16 area"),
            row("R4", NA, "a layer does not decide the background palettes; the composed frame does"),
            verdict_for(by_rule(problems, "sprite_tile"),
                        "every 8 by 8 sprite tile carries 3 colours plus transparency",
                        "a sprite tile carries more than 3 colours"),
            row("R6", NA, "a sheet is not a frame: which sprite uses which group is settled on the frame"),
            row("R7", NA, "a sheet is not a frame: sprite placement is settled on the frame"),
            verdict_for(by_rule(problems, "screen_colours"),
                        "the image shows at most 25 colours",
                        "the image shows more than 25 colours"),
        ]
    else:
        rows = [
            row("R1", PASS if not by_rule(problems, "grid") else REJECT,
                "on the 8 by 8 grid" if not by_rule(problems, "grid") else "the image is not a multiple of 8",
                by_rule(problems, "grid")),
            row("R2", PASS if not by_rule(problems, "palette") else REJECT,
                "every pixel is a PPU output" if not by_rule(problems, "palette") else
                "full colour layer: %d colour(s) the PPU cannot output"
                % len(by_rule(problems, "palette")),
                by_rule(problems, "palette")),
            verdict_for(by_rule(problems, "background_area"),
                        "every 16 by 16 area carries 3 colours besides the backdrop",
                        "a 16 by 16 area carries more than 3 colours besides the backdrop"),
            row("R4", NA, "a single layer does not decide the 4; the composed frame does"),
            row("R5", NA, "a background plate carries no sprite tiles"),
            row("R6", NA, "a background plate carries no sprites"),
            row("R7", NA, "a background plate carries no sprites"),
            verdict_for(by_rule(problems, "screen_colours"),
                        "the image shows at most 25 colours",
                        "the image shows more than 25 colours"),
        ]
    rows = [row(RULES[index][0], item["verdict"], item["note"], item["problems"])
            for index, item in enumerate(rows)]
    return {"path": picture, "kind": kind, "size": [image.width, image.height], "rows": rows,
            "report": report}


def gate(path: str, kind: str = "auto", backdrop=None, mask=None, sprite_list=None,
         sprite_height: int = 16, crop: str = "auto", no_sprites: bool = False) -> dict:
    """Run the checklist over one picture and answer with a row per rule."""
    composite = load_tool("nes_composite_check_gate", "nes_composite_check.py")
    checker = load_tool("nes_check_gate", "nes_check.py")
    palette = composite.load_palette(composite.default_palette_path(ROOT))
    with open(os.path.join(ROOT, "data", "nes_palette.json"), encoding="utf-8-sig") as handle:
        palette["entries"] = json.load(handle).get("entries")
    with Image.open(path) as picture:
        width, height = picture.size
    chosen = classify(width, height, kind)
    if chosen == "frame":
        result = frame_rows(path, palette, backdrop, mask, sprite_list, sprite_height, crop,
                            no_sprites, composite)
    elif chosen in ("sprite", "background"):
        result = asset_rows(path, chosen, palette, backdrop, checker)
    else:
        raise ValueError("%s is not a kind this gate checks" % chosen)
    result["verdict"] = overall(result["rows"])
    return result


def overall(rows) -> str:
    """The picture's verdict: a reject beats a skip, and a skip is not a pass."""
    if any(item["verdict"] == REJECT for item in rows):
        return REJECT
    if any(item["verdict"] == NOT_MEASURED for item in rows):
        return NOT_MEASURED
    return PASS


def describe(result: dict, limit: int = 8) -> list:
    lines = ["review_gate: %s  (%s, %d by %d)" % (result["path"], result["kind"],
                                                 result["size"][0], result["size"][1])]
    for item in result["rows"]:
        lines.append("  %-2s %-12s %s" % (item["id"], item["verdict"], item["note"]))
        # A real capture fails R2 in thousands of colours: printing every one buries the rule that
        # mattered, so the console shows the worst eight and the count, and --json keeps all of them.
        for problem in item["problems"][:limit]:
            where = ""
            for key in ("block", "area", "tile", "box"):
                if key in problem:
                    where = " %s %s" % (key, problem[key])
                    break
            lines.append("      [%s]%s %s" % (problem.get("rule", "?"), where,
                                             problem.get("detail", "")))
        hidden = len(item["problems"]) - limit
        if hidden > 0:
            lines.append("      ... %d more %s problem(s); --json keeps every one" % (hidden, item["id"]))
    refused = [item["id"] for item in result["rows"] if item["verdict"] == REJECT]
    skipped = [item["id"] for item in result["rows"] if item["verdict"] == NOT_MEASURED]
    if result["verdict"] == PASS:
        lines.append("review_gate: PASS, every rule that applies to this picture passed")
    elif refused:
        lines.append("review_gate: REJECT, %d rule(s) failed: %s" % (len(refused), ", ".join(refused)))
    else:
        lines.append("review_gate: NOT MEASURED, %s was not measured" % ", ".join(skipped))
    return lines


def unreadable_frame(picture: str, error) -> list | None:
    """A picture that holds no legal viewport is a reject, not an unreadable file.

    find_viewport refuses to guess (tools/nes_composite_check.py): if no 768 by 720 box inside the
    picture is at least 90 percent PPU colours, the picture is not a frame of this game. A still cut
    from an h264 capture and resampled is exactly that, so it is reported at R2 rather than as "cannot
    read". Exit 2 stays for a file that cannot be opened or an argument that cannot be parsed.
    """
    text = str(error)
    if "no 3x viewport found" not in text:
        return None
    return [
        "review_gate: %s  (frame)" % picture,
        "  R1 PASS         the file was read",
        "  R2 REJECT       full colour frame: %s" % text,
        "review_gate: REJECT, R2 failed: no part of this picture is a frame the chip could draw",
    ]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="The picture review gate: reject a full colour frame and "
                                                 "require the palette and sprite limits.")
    parser.add_argument("picture", help="the picture to judge: a 256x240 frame, a sprite sheet or a layer")
    parser.add_argument("--type", default="auto", choices=("auto", "frame", "sprite", "background"),
                        help="auto: a 256 by 240 picture is a frame, anything else a background layer")
    parser.add_argument("--backdrop", default=None, help="the shared backdrop colour, #RRGGBB or $0F or 15")
    parser.add_argument("--crop", default="auto", help="auto, 1, 3, or x,y: where the viewport sits in a capture")
    parser.add_argument("--sprite-mask", default=None, help="PNG whose non transparent pixels belong to sprites")
    parser.add_argument("--sprites", dest="sprite_list", default=None,
                        help='JSON list of sprite rectangles: [{"x":0,"y":0,"w":8,"h":16}]')
    parser.add_argument("--sprite-height", type=int, default=16, choices=(8, 16),
                        help="sprite height for mask grouping; 8x16 is one OAM entry, not two")
    parser.add_argument("--no-sprites", action="store_true",
                        help="the reviewer states this picture carries no sprites, so R5 to R7 pass")
    parser.add_argument("--json", dest="json_path", default=None, help="write the gate's report as JSON")
    parser.add_argument("--quiet", action="store_true", help="print only a picture that does not pass")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.picture):
        print("review_gate: no such picture: %s" % args.picture, file=sys.stderr)
        return 2
    try:
        result = gate(args.picture, args.type, None, args.sprite_mask, args.sprite_list,
                      args.sprite_height, args.crop, args.no_sprites)
    except (ValueError, OSError, KeyError, SystemExit) as error:
        refused = unreadable_frame(args.picture, error)
        if refused is None:
            print("review_gate: cannot judge this picture: %s" % error, file=sys.stderr)
            return 2
        for line in refused:
            print(line)
        return 1

    lines = describe(result)
    if not args.quiet or result["verdict"] != PASS:
        for line in lines:
            print(line)
    if args.json_path:
        record = {key: value for key, value in result.items() if key != "report"}
        record["checker_problems"] = result["report"].get("problems", [])
        with open(args.json_path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(record, handle, indent=2, default=str)
            handle.write("\n")
    return 0 if result["verdict"] == PASS else 1


if __name__ == "__main__":
    sys.exit(main())
