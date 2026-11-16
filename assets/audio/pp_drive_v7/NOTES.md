# PP-02 Drive, take v7: the last CP-01 closed and the take rendered

Card t_16784440 (AUTO-MUSIC-NEXT, musician), 2026-11-14, node CitadelArana. Clean room: this is the
lane's own composition on the project's own score, `assets/audio/pp_drive/score_pp_drive.yaml`, by
way of the v6 take. `pp_drive/`, `pp_drive_v2/`, `pp_drive_v4/`, `pp_drive_v5/`,
`pp_drive_v5_master/`, `pp_drive_v6/`, and the delivered `pp_drive_master1.ogg` are untouched.

## Why this cue, measured

`tools/hook_score.py` on the best take on disk for every live family, run in this session:

| family | take measured | hook |
| --- | --- | --- |
| PP-02 pp_drive | pp_drive_v6.mid | 93 |
| PP-15b pp_15b_credits_spare | pp_15b_credits_spare_v3.mid | 99 |
| PP-01 pp_01_title | pp_01_title_v13.mid | 100 |
| PP-03 pp_03_quay_storm | pp_03_quay_storm_v4.mid | 100 |
| PP-04 pp_04_navy_sailors | pp_04_navy_sailors_v3.mid | 100 |
| PP-04b pp_04_fight_baroque | pp_04_fight_baroque_v10.mid | 100 |
| PP-05 pp_05_small_ship | pp_05_small_ship_v7.mid | 100 |
| PP-06 pp_06_percy_possessed | pp_06_percy_possessed_v5.mid | 100 |

PP-02 is the only live family under 99, and its 93 is a ceiling, not a gap: 6 of the 7 missing points
are loop length (a 125 bar cue on the film grid cannot be 8, 16 or 32 bars) and 1.1 is contour. The
melody is therefore frozen, and the improvement this card can make is everything around it.

## The score table, before and after

All hook numbers are `tools/hook_score.py`; gate numbers are `tools/counterpoint/cue_gate.py`.

| file | hook | CP-01 open | CP-09 open | M1a hard | raw clashes (strong) | rendered |
| --- | --- | --- | --- | --- | --- | --- |
| pp_drive_v5.mid, two takes back | 93 | 67 | 4 | FAIL 343 | 896 (116) | yes |
| pp_drive_v6.mid, previous take | 93 | 1 | 0 | PASS 72 | 31 (9) | no |
| **pp_drive_v7.mid, this take** | **93** | **0** | **0** | **PASS 71** | **31 (9)** | **yes** |

The hook is frozen, not approximated: the melody voice `vrc6 pulse a` holds 448 notes and
`cp01_fix_report_v7.json` records `"hook_voice_identical": true`.

## The one edit

`tools/counterpoint/cue_gate.py` on v6 left one hard finding: bar 81 beat 1.0, `G5` in `vrc6 pulse a`
a major second against `pulse 2`'s `A5`, leaving to `E5` by leap instead of by step. Both voices
sustain through that tick, so the v6 clash pass had no onset to move.

The v7 fix splits the `pulse 2` note at tick 115200 and lets its tail change pitch, `A5` to `D5`:

    bar 81 beat 1.0, before:  vrc6 pulse a G5, pulse 1 B4, pulse 2 A5   (M2, unprepared)
    bar 81 beat 1.0, after:   vrc6 pulse a G5, pulse 1 B4, pulse 2 D5   (P4 over B4, m3 under G5)

`D5` is chosen by ear among the eight candidates the analyser scores equally at CP-01 0 (`G#5`, `B5`,
`G5`, `F5`, `E5`, `D5` and the octave shifts `D6` and `E6`): `G#5` would sit a minor second under the
melody, which is the one thing `knowledge/MUSIC-DISSONANCE.md` forbids outright, and `G5`/`E5` would
double the lead, which the same file scores -3 and forbids in its one voice table ("no device may be
doubled across two channels"). `D5`
leaves a G major colour under the `G5` that becomes `Em7` when the melody lands on `E5`: no doubling,
no second, and the resolution stays audible. The judge is the project's own engine
(`rules.load_score` + `rules.analyse`), and only a move that lowered the count was accepted.

The script is `fix_cp01_v7.py` in this folder; `cp01_fix_report_v7.json` holds the measured before and
after and the exact note rectangles.

## Render and seam

`tools/render_chip.py` (v2 voices, 2A03 pulse, triangle and noise plus VRC6 pulse a, pulse b and saw,
dpcm kick and snare), 178.563 s, peak -1.00 dBFS, RMS -16.25 dBFS, 126.0001 bpm, 3/4.

Loop seam from `tools/drive_v2.seam_check` on the render:

| section | max step inside | step across the join | ratio | verdict |
| --- | --- | --- | --- | --- |
| A to A (bars 1 to 25) | 12091 | 288 | 0.02 | clean |
| B to B (bars 26 to 59) | 15623 | 1129 | 0.07 | clean |

The same check on the previous take, `pp_drive_v5.wav`, gives 288 and 1129 as well: the pitch edit
does not touch a loop edge.

## The ear loop did not run

`tools/ear_critic.py` reads `GEMINI_API_KEY` from the process environment only. A `os.environ` check
in this session finds it unset, so no ear round was played and no ear score for v7 exists. The key was
never read from a file and never printed. This is the fourth card in a row on this wall
(t_50cbadb5, t_5b93b0cc, t_71c5dea2, t_e2731314).

## Limits the take respects

Two 2A03 pulses, triangle, noise and dpcm (real 2A03), plus the three VRC6 voices, which is the board
the score uses. 126 bpm and 3/4 across all 125 bars. Drums vary every 4 and every 8 bars, carried from
v5 (`drive_v2.drum_bar`), untouched here. Humanizing stays inside the score (delayed vibrato,
`v5`'s own humanize pass) so the renderer cannot smear an onset off the grid.

## Files

    pp_drive_v7.mid                 the take, hook 93, gate CP-01 0, CP-09 0, PASS
    pp_drive_v7.wav                 the render, 178.563 s, peak -1.00 dBFS
    pp_drive_v7.mp3                 192k encode of the same render
    pp_drive_v7.ogg                 libvorbis q5, 2168855 bytes
    pp_drive_v7_loop.json           loop points and voice map from the renderer
    hook_report_render_v7.json      hook score of the rendered MIDI
    cp01_fix_report_v7.json         the one edit, measured before and after
    fix_cp01_v7.py                  the pass, judged by rules.analyse
