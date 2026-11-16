# PP-18 Harbor, take v5: the heard take keeps the hook the score writes

Card t_e83bbd8d (AUTO-MUSIC-NEXT, musician), 2026-11-16. Clean room: the score is the lane's own
`assets/audio/pp_03_harbor_v4/pp_03_harbor_v4b.mid`, copied byte for byte; `pp_03_harbor/`,
`pp_03_harbor_master1/`, `pp_03_harbor_v2/`, `pp_03_harbor_v3/` and `pp_03_harbor_v4/` are untouched.

## 1. Why this cue, measured

Every `.mid` under `assets/audio/` that belongs to a live cue family was scored with
`tools/hook_score.py` in this session, and the two grids were scored separately because the
humanized file is what a player hears:

| cue | newest take | hook, score grid | hook, humanized |
| --- | --- | --- | --- |
| PP-02 The Drive | pp_drive_v7 | 93 | no humanized take |
| PP-15b Mercy | pp_15b_credits_spare_v3 | 99 | none |
| PP-01 Title | pp_01_title_v13 | 100 | 99 |
| **PP-18 Harbor, Calm** | **pp_03_harbor_v4b** | **100** | **95** |
| PP-03 Harbor Storm | pp_03_quay_storm_v4 | 100 | none |
| PP-04 Navy Sailors | pp_04_navy_sailors_v3 | 100 | 99 |
| PP-05 Small Ship | pp_05_small_ship_v7 | 100 | none |
| PP-06 Percy, Possessed | pp_06_percy_possessed_v5 | 100 | none |
| PP-15a Entropy | pp_15a_credits_kill_v3 | 100 | none |
| PP-17 Boarding | pp_boarding_v4 | 100 | 100 |

PP-02 sits at 93 on a documented ceiling (a 125 bar film cue cannot be 8, 16 or 32 bars, which is
6 of its 7 missing points; card t_16784440 and knowledge/PP-02-CEILING-2026-11-14.md). PP-17 closed
its own humanize gap yesterday (card t_ec3c4d32). PP-18 at 95 on the heard grid is therefore the
lowest improvable hook score among the live cues, and its 5 missing points are not composition:
they are what the humanize pass did to the melody.

## 2. The defect, measured, in four rounds

`tools/humanize.py` writes a grace note and a mordent on the first melody note of the motif's third
return. Those two added onsets change what `hook_score` reads as the phrase, so the written 80
percent third return reads as a 100 percent copy. Four rounds on this cue, each scored:

| round | humanize pass | melody notes | hook | failing criteria |
| --- | --- | --- | --- | --- |
| 1 | `--ornament-note first` (the tool default) | 110 | 95 | motif coverage 19.4 / 20, third return 3.2 / 8 |
| 2 | `--ornament-note second` | 110 | 94 | motif coverage 19.1 / 20, third return 3.2 / 8 |
| 3 | `--ornament-note none` | 107 | **100** | none |
| 4 | round 3 plus `tools/counterpoint/repair.py --rounds 2` on the score | 107 | 100 | gate CP-01 8 to 10, strong beat raw clashes 4 to 12 |

Round 4 is kept as a rejected take, not shipped: the accompaniment repair cut raw clashes 114 to 14
and parallel perfect intervals 2 to 0, and made the gate's own G1 criterion worse (8 to 10 CP-01,
4 to 12 raw clashes on a strong beat) by moving notes onto strong beats. It is on disk at
`assets/audio/_rejected_pp_03_v5_repair/pp_03_harbor_v6_draft.mid` with its
`repair_report.json`. Round 3 is what ships: the
articulation to the frame grid, the velocity, the envelopes, the vibrato, the breaths and the fills
are all still applied (`humanize_report_v5.json`); only the two ornament notes are gone, and the
written melody is 107 notes on both grids.

## 3. The score table, before and after

| take | hook, score grid | hook, humanized (heard) | gate | seam | rendered |
| --- | --- | --- | --- | --- | --- |
| pp_03_harbor_v4b | 100 | 95 | LEGACY, CP-01 8 / CP-09 2 / raw 114 / strong 4 | jump 0 | yes |
| **pp_03_harbor_v5** | **100** | **100** | REFUSED, the same CP-01 8 / CP-09 2 / raw 114 / strong 4 | join 0 of 4980706, clean | yes |

The gate numbers are identical rule for rule because not one written note changed: v5 is v4b's own
score, played. v4b answers LEGACY against `data/cue_gate_baseline.json` only because it is registered
there; without the baseline v5 refuses the same way, which is the cue's known state, not a
regression from this card. `gate_report_v5_plain.json` and `gate_report_v5_humanized.json` hold the
per-spot list (bars 7, 11, 15, 18, 27, 31 for CP-01; bars 26 and 28 for the parallel fifths).

## 4. Files, render and seam

| file | what it is |
| --- | --- |
| `pp_03_harbor_v5.mid` | v4b's score, byte identical, sha256 `0ff67d917059321fbaa73a8448f3cdad531b53c8a0f7d0d707241d174d342128` |
| `pp_03_harbor_v5_humanized.mid` | the heard take, 13545 bytes, sha256 `8e3e89e55a2d9d2afb2ebae9f67b87d00910e171e2f2f58c09e9ecbc1fc98114` |
| `pp_03_harbor_v5.wav` | the render, 112.941 s, peak -1.00 dBFS, rms -16.15 dBFS, 4980706 samples |
| `pp_03_harbor_v5.mp3`, `pp_03_harbor_v5.ogg` | the same render, 192k mp3 and libvorbis q5 (1477419 bytes) |
| `pp_03_harbor_v5_loop.json` | loop point and voice map from the renderer |
| `hook_report_v5.json`, `hook_report_v5_humanized.json` | the two hook reports |
| `humanize_report_v5.json` | what the pass applied, per role |
| `gate_report_v5_plain.json`, `gate_report_v5_humanized.json` | the gate, per spot |

Render: `render_chip.py` v2 voices (2A03 pulse 1, pulse 2, triangle, noise, dpcm plus VRC6 pulse a,
pulse b, saw), soft limiter, peak target -1.0 dBFS, 32 bars, 68 bpm, 4/4, 112.941 s.

Seam, `check_seam_v4.py pp_03_harbor_v5.wav 32`:

    loop point sample 4980706 (112.9412 s)
    seam jump 0
    last sample of the loop 0, first sample 0
    tail beyond loop point: 0 samples

## 5. Drum variation

The drums are not written in this take: they come from `data/drum_patterns.json` through the rung
builder in `build_pp03_v4.py` (`build_bar_grid`). v5 carries that grid unchanged, because the score
is unchanged. The four `drums:` specs in `score_pp03_v4b.yaml` are, per 8 bar phrase, a list of
eight per-bar rungs over a named home pattern (lines 74, 93, 113, 134):

    arrival  home CLM-01  rungs [5, 1, 0, 2, 4, 1, 6, 3]
    settle   home CLM-01  rungs [0, 1, 2, 4, 3, 1, 6, 7]
    light    home CLM-02  rungs [5, 2, 1, 4, 3, 6, 1, 7]
    close    home CLM-08  rungs [5, 1, 2, 4, 3, 6, 4, 7]  build_up [7, 8]

So no two adjacent bars share a rung (the `1` rung returns once inside most phrases), bar 4 of every
phrase takes the one beat fill (`fill_beat: FLF-01`) and bar 8 the two beat fill (`fill_end: FLR-01`,
`FLT-02` and `FLX-10` in the last two phrases), and the close rolls brighter through bars 7 and 8 into
the loop point, which is the same `phrase_plan` the score states at line 149.

## 6. The ear loop did not run

`tools/ear_critic.py` reads `GEMINI_API_KEY` from the process environment only. An `os.environ`
check in this session finds it unset, so zero of the four ear rounds were played on Gemini and no
ear score exists for v5. The key was never read from a file and never printed.

Q: for gamedev, fourth repeat across cards t_50cbadb5, t_5b93b0cc, t_71c5dea2 and t_e83bbd8d: is
the ear key meant to be exported into musician sessions, or are the ear rounds expected to be
skipped when it is not?

## 7. What Nayil has to decide by ear

v5 is a candidate, not a delivery. `data/audio.json` PP-18 still names
`assets/audio/pp_03_harbor_master1/pp_03_harbor_master1.ogg`, and re-pointing that row is a wiring
decision that needs his ear on v5 first, together with the four CP-01 spots the gate still lists.
