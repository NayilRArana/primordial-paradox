# How this was built: one person and a team of AI agents

Primordial Paradox is directed by one person, Nayil Arana, and built by a fleet of specialised AI agents working a shared task board. Nayil sets the direction, makes the taste calls (the ear test on every cue, the look of every sprite) and approves anything that leaves the machine. The agents do the rest, and none of them is trusted on its word.

## The team

| Role | What it does |
|---|---|
| Game director | owns the specs and rules on every design question the others raise |
| Builder | engine code, tools, the build, the pipeline |
| Art | redraws sprites and scenes to the NES limits, from concept art to legal tiles |
| Music | writes and revises chiptune cues, scored by an ear loop |
| Testing | the gates, the demo autoplay and capture, the nightly checks |
| Code review and audit | independent re-runs of every claim before work counts as done |
| Research | rules, platform docs and prior art, each claim with its source |

## How work moves

1. Every piece of work is a card with a goal, the exact inputs, the output and the check that proves it.
2. A card cannot close without evidence: the command it ran and its output, a test count, a commit, or a file hash. "It should work" is not evidence.
3. A different agent re-runs the check before the work is trusted.
4. Gates are code, not instructions: a secret scan, data schemas, a clean-room provenance check, and a measured check of every frame against the NES picture chip's palette and tile limits. A change that fails a gate does not land.
5. Questions an agent cannot settle go to the game director or to Nayil as a single decision, never as a guess.

## Where it runs

- A Windows desktop for GameMaker builds and the agents themselves.
- Cloud sandboxes for parallel test runs.
- A free GPU for concept art and image generation.

## What is deliberately not here

The agents' instructions, model routing and internal tooling stay private. This page describes how the work was organised; the game, its tools and its tests are in this repository.
