# Spec 04: overworld rails and triggers

Status: spec, 2026-10-19, rules 1 to 5 rewritten 2026-10-26. No code yet. Numbers are DECISIONS.

Goal: the player walks a map in eight directions and presses confirm on things; on some screens the game walks for
them while the story plays, and hands control back with no button press.

Three data pieces per map
1. Tile map: 16x16 tiles, 16 by 15 tiles visible, larger maps scroll (spec 03).
2. Collision grid: one byte per tile, 0 walkable, 1 blocked, 2 story blocked. Separate from tile art so walls can change
   without redrawing tiles.
3. Trigger list: `{x, y, kind, id, once, condition}` with kinds `scene`, `battle`, `map`, `say`, `flag`, `marker`.
   A map also carries name, spawn points and music id.

Rails: a list of `walk(direction, tiles)`, `wait(steps)`, `say(dialogue_id)`, `face(direction)`.
- Rail walk is `PP_WALK_STEPS_RAIL`, 8 steps per tile. A scripted move is a TILE path: it snaps the hero to the nearest
  tile centre before it runs, then plays exactly as it did before the free walk existed, so a rail, a cutscene and the
  demo route are all unchanged by it.
- A rail may not cross a blocked tile: the data checker rejects that rail, so a rail cannot soft lock.
- Confirm skips to the next `say` but never skips a walk. Only the rail's own end or a scene request cancels it.

Rules
1. Free movement is EIGHT directions, diagonals included, and the hero walks in pixels rather than in tiles. The walk
   speed is `PP_WALK_SPEED`, 120 pixels a second, which is 7.5 tiles a second at 16 pixels a tile, and it is the same in
   every direction: a diagonal is scaled by 1/sqrt(2) on each axis, so holding down and right covers the ground that
   holding right covers. Keyboard, d-pad and the left stick all walk, and the stick is read only in `pp_input` (spec 02
   rule 1). Shift or the right shoulder runs at `PP_RUN_SPEED`, 200 pixels a second; both were the only inputs no other
   action claimed. Order of Nayil, 2026-10-26: "The grid movement is too rigid. This ain't pokemon. Most games nowadays
   let you hold down and right to go diagonally."
2. Collision is a 10x6 hitbox at the FEET (`PP_HERO_FEET_W` by `PP_HERO_FEET_H`), against the map's collision grid and
   against actors, and it is resolved ONE AXIS AT A TIME: the X move is tried, then the Y move against the X result. That
   is what makes a wall stop only the axis that faces it, so a diagonal push slides along a wall instead of sticking on
   it. A push that a corner blocks by `PP_CORNER_NUDGE` (3) pixels or less is walked round the corner instead of into it,
   and a long wall offers no such offset, so a straight wall is still a dead stop.
3. Facing is four directions for the sheet, and the component that CHANGED on the step wins: a diagonal held from the
   start faces its horizontal half and keeps that face while both keys stay down, adding the other axis turns him once,
   and letting one axis go leaves him facing the one still held. The two frame walk cycle is timed to the distance
   walked, one frame every `PP_WALK_FRAME_PX` (8) pixels, never to the number of steps a key has been held: a walker
   pushed into a wall stands still, and a runner animates at the speed he is actually covering.
4. Confirm reaches what is IN FRONT OF THE FEET, not the next tile: a reach box of `PP_REACH` (14) pixels ahead of the
   feet box, tested against each actor's own feet box and against the trigger tiles it covers. The door the player aims
   at is chosen before the one underfoot, and a trigger under the feet is the last chance. Confirm is still a PRESS and
   never a hold, so a key held down cannot open a box every step.
5. A touch trigger fires when the feet ENTER its rectangle, once per entry, held walk or not. The world remembers the
   tile the feet were on, so standing still on a marker is not an entry on every step. The 20 step grace after any scene
   or battle is unchanged, and a marker is still gone for 30 steps after it is touched.
6. The camera is PINNED to the walker while he walks: its position is his own pixel less the constant half tile, so the
   figure holds one screen pixel and the world slides under him. That is the only way the view has no jitter on a
   diagonal: a camera that eases toward him (`PP_CAMERA_SMOOTH` a step) lags him by (1 - smooth) / smooth of his speed,
   and while it lags, his pixel and the camera's cross their own rounding boundaries on different steps, which bobs him
   one pixel against a grid that is standing still, two frames in three. While he STANDS the camera eases the rest of
   the way and snaps the last pixel, so a map load or a scene handback slides into place. The map, the figures and the
   markers are all drawn from the same floored camera. A camera pan, a fade and a shake are unchanged.
7. A trigger marked once is recorded in the route ledger (spec 10), so doors stay open across a save and load.
8. Story blocked tiles open when a flag is set: that is the ship's locked door and the data center gate.
9. The free walk never moves the hero while a text box is open or a rail is running: a scripted move owns him until it
   lands, and the walker is free again the step after.

Encounters: markers only, drawn as a small silhouette, never random. Touching one starts a battle; the marker is gone
for 30 steps then respawns, so a corner cannot trap the player. An area may cap marker density.

Map changes: 12 step fade each way, spawn at the named spawn point unless the entry says `keep_position`.

PP content: Map 1 Soton High Street and Harbor is the free walk map; the Faux Wessex Lane Halls intro is one rail with
three `say` beats; Map 2 the small ship is a corridor with story blocked doors; Map 3 the AI data center uses trigger
chains for its hack puzzles; the London prison corridor is the case that needs the 20 step lock.

Acceptance (Nayil)
1. Holding down and right walks him diagonally at the same speed as holding right, into every corner of a room, with no
   stop and no jitter; a wall is slid along rather than bumped into.
2. Walking into a corner within three pixels slides him round it; walking into a long wall does nothing, with no
   animation past one push frame and no repeated bump.
3. The intro rail walks on its own, confirm advances text, control returns unprompted.
4. An encounter marker does not immediately re-fight after the battle.
5. Deleting a dialogue id in data makes the checker name the missing id before the game runs.

Out of scope: NPC pathfinding, parallax, a map editor GUI.

## Change log

- 2026-10-26, card PP-FREE-MOVE, on Nayil's order of the same date: "The grid movement is too rigid. This ain't pokemon.
  Most games nowadays let you hold down and right to go diagonally." Rules 1 to 6 and the rail line above were rewritten
  from a tile walk to free movement in pixels: eight directions from keys, d-pad and left stick; a 10x6 feet hitbox
  resolved per axis with a 3 pixel corner nudge; a four direction face decided by the component that changed and a two
  frame cycle timed to distance walked; a confirm that reaches in front of the feet, read from the middle of the reach
  box and not from its far corner; touch triggers that fire once per entry; and a camera pinned to his pixel while he
  walks, because an eased camera bobs him a pixel against the map on every diagonal. `PP_WALK_STEPS_FREE` is gone: the
  free walk is pixels now. The rail walk stays 8 steps per tile and the trigger grace stays 20 steps, and a scripted
  move snaps the hero to the nearest tile centre first so every rail, cutscene and demo beat still plays as it did.
  `knowledge/SPEC-DELTAS.md` carries the record as D2.
- 2026-10-26, card t_771e78ef, on Nayil's order of the same date: "the movement system on the map was fucked, had to
  press direction keys a billion times to move. Fix." Rules 1, 2 and 7 and the rail line above were rewritten from
  "one tile per press" to "hold to walk, tap for one tile", free walk became 8 steps per tile (was 12), and the left
  stick was added as a walk direction through `pp_input`. Rail walk stays 8 steps per tile and the trigger grace stays
  20 steps: neither is touched by that order.
