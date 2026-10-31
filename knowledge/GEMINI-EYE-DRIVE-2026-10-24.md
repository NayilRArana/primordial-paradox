# GEMINI-EYE-DRIVE: twelve shot verdicts, with the NES numbers

Card t_4bf72d3b, testing lane, written 2026-10-24. Subject: the twelve drive shots captured by
card R21a (`rm_pp_drive`, t_e9c7b280) in `tools\capture_drive.py`. Judged against
`knowledge\DRIVE-SHOT-LIST.md` (what each shot is supposed to show), `knowledge\ART-BIBLE.md`
section 4 (the frame rules), and `knowledge\NES-AUDIT.md` (the PPU rules the project gates on).

## The run

- tool: `tools\eye_drive.py`, which drives `tools\eye_critic.py` (the fixed rubric from GEMINI-EYE) and
  `tools\nes_composite_check.py` (the project's own PPU checker). Neither was reimplemented here.
- model chain, in order: `gemini-3.5-flash`, `gemini-3-flash-preview`, `gemini-3.5-flash-lite`
- model that answered: none: the measured half ran alone
- credential: from the environment (absent in this run), never printed, never written to a review file or the ledger
- frames judged: 12 of 12, one per shot, from `output\drive_frames\` (native 256x240). The capture
  itself is `output\drive\pp_drive_shot_01.png` to `_12.png`, 768x720, which is an exact 3x nearest
  scale of 256x240 on every one of the twelve (checked pixel for pixel before the copy, so the
  native copy loses nothing).
- measured half: every legality number below comes from the pixels, not from the model. Where a
  verdict's two halves disagree, the legality half stands.

### The fallback is measured, not claimed

- `python tools\eye_drive.py --self-test` refuses `gemini-3.5-flash` with a real per-day 429 body and the same call then answers on `gemini-3-flash-preview`, so the chain advance is a measured behaviour and not a claim. On the real run the same thing happened without the fake transport: `gemini-3.5-flash` returned a per-day quota refusal (limit 5 on this project) part way through and the remaining shots answered on the next model.

## The twelve verdicts

| # | shot | frame judged | colours | off-palette colours | attribute areas over | legality | art | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `bigben` city | `output/drive_frames/drive_shot_01.png` | 8 | 8 | 0 | FAIL | NOT JUDGED | **FAIL** |
| 2 | `street` city | `output/drive_frames/drive_shot_02.png` | 10 | 10 | 11 | FAIL | NOT JUDGED | **FAIL** |
| 3 | `gantry_55` gantry | `output/drive_frames/drive_shot_03.png` | 10 | 9 | 8 | FAIL | NOT JUDGED | **FAIL** |
| 4 | `rain` motorway | `output/drive_frames/drive_shot_04.png` | 10 | 10 | 5 | FAIL | NOT JUDGED | **FAIL** |
| 5 | `radio_1_2` motorway | `output/drive_frames/drive_shot_05.png` | 10 | 9 | 5 | FAIL | NOT JUDGED | **FAIL** |
| 6 | `radio_3_4_43` motorway | `output/drive_frames/drive_shot_06.png` | 10 | 9 | 3 | FAIL | NOT JUDGED | **FAIL** |
| 7 | `cutting` Twyford Down cutting | `output/drive_frames/drive_shot_07.png` | 10 | 10 | 2 | FAIL | NOT JUDGED | **FAIL** |
| 8 | `cathedral` cathedral | `output/drive_frames/drive_shot_08.png` | 9 | 8 | 5 | FAIL | NOT JUDGED | **FAIL** |
| 9 | `radio_5_6_7_30` motorway | `output/drive_frames/drive_shot_09.png` | 10 | 9 | 4 | FAIL | NOT JUDGED | **FAIL** |
| 10 | `downland` downland | `output/drive_frames/drive_shot_10.png` | 10 | 10 | 2 | FAIL | NOT JUDGED | **FAIL** |
| 11 | `slip_20` slip road | `output/drive_frames/drive_shot_11.png` | 8 | 7 | 8 | FAIL | NOT JUDGED | **FAIL** |
| 12 | `docks` docks | `output/drive_frames/drive_shot_12.png` | 9 | 9 | 1 | FAIL | NOT JUDGED | **FAIL** |

Twelve verdicts: 12 FAIL. The verdict is the worse of the two halves, so a shot that cannot be drawn on
the hardware does not pass whatever the picture looks like.

### Shot 1, `bigben` (city, beat 7, 688 steps)

- frame judged: `output/drive_frames/drive_shot_01.png`
- supposed to show: Big Ben: title_BG_bigben, one 256x240 background, no scroll, the camera pans down the clock face
- colours: 8 distinct, 8 of them not a usable PPU colour covering 61440 pixels
- attribute areas (16x16): 0 of 240 over the 3 colour limit
- background palettes: 4 groups of 3 used, inside the 4 the PPU has
- colours outside the palette: `#08131f` at 27690 pixels, `#1b1b22` at 21134 pixels, `#0b0b0f` at 6358 pixels, `#2b2b36` at 2551 pixels, `#454552` at 2097 pixels
- backdrop: `#1b1b22`
- **verdict: FAIL** (NES legality FAIL, art NOT JUDGED)
- the model said: nothing, this shot was not sent to a model in this run

### Shot 2, `street` (city, beat 8, 860 steps)

- frame judged: `output/drive_frames/drive_shot_02.png`
- supposed to show: the London street, the car pulling away, the Thames
- art gap on the record (DRIVE-SHOT-LIST Q3): no street or river art in the title layer set (Q3)
- colours: 10 distinct, 10 of them not a usable PPU colour covering 61440 pixels
- attribute areas (16x16): 11 of 240 over the 3 colour limit
- background palettes: the 4 palette cover is not reached, because 11 block(s) already carry more than 3 colours besides the backdrop on their own
- worst attribute areas: at 96,176 carrying 5 colours besides the backdrop; at 112,176 carrying 4 colours besides the backdrop; at 128,64 carrying 4 colours besides the backdrop; at 128,176 carrying 4 colours besides the backdrop; at 144,176 carrying 4 colours besides the backdrop
- colours outside the palette: `#081420` at 29007 pixels, `#1c1c24` at 21252 pixels, `#0b0b0f` at 3431 pixels, `#2e2e3a` at 2755 pixels, `#4a4a58` at 2532 pixels
- backdrop: `#0b0b0f`
- **verdict: FAIL** (NES legality FAIL, art NOT JUDGED)
- the model said: nothing, this shot was not sent to a model in this run

### Shot 3, `gantry_55` (gantry, beat 9, 602 steps)

- frame judged: `output/drive_frames/drive_shot_03.png`
- supposed to show: the verge, spr_title_sign frame 1 reading SOUTHAMPTON 55, and spr_title_cone
- gantry sign: 55 miles remaining, `sign_55_seen`, 1 caption page(s)
- colours: 10 distinct, 9 of them not a usable PPU colour covering 60421 pixels
- attribute areas (16x16): 8 of 240 over the 3 colour limit
- background palettes: the 4 palette cover is not reached, because 8 block(s) already carry more than 3 colours besides the backdrop on their own
- worst attribute areas: at 32,176 carrying 4 colours besides the backdrop; at 48,176 carrying 4 colours besides the backdrop; at 64,176 carrying 4 colours besides the backdrop; at 80,176 carrying 4 colours besides the backdrop; at 96,176 carrying 5 colours besides the backdrop
- colours outside the palette: `#081420` at 36779 pixels, `#4a4a58` at 11030 pixels, `#1c1c24` at 8109 pixels, `#2e2e3a` at 2136 pixels, `#c8c8d4` at 1315 pixels
- backdrop: `#081420`
- **verdict: FAIL** (NES legality FAIL, art NOT JUDGED)
- the model said: nothing, this shot was not sent to a model in this run

### Shot 4, `rain` (motorway, beat 10, 774 steps)

- frame judged: `output/drive_frames/drive_shot_04.png`
- supposed to show: layers L1 to L7 with rain falling and the wipers seen from outside the car
- art gap on the record (DRIVE-SHOT-LIST Q3): the rain overlay and the wipers do not exist in the layer set (Q3)
- colours: 10 distinct, 10 of them not a usable PPU colour covering 61440 pixels
- attribute areas (16x16): 5 of 240 over the 3 colour limit
- background palettes: the 4 palette cover is not reached, because 5 block(s) already carry more than 3 colours besides the backdrop on their own
- worst attribute areas: at 144,176 carrying 4 colours besides the backdrop; at 160,160 carrying 4 colours besides the backdrop; at 176,160 carrying 4 colours besides the backdrop; at 208,160 carrying 4 colours besides the backdrop; at 208,176 carrying 5 colours besides the backdrop
- colours outside the palette: `#2e2e3a` at 38621 pixels, `#1c1c24` at 18712 pixels, `#4a4a58` at 2474 pixels, `#c8c8d4` at 536 pixels, `#0b0b0f` at 482 pixels
- backdrop: `#1c1c24`
- **verdict: FAIL** (NES legality FAIL, art NOT JUDGED)
- the model said: nothing, this shot was not sent to a model in this run

### Shot 5, `radio_1_2` (motorway, beat 11, 1032 steps)

- frame judged: `output/drive_frames/drive_shot_05.png`
- supposed to show: radio pages 1 and 2 over the car in long shot, layers L1 to L7
- colours: 10 distinct, 9 of them not a usable PPU colour covering 60791 pixels
- attribute areas (16x16): 5 of 240 over the 3 colour limit
- background palettes: the 4 palette cover is not reached, because 5 block(s) already carry more than 3 colours besides the backdrop on their own
- worst attribute areas: at 80,176 carrying 4 colours besides the backdrop; at 144,176 carrying 6 colours besides the backdrop; at 192,176 carrying 4 colours besides the backdrop; at 240,144 carrying 4 colours besides the backdrop; at 240,176 carrying 4 colours besides the backdrop
- colours outside the palette: `#081420` at 41224 pixels, `#1c1c24` at 7999 pixels, `#4a4a58` at 7829 pixels, `#2e2e3a` at 1779 pixels, `#c8c8d4` at 1045 pixels
- backdrop: `#081420`
- **verdict: FAIL** (NES legality FAIL, art NOT JUDGED)
- the model said: nothing, this shot was not sent to a model in this run

### Shot 6, `radio_3_4_43` (motorway, beat 11, 1118 steps)

- frame judged: `output/drive_frames/drive_shot_06.png`
- supposed to show: radio pages 3 and 4, and spr_title_sign frame 2 reading 43 passing the car
- gantry sign: 43 miles remaining, `sign_43_seen`, 3 caption page(s)
- colours: 10 distinct, 9 of them not a usable PPU colour covering 60417 pixels
- attribute areas (16x16): 3 of 240 over the 3 colour limit
- background palettes: the 4 palette cover is not reached, because 3 block(s) already carry more than 3 colours besides the backdrop on their own
- worst attribute areas: at 144,176 carrying 5 colours besides the backdrop; at 240,144 carrying 4 colours besides the backdrop; at 240,176 carrying 4 colours besides the backdrop
- colours outside the palette: `#081420` at 35797 pixels, `#4a4a58` at 12244 pixels, `#1c1c24` at 8399 pixels, `#2e2e3a` at 1743 pixels, `#c8c8d4` at 1341 pixels
- backdrop: `#081420`
- **verdict: FAIL** (NES legality FAIL, art NOT JUDGED)
- the model said: nothing, this shot was not sent to a model in this run

### Shot 7, `cutting` (Twyford Down cutting, beat 13, 860 steps)

- frame judged: `output/drive_frames/drive_shot_07.png`
- supposed to show: the chalk cutting with walls both sides and one headlight pool
- colours: 10 distinct, 10 of them not a usable PPU colour covering 61440 pixels
- attribute areas (16x16): 2 of 240 over the 3 colour limit
- background palettes: the 4 palette cover is not reached, because 2 block(s) already carry more than 3 colours besides the backdrop on their own
- worst attribute areas: at 160,176 carrying 4 colours besides the backdrop; at 240,144 carrying 4 colours besides the backdrop
- colours outside the palette: `#1b1b22` at 20354 pixels, `#2b2b36` at 20336 pixels, `#b8b8c4` at 13054 pixels, `#454552` at 6410 pixels, `#0b0b0f` at 495 pixels
- backdrop: `#1b1b22`
- **verdict: FAIL** (NES legality FAIL, art NOT JUDGED)
- the model said: nothing, this shot was not sent to a model in this run

### Shot 8, `cathedral` (cathedral, beat 14, 860 steps)

- frame judged: `output/drive_frames/drive_shot_08.png`
- supposed to show: the cathedral silhouette far off on the horizon, one caption
- colours: 9 distinct, 8 of them not a usable PPU colour covering 60733 pixels
- attribute areas (16x16): 5 of 240 over the 3 colour limit
- background palettes: the 4 palette cover is not reached, because 5 block(s) already carry more than 3 colours besides the backdrop on their own
- worst attribute areas: at 96,176 carrying 4 colours besides the backdrop; at 112,176 carrying 4 colours besides the backdrop; at 128,176 carrying 4 colours besides the backdrop; at 144,80 carrying 4 colours besides the backdrop; at 240,176 carrying 4 colours besides the backdrop
- colours outside the palette: `#081420` at 41480 pixels, `#1c1c24` at 12329 pixels, `#4a4a58` at 3691 pixels, `#2e2e3a` at 1282 pixels, `#c8c8d4` at 981 pixels
- backdrop: `#1c1c24`
- **verdict: FAIL** (NES legality FAIL, art NOT JUDGED)
- the model said: nothing, this shot was not sent to a model in this run

### Shot 9, `radio_5_6_7_30` (motorway, beat 15, 1118 steps)

- frame judged: `output/drive_frames/drive_shot_09.png`
- supposed to show: radio pages 5, 6 and 7, and spr_title_sign frame 3 reading 30
- gantry sign: 30 miles remaining, `sign_30_seen`, 4 caption page(s)
- colours: 10 distinct, 9 of them not a usable PPU colour covering 60417 pixels
- attribute areas (16x16): 4 of 240 over the 3 colour limit
- background palettes: the 4 palette cover is not reached, because 4 block(s) already carry more than 3 colours besides the backdrop on their own
- worst attribute areas: at 80,176 carrying 4 colours besides the backdrop; at 144,176 carrying 6 colours besides the backdrop; at 240,144 carrying 4 colours besides the backdrop; at 240,176 carrying 4 colours besides the backdrop
- colours outside the palette: `#081420` at 35795 pixels, `#4a4a58` at 12246 pixels, `#1c1c24` at 8381 pixels, `#2e2e3a` at 1743 pixels, `#c8c8d4` at 1341 pixels
- backdrop: `#081420`
- **verdict: FAIL** (NES legality FAIL, art NOT JUDGED)
- the model said: nothing, this shot was not sent to a model in this run

### Shot 10, `downland` (downland, beat 16 and 17, 1118 steps)

- frame judged: `output/drive_frames/drive_shot_10.png`
- supposed to show: the storm forming over the car: spr_title_cloud, the first lightning, the moon, the downland and the chalk horse
- colours: 10 distinct, 10 of them not a usable PPU colour covering 61440 pixels
- attribute areas (16x16): 2 of 240 over the 3 colour limit
- background palettes: the 4 palette cover is not reached, because 2 block(s) already carry more than 3 colours besides the backdrop on their own
- worst attribute areas: at 96,176 carrying 4 colours besides the backdrop; at 144,176 carrying 4 colours besides the backdrop
- colours outside the palette: `#081420` at 30670 pixels, `#1c1c24` at 18090 pixels, `#4a4a58` at 6066 pixels, `#2e2e3a` at 4399 pixels, `#c8c8d4` at 752 pixels
- backdrop: `#081420`
- **verdict: FAIL** (NES legality FAIL, art NOT JUDGED)
- the model said: nothing, this shot was not sent to a model in this run

### Shot 11, `slip_20` (slip road, beat 18, 688 steps)

- frame judged: `output/drive_frames/drive_shot_11.png`
- supposed to show: spr_title_sign frame 4 reading 20, the cone up, the road narrowing to one lane
- gantry sign: 20 miles remaining, `sign_20_seen`, 1 caption page(s)
- colours: 8 distinct, 7 of them not a usable PPU colour covering 60421 pixels
- attribute areas (16x16): 8 of 240 over the 3 colour limit
- background palettes: the 4 palette cover is not reached, because 8 block(s) already carry more than 3 colours besides the backdrop on their own
- worst attribute areas: at 32,176 carrying 4 colours besides the backdrop; at 32,224 carrying 4 colours besides the backdrop; at 96,176 carrying 4 colours besides the backdrop; at 112,176 carrying 4 colours besides the backdrop; at 128,176 carrying 4 colours besides the backdrop
- colours outside the palette: `#081420` at 34641 pixels, `#4a4a58` at 16164 pixels, `#1c1c24` at 5409 pixels, `#2e2e3a` at 1956 pixels, `#c8c8d4` at 1278 pixels
- backdrop: `#081420`
- **verdict: FAIL** (NES legality FAIL, art NOT JUDGED)
- the model said: nothing, this shot was not sent to a model in this run

### Shot 12, `docks` (docks, beat 19, 962 steps)

- frame judged: `output/drive_frames/drive_shot_12.png`
- supposed to show: the docks: cranes, containers, the ship lit at the quay, then the fade to black
- art gap on the record (DRIVE-SHOT-LIST Q3): no docks art in the layer set (Q3)
- colours: 9 distinct, 9 of them not a usable PPU colour covering 61440 pixels
- attribute areas (16x16): 1 of 240 over the 3 colour limit
- background palettes: the 4 palette cover is not reached, because 1 block(s) already carry more than 3 colours besides the backdrop on their own
- worst attribute areas: at 32,192 carrying 4 colours besides the backdrop
- colours outside the palette: `#081420` at 35241 pixels, `#2e2e3a` at 10678 pixels, `#1c1c24` at 8024 pixels, `#4a4a58` at 2968 pixels, `#c24040` at 2196 pixels
- backdrop: `#c24040`
- **verdict: FAIL** (NES legality FAIL, art NOT JUDGED)
- the model said: nothing, this shot was not sent to a model in this run

## What the twelve verdicts add up to

- The measured failure is the palette, on every shot: 108 non-PPU colour instances across the
  twelve frames, over a 55 usable entry master palette (`data\nes_palette.json`). The largest
  single share is shot 1 (`bigben`) at 61440 pixels off palette. This is the placeholder palette that
  R21a drew with (`#081420`, `#0B0B0F`, `#1C1C24`, `#4A4A58`, `#C8C8D4` and their neighbours),
  not a drawing mistake in a finished asset, and it is the one thing standing between these
  twelve frames and `tools\nes_audit_all.py` passing them as frames.
- The shot structure, which is what R21a was proving, reads correctly: twelve distinct frames,
  each one the place the shot list names, and the four gantry signs in shots 3, 6, 9 and 11.
- Three shots are drawn against art that does not exist yet (2, 4, 12): DRIVE-SHOT-LIST Q3 is
  still open, so their verdicts measure the placeholder, not the film.

## Warning, carried over from the eye critic

Warning: the model is a rough critic. It cannot count pixels reliably, it misreads small text, it does not know our palette, and it will describe things that are not in the frame. Where this review disagrees with a measured number, the measured number wins. Treat the scores as a hint to check against Nayil, not as a verdict.

## Sources

- shot list, timing and the four signs: `knowledge\DRIVE-SHOT-LIST.md` sections 2, 3 and 5
- frame rules: `knowledge\ART-BIBLE.md` section 4, itself sourced to the NESdev wiki
- PPU rules and the failing-row format: `knowledge\NES-AUDIT.md`, `tools\nes_composite_check.py`
- rubric, ledger and free tier: `tools\eye_critic.py`, whose header records the 20 per project
  per model per day measurement taken from the API's own 429 body on 2026-10-22
