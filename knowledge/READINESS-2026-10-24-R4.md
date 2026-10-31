# Readiness refresh 4, 2026-10-23 21:01 to 21:41: the 22 row table re-measured

Written by audit for card `t_dd873de6` (AUTO-AUDIT-REFRESH). Every number below came from a command this run executed
on this PC between 21:01 and 21:41 Pacific, or from a file this run opened; worker reports, card results and the
earlier readiness pages were not accepted as evidence. The pages `READINESS-2026-10-24.md` (02:05),
`READINESS-2026-10-24-R2.md` (06:30) and `READINESS-2026-10-24-R3.md` (13:07) are left untouched; this is a new page.

P: the 22 row table still sums to 57, mean 2.591, exactly where the 13:07 page left it. No score moved in eight hours.
P: one number in the 13:07 page does not reproduce: it read the drive shots as 10 of 12 palette legal. I measure 0 of 12.
P: the drive room's own frames are drawn in colours that are not in the 2C02 palette at all, and no gate scans them.
P: the eleven art tests that were red at 13:07 are green now: ten of them on Windows, all eleven inside the Pine total.
P: my build compiled and ran the game live 21:01 to 21:07 from HEAD ab475d2, and the title capture passed at 21:08.

## 0. The tree this run measured

    git HEAD                       ab475d2 at 20:24 (PP: rebuild PP-04 navy, the hook meter floor, as v2 and v3)
    git status --porcelain         730 entries, dirty
    data/slice.json                1741 B a42993c7ca7245cb, 9 route steps (title, crawl, drive, arrival, gate,
                                   boarding, fight, save, gameover)
    data/scenes/all.json           5423 B 78390c43b363fa59, 13 scene ids, no drive_to_southampton
    data/maps/all.json             16826 B 8f5df49b72e6b1ff, music PP-03 twice and PP-05 twice
    data/dialogue/all.json         11547 B fcbe450b94f4b60c
    data/scene_palettes.json       24192 B 74e9807fe9aa4cde, 12 scenes, none of them the drive
    data/characters/party.json     295 B 792079001e701035, unchanged since 10-19 18:47
    game/rooms                     rm_pp_boot, rm_pp_drive, rm_pp_ship, rm_pp_title (4)
    output/PrimordialParadox.win   459724 B written 21:01 by my build
    README.md 11908 B 03:13, LICENCE 5040 B 02:21, CREDITS.md 14394 B 06:48 (root)

All from `probe_r6.py` output, `probe_r6.out`.

## 1. The four gates, each from this run's own output

1. `python tools/check_data.py` 21:03, **exit 0**, `check_data: all files pass` (`gate1_r6.out`).
2. `python tools/check_cleanroom.py` 21:03, **exit 0**, `check_cleanroom: no study reference, no foreign name, no
   foreign phrase, every module reviewed` (`gate2_r6.out`).
3. Pine suite, **1325 passed, 4 failed, 28 skipped, 1 deselected** over 3 completed shards and 76 files
   (`python3 pine_offload.py --shards 3 --name audit-r6`, all started 21:01:42, wall 197.1 s, 86.7 s, 92.0 s;
   `offload-audit-r6-0.json` 418 passed 0 failed, `-1.json` 537 passed 2 failed, `-2.json` 370 passed 2 failed).
   The 4 reds are `tests/test_slice_route.py` twice (both the drive step) and `tests/test_project.py` twice
   (`test_project_graph_matches_disk`, `test_generated_project_files_are_current`).
4. `python tools/nes_audit_all.py` 21:04, **exit 1**, `nes_audit_all: FAIL 184 file(s), 34 failing, 0 unmeasured`
   (`gate4_r6.out`). Same 34 count as 13:07, different membership: `output/drive_gantry_preview.png` is now in the
   scan and fails `background_area x1`, while the three title captures still fail 2 px each.

Local runs beside the Pine ones, this PC, this run:

- `python -m pytest tests/test_make_title_ui.py tests/test_title_art_v2.py tests/test_look.py
  tests/test_scene_palette_set.py tests/test_nes_check.py tests/test_project.py -q` 21:07 gives **3 failed, 116
  passed in 26.09 s** (`local_art_r6.out`), and all three reds are `test_project.py`
  (`test_project_graph_matches_disk`, `test_generated_project_files_are_current`,
  `test_build_inputs_are_committed`). The third is not in the Pine total: `test_build_inputs.py` is never offloaded
  because it shells out to git.
- `python -m pytest tests/test_slice_route.py -q` 21:03 gives **2 failed, 22 passed in 0.75 s**
  (`local_route_r6.out`), both reds naming `step drive: the scene 'drive_to_southampton' is not in
  data/scenes/all.json`.

## 2. The 22 row table

Scale unchanged: 0 nothing, 1 spec only, 2 code or data but unproven in the game, 3 proven in the running game with a
capture or a test, 4 polished. Base is `HACKATHON-AUDIT-2026-10-22.md` section 1.

| # | Subsystem | Base | 02:05 | 06:30 | 13:07 | Now | Evidence for the Now value |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Title screen | 3 | 3 | 3 | 3 | 3 | Fresh capture this run: `python tools/capture_title.py` 21:08, exit 0, `output/title_run_1.png` 784x759 written 21:08:01, `viewport score 1.000`, "the game closed on request (exit code 0)" (`capture_title_r6.out`). Viewport crop [8,31,768,720] is 38 colours at **0.9999** on the 55 colour master, 28 blended colours (`probe_r6d.out`). Not 4: `python tools/nes_check.py output/title_run_reference_3x.png --type background` is **FAIL 31 problem(s)**, all palette blends at 1 to 3 px (`nes_title_r6.out`), and the committed native frame `output/nes_title_frame.png` 11 colours 1.0000 is stale at 10-21 22:01, before the 20:16 title sprite rewrite. |
| 2 | Intro crawl | 3 | 3 | 3 | 3 | 3 | `output/crawl_mid.png` 4 colours at 0.9667, `crawl_end.png` 4 at 0.9619, each 1 off-palette colour (`probe_r6.out`); files are 10-22 07:57, not re-shot this run. Route step `crawl` resolves in the 9 step slice (`local_route_r6.out`, 22 passed). |
| 3 | Drive cutscene | 1 | 2 | 3 | 3 | 3 | `rm_pp_drive` exists and compiles. The 12 frames the room wrote are in `%LOCALAPPDATA%\PrimordialParadox` (`tools/capture_drive.py:58` names it), copied into `output/drive/pp_drive_shot_01..12.png` 768x720 at 02:35, and `output/drive_frames/drive_shot_01..12.png` are their 3x nearest downscales (`tools/eye_drive.py:62-63`). Proven in the running game. **The 13:07 palette figure does not reproduce:** measuring those frames against the 55 RGB values of `data/nes_palette.json`, every shot is 0.0000 to 0.0167 legal (`probe_r6e.out`), and shot 01's eight colours (`08131F` 45.1 pct, `1B1B22` 34.4 pct, `0B0B0F` 10.3 pct) are all outside the 2C02 set. Not 4 even on the old reading: the route cannot take the step (section 3). |
| 4 | Overworld movement | 3 | 3 | 3 | 3 | 3 | No live evidence from my build this run: the live log reaches `rm_pp_title` and no further (`build/last-igor.log` lines 108 to 130). Carried on `build/first_fight_game.log` footstep cues and `output/demo/run_002_verify.json`, both from earlier runs and labelled as such. |
| 5 | Maps and doors | 2 | 2 | 2 | 2 | 2 | `data/maps/all.json` 16826 B, 4 map ids, music on 4 rows; the route's `arrival` and `gate` steps resolve in `local_route_r6.out`. Still no capture of a door traversed on any map but `ship_small`, and `rm_pp_ship` is the only playable room. |
| 6 | Dialogue and talk | 3 | 3 | 3 | 3 | 3 | `data/dialogue/all.json` 11547 B (unchanged from 13:07); `tests/test_dialogue_v2.py` and `test_dialogue_choice_layout.py` are in Pine shard 0, which is 418 passed 0 failed (`offload-audit-r6-0.json`). |
| 7 | Battle and the talk fight | 2 | 2 | 3 | 3 | 3 | Carried, not re-earned: `output/first_fight_verify.json` is `ok: true` at 06:31, 247407 B, and no new capture exists since (`ls output/*fight*`). `tests/test_first_fight.py` is in Pine shard 2 and green. Not 4: the art defects in row 18 survive. |
| 8 | Enemies | 2 | 2 | 2 | 2 | 2 | `output/enemies_preview_3x.png` 464x772, 9 colours, 1.0000 on master (`probe_r6.out`); the enemy art inside a live fight is still unmeasured. |
| 9 | Party and stats | 2 | 2 | 2 | 2 | 2 | `data/characters/party.json` 295 B, last written 10-19 18:47; no test names a level up and no card on the board mentions party or stats (`kw_r6.py`). |
| 10 | Save and load | 2 | 2 | 3 | 3 | 3 | `output/save_capture_verify.json` `ok: true` at 03:43 with the four frames named, `output/save_capture_landing.png` 768x720 7 colours 1.0000 and `output/save_capture_log_terminal.png` 768x720 7 colours 1.0000 (`probe_r6.out`, `final_r6.py`); the live log this run prints `PP: save read and accepted, music` (`build/last-igor.log:118`). The confirm frame is a raw 784x758 window shot at 1640 colours and 0.0995, so it is evidence of a window, not of a legal frame. |
| 11 | Ledger | 2 | 2 | 2 | 2 | 2 | `tests/test_ledger.py` is in Pine shard 0, which is 418 passed 0 failed (`offload-audit-r6-0.json`); still no capture of a ledger row read back. No open card mentions the ledger (`kw_r6.py`). |
| 12 | Audio bus and cues | 3 | 3 | 3 | 3 | 3 | My build's live log (`build/last-igor.log`, 21:01 to 21:07): `PP audio: title_theme streaming streams/title_theme_v3_126.ogg, instance 400001, gain 0.70`, `PP audio: focus lost, music paused (cue and theme) and every effect stopped`. The storm that played `thunder_soft` **435 times** at 13:01 played it **11 times** in this 6 minute run (instances 400002 to 400012), so it is damped, not fixed. |
| 13 | Music per scene | 2 | 2 | 2 | 2 | 2 | Data now names music on 4 map rows (`PP-03` twice, `PP-05` twice) and 3 scene music commands, but my live log names only the title theme, so per-room coverage stays unproven in the game. |
| 14 | SFX | 3 | 3 | 3 | 3 | 3 | Live cues this run (thunder, text blip, menu), and `game/datafiles/sfx/sfx.json` has **0** entries for `car_engine` while the live log line 109 still prints `PP audio: car_engine_loop silent, not in sfx/sfx.json`, so the drive is silent. |
| 15 | UI windows and menus | 2 | 2 | 2 | 2 | 2 | The three window assertions that failed in `tests/test_nes_check.py` at 13:07 are green now, on this PC (`local_art_r6.out`, 116 passed) and on Pine (`offload-audit-r6-1.json`, 537 passed 2 failed, neither of them this file). Still 2 because a preview is not a live window and gate 4 still fails `output/title_ui_preview.png` (1920x784, 0.0110 on master, 7 off-palette colours, `probe_r6.out`). |
| 16 | Art pipeline | 2 | 3 | 3 | 3 | 3 | Re-earned this run, where 13:07 carried it: the ten art tests that were red in the files I ran (5 `test_make_title_ui`, 2 `test_title_art_v2`, 2 `test_look`, 1 `test_scene_palette_set`) pass on Windows (`local_art_r6.out`), and the eleventh, `test_make_title_world`, is green inside Pine shard 0 (`offload-audit-r6-0.json` 418 passed 0 failed). Every sprite source rewritten today is 1.0000 on master with 0 off-palette colours (`probe_r6b.out`, 45 files). Not 4: the pipeline's own drive output is the off-palette art in row 3. |
| 17 | Sprites per character | 2 | 2 | 2 | 2 | 2 | Five new sheets at 16:09, `percy_ow_v2`, `hadrian_ow_v2`, `zander_ow_v2`, `konrad_ow_v2`, `sailor_ow_v2`, each 128x16 = 8 frames of 16x16 and each 1.0000 on master (`probe_r6b.out`). Still 2: `chars_contact.png` and `chars_preview_3x.png` are 10-22 02:40 and no capture names a character sprite in the running game; card `t_858c2908` (car, Ronan, Theo, storm cloud) is blocked. |
| 18 | Backgrounds per scene | 3 | 3 | 2 | 2 | 2 | Unchanged: three roles still print `PP_COLOUR_MISSING` and the strip lookup still names a room palette set the scene does not own (`build/first_fight_game.log`); my build reaches no battle, so this is carried, not re-measured. |
| 19 | Build and packaging | 3 | 3 | 3 | 3 | 3 | My build: `python tools/integration_build.py` started 21:01, `output/PrimordialParadox/PrimordialParadox.win` 459724 B at 21:01, `build/last-build-error.log` 0 B, and at 21:07 `Igor finished` then **`BUILD PASS: Igor compiled the project and launched the game`, exit 0** (`build/audit-r6-build.log`). The game ran as `Runner.exe` pid 19300, window `Primordial Paradox`, for 6 minutes; `taskkill /PID 19300` with no force flag sent the close, the process was gone on the next check, and the build then returned 0. Runner is still the 7941704 B exe of 10-20; no zip and no install step. |
| 20 | Tests and gates | 2 | 2 | 2 | 2 | 2 | Gate 1 exit 0, gate 2 exit 0, gate 4 exit 1 on 34 of 184, Pine **1325 passed, 4 failed** (`offload-audit-r6-*.json`), local art and project set **3 failed, 116 passed** (`local_art_r6.out`), local route **2 failed, 22 passed** (`local_route_r6.out`). Five reds across the two platforms, four of them the same two defects. Not green, so not 3. |
| 21 | Capture and demo tooling | 2 | 2 | 3 | 3 | 3 | `tools/capture_title.py` passes end to end in this run at 21:08, exit 0, two frames, game closed with code 0 (`capture_title_r6.out`); `tests/test_capture_title.py` and `tests/test_play_demo.py` are green on Pine (`offload-audit-r6-1.json`, `-2.json`). Not 4: no new video since 01:49, and `output/demo/run_002_verify.json` still says `audio: rendered stand-in from run_002_audio.m4a, not the game's live output`. |
| 22 | Docs and repo hygiene | 1 | 2 | 3 | 3 | 3 | Root `README.md` 11908 B 03:13, `LICENCE` 5040 B 02:21, `CREDITS.md` 14394 B 06:48, all opened this run. The README's own state table and its "mean 2.2" line are 10-22 vintage, so it is honest but stale against this page. |

Rows 22, sum **57**, mean **2.591**; the 02:05 page was 53, the 06:30 page 57, the baseline 50. Sums are computed by
`sums_r6.py`, which prints all five columns.

## 3. What moved, and what did not, with the command behind each

No score moved. Five things changed under the scores, and one earlier number is corrected:

- **The drive frames were never palette legal.** 13:07 read "10 of 12 at 1.0000 on palette". Measured now against the
  55 distinct RGB values of `data/nes_palette.json`, every one of the 12 shots in `output/drive/` and their
  `output/drive_frames/` downscales is 0.0000 to 0.0167 legal, and shot 01's top three colours (`08131F`, `1B1B22`,
  `0B0B0F`) are each outside the 2C02 set (`probe_r6e.out`). `data/scene_palettes.json` holds 12 scene sets and none
  of them is the drive, so RULE 0 point 1 was never written for this scene. One auxiliary conversion exists,
  `output/drive/pp_drive_shot_03_1x_ppu.png` 256x240 7 colours at 1.0000, for shot 03 only.
- **The art tests flipped green, on two platforms.** Eleven art rows were red at 13:07: 5 `test_make_title_ui`, 2
  `test_title_art_v2`, 2 `test_look`, 1 `test_scene_palette_set` and 1 `test_make_title_world`. This run the first ten
  are green on Windows (`local_art_r6.out`, 3 failed 116 passed, all three reds `test_project`) and all eleven are
  green inside the Pine total, whose 4 reds are the route and the project rows (`offload-audit-r6-0.json` 418 passed 0
  failed, `-2.json`). The reproducibility blocker from the 10-22 audit is closed; row 16 was the only row still
  carrying it as an assumption and it no longer does.
- **The thunder storm is damped tenfold, not fixed.** 435 `thunder_soft` plays in one launch at 13:01 against 11 in
  a 6 minute launch at 21:01 to 21:07 (`build/igor-show-run.log` then `build/last-igor.log`). At the title alone,
  that is still one strike every 30 seconds.
- **The engine loop is still missing from the sfx index.** `PP audio: car_engine_loop silent, not in sfx/sfx.json`
  (`build/last-igor.log:109`), and `grep -c car_engine game/datafiles/sfx/sfx.json data/audio.json` returns 0 and 0.
- **A fresh title capture exists and is still not NES legal.** 21:08 capture, 38 colours at 0.9999 with 28 blended
  colours, and `tools/nes_check.py` returns FAIL 31 problems on the 3x reference (`nes_title_r6.out`). The blends are
  the same defect card `t_a1170172` already names for the scroll frames (`#0b0b0f` at 1314 px there); `0B0B0F` is also
  10.3 pct of drive shot 01, so one partial-alpha draw is dirtying two subsystems.
- **Gate membership moved.** Still 34 of 184, but `output/drive_gantry_preview.png` is now scanned and fails, while
  `output/drive/` and `output/drive_frames/` (24 files) are still outside the scan (`gate4_r6.out`, `probe_r6e.out`).

## 4. The top five blockers to the playable slice, with the card that owns each

1. **The drive has no palette set and no scene row, and the route cannot take its step.** 12 of 12 game frames are
   outside the 2C02 palette, `data/scene_palettes.json` has no drive entry, and `pytest tests/test_slice_route.py -q`
   is 2 failed 22 passed with both reds naming `drive_to_southampton` (`probe_r6e.out`, `local_route_r6.out`).
   Covered: `t_c27552e3` R21b DRIVE-SCENE (builder, todo, priority 98), `t_ff5a3714` SLICE-ROUTE-DATA (gamedev,
   todo), `t_3cca8576` REVIEW-R21-DRIVE (code-review, todo). None of them owns the palette set. Proposed card, owner
   gamedev, because RULE 0 point 1 is a spec: `DRIVE-PALETTE-SET: a drive scene palette set in
   data/scene_palettes.json and 12 of 12 shots inside it, with the measured fraction per shot as the acceptance`.
2. **Two `test_project` rows are the remaining non-route reds, and no open card names them.**
   `test_project_graph_matches_disk` and `test_generated_project_files_are_current` are 2 of the 4 Pine reds and 2 of
   the 3 local reds (`offload-audit-r6-2.json`, `local_art_r6.out`). `t_c31f9295` (audit, blocked) names a different
   defect, four untracked audio sources. Proposed card, owner builder: `PROJECT-GATE-RED: test_project_graph_matches_disk
   and test_generated_project_files_are_current green on the current tree, or each restated with the reason it is red`.
3. **The NES gate does not scan the drive art.** `nes_audit_all: FAIL 184 file(s), 34 failing` and the only drive file
   in the list is `output/drive_gantry_preview.png` (`gate4_r6.out`). The 16 PNGs in `output/drive` and the 12 in
   `output/drive_frames`, including the 12 the drive room itself wrote, are outside the scan, which is how 12 illegal
   frames shipped with every gate as it was. `t_3cca8576` reviews
   the shots against the shot list, which is judgement and not the gate. Proposed card, owner testing:
   `NES-GATE-DRIVE-FRAMES: the NES gate scans output/drive/ and output/drive_frames/, and every shot is measured
   against data/nes_palette.json in the report`.
4. **The judged video's audio is a rendered stand-in and both videos are old.** `output/demo/run_002_verify.json`
   `ok: true` with `audio: rendered stand-in from run_002_audio.m4a, not the game's live output`; run_002.mp4 is 01:49
   and run_001.mp4 10-22 18:13; the only open card with "demo" in it is `t_030a89e5` R32 TEST-SLICE-ROUTE (testing,
   blocked), which is about the route, not the recorder (`kw_r6.py`). Proposed card, owner testing:
   `DEMO-AUDIO-LIVE: one recorded run whose audio track is the game's own output, with the verifier's audio field
   reading live and not stand-in`.
5. **The drive plays silent, and no card owns it.** `PP audio: car_engine_loop silent, not in sfx/sfx.json`
   (`build/last-igor.log:109`), and `car_engine` appears 0 times in `game/datafiles/sfx/sfx.json` and 0 times in
   `data/audio.json` (`grep -c`, this run). The drive is the pitch's signature scene and the one sound it needs is the
   one missing. No card on the board matches `car_engine` or `engine loop` (`kw_r6.py`). Proposed card, owner
   musician, because the sfx index and the cue are the audio lane's: `DRIVE-ENGINE-LOOP: car_engine_loop in
   game/datafiles/sfx/sfx.json with a cue, and the live log stops printing "silent, not in sfx/sfx.json"`.

Not a blocker, but worth correcting from 13:07: the first fight **is** captured. `output/first_fight_capture.mp4` is
2237724 B at 04:42, `output/first_fight_frames/` holds 123 frames, and `output/first_fight_verify.json` is `ok: true`
at 06:31, 247407 B. Row 7 stays 3 on that evidence, held by `t_87ee4228` FIRST-FIGHT-LIVE in review. What my run
cannot do is add anything newer, because the build never reached a battle.

Outside the five and still true: gate 4 red on 34 of 184; `output/title_ui_preview.png` 1920x784 at 0.0110 on master;
`title_run_1.png` fails `nes_check` at native size on grid and palette; `output/crawl_mid.png` still carries its one
off-palette colour; the ledger and party stats have no card at all (`kw_r6.py`).

## 5. What I could not measure, and why

- **A live battle and a live overworld walk.** My build ran the game 21:01 to 21:07 and the log stops in the title
  room. Rows 4, 7 and 18 are carried from earlier logs and say so.
- **The three Windows-only suite files.** `tests/test_build_inputs.py`, `test_test_inputs.py` and `test_sync_art.py`
  are never offloaded; I ran `test_build_inputs.py` locally inside the 6 file command above, which is where the third
  `test_project` red comes from, and I did not run `test_test_inputs.py` or `test_sync_art.py`.
- **The 20:16 title sprite rewrite on screen.** The fresh capture is live but I did not diff it pixel for pixel against
  the 20:16 sources, and the committed native frame is 10-21, so "the rewrite reached the screen" is unverified.
- **Any Meta model call.** None was made by this run; every line of text the game printed is the written fallback.

## 6. Q: for gamedev

Two questions, both spec, neither mine to decide. The first is posted as blocked card `t_f034f9d0`
(assignee gamedev, created by audit, 21:18) so it has an owner. The second still has no card: section 4 of the 13:07
page proposed `BATTLE-FIELD-WIRING` for it and the board still does not carry that name (`kw_r6.py`, `board_r6.out`).

1. The drive's palette. RULE 0 point 1 says every scene starts from a palette set in `data/scene_palettes.json`, and
   the drive has none; its room draws 12 frames in `081420`/`2E2E3A`/`4A4A58` and similar, which are not 2C02
   entries. Is the drive meant to be a graded, non-NES look (and then the art bible needs that ruling written down),
   or is it meant to be quantized like the rest, with shot 03's `pp_drive_shot_03_1x_ppu.png` as the pattern for all
   twelve?
2. The battle field's palette set. Carried from 13:07 and still unmeasured: the fight at `ship_small 4,7` logs
   `bg_battle_deck_night is not in the art index` while its room palette set is `deck_day`, and three roles print
   `PP_COLOUR_MISSING` (`build/first_fight_game.log`, 04:43). Which is the contract: the `deck_night` strip with
   `deck_night` roles, or a `deck_day` room and the strip name is the error?

## 7. Check for this page

- Every row carries a file this run opened or a command it ran. The run's own outputs are `gate1_r6.out`,
  `gate2_r6.out`, `gate4_r6.out`, `local_route_r6.out`, `local_art_r6.out`, `capture_title_r6.out`,
  `nes_title_r6.out`, `probe_r6.out`, `probe_r6b.out`, `probe_r6c.out`, `probe_r6d.out`, `probe_r6e.out`,
  `board_r6.out`, `kw_r6.py`, `sums_r6.py`, all under
  `<agent-runtime>\kanban\boards\nayil-ops\workspaces\t_dd873de6\`.
- The Pine evidence is `offload-audit-r6-0.json`, `-1.json`, `-2.json` under
  `<workspace>\Shared\projects\arananet\pine\data\results\`.
- The sums are computed by `sums_r6.py`, which prints `base 50`, `0205 53`, `0630 57`, `r3 57`, `now 57`,
  `mean 2.591`.
- Board statuses in section 4 come from `nayil-ops\kanban.db` read-only at 21:03 (`board_r6.py`), 86 open cards, of
  which 63 blocked. The Q card `t_f034f9d0` was created after that read and verified with `kanban show`.
- One side effect to declare: running `python tools/nes_audit_all.py` rewrote `knowledge\NES-AUDIT.md` (122226 B,
  21:04) and the 170 per-file reports under `output\nes_audit\` plus `output\nes_audit_worst_3x.png`, because that is
  what the gate writes on every run. Nothing in `data\`, `game\` or `tests\` was written by this run.
- This page contains 0 em dashes, 0 en dashes and 0 figure dashes; hyphens appear only in file names, card ids,
  flags and compounds.
