# Readiness refresh 3, 2026-10-23 12:57 to 13:55: the 22 row table re-measured

Written by audit for card `t_85c957fd` (AUTO-AUDIT-REFRESH). Every number below came from a command this run
executed on this PC between 12:57 and 13:55 Pacific, or from a file this run opened; card results and the earlier
readiness pages were not accepted as evidence. Pages `READINESS-2026-10-24.md` (02:05) and
`READINESS-2026-10-24-R2.md` (06:30) are left untouched; this is a new page beside them.

P: the 22 row table sums to 57, mean 2.591, exactly where the 06:30 page left it; nothing moved in six hours of commits.
P: three real movements are below the score line: the fight verifier flipped to `ok: true`, gate 2 went fully green, the title crop is 0.9999 palette legal.
P: the route still cannot take its drive step (`drive_to_southampton` absent from `data/scenes/all.json`), measured twice: a local pytest and the test.
P: the first Pine run errored on all three shards because `python` has no pinesandbox module; the `python3` rerun finished 1325 passed, 4 failed.
P: my build compiled and ran live at 12:58 to 13:01 from `HEAD cb671e1`, and the live log shows `thunder_soft` fired 435 times in one run.

## 0. The tree this run measured

    git HEAD                       cb671e1 at 10:52 (PP FIX-YYP-5: list pp_05_small_ship_v4.ogg in the yyp)
    git status --porcelain         705 entries, dirty
    data/slice.json                1741 B a42993c7ca7245cb, 9 route steps, save trigger deck_save
    data/scenes/all.json           5423 B 78390c43b363fa59, 13 scene ids, no drive_to_southampton
    data/maps/all.json             16826 B 8f5df49b72e6b1ff, 4 map ids
    data/dialogue/all.json         11547 B fcbe450b94f4b60c, 40 rows
    data/encounters/all.json       4533 B 850b911efc5d57e5, 3 ids
    data/scene_palettes.json       24192 B 74e9807fe9aa4cde, 12 scenes, 4 hero palettes
    game/rooms                     rm_pp_boot, rm_pp_drive, rm_pp_ship, rm_pp_title (4)
    output/PrimordialParadox.win   459724 B written 12:58 by my build

The clock note that matters: the twelve drive frames were rewritten at 12:28, inside this run's window, and the
dialogue file grew by 511 B since 06:30.

## 1. The four gates, each from this run's own output

1. `python tools/check_data.py` 12:58, **exit 0**, `check_data: all files pass` (`gate1_r4.out`).
2. `python tools/check_cleanroom.py` 12:58, **exit 0**, `check_cleanroom: no study reference, no foreign name, no
   foreign phrase, every module reviewed` (`gate2_r4.out`). At 06:30 this gate still listed 1 of 40 modules awaiting
   review; it now reports every module reviewed. That is a real change under the score line.
3. Pine suite, **1325 passed, 4 failed** over three completed shards (`python3 pine_offload.py --shards 3 --name
   audit-r5`, uploaded 34231563 B, 76 files, 13:13 to 13:52; `offload-audit-r5-0.json` 418 passed 0 failed,
   `-1.json` 537 passed 2 failed, `-2.json` 370 passed 2 failed, 1 deselected by design). The 4 reds are
   `test_slice_route` twice (both the drive step) and `test_project` twice
   (`test_project_graph_matches_disk`, `test_generated_project_files_are_current`). Note the trap in front of that
   number: the first attempt (`python pine_offload.py --shards 3 --name audit-r4`, 12:57) returned `status: error` on
   all three shards with `PineConfigError: the pinesandbox SDK is not importable in this process
   (ModuleNotFoundError)` (`offload-audit-r4-0.json`, `-1.json`, `-2.json`) and still exited 0. The interpreter named
   `python` lacks the module; `python3` imports it (
   `<home>\AppData\Local\Python\pythoncore-3.14-64\...\pinesandbox\__init__.py`, checked).
4. `python tools/nes_audit_all.py` 13:00, **exit 1**, `nes_audit_all: FAIL 184 file(s), 34 failing, 0 unmeasured`
   (`gate4_r4.out`): 20 `sheet*`, 10 `frame`, 4 `capture*`. Same 34 as 06:30 against 3 more files.

Local stand-in for the suite while Pine was pending, on Windows, this PC, 13:20:
`python -m pytest tests/test_slice_route.py tests/test_no_network_in_build.py -q` gives **2 failed, 35 passed**
(`local_route_r4.out`), and both reds are the drive step. `test_no_network_in_build` is green now, which it was not
in the 06:30 Pine run.

## 2. The 22 row table

Scale unchanged: 0 nothing, 1 spec only, 2 code or data but unproven in the game, 3 proven in the running game with a
capture or a test, 4 polished.

| # | Subsystem | Baseline | 02:05 | 06:30 | Now | Evidence for the Now value |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Title screen | 3 | 3 | 3 | 3 | `output/title_run_1.png` 784x759, 267 colours overall but its 768x720 viewport crop is 32 colours at **0.9999 on palette** against the 109 hex values of `data/nes_palette.json` plus `data/palette.json` (`probe_png2.py`). Frames are the 05:05 pair; no fresh capture this run. Not 4: gate 4 still fails `title_run_1.png`, `title_run_2.png` and `title_run_reference_3x.png` on `background_area x2, palette x2` (`gate4_r4.out`). |
| 2 | Intro crawl | 3 | 3 | 3 | 3 | `output/crawl_mid.png` 4 colours at 0.9667 on palette and `crawl_end.png` 4 at 0.9619, both carrying `F9F9F9` at 3.33% and 3.81% (`probe_png2.py`). Not re-run live this window. |
| 3 | Drive cutscene | 1 | 2 | 3 | 3 | All 12 `output/drive_frames/drive_shot_*.png` are 256x240 and were rewritten 12:28; 10 of 12 are at **1.0000** on palette, shot 01 at 0.1035 (dominated by `08131F` 45%, `1B1B22` 34%) and shot 07 at 0.0081 (`probe_png2.py`). Room `rm_pp_drive` exists and compiles. Not 4: the route cannot take the step, section 3. |
| 4 | Overworld movement | 3 | 3 | 3 | 3 | No live evidence from my build this run (it stopped in `rm_pp_title`); carried on `build/first_fight_game.log`'s footstep cues and trigger line, labelled as not from this run. |
| 5 | Maps and doors | 2 | 2 | 2 | 2 | 4 map ids in `data/maps/all.json`; the route's `arrival` and `gate` steps resolve; no capture shows a door traversed on any map but `ship_small`. |
| 6 | Dialogue and talk | 3 | 3 | 3 | 3 | `data/dialogue/all.json` 40 rows, 11547 B (was 11036 B at 06:30); no dialogue test ran in my two local files and Pine is pending, so this row rests on the data plus the 06:30 green run. |
| 7 | Battle and the talk fight | 2 | 2 | 3 | 3 | `output/first_fight_verify.json` is now **`ok: true`** at 06:31 (247407 B), where the 06:30 page read `ok: false`; `build/_first_fight_run3.log`, `run4`, `run5` each carry `battle start` 3 times and `victory` once. Not 4: three `COLOUR_MISSING` lines survive in `build/sfxwire-run2-all-seven.log`. |
| 8 | Enemies | 2 | 2 | 2 | 2 | `output/enemies_preview_3x.png` 464x772, 9 colours, 1.0000 on palette; the enemy art inside the live fight is still unmeasured. |
| 9 | Party and stats | 2 | 2 | 2 | 2 | `data/characters/party.json` 295 B, 3 characters, still the only stats artifact; no test names a level up. |
| 10 | Save and load | 2 | 2 | 3 | 3 | `output/save_capture_verify.json` `ok: true` at 03:43; `output/save_capture_landing.png` 768x720 7 colours at 1.0000 on palette (`probe_png2.py`). |
| 11 | Ledger | 2 | 2 | 2 | 2 | `tests/test_ledger.py` exists and is not among the two local reds; still no capture of a ledger row. |
| 12 | Audio bus and cues | 3 | 3 | 3 | 3 | My build's live log 12:58 to 13:01 (`build/igor-show-run.log`, 441 PP lines): `title_theme streaming streams/title_theme_v3_126.ogg, instance 400001, gain 0.70`, `focus lost, music paused ... and every effect stopped`. New defect below the score: `thunder_soft` played 435 times in one run (instances 400002 to 400436). |
| 13 | Music per scene | 2 | 2 | 2 | 2 | Per-room coverage still unmeasured: the only rooms my log names are the title. |
| 14 | SFX | 3 | 3 | 3 | 3 | Live cues in `build/igor-show-run.log` (thunder, menu_select). New gap in the same log: `car_engine_loop silent, not in sfx/sfx.json`. |
| 15 | UI windows and menus | 2 | 2 | 2 | 2 | `ui_battle_preview.png` 5 colours 1.0000, `ui_dialogue_preview.png` 5 at 1.0000; `title_ui_preview.png` is 1920x784 9 colours and still among gate 4's reds. A preview is not a live window. |
| 16 | Art pipeline | 2 | 3 | 3 | 3 | `output/palette_synergy.json` (272081 B, 12:41) holds 6 results and `data/scene_palettes.json` names 12 scenes and 4 hero palettes, so the RULE 0 toolchain is producing. Not re-tested this run: the art tests were in Pine's pending shards, so the reproducibility claim is carried, not re-earned. |
| 17 | Sprites per character | 2 | 2 | 2 | 2 | `output/chars_contact.png` 736x2768, 22 colours at 1.0000 on palette; `chars_preview_3x.png` still among gate 4's 34 reds. |
| 18 | Backgrounds per scene | 3 | 3 | 2 | 2 | Unchanged from 06:30: the live fight log still prints `PP: role hazard is not in the room palette set deck_day, drawing it as PP_COLOUR_MISSING` and two more roles, and `bg_battle_deck_night is not in the art index` (`build/first_fight_game.log`). |
| 19 | Build and packaging | 3 | 3 | 3 | 3 | My build 12:58 to 13:01: `output/PrimordialParadox/PrimordialParadox.win` 459724 B at 12:58, `build/last-build-error.log` 0 B, `build/last-igor.log` 6296 B at 13:01, live PP lines in `build/igor-show-run.log`. Runner still the 7941704 B exe of 10-20 18:28. No zip, no install step. |
| 20 | Tests and gates | 2 | 2 | 2 | 2 | Gate 1 exit 0, gate 2 exit 0, gate 4 exit 1 on 34 of 184, Pine **1325 passed, 4 failed**, 1 deselected (`offload-audit-r5-*.json`), and the local route pair `2 failed, 35 passed` agrees with the 2 Pine route reds. Four reds is a real improvement on 12, and the gate is still not green. |
| 21 | Capture and demo tooling | 2 | 2 | 3 | 3 | `output/demo/run_002_verify.json` `ok: true`, 4453751 B, 73.5 s, and the same file's own `audio` field reads `rendered stand-in from run_002_audio.m4a, not the game's live output`. Not 4 for that reason. |
| 22 | Docs and repo hygiene | 1 | 2 | 3 | 3 | At the root: `README.md` 11908 B 03:13, `LICENCE` 5040 B 02:21, `CREDITS.md` 14394 B 06:48 (`ls -la`). |

## 3. What moved, and what did not, with the command behind each

The row total did not move: 50 at the baseline, 53 at 02:05, 57 at 06:30, **57 now, mean 2.591** (sums checked by
`sums.py`, 22 rows). Four things changed under the scores and each is measured:

- **The fight verifier is green now.** `output/first_fight_verify.json` `ok: true` at 06:31, 247407 B. The 06:30 page
  read `ok: false` on the same file at 04:49. Row 7 stays 3 because the score ceiling is the art defects, not the
  verifier.
- **Gate 2 is fully green.** `check_cleanroom: ... every module reviewed` (`gate2_r4.out`), against `1 of 40 modules
  still await clean-room review` at 06:30. No score for it; row 20 needs all four gates.
- **The title crop is palette legal.** 32 colours, 0.9999 on palette, against the 06:30 line of 32 colours and 23 off
  palette (`probe_png2.py`). Row 1 stays 3 only because gate 4 fails the three title captures on 2 px each.
- **The drive frames were rewritten and the defect survived.** All twelve have mtime 12:28, and shots 01 and 07 are
  still 0.1035 and 0.0081 on palette, byte sizes 1185 and 1133. A rewrite that leaves the same two shots off palette is
  a repeat, not a fix, and no gate sees it because `output/drive_frames/` is outside the 184 files gate 4 scans.

Two defects that no score covers yet, both from my own live run:

- `PP audio: thunder_soft played, instance 400002` through `400436`: 435 plays in one launch, about 3.6 a second for
  two minutes, in `build/igor-show-run.log`. Either the title storm loops a one shot cue without a rate limit or the
  scheduler is stuck; the audio bus is the judged "it works" surface.
- `PP audio: car_engine_loop silent, not in sfx/sfx.json` in the same log: the drive's engine loop is named by code and
  absent from the sfx index, so the drive plays silent.

## 4. The top five blockers to the playable slice, with the card that owns each

1. **The drive step cannot be taken.** `python -m pytest tests/test_slice_route.py -q` is `2 failed, 35 passed`
   (`local_route_r4.out`), both reds naming `step drive: the scene 'drive_to_southampton' is not in
   data/scenes/all.json`, and the 13 ids in that file do not include it. Covered twice: `t_c27552e3` R21b DRIVE-SCENE
   (builder, todo) and `t_ff5a3714` SLICE-ROUTE-DATA (gamedev, todo). No new card.
2. **Two `test_project` rows are the remaining non-route reds, and their only card is blocked.**
   `tests/test_project.py::test_project_graph_matches_disk` and `::test_generated_project_files_are_current` are 2 of
   the 4 Pine reds (`offload-audit-r5-2.json`). On the board, `t_c31f9295` PP FIX-BUILD-INPUTS-4 (audit) is blocked and
   names a different defect (four untracked audio sources), and no open card names the project graph
   (`board_r4.py`, `board2_r4.py`, 85 open cards). Proposed card, owner builder:
   `PROJECT-GATE-RED: test_project_graph_matches_disk and test_generated_project_files_are_current green on the current tree, or each restated with its reason`.
3. **The battle field still draws with missing palette roles.** `PP: role hazard is not in the room palette set
   deck_day, drawing it as PP_COLOUR_MISSING` (three roles, `build/first_fight_game.log`), while the strip lookup
   names `bg_battle_deck_night`. That is a spec decision, so it is a Q: for gamedev, and it needs a card: nothing on
   the board mentions `art index` or `COLOUR_MISSING`. Proposed card, owner gamedev:
   `BATTLE-FIELD-WIRING: the tutorial fight at ship_small 4,7 draws its strip and every role from one palette set, with the live log lines quoted as the acceptance`.
4. **Two off-palette drive frames pass every gate.** `output/drive_frames/` is not in gate 4's file list
   (`nes_audit_all: FAIL 184 file(s)`, `gate4_r4.out`) while `output/` is, so shots 01 and 07 at 0.1035 and 0.0081 are
   invisible to the guard. `t_3cca8576` REVIEW-R21-DRIVE (code-review, todo) reviews the shots against the shot list,
   which is judgement, not the gate. Proposed card, owner testing:
   `NES-GATE-DRIVE-FRAMES: the NES gate scans output/drive_frames/, and shots 01 and 07 stop being 0.1035 and 0.0081 on palette`.
5. **The Pine offload silently errors under the interpreter the fleet uses.** Three of three shards returned
   `PineConfigError: the pinesandbox SDK is not importable in this process` for `python`, and the same command under
   `python3` imports it (`offload-audit-r4-*.json`, then `audit-r5`). A lane that reports "error" three times and
   exits 0 is a gate that looks like it ran. This card hit it; any other lane will too. No card covers it. Proposed
   card, owner builder: `PINE-SDK-INTERPRETER: pine_offload.py names the interpreter it needs, fails loudly when the module is missing, and the fleet docs name python3`.

Outside the five and still true: gate 4 red on 34 of 184, `title_ui_preview.png` 1920x784 red, `chars_preview_3x.png`
red, `output/crawl_mid.png` still carries `F9F9F9` at 3.33%, and the demo video's audio is a rendered stand-in.

## 5. What I could not measure, and why

- **The three Windows-only files.** `tests/test_build_inputs.py`, `test_test_inputs.py` and `test_sync_art.py` are not
  offloaded by design; I did not run them. The Pine total therefore covers 76 of 79 test files, and the skip counts are
  partial in my capture (8 in shard 0, 11 in shard 1).
- **A fresh title capture and a fresh live fight.** My build ran the game at 12:58 to 13:01 and the log stops in the
  title room with the thunder loop; it reaches no battle, so the fight evidence here is the 06:31 verifier and the
  `_first_fight_run*.log` files, both labelled. I did not launch a separate capture because RULE 1's idle gate and the
  card's 45 minute cap between them left no clean window, and the idle state I sampled at 13:00 (4792 s idle) was spent
  on the build.
- **Windows-only suite files.** `tests/test_build_inputs.py`, `test_test_inputs.py` and `test_sync_art.py` are not
  offloaded by design; I did not run them.

## 6. Q: for gamedev

Carried and still open, now with a second witness. The tutorial fight at `ship_small 4,7` logs
`bg_battle_deck_night is not in the art index` while its room palette set is `deck_day`, and three roles
(`hazard`, `marker`, `marker_trail`) print `PP_COLOUR_MISSING` (`build/first_fight_game.log`,
`build/sfxwire-run2-all-seven.log`). Which is the contract: the `deck_night` strip with `deck_night` roles, or a
`deck_day` room and the strip name is the error? Row 18 stays at 2 until a live run draws a strip.

## 7. Check for this page

- Every row carries a file this run opened or a command it ran; the runs' own outputs are `gate1_r4.out`,
  `gate2_r4.out`, `gate4_r4.out`, `local_route_r4.out`, `pine_r4.out`, `pine_r5.out` under
  `...\workspaces\t_85c957fd\`, plus the scripts `probe_r4.py`, `probe_pal.py`, `probe_png2.py`, `probe_misc.py`,
  `board_r4.py`, `sums.py`.
- The sum is computed, not counted by hand: `sums.py` prints `rows 22 sum 57 mean 2.591` and `baseline sum 50`.
- Board statuses in section 4 come from `nayil-ops\kanban.db` read-only at 13:24 (`board_r4.py`), 85 open cards.
- This page contains 0 em dashes, 0 en dashes and 0 figure dashes; hyphens appear only in file names, card ids,
  flags and compounds.
