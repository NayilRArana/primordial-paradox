# QA-PLAYTHROUGH 2026-10-27: the played route, the frames, and the ranked bug list

Card t_84fe6ab8 (lane testing, node CitadelArana, the desktop). The build under test is
`output/PrimordialParadox/PrimordialParadox.win`, sha256
`e5a4b6b56cc83751bc7ed6e083fed1604bedf09f8336d92263968f808adecf5f`, written 2026-10-27 06:59:19 -0700
(`output/qa_playthrough_20261026/_build_identity_oct27.txt`). The earlier build, written 2026-10-26 22:49, is
quoted only in section 8 and only where its frames are named.

Status in one line: the title, the menu and the crawl played, the drive started, and at 69 s the drive's first
cutscene line opened and drew nothing, so the picture never changed again for the rest of the take. The cause is
measured and it is one line of code, not the host: a scene `say` stores its dialogue box on the scene, the only
draw call reads the world, so **no cutscene line in this build can draw a box**. Every scene the demo still needs
opens with a `say`, so the arrival walk, the gate, the boarding, the deck, the sailor's talk, the first fight and
the 30 second held walk are NOT MEASURED.

Nothing on the card's MUST NOT list was done. No game file was changed. The files written are under
`output/qa_playthrough_20261026/`, `output/demo/` (the killed raw recordings) and this knowledge file. Nothing was
posted, pushed or published, no other lane's process was killed, and no `--force` was passed to the launch gate.

## 1. The findings, newest build

Severity 1 is a demo stopper: a player or a judge cannot see the shot. Severity 2 is visible on screen or in the
audio and costs demo points. Severity 3 is small, or a warning so that nobody re-reports it. Every frame path in
this table exists on disk and every severity 1 finding has a frame.

| # | sev | frame | what a player sees | probable owner |
| --- | --- | --- | --- | --- |
| 1 | 1 | `output/qa_playthrough_20261026/frames_oct27/f_0069.png` to `f_0129.png` (61 identical frames, 68 s to 128 s, one md5 `9c0dae9779a6e4c87fd3eb76285ee19f`, and `f_0090.png` is the copy to open) | From 69 s the drive holds one picture: grey wall, white rail, green ground, the reading `hold X to skip` at the top left, and no dialogue box anywhere on screen. The drive's first line is open at that second, the reveal is typing it (the log plays five text blips and stops), and none of it is drawn. The box's own rectangle is empty: sampled at the box's coordinates it holds three greens and nothing else (`_crop_f0090_box.png`, section 4), so this is not a box drawn in the wrong colour, it is a box that is never drawn. The scene then waits for confirm, which a scripted run never sends, so the demo stops dead there and stays stopped. | `game/scripts/pp_scene/pp_scene.gml:191`, which stores the box on the scene (`_sc.dialogue = pp_dialogue_open(_cmd.id)`), against `game/scripts/pp_overworld/pp_overworld.gml:906`, which is the one place a box is drawn and it reads `_world.dialogue`. The only writes to `_world.dialogue` are the map trigger at `pp_overworld.gml:543` and the talk path at `:808`; there is no write from the scene path, and `pp_dialogue_closed(undefined)` returns true (`game/scripts/pp_dialogue/pp_dialogue.gml:326`), so the draw block is skipped entirely |
| 2 | 1 | `output/qa_playthrough_20261026/frames_oct27_skip/f_0080.png` (part of 54 identical frames, 74 s to 127 s, one md5 `f7677ff95f7f4668a54752e3e2ddf963` over `f_0075.png` to `f_0128.png`), and no frame exists for the shots after it because they were never drawn | Every remaining shot of the demo opens with a scene `say`, so the same missing draw stops the route four more times: `ship_boarding` (say `ship_gangway` at scene 4.2 s), `ship_log` (say `ship_log_open` at 0.0 s), `quay_gate_checkpoint` (say `quay_gate_checkpoint` at 0.0 s) and `quay_dock_office_play` (say `quay_dock_office` at 0.0 s), from `data/scenes/all.json` read by `output/qa_playthrough_20261026/scene_says.py`. The skip take is the live proof: it reaches the arrival at Town Quay, the log records it (`PP route: step drive handed to step arrival`, `build/qa-grab-game.log:165`), and then the picture holds that one quay frame for 54 s. A judge would see a still picture at every one of those scenes, with no text and nothing to explain why. | the same pair of lines as finding 1 |
| 3 | 1 | `frames_oct27/f_0129.png` (128 s) and `frames_oct27_skip/f_0128.png` (127 s), which is as far as any take got | Every take today ends at 143.4 s with `the clock stopped advancing at step 8604, 396 steps short of 9000`, and a second take with `step 8601, 399 steps short of 9000`, so the stop is at the same place every time. This one is the host, not the game: the clock that fails is wall clock (`tools/play_demo.py:427` to `:437`), so the harness process itself got no CPU for 60 s, and the host reads 98% of RAM in use with 0.42 GB free (`python output/qa_playthrough_20261026/probe_host.py`, re-measured 2026-10-27). The manager's balancer logged the same pressure twice during the runs: `memory low (0.9 GB free)` at 07:13 and `memory low (0.3 GB free)` at 07:24 (`<workspace>\Shared\projects\arananet\manager\guard\balancer.log`). | the host, not the game: `tools/play_demo.py` and `output/screens_newest/play_and_grab.py` both die at it |
| 4 | 2 | log line `build/qa-grab-game.log:159`, no frame | The drive's music is a placeholder in the built game. The row says the master is delivered (`data/audio.json`, PP-02, `"pending": false`, `assets/audio/pp_drive_master1/pp_drive_master1.ogg`) and the OGG is on disk (`game/datafiles/streams/pp_drive_master1.ogg`, 2,221,427 bytes, 2026-10-26 11:44), but the game logs `PP audio: music cue PP-02 has no OGG yet, expected pp_drive_master1.ogg, placeholder 1` at the second the drive starts. | `game/PrimordialParadox.yyp`: `python tools/check_project.py` reports 25 files on disk that are not listed as Included Files, and `pp_drive_master1.ogg` is one while the older `pp_drive_v2.ogg` is the one still listed. The list is generated, so the fix is `python tools/gen_project.py` plus a rebuild |
| 5 | 2 | no frame: `python tools/check_project.py`, exit 1, 25 problems | The same miss takes the sound out of the rest of the route. Unlisted and therefore absent from the built game: `footstep_a.ogg`, `footstep_b.ogg`, `knife_slash.ogg`, `text_blip_kronos.ogg`, `text_blip_narrator.ogg`, `text_blip_oldman.ogg`, `text_blip_percy.ogg`, `text_blip_zeus.ogg`, `pp_01_title_v9.ogg`, `pp_03_harbor_master1.ogg`, `pp_04_navy_sailors_master1.ogg`, `pp_boarding_master1.ogg`, `title_theme_v6.ogg` (`output/qa_playthrough_20261026/_static_checks_oct27.log:13` to `:26`). The walk and the fight are carried by footsteps and the knife. | `game/PrimordialParadox.yyp`, whose Included Files list is generated by `tools/gen_project.py`; `tools/check_project.py` is the gate that should have blocked the build |
| 6 | 3 | `frames_oct27/f_0047.png` (md5 `2779e7fdd942ffff8a6e996e81ddc5bb`, 22 identical frames, 46 s to 67 s) | A still picture for 22 s at the start of the drive. This one is NOT a bug and is listed so nobody re-reports it: the scene holds the camera at x=0 for `wait 600`, `wait 2`, `wait 600` before it moves (`data/scenes/all.json`, scene `drive_to_southampton`), which is 20 s of a picture that is meant not to move. | none: `data/scenes/all.json` says the hold on purpose |
| 7 | 3 | `frames_oct27/f_0045.png` | The only frame outside the palette: share 0.6905, 24 colours, mean luma 4.78 (`output/qa_playthrough_20261026/route_frame_measures.json`). It is the dissolve from the crawl into the scene, it sits between two in-palette frames, and it is not foreign art. | none: mark it, do not chase it |
| 8 | 3 | `frames_oct27/f_0016.png` to `f_0021.png` | Six black frames at 16 s to 21 s. That is the intro fade, on purpose, and a black frame scores a legal NES colour. | none |
| 9 | 3 | `frames_oct27/f_0030.png` and `frames_oct27_skip/f_0053.png` | The crawl's lowest visible line is a half line (`A SA`), which is the text scrolling in, not a line running out of its box. The skip prompt is drawn at x 8, y 8 (`game/scripts/pp_overworld/pp_overworld.gml:924`), so the prompt is not clipped either. In the skip take `f_0053.png` (52 s) is the one frame the measure cannot call the game at all, share 0.352 and 26 colours, and it is the skip transition itself. | none: `game/scripts/pp_title/pp_title.gml` scrolls it on purpose |
| 10 | 3 | none: the log of the take that carried the evidence | The grab tool writes every take's game log to one fixed path, `build/qa-grab-game.log` (`output/screens_newest/play_and_grab.py:108`), so a later take overwrites an earlier one's evidence. The full route's log was overwritten by the skip take at 07:30 and cannot be re-read; the finding 1 claim that rests on it is instead proved by the frames and by the code, which do not disappear. A tool that copies the log beside the frames would stop this. | `output/screens_newest/play_and_grab.py`, and the same one path in `tools/play_demo.py` |
| 11 | 2 | `frames_oct27/f_0001.png` (0 s, the title), cropped at `output/qa_playthrough_20261026/_crop_f0001_lowerleft.png` | The title screen draws a sign panel about 40 game pixels off the left edge of the screen, so the two lines a player can read are `STOKE 20` and `MPTON 55` instead of `BASINGSTOKE 20` and `SOUTHAMPTON 55`, and the panel's own left border is off screen. This is the demo's first shot, and it is not in the 22:49 build: `output/screens_newest/frames_show/f_0004.png` is the same title with no panel on it at all, so this is new in the 06:59 build. The two lines it is clipping are the two pages of `drive_sign_55` (`* SOUTHAMPTON 55.` and `* BASINGSTOKE 20.`, `data/dialogue/all.json`), which is the same dialogue finding 1 is about, drawn here at an x off screen instead of not drawn. | `game/scripts/pp_title/pp_title.gml` for the composition, and whichever draw path puts that panel up: the box's own rect is at x 8 (`game/scripts/pp_config/pp_config.gml:235`) and this panel is not, so it is a second draw of sign text with its own alignment |

### The one line that proves finding 1

Read on the same tree as the build, 2026-10-27:

    grep -rn "_world\.dialogue *=" game/scripts/          -> only pp_overworld.gml:543 (map trigger say),
                                                             :740, :744 (clearing), :808, :809 (talk)
    grep -rn "_sc\.dialogue *=" game/scripts/             -> pp_scene.gml:191 (opening a scene say), :435, :497, :674
    grep -rn "pp_dialogue_draw(" game/scripts/*/*.gml     -> pp_overworld.gml:906 only, and it reads _world.dialogue
    grep -n "function pp_dialogue_closed" pp_dialogue.gml -> :326, and an undefined box is closed, so line 905
                                                             skips the whole draw block

A scene `say` therefore opens a box that is stepped (`pp_scene_step`, `pp_scene.gml:475` to `:498`, which calls
`pp_dialogue_step` and waits for `pp_pressed("confirm")`) and never drawn. The reveal keeps running, which is why
the text blips play, and nothing appears, which is why 61 frames in a row are byte identical.

Numbers that agree with it, each measured today:

- the drive scene reaches `camera 37` and `say drive_sign_55` at scene 23.5 s (`scene_timeline.py`), and the route's
  crawl handoff puts the scene's first second at 46 s of the recording, so the line opens at 69 s of the take;
  the picture changes once at 68 s (the camera move, the blue pixels leaving the frame) and never again.
- `drive_sign_55` page 0 is `* SOUTHAMPTON 55.`, 15 non-space characters, and the blip interval is 3
  (`game/scripts/pp_config/pp_config.gml:264`), so the page is exactly 5 blips, and the log's last five text blips
  are a narrator line (`pp_audio_blip_cue` sends narrator to `text_blip_a`, `game/scripts/pp_audio/pp_audio.gml:497`).
  The reveal completed the page and then waited. An earlier draft of this report read those five blips as five
  characters typed; it is fifteen, and the correction is why the stop is a completed page waiting for a press and
  not a game that died mid word.
- the scene schedules `fade out`, `fade in` and `camera 83` at scene 80.3 s, which is 126.3 s of the recording.
  Frames f_0127 to f_0129 are past that second and are identical to f_0069, so the scene did not merely look static,
  it did not advance.

What a player gets out of this: pressing confirm does still advance the page, because `pp_scene_step` reads the key
before it draws anything, so a human can push through a cutscene blind. An unattended demo, a judge watching a
recording, or anybody who expects a box to appear cannot.

## 2. The ten that cost the most Demo points, in order

The demo is scored out of 25 over six shots, S1 title, S2 crawl, S3 drive, S4 gate, S5 dock office and S6 fight
(`knowledge/DEMO-SCRIPT.md`). Six ranked findings is the honest length, not ten: finding 1 stops S3 in its first
minute, finding 2 repeats that stop at the head of S4, S5 and S6, and finding 3 ends every take at 143 s.

| rank | finding | the shot it costs | why it costs those points |
| --- | --- | --- | --- |
| 1 | finding 1, no cutscene box is drawn, so the drive holds one picture from 69 s | S3 drive, and with it S4, S5 and S6 | four of six shots sit after that second; a judge who cannot see past the still cannot score the gate, the dock office or the fight, and the one line to fix is named |
| 2 | finding 2, the same missing draw at the head of every later scene | S4 gate, S5 dock office and S6 fight | it is why fixing the drive alone does not make the demo runnable: each of the three later shots opens with a `say` and would stop on its first second |
| 3 | finding 3, every take dies at 143.4 s on this host | every shot after S3 in practice | it is the reason this report cannot answer for the ship, the talk or the fight, and the reason a fix can only be checked in takes shorter than 143 s until the host has memory |
| 4 | finding 11, the title screen clips a sign panel off the left edge | S1 title | it is the first picture a judge sees and the words on it are cut in half, so the demo's opening frame reads as a bug rather than as a deliberate NES sign |
| 5 | finding 4, the drive's music is a placeholder | S3 drive | the shot's claim is an NES faithful night drive, and its music is the first thing a judge hears |
| 6 | finding 5, footsteps, knife and six blips are not in the project file | S4 gate, S5 dock office, S6 fight | the walk and the fight are carried by footsteps and the knife; without them the two loudest shots are silent |

## 3. The 30 second capture of held walking

Not measured, and now for a precise reason rather than a vague one: the held walk script starts on the ship's deck
(`output/qa_playthrough_20261026/qa_held_walk.json`, holds at 60.00 s, 71.67 s and 83.33 s of a 95 s script), the
deck is reached through `ship_boarding`, and `ship_boarding` opens with `say ship_gangway` at scene 4.2 s. So the
held walk is behind both finding 1 and finding 3, and it cannot be measured on this build at all until a cutscene
box draws.

The last measured answer on the walking question is the 2026-10-26 take, and it is a red, not a pass:
`output/demo/hold_walk-2026-10-26.json` carries `footstep_cues 8` against `footstep_floor 37`, and its frames are
static after the first second because `ship_small` row 7 is eight tiles long (`data/maps/all.json`).

## 4. The frames this report was built from

Every path below exists on disk. `output/*` is ignored by git (`projects/primordial-paradox/.gitignore:28`), so the
frames are local to this host and are regenerated by the commands in section 10.

- `output/qa_playthrough_20261026/frames_oct27/f_0001.png` to `f_0129.png`, 129 files, one per second, 0 s to 128 s,
  from `python output/screens_newest/play_and_grab.py --script output/qa_playthrough_20261026/qa_full_route.json
  --out-dir output/qa_playthrough_20261026/frames_oct27 --idle-wait 600`
- `output/qa_playthrough_20261026/frames_oct27/_preroll.png` (the tool's own pre-roll picture, not a frame, which is
  why the folder holds 130 png files for 129 frames)
- `output/qa_playthrough_20261026/frames_oct27/grab_run.json`, the tool's summary: `first_second 0.0`,
  `last_second 143.06`, `viewport_box [8, 31, 768, 720]`
- `output/qa_playthrough_20261026/route_frame_measures.json`, one measured row per frame of the full route take,
  from `python output/qa_playthrough_20261026/analyze_frames.py --mode route --frames-dir
  output/qa_playthrough_20261026/frames_oct27`
- the still stretches, from `python output/qa_playthrough_20261026/summarize_runs.py`: `f_0047.png` (46 s) to
  `f_0068.png` (67 s) and `f_0069.png` (69 s) to `f_0129.png` (128 s), and an md5 over the files says `f_0047` to
  `f_0068` is one picture and `f_0069` to `f_0129` is one picture
- 48 distinct pictures in 129 frames
- `output/qa_playthrough_20261026/frames_oct27_skip/f_0001.png` to `f_0128.png`, 128 files, one per second, 0 s to
  127 s, from the same tool with `--script output/qa_playthrough_20261026/qa_skip_route.json --out-dir
  output/qa_playthrough_20261026/frames_oct27_skip --idle-wait 600`
- `output/qa_playthrough_20261026/route_frame_measures_skip.json`, the same measure over the skip take: stills of 6
  frames (46 s to 51 s), 19 frames (54 s to 72 s) and 54 frames (74 s to 127 s), and `f_0053.png` the one frame the
  measure cannot call the game (share 0.352)
- an md5 over `frames_oct27_skip/f_0075.png` to `f_0128.png` returns 1 distinct hash, so finding 2's 54 frames are one
  picture
- `output/qa_playthrough_20261026/_crop_f0090_box.png`, the dialogue box's own rectangle cut out of `f_0090.png` at
  2x, which is the picture that shows the box is not there
- `output/qa_playthrough_20261026/_crop_f0090_top.png`, the top of the same frame at 2x, which is the picture of the
  `hold X to skip` line that is there

## 5. What is not measured, and why

- The arrival walk, the gate, the boarding, the deck walk, the sailor's talk and the first fight: finding 1 stops the
  drive at its first line and finding 2 stops every later scene at its own first line, so nothing later was ever
  drawn where a camera could see it. The skip take does show the arrival itself, one still picture of the quay
  (`frames_oct27_skip/f_0080.png`), and that is the farthest any take got.
- `a frame where nothing responds to input for more than 3 seconds`: the stills in finding 1 and 2 are a picture that
  does not move while the game does read input, so this question is answered as "the picture is still, the input is
  not dead", and it is not the same defect. Any longer input test sits behind the same cutscene stop.
- Sound: every take is launched muted (`PP_MUTE=1`, and the `PP: muted` line is in `build/qa-grab-game.log`), so
  nothing here is a listening test. Findings 4 and 5 are the game's own log lines and the project file, not an ear.
- Whether a box drawn in the wrong place or the wrong colour is also happening: it cannot be, on these frames, because
  the box rect holds only grass greens and no missing colour marker; that is measured in section 1, finding 1.

## 6. The static gates, measured on the same tree

Run in one pass, `output/qa_playthrough_20261026/_static_checks_oct27.log`:

- `check_project` exit 1, 25 problems (finding 5)
- `check_data`, `check_font_coverage`, `check_ui_nes`, `check_cues`, `check_env_tiles`, `check_runtime_palette`,
  `check_scene_palettes`, `check_cleanroom` all exit 0
- `check_font_coverage` scanned 225 printed strings across six data files and found 0 missing glyphs, so the missing
  text on screen in this build is not a font hole and not a glyph the sheet lacks: the box is never handed to the
  draw call at all (section 1)

## 7. The host, measured

`python output/qa_playthrough_20261026/probe_host.py`, re-run 2026-10-27 late in the day:

    monitors: 2   (\\.\DISPLAY1 1920x1080 at 0,0 and \\.\DISPLAY2 1920x1080 at 1920,0)
    power: AC line status 1 (plugged in)
    memory: 98% in use, 0.42 GB free of 31.82 GB

`powercfg /q SCHEME_CURRENT SUB_SLEEP` reports AC sleep after 0 (never) and `SUB_VIDEO` reports display off after
3600 s, so the 143 s wall is not a power plan. `wevtutil qe System` for Display, Kernel-Power and DxgKrnl returns no
event on 2026-10-27, and the last Kernel-Power 41 is 2026-10-23, so the wall is not a driver reset or a reboot.

`python tools/idle_check.py` still answers `REFUSED: a desktop automation is running
(codex-computer-use-swift.exe, codex.exe)` with exit 4 on this host, so no further take was possible in this run
either; the gate refuses on presence (`tools/idle_check.py:145` to `:161`), and `--force` is a human override that
this lane does not use.

## 8. The earlier build, 2026-10-26 22:49, kept because its frames exist and its defects are the same class

These were measured on the previous build with the same route and a different recorder, and their frames are on disk
under `output/screens_newest/`. They are not evidence about the 06:59 build; they are here so the history is not lost.

| sev | frame | what a player saw | probable owner |
| --- | --- | --- | --- |
| 1 | `output/screens_newest/frames_show/f_0048.png`, `f_0070.png`; `output/screens_newest/frames_skip/f_0053.png` | the screen stopped following the game after the crawl: one still for 22 s, one repaint, then a still for 32 s and for 72 s in two runs | the same assignment gap, now measured on the newest build as finding 1 (`game/scripts/pp_scene/pp_scene.gml:191` against `game/scripts/pp_overworld/pp_overworld.gml:906`) |
| 1 | `output/screens_newest/frames_skip/f_0058.png` | the `hold X to skip` prompt stayed on screen after the skip had been accepted and logged | the same prompt the newest build draws at `pp_overworld.gml:924`, which clears on the hold count rather than on the scene ending |
| 2 | log line only | the drive's music cue had no OGG and played a placeholder | `data/audio.json` PP-02 and the missing stream (now on disk, still unlisted: finding 4) |
| 2 | log line only | `PP: role hazard is not in the room palette set quay_night, drawing it as PP_COLOUR_MISSING` on the quay | `data/maps/all.json`, room `southampton_town_quay`, palette `quay_night` |
| 2 | `output/screens_newest/frames_show/f_0004.png` | the title logo ran off the top edge | `game/scripts/pp_title/pp_title.gml` |
| 3 | `output/screens_newest/frames_show/f_0040.png` | one centred `P` on an otherwise empty crawl line | `game/scripts/pp_title/pp_title.gml` |

## 9. What finishes this card

In this order, from `<repo>`:

1. Give the scene its box: either `pp_overworld_draw` reads the running scene's dialogue as well as the world's, or
   `pp_scene_command_start` writes the box to `_world.dialogue` at `pp_scene.gml:191` and the scene steps it from
   there. One writer for the box, whichever way it goes, or the two copies drift again.
2. `python tools/gen_project.py` for findings 4 and 5, then rebuild with `python tools/integration_build.py`; the
   `check_project` row is the gate that should have refused this build.
3. Give the take a host with memory before asking for the fight: finding 3 caps every take at 143 s, and this host
   reads 0.42 GB free.
4. Re-run the three captures, which write frames as they go and so survive a stall:
   `python output/screens_newest/play_and_grab.py --script output/qa_playthrough_20261026/qa_full_route.json --out-dir output/qa_playthrough_20261026/frames_route --idle-wait 900`
   `python output/screens_newest/play_and_grab.py --script output/qa_playthrough_20261026/qa_skip_route.json --out-dir output/qa_playthrough_20261026/frames_skip --idle-wait 900`
   `python output/screens_newest/play_and_grab.py --script output/qa_playthrough_20261026/qa_held_walk.json --out-dir output/qa_playthrough_20261026/frames_walk --idle-wait 900`
5. Then `python output/qa_playthrough_20261026/analyze_frames.py --mode route --frames-dir <folder>` and
   `python output/qa_playthrough_20261026/finish_take.py` for the 30 s held walk cut.
6. The launch gate needs `codex.exe` and `codex-computer-use-swift.exe` stopped, or a host without a desktop
   automation.

## 10. Commands, their output and the node

All from `<repo>` on CitadelArana, the desktop, 2026-10-27,
07:00 to 07:50 for items 1 to 5 and 08:00 to 08:40 for items 6 to 14.

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
   `prepend_sps.py` copies the SPS and PPS (24 and 6 bytes) from `output/demo/_walk_ref.h264`. Decoding still fails
   at a 0.98 error rate because the killed take is the 784x759 window copy and the borrowed parameter sets are the
   768x720 finished ones. `output/qa_playthrough_20261026/route_oct27_v2/` holds the 136 pictures that decode
   produced and they are NOT evidence.
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
8. `python output/qa_playthrough_20261026/route_timeline.py` -> 40 events over 317.80 s at 60 fps;
   `q08` at step 3360 (56.0 s) carries the marker `PP title: the crawl handed to the route's step drive` and the note
   that the drive `needs no input`, which is the reason no key is sent after that second.
9. `python output/qa_playthrough_20261026/scene_timeline.py` -> the drive scene's 64 commands, `camera 37` and
   `say drive_sign_55` both at scene 23.5 s, `fade out` / `fade in` and `camera 83` at scene 80.3 s, 23 waits
   totalling 170.8 s of a 170.8 s scene.
10. `python output/qa_playthrough_20261026/scene_says.py` -> the scenes that open with a `say`: `ship_boarding`
    (`ship_gangway` at 4.2 s), `ship_log` (0.0 s), `quay_gate_checkpoint` (0.0 s), `quay_dock_office_play` (0.0 s),
    `drive_to_southampton` (12 says, first at 23.5 s).
11. `python output/qa_playthrough_20261026/drive_page_measure.py` -> `PP_TEXT_BLIP_EVERY: 3`,
    `drive_sign_55` speaker `narrator`, 3 pages, page 0 `'* SOUTHAMPTON 55.'` (17 characters, 2 spaces, so 15 that
    blip, and 5 blips at an interval of 3), and the take's last five blips are all `text_blip_a`.
12. `python output/qa_playthrough_20261026/frame_sizes.py` -> every frame is 768x720 RGB, and `f_0090`'s top strip
    holds 3 colours.
13. `python output/qa_playthrough_20261026/crop_box.py` -> the box rectangle (frame x 24 to 744, y 504 to 696) in
    `f_0055`, `f_0069` and `f_0090` holds exactly three colours in every one of them: `(0, 104, 0)`, `(0, 88, 0)`,
    `(0, 168, 0)`. Grass. No box, and no missing colour.
14. `python output/qa_playthrough_20261026/find_boxes.py` -> `f_0069`, `f_0090` and `f_0129` report the same 234
    rows with a long run, the same blocks and the same 28 colours in the same counts, so those three frames are one
    picture; `f_0065` differs and carries the blues `(0, 0, 252)` and `(164, 228, 252)` that leave the frame at 68 s.
15. `python output/qa_playthrough_20261026/confirm_mapping.py` -> the 28 colours of the frozen frame, none of them
    the missing colour marker, and the brightest `(248, 248, 248)` text starting at y 21, which is the prompt drawn
    at game y 8 times 3.
16. `grep -rn "_world\.dialogue *=" game/scripts/` and `grep -rn "_sc\.dialogue *=" game/scripts/` and
    `grep -rn "pp_dialogue_draw(" game/scripts/*/*.gml` -> the assignment gap quoted in section 1, and the single
    draw call site at `pp_overworld.gml:906`.
17. `sed -n '145,167p' build/qa-grab-game.log` (read before the skip take overwrote it) -> the crawl hands to the
    drive, the PP-02 placeholder line, the engine loop, five `text_blip_a` lines, end of file.
18. `python tools/check_project.py` -> 25 `is not listed as an Included File` lines, exit 1; the rest of the checks
    in `output/qa_playthrough_20261026/_static_checks_oct27.log` exit 0.
19. `python output/qa_playthrough_20261026/probe_host.py` -> the two monitors, AC line status 1, and
    `memory: 98% in use, 0.42 GB free of 31.82 GB`.
20. `grep -n "hold X to skip" -B 6 -A 6 game/scripts/pp_overworld/pp_overworld.gml` -> the prompt is drawn at 8, 8
    (line 924), so it is not clipped (finding 9).
21. `python output/screens_newest/play_and_grab.py --script output/qa_playthrough_20261026/qa_skip_route.json
    --out-dir output/qa_playthrough_20261026/frames_oct27_skip --idle-wait 600` -> allowed after
    `a desktop automation is running (codex-computer-use-swift.exe, codex.exe)` gave way, 128 frames to 127 s, then
    `failures: the replay stopped early: the clock stopped advancing at step 8601, 399 steps short of 9000`.
    `build/qa-grab-game.log` then carries `PP scene: drive_to_southampton skipped by the player after 30 steps of
    holding cancel`, `PP scene: drive_to_southampton end at tile 0,8`,
    `PP route: step drive handed to step arrival (arrival at Town Quay)` at lines 163 to 165, and ends with four
    `focus lost` / `focus back` pairs. That run is also what overwrote the full route's log (finding 10).
22. `tail` of `<workspace>\Shared\projects\arananet\manager\guard\balancer.log` ->
    `2026-10-27T07:13:29 memory low (0.9 GB free): no dispatch, no moves` and
    `2026-10-27T07:24:36 memory low (0.3 GB free): no dispatch, no moves` (finding 3).
23. `python tools/idle_check.py` again at the end of this run -> the same REFUSED line, exit 4, which is why the
    cutscene fix has not been watched running yet.
24. `python output/qa_playthrough_20261026/crop_title.py` -> `_crop_f0001_lowerleft.png` and `_crop_f0001_top.png`,
    the 2x crops that carry finding 11.
25. Read of `output/screens_newest/frames_show/f_0004.png`, the 22:49 build's title frame, against
    `output/qa_playthrough_20261026/frames_oct27/f_0001.png`, the 06:59 build's: the first has `PRIMORDIAL`,
    `PARADOX` and the copyright line and no sign panel at all, the second adds the panel that clips
    `BASINGSTOKE 20` and `SOUTHAMPTON 55` at the left edge (finding 11).
26. `python "<workspace>/Shared/projects/arananet/manager/guard/lane_commit.py" --repo
    "<workspace>/Shared" --lane testing -m "QA-PLAYTHROUGH (t_84fe6ab8) ..." --
    projects/primordial-paradox/knowledge/QA-PLAYTHROUGH-2026-10-26.md` -> `COMMITTED 5e02e638091f9eba0d27024b3cdb5937ec64ddaf
    lane=testing paths=2`, the report plus the gate log line the gate adds. The first two attempts exited 8 with
    `staged claim: FAIL`, because other lanes committed to the same repo while the private index was building
    (`DRIFT: the private index was built from HEAD ee04f81fc, and HEAD is now 4ac179edc`, then `4ac179edc` to
    `cb0c05d22`); the third fired straight after another lane's commit and landed.
