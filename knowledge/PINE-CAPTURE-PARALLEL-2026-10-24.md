# PINE-CAPTURE-PARALLEL: two captures at once, measured, 2026-10-23

Card `t_272feb33` (PINE-CAPTURE-PARALLEL), owner testing, created by gamedev. Tree measured:
`<repo>`. Build used: `output\PrimordialParadox\PrimordialParadox.win`,
written 2026-10-23 02:40, from `output\PrimordialParadox\`.

## 1. What the check asked for, and what this run could actually prove

The card asked for capture A local and capture B offloaded to Pine, in parallel, both muted, both 256x240 content in a
768x720 viewport, with the pair under the sum of the two serial times (`kanban` card body, `t_272feb33`).

The Pine half is impossible on this project, and that is measured, not assumed: see section 6. So the pair was measured
on this one host, which is also the only place the card's question exists at all, because "stealing each other's window
or audio" is a same-desktop phenomenon and two captures on two machines cannot contend for a window
(`<repo>\knowledge\PINE-CAPTURE-PARALLEL-2026-10-24.md`).

## 2. The mechanism: keyless self-frames, one save area per instance

- Each capture launches the game through `tools\pp_launch.py` `start_game()`, so PP_MUTE=1 is set in the child, the
  idle gate runs first, and exactly one `PP: muted` line is printed per launch
  (`<repo>\tools\pp_launch.py` lines 75 to 90 and 208 to 238).
- The frame is the game's own, not a desktop copy: with PP_TITLE_CAPTURE set, the title writes `pp_title_frame.png`
  from inside its draw at title step 30 and logs it (`game\objects\obj_pp_title\Draw_0.gml` lines 7 to 21).
- A self-frame needs no keyboard, and that is what makes concurrency possible: GameMaker reads key STATE from the
  focused window, so a posted key is a dud and only one window can hold focus
  (`tools\capture_title.py` lines 1618 to 1622, `send_vk` at line 619).
- Two instances would collide on one filename, so each child gets its own `LOCALAPPDATA`, which is the directory
  GameMaker's `screen_save` writes under (`tools\capture_title.py` `self_frame_paths()` lines 1542 to 1551). Measured:
  each instance's file landed in its own directory and the other instance's folder was untouched
  (`<agent-runtime>\kanban\boards\nayil-ops\workspaces\t_272feb33\localappdata_a` and `_b`).
- Harness and verifier, both kept beside this card's workspace:
  `parallel_capture.py`, `verify_parallel_capture.py`, `summarize.py`
  (`<agent-runtime>\kanban\boards\nayil-ops\workspaces\t_272feb33`).

The idle gate was asked once, before any window opened, and it allowed the run: `P: idle gate allows the launch: no
input for 676 s, 120 s required` (`parallel_stdout.txt` in the workspace above). The number is D9's two minutes, not the
gate module's three (`tools\pp_launch.py` line 59).

## 3. The numbers

Five rounds of the same harness, each round one serial capture A, one serial capture B, then the pair at once. Round 1
was the first launch of the build in this session, so its serial A carries the cold start; rounds 2 to 5 are warm.

| Round | serial A s | serial B s | sum s | pair s | pair under sum |
|---|---|---|---|---|---|
| 1, cold | 4.797 | 2.266 | 7.063 | 2.562 | yes |
| 2 | 8.921 | 2.469 | 11.390 | 3.406 | yes |
| 3 | 3.250 | 2.156 | 5.406 | 2.625 | yes |
| 4 | 2.125 | 2.172 | 4.297 | 2.640 | yes |
| 5 | 2.875 | 8.313 | 11.188 | 3.953 | yes |

Warm rounds (2 to 5): sum median 8.297 s, pair median 3.023 s, so the pair cost 36 percent of the serial sum, and the
check's inequality held in 5 of 5 rounds (`timing_summary.json`, `parallel_report_run1.json` to `_run5.json` in the
workspace above). The serial spread is wide (2.1 to 8.9 s per capture) because most of a serial capture's wall clock is
the runner starting and the forced close, not the capture: the game's frame exists 1.5 s after launch in every serial
run, measured as `frame_after_s` (`parallel_report_run5.json`).

Under the pair the frames arrive later, 2.015 s and 2.781 s in round 5 against 1.469 s and 1.531 s serial, so two
runners do compete while booting. That contention is real and it still leaves the pair under the serial sum
(`parallel_report_run5.json`).

Every one of the 15 measured launches (5 rounds x 3 captures) returned `ok: true` for both members of its round, so the
parallel pair finished both captures in every round (`timing_summary.json`).

## 4. The two outputs and the frame check

`output\parallel_capture_a.png` and `output\parallel_capture_b.png` are round 5's pair, 4,369 bytes each
(`<repo>\output`).

Measured on the files, `verify_parallel_capture.py`: 768x720 each, every 3x3 block one flat colour (0 uneven blocks),
native 256x240, 6 native colours, which is the 256x240 frame shown at 3x and not a resampled screenshot
(`verify.json` in the workspace above).

The pair is pixel identical, sha256 `4936ff4e5436677318c04aef9d5f56659b207ce2eb6bb5c93c993a08ac9846d8` on both, and
that is the title's step 30 being deterministic rather than one file copied twice: the two files were written 14 ms
apart, `localappdata_b` at 03:54:55.502 and `localappdata_a` at 03:54:55.516, by two processes with different pids,
into two different save areas
(`localappdata_a\PrimordialParadox\pp_title_frame.png`, `localappdata_b\PrimordialParadox\pp_title_frame.png`).

The frame is real art and not a fade: the opening shot of the night quay, clock tower, stars, battlements and the road
dashes, read from the image (`output\parallel_capture_a.png`).

## 5. The interference that was found, exactly

- Foreground stealing is real and it was measured: the background instance logged `PP audio: focus lost, music paused
  (cue and theme) and every effect stopped` while the foreground one did not
  (`game_a.log` line 46, `game_b.log` with no such line, in the workspace above). Two windows cannot both hold the
  foreground, so each launch takes it from the other.
- That steal cost nothing here because both runs were muted (PP_MUTE=1, the game's own line at `game_a.log` line 32 and
  `game_b.log` line 32) and because a keyless capture never needs the focus.
- Key-driven captures cannot be paired this way. The ship capture and the demo recorder press keys through the focused
  window (`tools\capture_title.py` lines 1618 to 1643, `tools\play_demo.py`), so a second game window taking focus would
  eat the presses, and a screen-rectangle copy raises the window before copying (`bring_to_front`, line 322), which
  makes two desktop copies of two overlapping windows mutually destructive.
- No window was left open: `run.finish()` closed each launch, `P: exit:` printed once per capture, and
  `tasklist | grep -i primordial` answers `no PrimordialParadox.exe running` after the rounds
  (`tools\pp_launch.py` lines 193 to 202).

## 6. Why the second capture cannot run on Pine, measured in one run

The card named `tools\pine_offload.py`, which does not exist in the project; the helper is
`<workspace>\Shared\projects\arananet\pine\pine_offload.py` (the same correction PINE-SUITE recorded at
`knowledge\PINE-SUITE-2026-10-24.md`).

One probe run, `python pine_offload.py --cmd '...' --name captureprobe`, zip 24,377,780 bytes, one shard, completed in
63.9 s, $0.0032 of Computer time. Its `results_txt`, verbatim:

    Linux
    DISPLAY=[]
    no-wine
    exe-not-in-zip
    EXIT=0

(`<workspace>\Shared\projects\arananet\pine\data\results\offload-captureprobe-0.json`)

Three independent reasons, each measured or read from source:

1. Pine is Linux with no display session (`DISPLAY=[]` in the result above), and the launch gate itself says a host with
   no desktop must not launch anything (`tools\idle_check.py` lines 69 to 81).
2. There is no Wine on the far side (`no-wine`), and the runner is a 7,941,704 byte
   `output\PrimordialParadox\PrimordialParadox.exe`, which the zip refuses because every non-audio file at or over
   3 MB is skipped (`pine_offload.py` `_wanted()`, line 89), so the game binary never travels: `exe-not-in-zip`.
3. `pine\OFFLOAD.md` line 18 states it directly: the capture harness and anything needing the game window stay on the
   PC.

So a Pine capture is not a slow capture, it is no capture: no window, no runner, no frame. The card's premise that Pine
can hold capture B is wrong, and nothing was left unmeasured about it.

## 7. What this means for the recording night

- Two keyless self-frame captures at once are safe and faster than serial: the pair's median 3.023 s against a serial
  sum median of 8.297 s over four warm rounds, with 5 of 5 rounds under the sum (`timing_summary.json`).
- Two focus-driven recordings at once are not safe. The nightly demo is a key script plus a desktop recording
  (`tools\play_demo.py`), so for the recording night the answer is serial: one recording at a time. Parallelism is
  proven only for the keyless self-frame path, which is a capture, not a recording.
- If parallel captures are wanted nightly, the rule that makes them work is the per-instance `LOCALAPPDATA` isolation,
  and it has to stay in the tool that launches them, not in a lane's notes (`parallel_capture.py` in the workspace
  above).

## 8. P: lines, as run

Round 5's console output, verbatim, from `parallel_stdout.txt` in the workspace above:

    P: build: PrimordialParadox.win
    P: idle gate allows the launch: no input for 676 s, 120 s required
    P: parallel capture: launch allowed, the game starts with PP_MUTE=1, so nothing plays
    PP: muted, PP_MUTE=1 in the child environment and the game's own log says so (game_a.log)
    P: a: window Primordial Paradox hwnd 986868 pid 40816
    P: window: moved off the primary screen to 1920,0, which is the second monitor
    P: exit: capture a, capture a, the game process is closed (pid 40816, code 1)
    P: serial a: 2.88 s
    PP: muted, PP_MUTE=1 in the child environment and the game's own log says so (game_b.log)
    P: b: window Primordial Paradox hwnd 5377524 pid 40348
    P: window: moved off the primary screen to 1920,0, which is the second monitor
    P: exit: capture b, capture b, the game process is closed (pid 40348, code 1)
    P: serial b: 8.36 s
    PP: muted, PP_MUTE=1 in the child environment and the game's own log says so (game_a.log)
    PP: muted, PP_MUTE=1 in the child environment and the game's own log says so (game_b.log)
    P: a: window Primordial Paradox hwnd 2953022 pid 43160
    P: window: moved off the primary screen to 1920,0, which is the second monitor
    P: b: window Primordial Paradox hwnd 2031658 pid 2648
    P: window: moved off the primary screen to 1920,0, which is the second monitor
    P: exit: capture b, capture b, the game process is closed (pid 2648, code 1)
    P: exit: capture a, capture a, the game process is closed (pid 43160, code 1)
    P: parallel pair: 3.95 s (serial sum was 11.19 s)
    P: parallel_capture_a.png: 768x720, native 256x240, uneven 3x blocks 0, native colours 6, ok True
    P: parallel_capture_b.png: 768x720, native 256x240, uneven 3x blocks 0, native colours 6, ok True

Two cosmetic notes on that output, both this harness's own doing and neither a finding: the exit line repeats the label
because `parallel_capture.py` passes `capture a` as both label and note, and `code 1` is the code `taskkill /F` leaves
after a forced close, not a game failure, since `P: exit` reports the process closed and the frame was already written
(`tools\pp_launch.py` `kill_tree()` lines 120 to 152).
