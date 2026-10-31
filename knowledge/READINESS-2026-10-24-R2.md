# Readiness refresh, 2026-10-23 06:17 to 06:30: the 22 row table re-measured

Written by audit for card `t_8ca7ba45` (AUTO-AUDIT-REFRESH). Every number below came from a command this run executed
on this PC between 06:17 and 06:30 Pacific, or from a file this run opened and read; worker reports, card results and
the earlier readiness pages were not accepted as evidence, and every line says which file or command produced it.

File name: `READINESS-2026-10-24.md` already exists (written 02:05 by `t_d5ecf73f`), so this refresh is a new page
beside it and that page is left untouched. The "Before" column is the baseline table `knowledge\HACKATHON-AUDIT-2026-10-22.md`
section 1; the "02:05" column is `READINESS-2026-10-24.md` section 2.

P: build exit 0 with BUILD PASS and the game ran live from it; the drive is in the .yyp and draws 12 native frames, 10 of them fully on the palette.
P: the first fight now starts in a live run and a second launch reads its save; both are proven, and both have a red gate on top of them.
P: my Pine run is 1301 passed, 12 failed, 21 skipped, 1 deselected; gate 4 is still red at 34 of 181 files.
P: one row up in four places, one row down in one, for a net +4: 53 to 57 over 22 rows, mean 2.591.
P: capture_title refused to open a window (idle gate, exit 4), so the title row keeps its 05:05 evidence and is labelled as not from this run.

## 0. The tree this run measured

    git HEAD                      12c5731 at 05:06 (DEVLOG: BATTLE-CRASH)
    git status --porcelain        674 entries, the tree is dirty and moving
    data/slice.json               a42993c7ca7245cb 1741 B, written 06:19:34, WHILE this run was measuring
    data/scenes/all.json          78390c43b363fa59 5423 B, 13 scene ids
    data/maps/all.json            8f5df49b72e6b1ff 16826 B, 4 map ids
    data/dialogue/all.json        24bb4d30a7c9595f 11036 B, 40 rows
    data/flags.json               f966238fe9a1e757 391 B, 16 flags
    data/encounters/all.json      850b911efc5d57e5 4533 B, 3 encounter ids

The movement that matters: `data/slice.json` gained `deck_save` as the `save` step's trigger at 06:19:34
(`data/slice.json` line 65), which is the exact thing the route test was failing on. My Pine zip was packed in the same
minute, so two of its red rows are a race against that write and are corrected in section 3, not counted against the tree.

## 1. The four gates, each with its own exit code from this run

1. `python tools/check_data.py`, 06:19, **exit 0**, `check_data: all files pass` (`gate1_r3.out`).
2. `python tools/check_cleanroom.py`, 06:19, **exit 0**, `check_cleanroom: no blacklist hit, but 1 of 40 modules still
   await clean-room review`, naming `game/scripts/pp_map_tile/pp_map_tile.gml` (`gate2_r3.out`). Green, with one
   unreviewed module listed rather than failed.
3. `pine_offload.py --shards 3 --name audit-r3` from `<workspace>\Shared\projects\arananet\pine`, started
   06:19 and finished 06:22, zip 33077756 bytes, 74 test files, **1301 passed, 12 failed, 21 skipped, 1 deselected** over three completed
   shards (`offload-audit-r3-0.json` 2 failed 539 passed, `-1.json` 1 failed 443 passed, `-2.json` 9 failed 319 passed).
   The 12 are `test_first_fight_capture` 5, `test_slice_route` 4, `test_project` 2, `test_no_network_in_build` 1.
4. `python tools/nes_audit_all.py`, 06:21, **exit 1**, `nes_audit_all: FAIL 181 file(s), 34 failing, 0 unmeasured`
   (`gate4_r3.out`). The 34 include `title_run_1.png`, `title_run_2.png`, `title_ui_preview.png`, all eight
   `bg_battle_*_preview.png` and `enemies_preview_3x.png`.

## 2. The 22 row table, re-measured

Scale unchanged: 0 nothing, 1 spec only, 2 code or data but unproven in the game, 3 proven in the running game with a
capture or a test, 4 polished.

| # | Subsystem | Before | 02:05 | Now | Delta | Evidence for the Now value |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Title screen | 3 | 3 | 3 | 0 | No fresh capture: `capture_title.py --idle-wait 240` was refused at 06:26 with `input 21 s ago, 120 s required` and `CAPTURE EXIT=4` (`capture_r3b.out`). On the 05:05 frames, `crop_probe.py` measures the 768x720 crop at 32 distinct RGB, 23 off palette, 10 of 61440 3x blocks not uniform. Not 4. |
| 2 | Intro crawl | 3 | 3 | 3 | 0 | `build/first_fight_game.log` line `PP title: intro finished, starting the run in rm_pp_ship`; `output\crawl_mid.png` and `crawl_end.png` 4 colours each, 1 off palette (`F9F9F9`, `png_r3.out`). |
| 3 | Drive cutscene | 1 | 2 | 3 | +1 | Twelve frames `output\drive_frames\drive_shot_01..12.png` at 256x240, written 05:05, are game-native (no scaling): `colours.py` puts 10 of 12 at 1.0000 on-palette share. `game\PrimordialParadox.yyp` names `rm_pp_drive` 4 times and my 06:19 build compiled it (`PrimordialParadox.win` 458956 B). Not 4: shots 01 and 07 are 0.1035 and 0.0081 on palette, and the route still cannot take the step (section 3). |
| 4 | Overworld movement | 3 | 3 | 3 | 0 | `build/first_fight_game.log`: footstep cues and `PP: battle start tutorial_sailors on ship_small 4,7`, so the walk reaches a trigger tile in a live run. |
| 5 | Maps and doors | 2 | 2 | 2 | 0 | `data/maps/all.json` holds 4 ids now, `southampton_town_quay` among them, and the route's arrival step resolves; no capture shows a door traversed on any map but `ship_small` (`test_slice_route` 22 of 24 checks pass, `slice_route_win.out`). |
| 6 | Dialogue and talk | 3 | 3 | 3 | 0 | `data/dialogue/all.json` 40 rows (was 35), `data/flags.json` 16 flags; no `test_dialogue*` file is among my 12 Pine reds (`pine_summary_r3.out`). |
| 7 | Battle and the talk fight | 2 | 2 | 3 | +1 | `build/first_fight_game.log` line `PP: battle start tutorial_sailors on ship_small 4,7` is a live start; `output\first_fight_verify.json` (04:49) records the battle box on 22 frames and `victory_text_in_sample ok=True` on 3 frames from `f_0100.png`. Not 4: the field draws without its strip and three roles print as missing (row 18), and the capture's own verifier is red (section 3). |
| 8 | Enemies | 2 | 2 | 2 | 0 | `output\enemies_preview_3x.png` 9 colours, 0 off palette (`png_r3.out`); the live encounter's enemy art is unmeasured because the fight grab is not a clean framebuffer (section 3). |
| 9 | Party and stats | 2 | 2 | 2 | 0 | `data/characters/party.json` only; no test names a level up (`pine_summary_r3.out` has no stats row). |
| 10 | Save and load | 2 | 2 | 3 | +1 | `output\save_capture_verify.json` `ok: true` over 15 checks: written at `PP: ship's log, deck_save, saved on ship_small 2,5`, a second launch read it, CONTINUE landed on the tile, and the slot digest `c1646e72...` is the same in both runs. `output\save_capture_landing.png` and `save_capture_log_terminal.png` are 768x720, 7 colours, 1.0000 on palette (`colours.py`). |
| 11 | Ledger | 2 | 2 | 2 | 0 | `tests\test_ledger.py` is not among the 12 Pine reds; no capture shows a ledger row. |
| 12 | Audio bus and cues | 3 | 3 | 3 | 0 | From my own build: `build/last-igor.log` lines `PP audio: title_theme streaming streams/title_theme_v3_126.ogg`, `thunder_soft played, instance 400002` through `400006`, `menu_select played`. |
| 13 | Music per scene | 2 | 2 | 2 | 0 | Per-room coverage still unmeasured: `capture_title.py` was refused this run, so the title theme is the only room whose music I have seen a line for (`build/last-igor.log`). |
| 14 | SFX | 3 | 3 | 3 | 0 | `tests\test_sfx.py` is not among the 12 Pine reds; live cue lines in `build/first_fight_game.log`. |
| 15 | UI windows and menus | 2 | 2 | 2 | 0 | `output\ui_battle_preview.png`, `ui_dialogue_preview.png`, `ui_menu_preview.png` are 5, 5 and 4 colours with 0 off palette (`png_r3.out`) and none of the three is among gate 4's 34 reds (`gate4_r3.out`), and no `test_nes_check` row is among my 12 Pine reds. Held at 2 because a preview is not a live window: the only red in this area is `output\title_ui_preview.png` (1,432,648 px, `background_area x301, palette x7`). |
| 16 | Art pipeline | 2 | 3 | 3 | 0 | Green on the reproducibility tests: no `test_look`, `test_title_art_v2`, `test_make_title_ui` or `test_scene_palette_set` row is among my 12 Pine reds (`pine_summary_r3.out`). Not 4: the live title crop still carries 23 colours off palette (row 1). |
| 17 | Sprites per character | 2 | 2 | 2 | 0 | `output\chars_contact.png` 736x2768, 22 colours, 0 off palette; `output\chars_preview_3x.png` is among gate 4's reds; `t_858c2908` still blocked on the board (`board_r3.out`). |
| 18 | Backgrounds per scene | 3 | 3 | 2 | -1 | The live fight does not draw its strip: `build/first_fight_game.log` line `PP battle: bg_battle_deck_night is not in the art index, the field draws without its strip`, and gate 4 fails all eight `bg_battle_*_preview.png` (`gate4_r3.out`). The strips exist and are drawn nowhere I can measure; 3 was the score for "drawn, not wired" and the live run says not wired. |
| 19 | Build and packaging | 3 | 3 | 3 | 0 | `python tools/integration_build.py` 06:18 to 06:20, exit 0, `BUILD PASS: Igor compiled the project and launched the game`; `output\PrimordialParadox\PrimordialParadox.win` 458956 B written 06:19, runner still the 7941704 B exe of Oct 20. No zip, no install step. |
| 20 | Tests and gates | 2 | 2 | 2 | 0 | Gate 1 green, gate 2 green, gate 3 `12 failed` of 1313 graded rows, gate 4 red on 34 of 181. The Windows/Pine split is written (`t_f64b44a4` done) and 21 skips are marked, and the gate still is not green. |
| 21 | Capture and demo tooling | 2 | 2 | 3 | +1 | `ffprobe output\demo\run_002.mp4` gives h264 768x720 60 fps with an aac track, `duration=73.500000`, 4453751 B at 01:49, and its own `output\demo\run_002_verify.json` reads `"ok": true`. `capture_title.py` itself is honest under pressure: it refused rather than reporting a pass (`capture_r3b.out`). Not 4: the fight capture's verifier returns `ok: false`. |
| 22 | Docs and repo hygiene | 1 | 2 | 3 | +1 | At the root: `README.md` 11908 B, `LICENCE` 5040 B, `CREDITS.md` 14267 B (`ls -la`, 06:24), and my build wrote `output\credits.json` 10689 B at 06:19. Not 4: `t_d71e0dda` was done but five credits URLs still carry no citation provenance in the data the build ships. |
| 23 | Slice route (carried row) | n/a | 2 | 2 | 0 | `python -m pytest tests/test_slice_route.py -q` at 06:23 is `2 failed, 22 passed`, and both reds are the drive (`slice_route_win.out`). The save step now resolves, so the route has 8 of 9 steps resolvable and still cannot be played end to end. |

Sums: 50 over 22 at the baseline (2.273), 53 at 02:05 (2.409), **57 over 22 now, mean 2.591**; with the carried route
row, 59 over 23, mean 2.565. Five rows moved up by one (3, 7, 10, 21, 22) and one moved down by one (18).

## 3. What moved, and the command or file behind each

**Row 3, the drive, 2 to 3.** `output\drive_frames\` holds `drive_shot_01.png` to `drive_shot_12.png`, 256x240 each,
all written 05:05:10, and `colours.py` reports 10 of the 12 at on-palette 1.0000 against the 113 hex values of
`data\nes_palette.json` plus `data\palette.json`. 256x240 is the framebuffer, so these are game pixels, not a scaled
screen grab. `game\scripts\pp_drive\pp_drive.gml` is 31468 B at 02:33, `game\rooms\rm_pp_drive\rm_pp_drive.yy` 6662 B
at 00:59, and the `.yyp` my build compiled names it 4 times. That is a capture of the drive in the running game.
The two off-palette shots are a real finding, not a capture fault: shot 01 spends 89.65% of its pixels on
`B8B8C4`, `C79856`, `D6B754`, `454552` and `2B2B36`, none of which is in either palette file.

**Row 7, the battle, 2 to 3.** `build\first_fight_game.log`, a 4142 B run of the built game at 04:42, carries
`PP: battle start tutorial_sailors on ship_small 4,7` followed by `encounter_swoosh played`. `output\first_fight_verify.json`
(04:49) then records `battle_box_in_sample ok=true` on 22 frames, `fight_command_in_sample ok=true`, and
`victory_text_in_sample ok=true` on 3 frames starting `f_0100.png`. The fight starts, is drawn and reaches its ending
text in the running game. What it does not have is a green artifact: see blocker 2.

**Row 10, save and load, 2 to 3.** `output\save_capture_verify.json` is `ok: true` across 15 checks, including
`the slot run 2 opened is the one run 1 wrote` with the digest `c1646e72ee6a18afbee95da2e7752bb39338cf97e4aea553d9b08864b3e7cd08`
on both sides, and `the spawn frame exists` at `1.0000 legal, 61440 of 61440 pixels are 2C02 colours`. I opened
`output\save_capture_landing.png` and `save_capture_log_terminal.png` myself: 7 colours each, 1.0000 on palette.

**Row 21, capture and demo tooling, 2 to 3.** `output\demo\run_002.mp4` is 4453751 B at 01:49, 73.5 s, 768x720 at
60 fps, h264 with aac (`ffprobe`), and `output\demo\run_002_verify.json` says `"ok": true`. The recorder that used to
answer `ok: false` on five of seven frames (row 21's old evidence, `output\demo\run_001_verify.json`) now has a
recording of its own that passes its own verifier.

**Row 22, docs and repo hygiene, 2 to 3.** Three files the baseline page said did not exist are at the root:
`README.md` 11908 B, `LICENCE` 5040 B, `CREDITS.md` 14267 B, and the in-game credits data is built.

**Row 18, backgrounds per scene, 3 to 2, the one downgrade.** The fight is live now, and the live line is
`PP battle: bg_battle_deck_night is not in the art index, the field draws without its strip`
(`build\first_fight_game.log`). Three lines under it say
`PP: role hazard is not in the room palette set deck_day, drawing it as PP_COLOUR_MISSING`, and the same for `marker`
and `marker_trail`. R48 landed the strips and the field cannot find them at play time. That is the difference between
"drawn, not wired" (3) and "not wired" (2), and it is measured, not inferred.

Two corrections to my own Pine numbers, both from the mid-run write:

- Two of the 12 Pine reds are `test_slice_route` save checks (`test_the_save_step_names_a_trigger_that_exists_on_its_map`
  and `test_a_step_resolves_the_one_id_it_names[save]`). The zip was packed in the 06:19 minute and `data/slice.json`
  gained the `deck_save` trigger at 06:19:34. Run against the current file, `pytest tests/test_slice_route.py -q` at 06:23 gives
  `2 failed, 22 passed` with only the drive red. I do not count the two save rows as tree failures.
- The Pine `test_first_fight_capture` reds (5) reproduce on Windows in the lane's own runs and are a real red in the
  current tree; they are counted.

## 4. The top five blockers to the playable slice, with the card that owns each

1. **The drive step cannot be taken, and the game says so itself.** `build\first_fight_game.log`:
   `PP title: the route's next step drive cannot be taken yet: the scene drive_to_southampton is not in data/scenes/all.json`.
   Two `test_slice_route` checks fail on the same missing row (`slice_route_win.out`). Covered by R21b DRIVE-SCENE
   `t_c27552e3` (todo, builder). Nothing else is needed: the room exists and draws.

2. **The fight has no artifact that passes its own gate.** `output\first_fight_verify.json` is `ok: false` with six of
   seven checks true; the red one is the video check (`nes_palette_ok: false`, `nes_share_min: 0.9`). I measured why
   that check cannot be trusted either way: `output\first_fight_frames\f_0096.png` is 768x720 with 859 distinct colours
   and 0.0039 on-palette share, while the save capture's 768x720 frames on the same machine carry 7 colours at 1.0000
   (`colours.py`). The fight grab is not a clean framebuffer, so the fight's colour legality is unmeasured, not failed.
   Covered by FIRST-FIGHT-LIVE `t_87ee4228` (running, testing). The 5 red `test_first_fight_capture` tests are the same
   defect as a test, and **no card on the board names them** (`board_probe2.py`): proposed card, owner testing,
   `FIGHT-CAPTURE-FRAMEBUFFER: capture the fight at 256x240 from the framebuffer, not the scaled window, and make the
   five test_first_fight_capture rows pass on the current tree`.

3. **The battle field draws without its strip and with three missing palette roles.** `build\first_fight_game.log` as
   quoted under row 18. This is the judged surface of the "talk your way through a fight" pitch and it is visibly
   wrong in the one live fight I have a log for. R48 `t_59bfc884` is done and does not cover the lookup. **No card
   mentions `art index`, `COLOUR_MISSING` or `deck_night`** (`board_probe2.py`): proposed card, owner gamedev (it is
   its room and palette spec), `BATTLE-FIELD-WIRING: the tutorial fight at ship_small 4,7 draws its strip and every
   role from one palette set, with the live log lines quoted as the acceptance`.

4. **Three red tests with no owner block an honest green gate.** `test_project::test_project_graph_matches_disk`,
   `test_project::test_generated_project_files_are_current` and
   `test_no_network_in_build::test_the_build_holds_no_endpoint_no_key_and_no_live_call` are red in my Pine run
   (`pine_summary_r3.out`). `test_project` has one blocked card, `t_c31f9295` (audit, FIX-BUILD-INPUTS-4); the other
   two names appear in no open card (`board_probe2.py`). Proposed card, owner builder: `PROJECT-GATE-RED: the two
   test_project rows and the no-network row, each green or restated with the reason`.

5. **The captured art is not uniformly legal, and only some of it is gated.** Drive shots 01 and 07 are 0.1035 and
   0.0081 on palette and nothing scans them: gate 4 covers `output\*.png` and `output\drive_frames\` is not in its 181
   files (`gate4_r3.out`). The title crop is 23 colours off palette and `title_run_1.png` is among the 34 reds while
   `output\crawl_mid.png` still carries `F9F9F9`, which is in neither palette file. R21 review `t_3cca8576` (todo,
   code-review) reviews the twelve shots against the shot list, so the two off-palette shots are **partly covered**;
   the title frame is `t_a1170172` (review). What is not covered: `output\drive_frames\` is outside the NES gate at all.
   Proposed card, owner testing: `NES-GATE-COVERAGE: the guard scans output\ and not output\drive_frames\, so two
   off-palette drive frames pass unseen; add the folder to the gate`.

Outside the top five and still true: gate 4 is red on 34 of 181 files, `t_858c2908` (four sprites) is still blocked,
`t_a3fa132a` (SHIP-DECK-MAP) is still todo, and `output\crawl_mid.png`'s `F9F9F9` shows the crawl is one colour off
the palette set it ships against.

## 5. What I could not measure, and why

- **The title capture.** `python tools/capture_title.py --idle-wait 240` waited the full 240 s and then printed
  `P: idle gate SKIPPED the launch: input 21 s ago, 120 s required, waited 240 s of 240 s, so nothing was opened` and
  `CAPTURE EXIT=4` (`capture_r3b.out`). The idle gate exists so an agent does not seize the screen while Nayil is
  typing, and I did not reach for `--force`, which the tool documents as a person-at-the-keyboard flag. Row 1 therefore
  rests on the 05:05 frames and says so.
- **The drive from the route.** The frames prove the room runs; no run reaches it through `data/slice.json`, because of
  blocker 1.
- **The fight's colour legality.** The only fight grab is a scaled window, so its palette share measures the capture
  path, not the game (blocker 2).
- **The full Windows suite.** I did not run `pytest tests` on this PC; the card orders Pine, and the Pine numbers are
  the gate's. The two files Pine does not offload (`test_build_inputs`, `test_test_inputs`, plus `test_sync_art`) are
  unmeasured by me this run and are named as such.

## 6. Q: for gamedev

One question, because it is a spec decision and not mine to make. The tutorial fight at `ship_small 4,7` logs
`bg_battle_deck_night is not in the art index` while the room's palette set is `deck_day`
(`build\first_fight_game.log`). Which is the contract: does that fight draw the `deck_night` strip and take the
`deck_night` palette roles (`hazard`, `marker`, `marker_trail`), or is the room meant to be `deck_day` and the strip
name is the error? I have scored row 18 down to 2 on the log line alone and will move it back the moment the live run
draws a strip.

## 7. Check for this page

- Every changed score carries a command or a file this run read: rows 3, 7, 10, 21, 22 up and row 18 down, each with
  the file, the byte count or the log line named in section 3.
- The four gates carry their own exit codes from this run's output under
  `...\workspaces\t_8ca7ba45\`: `gate1_r3.out`, `gate2_r3.out`, `pine_summary_r3.out`, `gate4_r3.out`, plus
  `build_r3.out`, `capture_r3b.out`, `png_r3.out`, `slice_route_win.out`, `data_probe_r3.out`, `board_r3.out`,
  `board_probe2.py`, `colours.py`, `crop_probe.py`. That workspace is scratch and may be pruned, so every number also
  carries the command that reproduces it from the repository alone.
- Two of my own numbers are corrected rather than reported as the tree's fault (section 3), because the zip was packed
  one second before `data/slice.json` changed.
- The board statuses in sections 3 and 4 were read from `kanban.db` read-only at 06:27 (`board_r3.out`,
  `board_probe2.py`).
- A read of this file finds 0 em dashes, 0 en dashes and 0 figure dashes; the hyphens that remain are inside file names,
  card ids, command flags and the compounds `end to end`, `clean-room` and `on-palette`.
