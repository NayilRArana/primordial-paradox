# SPRITE-ROWS-2026-10-23: two P0 title rows redrawn, and what game/art actually is

Card t_265cabb7 (AUTO-SPRITE-NEXT). Two rows of `data/sprite_redraw_queue.json` are now `done`, both drawn by
`tools/art/make_title_rows_v2.py`, and both pass `tools/nes_check.py --type sprite`.

## 1. What was on disk before this card looked

The queue has fifteen rows and three were already `redrawn` (the player, the car, the gate sentry). The highest
priority row not done is `spr_pp_font8` (P0), and it could not be finished; section 3 says why. The next two P0
rows were `spr_pp_window` and `spr_title_bubble`, and both are fixed here.

Measured on 2026-10-23 with `tools/nes_check.py` and a PIL colour count, on both copies of every title sheet:

| sheet | game/sprites_src/title | game/art (before) |
| --- | --- | --- |
| spr_pp_font8 | 592x8, 1 colour, PASS | 352x8, 1 colour `#c8c8d4`, off palette at 564 px, FAIL |
| spr_pp_menu_cursor | 16x8, 2 colours, PASS | 16x8, 3 colours, 3 problems |
| spr_pp_title_logo | 448x64, 3 colours, PASS | 448x56, 4 colours, 211 problems |
| spr_pp_window | 72x8, 3 colours, PASS | absent |
| spr_title_bubble | 48x16, 2 colours, PASS | 42x10, 2 colours, 4 problems |
| spr_title_cloud | 72x16, 2 colours, PASS | 72x12, 5 colours, 7 problems |
| spr_title_cone | 96x40, 1 colour, PASS | 90x40, 2 colours, 3 problems |
| spr_title_exhaust | 64x16, 2 colours, PASS | 48x10, 2 colours, 8 problems |
| spr_title_sign | 384x24, 2 colours, PASS | 356x16, 4 colours, 48 problems |
| spr_title_wheel | 64x16, 3 colours, PASS | 40x10, 3 colours, 4 problems |
| spr_title_ronan | absent (superseded by spr_title_konrad) | 96x12, 8 colours, 16 problems |
| spr_title_theo | absent (superseded by spr_title_zander) | 96x12, 6 colours, 14 problems |
| spr_title_car | 192x32, 3 colours, PASS | 192x32, 7 colours, PASS |

Every live sheet passes the hardware rule. Eleven of the twelve `game/art` copies fail it and one is missing.
The eye's 2026-10-22 complaint ("three of the seven sprites are one colour") is about the LIVE sheets, not about
`game/art`: the font and the cone really are one colour there, and that is a separate, artistic row.

## 2. The two rows this card closes

Both were drawn as character grids in the new tool, one letter per pixel, palette looked up in
`data/nes_palette.json` only, then measured. Neither replaces a gamedev design: after the redraw, each file is
pixel identical to the live sheet beside it (0 of 576 and 0 of 768 pixels differ), so the queue no longer
measures a third, stale copy.

| row | before in game/art | after | nes_check |
| --- | --- | --- | --- |
| spr_pp_window | absent | 72x8, 9 frames of 8x8, 3 colours ($20 white outer line, $0B dark green inner line, $0F ink fill), worst tile 3 opaque | PASS, 9 tiles, 3 colours |
| spr_title_bubble | 42x10, frame off the tile grid, 4 problems | 48x16, 3 frames of 16x16, 2 colours ($10 light grey body, $0C dark teal outline and dots), worst tile 2 opaque | PASS, 12 tiles, 2 colours |

`tools/palette_synergy.py --scene title --background output/nes_title_frame.png` on the pair:

- the bubble fits a scene sprite palette: title sp2 (12/16/32 = $0C, $10, $20), R6 passes on all three frames.
  Its R1 body_ground failures come from the tool's automatic placement, which stands the frame on the bottom
  road band; a bubble hangs in the sky, so that pair is the pairing warning the tool's own docstring describes.
- the window fails R6 on all nine frames: it spends $0F, $0B and $20 and no title sprite palette carries that
  triple (sp0 15/0/40, sp1 9/0/32, sp2 12/16/32, sp3 12/11/32). See the Q: below.

Contact sheet: `output/sprites_v2_sheet.png`, 640x1152, seven bands at 4x (the five cast rows plus the window and
the bubble). The cast bands are drawn in memory from `tools/art/make_characters_v2.py`; no cast sheet on disk
was rewritten by this card.

## 3. Why the font row is not finished

`spr_pp_font8` is the highest priority row left and its defect is real: the live sheet is one colour ($20 white),
so every glyph is a flat light mass with no weight, and SP-045 asks a glyph for a light and a dark. The queue's
row offers $30 white, $0F ink and a $02 navy shadow at 1 px. That shadow cannot be drawn: `data/scene_palettes.json`
for the title names `spr_pp_font8` in bg2 and bg3, and those two background palettes share exactly `$0B` dark green
and `$20` white, so a third entry on the sheet breaks the band plan the title is built on.

## 4. Q: for gamedev

- `Q:` The dialogue box interior: `spr_pp_window` paints it `$0F` ink, which is also the title's shared backdrop
  (15). No title sprite palette carries $0F with $0B and $20, so `palette_synergy` R6 fails the sheet on every
  frame. Should the interior be transparent (the backdrop shows through, and the sheet then spends only $0B and
  $20, which sp3 carries) or should a sprite palette be widened to $0F, $0B, $20? Both are palette decisions, and
  the second one moves a scene palette.
- `Q:` The font's second tone: if the band plan holds (bg2 and bg3 share only $0B and $20), the only legal shadow
  is $0B dark green on an ink fill, which is invisible. So SP-045 can only be met by widening the font's band
  palettes or by keeping one ink and dropping the row. Which?
- `Q:` `game/art` reaches nothing that ships: the runtime reads `game/datafiles/art`, which `tools/sync_art.py`
  rebuilds from `game/sprites_src`, and `game/art` is not in git. Should `data/sprite_redraw_queue.json` measure
  `game/sprites_src` (with `game/datafiles/art` as the shipped copy) rather than `game/art`, so that future
  AUTO-SPRITE-NEXT cards measure art that reaches the build? This card followed each row's own path, so it drew
  into `game/art` and kept the drawings identical to the live sheets.
