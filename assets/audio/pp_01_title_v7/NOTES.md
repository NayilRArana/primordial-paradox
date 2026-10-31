# PP-01 "Title Theme" v7, notes. Card AUTO-MUSIC-NEXT (t_61d9e8a2), written 2026-10-24 19:30 UTC.

## 1. Why this cue

Every registry cue was scored on the same melody track (`vrc6 pulse a`, `tools/hook_score.py`); the
before table is `score_table_before.txt` in the card workspace and the numbers are below. The floor
is a tie at **83 of 100** between PP-01 title (v6) and PP-02 drive (v2, and its v3 cut-grid copy which
is the same music).

PP-02 was rejected as the target even though it ties: its biggest failing criterion is loop length
(0 of 6 points, 125 bars), and 125 bars is the 178.57 s cue the film's eleven hard cuts are pinned to
(`assets/audio/pp_drive/NOTES-v3.md` section 1, `knowledge/DRIVE-SHOT-LIST.md` section 8). Shrinking
it to an 8, 16 or 32 bar loop would score the meter and break the cut grid, so that point cannot be
taken honestly.

PP-01's two heavy failures are also structural, and this build does not pretend otherwise:

| failing criterion | weight | why it does not move here |
| --- | --- | --- |
| contour, 2 of 12 returns arch or pedal | 10 | each 2 bar phrase pairs a call cell (K: down a third then three eighths up; K2: the same a fourth lower) with a held W bell, which is a sawtooth plus a hold, never one rise and one fall. Changing it means rewriting K or K2, the cue's leitmotif identity, which the score and `knowledge/MUSIC-STYLE-BIBLE.md` section 4.2 own |
| loop length, 52 bars | 6 | the form is Intro 4 + A 8 + A' 8 + B 8 + B' 8 + trio 8 + A return 8, and the trio is the only place P and H sound. Cutting to 32 bars deletes two of the four leitmotifs |

What was left to improve is what the ear is actually scoring low and what the card asks for: drums,
tension (dissonance) and human feel. That is what v7 changes.

## 2. Hook meter, before and after

| file | score | failing criteria |
| --- | --- | --- |
| `pp_01_title_v6.mid` (previous version, untouched) | 83 / 100 | contour, loop length, step ratio, motif coverage |
| `pp_01_title_v7.mid` | 83 / 100 | the same four |

Criterion by criterion the scores are identical to the reporting digit; the only movement is motif
coverage 18.75 to 18.6 of 20, because the anticipation adds one note outside the 2 bar motif (129
notes instead of 128). The meter does not reward this build and it is not claimed as a win.
`hook_report_v7.json`.

## 3. Ear, before and after, same judge back to back

| read | file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | `pp_01_title_v6.mp3` | 7 | 5 | 6 | 4 | 7 | 6 | **33** |
| after | `pp_01_title_v7.mp3` | 8 | 5 | 6 | 4 | 8 | 7 | **38** |

Judge `gemini-3.5-flash`, one call each, 19:19 UTC, reviews
`assets/audio/ear_reviews/pp_01_title_v6_20261024T191908Z.md` and
`..._v7_20261024T191937Z.md`. `assets/audio/EAR_SWEEP_2026-10-22.md` puts the ear's own noise floor
at 1 point per criterion, so +5 total with +1 on three axes is just above the floor: a small
positive read, not a verdict.

## 4. What changed, and the measure for each

| change | measure | check |
| --- | --- | --- |
| DIS-09 anticipation, risk 1: G4 on the last eighth of bar 36, resolving into the Em on bar 37 where G is a chord tone | 1 note added at bar 36 | `build_report_v7.json` devices |
| DIS-04 suspension 4 to 3, risk 1: vrc6 pulse b (silent in the trio in v6) holds E5 from bar 38 across into the B7 bar and resolves to D#5 on beat 2 | 2 notes added in the trio; the script asserts the voice was silent there first | `build_report_v7.json` devices |
| kit: a 16 bar rung (bars 16 and 32 go half time with no hats), ghost snares under the B backbeat, a three hit tom fill before bars 13, 21, 29, 37 | noise 270 to 266 hits (the hat dropout takes more than the fills add), dpcm 101 to 105 | `build_report_v7.json` kit |
| human pass, the same one v6 used | articulation 90.2% of 1259 notes, vibrato on 52 melody notes, 22 breaths, 1 grace note, 1 mordent, seed 20261021 | render log |

Budget check against `knowledge/MUSIC-DISSONANCE.md` section 4: A, A', B, B', trio and A return each
get 1 or 2 devices per 8 bars. v7 places one in B and one in the trio, both risk 1, both leaving F1
(no device on the first or last note of a K, K2, Z, P or H statement) satisfied: the anticipation is
in a held W bell bar with a written rest after it, and the suspension is in a voice that carries no
motif statement in the trio. No device sits in the final cadence bar of any section (F2).

Only those voices changed. Every K, K2, Z, P, H and W statement is v6's notes in v6's order; pulse 1
arpeggios, pulse 2 echo, the vrc6 saw oom pah and the triangle bass are v6's notes untouched.

## 5. Form, tempo, loop

A minor, 3/4, 126 bpm, 52 bars, 74.286 s, loop from bar 5 for 48 bars. Nothing about the form changed.

`pp_01_title_v7_loop.json`: 3275997 samples, **loop seam sample difference 0**, peak -1.00 dBFS, RMS
-17.08 dBFS, edge peak head 206, edge peak tail 0, 5 ms raised cosine fade. As with v6 this measures
the file's own head and tail; the seam the game actually uses is the bar 52 to bar 5 junction, and
that junction is not what this measurement reaches.

## 6. Chip limits

All 8 voices the hardware has and no others: 2A03 pulse 1, pulse 2, triangle, noise, dpcm plus VRC6
pulse a, pulse b, sawtooth. Melody 64..81, pad 43..64, bass 36..52, all inside their instrument
ranges, and `render_chip` rendered the file on its v2 voice path. The noise channel carries drum ids
rather than pitches (12 hat, 38 snare, 4 to 8 toms), which is v6's own encoding.

## 7. Rounds, and why the loop stopped here

1. Baseline: v6, hook 83, ear 33.
2. Round 1: v7, hook 83, ear 38. Kept.
3. Round 2: v8 (`assets/audio/pp_01_title_v8/`), ear 37 (hook 7, drums 5, tension 6, human 4,
   variety 7, structure 8), hook 83. The one axis it gains is structure, and it gives back hook and
   variety: a 1 point read in each direction on three axes is the judge's noise floor, not a
   difference. Stopped after round 2 of the allowed 4 because further rounds would be tuning the mix
   to a judge whose answers move by exactly its own error bar on consecutive calls.

Ear quota this card: three calls, all served by `gemini-3.5-flash`, no model marked exhausted. The
key was read from the user environment variable at call time and never printed or written to a file.

## 8. Files

- `pp_01_title_v7.mid`, `_humanized.mid`, `.wav`, `.mp3`, `.ogg`, `_loop.json`
- `hook_report_v7.json`, `build_report_v7.json`, `build_pp01_v7.py`
- the round 2 build sits beside it in `pp_01_title_v8/` and is not the recommended file

## 9. Q: for gamedev

Q: PP-01 still points at `assets/audio/pp_01_title/pp_01_title.ogg` in `data/audio.json` and still
carries `"placeholder": true`. Landed v6, v7 or neither is a registry edit and an ear call, and
that table is gamedev's. My recommendation is v7 on the ear read (38 against v6's 33); the hook
meter gives no reason to prefer either.
