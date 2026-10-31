# PP-05 "Small Ship" v5, notes. Card AUTO-MUSIC-NEXT (t_cb333899), written 2026-10-25.

The cue picked is PP-05 Small Ship because it is the floor of the current versions in
`data/ear_ledger.csv`: v4 read 29 (hook 6, drums 4, tension 5, human 3, variety 6, structure 5) on
`gemini-3.5-flash` and 30 on `gemini-3.5-flash-lite`, and every other current cue is at 31 or
above (Percy v2 31, Boarding v2 30 with a fresh v2 build behind it, Fight v2 30, Arrival 31,
Harbor v4b 35, Drive v4 32, Navy v3 32, Title v8 37). Both current weak cues sit on the same hook
meter read of 91, so the ear decided it.

v1 (`pp_05_small_ship/`), v2, v3 and v4 are untouched. This folder is a new version suffix and
every file in it carries `_v5`.

## The score table, before and after

Same judge for both rows: `gemini-3.5-flash`, one call per row, whole file, back to back on
2026-10-25 07:26 UTC. The v4 row was re-read today, not reused, because the earlier v4 reads were
on mixed models and `knowledge/EAR-LOOP-2026-10-24.md` records a 14 point swing between models on
the same file.

| read | file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before, v4, read today | `pp_05_small_ship_v4.mp3` | 6 | 4 | 5 | 3 | 6 | 5 | 29 |
| after, v5 | `pp_05_small_ship_v5.mp3` | 7 | 4 | 5 | 3 | 6 | 6 | 31 |

Two points up, on hook and structure, nothing down. Human feel stays at 3, which is the same
number every tracker render in this project has ever been given (see the hearing in
`assets/audio/EAR_SWEEP_2026-10-22.md`: no file in the set scored above 4, so that axis is
measuring "is this a tracker at all"). Drums stay at 4.

Hook meter (`tools/hook_score.py`, melody track `vrc6 pulse a`):

| file | score | bars | returns | coverage | contour | range | loop |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pp_05_small_ship_v3.mid` | 80 / 100 | 24 | 5 | 58% | 0 of 5 arch | 24 st | 24 bars, fails |
| `pp_05_small_ship_v4.mid` | 91 / 100 | 24 | 5 | 56% | 5 of 5 arch | 12 st | 24 bars, fails |
| `pp_05_small_ship_v5.mid` | 94 / 100 | 32 | 7 | 55% | 7 of 7 arch | 14 st | 32 bars, passes |

The three points are the loop length criterion, which v4 could not win without breaking the
demo timing. That is what this version buys.

## What changed, and the measure for each

| change | measure | check |
| --- | --- | --- |
| tempo 96 to 128 bpm, the cue now sits in the 126 family | every note keeps its tick position, so the 24 bars of v4 play in 45 s instead of 60 s | `build_report_v5.json` `tempo_bpm` 128.0, `pp_05_small_ship_v5_loop.json` bpm 128.0 |
| form 24 to 32 bars, a new eight bar section (25 to 32) fills the freed 15 s | loop length passes the meter's 8/16/32 rule, and 32 bars at 128 bpm is exactly 60.000 s, the length `knowledge/DEMO-SCRIPT.md` times the scene against | hook report loop length 6.0 of 6; render duration 60.000 s |
| the hook is restated in pitch at bars 25, 29 and 30, so the motif is heard seven times instead of five | returns 5 to 7, contour 5 of 5 to 7 of 7 arch | `hook_report_v5.json` |
| the development: bars 25 to 28 are half time (kick on beats 1 and 3, snare on beat 3 only), pulse 2 rests on bars 27 and 28, pulse 1 climbs G3 A3 Bb3 B3 C#4 D4 E4 G4, then the reprise lands at bar 29 | structure 5 to 6 on the ear; 16 inner voice notes added, 12 arpeggio notes a bar on six of the eight new bars | `build_report_v5.json` `inner_voice`, `arpeggio`, `kit.half_time_section` |
| the kit is written out over all 32 bars with four rungs, not only the 4 and 8 bar fills v4 had | 2 bar rung 16 groups, 4 bar rung 8, 8 bar rung 4, 16 bar rung 2; 308 noise and 207 dpcm hits, 49 and 50 velocity steps, 5 noise pitches | `build_report_v5.json` `kit` |
| tasteful dissonance, three devices, each prepared and each resolved by step, none on the first or last note of a statement (rule F1 of `knowledge/MUSIC-DISSONANCE.md`) | bar 26 C5, the 9th of Bb, held and resolved to Bb4 (9-8 suspension); bar 27 D5, the 11th of A7, resolved down to C#5 (11-3); bar 28 D5 as the upper neighbour of C#5, resolved on the fourth eighth; the chromatic climb on pulse 1 is the preparation for all three | builder comments, `build_report_v5.json` `lead.dissonance` |
| humanize | lead micro timing on 10 of the new notes, vibrato depth 9 on the development and 11 on the reprise, hat swing 8 to 14 ticks, backbeat slack 0 to 6 ticks | `build_report_v5.json` `human`; `render_chip.py --humanize` pass |

## 2A03 plus VRC6, and the loop

- 8 voices written: 2A03 pulse 1, pulse 2, triangle, noise, DPCM; VRC6 pulse a, pulse b, saw.
  1130 notes. The builder refuses a note past the loop point and writes nothing in a channel that
  already holds a note on the same tick.
- `render_chip.py --loop-bars 32 --humanize`: 60.000000 s, 2646000 samples, peak -1.00 dBFS,
  rms -19.50 dBFS, renderer v2, soft limiter, seam sample difference 0.
- `check_seam_v5.py pp_05_small_ship_v5.wav 32 128`: loop point sample 2646000 (60.0000 s), seam
  jump 0, last sample of the loop 0, first sample 0, 0 samples of tail beyond the loop point.

## Tempo: the card's "126 bpm family" line, now satisfied

v2, v3 and v4 all recorded that the 126 family and the hook meter's 8/16/32 bar rule could only be
met together by 32 bars at 128 bpm, which is exactly 60.000 s, and that this was a gamedev timing
decision rather than a musician one. Nothing in `specs/` pins a tempo for PP-05 (grep of
`specs/*.md`, 2026-10-25), the card that asked for it is this one, and the demo timing is
preserved to the sample, so the change is made here and recorded rather than assumed: the cue is
now 32 bars at 128.0 bpm, 60.000 s, and both rules hold at once. If gamedev wants the 96 bpm feel
back, v4 is untouched.

## Rounds run

1. v4 read today on `gemini-3.5-flash` (29) and v5 read on the same model (31): the build, the
   tempo, the form and the new section in one pass. Hook meter 91 to 94.
2. Not run. The card allows four rounds; the budget for this card was 45 minutes and one build
   round plus two paired ear reads used it. The next lever, if a later card picks this cue up, is
   the one the judge keeps naming: human feel, which is a `render_chip.py` envelope question (a
   fixed linear decay per note), not an arrangement one, and drums, which has been written out
   bar by bar in v4 and again here without the number moving.

## What is still weak, in the judge's own words

- Drums (4). Every fill the judge asks for is already written, including the syncopated snare
  before the downbeat. It still reads the kit as rigid. The next lever is a different kick feel,
  not more fills.
- Human feel (3). Same read for v1 through v5.
- Hook meter, coverage 55% against 60%, and the third return read as a copy. The meter compares
  its third detected occurrence against the first; every rhythm variation tried on the early
  statements (bars 9 and 10 were rewritten and reverted during this build) either drops an
  occurrence or leaves the segment identical in pitch, and both outcomes cost more than they pay.
  Measured, not guessed: the reverted attempt read 91 with 6 returns and 48% coverage.

## Files here

| file | what it is |
| --- | --- |
| `build_pp05_v5.py` | the builder: reads v4's MIDI, sets 128 bpm, writes bars 25 to 32 on all voices, rewrites the kit for 32 bars, adds the human pass |
| `pp_05_small_ship_v5.mid` | the arrangement, 1130 notes across 8 voices (v4 was 835) |
| `pp_05_small_ship_v5.wav` / `.mp3` / `.ogg` | 44.1 kHz mono, 60.000000 s, peak -1.00 dBFS, rms -19.50 dBFS |
| `pp_05_small_ship_v5_loop.json` | the renderer's loop record, 32 bars, 128.0 bpm, 2646000 samples, seam difference 0 |
| `build_report_v5.json`, `hook_report_v5.json`, `hook_report_render_v5.json` | the measurements the table above cites |
| `check_seam_v5.py` | the independent seam check |
