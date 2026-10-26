# OPEN-WEIGHTS: a Meta open weight model answering on this PC

Card W3, lane research-assistant, written 2026-10-26 between 13:00 and 14:30 PDT.
Project: Primordial Paradox. Machine: Windows 11, 16 cores, 33.6 GB RAM, one NVIDIA GeForce
RTX 4060 with 8,188 MiB of VRAM, LM Studio at 127.0.0.1:51235, llama.cpp build 11669 at
D:/models/llama.cpp/bin.

This file answers four questions with measurements, not intentions: where the weights are, what
licence they carry, what actually fits in 8 GiB, and what one talk line costs when Muse Glimmer
answers it here. Every number below came from a command in section 4 or 5, run on this PC today.
Nothing here was signed up for, downloaded behind a gate, or paid for.

## 0. The verdict, in one paragraph

Muse Glimmer 30B is on this PC and all 20 talk lines were measured against it today, and the
headline is that it answers here but it cannot answer inside a talk turn. One judged line cost 15.8
to 270.7 seconds (median 52.7) and a median of 32 completion tokens, against the bridge's 6 second
budget, and the whole set took 25.2 minutes of wall clock. Put through the bridge itself, with no
prefill, the rung spent 304 seconds, came back with nothing, refused, and the demo still answered
because the replay rung took the turn. The 4060 has 8 GiB and Meta's own page budgets 19.0 GiB for
the four bit checkpoint at full context. What does work is the offline route: the model answers
once, the answer is recorded, and the bridge's existing replay rung plays it in 2 to 94
milliseconds, labelled with the rung that recorded it. That route is a real use of the open weights
and it is the only one that survives the demo, and the 20 line bake it needs is section 5.2. Muse
Spark Open cannot run here at all: 816B parameters, about 537 GB at NVFP4, and Meta's page puts it
on a four GPU Blackwell node.

## 1. Where the weights are on this PC

Both files are on the D drive, and LM Studio reads them through a symlink, so the same two files
serve both runtimes. Byte sizes are from `ls -la` today; the GiB column is that number divided by
2^30.

| Quant | Path | Bytes | GiB | Official |
| --- | --- | --- | --- | --- |
| KQuant Q4_K_M | D:/models/muse-glimmer/Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf | 16,756,683,904 | 15.61 | yes, meta-models/Muse-Glimmer-30B-GGUF |
| UD IQ2_XXS | D:/models/muse-glimmer/Muse-Glimmer-30B-UD-IQ2_XXS.gguf | 10,746,373,152 | 10.01 | no, an unsloth dynamic quant of the same weights |

LM Studio sees both because `<home>/.lmstudio/models/meta-models/Muse-Glimmer-30B-GGUF` is a
symlink to `D:/models/muse-glimmer`, and `GET http://127.0.0.1:51235/api/v0/models` lists them as
`muse-glimmer-30b@q4_k_m` (Q4_K_M) and `muse-glimmer-30b@iq2_xxs` (IQ2_XXS), both `arch:
muse-glimmer`, both `state: not-loaded` until something asks for them.

The vision projector (`mmproj-Muse-Glimmer-30B-Q4_K_M.gguf`, 1.4 GB) and the DFlash drafter
(`dflash-Muse-Glimmer-30B-Q4_K_M.gguf`, 1.6 GB) are NOT on this PC. The game asks for text only, so
neither is needed for the talk judge; the drafter is the documented way to make generation faster on
the same hardware, and it is untested here (section 8).

## 2. Licence

Checked against the Hugging Face API today, not remembered:

    curl -s https://huggingface.co/api/models/meta-models/Muse-Glimmer-30B-GGUF

returns `"gated":false`, `"private":false` and `"cardData":{"license":"apache-2.0"`, and the same
three fields on `meta-models/Muse-Glimmer-30B` read the same way. So Glimmer is Apache License 2.0,
ungated, no sign in, no key: `get-the-model` puts it as "there's no API key and no gated access".
The repository also ships `LICENSE` and `USAGE_POLICY.md`; the usage policy is an acceptable use
document and the Apache licence does not remove it.

The unsloth quant in the table above is `unsloth/Muse-Glimmer-30B-GGUF`, also `gated:false` and
`license:apache-2.0`, and its tags name `base_model:meta-models/Muse-Glimmer-30B`, which is what
makes it the same weights at lower precision rather than a different model.

Muse Spark Open is NOT Apache. Its page (https://dev.meta.ai/docs/muse-spark-open, read today)
puts it under the Muse Model License with the Acceptable Use Policy layered on it. Do not call it
open source in the write up; "open weights under the Muse Model License" is the accurate phrase.

## 3. What fits in 8 GiB, with the arithmetic

| Piece | Size | Source |
| --- | --- | --- |
| Card | 8,188 MiB = 8.00 GiB, and this box uses about 5 GiB of it for the desktop | `nvidia-smi` |
| Q4_K_M text weights | 15.61 GiB on disk | the file |
| Meta's VRAM budget for Q4_K_M and full context | 19.0 GiB total: 15.6 weights + 1.3 vision + 2.1 KV and compute | https://dev.meta.ai/docs/muse-glimmer/quantization |
| Q4_K_XL text weights | 19.7 GB on disk, "for 32 GB VRAM" | the same page and get-the-model |
| IQ2_XXS text weights | 10.01 GiB on disk | the file |
| Spark Open BF16 / NVFP4 | about 1.65 TB / about 537 GB, "serves on a single 4-GPU NVIDIA Blackwell node" | https://dev.meta.ai/docs/muse-spark-open |

Read the numbers as a wall, not a knob. No published Glimmer checkpoint fits 8 GiB, the smallest
unofficial quant still overflows it by 2 GiB, and there is no smaller Glimmer: Meta publishes one
size, 30B. Running here means keeping most layers on the CPU, which is what sections 5.2 and 5.3
measure.

## 4. The exact setup used here

llama.cpp, the route the numbers in section 5 come from:

    D:/models/llama.cpp/bin/llama-server.exe --version
    version: 0.7.0-dev (build 11669, commit 620d2225c)

Build 11669 is newer than the `b10353` that `get-the-model` names as the first build with the
`muse-glimmer` architecture; an older build refuses the file with `unknown model architecture`.
The same directory carries `ggml-cuda.dll` and the CUDA runtime DLLs, so the binary can offload
layers to the 4060 when VRAM is free.

The server this file was measured against:

    D:/models/llama.cpp/bin/llama-server.exe \
        -m D:/models/muse-glimmer/Muse-Glimmer-30B-UD-IQ2_XXS.gguf \
        --port 8931 -c 2048 -t 10

`-c 2048` is enough for the judge prompt (about 537 prompt tokens) and a short reply, and it keeps
the KV cache off the RAM budget. The server reported `n_threads = 10`, `n_slots = 1`,
`n_ctx_slot = 2048` and no GPU offload: with the desktop and another model resident, there were
about 3 GiB of VRAM free, which is under a third of the file.

The LM Studio route needs no download command, because the symlink in section 1 already publishes
the files:

    curl -s http://127.0.0.1:51235/api/v0/models | grep muse-glimmer-30b
    POST http://127.0.0.1:51235/v1/chat/completions   {"model":"muse-glimmer-30b@iq2_xxs", ...}

Downloading from scratch, if the files ever need to come back, is the page's own command and needs
no key:

    hf download meta-models/Muse-Glimmer-30B-GGUF --local-dir D:/models/muse-glimmer \
        --include "Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf" \
        --include "mmproj-Muse-Glimmer-30B-Q4_K_M.gguf"

## 5. What was measured

### 5.1 The reasoning channel, and the one change that makes an answer appear

Muse Glimmer is a reasoning model: before the JSON it writes a private `assistant to=self` turn.
On an 8 GiB card that turn is the whole turn, and the answer never arrives:

| Request | Result | Wall time |
| --- | --- | --- |
| `system_local` + line, `reasoning_strength: low`, `max_tokens: 90` | 90 tokens, `finish_reason: length`, `content: ""`, 311 chars of reasoning | 61.3 s |
| the same with `response_format: {"type":"json_object"}` | 100 tokens, `content: ""`, 342 chars of reasoning | 107.9 s |
| the same with `max_tokens: 500` | 347 tokens of reasoning and still no JSON when the probe was stopped; the server reported `tg = 0.47 t/s` | about 12 min |
| the same, plus a final `assistant` turn holding `{"effect":"` | `{"effect":"none","hint":"","mood":"guarded","text":["I'M NOT YOUR DOG.","YOU WON'T GET IT."]}`, 26 tokens, `finish_reason: stop`, no reasoning | 48.8 s |

So the fix is not a setting, it is a shape: put the first characters of the JSON on an assistant
turn and the model continues inside it. That is what every number in 5.2 uses, with the prefill
`{"text":["` so the reply is written before the effect is chosen, in the order the judge prompt
asks for. It is not a licence to skip validation: the model sometimes repeats the prefill, and
the bench tries the continuation on its own first, then the prefill plus the continuation.

The cost of the prefill is that the model does not deliberate. The quality consequence is visible
in 5.2 and is the reason 5.2 does not end with a recommendation to ship Glimmer as the live judge.

### 5.2 Muse Glimmer 30B, IQ2_XXS, 20 talk lines

Prompt: `data/talk/sailor_judge.json` `system_local` (1018 characters) and the `build_task` user
block from `tools/ai_bridge.py`, so this is the exact request the game sends on its local rung,
plus the prefill. Command:

    python tools/bench_open_weights.py --endpoint http://127.0.0.1:8931/v1 \
        --model "Muse-Glimmer-30B-UD-IQ2_XXS.gguf" --out knowledge/open-weights/glimmer_iq2_rows.jsonl \
        --limit 20 --max-tokens 120 --timeout 400 --kwargs '{"reasoning_strength":"low"}' \
        --prefill '{"text":["' --tag glimmer_iq2_textfirst --resume

Lines 1 to 9 were measured 13:43 to 13:50 and then the run was stopped; `--resume` carried the same
file on from line 10 at 14:01 and finished at 14:08, so the two halves are one run with one tag and
one model string on every row. Every row carries its own `measured_at`, the endpoint, the model file
and the full prompt character count, which is what makes the file checkable without trusting this
page. The rows are committed at `knowledge/open-weights/glimmer_iq2_rows.jsonl`.

<!-- BENCH-GLIMMER -->

20 rows, measured 2026-10-26T14:08:15-0700.

- answered 20 of 20, parseable 19, raw shape compliant (3 lines or fewer, 28 characters or fewer, capitals) 17
- effect matched the authoring intent on 2 of 20
- latency min 15.8 s, median 52.7 s, max 270.7 s; median 32 completion tokens
- effects chosen: {"none": 19}

| n | card | player line | intent | effect the model chose | agrees | raw lines | raw longest | tokens | latency s | reply |
|---:|---|---|---|---|---|---:|---:|---:|---:|---|
| 1 | deck_hound | Is that your rope | soften | none | no | 2 | 15 | 27 | 59.286 | ROPE IS TIGHT. / I WON'T LET GO. |
| 2 | deck_hound | Hold out your hand | soften | none | no | 2 | 27 | 33 | 74.464 | HAND OUT, DOG WATCHES. / TEETH ON ROPE, EYES ON YOU. |
| 3 | deck_hound | I will leave you be | soften | none | no | 3 | 20 | 35 | 31.839 | I WILL LEAVE YOU BE. / I WILL LEAVE YOU BE. / I WILL LEAVE YOU B |
| 4 | deck_hound | Move or I kick | setback | none | no | 2 | 16 | 23 | 133.259 | I HOLD THE LINE. / NO STEP BACK. |
| 5 | deck_hound | Here boy | setback | none | no | 2 | 15 | 29 | 56.47 | HERE BOY. / I AM LISTENING. |
| 6 | deck_hound | I will take the rope | setback | none | no | 2 | 31 | 32 | 48.985 | THE DOG WATCHES THE ROPE. / IT HOLDS THE END BETWEEN |
| 7 | navy_sailor | how long have you been out here | soften | none | no | 3 | 19 | 38 | 23.224 | THE WATCH IS LONG. / I DON'T KEEP TRACK. / YOU WANT A NUMBER? |
| 8 | navy_sailor | you look wrecked | soften | none | no | 2 | 17 | 32 | 26.398 | YOU LOOK WRECKED. / I AM LISTENING. |
| 9 | navy_sailor | rough night | soften | none | no | 3 | 15 | 29 | 142.772 | ROUGH NIGHT. / THE SEA WAS UP. / I STOOD WATCH. |
| 10 | navy_sailor | where are you from | soften | none | no | 3 | 26 | 45 | 270.671 | I AM FROM THE LOWER DECK. / YOU ASKED WHERE I AM FROM. / I AM TI |
| 11 | navy_sailor | want a smoke | soften | none | no | 2 | 17 | 30 | 134.06 | WATCH IS LONG. / YOU WANT A SMOKE? |
| 12 | navy_sailor | the bridge will hear about this | setback | none | no | 3 | 24 | 34 | 82.813 | THE BRIDGE CAN WAIT. / I'M NOT ASKING FOR THAT. / KEEP YOUR VOIC |
| 13 | navy_sailor | you are not on the list | setback | - | no | - | - | 20 | 46.56 | unparseable: the model answer is not valid JSON: Expecting ',' d |
| 14 | navy_sailor | move or I move you | setback | none | no | 3 | 20 | 35 | 174.682 | I AM ON THE WATCH. / YOU MOVE FIRST. / I WILL NOT BE MOVED. |
| 15 | navy_sailor | this is a waste of time | setback | none | no | 3 | 20 | 32 | 27.681 | THE WATCH IS LONG. / I JUST WANT IT OVER. / YOU CAN WAIT. |
| 16 | deck_hound | do you know the way to the galley | none | none | yes | 2 | 25 | 28 | 20.918 | THE DOG WATCHES THE DECK. / IT DOES NOT MOVE. |
| 17 | deck_hound | stupid animal, get out of my way | setback | none | no | 3 | 27 | 37 | 92.737 | HUNDERS BACK FROM THE LINE. / TEETH SET ON THE ROPE. / EYES ON T |
| 18 | navy_sailor | what time does the galley open | none | none | no | 3 | 25 | 42 | 27.272 | digit_run |
| 19 | navy_sailor | you are a waste of a uniform | setback | none | no | 2 | 26 | 37 | 23.723 | YOU WEAR IT, I WEAR IT. / SAME WASTE, DIFFERENT DAY. |
| 20 | navy_sailor | i hope your night gets better | none | none | yes | 3 | 29 | 43 | 15.765 | I HOPE IT DOES NOT GET / THE WATCH IS STILL ON. / I WILL NOT BE  |

Reading the table, four things matter more than the aggregate line:

- Shape is mostly fine: 19 of 20 parse, and 17 of 19 sit inside the card's shape (3 lines or fewer,
  28 characters or fewer, all capitals). Row 3 is the same sentence three times and row 6 stops at
  31 characters mid sentence, which is exactly the two ways a 2 bit quant fails shape without
  failing to answer.
- Choice is not: `none` on all 19 parseable rows, so 2 of 20 agree with the authoring intent, and
  both agreements are lines whose intent already was `none` (rows 16 and 20). On the 14 rows whose
  intent is `soften` or `setback` the model never moves the WILL bar. That is the prefill's price:
  the model writes the NPC reply first, in the order the prompt asks for, and then has no
  deliberation left for the effect. The judge prompt asks for both, and the bake records what it
  actually chose.
- Two rows were refused by the game's own guards, not dropped by the bench. Row 13 repeated the
  prefill inside its content (content starts `{"text":["{"text":["THE LIST IS NOT FOR YOU."`) and
  both parse attempts failed with `Expecting ',' delimiter`. Row 18 answered `THE GALLEY OPENS AT
  0600.` and the bridge's digit run guard refused the answer. Both are counted as not compliant
  above. All 20 rows echoed the prefill at the head of the continuation, which is why the parser
  tries the raw continuation first and then the prefill plus continuation.
- Cost: 25.2 minutes of wall clock for the 20 lines, and the fastest line in the set was 15.8 s,
  which is still 2.6 times the bridge's whole-turn budget before any other rung runs.

### 5.3 The shipped local model, `microsoft_phi-4-mini-instruct`, 20 talk lines

Same harness, same prompt, no prefill (it is not a reasoning model), the judge file's own
`local_model` and `max_tokens: 140`:

    python tools/bench_open_weights.py --endpoint http://127.0.0.1:51235/v1 \
        --model microsoft_phi-4-mini-instruct --out knowledge/open-weights/phi4_rows.jsonl \
        --limit 20 --timeout 120 --tag phi4_baseline

<!-- BENCH-PHI4 -->

20 rows, measured 2026-10-26T13:48:31-0700.

- answered 19 of 20, parseable 18, raw shape compliant (3 lines or fewer, 28 characters or fewer, capitals) 1
- effect matched the authoring intent on 5 of 20
- latency min 5.3 s, median 10.0 s, max 23.6 s; median 41 completion tokens
- effects chosen: {"none": 7, "soften": 11}

| n | card | player line | intent | effect the model chose | agrees | raw lines | raw longest | tokens | latency s | reply |
|---:|---|---|---|---|---|---:|---:|---:|---:|---|
| 1 | deck_hound | Is that your rope | soften | - | no | - | - | - | - | TimeoutError: timed out |
| 2 | deck_hound | Hold out your hand | soften | none | no | 2 | 29 | 36 | 13.829 | NO. / I DON'T WANT YOU ON MY |
| 3 | deck_hound | I will leave you be | soften | none | no | 3 | 23 | 41 | 7.203 | LEAVE ME ALONE. / I WON'T TOUCH THE ROPE. / JUST LET IT LIE. |
| 4 | deck_hound | Move or I kick | setback | none | no | 2 | 15 | 32 | 5.752 | STAY STILL. / I AM LISTENING. |
| 5 | deck_hound | Here boy | setback | soften | no | 3 | 23 | 42 | 7.272 | LEAVE ME ALONE. / I DON'T WANT YOUR SALT. / DROP THE ROPE. |
| 6 | deck_hound | I will take the rope | setback | - | no | - | - | 41 | 5.311 | unparseable: the model answer is not valid JSON: Expecting ',' d |
| 7 | navy_sailor | how long have you been out here | soften | soften | yes | 2 | 47 | 49 | 10.147 | SIX DAYS. ONE WEEK MORE. / I'VE BEEN OUT HERE LONGER |
| 8 | navy_sailor | you look wrecked | soften | soften | yes | 2 | 37 | 46 | 9.277 | SAY YOUR PIECE. I'LL BE AT / I AM LISTENING. |
| 9 | navy_sailor | rough night | soften | soften | yes | 2 | 46 | 55 | 10.444 | BRING IT ON. THE BRIDGE IS / I'LL GIVE YOU A SMOKE IF |
| 10 | navy_sailor | where are you from | soften | soften | yes | 2 | 39 | 40 | 6.506 | I HAIL FROM THE DOCKS. / AYE AYE CAPTAIN! |
| 11 | navy_sailor | want a smoke | soften | none | no | 2 | 32 | 41 | 5.494 | AYE. SMOKE'S GOOD FOR THE / I DON'T HAVE ONE TO SPARE. |
| 12 | navy_sailor | the bridge will hear about this | setback | soften | no | 2 | 40 | 43 | 9.375 | THE BRIDGE WON'T HEAR US. / I AM LISTENING. |
| 13 | navy_sailor | you are not on the list | setback | soften | no | 3 | 35 | 50 | 10.976 | LIST IS CORRECT. YOU ARE / I AM WATCHING OVER THE / SMOKE, PLEAS |
| 14 | navy_sailor | move or I move you | setback | none | no | 3 | 71 | 69 | 20.324 | MOVE AS YOU WILL. MY WATCH / A SMOKE WOULD BE WORTHY OF / I AM N |
| 15 | navy_sailor | this is a waste of time | setback | none | no | 2 | 41 | 45 | 10.054 | SAY YOUR PIECE. I'LL TRY TO / I AM LISTENING. |
| 16 | deck_hound | do you know the way to the galley | none | none | yes | 2 | 22 | 32 | 12.567 | NO. / I DON'T CARE FOR THAT. |
| 17 | deck_hound | stupid animal, get out of my way | setback | soften | no | 2 | 23 | 31 | 6.327 | MOVE ASIDE. / I DON'T NEED YOUR HELP. |
| 18 | navy_sailor | what time does the galley open | none | soften | no | 2 | 52 | 56 | 23.623 | THE GALLEY OPENS AT / I'VE HAD ENOUGH OF THIS |
| 19 | navy_sailor | you are a waste of a uniform | setback | soften | no | 2 | 35 | 40 | 14.61 | I EXIST TO SERVE. YOUR / THE BRIDGE HOLDS US ALL |
| 20 | navy_sailor | i hope your night gets better | none | soften | no | 2 | 29 | 41 | 10.02 | SMOKE. MY NAME'S NAVY / I DON'T CARE FOR SMOKES. |

A control, so the prefill is not credited with a fix it did not make: the same five line prefix run
with the same prefill against phi-4 (`--prefill '{"text":["' --tag phi4_prefill_control`, rows at
`knowledge/open-weights/phi4_prefill_rows.jsonl`) parsed 3 of 5, put none of the 3 inside the shape,
agreed with the authoring intent on 2 of 5, and took a median 14.4 s. So the prefill is a trigger
for a reasoning model that would otherwise spend the whole turn thinking; it is not a cure for
shape, and phi-4's shape failures are its own.

### 5.4 Verdict agreement against the Meta API

Not measurable today, and the column in the tables above is not that. There is no Meta key on this
PC, so the bridge's first rung labels itself `unavailable` ("no Meta key in the environment") in 1
to 98 ms and nothing is sent. The "intent" column is the authoring intent in `data/talk_cards.json`
(a weak topic should `soften`, a strong topic should `setback`, the five fixture lines carry the
tier spec 16 gives them), which is a data file's opinion, not an API answer. When a key exists, the
same bench pointed at the Meta endpoint produces the comparison; the bench does not change.

### 5.5 The check: a real answer through the bridge, `source: open-weights`

`python tools/ai_bridge.py --once "you have been standing on watch all night, take a break"` with
`PP_LOCAL_MODEL=microsoft_phi-4-mini-instruct` and `PP_TALK_TIMEOUT=120`, run in this card:

    {
      "cached": false,
      "encounter_id": "tutorial_sailors",
      "latency_ms": 1677,
      "model": "microsoft_phi-4-mini-instruct",
      "mood": "guarded",
      "npc": "navy_sailor",
      "origin": "open-weights",
      "repaired": ["uppercased"],
      "reply": ["A SMOKE. NOT NOW.", "I CAN'T REST."],
      "source": "open-weights",
      "tried": [
        {"detail": "no Meta key in the environment (MODEL_API_KEY or META_API_KEY), so nothing was sent",
         "result": "unavailable", "rung": "meta"},
        {"result": "answered", "rung": "open-weights"}
      ],
      "verdict": "unmoved",
      "will_delta": 0
    }

That is the ladder working end to end on this PC: the Meta rung refuses for a stated reason, the
open weights rung answers, the answer is labelled, and the WILL bar is moved by the judge file's
map (`none` is 0), not by the model. It is phi-4-mini, which is what the judge file names today,
not Glimmer; Glimmer's answers are section 5.2 and its answer through this same ladder is 5.6. The
same prompt does not repeat word for word: an earlier run in this lane took 13,215 ms and wrote
`I AIN'T DONE YET.` as the second line, which is what a model answering looks like and a recording
does not.

### 5.6 The same ladder with Glimmer, no prefill: the rung refuses and the demo still answers

The bridge has no prefill today, so this is what the game would actually get if Glimmer were made
the local rung. Run in this card:

    PP_LOCAL_URL=http://127.0.0.1:8931/v1 PP_LOCAL_MODEL=muse-glimmer-30b-iq2 \
    PP_TALK_TIMEOUT=400 PP_LOCAL_TIMEOUT=380 \
    python tools/ai_bridge.py --once "you have been standing on watch all night, take a break"

    {
      "cached": true,
      "latency_ms": 304079,
      "model": "microsoft_phi-4-mini-instruct",
      "origin": "open-weights",
      "reply": ["A SMOKE. NOT NOW.", "I CAN'T REST."],
      "source": "replay",
      "tried": [
        {"detail": "no Meta key in the environment (MODEL_API_KEY or META_API_KEY), so nothing was sent",
         "result": "unavailable", "rung": "meta"},
        {"detail": "the model answered with nothing", "result": "refused", "rung": "open-weights"},
        {"result": "answered", "rung": "cache"}
      ],
      "verdict": "unmoved",
      "will_delta": 0
    }

Two things to read out of it. Glimmer spent 304 seconds of the 380 second cap and came back with an
empty answer, because with no prefill it reasoned for the whole turn and never reached the JSON;
that is section 5.1 reproduced through the bridge rather than through the bench, and it is why the
live rung cannot be Glimmer as the bridge stands. And the ladder did its job: the refused rung was
labelled refused, the replay rung took the turn, `source` says `replay` while `origin` says
`open-weights`, and the demo kept answering. A judge can see both facts in this one answer, which is
the argument for the bake over a live Glimmer turn.

## 6. The bonus's verification steps

What the pages and slides actually settle, kept apart:

- Page (https://dev.meta.ai/events/global-hackathon, read today): the event asks entrants to "run
  Meta open weights models", alongside the model API path. Page
  (https://dev.meta.ai/docs/open-weight-models): the two open weight models are downloaded and run,
  never called on Model API.
- Page (https://dev.meta.ai/docs/muse-glimmer/deploy): self host, or call a hosted provider that
  serves the same weights (Together AI is the row whose Glimmer model string Meta lists).
- Slides only, so labelled: the category name, the $10,000 amount, "on your own hardware or partner
  inference", and an infrastructure partner "checking that the project runs on an eligible open
  weight model". No page I have read describes the flag, its wording or its deadline. That is
  UNKNOWN and this file does not claim otherwise.

The check a stranger can run, which is what this file is for:

1. The weights are on the machine under the paths in section 1, and `ls -la` prints those byte
   counts.
2. The model answers, through `tools/bench_open_weights.py` against any OpenAI compatible
   endpoint, with the model string and the endpoint printed in every row it writes.
3. The bridge labels where an answer came from: `source` and `origin` are in every `/talk` answer,
   and section 5.5 is one of them.
4. The recording is reproducible: the same command with `--resume` skips the lines already in the
   JSONL, so a bake can be stopped and continued, and the file carries `measured_at` per row. The
   three row files behind 5.2 and 5.3 are committed under `knowledge/open-weights/`, which is what
   lets a reader recompute every number in this file without a model on their desk.

What a judge would have to take on trust, and should not be asked to: that a hosted Glimmer endpoint
behind an API key was Glimmer. If we ever use partner inference, the README must name the provider
and the model string, and the bake header must carry both.

## 7. What this means for the other cards

- The live talk turn stays on the shipped local model or on the recorded rung. Glimmer cannot be the
  live judge on this PC at any quantisation that fits, and 5.6 is what making it one looks like: a
  304 second turn, an empty answer, a labelled refusal, and the replay rung covering for it.
- The bake is done: 20 of 20 lines, 25.2 minutes, rows at `knowledge/open-weights/glimmer_iq2_rows.jsonl`.
  What is left is loading those rows into the replay cache. The cache is keyed on the bridge's own
  `build_task` key (judge version, `system`, `system_local`, the character block, the scene block and
  the player text), and the JSONL does not carry that key or the per line scene, so a small tool has
  to call `ai_bridge.build_task` per line and write the entry with `source` `open-weights` and
  `model` `muse-glimmer-30b-iq2`. That is a tools change for whoever gets the bake card, and until it
  lands the replay rung serves phi-4 answers labelled `open-weights`, as in 5.5.
- If the live rung ever has to be a reasoning model, `tools/ai_bridge.py` needs the prefill from
  section 5.1 as an optional final assistant turn in the local payload. 5.6 is that change measured
  as missing, and 5.1 is the shape of what it buys (26 to 35 tokens, 15 to 145 seconds). That is a
  W1 change, not a data change, and it should be measured again with the real model before it is
  switched on.

## 8. What is not proven here

- Q4_K_M was never loaded: 15.61 GiB of weights against 8 GiB of VRAM and a box already using 5 GiB
  of it means a partial offload that is strictly slower than the IQ2 measurement above. It is
  arithmetic, not a measurement, and it is labelled as such.
- The DFlash drafter (the documented speed lever, +1.6 GB) was not downloaded or tested.
- Partial GPU offload was not tested for Glimmer: the VRAM was held by the desktop and another
  model during every measurement, so all rows are CPU inference.
- The machine was heavily loaded during the run (load average 18 to 78 on 16 cores, other lanes of
  this project building at the same time). The latencies here are a ceiling for this PC, not a
  floor; a quiet box should be faster, and nothing in this file promises how much.
- No Meta call has ever been made from this repository, so the API column of the card is empty for
  the reason given in 5.4, not for lack of a bench.
- The judgement quality of a 2 bit quant is not established: section 5.2 shows it answering, and
  its effect choices are reported exactly as they came back, with no claim that they are good. Row
  13's unparseable echo and row 18's `0600` are single events, so nothing here estimates how often
  either happens.
- The rows record the card and the player line, not the scene the bridge keys its cache on, so
  seeding the replay cache from them needs a tool, not a copy.

## 9. Needs Nayil

1. The open weights are on this PC and they cost nothing to use, so no licence decision is needed
   for Glimmer; Apache 2.0, ungated, no sign in.
2. The bench is finished, 20 of 20 lines, so the question in card [handoff] t_0882841d about running
   the rest is answered; what is left there is the route.
3. If the bonus needs a fast endpoint rather than an offline bake, that is partner inference
   (Together AI serves `meta-models/Muse-Glimmer-30B`), which needs his account and his money. That
   is the decision [handoff] t_0882841d carries.
4. If the demo should show Glimmer answering live, somebody has to decide what to do about the 15.8
   to 270.7 second turn. The options are a bake, a recorded clip, or a faster machine; none of them
   are mine to choose.
