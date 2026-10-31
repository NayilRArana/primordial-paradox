# Readiness refresh 7, 2026-10-24 21:13 to 21:25: the 22 row table re-measured

Written by audit for card `t_2daeccc6` (AUTO-AUDIT-REFRESH). Every number below came from a command this run executed on
this PC between 21:13 and 21:25 Pacific, or from a file this run opened. Worker reports, card results,
`GATE-GREEN-2026-10-24-1705.md` and the seven earlier readiness pages were not accepted as evidence. The earlier pages are
left untouched; this is a new page.

P: the 22 row table sums 57 again, mean 2.591, the sixth page in a row with no score moving (section 3 of this page).
P: the build passed and ran the game live from HEAD `f41531b`: `BUILD PASS`, exit 0, `.win` 470476 B, nothing left running (`build_r9.log`).
P: the live run went further than any earlier audit run: title, crawl finished, the crawl handed to `drive`, PP-02 requested, `car_engine_loop` played (`build/last-igor.log:206` to `:211`).
P: Pine is fully green for the first time in these pages: 1422 passed, 0 failed over three shards (12 skips in shard 0), shard 2 after one transport retry (`offload-audit-r9-0.json`, `-1.json`, `-s2-0.json`).
P: Windows is 3 reds from one cause, `pp_03_harbor_v4b.ogg` uncommitted; the v7/v8 title theme reds and the dash red are closed (`local_winonly_r9.out`, `dash_r9.out`).
P: the drive plays silent: the cue is a placeholder and `assets/audio/pp_drive_v2.ogg` does not exist (`build/last-igor.log:209`, `dash_r9.out`).

## 0. The tree this run measured

    git HEAD                       f41531b at 21:07:44 (gate log: record the TESTS-UNTRACKED-2 bypass)
    git status --porcelain         860 entries, dirty
    game/rooms                     rm_pp_boot, rm_pp_drive, rm_pp_ship, rm_pp_title (4)
    data/slice.json                1741 B 2026-10-23 06:19, sha256 a42993c7ca7245cb, route title, crawl, drive, arrival,
                                   gate, boarding, fight, save, gameover
    data/scenes/all.json           9108 B 2026-10-24 21:09, sha256 bcf231d100797080, 15 scene ids, drive_to_southampton
                                   among them (map drive_m4_corridor)
    data/scene_palettes.json       24192 B 2026-10-24 13:33, sha256 e33faeee706c7d3a, 11 entries, no drive entry
    data/maps/all.json             26649 B 2026-10-24 20:44, sha256 18aa2817dc06644f (16826 B at 13:07)
    data/dialogue/all.json         15056 B 2026-10-24 21:09, sha256 ad63e7fcf2b3804f (11547 B at 13:07)
    data/characters/party.json     295 B 2026-10-19 18:47, sha256 792079001e701035, unchanged since 10-19
    game/datafiles/sfx/sfx.json    5335 B 2026-10-24 21:12, sha256 f87b6ca379d96467, 22 cues, car_engine_loop 0.8 s
    data/nes_palette.json          13183 B 2026-10-21 19:25, sha256 2fba4fddd1bc7416, 55 distinct usable RGB
    README.md                      12887 B 2026-10-24 11:18, sha256 da4acb95e59775ca
    LICENCE                        5040 B 2026-10-23 02:21, sha256 b48d6fe2a0dbfe0b
    game/scripts                   25 folders, 25 gml files, 10694 lines (6924 on 10-22)

All from `probe.out` and `probe.py` in this run's workspace.

## 1. The build, and the game it launched

`python tools/integration_build.py` started 21:15, printed **`BUILD PASS: Igor compiled the project and launched the
game`** and `EXIT=0` at 21:17 (`build_r9.log`). The rebuilt `.win` is 470476 B at 21:15, sha256
`43354cad930846274c1a24926dea3b56e50c4d984c5f7b3b2aa1c4e2042fb763`. `tasklist` after the run counted 0 `Igor.exe` and
0 `Runner.exe`.

`build/last-igor.log` is 217 lines and this is the sequence that matters, quoted by line number:

    108  PP audio: title_theme streaming streams/title_theme_v3_126.ogg, instance 400001, gain 0.70
    109  PP audio: car_engine_loop loaded car_engine_loop.wav (0.80 s, 44100 Hz, buffer ref buffer 2)
    110  PP audio: car_engine_loop played, instance 400002
    118  PP: save read and accepted, music
    133  PP title: intro started, pan 180 steps, 24 stars, 14 crawl lines
    205  PP audio: title_theme back to full after 6 dB
    206  PP title: intro finished, starting the run in rm_pp_ship
    207  PP title: the crawl handed to the route's step drive
    209  PP audio: music cue PP-02 has no OGG yet, expected pp_drive_v2.ogg, placeholder 1
    210  PP: music PP-02 requested
    211  PP audio: car_engine_loop played, instance 400083
    213  ###game_end###254

So the slice's title to drive chain now runs unattended in a fresh build, and it stops there: no arrival walk, no gate
scene, no battle, no save written, no game over in this run.

## 2. The gates, each from this run's own output

1. `python tools/check_data.py`, **exit 0**, `check_data: all files pass` (`gate1_r9.out`).
2. `python tools/check_cleanroom.py`, **exit 0**, `check_cleanroom: no study reference, no foreign name, no foreign
   phrase, every module reviewed`, 121 OSM place names exempt (`gate2_r9.out`).
3. Pine suite, zip 40691199 B, 81 files, 3 shards (`pine_r9.log`): shard 0 **367 passed 0 failed, 12 skipped**,
   shard 1 **597 passed 0 failed**, shard 2 died on a transport error at 21:15:52
   (`pinesandbox: connection failed ... op=PUT /v1/sessions/main/files`, `offload-audit-r9-2.json`), rerun alone as
   `audit-r9-s2` at 21:18 to 21:20, **458 passed 0 failed** (`offload-audit-r9-s2-0.json`). Total **1422 passed,
   0 failed, 12 skipped**, walls 207.8 s, 127.1 s, 119.4 s. Three nodes were deselected on the far side as declared
   (`test_project.py` two, `test_mix_check_v3.py` one).
4. `python tools/nes_audit_all.py`, **exit 1**, `nes_audit_all: FAIL 184 file(s), 34 failing, 0 unmeasured`
   (`gate4_r9.out`). The 34 include `output/title_ui_preview.png` at `background_area x301, palette x7`,
   all eight `bg_battle_*_text_preview` and `_fight_preview` frames, `output/bg_battle_preview.png` at
   `background_area x117`, `output/gameover_preview.png` at `palette x4`, and the three fresh title captures at
   `2 px background_area x2, palette x1`.
5. `python -m pytest tests/test_slice_route.py -q`: **24 passed in 7.72 s**, 0 failed (`local_route_r9.out`); at 13:07
   the same file was 22 passed 2 failed, both `[drive]` rows.
6. `python -m pytest tests/test_make_title_ui.py tests/test_title_art_v2.py tests/test_look.py
   tests/test_scene_palette_set.py tests/test_nes_check.py -q`: **97 passed in 26.69 s**, 0 failed (`local_art_r9.out`).
7. `python -m pytest tests/test_project.py tests/test_build_inputs.py tests/test_test_inputs.py tests/test_sync_art.py
   -q`: **3 failed, 48 passed in 13.82 s** (`local_winonly_r9.out`), all three from one file:
   `MISSING FROM COMMIT datafiles/streams/pp_03_harbor_v4b.ogg` and `UNCOMMITTED SOURCE
   projects/primordial-paradox/assets/audio/pp_03_harbor_v4/pp_03_harbor_v4b.ogg`. The yyp contains neither
   `harbor_v4b` string, the stream exists in `game/datafiles/streams`, and the source exists in `assets/audio`
   (`dash_r9.out`).

The two reds that R6 recorded as five are closed: the yyp now contains `title_v7` and `title_v8` (`dash_r9.out`), and
`output/_eye_r10_digest.txt` is 211 lines with **0** dash lines (`dash_r9.out`), so
`test_project.py::test_no_em_or_en_dashes_anywhere` passed inside `local_winonly_r9.out`.

## 3. The 22 row table

Scale unchanged: 0 nothing, 1 spec only, 2 code or data but unproven in the game, 3 proven in the running game with a
capture or a test, 4 polished. Base is the table in `HACKATHON-AUDIT-2026-10-22.md` section 1.

| # | Subsystem | Base | 02:05 | 06:30 | 13:07 | 21:41 | 05:15 | 13:30 | Now | Evidence for the Now value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Title screen | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | Fresh this run: `python tools/capture_title.py` at 21:20 exit 0, `output/title_run_1.png` 784x759 rewritten, two frames captured, enter sent, `the game closed on request (exit code 0)` (`capture_title_r9b.out`). Measured on the viewport crop 768x720: 38 distinct RGB, 552924 of 552960 px on the 55 colour master (0.9999), 29 off-master colours, largest `#184F63` 4 px (`exact_r9b.out`). Not 4 on the 36 blended pixels; `output/nes_title_frame.png` 256x240 is 11 colours, 1.0000, dated 10-21. |
| 2 | Intro crawl | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | Live this run: `PP title: intro started, pan 180 steps, 24 stars, 14 crawl lines` then `intro finished, starting the run in rm_pp_ship` (`build/last-igor.log:133`, `:206`), with `text_blip_a` fired 69 times (`:136` to `:204`). Frames `crawl_mid.png` and `crawl_end.png` are still 10-22, 4 colours each, and the one off-master colour is `#F9F9F9` at 18423 and 21060 px of 552960 (`png_r9.out`). Not 4: the crawl text is off the palette. |
| 3 | Drive cutscene | 3 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | Live this run, first time: `the crawl handed to the route's step drive`, `PP: music PP-02 requested`, `car_engine_loop played, instance 400083` (`build/last-igor.log:207`, `:210`, `:211`). `rm_pp_drive` is 1 of 4 rooms; `drive_to_southampton` is in `data/scenes/all.json` with map `drive_m4_corridor` (`probe.out`, `cues_r9.out`). Not 4, three measured reasons: 0 of 12 native frames legal, no scene palette entry, and the cue has no OGG. |
| 4 | Overworld movement | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | Carried, not re-earned: this run's build reaches title, crawl and drive then `###game_end###254` (`build/last-igor.log:213`), so no walk is captured. The footstep evidence stays the 10-23 recorded run. |
| 5 | Maps and doors | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | `tests/test_slice_route.py` is 24 passed 0 failed (`local_route_r9.out`), including the `drive`, `arrival` and `gate` steps, and `data/maps/all.json` is 26649 B, sha256 18aa2817dc06644f (`probe.out`). Still no door traversal captured in a live run, so 2. |
| 6 | Dialogue and talk | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | `data/dialogue/all.json` 15056 B, sha256 ad63e7fcf2b3804f, written 21:09 (`probe.out`); `text_blip_a` 69 times live (`build/last-igor.log:136` to `:204`); Pine shard 0, which carries the dialogue and choice layout files, is 367 passed 0 failed (`offload-audit-r9-0.json`). |
| 7 | Battle and the talk fight | 3 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | Carried, and the carrying is visible: `output/first_fight_verify.json` says `"ok": true` but its own `checked_at` is `2026-10-23T06:31:07` while the file was rewritten today 15:06 (`probe.out`, `verify_jsons.py`), so it is a re-copy and not a new capture. This run's build never reaches a battle (`build/last-igor.log:213`). |
| 8 | Enemies | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | `output/enemies_preview_3x.png` rewritten 20:30, 464x772, 9 colours, 1.0000 on master, and gate 4 still flags it at `background_area x4, grid x1` (`png_r9.out`, `gate4_r9.out`). No enemy inside a live fight is captured. |
| 9 | Party and stats | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | `data/characters/party.json` 295 B, 10-19 18:47, sha256 792079001e701035 (`probe.out`); no open card names party or stats (`cards_r9.out`: the title search returns none). |
| 10 | Save and load | 3 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | `output/save_capture_verify.json` written 20:47 today, 20 `"ok": true` and 0 false, naming both runs muted and one slot sha (`save_capture_verify.json`, `verify_jsons.py`); live log `PP: save read and accepted, music` (`build/last-igor.log:118`). Not 4: the slice run in this build writes no save. |
| 11 | Ledger | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | The ledger tests sit in the green Pine shards (`offload-audit-r9-*.json`), but no captured run reads a ledger row back and no open card names the ledger (`cards_r9.out`). |
| 12 | Audio bus and cues | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | Live this run: `title_theme streaming ... gain 0.70`, `ducked 6 dB, gain 1.40`, `back to full after 6 dB`, `handed to the fade, the cue takes the one music source` (`build/last-igor.log:108`, `:134`, `:205`, `:208`). |
| 13 | Music per scene | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | The only music in the live run is the title theme. The drive asks and misses: `music cue PP-02 has no OGG yet, expected pp_drive_v2.ogg, placeholder 1` (`build/last-igor.log:209`), and `assets/audio/pp_drive_v2.ogg` does not exist (`dash_r9.out`). Per-scene music is therefore requested but not playable. |
| 14 | SFX | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | The gap R6 recorded is closed and measured: `game/datafiles/sfx/sfx.json` holds 22 cues including `car_engine_loop` 0.8 s at 44100 Hz, and the live log loads and plays it twice (`build/last-igor.log:109`, `:110`, `:211`; `game/datafiles/sfx/sfx.json`). Stays 3, not 4: this run measured the cue set and the two live plays, not the ear pass on the slice. |
| 15 | UI windows and menus | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | `ui_battle_preview.png` and `ui_dialogue_preview.png` are 5 colours, 1.0000 (`png_r9.out`), but `title_ui_preview.png` was rewritten 20:24 and is 1920x784, 9 colours, **0.0109** on master with gate 4 at `background_area x301, palette x7` (`png_r9.out`, `gate4_r9.out`). A preview is not a live window. |
| 16 | Art pipeline | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | Re-earned on Windows this run: the five art test files are **97 passed, 0 failed in 26.69 s** (`local_art_r9.out`). Not 4: the pipeline's own drive frames are 0 of 12 legal (`png_r9.out`). |
| 17 | Sprites per character | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | `output/chars_contact.png` 736x2768, 22 colours, 1.0000, still dated 10-22 02:40 (`png_r9.out`, `probe.out`). Card `t_858c2908` (the car, Ronan, Theo, the storm cloud) is now **done** (`cards_r9.out`), but no contact sheet was regenerated, so the row is not re-earned by this run. |
| 18 | Backgrounds per scene | 2 | 3 | 2 | 2 | 2 | 2 | 2 | 2 | `output/bg_battle_preview.png` is 1.0000 on the PNG itself, but gate 4 fails it at `background_area x117` and all eight `bg_battle_*_text_preview` and `_fight_preview` frames at 3 to 7 `background_area` plus `palette x4` (`gate4_r9.out`). No battle is reached live, so this is carried. |
| 19 | Build and packaging | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 21:15 to 21:17, **`BUILD PASS`**, exit 0, `.win` 470476 B sha256 43354cad930846274c1a24926dea3b56e50c4d984c5f7b3b2aa1c4e2042fb763, 0 `Igor.exe` and 0 `Runner.exe` left (`build_r9.log`). Not 4: no zip, no install step, runner still the 7941704 B exe of 10-20. |
| 20 | Tests and gates | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | Pine **1422 passed 0 failed** (12 skips in shard 0), all shards completed (`offload-audit-r9-*.json`); gates 1 and 2 exit 0 (`gate1_r9.out`, `gate2_r9.out`); gate 4 exit 1 on 34 of 184 (`gate4_r9.out`); Windows **3 reds, one uncommitted file** (`local_winonly_r9.out`). The best suite state in these pages, but the gate chain is still red, so not 3. |
| 21 | Capture and demo tooling | 3 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | `tools/capture_title.py` ran clean at 21:20: two frames, enter sent, game closed code 0 (`capture_title_r9b.out`); the first attempt at 21:19 was refused on the idle gate at `input 113 s ago, 120 s required`, exit 4 (`capture_title_r9.out`). `output/demo/run_002_verify.json` still says `"audio": "rendered stand-in from run_002_audio.m4a, not the game's live output"`, `run_002.mp4` is 10-23 01:49 and there is no `run_003` (`probe.out`). |
| 22 | Docs and repo hygiene | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | `README.md` 12887 B, `LICENCE` 5040 B, `CREDITS.md` 14394 B, all at the root (`probe.out`), 0 dash lines in all three checked documents (`dash_r9.out`). Not 4: `README.md:26` still reads `shot list and generator, no room yet` for the drive while `rm_pp_drive` is 1 of 4 rooms and this build's live run enters the drive step (`README.md:26`, `build/last-igor.log:207`). |

Rows 22, sum **57**, mean **2.591**. The columns read 53 at 02:05, then 57 at 06:30, 13:07, 21:41, 05:15, 13:30 and 57
now. Rows that moved against the 13:30 page: **none**. Every row's value below is the one that page recorded, except
row 14, whose recorded reason changed from a missing cue to a cue that loads and plays.

## 4. What moved, and what did not, with the command behind each

No score moved, for the sixth page running. Seven things moved underneath the scores:

- **The live run got three steps further than any earlier audit run.** The crawl finished and handed to `drive`, PP-02
  was requested, and the engine loop played (`build/last-igor.log:206` to `:211`). At 13:09 the same build stopped at
  `rm_pp_title` and the main loop.
- **The drive step resolves.** `tests/test_slice_route.py` is 24 passed 0 failed against 2 failed 22 passed at 13:07, and
  all three of `DRIVE-SCENE` (`t_c27552e3`), `DRIVE-MAP` (`t_e8a8f18a`) and `REVIEW-R21-DRIVE` (`t_3cca8576`) are done
  on the board (`local_route_r9.out`, `cards_r9.out`).
- **The Pine suite went from 3 reds to 0.** 13:07 was 1324 passed 3 failed; this run is 1422 passed 0 failed over
  three completed shards (`offload-audit-r9-*.json`). The 13:07 reds were 2 `test_slice_route[drive]` rows and the dash
  row, and both are closed in rows above.
- **The title theme sources landed.** The yyp now lists `title_v7` and `title_v8` (`dash_r9.out`), which closes the five
  reds R6 grouped under that cause and answers half of the question card `t_16417018` asks.
- **The dash red was fixed at the source, not in the test.** `output/_eye_r10_digest.txt` went from 2 dash lines at
  17:01 to 0 dash lines, tested over 211 lines (`dash_r9.out`); the test file itself is unchanged in this run's output
  (`local_winonly_r9.out`).
- **A new uncommitted build input replaced the old one.** `pp_03_harbor_v4b.ogg` is in `game/datafiles/streams` and in
  neither the yyp nor the commit (`local_winonly_r9.out`, `dash_r9.out`). The same class of red as v7/v8, one file later.
- **A fresh title capture exists for the first time since 05:08.** 21:20, exit 0, two frames, viewport score 1.000
  (`capture_title_r9b.out`). Its measured legality is 0.9999 with 36 blended pixels, the same shape as the 05:08 frame,
  so the row does not move.

## 5. The top five blockers to the playable slice, with the card that owns each

1. **The drive has no palette set and its art is outside the console.** 12 of 12 native frames in `output/drive_frames/`
   are at 0.0000 to 0.0167 legal against the 55 colour master, with `#081420` the largest offender in eight of them
   (`png_r9.out`); `data/scene_palettes.json` holds 11 entries and no drive entry (`probe.out`). Covered by
   `t_f034f9d0` (Q for gamedev, blocked, open since 10-23), `t_ce63cb65` DRIVE-GRID (gamedev, ready, p60) and
   `t_af836a62` DRIVE-TILE-WIRE (gamedev, running). Uncovered: the palette set itself, which `ART-BIBLE.md` RULE 0
   point 1 makes a spec, and which has been asked in `t_f034f9d0` with no gamedev answer. Proposed card, owner gamedev:
   `DRIVE-PALETTE-SET: a drive entry in data/scene_palettes.json plus 12 of 12 shots inside it, with the measured legal
   fraction per shot as the acceptance`.
2. **The drive plays silent and the cue file does not exist.** `build/last-igor.log:209` says
   `music cue PP-02 has no OGG yet, expected pp_drive_v2.ogg, placeholder 1`, and `assets/audio/pp_drive_v2.ogg` is
   absent (`dash_r9.out`). No open card names drive music (`cards_r9.out`: title search for drive music returns none).
   Proposed card, owner musician: `DRIVE-CUE-OGG: pp_drive_v2.ogg rendered, listed in data/audio.json and the yyp, and
   the live log stops printing "no OGG yet, placeholder 1"`.
3. **One uncommitted stream keeps the Windows suite red.** `pp_03_harbor_v4b.ogg` is in `game/datafiles/streams`, its
   source is in `assets/audio/pp_03_harbor_v4/`, the yyp lists neither, and that single file produces all three Windows
   reds (`local_winonly_r9.out`, `dash_r9.out`). No open card names the file; `t_c31f9295` (audit, blocked) names four
   audio sources in three directories, so its count is now stale against this measurement. Proposed card, owner
   builder with musician on the asset: `HARBOR-V4B-LAND: the file committed or removed with its source, and
   tests/test_build_inputs.py green on Windows`.
4. **The judged video's audio is a stand-in and the video is two days old.** `run_002_verify.json` says `"ok": true` and
   `"audio": "rendered stand-in from run_002_audio.m4a, not the game's live output"`; `run_002.mp4` is 10-23 01:49,
   4453751 B, and `output/demo/` holds no `run_003` (`probe.out`, `verify_jsons.py`). No open card owns the recorder's
   audio (`cards_r9.out`: the demo audio search returns none). Proposed card, owner testing: `DEMO-AUDIO-LIVE: one
   recorded run whose audio track is the game's own output, with the verifier's audio field reading live and not
   stand-in`.
5. **Gate 4 is red on 34 of 184 files and nothing owns the list.** The worst are `output/title_ui_preview.png`
   (`background_area x301, palette x7`, measured 0.0109 on master), `output/music_style_bible_preview.png`
   (`background_area x9694, palette x61`) and all eight `bg_battle_*` frames (`gate4_r9.out`, `png_r9.out`). Covered
   only in part by `t_a5e0d631` ART-REPRO-TITLE (code-review, blocked), which is about reproducing the title and UI
   PNGs, not about the scan. Proposed card, owner testing: `NES-GATE-TRIAGE: the 34 gate 4 findings split into sheet
   and preview files that the rule should exempt and frames that must be fixed, with the exempt list written into
   tools/nes_audit_all.py`.

Outside the five and still true: `README.md:26` still tells a reader the drive has no room while this build walks into it
(`README.md:26`, `build/last-igor.log:207`); no open card names party stats or the ledger (`cards_r9.out`); the battle
row's only evidence is a JSON file whose own timestamp is 10-23 (`verify_jsons.py`).

## 6. What I could not measure, and why

- **A live walk, battle or save in the slice.** This run's build stops after the drive with `###game_end###254`
  (`build/last-igor.log:213`). Rows 4, 5, 7, 8 and 18 are carried and say so.
- **The first capture attempt.** `capture_title.py` refused at 21:19 with `input 113 s ago, 120 s required`, exit 4
  (`capture_title_r9.out`). The second attempt at 21:20 passed the gate on its own terms and captured
  (`capture_title_r9b.out`). I did not work around the gate.
- **The three nodes Pine deselects.** Two of `test_project.py` and one of `test_mix_check_v3.py` ran on Windows inside
  `local_winonly_r9.out`, which is where this run's 3 reds come from.
- **Pine shard 2 on the first attempt.** The remote closed the connection during upload at 21:15:52
  (`offload-audit-r9-2.json`), which is a transport error and not a verdict; the rerun completed 458 passed 0 failed.

## 7. Q: for gamedev

1. Carried and still unanswered from `t_f034f9d0`: is the drive a graded, non-NES look that needs `ART-BIBLE.md` RULE 0
   point 1 amended, or quantized like the rest, with `output/drive/pp_drive_shot_03_1x_ppu.png` (7 colours, 1.0000) as
   the pattern for all twelve (`png_r9.out`)?
2. New: the drive cue expects `pp_drive_v2.ogg` and the file does not exist (`build/last-igor.log:209`). Is PP-02 the
   intended drive cue, in which case musician renders it to that name, or is the drive meant to run on the engine loop
   alone with the cue removed from `data/audio.json`?
3. Narrowed from R6: `pp_01_title_v7.ogg` and `pp_01_title_v8.ogg` are now listed in the yyp (`dash_r9.out`), so the
   tree has answered the mechanical half of `t_16417018`. What is left is gamedev's call on whether they are the
   accepted title theme.

## 8. Check for this page

- Every row carries a file this run opened or a command it ran. This run's outputs are in
  `<agent-runtime>\kanban\boards\nayil-ops\workspaces\t_2daeccc6\`: `probe.out`, `probe.py`,
  `board_r9.out`, `cards_r9.out`, `verify_jsons.py`, `png_r9.out`, `exact_r9.out`, `exact_r9b.out`, `dash_r9.out`,
  `cues_r9.out`, `build_r9.log`, `gate1_r9.out`, `gate2_r9.out`, `gate4_r9.out`, `local_route_r9.out`,
  `local_art_r9.out`, `local_winonly_r9.out`, `capture_title_r9.out`, `capture_title_r9b.out`, `pine_r9.log`,
  `pine_s2_r9.log`, `pine_read_r9.out`.
- The Pine evidence is `offload-audit-r9-0.json`, `-1.json`, `-2.json` and `offload-audit-r9-s2-0.json` under
  `<workspace>\Shared\projects\arananet\pine\data\results\`, read by `pine_read_r9.py`.
- Board statuses in section 5 come from `nayil-ops\kanban.db` opened read-only at 21:17 (`board_r9.py`, `cards_r9.py`),
  which read 83 open cards; a second read at 21:24 gave 66 blocked, 10 todo, 3 running, 3 ready, 858 done and 583
  archived (`dashcheck_r7.out`). The two reads differ because other workers moved cards between them.
- Side effects to declare, all of them what the tools write on every run: `tools/nes_audit_all.py` rewrote
  `knowledge/NES-AUDIT.md`, the per-file reports under `output/nes_audit/` and `output/nes_audit_worst_3x.png`; the build
  rewrote `output/PrimordialParadox/` and `build/last-igor.log`; `capture_title.py` rewrote `output/title_run_1.png`,
  `output/title_run_2.png` and `output/title_run_reference_3x.png`; the Pine tool wrote its four result JSON files. The
  pytest runs rewrote `game/datafiles/sfx/` mirrors as their setup always does. Nothing in `data/`, `game/scripts/` or
  `tests/` was edited by this run.
- Another worker (`t_af836a62`, DRIVE-TILE-WIRE) was running in this same tree throughout: `output/drive_frames/` was
  rewritten at 21:11 and `data/scenes/all.json` and `data/dialogue/all.json` at 21:09, all before my first probe at
  21:14. The measurements above are of that snapshot plus nothing after it; I did not edit any of those files.
- This page contains 0 em dashes and 0 en dashes, checked by `dashcheck_r7.py` on this file.
