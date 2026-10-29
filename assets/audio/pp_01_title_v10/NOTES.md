# PP-01 "Title Theme" v10, notes. Card M3 BAROQUE-CUES (t_65512e1c), built 2026-10-29.

v10 is the first title built FROM the counterpoint engine rather than repaired after
composition. Nothing earlier is touched: v6, v7, v8 and v9 stay exactly as they were, and
every file in this folder carries `_v10`.

## What it is

A two-part invention on the game's own leitmotif with a triangle continuo, in A minor,
3/4, 126 bpm, 32 bars (45.7 s), loop over all 32 bars.

* The leitmotif is READ out of `assets/audio/pp_01_title_v7/pp_01_title_v7.mid`, track
  `vrc6 pulse a`, bars 3 to 6 (13 notes), not retyped, and the build asserts the read
  against its own constant (`leitmotif.matches_constant` in `build_report.json`).
* Pulse 1 states the subject at bars 1 to 4, 13 to 16 and 25 to 28. Pulse 2 states the
  answer an octave below at bars 5 to 8 and 17 to 20. Every one of those notes is marked
  FIXED, and neither the repair pass nor the polish pass may move one: `motif_pulse1`
  reports 13 of 13 present at their own ticks in `build_report.json`.
* Each statement carries a generated countersubject in the other upper voice, and the
  pair is measured again with the two voices swapped between registers
  (`swap_check`, bars 1 to 4): 0 hard findings, 0 raw clashes, so the counterpoint is
  invertible at the octave and that is measured, not claimed.
* The episodes at bars 9 to 12 and 21 to 24 sequence the leitmotif head (F E D C, C B A G,
  G F E D, E D C B) over VI, VII, III and i, and bars 29 to 32 close with the head once
  more and an authentic cadence on A.
* The triangle walks the chord on beats 1, 2 and 3. Chord plan, per bar, as measured in
  the report: i V i V | i i V7 V | VI VII i i | i V i V | i i V7 V | III III i i |
  i V i V | V i i i.

## NES timbres, per voice

| voice | timbre | duty | level |
| --- | --- | --- | --- |
| pulse 1 | 2A03 square, the subject and the episodes | 50 percent (CC12 = 2) | 104 |
| pulse 2 | 2A03 square, the answer and the countersubjects | 25 percent (CC12 = 1) | 88 |
| triangle | 2A03 triangle, the continuo, fixed level | n/a | n/a |

Vibrato is a delayed NES vibrato, not a delayed LFO: CC1 depth 4 with CC20 onset 1 eighth
on pulse 1, depth 3 with onset 2 eighths on pulse 2, so held notes move and eighth runs do
not. The render is `tools/render_chip.py --humanize`, the project's own 2A03 renderer, with
the chip legal humanization and its output kept beside the render
(`pp_01_title_v10_humanized.mid`).

Real 2A03 through Dn-FamiTracker (`musikage/tools/dnft.py`) was NOT used, and the reason is
in the pipeline: dnft renders a .dnm module, and the MuseScore to .dnm route belongs to the
Musikage arranger, which writes a module from its own band arrangement (drums, VRC6, a
pattern per channel). There is no .dnm writer for a three-part counterpoint line here, and
inventing one on this card would mean shipping an unverified exporter. `render_chip.py` is
the project's own 2A03 renderer and the one every landed cue in this tree uses.

## The measurement, which is the point

Same engine the cue gate uses (`tools/counterpoint/check.py`, profile free, key declared
A minor) and the clash counter (`tools/counterpoint/clash.py`):

| measure | value |
| --- | --- |
| hard findings | **0** |
| soft findings | 2 (CP-14 voice overlap at one bar, CP-15 spacing at one bar) |
| style findings | 0 |
| raw clashes (all pairs) | **0** |
| raw clashes on a downbeat | **0** |
| dissonances judged | 37 |
| devices | passing 28, suspension 13, neighbour 1, appoggiatura 0, escape 0 |
| notes | 340 (pulse 1 107, pulse 2 122, triangle 111) |
| voices in range (CP-17) | 0 out of range |
| cue gate, `--no-baseline` | PASS (exit 0), on the MIDI and on the humanized MIDI |
| swap check, bars 1 to 4 | hard 0, clash 0 |

For comparison, from the M0 diagnosis: v7 had 196 raw clashes with 30 on a downbeat, v8
204 with 35, and v9 was repaired down to 2 with 0. v10 is written clean from the start and
carries devices, which v9 had 75 judged dissonances to speak of and v10 has 37: fewer
dissonances, every one of them a prepared figure.

## Loudness and loop

| measure | value |
| --- | --- |
| render | 45.714 s, peak -1.00 dBFS, RMS -14.06 dBFS (humanized) |
| delivered OGG | **-14.07 LUFS integrated, -1.01 dBTP**, LRA 2.7 LU |
| target | -14.0 LUFS, ceiling -1.0 dBTP (specs/12-audio.md, the W5 masters) |
| loop | 32 bars, 2015998 samples, seam sample difference 0, head edge peak 957 |

The master chain is gain then a lookahead limiter (`tools/counterpoint/m3_build.py`),
iterated until the DELIVERED encode measures on target; the limiter sits at -1.9 dBFS
because a square wave's intersample peaks run about 0.8 dB over its sample peak, and
alimiter's auto level is off (with it on it puts its own output back at full scale).

## The ear

`tools/ear_critic.py`, model `gemini-3.5-flash`, one call per row, whole file.

| round | file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | plain render | 7 | 4 | 5 | 3 | 6 | 5 | 30 |
| 2 | humanized render, delayed vibrato | 7 | 4 | 7 | 3 | 6 | 7 | **34** |

Reviews: `ear_reviews/pp_01_title_v10_20261029T230426Z.md` (round 1),
`ear_reviews/pp_01_title_v10_20261029T230729Z.md` (round 2).

What that means honestly: the critic rewards tension and structure once the vibrato and
humanization land, and it still calls the performance mechanical (human 3) and asks for
percussion (drums 4) that this design does not have, because a two-part invention with a
continuo has no drum part. The same critic scored v7 at 41 and v9 at 33, and the whole
ledger for the cue is in `data/ear_ledger.csv`; it is a hint to check against Nayil's ear,
not a verdict.

Hook meter (`tools/hook_score.py`, melody track `pulse 1`): **67 / 100** (v9 83). It scores
an invention badly on purpose: it wants a two-bar hook repeated with small variation, and
v10 spends 8 of its 32 bars on episodes, so motif coverage reads 22 percent. The episode
bars are the form, not an accident, and the hook meter's own weakest line names it.

## Files

| file | what it is |
| --- | --- |
| `build_pp01_v10.py` | the build script for this folder (calls the two tools below) |
| `pp_01_title_v10.mid` | the score, three voices, on the eighth grid |
| `pp_01_title_v10_humanized.mid` | the renderer's chip legal humanization |
| `pp_01_title_v10.wav` | the raw 2A03 render |
| `pp_01_title_v10_master.wav` | the master, before the lossy encode |
| `pp_01_title_v10.ogg` | the delivered file, -14.07 LUFS / -1.01 dBTP |
| `pp_01_title_v10.mp3` | the same master as MP3, for the ear critic and a quick listen |
| `pp_01_title_v10_loop.json` | loop point in samples and seconds |
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

    .venv/Scripts/python.exe tools/counterpoint/m3_build.py --piece title \
        --asset-dir assets/audio/pp_01_title_v10 --slug pp_01_title_v10 --loop-bars 32

The engine is `tools/counterpoint/m3_cues.py` and the pipeline around it is
`tools/counterpoint/m3_build.py`. Nothing in `data/audio.json` was changed: pointing PP-01
at a new file is a data edit a person makes, and this card does not own that file.
