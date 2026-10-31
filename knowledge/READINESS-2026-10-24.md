# Readiness, 2026-10-24: the 22 row table re-scored on measured evidence

Written by audit for card `t_d5ecf73f` (READINESS-2026-10-24). Every number on this page came from a command this run
executed on 2026-10-23 between 00:44 and 01:40 Pacific, on this PC, against the working tree at
`<repo>`. Worker reports, card results and the earlier readiness
pages were not accepted as evidence; where I did not measure, the line says unverified.

Shape is `knowledge\READINESS-2026-10-23.md` (R40, `t_4d0c2ef5`): the tree, the four gates, then one block per step.
The 22 rows and the delta column are `knowledge\HACKATHON-AUDIT-2026-10-22.md` section 1 (the baseline table) against
`knowledge\READINESS-2026-10-22.md` section 2, which is the last time the table was actually re-measured. The step page
`READINESS-2026-10-23.md` carries no table, so it cannot supply a per row delta and is not used as one.

## 0. The tree that was measured

    git HEAD                 b61c575 at 01:40 (it was 02b7d52 at 00:44 when this run started)
    git status --porcelain   629 entries, the tree is dirty and moving
    data/scenes/all.json     7f612b924346349429915bf4d8bb1f85d6db6223c5623feae36e3d47dd3fa9d3
    data/dialogue/all.json   3bf4323df45170821ce5e43d55c134ece4715d8e67d86388bb21c1e21001c666  (was b610e3f0)
    data/maps/all.json       2f12bdb70a30f55bb356cdfa10bcf81b6b82b3ae5426531776693d434702b60c
    data/slice.json          eb1767524b2c1a754cde79bb901337999457e7851366ca183d1cb0af78e37eef  (unchanged since 20:39)
    data/flags.json          1c4debea82c016d7d969e36a23a94452225021150b50c580fa4563cb9e6da852, 14 flags

The tree moved under this audit, and one of those movements changes a score. R21a DRIVE-ROOM (`t_e9c7b280`, builder,
running) wrote `game\scripts\pp_drive\pp_drive.gml` (29488 bytes) at 00:52, `game\objects\obj_pp_drive\*.gml` at 00:53 to 00:55,
and `game\rooms\rm_pp_drive\rm_pp_drive.yy` plus the `game\PrimordialParadox.yyp` entry that registers it at 00:59. My
build finished compiling at 00:50, so the build I measured does not contain that room. Row 3 states both halves.

## 1. The four gates

1. `python tools/check_data.py`, 01:02, **exit 0**, `check_data: all files pass`.
2. `python tools/check_cleanroom.py`, 01:02, **exit 1**, `355 files scanned for 26 names and 12 phrases, 40 GML modules,
   1 awaiting review` and then four FAIL lines: `game\objects\obj_pp_drive\Create_0.gml`, `Draw_0.gml`, `Step_0.gml`
   and `game\scripts\pp_drive\pp_drive.gml` each carry `no clean-room review row in knowledge\CLEANROOM-REVIEW.md`.
   That red gate is caused by the card writing right now, not by a regression this audit can attribute to a commit.
3. `python -m pytest tests -q`, started 01:14 and finished 01:23, **exit 1**, `13 failed, 1155 passed, 117 warnings
   in 548.92s (0:09:08)`. The 13 are `test_slice_route` 8, `test_look` 2, `test_build_inputs` 1,
   `test_project::test_build_inputs_are_committed` 1 and `test_title_path::test_continue_without_a_save_is_dim` 1
   (`gate_3_pytest_windows.out`). The Pine offload the card prescribed did not produce a full suite number this run;
   section 1a says exactly what happened and what it returned.
4. `python tools/nes_audit_all.py`, 01:15, **exit 1**, `nes_audit_all: FAIL  178 file(s), 33 failing, 0 unmeasured`.
   Yesterday the same tool printed `PASS 160 file(s), 24 failing` and exited 0, so it cannot have been gating anything.
   Today it fails the run, and 33 rows are red, the largest group being the `output\bg_battle_*_text_preview.png` and
   `output\bg_battle_*_fight_preview.png` strips at 4 palette violations each (`gate_4_nes_audit.out`).

### 1a. The offloaded test run the card asked for, and why it is not the number above

The card names `python tools/pine_offload.py --cmd "<pytest>"`. That file is not in this repository; it lives at
`<workspace>\Shared\projects\arananet\pine\pine_offload.py`, which is where I ran it, with the interpreter
its docstring names (`AppData\Local\Python\bin\python.exe`). Two attempts:

1. `--cmd "python -m pytest tests -q"`, started 00:58, finished 01:00: the Pine agent replied
   `ERROR: file or directory not found: tests` and `EXIT=4` (`offload-audit-r24-0.json`, status `completed`). The tool
   is at fault, not the tree: `build_zip()` packs every path under `projects/primordial-paradox/` (`REPO_ARC`, line 68)
   while `GOAL_CMD` (line 74 on) tells the agent to unzip into `~/repo` and run there, so `tests/` is one directory
   deeper than the command assumes. The exact command in the card cannot work as written.
2. `--shards 3 --name audit-r24b`, started 01:04: the 51.7 MB zip uploaded, then shard 0 and shard 2 died on
   `PineCallError: pine write_file failed: TimeoutError ... op=PUT /v1/sessions/main/files`. Those two are transport
   errors and I do not count them as verdicts. Shard 1 completed with a real result: **429 passed, 17 failed** over 20
   test files (`offload-audit-r24b-1.json`, `SUMMARY passed=429 failed=17`). Its 17 failures are `test_look` 2,
   `test_project` 7 and `test_slice_route` 8, and they name the missing route rows by step:
   `step arrival: the map 'southampton_town_quay' is not in data/maps/all.json` and `step save: the row names no trigger`.

So the offload did produce one honest Linux shard, and the full suite number in gate 3 is this PC's own run, which
means Windows-only tests pass there and the count is not comparable to yesterday's Pine numbers.

## 2. The 22 row table, re-scored

Scale unchanged: 0 nothing, 1 spec only, 2 code or data but unproven in the game, 3 proven in the running game with a
capture or a test, 4 polished. Before is the audit baseline (18:41 to 19:24 on 2026-10-22); Yesterday is
`READINESS-2026-10-22.md` section 2 (20:43 to 21:15); Now is this run.

| # | Subsystem | Before | Yesterday | Now | Delta | Evidence for the Now value |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Title screen | 3 | 3 | 3 | 0 | `capture_title.py` exit 0 at 01:00, `title_run_1.png` and `title_run_2.png` both `score 1.000`; the 768x720 crop carries 32 distinct RGB, 23 of them outside the 64 hex values listed in `data\nes_palette.json`, 10 of 61440 3x blocks not uniform. Not 4 on those numbers. |
| 2 | Intro crawl | 3 | 3 | 3 | 0 | `output\crawl_mid.png` 4 colours (1 off palette), `output\crawl_end.png` 4; `test_intro` is not among gate 3's 13 failures. |
| 3 | Drive cutscene | 1 | 1 | 2 | +1 | `game\scripts\pp_drive\pp_drive.gml` 29488 bytes at 00:52, `game\rooms\rm_pp_drive\` present at 01:04, `game\PrimordialParadox.yyp` references `rm_pp_drive` 6 times and `obj_pp_drive` 3 times (written 00:59). Not 3: my build compiled at 00:50, before the room existed, and no capture shows the drive. |
| 4 | Overworld movement | 3 | 3 | 3 | 0 | `output\demo\run_001.mp4` frames t=24.99 and 36.75 score exact viewport 0.966 and 0.954 in `play_demo.py --check`, the walk is the part of that recording that holds. |
| 5 | Maps and doors | 2 | 2 | 2 | 0 | `data\maps\all.json` holds `ship_small` and `ship_cabin` only; the route's `southampton_town_quay` is absent, so `test_slice_route` fails `[arrival]` on the spawn tile. |
| 6 | Dialogue and talk | 3 | 3 | 3 | 0 | `data\dialogue\all.json` 35 rows, now including `quay_gate_checkpoint` and `quay_gate_choice`; `data\flags.json` carries all five gate flags (14 of 200 spent). `test_dialogue_v2` is not among gate 3's 13 failures. |
| 7 | Battle and the talk fight | 2 | 2 | 2 | 0 | `test_first_fight.py` passed on Pine shard 1 (429 passed run); no scene op anywhere names `tutorial_sailors`, so the fight is still unreachable from the walk. |
| 8 | Enemies | 2 | 2 | 2 | 0 | `output\enemies_preview_3x.png` 9 colours, 0 off palette; no live encounter captured. |
| 9 | Party and stats | 2 | 2 | 2 | 0 | `data\characters\party.json` only; no test names a level up. |
| 10 | Save and load | 2 | 2 | 2 | 0 | `grep` count of `"save"` in `game\scripts\pp_scene\pp_scene.gml` is 0; no save file exists in the tree (only `build\save_slot_probe\pp_save_01.original.json`, a fixture); `test_save_gameover.py` passed on Pine shard 1. |
| 11 | Ledger | 2 | 2 | 2 | 0 | `tests\test_ledger.py` passed in gate 3's run; no capture. |
| 12 | Audio bus and cues | 3 | 3 | 3 | 0 | live from my build: `PP audio: focus lost, music paused (cue and theme) and every effect stopped`, `thunder_soft played, instance 400027`, and `PP: muted, PP_MUTE=1 in the environment, so the master gain is 0 for this run` at line 106 of `build\last-igor.log`. |
| 13 | Music per scene | 2 | 2 | 2 | 0 | per room coverage unverified; `tests\test_pp_drive_cue.py` exists now (shard 0, which errored), the drive cue capture card `t_b84a9264` is not done. |
| 14 | SFX | 3 | 3 | 3 | 0 | `tests\test_sfx.py` passed in gate 3's run; live cue lines in `build\last-igor.log`. |
| 15 | UI windows and menus | 2 | 2 | 2 | 0 | `output\ui_battle_preview.png` 5 colours, `ui_dialogue_preview.png` 5, `ui_menu_preview.png` 4, all rewritten 22:47; card NES-GATE-ROW15 `t_852f3689` is ready, not done. |
| 16 | Art pipeline | 2 | 2 | 3 | +1 | `python -m pytest tests/test_look.py tests/test_title_art_v2.py tests/test_make_title_ui.py tests/test_make_title_world.py tests/test_title_bands.py tests/test_scene_palette_set.py tests/test_make_env_ship.py tests/test_quantize_concept.py -q` at 01:36 returns `2 failed, 128 passed in 119.69s`, and the only red pins are `test_look`'s two palette-role checks, so every reproducibility test (title_art_v2, make_title_ui, make_title_world, title_bands, scene_palette_set, make_env_ship, quantize_concept) is green on the build host. Not 4: the live title crop is still 23 colours off the palette and `test_look` is still red. This is the Windows run; the Pine shard holding `test_make_title_ui` died on upload, so the Linux side is unverified. |
| 17 | Sprites per character | 2 | 2 | 2 | 0 | 12 `spr_*.png` in `game\art` (count this run), `output\chars_contact.png` 736x2768, 22 colours, 0 off palette; card `t_858c2908` still blocked. |
| 18 | Backgrounds per scene | 3 | 3 | 3 | 0 | R48 landed at 22:39 (`43f4243`), four strips present, `output\bg_battle_preview.png` 16 colours; `nes_audit_all` fails all eight `bg_battle_*_preview.png` files at 3 to 7 background area violations each, and no battle capture exists. |
| 19 | Build and packaging | 3 | 3 | 3 | 0 | `python tools\integration_build.py` exit 0, `BUILD PASS: Igor compiled the project and launched the game`; `output\PrimordialParadox\PrimordialParadox.win` 388044 bytes at 00:50 (was 363212). No zip, no install step. |
| 20 | Tests and gates | 2 | 2 | 2 | 0 | gate 1 green, gate 2 red on 4 files, gate 3 `13 failed, 1155 passed` on this PC, gate 4 red on 33 of 178; the Windows/Pine split is still unwritten by TEST-CLASSIFY-33 `t_f64b44a4` (running). |
| 21 | Capture and demo tooling | 2 | 2 | 2 | 0 | `capture_title.py` green end to end today; `output\demo\run_001_verify.json` still `"ok": false` with `not_a_terminal` FAIL 5 of 7, and `play_demo.py --check` exits 0 while its own exact viewport score is 0.0 on the same 5 of 7. |
| 22 | Docs and repo hygiene | 2 | 2 | 2 | 0 | `README.md` at the root, 0 files matching `^licen`; LICENSE-AND-CREDITS `t_4fefed64` is ready, not done. |
| 23 | Slice route (row carried from yesterday) | n/a | 2 | 2 | 0 | `data\slice.json` 9 steps, hash unchanged since 20:39; three of its targets name no row (`drive_to_southampton`, `southampton_town_quay`, `quay_gate_checkpoint`) and `test_slice_route` fails 8 checks naming drive, arrival, gate and save. |

Sums, computed by `scores.py` in this run's workspace: 50 over 22 at the baseline (mean 2.273), 51 over 22 yesterday
(2.318), **53 over 22 now, mean 2.409**; with the carried route row, 55 over 23, mean 2.391. Two rows moved, each by
one point: row 3 up on a file that appeared during the audit, row 16 up on a test run that passed.

## 3. What moved, and the command behind it

Two rows moved. Row 3 moved because a file appeared under the tree while this audit was measuring it; row 16 moved
because a test run passed where it used to fail. Neither moved on a card's claim.

Row 3, the drive:

- `ls game/rooms` at 01:04 lists `rm_pp_boot`, `rm_pp_drive`, `rm_pp_ship`, `rm_pp_title`. At 00:47 the same command
  listed three rooms.
- `ls -l game/scripts/pp_drive/pp_drive.gml` is 29488 bytes at 00:52; `grep -o "rm_pp_drive\|obj_pp_drive\|scripts/pp_drive"
  game/PrimordialParadox.yyp` returns 6, 3 and 1 matches, with the `.yyp` written at 00:59.
- The build that proves the rest of the table ran 00:47 to 00:56 and compiled at 00:50, `PrimordialParadox.win` 388044
  bytes. It predates the room by 9 minutes. A row cannot be raised to 3 on a file that no build has compiled and no
  capture has shown, and it is not raised here.

Row 16, the art pipeline:

- `python -m pytest tests/test_look.py tests/test_title_art_v2.py tests/test_make_title_ui.py
  tests/test_make_title_world.py tests/test_title_bands.py tests/test_scene_palette_set.py tests/test_make_env_ship.py
  tests/test_quantize_concept.py -q`, 01:36, `2 failed, 128 passed, 97 warnings in 119.69s` (01:38).
- Both failures are `test_look`: `test_draw_colour_comes_from_a_palette_role` and `test_no_colour_literal_in_draw_code`.
  Every byte-level reproduction pin passed, which is the thing yesterday's 8 failures said could not be shown.
- The audit set this row at 2 on 11 failing art tests, then 8. It is 2 failures now, and the two that remain are about
  drawing code spelling a colour, not about a rebuild changing pixels. That is a 3 on the audit's own wording, and not
  a 4 because the live title crop carries 23 colours outside the palette.

Two things that did not move a score but moved the evidence behind one:

- The clean-room gate went from exit 0 (yesterday) to exit 1, on the four files of that same in-flight card.
- The NES art gate went from exit 0 with 24 failing to exit 1 with 33 failing. Same tool, stricter build.

## 4. The eight steps

Each row below names the command this run executed, its exit code or its result, and the verdict on the R40 scale.

**S1 TITLE: PARTIAL.** `tools\capture_title.py` exit 0 at 01:00, two frames at `score 1.000`, game closed on request.
The title runs and is capturable. The reproducibility pins under it pass (row 16), `test_look`'s two palette-role pins
are still red, and `test_title_path::test_continue_without_a_save_is_dim` is red in this run, so it is not proven clean.

**S2 CRAWL: PROVEN.** `output\crawl_mid.png` 4 colours, `output\crawl_end.png` 4 colours, both present and opened this
run, and `test_intro` and `test_text_reveal` are both absent from gate 3's 13 failures, so the text reveal pins hold.
The same verdict as yesterday on the same evidence; the START skip is still Nayil's manual check and unverified here.

**S3 DRIVE: PARTIAL.** `game\scripts\pp_drive\pp_drive.gml` 29488 bytes, `game\rooms\rm_pp_drive\` and `obj_pp_drive`
registered in the `.yyp` at 00:59. Yesterday this row was MISSING because no drive module, room or scene row existed.
The module and the room now exist. What is still absent: a build that contains them, any capture of the twelve shots,
and the scene row `drive_to_southampton`.

**S4 ARRIVAL: PARTIAL.** `data\dialogue\all.json` now carries `quay_gate_checkpoint` and `quay_gate_choice` as
dialogue rows, and `data\flags.json` carries `gate_passed`, `gate_truth`, `gate_bluff`, `gate_authority` and
`has_boarding_pass`. The map and the scene still do not exist: `data\maps\all.json` holds 2 maps, and the route's
`arrival` step fails in `test_slice_route` with `the map 'southampton_town_quay' is not in data/maps/all.json`. Note
the name collision: `quay_gate_checkpoint` is now a dialogue row id, while the route's `gate` step asks for a scene of
that name, which is still absent. A reader who greps the name will find a hit and be wrong.

**S5 BOARDING: PARTIAL.** `tests\test_scene_runner.py` passed on Pine shard 1. `ship_boarding` on `ship_small` carries
`music PP-05`, `say ship_rail_note`, `move`, `wait`, `setflag`, `end`. The boarding pass exists as a dialogue row,
`quay_dock_office_pass`, which sets `has_boarding_pass` (`data\dialogue\all.json` line 342 and line 370, pinned by
`tests\test_dialogue_v2.py` line 440), and no scene row reaches it: `ship_boarding` names `ship_rail_note` only. No
scene carries a `save` op.

**S6 FIRST FIGHT: PARTIAL.** `tests\test_first_fight.py` passed on Pine shard 1 and the encounter `tutorial_sailors` is
in `data\encounters\all.json`. Still unreachable: no scene op names it, and FIRST-FIGHT-WIRE `t_4a1a6662` is ready, not
done.

**S7 SAVE: PARTIAL.** `tests\test_save.py` and `tests\test_save_gameover.py` pass (the second on Pine shard 1), the save
contract is real, and no run has produced a save file: the tree contains only the probe fixture
`build\save_slot_probe\pp_save_01.original.json`. `grep -c '"save"' game\scripts\pp_scene\pp_scene.gml` returns 0.

**S8 GAME OVER: PARTIAL.** Yesterday this was MISSING with no test at all. `tests\test_save_gameover.py` exists now (19
test functions) and passed on Pine shard 1, and `game\scripts\pp_app\pp_app.gml` watches for `"defeat"`. No capture
shows a defeat, so the screen is tested as a contract and unproven as a picture.

So: one of the eight is PROVEN (the crawl, unchanged), seven are PARTIAL, and none is MISSING, where yesterday two were
MISSING (the drive and the game over). What changed is that both of those now have code and a test, and neither has a
picture or a build that reaches it.

## 5. The recording that exists

`output\demo\run_001.mp4` is still the 18:13 file, 4164230 bytes, 73.5 s, 768x720 h264 60 fps. Two checks on it, both
run or read this run, and they agree on the strict column and disagree on the loose one:

- `output\demo\run_001_verify.json` (written 18:14): `"ok": false`, `not_a_terminal` FAIL, `5 of 7 sampled frames are
  not the game: t=1.5 score 0.0, t=13.2 score 0.0, t=48.5 score 0.0, t=61.7 score 0.0, t=69.8 score 0.0`.
- `python tools\play_demo.py --check --video output\demo\run_001.mp4`, 01:12, exit 0: `PASS 4 of 7 sampled frames are
  the game's own picture`, with the same five samples at exact viewport `0.0` and palette share 0.113 on the three walk
  frames the tool calls an art finding.

The recording covers the title, the crawl and the walk. It covers no drive, no arrival, no gate choice, no boarding
pass, no fight, no save and no defeat. DEMO-RECORDER-FIX `t_3d0fc247` is the card that owns the tool; no capture card
owns a re-record after the drive lands.

## 6. The three things between this repo and Sunday's definition of done

1. **Three of the route's nine steps name content nobody wrote.** `data\slice.json` asks for scene
   `drive_to_southampton`, map `southampton_town_quay` and scene `quay_gate_checkpoint`; `data\scenes\all.json` holds 5
   rows and `data\maps\all.json` holds 2, and none of the three names is among them. This is the same blocker as
   yesterday in the same place, and it now has a failing test behind it: `test_slice_route` fails 8 checks spread over its
   drive, arrival, gate and save steps, by step id (`offload-audit-r24b-1.json`).
   Removing it: R21b DRIVE-SCENE `t_c27552e3` (todo) for the scene row, ARRIVAL-MAP-2 `t_db2995d7` (todo) for the quay
   map and gate scene, SHIP-DECK-MAP `t_a3fa132a` (todo) for the ship side. Three cards, three rows, all todo.

2. **The first fight still cannot be reached by playing.** The encounter exists and its test passes, and no scene op
   anywhere names `tutorial_sailors`; the only `battle` op in the five scenes is `battle percy` in `percy_lore_stop`
   (`data\scenes\all.json` read this run). FIRST-FIGHT-LIVE `t_87ee4228` (running) will prove a fight it cannot reach
   until the wire is in.
   Removing it: FIRST-FIGHT-WIRE `t_4a1a6662` (ready, builder), one trigger on `ship_small`.

3. **The save step has nothing to call.** `data\slice.json` has a `save` step whose own check reports `step save: the row
   names no trigger`, the scene command list has no `"save"` case, and no run has written a save file. The contract is
   tested and the route cannot invoke it.
   Removing it: SHIP-DECK-MAP `t_a3fa132a` (todo, job-discovery) is scoped to the cabin with the log terminal that writes
   the first save, so it owns the scene row; the mechanism is the open question below, because the runner has no `save`
   command for it to call. No other card on the board claims the step.

Outside the top three and still true: the clean-room gate is red on the four files of the drive card that is writing now
(transient, but it blocks any commit gate until the review rows land), the recorder still returns `ok: false`, and there
is no licence file at the root (`t_4fefed64`, ready).

Q: for gamedev, two questions this page cannot settle. First, the save: the route's `save` step fails its own check with
`step save: the row names no trigger`, and `game\scripts\pp_scene\pp_scene.gml` contains no `save` command at all
(count 0), while SHIP-DECK-MAP `t_a3fa132a` is scoped to "the ship's log terminal that writes the first save" and
requires every command in its scenes to be one the runner already implements. So either the save is a map trigger and
the route row gains a trigger name, or the runner gains the command. Which one is the contract, and does R26
`t_7098c5fe` (done) leave an op behind for it? Second, `quay_gate_checkpoint` now exists as a dialogue row id and is also
the scene id the route's `gate` step asks for; if the intent is one name for both kinds, the route says so and no card
on the board is writing the scene row.

## 7. Check for this page

- Every row carries a file, a command or a test result, and each of the four gates carries its own exit code from this
  run's output under `...\workspaces\t_d5ecf73f\`: `gate_1_check_data.out`, `gate_2_cleanroom.out`,
  `gate_3_pytest_windows.out`, `gate_4_nes_audit.out`, plus `build.out`, `capture.log`, `demo_check.log`,
  `probe_structure.out`, `png_colours.py`, `probe_board.py`, `scores.py` and `verify_page.py`. That workspace is the
  run's scratch directory and may be pruned, so every number the page states also carries the command that produced it
  and can be reproduced from the repository alone.
- Two rows moved and each moved on a command, not on a card's claim: row 3 on `ls game/rooms`,
  `ls -l game/scripts/pp_drive/pp_drive.gml` and a `.yyp` grep, and it was held at 2 rather than 3 because the build
  predates the room; row 16 on the eight-file art pytest run at 01:36.
- Two measurements I could not finish are labelled rather than guessed: the full Pine suite (two of three shards died on
  an upload timeout, one shard returned 429 passed and 17 failed), and the drive in the running game (no build contains
  it yet).
- The board statuses quoted in section 6 were read from `kanban.db` read-only at 01:10 (`probe_board.py`).
- A second read of this file, by `verify_page.py` at 01:58, finds 0 em dashes, 0 en dashes, 0 figure dashes and 0
  horizontal bars. The hyphens that remain are inside file names, card ids, command flags, the lane name, and the two
  compound words `clean-room` and `in-flight`.
