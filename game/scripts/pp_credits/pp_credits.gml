/// pp_credits: the credits roll, a mode of the app machine (card CREDITS, FINAL-SCOPE 2026-11-03, contract C3).
/// pp_credits_start("spare" or "kill") asks the app for the mode, the mode scrolls data\credits.json in the game's own
/// font (pp_font) over black, plays the variant's music cue, and goes back to the title screen when the roll ends or when
/// the player holds cancel. Modelled on the game over card (black frame, one ink sheet, the title room as the way out).
/// The file is read here with its own tolerant reader, never through pp_data_json, because a missing file there is
/// pushed onto the boot error list and would switch the title's save read off. Without the file a short built in roll runs.

#macro PP_CREDITS_FILE "credits.json"
// Steps of holding cancel that skip the roll: the same half second the scenes use, so the two skips feel alike.
#macro PP_CREDITS_SKIP_HOLD 30

/// The mode struct the app machine registers.
function pp_credits_mode() {
    return {
        enter: function(_params) { pp_credits_enter(_params); },
        step: function(_params) { pp_credits_step(_params); },
        draw: function(_params) { pp_credits_draw(_params); }
    };
}

/// Register the mode once. pp_credits_start calls this, so no other file has to know the mode exists.
function pp_credits_register() {
    var _app = global.pp.app;
    if (variable_struct_exists(_app.modes, string(PPMode.credits))) return false;
    pp_app_register(PPMode.credits, pp_credits_mode());
    return true;
}

/// "kill" for kill or killed, "spare" for everything else. The world flags say spared and killed, the contract says spare
/// and kill, and a call site that mixes them up must still get a roll, never a dead end.
function pp_credits_variant_name(_variant) {
    var _v = string_lower(string(_variant));
    if (_v == "kill" || _v == "killed") return "kill";
    if (_v != "spare" && _v != "spared") {
        show_debug_message("PP credits: unknown variant " + _v + ", the spare roll is used");
    }
    return "spare";
}

/// True while a roll owns the screen.
function pp_credits_running() {
    if (!variable_struct_exists(global.pp, "credits")) return false;
    var _s = global.pp.credits;
    return is_struct(_s) && !_s.done;
}

/// The door FLOW calls (contract C3). Returns true when the roll was asked for.
function pp_credits_start(_variant) {
    var _name = pp_credits_variant_name(_variant);
    if (pp_credits_running()) {
        show_debug_message("PP credits: a roll is already running, start ignored");
        return false;
    }
    pp_credits_register();
    if (!pp_app_request(PPMode.credits, { variant: _name })) {
        show_debug_message("PP credits: the app machine refused the request");
        return false;
    }
    if (_name == "kill") show_debug_message("PP: credits start kill");
    else show_debug_message("PP: credits start spare");
    return true;
}

/// The built in roll and timing, used for every field the file does not give.
function pp_credits_defaults() {
    return {
        line_h: 12,
        head_h: 18,
        section_gap_rows: 2,
        speed: 0.5,
        lead_in_steps: 90,
        hold_steps: 300,
        leave_steps: 45,
        hint_steps: 360,
        music_fade_steps: 30,
        sections: [
            { id: "title", rows: [
                { style: "title", text: "PRIMORDIAL PARADOX" },
                { style: "text", text: "A GAME BY NAYILINIST" }
            ] }
        ],
        variants: {
            spare: { music_cue: "PP-15b", music_fallback: "PP-01", closing: { id: "closing", rows: [
                { style: "title", text: "THANK YOU FOR PLAYING" } ] } },
            kill: { music_cue: "PP-15a", music_fallback: "PP-01", closing: { id: "closing", rows: [
                { style: "title", text: "THANK YOU FOR PLAYING" } ] } }
        }
    };
}

/// Read data\credits.json, or undefined. Failure is logged and never raised.
function pp_credits_read_json() {
    var _paths = pp_data_paths(PP_CREDITS_FILE);
    for (var i = 0; i < array_length(_paths); i += 1) {
        var _p = _paths[i];
        if (!file_exists(_p)) continue;
        var _f = file_text_open_read(_p);
        if (_f < 0) continue;
        var _out = "";
        while (!file_text_eof(_f)) {
            _out += file_text_readln(_f);
            if (!file_text_eof(_f)) _out += "\n";
        }
        file_text_close(_f);
        try {
            var _d = json_parse(_out);
            if (is_struct(_d)) return _d;
        } catch (_e) {
            show_debug_message("PP credits: " + PP_CREDITS_FILE + " does not parse, the built in roll is used");
            return undefined;
        }
    }
    show_debug_message("PP credits: " + PP_CREDITS_FILE + " not found, the built in roll is used");
    return undefined;
}

/// A number from a struct inside [low, high], else the default.
function pp_credits_pick_num(_struct, _key, _default, _low, _high) {
    if (!variable_struct_exists(_struct, _key)) return _default;
    var _v = _struct[$ _key];
    if (!is_real(_v)) return _default;
    return clamp(_v, _low, _high);
}

/// The roll settings: defaults with whatever data\credits.json (key roll) gives laid over them.
function pp_credits_roll_data() {
    var _d = pp_credits_defaults();
    var _file = pp_credits_read_json();
    if (!is_struct(_file) || !variable_struct_exists(_file, "roll") || !is_struct(_file.roll)) return _d;
    var _r = _file.roll;
    _d.line_h = pp_credits_pick_num(_r, "line_h", _d.line_h, 8, 32);
    _d.head_h = pp_credits_pick_num(_r, "head_h", _d.head_h, 8, 40);
    _d.section_gap_rows = pp_credits_pick_num(_r, "section_gap_rows", _d.section_gap_rows, 0, 8);
    _d.speed = pp_credits_pick_num(_r, "speed", _d.speed, 0.1, 4);
    _d.lead_in_steps = pp_credits_pick_num(_r, "lead_in_steps", _d.lead_in_steps, 0, 600);
    _d.hold_steps = pp_credits_pick_num(_r, "hold_steps", _d.hold_steps, 30, 1800);
    _d.leave_steps = pp_credits_pick_num(_r, "leave_steps", _d.leave_steps, 12, 300);
    _d.hint_steps = pp_credits_pick_num(_r, "hint_steps", _d.hint_steps, 0, 1800);
    _d.music_fade_steps = pp_credits_pick_num(_r, "music_fade_steps", _d.music_fade_steps, 1, 300);
    if (variable_struct_exists(_r, "sections") && is_array(_r.sections) && array_length(_r.sections) > 0) {
        _d.sections = _r.sections;
    }
    if (variable_struct_exists(_r, "variants") && is_struct(_r.variants)) {
        if (variable_struct_exists(_r.variants, "spare") && is_struct(_r.variants.spare)) _d.variants.spare = _r.variants.spare;
        if (variable_struct_exists(_r.variants, "kill") && is_struct(_r.variants.kill)) _d.variants.kill = _r.variants.kill;
    }
    return _d;
}

/// The row list: every section then the variant's closing block, top to bottom in roll space. Returns the rows, each with
/// its y, text and style, and the height. A gap row only advances; a heading or title advances head_h, the rest line_h.
function pp_credits_build_rows(_roll, _variant) {
    var _list = [];
    var _blocks = [];
    for (var i = 0; i < array_length(_roll.sections); i += 1) array_push(_blocks, _roll.sections[i]);
    var _vrow = _roll.variants[$ _variant];
    if (is_struct(_vrow) && variable_struct_exists(_vrow, "closing") && is_struct(_vrow.closing)) {
        array_push(_blocks, _vrow.closing);
    }
    var _y = 0;
    for (var b = 0; b < array_length(_blocks); b += 1) {
        var _block = _blocks[b];
        if (!is_struct(_block) || !variable_struct_exists(_block, "rows") || !is_array(_block.rows)) continue;
        if (array_length(_list) > 0) _y += _roll.section_gap_rows * _roll.line_h;
        for (var r = 0; r < array_length(_block.rows); r += 1) {
            var _row = _block.rows[r];
            if (!is_struct(_row)) continue;
            var _style = "text";
            if (variable_struct_exists(_row, "style") && is_string(_row.style)) _style = _row.style;
            if (_style == "gap") {
                _y += _roll.line_h;
                continue;
            }
            var _text = "";
            if (variable_struct_exists(_row, "text") && is_string(_row.text)) _text = _row.text;
            array_push(_list, { y: _y, text: _text, style: _style });
            if (_style == "heading" || _style == "title") _y += _roll.head_h;
            else _y += _roll.line_h;
        }
    }
    return { list: _list, height: _y };
}

/// The cue to play: the variant's own when audio.json registers it, else the variant's fallback.
function pp_credits_pick_cue(_roll, _variant) {
    var _vrow = _roll.variants[$ _variant];
    var _cue = "";
    var _fallback = "PP-01";
    if (is_struct(_vrow)) {
        if (variable_struct_exists(_vrow, "music_cue") && is_string(_vrow.music_cue)) _cue = _vrow.music_cue;
        if (variable_struct_exists(_vrow, "music_fallback") && is_string(_vrow.music_fallback)) _fallback = _vrow.music_fallback;
    }
    if (_cue != "" && !is_undefined(pp_audio_cue(_cue))) return _cue;
    return _fallback;
}

/// A fresh roll state. The first row starts just under the bottom edge and the roll ends with the last row at mid screen.
function pp_credits_state_new(_variant, _roll) {
    var _built = pp_credits_build_rows(_roll, _variant);
    var _last_y = 0;
    if (array_length(_built.list) > 0) _last_y = _built.list[array_length(_built.list) - 1].y;
    return {
        variant: _variant,
        phase: "lead",
        steps: 0,
        phase_steps: 0,
        scroll: 0,
        scroll_end: max(0, PP_FRAME_H + _last_y - 112),
        speed: _roll.speed,
        lead_in_steps: _roll.lead_in_steps,
        hold_steps: _roll.hold_steps,
        leave_steps: _roll.leave_steps,
        hint_steps: _roll.hint_steps,
        rows: _built.list,
        skip_hold: 0,
        armed: false,
        done: false
    };
}

/// Enter the mode: build the state, take the ui palette set, start the music.
function pp_credits_enter(_params) {
    var _variant = "spare";
    if (is_struct(_params) && variable_struct_exists(_params, "variant")) _variant = pp_credits_variant_name(_params.variant);
    var _roll = pp_credits_roll_data();
    global.pp.credits = pp_credits_state_new(_variant, _roll);
    pp_look_palette("ui");
    var _cue = pp_credits_pick_cue(_roll, _variant);
    pp_audio_music(_cue, _roll.music_fade_steps);
    show_debug_message("PP credits: enter, variant " + _variant + ", cue " + _cue + ", "
        + string(array_length(global.pp.credits.rows)) + " rows, scroll end " + string(global.pp.credits.scroll_end));
}

/// Start the fade out and the music out.
function pp_credits_leave(_s) {
    _s.phase = "leave";
    _s.phase_steps = 0;
    pp_audio_music_stop();
}

/// The roll is over: the title room is the way out, the same door the game over card uses.
function pp_credits_finish(_s) {
    _s.done = true;
    show_debug_message("PP credits: end, back to the title");
    pp_app_enter_room(PPMode.title, {}, rm_pp_title);
}

/// One step: the skip, then the phase (lead in, roll, hold on the last card, leave).
function pp_credits_step(_params) {
    if (!variable_struct_exists(global.pp, "credits")) return;
    var _s = global.pp.credits;
    if (!is_struct(_s) || _s.done) return;
    _s.steps += 1;
    _s.phase_steps += 1;

    if (_s.phase != "leave") {
        // Cancel must be seen released once first, so a key still held from the scene before cannot skip the roll.
        if (!pp_action("cancel")) {
            _s.armed = true;
            _s.skip_hold = 0;
        } else if (_s.armed) {
            _s.skip_hold += 1;
            if (_s.skip_hold >= PP_CREDITS_SKIP_HOLD) {
                show_debug_message("PP credits: skipped by the player after " + string(_s.skip_hold) + " steps of holding cancel");
                pp_credits_leave(_s);
                return;
            }
        }
    }

    if (_s.phase == "lead") {
        if (_s.phase_steps >= _s.lead_in_steps) {
            _s.phase = "roll";
            _s.phase_steps = 0;
        }
        return;
    }
    if (_s.phase == "roll") {
        _s.scroll += _s.speed;
        if (_s.scroll >= _s.scroll_end) {
            _s.scroll = _s.scroll_end;
            _s.phase = "hold";
            _s.phase_steps = 0;
            show_debug_message("PP credits: the roll reached its last card after " + string(_s.steps) + " steps");
        }
        return;
    }
    if (_s.phase == "hold") {
        if (_s.phase_steps >= _s.hold_steps) pp_credits_leave(_s);
        return;
    }
    if (_s.phase == "leave") {
        if (_s.phase_steps >= _s.leave_steps) pp_credits_finish(_s);
    }
}

/// A one pixel rule in the dim role, centred on the frame, half_w pixels each side.
function pp_credits_rule(_y, _half_w) {
    draw_set_colour(pp_role_colour("dim"));
    draw_rectangle(PP_FRAME_W * 0.5 - _half_w, _y, PP_FRAME_W * 0.5 + _half_w - 1, _y, false);
}

/// One row at a screen y. Headings carry a rule under them, titles a rule above and below.
function pp_credits_draw_row(_row, _y) {
    var _half = min(PP_FRAME_W * 0.5 - 8, floor(pp_font_width(_row.text) / 2) + 8);
    if (_row.style == "title") pp_credits_rule(_y - 4, _half);
    pp_font_draw_centre(_row.text, PP_FRAME_W * 0.5, _y, 1);
    if (_row.style == "heading") pp_credits_rule(_y + 10, _half);
    if (_row.style == "title") pp_credits_rule(_y + 11, _half);
}

/// The frame: black, the rows that are on screen, the skip hint and bar, and the fade out.
function pp_credits_draw(_params) {
    draw_set_alpha(1);
    draw_set_colour(pp_role_colour("ink"));
    draw_rectangle(0, 0, PP_FRAME_W, PP_FRAME_H, false);
    if (!variable_struct_exists(global.pp, "credits")) return;
    var _s = global.pp.credits;
    if (!is_struct(_s)) return;

    var _top = floor(_s.scroll);
    for (var i = 0; i < array_length(_s.rows); i += 1) {
        var _row = _s.rows[i];
        var _y = PP_FRAME_H + _row.y - _top;
        if (_y > -16 && _y < PP_FRAME_H) pp_credits_draw_row(_row, _y);
    }

    if (_s.phase != "leave") {
        if (_s.skip_hold == 0 && _s.steps < _s.hint_steps) {
            pp_font_draw("hold X to skip", 8, 8, 1);
        } else if (_s.skip_hold > 0) {
            draw_set_colour(pp_role_colour("dim"));
            draw_rectangle(8, 8, 87, 11, false);
            draw_set_colour(pp_role_colour("text"));
            draw_rectangle(8, 8, 8 + floor(80 * _s.skip_hold / PP_CREDITS_SKIP_HOLD) - 1, 11, false);
        }
    } else {
        draw_set_alpha(min(1, _s.phase_steps / _s.leave_steps));
        draw_set_colour(pp_role_colour("ink"));
        draw_rectangle(0, 0, PP_FRAME_W, PP_FRAME_H, false);
        draw_set_alpha(1);
    }
}
