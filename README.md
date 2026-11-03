# Primordial Paradox

You play a retro role playing game in the style of the 8-bit NES, an old Nintendo console. You meet Greek gods reincarnated in modern England.

You win fights by talking as well as by hitting.

## The game

A hurricane is battering Southampton's Town Quay. Percy, the reincarnation of Poseidon, is possessed and is causing it. Captain Morgan is possessed and is causing it too.

Zander (Zeus), Konrad (Kronos) and Hadrian (Hades) have to stop them so they return to their usual selves.

Talk to an enemy and answer well to fill its MERCY meter, which measures forgiveness, then choose SPARE, which lets it live. Or take its HP, which means health, to zero. Then it disintegr

## Play it

Download the hackathon repository at https://github.com/NayilRArana/primordial-paradox-hackathon, which holds the project files. Open the `play` folder. Double-click `PrimordialParadox.exe` (Windows, nothing to install).

Controls:

* arrow keys move
* Z confirms
* X cancels
* Enter starts and sends in the TALK box, the in game message box
* hold X to skip the credits

## How it is built

The game is a GameMaker project at 256 by 240 pixels. GameMaker is the game engine.

Python is used only for tooling:
- the NES picture chip gate (`tools/nes_check.py`), which checks image limits
- the data checks
- the tests (about 2,700)
- the art and music pipelines, which prepare assets
- the build scripts, which assemble the release

The music is original chiptune, simple retro game music, composed with the counterpoint toolchain in `tools/counterpoint/`.

Meta's `muse-spark-1.3` answers the TALK box and judges dialogue. Its answers are recorded in `data/ai_cache` so the game plays offline.

## Where the code lives

This folder is the development tree, the working files.

The submission splits into two public repositories:

* the engine as it was before the event (https://github.com/NayilRArana/primordial-paradox-engine)
* the work done during the event (https://github.com/NayilRArana/primordial-paradox-hackathon)

## Licence and credits

See `LICENCE` and `CREDITS.md`.

This README is written by a Meta model, an automated text tool, through `tools/readme_meta.py`. `tests/test_readme_meta.py` fails if it is edited by hand.

<!-- readme-author: muse-spark-1.3 body-sha256: 6d4bfe4a5a1dbe77dac1cbc682831b6c2e4afa6f668d45f493fec33fa46cb57e -->
