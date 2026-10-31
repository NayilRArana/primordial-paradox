# Review of R21a and R21b: the drive room against the drive scene against the shot list, 2026-10-24

Card t_3cca8576, created 2026-10-23 by gamedev. Reviewer: code-review, this run only.
The two cards are read as one unit: `knowledge/DRIVE-SHOT-LIST.md` is the authoring table, R21a (`t_e9c7b280`,
commit c464edd) owns the room that draws the film, R21b (`t_c27552e3`) owns the row in `data/scenes/all.json`. The
question is not whether each card passed its own check, it is whether the picture, the data and the table are one
film or three.

States reviewed:

| What | State | sha256 (first 16) |
| --- | --- | --- |
| `knowledge/DRIVE-SHOT-LIST.md` | working tree, 230 lines, mtime 2026-10-22 13:21, **untracked** (`??`) | `ea200985f19729ff` |
| `data/scenes/all.json`, the `drive_to_southampton` row | measured at HEAD 9d72974 (pasted by DRIVE-MAP at 3c349b6), re-compared at HEAD f41531b after the tree moved mid review: the row is byte identical, canonical sha256 `5344ea28...f8f959d`. The file differs from HEAD only in three ship scene lines, not the drive | `bcf231d100797080` |
| `game/scripts/pp_drive/pp_drive.gml` | working tree, last commit c464edd, mtime 2026-10-23 02:33 (two later edits by other lanes per its own handoff) | `e89786a5f58346d3` |
| `game/rooms/rm_pp_drive/rm_pp_drive.yy` | HEAD, c464edd | `1f7d7f53b5e5a049` |
| `data/title_timing.json`, the tempo source | HEAD, `bar_steps` 87 since e26709b (TEMPO-1, 2026-10-22 14:11) | `4a2c5013c5046e47` |

The shot list itself is untracked. That is the same exposure the review of 2026-10-22 recorded for spec 17: the file
this review's verdict rests on is one cleanup away from gone. It is not this card's file to commit, and I did not.

## Verdict

| Artifact | Verdict | Why |
| --- | --- | --- |
| R21a, the room (`rm_pp_drive`, `pp_drive.gml`) | PASS WITH FIXES | Twelve distinct pictures, the twelve durations, four fades, eight places, all measured and sound. But the room is not on the route, its twelve durations are a second copy of the data with no test tying the two, and its pages advance on their own against spec 05. |
| R21b, the scene data (`drive_to_southampton`) | PASS WITH FIXES | The 59 commands reproduce the shot list shot for shot; 10,680 steps is mine by arithmetic, not the card's; `check_data` exit 0 and 50 tests pass in my run. The four sign flags the shot list names are absent (already carded), and the engine bed cannot loop. |
| The unit, picture against data against table | PASS WITH FIXES | The three agree on every number today. They are not wired to each other: the route plays the scene on a corridor map, the room plays pictures the route never enters, and the bar grid all twelve durations are snapped to is stale against its own cited source. |

A PASS WITH FIXES here means the numbers hold and the film can be cut; the fixes are decisions and missing rows, not
broken code. Nothing in this review is a judgment of either author's care. Both cards are careful.

## The check I named before starting, and what it returned

Named first: re-derive the twelve durations from `data/scenes/all.json` with the step costs spec 06 fixes (camera 24,
fade 12, `say` and `music` and `sfx` and `end` 0, `wait` its own steps), compare them to the shot list's section 2
table and to the twelve rows in `pp_drive_shots()`, then re-run `tools/check_data.py` and the three drive test files.

Returned:

```
check_data: all files pass                     exit 0
pytest tests/test_drive_map.py tests/test_slice_route.py tests/test_scene_runner.py -q
50 passed in 1.19s
my arithmetic over the 59 commands:            10,680 steps, 178.00 s
data-derived duration list:  [688, 860, 602, 774, 1032, 1118, 860, 860, 1118, 1118, 688, 962]
room table step list:        [688, 860, 602, 774, 1032, 1118, 860, 860, 1118, 1118, 688, 962]
shot list section 2 list:    [688, 860, 602, 774, 1032, 1118, 860, 860, 1118, 1118, 688, 962]
equal on all three:          True, and the sum is 10,680
```

## The twelve shots, one row each

The picture column cites the frame R21a's capture wrote for that shot, hashed by me at 1x or 3x, plus the room's
`place`. Frame hashes are the first 12 characters of the sha256 of the RGB pixels.

| # | Shot list: place and steps | Data steps | Room place, steps | Picture evidence | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | city, Big Ben pan down, 688 | 688 | `city`, 688 | frame 01, 8 colours, 768x720, sha `a1cdc19b5a47`; the pan is 48 px of clock face, the car is deliberately not in shot | MATCH |
| 2 | city, London street and the Thames, 860 | 860 | `city`, 860 | frame 02, 10 colours, sha `769931a14d82`; Thames band, car shrinking, distinct from shot 1 | MATCH on duration and reading; the street and river are placeholder bands, which the shot list's `Q3` already records as no art |
| 3 | gantry, SOUTHAMPTON 55, 602 | 602 | `gantry`, 602, sign `55`, page `drive_sign_55` | frame 03, 10 colours, sha `2c03c4e42d54`, plus the 1x and the PPU frame; camera x 37, L3 offset 89, inside the stated 0 to 90 | MATCH |
| 4 | open motorway, rain starts, wipers, 774 | 774 | `motorway`, 774 | frame 04, 10 colours, sha `4dfed3e36511`; rain and wiper bands are drawn | MATCH on the picture; difference: no rain cue exists and the data carries none, so the shot is silent, which `Q2` already records |
| 5 | open motorway, radio pages 1 and 2, 1032 | 1032 | `motorway`, 1032, 2 pages | frame 05, 10 colours, sha `0c4847df6eac`; 1,008 wait steps for two pages, 504 each, the shot list's own budget | MATCH |
| 6 | open motorway, radio pages 3 and 4, the sign 43, 1118 | 1118 | `motorway`, 1118, sign `43`, 3 pages | frame 06, 10 colours, sha `7f3bca1abf5a`; distinct from shot 5 | MATCH on duration, sign and captions; difference: the shot list's page budget says 365 a page, the data provides 1,082 wait steps for three pages, which is 360.67 a page (13 steps short of the claim); and the shot list's command column for this shot omits the 12 step fade out the data carries |
| 7 | Twyford Down cutting, headlight pool, 860 | 860 | `cutting`, 860 | frame 07, 10 colours, sha `d486fe9a14af`; camera x 83, L3 offset 199, inside the stated 170 to 200 | MATCH |
| 8 | cathedral silhouette, one caption, 860 | 860 | `cathedral`, 860, page `drive_cathedral` | frame 08, 9 colours, sha `bacf7cf924d4`; camera x 141, L3 offset 338, inside the stated 320 to 340; 836 wait steps, the stated budget exactly | MATCH |
| 9 | open motorway, radio pages 5, 6, 7, the sign 30, 1118 | 1118 | `motorway`, 1118, sign `30`, 4 pages | frame 09, 10 colours, sha `6192370b7bbb`; 1,094 wait steps for four pages, 273.5 each against the stated 274 (rounding) | MATCH |
| 10 | downland, storm, first lightning, moon, 1118 | 1118 | `downland`, 1118 | frame 10, 10 colours, sha `16c41eab92af`; camera x 25, L3 offset 60, the stated window's edge | MATCH on duration and picture; difference: the 2 frame palette flash `Q1` asks for is not built, the shot carries `sfx thunder_soft` only |
| 11 | slip road, the sign 20, headlights, 688 | 688 | `slip`, 688, sign `20`, page `drive_sign_20` | frame 11, 8 colours, sha `e8eecb1ca29c`; 664 wait steps, the stated budget exactly | MATCH |
| 12 | docks, cranes, containers, the lit ship, 962 | 962 | `docks`, 962 | frame 12, 9 colours, sha `193a10734976`; two camera moves, wait 902, fade out 12, then `end` last | MATCH on duration and count; the docks are placeholder bands (`Q3`), and the frame is 962 steps, the only shot off the bar grid, as section 2 says |

Twelve rows, twelve MATCH on duration. Four rows carry a difference, all of them already named by the shot list's own
`Q` list or by this review's findings below; none of them moves a step count.

## The 10,680, by arithmetic from the data

Not from either card's claim. The 59 commands cost, by spec 06:

| Command | Count | Steps each | Steps |
| --- | --- | --- | --- |
| `camera` | 16 | 24 | 384 |
| `fade` | 4 | 12 | 48 |
| `wait` | 23 | its own steps: 604, 812, 578, 750, 1,008, 1,082, 824, 836, 1,094, 1,094, 664, 902 by shot | 10,248 |
| `say` | 12 | 0 | 0 |
| `music` | 1 | 0 | 0 |
| `sfx` | 2 | 0 | 0 |
| `end` | 1 | 0 | 0 |
| **total** | **59** | | **10,680** |

384 + 48 + 10,248 = 10,680 steps, which is 178.00 s at 60 steps a second. The cumulative ends fall on the shot list's
eleven hard cuts exactly: 688, 1,548, 2,150, 2,924, 3,956, 5,074, 5,934, 6,794, 7,912, 9,030, 9,718, then 10,680 after
shot 12. The macro `PP_DRIVE_TOTAL_STEPS` in the room is 10,680 too, and `pp_drive_table_ok()` refuses a table that
does not sum to it. `next` is nowhere; `end` is the last command; every command name is one of spec 06's fifteen.

## Findings

### F1 (the finding that matters) The bar grid is stale, and every duration inherits it

Shot list section 1 says the bar is "85.714 exact, 86 as the integer each cut is snapped to", and cites
`data/title_timing.json` `steps_per_bar` and `bar_steps` as the source. That file says `bar_steps` is **87**, not 86,
and its own `_integer_note` explains why: 87 is three beats of 29, and "rounding the bar on its own gave 86, which is
not three beats". The change landed at e26709b (TEMPO-1) on 2026-10-22 at 14:11, fifty minutes after this shot list
was written at 13:21. The shot list is not wrong by carelessness; its citation moved underneath it.

What that costs, measured against the two grids that exist:

| Grid | Cut 1 at 688 | Cut 11 at 9,718 | Drift |
| --- | --- | --- | --- |
| 86, the shot list's snap | bar 8.000 | bar 113.000 | 0 by construction |
| 85.714, the music's exact bar at 126 bpm | bar 8.027 | bar 113.377 | late by 0.286 steps a bar, 32 steps = 0.54 s at cut 11, more than a beat (a beat is 28.57 steps) |
| 87, the title's own integer lattice | bar 7.908 | bar 111.70 | early by 1 step a bar, 113 steps = 1.88 s at cut 11 |

The film's stated reason for existing is that "every hard cut lands on a bar line, because a cut only reads as
intended when the music says so". On the exact music grid and on the title's own counter it does not. This is a
gamedev decision, not a code fix: which lattice is the drive cut to? On the 87 lattice the same twelve bar counts come
to 10,793 steps (179.88 s), so the 10,680 target and every duration would be re-derived, and the music cue, which
`tests/test_cue_cut_v3.py` pins to `film_steps` 10,680, would have to move with it. On the exact 85.714 grid the same
question comes back smaller but still open (32 steps, 0.54 s at the last cut). `Q:` for gamedev.

### F2 (blocking, already carded) The four sign flags are in no table and the scene sets none

`data/flags.json` holds 16 rows and none of them is `sign_55_seen`, `sign_43_seen`, `sign_30_seen` or
`sign_20_seen`; the drive scene has 0 `setflag` commands; a grep for the four names across `*.gml`, `*.json` and
`*.py` returns nothing outside prose. Shot list section 5 says each sign is "one beat, one flag and one caption", and
section 10 hands the flags to the scene card. Measured, the film's only counting device leaves no route ledger fact,
so a player can count four signs and the game records none of them. `check_data` passes anyway, which is the second
half of the finding: nothing in the checker requires that a caption's sign has a flag. Card t_1cbff27e (gamedev,
ready) holds the gap, the proof that four `setflag` commands cost 0 steps, and the fact that without the four flag
rows `check_data.py:1575` refuses the commands by name. I did not add the flags; that is data, not my file.

### F3 (fix) The engine bed cannot loop, so shot 2's "from here to the end" is not delivered

Shot list section 3 gives shot 2 `sfx car_engine_loop` running "from here to the end"; the data carries exactly one
`sfx car_engine_loop`, at command 9. `pp_audio_sfx(_kind, _id)` takes no loop argument, and `data/audio.json`'s own
row for `car_engine_loop` records the `Q`: "pp_audio_sfx plays every effect with loop off, so the drive needs a
looping play call (or a music-slot ambience) before this file can actually loop in the runner". So the bed plays once
for 0.8 s and stops, and shots 3 to 12 have no engine under them. A `Q:` for gamedev and the audio lane, not a defect
in the scene row.

### F4 (fix, documentation) Two arithmetic slips in the shot list, neither in the data

Shot 6's page budget: the shot list says 365 steps a page for three pages, "the shot's steps minus its 24 step camera
move", which is 1,094 / 3 = 364.67. The shot also spends its last 12 steps on the fade out, so the pages actually
have 1,082 wait steps, 360.67 a page. The data is right and the budget row is 13 steps generous.

Shot 6's command column omits `fade out 12` even though section 8 counts it as one of the four fades and the data
carries it at command index 29 of the 59. Small, but it is the column a coder types from.

Section 4's closing sentence says "Four of the eight carry more than one shot (city two, open motorway four) and four
carry one each." The parenthetical, the table above it and the data all say two locations carry more than one shot
(city twice, open motorway four times) and six carry one. The sentence is wrong on both halves.

### F5 (decision) There are two drives, and the route plays the one without the eight places

`data/slice.json`'s `drive` step is `kind: "scene"`, scene `drive_to_southampton`, which the runner plays on the map
the row names, `drive_m4_corridor` (160 by 24, road on row 8, start (0,8), arrive (159,8), no triggers, no rails).
`rm_pp_drive` is reachable only when `PP_DRIVE_ROOM` is set (`game/objects/obj_pp_game/Create_0.gml:62`, "unset in
every real launch"), and the room is 256 by 240 with `obj_pp_drive` drawing its own frame.

Consequences, measured:

- On the route the drive is one continuous corridor plus twelve caption boxes and sixteen camera moves. The eight
  locations the shot list counts in section 4 exist as pictures only in the room, which the route does not enter.
- The twelve durations exist twice: `pp_drive_shots()` in GML and the `wait`/`camera`/`fade` steps in the JSON. They
  are equal today (I checked all twelve above), and no test ties them: `tests/test_drive_map.py` pins the JSON row's
  sum to 10,680, `tests/test_battle_font.py` reads the GML for font reasons, and nothing compares the two tables. A
  future edit to either will pass the whole suite and the two films will drift.
- The room's pages advance on their own (`pp_drive_page_index` from the shot clock, said so in its own comment),
  against spec 05 and the shot list's "a page advances on the player's press and never on its own". That is honest
  for a placeholder; it stops being honest the moment the room is wired.

`Q:` for gamedev: does the drive ship as the room (then the route needs the door and the data becomes the room's
input, not a parallel copy), or as the scene on the corridor (then the eight places and the room are for the
capture only, and somebody should say so in `knowledge/DRIVE-SHOT-LIST.md`)?

### F6 (observation, tree drift) Another lane's uncommitted fix decides whether the drive draws its own tiles

R21b recorded as not proven that "`pp_map_tile_set_for_room` has no `drive_night` branch and `sync_art.py` does not
read `assets/tiles/drive`, so every cell draws the ship's deck tile". That is exactly true at HEAD: `git show
HEAD:...pp_map_tile.gml | grep -c drive_night` returns 0, and `PP_TILE_SET_DRIVE` does not exist at HEAD.

It is not true in the working tree. `pp_map_tile.gml` line 249 and `tools/sync_art.py` are modified and uncommitted
(mtime 2026-10-24 21:06, card t_af836a62), adding the `drive_night` branch and the drive sheet, and
`game/datafiles/art/drive_tiles.png` exists. So at HEAD the corridor road is drawn with the ship's deck tiles and in
the tree it is drawn with the drive sheet, and which one a build sees depends on an uncommitted edit. This review is
against HEAD for that function and says so; the verdict does not rest on the fix being present.

### F7 (observation, outside the drive) HEAD moved mid review, and the two scenes copies disagree at HEAD

Measured at 21:10, `data/scenes/all.json` and `game/datafiles/scenes/all.json` differed in three lines, all ship scenes
(`ship_gangway` against `ship_rail_note`, and a `ship_log_open` line present only in `data/`). At 21:16 the copies are
equal in the working tree, and the working tree's `data/` copy differs from HEAD's, which carries the `ship_rail_note`
version. HEAD also moved from 9d72974 to f41531b during this review (three commits by card t_bc38ffd6), so what is
committed and what is in the tree are two different scenes files, both only in the ship rows. The drive block is
identical in all three (canonical sha256 `5344ea28...f8f959d`), and `pp_drive.gml`, `rm_pp_drive.yy`,
`data/title_timing.json` and `data/flags.json` are clean against the new HEAD, so nothing in this review moves. Said
for the record because the game reads `game/datafiles`, and a reviewer who checked one copy and shipped the other
would be wrong about the ship.

## What I re-measured and found sound

- Twelve durations, all equal to the shot list, sum exactly 10,680 steps = 178.00 s, by my own command ledger.
- The eleven cumulative cut steps are the shot list's eleven hard cuts, in order.
- 16 camera commands, and every one lands inside its shot's stated L3 window: x 37 gives offset 89 (shots 3, 5, 6 and
  9 state 0 to 90; shot 11 states no window and uses 37 too), x 83 gives 199 (170 to 200, shot 7), x 141 gives 338
  (320 to 340, shot 8), x 25 gives 60 (0 to 60, shot 10), x 0 gives 0 for the city and docks. The furthest camera,
  141, plus a 16 tile screen is 157, inside the map's 160.
- Four fades at 12 steps: in on shot 1 (command 1), out at the end of shot 6 (29), in on shot 7 (30), out on shot 12
  (57). Each is counted inside its shot, so the twelve durations still sum to 178.00 s.
- Eight distinct places in the room table (`city, gantry, motorway, cutting, cathedral, downland, slip, docks`), two
  of them carrying more than one shot (city two, open motorway four) and six carrying one. That is what the data
  shows and it is not what section 4's closing sentence says; see F4.
- Twelve caption ids, distinct, all present in `data/dialogue/all.json`, and in the room table in the same order as
  the scene's twelve `say` commands.
- Four sign rows: 55 on shot 3, 43 on 6, 30 on 9, 20 on 11, in both the data and the room table.
- The capture's twelve frames are twelve distinct byte-level pictures at 768x720 (3x), 8 to 10 colours each, which is
  R21a's own claim, reproduced by hashing its files rather than by re-reading its report.
- `check_data` exit 0; 50 tests pass in my run.

## Deltas this review opens for the manager

1. F1 is the one that can change the film: the bar grid the twelve durations are snapped to is stale against
   `data/title_timing.json`, and no document in the tree states which lattice the drive is actually cut to.
2. F5 is the one that decides what "the drive" means: the room's pictures, or the scene on the corridor. Until it is
   answered, two implementations both claim the same twelve numbers and only one is reachable.
3. F2 is already carded (t_1cbff27e, gamedev, ready) and blocks nothing in the timing.
4. F3 needs a looping play call owned by the audio lane; the data is ready for it.
5. F4 is a three-line correction in the shot list, which no one owns because the file is untracked.

## Limits of this review

- Nothing ran in GameMaker this run. The twelve pictures are R21a's own frame writes in `output/drive`, which I hashed
  and counted; that is evidence inspection, not a fresh capture.
- The capture holds each shot for 24 steps and writes the frame at step 12 (`PP_DRIVE_CAPTURE_STEPS` 24,
  `PP_DRIVE_CAPTURE_AT` 12), so it proves neither the real durations nor the fade tails. No run has played 178 s of
  film or held a shot for 1,118 steps.
- I did not read the sign text in the frames. "SOUTHAMPTON 55" in shot 3 rests on R21a's `nes_check` crop and on the
  room's own sign table, and my check of that crop is its 5 colours and the room's drawing code, not OCR.
- The bar and beat figures are arithmetic against `data/title_timing.json`. No listening test was run, so whether a 0.54
  s or 1.88 s cut offset is audible at 126 bpm is an argument from the numbers, not an ear.
- The working tree differs from HEAD in another lane's file (F6). I reviewed HEAD and named the difference rather than
  choosing which one is live.

Scope: this review wrote `knowledge/REVIEW-R21-DRIVE-2026-10-24.md` and nothing else. No code, no data, no spec and
no card body was edited, and no key or login file was read.
