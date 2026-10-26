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

What passing means, in three parts, so this check cannot go green by absence:

  1. `data/palette_ppu.json` exists and carries a mapping for **every** colour of `data/palette.json`, by index.
  2. every mapped target names a usable entry of `data/nes_palette.json`, so the resolved colour is a real output.
  3. `game/scripts/pp_data/pp_data.gml` names `palette_ppu.json`, so the table is what the runtime reads rather than
     a file somebody wrote and left beside the code.

Usage:
    python tools\\check_runtime_palette.py
    python tools\\check_runtime_palette.py --json output\\runtime_palette.json

Exit 0 when all three hold, 1 otherwise, and it always prints the count of design colours that have no legal output so
a red run says how big the job is.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGN = os.path.join("data", "palette.json")
MASTER = os.path.join("data", "nes_palette.json")
TABLE = os.path.join("data", "palette_ppu.json")
RUNTIME = os.path.join("game", "scripts", "pp_data", "pp_data.gml")
RUNTIME_NAME = "palette_ppu.json"


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

    counts = {"colours": len(colours), "mapped": len(mapping), "legal": len(colours) - off, "off": off,
              "runtime_reads": bool(names_it)}
    return problems, rows, counts


def report(rows: list, counts: dict, problems: list) -> int:
    print("runtime palette: %d colour(s) in data/palette.json, %d mapped in %s, %d resolved to a 2C02 output, %d not"
          % (counts["colours"], counts["mapped"], TABLE.replace(os.sep, "/"), counts["legal"], counts["off"]))
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
