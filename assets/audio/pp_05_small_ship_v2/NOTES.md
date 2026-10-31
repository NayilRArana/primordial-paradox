# PP-05 "Small Ship" v2, notes. Card AUTO-MUSIC-NEXT (t_e4bc0cf6), written 2026-10-23 05:40 UTC.

v1 lives untouched in `assets/audio/pp_05_small_ship/`; nothing there was written by this card. v2 is a
new version suffix folder, `assets/audio/pp_05_small_ship_v2/`, and every file in it carries the `_v2`
suffix.

The cue this card picks is PP-05 Small Ship, because R35's gate file
(`knowledge/EAR-GATE-2026-10-23.md` row 5) scored it lowest in the slice: total 15 on
`gemini-3.5-flash-lite` against 29 to 35 for the rest, and the gate ranked its fix first at 6.0 points per
hour. The other low rows in that table (the drive and the harbor) were worked in t_f1692c31 and t_14c42859;
the ship was the remaining floor.

## The score table, before and after

Same judge for both columns: `gemini-3.5-flash-lite`, one call per row. Before is
`assets/audio/ear_reviews/pp_05_small_ship_20261023T020546Z.md`; after is the two v2 rows below, because
the same judge gave the same file two reads three minutes apart and they differ by 3 points, which is the
sweep's own noise floor applied across three criteria.

| read | file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before, gate row 5 | `pp_05_small_ship.mp3` | 4 | 2 | 3 | 1 | 3 | 2 | 15 |
| after, first call 05:34 UTC | `pp_05_small_ship_v2.mp3` | 5 | 4 | 5 | 3 | 6 | 5 | 28 |
| after, second call 05:38 UTC | `pp_05_small_ship_v2.mp3` | 5 | 3 | 4 | 2 | 6 | 5 | 25 |

So the measured change is +10 to +13 on the same judge, and it is a gain on all six axes in both reads.
Which individual criteria are real: variety 3 to 6 and structure 2 to 5 are outside the noise floor in
both reads, and pulse 1 stops being silent by construction. Drums 2 to 3 or 4 and human 1 to 2 or 3 are
inside one read's noise, so read them as direction, not measurement. The judge is explicitly a rough
listener (it writes "no velocity variance" over a MIDI that now carries 11 to 37 distinct velocity steps
per voice), and the review's bar numbers are its own estimate, not the score's.

Hook meter (`assets/audio/pp_05_small_ship_v2/hook_report_v2.json`): 58 of 100, unchanged from v1
(`hook_report.json`), weakest item motif coverage 19 percent. This card did not rewrite the melody, so the
hook meter could not move; the gate's fix 5 was about thinness, not about the tune.

## What changed, and the measure for each

| change | measure before to after | check |
| --- | --- | --- |
| pulse 1 counterline over bars 17 to 20 at chip level 5 | 0 notes to 10 notes on pulse 1, control change 11 raised from 0 to 5 | `check_v2.py` |
| noise kit raised from level 3 to level 6 | control change 11 3 (2 in the close) to 6 (4 in the close), velocities times 1.6 | `check_v2.py` |
| drum variation rung every 4 bars, longer every 8 | noise 80 to 125 notes, dpcm 48 to 51, noise gets 37 velocity steps from 1 | `check_v2.py` |
| human pass | vibrato events 0 to 86 on the lead, velocity steps 1 to 11 on the lead | `check_v2.py` |
| no tempo, key, form or v1 note change | tempo 625000 us unchanged, division 480, 24 bars, 60.000 s | `check_v2.py` |
| loop seam | `loop_seam_sample_difference` 0, loop 0 to 2646000 samples | `check_v2.py`, loop json |

The drum ladder is by bar number, so it changes at a 4 bar rung and again at an 8 bar rung: bars 5 to 8
and 13 to 16 carry an added backbeat snare and offbeat hats, bars 4, 8, 12, 16, 20 and 24 carry a one beat
noise fill, and bars 8, 16 and 24 carry a longer four hit fill, which is the one bar 24 fill that leads the
wrap back into bar 1. Bars 9 to 12 and 21 to 24 keep v1's plain kit on purpose, so the kit has contrast
rather than uniform busier.

The counterline is built only from chord tones of the chords v1 already writes (Dm Bb Gm A7 over bars 17 to
20), with one prepared dissonance: F4 over Gm at bar 19 is the seventh, and it resolves by step to E4 over
A7 at bar 20 (`knowledge/MUSIC-DISSONANCE.md` section 2, preparation then dissonance then resolution). That
keeps the chromatic budget of the cue where v1 left it, one named device, inside the 3 to 6 percent band.

## Tempo: the card's "126 bpm family" line

This cue stays at 96 bpm 4/4 and the change is deliberate. `specs/12-audio.md` sets no tempo for any cue,
the cue's own card set 96 as a bed under a 32 s boarding scene plus a walk plus the log save, and
`knowledge/DEMO-SCRIPT.md` times the scene against a 60 s loop, which is exactly 24 bars at 96. Moving it to
126 would change the loop length to 45.7 s and break that timing. The 126 family is the waltz and the
drive. Flagged here rather than silently changed.

## What is still weak, by the same judge's own words

- Drums: the review still calls the kit a metronome. The variation is 4 and 8 bar rungs now, but the home
  pattern inside a rung is unchanged from v1, so the next step is a kit swap (a `CLM` pattern from
  `data/drum_patterns.json` instead of the hadrian set's fixed hats and kick) rather than more fills.
- Human: the critic asks for delayed vibrato on phrase ends and a swing on the bass eighths. `humanize.py`
  writes vibrato per two bar phrase and articulation, but note onsets stay on the grid; micro-timing on the
  triangle is the next real gain and it is a change to `tools/humanize.py`, which other cues share.
- Tension: the critic asks for a sus4 on the saw. The saw carries one note per bar and a sus4 there would
  beat against the hum; the honest fix is the tritone stab the gate already queued for the title cue, so it
  is not in this card.

## Files here

| file | what it is |
| --- | --- |
| `build_pp05_v2.py` | the builder: reads v1's MIDI, adds the counterline, raises the kit, writes the rungs, then runs `tools/humanize.py` |
| `check_v2.py` | the checks above, printed as a table, exits 0 only on all pass |
| `pp_05_small_ship_v2.mid` | the delivered arrangement, 669 notes across 8 voices |
| `pp_05_small_ship_v2.wav` / `.mp3` / `.ogg` | 44.1 kHz mono, 60.000000 s, peak -1.00 dBFS, rms -19.90 dBFS, loop 24 bars |
| `pp_05_small_ship_v2_loop.json` | the renderer's loop record, seam difference 0 |
| `build_report_v2.json` | the builder's own numbers: notes per change, rung map, humanize report |
| `hook_report_v2.json` | hook meter, 58 of 100 |

No key or login file was opened or written. `GEMINI_API_KEY` was placed in the process environment from
the Windows user environment by a scratch launcher, never printed and never written to disk.
