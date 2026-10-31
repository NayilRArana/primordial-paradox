# PP-05 "Small Ship" v4, notes. Card AUTO-MUSIC-NEXT (t_8dea3cf6), written 2026-10-23 15:12 UTC.

The cue picked is PP-05 Small Ship because it is still the floor of the ear ledger after the v3
round: `data/ear_calibration.csv` has v3 at hook 6, drums 3, tension 4, human 2, variety 5,
structure 4, and v2 at hook 5, drums 3, tension 4, human 2, variety 6, structure 5, while every
other theme sits at 6 to 8 on hook. Its hook meter was 80 of 100.

v1 (`assets/audio/pp_05_small_ship/`), v2 (`assets/audio/pp_05_small_ship_v2/`) and v3
(`assets/audio/pp_05_small_ship_v3/`) are untouched. This folder is a new version suffix and every
file in it carries `_v4`.

## The score table, before and after

Same judge for every row of the comparison: `gemini-3.5-flash-lite`, one call per row, whole file,
back to back on 2026-10-23. The three v4 rows are the two build rounds of this card plus a
cross check on a second model.

| read | file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before, gate row 5 (v1) | `pp_05_small_ship.mp3` | 4 | 2 | 3 | 1 | 3 | 2 | 15 |
| before, v3 as judged today | `pp_05_small_ship_v3.mp3` | 6 | 4 | 5 | 3 | 7 | 5 | 30 |
| after, v4 round 1 | `pp_05_small_ship_v4.mp3` | 7 | 4 | 5 | 3 | 6 | 5 | 30 |
| after, v4 round 2 (this file) | `pp_05_small_ship_v4.mp3` | 6 | 4 | 5 | 3 | 7 | 5 | 30 |
| after, v4 on `gemini-3.5-flash` | `pp_05_small_ship_v4.mp3` | 7 | 4 | 5 | 3 | 6 | 5 | 30 |

Read this honestly: the ear judge does not separate v3 from v4. Three v4 reads and one v3 read on
the same judge all total 30, and the single point that moves (hook 7 versus 6 on the round 1 read)
moves back on the round 2 read, so it is read noise, not a win. The ear still names the same two
axes as weak on every read: human feel 3 and structure 5. What did move, repeatably, is the hook
meter and the structural facts below.

Hook meter (`tools/hook_score.py`, melody track `vrc6 pulse a`):

| file | score | returns | coverage | contour | leaps | range | loop |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pp_05_small_ship_v2.mid` | 58 / 100 | 2 | 19% | fail | 0 | 24 st | 24 bars |
| `pp_05_small_ship_v3.mid` | 80 / 100 | 5 | 58% | 0 of 5 arch | 2 | 24 st | 24 bars |
| `pp_05_small_ship_v4.mid` | 91 / 100 | 5 | 56% | 5 of 5 arch | 1 | 12 st | 24 bars |

Still failing on the meter in v4: loop length 24 bars (3 of 6 points), variation on the third
return (3.2 of 8: the meter finds five returns and compares return three, which is the bar 9
statement, against return one, and they are identical by design), and coverage 56% against a 60%
line.

## What changed, and the measure for each

| change | measure | check |
| --- | --- | --- |
| the hook is now an arch: bar 1 F4 C5 D5 C5 climbs to the peak, bar 2 Bb4 A4 G4 F4 falls, one leap (F4 to C5, 7 semitones) | contour 0 of 5 to 5 of 5 arch, leaps 2 to 1, hook meter 80 to 91 | `hook_report_v4.json` |
| the variation on the third return is rhythm, not an octave: bar 13 holds F4 and C5 as half notes, bar 14 turns the tail into quarters, and the octave up answers on bars 15 and 16 are gone | range 24 to 12 semitones (62 to 74), inside the meter's 18 | `hook_report_v4.json` |
| the arpeggio voice (was 384 sixteenths on the single pitch 62) is now a chord arpeggio per bar, root fifth third fifth | pitches 1 to 11 distinct, 316 notes, velocity arch per bar, swing opens from 6 to 20 ticks across the loop, drops out for the bridge and the last beat of bar 24 | `build_report_v4.json` arpeggio block |
| the kit is written bar by bar instead of one bar repeated | 2 bar rung (kick variant, hat density, ghost snares), 4 bar rung (snare fill on bars 4, 8, 12, 16, 20, 24), 8 bar rung (tom fill and open hat on 8 and 16, open hat into 9 and 17), bar 24 break; 223 noise and 158 dpcm hits, 5 noise pitches (hat, open hat, three toms) | `build_report_v4.json` kit block |
| drum human pass | 49 velocity steps on noise and 47 on dpcm, offbeat hats swung 8 to 14 ticks, backbeat slack on the kick and snare | `build_report_v4.json` kit block |
| the human pass | lead micro timing (notes that do not end on a bar line nudged up to 10 ticks later), vibrato depth shaped per phrase, bass vibrato onset delay 1 to 3 eighths | `build_report_v4.json` human block |
| tasteful dissonance, three devices from `knowledge/MUSIC-DISSONANCE.md` section 2 | C#5 as a chromatic approach on bars 8, 12, 16, 23, each resolving by step; the bar 19 suspension F (seventh of Gm) resolving F E D; a chromatic fall in the arpeggio at bar 12 into bar 13 | builder comments, `hook_report_v4.json` |
| structure | bass pocket on bar 17 (the saw drops out on beats 3 and 4), bass dropout on bar 24 beat 4, arpeggio out through bars 17 to 20 | `build_report_v4.json` bass and human blocks |
| tempo, key, form, loop | 96 bpm, D minor, 24 bars, 60.000000 s, seam sample difference 0, peak -1.00 dBFS, rms -19.41 dBFS | `pp_05_small_ship_v4_loop.json` |

## Tempo: the card's "126 bpm family" line

Unchanged at 96 bpm, same reason v2 and v3 recorded: `specs/12-audio.md` sets no tempo,
`knowledge/DEMO-SCRIPT.md` times the scene against a 60 s loop, and 60 s is exactly 24 bars at 96.
The one way to satisfy both the 126 family and the hook meter's 8/16/32 bar rule is 32 bars at
128 bpm, which is also exactly 60.000 s; that is a form rewrite plus a gamedev timing decision,
and it is recorded here rather than done quietly.

## Rounds run, and why the loop stopped at three

1. v3 read on `gemini-3.5-flash-lite` (30) and on `gemini-3.5-flash` (30): the baseline.
2. v4 round 1, `gemini-3.5-flash-lite` (30) and `gemini-3.5-flash` (30): the arpeggio and kit
   rewrite in, read unchanged.
3. v4 round 2, `gemini-3.5-flash-lite` (30): micro timing, bass vibrato delay, bar 17 pocket,
   progressive swing. Still 30.

The card allows four rounds. The third round changed nothing the judge can hear, so a fourth read
would spend free tier quota to measure noise. The model rotation was exercised for real:
`gemini-3.5-flash` answered 429 with the daily cap on the first call of the second comparison and
`gemini-3.5-flash-lite` answered instead; no key was printed and none was written.

## What is still weak, in the judge's own words

- Human feel (3 on every read). It asks for "natural envelope drift" and a lead-in on the first
  note. The renderer's envelope is a fixed linear decay per note; that is a `render_chip.py`
  change, not an arrangement one.
- Drums (4). It asks for a syncopated snare fill before the downbeat of bar 4, which is written
  (bars 4, 8, 12, 16, 20, 24 have a four sixteenth snare fill on beat 4) and it still reads the
  kit as rigid. The next lever is a different kick feel, not more fills.
- Structure (5). It calls the transitions abrupt. The bar 17 pocket and the bridge dropout did not
  move the score.
- Loop length. 24 bars fails the meter; 16 or 32 breaks the demo timing unless the tempo moves,
  which is a gamedev decision.
- Coverage 56% and the third return variation: both are meter artifacts of comparing return three
  (bar 9) with return one; fixing it means varying bar 9, which is the statement the listener
  learns first. Not worth the hook to win 11.8 points on a meter.

## Files here

| file | what it is |
| --- | --- |
| `build_pp05_v4.py` | the builder: reads v3's MIDI, rewrites the lead, the arpeggio and the kit, then the human touches |
| `pp_05_small_ship_v4.mid` | the arrangement, 835 notes across 8 voices (v3 was 841) |
| `pp_05_small_ship_v4.wav` / `.mp3` / `.ogg` | 44.1 kHz mono, 60.000000 s, peak -1.00 dBFS, rms -19.41 dBFS |
| `pp_05_small_ship_v4_loop.json` | the renderer's loop record, 24 bars, 2646000 samples, seam difference 0 |
| `build_report_v4.json` | hook, arpeggio, kit, bass and human blocks |
| `hook_report_v4.json` | the hook meter, 91 of 100 |

`data/audio.json` still points PP-05 at `assets/audio/pp_05_small_ship/` (v1), as it did through
v2 and v3: adopting a version into the game is a registry decision for another card, and changing
it here would move the cue the demo plays without a gate.

No key or login file was opened or written. `GEMINI_API_KEY` was read from the Windows user
environment (HKCU\Environment) into the process environment by a launcher in the card's workspace;
it was never printed and never written to disk.
