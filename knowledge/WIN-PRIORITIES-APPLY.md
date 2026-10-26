# WIN PRIORITIES APPLY, 2026-10-26: the exact board commands behind knowledge/WIN-PRIORITIES.md

Generated from the same table as `knowledge/WIN-PRIORITIES.md`, so the two cannot drift. Card
`t_29dcf655` (gamedev, node CitadelArana). Run these from a profile that may mutate the board (the
manager), one shell, top to bottom. Every line names its card title after a `#` so a wrong paste is
visible. A worker run is refused every `kanban` verb, reads included, so all three blocks below run
where the edits run.

## 1. Priorities, 66 rows, highest first

```
hermes kanban edit t_29dcf655 --priority 99      # W0 WIN-PRIORITIES
hermes kanban edit t_771e78ef --priority 98      # MOVE-HOLD walk input
hermes kanban edit t_c784d239 --priority 97      # W1 PP-BRIDGE
hermes kanban edit t_ee178652 --priority 96      # W2 LIVE-TALK
hermes kanban edit t_4c8e4181 --priority 96      # W0b APPLY WIN-PRIORITIES
hermes kanban edit t_5031b766 --priority 95      # META-LIVE-1
hermes kanban edit t_29578bd8 --priority 95      # W3 OPEN-WEIGHTS
hermes kanban edit t_70840bce --priority 94      # W4 JUDGE-PANEL
hermes kanban edit t_9332fe42 --priority 93      # META-ART-1
hermes kanban edit t_120dc9f2 --priority 92      # W5 SCORE-FINAL
hermes kanban edit t_73682c8d --priority 91      # W6 DEMO-CUT
hermes kanban edit t_da67bc63 --priority 90      # SUBMISSION rows for Nayil
hermes kanban edit t_7b18be6f --priority 89      # PUB-1 public repo
hermes kanban edit t_2ecb3c38 --priority 88      # PUB-2 nightly publish
hermes kanban edit t_135be998 --priority 86      # META-LIVE-BAKE
hermes kanban edit t_2a2baf83 --priority 85      # Meta bonus decisions
hermes kanban edit t_d6060104 --priority 84      # KAGGLE-GPU-R17
hermes kanban edit t_8b07fe69 --priority 83      # title theme identity
hermes kanban edit t_c0597404 --priority 82      # M0 title v9
hermes kanban edit t_65512e1c --priority 81      # M3 Baroque cues
hermes kanban edit t_279ef225 --priority 80      # battle cue v2 ruling
hermes kanban edit t_16417018 --priority 79      # title v7/v8 ruling
hermes kanban edit t_9275989a --priority 78      # PP-BOARDING ruling
hermes kanban edit t_030a89e5 --priority 78      # R32 route test
hermes kanban edit t_6d66f32d --priority 77      # DECISIONS-SWEEP
hermes kanban edit t_769b545d --priority 76      # SHIP-BOX-FRAME
hermes kanban edit t_b50612ab --priority 75      # INTRO-POLISH
hermes kanban edit t_2a743083 --priority 74      # DRIVE-STILLS-LEGAL
hermes kanban edit t_f034f9d0 --priority 73      # drive palette ruling
hermes kanban edit t_6420e93e --priority 72      # ARENA-HAZARD-ROLE
hermes kanban edit t_8a23f384 --priority 71      # MUSIC-KAGGLE-INPUT
hermes kanban edit t_89109597 --priority 69      # VIRAL-CUT
hermes kanban edit t_fe2734d2 --priority 68      # SAM-SEGMENT-LIVE
hermes kanban edit t_fb09a735 --priority 67      # EYE-CRITIC-META
hermes kanban edit t_10cad8d9 --priority 65      # MUSIC-CUE-LEDGER
hermes kanban edit t_2c518ec8 --priority 64      # AUTO-SPRITE-NEXT (live)
hermes kanban edit t_c31f9295 --priority 63      # FIX-BUILD-INPUTS-4
hermes kanban edit t_cdb3a6be --priority 62      # FIX-YYP-11
hermes kanban edit t_41553cc5 --priority 61      # PP-OUTSIDE-INPUTS
hermes kanban edit t_4fca7154 --priority 60      # REPO-GATE
hermes kanban edit t_836dbb1a --priority 58      # M1a counterpoint checker
hermes kanban edit t_944ef2b6 --priority 57      # M1b counterpoint generator
hermes kanban edit t_aa3ab04e --priority 56      # M4 music gate
hermes kanban edit t_0ed3bd3f --priority 55      # M2 Baroque research
hermes kanban edit t_9d9b5b1d --priority 45      # gate build step
hermes kanban edit t_ba694028 --priority 40      # ear sweep landing
hermes kanban edit t_916a2382 --priority 31      # two spec numbers
hermes kanban edit t_73e40064 --priority 30      # gate cap ruling
hermes kanban edit t_ddbc8cff --priority 29      # spec ledger FAIL
hermes kanban edit t_a5e0d631 --priority 28      # ART-REPRO-TITLE
hermes kanban edit t_3a932e73 --priority 27      # GEMINI-EYE
hermes kanban edit t_d2b724e3 --priority 26      # GATE-CHOICE-CAPTURE
hermes kanban edit t_52166d5a --priority 25      # CAPTURE-QUIET
hermes kanban edit t_2f4229ac --priority 20      # VC-1 gated backups
hermes kanban edit t_9d6c1f43 --priority 14      # GATE4-RERUN
hermes kanban edit t_73295f13 --priority 13      # LEDGER-PROOF
hermes kanban edit t_1d9bc0a9 --priority 12      # VC-2 staged snapshot
hermes kanban edit t_a183f183 --priority 11      # VC-3 fast gate
hermes kanban edit t_44c83b34 --priority 10      # VC-4 commit path
hermes kanban edit t_c9316f7a --priority 9      # VC-6b commit sweep
hermes kanban edit t_ae018527 --priority 8      # VC-11 worktrees
hermes kanban edit t_1778cf9a --priority 7      # VC-10 repo hygiene
hermes kanban edit t_13e25e31 --priority 5      # AUTO-SPRITE-NEXT (duplicate)
hermes kanban edit t_bd32a72e --priority 5      # AUTO-SPRITE-NEXT (duplicate)
hermes kanban edit t_c024f8bc --priority 2      # ARRIVAL-MAP S4 (superseded)
hermes kanban edit t_00f5a63f --priority 0      # Meta API measured (knowledge)
```

## 2. Pauses, 8 rows, reason "after the submission"

```
hermes kanban block t_9d6c1f43 "after the submission"      # GATE4-RERUN
hermes kanban block t_73295f13 "after the submission"      # LEDGER-PROOF
hermes kanban block t_1d9bc0a9 "after the submission"      # VC-2 staged snapshot
hermes kanban block t_a183f183 "after the submission"      # VC-3 fast gate
hermes kanban block t_44c83b34 "after the submission"      # VC-4 commit path
hermes kanban block t_c9316f7a "after the submission"      # VC-6b commit sweep
hermes kanban block t_ae018527 "after the submission"      # VC-11 worktrees
hermes kanban block t_1778cf9a "after the submission"      # VC-10 repo hygiene
```

## 3. The check

```
hermes kanban list --json --sort priority-desc > /tmp/after.json   # every id here at its new priority
hermes kanban list --status blocked --json > /tmp/blocked.json     # the 8 paused ids are all present
```

Nothing here deletes a card. Nothing here touches `a protected profile`, MOVE-HOLD (`t_771e78ef`),
META-LIVE-1 (`t_5031b766`), META-ART-1 (`t_9332fe42`) or any W card: none of them carries a pause.
