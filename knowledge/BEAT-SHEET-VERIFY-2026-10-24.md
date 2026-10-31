# Beat sheet verify: the 900 seconds against the scenes and the drive

Card t_4883cf22 (BEAT-SHEET-VERIFY), research-assistant, written 2026-10-24 for Primordial Paradox.
Scope: this file only. It reads `knowledge/mechanics/PACING-AND-CUTSCENES.md` sections 7 and 9,
`knowledge/DRIVE-SHOT-LIST.md`, `data/scenes/all.json`, `data/slice.json`, `knowledge/ARRIVAL-CONTENT.md`,
`data/mechanics/pacing_recipes.json`, `data/intro_text.json` and `data/title_timing.json`. It writes no data file,
no scene, no spec and no test. No key, no login, no network.

What it answers: does the beat sheet's 900 seconds survive contact with the shot list and the scene rows, and is
the route's time real or only arithmetic?

---

## 1. The three clocks, and what each one actually counts

| Clock | Where it lives | Unit | Its own total | What it is not |
| --- | --- | --- | --- | --- |
| the beat sheet | `pacing_recipes.json` `beat_sheet` and PACING section 9 | seconds, 32 integer rows | 900 s exactly | not a measurement of any built scene |
| the drive film | `DRIVE-SHOT-LIST.md` section 2 | steps, 12 rows of 86 step bars | 10,680 steps = 178.00 s, plus 2,408 steps interlude | not the sheet's own cut: every shot re-cuts its beat |
| the scene rows | `data/scenes/all.json`, 11 rows | steps inside `wait`, `move`, `fade` | 208 steps = 3.47 s | the rest of a scene is player paced, so it carries no number |

The 900 is a budget. The 10,680 is a film. The 208 is what the scene data has actually priced. The three
disagree in specific, nameable places, and section 6 names every one with both numbers.

---

## 2. The route table: one row a route step, the three clocks side by side

The authored seconds in the fourth column are the sheet's, read through R32's own ownership map
(`tests/test_slice_route.py` `BEATS_BY_STEP` plus the encounter row's own `beat`), not invented here.

| Route step | Kind | Beats it owns | Sheet s | Content the step names | Authored there | There in s | Scene row minus sheet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| title | title | 1 to 2 | 42 | room `rm_pp_title`, no scene row | 0 | 0.00 | -42.00 |
| crawl | crawl | 3 to 6 | 30 | text `intro_text`, no scene row | 0 | 0.00 | -30.00 |
| drive | scene | 7 to 19 | 218 | scene `drive_to_southampton`, absent | 0 | 0.00 | -218.00 |
| arrival | map | 21 to 22 | 100 | map `southampton_town_quay`, no scene row | 80 (two orphan rows) | 1.33 | -98.67 |
| gate | scene | 20 | 52 | `quay_gate_checkpoint` | 0 | 0.00 | -52.00 |
| boarding | scene | 24 to 26 | 102 | `ship_boarding` | 44 | 0.73 | -101.27 |
| fight | battle | 28 | 90 | encounter `tutorial_sailors` | 90 s (its own pacing) | 90.00 | 0.00 |
| save | save | 27 | 50 | no scene, and the row names no trigger | 0 | 0.00 | -50.00 |
| gameover | branch | none, and the machine allows it | 0 | scene `title` by `to` | 0 | 0.00 | n/a |
| **total** | | **1 to 28 less 23** | **684** | **all 11 rows, not only the 9 steps** | **208** | **3.47** | **-680.53** |

The authored column counts steps for a scene row and seconds for the fight, because the encounter row authors its
own seconds and no steps. The 208 is the whole scene file, not the column's sum: 124 steps sit on the rows this
table names, and the other 84 sit on rows it does not. Of the 208, 104 steps are on rows the route can reach and
104 are not.

The total row against the sheet's own total: **the route authors 684 s of the 900, a delta of -216 s.** The 216
is not missing content, it is the five beats no route step walks, named: beat 23 the hound (48 s), beat 29 the
stairwell (42 s), beat 30 the ship leaves port (36 s), beat 31 Kronos from the deck (50 s), beat 32 the chapter
card (40 s). 684 + 216 = 900 exactly.

Three things fall out of this table and none of them is a rounding:

1. The route's order is not the sheet's order in two places. The route walks `arrival` (beats 21 and 22) before
   `gate` (beat 20), and it walks `save` (beat 27) after `fight` (beat 28) where the sheet saves before the hold
   fight. R32 prints both inversions and does not rule on them; this file does not rule on them either.
2. The fight row is the only step whose content authors exactly what the sheet says: 90 s, from
   `data/encounters/all.json` `tutorial_sailors.pacing` (27 s fixed plus 3 turns at 21 s). It is also beat 28,
   while the sheet's first fight is beat 23.
3. The scene data does not contradict the 684. It simply does not price it: 3.47 s is all the authored step time
   there is in all eleven rows, including the six rows no route step reaches.

---

## 3. The 900 itself, checked and sound

- 32 beats, and the 32 `seconds` values sum to 900 exactly. All 32 `running_total` values recompute from the
  durations with 0 mismatches.
- The markdown copy (PACING section 9) and the machine copy (`pacing_recipes.json` `beat_sheet`) agree row for
  row: 32 rows, 0 disagreements in beat number, kind, seconds or clock. One is safe to quote against the other.
- The kind shares in section 9 recompute: cutscene and dialogue 465 s (51.7 percent), walk 180 s (20.0),
  battle 138 s (15.3), save 50 s (5.6), title 32 s (3.6), crawl 25 s (2.8), menu 10 s (1.1), and walk plus
  battle 318 s (35.3). Sum 900.
- The five gates are on the seconds the sheet claims: first input 150 s, full control 342 s, first fight 442 s,
  first save 592 s, and every one of them is a beat boundary in the data, not a rounded statement.
- `pytest tests/test_beat_sheet.py -q` gives 35 passed, and `pytest tests/test_slice_route.py -q -k "sheet or
  authored or seconds or block"` gives 3 passed. The route's authorship of 684 s is green today.

So the 900 is sound as arithmetic and as a budget. It is not sound as a measurement, and section 6 is where.

---

## 4. The drive: 10,680 steps against beats 7 to 19

Both totals agree. No individual shot does.

| Shot | Beats | Sheet s for those beats | Steps | Shot s | Delta |
| --- | --- | --- | --- | --- | --- |
| 1 | 7 | 10 | 688 | 11.47 | +1.47 |
| 2 | 8 | 12 | 860 | 14.33 | +2.33 |
| 3 | 9 | 8 | 602 | 10.03 | +2.03 |
| 4 | 10 | 12 | 774 | 12.90 | +0.90 |
| 5 and 6 | 11 | 36 | 1,032 + 1,118 | 35.83 | -0.17 |
| 7 | 13 | 12 | 860 | 14.33 | +2.33 |
| 8 | 14 | 14 | 860 | 14.33 | +0.33 |
| 9 | 15 | 24 | 1,118 | 18.63 | -5.37 |
| 10 | 16 and 17 | 24 | 1,118 | 18.63 | -5.37 |
| 11 | 18 | 8 | 688 | 11.47 | +3.47 |
| 12 | 19 | 18 | 962 | 16.03 | -1.97 |
| **total** | **7 to 19** | **218** | **10,680** | **178.00** | **0.00** |

Read the total honestly: the block matches because the twelve deltas are exact and sum to 0.00 s. Read the rows
honestly: all twelve shots disagree with the beat they re-cut, the widest single move is 5.37 s, and the sheet is
not repairable shot by shot without either re-cutting the film on the sheet's seconds or restating beats 7 to 19
on the bar grid.

Add the interlude and the block is 10,680 + 2,408 = 13,088 steps = 218.13 s against the sheet's 218 s, a
difference of 0.13 s. That 0.13 s is the declared quantisation of beat 12 from 40.00 s to 28 bars.

Other numbers in the shot list that recompute: shortest shot 10.03 s (shot 3), longest 18.63 s (shots 6, 9, 10),
median 14.33 s, mean 14.83 s (178.00 / 12), all twelve between 8 and 20 s, eleven hard cuts each on a multiple of
86, eight distinct locations over 178 s.

---

## 5. Every scene row, its authored steps and its unpriced commands

Authored step time is counted from the commands that carry a duration: `wait` pays its own `steps`, `move` pays
8 steps a tile (`PP_WALK_STEPS_RAIL` in `game/scripts/pp_config/pp_config.gml`), `fade` pays 12 steps when the
argument is omitted (spec 06). `say`, `battle`, `branch`, `setflag`, `music` and `end` pay nothing authored.

| Scene row | Commands | Authored steps | There in s | No authored time | Reached from |
| --- | --- | --- | --- | --- | --- |
| `ship_boarding` | 6 | 44 | 0.73 | music, say, setflag, end | route step boarding |
| `percy_lore_stop` | 3 | 0 | 0.00 | say, battle, end | nothing |
| `prometheus_interrupt` | 8 | 24 | 0.40 | two says, two setflags, music, end | nothing |
| `percy_aftermath` | 3 | 0 | 0.00 | branch, say, end | nothing |
| `percy_aftermath_kill` | 2 | 0 | 0.00 | say, end | `percy_aftermath` only, itself unreachable |
| `quay_gate_checkpoint` | 7 | 0 | 0.00 | music, two says, three branches, end | route step gate |
| `quay_gate_truth` | 2 | 20 | 0.33 | end | branch from the gate |
| `quay_gate_bluff` | 2 | 20 | 0.33 | end | branch from the gate |
| `quay_gate_authority` | 2 | 20 | 0.33 | end | branch from the gate |
| `quay_yard_walk` | 5 | 80 | 1.33 | end | nothing, though it is sheet beat 21 |
| `quay_dock_office_play` | 3 | 0 | 0.00 | two says, end | nothing, though it is sheet beat 22 |
| **total, 11 rows** | | **208** | **3.47** | | **104 steps reachable from the route** |

The number that matters is the last one: the rows the route can actually reach author 104 steps, 1.73 s, of the
route's 684 s. Six of the eleven rows are unreachable from `data/slice.json` as it stands.

---

## 6. Every place the sources disagree, both numbers named

No average is used anywhere below.

- `D1` **shot against beat, twelve times.** Section 4 has the table. The widest three: beat 15 is 24 s and shot 9
  is 18.63 s, -5.37 s; beats 16 and 17 are 24 s together and shot 10 is 18.63 s, -5.37 s; beat 18 is 8 s and
  shot 11 is 11.47 s, +3.47 s. The twelve exact deltas sum to 0.00 s, and the twelve two decimal deltas sum to
  -0.02 s because the printed seconds sum to 177.98 while the steps give 178.00.
- `D2` **the bar is 86 steps in the shot list and 87 in the title machine.** `DRIVE-SHOT-LIST.md` section 1 says
  86 and cites `data/title_timing.json` `bar_steps`; that key is 87 (`steps_per_bar` 85.714, `bar_steps` 87,
  `beat_steps` 29). Same cut, both numbers: the first cut at film bar 8 is 688 steps on the 86 grid and 696 on the
  87 grid; the cut out of shot 11 at bar 113 is 9,718 against 9,831; the 28 bar interlude is 2,408 against
  2,436. `data/title_timing.json` `lightning` is built on its own grid too, 8 bars and 696 steps.
- `D3` **the interlude is 40 s on the sheet and 40.13 s (2,408 steps) in the shot list.** The wall total is
  218 s against 218.13 s (13,088 steps). This is declared in the shot list as a deliberate quantisation and it is
  the only place the two clocks differ in total.
- `D4` **the first input is at 150 s on the sheet and 156.57 s in the film.** Beat 12 begins at sheet second 150.
  In the film, shot 6 ends at step 5,074 (84.57 s) and the interlude begins there, and the film's step 0 sits at
  sheet second 72 where beat 7 begins, so control arrives at 72 + 84.57 = 156.57 s. Against the gate "the player
  touches a control by 2 min 30 s" the sheet passes with 0.00 s of headroom and the shot list misses by 6.57 s.
- `D5` **the first fight is 48 s at beat 23 and 90 s at beat 28.** The sheet's first fight is the hound, beat 23,
  48 s. The route's one fight step names encounter `tutorial_sailors`, whose row carries `beat` 28 and
  `pacing.seconds` 90. Beat 23 is owned by no route step, so the route's first fight costs 90 s where the sheet
  budgets 48 s, +42 s.
- `D6` **the crawl is 25 s on the sheet and 24.53 s in the text file.** Beats 4 to 6 are 8 + 9 + 8 = 25 s.
  `data/intro_text.json` carries six beats and a rate of 18 characters a second with a 1.2 s pause a beat, which
  computes to 24.53 s. Row by row the sheet's pairs are 8, 9 and 8 s against 8.57, 10.51 and 5.46 s, so the third
  pair carries 2.54 s of the sheet's "and hold" as slack.
- `D7` **the first interior is 370 s in section 9 and 442 s in the recipes' checks block.**
  `pacing_recipes.json` `checks.first_interior_seconds` is 442, and 442 s is the second beat 22 ends, which is
  also the second the first fight begins. PACING section 9 puts the first interior at 370 s, which is 6:10, the
  start of the dock office. Two numbers for one gate, and 442 s would fail the "inside 10 minutes" reading if the
  office were the first interior.
- `D8` **a walk tile is 8 steps in the code and 12 steps in the arrival prose.** `PP_WALK_STEPS_RAIL` is 8, so a
  `move` of 3 tiles is 24 steps. `ARRIVAL-CONTENT.md` section 2 says walking speed is 5 tiles a second, which at
  60 steps a second is 12 steps a tile, so the same 3 tiles would be 36 steps. Every move in section 5 is counted
  at 8; the prose would add 50 percent to all of them.
- `D9` **the compression ratio is 26.97 to 1 at 80 minutes.** PACING section 7 says "about 80 minutes of story
  time" and then "roughly 28 to 1". At 178 s, 80 minutes is 26.97 to 1; the section's own quoted 1 h 23 min gives
  27.98 to 1. The 28 is defensible from the 1 h 23 min figure and not from the 80 minutes printed beside it.
- `D10` **the shot list's printed seconds add to 177.98, its steps to 178.00.** Declared in its own section 8 and
  not a hidden error; it is the only rounding in the drive.

Not a disagreement, recorded because it was checked: the 2 frame lightning flash in beat 16 and the sheet's
"2 frame palette flash" agree, and `title_timing.json` `lightning.flash_steps` is 2. The one place the flash has
no command is the drive list's `Q1`, which this file does not reopen.

---

## 7. Every step whose time is missing

Missing means no authored seconds exist anywhere for that content, or the content the step names does not exist.

1. **`drive`.** The scene row `drive_to_southampton` is absent: `grep -c` over `data/scenes/all.json` returns 0,
   and R32 fails it twice today. The room `rm_pp_drive` does exist in `game/rooms`, so the drive has a room and no
   scene. Its 218 s exists on the sheet and in the shot list, and in no scene data. The
   shot list also says beat 12 "owns its own map and its own scene", so this step needs two rows, a film and an
   interlude, and has neither.
2. **`save`.** The sheet authors 50 s, but the route row names no trigger, and R32 fails it twice today
   (`step save: the row names no trigger`). No scene row and no trigger means the 50 s is a budget with no
   object.
3. **`arrival`.** The step is a map step, so no scene row is named, and the two rows that carry its content,
   `quay_yard_walk` (80 steps) and `quay_dock_office_play` (0 steps), are reached by no step at all. 98.67 s of
   its 100 s is unpriced even though its rows exist.
4. **`title` and `crawl`.** Both are correct for their kinds, which name a room and a text file rather than a
   scene, so no scene row is expected. Neither carries authored steps: the title's 42 s is a budget, and the
   attract loops until START, so it has no authored end; the crawl's 25 s is a budget against the text file's
   computed 24.53 s.
5. **Five of the eleven scene rows author 0 steps:** `percy_lore_stop`, `percy_aftermath`,
   `percy_aftermath_kill`, `quay_gate_checkpoint`, `quay_dock_office_play`. The gate is the one that matters,
   because it is 52 s of the sheet and the demo's S4.
6. **Six of the eleven scene rows are unreachable from the route:** `percy_lore_stop`, `prometheus_interrupt`,
   `percy_aftermath`, `percy_aftermath_kill`, `quay_yard_walk`, `quay_dock_office_play`.

---

## 8. The verdict

**VERDICT: the three minute demo fits its clock and not its data. The script authors 180.00 s (10,800 steps) and
the scene rows the route can reach author 104 steps (1.73 s) of that, so every remaining second is a player paced
`say` or a `battle`, and the one shot that does have a hard number, S3, names a scene row that does not exist.**

The supporting numbers, so the verdict is not a mood:

- The sheet's own first three minutes end 30 s inside beat 12 (beat 11 closes at 150 s, beat 12 runs to 190 s), so
  the sheet's third minute is the first input, not a cutscene.
- The drive film alone is 178.00 s, which sits inside 180 s with 2.00 s spare. With its interlude it is 218.13 s,
  which does not fit, so the demo is right to take one drive shot (S3, 602 steps) rather than the block.
- The demo's six shots name seven targets, and six of the seven resolve: room `rm_pp_title`, text `intro_text`,
  map `southampton_town_quay`, scene `quay_gate_checkpoint`, scene `ship_boarding` and encounter
  `tutorial_sailors`; the seventh, scene `drive_to_southampton`, does not. Of the six that resolve, only
  `ship_boarding` and the gate's three reply rows carry authored steps.
- If the drive row stays missing, the demo falls back to the intro's own 240 step drive and runs 173.97 s, which
  still fits three minutes but no longer shows the M3.

The 900 does not fail. It is 900 exactly, twice over, and 684 s of it is walked by the route. What fails is the
claim that any of it is measured: the scene rows author 3.47 s in total, 1.73 s of it on rows the route can reach,
and the drive's 178.00 s has no row to live in.

---

## 9. Q: for gamedev

Per the gamedev specs rule these are not decided here. Each is a conflict between two numbers this file verified.

- `Q1` **Bar 86 or bar 87?** The drive snaps every cut to 86 steps and cites `title_timing.json` `bar_steps`,
  which is 87. Pick one and say which file owns it, because the first cut is 688 or 696 steps depending on the
  answer, and the interlude is 2,408 or 2,436.
- `Q2` **Is the first input 150 s or 156.57 s?** The sheet's beat 12 begins at 150 s and the film reaches the
  interlude at 156.57 s on the sheet's clock. If 156.57 s is the real number, the sheet's gate has to say so and
  beat 11 or one of the shots before it has to give up 6.57 s.
- `Q3` **Is the first fight beat 23 or beat 28?** The sheet budgets the hound at 48 s and the route's only fight
  is the 90 s sailors' fight. As it stands the route's first fight is 42 s over the sheet and the sheet's first
  fight is a fight nobody walks.
- `Q4` **Is the first interior 370 s or 442 s?** Section 9 says 370 s and `pacing_recipes.json` `checks` says
  442, which is the second the dock office closes.
- `Q5` **Which speed converts a `move` to seconds, 8 steps a tile or 5 tiles a second?** The code says 8,
  `ARRIVAL-CONTENT.md` says 5 tiles a second (12 steps a tile). Every authored walk length in section 5 is 50
  percent short if the prose is right.

---

## 10. The proof lines (P:)

P: 32 beats in `data/mechanics/pacing_recipes.json` `beat_sheet`, seconds sum 900, all 32 running totals recompute, 0 mismatches.
P: the 32 rows in PACING section 9 match the json row for row, 0 disagreements in number, kind, seconds or clock.
P: the 12 rows in `DRIVE-SHOT-LIST.md` section 2 sum to 10,680 steps = 178.00 s, and the eleven hard cuts are all multiples of 86.
P: beats 7 to 19 sum to 218 s; 10,680 + 2,408 = 13,088 steps = 218.13 s, so the drive agrees on the total and differs by 0.13 s with the interlude.
P: beats 7 to 19 against the twelve shots: twelve deltas from -5.37 s to +3.47 s, exact sum 0.00 s.
P: `data/scenes/all.json` has 11 rows, 208 authored steps = 3.47 s in total, 5 rows with 0, and 6 rows no route step reaches.
P: `data/slice.json` walks 9 steps, 8 of them with beats; they own 684 s; beats 23 and 29 to 32 are 216 s; 684 + 216 = 900.
P: `grep -c drive_to_southampton data/scenes/all.json` returns 0.
P: `pytest tests/test_beat_sheet.py -q` gives 35 passed; `pytest tests/test_slice_route.py -q -k "sheet or authored or seconds or block"` gives 3 passed; the whole R32 file gives 4 failed and 20 passed, and the 4 are drive twice and save twice.
