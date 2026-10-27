# Music cue ledger, 2026-10-26

Card t_10cad8d9 (MUSIC-CUE-LEDGER, HACK-FEED), musician. Node CitadelArana, the desktop. Measured 2026-10-26
between 23:00 and 23:40 UTC (16:00 to 16:40 PDT).

What this file answers in one table: for every cue id the game knows, which file `data/audio.json` names, whether
that file exists, how long it is, which file is actually the newest take for that cue, the digest of both, the
licence and author line under which it ships, and whether the name and the newest take agree. Then it names the
rows that disagree, in the order the demo reaches them.

It reports drift. It does not decide any of it. `data/audio.json` is read and never written by this card, no cue was
recut or re-rendered, and the rulings that own each disagreement are named where they exist
(`knowledge/GAMEDEV-DECISIONS-2026-10-26.md` D1, D3, D4, and card t_279ef225).

Every path in this file is relative to `assets/audio/` unless it names another file. Durations are ffprobe on the
file in front of it. Digests are sha256 of the file bytes.

## The one rule this table uses

**Newest** means the latest modification time among the `.ogg` files that belong to the cue's own folder family,
because `.ogg` is the only form the music bus plays (`game/scripts/pp_audio/pp_audio.gml` line 41,
`PP_AUDIO_MUSIC_DIR "music/"`). The family of each cue is written out in section 9 so a reader can re-run the
comparison instead of trusting it. Files in `assets/audio/sfx/` are effects, not cues, and are excluded by the same
rule `data/audio.json` states: effects are not music and must not reach the cue table.

## 1. The ledger, one row per cue

17 rows: the 6 cues with a delivered file and the 11 pending rows, all of them from `data/audio.json`.

| cue | asset | the file `data/audio.json` names | exists | dur s | the newest file for this cue | dur s | newest mtime | DRIFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-01 | `pp_01_title` | `pp_01_title/pp_01_title.ogg` | yes | 74.266803 | `pp_01_title_v9/pp_01_title_v9.ogg` | 74.285646 | 2026-10-26 12:30 | DRIFT |
| PP-02 | `pp_drive_master1` | `pp_drive_master1/pp_drive_master1.ogg` | yes | 178.563333 | `pp_drive_master1/pp_drive_master1.ogg` | 178.563333 | 2026-10-26 11:44 | OK |
| PP-03 | `pp_03_harbor_master1` | `pp_03_harbor_master1/pp_03_harbor_master1.ogg` | yes | 225.882358 | `pp_03_harbor_master1/pp_03_harbor_master1.ogg` | 225.882358 | 2026-10-26 11:45 | OK |
| PP-04 | `pp_04_navy_sailors_master1` | `pp_04_navy_sailors_master1/pp_04_navy_sailors_master1.ogg` | yes | 43.636349 | `pp_04_navy_sailors_master1/pp_04_navy_sailors_master1.ogg` | 43.636349 | 2026-10-26 11:43 | OK |
| PP-05 | `pp_05_small_ship` | `pp_05_small_ship/pp_05_small_ship.ogg` | yes | 60.000000 | `pp_05_small_ship_v5/pp_05_small_ship_v5.ogg` | 60.000000 | 2026-10-25 00:25 | DRIFT |
| PP-06 | `percy_theme` | `percy_theme/percy_theme.ogg` | yes | 43.636327 | `percy_theme_v4/percy_theme_v4.ogg` | 43.636327 | 2026-10-26 06:40 | DRIFT |
| PP-07 | `pp_07_prometheus_explains` | none, `delivered_file` is null | no | n/a | none, no folder | n/a | n/a | PENDING |
| PP-08 | `pp_08_dead_rising` | none, `delivered_file` is null | no | n/a | none, no folder | n/a | n/a | PENDING |
| PP-09 | `pp_09_data_center` | none, `delivered_file` is null | no | n/a | none, no folder | n/a | n/a | PENDING |
| PP-10 | `pp_10_hector` | none, `delivered_file` is null | no | n/a | none, no folder | n/a | n/a | PENDING |
| PP-11 | `pp_11_rush_to_prison` | none, `delivered_file` is null | no | n/a | none, no folder | n/a | n/a | PENDING |
| PP-12 | `pp_12_one_north_quay` | none, `delivered_file` is null | no | n/a | none, no folder | n/a | n/a | PENDING |
| PP-13 | `pp_13_titan_employees` | none, `delivered_file` is null | no | n/a | none, no folder | n/a | n/a | PENDING |
| PP-14 | `pp_14_kronos` | none, `delivered_file` is null | no | n/a | none, no folder | n/a | n/a | PENDING |
| PP-15a | `pp_15a_entropy` | none, `delivered_file` is null | no | n/a | none, no folder | n/a | n/a | PENDING |
| PP-15b | `pp_15b_mercy` | none, `delivered_file` is null | no | n/a | none, no folder | n/a | n/a | PENDING |
| PP-16 | `pp_16_ouranos` | none, `delivered_file` is null | no | n/a | none, no folder | n/a | n/a | PENDING |

Counts: **3 DRIFT, 3 OK, 11 PENDING.** For the 11 pending rows the game plays their `fallback` instead, and every
fallback resolves to a delivered row: PP-07 to PP-05, PP-08, PP-09, PP-12 and PP-13 to PP-03, PP-10 and PP-14 to
PP-06, PP-11 to PP-02, PP-15a, PP-15b and PP-16 to PP-01.

A pending row is not a drift. It says so in its own `pending_reason`, and there is no file for the newest column to
beat.

One caveat that changes the count without changing a single cue: this table reads the **working tree**, and
`data/audio.json` is uncommitted at the moment of measuring. `git diff` shows HEAD naming `pp_drive_v2`,
`pp_03_harbor` and `pp_04_navy_sailors` (v1 for all three) with the three master re-points only in the working tree.
Read against HEAD instead of the tree, all six delivered rows would be DRIFT instead of three. Whoever commits the
W5 re-point moves this number to 3 without touching a cue, and whoever checks out HEAD today sees 6. The command and
its output are in section 9.

## 2. Digest and credit per cue

The licence and author line is the same for every row, because every cue is the holder's own work: `CREDITS.md`
section 2, the row "Music, sound effects, art, sprites, tiles, palettes, code, dialogue, data tables", holder line
verbatim:

    Copyright (c) 2026 Nayil Arana. All rights reserved.

It is reproduced in every row rather than stated once, so a reader who copies one row takes the line with it. The
outbound licence is `LICENCE`, which today records all rights reserved; no cue carries a third party obligation, and
`CREDITS.md` section 2 says so explicitly ("There is no audio sample pack, no soundbank, no commercial chip
instrument"): the music is rendered by this project's own tools from its own recipes.

| cue | sha256 of the named file | sha256 of the newest file | licence and author line |
| --- | --- | --- | --- |
| PP-01 | `e50e264dd076b9f743e9c71960460ab3be6a245e36c61bb8ee76293162b01574` | `f597b118c48fee6ea375b7e8e144d066a03a72eb9ea9e9fa699e43bae7a52137` | Copyright (c) 2026 Nayil Arana. All rights reserved. |
| PP-02 | `ef333b87f4850b37501408b7a06a26e6e4fd37607d03b3c62fae5a5972f78aaf` | `ef333b87f4850b37501408b7a06a26e6e4fd37607d03b3c62fae5a5972f78aaf` | Copyright (c) 2026 Nayil Arana. All rights reserved. |
| PP-03 | `d824298aefaa68d3d548c25c5c8d3ba38ecd383b324a949060e513c602b3e890` | `d824298aefaa68d3d548c25c5c8d3ba38ecd383b324a949060e513c602b3e890` | Copyright (c) 2026 Nayil Arana. All rights reserved. |
| PP-04 | `e600a607cbfc4464f57eda926e388744731ea2bd72cbe4efb447b9bb03a2a369` | `e600a607cbfc4464f57eda926e388744731ea2bd72cbe4efb447b9bb03a2a369` | Copyright (c) 2026 Nayil Arana. All rights reserved. |
| PP-05 | `9d82a847c80a970eb0b1668afcc98b33e2e36eeec2b2cb5d0a657a99048d3472` | `7e58c129b4de3a9973113f66c06f5ea9642b6ff6a3e3e4fbebe7ac2cae67932f` | Copyright (c) 2026 Nayil Arana. All rights reserved. |
| PP-06 | `2a8f3a5af8516c06b4f20649cdf606ef98ecb636fc2a879068bf059502669c9a` | `a7452b74d8e8062073a396010671e5083e98bdb50d4807c2089b3cb1e6110285` | Copyright (c) 2026 Nayil Arana. All rights reserved. |
| PP-07 | none, no file | none, no file | Copyright (c) 2026 Nayil Arana. All rights reserved. |
| PP-08 | none, no file | none, no file | Copyright (c) 2026 Nayil Arana. All rights reserved. |
| PP-09 | none, no file | none, no file | Copyright (c) 2026 Nayil Arana. All rights reserved. |
| PP-10 | none, no file | none, no file | Copyright (c) 2026 Nayil Arana. All rights reserved. |
| PP-11 | none, no file | none, no file | Copyright (c) 2026 Nayil Arana. All rights reserved. |
| PP-12 | none, no file | none, no file | Copyright (c) 2026 Nayil Arana. All rights reserved. |
| PP-13 | none, no file | none, no file | Copyright (c) 2026 Nayil Arana. All rights reserved. |
| PP-14 | none, no file | none, no file | Copyright (c) 2026 Nayil Arana. All rights reserved. |
| PP-15a | none, no file | none, no file | Copyright (c) 2026 Nayil Arana. All rights reserved. |
| PP-15b | none, no file | none, no file | Copyright (c) 2026 Nayil Arana. All rights reserved. |
| PP-16 | none, no file | none, no file | Copyright (c) 2026 Nayil Arana. All rights reserved. |

One fact found while digesting, and it is why PP-01's DRIFT row is worth reading twice: `pp_01_title/pp_01_title.ogg`
is byte for byte the same file as `title_theme_v5/title_theme_v5.ogg`, sha256
`e50e264dd076...62b01574` in both, and the same is true of `pp_01_title/pp_01_title_alt_v4_medium.ogg` against
`title_theme_v4/title_theme_v4_medium.ogg` (`d9e588fd99fb...`). The `pp_01_title` folder is not a new title render,
it is the R36 re-point of the v5 take under the row's own asset name. The row therefore names the v5 music, four
generations behind v9.

## 3. The cues whose named file is not the newest, in the order the demo reaches them

The order is `data/slice.json`'s route, nine steps: title, crawl, drive, arrival, gate, boarding, fight, save,
gameover. The cue each step asks for comes from `data/scenes/all.json`'s `music` commands and
`data/encounters/all.json`'s `music` field, not from a habit:

| step | scene or encounter | what the data asks for | DRIFT |
| --- | --- | --- | --- |
| 1 title | room `rm_pp_title`: `pp_audio_play("title_theme")` at `game/scripts/pp_title/pp_title.gml` line 276 | no cue id at all; see section 7, the theme path plays `title_theme_v3_126.ogg` | DRIFT (of the PP-01 row, not of an ask) |
| 2 crawl | `intro_text`, no music command; the crawl ducks the theme (`pp_audio_duck_db`) | none | n/a |
| 3 drive | scene `drive_to_southampton`, `music PP-02` | PP-02 | OK |
| 4 arrival | map step, no music command, PP-02 carries on | PP-02 | OK |
| 5 gate | scene `quay_gate_checkpoint`, `music PP-03` | PP-03 | OK |
| 6 boarding | scene `ship_boarding`, `music PP-05` | PP-05 | DRIFT |
| 7 fight | encounter `tutorial_sailors`, `music PP-04` | PP-04 | OK |
| 8 save | save step, no music command | none | n/a |
| 9 gameover | branch back to the title | none | n/a |

PP-01 is in this list first because it is the cue a judge hears first in the demo's stand-in bed, not because a
scene asks for it: no `music` command anywhere in `data/scenes/all.json` names PP-01, and the title room asks the
effects path for the name `title_theme` instead (section 7). PP-06 is in the list third for the same kind of reason,
because the route does not reach its scene at all.

So the rows a judge meets, in the order they meet them:

1. **PP-01, the title.** Three files, three different answers, and this is the worst row in the table. The row names
   `pp_01_title/pp_01_title.ogg` (v5's bytes). `pp_01_title_v9.ogg` is the newest take, and it landed at 12:30 UTC
   today, after `GAMEDEV-DECISIONS-2026-10-26` D4 wrote its acceptance rule at 07:15. And the code that actually
   starts the title music does not read the row at all: it streams `streams/title_theme_v3_126.ogg`, a take from
   2026-10-21 (section 7). D4's rule stands and is not overturned here: the accepted theme is whatever the row names.
   What changed is that D4 named v8 as the strongest candidate on the lane's numbers, v9 exists now, and neither of
   them is what the build plays. Row edits are the only thing that can move any of it, and they are not this card's.
2. **PP-05, the ship.** The row names `pp_05_small_ship/pp_05_small_ship.ogg` (96 bpm, 24 bars). `_v2` to `_v5`
   sit beside it, and v5 is a different cut: 32 bars at 128 bpm, still exactly 60.000 s, with the freed 15 s filled
   by a new section (`pp_05_small_ship_v5/NOTES.md` lines 45 to 46). `knowledge/FINAL-MIX-2026-10-26.md` section 6
   already hands this forward as its own card rather than guessing, because "which take ships is a gamedev
   decision".

And the third drifted row, which the slice route does not reach:

3. **PP-06, Percy.** The row names `percy_theme/percy_theme.ogg`; `percy_theme_v4.ogg` is the newest take, and
   `_v2` and `_v3` sit between them. D4 rules the pair v3/v4 and says in as many words that "candidates do not
   become the boss theme until `PP-06` names them". The cue is reached by scene `percy_lore_stop` (its `battle`
   command resolves to `data/encounters/all.json` `percy`, `music: PP-06`), which is row 2 of the scene file and is
   not a step of `data/slice.json`'s route. So a judge does not meet it in the three minute demo, and the drift
   stays invisible for exactly that reason.

## 4. Three rows where the named file is the newest and is still not the newest music

These are OK in the DRIFT column above, because the rule is a file comparison, and they are the reason the rule
needs one sentence of care. All three named files are masters built today from an older render, and a newer
composition exists beside the source:

| cue | the master the row names | the source the master was built from | the newer composition that exists | dur s of the newer composition |
| --- | --- | --- | --- | --- |
| PP-02 | `pp_drive_master1/pp_drive_master1.ogg` 178.563333 | `pp_drive_v2/pp_drive_v2.ogg` | `pp_drive_v4/pp_drive_v4.ogg` | 178.550431 |
| PP-03 | `pp_03_harbor_master1/pp_03_harbor_master1.ogg` 225.882358 | `pp_03_harbor/pp_03_harbor.ogg` | `pp_03_harbor_v4/pp_03_harbor_v4b.ogg` | 112.941179, exactly half the master's length |
| PP-04 | `pp_04_navy_sailors_master1/pp_04_navy_sailors_master1.ogg` 43.636349 | `pp_04_navy_sailors/pp_04_navy_sailors.ogg` | `pp_04_navy_sailors_v3/pp_04_navy_sailors_v3.ogg` | 43.583107 |

The source column is `knowledge/FINAL-MIX-2026-10-26.md` section 1's own "Source before" column, and the masters
themselves are card t_120dc9f2's (W5 SCORE-FINAL), which re-pointed three rows today at 11:43 to 11:45. Nothing here
says that was wrong: a gain pass on the shipped take is a delivery step, not a cue change, and the mix page says the
music is unchanged. What the ledger adds is that after a mastering pass, "newest by timestamp" and "newest music" are
two different questions, and only the row owner can answer the second.

## 5. Files on disk that no cue row names

Twelve `.ogg` files in `assets/audio/` belong to a cue-sized folder that no row of `data/audio.json` names. They are
not counted in the drift column above, because the column compares a named file against its own family, and these
have no row to compare against. They are listed because a reader asking "which file does the game play for each cue"
will otherwise find them and wonder.

| file | dur s | mtime | what rules it, if anything |
| --- | --- | --- | --- |
| `pp_boarding_master1/pp_boarding_master1.ogg` | 32.000000 | 2026-10-26 11:45 | PP-17. `GAMEDEV-DECISIONS-2026-10-26` D1 rules the cue, the row is not landed, and the master's own `.md` says the row should name this file and not `pp_boarding.ogg`. Newest boarding take on disk. |
| `pp_boarding_v2/pp_boarding_v2_humanized.ogg` | 32.000000 | 2026-10-24 16:22 | candidate, superseded by the master |
| `pp_boarding_v2/pp_boarding_v2.ogg` | 32.000000 | 2026-10-24 16:19 | candidate |
| `pp_boarding/pp_boarding.ogg` | 32.000000 | 2026-10-23 02:22 | the take D1 measures, not the one D1 wants wired |
| `pp_fight_v2/pp_fight_v2_states.ogg` | 45.684558 | 2026-10-24 08:25 | `pp_fight` family, ruled not wired by D3 |
| `pp_fight_v2/pp_fight_v2_calm.ogg` | 22.857143 | 2026-10-24 08:25 | as above, the calm state |
| `pp_fight_v2/pp_fight_v2_fight.ogg` | 22.857143 | 2026-10-24 08:25 | as above, the fight state |
| `pp_arrival_v2/pp_arrival_v2.ogg` | 96.000000 | 2026-10-24 04:14 | no ruling, no row, no scene command |
| `pp_fight/pp_fight_states.ogg` | 45.684558 | 2026-10-23 01:13 | as above, older generation |
| `pp_fight/pp_fight_calm.ogg` | 22.857143 | 2026-10-23 01:13 | as above |
| `pp_fight/pp_fight_fight.ogg` | 22.857143 | 2026-10-23 01:13 | as above |
| `pp_arrival/pp_arrival.ogg` | 144.000000 | 2026-10-23 01:00 | no ruling, no row, no scene command |

Three notes that keep this list honest:

- `pp_fight_v6` exists (built today, 13:16 UTC, per D3) and carries no `.ogg` at all, only `.mp3` and `.wav`, so the
  newest **playable** fight-state take is still v2. The card's RB-17 premise, "pp_fight_v2 landed and PP-04 still
  names v1", is now two rulings out of date: PP-04 names `pp_04_navy_sailors_master1` as of 11:43 today, and D3
  ruled pp_fight_v2 not wired at 07:15.
- `hadrian_theme/` and `baroque_demo/` are cue-sized folders with no `.ogg` and no row: `hadrian_theme` is a
  character theme from 2026-10-22 (92 bpm, 7.36 MB of wav) that no scene, encounter or data file names, and
  `baroque_demo` is the baroque engine's own research demo (`knowledge/BAROQUE-ENGINE-RESEARCH.md`).
- `render2_demo/` holds one `.mid` and no audio. It is a render test, not a cue.

## 6. The cue id is not one id space, and that is its own drift

The card asks for one table because the mapping from cue id to file drifts. It drifts in the data, and it also drifts
in the prose. The two newest ear pages in `knowledge/` (`EAR-LOOP-2026-10-24.md` and `GEMINI-EAR-SLICE-2026-10-24.md`) use a
second numbering for the same four files:

| cue id | `data/audio.json` says (row title, asset) | `knowledge/EAR-LOOP-2026-10-24.md` section 2 says | `knowledge/GEMINI-EAR-SLICE-2026-10-24.md` section 1 says |
| --- | --- | --- | --- |
| PP-02 | The Drive, `pp_drive_master1` | drive, `pp_drive/pp_drive_v3_humanized.mp3` | drive, the same file |
| PP-03 | Harbor, `pp_03_harbor_master1` | **arrival, night quay**, `pp_arrival/pp_arrival.mp3` | the same |
| PP-04 | Navy Sailors, `pp_04_navy_sailors_master1` | **fight**, `pp_fight/pp_fight_states.mp3` | the same |
| PP-06 | Percy, Tyrant of the Harbor, `percy_theme` | **boarding**, `pp_boarding/pp_boarding.mp3` | the same |

Three of those four rows attach a score to an id whose row names a different file. The scores themselves are not
wrong measurements of the files they name: the file column on both pages is explicit and matches. What is wrong is
the id in front of it, and a reader who carries "PP-03 is 31 of 60" into the harbor row would be scoring a different
cue. The fix is a naming decision on those pages, which is a musician card of its own, not a row edit here.

## 7. Which file the build actually plays, and why every other cue is silent

The table in section 1 says which file each row names. It does not say the game can play it, and the answer differs
by cue, so it gets its own section.

**The title plays a file no row names.** `game/scripts/pp_title/pp_title.gml` line 276 calls
`pp_audio_play("title_theme")`, and `pp_audio_play` sends that name to `pp_audio_play_theme`
(`game/scripts/pp_audio/pp_audio.gml` line 471). That function tries four hardcoded paths in order
(`pp_audio_theme_streams`, lines 368 to 371):

    streams/title_theme_v3_126.ogg
    streams/title_theme_v3.ogg
    streams/title_theme_v2.ogg
    streams/title_theme.ogg

The first one exists in the build, so the music a player hears on the title screen is
`game/datafiles/streams/title_theme_v3_126.ogg`, a 2026-10-21 take: 74.285646 s by ffprobe, sha256
`dedfda8291265fcdca4b54a58978fda58534c0481e184ad7c24829da1356b749`, byte for byte
`assets/audio/title_theme_v3/title_theme_v3_126.ogg`. It is not `pp_01_title.ogg`, not v9, and not anything the PP-01
row names. The candidate list predates the row's asset name and nothing ties the two together, so a row edit alone
will not change what the title plays.

**Every other cue is silent, whatever its row names.** `pp_audio_music` (the cue bus the scene `music` command
calls, `game/scripts/pp_scene/pp_scene.gml` line 276) asks for `music/<asset>.ogg` and `datafiles/music/<asset>.ogg`
(`pp_audio.gml` lines 41 and 144 to 145). The tree has no `game/datafiles/music/` directory at all, and the delivered
OGGs are mirrored into `game/datafiles/streams/`, which the cue bus never reads.

So in the build as it stands: PP-01's row is not consulted, the theme path plays v3_126, and PP-02 to PP-06 cannot
play even though their rows name files that exist. That is divergence 1 of `knowledge/DEMO-BED-2026-10-26.md`
section 1, unchanged since it was written, and it is repeated here because a cue ledger that implies playable audio
would be the same quiet drift this card exists to stop. Both fixes are the audio bus card's, not this one's: the
theme candidate list and the `music/` mirror are code and sync decisions.

## 8. Tempo: what the beat sheet says, and what each shipped take says

The card asks for tempo "if a beat sheet states one". The beat sheet is `data/audio_cues_source.json`, which is the
cue list's own 17 rows copied into the game for the tests to read; its `_copied` field warns that these are the
musician's working labels, not the game's. The second column is the shipped take's own `bpm` field from its
`_loop.json` sidecar, which is the render's number and not a plan.

| cue | beat sheet bpm and meter | the named take's own bpm (sidecar) | disagreement |
| --- | --- | --- | --- |
| PP-01 | 84, 3/4 | 126.0001 (`pp_01_title/pp_01_title_loop.json`) | the file is at 126, the sheet says 84 |
| PP-02 | 132, 4/4 | 126.0001 (`pp_drive_master1_loop.json`) | the file is at 126 |
| PP-03 | 108, 4/4 | 68.0 (`pp_03_harbor_master1_loop.json`) | the file is at 68 |
| PP-04 | 150, 4/4 | 176.0 (`pp_04_navy_sailors_master1_loop.json`) | the file is at 176; D3's 168 is the `pp_fight` family's own measured 167.9999, and that family has no row |
| PP-05 | 120, 4/4 | 96.0 named, 128.0 for `_v5` | v5 is a re-cut at 128, so the row and the newest take are also a tempo apart |
| PP-06 | 138, 3/4 | 132.0001 (`percy_theme_loop.json`, and the same in v2 to v4) | the file is at 132 |
| PP-07 to PP-16, in row order | 66, 96, 132, 156, 160 to 176, 100, 150, 96 then 144, 72, 76, 92 | nothing rendered | nothing to compare |

Read plainly: 6 of the 6 shipped cues disagree with the beat sheet's tempo, and every one of them was rendered at
its own number. The sheet is a plan from the round 1 note and is not a measurement of any file, so nobody should
quote it as one. PP-04 is the one that costs something: D3 rules "the battle cue stays 168 bpm" while the row it
names plays a 176 bpm render, and 168 is measurably the tempo of the unwired two-state fight cue. Both statements
are true of the file each was made about, and the id PP-04 is doing the confusing. D3's own file table is stale in
the same way: it writes PP-04's `delivered_file` as `assets/audio/pp_04_navy_sailors/pp_04_navy_sailors.ogg` and says
the ruling does not change it, while the row has named `pp_04_navy_sailors_master1.ogg` since 11:43 today. The
master is the same music at the delivery loudness, so the ruling's intent survives the re-point, but the cell does
not.

## 9. The commands, and their output

Measured on CitadelArana, 2026-10-26. Each block is the command that produced the numbers above, pasted as it ran.

Every named file exists (check 2 of the card):

    $ cd assets/audio && for f in pp_01_title/pp_01_title.ogg pp_drive_master1/pp_drive_master1.ogg \
        pp_03_harbor_master1/pp_03_harbor_master1.ogg pp_04_navy_sailors_master1/pp_04_navy_sailors_master1.ogg \
        pp_05_small_ship/pp_05_small_ship.ogg percy_theme/percy_theme.ogg; do
        if [ -f "$f" ]; then echo "EXISTS $f"; else echo "MISSING $f"; fi; done
    EXISTS pp_01_title/pp_01_title.ogg
    EXISTS pp_drive_master1/pp_drive_master1.ogg
    EXISTS pp_03_harbor_master1/pp_03_harbor_master1.ogg
    EXISTS pp_04_navy_sailors_master1/pp_04_navy_sailors_master1.ogg
    EXISTS pp_05_small_ship/pp_05_small_ship.ogg
    EXISTS percy_theme/percy_theme.ogg

Durations, ffprobe on the file itself (check 1 of the card), named file first and the drift candidate second where
the two differ:

    $ for f in pp_01_title/pp_01_title.ogg pp_01_title_v9/pp_01_title_v9.ogg \
        pp_drive_master1/pp_drive_master1.ogg pp_03_harbor_master1/pp_03_harbor_master1.ogg \
        pp_04_navy_sailors_master1/pp_04_navy_sailors_master1.ogg pp_05_small_ship/pp_05_small_ship.ogg \
        pp_05_small_ship_v5/pp_05_small_ship_v5.ogg percy_theme/percy_theme.ogg \
        percy_theme_v4/percy_theme_v4.ogg pp_boarding_master1/pp_boarding_master1.ogg; do
        printf '%-52s ' "$f"; ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$f"; done
    pp_01_title/pp_01_title.ogg                          74.266803
    pp_01_title_v9/pp_01_title_v9.ogg                    74.285646
    pp_drive_master1/pp_drive_master1.ogg                178.563333
    pp_03_harbor_master1/pp_03_harbor_master1.ogg        225.882358
    pp_04_navy_sailors_master1/pp_04_navy_sailors_master1.ogg 43.636349
    pp_05_small_ship/pp_05_small_ship.ogg                60.000000
    pp_05_small_ship_v5/pp_05_small_ship_v5.ogg          60.000000
    percy_theme/percy_theme.ogg                          43.636327
    percy_theme_v4/percy_theme_v4.ogg                    43.636327
    pp_boarding_master1/pp_boarding_master1.ogg          32.000000

Digests (section 2):

    $ sha256sum pp_01_title/pp_01_title.ogg pp_01_title_v9/pp_01_title_v9.ogg \
        pp_drive_master1/pp_drive_master1.ogg pp_03_harbor_master1/pp_03_harbor_master1.ogg \
        pp_04_navy_sailors_master1/pp_04_navy_sailors_master1.ogg pp_05_small_ship/pp_05_small_ship.ogg \
        pp_05_small_ship_v5/pp_05_small_ship_v5.ogg percy_theme/percy_theme.ogg \
        percy_theme_v4/percy_theme_v4.ogg pp_boarding_master1/pp_boarding_master1.ogg
    e50e264dd076b9f743e9c71960460ab3be6a245e36c61bb8ee76293162b01574 *pp_01_title/pp_01_title.ogg
    f597b118c48fee6ea375b7e8e144d066a03a72eb9ea9e9fa699e43bae7a52137 *pp_01_title_v9/pp_01_title_v9.ogg
    ef333b87f4850b37501408b7a06a26e6e4fd37607d03b3c62fae5a5972f78aaf *pp_drive_master1/pp_drive_master1.ogg
    d824298aefaa68d3d548c25c5c8d3ba38ecd383b324a949060e513c602b3e890 *pp_03_harbor_master1/pp_03_harbor_master1.ogg
    e600a607cbfc4464f57eda926e388744731ea2bd72cbe4efb447b9bb03a2a369 *pp_04_navy_sailors_master1/pp_04_navy_sailors_master1.ogg
    9d82a847c80a970eb0b1668afcc98b33e2e36eeec2b2cb5d0a657a99048d3472 *pp_05_small_ship/pp_05_small_ship.ogg
    7e58c129b4de3a9973113f66c06f5ea9642b6ff6a3e3e4fbebe7ac2cae67932f *pp_05_small_ship_v5/pp_05_small_ship_v5.ogg
    2a8f3a5af8516c06b4f20649cdf606ef98ecb636fc2a879068bf059502669c9a *percy_theme/percy_theme.ogg
    a7452b74d8e8062073a396010671e5083e98bdb50d4807c2089b3cb1e6110285 *percy_theme_v4/percy_theme_v4.ogg
    4043175f7ea9d3e0a7af20edcc71dcebc22e2b1dbc4a21d1197992029c57cea4 *pp_boarding_master1/pp_boarding_master1.ogg

The inventory behind the newest column, and the count of what was looked at, by family. Check 3 of the card, the
DRIFT count with the command that produced it, is the last block in this section.

    $ cd assets/audio && find . -name '*.ogg' -printf '%TY-%Tm-%Td %TH:%TM %p\n' | sort -k4
    (51 lines, one per non-effect OGG, all pasted into the working run)

    $ find . -name '*.ogg' | wc -l ; find ./sfx -name '*.ogg' | wc -l ; find . -name '*.ogg' -not -path './sfx/*' | wc -l
    81
    30
    51

Newest per family, the comparison the DRIFT column rests on:

    $ find pp_01_title pp_01_title_v6 pp_01_title_v7 pp_01_title_v8 pp_01_title_v9 title_theme title_theme_v2 \
        title_theme_v3 title_theme_v4 title_theme_v5 title_theme_v6 -name '*.ogg' -printf '%TY-%Tm-%Td %TH:%TM %p\n' | sort | tail -1
    2026-10-26 12:30 pp_01_title_v9/pp_01_title_v9.ogg

    $ find pp_05_small_ship pp_05_small_ship_v2 pp_05_small_ship_v3 pp_05_small_ship_v4 pp_05_small_ship_v5 \
        -name '*.ogg' -printf '%TY-%Tm-%Td %TH:%TM %p\n' | sort | tail -1
    2026-10-25 00:25 pp_05_small_ship_v5/pp_05_small_ship_v5.ogg

    $ find percy_theme percy_theme_v2 percy_theme_v3 percy_theme_v4 \
        -name '*.ogg' -printf '%TY-%Tm-%Td %TH:%TM %p\n' | sort | tail -1
    2026-10-26 06:40 percy_theme_v4/percy_theme_v4.ogg

The families, so the comparison can be repeated exactly as it was made:

| cue | folders its newest check covers |
| --- | --- |
| PP-01 | `pp_01_title`, `pp_01_title_v6` to `pp_01_title_v9`, `title_theme`, `title_theme_v2` to `title_theme_v6` |
| PP-02 | `pp_drive`, `pp_drive_v2`, `pp_drive_v4`, `pp_drive_master1` |
| PP-03 | `pp_03_harbor`, `pp_03_harbor_v2`, `pp_03_harbor_v3`, `pp_03_harbor_v4`, `pp_03_harbor_master1` |
| PP-04 | `pp_04_navy_sailors`, `pp_04_navy_sailors_v2`, `pp_04_navy_sailors_v3`, `pp_04_navy_sailors_master1` |
| PP-05 | `pp_05_small_ship`, `pp_05_small_ship_v2` to `pp_05_small_ship_v5` |
| PP-06 | `percy_theme`, `percy_theme_v2` to `percy_theme_v4` |
| PP-07 to PP-16 | no folder exists, so nothing to search |

`pp_fight`, `pp_fight_v2` to `pp_fight_v6`, `pp_arrival`, `pp_arrival_v2`, `pp_boarding`, `pp_boarding_v2`,
`pp_boarding_v3`, `pp_boarding_master1`, `hadrian_theme`, `baroque_demo` and `render2_demo` are deliberately outside
every family: no row names them, which is section 5's subject.

The file the build actually plays on the title screen, and the absent cue mirror (section 7):

    $ grep -n 'title_theme") return pp_audio_play_theme' game/scripts/pp_audio/pp_audio.gml
    471:    if (_cue == "title_theme") return pp_audio_play_theme(_a);

    $ test -d game/datafiles/music && echo "music dir EXISTS" || echo "music dir ABSENT"
    music dir ABSENT

    $ ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 game/datafiles/streams/title_theme_v3_126.ogg
    74.285646

    $ sha256sum game/datafiles/streams/title_theme_v3_126.ogg assets/audio/title_theme_v3/title_theme_v3_126.ogg
    dedfda8291265fcdca4b54a58978fda58534c0481e184ad7c24829da1356b749 *game/datafiles/streams/title_theme_v3_126.ogg
    dedfda8291265fcdca4b54a58978fda58534c0481e184ad7c24829da1356b749 *assets/audio/title_theme_v3/title_theme_v3_126.ogg

The uncommitted state of `data/audio.json` (section 1's caveat):

    $ git status --porcelain data/audio.json ; git diff --stat data/audio.json
    M projects/primordial-paradox/data/audio.json
     projects/primordial-paradox/data/audio.json | 21 +++++++++++++++++----
     1 file changed, 17 insertions(+), 4 deletions(-)

The DRIFT count, read off section 1's own table in this file (a plain `grep -c '| DRIFT |'` gives 9, because the
string is also a column heading in two tables and a value in the demo order table, so the command is scoped to the
ledger table):

    $ awk '/^## 1\. The ledger/,/^## 2\. Digest/' knowledge/MUSIC-CUE-LEDGER-2026-10-26.md \
        | grep -c '^| PP-[0-9ab]* | .* | DRIFT |$'
    3

    $ awk '/^## 1\. The ledger/,/^## 2\. Digest/' knowledge/MUSIC-CUE-LEDGER-2026-10-26.md \
        | grep '| DRIFT |$' | cut -d'|' -f2,9 | sed 's/^ *//;s/ *$//'
    cue | newest mtime
    PP-01 | 2026-10-26 12:30
    PP-05 | 2026-10-25 00:25
    PP-06 | 2026-10-26 06:40

## 10. What this file does not do

- It does not edit `data/audio.json`. No row moved, and the three drifted rows are still drifted the second after
  this file was written.
- It does not decide a drift. PP-01's acceptance is D4's, PP-04's wiring is D3's and card t_279ef225's, PP-17's row is
  the forward card D1 names, and PP-05's take is the card FINAL-MIX section 6 hands forward.
- It does not measure loudness, seams or peaks: `knowledge/FINAL-MIX-2026-10-26.md` owns those and nothing here
  restates them.
- It does not re-render anything. Every duration and digest is a read.
- It does not score the music. The ear pages own the scores, and section 6 is the warning about reading them by id.
