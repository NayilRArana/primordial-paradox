# PP-05 "Small Ship" v3, notes. Card AUTO-MUSIC-NEXT (t_75f72db4), written 2026-10-23 11:03 UTC.

The cue picked is PP-05 Small Ship because it is the floor of the ear ledger: `data/ear_ledger.csv`
has it at hook 5, drums 3 to 4, tension 4 to 5, human 2 to 3, variety 6, structure 5 (two reads,
2026-10-23 05:34 and 05:38 UTC), and `assets/audio/EAR_SWEEP_2026-10-22.md` plus
`knowledge/EAR-GATE-2026-10-23.md` row 5 rank it lowest of the slice (total 15 on the gate's read).
Its hook meter was 58 of 100.

v1 (`assets/audio/pp_05_small_ship/`) and v2 (`assets/audio/pp_05_small_ship_v2/`) are untouched.
This folder is a new version suffix and every file in it carries `_v3`.

## The score table, before and after

Same judge for every row: `gemini-3.5-flash-lite`, one call per row, whole file.

| read | file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before, gate row 5 | `pp_05_small_ship.mp3` (v1) | 4 | 2 | 3 | 1 | 3 | 2 | 15 |
| before, v2 read 1 | `pp_05_small_ship_v2.mp3` | 5 | 4 | 5 | 3 | 6 | 5 | 28 |
| before, v2 read 2 | `pp_05_small_ship_v2.mp3` | 5 | 3 | 4 | 2 | 6 | 5 | 25 |
| after, v3 round 1 (fuller lead) | `pp_05_small_ship_v3.mp3` | 5 | 4 | 3 | 2 | 5 | 4 | 23 |
| after, v3 round 2 read 1 | `pp_05_small_ship_v3.mp3` | 6 | 4 | 5 | 3 | 6 | 5 | 29 |
| after, v3 round 2 read 2 | `pp_05_small_ship_v3.mp3` | 6 | 3 | 4 | 2 | 5 | 4 | 24 |

Read this honestly: the two v3 reads (29 and 24) and the two v2 reads (28 and 25) overlap, so the
ear judge does not separate them. The one axis that moved in both v3 reads is hook, 5 to 6, and
round 1 showed why the loop matters: giving the lead a note in every bar scored 23, thinning the
bars between statements to two notes and a rest scored 29 on the first read. The hard evidence for
this round is the hook meter, not the judge.

Hook meter (`tools/hook_score.py`, melody track `vrc6 pulse a`):

| file | score | returns | coverage | third return | contour |
| --- | --- | --- | --- | --- | --- |
| `pp_05_small_ship_v2.mid` | 58 / 100 | 2 | 19% | no third return | fail |
| `pp_05_small_ship_v3.mid` | 80 / 100 | 5 | 58% | 55% the same, pass | fail |

Still failing on the meter in v3: contour 0 of 10 (the returns are not an arch or a pedal), range 24
semitones because of the octave-up statement, two leaps per motif where the ideal is one, and loop
length 24 bars where the meter wants 8, 16 or 32.

## What changed, and the measure for each

| change | measure | check |
| --- | --- | --- |
| the hook: one 2 bar phrase, A4 D5 C5 Bb4 A4 then F4 Bb4 A4 G4 F4, stated at bars 1, 5, 9, 13, 17, 21 | lead notes 43 to 89, motif returns 2 to 5, coverage 19% to 58% | `hook_report_v3.json` |
| the third return varied (bars 13 and 14 an octave up) | variation on the third return 0 to 55%, inside the meter's 30 to 85% band | `hook_report_v3.json` |
| the bars between statements breathe (two notes and a rest per bar) | lead 114 notes in round 1 to 89 in round 2, ear 23 to 29 | ledger rows 11:01 and 11:02 UTC |
| prepared dissonance, one device | F4 is the fifth of Bb at bar 18 and the seventh of Gm at bar 19, resolving F E D by step | `build_report_v3.py` hook block, `knowledge/MUSIC-DISSONANCE.md` section 2 |
| the kit: v2's 4 bar and 8 bar rungs kept, then 12 ghost snares on the answer bars, 27 swung offbeat hats, hit by hit velocity spread | noise 36 velocity steps from 1, dpcm 48 to 63 notes | `build_report_v3.json` kit block |
| the human pass | vibrato and articulation from `tools/humanize.py`, plus the onset nudges above | `build_report_v3.json` |
| tempo, key, form and the loop | 96 bpm, D minor, 24 bars, 60.000 s, loop seam sample difference 0 | `pp_05_small_ship_v3_loop.json` |

## Tempo: the card's "126 bpm family" line

Unchanged at 96 bpm, same reason v2 recorded: `specs/12-audio.md` sets no tempo, `knowledge/DEMO-SCRIPT.md`
times the scene against a 60 s loop, and 60 s is exactly 24 bars at 96. The 126 family belongs to the
waltz and the drive. Flagged, not silently changed.

## What is still weak, in the judge's own words

- Human (2 to 3). The critic keeps asking for delayed vibrato and for swing on the arpeggios. The
  vibrato is written per two bar phrase by `humanize.py`; onsets are nudged here but the arpeggio
  voice (pulse 2) is not swung, which is the next real gain.
- Structure (4 to 5). The critic asks for a bass drop out on bar 24 beat 4. The saw holds one note
  per bar, so a dropout is a change to the bass voice, not a mix move.
- Contour (0 of 10 on the hook meter). The returns need to be shaped as an arch; that is the next
  rewrite of the phrase, not a mix change.
- Loop length. 24 bars fails the meter, and 16 or 32 breaks the 60 s demo timing; it is a gamedev
  timing decision, not mine.

## Files here

| file | what it is |
| --- | --- |
| `build_pp05_v3.py` | the builder: v1's MIDI through v2's three functions, then the hook rewrite and the kit human pass, then `tools/humanize.py` |
| `pp_05_small_ship_v3.mid` | the delivered arrangement, 721 notes across 8 voices |
| `pp_05_small_ship_v3.wav` / `.mp3` / `.ogg` | 44.1 kHz mono, 60.000000 s, peak -1.00 dBFS, rms -20.06 dBFS |
| `pp_05_small_ship_v3_loop.json` | the renderer's loop record, 24 bars, 2646000 samples, seam difference 0 |
| `build_report_v3.json` | hook block, kit block, humanize report, notes per change |
| `hook_report_v3.json` | hook meter, 80 of 100 |

No key or login file was opened or written. `GEMINI_API_KEY` was read from the Windows user
environment by a launcher in the card's workspace and passed to `tools/ear_critic.py` through the
process environment; it was never printed and never written to disk.
