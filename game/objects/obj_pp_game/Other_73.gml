/// obj_pp_game, Other 73: the Audio Recording asynchronous event (spec 21 section 3, card t_ee178652).
///
/// Holding the voice key starts a recording, releasing it stops one, and the engine hands the samples back here as a
/// buffer in async_load. The buffer is kept on the battle and turned into a wav by pp_talk_live_wav when the box is
/// ready to send it, so this event does one thing: hand the bytes over and say how many.
///
/// The event number is the IDE's Async - Audio Recording slot and, like Other_72 and Other_69, the number is the one
/// fact here that only the IDE or a running build confirms. If it never fires, the voice leg reports "no recording"
/// and the keyboard and the letter grid still work, because the three input paths never depend on each other.
var _buffer = ds_map_find_value(async_load, "buffer_id");
if (is_struct(global.pp) && is_struct(global.pp.battle)) {
    pp_talk_live_voice_recorded(global.pp.battle, _buffer);
}
