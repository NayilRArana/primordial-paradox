# CRASH-PORTRAIT: the game died in the draw event within seconds of the title screen

2026-10-26. gamedev. Found while answering a build-status question, not from a bug report.

## What was measured

Clean worktree at HEAD `a51fac8e`, no untracked files, `sync_data` and `sync_art` run, then
`python tools/integration_build.py`:

    BUILD PASS: Igor compiled the project and launched the game
    PP title: room rm_pp_title live, screen owned by obj_pp_title     build/last-igor.log:111
    Entering main loop.                                                build/last-igor.log:116
    PP CRASH: Variable <unknown_object>.portrait(100769, -2147483648) not set before reading it.
      at gml_Script_pp_dialogue_draw line 367                          build/last-igor.log:233
    ###game_end###0                                                    build/last-igor.log:234

So the project compiled, the room started, the main loop was entered, and the game ended on its own a moment
later. `pp_crash.log` in the save area was rewritten at 13:17 with the same text. The crash handler did its
job: no modal box, one line in the log, one file on disk.

## The defect

`game/scripts/pp_dialogue/pp_dialogue.gml` line 367:

    var _bust = _page_data.portrait;

Every other portrait read in that same file is guarded (`variable_struct_exists` at lines 101 and 109 and 234).
Line 367 was the one that was not. A dialogue page that names no portrait is a page with no portrait, which is
normal data, so the unguarded read turned ordinary content into a fatal error inside a draw event.

## The fix

    var _bust = "";
    if (variable_struct_exists(_page_data, "portrait")) _bust = _page_data.portrait;

`""` is the value the rest of the function already treats as "no bust": the `if (_bust != "")` block below it
skips drawing, and the speaker plate keeps its non-bust inset. So the fix restores the intended behaviour
rather than papering over the read.

## Proved, not argued

Rebuilt the patched tree, deleted `pp_crash.log` first, then ran:

- `BUILD PASS`, game window opened, room live, main loop entered.
- Run log carried 294 `PP audio` lines, including footsteps and the focus-lost/focus-back pause pair, so the
  game was well past the title rather than frozen.
- `pp_crash.log` was ABSENT after the run, not rewritten, not empty. Deleted before, still gone after.
- Closed with `taskkill /PID`, a plain termination signal, and the process left cleanly.

## The second, separate blocker in the working tree

The live working tree does not compile at all, and the cause is a concurrent writer rather than HEAD:

    Error : gml_GlobalScript_pp_talk_live(730) : wrong number of arguments for function audio_stop_recording

`game/scripts/pp_talk_live/` is untracked, its file was written at 13:13:34 during a compile started at 13:12,
and `game/PrimordialParadox.yyp` was modified to reference it (two references). HEAD references it zero times
and does not contain it. That is why a live-tree build fails and a clean HEAD build passes, and it is the same
"declared but absent" shape as DECLARATION-VS-CONTENT.md, one level up: declared in the project file, absent
from the commit.
