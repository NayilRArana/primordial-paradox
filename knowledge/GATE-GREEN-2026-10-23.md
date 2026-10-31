# GATE-GREEN 2026-10-23

Card t_1ed727b8 (testing). Whole primordial-paradox Python suite run on Pine Computers at 04:29,
compared with `knowledge/GATE-GREEN-2026-10-22.md` and `knowledge/TEST-TRIAGE-PINE-2026-10-22.md`;
every new red classified and a fix card raised for each real regression that no live card owns.

P: 1281 passed, 8 failed, 21 skipped, 1 deselected; every red fails on Windows too, so all 8 are real.
P: 21 skips are the TEST-CLASSIFY-33 markers, and no skip is counted as a pass here.
P: 2 new fix cards (musician cue debt, builder yyp) plus 1 for the credits data; the four slice rows are t_ff5a3714's.
P: one row, `test_project_graph_matches_disk`, is part zip gap and cannot be closed by INCLUDE: measured 33.9 MB of audio sources against 12.5 MB of headroom.

Check named before work started: the three `SUMMARY` lines in
`<workspace>\Shared\projects\arananet\pine\data\results\offload-gate23-0.json`, `-1.json`,
`-2.json` (no SKIP and no errored row counted as a pass), plus a Windows run of every file that
carries a Pine red, in the real tree at `<repo>`.

No key was opened or printed. `PINE_SANDBOX_API_KEY` was read by `pine_client.py` from the
environment only.

## The run

Command: `<home>\AppData\Local\Python\bin\python.exe pine_offload.py --shards 3 --name gate23`
from `<workspace>\Shared\projects\arananet\pine`, zip 27,513,810 bytes, 72 test files,
3 shards, started 04:29, last shard done 04:33. The 75 `test_*.py` files on disk are 72 offloaded plus
the three the runner keeps on the Windows suite (`tests/test_build_inputs.py`, `tests/test_test_inputs.py`
as `GIT_TESTS`, `tests/test_sync_art.py` as `ASSET_TESTS`), and one node deselected on the far side
(`tests/test_mix_check_v3.py::test_the_script_still_runs_on_a_slice`, the 16.7 MB render).

| shard | passed | failed | skipped | deselected | file |
|---|---|---|---|---|---|
| gate23-0 | 409 | 5 | 9 | 0 | `offload-gate23-0.json` |
| gate23-1 | 436 | 2 | 11 | 1 | `offload-gate23-1.json` |
| gate23-2 | 436 | 1 | 1 | 0 | `offload-gate23-2.json` |
| **total** | **1281** | **8** | **21** | **1** | 1311 rows |

Pass rate of the graded rows (passed against passed plus failed) is 99.38%; across every collected row
including the skips it is 97.71%. All counts come from the `results_txt` field of the three JSON files
above, which hold the pytest summary lines `5 failed, 409 passed, 9 skipped`, `2 failed, 436 passed,
11 skipped, 1 deselected`, `1 failed, 436 passed, 1 skipped`.

## The 21 SKIPs are not passes

They are all added by the `pytest_collection_modifyitems` hook at `tests/conftest.py:73` (card
TEST-CLASSIFY-33), and `python -m pytest --collect-only -q -m "windows_only or host_png_bytes or
needs_git_checkout" tests/` collects 37 marked items, of which 16 sit in the two `GIT_TESTS` files
that are never offloaded. 37 - 16 = 21, which is exactly the skip count in the run:

| marker | rows on Pine | tests |
|---|---|---|
| `windows_only` | 14 | `capture_title.py` x5 (module `pytestmark`, `tests/test_capture_title.py:29`), `play_demo.py` x9 (`tests/test_play_demo.py:62` and following) |
| `host_png_bytes` | 4 | `test_intro.py::test_the_star_generator_rewrites_the_committed_sprite`, `test_make_env_ship.py::test_the_committed_outputs_are_what_the_script_writes_today`, `test_make_title_ui.py::test_the_committed_sprites_match_a_fresh_run`, `test_title_art_v2.py::test_the_two_busts_regenerate_from_the_committed_tree` (`tests/test_title_art_v2.py:186`) |
| `needs_git_checkout` | 3 | `test_project.py` lines 125, 167, 197, including `test_build_inputs_are_committed` |

What this means for the trend: the 15 Windows-only reds of the 18:56 run did not go green, they
stopped being measured, and the honest reading of 99.38% is "99.38% of the rows that were graded".
Two of the four `host_png_bytes` rows (`test_make_title_ui`, `test_title_art_v2`) and both
`test_intro`/`test_make_env_ship` rows were red on Pine at 18:56 and are skips now, so the red count
fell by 21 rows in part because of that hook, not only because of fixes.

## Trend

| run | when | files | passed | failed | skipped | error rows | pass rate | files |
|---|---|---|---|---|---|---|---|---|
| full2 | 10-22 14:06 | 42 | 666 | 49 | 4 | 12 | 92.0% | `offload-full2-0/-1/-2.json` |
| triage | 10-22 15:30 | 42 | 725 | 24 | 0 | 0 | 96.8% | `offload-triage-0/-1/-2.json` |
| gate | 10-22 18:56 | 49 | 857 | 36 | 1 | 0 | 95.9% | `offload-gate-0/-1/-2.json` |
| gate23 | 10-23 04:29 | 72 | 1281 | 8 | 21 | 0 | 99.4% graded | `offload-gate23-0/-1/-2.json` |

Red rows fell 36 to 8 while the suite grew 49 to 72 files and 894 to 1311 rows. Of the 28 red rows
that left, 21 are the skip classes above and 7 are fixed: the title art and palette cluster that owned
16 of the 19 real regressions at 18:56 is not red on Pine any more, with one caveat, two of its rows
(`test_make_title_ui::test_the_committed_sprites_match_a_fresh_run` and
`test_title_art_v2::test_the_two_busts_regenerate_from_the_committed_tree`) left the red list by
becoming `host_png_bytes` skips rather than by going green, and the yyp rows t_e8f3ce1b fixed at 498d81f
stayed fixed until the v3 stream landed at 04:02 (which is the red t_d5655cf1 now carries).

## The 8 red rows, classified

Classes: (a) windows only, (b) zip gap, (c) real regression. Local evidence is the Windows run of the
same four files at 04:55 to 05:05, which returned `5 failed, 32 passed` (`test_slice_route.py`,
`test_no_network_in_build.py`) and `4 failed, 43 passed` (`test_audio.py`, `test_project.py`).

| test | class | evidence | owner | card |
|---|---|---|---|---|
| `test_audio.py::test_unreferenced_cue_rows_are_the_recorded_debt_list` | c | fails here too: `['PP-01', 'PP...'] == ['PP-01', 'PP...']`, at index 2 `PP-08` where the recorded list has `PP-03`, and `PP-16` is on the recorded side only; `data/audio.json` is modified in the working tree (32 insertions, 18 deletions, mtime 22:36) and `tests/test_audio.py` is clean, so the cue registry moved and the debt list did not | musician | t_6b4724a9 |
| `test_slice_route.py::test_a_step_resolves_the_one_id_it_names[drive]` | c | fails here too: `step drive: the scene 'drive_to_southampton' is not in data/scenes/all.json, so its commands cannot be read` (`tests/test_slice_route.py:528`) | gamedev | live card t_ff5a3714, comment posted |
| `test_slice_route.py::test_a_step_resolves_the_one_id_it_names[save]` | c | fails here too: `step save: the row names no trigger` (`tests/test_slice_route.py:607`) | gamedev | live card t_ff5a3714, comment posted |
| `test_slice_route.py::test_a_scene_step_reaches_end_with_only_known_commands[drive]` | c | fails here too, same missing `drive_to_southampton` scene | gamedev | live card t_ff5a3714, comment posted |
| `test_slice_route.py::test_the_save_step_names_a_trigger_that_exists_on_its_map` | c | fails here too, same unset trigger on the save row | gamedev | live card t_ff5a3714, comment posted |
| `test_project.py::test_project_graph_matches_disk` | c and b | local `python tools/check_project.py` prints `1 project problem(s)`, `FAIL PrimordialParadox.yyp: game/datafiles/streams/pp_05_small_ship_v3.ogg is not listed as an Included File` (the v3 stream landed 04:02); on Pine the same checker reports 24 problems, first extra `lists Included File streams/percy_theme.ogg which is not in game/datafiles`, which is the zip gap below | builder | t_d5655cf1 |
| `test_project.py::test_generated_project_files_are_current` | c | fails here too: `STALE: game/PrimordialParadox.yyp`, `33 resources: 25 scripts, 4 objects, 4 rooms, 242 included files`, `gen_project.main` returns 1 (`tests/test_project.py:67`) | builder | t_d5655cf1 |
| `test_no_network_in_build.py::test_the_build_holds_no_endpoint_no_key_and_no_live_call` | c | fails here too: `10 finding(s)`, being 5 lines in `data/credits.json` and the same 5 in `game/datafiles/credits.json` (`REFUSED .../credits.json:29 URL in a data file that declares no citation and no third party provenance (https://github.com/google/fonts/blob/main/ofl/pressstart2p/OFL.txt)`, `:30 http://scripts.sil.org/OFL`, `:39`, `:42`, `:43 https://www.openstreetmap.org/copyright`); the test file is new, added in 43995a0 at 2026-10-22 23:00 by card t_41c97c88, so this is a new pin on data that was already committed in 6e4d55f | gamedev | t_d71e0dda |

Count: 8 (c), 0 (a), 0 (b) standing alone, 0 error rows. One row (`test_project_graph_matches_disk`)
carries both a real row and a Pine-only set the zip cannot close.

## The zip gap I measured and did not fix

`test_project_graph_matches_disk` compares every `Included File` in the yyp with `game/datafiles`. On
Pine, `tests/conftest.py` rebuilds `game/datafiles/streams` from `assets/audio/<name>/*.ogg`
(`tools/sync_art.py` `mirror_streams()`), and the zip excludes `game/datafiles/streams/` as
`GENERATED_MIRRORS` while `SKIP_EXT` drops every `.ogg` outside `AUDIO_PREFIXES`
(`<workspace>\Shared\projects\arananet\pine\pine_offload.py:29` to `:112`). Measured on
this host at 05:10: 47 streams exist in `game/datafiles/streams`, and 25 of them have no source the
zip carries. Those 25 sources are 33,934,704 bytes; the zip built this run is 27,513,810 bytes, so
carrying them makes it 61.4 MB, over the 40,000,000 ceiling that has failed the upload twice (the
ceiling and its history are in the `pine_offload.py` docstring). So `INCLUDE` and `AUDIO_PREFIXES`
are unchanged by this card, and that node will stay red on Pine for the mirror reason until the
ceiling moves or the node is deselected. Deselecting it was rejected here: the same node also carries
the real stale-yyp row above, and a deselect would hide it from the Pine side.

## Also red on the Windows suite, not on Pine

`tests/test_project.py::test_build_inputs_are_committed` is skipped on Pine by `needs_git_checkout`
and red here: 13 items, first `MISSING FROM COMMIT datafiles/ear_loop_state.json`. Live cards own it:
t_c31f9295 (audit, blocked) covers the untracked audio sources in three directories, so no new card.
The other 16 local-only rows (`tests/test_build_inputs.py` x7 and `tests/test_test_inputs.py` x9) were
not run locally this round; their state is unverified.

## The three new fix cards

1. t_6b4724a9 (musician): `data/audio.json` references changed and `RECORDED_UNREFERENCED` in
   `tests/test_audio.py:270` was not updated. Evidence and the two list diffs in the card.
2. t_d5655cf1 (builder): the yyp must be regenerated after `game/datafiles/streams/pp_05_small_ship_v3.ogg`
   landed at 04:02, the same mechanical job t_e8f3ce1b did at 498d81f. The card names the exact
   commands and the two rows it closes.
3. t_d71e0dda (gamedev): `data/credits.json` and its mirror carry 5 URLs with no provenance block,
   and the new test from t_41c97c88 refuses them. The card leaves the fix shape to gamedev, who owns
   the credits data and the spec, and says so explicitly.

No test was weakened, no test file was edited, and no other lane's code was touched.

## What is still unproven

- The Pine-only extra items in `test_project_graph_matches_disk` are reported as 24 problems with only
  the first named, because the shard output is `tail -80`. That the other 23 are the 25 no-source
  streams is my inference from the measurement above, not read off the shard. The check that settles it
  is `--shards 1 --name gate23proj --files tests/test_project.py` with the far side logging
  `check_project.py` in full.
- `tests/test_build_inputs.py` and `tests/test_test_inputs.py` local state this round.

## Hotspot

hotspot: `data/audio.json`, `data/credits.json` and `game/PrimordialParadox.yyp`, because three lanes
wrote them after the 18:56 gate and each one is pinned by a checker that only runs in the full suite,
so a lane that edits one sees green locally and red only at the gate.
