# PRODUCTION-PLAN: the production half of the game director's research (GD-1b)

Written by assistant, 2026-10-26, card `t_2f3a695c`, node CitadelArana. This is sections 4, 5 and 6 of
`Shared\projects\arananet\manager\cards\game-1026\GD-1.md`. The design half (sections 1 to 3) is card `t_1034799a`
and its output is `DIRECTOR-PLAYBOOK.md`. Sources are numbered [n] and listed in `knowledge\SOURCES.md`; every claim
carries its number, and anything that is our own decision is marked as such.

Scope: this file only. It publishes nothing, submits nothing, and changes no game file. The deadline that frames every
date below is the Meta Global AI Developer Hackathon submission, Wednesday 4 November 2026, 9 PM ET
(`..\arananet\meta-hackathon\SUBMISSION-CHECKLIST.md` section 0).

---

## 4. Production stages, exit tests, vertical slice first, scope and triage

### 4.1 The eight stages, and what each must prove before the next

The classic ladder is concept, pre-production, vertical slice, production, alpha, beta, polish, launch. The point of
naming the stages is not the words but the exit test: each stage must prove one thing in a binary way before the next
one may start, because a milestone that cannot be answered with a yes or a no is not a milestone [3].

| Stage | What it must prove | Exit test (binary) |
| --- | --- | --- |
| Concept | The idea is worth making | The core loop answers "is this fun" in a disposable prototype, not a document |
| Pre-production | The team can build it at final quality | A vertical slice, one small piece finished through every discipline [1] |
| Vertical slice | Quality and pipelines are real, not imagined | A playable, near-final section a stranger can run unaided [1] |
| Production | The features exist | Alpha: every system implemented, testable, not yet content complete or polished [3] |
| Alpha | The game is testable end to end | Every system code complete, QA ramping up, bug count expected to spike [3] |
| Beta | The game is complete | Content complete: every level, enemy, cue and credits in, game finishable [3] |
| Polish | The game is good enough to ship | Bug bar met, performance held, the known-issue list is locked and triaged [4] |
| Launch | The game is released | Gold: certified or submitted, with a day one patch already queued [3] |

Two rules from the sources hold the ladder together. First, write an exit criteria document per milestone with binary
conditions ("all P1 and P2 bugs closed", "the game plays start to finish"), not "the game feels fun" [3]. Second, agree
in writing what each milestone word means before work starts; an undefined "vertical slice" absorbs months of polish
and traps a team in "demo hell" of repeated feedback rounds [1].

### 4.2 Vertical slice first, and why it is the right first target for a jam

The vertical slice is a production proof: one thin piece of the game finished through every discipline, design, code,
art, animation, audio, UI and QA, so whoever is paying can judge final quality before funding the rest [1]. A
prototype answers "should we make this", a vertical slice answers "can we" [1]. Volition treats the slice, or proof of
concept, or minimum viable product, as the tool to decide whether the team should go forward at all [2].

For a hackathon the slice is the whole game. Three of its properties matter more than the others:

1. It is deep, not wide. One loop done properly beats five loops done roughly, and a slice that adds breadth without
   helping a judge judge quality wastes budget [1].
2. It surfaces pipeline, performance, control and art direction problems early, while they are still cheap, because it
   cuts through every layer for one piece of content [1].
3. It must be a real build on the target platform, not an editor screenshot: a build that runs, at target frame rate,
   with no crash in a full session [1].

What to leave out of a slice, per the same source: extra levels and modes, secondary systems (achievements, cloud
saves, full localisation), full monetization, and one off hacks that only work for the one level and flatter the slice
[1].

### 4.3 Milestone and greenlight reviews

A greenlight review is the decision gate at the end of pre-production (and again at later milestones): the team shows a
playable slice, not slideware, and the funder or the board decides whether to release the next tranche of money or
time [1][3]. The discipline that makes it work is the exit criteria document: if a publisher pushes back, the two sides
are comparing a checklist, not opinions [3]. A jam compresses the same gate into one person, Nayil, applying the same
binary checklist on a fixed date.

### 4.4 Playtesting cadence

The cadence of playtests should follow how often the team has a decision that needs playtest data to answer, not a
fixed ritual [10]. For a small team that means: early and often on the core loop, once a week once the loop is stable,
and a full external pass only when a stranger must be able to finish the game unaided. A slice with a choice that
cannot be failed is a legitimate playtest finding made into design, which is the point: playtests answer questions,
they do not produce a score.

### 4.5 Scope cutting

Scope cutting is a plan, not a panic. The jam postmortem that scoped down successfully did three things in order:
grounded the initial scope in what each department could actually do, caught the shortfall early, then cut to the work
that was already close to done and built backstops for the rest so a dropped feature could not break the product [5].
The lesson is that a cut list written before the deadline is cheap; a cut made under pressure on the last night is
where games lose their one good idea. Our cut list, written now, is section 6.4.

### 4.6 Bug triage

Triage answers four questions and nothing else: does it reproduce, how severe, how urgent, who owns it. It is not
fixing, and it is not a democracy; one accountable owner, usually QA or a producer, decides, and everyone else supplies
information, not votes [4]. Severity (how bad) and priority (how soon) are separate: a rare crash in an obscure menu
is high severity and low priority, a title screen typo is low severity and high priority [4]. The rhythm is daily
intake plus a weekly reprioritisation, and the filing standard, mandatory repro steps, a severity tag, and "screenshot
or video or it did not happen", does more than the tool choice [4]. For a nine day jam the same rule shrinks to: one
list, re-ranked daily, and a bug bar per stage decided in advance, so ship decisions are applying a rule, not
negotiating one [4].

---

## 5. Directing the team, and where AI agents fit

### 5.1 The director's job versus the producer, the leads and the art director

The clean split is: the game director owns what the game is and why; the producer owns how it gets made; the lead owns
a discipline's day to day execution; the art director owns the visual target [6]. The producer's three objects are
scope, schedule and capacity, and the producer finds risk before the gate, not at it [6]. A director who must be in
every decision is a bottleneck; a director too abstract to give concrete guidance produces drift [6]. The lead
translates quality targets into specific technical requirements and protects the team from counter productive work [6].
The art director owns the style guide and the quality standard; a lead artist and art director who both think they own
visual approval revise assets in circles [6].

For a one person game run by lanes, Nayil is the director (taste and the final call), the manager profile is the
producer (scope, schedule, capacity, the board), gamedev is the lead designer and lead on the engine, builder is the
lead on code and art execution, musician the lead on sound, testing the QA lead, and the art direction is a written
bible checked by a tool rather than argued in a meeting.

### 5.2 Design pillars

Pillars are the three to five core elements and emotions the game is trying to make the player feel, and they exist to
keep the game coherent and to let every teammate make the same design decision: the test is "does this mechanic or
idea serve a pillar", and if the answer is no, it is removed [11]. Our pillars are already written as the NES hardware
limit and the checker that says no, which is a taste decision Nayil made and this file does not reopen (see section
6.6).

### 5.3 Writing a task a junior can finish

A director writes a task a junior, or a lane, can finish, not a task a senior would have to rescue. The shape is: one
file and one check, a binary exit test, and the context the worker cannot see. This is already the house style: every
card in `CARD-MAP.md` carries a card, a lane, a file scope and a FOX-STYLE parent, and a card with no parent is a bug.
A task with no binary exit test is a research wish, not a task, and belongs in a document, not on the board.

### 5.4 Review and taste

Review applies the pillars and the exit criteria, not the reviewer's mood. Taste is applied where it is cheap to apply
and expensive to get wrong: art style, the title theme, the final lines of text. Those are Nayil's, in every source,
because they are the identity of the game and no model or lane owns them. Section 6.6 lists them.

### 5.5 Which tasks cheap models do well, and which need a strong model or a human

The working 2026 consensus across studios that actually ship: AI is a velocity multiplier on the direction already
chosen, and it lowers the cost of producing something, not the cost of producing something good [8]. Routine, well
scoped, verifiable work is where a cheap model earns its keep: performance fixes on a named area, bug diagnosis from a
save file plus a text state log, proposing QA scenarios, reviewing a design doc diff against written rules, building
isolated modules and automations [7]. A text representation of game state, logs and replays is what makes any of this
work [7].

What needs a strong model or a human: anything needing taste or whole game context, level design, gameplay feel,
narrative coherence [8]. The honest rule the same source states is to point agents at well scoped, verifiable tasks (a
function, a batch job, a test pass) and keep a human reviewing every diff, because an agent that edits twenty files
unsupervised is a liability, not a teammate [8]. Althera's own numbers: a 38 percent time cut on routine systems, about
12 percent on systems the engineer had never built, because the human still had to read the output critically [8].

### 5.6 Where agents fail in games: taste, feel, consistency

The failure is structural, not prompt depth. Luden.io could not get agents to plan, implement, test and polish a whole
gameplay feature: a programmer makes many small design decisions while writing code and understands the intended
experience and the dangerous shortcuts, and the agent, even with a detailed plan, an answer loop and a critic agent,
still could not be trusted to know whether the result was good [7]. Autonomous end to end playtesting failed the same
way twice, screenshot analysis was too slow and unstable, and a text input agent clicked objects players could not see
[7]. Taste, feel and consistency are the same three things Althera names as the 2026 failure boundary [8].

Two more measured failures matter for a team of lanes. Stanford's CooperBench found that two coding agents collaborating
perform worse than one alone, losing nearly half their capability in the coordination gap, and that giving them a chat
channel did not help because their language fluency masked failures rather than resolved them [9]. A large scale
analysis of 20,574 real coding agent sessions found 90.5 percent of episodes imposed effort and trust costs, and 91.49
percent of visible resolutions required explicit user correction [12]. The conclusion for us: one lane owns one file
with one binary exit test, and no two lanes answer the same question, because coordination is where agents lose the
work, not in the code.

### 5.7 How studios structure AI agent use

The studios that make it work use AI in narrow, boring places, not end to end: code assistants in the editor, concept
art as the first ten percent that a human then paints over, voice and music as placeholders that let the team iterate
the script before paying a human, and an agent that reviews the design doc diff like a code review [7][8]. Every one of
them keeps a human in the loop on the direction and reviews every change, and the ones that lose money are the ones
that tried to replace senior decisions rather than use AI for plumbing [8].

---

## 6. Our team as it is, the plan to 4 November, the cut list, and the RACI

### 6.1 The lanes, by their new names

From `Shared\projects\arananet\manager\BOT-NAMES.md` (Nayil, 2026-10-26): assistant = Aaliyah; builder = Mei;
musician = Lyra; research-assistant = Priya; gamedev = Sakura; testing = Leilani; code-review = Valentina;
social-media-monitoring = Zara; job-discovery = Sofia; healthcare = Amara; a protected profile = Demiurge (label only, the
profile is untouched). Off the picker: audit = Imani; security-organization-audit = Nadia; lumen = Luna;
default = Athena (the manager).

The lanes that do game work, and their production role here:

| Lane (name) | Production role |
| --- | --- |
| gamedev (Sakura) | Lead designer and engine lead; owns the specs, the rooms, the doctrine (`FOX-STYLE.md`) |
| builder (Mei) | Code and art execution lead; concept art, sprites, maps, the pixeliser and the gates |
| musician (Lyra) | Sound lead; the chip engine, the cues, the title theme |
| testing (Leilani) | QA lead; the gates, the tests, the demo recorder and the capture |
| research-assistant (Priya) | Rules and reference; the rules watch, the drive shot list, the quay research |
| code-review (Valentina) | Review; the spec and data reviews before a card closes |
| audit (Imani) | Readiness and the card map; the maturity table and the night audit |
| security-organization-audit (Nadia) | Key hygiene and what the repo may hold |
| assistant (Aaliyah) | Submission assembly; the README, the write up, the scripts, this plan |
| default (Athena, the manager) | Producer; scope, schedule, capacity, the board |

### 6.2 The nodes

| Node | What it is | What it does for the game |
| --- | --- | --- |
| This PC (CitadelArana) | RTX 4060 8 GB, GameMaker LTS 2026, local models (LM Studio) | Builds and runs the game, the pixeliser, the capture and ffmpeg, the local model fallback |
| Kaggle GPU | `kaggle_run.py` in `arananet\compute-2026-10-20\kaggle-runner` | The concept art foundry: muse-image and sam-3.1 generation, quantization, the batch queues |
| Pine sandboxes | `pine_offload.py`, PINE_SANDBOX_API_KEY at user scope | Offloads the test suite (1553 passed, 1 failed on 2026-10-26) and the audits |
| Gemini (vision critic) | `tools\eye_critic.py` behind GEMINI_API_KEY | The eye critic: scores a drawn frame against the art bible; a 20 call a day cap applies |
| Meta models | muse-image-1.0, sam-3.1, muse-spark-1.3 | Concept art, silhouette and mask, and the baked TALK replies; billing pending |

Capability note, read from `manager\CAPABILITIES.md` (2026-10-25): every lane has screen capture, browser, Pine, Kaggle,
GameMaker and Android, and no lane has desktop input or messaging in a dispatched run. So the work that needs a hand at
the keyboard, the live capture, the submit click, is Nayil's or a scheduled quiet window, not a lane's.

### 6.3 The stages from today to 4 November, with real dates and exit tests

Today is Monday 26 October 2026. The submission is Wednesday 4 November, 9 PM ET. The scaffold exists (title, crawl,
drive, ship, save; 22 row readiness table at mean 2.4545, no row at 4). The window is for turning the rows at 2 into
rows at 3 and closing the slice, not for adding a feature.

| Stage | Dates | What it does | Exit test (binary, run on this PC) |
| --- | --- | --- | --- |
| A. Kickoff and route | Mon Oct 26 | The slice route is the contract: nine steps, title to game over | `python -m pytest tests/test_slice_route.py -q` green, and the demo holds the drive step with `PP_ROUTE_HOLD=drive` |
| B. Vertical slice complete | Tue Oct 27 to Wed Oct 28 | S3 to S6 rooms land: gate, boarding, first fight, talk fight, save, defeat; the first fight capture goes green; the 12 drive stills come inside the palette | `output\first_fight_verify.json` is `ok: true`; all 12 `output\drive_frames\*.png` inside the palette; a scripted run reaches all nine steps with footsteps |
| C. Alpha, all features in | Thu Oct 29 | Every slice system exists and the gate set is green: the 35 NES audit failures close or are triaged, the scene palette report regenerates, the game over preview is legal | `python tools\check_data.py` and `check_cleanroom.py` exit 0, `python tools\nes_audit_all.py` exits 0, the Pine suite is green |
| D. Beta, content complete | Fri Oct 30 to Sat Oct 31 | The game is finishable end to end: audio cues per scene, SFX, the known bug list locked and triaged | The alpha build plays S1 to S6 with audio and no placeholder, and the bug list has every open item classified fix required, fix if time, or ship with disclosure |
| E. Final capture | Sun Nov 1 | One judged recording of the real build | `python tools\play_demo.py` then `--check` pass, and the nightly verify reports every beat, footsteps, the fight, the save and the defeat |
| F. Video and submission assets | Mon Nov 2 | The 90 second and 3 minute cuts, the write up, the README, the architecture diagram, the licence | The 3 minute cut renders with narration; the README states the true state; the diagram names real modules |
| G. Submission dry run | Tue Nov 3 | Every checklist item 1 to 10 answered or passed | `SUBMISSION-CHECKLIST.md` has no NOT DONE line that a lane can close |
| H. Buffer and submit | Wed Nov 4, by 9 PM ET | Nothing new; the submit click | Nayil submits |

### 6.4 The cut list, if late

Ordered, cut from the top down and stop as soon as the deadline is held. Written now, not on the night.

1. Cut the 3 minute narration to the 90 second silent cut (the six captions stay).
2. Cut the defeat beat: S6 ends on the save, CONTINUE is dropped.
3. Cut the office and boarding pass beat (S5) to a held drive frame with the caption removed.
4. Cut the gate beat (S4) to a held crawl frame with the caption removed.
5. Cut the drive shot (S3) to the 4.0 second night drive already in the recording.
6. Final fallback: title and crawl only (S1 and S2), which is still over the 30 seconds item 1 requires.

What must never be cut, because it is the thesis: the NES frame at a true 3x, the checker that can fail and publishes
its own failures, and the statement that the build holds no key and makes no call. These are the Impact, technical
depth and Meta tooling scores, and cutting them cuts the reason the game exists.

### 6.5 The RACI: every recurring kind of work against lane, model and node

R = responsible, A = accountable, C = consulted, I = informed. Models by cost, per the brief: deepseek-v4.1-flash is
the cheap default; kimi-k3.1-pro is for writing and taste; a vision critic is for art. Nodes from section 6.2.

| Work | R (lane) | A | C | I | Model | Node |
| --- | --- | --- | --- | --- | --- | --- |
| Code: GML, tools, tests | builder | gamedev | code-review, testing | manager | deepseek-v4.1-flash | this PC, Pine for the suite |
| Levels, maps, rooms | gamedev | gamedev | builder, research-assistant | testing | deepseek-v4.1-flash | this PC |
| Writing: crawl, captions, narration | assistant | Nayil | gamedev, research-assistant | manager | kimi-k3.1-pro | this PC |
| Writing: baked NPC and TALK lines | builder (routes the calls) | gamedev | code-review | testing | muse-spark-1.3 (Meta), checker decides | this PC, Meta |
| Art: concept, sprites, backgrounds, palette | builder | gamedev | Gemini eye critic, audit | Nayil | vision critic (Gemini + muse-spark) | Kaggle GPU, this PC pixeliser, Pine audit |
| Music | musician | Nayil | ear critic (spectrogram vision) | gamedev | deepseek-v4.1-flash + ear critic | this PC |
| Sound and SFX | musician, builder | gamedev | testing | manager | deepseek-v4.1-flash | this PC |
| QA: gates, tests, readiness | testing | gamedev | audit, code-review | manager | deepseek-v4.1-flash | Pine, this PC |
| Capture and video | testing | assistant | gamedev | Nayil | deepseek-v4.1-flash | this PC (ffmpeg) |
| Submission: write up, README, repo, diagram | assistant | Nayil | gamedev, research-assistant | manager | kimi-k3.1-pro | this PC |

### 6.6 Nayil's taste only decisions

These are his, and no lane or model answers them. The list is the brief's, with the one outward boundary added:

1. Art style: the final look, the palette direction, any frame a judge will see as "the game".
2. The title theme: whether the music is the identity he wants.
3. The final lines: the last wording of the crawl, the captions, the narration, and any NPC line that defines a
   character.
4. What ships: the submit click, the public repo URL, the licence, and every outward action. Nothing outward is a
   lane's to take without his yes on that exact action.

---

## 7. Verification

| Check | Result |
| --- | --- |
| Distinct sources cited | 12, numbered [1] to [12], all listed with link and date in `knowledge\SOURCES.md` |
| Sources dated 2024 or later | 10 of 12 (all except [5] 2023-07-27 and [11] 2017-10-12) |
| Dash characters | scanned after writing; U+2012, U+2013, U+2014, U+2015 all count 0 |
| Dates | every stage date is a real calendar date, 26 Oct to 4 Nov 2026, checked against `date` on this PC |
| Own decisions | marked as such; every other claim carries a source number |

Written by assistant, 2026-10-26, node CitadelArana. Nothing in this file was published, uploaded or submitted.
