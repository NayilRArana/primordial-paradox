# Readiness refresh 10, 2026-10-25 21:26 to 21:50: the 22 row table re-measured

Written by audit for card `t_2cc56615` (AUTO-AUDIT-REFRESH). Every number below came from a command this run ran on this
PC between 21:26 and 21:50 Pacific, or from a file this run opened. Worker reports, card results and the earlier readiness
pages were not accepted as evidence. `READINESS-2026-10-25-R2.md` (refresh 9) is untouched; this is a new page and its
`Before` column is that page.

The tree this run measured: HEAD `080dc56` "SHIP-ROWS-PINNED: the ship's palette rows stay, and the file now says a solve
may not move them (card t_23b5739a)", committed 21:03:37, 1259 dirty porcelain entries, and HEAD moved again to `6456593`
at 21:36 in the middle of this run (`git rev-parse --short HEAD`, `git status --porcelain`). Refresh 9 finished on
`29128aa` at 18:05, so 20 commits and about 3.5 hours separate the two pages.

P: the table does not hold this time. Two rows drop, from 57 to 55, mean 2.5, and both drops are measured negative
evidence rather than a missing re-earn (`READINESS-2026-10-25-R2.md` before column, this page's section 3).
P: the biggest mover is row 7, the battle: a **fresh** capture exists, `output/first_fight_verify.json` written
18:15:50 today, and it is `"ok": false` with 5 of its 7 checks not true, 0 frames carrying the battle box, and no
`PP: battle start` line in 168 log lines (`output/first_fight_verify.json`).
P: row 3, the drive, drops because its one piece of live evidence did not repeat and the art under it is outside the
palette: 12 of 12 `output/drive_frames/*.png` are illegal, share 0.0000 to 0.0167, `#081420` the largest offender in 8
of 12, and `data/scene_palettes.json` still has 0 occurrences of "drive" (`png_r13.out`, `grep -c drive`).
P: the Pine suite is **1547 passed, 0 failed** across three shards, the best this table has recorded, against refresh 9's
1484 passed and 2 failed (`pine_r13b.log`, `offload-audit-ready-1025e-*.json`). Shard 1 alone is 471 passed 0 failed 21
skipped in 25.63 s.
P: the build step did not return at all this cycle, twice, and the reason is in the script: `Start-Process ... -Wait`
with no timeout (`tools/run.ps1:187`). Attempt 2 has run since 21:33:49, its log reached **178 lines by 21:44** and grew
after that, and it has not printed `BUILD PASS` (`build/audit-readiness-build-2026-10-25-R3b.log`,
`last-igor-snapshot.log`).
P: the capture harness worked where the build did not: `tools/capture_title.py` exited 0, wrote two 784x759 frames, scored
the viewport 1.000 twice and closed the game on request (`capture_title_r13.out`), and the fresh crop is legal to
**0.9999** on the 2C02 master, 36 off-master pixels in 32 colours, largest `#063F57` at 2 px (`title_run_reference_3x.png`).

## 0. What this run measured, in one place

| Measurement | Command or source | Result |
| --- | --- | --- |
| HEAD at start and at end | `git rev-parse --short HEAD` | `080dc56` 21:03:37, then `6456593` 21:36:20 |
| Dirt | `git status --porcelain` | 1259 entries |
| Build attempt 1 | `python tools/integration_build.py` | cut by this shell at 420 s, log 0 bytes, no verdict (`build/audit-readiness-build-2026-10-25-R3.log`) |
| Build attempt 2 | same, background, started 21:33:49 | no `BUILD PASS` at 21:44, **178 lines** in `build/last-igor.log` and still growing, Igor still alive (`build/audit-readiness-build-2026-10-25-R3b.log`, `last-igor-snapshot.log`) |
| The wait that never ends | `grep -nE "Start-Process|Wait-|ExitCode" tools/run.ps1` | `:187` `Start-Process ... -PassThru -Wait`, no timeout anywhere in 197 lines (`tools/run.ps1`) |
| What the build did reach | `build/last-igor.log`, frozen by this run at 21:44 into `knowledge/igor-log-2026-10-25-2144.log` (178 lines) | `:108` title theme streaming, `:111` title room live, `:118` save read and accepted, `:143` to `:145` a pause and its unregister, `:147` focus back with music resumed; `grep -c intro` returns **0** (`knowledge/igor-log-2026-10-25-2144.log`) |
| Compiled artifact | `ls -la output/PrimordialParadox/*.win` | `PrimordialParadox.win` 477772 B, 21:33, rebuilt by attempt 1; exe 7941704 B, Oct 20 18:28 |
| Left behind | `tasklist` at 21:46, after I stopped the runaway build | no `Igor.exe` and no `PrimordialParadox.exe`; the capture had already closed the game it found (`tasklist`) |
| Pine suite | `python pine_offload.py --shards 3 --name audit-ready-1025e` | 471 + 536 + 540 = **1547 passed, 0 failed**, 21 skipped in shard 1, 3 nodes deselected by name (`pine_r13b.log`) |
| The Pine trap | first attempt with the Hermes venv python | all three shards `error` in 4 s, the SDK is not importable there; rerun with `AppData/Local/Python/bin/python` worked (`offload-audit-ready-1025d-*.json`, `pine_r13b.log`) |
| Title capture | `python tools/capture_title.py` | exit 0, `title_run_1.png` and `title_run_2.png` 784x759, viewport score 1.000 twice, `the game closed on request (exit code 0)` (`capture_title_r13.out`) |
| The capture's own P line | `capture_title_r13.out` | `P: window: moved off the primary screen to 1920,0, which is the second monitor` |
| Fresh title frame legality | Pillow over `output/title_run_reference_3x.png` | 768x720, 41 RGB, share **0.9999**, 36 off-master px in 32 colours, largest `#063F57` 2 px (`title_probe.py` output) |
| Window frame legality | Pillow over `title_run_1.png`, `title_run_2.png` | 784x759, 4716 and 5255 RGB, share 0.9294, off-master chrome `#F9F1ED` 7907 px (desktop behind the window) |
| Committed title frame | `output/nes_title_frame.png` | 256x240, 11 RGB, share 1.0000 |
| Fight capture | `output/first_fight_verify.json` | **ok false**, `checked_at 2026-10-25T18:15:50`, 5 of 7 checks not true, video h264 768x720 60 fps (`ff_probe.py`) |
| The five red checks | `output/first_fight_verify.json` | `battle_box_in_sample` frames 0, `fight_command_in_sample` frames 0, `victory_text_in_sample` frames 0, `battle_start_in_log` count 0, `video` (`ff_probe.py`) |
| Drive frames | Pillow over `output/drive_frames/*.png`, 12 files, mtime 21:22 | **0 of 12 legal**, share 0.0000 to 0.0167, `#081420` the largest offender in 8 of 12 (`png_r13.out`) |
| Battle strips | Pillow over `output/bg_battle_*_frame.png`, mtime 19:14 | 4 of 4 legal at 1.0000, 7 to 9 RGB (`png_r13.out`) |
| The battle previews that are not | Pillow over `output/bg_battle_*_text_preview.png` and `*_fight_preview.png` | share 0.2222 and 0.4222, `#1C1C24` the offender in all eight (`png_r13.out`) |
| The two red previews | `title_ui_preview.png`, `gameover_preview.png` | share 0.0109 (`#081420` 1362523 px) and 0.0000 (`#0B0B0F` 58824 px), mtimes 10-24 20:24 and 10-22 20:46 (`png_r13.out`) |
| New town art | `output/{southampton,westminster,winchester}_sample_frame*.png`, 19:28 | 9 to 10 RGB, share 1.0000 on every frame and preview (`png_r13.out`) |
| Gate 1 | `python tools/check_data.py` | exit **0**, `check_data: all files pass` |
| Gate 2 | `python tools/check_cleanroom.py` | exit **0**, `no reference, no foreign name, no foreign phrase, every module reviewed` |
| Gate 4 | `python tools/nes_audit_all.py` | exit **1**, `183 file(s), 35 failing, 0 unmeasured`, up from 34 failing at refresh 9 (`nesaudit_r13.out`) |
| Rooms | `ls game/rooms` | 4: `rm_pp_boot`, `rm_pp_drive`, `rm_pp_ship`, `rm_pp_title` |
| GML size | walk over `game/scripts` | 25 files, 10905 lines, 25 folders, up 153 lines since refresh 9 |
| Slice route | `data/slice.json` 1741 B sha `a42993c7ca7245cb`, unchanged 10-23 06:19 | 9 steps: title, crawl, drive, arrival, gate, boarding, fight, save, gameover (`slice_probe.py`) |
| Scenes | `data/scenes/all.json` 9424 B sha `1eaa6519d26b25be` | 15, `drive_to_southampton` among them |
| Scene palette sets | `data/scene_palettes.json` 36606 B sha `dfb5b6a6e57c80bb`, mtime 21:25 | 12 sets, 0 occurrences of "drive"; grew 5970 B since 17:24 with no new set |
| The README's drive line | `README.md:26` | still `shot list and generator, no room yet`, while `rm_pp_drive` is 1 of 4 rooms |
| Root docs | `ls` | `README.md` 12887 B, `LICENCE` 5040 B, `CREDITS.md` 14394 B |
| Board | read-only copy of `boards/nayil-ops/kanban.db`, 24264704 B at 21:36 | 948 done, 587 archived, **67 blocked, 10 todo, 5 running, 2 ready** (`board_probe.py`) |

No key or login file was opened, and no value from one appears anywhere on this page. Only paths, sizes, digests, log
lines, pixels and test output appear here.

## 1. The build, and why it has no verdict

Two attempts, neither returned, and the second is still open at the time of writing.

Attempt 1: `python tools/integration_build.py` from 21:26:00. The shell cut it at 420 s. Because the child's stdout was
block-buffered into a file, the log holds 0 bytes, and I will not read a buffered-away run as a fail
(`build/audit-readiness-build-2026-10-25-R3.log`).

Attempt 2: the same command, unbuffered (`python -u`), started 21:33:49 in the background
(`build/audit-readiness-build-2026-10-25-R3b.log`). At 21:44 it holds one timestamp and nothing else, which is the whole
trouble: the shell that started it has nothing to show. Igor is alive (pid 3176) and `build/last-igor.log` had grown to
178 lines, and kept growing after I froze a copy of it (`last-igor-snapshot.log`).

What those 178 lines say, with line numbers exact in that snapshot:

    108  PP audio: title_theme streaming streams/title_theme_v3_126.ogg, instance 400001, gain 0.70
    111  PP title: room rm_pp_title live, screen owned by obj_pp_title
    118  PP: save read and accepted, music
    143  Pause event has been registered for this frame
    144  PP audio: focus lost, music paused (cue and theme) and every effect stopped
    145  Pause event has been unregistered
    147  PP audio: focus back, music resumed where it stopped

`grep -nE "intro|crawl|battle start|PP-02|game_end"` over that snapshot returns nothing, and `grep -c intro` returns **0**
(`last-igor-snapshot.log`). Refresh 9's build of the same
project reached `PP title: intro started, pan 180 steps, 24 stars, 14 crawl lines` at 71 s (`READINESS-2026-10-25-R2.md`
section 1). Mine did not, and the difference is not a mystery in the code: the intro only starts when `pp_title_select`
takes the `NEW GAME` row (`game/scripts/pp_title/pp_title.gml:419`), which is an input event, so an unattended launch
depends on something sending that key. `tools/capture_title.py` sends an enter and got two frames; the build step sends
nothing and waits (`tools/run.ps1:187`).

The verdict on row 19 is therefore: **compiled and launched, not returned**. The `.win` was rebuilt at 21:33 (477772 B),
the game ran and logged its own audio and save lines, and no `BUILD PASS` was ever printed. I do not score that as a pass,
and I do not score it as a fail either: it is the third case, and it is the case that matters to the gate, because a gate
step that cannot return cannot report anything.

At 21:46 I stopped the runaway attempt rather than leave it running past this audit: the python parent was killed through
this session's process handle, and `tasklist` straight after shows no `Igor.exe` and no `PrimordialParadox.exe`. Nothing of
mine is left open, and the build's own log still holds nothing but its start timestamp, which is the last word on it
(`build/audit-readiness-build-2026-10-25-R3b.log`).

## 2. The Pine suite, and the trap that ate one attempt

Attempt 1 used the Hermes venv interpreter and every shard died in about four seconds with `error`
(`offload-audit-ready-1025d-0.json`, `-1`, `-2`). That is the trap refresh 9 wrote down and it still costs a run: the
pinesandbox SDK lives in `AppData/Local/Python/bin/python` only.

Attempt 2 with that interpreter, `--shards 3 --name audit-ready-1025e`:

| Shard | Result | Finished |
| --- | --- | --- |
| `audit-ready-1025e-0` | 540 passed, 0 failed | 21:41:30 |
| `audit-ready-1025e-1` | 471 passed, 0 failed, 21 skipped | 21:39:33 |
| `audit-ready-1025e-2` | 536 passed, 0 failed | 21:39:53 |

1547 passed, 0 failed (`pine_r13b.log`). Three nodes were deselected on the far side by name and the run says why for each
(`pine_r13b.log`): `test_mix_check_v3.py::test_the_script_still_runs_on_a_slice` needs two renders totalling 16,752,241
bytes; `test_project.py::test_generated_project_files_are_current` and `::test_project_graph_matches_disk` need 30 stream
sources the zip drops. `tests/test_build_inputs.py` and `tests/test_test_inputs.py` were not offloaded because they shell
out to git. Those five are on the Windows suite, not measured by this run.

This is the one unambiguous gain of the cycle: refresh 9 carried 2 reds and proved both to be Linux artefacts by a Windows
rerun; tonight there is nothing to explain.

## 3. The table, before and after

Scale unchanged: 0 nothing, 1 spec only, 2 code or data but unproven in the game, 3 proven in the running game with a
capture or a test, 4 polished. `Before` is `READINESS-2026-10-25-R2.md`.

| # | Subsystem | Before | After | Evidence measured this run |
| --- | --- | --- | --- | --- |
| 1 | Title screen | 3 | 3 | Fresh capture 21:38, exit 0, viewport score 1.000 twice; crop 768x720 41 RGB share 0.9999, 36 off-master px (`capture_title_r13.out`, `title_run_reference_3x.png`) |
| 2 | Intro crawl | 3 | 3 | Carried, **not re-earned**: no intro line anywhere in the 178 line snapshot of my build's log (`last-igor-snapshot.log`) |
| 3 | Drive cutscene | 3 | **2** | **Dropped.** No live handoff this run, `data/scene_palettes.json` has 0 drive sets, and 12 of 12 `output/drive_frames/*.png` are illegal, share 0.0000 to 0.0167 (`png_r13.out`) |
| 4 | Overworld movement | 3 | 3 | Carried: no footstep and no walk line in my log, so not re-earned (`build/last-igor.log`) |
| 5 | Maps and doors | 2 | 2 | New town data renders legal: southampton, westminster, winchester frames and previews all share 1.0000, 19:28 (`png_r13.out`); still no door traversal captured |
| 6 | Dialogue and talk | 3 | 3 | Carried, not re-earned: `grep -c text_blip` on the 178 line snapshot returns 0 (`last-igor-snapshot.log`) |
| 7 | Battle and the talk fight | 3 | **2** | **Dropped.** `output/first_fight_verify.json` `ok: false` at 18:15:50, 5 of 7 checks false, 0 frames with the battle box, no `PP: battle start` in 168 lines (`ff_probe.py`) |
| 8 | Enemies | 2 | 2 | `enemies_preview_3x.png` 464x772 9 RGB share 1.0000, regenerated 17:23; no live encounter (`png_r13.out`) |
| 9 | Party and stats | 2 | 2 | No new test and no capture; `output/sprites_v2_sheet.png` 640x832 11 RGB share 1.0000, 19:32, is art not stats (`png_r13.out`) |
| 10 | Save and load | 3 | 3 | **Re-earned live**: `PP: save read and accepted, music` at `:118` of my build (`build/last-igor.log`) |
| 11 | Ledger | 2 | 2 | `grep -c ledger` on the 178 line snapshot returns 0, and no capture reads a ledger row back (`last-igor-snapshot.log`) |
| 12 | Audio bus and cues | 3 | 3 | **Re-earned live**: title theme streaming `:108`, and `focus back, music resumed where it stopped` `:147` (`knowledge/igor-log-2026-10-25-2144.log`) |
| 13 | Music per scene | 2 | 2 | Not measurable this cycle: my log never reached the drive handoff, so `grep -c PP-02` returns 0 (`knowledge/igor-log-2026-10-25-2144.log`) |
| 14 | SFX | 3 | 3 | **Re-earned live**: `thunder_soft played` instances 400001 to 400057 in the frozen 178 line log (`knowledge/igor-log-2026-10-25-2144.log`) |
| 15 | UI windows and menus | 2 | 2 | `ui_battle_preview` 5 RGB 1.0000, `ui_dialogue_preview` 5 RGB 1.0000; `title_ui_preview` 0.0109 is the red one (`png_r13.out`) |
| 16 | Art pipeline | 3 | 3 | **Re-earned with no caveat for the first time**: Pine 1547 passed 0 failed, and the town and battle renders are legal (`pine_r13b.log`, `png_r13.out`) |
| 17 | Sprites per character | 2 | 2 | `chars_contact.png` 736x2768 25 RGB 1.0000, `sprites_v2_sheet.png` 11 RGB 1.0000 (`png_r13.out`); the cast is still incomplete |
| 18 | Backgrounds per scene | 2 | 2 | 4 of 4 `bg_battle_*_frame.png` legal at 1.0000 (19:14), but the eight `*_text_preview` and `*_fight_preview` files are 0.2222 and 0.4222 (`png_r13.out`) |
| 19 | Build and packaging | 3 | 3 | Compiled and launched (`.win` 477772 B at 21:33, game lines in `build/last-igor.log`), but **no `BUILD PASS`**: the step never returned (`build/audit-readiness-build-2026-10-25-R3b.log`) |
| 20 | Tests and gates | 2 | 2 | Pine is 1547 passed 0 failed, but gate 4 exits **1** on 35 files and the build step cannot return, so the gate set is not green (`nesaudit_r13.out`, `tools/run.ps1:187`) |
| 21 | Capture and demo tooling | 3 | 3 | **Re-earned live**: `capture_title.py` exit 0, two frames, score 1.000, game closed on request (`capture_title_r13.out`); its own `P:` line reports the window on monitor 2 |
| 22 | Docs and repo hygiene | 3 | 3 | `README.md` 12887 B, `LICENCE` 5040 B, `CREDITS.md` 14394 B, but `README.md:26` still says the drive has `no room yet` while `rm_pp_drive` exists |

Sum 55, mean 2.5. Refresh 9 summed 57 at 2.591.

## 4. What moved, and what only looked like it moved

Down, measured:

1. Row 7, battle, 3 to 2. Not a missing measurement, the opposite: there is a fresh capture from 18:15:50 today and it
   says the fight did not happen. `battle_box_in_sample` frames 0, `fight_command_in_sample` frames 0,
   `victory_text_in_sample` frames 0, `battle_start_in_log` count 0 over 168 lines (`output/first_fight_verify.json`).
   Refresh 9 carried this row at 3 on `"ok": true` with `checked_at 2026-10-23T06:31:07`, a file it flagged itself as a
   re-copy. The re-copy is now superseded by a real run, and the real run is red.
2. Row 3, drive, 3 to 2. Refresh 9 earned it on one log line (`the crawl handed to the route's step drive`). That line
   needs the crawl, the crawl needs an input event, and my unattended launch never got past the title. Separately the
   room's own art is 12 of 12 outside the palette, and the palette set the art bible's RULE 0 asks for first does not
   exist for the drive. A row cannot stay at 3 on a log line whose precondition no run this cycle met.

Up, measured:

3. Row 16, art pipeline, held at 3 but for a stronger reason than before: Pine is 0 failed where refresh 9 had 2 reds
   needing a Windows rerun to explain (`pine_r13b.log`).
4. Not a score: the Pine suite itself, 1484/2 to 1547/0, and gate 1 and gate 2 both exit 0 in my hands
   (`pine_r13b.log`, `tools/check_data.py`, `tools/check_cleanroom.py`).

Held, but with weaker evidence than refresh 9 had, and the difference is the honest part of this page: rows 2, 4, 6, 13
were re-earned live at 18:05 and could not be re-earned at 21:45, because the build never left the title room
(`build/last-igor.log`).

## 5. The top five blockers to a playable slice, in order

1. **Nothing live between the crawl and the fight.** The route names 9 steps and 4 of them (arrival, gate, boarding,
   fight) have no live measurement today. My build stopped at the title, and the only fresh evidence about the fight is a
   red capture (`data/slice.json`, `build/last-igor.log`, `output/first_fight_verify.json`). Cards that cover it:
   `t_030a89e5` R32 TEST-SLICE-ROUTE (blocked, testing), `t_c024f8bc` ARRIVAL-MAP (blocked, gamedev). Both are blocked and
   neither can be closed by an implementer without a decision.
2. **The first fight capture is red while the card that owns it is closed.** `t_87ee4228` FIRST-FIGHT-LIVE is `done`, and
   its artifact reads `ok: false` on 5 of 7 checks at 18:15:50 (`board_probe.py`, `output/first_fight_verify.json`).
   Uncovered by any open card.
3. **The build gate cannot return.** `tools/run.ps1:187` waits on Igor with no timeout, and Igor's Run mode waits for the
   game to close. Two attempts, no verdict, 12 minutes of a 45 minute budget spent (`tools/run.ps1`,
   `build/audit-readiness-build-2026-10-25-R3b.log`). Covered by `t_9d9b5b1d`, todo, gamedev, p0.
4. **The drive has no palette set and its frames are outside the palette.** 0 sets in `data/scene_palettes.json`, 12 of 12
   frames illegal, `#081420` the offender (`png_r13.out`). Covered by `t_f034f9d0`, blocked, gamedev, p0, which is a
   `Q for gamedev` and is gamedev's to answer; I do not move it.
5. **An unattended launch stalls, and the window is not on the primary monitor.** `capture_title_r13.out` reports
   `moved off the primary screen to 1920,0, which is the second monitor`, and my build's log shows a pause and a focus
   return inside the first 150 lines (`last-igor-snapshot.log:147`). Uncovered: no open card names the monitor or the stall.

The card `t_8690e219` PALETTE-REPORT-STALE (todo, gamedev, p0) covers the one measurement oddity I could not explain:
`data/scene_palettes.json` grew 5970 B between 17:24 and 21:25 while its set count stayed at 12 (`board_probe.py`).

## 6. Uncovered gaps, with one proposed card each

These are proposals, not creations. I do not create cards on another lane's head, and gamedev is a head here.

1. `UNATTENDED-LAUNCH-STALL` (testing): prove that an Igor Run launch with nobody at the keyboard advances past the title,
   pin the window to the primary screen at 0,0 first, and record the key it sends. Evidence for the card: `P: window:
   moved off the primary screen to 1920,0` (`capture_title_r13.out`), `Pause event has been unregistered` and
   `PP audio: focus back` (`knowledge/igor-log-2026-10-25-2144.log:147`), and 178 log lines with no intro line.
2. `FIRST-FIGHT-CAPTURE-RED` (testing): take `output/first_fight_verify.json` from `ok: false` to `ok: true`, or show
   which of the 5 red checks is the check that is wrong. The thresholds are on the file (`0.7`, `5` clusters, `20` ink,
   `24` width) and `talk_leg` already passes, so the fight leg is the one to chase (`output/first_fight_verify.json`).
3. `README-DRIVE-LINE` (builder): `README.md:26` still says `shot list and generator, no room yet` for the drive while
   `rm_pp_drive` is one of four rooms. One line, and it is the line a judge reads first (`README.md:26`, `ls game/rooms`).

I did not propose a card for the drive palette, the arrival map, the slice route or the stale palette report: `t_f034f9d0`,
`t_c024f8bc`, `t_030a89e5` and `t_8690e219` already hold them (`board_probe.py`).

## 7. What I did not measure, and will not call verified

- The suite's five Windows-only nodes: `tests/test_build_inputs.py`, `tests/test_test_inputs.py`,
  `tests/test_sync_art.py`, and the two `test_project.py` nodes and one `test_mix_check_v3.py` node the offload
  deselects by name. They were not run in this cycle (`pine_r13b.log`).
- A returning `BUILD PASS`. I have compilation and launch, not a pass line
  (`build/audit-readiness-build-2026-10-25-R3b.log`).
- Any live fight, gate, boarding, arrival or game over frame. There is none newer than 18:15 and that one is red
  (`output/first_fight_verify.json`).
- Whether the drive cue `pp_drive_v2.ogg` is reached by the game, because my log never got to the handoff
  (`build/last-igor.log`).
- The board copy is read only and 3 minutes old at 21:36; two cards may have moved since (`board_probe.py`).

Chain of command: gamedev's ART-BIBLE RULE 0 is applied exactly as written in `knowledge/ART-BIBLE.md:283`, including the
tiled layer amendment, and no spec of gamedev's is overridden on this page. Where this page disagrees with a gamedev
number it says so and leaves the decision there, and there is one such case: a row at 3 needs a live line, and the drive
had none today.
