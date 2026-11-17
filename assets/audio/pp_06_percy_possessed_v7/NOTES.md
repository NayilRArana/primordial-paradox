# PP-06 "Percy, Possessed", take G (`pp_06_percy_possessed_v7`): the 48 bar form, hook 97

Card `t_2adbbc6e` (AUTO-MUSIC-NEXT, musician lane), 2026-11-16, node CitadelArana. Clean room: take F
(`pp_06_percy_possessed_v6`) is read, never written; takes D, E and F, `data/audio.json`,
`data/ear_ledger.csv` and the shipped stream `assets/audio/pp_06_percy_possessed/` are untouched.

## 1. The sweep, and why this cue

Every `.mid` under `assets/audio/` was scored in this session with `tools/hook_score.py`: 180 files,
20 cue families, grammar `knowledge/MUSIC-HOOK-GRAMMAR.md`. Best take per live family:

| family | best take on disk | hook | bars | what is missing |
| --- | --- | --- | --- | --- |
| PP-02 pp_drive | pp_drive_v7 | **93** | 125 | loop length 0.0 of 6 (125 bar film grid), contour 8.9 of 10 |
| PP-01 title | pp_01_title_v13 | 100 | 32 | full |
| PP-03 quay storm | pp_03_quay_storm_v4 | 100 | 32 | full |
| PP-04 navy | pp_04_navy_sailors_v3 | 100 | 32 | full |
| PP-04b fight | pp_04_fight_baroque_v11 | 100 | 16 | full |
| PP-05 small ship | pp_05_small_ship_v7 | 100 | 32 | full |
| **PP-06 percy** | **pp_06_percy_possessed_v6** | **100** | **32** | full, but 32 bars |
| PP-15a, PP-15b, PP-17, PP-18, pp_arrival | newest take | 100 | 32 | full |
| PP-06 theme `percy_theme` | percy_theme_v4 | 99 | 32 | contour 9.0 of 10; not a registered row |

PP-02 is the lowest number on the board and it is a ceiling, not a gap: the meter itself prints
`125 bars does not loop cleanly; write 8, 16 or 32 bars`, and the 125 bars are the film grid in
`data/title_timing.json`, which is a gamedev decision (`knowledge/PP-02-CEILING-2026-11-14.md`).

The cue with headroom that nobody has spent is PP-06. The stream the game plays,
`assets/audio/pp_06_percy_possessed/pp_06_percy_possessed.ogg`, is rendered from
`pp_06_percy_possessed.mid` and scores **52**. The takes since D score 96 and 100 and none of them can
be adopted, because they are 32 bars while `data/audio.json` records the cue as "E minor then G minor,
3/4, 150 bpm, **48 bars (57.6 s)**". The meter pays loop length for 8, 16 and 32 bars, so every take
that chased the meter shortened the cue, and the shorter it got the less adoptable it became.

## 2. What take G is

`build_pp_06_v7.py` reads take F, and appends a reprise the cue already contains: bars 1 to 16 again,
at bars 33 to 48, every voice, notes and control changes both. No note is composed outside take F, so
the leitmotifs, the drums and the dissonance devices are take F's own; the cue is simply 48 bars long
again, at 150 bpm, 3/4, 57.600 s, and its loop wraps at the sample it should.

Three candidates were written and scored, and the best was kept:

| candidate | bars | hook | weakest |
| --- | --- | --- | --- |
| `_cand_open` (bars 1 to 16 again) | 48 | **97** | loop length 3.0 of 6 |
| `_cand_second` (bars 17 to 32 again) | 64 | 97 | loop length 3.0 of 6 |
| `_cand_varied` (bars 1 to 16, last melody note up a step) | 48 | 93 | motif coverage 16.38 of 20 |

## 3. The score table, before and after

`tools/hook_score.py`, melody track `vrc6 pulse a`, same grammar for every row.

| file | bars | seconds | hook |
| --- | --- | --- | --- |
| pp_06_percy_possessed.mid (the shipped stream) | 48 | 57.6 | 52 |
| pp_06_percy_possessed_v3.mid | 48 | 57.6 | 88 |
| pp_06_percy_possessed_v4.mid (take D) | 32 | 38.4 | 96 |
| pp_06_percy_possessed_v5.mid (take E) | 32 | 38.4 | 100 |
| pp_06_percy_possessed_v6.mid (take F) | 32 | 38.4 | 100 |
| **pp_06_percy_possessed_v7.mid (take G, plain)** | **48** | **57.6** | **97** |
| **pp_06_percy_possessed_v7_humanized.mid (take G, heard)** | **48** | **57.6** | **97** |

Per criterion, take G: motif coverage 20.0 of 20 (83 percent), motif returns 12.0 of 12 (20 returns),
hook cell 10.0 of 10, steps over leaps 12.0 of 12 (78 percent), leaps per motif 8.0 of 8,
contour 10.0 of 10 (20 of 20 returns pedal), third return 8.0 of 8 (80 percent the same), range 8.0
of 8 (8 semitones), repeated pitch 6.0 of 6, loop length 3.0 of 6 (48 bars is a multiple of 16).

The four points take G gives up are the price of the spec's own length: 32 bars scores 100, 48 bars
scores 97. Against the stream the game plays, take G is **+45 points** and it needs no form change.

## 4. Render, master and seam

`tools/render_chip.py`, v2 voices (2A03 pulse, triangle, noise, dpcm plus VRC6 pulse a, pulse b and
saw), `--loop-bars 48`: peak -1.00 dBFS, RMS -15.25 dBFS, duration **57.600 s**, loop 2540160 samples,
**seam sample difference 0**, edge peak head 1170 and tail 416.

`tools/humanize.py` ran on take G for the heard variant: 1827 envelope points, 24 breaths, 12 fills
before section changes at bars 9, 17, 25, 33, 41 and 49 (loop period 8), 1 grace note, 1 mordent.

`master_v7.py` (fixed gain then a 5 ms attack look-ahead limiter, the `tools/final_mix.py` shape).
Source -16.64 LUFS, -1.00 dBTP. One pass, gain +2.64 dB, limiter -2.2 dBFS, and the delivered OGG
measures **-14.27 LUFS integrated, -1.21 dBTP true peak, LRA 0.4 LU**. The Vorbis overshoot is why the
limiter sits at -2.2 dBFS for a -1.21 dBTP result.

## 5. The ear loop did not run

`tools/ear_critic.py` reads `GEMINI_API_KEY` from the process environment only, and in this session
`os.environ` has it unset. No ear round was played, no ear score for take G exists, and no key file was
opened or printed. This is the fifth card in a row on that wall (t_50cbadb5, t_5b93b0cc, t_71c5dea2,
t_e2731314, and the take F card today).

## 6. Limits the take respects

Real 2A03 plus VRC6: the renderer's voice map is pulse 1, pulse 2, triangle, noise, dpcm and vrc6
pulse a, pulse b, saw, and no track is given a note outside its range (`build_report.json` of take F,
carried unchanged). 3/4, 150 bpm, the cue's own key plan. Drums are take F's, which vary every 4 and
every 8 bars and fill before each 8 bar section change. Dissonance is take F's, unchanged.

## 7. Files

    pp_06_percy_possessed_v7.mid              14697 bytes, hook 97, sha256 276dfc9b386dbf770efe1940c7b6702bfaad65bd4d818b276c8a39d0591428d3
    pp_06_percy_possessed_v7_humanized.mid   23600 bytes, hook 97, the heard variant
    pp_06_percy_possessed_v7.wav           5080364 bytes, the render, 57.600 s
    pp_06_percy_possessed_v7_master.wav    5080398 bytes, -14.27 LUFS
    pp_06_percy_possessed_v7.ogg            764368 bytes, sha256 e919a44af0f4118b69f4bdd0a3161118e48bc7c3e5a78d03e8312f06b569e4db
    pp_06_percy_possessed_v7.mp3           1383696 bytes, 192k
    pp_06_percy_possessed_v7_loop.json        1696 bytes, loop points of the render
    hook_report_v7_render.json                4105 bytes, hook score of the rendered MIDI
    humanize_report_v7.json                   2351 bytes, the humanize pass
    master_report_v7.json                     1148 bytes, the loudness walk
    candidates_v7.json                        1213 bytes, the three candidates
    build_pp_06_v7.py                         4073 bytes, the build
    master_v7.py                              3330 bytes, the master

## 8. What is still owed

Q: for gamedev. Take G is the same cue in the form the row records, 48 bars and 57.6 s, and it scores
97 against the shipped stream's 52. Moving the PP-06 row to it is the gamedev head's row to change, and
that card can point `data/audio.json` at
`assets/audio/pp_06_percy_possessed_v7/pp_06_percy_possessed_v7.ogg` without touching the form, the key,
the tempo or the length the spec records. Take F's 100 stays on disk as the 32 bar alternative: it is a
better hook score and a shorter cue, and choosing between them is a design call, not a measurement.
