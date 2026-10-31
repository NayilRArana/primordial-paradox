# PP-01 "Title Theme" v6, notes. Card AUTO-MUSIC-NEXT (t_9b5ccc92), written 2026-10-23 23:15 UTC.

The cue picked is PP-01 because it is the floor of the hook meter once every cue is scored on the
same melody track (`vrc6 pulse a`): **73 of 100**, lowest of the ten cues, with PP-04 navy next at
74. The first sweep of this run scored files on the meter's auto picked track and put the title at
59, which was a measurement error: the meter's default track for these files is not the lead, so
the table below was re-run with `--track "vrc6 pulse a"` on every file before the pick was made.
The ear had PP-01 at 31 of 60 on `gemini-3.5-flash-lite` (2026-10-23T02:05:36Z), also near the floor.

v5 (`assets/audio/pp_01_title/`) is untouched. This folder is a new version suffix and every file
in it carries `_v6`.

## 1. Hook meter, before and after (`tools/hook_score.py`, track `vrc6 pulse a`)

| file | score | failing criteria |
| --- | --- | --- |
| `pp_01_title.mid` (v5, the landed master) | 73 / 100 | motif_coverage, loop_length, leaps_per_motif, range, contour |
| `pp_01_title_v6.mid` (v6) | 83 / 100 | contour, loop_length, step_ratio, motif_coverage |

| criterion | v5 | v6 |
| --- | --- | --- |
| motif coverage | under half | 56% of 128 notes (needs 60%) |
| motif returns | 3 | 12 |
| hook cell | none | 6 notes repeated 5 times |
| steps over leaps | failing | 50% steps, 1 leap |
| leaps per motif | failing | 1, pass |
| range | failing | 17 semitones, pass |
| contour | failing | 2 of 12 returns arch or pedal |
| third return | copy | 67% the same, pass |
| loop length | 52 bars | 52 bars, still fails |

## 2. Ear, before and after (same judge, back to back)

| read | file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | `pp_01_title.mp3` | 7 | 5 | 6 | 3 | 7 | 6 | 33 |
| after | `pp_01_title_v6.mp3` | 6 | 4 | 5 | 3 | 6 | 5 | 29 |

Judge `gemini-3.5-flash-lite`, one call each, 23:11 UTC, reviews
`assets/audio/ear_reviews/pp_01_title_20261023T231122Z.md` and `..._v6_20261023T231128Z.md`.

**The ear went down 4 points, one point on every axis.** `assets/audio/EAR_SWEEP_2026-10-22.md`
puts the ear's own noise floor at 1 point per criterion, so this is a move at the floor, not a
signal; it is still the wrong direction and it is not claimed as a win. The review's own words do
not describe v6's build either: it says the drums "never vary in velocity or placement" and there
is "no delayed vibrato", while v6 has 270 noise hits across 2, 4 and 8 bar rungs with fills and
crashes, and the human pass put vibrato on 52 melody notes.

What the review does say that matters: the lead at bars 5 to 16 is "clean, perky and easy to hum"
but "lacks that one signature interval leap that turns a good tune into an earworm". That is the
opposite of the meter, which penalises leaps over 50% steps. The two measures disagree on this
cue, and Nayil's ear is the tiebreak.

## 3. What changed, and the measure for each

| change | measure | check |
| --- | --- | --- |
| the lead is twelve statements of the score's own two bar phrase, K then K2 (both are `score_v5.yaml` cells, no new material) | coverage under half to 56%, returns 3 to 12 | `hook_report_v6.json` |
| statement 3 (bars 9 and 10) opens its tail into a quarter, so the phrase returns changed | third return 67% the same, pass | `hook_report_v6.json` |
| the rhythm cell: dotted quarter then three eighths, the same in both bars | hook cell 6 notes repeated 5 times | `hook_report_v6.json` |
| the octave transposition in A prime is dropped (it is v5's, not the score's melody section) | range 17 semitones, pass; the motif no longer splits into two octaves | `build_report_v6.json` lead block |
| the kit is written bar by bar: 2 bar rung (hat density), 4 bar rung (open hat fill and a second kick), 8 bar rung (five hit tom run), crash into 13, 21, 29, 37, 45 | dpcm 101 hits, noise 270 hits over 4 noise pitches | `build_report_v6.json` kit block |
| the trio's cold half (bars 41 to 44) keeps one kick per bar and no hats | the 8 bar section line is audible as a texture change | builder `write_kit` |
| human pass: articulation on 89.3% of notes, vibrato on 52 melody notes, 21 breaths, 1 grace note, 1 mordent | `render_chip --humanize`, seed 20261021 | humanize block in the render log |

Only the lead and the kit were rewritten. Pulse 1 arpeggios, pulse 2 echo, vrc6 pulse b thirds,
vrc6 saw oom pah and the triangle bass are v5's notes, untouched, so no part is invented.

## 4. Form, tempo, loop

A minor, 3/4, 126 bpm (the card's 126 bpm family line, and `score_v5.yaml`'s own tempo), 52 bars,
74.286 s, loop from bar 5 to bar 52 as the score says. Nothing about the form changed.

`pp_01_title_v6_loop.json`: 52 bars, 3275997 samples, **seam sample difference 0**, peak -1.00
dBFS, RMS -17.15 dBFS, edge peak head 223. Edge peak tail is 0: the trim ends on the release of
the last held note, so the file's last millisecond is silence. The seam the game actually uses is
the bar 52 to bar 5 junction, which this measure does not reach; that is the check to run before
this replaces the master.

## 5. Rounds run

1. Baseline: v5 landed master, hook meter 73, ear 33.
2. v6 build 1: lead rewritten from the score's cells, kit written bar by bar, hook meter 83. Ear
   29. No further round: the ear was already at its floor and the meter's remaining failures
   (contour, loop length, coverage by 4 points) cannot be fixed without changing the form or the
   motifs, which the score owns.

Quota: two ear calls, both served by `gemini-3.5-flash-lite`, no model marked exhausted. The key
was read from HKCU\Environment inside the process, never printed, never written to a file.

## 6. Files

- `pp_01_title_v6.mid`, `pp_01_title_v6_humanized.mid`, `pp_01_title_v6.wav`, `.mp3`, `.ogg`
- `pp_01_title_v6_loop.json`, `hook_report_v6.json`, `build_report_v6.json`, `build_pp01_v6.py`

## 7. Q: for gamedev

Q: PP-01 still carries `"placeholder": true` in `data/audio.json` with `delivered_file`
`assets/audio/pp_01_title/pp_01_title.ogg`. v6 is not landed: landing it is a registry edit
(gamedev owns `data/audio.json`) and the ear read is down 4, so the call is yours or Nayil's,
not mine.
