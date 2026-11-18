# Drunk and high: the design answer, 2026-11-17 (card t_c77d489c)

Status: design only. Nothing here is built and nothing here is a build order. This answers the four questions the
tone capture left open (`knowledge/TONE-2026-11-17-wetherspoons.md`): how the two statuses sit beside MERCY and HP,
what each one changes that a player can see, how an item carries a side effect so the tenth item is data, and where
the comedy surfaces through the TALK box that already exists. Nayil's word starts step 1 of section 8.

## 1. The answer in five lines

1. DRUNK and HIGH are clocks, not scores. HP is what you have, MERCY is what they think of you, and a status is how
   many turns the room keeps doing that to you. One number per status, 1 to 9 turns, printed next to the actor.
2. They are carried by the hero and by the enemy alike, they never add a fourth win condition, and they never touch
   HP or MERCY directly. They move the three dice the fight already rolls: the FIGHT bar, the enemy's aim, the TALK
   delta.
3. DRUNK is the body status: hit harder, aim worse. HIGH is the mind status: TALK swings harder both ways, the
   enemy loses turns, the text crawls, the words stop making sense.
4. The item carries the effect in a `use` block (target, damage band, an `apply` list, its own lines), so the beer
   can is one row in `data/items.json` and the tenth throwable is one more row. No GML names a drink.
5. The comedy rides the TALK box: a status selects a different reply pool and the verdict line names the state
   ("SOFTEN. MERCY UP 35. HE IS DRUNK 3."). Zero new windows, zero new colours, both statuses print in palette roles
   that `data/palette.json` already holds.

## 2. System shape: where they sit

The fight today shows four numbers: party HP, party WILL (the spend for POWER), enemy HP and the enemy MERCY meter
(`pp_battle_hud_state`, `game/scripts/pp_battle_director/pp_battle_director.gml:1558`). A status joins that set as a
different kind of number, and the difference is the point:

| number | who has it | moved by | reaches zero | ends the fight |
| --- | --- | --- | --- | --- |
| HP | hero and enemy | damage | yes, that is a defeat or a kill | yes |
| WILL | hero only | POWER costs | no, refilled per fight | no |
| MERCY | enemy only | TALK only | no, it rises toward a spare | yes, through SPARE |
| DRUNK / HIGH | either side | items, TALK, phase rows | yes, one turn at a time | no |

Rules that keep it from touching the balance the demo already proved:

1. **Cost, not gate.** A status never enables or blocks SPARE, TALK or FIGHT. The three ways out of a fight stay the
   three ways out; a route never depends on a status. `spare_refuses_on_route`, `trust_to_spare` and `spare_hp_percent`
   are unchanged.
2. **Clock.** A status carries `turns` (1 to 9). One tick at the end of each full round, after the enemy's turn, so a
   drunk of 3 covers three player actions. At 0 it clears and prints its `clear_line`.
3. **One at a time per actor.** A new status replaces the old one on that actor and prints the swap. That bounds the
   HUD to one tag per side and stops stacking from becoming a second balance system.
4. **Never the player's turn.** A hero status may misalign input or slow text. It may never skip a turn the player did
   not press, and it may never hide a command. Skip is an enemy side only effect (`skip_turn_percent` is read only on
   an AI turn), which is the same courtesy `skip_enemy_turn` already shows (`pp_battle_director.gml:733`).
5. **No ledger, no save.** Statuses live in the battle struct, tick in the fight, and are gone at the result. No
   `data/flags.json` key, no save key, no route counter. Spec 10 and spec 11 do not move.
6. **Data is the only home for a number.** Durations, wobble amplitudes, the swing percentage, the skip percentage,
   the text divisor and every line of text sit in `data/statuses.json`. The two screen positions sit in
   `data/ui_layouts.json` beside the layout numbers already there. GML reads fields; it does not hold a status number.
7. **No blend, ever.** The project already measured what an alpha blend does to a 25 colour screen
   (`knowledge/BATTLE-DIM-OFF-PALETTE-2026-10-26.md`: a 60 percent ink rectangle turned a legal blue into a colour no
   NES outputs). A status therefore never tints a portrait or a sprite. Its colour is a palette role used as ink and
   as a 1 pixel rule, and nothing else.

### Where the two tags print (measured against the shipping layout)

- **Enemy:** the plate's own MERCY label line. `data/ui_layouts.json` battle_b.plate has `label_x` 16, `mercy_y` 77,
  `bar_x` 80. "MERCY" is 5 cells (x 16 to 55), one space, then the tag and its digit ("D3") is 3 cells (x 56 to 79).
  The whole string is 8 cells, x 16 to 79, and the bar starts at x 80. Exact fit, and the label word never moves, so
  `tools/capture_talk_live.py`, which reads that line as the MERCY row, keeps working.
- **Hero:** the command band's right column, first label row. `battle_b.command` is x 8, y 168, w 30, h 8, the labels
  sit at x 24 and x 128 with a 5 cell word each (ending x 167), and `pp_battle_draw_menu`
  (`pp_battle_director.gml:1967`) leaves x 176 to 247 empty on every label row. "DRUNK 3" is 7 cells, x 176 to 231,
  inside the band's border at 247. The band frame is drawn in every phase (line 1795 for the phases that are not
  menu or resolve, and the menu's own draw for those two), and the strip is drawn with the frame rather than from
  `pp_battle_draw_menu`, so the tag survives the message phase; the menu's own labels never reach it.
- **Popup:** the word and its clock also print for 30 steps where "+35 MERCY" prints now
  (`pp_battle_director.gml:1833`), so the moment of application is readable even if a player has not learned the tag.
- Two actors, two tags, no new window, no new row. When the layout is absent the legacy rows do the same job: the
  hero's tag appends to the stat line at y 156, whose widest case spec 07 measures at 22 cells ending x 192, which
  leaves 8 cells before the frame edge.

## 3. What each one changes that a player can see

Each status carries a flat record. Each field is read only by the side that can feel it, which is what lets one table
describe the hero and the enemy without two copies.

| field (data) | DRUNK | HIGH | what the player sees |
| --- | --- | --- | --- |
| `bar_wobble_px` | 4 | 2 | the FIGHT marker drifts sideways on a sine of the step count, so the sweet spot has to be timed through the wobble |
| `damage_max_percent` | 150 | 100 | the carrier's damage ceiling rises: the hero's 2 to 12 becomes 2 to 18, the sailor's 2 to 2 becomes 2 to 3 (`pp_battle_fight_damage`, `pp_battle_director.gml:655`) |
| `pattern_wobble_px` | 3 | 0 | the carrier's bullets spawn offset sideways, so a drunk enemy's pattern is easier to read and to dodge |
| `talk_swing_percent` | 0 | 50 | the verdict's number moves away from zero: soften 20 becomes 30, setback 10 becomes 15, sign kept |
| `skip_turn_percent` | 0 | 25 | an enemy carrier loses the turn: the telegraph prints the status line and the pattern never spawns (reuses `skip_enemy_turn`) |
| `type_divisor` | 1 | 2 | the text board types at half speed, which is felt in every box |
| `tag` | D | H | one cell, used on the plate and the band |
| `label` | DRUNK | HIGH | the popup and the verdict line |
| `role` | wine_4 | violet_4 | the tag, the popup and the verdict word are drawn in that role; both roles already exist in `data/palette.json` (wine 18 to 23, violet 42 to 47) |
| `turns_default` | 3 | 2 | the dose a standard item applies |

The two identities are deliberately different, so the player never has to remember two variations of the same thing:

- **DRUNK is the body status.** More damage on both sides, less aim on both sides. Throwing the can at the enemy is a
  real trade: 2 to 6 now, and from then on the sailor hits for up to 3 instead of 2 while its pattern sprawls.
  Drinking yourself is the same trade with the FIGHT bar in your hands.
- **HIGH is the mind status.** It does nothing to damage. It doubles what a TALK does, in both directions, slows every
  word on screen and makes an enemy miss turns. It is the shortcut to a spare and the shortcut to a setback, which is
  exactly the register of the direction: the fun is in the risk, not in the numbers.

Ways out, all three already in the system: the clock runs down; a clearing item (section 5) ends it early; the fight
ends and everything clears at the result. There is no fourth door and no new command.

## 4. The TALK box: where the comedy lands

The box already prints four things: the player's line, the reply, the verdict with the WILL move, and a receipt. The
status touches two of them and adds no new window.

1. **Reply selection.** The reply ladder today is bake row, then card pool, then encounter fallback
   (`pp_talk_reply_clean`, `pp_talk_effect_delta`, `game/scripts/pp_battle_text/pp_battle_text.gml:80` on). The card
   gains a `status_pools` block keyed by status id. Matching order becomes: a bake row carrying that status, then a
   bake row with no status (every row the 2026-11-03 bake holds, untouched), then the status pool, then the sober
   pool, then the encounter fallback. A drunk enemy therefore says something a sober one cannot, and a build with no
   model still says it.
2. **The verdict line.** `pp_talk_verdict_line` composes "<WORD>. <MERCY|WILL> <UP|DOWN|HELD> <n>". It gains the
   carrier's state on the end: "SOFTEN. MERCY UP 35. HE IS DRUNK 3." That is the one place a judge, or a player, can
   see why the reply is strange.
3. **The player's own state** prints on the band tag every turn and, while TALK is open, in the hint row at
   `pp_talk_hint_y` (40) with the status's own `talk_hint`: "YOUR WORDS HAVE WEIGHT." or "THE WORDS KEEP MOVING."

The register, written here as originals, not lifted from anything studied:

- Sober sailor: "You are not on the list."
- Drunk sailor: "You are not... on the list... mate." then "I'm not arguing. I'm explaining."
- High sailor: "Is the list a boat?" then "The clipboard is breathing. It's fine."
- Verdict, drunk enemy: "NUDGE. MERCY UP 5. HE IS DRUNK 3."
- Verdict, high enemy: "SOFTEN. MERCY UP 30. HE IS HIGH 2." (30, not 20: the swing is the status working.)
- Hero drunk hint: "YOUR WORDS HAVE WEIGHT." Hero high hint: "YOU HAVE FORGOTTEN THE QUESTION."

The word on the tag is plain DRUNK, not a slang that reads differently in Seattle and in Southampton. The register
lives in the reply lines, where it can be funny without the mechanics being cute. Nothing real is named: no chain, no
brand, no logo. The vibe is the cheap pint and the sticky carpet, not a company.

## 5. Items: the side effect is data

The engine today uses `items[0]` and adds `heal` (`pp_battle_begin_action`, `pp_battle_director.gml:620`), and
`tools/check_data.py:552` requires a consumable to carry `heal` and `max_carry`. The design keeps that path as the
default and adds an optional `use` block. A row with no `use` behaves exactly as the salve does today, so the
existing tests and the party's two salves do not move.

```json
{
  "id": "beer_can",
  "kind": "consumable",
  "name": "Warm Beer Can",
  "description": "It has been in a bag. It has opinions.",
  "sprite": "spr_pp_can",
  "max_carry": 4,
  "use": {
    "verb": "throw",
    "target": "enemy",
    "damage_min": 2,
    "damage_max": 6,
    "hit_chance": 100,
    "apply": [{ "status": "drunk", "turns": 3 }],
    "lines": {
      "use":   "* You lob the {name}. It does not open so much as give up.",
      "hit":   "* {damage} damage. The deck smells like a Tuesday.",
      "apply": "* {enemy} IS DRUNK {turns}."
    }
  }
}
```

- `target` is `enemy` or `self`. The tenth item is a row: a kebab that clears both statuses is
  `"use": {"target": "self", "heal": 2, "clear": ["drunk", "high"]}` with no GML edit. A rum and coke that leaves you
  drunk and them drunk is the same row with two entries in `apply` and `"target": "both"`.
- `damage_min` and `damage_max` stay inside spec 07's 2 to 12 band; the checker enforces it, so an item cannot
  quietly out-damage FIGHT.
- The damage floor, the popup, the shake and the enemy turn are the existing paths: the item calls `pp_battle_hurt_enemy`
  and the status applier, so a throw spends the turn like any other command.
- One new art name, `spr_pp_can`, drawn as a 3 frame arc the same way the knife's `slash_frames` work. That is art,
  queued through the existing sprite pipeline, not code.

Checks that make the tenth item safe to add (all text, no GameMaker needed):

- `tools/check_data.py` refuses an item whose `use.apply[].status` is not a row of `statuses.json`, a `turns` outside
  1 to 9, a `target` outside the two words, a damage band outside 2 to 12, or a sprite the art index does not hold.
- `tools/check_data.py` refuses a status whose `role` is not a role of `data/palette.json`, whose `label` is longer
  than 6 cells, whose `tag` is not one cell, or whose any line is longer than 28 columns or holds a glyph the sheet
  lacks (the same rule `pp_talk_line_drawable` already applies to replies).
- A pytest row asserts that no file under `game/scripts` contains the string `drunk` or `high` as an id, because the
  proof that item ten is data is that the engine does not know the name.

## 6. The budget

- **Screen.** 256 by 240, and not one new window: the enemy tag rides the plate's existing label line (8 cells, exact
  fit before the bar at x 80), the hero tag rides the command band's empty right column (7 cells inside the border at
  247). No new row, no new box, no shifted label.
- **Colours.** 25 on screen, and no entry is added. `data/palette.json` is frozen at 54 with an append only rule; DRUNK
  uses the wine family and HIGH the violet family, both already there. A status spends one role at a time, as ink and
  a 1 pixel rule. No blend, so no off palette pixel (the BATTLE-DIM finding is the precedent).
- **Data, not magic numbers.** New file `data/statuses.json` (format 1, kind statuses) with two rows to start. New
  optional blocks in `data/items.json`, `data/talk_cards.json` and `data/schemas/`. Two new geometry numbers in
  `data/ui_layouts.json` battle_b (`plate.status_x`/`status_y`, `command.status_x`/`status_y`), so the offline
  renderer and the draw call read one source. GML gains readers, not constants.
- **Nothing else moves.** No new save key (`specs/11-save.md`), no new ledger counter (`specs/10-route-ledger.md`), no
  new command, no EXP, and the overworld is untouched. `specs/07-battle-director.md` lists status effects as out of
  scope; accepting this design means that line moves to a new `specs/23-statuses.md` as a delta, not a rewrite.

## 7. What the comedy is, and what it is not

- It is the register of a cheap night out: the can, the sticky carpet, the bouncer, the nan on the karaoke. The
  comedy lands in replies and item lines, in the box the game already has.
- It is not a joke in the numbers. A player who never reads a line still understands drunk (the bar wanders, the hits
  are bigger) and high (the words crawl, the talking lands harder).
- It is not real names. No chain, no brand, no logo, no real drink. And no borrowed gag: the lines above are written
  here, and the throw-the-can idea is Nayil's own.

## 8. If he says build, in this order, each step with its check

1. `data/statuses.json`, its schema, the `check_data` rules, and the two tags drawn from data. Check: `python
   tools\check_data.py` and a pytest that a status with an unknown role, a 7 cell label or a bad turns value is
   refused with the file and field named.
2. The `use` block and the beer can row, with the salve path first proved unchanged. Check: the existing item and
   knife tests, plus a test that a throw applies `drunk` and spends the turn.
3. TALK pools and the verdict suffix. Check: every baked row and card pool with no status answers byte identically to
   today, and a drunk row is chosen only while drunk.
4. The four fight effects (bar wobble, damage ceiling, pattern offset, skip roll, text divisor). Check:
   `tools/render_battle_visuals.py` measures both tags inside their slots and no pixel of the frame outside the
   palette's roles; a fight run in the Python mirror reproduces the wobble and the skip from the fight seed.
5. Optional last: the live bridge carries `status` in its request, and the tape rows may carry it. Every existing row
   keeps its behaviour without the field.

Rough size, stated honestly: steps 1 to 3 are a day of data and one GML reader; step 4 is the only part that touches
the fight loop and the arena, and it is where I would expect the cost. Nothing here is proven by a playtest until
Nayil opens GameMaker; the checks above are text and sampled frames, and they will say so.

## 9. The three questions I cannot answer for him

1. Does the hero get drunk on purpose (a pint item that targets self) or only by accident (an enemy throws it back)?
   The design supports both; the answer decides whether the first slice needs a self target item and the drunk hint.
2. Is the can an ITEM (consumed from the four slots, as written here) or a FIGHT weapon with a throw frame? The
   direction says item, so this design spends the turn from the ITEM row; a weapon version would be a different band
   and a different sprite queue.
3. Does the register reach the overworld (the quay sways, strangers comment) or stay inside fights? Everything above
   is fight only, and I would keep it there until the three ranks are done.
