# READINESS 2026-10-22 (refresh): the slice table re-measured

Written by the audit profile for card `t_2362f051` (AUTO-AUDIT-REFRESH). Every number on this page came from a
command this run executed between 20:43 and 21:15 PDT on 2026-10-22, on this PC, against the working tree at
`<repo>`. Worker reports, card results and the earlier audit
pages were not accepted as evidence; where I did not measure, the line says unverified.

Read first, as the card ordered: `knowledge\ART-BIBLE.md` section 0 (the rules of that file: source tag per number,
a confidence word per row, and nothing in it is a claim about what this game must look like; palette first is the
convention the art pipeline is reviewed against) and section 1 (256 x 240, 8 x 8 tiles, 64 entries in the master
palette, 4 background palettes, 25 colours on screen at the ceiling).

The "before" table is `knowledge\HACKATHON-AUDIT-2026-10-22.md` section 1, measured 18:41 to 19:24. The earlier
readiness page `knowledge\READINESS-2026-10-23.md` (card R40) is untouched by this run; this is a new file.

## 0. The tree that was measured

    git HEAD                 2c490f8  R27 GAME-OVER  (git log --oneline -1)
    git status --porcelain   630 entries (dirty tree, R25 is writing)
    data/scenes/all.json     7f612b924346349429915bf4d8bb1f85d6db6223c5623feae36e3d47dd3fa9d3
    data/dialogue/all.json   b610e3f0565ca6c8b17a462661b209179781548dc410c1a87079c4a2c7061afd
    data/maps/all.json       2f12bdb70a30f55bb356cdfa10bcf81b6b82b3ae5426531776693d434702b60c
    data/slice.json          eb1767524b2c1a754cde79bb901337999457e7851366ca183d1cb0af78e37eef   (was bb3c0d73 at 19:22)

Three of the four data files are byte identical to the R40 page; `data\slice.json` changed because R24 landed at
20:39 (`git log`, commit 433d3b3 and its follow up 7a0502f).

## 1. Every measurement this run made, in one place

| Measurement | Command this run executed | Result |
| --- | --- | --- |
| Build from current source | `python tools/integration_build.py`, started 20:45:27, log `build\audit-refresh-build.log` | exit 0, `BUILD PASS: Igor compiled the project and launched the game` at 21:06 |
| Game actually ran | `build\last-igor.log`, 13109 bytes, last write 21:03:16 | live lines `PP audio: thunder_soft played, instance 400092`, `focus lost, music paused`, `focus back, music resumed` |
| Window closed, nothing left | `taskkill /PID 18804` (no force flag), then `tasklist` | Igor.exe and Runner.exe gone, no PrimordialParadox.exe listed |
| Rebuilt game data | `output\PrimordialParadox\PrimordialParadox.win` | 363212 bytes at 20:45:34 (was 311372); runner exe 7941704 bytes at 18:28:44, sha256 `5cbf3f4a9b1f4d8b6abd2dd3c451de7e2f561dac02d122176a28a5fa7b3e2375`, unchanged |
| Capture harness | `python tools\capture_title.py`, 21:07 | exit 0, `captured output\title_run_1.png 784x759`, `viewport [8, 31, 768, 720] score 1.000`, `the game closed on request (exit code 0)` |
| Fresh live title frame, colours | Pillow over the 768x720 crop | 38 distinct RGB, 29 of them not in the 55 entries of `data\nes_palette.json`; 10 of 61440 3x blocks not uniform |
| Committed title frame | Pillow over `output\nes_title_frame.png` | 256x240, 11 colours, 3813 bytes, written 22:01 on 2026-10-21 |
| Other committed frames | Pillow over `output\*.png` | ui_battle 5 colours, ui_dialogue 5, ui_menu 4, crawl_mid 4, crawl_end 4, chars_contact 22, bg_battle_preview 16, enemies_preview_3x 9 |
| Test suite on Pine | `pine_offload.py --shards 3 --name audit-refresh`, then per file lists for the shards whose transport died | 886 passed, 25 failed, 51 test files offloaded, 2 not offloaded (`tests\test_build_inputs.py`, `tests\test_test_inputs.py`) |
| Failures by file | the Pine result files under `pine\data\results\offload-audit-refresh*` | play_demo 8, capture_title 5, title_art_v2 3, project 3, look 1, scene_palette_set 1, make_title_world 1, make_title_ui 1, make_env_ship 1, intro 1 |
| Demo recorder, own check | `python tools\play_demo.py --check --video output\demo\run_001.mp4` | exit 0, `4 of 7 sampled frames are the game's own picture`, plus `FINDING 3 of 7 sampled frames are the game drawn off the 2C02 palette` with palette share 0.113 at t=48.5, 61.7, 69.8 |
| Demo recorder, strict check | `output\demo\run_001_verify.json`, written 18:14 | untouched by this run; still `ok: false` with exact viewport score 0.0 on 5 of 7 sampled frames |
| Slice route resolves | my `route_check.py` over `data\slice.json`, `data\scenes\all.json`, `data\maps\all.json`, `data\encounters\all.json`, `game\rooms` | title room FOUND, boarding scene FOUND, fight encounter FOUND, drive scene `drive_to_southampton` MISSING, arrival map `southampton_town_quay` MISSING, gate scene `quay_gate_checkpoint` MISSING |
| Scene commands | the same script over the 5 scene rows | no scene carries a `save` op; no scene op names `tutorial_sailors`; the only `battle` op is in `percy_lore_stop` |
| Save wiring | `grep -c '"save"' game\scripts\pp_scene\pp_scene.gml` | 0 |
| A save produced by a run | `find` for save files, maxdepth 4 | none; the only match is `build\save_slot_probe\pp_save_01.original.json`, 314 bytes, 19:36, a probe fixture |
| Game over proof | `grep -rln "gameover\|game_over" tests\` | no test file mentions it; the code is in `game\scripts\pp_battle_director\pp_battle_director.gml` lines 50 to 60 and 373 to 400 |
| Root documents | `ls` at the repository root | `README.md` present; 0 files matching `^licen` |

No key or login file was opened. `PINE_SANDBOX_API_KEY` and `KAGGLE_API_TOKEN` were read from the environment only
and never printed.

## 2. Scores before and after

Scale unchanged from the audit: 0 nothing, 1 spec only, 2 code or data but unproven in the game, 3 proven in the
running game with a capture or a test, 4 polished.

| # | Subsystem | Before | After | Evidence for the after value |
| --- | --- | --- | --- | --- |
| 1 | Title screen | 3 | 3 | fresh capture passes, `output\title_run_1.png` 62976 bytes; art pins still red: title_art_v2 3, make_title_ui 1, look 1, make_title_world 1; live crop carries 29 colours off the palette |
| 2 | Intro crawl | 3 | 3 | 114 of 115 `test_intro` tests pass on Pine; `test_the_star_generator_rewrites_the_committed_sprite` fails on a PNG byte compare; `output\crawl_mid.png` 4 colours |
| 3 | Drive cutscene | 1 | 1 | no drive module in `game\scripts`, no drive room (`ls game\rooms` = 3), and route step `drive` names scene `drive_to_southampton` which is absent from `data\scenes\all.json` |
| 4 | Overworld movement | 3 | 3 | `pp_overworld.gml` present; the recorded walk at t=36.75 scores palette share 0.9937, and at t=48.5 scores 0.1127 (`output\demo` check output) |
| 5 | Maps and doors | 2 | 2 | `data\maps\all.json` holds 2 maps; route step `arrival` names `southampton_town_quay`, absent |
| 6 | Dialogue and talk | 3 | 3 | `test_dialogue_v2` in the Pine run carried no FAILED line this time |
| 7 | Battle and the talk fight | 2 | 2 | `test_first_fight` rows pass from data; no scene op names `tutorial_sailors`, so no route step reaches it |
| 8 | Enemies | 2 | 2 | `data\enemies\all.json` and `output\enemies_preview_3x.png` 9 colours; no live encounter captured |
| 9 | Party and stats | 2 | 2 | `data\characters\party.json` only, no test named for a level up |
| 10 | Save and load | 2 | 2 | R26 is done and `test_save` and `test_ledger` pass, but no scene writes a save and no run produced a save file |
| 11 | Ledger | 2 | 2 | `test_ledger` passes on Pine; no capture |
| 12 | Audio bus and cues | 3 | 3 | live `PP audio: focus lost, music paused` and `thunder_soft played` lines from this build |
| 13 | Music per scene | 2 | 2 | R36 CUE-WIRING landed, so every named cue resolves to an asset or a pending row; only the title theme has a live capture |
| 14 | SFX | 3 | 3 | `test_sfx` passes on Pine; live footstep and text_blip lines in `build\last-igor.log` |
| 15 | UI windows and menus | 2 | 2 | the 3 `test_nes_check` failures the audit listed are gone from this run (`tests\test_nes_check.py` ran in the Pine shard that returned 179 passed 0 failed); the previews are still previews: `output\ui_battle_preview.png` 5 colours |
| 16 | Art pipeline | 2 | 2 | art failures fell from 11 to 8 (title_art_v2 3, make_title_ui 1, look 1, make_title_world 1, scene_palette_set 1, make_env_ship 1), so a rebuild still cannot reproduce its own output |
| 17 | Sprites per character | 2 | 2 | 12 `spr_*.png` files in `game\art` (count this run, the audit said 13) and `output\chars_contact.png` 22 colours; card `t_858c2908` still blocked |
| 18 | Backgrounds per scene | 3 | 3 | four strips present, `output\bg_battle_preview.png` 16 colours; card `t_59bfc884` still todo |
| 19 | Build and packaging | 3 | 3 | BUILD PASS at 21:06 with a fresh `.win` of 363212 bytes; still no zip and no install step |
| 20 | Tests and gates | 2 | 2 | 886 passed, 25 failed on Pine tonight against 833 passed, 33 failed in the audit; the split between Windows-only and real is still unwritten |
| 21 | Capture and demo tooling | 2 | 2 | `capture_title.py` green end to end tonight; `play_demo.py --check` exits 0 but 8 of its own 17 tests fail and 3 of 7 sampled frames are off the palette |
| 22 | Docs and repo hygiene | 1 | 2 | `README.md` now exists and states the slice is under construction; 0 licence files at the root |
| 23 | Slice route (new row) | n/a | 2 | `data\slice.json` now carries 9 ordered steps and `pp_app.gml` walks them, gated on the `PP_SLICE` environment variable; 3 of 5 named targets do not exist and no `pp_slice_run.log` was produced anywhere in the tree |

Row 22 is the only row that changed value. Sum before 50 over 22 rows, mean 2.27; sum after 51 over 22, mean 2.32.
The audit page printed "Mean over 22 rows: 2.2", which its own rows do not support (they sum to 50, 2.27); this
refresh uses the arithmetic rather than the printed line. With the new route row counted, the table is 53 over 23,
mean 2.30.

## 3. What moved, and the measurement behind each

1. Docs went 1 to 2: `README.md` exists at the root and names what runs and what does not (`README.md` line 9
   onward). No licence file exists at the root, so this row cannot reach 3 on the audit's own wording.
2. The route went from "not data" to data: `data\slice.json` carries 9 steps in order and `game\scripts\pp_app\pp_app.gml`
   reads them (`pp_slice_start`, `pp_slice_walk_step`). The walk is dead unless `PP_SLICE` is set, so a normal launch
   still opens on the first step only.
3. The failure count fell 33 to 25 and the pass count rose 833 to 886, on a tree that grew (51 test files tonight
   against 49 in the audit's three shards). Four Pine result files are transport errors (`Errno 10054`), retried and
   superseded; they are not verdicts and I did not count them.
4. The art pipeline improved but did not clear: 11 failures to 8, with a new one (`test_make_env_ship`) and
   `test_play_demo` at 8 against 9.
5. The 3 `test_nes_check` failures the audit listed (font sprite and two window pins) produced no FAILED line in
   tonight's shards, including a completed shard that carried `test_nes_check`.
6. The recorder's own check now exits 0 where the audit read a hard failure, but the strict check in
   `output\demo\run_001_verify.json` still reports `ok: false`, and the loose check passes on "4 of 7" frames while
   printing a palette finding for the other 3. Two checks on one file still disagree, and the video itself is still
   the 18:13 recording.
7. Game over moved from absent to code-only: `pp_battle_director.gml` carries the defeat fade, the card and the two
   choices, and `pp_app.gml` line 808 watches for `"defeat"`; no test names game over and no capture shows it, so it
   is not a 3 and the 22 row table has no row for it.
8. R26 SAVE-SLICE and R24 SLICE-ROUTE both closed at 20:06 and 20:39 (`kanban.db`, `tasks.completed_at`), and R27 at
   20:51. The save still does not reach the route: the scene command list has no `save` case.
9. The live title frame got worse on the audit's own colour measure: 28 distinct RGB and 8 non-uniform 3x blocks in
   the 19:01 file, 38 distinct and 10 in tonight's 21:07 file, with 29 colours off the 55-entry palette
   (`data\nes_palette.json`). Card `t_a1170172` (gamedev, running) owns this class.
10. CAPTURE-QUIET is a real finding, not a preference: this refresh opened two game windows and played music twice,
    once through the build and once through the capture, before any gate stopped it. Card `t_7c0f1450` is ready and
    unfixed.

## 4. The top 5 blockers to the playable slice, in order

1. **The route points at three rows that do not exist.** `data\slice.json` names scene `drive_to_southampton`,
   map `southampton_town_quay` and scene `quay_gate_checkpoint`; `data\scenes\all.json` holds 5 rows and none of
   those, `data\maps\all.json` holds 2 and neither is the quay. Everything from the drive to the gate is a name with
   no row behind it (`route_check.py` output this run).
   Covering cards: ARRIVAL-MAP-2 `t_db2995d7` (todo, job-discovery), TEST-ARRIVAL-MAP `t_3a52845d` (todo, testing),
   SHIP-DECK-MAP `t_a3fa132a` (todo, job-discovery). No card owns the drive scene, which is the largest single hole
   on this page.
2. **The first fight is not on the route.** No scene op anywhere names `tutorial_sailors`; the only `battle` op is in
   `percy_lore_stop`, which fights `percy` (`route_check.py` output). The fight is provable from
   `data\encounters\all.json` and `test_first_fight` and unreachable from the walk.
   Covering card: R32 TEST-SLICE-ROUTE `t_030a89e5` (running, testing) will detect it; no card fixes it.
3. **The save step has nothing to run.** `grep -c '"save"' game\scripts\pp_scene\pp_scene.gml` returns 0, no scene
   row carries a `save` op, and no run has produced a save file. R26 built the save contract and the log terminal;
   the route cannot call it.
   Covering card: R33 TEST-SAVE-GAMEOVER `t_00998131` (todo, testing) for the pin; no card adds the op.
4. **The game over has code and no proof.** `pp_battle_director.gml` lines 50 to 60 and 373 to 400 carry the fade, the
   card, CONTINUE and RETURN TO TITLE; `grep -rln "gameover\|game_over" tests\` returns nothing, and no capture shows
   a defeat. R27 is marked done on that code alone.
   Covering card: `t_00998131` for the test; no card captures the screen.
5. **The frames a judge watches are off the NES palette, and the pipeline that makes them is not reproducible.**
   `play_demo.py --check` finds palette share 0.1127 to 0.1132 on 3 of its 7 sampled frames (t=48.5, 61.7, 69.8) and
   files it as an art finding; the fresh title crop carries 29 colours outside `data\nes_palette.json`; 8 art and
   capture tests stay red, so a rebuild can change pixels nobody chose.
   Covering card: `t_a1170172` (running, gamedev) for the title frame only; nothing covers the walk and dialogue
   frames or the reproducibility class.

Not in the top 5 and still true: no licence file at the root (row 22), and the 25 Pine failures remain unclassified
between Windows-only and real, which is the audit's own proposed card AUDIT-GATE-CLASSIFY.

## 5. Cards that cover these, and the gaps no card covers

| Blocker | Covering card and status | Uncovered part | Proposed card | Owner |
| --- | --- | --- | --- | --- |
| 1 route targets | `t_db2995d7`, `t_3a52845d`, `t_a3fa132a` (all todo) | the drive scene and its scene row | DRIVE-SCENE: build `drive_to_southampton` in `data\scenes\all.json` with a map and a room, or remove the route row and say so in `PLAN.md` | gamedev (the spec is theirs) |
| 2 fight not on the route | `t_030a89e5` (running) detects only | the wiring | ROUTE-FIGHT-WIRE: put a `battle tutorial_sailors` op on the boarding scene or the route step, and one command that reaches it | builder |
| 3 save step | `t_00998131` (todo) pins only | the op itself | SLICE-SAVE-OP: add the `save` case to the scene command list and prove one save file appears | builder |
| 4 game over unproven | `t_00998131` (todo) tests only | the capture | GAMEOVER-PROOF: one capture of a defeat, the CONTINUE and the RETURN TO TITLE, named by path | testing |
| 5 off-palette frames and reproducibility | `t_a1170172` (running, title only) | walk, dialogue frames, and the 8 red art tests | SLICE-FRAME-PALETTE: every sampled frame of the recording holds palette share 0.90 or better, or the frame is restated as accepted | builder |
| 5 (second half) | none | a rebuild that reproduces its committed PNGs | ART-REPRO: `title_art_v2`, `make_title_ui`, `look`, `make_title_world`, `scene_palette_set`, `make_env_ship` green on Pine, or each one declared Linux-only with the reason | builder |
| 22 docs, licence | `t_8d7bad5f` done for the README | the licence file | LICENCE-ROOT: one root `LICENCE` naming the project's own terms and the prior-work position | assistant |
| 20 gate classification | none | the Windows-only split of 25 failures | AUDIT-GATE-CLASSIFY: a written split, one line per failing test, so the gate can go green honestly | audit |

None of these is created. Chain of command as of 2026-10-22: Nayil and the gamedev profile are the heads, and the
gamedev spec is never overridden here. The DRIVE-SCENE item is the one place a proposal could collide with a spec
decision, so it is stated as gamedev's call: if the drive is cut from the slice, the route row is deleted, not
invented. Anything that needs Nayil's decision is posted as `Q: for gamedev`, not settled here.

## 6. Check for this page

- Every changed score carries a measured line: row 22 has `README.md` at the root read this run plus a `^licen`
  count of 0; the new route row has the `route_check.py` table above; the mean is arithmetic over the table, printed
  by `scores.py` (50 over 22 before, 51 over 22 after).
- The three PIN outcomes I could not settle are labelled as such: the 25 Pine failures are not split into Windows-only
  and real; `test_intro::test_the_star_generator_rewrites_the_committed_sprite` failed on a PNG byte compare and is a
  Pillow-build suspect, not a verdict; and I did not run the recorder itself, so the only recording is still the 18:13
  file.
- Four Pine result files are `error` with `Errno 10054` and I retried each dead shard once before writing this page;
  the 886 and 25 come only from the 7 shards that returned a `SUMMARY` line.
- A second read finds 0 em dashes and 0 en dashes in this file; the hyphens that remain are inside file names, card
  ids, command flags and the words `Windows-only` and `Game-over` in the table above.
- The raw outputs this page quotes sit in the card workspace
  `<agent-runtime>\kanban\boards\nayil-ops\workspaces\t_2362f051`: `pine3b.log`, `pine_s0.log`,
  `pine_s1.log`, `pine_r0b.log`, `pine_r1.log`, `capture.log`, `demo_check.log`, `route_check.py`, `fresh_crop.py`,
  `png_compact.py`, `scores.py`.
