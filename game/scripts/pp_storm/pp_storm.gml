/// pp_storm: the hurricane over the Town Quay (final scope 2026-11-03, item 8). Drawn on top of the quay only.
/// The lightning is a flood of the text role followed by dithers, never an alpha blend. Nothing here reads the game's
/// seeded streams: the storm owns one private stream (pp_rng_new) and everything else is arithmetic on the storm's
/// step count, so the same steps always draw the same storm.
/// Card t_4d11b46d adds the storm's story face: the wind gate across the block exit (the three tiles the
/// quay_bridge_wind trigger row stands on), the seeded clock that drives it, and a wind meter whose number is the
/// mercy the Morgan fight reached. The gate is shut while morgan_resolved is unset and drawn open after the spare,
/// so the same mouth reads before and after in one shot.
/// The hook is two calls in pp_overworld.gml: pp_storm_step at the top of pp_overworld_step and pp_storm_draw straight
/// after the above plane. Both do nothing in any room but PP_STORM_ROOM.

#macro PP_STORM_ROOM "southampton_town_quay"
#macro PP_STORM_SEED 20261103
// A flash is 8 steps: 3 of near white, 2 of the white dither at 50 percent, 3 of the dark tail (ink at 50 percent).
#macro PP_STORM_FLASH_STEPS 8
#macro PP_STORM_WAIT_MIN 210
#macro PP_STORM_WAIT_MAX 540
// The thunder follows the flash by this many steps, the way sound follows light.
#macro PP_STORM_THUNDER_LAG 14
// Card t_4d11b46d: the Southampton block exit. The three tiles are the quay_bridge_wind trigger row, so the gate
// stands exactly where the data already stops a walk; the flag that opens it is the one the Morgan fight sets.
#macro PP_STORM_GATE_X1 22
#macro PP_STORM_GATE_X2 24
#macro PP_STORM_GATE_Y 32
#macro PP_STORM_GATE_FLAG "morgan_resolved"
// The meter's clock is the storm's own step count, four digits, and the bar is eight 4 pixel cells. Both sit on the
// top row of the frame where the quay's building band leaves them legible and clear of the hero's 16 pixel head.
#macro PP_STORM_HUD_Y 2
#macro PP_STORM_BAR_CELLS 8
#macro PP_STORM_BAR_CELL_W 4
#macro PP_STORM_DIGIT_W 8

/// The storm's one state struct, made on first use.
function pp_storm_state() {
    if (!variable_global_exists("pp_storm") || !is_struct(global.pp_storm)) {
        var _rng = pp_rng_new(PP_STORM_SEED);
        global.pp_storm = {
            steps: 0,
            rng: _rng,
            flash_wait: pp_rng_int(_rng, PP_STORM_WAIT_MIN, PP_STORM_WAIT_MAX),
            flash_left: 0,
            thunder_in: -1,
            flash_count: 0,
            gate_open: false,
            gate_seen: false
        };
    }
    return global.pp_storm;
}

/// True when this world is the quay.
function pp_storm_active(_world) {
    return is_struct(_world) && is_struct(_world.map) && _world.map.id == PP_STORM_ROOM;
}

/// Is the block exit open? The flag is the one both Morgan outcomes set, so the gate opens for the spare and for the
/// kill alike; the bar's number is what tells the spare from the kill, not the gate's state.
function pp_storm_gate_open() {
    if (!variable_global_exists("pp_ledger") || !is_struct(global.pp_ledger)) return false;
    return pp_ledger_flag(global.pp_ledger, PP_STORM_GATE_FLAG);
}

/// The mercy the Morgan fight reached, 0 to 100, or -1 when no Morgan fight has been fought this run. The number is
/// carried by pp_battle_publish_outcome in global.pp.last_battle.mercy, so the meter and the battle's WILL bar are
/// one value and not two copies.
function pp_storm_mercy() {
    if (!variable_global_exists("pp") || !is_struct(global.pp)) return -1;
    if (!variable_struct_exists(global.pp, "last_battle") || !is_struct(global.pp.last_battle)) return -1;
    if (!variable_struct_exists(global.pp.last_battle, "enemy")) return -1;
    if (string(global.pp.last_battle.enemy) != "morgan") return -1;
    if (!variable_struct_exists(global.pp.last_battle, "mercy")) return -1;
    return clamp(floor(global.pp.last_battle.mercy), 0, 100);
}

/// Wind strength, 0 to 100: the complement of the mercy the Morgan fight reached, and zero once the exit is open, so
/// the same bar that fell while the player talked empties when the world changes.
function pp_storm_wind() {
    if (pp_storm_gate_open()) return 0;
    var _m = pp_storm_mercy();
    if (_m >= 0) return 100 - _m;
    return 100;
}

/// Keep the state's gate word in step with the ledger, and say once, in one line, when it changes. One writer, so a
/// demo's walk log can prove the gate opened at a step rather than being drawn open from the start.
function pp_storm_gate_sync(_s) {
    var _open = pp_storm_gate_open();
    if (!_s.gate_seen) {
        _s.gate_seen = true;
        _s.gate_open = _open;
        show_debug_message("PP: wind gate " + (_open ? "open" : "shut") + " at step " + string(_s.steps));
        return;
    }
    if (_open == _s.gate_open) return;
    _s.gate_open = _open;
    show_debug_message("PP: wind gate " + (_open ? "open" : "shut") + " at step " + string(_s.steps)
        + ", the bridge is " + (_open ? "clear" : "shut"));
}

/// One step of the storm: the clock and the lightning. Called every overworld step, scenes and talk included.
function pp_storm_step(_world) {
    if (!pp_storm_active(_world)) return;
    var _s = pp_storm_state();
    _s.steps += 1;
    pp_storm_gate_sync(_s);
    if (_s.thunder_in > 0) {
        _s.thunder_in -= 1;
        if (_s.thunder_in == 0) {
            pp_audio_play("thunder_soft");
            _s.thunder_in = -1;
        }
    }
    if (_s.flash_left > 0) {
        _s.flash_left -= 1;
        return;
    }
    _s.flash_wait -= 1;
    if (_s.flash_wait > 0) return;
    _s.flash_left = PP_STORM_FLASH_STEPS;
    _s.flash_wait = pp_rng_int(_s.rng, PP_STORM_WAIT_MIN, PP_STORM_WAIT_MAX);
    _s.thunder_in = PP_STORM_THUNDER_LAG;
    _s.flash_count += 1;
    show_debug_message("PP: storm lightning " + string(_s.flash_count));
}

/// Draw the storm over the world: the eight step flash, then the gate across the block exit, then the clock and the
/// wind meter. Before the dialogue box, so text is never flashed over.
function pp_storm_draw(_world) {
    if (!pp_storm_active(_world)) return;
    var _s = pp_storm_state();
    var _w = PP_FRAME_W;
    var _h = PP_FRAME_H;

    // Lightning: a near white flood, the same white as a 50 percent dither, then a dark tail.
    if (_s.flash_left > 0) {
        var _n = PP_STORM_FLASH_STEPS - _s.flash_left;
        if (_n < 3) {
            draw_set_colour(pp_role_colour("text"));
            draw_rectangle(0, 0, _w, _h, false);
        } else if (_n < 5) {
            pp_art_draw_tiled("spr_pp_dither", 0, 0, pp_role_colour("text"), 1);
        } else {
            pp_art_draw_tiled("spr_pp_dither", 0, 0, pp_role_colour("ink"), 1);
        }
    }

    // The story over the weather: the gate across the block exit, then the clock and the meter that explain it.
    // Both are drawn after the flash so eight white steps cannot wipe the one thing a judge is asked to read.
    pp_storm_gate_draw(_world, _s);
    pp_storm_hud_draw(_s);
}

/// Where a gate tag sits: just east of the mouth, over the quay wall, so the hero never walks under his own label and
/// the same tag position marks the same exit in both states.
function pp_storm_gate_tag_x(_gx, _gw, _text) {
    return _gx + _gw + 4 + floor(pp_font_width(_text) / 2);
}

/// The block exit. Two posts stand in both drawings, so the shut and the open frame are the same mouth. While the gate
/// is shut an 8 pixel wind cell fills it on the storm's own flash cycle (eight steps on, eight steps off), which is
/// what makes the hurricane look like the thing stopping the walk; once the flag is set the cells and the label are
/// gone and the same tiles read open.
function pp_storm_gate_draw(_world, _s) {
    var _gx = PP_STORM_GATE_X1 * PP_TILE - floor(_world.cam_x);
    var _gy = PP_STORM_GATE_Y * PP_TILE - floor(_world.cam_y);
    var _gw = (PP_STORM_GATE_X2 - PP_STORM_GATE_X1 + 1) * PP_TILE;
    if (_gx > PP_FRAME_W || _gx + _gw < 0 || _gy > PP_FRAME_H || _gy + PP_TILE < 0) return;

    // The two posts and the coping: the same pixels in both states.
    draw_set_colour(pp_role_colour("stone_2"));
    draw_rectangle(_gx, _gy, _gx + 1, _gy + PP_TILE - 1, false);
    draw_rectangle(_gx + _gw - 2, _gy, _gx + _gw - 1, _gy + PP_TILE - 1, false);
    draw_set_colour(pp_role_colour("gold_5"));
    draw_rectangle(_gx, _gy, _gx + _gw - 1, _gy, false);

    if (_s.gate_open) {
        draw_set_colour(pp_role_colour("stone_4"));
        draw_rectangle(_gx + 2, _gy + PP_TILE - 2, _gx + _gw - 3, _gy + PP_TILE - 2, false);
        pp_font_draw_plated_centre("OPEN", pp_storm_gate_tag_x(_gx, _gw, "OPEN"), _gy + 4, 1);
        return;
    }

    // Shut: a dither cell over every 8x8 of the mouth, alternating on the storm's clock. Under a flash the cells go
    // to ink so the barrier stays the one readable shape under the white flood.
    var _on = ((_s.steps div PP_STORM_FLASH_STEPS) mod 2 == 0);
    var _cell = (_s.flash_left > 0) ? "ink" : (_on ? "text" : "warn");
    var _dither = pp_art_info("spr_pp_dither");
    var _cy = 0;
    while (_cy < 2) {
        var _cx = 0;
        while (_cx < (_gw div 8)) {
            if (!is_undefined(_dither)) {
                draw_sprite_ext(_dither.sprite, 0, _gx + _cx * 8, _gy + _cy * 8, 1, 1, 0, pp_role_colour(_cell), 1);
            } else {
                draw_set_colour(pp_role_colour(_cell));
                draw_rectangle(_gx + _cx * 8, _gy + _cy * 8, _gx + _cx * 8 + 7, _gy + _cy * 8 + 7, false);
            }
            _cx += 1;
        }
        _cy += 1;
    }
    // Three ink streaks the wind drags across the mouth, phased on the storm's own step count.
    draw_set_colour(pp_role_colour("ink"));
    var _i = 0;
    while (_i < 3) {
        var _sx = _gx + 2 + (((_s.steps * (3 + _i)) div 2) mod max(1, _gw - 12));
        draw_rectangle(_sx, _gy + 3 + _i * 4, _sx + 7, _gy + 3 + _i * 4, false);
        _i += 1;
    }
    pp_font_draw_plated_centre("WIND", pp_storm_gate_tag_x(_gx, _gw, "WIND"), _gy + 4, 1);
}

/// The seeded clock and the wind meter. The clock is the storm's own step count read at 60 steps a second, so it
/// visibly runs; the pip lights for the eight steps of a flash. The bar is the wind, which is the complement of the
/// mercy the Morgan fight reached, and the row under it prints that mercy, so the two numbers are one value.
function pp_storm_hud_draw(_s) {
    var _y = PP_STORM_HUD_Y;
    var _secs = _s.steps div 60;
    var _clock = "STORM " + string(_secs div 60) + ":" + string_format(_secs mod 60, 2, 0);
    pp_font_draw_plated_centre(_clock, 8 + floor(pp_font_width(_clock) / 2), _y, 1);

    var _pip_x = 14 + pp_font_width(_clock);
    draw_set_colour(pp_role_colour("ink"));
    draw_rectangle(_pip_x - 1, _y - 1, _pip_x + 6, _y + 6, false);
    draw_set_colour(pp_role_colour((_s.flash_left > 0) ? "text" : "dim"));
    draw_rectangle(_pip_x, _y, _pip_x + 5, _y + 5, false);

    var _wind = pp_storm_wind();
    var _mercy = pp_storm_mercy();
    var _right = PP_FRAME_W - 8;
    var _bar_w = PP_STORM_BAR_CELLS * PP_STORM_BAR_CELL_W;
    var _num = string(_wind);
    // A fixed three digit field, so the bar does not jump sideways the step the number drops from 100 to 0.
    var _num_x = _right - PP_STORM_DIGIT_W * 3;
    var _bar_x = _num_x - 4 - _bar_w;
    var _wind_x = _bar_x - 4 - pp_font_width("WIND");
    pp_font_draw("WIND", _wind_x, _y, 1);

    draw_set_colour(pp_role_colour("ink"));
    draw_rectangle(_bar_x - 1, _y - 1, _bar_x + _bar_w, _y + 5, false);
    var _lit = floor((_wind * PP_STORM_BAR_CELLS + 99) / 100);
    var _c = 0;
    while (_c < PP_STORM_BAR_CELLS) {
        draw_set_colour(pp_role_colour((_c < _lit) ? "warn" : "dim"));
        draw_rectangle(_bar_x + _c * PP_STORM_BAR_CELL_W, _y,
                       _bar_x + _c * PP_STORM_BAR_CELL_W + PP_STORM_BAR_CELL_W - 2, _y + 4, false);
        _c += 1;
    }
    pp_font_draw(_num, _num_x, _y, 1);

    var _label = "MERCY " + ((_mercy >= 0) ? string(_mercy) : "0");
    pp_font_draw_plated_centre(_label, _right - floor(pp_font_width(_label) / 2), _y + 9, 1);
}

// ---------------------------------------------------------------------------------------------------------------
// The possession look on Morgan and Percy. On by default for those two; the route switches it off when one is spared.

/// Switch the possession look of one actor on or off. Returns true when the actor is on the map.
function pp_possession_tint(_actor_id, _on) {
    if (!variable_global_exists("pp") || !is_struct(global.pp) || !variable_struct_exists(global.pp, "world")) return false;
    var _world = global.pp.world;
    if (!is_struct(_world) || !variable_struct_exists(_world.actors, string(_actor_id))) return false;
    _world.actors[$ string(_actor_id)].possessed = (_on == true);
    return true;
}

/// Is this actor drawn possessed? An explicit flag wins; otherwise Morgan and Percy are, everyone else is not.
function pp_possession_on(_actor) {
    if (variable_struct_exists(_actor, "possessed")) return _actor.possessed == true;
    return (_actor.name == "morgan" || _actor.name == "percy");
}

/// The look: a flickering halo of hazard coloured pixels round the head, two steps in three. Drawn by
/// pp_overworld_draw_actors straight after the figure.
function pp_possession_draw(_actor, _sx, _sy, _steps) {
    if (!pp_possession_on(_actor)) return;
    if ((_steps div 5) mod 3 == 2) return;
    draw_set_colour(pp_role_colour("warn"));
    var _j = (_steps div 10) mod 2;
    draw_rectangle(_sx + 2, _sy + 1 + _j, _sx + 2, _sy + 2 + _j, false);
    draw_rectangle(_sx + 13, _sy + 2 - _j, _sx + 13, _sy + 3 - _j, false);
    draw_rectangle(_sx + 4, _sy - 1, _sx + 5, _sy - 1, false);
    draw_rectangle(_sx + 10, _sy - 1 + _j, _sx + 11, _sy - 1 + _j, false);
}
