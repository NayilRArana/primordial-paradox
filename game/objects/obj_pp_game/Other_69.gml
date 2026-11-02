/// obj_pp_game, Other 69: the HTTP Request asynchronous event (spec 21 sections 2 and 5, card t_ee178652).
///
/// The live TALK leg is the only network call this project makes, and this event is the only door its answer comes
/// through. Each handler matches the reported id against the request its own box started, so an answer to a question
/// nothing asked is thrown away rather than applied to a turn it does not belong to.
///
/// The event number is the IDE's Async - HTTP Request slot. The manual page names the event and its async_load keys
/// and does not print the number, so this is a fact only the IDE or a running build confirms, exactly as Other_72's
/// Save/Load number is. Three things bound the damage if the IDE's slot turns out to be a different number: the same
/// handlers are also on Other_62 (the older Async - HTTP slot, which some builds deliver http_request through), a
/// request that never reports times out at the data file's step budget and the fallback answers, and every handler is
/// id matched so a second delivery of one answer is a no op.
///
/// The scene chat is the third box (card t_330b12ce): the S5 office exchange asks the same bridge the same question,
/// so its answer arrives here too. Three independent ifs, not an else-if chain: the chain used to stop at the battle
/// and leave a scene's answer unread.
// Every member is tested with variable_struct_exists first: global.pp does not define battle, talk_persona or world at
// start, and reading a struct member that was never set throws in GML, so a battle TALK answer arriving before any
// persona chat would otherwise end the game (found by the independent review of 2026-11-01).
if (is_struct(global.pp)) {
    if (variable_struct_exists(global.pp, "battle") && is_struct(global.pp.battle)) {
        pp_talk_live_async(global.pp.battle);
    }
    if (variable_struct_exists(global.pp, "talk_persona") && is_struct(global.pp.talk_persona)) {
        pp_talk_persona_async(global.pp.talk_persona);
    }
    if (variable_struct_exists(global.pp, "world") && is_struct(global.pp.world) && is_struct(global.pp.world.scene)
        && variable_struct_exists(global.pp.world.scene, "talk")) {
        pp_talk_scene_async(global.pp.world.scene.talk);
    }
}
