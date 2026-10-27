# JUDGE-PANEL 2026-10-27: what a judge would mark down

Card t_70840bce (W4 JUDGE-PANEL), testing lane. Rubric from
`../arananet/meta-hackathon/WIN-PLAN-2026-10-26.md` line 3: Impact 30, Use of Meta AI
tooling 25, Technical depth 20, Demo 25. Submission Nov 4, 9 PM ET.

## The run

- tool: `tools\judge_panel.py`, which sends through `tools\eye_critic.py` (`post_generate`, `RateGate`, `inline_part`, `redact`) and reads the key through `tools\eye_drive.py`'s loader or this tool's Meta loader; neither transport was reimplemented here.
- backend: meta, which hands the same payload to `tools\meta_client.py` and records the answer in `data\ai_cache`
- video judged: `output/demo/nightly-2026-10-26.mp4`
- frames: 6, taken at 6.1 s, 18.4 s, 30.6 s, 42.9 s, 55.1 s, 67.4 s, kept in `output/judge_frames`
- model chain, in order: `muse-spark-1.3`; the judge model is muse-spark-1.3 on the Meta Model API, set by the manager on 2026-10-26 17:15, and it is the only model in this chain: a billed API does not hand out a per-model free tier to walk, so a refusal from it is reported rather than walked past
- model that answered: `muse-spark-1.3`
- attempts in this run: muse-spark-1.3 answered
- credential: user environment (META_API_KEY), never printed and never written to this file
- the five drafts are also appended to `../arananet/manager/inbox/director.md` for the manager
- warning: Warning: the panel is a rough critic. It sees six still frames from a video, not the video, it cannot hear the audio, it cannot read the repository and it cannot know what the judges value beyond the four weights quoted here. Where a panel sentence disagrees with a measured number in this file, the measured number wins. Treat the scores as a prompt for the team's own judgement, not as a verdict.

## The score card

| criterion | weight | score | points | one reason |
| --- | --- | --- | --- | --- |
| Impact | 30 | 2 | 6.0 | None of the 6 frames shows talking, a verdict, or the S5 dock office and S6 TALK fight Meta shots. |
| Use of Meta AI tooling | 25 | 2 | 5.0 | No bake row, network line, or caption is visible and the log records 0 footstep cues with Right reaching dialogue not walk. |
| Technical depth | 20 | 3 | 6.0 | The last three frames are identical and frozen with nes_audit_all FAIL on 35 of 183 files and pine FAIL with 3 reds. |
| Demo | 25 | 2 | 5.0 | Measured 73.483s versus planned 180s with 2 of 6 frames over 90 percent one colour and no explainer card. |

Weighted total: **22.0 of 100** (4 of the 4 criteria scored).

Computed as score / 10 * weight for each criterion, by this tool and not by the model, so the total can be reproduced from the table above.

### Where the panel's words disagree with a measured number

- the panel reads the picture as blank or frozen; measured, 2 of 6 sampled frames are one colour over 90 percent (18.4 s, 30.6 s), and the other 4 are lit, so a sentence about the whole capture being static is stronger than the sample supports.

The score beside a sentence like this still stands as the panel's judgement. The measured number is what a reader should act on.

## The top five fixes, each a card body ready to paste

### Fix 1: Recut nightly to full 180s with dock, TALK fight and save ending

- lane: gamedev
- priority: 93 (the panel's order, so fix 1 is dispatched first)
- criterion it raises: Impact
- body file: `output/judge_cards/2026-10-27/fix-01.md`
- paths the body names that are not in this repository at that place: `scripts/play_demo.py`. The body is a direction, not a location: find the real file before editing anything.

Body, as the file holds it:

```text
Extend scripts/play_demo.py and the S5 dock office plus S6 TALK fight scenes to play the full 180 second shot table through ship log save and game over. Record live player speech to the local bridge and render the model verdict inside the NES textbox during the walk and the fight. A judge will watch the talking exchange, the single command win and the talking win without narration explaining it.
```

Paste:

```text
hermes kanban --board nayil-ops create --created-by judge-panel --assignee gamedev --priority 93 --body-file "<repo>\output\judge_cards\2026-10-27\fix-01.md" "Recut nightly to full 180s with dock, TALK fight and save ending"
```

### Fix 2: Render Meta verdict live in NES textbox with bake overlay

- lane: assistant
- priority: 91 (the panel's order, so fix 1 is dispatched first)
- criterion it raises: Use of Meta AI tooling
- body file: `output/judge_cards/2026-10-27/fix-02.md`

Body, as the file holds it:

```text
Add the bake row overlay and network line rendering to the S5 and S6 caption system in the demo overlay code. Show model name, bake time and offline dead network badge while the verdict types in the textbox. A judge will read the bake rows on screen and see the offline shot prove the model ran locally.
```

Paste:

```text
hermes kanban --board nayil-ops create --created-by judge-panel --assignee assistant --priority 91 --body-file "<repo>\output\judge_cards\2026-10-27\fix-02.md" "Render Meta verdict live in NES textbox with bake overlay"
```

### Fix 3: Fix walk input so Right steps play footsteps to dock office

- lane: testing
- priority: 90 (the panel's order, so fix 1 is dispatched first)
- criterion it raises: Technical depth
- body file: `output/judge_cards/2026-10-27/fix-03.md`

Body, as the file holds it:

```text
Fix the input routing in the Town Quay walk update so Right presses leave dialogue and drive the walk state with footstep cues. Repair output/demo/nightly-2026-10-26.mp4 generation to reach the dock office instead of stalling on the field. A judge will hear footsteps and watch the blue sprite cross the field to the dock in the video.
```

Paste:

```text
hermes kanban --board nayil-ops create --created-by judge-panel --assignee testing --priority 90 --body-file "<repo>\output\judge_cards\2026-10-27\fix-03.md" "Fix walk input so Right steps play footsteps to dock office"
```

### Fix 4: Burn in shot captions and title card explaining the build

- lane: builder
- priority: 88 (the panel's order, so fix 1 is dispatched first)
- criterion it raises: Demo
- body file: `output/judge_cards/2026-10-27/fix-04.md`

Body, as the file holds it:

```text
Burn in the six verbatim shot captions and an opening title card stating Meta models plus NES hardware limits in the video builder. Use the same caption font over S1 title, S2 crawl, S3 drive and S4 gate through S6 fight. A judge will understand the claim of each shot without being told what to see.
```

Paste:

```text
hermes kanban --board nayil-ops create --created-by judge-panel --assignee builder --priority 88 --body-file "<repo>\output\judge_cards\2026-10-27\fix-04.md" "Burn in shot captions and title card explaining the build"
```

### Fix 5: Commit missing theme audio and clear audit and pine reds

- lane: audit
- priority: 86 (the panel's order, so fix 1 is dispatched first)
- criterion it raises: Technical depth
- body file: `output/judge_cards/2026-10-27/fix-05.md`
- paths the body names that are not in this repository at that place: `datafiles/streams/percy_theme_v3.ogg`. The body is a direction, not a location: find the real file before editing anything.

Body, as the file holds it:

```text
Commit datafiles/streams/percy_theme_v3.ogg and assets/audio/percy_theme_v3/percy_theme_v3.ogg and fix the 35 failing nes_audit files. Rerun nes_audit_all and the pine suite until check_data, check_cleanroom and play_demo check all pass and document it in the README. A judge will see PASS badges in the README and hear the intended music in the video.
```

Paste:

```text
hermes kanban --board nayil-ops create --created-by judge-panel --assignee audit --priority 86 --body-file "<repo>\output\judge_cards\2026-10-27\fix-05.md" "Commit missing theme audio and clear audit and pine reds"
```

This tool creates no cards. Five bodies are written and the command above is the whole of what a card needs, so the limit of five a night cannot be broken by running it twice: a second run writes the same five files again and creates nothing.

## What the panel was shown, measured

- Measured duration: 73.483 s. The demo the script plans is 180 s (three minutes), so this capture is 106.5 s short of the judged length.
- Measured stream: 768 x 720, 60.0 fps, codec h264, which is 3x the 256 x 240 frame.
- Frames shown to the panel: 6, taken at 6.1 s, 18.4 s, 30.6 s, 42.9 s, 55.1 s, 67.4 s.
- Measured: 2 of the 6 frames are one colour over at least 90 percent of the picture (18.4 s, 30.6 s), which reads as a fade or a black screen.
- From the capture's own verify file: the run planned 71.0 s and recorded 73.5 s; audio is present.
- Recorded failure in that run: the game played no footstep cue, so the Right presses did not reach the walk.
- The nightly log's own last row, verbatim: 2026-10-26 | 37efb6a | output/demo/nightly-2026-10-26.mp4 | check_data PASS (exit 0) | check_cleanroom PASS (exit 0) | play_demo PASS (exit 0, 73.483 s, 768x720 h264 yuv420p at 60 fps, aac stand-in audio; note recorded by the tool: 0 footstep cues, so the Right presses reached the dialogue and not the walk) | play_demo --check PASS (exit 0, run_001.mp4; the nightly file checked the same way and passed all six) | nes_audit_all FAIL (exit 1, 35 of 183 files failing, 0 unmeasured) | pine suite FAIL (exit 1: pine passed=1557 failed=3 skipped=53 deselected=3, desktop passed=84 failed=3, SUMMARY passed=1641 failed=3, pine carried 94.9 percent of 1644; the 3 reds are the same 3 rows, and the cause is two theme sources git does not carry: MISSING FROM COMMIT datafiles/streams/percy_theme_v3.ogg, UNCOMMITTED SOURCE assets/audio/percy_theme_v3/percy_theme_v3.ogg, UNCOMMITTED SOURCE assets/audio/pe
- The frames are stills from an h264 capture, so their colour counts include the encoder's own colours and are not a PPU palette measurement; this panel judges what the frames show, not legal 2C02 colours.

The model's impression is not in this section and does not outrank it. Where the two disagree, these numbers win.

## The script excerpt it judged against

From `knowledge/DEMO-SCRIPT.md`, verbatim:

```text
| Shot | Clock | Seconds | Steps | Route step (ROADMAP section 0) | The claim it proves | What is drawn over the frame |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | 0:00.00 to 0:16.00 | 16.00 | 960 | title attract, PRESS START, NEW GAME | "whether it works", and "AI that obeys hardware limits" | one caption |
| S2 | 0:16.00 to 0:29.00 | 13.00 | 780 | the crawl | "Kronos and Zeus reincarnated on the M3" | one caption |
| S3 | 0:29.00 to 0:39.03 | 10.03 | 602 | the drive, one shot, with a gantry sign | "an NES-faithful night drive" | one caption |
| S4 | 0:39.03 to 1:19.03 | 40.00 | 2,400 | arrival at Town Quay, the gate checkpoint and its three option choice | the block is a real street; the gate cannot be failed | one caption |
| S5 | 1:19.03 to 1:53.03 | 34.00 | 2,040 | the walk to the dock office, the boarding pass, the boarding | "the person judging your line is a Meta model answering inside a NES text box" (Meta shot 1) | caption plus the bake row |
| S6 | 1:53.03 to 3:00.00 | 66.97 | 4,018 | the first fight, the TALK fight, the ship's log save, the game over | "One is won with a single command. The other is won by talking", and the bake on a dead network (Meta shot 2, the offline shot) | caption plus three bake rows plus the network line |
makes no decision. Every shot names what is on screen, what the player inputs, what the music does, what the caption
Caption, verbatim: `Cold boot to menu in 14 seconds. CONTINUE is dim because there is no save yet.`
Caption, verbatim: `The crawl is 1,238 steps on the engine. A held confirm reads it faster and never skips a page.`
Input: confirm once at 0:35.00, which closes the one caption.
Music: `title_theme` plus `car_engine_loop` from the fade in, plus text blips while the caption types, which is the
Caption, verbatim: `One of the twelve drive shots: the sign counts down, and the cut lands on a bar of the waltz.`
```

## Cost

- tokens reported by the API: 6253 in / 7549 out
- calls: 1 (one request carrying all 6 frames, plus 0 refused model(s))
- billed: this call ran on the Meta Model API and is charged to the team's credits, so it is not free and the token count above is the spend's shape.
- recorded for replay: the answer is in `data\ai_cache` (meta_client record mode), so the same panel can be played with `PP_AI_MODE=replay` and no key.
- the ledger row is in `data\eye_ledger.csv` with role `judge-panel`, and that row is what the tool's own 2 calls a day ceiling counts.

## Across nights

| date, run | model | impact | meta | depth | demo | points | video |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10-26T18:29:34Z | gemini-3.5-flash | 2 | 1 | 4 | 1 | 19.0 | output/demo/nightly-2026-10-26.mp4 |
| 2026-10-26T18:33:57Z | gemini-3.5-flash-lite | 5 | 4 | 7 | 3 | 46.5 | output/demo/nightly-2026-10-26.mp4 |
| 2026-10-26T18:36:48Z | gemini-3.5-flash-lite | 4 | 3 | 7 | 3 | 41.0 | output/demo/nightly-2026-10-26.mp4 |
| 2026-10-26T18:40:32Z | gemini-3.5-flash-lite | 4 | 3 | 6 | 3 | 39.0 | output/demo/nightly-2026-10-26.mp4 |
| 2026-10-27T00:34:49Z | muse-spark-1.3 | 2 | 2 | 3 | 2 | 22.0 | output/demo/nightly-2026-10-26.mp4 |

The ledger behind this table is `output/judge_panel_ledger.csv`, one row per run.
**The model changed inside this table (gemini-3.5-flash, gemini-3.5-flash-lite, muse-spark-1.3).** A panel score is comparable across nights only when the same model answered: the free tier forces a change when a model hits its daily cap, and a different model scores the same capture differently. Read the direction only where the model column matches, and read a change of model as a change of instrument.
**The same capture on the same model scored 46.5, 41.0, 39.0 (a spread of 7.5 points).** That spread is this instrument's own noise on one night, so a single run's total is not a trend: compare the direction across several nights, and treat a move smaller than about 8 points as no move at all.

## Sources

- judging weights and the deadline: `../arananet/meta-hackathon/WIN-PLAN-2026-10-26.md` line 3, read 2026-10-26
- the judge model, the inbox and the cache rule: manager comment on card t_70840bce, 2026-10-26 17:15
- the Meta API shape, its record and replay modes: `tools/meta_client.py` header, read 2026-10-26
- the three minute demo and its six shots: `knowledge/DEMO-SCRIPT.md` sections 1 and 2, read 2026-10-26
- free tier ceiling of 20 requests per project per model per day: `tools/eye_critic.py` header, measured 2026-10-22
- model rotation on a per day refusal: `tools/eye_drive.py`, measured 2026-10-24
- the capture's own numbers: `output/demo/nightly-2026-10-26_verify.json`
