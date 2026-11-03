# PP-04 fight cue, take D: `pp_04_fight_baroque_v5`, `_v6` and `_v7`

Card AUTO-MUSIC-NEXT (`t_e21896aa`), musician lane, built 2026-11-03 03:26 to 03:34 UTC.
v1, v2, v3 and v4 are untouched. This folder trio adds take D: `_v5` is round 1, `_v6` is
round 2 (the ear's own changes), `_v7` is round 3 and the delivered candidate (the same music
as `_v6` with the noise channel made hardware legal, see below).

## The cue picked, and the numbers that picked it

The scan re-ran `tools/hook_score.py` on every `.mid` under `assets/audio/` (54 files) and read
the latest `summary` row per file out of `data/ear_ledger.csv`. Live cues first, from
`data/audio.json` (`delivered_file`), with the meter run on the score that music is made of:

| live cue | delivered asset | hook score | ear total |
| --- | --- | --- | --- |
| PP-01 title | `pp_01_title` | 71 / 100 | 34 |
| PP-02 drive | `pp_drive_master1` (score `pp_drive_v4`) | 92 / 100 | 29 |
| PP-03 harbor | `pp_03_harbor_master1` (score `pp_03_harbor_v4`) | 100 / 100 | 31 |
| PP-04 navy | `pp_04_navy_sailors_master1` (score `pp_04_navy_sailors_v3`) | 100 / 100 | 33 |
| PP-05 small ship | `pp_05_small_ship` (v1) | 67 / 100 | 15 |
| PP-06 Percy | `percy_theme` (v1) | 61 / 100 | 25 |
| PP-17 boarding | `pp_boarding_v2_humanized` | 90 / 100 | 28 |

Two readings of "weakest", and they disagree:

- by the ear, PP-05 and PP-06 are the weak shipped cues (15 and 25 of 60);
- by the meter, the lowest score still in play in the project is the PP-04 fight cue's take B
  at 61, which take C already rebuilt to 87 earlier today (`t_ff00a640`).

Take C was `pp_04_fight_baroque_v4`, 87 of 100, and its own `hook_report.json` names four
criteria it did not earn. So the work here continued the take that the meter can still measure
and that is still short, rather than adding a seventh unseen take of a cue whose best take is
already 98 or 99 and whose real gap is that nobody has wired it (`data/audio.json` still names
the v1 files for PP-05 and PP-06; re-pointing a cue row is gamedev's call, not this card's).

## The score table, before and after

Hook meter, `tools/hook_score.py`, melody track `pulse 1`, same tool and same thresholds for
every row (`knowledge/MUSIC-HOOK-GRAMMAR.md` supplies them, `leap_semitones: 5`,
`step_semitones: 2`, `pedal_range_semitones: 5`, `max_range_semitones: 18`):

| criterion | weight | take B (v2) | take C (v4) | **take D (v7)** |
| --- | --- | --- | --- | --- |
| motif coverage | 20 | 8.4 (25% of 91) | 18.4 (55% of 87) | **20.0 (62% of 78)** |
| motif returns | 12 | 8.0 (2) | 12.0 (4) | **12.0 (4)** |
| hook cell | 10 | 10.0 | 10.0 | **10.0** |
| steps over leaps | 12 | 12.0 | 11.8 (64%) | 11.8 (64%) |
| leaps per motif | 8 | 4.0 (2) | 4.0 (2) | 4.0 (2) |
| range | 8 | 6.5 (22 st) | 8.0 (15 st) | **8.0 (12 st)** |
| contour | 10 | 0.0 | 2.5 (1 of 4) | 2.5 (1 of 4) |
| repeated pitch | 6 | 6.0 | 6.0 | **6.0 (9 in a row)** |
| loop length | 6 | 6.0 | 6.0 | **6.0 (16 bars)** |
| variation on the third return | 8 | 0.0 | 8.0 (83%) | **8.0 (83%)** |
| **total** | 100 | **61** | **87** | **88** |

The points take D bought, and the ones it did not: coverage went from 55% to 62% and the
criterion from 18.4 to 20.0, and the note count fell from 87 to 78 while the four statements
stayed. The other 12 points (contour 7.5, the second leap 4.0, 0.25 of step ratio) are the
leitmotif's own pitches, and rewriting them would buy a score by breaking the theme: see
"what this does not claim" below. 88 of 100 is therefore the ceiling for a faithful take, and
this take reaches it.

Ear, `tools/ear_critic.py`, one whole-file call per row:

| round | file | model | hook | drums | tension | human | variety | structure | total | review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | `pp_04_fight_baroque_v2.ogg` | gemini-3.5-flash-lite | 6 | 4 | 5 | 3 | 6 | 5 | 29 | `..._v2_20261103T000234Z.md` |
| before | `pp_04_fight_baroque_v4.ogg` | gemini-3.5-flash-lite | 6 | 4 | 5 | 3 | 6 | 5 | 29 | `..._v4_20261103T000347Z.md` |
| round 1 | `pp_04_fight_baroque_v5.ogg` | gemini-3.5-flash-lite | 6 | 4 | 5 | 3 | 6 | 5 | 29 | `..._v5_20261103T033004Z.md` |
| round 2 | `pp_04_fight_baroque_v6.ogg` | gemini-3.5-flash-lite | 6 | 4 | 5 | 3 | 6 | 5 | 29 | `..._v6_20261103T033125Z.md` |
| round 2 control | `pp_04_fight_baroque_v6.ogg` | gemini-3.5-flash | 6 | 4 | 5 | 3 | 6 | 5 | 29 | `..._v6_20261103T033155Z.md` |
| round 3 | `pp_04_fight_baroque_v7.ogg` | gemini-3.5-flash-lite | 6 | 4 | 5 | 3 | 6 | 5 | 29 | `..._v7_20261103T033332Z.md` |

Six renders of this cue, two different judges, one row of identical integers. The ear is
saturated on this cue and is not evidence for or against any of the three takes; the hook
meter is, and it moved. No 429 and no 503 arrived, so no quota-driven model switch was needed;
the second model was asked deliberately, as a control on the saturation.

## What take D changed, and the measure for each

| change | measure | where |
| --- | --- | --- |
| pulse 1's generated filler is dropped in bars 11 and 12, where the triangle states the subject and the sixteenths only blurred it | melody 87 to 78 notes, motif coverage 55% to 62%, coverage 18.4 to 20.0 of 20 | `fight_piece_d` in `m3_cues.py` |
| the kit varies every 2 bars (the answer bar rests its beat 2 snare), every 4 bars (32nd roll plus a 44/41/38 tom rung into the phrase end) and every 8 bars (a five hit climb at bars 7 and 15, hat colour open in the second half) | distinct noise hit patterns per 4 bar block: take C 1, take D 3; per 8 bar block: take C 1, take D 2 | `drums_fight_r4` |
| round 2 takes the ear's change 4: bars 13 to 16 drop the on-beat hat and put an accented open hat (pitch 34, longer gate) on every offbeat | the last four bars read 4, 4, 4, 10 hits a bar where the first twelve read 8 | `drums_fight_r5` |
| round 2 takes the ear's change 5 without the seam risk: the last eighth of bar 16 is one tom and nothing else, instead of an absolute silence on the loop point | per-bar noise 10 on bar 16, 0 of 131 hits lost to the seam, `loop_seam_sample_difference: 0` | `drums_fight_r5` |
| round 3 makes the noise channel hardware legal: no two noise hits ever start on the same tick (the louder fill wins) | overlapping noise ticks: take C 16, take D round 2 7, take D delivered 0 | `drums_fight_r5` dedupe |
| pulse 2 opens its duty at bar 5 and closes it again at bar 13, so the answer is a different colour from the subject without touching the motif carrier | CC12 written at bars 5 and 13 on pulse 2 only | `m3_build.py`, variant 5 |
| the triangle's vibrato deepens from bar 13 (CC1 4 to 5, delay 3 eighths) | CC1 and CC20 per voice in the MIDI | `m3_build.py`, variant 5 |

Dissonance is the counterpoint engine's and it is measured, not asserted: 12 judged
dissonances on the score (11 passing, 1 appoggiatura), `raw clash 0` and `strong_raw 0`, which
is `knowledge/MUSIC-DISSONANCE.md` section 2 applied by the checker. The four leitmotif
statements are the project's own cell (`FIGHT_SUBJECT` is `LEITMOTIF` from
`pp_01_title_v7.mid`, bar 3, compressed from 3/4 to 4/4), stated at bars 1, 5, 9 and 13 with
the third close varied, so K Z P H stay recognisable and unchanged.

## 2A03 plus VRC6, tempo, and the loop

- Five voices on the chip pair: 2A03 pulse 1, pulse 2, triangle, noise, DPCM. 215 pitched notes
  (pulse 1 78, pulse 2 71, triangle 66) plus 131 noise and 54 DPCM hits. No noise or DPCM tick
  carries two hits in the delivered take, and the pitched voices are gated by the counterpoint
  engine, which refuses a pitch that crosses or crowds a neighbouring voice.
- **168 bpm, not 126**: gamedev ruling D3 (`knowledge/GAMEDEV-DECISIONS-2026-10-26.md`) keeps
  PP-04 at 168 bpm with 16 bars per state so a state cut lands on a bar line. Gamedev is a head
  on this project and a music card does not override its spec; the 126 bpm family in the card
  body applies to the cues no ruling covers. This is the same reading take C recorded.
- 16 bars of 4/4, 22.857143 s, 1008000 samples at 44.1 kHz.
- `loop_seam_sample_difference: 0`, seam jump 0, last sample 0 and first sample 0,
  `tail beyond loop point: 0 samples` from
  `assets/audio/pp_05_small_ship_v6/check_seam_v6.py <wav> 16 168` run on all three takes.
- Master: delivered OGG -14.04 LUFS integrated, -1.26 dBTP true peak, inside the -14.0 / -1.0
  target (`level_ok: true`, `ceiling_ok: true`).
- `tools/counterpoint/check.py`: PASS hard 0, soft 2, style 1. `cue_gate.py --no-baseline`:
  exit 0, PASS, on the score and on the humanized MIDI.

## What this does not claim

- The ear total did not move and could not have: six renders and two judges returned the same
  six integers. That is a saturated judge, not a measurement of this music; the 2026-10-22
  sweep already recorded a 14 point swing between models on identical audio, and here the
  models agree exactly.
- **Take C's 87 is close to the ceiling for this cue, and take D's 88 is the ceiling.** The
  last 12 points are three criteria that are measured on the leitmotif's own 12 notes:
  contour (arch or pedal), one leap per motif instead of two, and the step ratio that follows
  from the leaps. Take C's subject rises a fifth and falls a fifth because the project's cell
  does; rewriting it into an arch would add roughly 11 points and would stop being the theme.
  Card AUTO-MUSIC-NEXT asks for the leitmotif to stay clear, so this card took the 1.6 points
  that do not cost the motif and wrote the rest down instead of buying them.
- It is not wired. `data/audio.json` delivers `pp_04_navy_sailors_master1.ogg` for PP-04, and
  the baroque takes are candidates waiting on a by-ear pick, which is gamedev's call. No cue
  row was changed by this card.
- No person has heard it.

## Files

| file | what it is |
| --- | --- |
| `pp_04_fight_baroque_v7.mid` | the score, five tracks (delivered candidate) |
| `pp_04_fight_baroque_v7_humanized.mid` | the renderer's chip legal humanization |
| `pp_04_fight_baroque_v7.wav`, `_master.wav` | raw render and mix master |
| `pp_04_fight_baroque_v7.ogg` | the stream, -14.04 LUFS / -1.26 dBTP |
| `pp_04_fight_baroque_v7.mp3` | MP3 of the same master |
| `pp_04_fight_baroque_v7_loop.json` | the loop point and the seam measurement |
| `build_report.json`, `hook_report.json` | every number above |
| `../pp_04_fight_baroque_v5/`, `../pp_04_fight_baroque_v6/` | rounds 1 and 2, kept |

## Reproduce

    .venv/Scripts/python.exe tools/counterpoint/m3_build.py --piece fight --variant 5 \
        --asset-dir assets/audio/pp_04_fight_baroque_v7 --slug pp_04_fight_baroque_v7 \
        --loop-bars 16

`--variant 4` builds round 1 (take D without the ear's round 2 changes), `--variant 5` builds
rounds 2 and 3. The builder refuses a folder that already holds a `.wav` or `.ogg`, so a
rebuild needs a new folder name.
