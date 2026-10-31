# TEST-TRIAGE-PINE 2026-10-22

Card t_cb1f931b (testing). Sorts the 49 Pine test failures from the 3 computer run of 2026-10-22 14:06
(`<workspace>\Shared\projects\arananet\pine\data\results\offload-full2-0.json`,
`-1.json`, `-2.json`, field `results_txt`) into windows only, zip gap and real regression, fixes the
gaps in `<workspace>\Shared\projects\arananet\pine\pine_offload.py`, and reruns the suite
with `--shards 3 --name triage`.

Check that was named before work started: the same 20 test files that carry the 49 failures, run on
this Windows machine with `python -m pytest <files> -q --tb=short`, plus the rerun summary in
`<workspace>\Shared\projects\arananet\pine\data\results\offload-triage-*.json`.

No key was opened or printed. `PINE_SANDBOX_API_KEY` is read by `pine_client.py` from the environment
only; the runs below never print it, and no file under `pine/` holding a credential was opened.

## Method

1. Local run of every failing file on Windows, 2026-10-22 15:10, real tree
   (`<repo>`): 7 failed, 334 passed.
   Local failure is the only evidence of class (c); a test that passes locally is class (a) or (b).
2. Built the exact Pine zip with `pine_offload.build_zip()`, extracted it, and ran the same files
   inside the extracted tree to separate a missing file from a platform difference.
3. Fixed `INCLUDE`, the audio prefixes and the shard instructions, then reran the full suite on Pine.

Rule used for every row: a test that fails here and on Pine is (c) real regression; a test that
passes here and failed on Pine is (b) zip gap when a named file or the shard layout explains it, and
(a) windows only when the failure is a Windows toolchain or window dependency. No SKIP and no errored
row is counted as a pass.

## The 49 failing tests

Classes: (a) windows only, (b) zip gap fixed in `pine_offload.py`, (c) real regression, card raised.
Source shorthand: `2-0`, `2-1`, `2-2` are the three
`<workspace>\Shared\projects\arananet\pine\data\results\offload-full2-*.json` files.

| test | class | evidence | owner | fix card |
|---|---|---|---|---|
| test_audio.py::test_cue_table_is_exactly_the_seventeen_ids_the_musician_wrote | b | Pine read the round 1 note and the sfx wavs from a tree that had neither; the note lives outside the repo and the wavs were dropped by SKIP_EXT (2-0) | pine runner | fixed here: EXTRA + AUDIO_PREFIXES |
| test_audio.py::test_no_cue_id_was_invented_against_the_musicians_note | b | same missing `notes/notebook-2026-10-19/round1/musician.md` and `assets/audio/sfx/*.wav` (2-0) | pine runner | fixed here: EXTRA + AUDIO_PREFIXES |
| test_audio.py::test_the_three_cues_the_card_left_out_are_rows_with_the_musicians_own_assets | b | same missing note and wav sources (2-0) | pine runner | fixed here: EXTRA + AUDIO_PREFIXES |
| test_capture_title.py::test_a_game_window_copy_passes_the_nes_check | a | needs the real game window; Pine raises AttributeError, no ctypes window API on Linux (2-0) | gamedev | none, stays on the Windows suite |
| test_capture_title.py::test_a_terminal_copy_is_refused | a | same window dependency, AttributeError on Linux (2-0) | gamedev | none, stays on the Windows suite |
| test_capture_title.py::test_the_frame_is_not_saved_when_the_copy_is_not_the_game | a | same window dependency (2-0) | gamedev | none, stays on the Windows suite |
| test_capture_title.py::test_the_frame_is_saved_when_the_copy_is_the_game | a | same window dependency (2-0) | gamedev | none, stays on the Windows suite |
| test_capture_title.py::test_the_threshold_sits_between_the_two_measurements | a | same window dependency (2-0) | gamedev | none, stays on the Windows suite |
| test_intro.py::test_the_star_generator_rewrites_the_committed_sprite | a | passes here, the committed PNG bytes come from the Windows Pillow and zlib build; same byte check still red on Pine in the rerun (2-0, offload-triage-2.json) | gamedev | none, stays on the Windows suite |
| test_sync_art.py::test_art_mirror_is_current | b | Pine mirror had no `game/datafiles/streams/alarm.ogg`, so the mirror was empty (2-0) | pine runner | fixed here: AUDIO_PREFIXES + game/datafiles/sfx/ |
| test_sync_art.py::test_main_mirrors_the_title_theme_stream | b | same missing `game/datafiles/streams/title_theme.ogg` (2-0) | pine runner | fixed here: AUDIO_PREFIXES |
| test_sync_art.py::test_the_project_lists_the_title_theme_stream | b | the yyp listing is read with the mirror in place; the mirror was empty for the same reason (2-0) | pine runner | fixed here: AUDIO_PREFIXES |
| test_check_data.py::test_real_data_passes | b | Pine: `data/schemas: jsonschema is not installed`, so check_data cannot enforce the schemas (2-1) | pine runner | fixed here: GOAL verifies `import jsonschema` |
| test_make_env_ship.py::test_the_committed_outputs_are_what_the_script_writes_today | a | passes here; on Pine `game/sprites_src/env/ts_ship.png` sha256 differs from a fresh build (offload-triage-0.json) | gamedev | none, stays on the Windows suite |
| test_osm_to_map.py::test_cached_place_never_re_queries_overpass | b | Pine ran the tree from `~/repo` instead of `~/shared/projects/primordial-paradox`, so `data/osm_cache` resolved where the test does not look (2-1, traceback path) | pine runner | fixed here: GOAL pins the working directory |
| test_render_chip_v2.py::test_the_old_four_voice_title_theme_still_renders_identically | b | Pine: `assets/audio/title_theme/title_theme.wav` is not a file; 6.0 MB, dropped by the 3 MB cap (2-1) | pine runner | fixed here: AUDIO_PREFIXES |
| test_schemas.py::test_real_data_matches_every_schema | b | Pine: `jsonschema is not installed` (2-1) | pine runner | fixed here: GOAL verifies `import jsonschema` |
| test_schemas.py::test_check_data_reports_unknown_enemy_field | b | Pine: `jsonschema is not installed` (2-1) | pine runner | fixed here: GOAL verifies `import jsonschema` |
| test_schemas.py::test_check_data_reports_a_wait_command_without_its_number | b | Pine: `jsonschema is not installed` (2-1) | pine runner | fixed here: GOAL verifies `import jsonschema` |
| test_schemas.py::test_check_data_reports_an_enemy_hp_below_one | b | Pine: `jsonschema is not installed` (2-1) | pine runner | fixed here: GOAL verifies `import jsonschema` |
| test_test_inputs.py::test_no_test_skips_on_a_missing_input_and_every_fixture_is_committed | c | fails here too: `tests/test_palette_synergy.py:132: a pytest.skip is guarded by a path existence test` (local run 15:10) | testing | t_6fe82061 |
| test_build_inputs.py::test_the_committed_project_resolves_every_included_file | c | fails here too: `UNCOMMITTED SOURCE .../pp_03_harbor.ogg` and two more, check_build_inputs exits 1 (local run 15:10) | musician | t_b1e1a770 |
| test_build_inputs.py::test_an_included_file_with_no_committed_source_is_named | b | passes here; Pine cannot answer a git question in a zipped tree (2-2) | pine runner | fixed here: GIT_TESTS skips the file offload |
| test_build_inputs.py::test_a_committed_source_satisfies_its_included_file | b | same, no git repository on the shard (2-2) | pine runner | fixed here: GIT_TESTS |
| test_build_inputs.py::test_a_data_json_resolves_through_the_sync_data_mirror | b | same, no git repository on the shard (2-2) | pine runner | fixed here: GIT_TESTS |
| test_build_inputs.py::test_generated_indexes_are_not_treated_as_missing_sources | b | same, no git repository on the shard (2-2) | pine runner | fixed here: GIT_TESTS |
| test_build_inputs.py::test_an_uncommitted_mirror_source_is_named | b | same, no git repository on the shard (2-2) | pine runner | fixed here: GIT_TESTS |
| test_cleanroom.py::test_the_gate_passes_on_this_repository | c | fails here too: `game/datafiles/maps/real_places.json:1099: foreign name 'Queen'` (local run 15:10) | gamedev | t_d0f24d14 |
| test_first_fight.py::test_decision_two_and_dm05_carry_the_same_band | b | passes here and in the rerun; the 14:06 shard ran at `~/repo` with none of the audio or sibling shared files, and its fixture errors came from the same tree (2-2) | pine runner | fixed here: GOAL pins the working directory |
| test_first_fight.py::test_the_talk_fight_length_is_the_same_two_numbers | b | passes here and in the rerun for the same tree reason (2-2) | pine runner | fixed here: GOAL pins the working directory |
| test_first_fight.py::test_the_fallback_line_is_in_its_own_pool_and_moves_no_mercy | b | passes here and in the rerun for the same tree reason (2-2) | pine runner | fixed here: GOAL pins the working directory |
| test_integration_build.py::test_the_gate_config_declares_three_as_unmeasured | b | the gate config lives outside the repo at `projects/arananet/manager/guard/suite_config.json` and no shard carried it (2-2) | pine runner | fixed here: EXTRA |
| test_look.py::test_real_data_passes | b | Pine: `jsonschema is not installed`, reached through check_data (2-2) | pine runner | fixed here: GOAL verifies `import jsonschema` |
| test_look.py::test_sixteen_colours_in_a_room_palette_still_passes | b | same missing jsonschema through check_data (2-2) | pine runner | fixed here: GOAL verifies `import jsonschema` |
| test_look.py::test_appending_a_new_master_colour_passes | b | same missing jsonschema through check_data (2-2) | pine runner | fixed here: GOAL verifies `import jsonschema` |
| test_look.py::test_a_seventeenth_colour_is_refused_and_reverting_clears_it | b | same missing jsonschema through check_data (2-2) | pine runner | fixed here: GOAL verifies `import jsonschema` |
| test_make_title_ui.py::test_the_committed_sprites_match_a_fresh_run | a | passes here; on Pine `spr_pp_font8` sha256 differs from what the script writes (offload-triage-1.json) | gamedev | none, stays on the Windows suite |
| test_project.py::test_project_graph_matches_disk | c | fails here too: `PrimordialParadox.yyp: game/datafiles/maps/real_places.json is not listed as an Included File` (local run 15:10) | gamedev | t_d0f24d14 |
| test_project.py::test_generated_project_files_are_current | c | fails here too: `STALE: game/PrimordialParadox.yyp` (local run 15:10) | gamedev | t_d0f24d14 |
| test_project.py::test_cleanroom_passes | c | fails here too: `game/datafiles/maps/real_places.json:1099: foreign name 'Queen'` (local run 15:10) | gamedev | t_d0f24d14 |
| test_project.py::test_data_passes | b | Pine: `jsonschema is not installed` (2-2); it now fails here too for the map data, which is the (c) cluster t_d0f24d14 | pine runner then gamedev | fixed here, then t_d0f24d14 |
| test_project.py::test_build_inputs_are_committed | c | fails here too: `UNCOMMITTED SOURCE .../pp_03_harbor.ogg`, pp_04_navy_sailors, pp_05_small_ship (local run 15:10) | musician | t_b1e1a770 |
| test_save.py::test_check_data_passes_on_a_private_copy_of_the_data | b | Pine: `jsonschema is not installed` through check_data (2-2) | pine runner | fixed here: GOAL verifies `import jsonschema` |
| test_sfx.py::test_format_is_mono_44100_16bit | b | Pine: `assets/audio/sfx/menu_move.ogg: No such file or directory`, all ogg dropped by SKIP_EXT (2-2) | pine runner | fixed here: AUDIO_PREFIXES |
| test_sfx.py::test_every_file_peaks_at_minus_3_dbfs | b | same missing ogg files (2-2) | pine runner | fixed here: AUDIO_PREFIXES |
| test_sfx.py::test_no_click_at_either_end | b | same missing ogg files (2-2) | pine runner | fixed here: AUDIO_PREFIXES |
| test_sfx.py::test_no_constant_offset | b | same missing ogg files (2-2) | pine runner | fixed here: AUDIO_PREFIXES |
| test_sfx.py::test_ogg_files_are_present | b | same missing ogg files (2-2) | pine runner | fixed here: AUDIO_PREFIXES |
| test_sfx.py::test_one_ogg_is_mono_44100 | b | same missing ogg files (2-2) | pine runner | fixed here: AUDIO_PREFIXES |

Count: 8 (a), 34 (b), 7 (c). 8 + 34 + 7 = 49.

## The 12 ERROR rows from the same run

An ERROR is a collection or fixture failure, not a pass, so it is classified too.

| row | class | evidence | owner | fix card |
|---|---|---|---|---|
| test_beat_sheet.py::test_the_roadmap_holds_six_steps_in_order | b | `FileNotFoundError: ROADMAP-2026-10-22.md`; the root document was not in INCLUDE (2-1, reproduced in the extracted zip) | pine runner | fixed here: root documents in INCLUDE |
| test_beat_sheet.py::test_each_step_names_a_spec_number_a_lane_and_a_check | b | same missing `ROADMAP-2026-10-22.md` (2-1) | pine runner | fixed here: root documents in INCLUDE |
| test_beat_sheet.py::test_each_step_lane_is_a_lane_the_roadmap_itself_lists | b | same missing `ROADMAP-2026-10-22.md` (2-1) | pine runner | fixed here: root documents in INCLUDE |
| test_beat_sheet.py::test_each_step_names_beats_that_exist_in_the_sheet | b | same missing `ROADMAP-2026-10-22.md` (2-1) | pine runner | fixed here: root documents in INCLUDE |
| test_beat_sheet.py::test_each_step_closes_on_the_clock_the_sheet_gives_its_last_beat | b | same missing `ROADMAP-2026-10-22.md` (2-1) | pine runner | fixed here: root documents in INCLUDE |
| test_first_fight.py::test_the_gml_function_is_the_shape_this_file_reimplements | b | fixture raised on the 14:06 shard; passes here and passes in the rerun (2-2) | pine runner | fixed here: GOAL pins the working directory |
| test_first_fight.py::test_three_worked_cases_match_the_director | b | same fixture failure (2-2) | pine runner | fixed here: GOAL pins the working directory |
| test_first_fight.py::test_the_bar_is_monotonic_so_no_press_is_wasted | b | same fixture failure (2-2) | pine runner | fixed here: GOAL pins the working directory |
| test_first_fight.py::test_one_fight_removes_the_enemy_at_every_bar_power | b | same fixture failure (2-2) | pine runner | fixed here: GOAL pins the working directory |
| test_first_fight.py::test_the_hero_survives_the_worst_case_for_every_turn_the_fight_runs | b | same fixture failure (2-2) | pine runner | fixed here: GOAL pins the working directory |
| test_first_fight.py::test_raising_the_enemy_hp_breaks_the_one_command_win | b | same fixture failure (2-2) | pine runner | fixed here: GOAL pins the working directory |
| test_first_fight.py::test_raising_the_enemy_attack_breaks_the_ceiling_and_the_margin | b | same fixture failure (2-2) | pine runner | fixed here: GOAL pins the working directory |

## Changes in pine_offload.py

`<workspace>\Shared\projects\arananet\pine\pine_offload.py`:

1. INCLUDE now carries the root documents the tests read: ROADMAP-2026-10-22.md, TITLE-COORD.md,
   PROGRESS.md, DEVLOG.md, PLAN.md, PLAN-V2-2026-10-21.md, SUMMARY-FOR-NAYIL.md.
2. AUDIO_PREFIXES gains `game/datafiles/sfx/`, so the committed sfx mirror travels with the tests.
3. GOAL pins the working directory to `~/shared/projects/primordial-paradox` and forbids copying or
   moving the tree (the tests resolve two directories above themselves), and verifies
   `import jsonschema, PIL, numpy, yaml, requests, pytest` before running.
4. Already in place from the first attempt and kept: EXTRA (the musician note and the gate config),
   the audio prefix lift to 8 MB, EXCLUDE of knowledge/study, GIT_TESTS (test_build_inputs.py and
   test_test_inputs.py stay on the Windows suite because a zipped tree cannot answer a git question).

No test was weakened and no test file was edited.

## Rerun summary

Command: `python <workspace>\Shared\projects\arananet\pine\pine_offload.py --shards 3 --name triage`
(2026-10-22 15:30, zip bytes 29268005, 42 files, 3 shards).

| run | passed | failed | errors | file |
|---|---|---|---|---|
| before, 2026-10-22 14:06 | 666 | 49 | 12 | offload-full2-0.json, -1.json, -2.json |
| after, 2026-10-22 15:30 | 725 | 24 | 0 | offload-triage-0.json, -1.json, -2.json |

Per shard after: 269 passed 3 failed, 301 passed 7 failed, 155 passed 14 failed
(`<workspace>\Shared\projects\arananet\pine\data\results\offload-triage-0.json`,
`-1.json`, `-2.json`).

The rerun did not reach windows-only. It removed the 12 error rows, all 34 zip gaps and 6 of the 7
real regressions from Pine's view. The 24 rows still red are:

- 9 rows from the map data cluster, which now fails on Windows too: check_data, save, look x4,
  project::data_passes, project::cleanroom_passes, cleanroom. Card t_d0f24d14 (gamedev).
- 1 row from the uncommitted ship theme sources: project::build_inputs_are_committed. Card t_b1e1a770 (musician).
- 5 rows that need the game window on Windows: capture_title x5. Permanent on Pine by design.
- 9 rows that compare committed art bytes with a fresh build, which the Linux Pillow build reproduces
  with different bytes: make_env_ship ts_ship.png, make_title_ui spr_pp_font8, intro star sprite,
  sync_art mirror, make_characters_v2 sailor and percy, title_art_v2 test_title_draws_no_cast,
  scene_palettes x2. These are the kind of row `pine_offload.py` documents as windows by design.

## Hotspot, and the reason counts move between runs

The tree was edited by other lanes while this triage ran, so two runs minutes apart disagree:
`spr_pp_title_logo.png` was rewritten at 15:18, `data/encounters/all.json` at 15:22, `data/maps/all.json`
is modified in the working tree, and `game/sprites_src/title/spr_title_theo*` and `spr_title_ronan*`
do not exist at all, which is what `test_scene_palettes` and `test_title_art_v2` report on Pine.

hotspot: data/maps/all.json and data/maps/real_places.json, plus game/sprites_src/title, because three
lanes are writing the map data and the title art while the gates read them. Decompose those files
before more work lands on them.

## What is still unproven

- test_first_fight.py (10 rows) and test_osm_to_map.py (1 row) are class (b) by the pass-locally rule,
  but the single file that the 14:06 shard lacked is not named in its truncated output. What is proven
  is that the 14:06 tracebacks all resolve to `~/repo` (not `~/shared/projects/primordial-paradox`) and
  that both files pass locally and pass in the corrected shard. The cause is the shard layout, named in
  the rows above, not a repository file; unverified whether a second missing file also contributed.
