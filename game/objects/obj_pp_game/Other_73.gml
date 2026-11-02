/// obj_pp_game, Other 73: the Audio Recording asynchronous event (spec 21 section 3, card t_ee178652).
///
/// Holding the voice key starts a recording, releasing it stops one, and the engine hands the samples back here as a
/// buffer in async_load. The buffer is kept on the box that asked for it and turned into a wav by pp_talk_live_wav when
/// that box is ready to send it, so this event does one thing: hand the bytes over and say how many.
///
/// Card t_330b12ce: the box that asked is not always the battle. The S5 office exchange records through the same key,
/// so the event asks every open box which one is listening (pp_talk_live_voice_event) instead of assuming the fight.
/// That is also the step the take was waiting for: a released recording sends its wav from here, because the samples
/// do not exist until this event fires.
///
/// The event number is the IDE's Async - Audio Recording slot and, like Other_72 and Other_69, the number is the one
/// fact here that only the IDE or a running build confirms. If it never fires, the voice leg reports "no recording"
/// and the keyboard and the letter grid still work, because the three input paths never depend on each other.
var _buffer = ds_map_find_value(async_load, "buffer_id");
pp_talk_live_voice_event(_buffer);
