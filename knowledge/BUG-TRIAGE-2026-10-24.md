# Bug triage, 2026-10-24: every red thing from the last 24 hours, sorted by what it does to Sunday

Card BUG-TRIAGE-2026-10-24 (`t_2be3400c`), owner of this page: the audit lane. Continuation of
`knowledge\BUG-TRIAGE-2026-10-23.md` (17 rows, written 20:36 on 2026-10-22), not a rewrite. A row carried from that
page keeps its old number in the last column, so the two pages can be read together and nothing is counted twice.

Method. Every command in this page was run by this card on `<repo>`
between 01:50 and 02:18 Pacific on 2026-10-23. Nothing was taken from a card result, a lane report or an earlier page
without the file it came from and the minute it was measured. Sunday's definition of done is the eight beats named in
`<workspace>\Shared\projects\arananet\meta-hackathon\PLAN-WIN-2026-10-22.md`, quoted at line 7 of
`knowledge\HACKATHON-AUDIT-2026-10-22.md`: title, intro crawl, drive, arrival, ship boarding, first fight, save and game
over, plus the recording. "Blocks Sunday" means a row stops one of those eight beats or the recording from existing.

The tree moved during this card, hard. Section 4 carries the timestamps; a row's number is only good at its minute.

## 1. The queue

Ordered by what it does to Sunday, not by size. Rows 1 to 8 stop a beat. Rows 7 and 8 are new work with no owner,
so their verdict is "needs a card" and the card id is in the owner column. Rows 9 to 15 are red or broken and do not
stop a beat.

| # | Symptom, measured 2026-10-23 | Command that showed it | Verdict | Owner | Carried from |
|---|---|---|---|---|---|
| 1 | Route step `drive` names scene `drive_to_southampton`; 0 hits in `data/scenes/all.json`. Two `test_slice_route` checks fail on it: "the scene 'drive_to_southampton' is not in data/scenes/all.json" | `python -m pytest tests/test_slice_route.py -q` gives `8 failed, 16 passed in 9.43s`; `grep -c drive_to_southampton data/scenes/all.json` gives `0` | blocks Sunday (the 0:29.00 to 0:39.03 drive shot) | R21b `t_c27552e3` (todo) | 2 |
| 2 | Route step `arrival` names map `southampton_town_quay`; 0 hits in `data/maps/all.json`, which the 01:40 readiness page counts at 2 maps | `grep -c southampton_town_quay data/maps/all.json` gives `0`; `test_slice_route` fails `[arrival]` twice, "the map 'southampton_town_quay' is not in data/maps/all.json, so its spawn tile cannot be read" | blocks Sunday (the quay at 0:39.03 and the yard walk at 1:08.23) | ARRIVAL-MAP-2 `t_db2995d7` (todo) | 3 |
| 3 | Route step `gate` names scene `quay_gate_checkpoint`; 0 hits in `data/scenes/all.json`. The name now exists as a **dialogue** row id at `data/dialogue/all.json` line 194, so a grep for it returns a hit and a reader concludes the gate landed. It did not; the scene did not. | `grep -c quay_gate_checkpoint data/scenes/all.json` gives `0`; `grep -n quay_gate_checkpoint data/dialogue/all.json` gives `194:`; `test_slice_route` fails `[gate]` twice | blocks Sunday (gate page 1 at 0:42.03 and the barrier lift at 1:04.23) | `t_db2995d7` owns the gate scene per the readiness page; the collision itself is unowned, and the `Q:` for it was posted on `t_d5ecf73f` at 02:02 | 4 |
| 4 | The save beat still has no writer on its path: `"save"` appears 0 times in `game/scripts/pp_scene/pp_scene.gml`, no save file exists anywhere in the tree (only the fixture `build/save_slot_probe/pp_save_01.original.json`), and `data/slice.json`'s save step names no trigger, which fails `test_the_save_step_names_a_trigger_that_exists_on_its_map` | `grep -c '"save"' game/scripts/pp_scene/pp_scene.gml` gives `0`; `python -m pytest tests/test_slice_route.py -q` fails with "step save: the row names no trigger"; `find . -name "pp_save_0*.json"` finds nothing outside `build/save_slot_probe` | blocks Sunday (the ship's log at 2:40.03 to 2:51.00) | R26 `t_7098c5fe`; the missing trigger is a one line addition to `data/slice.json` and R26 did not claim it | 8 |
| 5 | No game over screen exists: `game_over` returns 0 in `pp_battle_director.gml`, `pp_save.gml`, `pp_scene.gml` and `pp_overworld.gml`, and the only file under `game/scripts` or `game/objects` that mentions it is `pp_audio.gml`, which is a cue name | `grep -rc game_over game/scripts/pp_battle_director/pp_battle_director.gml game/scripts/pp_save/pp_save.gml game/scripts/pp_scene/pp_scene.gml game/scripts/pp_overworld/pp_overworld.gml` gives 0, 0, 0, 0; `grep -rl game_over game/scripts/ game/objects/` lists `pp_audio.gml` only | blocks Sunday (the game over and CONTINUE at 2:51.00 to 3:00.00) | R27 `t_24eab5ff` | 9 |
| 6 | The first fight cannot be reached from the walk: `tutorial_sailors` appears 1 time in `data/encounters/all.json` and 1 time in `data/maps/all.json`, and 0 times in `data/scenes/all.json`, so no scene op names the encounter the route needs | `grep -c tutorial_sailors data/scenes/all.json data/maps/all.json data/encounters/all.json` gives `scenes=0 maps=1 enc=1` | blocks Sunday (the hound at 1:53.03 and the sailors at 2:10.03) | FIRST-FIGHT-WIRE `t_4a1a6662` | 7 |
| 7 | The drive room crashes on its first shot. `build/capture-drive-game.log` at 01:43 ends `PP drive: wrote pp_drive_shot_01.png ... shot 1 bigben, step 12` then `PP CRASH: Push :: Execution Error - Variable Index [0] out of range [0] - -9.pages(100571,0) \| at gml_Script_pp_drive_draw_caption line 190`. One frame of 12. `pp_drive.gml` was 29488 bytes at 00:52 for that run and is 30949 bytes at 02:02, so this crash has NOT been re-measured against the running source | `tail -12 build/capture-drive-game.log` | needs a card (stops the drive shot until a rerun shows 12 shots) | created this run: `t_7bd6eec9` | new |
| 8 | The route walk crashes in the overworld draw. `build/first_fight_game.log` at 01:13 prints `PP title: the route's next step drive cannot be taken yet` and then `PP CRASH: Variable <unknown_object>.steps(100104, -2147483648) not set before reading it. \| at gml_Script_pp_overworld_draw line 478`. A struct field is read before it is assigned, in draw code, so every frame of the walk is at risk | `tail -6 build/first_fight_game.log` | needs a card (no walk capture can complete) | created this run: `t_7bd6eec9` | new |
| 9 | The nine step walk still runs only when the launching command sets the environment variable: `PP_SLICE` has 11 references in `pp_app.gml` and 0 in `tools/run.ps1`. It does run under the capture commands, which is why rows 1 to 8 can print route diagnostics at all | `grep -c PP_SLICE tools/run.ps1` gives `0`; `grep -c PP_SLICE game/scripts/pp_app/pp_app.gml` gives `11`; `build/demo-game.log` at 01:48 carries route messages | does not block (the recording path can walk; a plain `tools/run.ps1` launch still opens on the title and never advances) | builder, no card; carried row 1 was written as "the walk is dead", and it is not dead | 1 |
| 10 | `python tools/check_build_inputs.py` exits 1: four audio streams are mirrored into the committed project but not committed, and their four sources are uncommitted. This also fails `tests/test_build_inputs.py::test_the_committed_project_resolves_every_included_file` and `tests/test_project.py::test_build_inputs_are_committed` | `python tools/check_build_inputs.py` gives `MISSING FROM COMMIT datafiles/streams/pp_05_small_ship_v2.ogg` and 7 more lines, exit 1; `python -m pytest tests/test_build_inputs.py -q` gives `1 failed, 6 passed in 23.67s` | does not block (no beat changes; it is the only red left in `test_project`) | `t_c31f9295`, created by the testing lane at 01:38 for exactly these four files | new |
| 11 | `test_look::test_draw_colour_comes_from_a_palette_role` is red: drawing code spells a colour instead of naming a palette role | `python -m pytest tests/test_look.py -q` gives `1 failed, 33 passed in 8.81s` | does not block (one pin, no picture changes) | the cursor palette rule on `t_73e40064`, blocked | 11 |
| 12 | The NES gate now fails the run: `nes_audit_all` exits 1 with 178 files measured, 33 failing, 9 gated. Yesterday the same tool exited 0 with 24 failing, so it cannot have been gating anything then either | `python tools/nes_audit_all.py --quiet` prints `nes_audit_all: FAIL, 178 file(s), 33 failing (9 gated), 0 unmeasured, exit 1` and its exit status is 1 | does not block (the 33 are contact sheets and window captures, per the 01:15 measurement on row 17 of the previous page; no beat is unplayable because of them) | audit, no card | 17 |
| 13 | The suite is 4.5 to 5 times the gate cap: 548.92 s for the full run at 01:14 to 01:23 and 625.80 s at 01:27, against a 120 s cap on blocked card `t_73e40064` | `python -m pytest tests -q` in `knowledge/READINESS-2026-10-24.md` gate 3 gives `13 failed, 1155 passed ... in 548.92s`; `tail -6 cache/full_suite2.log` gives `16 failed, 1156 passed ... in 625.80s` | does not block the picture; it times out the gate every lane runs on | `t_73e40064`, blocked, decision is Nayil's | 15 |
| 14 | Runs are still polluted by other lanes, twice in this window. `cache/full_suite.log` at 01:13 died in collection: `NameError: name 'subprocess' is not defined` at `tests/conftest.py` line 67, `no tests ran in 7.99s`, exit 3, which reads as a total failure and is an artifact. The same conftest imports `subprocess` at line 7 now and collection completes, so the artifact is closed; the condition is not | `tail -30 cache/full_suite.log`; `head -25 tests/conftest.py` shows the import at line 7 | does not block (but every number above carries its minute for this reason) | gamedev | 16 |
| 15 | The demo recording still fails its own strict verifier and still passes its loose one: `output/demo/run_001_verify.json` is `"ok": false` with `not_a_terminal` FAIL on 5 of 7 sampled frames, while `play_demo.py --check` exits 0 on the same frames | the two numbers are from `knowledge/READINESS-2026-10-24.md` section 5, measured 01:12, and were not re-run by this card | does not block a beat; it is the evidence pack for the recording | R44 `t_97eec61b`, `t_3d0fc247` | 14 |

Counted from the table: 15 rows, **6 blocks Sunday**, 2 needs a card, 7 does not block.

## 2. Closed since the 2026-10-23 page, with the command that closed it

This is the point of a daily page: what the last 24 hours fixed. Each line is a command run today.

- Row 10, `spr_pp_window`'s repaint: `python -m pytest tests/test_nes_check.py -q` gives `20 passed in 3.45s`. Was
  `2 failed, 18 passed` at 20:36 on 2026-10-22.
- Row 11, the title band pins: `python -m pytest tests/test_title_bands.py -q` gives `10 passed, 80 warnings`. Was 4
  red. `test_look` is down from 2 red to 1, and the survivor is row 11 of this page.
- Row 12, the test that could never pass: `python -m pytest tests/test_make_title_world.py -q` gives `22 passed in
  3.68s`. Was `1 failed` on `AttributeError: 'str' object has no attribute 'read_text'`.
- Row 13, the palette set: `python -m pytest tests/test_scene_palette_set.py -q` gives `11 passed in 1.60s`.
- Row 5, the gate choice panel: `"choices"` appears 1 time in `data/dialogue/all.json`, on the row `quay_gate_choice`
  at line 224, and its three entries `goto` `quay_gate_truth`, `quay_gate_bluff` and `quay_gate_authority` (lines
  240, 245, 250), which are the three reply rows. Command: `grep -n '"choices"' data/dialogue/all.json` gives `236:`
  and `awk 'NR>=195 && NR<=236 && /"id"/'` gives `"id": "quay_gate_choice"`. Was `0` matches at 20:33 on 2026-10-22.
  The beat is in the data; row 3 of this page is why it still cannot be reached.
- The clean room gate: `python tools/check_cleanroom.py` exits 0 at 40 GML modules with 1 awaiting review, where the
  01:02 run in `knowledge/READINESS-2026-10-24.md` exited 1 on the four `pp_drive` files.
- `python tools/check_data.py` exits 0 (measured again, not inherited).

## 3. The three reds that were green four minutes later

At 02:05 `python -m pytest tests/test_project.py -q` gave `4 failed, 19 passed`: `test_project_graph_matches_disk`,
`test_yyp_lists_every_script_object_and_room`, `test_generated_project_files_are_current` and
`test_build_inputs_are_committed`. At 02:10 the same command gave `1 failed, 22 passed in 18.31s`, the same one that
row 10 of this page carries. Three reds closed inside five minutes while another lane was writing the tree, which is
row 14's condition reproducing inside this card. They are recorded here and not as rows: they are closed, and a row
that is already green is not a defect anybody can take.

## 4. What the tree did during this card

- 01:50, card start. `cache/full_suite.log` (01:13) had already died in collection on the conftest `NameError`.
- 01:52, `cache/full_suite2.log` (01:27) is the last full suite on this PC: `16 failed, 1156 passed, 625.80s`.
- 02:02, `game/scripts/pp_drive/pp_drive.gml` rewritten, 29488 to 30949 bytes. The 01:43 drive crash predates it by
  19 minutes and is therefore unverified against the running source, which is why row 7 is carded for a rerun and not
  called fixed.
- 02:05 to 02:10, `test_project` went from 4 red to 1 red, section 3.
- 02:12, the four gates re-run by this card: `check_data` exit 0, `check_cleanroom` exit 0, `check_build_inputs` exit
  1, `nes_audit_all` exit 1.
- 02:15, the nine separate file scoped runs in section 5.

## 5. The file scoped runs, pasted as they came back

Run from the repository root between 02:00 and 02:15, each as `python -m pytest tests/<file>.py -q --tb=no`:

    test_slice_route.py        8 failed, 16 passed in 9.43s
    test_look.py               1 failed, 33 passed in 8.81s
    test_title_path.py         13 passed in 0.62s
    test_nes_check.py          20 passed in 3.45s
    test_make_title_world.py   22 passed in 3.68s
    test_scene_palette_set.py  11 passed in 1.60s
    test_title_bands.py        10 passed, 80 warnings in 6.95s
    test_project.py            1 failed, 22 passed in 18.31s   (at 02:10; 4 failed, 19 passed at 02:05)
    test_build_inputs.py       1 failed, 6 passed in 23.67s

File scoped and full suite are different scopes and this page does not mix them: row 13's numbers are full suite,
section 5 is file scoped, and row 14 is why the difference matters.

## 6. Check for this page

Every row carries the file or log it comes from and the command this card ran, and one of the three verdicts. The two
"needs a card" rows name `t_7bd6eec9`, created by this card from them. No item appears twice: the six closed rows of
the 2026-10-23 page are in section 2 with the command that closed them, not in the table, and the three transient reds
are in section 3, not in the table. The counts in section 1 were counted from the rows: 15 rows, 6 blocks Sunday, 2
needs a card, 7 does not block. What this card did not do: it did not rerun a capture to confirm or clear the two
crashes (row 7 and row 8, now `t_7bd6eec9`), and it did not rerun the full suite, so row 13's wall clock is the 01:27
number and not a new one.
