SUPERSEDED (2026-11-01, manager decision): Nayil's order is exactly three battles, so the 180 s take below, built around a deck hound fight and a forced defeat (card t_866814e6), is retired. `full` is the 253.5 s three battle take from data/demo/run_002.json; the 180 s highlights recut is left to the demo card.

# SHOT-TABLE, 2026-11-01: the 180 s take is data the recorder reads

Superseded in one respect, 2026-11-01 (card t_866814e6): the six shot lengths below (16.00, 13.00, 10.03, 40.00,
34.00 and 66.97) were the plan's budget, and the take on disk now spends its 180.00 s differently (16.00, 13.00,
10.03, 16.53, 21.43 and 103.00) because the build reaches the gate without the town walk and the TALK fight runs
46.33 s on screen. What is written below about the recorder, the validator, `BEAT_CUES` and the command still holds.
The reason for the deviation, the map triggers, the encounter row and the forced defeat are in
`knowledge/DEMO-INTEGRATION-2026-11-01.md`; the three fight take this table's successor replaced is now
`data/demo/run_three.json` and the table `full-three`.

Card t_fb7e8271 (child of t_785b61f0, "Recut nightly to full 180s with dock, TALK fight and save ending"),
job-discovery lane. Nothing here is a rewrite of S5 or S6: the scene hooks and the route are unchanged, and the take is
played through the same public steps a player uses.

## What changed

1. `data/demo/shot_table.json` is new. It holds the shot table as data: six shots (S1 to S6) and six sub-shots
   (S5.1, S5.2, S6.1 to S6.4), each with its length in seconds, its start and end step on the 60 step clock, the beats
   of knowledge/DEMO-SCRIPT.md section 3 it comes from, and the `BEAT_CUES` name of the line the game's own log has to
   write when the shot is on screen. The six shot lengths are 16.00, 13.00, 10.03, 40.00, 34.00 and 66.97, which is
   180.00 s; the table's own tolerance is 1.0 s and its take band is the card's 170.0 to 190.0 s.
2. `tools/play_demo.py` reads it. `--shot-table NAME` loads the named table, validates it before anything is launched,
   takes the script the table names (`data/demo/run_002.json`), and applies the table's own `required_beats` and
   `end_step` to the run. New functions: `load_shot_table`, `shot_table_names`, `shot_table_seconds`,
   `shot_table_markers`, `narration_fields`, `validate_shot_table`, `apply_shot_table`, `validate_shot_table_script`,
   `shot_table_rows`, `print_shot_table`, `shot_table_report`, `shot_table_check`.
3. `BEAT_CUES` gains two rows the take needs at its end: `S6 game over` (`PP: game over frame`) and
   `S6 continue` (`PP: game over, CONTINUE restored the last save`). The game writes both
   (`game/scripts/pp_battle_director/pp_battle_director.gml:1407` and `:787`).
4. `validate_shot_table` refuses the four ways this table has been wrong or could go wrong: a plan whose seconds do
   not sum to the total inside its tolerance, a row whose start does not meet the row above it, a marker that is not a
   row of `BEAT_CUES` (so no log line could ever satisfy the shot), and a narrator, narration or voice over field,
   because this take carries no narration. A sub-shot's markers have to be exactly its shot's markers.
5. `data/demo/run_002.json` no longer stops at the defeat. Four beats finish the take, all on the same beat 29 and 27
   rows the tail already used: `r086` waits on the game over card's own line, `r087` presses CONTINUE (the row is lit
   because the ship's log save at 117.07 s is on disk), `r088` reads the line that says the save came back, and `r089`
   is one press in the loaded cabin so the last frames are the log and not an empty room. `checks.required_beats`
   gains `S6 game over`.
6. `tests/test_demo_shots.py` grows ten pins: the six shots and the sum, the steps meeting end to end and the seconds
   being their steps, the four endings the card names, the table and the script asking for the same log lines, the
   table naming a script that exists, no narrator field, the game over and CONTINUE beats in the script, the
   documented command, the recorder's own validator accepting the table, the recorder knowing every line the table
   names, the validator refusing a short plan, an unknown line, a gap and a narrator, and a take that never reached
   the game over being failed by that name.
   `tests/test_play_demo_audio.py::test_check_final_asks_the_verifier_for_the_shipping_answer`'s fake verifier takes
   the new `shot_table` keyword.

## The command

```
cd "<repo>"
python tools\play_demo.py --shot-table full
python tools\play_demo.py --shot-table full --check
```

`python tools\play_demo.py` with no arguments still plays `data/demo/run_002.json` and still writes
`output/demo/run_002.mp4`, so the nightly is unchanged; `--shot-table full` is the same take with the plan's own rows
printed, applied and checked.

## Measured this run, 2026-11-01

- `python tools\play_demo.py --shot-table full --dry-run` -> exit 0. `shot table 'full': 12 rows, 180.00 s (tolerance
  1.00 s, take band 170.0 to 190.0 s), script data/demo/run_002.json`, `run_002: 92 events, 180.0 s, 60 fps`, the last
  beat `r089` at 169.00 s, `beats covered by the script: 1, 2, 3, 4, 5, 7, 18, 20, 22, 23, 25, 26, 27, 28, 29`, and
  `shot table 'full' sums to 180.00 s against 180.00 s plus or minus 1.00 s: inside`.
- `python tools\play_demo.py --dry-run` (no flag) -> `run_002: 92 events, 180.0 s, 60 fps`, exit 0.
- `python tools\play_demo.py --script data\demo\run_001.json --dry-run` -> `run_001: 13 events, 71.0 s, 60 fps`, so the
  old take is still playable by name.
- `python -m pytest tests/test_demo_shots.py -q` -> `27 passed` (the four deck and map rows the 2026-11-01 testing note
  recorded as red are green in this working tree, because the level lane's `data/maps/all.json` is here uncommitted).
- `python -m pytest tests/test_play_demo.py tests/test_play_demo_audio.py tests/test_capture_quiet.py
  tests/test_demo_shots.py -q` -> `113 passed`.
- `python -m pytest tests/ -q -k "demo or play_demo or judge_panel or capture"` -> `265 passed`.
- `python tools/check_data.py` -> exit 0, `check_data: all files pass`.
- `python tools\play_demo.py --shot-table full --check --video output\demo\nightly-2026-10-26.mp4` -> exit 1, and the
  new row reads `FAIL the shot table 'full' is not met: 73.483 s of video is outside the 170.0 to 190.0 s band the
  shot table names; the game's log never named 11 of its lines: S1 title, S2 crawl, S3 drive, S4 gate, S5 office,
  S5 boarding, S6 talk fight, S6 hound fight, S6 ship log save, S6 game over, S6 defeat`. The check is a gate and not
  a print: the 73 s take is refused by name.

- `python tools\idle_check.py -> exit 4` (see "Not measured: the take itself" below).
- The plan on the real clock, no window: a harness in the task workspace loads `shot_table.json`, applies the table to
  `run_002.json`, and plays it through the shipped `Replay` with a stub key sender and a stub window that always
  reports focus, against a log that never names a beat. Result: `elapsed 180.50 s for a 10800 step plan (180.00 s) plus
  the 30 step hold`, 57 key presses, 14 holds down and 14 up, and the last four events fired in order:
  `r086 marker 'PP: game over frame' at 157.02 s`, `r087 key confirm at 162.00 s`,
  `r088 marker 'PP: game over, CONTINUE restored the last save' at 163.00 s`, `r089 key confirm at 169.00 s`, with the
  tape holding to 180.50 s. The 14 failures it reported are all `the log never carried ..., the step ... was used
  instead`, which is the documented marker fallback: a marker is an accelerator and never a stop, so a take that loses
  a line still runs to the end and then fails by that line's name. What this proves is the clock and the ordering, not
  the game's own log.

## Not measured: the take itself

```
python tools\idle_check.py -> exit 4
P: idle gate REFUSED: a desktop automation is running (codex-computer-use-swift.exe, codex.exe) ...
```

`tasklist` this run: `codex.exe` pid 22132 and `codex-computer-use-swift.exe` pid 26764, both in the Console session.
So no window may open, `python tools\play_demo.py --shot-table full` would refuse at the gate before recording, and no
180 s take exists from this run. That is the same wall the gamedev lane hit on 2026-10-27 and the testing lane recorded
on 2026-11-01, and the gate is not to be defeated to get past it. The take is card t_688422b1's ("Record full 180
second take through game over"), and the two commands above are its resume once the desktop is quiet.

What a take is still expected to show and this run could not: that the game's own log carries all eleven lines in one
run, and that the tail's CONTINUE press lands on a game over card whose CONTINUE row is lit. Each line has a real
emitter in the build (checked here: `PP route: step <id> handed to step <next>` at pp_app.gml:910 with :801, the TALK
pick at pp_battle_text.gml:621, `PP: ship's log` at pp_overworld.gml:591, the game over card at
pp_battle_director.gml:1407, CONTINUE at :787), and the deck, the office and the save are pinned by the tests above,
but the exact rows a live run writes are the take's own measurement and not this file's claim.

## Not touched

`game/scripts/pp_battle*` (the battle lane), `data/maps/all.json` and `data/slice.json` (the level lane), the S5 and S6
scene data, and `knowledge/DEMO-180-TAKE-2026-11-01.md` (the testing lane's note). Nothing is committed: the working
tree carries this card's change beside the level lane's uncommitted map rewrite.
