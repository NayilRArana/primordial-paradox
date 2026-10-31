# GATE-GREEN 2026-10-26 second feed (run 2, delta)

Card `t_aa2a36e0` (AUTO-GATE-GREEN, testing lane). This is the second feed of 2026-10-26, so it runs in
delta mode: the baseline is the previous run's own JSON artifacts, copied aside before this run overwrote
them, and only rows that changed since them are reported below.

Check named before the run started: the `SUMMARY passed=N failed=M` line and every `FAILED` row inside
`results_txt` of `data/results/offload-gate-0.json`, `-1.json`, `-2.json`, diffed field by field against
the same three files written 06:13 by card `t_41766656`; then this machine's own pytest line for the nodes
Pine does not carry (`<workspace>\Shared\projects\arananet\pine\OFFLOAD.md`).

No key was opened or printed; `PINE_SANDBOX_API_KEY` is read from the environment by `pine_client.py`
only. ART-BIBLE RULE 0 was not needed: nothing here judges art.

## 1. Why a second pass, and the baseline

- Baseline: `offload-gate-{0,1,2}.json` written 06:13 on 2026-10-26 at HEAD `ae3a6cb`, 1553 passed /
  1 failed / 52 skipped / 3 deselected / 0 errors, one red row,
  `tests/test_scene_palettes.py::test_the_check_reports_its_numbers_so_a_reviewer_can_read_them`,
  classified windows only in the inverted direction and sent to gamedev as card `t_8bb7bdea`
  (`<repo>\knowledge\GATE-GREEN-2026-10-26.md`).
- HEAD now `8220c95`, whose message is "PALETTE-REPORT-POSIX: the committed palette report prints its
  palette path the same on Windows and on Linux (card t_8bb7bdea)". It touches
  `output/scene_palettes.json`, `tests/test_scene_palettes.py`, `tests/test_nes_composite_check.py`,
  `tools/nes_composite_check.py` (6 files, 113 insertions), so the one red had a fix waiting to be
  measured. Card `t_8bb7bdea` is `done` on the board.
- Test files 92 -> 93; the new one is `tests/test_event_log.py` (7 tests plus 1 skip), nothing was
  removed (`git ls-files` check against the baseline file list).

## 2. Launch

- `<home>/AppData/Local/Python/bin/python.exe pine_offload.py --shards 3 --name gate` in
  `<workspace>\Shared\projects\arananet\pine`, background session `proc_e7ccbad15fc6`,
  pid 8316. One blocking wait on that session, no polling loop.
- Tool line: `zip bytes 15005390 files 90 shards 3`, `output/: shipping 34 tracked file(s), skipping
  1709 by-product(s)`. Every shard reports `upload_attempts: 1`, so the PINE-UPLOAD-DROP retry path did
  not fire.
- Wall time per shard: gate-0 166.4 s, gate-1 111.5 s, gate-2 153.1 s; all three `status: completed`.

## 3. Merged count on Pine

| shard | passed | failed | skipped | deselected | errors | file |
|---|---|---|---|---|---|---|
| gate-0 | 492 | 0 | 16 | 0 | 0 | `data/results/offload-gate-0.json` |
| gate-1 | 519 | 0 | 11 | 3 | 0 | `data/results/offload-gate-1.json` |
| gate-2 | 550 | 0 | 26 | 0 | 0 | `data/results/offload-gate-2.json` |
| total | 1561 | 0 | 53 | 3 | 0 | |

Pine is clean: 1561 passed, 0 failed, 0 errors. The 53 skips are the suite's own `skipif` rows, and the
3 deselects are the node-level exclusions the runner prints (`test_mix_check_v3` slice,
two `test_project` nodes); neither is counted as a pass anywhere above.

## 4. Rows that changed since 06:12

| row | 06:12 | 07:02 | what changed |
|---|---|---|---|
| `tests/test_scene_palettes.py::test_the_check_reports_its_numbers_so_a_reviewer_can_read_them` | FAILED | passed | `8220c95` prints the palette path POSIX on both sides; the committed report and the checker now agree |
| `tests/test_event_log.py` (7 tests) | absent | 7 passed, 1 skip | new file, first appearance in the gate |
| all other rows | passed | passed | no change |

Arithmetic: 1553 passed + 1 (the cleared red) + 7 (new file) = 1561; 52 skipped + 1 (new file) = 53;
1 failed -> 0 failed. Nothing else moved, and no row that passed at 06:12 is red on Pine now.

## 5. Windows only nodes, run locally

Ran at 07:04 on this machine, the nodes Pine cannot carry: `tests/test_build_inputs.py`,
`tests/test_test_inputs.py`, `tests/test_sync_art.py`,
`tests/test_mix_check_v3.py::test_the_script_still_runs_on_a_slice`, and the two `test_project.py` nodes
the runner deselects. The previously red palette node was added to the same call as a direct check.

`2 failed, 31 passed in 7.73s`

- `tests/test_build_inputs.py::test_the_committed_project_resolves_every_included_file` FAILED
- `tests/test_build_inputs.py::test_the_flag_absent_leaves_the_worktree_directions_alone` FAILED
  (`tests/test_build_inputs.py:212: AssertionError: the flagless check still measures the real tree`)
- `tests/test_scene_palettes.py::test_the_check_reports_its_numbers_so_a_reviewer_can_read_them` passed,
  which is the same node that was red at 06:12: `8220c95` closes it on both sides.

Captured output names the cause exactly:

```
MISSING FROM COMMIT datafiles/streams/percy_theme_v3.ogg
MISSING FROM COMMIT datafiles/streams/percy_theme_v4.ogg
UNCOMMITTED SOURCE projects/primordial-paradox/assets/audio/percy_theme_v3/percy_theme_v3.ogg
UNCOMMITTED SOURCE projects/primordial-paradox/assets/audio/percy_theme_v4/percy_theme_v4.ogg
```

Class: real, not windows only and not a zip gap. `test_build_inputs.py` is one of the files the runner
does not offload at all (it needs git history), so Pine never sees it; the failure is a fact about this
tree, not about the OS.

What produced it: the working tree carries an uncommitted edit to `game/PrimordialParadox.yyp` (mtime
07:05, `git status` shows it modified) that names `percy_theme_v3.ogg` and `percy_theme_v4.ogg`;
`git show HEAD:./game/PrimordialParadox.yyp` names neither, only `percy_theme_v2.ogg`. The two stream
files do not exist under `datafiles/streams/`, and the sources under
`assets/audio/percy_theme_v3/` and `assets/audio/percy_theme_v4/` are untracked (`?? include` in
`git status`). The cue work is the musician lane's card `t_7f331a39` (AUTO-MUSIC-NEXT, done, its
`NOTES.md` is headed "PP-06 Percy, Tyrant of the Harbor v4"); the yyp entry and the stream files are the
gamedev lane's to land.

No commit is at fault, so there is no commit to name: the red is a working-tree edit that got ahead of
the files it names. Fix card `t_28a81f2c` is raised for gamedev, following the FIX-YYP precedent of
`c927c2b` and `d12b9c7`: either land `datafiles/streams/percy_theme_v3.ogg` and `_v4.ogg` and the yyp
entry in one commit, or drop the two yyp entries until the streams exist. The testing lane does not
edit another lane's code, so nothing in `game/` was touched by this run.

## 6. Trend

| run | HEAD | Pine passed | Pine failed | local Windows-only |
|---|---|---|---|---|
| 2026-10-25 18:31 | `0b5dd01` | 1533 | 5 | n/a |
| 2026-10-26 06:12 | `ae3a6cb` | 1553 | 1 | 53 passed |
| 2026-10-26 07:02 | `8220c95` | 1561 | 0 | 31 passed, 2 failed |

Pine is green for the first time in the three runs on record, and the growth is the suite itself (7 new
tests), not a lower bar. The only red left in the whole gate is the uncommitted yyp entry pair above,
which a single commit closes. No SKIP row and no errored row is counted as a pass in any number here.

## 7. Files this run wrote or read

- Wrote: this note, `knowledge/GATE-GREEN-2026-10-26-R2.md`.
- Baseline copies kept for the next feed:
  `<agent-runtime>\kanban\boards\nayil-ops\workspaces\t_aa2a36e0\baseline\offload-gate-{0,1,2}.json`.
- Read: `data/results/offload-gate-{0,1,2}.json` (this run), `game/PrimordialParadox.yyp` (HEAD copy and
  working copy), `assets/audio/percy_theme_v3|v4/NOTES.md`, `tests/test_build_inputs.py` output.
