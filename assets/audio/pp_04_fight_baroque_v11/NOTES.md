# PP-04 fight, take G (pp_04_fight_baroque_v11): the heard stream now carries the humanize pass

Card t_1064983c (AUTO-MUSIC-NEXT, musician), 2026-11-16. Take F (`pp_04_fight_baroque_v10/`) is
untouched: this take reads its score and writes only inside this folder.

## 1. Why this cue, measured

Every `.mid` under `assets/audio/` was scored in this session with `tools/hook_score.py` (154
files, `knowledge/MUSIC-HOOK-GRAMMAR.md` loaded, report per file). The newest non-rejected take
per live cue family, score grid and heard grid separately, because the humanized file is what a
player hears:

| cue | newest take | hook, score grid | hook, humanized (heard) |
| --- | --- | --- | --- |
| PP-01 Title | pp_01_title_v13 | 100 | 99 |
| PP-02 The Drive | pp_drive_v7 | 93 | no humanized take |
| PP-03 Harbor Storm | pp_03_quay_storm_v4 | 100 | none |
| **PP-04 Fight | pp_04_fight_baroque_v10** | **100** | **88** |
| PP-04 Navy Sailors | pp_04_navy_sailors_v3 | 100 | 99 |
| PP-05 Small Ship | pp_05_small_ship_v7 | 100 | none |
| PP-06 Percy, Possessed | pp_06_percy_possessed_v5 | 100 | none |
| PP-15a Entropy | pp_15a_credits_kill_v3 | 100 | none |
| PP-15b Mercy | pp_15b_credits_spare_v3 | 99 | none |
| PP-17 Boarding | pp_boarding_v4 (humanized take only; no plain file on disk) | 100 | 100 |
| PP-18 Harbor, Calm | pp_03_harbor_v5 | 100 | 100 |

PP-02's 93 is a documented ceiling (a 125 bar film cue is not 8, 16 or 32 bars, which is 6 of its
7 missing points; `knowledge/PP-02-CEILING-2026-11-14.md`). PP-04 fight at 88 on the heard grid is
therefore the lowest improvable hook score on the board, and its 12 missing points are not
composition: take F's score grid is a full 100 and the humanize pass is what costs 12.

## 2. The defect, measured

Take F's delivered stream is rendered from the plain score, and its NOTES.md says why: the
humanize pass adds a grace note and a mordent on the motif's third return, the melody goes from 78
notes to 81, and the motif finder then prefers an 11 note window from bar 6 with 3 returns at 47
percent coverage. The measured failing criteria on that file are motif coverage 15.64 / 20, leaps
per motif 4.00 / 8 (2 leaps instead of 1) and contour 6.67 / 10, which is 12 points.

## 3. Four rounds, each scored

| round | humanize pass | melody notes | hook | failing criteria |
| --- | --- | --- | --- | --- |
| 1 | `--ornament-note first` (tool default) | 81 | 88 | motif coverage 15.64 / 20, leaps 4.00 / 8, contour 6.67 / 10 |
| 2 | `--ornament-note second` | 81 | 88 | the same three, to the same numbers |
| 3 | `--ornament-note none` | 78 | **100** | none |
| 4 | round 3 plus `--onset-frames 1` | 78 | 100 | motif coverage 19.66 / 20 (59 percent, inside the round's own tolerance) |

Round 3 is kept. Round 4 proves the micro-timing option is safe but costs a third of a point of
coverage for no gain, so the heard take keeps the written onsets. Round 2 is worth recording: on
this cue the first and second placements score the same, because both move the motif's start off
the bar line the finder reads it from, so the choice is not about which note takes the ornament
but about whether the motif's onset is rewritten at all.

## 4. The score table, before and after

| take | hook, score grid | hook, humanized (heard) | gate | seam | rendered from |
| --- | --- | --- | --- | --- | --- |
| pp_04_fight_baroque_v10 | 100 | 88 | PASS | jump 0, tail 894 | the plain score |
| **pp_04_fight_baroque_v11** | **100** | **100** | PASS | jump 0, tail 0, first and last samples 0 | the humanized take |

Nothing in the written score changed: `pp_04_fight_baroque_v11.mid` is take F's own bytes, sha256
`301158ed2ff98c9f921d97b811954839189e8f41316bf4a5b32c0b98d90a7cac`. Both grids read the same
motif on the same bars: 2 bar motif from bar 1, 12 notes, 4 returns at bars 1, 5, 9 and 13, 61.5
percent coverage, and all ten criteria full on both files (`hook_report_v11.json`,
`hook_report_v11_humanized.json`).

## 5. Files

| file | what it is | bytes |
| --- | --- | --- |
| `pp_04_fight_baroque_v11.mid` | take F's score, byte for byte | 3851 |
| `pp_04_fight_baroque_v11_humanized.mid` | the heard take, sha256 `a411673e7a1064407606d7dd4c3bb843ee780013422cf4281f87b3ac09e1b0d0` | 5921 |
| `pp_04_fight_baroque_v11.wav` | the render of the heard take, 22.857 s, 1008000 samples, peak -1.00 dBFS | 2016044 |
| `pp_04_fight_baroque_v11_master.wav` | -14.59 LUFS integrated, -0.65 dBTP | 2194364 |
| `pp_04_fight_baroque_v11.ogg` | the delivered stream, libvorbis q6 from the master, sha256 `2949a90ce2d1b3ed36a10d80bccf8c898e5c052e18dbb7574d44cd18c681df40` | 354073 |
| `pp_04_fight_baroque_v11.mp3` | the same master, lamemp3 q2, for review | 360980 |
| `pp_04_fight_baroque_v11_loop.json` | seam and level measurements from the renderer | 1543 |
| `hook_report_v11.json`, `hook_report_v11_humanized.json` | the two hook grids | |
| `humanize_report_v11.json` | what the pass applied: 388 of 403 notes changed, 4 breaths, 8 vibrato notes, 374 envelope points, 3 fills | |
| `build_report.json` | what was rendered from what, with the loudness numbers | |
| `gate_report_v10.json`, `gate_report_v11_humanized.json` | the cue gate, before and after | |
| `build_pp_04_fight_v11.py` | the whole build, rerunnable | |

What the pass applies, per `humanize_report_v11.json`: articulation to the NES 1/60 s frame grid
on 388 notes, velocity plus or minus 6 from a fixed seed, control change 11 envelopes per role,
control change 1 and 20 vibrato varying per two bar phrase on 8 melody notes, 4 phrase breaths,
and a noise fill in the last beat before each of the 3 section changes. Everything is
deterministic: the same score and the same seed give the same bytes.

## 6. Loop seam

Measured on the render, not asserted from the renderer's log: `pp_04_fight_baroque_v11.wav` is
1008000 samples at 44100 Hz (22.857143 s), the first eight samples read 0, 0, 0, 1, 2, 5, 9, 15
and the last eight read 0, 0, 0, 0, 0, 0, 0, 0, and the loop json records
`loop_seam_sample_difference 0`, `loop_edge_peak_tail 0`, `loop_edge_max_jump 488` against take
F's 499. The loop point is the last sample of bar 16, which is the whole 16 bar loop.

## 7. Drum variation

The drum figure is take F's, note for note (this take touches no pitched note and no percussion
note: the score is byte identical). Measured per bar on the noise track, 16 bars:

    bars 1, 2, 3    8 closed hats each (pitch 42)
    bar 4           11 hits, hat plus kick 38 and open 44, the one beat fill
    bars 5, 6, 7    8 closed hats each
    bar 8           15 hits, the two beat fill and the brightness lift
    bars 9, 10, 11  8 hits each, the phrase turns over: hat 40 on the downbeat instead of 42
    bar 12          11 hits, fill
    bars 13, 14, 15 4 low hits each (pitch 34), the texture change into the close
    bar 16          10 hits, the close and the lift into the loop point

So the figure changes every 4 bars (a fill at 4, 8, 12 and 16) and every 8 bars (hat register from
bar 9, low texture from bar 13), which is the structure the card asks for. The inner bars are
steady on purpose: a fight cue's drums sit under a four bar phrase, and the card's no invented
parts rule keeps this take to what take F wrote.

## 8. Dissonance and the cue gate

`tools/counterpoint/cue_gate.py` PASSES both grids with the same hard and soft counts:

| measure | v10 plain | v11 humanized |
| --- | --- | --- |
| state | PASS | PASS |
| raw clashes on a strong beat | 0 | 0 |
| parallel perfect fifths or octaves between the outer voices | 0 | 0 |
| by severity | hard 0, soft 2, style 1 | hard 0, soft 2, style 1 |
| clash classes | passing 11, appoggiatura 1, raw 0 | passing 11, appoggiatura 1, raw 1 |

The humanize pass raises the off beat raw clash count from 0 to 1 (one spot, no strong beat
involved, next to the 11 passing tones) and moves no rule from clean to open; the verdict's reason
line is unchanged. Per `knowledge/MUSIC-DISSONANCE.md` those passing and appoggiatura places are
the tasteful kind, and its F1 rule (no device on the first or last note of a leitmotif statement)
holds here because this take adds no melody note at all: the motif is `FIGHT_SUBJECT` (76 74 72 71
71) stated at bars 1, 5, 9 and 13, and none of its edges moved.

`tools/check_dissonance_rules.py`: not run, it audits `data/dissonance_rules.json` and the
injector, not a cue. `python -m pytest tests/test_humanize.py` was not run either; the pass used
the tool unmodified, at a supported option.

## 9. Tempo

168.0 bpm, 4/4, 16 bars, unchanged (the score is take F's bytes). 168 = 126 x 4/3, but tempo is
the cue's own value and not this card's to move.

## 10. The ear loop did not run

`tools/ear_critic.py` reads `GEMINI_API_KEY` from the process environment only. Checked with
`os.environ` in this session: unset. So zero of the four ear rounds ran on Gemini and no ear score
exists for v11. No key file was opened and nothing was printed.

Q: for gamedev, fifth repeat across cards t_50cbadb5, t_5b93b0cc, t_71c5dea2, t_e83bbd8d and now
t_1064983c: is the ear key meant to be exported into musician sessions, or are the ear rounds
expected to be skipped when it is not?

## 11. What Nayil has to decide by ear

v11 is a candidate, not a delivery. `data/audio.json` PP-04 still names the take F stream, and
re-pointing that row is a wiring decision that needs his ear on the two files side by side:

    assets/audio/pp_04_fight_baroque_v10/pp_04_fight_baroque_v10.ogg   the sequencer grid, 100 on
                                                                       the score grid, 88 on the
                                                                       heard grid
    assets/audio/pp_04_fight_baroque_v11/pp_04_fight_baroque_v11.ogg   the same notes played, 100
                                                                       on both grids

Both are mono 48 kHz, both loop at 22.857 s, both loudness matched to about -14.6 LUFS.
