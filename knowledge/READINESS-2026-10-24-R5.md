# Readiness refresh 5, 2026-10-24 05:04 to 05:15: the 22 row table re-measured

Written by audit for card `t_2b59696a` (AUTO-AUDIT-REFRESH). Every number below came from a command this run executed on
this PC between 05:04 and 05:15 Pacific, or from a file this run opened. Worker reports, card results, `GATE-GREEN-2026-10-24.md`
and the five earlier readiness pages were not accepted as evidence. The earlier pages are left untouched; this is a new page.

P: the 22 row table sums to 57 again, mean 2.591, the same total as the 06:30, 13:07 and 21:41 pages. No score moved.
P: my build passed and ran the game live 05:05 to 05:07 from HEAD 23acab0, and the title capture passed at 05:08.
P: the Pine suite grew from 4 reds at 04:49 to 21 reds on the same tree, and 19 of those 21 pass on Windows in this run.
P: the cause of that jump is a Windows-only import at module level, not 19 defects: `tools/play_demo.py:58` imports
   `capture_title`, which imports `ctypes.wintypes` at line 39, so on Linux every test that imports it fails at import.
P: the two `test_project` reds that blocked the 21:41 page are green now; the remaining build-input red names 8 streams
   that the commit does not carry, the first `datafiles/streams/percy_theme_v2.ogg`.

## 0. The tree this run measured

    git HEAD                      23acab0 at 04:54:07 (PP FIX-YYP-8: list pp_03_harbor_v3.ogg and pp_arrival_v2.ogg in the yyp)
    git status --porcelain         743 entries, dirty
    game/rooms                     rm_pp_boot, rm_pp_drive, rm_pp_ship, rm_pp_title (4)
    data/slice.json                1741 B b54970a2f7270834, 9 route steps (title, crawl, drive, arrival, gate,
                                   boarding, fight, save, gameover)
    data/scenes/all.json           5423 B 5e1c9a63c82776cb, 13 scene ids, no drive_to_southampton
    data/maps/all.json             16826 B b52bcf7186e3b466
    data/dialogue/all.json         11547 B 9f8f00fbf27b8a12
    data/scene_palettes.json       24192 B 6203f0c7d6971dbb, no drive entry
    data/characters/party.json     295 B afffdde3f5a220bc, unchanged since 10-19 18:47
    data/nes_palette.json          13183 B a0b761011cc88cc4, 64 hex values, 55 distinct RGB
    game/datafiles/sfx/sfx.json    5089 B 9bb2ff86e7d1ac88, rewritten 05:03
    README.md 11908 B 10-23 03:13, LICENCE 5040 B 10-23 02:21, CREDITS.md 14394 B 10-23 06:48 (all at the root)
    output/PrimordialParadox/PrimordialParadox.win   459724 B written 05:05:10 by my build

All from `probe_r7.py` and `inspect_r7.py`, output in `probe_r7.out` and `inspect_r7.out`.

## 1. The build, and the game it launched

`python tools/integration_build.py` started 05:04:52, `.win` written 05:05:10, and at 05:07:28 it printed
**`BUILD PASS: Igor compiled the project and launched the game`** (`build_r7.log`), with `build/last-build-error.log`
at 0 B. The game ran as `Runner.exe` pid 33820 from 05:05:10 (`tasklist`), the live log reached `rm_pp_title` and the
main loop, and `taskkill /PID 33820` with no force flag closed it; the process was gone on the next check and the build
returned its PASS line (`build_r7.log`, `build/last-build.log`).

Live lines this run, from `build/last-igor.log` (135 lines):
`PP audio: title_theme streaming streams/title_theme_v3_126.ogg, instance 400001, gain 0.70`,
`PP audio: car_engine_loop silent, not in sfx/sfx.json`,
`PP title: room rm_pp_title live, screen owned by obj_pp_title`,
`PP: save read and accepted`, and `thunder_soft played` **11 times** (instances 400002 to 400012), the same rate as the
21:01 run and nothing like the 435 of 13:01.

## 2. The four gates, each from this run's own output

1. `python tools/check_data.py` 05:06, **exit 0**, `check_data: all files pass` (`gate1_r7.out`).
2. `python tools/check_cleanroom.py` 05:06, **exit 0**, `check_cleanroom: no study reference, no foreign name, no
   foreign phrase, every module reviewed` (`gate2_r7.out`).
3. Pine suite at 05:05, zip 34,771,551 B, 76 files, 3 shards: **955 passed, 21 failed over 2 completed shards, and
   shard 2 did not run**. `offload-audit-r7b-0.json` is `SUMMARY passed=418 failed=8` (7 in
   `tests/test_first_fight_capture.py`, 1 in `tests/test_title_art_v2.py`), `offload-audit-r7b-1.json` is
   `SUMMARY passed=537 failed=13` (10 `test_play_demo`, 1 `test_intro`, 1 `test_make_env_ship`, 2 the drive route
   rows). `offload-audit-r7b-2.json` is `status error`, `PineCallError: pine write_file failed: ConnectionError
   [Errno 10054] ... op=PUT /v1/sessions/main/files`, which is a transport failure and not a verdict. A first attempt
   at 05:05 (`audit-r7`) produced three `PineConfigError` rows instead, because the Hermes venv python cannot import
   the SDK; the run above used `<home>\AppData\Local\Python\bin\python`, the interpreter that can
   (`pine_offload.py:17` names it).
4. `python tools/nes_audit_all.py` 05:08, **exit 1**, `nes_audit_all: FAIL 184 file(s), 34 failing, 0 unmeasured`
   (`gate4_r7.out`). Same 34 count as 21:04, and `output/drive_gantry_preview.png` is again the only drive file in
   the scan (`FAIL frame ... 2 px background_area x1`). `output/drive/` (16 PNG) and `output/drive_frames/` (12 PNG)
   are still not in the 184.

Local runs beside the Pine ones, this PC, this run:

- `python -m pytest tests/test_make_title_ui.py tests/test_title_art_v2.py tests/test_look.py
  tests/test_scene_palette_set.py tests/test_nes_check.py tests/test_project.py -q` finished 05:07 with **1 failed, 118
  passed in 26.60 s** (`local_art_r7.out`), and the single red is `test_project.py::test_build_inputs_are_committed`
  with `MISSING FROM COMMIT datafiles/streams/percy_theme_v2.ogg` and 7 more. The two reds the 21:41 page named,
  `test_project_graph_matches_disk` and `test_generated_project_files_are_current`, are green.
- `python -m pytest tests/test_slice_route.py -q` finished 05:06 with **2 failed, 22 passed in 0.59 s**
  (`local_route_r7.out`), both reds the `[drive]` rows.
- `python -m pytest tests/test_play_demo.py tests/test_intro.py tests/test_make_env_ship.py -q` finished 05:10 with
  **41 passed in 3.59 s** (`local_demo_r7.out`): the 12 Pine reds in those three files do not reproduce on Windows.
- `python -m pytest tests/test_first_fight_capture.py tests/test_title_art_v2.py -q` finished 05:12 with **18 passed in
  9.57 s** (`local_fightcap_r7.out`): the 8 Pine reds in those two files do not reproduce either.
- `python tools/capture_title.py` 05:07:59 to 05:08:09, **exit 0**, `output/title_run_1.png` and `_2.png` 784x759,
  `viewport ... score 1.000`, `the game closed on request (exit code 0)` (`capture_title_r7.out`).

## 3. The 22 row table

Scale unchanged: 0 nothing, 1 spec only, 2 code or data but unproven in the game, 3 proven in the running game with a
capture or a test, 4 polished. Base is the table in `HACKATHON-AUDIT-2026-10-22.md` section 1.

| # | Subsystem | Base | 02:05 | 06:30 | 13:07 | 21:41 | Now | Evidence for the Now value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Title screen | 3 | 3 | 3 | 3 | 3 | 3 | Fresh capture 05:08, exit 0, `output/title_run_1.png` 784x759 written 05:08:01, viewport [8,31,768,720] `score 1.000` (`capture_title_r7.out`). The viewport crop is 38 colours at **0.9999** on the 55 colour master with **28 blended colours** (`title_crop_r7.py`), and `python tools/nes_check.py output/title_run_reference_3x.png --type background` is **FAIL 31 problem(s)** (`nes_title_r7.out`), exactly the 21:08 reading. The committed native frame still carries 11 colours at 1.0000 (`nes_title_r7.out` on `output/nes_title_frame.png`, PASS) but its file date is 10-21 22:01, before the 20:16 sprite rewrite. Not 4 on either number. |
| 2 | Intro crawl | 3 | 3 | 3 | 3 | 3 | 3 | `output/crawl_mid.png` 768x720, 4 colours at 0.9667 with 1 off-palette colour, `crawl_end.png` 4 at 0.9619 (`png_r7.out`); both files are 10-22 07:57 and were not re-shot this run. Route step `crawl` resolves (22 passed in `local_route_r7.out`). |
| 3 | Drive cutscene | 1 | 2 | 3 | 3 | 3 | 3 | `rm_pp_drive` exists in a 4 room build that compiled and ran (`probe_r7.out`, `build_r7.log`). The 12 frames are in `output/drive/pp_drive_shot_01..12.png` 768x720 and their downscales in `output/drive_frames/drive_shot_01..12.png` 256x240. Palette legality, per shot, measured against the 55 RGB of `data/nes_palette.json`: **0.0000 to 0.0167** (`png_r7.out`), shot 01 at 0.0000 with `08131F` 45.1 pct, `1B1B22` 34.4 pct, `0B0B0F` 10.3 pct, and the whole drive 11 of 12 shots under 2 pct. The single legal file is the auxiliary `output/drive/pp_drive_shot_03_1x_ppu.png` at 1.0000, shot 03 only. `data/scene_palettes.json` holds no drive entry (`inspect_r7.out`), and the route cannot take the step (`local_route_r7.out`), so not 4. |
| 4 | Overworld movement | 3 | 3 | 3 | 3 | 3 | 3 | No live evidence from my build: the log reaches `rm_pp_title` and the main loop and no further (`build/last-igor.log`). Carried from `output/demo/run_002_verify.json` and the earlier fight logs and labelled as carried, not re-measured. |
| 5 | Maps and doors | 2 | 2 | 2 | 2 | 2 | 2 | `data/maps/all.json` 16826 B; the `arrival` and `gate` route steps resolve (`local_route_r7.out`); `rm_pp_ship` is the only room with a walkable map and no door traversal is captured. |
| 6 | Dialogue and talk | 3 | 3 | 3 | 3 | 3 | 3 | `data/dialogue/all.json` 11547 B; `tests/test_dialogue_choice_layout.py` is in Pine shard 0, which is 418 passed with 8 reds, none of them this file (`offload-audit-r7b-0.json`). |
| 7 | Battle and the talk fight | 3 | 2 | 3 | 3 | 3 | 3 | Carried, not re-earned: `output/first_fight_verify.json` `"ok": true` and `output/first_fight_capture.mp4` 2237724 B at 10-23 04:42, with 123 frames in `output/first_fight_frames/`; no new capture exists since (`probe_r7.out`). The 7 reds in `tests/test_first_fight_capture.py` on Pine are green on Windows (`local_fightcap_r7.out`, 18 passed). Not 4: the art defects behind row 18 survive. |
| 8 | Enemies | 2 | 2 | 2 | 2 | 2 | 2 | `output/enemies_preview_3x.png` 464x772, 9 colours, 1.0000 on master (`png_r7.out`); no enemy inside a live fight is captured. |
| 9 | Party and stats | 2 | 2 | 2 | 2 | 2 | 2 | `data/characters/party.json` 295 B, one hero row, last written 10-19 18:47 (`probe_r7.out`, `inspect_r7.out`); no open card on the board names party or stats (`board_r7.out`). |
| 10 | Save and load | 3 | 2 | 3 | 3 | 3 | 3 | `output/save_capture_verify.json` `"ok": true` at 03:43, and this run's live log prints `PP: save read and accepted` (`build/last-igor.log`). The two landing frames are legal: `save_capture_landing.png` and `save_capture_log_terminal.png` 768x720, 7 colours, 1.0000 each (`png_r7.out`). |
| 11 | Ledger | 2 | 2 | 2 | 2 | 2 | 2 | `tests/test_ledger.py` sits in Pine shard 0, whose 8 reds do not include it (`offload-audit-r7b-0.json`); still no capture of a ledger row read back, and no open card names the ledger (`board_r7.out`). |
| 12 | Audio bus and cues | 3 | 3 | 3 | 3 | 3 | 3 | Live this run: `PP audio: title_theme streaming streams/title_theme_v3_126.ogg, instance 400001, gain 0.70` and `PP audio: focus lost, music paused (cue and theme) and every effect stopped` (`build/last-igor.log`). |
| 13 | Music per scene | 2 | 2 | 2 | 2 | 2 | 2 | My live log names the title theme only, so per-room coverage stays unproven in the game (`build/last-igor.log`). |
| 14 | SFX | 3 | 3 | 3 | 3 | 3 | 3 | Live cues this run (`thunder_soft` 11 times, instances 400002 to 400012, `build/last-igor.log`). Still not 4: `game/datafiles/sfx/sfx.json`, rewritten today at 05:03, holds **0** occurrences of `car_engine`, and the live log still prints `PP audio: car_engine_loop silent, not in sfx/sfx.json`. |
| 15 | UI windows and menus | 2 | 2 | 2 | 2 | 2 | 2 | `ui_battle_preview.png` 5 colours 1.0000 and `ui_dialogue_preview.png` 5 colours 1.0000 (`png_r7.out`), but `title_ui_preview.png` is 1920x784 at **0.0110** with 7 off-palette colours, and gate 4 fails it plus the four `bg_battle_*_text_preview` and four `bg_battle_*_fight_preview` frames (`gate4_r7.out`). A preview is not a live window. |
| 16 | Art pipeline | 2 | 3 | 3 | 3 | 3 | 3 | Re-earned on Windows this run: the art and project set is 118 passed, 1 failed, and the one red is `test_build_inputs_are_committed`, a git commit test, not an art check (`local_art_r7.out`). `tests/test_title_art_v2.py::test_the_two_busts_regenerate_from_the_committed_tree` is red on Pine and green on Windows (`local_fightcap_r7.out`). Not 4: the pipeline's own drive output is the off-palette art in row 3. |
| 17 | Sprites per character | 2 | 2 | 2 | 2 | 2 | 2 | `output/chars_contact.png` 736x2768, 22 colours, 1.0000 (`png_r7.out`), but files dating to 10-22 02:40 and no capture naming a character sprite in the running game; card `t_858c2908` is still blocked (`board_r7.out`). |
| 18 | Backgrounds per scene | 2 | 3 | 2 | 2 | 2 | 2 | `output/bg_battle_preview.png` 16 colours at 1.0000 (`png_r7.out`), and gate 4 fails all eight `bg_battle_*_text_preview` and `_fight_preview` frames at 3 to 7 background-area violations each (`gate4_r7.out`). My build reaches no battle, so this is carried, not re-measured. |
| 19 | Build and packaging | 3 | 3 | 3 | 3 | 3 | 3 | My build 05:04:52 to 05:07:29, `.win` 459724 B at 05:05:10, **`BUILD PASS`**, exit 0, game live 05:05:10 to 05:07:28 as `Runner.exe` and closed with a graceful `taskkill` (`build_r7.log`, `build/last-build.log`). Not 4: no zip, no install step, and the runner is still the 7941704 B exe of 10-20. |
| 20 | Tests and gates | 2 | 2 | 2 | 2 | 2 | 2 | Gate 1 exit 0, gate 2 exit 0, gate 4 exit 1 on 34 of 184 (`gate1_r7.out`, `gate2_r7.out`, `gate4_r7.out`); Pine **955 passed, 21 failed over 2 of 3 shards**, shard 2 a transport error (`offload-audit-r7b-*.json`); local 118/1, 22/2, 41/0, 18/0 (`local_art_r7.out`, `local_route_r7.out`, `local_demo_r7.out`, `local_fightcap_r7.out`). 19 of the 21 Pine reds pass on Windows, 2 are real, and the gate still cannot be read as green. |
| 21 | Capture and demo tooling | 3 | 2 | 3 | 3 | 3 | 3 | `tools/capture_title.py` passes end to end at 05:08, exit 0, two frames, `the game closed on request (exit code 0)` (`capture_title_r7.out`). Not 4: no new video since 10-23 01:49, `output/demo/run_003*` does not exist, and `output/demo/run_002_verify.json` still says `audio: rendered stand-in from run_002_audio.m4a, not the game's live output`. The 10 `test_play_demo` reds on Pine are green on Windows (`local_demo_r7.out`). |
| 22 | Docs and repo hygiene | 2 | 3 | 3 | 3 | 3 | 3 | Root `README.md` 11908 B 10-23 03:13, `LICENCE` 5040 B 10-23 02:21, `CREDITS.md` 14394 B 10-23 06:48, each opened this run (`probe_r7.out`). The README's own state table is 10-22 vintage and stale against this page. |

Rows 22, sum **57**, mean **2.591**; the 02:05 page was 53, the 06:30 page 57, the 21:41 page 57, and the baseline is 50
as the 02:05 page re-based row 22's base from 1 to 2 (`sums_r7.py` prints all six columns). The 10-22 audit table alone
sums to 49 with row 22 at 1; the difference is that one re-base, not a movement.

## 4. What moved, and what did not, with the command behind each

No score moved for the fourth page in a row. Five things changed under the scores:

- **The Pine gate went from 4 reds to 21, and 19 of them are a Windows import.** `offload-audit-r7b-0.json` 418 passed
  8 failed, `-1.json` 537 passed 13 failed, against 1325 passed 4 failed in the 04:44 run
  (`GATE-GREEN-2026-10-24.md`). The new reds are 10 `test_play_demo`, 7 `test_first_fight_capture`, 1 `test_intro`,
  1 `test_make_env_ship`, 1 `test_title_art_v2`, and this run measured all 19 green on Windows
  (`local_demo_r7.out` 41 passed, `local_fightcap_r7.out` 18 passed). The mechanism is at the top of the import chain:
  `tools/play_demo.py:58` does `import capture_title as cap`, and `tools/capture_title.py:39` does
  `import ctypes.wintypes as wt`, which cannot import on Linux. `tests/test_first_fight_capture.py:24` names the same
  chain for its own tool. So the Pine number is a platform artefact here, and the honest count of real reds on this
  tree is 2 (the drive route rows).
- **The two `test_project` reds are green and the build-input red changed shape.** At 21:41 three `test_project` rows
  were red; now `test_graph_matches_disk` and `test_generated_project_files_are_current` pass on Windows and the only
  red is `test_build_inputs_are_committed`, naming 8 streams that the commit does not carry, first
  `MISSING FROM COMMIT datafiles/streams/percy_theme_v2.ogg` (`local_art_r7.out`). Card `t_c31f9295` names four
  untracked audio sources and is blocked, so the count in that card and the count here disagree.
- **The drive is unchanged and still illegal.** 12 of 12 shots 0.0000 to 0.0167 legal, no drive palette set, route
  step red (`png_r7.out`, `inspect_r7.out`, `local_route_r7.out`). The Q card `t_f034f9d0` from 21:18 is still
  blocked and no gamedev decision page answers it: `knowledge/GAMEDEV-DECISIONS-2026-10-23.md:45` mentions the drive
  only to score it at 1 of 4.
- **The drive is silent after an sfx rewrite.** `game/datafiles/sfx/sfx.json` was rewritten at 05:03 (5089 B) and still
  holds 0 occurrences of `car_engine`; `data/audio.json` 0 as well, and the live 05:05 log prints
  `PP audio: car_engine_loop silent, not in sfx/sfx.json` (`probe_r7.out`, `build/last-igor.log`).
- **The fresh title is legal-looking and still not legal.** 38 colours at 0.9999 with 28 blended colours and
  `nes_check ... FAIL 31 problem(s)` on the 3x reference, while the committed native frame PASSes at 11 colours but is
  10-21 (`title_crop_r7.py`, `nes_title_r7.out`, `nes_native_r7.out`).

## 5. The top five blockers to the playable slice, with the card that owns each

1. **The drive step cannot resolve, and the scene has no palette set.** `local_route_r7.out` is 2 failed, 22 passed
   with both reds naming `drive_to_southampton`; `data/scenes/all.json` holds 13 scene ids and none is the drive; and
   all 12 captured shots are outside the 2C02 palette (`probe_r7.out`, `png_r7.out`). Covered: `t_c27552e3` R21b
   DRIVE-SCENE (builder, todo, priority 98), `t_ff5a3714` SLICE-ROUTE-DATA (gamedev, todo), `t_3cca8576`
   REVIEW-R21-DRIVE (code-review, todo). Uncovered: the palette set, which RULE 0 point 1 of `ART-BIBLE.md:283`
   makes a spec. Proposed card, owner gamedev: `DRIVE-PALETTE-SET: a drive scene palette set in
   data/scene_palettes.json plus 12 of 12 shots inside it, with the measured legal fraction per shot as the acceptance`.
   The question is already asked as `t_f034f9d0` and still unanswered.
2. **The build input gate is red on 8 streams the commit does not carry.** `local_art_r7.out`:
   `['MISSING FRO..._v6.ogg', ...]`, first extra `MISSING FROM COMMIT datafiles/streams/percy_theme_v2.ogg`, 8 rows.
   `t_c31f9295` (audit, blocked, priority 90) names four untracked audio sources in three directories, a different
   count from today's 8. Proposed card, owner builder: `BUILD-INPUTS-8: the 8 streams test_build_inputs_are_committed
   names are in the commit, or each is restated with the reason it stays out`.
3. **The Pine gate is unreadable: 21 reds, 19 of them a Linux import failure.** `offload-audit-r7b-0.json` and
   `-1.json` against `local_demo_r7.out` and `local_fightcap_r7.out`, with the cause at `tools/play_demo.py:58` and
   `tools/capture_title.py:39`. No open card names the platform split: `t_030a89e5` R32 (testing, blocked) is the
   route only, and `GATE-GREEN-2026-10-24.md` is the testing lane's own report of 2 reds. Proposed card, owner
   testing: `PINE-IMPORT-SPLIT: tests that import tools/play_demo or tools/capture_first_fight are deselected on Pine
   with the reason printed, as test_project and test_sync_art already are, so the Pine count is a defect count`.
4. **The judged video's audio is a rendered stand-in and the video is 28 hours old.**
   `output/demo/run_002_verify.json` says `"ok": true` with `audio: rendered stand-in from run_002_audio.m4a, not the
   game's live output`, `output/demo/run_002.mp4` is 10-23 01:49 and no `run_003*` exists (`probe_r7.out`). No open
   card owns the recorder (`board_r7.out`; `t_030a89e5` is the route). Proposed card, owner testing:
   `DEMO-AUDIO-LIVE: one recorded run whose audio track is the game's own output, with the verifier's audio field
   reading live and not stand-in`.
5. **The drive plays silent and no card owns the sound.** `car_engine` appears 0 times in
   `game/datafiles/sfx/sfx.json` (rewritten 05:03) and 0 times in `data/audio.json`, and the live log prints
   `PP audio: car_engine_loop silent, not in sfx/sfx.json` (`build/last-igor.log`, 109 style line this run at the
   title). The drive is the pitch's signature scene. Proposed card, owner musician: `DRIVE-ENGINE-LOOP:
   car_engine_loop in game/datafiles/sfx/sfx.json with a cue, and the live log stops printing "silent, not in
   sfx/sfx.json"`.

Outside the five and still true: gate 4 red on 34 of 184 with the drive frames outside the scan (`gate4_r7.out`);
`output/title_ui_preview.png` 1920x784 at 0.0110 (`png_r7.out`); `crawl_mid.png` and `crawl_end.png` each carry 1
off-palette colour; party stats and the ledger have no card at all (`board_r7.out`); the committed native title frame
is 10-21 and older than the sprite rewrite it is supposed to show.

## 6. What I could not measure, and why

- **A live battle and a live overworld walk.** My build ran 05:05 to 05:07 and the log stops in the title room
  (`build/last-igor.log`). Rows 4, 7 and 18 are carried and say so.
- **The third Pine shard.** `offload-audit-r7b-2.json` is `PineCallError: ... ConnectionError [Errno 10054] ... op=PUT
  /v1/sessions/main/files`. That shard held 370 passed 2 failed at 21:01 and this run has no number for it, so 955
  passed is a partial total, not the suite.
- **The three Windows-only suite files.** `tests/test_build_inputs.py` ran inside `local_art_r7.out`; `test_test_inputs.py`
  and `test_sync_art.py` were not run by this run.
- **A pixel diff of the 20:16 title sprite rewrite.** The capture is live but I did not compare it against the sources,
  and the committed native frame predates it.

## 7. Q: for gamedev

1. The drive's palette, carried from 21:18 and still unanswered on card `t_f034f9d0`: is the drive meant to be a graded,
   non-NES look (then `ART-BIBLE.md` needs that ruling written in, because RULE 0 point 1 requires a palette set per
   scene), or is it meant to be quantized like the rest, with `output/drive/pp_drive_shot_03_1x_ppu.png` (7 colours,
   1.0000) as the pattern for all twelve?
2. The build-input red: is `datafiles/streams/percy_theme_v2.ogg` and the 7 with it meant to be committed, or are the
   streams generated and the gate's input list should exclude them? That is a spec call about what the repo carries,
   not mine.

## 8. Check for this page

- Every row carries a file this run opened or a command it ran. This run's own outputs are `probe_r7.out`,
  `inspect_r7.out`, `png_r7.out`, `title_crop_r7.out` (printed by `title_crop_r7.py`), `build_r7.log`, `gate1_r7.out`,
  `gate2_r7.out`, `gate4_r7.out`, `local_route_r7.out`, `local_art_r7.out`, `local_demo_r7.out`,
  `local_fightcap_r7.out`, `capture_title_r7.out`, `nes_title_r7.out`, `nes_native_r7.out`, `board_r7.out`,
  `sums_r7.stdout`, all under
  `<agent-runtime>\kanban\boards\nayil-ops\workspaces\t_2b59696a\`.
- The Pine evidence is `offload-audit-r7b-0.json`, `-1.json` and `-2.json` under
  `<workspace>\Shared\projects\arananet\pine\data\results\`, read by `pine_read_r7.py`.
- `sums_r7.py` (output in `sums_r7.stdout`) prints base 49 with row 22 at 1 as the 10-22 audit table scores it, 50 with
  row 22 re-based to 2 as the 02:05 page did, 0205 53, 0630 57, 1307 57, r4 57, now 57, and
  `rows that moved vs the 21:41 page: []`.
- Board statuses in section 5 come from `nayil-ops\kanban.db` opened read-only at 05:10 (`board_r7.py`): 1425 tasks,
  89 open, 65 blocked, 2 ready, 2 running.
- Side effects to declare, all of them what the tools write on every run: `python tools/nes_audit_all.py` rewrote
  `knowledge/NES-AUDIT.md`, the per-file reports under `output/nes_audit/` and `output/nes_audit_worst_3x.png`;
  `capture_title.py` rewrote `output/title_run_1.png`, `_2.png` and `output/title_run_reference_3x.png`; the Pine tool
  wrote its three result JSON files. Nothing in `data/`, `game/` or `tests/` was written by this run.
- This page contains 0 em dashes, 0 en dashes and 0 figure dashes; hyphens appear only in file names, card ids, flags
  and compounds.
