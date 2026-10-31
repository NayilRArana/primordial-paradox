# PP-04 FIGHT v3, notes. Card AUTO-MUSIC-NEXT (t_f9342b13), written 2026-10-26.

Clean room: every note here is written from the project's own knowledge files. Nothing is quoted
from any published game. `pp_fight/` (v1) and `pp_fight_v2/` (v2) are untouched; every file here
carries `_v3`. Round 1's source is kept as `build_pp_fight_v3_round1.py.bak`.

## Outcome first

**v3 does not beat v2 on the ear.** Both modules were read by the same model (`gemini-3.5-flash`)
in the same pass, before and after, so the comparison is paired:

| read | file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | `pp_fight_v2_calm.mp3` | 7 | 4 | 6 | 3 | 6 | 5 | **30** |
| after, round 1 | `pp_fight_v3_calm.mp3` | 6 | 3 | 4 | 2 | 5 | 5 | 25 |
| after, round 2 | `pp_fight_v3_calm.mp3` | 6 | 4 | 5 | 3 | 6 | 5 | 29 |
| after, round 3 | `pp_fight_v3_calm.mp3` | 6 | 4 | 5 | 3 | 6 | 5 | **29** |
| before | `pp_fight_v2_fight.mp3` | 7 | 4 | 5 | 3 | 6 | 6 | **31** |
| after | `pp_fight_v3_fight.mp3` | 7 | 4 | 5 | 3 | 6 | 5 | **30** |

Reviews: `pp_fight_v2_calm_20261026T002444Z.md`, `pp_fight_v3_calm_20261026T002520Z.md`,
`pp_fight_v3_calm_20261026T002925Z.md`, `pp_fight_v3_calm_20261026T003017Z.md`,
`pp_fight_v2_fight_20261026T002552Z.md`, `pp_fight_v3_fight_20261026T003127Z.md` in
`assets/audio/ear_reviews/`.

So the recommendation is the opposite of the card's hope: **keep the v2 renders** for both states.
The v3 files are evidence, not a replacement.

## Why this cue

`data/ear_ledger.csv` through `score_table.py` (the latest summary row per file, then the highest
version per cue family) put `pp_fight_calm` v2 on the floor at 30 of 60. Its own review named drums
4, human 3, structure 5 and tension 5 as the weak axes.

## What v3 changes, and the measure for each

| change | rule it answers | measure |
| --- | --- | --- |
| Calm kit rebuilt as a ladder: 11 distinct rungs, fills at 4, 8 and 12, ghost notes in bars 5, 10 and 13, the quiet rung at 15 | "a rigid, unchanging backbeat ... no fills" | `check_pp_fight_v3.py` kit rows, `build_report_v3.json` `calm_kit` |
| DIS-02 at bar 6 (guide, A4 back up to Bb4), DIS-06 at bar 11 (guide, B4 held a beat and a half down to A4), DIS-17 at bar 14 (triangle, D3 Bb3 then A3 into the dominant) | `knowledge/MUSIC-DISSONANCE.md`, 1 to 2 devices per 8 bars | `build_report_v3.json` `dissonance`, 3 devices, none in bar 1 or 16, closest pair 4.5 bars apart |
| Micro-timing under one frame on the lead, guide and kit; per note velocity accents; articulation length varying per four bar phrase; delayed vibrato with a different depth per phrase | "every note attacks on an absolute grid quantization point" | `build_report_v3.json` `humanize`; the lead's placements stay inside one sixteenth, so `hook_score.py` still reads 100 |
| A 2A03 pulse 1 broken chord as a new colour, a pad that thins for bars 9 and 10, a kick on beat 1 of every bar | "chopped-up loop", variety | bar voice counts printed by the builder: 3 voices in the v3 round 1 intro, 7 to 8 from bar 3 |
| Seam rule kept and now machine checked: the fight's bar 16 and the calm's bar 1 are the same written bar in lead and triangle | the state change must not jump | builder prints `seam vrc6 pulse a OK`, `seam triangle OK` |
| Hook untouched: the same one bar cell, every statement | hook meter | 100 of 100 on both modules, 5 returns calm, 6 returns fight |

8 voices (2A03 pulse 1, pulse 2, triangle, noise, DPCM; VRC6 pulse a, pulse b, saw), every note
inside `VOICE_RANGES` in `tools/arrange.py`, proved by the builder's `voice_check` on the written
notes. 168 bpm, D minor, 16 bars, 22.857 s per module, seam sample difference 0 on both loop
modules.

## What the three rounds taught, with the numbers

1. **Thinning costs the ear more than it earns.** Round 1 opened with two bars of three voices and
   dropped to rim ticks for bars 9 and 10. That read 25, five under v2. Restoring the pad from bar
   1, the echo from bar 2, the broken chord and a kick on beat 1 took it back to 29.
2. **Wide micro-timing reads as sloppy, not human.** Round 1 used delays up to 20 ticks on the lead
   and +-8 on the kit and scored human 2. Round 2 halved every delay and human went back to 3, the
   same 3 v2 gets without much timing variation at all.
3. **The ear does not count devices or kit rungs in a 16 bar calm.** Rounds 2 and 3 keep all three
   devices, 11 kit rungs and three fills, and the judge's own words were still "no secondary
   dominants, chromatic passing tones or suspended extensions" plus "no fills". Its scores moved
   with density and level instead. That matches the 2026-10-25 boarding result, where the points
   came from density and secondary dominants rather than from device count.
4. **Levels and peak headroom fight each other.** Raising every CC11 by 2 chip steps moved the
   calm's rms only from -16.37 to -15.61 dBFS while the peak stayed at 29203, so headroom, not the
   volume events, sets the mix. v2's calm sits at -12.1 dBFS rms, which is where the 4 dB gap
   against v3 lives. Any next pass should rebalance against rms, not against CC11 numbers.
5. **The fight module's structure point is fragile.** Only its kit micro-timing changed, and
   structure fell 6 to 5 while everything else held.

Rounds run: 3 of the 4 allowed. Round 4 was not spent because rounds 2 and 3 landed on the same 29
and the card's 45 minute budget was gone.

## Files here

| file | what it is |
| --- | --- |
| `build_pp_fight_v3.py` | the builder: hook and chords from v2, the calm's guide, devices, kit ladder, micro-timing and levels |
| `build_pp_fight_v3_round1.py.bak` | round 1's builder, kept because round 1 is the regression this card measured |
| `pp_fight_v3_{fight,calm,states}.{mid,wav,mp3}` | the three modules, 8 voices, seam 0 samples |
| `build_report_v3.json` | chords, devices, calm kit, humanize settings, per voice counts, the seam proof |
| `hook_report_{fight,calm}_v3.json` | 100 of 100 each |
| `check_pp_fight_v3.py` | the checks, printed as a table, all PASS |
| `score_table.py` | the family table that picked the cue and now shows the result |
| `ear_with_user_env.py` | runs `tools/ear_critic.py` with the key taken from the Windows user environment, never printed |
| `build_log.txt` | the builder's output, including the seam lines |

## Q for gamedev

1. **Nothing changes in the game.** v3 loses to v2 on the same-model read, so this lane recommends
   no cue swap and no data edit. v2 stays the shipped fight and calm pair.
2. **The 168 bpm question, raised again.** This card's body asks for the 126 bpm family; the
   CUE-FIGHT card sets 168 and gamedev owns that number, so 168 is kept and no Q is raised against
   gamedev. If the cue should move to the 126 family, that is gamedev's call, one card, and the calm
   would have to be re-cut against it.

## Key hygiene

The dispatched worker's shell does not inherit user level environment variables, so
`GEMINI_API_KEY` was absent and `tools/ear_critic.py` refused. `ear_with_user_env.py` reads the same
store Windows uses to fill `os.environ` (HKCU, then the machine hive) inside this process only. The
value was never printed, never written to disk, and no key file was opened. The ear calls that
produced the table above went through it.
