# CI-COST-DISCIPLINE 2026-10-29: a fake Meta door, a gate that measures it, and the PRECOG red it cannot fix

Card t_fc0cb4d9. The card asks for the CI to run against a fake Meta API so it never spends credits, never
hits a rate limit and never logs a player's text, and for the LrBronJames cost harness to be adopted. Its
check is two lines: CI green against fake Meta, and a PRECOG forecast with no red before demo day. The first
line is met and measured below. The second is not met, and the numbers say so.

## 1. What was missing, stated precisely

`tools/meta_client.py` already refuses a live call without a key, and `tests/test_meta_client.py` already
drives it on a `FakeTransport`, which is the right seam for request shapes. What no test covered is the door
itself: `UrllibTransport.post`, the `Authorization` header, the timeout, the rate gate, the 429 and 5xx retry
policy, and the response decoding. A live call would cover it and costs credits, which is exactly what CI
must not do. So the missing piece was a server, not another mock.

## 2. `tools/fake_meta.py`: the door, on loopback, for nothing

Four routes, the four `_live_call()` uses: `POST /v1/chat/completions`, `/v1/images/generations`,
`/v1/images/edits`, `/v1/responses` (segment and transcribe, told apart by the `metadata` block's own keys:
`audio_format` is a transcription, `mask_encoding` is a segmentation). Answers are deterministic in the
request body, so a rerun of the same call returns the same bytes.

Three refusals, none of them a skip:

| refusal | what it stops |
| --- | --- |
| not loopback, not started | `FakeMeta(("0.0.0.0", 0))` raises before a socket exists, so a harness cannot publish a fake API |
| model not pinned, 400 | only the ids `meta_client.DEFAULT_MODELS` pins are answered (muse-spark-1.3 chat and vision, muse-image-1.0 image and edit, sam-3.1 segment, muse-voice-transcribe-1.0 transcribe); "spark-1.3 only" is enforced on the wire |
| no answer echoes the prompt | an answer carries the request's sha256 and length, never the request text |

The record it keeps per request has ten fields and none of them can hold a body: when, route, kind, model,
status, `body_sha256`, `body_bytes`, fake `prompt_tokens`, fake `output_tokens`, `answer_b64_chars`. The fake
token counts are arithmetic over the request with inline data URLs replaced by their size, so a fake image
call is not priced at the base64's length. Every priced figure out of it is labelled `would_have_cost_usd`,
because this server spent nothing and cannot: no key, no account, no route off the host.

Measured, `python tools\fake_meta.py --selftest` at 2026-10-29 18:5x on the live tree:

    FAKE META: 5 request(s), 0 refused, spent 0.000000 USD, would-have-cost 0.013023 USD
    models answered: muse-image-1.0, muse-spark-1.3, muse-voice-transcribe-1.0, sam-3.1
    kinds answered: chat, image, segment, transcribe

## 3. `tools/ci_cost_gate.py`: the gate, seven checks, and what each one fails on

`python tools\ci_cost_gate.py --report <path>` starts the fake, points the real client at it in live mode
with a fake key, arms a socket audit hook, drives the five kinds, then runs the Meta-consuming test files
with no Meta key in the environment at all. Measured 2026-10-29 on the live tree:

    FAKE UP          PASS  GET /health at http://127.0.0.1:56388 answered ['muse-image-1.0', 'muse-spark-1.3', 'muse-voice-transcribe-1.0', 'sam-3.1']
    FIVE KINDS       PASS  answered: chat, image, segment, transcribe, vision
    PINNED ONLY      PASS  refused as asked: MODEL_API_KEY answered 400: {"error": {"message": "model 'muse-spark-0.9' is not pinned fo
    NO EGRESS        PASS  audit hook saw 0 non-loopback attempt(s)
    NO PLAYER TEXT   PASS  absent from the fake's record, the cache, the ledger and this report
    SUITE GREEN      PASS  -m pytest -q --no-header -p no:cacheprovider tests/test_fake_meta_ci.py tests/test_meta_client.py tests/test_ai_client.py tests/test_ai_bridge.py tests/test_bake_meta.py in 80.5s, exit 0, network-true cache entries 279 -> 279
    COST             PASS  spent 0.000000 USD on 5 call(s); the same calls would have cost 0.013052 USD at list price
    CI COST GATE: PASS (all 7 checks)

Four things about that table matter more than the PASS column.

- `NO EGRESS` is not a promise. The hook is armed for the whole driving phase and raises `Egress` on any
  `socket.connect`, `socket.sendto` or `socket.getaddrinfo` aimed anywhere but loopback, so a call that
  slipped past the fake base URL fails the gate instead of spending credits. A test in
  `tests/test_fake_meta_ci.py` measures the hook itself in a child process, so the suite never runs with a
  hook armed by a passing test.
- `NO PLAYER TEXT` sends one sentinel line (`SENTINEL-PLAYER-LINE-7f3a ...`) on a chat call and a vision
  call, then searches the fake's record, the cache directory, the ledger and the gate's own report for it.
  One hit fails the gate. The bridge cache already stores `player_sha256` and `player_chars` rather than the
  line (`tools/ai_bridge.py` Cache.write), so this row measures the new surface, not a promise.
- `SUITE GREEN` runs with `META_API_BASE`, `MODEL_API_KEY`, `META_API_KEY` and the `PP_AI_*` knobs removed
  from the child environment: a test that tried a live call would refuse at `api_key()` instead of spending,
  and a test that asserts the documented default base URL still sees the documented default. The cache is
  compared before and after (279 -> 279 entries claiming `network: true`), so the run is also evidence that
  no live entry was written.
- The gate runs the five files that consume Meta (`test_fake_meta_ci`, `test_meta_client`, `test_ai_client`,
  `test_ai_bridge`, `test_bake_meta`), not the whole suite. The whole suite would be a different claim and a
  much slower one; the nightly is where that lives.

## 4. The nightly wiring, and the one thing it deliberately does not do

`tests/test_fake_meta_ci.py` is collected by the ordinary suite, so the nightly picks up: the loopback-bind
refusal, five kinds through the real client with a measured spend of 0.000000 USD, the unpinned-model
refusal, the no-echo check, the egress hook in a child process, and `tools/ci_cost_gate.py --skip-suite`
exiting 0. Measured: `6 passed in 5.23s`.

It runs the gate with `--skip-suite` on purpose. A test that ran the gate's own pytest selection would be
pytest inside pytest, and would double the nightly's Meta-file cost for no new evidence: the selection is
already being collected by the suite that is running.

## 5. The LrBronJames cost harness: adopted, measured, and where it sits

The card names the harness by the team that posted it. The post is in the manager's own Discord capture, so
it did not have to be guessed: `manager\demiurge\intel\discord-build-for-your-world-2026-10-27-part-3.md`
line 7, [4:11 PM] LrBronJames: "a cost harness for agents on Muse ... runs as a local server in front of the
API, shows where your tokens go, and cuts what it can without breaking the prompt cache ... saves around 21$
per 100$", with the link `https://github.com/IrwinJam/agent-cost-harness`. The repo is public and MIT
licensed, so it was cloned and run here rather than described from a quote.

What it is: a Python 3.11+ package (`pip install -e ".[dev]"`, deps `httpx` and `pyyaml`) whose
`python -m harness serve` is an OpenAI-compatible server on 127.0.0.1 in front of a provider, with three
cost policies (`cache_layout`, `output_handles`, `masking`) and a local SQLite call log. Its own README
claims, on 40 customer-service tasks and 400 runs: -21% from `cache_layout`, -37% with low reasoning, cache
hit rate 84% to 94%, and two Muse API facts it treats as the causes (a missing shared `prompt_cache_key`
costs about 16% of input; each reasoning effort level has its own cache, so switching effort re-pays the
conversation). **Those percentages are its numbers, not ours:** they come from a benchmark we did not run,
and they are unverified here.

Three things were measured on this host, on 2026-10-29.

1. **It runs offline on this host, no key.** `PYTHONPATH=. python examples/simulate.py --clock` printed its
   own banner `SIMULATION ONLY` and the arm table: baseline 0.6431 USD, `cache` 0.1322 (-79%), `cache+handles`
   0.0455 (-93%), `cache+handles+mask` 0.0479, `naive-masking` 0.2294. Those are simulation numbers and they
   do not reproduce the README's -21%: the `--clock` scenario breaks the cache on every baseline call, which
   is the worst case rather than the benchmark's average. Read them as "the harness runs and its policies
   move cost in the expected direction", not as a saving.
2. **Our client drives it with no code change.** `python -m harness serve --simulate --port 8791` serves the
   same shapes from its fake provider, and `tools\meta_client.py` with `META_API_BASE=http://127.0.0.1:8791/s/probe-1/v1`
   answered `'simulated reply'` on a plain chat call. So the adoption seam is one environment variable,
   `META_API_BASE`, which the client already honours; nothing in this repository has to change to put the
   harness in front of the real API.
3. **Its cost log comes back on the same call.** `python -m harness spend --db <sqlite>` read back
   `total: $0.0007`, `most expensive conversations: $0.0007  1 calls  serve/probe-1`. Its token accounting
   survives the round trip through our client.

What adoption deliberately does not mean here: **CI does not depend on it.** The gate in section 3 uses our
own fake, so a nightly needs no clone, no pip install and no third-party code in the path of a commit. The
harness is a dev-side and demo-side proxy: point `META_API_BASE` at it when a billed run is being measured,
and its cache policy is the thing to try first because it is the one its own benchmark shows moving cost
without changing answers.

**UNVERIFIED:** the -21% and -37% figures, and whether its policies help this game's prompt shapes (one
system prompt and a short conversation per TALK line, where the 16% shared-key effect may be smaller than on
a 12,000-character tool-output agent).

## 6. PRECOG: the second check, and it is red

`python tools\precog.py` in `manager\` at 2026-10-29 18:43 wrote `manager\precog.json` and printed:

    precog: 2 alarm(s), 1 inbox line(s); disk 11.3 GB, RAM 1.6 GB, commit 24.3 GB, credit cycle 222.2 min

The two alarms, from the same file:

| resource | level | the forecast's own words |
| --- | --- | --- |
| disk C: free | below | 11.29 GB, at or below its 15.00 GB floor now (slope -0.082 GB/min over 256 samples) |
| OpenCode Go credits | crossing | next credit outage projected in 43 min: a 222 min cycle from 15:44, at 12.0 runs/h against 210.1 runs/h over the day |

So the card's second check, "PRECOG forecast no red before demo day", **does not hold today**: one resource
is already below its floor and the other is projected across its floor inside the alarm horizon. Neither is
a testing change: disk is the keepalive's `diskd` move plus Nayil's call, and credits are a top-up or a
throttle, both out of this lane and both named in the PRECOG inbox line as `needs Nayil`. Reporting it here
is the honest half of the check; pretending the row is green would be the other half failing.

## 7. What this page does not claim

- It does not claim the whole suite was run against the fake. Five Meta-consuming files were, 80.5 s, exit 0.
- It does not claim a rate limit cannot happen on a real call. The fake answers 200 and one 400; the 429 path
  is measured by `tests/test_meta_client.py` on a fake transport, not here.
- It does not claim the LrBronJames harness was vendored or made a CI dependency, and it does not claim its
  -21% and -37% figures: those are its benchmark's, run by its author, unverified here. What was measured is
  that it runs offline on this host and that our client reaches it through `META_API_BASE`.
- It does not claim the credits or disk alarms are solved, or that the demo-day forecast is safe.
- The fake's token counts are arithmetic over the request, not a model's usage; every USD figure derived
  from them is a counterfactual, and the real bill is Meta's.
