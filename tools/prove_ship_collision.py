#!/usr/bin/env python3
"""prove_ship_collision.py: the identical-collision proof of the ship restyle (SHIP-RESTYLE).

Compares ship_small and ship_cabin in data/maps/all.json against data/ship_restyle_baseline.json (a copy of HEAD at the
start of the card) on width, height, collision, triggers, spawns and actors, and against `git show HEAD:` when git is
there; also checks that every other room is byte for byte the HEAD room. Exit 1 and a cell list on any difference.
"""
import io, json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS = ("width", "height", "collision", "triggers", "spawns", "actors", "rails", "music", "story_flag", "room_palette", "palette_indices", "id", "name")
ROOMS = ("ship_small", "ship_cabin")


def rooms(path_or_text, is_text=False):
    text = path_or_text if is_text else io.open(path_or_text, encoding="utf-8-sig").read()
    return {m["id"]: m for m in json.loads(text.lstrip("﻿"))["maps"]}


def diffs(old, new):
    out = []
    for k in KEYS:
        if old.get(k) != new.get(k):
            if k == "collision":
                for y, (a, b) in enumerate(zip(old[k], new[k])):
                    out += ["collision (%d,%d): %s -> %s" % (x, y, p, q) for x, (p, q) in enumerate(zip(str(a), str(b))) if p != q]
                if len(old[k]) != len(new[k]):
                    out.append("collision row count differs")
            else:
                out.append("%s differs: %r -> %r" % (k, old.get(k), new.get(k)))
    return out


def main():
    cur = rooms(os.path.join(ROOT, "data", "maps", "all.json"))
    bad = []
    base = json.load(io.open(os.path.join(ROOT, "data", "ship_restyle_baseline.json"), encoding="utf-8"))["rooms"]
    for rid in ROOMS:
        bad += ["[baseline] %s: %s" % (rid, d) for d in diffs(base[rid], cur[rid])]
    try:
        raw = subprocess.check_output(["git", "show", "HEAD:projects/primordial-paradox/data/maps/all.json"], cwd=ROOT, stderr=subprocess.DEVNULL).decode("utf-8")
        head = rooms(raw, True)
        for rid in ROOMS:
            bad += ["[HEAD] %s: %s" % (rid, d) for d in diffs(head[rid], cur[rid])]
        for rid, room in head.items():
            if rid not in ROOMS and cur.get(rid) != room:
                bad.append("[HEAD] room %s differs from HEAD (this card must not touch it)" % rid)
        mode = "baseline + git HEAD"
    except Exception:
        mode = "baseline only (git not available)"
    if bad:
        print("DIFFERENCE (%s):\n%s" % (mode, "\n".join(bad[:40])))
        return 1
    print("identical: width, height, collision, triggers, spawns, actors, rails of %s match (%s)" % (", ".join(ROOMS), mode))
    return 0


if __name__ == "__main__":
    sys.exit(main())
