# Card map: every gamedev card, ordered, with its FOX-STYLE parent

Rule from the 2026-10-22 order: a card with no parent in `knowledge/FOX-STYLE.md` is a bug. This file is the index
that makes an orphan card visible. It is checked by reading, and by re-running the two queries in "How to recompute
this file" at the bottom, because card ids and statuses live on the board and not in the repo.

Ordering rule. Two axes, kept apart on purpose. Block 1 is the module lineage: each system is a derivative of the
one before, so read the table top to bottom and the dependencies hold. Block 2 is the roadmap batch: the same
product, cut into six steps of play by `ROADMAP-2026-10-22.md`, ordered by step and then by R code. A card in
block 2 is not a continuation of block 1 and is not numbered as one. Merging the two into one sequence would
claim an order that neither document asserts.

Legend for status: DONE, RUNNING, TODO, BLOCKED, and PLANNED for a row with no card on the board yet. These are
the board's own status values, uppercased. A status is a snapshot with the date on it, nothing more.

Legend for the parent column: a bare number is a numbered section of `knowledge/FOX-STYLE.md`, `law N` is one of
the ten laws in its section 0, and `all` means the row was derived from the doctrine as a whole and no single
section owns it.

## Block 1. The G0 lineage, 0 to 34

| # | Card | Board id | Lane | Status | FOX-STYLE parent |
| --- | --- | --- | --- | --- | --- |
| 0 | P1-A knowledge pack, licence-clean references, specs | t_90bcee8e | gamedev | DONE | 11, 12 |
| 1 | P1-B GameMaker skeleton, schemas, checker, run script, gates | t_f7d3a69d | gamedev | DONE | 11, 12 |
| 2 | G0 engine orchestration (the parent of this lane) | t_38a5fbf4 | gamedev | DONE | all |
| 3 | G0-1 save, load, resume and ledger persistence | t_a311bdff | gamedev | DONE | 6, 2 |
| 4 | UI-NES JRPG screens (battle layout, windows, dialogue box) | t_0df13164 | security-organization-audit | DONE | 4, 7, 8 |
| 5 | SPRITE-1 procedural overworld and battle sprites | t_b2acf67d | builder | DONE | 12 |
| 6 | BG-BATTLE NES battle backgrounds | t_1c5a8599 | job-discovery | DONE | 4, 12 |
| 7 | W1 wire the title room | t_9d403d42 | gamedev | DONE | 8, 12 |
| 8 | TS1-CODE working title screen proven by a run | t_90c0cc4a | gamedev | BLOCKED | 8 |
| 9 | TS2-CODE title v2 in the game | t_340b1578 | gamedev | DONE | 8 |
| 10 | PP build and run for real; fix the save-backup crash | t_b72efa81 | gamedev | DONE | 6 |
| 11 | NES-CHECK palette and font validator | t_a822bbbf | builder | DONE | 11, 12 |
| 12 | ENV-TILES ship tileset and sample map | t_4f58c88d | audit | DONE | 12 |
| 13 | SPEC study, doctrine and audit (this pass) | (no card, this session) | none | DONE | all |
| 14 | TEXT-REVEAL-1 one reveal machine, two layouts | t_fa2fc030 | gamedev | DONE | 7, law 8 |
| 15 | LEDGER-2 per-enemy exit ledger and verdict | t_48020b30 | gamedev | DONE | 2 |
| 16 | NES-PALETTES scene palette sets for title and ship | t_c8156a77 | gamedev | DONE | 12 |
| 17 | TS2-ART-A title v2 logo, emblem, car exterior | t_758934a8 | gamedev | DONE | 12 |
| 18 | SFX-1 NES style sound effect set | t_f9a87b4f | builder | DONE | 9 |
| 19 | SFX-WIRE menu and text sounds in every menu | t_efdf181b | gamedev | BLOCKED | 9, 8 |
| 20 | SFX-WIRE-PROOF prove footsteps, door, encounter in a scripted run | t_0cac113b | gamedev | TODO | 9, 5 |
| 21 | ENEMIES-1 NES enemy sprites for the ship and the sea | t_97871d4b | security-organization-audit | DONE | 12 |
| 22 | CHAR-PIPE concept art to sprite pipeline | t_d01614a1 | code-review | DONE | 12 |
| 23 | ASSEMBLE playable Map 2 test room with tileset and walk | t_e32c2a29 | gamedev | DONE | 5, 12 |
| 24 | NES-AUDIT fixes, 24 gated art rows worst first | t_5f3bba57 | gamedev | DONE | 12 |
| 25 | INTRO-1 stars, fade, text crawl | t_d2ec48a1 | gamedev | BLOCKED | 10, 9 |
| 26 | MENU-1 extract `pp_menu`, then the pause screen | PLANNED | PLANNED | PLANNED | 8, audit 3c |
| 27 | FLOW-1 door and transition module (`pp_flow`) | PLANNED | PLANNED | PLANNED | 5 |
| 28 | TALK-1 the TALK command as a battle command | PLANNED | PLANNED | PLANNED | 1, 2 |
| 29 | BATTLE-1 encounter and enemy rows as data | PLANNED | PLANNED | PLANNED | 1, 11 |
| 30 | PATTERN-1 the first three authored bullet recipes | PLANNED | PLANNED | PLANNED | 3 |
| 31 | SLICE-1 the Percy fight end to end | PLANNED | PLANNED | PLANNED | 1, 2, 3, 4 |
| 32 | SAVE-2 the slot list screen over the summary | PLANNED | PLANNED | PLANNED | 6, 8 |
| 33 | P6-ROUTE the prison branch and the Kronos ending | PLANNED | PLANNED | PLANNED | 2, 10 |
| 34 | AUDIT-NIGHT one pass re-running the whole gate set | PLANNED | PLANNED | PLANNED | 12 |

## Block 2. The roadmap batch, R01 to R20, ordered by step

From `ROADMAP-2026-10-22.md` section 3. The R code, the step, the lane and the file scope are that file's. The
board id and the status were read off the nayil-ops board at 2026-10-22 13:04 PDT. Every lane below equals the
card's assignee on the board; no card in this block is assigned to a profile the roadmap does not name.

| R | Card | Lane | Step | Board id | Status | FOX-STYLE parent |
| --- | --- | --- | --- | --- | --- | --- |
| R07 | beat sheet and gates as a test | testing | S1 to S6 | t_098da427 | RUNNING | law 6, 12 |
| R16 | the drive shot list, 12 shots | research-assistant | S3 | t_9b2e63d2 | RUNNING | 10 |
| R01 | spec 17 action movement | builder | S3, S6 | t_f5a7ca5c | RUNNING | 5, law 6, law 7 |
| R15 | who and what is at the quay | research-assistant | S4 | t_7e72fe1c | RUNNING | 11, 5 |
| R03 | arrival map and gate scene | builder | S4 | t_c024f8bc | TODO | 5, 10, 11 |
| R08 | arrival map test | testing | S4 | t_3a52845d | TODO | 5, 11 |
| R18 | review of the arrival data | code-review | S4 | t_6cd706d0 | TODO | 12, 11 |
| R12 | cue PP-03 harbor | musician | S4 | t_1140be15 | RUNNING | 9 |
| R06 | the contrast tool the redraw queue names | builder | S4 art | t_ee44cf97 | TODO | 4 (owns spec 13), 12 |
| R20 | the five P0 sprite rows | assistant | S4 art | t_2924b0d7 | TODO | 12, law 10 |
| R04 | ship deck map and gangway scene | builder | S5 | t_a3fa132a | TODO | 5, 10, 12 |
| R13 | cue PP-05 small ship | musician | S5 | t_1c42a535 | RUNNING | 9 |
| R02 | spec 18 boss phases and rule changes | builder | S6 | t_92ee7b8e | RUNNING | 1, 3, 4 |
| R05 | first fight rows: enemy and encounter | builder | S6 | t_8a7ada73 | RUNNING | 1, 11 |
| R09 | first fight cannot be lost, test | testing | S6 | t_6cd2cc3c | TODO | 1, 4, 11 |
| R14 | cue PP-04 navy sailors | musician | S6 | t_becd6879 | RUNNING | 9 |
| R17 | review of spec 17 and spec 18 | code-review | S3, S6 | t_eab7904b | TODO | 12 |
| R10 | card map gains the twenty (this file) | audit | all | t_8595b06c | RUNNING | 12, law 4 |
| R11 | the evidence pack | audit | all | t_4b148e6d | TODO | 12 |
| R19 | key hygiene, measured | security-organization-audit | all | t_363f729a | RUNNING | none, see the flaw list |

The links that make block 2 an order rather than a list, read from the board's own dependency table: R15 before
R03, R03 before R04, R02 before R06, R03 before R08, R05 before R09, R03 before R18, R01 and R02 before R17,
R06 before R20, and R07, R08 and R09 before R11. That is 12 links between cards in this batch, which is the
number `ROADMAP-2026-10-22.md` claims. All 20 also hang off the roadmap card `t_97e248a6`.

R21 is deliberately not a row. It is the S3 drive scene, created from `knowledge/DRIVE-SHOT-LIST.md` when R16
lands, and it owns the drive block in `data/scenes/all.json` after R04. It has no board id because it has no card,
and writing a row for it here would be the same invented id this file exists to prevent.

## The counts, recomputed from the rows above

Block 1: 35 numbered rows. 25 carry a board id, 1 is a session with no card (row 13), 9 are planned (rows 26 to 34).
Block 2: 20 rows, all with a board id, 0 planned.
Rows in this file: 55. Rows carrying a board id: 45. Distinct board ids: 45. Ids missing from the board: 0. Ids
appearing twice in this file: 0. Cards listed twice: 0.

The 45 board rows by status on 2026-10-22 13:04 PDT: DONE 21, RUNNING 11, TODO 10, BLOCKED 3. That sums to 45.
The 25 lineage rows that carry a board id are DONE 21, BLOCKED 3, TODO 1. Row 13 also reads DONE but it is a
session and not a card, so it is not in that sum. The 20 batch rows are RUNNING 11, TODO 9.

The 20 batch rows by lane: builder 6, testing 3, musician 3, research-assistant 2, code-review 2, audit 2,
security-organization-audit 1, assistant 1. That sums to 20 and it is the split `ROADMAP-2026-10-22.md` states.

The earlier version of this file said 25 real cards, "20 before this pass, 2 created by it, 3 counted here from
other lanes' boards that this lane consumes". The 25 was right and still is. The breakdown was not recomputable
from anything in this repo, so it is gone rather than repeated, and the numbers above are the ones a reader can
recount from the rows.

## Per-lane concurrency

Running cards per lane across the whole nayil-ops board, all statuses other than archived, 2026-10-22 13:04 PDT:
gamedev 3, builder 3, musician 3, research-assistant 2, testing 1, audit 1, security-organization-audit 1. That is
14 running cards and the largest number on any lane is 3, so no lane is over the cap of 3 that the roadmap sets.
The three builder cards that are running are R01, R02 and R05 from block 2.

## Flags: the cards this map cannot give a section to

The rule is that a card with no FOX-STYLE parent is a bug, and the fix is to extend `FOX-STYLE.md` first, not to
invent a section here. These are the rows where I could not honestly name one. Each is a decision for gamedev.

1. R19, key hygiene measured (`t_363f729a`): no parent. The nearest candidate is section 12, which governs the
   repository, but it governs its structure and its check layer (generated resource list, hand-written event
   bodies, specs, schemas, tests, provenance) and says nothing about what the repository may hold or run. Law 10
   is about foreign material, which is a different subject. Rather than stretch section 12 over a card about
   secrets and logins, this row reads none: either FOX-STYLE gains a short section on what the repository may
   hold and run, or it states that key hygiene is outside its scope. Until one of those is written, this card is
   an orphan by the file's own rule.
2. R07, beat sheet and gates as a test (`t_098da427`): laws only, law 6 for frame timing and section 12 for the
   test layer. No numbered section owns pacing, the beat sheet or the gate times; those numbers come from
   `knowledge/mechanics/PACING-AND-CUTSCENES.md`, which is a study and not doctrine. A test that enforces 45 to
   60 s fights is enforcing a study, not a section.
3. R01, spec 17 action movement (`t_f5a7ca5c`): partly covered. Section 5 owns spec 04 and therefore the walk and
   the rails, and law 6 and law 7 cover the frame timings and the input. The jump arc (4 steps up, 40 steps of
   air, apex 42 px), the whip reach tiers and knockback have no section anywhere in FOX-STYLE, and spec 17 is a
   new spec that is not in the derivation map's list of specs awaiting a section.
4. R20, the five P0 sprite rows (`t_2924b0d7`): section 12 covers art as a listed resource and law 10 covers
   provenance. No section covers sprite craft itself; the rules live in `knowledge/SPRITE-CRAFT.md`, a study.

Two smaller notes on the same subject, reported and not changed here because this file is the only file in scope:

- `knowledge/FOX-STYLE.md` line 332 lists the specs with no section yet as 02, 03, 15 and 16. Specs 17 and 18 are
  now being written by R01 and R02 and are not on that list, so the list is stale by two entries.
- The same line's last clause puts spec 16 TALK under section 1, and TALK-1 (row 28 here) still has no card, so
  the command the non-violent premise rides on is still planned rather than built.

## What changed in this pass, 2026-10-22

- Block 2 was added: 20 rows, each with the roadmap's R code, step and lane, the board id as it exists today, the
  assignee, and a FOX-STYLE parent or a named gap.
- Ten statuses in block 1 were stale and are corrected to the board: rows 14, 15, 16, 17, 18, 21, 22, 23 and 24
  read READY and are DONE, and row 19 read RUNNING and is BLOCKED. A map that keeps a finished card in the READY
  column is wrong in the direction that costs money, because the next reader queues work that is already done.
- A Lane column was added to block 1, read from the board. It shows cards this lineage consumes that were built
  outside it, which is what the old footnote was trying to say without evidence.
- The count line was replaced by counts that recompute from the rows, and the unrecomputable breakdown was dropped.

## Why each planned card exists

- MENU-1. The audit found no `pp_menu` module: the title menu is inline in `pp_title`. Not a violation yet, because
  there is one menu. It becomes one the moment a second is written inline. The trigger is explicit, so the card is
  created with whatever card needs the second menu, or earlier if that is cheaper.
- FLOW-1. `pp_overworld` currently handles rails. Doors and the fade belong in one module so a scene cannot implement
  half a transition (FOX-STYLE 5).
- TALK-1. Nayil's battle command set is FIGHT, POWER, TALK, SPARE, ITEM. TALK is the one with no implementation and no
  card. It is the command the whole non-violent premise rides on.
- BATTLE-1. The enemy and encounter tables are still code shaped in the battle director. Section 1 requires rows.
- PATTERN-1. The recipe runner exists and is tested; there is no authored content yet.
- SLICE-1. The vertical slice Nayil scoped: Map 2 ship plus Percy, end to end.
- SAVE-2. The save module works; there is no slot list screen, so a player cannot choose a file.
- P6-ROUTE. The two route branches exist in the ledger; no scene reads them yet.
- AUDIT-NIGHT. A scheduled-by-hand re-run of every gate, so the audit does not rot.

## Cards that must not be created

Anything that adds a subsystem with no FOX-STYLE section. If a card seems to need one, extend `FOX-STYLE.md` first and
add the section to the derivation table at the end of it. That is the rule that keeps the doctrine complete rather
than decorative.

## How to recompute this file

Read only. The board database is `<agent-runtime>\kanban\boards\nayil-ops\kanban.db`, opened as
`sqlite3.connect('file:<path>?mode=ro', uri=True)` so nothing can be written by the check itself. The two statements
behind every number above:

```
select id, assignee, status from tasks where id in (<the 45 ids in this file>);
select assignee, count(*) from tasks where status = 'running' group by assignee;
```

Recount the rows in the first result set against the rows in the two tables; recount the second against the
per-lane paragraph. A row here with no row there is a dead id. A row there with no row here is a missing card.
