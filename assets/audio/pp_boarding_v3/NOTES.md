# PP-BOARDING v3, notes. Card AUTO-MUSIC-NEXT (t_329400a4), written 2026-10-25.

Clean room: every note here is written from the project's own knowledge files. Nothing is quoted
from any published game. `pp_boarding/` (v1) and `pp_boarding_v2/` are untouched; every file here
carries `_v3`.

## Why this cue

The newest ear row per cue was read from `data/ear_ledger.csv` (the score table script that built
this list is quoted at the bottom). Two cues tied on the floor at 30:

| cue | newest build | ear total of 60 |
| --- | --- | --- |
| PP-06 boarding | `pp_boarding_v2` | 30 raw, 31 on the humanized render |
| PP-04 fight, calm section | `pp_fight_v2_calm` | 30 (its fight section reads 32, so the cue is not the floor) |

Boarding was taken because its main section is the floor and its hook meter was already 100, so the
only headroom left is the ear's two low axes, which is what this card asks for. Fight's calm
section was built on 2026-10-24 and its loud section is 2 points above boarding.

## The score table, before and after

Same judge, same model, one call per row, whole file, back to back at 2026-10-25 11:28 and 11:29 UTC.
The v2 row is a fresh read, not yesterday's, because the ledger shows a 14 point swing between
models on the same file (`knowledge/EAR-LOOP-2026-10-24.md` section 3).

| read | file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before, v2 humanized | `pp_boarding_v2_humanized.mp3` | 6 | 4 | 4 | 3 | 6 | 5 | 28 |
| after, v3 | `pp_boarding_v3.mp3` | 7 | 5 | 5 | 4 | 6 | 6 | 33 |

Five points up, nothing down. `human 4` is the first 4 this project has been given on that axis by
`gemini-3.5-flash`; the 2026-10-22 sweep records no file above 4.

Reviews: `assets/audio/ear_reviews/pp_boarding_v2_humanized_20261025T112844Z.md` and
`assets/audio/ear_reviews/pp_boarding_v3_20261025T112920Z.md`.

Hook meter (`tools/hook_score.py`, melody track `vrc6 pulse a`): 100 / 100 before and after, 4
returns, 64 percent coverage, 1 leap, 4 of 4 arch returns.

## What changed, and the measure for each

| change | rule it answers | measure |
| --- | --- | --- |
| Two secondary dominants: E7 at bars 4 and 8, A7 at bar 11 resolving to Dm at 12, voiced in the guide (G#3/D4, C#4/G4) and the broken chord | the judge's first named ask, "no secondary dominants" | `build_report_v3.json` `chords` and `secondary_dominants` |
| DIS-02 chromatic upper neighbour, bar 10, guide: B4 on beat 3.5 resolving down a semitone to Bb4, the third of Gm | `knowledge/MUSIC-DISSONANCE.md` DIS-02, risk 1 | the note is in the MIDI at tick 9 bars + 5 eighths; rate 3 devices per 16 bars, inside DIS-02's 1 to 3 per 8 bars |
| DIS-06 suspension 9 to 8 over the E pedal, bar 13, guide: F#5 for half an eighth then E5 held for the bar | DIS-06, risk 2, dominant held two or more beats | same, tick at bar 13 |
| DIS-27 chromatic bass descent, bar 15, triangle: E4 Eb4 D4 C#4 C4 B3 Bb3 A3 in eighths, landing A3 a semitone from Bb3 at the stop | DIS-27, risk 2 | `build_report_v3.json` `dissonance`, triangle note count 60 |
| A real drop at bars 5 and 6: kit down to CLM-02 rim ticks, broken chord thin from eight notes to four, echo and guide quieter | the judge's "no sudden drop-out or quiet breakdown" | bar voice counts print from the builder: bars 5 and 6 lose the noise kit entirely, bar 9 gains MAR-13 |
| Bar 15 carries nothing but the descent (lead, saw, noise and broken chord silent), then the stop | same | builder prints 2 voices in bar 15, 8 in bars 9 to 12 |
| No sixteenth hat bar anywhere; 12 distinct patterns over 14 bars, 4 bar fills at 4, 8 and 12, the one crash at 9 | "relentless sixteenth-note hats" and drums 5 | `check_pp_boarding_v3.py` kit row |
| Per note velocity accents on the lead, delayed vibrato (CC20 3), gentler breath, renderer `--humanize` | human feel | 588 envelope points, 6 vibrato notes, 7 breaths, 1 grace note, 1 mordent |

Nothing else moved: 120 bpm, 16 bars, 32.000 s (31.813 s rendered), the 11 note hook A4 to E5, the
echo, the held breath, the stop, 8 voices, 412 notes.

### Two things that were tried and reverted, with the numbers

1. The chromatic neighbour and the 9-8 suspension were first written in the lead. Both cost hook
   meter points: the lead's third statement (bar 8) also had to be restored, because v2 states the
   hook at bars 1, 3, 5 and 7 and this build had replaced bar 8 with a deck figure. Measured: lead
   placements read 85 then 95 then 96 of 100 with 3 returns instead of 4. Moving both devices into
   the guide voice, which DIS-02 and DIS-06 both permit, restores 100 of 100 and keeps the devices
   audible. The lesson is in `lessons-inbox.md`.
2. Bar 11's answer was first rewritten to end on C#5 (the third of A7, a semitone under bar 12's
   D5). It cost a motif return, so it was reverted; the A7 is still heard through the guide's C#4
   and the broken chord.

## 2A03 plus VRC6, and the one shot

- 8 voices: 2A03 pulse 1, pulse 2, triangle, noise, DPCM; VRC6 pulse a, pulse b, saw. 412 notes.
- `render_chip.py --humanize`: 31.813 s, peak -1.00 dBFS, rms -15.18 dBFS, renderer v2, soft
  limiter. The render is bit-identical in peak and rms before and after the last CC change, so the
  ear verdict above belongs to this audio.
- One shot, no loop: the last 0.5 s measures peak 460 of 32768 (-37.1 dBFS) in a 0.25 s window at
  31.46 s, which is a renderer tail, not a note (the score is silent from beat 3 of bar 16). The
  check states the threshold it uses (-30 dBFS) rather than claiming digital silence.

## Rounds run

1. Round 1: the build plus the paired reads, v2 humanized 28 against v3 33 on `gemini-3.5-flash`.
   That is one round of the four the card allows; the card's 45 minute budget went to the build,
   the two reverted lead placements and the checks.

## What is still weak, in the judge's own words

- Variety (6, unchanged). The judge asks for timbre changes; this cue has no new instrument, only
  new levels.
- Hook (7). The meter says 100 and the ear says 7; the gap is the ear wanting a lyrical line, which
  would mean rewriting the hook that card CUE-BOARDING authored.

## Q for gamedev

1. **Which render ships.** v3 beats v2 on the ear by 5 points on the same model, so this lane
   recommends `assets/audio/pp_boarding_v3/pp_boarding_v3.mp3` replacing the v2 humanized render. It
   is not a registry cue, so the pointer lives in the boarding scene's data, which is not this
   lane's to edit.
2. **The leitmotifs.** K, Z, P and H are still absent by design: this cue was briefed as its own
   gangway theme. Adding one is one bar of work and changes its identity, so it stays gamedev's call.

## Key hygiene, reported because it happened

While reading `GEMINI_API_KEY` for the ear calls this session ran `reg query HKCU\Environment` and a
redaction pattern that assumed an `=` in the output. It did not match, so the listing printed the
values of `GEMINI_API_KEY`, `PINE_SANDBOX_API_KEY` and `KAGGLE_API_TOKEN` into the session log. No
key file was opened and nothing was written to disk by this card, but those three values should be
rotated, and the lane's habit of "read the key from the user environment" needs a command that
never echoes the value. Recorded in `lessons-inbox.md`.

## Files here

| file | what it is |
| --- | --- |
| `build_pp_boarding_v3.py` | the builder: v2's grid and hook, the new harmony, the kit ladder, the three devices, the thin bars, the accents |
| `pp_boarding_v3.mid` | the arrangement, 412 notes across 8 voices |
| `pp_boarding_v3.wav` / `.mp3` | 44.1 kHz mono, 31.813 s, peak -1.00 dBFS, rms -15.18 dBFS |
| `build_report_v3.json` | chords, kit, devices, per voice counts |
| `hook_report_v3.json`, `hook_report_render_v3.json` | 100 of 100, 4 returns, 64 percent coverage |
| `check_pp_boarding_v3.py` | the checks above, printed as a table |
| `tail_probe.py` | the last second's envelope, which is where the -37 dBFS figure comes from |
| `pp_boarding_v3_loop.json` | the renderer's report for the one shot trim |

The score table that picked this cue, and the one that now picks the next:

    python score_table.py     (in this folder)

It reads `data/ear_ledger.csv`: the latest summary row per file, then the highest version suffix per
cue family, sorted by total. Before this build the floor was boarding v2 at 30. After it, boarding
reads 33 and the floor is `pp_fight_calm` v2 at 30, with title v5, Percy v2, PP-05 v5 and arrival at
31. The next AUTO-MUSIC-NEXT card has its target.
