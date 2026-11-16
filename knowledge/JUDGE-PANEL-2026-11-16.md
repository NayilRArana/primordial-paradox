# JUDGE-PANEL 2026-11-16: what a judge would mark down

Card t_70840bce (W4 JUDGE-PANEL), testing lane. Rubric from
`../arananet/meta-hackathon/WIN-PLAN-2026-10-26.md` line 3: Impact 30, Use of Meta AI
tooling 25, Technical depth 20, Demo 25. Submission Nov 4, 9 PM ET.

## The run

- tool: `tools\judge_panel.py`, which sends through `tools\eye_critic.py` (`post_generate`, `RateGate`, `inline_part`, `redact`) and reads the key through `tools\eye_drive.py`'s loader or this tool's Meta loader; neither transport was reimplemented here.
- backend: meta, which hands the same payload to `tools\meta_client.py` and records the answer in `data\ai_cache`
- video judged: `output/demo/nightly-2026-11-15.mp4`
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
| Impact | 30 | 4 | 12.0 | Battle frames show talk or spare win over Morgan and Percy but show no live verdict proving only Meta models make it possible. |
| Use of Meta AI tooling | 25 | 3 | 7.5 | Last frame names Muse Spark Image and SAM but no S5 bake receipts or network line is visible and verify file labels no Meta number. |
| Technical depth | 20 | 4 | 8.0 | Town grid and HP MERCY turn UI at 3x scale looks like real engine but log shows dirty tree with 1112 paths and play_demo NOT COMPLETED. |
| Demo | 25 | 3 | 7.5 | 180s capture has picture in all 6 samples but audio is absent and open is blue bars with only one bottom caption visible. |

Weighted total: **35.0 of 100** (4 of the 4 criteria scored).

Computed as score / 10 * weight for each criterion, by this tool and not by the model, so the total can be reproduced from the table above.

## The top five fixes, each a card body ready to paste

### Fix 1: Add narrator voiceover proving live Meta talk judgement

- lane: assistant
- priority: 93 (the panel's order, so fix 1 is dispatched first)
- criterion it raises: Demo
- body file: `output/judge_cards/2026-11-16/fix-01.md`

Body, as the file holds it:

```text
Edit data/slice.json shot S5 morgan and the narration script to add a recorded human voice explaining the talk input and the model verdict. Rerecord output/demo/nightly video with the voice mixed over game audio so captions remain readable. A judge will hear the explanation and see the cursor choose TALK then SPARE during the Morgan and Percy fights in the 3 minute video.
```

Paste:

```text
hermes kanban --board nayil-ops create --created-by judge-panel --assignee assistant --priority 93 --body-file "<repo>\output\judge_cards\2026-11-16\fix-01.md" "Add narrator voiceover proving live Meta talk judgement"
```

### Fix 2: Show AI verdict box with bake receipts and network line

- lane: gamedev
- priority: 91 (the panel's order, so fix 1 is dispatched first)
- criterion it raises: Use of Meta AI tooling
- body file: `output/judge_cards/2026-11-16/fix-02.md`

Body, as the file holds it:

```text
Edit the morgan battle scene to draw the S5 verdict box that names Muse Spark 1.3, shows the decision text, plus three bake receipts and the network line. Keep the HP 28/28 and MERCY bars and party line ZANDER KONRAD HADRIAN visible behind the box. A judge will see the model decision and receipts on screen from 1:18 to 1:50 in the video and in the README screenshot.
```

Paste:

```text
hermes kanban --board nayil-ops create --created-by judge-panel --assignee gamedev --priority 91 --body-file "<repo>\output\judge_cards\2026-11-16\fix-02.md" "Show AI verdict box with bake receipts and network line"
```

### Fix 3: Replace starfield open with readable title and boot menu

- lane: gamedev
- priority: 90 (the panel's order, so fix 1 is dispatched first)
- criterion it raises: Demo
- body file: `output/judge_cards/2026-11-16/fix-03.md`

Body, as the file holds it:

```text
Edit the title route step to draw a title card with game name, controls, and the verbatim caption Cold boot to menu takes 14 seconds with dim CONTINUE. Replace the abstract blue band starfield used at 0:00 to 0:16. A judge will see a readable opening that states what the game is in the first 16 seconds of the video.
```

Paste:

```text
hermes kanban --board nayil-ops create --created-by judge-panel --assignee gamedev --priority 90 --body-file "<repo>\output\judge_cards\2026-11-16\fix-03.md" "Replace starfield open with readable title and boot menu"
```

### Fix 4: Mix hurricane and battle audio and ship video with sound

- lane: musician
- priority: 88 (the panel's order, so fix 1 is dispatched first)
- criterion it raises: Demo
- body file: `output/judge_cards/2026-11-16/fix-04.md`

Body, as the file holds it:

```text
Ask the musician lane to add a hurricane wind loop for quay and simple square wave blips for cursor and talk in the engine audio module. Render the nightly capture with audio enabled at 60 fps and confirm the verify file reports audio present. A judge will hear storm and menu sounds across the full 180 seconds instead of silence.
```

Paste:

```text
hermes kanban --board nayil-ops create --created-by judge-panel --assignee musician --priority 88 --body-file "<repo>\output\judge_cards\2026-11-16\fix-04.md" "Mix hurricane and battle audio and ship video with sound"
```

### Fix 5: Tag clean repo and finish full 180 second nightly render

- lane: testing
- priority: 86 (the panel's order, so fix 1 is dispatched first)
- criterion it raises: Technical Depth
- body file: `output/judge_cards/2026-11-16/fix-05.md`

Body, as the file holds it:

```text
Create a clean tag from repo HEAD 461cb9a5 without the 1112 dirty paths and rerun play_demo to completion to produce output/demo/nightly-2026-11-15.mp4. Record the passing check_data and check_cleanroom lines in the README. A judge will see a complete reproducible build and a finished 180 second video in the repo.
```

Paste:

```text
hermes kanban --board nayil-ops create --created-by judge-panel --assignee testing --priority 86 --body-file "<repo>\output\judge_cards\2026-11-16\fix-05.md" "Tag clean repo and finish full 180 second nightly render"
```

This tool creates no cards. Five bodies are written and the command above is the whole of what a card needs, so the limit of five a night cannot be broken by running it twice: a second run writes the same five files again and creates nothing.

## What the panel was shown, measured

- Measured duration: 180.000 s. The demo the script plans is 180 s (three minutes), so this capture is inside the judged length.
- Measured stream: 768 x 784, 60.0 fps, codec h264, which is 3x the 256 x 240 frame.
- Frames shown to the panel: 6, taken at 15.0 s, 45.0 s, 75.0 s, 105.0 s, 135.0 s, 165.0 s.
- Measured: none of the 6 frames is one colour over 90 percent of the picture, so the capture has picture at every sample.
- From the capture's own verify file: audio is absent.
- The capture's verify file labels no Meta number, so nothing in it says which Meta figures were measured, computed or inferred.
- The nightly log's own last row, verbatim: 2026-11-15 (nightly run, 20:04, card t_e28a2831) | repo HEAD 461cb9a5 on master, tree dirty with other lanes' work (1112 changed paths) | NO VIDEO: the name output/demo/nightly-2026-11-15.mp4 was already taken by an older take of 18643057 bytes written 2026-11-15 16:14, which was left untouched, and tonight's new take output/demo/nightly-2026-11-15b.mp4 did NOT FINISH | check_data PASS (exit 0, "check_data: all files pass") | check_cleanroom PASS (exit 0, 905 files scanned for 26 names and 12 phrases, 48 GML modules, 0 awaiting review, 6 downloaded map file(s) skipped, 242 OSM place name(s) exempt in 2 generated geography card(s); no study reference, no foreign name, no foreign phrase, every module reviewed) | play_demo NOT COMPLETED (no exit code: the idle gate passed and let the launch through, the window was found and the recording started at 20:04, and the replay was still cycling ba
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

- tokens reported by the API: 6314 in / 6797 out
- calls: 1 (one request carrying all 6 frames, plus 0 refused model(s))
- billed: this call ran on the Meta Model API and is charged to the team's credits, so it is not free and the token count above is the spend's shape.
- recorded for replay: the answer is in `data\ai_cache` (meta_client record mode), so the same panel can be played with `PP_AI_MODE=replay` and no key.
- the ledger row is in `data\eye_ledger.csv` with role `judge-panel`, and that row is what the tool's own 2 calls a day ceiling counts.

## Across nights

| date, run | model | impact | meta | depth | demo | points | video |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10-27T00:34:49Z | muse-spark-1.3 | 2 | 2 | 3 | 2 | 22.0 | output/demo/nightly-2026-10-26.mp4 |
| 2026-10-31T04:23:36Z | muse-spark-1.3 | 2 | 3 | 4 | 2 | 26.5 | output/demo/nightly-2026-10-26.mp4 |
| 2026-11-12T05:15:06Z | muse-spark-1.3 | 2 | 3 | 4 | 2 | 26.5 | output/demo/nightly-2026-10-26.mp4 |
| 2026-11-13T05:09:48Z | muse-spark-1.3 | 3 | 3 | 4 | 2 | 29.5 | output/demo/nightly-2026-10-26.mp4 |
| 2026-11-14T05:16:18Z | muse-spark-1.3 | 4 | 3 | 4 | 3 | 35.0 | output/demo/nightly-2026-11-12.mp4 |
| 2026-11-15T05:05:41Z | muse-spark-1.3 | 3 | 3 | 4 | 3 | 32.0 | output/demo/nightly-2026-11-14.mp4 |
| 2026-11-16T05:05:59Z | muse-spark-1.3 | 4 | 3 | 4 | 3 | 35.0 | output/demo/nightly-2026-11-15.mp4 |

The ledger behind this table is `output/judge_panel_ledger.csv`, one row per run.
**The same capture on the same model scored 22.0, 26.5, 26.5, 29.5 (a spread of 7.5 points).** That spread is this instrument's own noise on one night, so a single run's total is not a trend: compare the direction across several nights, and treat a move smaller than about 8 points as no move at all.

## Sources

- judging weights and the deadline: `../arananet/meta-hackathon/WIN-PLAN-2026-10-26.md` line 3, read 2026-10-26
- the judge model, the inbox and the cache rule: manager comment on card t_70840bce, 2026-10-26 17:15
- the Meta API shape, its record and replay modes: `tools/meta_client.py` header, read 2026-10-26
- the three minute demo and its six shots: `knowledge/DEMO-SCRIPT.md` sections 1 and 2, read 2026-10-26
- free tier ceiling of 20 requests per project per model per day: `tools/eye_critic.py` header, measured 2026-10-22
- model rotation on a per day refusal: `tools/eye_drive.py`, measured 2026-10-24
- the capture's own numbers: `output/demo/nightly-2026-11-15_verify.json`
