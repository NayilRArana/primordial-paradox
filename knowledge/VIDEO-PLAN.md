# Video plan: capture, ffmpeg chain, captions, receipts, description, thumbnail

Card t_97eec61b (GAME-ROADMAP-2 child R44), assistant, written 2026-10-22 for Primordial Paradox.
Scope: this file only. The write-up and the application draft belong to SUBMISSION-KIT (t_7b2f6aae); the recorder
belongs to DEMO-KIT (t_9ebd35dc); the bake belongs to R29. Nothing here edits those.

What it is for: a person with the finished take on disk runs three commands, types six captions and two receipts into
the edit, and exports. No shot, no caption and no second is decided in the booth.

Inputs read for this plan, with the state each one was in when it was read (2026-10-22, 19:50 to 20:20):

| Input | State at read | What it gave this file |
| --- | --- | --- |
| `knowledge/DEMO-SCRIPT.md` (R39) | landed, 429 lines, six shots, 180.00 s | every shot's screen, input, caption text, music cue, claim |
| `tools/play_demo.py` and `data/demo/run_001.json` (DEMO-KIT t_9ebd35dc) | landed and run for real: `output/demo/run_001.mp4`, 73.500 s, 768x720 | the capture region, the crop, the encoder settings that already work |
| `data/meta_bake.json` | **ABSENT.** R29 META-BAKE (t_f943951a) owns it | the shape the two receipt overlays read, never the values |
| `data/ai_cache/` | 6 entries, all `backend: mock`, `network: false` | which model ids the pipeline names, and the fact that no real call is on disk |
| `specs/13-8bit-look.md` | spec, numbers are decisions | 256x240, integer scale, point sample, no anti aliasing |
| `TITLE-COORD.md` | at the repo root, not `knowledge/` | the 512 px layers, the scroll speed table, 3x previews |
| `..\arananet\meta-hackathon\PLAN-WIN-2026-10-22.md` section 1 | landed | the claims the captions are evidence for |
| ffmpeg 9.0.2 (gyan build) on this PC | present, `ffmpeg -version` checked | the chain below was run, not guessed |

---

## 1. Capture: the region, the scale, and the one number that 1080p cannot have

The game draws 256x240 and GameMaker puts that into a 768x720 viewport at [8, 31] inside a 784x759 window. Both numbers
were measured, not assumed: `tests/test_capture_title.py` pins the window form and `tools/capture_title.py` finds the
rectangle by process image name, not by title. `tools/play_demo.py` already records the whole window and then crops to
the viewport with `tools/nes_composite_check.py`'s own search, so the recorded file is the game's pixels and not the
desktop's scaling of them.

The capture region, for a person setting this up by hand as well as for the recorder:

- Record the viewport only: 768x720, top left at (8, 31) of the client area. Not the window, not the desktop, no
  cursor, no taskbar.
- 60 fps, one recorded frame per game step. The game's step event is room speed 60, so the recorder's clock is the
  game's clock and a step in the script is a step in the file.
- Never let the operating system scale the window. A 125 percent display scale turns every pixel into 2.5 pixels and
  no later stage can undo it.

The scale chain, and the exact factor:

| Stage | Pixels | Factor from 256x240 |
| --- | --- | --- |
| the game's own frame | 256x240 | 1x |
| the captured viewport | 768x720 | 3x |
| the edit lattice (what every effect and cut is timed on) | 256x240 | back to 1x, exact 1/3 |
| the picture inside the delivered frame | 1024x960 | **4x** |
| the delivered frame | 1920x1080 | 4x picture, plus padding |

**The exact scale factor is 4x.** 1080 is not a multiple of 240: 240 times 4 is 960 and 240 times 4.5 is 1080. So a
1080p frame cannot hold a 256x240 picture at whole pixel multiples with no bars, and the honest choice is the largest
integer that fits, which is 4x, with the remainder filled by black: 448 pixels of pillarbox on each side (1024 + 448 +
448 = 1920) and 60 pixels of letterbox above and below (960 + 60 + 60 = 1080). Every 256x240 pixel becomes a 4x4 block
of identical colour. The picture occupies x 448 to 1471 and y 60 to 1019 of the delivered frame.

What is refused, and why: `scale=1920:1080:flags=neighbor` in one step is 7.5x across and 4.5x down, which makes some
source pixels 7 wide and their neighbours 8, and some 4 tall and their neighbours 5. That is the uneven pixel grid spec
13 forbids by name ("no fractional scaling", "no anti aliasing"), and it is visible at 1080p on a 65 inch screen. No
5x either: 5x is 1280x1200, and 1200 does not fit in 1080.

One row of video that is not the game: the two receipt overlays and the six captions are drawn in the letterbox and
pillarbox padding, outside the 256x240 area, so no caption ever covers a game pixel.

---

## 2. The ffmpeg chain, pasted and measured

### 2.1 The master

The delivered file is built from the take in one pass. The two scale steps are both integer, which is the whole point:
768 to 256 is an exact 1/3 lattice and 256 to 1024 is an exact 4x, so the upscale never invents an in between colour.

    ffmpeg -y -i output/demo/run_001.mp4 ^
      -vf "scale=256:240:flags=neighbor,scale=1024:960:flags=neighbor,pad=1920:1080:448:60,setsar=1" ^
      -r 60 -c:v libx264 -preset medium -crf 12 -pix_fmt yuv420p ^
      -c:a aac -b:a 192k -ar 48000 -movflags +faststart ^
      output/final/primordial_paradox_vertical_slice.mp4

Notes on each argument, so nobody "improves" one of them in the booth:

- `scale=256:240:flags=neighbor` first, not last. It puts the take back on the NES lattice before anything is done to
  it, so the 4x step is measured from whole game pixels and not from a 3x desktop stretch.
- `flags=neighbor` on both, never `bicubic` and never the default. The default is bicubic, which is exactly the blend a
  palette first project cannot have.
- `pad=1920:1080:448:60` and `setsar=1`. The pad is where the captions live; `setsar=1` stops a player from
  re stretching the file and turning 4x blocks into 4.5x ones.
- `-r 60` matches the source rate, which is 60.00 in the take, so no frame is duplicated and none is blended. Do not
  add an `fps` filter: that is the one filter that would soften the picture.
- `-crf 12`, not 18 or 23. The chain is exact but x264 is lossy; on a flat NES palette its noise shows up inside a
  block. Section 2.4 has the measured numbers.

### 2.2 The per shot cut

Every cut in this plan is on a stated second, so a shot is cut from the master with a re encode at the same settings or,
for a review pass only, a stream copy:

    ffmpeg -y -ss 00:00:29.03 -to 00:00:39.03 -i output/final/primordial_paradox_vertical_slice.mp4 ^
      -c:v libx264 -preset medium -crf 12 -pix_fmt yuv420p -c:a aac -b:a 192k output/final/cut_s3.mp4

`-ss` before `-i` seeks the input and is fast; the re encode keeps every cut on the same grid. A stream copy (`-c copy`)
is allowed only to look at a shot, because it can land half a second off the keyframe.

### 2.3 The thumbnail

    ffmpeg -y -ss 10.8 -i output/demo/run_001.mp4 ^
      -vf "scale=256:240:flags=neighbor,scale=768:720:flags=neighbor,pad=1280:720:256:0,setsar=1" ^
      -frames:v 1 output/final/thumbnail_1280x720.png

Same rule at a different size: 1280x720 cannot hold 256x240 at a whole multiple either (3x is 768x720, which fits the
height and leaves 256 pixels on each side), so the thumbnail is 3x plus 256 pixel pillarbox. Section 6 says which frame
and why.

### 2.4 What was actually run, on this PC, tonight

The chain above was executed on the real take, `output/demo/run_001.mp4` (73.500 s, 768x720, h264, 60 fps), not on a
synthetic clip. Measured with `ffprobe` on the result:

- output: 1920x1080, `yuv420p`, h264, `r_frame_rate` 60/1, duration 73.500000, 4.3 MB at `crf 12` (3.2 MB at `crf 16`)
- encode time on this PC: 19.4 s for 73.5 s of video at `crf 12`, preset medium
- a decoded frame of the result: 9,276 distinct colours, and 90.92 percent of its 4x4 blocks are a single colour. At
  `crf 16` the same measure is 88.27 percent, which is why the master uses 12.

The 9 percent that is not a single colour is compression noise, not a filter fault, and the reason is worth knowing:
the take is already h264, so the 1/3 downscale samples whatever the first encoder left inside a 3x3 block. **A cleaner
master is one line in `tools/play_demo.py`**: put this same filter chain in the capture encode, so the 1080p master is
cut from one encode of the raw window instead of two. That file is DEMO-KIT's (t_9ebd35dc) and this card does not edit
it; it is recorded here as a finding for that owner, with these numbers as the evidence.

---

## 3. The six shots at a glance

Times are the delivered frame's own clock. The six shots are exactly DEMO-SCRIPT section 3, unchanged, then a credit
card is appended (section 7).

| Shot | Shot range | Caption range | Music bed | Overlay |
| --- | --- | --- | --- | --- |
| S1 title | 0:00.00 to 0:16.00 | 0:01.00 to 0:14.20 | `title_theme`, `title_theme_v5.ogg` | none |
| S2 crawl | 0:16.00 to 0:29.00 | 0:16.60 to 0:27.00 | `title_theme`, ducked | none |
| S3 drive | 0:29.00 to 0:39.03 | 0:29.40 to 0:35.00 | `title_theme`, no engine loop yet | none |
| S4 quay and gate | 0:39.03 to 1:19.03 | 0:39.60 to 0:45.00 | `PP-03` Harbor, `pp_03_harbor.ogg` | none |
| S5 office and boarding | 1:19.03 to 1:53.03 | 1:19.60 to 1:23.30 | `PP-05` Small Ship on the fade | bake row 1 |
| S6 two fights, save, game over | 1:53.03 to 3:00.00 | 1:53.03 to 1:57.00 | `PP-04`, then `PP-05`, then the save chime | bake rows 2 to 4, network line |
| credit card | 3:00.00 to 3:04.00 | the card is the caption | silent | none |

Caption typing runs at 2 steps a character, the rate S3 of the demo script fixes. Measured fit for all six, at 60 steps
a second, so no caption is cut off mid word:

| Shot | Characters | Typing time | Window | Hold after the last character |
| --- | --- | --- | --- | --- |
| S1 | 78 | 2.60 s | 13.20 s | 10.60 s |
| S2 | 94 | 3.13 s | 10.40 s | 7.27 s |
| S3 | 93 | 3.10 s | 5.60 s | 2.50 s |
| S4 | 95 | 3.17 s | 5.40 s | 2.23 s |
| S5 | 87 | 2.90 s | 3.70 s | 0.80 s |
| S6 | 98 | 3.27 s | 3.97 s | 0.70 s |

The caption text, verbatim from DEMO-SCRIPT section 3, with the range this plan gives it. The wording is not reworded
here; only the in and out seconds are this file's decision.

| Shot | Range | Caption, verbatim |
| --- | --- | --- |
| S1 | 0:01.00 to 0:14.20 | `Cold boot to menu in 14 seconds. CONTINUE is dim because there is no save yet.` |
| S2 | 0:16.60 to 0:27.00 | `The crawl is 1,238 steps on the engine. A held confirm reads it faster and never skips a page.` |
| S3 | 0:29.40 to 0:35.00 | `One of the twelve drive shots: the sign counts down, and the cut lands on a bar of the waltz.` |
| S4 | 0:39.60 to 0:45.00 | `The gate cannot be failed. Three replies, three flags, and every one of them lifts the barrier.` |
| S5 | 1:19.60 to 1:23.30 | `The pass is one page and one flag. The clerk's line is a bake row, and here is the row.` |
| S6 | 1:53.03 to 1:57.00 | `FIGHT once ends the hound. Three TALK options reach MERCY 60 and SPARE. Then a save, and a defeat.` |

A caption is drawn in the bottom letterbox band (y 1020 to 1079), one line, 40 pixel monospace, white on black,
centred. Longer than one line at 40 pixels means the line is wrong, not that the font shrinks.

---

## 4. The input script, shot by shot

Vocabulary is the one `data/demo/run_001.json` already uses: `enter`, `confirm`, `up`, `down`, `right`, and a hold is
written `confirm hold` with the step it is released at. Steps are absolute on the 180.00 s clock at 60 a second, so the
recorder needs no arithmetic. The deltas below are what that file grows into; four of the six shots are short of the
build (section 9).

**S1, 0 to 960**

| Step | Key |
| --- | --- |
| 0 | none (the attract plays, no key until the flash has run) |
| 708 | `enter` (PRESS Z OR ENTER opens the menu) |
| 852 | `enter` (NEW GAME) |

**S2, 960 to 1,740**

| Step | Key |
| --- | --- |
| 1,320 | `confirm hold` to 1,620 (3x reveal through beats 3 and 4, no page skipped) |
| 1,620 | release (the last beat reads at 1x) |

**S3, 1,740 to 2,342**

| Step | Key |
| --- | --- |
| 2,100 | `confirm` (closes `drive_sign_55`) |

**S4, 2,342 to 4,742**

| Step | Key |
| --- | --- |
| 2,522 | `confirm hold` to 2,582, then `confirm` at 2,642 (page 1, fast read, advance) |
| 2,882 | `confirm hold` to 2,942, then `confirm` at 3,002 (page 3) |
| 3,242 | `confirm` (page 4 closed, the choice panel opens) |
| 3,254 | `down` (cursor moves from No pass. to Crew list.) |
| 3,422 | `confirm` (takes Crew list.) |
| 3,734 | `confirm` (`quay_gate_bluff` page 1) |
| 3,854 | `confirm` (page 2, the barrier lifts) |
| 4,100 to 4,660 | `up` and `right`, held in turns (walks the block to the office frontage) |
| 4,742 | `confirm` (the office door) |

**S5, 4,742 to 6,782**

| Step | Key |
| --- | --- |
| 4,862 | `confirm hold` to 4,922, then `confirm` at 4,982 (office page 1) |
| 5,252 | `confirm hold` to 5,312, then `confirm` at 5,372 (page 3) |
| 5,492 | `confirm` (page 4) |
| 5,612 | `confirm` (page 5) |
| 5,792 | `confirm` (page 6, `has_boarding_pass` set) |
| 5,800 to 6,140 | `right` and `down`, held in turns (the quay south, the gangway) |
| 6,422 | `confirm` (`ship_rail_note`) |
| 6,440 | `up`, three presses (the scene's three tile move) |

**S6, 6,782 to 10,800**

| Step | Key |
| --- | --- |
| 7,022 | `confirm` (FIGHT, the bar starts) |
| 7,052 | `confirm` (the bar at about 66, the blow lands) |
| 7,262 | `confirm` (`hound_win_kill`) |
| 7,802 | `confirm` (`battle_intro_sailors`) |
| 7,970 | `down` (cursor to TALK) |
| 7,982 | `confirm` (TALK opens) |
| 8,042 | `confirm` (option 1) |
| 8,102 | `confirm` (reply 1) |
| 8,312 | `confirm`, then `confirm` (option 2 and its reply) |
| 8,612 | `confirm`, then `confirm` (option 3 and its reply, MERCY reaches 60) |
| 8,882 | `confirm` (SPARE) |
| 9,092 | `confirm` (`navy_win_spare`) |
| 9,506 | `up` and `right` (the deck to the hatch and the cabin door) |
| 9,602 | `confirm` (the cabin door) |
| 9,752 | `confirm` (the ship's log) |
| 9,872 | `confirm` (the Saving panel, the chime) |
| 10,260 | the defeat input R27 lands (no key invented here) |
| 10,290 | `confirm` (`battle_lose`) |
| 10,530 | `confirm` (the game over screen, then CONTINUE on the title menu) |
| 10,620 | none (the load, the last frame) |

---

## 5. The receipts: two bake rows, printed as a caption, never drawn by the game

The reason the receipts exist is D5 in `knowledge/GAMEDEV-DECISIONS-2026-10-22.md`: the shipped build holds no key and
makes no call, so the evidence that a model was in the loop is the row, and the recording prints the row.

Where the values come from, exactly: `data/meta_bake.json`, the row whose `request_hash` matches the assembled request
for that line, fields `model` and `request_hash` (spec 19 section 2, fields fixed by D5). The bake file is R29
META-BAKE's deliverable and **does not exist on disk tonight** (checked: `ls data/meta_bake.json` is empty, the file is
absent). The two Meta shots are therefore not recordable yet, and that is a fact the booth needs in advance rather than
at 2 am.

How it is drawn, so it cannot become a hand typed caption:

1. A small tool empties the row into a text file, one line per overlay: `model: <id> request_hash: <64 hex>`. The tool
   reads `data/meta_bake.json`; it never accepts a value from a person.
2. `drawtext` reads that file with `textfile=`, so the string on screen is the file's string and nothing else:
   `fontfile='C\:/Windows/Fonts/consola.ttf':textfile=overlay_s5.txt:fontcolor=white:fontsize=30:x=(w-text_w)/2:y=1026`
3. The overlay is enabled only inside its own second range, with `enable='between(t,83.400,87.400)'`.
4. The overlay sits in the bottom letterbox band, y 1026, which is 6 pixels below the last row of the game picture. No
   pixel of the 256x240 area is touched, which is the same rule DEMO-SCRIPT section 4 puts on the edit.
5. A row that is missing stops the overlay: the tool exits non zero rather than printing a guess. A receipt that lies
   is worse than a missing shot.

| # | Shot and on screen line | Range | What the overlay prints |
| --- | --- | --- | --- |
| 1 | S5, Nye page 2, `You are the last one. Name, then. Slowly.` | 1:23.40 to 1:27.40 | `model` and `request_hash` of the `npc` Nye row at `southampton_dock`, turn 1 |
| 2 | S6, TALK reply 1 | 2:15.03 to 2:17.03 | `model`, then the `request_hash` of the `fight` deck watch row, turn 1 |
| 3 | S6, TALK reply 2 | 2:18.53 to 2:22.03 | `request_hash` alone, turn 2 (a different value) |
| 4 | S6, TALK reply 3 | 2:23.53 to 2:28.03 | `request_hash` alone, turn 3 (a third value) |
| 5 | S6, on the win text while the machine has no network | 2:34.40 to 2:38.40 | the sentence below, plus the row that backed the line above it |

The network line, verbatim, and it is a sentence rather than a receipt because it reports a state and not a value:

    network off since 00:00.00; this reply was read from data/meta_bake.json

Three values with three different hashes is the point of rows 2 to 4: it proves three calls at three scene states and
not one line reused. `created_at` is in the row and is not printed; DEMO-SCRIPT section 4 says why.

---

## 6. The music bed and the sound

The bed is assembled from the game's own cue files, in the repository, with their real durations measured by `ffprobe`
tonight. This is not a hope about the soundtrack: the files exist and are the ones `data/audio.json` names.

| Shot | Cue | File | Length | How it is used |
| --- | --- | --- | --- | --- |
| S1 | `title_theme` | `assets/audio/title_theme_v5/title_theme_v5.ogg` | 74.27 s | one pass covers S1 to S3 (39.03 s), no loop |
| S2 | `title_theme` ducked | same file | | the same pass, volume down 6 dB under the crawl, restored at 0:29.00 |
| S3 | `title_theme` | same file | | continues; the cut at 0:39.03 lands on the waltz's bar |
| S4 | `PP-03` Harbor | `assets/audio/pp_03_harbor/pp_03_harbor.ogg` | 225.88 s | one pass covers 40.00 s, no loop |
| S5 | `PP-05` Small Ship | `assets/audio/pp_05_small_ship/pp_05_small_ship.ogg` | 60.00 s | starts on the boarding fade at 1:42.53, one loop point at 2:42.53 |
| S6 | `PP-04` Navy Sailors | `assets/audio/pp_04_navy_sailors/pp_04_navy_sailors.ogg` | 43.64 s | restarts at each encounter, as the game does: 1:53.03 and 2:10.03 |
| S6 | `PP-05` | `pp_05_small_ship.ogg` | | back on the deck from 2:01.03 and in the cabin from 2:42.53 |
| S6 | `game_over` | `assets/audio/sfx/game_over.ogg` | 1.40 s | once at 2:51.00, then silence until the load |
| credit | none | | | silent card |

Sound effects, all present as files under `assets/audio/sfx/`: `menu_move.ogg`, `menu_select.ogg` (the two menu
presses in S1), `text_blip_a.ogg`, `text_blip_b.ogg`, `text_blip_c.ogg` (the dialogue blips in S2 to S6),
`footstep.ogg` (the yard walk and the deck), `door_hatch.ogg` (the office door and the cabin), `save_jingle.ogg` (the
save chime, 1.40 s), `game_over.ogg`, `encounter_swoosh.ogg` (the two encounter flashes), `hit_light.ogg` (the FIGHT
blow).

One gap, named rather than papered over: `car_engine_loop` is the cue the drive list gives S3 (`sfx car_engine_loop`,
DRIVE-SHOT-LIST section 2), and **no such file is in `assets/audio/sfx/` tonight**. The bed for S3 is therefore
`title_theme` plus the text blips, which is what DEMO-SCRIPT says S3 sounds like today; the engine loop joins the mix
only if the musician lane lands it, and no caption promises it.

How it is muxed: one AAC track, 192 kbps, 48 kHz, normalised to about minus 16 LUFS integrated with a true peak under
minus 1 dBTP, no fade out under the last caption. The existing take's audio is a stand-in rendered from the title theme
because this PC reports no loopback device (`tools/play_demo.py` labels it in the mp4 comment and in the verify file);
the edit does not need the loopback, because it builds the bed from the cue files. The mp4's comment keeps that
distinction so nobody reads the stand-in as live capture.

---

## 7. The credit card, and the new total

ARRIVAL-CONTENT section 1 requires the Open Database Licence line on anything built from the OpenStreetMap extract, and
DEMO-SCRIPT N2 hands the placement to this card. It is a black card with one line of text, appended after S6, so it
cannot be missed by a person who stops watching at the game over:

| Card | Range | Text, verbatim |
| --- | --- | --- |
| credit | 3:00.00 to 3:04.00 | `(c) OpenStreetMap contributors, Open Database Licence (ODbL) 1.0, https://www.openstreetmap.org/copyright` |

The total changes from DEMO-SCRIPT's 180.00 s to **184.00 s**, which is still inside the 170 to 190 band. Old to new,
stated once: S1 to S6 unchanged at 180.00 s; the credit card adds 4.00 s; delivered length 184.00 s. If the band ever
tightens to 180, the card shortens to 2.00 s and the last game frame holds under it.

---

## 8. The one paragraph under the video

89 words, counted with a script rather than by eye. It is written for the submission build and it names only models the
pipeline has an id for in `tools/meta_client.py`.

> Primordial Paradox is a three minute NES slice: Kronos and Zeus reincarnated on the M3, a night drive into
> Southampton, and a fight you win by talking. The game draws at 256 by 240; the video is that frame at an exact 4x,
> nearest neighbour, no blending. The build makes no network call and holds no key: TALK replies are baked
> ahead of time with muse-spark-1.3, concept art and silhouettes come from muse-image-1.0 and sam-3.1, and the
> recording prints each reply's model and request hash from the bake file.

Two conditions on that paragraph, and both are checkable in one minute on the day the video is cut:

1. The `muse-spark-1.3` clause is backed by the receipts in section 5, which read `data/meta_bake.json`. If the bake
   row is absent the shot is not recorded, so the clause cannot go out unbacked by accident.
2. The `muse-image-1.0` and `sam-3.1` clause is backed by the art provenance log, not by the video. Tonight
   `data/ai_cache/` holds 6 entries, all `backend: mock` and `network: false`, so no real Meta call has produced a
   shipped pixel yet. If the provenance log does not name those two models on the day, delete the clause "concept art
   and silhouettes come from muse-image-1.0 and sam-3.1" and the paragraph is still 79 words and still true. This is
   the one place in this plan where a claim is conditional, and it is marked instead of assumed.

---

## 9. The thumbnail the slice can actually produce today

Today's build reaches the title, the menu, the crawl and one ship room with eight steps of walking and one NPC
dialogue: DEMO-KIT's manifest covers beats 1 to 6, marks 7 and 26 partial and 24 unreachable. A thumbnail has to come
from those, so the choice is a title frame, and the best one is the title attract with the menu open, because in one
look it says "this is a game, this is a menu, it runs".

| What | Value |
| --- | --- |
| Source | `output/demo/run_001.mp4`, the real recording from DEMO-KIT, 73.500 s, 768x720 |
| Frame | 10.80 s, which is the title attract with the logo, the moon, the storm cloud, the car and the menu open on NEW GAME, CONTINUE, SETTINGS, QUIT |
| Command | section 2.3, run tonight |
| Output | 1280x720, PNG, 48 KB, produced tonight by that command; on export night it lands at `output/final/thumbnail_1280x720.png` |
| Why not a later shot | the quay, the drive and the office are not in the build, so a thumbnail of them would be a mock up, and a mock up thumbnail is a claim the video cannot meet |
| Why not the crawl | a frame of scrolling text reads as a wall of words at thumbnail size; the menu reads as a game |

The frame was checked rather than assumed: extracted at 10.80 s, the menu labels read NEW GAME, CONTINUE, SETTINGS,
QUIT, the picture is not a fade and not black, and the frame is the game's own 3x pixels.

---

## 10. What cannot be recorded yet, and who owns it

Stated plainly, because a plan that assumes these landed is a plan that fails on the night:

| Missing today | Blocks | Owner |
| --- | --- | --- |
| `data/meta_bake.json` | the two receipt overlays and therefore S5's bake row and S6's three rows | R29 META-BAKE (t_f943951a) |
| the quay map and the gate scene `quay_gate_checkpoint` | all of S4, and S5's door trigger | ARRIVAL-MAP-2 (t_db2995d7), R22 DIALOGUE-V2 (t_5b27880e) |
| the drive block in `data/scenes/all.json` and `drive_sign_55` | S3 | R21 |
| the forced defeat input | S6.4 | R27 GAME-OVER (t_24eab5ff) |
| `sfx car_engine_loop` | the S3 engine layer only, not the shot | musician lane, no card yet |
| one row per route step in `data/slice.json` | the route re-read check, not the recording | R24 SLICE-ROUTE (t_e063f248) |

Q: for gamedev, two items, neither of which changes a second of the 184.00:

1. The engine loop for S3: is `car_engine_loop` a real asset the musician lane owes, or does the drive list's cue
   column change to the blips only? The plan takes blips only until told otherwise.
2. The credit card: 4.00 s after the last game frame, or a 2.00 s card, if the delivered length has to stay at or
   under 180.00 s for a platform limit this plan does not know about.

---

## 11. The checks, and how each is met

| The card's check | How this file meets it |
| --- | --- |
| every shot in the demo script appears with its input, caption, second range and music | S1 to S6 each carry a row in section 3 (range, caption range, bed) and a table in section 4 (steps and keys), with the caption text verbatim from DEMO-SCRIPT and its fit measured in section 3 |
| the ffmpeg command is pasted and its filter chain is valid for a 256x240 source, with the exact scale factor stated | section 2.1 paste, section 2.4 measured on the real take: 1920x1080, 60/1, 73.500 s out of 73.500 s in; the factor is stated as 4x, with the reason 1080/240 is not an integer and the pad geometry given in pixels |
| the description is 90 words or fewer and names the Meta models actually used | 89 words, counted by script; names `muse-spark-1.3`, `muse-image-1.0`, `sam-3.1`, the three ids `tools/meta_client.py` routes chat, image and segment to; and the one clause the build cannot back yet is marked conditional with the exact words to delete |
| no dash characters | the file was scanned for U+2013, U+2014 and U+2015 after writing |
| no claim the build cannot back | every stated running thing was run tonight (the chain, the thumbnail, the frame extraction); every unlanded thing is in section 10 with its owner; the art models clause carries its own condition |

Written by assistant, 2026-10-22. Every command in section 2 was executed on this PC against the real take; the numbers
in section 2.4 and the frame in section 9 are their output.
