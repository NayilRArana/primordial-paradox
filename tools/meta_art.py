#!/usr/bin/env python3
"""meta_art.py: Muse Image concept, SAM 3.1 cut, then the project's own NES conversion and gates.

Card META-ART-1. The concept art for the slice has come from a painted lane and from SDXL on Kaggle;
the Meta image path was mocked. This tool is the Meta path, end to end, and it is deliberately thin:

  1. REQUEST. tools/meta_client.py asks Muse Image for one concept at the documented size (`size` sets
     an aspect ratio on the real API, not exact pixels), through the client's cache, so a live call is
     recorded in data/ai_cache with network true and replays with the wifi off.
  2. CUT. tools/meta_client.py asks SAM 3.1 for one noun phrase on that concept. The SAM token grammar
     is not in the docs we hold, so the answer is kept verbatim and a silhouette is written ONLY when
     the answer carried a box. No box means no cut, and the evidence says "no geometry", never a
     silhouette drawn from a guess.
  3. CONVERT. The concept is fitted to 256x240 and quantised by tools/quantize_concept.py against the
     asset's own scene set, per 16x16 area, which is the only mapping a 2C02 can draw.
  4. GATE. tools/nes_check.py, tools/palette_synergy.py and tools/nes_audit_all.py run against that one
     file and their exit codes and last lines are recorded. None of their rules is restated here.
  5. EVIDENCE. output/meta_art/<asset>/<candidate>/ holds request.json (the exact payload, no key),
     cached_response.json (the cache entry), sam_mask.json, concept.png, cut.png, frame.png, the NES
     PNG and the comparison sheet; output/meta_art/<asset>_sheet.png is the side by side.

Style. Nayil picked direction B, LATE NES POLISH, on 2026-10-26 19:00, so every prompt below asks for
that treatment in the words knowledge/ART-STYLE.md section 4 uses for it: bold outlines, three tone
shading lit from the top left, detailed 16x16 tiles, restricted palette. A, C and the earlier style
sweep were dropped by the same decision; this tool renders B only.

Nothing is installed anywhere: no asset in the game tree is replaced by this tool. A shipped asset
changes only when Nayil picks one, per the card.

Where the spend is recorded, and why not in knowledge/META-SPEND.md
---------------------------------------------------------------
knowledge/META-SPEND.md is REWRITTEN from data/ai_cache by tools/meta_spend_ledger.py (card
t_5031b766), so a line appended to it by this tool would be erased on that page's next build. Every
call this tool makes is a live cache entry, so the ledger already prices it on its own page, which is
the single place the card's spend is read from. This tool therefore keeps its own run log beside the
run's evidence, at <out>/spend_log.md (output/meta_art/spend_log.md by default), and prices each row
from the documented list prices that tools/meta_spend_ledger.py already carries, so there is one price
source and no second guess:

    muse-image-1.0   0.01 USD per generated image, flat
    sam-3.1          0.0025 USD per segmentation call

A price is written as MEASURED when the response itself reported a cost field, and as LIST when it
came from those two constants; a row never carries a number nobody published.

Budget. --budget defaults to this card's 25.00 USD ceiling. Before anything is sent, the projected
cost of the plan (images plus segments at list price) is compared with it, and a plan over the
ceiling is refused with nothing sent. --max-calls is the same guard in calls, not dollars.

Usage
    python tools\\meta_art.py --dry-run
    python tools\\meta_art.py --budget-report
    python tools\\meta_art.py --assets title_backdrop --seeds 1
    python tools\\meta_art.py --seeds 6                six candidates per asset, for the pick
    PP_AI_BACKEND=mock python tools\\meta_art.py       offline proof of the chain

Exit 0 when every gate passed for every candidate; 1 when any gate failed or any delivery was refused;
2 on a bad argument or a plan over budget; 3 when the Meta key is missing (nothing was sent).
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "art"))

import meta_client  # noqa: E402
import quantize_concept  # noqa: E402
import nes_audit_all  # noqa: E402
import palette_synergy  # noqa: E402
import scene_palette_set  # noqa: E402
import meta_spend_ledger  # noqa: E402

try:
    from PIL import Image, ImageDraw
except ImportError as exc:  # pragma: no cover - PIL is a project dependency
    raise SystemExit("meta_art: Pillow is required: %s" % exc)

OUT = os.path.join(ROOT, "output", "meta_art")
SPEND_NAME = "spend_log.md"
FRAME_W, FRAME_H = 256, 240
DEFAULT_SIZE = "1024x1024"
CARD = "t_9332fe42"

# Direction B, late NES polish, from knowledge/ART-STYLE.md section 4. One string so the prompt and
# the evidence cannot drift apart.
STYLE = "B"
STYLE_WORDS = ("late NES era 8 bit art, bold black 1 pixel outlines on every form, "
               "three tone shading lit from the top left, detailed tiles on a 16x16 grid, "
               "restricted palette of about fourteen colours")

# The three slice assets where a Meta concept changes what a judge sees most (card body). `scene` is a
# real scene id in data/scene_palettes.json, checked by scene_palette_set at run time.
ASSETS = {
    "title_backdrop": {
        "scene": "title",
        "noun": "the temple",
        "subject": "Zeus and Kronos on the title screen",
        "prompt": ("NES style title screen backdrop for a 1989 adventure about two Greek houses, "
                   "a marble temple front with cracked columns at night, a low mountain ridge behind "
                   "it, deep indigo sky, %s, cold grey stone against black, strong readable "
                   "silhouette, no text, no logo, no characters" % STYLE_WORDS),
    },
    "quay_night": {
        "scene": "battle_quay_dusk",
        "noun": "the ship at the quay",
        "subject": "the ship waiting at the quay",
        "prompt": ("NES style background for a 1989 adventure, a cargo ship tied up at a stone quay at "
                   "night, sodium lamp on a bollard, wet cobbles, black water, %s, no text, "
                   "no characters" % STYLE_WORDS),
    },
    "ship_deck": {
        "scene": "battle_deck_night",
        "noun": "the deck",
        "subject": "the ship deck at night",
        "prompt": ("NES style background for a 1989 adventure, the open deck of a cargo ship at night, "
                   "railing and hatch and a coil of rope, one mast, dark sea behind, plank and "
                   "plate detail on the tile grid, %s, no text, no characters" % STYLE_WORDS),
    },
}


# --------------------------------------------------------------------------- small helpers

def stamp():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def shown(path):
    try:
        return os.path.relpath(path, ROOT).replace(os.sep, "/")
    except ValueError:
        return path


def ensure(path):
    os.makedirs(path, exist_ok=True)
    return path


def fit_frame(path, target):
    """256x240 nearest neighbour: the frame the 2C02 can actually draw, from whatever the model sent."""
    with Image.open(path) as handle:
        image = handle.convert("RGB")
    if image.size != (FRAME_W, FRAME_H):
        image = image.resize((FRAME_W, FRAME_H), Image.NEAREST)
    image.save(target, "PNG")
    return target


def cut_from_box(concept_path, boxes, out_path):
    """Silhouette from the first box SAM reported, or None when it reported no box.

    The box is in the concept's own pixels (the docs say source pixels). Anything outside it is made
    transparent. This is a rectangle cut, not a pixel accurate matte, and the evidence says so.
    """
    if not boxes:
        return None, "no box in the SAM answer, so no silhouette was written"
    with Image.open(concept_path) as handle:
        image = handle.convert("RGBA")
    width, height = image.size
    left, top, right, bottom = boxes[0]
    left, top = max(0, int(left)), max(0, int(top))
    right, bottom = min(width, int(right)), min(height, int(bottom))
    if right <= left or bottom <= top:
        return None, "the SAM box %s is empty or inverted at %dx%d" % (boxes[0], width, height)
    pixels = image.load()
    kept = 0
    for y in range(height):
        for x in range(width):
            if left <= x < right and top <= y < bottom:
                kept += 1
                continue
            r, g, b, _ = pixels[x, y]
            pixels[x, y] = (r, g, b, 0)
    image.save(out_path, "PNG")
    share = 100.0 * kept / float(width * height)
    return out_path, "rectangle cut on box %s: %.1f percent of the concept kept" % (
        [left, top, right, bottom], share)


def run_gate(argv, name):
    """One gate as a subprocess: its exit code and its last lines, never a summary of them."""
    try:
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=900)
        output = (result.stdout or "") + (result.stderr or "")
        lines = [line for line in output.strip().splitlines() if line.strip()][-4:]
        return {"gate": name, "argv": argv, "exit_code": result.returncode, "tail": lines,
                "passed": result.returncode == 0}
    except (OSError, subprocess.SubprocessError) as exc:
        # A gate that could not be run is UNKNOWN, which is not a pass.
        return {"gate": name, "argv": argv, "exit_code": None, "tail": [str(exc)],
                "passed": False}
        # noqa note: the branch records the failure instead of swallowing it (the clean code gate).


def gate_palette_synergy(nes_path, scene_id):
    """The background half of palette_synergy, called in process.

    The CLI needs a background AND a sprite, because it judges a composite frame; a concept backdrop has
    no sprite yet, so the background rules (3 colours per 16x16 area, at most 4 palettes for the frame,
    every colour a member of the 2C02 set) are asked for directly and their own problem list is kept.
    """
    try:
        grid = palette_synergy.Grid(ROOT)
        scene = scene_palette_set.scene(ROOT, scene_id)
        with Image.open(nes_path) as handle:
            problems = palette_synergy.background_report(grid, scene, handle.convert("RGBA"))
        tail = ["%s: %s" % (problem.get("rule"), problem.get("detail")) for problem in problems[:4]]
        return {"gate": "palette_synergy (background_report)", "exit_code": 0 if not problems else 1,
                "tail": tail or ["no background problem: 3 colours per area, <=4 palettes, all 2C02 members"],
                "problems": len(problems), "passed": not problems}
    except (OSError, ValueError, SystemExit) as exc:
        return {"gate": "palette_synergy (background_report)", "exit_code": None, "tail": [str(exc)],
                "problems": None, "passed": False}


def gate_nes_audit(nes_path):
    """nes_audit_all's own per-file record, called in process.

    The CLI only discovers files under game/sprites_src and output/*preview*.png, so a candidate under
    output/meta_art is invisible to it. Its Target plus audit_one() is the same code the CLI runs for one
    file, with the same checkers and the same palette, and it writes nothing to the shared page.
    """
    try:
        check_mod = nes_audit_all.load_module("meta_art_nes_check",
                                              os.path.join(HERE, "nes_check.py"))
        composite = nes_audit_all.load_module("meta_art_composite",
                                              os.path.join(HERE, "nes_composite_check.py"))
        palette = composite.load_palette(composite.default_palette_path(ROOT))
        rel = shown(nes_path)
        target = nes_audit_all.Target(rel, "meta_art", "frame", True, 1,
                                      "a finished 256x240 frame written by tools/meta_art.py")
        record = nes_audit_all.audit_one(ROOT, target, check_mod, composite, palette)
        ok = bool(record.get("ok")) and not record.get("unmeasured")
        tail = ["%s: %d problem(s) %s" % (record.get("checker"), record.get("problem_count"),
                                         record.get("rules"))]
        if record.get("unmeasured"):
            tail.append("UNMEASURED: %s" % record["unmeasured"])
        return {"gate": "nes_audit_all (audit_one)", "exit_code": 0 if ok else 1, "tail": tail,
                "problems": record.get("problem_count"), "passed": ok}
    except (OSError, ValueError, SystemExit, AttributeError) as exc:
        return {"gate": "nes_audit_all (audit_one)", "exit_code": None, "tail": [str(exc)],
                "problems": None, "passed": False}


def build_sheet(panels, out_path, title):
    """Side by side: concept, cut, NES frame, each captioned. Same width, so the eye compares like with like."""
    scale = 2
    height = FRAME_H * scale
    rendered = []
    for label, path in panels:
        if path and os.path.exists(path):
            with Image.open(path) as handle:
                panel = handle.convert("RGB")
            if panel.size != (FRAME_W, FRAME_H):
                panel = panel.resize((FRAME_W, FRAME_H), Image.NEAREST)
            panel = panel.resize((FRAME_W * scale, height), Image.NEAREST)
        else:
            # A missing panel is drawn as flat black with its label, so the sheet never hides a gap.
            panel = Image.new("RGB", (FRAME_W * scale, height), (10, 10, 10))
        rendered.append((label, panel))
    pad = 8
    width = sum(p.width for _, p in rendered) + pad * (len(rendered) + 1)
    sheet = Image.new("RGB", (width, height + 28), (18, 18, 18))
    draw = ImageDraw.Draw(sheet)
    draw.text((pad, 6), title, fill=(240, 240, 240))
    x = pad
    for label, panel in rendered:
        sheet.paste(panel, (x, 24))
        draw.text((x + 4, 26), label, fill=(255, 220, 90))
        x += panel.width + pad
    ensure(os.path.dirname(out_path))
    sheet.save(out_path, "PNG")
    return out_path


# --------------------------------------------------------------------------- spend

def spend_usage(usage):
    """The cost numbers a response actually reported, or empty when it reported none."""
    if not isinstance(usage, dict):
        return {}
    out = {}
    for key in ("cost", "cost_usd", "total_cost", "price", "price_usd", "credits"):
        if isinstance(usage.get(key), (int, float)):
            out[key] = usage[key]
    return out


def append_spend(rows, spend_path):
    """Append one table block to the spend log inside the run's own output folder. Append only."""
    if not rows:
        return None
    if not os.path.exists(spend_path):
        ensure(os.path.dirname(spend_path))
        with open(spend_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("# Meta art spend, this tool's own log (card %s)\n\n"
                         "One row per image and segment call, written as the call returns. knowledge/"
                         "META-SPEND.md is generated from data/ai_cache by tools/meta_spend_ledger.py "
                         "and already prices every live entry here, so that page is the total and this "
                         "one is the per candidate trail. MEASURED means the response reported a cost; "
                         "LIST means it did not, and the documented list price was applied.\n\n"
                         "| when | card | kind | model | backend | network | candidate | cost | basis | notes |\n"
                         "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n" % CARD)
    with open(spend_path, "a", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |\n" % (
                row["when"], row["card"], row["kind"], row["model"], row["backend"],
                row["network"], row["candidate"], row["cost"], row["basis"], row["notes"]))
    return spend_path


def spend_line(kind, model, result, candidate):
    usage = result.get("usage") or {}
    cost = spend_usage(usage)
    basis = "MEASURED"
    if not cost and kind == "image":
        cost = {"cost_usd": meta_spend_ledger.PER_IMAGE}
        basis = "LIST"
    if not cost and kind == "segment":
        cost = {"cost_usd": meta_spend_ledger.PER_SEGMENT}
        basis = "LIST"
    notes = "response usage keys: %s" % (", ".join(sorted(usage)) or "none")
    if cost:
        amount = ", ".join("%s=%s" % (k, v) for k, v in sorted(cost.items()))
    else:
        amount = "UNKNOWN"
        basis = "NONE"
    return {"when": stamp(), "card": os.environ.get("HERMES_KANBAN_TASK", CARD),
            "kind": kind, "model": model, "backend": result.get("backend", "?"),
            "network": str(meta_client.network_used(result.get("backend", ""),
                                                   result.get("mode", ""),
                                                   bool(result.get("cached")))),
            "candidate": candidate, "cost": amount, "basis": basis, "notes": notes}


# --------------------------------------------------------------------------- the run

def one_candidate(asset, candidate_tag, args):
    """Everything for one concept: request, cache, cut, convert, gates, sheets, evidence row."""
    spec = ASSETS[asset]
    folder = ensure(os.path.join(args.out, asset, candidate_tag))
    record = {"asset": asset, "candidate": candidate_tag, "when": stamp(), "scene": spec["scene"],
              "style": STYLE, "prompt": spec["prompt"], "size": args.size, "steps": {},
              "spend": [], "problems": []}

    concept = os.path.join(folder, "concept.png")
    try:
        image = meta_client.generate_image(spec["prompt"], size=args.size, out_path=concept)
    except meta_client.MetaKeyMissing as exc:
        record["problems"].append("no key: %s" % exc)
        return record, "no-key"
    except meta_client.MetaError as exc:
        record["problems"].append("image call failed: %s" % exc)
        return record, "image-failed"

    record["steps"]["image"] = {
        "model": image.get("model"), "backend": image.get("backend"), "mode": image.get("mode"),
        "cached": image.get("cached"), "path": shown(concept),
        "reported_width": image.get("width"), "reported_height": image.get("height"),
        "revised_prompt": image.get("revised_prompt"),
    }
    record["spend"].append(spend_line("image", image.get("model", "?"), image, candidate_tag))
    if image.get("backend") == "meta" and image.get("mode") == "record":
        record["steps"]["image"]["network"] = True

    # The cache entry this call wrote: same key arithmetic as the client, so the evidence names a file
    # that exists. Recomputed rather than guessed, and marked as recomputed.
    payload = {"model": image.get("model"), "prompt": spec["prompt"], "size": args.size, "n": 1,
               "output_format": "png"}
    key = meta_client.request_key("image", image.get("model"), payload, extra=str(image.get("backend")))
    entry_path = meta_client.cache_path(key)
    if os.path.exists(entry_path):
        shutil.copyfile(entry_path, os.path.join(folder, "cached_response.json"))
        record["steps"]["image"]["cache_entry"] = shown(entry_path)
        record["steps"]["image"]["cache_copied_to"] = shown(os.path.join(folder, "cached_response.json"))
        try:
            with open(entry_path, "r", encoding="utf-8") as handle:
                record["steps"]["image"]["cache_network"] = bool(json.load(handle).get("network"))
        except (OSError, ValueError) as exc:
            record["problems"].append("cache entry unreadable: %s" % exc)
    else:
        record["problems"].append("no cache entry at %s (mode %s)" % (shown(entry_path),
                                                                     image.get("mode")))

    with open(os.path.join(folder, "request.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")

    # SAM 3.1
    try:
        segmentation = meta_client.segment(concept, spec["noun"])
        record["steps"]["segment"] = {
            "model": segmentation.get("model"), "noun": spec["noun"],
            "boxes": segmentation.get("boxes"), "masks_found": len(segmentation.get("masks") or []),
            "text": (segmentation.get("text") or "")[:2000],
            "note": segmentation.get("note"), "backend": segmentation.get("backend"),
            "mode": segmentation.get("mode"), "cached": segmentation.get("cached"),
        }
        record["spend"].append(spend_line("segment", segmentation.get("model", "?"),
                                          segmentation, candidate_tag))
        with open(os.path.join(folder, "sam_mask.json"), "w", encoding="utf-8", newline="\n") as handle:
            json.dump({k: v for k, v in segmentation.items() if k != "image_b64"}, handle, indent=2,
                      sort_keys=True)
            handle.write("\n")
        cut, why = cut_from_box(concept, segmentation.get("boxes") or [],
                                os.path.join(folder, "cut.png"))
        record["steps"]["cut"] = {"path": shown(cut) if cut else None, "why": why}
    except meta_client.MetaError as exc:
        record["problems"].append("segment call failed: %s" % exc)
        record["steps"]["cut"] = {"path": None, "why": "segment failed"}

    # Convert and gate
    frame = fit_frame(concept, os.path.join(folder, "frame.png"))
    try:
        stats = quantize_concept.convert(ROOT, frame, spec["scene"], max_delta_e=args.max_delta_e)
        record["steps"]["convert"] = {k: stats.get(k) for k in
                                      ("scene", "mean_delta_e", "max_delta_e", "changed_percent",
                                       "colours_before", "colours_after", "allowed_entries",
                                       "free_mean_delta_e", "accepted", "out", "sheet")}
    except (SystemExit, OSError, ValueError) as exc:
        record["problems"].append("convert failed: %s" % exc)
        return record, "convert-failed"

    nes_path = os.path.join(ROOT, stats["out"]) if not os.path.isabs(stats["out"]) else stats["out"]
    if not os.path.exists(nes_path):
        nes_path = os.path.join(folder, "frame_nes.png")
    backdrop = "$%02X" % _scene_backdrop(spec["scene"])
    gates = [
        run_gate([sys.executable, os.path.join(HERE, "nes_check.py"), nes_path, "--type", "background",
                  "--backdrop", backdrop], "nes_check"),
        gate_palette_synergy(nes_path, spec["scene"]),
        gate_nes_audit(nes_path),
    ]
    record["steps"]["gates"] = gates
    failed = [gate["gate"] for gate in gates if not gate["passed"]]
    if failed:
        record["problems"].append("gates failed: %s" % ", ".join(failed))

    sheet = build_sheet([("concept (Muse Image)", concept),
                         ("SAM cut" if record["steps"]["cut"]["path"] else "SAM cut: none",
                          record["steps"]["cut"]["path"]),
                         ("NES frame, style %s" % STYLE, nes_path)],
                        os.path.join(folder, "comparison.png"),
                        "%s / %s / scene %s / style %s" % (asset, candidate_tag, spec["scene"], STYLE))
    record["steps"]["comparison"] = shown(sheet)
    with open(os.path.join(folder, "evidence.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(record, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return record, ("ok" if not failed else "gate-failed")


def _scene_backdrop(scene_id):
    return scene_palette_set.scene(ROOT, scene_id).backdrop


def projected_cost(concepts):
    """Documented list price for the plan: one image and one segment per concept."""
    return concepts * (meta_spend_ledger.PER_IMAGE + meta_spend_ledger.PER_SEGMENT)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Muse Image plus SAM 3.1 into the NES gates (META-ART-1).")
    parser.add_argument("--assets", default=",".join(ASSETS),
                        help="comma separated: %s" % ", ".join(ASSETS))
    parser.add_argument("--seeds", type=int, default=1, help="candidates per asset (1 to 8)")
    parser.add_argument("--candidates", default="", help="explicit tags, e.g. c1,c2 (overrides --seeds)")
    parser.add_argument("--size", default=DEFAULT_SIZE, help="the size sent to the API (aspect ratio)")
    parser.add_argument("--max-delta-e", type=float, default=quantize_concept.DEFAULT_MAX_DELTA_E)
    parser.add_argument("--max-calls", type=int, default=24,
                        help="hard ceiling on live image plus segment calls for this run")
    parser.add_argument("--budget", type=float, default=25.0,
                        help="USD ceiling for this run, at the documented list prices")
    parser.add_argument("--out", default=OUT)
    parser.add_argument("--dry-run", action="store_true", help="print the plan, the price and the key state only")
    parser.add_argument("--budget-report", action="store_true", help="what this tool's spend log holds so far")
    args = parser.parse_args(argv)

    assets = [name.strip() for name in args.assets.split(",") if name.strip()]
    unknown = [name for name in assets if name not in ASSETS]
    if unknown:
        print("meta_art: unknown asset(s) %s; known: %s" % (", ".join(unknown), ", ".join(ASSETS)))
        return 2
    if not 1 <= args.seeds <= 8:
        print("meta_art: --seeds must be 1 to 8")
        return 2
    tags = [t.strip() for t in args.candidates.split(",") if t.strip()] or \
           ["c%d" % (index + 1) for index in range(args.seeds)]

    spend_path = os.path.join(args.out, SPEND_NAME)
    if args.budget_report:
        if not os.path.exists(spend_path):
            print("meta_art: no spend log at %s (no call has been made by this tool)"
                  % shown(spend_path))
            return 0
        with open(spend_path, "r", encoding="utf-8") as handle:
            rows = [line for line in handle if line.startswith("| ") and "---" not in line][1:]
        unknown_cost = sum(1 for line in rows if "UNKNOWN" in line)
        print("meta_art: %d spend row(s) in %s, %d with cost UNKNOWN"
              % (len(rows), shown(spend_path), unknown_cost))
        print("meta_art: knowledge/META-SPEND.md is the total and is generated by "
              "tools/meta_spend_ledger.py from data/ai_cache")
        return 0

    concepts = len(assets) * len(tags)
    planned = concepts * 2
    projected = projected_cost(concepts)
    state = meta_client.describe("image")
    print("meta_art: style %s, %d asset(s) x %d candidate(s) = %d concept(s), %d call(s) at most "
          "(image + segment)" % (STYLE, len(assets), len(tags), concepts, planned))
    print("meta_art: projected cost at the documented list prices %.4f USD of a %.2f USD ceiling "
          "(%.4f per image, %.4f per segment)"
          % (projected, args.budget, meta_spend_ledger.PER_IMAGE, meta_spend_ledger.PER_SEGMENT))
    print("meta_art: backend %s, mode %s, key %s, cache %s (%d entries)"
          % (state["backend"], state["mode"],
             "present" if state["key_present"] else "MISSING", shown(state["cache_dir"]),
             state["cache_entries"]))
    for asset in assets:
        print("  %-15s scene %-16s noun %r" % (asset, ASSETS[asset]["scene"], ASSETS[asset]["noun"]))
    if args.dry_run:
        print("meta_art: dry run, nothing was sent")
        return 0
    if planned > args.max_calls:
        print("meta_art: that is %d calls against --max-calls %d, so nothing was sent"
              % (planned, args.max_calls))
        return 2
    if projected > args.budget:
        print("meta_art: that plan projects %.4f USD against a %.2f USD ceiling, so nothing was sent"
              % (projected, args.budget))
        return 2
    if state["backend"] == "meta" and not state["key_present"]:
        print("meta_art: no Meta key in this process environment (%s). Nothing was sent. "
              "Set the key in the shell that runs this, or use PP_AI_BACKEND=mock for the offline chain."
              % state["key_env"])
        return 3

    records = []
    spend_rows = []
    worst = 0
    for asset in assets:
        for tag in tags:
            record, verdict = one_candidate(asset, tag, args)
            records.append(record)
            spend_rows.extend(record["spend"])
            print("%-15s %-4s %-12s %s" % (asset, tag, verdict,
                                           "; ".join(record["problems"]) or "all steps recorded"))
            if verdict != "ok":
                worst = 1
    written = append_spend(spend_rows, spend_path)
    summary = {"when": stamp(), "card": CARD, "style": STYLE, "assets": assets, "candidates": tags,
               "projected_usd": projected, "records": records,
               "spend_log": shown(spend_path) if written else None}
    ensure(args.out)
    with open(os.path.join(args.out, "run_summary.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("meta_art: %d candidate(s) written under %s, spend rows %d%s"
          % (len(records), shown(args.out), len(spend_rows),
             " appended to %s" % shown(spend_path) if written else " (none: no live call)"))
    return worst


if __name__ == "__main__":
    sys.exit(main())
