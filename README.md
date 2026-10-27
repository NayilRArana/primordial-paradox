# Primordial Paradox

A retro role playing game about Greek gods in modern England, where you can win a fight by finding the right words.

![A sailor challenges the player on a ship deck](output/ship_dialogue.png)

## What it is

A father drives his son south to Southampton as the veil between the gods' world and ours wears thin. This is a GameMaker adventure at 256 by 240 pixels, with 8 by 8 tiles, limited palettes and checks against NES picture chip rules. In a battle, you can type or speak your own reply to a sailor instead of choosing a written line. His answer and his mercy meter react to what you said.

## Built during the event

The event runs from 26 October to 4 November 2026. Work since the frozen baseline includes:

- A guided demo route, improved ship scenes and dialogue, and revised battle presentation.
- New pixel palette checks, with their test and measurement tools.
- An architecture diagram and records that separate baseline work from event work.

See the complete event diff:

```sh
git diff --stat hackathon-baseline-2026-10-25..HEAD
```

## Meta AI in this game

- **`muse-spark-1.3`:** `tools/bake_meta.py` calls it to judge dialogue. `tools/eye_critic.py` also sends it frames for art review. The live TALK path asks the same model through a local bridge this repository does not ship.
- **`muse-image-1.0`:** `tools/meta_client.py` calls `generate_image()` for concept art and `edit_image()` for revisions.
- **`sam-3.1`:** `tools/meta_client.py` calls `segment()` to separate a subject from its background.

Live and replayed, measured on 2026-10-27 10:13 UTC. These integrations use the Meta Model API through `tools/meta_client.py`, and the recorded cache is the evidence:

- **Recorded against the live API:** 274 of the 285 entries in `data/ai_cache`, covering every kind: 250 chat, 17 vision, 2 image, 1 edit and 4 segmentation calls. `python tools\meta_client.py --cache-status` recomputes that count from the entries themselves, and the 11 entries that are not live are labelled mock.
- **The TALK verdicts are live:** 13 of the 18 rows in `data/meta_bake.json` are answers from `muse-spark-1.3`, and the other 5 are the card's own weak-topic line, each one labelled with its reason in the row and counted in the bake block (baked 2026-10-27T03:45:20Z, 0 unlabelled rows). A row falls back when the answer's effect is not the one that option is authored to move, which is what keeps the fight winnable by picking options; the row keeps the authored effect and says so.
- **The eye critic is live:** `muse-spark-1.3` scored the six frames of the newest nightly run, 2026-10-26, and `data/eye_ledger.csv` holds one row per call naming the frame it read. The frames and the review text are generated output and are not tracked; the ledger is.
- **Measured spend:** 3.2068 USD at the documented list prices for every live call in the cache, itemised in [knowledge/META-SPEND.md](knowledge/META-SPEND.md).

The demo never needs the network. For every Python tool, `PP_AI_MODE=replay` reads the recorded answers in `data/ai_cache` and makes no request, so it needs no key; `record` is the mode that writes a new answer and `live` calls without writing. The game itself defaults to replay, reading `data/talk_live_tape.json` without opening a network connection, and F6 switches between replay and live mode.

Art in this build was generated with Muse Image 1.0 and cut out with SAM 3.1, used under Meta's terms as confirmed by the entrant.

### Meta in the pipeline

`tools/meta_art.py` runs one asset from prompt to NES frame and keeps every step beside the finished picture, so a reader can check the Meta call instead of taking it on trust. The reference run is the title backdrop in `output/meta_art/title_backdrop/c1`:

| step | file beside it | measured |
| --- | --- | --- |
| request to `muse-image-1.0` at 1024 by 1024 | `request.json` | 0.0100 USD |
| the answer as recorded, network true | `cached_response.json` | recorded 2026-10-27T08:58:17Z |
| `sam-3.1` asked for "the temple" | `sam_mask.json` | 0.0025 USD, the answer was empty, so no mask was written |
| the frame at 256 by 240 | `frame_nes.png` | 4 colours, 960 tiles |
| concept beside frame | `comparison.png` | 96.75 percent of pixels changed, mean Delta E 19.59 |

That frame passes the project's NES limits: `tools/nes_check.py` passes it at 256 by 240 and 960 tiles with the backdrop declared `$0F`; `tools/palette_synergy.py --gate` reports 0 gated failures across its 10 scene entries; `nes_composite_check.check_frame()` reports 0 problems in its palette, background and screen sections. An empty segmentation answer is recorded as a missing cut and never drawn as a guessed silhouette. Two further assets, the quay at night and the ship deck, are queued on the same chain and are not rendered yet.

## Run it

**Play or build: Windows, GameMaker LTS2026 and Python 3.** Run this from the repository root. It checks the data, builds the game and opens it. The first fight is the place to try TALK, then SAY IT YOURSELF.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\run.ps1
```

**Check the data: Python 3 only.** Install the dependency, then run the checker. Neither step needs GameMaker.

```sh
python -m pip install -r tools/requirements.txt
python tools/check_data.py
```

## How it was made

Nayil Arana directs specialised AI agents through a shared task board. Every claimed change requires a reproducible check, and a different agent reruns it before the work counts as done. Read [BUILT-WITH-AGENTS.md](BUILT-WITH-AGENTS.md). The build and publish machinery behind the game is formally verified; read [FORMAL-VERIFICATION.md](docs/FORMAL-VERIFICATION.md).

## Licence and credits

All rights reserved today; see [LICENCE](LICENCE) for terms and [CREDITS.md](CREDITS.md) for third party notices.
