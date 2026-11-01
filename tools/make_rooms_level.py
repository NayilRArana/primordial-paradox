#!/usr/bin/env python3
"""make_rooms_level.py: the level design pass for the small rooms (card LD-3, 2026-10-27).

ship_small is NOT touched: tests/test_ship_deck.py and test_save_gameover.py pin its tiles and the hatch. ship_cabin: the two sealed bunk booths are opened so no floor tile is unreachable. quay_dock_office: the
desk edge that made a corner snag with Dylan is opened. Idempotent: every edit sets a cell to a fixed value.
Row 7 of the deck, the tutorial, hound and Percy triggers, the log door at 3,6 and the save at 3,2 are untouched,
so the recorded tape (data/demo/run_002.json) still walks the same tiles.

The write splices the two edited rooms into the file text and nothing else, the rule tools/make_quay_town.py
follows: a json.dump of the whole document reformats every room's tile_legend and buries the seven changed cells
in a two thousand line diff.
"""
import io, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS = os.path.join(ROOT, "data", "maps", "all.json")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import make_quay_town as qt  # noqa: E402


def setcell(room, x, y, ch, coll):
    row = list(room["tiles"][y]); row[x] = ch; room["tiles"][y] = "".join(row)
    row = list(str(room["collision"][y])); row[x] = str(coll); room["collision"][y] = "".join(row)


def edits(by):
    """The fixed cells of the pass, applied in place. Returns the room ids it touched, in the order it touched them."""
    touched = []
    c = by["ship_cabin"]
    for x in (6, 7, 8, 9):
        setcell(c, x, 12, ".", 0)                            # the lower booth opens to the south corridor
    setcell(c, 8, 3, ".", 0)                                 # the upper booth door is two wide
    touched.append(c["id"])
    o = by["quay_dock_office"]
    setcell(o, 12, 8, "#", 1); setcell(o, 11, 8, "#", 1)   # desk edge: the gap under Dylan is two wide, no corner snag
    touched.append(o["id"])
    return touched


def main():
    with io.open(MAPS, "r", encoding="utf-8-sig") as f:
        text = f.read()
    by = {m["id"]: m for m in json.loads(text)["maps"]}
    touched = edits(by)
    before = text
    for rid in touched:
        text, exact = qt.splice_room(text, rid, by[rid])
        if not exact:
            print("note: the old %s text is not reproduced exactly by json.dumps(indent=2); only this room's own "
                  "formatting may differ" % rid)
    if text != before:
        with io.open(MAPS, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    print("make_rooms_level: %s %s" % (", ".join(touched),
                                       "updated" if text != before else "already as the pass sets them"))


if __name__ == "__main__":
    sys.exit(main())
