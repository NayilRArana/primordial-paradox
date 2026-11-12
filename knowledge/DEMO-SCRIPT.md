# Demo script: three minutes, six shots, one claim per shot

Card t_c0f33e5d (GAME-ROADMAP-2 child R39), research-assistant, written 2026-10-22 for Primordial Paradox.
Rewritten 2026-11-12 by research-assistant under card t_ec47a1dd, to the quay only build.
Scope: this file only. It does not write route data, the recorder or the edit. `knowledge/VIDEO-PLAN.md` (R44) is
built from this file, and the builder's card t_892cc851 recuts the picture from it.

What it is for: a person opens this file in the recording booth, presses the keys in the order they appear, and
makes no decision. Every shot names what is on screen, what the player inputs, what the music does, what the caption
says, and which claim of the write-up that shot is evidence for.

Authority, in the order it was read:
1. `knowledge/DEMO-AUTHORITY-RULING-2026-11-12.md` (commit 005360a8) rules that the build governs what the demo
   shows and this file governs only its shape: the total length, six shots, one caption and one claim per shot, and
   the receipts read out of `data/meta_bake.json` at edit time.
2. `data/slice.json`, and its shipped copy `game/datafiles/slice.json`, is the route: title, crawl, quay, morgan,
   percy, five steps in that order.
3. `..\arananet\meta-hackathon\PLAN-WIN-2026-10-22.md` section 1 and `..\arananet\meta-hackathon\kit\ONE-PAGER.md`
   are the claims the shots are evidence for. Quoted phrases below are verbatim from those two files.
4. The quay's own data: `data/maps/all.json` (the map `southampton_town_quay`, its triggers, its two actors, its
   cue), `data/scenes/all.json` (the quay scenes), `data/encounters/all.json` (`morgan_gate`, `percy`),
   `data/enemies/all.json` (`morgan`, `percy`), `data/dialogue/all.json` (the quay pages and the door pages),
   `data/meta_bake.json` (the recorded answers), `data/talk_cards.json` (the cards), `data/credits.json` (the roll).
5. The engine's own numbers: `game/scripts/pp_storm/pp_storm.gml` (the hurricane's clock),
   `pp_battle_director/pp_battle_director.gml` (the spare gate), `pp_battle_text/pp_battle_text.gml` (the TALK panel,
   the WILL bar, the effect table), `pp_credits/pp_credits.gml` (the roll's clock), `pp_save/pp_save.gml` (the save
   panel and the entry autosave).
6. `specs/19-llm-talk.md` is the bake and the receipt fields; `specs/05`, `07`, `11`, `14` are the inputs and the
   screens this script presses keys into.

---

## 1. The six shots at a glance

| Shot | Clock | Seconds | Steps | Route step (`data/slice.json`) | The claim it proves | What is drawn over the frame |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | 0:00.00 to 0:16.00 | 16.00 | 960 | `title` | "whether it works", and "AI that obeys hardware limits" | one caption |
| S2 | 0:16.00 to 0:29.00 | 13.00 | 780 | `crawl` | "Kronos and Zeus reincarnated on the M3" | one caption |
| S3 | 0:29.00 to 0:39.00 | 10.00 | 600 | `quay` | the hurricane, and the block it lands on | one caption |
| S4 | 0:39.00 to 1:18.00 | 39.00 | 2,340 | `quay`, then `morgan` | the wind is the only gate, and Morgan offers three answers | one caption |
| S5 | 1:18.00 to 1:50.00 | 32.00 | 1,920 | `morgan` | "the person judging your line is a Meta model answering inside a NES text box", and the quay's own saves | one caption, three bake receipts, the network line |
| S6 | 1:50.00 to 3:00.00 | 70.00 | 4,200 | `percy` | "the other is won by talking", and the one ending the game now has | one caption |

Total: 180.00 s, 10,800 steps.

---

## 2. The clock, and why the total is 180.00

- The unit is the step, 60 to a second, the game's own step event (spec 05, spec 07). 180.00 s is 10,800 steps, and
  every row below carries its absolute step so the booth sheet in section 7 can be typed without arithmetic.
- 180 is the middle of the card's 170 to 190 band, and the six lengths are 16, 13, 10, 39, 32 and 70.
- S3 is 600 steps and not the 602 an old cut carried. 602 was the drive's arithmetic on a retired 86 step snap;
  `knowledge/DRIVE-SHOT-LIST.md` section 1 puts every count on the exact 85.714 grid, where seven bars is 600.0. The
  drive is not in the build anyway, so the shot earns its length from the storm: `pp_storm.gml` draws one flash every
  210 to 540 steps (`PP_STORM_WAIT_MIN`, `PP_STORM_WAIT_MAX`) and a flash is 8 steps (`PP_STORM_FLASH_STEPS`), so the
  longest a single flash can be away is 548 steps, and 600 always contains one. The 0.03 s the old snap left behind
  is gone: no shot carries an odd length any more.
- S5's three receipts sit at the clock the old cut measured against, 83.40 s for the first one, because that is the
  second the first reply is whole and held. The two receipts after it are at the seconds their own replies land,
  listed in section 4.
- Fallbacks, all designed, all inside the band, and none of them changes the total:
  1. If the re-bake in Q1 has not landed, S5 draws its caption and its box and no plate. The shot still times to
     32.00 s and the total is still 180.00.
  2. If the credits roll grows past the 2,520 steps the spare cut allows, S6's last frame lands inside the roll
     rather than on its closing card. The total is still 180.00; the ending is what moves.
  3. If Percy's spare is refused, the fight ends on the kill path: `quay_percy_kill` and the `kill` credits, which
     are 24 steps shorter than the spare ones (2,551 against 2,575), so S6 still fits 70.00 s.

---

## 3. S1 to S6, second by second

### S1, the title, 0:00.00 to 0:16.00 (960 steps)

Screen: the attract loop of `rm_pp_title`, seven night layers, the car, the storm cloud, the logo.
Input: none until 0:11.80, then Enter twice.
Music: `title_theme` (PP-01, Title Theme), the A minor waltz at 126 bpm in 3/4, one pass is 52 bars. It starts on
step 0 and runs under the whole shot. The menu press adds the two interface sounds (`menu_move`, then
`menu_select`).
Caption, verbatim: `Cold boot to menu takes 14 seconds. CONTINUE is dim, because nothing is saved yet.`
Caption runs 0:01.00 to 0:14.20.
Claim: "Whether it works is the floor" (PLAN-WIN section 1), proved by roadmap checks 1 and 2, a cold start with no
console window and a menu that opens; and "AI that obeys hardware limits", proved by the frame itself, one 256 by
240 screen, at most 16 colours from `data/palette.json`, a 2 frame palette swap instead of a filter (spec 13,
`data/title_flash.json`).

| t | step | On screen | Input | Music and sound |
| --- | --- | --- | --- | --- |
| 0:00.00 | 0 | attract: sky, moon, the two star layers, the storm cloud over the car, the logo; road dashes one per beat, car bob 1 pixel per beat | none | `title_theme` starts |
| 0:05.80 | 348 | the logo's gold shimmer pass (every 4 bars, 24 step pass) | none | `title_theme` |
| 0:11.60 | 696 | the lightning: the whole screen swaps to the flash palette for 2 frames, then back | none | `title_theme` |
| 0:11.80 | 708 | the logo, its line PRESS Z OR ENTER blinking one blink every 29 steps | Enter (the title's own confirm) | `menu_select` |
| 0:12.10 | 726 | the menu: NEW GAME, CONTINUE, SETTINGS, QUIT; the cursor sits on NEW GAME; CONTINUE is drawn in the second ink because `pp_save_01.json` does not exist yet | none | `menu_move` |
| 0:14.20 | 852 | NEW GAME chosen | Enter | `menu_select` |
| 0:14.40 | 864 | 12 step fade, then the star field of the crawl machine, 24 stars from `data/intro_stars.json`, twinkling on the bar | none | `title_theme` continues |

### S2, the crawl, 0:16.00 to 0:29.00 (780 steps)

Screen: the crawl, 6 beats and 16 rows, from `data/intro_text.json`, drawn over the star field.
Input: confirm held from 0:22.00 to 0:27.00, then released; no other key.
Music: the same cue, `title_theme`, ducked under the words (spec 14 addendum), with the text blip every 3 characters
(`data/title_timing.json` `text.blip_every_chars`).
Caption, verbatim: `The crawl runs 1,238 steps. Hold confirm to read it faster; no page is skipped.`
Caption runs 0:16.60 to 0:27.00.
Claim: "Kronos and Zeus reincarnated on the M3" (PLAN-WIN section 1), which is beats 2 and 3 of the crawl in the
game's own words; and the skip rule, that a held confirm speeds the reveal and a double tap cannot skip the story
(spec 14 addendum, recipe PAC-05).

| t | step | On screen | Input | Music and sound |
| --- | --- | --- | --- | --- |
| 0:16.00 | 960 | beat 1, one row: THE GODS NEVER DIED. | none | `title_theme` ducked; blip every 3 characters |
| 0:17.20 | 1,032 | beat 2, four rows: THEY WERE FORGOTTEN, ... WEARS THIN. | none | as above |
| 0:22.00 | 1,320 | beats 3 and 4 arrive (the four who do not know; tonight a father drives his son south) | confirm held, 3x reveal, no page skipped (spec 05 rule 3) | as above |
| 0:27.00 | 1,620 | release; beat 6 types at 1x: SOUTHAMPTON. OCTOBER. | released | as above, back to 1x |
| 0:28.00 | 1,680 | the last beat whole, then its 60 step hold | none | as above |
| 0:28.80 | 1,728 | 12 step fade out | none | `title_theme` carries the fade |

### S3, the hurricane on Town Quay, 0:29.00 to 0:39.00 (600 steps)

Screen: `southampton_town_quay`, the map the route names, entered at its `start` spawn (24,1), in the map's own
`quay_night` palette. The route's scene is `quay_arrival`, whose whole command list is one `end`: the arrival is the
map itself, and `pp_storm.gml` draws the hurricane over it because this is the map `PP_STORM_ROOM` names. The storm
owns one private seeded stream (seed 20261103), so the same steps always draw the same lightning: a flash is 3 steps
of near white, 2 of the white dither, 3 of the ink dither (`PP_STORM_FLASH_STEPS` 8), and the thunder follows 14
steps later (`PP_STORM_THUNDER_LAG`).
Input: held walk south, one confirm at the Red Funnel door row.
Music: the map's own `music` field, PP-03, Harbor Storm (`data/maps/all.json`, `data/audio.json`). It does not
change inside the shot.
Caption, verbatim: `Town Quay in the hurricane. The storm runs on its own seeded clock, 8 step flashes over a real Southampton block.`
Caption runs 0:29.40 to 0:35.00.
Claim: the block is a real street. The tile plan is built from the project's own OpenStreetMap extract
(`data/maps/southampton_sample.json`, ARRIVAL-CONTENT sections 3 and 4), and the shopfronts on it carry the town's
own names in their own pages: the Red Funnel door says its ferries are not your ship (`say_door_red_funnel`,
`data/dialogue/all.json`). And the weather is the game's, not the film's: one flash of 8 steps on a private seeded
stream, and the thunder 14 steps behind it, with no particle system and no alpha blend.

| t | step | On screen | Input | Music and sound |
| --- | --- | --- | --- | --- |
| 0:29.00 | 1,740 | 12 step fade in from the crawl's fade out; the quay at (24,1); the storm clock at 0 | none | PP-03 starts on the cut |
| 0:29.40 | 1,764 | the walk south begins, two pixels a step, so a tile is 8 steps | hold the walk key | PP-03 |
| 0:32.00 | 1,920 | the player stops at the Red Funnel door row (y 16, x 22 to 24) and faces it | confirm | PP-03 |
| 0:32.20 | 1,932 | `say_door_red_funnel`, one page: Ferries. Not your ship. / Yours has worse snacks. | none | text blips |
| 0:33.20 | 1,992 | the page closes | confirm | PP-03 |
| 0:33.40 | 2,004 | the walk south again, down the middle of the street | hold the walk key | PP-03 |
| 0:35.00 | 2,100 | a flash: 3 steps near white, 2 of the white dither, 3 of the ink dither, and `thunder_soft` 14 steps after it. The first flash lands somewhere in steps 210 to 540 of the entry, and 600 holds at least one whatever the seed draws | none | `thunder_soft` |
| 0:37.00 | 2,220 | the walk continues; the bridge mouth and the water at row 32 come into frame | hold the walk key | PP-03 |
| 0:39.00 | 2,340 | cut: the hero is at y 30, two tiles short of the bridge | none | cut |

### S4, the wind, and Morgan's three answers, 0:39.00 to 1:18.00 (2,340 steps)

Screen: the bridge at row 32 of the quay, shut by the wind; then the street north west, the tower at (5,30), and
Captain Morgan at (6,9) with his clipboard. Then `quay_morgan_encounter`: a face, `thunder_soft`, a 2 step flash,
three pages of `quay_morgan_pre`, `quay_morgan_intro`, and the battle `morgan_gate` on its own `quay_town`
background. The TALK panel opens with three authored answers and, under them, SAY IT YOURSELF.
Input: held walk; confirm at the tower save; confirm on Morgan; confirm through four pages; Down to TALK and confirm;
four cursor moves; the shot ends with the cursor on the first answer.
Music: PP-03 on the map, which stops on the encounter's own `music` field, PP-04, Navy Sailors. A cue change on a
scene start is legal (pacing 4.4).
Caption, verbatim: `Morgan asks three things and two answers are enough. No reply can lose the talk, and the wind drops when he does.`
Caption runs 0:39.60 to 0:45.00.
Claim: the wind is the only gate the quay has, and Morgan is its key. Three tiles of `quay_bridge_wind` at (22 to
24, 32) fire on touch under the condition `!morgan_resolved`, the page says why (The wind shoves you back. / The
bridge is not for you. / Not while Morgan rages.), and the scene moves the hero back up two tiles; the bridge opens
for both outcomes, because `morgan_resolved` is in the encounter's `flags_on_kill` and its `flags_on_spare`
alike (`data/encounters/all.json`). `tests/test_quay_flow.py` pins that the hero cannot reach Percy without it. And
the choice cannot be failed: `morgan_gate` draws three answers plus SAY IT YOURSELF (`talk_morgan`,
`data/dialogue/all.json`), and each answer earns WILL on the encounter's own `talk_mercy` table, soften 50, nudge
35, setback 20, so even the worst of the three is +20 and none of them ends the fight. Two TALK turns are enough to
open SPARE: `trust_per_talk` is 2 and `trust_to_spare` is 3, and the spare gate is `pp_battle_spare_allowed`
(`pp_battle_director.gml`).

| t | step | On screen | Input | Music and sound |
| --- | --- | --- | --- | --- |
| 0:39.00 | 2,340 | the wind page is closed; the hero at y 30, the bridge behind him | confirm closes it | PP-03 |
| 0:39.40 | 2,364 | the feet enter (23,32): `quay_bridge_wind` fires on touch, `!morgan_resolved` is true | none | the page's blips |
| 0:39.60 | 2,376 | the page: The wind shoves you back. / The bridge is not for you. / Not while Morgan rages. | none | PP-03 under the box |
| 0:41.40 | 2,484 | the page closes; the scene moves the hero up two tiles | confirm | PP-03 |
| 0:42.00 | 2,520 | the walk west and north; the quay's building rows, the shopfront doors | hold the walk key | PP-03 |
| 0:45.00 | 2,700 | the tower at (5,30), the quay's second save point, on the way | none | PP-03 |
| 0:46.00 | 2,760 | confirm at the tower save: the Saving panel, the chime once, `pp_save_01.json` written; the panel holds while the write lands | confirm, then confirm | `chime` |
| 0:48.00 | 2,880 | the walk north to Morgan's corner; he stands at (6,9) facing right | hold the walk key | PP-03 |
| 0:51.00 | 3,060 | confirm on Morgan: he faces left, `thunder_soft`, the 2 step flash | confirm | `thunder_soft` |
| 0:51.30 | 3,078 | `quay_morgan_pre` page 1: Rain walks sideways here. / Captain Morgan waits, / clipboard bone dry. | none | blips |
| 0:53.50 | 3,210 | page 2, Morgan: Name. Business. STORM. / His eyes are all cloud. / The pen crackles. | confirm to close page 1 | blips |
| 0:56.50 | 3,390 | page 3: The storm is wearing him. / Free him, somehow. | confirm to close page 2 | blips |
| 0:59.00 | 3,540 | `quay_morgan_intro`: Captain Morgan salutes. / Thunder salutes back. / Talk him round, or fight. Then the battle frame, the HUD, the menu | confirm to close page 3, then confirm the intro | PP-04 from the encounter's `music` |
| 1:02.00 | 3,720 | the battle menu: the cursor on FIGHT; Down to TALK and confirm | Down, confirm | `menu_move`, `menu_select` |
| 1:03.00 | 3,780 | the TALK panel: three authored answers, `May I see the form?`, `Lovely handwriting.`, `The captain is coming!`, and SAY IT YOURSELF under them; WILL 0/100; the hint HEAR HIM OUT: 3 MORE TALKS | none | blips |
| 1:06.00 | 3,960 | the cursor reads the three answers once, and comes back to the first | Down, Down, Down, Up, Up, Up | `menu_move` per move |
| 1:10.00 | 4,200 | the panel is held: four entries, WILL 0/100, the hint under the box | none | PP-04 |
| 1:18.00 | 4,680 | cut, with the cursor on `May I see the form?` | none | cut |

The three answers and the pages are in the tree today: `talk_morgan`, `quay_morgan_pre` and `quay_morgan_intro` in
`data/dialogue/all.json`, the panel's arithmetic in `data/encounters/all.json` under `morgan_gate`, and the fight's
own rows in `data/meta_bake.json` at `fight/morgan/1` to `fight/morgan/3`.

### S5, the three replies, the spare, and the quay's own save, 1:18.00 to 1:50.00 (1,920 steps)

Screen: the same battle. Three TALK turns: the box types a reply from `data/meta_bake.json`, the WILL bar climbs,
the enemy takes its turn, and the panel comes back. Then SPARE in the first ink, `quay_morgan_win_spare`, the map,
and the two pages of `quay_morgan_after_spare` (Where did my cap go? / Go. Percy is worse. then The wind sulks
south. / The bridge is calling.). Then the walk south past the open bridge and the pier save at (23,35).
Input: confirm on each answer, confirm to close each reply, one SPARE, two page presses, held walk, confirm at the
pier save.
Music: PP-04 under the fight; PP-05 is not used on this route; the map's PP-03 returns when the scene ends, which is
the cue change a scene end allows (pacing 4.4); `save_jingle` and `chime` at the save (spec 11 acceptance 5).
Caption, verbatim: `Three replies, each a row of data/meta_bake.json, and a WILL bar that only goes up.`
Caption runs 1:19.60 to 1:23.30.
Claim: "the person judging your line is a Meta model answering inside a NES text box" (ONE-PAGER), carried by the
three rows and the plate, not by the picture alone. The box is spec 05's 240 by 64 window, the reply is the row's
`text` drawn two lines at a time behind the `* ` narration marker, so 28 columns plus 2 is spec 05's 30 (spec 19
section 5). The plate prints the row's own fields: the model on the first reply, then the request hash on replies
two and three (section 4). The arithmetic is the encounter's: WILL 0 to 50 to 85 to 100 on `soften` 50, `nudge` 35
and `setback` 20, clamped to 0 and 100 by `pp_talk_apply`, and three turns is one more than the spare gate needs.
The save is the quay's own: `quay_rest_pier` at (23,35), a `save` trigger in `data/maps/all.json`, written by the
same `pp_save.gml` the title reads at boot.

| t | step | On screen | Input | Music and sound |
| --- | --- | --- | --- | --- |
| 1:18.00 | 4,680 | confirm on `May I see the form?`; the box clears; reply 1 types | confirm | `menu_select`, blips |
| 1:20.00 | 4,800 | reply 1 is whole and held: FORM FIRST. THEN WE TALK. WILL 0 to 50 | none | PP-04 |
| 1:23.40 to 1:27.40 | 5,004 to 5,244 | the bake plate for row `fight/morgan/1`: BAKE MODEL muse-spark-1.3, MODE replay, the row's ROW and SOURCE line, and HASH | none | PP-04 |
| 1:27.40 | 5,244 | confirm closes the reply; the enemy turn, `officer_stamp` or `officer_clipboard` | confirm | `hit` or the pattern's own cue |
| 1:29.00 | 5,340 | the menu; TALK; the panel; confirm on `Lovely handwriting.` | Down, confirm, Down, confirm | `menu_move`, `menu_select` |
| 1:29.40 | 5,364 | reply 2 types: STATE YOUR BUSINESS. WILL 50 to 85 | none | blips |
| 1:31.00 to 1:35.00 | 5,460 to 5,700 | the plate for row `fight/morgan/2`: HASH alone, which is a different hash from the first | none | PP-04 |
| 1:35.00 | 5,700 | confirm; the enemy turn | confirm | the pattern's cue |
| 1:36.40 | 5,784 | TALK; the panel; confirm on `The captain is coming.` | Down, confirm, Down, confirm | `menu_move`, `menu_select` |
| 1:37.00 | 5,820 | reply 3 types: YOU WILL NOT SKIP THIS. WILL 85 to 100 | none | blips |
| 1:38.00 to 1:41.00 | 5,880 to 6,060 | the plate for row 3, `fight/morgan/3`: HASH alone, a third value | none | PP-04 |
| 1:41.00 | 6,060 | confirm; the enemy turn; the SPARE entry turns to the first ink, because trust 4 is at or past `trust_to_spare` 3, and the hint reads HE HAS HAD HIS SAY. SPARE. | confirm | the ready spark |
| 1:42.40 | 6,144 | SPARE taken: `quay_morgan_win_spare`, The cloud leaves his eyes. / Was I shouting? Sorry. / He puts the pen away. | confirm | PP-04, then PP-03 |
| 1:44.00 | 6,240 | back on the quay: `quay_morgan_after_spare` page 1, then page 2 | confirm twice | PP-03 |
| 1:46.00 | 6,360 | the walk south; the bridge tiles do not fire, because `morgan_resolved` is set | hold the walk key | PP-03 |
| 1:47.00 | 6,420 | the pier at (23,35), `quay_rest_pier`: the Saving panel, the chime once, `pp_save_01.json` written | confirm, then confirm | `chime` |
| 1:41.00 to 1:44.00 | 6,060 to 6,240 | a window over the table above, not a step: the network line runs there, over the three receipts just shown (section 5) | none | PP-04 |
| 1:50.00 | 6,600 | cut to Percy, two tiles south east | none | cut |

### S6, Percy, and the one ending the game has, 1:50.00 to 3:00.00 (4,200 steps)

Sub-shots, because the fallbacks in section 2 name them: S6.1 the pages and the encounter, 1:50.00 to 1:59.00 (540
steps); S6.2 the fight, 1:59.00 to 2:14.30 (918 steps); S6.3 the spare and the pages, 2:14.30 to 2:18.00 (222
steps); S6.4 the credits, 2:18.00 to 3:00.00 (2,520 steps). 540, 918, 222 and 2,520 make the shot's 4,200.

Screen: the pier. Percy at (23,37), `quay_percy_encounter`: a face, `thunder_soft`, the flash, three pages of
`quay_percy_pre`, `quay_percy_intro`, and the battle `percy` on its own background, 40 hp, two phases. Then the
spare, `quay_percy_win_spare`, `quay_percy_spare` (the party joins, `save_jingle`), and the credits roll from
`data/credits.json`, variant `spare`, which ends on THE STORM IS OVER and THANK YOU FOR PLAYING.
Input: confirm through four pages before the fight and three after it, FIGHT twice, TALK twice, SPARE once; then no
input until the cut.
Music: PP-06, Percy, Possessed, the encounter's own `music` field; `save_jingle` when the flag is set; PP-15b, Mercy,
the spare variant's own cue (`data/credits.json` `roll.variants.spare.music_cue`), not PP-15a, Entropy, which is the
kill variant's.
Caption, verbatim: `Percy is talked down, the storm ends, the credits name the Meta models; play the build offline from the repo.`
Caption runs 1:53.03 to 1:57.00.
Claim: "the other is won by talking" (ONE-PAGER), and the ending the game now has. Percy can be spared without a
killing blow: `trust_per_talk` 2 against `trust_to_spare` 3 means two TALK turns open SPARE, and the route is not
`genocide`, which is the only thing that would refuse it (`spare_refuses_on_route` in `data/encounters/all.json`).
The fight is worth showing for its shape: 40 hp, a wall at 70 per cent and a fan at 40 per cent, each with its own
pattern and its own talk set. The ending is `quay_percy_spare`'s own `credits` command with `variant: spare`, and the
roll is data: 54 rows, the model names in a section of their own (MUSE SPARK 1.3, MUSE IMAGE 1.0, SAM 3.1) and the
OpenStreetMap ODbL line among the licences, which is the attribution ARRIVAL-CONTENT section 1 requires on any frame
built from that block. The roll's clock is the engine's: 90 steps of lead in, a scroll at 0.5 pixels a step, 300
steps of hold on the last card and 45 of leave, which is 2,575 steps from the first frame of S6.4 to the last.

| t | step | On screen | Input | Music and sound |
| --- | --- | --- | --- | --- |
| 1:50.00 | 6,600 | the pier; Percy at (23,37) faces up as the hero arrives; `thunder_soft`, the flash | confirm | `thunder_soft` |
| 1:50.30 | 6,618 | `quay_percy_pre` page 1: The bridge groans. / Percy stands at its end, / trident up, hair wild. | none | blips |
| 1:52.00 | 6,720 | page 2, Percy: I CALLED THE STORM. / No. It called ME. / STAND BACK. I CANNOT. | confirm | blips |
| 1:55.00 | 6,900 | page 3: This hurricane is his. / Stop him. Bring him back. | confirm | blips |
| 1:57.00 | 7,020 | `quay_percy_intro`: Percy raises the trident. / The sea stands behind him. / Talk him down, or fight. Then the battle frame and the menu | confirm twice | PP-06 from the encounter's `music` |
| 1:59.00 | 7,140 | FIGHT, the timed bar, the hit: 40 hp down to about 30 | confirm, then confirm at the bar | `hit` |
| 2:02.00 | 7,320 | FIGHT again: the bar at 70 per cent fires the wall, `percy_wall`, and the telegraph line PERCY LEVELS THE TRIDENT | confirm twice | `hit`, the phase beat |
| 2:05.00 | 7,500 | TALK: the panel draws `talk_percy`'s three answers, STILL TALKING. NOTED. / THE VEIL. YOUR QUESTION. / PLAINLY. | Down, confirm | `menu_move`, `menu_select` |
| 2:07.00 | 7,620 | the first talk reply; it comes from the card pool, not the bake, and no receipt is drawn here (section 4) | confirm on an answer | blips |
| 2:09.00 | 7,740 | the enemy turn; the menu | none | the pattern's cue |
| 2:11.00 | 7,860 | TALK again; the panel draws the phase's own talk set, THE TIDE TURNS. LOG IT.; trust reaches 4, so SPARE turns to the first ink and the hint reads THE LOG IS CLOSED. SPARE. | Down, confirm, Down, confirm | `menu_move`, `menu_select` |
| 2:13.00 | 7,980 | the second reply; the enemy turn | confirm, none | blips, the pattern's cue |
| 2:14.30 | 8,058 | SPARE: `quay_percy_win_spare`, The sea... is quiet? / Did I do all this? | confirm | PP-06 |
| 2:15.30 | 8,118 | `quay_percy_spare`: `percy_recruited` set, `save_jingle`, and the three pages of `quay_percy_after_spare`, I remember. All of it. / The clouds tear open. / PERCY JOINS THE PARTY! | confirm per page | `save_jingle`, then PP-06 |
| 2:18.00 | 8,280 | the credits: PP-15b, Mercy; 90 steps of lead in, then the roll | none | PP-15b |
| 2:19.50 | 8,370 | the scroll starts, 0.5 pixels a step | none | PP-15b |
| 2:23.77 | 8,626 | PRIMORDIAL PARADOX, A GAME BY NAYILINIST at mid screen | none | PP-15b |
| 2:27.57 | 8,854 | MADE FOR THE META GLOBAL AI DEVELOPER HACKATHON 2026, then CAST | none | PP-15b |
| 2:31.37 | 9,082 | THE META MODELS: MUSE SPARK 1.3 the talk judge, then MUSE IMAGE 1.0 and SAM 3.1 | none | PP-15b |
| 2:36.37 | 9,382 | THE BOTS: one human and a crew of AI agents who drew, wrote, composed, tested and checked | none | PP-15b |
| 2:43.97 | 9,838 | THE NODES, then ALSO THANKS TO: GAMEMAKER LTS2026 and PRESS START 2P | none | PP-15b |
| 2:48.17 | 10,090 | MAP DATA, (c) OPENSTREETMAP CONTRIBUTORS, OPEN DATABASE LICENCE 1.0, openstreetmap.org/copyright | none | PP-15b |
| 2:52.17 | 10,330 | the closing block: THE STORM IS OVER, Percy is himself again, He joins the party | none | PP-15b |
| 2:55.17 | 10,510 | THANK YOU FOR PLAYING at mid screen; the scroll ends after 2,140 steps and the 300 step hold begins | none | PP-15b |
| 3:00.00 | 10,800 | last frame: the closing card, 290 steps into its 300 step hold | none | end |

---

## 4. The Meta shot, and the fields the frame prints

The bake is the architecture, not a nicety: the shipped build holds no key and makes no call (D5,
`specs/19-llm-talk.md` section 2). So the evidence that a model was in the loop is the row, and the row is printed
where the row answers.

The quay build has one such place, not two. S5's three TALK replies are rows of `data/meta_bake.json` at
`fight/morgan/1`, `fight/morgan/2` and `fight/morgan/3`: the encounter `morgan_gate` carries a `talk` block whose
`card` is `morgan`, and `pp_talk_bake_key` builds the row key from the card and the enemy phase, so the fight reads
the bake. The old cut's second receipt shot sat on the deck watch, whose `fight/navy_sailor/1` to `3` rows are still
live in the file; that scene is not on the route, so its rows are not printed here. Percy's fight reads no bake at
all: the file holds `fight/percy/1` to `3` and `fight/percy_phase2/1` to `3`, all six `fallback`, but a fight row is
only read when `pp_talk_bake_key` can name a card, and `percy`'s encounter carries no `talk` block, so those six rows
are never reached and the card pool answers. That is why his two talk replies are on screen with no plate over them
and no claim made about them.

| Shot | The line on screen | The row behind it | The field the overlay prints | Why that field |
| --- | --- | --- | --- | --- |
| S5, reply 1, 1:23.4 to 1:27.4 | the box, turn 1, over `May I see the form?` | `fight/morgan/1` | `model` and `request_hash`, read out of `data/meta_bake.json` at draw time | `model` names the model that answered, `request_hash` names the exact assembled request, so the printed pair cannot be a hand typed line |
| S5, reply 2, 1:31.0 to 1:35.0 | the box, turn 2, over `Lovely handwriting.` | `fight/morgan/2` | `request_hash` alone | a second, different hash proves a second call at a different scene state, not one line reused |
| S5, reply 3, 1:38.0 to 1:41.0 | the box, turn 3, over `The captain is coming.` | `fight/morgan/3` | `request_hash` alone | the third value completes the proof that three turns were three requests |

Rules for the plates, so the builder can draw them without asking:
1. The text is read from the file at edit time, never typed. A row that is missing means the shot is not recordable
   and the booth stops, which is better than a receipt that lies.
2. The plate is drawn as a caption under the frame or beside it, never inside the 256 by 240 area. The frame stays
   the game's own pixels.
3. `created_at` and the shadowed fallback are in the row by D5, and neither is printed on screen. If a third line is
   wanted later, `created_at` is the one to add.
4. The three rows are `source: "fallback"` in `data/meta_bake.json` today, in both the working copy and the shipped
   copy, while 11 of the file's 21 rows are live. `tools/demo_overlay.py` refuses to print a fallback row as a
   receipt, which is the right refusal: the line in the box would be the bake's hand written fallback and the plate
   would be claiming a model wrote it. Q1 carries what that needs.

---

## 5. The one shot with the network line

The network is dead for the whole recording, not for one shot: the adapter is disabled before the first frame at
0:00.00 and stays down for all 180.00 s, so nothing anywhere in the cut could have been a call. The line that says so
runs on S5, from 1:41.00 to 1:44.00, in the four seconds after the third receipt and before the spare: the replies it
speaks about are the three that were just on screen.

The two lines are `tools/demo_overlay.py`'s own, chosen from the bake's flags and not typed by hand: NETWORK DEAD
SINCE THE FIRST FRAME. / THESE REPLIES CAME FROM data/meta_bake.json. If the bake ever records a live run, the same
drawing prints the live pair instead, because a line that always says dead is not evidence either.

| What the frame shows | What backs it |
| --- | --- |
| three TALK replies played on a machine with no network | each is a row of `data/meta_bake.json` (section 4); the replay is a file read, not a call (spec 19 section 2) |
| the badge and the line, drawn from the file's own flags | `data/meta_bake.json` `bake.network` is `false` and `bake.offline` is `true`, and `network_lines` picks the words from those two fields |
| the run continuing through the spare, the walk, the pier save, Percy and the credits with the network still dead | `tests/test_no_network_in_build.py` (R34), which asserts that nothing under `game/` carries a URL, an `http` or a key name |

What this shot does not claim: it does not claim the card pool rung (spec 19 section 8 rung 2), which answers a line
the bake does not cover. S6's two talk replies are that rung, and no plate is drawn over them. Saying so is part of
the claim being honest.

---

## 6. The route, step by step, and where each step lives

Every step of `data/slice.json` `route.steps` appears exactly once, in this order. A step that spans two shots says
so in its own row.

| Route step (`data/slice.json`) | Shot | In data today | The card that lands it |
| --- | --- | --- | --- |
| `title`, the title screen | S1 | `rm_pp_title`, `data/title.json`, `data/title_flash.json`, `data/title_timing.json` | nothing; it is in the build |
| `crawl`, the intro crawl | S2 | `data/intro_text.json`, 6 beats and 16 rows; the reveal machine measured at 1,238 steps (spec 14 addendum) | nothing; it is in the build |
| `quay`, the Town Quay in the hurricane | S3, and S4's first beat | map `southampton_town_quay`, scene `quay_arrival`, `pp_storm.gml`, and the map's 17 `say` triggers, which draw on seven `say_door_*` pages | nothing; it is in the build |
| `morgan`, talk or fight | S4 (the pages and the panel) and S5 (the three replies, the spare, the pages, the save) | scene `quay_morgan_encounter`, encounter `morgan_gate`, `quay_morgan_pre`, `quay_morgan_intro`, `quay_morgan_win_spare`, `quay_morgan_after_spare`, `talk_morgan`, the bake rows `fight/morgan/1` to `3` | nothing for the scene; a live re-bake for the receipts (Q1) |
| `percy`, talk or fight, then the credits | S6 | scene `quay_percy_encounter`, encounter `percy`, `quay_percy_pre`, `quay_percy_intro`, `quay_percy_win_spare`, `quay_percy_after_spare`, `talk_percy`, `data/credits.json` | nothing; it is in the build |

No step outside that list appears in this script. The drive, the gate checkpoint, the dock office, the boarding
pass, the ship, the deck hound and the deck watch are not on the route and are not in the demo; section 11 lists
what was in the 2026-10-22 draft and what replaced it.

---

## 7. The booth sheet

Keys in the order they are pressed, in the vocabulary `data/demo/run_001.json` already uses (`enter`, `confirm`,
`up`, `down`, `left`, `right`), with the absolute step each one lands on. A held key is written as `confirm hold`
with the step it is released at. This is the list the builder turns into the recorder's events; nothing here is
decided at the desk.

| Step | Key | Where the run is | Why |
| --- | --- | --- | --- |
| 0 | none | attract | the recording starts, no key until the flash has played |
| 708 | enter | title, PRESS Z OR ENTER | opens the menu |
| 852 | enter | menu, cursor on NEW GAME | NEW GAME |
| 1,320 | confirm hold to 1,620 | crawl, beat 2 ends | 3x reveal through beats 3 and 4 |
| 1,620 | release | crawl, beat 5 typing | the last beat reads at 1x |
| 1,764 to 1,920 | down, held | the quay, from (24,1) south | the arrival walk |
| 1,920 | confirm | the Red Funnel door row | opens `say_door_red_funnel` |
| 1,992 | confirm | the door page | closes it |
| 2,004 to 2,340 | down, held | the quay, south | the walk to the bridge mouth |
| 2,364 | none | (23,32) | the wind fires on touch, no key |
| 2,484 | confirm | the wind page | closes it |
| 2,520 to 2,700 | left, then up, held in turns | the quay, west and north | the walk to the tower |
| 2,700 | confirm | `quay_rest_tower` save | the panel opens |
| 2,760 | confirm | the Saving panel | the save writes, the chime once |
| 2,800 to 3,060 | up, then right, held in turns | the quay, north east | the walk to Morgan's corner |
| 3,060 | confirm | Morgan at (6,9) | enters `quay_morgan_encounter` |
| 3,210 | confirm | page 1 | advance |
| 3,390 | confirm | page 2 | advance |
| 3,540 | confirm | page 3 | advance |
| 3,600 | confirm | `quay_morgan_intro` | the battle opens |
| 3,720 | down, then confirm | the battle menu | TALK; the panel opens at 3,780 |
| 3,780 to 3,960 | down, down, down, up, up, up | the TALK panel | the cursor reads the three answers |
| 4,680 | confirm | `May I see the form?` | reply 1, WILL 50 |
| 5,244 | confirm | reply 1 | closes it |
| 5,280 | down, then confirm | the menu, then TALK | the panel |
| 5,340 | down, confirm | `Lovely handwriting.` | reply 2, WILL 85 |
| 5,700 | confirm | reply 2 | closes it |
| 5,760 | down, then confirm, then down, confirm | the menu, TALK, the panel | `The captain is coming.` |
| 6,060 | confirm | reply 3 | closes it, WILL 100 |
| 6,090 | down, then confirm | the menu | SPARE, which is now in the first ink |
| 6,144 | confirm | `quay_morgan_win_spare` | advance |
| 6,240 | confirm, then confirm | `quay_morgan_after_spare` pages 1 and 2 | advance |
| 6,300 to 6,360 | down, held | the quay, south | the bridge is open |
| 6,420 | confirm | `quay_rest_pier` save | the panel opens |
| 6,480 | confirm | the Saving panel | the save writes, the chime once |
| 6,660 | confirm | Percy at (23,37) | enters `quay_percy_encounter` |
| 6,720 | confirm | page 1 | advance |
| 6,900 | confirm | page 2 | advance |
| 7,020 | confirm, then confirm | page 3, then `quay_percy_intro` | the battle opens |
| 7,140 | confirm, then confirm at the bar | the menu, FIGHT | the blow lands |
| 7,320 | confirm, then confirm at the bar | the menu, FIGHT | the wall phase fires |
| 7,500 | down, then confirm, then down, confirm | the menu, TALK, the panel, an answer | the first talk |
| 7,740 | none | the reply and the enemy turn | no key |
| 7,860 | down, then confirm, then down, confirm | the menu, TALK, the panel, an answer | the second talk, trust 4 |
| 8,010 | down, then confirm | the menu | SPARE |
| 8,058 | confirm | `quay_percy_win_spare` | advance |
| 8,118 | confirm, then confirm, then confirm | `quay_percy_after_spare` pages 1 to 3 | the party joins |
| 8,280 | none | the credits | no key until the cut |

---

## 8. What this script leaves out, on purpose

- The drive, the gate checkpoint, the dock office, the boarding pass, the ship and its two fights. None of them is
  on the route any more; the ruling's section 4 forbids rebuilding them to make an old shot table filmable.
- Percy's kill path. The demo spares him, because the story's through line is the talk, and because the spare
  ending is the one that names the party. The kill ending exists, is 24 steps shorter, and is Q3.
- Percy's second phase and his fan. The demo lands him in the wall and stops fighting there; the cut would need
  another twenty seconds of battle to reach 40 per cent, and twenty seconds is the credits.
- The free typed line. SAY IT YOURSELF is drawn on the panel and the demo never takes it: `data/talk_live_tape.json`
  holds recordings for the navy sailor only, so a typed line to Morgan or Percy would be answered by the card pool
  or the fallback, and the demo would be showing a rung it then has to explain.
- The card pool and the encounter fallback. They are real (spec 19 section 8 rungs 2 and 3) and no receipt is
  claimed for them here.
- Any number the build cannot print. The receipts are read from the file at edit time; the game over carries no
  statistic; the save shows no counter.

---

## 9. Q: for gamedev, four items, and three notes

1. **Q1, the receipts have no live row.** `fight/morgan/1`, `/2` and `/3` are `source: "fallback"` in
   `data/meta_bake.json`, in the working copy and in `game/datafiles/meta_bake.json` alike, while 11 of the file's
   21 rows are live. So `tools/demo_overlay.py` refuses the plate for the three replies, correctly: the line in the
   box is the bake's hand written fallback, not an answer. The shot is therefore not recordable with a receipt
   until the bake holds a live answer for Morgan's three rows, which is a re-bake (`tools/bake_meta.py` against the
   loopback bridge) and a data card, not a script change. Until then S5 keeps its caption and its box and draws no
   plate, and the demo's claim rests on the box and on the file's own counts, which is weaker than the write-up
   says. Gamedev to say whether the re-bake is carded before the judged take.
2. **Q2, the plate, the network window and the clock pin are the old cut's.** `tools/demo_overlay.py` `SHOT_ROWS`
   still names `npc/nye/turn_1` for S5 and the three `fight/navy_sailor` rows for S6; `SHOT_WINDOWS` gives S5 one
   bake window (83.40 to 87.40), S6 three (135.03, 138.53, 143.53) and S6 the network line (154.40 to 158.40);
   `tools/demo_cut_180.py` `PLATE_WINDOWS` still places a plate on S6. This script has one plate shot, S5, with three
   rows at 83.40 to 87.40, 91.00 to 95.00 and 98.00 to 101.00, and the network line on S5 at 101.00 to 104.00. Those
   tables and `tests/test_demo_overlay.py`'s clock test, which pins the old S6 receipt clocks and the S6 network
   window, follow this file and are the builder's card t_892cc851's to move. That test is the one check this file
   cannot make green from here, and it goes red for the right reason: the script moved and the tool has not.
3. **Q3, the credits ending.** S6 ends on the `spare` variant of `quay_percy_spare`'s `credits` command, because
   the demo has just spared both men and the spare closing block is the one that names the party. The `kill`
   variant is real, is 24 steps shorter, and is not shown. If the panel wants both endings in one cut, that is a
   second cut, not a longer S6.
4. **Q4, the WILL numbers.** The three answers earn 50, 35 and 20 through the encounter's `talk_mercy` table, not
   20 each from `mercy_per_option`, and the spare gate is trust 3 (two TALK turns at 2 each), not the 60 that
   `mercy_to_spare` names: no GML file reads that field. This script prints what the game draws. If the 60 was meant
   to be the gate, that is a data or a director question, and it moves no second here.

Notes, not questions:

- **N1, the attribution line.** The frames from S3 to S6 are built from the OpenStreetMap extract, and
  ARRIVAL-CONTENT section 1 requires the ODbL line on any screenshot or credit built from that block. The credits
  roll already carries it, MAP DATA, `(c) OPENSTREETMAP CONTRIBUTORS`, `OPEN DATABASE LICENCE 1.0`,
  `openstreetmap.org/copyright`, so the demo's last second satisfies the requirement without a separate card.
- **N2, the recorder.** `tools/play_demo.py` reads a table by name from `data/demo/shot_table.json`, and its `full`
  table is still the retired ten step take: 253.5 s, with S3 the drive, S4 the gate and its three options, S5 the
  office and the boarding, and S6 the deck watch, the log and Percy's office fight. The recorder is the furthest
  behind of the three instruments this file touches, and the builder's card is where all three are brought back into
  line with the six lengths above.
- **N3, the entry autosave.** `pp_save.gml` writes a silent save once per map entry, after the fade in. The demo
  enters the quay once, at S3, so a `pp_save_01.json` exists by S4 and CONTINUE is lit from the first fight on.
  The two visible saves in S4 and S5 are the panel the player confirms, and they are what the demo shows.

---

## 10. The checks, and how each is met

| The card's check | How this file meets it |
| --- | --- |
| the total runs 170 to 190 seconds | 180.00 s exactly, 10,800 steps: 16, 13, 10, 39, 32 and 70, printed per shot in section 1 and recomputed in section 2 |
| every step of the slice route appears | the five rows of section 6 are `data/slice.json`'s own steps, in order, each mapped to the shot or shots that carry it |
| each shot names its input and its claim | every shot heading carries a `Screen`, `Input`, `Music`, `Caption` and `Claim` line, and every beat row carries the input that lands on it |
| the Meta shot names the bake receipt field the frame shows | section 4 names `model` on the first reply and `request_hash` on replies two and three, all read from `data/meta_bake.json` at draw time |
| no dash characters | scanned for U+2012, U+2013, U+2014 and U+2015 after writing: zero |
| a re-read against `data/slice.json` names no step the route does not carry | passes: five steps, and every map, scene, encounter, dialogue id and bake row in sections 3 to 7 belongs to one of them |

Written by research-assistant, 2026-10-22, rewritten 2026-11-12. Nothing here was run in the engine: this file plans
the recording, and the recording is where each row is proved or corrected.

---

## 11. What the rewrite changed, and what it could not

The 2026-10-22 draft was written against a ten step route that the author's scope cut on 2026-11-03
(`28d407a2`). The ruling's section 2 is the evidence, and this is the table of what it cost.

| The draft's shot | What it named | Why it could not stay | What replaced it |
| --- | --- | --- | --- |
| S3, the drive | `drive_to_southampton`, the drive list's shot 3, a gantry sign counting down | no route step names the drive, no map trigger leads into `drive_m4_corridor`, and no capture of a drive exists in the repository | the hurricane arrival on `southampton_town_quay`, scene `quay_arrival`, the storm's own seeded clock, and the street's door pages |
| S4, the gate checkpoint | `quay_gate_checkpoint`, a barrier arm, three labels and a flag each | the scene has zero hits in the source data and in the GML; every hit is under `output/`, `build/` or a retired copy | the wind at the bridge, which is the gate the build has, and Morgan's three answers, which is the choice it has |
| S5, the office and the boarding | `quay_dock_office_play`, a boarding pass, the gangway and `ship_boarding` | the office and the ship exist as data and nothing reaches them: the office's only map trigger leads out, and no trigger on the quay leads in | the three TALK replies, their bake rows, the spare, and the quay's own pier save |
| S6, the ship's fights and the log | the deck hound, the deck watch, the ship's log save, a forced defeat | the ship is off the route, and a demo that ends on a save shows neither ending the game has | Percy, the spare, and the credits, whose last card is THANK YOU FOR PLAYING |
| the two Meta shots | an `npc` row at the dock office and three fight rows on the deck | both scenes are off the route | one shot, S5, with three rows from the fight that is on it (Q1, Q2) |
