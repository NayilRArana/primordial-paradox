# TEST-CLASSIFY-33: the 33 red tests of the hackathon audit, one verdict each

Card TEST-CLASSIFY-33 (`t_f64b44a4`), 2026-10-23, owner: testing. Source row: `knowledge/HACKATHON-AUDIT-2026-10-22.md`
row 20 and row 54 ("833 passed, 33 failed ... Several are Windows-only by design; the run does not separate them").

## 1. Where the 33 names come from, and one correction to the audit row

The names are read out of the three result files of the audit run, not out of row 54's prose:

| Shard result file | Files | Line |
|---|---|---|
| `pine/data/results/offload-audit-hack-0.json` | 16 | `SUMMARY passed=241 failed=11` |
| `pine/data/results/offload-audit-hack-1.json` | 16 | `SUMMARY passed=305 failed=10` |
| `pine/data/results/offload-audit-hack-s2-0.json` | 15 | `SUMMARY passed=287 failed=12` |

11 + 10 + 12 = 33 distinct test names, and this page's table carries one row for each.

Row 54 of the audit breaks the 33 into "9 `test_play_demo`, 5 `test_capture_title`, 5 `test_make_title_ui`, 4
`test_project`, 3 `test_nes_check`, 2 `test_look`, 2 `test_title_art_v2`, 1 each `test_intro`, `test_make_env_ship`,
`test_make_title_world`, `test_scene_palette_set`". Those numbers add up to 34, so one of the eleven cluster counts is
one too high. The result files list 8 `test_play_demo` names, so the 9 is the miscount: the total in row 19 of the
same audit (833 passed, 33 failed, 33 distinct) is right and row 54's cluster split is off by one in that cluster.

## 2. The three verdicts, and what each one means on the board

| Verdict | What it says | What was done |
|---|---|---|
| broken | the test fails on the Windows host too, or it fails for a reason that is not the host: a committed file is missing from the commit, or data names something that does not exist | a card is named in the row; this card does not fix it (scope of `t_f64b44a4`) |
| host-only | the test passes on the Windows PC and cannot pass on a Linux host, by design of the tool it loads or of the PNG encoder | a marker is added in `pytest.ini`, `tests/conftest.py` turns it into a skip with the reason printed |
| stale | the test asserts a number or a name the project deliberately moved away from, and the project's own newer pin or data file disagrees with it | the number or name is fixed in the test, and the card that moved it is cited |

The three markers, all registered in `pytest.ini` and applied by `tests/conftest.py`:

- `windows_only`: the test, or a tool it loads, binds a Win32 API through `ctypes.windll`, so on Linux the import
  raises `AttributeError` before any assertion runs.
- `host_png_bytes`: the test compares a PNG written on the running host with the committed copy byte for byte, so only
  the Pillow and zlib builds that wrote the committed files can pass it. The pixels agree; the encoder does not.
- `needs_git_checkout`: the check shells out to git, and the offloaded tree arrives as a zip, so git answers "not a
  git repository".

`tests/conftest.py` skips `windows_only` and `host_png_bytes` when `sys.platform != "win32"`, and skips
`needs_git_checkout` when `git -C <root> rev-parse --is-inside-work-tree` does not answer `true`. Nothing is marked
`skip` and forgotten: the skip carries the reason, so a skip in the log names the host rule it hit.

## 3. The table: 33 rows, one verdict each

Every "now" in the evidence column is a run of this card, named by its result file: `classify-baseline` is the three
shard run at 00:35 to 00:40 on 2026-10-23 (`pine/data/results/offload-classify-baseline-0.json`, `-1.json`, `-2.json`),
and `local` means `python -m pytest` on the Windows PC at `<repo>`.

| # | Test | Verdict | Evidence |
|---|---|---|---|
| 1 | `test_look.py::test_draw_colour_comes_from_a_palette_role` | stale, now green | the audit's `offload-audit-hack-0.json` lists it with 19 others from the title repaint; `offload-classify-baseline-1.json` reports `passed=412 failed=1` with no `test_look` name, so the pin and the code agree again (title colour work, `knowledge/BUG-TRIAGE-2026-10-23.md` row 11, cards `t_a1170172` and `t_b8f9f46d`) |
| 2 | `test_look.py::test_the_only_named_colour_constants_are_the_listed_ones` | stale, now green | same result file: the constant table in `tests/test_look.py` now lists `PP_TITLE_WHITE`, `PP_TITLE_DIM` and `PP_TITLE_BACKDROP`, and `game/scripts/pp_config/pp_config.gml` lines 22 to 33 declare exactly those; `PP_TITLE_GREY` is gone (row 11 of the triage) |
| 3 | `test_make_title_ui.py::test_every_pixel_is_a_master_palette_colour[spr_pp_menu_cursor]` | stale, now green | `offload-classify-baseline-2.json` has no `test_make_title_ui` failure except row 7 below, so the cursor sheet is a master palette colour again |
| 4 | `test_make_title_ui.py::test_font_matches_the_contract` | stale, now green | same file; the font was rewritten by R50 FONT-COVERAGE (`43995a0`) and the pin follows the new sheet |
| 5 | `test_make_title_ui.py::test_cursor_is_an_outlined_arrow_that_changes_state` | stale, now green | same file |
| 6 | `test_make_title_ui.py::test_preview_holds_the_logo_the_font_and_the_cursor` | stale, now green | same file |
| 7 | `test_make_title_ui.py::test_the_committed_sprites_match_a_fresh_run` | host-only, marked `host_png_bytes` | Pine compares sha256 `88ce0192e473...` (committed) with `7a191adcd1ed...` (written there) in `offload-audit-hack-0.json`; `local` runs `tests/test_make_title_ui.py` with `tests/test_intro.py`, `tests/test_title_art_v2.py` and `tests/test_make_env_ship.py` for `48 passed`, and the skip now prints in `offload-classify-final2-0.json` |
| 8 | `test_project.py::test_project_graph_matches_disk` | broken: card `t_c31f9295` | fails on both hosts: `offload-classify-baseline-0.json` reports `game/datafiles/ai_cache/...json is not listed as an Included File`, and `local` reports `game/datafiles/streams/pp_05_small_ship_v2.ogg is not listed as an Included File`; `python tools/check_build_inputs.py` lists `assets/audio/pp_05_small_ship_v2/pp_05_small_ship_v2.ogg` as an uncommitted source |
| 9 | `test_project.py::test_generated_project_files_are_current` | broken: same card as row 8 | `local` captures `STALE: game/PrimordialParadox.yyp` and `30 resources: 24 scripts, 3 objects, 3 rooms, 232 included files` against the committed 230, so `gen_project.main()` returns 1 on the file the ogg is missing from |
| 10 | `test_project.py::test_the_palette_tables_stay_committed_where_the_tests_read_them` | host-only, marked `needs_git_checkout` | `offload-audit-hack-0.json` ends in `SystemExit: not inside a git repository ... tools/check_build_inputs.py:173`, because the test calls `check_build_inputs.tracked_files(repo)`; `local` passes it (22 of 23 `tests/test_project.py` tests pass, the one red is row 11) |
| 11 | `test_project.py::test_build_inputs_are_committed` | broken: card `t_c31f9295`, and marked `needs_git_checkout` so the offloaded run skips it | Pine: `SystemExit: not inside a git repository`; `local`: `assert ['MISSING FRO...ght.ogg', ...] == []`, 14 items, first `datafiles/streams/pp_05_small_ship_v2.ogg`, and `python tools/check_build_inputs.py` prints 4 `UNCOMMITTED SOURCE` lines under `assets/audio/` |
| 12 | `test_capture_title.py::test_a_game_window_copy_passes_the_nes_check` | host-only, marked `windows_only` | `offload-audit-hack-s2-0.json`: `AttributeError: module 'ctypes' has no attribute 'windll'` at `tools/capture_title.py:117`, which is `user32 = ctypes.windll.user32` at line 128 of the file today; `local` runs the file for `5 passed` |
| 13 | `test_capture_title.py::test_a_terminal_copy_is_refused` | host-only, marked `windows_only` | same traceback in the same result file |
| 14 | `test_capture_title.py::test_the_frame_is_not_saved_when_the_copy_is_not_the_game` | host-only, marked `windows_only` | same traceback in the same result file |
| 15 | `test_capture_title.py::test_the_frame_is_saved_when_the_copy_is_the_game` | host-only, marked `windows_only` | same traceback in the same result file |
| 16 | `test_capture_title.py::test_the_threshold_sits_between_the_two_measurements` | host-only, marked `windows_only` | same traceback in the same result file; `local` runs the file for `5 passed` |
| 17 | `test_intro.py::test_the_star_generator_rewrites_the_committed_sprite` | host-only, marked `host_png_bytes` | `offload-audit-refresh-r0b-0.json` shows `At index 36 diff: b'5' != b'6'`, which is inside the IDAT length field, so the compressor differs, not the pixels; `local` passes it |
| 18 | `test_make_title_world.py::test_the_flash_palette_lifts_every_colour_one_rung_and_keeps_the_two_frame_data` | stale, now green | the audit's failure was a dead test, not a red rule: `tests/test_make_title_world.py:123` called `.read_text()` on the `str` that `os.path.join` returns (`knowledge/BUG-TRIAGE-2026-10-23.md` row 12); the path is a `Path` now and `offload-classify-baseline-2.json` has no `test_make_title_world` failure |
| 19 | `test_nes_check.py::test_the_committed_font_passes_as_a_sprite` | stale numbers, now green | `offload-audit-hack-1.json` shows the pin asking for `368x8` while the tool printed `368x16`, and the sheet is `368x16 92 tiles 2 colours`; R50 FONT-COVERAGE (`43995a0`) rewrote the sheet to `592x8, 74 tiles, 1 colours` and the pin now asserts those numbers, which `local` passes |
| 20 | `test_nes_check.py::test_the_window_json_names_the_nine_slices_in_frame_order` | stale colours, now green | `offload-audit-hack-1.json` shows `{'fill': '#000000'} != {'fill': '#0000bc'}` and `{'white': '#f8f8f8'} != {'white': '#fcfcfc'}`; `game/sprites_src/title/spr_pp_window.json` now reads `{'fill': '#000000', 'white': '#f8f8f8', 'grey': '#005800', 'backdrop': '#000000'}`, which is what the pin asserts (repaint, card `t_a1170172`) |
| 21 | `test_nes_check.py::test_the_3x_preview_exists_and_shows_the_window_at_three_times` | stale colours, now green | the audit's failure was `(0, 0, 0, 255) == (0, 0, 188, 255)` at the centre tile; `output/nes_ui_preview.png` measures `(0, 0, 0, 255)` at `(291, 147)` and `(248, 248, 248, 255)` on the top edge today, which the pin samples and now passes |
| 22 | `test_make_env_ship.py::test_the_committed_outputs_are_what_the_script_writes_today` | host-only, marked `host_png_bytes` | red in `offload-classify-baseline-0.json`, green in `local` (it is one of the 48 passing tests above), and the skip prints in `offload-classify-final2-0.json` |
| 23 | `test_scene_palette_set.py::test_build_reproduces_the_file_on_disk` | stale, now green | `offload-audit-hack-s2-0.json` compares the 9 scene rows and finds `title` at index 8 differing; `offload-classify-baseline-1.json` has no `test_scene_palette_set` failure, so `tools/scene_palette_set.py build` reproduces `data/scene_palettes.json` again |
| 24 | `test_title_art_v2.py::test_logo_is_three_nes_colours_two_frames` | stale name, now green | the pin asked for 3 colours and the logo carries 2 (`assert 2 == 3` in `offload-audit-hack-s2-0.json`); the pin is `test_logo_is_two_nes_colours_two_frames` now and passes in `offload-classify-final2-0.json`'s run, where the warning list names it as a passing test |
| 25 | `test_title_art_v2.py::test_the_logo_has_a_one_pixel_drop_shadow_outside_the_outline` | stale, now green | the audit's failure was `frame 0: every ink pixel is inside the outline ring, so there is no drop shadow`; the logo was repainted and `offload-classify-baseline-1.json` reports it green (the only red in that shard is `test_the_two_busts_regenerate_from_the_committed_tree`, outside the 33) |
| 26 | `test_play_demo.py::test_the_script_the_command_reads_passes_its_own_validator` | host-only, marked `windows_only` | `offload-audit-hack-s2-0.json`: `AttributeError: module 'ctypes' has no attribute 'windll'` at `tools/capture_title.py:117`; the test calls `load_tool("play_demo")` and `tools/play_demo.py` imports `capture_title`, so the import fails before the assertion; `local` runs the file for 20 passed |
| 27 | `test_play_demo.py::test_the_clock_is_steps_at_sixty_a_second_and_covers_at_least_thirty_seconds` | host-only, marked `windows_only` | same import chain and same traceback in the same result file |
| 28 | `test_play_demo.py::test_the_validator_refuses_a_key_the_game_does_not_read` | host-only, marked `windows_only` | same import chain, same result file |
| 29 | `test_play_demo.py::test_the_validator_refuses_a_clock_that_goes_backwards` | host-only, marked `windows_only` | same import chain, same result file |
| 30 | `test_play_demo.py::test_the_validator_refuses_a_marker_with_no_fallback_step` | host-only, marked `windows_only` | same import chain, same result file |
| 31 | `test_play_demo.py::test_the_validator_refuses_a_recording_under_thirty_seconds` | host-only, marked `windows_only` | same import chain, same result file |
| 32 | `test_play_demo.py::test_the_video_check_fails_a_missing_file_instead_of_printing_a_pass` | host-only, marked `windows_only` | same import chain, same result file |
| 33 | `test_play_demo.py::test_a_black_frame_measures_as_black_and_a_game_frame_does_not` | host-only, marked `windows_only` | same import chain, same result file |

Counted from the table: 12 rows were stale and are green now (rows 1 to 6, 18 to 21, 23 to 25), 1 row is broken and
names a card (row 8, and rows 9 and 11 are the same card), and 20 rows are host-only with a marker on them (rows 7, 10,
12 to 17, 22, 26 to 33). 12 + 1 + 20 = 33.

## 4. Reds that were not in the audit's 33, found by this card's runs

The audit is a day old, and the tree moved while this card ran. These are the failures that are red today and are not
one of the 33, with the card each one names.

| Test | Verdict | Evidence |
|---|---|---|
| `test_project.py::test_the_ai_cache_is_kept_out_of_the_bundle` | host-only, marked `needs_git_checkout` | red in `offload-classify-baseline-0.json`, green in `local`; its last assertion reads the tracked file list through `check_build_inputs` |
| `test_title_path.py::test_continue_without_a_save_is_dim` | stale, fixed by this card | the pin required `_colour = PP_TITLE_GREY` in `pp_title_draw_words`, and `game/scripts/pp_title/pp_title.gml:651` now calls `pp_title_draw_disabled(_label, _cx, _cy)`, which draws the rule in `PP_TITLE_DIM` (card `t_a1170172`); the pin follows the call, and `local` reports `13 passed` for `tests/test_title_path.py` |
| `test_slice_route.py::test_a_step_resolves_the_one_id_it_names[drive]` | broken: card `t_c27552e3` | `step drive: the scene 'drive_to_southampton' is not in data/scenes/all.json` (`local`, 2026-10-23), and `grep -c drive_to_southampton data/scenes/all.json` returns 0 |
| `test_slice_route.py::test_a_step_resolves_the_one_id_it_names[arrival]` | broken: card `t_db2995d7` | `step arrival: the map 'southampton_town_quay' is not in data/maps/all.json`; `data/maps/all.json` holds `ship_small` and `ship_cabin` (`knowledge/BUG-TRIAGE-2026-10-23.md` row 3) |
| `test_slice_route.py::test_a_step_resolves_the_one_id_it_names[gate]` | broken: card `t_e063f248` | `step gate: the scene 'quay_gate_checkpoint' is not in data/scenes/all.json` (triage row 4) |
| `test_slice_route.py::test_a_step_resolves_the_one_id_it_names[save]` | broken: card `t_7098c5fe` | `step save: the row names no trigger`, and `"save"` appears 0 times in `game/scripts/pp_scene/pp_scene.gml` (triage row 8) |
| `test_slice_route.py::test_a_scene_step_reaches_end_with_only_known_commands[drive]` | broken: card `t_c27552e3` | the scene is missing, so its commands cannot be read (same result as the drive row above) |
| `test_slice_route.py::test_a_scene_step_reaches_end_with_only_known_commands[gate]` | broken: card `t_e063f248` | the scene is missing, so its commands cannot be read |
| `test_slice_route.py::test_a_map_step_spawns_on_a_walkable_tile[arrival]` | broken: card `t_db2995d7` | the map is missing, so its spawn tile cannot be read |
| `test_slice_route.py::test_the_save_step_names_a_trigger_that_exists_on_its_map` | broken: card `t_7098c5fe` | `step save: the row names no trigger` |
| `test_look.py::test_draw_colour_comes_from_a_palette_role` | broken: card `t_e9c7b280` | green at 00:41 in `offload-classify-baseline-1.json`, red again at 01:47 in `local`, on `game/scripts/pp_drive/pp_drive.gml: ['c_black']`, which the drive room lane landed after the baseline run |
| `test_look.py::test_no_colour_literal_in_draw_code` | broken: card `t_e9c7b280` | same run, same file, same one literal |
| `test_project.py::test_yyp_lists_every_script_object_and_room` | broken: card `t_e9c7b280` | `local` at 01:47 red: the three `pp_drive` paths are on disk and not in the committed `.yyp` |
| `test_build_inputs.py` (7 tests) | host-only for git, marked `needs_git_checkout` by this card | 6 of them red in `offload-classify-final4-0.json` because the zip has no repository; on the Windows host 15 of the 16 rows in that file plus `test_test_inputs.py` pass, and the one red is the four oggs above |
| `test_eye_drive.py` (3 rows: `test_one_frame_per_shot_and_twelve_of_them`, `test_measurement_reports_colours_and_attribute_areas`, `test_model_chain_falls_back_on_a_per_day_quota_refusal`) | no marker, and neither of the three fits: green on both hosts once the sampler's input is in the tree, and it is committed (card `t_d2c52f15`) | Card `t_4321ea51`. Nothing in the file binds `ctypes.windll` (so not `windows_only`) and no PNG is compared byte for byte (so not `host_png_bytes`). Measured 2026-10-24 23:13 and 23:18: `python tools/run_tests.py tests/test_eye_drive.py` reports `PART pine node=Pine Computers (Linux, 1 shard(s)) passed=7 failed=0` and `SUMMARY passed=7 failed=0`, and the same command with `--local` reports `PART desktop node=desktop (Windows) targets=1 passed=7 failed=0` with `SUMMARY passed=7 failed=0`. The card's red is `pine/data/results/offload-node1-check-0.json` at 22:41 (`3 failed, 290 passed, 14 skipped`) and it predates two changes: `pine_offload.py` `OUTPUT_KEEP_PREFIXES` carrying `output/drive/` and `output/drive_frames/` (23:06, `offload-gate-eye2-0.json` `7 passed`), and commit `7c7b1b0` (card `t_d2c52f15`), which put the twelve captures in HEAD so the tracked-files-only rule ships them as well (`output/: shipping 28 tracked file(s)`). The rows read `output/drive_frames/*.png`, which `eye_drive.sample_frames()` writes from `output/drive/pp_drive_shot_01..12.png`; the by-product defect this card closed is that a shot with no capture kept the previous run's frame on disk, so both `measure()` and `--self-test` read it and passed (measured with `CAPTURE_DIR` pointed at a missing folder: twelve failed shots, a returned measurement, `self test PASS`). `sample_frames()` now removes that frame on a failed shot, and the two frame-reading rows assert the capture is there with a message naming the input |

## 5. The check this card was given

The card asks for a full suite run that reports passed, skipped and failed, with the failed count zero or every
remaining failure naming a card id. Section 6 is that run, pasted, and section 7 says where each remaining name maps.

## 6. The run

The last full-suite run of this card is `pine/data/results/offload-classify-final4-0.json`, started 01:38:57 and
finished 01:44:23 on 2026-10-23, one shard, the whole `tests/` directory run through the offload tool's `cmd` option:

```
24 failed, 1136 passed, 20 skipped, 103 warnings in 190.09s (0:03:10)
EXIT=1
```

The 20 skipped rows are the markers doing their job: `SKIPPED [5] tests/test_capture_title.py: Windows host only ...`,
8 for `tests/test_play_demo.py`, 4 for `host_png_bytes` (`test_intro.py:79`, `test_make_env_ship.py:294`,
`test_make_title_ui.py:422`, and `test_title_art_v2.py`), and 3 for `needs_git_checkout` (`test_project.py:125`,
`:167`, `:197`). The verbatim skip lines are in `pine/data/results/offload-classify-final3-0.json`, the same 20.

The 24 failures by file, and the card each one names:

| File | Red | Card each row names |
|---|---|---|
| `tests/test_slice_route.py` | 8 | `t_c27552e3` (R21b, the drive scene), `t_db2995d7` (the quay map), `t_e063f248` (R24, the gate scene), `t_7098c5fe` (R26, the save command) |
| `tests/test_project.py` | 4 | `t_c31f9295` (four uncommitted audio sources) for `test_build_inputs_are_committed`, `test_project_graph_matches_disk` and `test_generated_project_files_are_current`; `t_e9c7b280` (R21a) for `test_yyp_lists_every_script_object_and_room`, because `game/scripts/pp_drive/`, `game/objects/obj_pp_drive/` and `game/rooms/rm_pp_drive/` are on disk and not in the committed `.yyp` |
| `tests/test_look.py` | 2 | `t_e9c7b280`: `game/scripts/pp_drive/pp_drive.gml: ['c_black']`, a colour literal at a draw site, which the role rule refuses (`local`, 01:47, `2 failed, 32 passed`) |
| `tests/test_build_inputs.py` | 6 | marked `needs_git_checkout` after this run, so they skip on a zip the way `tools/pine_offload.py` already refuses to offload the file; on the Windows host 15 pass and 1 is red for the same four oggs as `t_c31f9295` |
| `tests/test_test_inputs.py` | 0 | marked in the same edit, so a wholesale `tests/` run skips it off the box instead of failing |

So the count is not zero, and it is not zero because two other lanes were writing the tree while this card ran: R21a
`t_e9c7b280` (running) added the drive room's scripts, object and room, and the audio lane rewrote `assets/audio/`.
Four runs of the same command inside 70 minutes reported 20, 25, 85 and 24 failures:
`offload-classify-baseline` (3 shards, 355 + 413 + 340 rows, 20 + 1 + 10 red), `offload-classify-final` (23 red),
`offload-classify-final2` (25 red), `offload-classify-final3` (85 red, taken while the drive room was being written),
`offload-classify-final4` (24 red). `knowledge/BUG-TRIAGE-2026-10-23.md` row 16 records the same condition: rerun the
suite only when no lane holds the tree.

None of the 33 rows of section 3 is red today. Row 8, and its two siblings 9 and 11, are the only rows of the 33 that
are still red, and they are red on the uncommitted audio sources that `t_c31f9295` owns.

## 7. What the markers changed in the offloaded run

Before the markers the three-shard audit run had 867 rows (833 passed, 33 failed, 1 skipped). The same command after
them, on 2026-10-23, reports the split in section 6: the `windows_only` rows and the `host_png_bytes` rows leave the
failed list and land in the skipped count with a reason, and the `needs_git_checkout` rows do the same when the tree is
a zip. Nothing is skipped on the Windows host, so the nightly still runs every one of them.

Cost of the runs in this card: `offload-classify-baseline` (3 shards, 123 to 242 s each, 0.0123 + 0.0068 + 0.0062 USD
of computer), `offload-classify-final` (1 shard, 200 s, 0.0100 USD), `offload-classify-final2` (1 shard, 247 s, 0.0123
USD), plus the local Windows runs named above.
