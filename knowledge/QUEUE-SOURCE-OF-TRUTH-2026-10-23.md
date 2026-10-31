# QUEUE-SOURCE-OF-TRUTH-2026-10-23

Card t_4e54cc9e, the work order that ruling 3 of `knowledge/PALETTE-RULINGS-2026-10-23.md` names.
The ruling answered the queue's Q3 with YES: the sprite queue measures `game/sprites_src`, and
`game/art` retires. This file is what was done, measured, and deleted, so the next lane can check it
without re-running anything.

## What the queue measures now

Nineteen rows, no row measuring `game/art`. Fifteen were repointed, two were renamed to the names the
shipped sheets carry, two were retired. Every number below was measured from the file the row now
names, on 2026-10-23, with `tools/nes_check.py`; the numbers the rows used to carry are kept in each
row's `defect.ghost_before`, labelled as a retired copy that a clone cannot reproduce.

| row | path before (state) | path now | sheet | frames | colours | off palette | nes_check | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `spr_pp_font8` | `game/art/spr_pp_font8.png` (measured) | `game/sprites_src/title/spr_pp_font8.png` | 616x8 | 77 | 1 | 0 px | PASS | `done` |
| `spr_pp_menu_cursor` | `game/art/spr_pp_menu_cursor.png` (measured) | `game/sprites_src/title/spr_pp_menu_cursor.png` | 16x8 | 2 | 2 | 0 px | PASS | `queued` |
| `spr_pp_title_logo` | `game/art/spr_pp_title_logo.png` (measured) | `game/sprites_src/title/spr_pp_title_logo.png` | 448x64 | 2 | 3 | 0 px | PASS | `done` |
| `spr_pp_window` | `game/art/spr_pp_window.png` (measured) | `game/sprites_src/title/spr_pp_window.png` | 72x8 | 9 | 3 | 0 px | PASS | `done` |
| `spr_title_bubble` | `game/art/spr_title_bubble.png` (measured) | `game/sprites_src/title/spr_title_bubble.png` | 48x16 | 3 | 2 | 0 px | PASS | `done` |
| `spr_title_car` | `game/art/spr_title_car.png` (measured) | `game/sprites_src/title/spr_title_car.png` | 192x32 | 3 | 3 | 0 px | PASS | `redrawn` |
| `spr_title_cloud` | `game/art/spr_title_cloud.png` (measured) | `game/sprites_src/title/spr_title_cloud.png` | 72x16 | 3 | 2 | 0 px | PASS | `queued` |
| `spr_title_cone` | `game/art/spr_title_cone.png` (measured) | `game/sprites_src/title/spr_title_cone.png` | 96x40 | 1 | 1 | 0 px | PASS | `queued` |
| `spr_title_exhaust` | `game/art/spr_title_exhaust.png` (measured) | `game/sprites_src/title/spr_title_exhaust.png` | 64x16 | 4 | 2 | 0 px | PASS | `queued` |
| `spr_title_konrad` | `game/art/spr_title_ronan.png` (measured) | `game/sprites_src/title/spr_title_konrad.png` | 128x16 | 8 | 3 | 0 px | PASS | `queued` |
| `spr_title_sign` | `game/art/spr_title_sign.png` (measured) | `game/sprites_src/title/spr_title_sign.png` | 384x24 | 4 | 2 | 0 px | PASS | `queued` |
| `spr_title_zander` | `game/art/spr_title_theo.png` (measured) | `game/sprites_src/title/spr_title_zander.png` | 128x16 | 8 | 5 | 0 px | PASS | `queued` |
| `spr_title_wheel` | `game/art/spr_title_wheel.png` (measured) | `game/sprites_src/title/spr_title_wheel.png` | 64x16 | 4 | 3 | 0 px | PASS | `queued` |
| `spr_player_ow` | `game/art/spr_player_ow.png` (retired) | none | retired, kept at `assets/retired_art/spr_player_ow.png` | | | | | `retired` |
| `spr_gate_sentry_ow` | `game/art/spr_gate_sentry_ow.png` (retired) | none | retired, kept at `assets/retired_art/spr_gate_sentry_ow.png` | | | | | `retired` |
| `spr_pp_portrait_percy` | `game/art/spr_pp_portrait_percy.png` (no file at that path) | `game/sprites_src/chars/spr_pp_portrait_percy.png` | 48x48 | 1 | 4 | 0 px | PASS | `queued_by_eye` |
| `spr_pp_portrait_prometheus` | `game/art/spr_pp_portrait_prometheus.png` (no file at that path) | `game/sprites_src/chars/spr_pp_portrait_prometheus.png` | 48x48 | 1 | 4 | 0 px | PASS | `queued_by_eye` |
| `hadrian_ow_v2` | `game/art/hadrian_ow_v2.png` (no file at that path) | `game/sprites_src/chars/hadrian_ow_v2.png` | 128x16 | 8 | 3 | 0 px | PASS | `queued_by_eye` |
| `ts_exterior` | `game/art/ts_exterior.png` (no file at that path) | `game/sprites_src/env/ts_exterior.png` | 256x64 | 1 | 13 | 0 px | PASS, 57 checks, 0 failed (tools/check_ts_exterior.py, which runs nes_check --type background on this sheet) | `queued_by_eye` |

Notes on the table:

- Four rows never had a file at the `game/art` path at all (`spr_pp_portrait_percy`,
  `spr_pp_portrait_prometheus`, `hadrian_ow_v2`, `ts_exterior`). The eye round that wrote them read the
  shipped copy under `output/PrimordialParadox/art` and guessed the folder. Their measured numbers
  survive the repoint unchanged, which is the useful part: it confirms the eye read the right file and
  only wrote the wrong path.
- `ts_exterior` is a tileset, not a sprite sheet, so its check is `python tools/check_ts_exterior.py`
  (57 checks, 0 failed, which itself runs `nes_check.py --type background`). `nes_check --type sprite`
  is the wrong rule set there: a background tile may carry four opaque colours, so the sprite rule
  fails 64 tiles on a legal set.
- Statuses were not advanced by this card except where the row is retired. A green `nes_check` is a
  palette and grid verdict, not an art reading, so a row whose palette defect is measured gone is left
  where the art lane left it, with a `status_note` saying exactly that.

## The four rows that could not simply be repointed

1. `game/art/spr_title_ronan.png` -> row renamed **`spr_title_konrad`**, path
   `game/sprites_src/title/spr_title_konrad.png`. Shipped sheet 128x16, 8 frames of 16x16, 3 entries,
   0 off palette, PASS. The retired name is kept in the row as `retired_row_id`.
2. `game/art/spr_title_theo.png` -> row renamed **`spr_title_zander`**, path
   `game/sprites_src/title/spr_title_zander.png`. 128x16, 8 frames, 5 entries, 0 off palette, PASS.
   New finding written on the row: the shipped sheet spends $0F, $00, $02, $10 and $28 and does not
   spend the hero blue $21 or $31 that the row's `palette_roles` list, so the repoint surfaces a
   palette question for gamedev.
3. `game/art/spr_player_ow.png` -> **row retired**, not repointed. No copy of this name exists under
   `game/sprites_src`; the overworld walker draws the `chars/spr_*_ow` sheets (`zander_ow_v2`), so
   repointing it would point the row at the wrong sheet.
4. `game/art/spr_gate_sentry_ow.png` -> **row retired** for the same reason.

Both retired rows carry a `retired` block: the reason, the superseding sheet, the sha256 of the file at
retirement, where the only copy is kept, and the tool that can redraw it. `path` is null and the check
block says no check applies.

## The two orphans, and why nothing was destroyed

`game/art` held 22 PNGs and one index. Twenty of the PNGs were a copy of a tracked
`game/sprites_src` sheet, or output a tracked generator can redraw. Two were the only copy in the tree:

| file | sha256 | sheet |
| --- | --- | --- |
| `spr_player_ow.png` | `112d5a97b5abd2f8b3327ad367d9c31cba5b139b1c56bd052db5ba79c0fa6e89` | 128x16, 8 frames, 5 entries, PASS |
| `spr_gate_sentry_ow.png` | `f4be8f6c5cf01ec5e001e2e8f7789d1cec844f8014d60a72e83f97538df92248` | 128x16, 8 frames, 4 entries, PASS |

Both were copied to `assets/retired_art/` and the copies were hash checked against the originals before
the folder was removed (`assets/retired_art/README.md` says why they are there).
`tools/art/make_redraw_rows.py` can redraw both anyway, and now writes `output/redraws/`.

## What was deleted, and the inventory at deletion

`game/art` was untracked and gitignored (`.gitignore` line 12), so `git ls-files game/art` was 0 files
and no clone could reproduce a number measured there. The folder was removed on 2026-10-23 after the
decisions above were written into the queue. Hashes at deletion, so a later reader can tell one copy
from another:
```
05aa520ce2be spr_pp_font8.png          6a15feed3f25 spr_pp_menu_cursor.png
a81769b063de spr_pp_title_logo.png     97c151655451 spr_pp_window.png
86ac8767d37c spr_title_bubble.png      3761de598e96 spr_title_car.png
7dfdc8574553 spr_title_cloud.png       af2ee90bf212 spr_title_cone.png
31fda8151a90 spr_title_exhaust.png     3c38713e52b7 spr_title_ronan.png
ef43d057fe94 spr_title_sign.png        9588989b1bba spr_title_theo.png
df864fa266e4 spr_title_wheel.png       f4be8f6c5cf0 spr_gate_sentry_ow.png (archived)
112d5a97b5ab spr_player_ow.png (archived)
96b705b02c9b title_L1_sky.png    89b9f4cdbd7f title_L2_clouds.png
9d576abfc3f3 title_L3_downs.png  28bcaf258d09 title_L4_fields.png
98b19591674e title_L5_verge.png  50fd81df7308 title_L6_road.png
3e304d838dc2 title_L7_fg.png     95dd9799a159 title_manifest.json
```

Reproducibility was then checked rather than assumed: the three redraw tools were re-run into
`output/redraws/` on 2026-10-23 and they reproduced seven of the deleted sheets byte for byte, the two
archived orphans included: `spr_pp_font8` `05aa520c`, `spr_pp_window` `97c15165`, `spr_title_bubble`
`86ac8767`, `spr_pp_title_logo` `a81769b0`, `spr_title_car` `3761de59`, `spr_player_ow` `112d5a97`,
`spr_gate_sentry_ow` `f4be8f6c`. The other sheets in the folder were copies of tracked
`game/sprites_src` files or title world layers the world generator draws. Running the tools also proved
the real point of the redirect: `game/art` did not come back.

## The code that pointed at the folder

- `.gitignore`: line 12 (`game/art/`) and the six comment lines above it are gone. A four line note
  records the retirement, so a later reader does not restore the rule and with it the folder.
- `tools/sync_art.py`: the docstring said the mirror copies into `game\art\` while the code writes
  `game\datafiles\art\`. Fixed, and the `--check` stale messages now name
  `game/datafiles/art/` instead of `game/art/`.
- `tests/test_make_font_row.py`: `COMMITTED` now points at `game/sprites_src/title/spr_pp_font8.png`,
  the shipped sheet. The byte comparison needs one honest adjustment: the shipped sheet spends $20
  while the tool's default ink is $30 and which of the two ships is the font row's open Q2, so the
  test builds the tool's output in the ink the sheet actually spends and refuses any ink that is
  neither. Every other assertion in the file is unchanged. The contact sheet test was red before this
  card (`contact()` had grown a logo band argument) and is now green, with the same intent: the canvas
  is the widest band plus one margin, and the font strip fits inside it.
- `tools/art/make_font_row_v2.py`: `glyph_frames()` takes an optional `ink`, and the tool writes its
  redraw to `output/redraws/` instead of the retired folder.
- `tools/art/make_title_rows_v2.py` and `tools/art/make_redraw_rows.py`: same move to
  `output/redraws/`. Without this, the next run of either tool would have recreated `game/art`, which
  is the one thing this card exists to stop.
- `data/sprite_redraw_queue.json`: the repoint, the two renames, the two retirements, and a
  `measured_source` block on every row with the sidecar and the sha256. `mirror_note` now says the
  question is answered instead of describing a folder that is gone.

## Checks, run on 2026-10-23 after the deletion

```
python tools/sync_art.py --check        art mirror is current: 105 animations        exit 0
python tools/sync_data.py               copied 1, removed 0, 69 unchanged            exit 0
python tools/sync_data.py --check       datafiles mirror is current: 70 files         exit 0
cmp data/sprite_redraw_queue.json game/datafiles/sprite_redraw_queue.json             byte identical
python tools/check_data.py              check_data: all files pass                   exit 0
python tools/palette_synergy.py --gate  0 gated failure(s), 6 advisory               exit 0
python tools/check_ts_exterior.py       57 checks passed, 0 failed                   exit 0
python -m pytest tests/test_make_font_row.py tests/test_sprite_pipe.py \
    tests/test_title_art_v2.py tests/test_palette_synergy.py -q     56 passed          exit 0
```

`tools/check_build_inputs.py` still reports three findings, all of them the audio lane's uncommitted
`pp_05_small_ship_v4.ogg` and `percy_theme_v2.ogg`, which were red before this card and are not art.

## What is left for gamedev

1. **Which white the font ships.** The shipped sheet spends $20 #f8f8f8, which no ui sprite palette
   carries; this lane's tool draws $30 #fcfcfc, which all four do. The row's Q2, still open. The test
   now accepts either and says so.
2. **The car's lights.** The shipped sheet is three entries and palette clean; the seven entry redraw
   with the headlight, tail light and beige door lived in the retired folder. It is reproducible rather
   than lost: `tools/art/make_redraw_rows.py` now writes `output/redraws/` and was run there on
   2026-10-23 (byte identical to the copy that was deleted). Whether the car takes those lights is a
   change to `tools/art/title_car_v2.py`, which owns the name.
3. **Zander's palette_roles.** The shipped sheet does not spend the hero blue $21/$31 the row lists.
   Either the sheet is wrong or the row is; gamedev owns both.
4. **`spr_pp_title_logo` is closed.** Card t_e5338932 ported spec 14's crack into
   `tools/art/title_logo_v2.py` on 2026-10-23, after the parent card's ruling, so the shipped sheet now
   carries it: 330 gold pixels in frame 0 and 629 in frame 1, measured here. The row's own text said the
   crack was still outstanding; this card corrected it rather than repeating it.
