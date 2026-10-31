# Review of specs 17 and 18, 2026-10-22

Card t_eab7904b, ROADMAP-2026-10-22 R17, steps S3 and S6. Reviewer: code-review, this run only. The two specs are
read as a coder would read them, not as an editor: the test is whether code can be written from the text without
asking a question, whether every field has a type and a range, and whether every number stands against its source.

## Verdict

| Spec | Verdict | Why |
| --- | --- | --- |
| `specs/17-action-movement.md` | FAIL, against sha256 `5f52dcd2`, the 340 line text read at 13:50 and verified again on disk at 14:17 | Five blocking findings. The deep landing cancel contradicts itself, the shipped arc table has no data home, the three new debug keys have no row in spec 02, `whip_level` has no type and no key in spec 11, and the proposed action mode would be a second owner of the confirm door rule. |
| `specs/18-boss-phases.md` | FAIL, against sha256 `dfaa8b8e`, commit b066c64, the 512 line text committed at 14:40:42 | Seven blocking findings. The chosen interrupt scene id has no consumer in spec 06, the 30 step break has no home in spec 07's turn flow, acceptance 7 needs a refusal section 7 does not list, the widest phase label falls 8 pixels outside spec 05's text area, the slow key spec 08 does not have, C18-2 omits `unless_flag` from the schema delta, and the attack band is undefined against the row's own 3 to 5. |

## The two spec files left the tree for about five minutes, mid review

This is worth the manager's attention even though it ended well, because both files were untracked.

| Time | What was observed |
| --- | --- |
| 13:50 to 13:53 | `specs/17-action-movement.md` read in full, 340 lines, sha256 `5f52dcd2`, mtime 13:20:16. `specs/18-boss-phases.md` read in full, 440 lines, sha256 `63287b9f` recorded at 13:57. |
| 13:57 to 14:05 | Spec 18 rewritten in place by card t_00a94c86: sha256 `cf265d5e` at 14:00:15, `c62bf910` at 14:00:54, `158864f2` at 14:04:57, 460 lines at 14:01. |
| 14:09 | Two rows added to `knowledge/SPEC-REVIEW.md` for specs 17 and 18. |
| 14:10:17 | Commit 10ec031 lands ("clean_code: cover primordial-paradox in the gate roots"). |
| 14:11:41 | `python tools/check_spec_review.py` reports **16 specs**, not 18. `ls specs/` shows files 01 to 16 only. Both files absent. |
| 14:17 | Both files are on disk again. Spec 17 hashes to `5f52dcd2`, 340 lines, mtime 13:20:16, so it is byte identical to the reviewed text. Spec 18 hashes to `8400125b`, 519 lines, 38406 bytes, mtime 14:11. |
| 14:20:06 | The checker reports 18 specs, 2 pending, 0 problems, and its output is printed below. |
| 14:25:28 | Commit 43b6fe6 lands ("gamedev: spec 18, the five boss phase questions answered"). `specs/18-boss-phases.md` is now tracked, sha256 `adb31da2`, 512 lines. `specs/17-action-movement.md` is still untracked. |
| 14:40:42 | Commit b066c64 lands ("gamedev: spec 18, the crossing threshold numbers stated exactly"). Section 0 item 9, section 4 and A18-1 only, 13 insertions and 13 deletions. Sha256 `dfaa8b8e`, 512 lines. This is the text the verdict above is against. |

The likely shape is a move out and back, since both mtimes were preserved, but which operation did it is not something
this review can prove and I am not guessing. What is certain is that both files were untracked (`git status` showed
`?? specs/17-action-movement.md` and `?? specs/18-boss-phases.md` from the start of this card), that no version of
either text is in git history (`git log --all -- specs/17-action-movement.md specs/18-boss-phases.md` is empty), and
that for those five minutes nothing in the repository, the stash, the card workspaces or `Shared/projects` held a copy.
Had the restore not happened, both specs would have been unrecoverable. Two untracked spec files vanishing during
another lane's commit is worth a rule: either a new spec is committed when its card completes, or it is copied into
the card's own record, because an untracked file in this shared tree is one cleanup away from gone. That rule now has
a working example and a live exception: card t_00a94c86 committed spec 18 at 14:25:28 (43b6fe6), so it is safe, and
`specs/17-action-movement.md` is still untracked today (`git status` shows it as `??`), so the same exposure is still
open on the other file this review covers.

This card did not delete them: it wrote only `knowledge/REVIEW-ACTION-PHASES-2026-10-22.md` and the two rows in
`knowledge/SPEC-REVIEW.md`, and no tool this card ran removes files.

Because spec 17 returned byte identical, the findings below need no re-basing: they are against `5f52dcd2`, which is
what is on disk at 14:17 and what R01 delivered.

A FAIL is not a judgment of the author's work. Both files are careful documents. The failures are specific and each
one is written below with the line, the number and the smallest fix I can see.

## The check I named before starting, and its before and after

Check named first: `python tools/check_spec_review.py --strict` must not get worse, and the review itself must name
file, line and number for every claim.

Before this run, at 13:53, with spec 17 at sha256 `5f52dcd2` (340 lines, untouched since 13:20) and spec 18 at the
440 line text:

```
check_spec_review: 18 specs, 0 still awaiting a clean-room reviewer, 2 problem(s)
FAIL specs/17-action-movement.md: no row in knowledge/SPEC-REVIEW.md
FAIL specs/18-boss-phases.md: no row in knowledge/SPEC-REVIEW.md

2 spec review problem(s)
EXIT=1
=== strict ===
check_spec_review: 18 specs, 0 still awaiting a clean-room reviewer, 2 problem(s)
FAIL specs/17-action-movement.md: no row in knowledge/SPEC-REVIEW.md
FAIL specs/18-boss-phases.md: no row in knowledge/SPEC-REVIEW.md

2 spec review problem(s)
EXIT_STRICT=1
```

After the two rows were added to `knowledge/SPEC-REVIEW.md`, measured at 14:20:06 with both spec files on disk:

```
python tools/check_spec_review.py
check_spec_review: 18 specs, 2 still awaiting a clean-room reviewer, 0 problem(s)
PENDING spec review: specs/17-action-movement.md
PENDING spec review: specs/18-boss-phases.md
check_spec_review: no malformed row, but 2 of 18 specs still await a clean-room verdict
EXIT=0
python tools/check_spec_review.py --strict
check_spec_review: 18 specs, 2 still awaiting a clean-room reviewer, 0 problem(s)
PENDING spec review: specs/17-action-movement.md
PENDING spec review: specs/18-boss-phases.md
check_spec_review: STRICT REFUSED, 2 of 18 specs have no clean-room verdict yet
EXIT_STRICT=1
```

The default run improves from 1 to 0, the strict run holds at 1, which is the correct state: neither spec is
confirmed, so the gate that an implementation card runs must still refuse. The ledger has no FAIL word, and a
`confirmed` row on either file would be the breach the gate exists to prevent, so both rows say `pending` and carry
the reason in the note. One intermediate run at 14:11 is not part of this record: it reported 16 specs because the
two files were briefly absent from the tree (see above), so its green result was an artifact of missing input, not of
these rows.

Both rows were finalised after the spec 18 verdict (its note now names `dfaa8b8e` and the seven blocking findings;
spec 17's is unchanged). The checker was re-run at 14:51:16 with both rows in their final state: the same 18 specs, 2
pending, 0 problems, exit 0, and strict exit 1. The status cell stays `pending` because the ledger has no FAIL word;
each verdict lives in the note and in this file.

`python tools/check_data.py` at 14:06: `check_data: all files pass`. It knows nothing about phases (grep for
`hp_at_or_below` and `PHASE_ATTACK_BAND` in `tools/` returns nothing), so it is not evidence for or
against spec 18's section 7, which is the delta its own section 7 records.

## Spec 17: FAIL, five blocking findings

### F17-1 (blocking) The deep landing cancel contradicts itself

`specs/17-action-movement.md` lines 241 to 246, section 5 rules 4 and 5, against lines 167 to 169, section 3 rule 6.

Rule 4 says: during the 10 stun steps "the whip is allowed, and that is the whole point of the rule". Rule 5 says the
cancel needs "the attack's last step must be the ground contact step. From the press that is 12 steps at tier 1 and 2
on a miss, 16 on a hit, and 14 at tier 3 on a miss, 19 on a hit". Section 3 rule 6 says "a whip started in the air is
the only thing that cancels a deep landing stun".

The numbers do not meet. The stun is 10 steps. The shortest whip is 12 steps. A press on the first stun step ends 12
steps later, which is 2 steps after control has already returned, so it cannot end on the contact step, and it is not
"started in the air". As written the mechanic has two rules that cannot both be implemented, and acceptance 5 and
machine check M4 both test it.

Smallest fix: in rule 4 say what a press during the stun actually does (nothing for that stun, a normal swing that
lands after control returns) and delete "that is the whole point of the rule"; or delete the whip clause from rule 4
and keep section 3 rule 6 as the only cancel path.

### F17-2 (blocking) The shipped jump arc has no data home, no key, no type and no range

`specs/17-action-movement.md` lines 104 to 124, section 2 rule 3, and lines 197 to 199, section 4 rule 3.

Line 124 says "the table commits in data so a change is one edit, not a code change". The knockback arc follows "the
same preset table idea". Neither rule names the file, the key, the row shape, the value type or the legal range, and
`knowledge/SPEC-DELTAS.md` line 63 (M1) says no spec defines the data file formats. A coder cannot write the table
loader from this spec. The card's first test, "no field without a type and a range", fails here: the arc table is a
field with no type, no range and no home.

Smallest fix: name the file and the key (`data/mechanics/movement.json`, `jump_arc` and `knockback_arc`), and give the
row shape (`{ "step": integer 0 to 46, "height": integer -48 to 42 }`) with the rule that step 0 is 0 and steps
ascend by 1. The eight checkpoints stay as the test.

### F17-3 (blocking) Three new debug keys, no rows in the one key table

`specs/17-action-movement.md` lines 259 to 261 and 265 to 267, section 6. `specs/02-input.md` line 13 and rules 1
and 6 at lines 27 and 32.

The tools bind F4, F5 and F6. Spec 02's table lists only "F1 / F2 / F3" for `debug_warp / debug_step / debug_flags`,
its rule 1 makes a read outside that module a review failure, and rule 6 says "keys live in one table so a later
options screen can read them". Spec 17's delta list, section 8 items 1 to 9, asks spec 02 for `jump` and `whip` (item
2) but never for the three tool keys. So the keys have no legal home and the M7 grep check would fail the very code
the spec asks for.

Smallest fix: add one delta line: spec 02 gains `debug_arc`, `debug_reach` and `debug_move` on F4, F5, F6, debug build
only.

### F17-4 (blocking) `whip_level` has no type and no key in the save

`specs/17-action-movement.md` lines 170 to 172, section 3 rule 7: "The tier is a player field, `whip_level` in save
data, 1 to 3." `specs/11-save.md` lines 13 to 17 list the 16 keys (`format`, `game_version`, `saved_at`,
`play_seconds`, `map`, `spawn`, `x`, `y`, `hp`, `max_hp`, `powers`, `items`, `flags`, `counters`, `seen_scenes`,
`music`) and line 19 names the only optional key, `fight_exits`. There is no `whip_level`. Spec 11 rule 3 (line 27)
says loading validates "every number in range", so a field with no type cannot be validated either.

Smallest fix: either add a delta to spec 11 for `whip_level` as an integer 1 to 3 with a default of 1 for old saves,
or stop calling it a save field and give it a home in the player state spec that owns it.

### F17-5 (blocking) The second confirm consumer, left open

`specs/17-action-movement.md` lines 321 to 323, section 8 item 3, against `specs/04-overworld-rails-and-triggers.md`
line 22 and `specs/01-state-machine.md` line 10.

Item 3 offers two futures: spec 01 gains an `action` mode "owning move, jump, whip and confirm on doors", or the
action room is the overworld with a pixel movement kind. The first gives a second mode the confirm door job that spec
04 rule 2 already owns ("confirm facing a door fires that tile's map trigger"), and spec 01's table gives the
overworld confirm for it. The item states both and chooses neither, so a coder cannot tell which spec owns door
confirm in an action room. That is the card's "no second confirm consumer" test, unanswered in the spec text.

Smallest fix: pick the pixel movement kind (no second consumer), or name the action mode as the overworld's
replacement and give spec 04's door rule to it explicitly, with the delta to both spec 01 and spec 04.

## Spec 17: defects, not blocking on their own

### D17-1 A number is rounded into a claim about exactness

`specs/17-action-movement.md` line 127: "a symmetrical arc that is 42 pixels high at step 20 passes 32 pixels at step
30, and A-M's table says 29". With the apex at 42 on step 20 over 40 steps, the height at step 30 is 31.5
(`42 * (1 - (10/20)^2)`), and the 32 pixel crossing is at step 29.76. The conclusion, that no symmetric parabola
fits both the apex and the six landing rows, still holds. The number should read 31.5, or "about 32", because the
whole point of the paragraph is that this spec does not round.

### D17-2 It claims spec 02 was fixed when its table still says otherwise

`specs/17-action-movement.md` lines 320 to 321: "C and V are free (SPEC-DELTAS C6 fixed confirm to Z, Space, Enter
and menu to Tab and Start)." `specs/02-input.md` line 11 still lists `menu` as "Enter, Tab", and line 9 lists
`confirm` as "Z, Space, Enter", so the spec text still binds Enter to two actions. C6's entry in `SPEC-DELTAS.md`
records the fix as implemented in `game/scripts/pp_input`, not as an edit to spec 02. The new bindings are fine; the
parenthetical is not, and it is exactly the duplicate binding the card's confirm test is about.

Smallest fix: say "C6 fixes this in pp_input; spec 02's table is still owed the corrected row", which also gives the
edit a home.

### D17-3 The knockdown rise is a decision that overrides a cited source without saying so

`specs/17-action-movement.md` lines 181 to 182 set the rise at 10 pixels cited to A-M section 7, and A-M section 7
line 198 states the ancestors peak "14 pixels above the start" from S1, S3 and S9. The 10 is A-M's own decision
(KNB-01 to KNB-03), so the citation is right, but a reader who follows the source trail finds 14 first. One clause
("S1 and S3 measure 14; KNB chose 10") would stop the next reader treating it as a typo. Not blocking.

## Spec 17: what I re-measured and found sound

These were checked by script and by reading the cited lines, so the author knows what is not in dispute:

- Every whip column (24 / 28 / 48 px, damage 2 / 3 / 3, animation 12 / 12 / 14, hit step 8 / 8 / 9, recovery 4 / 4 /
  5) matches A-M section 7's table exactly, and the totals 16, 16 and 19 are the correct sums. Tier 2 is +4 px and +1
  damage over tier 1; tier 3 is +20 px over tier 2. Both true.
- 42 / 16 = 2.625 blocks. 256 steps at 60 per second is 4.2667 s, printed as 4.27. 16 px of stairs at 0.5 px per step
  is 32 steps. 4 blocks is 64 px; 3 blocks is 48 px. The 4 step startup plus 40 air steps is 44. All correct.
- The six landing rows 29 / 36 / 40 / 42 / 44 / 46 and their heights 32 / 16 / 0 / -16 / -32 / -48 match A-M section
  6, and the 8 px per step fall after step 40 is arithmetically consistent with them.
- The knockback protection total, 16 steps of arc plus 30 after landing = 46, is correct.
- The cancel leads 12 / 16 / 14 / 19 are the section 3 totals, so they are internally consistent (the problem is
  F17-1, which is where the press may happen, not the arithmetic).
- The i-frame start split (action room on landing, arena on hit) is correctly sourced: A-M section 7 line 216 says
  "then 30 steps of i-frames from the landing step", while A-M section 3 and its P2 say the clock starts on the hit.
  A-M contradicts itself; spec 17 follows the more specific section and says so. The fix belongs in A-M, not here.
- `specs/04-overworld-rails-and-triggers.md` line 9 does give 16x16 tiles, so "16 pixels is one block" is right, and
  `specs/03-camera-and-scaling.md` rule 3 is the snap rule the spec cites.
- `specs/13-8bit-look.md` does fix battle sprite sizes (32x48 player), so the claim in section 8 item 8 is accurate.
- F1, F2 and F3 are taken by spec 02, and F2 is already used by spec 08's debug and spec 06 rule 7. The free key
  claim is right; the missing table rows are F17-3.
- No en or em dash in either spec, checked by code point scan for seven dash variants, 0 hits in each file.

## Spec 18: FAIL, seven blocking findings

Reviewed at sha256 `dfaa8b8e` (commit b066c64 at 14:40:42, 512 lines), the settled text card t_00a94c86 left behind.
The first read was `adb31da2` (commit 43b6fe6); one follow-up commit then changed section 0 item 9, section 4 and
A18-1 and nothing else (13 insertions, 13 deletions, measured with `git show b066c64 --stat`), and every finding below
was re-checked against the newer text. The file changed six times during this card, from 440 to 519 to 512 lines, and
the review is against the committed version only. The rewrite fixed the biggest thing the earlier text got wrong: the
interruption is no longer an hp crossing, so Percy's phase 3 is reachable and the kill route exists. That is a real
repair and it is acknowledged here. The findings that follow are what the settled text still does not close.

### F18-1 (blocking) The chosen scene id has no consumer in spec 06

`specs/18-boss-phases.md` lines 234 to 235 (section 4 item 4) and lines 27 to 29 (section 0 item 5), against
`specs/06-cutscene-runner.md` line 21 (`battle | enemy id | starts a battle, waits for its result`) and line 23
(`branch | flag, scene id | jumps if true`).

The director returns `battle_end` and the scene id "to the caller that ran `battle` (spec 06), which continues with no
press". Spec 06's `battle` command takes an enemy id, waits, and then keeps walking its own command list. It has no
argument for a result scene, and its only control flow is `branch` on a flag. So the returned scene id is dropped:
nothing starts the per route scene. A18-4 (lines 447 to 454) confirms the per route object and never adds the rule
that consumes it. "No new command is needed" (line 28) is true only for the flag option, and the spec chose the id
option.

Smallest fix: add a spec 06 rule, "on `battle_end = interrupted`, enter the scene id the battle returned", as a named
delta; or have the battle write a flag and let the scene branch, and say so in section 4.

### F18-2 (blocking) The 30 step break has no home in spec 07's turn flow

`specs/18-boss-phases.md` line 50 and line 54, against `specs/07-battle-director.md` lines 9 to 10 ("Player turn
resolves with 20 steps of message. Enemy turn telegraphs 12 steps, runs its pattern, then 20 steps") and
`specs/08-dodge-arena.md` rule 1 (line 17, "Every pattern opens with a 12 step warning").

Spec 18 inserts a 30 step break between the player's message and the enemy turn, with the new pattern's 12 step
warning inside it (break steps 18 to 29). Spec 07's turn flow has no break state, and the spec never says whether the
enemy turn's own 12 step telegraph still runs at break step 30. Read one way a phase change costs 30 steps; read the
other it costs 42 and the player gets two warnings. Section 9's deltas (C18-1 to C18-7) assign no edit to spec 07.

Smallest fix: one delta to spec 07 saying the break replaces the enemy turn's telegraph for the first pattern of the
new phase, and no second warning follows.

### F18-3 (blocking) Acceptance 7 needs a refusal that section 7 does not contain

`specs/18-boss-phases.md` line 506 ("A phase row at 0 percent, at 100 percent, or on a regular enemy: each is refused
with the row named") against refusals 1 to 11 at lines 371 to 388. No refusal covers a `phases` array on an enemy whose
`route_kind` is not `boss`; refusal 7 is only about an `interrupt` on a non boss. The checker cannot be written to pass
acceptance 7 from this list.

Smallest fix: add refusal 12, a `phases` array on a non boss, naming the row.

### F18-4 (blocking) The label placement contradicts itself for the widest label

`specs/18-boss-phases.md` lines 171 to 182: the label is "centred on the frame centre x 128", and "the longest string
is 16 characters, 128 pixels, inside ... spec 05's text area (x 72 to 240)".

A 128 pixel line centred on x 128 occupies x 64 to 192. `specs/05-dialogue.md` line 11 puts the text area at x 72 to
240, so `CONTROLS FLIPPED` (16 characters, the longest in the table at line 164) is 8 pixels outside it on the left.
The other six labels are 11 to 13 characters (88 to 104 pixels) and their left edges are x 84 to 76, so they fit. A
coder cannot satisfy both rules for the one string that matters.

Smallest fix: centre at x 136, or state x 64 to 192 and drop the text area claim.

### F18-5 (blocking) The slow key spec 08 does not have

`specs/18-boss-phases.md` lines 103 to 105: "The slow key that spec 08 gains (1 pixel per step) is unaffected and
stays available in every phase". `specs/08-dodge-arena.md` line 14 fixes marker speed at 2 pixels per step and names no
slow key; its out of scope line (44) names shooting, a second marker, gravity and touch dragging. A-M section 10
(line 297) says the slow key (BRD-05) needs a `marker_speed` field spec 08 does not allow. C18-5 (lines 482 to 483)
covers the second marker and the fixed speed 2, not the slow key, and section 9 assigns no card to add it.

Smallest fix: add the delta (spec 08 gains "hold cancel for 1 pixel per step"), or delete the sentence and put the
slow key out of scope for this spec.

### F18-6 (blocking) C18-2 omits `unless_flag`, so the schema delta rejects the field the spec requires

`specs/18-boss-phases.md` lines 468 to 471 (C18-2) list `interrupt` with its `on`, `hp_at_or_below` and `scene` fields.
Section 4 line 195 defines `unless_flag`, and C18-7 lines 489 to 490 say "the enemy level keeps an optional
`unless_flag`". The rest of `data/schemas/enemies.schema.json` is written with `additionalProperties: false` at every
object level (`$defs/phase` line 29, `$defs/enemy` line 62), so an `interrupt` object built as C18-2 says would reject
`unless_flag`, and refusal 7 has no clause for a flag name that does not exist.

Smallest fix: add `unless_flag` (string, optional, an existing flag) to C18-2 and to refusal 7.

### F18-7 (blocking) The attack band has no definition, and the spec's own example is outside the data row's band

`specs/18-boss-phases.md` line 286 says Percy's data row is "attack 3 to 5" (measured, correct). Line 327 gives phase
3 `"attack": { "min": 4, "max": 6 }`. Line 344 says a phase may raise the attack "inside the enemy's spec 07 band (3
to 6 for Percy)". `specs/07-battle-director.md` line 32 does say 3 to 6, but the row on disk says 3 to 5, and neither
C18-1 nor C18-2 widens it. Section 7's refusals 1 to 11 never mention `attack` at all, so the one rule the schema
description says the checker pins (`PHASE_ATTACK_BAND`) has no refusal in this spec.

Smallest fix: decide the band (the row's own, widened to 6 by C18-1, or spec 07's 3 to 6 with the row corrected), state
it in refusal 12, and make the example agree.

## Spec 18: defects, not blocking on their own

### D18-1 (answered by b066c64, one wording residue left) The kill wall arithmetic

At `adb31da2` this read "a kill needs a standing hp of at most 18 and therefore an interrupt threshold of at most 11
hp, which is 9 percent", mixing the 18 damage ceiling with the 12 ceiling's wall. Commit b066c64 answers it: section 4
now says "the interrupt threshold at most 11 hp with FIGHT alone (9 percent of 120) or at most 17 hp with the power (14
percent)", and A18-1 and section 0 item 9 carry both numbers.

I re-measured it myself over every percent from 1 to 99 rather than taking the commit's word: the highest percent a
blind one blow kill can pass through is 9 at a 12 ceiling and 14 at 18, and the crossing hp on 120 max hp is 10 at 9
percent and 16 at 14 percent. Both pairs are exact.

What is left is wording. Section 0 item 9 (lines 35 to 37) still says an interrupt "above 9 percent of its hp cannot
be killed by FIGHT at all", then gives 14 percent as the wall "once `tide_step` is spent". "At all" is false once the
power is in play (10 to 14 percent is killable with it), and "spent" reads as "used up", which would put the wall back
at 9. "With FIGHT alone" and "available" are the two words that close it.

### D18-6 The paragraph that rejects a crossing trigger still calls it "rule 4"

`specs/18-boss-phases.md` lines 210 to 212: "Rule 3 can only win on a blow that takes the bar from above the threshold
all the way to 0, because a blow that stops short crosses the threshold and rule 4 fires first." In the resolution
order at line 206, rule 4 is the SPARE press; the crossing is rule 5. Read as current rules the sentence is false, and
it is the first sentence of the paragraph that justifies the whole mechanism. "Under a crossing trigger the crossing
rule would fire first" says the same thing without naming a rule that no longer does that.

### D18-2 `route_gate` is a phase row field missing from the field table

`specs/18-boss-phases.md` lines 84 to 85: "Every field is optional in a phase row; the five permitted values above are
the whole legal set". Section 2.4 (lines 140 to 141) introduces `route_gate` as a phase row field, section 5 rule 7
(lines 280 to 282) makes it load bearing, refusal 9 (lines 384 to 385) pins its legal key set, and C18-2 adds it to
the schema. The table at lines 76 to 82 never gives it a type or a range, so the one table a coder reads for the row's
shape is false.

Smallest fix: add a row, `route_gate` | array of 1 to 4 strings | a non empty subset of `undecided`, `mercy`,
`blooded`, `genocide`.

### D18-3 The phase cap is stated two ways

`specs/18-boss-phases.md` line 23 and line 49 say `phases` holds "at most 4 rows", refusal 1 (line 371) refuses "a
fifth phase row", and phase 1 is the enemy row itself (line 41), so 4 rows means 5 phases. Line 510 puts "more than
four phases" out of scope. Pick one: 4 rows (5 phases) and out of scope "more than four rows", or 4 phases (3 rows)
and refusal 1 refuses "a fourth phase row".

### D18-4 Percy's phase 3 introduces no new shape, so the worked example is false

Section 5 rule 3 (line 271) and A18-1 (line 428) say phase 3 introduces a new hazard shape and that the study's "all
three shapes have been seen once" is now true. Section 5 defines a shape as `(size, sprite)` (lines 259 to 261) and
says no frame names a sprite, so the shape is the size. Measured in `data/patterns/all.json` today: `percy_rain`,
`percy_wall` and `percy_fan` all use size 8 only, and no frame carries a `sprite` key; `data/schemas/patterns.schema.json`
has no `sprite` property on a frame at all. So every Percy phase shows the same single shape and rule 3's only example
is an example of nothing.

Smallest fix: either give rule 3 an example that ships a 16x16 frame, or say "three patterns" rather than "three
shapes" here and in A18-1, which is what the study's sentence means.

### D18-5 Rule 4's percent compare is not restated

`specs/18-boss-phases.md` lines 206 to 207: "while its hp is at or below `interrupt.hp_at_or_below`". The field is a
percent of max hp (line 194), and section 1 defines the integer compare for phase breakpoints (line 44,
`hp * 100 <= hp_at_or_below * max_hp`) but section 4 never repeats it for the interrupt. "hp at or below 40" can be
read as 40 hp points or as 40 percent (48 hp on Percy). Acceptance 5 (line 502) disambiguates with 48 hp, but the rule
itself should carry the compare.

## Spec 18: what I re-measured and found sound

- The kill walls are exact, and so are the crossing points: 9 percent at the 12 ceiling and 14 percent at 18, crossing
  at 10 hp and 16 hp on 120. I measured this over every percent from 1 to 99 with my own script rather than reading it
  off the commit message.
- The new refusal 8 is correct: an interrupt threshold at or below `spare_hp_percent` can never fire, because rule 2
  accepts every SPARE in that range. Percy passes at 40 against 25, and the refusal window 48 hp down to 31 hp is
  arithmetically right (30 hp is 25 percent, so 31 hp is the first hp where SPARE is refused).
- Rules 2 and 4 no longer share an axis with rule 5, so a phase breakpoint and an interrupt percent on the same value
  do not shadow each other. That is the repair the rewrite made and it holds.
- Percy's crossings are 84 and 48 hp on 120 with the integer compare, giving bands 120..85, 84..49 and 48..1.
- Phase 3 is reachable on the 40 percent crossing, and the story exit is now a SPARE press. The old impossibility is
  gone.
- The concurrency numbers 2, 3 and 3 match spec 09's acceptance 5 and the data (`percy_rain` 2, `percy_wall` 3,
  `percy_fan` 3).
- The speed ratios are right: 2.0 / 1.6 = 1.25 and 2.1 / 1.7 = 1.2353.
- The box arithmetic is right: 160 * 80 / 100 = 128, 100 * 100 / 100 = 100, the narrowest box is 80x50, 72 pixels of
  centre travel at 3.00 is 24 steps, and every legal width gives an even result.
- All seven label character counts are right (12, 13, 13, 16, 13, 11, 12), and 24 steps from break step 18 is steps
  18 to 41.
- C18-1 is accurate: the Percy row on disk is `patterns: [percy_rain, percy_wall]` plus one phase at
  `hp_at_or_below: 60`.
- C18-3 is accurate: `prometheus_interrupt` exists and sets both `met_prometheus` and `percy_standing`.
- C18-7 is accurate: the Percy encounter row carries `interrupt: { hp_at_or_below: 60, unless_flag:
  met_prometheus, scene: prometheus_interrupt }`, which disagrees with the enemy row exactly as the delta says.
- The four route keys match spec 10's table (lines 20 to 23), and consequence 4 is right: `genocide` needs
  `bosses_killed` 1 or more, so it cannot be derived at the first boss.
- `tide_step` is power 6 and FIGHT's ceiling is 12, so 18 is the right ceiling.
- The spec's own warning stands: `tools/check_data.py` has no phase logic, so section 7 is the refusal list, not a
  description of running code.

## Deltas this review opens for the manager

- Spec 02: three debug keys (F4, F5, F6) as new actions, debug build only. From F17-3.
- Spec 11: `whip_level` as an integer 1 to 3 with a default of 1, or a different home for the tier. From F17-4.
- Spec 01 and spec 04: one owner of confirm on doors in an action room. From F17-5.
- Spec 06: a rule that consumes `battle_end = interrupted` and the returned scene id. From F18-1.
- Spec 07: the phase break replaces the enemy turn's telegraph for the first pattern of the new phase. From F18-2.
- Spec 08: the slow key (hold cancel, 1 pixel per step), which this spec depends on and no delta assigns. From F18-5.
- Enemies schema: `unless_flag` in the `interrupt` object (C18-2 as written omits it). From F18-6.
- Enemies schema and data: the attack band has to be named, and Percy's row either widens to 6 or the example drops to
  5. From F18-7.
- Patterns schema: a `sprite` property on a frame, if the shape pair is ever to have its second half. From D18-4.

## Limits of this review

- No GameMaker build and no playtest. Every number here was checked by reading and by script, not by playing.
- The data files were measured on 2026-10-22 between 13:53 and 14:35 (enemy and pattern facts at 13:53 to 14:06, the
  encounter, scene and power facts at 14:35). `data/enemies/all.json` and `data/patterns/all.json` are being edited by
  other cards this afternoon; a later reader should re-measure before relying on the shape and band facts.
- I read the files the card named, plus the specs each claim pointed at (01, 02, 04, 05, 06, 07, 08, 09, 10, 11, 13). I
  did not read the quarantined study copies or any file holding a key or a login.
- Spec 18 is reviewed against `dfaa8b8e` (commit b066c64, 512 lines), read in full at 14:36 and re-checked after the
  14:40:42 arithmetic commit. If it changes again, this verdict is against the committed text, not against whatever
  lands next.
