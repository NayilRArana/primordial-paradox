# JUDGE-PANEL 2026-11-17: what a judge would mark down

Card t_70840bce (W4 JUDGE-PANEL), testing lane. Rubric from
`../arananet/meta-hackathon/WIN-PLAN-2026-10-26.md` line 3: Impact 30, Use of Meta AI
tooling 25, Technical depth 20, Demo 25. Submission Nov 4, 9 PM ET.

## The run

- tool: `tools\judge_panel.py`, which sends through `tools\eye_critic.py` (`post_generate`, `RateGate`, `inline_part`, `redact`) and reads the key through `tools\eye_drive.py`'s loader or this tool's Meta loader; neither transport was reimplemented here.
- backend: meta, which hands the same payload to `tools\meta_client.py` and records the answer in `data\ai_cache`
- video judged: `output/demo/nightly-2026-11-15e-storm.mp4`
- frames: 6, taken at 15.0 s, 45.0 s, 75.0 s, 105.0 s, 135.0 s, 165.0 s, kept in `output/judge_frames`
- model chain, in order: `muse-spark-1.3`; the judge model is muse-spark-1.3 on the Meta Model API, set by the manager on 2026-10-26 17:15, and it is the only model in this chain: a billed API does not hand out a per-model free tier to walk, so a refusal from it is reported rather than walked past
- model that answered: `muse-spark-1.3`
- attempts in this run: muse-spark-1.3 answered
- credential: user environment (META_API_KEY), never printed and never written to this file
- the five drafts are also appended to `../arananet/manager/inbox/director.md` for the manager
- warning: Warning: the panel is a rough critic. It sees six still frames from a video, not the video, it cannot hear the audio, it cannot read the repository and it cannot know what the judges value beyond the four weights quoted here. Where a panel sentence disagrees with a measured number in this file, the measured number wins. Treat the scores as a prompt for the team's own judgement, not as a verdict.

## The score card

| criterion | weight | score | points | one reason |
| --- | --- | --- | --- | --- |
| Impact | 30 | 4 | 12.0 | Talk to SPARE with Mercy is visible but S5 plate says NOT LIVE from bake file so live value is not shown. |
| Use of Meta AI tooling | 25 | 5 | 12.5 | Models are named on title and 21 calls with receipts show on screen but verify labels no Meta number and network dead. |
| Technical depth | 20 | 6 | 12.0 | 256x240 scaled to 768x784 at 60 fps with HP MERCY WILL engine looks real but audio absent and play_demo did not complete. |
| Demo | 25 | 4 | 10.0 | 180 s with picture at every sample and captions explain shots but no voice and no playable nightly file per log. |

Weighted total: **46.5 of 100** (4 of the 4 criteria scored).

Computed as score / 10 * weight for each criterion, by this tool and not by the model, so the total can be reproduced from the table above.

## The top five fixes, each a card body ready to paste

### Fix 1: Repair nightly export so 180s demo plays with sound

- lane: builder
- priority: 93 (the panel's order, so fix 1 is dispatched first)
- criterion it raises: Demo
- body file: `output/judge_cards/2026-11-17/fix-01.md`
- paths the body names that are not in this repository at that place: `output/demo/nightly-2026-11-16.mp4`. The body is a direction, not a location: find the real file before editing anything.

Body, as the file holds it:

```text
Fix the capture harness that wrote output/demo/_run_002_raw.mp4 without a moov atom so output/demo/nightly-2026-11-16.mp4 is finalized inside the 1500 s bound. Add ffmpeg faststart finalization and a verify check that duration reads 180 s with audio present. A judge will see a playable three minute file that opens, plays with sound, and matches the six shot plan in the video.
```

Paste:

```text
hermes kanban --board nayil-ops create --created-by judge-panel --assignee builder --priority 93 --body-file "<repo>\output\judge_cards\2026-11-17\fix-01.md" "Repair nightly export so 180s demo plays with sound"
```

### Fix 2: Show live Muse Spark verdict inside Morgan talk box

- lane: gamedev
- priority: 91 (the panel's order, so fix 1 is dispatched first)
- criterion it raises: Impact
- body file: `output/judge_cards/2026-11-17/fix-02.md`

Body, as the file holds it:

```text
Edit the morgan battle scene and its talk handler to call the local bridge live and draw the returned SOFTEN or NUDGE or SETBACK verdict inside the NES text box during shot S5 from 1:18 to 1:50. Keep data/meta_bake.json only as fallback and keep the three receipts below the box. A judge will see the typed line then the verdict appear in the box and Mercy move in the same shot.
```

Paste:

```text
hermes kanban --board nayil-ops create --created-by judge-panel --assignee gamedev --priority 91 --body-file "<repo>\output\judge_cards\2026-11-17\fix-02.md" "Show live Muse Spark verdict inside Morgan talk box"
```

### Fix 3: Add audible music and talk blips provable in capture

- lane: musician
- priority: 90 (the panel's order, so fix 1 is dispatched first)
- criterion it raises: Demo
- body file: `output/judge_cards/2026-11-17/fix-03.md`

Body, as the file holds it:

```text
Add hurricane wind, text blips and battle stingers in the quay, morgan and percy scenes using the musician lane tracks and wire them to the capture mix. Update the verify step to fail when audio is absent. A judge will hear storm and UI sound through the 180 s video and see audio present in the verify file.
```

Paste:

```text
hermes kanban --board nayil-ops create --created-by judge-panel --assignee musician --priority 90 --body-file "<repo>\output\judge_cards\2026-11-17\fix-03.md" "Add audible music and talk blips provable in capture"
```

### Fix 4: Surface measured Meta receipts and counts on screen

- lane: assistant
- priority: 88 (the panel's order, so fix 1 is dispatched first)
- criterion it raises: Use of Meta AI tooling
- body file: `output/judge_cards/2026-11-17/fix-04.md`

Body, as the file holds it:

```text
Update data/meta_bake.json, the S5 on screen plate and README to show the same measured counts for Muse Spark 1.3 calls, live rows and share percent with full receipt IDs. Make the verify file label which numbers were measured. A judge will read matching numbers on screen, in README and in verify during the Morgan shot.
```

Paste:

```text
hermes kanban --board nayil-ops create --created-by judge-panel --assignee assistant --priority 88 --body-file "<repo>\output\judge_cards\2026-11-17\fix-04.md" "Surface measured Meta receipts and counts on screen"
```

### Fix 5: Enforce and display 16 colour 256x240 check in build

- lane: testing
- priority: 86 (the panel's order, so fix 1 is dispatched first)
- criterion it raises: Technical depth
- body file: `output/judge_cards/2026-11-17/fix-05.md`

Body, as the file holds it:

```text
Add a build time palette and resolution check for 256x240 with at most 16 colours and draw its PASS badge on the title scene next to the NES LIMITS text. Log the check in check_data output. A judge will see the badge on the title card in S1 and find the same PASS in the repo check log.
```

Paste:

```text
hermes kanban --board nayil-ops create --created-by judge-panel --assignee testing --priority 86 --body-file "<repo>\output\judge_cards\2026-11-17\fix-05.md" "Enforce and display 16 colour 256x240 check in build"
```

This tool creates no cards. Five bodies are written and the command above is the whole of what a card needs, so the limit of five a night cannot be broken by running it twice: a second run writes the same five files again and creates nothing.

## What the panel was shown, measured

- Measured duration: 180.000 s. The demo the script plans is 180 s (three minutes), so this capture is inside the judged length.
- Measured stream: 768 x 784, 60.0 fps, codec h264, which is 3x the 256 x 240 frame.
- Frames shown to the panel: 6, taken at 15.0 s, 45.0 s, 75.0 s, 105.0 s, 135.0 s, 165.0 s.
- Measured: none of the 6 frames is one colour over 90 percent of the picture, so the capture has picture at every sample.
- From the capture's own verify file: audio is absent.
- The capture's verify file labels no Meta number, so nothing in it says which Meta figures were measured, computed or inferred.
- The nightly log's own last row, verbatim: 2026-11-16 (nightly run, 20:07, card t_c7a749dc) | repo HEAD 390e9dc7 on master, tree dirty with other lanes work | NO VIDEO: output/demo/nightly-2026-11-16.mp4 was NOT WRITTEN and no older nightly file was touched, because the replay overran the worker 1500 s bound and the harness was stopped mid take; the raw capture output/demo/_run_002_raw.mp4 is 210501680 bytes and has no moov atom, so it cannot be played or cut | check_data PASS (exit 0, "check_data: all files pass") | check_cleanroom PASS (exit 0, 906 files scanned for 26 names and 12 phrases, 48 GML modules, 0 awaiting review, 6 downloaded map file(s) skipped, 242 OSM place name(s) exempt in 2 generated geography card(s); no study reference, no foreign name, no foreign phrase) | play_demo NOT COMPLETED (the idle gate allowed the launch after waiting about 120 s with codex.exe resident and not driving, the window was found and the
- The frames are stills from an h264 capture, so their colour counts include the encoder's own colours and are not a PPU palette measurement; this panel judges what the frames show, not legal 2C02 colours.

The model's impression is not in this section and does not outrank it. Where the two disagree, these numbers win.

## The script excerpt it judged against

From `knowledge/DEMO-SCRIPT.md`, verbatim:

```text
| Shot | Clock | Seconds | Steps | Route step (`data/slice.json`) | The claim it proves | What is drawn over the frame |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | 0:00.00 to 0:16.00 | 16.00 | 960 | `title` | "whether it works", and "AI that obeys hardware limits" | one caption |
| S2 | 0:16.00 to 0:29.00 | 13.00 | 780 | `crawl` | "Kronos and Zeus reincarnated on the M3" | one caption |
| S3 | 0:29.00 to 0:39.00 | 10.00 | 600 | `quay` | the hurricane, and the block it lands on | one caption |
| S4 | 0:39.00 to 1:18.00 | 39.00 | 2,340 | `quay`, then `morgan` | the wind is the only gate, and Morgan offers three answers | one caption |
| S5 | 1:18.00 to 1:50.00 | 32.00 | 1,920 | `morgan` | "the person judging your line is a Meta model answering inside a NES text box", and the quay's own saves | one caption, three bake receipts, the network line |
| S6 | 1:50.00 to 3:00.00 | 70.00 | 4,200 | `percy` | "the other is won by talking", and the one ending the game now has | one caption |
makes no decision. Every shot names what is on screen, what the player inputs, what the music does, what the caption
shows and this file governs only its shape: the total length, six shots, one caption and one claim per shot, and
1. If the re-bake in Q1 has not landed, S5 draws its caption and its box and no plate. The shot still times to
Caption, verbatim: `Cold boot to menu takes 14 seconds. CONTINUE is dim, because nothing is saved yet.`
Caption, verbatim: `The crawl runs 1,238 steps. Hold confirm to read it faster; no page is skipped.`
Caption, verbatim: `Town Quay in the hurricane. The storm runs on its own seeded clock, 8 step flashes over a real Southampton block.`
```

## Cost

- tokens reported by the API: 6304 in / 8646 out
- calls: 1 (one request carrying all 6 frames, plus 0 refused model(s))
- billed: this call ran on the Meta Model API and is charged to the team's credits, so it is not free and the token count above is the spend's shape.
- recorded for replay: the answer is in `data\ai_cache` (meta_client record mode), so the same panel can be played with `PP_AI_MODE=replay` and no key.
- the ledger row is in `data\eye_ledger.csv` with role `judge-panel`, and that row is what the tool's own 2 calls a day ceiling counts.

## Across nights

| date, run | model | impact | meta | depth | demo | points | video |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10-31T04:23:36Z | muse-spark-1.3 | 2 | 3 | 4 | 2 | 26.5 | output/demo/nightly-2026-10-26.mp4 |
| 2026-11-12T05:15:06Z | muse-spark-1.3 | 2 | 3 | 4 | 2 | 26.5 | output/demo/nightly-2026-10-26.mp4 |
| 2026-11-13T05:09:48Z | muse-spark-1.3 | 3 | 3 | 4 | 2 | 29.5 | output/demo/nightly-2026-10-26.mp4 |
| 2026-11-14T05:16:18Z | muse-spark-1.3 | 4 | 3 | 4 | 3 | 35.0 | output/demo/nightly-2026-11-12.mp4 |
| 2026-11-15T05:05:41Z | muse-spark-1.3 | 3 | 3 | 4 | 3 | 32.0 | output/demo/nightly-2026-11-14.mp4 |
| 2026-11-16T05:05:59Z | muse-spark-1.3 | 4 | 3 | 4 | 3 | 35.0 | output/demo/nightly-2026-11-15.mp4 |
| 2026-11-17T05:05:15Z | muse-spark-1.3 | 4 | 5 | 6 | 4 | 46.5 | output/demo/nightly-2026-11-15e-storm.mp4 |

The ledger behind this table is `output/judge_panel_ledger.csv`, one row per run.
**The same capture on the same model scored 26.5, 26.5, 29.5 (a spread of 3.0 points).** That spread is this instrument's own noise on one night, so a single run's total is not a trend: compare the direction across several nights, and treat a move smaller than about 3 points as no move at all.

## Sources

- judging weights and the deadline: `../arananet/meta-hackathon/WIN-PLAN-2026-10-26.md` line 3, read 2026-10-26
- the judge model, the inbox and the cache rule: manager comment on card t_70840bce, 2026-10-26 17:15
- the Meta API shape, its record and replay modes: `tools/meta_client.py` header, read 2026-10-26
- the three minute demo and its six shots: `knowledge/DEMO-SCRIPT.md` sections 1 and 2, read 2026-10-26
- free tier ceiling of 20 requests per project per model per day: `tools/eye_critic.py` header, measured 2026-10-22
- model rotation on a per day refusal: `tools/eye_drive.py`, measured 2026-10-24
- the capture's own numbers: `output/demo/nightly-2026-11-15e-storm_verify.json`
