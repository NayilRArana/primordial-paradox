/// obj_pp_game, Other 62: the older Async - HTTP event, pointed at the same handlers as Other_69.
///
/// Why two. http_request's answer arrives as "Async - HTTP Request" in the current GMS2 build and as "Async - HTTP"
/// in older ones, and the manual prints neither number. Rather than guess once and ship a signature feature that
/// silently times out, both slots call the same handlers: each one matches async_load's "id" against the request its
/// own box started, so whichever event the engine fires, the answer is applied once, and if both fire the second one
/// finds the id already consumed and does nothing.
///
/// Three boxes, three calls, no else-if (card t_330b12ce). The old chain tested the battle first and skipped the rest,
/// so a persona chat or a scene chat whose answer landed here was never read. The boxes are independent ifs now: only
/// the one holding this request's id acts, and the other two return false on the id alone.
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
