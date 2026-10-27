# QA-PLAYTHROUGH 2026-10-27: the played route, the frames, and the ranked bug list

Card t_84fe6ab8 (lane testing, node CitadelArana, the desktop). Two builds appear here and they are kept apart:
the build under test is `output/PrimordialParadox/PrimordialParadox.win`, sha256
`e5a4b6b56cc83751bc7ed6e083fed1604bedf09f8336d92263968f808adecf5f`, written 2026-10-27 06:59:19 -0700
(`output/qa_playthrough_20261026/_build_identity_oct27.txt`), and the earlier build, written 2026-10-26 22:49, is
quoted only in section 8 and only where its frames are named.

Status in one line: the title, the menu, the crawl, the handoff to the drive and the first line of the drive were
played on the newest build and 129 one second frames of it exist, and then the picture stops changing and stays
stopped for the rest of the take, so the arrival walk, the gate, the boarding, the deck, the sailor's talk, the first
fight and the 30 second held walk are NOT MEASURED.

Nothing on the card's MUST NOT list was done. No game file was changed. The files written are under
`output/qa_playthrough_20261026/`, `output/demo/` (the killed raw recordings) and this knowledge file. Nothing was
posted, pushed or published, no other lane's process was killed, and no `--force` was passed to the launch gate.

## 1. The findings, newest build

Severity 1 is a demo stopper: a player or a judge cannot see the shot. Severity 2 is visible on screen or in the
audio and costs demo points. Severity 3 is small, or a warning so that nobody re-reports it. Every frame path in
this table exists on disk and every severity 1 finding has a frame.

| # | sev | frame | what a player sees | probable owner |
| --- | --- | --- | --- | --- |
| 1 | 1 | `output/qa_playthrough_20261026/frames_oct27/f_0069.png` and `output/qa_playthrough_20261026/frames_oct27/f_0129.png` (the same picture, md5 `9c0dae9779a6e4c87fd3eb76285ee19f`, 61 identical frames, 68 s to 128 s) | From 68 s the drive's picture never changes again: a grey lit corridor with a white rail, green ground and a `hold X to skip` prompt at the top left, drawn once and then frozen to the end of the take. The game's own log stops in the same second, after five characters of the drive's first line (`PP audio: text_blip_a played, instance 400108` to `400112`, then nothing, `build/qa-grab-game.log:163` to `:167`). The drive is 178 s long (`data/audio.json`, PP-02 note), so everything the demo promises after the crawl is behind one still. | `data/scenes/all.json` (scene `drive_to_southampton`, the `say` of `drive_sign_55` that immediately follows `camera 37`), the reveal machine in `game/scripts/pp_text`, and `game/scripts/pp_scene/pp_scene.gml` `case "say"` at line 190 |
| 2 | 1 | `output/qa_playthrough_20261026/frames_oct27_skip/f_0075.png` to `f_0128.png` (54 identical frames, 74 s to 127 s, md5 checked in section 4) | The same defect with the drive skipped, which is why it is not the drive's own dialogue alone: the route reaches the arrival at Town Quay (`PP route: step drive handed to step arrival (arrival at Town Quay)`, `build/qa-grab-game.log:165`), the picture shows the quay's brick walls and grey pavement with two blue and white sprites (`frames_oct27_skip/f_0080.png`), and then it does not change again for 54 s while the take runs on to 127 s. The one thing a later run has to separate: the script sent no key after 62.7 s (`output/qa_playthrough_20261026/_grab_oct27_skip.log`, trace `q08c up cancel at 62.7 s`), so a picture waiting for the player cannot be told from a picture that stopped updating on this evidence alone. The check that separates them is one take that sends a key every 5 s through the still. | the room draw in `game/scripts/pp_overworld/pp_overworld.gml` and the presentation path under `game/scripts/pp_app`, not the input path: the skip itself was logged as accepted |
| 3 | 1 | no frame, and this one is an instrument wall rather than a game bug: the take ends at `output/qa_playthrough_20261026/frames_oct27/f_0129.png` (128 s) and `output/qa_playthrough_20261026/frames_oct27_skip/f_0128.png` (127 s) | Every take today ends at 143.4 s with `the clock stopped advancing at step 8604, 396 steps short of 9000` (full route) and `step 8601, 399 steps short of 9000` (skip route), and the two earlier runs read 8601 and 8602, so the stop is at the same place every time. The clock that fails is wall clock (`tools/play_demo.py:427` to `:437`), so the harness process itself got no CPU for 60 s. The power plan does not explain it (AC sleep after 0, display off after 3600 s, `powercfg /q SCHEME_CURRENT`), the event log has no display driver reset on 2026-10-27, and the host is measured at 95% of RAM in use with 1.55 GB free (`python output/qa_playthrough_20261026/probe_host.py`). The manager's own balancer logged the same pressure twice while these runs were happening: `memory low (0.9 GB free): no dispatch, no moves` at 07:13 and `memory low (0.3 GB free)` at 07:24 (`<workspace>\Shared\projects\arananet\manager\guard\balancer.log`). A take longer than 143 s needs this host to have memory, or a host with less on it. | the host, not the game: `tools/play_demo.py` and `output/screens_newest/play_and_grab.py` both die at it, on both scripts |
| 4 | 2 | log line `build/qa-grab-game.log:159`, no frame | The drive's music is a placeholder in the built game. The row says the master is delivered (`data/audio.json`, PP-02, `"pending": false`, `assets/audio/pp_drive_master1/pp_drive_master1.ogg`) and the OGG is on disk (`game/datafiles/streams/pp_drive_master1.ogg`, 2,221,427 bytes, 2026-10-26 11:44), but the game logs `PP audio: music cue PP-02 has no OGG yet, expected pp_drive_master1.ogg, placeholder 1` at the second the drive starts. A player hears a placeholder where the demo's third shot's music belongs, or nothing at all. | `game/PrimordialParadox.yyp`: `python tools/check_project.py` reports 25 files on disk that are not listed as Included Files, and `pp_drive_master1.ogg` is one while the older `pp_drive_v2.ogg` is the one still listed (`grep pp_drive game/PrimordialParadox.yyp`). The list is generated, so the fix is `python tools/gen_project.py` plus a rebuild |
| 5 | 2 | no frame: `python tools/check_project.py`, exit 1, 25 problems | The same miss takes the sound out of the rest of the demo route. Unlisted and therefore absent from the built game: `footstep_a.ogg`, `footstep_b.ogg`, `knife_slash.ogg`, `text_blip_kronos.ogg`, `text_blip_narrator.ogg`, `text_blip_oldman.ogg`, `text_blip_percy.ogg`, `text_blip_zeus.ogg`, `pp_01_title_v9.ogg`, `pp_03_harbor_master1.ogg`, `pp_04_navy_sailors_master1.ogg`, `pp_boarding_master1.ogg`, `title_theme_v6.ogg` (`output/qa_playthrough_20261026/_static_checks_oct27.log:13` to `:26`). The walk and the fight are the two shots that depend on footsteps and the knife, so this is one regeneration away from costing two more shots their sound. | `game/PrimordialParadox.yyp`, whose Included Files list is generated by `tools/gen_project.py`; `tools/check_project.py` is the gate that should have blocked the build |
| 6 | 3 | `output/qa_playthrough_20261026/frames_oct27/f_0047.png` (md5 `2779e7fdd942ffff8a6e996e81ddc5bb`, 22 identical frames, 46 s to 67 s) | A still picture for 22 s at the start of the drive. This one is NOT a bug and is listed so nobody re-reports it: the scene holds the camera at x=0 for `wait 600`, `wait 2`, `wait 600` before it moves (`data/scenes/all.json`, scene `drive_to_southampton`), which is 20 s of a picture that is meant not to move. | none: `data/scenes/all.json` says the hold on purpose |
| 7 | 3 | `output/qa_playthrough_20261026/frames_oct27/f_0045.png` | The only frame outside the palette: share 0.6905, 24 colours, mean luma 4.78 (`output/qa_playthrough_20261026/route_frame_measures.json`). It is the dissolve from the crawl into the scene, it sits between two in-palette frames, and it is not foreign art. | none: mark it, do not chase it |
| 8 | 3 | `output/qa_playthrough_20261026/frames_oct27/f_0016.png` to `f_0021.png` | Six black frames at 16 s to 21 s. That is the intro fade, which is a fade on purpose, and a black frame scores a legal NES colour, so it is not a finding. | none |
| 9 | 3 | `output/qa_playthrough_20261026/frames_oct27/f_0030.png` and `output/qa_playthrough_20261026/frames_oct27_skip/f_0053.png` | The crawl's lowest visible line is a half line (`A SA`), which is the text scrolling in and not a line running out of its box. The skip prompt is drawn at x 8, y 8 (`game/scripts/pp_overworld/pp_overworld.gml:924`), so the prompt is not clipped either. In the skip take `f_0053.png` (52 s) is the one frame the measure cannot call the game at all, share 0.352 and 26 colours, and it is the skip transition itself: mark it, it is not foreign art. | none: `game/scripts/pp_title/pp_title.gml` scrolls it on purpose |

Said plainly, because it changes how finding 1 must be read: the picture is a screen grab of the composed desktop
(`PIL.ImageGrab.grab(bbox=..., all_screens=True)`, `output/screens_newest/play_and_grab.py:64`), not a copy of the
window's own drawing surface, and the earlier build's runs used `ffmpeg` on the window. Three runs on two builds with
two instruments stop changing their picture in the same stretch after the crawl, which is why this is reported as a
game defect and not as a capture artefact. What the evidence does NOT settle is whether the still is the game waiting
for a key: the scripts sent nothing after 62.7 s in the skip run, and a picture that waits cannot be told from a
picture that stopped updating without a take that keeps pressing.

## 2. The ten that cost the most Demo points, in order

The demo is scored out of 25 over six shots, S1 title, S2 crawl, S3 drive, S4 gate, S5 dock office and S6 fight
(`knowledge/DEMO-SCRIPT.md`). Five findings is the honest length, not ten: findings 1 and 2 freeze the picture before
S4, and finding 3 ends every take at 143 s, so a longer list would be padding.

| rank | finding | the shot it costs | why it costs those points |
| --- | --- | --- | --- |
| 1 | finding 1, the drive freezes and the game log stops five characters into its first line | S3 drive, and with it S4, S5 and S6 | four of six shots sit after that second in the run; a judge who cannot see past the still cannot score the gate, the dock office or the fight |
| 2 | finding 2, the same freeze after the arrival with the drive skipped | S4 gate, S5 dock office and S6 fight | it is the proof that the fault is not the drive's own dialogue, and it is where the queue stops being short of the ship and starts being short of the whole second half |
| 3 | finding 3, every take dies at 143.4 s on this host | none on its own, and every shot after S3 in practice | it is the reason this report cannot answer for the ship, the talk or the fight, and the reason the two fixes above can only be checked in takes shorter than 143 s until the host has memory |
| 4 | finding 4, the drive's music is a placeholder | S3 drive | the shot's claim is an NES faithful night drive, and its music is the first thing a judge hears |
| 5 | finding 5, footsteps, knife and six blips are not in the project file | S4 gate, S5 dock office, S6 fight | the walk and the fight are carried by footsteps and the knife; without them the two loudest shots are silent |

## 3. The 30 second capture of held walking

Not measured, and it cannot be measured on this host from this build: the held walk script starts on the ship's deck
(`output/qa_playthrough_20261026/qa_held_walk.json`, holds at 60.00 s, 71.67 s and 83.33 s of a 95 s script), which is
behind finding 1. The last measured answer is the 2026-10-26 take, and it is a red, not a pass:
`output/demo/hold_walk-2026-10-26.json` carries `footstep_cues 8` against `footstep_floor 37`, and its frames are
static after the first second because `ship_small` row 7 is eight tiles long (`data/maps/all.json`). A 30 s held walk
needs three alternating legs on a corridor longer than eight tiles, which is a script change this card may not make.

## 4. The frames this report was built from

Every path below exists on disk. `output/*` is ignored by git (`projects/primordial-paradox/.gitignore:28`), so the
frames are local to this host and are regenerated by the commands in section 10, items 4 and 13.

- `output/qa_playthrough_20261026/frames_oct27/f_0001.png` to `f_0129.png`, 129 files, one per second, 0 s to 128 s,
  from `python output/screens_newest/play_and_grab.py --script output/qa_playthrough_20261026/qa_full_route.json
  --out-dir output/qa_playthrough_20261026/frames_oct27 --idle-wait 600`
- `output/qa_playthrough_20261026/frames_oct27/_preroll.png` (the tool's own pre-roll picture, not a frame)
- `output/qa_playthrough_20261026/frames_oct27/grab_run.json`, the tool's summary: `first_second 0.0`,
  `last_second 143.06`, `viewport_box [8, 31, 768, 720]`
- `output/qa_playthrough_20261026/route_frame_measures.json`, one measured row per frame of the full route take,
  from `python output/qa_playthrough_20261026/analyze_frames.py --mode route --frames-dir
  output/qa_playthrough_20261026/frames_oct27`
- the still stretches, from `python output/qa_playthrough_20261026/summarize_runs.py`: `f_0047.png` (46 s) to
  `f_0068.png` (67 s) and `f_0070.png` (69 s) to `f_0129.png` (128 s), and an md5 over the files says `f_0047` to
  `f_0068` is one picture and `f_0069` to `f_0129` is one picture, so the second still starts at 68 s
- 48 distinct pictures in 129 frames
- `output/qa_playthrough_20261026/frames_oct27_skip/f_0001.png` to `f_0128.png`, 128 files, one per second, 0 s to
  127 s, from the same tool with `--script output/qa_playthrough_20261026/qa_skip_route.json --out-dir
  output/qa_playthrough_20261026/frames_oct27_skip --idle-wait 600`
- `output/qa_playthrough_20261026/route_frame_measures_skip.json`, the same measure over the skip take: stills of 6
  frames (46 s to 51 s), 19 frames (54 s to 72 s) and 54 frames (74 s to 127 s), and `f_0053.png` the one frame the
  measure cannot call the game (share 0.352)
- an md5 over `frames_oct27_skip/f_0075.png` to `f_0128.png` returns 1 distinct hash, so finding 2's 54 frames are one
  picture

## 5. What is not measured, and why

- The arrival walk, the gate, the boarding, the deck walk, the sailor's talk and the first fight: findings 1 and 2
  freeze the picture before them and finding 3 ends every take at 143 s, so nothing later was drawn where a camera
  could see it for long enough to judge. The skip take does show the arrival itself, one still picture of the quay
  (`frames_oct27_skip/f_0080.png`), and that is the farthest any take got.
- `a frame where nothing responds to input for more than 3 seconds`: the input side is invisible in a still. The one
  input the logs do witness is the skip hold, accepted at 61.1 s to 62.7 s (`_grab_oct27_skip.log`), and after it the
  picture changed twice more before the last 54 s still, which is finding 2 rather than an answer to this question.
- Sound: every take is launched muted (`PP_MUTE=1`, and the `PP: muted` line is in `build/qa-grab-game.log`), so
  nothing here is a listening test. Findings 4 and 5 are the game's own log lines and the project file, not an ear.
- The ship interior, the deck and therefore the 30 s held walk: the scout route that skips the drive
  (`output/qa_playthrough_20261026/qa_skip_route.json`) got as far as the Town Quay arrival and no further, because
  the same 143 s wall stopped it, and its last scripted key lands at 62.7 s, so nothing after the arrival was driven.
- Why the full route's log goes quiet 5 characters into `drive_sign_55` while the skip route's log runs on to the
  arrival: not settled here. A hang in the reveal and a picture that stopped updating look the same from outside, and
  the one cheap test is a take that presses a key every 5 s through the still.

## 6. The static gates, measured on the same tree

Run in one pass, `output/qa_playthrough_20261026/_static_checks_oct27.log`:

- `check_project` exit 1, 25 problems (finding 5)
- `check_data`, `check_font_coverage`, `check_ui_nes`, `check_cues`, `check_env_tiles`, `check_runtime_palette`,
  `check_scene_palettes`, `check_cleanroom` all exit 0
- `check_font_coverage` scanned 225 printed strings across six data files and found 0 missing glyphs, so the missing
  text on screen in this build is not a font hole (`data/dialogue/all.json` and four more, same log line 39 to 49)

## 7. The host, measured

`python output/qa_playthrough_20261026/probe_host.py`:

    monitors: 2   (\\.\DISPLAY1 1920x1080 at 0,0 and \\.\DISPLAY2 1920x1080 at 1920,0)
    power: AC line status 1 (plugged in)
    memory: 95% in use, 1.55 GB free of 31.82 GB

`powercfg /q SCHEME_CURRENT SUB_SLEEP` reports AC sleep after 0 (never) and `SUB_VIDEO` reports display off after
3600 s, so the 143 s wall is not a power plan. `wevtutil qe System` for Display, Kernel-Power and DxgKrnl returns no
event on 2026-10-27, and the last Kernel-Power 41 is 2026-10-23, so the wall is not a driver reset or a reboot.

## 8. The earlier build, 2026-10-26 22:49, kept because its frames exist and its defects are the same class

These were measured on the previous build with the same route and a different recorder, and their frames are on disk
under `output/screens_newest/`. They are not evidence about the 06:59 build; they are here so the history is not lost.

| sev | frame | what a player saw | probable owner |
| --- | --- | --- | --- |
| 1 | `output/screens_newest/frames_show/f_0048.png`, `f_0070.png`; `output/screens_newest/frames_skip/f_0053.png` | the screen stopped following the game after the crawl: one still for 22 s, one repaint, then a still for 32 s and for 72 s in two runs | `game/scripts/pp_overworld/pp_overworld.gml`, `game/scripts/pp_scene/pp_scene.gml` |
| 1 | `output/screens_newest/frames_skip/f_0058.png` | the `hold X to skip` prompt stayed on screen after the skip had been accepted and logged | the same two files |
| 2 | log line only | the drive's music cue had no OGG and played a placeholder | `data/audio.json` PP-02 and the missing stream (now on disk, still unlisted: finding 4) |
| 2 | log line only | `PP: role hazard is not in the room palette set quay_night, drawing it as PP_COLOUR_MISSING` on the quay | `data/maps/all.json`, room `southampton_town_quay`, palette `quay_night` |
| 2 | `output/screens_newest/frames_show/f_0004.png` | the title logo ran off the top edge | `game/scripts/pp_title/pp_title.gml` |
| 3 | `output/screens_newest/frames_show/f_0040.png` | one centred `P` on an otherwise empty crawl line | `game/scripts/pp_title/pp_title.gml` |

## 9. What finishes this card

In this order, from `<repo>`:

1. Fix findings 4 and 5 with `python tools/gen_project.py`, then rebuild with
   `python tools/integration_build.py` (the same compile `tools\run.ps1 -SkipChecks` runs, and `check_project` itself
   is the gate that should have refused this build).
2. Settle finding 1 and finding 2 in one take: press a key every 5 s through the still, with the route stopped after
   the arrival, and see whether the picture moves. If it does not, the suspects are the reveal in `game/scripts/pp_text`
   and `pp_scene.gml` `case "say"` at line 190, and the room draw in `game/scripts/pp_overworld/pp_overworld.gml`.
3. Give the take a host with memory before asking for the fight: finding 3 caps every take at 143 s, and the balancer
   measured 0.3 GB to 0.9 GB free (`guard\balancer.log` at 07:13 and 07:24).
4. Re-run the two captures, which write frames as they go and so survive a stall:
   `python output/screens_newest/play_and_grab.py --script output/qa_playthrough_20261026/qa_full_route.json --out-dir output/qa_playthrough_20261026/frames_route --idle-wait 900`
   `python output/screens_newest/play_and_grab.py --script output/qa_playthrough_20261026/qa_held_walk.json --out-dir output/qa_playthrough_20261026/frames_walk --idle-wait 900`
5. Then `python output/qa_playthrough_20261026/analyze_frames.py --mode route --frames-dir <folder>` and
   `python output/qa_playthrough_20261026/finish_take.py` for the 30 s cut.
6. The launch gate needs `codex.exe` and `codex-computer-use-swift.exe` stopped, or a host without a desktop
   automation: it read the process list as unreadable at 07:05 and again at 07:27, and refused on presence at 07:00
   and again at 07:31.

## 10. Commands, their output and the node

All from `<repo>` on CitadelArana, the desktop, 2026-10-27
07:00 to 07:50 PDT.

1. `python tools/idle_check.py` -> `P: idle gate REFUSED: a desktop automation is running
   (codex-computer-use-swift.exe, codex.exe)`, exit 4. `tasklist /v` on the second one:
   `Window Title: ChatGPT is using your computer. Esc to cancel`, `Status: Running`.
2. `python tools/play_demo.py --script output/qa_playthrough_20261026/qa_full_route.json --out
   output/qa_playthrough_20261026/qa_route_oct27.mp4 --idle-wait 1500` (background) ->
   `P: idle gate cannot read this host's process list ... P: idle gate allows the launch: no input for 1361 s`,
   `PP: muted`, `window: moved off the primary screen to 1920,0`, `recording 322.5 s of the window to
   output/demo/_qa_full_route_raw.mp4`, events `q02` 10.2 s, `q03` 11.6 s, `q04` 11.7 s, `q08` 48.9 s, then
   `P: exit: demo recording, the game process is closed (pid 43140, code 1)` and
   `the clock stopped advancing at step 8605, 395 steps short of 9000`. No mp4 was closed, so this path gave no frames.
3. Recovery of that raw file, in four steps, all refused by the data: `python
   output/qa_playthrough_20261026/probe_boxes.py` lists `ftyp`, `free`, `mdat` and no `moov`;
   `dump_mdat.py` cuts 18,350,080 bytes of payload; `avcc_to_annexb.py` rewrites 8664 NAL units;
   `prepend_sps.py` copies the SPS and PPS (24 and 6 bytes) from `output/demo/_walk_ref.h264` (extracted from
   `output/demo/demo-walk-2026-10-26.mp4`, same encoder, 768x720 High). Decoding still fails at a 0.98 error rate
   because the killed take is the 784x759 window copy and the borrowed parameter sets are the 768x720 finished ones.
   `output/qa_playthrough_20261026/route_oct27_v2/` holds the 136 pictures that decode produced and they are NOT
   evidence.
4. `python output/screens_newest/play_and_grab.py --script output/qa_playthrough_20261026/qa_full_route.json
   --out-dir output/qa_playthrough_20261026/frames_oct27 --idle-wait 600` -> `P: idle gate allows the launch: no
   input for 130 s, 120 s required`, `PP: muted`, `window: 'Primordial Paradox' (hwnd 26546540)`, `coverage: clear`,
   `pre-roll viewport: [8, 31, 768, 720] score 1.000`, `grabbing the viewport every 1.0 s`, 129 frames to 143.06 s,
   then `failures: the replay stopped early: the clock stopped advancing at step 8604, 396 steps short of 9000`
   and `P: exit: QA window grabs, the game process is closed (pid 14104, code 1)`.
5. `python output/qa_playthrough_20261026/analyze_frames.py --mode route --frames-dir
   output/qa_playthrough_20261026/frames_oct27` -> 129 frames, `off_palette_art ["f_0045.png"]`, `not_the_game []`,
   `black_frames` `f_0016` to `f_0021`, `frozen_runs [22, 60]`, `min_share 0.6905`, `max_share 0.9999`.
6. `python output/qa_playthrough_20261026/summarize_runs.py output/qa_playthrough_20261026/route_frame_measures.json`
   -> `129 frames, seconds 0 to 128` and the two stills above.
7. `md5sum` over `frames_oct27/f_0047.png` to `f_0068.png` -> 1 distinct hash `2779e7fdd942ffff8a6e996e81ddc5bb`;
   over `f_0069.png` to `f_0129.png` -> 1 distinct hash `9c0dae9779a6e4c87fd3eb76285ee19f`.
8. `sed -n '145,167p' build/qa-grab-game.log` -> the crawl hands to the drive, the PP-02 placeholder line, the engine
   loop, five `text_blip_a` lines, end of file. 167 lines in the whole log, 106 of them text blips.
9. `python tools/check_project.py` -> 25 `is not listed as an Included File` lines, exit 1; the rest of the checks in
   `output/qa_playthrough_20261026/_static_checks_oct27.log` exit 0.
10. `python output/qa_playthrough_20261026/probe_host.py` -> the two monitors, AC line status 1 and the memory line,
     quoted in section 7.
11. `grep -n "hold X to skip" -B 6 -A 6 game/scripts/pp_overworld/pp_overworld.gml` -> the prompt is drawn at 8, 8,
    so it is not clipped (finding 9).
12. `sed -n '255,300p' data/scenes/all.json` -> the drive's command list, which says the camera holds at x=0 for 1202
    steps and then jumps to x=37 before `say drive_sign_55` (finding 6 and finding 1).
13. `python output/screens_newest/play_and_grab.py --script output/qa_playthrough_20261026/qa_skip_route.json
    --out-dir output/qa_playthrough_20261026/frames_oct27_skip --idle-wait 600` -> allowed after
    `a desktop automation is running (codex-computer-use-swift.exe, codex.exe)` gave way, 128 frames to 127 s, then
    `failures: the replay stopped early: the clock stopped advancing at step 8601, 399 steps short of 9000` and
    `P: exit: QA window grabs, the game process is closed (pid 8332, code 1)`. `build/qa-grab-game.log` then carries
    `PP scene: drive_to_southampton skipped by the player after 30 steps of holding cancel`,
    `PP scene: drive_to_southampton end at tile 0,8` and
    `PP route: step drive handed to step arrival (arrival at Town Quay)` at lines 163 to 165, and ends with four
    `focus lost` / `focus back` pairs.
14. `python output/qa_playthrough_20261026/analyze_frames.py --mode route --frames-dir
    output/qa_playthrough_20261026/frames_oct27_skip` -> 128 frames, `not_the_game ["f_0053.png"]`,
    `frozen_runs [6, 19, 54]`, `min_share 0.352`, `max_share 0.9999` (kept as
    `output/qa_playthrough_20261026/route_frame_measures_skip.json`); `summarize_runs.py` prints the three stills.
15. `md5sum` over `frames_oct27_skip/f_0075.png` to `f_0128.png` -> 1 distinct hash (finding 2).
16. `tail` of `<workspace>\Shared\projects\arananet\manager\guard\balancer.log` ->
    `2026-10-27T07:13:29 memory low (0.9 GB free): no dispatch, no moves` and
    `2026-10-27T07:24:36 memory low (0.3 GB free): no dispatch, no moves` (finding 3).
