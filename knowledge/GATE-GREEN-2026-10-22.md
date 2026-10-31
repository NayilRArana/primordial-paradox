# GATE-GREEN 2026-10-22

Card t_dacb50c7 (testing). Run of the whole primordial-paradox Python suite on Pine Computers at
18:56, compared with `knowledge/TEST-TRIAGE-PINE-2026-10-22.md`, every new red classified, and a fix
card raised for each real regression that no live card already owns.

Check named before work started: the three `SUMMARY` lines in
`<workspace>\Shared\projects\arananet\pine\data\results\offload-gate-0.json`, `-1.json`,
`-2.json` (pass and fail counts, no SKIP and no errored row counted as a pass), plus a Windows run of
every file that carries a new red, so a Pine-only row can be told from a real regression.

No key was opened or printed. `PINE_SANDBOX_API_KEY` was read from the environment only.

## The run

Command: `python <workspace>\Shared\projects\arananet\pine\pine_offload.py --shards 3 --name gate`
interpreter `<home>\AppData\Local\Python\bin\python.exe` (3.14.7, the one that can import
pinesandbox). Zip 37,453,029 bytes, 49 test files, 3 shards, started 18:56:12, last shard
finished 19:00:58. The 51 `test_*.py` files on disk are 49 offloaded plus the two `GIT_TESTS`
(`tests/test_build_inputs.py`, `tests/test_test_inputs.py`) that stay on the Windows suite.

| shard | passed | failed | skipped | errors | file |
|---|---|---|---|---|---|
| gate-0 | 258 | 6 | 0 | 0 | `offload-gate-0.json` |
| gate-1 | 354 | 17 | 1 | 0 | `offload-gate-1.json` |
| gate-2 | 245 | 13 | 0 | 0 | `offload-gate-2.json` |
| **total** | **857** | **36** | **1** | **0** | 894 rows |

The pytest summary lines those counts come from: `6 failed, 258 passed`, `17 failed, 354 passed, 1 skipped`,
`13 failed, 245 passed`, all three stored in the `results_txt` field of the JSON files above.

The one SKIP is not counted as a pass: `tests/test_dialogue_v2.py:340`, "no entry carries choices yet:
the gate checkpoint waits on data/flags.json (see the card)". It skips on Windows too (local run
19:07, same reason), so it is a known pending card, not a Pine effect.

## Trend

| run | when | passed | failed | skipped | error rows | pass rate | file |
|---|---|---|---|---|---|---|---|
| full2 | 14:06 | 666 | 49 | 4 | 12 | 92.0% | `offload-full2-0/-1/-2.json` |
| triage | 15:30 | 725 | 24 | 0 | 0 | 96.8% | `offload-triage-0/-1/-2.json` |
| gate | 18:56 | 857 | 36 | 1 | 0 | 95.9% | `offload-gate-0/-1/-2.json` |

Pass rate fell 0.9 points from the 15:30 rerun while the suite grew by 7 files and 145 rows, so the
counts are not a like-for-like series: 42 files ran at 15:30, 49 ran here. What the series does show:
zero error rows for the second run in a row (the collection and fixture class is gone), the 9-row map
data cluster from t_d0f24d14 is green, the 5-row skip guard from t_6fe82061 is green, and the 36 red
rows now sit in three places: a title art and palette rework that was landing in the tree while the
gate ran, two uncommitted build inputs, and the Windows-only classes that Pine can never prove.

## Every red row, classified

Classes: (a) windows only, (b) zip gap (would be fixed in `pine_offload.py` `INCLUDE`), (c) real
regression, the card or the live card that owns it named. Local evidence is the Windows run of the
same files in the real tree at 19:00 and 19:07 (11 failed, 465 passed, 9 errors across
`tests/test_drive_v2.py`, `test_make_title_world.py`, `test_nes_check.py`, `test_play_demo.py`,
`test_scene_palette_set.py`, `test_title_art_v2.py`, `test_look.py`, `test_scene_palettes.py`,
`test_make_title_ui.py`, `test_project.py`, `test_build_inputs.py`, `test_cleanroom.py`,
`test_intro.py`, `test_make_env_ship.py`, `test_sync_art.py`, `test_test_inputs.py`,
`test_palette_synergy.py`).

| test | class | evidence | owner | card |
|---|---|---|---|---|
| test_drive_v2.py::test_cell_is_pitch_stable_so_it_counts_as_one_return | not a regression | red at 18:56 and green in the focused Pine rerun at 19:05 (`offload-gateb-1.json`, 8 passed 0 failed); the two cue files were being rewritten in the tree at 18:36 | musician | none |
| test_intro.py::test_the_star_generator_rewrites_the_committed_sprite | a | committed PNG bytes come from the Windows Pillow and zlib build; passes here, byte mismatch on Pine (`offload-gate-0.json`) | gamedev | none, Windows suite |
| test_capture_title.py x5 (test_a_game_window_copy_passes_the_nes_check, test_a_terminal_copy_is_refused, test_the_frame_is_not_saved_when_the_copy_is_not_the_game, test_the_frame_is_saved_when_the_copy_is_the_game, test_the_threshold_sits_between_the_two_measurements) | a | `AttributeError: module 'ctypes' has no attribute 'windll'` at `tools/capture_title.py:117`, no window API on Linux (`offload-gateb-0.json`) | gamedev | none, Windows suite |
| test_play_demo.py x8 (test_the_script_the_command_reads_passes_its_own_validator, test_the_clock_is_steps_at_sixty_a_second_and_covers_at_least_thirty_seconds, test_the_validator_refuses_a_key_the_game_does_not_read, test_the_validator_refuses_a_clock_that_goes_backwards, test_the_validator_refuses_a_marker_with_no_fallback_step, test_the_validator_refuses_a_recording_under_thirty_seconds, test_the_video_check_fails_a_missing_file_instead_of_printing_a_pass, test_a_black_frame_measures_as_black_and_a_game_frame_does_not) | a | `tools/play_demo.py:53` imports `capture_title` at module level and `tools/capture_title.py:117` builds `ctypes.windll.user32` at import, so the module cannot load on Linux; 17 rows pass here (`offload-gateb-0.json`, 9 passed 8 failed) | testing | none; cheapest cure noted below |
| test_make_env_ship.py::test_the_committed_outputs_are_what_the_script_writes_today | a | passes here, fresh build hash differs on Pine (same class as the triage row) | gamedev | none, Windows suite |
| test_make_title_world.py::test_the_flash_palette_lifts_every_colour_one_rung_and_keeps_the_two_frame_data | c | fails here too: `title_L1_sky_flash draws [0, 15, 32, 40], not the lifted night entries` | gamedev | live card t_a1170172, comment posted |
| test_nes_check.py::test_the_committed_font_passes_as_a_sprite | c | fails here too: audit says `spr_pp_font8.png 368x16 92 tiles`, the test pins `368x8` | gamedev | live card t_a1170172, comment posted |
| test_nes_check.py::test_the_window_json_names_the_nine_slices_in_frame_order | c | fails here too: nine slice fill and stroke colours differ | gamedev | live card t_a1170172, comment posted |
| test_nes_check.py::test_the_3x_preview_exists_and_shows_the_window_at_three_times | c | fails here too: preview pixel (0,0) is (0,0,0,255), expected (0,0,188,255) | gamedev | live card t_a1170172, comment posted |
| test_look.py::test_draw_colour_comes_from_a_palette_role | c | fails here too: `a draw call sets its colour from something that is not a role` | gamedev | live card t_a1170172, comment posted |
| test_look.py::test_the_only_named_colour_constants_are_the_listed_ones | c | fails here too: new constants `PP_COLOUR_MISSING, PP_TITLE_BACKDROP, PP_TITLE_GREY, PP_TITLE_WHITE, PP_UNTINTED` | gamedev | live card t_a1170172, comment posted |
| test_scene_palette_set.py::test_build_reproduces_the_file_on_disk | c | fails here too: `scene_palette: title must declare 4 background and 4 sprite palettes`, `data/palettes/scene_title.json` written at 18:57 declares 3 and 3 | gamedev | live card t_a1170172, comment posted |
| test_scene_palettes.py::test_the_art_on_disk_fits_the_scenes | c | fails here too: `title: spr_title_konrad has 16 group(s) whose colours fit none of the four sprite palettes`, same for `spr_title_zander` | gamedev, busts under t_aa552437 | live card t_a1170172, comment posted |
| test_scene_palettes.py::test_the_check_reports_its_numbers_so_a_reviewer_can_read_them | c | fails here too, same two busts | gamedev, busts under t_aa552437 | live card t_a1170172, comment posted |
| test_title_art_v2.py::test_logo_is_three_nes_colours_two_frames | c | errors here too: the logo measures `{'#7c7c7c': 9367, '#f8b800': 925}`, two colours where the test pins three | gamedev | live card t_a1170172, comment posted |
| test_title_art_v2.py::test_the_logo_has_a_one_pixel_drop_shadow_outside_the_outline | c | errors here too: `frame 0: every ink pixel is inside the outline ring, so there is no drop shadow` | gamedev | live card t_a1170172, comment posted |
| test_make_title_ui.py::test_every_pixel_is_a_master_palette_colour[spr_pp_menu_cursor] | c | fails here too: `spr_pp_menu_cursor uses #7c7c7c, which is not in data/palette.json` | gamedev | live card t_a1170172, comment posted |
| test_make_title_ui.py::test_font_matches_the_contract | c | fails here too: `assert (8, 16) == (8, 8)`, the generator now writes two tiles tall | gamedev | live card t_a1170172, comment posted |
| test_make_title_ui.py::test_cursor_is_an_outlined_arrow_that_changes_state | c | fails here too: `cursor frame 0 outline pixel 0,0 is (124, 124, 124, 255)` | gamedev | live card t_a1170172, comment posted |
| test_make_title_ui.py::test_preview_holds_the_logo_the_font_and_the_cursor | c | fails here too: `the preview does not carry the 3x font strip` | gamedev | live card t_a1170172, comment posted |
| test_make_title_ui.py::test_the_committed_sprites_match_a_fresh_run | c | Pine red, passes here; `tools/art/make_title_ui.py` was modified but not committed at 18:59, so the committed sprites and a fresh run disagree in the working tree | gamedev | live card t_a1170172, comment posted |
| test_project.py::test_project_graph_matches_disk | c | fails here too: `tools/check_project.py` reports three Included Files the yyp does not list: `game/datafiles/demo/manifest.json`, `game/datafiles/demo/run_001.json`, `game/datafiles/streams/pp_drive_v2.ogg` | builder (yyp), files from t_9ebd35dc and the musician lane | t_e8f3ce1b |
| test_project.py::test_generated_project_files_are_current | c | fails here too: `STALE: game/PrimordialParadox.yyp`, 230 included files on disk, checker exits 1 | builder (yyp) | t_e8f3ce1b |
| test_project.py::test_build_inputs_are_committed | c | fails here too: `MISSING FROM COMMIT datafiles/streams/pp_drive.ogg`, `datafiles/streams/title_theme_v5.ogg`, and both sources are `UNCOMMITTED SOURCE` under `assets/audio/` | musician | t_f1692c31 |
| test_project.py::test_the_palette_tables_stay_committed_where_the_tests_read_them | unproven | passes here (local `tests/test_project.py` run 19:07: 3 failed, none of them this row), red on Pine; the focused Pine rerun that would name the reason died on a transport error: `PineCallError: pine write_file failed: ConnectionError ... [Errno 10054] An existing connection was forcibly closed` (`offload-gatec-0.json`, status error) | unverified | none yet |
| test_scene_palettes.py::test_both_scene_files_declare_the_nes_budget | c | fails here only (Pine died on an earlier row); same 3-of-4 palette set cause | gamedev | live card t_a1170172 |
| test_scene_palettes.py::test_the_scenes_stay_inside_the_colour_cap | c | fails here only, same cause | gamedev | live card t_a1170172 |

Count of the 36 Pine red rows: 15 (a) windows only, 0 (b) zip gap, 19 (c) real regression, and 2 that
are either not reproducible or unproven (the drive row and the palette tables row). 15 + 0 + 19 + 2 = 36.
No new zip gap appeared: nothing that is in the tree and readable on Linux was missing from the zip,
so `INCLUDE` in `pine_offload.py` is unchanged by this run.

## Why one cluster owns most of the reds, and why there is no second card for it

Sixteen of the 19 real regressions are one cluster: the title art and palette rework that was being
written into the working tree while the gate ran. The evidence is timestamps, not guesswork:
`data/palettes/scene_title.json` was written at 18:57 with 3 background and 3 sprite palettes where
`tools/art/scene_palette.py:112` now demands 4 and 4, and that same file's mtime was 19:03 for
`tools/art/make_pp_window.py` and 18:59 for `tools/art/make_title_ui.py`, all three modified and
uncommitted (`git status --porcelain -- tools/art data/palettes`). Card t_a1170172 (gamedev,
"[TEMPO-1 follow-up] the composited title frame is not NES legal: 2 blended colours") was running and
heartbeating every 30 seconds throughout, and t_aa552437 (TITLE-BUSTS-REDRAW) explains the two Konrad
and Zander bust rows. Raising a second card against the same files would put two agents in one file,
so the rows were posted as a comment on t_a1170172 instead, with the numbers above. gamedev is a HEAD
under the 2026-10-22 chain of command; the comment reports evidence and leaves the fix and the spec to
that lane.

## The two new fix cards

1. yyp drift, real and uncovered by any live card: the committed project file does not list the demo
   mirror (`game/datafiles/demo/manifest.json`, `run_001.json`, written 18:07 to 18:25 by the DEMO-KIT
   card t_9ebd35dc) or `game/datafiles/streams/pp_drive_v2.ogg` (18:36). `tools/gen_project.py` writes
   the file, and the rule in t_ab58bf6b says the lane that adds a datafile runs it. Assigned to
   builder, the lane that carried t_d0f24d14. Card t_e8f3ce1b.
2. uncommitted audio sources, real and uncovered: `assets/audio/pp_drive/pp_drive.ogg` and
   `assets/audio/title_theme_v5/title_theme_v5.ogg` are on disk and not in the commit their mirrors
   point at. Assigned to musician, whose running cards (t_b8f9f46d R37 TITLE-V5, t_6a70f6e8
   AUTO-MUSIC-NEXT) are writing those directories; the earlier card t_b1e1a770 closed the previous
   three files, not these. Card t_f1692c31.

## The cheapest way to shrink the Windows-only class (not done here)

Eight of the 14 (a) rows are `tests/test_play_demo.py`: `tools/play_demo.py:53` does
`import capture_title as cap` at module scope and `tools/capture_title.py:117` runs
`user32 = ctypes.windll.user32` at import, so the module cannot even load on Linux. A lazy import in
the four functions that touch a window would let the validator and video-check rows run on Pine
instead of being written off as Windows-only. It is 39 `cap.` call sites, so it was not attempted
inside this card's 45 minute budget, and no test was edited.

## What is still unproven

- `test_project.py::test_the_palette_tables_stay_committed_where_the_tests_read_them` has no captured
  Pine reason: the shard output is `tail -80` and the row fell above it, and the focused rerun
  (`--name gatec`) failed on a Pine transport reset, not on a test. The check that settles it is
  `python pine_offload.py --shards 1 --name gatec --files tests/test_project.py` once more.
- Whether the 19 (c) rows go green when the title rework commits and the two audio files land. The
  gate has to be rerun after those lands; this report is a snapshot of 18:56, and the tree moved
  under it (the same reason counts moved between the 15:30 and 18:56 runs).

hotspot: `data/palettes/scene_title.json`, `tools/art/scene_palette.py`, `tools/art/make_title_ui.py`
and `game/sprites_src/title/`, because one rework writes all four while three checkers read them, and
the gate reds follow that file set, not the test set.
