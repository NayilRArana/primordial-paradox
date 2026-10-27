/// obj_pp_game, Other 62: the older Async - HTTP event, pointed at the same handler as Other_69.
///
/// Why two. http_request's answer arrives as "Async - HTTP Request" in the current GMS2 build and as "Async - HTTP"
/// in older ones, and the manual prints neither number. Rather than guess once and ship a signature feature that
/// silently times out, both slots call pp_talk_live_async, and pp_talk_live_async matches async_load's "id" against
/// the request the fight started: whichever event the engine fires, the answer is applied once, and if both fire the
/// second one finds the id already consumed and does nothing.
///
/// One line, because the reasoning lives in Other_69's header and in pp_talk_live.gml's, and a third copy of it here
/// would be a comment to keep in step with two others.
if (is_struct(global.pp) && is_struct(global.pp.battle)) {
    pp_talk_live_async(global.pp.battle);
}
