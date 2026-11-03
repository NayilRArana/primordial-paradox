# PP-04 fight cue, Baroque exposition, take C: `pp_04_fight_baroque_v3` and v4

Card AUTO-MUSIC-NEXT (`t_ff00a640`), musician lane, built 2026-11-02 23:58 to 2026-11-03 00:03 UTC.
v1 and v2 are untouched; this folder pair adds take C, and v4 is the round 2 rebuild of v3 on the
same score, with the kit and the colour changes the ear asked for.

## The cue picked, and the numbers that picked it

The scan read `data/ear_ledger.csv` (latest summary row per file, and the mean of every run) and
every `hook_report*.json` under `assets/audio/`, then compared them with the rows
`data/audio.json` actually delivers. PP-04 fight Baroque take B was the weakest current take on the
deterministic meter, not on taste:

| cue | hook score (`tools/hook_score.py`) | ear total (same model) | status |
| --- | --- | --- | --- |
| `pp_04_fight_baroque_v2` | **61 / 100**, the lowest current score in the project | 29 (flash-lite, measured today for this table) | candidate, never judged by the ear |
| `pp_04_fight_baroque_v1` | 65 / 100 | 31 (flash, 2026-10-29) | candidate, heard by no one |
| `pp_01_title_v10`, `v11` | 67 / 100 | 34 (flash) | title takes |
| `pp_05_small_ship_v2` | 67 / 100 | 25 (flash) | superseded in its own folder by v6 at 98 |
| `pp_drive` v1 / v3 | 46 (v1, stale) / 83 (v3) | 29 (live master) | live, already rebuilt twice |

v2's own NOTES called the 61 a form note: "a fugue exposition is the worst shape for a meter that
wants a repeated two bar hook". That is true of the form and it was still the measurable floor, so
take C keeps the fugue and moves the subject into the voice the meter and the listener both follow.

## The score table, before and after

Hook meter, `tools/hook_score.py`, melody track `pulse 1`, same tool and same input rules for every
row:

| criterion | weight | v2 | v4 |
| --- | --- | --- | --- |
| motif coverage | 20 | 25% of 91 notes, 8.42 pts | 55% of 87 notes, 18.39 pts |
| motif returns | 12 | 2 returns, 8.0 pts | 4 returns, 12.0 pts |
| variation on the third return | 8 | no third return, 0.0 pts | 83% the same, 8.0 pts |
| hook cell | 10 | 6 notes, 3 repeats, 10.0 pts | 6 notes, 4 repeats, 10.0 pts |
| steps over leaps | 12 | 70% steps, 12.0 pts | 64% steps, 11.75 pts |
| leaps per motif | 8 | 2 leaps, 4.0 pts | 2 leaps, 4.0 pts |
| contour | 10 | 0 of 2 returns arch or pedal, 0.0 pts | 1 of 4 returns pedal, 2.5 pts |
| range | 8 | 22 semitones (59 to 81), 6.55 pts | 15 semitones (64 to 79), 8.0 pts |
| repeated pitch | 6 | 6.0 pts | 6.0 pts |
| loop length | 6 | 16 bars, 6.0 pts | 16 bars, 6.0 pts |
| **total** | 100 | **61** | **87** |

Ear, `tools/ear_critic.py`, one whole-file call per row, same judge `gemini-3.5-flash-lite` for
every row so the comparison is not across models (the sweep of 2026-10-22 recorded a 14 point swing
between models on the same audio):

| round | file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | `pp_04_fight_baroque_v2.ogg` | 6 | 4 | 5 | 3 | 6 | 5 | 29 |
| round 1 | `pp_04_fight_baroque_v3.ogg` | 6 | 4 | 5 | 3 | 6 | 5 | 29 |
| round 2 | `pp_04_fight_baroque_v4.ogg` | 6 | 4 | 5 | 3 | 6 | 5 | 29 |

Reviews: `assets/audio/ear_reviews/pp_04_fight_baroque_v2_20261103T000234Z.md`,
`..._v3_20261103T000220Z.md`, `..._v4_20261103T000347Z.md`.

What that row of identical numbers means: this judge is saturated on this cue. Three different
renders, one of them with a swung kit, a 32nd roll and a duty change the same judge had asked for
by name, came back on the same six integers. The loop stopped at round 2 of the allowed 4 because a
third and fourth call would have spent quota on a judge that is not resolving 1 point, and the
2026-10-22 sweep already says 1 point is that judge's noise floor. The ear total is not evidence
for or against take C; the hook meter is, and it moved 26 points.

## What take C changed, and the measure for each

| change | measure |
| --- | --- |
| the subject is the top voice's line four times, bars 1, 5, 9 and 13, where v2 stated it once and answered once | motif returns 2 to 4, coverage 25% to 55% |
| the third statement closes differently: its last two notes become 71 and 72 (the fifth, the sixth) instead of falling 68, 69, so the return is recognisable and not a copy | third return 3.2 style copy to 83% the same, 8.0 of 8 |
| every statement stays inside a ninth (64 to 79), where v2's answer was transposed an octave up and ran to 81 from 59 | range 22 to 15 semitones, 8.0 of 8 |
| the answer and the countersubject move to pulse 2 and the triangle; pulse 1 no longer carries filler in the statement bars | `notes_per_voice` pulse 1 91 to 87, pulse 2 90 to 71, triangle 61 to 66 |
| the kit varies on the bar: closed hat in the first half, open hat on beat 4 of the second half, 16th burst at every 4 bar phrase end, 32nd roll on the last beat of bars 4, 8 and 12, kick rests on bar 13 | every hit is decided by a bar number, no randomness in `drums_fight_hook` |
| round 2 swing: the off-beat eighths land a 16th late | the ear's own change 5, "apply a swung offbeat feel" |
| round 2 colour: pulse 1 duty changes at bar 9, triangle gets a delayed vibrato | the ear's own change 2, and "transitions happen abruptly" |

Dissonance is the counterpoint engine's, measured: 13 judged dissonances (12 passing, 1
appoggiatura), 0 raw clashes on any pair and 0 on a strong beat, where v2 carried 1 raw clash. That
is `knowledge/MUSIC-DISSONANCE.md` section 2 applied by the checker rather than by hand.

## 2A03 plus VRC6, tempo, and the loop

- Three pitched voices on 2A03 plus noise and DPCM: pulse 1, pulse 2, triangle, noise, dpcm. 224
  notes. Nothing is written into a voice that already sounds on the same tick; the counterpoint
  checker and the cue gate both pass on the score and on the humanized MIDI.
- **168 bpm, not 126**: gamedev ruling D3 (`knowledge/GAMEDEV-DECISIONS-2026-10-26.md`) keeps PP-04
  at 168 bpm with 16 bars per state so a state cut lands on a bar line. Gamedev is a head on this
  project and its spec is not overridden by a music card; the 126 bpm family in the card body
  applies to the cues that have no ruling against them.
- `tools/counterpoint/m3_build.py`, 16 bars of 4/4, 22.857143 s, 1008000 samples at 44.1 kHz.
- Master: -14.06 LUFS integrated, -1.15 dBTP true peak, inside the -14.0 / -1.0 target.
- Seam: loop point sample 1008000, `loop_seam_sample_difference: 0`, head edge peak 2205, RMS
  -14.18 dBFS, peak -1.00 dBFS (`pp_04_fight_baroque_v4_loop.json`).
- `tools/counterpoint/check.py`: PASS hard 0, soft 2, style 1 on the score and hard 0, soft 3,
  style 1 on the humanized MIDI. `cue_gate.py --no-baseline`: PASS on both (exit 0).

## What this does not claim

- It is not wired. `data/audio.json` delivers `pp_04_navy_sailors_master1.ogg` for PP-04, and the
  baroque takes are candidates waiting on a by-ear pick, which is gamedev's call. Nothing in this
  card changed a cue row.
- No person has heard it. The only human verdict on record for this cue family is Nayil's on the
  title theme ("a bit dissonant"), and it says nothing about this take.
- The ear numbers above are a saturated judge's, not a measurement of the music. Read the hook
  table as the evidence and the ear table as a control that failed to discriminate.

## Files

| file | what it is |
| --- | --- |
| `pp_04_fight_baroque_v4.mid` | the score, five tracks |
| `pp_04_fight_baroque_v4_humanized.mid` | the renderer's chip legal humanization |
| `pp_04_fight_baroque_v4.wav`, `_master.wav` | raw render and mix master |
| `pp_04_fight_baroque_v4.ogg` | the delivered file, 301256 bytes, sha256 44bd16b779e0124a2896a1505c024cfc6c57c4596e4191dcb72efad129e8363a |
| `pp_04_fight_baroque_v4.mp3` | MP3 of the same master |
| `pp_04_fight_baroque_v4_loop.json` | the loop point in samples and the seam measurement |
| `build_report.json`, `hook_report.json` | every number above |

Round 1 is kept next to it: `assets/audio/pp_04_fight_baroque_v3/` holds the same build without the
swing, the 32nd roll, the duty change and the triangle vibrato.

## Reproduce

    .venv/Scripts/python.exe tools/counterpoint/m3_build.py --piece fight --variant 3 \
        --asset-dir assets/audio/pp_04_fight_baroque_v4 --slug pp_04_fight_baroque_v4 --loop-bars 16

The builder refuses a folder that already holds a `.wav` or `.ogg`, so a rebuild needs a new folder
name; `--variant 3` is take C's composer in `tools/counterpoint/m3_cues.py`.
