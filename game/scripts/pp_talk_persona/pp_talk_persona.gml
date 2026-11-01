/// pp_talk_persona: the live TALK box opened outside a fight, answering as one of the three persona cards
/// (card t_0fda85b8, spec 21 section 11). The box is spec 21 sections 1 and 2's box (pp_talk_live), opened
/// with a persona id instead of a battle: a chat, no meter, no tries burned, effects none and end, and ESC
/// leaves without a turn. The reply draws in the same message window with the same `* ` marker and 8 pixel
/// pitch, and the persona's name plate is the card's `name` field, read from data/talk_personas.json.

// ---------------------------------------------------------------------------------------------------------------
// The cards

/// The persona cards from data/talk_personas.json, indexed by id. Loaded once; a missing file leaves the table
/// unloaded and the box refuses to open rather than guess a name plate.
function pp_talk_persona_cards() {
    if (variable_global_exists("pp_talk_persona_cards_table") && is_struct(global.pp_talk_persona_cards_table)) {
        return global.pp_talk_persona_cards_table;
    }
    var _table = { loaded: false, by_id: {} };
    var _doc = pp_data_json("talk_personas.json");
    if (is_struct(_doc) && variable_struct_exists(_doc, "personas") && is_array(_doc.personas)) {
        _table.loaded = true;
        for (var i = 0; i < array_length(_doc.personas); i++) {
            var _row = _doc.personas[i];
            if (is_struct(_row) && variable_struct_exists(_row, "id")) {
                _table.by_id[$ string(_row.id)] = _row;
            }
        }
    }
    global.pp_talk_persona_cards_table = _table;
    return _table;
}

/// One persona card by id, or undefined when the id is unknown or the file did not load.
function pp_talk_persona_card(_id) {
    var _table = pp_talk_persona_cards();
    if (!_table.loaded) return undefined;
    var _key = string(_id);
    if (!variable_struct_exists(_table.by_id, _key)) return undefined;
    return _table.by_id[$ _key];
}

/// The name plate: the card's `name` field, uppercased so a lowercase edit of the card still draws a plate.
function pp_talk_persona_name(_id) {
    var _card = pp_talk_persona_card(_id);
    if (is_struct(_card) && variable_struct_exists(_card, "name") && string(_card.name) != "") {
        return string_upper(string(_card.name));
    }
    return string_upper(string(_id));
}

// ---------------------------------------------------------------------------------------------------------------
// State

/// Build the persona talk state. It carries the same live_* fields the box steps on, plus the persona fields that
/// make it a chat with no fight: no meter, no tries, no enemy, and a finished flag the mode reads to hand back.
function pp_talk_persona_new(_id) {
    var _state = {
        persona: string(_id),
        persona_name: pp_talk_persona_name(_id),
        talk_mercy: 0,
        talk_mood: "guarded",
        talk_options: [],
        talk_stage: "",
        turn: 1,
        reply_steps: 0,
        finished: false
    };
    pp_talk_live_state_init(_state);
    return _state;
}

/// True when a persona card exists for this id.
function pp_talk_persona_known(_id) {
    return !is_undefined(pp_talk_persona_card(_id));
}

// ---------------------------------------------------------------------------------------------------------------
// Open, submit, request, answer

/// Open the box for one persona. Reuses the box's entry stage; the persona path skips the tries gate (a chat has
/// no tries) and the name plate comes from the card.
function pp_talk_persona_open(_state) {
    if (!is_struct(_state)) return false;
    if (!pp_talk_persona_known(_state.persona)) return false;
    pp_talk_live_state_init(_state);
    _state.live_stage = "entry";
    _state.live_text = "";
    _state.live_mode = "keys";
    _state.live_grid = 0;
    _state.live_pending = "";
    _state.live_handle = -1;
    _state.live_steps = 0;
    _state.live_cursor_steps = 0;
    _state.live_back_hold = 0;
    _state.live_note = "";
    _state.live_note_steps = 0;
    _state.live_reply = [];
    _state.reply_steps = 0;
    _state.finished = false;
    pp_input_text_begin();
    show_debug_message("PP: talk persona open, persona " + _state.persona + ", mode " + pp_talk_live_mode());
    return true;
}

/// Esc: put the box down and hand the map back, spending no turn and no try.
function pp_talk_persona_abandon(_state) {
    pp_audio_play("menu_move");
    show_debug_message("PP: talk persona abandoned at " + string(string_length(_state.live_text)) + " characters");
    pp_talk_live_close(_state);
    _state.finished = true;
    return true;
}

/// Send the line. An empty line is refused and the box stays open, because an empty TALK is not a turn.
function pp_talk_persona_submit(_state) {
    var _d = pp_talk_live_data();
    var _line = pp_talk_live_scrub(_state.live_text);
    if (_line == "") {
        pp_audio_play("menu_move");
        _state.live_note = _d.empty_note;
        _state.live_note_steps = 90;
        return false;
    }
    _state.live_text = _line;
    _state.live_steps = 0;
    _state.live_pending = "talk";
    _state.live_stage = "wait";
    _state.live_note = "";
    _state.live_note_steps = 0;
    pp_input_text_end();
    show_debug_message("PP: talk persona send, persona " + _state.persona + ", mode " + pp_talk_live_mode()
        + ", " + string(string_length(_line)) + " chars");
    if (pp_talk_live_is_live()) {
        pp_talk_live_send_talk(_state);
    } else {
        // Replay: no local recorded persona answers live in the bundle, so the persona's own fallback_pool answers.
        // Offline the miss falls to fallback_pool, which is the card's own rule.
        var _answer = pp_talk_persona_replay(_state);
        var _wait = 6;
        _state.live_deferred = _answer;
        _state.live_deferred_steps = _wait;
        _state.live_steps = 0;
    }
    return true;
}

/// The JSON body of one persona /talk request: a chat, so no encounter, no will and no meter. The bridge keys its
/// cache on the persona block and this player line (spec 21 section 11).
function pp_talk_persona_request(_state) {
    var _history = [];
    if (is_array(_state.live_history)) {
        var _start = max(0, array_length(_state.live_history) - PP_TALK_LIVE_HISTORY_MAX);
        for (var i = _start; i < array_length(_state.live_history); i++) {
            array_push(_history, _state.live_history[i]);
        }
    }
    var _body = {
        persona: _state.persona,
        player_text: _state.live_text,
        turn: max(1, array_length(_history) + 1),
        mood: "guarded"
    };
    _body.history = _history;
    return json_stringify(_body);
}

/// The offline answer for a persona: its own fallback_pool, one line, cycled so two misses read differently.
function pp_talk_persona_replay(_state) {
    var _card = pp_talk_persona_card(_state.persona);
    var _pool = [];
    if (is_struct(_card) && variable_struct_exists(_card, "fallback_pool") && is_array(_card.fallback_pool)) {
        _pool = _card.fallback_pool;
    }
    if (array_length(_pool) == 0) _pool = ["USE THE DESK."];
    var _index = 0;
    if (is_array(_state.live_history)) _index = array_length(_state.live_history) mod array_length(_pool);
    var _line = pp_talk_persona_answer_clean({ text: [string(_pool[_index])], mood: "guarded", effect: "none", hint: "" });
    if (is_undefined(_line)) _line = { reply: [string(_pool[_index])], mood: "guarded" };
    return _line;
}

/// One persona answer, checked against the bridge's persona shape (text, mood, effect, hint). Undefined means the
/// whole answer is refused and the fallback answers. Two lines, 28 characters, exactly the card's answer_cap.
function pp_talk_persona_answer_clean(_doc) {
    if (!is_struct(_doc)) return undefined;
    var _reply = [];
    if (variable_struct_exists(_doc, "text") && is_array(_doc.text)) {
        var _cols = pp_talk_live_data().cols;
        for (var i = 0; i < array_length(_doc.text); i++) {
            if (array_length(_reply) >= 2) break;
            var _line = string_trim(string(_doc.text[i]));
            if (_line == "") continue;
            if (!pp_talk_line_drawable(_line)) continue;
            if (string_length(_line) > _cols) _line = pp_talk_cut(_line, _cols);
            array_push(_reply, _line);
        }
    }
    if (array_length(_reply) == 0) return undefined;
    var _mood = "guarded";
    if (variable_struct_exists(_doc, "mood") && is_string(_doc.mood) && pp_talk_mood_legal(_doc.mood)) {
        _mood = _doc.mood;
    }
    return { reply: _reply, mood: _mood };
}

/// Apply one persona answer. No meter, no verdict, no turn: the reply goes to the box's own window and the box
/// closes into the reply, which the mode draws until the player confirms.
function pp_talk_persona_answer(_state, _doc, _via) {
    var _answer = pp_talk_persona_answer_clean(_doc);
    if (is_undefined(_answer)) {
        show_debug_message("PP: talk persona answer refused (" + string(_via) + "), fallback answers");
        _answer = pp_talk_persona_replay(_state);
        _via = "fallback";
    }
    // The history the bridge keys the turn and the last reply on, never the player's earlier lines (spec 19 section 3).
    var _row = { player_text: "", reply: [], effect: "none" };
    _row.reply = _answer.reply;
    if (is_array(_state.live_history) && array_length(_state.live_history) >= PP_TALK_LIVE_HISTORY_MAX) {
        array_delete(_state.live_history, 0, 1);
    }
    array_push(_state.live_history, _row);

    _state.live_reply = _answer.reply;
    _state.live_mood = _answer.mood;
    _state.live_source = _via;
    _state.live_stage = "";
    _state.live_steps = 0;
    _state.live_handle = -1;
    _state.live_pending = "";
    _state.live_deferred = undefined;
    _state.live_deferred_steps = 0;
    _state.reply_steps = 0;
    pp_input_text_end();
    show_debug_message("PP: talk persona answer via " + string(_via) + ", lines "
        + string(array_length(_state.live_reply)));
    pp_audio_play("menu_select");
    return true;
}

// ---------------------------------------------------------------------------------------------------------------
// The async handler. Mirrors pp_talk_live_async against the persona state, so the two /talk and /hear sites in
// pp_talk_live stay the project's only network path.

function pp_talk_persona_async(_state) {
    if (!is_struct(_state)) return false;
    pp_talk_live_state_init(_state);
    if (_state.live_stage != "wait") return false;
    var _id = ds_map_find_value(async_load, "id");
    if (is_undefined(_id) || !is_real(_state.live_handle) || _state.live_handle < 0) return false;
    if (_id != _state.live_handle) return false;
    _state.live_handle = -1;
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
    _state.live_pending = "";
    if (!_ok) {
        show_debug_message("PP: talk persona answer not ok, status " + string(_status) + ", http " + string(_http));
        pp_talk_persona_answer(_state, pp_talk_persona_replay(_state), "transport_error");
        return true;
    }
    var _doc = json_parse(_body);
    if (!is_struct(_doc)) {
        show_debug_message("PP: talk persona answer is not a JSON object, fallback answers");
        pp_talk_persona_answer(_state, pp_talk_persona_replay(_state), "refused");
        return true;
    }
    pp_talk_persona_answer(_state, _doc, "live");
    return true;
}

// ---------------------------------------------------------------------------------------------------------------
// The step and the draw, and the mode the app registers

/// The reply rows as the box draws them: `* ` plus each line, at the 8 pixel pitch, capped at the window's rows.
function pp_talk_persona_reply_rows(_state) {
    var _rows = [];
    if (!is_array(_state.live_reply)) return _rows;
    for (var i = 0; i < array_length(_state.live_reply); i++) {
        array_push(_rows, "* " + string(_state.live_reply[i]));
    }
    return _rows;
}

/// The persona name plate's own geometry, so the capture tool reads the same numbers the game draws.
function pp_talk_persona_plate_x() { return 48; }
function pp_talk_persona_plate_y() { return 56; }

/// Draw the message window, the name plate and either the box or the reply.
function pp_talk_persona_draw(_state) {
    if (!is_struct(_state)) return;

    // The field is a flat ink card; the scenes that wrap this box bring their own map.
    draw_set_colour(pp_role_colour("ink"));
    draw_rectangle(0, 0, PP_FRAME_W, PP_FRAME_H, false);

    // The same message window the battle reply uses (x 0 to 256, y 0 to 48).
    draw_set_colour(pp_role_colour("paper"));
    draw_rectangle(pp_battle_text_box_x1(), pp_battle_text_box_y1(),
                   pp_battle_text_box_x2() - 1, pp_battle_text_box_y2() - 1, false);
    draw_set_colour(pp_role_colour("dim"));
    draw_rectangle(pp_battle_text_box_x1(), pp_battle_text_box_y1(),
                   pp_battle_text_box_x2() - 1, pp_battle_text_box_y2() - 1, true);

    if (_state.live_stage != "") {
        pp_talk_live_draw(_state);
    } else if (array_length(_state.live_reply) > 0) {
        var _rows = pp_talk_persona_reply_rows(_state);
        for (var i = 0; i < array_length(_rows); i++) {
            pp_font_draw(_rows[i], pp_talk_text_x(), pp_talk_text_y() + i * pp_talk_line_pitch(), 1);
        }
    }

    // The name plate, below the window like the battle's enemy label, in the sheet's ink on the dark field.
    pp_font_draw_centre(_state.persona_name, pp_talk_persona_plate_x(), pp_talk_persona_plate_y(), 1);
}

/// Step the box, and hand the map back on a confirm over the reply or an Esc during entry.
function pp_talk_persona_step(_state) {
    if (!is_struct(_state)) return;

    // The reply is on screen: a confirm returns to the overworld (a chat's only exit is the player's own press).
    if (_state.live_stage == "" && array_length(_state.live_reply) > 0) {
        _state.reply_steps += 1;
        if (pp_pressed("confirm")) _state.finished = true;
        return;
    }

    pp_talk_live_step(_state);

    if (_state.live_stage == "" && array_length(_state.live_reply) > 0) _state.reply_steps = 0;
}

/// The app mode the overworld hands to when a persona trigger fires.
function pp_talk_persona_mode() {
    return {
        enter: function(_params) {
            var _id = "";
            if (is_struct(_params) && variable_struct_exists(_params, "persona")) _id = string(_params.persona);
            var _state = pp_talk_persona_new(_id);
            global.pp.talk_persona = _state;
            pp_talk_persona_open(_state);
        },
        step: function(_params) {
            var _state = global.pp.talk_persona;
            if (is_undefined(_state)) return;
            pp_talk_persona_step(_state);
            if (_state.finished) {
                global.pp.talk_persona = undefined;
                pp_app_request(PPMode.overworld, { resumed: true });
            }
        },
        draw: function(_params) {
            var _state = global.pp.talk_persona;
            if (is_undefined(_state)) return;
            pp_talk_persona_draw(_state);
        }
    };
}
