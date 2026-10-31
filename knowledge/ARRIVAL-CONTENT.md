# Arrival content: the Town Quay block, five to seven minutes in

Card: t_7e72fe1c (R15, step S4 of ROADMAP-2026-10-22.md). Lane: research-assistant.
Status: content spec, written 2026-10-22. Read by the arrival map card (t_c024f8bc) and the arrival data review (t_6cd706d0).
Scope of this file: who and what stands on the arrival block, with real names. It does not draw the map, write the map
data, or write the dialogue file.

The two answers the card asks for, first:

- The boarding pass is carried by the dock office clerk, **Nye**, who hands it over in the office scene (beat 22).
- The person the player can talk to twice is the gate sentry, **Morgan**, at the barrier. The first talk is the gate
  checkpoint scene (beat 20, four pages and one three option choice); the second talk is a short optional scene that
  plays only after the gate flag is set, and its line changes with which of the three choices was picked.

---

## 1. Sources and attribution

| What | Where |
| --- | --- |
| Map data | `data/osm_cache/southampton_town_quay.json`, an Overpass API extract already in this repo |
| Query bounding box | south 50.8938, west -1.4070, north 50.8978, east -1.4010 |
| Extract fetched | 2026-10-22T04:05:03+00:00 (the extract's own `_pp_fetched_utc`) |
| Overpass data timestamp | 2026-10-22T04:03:11Z (the extract's own `osm3s.timestamp_osm_base`) |
| Generator | Overpass API 0.7.62.11 87bfad18 |
| Contents | 313 elements: 312 ways and 1 relation; 68 carry a `name`; 52 are buildings; 40 are named roads; 4 are named parks |
| Terrain draft | `data/maps/osm/southampton_town_quay.json`, 53 by 56 tiles at 16 px, produced by `tools/osm_to_map.py` |
| Pacing numbers | `knowledge/mechanics/PACING-AND-CUTSCENES.md` sections 5, 6 and 9 |
| Names for people | `knowledge/NAMES-BIBLE.md` sections 3.5, 3.6 and 4.1; `knowledge/CHARACTER-BIBLE.md` |
| Trigger and dialogue rules | `specs/04-overworld-rails-and-triggers.md`, `specs/05-dialogue.md`, `specs/16-talk-command.md` |

Attribution, the ODbL line, as this repo already writes it in `data/maps/southampton_sample.json`:

    (c) OpenStreetMap contributors, Open Database Licence (ODbL) 1.0, https://www.openstreetmap.org/copyright

The extract carries the same statement in its own header, `osm3s.copyright`: "The data included in this document is from
www.openstreetmap.org. The data is made available under ODbL." Any map, screenshot or credit screen built from this
block carries the line above verbatim. The ODbL share alike term applies to the derived map data, not to the game's own
story text.

Provenance of the data itself, stated so nobody has to ask:

- No Google data, no Street View, no Google Maps, and no imagery of any kind was opened, viewed or traced for this card.
  Every coordinate in this file was read out of the OSM extract above, which is the project's own cached download.
- 32 elements in the extract carry a contributor `source` tag: 25 `Bing`, 4 `survey`, 3 `maxar`. Those are the OSM
  contributors' own notes on how they mapped the feature, and they travel inside ODbL data. Two of the eight doors
  below front buildings that carry such a tag: Southampton Register Office (way/48775316, `Bing`) and Dancing Man
  (way/88272970, `Bing`). The whole block is rasterised from the same extract, so swapping those two doors would not
  change the map's provenance, only its guest list. If an audit reads the rule as "no imagery derived geometry at
  all", drop those two doors and the block runs 6 doors, still inside the 6 to 10 rule.

---

## 2. The block in numbers

- 53 by 56 tiles at 8 m a tile, 424 by 448 m, which is 3.3 by 3.7 screens of 16 by 15 tiles (PACING section 5).
- Terrain tiles in the draft: 718 minor road, 659 building, 603 water, 355 ground, 224 quay, 197 major road, 101 park,
  99 path, 12 door tiles. 1706 of the 2968 tiles are walkable under the draft's class rules.
- The study's rule for a hub under 4 screens across: 6 to 10 doors and 3 to 5 people (ROADMAP S4). This file settles on
  **8 doors and 4 people**, both inside the rule.
- The draft map already paints 12 door tiles, one per building on the street side (`tools/osm_to_map.py`, gid 10). Eight
  of the twelve front a building that the extract names. The other four (at 22,0 / 13,3 / 12,9 / 46,15) front buildings
  with no `name` tag in OSM, so a door there could not be named from the source, and they are not used. That is the whole
  reason the count is 8 and not 12.
- Walking speed is 5 tiles a second, so one pass across the block is about 11 s in either direction. Every walk distance
  below is stated in tiles, which is what the builder places.

---

## 3. The eight doors

Every name below is the exact `name` tag in the extract, with its way id. The tile is the door tile the project's own
rasteriser already painted, so nothing here is placed by eye. "Approach" is the tile the player stands on to press
confirm, read off the draft's terrain.

| # | Tile | Name in OSM (verbatim) | Way id | What it is | Job in the beat |
| --- | --- | --- | --- | --- | --- |
| 1 | (11,0) | Southampton Register Office | way/48775316 | civic office, `amenity=public_building` | The first door the player sees, one tile from the spawn. It is shut and it is the wrong building, so it teaches that doors answer and that not every door is the one you want. |
| 2 | (8,5) | Dancing Man | way/88272970 | pub in the building OSM calls The Wool House | The town the player is leaving, still open and loud on the west side of the walk to the gate. Shut to the player, one line. |
| 3 | (51,5) | Oceana Boulevard | way/146620412 | apartment block, east edge | Gives the east side of the block one thing to press, so the map is not a corridor north to south. Shut, one line. |
| 4 | (26,6) | Telephone House | way/53541760 | eight storey building, `building=yes`, `building:levels=8` | The call he does not make. Shut, one line, and it plants the idea that a call is possible before the ship's log arrives at beat 27. |
| 5 | (1,11) | Kuti's Brasserie | way/30914539 | restaurant on the water, the Royal Pier gatehouse | The last warm kitchen on the waterfront. Shut, one line. Puts a light on the west shore so the water edge reads as a place and not a wall. |
| 6 | (10,20) | Red Funnel Terminal 1 | way/37375880 | ferry terminal | The first door that looks like the right door. It is the wrong terminal: a passenger ferry, not a Navy berth. Shut, one line, and the line points the player on toward the pier. |
| 7 | (23,22) | Playhouse Gentlmens Club | way/78306579 | nightclub, `amenity=nightclub` | The last wrong door before the office. Shut, no sign text and no name on screen at 8x8, one neutral line. The OSM name is not reproduced on screen; see section 8. |
| 8 | (18,25) | Town Quay Offices | way/78348527 | office building on the quay frontage | The dock office. The only door in the block that opens. Map trigger to the interior `quay_dock_office`, spawn `from_quay`, and the boarding pass is inside it. |

Approach tiles, read from the draft's terrain layer: (11,1) road for door 1; (8,6) path for 2; (51,6) road for 3;
(26,7) road for 4; (2,11) road for 5; (9,20) road for 6; (22,22) road for 7; (18,24) road for 8.

Trigger rows, in the spec 04 shape `{x, y, kind, id, once, condition}`:

| x, y | kind | id | once | condition |
| --- | --- | --- | --- | --- |
| 11, 0 | say | `say_door_register` | false | "" |
| 8, 5 | say | `say_door_dancing_man` | false | "" |
| 51, 5 | say | `say_door_oceana` | false | "" |
| 26, 6 | say | `say_door_telephone` | false | "" |
| 1, 11 | say | `say_door_kuti` | false | "" |
| 10, 20 | say | `say_door_red_funnel` | false | "" |
| 23, 22 | say | `say_door_playhouse` | false | "" |
| 18, 25 | map | `quay_dock_office` | false | "" |
| 8, 9 | scene | `quay_gate_checkpoint` | true | "" |
| 8, 10 | say | `morgan_again` | true | `gate_passed` |
| 25, 7 | say | `cass_high_street` | true | "" |

Seven `say` doors and one `map` door is deliberate: an interior costs a map, and the block can only afford one, which is
the office. Every other door is a line, which is 7 short dialogues and no new maps.

---

## 4. The four people

The people are the story's own invention. None of them exists in OSM and no OSM element is a person. Each name is taken
from an option already written up in `knowledge/NAMES-BIBLE.md`, so no new unsourced name enters the project.

### 4.1 Morgan, gate sentry (the person you can talk to twice)

- Name: **Morgan**, invented for this story, first name only. Source of the name: NAMES-BIBLE section 3.5, option A for
  the Navy Sailor, Old Welsh Morcant, possibly mor "sea" plus cant "circle". Morgan is a rating of the duty watch, not
  an officer, so the rank in his mouth is a leading hand's, not a lieutenant's.
- Where: at the barrier across Town Quay, drawn on the rasterised carriageway at row 9, tiles (7,9) to (9,9), three tiles
  wide. That row is Town Quay, way/9676782, way/754075550 and way/1145156236, all tagged `highway=primary` and
  `name=Town Quay`. The barrier tile (8,9) is a story blocked tile until `gate_passed` (spec 04 rule 5), which is what
  makes the gate matter without being able to fail the player. Morgan is drawn on (8,9); the player's landing tile after
  the scene is (8,10); the second talk trigger sits on (8,10) facing back, so no tile carries two triggers.
- Beat 20, 4:50 to 5:42, the four pages and the three option choice. 52 s.
- What he wants, one line: his watch to end with nothing written in the incident book.
- What he refuses to say, one line: what the clipboard actually says, because the crew list is blank against the name he
  is about to write down.
- First talk: `quay_gate_checkpoint` (4 pages, one three option choice, three replies). Sets `gate_passed` plus exactly
  one of `gate_truth`, `gate_bluff`, `gate_authority`.
- Second talk: `morgan_again`, one page, only after `gate_passed`, and its line is picked by which of the three flags is
  set. This is the block's only second conversation and it is where the plot first leaks: see section 6.

### 4.2 Nye, dock office clerk (carries the boarding pass)

- Name: **Nye**, invented for this story, first name only. Source of the name: NAMES-BIBLE section 3.6, option C, a Welsh
  diminutive of Aneurin, root "honour". Chosen because the scene turns on him being the only man in the building still
  doing the paperwork honestly.
- Where: at the counter inside `quay_dock_office`, the interior behind door 8 at (18,25). Not on the outdoor map.
- Beat 22, 6:10 to 7:22, six pages. 72 s. He speaks pages 2 and 4.
- What he wants, one line: the ledger to balance, so that the last berth is filled and he can shut the office.
- What he refuses to say, one line: who put the player's name on the manifest, because the last line in the ledger is
  not in his handwriting and he has stopped asking.
- He hands over the boarding pass on page 6. Flag `has_boarding_pass`. The pass itself is a pink slip in the fiction; the
  item is not in the inventory and does not need to be, it is a flag and a line of text.

### 4.3 Dylan, Navy Sailor (the runner in the office)

- Name: **Dylan**, invented for this story. Source: NAMES-BIBLE section 3.5, option B. This is the same man the data
  already calls `navy_sailor`, the enemy of the first fight and the TALK lesson, so the office scene is the player's one
  look at him before beat 23 and beat 28 and no new character is spent on it.
- Where: standing at the counter inside `quay_dock_office`, beside Nye. Speaks page 5.
- What he wants, one line: to be back on the ladder and out of the office, because the hold is not quiet tonight.
- What he refuses to say, one line: what is in the hold, which is the fight the player walks into at beat 23.
- Ties to data that already exists: `enemy: navy_sailor`, `talk_navy_sailor`, `battle_intro_sailors`, `navy_win_spare`,
  `navy_win_kill` in `data/dialogue/all.json`, and the Navy Sailor talk card in spec 16 section 10.

### 4.4 Cass, High Street (the missable one)

- Name: **Cass**, invented for this story. Source: NAMES-BIBLE section 3.6, option B, from Cassandra, the prophet nobody
  believes. Placed on High Street because High Street is inside this extract and this block.
- Where: standing tile (25,7), on High Street, way/625992354 (tertiary, centroid tile (25,7)). That is east of the walk
  from the spawn to the gate, so she is optional. A prophet nobody believes should be missable.
- Beat: none. She is not on the critical path and costs no seconds in the beat sheet. One page, one line.
- What she wants, one line: somebody to hear the warning tonight, before the water gets loud.
- What she refuses to say, one line: the name of the person she means, which is the name the game is about.
- Route reactive: `cass_high_street` plays one of two lines, picked by the route ledger's `blooded` flag. With no kills
  she warns about the water; after the first kill she says it got louder when the player arrived. This is the same one
  line the NAMES-BIBLE gives her, in its two states.

Three to five people is the rule; four is the count. Two outdoors (Morgan, Cass) and two inside the office (Nye, Dylan).

---

## 5. The dialogue, data ready

Rules the lines obey, all from spec 05: 30 characters a line, 3 lines a page, 2 steps a character, `*` opens a line, and
a line that cannot fit is a checker error. Choice labels sit in a 96 pixel panel, so 12 characters maximum.

Speaker ids: `narrator` exists. `guard`, `clerk`, `cass` are new and need a blip pitch row in the spec 05 speaker table.
`sailor` exists as `navy_sailor`'s speaking voice.

```json
{
  "format": 1,
  "kind": "dialogues",
  "source": "knowledge/ARRIVAL-CONTENT.md section 5, t_7e72fe1c",
  "dialogue": [
    {
      "id": "quay_gate_checkpoint",
      "speaker": "narrator",
      "pages": [
        { "speaker": "narrator", "lines": ["* Rain on the barrier arm.", "* A hut. One lit window.", "* The man inside stands up."] },
        { "speaker": "guard", "lines": ["* \"That is far enough.\"", "* \"Name and business.\"", "* He holds a clipboard."] },
        { "speaker": "narrator", "lines": ["* Past him the yard is dark.", "* Past that, a grey hull.", "* One lamp on the water."] },
        { "speaker": "guard", "lines": ["* \"No pass, no gate.\"", "* \"So. What is it?\"", "* He waits, pen ready."] }
      ],
      "choices": [
        { "id": "gate_truth", "label": "No pass.", "target": "quay_gate_truth" },
        { "id": "gate_bluff", "label": "Crew list.", "target": "quay_gate_bluff" },
        { "id": "gate_authority", "label": "Ask him.", "target": "quay_gate_authority" }
      ]
    },
    {
      "id": "quay_gate_truth",
      "speaker": "guard",
      "pages": [
        { "speaker": "guard", "lines": ["* \"Honest. That is new.\"", "* \"Office. Sign in.\""] },
        { "speaker": "narrator", "lines": ["* He lifts the arm himself."] }
      ],
      "sets": ["gate_passed", "gate_truth"]
    },
    {
      "id": "quay_gate_bluff",
      "speaker": "guard",
      "pages": [
        { "speaker": "guard", "lines": ["* \"The list is full.\"", "* \"Office, then. Sign.\""] },
        { "speaker": "narrator", "lines": ["* He does not look down."] }
      ],
      "sets": ["gate_passed", "gate_bluff"]
    },
    {
      "id": "quay_gate_authority",
      "speaker": "guard",
      "pages": [
        { "speaker": "guard", "lines": ["* \"My officer is asleep.\"", "* \"Office. Now.\""] },
        { "speaker": "narrator", "lines": ["* He does not believe it."] }
      ],
      "sets": ["gate_passed", "gate_authority"]
    },
    {
      "id": "morgan_again",
      "speaker": "guard",
      "pages": [
        { "speaker": "guard", "lines": ["* \"You came back.\"", "{by_flag}"] }
      ],
      "by_flag": {
        "gate_truth": "* \"You told me the truth.\"",
        "gate_bluff": "* \"I checked the list again.\"",
        "gate_authority": "* \"He was not asleep.\""
      }
    },
    {
      "id": "quay_dock_office",
      "speaker": "narrator",
      "pages": [
        { "speaker": "narrator", "lines": ["* A counter. A lamp. A ledger.", "* Two men. One is Navy.", "* The other is not."] },
        { "speaker": "clerk", "lines": ["* \"You are the last one.\"", "* \"Name, then. Slowly.\"", "* The pen is already wet."] },
        { "speaker": "narrator", "lines": ["* One line left in the ledger.", "* The ink on it is dry.", "* It is not the clerk's hand."] },
        { "speaker": "clerk", "lines": ["* \"Berth nine. Deck two.\"", "* \"Do not leave the cabin.\"", "* He tears a pink slip."] },
        { "speaker": "sailor", "lines": ["* \"Sign it and come on.\"", "* \"I have a ladder to hold.\"", "* He does not look up."] },
        { "speaker": "narrator", "lines": ["* The slip changes hands.", "* It is warm from a pocket.", "* Behind them, the gate shut."] }
      ],
      "sets": ["has_boarding_pass"]
    },
    {
      "id": "cass_high_street",
      "speaker": "cass",
      "pages": [
        { "speaker": "cass", "lines": ["* \"The water is loud tonight.\""] }
      ],
      "by_flag": {
        "blooded": "* \"Louder since you came.\""
      }
    },
    {
      "id": "say_door_register",
      "speaker": "narrator",
      "pages": [ { "speaker": "narrator", "lines": ["* Registry office. Shut."] } ]
    },
    {
      "id": "say_door_dancing_man",
      "speaker": "narrator",
      "pages": [ { "speaker": "narrator", "lines": ["* A pub. Warm and loud."] } ]
    },
    {
      "id": "say_door_oceana",
      "speaker": "narrator",
      "pages": [ { "speaker": "narrator", "lines": ["* Flats. Every bell dead."] } ]
    },
    {
      "id": "say_door_telephone",
      "speaker": "narrator",
      "pages": [ { "speaker": "narrator", "lines": ["* Telephone House. No call."] } ]
    },
    {
      "id": "say_door_kuti",
      "speaker": "narrator",
      "pages": [ { "speaker": "narrator", "lines": ["* A kitchen, still open."] } ]
    },
    {
      "id": "say_door_red_funnel",
      "speaker": "narrator",
      "pages": [ { "speaker": "narrator", "lines": ["* Ferries. Not your ship."] } ]
    },
    {
      "id": "say_door_playhouse",
      "speaker": "narrator",
      "pages": [ { "speaker": "narrator", "lines": ["* A door with no light."] } ]
    }
  ]
}
```

Line count: 4 pages at the gate, 6 in the office, 1 page for the second talk, 1 for Cass, 1 each for the seven shut doors.
About 240 words of story text in the whole block, which is what 8 doors and 4 people actually cost.

---

## 6. What the gate choice does, and why all three open it

The checkpoint cannot be failed. Beat 20 sits before the player has ever held a sword, and the beat sheet's own gates put
the first fight at 7:22; a gate that can be failed at 5:00 is a second tutorial with no lesson in it. So all three choices
lift the barrier and all three set exactly one flag:

| Choice | Label | The guard's read | Flag | What the second talk with Morgan reveals |
| --- | --- | --- | --- | --- |
| truth | No pass. | honesty is new to him | `gate_truth` | "You told me the truth." |
| bluff | Crew list. | he does not look at it | `gate_bluff` | "I checked the list again." Your name is on it now, which is the first hint that someone else wrote it. |
| authority | Ask him. | he says the officer is asleep | `gate_authority` | "He was not asleep." Which is the first hint that the Navy is waiting for him. |

The bluff branch is the strongest of the three and it is the one a player is most likely to pick, which is why the guard's
second line is the one that turns: the list was full a minute ago and it has his name on it now. That is the plot, in one
line, at 5:10, before any god has been seen.

Every branch is two pages: the reply, then a one line narrator page. That keeps the gate scene at 4 pages plus at most 2,
inside the 52 s beat, and it means the choice costs the same seconds whichever entry is picked.

---

## 7. What stands here that is not a door or a person

Real landmarks the two free walks pass, all named in the extract, no door and no dialogue. They exist to stop 3 screens
of yard from being 3 screens of nothing.

| Name in OSM (verbatim) | Way id | Tile of centroid | Where it sits in the walk |
| --- | --- | --- | --- |
| The Watergate Ruin | way/262730624 | (21,14) | Beat 21, the yard walk, 2 tiles east of the quay road. |
| Canute's Palace | way/262730631 | (19,11) | Beat 21, north end of the yard, just inside the gate. |
| St. Julians Chapel | way/183691408 | (29,17) | Beat 21, the east end of the loop, which is what makes the walk a loop. |
| God's House Tower | way/519439070 | (39,20) | Beat 21, the far east turn. Do not go further east than this with content. |
| Southampton Old Bowling Green | way/30476350 | (43,12) | Beat 21, visible east of the tower, no interaction. |
| Town Quay (pier) | way/665359685 | (15,42) | Beat 24 and 25. The pier the gangway is built from, and the end of this block. |
| Red Jet Ticket Office | way/128360615 | (8,45) | Beat 24, the quayside walk south, passed on the water side. |
| Red Funnel Terminal 2 | way/37375883 | (9,45) | Beat 24, behind the ticket office. Shut at this hour, no line. |
| Navico Group | way/128360618 | (7,50) | Beat 24, the last building before the pier. |

The route those landmarks make, in tiles, for the builder to lay and trim: spawn (11,1), the Register Office door (11,0),
south past Dancing Man (8,5) and Kuti's (1,11), the gate at (8,9), then Canute's Palace (19,11), the Watergate Ruin
(21,14), east to St. Julians Chapel (29,17) and God's House Tower (39,20), then back south west to the office door
(18,25), which is about 60 tiles and wants trimming to 45, then the quayside south past the Red Jet Ticket Office to the
pier (15,42), about 20 tiles.

Encounter markers: this block carries **one marker and no random ones**. The one is the first fight's hound at beat 23,
which stands in the yard between the office and the quay, at least 6 tiles from every door above and from the entry tile.
Section 11 raises a question about that against the density rule.

---

## 8. Real names and invented names

Every place name in this file is a `name` value that exists in `data/osm_cache/southampton_town_quay.json`, with its way
id beside it, spelled as the extract spells it (including "St. Julians Chapel" with the full stop and no apostrophe, and
"Playhouse Gentlmens Club" with the source's own spelling).

Invented by the story, and marked as invented here and wherever they are shipped:

| Invented | What it is | Note |
| --- | --- | --- |
| Morgan | gate sentry, first name only | from a NAMES-BIBLE option, the person is invented |
| Nye | dock office clerk | from a NAMES-BIBLE option, the person is invented |
| Dylan | Navy Sailor, the office runner and later the enemy | NAMES-BIBLE option; the enemy id `navy_sailor` already exists in data |
| Cass | High Street, the missable prophet | NAMES-BIBLE option |
| `quay_dock_office` | interior map id for the office | invented id |
| the barrier, the hut, the pink slip, the ledger | props and set dressing | invented; the ledger is a prop, no numbers on screen |
| berth nine, deck two | where the player is berthed | invented detail; the ship's own name is not settled here (see section 10) |
| the five flags in section 9 | new route flags | invented ids, needs a data owner |

One name is deliberately **not** put on screen: the nightclub's OSM name at (23,22), and with it any account of what kind
of club it is. The door gets a neutral narrator line and no sign text, because 8x8 capitals on a NES sign cannot carry that
name without it becoming the joke, and the game's rating rule is that no text on screen is worse than the dialogue files
already ship. The building is still named in this table and in the map's provenance, because the data is the data.

---

## 9. Flags this block sets

Read by triggers and by later scenes. None of these exists in `data/flags.json` today, and no card in this batch owns
that file, so the builder must raise it rather than write it (see section 11).

| Flag | Set by | Read by |
| --- | --- | --- |
| `gate_passed` | any of the three gate replies | the second talk with Morgan, and the yard walk's triggers |
| `gate_truth` / `gate_bluff` / `gate_authority` | one of the three gate replies | `morgan_again`'s line pick |
| `has_boarding_pass` | `quay_dock_office` page 6 | the gangway check at S5, and Percy's first line about a stowaway |
| `blooded` | already exists in the ledger's vocabulary (spec 16 section 3) | Cass's one line |

Autosave on entry is spec 11's rule (map entry after the fade), not this file's, and the first save the player is taught
to make is the ship's log at beat 27. The arrival block therefore writes one silent autosave and shows no save screen.

---

## 10. What this file does not decide

- The map geometry, the collision grid, the walkable path of the two free walks, and where the marker exactly stands. The
  builder places those; the tiles above are anchors read off the draft.
- The ship's name, the interior's art, and the office layout. The office interior is one room, a counter, a lamp, a
  ledger and a door; anything more is S5's business.
- Percy's arrival, Prometheus's call, and whether the guide on the quay is a god. None of them happens in this block.
- Dialogue file ownership: `data/dialogue/all.json` is named by no card in this batch, so the JSON in section 5 lands
  through a gamedev decision, not through this card. See section 11.

---

## 11. Q: for gamedev

Q1. Marker density. The roadmap check for this block quotes the study's density rule, one marker per 40 to 60 walkable
tiles. This block has 1706 walkable tiles, so that rule asks for 28 to 43 markers, which is a fight every 8 to 12 seconds
on a hub the beat sheet treats as 3 screens of walking and one scripted fight. My recommendation is one scripted marker
(the hound, beat 23) and no random markers, reading the study's own words as "a density ceiling" (PACING section 6.1) and
not a quota. Please confirm which reading the map card is graded against.

Q2. Dialogue ownership. The fourteen dialogue ids in section 5 have no owner card: `data/dialogue/all.json` is not in any
card's file list, and the map card is told to raise a Q rather than edit it. Either name an owner for that file, or say
that the map card may add these ids itself. The lines are written and length checked; the work is one file edit.

Q3. One tile, two conditions. Cass's single line has two states picked by the `blooded` flag. Spec 05 allows a condition
on a choice, not on a page, and spec 04 gives a trigger one `condition`, so the shape I would use is two trigger rows on
her tile with mutually exclusive conditions, first match wins. If the trigger runner does not guarantee that order, she
moves one tile and gets two tiles instead, which is worse. Please rule on the order guarantee.

---

## 12. Checks this file passes, and how

| Check | How it was proved |
| --- | --- |
| 6 to 10 doors | 8 doors, counted in section 3. |
| 3 to 5 named people | 4 people, counted in section 4. |
| Every door name exists in the extract, with its way id | Each of the eight way ids was looked up in `data/osm_cache/southampton_town_quay.json` and its `name` compared character for character; the door tile was confirmed to be a gid 10 tile in `data/maps/osm/southampton_town_quay.json` and to share an edge with that way's rasterised footprint. |
| Every invented name is marked | Section 8 is the table, and section 4 marks each person at the point of naming. |
| One line of what each person wants, one line of what they refuse to say | Section 4, every person, both lines present. |
| The boarding pass carrier and the talk twice person are named | The top of the file, and sections 4.1 and 4.2. |
| No Google, Street View or traced data | Section 1: the only source is the repo's own ODbL extract, and no imagery was opened. The extract's own 32 contributor `source` tags are listed rather than hidden. |
| Sources and the ODbL line | Section 1, the attribution line verbatim. |
| Dialogue fits the box | Every line was measured at 30 characters or fewer, every page at 3 lines or fewer, every choice label at 12 characters or fewer, and the page counts are 4 and 6 as the beat sheet says. |
| No em dash or en dash | The file was scanned for U+2013, U+2014 and U+2015: zero. |

The numbers above are the ones a reviewer can recompute from the two files named in section 1 without opening anything
else. Where a number could not be measured it is not in this file.
