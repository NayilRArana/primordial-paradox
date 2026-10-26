# Spec 20: the demo route, and the player who walks it

Status: spec, 2026-10-26, card t_009836b9. Numbers are DECISIONS. It documents the route data file that cards R24,
R32 and DRIVE-MAP built, and rules the three questions that card found open. Read it beside data/slice.json, spec 06
(the cutscene runner) and spec 04 (triggers).

## What the route is

data/slice.json carries one row per step: an id, the kind of handoff the step names, the room, scene, map or encounter
the handoff goes to, and the id of the step it hands to next. The step kinds are title, crawl, scene, map, battle,
save and branch (pp_slice_kind). The route is read once and walked by id, never by array position.

The demo's chain, as the file stands:

| step | kind | target | next |
| --- | --- | --- | --- |
| title | title | rm_pp_title | crawl |
| crawl | crawl | data/intro_text.json | drive |
| drive | scene | drive_to_southampton on drive_m4_corridor | arrival |
| arrival | map | southampton_town_quay, spawn start (11,1) | gate |
| gate | scene | quay_gate_checkpoint, triggered on the quay at (8,10) | boarding |
| boarding | scene | ship_boarding on ship_small, start (2,7) | fight |
| fight | battle | tutorial_sailors, triggered on the deck at (4,7) | save |
| save | save | the deck_save trigger on ship_small | (the demo ends) |
| gameover | branch | back to title | (nothing) |

## The problem this spec answers

Until 2026-10-26 the only code that read a row's `next` was pp_slice_walk_step, and that is dead unless PP_SLICE is
set. Every real launch took the crawl's handoff to the drive and then stopped: the drive played its 10,680 steps,
pp_scene_end handed control back on drive_m4_corridor, and no row was advanced again. The corridor map had no triggers
and no portal, so a player who pressed NEW GAME ended on a road with nothing on it. The first fight was unreachable
without the harness. Measured in knowledge/FIRST-FIGHT-FINDING-2026-10-26.md.

## Decision 1: a route scene hands to its row's next when it ends, for a player as well as for the walk

Yes. The route is the contract for both halves of the demo, so the player follows it too, through the same handoff
door the walk uses (pp_slice_handoff), and the two halves keep separate cursors: the walk owns `slice_step`, a player's
run owns `route_step`.

Rules, in pp_app.gml and pp_scene.gml:

1. A scene that takes the screen tells the route its id (pp_scene_take_scene calls pp_route_scene_started). A scene
   the route names becomes the route's current step and is armed; a scene the route does not name (ship_log,
   navy_aftermath) arms nothing, so it cannot move a run it does not own.
2. When a finished runner is dropped in pp_overworld_step, the route is told which runner it was
   (pp_route_scene_finished). It hands to its row's `next` only if that row is still a scene row and it is the armed one.
   Because the drop point is the one place a finished scene is let go, every way a scene can end (its own `end`, a
   runout, the command cap) reaches the route.
3. A `branch` adopts its target through pp_scene_take_scene, so a branched scene cannot lose the route. The gate is the
   case that needs this: quay_gate_checkpoint ends as quay_gate_truth, and the route is on the gate row either way.
4. Reaching the fight: a row whose `next` is a battle step hands nothing to a mode. The route parks on the fight row,
   prints one line naming the map, and waits. The player starts the fight from the map through the map's own battle
   trigger, which is what prints `PP: battle start <encounter> on <map> x,y`. A fight the route names then hands to the
   step after it when it ends.
5. Every route move prints one `PP route:` line, so a run that took the route and a run that stopped at a row can be
   told apart from the log alone.

## Decision 2: the corridor is a set, not a room, and it also gets a way out

drive_m4_corridor stays where it is: the drive scene plays on it and it is a corridor by design, 160 by 24 tiles with
two spawns and a road row. It is not a map a player walks around, and after decision 1 a player is never left on it:
the drive ends and the route puts them on the quay.

That is a design guarantee, not a proof against every future bug, so the row also carries one exit: a `map` trigger on
its own start tile (0,8) into southampton_town_quay at spawn from_pier. If a run ever ends on the corridor with no scene
running, confirm takes the hero to the quay instead of trapping him. The trigger sits on the tile the scene starts on
and fires only when no scene runs, so it costs the drive nothing.

## Decision 3: the 178 s drive is the intended opening, and the player may skip it

The drive is not shortened. knowledge/DRIVE-SHOT-LIST.md times it at 10,680 steps (178.00 s), it is cut to twelve
durations and eleven cuts against cue PP-02, and card DRIVE-MAP drew the corridor for it. Cutting it to fit a capture
would spend that work.

What a demo opening may not do is hold a player for three minutes with twelve presses before the first control, so the
drive is the first scene that asks to be skippable, and a player ends it by holding cancel for thirty steps (half a
second). Rules:

1. A scene row may carry `"skippable": true`. Only the drive does today.
2. The runner reads the cancel action (X, Escape, Backspace in pp_input's table) and counts a hold. At thirty steps the
   scene ends through pp_scene_end, the same door a written `end` uses, so the route hands on exactly as it would have.
3. Cancel is not the key confirm advances a caption with, so a player reading the captions cannot skip the scene by
   advancing them, and a scene with a choice in it never sets the flag.
4. While the scene runs and the hold is still zero, the overworld draws one line, `hold X to skip`, in the frame's own
   top left. It disappears the moment the hold starts, so the count is visible as the words going away.
5. The skip is a player's key, not a debug key and not PP_SLICE, and tools/capture_first_fight.py uses it the same way
   a player would.
6. A scene's `move` turns the hero the way it walks him, because confirm reads the tile he faces: the boarding scene
   walks him right onto 3,7 and the fight's trigger is at 4,7, so a stale facing put the trigger behind him and the
   confirm pressed nothing. pp_world_start_move sets the facing from the step it takes, which the free walk already did
   for itself. Measured on the second capture: the route parked on the fight row, 94 z presses went by, and the battle
   never started; with the facing set, the first press after the boarding scene starts it.

## The capture's schedule, which follows from decision 3

tools/capture_first_fight.py walks this route with the game's own keys: Enter, Enter, Enter (title, NEW GAME, crawl),
a held cancel (the drive), nine downs and three lefts (the arrival walk the tool derives from the map's own collision
grid), confirm to the gate and its choice, confirm through the boarding scene, then confirm on the fight trigger, then
the fight's own 2.4 s cadence from card t_da94341c. The recording is about 145 s, which is what the route costs with
the drive skipped, and the check the tool prints is the same one it always printed: the battle box, the FIGHT cell, the
victory panel, the muted line, one `PP: battle start` line and no crash.

Measured on the run that passed: the drive's skip ends it at 22.5 s, the walk reaches the gate at 28.4 s, the gate's
three pages and its choice and reply take the route to the boarding scene, the boarding scene ends the hero on 3,7 at
44 s, the trigger press starts the fight at 44.6 s, the battle box is on screen at 58 s, the FIGHT cell is legible at
62 s, the victory panel reads at 134 s with 30 px of word and 53 px of press, and the route hands the fight to the save
step at 8 turns, 15 HP of navy_sailor, party untouched.

## What this spec does not decide

The TALK leg (a three TALK spare of the same fight) needs its own launch and its own output file, because the deck's
trigger is once per run. The corridor's art, the drive's cue and the beat sheet's timing are their own cards.
