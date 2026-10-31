# GATE-GREEN 2026-10-25

Card `t_57ca9886` (AUTO-GATE-GREEN, testing), run at 04:55 on 2026-10-25. Filed as a new page because the
2026-10-24 pages are other cards' runs.

Check named before work started: the `SUMMARY` line and the `FAILED` lines inside `results_txt` of
`data/results/offload-gate-*.json`, plus this machine's own pytest line for the rows Pine does not carry
(`<workspace>\Shared\projects\arananet\pine\OFFLOAD.md`).

No key was opened or printed. `PINE_SANDBOX_API_KEY` is read from the environment by `pine_client.py` only
(`<workspace>\Shared\projects\arananet\pine\pine_client.py`).

ART-BIBLE RULE 0 was read at `knowledge/ART-BIBLE.md` line 283. Nothing in this page sets, changes or
overrides an art ruling; the two palette rows below are reported, not judged.

## 1. Tree and command

- `git rev-parse --short HEAD` -> `5f290c5`, `git status --porcelain | wc -l` -> `1058`, `ls tests/test_*.py`
  -> `85`, read at 04:55 in `<repo>`.
- `<home>/AppData/Local/Python/bin/python.exe pine_offload.py --shards 3 --name gate`, start 04:55:52,
  tool line `zip bytes 14198743 files 82 shards 3` (`pine_offload.py`).

HEAD moved since the 2026-10-24 22:52 page (`75161aa`): `5f290c5` is 15 commits later, and
`tests/test_check_data.py`, `tests/test_eye_drive.py`, `tests/test_palette_synergy.py`,
`tests/test_scene_palette_set.py`, `tests/test_scene_runner.py` and `tests/test_ship_deck.py` are among the
files those commits touched (`git diff --name-only 75161aa..HEAD -- tests/`).

## 2. Two shards lost the upload again, and the retry

| shard | result | line | file |
|---|---|---|---|
| gate-0 | error | `ConnectionError: [Errno 10054] An existing connection was forcibly closed ... op=PUT /v1/sessions/main/files` | `data/results/offload-gate-0.json` |
| gate-2 | error | same `[Errno 10054]`, same op | `data/results/offload-gate-2.json` |
| gate-1 | completed | `605 passed, 12 skipped, 250 warnings in 60.30s` | `data/results/offload-gate-1.json` |

This is the same failure the 2026-10-24 page recorded on two of three shards, not a size ceiling: 14,198,743
bytes is a third of the 40,000,000 in `OFFLOAD.md`. Each lost shard was retried alone, with the file list
`files[i :: 3]` that `pine_offload.py` itself computes (`pine_offload.py` line 357):

| attempt | files | line | file |
|---|---|---|---|
| gate-r0 | 28 | `1 failed, 372 passed, 12 skipped, 86 warnings in 96.47s` | `data/results/offload-gate-r0-0.json` |
| gate-r2 | 27 | `2 failed, 467 passed, 27 skipped, 3 deselected, 79 warnings in 41.46s` | `data/results/offload-gate-r2-0.json` |

Partition checked: 28 + 27 + 27 = 82 files, one per file in `tests/test_*.py` after the offloader's own
exclusions, no duplicate and none missing (`scratch/shard_list.py` against `pine_offload.py` `main()`).
Computer time spent: 0.0068 + 0.011 + 0.0059 + 0.004 = 0.0277 USD from `est_computer_usd`.

## 3. Merged count, trend, and the three reds

| shard | passed | failed | skipped | deselected | errors |
|---|---|---|---|---|---|
| gate-1 | 605 | 0 | 12 | 0 | 0 |
| gate-r0 | 372 | 1 | 12 | 0 | 0 |
| gate-r2 | 467 | 2 | 27 | 3 | 0 |
| total | 1444 | 3 | 51 | 3 | 0 |

1501 rows measured, 0 ERROR rows, so nothing hides behind a collection failure.

| run | passed | failed | errors | source |
|---|---|---|---|---|
| `triage`, 2026-10-22 15:30 | 725 | 24 | 0 | `knowledge/TEST-TRIAGE-PINE-2026-10-22.md` |
| `pinem`, 2026-10-24 17:34 | 1330 | 2 | 0 | `knowledge/PINE-HONEST-2026-10-24.md` |
| `gate`, 2026-10-24 22:52 | 1425 | 5 | 0 | `knowledge/GATE-GREEN-2026-10-24-R2.md` |
| `gate`, 2026-10-25 04:55 | 1444 | 3 | 0 | `data/results/offload-gate-*.json`, this page |
| Windows suite, 2026-10-25 05:04 | 1529 | 0 | 0 | section 5 below |

The 3 reds, all from this run, all green on this machine and in the working tree:

| test | class | evidence | owner |
|---|---|---|---|
| `test_palette_synergy.py::test_the_two_ruled_grounds_measure_clean_today` | b, zip gap, fixed here; also a real untracked fixture | `E SystemExit: palette_synergy: background output/cloud_sky_ground.png does not exist`, `tools/palette_synergy.py:157` (`data/results/offload-gate-r0-0.json`) | pine runner fixed here; repo defect card `t_19b41ab7` (gamedev) |
| `test_scene_palette_set.py::test_build_reproduces_the_file_on_disk` | b, zip gap, fixed here; also a real untracked fixture | 3 of the 6 audit rows in `data/scene_palettes.json` name an untracked `output/bg_*_frame.png`, and `tools/scene_palette_set.py` `build()` drops any row whose background is not on disk, so the rebuild returns 3 rows against 6 shipped (`data/results/offload-gate-r2-0.json`) | same as above |
| `test_scene_palette_set.py::test_the_cast_check_catches_the_row_that_was_stale` | b, zip gap, fixed here; also a real untracked fixture | same dropped row: `AssertionError: []`, `assert 0 == 1` (`data/results/offload-gate-r2-0.json`) | same as above |

Why the palette rows went red only today: the audit rows were a constant in `tools/scene_palette_set.py`
until commit `91cd53b` (DECK-ROW-CAST, card `t_4f18c0ac`), which moved them into
`data/palettes/scene_*.json` and gave `build()` the `os.path.isfile` filter, so the shipped file and the
rebuild can now disagree about a file that is not in git (`git log -S` on
`tools/scene_palette_set.py`). The `cloud_sky_ground` row is new in commit `5f290c5` (SPRITE-GROUND-TRUTH,
card `t_1dc346b9`, `git log -S test_the_two_ruled_grounds_measure_clean_today`).

## 4. The zip gap fixed in `pine_offload.py`, and the proof

`output/` ships tracked files only, so three PNGs that are matched by `output/*` in `.gitignore`, never
committed (`git log --all -- output/cloud_sky_ground.png output/bg_battle_corridor_frame.png
output/bg_battle_deck_night_frame.png` is empty), and read by a tracked test were dropped whole. Change:
`OUTPUT_KEEP_PREFIXES` gains `output/bg_`, `OUTPUT_KEEP` gains `output/cloud_sky_ground.png`; backup
`pine_offload.py.bak-20261025-t_57ca9886`. No test was edited, no other lane's file was touched.

| attempt | zip | line printed | result |
|---|---|---|---|
| gate (before) | `zip bytes 14198743 files 82` | 3 reds, above | `data/results/offload-gate-r0-0.json`, `-r2-0.json` |
| gate-cloud (after) | `zip bytes 14253329 files 2 shards 1` | `36 passed in ...`, `SUMMARY passed=36 failed=0` | `data/results/offload-gate-cloud-0.json` |

The two files in the proof run are the two that carried all three reds. Cost of the fix: +54,586 zip bytes
against a 40,000,000 ceiling, for 11 `output/bg_*` files (29 KB) and one 176 byte crop.

## 5. Windows side, and what a clean checkout says

1. `python -m pytest tests/test_build_inputs.py tests/test_test_inputs.py tests/test_sync_art.py
   tests/test_mix_check_v3.py::test_the_script_still_runs_on_a_slice
   tests/test_project.py::test_generated_project_files_are_current
   tests/test_project.py::test_project_graph_matches_disk -q -p no:cacheprovider --tb=line`
   -> `31 passed in 9.95s`. These are the rows Pine refuses: the two git files, the theme-stream file, the
   render node and the two stream nodes (`pine_offload.py` `GIT_TESTS`, `ASSET_TESTS`, `RENDER_NODES`,
   `STREAM_NODES`). The 2026-10-24 page's one real red here, `test_test_inputs`, is green now because card
   `t_d2c52f15` committed the sixteen fixtures it named.
2. `python -m pytest tests -q -p no:cacheprovider --tb=no -rfE` -> `1529 passed, 463 warnings in 239.14s
   (0:03:59)`, exit 0, 0 errors. That is the whole suite on this machine, not only the Windows rows; peak
   memory was never the limit (11,143 MB free of 32,581 MB before the run, measured with
   `GlobalMemoryStatusEx`).
3. Clean checkout, which the working tree cannot measure: `git archive HEAD | tar -x -C <temp>`, then
   `python -m pytest tests/test_palette_synergy.py tests/test_scene_palette_set.py -q -p no:cacheprovider
   --tb=line` in that tree -> `3 failed, 33 passed in 7.19s`, the same three rows. So the 1529 green above
   is carried by untracked by-products, and HEAD `5f290c5` is not green in a fresh checkout. Card
   `t_19b41ab7` (gamedev) carries that, with the three paths and the negation precedent of `output/drive/`.

## 6. Not proven here, and the hotspot

- 51 skips and 3 deselected nodes are not passes. The skipped rows are measured on the Windows run in
  section 5; the 3 deselected nodes are `tests/test_project.py` x2 and `tests/test_mix_check_v3.py` x1, each
  named with its reason on stdout by `pine_offload.py` (`DESELECT_GROUPS`).
- The three fixed rows are green against `gate-cloud`'s 2 file zip, not against a full 82 file re-run. A full
  re-run after the `OUTPUT_KEEP_PREFIXES` change was not made: the change adds files to the zip and removes
  none, so it cannot turn another row red by omission, but that is an argument, not a measurement.
- The clean-checkout defect in card `t_19b41ab7` is proven for two test files, not for the whole suite in a
  fresh tree. Whether other untracked by-products carry other rows is unverified.
- hotspot: `output/` and `data/scene_palettes.json` at `<repo>`.
  Three lanes write `output/` by-products that tracked tests read, and today two of them decided a green suite;
  the tracked-files-only rule in `pine_offload.py` and the `.gitignore` in the project have to be decided
  together before more by-products become test inputs.
