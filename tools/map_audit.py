"""Map audit: measure why the current maps feel janky, room by room (card LD-2).

Reads data/maps/all.json and, for every room, builds the walkability grid from the collision layer and reports:

  1. unreachable walkable tiles (playbook rule 4a: flood fill from every entrance),
  2. single tile gaps and pinch corridors (rule 4b),
  3. snag corners where the free 8 direction walk with wall sliding sticks (rule 4c, via tools/walker_bot.py),
  4. dead ends without a reward (a degree 1 tile with no point of interest on it or beside it),
  5. doors and transitions that do not match on both sides (rule 5),
  6. the longest walk without a point of interest (rule 1).

It also writes one overlay PNG per room under output/map_audit/ and a machine readable report at
output/map_audit/report.json. It changes nothing: every room, tile and collision stays as authored.

Run:  python tools/map_audit.py
"""

from __future__ import annotations

import json
import os
from collections import deque

from walker_bot import collision_value, sweep_snags

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS_JSON = os.path.join(ROOT, "data", "maps", "all.json")
OUT_DIR = os.path.join(ROOT, "output", "map_audit")
REPORT_JSON = os.path.join(OUT_DIR, "report.json")

POI_KINDS = {"say", "battle", "scene", "map", "save", "flag", "marker"}


def load_maps():
    with open(MAPS_JSON, "r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data["maps"]


def room_walkables(room):
    """Set of walkable tiles (collision 0)."""
    collision = room["collision"]
    out = set()
    for ty in range(room["height"]):
        for tx in range(room["width"]):
            if collision_value(collision, tx, ty) == 0:
                out.add((tx, ty))
    return out


def room_story_blocked(room):
    """Set of story blocked tiles (collision 2)."""
    collision = room["collision"]
    out = set()
    for ty in range(room["height"]):
        for tx in range(room["width"]):
            if collision_value(collision, tx, ty) == 2:
                out.add((tx, ty))
    return out


def room_spawns(room):
    return [(s["x"], s["y"]) for s in room.get("spawns", {}).values()]


def room_triggers(room):
    return [(t["x"], t["y"], t.get("kind", ""), t.get("id", "")) for t in room.get("triggers", [])]


def room_actors(room):
    return [(a["x"], a["y"]) for a in room.get("actors", [])]


def room_poi(room):
    """Point of interest tiles: every trigger and every actor."""
    poi = {(t[0], t[1]) for t in room_triggers(room)}
    poi.update(room_actors(room))
    return poi


def room_doors(room):
    """Door (map) triggers: (tx, ty, target_id, spawn_name)."""
    doors = []
    for t in room.get("triggers", []):
        if t.get("kind") == "map":
            doors.append((t["x"], t["y"], t.get("id", ""), t.get("spawn", "start")))
    return doors


def tile_kind(room, tx, ty):
    """The legend word for a tile ('floor', 'wall', 'door', 'hatch', ...). Off map reads as wall."""
    legend = room.get("tile_legend", {})
    tiles = room["tiles"]
    if tx < 0 or ty < 0 or ty >= len(tiles) or tx >= len(tiles[ty]):
        return "wall"
    return legend.get(tiles[ty][tx], "wall")


# ---------------------------------------------------------------------------------------------------------------------
# The six checks

def reachable_set(room):
    """Walkable tiles reachable from any spawn, flood filled over 4 connectivity."""
    walkables = room_walkables(room)
    spawns = room_spawns(room)
    reachable = set()
    queue = deque()
    for s in spawns:
        if s in walkables:
            reachable.add(s)
            queue.append(s)
    while queue:
        tx, ty = queue.popleft()
        for nx, ny in ((tx + 1, ty), (tx - 1, ty), (tx, ty + 1), (tx, ty - 1)):
            if (nx, ny) in walkables and (nx, ny) not in reachable:
                reachable.add((nx, ny))
                queue.append((nx, ny))
    return reachable


def check_reachability(room):
    walkables = room_walkables(room)
    reachable = reachable_set(room)
    unreachable = sorted(walkables - reachable)
    by_kind = {}
    for t in unreachable:
        by_kind[tile_kind(room, t[0], t[1])] = by_kind.get(tile_kind(room, t[0], t[1]), 0) + 1
    return {"unreachable_count": len(unreachable), "unreachable": [list(t) for t in unreachable],
            "unreachable_by_kind": by_kind}


def check_readability(room):
    """Rule 6: a blocked tile that looks walkable, or a walkable tile that looks like a wall.

    A door or hatch drawn as such is meant to be confirmed rather than walked onto, so a blocked door tile is not a
    readability bug; only a blocked FLOOR tile (an invisible wall) and a walkable WALL tile (a wall you fall through)
    are flagged.
    """
    collision = room["collision"]
    phantom_wall = []   # collision 0 but drawn as wall
    blocked_floor = []  # collision 1 but drawn as floor
    for ty in range(room["height"]):
        for tx in range(room["width"]):
            cval = collision_value(collision, tx, ty)
            kind = tile_kind(room, tx, ty)
            if cval == 0 and kind == "wall":
                phantom_wall.append([tx, ty])
            elif cval == 1 and kind == "floor":
                blocked_floor.append([tx, ty])
    return {"phantom_wall": phantom_wall, "blocked_floor": blocked_floor}


def check_pinches(room):
    walkables = room_walkables(room)
    pinch = []
    dead_ends = []
    for tx, ty in walkables:
        nbrs = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (tx + dx, ty + dy) in walkables:
                nbrs.append((dx, dy))
        deg = len(nbrs)
        if deg < 2:
            pinch.append((tx, ty))
            if deg == 1:
                dead_ends.append((tx, ty))
        elif deg == 2:
            # a 1 wide corridor: the two neighbours sit on one axis (opposite directions)
            (dx1, dy1), (dx2, dy2) = nbrs
            if dx1 == -dx2 and dy1 == -dy2:
                pinch.append((tx, ty))
    return {"pinch_count": len(pinch), "pinch": [list(t) for t in sorted(pinch)],
            "dead_end_count": len(dead_ends), "dead_ends": [list(t) for t in sorted(dead_ends)]}


def check_dead_ends(room):
    walkables = room_walkables(room)
    poi = room_poi(room)
    unrewarded = []
    for tx, ty in walkables:
        nbrs = [(tx + dx, ty + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if (tx + dx, ty + dy) in walkables]
        if len(nbrs) != 1:
            continue
        zone = {(tx, ty)} | set(nbrs)
        if not (zone & poi):
            unrewarded.append((tx, ty))
    return {"unrewarded_dead_ends": [list(t) for t in sorted(unrewarded)]}


def check_snags(room):
    reachable = reachable_set(room)
    actor_tiles = set(room_actors(room))
    # Only tiles the walker can legally stand on: reachable, and not an actor's tile.
    starts = sorted(reachable - actor_tiles)
    snags = sweep_snags(room["collision"], starts, actors=actor_tiles)
    return {"snag_count": len(snags), "snags": [{"tile": [s[0], s[1]], "dir": s[2], "stuck_frames": s[3]} for s in snags]}


def check_doors(room, rooms_by_id):
    findings = []
    for tx, ty, target_id, spawn_name in room_doors(room):
        door = {"from": room["id"], "tile": [tx, ty], "target": target_id, "spawn": spawn_name}
        if target_id not in rooms_by_id:
            findings.append({"kind": "dangling_door", **door,
                             "note": "target map %r is not in data/maps/all.json" % target_id})
            continue
        target = rooms_by_id[target_id]
        spawn = target.get("spawns", {}).get(spawn_name) or target.get("spawns", {}).get("start")
        if spawn is None:
            findings.append({"kind": "missing_spawn", **door,
                             "note": "target %r has no spawn %r" % (target_id, spawn_name)})
            continue
        lx, ly = spawn["x"], spawn["y"]
        landing_value = collision_value(target["collision"], lx, ly)
        if landing_value != 0:
            findings.append({"kind": "landing_blocked", **door, "landing": [lx, ly],
                             "note": "landing collision %r" % landing_value})
        # landing must face open space: at least one orthogonal neighbour walkable
        target_walk = room_walkables(target)
        open_nbrs = [(lx + dx, ly + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                     if (lx + dx, ly + dy) in target_walk]
        if not open_nbrs:
            findings.append({"kind": "landing_boxed", **door, "landing": [lx, ly],
                             "note": "landing has no walkable neighbour"})
        # symmetry: does the target carry a door back that lands beside this door?
        back_doors = [d for d in room_doors(target) if d[2] == room["id"]]
        if back_doors:
            back_spawns = []
            for btx, bty, _, bspawn in back_doors:
                bs = room.get("spawns", {}).get(bspawn)
                if bs:
                    back_spawns.append((bs["x"], bs["y"]))
            min_gap = min((max(abs(bx - tx), abs(by - ty)) for bx, by in back_spawns), default=None)
            if min_gap is None or min_gap > 1:
                findings.append({"kind": "asymmetric_door", **door,
                                 "note": "return door lands %s tiles from this door" % (min_gap)})
        else:
            findings.append({"kind": "one_way_door", **door,
                             "note": "target %r has no door back to %r" % (target_id, room["id"])})
    return findings


def check_poi_spacing(room):
    walkables = room_walkables(room)
    poi = room_poi(room) & walkables
    if not poi:
        return {"longest_walk": None, "over_8": [], "poi_count": 0}
    # BFS distance from the POI set over the walkable graph
    dist = {}
    queue = deque()
    for p in poi:
        dist[p] = 0
        queue.append(p)
    while queue:
        tx, ty = queue.popleft()
        d = dist[(tx, ty)]
        for nx, ny in ((tx + 1, ty), (tx - 1, ty), (tx, ty + 1), (tx, ty - 1)):
            if (nx, ny) in walkables and (nx, ny) not in dist:
                dist[(nx, ny)] = d + 1
                queue.append((nx, ny))
    longest = max(dist.values()) if dist else 0
    over_8 = sorted((t for t, d in dist.items() if d > 8), key=lambda t: -dist[t])
    return {"longest_walk": longest, "over_8": [list(t) for t in over_8],
            "poi_count": len(poi), "max_dist": longest}


def check_spawns(room):
    walkables = room_walkables(room)
    bad = [list(s) for s in room_spawns(room) if s not in walkables]
    return {"blocked_spawns": bad}


def check_markers(room):
    """A marker fires on touch, so it must sit on a walkable tile."""
    walkables = room_walkables(room)
    bad = [[t[0], t[1]] for t in room_triggers(room) if t[2] == "marker" and (t[0], t[1]) not in walkables]
    return {"blocked_markers": bad}


# ---------------------------------------------------------------------------------------------------------------------
# Overlay

def render_overlay(room, findings, out_path):
    from PIL import Image, ImageDraw

    w, h = room["width"], room["height"]
    scale = max(1, min(8, 512 // max(w, h)))
    collision = room["collision"]

    walkables = room_walkables(room)
    story = room_story_blocked(room)
    spawns = set(room_spawns(room))
    poi = room_poi(room)
    doors = {(d[0], d[1]) for d in room_doors(room)}

    unreachable = set()
    for f in findings:
        if f["kind"] == "reachability":
            unreachable.update(map(tuple, f.get("unreachable", [])))
    snags = set()
    for f in findings:
        if f["kind"] == "snag":
            snags.update((s["tile"][0], s["tile"][1]) for s in f.get("snags", []))
    dead = set()
    for f in findings:
        if f["kind"] == "dead_end":
            dead.update(map(tuple, f.get("unrewarded_dead_ends", [])))

    legend_h = 16
    img = Image.new("RGB", (w * scale, h * scale + legend_h), (20, 20, 20))
    draw = ImageDraw.Draw(img)

    colours = {
        "blocked": (42, 42, 42),
        "story": (70, 90, 180),
        "walk": (232, 232, 232),
        "unreach": (220, 60, 60),
        "snag": (255, 140, 0),
        "dead": (220, 200, 0),
    }
    for ty in range(h):
        for tx in range(w):
            cval = collision_value(collision, tx, ty)
            if cval == 2:
                col = colours["story"]
            elif cval == 1:
                col = colours["blocked"]
            elif (tx, ty) in unreachable:
                col = colours["unreach"]
            elif (tx, ty) in snags:
                col = colours["snag"]
            elif (tx, ty) in dead:
                col = colours["dead"]
            else:
                col = colours["walk"]
            draw.rectangle([tx * scale, ty * scale, tx * scale + scale - 1, ty * scale + scale - 1], fill=col)

    # markers
    def marker(t, col, inset=0):
        x, y = t
        draw.rectangle([x * scale + inset, y * scale + inset, x * scale + scale - 1 - inset,
                        y * scale + scale - 1 - inset], fill=col)

    for p in poi:
        if p in doors:
            marker(p, (0, 190, 190), inset=scale // 4)
        else:
            marker(p, (70, 200, 90), inset=scale // 3)
    for s in spawns:
        marker(s, (255, 255, 255), inset=scale // 3)

    # legend
    items = [("walk", colours["walk"]), ("blocked", colours["blocked"]), ("story(2)", colours["story"]),
             ("unreachable", colours["unreach"]), ("snag", colours["snag"]), ("dead-end", colours["dead"]),
             ("door", (0, 190, 190)), ("POI", (70, 200, 90)), ("spawn", (255, 255, 255))]
    lx = 4
    ly = h * scale + 3
    for label, col in items:
        draw.rectangle([lx, ly, lx + 8, ly + 8], fill=col)
        draw.text((lx + 11, ly - 2), label, fill=(220, 220, 220))
        lx += 11 + len(label) * 6 + 10

    img.save(out_path)
    return out_path


# ---------------------------------------------------------------------------------------------------------------------
# Report and main

def audit_room(room, rooms_by_id):
    findings = []
    findings.append({"kind": "reachability", **check_reachability(room)})
    findings.append({"kind": "readability", **check_readability(room)})
    findings.append({"kind": "pinch", **check_pinches(room)})
    dead = check_dead_ends(room)
    findings.append({"kind": "dead_end", **dead})
    snags = check_snags(room)
    findings.append({"kind": "snag", **snags})
    findings.extend(check_doors(room, rooms_by_id))
    findings.append({"kind": "poi_spacing", **check_poi_spacing(room)})
    findings.append({"kind": "spawns", **check_spawns(room)})
    findings.append({"kind": "markers", **check_markers(room)})
    return findings


def problem_score(findings):
    weights = {
        "unreachable": 5, "pinch": 3, "snag": 4, "dead_end": 2, "dangling_door": 6,
        "missing_spawn": 6, "landing_blocked": 5, "landing_boxed": 4, "asymmetric_door": 4,
        "one_way_door": 1, "poi_spacing": 2, "blocked_spawns": 5, "blocked_markers": 4,
    }
    score = 0
    for f in findings:
        kind = f["kind"]
        if kind == "reachability":
            score += weights["unreachable"] * max(0, f.get("unreachable_count", 0))
        elif kind == "snag":
            score += weights["snag"] * max(0, f.get("snag_count", 0))
        elif kind == "pinch":
            score += weights["pinch"] * len(f.get("pinch", []))
        elif kind == "dead_end":
            score += weights["dead_end"] * len(f.get("unrewarded_dead_ends", []))
        elif kind == "poi_spacing":
            longest = f.get("longest_walk")
            if longest is not None:
                score += weights["poi_spacing"] * max(0, longest - 8)
        elif kind == "spawns":
            score += weights["blocked_spawns"] * len(f.get("blocked_spawns", []))
        elif kind == "markers":
            score += weights["blocked_markers"] * len(f.get("blocked_markers", []))
        elif kind == "readability":
            score += 2 * (len(f.get("phantom_wall", [])) + len(f.get("blocked_floor", [])))
        else:
            score += weights.get(kind, 1)
    return score


def write_markdown(report):
    md_path = os.path.join(ROOT, "knowledge", "MAP-AUDIT.md")
    lines = []
    add = lines.append

    add("# MAP-AUDIT")
    add("")
    add("Card LD-2. Every room in data/maps/all.json measured against the walkability rules, with the evidence that")
    add("says why the current maps feel janky. Generated by tools/map_audit.py; nothing here changes a room, a tile or")
    add("a collision, those fixes are card LD-3.")
    add("")
    add("## Method")
    add("")
    add("Each room gets a walkability grid from its collision layer, then six checks:")
    add("")
    add("1. Unreachable walkable tiles: flood fill from every entrance over 4 connectivity; any walkable tile the fill")
    add("   does not reach is floor the player can see but never stand on (playbook rule 4a).")
    add("2. Single tile gaps and pinch corridors: walkable tiles with fewer than two neighbours, or exactly two on one")
    add("   axis (a one cell wide corridor), plus dead ends (rule 4b).")
    add("3. Snag corners: a walker bot (tools/walker_bot.py) presses a diagonal into every concave corner and reports")
    add("   the corners where the wall slide sticks, i.e. the 3 px nudge cannot clear the lip (rule 4c).")
    add("4. Dead ends without a reward: a dead end with no point of interest on it or beside it.")
    add("5. Doors and transitions that do not match on both sides (rule 5).")
    add("6. Longest walk without a point of interest, BFS from every trigger and actor (rule 1).")
    add("")
    add("The score ranks rooms by total problem weight; a higher number is more janky. The overlay marks reachable, blocked,")
    add("unreachable, snag and dead end tiles.")

    for m in report["maps"]:
        add("")
        add("## %s (%s) - score %d" % (m["name"], m["id"], m["score"]))
        add("")
        add("Overlay: %s" % m["overlay"])
        add("")
        items = []
        for f in m["findings"]:
            kind = f["kind"]
            if kind == "reachability" and f["unreachable_count"]:
                by_kind = ", ".join("%s %s" % (v, k) for k, v in sorted(f["unreachable_by_kind"].items()))
                items.append("- Unreachable walkable tiles: %d (%s)." % (f["unreachable_count"], by_kind))
            elif kind == "pinch" and f.get("pinch"):
                items.append("- Pinch tiles (single tile gaps and one cell corridors): %d." % len(f["pinch"]))
            elif kind == "snag" and f["snag_count"]:
                items.append("- Snag corners: %d." % f["snag_count"])
            elif kind == "dead_end" and f.get("unrewarded_dead_ends"):
                items.append("- Dead ends with no reward: %d." % len(f["unrewarded_dead_ends"]))
            elif kind in ("dangling_door", "missing_spawn", "landing_blocked", "landing_boxed",
                          "asymmetric_door", "one_way_door"):
                items.append("- %s: %s (tile %s, target %s)." % (kind, f.get("note", ""), f.get("tile"), f.get("target")))
            elif kind == "poi_spacing" and f.get("longest_walk") is not None:
                items.append("- Longest walk without a point of interest: %d tiles (threshold 8)." % f["longest_walk"])
            elif kind == "readability":
                if f.get("phantom_wall"):
                    items.append("- Walkable tiles drawn as wall: %d." % len(f["phantom_wall"]))
                if f.get("blocked_floor"):
                    items.append("- Blocked tiles drawn as floor: %d." % len(f["blocked_floor"]))
            elif kind == "spawns" and f.get("blocked_spawns"):
                items.append("- Blocked spawns: %d." % len(f["blocked_spawns"]))
            elif kind == "markers" and f.get("blocked_markers"):
                items.append("- Touch markers on blocked tiles: %d." % len(f["blocked_markers"]))
        if items:
            for it in items:
                add(it)
        else:
            add("- No findings.")
    add("")
    with open(md_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return md_path


def main():
    maps = load_maps()
    rooms_by_id = {m["id"]: m for m in maps}
    os.makedirs(OUT_DIR, exist_ok=True)

    report = {"maps": []}
    for room in maps:
        findings = audit_room(room, rooms_by_id)
        overlay = os.path.join(OUT_DIR, "%s.png" % room["id"])
        render_overlay(room, findings, overlay)
        report["maps"].append({
            "id": room["id"],
            "name": room["name"],
            "width": room["width"],
            "height": room["height"],
            "walkable": len(room_walkables(room)),
            "score": problem_score(findings),
            "overlay": os.path.relpath(overlay, ROOT),
            "findings": findings,
        })

    report["maps"].sort(key=lambda m: -m["score"])

    with open(REPORT_JSON, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    md_path = write_markdown(report)

    # human summary
    print("map_audit: %d rooms, report %s" % (len(report["maps"]), REPORT_JSON))
    print("map_audit: markdown %s" % md_path)
    for m in report["maps"]:
        print("\n== %s (%s) %dx%d  walkable=%d  score=%d" %
              (m["id"], m["name"], m["width"], m["height"], m["walkable"], m["score"]))
        for f in m["findings"]:
            kind = f["kind"]
            if kind == "reachability" and f["unreachable_count"]:
                print("  unreachable walkable tiles: %d" % f["unreachable_count"])
            elif kind == "pinch" and f.get("pinch"):
                print("  pinch tiles: %d" % len(f["pinch"]))
            elif kind == "snag" and f["snag_count"]:
                print("  snag corners: %d" % f["snag_count"])
            elif kind == "dead_end" and f.get("unrewarded_dead_ends"):
                print("  unrewarded dead ends: %d" % len(f["unrewarded_dead_ends"]))
            elif kind in ("dangling_door", "missing_spawn", "landing_blocked", "landing_boxed",
                          "asymmetric_door", "one_way_door"):
                print("  %s: %s" % (kind, f.get("note", "")))
            elif kind == "poi_spacing" and f.get("longest_walk") is not None:
                print("  longest walk without a POI: %d tiles (threshold 8)" % f["longest_walk"])
            elif kind == "readability":
                if f.get("phantom_wall"):
                    print("  walkable tiles drawn as wall: %d" % len(f["phantom_wall"]))
                if f.get("blocked_floor"):
                    print("  blocked tiles drawn as floor/door: %d" % len(f["blocked_floor"]))
            elif kind == "spawns" and f.get("blocked_spawns"):
                print("  blocked spawns: %d" % len(f["blocked_spawns"]))
            elif kind == "markers" and f.get("blocked_markers"):
                print("  markers on blocked tiles: %d" % len(f["blocked_markers"]))


if __name__ == "__main__":
    main()
