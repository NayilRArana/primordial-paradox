# Hackathon provenance: what was built during the event

Primordial Paradox is a solo entry to the Meta Global AI Developer Hackathon (2026-10-26 to 2026-11-04). The entrant is Nayil Arana, one person directing a team of AI agents (see [BUILT-WITH-AGENTS.md](BUILT-WITH-AGENTS.md)).

The rules say only work done during the event counts and that judges must be able to tell what was built in the window. This page is how to tell.

## How to see exactly what was built during the event

- The first commit of this repository is a snapshot of everything that existed before kickoff. It is tagged `hackathon-baseline-2026-10-25` and dated 2026-10-25 22:21 PDT, before the 2026-10-26 9:00 AM ET kickoff.
- Every later commit is event work and keeps its original timestamp and message.
- The whole event delta in one command:

      git diff --stat hackathon-baseline-2026-10-25..HEAD
      git log --reverse --format="%ad  %s" --date=iso hackathon-baseline-2026-10-25..HEAD

- [EVENT-LOG.md](EVENT-LOG.md) lists the same commits one line each. Its commit ids come from the private monorepo the project is developed in; this repository is an exact filtered export of that history, so ids differ. `python tools/event_log.py` prints the log again with this repository's ids.

## What the baseline already contained

The baseline is a vertical slice under construction: the GameMaker project and its rooms, the engine specs in `specs/`, the Python gate and pipeline tools in `tools/`, the data in `data/`, the test suite in `tests/`, and the art and audio produced so far. Its own README (in the baseline commit) states its condition plainly, including what did not work yet. Nothing from before the event is presented as event work.

## Which Meta model calls produced what is here

Measured on 2026-10-27 03:49 UTC from the repository itself, not from a plan.

| what | model | live or replayed | evidence |
| --- | --- | --- | --- |
| TALK rows the game reads | `muse-spark-1.3` | replayed: 9 of 18 rows are its recorded answers, read back from `data/ai_cache` with the network off, the other 9 the card's own pool line, each labelled with its reason, baked 2026-10-27T20:28:49Z | the bake block of `data/meta_bake.json` says mode replay and network false, and each of the 9 live rows matches one cache entry recorded 2026-10-27T02:12:30Z to 03:46:38Z with `network: true` (measured 2026-10-27T20:28Z) |
| Art review of the newest nightly run | `muse-spark-1.3` | live: six calls, one per frame of the 2026-10-26 nightly run | `data/eye_ledger.csv`, one row per call naming the frame it read; the frames and the review text are generated output, untracked |
| Concept art and a revision | `muse-image-1.0` | live: 1 image, 1 edit | `data/ai_cache` |
| Silhouette cut | `sam-3.1` | live: 3 calls | `data/ai_cache` |
| Every call the demo and the tests make | whichever model recorded the answer | replayed from `data/ai_cache` with the network off | `PP_AI_MODE=replay` |

`python tools\meta_client.py --cache-status` is the counter: on 2026-10-27 03:49 UTC it reported 203 entries recorded against the live API out of 209, covering chat (186), vision (12), image (1), edit (1) and segmentation (3). The total measured list price of those calls is 2.39 USD, itemised in [knowledge/META-SPEND.md](knowledge/META-SPEND.md), which `tools/meta_spend_ledger.py` regenerates from the cache.

This page replaces the earlier claim that no live Meta model call had been made from this repository. That claim was true when it was written and is not true now, which is why the counts above are dated and measured rather than asserted.

## What is not in this public repository

Internal planning notes, agent task records and research studies of other games are kept private, so that no third party's material is redistributed and the agent setup stays private. Nothing the game needs to build, run or be tested is left out. Rights and attributions for everything that is here are in [LICENCE](LICENCE) and [CREDITS.md](CREDITS.md).
