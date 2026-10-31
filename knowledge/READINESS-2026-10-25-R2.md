# Readiness refresh 9, 2026-10-25 17:18 to 18:05: the 22 row table re-measured

Written by audit for card `t_d6d02ccb` (AUTO-AUDIT-REFRESH). Every number below came from a command this run ran on this
PC between 17:18 and 18:05 Pacific, or from a file this run opened. Worker reports, card results, `GATE-GREEN-2026-10-25.md`
and the eight earlier readiness pages were not accepted as evidence. `READINESS-2026-10-25.md` (refresh 8) is untouched;
this is a new page, and its `Before` column is that page.

The tree this run measured: HEAD `29128aa` "ci: a suite failure now names the tests that failed, not just how many",
committed 2026-10-25 07:55:22, 1081 dirty porcelain entries (`probe.out`). Refresh 8 finished on `341109a` at 05:31.

P: the table sums 57 again, mean 2.591, so no score moved for the eighth page running. Two rows were re-earned live this
run (2 and 3) and one could not be re-earned at all (1, capture refused by the idle gate).
P: the build passed and reached further than at 05:26: `BUILD PASS` exit 0 in 71 s, and its own log carries the intro
start, the intro finish and the route's drive handoff, at `build/last-igor.log:124`, `:201`, `:202` (`build/last-igor.log`).
P: the drive cue is measured missing to the game while present on disk: `PP audio: music cue PP-02 has no OGG yet,
expected pp_drive_v2.ogg, placeholder 1` (`build/last-igor.log:204`), against a 2453706 byte
`game/datafiles/streams/pp_drive_v2.ogg` that `git ls-files --error-unmatch` rejects as untracked.
P: `tools/capture_title.py` did not open a window at all: three attempts, exit 4, `P: idle gate SKIPPED the launch: input
26 s ago, 120 s required` (`capture_title_r11.out`). The newest title frame on disk is still 05:28.
P: the Pine suite is **1484 passed, 2 failed** over three completed shards, and both reds are platform artifacts, proved by
rerunning the same two files on Windows: **34 passed in 2.29 s** (`offload-audit-ready-1025c-*.json`, `local_art_r11.out`).
P: attempt one of Pine died on the interpreter first, `PineConfigError: the pinesandbox SDK is not importable in this
process (ModuleNotFoundError)` in all three shards (`offload-audit-ready-1025b-*.json`), which is the trap refresh 8
documented and it cost this run 90 seconds.

## 0. What this run measured, in one place

| Measurement | Command or source | Result |
| --- | --- | --- |
| HEAD and dirt | `git rev-parse --short HEAD`, `git status --porcelain` | `29128aa`, 07:55:22, 1081 entries (`probe.out`) |
| Build | `python tools/integration_build.py` | exit 0 in 71.5 s, `BUILD PASS: Igor compiled the project and launched the game`, `Igor complete.` (`build/audit-readiness-build-2026-10-25.log`) |
| Process left behind | `tasklist` after the build | no `Igor.exe`, no game process (`tasklist`) |
| Reach of the built game | `build/last-igor.log`, 216 lines | `:108` title theme, `:118` save read, `:124` intro started, `:201` intro finished, `:202` crawl handed to the route's step drive, `:204` drive cue placeholder, `:212` `###game_end###254` |
| Rooms | `ls game/rooms` | 4: `rm_pp_boot`, `rm_pp_drive`, `rm_pp_ship`, `rm_pp_title` (`probe.out`) |
| GML size | walk over `game/scripts` | 25 files, 10752 lines, 25 folders (`probe.out`) |
| Slice route | `data/slice.json` 1741 B sha256 a42993c7ca7245cb | 9 steps: title, crawl, drive, arrival, gate, boarding, fight, save, gameover (`palette_probe.py`) |
| Scenes | `data/scenes/all.json` 9424 B sha256 1eaa6519d26b25be | 15, `drive_to_southampton` among them (`probe.out`) |
| Scene palette sets | `data/scene_palettes.json` 30636 B sha256 3937f9d5306761ba, mtime 07:28 | 12 sets, `grep -c drive` returns 0; grew 3847 B since refresh 8 with no new scene row (`palette_probe.py`) |
| Gate 1 | `python tools/check_data.py` | exit 0, `check_data: all files pass` |
| Gate 2 | `python tools/check_cleanroom.py` | exit 0, `check_cleanroom: no reference, no foreign name, no foreign phrase, every module reviewed`, 121 OSM names exempt |
| Gate 4 | `python tools/nes_audit_all.py` | exit 1, `184 file(s) checked, 34 failing, 0 unread, 10 gated failure(s)` (`knowledge/NES-AUDIT.md:16`) |
| Title frame legality | Pillow over `output/title_run_reference_3x.png` (05:28) | 768x720, 35 RGB, 0.9999 on the 55 colour master, 33 off-master px in 26 colours, largest `#053E53` 2 px (`png_r11.out`) |
| Window capture legality | Pillow over `output/title_run_1.png` (05:28) | 784x759, 2887 RGB, 0.9409 on master, off-master chrome `#F9F1ED` 7907 px (`png_r11.out`) |
| Committed title frame | Pillow over `output/nes_title_frame.png` | 256x240, 11 RGB, 1.0000 on master (`png_r11.out`) |
| Preview PNGs | Pillow, `output/` | ui_battle 5 RGB 1.0000, ui_dialogue 5 RGB 1.0000, ui_menu 4 RGB 1.0000, chars_contact 25 RGB 1.0000, bg_battle_preview 16 RGB 1.0000, enemies_preview_3x 9 RGB 1.0000 (`png_r11.out`) |
| The two red previews | Pillow, `output/` | `title_ui_preview.png` 1920x784 9 RGB **0.0109**, `#081420` 1362523 px; `gameover_preview.png` 256x240 4 RGB **0.0000**, `#0B0B0F` 58824 px (`png_r11.out`) |
| Drive frames | Pillow, `output/drive_frames/*.png` | 12 frames, 0 of 12 legal, 0.0000 to 0.0167, `#081420` the largest offender in 8 of 12 (`png_r11.out`) |
| Crawl frames | Pillow | `crawl_mid.png` 4 RGB 0.9667 (`#F9F9F9` 18423 px), `crawl_end.png` 4 RGB 0.9619 (`#F9F9F9` 21060 px) (`png_r11.out`) |
| Demo video | `output/demo/*.json` | `run_001_verify.json` `ok: false`; `run_002_verify.json` `not_a_terminal PASS 7 of 7` but `audio: rendered stand-in`, `checked_at` 2026-10-23T01:49:11; no `run_003.mp4` |
| Fight capture | `output/first_fight_verify.json` | `ok: true`, `checked_at` `2026-10-23T06:31:07`, file mtime 10-24 15:06, so a re-copy, not a capture from this build |
| Save capture | `output/save_capture_verify.json` | 15 checks, written 10-24 20:47, not rerun by this run |
| Root docs | `probe.out` | `README.md` 12887 B sha256 da4acb95e59775ca, `LICENCE` 5040 B, `CREDITS.md` 14394 B |
| The README's drive line | `README.md:26` | still `shot list and generator, no room yet`, while `rm_pp_drive` is 1 of 4 rooms |
| Board | read-only copy of `boards/nayil-ops/kanban.db`, 23478272 B at 17:24 | 907 done, 583 archived, **71 blocked, 11 running, 11 todo, 0 ready** (`board_r11.out`) |

No key or login file was opened. Only paths, sizes, digests, log lines and test output appear here.

## 1. The build, and the game it launched

One attempt, and it worked: `python tools/integration_build.py` returned exit 0 after 71.5 s and printed `BUILD PASS: Igor
compiled the project and launched the game` and `Igor finished. The game window is the only window that opened.`
(`build/audit-readiness-build-2026-10-25.log`). `tasklist` straight after shows no `Igor.exe` and no game process, so
nothing of mine is left running.

`build/last-igor.log` is 216 lines, up from the 138 lines refresh 8 measured, and it reaches further (`grep -nE` over the
file, line numbers exact):

    108  PP audio: title_theme streaming streams/title_theme_v3_126.ogg, instance 400001, gain 0.70
    118  PP: save read and accepted, music
    124  PP title: intro started, pan 180 steps, 24 stars, 14 crawl lines
    128  PP audio: title_theme ducked 6 dB, gain 1.40
    200  PP audio: title_theme back to full after 6 dB
    201  PP title: intro finished, starting the run in rm_pp_ship
    202  PP title: the crawl handed to the route's step drive
    203  PP audio: title_theme handed to the fade, the cue takes the one music source
    204  PP audio: music cue PP-02 has no OGG yet, expected pp_drive_v2.ogg, placeholder 1
    212  ###game_end###254

This is a strict gain of reach against refresh 8, whose log stopped at `:118` and ended at `:134` with no crawl line at all.
It is still short of a fight: nothing between `:204` and `:212` is a battle, a walk or a gate.

## 2. Gates, each with what it actually returned

1. `python tools/check_data.py`, exit 0, `check_data: all files pass`.
2. `python tools/check_cleanroom.py`, exit 0, 121 OSM place names exempt, every module reviewed.
3. `python tools/nes_audit_all.py`, exit 1, `184 file(s) checked, 34 failing, 0 the checker could not read, 10 gated
   failure(s)` (`knowledge/NES-AUDIT.md:16`). Same 184 and 34 as refresh 8 and R7.
4. Pine, attempt one: all three shards `status: error`, `PineConfigError: the pinesandbox SDK is not importable in this
   process (ModuleNotFoundError)` (`offload-audit-ready-1025b-0.json`, `-1.json`, `-2.json`). The zip did build
   (14337377 bytes, 86 files, 3 shards) and the tool deselected 3 nodes it cannot carry (`test_mix_check_v3` slice node,
   two `test_project` nodes). This is the interpreter trap refresh 8 already documented, hit again because the default
   `python` in this shell is the Hermes venv.
5. Pine, attempt two with `<home>/AppData/Local/Python/bin/python.exe`: all three shards `completed` in 231 s, zip
   14432209 bytes 86 files, **356 passed 0 failed**, **613 passed 1 failed**, **515 passed 1 failed**, so **1484 passed, 2
   failed** (`offload-audit-ready-1025c-0.json`, `-1.json`, `-2.json`). The two reds are
   `test_scene_palette_set.py::test_the_committed_cloud_ground_is_the_crop_its_generator_builds` and
   `test_make_battle_bg.py::test_the_committed_strips_are_what_the_generator_writes`, both byte comparisons of a committed
   PNG against its generator, which is the cross-platform class refresh 8 already named. I reran those two files on Windows
   at 18:12: **34 passed in 2.29 s** (`local_art_r11.out`), so both reds are artifacts of the Linux far side, not project
   defects, and gate row 20 uses the Windows number where it matters.
6. `python tools/capture_title.py`, three attempts, all exit 4, no window opened: `P: idle gate SKIPPED the launch: input
   26 s ago, 120 s required, waited 0 s of 0 s` (`capture_title_r11.out`), then `115 s ago`
   (`capture_title_r11b.out`), then a third attempt after a 215 s wait (`capture_title_r11c.out`). The game was not
   launched, so this is not a verdict on the title screen; it is a verdict on unattended capture on a PC somebody is using.

## 3. The 22 row table

Scale unchanged: 0 nothing, 1 spec only, 2 code or data but unproven in the game, 3 proven in the running game with a
capture or a test, 4 polished. `Before` is `READINESS-2026-10-25.md` section 3 (refresh 8).

| # | Subsystem | Base | Before | Now | Evidence for the Now value |
| --- | --- | --- | --- | --- | --- |
| 1 | Title screen | 3 | 3 | 3 | Re-measured on the 05:28 frame, not re-captured: `title_run_reference_3x.png` 768x720, 35 RGB, 0.9999 on the 55 colour master, 33 off-master px in 26 colours, largest `#053E53` 2 px (`png_r11.out`). The capture could not rerun (section 2 item 6), so this row is a measurement of an old frame and says so. Not 4 on those 33 px. |
| 2 | Intro crawl | 3 | 3 | 3 | **Re-earned live this run**: `PP title: intro started, pan 180 steps, 24 stars, 14 crawl lines` (`build/last-igor.log:124`) and `intro finished, starting the run in rm_pp_ship` (`:201`). Frames unchanged: `crawl_mid.png` 0.9667, `crawl_end.png` 0.9619, both 4 RGB (`png_r11.out`). |
| 3 | Drive cutscene | 3 | 3 | 3 | **Re-earned live this run**: `the crawl handed to the route's step drive` (`build/last-igor.log:202`), 4 rooms including `rm_pp_drive` (`probe.out`), `drive_to_southampton` in the 15 scene rows (`probe.out`). Not 4: the cue is a placeholder at `:204` and 0 of 12 drive frames are legal (`png_r11.out`). |
| 4 | Overworld movement | 3 | 3 | 3 | Carried, not re-earned: no footstep and no walk line between `:204` and `:212` (`build/last-igor.log`), and no room beyond the title and ship. The footstep evidence stays the 10-23 recorded run. |
| 5 | Maps and doors | 2 | 2 | 2 | `data/maps/all.json` 26815 B sha256 afd6c34b1c350837, unchanged (`probe.out`). No door traversal captured in a live run. |
| 6 | Dialogue and talk | 3 | 3 | 3 | `data/dialogue/all.json` 15056 B sha256 ad63e7fcf2b3804f unchanged, `data/talk_cards.json` 28977 B sha256 c5d4b8696220d6f3 (`probe.out`). No live blip line this run, so carried. |
| 7 | Battle and the talk fight | 3 | 3 | 3 | Carried and the carry is visible: `output/first_fight_verify.json` is `"ok": true` with `checked_at` `2026-10-23T06:31:07` while its mtime is 10-24 15:06, a re-copy. This build's log reaches `###game_end###254` (`build/last-igor.log:212`) with no battle line. |
| 8 | Enemies | 2 | 2 | 2 | `enemies_preview_3x.png` 464x772, 9 RGB, 1.0000 on master (`png_r11.out`), `data/enemies/roster.json` 19936 B sha256 cc516be9cf721136 (`probe.out`). No enemy inside a live fight. |
| 9 | Party and stats | 2 | 2 | 2 | `data/characters/party.json` 295 B, 10-19 18:47, sha256 792079001e701035, one character (`probe.out`). Unchanged for six days. |
| 10 | Save and load | 3 | 3 | 3 | **Live this run**: `PP: save read and accepted, music` (`build/last-igor.log:118`). `output/save_capture_verify.json` is 10-24 20:47 and was not rerun. Not 4: this build writes no save. |
| 11 | Ledger | 2 | 2 | 2 | No ledger line in this build's 216 log lines (`build/last-igor.log`), and no capture reads a ledger row back. Carried at 2. |
| 12 | Audio bus and cues | 3 | 3 | 3 | **Live this run**: `title_theme streaming ... gain 0.70` (`:108`), `ducked 6 dB, gain 1.40` (`:128`), `back to full after 6 dB` (`:200`), `the title theme handed to the fade, the cue takes the one music source` (`:203`). |
| 13 | Music per scene | 2 | 2 | 2 | Measured negative this run, and it is the sharpest line on this page: `music cue PP-02 has no OGG yet, expected pp_drive_v2.ogg, placeholder 1` (`:204`) while `game/datafiles/streams/pp_drive_v2.ogg` is 2453706 B on disk and `git ls-files --error-unmatch` rejects it as untracked, and `game/PrimordialParadox.yyp:2232` lists `pp_drive_v2.ogg`. Still 2: no scene other than the title has live music. |
| 14 | SFX | 3 | 3 | 3 | `game/datafiles/sfx/sfx.json` mirror present and the log's audio lines fire (`build/last-igor.log:108` to `:203`), plus refresh 8's load and play lines. Not 4: no ear pass on the slice. |
| 15 | UI windows and menus | 2 | 2 | 2 | `ui_battle_preview.png` and `ui_dialogue_preview.png` are 5 RGB at 1.0000 and `ui_menu_preview.png` 4 RGB at 1.0000, but `title_ui_preview.png` is **0.0109** with `#081420` at 1362523 px (`png_r11.out`) and gate 4 keeps it failing. A preview is not a live window. |
| 16 | Art pipeline | 3 | 3 | 3 | **Re-earned with a caveat stated**: Pine gave **1484 passed 2 failed**, and both reds are committed PNG against generator byte comparisons (`offload-audit-ready-1025c-1.json`, `-2.json`); rerunning those two files on Windows gives **34 passed in 2.29 s** (`local_art_r11.out`), so on this platform the pipeline reproduces its committed output. Eleven of the thirteen preview and frame PNGs measured are exactly 1.0000 on master (`png_r11.out`). Not 4: the drive frames are 0 of 12 legal. |
| 17 | Sprites per character | 2 | 2 | 2 | `output/chars_contact.png` 736x2768, 25 RGB, 1.0000 on master (`png_r11.out`). Not regenerated this run, so not re-earned. |
| 18 | Backgrounds per scene | 2 | 2 | 2 | `bg_battle_preview.png` 1560x696, 16 RGB, 1.0000 on master (`png_r11.out`), and gate 4 still fails the text and fight preview frames of the same family. No battle reached live. |
| 19 | Build and packaging | 3 | 3 | 3 | **`BUILD PASS`**, exit 0, 71.5 s (`build/audit-readiness-build-2026-10-25.log`), and nothing left running (`tasklist`). Not 4: no zip, no install step, and the runner exe is still the 10-20 build. |
| 20 | Tests and gates | 2 | 2 | 2 | Pine **1484 passed 2 failed**, both reds shown by a Windows rerun to be Linux artifacts (`offload-audit-ready-1025c-*.json`, `local_art_r11.out`); gates 1 and 2 exit 0; gate 4 exit 1 on 34 of 184 (`knowledge/NES-AUDIT.md:16`). The best suite state these pages have recorded, 29 tests better than refresh 8, but gate 4 is red, so not 3. |
| 21 | Capture and demo tooling | 3 | 3 | 3 | Held at 3 on the strength of the tool, not of a run: `capture_title.py` refuses to launch while the PC has keyboard input inside 120 s, which is a safety behaviour that works, and its last clean run is 05:28. The demo side did not move: `run_001` `ok: false`, `run_002` audio stand-in, no `run_003`. New finding, below. |
| 22 | Docs and repo hygiene | 3 | 3 | 3 | `README.md` 12887 B, `LICENCE` 5040 B, `CREDITS.md` 14394 B (`probe.out`). Not 4 on one measured line: `README.md:26` still reads `shot list and generator, no room yet` for a drive that is 1 of 4 rooms. |

Rows 22, sum **57**, mean **2.591**. Rows that moved against refresh 8: **none**. Rows re-earned live this run: 2, 3, 10,
12, 16, 20. The one row this run could not re-earn and states why: 1, whose capture was refused three times by the idle
gate, and 21, which held its value on the tool rather than on a fresh run.

## 4. What moved underneath the scores

- **Reach came back.** Refresh 8's build stopped at the save read and ended with no crawl line (`READINESS-2026-10-25.md`
  section 1); this build starts the intro at `:124`, finishes it at `:201` and hands the crawl to the route's drive at
  `:202` (`build/last-igor.log`). Rows 2 and 3 are live again rather than carried.
- **The drive cue is a new, specific defect.** The log says the cue has no OGG (`:204`), the file exists at 2453706 B
  (`ls game/datafiles/streams`), the project lists it (`game/PrimordialParadox.yyp:2232`), and git does not track it
  (`git ls-files --error-unmatch`). Refresh 8 wrote that the cue "is on disk and in the project" and that the render
  request was moot; the game's own line shows that reading was too generous.
- **The palette file grew without a new scene.** `data/scene_palettes.json` went 26789 B (refresh 8) to 30636 B at 07:28
  (`probe.out`), still 12 scene sets, `grep -c drive` still 0 (`palette_probe.py`). Something was added to it that is not
  a drive set, so the thing ART-BIBLE RULE 0 point 1 requires is still absent.
- **The board emptied of `ready` again.** 71 blocked, 11 running, 11 todo, 0 ready, 907 done, 583 archived
  (`board_r11.out`, read from a copy of the 17:24 board file). Refresh 8 read 69 blocked, 9 todo, 4 running, 0 ready.
- **Unattended capture is impossible on a PC in use.** Three attempts, exit 4 each, the gate reporting input 26 s and
  then 115 s old (`capture_title_r11.out`, `capture_title_r11b.out`, `capture_title_r11c.out`). Any auto-audit that
  depends on a fresh frame will silently keep measuring the previous frame unless it checks exit 4.
- **The Pine interpreter trap fired again, and cost 90 seconds.** `PineConfigError: the pinesandbox SDK is not importable`
  in all three shards because the default `python` in this shell is the Hermes venv (`offload-audit-ready-1025b-*.json`),
  exactly what refresh 8 documented; the retry with `AppData/Local/Python/bin/python.exe` completed in 231 s. The tool does
  not pin a working interpreter, so the trap is one command away at all times.
- **The suite is 29 tests better than this morning**: 1484 passed 2 failed against refresh 8's 1455 passed 2 failed, and
  both reds are the same cross-platform class on both pages (`offload-audit-ready-1025c-*.json`).

## 5. The top five blockers to the playable slice, with the card that owns each

1. **The drive cue does not resolve in the running game.** `music cue PP-02 has no OGG yet, expected pp_drive_v2.ogg,
   placeholder 1` (`build/last-igor.log:204`), against an untracked 2453706 B file on disk and a yyp entry at
   `game/PrimordialParadox.yyp:2232`. Covered by: nothing for the cue. `t_f034f9d0` (gamedev, blocked) owns the drive
   palette, not the cue. Uncovered gap. Proposed card, owner builder: `DRIVE-CUE-RESOLVE: one live log line proving
   pp_drive_v2.ogg loaded and played in the drive step, and the stream committed or its absence stated`.
2. **No unattended run reaches a fight, a walk, a gate or a save write.** This build ends at `###game_end###254`
   (`build/last-igor.log:212`) one step past the route handoff. Covered in parts by `t_030a89e5` R32 TEST-SLICE-ROUTE
   (blocked), `t_d2b724e3` GATE-CHOICE-CAPTURE, `t_c024f8bc` ARRIVAL-MAP. Uncovered: the reach itself. Proposed card,
   owner testing: `SLICE-RUN-REACH: a build whose own log carries walk, gate, fight ending and a save write in one run,
   with line numbers named and the ceiling stated where it still stops`.
3. **Gate 4 is red on 34 of 184 files and no card owns the list.** Worst measured here: `gameover_preview.png` at
   **0.0000** (`#0B0B0F` 58824 px) and `title_ui_preview.png` at **0.0109** (`#081420` 1362523 px)
   (`png_r11.out`, `knowledge/NES-AUDIT.md:16`). Covered only in part by `t_a5e0d631` ART-REPRO-TITLE (blocked), which is
   about reproducing two PNGs, not about the scan. Uncovered gap. Proposed card, owner testing: `NES-GATE-TRIAGE: the 34
   findings split into previews and sheets the rule should exempt and frames that must be fixed, with the exempt list
   written into tools/nes_audit_all.py`.
4. **The README contradicts the build on the drive.** `README.md:26` reads `shot list and generator, no room yet` while
   `ls game/rooms` returns `rm_pp_drive` as one of four (`probe.out`). A judge reads the README first. Covered by
   `t_8d7bad5f` R45 README-SLICE in intent, but that card was aimed at a README that did not exist and the README now
   exists and is wrong. Uncovered as a fix. Proposed card, owner default (assistant lane): `README-TRUTH: every subsystem
   line in README.md checked against the tree on the day, drive row corrected, and the date of the check printed in the
   file`.
5. **The audit loop cannot run its own two heaviest gates without a human workaround.** Capture exits 4 on the idle gate
   (three attempts today), Pine exits on the venv interpreter (one attempt today, 90 s lost), so row 1 is carried and row
   21 held on the tool rather than a run. Covered by: nothing. Uncovered gap. Proposed card, owner builder:
   `AUDIT-GATE-RUNNABLE: tools/capture_title.py states its idle gate in machine-readable form and
   tools/run_tests_offload.py pins the interpreter it needs, so an unattended refresh cannot mistake a skip or a config
   error for a result`.

Outside the five and still true: `pp_03_harbor_v4b.ogg` is still in no commit; no open card names party stats or the
ledger; the fight row's only capture is 10-23; `data/scene_palettes.json` grew without gaining a drive set.

## 6. What I could not measure, and why

- **A fresh title capture.** Three attempts, all exit 4 on the idle gate (`capture_title_r11.out` and its two retries). Row
  1 is a measurement of the 05:28 frame, and I say so in the cell.
- **A live fight, walk, gate, save write or game over.** The build's own log reaches `:204` and then `###game_end###254`.
- **Whether the drive cue would resolve after a further second.** The game closed itself at `:212`; `:204` is a request
  line, not a final answer, and I am not claiming the cue never loads.
- **The two Pine reds on Linux.** I classified them on Windows, not on Pine: 34 passed locally, so I can say they are not
  Windows defects. Whether the committed PNGs are byte-stable across zlib versions is a separate question no run today
  answered.

## 7. Q: for gamedev

1. Carried and still unanswered from `t_f034f9d0` since 10-23: is the drive graded, non-NES art that needs `ART-BIBLE.md`
   RULE 0 point 1 amended, or is it quantized like the rest? 0 of 12 frames are legal today (`png_r11.out`) and
   `data/scene_palettes.json` has 12 sets and no drive entry (`palette_probe.py`).
2. New: the log asks for `pp_drive_v2.ogg` and the file is on disk but untracked (`build/last-igor.log:204`,
   `git ls-files --error-unmatch`). Is PP-02 the intended drive cue, and if so should the stream be committed to the
   project, or should the placeholder line come out of `data/audio.json` and the drive run on the engine loop alone?
3. New: the intro now starts without input at `:124` and finishes at `:201`, so refresh 8's question 3 is answered for this
   build. Nothing to ask here; recording it so the question is not repeated.

## 8. Check for this page

- Every row carries a file this run opened or a command it ran. Outputs in
  `<agent-runtime>\kanban\boards\nayil-ops\workspaces\t_d6d02ccb\`: `probe.py`, `probe.out`,
  `palette_probe.py`, `png_probe.py`, `png_r11.out`, `peek_palette.py`, `pine_read.py`, `board_probe.py`,
  `board_r11.out`, `kanban_copy.db`, `capture_title_r11.out`, `capture_title_r11b.out`, `capture_title_r11c.out`,
  `pine_read.py`, `pine_read2.py`, `pine_c.out`, `local_art_r11.out`.
- Pine evidence: `offload-audit-ready-1025b-0.json`, `-1.json`, `-2.json` and `offload-audit-ready-1025c-0.json`, `-1.json`,
  `-2.json` under `<workspace>\Shared\projects\arananet\pine\data\results\`, each `summary` field quoted.
- Board counts come from a byte copy of `<agent-runtime>\kanban\boards\nayil-ops\kanban.db`
  (23478272 B, 17:24) opened read-only with sqlite3 (`board_probe.py`, `board_r11.out`).
- Side effects to declare: `tools/integration_build.py` rewrote `output/PrimordialParadox/`, `build/last-build.log` and
  `build/last-igor.log`; `tools/nes_audit_all.py` rewrote `knowledge/NES-AUDIT.md` and `output/nes_audit/`; this run wrote
  `build/audit-readiness-build-2026-10-25.log`. Nothing in `data/`, `game/scripts/`, `tests/` or `README.md` was edited,
  and `READINESS-2026-10-25.md` was not touched.
- One process of mine is unaccounted for in a good way: the second Pine offload (pid 38228) had exited `completed` before
  this page was finalised, and no game window or Igor process was left from the build (`tasklist`). `capture_title.py`
  never opened a window, so there was nothing to close there.
- This page contains 0 em dashes and 0 en dashes, checked with `grep -c $'\u2014\|\u2013'` on this file at 18:16 (0 hits).
