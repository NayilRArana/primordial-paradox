# DEMO-AUTHORITY-RULING, 2026-11-12: the build decides what is on screen, the script decides only the shape

Card t_6e10768e, gamedev. The question came from card t_55f52304 (builder, judge panel 2026-11-12 fix 3) and is
written out in `knowledge/DEMO-CUT-180-2026-11-11.md` section 5.

The question, in its own words: which is the authority for what the demo shows, `knowledge/DEMO-SCRIPT.md` (2026-10-22,
six shots with the drive, the gate checkpoint, the dock office and the boarding) or the story the build has since
commit `28d407a2` (title, crawl, hurricane Town Quay, Captain Morgan, Percy, two credits endings)?

## 1. The ruling

`knowledge/DEMO-SCRIPT.md` is not the authority for what the demo shows. The authority for content is the route the
build walks, `data/slice.json` as committed at `28d407a2` under the author's scope
`..\arananet\manager\FINAL-SCOPE-2026-11-03.md`: title, crawl, the hurricane Town Quay, Captain Morgan, Percy, the
credits.

The script keeps authority over the demo's form: the total length, six shots, one caption and one claim per shot, the
receipts read out of `data/meta_bake.json` at edit time. It has no authority over which scenes exist. Where it names a
scene the build does not carry, the build wins and the script's row is what changes.

Consequence, stated as an order: S3 (the drive), S4 (the gate checkpoint) and S5 (the dock office, the boarding pass,
the boarding) are rewritten to scenes that exist and are reachable, with new captions, by whoever owns the script
(research-assistant, card created by this card). The drive, the office and the boarding are not rebuilt.

## 2. Why, in six checkable facts

| # | The fact | Measured where | What it settles |
| --- | --- | --- | --- |
| 1 | The route is five steps: `title, crawl, quay, morgan, percy` | `data/slice.json` `route.steps`, and the shipped copy `game/datafiles/slice.json` carries the same five in the same order | a player's run has no drive, no gate checkpoint, no office, no ship |
| 2 | The gate checkpoint does not exist | `quay_gate_checkpoint` has zero hits in `data/dialogue/all.json`, `data/scenes/all.json`, `data/maps/all.json`, `game/scripts/` and `game/objects/`; every hit is under `output/`, `build/` or a copy of retired data | S4 as written cannot be filmed now, and no amount of polish makes it filmable |
| 3 | The other two exist as data and nothing reaches them | scenes `drive_to_southampton` (`data/scenes/all.json:493`), `ship_boarding` (`:245`), `quay_dock_office_play` (`:840`); maps `drive_m4_corridor` (`data/maps/all.json:804`), `quay_dock_office` (`:703`), `ship_small` (`:7`); the office's only map trigger leads out to the quay (`:769`) and no trigger on the quay leads in; the corridor's one trigger also leads to the quay (`:911`) | a capture of them is a capture of a room no player can reach, which is not evidence about the game |
| 4 | The script's own authority list is upstream of it | `knowledge/DEMO-SCRIPT.md:11-20` names the roadmap, PLAN-WIN, the beat sheet, the drive shot list, ARRIVAL-CONTENT and specs 05, 07, 11, 14 and 19 as the sources it was read from | a plan cannot outrank its own sources; when they move, the plan is what goes stale |
| 5 | Those sources moved | `ROADMAP-2026-10-23.md` section 0 is the pre-cut route, written for an Oct 25 done state and a Nov 4 submission; `28d407a2` executed FINAL-SCOPE-2026-11-03 and its own message says the old drive, gate, office, boarding and ship route is removed from the slice | S3, S4 and S5 were already stale by the script's own rule the day the scope landed |
| 6 | The repo's gates moved with the build, not with the script | `tests/test_demo_shots.py:126, :191, :451, :556, :674` carry `RETIRED by FLOW 2026-11-03` on the old route pins; `tests/test_quay_flow.py` pins the five step chain | the tree's own red and green lines already answer for the quay story |

One more, which is about the script's length rather than its content: the recorder does not play the script's lengths.
`tools/play_demo.py:194` defaults to `data/demo/run_002.json` and `:198` reads `data/demo/shot_table.json`, whose first
table is 253.50 s (`data/demo/shot_table.json:16`), not 180.00. The six lengths and six captions bind the cut tool
(`tools/demo_cut_180.py`) and the judge tooling. They do not bind the game. That is a second reason the script cannot
be the authority on content: it is not even the table the recorder walks.

## 3. What the quay only build can prove, shot by shot

This is the inventory the rewrite needs. Every id below is in the tree or on the route today.

| Shot | The script's scene | What the route has now | The claim that survives | What the rewrite must do |
| --- | --- | --- | --- | --- |
| S1 | title attract, `rm_pp_title` | route step `title`, yes | unchanged, works and obeys hardware limits | keep as written |
| S2 | the crawl, `intro_text` | route step `crawl`, yes | unchanged | keep as written |
| S3 | the drive, `drive_to_southampton`, off route, no capture anywhere | the quay arrival: route step `quay`, scene `quay_arrival` on `southampton_town_quay`, the hurricane overlay `pp_storm` | the drive claim dies, there is no drive. A street claim lives: the real block, the storm, the walk | rewrite scene and caption. S3's 602 steps exist only because the drive list cuts on 86 step bars (`knowledge/DEMO-SCRIPT.md:44-46`), so once the drive is gone the length is free |
| S4 | the gate checkpoint and its three option choice, `quay_gate_checkpoint`, absent | `morgan_gate`: three TALK options, `option_count` 3, `mercy_per_option` 20, `mercy_to_spare` 60 (`data/encounters/all.json:191-193`), entered by talking to Morgan at (6,9) (`data/maps/all.json:676-685`) | three answers, three flags, no failure state, all of that is intact. "The barrier lifts" is not: there is no barrier | rewrite to Morgan. Keep the choice and the no-failure claim, drop the barrier |
| S5 | the dock office, the boarding pass, the boarding | Morgan's talk pages (`talk_morgan`, `data/talk_cards.json` id `morgan`) and Percy's, with the bake row drawn by `tools/demo_overlay.py` | the Meta model inside a NES text box claim survives. The boarding pass claim dies, there is no pass | rewrite to a talk shot. The bake row fields do not move: `model` on the first reply, `request_hash` on replies two and three |
| S6 | deck hound, deck watch, ship's log save, forced defeat | `morgan_gate` (PP-04) then `percy` (PP-06, `data/encounters/all.json:138-150`); saves at `quay_rest_pier` (23,35) and `quay_rest_tower` (5,30) (`data/maps/all.json:660`, `:668`) plus the entry autosave (`game/scripts/pp_save/pp_save.gml:26-27`); both fights carry `lose_dialogue` `battle_lose` (`:150`, `:176`); the story ends on a `credits` command in `quay_percy_spare` (`data/scenes/all.json:210`) and `quay_percy_kill` (`:236`) | the two fights and the save survive. A game over survives only through a fight the player can lose. The credits are the ending the game now has and the script has no shot for | rewrite S6 around Morgan and Percy, the quay save, and one credits ending. A 180 s cut that stops at a save shows neither ending the game actually has |

That last line is the finding the cut note did not have: the quay only story ends in one of two credits endings, and
the six shot table ends on a game over and a load. A rewrite that only swaps S3, S4 and S5 still ends the demo before
the game's own ending.

## 4. What must not happen

1. **Do not build the drive, the office or the boarding to make the old shot table filmable.** The author's scope
   removed them. A demo does not put retired scenes back into the game; that inverts the whole chain. If Nayil wants
   the drive back, it is a new scope decision and a new card with its own review, not a demo requirement.
2. **Do not re-caption a quay scene with drive words.** The two mismatched captions in the 2026-11-11 cut are recorded
   as a mismatch and should not be repeated in a better cut. A caption names the thing under it.
3. **Do not delete the orphan data.** `drive_to_southampton`, `ship_boarding`, `quay_dock_office_play`,
   `drive_m4_corridor`, `quay_dock_office` and `ship_small` stay where they are. Nothing reads them wrongly, the pins
   hold that nothing starts them, and removing a map is its own card with its own review.

## 5. The constraints the rewrite inherits

- **Six sections, six captions, in the shape the readers parse.** A `### S1,` to `### S6,` heading, and inside each
  section one line starting `Caption, verbatim:` with the caption in backticks. `tools/demo_overlay.py:320`
  (`shot_caption`) finds the heading and then that line, and `tools/check_copy_tells.py:229-235` runs the humanizer
  pass over the six it reads that way. A reworded heading or an unbackticked caption stops both tools.
- **No U+2012, U+2013, U+2014 or U+2015 anywhere.** `shot_caption` refuses a caption that carries one.
- **The first caption opens on something concrete and the last carries the call to action,** because
  `check_copy_tells` applies the story rule to the set (`tools/check_copy_tells.py:25-26`).
- **The total is re-timed by whoever authors the script.** 180.00 s stays legal only while the six lengths add to it,
  and `tools/demo_cut_180.py` refuses a table whose ten rows do not add to its own total. If S3's 602 steps go, they
  are replaced by a length that shot earns, not by a borrowed 10.03.
- **The two receipts stay exactly as they are.** Nothing about changing which scene is on screen moves `model` or
  `request_hash`, and both are still read from `data/meta_bake.json` at draw time.

## 6. What this lane fixes, and what it does not

**Fixed here.** `specs/20-demo-route.md` still carried the ten step drive, gate, office, boarding chain as "the demo's
chain, as the file stands". It was written 2026-10-26, eight days before the scope cut, and it is this lane's file, so
it now carries a dated supersession section naming the five step chain and saying which of its decisions the cut
retired. A spec that documents a route the data no longer has is the same defect the question was asking about, one
layer up.

**Not this lane's.** The rewrite of `knowledge/DEMO-SCRIPT.md` and its six captions (research-assistant, card created
by this card), and the rebuild of the 180 s picture from the rewritten script (builder, child card of that rewrite).
Captions belong to whoever authors the script. This lane does not write them.

## 7. The checks run on this ruling

| Check | How | Result |
| --- | --- | --- |
| the gate checkpoint is absent from the build | `quay_gate_checkpoint` grepped across `data/` and `game/scripts`, `game/objects` | zero hits in source data and GML; the only hits are `output/`, `build/` and retired data copies |
| the route is five steps in the shipped copy too | `data/slice.json` and `game/datafiles/slice.json` read | both: title, crawl, quay, morgan, percy |
| nothing leads into the office or the ship from the quay | every `"kind": "map"` trigger in `data/maps/all.json` listed (lines 148, 157, 166, 276, 769, 911) | none names `quay_dock_office` or `ship_small` from the quay; the office and corridor triggers lead out to the quay |
| the cut is what removed the old route | `git show 28d407a2 -- data/slice.json` | ten steps replaced by five |
| spec 20 predates the cut | `git log -- specs/20-demo-route.md` | last touched `c6ea556e`, 2026-10-26 |
| the recorder's table is not the script's table | `tools/play_demo.py:194`, `:198`; `data/demo/shot_table.json:16` | default script `run_002.json`, table total 253.50 s against the script's 180.00 s |

Written by gamedev, 2026-11-12. Every id and line number above was read in the tree on this date. Nothing here was
played in the engine: this file rules which document governs, and the recording is where the rewritten rows are
proved or corrected.
