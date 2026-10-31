# Review: the arrival data, the hub map and the gate scene

Card t_6cd706d0 (R18, step S4 of ROADMAP-2026-10-22.md). Lane: code-review. Written 2026-10-24. I edited nothing:
this file is the only file this card writes. The map, scene and dialogue data belong to the builder lane and to
R22 DIALOGUE-V2.

**Verdict: FAIL.** Seven changes are required, in section 8. The data passes both project checkers and still sends the
player through a gate that is not there, past a second conversation that does not exist, on a walk that is 5 tiles
long, over a harbour drawn as brick, on a map whose pier cannot be reached on foot.

## 1. The bytes reviewed

| File | Rows read |
| --- | --- |
| `data/maps/all.json` | `southampton_town_quay`, `quay_dock_office` |
| `data/scenes/all.json` | `quay_gate_checkpoint`, `quay_gate_truth`, `quay_gate_bluff`, `quay_gate_authority`, `quay_yard_walk`, `quay_dock_office_play` |
| `data/dialogue/all.json` | `quay_gate_checkpoint`, `quay_gate_choice`, the three replies, `quay_dock_office`, `quay_dock_office_pass`, the seven `say_door_` lines |
| `data/flags.json` | the arrival's five flags (D3) |
| `data/maps/osm/southampton_town_quay.json` | the draft raster, read only to name each tile's class |

Read as a reader, not as data: `knowledge/ARRIVAL-CONTENT.md`, `specs/04`, `specs/05`, `specs/06`, `specs/11`,
`knowledge/mechanics/PACING-AND-CUTSCENES.md` sections 5 and 6, `knowledge/GAMEDEV-DECISIONS-2026-10-22.md` D1 to D5,
and the S4 check line in `ROADMAP-2026-10-22.md`.

The reviewed bytes are the committed bytes: `git status --porcelain` and `git diff --stat HEAD` are both empty for the
map, scene, dialogue and flag files, so no working copy is hiding a fix.

    sha256  data/maps/all.json      8f5df49b72e6b1ffbaa396455282ffcc1bc8c6e30973b07ffd6f933a1b9d4534
    sha256  data/scenes/all.json    78390c43b363fa597a3fdbdc677c32652df03c669a8fc80d5ff5d4a5cadef99d
    sha256  data/dialogue/all.json  23bf6cbd6a86bfe9126b2bcd05d428f78c4bf70f51ce3b5df328340db519e054

The built copies are in step with the source copies, md5 for md5, so what the game would load is what I reviewed:
`data/maps/all.json` and `game/datafiles/maps/all.json` are both `58e4d9dd7c3d15dc060228af3de35ed2`; the scene pair
`522708a820c2a68c73b4f22b4bb9169a`; the dialogue pair `e66053c04682cfd861edc7253c69bcf0`.

## 2. The two checks, with the exit codes they really returned

    $ python tools/check_data.py
    check_data: all files pass
    exit 0

    $ python tools/check_cleanroom.py
    check_cleanroom: 365 files scanned for 26 names and 12 phrases, 40 GML modules, 0 awaiting review,
      6 downloaded map file(s) skipped, 242 OSM place name(s) exempt in 2 generated geography card(s)
    OSM place names exempt from the foreign name pass: game/datafiles/maps/real_places.json (121 name(s))
    OSM place names exempt from the foreign name pass: data/maps/real_places.json (121 name(s))
    check_cleanroom: no study reference, no foreign name, no foreign phrase, every module reviewed
    exit 0

Both are green, and nine findings below stand anyway, so it is worth saying exactly what the green does not cover.
`tools/check_data.py` (lines 1387 to 1414) walks the trigger list and checks bounds, `kind`, `id`, `once` and
`condition`, and it never asks whether the trigger's own tile is walkable. Its one story flag test (line 1368) passes
if `2` appears anywhere in the collision grid, so a single invisible tile satisfies the gate. It has no reachability
test, no marker spacing test, and no test of what a tile draws with. `tools/check_cleanroom.py` is a text blacklist
plus a review ledger; the arrival rows are clean against it and were never the risk.

Every number below that is not quoted from a spec came from my own probe scripts, run against these files in a cold
process: `probe_arrival.py`, `probe_arrival2.py`, `probe_arrival3.py` and `probe_arrival4.py`, in this card's
workspace. They read the four files above and write nothing.

## 3. The three questions, in numbers

**How many screens.** `southampton_town_quay` is 53 by 56 tiles at 16 px, which is 3.31 by 3.73 screens of the 16 by
15 tile frame spec 04 draws. That is 38 by 42 = 1596 distinct scroll windows, and 12.37 screenfuls of area. It stays
inside the roadmap's "hub under 4 screens across" line at 3.31 across. The interior `quay_dock_office` is 20 by 15,
1.25 screens across, so it scrolls 5 columns.

Of the 2968 tiles, 1701 are collision class 0 (1693 floor tiles plus the 8 walkable door tiles), 1 is class 2 (the
story blocked tile), and 1266 are class 1. Of the 1701 walkable tiles, **1397 are reachable from the entry spawn
(11,1), which is 82.1 percent**, and they sit in **13 disconnected components**. The content file's "1706 of 2968
walkable" is 5 tiles too high; 1706 is every tile that is not a wall, which counts the story blocked tile and the four
blocked doors as if they were walkable.

**How many markers.** One. `southampton_town_quay` carries 1 marker trigger, `deck_hound` at (23,14), marked
`marker_kind: story`, and 0 wild markers, and the map says `encounters: "scripted"`. Under D1 of the gamedev decisions
that is conformant: a story marker's authored count wins, and the "1 per 40 to 60 walkable tiles" figure is about wild
markers only. The roadmap's S4 check line ("1 marker per 40 to 60 walkable tiles") is therefore the wrong yardstick
against this block and would ask for 28 to 43 markers. It should be rewritten to read D1, as the D1 ruling itself says
for the test card.

**How many seconds of walking, entry to the first marker.** **5.8 seconds.** The entry is the `start` spawn at (11,1)
and the marker is at (23,14). Breadth first search over the shipped collision grid, with the story blocked tile
treated as blocked, gives a shortest walkable path of 29 tiles; the Manhattan floor is 25. At spec 04's free walk of 12
steps a tile and 60 steps a second, 29 tiles is 5.8 s and the floor is 5.0 s. Two reference distances from the same
search: the first scene trigger (8,10) is 12 tiles, 2.4 s, and the office door (18,25) is 33 tiles, 6.6 s.

## 4. Findings

Each finding names the map or scene id, and the tile row or command index it is about.

### F1. The gate is a single invisible tile, and the scene plays after the player has walked past it (blocker)

`southampton_town_quay`, row 9. Collision class 2 exists on exactly one tile, (8,9); its art character is `.` (floor),
so nothing is drawn there. Its neighbours (7,9) and (9,9) are class 0, and so are (7,8), (8,8), (9,8) and (7,10),
(8,10), (9,10). The road at row 9 is open from x 5 to x 11 and only x 8 collides.

Three consequences, all player visible:

1. Walking south down the centreline of the road, the player is stopped by a wall that is not drawn, on a tile that
   looks exactly like the ground on both sides.
2. Walking one tile east or west of the centreline, the player passes the gate without a check. The gate scene trigger
   is `triggers[8]` at (8,10), which is one row *south* of the barrier and 12 tiles from the entry spawn, and the
   shortest path from the entry to it is monotone (12 tiles equals the Manhattan distance), so it is reached without
   ever touching (8,9). The checkpoint conversation therefore plays after the line has been crossed, from the wrong
   side of it.
3. `quay_gate_checkpoint`, command 1 and 2, play the lines "Rain on the barrier arm" and "No pass, no gate" while the
   barrier arm is drawn by nothing. The quay tile sheet has a barrier character ready for it: `pp_map_tile.gml` row
   `{ ch: "b", gid: 9, plane: PP_TILE_PLANE_PROPS }`, and the map uses none of the 20 characters it offers except `.`,
   `#` and `D`.

The content file is specific and the data does not follow it: ARRIVAL-CONTENT 4.1 says the barrier is drawn across
(7,9) to (9,9) and that Morgan stands on (8,9). The data puts `morgan` at (10,9), a walkable road tile two tiles east
of the blocked one, so the guard stands on the far side of his own gate, in the open.

### F2. Morgan's second conversation does not exist, so the choice has no echo (blocker)

ARRIVAL-CONTENT answers one of the card's two questions with Morgan, "the person you can talk to twice". The data
delivers one talk.

- No `morgan_again` dialogue id exists in `data/dialogue/all.json`, and no trigger fires one. The tile the content
  reserves for it, (8,10), holds the gate scene trigger instead.
- `quay_gate_choice` sets `gate_passed` plus one of `gate_truth`, `gate_bluff`, `gate_authority` (choices 0, 1, 2),
  and those three flags are then read by nothing that reaches the screen. The only readers are
  `quay_gate_checkpoint` commands 3, 4 and 5, which branch to `quay_gate_truth`, `quay_gate_bluff` and
  `quay_gate_authority`, and each of those three scenes is two commands: `wait 20` then `end`. Command 0 is the only
  thing they do, and it draws nothing.
- The beat the content file calls the strongest in the block ("The list is full" and then, on the second visit, "I
  checked the list again", the first hint that someone else wrote the player's name) is not in the data at all.
- D5 names "Morgan's gate lines" as one of the two Meta bake hook points and D6 Q5 names Morgan as the first NPC chat,
  so the missing second talk is also the missing showcase for a demo feature.

### F3. Cass is absent, so the block has three people, not four (major)

`southampton_town_quay` has one outdoor actor, `morgan`. `quay_dock_office` has two, `nye` and `dylan`. There is no
actor at (25,7), no `cass_high_street` dialogue id, no trigger on (25,7), and no `cass` speaker anywhere in the
dialogue file. ARRIVAL-CONTENT 4.4 calls her the block's only missable character and the only route reactive line on
the map; her two states read the ledger's `blooded` fact, which is also the only thing on this block that would make
the route system visible in the first five minutes.

The count is still inside the 3 to 5 rule at 3, but the block ships with no optional content and no line that changes
with how the player has played.

### F4. The yard walk is 5 tiles with no text, and it starts 2 tiles from where the player triggers it (major)

`quay_yard_walk` is 5 commands: `move hero down 2` (command 0), `wait 20` (1), `move hero right 3` (2), `wait 20` (3),
`end` (4). No `say`, so the beat has no text at all.

- The trigger is `triggers[9]` at (8,12) and the scene's `start` is (8,10), so when the scene begins the hero snaps 2
  tiles north before walking south again. That is a visible relocation of the sprite, and avoiding exactly that is what
  spec 04 rule 4 is for.
- The walk covers 5 tiles and ends at (11,12). ARRIVAL-CONTENT asks for the beat 21 loop across four named landmarks,
  about 60 tiles trimmed to 45. Canute's Palace (19,11) is 8 tiles from the end tile, the Watergate Ruin (21,14) is 10,
  St. Julians Chapel (29,17) is 18, and God's House Tower (39,20) is 28. None is on the walk, and since none of them
  has a trigger or a line, a player who walks there on their own sees a building and no text.
- The trigger only has 4 steps of margin against spec 04 rule 4: the gate scene ends with the player at (8,10), the
  yard trigger is 2 tiles away, and 2 tiles is 24 steps against the 20 step inert window.

### F5. The map draws with 3 of the sheet's 20 characters, and the harbour is drawn as a brick wall (major)

`southampton_town_quay`, all rows. The tile art uses `.` 1694 times, `#` 1266 times and `D` 8 times. Mapped against
the OSM draft's own classes:

| Draft class | Tiles | Art | Collision |
| --- | --- | --- | --- |
| minor road | 718 | `.` | walkable |
| major road | 197 | `.` | 196 walkable, 1 story blocked |
| ground | 355 | `.` | walkable |
| quay | 224 | `.` | walkable |
| park | 101 | `.` | walkable |
| path | 99 | `.` | walkable |
| building | 659 | `#` | blocked |
| **water** | **603** | **`#`** | **blocked** |
| door | 12 | `D` (8) / `#` (4) | walkable (8) / blocked (4) |

So the harbour is 603 tiles of the brick and iron wall tile, and the quay sheet's three harbour water characters
(`w` gid 4, `W` gid 5, `R` gid 6, group `bg1_harbour_water`) are never used. The block reads as paving and brick with
no waterline at all, on the one map in the demo whose subject is a quay. The props the sheet holds are unused too:
barrier `b`, bollard `B`, chain `c`, lamp `L`, harbour sign `S`, so the street has no furniture and the gate has no arm
(F1).

Every other blocked tile is a `#`, so the only tile in the whole grid that is drawn as floor and cannot be walked on is
(8,9), the barrier. There are no tiles drawn as wall that can be walked on.

### F6. The pier is an island, so the walk the block exists to open cannot happen (major)

`southampton_town_quay`, `spawns.from_pier` at (15,42). Breadth first search from the entry reaches 1397 tiles in one
component; (15,42) is not in it. The pier sits in a 74 tile component spanning x 15 to 34 and y 38 to 50, whose nearest
tile to the reachable main body is (7,31), 19 tiles away in Manhattan distance. The other components are 113, 45, 22,
22, 13, 4, 4 and 3 tiles: enclosed yards and alleys that a player can see and never enter.

ARRIVAL-CONTENT section 7 and the route notes put beat 24 and beat 25 on "the quayside walk south past the Red Jet
Ticket Office to the pier (15,42)", and S5 builds the gangway from that pier. As the grid stands, the player cannot
walk to it, and the `from_pier` spawn is a spawn point nothing can arrive at.

### F7. The first fight can fire before the beats that set it up (medium)

`southampton_town_quay`, `triggers[10]` at (23,14) has `condition: ""`, so the story marker is live from the first
step of control. It is 29 tiles from the entry; the gate scene is 12 tiles away and the office door 33. A player who
walks east instead of south fights the hound having met neither Morgan nor Nye, which inverts the beat sheet (the fight
is beat 23, after beats 20 to 22) and strips the payoff from Dylan's line about the hold.

The fix is a `condition` the data already supports, `gate_passed` or `has_boarding_pass`, or a ruling that the fight
may come first. I am not deciding which; see section 7.

### F8. The gate scene restarts the cue the map is already playing (minor)

`quay_gate_checkpoint`, command 0 is `music PP-03`, and the map's own `music` is `PP-03`. The same cue is already
running when the scene starts, so the command asks for a start or a crossfade of a cue already at full level. Whether
the engine rewinds it is an engine question, not a data one, but there is no reason to issue the command, and spec 06
gives a music crossfade 30 steps, so a restart would be 0.5 s of rewind at the exact moment the guard speaks.

### F9. Two doors are modelled two ways, and four more are drawn as wall (minor)

Seven of the eight named doors are `say` triggers sitting on the door tile itself, so the player stands inside the
doorway (the tile is walkable) and presses confirm there. The eighth, `quay_dock_office` at (18,25), is the only `map`
trigger, and spec 04 rule 2 fires it by facing it from the approach tile (18,24). The same object is interacted with in
two different ways one screen apart.

The draft paints 12 door tiles; 8 became `D` and walkable, and 4 stayed `#` and blocked: (22,0), (13,3), (12,9) and
(46,15). Those four are unnamed buildings' doors and ARRIVAL-CONTENT explains why they are unused, but the grid draws
them as plain wall, so a door and a wall are the same picture on four of the twelve.

### F10. Both office actors carry the scene's first dialogue id, so it can play twice (minor)

`quay_dock_office` actors `nye` at (8,7) and `dylan` at (11,7) both carry `dialogue: quay_dock_office`. That is the
first of the two entries the office scene plays (`quay_dock_office_play`, command 0). A player who walks up to the
counter and presses confirm on either man hears pages 1 to 3, then walks onto (6,12) and hears the same three pages
again as command 0 of the scene. Neither actor's dialogue can grant `has_boarding_pass`; only command 1 of the scene
can, through `quay_dock_office_pass`'s `sets`.

### F11. Numbers in the content file that a reader recomputes differently (note)

- "1706 of 2968 walkable": recomputed from the shipped grid it is 1701 walkable plus 1 story blocked, as section 3
  says.
- "12 door tiles, one per building": 12 in the draft, 8 painted `D` in the map, 4 painted `#`.
- "60 tiles and wants trimming to 45" for the yard walk: the scene walks 5.
- Everything else I recomputed held: 53 by 56 at 8 m a tile, 3.3 by 3.7 screens, the eight door names and way ids, the
  eight approach tiles, the four people's names and both lines each, the seven `say` doors plus one `map` door, and
  the dialogue line lengths (no page line exceeds 28 characters, no page exceeds 3 lines, no entry exceeds 3 pages,
  and every choice label is 12 characters or fewer, so spec 05's box is respected).

## 5. Spec by spec

| Spec | Result | Evidence |
| --- | --- | --- |
| 04 tile map 16 px, 16 by 15 visible | pass | 53 by 56 at tile_size 16; 3.31 by 3.73 screens |
| 04 collision 0 / 1 / 2 | pass as a grid, fail in effect | only `012`, but the one `2` is bypassable (F1) |
| 04 trigger shape and kinds | pass | 11 triggers, kinds `say`, `map`, `scene`, `marker`, all allowed, all with `x`, `y`, `kind`, `id`, `once`, `condition` |
| 04 rule 2 doors fire on confirm | pass | `quay_dock_office` map trigger at (18,25) with `spawn: from_quay` |
| 04 rule 3 once triggers recorded | pass, on paper | 3 `once` triggers; spec 10 rule 4 records their flag, and flags are saved |
| 04 rule 4 inert 20 steps | pass with 4 steps of margin | gate scene hands back at (8,10); yard trigger at (8,12) is 24 steps away |
| 04 rule 5 story blocked tiles open on a flag | fail | `story_flag: gate_passed` is declared and the tile opens, but the tile has no visible art and is not needed, because it can be walked around (F1) |
| 04 rail may not cross a blocked tile | not applicable | `rails` is empty on both maps; the walks are scene `move` commands, and all 5 steps of `quay_yard_walk` land on class 0 tiles |
| 04 encounters: markers only, respawn 30 steps | pass under D1 | 1 story marker, `once: true`, never re-arms, as D1 requires for a story marker |
| 05 box geometry and text rules | pass | longest page line 28 characters, 3 lines a page, 3 pages an entry, choice labels 8, 10 and 8 characters |
| 05 choices: `label`, `sets`, optional `goto` | pass | `quay_gate_choice` choices 0 to 2, each setting `gate_passed` plus one flag, each with `goto` |
| 05 every flag is in `data/flags.json` | pass | the five arrival flags are present (D3) |
| 05 portrait names a real sheet | pass | `spr_pp_portrait_guard.png` exists; no narrator carries a bust |
| 06 commands are data, one at a time | pass | all 21 commands over six scenes use declared commands only |
| 06 rule 3 branch is the only control flow | pass, but three branches do nothing | `quay_gate_checkpoint` commands 3 to 5 (F2) |
| 06 rule 4 checker proves ids and walkable moves | pass | `check_data` exit 0; the 5 move steps were re-checked by hand |
| 06 rule 6 no scene ends on an unresolved battle | pass | no `battle` command in any arrival scene |
| 06 256 command warning | pass | 7 commands is the longest |
| 11 flags a save must carry | pass | the five flags are declared, so a load validates them |
| 11 autosave on map entry | cannot be checked in data | no save trigger is needed and none is added; the first manual save stays at the ship's log |
| 11 once triggers across a save and load | open, see 7 | spec 10 rule 4 says a once trigger records its flag; that flag's name is not in `data/flags.json`, and spec 11 rule 3 validates every id against the data set |

## 6. What this review did not prove

- No engine was run and the map was not played. Every number is computed from the committed data, and both checkers
  were run for real. Whether the renderer draws the barrier, or restarts the cue at F8, is a code question in a lane
  that is not this one.
- `tests/test_arrival_map.py` (R08, t_3a52845d) does not exist yet, so nothing in the suite tests the four D1
  placement rules, reachability, or the door count. My findings are the only check on them right now.
- The one rule I could not settle from the data alone is F7's ordering; it needs a ruling (section 7).
- The `southampton_town_quay` row and the arrival scenes landed underneath commit 354f4f3 and later commits rather
  than in one arrival commit, so the history does not tell me which card made each change; I reviewed the bytes, not
  the intent, which is the right thing for a data review anyway.

## 7. Q: for gamedev

Q1. Story marker ordering (F7). Does the first story marker carry a `condition` of `gate_passed` or
`has_boarding_pass`, or is the fight allowed to come before the gate and the office? I did not pick one, because the
beat sheet and spec 04 both speak to it and neither settles it.

Q2. The roadmap's S4 check line ("no encounter marker within 6 tiles of the entry or a door, 1 marker per 40 to 60
walkable tiles") contradicts D1 for this map, and D1 wins. Should ROADMAP-2026-10-22.md's S4 line be corrected, and is
the correction this card's to report only?

Q3. A once trigger's recorded flag (F spec 11 row). Spec 10 rule 4 says a once trigger records its flag, and spec 11
rule 3 says a load validates every id against the data set. The arrival has three once triggers and none of their flag
names is in `data/flags.json`. Either the engine derives the name and spec 11 skips it, or the three names are appended
to `data/flags.json`. That is a spec question, not a data edit, so I am reporting it rather than choosing.

## 8. What must change, in the order I would fix it

1. **Make the gate real** (F1). Block the road where the barrier is drawn, at (7,9) to (9,9) or wider across the open
   carriageway, paint the arm with the sheet's `b` prop, move the gate trigger to the approach tile north of the arm so
   the conversation happens before the crossing, and keep the `from_gate` landing at (8,10) for the handback.
2. **Restore Morgan's second talk** (F2): a `morgan_again` entry with the three flag variants, a trigger for it, and a
   reader for `gate_truth`, `gate_bluff` and `gate_authority`; delete the three `wait 20` stub scenes or give them
   content, because as written they are the only readers and they draw nothing.
3. **Decide Cass** (F3): add her, her line and her trigger at (25,7), or record that the block ships with three people
   and no optional content. The second is a content decision and not the builder's.
4. **Give the yard walk its beat** (F4): set the scene `start` to the trigger tile (8,12) so the hero does not jump, and
   either walk the beat 21 route with its landmark lines or drop the beat from the beat sheet so nothing is promised.
5. **Draw the water** (F5): use `w`, `W` and `R` for the 603 water tiles and keep them blocked; the collision is fine,
   the picture is not.
6. **Connect the pier** (F6): open a walkable route from the main component to the (15,42) component, or move
   `from_pier` and the beat 24 route onto a pier the grid actually reaches. Until then the S5 gangway has no pier.
7. **Set the marker's condition** (F7), once Q1 is answered.
8. Minor, same card if the builder has room: F8, F9, F10.

P: the four checkers and probes above were run, the numbers are recomputed from the committed bytes, and the file I
wrote is this one.
