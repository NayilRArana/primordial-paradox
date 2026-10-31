# Readiness refresh 6, 2026-10-24 13:08 to 13:30: the 22 row table re-measured

Written by audit for card `t_c5b00165` (AUTO-AUDIT-REFRESH). Every number below came from a command this run executed on
this PC between 13:08 and 13:30 Pacific, or from a file this run opened. Worker reports, card results,
`GATE-GREEN-2026-10-24-1047.md` and the six earlier readiness pages were not accepted as evidence. The earlier pages are
left untouched; this is a new page.

P: the 22 row table sums to 57 again, mean 2.591, the same total as the 06:30, 13:07, 21:41 and 05:15 pages. No score moved, fifth page in a row.
P: my build passed and ran the game live from HEAD e8d7a2a: `.win` 459724 B at 13:09, `BUILD PASS` and exit 0 by 13:14, game closed cleanly.
P: the Pine suite is 1324 passed, 3 failed over all three shards, against 21 failed over two shards at 05:15; the 19 Windows-import reds are gone.
P: the 3 remaining Pine reds are 2 `test_slice_route[drive]` rows and 1 new one, `test_project.py::test_no_em_or_en_dashes_anywhere`.
P: on Windows the reds are 8, and 5 of them are one cause: the title theme v7 and v8 sources are on disk, in neither the commit nor the yyp.
P: the title capture was refused five times by the idle gate (last input 6 s, 27 s, 56 s, 66 s and 89 s before), so row 1 is carried from 05:08, not re-shot.

## 0. The tree this run measured

    git HEAD                       e8d7a2a at 11:43:22 (CI-METHOD: the staged_check key, and why a check that reads the worktree cannot judge a commit)
    git status --porcelain         787 entries, dirty
    game/rooms                     rm_pp_boot, rm_pp_drive, rm_pp_ship, rm_pp_title (4)
    data/slice.json                1741 B 2026-10-23 06:19, sha a42993c7ca7245cb, 9 route steps (title, crawl, drive, arrival,
                                   gate, boarding, fight, save, gameover)
    data/scenes/all.json           5423 B 2026-10-23 08:13, sha 78390c43b363fa59, 13 scene ids, no drive_to_southampton
    data/scene_palettes.json       24192 B 2026-10-22 22:54, sha 74e9807fe9aa4cde, 12 entries, no drive entry
    data/maps/all.json             16826 B 2026-10-23 02:19, sha 8f5df49b72e6b1ff
    data/dialogue/all.json         11547 B 2026-10-23 07:11, sha fcbe450b94f4b60c
    data/characters/party.json     295 B 2026-10-19 18:47, sha 792079001e701035, unchanged since 10-19
    data/nes_palette.json          13183 B 2026-10-21 19:25, sha 2fba4fddd1bc7416, 55 distinct usable RGB
    game/datafiles/sfx/sfx.json    5089 B 2026-10-24 12:21, sha 80a2d1e31f4ce2a8, 0 occurrences of car_engine
    README.md                      12887 B 2026-10-24 11:18, sha da4acb95e59775ca
    LICENCE                        5040 B 2026-10-23 02:21, sha b48d6fe2a0dbfe0b
    CREDITS.md                     14394 B 2026-10-23 06:48, sha 7287c6f3ecb504aa

All from `probe_r8.out`, `data_r8.out`, `dash_r8.out` and `inputs_r8.out` in this run's workspace.

## 1. The build, and the game it launched

`python tools/integration_build.py` started 13:09, wrote `output/PrimordialParadox/PrimordialParadox.win` at 13:09
(459724 B, sha256 1655afba382baa5741ab3553af452c62a9519eb5fa38a9f6b7422f8dfbbf93bb) and printed
**`BUILD PASS: Igor compiled the project and launched the game`** with `EXIT=0` at 13:14 (`build_r8.log`), after
`taskkill /PID 29316` sent a plain termination signal to the game window. `Igor finished. The game window is the only
window that opened` is the line before the PASS.

Live lines from `build/last-igor.log` (136 lines), this run:

    PP audio: title_theme streaming streams/title_theme_v3_126.ogg, instance 400001, gain 0.70
    PP audio: car_engine_loop silent, not in sfx/sfx.json
    PP title: room rm_pp_title live, screen owned by obj_pp_title
    Entering main loop.
    PP audio: focus lost, music paused (cue and theme) and every effect stopped
    PP: save read and accepted, music
    PP audio: focus back, music resumed where it stopped
    PP audio: thunder_soft played, instance 400002 ... 400012 (11 lines)

No process was left behind: `tasklist` after the close showed no `Runner.exe` and no `Igor.exe`.

## 2. The gates, each from this run's own output

1. `python tools/check_data.py`, **exit 0**, `check_data: all files pass` (`gate1_r8.out`).
2. `python tools/check_cleanroom.py`, **exit 0**, `check_cleanroom: no study reference, no foreign name, no foreign
   phrase, every module reviewed`, with 121 OSM place names exempt as declared (`gate2_r8.out`).
3. Pine suite at 13:09, zip 35105633 B, 76 files, 3 shards, all three completed (`pine_r8.log`):
   **418 passed 0 failed**, **537 passed 2 failed**, **369 passed 1 failed**, that is **1324 passed, 3 failed**.
   Walls 214.2 s, 96.0 s, 127.6 s (`offload-audit-r8-0.json`, `-1.json`, `-2.json` in
   `<workspace>\Shared\projects\arananet\pine\data\results\`, read by `pine_read_r8.py`).
   Three nodes were deselected on the far side as declared in `pine_offload.py`: `test_project_graph_matches_disk`
   and `test_generated_project_files_are_current` (both need 30 stream sources the zip cannot carry) and
   `test_mix_check_v3.py::test_the_script_still_runs_on_a_slice` (needs a 22 MB render pair).
4. `python tools/nes_audit_all.py`, **exit 1**, `nes_audit_all: FAIL 184 file(s), 34 failing, 0 unmeasured`
   (`gate4_r8.out`). The 34 include `output/title_ui_preview.png` 1920x784 `background_area x301, palette x7`, all
   four `bg_battle_*_text_preview` and all four `bg_battle_*_fight_preview` frames, and
   `output/drive_gantry_preview.png` as the only drive file in the scan, at `2 px background_area x1`.

Local Windows runs beside them, this run:

- `python -m pytest tests/test_make_title_ui.py tests/test_title_art_v2.py tests/test_look.py
  tests/test_scene_palette_set.py tests/test_nes_check.py -q` finished in 22.25 s with **96 passed, 0 failed**
  (`local_art_r8.out`): the whole art set is green on Windows, where 05:15 measured 118 passed 1 failed with
  `test_project.py` in the same command.
- `python -m pytest tests/test_slice_route.py -q`: **2 failed, 22 passed in 1.18 s**, both reds the `[drive]` rows
  (`local_route_r8.out`).
- `python -m pytest tests/test_project.py -q`: **4 failed, 19 passed in 2.42 s** (`local_project_r8.out`).
- `python -m pytest tests/test_build_inputs.py tests/test_test_inputs.py tests/test_sync_art.py -q`:
  **2 failed, 26 passed in 5.05 s** (`local_winonly_r8.out`), both reds in `test_build_inputs.py`.

So the Windows red count on this tree is **8**, and they are three causes, not eight defects (`inputs_r8.out`):

- **Two reds, the drive route step.** `test_slice_route.py::test_a_step_resolves_the_one_id_it_names[drive]` and
  `[drive]::test_a_scene_step_reaches_end_with_only_known_commands`. Known, carded.
- **Five reds, the title theme v7 and v8 sources.** `check_project.check` returns exactly two lines,
  `game/datafiles/streams/pp_01_title_v7.ogg is not listed as an Included File` and the same for `_v8`;
  `check_build_inputs.check` returns exactly two, `UNCOMMITTED SOURCE
  projects/primordial-paradox/assets/audio/pp_01_title_v7/pp_01_title_v7.ogg` and `_v8`. `game/datafiles/streams`
  holds 59 `.ogg` files and the yyp lists neither v7 nor v8. Those four findings produce
  `test_project.py::test_project_graph_matches_disk`, `::test_generated_project_files_are_current`,
  `::test_build_inputs_are_committed` and the two `test_build_inputs.py` rows.
- **One red, a dash in a generated digest.** `test_project.py::test_no_em_or_en_dashes_anywhere` fails on 2 lines,
  both in `output/_eye_r10_digest.txt` (line 190 and line 194), which is untracked and written by the eye lane's review
  text, not by source (`dash_r8.out`, `local_dash_r8.out`).

## 3. The 22 row table

Scale unchanged: 0 nothing, 1 spec only, 2 code or data but unproven in the game, 3 proven in the running game with a
capture or a test, 4 polished. Base is the table in `HACKATHON-AUDIT-2026-10-22.md` section 1.

| # | Subsystem | Base | 02:05 | 06:30 | 13:07 | 21:41 | 05:15 | Now | Evidence for the Now value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Title screen | 3 | 3 | 3 | 3 | 3 | 3 | 3 | Carried, not re-shot: the capture was refused five times by the idle gate (`capture_title_r8.out`: `input 27 s / 56 s / 89 s / 6 s / 66 s ago, 120 s required`, exit 4), so `output/title_run_1.png` is still 05:08, 34856 B, sha eb25782c3d79353d. Measured on it this run: viewport crop 768x720, 38 distinct colours, 35 px off the 55 colour master across 28 off-master colours, largest `#134C61` 3 px (`exact_r8.py`). `output/nes_title_frame.png` 256x240 is 11 colours, 0 px off master, 1.0000, but its date is 10-21 22:01, older than the sprite work. Not 4 on the blended pixels. |
| 2 | Intro crawl | 3 | 3 | 3 | 3 | 3 | 3 | 3 | `output/crawl_mid.png` and `crawl_end.png` 768x720, 4 colours each, and the one off-master colour is `#F9F9F9` at 18423 px and 21060 px of 552960, that is 3.3 and 3.8 pct of the frame (`exact_r8.py`); both files are 10-22 07:57, not re-shot this run. Route step `crawl` resolves (`local_route_r8.out`, 22 passed). Not 4: the crawl text is off the palette. |
| 3 | Drive cutscene | 1 | 2 | 3 | 3 | 3 | 3 | 3 | `rm_pp_drive` is one of the 4 rooms in a build that compiled and ran this run (`probe_r8.out`, `build_r8.log`). 12 native frames in `output/drive_frames/` (rewritten 12:16 today) plus 16 files in `output/drive/`; palette legality per frame against the 55 RGB master is **0.0000 to 0.0167 and 0 of 12 at 1.0000**, the same numbers as 05:15 (`png_r8.out`). The one legal file is `output/drive/pp_drive_shot_03_1x_ppu.png` at 1.0000, 7 colours, shot 03 only. Route red, no palette set. |
| 4 | Overworld movement | 3 | 3 | 3 | 3 | 3 | 3 | 3 | Carried, not re-earned: my build reaches `rm_pp_title` and the main loop and no further (`build/last-igor.log`), so the footstep evidence is the 10-23 recorded run, labelled carried. |
| 5 | Maps and doors | 2 | 2 | 2 | 2 | 2 | 2 | 2 | `data/maps/all.json` 16826 B sha 8f5df49b72e6b1ff; the `arrival` and `gate` route steps resolve (`local_route_r8.out`); `rm_pp_ship` is still the only walkable room and no door traversal is captured. |
| 6 | Dialogue and talk | 3 | 3 | 3 | 3 | 3 | 3 | 3 | `data/dialogue/all.json` 11547 B sha fcbe450b94f4b60c; Pine shard 0 is 418 passed 0 failed this run, which is the shard that carries the dialogue and choice layout files (`offload-audit-r8-0.json`). |
| 7 | Battle and the talk fight | 3 | 2 | 3 | 3 | 3 | 3 | 3 | Carried: `output/first_fight_verify.json` `"ok": true`, `output/first_fight_capture.mp4` 2237724 B at 10-23 04:42, and no new capture since (`probe_r8.out`). Not 4: the eight battle background frames fail gate 4 (row 18). |
| 8 | Enemies | 2 | 2 | 2 | 2 | 2 | 2 | 2 | `output/enemies_preview_3x.png` was regenerated at 12:18 today, 464x772, 9 colours, 1.0000 on master (`probe_r8.out`, `png_r8.out`); still no enemy inside a live fight is captured. |
| 9 | Party and stats | 2 | 2 | 2 | 2 | 2 | 2 | 2 | `data/characters/party.json` 295 B, last written 10-19 18:47, sha 792079001e701035 (`probe_r8.out`); no open card on the board names party or stats (`board_r8.out`, 91 open cards read). |
| 10 | Save and load | 3 | 2 | 3 | 3 | 3 | 3 | 3 | `output/save_capture_verify.json` `"ok": true` at 10-23 03:43, and this run's live log prints `PP: save read and accepted, music` (`build/last-igor.log`). No capture of a save written and read back after restart. |
| 11 | Ledger | 2 | 2 | 2 | 2 | 2 | 2 | 2 | `tests/test_ledger.py` sits in shard 0, which is 418 passed 0 failed this run (`offload-audit-r8-0.json`); still no capture of a ledger row read back, and no open card names the ledger (`board_r8.out`). |
| 12 | Audio bus and cues | 3 | 3 | 3 | 3 | 3 | 3 | 3 | Live this run: `title_theme streaming ... gain 0.70`, `focus lost, music paused (cue and theme) and every effect stopped`, `focus back, music resumed where it stopped` (`build/last-igor.log`). |
| 13 | Music per scene | 2 | 2 | 2 | 2 | 2 | 2 | 2 | The live log names the title theme only, so per-room coverage stays unproven in the game (`build/last-igor.log`). |
| 14 | SFX | 3 | 3 | 3 | 3 | 3 | 3 | 3 | Live cues this run, `thunder_soft` 11 times (instances 400002 to 400012). Still not 4: `game/datafiles/sfx/sfx.json` was rewritten again at 12:21 today, 5089 B, and still holds **0** occurrences of `car_engine`, and the log still prints `PP audio: car_engine_loop silent, not in sfx/sfx.json` (`probe_r8.out`, `build/last-igor.log`). |
| 15 | UI windows and menus | 2 | 2 | 2 | 2 | 2 | 2 | 2 | `ui_battle_preview.png` 5 colours 1.0000 and `ui_dialogue_preview.png` 5 colours 1.0000 (`png_r8.out`), but `title_ui_preview.png` is 1920x784, 9 colours, **0.0110** on master with `#081420` at 90.5 pct, and gate 4 fails it at `background_area x301, palette x7` (`gate4_r8.out`). A preview is not a live window. |
| 16 | Art pipeline | 2 | 3 | 3 | 3 | 3 | 3 | 3 | Re-earned on Windows this run: the five art test files are **96 passed, 0 failed in 22.25 s** with no git test in the command (`local_art_r8.out`). The pipeline's own drive output is the off-palette art in row 3, so not 4. |
| 17 | Sprites per character | 2 | 2 | 2 | 2 | 2 | 2 | 2 | `output/chars_contact.png` 736x2768, 22 colours, 1.0000, still dated 10-22 02:40 (`png_r8.out`, `probe_r8.out`); card `t_858c2908` (the car, Ronan, Theo, the storm cloud) is still blocked (`board_r8.out`). |
| 18 | Backgrounds per scene | 2 | 3 | 2 | 2 | 2 | 2 | 2 | `output/bg_battle_preview.png` 16 colours 1.0000 on the PNG itself, but gate 4 fails the same file at `background_area x117` and all eight `bg_battle_*_text_preview` and `_fight_preview` frames at 3 to 7 `background_area` each plus `palette x4` (`gate4_r8.out`). My build reaches no battle, so this is carried. |
| 19 | Build and packaging | 3 | 3 | 3 | 3 | 3 | 3 | 3 | My build 13:09 to 13:14, `.win` 459724 B, **`BUILD PASS`**, exit 0, game live and closed with a plain `taskkill` (`build_r8.log`). Not 4: no zip, no install step, and the runner is still the 7941704 B exe of 10-20, sha 5cbf3f4a9b1f4d8b. |
| 20 | Tests and gates | 2 | 2 | 2 | 2 | 2 | 2 | 2 | Gate 1 exit 0, gate 2 exit 0, gate 4 exit 1 on 34 of 184 (`gate1_r8.out`, `gate2_r8.out`, `gate4_r8.out`); Pine **1324 passed 3 failed, all three shards completed** (`offload-audit-r8-*.json`); Windows **8 reds from three causes** (`local_route_r8.out`, `local_project_r8.out`, `local_winonly_r8.out`). Better than 05:15, but the gate is still red, so not 3. |
| 21 | Capture and demo tooling | 3 | 2 | 3 | 3 | 3 | 3 | 3 | `tools/capture_title.py` ran and refused to open a window five times on the idle gate, which is the tool working as RULE 1 declares, not a capture (exit 4, `capture_title_r8.out`); `output/demo/run_002_verify.json` says `"ok": true` with `not_a_terminal: PASS 7 of 7 sampled frames`, and `"audio": "rendered stand-in from run_002_audio.m4a"`; `run_002.mp4` is 10-23 01:49 and no `run_003` exists (`probe_r8.out`). Not 4 on the stand-in audio. |
| 22 | Docs and repo hygiene | 3 | 3 | 3 | 3 | 3 | 3 | 3 | `README.md` 12887 B rewritten 11:18 today, `LICENCE` 5040 B, `CREDITS.md` 14394 B, all at the root (`probe_r8.out`). Its own state table still says the drive is `shot list and generator, no room yet` (`README.md:26`) while `rm_pp_drive` is one of four rooms in this run's build, so the front door document is stale against the build. |

Rows 22, sum **57**, mean **2.591**. The columns read 53 at 02:05, then 57 at 06:30, 13:07, 21:41 and 05:15, and 57 now.
The 10-22 audit table alone sums to 49 with row 22 at 1; the 02:05 page re-based that row to 2, which is the whole of the
49 to 50 difference. Rows that moved against the 05:15 page: **none**.

## 4. What moved, and what did not, with the command behind each

No score moved. Six things changed underneath the scores:

- **The Pine suite lost 18 reds and gained one.** 05:15 was 955 passed 21 failed with shard 2 dead on a transport error;
  this run is 418 / 0, 537 / 2, 369 / 1, all three shards completed (`offload-audit-r8-*.json` against
  `offload-audit-r7b-*.json`). The 19 Windows-import reds the 05:15 page diagnosed are gone. The one new red,
  `test_project.py::test_no_em_or_en_dashes_anywhere`, is not new to the tree; it is new to the offload, because shard 2
  never ran at 05:15 (`pine_r8.log`).
- **That new red is a generated file, not a source file.** 2 lines, `output/_eye_r10_digest.txt:190` and `:194`, both
  em dashes inside quoted eye-review prose (`dash_r8.out`). The file is untracked and `test_project.py` walks the
  worktree, so a lane's scratch output turned the dash gate red.
- **A new build-input red, with a known cause and a disputed count.** `check_project.check` names exactly
  `pp_01_title_v7.ogg` and `pp_01_title_v8.ogg` as not listed in the yyp, and `check_build_inputs.check` names the same
  two as `UNCOMMITTED SOURCE` (`inputs_r8.out`). The 59 files in `game/datafiles/streams` contain v7 and v8 and the yyp
  contains neither. Card `t_c31f9295` (mine, blocked) says four audio sources in three directories, a different number
  from today's two; that card's count needs restating against this measurement.
- **The art set is finally green together on Windows.** 96 passed, 0 failed, with `test_nes_check.py` inside the same
  command (`local_art_r8.out`). At 05:15 the same idea was 118 passed with `test_project.py` folded in and 1 red; the art
  files themselves were already green, and this run measures them without the git test to say so cleanly.
- **Two art artefacts were regenerated by another lane today and both were re-measured here.** `output/enemies_preview_3x.png`
  rewritten 12:18: 9 colours, 1.0000, unchanged verdict. `output/drive_frames/` rewritten 12:16: still 0 of 12 shots at
  1.0000, minimum 0.0000, maximum 0.0167 (`png_r8.out`). A regeneration that changes no legality number.
- **The build input the drive needs is still missing after a fresh sfx rewrite.** `sfx.json` changed again at 12:21
  (5089 B, sha 80a2d1e31f4ce2a8) and `car_engine` is in it 0 times; the 13:09 build log prints
  `PP audio: car_engine_loop silent, not in sfx/sfx.json` (`probe_r8.out`, `build/last-igor.log`).

## 5. The top five blockers to the playable slice, with the card that owns each

1. **The drive step cannot resolve, and the drive has no palette set.** `local_route_r8.out` is 2 failed 22 passed with
   both reds naming `drive_to_southampton`; `data/scenes/all.json` holds 13 scene ids and none is the drive;
   `data/scene_palettes.json` holds 12 entries and none is the drive; 12 of 12 native frames are outside the 2C02 master
   (`inputs_r8.out` neighbours: `probe_r8.out`, `png_r8.out`). Covered by `t_c27552e3` R21b DRIVE-SCENE (builder, todo,
   priority 98), `t_ff5a3714` SLICE-ROUTE-DATA (gamedev, todo) and `t_3cca8576` REVIEW-R21-DRIVE (code-review, todo).
   Uncovered: the palette set, which RULE 0 point 1 of `ART-BIBLE.md` makes a spec. Proposed card, owner gamedev:
   `DRIVE-PALETTE-SET: a drive scene palette set in data/scene_palettes.json plus 12 of 12 shots inside it, with the
   measured legal fraction per shot as the acceptance`. That question is already asked as `t_f034f9d0`, blocked, and
   still has no gamedev answer: `knowledge/GAMEDEV-DECISIONS-2026-10-23.md:42` to `:48` rules only that R21 exists and
   that builder owns the drive block, and mentions the palette nowhere.
2. **Five of the eight Windows reds are one uncommitted title theme.** v7 and v8 in `assets/audio/` and
   `game/datafiles/streams/`, in neither the commit nor the yyp (`inputs_r8.out`: 2 + 2 lines). No open card on the
   board names v7 or v8 (`board_r8.out`); `t_c31f9295` (audit, blocked) is the nearest and it names four audio sources in
   three directories, not these two, so its count needs restating. Proposed card, owner musician with builder on the yyp
   row:
   `TITLE-THEME-V7V8-LAND: pp_01_title_v7.ogg and pp_01_title_v8.ogg committed, listed in the yyp, and
   test_project.py::test_build_inputs_are_committed green on Windows`.
3. **The judged video's audio is still a rendered stand-in, and the video is two days old.**
   `output/demo/run_002_verify.json` says `"ok": true`, `not_a_terminal` PASS 7 of 7, and
   `"audio": "rendered stand-in from run_002_audio.m4a, not the game's live output"`; `run_002.mp4` is 10-23 01:49,
   4453751 B, and `output/demo/` holds no `run_003` (`probe_r8.out`). No open card owns the recorder (`board_r8.out`;
   `t_030a89e5` R32 is the route). Proposed card, owner testing: `DEMO-AUDIO-LIVE: one recorded run whose audio track is
   the game's own output, with the verifier's audio field reading live and not stand-in`.
4. **The dash gate is red on a lane's scratch output.** `output/_eye_r10_digest.txt` lines 190 and 194 carry em dashes;
   the file is untracked and written by the eye lane's digest text (`dash_r8.out`, `local_dash_r8.out`). No card owns it
   and `t_3a932e73` GEMINI-EYE is blocked on quota, not on this. Proposed card, owner testing: `DIGEST-DASHES: the eye
   digest writer emits no em or en dash, or the digest is written outside the tree test_project walks, so
   test_project.py::test_no_em_or_en_dashes_anywhere is green`.
5. **The drive plays silent and no card owns the sound.** `car_engine` is 0 times in
   `game/datafiles/sfx/sfx.json` (rewritten 12:21 today) and 0 times in `data/audio.json`, and the 13:09 build log prints
   `PP audio: car_engine_loop silent, not in sfx/sfx.json` (`probe_r8.out`, `build/last-igor.log`). Proposed card, owner
   musician: `DRIVE-ENGINE-LOOP: car_engine_loop in game/datafiles/sfx/sfx.json with a cue, and the live log stops
   printing "silent, not in sfx/sfx.json"`.

Outside the five and still true: gate 4 red on 34 of 184, with `output/title_ui_preview.png` at 0.0110 and `palette x7`,
the eight `bg_battle_*` previews, and `output/drive_gantry_preview.png` still the only drive file the scan reaches
(`gate4_r8.out`); no open card names party stats or the ledger (`board_r8.out`); `README.md:26` still tells a reader the
drive has no room.

## 6. What I could not measure, and why

- **A fresh title capture.** `capture_title.py` refused five times on its idle gate with the exact lines `input 27 s ago`,
  `56 s ago`, `89 s ago`, `6 s ago` and `66 s ago` against `120 s required`, exit 4 (`capture_title_r8.out`). Someone was
  at the keyboard through the whole window this audit had, so RULE 1 kept the window shut and row 1 is carried from
  05:08. I did not work around the gate.
- **A live battle, a live overworld walk and a live drive.** My build runs to `rm_pp_title` and the main loop and stops
  there (`build/last-igor.log`). Rows 4, 7, 18 and the walk in 5 are carried and say so.
- **The three nodes Pine deselects.** Two of `test_project.py` and one of `test_mix_check_v3.py` were run on Windows
  instead, inside `local_project_r8.out` and `local_winonly_r8.out`, which is where their reds come from.

## 7. Q: for gamedev

1. Carried from `t_f034f9d0` and still unanswered: is the drive meant to be a graded, non-NES look, which would need
   `ART-BIBLE.md` RULE 0 point 1 amended, or quantized like the rest, with `output/drive/pp_drive_shot_03_1x_ppu.png`
   (7 colours, 1.0000) as the pattern for all twelve?
2. New, and the same kind of spec call: `pp_01_title_v7.ogg` and `pp_01_title_v8.ogg` are on disk and in neither the
   commit nor the yyp. Are those the accepted title theme going forward, in which case the yyp and the commit follow
   them, or are they experiments that belong outside `game/datafiles/streams`? Either answer closes five reds, and the
   choice is gamedev's, not mine.

## 8. Check for this page

- Every row carries a file this run opened or a command it ran. This run's outputs are `probe_r8.out`, `data_r8.out`,
  `png_r8.out`, `exact_r8.out`, `inputs_r8.out`, `dash_r8.out`, `build_r8.log`, `gate1_r8.out`, `gate2_r8.out`,
  `gate4_r8.out`, `local_art_r8.out`, `local_route_r8.out`, `local_project_r8.out`, `local_dash_r8.out`,
  `local_winonly_r8.out`, `capture_title_r8.out`, `board_r8.out`, `pine_r8.log` and `pine_read_r8.out`, all under
  `<agent-runtime>\kanban\boards\nayil-ops\workspaces\t_c5b00165\`.
- The Pine evidence is `offload-audit-r8-0.json`, `-1.json` and `-2.json` under
  `<workspace>\Shared\projects\arananet\pine\data\results\`, all three `status: completed`, read by
  `pine_read_r8.py`.
- Board statuses in section 5 come from `nayil-ops\kanban.db` opened read-only at 13:11 (`board_r8.py`):
  793 done, 560 archived, 67 blocked, 17 todo, 3 review, 2 ready, 2 running, 91 open cards listed.
- Side effects to declare, all of them what the tools write on every run: `python tools/nes_audit_all.py` rewrote
  `knowledge/NES-AUDIT.md`, the per-file reports under `output/nes_audit/` and `output/nes_audit_worst_3x.png`; the build
  rewrote `output/PrimordialParadox/` and `build/last-igor.log`; the Pine tool wrote its three result JSON files. The
  pytest runs rewrote `game/datafiles/sfx/` mirrors as their setup always does (`copied 1, removed 0, 69 unchanged`,
  `mirrored 21 sound effects into game/datafiles/sfx` in `local_dash_r8.out`). Nothing in `data/`, `game/scripts/` or
  `tests/` was edited by this run.
- This page contains 0 em dashes and 0 en dashes, checked by `dashcheck_r6.py`, which prints `dash lines: 0`; the two
  offending lines of `output/_eye_r10_digest.txt` are reported by line number and described, not quoted. Hyphens appear
  only in file names, card ids, flags and compounds.
