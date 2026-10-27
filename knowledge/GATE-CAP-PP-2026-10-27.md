# GATE-CAP-PP, 2026-10-27: the gate that judges this project is now sized from today's numbers

Card t_e7d53c94 (gamedev), node CitadelArana. Nothing here was pushed, published or spent. No key was
printed, stored or logged. Every number below came from a command run in this session, and the command
is named beside it.

## 1. What was broken, in two parts

A primordial-paradox commit could not land for two independent reasons, both of them about time
rather than about the change:

1. The suite grew past the cap that judged it. `staged_time_cap_s` was 1100 s, sized as 1.5x of a 714 s
   measurement on 2026-10-26. On the same evening a materialised worktree of HEAD plus one card's 27
   paths measured **1553.81 s** (15 failed, 1936 passed), so the cap no longer described the suite at
   all.
2. `lane_commit.py` gave the `git commit` call a budget of the suite cap plus 180 s (1280 s) and killed
   the gate at it. The gate's real wall clock carries materialisation, the project's prepare steps and
   the staged check on top of the suite, so at that margin the tool killed the gate **before the gate
   could print its own row**: the report read `TIMEOUT. Nothing was measured`, exit code 7, nothing
   landed.

## 2. What changed elsewhere first, and why it decides this card's shape

Card VC-3 (t_a183f183) has already replaced the blanket full-suite commit gate with a selection: in
staged mode `commit_gate.py` maps the claimed paths to the tests that exercise them (the static import
graph plus `guard/impact/primordial-paradox.json`, built 2026-10-27 06:11), falls back to
`fast_marker_set` when a source file maps to nothing, and runs that selection under
`commit_budget_s: 60`. A selection over budget is DEFERRED to the nightly and logged, never a pass and
never a fail. `fast_cmd` no longer ends with `tests`, so the mapped arguments are the selection. The
full suite now lives on push, on the nightly, and on Pine.

That is the fix for part 1 of section 1, and it means a commit no longer has to fit a 26 minute suite
inside its own gate. This card's job is to prove that on a real commit, and to leave the full-path
numbers correct rather than stale.

## 3. The measurement this card was asked for

Command, in a worktree of HEAD at `D:/hermes-worktrees/gatecap-t_e7d53c94`, with the project's own
prepare order and no other lane's uncommitted work:

    <home>/AppData/Local/Python/bin/python.exe -m pytest -q -p no:cacheprovider tests

Output:

    12 failed, 1920 passed, 507 warnings in 695.50s (0:11:35)

What that number is and is not:

- It is HEAD (29db96eb) alone, in the path the nightly measures. It is **11 and a half minutes**, not
  26: the 1553.81 s run was a busy box, and the same suite on this host moves by about 2.2x between a
  busy and a quiet run. That spread is the reason the cap rule uses the worst measurement and not the
  quietest.
- It is red, and the 12 are real: `test_bake_meta`, `test_check_data`, `test_enemy_phases`,
  `test_look` (four rows), `test_no_network_in_build`, `test_project`, `test_prometheus_interrupt`,
  `test_save`, `test_slice_story`. Every one of them reads `data/` **as committed at HEAD**. They read
  green in the live tree only because the 762 uncommitted paths sitting there repair what HEAD
  carries. That is the other half of "nothing can land": HEAD's own committed data does not pass HEAD's
  own checkers, so a full run on the nightly path is red for a reason no single card owns.
- The `MemoryError` rows from card t_f4d1c2d1 do NOT appear. Measured separately in the live tree on
  2026-10-27:

      python -m pytest -q -p no:cacheprovider tests/test_quantize_concept.py tests/test_render_chip_v2.py
      37 passed in 38.14s

  So the twelve rows that reddened the suite at 23:1x are green now, and nothing was skipped to make
  them so. The row that would pin them is card t_f4d1c2d1's, not this one's; a skip marker here would
  have hidden a green row behind another card's name.

## 4. The cap arithmetic, run rather than argued

The rule from `_cap_note_2026_10_26` is: cap = 1.5x the worst honest measurement on THAT path, and no
higher.

| cap | was | now | 1.5x of what |
| --- | --- | --- | --- |
| `fast_time_cap_s` | 1000 | 1000 | 661.68 s, live tree, 2026-10-26 09:37 (needs 992) |
| `staged_time_cap_s` | 1100 | **2331** | 1553.81 s, materialised worktree, 2026-10-26 late evening (needs 2330) |
| `full_timeout_s` | 1200 | 1200 | 695.50 s, worktree of HEAD, today (needs 1043) |
| `commit_budget_s` | 60 | 60 | untouched; it is VC-3's number and it governs the commit |

`staged_time_cap_s` no longer caps the staged commit: `commit_budget_s` 60 does, and it defers past
that. The raised number now sizes (a) a staged run that is not budget-limited and (b) the wait
`lane_limits.commit_budget_s` derives for `lane_commit.py`, which is 1100 + 180 today and should become
`commit_budget_s` + headroom. That file is VC-3's, so it is noted on card t_a183f183 rather than edited
here.

`tests/test_gate_caps.py` (new, 5 rows) runs this table instead of trusting it: it refuses a `fast_cmd`
that still ends with `tests`, a commit budget over 60 s, a cap with no measurement recorded beside it,
and any cap under 1.5x of its own recorded number. In a checkout of this project alone the rows skip
loudly, because the config is the manager tree's.

## 5. The rehearsal commit

Section 6 names the claim and quotes the gate's own row.

## 6. What a reader can reproduce

    # the suite number (about 12 minutes at HEAD, in a worktree, no other lane's work)
    git worktree add --detach D:/hermes-worktrees/pp-head HEAD
    cd D:/hermes-worktrees/pp-head/projects/primordial-paradox
    <home>/AppData/Local/Python/bin/python.exe tools/sync_data.py
    <home>/AppData/Local/Python/bin/python.exe tools/sync_art.py --no-project
    <home>/AppData/Local/Python/bin/python.exe -m pytest -q -p no:cacheprovider tests

    # the arithmetic
    <home>/AppData/Local/Python/bin/python.exe -m pytest -q -p no:cacheprovider tests/test_gate_caps.py
