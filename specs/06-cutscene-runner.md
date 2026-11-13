# Spec 06: cutscene runner

Status: spec, 2026-10-19. No code yet. Numbers are DECISIONS.

Goal: a scene is a list of plain commands in a data file. Characters walk, text opens, the screen fades, music changes.
The player presses confirm to advance text and otherwise watches. At the end, control returns with no press.

Commands
| Command | Arguments | Effect |
| --- | --- | --- |
| say | dialogue id | opens the box, waits for it to close |
| move | actor, direction, tiles | walks an actor at rail speed |
| face | actor, direction | instant turn |
| wait | steps | waits |
| fade | out or in, steps | fades the screen |
| music | id or stop | starts, crossfades or stops |
| sfx | id | plays once |
| camera | x,y or an actor | 24 step move, or back to the walker |
| shake | steps, strength | integer pixel shake |
| flash | steps, role | floods the frame in one declared role for 2 frames, 8 at most; costs no steps (2026-10-24) |
| spawn / destroy | actor, tile x, tile y / actor | story actors |
| battle | enemy id | starts a battle, waits for its result |
| talk | npc, plate, line (optional) | the player types a line in the box, or the command carries one, the character answers, confirm closes the answer (2026-11-01, 2026-11-13) |
| setflag | name, value | writes a route ledger fact |
| branch | flag, scene id | jumps if true |
| end | none | returns control |

Rules
1. Commands run one at a time; anything that takes time blocks the list.
2. All commands are data: Nayil reorders a scene or adds a line without code.
3. `branch` is the only control flow. No loops, because an authoring loop can hang the game.
4. The checker proves every dialogue, music, sfx, actor, scene and enemy id exists, and that every `move` lands on a
   walkable tile.
5. Confirm advances a `say` and is ignored by every other command, so nobody skips a camera move into a black frame.
   The one exception is `talk`, which is a box: confirm sends the typed line and then closes the answer (rule 10).
6. A scene that ends with a battle unresolved is a checker error.
7. Debug build: F2 steps one command and prints the index.
8. A `flash` spends no steps of its own. It is a palette change over steps the scene already spends, so it advances in
   the step it runs and the world counts its frames down. A flash priced as a wait would move every shot duration after
   it, and on the drive it would move the cue's cut grid with them.
9. A scene row may carry `"skippable": true`, and a skippable scene ends where it stands when the player holds cancel
   for PP_SCENE_SKIP_HOLD steps (30, half a second). It ends through the same pp_scene_end a written `end` uses, so the
   demo route hands on to the row's `next` exactly as it would have. Only the drive asks today, and a scene with a
   choice never sets it, because a skipped choice would answer for the player. See spec 20, decision 3.
10. A scene's end is where the demo route moves: whichever way the runner finishes (its own `end`, a runout, the
    command cap), the overworld drops it in one place and that place tells the route (pp_route_scene_finished). See
    spec 20, decision 1.
11. Amendment, 2026-10-26 (card t_ee178652, spec 21): no scene command opens the live TALK entry box. A scene blocks
    on a dialogue it owns and a box that waits on a player's typing has no bound, so a scene that needs the player to
    say something uses `branch` on a flag an earlier `say` set, exactly as rule 3 already requires. The box is entered
    from the battle menu only, where the fight's own turn loop bounds the wait. Superseded for the one route beat by
    rule 12.
12. Amendment, 2026-11-01 (card t_1163ca72): `talk` is a scene command, and it is the one place rule 11's objection
    does not hold. The wait it names had two halves and both are now closed. There is no network half: the answer is the
    character's recorded turn out of `data\meta_bake.json` (pp_talk_scene_submit reads pp_talk_npc_rows and opens no
    socket), so a scene can never sit on a call that does not come back. And there is no dead half: the typing stage
    takes cancel, which puts the box down and lets the scene walk on to its next command, so an exchange nobody wants
    to have cannot strand a scene. The line the player types is kept on the runner's own state (`scene_said`) and is
    never sent anywhere; the game's log carries its length and the verdict, never the words. It is used on the quay
    dock office beat, S5, where the clerk asks the player's name and the box answers in his plate; the drive never
    carries one, because the drive's cut grid cannot wait on a keyboard (spec 20, decision 1).
13. Amendment, 2026-11-13 (card t_21951674): a `talk` may carry its own `line`, the player's words for a beat that
    already has them, and then the box asks at once and one confirm closes the answer. Reason: the gate beat needs the
    model's verdict on a line a judge can see, and a recorded take cannot type. It is the same command, the same box and
    the same send (`pp_talk_scene_ask` is `pp_talk_scene_submit` underneath); `line` only skips the typing stage, so
    neither half of rule 12 reopens: the wait is bounded by the box's own scene clock (420 steps, spec 21 section 12),
    cancel is not needed because there is no typing stage to cancel, and a bridge that never answers lands on the
    visible fallback rows. The line is on screen while it is being judged, so the exchange reads as line, answer,
    verdict. It is used on the quay gate beat, S4, with Morgan's card (data/talk_personas.json, id `morgan`).

Numbers: camera move 24 steps, linear, floored; fade 12 steps when the argument is omitted; music crossfade 30 steps;
shake 1 or 2 pixels changing every 2 steps, maximum 60 steps; a scene over 256 commands is a checker warning, because
that scene should be two scenes. Flash: 2 frames when the argument is omitted (the title's own storm clock), 8 at most,
and the role defaults to `paper`, which every set in `data\room_palettes.json` declares. A role the scene's own room
set does not declare is a checker error: a flash may only spend a colour the screen already draws with (spec 13).

PP content: the intro uses spawn, move, say, camera and music; Prometheus interrupting the Percy fight uses battle then
say then branch; the prison scene picks the Prometheus or Atlas variant with one branch on the route flag; the Kronos
ending uses spawn, camera, say and fade; the Ouranos post credits scene is a separate scene entered from credits.

Acceptance (Nayil)
1. The intro plays in order, cannot be mashed past, and returns control at the end.
2. A wrong dialogue id in a scene is named by the checker with its command line number.
3. A camera pan stops exactly on target with no overshoot.
4. Both branch variants play when the flag is flipped.
5. F2 in a debug build steps one command per press, printing the index.
6. The dock office beat takes a typed line, answers it in the box with the character's verdict, and the scene walks on
   to the boarding fade whether the player sent a line or cancelled it.

Out of scope: parallel tracks, actor physics, a timeline editor.
