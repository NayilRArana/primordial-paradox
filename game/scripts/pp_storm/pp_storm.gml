/// pp_storm: the hurricane over the Town Quay (final scope 2026-11-03, item 8). Drawn on top of the quay only.
/// Only the lightning is drawn (a flood of the text role followed by dithers, never an alpha blend). Nothing here reads the game's seeded streams: the storm owns one private stream (pp_rng_new) and everything
/// else is arithmetic on the storm's step count, so the same steps always draw the same storm.
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
            flash_count: 0
        };
    }
    return global.pp_storm;
}

/// True when this world is the quay.
function pp_storm_active(_world) {
    return is_struct(_world) && is_struct(_world.map) && _world.map.id == PP_STORM_ROOM;
}

/// One step of the storm: the clock and the lightning. Called every overworld step, scenes and talk included.
function pp_storm_step(_world) {
    if (!pp_storm_active(_world)) return;
    var _s = pp_storm_state();
    _s.steps += 1;
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

/// Draw the storm over the world. The author removed the grain (dither darkening and rain streaks): only the lightning
/// flash is drawn now. Before the dialogue box, so text is never flashed over.
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
