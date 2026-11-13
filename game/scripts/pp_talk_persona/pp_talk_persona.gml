/// pp_talk_persona: the live TALK box opened outside a fight, answering as one of the three persona cards
/// (card t_0fda85b8, spec 21 section 11). The box is spec 21 sections 1 and 2's box (pp_talk_live), opened
/// with a persona id instead of a battle: a chat, no meter, no tries burned, effects none and end, and ESC
/// leaves without a turn. The reply draws in the same message window with the same `* ` marker and 8 pixel
/// pitch, and the persona's name plate is the card's `name` field, read from data/talk_personas.json.

/// The line the scene self test says when it walks into a scene chat (card t_1163ca72). Two words the sheet draws,
/// so a headless play of the office beat can be read in a log without a keyboard.
#macro PP_TALK_SCENE_SELFTEST_LINE "A NAME"

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
    // Two shapes reach this door and both are the bridge's own documented answer: `text` is a persona row's lines
    // (the shape pp_talk_persona_replay builds) and `reply` is what POST /talk answers with (tools/ai_bridge.py's
    // "The talk answer"). Reading only `text` refused every live persona answer, which fell back to the card's pool
    // and made a live persona chat indistinguishable from a dead bridge (found by card t_1163ca72 while wiring the
    // S5 office exchange, the only live chat in the game with a box that shows the verdict).
    if (variable_struct_exists(_doc, "reply") && is_array(_doc.reply)) {
        for (var r = 0; r < array_length(_doc.reply); r++) {
            array_push(_reply, string(_doc.reply[r]));
        }
    } else if (variable_struct_exists(_doc, "text") && is_array(_doc.text)) {
        for (var t = 0; t < array_length(_doc.text); t++) {
            array_push(_reply, string(_doc.text[t]));
        }
    }
    var _lines = [];
    var _cols = pp_talk_live_data().cols;
    for (var i = 0; i < array_length(_reply); i++) {
        if (array_length(_lines) >= 2) break;
        var _line = string_trim(_reply[i]);
        if (_line == "") continue;
        if (!pp_talk_line_drawable(_line)) continue;
        if (string_length(_line) > _cols) _line = pp_talk_cut(_line, _cols);
        array_push(_lines, _line);
    }
    if (array_length(_lines) == 0) return undefined;
    var _mood = "guarded";
    if (variable_struct_exists(_doc, "mood") && is_string(_doc.mood) && pp_talk_mood_legal(_doc.mood)) {
        _mood = _doc.mood;
    }
    var _verdict = "unmoved";
    if (variable_struct_exists(_doc, "verdict") && is_string(_doc.verdict)) _verdict = _doc.verdict;
    if (!pp_talk_live_verdict_legal(_verdict)) _verdict = "unmoved";
    return { reply: _lines, mood: _mood, verdict: _verdict };
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
    _state.live_verdict = _answer.verdict;
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
    pp_talk_turn_shown(_state, "persona", _state.persona);
    pp_audio_play("menu_select");
    return true;
}

// ---------------------------------------------------------------------------------------------------------------
// The async handler. Mirrors pp_talk_live_async against the persona state, so the two /talk and /hear sites in
// pp_talk_live stay the project's only network path.

function pp_talk_persona_async(_state) {
    if (!is_struct(_state)) return false;
    pp_talk_live_state_init(_state);
    // Card t_330b12ce: the id decides before the stage, because a /hear answer lands while the box is back in entry.
    var _id = ds_map_find_value(async_load, "id");
    if (is_undefined(_id) || !is_real(_state.live_handle) || _state.live_handle < 0) return false;
    if (_id != _state.live_handle) return false;
    if (_state.live_stage != "wait" && _state.live_pending != "hear") return false;
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
    var _pending = _state.live_pending;
    _state.live_pending = "";
    if (!_ok) {
        show_debug_message("PP: talk persona answer not ok, status " + string(_status) + ", http " + string(_http));
        if (_pending == "hear") {
            _state.live_note = pp_talk_live_data().voice_note;
            _state.live_note_steps = 120;
            show_debug_message("PP: talk persona hear answer not ok, the keyboard and the grid still work");
            return true;
        }
        pp_talk_persona_answer(_state, pp_talk_persona_replay(_state), "transport_error");
        return true;
    }
    var _doc = json_parse(_body);
    // Card t_330b12ce: a transcript belongs in the box, not in the answer cleaner. The persona box sent a /hear
    // request, so the same one-field reader the fight uses fills the line the player edits.
    if (_pending == "hear") return pp_talk_live_hear_answer(_state, _doc);
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

// ---------------------------------------------------------------------------------------------------------------
// The scene chat (card t_1163ca72): the S5 dock office exchange.
//
// What this is. A cutscene reaches a beat where the player speaks to somebody, the player types the line in the same
// box the fight talk uses, and the character answers inside the NES text box with the verdict on that line. Two answer
// paths, chosen by the box's own mode: replay reads the model's recorded turn for that character (data/meta_bake.json
// carries three turns per NPC at npc/nye/turn_1 to turn_3, written by tools/bake_meta.py from a real call, which
// pp_battle_text already loads into `pp_talk_bake_npc()`), and live sends the line to the same loopback bridge the
// fight talk uses (card t_330b12ce). The send is gated on pp_talk_live_is_live(), so the shipped default and every
// take open no socket, and a live one is the box's own request with the box's own clocks.
//
// Where the words come from is printed on every answer (`PP: talk scene answer ... source <label> via <path>`), so a
// claim that a model judged the line is a log line a reader can check rather than a suggestion of one.

/// True when this state is a scene chat. The same flag pp_talk_live reads, so the box's own step machine routes the
/// send and the cancel here instead of to the fight.
function pp_talk_scene_is(_state) {
    return pp_talk_live_is_scene(_state);
}

/// The plate a scene chat draws: the command's own `plate` when it names one, otherwise the npc id with its
/// underscores opened out, uppercased, because the box draws in caps and an id is not a name.
function pp_talk_scene_plate(_npc, _plate) {
    if (is_string(_plate) && _plate != "") return string_upper(_plate);
    return string_upper(string_replace_all(string(_npc), "_", " "));
}

/// Build the scene chat's state. It carries the live_* fields the box steps on plus the three the scene path owns:
/// the npc id, the recorded turns, and the lines the player has said (kept on the state and never sent anywhere).
function pp_talk_scene_new(_npc, _plate) {
    var _state = {
        scene_npc: string(_npc),
        scene_plate: pp_talk_scene_plate(_npc, _plate),
        scene_rows: [],
        scene_said: [],
        // Card t_330b12ce: the turns this exchange has already taken, in the bridge's history shape. The player's
        // lines are NOT in it (spec 19 section 3), only the reply and its verdict.
        scene_history: [],
        scene_turn: 0,
        talk_mercy: 0,
        talk_mood: "guarded",
        talk_options: [],
        talk_stage: "",
        turn: 1,
        reply_steps: 0,
        finished: false
    };
    pp_talk_live_state_init(_state);
    _state.live_hint = "";
    _state.scene_rows = pp_talk_npc_rows(_npc);
    return _state;
}

/// True when the bake carries a turn for this npc, which is the only condition a scene talk needs.
function pp_talk_scene_ready(_state) {
    return is_struct(_state) && is_array(_state.scene_rows) && array_length(_state.scene_rows) > 0;
}

/// Open the entry box on the map. Same stages and same keys as the fight talk; there are no tries in a conversation,
/// so the box never closes itself and only the player's own send moves it on.
function pp_talk_scene_open(_state) {
    if (!is_struct(_state)) return false;
    if (!pp_talk_scene_ready(_state)) {
        show_debug_message("PP: talk scene has no baked turn for " + string(_state.scene_npc)
            + ", the scene keeps its own dialogue");
        return false;
    }
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
    _state.live_hint = "";
    _state.reply_steps = 0;
    _state.finished = false;
    pp_input_text_begin();
    show_debug_message("PP: talk scene open, npc " + _state.scene_npc + ", plate " + _state.scene_plate
        + ", turns " + string(array_length(_state.scene_rows)));
    return true;
}

/// Cancel: put the box down and let the scene carry on. A conversation nobody wanted to have is not a stuck scene,
/// so the exchange still resolves into the beat that follows it.
function pp_talk_scene_abandon(_state) {
    show_debug_message("PP: talk scene abandoned at " + string(string_length(_state.live_text)) + " characters");
    pp_talk_live_close(_state);
    _state.live_hint = "";
    _state.finished = true;
    return true;
}

/// Send. The line is scrubbed by the same reader the fight talk uses, kept on the state, and answered either by the
/// local bridge (live mode, card t_330b12ce) or by the model's recorded turn for this character (replay, the shipped
/// default). The turn advances on every send in replay, so a second line gets turn 2, and a send past the last recorded
/// turn repeats the last one rather than answering with nothing.
function pp_talk_scene_submit(_state) {
    var _d = pp_talk_live_data();
    if (!pp_talk_scene_ready(_state)) return false;
    var _line = pp_talk_live_scrub(_state.live_text);
    if (_line == "") {
        pp_audio_play("menu_move");
        _state.live_note = _d.empty_note;
        _state.live_note_steps = 90;
        return false;
    }
    array_push(_state.scene_said, _line);
    _state.live_text = _line;
    _state.live_pending = "talk";
    _state.live_stage = "wait";
    _state.live_handle = -1;
    _state.live_steps = 0;
    _state.live_deferred = undefined;
    _state.live_deferred_steps = 0;
    _state.reply_steps = 0;
    _state.live_note = "";
    _state.live_note_steps = 0;
    pp_input_text_end();

    // Card t_330b12ce. The card asks the office exchange to answer what the player actually said, so in live mode the
    // line goes to the same local bridge the fight talk uses, on the same non blocking request. The address, the
    // timeout and the fallback are all the box's own, so a scene cannot grow a second network path or a second clock.
    // Replay is untouched: the bake's recorded turn answers and no socket is opened.
    show_debug_message("PP: talk scene send, npc " + _state.scene_npc + ", "
        + string(string_length(_line)) + " chars, mode " + pp_talk_live_mode());
    if (pp_talk_live_is_live()) {
        pp_talk_live_send_talk(_state);
        return true;
    }

    var _index = min(_state.scene_turn, array_length(_state.scene_rows) - 1);
    var _row = _state.scene_rows[_index];
    _state.scene_turn += 1;
    pp_talk_scene_answer(_state, {
        reply: _row.text,
        mood: _row.mood,
        effect: _row.effect,
        hint: _row.hint,
        source: "bake"
    }, "bake");
    return true;
}

/// The JSON body of one scene /talk request: the persona path's shape, because a character in a cutscene is a persona
/// with a place and a voice, not a fight with a meter. The player's earlier lines stay home (spec 19 section 3); the
/// history carries only the reply and the verdict.
function pp_talk_scene_request(_state) {
    var _history = [];
    if (is_array(_state.scene_history)) {
        var _start = max(0, array_length(_state.scene_history) - PP_TALK_LIVE_HISTORY_MAX);
        for (var i = _start; i < array_length(_state.scene_history); i++) {
            array_push(_history, _state.scene_history[i]);
        }
    }
    var _body = {
        persona: _state.scene_npc,
        player_text: _state.live_text,
        turn: max(1, array_length(_history) + 1),
        mood: "guarded"
    };
    _body.history = _history;
    return json_stringify(_body);
}

/// The one call scene code makes: a line in, a verdict text out. It is the same send the box uses, so a cutscene that
/// already has the player's words (a transcript, a chosen line, a self test) does not have to fake a key press.
///
///     var _talk = pp_talk_scene_new("nye", "NYE");
///     if (pp_talk_scene_open(_talk)) pp_talk_scene_ask(_talk, "MY NAME IS NAYIL");
///     ... then step it and read pp_talk_scene_rows(_talk)
///
/// A bridge answer lands through pp_talk_scene_async, so the caller must keep stepping the box; rows are empty until
/// the answer or the fallback has landed.
function pp_talk_scene_ask(_state, _line) {
    if (!is_struct(_state)) return false;
    if (is_string(_line)) _state.live_text = _line;
    _state.live_stage = "entry";
    return pp_talk_scene_submit(_state);
}

/// The rows the box draws for an answer, exactly as they appear, so a caller (or a capture, or a test) can read the
/// verdict text without re-deriving it: the reply rows, then the verdict row, then the hint when there is one.
function pp_talk_scene_rows(_state) {
    var _rows = [];
    if (!is_struct(_state)) return _rows;
    if (is_array(_state.live_reply)) {
        for (var i = 0; i < array_length(_state.live_reply); i++) {
            array_push(_rows, "* " + string(_state.live_reply[i]));
        }
    }
    if (_state.live_stage == "" && array_length(_state.live_reply) > 0) {
        array_push(_rows, pp_talk_scene_verdict_line(_state));
    }
    if (is_string(_state.live_hint) && _state.live_hint != "") array_push(_rows, _state.live_hint);
    return _rows;
}

/// One scene answer, checked against the bridge's documented shape. Undefined means the whole answer is refused and the
/// visible fallback answers instead. Two lines, 28 columns, the box's own numbers.
function pp_talk_scene_answer_clean(_doc) {
    if (!is_struct(_doc)) return undefined;
    var _reply = [];
    var _cols = pp_talk_live_data().cols;
    if (variable_struct_exists(_doc, "reply") && is_array(_doc.reply)) {
        for (var i = 0; i < array_length(_doc.reply); i++) {
            if (array_length(_reply) >= 2) break;
            var _line = string_trim(string(_doc.reply[i]));
            if (_line == "") continue;
            if (!pp_talk_line_drawable(_line)) continue;
            if (string_length(_line) > _cols) _line = pp_talk_cut(_line, _cols);
            array_push(_reply, _line);
        }
    } else if (variable_struct_exists(_doc, "text") && is_array(_doc.text)) {
        for (var t = 0; t < array_length(_doc.text); t++) {
            if (array_length(_reply) >= 2) break;
            var _text_line = string_trim(string(_doc.text[t]));
            if (_text_line == "") continue;
            if (!pp_talk_line_drawable(_text_line)) continue;
            if (string_length(_text_line) > _cols) _text_line = pp_talk_cut(_text_line, _cols);
            array_push(_reply, _text_line);
        }
    }
    if (array_length(_reply) == 0) return undefined;
    var _verdict = "unmoved";
    if (variable_struct_exists(_doc, "verdict") && is_string(_doc.verdict)) {
        _verdict = pp_talk_scene_verdict_word(_doc.verdict);
    } else if (variable_struct_exists(_doc, "effect") && is_string(_doc.effect)) {
        _verdict = pp_talk_live_effect_verdict(_doc.effect);
    }
    var _mood = "guarded";
    if (variable_struct_exists(_doc, "mood") && is_string(_doc.mood) && pp_talk_mood_legal(_doc.mood)) {
        _mood = _doc.mood;
    }
    var _hint = "";
    if (variable_struct_exists(_doc, "hint") && is_string(_doc.hint) && _doc.hint != "") {
        _hint = pp_talk_cut(pp_talk_live_scrub(_doc.hint), _cols);
    }
    var _source = "unknown";
    if (variable_struct_exists(_doc, "source") && is_string(_doc.source)) _source = _doc.source;
    return { reply: _reply, verdict: _verdict, mood: _mood, hint: _hint, source: _source };
}

/// What the box shows when nothing answered or the answer was refused: two drawable rows, the verdict row, and a note.
/// Visible on purpose. A silent fallback would let a dead bridge look like a character with nothing to say.
function pp_talk_scene_fallback() {
    var _d = pp_talk_live_data();
    return {
        reply: [string_upper(_d.fallback_line_1), string_upper(_d.fallback_line_2)],
        verdict: "unmoved",
        mood: "guarded",
        hint: "",
        source: "fallback"
    };
}

/// Apply one scene answer. No meter and no turn: the reply goes to the dialogue window and the box closes into the
/// answer, which the scene draws until the player confirms. Every failure path lands here with `_via` naming why, so a
/// take can hold the exchange to a line that says where its words came from.
function pp_talk_scene_answer(_state, _doc, _via) {
    if (!is_struct(_state)) return false;
    var _answer = pp_talk_scene_answer_clean(_doc);
    if (_via == "timeout" || _via == "transport_error" || _via == "send_failed" || _via == "refused") {
        show_debug_message("PP: talk scene answer did not arrive (" + string(_via) + "), the visible fallback answers");
        _answer = undefined;
    }
    if (is_undefined(_answer)) {
        _answer = pp_talk_scene_fallback();
        _via = "fallback";
    }
    if (!is_array(_state.scene_history)) _state.scene_history = [];
    if (array_length(_state.scene_history) >= PP_TALK_LIVE_HISTORY_MAX) array_delete(_state.scene_history, 0, 1);
    array_push(_state.scene_history, { player_text: "", reply: _answer.reply, verdict: _answer.verdict });

    _state.live_reply = _answer.reply;
    _state.live_mood = _answer.mood;
    _state.live_hint = _answer.hint;
    _state.live_verdict = _answer.verdict;
    _state.live_source = _answer.source;
    _state.live_stage = "";
    _state.live_steps = 0;
    _state.live_handle = -1;
    _state.live_pending = "";
    _state.live_deferred = undefined;
    _state.live_deferred_steps = 0;
    _state.reply_steps = 0;
    pp_input_text_end();
    // A note belongs to the answer it came with: a fallback's note must not sit under the next answer's rows.
    _state.live_note = "";
    _state.live_note_steps = 0;
    if (_via == "fallback") {
        var _d = pp_talk_live_data();
        _state.live_note = _d.fallback_note;
        _state.live_note_steps = 150;
    }
    show_debug_message("PP: talk scene answer, npc " + _state.scene_npc + ", verdict " + _state.live_verdict
        + ", source " + _state.live_source + " via " + string(_via)
        + ", rows " + string(array_length(_state.live_reply)));
    pp_talk_turn_shown(_state, "scene", _state.scene_npc);
    pp_audio_play("menu_select");
    return true;
}

/// The scene's door to the project's one async handler. A scene chat is the same box, so it is the same reader: the
/// id is matched against this state's own handle, and pp_talk_live_answer routes the answer back to
/// pp_talk_scene_answer. No second socket, no second body reader, no second timeout (card t_330b12ce).
function pp_talk_scene_async(_state) {
    return pp_talk_live_async(_state);
}

/// The verdict as a word, from either shape the field can hold. A scene send stores the verdict word (it runs the
/// row's effect through the map); the live box stores whatever the bridge answered, and pp_talk_live_state_init
/// seeds the field with the effect name "none". Both read right here, so the row never prints "NYE IS NONE."
function pp_talk_scene_verdict_word(_verdict) {
    var _v = "";
    if (is_string(_verdict)) _v = string_lower(_verdict);
    switch (_v) {
        case "persuaded": return "persuaded";
        case "angered":   return "angered";
        case "unmoved":   return "unmoved";
    }
    return pp_talk_live_effect_verdict(_v);
}

/// The verdict as the box draws it: the model's judgement of the player's line, in the character's own name, in the
/// one ink the window has. No new punctuation and no new word the sheet cannot carry.
function pp_talk_scene_verdict_line(_state) {
    return "* " + string(_state.scene_plate) + " IS "
        + string_upper(pp_talk_scene_verdict_word(_state.live_verdict)) + ".";
}

/// Draw the exchange in the dialogue box itself: the window, the character's plate on its top border, the reply on
/// the two rows under it, the verdict on the third row, and the model's hint on the window's bottom row. This is spec
/// 05's box, drawn with spec 05's numbers, so the office beat is the same text box every other line in the game uses.
function pp_talk_scene_draw(_state) {
    if (!is_struct(_state)) return;

    if (!pp_window_draw(PP_BOX_X, PP_BOX_Y, 30, 8, 1)) {
        draw_set_colour(pp_role_colour("paper"));
        draw_rectangle(PP_BOX_X, PP_BOX_Y, PP_BOX_X + PP_BOX_W - 1, PP_BOX_Y + PP_BOX_H - 1, false);
        draw_set_colour(pp_role_colour("ink"));
        draw_rectangle(PP_BOX_X, PP_BOX_Y, PP_BOX_X + PP_BOX_W - 1, PP_BOX_Y + PP_BOX_H - 1, true);
        draw_rectangle(PP_BOX_X + 1, PP_BOX_Y + 1, PP_BOX_X + PP_BOX_W - 2, PP_BOX_Y + PP_BOX_H - 2, true);
    }

    // The name plate, over the left of the top border, exactly where the dialogue box puts its own.
    draw_set_colour(pp_role_colour("paper"));
    draw_rectangle(PP_PLATE_X, PP_BOX_Y - 6, PP_PLATE_X + PP_PLATE_W, PP_BOX_Y + 6, false);
    draw_set_colour(pp_role_colour("ink"));
    pp_font_draw(_state.scene_plate, PP_PLATE_X + 4, PP_BOX_Y - 4, 1);

    if (_state.live_stage != "") {
        pp_talk_scene_draw_entry(_state);
        return;
    }

    if (array_length(_state.live_reply) > 0) {
        for (var i = 0; i < array_length(_state.live_reply); i++) {
            pp_font_draw("* " + string(_state.live_reply[i]), PP_TEXT_X, PP_TEXT_Y + i * PP_TEXT_LINE_H, 1);
        }
        var _verdict_y = PP_TEXT_Y + min(2, array_length(_state.live_reply)) * PP_TEXT_LINE_H;
        pp_font_draw(pp_talk_scene_verdict_line(_state), PP_TEXT_X, _verdict_y, 1);
    }

    // The model's hint, on the window's bottom row, in the row a baked NPC box already draws its hint on. A fallback
    // note takes that row instead, because a take that lost the bridge has to say so where the player is looking.
    var _foot = _state.live_hint;
    if (is_string(_state.live_note) && _state.live_note != "") _foot = _state.live_note;
    if (is_string(_foot) && _foot != "") {
        pp_font_draw_wrapped(_foot, PP_TEXT_X, PP_BOX_Y + PP_BOX_H - 22,
            pp_font_cols(PP_TEXT_RIGHT - PP_TEXT_X), 8, 1);
    }
    draw_set_halign(fa_left);
}

/// The typing rows. The prompt is the one prompt the project owns, the letter rows are the box's own two row window,
/// and the key hint sits where the reply's hint sits, so the box does not move between typing and reading. The line is
/// drawn in the sheet's caps because the whole screen is caps: the field still keeps exactly what the player typed.
function pp_talk_scene_draw_entry(_state) {
    var _d = pp_talk_live_data();
    if (_state.live_stage == "listen") {
        pp_font_draw("* " + _d.hint_voice, PP_TEXT_X, PP_TEXT_Y, 1);
        pp_font_draw(_d.hint_wait, PP_TEXT_X, PP_BOX_Y + PP_BOX_H - 22, 1);
        return;
    }
    if (_state.live_stage == "wait") {
        // Card t_21951674: the line being judged stays on the screen while the character weighs it. A typed exchange
        // shows it in the entry stage and then loses it, so a take could show the reply and the verdict with no record
        // of what the player actually said. The said line owns the top two rows, the thinking dots the row under it.
        var _said = pp_talk_live_rows(string_upper(_state.live_text));
        var _said_n = min(2, array_length(_said));
        for (var w = 0; w < _said_n; w++) {
            pp_font_draw(_said[w], PP_TEXT_X, PP_TEXT_Y + w * PP_TEXT_LINE_H, 1);
        }
        pp_font_draw(pp_talk_live_dots(_state.live_steps), PP_TEXT_X,
            PP_TEXT_Y + _said_n * PP_TEXT_LINE_H, 1);
        pp_font_draw(_d.hint_wait, PP_TEXT_X, PP_BOX_Y + PP_BOX_H - 22, 1);
        return;
    }
    pp_font_draw("* " + PP_TALK_PROMPT, PP_TEXT_X, PP_TEXT_Y, 1);
    var _rows = pp_talk_live_rows(string_upper(_state.live_text));
    for (var i = 0; i < array_length(_rows); i++) {
        pp_font_draw(string_upper(_rows[i]), PP_TEXT_X, PP_TEXT_Y + (1 + i) * PP_TEXT_LINE_H, 1);
    }
    var _foot = _d.hint_keys;
    if (is_string(_state.live_note) && _state.live_note != "") _foot = _state.live_note;
    pp_font_draw(_foot, PP_TEXT_X, PP_BOX_Y + PP_BOX_H - 22, 1);
}

/// One step. The typing stages are pp_talk_live's; the reply is this file's, and a confirm over it ends the exchange.
function pp_talk_scene_step(_state) {
    if (!is_struct(_state)) return;
    if (_state.live_stage == "" && array_length(_state.live_reply) > 0) {
        _state.reply_steps += 1;
        if (pp_pressed("confirm")) _state.finished = true;
        return;
    }
    pp_talk_live_step(_state);
    if (_state.live_stage == "" && array_length(_state.live_reply) > 0) _state.reply_steps = 0;
}

/// The F1 scene self test's player: say the canned line, wait for the answer, then confirm it. Never a real key,
/// never a real player's words, so the self test can play the office beat to `end` with nobody at the keyboard.
function pp_talk_scene_autoplay(_state) {
    if (!is_struct(_state)) return;
    // Card t_330b12ce: only the entry stage sends. A send from the wait stage would start a second request over the
    // one in flight, and a step that does that every frame would flood the bridge.
    if (_state.live_stage == "entry") {
        _state.live_text = PP_TALK_SCENE_SELFTEST_LINE;
        pp_talk_scene_submit(_state);
        return;
    }
    if (_state.live_stage != "") return;
    _state.finished = true;
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
