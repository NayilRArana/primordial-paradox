/// pp_touch: the on screen touch controls for the touch targets (spec 22).
/// An 8 direction pad for the left thumb and A, B and Menu buttons for the right thumb, drawn in the room palette,
/// semi transparent, and merged into pp_input's action table, so the game reads one action map and the pad, the
/// buttons and the keyboard all land on the same seven actions (spec 02 rule 1). Touch is the second input source
/// beside the keys and the pad, so this module is the one place a finger is read, the way pp_input is the one place a
/// key is read; pp_input consumes this module's held map and publishes the edges every reader already knows.
/// Only the touch targets sample and draw it (os_android, os_operagx, os_browser), so the Windows desktop build is
/// unchanged: this module never runs there, and where it runs it only ADDS held actions, it never eats a key, a pad
/// button or a mouse click. Desktop play does not change.
/// Provenance: knowledge\PROVENANCE.md, entry "pp_touch", written from specs\22-touch-overlay.md.

#macro PP_TOUCH_MAX 4
#macro PP_TOUCH_ALPHA 0.55
#macro PP_TOUCH_DEAD 8

/// Build the touch state. Called once from pp_app_boot, beside the other one time state.
function pp_touch_init() {
    global.pp_touch = {
        enabled: pp_touch_platform(),
        held: {},
        pad_active: false,
        pad_kx: 0,
        pad_ky: 0,
        pad_sector: -1,
        pad_finger: -1,
        a_finger: -1,
        b_finger: -1,
        menu_finger: -1
    };
    var _t = global.pp_touch;
    _t.held[$ "confirm"] = false;
    _t.held[$ "cancel"] = false;
    _t.held[$ "menu"] = false;
    _t.held[$ "up"] = false;
    _t.held[$ "down"] = false;
    _t.held[$ "left"] = false;
    _t.held[$ "right"] = false;
    return _t;
}

/// The touch targets. os_windows (the desktop) is deliberately absent, so the overlay cannot draw there.
function pp_touch_platform() {
    var _os = os_type;
    return (_os == os_android || _os == os_operagx || _os == os_browser);
}

function pp_touch_enabled() {
    if (!is_struct(global.pp_touch)) return false;
    return (global.pp_touch.enabled == true);
}

/// The free play layout: the pad bottom left, A, B and Menu bottom right, all inside the frame.
function pp_touch_layout_free() {
    return {
        pad:  { cx: 48,  cy: 190, r: 28 },
        a:    { cx: 204, cy: 198, r: 24 },
        b:    { cx: 236, cy: 174, r: 16 },
        menu: { cx: 236, cy: 134, r: 14 }
    };
}

/// The text layout: every control above the dialogue box (y 168), so the overlay never sits on the box's rows. The
/// pad moves to the top left, A and B stack at the top right, and Menu is hidden, because the box already owns the
/// bottom band and the pad is only needed to move a choice cursor.
function pp_touch_layout_text() {
    return {
        pad:  { cx: 44,  cy: 56,  r: 24 },
        a:    { cx: 216, cy: 128, r: 22 },
        b:    { cx: 232, cy: 88,  r: 16 },
        menu: undefined
    };
}

function pp_touch_layout() {
    if (pp_touch_text_open()) return pp_touch_layout_text();
    return pp_touch_layout_free();
}

/// True when a text box is showing, so the overlay moves off it. Two owners can show one: the overworld's own
/// dialogue (a say trigger or a talk, drawn by pp_overworld_draw) and a running scene's dialogue. Battle narration is
/// drawn at the top of the frame, not in the box, so a fight stays on the free layout.
function pp_touch_text_open() {
    if (pp_app_mode() != PPMode.overworld) return false;
    var _w = global.pp.world;
    if (!is_struct(_w)) return false;
    if (!pp_dialogue_closed(_w.dialogue)) return true;
    if (is_struct(_w.scene) && !pp_dialogue_closed(_w.scene.dialogue)) return true;
    return false;
}

/// True when the point is inside the circle. A control is a disc, so the test is one distance.
function pp_touch_in(_mx, _my, _c) {
    if (is_undefined(_c)) return false;
    return (point_distance(_mx, _my, _c.cx, _c.cy) <= _c.r);
}

/// Read one finger against the pad: set the knob for the draw and the sector for the walk. A finger inside the
/// deadzone is neutral; past it the angle is rounded to one of eight 45 degree sectors, the same eight the keys make.
function pp_touch_pad_read(_t, _mx, _my, _pad) {
    var _dx = _mx - _pad.cx;
    var _dy = _my - _pad.cy;
    var _len = point_distance(0, 0, _dx, _dy);
    _t.pad_active = true;
    if (_len > 0) {
        var _klen = min(_len, _pad.r);
        _t.pad_kx = _dx / _len * _klen;
        _t.pad_ky = _dy / _len * _klen;
    } else {
        _t.pad_kx = 0;
        _t.pad_ky = 0;
    }
    if (_len <= PP_TOUCH_DEAD) {
        _t.pad_sector = -1;
        return;
    }
    _t.pad_sector = round(point_direction(0, 0, _dx, _dy) / 45) mod 8;
}

/// One sample per step, called at the top of pp_input_sample, before the action loop. Every touch is read once, each
/// finger keeps the control it pressed down on until it lifts, and the result is the held map pp_input merges in.
function pp_touch_sample() {
    var _t = global.pp_touch;
    if (!is_struct(_t) || !_t.enabled) return;

    var _held = _t.held;
    _held[$ "confirm"] = false;
    _held[$ "cancel"] = false;
    _held[$ "menu"] = false;
    _held[$ "up"] = false;
    _held[$ "down"] = false;
    _held[$ "left"] = false;
    _held[$ "right"] = false;

    var _l = pp_touch_layout();
    var _pad = _l.pad;
    var _a = _l.a;
    var _b = _l.b;
    var _menu = _l.menu;

    for (var _d = 0; _d <= PP_TOUCH_MAX; _d += 1) {
        if (device_mouse_check_button_released(_d, mb_any)) {
            if (_d == _t.pad_finger) {
                _t.pad_finger = -1;
                _t.pad_active = false;
                _t.pad_sector = -1;
                _t.pad_kx = 0;
                _t.pad_ky = 0;
            }
            if (_d == _t.a_finger) _t.a_finger = -1;
            if (_d == _t.b_finger) _t.b_finger = -1;
            if (_d == _t.menu_finger) _t.menu_finger = -1;
            continue;
        }
        if (!device_mouse_check_button(_d, mb_any)) continue;

        // The finger is down. A finger that owns nothing yet takes the control under it; after that it keeps that
        // control even if it slides off, which is what makes a thumb drag out of the pad keep walking instead of drop.
        if (_d != _t.pad_finger && _d != _t.a_finger && _d != _t.b_finger && _d != _t.menu_finger) {
            var _mx = device_mouse_x(_d);
            var _my = device_mouse_y(_d);
            if (pp_touch_in(_mx, _my, _pad)) _t.pad_finger = _d;
            else if (pp_touch_in(_mx, _my, _a)) _t.a_finger = _d;
            else if (pp_touch_in(_mx, _my, _b)) _t.b_finger = _d;
            else if (pp_touch_in(_mx, _my, _menu)) _t.menu_finger = _d;
        }

        if (_d == _t.pad_finger) pp_touch_pad_read(_t, device_mouse_x(_d), device_mouse_y(_d), _pad);
        if (_d == _t.a_finger) _held[$ "confirm"] = true;
        if (_d == _t.b_finger) _held[$ "cancel"] = true;
        if (_d == _t.menu_finger) _held[$ "menu"] = true;
    }

    if (_t.pad_active) {
        var _s = _t.pad_sector;
        if (_s >= 0) {
            _held[$ "up"]    = (_s == 1 || _s == 2 || _s == 3);
            _held[$ "down"]  = (_s == 5 || _s == 6 || _s == 7);
            _held[$ "left"]  = (_s == 3 || _s == 4 || _s == 5);
            _held[$ "right"] = (_s == 0 || _s == 1 || _s == 7);
        }
    }
}

/// The held state one action reads from the touch controls. pp_input merges this into the same action table the keys
/// and the pad write, so a reader never knows whether a press came from a finger or a key.
function pp_touch_held(_action) {
    var _t = global.pp_touch;
    if (!is_struct(_t) || !is_struct(_t.held)) return false;
    if (!variable_struct_exists(_t.held, string(_action))) return false;
    return (_t.held[$ string(_action)] == true);
}

/// Draw the pad: a paper disc, an ink ring, a light cross, and the thumb knob where the finger is, inside the ring.
function pp_touch_draw_pad(_t, _pad) {
    draw_set_colour(pp_role_colour("paper"));
    draw_circle(_pad.cx, _pad.cy, _pad.r, false);
    draw_set_colour(pp_role_colour("ink"));
    draw_circle(_pad.cx, _pad.cy, _pad.r, true);
    draw_set_colour(pp_role_colour("text"));
    draw_line(_pad.cx, _pad.cy - _pad.r, _pad.cx, _pad.cy + _pad.r);
    draw_line(_pad.cx - _pad.r, _pad.cy, _pad.cx + _pad.r, _pad.cy);
    if (_t.pad_active) {
        draw_circle(_pad.cx + _t.pad_kx, _pad.cy + _t.pad_ky, 6, false);
    }
}

/// Draw one button: a disc that brightens while held, an ink ring, and the sheet's letter centred on it.
function pp_touch_draw_button(_c, _label, _held) {
    draw_set_colour(pp_role_colour(_held ? "text" : "paper"));
    draw_circle(_c.cx, _c.cy, _c.r, false);
    draw_set_colour(pp_role_colour("ink"));
    draw_circle(_c.cx, _c.cy, _c.r, true);
    draw_set_alpha(1);
    pp_font_draw(_label, _c.cx - 4, _c.cy - 4, 1);
    draw_set_alpha(PP_TOUCH_ALPHA);
}

/// Draw the Menu button: the same disc and ring, but the mark is three lines, the console pause glyph.
function pp_touch_draw_menu(_c) {
    draw_set_colour(pp_role_colour("paper"));
    draw_circle(_c.cx, _c.cy, _c.r, false);
    draw_set_colour(pp_role_colour("ink"));
    draw_circle(_c.cx, _c.cy, _c.r, true);
    draw_set_colour(pp_role_colour("text"));
    draw_line(_c.cx - 6, _c.cy - 4, _c.cx + 6, _c.cy - 4);
    draw_line(_c.cx - 6, _c.cy,     _c.cx + 6, _c.cy);
    draw_line(_c.cx - 6, _c.cy + 4, _c.cx + 6, _c.cy + 4);
}

/// Draw the overlay over the mode, under the save panel and the fade. Called from pp_app_draw.
function pp_touch_draw() {
    var _t = global.pp_touch;
    if (!is_struct(_t) || !_t.enabled) return;

    draw_set_alpha(PP_TOUCH_ALPHA);
    var _l = pp_touch_layout();
    pp_touch_draw_pad(_t, _l.pad);
    pp_touch_draw_button(_l.a, "A", pp_touch_held("confirm"));
    pp_touch_draw_button(_l.b, "B", pp_touch_held("cancel"));
    if (!is_undefined(_l.menu)) pp_touch_draw_menu(_l.menu);
    draw_set_alpha(1);
}
