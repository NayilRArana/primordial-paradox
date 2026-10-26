# HACKATHON-AUDIT 2026-10-22: primordial-paradox against the hackathon slice

Auditor: audit profile, task t_df448053 (run 2; run 1 timed out at 2713 s).
Every number below was produced by this run on this PC between 18:41 and 19:24 PDT, or is cited to the file that holds it.
Worker reports, DEVLOG claims and earlier logs were not accepted as evidence. Where I did not measure, the line says unverified.

Read first, as the card ordered: `<workspace>\Shared\projects\arananet\meta-hackathon\PLAN-WIN-2026-10-22.md` (definition of done: title, intro crawl, drive, arrival, ship boarding, first fight, game over and save by Sunday) and `HACKATHON-BRIEF.md` (judging: creativity, technical ambition, whether it works).

## 0. What this run measured, in one place

| Measurement | Command or source | Result |
| --- | --- | --- |
| Build from current source | `python tools/integration_build.py` (my run, log `build/audit-hack-build.log`) | exit 0, "BUILD PASS: Igor compiled the project and launched the game"; Igor complete at line 73 of `build/last-igor.log` |
| Rebuilt game data | `output/PrimordialParadox/PrimordialParadox.win` | 311372 bytes, written 18:51 by my build; runner `PrimordialParadox.exe` 7941704 bytes, sha256 5cbf3f4a9b1f4d8b6abd2dd3c451de7e2f561dac02d122176a28a5fa7b3e2375 |
| Build actually ran the game | `build/last-igor.log` tail | live lines "PP audio: thunder_soft played, instance 400037", "focus lost, music paused", "focus back, music resumed" |
| Window closed after my build | `tasklist` after WM_CLOSE | Igor.exe and the game gone, nothing left running |
| Test suite on Pine, shards 0 and 1 | `pine_offload.py --shards 3 --name audit-hack` | 241 passed 11 failed, and 305 passed 10 failed; shard 2 died on a transport error, not a verdict |
| Test suite on Pine, shard 2 rerun | `pine_offload.py --shards 1 --name audit-hack-s2 --files ...` | 287 passed 12 failed (`pine/data/results/offload-audit-hack-s2-0.json`) |
| Suite total this run | the three result files | 833 passed, 33 failed, 33 distinct failing tests; 2 git tests not offloaded (`tests/test_build_inputs.py`, `tests/test_test_inputs.py`) |
| Fresh title capture | `python tools/capture_title.py` (my run, 19:13) | exit 0, `output/title_run_1.png` 784x759, viewport [8,31,768,720] score 1.000, "the game closed on request (exit code 0)" |
| Live title frame, NES legality | Pillow over `output/title_run_1.png` crop 768x720 | 28 distinct RGB, 8 of 61440 3x blocks not uniform (seam or scaling artefact) |
| Committed title frame | Pillow over `output/nes_title_frame.png` | 256x240, 11 distinct RGB |
| Demo video | `ffprobe output/demo/run_001.mp4` | 768x720, h264 60 fps, 4410 frames, 73.5 s, aac audio |
| Demo video verdict | `output/demo/run_001_verify.json` written 18:13 | `ok: false`; `not_a_terminal` FAIL: 5 of 7 sampled frames are not the game (score 0.0 at t=1.5, 13.2, 48.5, 61.7, 69.8) |
| Preview PNGs | Pillow, `output/` | ui_battle_preview 768x720 5 RGB, ui_dialogue_preview 5, title_ui_preview 1152x784 9, chars_contact 736x2768 22, bg_battle_preview 1560x696 16, crawl_mid 768x720 4 |
| Code size | `wc -l` | 23 GML script folders, 6924 lines of GML; objects and rooms are thin (obj_pp_game Step 4 lines, Create 56, obj_pp_title Draw 22) |
| Rooms that exist | `ls game/rooms` | exactly three: `rm_pp_boot`, `rm_pp_title`, `rm_pp_ship` |

No key was read or printed. Only paths, sizes, digests and test output appear here.

## 1. Maturity table (0 nothing, 1 spec only, 2 code or data but unproven in the game, 3 proven in the running game with a capture or a test, 4 polished)

| # | Subsystem | Score | Evidence (file, test, capture, commit) |
| --- | --- | --- | --- |
| 1 | Title screen | 3 | `game/scripts/pp_title/pp_title.gml` (1019 lines, commit 04e94db); my capture `output/title_run_1.png` at 19:13, exit 0; `output/nes_title_frame.png` 11 colours. Not 4: card t_a1170172 says the composited frame carries 2 blended colours and 25 attribute-area violations, and my live crop shows 28 distinct RGB |
| 2 | Intro crawl | 3 | `data/intro_text.json`, `data/intro_stars.json`, `output/crawl_mid.png` 768x720 4 colours, `output/crawl_end.png`; `build/demo-game.log` line "PP title: intro finished, starting the run in rm_pp_ship" |
| 3 | Drive cutscene | 1 | `knowledge/DRIVE-SHOT-LIST.md` and `tools/drive_v2.py` exist (commit history in DEVLOG), but there is no drive room (`ls game/rooms` = 3 rooms) and no drive scene in `data/scenes/all.json` (its scenes are Ship boarding, Cabin: Percy, Cabin: the interruption); unverified in game |
| 4 | Overworld movement | 3 | `pp_overworld.gml` 601 lines (commit e29612f); `build/demo-game.log` footstep played lines and `data/demo/run_001_verify.json` records 8 footsteps in the recorded run |
| 5 | Maps and doors | 2 | `pp_map.gml` 167 lines, `data/maps/all.json` plus 5 sample maps, `tools/check_data.py` passes on Pine this run; but the only playable room is `rm_pp_ship`, so doors beyond it are data, not a proven traversal |
| 6 | Dialogue and talk system | 3 | `pp_dialogue.gml` 389 lines (commit ab4b80a), `pp_text.gml` 211, `data/dialogue/all.json`, `data/talk_cards.json`; text_blip audio lines in `build/demo-game.log`. Not 4: card t_5b27880e (DIALOGUE-V2, pages and a 3-option choice) is still running |
| 7 | Battle and the talk fight | 2 | `pp_battle_director.gml` 514, `pp_battle_commands.gml` 71, `pp_battle_text.gml` 60, `pp_dodge_arena.gml` 250, `tests/test_first_fight.py`; no capture or log line from this run shows a live fight, so unproven in the running game |
| 8 | Enemies | 2 | `data/enemies/all.json`, `data/enemies/roster.json`, `output/enemies_report.json`, `output/enemies_preview_3x.png` 464x772 9 colours, `output/enemies_battle_mask.png`; no live encounter captured |
| 9 | Party and stats | 2 | `data/characters/party.json` only; no test named for stats, no capture |
| 10 | Save and load | 2 | `pp_save.gml` 959 lines (commit 6780273), `tools/_save_load_probe.py`, `tests/test_save.py` passes on Pine this run; no capture of the save UI or of a load after restart |
| 11 | Ledger | 2 | `pp_ledger.gml` 194 lines (commit 9e6e1ea), `tests/test_ledger.py` passes on Pine; no capture |
| 12 | Audio bus and cues | 3 | `pp_audio.gml` 544 lines (commit 5e30093); live evidence "PP audio: focus lost, music paused (cue and theme) and every effect stopped" from my build in `build/last-igor.log` |
| 13 | Music per scene | 2 | Title theme proven live (`PP audio: title_theme back to full after 6 dB`, `build/demo-game.log`); per-scene coverage is a card (t_3d318ae9 R36) not a measurement; unverified for every room but the title |
| 14 | SFX | 3 | `data/sfx`, `game/datafiles/sfx`, `tests/test_sfx.py` passes; live cue lines footstep, text_blip_a, thunder_soft, door_hatch in `build/demo-game.log` and `build/last-igor.log` |
| 15 | UI windows and menus | 2 | `data/ui_layouts.json`, `output/ui_battle_preview.png` 5 RGB, `ui_dialogue_preview.png` 5, `ui_menu_preview.png`, `ui_*_nes_report.json`; three tests in `tests/test_nes_check.py` fail on the window json and the 3x preview, so the windows are previews, not proof |
| 16 | Art pipeline (concept to sprite, palette-first) | 2 | `tools/art/*`, `tools/quantize_concept.py`, `data/palette_recipes.json`, `data/sprite_recipes.json`, `tools/check_palette_recipes.py`; but 5 tests in `tests/test_make_title_ui.py`, 2 in `tests/test_title_art_v2.py`, 2 in `tests/test_look.py` and 1 in `tests/test_scene_palette_set.py` fail on Pine this run, so the pipeline does not reproduce its own committed output |
| 17 | Sprites per character | 2 | `game/art/spr_*.png` (13 files), `output/chars_contact.png` 736x2768 22 colours, `game/sprites_src`; card t_858c2908 (car, Ronan, Theo, storm cloud) is blocked, so the cast is incomplete |
| 18 | Backgrounds per scene | 3 | four strips `output/bg_battle_*_frame.png` (corridor, deck_night, quay_dusk, wardroom), `output/bg_battle_report.json`, `bg_battle_preview.png` 16 RGB; card t_59bfc884 (R48 wiring at the spec 07 origin) is todo, so drawn but not wired |
| 19 | Build and packaging | 3 | my build exit 0 with "BUILD PASS"; `output/PrimordialParadox/` holds exe, .win, yydebug and the data mirrors; not 4: no install step, no zipped artifact, and the exe is the Oct 20 runner while the data is rebuilt |
| 20 | Tests and gates | 2 | 833 passed, 33 failed on Pine this run; the 33 split into 9 `test_play_demo`, 5 `test_capture_title`, 5 `test_make_title_ui`, 4 `test_project`, 3 `test_nes_check`, 2 `test_look`, 2 `test_title_art_v2`, 1 each `test_intro`, `test_make_env_ship`, `test_make_title_world`, `test_scene_palette_set`. Several are Windows-only by design; the run does not separate them, so the gate is not green and not yet classified |
| 21 | Capture and demo tooling | 2 | `tools/capture_title.py` passes end to end in my run; `tools/play_demo.py` produced a 73.5 s 60 fps 768x720 mp4 but its own verifier returns `ok: false`, 5 of 7 sampled frames not the game (`output/demo/run_001_verify.json`), and 9 of its own tests fail |
| 22 | Docs and repo hygiene (README, licence, keys) | 1 | no `README.md` and no licence file at the project root (`ls | grep -iE 'readme|licen'` returns nothing); `knowledge/LICENSES.md` (77 lines), `knowledge/PROVENANCE.md`, `knowledge/KEY-HYGIENE-2026-10-22.md` exist; card t_8d7bad5f (R45 README-SLICE) is ready, so the front door a judge reads does not exist yet |

Mean over 22 rows: 2.2. Nothing scores 4, and only eight rows score 3.

## 2. Blockers to a playable end to end slice (title to first fight), in order

1. The route is not data. `data/slice.json` names map `ship_small`, spawn `start`, scene `ship_boarding`, encounter `tutorial_sailors`, but the build has three rooms and no drive room, so title, crawl, drive, arrival and boarding are not one continuous run (`ls game/rooms`, `data/scenes/all.json`). Card t_e063f248 (R24 SLICE-ROUTE) covers this.
2. The first fight has never been seen by this audit in the running game. No log line or capture from my build reaches a battle; only `data/scenes/all.json` rows and `tests/test_first_fight.py` claim it. Nothing here is a verdict, it is an absence of proof.
3. The demo recorder does not currently record the game: `output/demo/run_001_verify.json` says `ok: false`, 5 of 7 frames not the game. A video pipeline that reports failure is better than one that lies, but it is not a demo yet.
4. The art pipeline does not reproduce its own committed output: 11 failing art tests (`test_make_title_ui` 5, `test_title_art_v2` 2, `test_look` 2, `test_scene_palette_set` 1, `test_make_title_world` 1), so a rebuild today can change pixels nobody chose.
5. The font is contested on two fronts at once: `test_make_title_ui.py::test_font_matches_the_contract` and `test_nes_check.py::test_the_committed_font_passes_as_a_sprite` both fail, so every line of dialogue the slice prints sits on an unproven font.
6. Save and load are green in tests and invisible in the game: `pp_save.gml` 959 lines, `tests/test_save.py` passes, no capture of a save or of a CONTINUE after restart. Card t_7098c5fe (R26 SAVE-SLICE) and t_136b5d08 (R25 TITLE-PATH) are open.
7. Game over does not exist as a path: card t_24eab5ff (R27 GAME-OVER) is todo, and nothing in `game/scripts` or the rooms shows a defeat screen.
8. The project has no README and no licence at its root, which is the first thing the judges and any prior-work decision touch.

## 3. The ten riskiest items for the demo

1. The demo video fails its own not-a-terminal check (5 of 7 frames). Highest risk: the artifact the judges watch is unverified.
2. No live capture of the first fight. The judged claim "a talk-your-way-through fight" has no evidence in this audit.
3. No drive cutscene in the build (3 rooms, no drive scene), while the pitch and PLAN-WIN both name the night drive.
4. 33 failing tests, unclassified between real regressions and Windows-only artefacts. A gate nobody can read is a gate that stops mattering.
5. Art pipeline not reproducible (11 art test failures), so every rebuild risks silent pixel drift before Nov 4.
6. Font contract failures: text is the talk fight's whole surface.
7. Title frame legality: 2 blended colours and 25 attribute-area violations per card t_a1170172, and my live crop measures 28 distinct RGB in the 3x viewport.
8. Prior-work question unresolved until the rules land (HACKATHON-BRIEF section 2 marks it UNKNOWN); no README and no timestamped build log at the root to answer it.
9. Save and game over unproven in game, which is the "whether it works" floor for a three minute slice.
10. Memory and runtime pressure: shard 2 of my first Pine run died on a transport error, and the prior run of this card timed out at 2713 s. Long verification runs are themselves a demo risk in the final week.

## 4. Coverage against open cards (116 open on nayil-ops, read from `kanban.db` read-only)

Covered, with the card id:

- Slice route: t_e063f248 (R24). Arrival map: t_c024f8bc blocked, t_db2995d7 replacement, t_3a52845d test. Ship deck and log terminal: t_a3fa132a.
- Title path and menu: t_90c0cc4a (blocked), t_136b5d08. Title art legality: t_a1170172. Title theme: t_b8f9f46d.
- Intro crawl: t_d2ec48a1 (blocked).
- Dialogue: t_5b27880e, t_45ef4217, t_23377d65, t_be10336d. Font: t_41c97c88. Talk bake: t_f943951a, t_8cd9c10a, t_cd908367.
- Battle background: t_59bfc884. Percy phases: t_2eb874af (blocked). Battle text: t_155e22e2 (done).
- Save and game over: t_7098c5fe, t_00998131, t_24eab5ff. Ledger: no open card; LEDGER-2 landed as commit 9e6e1ea.
- Audio cues: t_3d318ae9, t_54ecd177, t_6a70f6e8. SFX proof: t_0cac113b.
- Art: t_858c2908 (blocked), t_aa552437, t_7d1380f9. NES audit: t_c56b82b3, t_d8f13f33.
- Demo and capture: t_c0f33e5d (R39 script), t_3a932e73 (Gemini eye), t_7b2f6aae (kit). None of them owns the current not-a-terminal failure.
- README: t_8d7bad5f. Tests and gate: t_dacb50c7, t_5c018549 (R51 triage), t_72c3bc02.
- Audit readiness: t_4d0c2ef5 (R40), t_c56b82b3 (R41).

Not covered by any open card. Proposed cards, listed only, none created:

1. DRIVE-SCENE: build `rm_pp_drive` and a `data/scenes` drive row, or state in `PLAN.md` that the drive is cut from the slice. Owner gamedev (it is their spec).
2. BATTLE-PROOF: one scripted capture and log trace that reaches `tutorial_sailors`, plays the talk fight to an ending, and names the file. Owner testing.
3. PARTY-STATS: `data/characters/party.json` against the stat model, with a test that a level up changes a displayed number. Owner builder.
4. LEDGER-PROOF: a captured run whose ledger rows are read back and counted. Owner testing.
5. UI-WINDOW-PROOF: the three failing `test_nes_check` window assertions and the 3x preview, fixed or restated. Owner builder.
6. FONT-SPRITE-FIX: the font contract in `test_make_title_ui` and the sprite verdict in `test_nes_check` reconciled against `knowledge/ART-BIBLE.md`. Owner builder.
7. DEMO-CAPTURE-FIX: make `play_demo.py` record the game (5 of 7 frames currently not the game) and hold `ok: true` before any video is shown. Owner testing.
8. LICENCE-ROOT: a root `LICENCE` file and a one screen root `README` that states what is prior work (pairs with R45). Owner assistant.
9. TITLE-FRAME-LEGAL: close the 2 blended colours and 25 attribute violations, or record why they are accepted, with a fresh `output/nes_title_frame.png`. Owner builder (card t_a1170172 covers the finding, not the fix).
10. AUDIT-GATE-CLASSIFY: a written split of the 33 failures into Windows-only and real, so the gate can go green honestly. Owner audit.

## 5. Verdict

The scaffold is real and it builds: my build passed, the game launched, played audio and closed cleanly, the title capture passed at 19:13, and 833 tests pass on Pine. The slice is not playable end to end: no drive, no captured fight, no game over, no README, and the demo recorder currently returns `ok: false`.

Score for the card's question: the project is at maturity 3 for title, crawl, overworld, dialogue, audio and sfx; 2 for most systems behind them; 1 for the drive and the docs. The gap to Sunday is concentrated in four places: the route, the fight, the recorder, and the art reproducibility.
