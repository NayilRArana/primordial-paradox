# PP-04 FIGHT v4, notes. Card AUTO-MUSIC-NEXT (t_ceb25fd1), written 2026-10-26.

Clean room: every note here is written from the project's own knowledge files. Nothing is quoted
from any published game. `pp_fight/` (v1), `pp_fight_v2/` (v2) and `pp_fight_v3/` (v3) are
untouched; every file here carries `_v4`.

## Outcome first

**v4 does not beat v2 on the ear.** Two paired same-model reads, before and after, both on the
plain (not humanized) render of each file, so the pairing is like for like:

| listener | file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gemini-3.5-flash-lite` | `pp_fight_v2_calm.mp3` | 6 | 4 | 5 | 3 | 6 | 5 | **29** |
| `gemini-3.5-flash-lite` | `pp_fight_v4_calm.mp3` | 6 | 4 | 5 | 3 | 6 | 5 | **29** |
| `gemini-3.5-flash` | `pp_fight_v2_calm.mp3` | 6 | 4 | 5 | 3 | 6 | 5 | **29** |
| `gemini-3.5-flash` | `pp_fight_v4_calm.mp3` | 6 | 2 | 4 | 2 | 5 | 5 | **24** |

Reviews: `ear_reviews/pp_fight_v2_calm_20261026T003909Z.md`,
`pp_fight_v4_calm_20261026T003914Z.md`, `pp_fight_v2_calm_20261026T004036Z.md`,
`pp_fight_v4_calm_20261026T004107Z.md`.

So the recommendation is again **keep the v2 renders** for the calm, and one round of this card
found the direction that makes it worse rather than better. The v4 files are evidence, not a
replacement. Scores and review files are in `data/ear_ledger.csv` as usual.

## Why this cue, and what was actually left to try

`score_table.py` at 00:25 UTC put `pp_fight_calm` on the floor of the current versions, and card
t_f9342b13 (v3, three rounds, 2026-10-25) had already shown that adding devices, kit rungs and
micro-timing did not move this cue. Its own notes left one measurement unspent: v2's calm renders
at -12.10 dBFS rms and v3's at -15.61, and every render is peak normalized to -1.0 dBFS, so the
mix's loudness is set by whichever transient is tallest, not by CC11. That is the lever v4 pulled.

Measured here, all four renders normalized to the same peak of 29203:

| render | rms | crest factor |
| --- | --- | --- |
| `pp_fight_v2_calm.wav` | -12.10 dBFS | 11.1 dB |
| `pp_fight_v3_calm.wav` | -15.61 dBFS | 14.6 dB |
| `pp_fight_v4_calm.wav` | **-14.57 dBFS** | **13.6 dB** |
| `pp_fight_v4_fight.wav` | -14.09 dBFS | 12.7 dB |
| `pp_fight_v4_states.wav` | -15.66 dBFS | 13.8 dB |

v4 closes 1.0 dB of the 3.5 dB gap and stops there. The search was done by reading the sample the
peak sits on, not by guessing: the tallest sample was at bar 15 beat 1.03, a bar line where lead,
bass, pad, kick and noise all attack on the same sample.

## What v4 changes, and the measure for each

| change | why | measure |
| --- | --- | --- |
| DPCM kick lowered from velocity 62 to 38 (34 after bar 9) | v3's own comment blamed the kick for taking the peak; lowering it alone moved rms the wrong way (-15.61 to -16.46), which is the useful negative result here | rms table above; `build_report_v4.json` `calm_kit` unchanged apart from this |
| 6 tick flam on every DPCM hit (4.5 ms at 168 bpm) | the peak was a DPCM hit and a noise hit summing on one sample | rms -16.46 to -16.25 |
| Bar 15 kit removed rather than scaled to 0.32 | v3's notes claimed bar 15 was a hole; the code still wrote the CLM-02 pattern there. Now bar 15 carries one rim tick and nothing else, which is the "hole before the return" the structure axis asks for | `build_log.txt` calm bar 15 still lists kit voices for bar 16 only; rms -16.25 to -16.46 to -14.57 combined with the next row |
| Saw pad and triangle bass enter 15 ms and 7 ms behind the lead, from bar 2 | those were the two voices stacked on the same onset as the lead, so the bar line no longer sums five attacks on one sample | rms -16.25 to -14.57 |
| Sustained bed lifted: pad 66 to 74 (80 from bar 12), guide velocity 86 to 92, saw CC11 +2, guide CC11 +2, bass CC11 +2 | with the peak lowered, the bed is what the normalizer now scales against | rms table above |

Unchanged and re-proved: the 168 bpm, the D minor key, the 16 bar form, the one bar hook and every
statement of it (`hook_report_calm_v4.json` and `hook_report_fight_v4.json` both 100 of 100, 5 and
6 returns), the three devices DIS-02 at bar 6, DIS-06 at bar 11 and DIS-17 at bar 14, the kit
ladder (11 rungs, fills at 4, 8 and 12), 8 voices inside the 2A03 plus VRC6 ranges, and the seam.
`pp_fight_v4_fight.mid` is byte identical to `pp_fight_v3_fight.mid` (md5 80d42d60...), so the
fight module is v3's arrangement rendered again, not a new arrangement.

## What this pass teaches

1. **The peak is a summed onset, not one loud instrument.** Lowering the loudest single hit gave
   back nothing (rms fell 0.85 dB); separating the hits that share a sample gave 1.7 dB. Any later
   pass on mix loudness should look for coincident attacks with a peak position read, which is one
   script and no listening.
2. **A real hole in the loop costs more than it earns, at least on one listener.** The two changes
   the flash listener punished hardest were drums 4 to 2 and human 3 to 2, and the only structural
   change to the kit in v4 is that bar 15 now has no library pattern at all. That is one
   observation on one judge with the level work shipped alongside it, so the next pass should
   isolate it: build the same v4 twice, once with the CLM-02 pattern back in bar 15, and read both.
3. **The listeners disagree more than the changes are worth.** The same two files read 29 against
   29 on lite and 29 against 24 on flash, and v2 alone read 30 earlier today on flash and 29 now.
   One cue, two files, four reads: the spread is 5 points. A single paired read cannot order two
   renders this close, which is why this card does not claim v4 is worse, only that it is not better.
4. **The card's own floor is now a scorer artifact.** `score_table.py` takes the latest read per
   file, so it now shows v4 at 24 and calls it the floor, while the paired reads show 29 against 29.
   The table is a queue position, as `knowledge/EAR-LOOP-2026-10-24.md` section 3 already says.

Rounds run: 2 of the 4 allowed (one per listener), because the 45 minute budget was spent on the mix
search, and round 3 would have needed a third listener to break a tie between two.

## Files here

| file | what it is |
| --- | --- |
| `build_pp_fight_v4.py` | the builder: v3's notes and harmony, the crest work, the bar 15 hole, the onset stagger |
| `build_report_v4.json` | devices, kit, humanize values, seam and voice check from the build itself |
| `check_pp_fight_v4.py` | the card's checks as one table: files, lengths, seams, hook meter, kit ladder, devices, dashes |
| `check_output.txt` | that script's output, 22 rows, all PASS |
| `pp_fight_v4_{fight,calm,states}.{mid,wav,mp3}` | the three modules, 8 voices, seam 0 samples |
| `hook_report_{calm,fight}_v4.json` | 100 of 100 on both |
| `score_table_before.txt`, `score_table_after.txt` | the score table around this pass |
| `ear_with_user_env.py` | the wrapper that reads GEMINI_API_KEY from the Windows user store for `ear_critic.py` |
