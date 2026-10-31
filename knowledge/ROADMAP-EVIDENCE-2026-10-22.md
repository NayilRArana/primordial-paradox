# Roadmap evidence, 2026-10-22 path: what a command proved, and what it did not

Card t_4b148e6d (R11), audit profile, measured 2026-10-24 between 20:11 and 20:18 Pacific.
Scope: this file only. I wrote no data, no scene, no test, no spec, and I changed no card.

The rule this page is built on: a card summary is a claim, a command is a measurement. Every result pasted below
is from a command I ran in this session, at the paths named, on the tree as it stood at 20:18 on 2026-10-24. Where
the roadmap's check cannot be run as written, the step is marked NOT PROVEN and the reason is given in plain words.

Two conditions of this measurement, stated before the evidence:

1. The tree is moving. `data/scenes/all.json` was written at 20:10, one minute before I started, by another lane. A
   green or red below is true at 20:18 and can change under the next worker.
2. One command writes. `python tools/nes_audit_all.py` rewrites `knowledge/NES-AUDIT.md`, `output/nes_audit/*.json`,
   `output/nes_audit_worst_3x.png` and the palette synergy report on every run, by design (`tools/nes_audit_all.py`
   lines 35 to 39). That happened at 20:13 because the roadmap's own gate names it. I hand-edited nothing outside
   this file; the audit's own report files are the tool's output, not my writing.

The roadmap under test: `ROADMAP-2026-10-22.md`. Its gate commands are section 5, lines 171 to 176.

---

## 1. Verdict, one line a step

| Step | Verdict | One line |
| --- | --- | --- |
| S1 title attract | NOT PROVEN | Four title captures fail the NES frame audit, and the 32 s attract capture the check asks for was not produced. |
| S2 intro crawl | NOT PROVEN | The crawl data and reveal machine pass their tests, but the skip rule as written is not in the code and two numbers disagree with the beat sheet. |
| S3 drive on the M3 | NOT PROVEN | The scene row `drive_to_southampton` does not exist, two route tests fail on it, and the gantry capture fails the gated frame audit. |
| S4 arrival Town Quay | PROVEN, data only | `22 passed`, exit 0, rerun by me. No engine was run. |
| S5 ship boarding | PROVEN, data only | The gangway scene ends on `end` with known commands, the ship tile set and the save tests pass. No engine was run. |
| S6 first fight | PROVEN, test only | `26 passed`, exit 0, rerun by me. The test recomputes from source, it does not execute GameMaker. |
| Gate: the four commands | NOT GREEN | `check_data` 0, `check_cleanroom` 0, `pytest tests -q` 1, `nes_audit_all` 1. |

Three of the six steps are green on the check the roadmap names for them (S4, S5, S6). Three are not (S1, S2, S3),
and each of those has a command behind the red, not an opinion. None of the six is proven as play: no engine was
run, so "proven" on this page means the data, the source or the test that the roadmap itself names.

---

## 2. S1. Title screen: attract loop, PRESS START, menu

Cards that claim it: R10 (t_8595b06c, done), R14 (t_becd6879, done, the fight cue), and the roadmap's own claim at
`ROADMAP-2026-10-22.md` lines 53 to 56 that the state is built and "what is missing is proof, not code".

The check as written: a 32 s attract capture at 256 x 240 that `python tools/nes_audit_all.py` passes as a frame;
one 2 frame full screen palette flash inside it; the menu opens on START and NEW GAME is the first entry.

What I ran, and what came back:

```
$ python tools/nes_audit_all.py
nes_audit_all: FAIL  184 file(s), 34 failing, 0 unmeasured
  FAIL capture*  output/title_run_1.png                     256x240  2 px  background_area x2, palette x1
  FAIL capture*  output/title_run_2.png                     256x240  2 px  background_area x2, palette x1
  FAIL capture*  output/title_run_reference_3x.png          256x240  2 px  background_area x2, palette x1
  exit: 1
```

`capture*` is the audit's own advisory marker (`tools/nes_audit_all.py` lines 21 to 23): window captures are
reported and never counted as a pass. A fourth capture also fails, `output/title_run_1_marks_overlay.png` at
14,776 px, which is a debug marks overlay rather than a frame. One capture of the title does pass:
`output/title_run_1_nes.png` is `"ok": true`, 256x240, 10 colours, 0 offending pixels
(`output/nes_audit/output__title_run_1_nes.json`). It is not the 32 s attract capture the roadmap asks for; it is
one quantised frame.

The menu and crawl half is proven at source level only, and it does pass:

```
$ python -m pytest tests/test_title_path.py -q      -> 13 passed in 0.73s, exit 0
$ python -m pytest tests/test_title_bands.py -q     -> 10 passed, 80 warnings in 2.86s, exit 0
$ python -m pytest tests/test_title_art_v2.py -q    -> 12 passed, 3 warnings in 10.02s, exit 0
$ python -m pytest tests/test_title_timing.py -q    -> 4 passed in 0.76s, exit 0
```

`tests/test_title_path.py` states in its own docstring (lines 6 to 9) that it reads the GML source and does not
run the machine. So "START opens the menu on NEW GAME" is proven about the source, not about a running game, and
the 2 frame full screen palette flash is proven nowhere I could run.

Verdict: NOT PROVEN. Reason: the frame the check names fails the audit as an advisory capture, and the attract
capture itself was not made in this session.

---

## 3. S2. Intro crawl

Cards that claim it: R07 (t_098da427, done) for the beat sheet's timing, and the roadmap line 64 for the data.

The check as written: six beats, 25 s total, skip allowed only after a beat completes, 45 step hold on START,
60 step ignore window after skipping, and the crawl ends while the title theme still has music left.

What I measured, and what came back:

```
$ python measure_roadmap.py
beat_sheet rows: 32
sum of seconds: 900
beats 1-2 (S1)           42 s  rows=[1, 2]
beats 3-6 (S2)           30 s  rows=[3, 4, 5, 6]
intro_text beats: 6 chars: 256 lines: 14 columns: 32
```

Three disagreements with the roadmap's own words, all measured:

1. `ROADMAP-2026-10-22.md` line 61 says the crawl is 25 s. The sheet's beats 3 to 6 sum to 30 s
   (`data/mechanics/pacing_recipes.json` `beat_sheet.beats`).
2. `ROADMAP-2026-10-22.md` line 64 says 258 characters. `data/intro_text.json` carries 256 over 6 beats, 14 lines.
3. The skip rule is not the rule in the code. `pp_title_step_intro` jumps the crawl to its end on any press of
   `menu`, `cancel` or `confirm`, whether or not a beat has completed (`game/scripts/pp_title/pp_title.gml` lines
   903 to 909). The two window constants that do exist are `PP_TITLE_OPEN_FADE 45` and `PP_TITLE_INTRO_HOLD 60`
   (`pp_title.gml` lines 94 and 42); neither is a "45 step hold on START" followed by a "60 step ignore window
   after skipping", and no test asserts that pair.

The tests that do exist pass:

```
$ python -m pytest tests/test_intro.py -q           -> 7 passed, 3 warnings in 0.93s, exit 0
$ python -m pytest tests/test_text_reveal.py -q     -> 10 passed in 0.74s, exit 0
```

Verdict: NOT PROVEN. Reason: the skip rule as written is not implemented, and neither 25 s nor 258 characters
matches the file the roadmap cites for them.

---

## 4. S3. First cutscene, the drive on the M3

Cards that claim it: R16 (t_9b2e63d2, done, the shot list), R01 (t_f5a7ca5c, done, spec 17), R14 (done, the cue).
R21, the card that owns the drive block in `data/scenes/all.json`, was deliberately not created until R16 landed
(`ROADMAP-2026-10-22.md` lines 150 to 153).

The check as written: the shot list sums to 178 s; 12 shots, 8 distinct locations, no shot under 6 s or over 20 s;
a capture of the gantry sign frame passes the NES audit; the chapter card fade is 24 steps and every other cut 12.

The shot list half is sound. My parse of `knowledge/DRIVE-SHOT-LIST.md` section 2, table rows only:

```
shot rows: 12
steps sum: 10680 = seconds 178.0
length column sum: 177.98 last running total: 178.0
distinct location prefixes: 8 ['Twyford Down', 'cathedral', 'city', 'docks', 'downland', 'gantry', 'open motorway', 'slip road']
min shot s: 10.03 max shot s: 18.63
shots under 6 s: [] over 20 s: []
```

The scene half is absent, and the suite says so out loud:

```
$ python -m pytest tests -q
FAILED tests/test_slice_route.py::test_a_step_resolves_the_one_id_it_names[drive]
FAILED tests/test_slice_route.py::test_a_scene_step_reaches_end_with_only_known_commands[drive]
2 failed, 1436 passed, 112 warnings in 237.80s (0:03:57)
exit 1
```

The failure text is the plainest evidence on the page:

```
E  AssertionError: step drive: the scene 'drive_to_southampton' is not in data/scenes/all.json
E  AssertionError: step drive: the scene 'drive_to_southampton' is not in data/scenes/all.json,
   so its commands cannot be read
```

The gantry capture also fails the gated frame audit:

```
  FAIL frame     output/drive_gantry_preview.png            256x240  2 px  background_area x1
```

`frame` scope is gated by the audit's own definition (`tools/nes_audit_all.py` lines 16 to 17: every
`output/*preview*.png` that is exactly 256x240), so this row is one of the 10 gated failures behind the exit 1.

Verdict: NOT PROVEN. Reason: the largest step in the path has no scene data at all, and its named capture fails the
frame audit. Only the shot list document is proven, and only as arithmetic.

---

## 5. S4. Arrival in Southampton

Cards that claim it: R15 (t_7e72fe1c, done), R03 (t_c024f8bc, **blocked** on the board at my measurement), R08
(t_3a52845d, done), R18 (t_6cd706d0, done), R12 (t_1140be15, done).

The check as written: the arrival map loads, the spawn point is on a walkable tile, every door has a target map and
spawn, no encounter marker within 6 tiles of the entry or a door, 1 marker per 40 to 60 walkable tiles,
`check_data` green.

What I ran:

```
$ python -m pytest tests/test_arrival_map.py -q
......................                                                   [100%]
22 passed in 1.02s
exit 0

$ python tools/check_data.py
check_data: all files pass
exit 0
```

`tests/test_arrival_map.py` is the test that carries each line of that check: both schemas, the 53 by 56 grid, the
entry spawn and every named spawn, every door resolving to a map and a walkable spawn, both flood fills, the marker
clearance and the 40 to 60 band, and the command set equal to `check_data.SCENE_COMMANDS`.

Verdict: PROVEN for every data check the test measures, and for `check_data` separately at exit 0. Not proven: that
the map loads in a running engine, because no GameMaker run happened here. Two side notes I did not rule on: R03 is
blocked on the board while its data passes, and the test files its own Q: for gamedev about the tiles at the entry.

---

## 6. S5. Ship boarding

Cards that claim it: R04 (t_a3fa132a, **running** at my measurement), R13 (t_1c42a535, done), and the roadmap's
check at lines 103 to 105.

The check as written: the gangway scene runs to `end` without an unhandled command; the deck map uses the 48 tile
ship set; the log writes a save that `python -m pytest tests/test_save.py -q` still accepts; the first save lands
inside the first fifteen minutes.

What I ran, and what came back:

```
$ python -m pytest tests/test_slice_route.py -q -k "boarding"
2 passed, 22 deselected in 0.67s
exit 0

$ python -m pytest tests/test_slice_route.py -q -k "reaches_end"
FAILED tests/test_slice_route.py::test_a_scene_step_reaches_end_with_only_known_commands[drive]
1 failed, 2 passed, 21 deselected in 0.76s

$ python -m pytest tests/test_slice_story.py -q     -> 32 passed in 2.16s, exit 0
$ python -m pytest tests/test_scene_runner.py -q    -> 9 passed in 0.71s, exit 0
$ python -m pytest tests/test_make_ship_tiles.py -q -> 9 passed, 3 warnings in 0.70s, exit 0
$ python -m pytest tests/test_save.py -q            -> 26 passed in 1.54s, exit 0
```

The scene itself, from `data/scenes/all.json` lines 6 to 22: `ship_boarding` on map `ship_small`, 11 commands
(`music`, `shake`, `wait`, `camera`, `wait`, `say`, `camera`, `move`, `wait`, `setflag`, `end`), ending on `end`.
Every one of those names is in the fifteen the runner implements, which is what `test_a_scene_step_reaches_end...`
checks and where only `drive` fails. The first save gate is 592 s, 9 min 52 s, inside the fifteen minutes, and
`tests/test_beat_sheet.py` asserts it (35 passed, exit 0).

Verdict: PROVEN for the four data and test checks. Not proven: that the gangway scene runs in the engine. Note that
R04, the card that owns this map and scene, was still running when I measured, so the map is not frozen yet.

---

## 7. S6. First fight

Cards that claim it: R05 (t_8a7ada73, done), R09 (t_6cd2cc3c, done), R02 (t_92ee7b8e, done, spec 18), R14 (done, the
fight cue), R17 (t_eab7904b, done, the spec review).

The check as written: a test that computes the first fight from the enemy row and proves it cannot be lost at full
aggression and dies to one command; damage per hit never above 5; the fight length falls in 45 to 60 s at the
authored numbers; the SECOND fight reaches SPARE through three TALK options with the deterministic fallback path.

What I ran:

```
$ python -m pytest tests/test_first_fight.py -q
..........................                                               [100%]
26 passed in 3.00s
exit 0
```

What that run is worth, in its own words (`tests/test_first_fight.py` docstring and the card's own handoff): it
reimplements the damage from `pp_battle_fight_damage` and the macros, it solves the fight length from beats 23 and
28, and it checks the TALK route against both meters. It does not execute GameMaker. The sheet's own numbers are
beat 23 at 48 s and beat 28 at 90 s (`measure_roadmap.py` output above), and the band of 45 to 60 s is asserted for
the authored first fight.

Verdict: PROVEN as a test, which is exactly what this step's check is. Not proven: anything about a running battle.

---

## 8. The gate, roadmap section 5, all four commands and their exit codes

```
$ python tools/check_data.py
check_data: all files pass
exit 0

$ python tools/check_cleanroom.py
check_cleanroom: 365 files scanned for 26 names and 12 phrases, 40 GML modules, 0 awaiting review,
6 downloaded map file(s) skipped, 242 OSM place name(s) exempt in 2 generated geography card(s)
check_cleanroom: no study reference, no foreign name, no foreign phrase, every module reviewed
exit 0

$ python -m pytest tests -q
2 failed, 1436 passed, 112 warnings in 237.80s (0:03:57)
exit 1
(failed: test_slice_route.py::test_a_step_resolves_the_one_id_it_names[drive] and
 ::test_a_scene_step_reaches_end_with_only_known_commands[drive])

$ python tools/nes_audit_all.py
nes_audit_all: FAIL  184 file(s), 34 failing, 0 unmeasured
exit 1
```

`output/nes_audit/SUMMARY.json` carries the split the console line does not. Read straight out of that file:

```
$ python gated_failures.py
verdict: FAIL files: 184 gated_failures: 10 advisory_failures: 30 exit_code: 1
gated failing files: 10 advisory failing files: 24
  GATED frame output/bg_battle_corridor_fight_preview.png [256, 240] problems: 11
  GATED frame output/bg_battle_corridor_text_preview.png [256, 240] problems: 7
  GATED frame output/bg_battle_deck_night_fight_preview.png [256, 240] problems: 9
  GATED frame output/bg_battle_deck_night_text_preview.png [256, 240] problems: 9
  GATED frame output/bg_battle_quay_dusk_fight_preview.png [256, 240] problems: 7
  GATED frame output/bg_battle_quay_dusk_text_preview.png [256, 240] problems: 7
  GATED frame output/bg_battle_wardroom_fight_preview.png [256, 240] problems: 8
  GATED frame output/bg_battle_wardroom_text_preview.png [256, 240] problems: 8
  GATED frame output/drive_gantry_preview.png [256, 240] problems: 1
  GATED frame output/gameover_preview.png [256, 240] problems: 4
```

The ten gated failures are the eight `bg_battle_*` preview frames, `output/gameover_preview.png`, and
`output/drive_gantry_preview.png`. The 24 advisory failing files are contact sheets and window captures; the
remaining 6 in `advisory_failures: 30` are palette synergy pairs. The exit code is 1 only for gated rows
(`tools/nes_audit_all.py` lines 837 to 845).

Two of the four gate commands are green. The suite is red on one root cause, the missing drive scene. The art gate
is red on ten frames, one of them the drive gantry the roadmap names as S3's capture.

---

## 9. What is NOT PROVEN, in plain words

1. S1's attract capture. No 32 s capture exists that passes the frame audit. The four title captures fail as
   advisory rows, and the one passing capture is a single quantised frame.
2. S1's two frame palette flash. No command I ran measures it.
3. S2's skip rule. The code skips to the end of the crawl on any press, mid beat or not.
4. S2's 25 s and 258 characters. Both disagree with the files they cite (30 s, 256 characters).
5. S3 entirely as a built scene. `drive_to_southampton` is not in `data/scenes/all.json`.
6. S3's gantry capture. It fails the gated frame audit with 2 offending pixels.
7. Every engine run. No GameMaker process was started, so no step is proven as play. The green checks above are
   proof about data, source and tests.
8. R03 and R04 are not done on the board (blocked and running), so the map data behind S4 and S5 can still move.

Two clock disagreements I measured beside the rows: the S5 heading spans 90 s (9:12 to 10:42) while beats 25 to 27
sum to 122 s, and the S2 heading says 25 s while beats 3 to 6 sum to 30 s. The beat sheet card (t_098da427) has also
posted the S5 and S6 clock questions and `data/mechanics/pacing_recipes.json` `checks.first_interior_seconds` 442
against the sheet's 370 to gamedev. I measured the row totals and ruled on none of them.

---

## 10. How to rerun this page

From the repository root, in this order. The first four are the roadmap's own gate.

```
python tools/check_data.py
python tools/check_cleanroom.py
python -m pytest tests -q
python tools/nes_audit_all.py

python -m pytest tests/test_beat_sheet.py tests/test_arrival_map.py tests/test_first_fight.py -q
python -m pytest tests/test_title_path.py tests/test_title_bands.py tests/test_title_art_v2.py tests/test_title_timing.py -q
python -m pytest tests/test_intro.py tests/test_text_reveal.py -q
python -m pytest tests/test_slice_route.py -q
python -m pytest tests/test_slice_story.py tests/test_scene_runner.py tests/test_make_ship_tiles.py tests/test_save.py -q
```

The two arithmetic checks in sections 3 and 4 come from `measure_roadmap.py`, which I wrote for this card and which
reads `data/mechanics/pacing_recipes.json`, `data/intro_text.json` and `knowledge/DRIVE-SHOT-LIST.md` and writes
nothing. The gated split in section 8 comes from `gated_failures.py`, which reads `output/nes_audit/SUMMARY.json`.
The board status beside each step comes from `board_status.py`, a read-only SQLite open of
`kanban/boards/nayil-ops/kanban.db`. All three are in this card's workspace, not in the repository, because this
card's scope is this file.

Written by audit, 2026-10-24. Sources for every line: the command outputs pasted above, `ROADMAP-2026-10-22.md`, and
the file paths and line numbers named beside each claim.
