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

## What is not in this public repository

Internal planning notes, agent task records and research studies of other games are kept private, so that no third party's material is redistributed and the agent setup stays private. Nothing the game needs to build, run or be tested is left out. Rights and attributions for everything that is here are in [LICENCE](LICENCE) and [CREDITS.md](CREDITS.md).
