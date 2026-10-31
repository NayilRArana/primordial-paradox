# SPRITE ROUND 2026-10-25, card t_d8fd83fd

Written by the assistant profile for card `t_d8fd83fd` (AUTO-SPRITE-NEXT). Every number below was
measured in this repository on 2026-10-25 by the command named beside it.

## 1. Which row, and why this one

The queue at `data/sprite_redraw_queue.json` holds 31 rows and 20 were done when this card started.
Taken in priority order, the highest unfinished row is `spr_title_konrad` (P1), and it is the same row
card `t_b15e9c7a` measured and left queued: its only ground is the car's 15 x 8 glass pane, which holds
`$0C` on 103 px and `$20` on 14 px, and no entry any title sprite palette carries clears 3:1 on both
ends. That is an open Q: on gamedev, not a drawing fault, so no redraw of it can pass and it stays
queued. `spr_title_zander` sits in the same pane and is refused by the same arithmetic.

The next row is `spr_title_sign` (P1), the distance road sign, and it is the one this card took. Its
own check already passed on the shipped sheet, so the redraw had to pay for itself on the craft rule
the row names, SP-025, an outline on the side the ground is.

## 2. What was redrawn

`spr_title_sign`, 384 x 24, four frames of 96 x 24, from `queued` to `done`.
Tool: `tools/art/make_title_sign_v2.py`. The plate is a nine slice of nine hand written 8 x 8
character grids (corner, edge, fill) stamped into the frame, one pixel per character; the lettering is
stamped from the project's own 5 x 7 glyph table, the same one `tools/art/make_title_world.py` draws
the shipped sign with, so no second font is authored and nothing is scaled, recoloured or traced.

| | before, `game/sprites_src/title/spr_title_sign.png` | after, `output/redraws/spr_title_sign.png` |
| --- | --- | --- |
| entries | 2: `$09` 6710 px, `$20` 2506 px | 3: `$09` 5798 px, `$20` 2474 px, `$00` 944 px |
| largest entry | `$09`, 72.8 percent | `$09`, 62.9 percent |
| drawn px | 9216, fully opaque frames | 9216, fully opaque frames |
| outline edge | 0 of 944 outer boundary px in the plate's ink | 944 of 944 |
| worst 8 x 8 tile | 2 opaque colours | 3 opaque colours, ceiling 3 |
| `nes_check.py` | PASS, 144 tiles, 2 colours | PASS, 144 tiles, 3 colours |
| `palette_synergy.py` | PASS, 0 failing pairs, body `$20` `[1]` | PASS, 0 failing pairs, body `$20` `[1]` |
| sha256 | `86621d7f44ddeaea7f86aa1e50b927d34bc848d4657214ff32b1d7dbba112cec` | `6f6168a0e197cdc09d2d272c011b94913d1421de80a61fcc5a4c8cf49146d292` |

The shipped sheet is untouched: the generator that owns the name is `tools/art/make_title_world.py`
`sign_plate()`, and moving it onto this plate is gamedev's call (Q2 below).

The ground is `output/spr_title_sign_ground.png`, 96 x 24 at 30,154: the seven shipped title layers
composed at camera 0 with the sign left out, cropped at `data/title.json`'s `sign.x`, `sign.y` over the
verge layer's own y. It holds `$0B` `#005800` 1057 px, `$09` `#007800` 1055 px and `$0F` `#000000`
192 px.

Measured contrasts on the 2C02 table, with `tools/art/contrast_check.py`: body `$20` reads 5.36:1 on
the verge `$09`, 8.25:1 on `$0B` and 19.77:1 on `$0F`, so R1b clears on every ground colour under the
plate. The `$00` edge is the craft outline and not the separation: it reads 1.36:1 on `$09`, 2.10:1 on
`$0B` and 5.03:1 on `$0F`. The checker's own "darkest entry" for this sheet is `$09`, because
`#007800` measures 0.134 against `#7c7c7c` 0.202 on that table, which is why the plate's edge is `$00`
and its face is `$09` rather than the other way round.

Commands, all run, the last three on Pine:

    python tools/art/make_title_sign_v2.py
    python tools/art/make_title_rows_v2.py
    python tools/nes_check.py output/redraws/spr_title_sign.png --type sprite
    python tools/palette_synergy.py --scene title --background output/spr_title_sign_ground.png \
        --sprite output/redraws/spr_title_sign.png --frame-w 96 --frame-h 24 --at 0,0

Pine, through `projects/arananet/pine/pine_offload.py --shards 1 --name signcheck3 --cmd "...python
tools/art/make_title_sign_v2.py && python tools/nes_check.py ... && python tools/palette_synergy.py
..."`, `data/results/offload-signcheck3-0.json`: exit 0, `NES sprite check: PASS`, `palette_synergy
title on output/spr_title_sign_ground.png: PASS, 1 sprite file(s), 0 failing pair(s)`. The generator
ran on the far side because the zip carries only the files git tracks under `output/`, so an untracked
redraw is not in it (the first attempt, `offload-signcheck2-0.json`, stopped at `output/redraws/
spr_title_sign.png does not exist`, exit 1).

`output/sprites_v2_sheet.png` is 1024 x 4592 and carries the row as one band at 2x at (32, 3880),
found by a full pixel search of the sheet for the redraw. It is one band and not two: the plate is
opaque over its whole frame, so a band on the verge would show the same pixels.

The sheet still reports 4 `sprite_tile` problems at y 3208, in a band above the sign's. They are not
this row's: with the sign band switched off the same 4 tiles are reported, so they belong to an
earlier band, and they are left for the row that owns that band rather than papered over here.

A vision check on `output/sign_redraw_4x.png` (1536 x 96, 4x) read the four frames back as
BASINGSTOKE 20 over SOUTHAMPTON 55, BASINGSTOKE 8 over SOUTHAMPTON 43, WINCHESTER 12 over SOUTHAMPTON
30, WINCHESTER 2 over SOUTHAMPTON 20, lettering legible, each plate with a dark edge, a white keyline
and a green face.

## 3. Q: for gamedev

1. **The row's palette_roles name entries the scene cannot carry.** They list `$0F` ink, `$30` white
   letters, `$09` green border and `$0B` green shade. `data/palettes/scene_title.json` gives
   `spr_title_sign` sp1, which is `[$09, $00, $20]`, and `$0F`, `$30` and `$0B` are in no title sprite
   palette this name can reach. The redraw spends sp1's three. May the row's palette_roles be rewritten
   to sp1's triple, the way the logo row's were rewritten to sp0's three on 2026-10-23?
2. **Who lands it.** `tools/art/make_title_world.py` `sign_plate()` owns `spr_title_sign`, so this
   redraw sits in `output/redraws` and the shipped sheet stays at sha256 `86621d7f`. May the title lane
   move `sign_plate()` onto this nine slice plate, which adds the SP-025 ink edge and leaves the game's
   own `SIGN_TEXTS` count down untouched?

## 4. Note on the checks

`python tools/art/make_title_rows_v2.py` rebuilt the contact sheet and its own bands print as before;
`python -m pytest tests/test_make_title_world.py -q` was not run on this card, and no test file was
edited: the redraw is a new tool and a new scratch sheet, and nothing under `game/sprites_src` or
`data/palettes` was written.
