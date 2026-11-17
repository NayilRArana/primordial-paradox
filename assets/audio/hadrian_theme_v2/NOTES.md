# hadrian_theme_v2, card t_03b3d044 (AUTO-MUSIC-NEXT), 2026-11-17

Version 2 of the Hadrian (H) leitmotif cue. Version 1 lives untouched at
`assets/audio/hadrian_theme/`; this folder carries the new take and every report it was built from.

## Files

| File | What it is | sha256 |
| --- | --- | --- |
| `score_hadrian_v2.yaml` | the score, v1 schema and comments, only the H and H4 bars changed | a178102154a4c1c769c41d11f1658621fb327a1b774ab9b206c56939ee2e3bd7 |
| `score_check_v2.json` | 19 checks on the score text, 19 passed, 0 failed | - |
| `hadrian_theme_v2.mid` | the arrangement, 8 tracks, ppq 480, 4/4, 92 bpm, 32 bars | b2652c388d1e497db9c1972237caaccf40458aed4d2707e94451d481e6bfe75d |
| `arrange_report_v2.json` | 32 bars, duration 83.478 s, lead 53 notes, answer 20, saw 32, triangle 32, hats 96, kick 64, hum 512, pulse 1 silent | - |
| `hadrian_theme_v2.wav` | 44.1 kHz mono 16 bit render, peak -1.00 dBFS, rms -19.22 dBFS | aeb2f396efc7c0ad5f4b8ed28247caf4792824381312ddbb677be13154c208a7 |
| `hadrian_theme_v2.mp3` | 192k mp3 of the same render | - |
| `hadrian_theme_v2_loop.json` | 32 bars, 83.478277 s, 3,681,392 samples, seam sample difference 0 | - |
| `hook_report_v2.json` | the hook score: 97 of 100, 1 criterion short | 834fcd4c7021b6920a93b071702b4196524b7c3cb8f7fa27fa4484ca873ab7e3 |
| `melody_guard_v2.json` | originality against `Shared/projects/musikage`: PASS, jaccard 0.0000, longest identical interval run 3 | - |

## What changed from v1

Seven bars of the lead and four bars of the fugue answer gained a one eighth answering lift at the end
of the bident, and the third entrance lifts to the dominant:

- bars 1, 5, 12, 21, 25: `D5 C#5 (rest) A4 G#4` becomes `D5 C#5 (rest) A4 G#4 D5`; the phrase now rises
  to one peak and falls, so it reads as an arch instead of a bare fall, and the G#4 to D5 lift is the one
  six semitone leap in the motif.
- bar 9, the card's own check bar, and bar 17: the lift goes to `A4` and to `Bb4`, so the third return is
  a variation (80 percent the same as the first) and not a copy. Bar 9's first two beats are still
  `D5` then `C#5` as quarters, which is what `check_hadrian_score.py` proves.
- the H4 answer on `vrc6 pulse b` (bars 11, 14, 19, 22) takes the same lift, so the answer breathes with
  the subject. Its first four pitches are unchanged.

Nothing else moved: 32 bars, 92 bpm, D minor, 4/4, the chord frame, the Neapolitan Eb at bars 7, 15 and
23, the Picardy turn to D major in bars 29 to 32, the voices block, the textures, the arranger profile,
the drums, the loop points.

The rest between the two prongs is one eighth shorter (the lift takes that eighth). The lead still rests
in 14 of 32 bars, the silence the cue is built on.

## Numbers

- Hook score 81 to 97 of 100 (`tools/hook_score.py`). Contour 0 to 10, leaps per motif 4 to 8, variation
  on the third return 3.2 to 8, motif coverage 20 to 20 at 66 percent, steps over leaps 12 to 9.2.
- The remaining 2.8 points are `steps over leaps`: the motif holds the bident's fourth drop (`C#5` to
  `A4`) plus the one leap, so 2 of 4 intervals are steps. Reaching 65 percent would mean breaking the
  bident's shape or its documented rhythm, which this lane does not own.
- Loop seam: `loop_seam_sample_difference` 0 on 3,681,392 samples, head edge peak 1410, tail edge peak 0,
  32 bars of 83.478277 s at 92 bpm, same as v1.
- Voices in the render: dpcm, noise, pulse 2, triangle, vrc6 pulse a, vrc6 pulse b, vrc6 saw; pulse 1
  absent. Peak simultaneous voices per section 6, inside 2A03 plus VRC6 (5 plus 3, with the DPCM and the
  noise shared as the arranger already does).

## Checks run

```
python tools/check_hadrian_score.py assets/audio/hadrian_theme_v2/score_hadrian_v2.yaml \
    --json assets/audio/hadrian_theme_v2/score_check_v2.json        -> 19 passed, 0 failed
python tools/arrange.py assets/audio/hadrian_theme_v2/score_hadrian_v2.yaml \
    -o assets/audio/hadrian_theme_v2/hadrian_theme_v2.mid \
    --report assets/audio/hadrian_theme_v2/arrange_report_v2.json   -> 32 bars, 83.478 s
python tools/hook_score.py assets/audio/hadrian_theme_v2/hadrian_theme_v2.mid \
    --json assets/audio/hadrian_theme_v2/hook_report_v2.json        -> 97 / 100
python tools/melody_guard.py assets/audio/hadrian_theme_v2/hadrian_theme_v2.mid \
    "<workspace>/Shared/projects/musikage" \
    --json assets/audio/hadrian_theme_v2/melody_guard_v2.json       -> PASS
python tools/render_chip.py assets/audio/hadrian_theme_v2/hadrian_theme_v2.mid \
    assets/audio/hadrian_theme_v2/hadrian_theme_v2.wav --loop-bars 32 \
    --loop-json assets/audio/hadrian_theme_v2/hadrian_theme_v2_loop.json
    -> seam sample difference 0
```

## Open

1. No ear round ran: `GEMINI_API_KEY` is not in this lane's environment, so `tools/ear_critic.py` refuses.
   This is the second AUTO-MUSIC-NEXT card in a row where the ear loop could not start.
2. The cue is 92 bpm by its own card (MUS-HADRIAN) and by check 2 of `check_hadrian_score.py`. The
   AUTO-MUSIC-NEXT card asks for the 126 bpm family, so the tempo is a spec question, not a bug.
3. The drums are the cold profile: kick on beats 1 and 3, hats on beats 1 and 3 in eighths, and they do
   not vary every 4 and 8 bars, which the AUTO-MUSIC-NEXT card also asks for. Changing that changes the
   cue's identity, so it is left as a question.
