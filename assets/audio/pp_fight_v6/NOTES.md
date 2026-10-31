# PP-04 FIGHT, fight module, v6 notes. Card AUTO-MUSIC-NEXT (t_7417cbca), written 2026-10-26.

Clean room: every change here is written from this project's own knowledge files. Nothing is
quoted from any published game. `pp_fight/`, `pp_fight_v2/`, `pp_fight_v3/`, `pp_fight_v4/` and
`pp_fight_v5/` are untouched; every file in this folder carries `_v6`.

## Why this module

`score_table_before.txt` (the same script, run on the ledger before this pass) puts the floor of
the current cue versions on `pp_fight_fight` at 30 of 60 on `gemini-3.5-flash`. That row is v3. It
is the same module v4 and v5 carried forward byte for byte: v4's and v5's notes both say the fight
module was not changed, so the loud half of this cue has not been through the ear loop since
2026-10-25 while the calm half was rebuilt three times.

The one thing the fight module has never carried is a declared dissonance device. The calm has
carried three since v5 (`dissonance` in `build_report_v5.json` lists DIS-02, DIS-06 and DIS-17,
all in the calm). The fight had none, so the tension axis was riding on the lead's written cell
alone.

## The score table, before and after

Both rows are one call each, same model, same session, same render flags (`render_chip.py
--humanize`, 16 bar loop, 192k mp3), back to back at 13:16 and 13:17 UTC on 2026-10-26. The
before row is a fresh render of v5's own fight MIDI (`ref_v5_fight_humanized.mp3`), not an older
read, because the previous v5 fight read does not exist: v4 and v5 never changed the module.

| read | file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before, v5 fight, rendered today | `ref_v5_fight_humanized.mp3` | 6 | 4 | 5 | 3 | 6 | 5 | **29** |
| after, v6 fight | `pp_fight_v6_fight.mp3` | 7 | 4 | 5 | 3 | 6 | 5 | **30** |

One point up on hook, nothing down. That is inside the spread this cue shows between listeners, so
the honest reading is "no loss and one point of gain in the paired read", not "a better cue". The
model that scored both is `gemini-3.5-flash-lite`, the judge that has room in its daily bucket
today (10 calls used, `gemini-3.5-flash` is at 22).

Reviews: `assets/audio/ear_reviews/ref_v5_fight_humanized_20261026T131747Z.md` and
`assets/audio/ear_reviews/pp_fight_v6_fight_20261026T131630Z.md`.

## What v6 changes, and the measure for each

| change | rule it answers | measure |
| --- | --- | --- |
| DIS-09 anticipation in the counter, bar 8: `Bb3` on the last eighth of the A7, the same pitch a chord tone of the Gm at the bar line | `MUSIC-DISSONANCE.md` DIS-09, risk 1, rate 0.5 to 2 | `build_report_v6.json` `fight_dissonance`, checked by `check_pp_fight_v6.py` |
| DIS-11 dominant flat nine in the counter, bar 12: `Bb4` on beat 1 over the A7, falling a semitone onto `A4`, prepared by the `F4` a whole tone below at the end of bar 11 | DIS-11, risk 3, rate 0 to 1 per cue | same row; the cue spends one risk 3 device, the calm spends none |
| DIS-02 chromatic lower neighbour in the counter, bar 15: `A3` on the and of 2, a semitone under the third of Gm, back up onto `Bb3` on beat 3 | DIS-02, risk 1, rate 1 to 3 per 8 bars | same row; two risk 1 devices in sixteen bars |
| all three in `vrc6 pulse b`, never in bar 1 or bar 16 | the hook must not move: `hook_score.py` reads only the lead track | hook meter 100 of 100 before and after, 6 returns on the fight |
| the kit's middle phrase moves off the BAT-01 skeleton: bars 5 and 7 to `BAT-04`, so the four bar phrases carry four different rung sets and the eight bar halves carry two | the card's "drums vary every 4 and every 8 bars" | `fight_kit_4_bar_states` four distinct sets, `fight_kit_8_bar_states` h1 `BAT-01`,`FLF-01` against h2 `BAT-04`,`BAT-06`,`BAT-02`,`FLT-01`,`BAT-05`,`FLR-01`,`BAT-03`,`BAT-07`,`BAT-09` |
| an eight bar layer on top of the four bar one: `EIGHT_BAR_GAIN` 1.0 then 1.06 and `EIGHT_BAR_TIMBRE` 0 then -1 | same | `eight_bar_gain`, `eight_bar_timbre` in the report |
| the fight's articulation varies by four bar phrase (16, 20, 14, 18 ticks of cut) instead of one flat 18 | human feel; the calm already did this in v5 | `fight_articulation_by_phrase`, and the check proves three distinct values |
| per note accents on the counterline, `[4, -3, 2, -4, 3, -2]` cycled | human feel; the lead had accents, the counter was flat | `counter_accent` in the report |

Nothing else moved: 168 bpm, D minor, 16 bars, 22.857 s loop, the eight voices, the hook cell, the
seam. The seam is still proved from the written notes and still reads 0 samples on both loop
modules, and the fight's bar 16 against the calm's bar 1 is identical in lead and triangle, which
is what keeps the state pair interchangeable.

## Checks

`check_pp_fight_v6.py` prints the card's checks as one table, now 28 rows, all PASS
(`check_output.txt`). It covers the nine files, the three module lengths, both loop seams, both
hook meters, the calm kit ladder and fills, the calm's three devices, and five new rows for this
pass: the fight's three devices and their voice, the fight kit's eight distinct rungs, the four
bar phrases differing, the eight bar halves differing, and the phrase articulation.

## Rounds

Two ear calls this pass (v5's fight re-rendered, then v6), which is round 1 of the card's 4 round
cap. The budget was spent on the build and the paired read, so no second round was run.

## Files here

| file | what it is |
| --- | --- |
| `build_pp_fight_v6.py` | v5's builder plus the fight devices, the 4 and 8 bar kit states, the phrase articulation and the counter accents |
| `build_report_v6.json` | devices, both kit state tables, articulation, accents, seam and voice check |
| `check_pp_fight_v6.py`, `check_output.txt` | the card's checks, 27 rows, all PASS |
| `pp_fight_v6_{fight,calm,states}.{mid,wav,mp3}` | the three modules, rendered with `--humanize` |
| `hook_report_{calm,fight}_v6.json` | 100 of 100 on both |
| `ref_v5_fight_humanized.{wav,mp3}` | v5's fight MIDI re-rendered with this pass's flags, for the paired before read |
| `score_table_before.txt`, `score_table_after.txt` | the table before and after this pass |
| `ear_with_user_env.py` | reads `GEMINI_API_KEY` from the Windows user store for `tools/ear_critic.py` |
