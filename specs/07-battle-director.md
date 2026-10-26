# Spec 07: battle director

Status: spec, 2026-10-19. No code yet. Numbers are DECISIONS.

Goal: a framed battle field, the player on the left, the enemy on the right, a five entry menu. Pick an action, it
resolves with numbers, the enemy answers with a dodge phase (spec 08) or a scripted beat. SPARE ends a fight without a
kill. No experience points exist anywhere.

Turn flow: 30 step encounter flash, 12 step frame slide in, menu. Player turn resolves with 20 steps of message. Enemy
turn telegraphs 12 steps, runs its pattern, then 20 steps. Repeat until an end condition. 30 step victory or defeat,
then the result returns to the caller.

| Action | Behaviour | Numbers |
| --- | --- | --- |
| FIGHT | timed bar sets power | sweeps 0 to 100 in 60 steps; damage 2 to 12 |
| POWER | spend a god power earned earlier | each power is data: name, cost, effect |
| TALK | up to 4 context options from enemy data | adds 1 trust, never damages |
| SPARE | peaceful end | enabled at trust 3 or enemy hp at 25 percent or less |
| ITEM | healing items, 4 slots in the demo | effect from item data |

Rules
1. Cursor starts on FIGHT each turn and remembers its position within the battle. Cancel backs out one level and does
   nothing at the top level. A disabled entry draws in the second ink, makes a low blip, and never silently no-ops.
2. Only the dodge phase damages the player. Menu text and talk never do.
3. Turn order is player then enemy for the whole demo; no speed stat.
4. Every enemy is beatable without killing; an exception needs an explicit data flag and the ledger still records it.
5. Rewards are god powers, items and health upgrades only.
6. Message text uses spec 05 in the upper area; the arena never draws the director's menus.
7. The director asks spec 08 for a pattern and waits; it never spawns hazards itself.

Health: player 20 at start plus 4 per upgrade found, carried across battles, restored only at save points. Navy Sailor
15 hp and attack 2; Percy 120 hp and attack 3 to 6 with three patterns; Hector 140 hp with two; Kronos 180 hp with
three, where the ending forces kill on the genocide route and spare otherwise, so the opposite entry is refused
visibly. Damage is a whole number, floored at 1, shown as a popup for 24 steps.

Enemy data: id, name, sprites, max hp, attack, pattern list, talk options, spare condition, drops, route contribution.

Party stat line: one row of 8 px glyph cells at x 16, y 156, over the paper field, in the text ink. The row is one
string, the current value then its maximum for each of the two numbers, three spaces between the pairs: the literal
`HP`, a space, the current hp, a slash, the max hp, three spaces, `WILL`, a space, the current will, a slash, the
max will. At the demo's party values (max hp 20, will max 3) it reads `HP 20/20   WILL 3/3` and one pp_font_draw
call draws it. The battle screen spends four roles and no others (ink, paper, dim, text); this row is the text one.

- The demo's row is 19 characters, 152 px, x 16 to x 167, which is what the game draws today.
- The widest case the draw site's own comment claims is 22 characters, 176 px, x 16 to x 191, which that comment
  writes as x 16 to x 192: inside the 256 x 240 frame, and it leaves rows 164 to 167 clear above the menu band at
  y 168 (PP_MENU_TOP, pp_config.gml:37).
- HP and WILL share the row and the one draw call, so a card that moves or reformats one of the two states what it
  does to the other instead of moving it alone, and any change that lengthens the row is measured against the
  widest case above.
- Read from frames, not from the call site alone: the two t_014b8496 captures (HP 20/20 and HP 18/20 on the same
  battle screen) read cell by cell at 3x give x 16 to x 167 in 19 cells, glyph rows 156 to 162 inside the 8 px cell
  at y 156 to 163, and `python tools/preview_battle_font.py` prints the same x 16..167 y 156..163 for the line.

PP content: the Navy Sailors tutorial, Percy on the small ship, Hector in the data center, Kronos in the AI OS room,
and the Titan employees in One North Quay. Powers taken from enemies are the only power curve, which is what no EXP
means here.

Acceptance (Nayil)
1. Winning by FIGHT gives damage between 2 and 12 and always a dodge phase in reply.
2. Three TALKs then SPARE ends the same fight with different victory text.
3. A disabled entry makes a sound and does not advance the turn.
4. Reaching 0 hp plays defeat once and returns to title with the save intact.
5. Changing Percy's hp in data to 60 changes the fight with no code edit.

Out of scope: several enemies at once, guard, status effects, flee.
