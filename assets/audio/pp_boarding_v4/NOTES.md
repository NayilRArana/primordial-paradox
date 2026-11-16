# PP-17 Boarding, take v4: the heard version keeps the written hook

Card t_ec3c4d32 (AUTO-MUSIC-NEXT, musician), 2026-11-16. Clean room: the music is the lane's own
score as v3 wrote it; `pp_boarding/`, `pp_boarding_v2/`, `pp_boarding_v3/` and the delivered
`pp_boarding_master1/` are untouched.

## Why this cue, measured

Every live family was scored today with `tools/hook_score.py` on the newest take on disk, both the
score grid version and the humanized version, because the humanized one is what a player hears:

| cue | newest take | hook, score grid | hook, humanized |
| --- | --- | --- | --- |
| PP-02 The Drive | pp_drive_v7 | 93 | no humanized take |
| PP-15b Mercy | pp_15b_credits_spare_v3 | 99 | none |
| PP-01 Title | pp_01_title_v13 | 100 | 99 |
| PP-18 Harbor, Calm | pp_03_harbor_v4 | 100 | 95 |
| PP-03 Harbor Storm | pp_03_quay_storm_v4 | 100 | none |
| PP-04 Navy Sailors | pp_04_navy_sailors_v3 | 100 | 99 |
| PP-05 Small Ship | pp_05_small_ship_v7 | 100 | none |
| PP-06 Percy, Possessed | pp_06_percy_possessed_v5 | 100 | none |
| PP-15a Entropy | pp_15a_credits_kill_v3 | 100 | none |
| PP-17 Boarding | pp_boarding_v3 | 100 | 93 |

The table is `assets/audio/hook_tax_2026-11-16.json`. PP-02 sits at 93 on a documented ceiling (a
125 bar film cue cannot be 8, 16 or 32 bars, which is 6 of its 7 missing points; card t_16784440).
PP-17 is the only other take whose measured score is below 99, and its 7 points are not composition:
they are what the humanize pass did to the melody. That is the gap this take closes.

## The defect, measured

`tools/humanize.py` writes a grace note and a mordent on the first melody note of the motif's third
return. Both add onsets on a phrase head, and `hook_score` finds the motif from those onsets. On
pp_boarding_v3 the same written melody scores:

| humanize variant | melody notes | hook | motif found |
| --- | --- | --- | --- |
| written score, no humanize | 67 | 100 | bar 5, 4 returns, 64 percent coverage |
| ornament on the bar's first note (the old default) | 70 | 93 | bar 6, 3 returns, 50 percent |
| ornament on the bar's second note | 70 | 78 | bar 1, 2 returns, 31 percent |
| no ornament, every other pass on | 67 | 100 | bar 5, 4 returns, 64 percent |

The second-note idea was the first attempt and it is worse, so it is kept only as a rejected take
(`assets/audio/_rejected_pp_boarding_v4_ornament_second/`). What ships is the fourth row: articulation
to the frame grid, velocity, envelopes, vibrato, seven breaths and eight fills all still applied
(`humanize_report_v4.json`), and only the two ornament notes dropped.

## The score table, before and after

| take | hook, score grid | hook, humanized (heard) | gate, no baseline | seam | rendered |
| --- | --- | --- | --- | --- | --- |
| pp_boarding_v3 | 100 | 93 | REFUSED, CP-01 16 / CP-02 14 / CP-04 5 / CP-06 21 / CP-07 15 | not measured | yes |
| **pp_boarding_v4** | **100** | **100** | REFUSED, the same 16 / 14 / 5 / 0 / 21 / 15 / 0 / 0 | join 0 of 9853, clean | yes |

The gate counts are identical rule for rule because not one written note changed: v4 is v3's own
score, played. v3 answers LEGACY against `data/cue_gate_baseline.json` only because it is registered
there; without the baseline both takes refuse the same way, which is the cue's known state, not a
regression from this card.

The melody is not approximated: v4's `vrc6 pulse a` holds the same 67 notes in the same order as
pp_boarding_v3.mid, which is why the meter reads the same motif at the same bar.

## Render and seam

`tools/render_chip.py` (v2 voices, 2A03 pulse, triangle, noise and dpcm plus VRC6 pulse a, pulse b and
saw): 31.813 s, peak -1.00 dBFS, RMS -15.06 dBFS, 120 bpm, 4/4. The gradient seam check is in
`seam_report_v4.json`: the step across the loop join is 0 against the largest step inside the last and
first half second of audio, 9853.

## The ear loop did not run

`tools/ear_critic.py` reads `GEMINI_API_KEY` from the process environment only, and it is unset in this
session (`os.environ` check, no file read, no print). So no ear round was played and no ear score for
v4 exists. This is the fifth card in a row on that wall.

## Limits the take respects

Two 2A03 pulses, triangle, noise and dpcm, plus the three VRC6 voices, the same board the score uses.
120 bpm and 4/4, which is the cue's own spec from gamedev ruling D1/D1a and is not changed by this
card. Drums keep v3's kit, which changes rung every two bars and every four, with fills at 4, 8 and 12.
The three dissonance devices, the two secondary dominants and the drop at bars 5 and 6 are v3's and are
untouched.

## Files

    pp_boarding_v4_humanized.mid    the take: v3's melody and v3's kit, humanized without the ornament
    pp_boarding_v4.wav              the render, 31.813 s, peak -1.00 dBFS
    pp_boarding_v4.mp3              192k encode of the same render
    pp_boarding_v4.ogg              libvorbis q5, 397221 bytes
    pp_boarding_v4_loop.json        loop points and voice map from the renderer
    hook_report_v4.json             hook 100 on the rendered MIDI
    humanize_report_v4.json         the pass, with ornaments 0 and fills 8
    gate_report_v4.json             the gate, rule counts identical to v3
    seam_report_v4.json             the join measurement
