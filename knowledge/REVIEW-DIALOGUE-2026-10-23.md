# Review: dialogue v2 (R42), does the code do D2

Reviewer: code-review lane. Written 2026-10-23. Card t_23377d65.
Subject: D2 of `knowledge/GAMEDEV-DECISIONS-2026-10-22.md` (lines 42 to 70), landed by R22 (t_5b27880e,
commits `79564da` and `8a198e4`).
Reviewer did not edit the subject: the only file written is this one.

## What state was read

`git rev-parse HEAD` at the time of reading: `69abae0`. The shared tree carries other lanes' work in progress, so
each input was classified before it was trusted.

| Input | State measured | Trusted as |
| --- | --- | --- |
| `data/dialogue/all.json` | clean at HEAD, landed in `79564da` and `8a198e4` | landed |
| `data/schemas/dialogue.schema.json` | clean at HEAD, landed in `79564da` | landed |
| `data/flags.json` | clean at HEAD, 14 flags, the five of D1 appended after `kronos_spared` | landed |
| `game/scripts/pp_dialogue/pp_dialogue.gml` | clean at HEAD, landed in `79564da` | landed |
| `tools/check_data.py` | dialogue checks landed in `79564da` (constants at 61 to 73, checks at 686 to 828). The same file carries 64 uncommitted lines from another lane at 58 to 63 and 922 to 985; neither block is dialogue | landed for dialogue, working tree elsewhere |
| `data/scenes/all.json` | modified in the working tree, +151 lines, uncommitted (ARRIVAL-MAP-2 in flight). HEAD holds no `quay_gate_*` scene at all | working tree only |
| `knowledge/ARRIVAL-CONTENT.md` | untracked (`??`), so it exists only in the working tree | working tree only, and it is the card's own input |
| `tests/test_dialogue_v2.py` | modified in the working tree, +209 lines, uncommitted (R31's file after this batch). HEAD version is 442 lines | both, labelled |

Method: read the four inputs as a reviewer, then mutate a copy of `data/` under the lane workspace and run the
landed checker against it. Nothing in the project tree was edited. GameMaker is not executable on this machine, so
question 2 rests on source reading; the tests that cover it are text pins, and that limitation is stated under Q2.

## Q1. Does the schema and the checker enforce D2 exactly?

Verdict: PARTLY. Six of the seven items hold, measured by mutation. The seventh, no goto cycle, is enforced by
neither the schema nor the checker. D2 itself never states a cycle rule (D2 lines 42 to 70 say only that `goto` is
"another dialogue id"), so the gap is against this card's checklist and against the hazard the rule exists for, not
against D2's own words.

| D2 item | Where | Result |
| --- | --- | --- |
| exactly one of `lines` or `pages` | schema `oneOf` 56 to 59; `tools/check_data.py:701-706` | enforced, both layers |
| 1 to 3 pages | schema 64; `check_data.py:748-752` | enforced |
| 1 to 3 lines per page | schema 39; `check_data.py:765-769` | enforced |
| 30 characters per page line | schema `page_line` 27 to 31; `check_data.py:777-780` | enforced |
| 1 to 3 choices | schema 65; `check_data.py:805-809` | enforced |
| 12 character label | schema 47; `check_data.py:815-822` | enforced |
| `sets` resolve to `data/flags.json` | `check_data.py:782-796` via `self.ref(ids, "flag", ...)` | enforced |
| `goto` resolves to a dialogue | `check_data.py:824-827` | enforced |
| no goto cycle | nothing | NOT enforced |

Evidence for the last row: mutations M9 and M10 (below) both exited 0 with the file unchanged in the checker's eyes.
The scene runner already has the matching guard, `tools/check_data.py:1495-1515` (`branch cycle: a -> b -> a`), so
the class of guard exists in this file and was simply not extended to `goto`. A self `goto` (entry X, last page,
choice 0 goes to X) makes a box that can never close: `pp_dialogue.gml:261-273` reloads the same entry, and
`pp_dialogue.gml:302` refuses to turn the page on a choice page, so the only way out is a choice that closes.

Two things the schema and checker carry that D2 does not:

1. An entry level `sets` field: schema `data/schemas/dialogue.schema.json:66`, checker `tools/check_data.py:711`,
   used by `data/dialogue/all.json:370` (`quay_dock_office_pass` sets `has_boarding_pass`). D2 line 52 fixes the
   entry shape as "`id`, `speaker`, and exactly one of `lines` or `pages`" and gives `sets` only to a choice (line
   57). The field is needed, because ARRIVAL-CONTENT line 145 wants the pass set on page 6 and D3 wants
   `has_boarding_pass` set in the office, and D2 provides no other home for a flag that is not a choice. So R22
   filled a hole in D2 and did not say so on its card. That is a defect of the ruling, not of the data.
2. `sets` maxItems 8 (schema 48 and 66) has no D2 number behind it and no checker counterpart. Harmless, but it is
   an invented cap in a file whose job is to describe D2.

## Q2. Does `pp_dialogue` apply `sets` before the box closes, on every path including a skip press and a scene bail out?

Verdict: NO. Blocker. A skip press on a choice page sets two flags and takes a reply the player never saw.

The box has three close sites. Two apply the flags first, one does not, and the two that apply them are reached one
step too early when the same press that finishes the typing is read again as a pick.

1. Close site, pick: `game/scripts/pp_dialogue/pp_dialogue.gml:277`, after `258-259` applies the choice's `sets` and
   the entry's `sets`. Correct.
2. Close site, page turn: `pp_dialogue.gml:304-305`, applies the entry's `sets` before `closed = true`. Correct.
3. Close site, debug step: `game/scripts/pp_scene/pp_scene.gml:616`, `_sc.dialogue.closed = true` with no flag
   application at all. It is the F2 key and it is dead unless `PP_SCENE_SELFTEST_ENV` is set (`pp_scene.gml:600`),
   so it is a low severity defect, but it is a path, and it loses `has_boarding_pass` if it finishes the office pass.

The blocker is the press ordering on the player path:

1. `game/scripts/pp_overworld/pp_overworld.gml:366` runs `pp_dialogue_advance` and line 367 runs `pp_dialogue_step`
   in the same step, from the same press. `game/scripts/pp_scene/pp_scene.gml:440-443` does the same.
2. On a choice page that is still typing, advance takes the first branch at `pp_dialogue.gml:298-301`: it calls
   `pp_text_reveal_complete` (`game/scripts/pp_text/pp_text.gml:175-180`, which fills the page and leaves
   `done = false`) and returns `false` without reaching the choice page guard at line 302.
3. `pp_dialogue_step` then runs. The guard at `pp_dialogue.gml:288` compares `revealed` against the unit length,
   which advance has just made equal, so it does not return.
4. `pp_dialogue.gml:291` reads `pp_pressed("confirm")`, which is still true because it is the same press in the same
   step, and the cursor is still 0.
5. `pp_dialogue.gml:257-259` applies choice 0, so `gate_passed` and `gate_truth` are written and
   `quay_gate_truth` opens. The player pressed once to finish the text and never saw the panel the draw code needs
   `_budget == 0` for (`pp_dialogue.gml:358`).

The author guarded this exact ordering in the one path a player does not drive: the autoplay branch at
`pp_scene.gml:431-436` picks only when `reveal.revealed >= pp_text_unit_length(...)` and advances otherwise. The
two player paths have no such guard. The smallest fix is to have `pp_dialogue_advance` mark the press as consumed
when it completes a page, and have `pp_dialogue_step` skip the pick on that step; a close entry point that applies
`_d.sets` would close the third site at the same time.

What the tests can and cannot see: the D2.6 obligation is covered by a Python model of the pick
(`tests/test_dialogue_v2.py:559-577` in the working tree), pinned to the GML's own order by string comparison at
`580-601`. It proves the pick applies flags in the right order; it never executes a press sequence, so the ordering
fault above is invisible to it. `tests/test_text_reveal.py:138-152` likewise only asserts that the calls exist.

## Q3. Does any scene carry control flow that spec 06 rule 3 forbids?

Verdict: PASS on the rule, with the scene being uncommitted work.

Measured on the working tree's `data/scenes/all.json` (HEAD has no gate scene at all): scene `quay_gate_checkpoint`
is `music`, `say quay_gate_checkpoint`, `say quay_gate_choice`, `branch gate_truth`, `branch gate_bluff`,
`branch gate_authority`, `end`. Three sequential `branch` commands are an if/elseif chain, not a loop, and `branch`
is the only control flow in the file. Command kinds used across all 11 scenes: music 3, say 10, move 3, wait 6,
setflag 3, end 11, battle 1, fade 2, branch 4. No new command, no `choice` command, and `SCENE_COMMANDS`
(`tools/check_data.py:101-104`) is unchanged, so D2.4 holds.

Two notes on that scene, for ARRIVAL-MAP-2 rather than for R22: the three branch targets
(`quay_gate_truth`, `quay_gate_bluff`, `quay_gate_authority`) each contain only `wait 20` and `end`, so a scene
named after the reply plays nothing, and the reply itself only ever plays through the choice's `goto`.

## Q4. Do the 14 arrival rows read as the content card wrote them?

Verdict: MOSTLY. The text that landed is the card's text, character for character, and no line is over the box.
Two of the card's fourteen rows never landed at all.

Measured by parsing the JSON block at `knowledge/ARRIVAL-CONTENT.md:184-304` (14 rows) and diffing it against the
landed file, after joining the two rows R22 had to split for the 3 page cap:

- `quay_gate_checkpoint` (3 pages) plus `quay_gate_choice` (1 page) equals the card's 4 page checkpoint exactly,
  including the page speakers, and the fourth page is verbatim.
- `quay_dock_office` (3 pages) plus `quay_dock_office_pass` (3 pages) equals the card's 6 page office exactly.
- `quay_gate_truth`, `quay_gate_bluff`, `quay_gate_authority`, and all seven `say_door_*` rows are byte identical
  to the card.
- Longest line in the landed arrival rows is 30 characters; nothing invented, and the seven door lines carry no
  page speaker override, which reads the entry speaker and is the same output the card asked for.
- Rows the card wrote that did not land: `morgan_again` (`ARRIVAL-CONTENT.md:233-243`) and `cass_high_street`
  (`:257-266`). Both rely on a `by_flag` mechanism that the landed schema cannot express (`additionalProperties:
  false` at `dialogue.schema.json:55`, and `by_flag` appears nowhere in `data/`, `game/`, `tools/`, `specs/` or
  `tests/`, only in this knowledge file). So the second talk with Morgan, which the card says changes with which
  gate choice was picked, has no landed form and no route to one.

Count check: the landed file holds 14 new rows, but they are not the card's 14. Two are splits of one card row each,
and two card rows are missing, so 12 of the card's 14 landed.

## Defects

B1, blocker. A skip press picks choice 0 and sets flags. `game/scripts/pp_dialogue/pp_dialogue.gml:288` and `:291`,
reached from `game/scripts/pp_overworld/pp_overworld.gml:366-367` and `game/scripts/pp_scene/pp_scene.gml:440-443`.
Trace in Q2. Fix: consume the press in `pp_dialogue_advance` and gate the pick on it in `pp_dialogue_step`.

B2, defect. The checker has no `goto` cycle guard, so a self or two step cycle passes clean.
`tools/check_data.py:798-827` has no cycle walk while `1495-1515` does it for `branch`. Evidence: mutations M9 and
M10. Fix: walk the `goto` graph the way the `branch` walk does, and report the trail.

B3, defect. The debug step closes the box without applying `sets`. `game/scripts/pp_scene/pp_scene.gml:616`. Debug
only (`PP_SCENE_SELFTEST_ENV`), and it loses `has_boarding_pass` on the office pass. Fix: one
`pp_dialogue_close(_d)` that applies `_d.sets` then closes, used by all three close sites.

B4, defect. Two of the content card's 14 arrival rows are missing, and one of them is unrepresentable in the landed
schema. `knowledge/ARRIVAL-CONTENT.md:233-243` (`morgan_again`, needs `by_flag`) and `:257-266`
(`cass_high_street`). No row in `data/dialogue/all.json` matches either id. Fix: a decision on how a flag chosen line
is written (D2 does not provide one), then the rows.

B5, defect of scope. The entry carries a `sets` field D2 does not give it. `data/schemas/dialogue.schema.json:66`,
`tools/check_data.py:711`, used at `data/dialogue/all.json:370`. D2 line 52 fixes the entry shape without `sets`.
Fix: amend D2 to name the field, or move `has_boarding_pass` to a mechanism D2 already has.

B6, defect of the ruling, not of the code. D2 line 53 says the `lines` shorthand keeps "the 14 existing ids" green,
but the file held 21 shorthand entries before this change and holds 21 now. Measured: 35 entries, 21 with `lines`,
14 with `pages`. The count in the ruling is wrong by seven and should be corrected so a later reader does not think
seven entries were added by someone else.

## Notes

N1. `specs/05-dialogue.md:25-30` still describes the pre D2 choice shape ("up to 4", `id`, `condition`, `target`),
and line 40 still promises that "a 40 character line in data is refused by the checker". The landed checker refuses
a shorthand line only when a single word is longer than 30 characters (`tools/check_data.py:732-737`), so a long
line wraps instead of being refused: the committed `hound_win_kill` line 0 is 31 characters and the checker exits 0.
Both are wording disagreements, and the spec file is already flagged on t_4464ac5c. No em or en dash appears in any
of the 14 landed rows.

N2. The schema and the checker both fire on the same fault, each naming the same path and index, which is the right
redundancy for a gate; six of the eight caught mutations above produce two lines for that reason.

N3. `pp_dialogue_on_choice_page` (`pp_dialogue.gml:238`) decides "last page" from the reveal's unit count, which
`pp_text_reveal_step` marks `done` on the last unit (`pp_text.gml:161-163`). It works, but only because
`pp_text_unit_length` returns 0 when done, so the two functions are coupled through a sentinel rather than a field.

## Mutation log, what the checker did

Each row: a copy of `data/` under the lane workspace, one edit to `data/dialogue/all.json`, then
`python tools/check_data.py --root <copy>`.

| Mutation | Exit | What the checker said |
| --- | --- | --- |
| M1 fourth page on `quay_gate_checkpoint` | 1 | schema oneOf and "4 pages is more than the 3 a box entry may carry (spec 05, D2)" |
| M2 31 character page line in `quay_dock_office` | 1 | "is too long (schema dialogue.schema.json)" and "is 31 characters, the box holds 30 on a page line" |
| M3 14 character label on choice 0 | 1 | "is too long (schema ...)" and "is 14 characters, the panel holds 12" |
| M4 choice sets `gate_maybe` | 1 | "unknown flag id 'gate_maybe'" |
| M5 `goto` to `quay_gate_nowhere` | 1 | "unknown dialogue id 'quay_gate_nowhere'" |
| M6 entry carries `lines` and `pages` | 1 | schema oneOf and "carries both lines and pages; an entry is exactly one of the two (D2)" |
| M7 fourth choice | 1 | "4 choices is more than the 3 the panel holds (spec 05)" |
| M8 page of four lines | 1 | schema maxItems and "4 lines is more than the 3 a page holds (spec 05)" |
| M9 choice 2 `goto` its own entry | 0 | nothing; the checker passed a self cycle |
| M10 `quay_gate_truth` and `quay_gate_bluff` goto each other | 0 | nothing; the checker passed a two step cycle |

Reproduce: the probe is `probe3.py` in the card workspace
(`<agent-runtime>\kanban\boards\nayil-ops\workspaces\t_23377d65\probe3.py`), which copies
`data/`, applies one mutation at a time, and restores the copy.

## Checks run

- `python tools/check_data.py` on the live tree: exit 0, "check_data: all files pass".
- `python -m pytest tests/test_schemas.py tests/test_check_data.py -q`: 59 passed. Both files are clean at HEAD,
  so this is the landed pin that the schema numbers and the checker constants agree (`tests/test_schemas.py:108-124`).
- `python -m pytest tests/test_dialogue_v2.py -q`: 32 passed, on R31's in-flight working tree version (647 lines).
  The HEAD version (442 lines) is the landed one; this run is labelled working tree, not landed.
- The 10 mutations above, on a copy of `data/`.

Not verified: nothing was executed inside GameMaker, so Q2 is a source level verdict. The card's D2.6 "headless
test that reads an entry with three choices, picks one, and asserts the flag is set" exists as a Python model, not
as a run of the engine.

## What this review did not do

Did not edit `data/dialogue/all.json`, the schema, the checker, `pp_dialogue`, the scenes, the tests, or the content
card. Did not commit anything: the shared tree is red on other lanes' files (the parent card logged 13 failures at
its own HEAD, none from this batch), so a commit through the gate would be refused for reasons outside this review.
This file is written and untracked.
