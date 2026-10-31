# GATE-GREEN 2026-10-24 R2

Card `t_b0f9d9e1` (AUTO-GATE-GREEN, testing), run at 22:52 on 2026-10-24. This is the second gate page of the
day: `knowledge/GATE-GREEN-2026-10-24.md` is card `t_1649d513`'s 04:44 run, and this page is filed as R2 so
neither card's numbers overwrite the other's.

Check named before work started: the three `pytest` summary lines inside `results_txt` of
`data/results/offload-gate-*.json`, plus the Windows suite's own line for the rows Pine cannot carry.

No key was opened or printed; `PINE_SANDBOX_API_KEY` is read from the environment by `pine_client.py` only
(`<workspace>\Shared\projects\arananet\pine\OFFLOAD.md`).

## Tree and command

- `git rev-parse --short HEAD` -> `75161aa`, `git status --porcelain | wc -l` -> 1015, `ls tests/test_*.py`
  -> 85, read at 22:52 in `<repo>`.
- `<home>/AppData/Local/Python/bin/python.exe pine_offload.py --shards 3 --name gate`, start 22:52:40,
  tool line `zip bytes 13985684 files 82 shards 3`.

## 1. Two shards lost the upload, and the retry

| shard | result | line | file |
|---|---|---|---|
| gate-0 | error | `[Errno 10054] An existing connection was forcibly closed ... op=PUT /v1/sessions/main/files` | `data/results/offload-gate-0.json` |
| gate-1 | error | `[Errno 10053] An established connection was aborted ... same op` | `data/results/offload-gate-1.json` |
| gate-2 | completed | `458 passed, 27 skipped, 3 deselected, 20 warnings in 48.22s` | `data/results/offload-gate-2.json` |

Not the size ceiling: 13,985,684 bytes is a third of the 40,000,000 in `OFFLOAD.md`. Retried once each,
alone, with its own 28 and 27 files (`files[i :: a.shards]`, `pine_offload.py`):

| attempt | line | file |
|---|---|---|
| gate-r0 | `3 failed, 369 passed, 12 skipped, 86 warnings in 76.01s` | `data/results/offload-gate-r0-0.json` |
| gate-r1 | `2 failed, 598 passed, 11 skipped, 6 warnings in 34.22s` | `data/results/offload-gate-r1-0.json` |

Partition checked: 82 files named across the three completed shards, 82 unique, no duplicate, none
missing. Cost 0.0121 + 0.0064 + 0.0046 = 0.0231 USD of Computer time from `est_computer_usd`.

## 2. Merged count and trend

| shard | passed | failed | skipped | deselected | errors |
|---|---|---|---|---|---|
| gate-2 | 458 | 0 | 27 | 3 | 0 |
| gate-r0 | 369 | 3 | 12 | 0 | 0 |
| gate-r1 | 598 | 2 | 11 | 0 | 0 |
| total | 1425 | 5 | 50 | 3 | 0 |

1483 rows, 0 ERROR rows, so nothing hides behind a collection failure.

| run | passed | failed | errors | source |
|---|---|---|---|---|
| `triage`, 2026-10-22 15:30 | 725 | 24 | 0 | `knowledge/TEST-TRIAGE-PINE-2026-10-22.md` section 6 |
| `pinem`, 2026-10-24 17:34 | 1330 | 2 | 0 | `knowledge/PINE-HONEST-2026-10-24.md` |
| `gate`, 2026-10-24 22:52 | 1425 | 5 | 0 | `data/results/offload-gate-*.json`, this page |

The 2 reds of `pinem` were the drive rows of `tests/test_slice_route.py` (builder card `t_c27552e3`); both
are green in this run and no FAILED line names that file (`data/results/offload-gate-2.json`). All 5 new
reds are classified below, and none is a defect in a lane's code.

## 3. The 5 reds

| test | class | evidence | owner |
|---|---|---|---|
| `test_eye_drive.py::test_one_frame_per_shot_and_twelve_of_them` | b, zip gap | `eye_critic.EyeError: run the sampler first: .../output/drive_frames/drive_shot_01.png is missing` | pine runner, fixed here |
| `test_eye_drive.py::test_measurement_reports_colours_and_attribute_areas` | b, zip gap | same fixture, same missing frames | pine runner, fixed here |
| `test_eye_drive.py::test_model_chain_falls_back_on_a_per_day_quota_refusal` | b, zip gap | same fixture, same missing frames | pine runner, fixed here |
| `test_scene_runner.py::test_runner_command_list_and_switch_agree_in_both_directions` | tree moved under the run | `the runner's command list changed; spec 06's table has to change with it` | gamedev, card `t_531bc76c` |
| `test_ship_deck.py::test_the_runner_command_list_and_the_checker_agree` | tree moved under the run | `pp_scene_commands() lists 16 commands, the card pins 15` | gamedev, card `t_531bc76c` |

The two tree-moved rows: the zip carried `game/scripts/pp_scene/pp_scene.gml` with `flash` in its 16-name
command list against a test file that still pinned 15. Both files were rewritten at 22:57:47 and 23:00:50,
after the zip. Green on the current tree, measured 23:02:
`python -m pytest tests/test_eye_drive.py tests/test_scene_runner.py tests/test_ship_deck.py -q
-p no:cacheprovider --tb=line` -> `40 passed in 8.74s`. Card `t_531bc76c` (DRIVE-FLASH, gamedev) is that
lane; this card edits none of it.

## 4. The zip gap fixed in `pine_offload.py`, and the proof

`output/` ships tracked files only, so the two untracked capture folders were dropped whole.
`tools/eye_drive.py` `sample_frames()` reads `output/drive/pp_drive_shot_01..12.png` (69,625 bytes, 17
files) and writes `output/drive_frames/drive_shot_01..12.png` (52,089 bytes). Change:
`OUTPUT_KEEP_PREFIXES = ("output/drive/", "output/drive_frames/")` plus one condition in `build_zip()`;
backup `pine_offload.py.bak-20261024-t_b0f9d9e1`. No test edited, no other lane's file touched.

| attempt | zip | line printed | result |
|---|---|---|---|
| frames only | `zip bytes 14011354 files 1 shards 1` | `1 failed, 6 passed in 2.02s`, `shots without a captured frame: [1..12]` | `data/results/offload-gate-eye-0.json` |
| frames and sources | `zip bytes 14044644 files 1 shards 1` | `7 passed in 1.60s` | `data/results/offload-gate-eye2-0.json` |

The first attempt was not enough because `output/drive_frames/_drive_eye_results.json` holds absolute
`D:\` paths from the machine that wrote it, so the far side has to rebuild it from the source captures.
Cost of the fix: +58,960 zip bytes against a 40,000,000 ceiling.

## 5. Windows side

1. `python -m pytest tests/test_build_inputs.py tests/test_test_inputs.py tests/test_sync_art.py tests/test_project.py tests/test_mix_check_v3.py -q -p no:cacheprovider --tb=line`
   -> `1 failed, 55 passed in 9.19s`, all four files and the three deselected nodes Pine refuses.
2. `python -m pytest tests -q -p no:cacheprovider --tb=no -rfE`
   -> `1 failed, 1513 passed, 112 warnings in 254.10s (0:04:14)`, 0 errors.

The one red is `tests/test_test_inputs.py::test_no_test_skips_on_a_missing_input_and_every_fixture_is_committed`.
`tools/check_test_inputs.py` `check()` returns 16 problems at 23:04: `MISSING FROM COMMIT
assets/audio/pp_drive/mix_check_v3.py`, `mix_check_v3.json`, `pp_drive_v3_humanized.wav`,
`assets/audio/pp_01_title/pp_01_title.wav`, and `MISSING FROM COMMIT output/drive/pp_drive_shot_01.png`
through `_12.png`. Class: real, untracked fixtures. Already owned by `t_d2c52f15` (gamedev, running, group
B) and `t_c31f9295` (audit, blocked, the four audio sources); this gate added its 16 paths to
`t_d2c52f15` rather than raise a duplicate card. The 2026-10-22 card for this row, `t_6fe82061`, is `done`
and fixed a different cause (`tests/test_palette_synergy.py:132`).

## 6. Not proven here

- 50 skips and 3 deselected nodes are not passes; the Windows run in section 5 is where those rows are
  measured (`data/results/offload-gate-2.json`).
- The 2 tree-moved rows are green against the 23:02 tree, not against the snapshot the zip carried, and
  the full suite was not re-run after the `flash` edit landed (`data/results/offload-gate-r1-0.json`).
- `output/drive/` and `output/drive_frames/` travel in the zip but are still untracked, so a clean
  checkout still fails the same row (`tools/check_test_inputs.py` output above, card `t_d2c52f15`).
- RULE 0 read at `knowledge/ART-BIBLE.md` line 283. Nothing here sets or overrides an art ruling.
