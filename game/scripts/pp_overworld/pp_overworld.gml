/// pp_overworld: the walker, the triggers, the markers and the scene that plays over the map (spec 04).
/// The player walks FREE, in pixels, in eight directions, the way this genre's modern games move: a held direction
/// becomes a unit vector, the vector becomes pixels at PP_WALK_SPEED, and collision is a 10x6 box at
/// the feet resolved one axis at a time so a wall is slid along instead of stuck on. Order Nayil gave on 2026-10-26
/// (card PP-FREE-MOVE): "The grid movement is too rigid. This ain't pokemon. Most games nowadays let you hold down and
/// right to go diagonally." A scripted move (a scene rail) is still a TILE path at PP_WALK_STEPS_RAIL, and it snaps the
/// walker to the nearest tile centre before it runs, so every scene, cutscene and demo beat plays as it always did.
/// Triggers are inert for 20 steps after a scene or battle; story blocked tiles open with a flag. Nothing here reads a
/// key or an axis directly, only pp_input.
/// Saving is here in two shapes (spec 11 rule 4): every map entry arms one silent autosave, which pp_overworld_step
/// releases once the fade is done and no scene owns the screen, and a trigger of kind `save` writes at a save point
/// the player confirms, printing the ship's log line that names the point.
/// Provenance: knowledge\PROVENANCE.md, entry "room and object conventions across a whole game", written before the
/// notice of 2026-10-19 and re-confirmed by the clean-room re-review of the same date. One map state carries the
/// walker, the scene and the fade; a battle is a mode swap asked for here and performed by pp_app (specs 01 and 04).

/// A fresh overworld on a map and spawn point.
function pp_overworld_new(_map_id, _spawn_name) {
    var _map = pp_map_load(_map_id);
    if (is_undefined(_map)) return undefined;
    var _spawn = pp_map_spawn_point(_map, _spawn_name);

    var _world = {
        map: _map,
        hero: pp_overworld_hero(_spawn.x, _spawn.y),
        actors: {},
        scene: undefined,
        dialogue: undefined,
        trigger_lock: PP_TRIGGER_LOCK_STEPS,
        marker_off: {},
        // The tile the feet stood on last step (card PP-FREE-MOVE rule 5). A touch trigger fires when the feet ENTER its
        // tile, so the tile he is standing on has to be remembered to tell an entry from a standstill: without it, a
        // walker standing still on a marker would fire it again the step its respawn counter ran out.
        enter_tx: _spawn.x,
        enter_ty: _spawn.y,
        cam_x: 0,
        cam_y: 0,
        camera_follow: true,
        cam_pan: undefined,
        fade: undefined,
        // The world's own frame clock, counted by pp_overworld_step and handed to pp_map_draw, which reads it for the
        // animated tiles. It is declared here because the first draw of any overworld reads it: a missing key ends the
        // game on the first frame (card FIRST-FIGHT-WIRE, measured in build/first_fight_game.log at pp_overworld_draw 478).
        steps: 0,
        shake_steps: 0,
        shake_strength: 0,
        // The whole screen flash a scene's `flash` command asks for (card t_531bc76c): frames left to draw and the
        // role the frame is flooded with. Declared here for the same reason `steps` is: the first draw of any overworld
        // reads its keys, and a missing one ends the game on that frame.
        flash_steps: 0,
        flash_role: "paper",
        music: "",
        sfx: "",
        battle_request: "",
        battle_done: "",
        spawn_name: _spawn_name,
        map_changes: 0
    };
    pp_overworld_camera_follow(_world);

    // Spec 11 rule 4: entering a map saves once, silently, after the fade in. The arm carries the map the player
    // actually stands on; pp_save_autosave_step waits for the fade, and for any scene that opens here to finish.
    pp_save_autosave_arm(_map.id);

    // Story actors placed by the map data (card ASSEMBLE). One sailor on the lower deck is the first of them.
    // They are read from the map, never hardcoded here, so a new NPC is a data edit and not a code edit.
    if (is_array(_map.actors)) {
        for (var _i = 0; _i < array_length(_map.actors); _i += 1) {
            var _a = _map.actors[_i];
            _world.actors[$ string(_a.id)] = {
                name: _a.id,
                kind: _a.kind,
                dialogue: _a.dialogue,
                facing: _a.facing,
                tx: _a.x,
                ty: _a.y,
                px: _a.x * PP_TILE,
                py: _a.y * PP_TILE,
                walk: 0
            };
        }
    }
    return _world;
}

function pp_overworld_hero(_tx, _ty) {
    return {
        tx: _tx,
        ty: _ty,
        px: _tx * PP_TILE,
        py: _ty * PP_TILE,
        facing: "down",
        // `moving` is what it always was: a SCRIPTED move owns him until it lands. The free walk does not set it (a
        // scene that waits for a rail would then wait for the player), so it has its own three keys below.
        moving: false,
        // The free walk's own state (card PP-FREE-MOVE): `walking` is the draw's question, `walk_px` is the distance
        // walked that times the two frame cycle, `walk_anim` is the frame it lands on, `step_px` is the distance since
        // the last footstep, and face_x / face_y are the input signs of the step before, which is what the facing rule
        // compares against to decide which component just changed.
        walking: false,
        walk_px: 0,
        walk_anim: 0,
        step_px: 0,
        face_x: 0,
        face_y: 0,
        from_x: _tx * PP_TILE,
        from_y: _ty * PP_TILE,
        to_x: _tx * PP_TILE,
        to_y: _ty * PP_TILE,
        steps: 0,
        total: 1
    };
}

/// Direction name to a unit vector. An unknown name is a stop, not a guess.
function pp_world_dir_vector(_dir) {
    switch (_dir) {
        case "up":    return { x: 0, y: -1 };
        case "down":  return { x: 0, y: 1 };
        case "left":  return { x: -1, y: 0 };
        case "right": return { x: 1, y: 0 };
    }
    show_debug_message("PP: unknown direction " + string(_dir));
    return { x: 0, y: 0 };
}

// ---------------------------------------------------------------------------------------------------------------
// The feet, the walls and the walk (card PP-FREE-MOVE). Everything below is in PIXELS: the walker's own position is
// `px` / `py` at the top left of his 16x16 figure, the tile he stands on is read off his feet, and the only thing the
// tiles are asked is whether a tile may be walked on.

/// The tile the feet stand on. The feet are the bottom middle of the figure, so the tile is read from the feet's own
/// centre and a walker straddling a boundary belongs to the tile his feet are most in, which is also the tile a trigger
/// on that boundary fires from.
function pp_world_tile_at(_px, _py) {
    return {
        x: floor((_px + PP_TILE * 0.5) / PP_TILE),
        y: floor((_py + PP_TILE - PP_HERO_FEET_H * 0.5) / PP_TILE)
    };
}

/// Keep `tx` / `ty` (what the triggers, the actors, the save file and every log line read) in step with the pixels.
function pp_world_sync_tile(_hero) {
    var _t = pp_world_tile_at(_hero.px, _hero.py);
    _hero.tx = _t.x;
    _hero.ty = _t.y;
}

/// The collision hitbox: 10x6 at the bottom middle of the figure, in pixels. Inclusive bounds, so it is exactly
/// PP_HERO_FEET_W by PP_HERO_FEET_H pixels and never a pixel more.
function pp_world_feet_box(_px, _py) {
    var _x1 = _px + (PP_TILE - PP_HERO_FEET_W) * 0.5;
    var _y1 = _py + PP_TILE - PP_HERO_FEET_H;
    return { x1: _x1, y1: _y1, x2: _x1 + PP_HERO_FEET_W - 1, y2: _y1 + PP_HERO_FEET_H - 1 };
}

/// True when the feet box would overlap a blocked tile or an actor if the figure stood at this position. The map is
/// asked per TILE (pp_map_walkable), which is the same collision grid every rail and every data checker already reads.
function pp_world_blocked(_world, _px, _py) {
    var _b = pp_world_feet_box(_px, _py);
    var _tx1 = floor(_b.x1 / PP_TILE);
    var _tx2 = floor(_b.x2 / PP_TILE);
    var _ty1 = floor(_b.y1 / PP_TILE);
    var _ty2 = floor(_b.y2 / PP_TILE);
    for (var _ty = _ty1; _ty <= _ty2; _ty += 1) {
        for (var _tx = _tx1; _tx <= _tx2; _tx += 1) {
            if (!pp_map_walkable(_world.map, _tx, _ty)) return true;
            if (!is_undefined(pp_overworld_actor_at(_world, _tx, _ty))) return true;
        }
    }
    return false;
}

/// The sideways offset, up to PP_CORNER_NUDGE pixels, that lets a blocked push go through; 0 when no offset within
/// reach makes the move legal (card PP-FREE-MOVE rule 2). The offset is tried nearest first and on both sides, and the
/// step onto the offset is tested as well as the move itself, so a nudge can never put the feet box somewhere the walk
/// could not have reached. A long wall offers no offset at all, which is why this costs nothing on a straight wall.
function pp_world_nudge(_world, _px, _py, _vx, _vy) {
    var _push_x = (_vx != 0);
    var _k = 1;
    var _s = -1;
    while (_k <= PP_CORNER_NUDGE) {
        _s = -1;
        while (_s <= 1) {
            var _ox = _push_x ? 0 : _s * _k;
            var _oy = _push_x ? _s * _k : 0;
            if (_s != 0
                && !pp_world_blocked(_world, _px + _ox, _py + _oy)
                && !pp_world_blocked(_world, _px + _ox + _vx, _py + _oy + _vy)) {
                return _push_x ? _oy : _ox;
            }
            _s += 2;
        }
        _k += 1;
    }
    return 0;
}

/// The facing rule for a free walk (card PP-FREE-MOVE rule 3): four directions for the sheet, and the component that
/// CHANGED this step wins. So a diagonal held from the start faces its horizontal half and keeps that face while both
/// keys stay down, adding the other axis turns him once, and letting one axis go leaves him facing the one still held.
function pp_world_face_input(_hero, _wx, _wy) {
    var _changed_x = (_wx != _hero.face_x);
    var _changed_y = (_wy != _hero.face_y);
    if (_wx != 0 && (_changed_x || _wy == 0)) {
        _hero.facing = (_wx > 0) ? "right" : "left";
    } else if (_wy != 0 && (_changed_y || _wx == 0)) {
        _hero.facing = (_wy > 0) ? "down" : "up";
    }
    _hero.face_x = _wx;
    _hero.face_y = _wy;
}

/// He is not walking this step: the cycle goes back to its standing frame, and the facing rule forgets which way the
/// input was pushing so the next push counts as a change.
function pp_world_stop_walk(_hero) {
    _hero.walking = false;
    _hero.walk_anim = 0;
    _hero.face_x = 0;
    _hero.face_y = 0;
}

/// One step of free movement (card PP-FREE-MOVE). The input pair becomes a UNIT vector, the unit vector becomes pixels
/// at the walk speed (or the run speed while run is held), and the pixels are resolved ONE AXIS AT A TIME: the X move is
/// tried against the position the figure stands at, then the Y move against the X result. That order is the whole
/// reason a wall is slid along instead of stuck on, because a blocked axis simply stays where it was while the other
/// one keeps its share of the step.
function pp_world_free_step(_world) {
    var _hero = _world.hero;
    // A scripted move owns him: a held key must never fight a scene's rail.
    if (_hero.moving) return false;

    var _wx = pp_walk_x();
    var _wy = pp_walk_y();
    if (_wx == 0 && _wy == 0) {
        pp_world_stop_walk(_hero);
        return false;
    }

    pp_world_face_input(_hero, _wx, _wy);

    // One speed in eight directions: the pair is divided by its own length, so a diagonal spends 0.7071 of a step on
    // each axis and covers the ground a straight walk covers in the same time.
    var _speed = pp_action("run") ? PP_RUN_STEP_PX : PP_WALK_STEP_PX;
    var _len = point_distance(0, 0, _wx, _wy);
    var _vx = (_wx / _len) * _speed;
    var _vy = (_wy / _len) * _speed;

    var _moved_x = 0;
    var _moved_y = 0;
    var _hit_x = false;
    var _hit_y = false;

    if (_vx != 0) {
        if (!pp_world_blocked(_world, _hero.px + _vx, _hero.py)) {
            _hero.px += _vx;
            _moved_x = _vx;
        } else {
            _hit_x = true;
        }
    }
    if (_vy != 0) {
        if (!pp_world_blocked(_world, _hero.px, _hero.py + _vy)) {
            _hero.py += _vy;
            _moved_y = _vy;
        } else {
            _hit_y = true;
        }
    }

    // A push that a corner blocks by three pixels or less is walked round instead of into.
    if (_hit_x) {
        var _nudge_y = pp_world_nudge(_world, _hero.px, _hero.py, _vx, 0);
        if (_nudge_y != 0) {
            _hero.py += _nudge_y;
            _hero.px += _vx;
            _moved_x = _vx;
            _moved_y = _nudge_y;
            _hit_x = false;
            _hit_y = false;
        }
    }
    if (_hit_y) {
        var _nudge_x = pp_world_nudge(_world, _hero.px, _hero.py, 0, _vy);
        if (_nudge_x != 0) {
            _hero.px += _nudge_x;
            _hero.py += _vy;
            _moved_x = _nudge_x;
            _moved_y = _vy;
            _hit_y = false;
        }
    }

    var _dist = point_distance(0, 0, _moved_x, _moved_y);
    if (_dist <= 0) {
        // Blocked on both axes, so the feet do not move and the cycle does not run: a walker pushed into a wall is
        // standing still with a direction held, which is not a walk.
        pp_world_stop_walk(_hero);
        return false;
    }

    _hero.walking = true;
    // The two frame cycle is timed to the PIXELS WALKED, not to the steps held (card PP-FREE-MOVE rule 3): a walker
    // pushed into a corner keeps both feet planted, and a runner cycles at the speed he is actually covering.
    _hero.walk_px += _dist;
    _hero.walk_anim = floor(_hero.walk_px / PP_WALK_FRAME_PX) mod 2;
    _hero.step_px += _dist;
    if (_hero.step_px >= PP_FOOTSTEP_PX) {
        _hero.step_px -= PP_FOOTSTEP_PX;
        pp_audio_play("footstep");
    }
    pp_world_sync_tile(_hero);
    return true;
}

/// Start a SCRIPTED move along a tile path (a scene's rail). A blocked tile stops the move where it is, and says so once.
/// Card PP-FREE-MOVE rule 6: the free walk leaves the figure anywhere in a tile, and a tile path has to start from a
/// tile, so he is snapped to the nearest tile centre first and the path is measured from there. The caller's target is
/// a DELTA from where he stood, so the same delta is applied to the tile the snap landed on: a figure nudged one tile by
/// the snap still walks the tiles the scene asked for, instead of one less.
function pp_world_start_move(_world, _tx, _ty, _steps_per_tile) {
    var _hero = _world.hero;
    if (_hero.moving) return false;
    var _delta_x = _tx - _hero.tx;
    var _delta_y = _ty - _hero.ty;
    _hero.px = round(_hero.px / PP_TILE) * PP_TILE;
    _hero.py = round(_hero.py / PP_TILE) * PP_TILE;
    pp_world_sync_tile(_hero);
    _tx = _hero.tx + _delta_x;
    _ty = _hero.ty + _delta_y;
    var _sx = sign(_tx - _hero.tx);
    var _sy = sign(_ty - _hero.ty);
    if (_tx != _hero.tx && _ty != _hero.ty) {
        show_debug_message("PP: no diagonal moves");
        return false;
    }
    // Every tile on the way must be walkable, so a rail cannot end inside a wall.
    var _cx = _hero.tx;
    var _cy = _hero.ty;
    var _guard = 0;
    while ((_cx != _tx || _cy != _ty) && _guard < 128) {
        _cx += _sx;
        _cy += _sy;
        if (!pp_map_walkable(_world.map, _cx, _cy)) {
            show_debug_message("PP: blocked move to " + string(_tx) + "," + string(_ty));
            return false;
        }
        _guard += 1;
    }
    _hero.moving = true;
    // The hero faces the way he walks, for a scene's rail move as much as for a press: pp_scene's own `move` used to
    // leave the facing where the last press put it, so a scene that walked him right left him looking left and the
    // confirm on the tile ahead read the tile behind (card t_009836b9, the deck's fight trigger).
    if (_sx != 0) {
        _hero.facing = (_sx > 0) ? "right" : "left";
    } else if (_sy != 0) {
        _hero.facing = (_sy > 0) ? "down" : "up";
    }
    // Card SFX-WIRE: a tile move shows two walk frames, so one footstep per move is one every second frame.
    pp_audio_play("footstep");
    _hero.from_x = _hero.px;
    _hero.from_y = _hero.py;
    _hero.to_x = _tx * PP_TILE;
    _hero.to_y = _ty * PP_TILE;
    _hero.tx = _tx;
    _hero.ty = _ty;
    _hero.steps = 0;
    var _dist = abs(_tx * PP_TILE - _hero.from_x) + abs(_ty * PP_TILE - _hero.from_y);
    _hero.total = max(1, (_dist / PP_TILE) * _steps_per_tile);
    return true;
}

/// One step of a scripted move; the walker stays whole pixel and finishes the tile. The free walk does NOT come through
/// here (card PP-FREE-MOVE): a rail is a tile path, and pp_scene is its only caller.
function pp_world_move_step(_world) {
    var _hero = _world.hero;
    if (!_hero.moving) return;
    _hero.steps += 1;
    _hero.walking = true;
    _hero.walk_anim = floor(_hero.steps / 4) mod 2;
    var _t = _hero.steps / _hero.total;
    if (_t >= 1) {
        _hero.px = _hero.to_x;
        _hero.py = _hero.to_y;
        _hero.moving = false;
        _hero.walking = false;
        _hero.walk_anim = 0;
        _hero.steps = _hero.total;
        pp_world_sync_tile(_hero);
        // Card SFX-WIRE: a hatch is a tile, not a trigger, so the sound fires when the hero lands on one.
        var _kind = pp_map_tile_kind(_world.map, _hero.tx, _hero.ty);
        if (string_pos("hatch", _kind) > 0) pp_audio_play("door_hatch");
        return;
    }
    _hero.px = floor(lerp(_hero.from_x, _hero.to_x, _t));
    _hero.py = floor(lerp(_hero.from_y, _hero.to_y, _t));
}

/// Ask for a whole screen flash (card t_531bc76c): N frames of the frame flooded in one role the room's palette set
/// declares. It spends no steps of the scene, because the world's own clock counts it down in pp_overworld_step; a
/// step count of zero or less asks for nothing rather than for a flash nobody can see.
function pp_world_flash(_world, _steps, _role) {
    if (!is_struct(_world)) return false;
    var _frames = round(_steps);
    if (_frames <= 0) return false;
    _world.flash_steps = min(_frames, PP_FLASH_MAX_STEPS);
    if (is_string(_role) && _role != "") _world.flash_role = _role;
    return true;
}

function pp_world_spawn_actor(_world, _name, _tx, _ty) {
    _world.actors[$ string(_name)] = { name: _name, tx: _tx, ty: _ty, px: _tx * PP_TILE, py: _ty * PP_TILE };
}

function pp_world_destroy_actor(_world, _name) {
    if (variable_struct_exists(_world.actors, string(_name))) {
        variable_struct_remove(_world.actors, string(_name));
    }
}

/// Follow the hero, clamped so the view never shows outside the map. This is the SNAP: it is called when a map loads, a
/// map is swapped and a scene hands control back, and it puts the view exactly where it belongs so nothing is seen
/// sliding into place. The per step follow is pp_overworld_camera_step.
function pp_overworld_camera_follow(_world) {
    var _map = _world.map;
    var _full = pp_map_pixel_size(_map);
    _world.cam_x = clamp(_world.hero.px + PP_TILE * 0.5 - PP_FRAME_W * 0.5, 0, max(0, _full.w - PP_FRAME_W));
    _world.cam_y = clamp(_world.hero.py + PP_TILE * 0.5 - PP_FRAME_H * 0.5, 0, max(0, _full.h - PP_FRAME_H));
}

/// The per step follow (card PP-FREE-MOVE rule 5). The target is the same clamped centre pp_overworld_camera_follow
/// computes, and there are two ways to reach it, because the two cases want opposite things:
///
/// WHILE HE WALKS the camera takes his own pixel, exactly: cam = floor(target), which is the hero's own floor less the
/// constant half tile the target adds, so the figure sits on the same screen pixel for the whole walk and the world
/// slides under him. The float camera this replaced could not do that. A lerp lags the walker by (1 - smooth) / smooth
/// of his speed, and while it lags his pixel and the camera's pixel cross their own rounding boundaries at different
/// moments, which on a diagonal (0.7071 of a step on each axis) makes the figure bob one pixel against a grid that is
/// standing still, about two frames in three. That bob is exactly the jitter the card forbids, and it is only visible
/// on the diagonals the card was written for.
///
/// WHILE HE STANDS the camera eases the rest of the way (PP_CAMERA_SMOOTH of the distance each step) and snaps the last
/// pixel, so a map load, a scene handback or a step out of a doorway slides into place instead of jumping. Nothing is
/// moving under it then, so there is no bob to make.
function pp_overworld_camera_step(_world) {
    var _map = _world.map;
    var _full = pp_map_pixel_size(_map);
    var _target_x = clamp(_world.hero.px + PP_TILE * 0.5 - PP_FRAME_W * 0.5, 0, max(0, _full.w - PP_FRAME_W));
    var _target_y = clamp(_world.hero.py + PP_TILE * 0.5 - PP_FRAME_H * 0.5, 0, max(0, _full.h - PP_FRAME_H));
    if (_world.hero.walking == true) {
        _world.cam_x = floor(_target_x);
        _world.cam_y = floor(_target_y);
        return;
    }
    _world.cam_x = lerp(_world.cam_x, _target_x, PP_CAMERA_SMOOTH);
    _world.cam_y = lerp(_world.cam_y, _target_y, PP_CAMERA_SMOOTH);
    if (abs(_target_x - _world.cam_x) < 1) _world.cam_x = _target_x;
    if (abs(_target_y - _world.cam_y) < 1) _world.cam_y = _target_y;
}

/// Start a scene over the current map.
function pp_overworld_start_scene(_world, _scene_id) {
    _world.scene = pp_scene_new(_scene_id, _world);
    return _world.scene;
}

/// Start an encounter: the app owns the mode swap, the world only asks.
function pp_overworld_start_encounter(_world, _encounter_id) {
    if (_world.battle_request != "") return false;
    _world.battle_request = _encounter_id;
    // The proof line FIRST-FIGHT-WIRE asks for: one unconditional line naming the encounter, the map and the tile the
    // hero stood on when the trigger fired, so a run that reached the fight and a run that never did can be told apart
    // from the log alone. It is deliberately not behind PP_DEBUG, because the release build is where that proof is wanted.
    show_debug_message("PP: battle start " + string(_encounter_id) + " on " + string(_world.map.id)
        + " " + string(_world.hero.tx) + "," + string(_world.hero.ty));
    // Card t_009836b9: a fight the route names puts the route on that row, whichever door started it.
    pp_route_battle_started(_encounter_id);
    return true;
}

/// Called by the battle mode when it hands control back. `_handoff_scene` is the scene id the fight handed over, or ""
/// when it handed nothing over; a caller that passes three arguments passes none.
///
/// Card t_905a18ce (F2): an interrupted fight names a scene, and spec 18 section 4 step 4 says the caller continues
/// with no press, so the scene is started HERE, through the one scene door, in the same call that takes the outcome.
/// That is what makes the caller the owner of the handover instead of the fight: the battle mode clears the battle and
/// hands two values over, and this door is the only place a world's scene is replaced. The scene launched path is the
/// same door, so a scene that ran a fight gets the interruption scene in place of the runner that waited for it, which
/// is what spec 18 section 4 step 6 asks for: the fight is not resumed, and control returns to the map when the
/// interruption scene ends. Kill and spare hand nothing over, so `battle_done` still carries the word a waiting scene
/// advances on (pp_scene's `battle` state).
function pp_overworld_battle_finished(_world, _encounter_id, _outcome, _handoff_scene) {
    if (is_undefined(_world)) return;
    var _enc = pp_data_find(global.pp_data.encounters.encounters, _encounter_id);
    if (!is_undefined(_enc)) {
        var _flags = [];
        if (_outcome == "spare" && variable_struct_exists(_enc, "flags_on_spare")) _flags = _enc.flags_on_spare;
        if (_outcome == "kill" && variable_struct_exists(_enc, "flags_on_kill")) _flags = _enc.flags_on_kill;
        var _i = 0;
        while (_i < array_length(_flags)) {
            pp_ledger_set_flag(global.pp_ledger, _flags[_i], true);
            _i += 1;
        }
    }
    _world.trigger_lock = PP_TRIGGER_LOCK_STEPS;
    // Card t_009836b9: the route follows the fight out too, so the step after the demo's first fight is the save step
    // the route authors. The call sits before the handoff branch because an interrupted fight hands a scene over and
    // the route still has to move on from the fight row.
    pp_route_battle_finished(_encounter_id);

    if (!is_string(_handoff_scene) || _handoff_scene == "") {
        _world.battle_done = _outcome;
        return;
    }

    // battle_done stays empty: the outcome travelled as the scene id, and a scene still waiting on a fight must not
    // read this handover as its own result and step past the story that was just started over it.
    _world.battle_done = "";
    pp_overworld_start_scene(_world, _handoff_scene);
    // One unconditional line, like the battle start line: a run that played the middle act and a run that never did
    // can be told apart from the log alone (the same reason FIRST-FIGHT-WIRE gives).
    show_debug_message("PP: fight handed over to scene " + string(_handoff_scene) + " with no press");
}

/// A once trigger is remembered in the ledger so a door stays open across a save and load (spec 04 rule 3).
function pp_overworld_trigger_seen(_world, _trigger) {
    return pp_ledger_flag(global.pp_ledger, pp_overworld_trigger_flag(_world, _trigger));
}

function pp_overworld_trigger_flag(_world, _trigger) {
    return "trig_" + string(_world.map.id) + "_" + string(_trigger.x) + "_" + string(_trigger.y);
}

/// Fire one trigger. Unknown kinds are reported and skipped rather than silently ignored.
function pp_overworld_fire(_world, _trigger) {
    if (is_undefined(_trigger)) return;
    if (_trigger.once && pp_overworld_trigger_seen(_world, _trigger)) return;
    if (_trigger.condition != "" && !pp_ledger_flag(global.pp_ledger, _trigger.condition)) return;

    switch (_trigger.kind) {
        case "say":
            if (!pp_dialogue_closed(_world.dialogue)) return;
            _world.dialogue = pp_dialogue_open(_trigger.id);
            break;

        case "battle":
            pp_overworld_start_encounter(_world, _trigger.id);
            break;

        case "scene":
            pp_overworld_start_scene(_world, _trigger.id);
            break;

        case "map":
            var _spawn = "start";
            if (variable_struct_exists(_trigger, "spawn")) _spawn = _trigger.spawn;
            // Card SFX-WIRE: a door between maps is a hatch in the story, so it gets the hatch sound.
            pp_audio_play("door_hatch");
            pp_overworld_change_map(_world, _trigger.id, _spawn);
            break;

        case "flag":
            pp_ledger_set_flag(global.pp_ledger, _trigger.id, true);
            break;

        // A save point (spec 11 rule 4). The row's id is a label for the player's sake, not a row in any table
        // (tools/check_data.py says so where it leaves "save" out of the id tables), so it names the point in the
        // logged line and travels no further. pp_save refuses everything but a settled overworld, so a save can
        // never land mid battle, mid scene or mid dialogue, and it says so in one line when it refuses.
        case "save":
            var _label = "save";
            if (is_string(_trigger.id) && _trigger.id != "") _label = _trigger.id;
            if (pp_save_write(_label, false)) {
                // The ship's log line. One line, and it names the point, the map and the tile, so a run that saved
                // and a run that never asked can be told apart from the log alone.
                show_debug_message("PP: ship's log, " + string(_label) + ", saved on " + string(_world.map.id)
                    + " " + string(_world.hero.tx) + "," + string(_world.hero.ty));
            }
            break;

        case "marker":
            pp_overworld_start_encounter(_world, _trigger.id);
            break;

        default:
            show_debug_message("PP: unknown trigger kind " + string(_trigger.kind));
            return;
    }

    if (_trigger.once) pp_ledger_set_flag(global.pp_ledger, pp_overworld_trigger_flag(_world, _trigger), true);
    _world.trigger_lock = PP_TRIGGER_LOCK_STEPS;
}

/// Swap maps behind the app's fade, so the walker never sees the swap.
function pp_overworld_change_map(_world, _map_id, _spawn_name) {
    var _map = pp_map_load(_map_id);
    if (is_undefined(_map)) return false;
    _world.map = _map;
    var _spawn = pp_map_spawn_point(_map, _spawn_name);
    _world.hero = pp_overworld_hero(_spawn.x, _spawn.y);
    _world.spawn_name = _spawn_name;
    _world.actors = {};
    _world.scene = undefined;
    _world.cam_pan = undefined;
    _world.camera_follow = true;
    _world.map_changes += 1;
    pp_overworld_camera_follow(_world);
    pp_app_fade_in();
    // The new map is an entry too (spec 11 rule 4), so it arms its own silent save. Like the first entry, the write
    // waits for the fade this call just started.
    pp_save_autosave_arm(_map.id);
    return true;
}

/// The rectangle a confirm reaches: the feet box, extended PP_REACH pixels the way the hero faces (card PP-FREE-MOVE
/// rule 4). This is what makes the target the person or the thing in FRONT OF THE FEET rather than the next tile: a
/// walker stopped against a doorway reaches the person standing in it, and a walker still a few pixels short of a sign
/// does not.
function pp_world_reach_box(_hero) {
    var _b = pp_world_feet_box(_hero.px, _hero.py);
    var _d = pp_world_dir_vector(_hero.facing);
    var _r = { x1: _b.x1, y1: _b.y1, x2: _b.x2, y2: _b.y2 };
    if (_d.x > 0) {
        _r.x1 = _b.x2 + 1;
        _r.x2 = _r.x1 + PP_REACH - 1;
    } else if (_d.x < 0) {
        _r.x2 = _b.x1 - 1;
        _r.x1 = _r.x2 - PP_REACH + 1;
    } else if (_d.y > 0) {
        _r.y1 = _b.y2 + 1;
        _r.y2 = _r.y1 + PP_REACH - 1;
    } else if (_d.y < 0) {
        _r.y2 = _b.y1 - 1;
        _r.y1 = _r.y2 - PP_REACH + 1;
    }
    return _r;
}

/// True when two inclusive pixel rectangles overlap.
function pp_world_boxes_overlap(_a, _b) {
    return (_a.x1 <= _b.x2 && _a.x2 >= _b.x1 && _a.y1 <= _b.y2 && _a.y2 >= _b.y1);
}

/// The trigger a confirm fires (card PP-FREE-MOVE rule 4). The reach box is asked from its FAR END toward the feet, so
/// the door the player is aiming at is chosen before the one he is standing on; the tile he stands on is the last
/// chance, because a door underfoot still opens on confirm.
///
/// The far end is one point, and which of its edges is "far" depends on the way he faces: the far edge on the facing
/// axis, and the MIDDLE of the box on the other one. Reading the far corner instead would make a walker facing up ask
/// the tile above and to the right of him, so a sign one tile to the side would open before the one straight ahead
/// (the reach box is 14 px wide against a 10 px feet box, so that corner really does fall in the next column).
function pp_overworld_confirm_target(_world) {
    var _hero = _world.hero;
    var _r = pp_world_reach_box(_hero);
    var _d = pp_world_dir_vector(_hero.facing);
    var _mid_x = floor(((_r.x1 + _r.x2) * 0.5) / PP_TILE);
    var _mid_y = floor(((_r.y1 + _r.y2) * 0.5) / PP_TILE);
    var _far_x = (_d.x == 0) ? _mid_x : floor(((_d.x < 0) ? _r.x1 : _r.x2) / PP_TILE);
    var _far_y = (_d.y == 0) ? _mid_y : floor(((_d.y < 0) ? _r.y1 : _r.y2) / PP_TILE);
    var _far = pp_map_trigger_at(_world.map, _far_x, _far_y);
    if (!is_undefined(_far)) return _far;
    var _next = pp_map_trigger_at(_world.map, _hero.tx + _d.x, _hero.ty + _d.y);
    if (!is_undefined(_next)) return _next;
    return pp_map_trigger_at(_world.map, _hero.tx, _hero.ty);
}

/// The actor standing on one tile, or undefined. Used for blocking a walk into somebody.
function pp_overworld_actor_at(_world, _tx, _ty) {
    var _names = variable_struct_get_names(_world.actors);
    for (var _i = 0; _i < array_length(_names); _i += 1) {
        var _a = _world.actors[$ _names[_i]];
        if (_a.tx == _tx && _a.ty == _ty) return _a;
    }
    return undefined;
}

/// The actor the hero is facing, or undefined: whoever's own feet box the reach box touches, nearest first in the order
/// the map placed them. Talk is confirm in front of the feet, so the same key that reads a sign reads a sailor.
function pp_overworld_actor_ahead(_world) {
    var _r = pp_world_reach_box(_world.hero);
    var _names = variable_struct_get_names(_world.actors);
    for (var _i = 0; _i < array_length(_names); _i += 1) {
        var _a = _world.actors[$ _names[_i]];
        if (pp_world_boxes_overlap(_r, pp_world_feet_box(_a.px, _a.py))) return _a;
    }
    return undefined;
}

/// Step the overworld: clocks, scene, dialogue, walking, triggers.
function pp_overworld_step(_world) {
    if (is_undefined(_world)) return;

    // Clocks that run whether or not anything else does. The world clock climbs every step so the animated tiles keep
    // moving through a scene, a dialogue or a walk; pp_map_draw reads it on the same frame it is drawn.
    _world.steps += 1;
    if (_world.shake_steps > 0) _world.shake_steps -= 1;
    // The flash counts down here, at the top of the step, exactly as the shake does, so the frame that asked for it
    // draws it: N on the step it is set, N-1 on the next, and off when it reaches zero. A `flash` command spends no
    // steps of its own, so this is the only clock it has (card t_531bc76c, spec 06).
    if (_world.flash_steps > 0) _world.flash_steps -= 1;
    if (_world.trigger_lock > 0) _world.trigger_lock -= 1;

    // The entry autosave (spec 11 rule 4) is asked every step and fires exactly once per entry, on a settled screen.
    // It sits before the scene branch below, because that branch returns; the save itself refuses while a scene runs.
    pp_save_autosave_step(_world);

    // A scene owns the screen while it runs.
    if (pp_scene_running(_world.scene)) {
        pp_scene_step(_world.scene, _world);
        pp_world_move_step(_world);
        pp_overworld_clock_step(_world);

        // A scene command can ask for a fight, and the scene then waits for battle_done. The request has to be drained
        // here, inside the scene branch: the app is the only thing that swaps modes, and the older drain below is
        // unreachable while a scene runs, which would leave the scene waiting for a battle nobody starts.
        if (_world.battle_request != "") {
            var _scene_battle = _world.battle_request;
            _world.battle_request = "";
            pp_app_request(PPMode.battle, { encounter_id: _scene_battle, from_world: true });
            return;
        }

        if (!pp_scene_running(_world.scene)) {
            // Card t_009836b9: the runner is read before it is dropped, because the route hands to its row's `next`
            // only for the scene it started. This is the one place a finished scene is let go, so every way a scene
            // can end (its own `end`, a runout, the command cap) reaches the route through here.
            var _ended_scene = _world.scene;
            _world.scene = undefined;
            _world.trigger_lock = PP_TRIGGER_LOCK_STEPS;
            if (is_struct(_ended_scene)) pp_route_scene_finished(_ended_scene.id);
        }
        return;
    }
    _world.scene = undefined;

    // A dialogue opened by a `say` trigger owns the screen too.
    if (!pp_dialogue_closed(_world.dialogue)) {
        if (pp_pressed("confirm")) pp_dialogue_advance(_world.dialogue);
        pp_dialogue_step(_world.dialogue);
        if (pp_dialogue_closed(_world.dialogue)) _world.dialogue = undefined;
        pp_overworld_clock_step(_world);
        return;
    }
    _world.dialogue = undefined;

    // Ask for the battle once per request; the app performs the swap.
    if (_world.battle_request != "") {
        var _id = _world.battle_request;
        _world.battle_request = "";
        pp_app_request(PPMode.battle, { encounter_id: _id, from_world: true });
        return;
    }

    // Copy the objective marker off for its respawn window (spec 04: gone for 30 steps).
    var _names = variable_struct_get_names(_world.marker_off);
    var _n = 0;
    while (_n < array_length(_names)) {
        var _key = _names[_n];
        var _left = _world.marker_off[$ _key] - 1;
        if (_left <= 0) {
            variable_struct_remove(_world.marker_off, _key);
        } else {
            _world.marker_off[$ _key] = _left;
        }
        _n += 1;
    }

    pp_world_move_step(_world);
    if (_world.hero.moving) {
        pp_overworld_clock_step(_world);
        return;
    }

    // The free walk moves him, so the tile he stands on is read AFTER it moved: an entry is a tile the feet were not on
    // the step before (card PP-FREE-MOVE rule 5), which is what makes a marker fire once per entry instead of once per
    // step stood on it. The tile he enters is kept even when the trigger underneath turns out to be inert, so the entry
    // is not repeated when the 20 step grace or a respawn counter runs out.
    pp_world_free_step(_world);
    var _entered = (_world.hero.tx != _world.enter_tx) || (_world.hero.ty != _world.enter_ty);
    _world.enter_tx = _world.hero.tx;
    _world.enter_ty = _world.hero.ty;

    if (_entered) {
        // A hatch is a tile, not a trigger, so its sound is played when the feet arrive on one, the same rule the
        // scripted walk has always used (card SFX-WIRE).
        var _kind_here = pp_map_tile_kind(_world.map, _world.hero.tx, _world.hero.ty);
        if (string_pos("hatch", _kind_here) > 0) pp_audio_play("door_hatch");

        // A marker fires on touch, never on confirm.
        var _here = pp_map_trigger_at(_world.map, _world.hero.tx, _world.hero.ty);
        if (!is_undefined(_here) && _here.kind == "marker") {
            var _mkey = string(_here.x) + "_" + string(_here.y);
            if (!variable_struct_exists(_world.marker_off, _mkey)) {
                _world.marker_off[$ _mkey] = PP_MARKER_RESPAWN_STEPS;
                pp_overworld_fire(_world, _here);
                pp_overworld_clock_step(_world);
                return;
            }
        }
    }

    if (_world.trigger_lock <= 0 && pp_pressed("confirm")) {
        var _talk = pp_overworld_actor_ahead(_world);
        if (!is_undefined(_talk)) {
            // Card R30 (spec 19 section 2, Q5 and Q10): an actor whose id the bake carries a conversation for talks
            // from data/meta_bake.json, and any other actor keeps its authored dialogue id. One door, in
            // pp_talk_actor_open, so the map data decides who speaks and this branch decides nothing by name.
            _world.dialogue = pp_talk_actor_open(_talk, _world);
            if (is_undefined(_world.dialogue)) _world.dialogue = undefined;
            // Card t_11f6a125: one unconditional line whenever a confirm opens a conversation, naming the box, the
            // person and the tile they stand on. It is the same kind of proof line as the battle start line above:
            // a recording can be read as "the press reached a talk entity" from the game's own log, instead of from
            // a frame somebody has to look at and guess about. Nothing is printed when no box opened.
            if (!is_undefined(_world.dialogue)) {
                show_debug_message("PP dialogue: " + string(_world.dialogue.id) + " with " + string(_talk.name)
                    + " on " + string(_world.map.id) + " " + string(_talk.tx) + "," + string(_talk.ty));
            }
            pp_overworld_clock_step(_world);
            return;
        }
        var _target = pp_overworld_confirm_target(_world);
        if (!is_undefined(_target) && _target.kind != "marker") {
            pp_overworld_fire(_world, _target);
            pp_overworld_clock_step(_world);
            return;
        }
    }

    // The free walk has already run, above, before the triggers were read: it is what moves him, and the tile it left
    // him on is what the entry test and the confirm target are read from (card PP-FREE-MOVE). Nothing is left to do here
    // but the clocks that run under everything.

    pp_overworld_clock_step(_world);
}

/// The fade, the camera pan and the follow, which run under everything else.
function pp_overworld_clock_step(_world) {
    if (!is_undefined(_world.fade)) {
        var _f = _world.fade;
        _f.steps += 1;
        _f.alpha = clamp(_f.alpha + _f.dir * (1 / max(1, _f.total)), 0, 1);
        if (_f.steps >= _f.total) {
            _f.alpha = (_f.dir < 0) ? 0 : 1;
            _world.fade = undefined;
        }
    }

    if (!is_undefined(_world.cam_pan)) {
        var _p = _world.cam_pan;
        _p.steps += 1;
        var _t = min(1, _p.steps / max(1, _p.total));
        _world.cam_x = floor(lerp(_p.from_x, _p.to_x, _t));
        _world.cam_y = floor(lerp(_p.from_y, _p.to_y, _t));
        if (_p.steps >= _p.total) _world.cam_pan = undefined;
    } else if (_world.camera_follow) {
        pp_overworld_camera_step(_world);
    }
}

/// Draw the map, the actors, the hero, the dialogue and the fade. Shake is whole pixels, 1 or 2, every 2 steps.
function pp_overworld_draw(_world) {
    if (is_undefined(_world)) return;

    var _ox = 0;
    var _oy = 0;
    if (_world.shake_steps > 0) {
        var _phase = floor(_world.shake_steps / PP_SHAKE_PERIOD) mod 2;
        _ox = _phase == 0 ? _world.shake_strength : -_world.shake_strength;
        _oy = _phase == 0 ? -_world.shake_strength : _world.shake_strength;
    }

    // The tile art, in the two planes the hero stands in front of: ground first, then the props that stand on it
    // (card R28). The above plane is drawn after him, below.
    pp_map_draw(_world.map, floor(_world.cam_x) + _ox, floor(_world.cam_y) + _oy, _world.steps);

    // Story actors and the hero, each a sheet frame when the art lane has delivered one and a shaped block
    // until then (card ASSEMBLE: SPRITE-1 was not on disk, so the block fallback is the live path and the
    // frame branch is what a delivered sheet switches on with no code change).
    pp_overworld_draw_actors(_world, _ox, _oy);

    // Encounter markers: a small silhouette, skipped while respawning.
    var _t = 0;
    while (_t < array_length(_world.map.triggers)) {
        var _tr = _world.map.triggers[_t];
        if (_tr.kind == "marker") {
            var _key = string(_tr.x) + "_" + string(_tr.y);
            if (!variable_struct_exists(_world.marker_off, _key)) {
                draw_set_colour(pp_role_colour("hazard"));
                // The camera is a float and is floored once here, on the same value the map and the figures are drawn
                // against, so a marker cannot land a fraction of a pixel inside its own tile (card PP-FREE-MOVE rule 5).
                draw_rectangle(_tr.x * PP_TILE - floor(_world.cam_x) + 4 + _ox, _tr.y * PP_TILE - floor(_world.cam_y) + 3 + _oy,
                               _tr.x * PP_TILE - floor(_world.cam_x) + 11 + _ox, _tr.y * PP_TILE - floor(_world.cam_y) + 15 + _oy, false);
            }
        }
        _t += 1;
    }

    // The hero, 12x12 in a 16x16 tile, centred, with the walk cycle.
    pp_overworld_draw_hero(_world, _ox, _oy);

    // The above plane of the tile art, over the hero and the actors: a lamp post, a harbour sign, the things a
    // walker passes behind (card R28). Drawn after him so the overlap is the layer order and not a coincidence.
    pp_map_draw_above(_world.map, floor(_world.cam_x) + _ox, floor(_world.cam_y) + _oy, _world.steps);

    if (!pp_dialogue_closed(_world.dialogue)) {
        pp_dialogue_draw(_world.dialogue);
        // Card R30 (spec 19 section 5, Q9): the hint is the row under the box's text, in the second ink, inside the
        // window's own 64 pixels. A box the bake did not open carries no hints and draws nothing here.
        var _hint = pp_talk_npc_hint(_world.dialogue);
        if (_hint != "") {
            // Card BATTLE-FONT-WIRE: the sheet's glyphs, wrapped to the box's 224 px inside, on the row under the
            // dialogue rows. Where it sits is what marks it out, not a second ink the sheet does not have (rule 6).
            pp_font_draw_wrapped(_hint, PP_TEXT_X, PP_BOX_Y + PP_BOX_H - 22,
                pp_font_cols(PP_TEXT_RIGHT - PP_TEXT_X), 8, 1);
        }
        draw_set_halign(fa_left);
    }

    // Card t_009836b9: the skip a player can press on a long scene. One line in the sheet's own ink, only while the
    // hold is still zero, so the words disappear the moment the player starts holding instead of sitting there through
    // the count. A scene that does not ask to be skippable draws nothing.
    if (pp_scene_running(_world.scene) && variable_struct_exists(_world.scene, "skippable")
        && _world.scene.skippable == true && _world.scene.skip_hold == 0) {
        pp_font_draw("hold X to skip", 8, 8, 1);
    }

    // A flash is the whole frame flooded in one role the room's own palette set declares (card t_531bc76c): a palette
    // change, never a blend, so the screen still spends one declared colour and spec 13's no-gradients rule holds.
    // Drawn over the map, the actors and the box, and under the fade, because a fade is the darker statement of intent.
    if (_world.flash_steps > 0) {
        draw_set_alpha(1);
        draw_set_colour(pp_role_colour(_world.flash_role));
        draw_rectangle(0, 0, PP_FRAME_W, PP_FRAME_H, false);
    }

    if (!is_undefined(_world.fade)) {
        draw_set_alpha(_world.fade.alpha);
        draw_set_colour(pp_role_colour("ink"));
        draw_rectangle(0, 0, PP_FRAME_W, PP_FRAME_H, false);
        draw_set_alpha(1);
    }

    // Card ASSEMBLE self check: with PP_SHIP_CAPTURE set in the environment, the room writes one PNG of its own frame
    // from inside the draw, so the room can be proven without a screen copy of whatever window sits on top of the game.
    // The 90th draw is 1.5 s in, past pp_app's 12 step fade in, so the file shows the room and not a black fade frame.
    // Unset, which is every real launch, this costs one environment read per frame and writes nothing.
    if (environment_get_variable(PP_SHIP_CAPTURE) != "") {
        if (!variable_global_exists("pp_ship_draws")) global.pp_ship_draws = 0;
        global.pp_ship_draws += 1;
        if (global.pp_ship_draws == 90) {
            screen_save("pp_ship_frame.png");
            show_debug_message("PP ship: wrote pp_ship_frame.png from the room itself at draw " + string(global.pp_ship_draws));
        }
        // The second file is five seconds in, after the harness has pressed Right eight times, so the pair proves the
        // walker moved and the camera followed it inside the room's own pixels.
        if (global.pp_ship_draws == 360) {
            screen_save("pp_ship_frame_2.png");
            show_debug_message("PP ship: wrote pp_ship_frame_2.png from the room itself at draw " + string(global.pp_ship_draws));
        }
        // The third file is after the harness has pressed confirm next to the sailor, so the dialogue box in the window
        // frame is in the room's own pixels rather than inferred from the code path.
        if (global.pp_ship_draws == 460) {
            screen_save("pp_ship_frame_3.png");
            show_debug_message("PP ship: wrote pp_ship_frame_3.png from the room itself at draw " + string(global.pp_ship_draws));
        }
    }
}

// ---------------------------------------------------------------------------------------------------------------
// The two overworld figures. Both ask the art index first: a delivered sheet is 4 directions by 3 frames
// (idle, walk a, walk b) in rows of 16x16, so the frame index is direction * 3 + step. With no sheet the
// same silhouette is drawn from blocks at the same size, which is the card's stated fallback and keeps the
// walk cycle, the facing and the dialogue reach working before any art lands.

#macro PP_HERO_SHEET "zander_ow_v2"
#macro PP_SAILOR_SHEET "sailor_ow_v2"

/// Row of a direction inside an overworld sheet. The sheet the character lane draws is 128x16, eight frames in
/// one row: down 0, down 1, up 0, up 1, right 0, right 1, left 0, left 1. So the direction order is down, up,
/// right, left, two frames each: frame 0 stands (idle) and frame 1 steps.
function pp_world_dir_row(_dir) {
    switch (_dir) {
        case "down":  return 0;
        case "up":    return 1;
        case "right": return 2;
        case "left":  return 3;
    }
    return 0;
}

/// The frame of one figure in its sheet: direction times frames per direction, plus the walk frame. Frames per
/// direction is read off the sheet (eight frames over four directions is two), so a twelve frame sheet with three
/// frames per direction would animate without a code change. Idle is frame 0 of the direction; a walk cycles.
/// `_walk_frame` is the frame the caller has already chosen from the DISTANCE walked (card PP-FREE-MOVE rule 3), not a
/// step count, so a figure standing still cannot animate and a runner animates at the speed he covers.
function pp_world_sheet_frame(_name, _dir, _walking, _walk_frame) {
    var _per = 2;
    var _info = pp_art_info(_name);
    if (!is_undefined(_info) && _info.frames > 0 && (_info.frames mod 4) == 0) _per = _info.frames div 4;
    var _step = 0;
    if (_walking && _per > 1) _step = _walk_frame mod _per;
    return pp_world_dir_row(_dir) * _per + _step;
}

/// The walk frame of a figure: 0 standing, 1 and 2 while a walk is under way. Two frames, alternated by the distance
/// walked, so the cycle is timed to the movement rather than to the number of steps the key has been held.
function pp_world_walk_frame(_walking, _walk_frame) {
    if (!_walking) return 0;
    return 1 + (_walk_frame mod 2);
}

function pp_overworld_draw_hero(_world, _ox, _oy) {
    var _hero = _world.hero;
    // Floor the figure and the camera separately, on the same camera the map is drawn against (card PP-FREE-MOVE rule
    // 5). The walk moves him by fractions of a pixel on a diagonal and the camera eases by fractions every step, and a
    // 16x16 sprite drawn at a fraction of a pixel does not move: it shimmers, because its own edges land between the
    // pixels while the tiles behind it stay on them. Whole pixels on both sides keep him exact, and the pixel he is
    // on changes exactly when he has walked onto it.
    var _sx = floor(_hero.px) - floor(_world.cam_x) + _ox;
    var _sy = floor(_hero.py) - floor(_world.cam_y) + _oy;
    var _walking = (_hero.walking == true);
    var _step = pp_world_walk_frame(_walking, _hero.walk_anim);
    var _frame = pp_world_sheet_frame(PP_HERO_SHEET, _hero.facing, _walking, _hero.walk_anim);
    if (pp_art_draw(PP_HERO_SHEET, _frame, _sx, _sy, PP_UNTINTED, 1)) return;

    // Blocks: blond head, light blue bomber, dark trousers. 12 wide, 14 tall inside the 16 pixel tile.
    var _bob = (_step == 0) ? 0 : 1;
    draw_set_colour(pp_role_colour("warn"));
    draw_rectangle(_sx + 5, _sy + 1 + _bob, _sx + 10, _sy + 5 + _bob, false);
    draw_set_colour(pp_role_colour("marker"));
    draw_rectangle(_sx + 4, _sy + 6 + _bob, _sx + 11, _sy + 11 + _bob, false);
    draw_set_colour(pp_role_colour("ink"));
    draw_rectangle(_sx + 4, _sy + 12, _sx + 5, _sy + 14, false);
    draw_rectangle(_sx + 10, _sy + 12, _sx + 11, _sy + 14, false);
    if (_hero.facing == "left" || _hero.facing == "right") {
        draw_set_colour(pp_role_colour("ink"));
        draw_rectangle(_sx + (_hero.facing == "left" ? 5 : 9), _sy + 3 + _bob,
                       _sx + (_hero.facing == "left" ? 5 : 9), _sy + 3 + _bob, false);
    } else if (_hero.facing == "down") {
        draw_set_colour(pp_role_colour("ink"));
        draw_rectangle(_sx + 6, _sy + 3 + _bob, _sx + 6, _sy + 3 + _bob, false);
        draw_rectangle(_sx + 9, _sy + 3 + _bob, _sx + 9, _sy + 3 + _bob, false);
    }
}

function pp_overworld_draw_actors(_world, _ox, _oy) {
    var _names = variable_struct_get_names(_world.actors);
    var _i = 0;
    while (_i < array_length(_names)) {
        var _a = _world.actors[$ _names[_i]];
        // Whole pixels, exactly as the hero and the map (card PP-FREE-MOVE rule 5).
        var _sx = floor(_a.px) - floor(_world.cam_x) + _ox;
        var _sy = floor(_a.py) - floor(_world.cam_y) + _oy;
        var _frame = pp_world_sheet_frame(PP_SAILOR_SHEET, _a.facing, false, 0);
        if (!pp_art_draw(PP_SAILOR_SHEET, _frame, _sx, _sy, PP_UNTINTED, 1)) {
            // Blocks: navy jacket with a white collar, cap, so a sailor does not read as the hero.
            draw_set_colour(pp_role_colour("dim"));
            draw_rectangle(_sx + 3, _sy + 2, _sx + 12, _sy + 6, false);
            draw_set_colour(pp_role_colour("paper"));
            draw_rectangle(_sx + 4, _sy + 7, _sx + 11, _sy + 8, false);
            draw_set_colour(pp_role_colour("dim"));
            draw_rectangle(_sx + 4, _sy + 9, _sx + 11, _sy + 15, false);
        }
        _i += 1;
    }
}
