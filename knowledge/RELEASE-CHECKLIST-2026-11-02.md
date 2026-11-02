# RELEASE CHECKLIST, 2026-11-02: one measured row per route step

Card `t_e4276b12`, lane audit. Tree measured: repo HEAD `de11390b` (2026-11-02 15:09 PST), working tree DIRTY
(the music, party and sprite lanes were writing while this was read). The game was not run and no game file was
changed: every line below comes from a file this run opened, a command this run ran, or a frame this run looked at.

## What the four verdicts mean

- `PASS`: a log line, a frame or a test exists, the path is named, and it shows this step working in the real game.
- `FAIL`: an artifact exists and shows the step NOT working. A source-level cause is named beside it.
- `TEST ONLY`: a committed test pins the code, and no log line or frame from the game was ever produced. The code
  is pinned, the shot is unproven.
- `NO EVIDENCE`: nothing in this project shows it. The words are used deliberately.

## The four things this checklist found

1. **Six rows fail on one code path.** A scene `say` stores its box on the scene
   (`game/scripts/pp_scene/pp_scene.gml:198`, `_sc.dialogue = pp_dialogue_open(_cmd.id)`), the only draw call reads
   the world (`game/scripts/pp_overworld/pp_overworld.gml:944` to `:945`), and the scene overlay draws only the talk
   box (`game/scripts/pp_scene/pp_scene.gml:597` to `:603`, `pp_talk_scene_draw(_sc.talk)`). Nothing draws
   `_sc.dialogue`. The drive, the gate, the dock office, the boarding, the ship's log page and the end card all open
   with a `say`, so all six show a picture with no text. This was measured with frames on 2026-10-27
   (`knowledge/QA-PLAYTHROUGH-2026-10-26.md`, findings 1 and 2); I re-ran the md5 equality and looked at two of the
   frames myself today, and the source shape is unchanged at HEAD.
2. **The take the card names has no artifact.** `data/demo/run_002.json` is the 253.5 s plan (129 events, end step
   15,210) and the tests pin it, but there is no 253.5 s video on disk, and the only verifier scores a 182.5 s take
   against a script that no longer exists. So the single take this release rests on has never been scored.
3. **Game over and CONTINUE cannot be reached by the route at all.** The `deck_collapse` encounter row carries
   `forced_defeat`, the director reads it, and no map carries a trigger naming that row: `ship_cabin` has three
   triggers, a map at (1,7), a scene at (7,3) and a scene at (7,2). `tests/test_demo_shots.py` says both triggers were
   removed on Nayil's order. The step is in `data/slice.json` and in no take.
4. **Music and the three member battle party have no log and no frame.** The recorded takes are silent by
   construction, and no log line anywhere names a party member.

## The rows

| # | step | what the data says happens | evidence in the real game, or NO EVIDENCE | verdict | owner of the gap |
|---|---|---|---|---|---|
| 1 | title | `data/slice.json` step `title` is kind `title`, room `rm_pp_title`; `data/demo/run_002.json` event `r001` expects `PP title: room rm_pp_title live` | live multi line in `build/demo-game.log:37` (`PP title: room rm_pp_title live, screen owned by obj_pp_title`, 2026-10-27 take); frame `output/demo/title_attract.png` | PASS | none |
| 2 | crawl | run_002 event `r005` expects `PP title: intro started`; 24 stars, 16 crawl lines | live line in `build/demo-game.log:86` (`PP title: intro started, pan 180 steps, 24 stars, 16 crawl lines`); frame `output/qa_playthrough_20261026/frames_oct27/f_0030.png` | PASS | none |
| 3 | drive | scene `drive_to_southampton`, 64 commands (music PP-02, fade, camera, waits, `say drive_sign_55`); run_002 holds cancel at `r008`, expects `PP scene: drive_to_southampton skipped` at `r009` | the room draws and the skip fires (harness trace `build/_run002_attempt1.log`, marker seen at 28.6 s), and the first `say` is never drawn: frames f_0069 to f_0129 are one image, md5 `9c0dae9779a6e4c87fd3eb76285ee19f`, and I looked at `output/qa_playthrough_20261026/frames_oct27/f_0129.png` myself: it shows only the `hold X to skip` line, no box; cause `game/scripts/pp_scene/pp_scene.gml:198` | FAIL | gamedev (pp_scene draw path) |
| 4 | quay arrival | `data/slice.json` step `arrival` is the map `southampton_town_quay`; run_002 `r010` loads it at spawn 24,1 | live line `build/qa-grab-game.log:165` (`PP route: step drive handed to step arrival (arrival at Town Quay)`); frame `output/qa_playthrough_20261026/frames_oct27_skip/f_0080.png`, which I looked at: a drawn top down quay with two sprites and no box | PASS | none (the same frame then holds, because the gate's `say` never draws) |
| 5 | gate | trigger `quay_gate_checkpoint` at (8,10) in `data/maps/all.json`; scene is music, `say`, `say`, then three branches; run_002 sends 13 confirms and a Down to `Crew list.` | no log line from any take; the two `say` pages cannot draw (`game/scripts/pp_scene/pp_scene.gml:198` against `game/scripts/pp_overworld/pp_overworld.gml:945`); named as finding 2 in `knowledge/QA-PLAYTHROUGH-2026-10-26.md` | FAIL | gamedev |
| 6 | dock office | map `quay_dock_office` at (30,25); scene `quay_dock_office_play` is move, face, `say`, `talk`, `say`; run_002 types a five letter name and sends six confirms on the pass line | no log line from any take; the `talk` box does draw (`game/scripts/pp_scene/pp_scene.gml:602`), the two `say` pages do not; finding 2 in `knowledge/QA-PLAYTHROUGH-2026-10-26.md` | FAIL | gamedev |
| 7 | boarding | scene `ship_boarding` is music, shake, wait, camera, wait, `say`; run_002 `r040` to `r043` | no log line from any take; the `say` page cannot draw: `game/scripts/pp_scene/pp_scene.gml:198` against `game/scripts/pp_overworld/pp_overworld.gml:945`; finding 2 in `knowledge/QA-PLAYTHROUGH-2026-10-26.md` names this scene by id | FAIL | gamedev |
| 8 | ship deck fight | battle trigger `tutorial_sailors` at (4,7) in `data/maps/all.json`; run_002 `r044` to `r058` talks three times, SPAREs | live fight in `output/battle_proof_2026-11-02/game_tutorial_sailors.log` (`PP: battle start tutorial_sailors on ship_small 2,7`, `PP: fight result spare, turn 4`, `state=back_in_world`); frames `output/battle_proof_2026-11-02/frames/pp_fight_tutorial_sailors_spare_menu.png` and its three siblings | PASS | none (that run held the route with `PP_ROUTE_HOLD` and fought at the tour's spawn 2,7) |
| 9 | Percy office fight | scene `percy_lore_stop` at (7,3) in `ship_cabin` is `say`, `battle`, branches; run_002 `c03` to `p14` | live fight in `output/battle_proof_2026-11-02/game_percy.log` (`PP: battle start percy on ship_cabin 0,0`, `PP: fight result spare, turn 4`, `state=back_in_world`); frames `output/battle_proof_2026-11-02/frames/pp_fight_percy_spare_ending.png` and its three siblings | PASS | none (the tour's Percy stands at 0,0, the route reaches him from the lore stop) |
| 10 | ending | scenes `percy_aftermath` and `percy_aftermath_kill` say `demo_end_card`, whose page is `* END OF THE DEMO.` (`data/dialogue/all.json:728` to `:731`); run_002 `p90` to `p93` | no log line and no frame of the end card. The only ending frames are the fight result panel (`output/battle_proof_2026-11-02/frames/pp_fight_percy_spare_ending.png`), which is the battle, not the card; the card is a scene `say`, so it cannot draw | FAIL | gamedev |
| 11 | save | `data/slice.json` step `save`, trigger `deck_save`; save trigger at (3,2) in `data/maps/all.json` `ship_small`; scene `ship_log` is face, move, face, camera, `say` | live line `build/save_capture_run1.log:66` (`PP: ship's log, deck_save, saved on ship_small 3,2`, 2026-10-24 build); the trigger is unchanged in today's data; `tests/test_save_gameover.py` autosave pins pass (81 passed with three other files in 5.41 s today) | PASS | none (the page the log opens is a `say` and cannot draw; the write itself is proven) |
| 12 | game over | `data/slice.json` step `gameover` is a branch to `title`; encounter `deck_collapse` carries `forced_defeat`, read at `game/scripts/pp_battle_director/pp_battle_director.gml:339` to `:345` | NO log line and NO frame: `PP: fight result defeat` and `PP: game over frame` appear in knowledge documents only, never in a log under `build/` or `output/`; the hook is source pinned by `tests/test_save_gameover.py` and `knowledge/DEMO-INTEGRATION-2026-11-01.md:123` to `:128` says the game has never executed it; no map trigger names `deck_collapse`, so the route cannot reach it | TEST ONLY | manager and builder (the beat is in the slice and in no take; the map trigger is gone by Nayil's order) |
| 13 | continue | `data/slice.json` gameover branch back to `title`; `pp_battle_continue` applies the save; run_002 has no continue event | NO log line and NO frame (`PP: game over, CONTINUE restored the last save` appears in knowledge documents only); pinned at source by `tests/test_save_gameover.py:699` and `tests/test_save_gameover.py:766` | TEST ONLY | manager and builder, same as row 12 |
| 14 | music | every room and fight asks a cue (PP-02 drive, PP-03 quay, PP-05 ship, PP-06 office); run_002 `r007` and `r010` expect `PP: music PP-0x requested` | NO EVIDENCE that a player hears it. The takes are silent by construction: `build/_run002_attempt1.log:9` reads `system audio: no loopback device, the video is recorded silent` and `:10` reads `the game starts with PP_MUTE=1, so nothing plays`; `output/demo/run_002_verify.json` line 2 says the audio is a `rendered stand-in from run_002_audio.m4a, not the game's live output`; `knowledge/DEMO-AUDIO-2026-10-27.md` section 2 finds no usable loopback on this host; the only live cue lines are from muted tour runs (`output/battle_proof_2026-11-02/game_percy.log`, `playing PP-05 (started), stream yes`, with master gain 0). Static coverage passes (`knowledge/MUSIC-COVERAGE-2026-11-02.md`) | NO EVIDENCE | MUSIC-REAL, and Nayil for a virtual cable install |
| 15 | three member battle party | `data/ui_layouts.json:133` to `:160` now carries three battle slots, ZANDER as ZEUS, KONRAD as KRONOS, HADRIAN as HADES; `data/characters/party.json` still holds one member, the hero Aeson | NO EVIDENCE: no log line names a party member, and the three tour logs carry only `party_hp=20`. Renders exist (`output/battle_party_2026-11-02/after/percy_office.png`) but a render tool composited them, not the game, and the built game `output/PrimordialParadox/PrimordialParadox.win` is dated 2026-11-02 14:36:30, before the 14:51 layout edit, so the shipped build cannot carry the three member panel | NO EVIDENCE | BATTLE-PARTY-3 |

Rows: 15. PASS 6, FAIL 5, TEST ONLY 2, NO EVIDENCE 2.

## The take itself, and why six rows read as they do

The card calls `data/demo/run_002.json` the 253.5 s take. It is a plan, not a run: 129 events, end step 15,210,
modified 2026-11-01 17:02, pinned by `tests/test_demo_shots.py` (which passes, 84 passed across that file and three
others in 9.04 s today). Three artifacts a sign off would want do not match it:

- **No video.** `find . -name "run_002*.mp4"` returns one file, `output/demo/backup-2026-10-26/run_002.mp4`. There is
  no rendered 253.5 s take.
- **No verifier for this plan.** `output/demo/run_002_verify.json` (34,839 B) reports `duration_s 182.5` and
  `checked_at 2026-10-27T07:46:28`, and it scores ten beats of the 180 s script, including `S6 defeat` and
  `S6 hound fight`, neither of which the current file contains. It reports 7 of 10 beats `found: false`.
- **That verifier must not be read as a game failure.** Its own needle for the gate is
  `PP route: step arrival handed to step gate`, and `data/demo/run_002.json` event `r013` records that this build
  never prints that line, because a map step does not hand on. A polluted check is not a measurement, so this file
  cites it as evidence that no clean measurement exists, not as evidence about the gate.

The consequence for sign off: the 253.5 s take has never been recorded and never been scored, so no row can be
closed on "the take shows it". Six rows are proven by a log or frame from another run, five are broken by frames and
source, two are pinned only at source, and two have nothing.

## Check

The check this card names, run after the file was written. It reads this table, refuses a row without a verdict,
refuses a `PASS`, `FAIL` or `TEST ONLY` row whose evidence paths do not exist, and prints the counts:

```
$ python tools/check_release_checklist.py knowledge/RELEASE-CHECKLIST-2026-11-02.md
```

Its output is pasted in the card comment, with the row counts by verdict.

## Commands run in this session, and what they returned

- `git log --oneline -1` in the repo: `de11390b t_74fee92b MUSIC-COVERAGE: every room and every fight resolves to an
  OGG that ships, loops and is above -40 dB`; `date` `2026-11-02 15:09:01 PST`.
- `md5sum output/qa_playthrough_20261026/frames_oct27/f_0069.png f_0100.png f_0129.png`: all three
  `9c0dae9779a6e4c87fd3eb76285ee19f`; `f_0080.png` and `f_0128.png` in `frames_oct27_skip`: both
  `f7677ff95f7f4668a54752e3e2ddf963`.
- `grep -rn "_sc.dialogue" game/scripts/`, `grep -rn "pp_dialogue_draw(" game/scripts/`: one write
  (`pp_scene.gml:198`), one draw (`pp_overworld.gml:945`), and the overload draws only `_sc.talk`.
- `./.venv/Scripts/python.exe -m pytest tests/test_save_gameover.py tests/test_slice_route.py
  tests/test_music_coverage.py tests/test_battle_draw.py -q`: `81 passed in 5.41s`.
- `./.venv/Scripts/python.exe -m pytest tests/test_demo_shots.py tests/test_demo_paths.py
  tests/test_route_continuity.py tests/test_slice_story.py -q`: `84 passed in 9.04s`.
- `grep -rlF "PP: game over"` over `build/`, `output/`, `knowledge/`, `data/`: two knowledge documents, no log.
- `python` over `data/maps/all.json`: `ship_cabin` triggers are map (1,7), scene (7,3), scene (7,2); no battle
  trigger, so `deck_collapse` is unreachable.

## NOT verified here, and it must be said

- I did not run the game (the card forbids it), so no row rests on my own take.
- The frames that carry rows 3 and 5 are from the 2026-10-27 build. I re-checked that the source shape is unchanged
  today, and I looked at two of the frames, but I did not record a fresh frame of the gate or the office. A fresh
  frame of the gate and the office is the cheapest way to move rows 5 and 6 from FAIL to settled.
- I did not open the party or music artifacts' pixels; row 15 rests on the absence of any log line naming a member
  and on the build time, not on a frame.
