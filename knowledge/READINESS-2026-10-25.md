# Readiness refresh 8, 2026-10-25 05:17 to 05:36: the 22 row table re-measured

Written by audit for card `t_6a9da6b5` (AUTO-AUDIT-REFRESH). Every number below came from a command this run ran on this
PC between 05:17 and 05:36 Pacific, or from a file this run opened. Worker reports, card results, `GATE-GREEN-2026-10-25.md`
and the seven earlier readiness pages were not accepted as evidence. The earlier pages are untouched; this is a new page.

P: the 22 row table sums 57 again, mean 2.591, so no score moved for the seventh page running (section 3).
P: one row did go red and then green inside this run: at HEAD `5f290c5` the palette ground fixtures were missing from git
(`local_art_r10.out`, `local_winonly_r10.out`), and commit `546ab97` landed them at 05:22, which my rerun at `341109a`
measured green (`recheck_r10.out`, `local_art_r10b.out`).
P: the build passed and ran the game from `341109a`: `BUILD PASS`, exit 0, `.win` 471756 B sha256 `58d32f98cebeee08`
(`build_r11.log`), and nothing was left running (`tasklist` after the run, 0 `Igor.exe`).
P: the unattended run does not reach the slice: `build/last-igor.log` has 138 lines, the title theme streams at `:108`,
the save is read at `:118`, `###game_end###254` sits at `:134`, and there is no crawl, drive, walk or battle line between them.
P: Pine is 1455 passed 2 failed over three completed shards, and both reds reran alone are sandbox artifacts, quoted in
section 2 (`offload-audit-r10c-*.json`, `offload-audit-r10d-0.json`).
P: the drive is still the worst art in the tree: 0 of 12 frames legal against the 55 colour master, best 0.0167, and
`data/scene_palettes.json` has 12 scene sets and no drive entry (`png_r10.out`, `palette_probe.out`).
P: a claim in R7 is now measurably stale: `pp_drive_v2.ogg` exists twice on disk and the yyp lists it at line 2232
(`probe.out`, `game/PrimordialParadox.yyp:2232`), so "the cue file does not exist" is not true today.

## 0. The tree this run measured, and the fact that it moved

    git HEAD at 05:18    5f290c5, committed 01:39:29 (SPRITE-GROUND-TRUTH)
    git HEAD at 05:31    341109a, committed 05:22:07 (EXHAUST-LAYER)
    between them          546ab97 "TEST-INPUTS: commit the three grounds card t_19b41ab7 listed as fixtures"
    git status           1063 porcelain entries at 05:18, dirty
    game/rooms           rm_pp_boot, rm_pp_drive, rm_pp_ship, rm_pp_title (4)
    data/slice.json      1741 B 10-23 06:19 sha256 a42993c7ca7245cb, 9 steps: title, crawl, drive, arrival, gate,
                         boarding, fight, save, gameover
    data/scenes/all.json 9424 B 10-24 22:58 sha256 1eaa6519d26b25be, 15 scenes, drive_to_southampton among them
    data/scene_palettes.json 26789 B 10-25 01:26 sha256 60791ad72dec91e2, 12 scene sets, none of them the drive
    data/maps/all.json   26815 B 10-24 21:30 sha256 afd6c34b1c350837
    data/dialogue/all.json 15056 B 10-24 21:09 sha256 ad63e7fcf2b3804f
    data/audio.json      10803 B 10-24 18:34 sha256 bca8cdad21d0ae8d, 17 cues, PP-02 delivered_file
                         assets/audio/pp_drive_v2/pp_drive_v2.ogg
    data/characters/party.json 295 B 10-19 18:47 sha256 792079001e701035, unchanged since 10-19
    data/nes_palette.json 13183 B, 55 usable RGB
    README.md            12887 B 10-24 11:18 sha256 da4acb95e59775ca; LICENCE 5040 B; CREDITS.md 14394 B
    game/scripts         25 folders, 10752 gml lines (10694 on 10-24, 6924 on 10-22)

All from `probe.py` and `palette_probe.py` in this run's workspace.

The moving HEAD is the most important fact on this page: two of this run's own measurements disagree because a worker
committed between them, and section 2 says which HEAD each one is against.

## 1. The build, and the game it launched

Three attempts, and the first two failed for reasons that are about my own concurrency, not the project:

1. 05:17 attempt one started, compiled (`output/PrimordialParadox/PrimordialParadox.win` 471756 B written 05:25), launched
   the game, and Igor then held `build/last-igor.log` for about eight minutes without returning (`psinfo.ps1` read Igor pid
   37864, parent `run.ps1 -SkipChecks`, started 05:17:57).
2. 05:18 attempt two died at `tools/run.ps1:37` with `Cannot remove item ... last-igor.log: The process cannot access the
   file`, `BUILD FAIL: run.ps1 exited 1` (`build_r10.log`). Attempt two wrote to the same log path as attempt one and
   clobbered it, so `build_r10.log` now holds only attempt two's failure. That verdict is not about the tree.
3. I posted `WM_CLOSE` to my own game window (`Primordial Paradox`, hwnd 2886030, class `YYGameMakerYY`, `close_game.py`),
   Igor exited, and the single clean run at 05:26 printed **`BUILD PASS: Igor compiled the project and launched the
   game`**, `EXIT=0` at 05:28 (`build_r11.log`), with `Igor finished. The game window is the only window that opened.`

Build artifacts, measured after that run: `.win` 471756 B, 05:25, sha256
`58d32f98cebeee083f4c11d87d35c539dbd7ff6fc59c77070afa32e192965128`; runner `PrimordialParadox.exe` 7941704 B, 10-20 18:28,
sha256 `5cbf3f4a9b1f4d8b`, unchanged (`probe.out`). Note the ordering: the digest is of the compile attempt one made at
05:25; the 05:28 pass did not advance the mtime, so Igor reused it rather than recompiling from scratch.

`build/last-igor.log` is 138 lines. The sequence that matters, quoted by line number (`last-igor-r11.log`):

    108  PP audio: title_theme streaming streams/title_theme_v3_126.ogg, instance 400001, gain 0.70
    118  PP: save read and accepted, music
    119  PP audio: thunder_soft loaded thunder_soft.wav (1.45 s, 44100 Hz, buffer ref buffer 1)
    120  PP audio: thunder_soft played, instance 400003
    134  ###game_end###254
    138  Igor complete.

Between `:118` and `:134` there are fourteen thunder plays and nothing else. No `intro started`, no `intro finished`, no
`handed to the route's step drive`, no music cue request, no battle, no save written. In refresh 7 the same build reached
`the crawl handed to the route's step drive` at `:207` and `car_engine_loop played` at `:211` (`READINESS-2026-10-24-R7.md`
section 1). I ended this run myself at about 140 s of game time with `WM_CLOSE`, so I cannot say the crawl would never have
started; what I can say is that no crawl line appeared in 138 lines, and that is a strict loss of reach against yesterday.

After the run: `tasklist` counted 0 `Igor.exe` and no game process (`close_game.py` after-close count, `tasklist`).

## 2. The gates, each with the HEAD it was measured against

1. `python tools/check_data.py`, **exit 0**, `check_data: all files pass` (`gate1_r10.out`).
2. `python tools/check_cleanroom.py`, **exit 0**, `check_cleanroom: no study reference, no foreign name, no foreign
   phrase, every module reviewed`, 121 OSM place names exempt (`gate2_r10.out`).
3. Pine, three attempts. Attempt one is my own error: the Hermes venv python cannot import the pinesandbox SDK, so all
   three shards returned `PineConfigError ... ModuleNotFoundError` (`offload-audit-r10-*.json`). Attempt two, run with
   `<home>/AppData/Local/Python/bin/python.exe` as the pine README says, died on upload:
   `PineCallError ... [Errno 10054] An existing connection was forcibly closed` (`offload-audit-r10b-1.json`). Attempt
   three completed: shard 0 **372 passed 0 failed**, shard 1 **605 passed 0 failed**, shard 2 **478 passed 2 failed**,
   walls 164.5 s, 141.7 s, 136.8 s, total **1455 passed, 2 failed** (`offload-audit-r10c-0.json`, `-1.json`, `-2.json`).
4. The two Pine reds are artifacts, and this run proved it by rerunning them alone at 05:30: **36 passed 2 failed**
   (`offload-audit-r10d-0.json`), and both failures name the sandbox, not the project:
   `AssertionError: git ls-files failed in ...: fatal: not a git repository`, and
   `output/cloud_sky_ground.png is not what tools/art/title_cloud_ground.py builds ... At index 36 diff: b'|' != b'w'`,
   which is the known cross-platform zlib class the pine README lists as failing on Linux by design.
5. `python -m pytest tests/test_slice_route.py -q`, **24 passed 0 failed** (`local_route_r10.out`).
6. The five art files, at `5f290c5`: **109 passed 1 failed** (`local_art_r10.out`), the red being
   `test_scene_palette_set.py::test_every_judged_rows_ground_is_a_file_a_clean_checkout_carries` with
   `['output/bg_battle_corridor_frame.png', 'output/bg_battle_deck_night_frame.png']`. The same five files at `341109a`:
   **110 passed 0 failed in 36.71 s** (`local_art_r10b.out`).
7. Windows-only group `test_project.py test_build_inputs.py test_test_inputs.py test_sync_art.py`, at `5f290c5`:
   **50 passed 1 failed** (`local_winonly_r10.out`), `test_test_inputs.py` asserting
   `MISSING FROM COMMIT output/cloud_sky_ground.png`, `... bg_battle_corridor_frame.png`, `... bg_battle_deck_night_frame.png`.
   At `341109a` the three files are in the index and my rerun of `test_scene_palette_set.py tests/test_test_inputs.py
   tests/test_build_inputs.py` is **44 passed 0 failed** (`recheck_r10.out`); `test_project.py` and `test_sync_art.py` were
   not rerun at the new HEAD, so I claim those two only from the `5f290c5` run. The `pp_03_harbor_v4b.ogg` red
   that R7 recorded as three failures did not appear in either run, and `git ls-files` still does not carry that stream
   (`git ls-files --error-unmatch game/datafiles/streams/pp_03_harbor_v4b.ogg` exits non-zero).
8. `python tools/nes_audit_all.py`, **exit 1**, `nes_audit_all: FAIL 184 file(s), 34 failing, 0 unmeasured`
   (`gate4_r10.out`), the same 184 and 34 as R7.
9. `python tools/capture_title.py`, **exit 0** at 05:28: two frames, viewport score 1.000 on both, `enter key sent`,
   `the game closed on request (exit code 0)`, pid 17800 (`capture_title_r10.out`). Its own first line is a finding:
   `P: window: moved off the primary screen to 1920,0, which is the second monitor`.

## 3. The 22 row table

Scale unchanged: 0 nothing, 1 spec only, 2 code or data but unproven in the game, 3 proven in the running game with a
capture or a test, 4 polished. Base is `HACKATHON-AUDIT-2026-10-22.md` section 1; R7 is the `Now` column of
`READINESS-2026-10-24-R7.md`.

| # | Subsystem | Base | R7 | Now | Evidence for the Now value |
| --- | --- | --- | --- | --- | --- |
| 1 | Title screen | 3 | 3 | 3 | Fresh capture 05:28 exit 0, two frames, viewport 1.000 (`capture_title_r10.out`). Measured on the crop 768x720: 35 distinct RGB, 552927 of 552960 px on the 55 colour master (0.9999), 33 off-master px in 26 colours, largest `#053E53` 2 px (`title_verify_r10.out`). Not 4 on those 33 px. |
| 2 | Intro crawl | 3 | 3 | 3 | Carried, not re-earned: this run's log has no `intro started` and no `intro finished` line in 138 lines (`last-igor-r11.log:118` to `:134`). The frames are unchanged: `crawl_mid.png` 4 RGB at 0.9667 with `#F9F9F9` 18423 px, `crawl_end.png` 0.9619 with `#F9F9F9` 21060 px (`png_r10.out`). |
| 3 | Drive cutscene | 3 | 3 | 3 | Carried, not re-earned: no drive line in this run's log (`last-igor-r11.log`). The data is there: 4 rooms including `rm_pp_drive`, `drive_to_southampton` in `data/scenes/all.json` (`probe.out`). Not 4, measured: 0 of 12 native frames legal, no drive entry in `data/scene_palettes.json` (`png_r10.out`, `palette_probe.out`). |
| 4 | Overworld movement | 3 | 3 | 3 | Carried: this run reaches neither a walk nor a room beyond the title (`last-igor-r11.log:134`). The footstep evidence stays the 10-23 recorded run. |
| 5 | Maps and doors | 2 | 2 | 2 | `tests/test_slice_route.py` 24 passed 0 failed, `data/maps/all.json` 26815 B sha256 afd6c34b1c350837 (`local_route_r10.out`, `probe.out`). No door traversal captured in a live run, so 2. |
| 6 | Dialogue and talk | 3 | 3 | 3 | `data/dialogue/all.json` 15056 B sha256 ad63e7fcf2b3804f, written 10-24 21:09 (`probe.out`); the dialogue and choice layout tests sit in the green Pine shards (`offload-audit-r10c-*.json`). No live blip line this run. |
| 7 | Battle and the talk fight | 3 | 3 | 3 | Carried and the carry is visible: `output/first_fight_verify.json` says `"ok": true` with `checked_at` `2026-10-23T06:31:07` while the file's mtime is 10-24 15:06, so it is a re-copy and not a new capture (`title_verify_r10.out`). This run's build never reaches a battle. |
| 8 | Enemies | 2 | 2 | 2 | `output/enemies_preview_3x.png` 464x772, 9 RGB, 1.0000 on master, still 10-24 20:30 (`png_r10.out`, `probe.out`), and gate 4 still flags it (`gate4_r10.out`). No enemy inside a live fight. |
| 9 | Party and stats | 2 | 2 | 2 | `data/characters/party.json` 295 B, 10-19 18:47, sha256 792079001e701035 (`probe.out`); no open card names party or stats (`cards_r10.out`, 0 hits). |
| 10 | Save and load | 3 | 3 | 3 | Live this run: `PP: save read and accepted, music` (`last-igor-r11.log:118`). `output/save_capture_verify.json` is `"ok": true` with 15 of 15 checks true, mtime 10-24 20:47 (`title_verify_r10.out`). Not 4: this build writes no save. |
| 11 | Ledger | 2 | 2 | 2 | The ledger tests sit in the green Pine shards (`offload-audit-r10c-*.json`), but no captured run reads a ledger row back and no open card names the ledger (`cards_r10.out`, 1 hit which is a code-review spec handoff). |
| 12 | Audio bus and cues | 3 | 3 | 3 | Live this run: `title_theme streaming ... gain 0.70` (`last-igor-r11.log:108`), plus the thunder load and plays (`:119` to `:133`). The bus work itself (duck, fade, one music source) is R7's live evidence, not repeated. |
| 13 | Music per scene | 2 | 2 | 2 | The only music in this run is the title theme (`last-igor-r11.log:108`). The drive cue is no longer missing from disk: `assets/audio/pp_drive_v2/pp_drive_v2.ogg` 2453706 B and `game/datafiles/streams/pp_drive_v2.ogg` 2453706 B both exist and the yyp names it at line 2232 (`probe.out`, `game/PrimordialParadox.yyp:2232`). Whether the game resolves it is unproven, because no drive was reached. |
| 14 | SFX | 3 | 3 | 3 | `game/datafiles/sfx/sfx.json` 5335 B, sha256 f87b6ca379d96467, 22 cue rows (`probe.out`); the live log loads and plays `thunder_soft` 1.450 s at 44100 Hz (`last-igor-r11.log:119`, `:120`). Not 4: no ear pass on the slice. |
| 15 | UI windows and menus | 2 | 2 | 2 | `ui_battle_preview.png` and `ui_dialogue_preview.png` are 5 RGB at 1.0000, but `title_ui_preview.png` is 1920x784, 9 RGB, **0.0109** on master with `#081420` at 1362523 px (`png_r10.out`), and gate 4 keeps it at `background_area x301, palette x7` (`gate4_r10.out`). A preview is not a live window. |
| 16 | Art pipeline | 3 | 3 | 3 | Re-earned at the HEAD this run finished on: the five art test files are **110 passed 0 failed in 36.71 s** at `341109a` (`local_art_r10b.out`). At `5f290c5`, forty minutes earlier, the same command was 109 passed 1 failed. Not 4: the pipeline's drive frames are 0 of 12 legal. |
| 17 | Sprites per character | 2 | 2 | 2 | `output/chars_contact.png` 736x2768, 22 RGB, 1.0000, still 10-22 02:40 (`png_r10.out`, `probe.out`). No contact sheet regenerated this run, so the row is not re-earned. |
| 18 | Backgrounds per scene | 2 | 2 | 2 | `bg_battle_preview.png` 1560x696, 16 RGB, 1.0000 on the PNG (`png_r10.out`), but gate 4 still fails the eight `bg_battle_*_text_preview` and `_fight_preview` frames (`gate4_r10.out`). No battle reached live. |
| 19 | Build and packaging | 3 | 3 | 3 | **`BUILD PASS`**, exit 0, after the two aborted attempts described in section 1 (`build_r11.log`); `.win` 471756 B sha256 58d32f98cebeee08, runner exe unchanged since 10-20, 0 `Igor.exe` left (`probe.out`). Not 4: no zip, no install step. |
| 20 | Tests and gates | 2 | 2 | 2 | Pine **1455 passed 2 failed** with both reds shown to be sandbox artifacts (`offload-audit-r10c-*.json`, `offload-audit-r10d-0.json`); gates 1 and 2 exit 0; gate 4 exit 1 on 34 of 184 (`gate4_r10.out`). The best suite state these pages have recorded, but gate 4 is red and the tree moved mid-run, so not 3. |
| 21 | Capture and demo tooling | 3 | 3 | 3 | `tools/capture_title.py` ran clean at 05:28 (`capture_title_r10.out`). The demo side did not move: `run_002_verify.json` still says `"audio": "rendered stand-in from run_002_audio.m4a, not the game's live output"`, `run_002.mp4` is 10-23 01:49, `run_001_verify.json` is still `"ok": false`, and there is no `run_003.mp4` (`title_verify_r10.out`, `probe.out`). |
| 22 | Docs and repo hygiene | 3 | 3 | 3 | `README.md` 12887 B, `LICENCE` 5040 B, `CREDITS.md` 14394 B at the root (`probe.out`). Not 4: `README.md:26` still reads `shot list and generator, no room yet` for a drive that has `rm_pp_drive` as 1 of 4 rooms (`README.md:26`, `probe.out`). |

Rows 22, sum **57**, mean **2.591**. Rows that moved against R7: **none**. Row 16's value was briefly earned down and
earned back inside this run, and its cell says how.

## 4. What moved underneath the scores

- **The ground fixtures landed mid-run, and I have both sides of it.** At `5f290c5` the palette rows read three `output/`
  PNGs that no commit carried, so `test_test_inputs.py` and `test_scene_palette_set.py` were red
  (`local_winonly_r10.out`, `local_art_r10.out`). Commit `546ab97` landed them at 05:22, and at `341109a` the same tests
  are 44 passed and 110 passed respectively (`recheck_r10.out`, `local_art_r10b.out`). Two other workers moved this while
  I was measuring it; the fix is real and I verified it rather than taking the card's word.
- **Reach went backwards in the unattended run.** R7's build reached the crawl handoff and the drive cue request
  (`READINESS-2026-10-24-R7.md` section 1); this build's log stops at the save read and sixteen thunder plays before
  `###game_end###254` (`last-igor-r11.log:118` to `:134`). I closed that window myself, so this is a loss of reach
  relative to yesterday, with the caveat in section 1.
- **The drive cue is on disk and in the project.** `assets/audio/pp_drive_v2/pp_drive_v2.ogg` and
  `game/datafiles/streams/pp_drive_v2.ogg` are both 2453706 B, and `game/PrimordialParadox.yyp:2232` lists
  `pp_drive_v2.ogg` (`probe.out`). R7's blocker 2, "the cue file does not exist", is stale as written.
- **A window opened on the wrong monitor.** `capture_title.py` printed `P: window: moved off the primary screen to
  1920,0, which is the second monitor` (`capture_title_r10.out`). It still captured at 1.000, but the game window is being
  placed on the second screen by whatever sets its position.
- **The build tool cannot host two builds.** Both of my first two attempts collided on `build/last-igor.log`, one holding
  it, the other failing on `Remove-Item` (`build_r10.log`, `psinfo.ps1`). Any second lane building concurrently will see a
  false `BUILD FAIL`; that is a tooling defect, not a project defect.
- **Pine's invocation matters and the README says so.** The Hermes venv python produces `ModuleNotFoundError`, the
  `AppData/Local/Python/bin/python.exe` 3.14 interpreter completes (`offload-audit-r10-*.json`, `offload-audit-r10c-0.json`).
- **The board emptied of `ready`.** 69 blocked, 9 todo, 4 running, 0 ready, 892 done, 583 archived (`board_r10.out`); R7
  read 66 blocked, 10 todo, 3 running, 3 ready (`READINESS-2026-10-24-R7.md` section 8).

## 5. The top five blockers to the playable slice, with the card that owns each

1. **The judged video still has stand-in audio and no fresh run.** `run_002.mp4` is 10-23 01:49 and its verifier records
   `"audio": "rendered stand-in from run_002_audio.m4a, not the game's live output"`; `run_001_verify.json` is
   `"ok": false`; there is no `run_003` (`probe.out`, `title_verify_r10.out`). Covered by: nothing. `cards_r10.out` has one
   demo hit, `t_030a89e5` R32 TEST-SLICE-ROUTE, which tests the route and not the recorder. Uncovered gap. Proposed card,
   owner testing: `DEMO-AUDIO-LIVE: one recorded run whose audio track is the game's own output, with
   run_003_verify.json reading audio live and ok true`.
2. **No unattended run reaches the first fight, walk, gate or save.** This run's log stops at the title
   (`last-igor-r11.log:134`); R7's stopped after the drive. The rows that depend on it (2, 3, 4, 7, 8, 18) are all carried
   from records, not re-earned. Covered in parts by `t_030a89e5` (blocked), `t_d2b724e3` GATE-CHOICE-CAPTURE (blocked),
   `t_c024f8bc` ARRIVAL-MAP (blocked). Uncovered: the reach itself, one run from title to a fight ending, on the recorded
   tree. Proposed card, owner testing: `SLICE-RUN-REACH: a build whose own log carries intro, drive, walk, gate and a
   fight ending in one run, with the line numbers named, and the ceiling stated where it still stops`.
3. **The drive has no palette set and its art is outside the console.** 0 of 12 native frames legal, 0.0000 to 0.0167,
   `#081420` the largest offender in nine of the twelve (`png_r10.out`), and `data/scene_palettes.json` holds 12 sets with no
   drive among them (`palette_probe.out`). Covered by `t_f034f9d0` (Q for gamedev, blocked since 10-23, p0). Uncovered:
   the palette set itself, which `ART-BIBLE.md` RULE 0 point 1 makes a spec. Proposed card, owner gamedev:
   `DRIVE-PALETTE-SET: a drive entry in data/scene_palettes.json plus 12 of 12 shots inside it, measured legal fraction
   per shot as the acceptance`.
4. **Gate 4 is red on 34 of 184 files and no card owns the list.** The worst measured here are `title_ui_preview.png` at
   0.0109 with `#081420` at 1362523 px, and `gameover_preview.png` at **0.0000**, 4 RGB, `#0B0B0F` at 58824 px of 61440
   (`png_r10.out`, `gate4_r10.out`). Covered only in part by `t_a5e0d631` ART-REPRO-TITLE (code-review, blocked), which is
   about reproducing title and UI PNGs, not about the scan. Proposed card, owner testing: `NES-GATE-TRIAGE: the 34 findings
   split into sheets and previews the rule should exempt and frames that must be fixed, with the exempt list written into
   tools/nes_audit_all.py`.
5. **The palette ground rule is enforced by a test that cannot run on Pine.** `test_every_judged_rows_ground_is_a_file_a_clean_checkout_carries`
   fails on Pine with `fatal: not a git repository`, while it is the only test that would have caught the three uncommitted
   grounds before they turned the suite red (`offload-audit-r10d-0.json`, `local_art_r10b.out`). Covered by `t_19b41ab7`
   PALETTE-GROUND-FIXTURES (running), which fixed the files. Uncovered: the test's own portability, and the missing
   `test_test_inputs.py` acceptance, which that card never names. Proposed card, owner builder: `GROUND-TEST-PORTABLE:
   the clean-checkout ground test skips on a git-less tree or reports UNMEASURED, and tests/test_test_inputs.py is named
   in the fix`.

Outside the five and still true: `README.md:26` still tells a reader the drive has no room (`README.md:26`); no open card
names party stats or the ledger (`cards_r10.out`); the battle row's only evidence is a JSON whose own `checked_at` is
10-23 (`title_verify_r10.out`); `pp_03_harbor_v4b.ogg` is still in no commit while no test now complains about it
(`git ls-files --error-unmatch`, `local_winonly_r10.out`).

## 6. What I could not measure, and why

- **A live walk, fight, gate, save or game over.** This build's log stops at the title (`last-igor-r11.log:134`), and I
  closed the window at about 140 s of game time. Rows 2, 3, 4, 7, 8 and 18 are carried and say so.
- **Whether the crawl would have started.** The window was mine and I closed it; the log has no crawl line either way.
- **Pine at one fixed HEAD.** The shards zipped a tree that changed under them: `5f290c5` at 05:18, `546ab97` committed
  05:22, `341109a` at 05:31 (`probe.out`, `recheck_r10.out`). Shard results are against the zip, and the zip's HEAD was not
  recorded; the two reds were rerun alone at 05:30 and classified rather than accepted.
- **The first two build attempts.** Both died on my own concurrency, one on a held log, one clobbering the other's output
  file (`build_r10.log`). Only the third attempt is a verdict.
- **Row 7's fight.** The only artifact is a 10-23 capture re-copied on 10-24; I did not rerun the capture because nothing
  in this build reaches a battle to capture.

## 7. Q: for gamedev

1. Carried and unanswered from `t_f034f9d0` since 10-23: is the drive graded, non-NES art that needs `ART-BIBLE.md`
   RULE 0 point 1 amended, or is it quantized like the rest? 0 of 12 frames are legal today (`png_r10.out`).
2. New, and it narrows R7's question: the drive cue file now exists twice and the yyp lists it (`probe.out`,
   `game/PrimordialParadox.yyp:2232`), so the render request is moot. Is PP-02 the intended drive cue, or should the
   placeholder line come out of `data/audio.json` and the drive run on the engine loop alone?
3. New: is the crawl meant to start without input? This run's log shows the title theme, the save read, then only thunder
   for the rest of the run (`last-igor-r11.log:108` to `:134`), while R7's reached `intro finished` inside the same build
   path (`READINESS-2026-10-24-R7.md` section 1). If a keypress is now required, the unattended runs everywhere will stop
   at the title.

## 8. Check for this page

- Every row carries a file this run opened or a command it ran. This run's outputs are in
  `<agent-runtime>\kanban\boards\nayil-ops\workspaces\t_6a9da6b5\`: `probe.py`, `probe.out`,
  `palette_probe.py`, `palette_probe.out`, `png_probe.py`, `png_r10.out`, `title_verify_probe.py`, `title_verify_r10.out`,
  `cards_r10.py`, `cards_r10.out`, `open_cards.py`, `board_r10.out`, `sfx_cards.py`, `card_body.py`, `psinfo.ps1`,
  `run_psinfo.py`, `winlist.py`, `close_game.py`, `build_r10.log`, `build_r11.log`, `last-igor-r11.log`,
  `gate1_r10.out`, `gate2_r10.out`, `gate4_r10.out`, `local_route_r10.out`, `local_art_r10.out`, `local_art_r10b.out`,
  `local_winonly_r10.out`, `recheck_r10.out`, `clean_r10.out`, `capture_title_r10.out`, `pine_r10.log`, `pine_r10b.log`,
  `pine_r10c.log`, `pine_r10d.log`, `head_after.out`.
- The Pine evidence is `offload-audit-r10-*.json`, `offload-audit-r10b-*.json`, `offload-audit-r10c-*.json`,
  `offload-audit-r10d-0.json` under `<workspace>\Shared\projects\arananet\pine\data\results\`, and each
  `results_txt` field is quoted rather than summarised where it matters.
- The clean-checkout cross-check is this run's own: `git archive HEAD | tar -x` at 05:30 into the scratch dir, then
  `python -m pytest tests/test_palette_synergy.py tests/test_scene_palette_set.py -q` gave **36 passed 0 failed**
  (`clean_r10.out`). That extraction also showed the test file's name differs at HEAD from the working tree, which is why
  I re-ran the same tests in the working tree at `341109a` before drawing any conclusion.
- Board counts come from `nayil-ops\kanban.db` opened read-only at 05:31 (`board_r10.out`, `cards_r10.out`).
- Side effects to declare: `tools/integration_build.py` rewrote `output/PrimordialParadox/`, `build/last-build.log` and
  `build/last-igor.log`; `tools/capture_title.py` rewrote `output/title_run_1.png`, `output/title_run_2.png` and
  `output/title_run_reference_3x.png`; `tools/nes_audit_all.py` rewrote `knowledge/NES-AUDIT.md` and the reports under
  `output/nes_audit/`; the pytest runs rewrote `game/datafiles/sfx/` mirrors as their setup always does; the Pine tool wrote
  its result JSONs. `output/drive_frames/*.png` were rewritten at 05:17 by another lane, before my first probe at 05:18; I
  measured that snapshot and edited none of it. Nothing in `data/`, `game/scripts/` or `tests/` was edited by this run.
- Two processes of mine were involved and are gone: Igor pid 37864 (my 05:17 build) closed by `WM_CLOSE` on my own game
  window, and capture game pid 17800 exited code 0 (`close_game.py`, `capture_title_r10.out`).
- This page contains 0 em dashes and 0 en dashes, checked by `dashcheck_r10.py` on this file.
