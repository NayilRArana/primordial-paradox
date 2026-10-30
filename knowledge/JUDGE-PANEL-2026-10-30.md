# JUDGE-PANEL 2026-10-30: what a judge would mark down

Card t_70840bce (W4 JUDGE-PANEL), testing lane. Rubric from
`../arananet/meta-hackathon/WIN-PLAN-2026-10-26.md` line 3: Impact 30, Use of Meta AI
tooling 25, Technical depth 20, Demo 25. Submission Nov 4, 9 PM ET.

## The run

- tool: `tools\judge_panel.py`, which sends through `tools\eye_critic.py` (`post_generate`, `RateGate`, `inline_part`, `redact`) and reads the key through `tools\eye_drive.py`'s loader or this tool's Meta loader; neither transport was reimplemented here.
- backend: meta, which hands the same payload to `tools\meta_client.py` and records the answer in `data\ai_cache`
- video judged: `output/demo/nightly-2026-10-26.mp4`
- frames: 6, taken at 6.1 s, 18.4 s, 30.6 s, 42.9 s, 55.1 s, 67.4 s, kept in `output/judge_frames`
- model chain, in order: `muse-spark-1.3`; the judge model is muse-spark-1.3 on the Meta Model API, set by the manager on 2026-10-26 17:15, and it is the only model in this chain: a billed API does not hand out a per-model free tier to walk, so a refusal from it is reported rather than walked past
- model that answered: none: the measured half ran alone
- credential: user environment (META_API_KEY), never printed and never written to this file
- the five drafts are also appended to `../arananet/manager/inbox/director.md` for the manager
- warning: Warning: the panel is a rough critic. It sees six still frames from a video, not the video, it cannot hear the audio, it cannot read the repository and it cannot know what the judges value beyond the four weights quoted here. Where a panel sentence disagrees with a measured number in this file, the measured number wins. Treat the scores as a prompt for the team's own judgement, not as a verdict.

## The score card

| criterion | weight | score | points | one reason |
| --- | --- | --- | --- | --- |
| Impact | 30 | NOT JUDGED | - | **NOT JUDGED: the panel gave no score** |
| Use of Meta AI tooling | 25 | NOT JUDGED | - | **NOT JUDGED: the panel gave no score** |
| Technical depth | 20 | NOT JUDGED | - | **NOT JUDGED: the panel gave no score** |
| Demo | 25 | NOT JUDGED | - | **NOT JUDGED: the panel gave no score** |

Weighted total: **0.0 of 100** (0 of the 4 criteria scored). A total with a criterion missing is a floor, not a score: the missing criterion would only add points.

Computed as score / 10 * weight for each criterion, by this tool and not by the model, so the total can be reproduced from the table above.

## The top five fixes, each a card body ready to paste

No fix was parsed out of the panel's answer. That is a finding about the answer, not about the game: the machine readable block was missing or unreadable, and the panel text above is the only record of what it said.

## What the panel was shown, measured

- Measured duration: 73.483 s. The demo the script plans is 180 s (three minutes), so this capture is 106.5 s short of the judged length.
- Measured stream: 768 x 720, 60.0 fps, codec h264, which is 3x the 256 x 240 frame.
- Frames shown to the panel: 6, taken at 6.1 s, 18.4 s, 30.6 s, 42.9 s, 55.1 s, 67.4 s.
- Measured: 2 of the 6 frames are one colour over at least 90 percent of the picture (18.4 s, 30.6 s), which reads as a fade or a black screen.
- From the capture's own verify file: the run planned 71.0 s and recorded 73.5 s; audio is present.
- Labelled Meta number: meta.model_calls is 21, labelled measured, receipt rcpt-a505930564032c7c.
- Labelled Meta number: meta.rows is 21, labelled measured, receipt rcpt-228a2b86d113360e.
- Labelled Meta number: meta.live_rows is 11, labelled measured, receipt rcpt-d207989303deff10.
- Labelled Meta number: meta.fallback_rows is 10, labelled computed, receipt rcpt-a25d011c60f7d140.
- Labelled Meta number: meta.system_chars is 2408, labelled measured, receipt rcpt-f3f7be8c49be6e61.
- Labelled Meta number: meta.live_share_pct is 52.4, labelled computed, receipt rcpt-d5160e529fdadb8f.
- Labelled Meta number: meta.bridge_receipts is 156, labelled measured, receipt rcpt-e9fa4dfc6a87d43f.
- Labelled Meta number: meta.talk_turns_onscreen is 3, labelled inferred, receipt rcpt-f98665d451714d27.
- Every Meta number above carries one of three labels (measured, computed or inferred) and a receipt in data/receipts/meta_receipts.jsonl, so no Meta number in this capture is a number a reader has to take on trust.
- Recorded failure in that run: the game played no footstep cue, so the Right presses did not reach the walk.
- The nightly log's own last row, verbatim: 2026-10-27 | judge-frames | output/demo/nightly-2026-10-26.mp4 | JUDGE-FRAMES FAIL (exit 1, 6 sampled at 6.1 18.4 30.6 42.9 55.1 67.4 s, 2 blank (18.4 s 0.995, 30.6 s 0.924); bake row: 0 frame(s) measured, 2 failure(s); last three differ 0.0084 0.0083 0.0000) | blank: 2 of the 6 sampled frames are one colour over 90 percent: 18.4 s at 0.995, 30.6 s at 0.924 | S5: no frame exists at 85.400 s because the capture ends at 73.483 s, so the bake row is not on screen anywhere in this video | S6: no frame exists at 135.030 s because the capture ends at 73.483 s, so the bake row is not on screen anywhere in this video | frames differ: 3 of the 3 pairs in the last three samples are the same picture (42.9 s and 55.1 s differ in 0.0084; 42.9 s and 67.4 s differ in 0.0083; 55.1 s and 67.4 s differ in 0.0000), and each pair must differ in 0.01 of its pixels
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

## Across nights

| date, run | model | impact | meta | depth | demo | points | video |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10-26T18:29:34Z | gemini-3.5-flash | 2 | 1 | 4 | 1 | 19.0 | output/demo/nightly-2026-10-26.mp4 |
| 2026-10-26T18:33:57Z | gemini-3.5-flash-lite | 5 | 4 | 7 | 3 | 46.5 | output/demo/nightly-2026-10-26.mp4 |
| 2026-10-26T18:36:48Z | gemini-3.5-flash-lite | 4 | 3 | 7 | 3 | 41.0 | output/demo/nightly-2026-10-26.mp4 |
| 2026-10-26T18:40:32Z | gemini-3.5-flash-lite | 4 | 3 | 6 | 3 | 39.0 | output/demo/nightly-2026-10-26.mp4 |
| 2026-10-27T00:34:49Z | muse-spark-1.3 | 2 | 2 | 3 | 2 | 22.0 | output/demo/nightly-2026-10-26.mp4 |

The ledger behind this table is `output/judge_panel_ledger.csv`, one row per run.
**The model changed inside this table (gemini-3.5-flash, gemini-3.5-flash-lite, muse-spark-1.3).** A panel score is comparable across nights only when the same model answered: a change comes from a free-tier daily cap on the Gemini chain or from the team switching the judge model, and a different model scores the same capture differently. Read the direction only where the model column matches, and read a change of model as a change of instrument.
**The same capture on the same model scored 46.5, 41.0, 39.0 (a spread of 7.5 points).** That spread is this instrument's own noise on one night, so a single run's total is not a trend: compare the direction across several nights, and treat a move smaller than about 8 points as no move at all.

## Sources

- judging weights and the deadline: `../arananet/meta-hackathon/WIN-PLAN-2026-10-26.md` line 3, read 2026-10-26
- the judge model, the inbox and the cache rule: manager comment on card t_70840bce, 2026-10-26 17:15
- the Meta API shape, its record and replay modes: `tools/meta_client.py` header, read 2026-10-26
- the three minute demo and its six shots: `knowledge/DEMO-SCRIPT.md` sections 1 and 2, read 2026-10-26
- free tier ceiling of 20 requests per project per model per day: `tools/eye_critic.py` header, measured 2026-10-22
- model rotation on a per day refusal: `tools/eye_drive.py`, measured 2026-10-24
- the capture's own numbers: `output/demo/nightly-2026-10-26_verify.json`
