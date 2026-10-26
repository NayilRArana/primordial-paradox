/// pp_talk_live: the fifth TALK entry, SAY IT YOURSELF (spec 16 section 1 step 2, spec 21, card t_ee178652 W2).
///
/// What this file is for. The first fight's authored options are words somebody wrote before the fight. This module
/// lets the player write the words during it: a line typed on the PC keyboard, built on an NES letter grid with the
/// d-pad, or spoken into the microphone and edited as a transcript. The line goes to the local AI bridge
/// (tools\ai_bridge.py, 127.0.0.1 only, started by tools\run.ps1) and the answer moves the enemy's WILL bar.
///
/// Three things this file refuses to do, because each of them is how a demo dies on stage:
///   1. It never blocks the step. A request is sent with http_request, which is asynchronous, and the box shows a
///      thinking beat while it waits. At the data file's timings.timeout_steps with no answer the deterministic fallback answers
///      and a late answer is thrown away, so a dead bridge costs a beat and not a fight (spec 16 section 12).
///   2. It never lets the fight stall. Three free text tries, then the fifth entry closes and the authored options
///      carry the fight to SPARE exactly as they did before this card (spec 16 section 2's +20 per option).
///   3. It never depends on the network in replay mode. Replay is the default; every exchange comes from
///      data/talk_live_tape.json and no socket is opened at all.
///
/// Where the rules live. Every number and every string the player reads is in data/talk_live.json, loaded once
/// through pp_data_json, which is the same door every other data file comes through. A missing or unreadable file
/// falls back to this file's own defaults and the box still opens, because a data file that can stop the signature
/// moment of the demo is a data file in the wrong place.
///
/// The protocol is tools/ai_bridge.py's, not ours to invent (knowledge\PROVENANCE.md, entry "the local AI bridge"):
///   POST /talk  {"encounter_id","npc","player_text","history":[{player_text,reply,verdict}],"will","mood"}
///        answer {"verdict","will_delta","reply":[lines],"source","origin","mood","cached","latency_ms"}
///   POST /hear  raw wav bytes -> {"transcript":"..."}
/// source is printed on the debug line for every answer, because "the WILL bar moved" is not evidence until the run
/// says WHERE the words came from (meta, open-weights, replay or fallback).
///
/// Provenance: knowledge\PROVENANCE.md, entry "input, menus and text entry across a whole game" (the letter grid is
/// the classic console shape, design studied, nothing copied) and "the local AI bridge". Written from specs 16, 21
/// and tools/ai_bridge.py's own documented contract. No line of the bridge's Python was transcribed into GML.

// ---------------------------------------------------------------------------------------------------------------
// The data

#macro PP_TALK_LIVE_GRID_MAX 64
#macro PP_TALK_LIVE_HISTORY_MAX 8
#macro PP_TALK_LIVE_BACK_HOLD 30
#macro PP_TALK_LIVE_RECORD_CAP 900
#macro PP_TALK_LIVE_COLS 28

/// The whole live path's data, normalised once. Fields with a default here are the ones a missing data file must not
/// take out with it; a field with no default is optional and read through pp_talk_live_str/int.
function pp_talk_live_data() {
    // The name is distinct from every function in this project on purpose: a script function is itself a global in
    // GMS 2.3+, so a cache stored under a function's own name answers with the function (the bug card t_27aa179e
    // cost the TALK panel one release build to learn).
    if (variable_global_exists("pp_talk_live_table") && is_struct(global.pp_talk_live_table)) {
        return global.pp_talk_live_table;
    }

    var _doc = pp_data_json("talk_live.json");
    var _d = {
        loaded: is_struct(_doc),
        version: 1,
        scheme: "http",
        host: "127.0.0.1",
        port: 8791,
        talk_path: "/talk",
        hear_path: "/hear",
        mode_default: "replay",
        chars_max: 120,
        cols: 28,
        rows_shown: 2,
        shown_max: 60,
        tries_max: 3,
        timeout_steps: 420,
        blink_steps: 30,
        dots_steps: 15,
        voice_enabled: true,
        voice_rate: 16000,
        voice_channels: 1,
        voice_bits: 16,
        voice_file: "cache/talk_voice.wav",
        voice_hold_min: 15,
        grid: [],
        grid_cols: 11,
        grid_rows: 4,
        prompt: "SAY IT YOURSELF",
        hint_keys: "TYPE  ENTER SEND  ESC BACK",
        hint_grid: "D PAD MOVE  A TYPE  START SEND",
        hint_voice: "HOLD F5 TO SPEAK",
        hint_wait: "HE IS LISTENING",
        tries_note: "That is enough talking.",
        empty_note: "Say something first.",
        will_max: 100,
        // The label the shipped data file carries. The fallback is the shipped value on purpose: a missing data file
        // must draw the same screen, not a second screen with two things called WILL on it.
        will_label: "MERCY"
    };

    if (is_struct(_doc)) {
        if (variable_struct_exists(_doc, "version")) _d.version = max(1, floor(_doc.version));
        if (variable_struct_exists(_doc, "bridge") && is_struct(_doc.bridge)) {
            var _b = _doc.bridge;
            _d.scheme = pp_talk_live_str(_b, "scheme", _d.scheme);
            _d.host = pp_talk_live_str(_b, "host", _d.host);
            _d.port = pp_talk_live_int(_b, "port", _d.port);
            _d.talk_path = pp_talk_live_str(_b, "talk_path", _d.talk_path);
            _d.hear_path = pp_talk_live_str(_b, "hear_path", _d.hear_path);
        }
        if (variable_struct_exists(_doc, "mode") && is_struct(_doc.mode)) {
            _d.mode_default = pp_talk_live_str(_doc.mode, "default", _d.mode_default);
        }
        if (variable_struct_exists(_doc, "limits") && is_struct(_doc.limits)) {
            var _l = _doc.limits;
            _d.chars_max = pp_talk_live_int(_l, "chars_max", _d.chars_max);
            _d.cols = pp_talk_live_int(_l, "cols_per_row", _d.cols);
            _d.rows_shown = pp_talk_live_int(_l, "chars_shown_rows", _d.rows_shown);
            _d.shown_max = pp_talk_live_int(_l, "shown_max", _d.shown_max);
            _d.tries_max = pp_talk_live_int(_l, "tries_max", _d.tries_max);
        }
        if (variable_struct_exists(_doc, "timings") && is_struct(_doc.timings)) {
            var _t = _doc.timings;
            _d.timeout_steps = pp_talk_live_int(_t, "timeout_steps", _d.timeout_steps);
            _d.blink_steps = pp_talk_live_int(_t, "cursor_blink_steps", _d.blink_steps);
            _d.dots_steps = pp_talk_live_int(_t, "dots_step_steps", _d.dots_steps);
        }
        if (variable_struct_exists(_doc, "voice") && is_struct(_doc.voice)) {
            var _v = _doc.voice;
            _d.voice_enabled = pp_talk_live_bool(_v, "enabled", _d.voice_enabled);
            _d.voice_rate = pp_talk_live_int(_v, "sample_rate", _d.voice_rate);
            _d.voice_channels = pp_talk_live_int(_v, "channels", _d.voice_channels);
            _d.voice_bits = pp_talk_live_int(_v, "bits", _d.voice_bits);
            _d.voice_file = pp_talk_live_str(_v, "file", _d.voice_file);
            _d.voice_hold_min = pp_talk_live_int(_v, "hold_steps_min", _d.voice_hold_min);
        }
        if (variable_struct_exists(_doc, "grid") && is_struct(_doc.grid)) {
            _d.grid_cols = pp_talk_live_int(_doc.grid, "cols", _d.grid_cols);
            _d.grid_rows = pp_talk_live_int(_doc.grid, "rows", _d.grid_rows);
            if (variable_struct_exists(_doc.grid, "cells") && is_array(_doc.grid.cells)) {
                var _cells = [];
                for (var i = 0; i < array_length(_doc.grid.cells); i++) {
                    array_push(_cells, string(_doc.grid.cells[i]));
                }
                _d.grid = _cells;
            }
        }
        if (variable_struct_exists(_doc, "strings") && is_struct(_doc.strings)) {
            var _s = _doc.strings;
            _d.prompt = pp_talk_live_str(_s, "prompt", _d.prompt);
            _d.hint_keys = pp_talk_live_str(_s, "hint_keys", _d.hint_keys);
            _d.hint_grid = pp_talk_live_str(_s, "hint_grid", _d.hint_grid);
            _d.hint_voice = pp_talk_live_str(_s, "hint_voice", _d.hint_voice);
            _d.hint_wait = pp_talk_live_str(_s, "hint_wait", _d.hint_wait);
            _d.tries_note = pp_talk_live_str(_s, "tries_note", _d.tries_note);
            _d.empty_note = pp_talk_live_str(_s, "empty_note", _d.empty_note);
        }
        if (variable_struct_exists(_doc, "will") && is_struct(_doc.will)) {
            _d.will_max = pp_talk_live_int(_doc.will, "max", _d.will_max);
            _d.will_label = pp_talk_live_str(_doc.will, "label", _d.will_label);
        }
    }

    // The two ranges this file will not run outside of. A host that is not a loopback literal would send the player's
    // own words off this machine, which is the one promise the bridge makes and the one promise a data edit could
    // break, so it is refused here and the live rung is simply not available.
    if (_d.host != "127.0.0.1" && _d.host != "localhost") {
        show_debug_message("PP: talk live host " + _d.host + " is not loopback, the live rung is off this run");
        _d.host = "127.0.0.1";
    }
    if (!pp_talk_live_loopback_port(_d.port)) _d.port = 8791;
    if (array_length(_d.grid) == 0) _d.grid = pp_talk_live_grid_default();
    if (_d.chars_max < 1) _d.chars_max = 120;
    if (_d.cols < 8) _d.cols = 28;
    if (_d.rows_shown < 1) _d.rows_shown = 2;
    if (_d.tries_max < 1) _d.tries_max = 3;
    if (_d.timeout_steps < 60) _d.timeout_steps = 420;
    if (_d.blink_steps < 1) _d.blink_steps = 30;

    global.pp_talk_live_table = _d;
    show_debug_message("PP: talk live data, " + (_d.loaded ? "loaded" : "defaults") + ", mode " + _d.mode_default
        + ", " + string(array_length(_d.grid)) + " grid cells, " + string(_d.tries_max) + " tries, "
        + string(_d.timeout_steps) + " step budget");
    return _d;
}

/// Forget the loaded data, so a scene reload or a test reads the file again.
function pp_talk_live_forget() {
    global.pp_talk_live_table = undefined;
    global.pp_talk_live_tape_table = undefined;
}

function pp_talk_live_str(_block, _key, _default) {
    if (!is_struct(_block) || !variable_struct_exists(_block, _key)) return _default;
    var _value = _block[$ _key];
    if (!is_string(_value)) return _default;
    return _value;
}

function pp_talk_live_int(_block, _key, _default) {
    if (!is_struct(_block) || !variable_struct_exists(_block, _key)) return _default;
    var _value = _block[$ _key];
    if (!is_real(_value)) return _default;
    return floor(_value);
}

function pp_talk_live_bool(_block, _key, _default) {
    if (!is_struct(_block) || !variable_struct_exists(_block, _key)) return _default;
    return (_block[$ _key] == true);
}

function pp_talk_live_loopback_port(_port) {
    return (is_real(_port) && _port > 0 && _port < 65536);
}

/// The grid the data file carries in the shipped build. It is spelled here too so a build with no data file still
/// has a working letter grid rather than an empty panel (spec 16 section 1's order: capitals, digits, marks, commands).
function pp_talk_live_grid_default() {
    return ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K",
            "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V",
            "W", "X", "Y", "Z", "0", "1", "2", "3", "4", "5", "6",
            "7", "8", "9", " ", ".", ",", "!", "?", "'", "DEL", "END"];
}

// ---------------------------------------------------------------------------------------------------------------
// The mode switch: replay (the demo, no socket) or live (the bridge)

/// True when this run asks the bridge. The build switch is PP_TALK_LIVE_MODE (pp_config.gml) and F6 flips it at run
/// time, so a recording can show both without a rebuild. Anything other than the two known words in the macro is
/// ignored and the data file's own default is used, because a typo in a macro is not a reason to go offline.
function pp_talk_live_mode() {
    var _d = pp_talk_live_data();
    var _macro = string(PP_TALK_LIVE_MODE);
    if (_macro == "live" || _macro == "replay") return _macro;
    if (!variable_global_exists("pp_talk_live_mode_override")) return _d.mode_default;
    var _override = string(global.pp_talk_live_mode_override);
    if (_override == "live" || _override == "replay") return _override;
    return _d.mode_default;
}

function pp_talk_live_is_live() {
    return (pp_talk_live_mode() == "live");
}

/// F6 in a debug build flips the mode and says so. The line names the mode, never the address (see the header).
function pp_talk_live_mode_flip() {
    var _next = pp_talk_live_is_live() ? "replay" : "live";
    global.pp_talk_live_mode_override = _next;
    show_debug_message("PP: talk live mode " + _next);
    return _next;
}

// ---------------------------------------------------------------------------------------------------------------
// The battle's own state

/// Every field the live path reads or writes, declared in one place so a key a struct does not carry is not a crash
/// on the first frame that reads it (the lesson of card t_771e78ef's stick_dir).
function pp_talk_live_state_init(_battle) {
    if (!is_struct(_battle)) return _battle;
    if (!variable_struct_exists(_battle, "live_stage")) _battle.live_stage = "";
    if (!variable_struct_exists(_battle, "live_text")) _battle.live_text = "";
    if (!variable_struct_exists(_battle, "live_mode")) _battle.live_mode = "keys";
    if (!variable_struct_exists(_battle, "live_grid")) _battle.live_grid = 0;
    if (!variable_struct_exists(_battle, "live_source")) _battle.live_source = "";
    if (!variable_struct_exists(_battle, "live_tries")) _battle.live_tries = 0;
    if (!variable_struct_exists(_battle, "live_handle")) _battle.live_handle = -1;
    if (!variable_struct_exists(_battle, "live_steps")) _battle.live_steps = 0;
    if (!variable_struct_exists(_battle, "live_note")) _battle.live_note = "";
    if (!variable_struct_exists(_battle, "live_note_steps")) _battle.live_note_steps = 0;
    if (!variable_struct_exists(_battle, "live_pending")) _battle.live_pending = "";
    if (!variable_struct_exists(_battle, "live_reply")) _battle.live_reply = [];
    if (!variable_struct_exists(_battle, "live_verdict")) _battle.live_verdict = "none";
    if (!variable_struct_exists(_battle, "live_mood")) _battle.live_mood = "guarded";
    if (!variable_struct_exists(_battle, "live_delta")) _battle.live_delta = 0;
    if (!variable_struct_exists(_battle, "live_history")) _battle.live_history = [];
    if (!variable_struct_exists(_battle, "live_voice_steps")) _battle.live_voice_steps = 0;
    if (!variable_struct_exists(_battle, "live_voice_buffer")) _battle.live_voice_buffer = undefined;
    if (!variable_struct_exists(_battle, "live_voice_channel")) _battle.live_voice_channel = -1;
    if (!variable_struct_exists(_battle, "live_cursor_steps")) _battle.live_cursor_steps = 0;
    if (!variable_struct_exists(_battle, "live_back_hold")) _battle.live_back_hold = 0;
    if (!variable_struct_exists(_battle, "live_deferred")) _battle.live_deferred = undefined;
    if (!variable_struct_exists(_battle, "live_deferred_steps")) _battle.live_deferred_steps = 0;
    return _battle;
}

/// True while the box owns the menu. The director asks this instead of testing a stage string, so the one place that
/// knows the stage names is this file.
function pp_talk_live_open_now(_battle) {
    if (!is_struct(_battle) || !variable_struct_exists(_battle, "live_stage")) return false;
    return (_battle.live_stage != "");
}

function pp_talk_live_tries_left(_battle) {
    var _d = pp_talk_live_data();
    if (!is_struct(_battle) || !variable_struct_exists(_battle, "live_tries")) return _d.tries_max;
    return max(0, _d.tries_max - _battle.live_tries);
}

/// Open the entry box. Called when the player picks the fifth entry, and by nothing else.
function pp_talk_live_open(_battle) {
    pp_talk_live_state_init(_battle);
    var _d = pp_talk_live_data();
    if (pp_talk_live_tries_left(_battle) <= 0) {
        _battle.live_note = _d.tries_note;
        _battle.live_note_steps = 90;
        pp_audio_play("menu_move");
        show_debug_message("PP: talk live refused, " + string(_battle.live_tries) + " tries used");
        return false;
    }
    _battle.live_stage = "entry";
    _battle.live_text = "";
    _battle.live_mode = "keys";
    _battle.live_grid = 0;
    _battle.live_pending = "";
    _battle.live_handle = -1;
    _battle.live_steps = 0;
    _battle.live_cursor_steps = 0;
    _battle.live_back_hold = 0;
    _battle.live_note = "";
    _battle.live_note_steps = 0;
    pp_input_text_begin();
    show_debug_message("PP: talk live open, mode " + pp_talk_live_mode() + ", try "
        + string(_battle.live_tries + 1) + " of " + string(_d.tries_max) + ", will " + string(_battle.talk_mercy));
    return true;
}

/// Put the box down without spending a try. Cancel, or the hold, or the end of the battle.
function pp_talk_live_close(_battle) {
    if (!is_struct(_battle)) return _battle;
    pp_talk_live_state_init(_battle);
    _battle.live_stage = "";
    _battle.live_pending = "";
    _battle.live_handle = -1;
    _battle.live_steps = 0;
    _battle.live_text = "";
    _battle.live_voice_buffer = undefined;
    pp_input_text_end();
    show_debug_message("PP: talk live closed, tries " + string(_battle.live_tries) + ", will "
        + string(_battle.talk_mercy));
    return _battle;
}

// ---------------------------------------------------------------------------------------------------------------
// The step machine. Stages: entry -> wait -> reply (or entry -> listen -> wait), and "" when closed.

function pp_talk_live_step(_battle) {
    if (!is_struct(_battle)) return;
    pp_talk_live_state_init(_battle);
    switch (_battle.live_stage) {
        case "entry":  pp_talk_live_step_entry(_battle);  break;
        case "listen": pp_talk_live_step_listen(_battle); break;
        case "wait":   pp_talk_live_step_wait(_battle);   break;
    }
    if (_battle.live_note_steps > 0) _battle.live_note_steps -= 1;
    if (_battle.live_note_steps == 0) _battle.live_note = "";
}

/// The box itself: typing, the grid, send, back, and the voice key.
function pp_talk_live_step_entry(_battle) {
    var _d = pp_talk_live_data();
    _battle.live_cursor_steps += 1;

    // The voice key, held. A recording shorter than the data's floor is refused with the low blip, so a brush
    // against the key is not a transcribe round trip.
    if (_d.voice_enabled && pp_pressed("live_voice")) {
        if (pp_talk_live_voice_start(_battle)) {
            _battle.live_stage = "listen";
            _battle.live_voice_steps = 0;
            pp_audio_play("menu_select");
            show_debug_message("PP: talk live listening, mode " + pp_talk_live_mode());
        }
        return;
    }

    if (_battle.live_mode == "grid") {
        pp_talk_live_step_grid(_battle);
        return;
    }

    // Keyboard mode. The characters come from pp_input's text reader, which is the only place in the project that
    // reads a key (spec 02 rule 1), and the arrow keys are how a player discovers the grid exists.
    var _in = global.pp_input;
    if (is_struct(_in) && variable_struct_exists(_in, "text_char") && is_string(_in.text_char)
        && _in.text_char != "") {
        pp_talk_live_typed(_battle, _in.text_char);
    }
    if (is_struct(_in) && variable_struct_exists(_in, "text_del") && _in.text_del == true) {
        pp_talk_live_delete(_battle);
    }
    if (is_struct(_in) && variable_struct_exists(_in, "text_send") && _in.text_send == true) {
        pp_talk_live_submit(_battle);
        return;
    }
    if (is_struct(_in) && variable_struct_exists(_in, "text_back") && _in.text_back == true) {
        pp_talk_live_abandon(_battle);
        return;
    }
    if (pp_pressed("left") || pp_pressed("right") || pp_pressed("up") || pp_pressed("down")
        || pp_repeat("up") || pp_repeat("down") || pp_repeat("left") || pp_repeat("right")) {
        _battle.live_mode = "grid";
        _battle.live_grid = pp_talk_live_grid_index_of(_battle, "END");
        if (_battle.live_grid < 0) _battle.live_grid = 0;
        pp_audio_play("menu_move");
        show_debug_message("PP: talk live grid, " + string(array_length(_d.grid)) + " cells, cursor "
            + string(_battle.live_grid));
    }
}

/// The letter grid: d-pad moves, confirm types the cell, cancel deletes, menu (START) sends, and a held cancel puts
/// the box down so a player without a keyboard is never trapped in it.
function pp_talk_live_step_grid(_battle) {
    var _d = pp_talk_live_data();
    var _cols = max(1, _d.grid_cols);
    var _n = array_length(_d.grid);
    if (_n == 0) { _battle.live_mode = "keys"; return; }

    var _dx = pp_menu_axis("left", "right");
    var _dy = pp_menu_axis("up", "down");
    if (_dx != 0 || _dy != 0) {
        var _col = _battle.live_grid mod _cols;
        var _row = _battle.live_grid div _cols;
        _col = (_col + _dx + _cols) mod _cols;
        var _rows = max(1, _d.grid_rows);
        _row = (_row + _dy + _rows) mod _rows;
        var _next = _row * _cols + _col;
        if (_next >= _n) _next = _n - 1;
        _battle.live_grid = _next;
        pp_audio_play("menu_move");
    }

    // A printed character on a keyboard still types, and it switches the box back to where the player is looking:
    // two input paths, one line, and no mode a player cannot leave.
    var _in = global.pp_input;
    if (is_struct(_in) && variable_struct_exists(_in, "text_char") && is_string(_in.text_char)
        && _in.text_char != "") {
        _battle.live_mode = "keys";
        pp_talk_live_typed(_battle, _in.text_char);
        return;
    }

    var _cell = pp_talk_live_grid_cell(_battle);
    if (pp_pressed("confirm")) {
        if (_cell == "DEL") {
            pp_talk_live_delete(_battle);
        } else if (_cell == "END") {
            pp_talk_live_submit(_battle);
            return;
        } else {
            pp_talk_live_typed(_battle, _cell);
        }
    }

    // Cancel deletes one character. HELD cancel puts the box down and returns to the keyboard: a player on a pad
    // alone must never be trapped in the grid, and the hold is the only exit that cannot be mistaken for a delete.
    if (pp_pressed("cancel")) {
        _battle.live_back_hold = 1;
        pp_talk_live_delete(_battle);
    } else if (pp_action("cancel")) {
        _battle.live_back_hold += 1;
        if (_battle.live_back_hold >= PP_TALK_LIVE_BACK_HOLD) {
            _battle.live_back_hold = 0;
            _battle.live_mode = "keys";
            pp_audio_play("menu_move");
            show_debug_message("PP: talk live grid held cancel, back to the keyboard");
        }
    } else {
        _battle.live_back_hold = 0;
    }

    if (pp_pressed("menu")) pp_talk_live_submit(_battle);
}

/// Recording. The engine has no device-rate query, so the wav's rate is the data file's (spec 21 section 3), and a
/// recording shorter than the floor is refused rather than transcribed.
function pp_talk_live_step_listen(_battle) {
    var _d = pp_talk_live_data();
    _battle.live_voice_steps += 1;
    if (pp_action("live_voice")) {
        if (_battle.live_voice_steps > PP_TALK_LIVE_RECORD_CAP) {
            pp_talk_live_voice_stop(_battle);
            _battle.live_stage = "entry";
            _battle.live_note = _d.empty_note;
            _battle.live_note_steps = 90;
            show_debug_message("PP: talk live recording hit the cap, refused");
        }
        return;
    }
    var _steps = _battle.live_voice_steps;
    var _buffer = pp_talk_live_voice_stop(_battle);
    _battle.live_stage = "entry";
    if (_steps < _d.voice_hold_min || is_undefined(_buffer)) {
        pp_audio_play("menu_move");
        _battle.live_note = _d.empty_note;
        _battle.live_note_steps = 90;
        show_debug_message("PP: talk live recording " + string(_steps) + " steps, under the "
            + string(_d.voice_hold_min) + " step floor, refused");
        return;
    }
    pp_talk_live_send_hear(_battle, _buffer);
}

/// The thinking beat. The dots animate; at the budget the fallback answers and a late reply is discarded. In replay
/// mode the recorded answer is deferred by the latency it was recorded with, so the thinking beat is on screen for as
/// long as a live answer would have taken and the demo's timing is the live timing (spec 21 check 4).
function pp_talk_live_step_wait(_battle) {
    var _d = pp_talk_live_data();
    _battle.live_steps += 1;
    if (is_struct(_battle.live_deferred)) {
        if (_battle.live_steps >= _battle.live_deferred_steps) {
            var _answer = _battle.live_deferred;
            _battle.live_deferred = undefined;
            _battle.live_deferred_steps = 0;
            pp_talk_live_answer(_battle, _answer, "replay");
        }
        return;
    }
    if (_battle.live_steps >= _d.timeout_steps) {
        show_debug_message("PP: talk live timeout at " + string(_battle.live_steps) + " steps, fallback answers");
        pp_talk_live_answer(_battle, pp_talk_live_tape_miss(_battle), "timeout");
    }
}

// ---------------------------------------------------------------------------------------------------------------
// The line itself

/// Append one character. Only characters the 8x8 sheet can draw reach the buffer, so a line the player sent can
/// never draw a hole on screen (spec 19 section 4's drawable rule, spec 13's one font).
function pp_talk_live_typed(_battle, _char) {
    var _d = pp_talk_live_data();
    if (!is_string(_char) || string_length(_char) == 0) return false;
    var _c = string_char_at(_char, 1);
    if (pp_font_glyph_index(_c) < 0) {
        pp_audio_play("menu_move");
        return false;
    }
    if (string_length(_battle.live_text) >= _d.chars_max) {
        pp_audio_play("menu_move");
        _battle.live_note = _d.tries_note;
        _battle.live_note_steps = 30;
        return false;
    }
    _battle.live_text += _c;
    pp_audio_play("menu_select");
    return true;
}

function pp_talk_live_delete(_battle) {
    var _n = string_length(_battle.live_text);
    if (_n <= 0) {
        pp_audio_play("menu_move");
        return false;
    }
    _battle.live_text = string_delete(_battle.live_text, _n, 1);
    pp_audio_play("menu_select");
    return true;
}

/// Esc: put the box down, spend nothing, and hand the menu back. A player who changes their mind owes no turn.
function pp_talk_live_abandon(_battle) {
    pp_audio_play("menu_move");
    show_debug_message("PP: talk live abandoned at " + string(string_length(_battle.live_text)) + " characters");
    pp_talk_live_close(_battle);
    // Back to the panel the player came from, not to the command list: a cancel that costs a press to undo is a
    // cancel a player stops using.
    if (is_array(_battle.talk_options) && array_length(_battle.talk_options) > 0) _battle.talk_stage = "options";
    return true;
}

/// Send. An empty line is refused and the box stays open, because an empty TALK is not a turn.
function pp_talk_live_submit(_battle) {
    var _d = pp_talk_live_data();
    var _line = pp_talk_live_scrub(_battle.live_text);
    if (_line == "") {
        pp_audio_play("menu_move");
        _battle.live_note = _d.empty_note;
        _battle.live_note_steps = 90;
        return false;
    }
    _battle.live_text = _line;
    _battle.live_tries += 1;
    _battle.live_steps = 0;
    _battle.live_pending = "talk";
    _battle.live_stage = "wait";
    _battle.live_note = "";
    _battle.live_note_steps = 0;
    pp_input_text_end();
    show_debug_message("PP: talk live send, try " + string(_battle.live_tries) + " of "
        + string(_d.tries_max) + ", mode " + pp_talk_live_mode() + ", " + string(string_length(_line)) + " chars");
    if (pp_talk_live_is_live()) {
        pp_talk_live_send_talk(_battle);
    } else {
        // Replay: the recorded answer, or the tape's miss row, deferred by the latency it was recorded with so the
        // box shows the thinking beat for as long as a live answer would have taken (spec 21 check 4).
        var _answer = pp_talk_live_tape_lookup(_battle, _line);
        var _wait = 6;
        if (is_struct(_answer) && variable_struct_exists(_answer, "latency_ms")) {
            _wait = clamp(round(_answer.latency_ms / 1000 * 60), 6, 120);
        }
        _battle.live_deferred = _answer;
        _battle.live_deferred_steps = _wait;
        _battle.live_steps = 0;
    }
    return true;
}

/// Everything the line must survive before it is a request: the sheet's alphabet, one space per run, no leading or
/// trailing space, and the length cap. The bridge scrubs again on its own side (tools/ai_bridge.py, "What is cleaned
/// before an answer leaves this module"); this is the game's copy of the rule, not a substitute for it.
function pp_talk_live_scrub(_text) {
    var _d = pp_talk_live_data();
    var _out = "";
    for (var i = 1; i <= string_length(_text); i++) {
        var _c = string_char_at(_text, i);
        if (pp_font_glyph_index(_c) < 0) continue;
        _out += _c;
    }
    _out = string_trim(_out);
    while (string_pos("  ", _out) > 0) _out = string_replace_all(_out, "  ", " ");
    if (string_length(_out) > _d.chars_max) _out = string_copy(_out, 1, _d.chars_max);
    return _out;
}

// ---------------------------------------------------------------------------------------------------------------
// The request and the answer

/// The JSON body of one /talk request, built from the bridge's documented contract. Nothing here names a key, a
/// file path, a save, a flag, the player's earlier lines or an exact hp: a prompt cannot leak what it never received.
function pp_talk_live_request(_battle) {
    var _d = pp_talk_live_data();
    var _body = {
        encounter_id: "",
        npc: "",
        player_text: _battle.live_text,
        will: _battle.talk_mercy,
        mood: _battle.talk_mood
    };
    if (is_struct(_battle.encounter) && variable_struct_exists(_battle.encounter, "id")) {
        _body.encounter_id = string(_battle.encounter.id);
    }
    // The card id comes from the encounter's own talk row when it names one, because spec 16 section 10 puts the card
    // identity there and the bridge keys its prompt on it; the enemy id is the fallback for a fight whose talk row
    // does not name a card yet.
    var _npc = "";
    if (is_struct(_battle.encounter) && variable_struct_exists(_battle.encounter, "talk")
        && is_struct(_battle.encounter.talk) && variable_struct_exists(_battle.encounter.talk, "card")) {
        _npc = string(_battle.encounter.talk.card);
    }
    if (_npc == "" && is_struct(_battle.enemy) && variable_struct_exists(_battle.enemy, "id")) {
        _npc = string(_battle.enemy.id);
    }
    _body.npc = _npc;
    var _history = [];
    if (is_array(_battle.live_history)) {
        var _start = max(0, array_length(_battle.live_history) - _d.tries_max);
        for (var i = _start; i < array_length(_battle.live_history); i++) {
            array_push(_history, _battle.live_history[i]);
        }
    }
    _body.history = _history;
    return json_stringify(_body);
}

/// The address, assembled from data at call time. No address string is written anywhere in this project's GML, and
/// that includes the scheme: "http" is a field in data/talk_live.json, so the only way to find an address here is to
/// read the data file. tests/test_talk_baked.py keeps that rule absolute by refusing an http(s):// literal in any
/// shipped module, so the scheme cannot quietly come back as a string.
function pp_talk_live_url(_path) {
    var _d = pp_talk_live_data();
    return _d.scheme + "://" + _d.host + ":" + string(_d.port) + _path;
}

/// One request in flight, always (spec 16 section 12). Sending a second while one is out would put two answers on
/// one turn, so a second send is refused and the box says it is still listening.
function pp_talk_live_send_talk(_battle) {
    var _d = pp_talk_live_data();
    if (!is_real(_battle.live_handle)) _battle.live_handle = -1;
    if (_battle.live_handle >= 0) {
        show_debug_message("PP: talk live send refused, a request is already in flight");
        return false;
    }
    var _headers = ds_map_create();
    ds_map_add(_headers, "Content-Type", "application/json");
    var _body = pp_talk_live_request(_battle);
    _battle.live_handle = http_request(pp_talk_live_url(_d.talk_path), "POST", _headers, _body);
    ds_map_destroy(_headers);
    _battle.live_pending = "talk";
    if (!is_real(_battle.live_handle) || _battle.live_handle < 0) {
        show_debug_message("PP: talk live request could not start, fallback answers");
        _battle.live_handle = -1;
        pp_talk_live_answer(_battle, pp_talk_live_tape_miss(_battle), "send_failed");
        return false;
    }
    show_debug_message("PP: talk live request " + string(_battle.live_handle) + " sent, "
        + string(string_length(_body)) + " bytes of body");
    return true;
}

/// The voice leg. The recorded buffer becomes a wav at the data file's rate, and the wav goes to /hear.
function pp_talk_live_send_hear(_battle, _buffer) {
    var _d = pp_talk_live_data();
    if (!pp_talk_live_is_live()) {
        // Replay: the demo's transcripts are part of the tape, so the voice path shows the same box the live path
        // does without a microphone and without a socket.
        var _hear = pp_talk_live_hear_replay(_battle, _buffer);
        if (is_string(_hear) && _hear != "") {
            _battle.live_text = _hear;
            show_debug_message("PP: talk live transcript (replay), " + string(string_length(_hear)) + " chars");
        }
        return false;
    }
    var _wav = pp_talk_live_wav(_buffer, _d.voice_rate, _d.voice_channels, _d.voice_bits);
    if (is_undefined(_wav)) return false;
    var _headers = ds_map_create();
    ds_map_add(_headers, "Content-Type", "audio/wav");
    _battle.live_handle = http_request(pp_talk_live_url(_d.hear_path), "POST", _headers, _wav);
    ds_map_destroy(_headers);
    _battle.live_pending = "hear";
    if (!is_real(_battle.live_handle) || _battle.live_handle < 0) {
        _battle.live_handle = -1;
        _battle.live_note = _d.empty_note;
        _battle.live_note_steps = 90;
        show_debug_message("PP: talk live hear request could not start");
        return false;
    }
    show_debug_message("PP: talk live hear request " + string(_battle.live_handle) + " sent, "
        + string(buffer_get_size(_wav)) + " wav bytes");
    return true;
}

// ---------------------------------------------------------------------------------------------------------------
// Recording (spec 16 section 1 step 2's voice leg)

/// Start the microphone. False when the engine or the machine has none, which is a note on screen and not a crash.
///
/// The arity here is the runtime's own, read from GmlSpec.xml in runtime-2026.0.0.23 rather than remembered:
/// audio_start_recording(recorder_index) returns the recorder CHANNEL, and audio_stop_recording(channel_index) takes
/// that channel back. Calling audio_stop_recording() with no argument is a compile error, which is how the first
/// version of this function failed the build at gml_GlobalScript_pp_talk_live(730).
function pp_talk_live_voice_start(_battle) {
    _battle.live_voice_steps = 0;
    _battle.live_voice_buffer = undefined;
    _battle.live_voice_channel = -1;
    // Ask the engine whether a source exists before opening a channel: a channel on a machine with no microphone
    // never delivers a buffer, and the box would sit in "listening" until the hold read as a failure.
    if (audio_get_recorder_count() <= 0) {
        show_debug_message("PP: talk live no recording device, the keyboard and the grid still work");
        return false;
    }
    var _channel = audio_start_recording(0);
    if (!is_real(_channel) || _channel < 0) {
        show_debug_message("PP: talk live the recorder refused a channel, the keyboard and the grid still work");
        return false;
    }
    _battle.live_voice_channel = _channel;
    return true;
}

/// Stop the microphone and keep the recorded buffer. The buffer arrives through the audio recording event
/// (obj_pp_game's Other_73), so this asks for the stop and hands back whatever the event has already stored.
function pp_talk_live_voice_stop(_battle) {
    var _channel = -1;
    if (variable_struct_exists(_battle, "live_voice_channel")) _channel = _battle.live_voice_channel;
    if (is_real(_channel) && _channel >= 0) audio_stop_recording(_channel);
    _battle.live_voice_channel = -1;
    var _buffer = _battle.live_voice_buffer;
    _battle.live_voice_buffer = undefined;
    return _buffer;
}

/// Called from the audio recording event. The buffer's own format is the device's; the header this writes is the
/// data file's, which is the one fact the engine does not hand back.
function pp_talk_live_voice_recorded(_battle, _buffer) {
    if (!is_struct(_battle)) return false;
    pp_talk_live_state_init(_battle);
    if (!buffer_exists(_buffer)) return false;
    _battle.live_voice_buffer = _buffer;
    show_debug_message("PP: talk live recording " + string(buffer_get_size(_buffer)) + " bytes");
    return true;
}

/// A 44 byte RIFF header and the recorded samples behind it. buffer_text writes the four character tags without a
/// terminator, which is why the header is exactly 44 bytes and not 48.
function pp_talk_live_wav(_src, _rate, _channels, _bits) {
    if (!buffer_exists(_src)) return undefined;
    var _size = buffer_get_size(_src);
    if (_size <= 0) return undefined;
    var _bytes = max(1, _bits div 8);
    var _out = buffer_create(44 + _size, buffer_fixed, 1);
    buffer_write(_out, buffer_text, "RIFF");
    buffer_write(_out, buffer_u32, 36 + _size);
    buffer_write(_out, buffer_text, "WAVE");
    buffer_write(_out, buffer_text, "fmt ");
    buffer_write(_out, buffer_u32, 16);
    buffer_write(_out, buffer_u16, 1);
    buffer_write(_out, buffer_u16, _channels);
    buffer_write(_out, buffer_u32, _rate);
    buffer_write(_out, buffer_u32, _rate * _channels * _bytes);
    buffer_write(_out, buffer_u16, _channels * _bytes);
    buffer_write(_out, buffer_u16, _bits);
    buffer_write(_out, buffer_text, "data");
    buffer_write(_out, buffer_u32, _size);
    buffer_seek(_src, buffer_seek_start, 0);
    buffer_copy(_src, 0, _size, _out, buffer_tell(_out));
    var _name = pp_talk_live_data().voice_file;
    buffer_save(_out, _name);
    return _out;
}

// ---------------------------------------------------------------------------------------------------------------
// The asynchronous answer

/// Called from obj_pp_game's HTTP event. async_load is a ds_map (the same read pp_save uses for its own event), and
/// the id is matched against the request this battle started, so an unrelated transfer is never mistaken for one of
/// ours. Every key is probed rather than assumed: the manual names "status" and "result" for the send and
/// "http_status" for the server's own code, and a build that reports one and not the other must still answer.
function pp_talk_live_async(_battle) {
    if (!is_struct(_battle)) return false;
    pp_talk_live_state_init(_battle);
    if (_battle.live_stage != "wait") return false;

    var _id = ds_map_find_value(async_load, "id");
    if (is_undefined(_id) || !is_real(_battle.live_handle) || _battle.live_handle < 0) return false;
    if (_id != _battle.live_handle) return false;

    _battle.live_handle = -1;
    var _http = ds_map_find_value(async_load, "http_status");
    var _status = ds_map_find_value(async_load, "status");
    var _result = ds_map_find_value(async_load, "result");
    var _ok = true;
    if (is_real(_http) && _http != 200) _ok = false;
    else if (!is_real(_http)) {
        if (is_real(_status) && _status != 0) _ok = false;
        if (is_real(_result) && _result != 0) _ok = false;
    }

    var _body = pp_talk_live_async_body();
    var _pending = _battle.live_pending;
    _battle.live_pending = "";

    if (!_ok) {
        show_debug_message("PP: talk live answer not ok, status " + string(_status) + ", http " + string(_http));
        pp_talk_live_answer(_battle, pp_talk_live_tape_miss(_battle), "transport_error");
        return true;
    }

    var _doc = json_parse(_body);
    if (_pending == "hear") return pp_talk_live_hear_answer(_battle, _doc);
    if (!is_struct(_doc)) {
        show_debug_message("PP: talk live answer is not a JSON object, fallback answers");
        pp_talk_live_answer(_battle, pp_talk_live_tape_miss(_battle), "refused");
        return true;
    }
    pp_talk_live_answer(_battle, _doc, "live");
    return true;
}

/// The response body as text. The buffer is read from its start whatever the handler left the seek at, and a body
/// that is a plain string (some builds deliver one) is used as it stands.
function pp_talk_live_async_body() {
    if (!ds_map_exists(async_load, "response_body")) return "";
    var _body = ds_map_find_value(async_load, "response_body");
    if (is_string(_body)) return _body;
    if (!buffer_exists(_body)) return "";
    if (buffer_get_size(_body) <= 0) return "";
    buffer_seek(_body, buffer_seek_start, 0);
    return buffer_read(_body, buffer_string);
}

/// The /hear answer is one field: the transcript, which fills the same box the keyboard fills so the player can fix
/// a word before sending it.
function pp_talk_live_hear_answer(_battle, _doc) {
    var _d = pp_talk_live_data();
    var _text = "";
    if (is_struct(_doc) && variable_struct_exists(_doc, "transcript") && is_string(_doc.transcript)) {
        _text = pp_talk_live_scrub(_doc.transcript);
    }
    if (_text == "") {
        _battle.live_note = _d.empty_note;
        _battle.live_note_steps = 90;
        show_debug_message("PP: talk live hear answer carried no transcript");
        return false;
    }
    _battle.live_text = _text;
    _battle.live_stage = "entry";
    _battle.live_steps = 0;
    pp_input_text_begin();
    show_debug_message("PP: talk live transcript, " + string(string_length(_text)) + " chars");
    return true;
}

// ---------------------------------------------------------------------------------------------------------------
// Applying an answer

/// Validate, clamp and apply one answer, then show it. This is the ONLY path from an answer to the game's state: an
/// answer is three fields and a label, and every consequence below is the game's own arithmetic (spec 16 section 2
/// rule 3). The will_delta is clamped to the meter's row for a talk turn, so no answer can move the bar further
/// than an authored option could.
function pp_talk_live_answer(_battle, _doc, _via) {
    var _d = pp_talk_live_data();
    var _answer = pp_talk_live_answer_clean(_doc);
    if (is_undefined(_answer)) {
        show_debug_message("PP: talk live answer refused (" + _via + "), fallback answers");
        _answer = pp_talk_live_answer_clean(pp_talk_live_tape_miss(_battle));
        if (is_undefined(_answer)) {
            pp_talk_live_close(_battle);
            return false;
        }
        _via = "fallback";
    }

    var _before = _battle.talk_mercy;
    var _delta = clamp(_answer.will_delta, -20, 20);
    _battle.talk_mercy = clamp(_before + _delta, 0, _d.will_max);
    _battle.live_delta = _battle.talk_mercy - _before;
    _battle.live_verdict = _answer.verdict;
    _battle.live_mood = _answer.mood;
    _battle.live_source = _answer.source;
    _battle.talk_mood = _answer.mood;
    _battle.talk_effect = pp_talk_live_verdict_effect(_answer.verdict);
    _battle.talk_delta = _battle.live_delta;
    _battle.talk_last_effect = _battle.talk_effect;

    // The history the bridge uses for the turn number and the last reply, never the player's earlier lines
    // (spec 19 section 3). Capped, so a long fight cannot grow a request without a bound.
    var _row = { player_text: "", reply: [], verdict: _answer.verdict };
    if (is_array(_battle.live_history) && array_length(_battle.live_history) >= PP_TALK_LIVE_HISTORY_MAX) {
        array_delete(_battle.live_history, 0, 1);
    }
    array_push(_battle.live_history, _row);

    // The reply goes to the same board every other action uses, in the same narration shape (`* ` plus the line),
    // so the enemy's turn follows the words exactly as it follows a FIGHT.
    var _lines = [];
    for (var i = 0; i < array_length(_answer.reply); i++) {
        array_push(_lines, "* " + _answer.reply[i]);
    }
    _battle.live_reply = _answer.reply;
    _battle.live_stage = "";
    _battle.live_steps = 0;
    _battle.live_handle = -1;
    _battle.live_pending = "";
    _battle.live_deferred = undefined;
    _battle.live_deferred_steps = 0;
    _battle.talk_reply = true;
    _battle.talk_hint = "";
    pp_input_text_end();

    // The evidence line. Every card in this lane has to be able to say WHERE the words came from, and "the WILL bar
    // moved" is not that claim until this line names it.
    show_debug_message("PP: talk live answer, source " + _answer.source + " via " + _via
        + ", verdict " + _answer.verdict + ", will_delta " + string(_battle.live_delta)
        + ", will " + string(_before) + " -> " + string(_battle.talk_mercy)
        + ", turn " + string(_battle.turn) + ", try " + string(_battle.live_tries)
        + ", lines " + string(array_length(_answer.reply)));

    pp_audio_play("menu_select");
    pp_battle_say(_battle, _lines, "enemy_turn");
    return true;
}

/// The failure a turn takes when nothing answered: the tape's own miss row, which is the same shape as a real
/// answer so nothing downstream has to test for "no answer at all".
function pp_talk_live_tape_miss(_battle) {
    var _tape = pp_talk_live_tape();
    if (is_struct(_tape) && variable_struct_exists(_tape, "miss") && is_struct(_tape.miss)) return _tape.miss;
    return {
        verdict: "unmoved",
        will_delta: 0,
        reply: ["YOU ARE NOT ON", "THE LIST."],
        source: "fallback",
        mood: "guarded"
    };
}

/// One answer, checked against the bridge's documented shape. Undefined means the whole answer is refused: no will
/// change, no reply on screen, and the fallback answers this turn.
function pp_talk_live_answer_clean(_doc) {
    if (!is_struct(_doc)) return undefined;
    if (!variable_struct_exists(_doc, "will_delta") || !is_real(_doc.will_delta)) return undefined;
    var _verdict = "unmoved";
    if (variable_struct_exists(_doc, "verdict") && is_string(_doc.verdict)) _verdict = _doc.verdict;
    if (!pp_talk_live_verdict_legal(_verdict)) _verdict = "unmoved";

    var _mood = pp_talk_live_verdict_mood(_verdict);
    if (variable_struct_exists(_doc, "mood") && is_string(_doc.mood) && pp_talk_mood_legal(_doc.mood)) {
        _mood = _doc.mood;
    }

    var _source = "unknown";
    if (variable_struct_exists(_doc, "source") && is_string(_doc.source)) _source = _doc.source;

    var _reply = [];
    if (variable_struct_exists(_doc, "reply") && is_array(_doc.reply)) {
        for (var i = 0; i < array_length(_doc.reply); i++) {
            if (array_length(_reply) >= pp_talk_lines_max()) break;
            var _line = string_trim(string(_doc.reply[i]));
            if (_line == "") continue;
            if (!pp_talk_line_drawable(_line)) continue;
            // The row width is the data file's own column count, the same number the box draws with (a function that
            // does not exist here was the one undefined call the project's compile-lite test found).
            var _cols = pp_talk_live_data().cols;
            if (string_length(_line) > _cols) _line = pp_talk_cut(_line, _cols);
            array_push(_reply, _line);
        }
    }
    if (array_length(_reply) == 0) {
        var _miss = pp_talk_live_tape_miss(undefined);
        _reply = _miss.reply;
        _source = "fallback";
    }
    return {
        will_delta: clamp(floor(_doc.will_delta), -20, 20),
        verdict: _verdict,
        mood: _mood,
        source: _source,
        reply: _reply
    };
}

function pp_talk_live_verdicts() { return ["persuaded", "unmoved", "angered"]; }

function pp_talk_live_verdict_legal(_verdict) {
    var _set = pp_talk_live_verdicts();
    for (var i = 0; i < array_length(_set); i++) {
        if (_set[i] == _verdict) return true;
    }
    return false;
}

/// The effect enum the rest of the talk code already speaks (spec 19 section 4): persuaded is a soften when it is a
/// full row and a nudge when it is a small one, angered is a setback, unmoved is nothing.
function pp_talk_live_verdict_effect(_verdict) {
    switch (_verdict) {
        case "persuaded": return "soften";
        case "angered":   return "setback";
    }
    return "none";
}

function pp_talk_live_verdict_mood(_verdict) {
    switch (_verdict) {
        case "persuaded": return "warm";
        case "angered":   return "angry";
    }
    return "guarded";
}

// ---------------------------------------------------------------------------------------------------------------
// The replay tape

function pp_talk_live_tape() {
    if (variable_global_exists("pp_talk_live_tape_table") && is_struct(global.pp_talk_live_tape_table)) {
        return global.pp_talk_live_tape_table;
    }
    var _doc = pp_data_json("talk_live_tape.json");
    var _tape = { loaded: false, exchanges: [], hear: [], miss: undefined };
    if (is_struct(_doc)) {
        _tape.loaded = true;
        if (variable_struct_exists(_doc, "exchanges") && is_array(_doc.exchanges)) _tape.exchanges = _doc.exchanges;
        if (variable_struct_exists(_doc, "hear") && is_array(_doc.hear)) _tape.hear = _doc.hear;
        if (variable_struct_exists(_doc, "miss") && is_struct(_doc.miss)) _tape.miss = _doc.miss;
    }
    global.pp_talk_live_tape_table = _tape;
    show_debug_message("PP: talk tape, " + (_tape.loaded ? "loaded" : "missing") + ", "
        + string(array_length(_tape.exchanges)) + " exchanges, " + string(array_length(_tape.hear)) + " transcripts");
    return _tape;
}

/// The recorded answer for one line on this enemy, or the miss row. The match is on the enemy id and the scrubbed
/// lower case line, so a capital letter or a double space does not miss a recording.
function pp_talk_live_tape_lookup(_battle, _line) {
    var _tape = pp_talk_live_tape();
    var _key = pp_talk_normalise(_line);
    var _enemy = "";
    if (is_struct(_battle) && is_struct(_battle.enemy) && variable_struct_exists(_battle.enemy, "id")) {
        _enemy = string(_battle.enemy.id);
    }
    for (var i = 0; i < array_length(_tape.exchanges); i++) {
        var _row = _tape.exchanges[i];
        if (!is_struct(_row) || !variable_struct_exists(_row, "answer")) continue;
        var _row_enemy = "";
        if (variable_struct_exists(_row, "enemy")) _row_enemy = string(_row.enemy);
        if (_row_enemy != _enemy) continue;
        var _row_line = "";
        if (variable_struct_exists(_row, "line")) _row_line = string(_row.line);
        if (pp_talk_normalise(_row_line) == _key) return _row.answer;
    }
    show_debug_message("PP: talk tape miss, the fallback row answers \"" + _key + "\"");
    return pp_talk_live_tape_miss(_battle);
}

/// The recorded transcript for the voice path. The buffer's own size picks the row, because a replay has no audio to
/// recognise: the demo's takes are recorded in order, so the Nth recording that is at least the floor answers with
/// the Nth transcript and a recording nobody made falls to an empty string.
function pp_talk_live_hear_replay(_battle, _buffer) {
    var _tape = pp_talk_live_tape();
    if (array_length(_tape.hear) == 0) return "";
    var _index = 0;
    if (is_struct(_battle) && variable_struct_exists(_battle, "live_tries")) _index = max(0, _battle.live_tries);
    if (_index >= array_length(_tape.hear)) _index = array_length(_tape.hear) - 1;
    var _row = _tape.hear[_index];
    if (!is_struct(_row) || !variable_struct_exists(_row, "transcript")) return "";
    return pp_talk_live_scrub(string(_row.transcript));
}

// ---------------------------------------------------------------------------------------------------------------
// The grid

function pp_talk_live_grid_cell(_battle) {
    var _d = pp_talk_live_data();
    var _n = array_length(_d.grid);
    if (_n == 0) return "";
    var _i = clamp(_battle.live_grid, 0, _n - 1);
    return string(_d.grid[_i]);
}

function pp_talk_live_grid_index_of(_battle, _cell) {
    var _d = pp_talk_live_data();
    for (var i = 0; i < array_length(_d.grid); i++) {
        if (string(_d.grid[i]) == _cell) return i;
    }
    return -1;
}

// ---------------------------------------------------------------------------------------------------------------
// The line as the box shows it

/// The rows the box draws: the two row window scrolled to the end of the line, cut at a space where one is near, and
/// never wider than the data's column count. This is presentation only: the line that is sent is the full buffer.
function pp_talk_live_rows(_text) {
    var _d = pp_talk_live_data();
    var _cols = _d.cols;
    var _cap = _cols * max(1, _d.rows_shown);
    var _tail = _text;
    if (string_length(_tail) > _cap) _tail = string_copy(_tail, string_length(_tail) - _cap + 1, _cap);
    var _rows = [];
    var _rest = _tail;
    while (string_length(_rest) > _cols) {
        var _cut = pp_talk_cut(_rest, _cols);
        array_push(_rows, _cut);
        _rest = string_delete(_rest, 1, string_length(_cut));
        if (string_char_at(_rest, 1) == " ") _rest = string_delete(_rest, 1, 1);
    }
    array_push(_rows, _rest);
    while (array_length(_rows) > max(1, _d.rows_shown)) array_delete(_rows, 0, 1);
    return _rows;
}

/// The column the cursor sits in on the last row, for the blinking underscore the sheet cannot draw.
function pp_talk_live_cursor_col(_rows) {
    if (array_length(_rows) == 0) return 0;
    var _last = _rows[array_length(_rows) - 1];
    return string_length(_last);
}

// ---------------------------------------------------------------------------------------------------------------
// Drawing. The box lives in the battle's message window (x 0 to 256, y 0 to 48), which is the one window the talk
// reply already uses, so the entry box costs no new geometry and no capture region moves.

// Card t_ee178652: the box lives inside the battle's message window, whose 2 pixel border owns rows 0, 1, 46 and 47
// and columns 0, 1, 254 and 255. The interior is therefore y 2 to 45, five whole 8 pixel rows. The first layout put
// the prompt on y 0 and the grid's last row on 40 to 47, which printed the grid over the window's own bottom border;
// the capture tool's border check caught it on the pixels. These are the five rows that fit.
function pp_talk_live_box_x() { return 8; }
function pp_talk_live_prompt_y() { return 2; }
function pp_talk_live_rows_y() { return 10; }
function pp_talk_live_row_pitch() { return 8; }
function pp_talk_live_hint_y() { return 34; }
function pp_talk_live_grid_y() { return 2; }
function pp_talk_live_grid_pitch() { return 20; }

function pp_talk_live_draw(_battle) {
    if (!is_struct(_battle) || _battle.live_stage == "") return;
    var _d = pp_talk_live_data();
    var _x = pp_talk_live_box_x();

    // The prompt and how many tries are left, on the window's first row.
    pp_font_draw("* " + _d.prompt, _x, pp_talk_live_prompt_y(), 1);
    var _counter = string(pp_talk_live_tries_left(_battle)) + "/" + string(_d.tries_max);
    var _cw = pp_font_width(_counter);
    pp_font_draw(_counter, PP_FRAME_W - 8 - _cw, pp_talk_live_prompt_y(), 1);

    switch (_battle.live_stage) {
        case "entry":
            if (_battle.live_mode == "grid") pp_talk_live_draw_grid(_battle);
            else pp_talk_live_draw_keys(_battle);
            break;

        case "listen":
            pp_font_draw(_d.hint_voice, _x, pp_talk_live_rows_y(), 1);
            pp_talk_live_draw_hint(_d.hint_wait);
            break;

        case "wait":
            pp_font_draw(pp_talk_live_dots(_battle.live_steps), _x, pp_talk_live_rows_y(), 1);
            pp_talk_live_draw_hint(_d.hint_wait);
            break;
    }

    if (_battle.live_note != "" && _battle.live_note_steps > 0) pp_talk_live_draw_hint(_battle.live_note);
}

function pp_talk_live_draw_keys(_battle) {
    var _d = pp_talk_live_data();
    var _rows = pp_talk_live_rows(_battle.live_text);
    var _x = pp_talk_live_box_x();
    for (var i = 0; i < array_length(_rows); i++) {
        pp_font_draw(_rows[i], _x, pp_talk_live_rows_y() + i * pp_talk_live_row_pitch(), 1);
    }

    // The cursor: six pixels of rule under the next character's cell, blinking at the data's rate. The sheet has no
    // underscore glyph, so this is a drawn rule and not a character (the reason spec 16 section 1 says 6 pixels).
    var _blink = _d.blink_steps * 2;
    if (_blink < 2) _blink = 60;
    if ((_battle.live_cursor_steps mod _blink) < _d.blink_steps) {
        var _col = pp_talk_live_cursor_col(_rows);
        var _row = max(0, array_length(_rows) - 1);
        draw_set_colour(pp_role_colour("text"));
        draw_rectangle(_x + _col * 8, pp_talk_live_rows_y() + _row * pp_talk_live_row_pitch() + 8,
                       _x + _col * 8 + 5, pp_talk_live_rows_y() + _row * pp_talk_live_row_pitch() + 8, false);
    }

    pp_talk_live_draw_hint(_d.hint_keys);
}

function pp_talk_live_draw_grid(_battle) {
    var _d = pp_talk_live_data();
    var _x = pp_talk_live_box_x();
    var _y = pp_talk_live_grid_y();
    var _pitch = pp_talk_live_grid_pitch();
    var _cols = max(1, _d.grid_cols);
    var _n = array_length(_d.grid);
    var _tail = pp_talk_live_rows(_battle.live_text);
    if (array_length(_tail) > 0) pp_font_draw("* " + _tail[array_length(_tail) - 1], _x, pp_talk_live_hint_y(), 1);

    for (var i = 0; i < _n; i++) {
        var _cell = string(_d.grid[i]);
        var _cx = _x + (i mod _cols) * _pitch;
        var _cy = _y + (i div _cols) * 8;
        // The window's border owns y 46 and 47, so a cell whose bottom would reach them is not drawn at all: a grid
        // that prints a letter over the frame is worse than a grid one row shorter.
        if (_cy + 8 > 46) break;
        pp_font_draw(_cell, _cx, _cy, 1);
        if (i == _battle.live_grid) {
            // The selected cell carries a one pixel rule under it: one ink, no tint, and no colour the room's palette
            // set has to carry (rule 6 of the font contract).
            draw_set_colour(pp_role_colour("text"));
            draw_rectangle(_cx, _cy + 8, _cx + 7, _cy + 8, false);
        }
    }

    // In grid mode the hint row carries the line being built instead of the controls: the row is the only one left
    // inside the window, the cells themselves show what the d-pad does, and escape returns the controls in one press.
    if (array_length(_tail) == 0) pp_talk_live_draw_hint(_d.hint_grid);
}

function pp_talk_live_draw_hint(_text) {
    if (!is_string(_text) || _text == "") return;
    pp_font_draw(pp_talk_cut(_text, pp_talk_live_data().cols), pp_talk_live_box_x(), pp_talk_live_hint_y(), 1);
}

/// The thinking beat: one dot per data step, then a second and a third, and it stays at three. It is not a spinner,
/// because a spinner at 60 steps a second reads as a game that is busy rather than a game that is waiting.
function pp_talk_live_dots(_steps) {
    var _d = pp_talk_live_data();
    var _n = 1 + floor(max(0, _steps) / max(1, _d.dots_step_steps));
    if (_n > 3) _n = 3;
    var _out = "*";
    for (var i = 0; i < _n; i++) _out += " .";
    return _out;
}
