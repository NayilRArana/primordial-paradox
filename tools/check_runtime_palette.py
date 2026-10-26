#!/usr/bin/env python3
"""check_runtime_palette.py: are the colours the runtime draws actually outputs of the 2C02?

Why this exists (card t_30746cd8). The NES audit measures pixels in files. The battle screen, the game over screen and
every menu are not files: they are flat rectangles and glyphs drawn at run time from a role name, and
`pp_role_colour()` resolves a role to an index in `data/palette.json` and `pp_colour()` turns that index into a
drawing colour with no further test (game/scripts/pp_data/pp_data.gml lines 150 to 165). Measured on 2026-10-26:
**0 of the 54 colours in `data/palette.json` is an output of the Ricoh 2C02**, and a real window capture of the first
fight carries the design grey `#4a4a58` at `(73, 72, 87)` (knowledge/BATTLE-DIM-OFF-PALETTE-2026-10-26.md section 2,
the row for the `dim` role). So the defect is not in a picture, it is in the resolve, and no audit of pictures can see
it once the pictures stop being kept.

What passing means, in five parts, so this check cannot go green by absence:

  1. `data/palette_ppu.json` exists and carries a mapping for **every** colour of `data/palette.json`, by index.
  2. every mapped target names a usable entry of `data/nes_palette.json`, so the resolved colour is a real output.
  3. `game/scripts/pp_data/pp_data.gml` names `palette_ppu.json`, so the table is what the runtime reads rather than
     a file somebody wrote and left beside the code.
  4. a material family still ramps: the entries a hue family maps to never go backwards in measured luminance, since a
     darker level drawn brighter than the level above it turns a shadow into a highlight.
  5. the four roles every screen draws with stay four colours, and no room palette set collapses two levels of one
     family onto one entry, which would spend a screen's palette on a step nobody can see.

Parts 1 to 3 are the defect this file was opened for (card t_54db4d0f). Parts 4 and 5 pin the visual decision the card
made, because "it looks right on a built game" is not a check anybody can run on a box with no GameMaker licence.

Usage:
    python tools\\check_runtime_palette.py
    python tools\\check_runtime_palette.py --json output\\runtime_palette.json

Exit 0 when all five hold, 1 otherwise, and it always prints the count of design colours that have no legal output so
a red run says how big the job is.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGN = os.path.join("data", "palette.json")
MASTER = os.path.join("data", "nes_palette.json")
TABLE = os.path.join("data", "palette_ppu.json")
RUNTIME = os.path.join("game", "scripts", "pp_data", "pp_data.gml")
RUNTIME_NAME = "palette_ppu.json"
ROOMS = os.path.join("data", "room_palettes.json")

# Luminance is not restated here: tools\art\contrast_check.py owns the 2C02 luminance table (card CONTRAST-TOOL), and
# tools\palette_synergy.py imports it for the same reason.
sys.path.insert(0, os.path.join(ROOT, "tools", "art"))
import contrast_check  # noqa: E402

# The role names every screen draws with, in the order the window draws them: ink is the border and the fade, paper is
# the panel the glyphs sit on, dim is the mid tone (a bar track, a rule), text is the marker. window_shadow is separate
# because a shadow has to be a different entry from the fill and the border, not a rung between them.
UNIVERSAL = ("ink", "paper", "dim", "text")
SHADOW_ROLE = "window_shadow"


def read_json(path: str):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def master_entries(root: str) -> dict:
    """{entry index: {"code", "hex", "usable"}} from the 2C02 table, with the hex normalised to lowercase."""
    entries = {}
    for item in read_json(os.path.join(root, MASTER))["entries"]:
        entries[int(item["index"])] = {
            "code": item.get("code", "$%02X" % int(item["index"])),
            "hex": str(item["hex"]).lower(),
            "usable": bool(item.get("usable", True)),
        }
    return entries


def runtime_names_the_table(root: str) -> tuple:
    """(True/False, why) for the one line of GML that has to read the table."""
    path = os.path.join(root, RUNTIME)
    if not os.path.isfile(path):
        return False, "%s is not in this tree" % RUNTIME.replace(os.sep, "/")
    with open(path, "r", encoding="utf-8-sig", errors="ignore") as handle:
        body = handle.read()
    if RUNTIME_NAME not in body:
        return False, ("%s never names %s, so the table would be a file beside the code rather than what the "
                       "runtime reads" % (RUNTIME.replace(os.sep, "/"), RUNTIME_NAME))
    return True, "%s names %s" % (RUNTIME.replace(os.sep, "/"), RUNTIME_NAME)


def rgb_of(hex_value: str) -> tuple:
    body = str(hex_value).lstrip("#")
    return int(body[0:2], 16), int(body[2:4], 16), int(body[4:6], 16)


def family_levels(role_index: dict) -> dict:
    """{family: {level: design index}} from the family_level role names (grey_0, sea_3, ...) in data/palette.json."""
    found = {}
    for name, index in role_index.items():
        match = re.match(r"^([a-z]+)_([0-9])$", str(name))
        if not match:
            continue
        found.setdefault(match.group(1), {})[int(match.group(2))] = int(index)
    return found


def layout_guards(root: str, role_index: dict, rows: list) -> list:
    """The two guards that pin the visual decision, so the table cannot be tuned blind on a box with no GameMaker.

    Guard 4, a family ramps: the mapped entries of one hue family never go backwards in measured luminance. The 2C02
    cannot hold six levels of anything, so a level may share an entry with its neighbour; what it may not do is come
    out brighter than the level above it, which draws a shadow as a highlight.
    Guard 5, a screen keeps its steps: the four universal roles resolve to four different entries, and no room palette
    set collapses two different design colours of one family onto one entry.
    """
    problems = []
    lum = {}
    for row in rows:
        if row.get("legal") and row.get("entry_hex"):
            lum[row["index"]] = contrast_check.luminance(rgb_of(row["entry_hex"]))

    def code(index):
        for row in rows:
            if row["index"] == index:
                return row.get("entry_hex") or "-"
        return "-"

    families = family_levels(role_index)
    for family in sorted(families):
        levels = families[family]
        if family == "grey" or len(levels) < 2:
            # grey is the UI family: its order is checked below by role name, because ink and paper are not a ramp of
            # scenery but the fill and the border of a window.
            continue
        ordered = [levels[level] for level in sorted(levels) if levels[level] in lum]
        for lower, upper in zip(ordered, ordered[1:]):
            if lum[upper] < lum[lower] - 1e-9:
                low_level = [k for k, v in levels.items() if v == lower][0]
                high_level = [k for k, v in levels.items() if v == upper][0]
                problems.append("%s_%d maps to %s at luminance %.3f, which is darker than %s_%d at %s (%.3f), so the "
                                "family's ramp runs backwards"
                                % (family, high_level, code(upper), lum[upper],
                                   family, low_level, code(lower), lum[lower]))

    # The four roles every screen draws with: fill, border, mid tone and marker stay four colours, in that order.
    named = [role_index[name] for name in UNIVERSAL if name in role_index]
    entries = {index: None for index in named}
    if SHADOW_ROLE in role_index:
        entries[role_index[SHADOW_ROLE]] = None
    for row in rows:
        if row["index"] in entries:
            entries[row["index"]] = row.get("entry")
    ordered_roles = [name for name in UNIVERSAL if name in role_index]
    for first, second in zip(ordered_roles, ordered_roles[1:]):
        a, b = role_index[first], role_index[second]
        if a in lum and b in lum and lum[b] < lum[a] - 1e-9:
            problems.append("role %s resolves to %s at luminance %.3f and %s to %s at %.3f, so the window draws its "
                            "second colour darker than its first"
                            % (first, code(a), lum[a], second, code(b), lum[b]))
    for a, b in zip(ordered_roles, ordered_roles[1:]):
        if entries.get(role_index[a]) is not None and entries.get(role_index[a]) == entries.get(role_index[b]):
            problems.append("roles %s and %s both resolve to the same entry, so one of them draws nothing" % (a, b))
    if SHADOW_ROLE in role_index:
        shadow = role_index[SHADOW_ROLE]
        for other in ("ink", "paper"):
            if other in role_index and entries.get(shadow) is not None and entries.get(shadow) == entries.get(role_index[other]):
                problems.append("role %s resolves to the same entry as %s, so a window shadow draws nothing"
                                % (SHADOW_ROLE, other))

    # Guard 5b: a room palette set may not collapse two design colours of one family onto one entry.
    rooms_path = os.path.join(root, ROOMS)
    if os.path.isfile(rooms_path):
        rooms = read_json(rooms_path)
        for palette_set in rooms.get("sets", []):
            members = [role_index[name] for name in palette_set.get("roles", []) if name in role_index]
            per_family = {}
            for index in set(members):
                per_family.setdefault(index // 6, set()).add(index)
            for family, indices in sorted(per_family.items()):
                if len(indices) < 2:
                    continue
                targets = {}
                for index in indices:
                    for row in rows:
                        if row["index"] == index:
                            targets[index] = row.get("entry")
                if len(set(targets.values())) != len(indices):
                    problems.append("room palette set %r spends %d design colours of family %d and they resolve to %d "
                                    "entry(s), so one of them is a step nobody can see"
                                    % (palette_set.get("id"), len(indices), family, len(set(targets.values()))))
    return problems


def check(root: str = ROOT) -> tuple:
    """(problems, rows, counts). rows is one dict per design colour, for the report and for --json."""
    design = read_json(os.path.join(root, DESIGN))
    colours = list(design["colours"])
    roles = {}
    for name, index in (design.get("roles") or {}).items():
        roles.setdefault(int(index), []).append(name)
    master = master_entries(root)

    problems = []
    table_path = os.path.join(root, TABLE)
    mapping = {}
    if os.path.isfile(table_path):
        payload = read_json(table_path)
        raw = payload.get("mapping") if isinstance(payload, dict) else None
        if not isinstance(raw, dict):
            problems.append("%s has no \"mapping\" object" % TABLE.replace(os.sep, "/"))
            raw = {}
        for key, value in raw.items():
            try:
                mapping[int(key)] = int(value)
            except (TypeError, ValueError):
                problems.append("%s: mapping %r to %r is not two entry numbers"
                                % (TABLE.replace(os.sep, "/"), key, value))
    else:
        problems.append("%s is missing, so the runtime draws every design colour as it was painted"
                        % TABLE.replace(os.sep, "/"))

    rows = []
    off = 0
    for index, hex_value in enumerate(colours):
        target = mapping.get(index)
        row = {"index": index, "design_hex": str(hex_value).lower(), "roles": sorted(roles.get(index, [])),
               "entry": None, "entry_hex": None, "usable": None, "legal": False}
        if target is None:
            row["why"] = "no entry in %s" % TABLE.replace(os.sep, "/")
            off += 1
        elif target not in master:
            row["why"] = "names entry %d, which is not in data/nes_palette.json" % target
            off += 1
        else:
            entry = master[target]
            row.update({"entry": target, "entry_hex": entry["hex"], "usable": entry["usable"]})
            if not entry["usable"]:
                row["why"] = "%s is flagged unusable" % entry["code"]
                off += 1
            else:
                # The design hex is irrelevant once it resolves: what reaches the screen is the entry's output.
                row["legal"] = True
                row["why"] = "resolved to %s %s" % (entry["code"], entry["hex"])
        rows.append(row)

    if len(mapping) > len(colours):
        problems.append("%s carries %d mappings for %d colours of data/palette.json"
                        % (TABLE.replace(os.sep, "/"), len(mapping), len(colours)))

    names_it, why = runtime_names_the_table(root)
    if not names_it:
        problems.append(why)

    role_index = {}
    for name, index in (design.get("roles") or {}).items():
        try:
            role_index[str(name)] = int(index)
        except (TypeError, ValueError):
            continue
    problems.extend(layout_guards(root, role_index, rows))

    counts = {"colours": len(colours), "mapped": len(mapping), "legal": len(colours) - off, "off": off,
              "runtime_reads": bool(names_it), "distinct_entries": len(set(mapping.values()))}
    return problems, rows, counts


def report(rows: list, counts: dict, problems: list) -> int:
    print("runtime palette: %d colour(s) in data/palette.json, %d mapped in %s, %d resolved to a 2C02 output, %d not"
          % (counts["colours"], counts["mapped"], TABLE.replace(os.sep, "/"), counts["legal"], counts["off"]))
    print("runtime palette: %d distinct 2C02 entry(s) for the %d design colours"
          % (counts.get("distinct_entries", 0), counts["colours"]))
    for row in rows:
        print("  %2d %-9s %-9s  %s"
              % (row["index"], row["design_hex"],
                 row["entry_hex"] or "-", row["why"]))
    for problem in problems:
        print("FAIL %s" % problem)
    print("check_runtime_palette: %s" % ("PASS" if not problems and not counts["off"] else "FAIL"))
    return 0 if not problems and not counts["off"] else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check that the runtime resolves design colours to 2C02 outputs.")
    parser.add_argument("--root", default=ROOT)
    parser.add_argument("--json", dest="json_path", default=None)
    parser.add_argument("--quiet", action="store_true", help="one line, and the exit code carries the verdict")
    args = parser.parse_args(argv)

    problems, rows, counts = check(args.root)
    if args.json_path:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_path)), exist_ok=True)
        with open(args.json_path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump({"counts": counts, "rows": rows, "problems": problems}, handle, indent=2, sort_keys=True)
            handle.write("\n")
    if args.quiet:
        print("check_runtime_palette: %d of %d design colour(s) resolved to a 2C02 output"
              % (counts["legal"], counts["colours"]))
        return 0 if not problems and not counts["off"] else 1
    return report(rows, counts, problems)


if __name__ == "__main__":
    sys.exit(main())
