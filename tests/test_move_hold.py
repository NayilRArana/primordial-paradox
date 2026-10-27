"""Free movement in eight directions, in pixels (spec 04 rule 1, card PP-FREE-MOVE).

Why this file exists: Nayil's order of 2026-10-26 was "The grid movement is too rigid. This ain't pokemon. Most games
nowadays let you hold down and right to go diagonally." The walker used to finish every tile and to read a trigger, an
actor and a wall off "the next tile"; he now walks in pixels, in eight directions, collides with a 10x6 box at the feet
one axis at a time so a wall is slid along, and reads what is in front of the feet rather than what is in the next tile.
This file replaces the hold to walk tests of card t_771e78ef, because the tile walk they measured is gone.

GameMaker is installed on this PC but a GML module cannot be called from pytest, so the frame behaviour is proved two
ways and neither one is a story about the code:

  1. A simulation drives the SHIPPED numbers and the SHIPPED input table. `pp_input_table()` in
     game/scripts/pp_input/pp_input.gml is parsed for which key belongs to which action, every speed and every size is
     read out of game/scripts/pp_config/pp_config.gml, and the simulation is a line by line model of
     `pp_world_free_step` (the unit vector, the speed, the X then Y resolution, the corner nudge, the tile read from the
     feet). So "holding down and right for 60 frames covers the ground holding right covers" is arithmetic over the
     project's own numbers, and it moves the day a macro moves.
  2. The GML the simulation is a model of is pinned as text: the axis order, the nudge call, the entry test, the reach
     box, the snap a scripted move takes, and the two modules' one reader rule for keys and axes.

Sources this file measures, never restates: game/scripts/pp_overworld/pp_overworld.gml,
game/scripts/pp_input/pp_input.gml, game/scripts/pp_config/pp_config.gml, specs/04-overworld-rails-and-triggers.md.

No test here reads the network, opens a window, writes a data file or needs a key.
"""

from __future__ import annotations

import io
import json
import math
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERWORLD_GML = os.path.join(ROOT, "game", "scripts", "pp_overworld", "pp_overworld.gml")
INPUT_GML = os.path.join(ROOT, "game", "scripts", "pp_input", "pp_input.gml")
CONFIG_GML = os.path.join(ROOT, "game", "scripts", "pp_config", "pp_config.gml")
SPEC_04 = os.path.join(ROOT, "specs", "04-overworld-rails-and-triggers.md")
PLAY_DEMO = os.path.join(ROOT, "tools", "play_demo.py")
MAPS_JSON = os.path.join(ROOT, "data", "maps", "all.json")


def _read(path: str) -> str:
    with io.open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def code_only(text: str) -> str:
    """Drop `//` comments, so a structural check reads code and never the prose about it."""
    return "\n".join(line[:line.find("//")] if "//" in line else line for line in text.split("\n"))


def brace_block(text: str, marker: str) -> str:
    """The brace balanced block that starts at the first `{` at or after `marker`."""
    start = text.index(marker)
    open_index = text.index("{", start)
    depth = 0
    for index in range(open_index, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[open_index:index + 1]
    raise AssertionError("unbalanced block after %r" % marker)


def function_body(path: str, name: str) -> str:
    return brace_block(code_only(_read(path)), "function %s(" % name)


def macro(name: str) -> int:
    """One integer macro from pp_config.gml, read from the file the game is compiled from."""
    match = re.search(r"^#macro\s+%s\s+(-?\d+)\s*$" % re.escape(name), code_only(_read(CONFIG_GML)), re.M)
    assert match is not None, "pp_config.gml defines no integer macro %s" % name
    return int(match.group(1))


def macro_text(name: str) -> str:
    """The right hand side of one macro, as written, so an expression macro can be compared with itself."""
    match = re.search(r"^#macro\s+%s\s+(.+?)\s*$" % re.escape(name), code_only(_read(CONFIG_GML)), re.M)
    assert match is not None, "pp_config.gml defines no macro %s" % name
    return match.group(1)


# ---------------------------------------------------------------------------------------------------------------------
# The numbers, read from the file the game is built from

PP_STEPS = macro("PP_STEPS_PER_SECOND")
TILE = macro("PP_TILE")
FEET_W = macro("PP_HERO_FEET_W")
FEET_H = macro("PP_HERO_FEET_H")
CORNER = macro("PP_CORNER_NUDGE")
REACH = macro("PP_REACH")
FRAME_PX = macro("PP_WALK_FRAME_PX")
FOOTSTEP_PX = macro("PP_FOOTSTEP_PX")
WALK_SPEED = macro("PP_WALK_SPEED")
RUN_SPEED = macro("PP_RUN_SPEED")
WALK_STEP = WALK_SPEED / float(PP_STEPS)
RUN_STEP = RUN_SPEED / float(PP_STEPS)
CAMERA_SMOOTH = float(macro_text("PP_CAMERA_SMOOTH"))
TALK_LOCK = macro("PP_TRIGGER_LOCK_STEPS")
MARKER_OFF = macro("PP_MARKER_RESPAWN_STEPS")
FREEZE = 0.0001


# ---------------------------------------------------------------------------------------------------------------------
# The input table, as shipped

def input_table() -> dict:
    """action id -> {kind: set(tokens)}, read from the shipped table in pp_input.gml.

    The pads are in here as their own tokens: a pad button and a keyboard key come out of `pp_input_sample` as the same
    `held` flag, so a test that drives the keys drives the d-pad as well, and a test that reads the pad rows proves the
    pad never depended on the stick.
    """
    text = code_only(_read(INPUT_GML))
    table = text[text.index("function pp_input_table"):]
    table = table[:table.index("\n}")]
    rows = {}
    for row in re.findall(r"\{[^{}]*\}", table):
        action = re.search(r'id:\s*"([a-z_]+)"', row)
        if action is None:
            continue
        kinds = {}
        for field in ("keys", "pads"):
            group = re.search(r"%s:\s*\[([^\]]*)\]" % field, row)
            kinds[field] = {part.strip() for part in group.group(1).split(",") if part.strip()} if group else set()
        rows[action.group(1)] = kinds
    for required in ("up", "down", "left", "right", "run", "confirm"):
        assert required in rows, "pp_input_table binds no %r action: %s" % (required, sorted(rows))
    return rows


def walk_vector(actions_held, stick=(0.0, 0.0)) -> tuple:
    """pp_input_update_vector's walk vector: -1, 0 or 1 each. Keys and d-pad first, then the stick's own axes."""
    if any(actions_held.get(name) for name in ("left", "right", "up", "down")):
        wx = (1 if actions_held.get("right") else 0) - (1 if actions_held.get("left") else 0)
        wy = (1 if actions_held.get("down") else 0) - (1 if actions_held.get("up") else 0)
        return wx, wy
    deadzone = 0.35
    wx = int(math.copysign(1, stick[0])) if abs(stick[0]) > deadzone else 0
    wy = int(math.copysign(1, stick[1])) if abs(stick[1]) > deadzone else 0
    return wx, wy


# ---------------------------------------------------------------------------------------------------------------------
# The simulation: pp_world_free_step, and the entry and camera rules around it

def feet_box(px, py) -> tuple:
    """pp_world_feet_box: 10x6 at the bottom middle of the 16x16 figure, inclusive pixel bounds."""
    x1 = px + (TILE - FEET_W) / 2.0
    y1 = py + TILE - FEET_H
    return x1, y1, x1 + FEET_W - 1, y1 + FEET_H - 1


def blocked(grid, actors, px, py) -> bool:
    """pp_world_blocked: any tile the feet box touches that is not walkable, or an actor's tile."""
    x1, y1, x2, y2 = feet_box(px, py)
    for ty in range(int(math.floor(y1 / TILE)), int(math.floor(y2 / TILE)) + 1):
        for tx in range(int(math.floor(x1 / TILE)), int(math.floor(x2 / TILE)) + 1):
            if not grid(tx, ty):
                return True
            if (tx, ty) in actors:
                return True
    return False


def nudge(grid, actors, px, py, vx, vy) -> float:
    """pp_world_nudge: the sideways offset that lets a blocked push through, nearest first, or 0."""
    push_x = vx != 0
    for k in range(1, CORNER + 1):
        for side in (-1, 1):
            ox = 0 if push_x else side * k
            oy = side * k if push_x else 0
            if not blocked(grid, actors, px + ox, py + oy) and not blocked(
                    grid, actors, px + ox + vx, py + oy + vy):
                return oy if push_x else ox
    return 0


def tile_at(px, py) -> tuple:
    """pp_world_tile_at: the tile the FEET stand on, not the tile the sprite's top left is in."""
    return (int(math.floor((px + TILE * 0.5) / TILE)),
            int(math.floor((py + TILE - FEET_H * 0.5) / TILE)))


class Walker:
    """The hero, the triggers he has entered and the camera, as pp_overworld_step drives them."""

    def __init__(self, grid, actors=(), start=(0, 0), triggers=None, map_pixels=None, frame=(256, 240)):
        self.grid = grid
        self.actors = set(actors)
        self.px = start[0] * TILE
        self.py = start[1] * TILE
        self.tx, self.ty = start
        self.enter = (self.tx, self.ty)
        self.facing = "down"
        self.face_x = 0
        self.face_y = 0
        self.walking = False
        self.walk_px = 0.0
        self.walk_anim = 0
        self.step_px = 0.0
        self.smooth = bool(map_pixels)
        self.map_pixels = map_pixels or (frame[0], frame[1])
        self.frame = frame
        self.cam_x = max(0.0, min(self.px + TILE * 0.5 - frame[0] * 0.5,
                                  max(0, self.map_pixels[0] - frame[0])))
        self.cam_y = max(0.0, min(self.py + TILE * 0.5 - frame[1] * 0.5,
                                  max(0, self.map_pixels[1] - frame[1])))
        self.triggers = dict(triggers or {})
        self.marker_off = {}
        self.fires = []
        self.visited = []
        self.cam_x_trail = []

    # -- the facing rule (pp_world_face_input)
    def face_input(self, wx, wy):
        changed_x = wx != self.face_x
        changed_y = wy != self.face_y
        if wx != 0 and (changed_x or wy == 0):
            self.facing = "right" if wx > 0 else "left"
        elif wy != 0 and (changed_y or wx == 0):
            self.facing = "down" if wy > 0 else "up"
        self.face_x = wx
        self.face_y = wy

    def stop_walk(self):
        self.walking = False
        self.walk_anim = 0
        self.face_x = 0
        self.face_y = 0

    # -- pp_world_free_step
    def free_step(self, wx, wy, running=False):
        if wx == 0 and wy == 0:
            self.stop_walk()
            return False
        self.face_input(wx, wy)
        speed = RUN_STEP if running else WALK_STEP
        length = math.hypot(wx, wy)
        vx = (wx / length) * speed
        vy = (wy / length) * speed

        moved_x = 0.0
        moved_y = 0.0
        hit_x = hit_y = False

        if vx != 0:
            if not blocked(self.grid, self.actors, self.px + vx, self.py):
                self.px += vx
                moved_x = vx
            else:
                hit_x = True
        if vy != 0:
            if not blocked(self.grid, self.actors, self.px, self.py + vy):
                self.py += vy
                moved_y = vy
            else:
                hit_y = True

        if hit_x:
            offset = nudge(self.grid, self.actors, self.px, self.py, vx, 0)
            if offset != 0:
                self.py += offset
                self.px += vx
                moved_x = vx
                moved_y = offset
        if hit_y:
            offset = nudge(self.grid, self.actors, self.px, self.py, 0, vy)
            if offset != 0:
                self.px += offset
                self.py += vy
                moved_x = offset
                moved_y = vy

        distance = math.hypot(moved_x, moved_y)
        if distance <= 0:
            self.stop_walk()
            return False

        self.walking = True
        self.walk_px += distance
        self.walk_anim = int(math.floor(self.walk_px / FRAME_PX)) % 2
        self.step_px += distance
        if self.step_px >= FOOTSTEP_PX:
            self.step_px -= FOOTSTEP_PX
        self.tx, self.ty = tile_at(self.px, self.py)
        return True

    # -- the entry test, the marker and the camera, in pp_overworld_step's order
    def step(self, held_tokens, stick=(0.0, 0.0)):
        table = input_table()
        actions = {name: bool(row["keys"] & held_tokens) for name, row in table.items()}
        wx, wy = walk_vector(actions, stick)
        self.visited.append((self.px, self.py))
        self.free_step(wx, wy, running=actions.get("run", False))
        self.tx, self.ty = tile_at(self.px, self.py)
        entered = (self.tx, self.ty) != self.enter
        self.enter = (self.tx, self.ty)
        if entered:
            trigger = self.triggers.get((self.tx, self.ty))
            if trigger is not None and trigger == "marker":
                key = (self.tx, self.ty)
                if key not in self.marker_off:
                    self.marker_off[key] = MARKER_OFF
                    self.fires.append(key)
        # the marker's respawn counter, counted down at the top of the next step as pp_overworld_step does
        for key in list(self.marker_off):
            self.marker_off[key] -= 1
            if self.marker_off[key] <= 0:
                del self.marker_off[key]
        self.camera_step()
        return self

    def camera_step(self):
        """pp_overworld_camera_step: pinned to his pixel while he walks, an eased settle while he stands."""
        target_x = max(0.0, min(self.px + TILE * 0.5 - self.frame[0] * 0.5,
                                max(0, self.map_pixels[0] - self.frame[0])))
        target_y = max(0.0, min(self.py + TILE * 0.5 - self.frame[1] * 0.5,
                                max(0, self.map_pixels[1] - self.frame[1])))
        if self.walking:
            self.cam_x = math.floor(target_x)
            self.cam_y = math.floor(target_y)
            self.cam_x_trail.append(self.cam_x)
            return
        self.cam_x += (target_x - self.cam_x) * CAMERA_SMOOTH
        self.cam_y += (target_y - self.cam_y) * CAMERA_SMOOTH
        if abs(target_x - self.cam_x) < 1:
            self.cam_x = target_x
        if abs(target_y - self.cam_y) < 1:
            self.cam_y = target_y
        self.cam_x_trail.append(self.cam_x)


def open_room(width=40, height=12):
    return lambda x, y: 0 <= x < width and 0 <= y < height


def run(walker, frames, tokens=lambda step: set(), stick=lambda step: (0.0, 0.0)):
    for step in range(1, frames + 1):
        walker.step(tokens(step), stick(step))
    return walker


def travelled(walker, start_px, start_py):
    return math.hypot(walker.px - start_px, walker.py - start_py)


# ---------------------------------------------------------------------------------------------------------------------
# 1. The numbers the walk is made of

def test_the_walk_speed_is_the_seven_and_a_half_tiles_a_second_the_tile_walk_had():
    """The card asks for the walk speed to stay close to today's 7.5 tiles a second, as a macro in pp_config.gml."""
    tiles_per_second = WALK_SPEED / float(TILE)
    assert abs(tiles_per_second - 7.5) < FREEZE, (
        "the walk is %.3f tiles a second; the card says keep it at 7.5" % tiles_per_second)
    assert macro_text("PP_WALK_STEP_PX") == "(PP_WALK_SPEED / PP_STEPS_PER_SECOND)", (
        "the per step walk speed is not derived from the per second walk speed: %s" % macro_text("PP_WALK_STEP_PX"))
    assert abs(WALK_STEP - 2.0) < FREEZE, WALK_STEP


def test_the_run_is_faster_than_the_walk_and_is_derived_the_same_way():
    assert RUN_SPEED > WALK_SPEED, (RUN_SPEED, WALK_SPEED)
    assert macro_text("PP_RUN_STEP_PX") == "(PP_RUN_SPEED / PP_STEPS_PER_SECOND)", macro_text("PP_RUN_STEP_PX")
    assert abs(RUN_STEP - RUN_SPEED / float(PP_STEPS)) < FREEZE


def test_the_feet_the_corner_and_the_reach_are_the_sizes_the_card_asked_for():
    """The card's own numbers: about 10x6 at the feet, a 3 pixel corner nudge, a short reach."""
    assert (FEET_W, FEET_H) == (10, 6), (FEET_W, FEET_H)
    assert FEET_W < TILE and FEET_H < TILE, "the feet box is bigger than a tile, so it can never fit anywhere"
    assert CORNER == 3, CORNER
    assert 0 < REACH <= TILE, "a reach of %d pixels is not a short reach, it is a tile and a half" % REACH
    assert FRAME_PX > 0 and FOOTSTEP_PX >= FRAME_PX, (FRAME_PX, FOOTSTEP_PX)
    assert 0 < CAMERA_SMOOTH <= 1, CAMERA_SMOOTH


def test_the_rail_walk_and_the_trigger_grace_are_untouched():
    """The card says the rails and the 20 step grace do not move."""
    assert macro("PP_WALK_STEPS_RAIL") == 8, "the rail walk moved; the card says it stays"
    assert TALK_LOCK == 20, "the 20 step trigger grace moved"
    assert MARKER_OFF == 30, "the marker's respawn window moved"
    config = code_only(_read(CONFIG_GML))
    assert "PP_WALK_STEPS_FREE" not in config, (
        "the tile walk's steps per tile macro is still in pp_config; the free walk is pixels now")


def test_the_run_took_the_keys_the_input_table_had_left_free():
    """The card conditions the run button on a key no other action owns. It says free, so this proves it."""
    table = input_table()
    assert table["run"]["keys"] == {"vk_shift"}, table["run"]["keys"]
    assert table["run"]["pads"] == {"gp_shoulderr"}, table["run"]["pads"]
    owners = {}
    for action, kinds in table.items():
        for token in kinds["keys"] | kinds["pads"]:
            owners.setdefault(token, []).append(action)
    shared = {token: users for token, users in owners.items() if len(users) > 1}
    assert shared == {}, "a key or button is bound to more than one action: %s" % shared
    for token in ("vk_shift", "gp_shoulderr"):
        assert owners[token] == ["run"], owners[token]


# ---------------------------------------------------------------------------------------------------------------------
# 2. The behaviour the card asks for, driven through the input table

def test_holding_down_and_right_for_sixty_frames_covers_what_holding_right_covers():
    """The card's first case, and the whole point of the order: a diagonal is not 1.41 times faster."""
    straight = run(Walker(open_room(), start=(1, 1)), 60, tokens=lambda step: {"vk_right"})
    straight_distance = travelled(straight, TILE, TILE)

    diagonal = run(Walker(open_room(), start=(1, 1)), 60, tokens=lambda step: {"vk_right", "vk_down"})
    diagonal_distance = travelled(diagonal, TILE, TILE)

    assert straight_distance > 100, straight_distance
    assert abs(diagonal_distance - straight_distance) <= 1.0, (
        "60 frames of down plus right covered %.2f px and 60 frames of right covered %.2f px"
        % (diagonal_distance, straight_distance))
    assert abs((diagonal.px - TILE) - (diagonal.py - TILE)) <= 1.0, (
        "the diagonal is not even: x moved %.2f and y moved %.2f" % (diagonal.px - TILE, diagonal.py - TILE))


def test_all_eight_directions_cost_the_same():
    """Eight directions, one speed: every pair of keys covers the same ground in the same 30 frames."""
    distances = {}
    for name, tokens in (
            ("right", {"vk_right"}), ("left", {"vk_left"}), ("up", {"vk_up"}), ("down", {"vk_down"}),
            ("up right", {"vk_right", "vk_up"}), ("up left", {"vk_left", "vk_up"}),
            ("down right", {"vk_right", "vk_down"}), ("down left", {"vk_left", "vk_down"})):
        walker = run(Walker(open_room(20, 20), start=(9, 9)), 30, tokens=lambda step, t=tokens: t)
        distances[name] = travelled(walker, 9 * TILE, 9 * TILE)
    low, high = min(distances.values()), max(distances.values())
    assert high - low <= 1.0, "the eight directions do not share one speed: %s" % (
        {name: round(value, 2) for name, value in distances.items()})
    assert abs(high - 30 * WALK_STEP) <= 1.0, distances


def test_the_left_stick_walks_and_a_corner_push_is_a_diagonal():
    """The stick goes through the same vector, and both axes past the deadzone make it eight directions too."""
    walker = run(Walker(open_room(20, 20), start=(9, 9)), 30, stick=lambda step: (0.9, 0.9))
    assert walker.px > 9 * TILE + 30, walker.px
    assert abs((walker.px - 9 * TILE) - (walker.py - 9 * TILE)) <= 1.0, (walker.px, walker.py)
    assert walker.facing in ("right", "down"), walker.facing


def test_pushing_into_a_wall_slides_along_it_instead_of_sticking():
    """The card's second case: a diagonal into a horizontal wall keeps its horizontal half."""
    grid = lambda x, y: 0 <= x < 40 and 2 <= y <= 7
    walker = Walker(grid, start=(1, 3))
    run(walker, 60, tokens=lambda step: {"vk_right", "vk_up"})
    for px, py in walker.visited:
        assert not blocked(grid, set(), px, py), "the walker stood in a wall at %.2f,%.2f" % (px, py)
    assert abs((walker.px - TILE) - 60 * WALK_STEP * math.sqrt(0.5)) <= 1.5, (
        "the vertical wall cost him his horizontal share: x moved %.2f in 60 frames, and %.2f is its share"
        % (walker.px - TILE, 60 * WALK_STEP * math.sqrt(0.5)))
    assert walker.py >= TILE + FEET_H - FREEZE, (
        "the walker's feet went into the wall row: y is %.2f" % walker.py)
    assert walker.py < 3 * TILE, "the walker never left his own row: y is %.2f" % walker.py


def test_a_wall_that_offers_no_corner_does_not_move_him_at_all():
    """A long wall is still a dead stop: nothing slides, and the walk cycle does not run while he pushes into it."""
    grid = lambda x, y: 0 <= x < 40 and 2 <= y <= 7
    walker = Walker(grid, start=(1, 3))
    run(walker, 60, tokens=lambda step: {"vk_up"})
    assert abs(walker.px - TILE) < FREEZE, "a straight push into a wall drifted him sideways: x is %.3f" % walker.px
    assert walker.py >= TILE + FEET_H - FREEZE, walker.py
    assert walker.walking is False, "the walk cycle ran while he was pinned against a wall"
    assert walker.walk_anim == 0, walker.walk_anim


def test_a_two_pixel_corner_is_nudged_round():
    """The card's third case: a push blocked by three pixels or less of corner is walked round the corner."""
    door_x = 6
    grid = lambda x, y: 0 <= x < 20 and 0 <= y < 10 and not (y == 4 and x != door_x)
    # His feet box is 95..104, so it clears the door tile (96..111) by ONE pixel and no more: the corner is what stops
    # him, and the nudge is what lets him through.
    walker = Walker(grid, start=(0, 3))
    walker.px = 92
    walker.py = 3 * TILE
    start_x = walker.px
    run(walker, 2, tokens=lambda step: {"vk_down"})
    assert abs(walker.px - start_x) <= CORNER, (
        "the nudge moved him %.2f px sideways, and the card allows %d" % (abs(walker.px - start_x), CORNER))
    assert walker.px > start_x, "the corner was not rounded: he stayed at %.2f" % walker.px
    run(walker, 30, tokens=lambda step: {"vk_down"})
    assert walker.py > 4 * TILE, (
        "he never went through the doorway: his feet are still at %.2f" % walker.py)
    assert tile_at(walker.px, walker.py)[0] == door_x, tile_at(walker.px, walker.py)


def test_a_corner_further_than_three_pixels_is_not_nudged():
    """The nudge has a limit, and this is it: four pixels short of the doorway is a wall, not a corner."""
    door_x = 6
    grid = lambda x, y: 0 <= x < 20 and 0 <= y < 10 and not (y == 4 and x != door_x)
    walker = Walker(grid, start=(0, 3))
    walker.px = 89
    walker.py = 3 * TILE
    run(walker, 30, tokens=lambda step: {"vk_down"})
    assert tile_at(walker.px, walker.py)[1] == 3, (
        "a corner %d px away was rounded anyway: he is on tile %s" % (CORNER + 1, tile_at(walker.px, walker.py)))


def test_a_trigger_rectangle_fires_once_per_entry():
    """The card's fourth case: entering is the event, standing on it is not, and every re-entry is a new one.

    The pass east is the first entry. The pass west crosses the marker's rectangle again, and the pass east crosses it a
    third time: three entries, three fires, and none of them from standing still on it for sixty frames.
    """
    grid = open_room(20, 3)
    walker = Walker(grid, start=(0, 1), triggers={(3, 1): "marker"})
    run(walker, 60, tokens=lambda step: {"vk_right"})
    assert walker.fires == [(3, 1)], walker.fires
    run(walker, 60, tokens=lambda step: set())
    assert walker.fires == [(3, 1)], "standing on a marker fired it again: %s" % walker.fires
    run(walker, 120, tokens=lambda step: {"vk_left"})
    assert walker.fires == [(3, 1), (3, 1)], "the walk back across the marker did not fire: %s" % walker.fires
    run(walker, 120, tokens=lambda step: {"vk_right"})
    assert walker.fires == [(3, 1), (3, 1), (3, 1)], "the third entry did not fire: %s" % walker.fires


def test_the_walk_cycle_is_timed_to_distance_walked_and_not_to_frames_held():
    """The card's third rule: the animation follows the feet, so a runner cycles faster and a pinned walker not at all."""
    walk = run(Walker(open_room()), 16, tokens=lambda step: {"vk_right"})
    sprint = run(Walker(open_room()), 16, tokens=lambda step: {"vk_right", "vk_shift"})
    assert walk.walk_px > 0 and sprint.walk_px > walk.walk_px, (walk.walk_px, sprint.walk_px)
    assert int(walk.walk_px // FRAME_PX) < int(sprint.walk_px // FRAME_PX), (
        "the run covered more ground but did not cycle more frames: %s vs %s" % (walk.walk_px, sprint.walk_px))


def test_the_camera_follows_a_diagonal_without_jitter():
    """The card's fifth rule: the view slides with him and never steps back and forth on the pixel grid."""
    walker = Walker(open_room(60, 20), start=(9, 9), map_pixels=(60 * TILE, 20 * TILE))
    run(walker, 90, tokens=lambda step: {"vk_right", "vk_down"})
    trail = walker.cam_x_trail
    assert trail, "no camera steps were recorded"
    for before, after in zip(trail, trail[1:]):
        assert after >= before - FREEZE, "the camera went backwards on the x axis: %.3f then %.3f" % (before, after)
        assert after - before <= WALK_STEP + FREEZE, (
            "the camera jumped %.2f px in one step, faster than the walker moves" % (after - before))
    assert trail[-1] > trail[0] + 40, "the camera did not follow him: %.2f to %.2f" % (trail[0], trail[-1])
    # Pinned, not lagged: every one of those steps is a whole pixel, which is what the map and the figures are drawn on.
    for value in trail:
        assert abs(value - round(value)) < FREEZE, (
            "the camera sat on a fraction of a pixel while he walked: %.4f" % value)


# ---------------------------------------------------------------------------------------------------------------------
# 3. The GML the simulation is a model of, pinned as text

def test_the_free_step_resolves_one_axis_at_a_time_and_nudges_each_one():
    """pp_world_free_step: X, then Y against the X result, and the nudge is asked for each axis that was blocked."""
    body = function_body(OVERWORLD_GML, "pp_world_free_step")
    x_move = body.index("_hero.px += _vx")
    y_move = body.index("_hero.py += _vy")
    assert x_move < y_move, "the free step resolves Y before X, which is not the order the simulation models"
    assert "pp_world_blocked(_world, _hero.px + _vx, _hero.py)" in body, body
    assert "pp_world_blocked(_world, _hero.px, _hero.py + _vy)" in body, (
        "the Y move is not tested against the position the X move left")
    assert "pp_world_nudge(_world, _hero.px, _hero.py, _vx, 0)" in body, body
    assert "pp_world_nudge(_world, _hero.px, _hero.py, 0, _vy)" in body, body
    assert "point_distance(0, 0, _wx, _wy)" in body, "the input pair is not normalised, so a diagonal is 1.41 x fast"
    assert "PP_RUN_STEP_PX" in body and "PP_WALK_STEP_PX" in body, body
    assert "_hero.moving" in body, "the free walk no longer refuses to run while a scripted move owns him"


def test_the_collision_is_the_feet_box_and_the_nudge_is_three_pixels():
    """pp_world_blocked and pp_world_nudge, as the card states them."""
    box = function_body(OVERWORLD_GML, "pp_world_feet_box")
    assert "PP_HERO_FEET_W" in box and "PP_HERO_FEET_H" in box, box
    assert "PP_TILE - PP_HERO_FEET_H" in box, "the feet box is not at the bottom of the figure: %s" % box
    guard = function_body(OVERWORLD_GML, "pp_world_blocked")
    assert "pp_map_walkable(_world.map, _tx, _ty)" in guard, guard
    assert "pp_overworld_actor_at(_world, _tx, _ty)" in guard, (
        "the walker no longer collides with actors, so he can walk through people")
    slide = function_body(OVERWORLD_GML, "pp_world_nudge")
    assert "while (_k <= PP_CORNER_NUDGE)" in slide, slide
    assert "PP_CORNER_NUDGE" in slide, slide


def test_the_walk_cycle_and_the_tile_are_read_from_the_distance_and_the_feet():
    """A two frame cycle timed to pixels, and `tx` / `ty` kept in step with the pixels under the feet."""
    cycle = function_body(OVERWORLD_GML, "pp_world_free_step")
    assert "_hero.walk_px += _dist" in cycle, cycle
    assert "PP_WALK_FRAME_PX" in cycle, "the cycle is not timed to distance walked"
    assert "PP_FOOTSTEP_PX" in cycle, "the footstep is no longer counted in pixels"
    sync = function_body(OVERWORLD_GML, "pp_world_sync_tile")
    assert "pp_world_tile_at(_hero.px, _hero.py)" in sync, sync
    tile = function_body(OVERWORLD_GML, "pp_world_tile_at")
    assert "PP_HERO_FEET_H" in tile, "the tile is read from the sprite rather than from the feet: %s" % tile
    face = function_body(OVERWORLD_GML, "pp_world_face_input")
    assert "_changed_x" in face and "_changed_y" in face, face


def test_a_scripted_move_snaps_the_hero_to_a_tile_before_it_walks():
    """Card rule 6: a scene that moves the hero snaps him to the nearest tile centre, then plays as before."""
    body = function_body(OVERWORLD_GML, "pp_world_start_move")
    snap = body.index("round(_hero.px / PP_TILE) * PP_TILE")
    assert "pp_world_sync_tile(_hero)" in body, body
    guard = body.index("pp_map_walkable(_world.map, _cx, _cy)")
    assert snap < guard, "the snap happens after the path is checked, so a rail can be refused for the wrong tile"
    assert "PP_WALK_STEPS_RAIL" in function_body(os.path.join(ROOT, "game", "scripts", "pp_scene", "pp_scene.gml"),
                                                 "pp_scene_command_start")


def test_the_touch_trigger_fires_on_an_entry_and_keeps_the_grace():
    """The entry is a tile the feet were not on before, and the marker memory is still written before it fires."""
    step = function_body(OVERWORLD_GML, "pp_overworld_step")
    walk = step.index("pp_world_free_step(_world)")
    entry = step.index("_world.enter_tx = _world.hero.tx")
    assert walk < entry, "the entry is read before the walk moves him, so it describes the tile he left"
    assert "(_world.hero.tx != _world.enter_tx) || (_world.hero.ty != _world.enter_ty)" in step, step
    marker = step[step.index("var _here = pp_map_trigger_at"):]
    marker = marker[:marker.index('if (_world.trigger_lock <= 0')]
    assert marker.index('_world.marker_off[$ _mkey] = PP_MARKER_RESPAWN_STEPS') < marker.index(
        "pp_overworld_fire(_world, _here)"), "the marker fires before it is remembered, so it fires again"
    fire = function_body(OVERWORLD_GML, "pp_overworld_fire")
    assert "_world.trigger_lock = PP_TRIGGER_LOCK_STEPS;" in fire, fire[-400:]


def test_the_confirm_reaches_in_front_of_the_feet_and_not_the_next_tile():
    """Card rule 4: the actor and the trigger are found by a pixel box in front of the feet."""
    reach = function_body(OVERWORLD_GML, "pp_world_reach_box")
    assert "pp_world_feet_box(_hero.px, _hero.py)" in reach, reach
    assert "PP_REACH" in reach, reach
    talk = function_body(OVERWORLD_GML, "pp_overworld_actor_ahead")
    assert "pp_world_reach_box(_world.hero)" in talk, talk
    assert "pp_world_boxes_overlap" in talk, talk
    assert "_d.x" not in talk and "tx + " not in talk, (
        "the talk target is still computed as the next tile: %s" % talk)
    target = function_body(OVERWORLD_GML, "pp_overworld_confirm_target")
    assert "pp_world_reach_box(_hero)" in target, target
    assert "_far" in target, target


def test_the_confirm_is_still_a_press_and_the_actor_line_is_still_unconditional():
    """The card forbids touching the dialogue and battle input, and the proof line is what a recording is read by."""
    step = function_body(OVERWORLD_GML, "pp_overworld_step")
    assert 'if (_world.trigger_lock <= 0 && pp_pressed("confirm"))' in step, (
        "confirm is no longer a press, so a held key could open a box every step")
    assert 'if (pp_pressed("confirm")) pp_dialogue_advance(_world.dialogue);' in step
    actor_branch = step[step.index("pp_overworld_actor_ahead(_world)"):]
    actor_branch = actor_branch[:actor_branch.index("var _target = pp_overworld_confirm_target")]
    assert '"PP dialogue: "' in actor_branch, actor_branch
    assert "PP_DEBUG" not in actor_branch, "the proof line is behind the debug switch, so a release build never prints it"


def test_the_keys_and_the_axes_are_still_read_in_pp_input_alone():
    """spec 02 rule 1, unchanged by this card: one reader for keys, one reader for pad axes."""
    world = code_only(_read(OVERWORLD_GML))
    assert "gamepad_" not in world, "pp_overworld reads a pad directly (spec 02 rule 1)"
    assert "keyboard_check" not in world, "pp_overworld reads a key directly (spec 02 rule 1)"
    assert "pp_walk_x()" in world and "pp_walk_y()" in world, (
        "the overworld does not read the walk vector pp_input publishes")
    vector = function_body(INPUT_GML, "pp_input_update_vector")
    assert "_in.walk_x = _walk_x;" in vector and "_in.walk_y = _walk_y;" in vector, vector
    assert 'if (abs(_ax) > PP_STICK_DEADZONE) _walk_x = sign(_ax);' in vector, (
        "the stick's x axis no longer has to clear the deadzone on its own, so the stick cannot make a diagonal")
    init = function_body(INPUT_GML, "pp_input_init")
    assert "walk_x: 0" in init and "walk_y: 0" in init, "the input struct does not declare the walk vector"
    for action, pad in (("up", "gp_padu"), ("down", "gp_padd"), ("left", "gp_padl"), ("right", "gp_padr")):
        assert pad in _read(INPUT_GML), "the d-pad row for %s is gone: %s" % (action, pad)
        row = [line for line in _read(INPUT_GML).split("\n") if 'id: "%s"' % action in line]
        assert len(row) == 1 and pad in row[0], row


def test_the_confirm_reads_the_tile_straight_ahead_and_not_a_corner_of_the_reach_box():
    """Rule 4, at the pixel: the far end of the reach box is one point, and the box is wider than the feet.

    A 10 px feet box is surrounded by a 14 px reach box, so on a walker straddling a column boundary the far CORNER of
    the reach box falls in the next column along. Asked from the corner, a walker facing up would open a sign that is
    up and to the right of him instead of the one straight up. This drives the same arithmetic the GML runs over a
    straddling position in all four facings.
    """
    px = 5 * TILE + 6          # feet box 89..98, so the feet straddle tiles 5 and 6
    py = 3 * TILE + 2          # feet box 60..65, so the feet straddle rows 3 and 4
    x1 = px + (TILE - FEET_W) / 2.0
    y1 = py + TILE - FEET_H
    bx1, by1, bx2, by2 = x1, y1, x1 + FEET_W - 1, y1 + FEET_H - 1
    mid_x = int(math.floor((bx1 + bx2) / 2.0 / TILE))
    mid_y = int(math.floor((by1 + by2) / 2.0 / TILE))
    assert int(math.floor(bx2 / TILE)) != mid_x and int(math.floor(by2 / TILE)) != mid_y, (
        "this position does not straddle a boundary, so the test would prove nothing")

    def far_tile(facing):
        """pp_overworld_confirm_target, as the GML computes the far point."""
        if facing == "left":
            return int(math.floor((x1 - REACH) / TILE)), mid_y
        if facing == "right":
            return int(math.floor((bx2 + REACH) / TILE)), mid_y
        if facing == "up":
            return mid_x, int(math.floor((by1 - REACH) / TILE))
        return mid_x, int(math.floor((by2 + REACH) / TILE))

    feet_tile = tile_at(px, py)
    up, down = far_tile("up"), far_tile("down")
    right, left = far_tile("right"), far_tile("left")
    # The axis that is not the facing axis is the MIDDLE of the box, never its far corner.
    assert up[0] == mid_x and down[0] == mid_x, (up, down, mid_x)
    assert right[1] == mid_y and left[1] == mid_y, (right, left, mid_y)
    assert up[0] != int(math.floor(bx2 / TILE)) and right[1] != int(math.floor(by2 / TILE)), (
        "the corner and the middle are the same tile here, so this test would prove nothing")
    # And the facing axis really does reach past the feet, in the way he is facing.
    assert up[1] < feet_tile[1] <= down[1], (up, down, feet_tile)
    assert left[0] < feet_tile[0] <= right[0], (left, right, feet_tile)

    target = function_body(OVERWORLD_GML, "pp_overworld_confirm_target")
    assert "_mid_x" in target and "_mid_y" in target, (
        "the far end of the reach box is read from a corner again: %s" % target)
    assert "_d.x == 0" in target and "_d.y == 0" in target, target


def test_the_camera_step_is_the_smoothed_follow_and_the_snap_is_still_named():
    """pp_overworld_camera_step smooths, floors nothing, and snaps its last pixel; the snap keeps its own function."""
    smooth = function_body(OVERWORLD_GML, "pp_overworld_camera_step")
    assert "lerp(_world.cam_x, _target_x, PP_CAMERA_SMOOTH)" in smooth, smooth
    assert "lerp(_world.cam_y, _target_y, PP_CAMERA_SMOOTH)" in smooth, smooth
    assert "if (abs(_target_x - _world.cam_x) < 1) _world.cam_x = _target_x;" in smooth, (
        "the camera never snaps its last pixel, so it lags by a pixel forever")
    assert "if (_world.hero.walking == true)" in smooth and "_world.cam_x = floor(_target_x);" in smooth, (
        "the camera is not pinned to the walker's own pixel while he walks, so it lags him and the figure bobs: %s"
        % smooth)
    clock = function_body(OVERWORLD_GML, "pp_overworld_clock_step")
    assert "pp_overworld_camera_step(_world)" in clock, clock
    assert "floor(_world.cam_x)" in function_body(OVERWORLD_GML, "pp_overworld_draw"), (
        "the draw does not floor the camera, so it spends fractions of a pixel")


def test_the_figures_and_the_markers_land_on_whole_pixels_with_the_map():
    """Rule 5's other half, and the one a screenshot shows: a float camera must not put a sprite between pixels.

    pp_art_draw hands its coordinate straight to draw_sprite_part_ext, so a hero drawn at `px - cam_x` sits a fraction
    of a pixel off while the tiles behind him are drawn from a floored camera. That does not read as a smooth walk: the
    figure shimmers against a grid that is standing still. So the figure is floored and the camera is floored, both
    separately, and his offset from the map depends only on the pixel he has walked onto.
    """
    art = function_body(os.path.join(ROOT, "game", "scripts", "pp_art", "pp_art.gml"), "pp_art_draw")
    assert "floor(" not in art and "round(" not in art, (
        "pp_art_draw now rounds for its caller, so this test no longer measures the two draw callers: %s" % art)

    hero = function_body(OVERWORLD_GML, "pp_overworld_draw_hero")
    assert "var _sx = floor(_hero.px) - floor(_world.cam_x) + _ox;" in hero, hero
    assert "var _sy = floor(_hero.py) - floor(_world.cam_y) + _oy;" in hero, hero
    actor = function_body(OVERWORLD_GML, "pp_overworld_draw_actors")
    assert "var _sx = floor(_a.px) - floor(_world.cam_x) + _ox;" in actor, actor
    assert "var _sy = floor(_a.py) - floor(_world.cam_y) + _oy;" in actor, actor

    draw = function_body(OVERWORLD_GML, "pp_overworld_draw")
    assert "- _world.cam_x" not in draw and "- _world.cam_y" not in draw, (
        "a marker or the map is still drawn against the unfloored camera: %s" % draw)

    # And the arithmetic: over a diagonal walk in a room too big to clamp the view, the figure holds ONE screen pixel
    # while the world slides under him. Any other answer is the bob the card calls jitter.
    walker = Walker(open_room(60, 60), start=(9, 9), map_pixels=(60 * TILE, 60 * TILE))
    drawn = []
    for step in range(90):
        walker.step({"vk_right", "vk_down"})
        drawn.append((int(math.floor(walker.px)) - int(math.floor(walker.cam_x)),
                      int(math.floor(walker.py)) - int(math.floor(walker.cam_y))))
    assert len({x for x, y in drawn}) == 1, (
        "the figure moved on screen while the map slid: x offsets %s" % sorted({x for x, y in drawn}))
    assert len({y for x, y in drawn}) == 1, (
        "the figure moved on screen while the map slid: y offsets %s" % sorted({y for x, y in drawn}))
    assert walker.px > 9 * TILE + 100, "he did not actually walk: %.2f" % walker.px


def test_the_spec_carries_nayils_words_this_date_and_this_card():
    spec = _read(SPEC_04)
    assert "EIGHT directions" in spec, "spec 04 does not state the eight direction rule"
    assert "This ain't pokemon" in spec, "spec 04 does not quote the order it changed on"
    assert "PP-FREE-MOVE" in spec and "2026-10-26" in spec, "the spec change carries no card or date"
    for macro_name in ("PP_WALK_SPEED", "PP_CORNER_NUDGE", "PP_REACH", "PP_CAMERA_SMOOTH", "PP_WALK_STEPS_RAIL"):
        assert macro_name in spec, "spec 04 does not name %s" % macro_name
    assert "Out of scope: NPC pathfinding" in spec, "diagonals are still listed out of scope"


# ---------------------------------------------------------------------------------------------------------------------
# 4. What the card says must not move

def test_the_rail_move_keeps_its_tile_path_and_its_speed():
    """The scene runner still asks for PP_WALK_STEPS_RAIL, and the rail still refuses a diagonal."""
    scene = code_only(_read(os.path.join(ROOT, "game", "scripts", "pp_scene", "pp_scene.gml")))
    assert "PP_WALK_STEPS_RAIL" in scene, "the scripted rail move no longer names the rail speed"
    start = function_body(OVERWORLD_GML, "pp_world_start_move")
    assert 'show_debug_message("PP: no diagonal moves");' in start, start
    assert "_hero.from_x = _hero.px;" in start and "_hero.to_x = _tx * PP_TILE;" in start, start


def test_the_demo_route_walks_the_corridor_with_one_hold_and_not_eight_taps():
    """The demo route must still reach the sailor, and under the free walk a tap is a couple of pixels, not a tile.

    Eight taps of Right, one a second, was eight tiles under the tile walk. The free walk moves him while the key is
    HELD, so the beat is one hold long enough for the 8 tiles the corridor is open for, and the confirm after it is
    pressed with the walk key already released.
    """
    with io.open(os.path.join(ROOT, "data", "demo", "run_001.json"), "r", encoding="utf-8-sig") as handle:
        route = json.load(handle)
    holds = [e for e in route["events"] if e.get("kind") == "hold" and e.get("key") == "right"]
    taps = [e for e in route["events"] if e.get("kind") == "key" and e.get("key") in ("right", "left", "up", "down")]
    assert len(holds) == 1, "the route's walk beat is not one hold: %s" % holds
    assert taps == [], "the route still walks with direction taps, and a tap moves the walker a couple of pixels"
    assert holds[0]["steps"] * WALK_STEP >= 8 * TILE, (
        "the hold is %d steps, which is %.1f px, short of the 8 tiles (128 px) the corridor is open for"
        % (holds[0]["steps"], holds[0]["steps"] * WALK_STEP))
    confirms = [e for e in route["events"] if e.get("key") == "confirm"]
    assert confirms, "the route no longer presses confirm on the sailor"
    assert confirms[0]["step"] >= holds[0]["step"] + holds[0]["steps"], (
        "the confirm fires while the walk key is still down, so the press would land on a walker that is still moving")


def test_play_demo_can_hold_a_key_because_the_route_needs_one():
    """play_demo's event kinds carry the hold, its validation refuses a beat that lands inside one, and it looks at the
    shipped script the route is written in."""
    text = _read(PLAY_DEMO)
    assert 'if kind not in ("key", "hold", "note")' in text, "play_demo validates no hold event"
    assert 'if event["kind"] == "hold":' in text, "play_demo replays no hold event"
    assert "cap.send_vk_down(cap.KEY_CODES[event[\"key\"]])" in text, text[-2000:]
    assert "busy_until" in text, "a beat can still fire inside a hold, while the key is down"


def test_the_ship_deck_gives_a_held_walk_eight_tiles_east_before_the_sailor_stops_it():
    """The run room is a corridor, so the walker stops at the first actor: that is the count a capture can read.

    The take kept on 2026-10-26 shows 8 footsteps, and 8 is exactly the open run east of the spawn: tiles 3 to 10, with
    the navy_sailor standing on 11,7. So this pins the map, and it also pins the HOLD the route needs now that the walk
    is free: 8 tiles is 128 pixels, which is 64 frames at 2 pixels a frame, where eight taps of a key would cover 16.
    """
    with io.open(MAPS_JSON, "r", encoding="utf-8-sig") as handle:
        maps = json.load(handle)["maps"]
    ship = [row for row in maps if row.get("id") == "ship_small"][0]
    spawn = ship["spawns"]["start"]
    actors = {(actor["x"], actor["y"]): actor["id"] for actor in ship.get("actors") or []}
    assert (spawn["x"], spawn["y"]) == (2, 7), "the run no longer starts where the capture starts"
    x, y = spawn["x"], spawn["y"]
    crossed = 0
    while True:
        x += 1
        if not 0 <= x < ship["width"]:
            stopped_by = "the edge of the map at %d,%d" % (x, y)
            break
        if str(ship["collision"][y][x]) != "0":
            stopped_by = "a blocked tile at %d,%d" % (x, y)
            break
        if (x, y) in actors:
            stopped_by = "the actor %r at %d,%d" % (actors[(x, y)], x, y)
            break
        crossed += 1
    assert (crossed, stopped_by) == (8, "the actor 'navy_sailor' at 11,7"), (crossed, stopped_by)
    frames = int(round(crossed * TILE / WALK_STEP))
    assert frames == 64, "the hold that crosses the open run is %d frames, not 64" % frames
