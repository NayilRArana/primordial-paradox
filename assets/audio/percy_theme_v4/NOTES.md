# PP-06 "Percy, Tyrant of the Harbor" v4, notes. Card AUTO-MUSIC-NEXT (t_7f331a39), 2026-10-26.

## Which cue, and why this one

The floor of the score table at the start of this card was `ref_fight` at 29 (a reference file, not a
cue) and `pp_fight_fight` v6 at 30, and that row had just been rebuilt an hour earlier (t_7417cbca).
The lowest row that no round had touched since its own build was `percy_theme` at 31, last read
2026-10-23, and it is a shipped cue: the PP-06 row of `data/audio.json` names `percy_theme` as the
tyrant waltz, and the boss scene plays it. Its own v2 notes had already named the one number it left
unfixed and set the condition for another round: contour, 1 of 10 returns arch, "worth a round only
if the ear stops moving". The ear had stopped moving (v2 read 31 on 2026-10-23 and 30 on a paired
re-read today, and four pp_fight rounds between them landed 29, 30, 30, 31).

## The score table, before and after

Same script, `score_table.py`, over `data/ear_ledger.csv`. Model swing between rows is the reason
every paired read below was taken back to back on one model.

| read | file | model | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before, table row | `percy_theme_v2.mp3` (2026-10-23) | flash-lite | 6 | 4 | 5 | 3 | 7 | 6 | 31 |
| before, paired today | `percy_theme_v2.mp3` | flash-lite | 5 | 4 | 6 | 3 | 7 | 5 | 30 |
| v3, paired today | `percy_theme_v3.mp3` | flash-lite | 6 | 3 | 5 | 2 | 7 | 5 | 28 |
| after, paired today | `percy_theme_v4.mp3` | flash-lite | 7 | 4 | 5 | 3 | 6 | 5 | 30 |
| before, paired today | `percy_theme_v2.mp3` | flash | 7 | 3 | 5 | 3 | 6 | 6 | 30 |
| v3, paired today | `percy_theme_v3.mp3` | flash | 7 | 5 | 6 | 4 | 7 | 7 | 36 |
| after, paired today | `percy_theme_v4.mp3` | flash | 7 | 4 | 6 | 4 | 7 | 6 | 34 |

`gemini-3.5-flash` answered 503 UNAVAILABLE on three tries between 13:40 and 13:47 UTC and
`gemini-3.7-flash` and `gemini-3.8-flash` the same (3.8 also timed out once), so the v4 row on flash
was written at 14:00 UTC on the fourth attempt, after the two v2 and v3 flash rows above. Read across
both models, v4 is 32 against v2's 30 (34 against 30 on flash, 30 against 30 on flash-lite), and v3,
which is v4 without the kit pass, is 32 as well (36 and 28). The delivered file therefore claims a
hook gain measured deterministically and an ear gain on one of the two models that answered, and it
records that the other model did not move.

## The hook meter, the measure that did move

`tools/hook_score.py`, melody track `vrc6 pulse a`, same 32 bars, same key, same tempo.

| file | score | contour | motif coverage | returns | range |
| --- | --- | --- | --- | --- | --- |
| `percy_theme.mid` (v1) | 61 / 100 | 3 of 3 arch | 22% | 3 | 31 st |
| `percy_theme_v2.mid` | 91 / 100 | 1 of 10 arch or pedal | 73% | 10 | 8 st |
| `percy_theme_v3.mid` | 99 / 100 | 9 of 10 arch or pedal | 76% | 10 | 8 st |
| `percy_theme_v4.mid` | 99 / 100 | 9 of 10 arch or pedal | 76% | 10 | 8 st |

That is the fix v2 declined. The meter scores every 2 bar window and a bar that descends into the
next bar's rise reads as two turns, so the second bar of the phrase is now a HELD PEDAL, F#4 (the
leading tone, the pull into the next statement) or G4 (the tonic, a local close). Thirteen of the 24
lead bars now hold one pitch. The head bar, the crest, the one leap and the third-return variation
are v2's, unchanged. The one window still failing is bars 29 to 30, where the wave at its height
(`C5 D5 D5`) is kept on purpose: a pedal there would read as a pedal at the cost of the cue's crest.

At 99 of 100 the meter can no longer rank this cue against the others: it is at its ceiling, so the
ear is the only judge left for it.

## What v4 adds to the kit, and the measure for each

| change | measure | where |
| --- | --- | --- |
| ghost notes under the offbeat in A and A2, 34 to 47 velocity, differently placed on every bar | 22 of the 49 snare hits sit at 56 velocity or below | `check_percy_v4.py` |
| a flam into the beat 2 snare before bars 13, 21 and 29 | 2 grace hits landed (the third was moved by the human pass) | `check_percy_v4.py` |
| snare late, kick early, the push eighth late | dpcm onsets land at 10, 16, 221 and 235 ticks against the 0 tick grid | `check_percy_v4.py` |
| a crescendo over bars 31 and 32 into the loop point | hat and snare velocities rise 8 and 14 (hat), 6 and 12 (kit) before the human pass | `build_report_v4.json` |
| v2's 2, 4 and 8 bar rungs, kept | 142 noise hits over 5 pitches, 82 dpcm hits, open hat into 13 and 29, six hit tom fill on the 8 bar line | `build_report_v4.json` |

## What is unchanged, and the Q: that stands

Key (G minor), time (3/4), 132 bpm, 32 bars, 43.636327 s, and the loop point are v2's. Spec 12 and
the PP-06 row of `data/audio.json` pin the tyrant waltz and the boss scene is timed against that
length. The card's "126 bpm family" line stays the Q: v2 already opened for gamedev rather than
overriding a gamedev spec (chain of command, 2026-10-22).

Dissonance: v2's one chromatic approach (C#5 in bar 12) is kept and no device is added. This round is
the phrase shape and the kit; `knowledge/MUSIC-DISSONANCE.md` risk 2 and 3 devices need a round of
their own to place and audit.

## Checks

`python assets/audio/percy_theme_v4/check_percy_v4.py`: 11 of 11 PASS.

| check | result |
| --- | --- |
| files, new suffix | 5 of 5 (mid, wav, mp3, ogg, loop json) |
| v1, v2, v3 untouched | nothing written to them |
| loop length unchanged | 43.636327 s, the same to the sample as v2 |
| loop seam sample difference | 0 samples, max edge jump 37, head peak 614, tail peak 0 |
| peak | -1.00 dBFS |
| rms against v2 | -16.35 dBFS, v2 -16.48 dBFS |
| voices present | 8 of 8, none silent |
| ghost notes | 22 of 49 snare hits at 56 velocity or below, 2 flam grace hits |
| snare late, kick early | dpcm onsets at 0, 6, 10, 16, 134, 136, 221, 235 ticks |
| pedal tail bars | 13 of the 24 lead bars hold one pitch |
| hook meter | 99 of 100, v3 99, v2 91 |

Every Python check above ran on this PC (pure MIDI and JSON reads, no numpy matrix work); no pytest
run was needed for a cue build and none is claimed. The render is `tools/render_chip.py`
(renderer v2, soft limiter), the OGG is ffmpeg libvorbis q5 from the same WAV.

## What Nayil has to decide by ear

1. The pedal tails. v2 walks the phrase down to the leading tone (A4 G4 F#4); v3 and v4 hold the
   leading tone for the whole bar. One ear gained 6 points on it, the other lost 2, and the meter
   gained 8. This is the one change that alters the boss theme's signature phrase.
2. Whether v4's ghost notes and flam are audible enough to earn the kit, or whether the boss cue
   wants the stripped waltz back.
3. Whether the "126 bpm family" line applies to the boss cue at all. If it does, the change is 32
   bars at 126 bpm = 45.7 s and the boss scene length moves with it.

## Files

- `percy_theme_v4.mid`, `.wav`, `.mp3`, `.ogg`, `percy_theme_v4_loop.json`
- `build_percy_v4.py`, `build_report_v4.json`, `check_percy_v4.py`, `ear_with_user_env.py`
- `score_table_before.txt`, `score_table_after.txt`, `score_table.py`, `render_log.txt`
- reviews: `assets/audio/ear_reviews/percy_theme_v4_20261026T134048Z.md` (flash-lite) and
  `assets/audio/ear_reviews/percy_theme_v3_20261026T133738Z.md` (flash, the v3 read)
- the previous versions are `assets/audio/percy_theme/`, `percy_theme_v2/` and `percy_theme_v3/`
