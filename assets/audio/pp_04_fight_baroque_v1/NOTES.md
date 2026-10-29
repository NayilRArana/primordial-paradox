# PP-04 fight cue, Baroque exposition (`pp_04_fight_baroque_v1`), notes. Card M3
# BAROQUE-CUES (t_65512e1c), built 2026-10-29.

This is a new candidate for the first fighter cue, not a replacement: `pp_04_navy_sailors`,
`pp_04_navy_sailors_master1`, `pp_fight` and `pp_fight_v2` are untouched, and nothing in
`data/audio.json` points at this folder yet. Naming a delivered cue is a data edit a person
makes, and this card does not own that file.

## What it is

A three-voice fugue exposition on the game's leitmotif, with driving rhythm. A minor, 4/4,
**168 bpm** (the tempo gamedev ruling D3 of 2026-10-26 keeps for the fight), 16 bars
(22.857 s), loop over all 16 bars.

The shape, by bar:

| bars | what happens |
| --- | --- |
| 1 to 2 | subject on pulse 1. The leitmotif compressed into two bars of 4/4 at driving speed, every interval of the original kept (E D C B, B held, E C D E, B G# A) |
| 3 to 4 | tonal answer on pulse 2, a fifth below, with the one chromatic note lowered (C# to C), the classic tonal answer, over a generated countersubject on pulse 1 |
| 5 to 6 | the subject in the triangle, two octaves down, with countersubjects above it |
| 7 to 8 | episode over V: both upper voices in eighth motion over a driving continuo |
| 9 to 10 | subject returns on pulse 1 |
| 11 to 12 | answer returns on pulse 2 |
| 13 to 14 | subject in the triangle again, over iv |
| 15 to 16 | cadence: the head, then V to i, ending on the tonic so the loop starts on a downbeat |

## NES timbres and the drive

| voice | timbre | duty | level |
| --- | --- | --- | --- |
| pulse 1 | 2A03 square, subject and countersubjects | 50 percent (CC12 = 2) | 104 |
| pulse 2 | 2A03 square, answer and countersubjects | 25 percent (CC12 = 1) | 88 |
| triangle | 2A03 triangle, the subject entry and the driving continuo | n/a | n/a |
| noise | 15 bit LFSR, closed hat on every off-beat eighth | n/a | 72 |
| dpcm | kick on beats 1 and 3, snare on beat 2 | n/a | 118 / 104 |

Delayed NES vibrato as on the title: CC1 4 with CC20 1 eighth on pulse 1, CC1 3 with CC20 2
eighths on pulse 2. Rendered by `tools/render_chip.py --humanize`, the project's own 2A03
renderer. The Musikage Dn-FamiTracker route was not used, for the same reason as the title:
`dnft.py` renders a .dnm module and there is no .dnm writer for a three-part counterpoint
line in this project; writing one would be an unverified exporter, and the card allows the
`render_chip.py` route explicitly.

## The measurement

`tools/counterpoint/check.py` (profile free, key declared A minor) and
`tools/counterpoint/clash.py`:

| measure | value |
| --- | --- |
| hard findings | **0** |
| soft findings | 2 (CP-14 voice overlap at one bar, CP-15 spacing at one bar) |
| style findings | 0 |
| raw clashes (all pairs) | **0** |
| raw clashes on a downbeat | **0** |
| dissonances judged | 10 |
| devices | passing 8, suspension 1, appoggiatura 0, neighbour 0, escape 0 |
| pitched notes | 240 (pulse 1 92, pulse 2 79, triangle 69) |
| voices in range (CP-17) | 0 out of range |
| cue gate, `--no-baseline` | PASS (exit 0), on the MIDI and on the humanized MIDI |
| motif in pulse 1 | present, 2 statements of the 12 note compressed subject |
| motif in the triangle | present, 2 statements at two octaves down |

The noise and dpcm tracks are unpitched, so the checker ignores them; the drive lives in the
eighth-note continuo and in the bass entries, which are the pitched voices the rules judge.

## Loudness and loop

| measure | value |
| --- | --- |
| render | 22.857 s, peak -1.00 dBFS, RMS -14.21 dBFS (humanized) |
| delivered OGG | **-14.05 LUFS integrated, -1.04 dBTP**, LRA 2.8 LU |
| target | -14.0 LUFS, ceiling -1.0 dBTP |
| loop | 16 bars, seam measured by the renderer, reported in the render line |

## The ear

`tools/ear_critic.py`, `gemini-3.5-flash`, whole file, one call per row.

| round | file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | plain render | 7 | 5 | 4 | 4 | 6 | 6 | 32 |
| 2 | humanized render, delayed vibrato | 7 | 4 | 5 | 3 | 6 | 6 | 32 |

Reviews: `ear_reviews/pp_04_fight_baroque_v1_20261029T230527Z.md`,
`ear_reviews/pp_04_fight_baroque_v1_20261029T230823Z.md`.

Honest read: the total did not move between the two rounds (32 to 32, drums down and
tension up), and the critic still ranks the fights' tension low because a fugue exposition
is consonant by design. The compare row against the landed fight cue is in the same ledger
(`data/ear_ledger.csv`); the ear is a hint, the pick is Nayil's.

Hook meter (`tools/hook_score.py`, melody track `pulse 1`): 65 / 100. A fugue exposition is
the worst possible shape for that meter, which measures a repeated two-bar hook, so read it
as a form note and not as a defect.

## Files

| file | what it is |
| --- | --- |
| `build_pp04_fight_baroque_v1.py` | the build script for this folder |
| `pp_04_fight_baroque_v1.mid` | the score, five tracks (three pitched, noise, dpcm) |
| `pp_04_fight_baroque_v1_humanized.mid` | the renderer's chip legal humanization |
| `pp_04_fight_baroque_v1.wav` | the raw 2A03 render |
| `pp_04_fight_baroque_v1_master.wav` | the master before the lossy encode |
| `pp_04_fight_baroque_v1.ogg` | the delivered file, -14.05 LUFS / -1.04 dBTP |
| `pp_04_fight_baroque_v1.mp3` | MP3 of the same master |
| `pp_04_fight_baroque_v1_loop.json` | loop point in samples and seconds |
| `hook_report.json` | the hook meter's full report |
| `build_report.json` | every number above, plus the repair and polish logs |

## What is in git, and what is not

The `.ogg`, `.mp3` and `.mid` of this take are NOT in the commit, and that is the
project's rule rather than an omission: `tools/check_build_inputs.py --staged` refuses a
stream that `game/PrimordialParadox.yyp` does not name, so a candidate cue lands in git
only when it is wired, together with the regenerated project file, and wiring is a data
edit this card does not own. The delivered `.ogg` rides on card t_65512e1c as an
attachment for the by-ear pick, and the reproduce command below rebuilds it from the
committed engine, renderer and report.

## Reproduce

    .venv/Scripts/python.exe tools/counterpoint/m3_build.py --piece fight \
        --asset-dir assets/audio/pp_04_fight_baroque_v1 \
        --slug pp_04_fight_baroque_v1 --loop-bars 16
