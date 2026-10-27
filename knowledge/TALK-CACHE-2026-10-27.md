# The talk cache after the prompt fix (card t_1ef2d52d), 2026-10-27

## What was wrong

`data/talk/sailor_judge.json` `system_local` gave its shape example as two drawable sentences:
`{"text":["SAY YOUR PIECE.","I AM LISTENING."], ...}`. A model copies an example that looks like a reply, and
one recorded answer in `data/ai_cache/bridge` did exactly that: file `7459197ba36a...json`, source open-weights,
text `THE BRIDGE WON'T HEAR US.` / `I AM LISTENING.` The second line is the prompt, not a verdict, and it was
inside a line the demo could replay.

## What changed

1. `system_local` now carries placeholders: `{"text":["<LINE 1>","<LINE 2>"], ...}`. The angle brackets are
   outside the prompt's own alphabet (capital A to Z, digits, `. , : ! ? ' ( )`), so a model that copies the
   example is refused by `clean_lines` instead of having its echo drawn in the box. The prompt is 1004
   characters, down from 1018. `system_local_note` records the reason and the date.
2. `tests/...` were not touched. `tools/ai_bridge.py` was not edited (the card says not to: the re-clean on
   read and the dangling article rule are already there).
3. `docs/AI-BRIDGE.md` now says 1004 characters and names the placeholders.
4. `tools/kaggle_bake_open.py` holds its own copy of `system_local` (it is the self-contained Kaggle kernel), so
   that literal was patched to match. `tools/make_bake_open_kernel.py` could NOT regenerate it: it replaces
   `__CARDS_JSON__` and `__SYSTEM_LOCAL_JSON__` markers, and the generated file no longer has them, so it
   exits with `tools\kaggle_bake_open.py is missing its injection markers`. That file is untracked in this repo
   (see `knowledge/COMMIT-BACKLOG-2026-10-27.md`), so this change lives in the working tree only.

The judge file's `version` stayed 1 on purpose. The cache key is
`sha256(judge.version, sha256(system), sha256(system_local), character, scene, persona, limits, player line)`,
so the prompt change alone moves every key. Bumping `version` would invalidate the rows `data/meta_bake.json`
records a version for, and buy nothing.

## The re-bake, measured on this PC 2026-10-27

The key includes the prompt hash, so the prompt edit made all 153 recorded talk answers unreachable at once
(the cache is read by key, never by content). Two bakes put the shipped answers back.

Ten demo lines (`ai_bridge.SELFTEST_LINES`, the lines the TALK fight and the latency table use), through
`tools/ai_bridge.py`'s Meta rung, one call each, 9 calls because one line was already recorded under the new
key. Measured 6032 to 10016 ms per line. All ten read as dialogue:

    YEAH. ALL NIGHT HERE. / TIRED TO THE BONE.
    SAY IT AGAIN. I DARE YOU. / WATCH STAYS. YOU LEAVE.
    NOT ON MY WATCH. / TRY IT.
    KEEP THE BRIDGE OUT OF IT. / I AM ON WATCH. THAT IS ALL.
    YEAH. I WANT ONE TOO. / STILL ON WATCH. TIRED.
    YEAH. HOURS NOW. / STILL ON WATCH.
    CORSO. THIRD WATCH. / NOBODY ASKS THAT.
    LIST IS LIST. WALK ON.
    NO. NOT HAPPENING. / WALK BACK DOWN.
    YEAH. SWELL IS BAD. / LONG WATCH FEELS LONGER.

Forty five persona lines (`tools/bake_personas.py`, 15 each for konrad, urien, quay_townsperson), mode live,
45 calls attempted, 45 answered, 330.2 s. `data/talk_personas_bake.json` was rewritten by that tool, and
`bake_personas.check_file()` reports `45 rows, 0 problems, 45 live`.

Why the Meta rung and not the local one, which the card suggested: the open weights rung could not answer at
all today. `microsoft_phi-4-mini-instruct` on LM Studio at 127.0.0.1:51235 timed out twice at a 59.6 s share and
then answered HTTP 400, and a direct curl to the same model with an 8 token prompt hung past 35 s. That is a
cold or contended endpoint (two other agents were working this PC), not a prompt fault. The Meta rung is also
the rung that recorded the ten lines the demo replays today, so the recorded answers keep one voice and one
provenance.

## What the cache holds now

    156 files: 153 talk, 3 hear (whisper transcripts, keyed on wav bytes, untouched)
     55 reachable under the current prompt: 45 persona rows + 10 demo lines
    101 unreachable: recorded under an earlier prompt, or for a player line nobody can rebuild from the file

The prompt-echo entry `7459197ba36a...json` is one of the 101: unreachable, because the bridge asks for a key
computed from the current prompt and will never ask for that one. It was left on disk as the evidence for this
card rather than deleted. The 101 were left in place too: `data/talk_personas_bake.json` names only live keys
now, no other report names a cache file, and git history can answer "what did the old prompt say" without a
file that a future reader might mistake for a served answer.

Replay, with no key and no model (`PP_AI_MODE=replay`, rungs `['cache', 'fallback']`):

    ten demo lines: 10 of 10 answered, source replay, 0 ms each
    one line per persona: source replay, 0 to 16 ms

## Checks run

    python -m pytest tests/test_ai_bridge.py tests/test_talk_personas.py tests/test_bench_open_weights.py -q
    -> 89 passed in 23.22 s

    python tools/bake_personas.py --check -> 45 rows, 0 problems, 45 live

    verify_rebake.py: every one of the 45 report rows rebuilds to the key the report names and the stored text
    matches the row, 45 of 45; all 10 demo lines resolve to a meta answer.

## Still open

- `tools/make_bake_open_kernel.py` cannot regenerate its own output because the markers are consumed. Either
  the template has to live in a separate file, or the generator has to re-read the `SYSTEM_LOCAL` and
  `CARDS = [...]` literals it wrote. Until then a prompt or card change means a hand patch of the kernel.
- The 101 dead cache entries are a decision for the manager: keep them as history, or delete them so the folder
  is only what replay can serve.
- The local rung should be re-measured on an idle PC. If `phi-4-mini` answers in about a second again, a local
  re-bake is the cheaper path for future prompt changes; the 2.3 s to 10.0 s clipped tails it produced on
  2026-10-26 are why the Meta rung recorded this bake.
