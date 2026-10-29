# PP-04 fight cue, Baroque exposition, take B (`pp_04_fight_baroque_v2`). Notes. Card M3
# BAROQUE-CUES (t_65512e1c), built 2026-10-29.

This is the SECOND candidate for the first fighter cue, to be heard against
`pp_04_fight_baroque_v1`. It is a different piece, not a reseed: the exposition starts in
the bass, the answers are placed differently, the episode walks a circle of fifths, the
cadence leans on a six-four, and the drums are a backbeat. `pp_04_navy_sailors`,
`pp_04_navy_sailors_master1`, `pp_fight` and the v1 take are untouched, and nothing in
`data/audio.json` points at this folder.

## What it is

A three-voice fugue exposition on the game's leitmotif, bass first. A minor, 4/4,
**168 bpm**, 16 bars (22.857 s), loop over all 16 bars.

* 168 bpm is not this take's choice: gamedev ruling D3 (`knowledge/GAMEDEV-DECISIONS-2026-10-26.md`)
  keeps PP-04 at 168 bpm, 16 bars per state, so a state cut lands on a bar line. At 168 the
  file is 22.857 s, the same length as the calm state (`pp_fight_v2_calm.ogg` 22.857143 s,
  measured in that ruling); a candidate at another tempo would break the seam before the
  music could be judged.
* The shape, by bar:

| bars | what happens |
| --- | --- |
| 1 to 2 | the subject in the TRIANGLE, two octaves down: the bass enters first, which is the one thing v1 does not do |
| 3 to 4 | the subject on pulse 1, the answer in the top voice |
| 5 to 6 | the subject on pulse 2, an octave down |
| 7 to 8 | episode over iv VII III VI ii V: the bass walks a circle of fifths |
| 9 to 10 | the subject returns in the triangle |
| 11 to 12 | the subject answered a fifth above on pulse 1 |
| 13 to 14 | the answer on pulse 2 |
| 15 to 16 | cadence: the head over a cadential six-four in the triangle (E, then A), landing on the tonic so the loop starts on a downbeat |

* The subject is the same 12 note compressed subject as v1, derived from the leitmotif with
  every interval of the original kept; the answer is the tonal answer, one chromatic note
  lowered. Measured in `build_report.json`: the subject appears once in pulse 1, the answer
  once in pulse 2, and the subject TWICE in the triangle (`motif_bass.statements: 2`).
* The chord plan as measured, one per bar: i V7 i V7 | i V7 iv VII | III V7 i V | i i V i.

## NES timbres and the drive

| voice | timbre | duty | level |
| --- | --- | --- | --- |
| pulse 1 | 2A03 square, the answer, the return subject and countersubjects | 50 percent (CC12 = 2) | 104 |
| pulse 2 | 2A03 square, the middle entry, the answer and countersubjects | 25 percent (CC12 = 1) | 88 |
| triangle | 2A03 triangle, the bass entry, the walking episode and the six-four | n/a | n/a |
| noise | 15 bit LFSR, a closed hat on EVERY eighth (velocity 66 on the beat, 78 off it) | n/a | 25 percent gain |
| dpcm | kick on beats 1 and 3, snare on beats 2 and 4, the backbeat | n/a | 118 / 108 |

That is the audible difference from v1, which had hats only on the off-beat eighth and a
snare on beat 3: here the subdivision is filled and the snare lands on 2 and 4.

Delayed NES vibrato as on v1: CC1 depth 4 with CC20 onset 1 eighth on pulse 1, depth 3 with
onset 2 eighths on pulse 2. Rendered by `tools/render_chip.py --humanize`. The Musikage
Dn-FamiTracker route was not used, for the reason recorded in v1's notes: `dnft.py` renders
a .dnm module and this project has no .dnm writer for a three part counterpoint line.

## The measurement

`tools/counterpoint/check.py` (profile free, key declared A minor) and `clash.py`:

| measure | v2 | v1 for comparison |
| --- | --- | --- |
| hard findings | **0** | 0 |
| soft findings | 2 (CP-14 voice overlap, CP-15 spacing) | 2 |
| style findings | 1 (CP-06) | 0 |
| raw clashes (all pairs) | 1, none on a downbeat | 0 |
| dissonances judged | 14 | 10 |
| devices | passing 9, appoggiatura 1, neighbour 1 | passing 8, suspension 1 |
| pitched notes | 242 (pulse 1 91, pulse 2 90, triangle 61) | 240 |
| voices in range | 0 out of range | 0 |
| cue gate, `--no-baseline` | PASS (exit 0) on the MIDI and the humanized MIDI | PASS |
| originality (`melody_guard.py` against `projects/musikage`) | PASS, 32 references, longest identical interval run 7, best 5-gram Jaccard 0.0000 | not run on v1 |

The one style finding is CP-06; it is a taste rule, not a hard one, and it is left in the
count rather than argued away. The noise and dpcm tracks are unpitched, so the checker
ignores them; the drive lives in the pitched voices the rules judge.

## Loudness and loop

| measure | value |
| --- | --- |
| render | 22.857 s, peak -1.00 dBFS, RMS -14.01 dBFS (humanized) |
| delivered OGG | **-14.04 LUFS integrated, -1.21 dBTP**, LRA 3.2 LU |
| target | -14.0 LUFS, ceiling -1.0 dBTP |
| loop | 16 bars, 1008000 samples, seam sample difference 0, head edge peak 2399 |

## The ear

No Gemini ear read on this take: the ear critic needs `GEMINI_API_KEY` and the session that
built v2 had no key in its environment, so no call was made and no score is written here in
its place. v1's two rounds are in `data/ear_ledger.csv` and `assets/audio/ear_reviews/`.

Hook meter (`tools/hook_score.py`, melody track `pulse 1`): **61 / 100**. As with v1, a fugue
exposition is the worst shape for a meter that wants a repeated two bar hook; read it as a
form note, not a defect.

## Files

| file | what it is |
| --- | --- |
| `pp_04_fight_baroque_v2.mid` | the score, five tracks (three pitched, noise, dpcm) |
| `pp_04_fight_baroque_v2_humanized.mid` | the renderer's chip legal humanization |
| `pp_04_fight_baroque_v2.wav` | the raw 2A03 render (gitignored) |
| `pp_04_fight_baroque_v2_master.wav` | the master before the lossy encode |
| `pp_04_fight_baroque_v2.ogg` | the delivered file, -14.04 LUFS / -1.21 dBTP |
| `pp_04_fight_baroque_v2.mp3` | MP3 of the same master |
| `pp_04_fight_baroque_v2_loop.json` | loop point in samples and seconds |
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

    .venv/Scripts/python.exe tools/counterpoint/m3_build.py --piece fight --variant 2 \
        --asset-dir assets/audio/pp_04_fight_baroque_v2 \
        --slug pp_04_fight_baroque_v2 --loop-bars 16
