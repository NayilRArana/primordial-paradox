# Ear critic calibration against Nayil's ear (M4, card t_aa3ab04e, 2026-10-30)

Why this note exists: the ear critic ranked the title takes Nayil called dissonant as the best title
music in the tree, so a critic score alone cannot be the thing that decides a cue
(knowledge/COUNTERPOINT-PLAN-2026-10-26.md lines 10 to 12). This note records the picks, the verdicts,
and the arithmetic that now stops a score from rising while clashes do
(tools/ear_loop.py lines 354 to 375).

## What the critic picked

Every row below is one ledger summary row, six rubric lines, and the total is their sum
(data/ear_ledger.csv lines 146, 148 and 237; tools/ear_loop.py lines 381 to 387).

| sitting | file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10-24T19:19:37Z | pp_01_title_v7 | 8 | 5 | 6 | 4 | 8 | 7 | 38 |
| 2026-10-24T19:21:30Z | pp_01_title_v8 | 7 | 5 | 6 | 4 | 7 | 8 | 37 |
| 2026-10-26T19:04:37Z | pp_01_title_v7 | 8 | 6 | 7 | 5 | 8 | 7 | 41 |
| 2026-10-26T19:04:37Z | pp_01_title_v9 | 5 | 7 | 5 | 6 | 5 | 5 | 33 |

The two takes the critic scored highest across the catalogue are v7 and v8, which is what the plan
records as the failure (knowledge/COUNTERPOINT-PLAN-2026-10-26.md lines 10 to 11): v7 leads v8 by one
point in the 2026-10-24 sitting, and it leads the repaired v9 by 8 points in the back-to-back compare,
which is outside the judge's own one point per criterion noise floor
(knowledge/TITLE-DISSONANCE-2026-10-26.md lines 185 to 188).

## What the ear said

Nayil's verdict on both top-scoring titles: the music "are a bit dissonant"
(knowledge/COUNTERPOINT-PLAN-2026-10-26.md lines 3 to 4). That is the human verdict this gate is
calibrated against, and it is recorded on the two approval rows in data/cue_ear_approvals.json so the
gate notes them instead of blocking them (data/cue_ear_approvals.json, entries 1 and 2).

## What the clash counter measured

Measured on 2026-10-30 with `python tools/counterpoint/cue_gate.py <file>` under the project
interpreter `<home>/AppData/Local/Python/bin/python.exe`:

| cue | critic total | raw clashes | raw clashes on a strong beat | bars | clash dose per bar | clean share | final |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pp_01_title_v7 | 38 | 196 | 30 | 52 | 0.8962 | 0.1038 | 3.95 |
| pp_01_title_v8 | 37 | 204 | 35 | 52 | 0.9981 | 0.0019 | 0.07 |
| pp_01_title_v7 | 41 | 196 | 30 | 52 | 0.8962 | 0.1038 | 4.26 |
| pp_01_title_v9 | 33 | 2 | 0 | 52 | 0.0038 | 0.9962 | 32.87 |

The dose is `(strong + 0.1 * (raw - strong)) / bars`, the share is `max(0, 1 - dose / 1.0)`, and the
final is the critic total times the share (tools/ear_loop.py lines 406 to 434). One clash per bar takes
a whole score, and a clash off the strong beat counts a tenth of one, because the same counter counts
the passing and neighbour tones the style wants (tools/ear_loop.py lines 358 to 369).

## The order under each rule

The compare sitting inverts the critic's ranking:

    2026-10-26  critic order:         ['pp_01_title_v7', 'pp_01_title_v9']
                clash weighted order: ['pp_01_title_v9', 'pp_01_title_v7']

The earlier sitting keeps v7 above v8, but both of them fall to almost nothing while the critic called
them a one point apart: 3.95 against 0.07 (the probe run above, 2026-10-30). So the critic's two top
picks are the two cues with the largest clash debt in this comparison, which is exactly the ranking the
gate exists to stop (knowledge/COUNTERPOINT-PLAN-2026-10-26.md lines 32 to 33).

The gate's own verdicts on the same files are GRANDFATHERED for v7, GRANDFATHERED for v8 and LEGACY for
v9, so none of them is called clean (data/cue_ear_approvals.json and data/cue_gate_baseline.json).

## What is pinned, and what this note does not claim

`tests/test_ear_loop_clashes.py` pins the property rather than these numbers: the same critic score
falls as the clashes rise, a strong-beat clash costs more than one off the beat, and a higher critic
total cannot outrank a cleaner cue (tests/test_ear_loop_clashes.py lines 37 to 66).

Three limits, stated rather than smoothed over:

- The totals above come from two sittings, and a total is only comparable inside its own sitting:
  the 2026-10-24 rows and the 2026-10-26 rows are different sessions even where the same file was
  scored (data/ear_ledger.csv lines 146, 148 and 237).
- v9's 33 was measured on the first build of v9, before the anticipation rule was widened and before
  the pedal fix, so it is not the shipped file's number
  (knowledge/TITLE-DISSONANCE-2026-10-26.md lines 176 to 178).
- The weighted score is a floor on honesty, not a judge of taste. The critic's reason for preferring v7,
  a lead that sits above the accompaniment, is something the clash counter cannot hear, and the repair
  that keeps that bite with a preparation in front of it and a resolution behind it is the musician's
  call (knowledge/TITLE-DISSONANCE-2026-10-26.md lines 186 to 190).

Full cue census for the day this note was written: 137 cues under assets/audio, 11 PASS, 2
GRANDFATHERED, 120 LEGACY, 1 REFUSED and 3 UNMEASURED, produced by tools/counterpoint/cue_gate.py (the
census JSON is attached to card t_aa3ab04e).
