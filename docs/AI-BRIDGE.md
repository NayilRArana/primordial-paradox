# The talk bridge, and what it measured

Card W1 PP-BRIDGE, written 2026-10-26 by the builder lane. This document is for a judge reading the repo and
for whoever runs the demo: what `tools/ai_bridge.py` is, how to start it, what it was measured at, and what is
still not proven.

Short version: the game can ask a local service for an in character verdict on what the player said, and gets
one back labelled with the rung that answered. On this PC, with the machine otherwise idle, the open weights
model answered in 1.8 to 1.9 seconds. With the rest of the fleet using every core, it answered in 5 to 62
seconds, which is past the budget, and the recorded answer then came back in 2 to 94 milliseconds instead. Both
of those are the design working, and the second one is why the demo runs on the recorded path.

## What it is

`tools/ai_bridge.py` is one small HTTP server, Python standard library only, bound to `127.0.0.1`. It is started
by `tools/run.ps1` before the game and stopped after the game window closes, so it is not a daemon and nothing
survives a play session.

    POST /talk    {"encounter_id": "tutorial_sailors", "npc": "navy_sailor", "player_text": "...",
                   "history": [...], "will": 20, "mood": "guarded"}
                  -> {"verdict": "persuaded", "will_delta": 20, "reply": ["GO ON THEN."],
                      "source": "open-weights", "mood": "warm", "latency_ms": 1801, ...}

    POST /hear    raw 16000 Hz mono 16 bit wav bytes
                  -> {"transcript": "you have been standing on watch all night, sailor"}

    GET  /health  what every rung is doing, without spending a call: the judge file's version, whether a Meta
                  key is present, which local model is named, whether the whisper worker is up.

`verdict` is one of `persuaded`, `unmoved`, `angered`; `will_delta` is the WILL bar movement those three map to,
and the mapping lives in `data/talk/sailor_judge.json` (`soften` +20, `nudge` +5, `none` 0, `setback` -10), so
the model picks a word and the data file decides the number. The model never sends a number that reaches a bar.

## The ladder, in the order it is tried

| Rung | What it is | How it can fail, and what that looks like |
| --- | --- | --- |
| `meta` | `tools/meta_client.py`, Muse Spark, structured output against the schema built from the judge file | no key, backend mock, a rate limit, an HTTP error: labelled `unavailable` with the reason, nothing is sent when no key exists |
| `open-weights` | an OpenAI compatible endpoint on this PC, LM Studio at `127.0.0.1:51235`, model from `PP_LOCAL_MODEL` or the judge file | a non loopback URL is refused before a byte is sent; a slow model is abandoned at its share of the budget |
| `replay` | this line's recorded answer out of `data/ai_cache/bridge/`, labelled with the rung that recorded it | a miss when a line was never recorded |
| `fallback` | the encounter's own `talk.fallback_pool` line from `data/encounters/all.json`, wrapped to the box | cannot fail, which is why it is last |

`PP_AI_MODE=replay` starts the ladder at the third rung, which is what plays the demo with the network off and
no model loaded. `source` is always in the answer, and `origin` says which rung recorded a replayed answer.

One judgement call to state plainly: the card lists three sources (`meta`, `open-weights`, `replay`) and this
implements a fourth, `fallback`. A game that must always answer needs a rung that cannot fail, and labelling the
encounter's own line as `replay` would be a lie about where it came from. The fourth label is the honest shape
of the same idea.

The whole request runs under one deadline, `PP_TALK_TIMEOUT` seconds. The default is 6 s, and it grows to 12 s
when a Meta key is present (Demiurge decision 2026-10-27, handoff t_3da6e753): muse-spark-1.3 answers the fight
prompt in 8.3 to 9.7 s, so a 6 s budget can never carry it. With a key the Meta rung keeps all but a 0.6 s
reserve for the file rungs instead of a half share; the two live rungs otherwise get shares of what is left and
the two file rungs keep a small reservation. A rung that runs past its share is abandoned (a daemon thread, so it
cannot hold the door open) and the next one answers.

Three defects were found and fixed after the first measurements, and each has a test that names it:

| What was wrong | What it did on this PC | Where the fix is |
| --- | --- | --- |
| the loop stopped when the budget was spent, before the file rungs | with a 6 s budget a cold model used its whole share, the fallback was recorded as `no_budget`, and the turn raised instead of answering: the one failure the ladder exists to prevent | `FILE_RUNGS` / `FILE_RUNG_SHARE` in `judge_talk` and `_share`; `test_a_spent_budget_still_ends_in_an_answer_not_an_exception` |
| a model answer that mixes quote styles was refused outright | `microsoft_phi-4-mini-instruct` wrote its first array item in double quotes and the next two in single quotes, so strict JSON refused a usable answer (measured twice, 20:18 and 20:51) | `brace_span` / `literal_object` in `parse_json_object`, which read the same object as a Python literal with `ast.literal_eval`; two tests |
| the Meta client was imported inside the first turn | a cold import cost 1.4 s of a 6 s budget, on a request that then found no key and answered `unavailable` | `--serve` imports it before it listens and prints the backend and whether a key is present, never the key |
| a note written inside the judge file's `local_request` was sent to the model server as a request field | the open weights rung failed with `HTTP Error 400` on every call, at 22:27, while the same endpoint answered a clean body in 22 s; the rung read as broken and only the replayed answers worked | `is_request_field` in `_rung_local`: a leading underscore or a documentation name (`note`, `comment`, `doc`) stays in the file and out of the body; the judge file now writes `_note`; two tests |

## The prompt is a data file the talk director owns

`data/talk/sailor_judge.json` holds the system text, the line limits, the verdict map, the encounter aliases and
the local model id. `tests/test_ai_bridge.py` reads the fenced block out of `specs/19-llm-talk.md` section 3 and
fails if the copy drifts, so the prompt has one home and the data file is a verified copy of it.

It also holds `system_local`, a shorter variant used only on the open weights rung, for a reason that is a
measurement: the full 2408 character prompt made a warm `phi-4-mini` answer in 20 to 27 seconds on this PC, and
made two 2B reasoning models spend their whole token budget thinking (`finish_reason: length`, empty content).
The 1018 character local prompt answers in the same shape in seconds. Meta always gets the full text. The local
prompt's example lines are deliberately neutral, because an example that reads like a real reply gets copied
verbatim (measured: every answer opened with the example's line until it stopped being one).

## What was measured, on this PC

Machine: Windows 11, 16 cores, LM Studio at `127.0.0.1:51235`, model `microsoft_phi-4-mini-instruct` (the
judge file's `local_model`), faster-whisper `tiny` under the Python 3.11 interpreter. Every number below is from
a run of the shipped code, and the run's own log is named.

| What | Measurement | Where it came from |
| --- | --- | --- |
| Meta rung | `unavailable`, "no Meta key in the environment", 1 to 98 ms | no key exists on this PC. `data/talk/bridge_latency.json`, ten rows |
| Open weights, box idle | 1801 ms and 1939 ms for two lines, verdict and reply correct | the selftest at 2026-10-26T18:46:23Z |
| Open weights, fleet busy | 4910, 5663, 7057, 7973, 8928, 9646, 10084, 10477, 61908 ms | `output/ai_bridge/cache_fill.log`, ten lines, 90 s budget, 9 answered, 1 abandoned |
| Open weights, fleet busy, 6 s budget | 0 of 10 answered; each abandoned at its 5.6 s share | `data/talk/bridge_latency.json`, CPU busy 100 percent, re-measured 20:44 |
| Open weights, fleet busy, 90 s budget | one line answered in 22911 ms, verdict persuaded, reply three lines | `output/ai_bridge/once-openweights-t_c784d239.txt`, CPU busy 100 percent |
| Replay rung | 2, 3, 13, 38, 44, 55, 58, 94 ms, one 2593 ms outlier | the same file, nine lines with a recorded answer |
| Replay rung, re-measured | 9 of 10 answered, worst 19 ms | the 20:44 table, CPU busy 100 percent |
| Fallback rung | 1 ms | the selftest's ladder report |
| Voice, cold worker | 10.8 s for a 6.8 s wav; 57.3 s when the box was saturated | the first `/hear` of a session loads the model |
| Voice, cold worker, re-measured | 18867 ms for the 6.8 s wav, transcript word for word, `cached=false` | `output/ai_bridge/hear-live-t_c784d239.log`, CPU busy 100 percent |
| Voice, worker loaded | 443 and 431 ms for a 6.1 s wav | prompt probes during the voice work |
| Voice, worker loaded, re-measured | 35 ms for the second call on the same wav | the same log |
| Voice, recorded | 1 to 5 ms for a wav already in the cache | the selftest's `/hear` line, and the HTTP smoke run |
| Open weights, after the `local_request` fix, fleet busy | 1547 ms in the ladder, 1891 ms and 1971 ms over HTTP for two lines, verdict and reply correct, `source=open-weights` | the selftest at 2026-10-26T22:31:25Z and the `/talk` calls at 22:34, on `127.0.0.1:8900` |
| Voice, uncached, worker already loaded | 625 ms for a 195886 byte wav, transcript word for word, `cached=false` | the `/hear` call at 22:33 on `127.0.0.1:8900` with `PP_BRIDGE_CACHE` pointed at an empty directory |
| A fallback turn, live, model server refusing to load | 5608 ms, `source=fallback`, reply `["SAY WHAT YOU CAME TO SAY."]`, `tried` lists meta unavailable (no key), open weights timeout, cache no recorded answer | the `/talk` call at 2026-10-27T00:30Z on `127.0.0.1:8791`, `output/ai_bridge/serve-t_c784d239-2.log` |
| The same rung on the next turn, model now loaded | 3442 ms, `source=open-weights`, verdict persuaded, `+20`, reply two lines | the second `/talk` at 00:30Z, same log |
| Voice, recorded, after the model server reset | 9 ms, `cached=true`, 195886 byte wav, transcript word for word | the `/hear` call at 00:31Z, same log |
| Voice accuracy | both test wavs transcribed word for word, including punctuation-free casing | wavs synthesised on this PC with its own voice, no network |
| Open weights, the server's just-in-time load refusing | `HTTP 400`, body `Failed to load model "microsoft_phi-4-mini-instruct". Error: Engine protocol startup was aborted.`, to the bridge and to a hand written `curl` body alike, for three model ids (phi-4-mini, minicpm5-2b, nemotron-3-nano-4b) while `qwen3-4b` answered in 2.5 s from an already loaded state | this run at 01:30Z, `curl /v1/chat/completions`, `curl /api/v0/models` |
| The same weights, loaded by hand | `lms load microsoft_phi-4-mini-instruct --gpu max` reported `Model loaded successfully in 1m 40.18s` (2.32 GiB), and a `/talk` then answered from `open-weights`, verdict `unmoved`, three lines inside the box | this run at 01:38Z |
| Open weights, server not answering at all | a hand written `curl` got no response in 90 s (`HTTP=000`), so the ladder's 5.6 s share expired, the turn was labelled `timeout` and the fallback answered in 5625 ms | this run at 01:42Z, `tools/ai_bridge.py --selftest` |

Reading that table: the card's "under 2 s with a local model" is met twice on an idle box and is not met while
the rest of the fleet is compiling. What the bridge guarantees is not the model's speed, it is the turn: inside
the budget the player gets an in character answer, and `source` says whether it came from a model, a recording,
or the encounter's own line.

Two operational facts worth keeping in view. First, the first call to a model LM Studio has not loaded costs 11
to 85 seconds here, which is a load from disk, not a slow answer: `tools/run.ps1` passes `--warm`, so the weights
load while the game is booting. Second, LM Studio unloads an idle model, so `--warm` also starts a keepalive that
sends one token every 90 seconds (`PP_LOCAL_KEEPALIVE`); without it, a line answered in 2.1 s came back at 20 to
28 s a minute later.

## How to run it

    powershell -NoProfile -ExecutionPolicy Bypass -File tools\run.ps1
        starts the bridge, builds, launches, stops the bridge when the game closes
    ... -NoBridge        build and play without a bridge at all
    ... -Compile         compile only, no bridge (this is what the push gate runs)

    python tools\ai_bridge.py --serve --warm     what run.ps1 starts
    python tools\ai_bridge.py --selftest         every rung printed, one line each, plus one /hear
    python tools\ai_bridge.py --latency          the measured table, written to data\talk\bridge_latency.json
    python tools\ai_bridge.py --once "a line"    one call, printed, no server

The selftest loads the local model before it reports, because the local rung's failure mode on a healthy machine
is a model that is not loaded yet: the rung's share of the 6 s budget is 5.6 s, and a cold load of these weights
took 100 s here. `PP_SELFTEST_WARM` (seconds, default 120) is that load's own budget, and a load that fails is
printed with its reason rather than counted as a code failure. The report also asks about a line the cache can
answer, so the recorded rung gets to show itself instead of reporting a miss on a line nobody recorded: measured
2026-10-26, it printed `no recorded answer for this line` while 91 answers sat in `data\ai_cache\bridge`.

The selftest wants a speech wav for `/hear`; this PC can make one with its own voice, offline:

    powershell -NoProfile -ExecutionPolicy Bypass -File tools\make_speech_wav.ps1

Then `python tools\ai_bridge.py --selftest --wav output\ai_bridge\selftest_speech_two.wav`.

## What is not proven

- **No call has been made through this bridge's Meta rung.** No key was in a worker's environment on this PC, so
  the first rung is unexercised against the real API from here. The manager reported billing live and a
  `muse-spark-1.3` probe answered at 17:00; the key still had not reached a worker's environment when this lane
  checked at 17:20 and again at 01:29Z, so the rung stays labelled rather than guessed at, and no key value is
  printed, logged or stored anywhere in this work. The machine does hold a live key: a sibling tool,
  `tools/bake_meta.py`, made live Meta calls today and its answers sit in `data/ai_cache` labelled `backend: meta`,
  `model: muse-spark-1.3`, recorded at `2026-10-27T00:22Z`. The bridge has never been the one spending them, so its
  Meta row stays `unavailable` and labelled, not inferred. Its shape is the documented OpenAI compatible one that
  `tests/test_meta_client.py` drives through a fake transport; the bridge hands it the schema from the judge file
  and labels a refusal honestly instead of pretending.
- **The open weights rung is up or down with the model server.** Measured 2026-10-27T00:27Z: `--selftest` printed
  `open-weights SourceTimeout : ran past its 5.60 s share`, and the request's `tried` list carried
  `HTTP Error 400: Bad Request`. The endpoint's own body names the cause: `Failed to load model
  "microsoft_phi-4-mini-instruct". Error: Engine protocol startup was aborted.` `GET /v1/models` still lists the
  model and the same request shape answered in 22.9 s earlier the same evening, so this is the server failing to
  load the model while the PC is full (98 percent disk, a dozen lanes running), not the unknown field defect fixed
  above. The bridge labels it `unavailable` and falls through, which is what the ladder is for. A demo on the night
  should play the recorded path unless the model is confirmed loaded. Measured again at 01:30Z: the endpoint
  refused to load three model ids with that same `Engine protocol startup was aborted`, while an already loaded
  `qwen3-4b` answered in 2.5 s, and `lms load microsoft_phi-4-mini-instruct` loaded the configured model by hand in
  100 s, after which one `/talk` answered from `open-weights`. By 01:42Z the endpoint answered nothing at all: a
  hand written `curl` returned no response in 90 s, so a talk turn inside the 6 s budget was labelled `timeout`
  and the encounter's own line answered. None of that is a bridge defect and all of it is invisible to a judge
  watching the recorded path, but it is why the local rung cannot be relied on for the video.
- **The judge text is good at deciding, not at being pretty.** A 4B model produces lines like `ASK ABOUT THE
  WATCH. I` and `SHE'S A STOWAWAY. NOT MY`. The bridge cleans them to the font and refuses a bad one, but the in
  character quality is a prompt and model question (card W3 owns the model, the talk director owns the prompt).
- **The 3 line limit is this card's, not the spec's 4.** `data/talk/sailor_judge.json` says 3 because the fight's
  box also draws the hint line; raising `max_lines` to 4 there needs no code change.
- **Demo timing under load is unproven for the model path**, for the reason in the table: on 2026-10-26 at 20:44,
  with the rest of the fleet using every core, a warm `phi-4-mini` took 19 to 23 s for one judged line, so a 6 s
  turn always falls through to the recording. The replay path is the one to trust on the night, and it is
  measured at 1 to 19 ms.
- **`tools/run.ps1` was not executed in the verification run that shipped this.** The machine refuses to start a
  PowerShell script from that session (the sandbox blocks it), so the start and stop of the bridge around a play
  session is reviewed by reading the diff, not measured. What was measured is everything the script starts: the
  server over real HTTP, its loopback bind, `/talk`, `/hear`, and the selftest. The first run that will prove the
  script is the next one Nayil plays, and `build\last-bridge.log` is where it says what it did.
