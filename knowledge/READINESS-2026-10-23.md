# Readiness, 2026-10-23: whether the slice can be recorded today

Written by audit from commands run on 2026 10 22 between 19:22 and 19:47 Pacific, on the working tree at
`<repo>`. Nothing in this page comes from a card that claims
done; every row is a command this run executed and the exit code it returned. Read the four gates, then one block
per step, then the recording, then the single next thing.

## The tree that was measured

    data/scenes/all.json    7f612b924346349429915bf4d8bb1f85d6db6223c5623feae36e3d47dd3fa9d3
    data/dialogue/all.json  b610e3f0565ca6c8b17a462661b209179781548dc410c1a87079c4a2c7061afd
    data/maps/all.json      2f12bdb70a30f55bb356cdfa10bcf81b6b82b3ae5426531776693d434702b60c
    data/slice.json         bb3c0d73fdeefc8eeba2781e636e50ad09f5a86326494d8b4c9562aae71ecbdf

The tree moved under this audit. R23 is running and wrote `game/scripts/pp_scene/pp_scene.gml` at 19:31, and
`tests/test_scene_runner.py` was written at 19:23. The full suite at 19:23 saw `ship_boarding[1] say` carrying an
unknown argument; the same test passed at 19:32 against the same data hashes above. Each row states its own time.

## The four gates

1. `python tools/check_data.py`, 19:22:43, **exit 0**, `check_data: all files pass`.
2. `python tools/check_cleanroom.py`, 19:22:56, **exit 0**, `341 files scanned for 26 names and 12 phrases, 35 GML
   modules, 0 awaiting review ... no study reference, no foreign name, no foreign phrase, every module reviewed`.
3. `python -m pytest tests -q`, 19:30:42, **exit 1**, `22 failed, 898 passed, 1 skipped, 19 warnings in 416.96s`.
4. `python tools/nes_audit_all.py`, 19:24:52, **exit 0**, `nes_audit_all: PASS 160 file(s), 24 failing, 0
   unmeasured`.

Gate 4 prints 24 FAIL rows and still exits 0, so it cannot stop a build on art. That is how the tool is built, not a
pass. Gate 3 is the only gate that goes red today.

Of the 22 failures, 12 name title art or its palette pins (`test_look` 2, `test_make_title_ui` 3,
`test_make_title_world` 1, `test_title_art_v2` 5, `test_title_bands` 1), 5 name the project graph, the datafiles
mirror or generated file currency (`test_project` 4, `test_build_inputs` 1), 3 are `test_nes_check` font and window
pins, 1 is `test_scene_palette_set`, and 1 was the scene runner mid edit described above.

## S1 TITLE: attract, PRESS START, NEW GAME and CONTINUE

command: `python -m pytest tests/test_title_bands.py tests/test_make_title_world.py -q`
exit: **1**, `2 failed, 28 passed in 3.37s` (19:31:43)
artifact: `output/title_run_1.png` exists, 36897 bytes, written 19:01; the title scene data is `data/title.json`,
1674 bytes, written 17:29.
verdict: **PARTIAL**
gap: two pins are red. `test_title_bands` measures 8 colours where the title may spend 7 (`#004058`, `#005800`,
`#0058f8`, `#007800`, `#0078f8`, `#7c7c7c` and two more). `test_make_title_world` finds the flash strip drawing
`[0, 15, 32, 40]` where the lift should give `[0, 16, 33, 34, 48]`. The rest of `test_make_title_ui` and
`test_title_art_v2` are also red, so the title art is mid flight under R37's follow up. What is not in question is
that the title runs: the recorded run's own trace saw the marker `PP title: intro started` at 11.533 s.
closing card: R25 TITLE PATH `t_136b5d08` (todo) for NEW GAME and CONTINUE, plus the title art debt above, which has
no card of its own on the board.

## S2 CRAWL

command: `python -m pytest tests/test_intro.py tests/test_text_reveal.py -q`
exit: **0**, `17 passed, 3 warnings in 3.81s` (19:32:05)
artifact: `output/intro_1.png` (16380 bytes, 07:55), `output/intro_4.png` (14667 bytes, 07:56),
`output/crawl_mid.png` (5527 bytes, 07:57), all present; text source `data/intro_text.json`.
verdict: **PROVEN**
gap: none on the crawl itself. It reaches the screen from the title in the recorded run (marker at 11.533 s) and the
text reveal pins hold. It is proven as a rendered, reachable beat, not as a beat with a skip rule; START skipping
after a beat finishes is Nayil's manual check 3 and is unverified from here.

## S3 DRIVE

command: `python -m pytest tests/test_drive_v2.py -q`
exit: **0**, `8 passed in 1.22s` (19:32:17)
artifact: **none produced by the route.** The only drive work on disk is `knowledge/DRIVE-SHOT-LIST.md` (card
`t_9b2e63d2`, done) and the drive music builder.
verdict: **MISSING**
gap: the passing command above measures `tools/drive_v2.py`, a music cue builder whose own docstring says so on line
1. It is not the drive scene, and using it as proof of S3 would be a false pass. `data/scenes/all.json` holds 5
scenes and none of them is a drive scene; `game/scripts/` has no drive module; `data/maps/all.json` holds ship maps
only. The gantry sign reading 55 and the no shot still for 20 seconds of Nayil's manual check 4 have nothing to
measure.
closing card: **R21 does not exist on the board.** A search of nayil ops for a title beginning `R21` returns no rows,
and the roadmap says it is created only after ARRIVAL MAP 2 `t_db2995d7` (todo) and SHIP DECK MAP `t_a3fa132a`
(todo) release `data/maps/all.json` and `data/scenes/all.json`. Until then the step has no owner, and that is the
largest structural hole on this page.

## S4 ARRIVAL: Town Quay, the checkpoint, three replies

command: `python -m pytest "tests/test_dialogue_v2.py::test_the_arrival_rows_are_landed" -q`
exit: **0**, `1 passed in 0.46s` (19:34:49)
artifact: `data/dialogue/all.json`, 6997 bytes, written 18:51, carrying `quay_gate_truth`, `quay_gate_bluff`,
`quay_gate_authority` and seven `say_door_*` entries, each with real `pages`.
verdict: **PARTIAL**
gap: the text landed, the scene did not. None of the three gate rows carries a `choices` list (each has `id`, `pages`
and `speaker` only), so the three option choice Nayil checks in manual item 5 has no data form. `data/maps/all.json`
holds 2 maps, `ship_small` and `ship_cabin`, so there is no quay to arrive at, and no scene names the gate rows.
closing card: ARRIVAL MAP 2 `t_db2995d7` (todo, job-discovery) for the map and scene rows, and R31 TEST DIALOGUE V2
`t_45ef4217` (todo) for the choice wiring pin.

## S5 BOARDING

command: `python -m pytest tests/test_scene_runner.py -q`
exit: **0**, `9 passed in 0.81s` (19:32:47)
artifact: `data/scenes/all.json`, 1977 bytes, written 05:42, whose `ship_boarding` row carries six commands in order
`music PP-05`, `say ship_rail_note`, `move hero up 3`, `wait 20`, `setflag ship_deck_seen`, `end`, on map
`ship_small`.
verdict: **PARTIAL**
gap: the boarding pass and the dock office do not exist. The scene is the rail note on deck, the flag list in
`data/flags.json` holds 9 names and none of them is a boarding pass, and no scene carries a `save` command. The
runner now accepts the row, but at 19:23 the same file was red on `ship_boarding[1] say` carrying an unknown
argument, so this row is a snapshot of a file under active edit by R23.
closing card: SHIP DECK MAP `t_a3fa132a` (todo) for the gangway and corridor, and R24 SLICE ROUTE `t_e063f248`
(todo) to put the boarding beat in the route.

## S6 FIRST FIGHT

command: `python -m pytest tests/test_first_fight.py -q`
exit: **0**, `26 passed in 7.06s` (19:33:08)
artifact: `data/encounters/all.json` carrying `tutorial_sailors` (deck watch, one navy sailor, intro dialogue
`battle_intro_sailors`, 3 authored turns, 90 s, beat 28), plus `data/enemies/all.json` and
`data/characters/party.json` that the test reads.
verdict: **PARTIAL**
gap: the fight is provable from data and is not reachable from any scene. The only `battle` command in the 5
committed scenes is in `percy_lore_stop`, which fights `percy`; no committed scene names `tutorial_sailors`. The one
fight ONE FIGHT cannot lose is proven as a calculation (damage, ceiling of 5 per hit, hero hp with margin) and not
as a step of the route.
closing card: R30 TALK BAKED `t_8cd9c10a` (todo, waits on R22 and R29 `t_f943951a`) and R24 `t_e063f248` for the
route step.

## S7 SAVE: the ship's log

command: `python -m pytest tests/test_save.py tests/test_ledger.py -q`
exit: **0**, `49 passed in 1.98s` (19:33:21)
artifact: `game/scripts/pp_save/pp_save.gml`, present and passing its contract pins; it was 50886 bytes at 19:44 and
50107 when the pins ran at 19:33, because R26 is writing it now. **No save file exists anywhere in the tree**, so
there is no artifact produced by a save, only a contract that a save would hold.
verdict: **PARTIAL**
gap: R26 is running. Nothing in the route writes a save: the scene command list in `pp_scene.gml` has no `save` case,
and `test_save.py`'s own docstring says GameMaker is not installed on this PC, so the round trip has never executed.
closing card: R26 SAVE SLICE `t_7098c5fe` (running, builder) for autosave on entry and the log terminal, and R33
TEST SAVE GAMEOVER `t_00998131` (todo) for the round trip pin.

## S8 GAME OVER

command: `python -m pytest tests -q -k "gameover or game_over" --collect-only`
exit: **5**, `no tests collected (921 deselected) in 4.78s` (19:34:04)
artifact: **none.** `game_over` appears 0 times in `pp_battle_director.gml`, `pp_save.gml`, `pp_scene.gml` and
`pp_overworld.gml`. The battle director does model a `defeated` state and returns the string `"defeat"` (9 matches),
so the seed of the screen exists and the screen does not.
verdict: **MISSING**
gap: no test, no screen, no CONTINUE from a save after defeat. Nayil's manual items 8 and 9 both end here.
closing card: R27 GAME OVER `t_24eab5ff` (todo, builder), which is the only card that closes this row.

## The recording that exists today

artifact: `output/demo/run_001.mp4`, 4164230 bytes, written 18:13, 73.5 s, 768x720 h264 at 60 fps, with
`output/demo/run_001_verify.json` beside it.
verdict: **PARTIAL, and its own verifier says no.** `run_001_verify.json` records `"ok": false` and a `not_a_terminal`
FAIL on 5 of 7 sampled frames (`t=1.5`, `13.2`, `48.5`, `61.7`, `69.8`, each exact viewport score 0.0). A later
check, `_demo_check.log` in the repository root (1687 bytes, written 18:25), passes the same bytes on a looser
measure: `4 of 7 sampled frames are the game's own picture`. Two versions of the check disagree on one file, and
only 2 of 7 frames score as the game under the strict one.
What it covers: title (marker at 11.533 s), the crawl, and a walk to the right on the ship from 43.2 s to 65 s with
one confirm. What it does not cover: the drive, the arrival, the gate choice, the boarding pass, either fight, the
log save, or a game over.

## Can this be recorded today

No. One of the eight steps is PROVEN (the crawl), five of the eight are PARTIAL on text or contract without a route
step, and two are MISSING outright (the drive and the game over). The sixth PARTIAL verdict below the steps belongs
to the recording, which is not a step. `data/slice.json` is still the 2026 10 19 ship slice (`map
ship_small`, `spawn start`, `scene ship_boarding`, `encounter tutorial_sailors`), so no step of the six the roadmap
names is ordered anywhere the game reads.

## The single next thing to fix

**R24 SLICE ROUTE, `t_e063f248` (builder, todo).** Everything on this page that is PARTIAL is blocked on the same
thing: a route in `data/slice.json` that names the six steps in order, so that a scene, a fight, a save and a game
over have somewhere to be reached from. It is gated by R23 SCENE RUNNER HARDEN `t_a98183d0`, which is running and
wrote `pp_scene.gml` at 19:31, so R24 can start the moment R23 lands. The 22 test failures are not the next fix:
12 of them are title art pins that no rule on this page depends on, and the title renders and runs today.

## Check for this page

Every row carries a command and the exit code this run returned, and every artifact path in a PROVEN or PARTIAL row
was opened by `stat` in this run. One row says PROVEN (the crawl) and each of the four artifacts it names exists:
`output/intro_1.png`, `output/intro_4.png`, `output/crawl_mid.png` and `data/intro_text.json`. Each MISSING row names
the card that would close it: the drive names R21, which is not on the board, and the game over names `t_24eab5ff`.
A second read finds 0 en dashes and 0 em dashes in this file; the only hyphens left are those inside command flags,
card ids, the lane name `job-discovery`, the cue id `PP-05` and file names, all of which must be quoted as they run.
The gate output quoted above is this run's own, captured at
`<agent-runtime>\kanban\boards\nayil-ops\workspaces\t_4d0c2ef5\gate\` as `1_check_data.out`,
`2_check_cleanroom.out`, `3_pytest.out` and `4_nes_audit.out`.
