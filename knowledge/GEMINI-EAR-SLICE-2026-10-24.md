# GEMINI EAR SLICE, four cues, 2026-10-24

Card GEMINI-EAR-SLICE (t_eb99e5e3), created 2026-10-23 by gamedev, run on the testing lane through EAR-ROTATE (t_154766b8). Written 2026-10-24 by the testing lane. Scope: this file only; no audio asset was edited and no key or login file was opened.

The job: one ear verdict per new cue, each quoting the gate criterion it passes or fails by name, the model recorded per cue, and one cue named first. The criteria are not restated by invention: `knowledge/EAR-GATE-2026-10-23.md` section 1 owns the four gate axes and their ceilings, and section 2 owns the scores the earlier rows were given.

## 1. The judge, per cue

| # | cue | file scored | model | hook | drums | tension | human | variety | structure | total | review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PP-02 drive | `assets/audio/pp_drive/pp_drive_v3_humanized.mp3` | `gemini-3.5-flash-lite` | 6 | 4 | 5 | 3 | 6 | 5 | 29 | `assets/audio/ear_reviews/pp_drive_v3_humanized_20261023T094326Z.md` |
| 2 | PP-03 arrival, night quay | `assets/audio/pp_arrival/pp_arrival.mp3` | `gemini-3.5-flash-lite` | 7 | 4 | 5 | 3 | 6 | 6 | 31 | `assets/audio/ear_reviews/pp_arrival_20261023T094334Z.md` |
| 3 | PP-06 boarding | `assets/audio/pp_boarding/pp_boarding.mp3` | `gemini-3.5-flash-lite` | 6 | 4 | 5 | 3 | 6 | 5 | 29 | `assets/audio/ear_reviews/pp_boarding_20261023T094341Z.md` |
| 4 | PP-04 fight | `assets/audio/pp_fight/pp_fight_states.mp3` | `gemini-3.5-flash-lite` | 7 | 5 | 4 | 3 | 8 | 6 | 33 | `assets/audio/ear_reviews/pp_fight_states_20261023T094348Z.md` |

The scores above are the run's own summary rows in `data/ear_ledger.csv`, dated `2026-10-23T09:43`, column `model`; the same rows sit in `data/ear_loop_state.json` under run `20261023T094318Z`.

Every one of the four cues came back on the first model in the order, so no quota failure happened inside this run: four calls, four reviews, `assets/audio/ear_reviews/` written at 09:43.

Rotation is proved rather than assumed. This card re-ran the offline check, which simulates a 429 on the first model and needs no network and no key; the output, verbatim:

```
self check: simulated 429 on gemini-3.5-flash-lite, fallthrough to gemini-3.5-flash
cues scored: 4 of 4
models used: gemini-3.5-flash
state marked: gemini-3.5-flash-lite
RESULT: PASS
```

So a quota failure rotates to the next model, the failed model is marked exhausted in `data/ear_loop_state.json`, and the run still returns four verdicts; the stub ledger and stub reviews for that check stay in `cache/ear_loop_stub/` and never touch `data/ear_ledger.csv` (`tools/ear_loop.py`, `_self_check`).

## 2. The criteria, quoted, and the pass rule

| axis | the gate's words for what a fix has to change | ceiling in the 17 file sweep |
| --- | --- | --- |
| drums | "the kit: pattern id, rung length, fill id, ghost level" | 5 |
| tension | "harmonic colour: an altered chord, a stab, a pedal" | 6 |
| human | "note length and gate, velocity steps, vibrato events" | 4 |
| structure | "section contrast, a hole before a return, level per section" | 7 |

The table's words and ceilings are `knowledge/EAR-GATE-2026-10-23.md` section 1, the same four lines quoted in the verdicts below.

The gate file gives ceilings, not pass marks, so this slice states its rule instead of inferring one: a score at or above the ceiling passes that axis, and a score below the ceiling fails it. Hook and variety are recorded in the table and are not gated, because the gate keeps them out of the ranked list for already sitting at their ceiling (`knowledge/EAR-GATE-2026-10-23.md` section 1).

### 2.1 The hook grammar's part, which changes no score here

`knowledge/MUSIC-HOOK-GRAMMAR.md` is the declared input for the hook column and it is used as a target, not as a gate. Its own rule of thumb is recognition time: people recognised well known songs in about 5 seconds on average, the fastest answers at 2.29 s for "Wannabe" (`knowledge/MUSIC-HOOK-GRAMMAR.md` section 1.1, source [S45]). At this cue family's 126 bpm in 3/4 one bar is 1.4286 s, so four bars is 5.7143 s and the 5 s marker lands at bar 3.5 (arithmetic on the bar lengths `knowledge/MUSIC-HOOK-GRAMMAR.md` section 1.2 gives for other tempos).

On the ear's own timing the drive states its theme later than that: it times the intro at 0:00 to 0:35 and calls the lead there a "rising, arpeggiated motif" before the main theme (`assets/audio/ear_reviews/pp_drive_v3_humanized_20261023T094326Z.md` line 16). That is recorded as an observation and not as a verdict, for two reasons this card has to hold to: the hook axis is not gated (`knowledge/EAR-GATE-2026-10-23.md` section 1), and the ear's section timings are the part of its output the gate already declares unreliable (`knowledge/EAR-GATE-2026-10-23.md` section 5). No score and no ranking in this file moves on it.

## 3. The four verdicts

### Verdict 1, PP-02 drive: fails drums, tension, human and structure; 5 points available

- drums 4 against a ceiling of 5, so it fails "the kit: pattern id, rung length, fill id, ghost level"; the ear's line is "the kick and snare pattern loops identically bar after bar, lacking the syncopation or dynamic ghost notes" (`assets/audio/ear_reviews/pp_drive_v3_humanized_20261023T094326Z.md` line 28).
- tension 5 against a ceiling of 6, so it fails "harmonic colour: an altered chord, a stab, a pedal"; the ear's line is "The harmony stays overwhelmingly safe, leaning heavily on major and minor triads" (`assets/audio/ear_reviews/pp_drive_v3_humanized_20261023T094326Z.md` line 30).
- human 3 against a ceiling of 4, so it fails "note length and gate, velocity steps, vibrato events"; the ear's line is "no pitch bend, no delayed vibrato, and no velocity scaling" (`assets/audio/ear_reviews/pp_drive_v3_humanized_20261023T094326Z.md` line 32).
- structure 5 against a ceiling of 7, so it fails "section contrast, a hole before a return, level per section"; the ear's line is "the emotional arc flatlines because the intensity resets immediately without a proper buildup" (`assets/audio/ear_reviews/pp_drive_v3_humanized_20261023T094326Z.md` line 36).
- the structure score has a shape in the file: A is 25 bars, B is 34 bars, and A_return is 66 of the cue's 125 bars starting at bar 60, so half the cue is one section (`assets/audio/pp_drive/arrange_report_v3.json`, `section_bars` and `section_first_bar`).
- the human score is the one that disagrees with the delivered file: the humanized MIDI now carries 423 controller 1 and 423 controller 20 events over 2846 note ons and 85 distinct velocities, where `pp_drive_v3.mid` carries 0 of each, a read only scan of `assets/audio/pp_drive/pp_drive_v3_humanized_humanized.mid` and `assets/audio/pp_drive/pp_drive_v3.mid`.
- so gate fix 3's measure, controller 1 and 20 events from 0 to at least 106, is met in the MIDI the humanized master was actually rendered from: `assets/audio/pp_drive/pp_drive_v3_humanized_loop.json` records `source_midi` as `pp_drive_v3_humanized_humanized.mid`, the file with 423 of each controller, and its `source_duration_seconds` of 178.550417 matches the humanized render `assets/audio/pp_drive/NOTES-v3.md` line 73 reports at 178.550 s. So the ear scored a file that already carries the fix's own measure and still gave human 3, the same 3 it gave `pp_drive_v2_humanized` on 2026-10-23 (`knowledge/EAR-GATE-2026-10-23.md` row 3).

### Verdict 2, PP-03 arrival: fails drums, tension, human and structure; 4 points available

- drums 4 against a ceiling of 5, so it fails "the kit: pattern id, rung length, fill id, ghost level"; the ear's line is "locked into the exact same rigid 16-step kick-snare loop for almost the entire track" and "There are no ghost notes, no fills" (`assets/audio/ear_reviews/pp_arrival_20261023T094334Z.md` line 28).
- tension 5 against a ceiling of 6, so it fails "harmonic colour: an altered chord, a stab, a pedal"; the ear's line is "harmony is strictly textbook major/minor triads" (`assets/audio/ear_reviews/pp_arrival_20261023T094334Z.md` line 29).
- human 3 against a ceiling of 4, so it fails "note length and gate, velocity steps, vibrato events"; the ear's line is "The vibrato is turned on and off like a light switch rather than naturally swelled into" (`assets/audio/ear_reviews/pp_arrival_20261023T094334Z.md` line 30).
- structure 6 against a ceiling of 7, so it fails "section contrast, a hole before a return, level per section"; the ear's line is "the transition back to the main theme at 1:04 feels abrupt rather than earned" (`assets/audio/ear_reviews/pp_arrival_20261023T094334Z.md` line 32).
- the drums complaint is contradicted by the cue's own build: the drum plan changes rung every section, 4 rungs over 16 bars in quay, 4 in lamplight, 5 over 12 in gate, 2 over 4 in turn (`assets/audio/pp_arrival/NOTES.md` line 61), so the ear heard the mix and not the plan.
- the human complaint is testable and thin: the delivered MIDI carries 22 controller 1 and 22 controller 20 events over 1093 note ons, against 106 of each over 1375 note ons in the harbor reference, a read only scan of `assets/audio/pp_arrival/pp_arrival.mid` and `assets/audio/pp_03_harbor/pp_03_harbor.mid`; the cue has about a fifth of the vibrato density the gate already treats as the working level.

### Verdict 3, PP-06 boarding: fails drums, tension, human and structure; 5 points available

- drums 4 against a ceiling of 5, so it fails "the kit: pattern id, rung length, fill id, ghost level"; the ear's line is "overall the percussion feels like a static metronome rather than a live-played kit" (`assets/audio/ear_reviews/pp_boarding_20261023T094341Z.md` line 26).
- tension 5 against a ceiling of 6, so it fails "harmonic colour: an altered chord, a stab, a pedal"; the ear's own exception is "save for a minor-third lift in the bridge around 0:18", one event in 32 s (`assets/audio/ear_reviews/pp_boarding_20261023T094341Z.md` line 27).
- human 3 against a ceiling of 4, so it fails "note length and gate, velocity steps, vibrato events"; the ear's line is "Every note is locked mercilessly to the grid with zero velocity variation" (`assets/audio/ear_reviews/pp_boarding_20261023T094341Z.md` line 28), and the MIDI agrees on the number, 1 controller 1 event over 419 note ons (read only scan of `assets/audio/pp_boarding/pp_boarding.mid`).
- structure 5 against a ceiling of 7, so it fails "section contrast, a hole before a return, level per section"; the ear's line is "the sections bleed into one another without distinct transitional fills or dynamic drops" (`assets/audio/ear_reviews/pp_boarding_20261023T094341Z.md` line 30).
- the structure verdict is the weakest instrument in this file: the cue is a 16 bar one shot that stops on a stab and two beats of air, so the loop mark is 0 of 6 by design (`assets/audio/pp_boarding/NOTES.md` lines 91 to 95, where the cue's own card calls both marks true and intended), and the gate itself says four of the six questions barely mean anything at that length (`knowledge/EAR-GATE-2026-10-23.md` section 5).
- work on this cue is also held open by gamedev: the scene row is 208 steps while the authored beat is 1920, so the cue's own length is a live question and a rewrite could be cut to nothing (`assets/audio/pp_boarding/NOTES.md`, Q1).

### Verdict 4, PP-04 fight: passes drums, fails tension, human and structure; 4 points available

- drums 5 against a ceiling of 5, so it passes "the kit: pattern id, rung length, fill id, ghost level"; it is the only axis pass in the four cues, and the ear's line still files a complaint next to the score, "they lack syncopation, fills, or dynamic timbre shifts" (`assets/audio/ear_reviews/pp_fight_states_20261023T094348Z.md` line 30).
- tension 4 against a ceiling of 6, so it fails "harmonic colour: an altered chord, a stab, a pedal", and it is the widest single gap in this slice at 2 points; the ear's line is "The harmony is resolutely diatonic and safe" (`assets/audio/ear_reviews/pp_fight_states_20261023T094348Z.md` line 32).
- the tension score agrees with the cue's own card, which names the C# leading tone in bar 4 as the one note outside D minor in the phrase and E flat in bar 9 as the only other chromatic note (`assets/audio/pp_fight/NOTES.md` section "The hook").
- human 3 against a ceiling of 4, so it fails "note length and gate, velocity steps, vibrato events"; the ear's line is "velocity/volume levels are completely static across all channels from 0:00 to 0:45" (`assets/audio/ear_reviews/pp_fight_states_20261023T094348Z.md` line 34), and the MIDI carries 2 controller 1 events over 700 note ons (read only scan of `assets/audio/pp_fight/pp_fight_states.mid`).
- structure 6 against a ceiling of 7, so it fails "section contrast, a hole before a return, level per section"; the ear's line is "the bridge at 0:22 doesn't offer enough harmonic contrast to feel like a true departure" (`assets/audio/ear_reviews/pp_fight_states_20261023T094348Z.md` line 38).

## 4. The scoreboard, and where the ear is not evidence

| cue | drums | tension | human | structure | points available to the ceiling | axes passed |
| --- | --- | --- | --- | --- | --- | --- |
| PP-02 drive | 4 | 5 | 3 | 5 | 5 | none |
| PP-03 arrival | 4 | 5 | 3 | 6 | 4 | none |
| PP-06 boarding | 4 | 5 | 3 | 5 | 5 | none |
| PP-04 fight | 5 | 4 | 3 | 6 | 4 | drums |

Points available is the four ceilings minus the four scores, so 18 points sits between these four cues and their ceilings (`knowledge/EAR-GATE-2026-10-23.md` section 1 for the ceilings, `data/ear_ledger.csv` for the scores).

The human axis is 3 on all four cues, and it is the axis whose ear evidence is thinnest: the same complaint arrives for a file with 1 vibrato event (`assets/audio/pp_boarding/pp_boarding.mid`) and for a file with 423 (`assets/audio/pp_drive/pp_drive_v3_humanized_humanized.mid`), so a 423 fold change in the measured thing moved the score by 0. Read human 3 as this judge's constant, not as a measurement of any cue; the gate's own fix list already grounds the human work in MIDI counts instead (`knowledge/EAR-GATE-2026-10-23.md` section 4).

The bar counts are wrong in all four reviews, which is the warning the gate already carries: the drive is heard out to "bars 111-150+" in a cue that is 125 bars (`assets/audio/ear_reviews/pp_drive_v3_humanized_20261023T094326Z.md` line 19 against `assets/audio/pp_drive/NOTES-v3.md` line 19), arrival is heard as six 8 bar sections running out to bar 48 where the score has four sections of 16, 16, 12 and 4 bars (`assets/audio/ear_reviews/pp_arrival_20261023T094334Z.md` lines 16 to 21 against `assets/audio/pp_arrival/NOTES.md` lines 15 to 18), boarding is heard to bar 30 where the cue is 16 bars (`assets/audio/ear_reviews/pp_boarding_20261023T094341Z.md` line 19 against `assets/audio/pp_boarding/NOTES.md` line 29), and the fight is heard to bar 48 where STATES is 32 bars (`assets/audio/ear_reviews/pp_fight_states_20261023T094348Z.md` line 22 against `assets/audio/pp_fight/NOTES.md` line 87).

## 5. How to check this file

- model per cue: `data/ear_ledger.csv`, summary rows dated 2026-10-23T09:43, column `model`; all four read `gemini-3.5-flash-lite`.
- rotation: `python tools/ear_loop.py --self-check` prints the five lines quoted in section 1 and ends `RESULT: PASS`; it needs no key and sends no audio.
- scores: `data/ear_loop_state.json`, run `20261023T094318Z`, `rows[*].scores`.
- vibrato counts: the read only MIDI scan attached to this card as `vibrato_probe.py` prints note ons, distinct velocities, controller 1 and controller 20 per file; run it with the six MIDI files named above as arguments.
- points available: subtract each row's four scores from 5, 6, 4 and 7 in that order.
- dashes: this file carries no em dash, en dash, figure dash or horizontal bar.

## 6. The one cue to fix first: PP-02 drive, on the structure axis

The rule this pick uses, stated so it can be argued with: take the cue with the most gate points available among the cues the slice already plays whose fix is not waiting on a gamedev decision. Drive and boarding tie at 5 points.

The drive wins that tie on three facts. It is the lowest total in the slice at 29, level with boarding and 2 under arrival and 4 under the fight (`data/ear_ledger.csv`). It is the cue whose scene slot the slice already plays, PP-02, and whose card argues the cue identity question in its favour while waiting on gamedev's confirmation (`knowledge/EAR-GATE-2026-10-23.md` row 3, `assets/audio/pp_drive/NOTES-v3.md` section 5 Q2). And its fix is not blocked: boarding's length is an open question against the 1920 step authored beat (`assets/audio/pp_boarding/NOTES.md`, Q1), while the drive's grid is settled at 125 bars on eleven cuts that all snap to a downbeat (`assets/audio/pp_drive/NOTES-v3.md` section 2).

The axis is structure, the 2 point gap, because the drive's other three gaps are already spent or already tried: the human gap is the one the humanize pass filled in the MIDI for 0 points of ear movement, and drums and tension sit 1 point each under their ceilings, which is inside the 1 point noise floor the 2026-10-22 sweep measured (`knowledge/EAR-GATE-2026-10-23.md` section 1). A 2 point structure gap is the only one on this cue that is bigger than the judge's own noise.

The measure to check, in the gate's own terms for structure: a hole before the return and a level per section. The hole is checkable today because there is none, A_return begins at bar 60 with no silent bar in front of it (`assets/audio/pp_drive/arrange_report_v3.json` `section_first_bar`), while the only hole the mix check reports is the drum hole at bars 24 to 26 (`assets/audio/pp_drive/mix_check_v3.json`, `engine_band_median_db`). The level per section is not measured for this cue yet; the form that would measure it is the one the ship cue already carries, section RMS per section in `assets/audio/pp_05_small_ship/measure_pp_05.json`, so the fix adds a per section RMS read and the section step it shows is the number the re-score is checked against. Fix that, re-score the one cue, and the drive moves from a 66 bar second half to a section that arrives; the ear's structure sentence is the one this slice takes at its word, because it is the only one of the four complaints the cue's own numbers agree with.
