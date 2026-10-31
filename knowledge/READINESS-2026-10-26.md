# Readiness refresh 11, 2026-10-26 06:12 to 06:30: the 22 row table re-measured

Written by audit for card `t_51952d6f` (AUTO-AUDIT-REFRESH). Every number below came from a command this run ran on
this PC or offloaded to Pine between 06:12 and 06:30 Pacific, or from a file this run opened and read. Worker reports,
card results and the earlier readiness pages were not accepted as evidence. `READINESS-2026-10-25-R3.md` (refresh 10)
is untouched; this is a new page and its `Before` column is that page.

The tree this run measured: HEAD `ae3a6cb` "SHIP-DRAWN-IN-ITS-ROWS: the ship's sea is drawn in the three tones its row
can show, the brass is no longer sanded off, and a measured floor replaces the pin (card t_463cb8c1)", committed
2026-10-25 22:21:08, with 1275 dirty porcelain entries (`git rev-parse --short HEAD`, `git status --porcelain`).
Refresh 10 finished on `6456593` at 21:36, so three commits and about nine hours separate the two pages, and all three
commits in that range touch art and the palette report, not GML: `git diff --stat 6456593..HEAD -- game/scripts`
returns nothing, and `game/scripts` still holds 25 files and 10905 lines.

P: the build returns again. `python tools/integration_build.py` printed `BUILD PASS: Igor compiled the project
(compile mode, the game was not run)` and exited 0 in about 83 s, with `Igor complete.` at line 67 of
`build/last-igor.log` (`knowledge/_r11/build.log`). Refresh 10 spent 12 minutes on two attempts and got no verdict.
P: the reason is a landed rewrite, not luck: the step now compiles and never launches, and it kills its own process
tree after `GATE_BUILD_TIMEOUT_S = 480` (`tools/integration_build.py:46`, `tools/integration_build.py:24`).
P: the cost of that fix is that the build no longer produces live game lines: `grep -c "^PP " build/last-igor.log`
returns **0** against 178 such lines at refresh 10, so rows that need a live line could not be re-earned by this step.
P: the Pine suite is **1553 passed, 1 failed** across three shards, and the one red is real and names an artifact this
project ships: `output/scene_palettes.json is stale: it is not what the checker writes today`
(`offload-audit-ready-1026a-2.json`). Row 16 drops 3 to 2 on it, the only score that moved.
P: the first fight is still not captured: `output/first_fight_verify.json` is unchanged at `checked_at
2026-10-25T18:15:50`, `"ok": false`, 5 of its 7 checks false, and I read two of its 123 sampled frames myself
(`f_0000.png` is the title screen, `f_0060.png` and `f_0120.png` are an empty deck with no box and no character).
P: I could not take a fresh live capture at all: `tools/capture_title.py` refused twice and then polled its idle gate
for the full 300 s and refused again with `EXIT=4`, because the machine was in use the whole time
(`knowledge/_r11/capture.log`, `knowledge/_r11/capture2.log`, `knowledge/_r11/capture3.log`). I did not pass `--force`.

## 0. What this run measured, in one place

| Measurement | Command or source | Result |
| --- | --- | --- |
| HEAD at start | `git rev-parse --short HEAD` | `ae3a6cb`, committed 2026-10-25 22:21:08 |
| Dirt | `git status --porcelain` | 1275 entries |
| GML size | walk over `game/scripts` | 25 files, 10905 lines, unchanged since refresh 10 |
| Rooms | `ls game/rooms` | 4: `rm_pp_boot`, `rm_pp_drive`, `rm_pp_ship`, `rm_pp_title` |
| Build | `python tools/integration_build.py` | **exit 0**, `BUILD PASS: Igor compiled the project (compile mode, the game was not run)`, about 83 s (`knowledge/_r11/build.log`) |
| Build internals | `build/last-igor.log` | `:65 Stats : GMA : Elapsed=808.3123`, `:66 ... da=275 ...`, `:67 Igor complete.` |
| Compiled artifact | `ls -la output/PrimordialParadox/PrimordialParadox.win` | 477772 B, 06:12 today |
| Live game lines in my build | `grep -c "^PP " build/last-igor.log` | **0**, against 178 at refresh 10 |
| Build bound | `tools/integration_build.py` | `GATE_BUILD_TIMEOUT_S = 480` at `:46`, process tree killed after it (`:24`) |
| Gate's own bound | `guard/suite_config.json:211` | `timeout_s: 600`, `unmeasured_exit_codes: [3]` |
| Pine suite | `pine_offload.py --shards 3 --name audit-ready-1026a` | 464 + 562 + 527 = **1553 passed, 1 failed** (`offload-audit-ready-1026a-{0,1,2}.json`) |
| The one red | shard 2 `results_txt` | `tests/test_scene_palettes.py::test_the_check_reports_its_numbers_so_a_reviewer_can_read_them`, `1 failed, 527 passed, 16 skipped in 40.41s` |
| The red's assertion | same | `AssertionError: output/scene_palettes.json is stale: it is not what the checker writes today.` |
| Gate 1 | `python tools/check_data.py` | exit **0**, `check_data: all files pass` (`knowledge/_r11/g1.log`) |
| Gate 2 | `python tools/check_cleanroom.py` | exit **0**, `no study reference, no foreign name, no foreign phrase, every module reviewed` (`knowledge/_r11/g2.log`) |
| Gate 4 | `python tools/nes_audit_all.py` | exit **1**, `183 file(s), 35 failing, 0 unmeasured`; 229 PNGs on disk, 175 skipped by name (`knowledge/_r11/g4.log`) |
| Fight capture | `output/first_fight_verify.json` | **ok false**, `checked_at 2026-10-25T18:15:50`, 5 of 7 checks false; 123 frames on disk, all 18:15 |
| Fight frames, my read | Pillow over `output/first_fight_frames/*.png` | 123 frames, 122 consecutive pairs compared: 59 of 122 changed under 0.1 percent of pixels, min 0.0000, max 0.9454 (`knowledge/_r11/fight.log`, motion probe) |
| Fight frames, my eyes | this model over `f_0000`, `f_0060`, `f_0120` | title screen; empty deck; empty deck. No box, no command row, no character |
| Title capture | `python tools/capture_title.py`, then `--idle-wait 300` | refused twice, `EXIT=4`; `P: idle gate SKIPPED the launch: input 0 s ago, 120 s required, waited 300 s of 300 s` (`knowledge/_r11/capture3.log`) |
| Title artifacts on disk | `ls -la output/title_run_*.png` | 59093 and 64275 B, **21:38 yesterday**, not re-earned by this run |
| Title crop legality | Pillow over `output/title_run_reference_3x.png` | 768x720, 41 RGB, share **0.9999**, 36 off-master px in 32 colours, largest `#063F57` 2 px (`knowledge/_r11/png.log`) |
| Window frame legality | Pillow over `title_run_1.png`, `title_run_2.png` | 784x759, 4716 and 5255 RGB, share 0.9294, `#F9F1ED` 7907 px (desktop behind the window) |
| Committed title frame | `output/nes_title_frame.png` | 256x240, 11 RGB, share **1.0000**, 0 off-master px |
| UI previews | Pillow | `ui_battle` 5 RGB 1.0000, `ui_dialogue` 5 RGB 1.0000, `ui_menu` 4 RGB 1.0000 |
| The two red previews | Pillow | `title_ui_preview` 1920x784 share **0.0109**, `#081420` 1362523 px; `gameover_preview` 256x240 share **0.0000**, `#0B0B0F` 58824 px, mtime 10-22 20:46 |
| Sprite sheets | Pillow | `chars_contact` 736x2768 25 RGB 1.0000; `sprites_v2_sheet` **1024x4592** 19 RGB 1.0000; `enemies_preview_3x` 464x772 9 RGB 1.0000 |
| Background strips | Pillow, `output/bg_battle_*_frame.png` | 4 of 4 share **1.0000**, 7 to 9 RGB, mtime 10-25 19:14 |
| The eight battle previews | Pillow, `*_text_preview` and `*_fight_preview` | **8 of 8 illegal**, share **0.2222** (text) and **0.4222** (fight), `#1C1C24` 27762 px (text) and 17185 px (fight), mtime 10-22 22:22 |
| Crawl frame | Pillow, `output/crawl_mid.png` | 768x720, 4 RGB, share **0.9667**, `#F9F9F9` **18423 px**, the only off-master colour |
| Drive frames | Pillow, `output/drive_frames/drive_shot_*.png`, 12 files | **0 of 12 legal**, share 0.0000 to 0.0167, 8 to 10 RGB, 256x240, `#081420` the worst in **9 of 12**, mtime **10-25 22:22** |
| Scene palette sets | `data/scene_palettes.json` 38704 B, mtime 21:40 yesterday | 12 sets by id: battle_corridor, battle_deck_night, battle_quay_dusk, battle_wardroom, icons, sea, ship, southampton, title, ui, westminster, winchester. No drive, no gameover; `grep -c drive` returns **0** |
| Scenes | `data/scenes/all.json` 9424 B, mtime 10-24 22:58 | 48 `"id":` keys; `grep -c "gameover\|game_over"` returns **0** |
| Slice route | `data/slice.json` 1741 B, mtime 10-23 06:19 | 9 steps: title, crawl, drive, arrival, gate, boarding, fight, save, gameover |
| Game over in code | `grep -ci gameover game/scripts/pp_battle_director/pp_battle_director.gml` | **47** lines: `gameover_choice`, `gameover_cursor`, `gameover_note` and the rest; `tests/test_save_gameover.py` holds 19 tests |
| Save capture | `output/save_capture_verify.json`, mtime 10-24 20:47 | **20 `"ok": true`, 0 `"ok": false`**, 18 distinct checks including `CONTINUE landed on the saved tile` |
| Demo, run 001 | `output/demo/run_001_verify.json`, mtime 10-22 18:14 | `"ok": false` |
| Demo, run 002 | `output/demo/run_002_verify.json`, mtime 10-23 01:49 | **`"ok": true`**, `not_a_terminal` PASS `7 of 7 sampled frames are the game's own picture`, 8 footsteps, markers at 11.55 s and 43.117 s |
| README | `README.md` 12887 B, mtime 10-24 11:18 | `:26` drive row still `shot list and generator, no room yet`; the game over row still `game over does not exist yet` |
| Root docs | `ls` | `README.md` 12887 B, `LICENCE` 5040 B, `CREDITS.md` 14394 B |
| Board | read-only copy of `boards/nayil-ops/kanban.db`, 24969216 B at 06:14 | 954 done, 587 archived, **67 blocked, 10 todo, 7 running, 0 ready** (`board_probe.py`) |

No key or login file was opened, and no value from one appears anywhere on this page. Only paths, sizes, digests, log
lines, pixels and test output appear here.

The PNG numbers above are my own: the 2C02 master set (`data/nes_palette.json`, 55 unique colours, read through
`tools/nes_check.py`'s own loader) and "share" means the fraction of non-transparent pixels whose RGB is one of those
55. The method is validated against refresh 10 rather than assumed: my probe reproduces its `nes_title_frame` 1.0000 and
11 RGB, its title crop 0.9999 with `#063F57` at 2 px, its 0.9294 with `#F9F1ED` at 7907 px, and its 0.2222 and 0.4222 on
the eight battle previews, so it is the same metric and the two pages can be compared line by line. The first pass of
that probe was wrong, and section 4 records why.

## 1. The build, and what changed about it

Refresh 10 had no verdict at all: `Start-Process ... -Wait` with no timeout, two attempts, 12 minutes spent. That
finding was right and it has been acted on. The landed rewrite is `integration_build.py` calling
`tools/run.ps1 -SkipChecks -Compile`, so Igor compiles and never launches, and the tool enforces its own cap:

    GATE_BUILD_TIMEOUT_S = 480            `tools/integration_build.py:46`
    the compile gets GATE_BUILD_TIMEOUT_S, after which the powershell/Igor process tree is killed and the step fails
                                          `tools/integration_build.py:24`

My run, 06:12:53 to 06:14:16, about 83 s:

    BUILD PASS: Igor compiled the project (compile mode, the game was not run)
    EXIT=0                                `knowledge/_r11/build.log`

and the three things the tool insists on are all present in `build/last-igor.log`: `:67 Igor complete.`, `:65 Stats :
GMA : Elapsed=808.3123`, `:66 ... ob=4,ro=4,da=275,ex=0,ma=6 ...`, and a `.win` rewritten by this run at 06:12
(477772 B). This is the first refresh in three that can say that.

Two consequences follow, and both matter more than the pass itself.

First, the gate's bound and the tool's bound disagree in a way nobody would see from the gate: `suite_config.json:211`
gives the step `timeout_s: 600`, and the tool kills itself at 480 s, so the effective cap is the smaller one and the
gate's number never fires. That is the safe direction, and it is worth writing down because the card that made this
change (`t_9d9b5b1d`) says `timeout_s: 900` in its body.

Second, the step no longer launches the game, so it no longer produces the live lines that rows 2, 4, 6, 12, 13 and 14
were earned on at refresh 9 and 10. `grep -c "^PP " build/last-igor.log` returns **0** today against 178 yesterday.
The live-evidence role has therefore moved entirely onto `tools/capture_title.py`, `tools/capture_first_fight.py` and
`tools/capture_save.py`, and both of the first two were unavailable or red this cycle (sections 2 and 3).

## 2. The Pine suite, and the one red that is not an artefact

Attempt with the sandbox interpreter, `--shards 3 --name audit-ready-1026a`, exit 0 on the driver:

| Shard | Result | Finished |
| --- | --- | --- |
| `audit-ready-1026a-0` | 464 passed, 0 failed | 06:15 |
| `audit-ready-1026a-1` | 562 passed, 0 failed | 06:16 |
| `audit-ready-1026a-2` | 527 passed, **1 failed**, 16 skipped in 40.41 s | 06:16 |

1553 passed, 1 failed (`offload-audit-ready-1026a-0.json`, `-1`, `-2`). The driver also logged one transport retry,
`upload attempt 1 for audit-ready-1026a-1 failed (ConnectionError); retrying on a fresh connection`, which cost time and
changed no verdict (`knowledge/_r11/pine.log`).

The red, verbatim from the shard 2 results:

    AssertionError: output/scene_palettes.json is stale: it is not what the checker writes today. Regenerate it with
    `python tools/check_scene_palettes.py --json output/scene_palettes.json` and commit
    tests/test_scene_palettes.py::test_the_check_reports_its_numbers_so_a_reviewer_can_read_them

This is not a Linux artefact and it is not a flake. It compares a committed JSON to what the checker computes today from
the same tree, and the difference it names is `title_frame` and `title_car_frame` report content. It is the guard that
card `t_8690e219` (gamedev, marked done) added on purpose, firing on the tree that HEAD `ae3a6cb` produced after it
changed the ship tiles. The guard works; the artifact went stale behind it, and nothing in the working day regenerated
it.

The five nodes the offload deselects by name are unchanged and still unmeasured by me: `test_mix_check_v3.py::
test_the_script_still_runs_on_a_slice` (needs 16,752,241 bytes of renders), `test_project.py::
test_generated_project_files_are_current`, `test_project.py::test_project_graph_matches_disk` (both need the 30 stream
sources the zip drops), and `tests/test_build_inputs.py`, `tests/test_test_inputs.py`, `tests/test_sync_art.py` are not
offloaded at all (`knowledge/_r11/pine.log`).

## 3. The table, before and after

Scale unchanged: 0 nothing, 1 spec only, 2 code or data but unproven in the game, 3 proven in the running game with a
capture or a test, 4 polished. `Before` is `READINESS-2026-10-25-R3.md` (refresh 10).

| # | Subsystem | Before | After | Evidence measured this run |
| --- | --- | --- | --- | --- |
| 1 | Title screen | 3 | 3 | **Not re-earned.** `capture_title.py` refused three times and then polled 300 s and refused (`EXIT=4`); the frames on disk are 21:38 yesterday and measure 0.9999 with 36 off-master px (`knowledge/_r11/capture3.log`, `knowledge/_r11/png.log`) |
| 2 | Intro crawl | 3 | 3 | **Not re-earned.** `grep -c intro` over my build log returns 0 because the step compiles only; `crawl_mid.png` is 0.9667 with `#F9F9F9` 18423 px, the one off-master colour in the crawl |
| 3 | Drive cutscene | 2 | 2 | Holds down: **0 of 12** `output/drive_frames/*.png` legal, share 0.0000 to 0.0167, `#081420` worst in 9 of 12, frames regenerated 10-25 22:22, and `data/scene_palettes.json` still holds 0 drive sets (`knowledge/_r11/png.log`) |
| 4 | Overworld movement | 3 | 3 | **Not re-earned.** No footstep or walk line in my log, which has 0 game lines; the 8 footsteps in `run_002_verify.json` are from 10-23 |
| 5 | Maps and doors | 2 | 2 | Town renders legal in my probe (share 1.0000 on frames), but gate 4 still fails the three `*_sample_preview_2x.png` on background areas (241, 150, 152) and no door traversal has a capture (`knowledge/_r11/g4.log`) |
| 6 | Dialogue and talk | 3 | 3 | **Not re-earned.** 0 `text_blip` lines in my build log; the v2 work is not visible to this run |
| 7 | Battle and the talk fight | 2 | 2 | Holds down: `output/first_fight_verify.json` **ok false**, `checked_at 2026-10-25T18:15:50`, 5 of 7 false; my own reads of `f_0000`, `f_0060`, `f_0120` show a title screen and an empty deck (`knowledge/_r11/fight.log`) |
| 8 | Enemies | 2 | 2 | `enemies_preview_3x.png` 464x772 9 RGB share 1.0000; no live encounter, and gate 4 fails `enemies_preview_3x.png` on grid x1 (`knowledge/_r11/png.log`, `knowledge/_r11/g4.log`) |
| 9 | Party and stats | 2 | 2 | `data/characters/party.json` is 295 B from 10-19 with one character; `max_hp`, `will_max` and `power_multiplier` appear in 41 test modules including `test_save` and `test_first_fight`, but no capture shows a stat number on screen (`grep -rln` over `tests/`) |
| 10 | Save and load | 3 | 3 | **Stronger than before.** `output/save_capture_verify.json` is 20 `"ok": true`, 0 false, over 18 checks including `CONTINUE landed on the saved tile` and `the landing frame is the log terminal screen` (10-24 20:47, not re-run this cycle) |
| 11 | Ledger | 2 | 2 | `tests/test_ledger.py` is green inside the 1553, but no capture reads a ledger row back and no open card owns it (`board_probe.py`) |
| 12 | Audio bus and cues | 3 | 3 | **Not re-earned.** The compile-only step writes no audio line; `run_002_verify.json` names its audio a `rendered stand-in ... not the game's live output` |
| 13 | Music per scene | 2 | 2 | `data/scene_palettes.json` carries 12 sets, the four battle grounds and `sea` among them, and 0 for drive and 0 for game over; no per-scene cue was heard this cycle because `build/last-igor.log` holds 0 game lines |
| 14 | SFX | 3 | 3 | **Not re-earned.** 0 SFX lines in my build log; the 4 cue families last measured live are in `knowledge/igor-log-2026-10-25-2144.log` |
| 15 | UI windows and menus | 2 | 2 | `ui_battle`, `ui_dialogue`, `ui_menu` are 1.0000 in my probe; `title_ui_preview` is 0.0109 and gate 4 fails `title_ui_preview.png` on background_area 301 and palette 7 (`knowledge/_r11/g4.log`) |
| 16 | Art pipeline | 3 | **2** | **Dropped.** The Pine red is this row's own surface: `output/scene_palettes.json is stale: it is not what the checker writes today` (`offload-audit-ready-1026a-2.json`). The renders themselves are legal, so the drop is about the pipeline reproducing its own report |
| 17 | Sprites per character | 2 | 2 | `sprites_v2_sheet.png` is now **1024x4592**, 19 RGB, share 1.0000, and `chars_contact.png` 25 RGB 1.0000; `t_858c2908` (car, Ronan, Theo, storm cloud) is now done, but no capture shows a character drawn on screen in the fight run |
| 18 | Backgrounds per scene | 2 | 2 | 4 of 4 `bg_battle_*_frame.png` at 1.0000 (10-25 19:14), but **8 of 8** `*_text_preview` and `*_fight_preview` at share **0.2222** and **0.4222** with `#1C1C24` (`knowledge/_r11/png.log`) and gate 4 fails all eight |
| 19 | Build and packaging | 3 | 3 | **New evidence class:** exit 0, `BUILD PASS`, `Igor complete.`, `.win` 477772 B at 06:12, bounded at 480 s (`knowledge/_r11/build.log`). Not 4: still no install step and no zipped artifact |
| 20 | Tests and gates | 2 | 2 | Pine 1553 passed 1 failed; gate 1 and 2 exit 0; gate 4 exits **1** on 35 of 183 files; the build step is green but compile only, so the gate set is still not green (`knowledge/_r11/g4.log`) |
| 21 | Capture and demo tooling | 3 | 3 | `capture_title.py` refused rather than lied (`EXIT=4`, idle gate), `capture_first_fight.py` produced a red self check and says so, and `run_002_verify.json` is **ok true with 7 of 7 frames** the game's picture |
| 22 | Docs and repo hygiene | 3 | 3 | `README.md` 12887 B, `LICENCE` 5040 B, `CREDITS.md` 14394 B all exist, but `README.md:26` still says the drive has `no room yet` and the game over row still says `game over does not exist yet` while `rm_pp_drive` is one of four rooms and `pp_battle_director.gml` implements the screen |

Sum 54, mean 2.4545, against refresh 10's 55 at 2.5. One row moved, and it moved down.

## 4. What moved, what looked moved, and one place I do not agree with refresh 10

Down, measured:

1. Row 16, art pipeline, 3 to 2. The only reason refresh 10 held it at 3 with "no caveat for the first time" was a Pine
   suite with 0 failures. Tonight the suite has one failure and it is exactly the art pipeline's own output:
   `output/scene_palettes.json is stale: it is not what the checker writes today`
   (`offload-audit-ready-1026a-2.json`). The same page cannot hold a row at 3 on a green suite in one cycle and keep 3
   when the suite goes red on that row's artifact.

Up, measured, and it is not a score change because the row was already at 3:

2. Row 19, the build, from "compiled and launched, not returned" to `BUILD PASS` with a 480 s bound. This is the
   clearest gain of the cycle and it is a gain in the one place the gate needed it.
3. Row 10, save and load, from a single log line to a 20-check green two-run capture that names the slot, the write, the
   read and the landing tile (`output/save_capture_verify.json`).

Corrections to the previous page, which are findings in their own right:

4. Refresh 10's blocker 2 and its "the demo recorder does not record the game" line rest on `output/demo/run_001_verify
   .json` (`ok: false`, 10-22 18:14). That is the **first** run. `run_002_verify.json` (10-23 01:49) is `ok: true`, with
   `not_a_terminal` PASS `7 of 7 sampled frames are the game's own picture`, 8 footsteps and both title markers. The
   recorder has been green for three days and the page did not notice, because it read the older of two files and
   treated it as current. I am not scoring this as an improvement, since 10-23 is not this cycle; I am recording that a
   claim I inherited was out of date.
5. One correction is mine, and it belongs on the page because the numbers in it would otherwise be wrong. My first pass
   of the PNG probe read `tools/nes_check.py`'s palette loader wrongly (`palette_path` returns a 3-key dict, not the
   rgb map) and computed against an empty master set, which reported share 0.0000 for every file including
   `nes_title_frame.png`. That file is 1.0000 by refresh 10's measurement and by mine, so the zero was a polluted run
   and not a finding. I fixed the loader call and reran into the same log, so `knowledge/_r11/png.log` now holds only
   the corrected pass, and that pass reproduces refresh 10 on all four cross-check files. The polluted output was
   discarded with the run and none of it appears anywhere on this page.

Held, with weaker evidence than refresh 10 had, and that difference is the honest part of this page: rows 1, 2, 4, 6, 12
and 14 were re-earned live yesterday and could not be re-earned today, because the build compiles only and the capture
harness refused to open a window while the machine was in use. None of them lost a point for that; the evidence behind
them is simply one day older than the page.

## 5. The top five blockers to a playable slice, in order

1. **The first fight has no green capture, and the card that owns it is closed.** `t_87ee4228` FIRST-FIGHT-LIVE is
   `done` (code-review, p92) and its artifact is `output/first_fight_verify.json`, `"ok": false` at
   `checked_at 2026-10-25T18:15:50`, with `battle_box_in_sample` frames 0, `fight_command_in_sample` frames 0,
   `victory_text_in_sample` frames 0 and `battle_start_in_log` count 0. I read `f_0000`, `f_0060` and `f_0120` myself:
   a title screen and two empty decks. Uncovered by any open card (`board_probe.py`).
2. **Nothing between the crawl and the fight has live proof, and the drive is the worst of it.** `data/slice.json`
   names 9 steps; the build has 4 rooms; `data/scenes/all.json` has 0 game over rows; the drive has 0 palette sets and
   **12 of 12** frames outside the palette, regenerated at 22:22 yesterday and still illegal. Covered by `t_c024f8bc`
   ARRIVAL-MAP (blocked, gamedev, p97), `t_030a89e5` R32 TEST-SLICE-ROUTE (blocked, testing, p79) and `t_f034f9d0`
   (blocked, gamedev, p0, a `Q for gamedev` that is gamedev's to answer, not mine).
3. **The gate set is not green, and one red is a real regression against a guard that works.** Gate 4 exits 1 on 35 of
   183 files, unchanged in count from refresh 10; Pine has 1 real red naming `output/scene_palettes.json`; gate 1 and
   gate 2 are green. `t_41766656` AUTO-GATE-GREEN is running (testing) and `t_9d9b5b1d` is running (gamedev, and its
   build half has landed). The stale report itself is uncovered.
4. **The front door misstates the project to a judge.** `README.md:26` still says the drive has `no room yet` while
   `rm_pp_drive` is 1 of 4 rooms, and the game over row still says `game over does not exist yet` while
   `pp_battle_director.gml` carries `gameover_choice` and `tests/test_save_gameover.py` holds 19 tests, with
   `output/gameover_preview.png` at share 0.0000 as its only frame. `t_8d7bad5f` R45 README-SLICE is `done`, so no open
   card holds this.
5. **The only live-evidence tools refuse while the machine is in use, and this cycle lost that evidence entirely.**
   `capture_title.py` refused twice immediately and once after polling its whole 300 s window, `EXIT=4`, message `P:
   idle gate SKIPPED the launch: input 0 s ago, 120 s required` (`knowledge/_r11/capture3.log`). That is the gate
   working as designed and I did not override it, but it means six rows of this table can only be re-earned in a quiet
   window. `t_52166d5a` CAPTURE-QUIET (blocked, testing, p0) covers the muted negative control, not this.

## 6. Uncovered gaps, with one proposed card each

These are proposals, not creations. I do not create cards on another lane's head, and gamedev is a head here.

1. `PALETTE-REPORT-COMMIT` (builder): run `python tools/check_scene_palettes.py --json output/scene_palettes.json`,
   then commit the regenerated file with the ship tile change that made it stale. Evidence: the shard 2 assertion text,
   and `data/scene_palettes.json` at 38704 B mtime 10-25 21:40 against a tree at `ae3a6cb` from 22:21.
2. `FIRST-FIGHT-CAPTURE-RED` (testing): take `output/first_fight_verify.json` from `ok: false` to `ok: true`, or show
   which of the 5 red checks is the check that is wrong. `talk_leg` already passes, so the fight leg is the one to
   chase; the thresholds are on the file.
3. `README-TRUTH-2026-10-26` (builder): fix the two rows named in blocker 4, in the table a judge reads first.
4. `GAMEOVER-PREVIEW-LEGAL` (builder): `output/gameover_preview.png` is 4 RGB at share **0.0000** with `#0B0B0F` on
   58824 px, mtime 10-22 20:46, and gate 4 fails it on `palette x4`. Regenerate it inside the palette or delete it.
5. `CRAWL-WHITE` (builder): `output/crawl_mid.png` carries `#F9F9F9` on **18423** px, share 0.9667, the one off-master
   colour in the crawl still. One colour, on the screen the intro ends on.
6. `PARTY-STATS` (builder): `data/characters/party.json` is 295 B from 10-19 with one character; nothing shows a stat
   number changing. Refresh 9 proposed this and no card was ever made.
7. `LEDGER-PROOF` (testing): a captured run whose ledger rows are read back and counted. `tests/test_ledger.py` is green
   and no capture touches it.

I did not propose a card for the drive palette, the arrival map, the slice route or the build step: `t_f034f9d0`,
`t_c024f8bc`, `t_030a89e5` and `t_9d9b5b1d` already hold them, and the last of those has already landed its build half
(`board_probe.py`, `knowledge/_r11/build.log`).

## 7. What I did not measure, and will not call verified

- Any fresh live capture. Three refusals by the idle gate and no override (`knowledge/_r11/capture3.log`).
- A live fight, gate, boarding, arrival or game over frame. The newest is 10-25 18:15 and it is red
  (`output/first_fight_verify.json`).
- The six rows that need a live line: 1, 2, 4, 6, 12, 14. Their scores are carried from refresh 10 and say so.
- The five Windows-only nodes the Pine driver deselects or does not offload (`knowledge/_r11/pine.log`).
- `run_002.mp4` playback itself. I read its verifier's report, not the video, and the report is 10-23.
- The board copy is read-only and about 4 minutes old at 06:14; cards may have moved since (`board_probe.py`).

Chain of command: gamedev's `knowledge/ART-BIBLE.md` RULE 0 is applied as written, palette first, one shared backdrop,
all colours from the 54 usable master colours, and the tiled layer amendment stands. No spec of gamedev's is overridden
on this page. Where this page disagrees with a gamedev number it says so and leaves the decision there, and there are
two such cases: the drive row stays at 2 while `t_f034f9d0` is unanswered, and row 16 drops because gamedev's own
stale-report guard fires, which is a question for their lane and not a spec change of mine.
