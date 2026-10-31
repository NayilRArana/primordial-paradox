# Spec 17: action movement, the jump, the whip and the knockback

Status: spec, 2026-10-22. Card t_f5a7ca5c, ROADMAP-2026-10-22 R01, steps S3 and S6. No code yet. Numbers are
DECISIONS unless a source is named.

Source of every number here: `knowledge\mechanics\ACTION-MECHANICS.md`, cited in this file as A-M, sections 6, 7 and 8
and its P lines 1 to 5. That study's own decision ids are cited too (JMP, WHP, KNB, IFR), so a reader can find the
paragraph a number came from instead of trusting this file.

How to read a citation in this file:

- `(A-M section 6)`, `(A-M section 7, WHP-01)`: the number is stated there and this spec adopts it unchanged. If the
  two ever disagree, A-M wins and this file is corrected.
- `[inference]`: the number is not in A-M. It is either arithmetic over A-M numbers (the arithmetic is printed here) or
  a choice this spec had to make to be implementable at all. Every one of them can be changed without changing a cited
  number, and each is a candidate for A-M to adopt or overturn.
- `(spec NN)`: a number or rule that belongs to another spec, cited rather than restated.

Goal: in an action room the player walks, jumps a fixed arc, uses one whip with three tiers, and is thrown back by a
hit. Nothing in here is variable height, air control, running, wall jumping or a slope: one arc, one whip, one
knockback, all in whole pixels, so a gap and a reach are a yes or a no and a script can check them before the game
runs.

## 0. What this spec owns, and the two gaps it cannot close

This spec owns the section 6 and section 7 numbers of A-M: walk and stairs, the jump arc, the whip tiers, the
knockback, the deep landing stun, and the debug tools the study names in section 10. It does not own the dodge arena
marker (spec 08), the battle FIGHT bar (spec 07), the bullet patterns (spec 09), room data (no spec defines it yet,
see SPEC-DELTAS M1) or any art (spec 13).

Gap 1, the whip question. A-M section 11 leaves Q1 open: does the action segment get a whip at all, or is the whip a
battle verb only? The card that ordered this spec orders the whip tiers written, which is the reading this file takes.
It is recorded again as an open question in section 8 item 1 rather than treated as answered, and section 3 is written
so that a "no whip in the corridors" answer removes it cleanly: sections 1, 2, 4 and 5 stand, section 3, the whip half
of section 5 and debug tool T2 fall away, and no other number moves.

Gap 2, the rooms. Every room that exists today is a top down 16x16 tile map: spec 04 walks the player freely, in
pixels and in eight directions, across one, and spec 15's ship sample gives stairs and ladders as exits between maps. A-M
sections 6 and 7 describe a side on surface with gravity, a landing and a fall. So this spec defines movement for a room
kind that does not exist in the room data
yet, and it does not convert any existing map. Which rooms become action rooms is section 8 item 4, and spec 01's mode
table has no action mode, which is section 8 item 3.

## 1. Walk and stairs

The action room has one ground plane and gravity. Horizontal is the only ground input, so there is no diagonal walk
[inference: A-M section 6 gives horizontal speed only, and the vertical axis is gravity's].

| Fact | Number | Source |
| --- | --- | --- |
| Walk speed | 1 pixel per step | A-M section 6, JMP-04 |
| Stair speed | 0.5 pixel per step | A-M section 6, JMP-04 |
| Stairs are a mode, not a slope | a stair tile switches the mode; no slope geometry exists | A-M section 6 gives the half speed and the no-landing rule; the phrase is JMP-04's, in `data\mechanics\action_recipes.json` |
| Landing on stairs | never | A-M section 6 |
| Jumping from stairs | allowed | `data\mechanics\action_recipes.json`, JMP-04 params |
| Crossing the 256 pixel frame on foot | 256 steps, 4.27 s | [inference: 256 / 1 per step at 60 steps per second, spec 01] |
| One 16 pixel block of stairs | 32 steps | [inference: 16 / 0.5, and spec 03 rule 3 snaps the drawn position, so the pixel advances every second step] |

Rules

1. Steps are 60 per second (spec 01). A-M counts in frames and this spec counts in steps; one step is one frame
   [inference: the two are the same clock at 60 per second, spec 01].
2. Horizontal speed is identical walking, jumping and being knocked back, 1 pixel per step (A-M section 6). There is no
   running, no acceleration and no momentum to build.
3. Facing is left or right and follows the last horizontal direction held; it changes on the step of the press. The
   whip and the reach box use facing only, never an up or down direction [inference: A-M section 7 gives one reach per
   tier and no vertical reach].
4. Position maths may carry a fraction; every drawn position is snapped to whole pixels first (spec 03 rule 3), so the
   half speed of stairs never produces a half pixel on screen.
5. A stair tile is climbable, not standable: a jump that passes through a stair tile keeps falling through it
   (A-M section 6, "you cannot land on stairs").
6. The overworld's free walk in pixels, in eight directions, is spec 04's (rule 1, changed 2026-10-26 by Nayil's order,
   card PP-FREE-MOVE) and is not touched by this spec. This section applies to action rooms only.

Open, and not decided here: A-M section 11 says whether walk speed stays 1 pixel per step in the action segment is
deliberately left alone. This spec carries JMP-04's 1 pixel per step and nothing else, and section 8 item 7 repeats
the question.

## 2. Jump

One input action, one press, one whole arc. The button is a command, not a throttle: no variable height, no air
control, no double jump (A-M section 6, JMP-01, P4).

| Fact | Number | Source |
| --- | --- | --- |
| Startup, on the ground | 4 steps | A-M section 6, JMP-01 |
| Air, to flat ground | 40 steps | A-M section 6, JMP-01, P4 |
| Press to flat landing | 44 steps | [inference: 4 startup + 40 air] |
| Apex | 42 pixels above the takeoff ground | A-M section 6, JMP-01, P4 |
| Apex in blocks | 2.625 of 16 pixels, quoted in A-M as about 2.6 | A-M section 6 |
| Ground covered on a flat jump | 40 pixels, 2.5 blocks | [inference: 40 steps x 1 pixel per step; JMP-01 states the same 40 pixels] |
| Vertical clearance | 2 blocks | A-M section 6 |
| A 3 block gap | clearable from the ledge edge only | A-M section 6 |
| Air control | 0; horizontal speed committed at takeoff | A-M section 6, JMP-01 params |

Rules

1. During the 4 startup steps the player is grounded, still walks at 1 pixel per step, rises 0 pixels, and the jump
   cannot be cancelled. A second press inside startup is ignored, so one press is one jump [inference: A-M gives the
   4 step startup and no cancel, and a jump that could be re-triggered inside it would be a variable height in
   disguise, which P4 forbids].
2. The horizontal speed at the step the player leaves the ground is the speed for the whole arc, 1 pixel per step
   (A-M section 6). If the player lets go of the direction in the air, the player still travels: no air control means no
   air braking either [inference: "no mid air steering" read as no change in either direction].
3. The arc is a preset table, not force plus gravity, so the same press gives the same arc twice in a row (A-M
   section 6). This spec does not publish 40 invented rows. It publishes eight integration checkpoints the table must
   hit, and the debug overlay draws the table that ships, so the check compares the table to A-M rather than to a
   formula:

| Step | Height above takeoff ground | Why this point |
| --- | --- | --- |
| 0 | 0 pixels | takeoff, the last grounded step |
| 20 | 42 pixels | apex, A-M section 6 |
| 29 | 32 pixels, descending | a landing 2 blocks higher ends here, A-M section 6 and JMP-02 |
| 36 | 16 pixels, descending | a landing 1 block higher ends here, A-M section 6 and JMP-02 |
| 40 | 0 pixels | a flat landing ends here, A-M section 6 and JMP-02 |
| 42 | 16 pixels below takeoff | a landing 1 block lower ends here, A-M section 6 and JMP-02 |
| 44 | 32 pixels below takeoff | a landing 2 blocks lower, A-M section 6 and JMP-02 |
| 46 | 48 pixels below takeoff | a landing 3 blocks lower, A-M section 6 and JMP-02 |

All eight rows of that table are [inference] in their placement, and every one of them is fixed by a cited number: the
apex at step 20 assumes an arc symmetric in time over 40 steps, and the three rows below takeoff fix the fall after
step 40 at 8 pixels per step, because 1 block is 2 steps and 2 blocks is 4 steps (16 / 2 = 8; JMP-02). The steps
between checkpoints are free as long as the height rises from step 0 to step 20 and falls from step 20 to step 40, and
the table commits in data so a change is one edit, not a code change.

4. No single symmetric parabola satisfies both the apex and the six landing rows of A-M exactly: a symmetrical arc that
   is 42 pixels high at step 20 passes 32 pixels at step 30, and A-M's table says 29. The six landing rows win, because
   they are the cited numbers and the ones level design is checked against; the apex step is what bends to fit them.
   Recorded so nobody rediscovers it as a bug [inference, arithmetic over A-M section 6].
5. A ceiling or a stair tile ends the rise without ending the jump: the player keeps the remaining arc and falls
   [inference: A-M section 6 gives one arc per press and no ceiling case].
6. The jump does not exist in the dodge arena. The marker moves 2 pixels per step in 8 directions and has no vertical
   axis of its own (spec 08 geometry), and A-M section 6's numbers are the action segment's. A jump press in the arena
   does nothing.
7. A deep landing after a jump is section 5's rule, not a variant of the jump: the arc is identical and only the
   stun differs.

## 3. Whip

Three tiers, one button, one direction. The whip is the action segment's attack and it does not exist in battle, where
FIGHT and its timed bar are the verb (spec 07).

| Tier | Reach | Damage | Animation | Hit lands | Recovery after hit | Total after a hit |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 24 pixels, 1.5 blocks | 2 | 12 steps | step 8 | 4 steps | 16 steps [inference: 12 + 4] |
| 2 | 28 pixels | 3 | 12 steps | step 8 | 4 steps | 16 steps [inference: 12 + 4] |
| 3 | 48 pixels, 3 blocks | 3 | 14 steps | step 9 | 5 steps | 19 steps [inference: 14 + 5] |

Every column except the last is A-M section 7's decision table (WHP-01, WHP-02, WHP-03, P5).

Rules

1. Reach is measured from the front edge of the player's hitbox, in whole pixels, in the facing direction. It is a box
   as wide as the reach and as tall as the player's hitbox, drawn as a 1 pixel outline by debug tool T2. No spec fixes
   the player's hitbox size yet (section 8 item 8), so the reach is defined from the edge and stays correct whatever
   the art does.
2. The reach box is active on the hit step only, step 8 or step 9 by tier; a target inside the box on that step takes
   the damage once per swing (A-M section 7 gives one hit step per tier, and a second hit inside one swing would be a
   different weapon).
3. A miss costs the whole animation, 12 steps at tiers 1 and 2 and 14 at tier 3. A hit costs the animation plus
   recovery, 16 and 19 steps (A-M section 7, WHP-04). Two presses are therefore 12 or 14 steps apart after a miss and
   16 or 19 apart after a hit, and that asymmetry is the combat.
4. Tier 2 is a damage tier: it adds 4 pixels of reach and 1 damage over tier 1 (A-M section 7, WHP-02). Tier 3 keeps
   the damage at 3 and adds 20 pixels of reach with 2 more steps of animation (A-M section 7, WHP-03).
5. A whip that misses still swings: there is no cancel inside the animation, and pressing the button again during it is
   ignored [inference: A-M section 7's miss cost is only meaningful if the animation cannot be cancelled].
6. The whip can be started in the air. It does not change the arc, the horizontal speed or the landing (A-M section 6
   keeps one arc per jump), and a whip started in the air is the only thing that cancels a deep landing stun
   (section 5).
7. The tier is a player field, `whip_level` in save data, 1 to 3. This spec does not set how a tier is earned: the
   recipes file carries an upgrade gate by hearts (WHP-05) that A-M sections 6 to 8 do not state, and hearts and
   subweapons are not in any PP spec. Section 8 item 6 keeps that question open rather than adopting it here.

## 4. Knockback

The player is ejected on a hit in an action room, and not in the arena, where the marker is never thrown (A-M
section 7, KNB-01).

| Fact | Number | Source |
| --- | --- | --- |
| Horizontal distance | 16 pixels, 1 block, away from the hit's side | A-M section 7 |
| Rise | 10 pixels | A-M section 7 |
| Horizontal speed | 1 pixel per step, the walk speed | A-M section 7, KNB-01 |
| Arc length to the same ground | 16 steps | [inference: 16 pixels / 1 per step] |
| Rise peak | at step 8, the middle of the arc | [inference: symmetric about the arc's middle, 16 / 2] |
| Control | locked until landing | A-M section 7, KNB-01 |
| Invulnerability | 30 steps, starting on the landing step | A-M section 7, and 30 is A-M section 3's IFR-01 number, P2 |
| Invulnerability blink | every 4 steps | A-M section 3, IFR-02 |
| Total protection from the hit | 46 steps | [inference: 16 steps of arc + 30 after landing] |

Rules

1. Direction is a field, `knockback_dir`, written by whatever applied the damage, values left and right. It is never
   read from the player's facing (A-M section 7, KNB-02).
2. The arc ignores current momentum. A hit taken in mid jump drops the player out of the jump, and the jump is lost:
   there is no resume when the knockback ends (A-M section 7, KNB-01).
3. The arc is 16 steps of horizontal travel at 1 pixel per step, with the vertical offsets following the same preset
   table idea as the jump, rising 0 to 10 pixels by step 8 and returning to 0 by step 16 [inference: A-M gives the
   rise and the speed, not the shape].
4. If a wall interrupts the horizontal travel, the horizontal stops at the wall and the arc finishes its rise and fall
   in place. If the ground below is gone, the arc ends and the player falls, and that fall counts for section 5's
   landing rule [inference: A-M section 7 states no wall or pit case, and a room can hold both].
5. The 30 step invulnerability window starts on the landing step, not on the hit, which is the one place A-M section 3's
   landing rule attaches: there, the knockback is a fixed ejection that already removes control. The arena keeps the
   on-hit start, because the marker is never ejected (A-M section 3, IFR-03).
6. A knockback landing never causes the deep landing stun: the arc rises 10 pixels and section 5's threshold is 4
   blocks, 64 pixels (A-M section 6, JMP-05) [inference: 10 is under 64].
7. A hit costs the enemy's attack value, minimum 1, and the value never scales with the stage (A-M section 8 damage
   floor, and section 8's last row, P3).
8. Level rule, and it is a checker's job, not a reviewer's: no pit edge within 16 pixels of the hitbox of an enemy that
   survives one whip (A-M section 7, KNB-03). A one whip enemy beside a ledge is a coin flip that looks like a mistake.
9. Conflict on the record: spec 07 rule 2 says only the dodge phase damages the player. An action room is a second
   damage source, so that rule needs the words "in battle" before this section can be implemented. Section 8 item 5.

## 5. Landing

Landing covers two things that are easy to confuse: the jump's air time depends on the height of the ground it lands
on, and a long fall costs control for 10 steps.

Air time by landing height. The air steps column is A-M section 6 and JMP-02; the ground covered column is one pixel
per step [inference: air steps x 1 pixel]:

| Landing | Air steps | Ground covered | Source |
| --- | --- | --- | --- |
| 2 blocks higher | 29 | 29 pixels | A-M section 6, JMP-02; ground covered is [inference: steps x 1 pixel] |
| 1 block higher | 36 | 36 pixels | as above |
| level | 40 | 40 pixels | as above |
| 1 block lower | 42 | 42 pixels | as above |
| 2 blocks lower | 44 | 44 pixels | as above |
| 3 blocks lower | 46 | 46 pixels | as above |

Rules

1. The player lands the step the feet reach the ground, and the air time is read from the arc table, so a jump onto a
   ledge ends early and a jump into a pit keeps falling (A-M section 6, JMP-02). The debug overlay prints the step
   count on landing so the table can be compared with this one.
2. A fall of 4 blocks or more, 64 pixels, forces a crouch and a 10 step loss of control (A-M section 6, JMP-05, P4).
   16 pixels is one block (spec 04's tile size).
3. A fall of 3 blocks, 48 pixels, costs nothing: the threshold is 4 or more [inference: JMP-05's number is the
   threshold, and a fall of exactly 4 is in].
4. During the 10 steps the player has no horizontal input and no jump; the whip is allowed, and that is the whole point
   of the rule (A-M section 6: a whip timed to end on the landing frame cancels it).
5. The cancel is exact, not approximate: the attack's last step must be the ground contact step. From the press that is
   12 steps at tier 1 and 2 on a miss, 16 on a hit, and 14 at tier 3 on a miss, 19 on a hit [inference: the animation
   plus recovery of section 3]. A press one step early or later leaves the full 10 step stun. Both outcomes must be
   reachable in the debug room, which is what the acceptance check tests.
6. A deep landing grants no invulnerability. The 30 step window belongs to a hit, not a fall [inference: A-M section 3
   attaches the window to a hit and JMP-05 attaches the stun to a fall, and nothing joins them].
7. Landing on stairs is not a landing at all (section 1 rule 5): the player passes through and keeps falling.
8. None of this exists in the arena, which has no gravity (spec 08).

## 6. Debug tools

Three tools, all behind `PP_DEBUG`, the compile time constant of spec 01, so a release build holds no debug draw call
at all. SPEC-DELTAS M3 names the debug switch itself as a gap; it is spec 01's constant and this spec only uses it.

| Tool | Key | What it draws |
| --- | --- | --- |
| T1 jump arc overlay | F4 | the shipped arc table as dots, the 16 pixel block grid, the takeoff column, and the six landing rows from section 5 each labelled with its step count, in the brightest ink so the grid never hides them |
| T2 reach box, per whip level | F5 | one reach box at tier 1, 2, 3 and off; the exact width from section 3, a 1 pixel outline in the brightest ink, the active hitbox drawn only on the hit step, and the tier, reach and hit step printed in the 8x8 font |
| T3 movement readout | F6 | x and y in whole pixels, ground mode as floor, stair, air or stun, the step inside the jump as n of 40 air steps (0 to 4 during startup, then 1 to 40), the stun counter, the invulnerability counter and `knockback_dir` |

Rules

1. F1, F2 and F3 are taken: debug warp, single step and debug flags (spec 02). F2 is the step advance these tools are
   read against, and spec 08 already uses it for the arena (spec 08 debug). F4, F5 and F6 are free as of this spec
   [inference: they are the next three function keys after spec 02's F1 to F3].
2. T1 draws the table that ships, not a formula, because section 2's checkpoints are the contract and a formula would
   hide a table that drifted (section 2 rule 4). If the table and the checkpoints disagree, T1 shows the disagreement.
3. T2 must be able to hold a tier: F5 cycles and the chosen tier stays until it is cycled, so a designer can place a
   dummy at exactly 24, 28 and 48 pixels and see the box edge touch it.
4. T3 is the only place the air step and the stun counter are readable, so it is the tool the acceptance checks in
   section 7 are read from. Every number it prints is a whole number (spec 13, whole numbers for the font).
5. One debug room, 256x240 like the frame (spec 03), holding a 3 block gap, a ledge 1 block up and a ledge 2 blocks
   up, a 4 block drop, one stair, and three dummies at 24, 28 and 48 pixels from a standing position. Its room file
   name and format belong to whoever defines room data (SPEC-DELTAS M1), and this spec fixes only its contents.
6. No debug draw in a release build, and a grep for the debug keys outside this section and spec 02 is a review
   failure [inference: the same shape as spec 02 rule 1, applied to the draw side rather than the input side].

## 7. Acceptance

Nayil, by playing the debug room:

1. Walk a flat 256 pixel room: it takes 256 steps and the sprite never shows a half pixel; walk one block of stairs:
   it takes twice as long as a flat block, with no stutter.
2. Jump ten times from the same standing spot and release the button at ten different moments: one arc every time, and
   holding the button never goes higher. Jump from each of the six landing heights and read the step count off T1 and
   T3: it matches the section 5 table row for row.
3. Put a dummy at exactly 24 pixels and one at 26: tier 1 hits the first and not the second. At tier 3 a dummy at 48
   is hit and one at 50 is not. Two swings after a hit are 16 steps apart, after a miss 12, counted on F2 single step
   with T2 showing the tier.
4. Take a hit standing, then the same hit in mid jump: the same distance from the attacker both times, no control until
   landing, and about half a second of blinking after landing.
5. Fall 3 blocks: no stun. Fall 4 blocks: 10 steps of crouch with no input. Repeat the 4 block fall with a whip pressed
   so its last step is the contact step: control on the landing step. Then press one step early and one step late: the
   stun is back. No debug drawing appears in a release build.

Machine checks, to be written by the cards that implement movement. This card writes this file and no code, so none of
these exist yet and none is claimed:

1. M1: a test reads the shipped arc table and asserts the eight checkpoints of section 2 to the pixel.
2. M2: a test places a target at reach and at reach plus 2 for each tier and asserts hit and miss, and asserts the hit
   step is 8, 8, 9.
3. M3: a test measures press to press as 16 after a hit and 12 after a miss at tier 1, and 19 and 14 at tier 3.
4. M4: a test drives a fall of 3 and 4 blocks and asserts no stun and 10 steps of stun, then asserts the cancel fires
   at exactly 12, 16, 14 and 19 steps of lead.
5. M5: a test takes one hit standing and one in the last air step and asserts equal final distance from the attacker
   and one lost jump.
6. M6: a script walks every room that holds an action room and names every pit edge inside 16 pixels of a hitbox of an
   enemy that survives one whip (A-M section 7, KNB-03), printing room, tile and enemy.
7. M7: a grep for the T1 to T3 draw calls and for the F4 to F6 keys outside `PP_DEBUG` and spec 02 fails the commit.

## 8. Deltas and open questions, for the manager and for gamedev

1. Q: the whip question, A-M section 11 Q1, is still open. Does the action segment get a whip, or does Percy use the
   whip only in battle? This spec takes the ordering card's reading, that it does. If the answer is no, section 3, the
   whip half of section 5 and debug tool T2 fall away and nothing else changes.
2. D: spec 02's action table has no jump and no attack, and its rule 1 forbids reading a key anywhere else. Proposed
   bindings, to be decided with spec 02: `jump` = C and the pad's left face button, `whip` = V and R1. C and V are
   free (SPEC-DELTAS C6 fixed confirm to Z, Space, Enter and menu to Tab and Start).
3. D: spec 01's mode table has no action mode. Either it gains one row (`action`, owning move, jump, whip and confirm
   on doors) or the action room is the overworld with a pixel movement kind. This spec assumes neither and adds no
   mode, because a mode table is spec 01's to change.
4. Q, the biggest one: A-M sections 6 and 7 describe a side on room with gravity and landings, while spec 15's ship
   sample and spec 04's overworld are top down tile maps whose stairs and ladders are exits to another map. Which rooms
   are action rooms, and does the ship corridor become a side on room or keep the top down map it has? This spec cannot
   answer it and does not convert a map.
5. D: spec 07 rule 2 says only the dodge phase damages the player. An action room damages the player on contact, so the
   rule needs the words "in battle": in battle, only the dodge phase damages the player.
6. Q: the whip's upgrade gate is in `data\mechanics\action_recipes.json` as WHP-05, 4 hearts for tier 2 and 8 for tier
   3, no subweapon on screen, lost on death. A-M sections 6 to 8 do not state it and hearts and subweapons are in no PP
   spec, so this spec does not adopt it. The tier the player holds is `whip_level` and how it is earned is open.
7. Q: A-M section 11 leaves the action segment's walk speed undecided. This spec carries 1 pixel per step (JMP-04) and
   the 4.27 s frame crossing that comes with it.
8. D: no spec fixes the player's hitbox size in an action room; spec 13 fixes sprite sizes for battle sprites. The reach
   box is defined from the hitbox's front edge so it holds at any size, but a pixel exact hitbox rect is owed by spec 13
   or by room data.
9. Not in this spec: the dodge arena marker and its slow key (spec 08, which is A-M section 2's P1 and not this spec's
   to restate), the FIGHT bar (spec 07), bullet patterns (spec 09), boss phases and rule changes (spec 18), room data
   formats (SPEC-DELTAS M1), and any art or sound.
