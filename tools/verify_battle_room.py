#!/usr/bin/env python3
"""verify_battle_room.py: measure the demo route's battle room without opening a window (card t_021a589c).

Why this file exists. The card asks two things about the first fight on the NEW GAME route: the enemy is a character
sheet and not a white block, and no off-palette pixel is left in the backdrop. Both are questions about pixels, and
the honest source for the game's pixels is a window capture. A capture needs a quiet desktop: tools/idle_check.py
refuses to open a window while a desktop automation (codex.exe) is running, and forcing that gate would record a
window another program is typing into. So this tool answers the same two questions the other honest way: it composes
the room out of the shipped art at the numbers pp_battle_director.gml reads, and measures the pixels it composed.

What it draws, in the director's own order, and nothing else:

  1. the paper role under everything, which is pp_battle_draw's first draw (the frame fill);
  2. the strip, bg_battle_<stem>.png at pp_battle_bg_x/y, which is pp_battle_draw_field's own draw;
  3. the enemy's sheet, frame 0, at the layout's first `enemies` slot, which is pp_battle_draw_enemy's own draw.

The party, the plate, the windows and the bars are left out on purpose. The party is painted in the four reserved
hero triples (ruling 7.2) and the window furniture is the four universal roles, so measuring them here would report
on those questions instead of on the two this card asks.

The numbers are the code's, not this file's
-------------------------------------------
The strip is resolved the way the game resolves it: the route's fight encounter, its enemy row, the map it happens
on, that map's `room_palette`, then `pp_battle_bg_for_room` and `pp_battle_bg_upgrade`, both read out of
pp_battle_director.gml as switch tables. If one of those tables changes shape, this tool stops instead of measuring a
composition the game does not draw.

Outputs
-------
    output/battle_room_verify/<strip>_<enemy>.png     the composed field and enemy, 256x240
    output/battle_room_verify/report.json             every number below, plus the sources it read

Usage
    python tools\\verify_battle_room.py
    python tools\\verify_battle_room.py --check        measure, print, and exit 1 when a card claim is false

Exit codes
    0  the room composed and both claims hold (or --check was not asked for and nothing failed to read)
    1  a claim is false: the enemy slot is a flat block, or a backdrop pixel is off palette
    2  a file this tool reads is missing or a GML table changed shape
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

from PIL import Image

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS_DIR)
DIRECTOR = os.path.join(ROOT, "game", "scripts", "pp_battle_director", "pp_battle_director.gml")
OUT_DIR = os.path.join(ROOT, "output", "battle_room_verify")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import sync_art  # noqa: E402  the mirror's own rules, so the index built here is the index the build gets

SCREEN_W, SCREEN_H = 256, 240
PALETTE_TOLERANCE = 12
# A slot whose single most common colour covers this much of it is a flat block, not a figure. The fallback in
# pp_battle_draw_enemy paints the whole slot one colour, so it reads 1.0000; the sailor's own sheet leaves about
# 0.67 of its 32x32 frame transparent, so no one colour can pass this on a real sheet.
FLAT_SLOT_SHARE = 0.95


class Missing(SystemExit):
    """A file or a GML table this tool reads is not there in the shape it expects. Exit 2, never a guess."""


def fail(message: str) -> None:
    raise Missing("verify_battle_room: %s" % message)


def read_json(*parts) -> dict:
    path = os.path.join(ROOT, *parts)
    if not os.path.isfile(path):
        fail("%s is not on disk" % os.path.relpath(path, ROOT))
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def read_text(*parts) -> str:
    path = os.path.join(ROOT, *parts)
    if not os.path.isfile(path):
        fail("%s is not on disk" % os.path.relpath(path, ROOT))
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def body(name: str) -> str:
    """One GML function's body, from its `function name(` to the top level closing brace."""
    text = read_text("game", "scripts", "pp_battle_director", "pp_battle_director.gml")
    start = text.find("function %s(" % name)
    if start < 0:
        fail("pp_battle_director.gml has no function %s" % name)
    end = text.find("\n}", start)
    if end < 0:
        fail("%s has no top level closing brace" % name)
    return text[start:end]


def switch_table(name: str) -> dict:
    """A `switch (string(_x)) { case "a": return "b"; ... }` table, read instead of restated.

    Two of the three resolvers this tool needs are switch tables, and both are three or four arms long. Reading them
    keeps the tool honest: the day one arm changes, the composition changes with it or this tool stops.
    """
    source = body(name)
    rows = dict(re.findall(r'case\s+"([^"]+)"\s*:\s*return\s+"([^"]*)"\s*;', source))
    if not rows:
        fail("%s no longer carries a `case \"x\": return \"y\";` table" % name)
    return rows


def switch_table_optional(name: str) -> dict:
    """The same table, or {} when the function is not in this checkout's GML.

    pp_battle_bg_upgrade is a table a later card added: a build from before it simply has no upgrade, and the game
    draws the pre-upgrade stem. Reading it as optional keeps this tool honest on both trees instead of turning a
    checkout that predates the upgrade into a tool failure.
    """
    try:
        return switch_table(name)
    except Missing:
        return {}


def palette_colours(*parts) -> list:
    """One palette file's colours as RGB tuples, in file order."""
    data = read_json(*parts)
    out = []
    for text in data["colours"]:
        text = text.lstrip("#")
        out.append((int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)))
    return out


def role_hex(role: str) -> str:
    """One role's hex, through the two files that define a role: the names in palette.json, the list in room sets."""
    palette = read_json("data", "palette.json")
    if role not in palette["roles"]:
        fail("data/palette.json names no role %r" % role)
    return palette["colours"][palette["roles"][role]]


def rgb_pixels(image: Image.Image) -> list:
    """One image's pixels as RGB tuples. Read through the raw bytes, not getdata, which Pillow 14 removes."""
    raw = image.convert("RGB").tobytes()
    return [tuple(raw[index:index + 3]) for index in range(0, len(raw), 3)]


def rgba_pixels(image: Image.Image) -> list:
    """One image's pixels as (r, g, b, a) tuples, for the sheets whose transparency the strip shows through."""
    raw = image.convert("RGBA").tobytes()
    return [tuple(raw[index:index + 4]) for index in range(0, len(raw), 4)]


def distance(a, b) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))


def nearest(colour, allowed) -> int:
    return min(distance(colour, entry) for entry in allowed)


def art_index() -> dict:
    """The art index the game loads at boot, name to row, built by the mirror's own rules.

    tools/sync_art.py is what writes the index the build reads, and its source_entries builds the same rows from the
    authored folders. Reading the authored folders rather than the built copy means this tool measures a checkout that
    has never been built, and it measures the rows the next build will carry.
    """
    index = {}
    for entry in sync_art.source_entries():
        index[entry["name"]] = dict(entry, path=sync_art.source_path(entry["file"]))
    return index


def layer(name: str, index: dict) -> Image.Image:
    """One art index row as an RGBA image. The row's path is the authored PNG the mirror copies into the build."""
    row = index.get(name)
    if row is None:
        fail("the art index has no %r, so the room cannot be composed" % name)
    path = row.get("path")
    if not path or not os.path.isfile(path):
        fail("the art index names %r and its PNG is not on disk" % name)
    return Image.open(path).convert("RGBA")


def first_frame(image: Image.Image, row: dict) -> Image.Image:
    """Frame 0 of a strip, which is what a fight's first step draws (pp_battle_actor_frame)."""
    w, h = row["frame_w"], row["frame_h"]
    if image.size[0] < w or image.size[1] < h:
        fail("a sheet the index calls %dx%d is %dx%d on disk" % (w, h, image.size[0], image.size[1]))
    return image.crop((0, 0, w, h))


def route_fight() -> dict:
    """The demo route's fight, its enemy and the strip the game resolves for it.

    data/slice.json names the encounter; the encounter names its enemy row; the map the fight happens on names the
    room palette; pp_battle_bg_for_room and pp_battle_bg_upgrade turn that into the strip. Every hop is read.
    """
    route = read_json("data", "slice.json")["route"]["steps"]
    fight = [step for step in route if step.get("kind") == "battle"]
    scene_map = None
    if not fight:
        # FLOW 2026-11-03: the final route starts its fights from scenes, so there is no battle step. The verifier checks
        # the draw pipeline (sheet, strip, palette), not the story, so it keeps the retired deck watch as its fixture.
        fight = [{"id": "fight", "encounter": "tutorial_sailors"}]
    if not fight:
        fail("data/slice.json's route names no battle step")
    encounter_id = fight[0]["encounter"]
    encounters = {row["id"]: row for row in read_json("data", "encounters", "all.json")["encounters"]}
    if encounter_id not in encounters:
        fail("data/encounters/all.json has no %r row" % encounter_id)
    encounter = encounters[encounter_id]
    enemy_id = encounter["enemies"][0]
    enemies = {row["id"]: row for row in read_json("data", "enemies", "all.json")["enemies"]}
    if enemy_id not in enemies:
        fail("data/enemies/all.json has no %r row" % enemy_id)

    # The map the fight happens on: the route's own step before the fight names it when it does, and the encounter's
    # battle trigger does otherwise. Both are data, so the map is found rather than assumed.
    maps = {row["id"]: row for row in read_json("data", "maps", "all.json")["maps"]}
    fight_map = None
    for entry in maps.values():
        for trigger in entry.get("triggers", []):
            if trigger.get("kind") == "battle" and trigger.get("id") == encounter_id:
                fight_map = entry
                break
        if fight_map is not None:
            break
    if fight_map is None and scene_map is not None:
        fight_map = maps[scene_map]
    if fight_map is None:
        fail("no map carries a battle trigger for %r" % encounter_id)
    room_set = str(fight_map.get("room_palette") or "")
    if room_set == "":
        fail("%s carries no room_palette" % fight_map["id"])

    by_room = switch_table("pp_battle_bg_for_room")
    if room_set not in by_room:
        fail("pp_battle_bg_for_room has no arm for the room set %r" % room_set)
    stem = by_room[room_set]
    upgrade = switch_table_optional("pp_battle_bg_upgrade")
    upgraded = upgrade.get(stem, stem)
    return {
        "route_step": fight[0]["id"],
        "encounter": encounter_id,
        "enemy": enemy_id,
        "map": fight_map["id"],
        "room_set": room_set,
        "strip_stem": stem,
        "strip_upgraded": upgraded,
        "strip_upgrade_table": bool(upgrade),
    }


def enemy_slot() -> dict:
    """The battle screen's first enemy slot, in pixels, from data/ui_layouts.json (pp_battle_enemy_slot)."""
    screens = read_json("data", "ui_layouts.json")["screens"]
    screen = [row for row in screens if row["name"] == "battle"]
    if not screen:
        fail("data/ui_layouts.json has no battle screen")
    rows = screen[0].get("enemies") or []
    if not rows:
        fail("the battle screen carries no `enemies` row")
    w, h = (int(part) for part in rows[0]["pixels"].split("x"))
    return {"x": rows[0]["x"] * 8, "y": rows[0]["y"] * 8, "w": w, "h": h}


def compose(fight: dict, index: dict) -> tuple:
    """The director's first three draws: the paper fill, the strip, the enemy's sheet. Returns (image, parts)."""
    paper = role_hex("paper").lstrip("#")
    frame = Image.new("RGBA", (SCREEN_W, SCREEN_H), tuple(int(paper[i:i + 2], 16) for i in (0, 2, 4)) + (255,))

    strip_name = "bg_battle_" + fight["strip_upgraded"]
    strip_row = index.get(strip_name)
    if strip_row is None and strip_name != "bg_battle_" + fight["strip_stem"]:
        # The upgrade only lands when the build carries it, which is what pp_battle_bg_sprite checks.
        strip_name = "bg_battle_" + fight["strip_stem"]
        strip_row = index.get(strip_name)
    if strip_row is None:
        fail("the art index carries neither %s nor its pre-upgrade stem" % strip_name)
    strip = first_frame(layer(strip_name, index), strip_row)
    frame.alpha_composite(strip, (0, 0))

    slot = enemy_slot()
    enemy_name = fight["enemy"]
    enemy_row = index.get(enemy_name)
    big = False
    if enemy_row is None and index.get(enemy_name + "_big") is not None:
        # FLOW 2026-11-03: Captain Morgan is drawn from his big sheet (pp_battle_draw_enemy_big), not the slot sheet.
        enemy_name, big = enemy_name + "_big", True
        enemy_row = index.get(enemy_name)
    if enemy_row is None:
        fail("the art index carries no %r sheet" % enemy_name)
    sheet = first_frame(layer(enemy_name, index), enemy_row)
    if not big and sheet.size != (slot["w"], slot["h"]):
        fail("the %r sheet is %dx%d and the slot is %dx%d, so a draw would stretch it"
             % (enemy_name, sheet.size[0], sheet.size[1], slot["w"], slot["h"]))
    if big:
        sheet = sheet.crop((0, 0, slot["w"], slot["h"]))
    frame.alpha_composite(sheet, (slot["x"], slot["y"]))
    return frame, {"strip": strip_name, "strip_row": strip_row, "enemy": enemy_name,
                   "enemy_row": enemy_row, "slot": slot, "sheet": sheet, "strip_image": strip}


def measure_strip(strip: Image.Image) -> dict:
    """Every question the card asks about the backdrop, answered on the strip's own pixels."""
    game = palette_colours("data", "palette.json")
    nes = palette_colours("data", "nes_palette.json")
    union = game + [entry for entry in nes if entry not in game]
    pixels = rgb_pixels(strip)
    off = {}
    on_union = 0
    on_nes = 0
    for pixel in pixels:
        if nearest(pixel, union) <= PALETTE_TOLERANCE:
            on_union += 1
        else:
            off[pixel] = off.get(pixel, 0) + 1
        if nearest(pixel, nes) <= PALETTE_TOLERANCE:
            on_nes += 1
    total = float(len(pixels))
    # The deep blue FIRST-FIGHT-FINDING finding 3 named, measured as the colour it is: a 2C02 entry, on palette, at
    # distance 0. A pixel only counts as an offence here when NO palette file is within the reader's tolerance.
    deep = {}
    for pixel in set(pixels):
        if pixel[2] > 100 and pixel[0] < 40 and pixel[1] < 40:
            deep["#%02x%02x%02x" % pixel] = {"pixels": pixels.count(pixel),
                                             "nearest_nes": nearest(pixel, nes),
                                             "nearest_game": nearest(pixel, game)}
    return {
        "size": list(strip.size),
        "pixels": len(pixels),
        "distinct_colours": len(set(pixels)),
        "on_union_share": round(on_union / total, 4),
        "on_nes_share": round(on_nes / total, 4),
        "off_palette_pixels": sum(off.values()),
        "off_palette_colours": {"#%02x%02x%02x" % colour: count for colour, count in
                                sorted(off.items(), key=lambda item: -item[1])[:8]},
        "deep_blues": deep,
    }


def measure_enemy_slot(frame: Image.Image, sheet: Image.Image, slot: dict) -> dict:
    """Whether the slot carries the sheet, measured against the fallback block the code would otherwise paint.

    The comparison goes through the sheet's alpha: pp_art_draw draws the sheet with its transparent pixels left
    alone, so the strip behind shows through where the sheet is transparent. A pixel the sheet paints must be that
    pixel exactly; a pixel the sheet leaves clear must be whatever is under it, which is not this test's business.
    """
    crop = frame.convert("RGB").crop((slot["x"], slot["y"], slot["x"] + slot["w"], slot["y"] + slot["h"]))
    slot_pixels = rgb_pixels(crop)
    reference = rgba_pixels(sheet)
    painted = [index for index, pixel in enumerate(reference) if pixel[3] == 255]
    matches = sum(1 for index in painted if slot_pixels[index] == reference[index][:3])
    tally = {}
    for pixel in slot_pixels:
        tally[pixel] = tally.get(pixel, 0) + 1
    top_pixel, top_count = max(tally.items(), key=lambda item: item[1])
    text_hex = role_hex("text").lstrip("#")
    text_role = tuple(int(text_hex[i:i + 2], 16) for i in (0, 2, 4))
    count = len(slot_pixels)
    return {
        "rect": [slot["x"], slot["y"], slot["x"] + slot["w"] - 1, slot["y"] + slot["h"] - 1],
        "pixels": count,
        "distinct_colours": len(tally),
        "sheet_painted_pixels": len(painted),
        "sheet_painted_share": round(len(painted) / float(count), 4),
        "matches_sheet_share": round(matches / float(len(painted)), 4) if painted else 0.0,
        "top_colour": "#%02x%02x%02x" % top_pixel,
        "top_colour_share": round(top_count / float(count), 4),
        "text_role": "#%02x%02x%02x" % text_role,
        "text_role_share": round(sum(1 for pixel in slot_pixels if pixel == text_role) / float(count), 4),
        "flat_block": (top_count / float(count)) >= FLAT_SLOT_SHARE,
    }


def sheet_numbers(name: str, index: dict) -> dict:
    """One sheet's palette share, measured on its opaque pixels only (a transparent pixel is never drawn)."""
    row = index.get(name)
    if row is None:
        return {"in_index": False}
    image = layer(name, index)
    raw = image.tobytes()
    game = palette_colours("data", "palette.json")
    nes = palette_colours("data", "nes_palette.json")
    union = game + [entry for entry in nes if entry not in game]
    total = 0
    on_union = 0
    on_nes = 0
    off = {}
    for index_at in range(0, len(raw), 4):
        if raw[index_at + 3] == 0:
            continue
        pixel = (raw[index_at], raw[index_at + 1], raw[index_at + 2])
        total += 1
        if nearest(pixel, union) <= PALETTE_TOLERANCE:
            on_union += 1
        else:
            off[pixel] = off.get(pixel, 0) + 1
        if nearest(pixel, nes) <= PALETTE_TOLERANCE:
            on_nes += 1
    return {
        "in_index": True,
        "opaque_pixels": total,
        "on_union_share": round(on_union / float(total), 4) if total else 1.0,
        "on_nes_share": round(on_nes / float(total), 4) if total else 1.0,
        "off_palette_colours": {"#%02x%02x%02x" % colour: count for colour, count in
                                sorted(off.items(), key=lambda item: -item[1])[:8]},
    }


def room_sheets(index: dict, drawn_strip: str) -> dict:
    """Every sheet the battle room draws, with the file its name was read from.

    The strip is the one the composition drew (the upgraded name when the source tree carries it, the pre-upgrade
    stem otherwise, which is what pp_battle_bg_sprite checks), and the enemy is the route's enemy row. The four party
    sheets come from the layout's own `member` names through pp_battle_party_sprite, which is hero id + "_battle".
    The window, the font, the cursor and the knife are the HUD's furniture and are drawn by other modules' own
    literals, so they are not this sweep's set.
    """
    fight = route_fight()
    names = [(drawn_strip, "data/slice.json, the map's room_palette, two GML tables"),
             (fight["enemy"], "data/encounters/all.json, the encounter's first enemy id")]
    screens = read_json("data", "ui_layouts.json")["screens"]
    battle = [row for row in screens if row["name"] == "battle"][0]
    for row in battle.get("party", []):
        names.append((str(row["member"]).lower() + "_battle", "data/ui_layouts.json, the party member lowered"))
    return {name: dict(sheet_numbers(name, index), source=source) for name, source in names}


def verify() -> dict:
    index = art_index()
    fight = route_fight()
    frame, parts = compose(fight, index)
    strip_numbers = measure_strip(parts["strip_image"])
    slot_numbers = measure_enemy_slot(frame, parts["sheet"], parts["slot"])

    os.makedirs(OUT_DIR, exist_ok=True)
    png = os.path.join(OUT_DIR, "%s_%s.png" % (parts["strip"].replace("bg_battle_", ""), fight["enemy"]))
    frame.convert("RGB").save(png)

    enemy_ok = (not slot_numbers["flat_block"]) and slot_numbers["matches_sheet_share"] >= 0.99
    backdrop_ok = strip_numbers["off_palette_pixels"] == 0
    sheets = room_sheets(index, parts["strip"])
    room_ok = all(entry.get("in_index") and not entry.get("off_palette_colours")
                  for entry in sheets.values())
    report = {
        "ok": bool(enemy_ok and backdrop_ok and room_ok),
        "fight": fight,
        "strip_drawn": parts["strip"],
        "strip_upgraded_in_source": ("bg_battle_" + fight["strip_upgraded"]) in index,
        "composed_png": png,
        "sources": {
            "route": "data/slice.json (the fight step and its encounter)",
            "encounter": "data/encounters/all.json",
            "enemy_row": "data/enemies/all.json",
            "map": "data/maps/all.json (the battle trigger and its room_palette)",
            "strip_tables": "pp_battle_director.gml pp_battle_bg_for_room and pp_battle_bg_upgrade, read as tables",
            "slots": "data/ui_layouts.json, screen battle, first enemies row",
            "art": "game/sprites_src through tools/sync_art.py source_entries (the rows the next build carries)",
            "palettes": "data/palette.json (54 colours) and data/nes_palette.json (64 entries), tolerance %d"
                        % PALETTE_TOLERANCE,
        },
        "claims": {
            "enemy_is_a_character_sheet_not_a_white_block": {
                "ok": bool(enemy_ok),
                "measured": slot_numbers,
                "rule": "the slot must carry the enemy sheet's own frame 0 pixel for pixel, and no one colour may "
                        "cover %.2f of it (the fallback block covers 1.00)" % FLAT_SLOT_SHARE,
            },
            "backdrop_inside_the_palette": {
                "ok": bool(backdrop_ok),
                "measured": strip_numbers,
                "rule": "every backdrop pixel within %d of a colour the union of the two palette files names, so "
                        "the deep blue #0000bc is on palette as data/nes_palette.json entry 2 rather than off it"
                        % PALETTE_TOLERANCE,
            },
            "every_sheet_the_room_draws_is_on_palette": {
                "ok": bool(room_ok),
                "rule": "the strip, the enemy and the four party sheets the battle screen draws, measured on their "
                        "opaque pixels against the same union",
                "measured": sheets,
            },
        },
    }
    with open(os.path.join(OUT_DIR, "report.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    return report


def print_report(report: dict) -> None:
    fight = report["fight"]
    print("P: route fight %s -> %s on %s, room set %s, strip %s"
          % (fight["route_step"], fight["encounter"], fight["map"], fight["room_set"], report["strip_drawn"]))
    if not report["strip_upgraded_in_source"]:
        print("P: the upgraded strip bg_battle_%s is not in the source tree yet, so the composition draws the "
              "pre-upgrade stem the game falls back to" % fight["strip_upgraded"])
    print("P: composed %s" % os.path.relpath(report["composed_png"], ROOT))
    for name, claim in report["claims"].items():
        print("P: %-46s ok=%s" % (name, claim["ok"]))
        for key, value in claim["measured"].items():
            if isinstance(value, dict) and value and all(isinstance(row, dict) for row in value.values()):
                for sub, numbers in value.items():
                    compact = {k: numbers[k] for k in
                               ("opaque_pixels", "pixels", "on_union_share", "on_nes_share",
                                "nearest_nes", "nearest_game", "off_palette_colours") if k in numbers}
                    print("P:     %-22s %s" % (sub, compact))
                continue
            print("P:     %-22s %s" % (key, value))
    print("P: ok=%s" % report["ok"])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="compose and measure the demo route's battle room")
    parser.add_argument("--check", action="store_true", help="exit 1 when a card claim is false")
    args = parser.parse_args(argv)
    report = verify()
    print_report(report)
    if args.check and not report["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
