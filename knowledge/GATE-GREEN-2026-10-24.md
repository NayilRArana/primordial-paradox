# GATE-GREEN 2026-10-24

Card t_1649d513 (testing). Whole primordial-paradox Python suite run on Pine Computers between 04:44 and 04:49 on 2026-10-24,
compared with `knowledge/GATE-GREEN-2026-10-23-2255.md` (the 22:45 run, card t_9a18f2e9) and
`knowledge/TEST-TRIAGE-PINE-2026-10-22.md`; every red classified, one fix card raised, one existing card commented.

P: 1325 passed, 2 failed, 28 skipped, 3 deselected, 0 error rows, 1358 collected rows across 76 offloaded test files
(`<workspace>\Shared\projects\arananet\pine\data\results\offload-gate28-0.json`, `-1.json`, `-2.json`).
P: graded pass rate 99.85% (1325 of 1327), against 99.70% (1325 of 1329) at 22:45, but the base moved: two nodes are
deselected on Pine since 23:01 (`<workspace>\Shared\projects\arananet\pine\pine_offload.py:123`), so the
Pine rate is not comparable row for row and the deselected two were graded on Windows in this report instead.
P: 0 windows-only rows and 0 zip gaps among the 2 reds; the 2 reds are the drive scene rows, already owned by card
t_c27552e3 (builder, todo), and the yyp cause rotated again to a new landing, card t_72d1b803 (FIX-YYP-8, builder).

Check named before work started: the `summary` and `results_txt` fields of the Pine result JSON files under
`<workspace>\Shared\projects\arananet\pine\data\results\`, with no SKIP and no deselected or errored row
counted as a pass, plus a Windows run of every file that carries a Pine red and of every file and node the Pine zip
cannot carry, in the real tree at `<repo>`.

No key was opened or printed. `PINE_SANDBOX_API_KEY` is read from the environment by `pine_client.py` only
(`<workspace>\Shared\projects\arananet\pine\pine_client.py`).

## The run

The card's `--name gate` was not used: it would overwrite `offload-gate-0/-1/-2.json` from 2026-10-22 18:56 and break the
trend below. The name used is `gate28` (gate27 was taken by the 23:01 project-graph probe, `offload-gate27-proj-0.json`).

Command: `<home>\AppData\Local\Python\bin\python.exe pine_offload.py --shards 3 --name gate28`, run from
`<workspace>\Shared\projects\arananet\pine`.
Zip 34,761,003 bytes, 76 test files, 3 shards, all three started at 04:44:09
(`<workspace>\Shared\projects\arananet\pine\pine_offload.py`).

All three shards completed on the first attempt, in 214.6 s, 112.7 s and 105.4 s. There was no repeat of the
`[Errno 10054]` upload refusal that cost gate25 and gate26 three attempts each
(`offload-gate26-1.json`, `offload-gate26b-0.json`, `offload-gate26c-0.json`); `run_shard` still has no retry around
`worker.put_file` (`<workspace>\Shared\projects\arananet\pine\pine_offload.py:227`), so the gap is untested
this round rather than fixed.

## The measured shards

| shard | files | passed | failed | skipped | deselected | pytest line | file |
|---|---|---|---|---|---|---|---|
| gate28-0 | 26 | 418 | 0 | 8 | 0 | `418 passed, 8 skipped, 9 warnings in 129.54s` | `offload-gate28-0.json` |
| gate28-1 | 25 | 537 | 2 | 11 | 0 | `2 failed, 537 passed, 11 skipped, 86 warnings in 29.64s` | `offload-gate28-1.json` |
| gate28-2 | 25 | 370 | 0 | 9 | 3 | `370 passed, 9 skipped, 3 deselected, 17 warnings in 39.81s` | `offload-gate28-2.json` |
| **total** | **76** | **1325** | **2** | **28** | **3** | | 1358 rows |

Row arithmetic: 1325 + 2 + 28 + 3 = 1358, the same row count every gate has collected since 10:35, so no test file entered
or left the offloaded set (`knowledge/GATE-GREEN-2026-10-23-2255.md`).
76 is the 79 `tests/test_*.py` on disk minus `GIT_TESTS` (`tests/test_build_inputs.py`, `tests/test_test_inputs.py`),
`ASSET_TESTS` (`tests/test_sync_art.py`) and the one `RENDER_NODES` file, all declared in
`<workspace>\Shared\projects\arananet\pine\pine_offload.py`.

## Why the Pine red count fell from 4 to 2

It is not a repair by a lane: it is a change in what Pine measures. `pine_offload.py` was rewritten at 23:01 under card
t_5b98704a and now holds `tests/test_project.py::test_project_graph_matches_disk` and
`::test_generated_project_files_are_current` in a new `STREAM_NODES` dict, deselected on the far side because
`check_project.check()` needs every Included File the yyp lists to exist under `game/datafiles` and the zip drops the
only source of 30 of the 52 streams (`<workspace>\Shared\projects\arananet\pine\pine_offload.py:123`).
Those two rows therefore left the Pine count (deselected 1 to 3, failed 4 to 2) and are graded on Windows in this report.
The third deselected node, `tests/test_mix_check_v3.py::test_the_script_still_runs_on_a_slice`, was deselected at gate26
too and passed on Windows in this round.

## The 28 SKIPs are not passes

28 is the same number as the 22:45 run, shard by shard: 8 on shard 0, 11 on shard 1, 9 on shard 2
(`offload-gate28-0.json`, `offload-gate28-1.json`, `offload-gate28-2.json`). The 7
`tests/test_first_fight_capture.py` rows are still skipped off Windows by the `windows_only` marker at
`tests/test_first_fight_capture.py:28`, and the rest are the standing markers in `pytest.ini:7` applied by
`tests/conftest.py:73`. None of them is counted as a pass anywhere in this report.

## Trend

| run | when | files | passed | failed | skipped | deselected | error rows | graded pass rate | file |
|---|---|---|---|---|---|---|---|---|---|
| full2 | 10-22 14:06 | 42 | 666 | 49 | 4 | 0 | 12 | 92.0% | `offload-full2-0/-1/-2.json` |
| triage | 10-22 15:30 | 42 | 725 | 24 | 0 | 0 | 0 | 96.8% | `offload-triage-0/-1/-2.json` |
| gate | 10-22 18:56 | 49 | 857 | 36 | 1 | 0 | 0 | 95.9% | `offload-gate-0/-1/-2.json` |
| gate23 | 10-23 04:29 | 72 | 1281 | 8 | 21 | 1 | 0 | 99.38% | `offload-gate23-0/-1/-2.json` |
| gate24 | 10-23 10:35 | 76 | 1325 | 11 | 21 | 1 | 0 | 99.18% | `offload-gate24-0/-1/-2.json` |
| gate25 | 10-23 16:39 | 76 | 1325 | 4 | 28 | 1 | 0 | 99.70% | `offload-gate25b-0.json`, `offload-gate25d-0.json`, `offload-gate25b-2.json` |
| gate26 | 10-23 22:45 | 76 | 1325 | 4 | 28 | 1 | 0 | 99.70% | `offload-gate26-0.json`, `offload-gate26d-0.json`, `offload-gate26d-1.json`, `offload-gate26-2.json` |
| gate28 | 10-24 04:44 | 76 | 1325 | 2 | 28 | 3 | 0 | 99.85% | `offload-gate28-0/-1/-2.json` |

The rows from full2 to gate26 are read from the earlier reports and their JSON files; the gate28 row was parsed from the
JSON `results_txt` fields in this run (`<workspace>\Shared\projects\arananet\pine\data\results\`).
Passed has not moved in four runs at 76 files. What moved is the denominator and the owner of the reds, not the tree
quality: the one thing the Pine number no longer sees is the yyp cause, which is red on Windows below.

## The 2 Pine red rows, classified

Classes: (a) windows only, (b) zip gap, (c) real regression. Counting: 0 (a), 0 (b), 2 (c).

| test | class | evidence | owner | card |
|---|---|---|---|---|
| `tests/test_slice_route.py::test_a_step_resolves_the_one_id_it_names[drive]` | c | fails on Pine (`offload-gate28-1.json`) and here at 04:51: `step drive: the scene 'drive_to_southampton' is not in data/scenes/all.json`, `tests/test_slice_route.py:498` | builder | t_c27552e3 (todo) |
| `tests/test_slice_route.py::test_a_scene_step_reaches_end_with_only_known_commands[drive]` | c | same missing scene, `tests/test_slice_route.py:528`, fails both places (`<repo>\tests\test_slice_route.py`) | builder | t_c27552e3 |

`grep -c drive_to_southampton data/scenes/all.json` returns 0 in
`<repo>\data\scenes\all.json`, the same measurement as at 22:42, so
nothing advanced on that card in six hours.

No card was raised for these two rows: t_c27552e3 already owns them, is in `todo`, and its parent t_a3fa132a is still
open, so a second card would split one fix across two lanes. The current measurement is on that card instead
(comment at 04:53).

## The Windows side of the gate, measured this round

Memory on this PC is scarce and the card caps the local work at 4 GB, so the Windows suite was run only where it had to
be run: every red file, every file the zip never carries, and every node deselected on the far side.

| files | result | what it shows |
|---|---|---|
| `tests/test_project.py` | `2 failed, 18 passed, 3 skipped in 2.16s` at 04:51 | the two yyp rows, card t_72d1b803 |
| `tests/test_project.py` + the two drive nodes | `4 failed, 28 passed, 3 skipped in 2.77s` at 04:51 | the two yyp rows plus the two drive rows, so all 4 Windows reds are named |
| `tests/test_build_inputs.py tests/test_test_inputs.py tests/test_sync_art.py tests/test_mix_check_v3.py::test_the_script_still_runs_on_a_slice` | `1 failed, 20 passed in 2.20s` at 04:52 | `test_the_committed_project_resolves_every_included_file` fails with 3 `MISSING FROM COMMIT` lines (`percy_theme_v2.ogg`, `pp_01_title_v6.ogg`, `pp_05_small_ship_v4.ogg`) and 4 `UNCOMMITTED SOURCE` lines (the same three plus `pp_arrival_v2/pp_arrival_v2.ogg`, new since 04:14), which is the blocked card t_c31f9295. The other three files and the deselected mix-check node are green (`<repo>\tools\check_build_inputs.py`) |
| `tests/test_capture_title.py tests/test_first_fight_capture.py` | `12 passed in 3.68s` at 04:53 | the game window rows, which Pine skips by marker, pass on this desktop |

That `test_build_inputs.py` row is in no Pine count by design: the file is in `GIT_TESTS` and never travels
(`<workspace>\Shared\projects\arananet\pine\pine_offload.py`).

## The new fix card

t_72d1b803 (builder, FIX-YYP-8). Two streams landed and `tools/gen_project.py` was not run: `pp_03_harbor_v3.ogg`
(1,494,098 bytes) with commit 3dbf5f8 at 10-24 00:21, and `pp_arrival_v2.ogg` (1,458,131 bytes) at 04:14, which is still
untracked. `python tools/check_project.py` at 04:50 in the real tree prints 2 problems, both Included Files missing from
`game/PrimordialParadox.yyp`, and `python tools/gen_project.py --check` prints `STALE: game/PrimordialParadox.yyp` and
`33 resources: 25 scripts, 4 objects, 4 rooms, 252 included files`
(`<repo>\tools\check_project.py`,
`<repo>\tools\gen_project.py`). The committed yyp lists
`pp_03_harbor.ogg` at `game/PrimordialParadox.yyp:2025` and `pp_03_harbor_v2.ogg` at `:2034` and neither new stream
(`git show HEAD:./game/PrimordialParadox.yyp`). The card names the two commands, says run the generator and commit the
yyp alone, edit no test, deselect nothing, and holds the chain of command line: gamedev's specs are not overridden.

## The zip, re-measured

34,761,003 bytes against the 40,000,000 ceiling in the `pine_offload.py` docstring: 5,238,997 bytes of headroom, against
5,400,729 at 22:45, so the tree grew 161,732 bytes in six hours under a fixed ceiling for reasons that are not a change
in this card (`<workspace>\Shared\projects\arananet\pine\pine_offload.py`).
The standing zip gap is now handled by deselection rather than repair: 30 of the 52 streams have their only source under
`assets/audio/<name>/`, which the zip drops, so `test_project_graph_matches_disk` and
`test_generated_project_files_are_current` are measured only on Windows from 23:01 onward
(`knowledge/TEST-TRIAGE-PINE-2026-10-22.md`).

## What is still unproven

- Whether the `[Errno 10054]` upload refusal returns on a later 34.8 MB gate: unverified. It did not appear once in this
  run, and `worker.put_file` still has no retry (`<workspace>\Shared\projects\arananet\pine\pine_offload.py:227`).
- Shard 0 was measured at 04:44 to 04:48 while shards 1 and 2 finished at 04:46 to 04:47, and other lanes were writing
  the tree during that window (`pp_arrival_v2.ogg` landed at 04:14, `game/datafiles/streams` mtime 04:14), so a file
  edited between 04:44 and 04:48 is measured in one shard and not another: unverified whether any such edit landed.
- Whether the deselection of the two yyp rows is the right call for a gate whose job is to catch a stale yyp: unverified
  as a policy. What is measured is that the Pine gate can no longer see that cause, and the Windows suite can, which is
  why this report grades those two rows here and why t_72d1b803 exists.
- Whether `pp_arrival_v2.ogg` should be listed in the yyp before its source is committed: unverified, and that is the one
  open question on t_72d1b803 and on t_c31f9295.

## Hotspot

hotspot: `game/PrimordialParadox.yyp` and `game/datafiles/streams/`. Fifth occurrence in two days of the same cause: an
audio lane lands a stream, `tools/sync_art.py` mirrors it, nobody runs `tools/gen_project.py` (commit times from
`git show -s --format='%ci %h'`: cb671e1 10-23 10:52, a16eb41 16:52, ab475d2 20:24, 3dbf5f8 10-24 00:21, plus the 04:14
arrival landing). Five fix cards is five times the same repair. The durable fix is to run the generator inside the audio
landing path, or as the first step of this gate, and it is not a test change
(`<repo>\tools\gen_project.py`).

hotspot: `pine_offload.py` and the gate's comparability. Two runner changes in two days (audio prefix lift, then the
STREAM_NODES deselection at 23:01) each moved the Pine denominator, so the graded rate is only comparable within a
runner version (`<workspace>\Shared\projects\arananet\pine\pine_offload.py`).
