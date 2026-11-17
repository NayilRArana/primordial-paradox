# AUTO-MUSIC-NEXT sweep, 2026-11-17 (card t_03b3d044, musician lane)

## 1. What was measured

`tools/hook_score.py` (grammar `knowledge/MUSIC-HOOK-GRAMMAR.md`) was run in process over every `.mid`
under `assets/audio/` that is not a rejected take, a scratch candidate or a probe: **173 files scored, 0
failed**, before the work and again after it. The ear side is `data/ear_ledger.csv`, which holds the last
recorded six criterion review per file.

## 2. The score table before, best take per family, weakest first

| hook | family | best take on disk | bars | weakest criterion |
| --- | --- | --- | --- | --- |
| 44 | render2_demo | render2_demo.mid | 4 | hook cell |
| 49 | baroque_demo | baroque_demo.mid | 20 | hook cell |
| 78 | title_theme | title_theme_v6.mid | 52 | motif coverage |
| 81 | hadrian_theme | hadrian_theme.mid | 32 | contour |
| 93 | pp_drive | pp_drive_v5.mid | 125 | loop length |
| 97 | pp_06_percy_possessed_v7 | _cand_open.mid | 48 | loop length |
| 98 | pp_fight_v6 | ref_v5_fight_humanized_humanized.mid | 16 | contour |
| 99 | percy_theme | percy_theme_v3.mid | 32 | contour |
| 100 | the other thirteen families (pp_01_title, pp_03_harbor, pp_03_quay_storm, pp_04_fight_baroque, pp_04_navy_sailors, pp_05_small_ship, pp_06_percy_possessed, pp_15a, pp_15b, pp_15b_v5, pp_arrival, pp_boarding, pp_fight) | 16 to 32 bars | motif coverage |

## 3. The cue this card picked, and why

`title_theme` at 78 is superseded (PP-01 `pp_01_title_v13` is the live title cue at 100), `percy_theme`
at 99 is retired, `pp_06` and `pp_drive` lose only `loop length` to a gamedev-owned cut length (48 bar
boss scope, 125 bar film grid), and the two demos are not cues.

`hadrian_theme` was the weakest live theme that this lane may change: 81 of 100, and the losses were all
in the melody itself, `contour` 0 of 10 (0 of 7 returns were an arch or a pedal), `leaps per motif` 4 of
8 (0 leaps), `variation on the third return` 3.2 of 8 (100 percent a copy).

## 4. The score table after

| hook | family | best take on disk | bars | weakest criterion |
| --- | --- | --- | --- | --- |
| 44 | render2_demo | render2_demo.mid | 4 | hook cell |
| 49 | baroque_demo | baroque_demo.mid | 20 | hook cell |
| 78 | title_theme | title_theme_v6.mid | 52 | motif coverage |
| 93 | pp_drive | pp_drive_v5.mid | 125 | loop length |
| 97 | pp_06_percy_possessed_v7 | _cand_open.mid | 48 | loop length |
| **97** | **hadrian_theme** | **hadrian_theme_v2/hadrian_theme_v2.mid** | **32** | **steps over leaps** |
| 98 | pp_fight_v6 | ref_v5_fight_humanized_humanized.mid | 16 | contour |
| 99 | percy_theme | percy_theme_v3.mid | 32 | contour |
| 100 | the other thirteen families, unchanged | | | motif coverage |

## 5. hadrian_theme criterion by criterion

| criterion | v1 points | v2 points | v2 measured |
| --- | --- | --- | --- |
| motif coverage (20) | 20.0 | 20.0 | 66 percent of 53 notes |
| motif returns (12) | 12.0 | 12.0 | 7 returns |
| hook cell (10) | 10.0 | 10.0 | 6 notes, rhythm 2/2/2/4/4/2 repeated 3 times |
| steps over leaps (12) | 12.0 | 9.2 | 50 percent steps (2 of 4 intervals), 1 leap |
| leaps per motif (8) | 4.0 | 8.0 | 1 leap |
| range (8) | 8.0 | 8.0 | 9 semitones (68 to 77) |
| contour (10) | 0.0 | 10.0 | 7 of 7 returns arch |
| repeated pitch (6) | 6.0 | 6.0 | 2 repeated pitches in a row |
| loop length (6) | 6.0 | 6.0 | 32 bars |
| variation on the third return (8) | 3.2 | 8.0 | 80 percent the same as the first |
| **total** | **81** | **97** | |

## 6. What the change is

Seven lead bars and four answer bars gained a one eighth answering lift: `D5 C#5 (rest) A4 G#4` becomes
`D5 C#5 (rest) A4 G#4 D5`, so the bident falls and the blade springs back to the tonic, one arch per
phrase and one six semitone leap in the motif. The third entrance (bar 9, the card's own check bar) lifts
to `A4` and the third phrase's to `Bb4`, so the third return is a variation rather than a copy. The H4
answer on `vrc6 pulse b` takes the same lift. Full notes, hashes and the check list:
`assets/audio/hadrian_theme_v2/NOTES.md`.

Nothing else moved: 32 bars, 92 bpm, D minor, 4/4, the chord frame, the Neapolitan Eb at bars 7, 15 and
23, the Picardy, the voices, the textures, the drums, and the loop.

## 7. Loop seam

`assets/audio/hadrian_theme_v2/hadrian_theme_v2_loop.json`: loop 32 bars, 83.478277 s, 3,681,392 samples,
`loop_seam_sample_difference` 0, `loop_edge_peak_head` 1410, `loop_edge_peak_tail` 0, fade 5.0 ms raised
cosine, peak -1.0 dBFS. The seam numbers are the same as v1's.

## 8. Checks run

`check_hadrian_score.py` 19 passed 0 failed; `arrange.py` 32 bars 83.478 s; `hook_score.py` 97; 
`melody_guard.py` PASS against 32 musikage references (jaccard 0.0000, longest identical interval run 3);
`render_chip.py` wav + 192k mp3 + loop json. Every command and its output is in the v2 NOTES.

## 9. The ear loop, and why it did not run again

`tools/ear_critic.py` reads `GEMINI_API_KEY` from `os.environ` at call time and refused:

    not configured: GEMINI_API_KEY is not set in the environment

This session carries `PINE_SANDBOX_API_KEY` and `KAGGLE_API_TOKEN` and no Gemini key, and the card forbids
opening key files. The four rounds this card allows were therefore hook score rounds, not ear rounds, and
the ear column above is the last recorded review per file, not a new measurement.

## 10. Questions

Q: for Nayil. The Gemini key is not in this lane's session environment, so no AUTO-MUSIC-NEXT card can run
an ear round until it is exported there. This is the second card in a row that could not start the loop.
Should it be exported to the lane, or should ear rounds stay a manual step?

Q: for gamedev, row owner of `data/audio.json`. `hadrian_theme` is not a delivered cue yet (PP-07 to PP-14
are all null), so nothing is registered for it. If it should become a cue row, which id, and does the
92 bpm and the cold drum profile (no variation every 4 or 8 bars) stand against the AUTO-MUSIC-NEXT line
that asks for the 126 bpm family and drums that vary? Both are pinned by the cue's own card and its 19
checks, so this lane did not move them.
