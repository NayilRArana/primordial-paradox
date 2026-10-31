# Bug triage, 2026-10-23: every red thing, ordered by what it does to the demo

Card R51 BUG-TRIAGE (`t_5c018549`). Owner of this page: the audit lane. Scope of the card: this one file.

Method. Every row below is a command this run executed on
`<repo>` between 20:12 and 20:34 Pacific on 2026-10-22, or a
number this run measured on the files it names. The demo seconds come from `knowledge/DEMO-SCRIPT.md` (owning card
R39), which is the only demo route with second markers. Two full suite runs happened in this window and the tree
moved between them; section 3 says what moved.

Sizes: **S** is under 45 minutes for one worker, **M** is one work block, **L** is a card that needs a map or a
scene written from a shot list. Counted by hand from the table: 17 rows, **8 S**, 6 M, 3 L. The 8 S rows are what a
hackathon day burns down; the 3 L rows are the ones that make the demo stop.

## 1. The queue

Ordered by what it does to the demo, not by how annoying it is. Rows 1 to 9 stop the run. Rows 10 to 13 are visible
defects on a run that still plays. Rows 14 to 17 are not on the demo path and say so.

| # | Symptom, measured | What it breaks in the demo | Smallest fix | File the fix lands in | Lane | Size | Reproduce |
|---|---|---|---|---|---|---|---|
| 1 | The nine step route walk is dead: `pp_app.gml` line 721 gates it on `environment_get_variable(PP_SLICE)`, and no tool sets that variable (`grep PP_SLICE tools/run.ps1` returns nothing) | 0:16.00, the first handoff the walk would take (crawl to drive). A launch from `tools/run.ps1` opens on the title and never advances the route | Set the variable in the launcher, or walk the route by default and keep the gate as an opt out | `tools/run.ps1`, `game/scripts/pp_app/pp_app.gml` | builder | S | `grep -n "PP_SLICE" tools/run.ps1 game/scripts/pp_app/pp_app.gml` |
| 2 | `data/slice.json` names step `drive` scene `drive_to_southampton`, and that scene does not exist: 0 matches in `data/scenes/all.json`. R21 is not on the board | 0:29.00 to 0:39.03, the whole drive shot | Create R21 from `knowledge/DRIVE-SHOT-LIST.md` and land the scene block | `data/scenes/all.json` | builder (card has to be created) | L | `grep -c drive_to_southampton data/scenes/all.json` |
| 3 | Route step `arrival` names map `southampton_town_quay`; 0 matches in `data/maps/all.json`, which holds only `ship_small` and `ship_cabin` | 0:39.03, the quay, and the yard walk at 1:08.23 | Splice the ARRIVAL-MAP rows already proven on the copy | `data/maps/all.json` | job-discovery, A2 `t_db2995d7` | L | `grep -c southampton_town_quay data/maps/all.json` |
| 4 | Route step `gate` names scene `quay_gate_checkpoint`; 0 matches in `data/scenes/all.json`. No scene names the three gate rows | 0:42.03, gate page 1, and the barrier lift at 1:04.23 | Author the gate scene over the landed dialogue rows | `data/scenes/all.json` | builder, R24 `t_e063f248` | M | `grep -c quay_gate_checkpoint data/scenes/all.json` |
| 5 | The three gate rows still carry no `choices` list: `quay_gate_truth`, `quay_gate_bluff`, `quay_gate_authority` have keys `id`, `pages`, `speaker` only, and `"choices"` appears 0 times in the file | 0:54.03, the choice panel with `No pass.`, `Crew list.`, `Ask him.` | Add `choices` to the three rows, setting `gate_passed` and the flag per reply | `data/dialogue/all.json` | builder, R22 `t_5b27880e` (blocked on the flag ruling) | S | `grep -c '"choices"' data/dialogue/all.json` |
| 6 | Route step `boarding` reaches `ship_boarding`, and the office and the pass do not exist: 0 matches for `quay_dock_office` in `data/maps/all.json`, and no scene sets `has_boarding_pass` | 1:19.03 to 1:36.53, the dock office, the ledger and the boarding pass | Land the office map and the pass scene row | `data/maps/all.json`, `data/scenes/all.json` | job-discovery, A2 `t_db2995d7` | L | `grep -c quay_dock_office data/maps/all.json` |
| 7 | No scene names the fight the route names: 0 matches for `tutorial_sailors` in `data/scenes/all.json`; the only `battle` command in the 5 scenes is `percy_lore_stop` fighting `percy` | 1:53.03, the hound, and 2:10.03, the sailors | Put the two battle commands in the boarding and deck rows | `data/scenes/all.json` | builder, R24 with R30 `t_8cd9c10a` | M | `grep -c tutorial_sailors data/scenes/all.json` |
| 8 | Nothing writes a save: `"save"` appears 0 times in `pp_scene.gml` (33781 bytes), so route step `save` has no command behind it and no save file exists | 2:40.03 to 2:51.00, the ship's log | Add the `save` case to the scene command list | `game/scripts/pp_scene/pp_scene.gml` | builder, R26 `t_7098c5fe` (running) | M | `grep -c '"save"' game/scripts/pp_scene/pp_scene.gml` |
| 9 | `game_over` appears 0 times in all four GML modules (`pp_battle_director`, `pp_save`, `pp_scene`, `pp_overworld`), and route step `gameover` targets a screen that does not exist | 2:51.00 to 3:00.00, the game over and CONTINUE | Draw the screen and wire defeat to it | `game/scripts/pp_battle_director/` | builder, R27 `t_24eab5ff` | M | `grep -rc game_over game/scripts/pp_*/pp_*.gml` |
| 10 | `spr_pp_window` was repainted: its sidecar declares `fill #000000`, `grey #005800` where the pins want `#0000bc`, `#7c7c7c`. `scene_palette.py` line 522 records this exact failure mode (`the cursor's ink came back as $0F black and four pins went red`). Two pins red | 0:42.03 and every text box after it: the box reads black with a dark green inner line | Re-run `tools/art/make_pp_window.py` and keep UI sprites out of the title repaint | `game/sprites_src/title/spr_pp_window.png` and its `.json` | builder, R22 | S | `python -m pytest tests/test_nes_check.py -q` |
| 11 | Title art pins: 4 red in `test_title_bands` (8 colours in a 7 colour budget, 16x16 blocks at (80,208), (80,224), (112,208), (112,224) carrying 4 colours, `title_L1_sky` 3072 pixels off its band plan) and 2 red in `test_look` (a draw colour that is not a role, and 6 named constants including `PP_TITLE_GREY`, `PP_TITLE_DIM`) | 0:00.00 to 0:14.40, the attract screen and the logo. Visible, playable: the recorded run reached the crawl at 11.533 s | Decide the title band colours once, then repaint and repin in one card | `tools/art/title_bands.py`, `game/scripts/pp_config/pp_config.gml` | musician R37 `t_b8f9f46d` with gamedev, plus the cursor palette ruling on `t_73e40064` | M | `python -m pytest tests/test_title_bands.py tests/test_look.py -q` |
| 12 | A test that can never pass: `tests/test_make_title_world.py:123` calls `.read_text()` on the `str` that `os.path.join` returns, so the flash rule is unmeasured, not failing | 0:11.60, the lightning flash. The pin that should cover it is dead | Wrap the path in `pathlib.Path`, then judge what the pin says | `tests/test_make_title_world.py` | testing | S | `python -m pytest tests/test_make_title_world.py -q` |
| 13 | `tools/scene_palette_set.py build` does not reproduce `data/scene_palettes.json` on disk, and `tools/check_scene_palettes.py` still exits 0 on the art it declares | 0:39.03 onward, every scene's colour set | Rebuild the file from the tool, or fix the tool to match the file | `data/scene_palettes.json`, `tools/scene_palette_set.py` | builder | M | `python -m pytest tests/test_scene_palette_set.py -q` |
| 14 | Not on the demo path, but it is the proof the demo happened: `output/demo/run_001_verify.json` has `"ok": false` and fails 5 of 7 sampled frames as `not_a_terminal` | 0:00 of the recording, and the evidence pack | One clean capture with the game window raised, then rerun the verifier | `tools/capture_title.py`, `output/demo/` | assistant, R44 `t_97eec61b` | S | `grep -c '"ok": false' output/demo/run_001_verify.json` |
| 15 | Not on the demo path, blocks every card's check: the suite takes 275 s (this run) and 362 s (the run before), against the 120 s gate cap recorded on blocked card `t_73e40064` | nothing on screen; it times out the gate the fleet runs | Raise the cap to a measured number, or split the suite by lane | the gate config, then `t_73e40064` | gamedev, decision is Nayil's | S | `python -m pytest tests -q` (watch the wall clock) |
| 16 | Not on the demo path, makes every other row unreliable: the 20:28 run produced 10 errors, all `PermissionError` on `game/sprites_src/title/spr_title_sign.png`, because another lane was writing title art during the run | the suite's own verdict | Rerun the suite only when no lane holds the tree, and say in the log who else was writing | the gate runner | gamedev | S | `python -m pytest tests -q` then `grep -c PermissionError <log>` |
| 17 | Not on the demo path: the NES gate prints 24 failing rows and exits 0. All 24 are contact sheets and window captures (20 sheets, 4 captures); 0 of 134 gated rows fail, and 0 of the 15 measured slice artifacts fail the NES rules | nothing on screen; it hides 24 red rows in a green exit | Make the gate exit 1 on an advisory failure, or name the sheets out of the audit universe | `tools/nes_audit_all.py` | audit, no open card | S | `python tools/nes_audit_all.py --quiet` |

## 2. The three rows that are cheapest and hurt most

1. **Row 1, an environment variable.** The whole nine step route is written in `data/slice.json`, the walker is
   written in `pp_app.gml`, and it never runs. One line in `tools/run.ps1` turns it on.
2. **Row 5, a `choices` list.** The gate text landed and the choice is the only thing Nayil's manual check 5 has to
   look at. The data shape is already legal; R22 proved it on ten rows.
3. **Row 12, a `Path`.** One test, guaranteed red, covering the one title rule nobody has measured.

## 3. What the tree did during this card, so these numbers can be read

- 19:52, card start. `data/slice.json` carried no route at all; `knowledge/READINESS-2026-10-23.md` was right at
  19:47.
- 20:19, full suite run, 16 failed, 904 passed, 1 skipped, 362 s. Failures included `test_build_inputs`,
  `test_make_title_ui::test_cursor_is_an_outlined_arrow_that_changes_state` and two in `test_scene_palettes`.
- 20:23, the same failing files run alone: 12 failed, 116 passed. Those 3 files pass alone. **A row reproduced by a
  file scoped command and a row reproduced only by the full suite are different rows**, and rows 1 to 17 above never
  rely on the file scope alone.
- 20:26, `data/slice.json` now carries the nine step route (R24 landed during this card), `python
  tools/check_build_inputs.py` exits 0, and `PP_SLICE_ENV` is no longer used anywhere (`test_project` is green).
  Three rows of READINESS's red list closed while this card ran.
- 20:28, full suite again: 10 failed, 907 passed, 1 skipped, **10 errors** (the file lock), 275 s.
- 20:33, `data/scenes/all.json` holds 5 scenes, `data/maps/all.json` holds 2 maps, and the counts in section 1 were
  taken then.

The title art cluster moved under this card: 5 red at 20:19, 10 errors at 20:28. Rows 10 and 11 name the modules,
not a line number, for that reason.

## 4. What is blocked on a person, not on work

- `t_5b27880e` R22 DIALOGUE-V2, blocked `needs_input`: the gate and office rows need five flag names ruled
  (`gate_passed`, `gate_truth`, `gate_bluff`, `gate_authority`, plus the pass flag). Row 5 cannot be taken until
  that lands.
- `t_73e40064`, blocked: the gate cap (120 s against these 275 s) and the cursor palette rule. Rows 11 and 15.
- R21 does not exist on the board at all, so row 2 has no owner to take it, only a lane.

## 5. Check for this page

Every row carries a reproduction command that this run executed or a file count this run measured, and every row
names a lane and a size. Three sampled commands were rerun after the page was written; the section 6 log is that
rerun. The page states 8 S rows, and the table's S cells count 8. Nothing here was copied from a card that claims
done: READINESS and NES-AUDIT-SLICE were used as the map of what to check, and where this page disagrees with them
the disagreement is stated with its time (section 3).

## 6. The three sampled reruns, pasted

Rerun at 20:36, after the page was written, from the repository root.

```
python -m pytest tests/test_nes_check.py -q
2 failed, 18 passed in 8.92s
  FAILED test_the_window_json_names_the_nine_slices_in_frame_order
  FAILED test_the_3x_preview_exists_and_shows_the_window_at_three_times
```
Row 10 said two pins red. Same verdict.

```
python -m pytest tests/test_make_title_world.py -q
E   AttributeError: 'str' object has no attribute 'read_text'
tests\test_make_title_world.py:123: AttributeError
1 failed, 21 passed in 1.84s
```
Row 12 said the test can never pass on line 123. Same verdict.

```
grep -c drive_to_southampton data/scenes/all.json
0
grep -c "PP_SLICE" tools/run.ps1
0
```
Rows 1 and 2 said nothing sets the variable and the scene does not exist. Same verdict.

The other 14 rows were measured in the runs recorded in section 3 and were not rerun after the write.
