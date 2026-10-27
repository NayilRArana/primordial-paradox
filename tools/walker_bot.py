"""The walker bot: a line by line simulation of the free 8 direction walk with wall sliding.

Card LD-2 (map audit). This is the same simulation tests/test_move_hold.py pins, kept here so the audit tool and the
bot share one copy. The numbers are read from the shipped GML (game/scripts/pp_overworld/pp_overworld.gml and
game/scripts/pp_config/pp_config.gml), not retyped: PP_TILE 16, the feet box is 10x6 at the bottom middle of the 16x16
figure, a blocked push is nudged round a corner by up to PP_CORNER_NUDGE 3 pixels, and a walk is 2 px a step
(120 px a second at 60 steps a second).

The GML resolves a step one axis at a time (X then Y), so a wall is slid along instead of stuck on. This file models
that exactly, including the per axis nudge, so the bot's "stuck frame" log measures the shipped behaviour, not a
simplified grid walk.
"""

from __future__ import annotations

import math

TILE = 16
FEET_W = 10
FEET_H = 6
CORNER = 3
WALK_STEP = 2.0  # PP_WALK_SPEED 120 / PP_STEPS_PER_SECOND 60
RUN_STEP = 200.0 / 60.0


def collision_value(collision, tx, ty):
    """The collision byte at a tile: 0 walkable, 1 blocked, 2 story blocked. Off map is 1 (blocked)."""
    if tx < 0 or ty < 0 or ty >= len(collision) or tx >= len(collision[ty]):
        return 1
    ch = collision[ty][tx]
    if ch == "1":
        return 1
    if ch == "2":
        return 2
    return 0


def feet_box(px, py):
    """pp_world_feet_box: 10x6 at the bottom middle of the 16x16 figure, inclusive pixel bounds."""
    x1 = px + (TILE - FEET_W) / 2.0
    y1 = py + TILE - FEET_H
    return (x1, y1, x1 + FEET_W - 1, y1 + FEET_H - 1)


def blocked(collision, px, py, actors=()):
    """pp_world_blocked: any tile the feet box touches that is not walkable, or an actor's tile."""
    x1, y1, x2, y2 = feet_box(px, py)
    for ty in range(int(math.floor(y1 / TILE)), int(math.floor(y2 / TILE)) + 1):
        for tx in range(int(math.floor(x1 / TILE)), int(math.floor(x2 / TILE)) + 1):
            if collision_value(collision, tx, ty) != 0:
                return True
            if (tx, ty) in actors:
                return True
    return False


def nudge(collision, px, py, vx, vy, actors=()):
    """pp_world_nudge: the sideways offset (up to 3 px) that lets a blocked push through, or 0."""
    push_x = vx != 0
    for k in range(1, CORNER + 1):
        for side in (-1, 1):
            ox = 0 if push_x else side * k
            oy = side * k if push_x else 0
            if not blocked(collision, px + ox, py + oy, actors) and not blocked(
                    collision, px + ox + vx, py + oy + vy, actors):
                return oy if push_x else ox
    return 0


def tile_at(px, py):
    """pp_world_tile_at: the tile the FEET stand on, read from the feet's centre."""
    return (int(math.floor((px + TILE * 0.5) / TILE)),
            int(math.floor((py + TILE - FEET_H * 0.5) / TILE)))


def free_step(collision, px, py, wx, wy, actors=(), running=False):
    """pp_world_free_step: returns (new_px, new_py, moved, hit_x, hit_y). One axis at a time, then a nudge each."""
    if wx == 0 and wy == 0:
        return px, py, 0.0, False, False

    speed = RUN_STEP if running else WALK_STEP
    length = math.hypot(wx, wy)
    vx = (wx / length) * speed
    vy = (wy / length) * speed

    moved_x = 0.0
    moved_y = 0.0
    hit_x = False
    hit_y = False

    if vx != 0:
        if not blocked(collision, px + vx, py, actors):
            px += vx
            moved_x = vx
        else:
            hit_x = True
    if vy != 0:
        if not blocked(collision, px, py + vy, actors):
            py += vy
            moved_y = vy
        else:
            hit_y = True

    if hit_x:
        offset = nudge(collision, px, py, vx, 0, actors)
        if offset != 0:
            py += offset
            px += vx
            moved_x = vx
            moved_y = offset
            hit_x = False
            hit_y = False
    if hit_y:
        offset = nudge(collision, px, py, 0, vy, actors)
        if offset != 0:
            px += offset
            py += vy
            moved_x = offset
            moved_y = vy
            hit_y = False

    return px, py, math.hypot(moved_x, moved_y), hit_x, hit_y


# ---------------------------------------------------------------------------------------------------------------------
# The bot: sweep every walkable tile, hold every direction, log frames the walker stops against nothing visible.

DIRECTIONS = (
    (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1),
)
DIR_NAMES = {
    (1, 0): "right", (1, 1): "down_right", (0, 1): "down", (-1, 1): "down_left",
    (-1, 0): "left", (-1, -1): "up_left", (0, -1): "up", (1, -1): "up_right",
}


def sweep_snags(collision, walkables, actors=(), frames=40, min_stuck=2):
    """Press a diagonal into every concave corner and report the corners where the wall slide sticks.

    A concave corner is a walkable tile whose diagonal neighbour is walkable but whose two axis neighbours are walled,
    i.e. the only way through is diagonally and the 10x6 feet box cannot fit without the 3 px nudge. The walker is then
    simulated pressing the diagonal for `frames` steps; a corner is a snag when it piles up `min_stuck` or more
    consecutive zero movement frames, which is the nudge failing on a lip deeper than it can clear (playbook rule 4c).
    A flat wall or a room corner has no walkable diagonal ahead, so neither is tested. Returns
    (tx, ty, dir_name, stuck_frames) for the approach tile.
    """
    walk_set = set(walkables)
    actor_set = set(actors)
    diagonals = ((1, 1), (1, -1), (-1, 1), (-1, -1))
    snags = []
    for tx, ty in walkables:
        if (tx, ty) in actor_set:
            continue
        for (dx, dy) in diagonals:
            diag = (tx + dx, ty + dy)
            ax1 = (tx + dx, ty)
            ax2 = (tx, ty + dy)
            if diag not in walk_set or diag in actor_set:
                continue
            if ax1 in walk_set or ax2 in walk_set:
                continue
            px = tx * TILE
            py = ty * TILE
            cpx, cpy = px, py
            run = 0
            best = 0
            for _ in range(frames):
                cpx, cpy, moved, _, _ = free_step(collision, cpx, cpy, dx, dy, actor_set)
                if moved <= 0:
                    run += 1
                    if run > best:
                        best = run
                else:
                    run = 0
            if best >= min_stuck:
                snags.append((tx, ty, DIR_NAMES[(dx, dy)], best))
    return snags
