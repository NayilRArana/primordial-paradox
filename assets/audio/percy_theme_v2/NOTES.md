# PP-06 "Percy, Tyrant of the Harbor" v2, notes. Card AUTO-MUSIC-NEXT (t_80a0daa7), written 2026-10-23 19:10 UTC.

The cue picked is PP-06 Percy because it is the floor of the hook meter, not of the ear:
`tools/hook_score.py` read **61 of 100** on v1, the lowest of the nine cues in
`assets/audio/`, with no rhythm cell, 22 percent motif coverage, 20 percent steps, 0 leaps
and a 31 semitone range. Every other cue of the project sits at 73 and above. The ear ledger
had it at 33 with `gemini-3.5-flash` on 2026-10-22, mid table, so the deficit was the melody
grammar and this card is the one that measures it.

v1 (`assets/audio/percy_theme/`) is untouched. This folder is a new version suffix and every
file in it carries `_v2`.

## The score table, before and after

Same judge for both rows: `gemini-3.5-flash-lite`, one call per row, whole file, back to back
on 2026-10-23 19:06 and 19:07 UTC. v2 was read twice (`19:0649` and `19:0701`) and returned the
same six numbers both times, so this read is repeatable, not one sample.

| read | file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before (v1) | `percy_theme.mp3` | 5 | 3 | 4 | 2 | 6 | 5 | 25 |
| after (v2) | `percy_theme_v2.mp3` | 6 | 4 | 5 | 3 | 7 | 6 | 31 |

Six points up, every axis up by one and none down. Do not compare the v1 row against the 33
in `data/ear_ledger.csv`: that row was `gemini-3.5-flash`, and `knowledge/EAR-LOOP-2026-10-24.md`
records a 14 point swing between models on the same file. The before row here was re-measured
on the same model as the after row for exactly that reason.

Hook meter (`tools/hook_score.py`, melody track `vrc6 pulse a`), the check this card is about:

| file | score | returns | coverage | contour | leaps | range | hook cell | third return |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `percy_theme.mid` (v1) | 61 / 100 | 3 | 22% | 3 of 3 arch | 1 | 31 st | none | 100% copy |
| `percy_theme_v2.mid` (v2) | 91 / 100 | 10 | 73% | 1 of 10 arch | 1 | 8 st | 6 notes, x12 | 80% the same |

## What changed, and the measure for each

| change | measure | check |
| --- | --- | --- |
| the lead is one phrase, P2, stated fourteen times: bar 1 climbs G4 A4 D5 (one leap, A4 to D5) then C5 Bb4, bar 2 walks A4 G4 to F#4 | score 61 to 91, coverage 22 to 73 percent, returns 3 to 10 | `hook_report_v2.json` |
| the rhythm cell: six eighths then three quarters, the same two bars every statement | hook cell 0 to 10 of 10 (6 notes, rhythm 2/2/2/2/2/2 twelve times) | `hook_report_v2.json` |
| the motif is 7 steps of 8 intervals with the single leap at the crest | steps 20 to 88 percent, leaps 0 to 1 in the returned motif | `hook_report_v2.json` |
| the third statement (bars 9 and 10) opens its rhythm and holds Bb, so the phrase returns changed | third return 100 percent copy to 80 percent the same | `hook_report_v2.json` |
| the melody sits inside F#4 to D5 instead of G3 to A5 | range 31 to 8 semitones | `build_report_v2.json` lead block |
| the kit is written out bar by bar instead of one bar repeated: 130 noise hits and 60 dpcm hits over 5 noise pitches | before 28 noise and 42 dpcm on one bar of pattern | `build_report_v2.json` kit block |
| drum human pass: 7 velocity steps on noise, 5 on dpcm, offbeat hats and fills nudged off the grid | deterministic, seeded by hit index | `build_report_v2.json` kit block |
| chromatic approach: C#5 on bar 12 resolves to D5 on the downbeat of 13, the seventh of the chord under it (`knowledge/MUSIC-DISSONANCE.md`, chromatic approach and resolution by step) | one device, three notes | builder comments |
| structure: intro bars 1 to 4 have no lead at all (P2 arrives at bar 5), B bars 13 to 20 thin to hats on beats 2 and 3 with no backbeat, the cadence stops the backbeat on bar 32 for a three hit snare close | sections differ in kit, not only in melody | `build_report_v2.json` |

## Tempo: the card's "126 bpm family" line, and why this cue keeps 132

Unchanged at 132 bpm, 3/4, G minor, 32 bars, 43.636 s. The tempo, key, time and form come from
`data/audio.json` PP-06 ("G minor tyrant waltz, 32 bars") and from the cue's own card MUS-PERCY,
which wrote it `score_percy.yaml`; the boss scene is timed against that 43.636 s loop. Under the
chain of command in this card, a gamedev spec is not overridden by a balancer line, so the choice
here is recorded instead of taken quietly.

Q: for gamedev: is the "126 bpm family" line meant to hold for the boss cue too? If yes, the
change is 32 bars at 126 bpm = 45.7 s, and the boss scene length has to move with it.

## What is still weak

Contour, 1 of 10 returns arch. The phrase itself is an arch (bar 1 up to D5, bar 2 down to F#4),
but the meter tests every 2 bar window that is 60 percent similar to it, and the windows that
start on a descending bar read as two turns (down, up, down). Fixing it means making each window
self contained, which costs the descent that gives the phrase its pull; it is worth a round only
if the ear stops moving. Human feel is still 3, the same ceiling every tracker render in this
project hits, per `assets/audio/EAR_SWEEP_2026-10-22.md`.

## Rounds run

1. Baseline (v1) on `gemini-3.5-flash-lite`: 25. Read at 19:07 UTC.
2. v2 build 1: lead rewritten, kit written out, hook meter 61 to 86. Ear read 31, twice.
3. v2 build 2: the leap moved from Bb4 to D5 up to A4 to D5 so it clears the grammar's 5 semitone
   line, hook meter 86 to 91. No ear call spent on it: the meter is the measure that moved and the
   ear had already answered twice with the same six numbers.

Quota was never hit: all three ear calls returned on `gemini-3.5-flash-lite` and no model was
marked exhausted. The key stayed in the process environment (read from HKCU\Environment) and was
never printed or written.

## Files

- `percy_theme_v2.mid`, `percy_theme_v2.wav`, `percy_theme_v2.mp3`, `percy_theme_v2.ogg`
- `percy_theme_v2_loop.json`: 32 bars, 1924362 samples, seam sample difference 0, peak -1.00 dBFS
- `hook_report_v2.json`, `build_report_v2.json`, `build_percy_v2.py`
- reviews: `assets/audio/ear_reviews/percy_theme_20261023T190719Z.md` (v1, before) and
  `assets/audio/ear_reviews/percy_theme_v2_20261023T190649Z.md` (v2, after)
