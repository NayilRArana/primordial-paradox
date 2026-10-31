# GATE-GREEN 2026-10-26 06:12

Card `t_41766656` (AUTO-GATE-GREEN, testing lane). First run of the day, so this is a full pass and not a
delta: no `GATE-GREEN-2026-10-26*.md` existed when the run started.

Check named before work started: the `SUMMARY` line and the `FAILED` lines inside `results_txt` of
`data/results/offload-gate-0.json`, `-1.json`, `-2.json`, compared field by field against the previous
run's same three files (`offload-gate-*.json`, written 2026-10-25 18:34 to 18:36), plus this machine's own
pytest line for the five files the Pine runner does not carry and for the one row Pine reports red
(`<workspace>\Shared\projects\arananet\pine\OFFLOAD.md`).

No key was opened or printed. `PINE_SANDBOX_API_KEY` is read from the environment by `pine_client.py` only
(`<workspace>\Shared\projects\arananet\pine\pine_client.py`). ART-BIBLE RULE 0 was not needed
for this card: nothing here judges art, the one red is a report string.

## 1. Tree, interpreter, launch

- `git rev-parse --short HEAD` -> `ae3a6cb`, `git status --porcelain | wc -l` -> `1274`,
  `ls tests/test_*.py | wc -l` -> `92`, read at 06:11 in `<repo>`.
- Interpreter `<home>/AppData/Local/Python/bin/python.exe`, 3.14.7, `pinesandbox` 0.3.2 confirmed
  importable before the launch (the Hermes venv interpreter fails this offload with `PineConfigError`;
  that was measured on 2026-10-25 and not repeated today).
- `python pine_offload.py --shards 3 --name gate` at 06:12, background session `proc_e4f600a56eb3`, pid 10960,
  log `gate-run.log` in this run's workspace. Tool line: `zip bytes 14823545 files 89 shards 3`,
  `output/: shipping 34 tracked file(s), skipping 1694 by-product(s)`. All three shards report
  `upload_attempts: 1`, so the `PINE-UPLOAD-DROP` retry path did not fire.

## 2. Merged count

| shard | passed | failed | skipped | deselected | errors | file |
|---|---|---|---|---|---|---|
| gate-0 | 464 | 0 | 6 | 3 | 0 | `data/results/offload-gate-0.json` |
| gate-1 | 562 | 0 | 30 | 0 | 0 | `data/results/offload-gate-1.json` |
| gate-2 | 527 | 1 | 16 | 0 | 0 | `data/results/offload-gate-2.json` |
| total | 1553 | 1 | 52 | 3 | 0 | |

Windows-only nodes, run locally at 06:17 (memory stayed well under the 4 GB line, 53 tests, 11.55 s):
`tests/test_build_inputs.py`, `tests/test_test_inputs.py`, `tests/test_sync_art.py`,
`tests/test_mix_check_v3.py::test_the_script_still_runs_on_a_slice`, and the two `tests/test_project.py`
nodes the runner deselects -> `53 passed`. No SKIP and no errored row is counted as a pass anywhere above.

## 3. Trend against the last run

Last run: 2026-10-25 18:31, HEAD `0b5dd01`, 1533 passed / 5 failed / 52 skipped / 3 deselected
(`GATE-GREEN-2026-10-25-1831.md`, artifacts `offload-gate-0/1/2.json` at 18:34 to 18:36).

| | passed | failed |
|---|---|---|
| 2026-10-25 18:31 (`0b5dd01`) | 1533 | 5 |
| 2026-10-26 06:12 (`ae3a6cb`) | 1553 | 1 |

All five of the old reds are green today, so none of them was carried forward:

- `tests/test_enemy_phases.py::test_no_enemy_name_appears_anywhere_in_the_director_code`
- `tests/test_make_battle_bg.py::test_the_committed_strips_are_what_the_generator_writes`
- `tests/test_prometheus_interrupt.py::test_no_enemy_name_scene_id_or_route_name_is_hardcoded_in_the_director`
- `tests/test_scene_palette_set.py::test_the_committed_cloud_ground_is_the_crop_its_generator_builds`
- `tests/test_make_exterior_maps.py::test_the_three_shipped_town_files_are_what_the_generator_writes`

## 4. The one red, classified

`tests/test_scene_palettes.py::test_the_check_reports_its_numbers_so_a_reviewer_can_read_them`
in `offload-gate-2.json`: `AssertionError: output/scene_palettes.json is stale: it is not what the checker
writes today. Regenerate it with python tools/check_scene_palettes.py --json output/scene_palettes.json
and commit the result (card t_8690e219).`

Class: **windows only, in the inverted direction** (it passes on Windows and fails on Pine), which makes it
a platform leak rather than a regression. Evidence, in the order it was measured:

1. Windows, shared tree at `ae3a6cb` at 06:14: `python -m pytest tests/test_scene_palettes.py -q --tb=line`
   -> `10 passed in 2.50s`. `git diff --stat -- output/scene_palettes.json` is empty, so the committed copy
   is the one on disk and the fresh run agrees with it.
2. The exact zip: `pine_offload.build_zip()` rebuilt at 06:25 was `14877069` bytes, extracted, and the
   report in it is `4f27ee7f698f13f3f7b125d93bec9e63472085cd04a3fb4667febf72cd677a48`, byte for byte the
   committed copy. The same test inside that extracted tree: `10 passed in 6.09s`. So nothing is missing
   from the zip; this is not the (b) class.
3. Pine, fresh checker output from `--cmd 'cd projects/primordial-paradox && python
   tools/check_scene_palettes.py --json /tmp/f.json --quiet'` (`offload-palrep3-0.json`): `ship_frame`
   reports `colours: 10 in the frame`, `background: 240 blocks, 11 distinct colour sets, 4 palette(s)` with
   the same four triples as the committed copy, and `title_car_frame` the same four colours and
   `sprite palette #004058 #005800 #f8f8f8`. Every measured number is identical.
4. The only field that moves is one string, the palette file the frame check read:
   committed and Windows `  palette: data\nes_palette.json (55 usable of 64 entries)`, Pine
   `  palette: data/nes_palette.json (55 usable of 64 entries)`. The committed report pins that line inside
   `report`, and the test compares the parsed JSON, so the separator alone is the whole failure.

Not a real regression, so no fix card was raised against a commit. It is still a defect worth its own card
because the row will be red on every Pine run until the string is normalized or the node is deselected:
**`t_8bb7bdea` PALETTE-REPORT-LINUX, owner gamedev**. That lane owns `tools/check_scene_palettes.py`,
`tools/nes_composite_check.py` and the report; this lane does not edit it.

## 5. Cost of this run

`python <workspace>\Shared\projects\arananet\manager\guard\usage_ledger.py --day 2026-10-26`,
testing row at 06:25: fresh 146,977 tokens (input plus output), cache read 3,448,448 tokens, 57 calls,
3 sessions. One full suite pass, then three single-node Pine probes (`palrep`, `palrep2`, `palrep3`) used
only to name the differing string, which is the cost this page's check 4 asks about: the first gate run was
clean enough to report, and the probes exist to classify, not to re-run the suite.
