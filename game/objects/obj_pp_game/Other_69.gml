/// obj_pp_game, Other 69: the HTTP Request asynchronous event (spec 21 sections 2 and 5, card t_ee178652).
///
/// The live TALK leg is the only network call this project makes, and this event is the only door its answer comes
/// through. pp_talk_live_async matches the reported id against the request this battle started, so an answer to a
/// question the fight did not ask is thrown away rather than applied to a turn it does not belong to.
///
/// The event number is the IDE's Async - HTTP Request slot. The manual page names the event and its async_load keys
/// and does not print the number, so this is a fact only the IDE or a running build confirms, exactly as Other_72's
/// Save/Load number is. Three things bound the damage if the IDE's slot turns out to be a different number: the same
/// handler is also on Other_62 (the older Async - HTTP slot, which some builds deliver http_request through), a
/// request that never reports simply times out at the data file's step budget and the fallback answers, and the
/// handler is id matched so a second delivery of one answer is a no op.
if (is_struct(global.pp) && is_struct(global.pp.battle)) {
    pp_talk_live_async(global.pp.battle);
}
