/// pp_input: the only place in the project that reads a key or a gamepad (spec 02 rule 1).
/// Samples once per step in Begin Step, then publishes held, pressed, released and repeat per action.
/// Provenance: our own action table and normalised vector; see knowledge\PROVENANCE.md.

#macro PP_STICK_DEADZONE 0.35
#macro PP_REPEAT_FIRST 16
#macro PP_REPEAT_EVERY 8

/// The action table (spec 02 table). A later options screen reads this, so keys are data here and nowhere else.
/// A key or a pad button belongs to one action only: two actions on one key is a silent double fire, and the table is
/// what an options screen will show. tests\test_project.py pins that rule.
function pp_input_table() {
    return [
        { id: "confirm", keys: [ord("Z"), vk_space, vk_enter], pads: [gp_face1], axis: "" },
        { id: "cancel",  keys: [ord("X"), vk_escape, vk_backspace], pads: [gp_face2], axis: "" },
        { id: "menu",    keys: [vk_tab], pads: [gp_start], axis: "" },
        { id: "up",      keys: [vk_up, ord("W")], pads: [gp_padu], axis: "y" },
        { id: "down",    keys: [vk_down, ord("S")], pads: [gp_padd], axis: "y" },
        { id: "left",    keys: [vk_left, ord("A")], pads: [gp_padl], axis: "x" },
        { id: "right",   keys: [vk_right, ord("D")], pads: [gp_padr], axis: "x" },
        // The run (spec 04 rule 1, card PP-FREE-MOVE): shift and the right shoulder are the two inputs no other action
        // claims, so the run takes the keys that are free rather than one another action already owns. It is HELD, and
        // only the overworld reads it, so a menu or a box can never be moved faster by it.
        { id: "run",     keys: [vk_shift], pads: [gp_shoulderr], axis: "" },
        { id: "debug_warp",  keys: [vk_f1], pads: [], axis: "" },
        { id: "debug_step",  keys: [vk_f2], pads: [], axis: "" },
        { id: "debug_flags", keys: [vk_f3], pads: [], axis: "" },
        // The TALK box's voice key (spec 21 section 2, card t_ee178652). HELD, not pressed: a press starts a
        // recording and the release ends it. F5 and the left shoulder are the two keys no other action claims, and a
        // letter would have been a letter the player could no longer type.
        { id: "live_voice",  keys: [vk_f5], pads: [gp_shoulderl], axis: "" },
        // F6 flips the live TALK path between replay and live at run time, so the demo can be recorded both ways
        // without a rebuild (spec 21 section 1).
        { id: "live_mode",   keys: [vk_f6], pads: [], axis: "" }
    ];
}

/// Build the input state. Called once from pp_app_boot.
function pp_input_init() {
    var _actions = {};
    var _table = pp_input_table();
    for (var i = 0; i < array_length(_table); i++) {
        var _row = _table[i];
        _actions[$ _row.id] = {
            keys: _row.keys,
            pads: _row.pads,
            axis: _row.axis,
            held: false,
            prev: false,
            pressed: false,
            released: false,
            repeat: false,
            held_steps: 0
        };
    }
    return {
        actions: _actions,
        lock_steps: 0,
        vec_x: 0,
        vec_y: 0,
        vec_len: 0,
        // The text entry reader's state (spec 21 section 2, card t_ee178652). Declared here for the same reason
        // stick_dir below is: the TALK box reads these every step it is open, and a key a struct does not carry is a
        // crash on the first frame that reads it.
        text_mode: false,
        text_char: "",
        text_send: false,
        text_back: false,
        text_del: false,
        // The left stick's dominant direction as one of the four walk names, or "" when the stick is inside the
        // deadzone (card t_771e78ef). Declared here because the overworld reads it every step it walks, and a key a
        // struct does not carry is a crash on the first frame that reads it.
        stick_dir: "",
        // The WALK vector (card PP-FREE-MOVE): -1, 0 or 1 on each axis, so the four directions make eight, from the keys
        // and the d-pad through the action table or from the left stick. Published here for the same reason stick_dir
        // is: no module outside this one touches a pad axis (spec 02 rule 1). Declared because pp_overworld reads both
        // every step the player can walk, and a key a struct does not carry is a crash on the first of them.
        walk_x: 0,
        walk_y: 0,
        pad_seen: -1
    };
}

/// One sample per step. Call from Begin Step only (spec 02, event order).
function pp_input_sample() {
    var _in = global.pp_input;
    var _keys = variable_struct_get_names(_in.actions);
    for (var i = 0; i < array_length(_keys); i++) {
        var _a = _in.actions[$ _keys[i]];
        var _down = false;
        for (var k = 0; k < array_length(_a.keys); k++) {
            if (keyboard_check(_a.keys[k])) { _down = true; break; }
        }
        for (var p = 0; p < array_length(_a.pads); p++) {
            if (gamepad_is_connected(0) && gamepad_button_check(0, _a.pads[p])) { _down = true; break; }
        }

        _a.prev = _a.held;
        _a.held = _down;
        _a.pressed = _a.held && !_a.prev;
        _a.released = (!_a.held) && _a.prev;

        if (_a.pressed) {
            _a.held_steps = 1;
            _a.repeat = false;
        } else if (_a.held) {
            _a.held_steps += 1;
            _a.repeat = (_a.held_steps == PP_REPEAT_FIRST)
                || (_a.held_steps > PP_REPEAT_FIRST && ((_a.held_steps - PP_REPEAT_FIRST) mod PP_REPEAT_EVERY == 0));
        } else {
            _a.held_steps = 0;
            _a.repeat = false;
        }
    }

    if (_in.lock_steps > 0) {
        _in.lock_steps -= 1;
        pp_input_clear_edges();
    }

    pp_input_text_step();
    pp_input_update_vector();
    if (gamepad_is_connected(0)) _in.pad_seen = 1; else _in.pad_seen = -1;
}

/// Wipe the one step edges. Called on mode entry (spec 02 rule 3) and by the lock counter.
function pp_input_clear_edges() {
    var _in = global.pp_input;
    var _keys = variable_struct_get_names(_in.actions);
    for (var i = 0; i < array_length(_keys); i++) {
        var _a = _in.actions[$ _keys[i]];
        _a.pressed = false;
        _a.released = false;
        _a.repeat = false;
    }
}

/// Lock input for a few steps after a mode swap, so a held confirm cannot act twice (spec 02 rule 3).
function pp_input_lock(_steps) {
    global.pp_input.lock_steps = _steps;
    pp_input_clear_edges();
}

/// True on the step any key, any face button or start goes down. The title's opening shot is skippable with any
/// key, and this stays the only place that reads a key (spec 02 rule 1). A locked input reports nothing, so a
/// held key from the previous mode cannot skip the shot by accident.
function pp_input_any_pressed() {
    var _in = global.pp_input;
    if (!is_struct(_in)) return false;
    if (_in.lock_steps > 0) return false;
    if (keyboard_check_pressed(vk_anykey)) return true;
    if (gamepad_is_connected(0)) {
        for (var b = gp_face1; b <= gp_face4; b += 1) {
            if (gamepad_button_check_pressed(0, b)) return true;
        }
        if (gamepad_button_check_pressed(0, gp_start)) return true;
    }
    return false;
}

function pp_action(_name) {
    var _a = global.pp_input.actions[$ _name];
    if (is_undefined(_a)) return false;
    return _a.held;
}

/// The left stick as one of the four walk directions, or "" when it is inside the deadzone (card t_771e78ef).
/// Read by the overworld so a stick push and a d-pad push walk the same way, and so pp_overworld never touches an axis.
function pp_stick_dir() {
    var _in = global.pp_input;
    if (!is_struct(_in)) return "";
    if (!is_string(_in.stick_dir)) return "";
    return _in.stick_dir;
}

/// The walk vector's two components (card PP-FREE-MOVE): each is -1, 0 or 1, so four keys make eight directions.
/// Read by pp_overworld, which divides the pair by its own length to make every direction the same speed.
function pp_walk_x() {
    var _in = global.pp_input;
    if (!is_struct(_in) || !variable_struct_exists(_in, "walk_x")) return 0;
    return _in.walk_x;
}

function pp_walk_y() {
    var _in = global.pp_input;
    if (!is_struct(_in) || !variable_struct_exists(_in, "walk_y")) return 0;
    return _in.walk_y;
}

function pp_pressed(_name) {
    var _a = global.pp_input.actions[$ _name];
    if (is_undefined(_a)) return false;
    return _a.pressed;
}

function pp_released(_name) {
    var _a = global.pp_input.actions[$ _name];
    if (is_undefined(_a)) return false;
    return _a.released;
}

function pp_repeat(_name) {
    var _a = global.pp_input.actions[$ _name];
    if (is_undefined(_a)) return false;
    return _a.repeat;
}

/// One normalised vector for the dodge phase (spec 02 rule 5, spec 08, and delta T3).
/// Keyboard gives one of eight unit directions; stick keeps its angle but not its magnitude.
///
/// It also publishes `stick_dir`, the same stick as ONE of the four walk directions (card t_771e78ef): a tile walk
/// cannot spend a diagonal, and the overworld needs the stick to behave like the d-pad (spec 04 rule 1). The dominant
/// axis wins, ties go to vertical, and the reading is taken here so no module outside this file touches an axis.
///
/// And it publishes the WALK vector itself (card PP-FREE-MOVE): `walk_x` and `walk_y`, each -1, 0 or 1, so the four
/// directions become eight. The four key and d-pad actions are read first and the stick second, so a resting stick can
/// never fight a key that is being held; each stick axis has to clear the deadzone on its own, which is what makes a
/// stick pushed into a corner a diagonal instead of a single direction.
function pp_input_update_vector() {
    var _in = global.pp_input;
    var _x = 0;
    var _y = 0;
    var _ax = 0;
    var _ay = 0;
    var _from_stick = false;

    _in.stick_dir = "";
    if (gamepad_is_connected(0)) {
        _ax = gamepad_axis_value(0, gp_axislh);
        _ay = gamepad_axis_value(0, gp_axislv);
        if (point_distance(0, 0, _ax, _ay) > PP_STICK_DEADZONE) {
            _x = _ax;
            _y = _ay;
            _from_stick = true;
            if (abs(_ax) >= abs(_ay)) {
                _in.stick_dir = (_ax > 0) ? "right" : "left";
            } else {
                _in.stick_dir = (_ay > 0) ? "down" : "up";
            }
        }
    }

    if (!_from_stick) {
        if (pp_action("left")) _x -= 1;
        if (pp_action("right")) _x += 1;
        if (pp_action("up")) _y -= 1;
        if (pp_action("down")) _y += 1;
    }

    var _len = point_distance(0, 0, _x, _y);
    if (_len > 1) {
        _x = _x / _len;
        _y = _y / _len;
        _len = 1;
    }
    _in.vec_x = _x;
    _in.vec_y = _y;
    _in.vec_len = point_distance(0, 0, _x, _y);

    // The walk vector (card PP-FREE-MOVE). Signs rather than magnitudes, because the overworld makes its own unit vector
    // from the pair: a diagonal is (1, 1) or (-1, 1) and the speed is applied after the divide, so all eight directions
    // are the same speed. Keys first, so a stick left off centre cannot pull a keyboard walk off its axis.
    var _walk_x = 0;
    var _walk_y = 0;
    if (pp_action("left") || pp_action("right") || pp_action("up") || pp_action("down")) {
        if (pp_action("left")) _walk_x -= 1;
        if (pp_action("right")) _walk_x += 1;
        if (pp_action("up")) _walk_y -= 1;
        if (pp_action("down")) _walk_y += 1;
    } else if (_from_stick) {
        if (abs(_ax) > PP_STICK_DEADZONE) _walk_x = sign(_ax);
        if (abs(_ay) > PP_STICK_DEADZONE) _walk_y = sign(_ay);
    }
    _in.walk_x = _walk_x;
    _in.walk_y = _walk_y;
}

/// Cursor axis with repeat, for menus: -1, 0 or 1 on the step the player moves the cursor.
function pp_menu_axis(_negative, _positive) {
    var _dir = 0;
    if (pp_pressed(_negative) || pp_repeat(_negative)) _dir = -1;
    if (pp_pressed(_positive) || pp_repeat(_positive)) _dir = (_dir == -1) ? 0 : 1;
    return _dir;
}

// ---------------------------------------------------------------------------------------------------------------
// Text entry (spec 16 section 1 step 2, spec 21 section 2, card t_ee178652)
//
// The TALK box needs letters, and letters are the one thing a five action table cannot carry. The wrong fix is a
// keyboard_check inside the box, because then two places in the project read a key and spec 02 rule 1 stops being
// true. So the reader lives here, in the one module that may read a key, and the box asks for a character the same
// way every other feature asks for a press: once per step, from a value the sampler published.
//
// Three things this reader knows that a naive scan does not:
//   1. A letter is one key with two characters. Scanning 32 to 126 would report both A and a for one press, so the
//      letters are scanned once from A to Z and the case comes from the shift key.
//   2. A digit with shift is the mark above it, which is how ! " ' ( ) * : ? are typed at all: the sheet carries
//      those glyphs and a player with no letter grid would otherwise have no way to reach them.
//   3. A locked input reports nothing, so a key held from the step before a box opens cannot type into it.

/// Turn the reader on. The box calls this when it opens and pp_input_text_end when it closes, so a stray key in the
/// overworld never builds a string.
function pp_input_text_begin() {
    var _in = global.pp_input;
    if (!is_struct(_in)) return false;
    if (!variable_struct_exists(_in, "text_mode")) _in.text_mode = false;
    _in.text_mode = true;
    _in.text_char = "";
    _in.text_send = false;
    _in.text_back = false;
    _in.text_del = false;
    return true;
}

function pp_input_text_end() {
    var _in = global.pp_input;
    if (!is_struct(_in)) return false;
    _in.text_mode = false;
    _in.text_char = "";
    _in.text_send = false;
    _in.text_back = false;
    _in.text_del = false;
    return true;
}

function pp_input_text_active() {
    var _in = global.pp_input;
    if (!is_struct(_in) || !variable_struct_exists(_in, "text_mode")) return false;
    return (_in.text_mode == true);
}

/// The shift map for the marked digits and the two marks the sheet carries. Keyed by the unshifted ASCII code.
function pp_input_text_shift(_code) {
    switch (_code) {
        case 49: return "!";
        case 50: return "\"";
        case 51: return "";      // # is not on the sheet, so the key types nothing rather than a hole
        case 52: return "";      // $
        case 53: return "";      // %
        case 54: return "";      // &
        case 55: return "'";
        case 56: return "(";
        case 57: return ")";
        case 59: return ":";     // ; shifted
        case 47: return "?";     // / shifted
    }
    return "";
}

/// One sample per step, called from pp_input_sample. Everything is cleared every step, so a caller that reads
/// text_char twice reads the same character and a caller that never reads it costs nothing.
function pp_input_text_step() {
    var _in = global.pp_input;
    if (!is_struct(_in)) return;
    if (!variable_struct_exists(_in, "text_mode")) _in.text_mode = false;
    _in.text_char = "";
    _in.text_send = false;
    _in.text_back = false;
    _in.text_del = false;
    if (_in.text_mode != true) return;
    if (_in.lock_steps > 0) return;

    _in.text_send = keyboard_check_pressed(vk_enter);
    _in.text_back = keyboard_check_pressed(vk_escape);
    _in.text_del  = keyboard_check_pressed(vk_backspace);

    var _shift = keyboard_check(vk_shift);

    // Marks and digits first: every printable code that is not a letter.
    for (var _code = 32; _code <= 126; _code++) {
        if (_code >= 65 && _code <= 90) continue;                              // A to Z, handled below
        if (_code >= 97 && _code <= 122) continue;                              // a to z, same keys
        if (!keyboard_check_pressed(_code)) continue;
        var _char = chr(_code);
        if (_shift) {
            var _marked = pp_input_text_shift(_code);
            if (_marked != "") _char = _marked;
        }
        _in.text_char = _char;
        return;
    }

    // Then the letters, once each, with the case the player is holding.
    for (var _code = 65; _code <= 90; _code++) {
        if (!keyboard_check_pressed(_code)) continue;
        var _letter = chr(_code);
        if (!_shift) _letter = string_lower(_letter);
        _in.text_char = _letter;
        return;
    }
}
