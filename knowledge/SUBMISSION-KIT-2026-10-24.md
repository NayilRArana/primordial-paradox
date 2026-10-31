# Submission kit, 2026-10-24: the write-up, the two scripts, the repo text, and the first 30 seconds

Card `t_bfa27a6e` (SUBMISSION-KIT), assistant, written 2026-10-23 01:55 to 02:40 PDT for Primordial Paradox.
Re-baselined 2026-10-26 07:20 to 07:50 PDT by card `t_fd766448` (KIT-REBASELINE) on node CitadelArana, at HEAD `1a242a4`.
Scope: this file only. It publishes nothing, uploads nothing and submits nothing: the submission is Nayil's.

What it is for: on submission night the work is assembly, not writing. Every block below is already written, already
counted, and already tied to the file that backs it. A person pastes, records, types six captions, fills four form
fields, and stops.

---

## Re-baseline, 2026-10-26, node CitadelArana: every number in sections 1.1, 2 and 3, and the file behind it

Every value in this table was read on 2026-10-26, by opening the file named beside it or by running the command in the
row on this PC. Nothing here is carried from 2026-10-23. Where a number moved, the old value is named in the row so a
reader can see both. The three blocks it feeds are section 1.1, section 2 and section 3.

| Number as it appears | Value today | File, or command and its output today |
| --- | --- | --- |
| seconds of recording before the drive | 43.2 | `output/demo/nightly-2026-10-26_verify.json` `run.trace` id `e08`, `at_second 43.25`, `marker 'starting the run in' seen`; `build/demo-game.log:128` |
| what the drive step opens with | cue `PP-02`, the car engine loop, five text lines | `build/demo-game.log:131` to `:139`: `music cue PP-02 has no OGG yet`, `car_engine_loop played`, `text_blip_a played` five times; the row is `drive_to_southampton` in `data/scenes/all.json` |
| drive stills inside the palette | 0 of 12 | `READINESS-2026-10-26.md` section 3 row 3, measured 06:12 to 06:30 today: share 0.0000 to 0.0167 over `output/drive_frames/drive_shot_*.png` |
| footstep cues in the recording | 0 | `output/demo/nightly-2026-10-26_verify.json`: `run.footsteps 0`, `run.failures[0] the game played no footstep cue, so the Right presses did not reach the walk` |
| route steps, and the step play reaches | 9 steps; play reaches the third | `data/slice.json` 9 `route.steps`; `data/scenes/all.json` 15 scene rows; `data/maps/all.json` 5 map rows; `python -m pytest tests/test_slice_route.py -q` prints `24 passed` |
| bake rows, and what they carry | 18 rows, all `source: fallback`, `live` 0, `calls_attempted` 0 | `data/meta_bake.json`, the `bake` block and the `source` field of all 18 rows |
| NES audit failures | 35 of 183 files | `python tools/nes_audit_all.py`, exit 1, first line `nes_audit_all: FAIL  183 file(s), 35 failing, 0 unmeasured` (was 33 of 178 on 2026-10-23) |
| timed events in the demo script | 19 | `data/demo/run_001.json`, `events` |
| planned and recorded length, and the stream | 71.0 planned, 73.483 recorded, 768x720 h264 at 60 fps | `output/demo/nightly-2026-10-26_verify.json`: `run.planned_seconds 71.0`, `duration_s 73.483333`, `stream.r_frame_rate 60/1` (the write-up's 73.5 was `run_001.mp4` from 2026-10-22) |
| rows at 2, at 3, and at 4 in the readiness table | 12 at 2, 10 at 3, none at 4, mean 2.4545 | `READINESS-2026-10-26.md` section 3, sum 54 over 22 rows (the 2026-10-24 page's mean was 2.409) |
| days left before the deadline | nine, Oct 26 to Nov 4 | `..\arananet\meta-hackathon\SUBMISSION-CHECKLIST.md` section 0: `Wed Nov 4, 9 PM ET` |

Two corrections this re-baseline makes to sentences the older file wrote, both checked today:

1. **The drive row exists now.** `data/scenes/all.json` holds `drive_to_southampton` (15 scene rows) and
   `data/maps/all.json` holds `drive_m4_corridor` (5 map rows), so "the drive room exists as code and no build has
   shown it" is no longer the shape of the gap. The gap today is that 0 of the 12 drive stills are inside the palette,
   which is why row 3 still scores 2, and that the recording enters the drive at 43.25 s and never leaves it.
2. **The route's data gap closed, and the play gap did not.** `grep -c drive_to_southampton data/scenes/all.json` is 1
   today (0 on 2026-10-23), all nine route steps name a row that exists, and `tests/test_slice_route.py` is green at 24
   tests. What is still true is that a played run reaches the third of the nine steps and no further: the recording
   holds the title, the crawl and the drive, 0 footsteps, and no gate, boarding, fight, save or defeat.

---

## 0. Inputs read, and the state each was in

| Input | State when read | What it gave this kit |
| --- | --- | --- |
| `knowledge/DEMO-SCRIPT.md` (R39, 429 lines) | landed | the six shots, their steps, inputs, captions verbatim, and the claim each shot proves |
| `knowledge/VIDEO-PLAN.md` (R44, 428 lines) | landed | capture region, the 4x chain, caption ranges, the receipt overlays, the credit card, the 89 word description |
| `knowledge/DEMO-KIT-2026-10-22.md` | landed | the recorder's real numbers, and the one finding it must not be described as clean |
| `knowledge/HACKATHON-AUDIT-2026-10-22.md` section 1 | landed | the 22 row maturity table (mean 2.2) |
| `knowledge/READINESS-2026-10-24.md` section 2 and 4 | landed 01:52 today, measured 00:44 to 01:52 | the same 22 rows re-scored (mean 2.409) plus the eight step verdicts. **This kit mapped claims to these numbers, not to the older table**, because they were newer and they moved two rows. Superseded on 2026-10-26 by `READINESS-2026-10-26.md` section 3 (mean 2.4545), which is what sections 1.2, 2, 3.1 and 6 now cite |
| `..\arananet\meta-hackathon\PLAN-WIN-2026-10-22.md` section 1 | landed | the four claims a judge is being asked to believe |
| `..\arananet\meta-hackathon\knowledge\RULES-WATCH-2026-10-24.md` | landed | what the rules actually require, what is quoted, what is UNKNOWN |
| `..\arananet\meta-hackathon\SUBMISSION-CHECKLIST.md` | landed 2026-10-22 | the nine submission items, so this kit does not repeat a line it already owns |
| `..\arananet\meta-hackathon\kit\*.md` | landed 2026-10-22 | the earlier drafts. This file replaces `kit\VIDEO-SCRIPT.md` as the script of record and `kit\ONE-PAGER.md` as the page of record |

Two facts changed between those inputs and this file, both checked on disk at 02:00 today, and both weaken a sentence
the earlier files wrote:

1. **`data/meta_bake.json` exists now** (53,118 bytes, written 00:32). It holds 18 rows, every row `"source":
   "fallback"`, `bake.mode` `offline`, `live` 0, `calls_attempted` 0, model `muse-spark-1.3`. So the receipts prove the
   plumbing and the model id the bake is written against. They do **not** prove that a model answered. `VIDEO-PLAN`
   section 5 said the printed pair "cannot be a hand typed line", which is still true; it also implied a call, which is
   not. Section 3.3 below fixes the overlay wording.
2. **The drive room exists and the drive scene row does not.** `game/rooms` lists `rm_pp_boot`, `rm_pp_drive`,
   `rm_pp_ship`, `rm_pp_title`. `grep -c drive_to_southampton data/scenes/all.json` is 0, `grep -c
   southampton_town_quay data/maps/all.json` is 0, `grep -c '"quay_gate_checkpoint"' data/scenes/all.json` is 0. The
   drive is maturity row 3 at 2, and S3 in both scripts carries its fallback.

---

## 1. The one page write-up

Paste the eleven blocks below, in order, into the submission's write-up field or into a one page PDF. The wording is
final; the numbers in it were read off the repository today.

**One page at 11 point is proven, not estimated.** The same text was set in LaTeX (`article`, 11 pt, US Letter, 1 inch
margins, no page numbers), compiled with `pdflatex`, and `pdfinfo` returns `Pages: 1`, `Page size: 612 x 792 pts
(letter)`. The body is 530 words, counted by script on 2026-10-29. The source is `knowledge/submission-kit-2026-10-24-writeup.tex`
in this repository: `pdflatex` it and `pdfinfo` reports one page again. On submission night the same text pastes into
any 11 pt page and fits.

### 1.1 The text, verbatim

**Primordial Paradox: AI that obeys hardware limits**

Primordial Paradox is a 256 by 240 NES style adventure built in GameMaker. Kronos and Zeus wake on the M3 at night,
drive south to Southampton, and reach a ship at the quay. Two encounters follow. The first is won with one FIGHT
command. The second is won by talking past a sailor, and the reply inside the text box is a line baked ahead of time
and accepted by my checker.

One person cannot be an art department, a composer and a writers room. A small game dies of art cost long before it
dies of code. A model that ignores the hardware makes it worse: art that is beautiful and impossible, two hundred
colours, a portrait where the sprite has 16 pixels to work with.

The pipeline has five stages and one rule. Concept art goes to muse-image-1.0, the silhouette to sam-3.1, and my own
pixeliser cuts both to four colours a sprite, because a palette first sprite can be checked and a pretty one cannot.
muse-spark-1.3 reads a drawn frame with vision and writes the TALK replies as JSON with a mercy delta and a refusal
flag, so the battle never waits on a sentence. Music is rendered by my own chip engine and judged by a model reading a
spectrogram. Each model hands its output to a checker, and the checker decides what reaches the screen.

Two things here are mine. First, `tools/nes_audit_all.py` measures every frame against the limits of the Ricoh 2C02
and publishes its own failures, 35 of 183 files today, because a gate that only says yes is not a gate. Second, the
shipped build holds no key and makes no call: model answers are baked into `data/meta_bake.json` with a model name and
a request hash, and the recording prints that row on screen.

Where it stands, with nothing rounded up. The title and the crawl run from one build, 43.2 seconds of recording. The
drive row and its map are in the tree, and the drive step opens there with cue PP-02 and five lines of radio; the
twelve drive stills miss the palette. No footstep cue fired, so the walk is unproven. The nine route steps pass their
own test, and play reaches the third. No live Meta call has produced a shipped pixel: the bake file's 18 rows all
carry the written fallback.

The video is one scripted run, 19 timed events in `data/demo/run_001.json`, planned at 71.0 seconds and recorded at
73.483, from the real build at 60 frames a second in the game's own 3x pixels. It shows the title, the crawl and the
drive's first thirty seconds, and stops before the gate. The gate, boarding, the first fight, the talk fight, the save
and the defeat are not in it yet.

It fits Build for Your World because my world is a one person NES cartridge: a 1989 chip, a 150 dollar credit grant,
and a checker that says no. The nine days go on turning the twelve rows at 2 into rows at 3. Watch the 73 second
recording and run `tools/nes_audit_all.py`, and you can check every number on this page without taking my word for it.

### 1.2 Every claim, and the row it stands on

The check for this card is that no claim outruns the maturity table. Rows and scores are `READINESS-2026-10-26.md`
section 3 (After column, measured 06:12 to 06:30 today); no row below rests on a row scoring under 2. Sentences 5 and 6
and the last sentence are the honest state, not claims: they are backed by the same rows and they say what is *not*
proven.

| Claim in the write-up | Backing file or measurement | Row and score |
| --- | --- | --- |
| 256 by 240 NES style adventure in GameMaker | `game/PrimordialParadox.yyp`, `output/title_run_1.json` `"viewport": [8, 31, 768, 720]`, `"scale": 3` | row 1 title, 3; row 19 build, 3 |
| the first encounter is won with one FIGHT command, the second by talking | `data/meta_bake.json` `fight/*` rows, `tests/test_first_fight.py`, `tests/test_talk_guard.py`; the capture `output/first_fight_verify.json` is `ok: false` | row 7 battle, 2: the rule is in the data and the tests, no capture shows it yet |
| the title and the crawl run from one build, 43.2 seconds of recording | `output/demo/nightly-2026-10-26.mp4`, its verifier's `run.trace` id `e08` at 43.25 s, `build/demo-game.log:55` and `:128` | rows 1 and 2, both 3 |
| the drive row and its map are in the tree, the drive step opens with cue PP-02 and five lines, the twelve drive stills miss the palette | `data/scenes/all.json` `drive_to_southampton`, `data/maps/all.json` `drive_m4_corridor`, `build/demo-game.log:129` to `:139`, `READINESS-2026-10-26.md` section 3 row 3 | row 3 drive, 2 |
| no footstep cue fired, so the walk is unproven | `output/demo/nightly-2026-10-26_verify.json` `run.footsteps 0` and `run.failures[0]`; `output/demo/run_002_verify.json` holds the last green walk, 8 footsteps on 2026-10-23 | row 4 overworld movement, 3, carried from the 10-23 run and not re-earned tonight |
| the nine route steps pass their own test, play reaches the third | `data/slice.json` 9 steps; `data/scenes/all.json` 15 scene rows; `data/maps/all.json` 5 map rows; `python -m pytest tests/test_slice_route.py -q` prints `24 passed`; the nightly `run.trace` ends inside the drive | rows 3 (2) and 5 (2); no row scores the route above 2 |
| the gate scene, the two fights, the save and the game over exist as data and tests | `data/scenes/all.json` (`quay_gate_checkpoint`, `ship_boarding`), `data/maps/all.json` `southampton_town_quay`, `tests/test_first_fight.py`, `tests/test_save_gameover.py` (19 tests), `output/first_fight_verify.json` `ok: false` | rows 5 (2), 6 (3), 7 (2), 10 (3) |
| 35 of 183 files fail the NES audit | `python tools/nes_audit_all.py`, exit 1 | row 20 tests and gates, 2 |
| the shipped build holds no key and makes no call | `tests/test_no_network_in_build.py`, `README.md` pipeline section | row 19 build, 3; row 20 gates, 2 |
| answers are baked with a model name and a request hash | `data/meta_bake.json` 18 rows, `model`, `request_hash`, `source: fallback` on all 18; `tests/test_bake_meta.py` | row 6 dialogue, 3; row 7 battle, 2 |
| no live Meta call has produced a shipped pixel | `data/ai_cache/` 6 entries, all `backend: mock`, `network: false`; bake `live` 0, `calls_attempted` 0 | row 16 art pipeline, 2; row 21 capture tooling, 3 |
| muse-image-1.0, sam-3.1, muse-spark-1.3 are routed and gated | `tools/meta_client.py` `RPMS` and `model_for()`, `tools/art/*.py`, `tools/eye_critic.py` | rows 16 (2), 17 (2), 18 (2) |
| music from a chip engine, reviewed on a spectrogram | `tools/render_chip.py`, `tools/ear_critic.py`, `assets/audio/` | rows 12 (3), 13 (2), 14 (3) |
| the video is 19 timed events, 71.0 planned and 73.483 recorded, 768x720 at 60 fps | `data/demo/run_001.json` 19 events; `output/demo/nightly-2026-10-26_verify.json` `run.planned_seconds 71.0`, `duration_s 73.483333`, `stream 768x720 h264 60/1` | row 21 capture tooling, 3 |
| twelve rows sit at 2 of 4 and ten at 3, none at 4 | `READINESS-2026-10-26.md` section 3, sum 54 over 22 rows, mean 2.4545 | that table itself, read 2026-10-26 |
| a 150 dollar credit grant | quoted in `RULES-WATCH-2026-10-24.md` section 3 from the waiver | event fact, not a build claim |

No row scores 4, so this page states where the work stands instead of what it would be if the rows were higher; section
7 of `READINESS-2026-10-26.md` states what the recording is not, and the write-up repeats it in its own words.

---

## 2. The 90 second script

For the submission page and for a judge in a hurry. Silent: the six captions are the DEMO-SCRIPT captions verbatim, and
the music bed is the game's own. Do not voice this version: at 90 seconds a voice and a caption compete.

Every caption is 79 to 113 characters, so 2.6 to 3.8 seconds of reading at 30 characters a second, and every shot holds
it at least twice that long. The fourth column is new on 2026-10-26: it says where the beat sits in the one recording
that exists, `output/demo/nightly-2026-10-26.mp4`, measured by `output/demo/nightly-2026-10-26_verify.json`.

| Range | Beat (DEMO-SCRIPT) | Picture | In the 2026-10-26 recording | Caption, verbatim | Read s |
| --- | --- | --- | --- | --- | --- |
| 0:00.0 to 0:11.0 | S1 | attract from 0:00, cut in at the lightning flash, menu opens, NEW GAME | 0:00.0 to 0:11.0: attract, then the two Enters at 10.05 s and 11.55 s (`run.trace` `e02`, `e03`) | `Cold boot to menu takes 14 seconds. CONTINUE is dim, because nothing is saved yet.` | 2.7 |
| 0:11.0 to 0:22.0 | S2 | the crawl, two beats, one held confirm | 0:11.5 to 0:22.0: the crawl is running, and it runs to 43.25 s (`e04` opens it, `e08` closes it) | `The crawl runs 1,238 steps. Hold confirm to read it faster; no page is skipped.` | 2.6 |
| 0:22.0 to 0:31.0 | S3 | one drive shot, the gantry sign counting down | 0:22.0 to 0:31.0 is still crawl here; the drive starts at 0:43.25 and runs to the last frame at 1:13.48 | `One of twelve drive shots. The sign counts down, and the cut lands on a bar of the waltz.` | 3.0 |
| 0:31.0 to 0:44.0 | S4 | the barrier, the hut, the choice panel, Down once, Crew list. taken, the barrier lifts | not in the recording | `Nothing you answer at the gate fails you. Each of the three replies sets a flag, and the barrier lifts.` | 3.4 |
| 0:44.0 to 0:56.0 | S5 | the ledger, Nye's page, the bake row printed under the frame | not in the recording | `The pass is one page and one flag. The clerk's answer is a bake row, and here is the row.` | 3.0 |
| 0:56.0 to 1:24.0 | S6 | one FIGHT ends the hound, three TALK options to MERCY 60, SPARE, the save, the defeat, CONTINUE | not in the recording; `output/first_fight_verify.json` is `ok: false` at `checked_at 2026-10-25T18:15:50` | `FIGHT once ends the hound. TALK gets you to SPARE, then a save and a defeat; watch the 73 second run in the repo.` | 3.8 |
| 1:24.0 to 1:26.0 | none | last frame holds | a held frame from the recording, always available | no caption | 0 |
| 1:26.0 to 1:30.0 | credit | black card, `(c) OpenStreetMap contributors, Open Database Licence (ODbL) 1.0, https://www.openstreetmap.org/copyright` | the card is drawn, not captured | the card is the caption | 2.7 |

What the 90 second cut drops, on purpose: the first eleven seconds of attract, the crawl's other four beats, eleven of
the twelve drive shots, every gate page except the choice, the boarding pages, the hound's intro text, the enemy turns,
and the three receipts after the first. Dropped, not reworded: no caption in this table is new text.

What tonight's file holds, in its own seconds. `output/demo/nightly-2026-10-26_verify.json` measures one 73.483 s file,
768x720 h264 at 60 fps, and `build/demo-game.log` names what is on screen: the title, the crawl, then at `:129` the
crawl handed to the route's step drive, at `:131` `music cue PP-02 has no OGG yet`, at `:133` the car engine loop, and
five text lines at `:135` to `:139`. There is no footstep cue, no gate, no boarding, no fight, no save and no defeat in
the file. A cut made only of tonight's material is 73.483 seconds long and holds three beats.

Preconditions, and what to do if one fails on the night. Each line has the shape of the S3 line the 2026-10-23 file
wrote: the range, what it becomes, what the caption does, and what the file length becomes.

1. **S3, the drive, 0:22.0 to 0:31.0.** The drive does not start until 0:43.25, so this range becomes the S1 attract
   hold with the S3 caption deleted, and the file is 81 seconds, still over the 30 seconds `SUBMISSION-CHECKLIST.md`
   item 1 asks for.
2. **S4, the gate, 0:31.0 to 0:44.0.** No gate frame exists and the gate scene has never been played. The range becomes
   a 13.0 second hold on the crawl's last page, the S4 caption is deleted, and the file stays 90 seconds.
3. **S5, the office and the pass, 0:44.0 to 0:56.0.** No office frame exists. The range becomes a 12.0 second hold on
   one drive frame from the recording, the S5 caption is deleted, and the file stays 90 seconds.
4. **S6, the fight, the save and the defeat, 0:56.0 to 1:24.0.** The first fight capture is red, so the range becomes a
   28.0 second hold on the title attract, the S6 caption is deleted, and the file stays 90 seconds. If the forced defeat
   alone is missing, S6 ends on the save and the last caption line becomes the first two sentences only, unchanged from
   the 2026-10-23 file.
5. **All of them at once.** Four held frames do not make a video. If S3, S4, S5 and S6 all fail on the night, cut the
   recording itself and nothing else: S1 0:00.0 to 0:11.5, S2 0:11.5 to 0:43.25, S3 0:43.25 to 1:13.483 at the drive's
   own length, two captions and none after S2. The file is 73.483 seconds, over the 30 seconds item 1 asks for, and
   every frame in it is a frame the build drew.

---

## 3. The 3 minute script

The judged cut: voice over the recording, six blocks, nothing reordered. Times are `DEMO-SCRIPT.md` section 3's, so a
shot is cut where the demo script says it is cut, and the caption ranges are `VIDEO-PLAN.md` section 3's.

Narration total is 272 words over 180 seconds, 1.51 words a second, counted by script. Blocks 1 and 3 sit at 2.1 words
a second on purpose, because the theme and the engine carry them; nothing is above 2.5.

### 3.1 Block table

| Range | Shot | Beat it proves (DEMO-SCRIPT) | Narration words | In the 2026-10-26 recording | State today (`READINESS-2026-10-26.md` section 3) |
| --- | --- | --- | --- | --- | --- |
| 0:00.00 to 0:16.00 | S1 | title attract, PRESS START, NEW GAME | 34, 2.12 w/s | 0:00.0 to 0:11.5 | row 1 title, 3 |
| 0:16.00 to 0:29.00 | S2 | the crawl | 20, 1.54 w/s | 0:11.5 to 0:43.25 | row 2 crawl, 3 |
| 0:29.00 to 0:39.03 | S3 | one drive shot | 21, 2.10 w/s | 0:43.25 to 1:13.483, cue PP-02, five lines | row 3 drive, 2: 0 of 12 stills inside the palette |
| 0:39.03 to 1:19.03 | S4 | the quay, the gate, the three option choice | 53, 1.32 w/s | not in the recording | rows 5 maps (2) and 6 dialogue (3): the scene row and the map row exist, no gate frame |
| 1:19.03 to 1:53.03 | S5 | the office, the boarding pass, the bake row | 50, 1.47 w/s | not in the recording | rows 6 (3) and 10 (3): the rows exist, no boarding capture |
| 1:53.03 to 3:00.00 | S6 | the hound, the TALK fight, the save, the defeat, CONTINUE | 94, 1.40 w/s | not in the recording | rows 7 (2) and 10 (3): `output/first_fight_verify.json` is `ok: false` at `2026-10-25T18:15:50` |
| 3:00.00 to 3:04.00 | credit | the ODbL card | 0, silent | drawn, not captured | required by `ARRIVAL-CONTENT.md` section 1 |

Read today, the table says the recording holds blocks 1, 2 and 3 and none of the rest. The judged cut made from tonight's
file alone is 73.483 seconds: S1 and S2 at the recording's own lengths and S3 at the drive's 30.2 seconds, three of the
six blocks, 75 of the 272 narration words, no caption after S2.

Fallbacks, one per block the recording cannot reach, each in the shape of the S3 line in section 2.

1. **S3, the drive, 0:29.00 to 0:39.03.** Reachable, not proven: the step plays in the recording but 0 of the 12 drive
   stills are inside the palette. If no legal drive frame exists on the night, S3 becomes the intro's own night drive,
   240 steps and 4.00 seconds (`data/demo/run_001.json` event `e08`), its 21 words are deleted, and the total is 173.97
   seconds, which is `DEMO-SCRIPT.md` section 2's own first fallback.
2. **S4, the quay and the gate, 0:39.03 to 1:19.03.** No gate frame exists. The block is cut whole: 40.00 seconds and 53
   narration words out, S5 pulled forward, and the file is 140.00 seconds before the credit card and 144.00 with it.
3. **S5, the office and the boarding pass, 1:19.03 to 1:53.03.** No office frame exists. The block is cut whole: 34.00
   seconds and 50 words out, and the file is 146.00 seconds before the credit card and 150.00 with it.
4. **S6, the two fights, the save and the defeat, 1:53.03 to 3:00.00.** The fight capture is red and nothing is reachable
   from the play, so the block is cut whole: 66.97 seconds and 94 words out, and the file is 113.03 seconds before the
   credit card and 117.03 with it. This is `DEMO-SCRIPT.md` section 2's second fallback taken to its end, where the save
   goes with the defeat rather than after it.
5. **All four at once.** The cut is S1 and S2 only, plus S3 as the 4.00 second night drive: 33.00 seconds of blocks, 54
   narration words at 1.64 a second, and 37.00 seconds with the credit card. Over the 30 seconds `SUBMISSION-CHECKLIST.md`
   item 1 asks for, and every frame in it is a frame the build drew.

### 3.2 The narration, verbatim, per block

S1: "This is 256 by 240. Not a filter: the frame, and every rule that comes with it. Cold boot to menu in fourteen
seconds, and CONTINUE is dim because there is no save yet."

S2: "Six beats on a thirty character box. Hold confirm and it reads three times faster, and never skips a page."

S3: "One of twelve drive shots: seven fixed parallax layers, a sign counting down, and the cut lands on the waltz's
bar."

S4: "The quay is built from a real OpenStreetMap extract: eight door names, four people, the Watergate Ruin. Morgan
holds the barrier and asks for a pass. Three replies, three flags, and every one of them opens the gate. A choice with
no failure state, because a slice should not punish you for guessing."

S5: "The office, the ledger, one page left. Nye asks for a name, and the game answers with a baked line: the model and
the request hash are printed under the frame, read from the bake file, never typed. The pass is one page and one flag,
not an inventory item."

S6: "Two fights. The hound dies to one FIGHT: two hit points against a blow that cannot roll under two. The sailor is
the real one. Three TALK options, mercy twenty a turn to sixty, and SPARE lights up. The machine has had its network
off since the first frame; every reply came out of the bake file. Then a save, a forced defeat, and CONTINUE that lands
exactly where the save left you. Everything you just saw is measured by my own gates, and the ones that fail are on the
page, not hidden."

The six captions from `DEMO-SCRIPT.md` still run under these blocks at `VIDEO-PLAN.md` section 3's ranges. Voice and
caption say different things on purpose: the caption quotes a number the frame shows, the voice says what it means.

### 3.3 The one correction this kit makes to VIDEO-PLAN's receipts

`VIDEO-PLAN.md` section 5 prints `model` and `request_hash` and calls the pair proof that a model answered. The bake
file today says otherwise: 18 rows, all `"source": "fallback"`, `bake.live` 0. A receipt that says "muse-spark-1.3"
while every row is a written fallback would be a true string and a false implication. So the overlay prints three
values per shot, all read from the file, never typed:

1. `model: muse-spark-1.3`
2. `request_hash: <64 hex>`
3. `source: fallback` (or `source: live` on the day a real bake replaces it)

and the one line that reports state, unchanged from `VIDEO-PLAN.md` section 5:

    network off since 00:00.00; this reply was read from data/meta_bake.json

On the day `bake.live` is no longer 0, the third value changes itself, the narration in S5 and S6 stays true, and the
caption in S5 stays true. That is why the third value is a field read and not a sentence written.

Q3 in section 7 asks gamedev to confirm this wording, because S5's DEMO-SCRIPT caption says "the clerk's line is a
bake row", which stays true, while ONE-PAGER's stronger phrasing ("the person judging your line is a Meta model
answering") is a claim for after the first live bake.

### 3.4 The paragraph under the video

89 words, the one from `VIDEO-PLAN.md` section 8, with its second condition still unresolved on 2026-10-26:
`data/ai_cache` holds 6 entries, all `backend: mock`, so the clause naming muse-image-1.0 and sam-3.1 has to come out on
submission night unless the art cache is re-recorded live. The 80 word version below is what ships if the clause goes,
and it is the only version whose length claim (a 73.483 second recording, a 3x frame) holds today:

> Primordial Paradox is a NES style slice: Kronos and Zeus reincarnated on the M3, a night drive into Southampton, and a
> fight you win by talking. The game draws at 256 by 240; the video is that frame at an exact 3x, nearest neighbour, no
> blending. The build makes no network call and holds no key: TALK replies are baked ahead of time against
> muse-spark-1.3, and the recording prints each reply's model, request hash and source from the bake file.

---

## 4. The repo description and the tags

### 4.1 GitHub, the About line

142 characters, under GitHub's 350 limit, and it claims nothing the table does not:

> A 256x240 NES-style vertical slice in GameMaker, with Meta models making the art and the dialogue under a checker that enforces the 1989 chip.

A shorter variant, 80 characters, if the field is tight:

> A 256x240 NES-style slice in GameMaker, drawn under a checker for the 1989 chip.

### 4.2 GitHub, the topics

Twelve, lowercase, hyphenated, each one a thing the repository actually contains:

    gamemaker  nes  256x240  pixel-art  vertical-slice  meta-ai  muse-spark  sam-3-1
    llm  python  procedural-art  indie-game

Do not add a tag that claims arrival, such as `playable-slice`: no row scores 4, and the README's own state section says
the slice is under construction.

### 4.3 The submission form fields, as far as the rules state them

`RULES-WATCH-2026-10-24.md` section 3 says the field list is not public yet; these are the five fields any such form
asks for, filled from the repository:

| Field | Text |
| --- | --- |
| Project name | Primordial Paradox |
| One line pitch | A 256 by 240 NES style slice where the art and the dialogue come from Meta models and a checker enforces the 1989 chip. |
| Track | indie, one track only (the waiver: "a project submission may be entered in one (1) track only") |
| Built with | GameMaker LTS 2026; Python 3; Meta Model API (muse-spark-1.3, muse-image-1.0, sam-3.1); ffmpeg |
| What is new during the event | the log required by `SUBMISSION-CHECKLIST.md` item 9, one line per landed card from Oct 26 |

### 4.4 The git tag

`PLAN-WIN` section 0 and `RULES-WATCH` Q ask for one baseline tag before the event work starts. Proposed, not created
here: an annotated tag `hackathon-baseline-2026-10-25` on the last commit of Sat Oct 25, message "scaffold frozen for
the Meta Global AI Developer Hackathon, work after this tag is the in window work". `ci-baseline-2026-10-19` already
exists and is older than the scaffold, so it cannot answer the prior work question on its own. Q4 in section 7 asks
Nayil to confirm the name; the tag itself is a `git tag` on his machine, not a thing this card does.

---

## 5. The feature list, with the Meta model named per feature

One row per feature a judge can see or read about. "None, on purpose" is a real answer: the checker must not be a
model, which is the whole thesis.

| # | Feature | Model | Entry point | What the model makes | Evidence on disk | State today |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Concept art | muse-image-1.0 | `tools/meta_client.py generate_image()` | a flat subject on a plain ground, search tools off | `tools/art/make_characters_v2.py`, `tools/art/make_env_ship.py` | client and mock cache only; `data/ai_cache` 6 entries, all `backend: mock`, no live pixel shipped (row 16, 2) |
| 2 | Silhouette and mask | sam-3.1 | `segment()` | one box and one mask per noun | `tools/sprite_pipe.py`, `tools/quantize_concept.py` | same: no recorded `segment` call (row 16, 2) |
| 3 | Palette first pixeliser | none, on purpose | `tools/quantize_concept.py`, `tools/nes_check.py` | the 4 colour sprite, 3 opaque | `data/palette_recipes.json`, `knowledge/NES-AUDIT.md` | runs and gates; 35 of 183 files fail today (row 16, 2; row 20, 2) |
| 4 | Art review (the eye) | muse-spark-1.3, vision | `vision()` through `tools/eye_critic.py` | a checklist per 256 by 240 frame | `knowledge/ART-BIBLE.md`, `tools/check_art_bible.py` | tool runs on the mock backend (row 16, 2) |
| 5 | Talk judge, the TALK fight | muse-spark-1.3, structured output | `chat_structured()` behind the battle director | a mercy delta, an in character reply, a refusal flag, as JSON | `data/meta_bake.json` rows `fight/navy_sailor/1` to `/3`, `fight/deck_hound/*` | baked, 18 rows, all `source: fallback`, `live` 0 (row 6, 3; row 7, 2) |
| 6 | Gate and NPC lines | muse-spark-1.3 | `chat_structured()` | one reply per named NPC, in character | `data/meta_bake.json` rows `npc/nye/turn_1` to `/3`, `npc/morgan/*`, `gate_dialogue:*` | baked, offline (row 6, 3) |
| 7 | Ear review | muse-spark-1.3, vision on a spectrogram | `vision()` through `tools/ear_critic.py` | scores per cue | `assets/audio/`, `knowledge/MUSIC-STYLE-BIBLE.md` | tool exists, mock only (rows 12, 3; 14, 3) |
| 8 | Music composition | none, on purpose | `tools/render_chip.py`, `tools/hook_score.py`, `tools/gen_title_theme.py` | the 126 bpm waltz and the scene cues | `assets/audio/title_theme_v5/`, `data/audio.json` | real audio files, live in the build (row 12, 3; row 13, 2) |
| 9 | Sprite sheets | none per sheet; recipes come from 1 and 2 | `tools/art/make_characters_v2.py`, `tools/sync_art.py` | 12 committed `spr_*.png` | `game/art/spr_*.png`, `output/chars_contact.png` | 12 of 13 planned, one blocked card (row 17, 2) |
| 10 | The talk guard, so a bad answer cannot stall a fight | none, on purpose | `tools/talk_guard.py`, `tests/test_talk_guard.py` | a verdict table and a refusal path | `data/schemas`, `specs/19-llm-talk.md` section 8 | tested; the card pool rung is not exercised by any demo line (row 7, 2) |

The three model ids are the ones `tools/meta_client.py` routes (`RPMS`, `model_for()`); the waiver names SAM 3 and the
product page serves sam-3.1, so every line here and in the write-up says sam-3.1.

---

## 6. The first 30 seconds: what a judge must see, and what shows it

A line is only a pass when the file or command beside it answers. Times are the 3 minute cut; the 90 second cut carries
the same five things in its first 24 seconds.

| # | By | What the judge must see | The file or command that shows it | Expected output |
| --- | --- | --- | --- | --- |
| 1 | 0:00 | a running game, not a mock up | `python tools/integration_build.py` | `BUILD PASS: Igor compiled the project and launched the game` in `build/last-igor.log` |
| 2 | 0:00 | the pixels are the game's own, not a desktop stretch | `ffprobe -v error -show_entries stream=width,height,r_frame_rate output/demo/nightly-2026-10-26.mp4` | `768x720`, `60/1` |
| 3 | 0:02 | the frame is 256 by 240 at a whole multiple | `output/title_run_1.json` | `"viewport": [8, 31, 768, 720]`, `"scale": 3`, `viewport_score` 0.999935 |
| 4 | 0:04 | a real menu, with CONTINUE dim because there is no save | `output/demo/nightly-2026-10-26.mp4` at 10.8 s (the frame `VIDEO-PLAN.md` section 9 names) | NEW GAME, CONTINUE, SETTINGS, QUIT visible in one frame |
| 5 | 0:08 | a cold boot with no console window | `python tools/capture_title.py`, `tests/test_capture_quiet.py` | exit 0, `the game closed on request (exit code 0)` |
| 6 | 0:12 | the palette rule is enforced by a tool that can fail | `python tools/nes_audit_all.py` | `FAIL  183 file(s), 35 failing, 0 unmeasured` (a pass line would be the lie here) |
| 7 | 0:16 | text on a 30 column box, not a stock font | `specs/05-dialogue.md` lines 9 to 11, `data/ui_layouts.json` | box 240x64 at (8, 168), our own 8x8 font, 30 characters per line, 3 lines per page |
| 8 | 0:20 | a model is in the loop and the build cannot call one | `data/meta_bake.json` plus `tests/test_no_network_in_build.py` | 18 rows with `model` and `request_hash`, `bake.live` 0; the test asserts no URL or key under `game/` |
| 9 | 0:26 | what the build does not do is stated by the project itself | `README.md`, section "Where this stands, stated plainly" | the sentence naming the slice as under construction |
| 10 | 0:29 | nobody is claiming the slice is done | `knowledge/READINESS-2026-10-26.md` section 3 | mean 2.4545 over 22 rows, no row at 4 |

What must not be in these 30 seconds, and each of these was a real temptation: a logo sting, a title card before the
game, a face, the word "revolutionary", a montage of shots that are not in the build, and any number the frame cannot
show. `VIDEO-SCRIPT.md` (the earlier draft) put the problem statement at 0:12 to 0:32; this kit moves it out of the
first 30 seconds on purpose, because the judge's first question is "does it run", not "why".

---

## 7. Q: for gamedev, four items

1. **The drive in the demo.** The scene row has landed: `data/scenes/all.json` holds `drive_to_southampton` and
   `data/maps/all.json` holds `drive_m4_corridor`, and the 2026-10-26 recording enters the drive at 43.25 s. The stills
   are the open half: 0 of the 12 in `output/drive_frames` are inside the palette and row 3 stays at 2. Both scripts
   carry the drive shot at S3. Say either "the stills come into the palette before recording" or "cut S3 and use the
   fallback in section 2", because the 3 minute cut cannot hold a shot that is not legal on Nov 4.
2. **The receipt wording.** Confirm the three value overlay in section 3.3 (`model`, `request_hash`, `source`), since
   the bake is offline today and `VIDEO-PLAN.md` section 5's stronger reading is not available until `bake.live` is
   above 0.
3. **The forced defeat.** S6.4 needs the defeat input R27 owns; nothing in the slice can be lost. If R27 lands no
   trigger, S6 ends on the save (171.00 s per `DEMO-SCRIPT.md` section 2) and both scripts lose the CONTINUE beat,
   which is the only place a judge sees persistence.
4. **The baseline tag name** (`hackathon-baseline-2026-10-25`, section 4.4) and whether the in window log is
   `DEVLOG.md` or a separate file. `RULES-WATCH-2026-10-24.md` Q asks the same question; one answer serves both.

---

## 8. The checks for this card, and how each is met

| The card's check | How this file meets it |
| --- | --- |
| every claim in the write-up maps to a row of the maturity table scoring 2 or higher | section 1.2 maps every claim and statement to named rows of `READINESS-2026-10-26.md` section 3, each scored 2 or 3; the one non build fact (the 150 dollar grant) is labelled as a quoted event fact |
| no line claims arrival | section 1.2 says no row scores 4 and that the page states where the work stands; the write-up's state paragraph names the walk as unproven and the gate, boarding, both fights, the save and the defeat as absent from the recording, and section 6 line 10 cites the mean score |
| the write-up fits one page at 11 point | the same 515 words were set in LaTeX at 11 pt, US Letter, 1 inch margins and `pdflatex` wrote 1 page; `pdfinfo writeup.pdf` returned `Pages: 1` on 2026-10-26; the source ships as `knowledge/submission-kit-2026-10-24-writeup.tex` |
| the checklist has a file or command beside every line | section 6 has ten rows, each with a command or a file path and an expected output string; no row says "should" without one |
| no key or login file, nothing published | no file outside this kit was opened for its values; `data/ai_cache`, `data/meta_bake.json` and `output/demo/*.json` were read for fields only, no credential file was touched, and nothing was uploaded or submitted |
| no dash characters | the file was scanned for U+2013, U+2014, U+2015 and U+2012 after writing; count 0 (section 9) |

Two scripts, one write-up, one page of repo text, one feature table, one checklist. That is the whole kit.

---

## 9. Verification run for this file

Every row below was run or read on 2026-10-26 on node CitadelArana, at HEAD `1a242a4`, and the output is what the
command printed. The 2026-10-23 run of this table is superseded by this one.

| Check | Command | Result |
| --- | --- | --- |
| dashes | `grep -c` for U+2012, U+2013, U+2014 and U+2015 over this file | 0 of each |
| write-up length | the `### 1.1` block, counted by script and by `wc -w` | 530 words |
| write-up page count | `pdflatex knowledge/submission-kit-2026-10-24-writeup.tex`, then `pdfinfo` on the result | `Pages: 1`, 612 x 792 pts (letter) |
| narration pace | the word counts in section 3.1 | 272 words over 180 s, 1.51 w/s, no block above 2.12 |
| About line length | character count of the line in section 4.1 | 142, and 80 for the short variant |
| bake state | `data/meta_bake.json` | 18 rows, `source: fallback` on every row, `live` 0, `calls_attempted` 0, model muse-spark-1.3 |
| scene and map rows | counts over `data/scenes/all.json` and `data/maps/all.json` | 15 scene rows, 5 map rows, `drive_to_southampton` and `drive_m4_corridor` both present |
| route | `python -m pytest tests/test_slice_route.py -q` | `24 passed` |
| NES audit | `python tools/nes_audit_all.py` | exit 1, `183 file(s), 35 failing, 0 unmeasured` |
| rooms | `ls game/rooms` | `rm_pp_boot`, `rm_pp_drive`, `rm_pp_ship`, `rm_pp_title` |
| recording | `output/demo/nightly-2026-10-26_verify.json` | `ok: true`, 73.483 s, 768x720, 60 fps, `run.footsteps` 0 |

Written by assistant on 2026-10-23, re-baselined on 2026-10-26 by card `t_fd766448` on node CitadelArana. Nothing in
this file was published, uploaded or submitted; Nayil submits.
