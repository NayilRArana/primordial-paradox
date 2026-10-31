# SPRITE ROUND 2026-10-25, card t_b15e9c7a

Written by the assistant profile for card `t_b15e9c7a` (AUTO-SPRITE-NEXT). Every number below was
measured in this repository on 2026-10-25 by the command named beside it.

## 1. What was redrawn

`spr_pp_ui_enemy`, the 32x32 battle enemy frame, from `queued_by_eye` to `done`.
Tool: `tools/art/make_ui_frames_v2.py`. The frame is three flat rings, written row by row: ink `$0F`
on the outside, white `$30` inside it, gold `$28` filling the block.

| | before, `game/sprites_src/ui/spr_pp_ui_enemy.png` | after, `output/redraws/spr_pp_ui_enemy.png` |
| --- | --- | --- |
| colours | 2, `$f8b800` 900 px and `$fcfcfc` 124 px | 3, `$f8b800` 784 px, `$fcfcfc` 116 px, `$000000` 124 px |
| drawn px | 1024 | 1024 |
| boundary px on the darkest entry | 0 of 124, 0.0 percent | 124 of 124, 100.0 percent |
| palette coverage | tiles fit sp1 and sp2 | every one of the 16 tiles is `$0F $30 $28`, ui sp0 `[15, 40, 48]`, 0 uncovered |
| `nes_check.py` | PASS | PASS, 32x32 16 tiles 3 colours |
| `palette_synergy.py` | PASS, 0 failing pairs | PASS, 0 failing pairs |

The ground is `output/spr_pp_ui_enemy_ground.png`, the 32 x 32 at (160, 88) of
`game/sprites_src/ui/screens/ui_battle.png`: sky `$0F` 288 px and floor `$00` 736 px, cropped where no
block is drawn.

Commands, all run:

    python tools/art/make_ui_frames_v2.py --audit
    python tools/nes_check.py output/redraws/spr_pp_ui_enemy.png --type sprite
    python tools/palette_synergy.py --scene ui --background output/spr_pp_ui_enemy_ground.png \
        --sprite output/redraws/spr_pp_ui_enemy.png --frame-w 32 --frame-h 32

`output/sprites_v2_sheet.png` is 1024 x 4448 and carries the row as a band at 4x at y 3654, found by
comparing the sheet pixels against the redraw. The band is one picture, not two: the block is opaque
over its whole frame, so a second band on its floor would show the same pixels.

## 2. What could not be redrawn, and why it is arithmetic

`spr_title_konrad` and `spr_title_zander` were redrawn first and then left queued, because the row's
own check refuses them and no drawing can change it.

The only ground the two busts have is the car's glass pane: `spr_title_car.png` at x 11 to 25, rows 8
to 15, which is 15 x 8 px. Measured, it holds `$0C` on 103 px (88.0 percent) and `$20` on 14 px (12.0
percent), the diagonal reflection streak. On a window that carries both, the title's four sprite
palettes have no answer:

| entry | on `$0C` | on `$20` | verdict |
| --- | --- | --- | --- |
| `$0F` | 1.87:1, 0 rows | 19.77:1 | refuses the glass |
| `$00` | 2.68:1, 0 rows | 3.93:1 | refuses the glass |
| `$28` | 6.32:1 | 1.67:1, 0 rows | refuses the streak |
| `$10` | 5.90:1 | 1.79:1, 1 row | refuses the streak |

Contrasts measured with `tools/art/contrast_check.py` on the 2C02 luminances.

The `$10` row is a probe drawn in title sp2 (`$0C $10 $20`) and run through `palette_synergy.py` on
that pane: 4 of 8 pairs still fail. So no entry of any title sprite palette clears both ends, and the
pane's two entries sit two luminance rows apart, which is the same arithmetic that made the exhaust
puff a tiled layer on card `t_474cde50`.

The redraw of Konrad still exists and is legal on its own terms: `output/redraws/spr_title_konrad.png`,
8 frames of 16x16 from hand written 12x12 grids, three entries `$0F` ink, `$00` grey and `$28` gold,
which is `hero_palettes.konrad` exactly, `nes_check.py` PASS, and all 32 inked 8x8 tiles of the strip
covered by title sp0 with 0 uncovered. It is not landed and not marked done.

`spr_pp_ui_party` carries the same boundary defect (0 of 108 boundary pixels on the darkest entry) and
is left `queued_by_eye`: an ink ring over its grey body and white keyline needs the set `$0F $30 $00`,
which none of the ui scene's four sprite palettes carries.

## 3. Q: for gamedev

1. **The title busts' ground is two entries, not one.** `knowledge/PALETTE-RULINGS-2026-10-25.md`
   section 2 tables `spr_title_konrad` and `spr_title_zander` as figures because their window is one
   ground, the car interior behind the glass. Measured, the pane is `$0C` 103 px and `$20` 14 px on a
   15 x 8 box, two rows apart at the ends. Either the `$20` reflection comes out of the car sheet, or
   the two busts are classified again, or they get an entry that sits between the two. All three are
   gamedev's, and until one is answered neither row can pass its own check.
2. **The battle enemy frame's new sheet has to be landed by the tool that owns the name.**
   `tools/art/make_ui_nes.py` still draws the two colour block, and the redraw sits in
   `output/redraws` the way the cone and the puff did. Moving it is a change to the owner tool.
3. **The party placeholder needs a palette it does not have** before its boundary can be ink.

## 4. Note on the checks

`python -m pytest tests/test_project.py -q -k "dash or queue"`: 1 passed, 22 deselected.
`python -m pytest tests/test_make_font_row.py tests/test_palette_synergy.py tests/test_scene_palette_set.py -q`:
57 passed, 1 failed. The failure is `test_scene_palette_set.py::test_build_reproduces_the_file_on_disk`
on the `ship` scene's sprite palettes, which this card did not touch: no file under `game/sprites_src`
or `data/palettes` was written by `t_b15e9c7a`.
