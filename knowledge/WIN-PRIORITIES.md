# WIN PRIORITIES, 2026-10-26: every open Primordial Paradox card, ranked by what a judge will see

Card `t_29dcf655` (gamedev, node CitadelArana), written in the hour after the win plan
(`Shared/projects/arananet/meta-hackathon/WIN-PLAN-2026-10-26.md`). Submission is 2026-11-04 21:00 ET,
and the scoring is Impact 30, Meta AI tooling 25, Technical depth 20, Demo 25. Judges mostly watch a
3 minute video and skim a README and a repo.

The one rule applied to every card below: **would a judge see it in the 3 minute video, the README, or
the repo?** If the answer is no, the card is paused with the reason `after the submission`, or parked at
a priority under 30 when it was already blocked and needed no status change.

## What was measured

    board nayil-ops, read at 2026-10-26 (the board sqlite, read only, and hermes kanban list --json)
    130 open cards = 23 todo + 10 ready + 83 blocked + 14 running
     65 of them are Primordial Paradox cards, listed below
     64 are other projects (Musikage, job discovery, remote client, the fleet, a protected profile)

A few cards closed while this page was being written, so they no longer hold a priority. They are
named here because the ranking was made on them, with the priority this page gave them:

- `t_2f0b1f93` LICENCE-INVENTORY: ranked 66, closed before the priorities were applied
- `t_c146e9cd` WRITEUP-CLAIM-BANK: ranked 87, closed before the priorities were applied
- `t_c8bfe899` MUSIC-DEMO-BED: ranked 70, closed before the priorities were applied
- not game cards, closed while writing: `t_b6a1a4f5`, `t_dca2eecd`

Two cards are protected by the board rules and appear at the top whatever their visibility:
`t_771e78ef` MOVE-HOLD (Nayil's own order) and the META cards `t_5031b766` and `t_9332fe42`. No W card is
paused either. `a protected profile` was not touched.

## 1. The win path, priorities 90 to 99

These are the cards the plan puts at the top and they stay there: W1 and W2 (the live talk fight), the
title and fight music rulings, the README, and the public repo. Two changes in this band. `t_73682c8d`
W6 DEMO-CUT goes from 90 to 91, because the video is the only artifact every judge watches and it
should not sit below a mix pass. `t_da67bc63`, the five submission rows only Nayil can close, goes
from 88 to 90: the submission cannot be filed without them.

| Card | Status | Was | Now | Visible in video, README or repo | Judging axis | Effort | What it is |
|---|---|---|---|---|---|---|---|
| `t_29dcf655` | running | 99 | 99 | no | Demo (it decides the rest) | S | the ranking itself: every other card is read through it |
| `t_771e78ef` | running | 98 | 98 | video | Demo | S | holding a direction walks the map; every map second of the video rides on it |
| `t_c784d239` | running | 97 | 97 | README+repo | Meta tooling | M | the local bridge the talk fight calls: a bridge in the repo is an architecture a judge can read |
| `t_ee178652` | ready | 96 | 96 | video | Impact + Meta tooling | M | speak an argument, the sailor answers and his WILL bar moves: the one clip that wins the video |
| `t_5031b766` | blocked | 95 | 95 | README+repo | Meta tooling | M | real Meta calls in the game and a README that says which ones are live |
| `t_29578bd8` | running | 95 | 95 | README+repo | Meta tooling (bonus) | M | a Meta open-weight model answering on this PC: the Open Weights bonus verification steps |
| `t_70840bce` | running | 94 | 94 | no | Demo (it feeds the video) | S | nightly mock judging of the cut; it sees nothing a judge sees but it is what moves the demo score |
| `t_9332fe42` | blocked | 93 | 93 | video | Meta tooling + Impact | M | Muse Image and SAM 3.1 pixels on screen, credited on the page |
| `t_120dc9f2` | running | 92 | 92 | video | Demo | M | the final mixes on the route; a video with a cue sheet is the difference between a game and a clip |
| `t_73682c8d` | running | 90 | 91 | video | Demo | M | the 3 minute cut built around the live talk moment: the only artifact every judge watches |
| `t_da67bc63` | blocked | 88 | 90 | no (the submission form) | Submission gate | S (Nayil) | five submission rows need Nayil: licence and public URL, tag push, demo hosting, team, rules |

## 2. On screen or in the tree, priorities 60 to 89

Everything here lands on a screen a judge sees (the demo route, the ship dialogue box, the drive stills,
the arena, art) or in the tree a judge clones (the public repo, the licences, the build inputs).

One correction, measured after the first draft. `t_c024f8bc` ARRIVAL-MAP was ranked at 77 on the
assumption that the Town Quay map did not exist. It does: `data/maps/all.json` line 133 defines
`southampton_town_quay` at 53 by 56 tiles, because the work was re-issued as ARRIVAL-MAP-2
(`t_db2995d7`) and that card is done. `t_c024f8bc` is the superseded original, so it is parked at 2 and
the only work left on it is closing it. The lesson is on the page rather than quietly fixed: a card's
status is not the state of the tree, and the tree is what a judge sees.

| Card | Status | Was | Now | Visible in video, README or repo | Judging axis | Effort | What it is |
|---|---|---|---|---|---|---|---|
| `t_7b18be6f` | running | 92 | 89 | repo | Technical depth | M | the public repo: tests for the README tools and the exporter, and a privacy gate on push |
| `t_2ecb3c38` | todo | 86 | 88 | repo | Technical depth | S | the public repo follows the project nightly, so the repo a judge opens is today's |
| `t_135be998` | blocked | 90 | 86 | README+repo | Meta tooling | S | one live Meta call replaces a fallback row, so a judge reads source: live in the shipped file |
| `t_2a2baf83` | blocked | 0 | 85 | no (the bonus) | Meta tooling (bonus) | S (Nayil) | four Meta bonus decisions, three of which gate the bonus cards |
| `t_d6060104` | running | 82 | 84 | video | Demo + Impact | L | the palette-first GPU art batches that put plates and sprites on screen |
| `t_8b07fe69` | blocked | 0 | 83 | video | Demo | S | the title theme is landed; PP-01 identity and one ear pass are the last two steps before the menu music is final |
| `t_c0597404` | running | 93 | 82 | video | Demo | M | M0: why title v7 and v8 sound dissonant, and a resolved v9. Nayil called the top-scoring title dissonant, and the title is the first sound in the video |
| `t_65512e1c` | todo | 90 | 81 | video | Demo | L | M3: Baroque title and fight cues from the counterpoint engine, Nayil picks by ear. This is the cue set the video plays |
| `t_279ef225` | blocked | 0 | 80 | video | Demo | S | battle cue v2, PP-04 wiring and the 168 vs 126 tempo line: the fight music the video plays |
| `t_16417018` | blocked | 0 | 79 | video+repo | Demo + Technical depth | S | two title builds sit uncommitted and the yyp names a third: five red rows and the title music in one commit |
| `t_9275989a` | blocked | 70 | 78 | video | Demo | S | PP-BOARDING is cut to the authored 32 s beat while the scene row asks for 208 steps: a one line ruling |
| `t_030a89e5` | blocked | 79 | 78 | repo | Technical depth | M | a test that proves every step of the demo route exists and ends before anything is recorded |
| `t_6d66f32d` | blocked | 85 | 77 | video | Demo | S | one rulings file that frees the four decision cards above: the cheapest unblock on the board |
| `t_769b545d` | running | 20 | 76 | video | Demo | S | the dialogue box frame on the ship draws in PP_COLOUR_MISSING; it is on screen in every ship line of the video |
| `t_b50612ab` | blocked | 60 | 75 | video | Demo | S | the first five seconds after NEW GAME: the star pan, the twinkle and the fade a judge sees before anything else |
| `t_2a743083` | blocked | 80 | 74 | video | Demo | M | all 12 drive stills outside the 2C02 set: the S3 shot in the cut is a frame the hardware could not draw |
| `t_f034f9d0` | blocked | 0 | 73 | video | Demo | S | the same drive defect as a ruling: the drive has no palette set at all in scene_palettes.json |
| `t_6420e93e` | blocked | 55 | 72 | video | Demo | M | dodge hazards are 1.00:1 on the deck's sea, so the hazard is invisible in the very frames the arena is shown |
| `t_8a23f384` | ready | 85 | 71 | video | Demo | M | the three music GPU jobs that finish the route cues |
| `t_89109597` | running | 78 | 69 | video | Demo (bonus) | S | the 45 to 60 second cut for the viral prize, made from game footage |
| `t_fe2734d2` | todo | 79 | 68 | README+repo | Meta tooling | S | one real sam-3.1 segmentation in data/ai_cache, so the README sentence about SAM is a measurement |
| `t_fb09a735` | todo | 78 | 67 | README+repo | Meta tooling | S | the eye critic scoring four real frames on a Meta vision model |
| `t_10cad8d9` | ready | 40 | 65 | repo | Technical depth | S | one table of every shipped cue with its digest, duration and licence |
| `t_2c518ec8` | blocked | 85 | 64 | video | Demo | S | redraw the next sprite row to the palette rules: sprites are on screen, this is the one live copy of the three |
| `t_c31f9295` | blocked | 90 | 63 | repo | Technical depth | S | four audio sources untracked: the yyp and the build input gate are red in the repo a judge clones |
| `t_cdb3a6be` | blocked | 70 | 62 | repo | Technical depth | S | percy_theme_v3 and v4 uncommitted, the yyp names v3, three build input rows red |
| `t_41553cc5` | ready | 0 | 61 | repo | Technical depth | S | four red rows in the public repo come from two files that cannot be published: pick the fix |
| `t_4fca7154` | todo | 40 | 60 | repo | Technical depth | S | land the six R7 GPU lane paths so the work is in the tree a judge reads |

## 3. Under 50: paused, parked, or waiting on Nayil

The gate, audit and bookkeeping cards. None of them is visible in a video, a README or a repo, and
every one of them was still competing for dispatch time with the talk fight. The action column says
what was done: `pause` means the card was moved to blocked with the reason `after the submission`;
`park` means it was already blocked, so only its priority moved; `lower` means it is already blocked and
invisible but it protects a visible card, or it cannot move at all without Nayil.

Three cards in this band are deliberately not paused. `t_9d9b5b1d` (the GameMaker build step that can
only time out) stands between the tree and the public repo, so it keeps a working priority of 45.
`t_916a2382` and `t_73e40064` are decisions that need Nayil, so they are parked where they will not be
dispatched but will not be lost either.

Nothing is deleted. Every card keeps its body, its comments and its assignee.

| Card | Status | Was | Now | Visible in video, README or repo | Judging axis | Effort | What it is |
|---|---|---|---|---|---|---|---|
| `t_9d9b5b1d` | todo | 0 | 45 | repo (indirect) | Technical depth | M | the gate's GameMaker build step can only time out, so every push blocks for 900 s: it stands between the tree and the public repo |
| `t_ba694028` | blocked | 0 | 40 | repo (marginal) | Demo (marginal) | S | the ear sweep table is written; landing the artifacts and the Gemini quota need a decision |
| `t_916a2382` | blocked | 30 | 31 | no | none until decided | S (Nayil) | two spec numbers need Nayil (dialogue width, pattern angle); a spec number is not on screen |
| `t_73e40064` | blocked | 0 | 30 | no | Technical depth | S (Nayil) | the commit gate cap is 120 s against a 177 s suite, plus the cursor palette rule |
| `t_ddbc8cff` | blocked | 0 | 29 | no | none | M | the spec ledger has no FAIL word and two untracked specs: record keeping, nobody sees it |
| `t_a5e0d631` | blocked | 82 | 28 | repo (tests only) | Technical depth (weak) | M | the art tools do not reproduce their committed PNGs: a test row, not a frame |
| `t_3a932e73` | blocked | 95 | 27 | no | none (and Gemini, not Meta) | M | Gemini vision review of every captured frame: a private QA loop, and the wrong model for the Meta axis |
| `t_d2b724e3` | blocked | 88 | 26 | no | none | M | a captured run proving the gate choice branches: proof of a scene, not the scene |
| `t_52166d5a` | blocked | 0 | 25 | no | none | S | a negative control for the muted capture check |
| `t_2f4229ac` | running | 97 | 20 | no | none | M | backups commit and push on every sync: it protects the work, it shows nothing |
| `t_9d6c1f43` | ready | 50 | 14 | no | none | M | re-run the whole audit and classify every red: the audit is not in the video |
| `t_73295f13` | ready | 22 | 13 | no | none | S | read a captured run's ledger rows back: proof of bookkeeping |
| `t_1d9bc0a9` | todo | 95 | 12 | no | none | M | the commit gate should test the staged snapshot: dev velocity, invisible to a judge |
| `t_a183f183` | todo | 90 | 11 | no | none | L | a fast commit gate by test impact: dev velocity |
| `t_44c83b34` | todo | 88 | 10 | no | none | M | one attributed commit path through lane_commit.py: dev process |
| `t_c9316f7a` | todo | 84 | 9 | no | none | M | a commit sweep by lane: dev process |
| `t_ae018527` | todo | 75 | 8 | no | none | L | per lane worktrees and a merge queue: dev process |
| `t_1778cf9a` | todo | 70 | 7 | no | none | M | repo hygiene report and LFS assessment: a report about the repo, not the repo |
| `t_13e25e31` | blocked | 85 | 5 | video | Demo | S | a third copy of AUTO-SPRITE-NEXT; t_2c518ec8 is the live one |
| `t_bd32a72e` | blocked | 85 | 5 | video | Demo | S | a second copy of AUTO-SPRITE-NEXT; t_2c518ec8 is the live one |
| `t_c024f8bc` | blocked | 97 | 2 | repo (already landed) | none, no work left | S (close it) | superseded by ARRIVAL-MAP-2 (`t_db2995d7`, done): the 53 by 56 Town Quay map is in data/maps/all.json at line 133, so the only work left here is closing a stale duplicate |
| `t_00f5a63f` | blocked | 0 | 0 | README (reference) | Meta tooling (reference) | none | the Meta Model API facts the META cards are built on: a knowledge note, never dispatched |

## 4. The 64 open cards that are not this project

Listed here so the count is honest and so nobody re-derives it. They were not re-ranked and nothing was
done to them: Musikage and the composition engine, the job and PhD lanes, remote-client, the fleet audit
and routing cards, social and publishing, the Xbox worker, and the two protected `a protected profile` cards.

- `t_0bf15b8e` [knowledge] Keyless job-source APIs, the robots refusals, and the gate that actually binds the f: job source APIs
- `t_0d0c7175` PLAYLIST-NOW second screen fullscreen trap classical playlist: his second screen playlist
- `t_0e092241` Implement pull-worker SHA-256 job end-to-end and verify hashes: Xbox worker
- `t_1542ae22` [gap] leak_scan: a name ending in a bare _key matches no pattern, so any value under it passes (: leak_scan guard gap
- `t_1834f525` [knowledge] claim bank: hold a document to its own numbers, three verdicts, replacement in the r: claim bank method note (knowledge)
- `t_1a301b94` [handoff] social-media-monitoring: VIRAL-1 X launch kit for the Most Viral prize, drafts only: X launch kit
- `t_20d87e06` [brain-request] musician: composition engine ceiling, six voices, and a 14 piece Fox profile: Musikage engine ceiling
- `t_213f5306` [handoff] builder: lumen's only fallback hop is walled (opencode-go HTTP 403), C24 red until it : lumen fallback hop
- `t_23bc0784` [handoff] audit: the proof rule is unenforceable as written: proof rule audit
- `t_2bb65348` [handoff] builder: the offsite copy is frozen by three decisions, not by code: offsite backup decisions
- `t_2c1e3bd2` [handoff] audit: fleet audit is written, four decisions before the improvement loop starts: fleet audit decisions
- `t_3090b35c` [brain-request] musician: composition engine (MuPT) and the quality bar: Musikage composition engine
- `t_31c3404d` [handoff] builder: messaging outbox, the wiring route and the stranded temp messages: messaging outbox
- `t_32f624f5` [handoff] job-discovery: two minutes in Campus France would settle the CEA-LIST federated-learni: Campus France PhD
- `t_34349175` [handoff] builder: CMP3 LLM security review kit needs Nayil's final prices and go/no-go: CMP3 review kit
- `t_34847c0b` [handoff] social-media-monitoring: enable the YouTube Analytics API on Google Cloud project 4147: YouTube analytics API
- `t_372d9694` Measure throughput, constraints, and optional ONNX/DirectML: Xbox worker
- `t_3902f9fa` Deploy hello-world to console with Nayil and verify launch: Xbox worker
- `t_3a51d247` RC9 follow-up: a steer is accepted and injected but does not change the answer: RC9 follow up
- `t_40b7cf6f` [handoff] musician: decide the Kaggle fine-tune upload and the Deltarune source: Kaggle fine tune upload
- `t_440f7f4e` Prove USB NTFS read/write and measure staging throughput: Xbox worker
- `t_4accccf9` Confirm Xbox Dev Mode activation with Nayil: Xbox dev mode
- `t_4b09b4b9` [handoff] social-media-monitoring: two YouTube proposals need Nayil's wording (commission line, : YouTube proposal wording
- `t_54ff105f` [handoff] builder: Shared backup blocked by Nayil's manual acceptance for primordial-paradox: Shared backup acceptance
- `t_5cf30786` [knowledge] Structured pay in ATS feeds: a lone salary minimum is a truncated range, not a floor: ATS pay parsing
- `t_63b372d9` Android: wire turn, reasoning, steer, stop and warm into the phone app: Android app
- `t_6c1c29c5` [handoff] social-media-monitoring: Soundrop bundle needs credits, cover art and the licence deci: Soundrop bundle
- `t_6e46e6be` [handoff] builder: publish the ClipForge OAuth app (home page and privacy policy are built and r: ClipForge OAuth
- `t_71d3d8b7` [handoff] research-assistant: approve engineering standard wave 1 (2 decisions): engineering standard
- `t_72214b17` [knowledge] A scripted search page can return an empty result set that is not a real answer: search page behaviour
- `t_7323c1b2` Mobile app: seamless means numbers. Latency harness, warm chat, streamed reasoning, steering.: mobile app
- `t_742268cf` Plan: local draft website after the business name decision (gated): consulting website
- `t_7620c4af` [handoff] job-discovery: seven dated PhD calls lapse 30 Oct to 2 Nov while applications are park: PhD deadlines
- `t_79f8cebb` [handoff] code-review: thumbnail tool sign-off, trademark naming on published thumbnails and who: thumbnail tool
- `t_7ac24619` [handoff] social-media-monitoring: three licence decisions on the 711-record release schedule: release schedule licences
- `t_7d9d379d` [standing tracker] Apply-lane quality gate, do not run: apply lane tracker
- `t_88370f11` [handoff] job-discovery: the repo's two bot-check policy lines both authorize bypass, and one of: bot check policy
- `t_89d992da` [knowledge] Aalborg ref 2026/987 is closed and applied for; no AAU equivalent open (verified 202: AAU PhD (closed)
- `t_8a331401` RC9 follow-up: the first turn after a worker boot pays about 15 s of cold model connection: RC9 follow up
- `t_8bfcb864` [knowledge] How the closure gate matches a quote to a page: HTML tags become spaces, dev.meta.ai: closure gate mechanics
- `t_8ddd09d6` VIRAL-WATCH: what other entrants are posting and what the community vote rewards, a cited digest: viral watch research
- `t_968cce3b` [handoff] research-assistant: AEGIS DC13 packet needs three decisions before 31 Oct: AEGIS PhD packet
- `t_968e6b6f` [knowledge] Text-to-CAD and Text-to-PCB in 2026: the open problem is verification, not generatio: text to CAD
- `t_9a749515` Nightly suite runner (standing, never dispatchable): nightly suite runner tracker
- `t_a8cf24a0` Dating DG1: first daily digest with three drafts per item (drafts only): a protected profile dating (protected, untouched)
- `t_abf4740f` [handoff] research-assistant: Pine Computer, key variable name and persisted versus ephemeral: Pine Computer SDK
- `t_ac15d469` Resume and CV: finish the 2026-10-14 resume work, fix errors, build PDFs (no submissions): resume and CV
- `t_b0a237b0` CIT-SECRETS set an API key from the phone, no agent sees it: Citadel secrets
- `t_b3cd0758` [handoff] code-review: who applies the witness-authz rework, a protected profile is protected: remote-client witness authz
- `t_bdab2ba5` [handoff] social-media-monitoring: pick the account, the Discord and the signing name for the ni: devlog drafts (outward)
- `t_c15144f5` [handoff] builder: C15 red, a protected profile config.yaml drifted from its blessed manifest (Nayil: a protected profile config (protected, untouched)
- `t_c31a9894` Audit stream: independent verification of fleet claims: audit stream tracker
- `t_c6ed6a1c` [handoff] musician: rotate GEMINI, PINE and KAGGLE keys printed by a reg query: key rotation
- `t_d3472271` [handoff] audit: a lane's shared-index commit silently reverted another lane's committed work (0: shared index revert audit
- `t_d92b476c` [knowledge] AAU 2026/987 (Copenhagen, secure/privacy-preserving collaborative LMs) is closed; pa: AAU PhD (closed)
- `t_dadec492` [brain-request] musician: CV1 style judgment calls (melody length, composed P2, noise figure): Musikage CV1 style
- `t_df487670` Deliver the five proactive jobs to Nayil's email (self-addressed only): proactive email delivery
- `t_e70ddb80` [handoff] audit: sign or waive the RC7 acceptance record, which is holding the fleet backup 71 c: RC7 acceptance record
- `t_e86d59d4` [handoff] musician: four generated pieces need your ear (composition engine): Musikage ear pass
- `t_e8821b0b` [brain-request] musician: SBR original credit (Kanno vs Iruma Jazz) and the lyricist field: Musikage credit decision
- `t_fc4ffda7` [handoff] audit: the fleet left the documented route because opencode-go ran out of credits, 982: fleet credits
- `t_fd0c5401` [handoff] musician: FLP reader needs one on-screen check in FL Studio: Musikage FLP reader
- `t_fd9b9219` [spike] Xbox Series S UWP worker: prove the pull-worker loop and measure throughput: Xbox worker
- `t_fdbdb18f` [knowledge] WA trade names are $5 and plural; the LLC already exists; Nayilinist domains are fre: business name facts

## 5. Opened after this ranking was drafted, listed but not ranked

The board was being written to while this page was built. These cards exist and are open, and they
carry the priority their author gave them. The next reader of this page should rank them by the same
rule: video, then README, then repo.

- `t_4c8e4181` W0b APPLY WIN-PRIORITIES: 65 priorities and 8 pauses, from the committed table (needs a profile that may mutate the board)

## 6. What this changes for the next four days

1. Dispatch order is now the order of the table. The two cards that can move the demo score most, W1 and
   W2, hold 97 and 96 and nothing invisible can be picked ahead of them.
2. The music rulings (83, 82, 81, 80, 79, 78) are six mostly one line decisions that free
   `t_6d66f32d` at 77. They are the cheapest visible wins on the board.
3. The repo cards (89 to 60) are what a judge who does not watch the video will read. They are ranked
   under the video on purpose: the video is 25 points and the repo supports Impact and Technical depth.
4. The eight `pause` cards cannot come back before 2026-11-04 unless someone edits this page.

---

## 7. How this gets applied, and why the page carries the numbers

`hermes kanban edit --priority` refuses a board mutation from inside a worker run, and so does the
`kanban_block` tool (both answer that a worker is scoped to its own card). The sanctioned route out is a
comment, which does not change a priority. So this page carries every number in a form that can be
applied mechanically instead of retyped: `knowledge/WIN-PRIORITIES-APPLY.md` holds one exact command per
card, generated from the same table, and the manager card linked from `t_29dcf655` runs them.

    python tools/apply_win_priorities.py --check     # if the follow-up card lands a script
    hermes kanban edit <id> --priority <n>           # the 65 priority rows below
    hermes kanban block <id> "after the submission"  # the 8 paused cards

Written by gamedev on node CitadelArana, 2026-10-26.
