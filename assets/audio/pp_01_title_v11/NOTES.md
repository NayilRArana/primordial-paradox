# PP-01 "Title Theme" v11, take B. Notes. Card M3 BAROQUE-CUES (t_65512e1c), built
# 2026-10-29.

v11 is the SECOND candidate for the title, built for Nayil to pick against v10 by ear. It
is a different piece, not a reseed of v10: the voices swap roles, the harmony plan is a
different progression, and the continuo moves in a different rhythm. Nothing earlier is
touched: v6, v7, v8, v9 and v10 stay exactly as they were, and every file in this folder
carries `_v11`.

## What it is

A fugato on the game's own leitmotif, in which the LOWER voice states the subject first.
A minor, 3/4, **126 bpm**, 32 bars (45.714 s), loop over all 32 bars.

* 126 bpm is not this take's choice. `data/title_timing.json` is the source of truth for
  the title's timing and `tools/apply_title_timing.py` turns it into the game's macros, so
  the car bob, the lane dashes and the logo shimmer all count against the theme's tempo.
  A candidate at another tempo would move the animation, not just the music.
* The leitmotif is READ out of `assets/audio/pp_01_title_v7/pp_01_title_v7.mid`, track
  `vrc6 pulse a`, bars 3 to 6, 13 notes, and the read is asserted against the module's own
  constant (`leitmotif.matches_constant: true` in `build_report.json`).
* The entries: pulse 2 states the subject an octave below at bars 1 to 4, pulse 1 answers
  at bars 5 to 8, the pair returns at bars 13 to 20, the triangle enters with the head at
  bar 21 as the third voice, and pulse 1 states the subject once more at bars 25 to 28.
  Measured: 13 of 13 subject notes present on pulse 2, 13 of 13 answer notes present on
  pulse 1 at bar 5, 4 of 4 head notes in the triangle at bar 21.
* Episodes at bars 9 to 12 sequence the head in the soprano. Bars 28 to 32 close with the
  head once more and an authentic cadence on A.
* The continuo walks every eighth of every bar (185 triangle notes against v10's 111), and
  the harmony runs a circle of fifths through the middlegame. The chord plan as measured,
  one per bar: i V i V | i i V7 V | ii VII i VI | ii V i i | i V V7 V | VI ii V i |
  i i i i | V i V i.
* Invertibility: the two upper voices are measured again with their registers exchanged
  over the first entry pair, `swap_check` bars 5 to 8: hard 0, raw clashes 1, 0 on a
  downbeat.

## NES timbres, per voice

| voice | timbre | duty | level |
| --- | --- | --- | --- |
| pulse 1 | 2A03 square, the answer and the episodes | 50 percent (CC12 = 2) | 104 |
| pulse 2 | 2A03 square, the subject and the countersubjects | 25 percent (CC12 = 1) | 88 |
| triangle | 2A03 triangle, the third entry and the walking continuo | n/a | n/a |

Delayed NES vibrato as on v10: CC1 depth 4 with CC20 onset 1 eighth on pulse 1, depth 3
with onset 2 eighths on pulse 2, so held notes move and the eighth runs do not. Rendered by
`tools/render_chip.py --humanize`, the project's own 2A03 renderer, with the chip legal
humanization kept beside the render (`pp_01_title_v11_humanized.mid`).

The Musikage Dn-FamiTracker path was not used, for the same measured reason recorded in
v10's notes: `dnft.py` renders a .dnm module, and this project has no .dnm writer for a
three part counterpoint line; writing one here would ship an unverified exporter, and the
card allows `render_chip.py` explicitly.

## The measurement, which is the point

Same engine the cue gate uses (`tools/counterpoint/check.py`, profile free, key declared A
minor) and the clash counter (`tools/counterpoint/clash.py`):

| measure | v11 | v10 for comparison |
| --- | --- | --- |
| hard findings | **0** | 0 |
| soft findings | 1 (CP-15 spacing, bar 3) | 2 |
| style findings | 0 | 0 |
| raw clashes (all pairs) | 2, none on a downbeat | 0 |
| dissonances judged | 6, all passing tones | 37 |
| devices | passing 6 | passing 28, suspension 13, neighbour 1 |
| notes | 390 (pulse 1 106, pulse 2 99, triangle 185) | 340 |
| voices in range | 0 out of range | 0 |
| cue gate, `--no-baseline` | PASS (exit 0) on the MIDI and the humanized MIDI | PASS |
| originality (`melody_guard.py` against `projects/musikage`) | PASS, 32 references, longest identical interval run 5, best 5-gram Jaccard 0.0000 | not run on v10 |

Honest read of that table: v11 is the plainer piece. It has fewer dissonances and fewer
devices than v10, because the walking continuo and the sparser upper lines leave less room
for prepared figures; what it has instead is a continuous bass, a third entry and a
circle of fifths. It is a different idea, not a better one, and that is what a pick is for.

## Loudness and loop

| measure | value |
| --- | --- |
| render | 45.714 s, peak -1.00 dBFS, RMS -12.45 dBFS (humanized) |
| delivered OGG | **-14.02 LUFS integrated, -1.18 dBTP**, LRA 0.8 LU |
| target | -14.0 LUFS, ceiling -1.0 dBTP (specs/12-audio.md, the W5 masters) |
| loop | 32 bars, 1764001 samples, seam sample difference 0, head edge peak 1237 |

## The ear

No Gemini ear read on this take, and the reason is a fact about the run that built it: the
ear critic needs `GEMINI_API_KEY`, and the session that built v11 had no key in its
environment (`tools/ear_critic.py` reads it at call time), so no call was made. Nothing is
invented here in its place: the scores are absent rather than guessed. v10's two ear rounds
are in `data/ear_ledger.csv` and `assets/audio/ear_reviews/` if a comparison is wanted.

Hook meter (`tools/hook_score.py`, melody track `pulse 1`): **67 / 100**, the same as v10
and for the same structural reason: the meter wants a two bar hook repeated, and a fugato
spends its bars on entries and episodes.

## Files

| file | what it is |
| --- | --- |
| `pp_01_title_v11.mid` | the score, three voices, on the eighth grid |
| `pp_01_title_v11_humanized.mid` | the renderer's chip legal humanization |
| `pp_01_title_v11.wav` | the raw 2A03 render (gitignored, like every .wav here) |
| `pp_01_title_v11_master.wav` | the master before the lossy encode |
| `pp_01_title_v11.ogg` | the delivered file, -14.02 LUFS / -1.18 dBTP |
| `pp_01_title_v11.mp3` | the same master as MP3, for a quick listen |
| `pp_01_title_v11_loop.json` | loop point in samples and seconds |
| `hook_report.json` | the hook meter's full report |
| `melody_guard.json` | the originality report |
| `build_report.json` | every number above, plus the chord fit and the polish log |

## What is in git, and what is not

The `.ogg`, `.mp3` and `.mid` of this take are NOT in the commit, and that is the
project's rule rather than an omission: `tools/check_build_inputs.py --staged` refuses a
stream that `game/PrimordialParadox.yyp` does not name, so a candidate cue lands in git
only when it is wired, together with the regenerated project file, and wiring is a data
edit this card does not own. The delivered `.ogg` rides on card t_65512e1c as an
attachment for the by-ear pick, and the reproduce command below rebuilds it from the
committed engine, renderer and report.

## Reproduce

    .venv/Scripts/python.exe tools/counterpoint/m3_build.py --piece title --variant 2 \
        --asset-dir assets/audio/pp_01_title_v11 --slug pp_01_title_v11 --loop-bars 32

Nothing in `data/audio.json` was changed: pointing PP-01 at a new file is a data edit a
person makes, and this card does not own that file.
