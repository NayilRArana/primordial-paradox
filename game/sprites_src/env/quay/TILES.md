# QUAY TILES: the tile table the map wiring reads

Drawn by `tools/art/make_quay_tiles.py`. Card R46 (t_abfb6024) drew the vocabulary; card ART-B-MAPS (t_d0566ebc) redrew every tile in art direction B, late NES polish: bold dark outlines, three tone shading lit from the top left, detailed tiles. Do not edit by hand: rerun the tool.

The sheet is `quay_tiles.png`, 128 by 48, 24 cells of 16 x 16, 20 tiles used. The manifest beside it (`quay_tiles.json`) is the machine readable copy of this table.

Colours are ROLES from `data/palette.json`, not hex. The role resolves to one Ricoh 2C02 entry, because the audit's authority on a colour is `data/nes_palette.json` and the design palette's hexes are not 2C02 outputs. The bridge is the table below, and it is written in the manifest too.

| role | 2C02 entry | hex | why that entry |
|---|---|---|---|
| `grey_4` | $00 | #7c7c7c | $00 #7c7c7c is the one neutral mid grey in the 2C02 and it is the wet quay stone |
| `blood_3` | $07 | #881400 | $07 #881400 is the dark brick face and the lit edge of iron after dark |
| `stone_2` | $08 | #503000 | $08 #503000 is the brown one step under the brick, mortar and the iron body |
| `sea_1` | $0C | #004058 | $0C #004058 is the darkest cool output, the wet shadow in a joint and the deep water |
| `ink` | $0F | #000000 | the canonical black $0F, the shared backdrop of every area in both sets |
| `grey_5` | $10 | #bcbcbc | $10 #bcbcbc is the lighter neutral, the sheen a wet slab keeps on its lit edge |
| `blood_4` | $17 | #e45c10 | $17 #e45c10 is the brick face under the lamp and the paint on the barrier rail |
| `sea_2` | $1C | #008888 | $1C #008888 is the harbour's mid swell, one step above the deep water |
| `gold_4` | $28 | #f8b800 | $28 #f8b800 is lamp glass and the lit window's fill |
| `sea_4` | $2C | #00e8d8 | $2C #00e8d8 is the brightest teal, a two pixel glint on a swell and nothing more |
| `gold_5` | $38 | #f8d878 | $38 #f8d878 is the hot core of a window and the lettering on the sign |

## The room palette sets

- **quay_night** (11 roles, cap 16): `ink`, `grey_4`, `grey_5`, `sea_1`, `sea_2`, `sea_4`, `blood_3`, `stone_2`, `blood_4`, `gold_4`, `gold_5`
- **office_night** (10 roles, cap 16): `ink`, `grey_4`, `grey_5`, `sea_1`, `sea_2`, `blood_3`, `stone_2`, `blood_4`, `gold_4`, `gold_5`
- **quay_storm** (11 roles, cap 16): `ink`, `grey_4`, `grey_5`, `sea_1`, `sea_2`, `sea_4`, `blood_3`, `stone_2`, `blood_4`, `gold_4`, `gold_5`

## The four background palettes

| palette | roles | 2C02 entries | what it draws |
|---|---|---|---|
| `bg0_quay_stone` | `grey_4`, `grey_5`, `sea_1` | $00, $10, $0C | wet paving, the coping and the iron that stands on the stone, drawn in the stone's own ramp |
| `bg1_harbour_water` | `sea_1`, `sea_2`, `sea_4` | $0C, $1C, $2C | the harbour: deep water, one step of swell, a glint |
| `bg2_brick_iron` | `blood_3`, `stone_2`, `blood_4` | $07, $08, $17 | the brick frontage, its mortar, and the doors and wood in the same warm ramp |
| `bg3_lamp_glass` | `gold_4`, `gold_5`, `stone_2` | $28, $38, $08 | the light sources: a lit window, the lamp, the sign, with the dark brown that frames them |

## The rules of ART-STYLE.md section 2, measured on this sheet

| rule | measurement on the shipped sheet |
|---|---|
| no orphan pixels | 0 |
| no dithering unless deliberate | 0 patch(es) |
| light from the top left | 360 correct / 15 wrong (ratio 24.0) |
| 2C02 only | 0 off palette pixel(s), and tools/nes_audit_all.py re-checks every entry |
| at most 3 colours besides the backdrop in a 16 x 16 area | enforced while drawing: a tile that leaves its palette raises |

## The tiles

| # | name | char | palette | roles | blob test | what it is |
|---|---|---|---|---|---|---|
| 0 | `quay_paving` | `.` | `bg0_quay_stone` | `grey_4` `grey_5` `ink` `sea_1` | n/a (light 17%, 12 rows no dark, 8 runs, 5 inner dark) | wet flagstone on a bold black joint, a lit top and left edge per slab, the ground of every walk |
| 1 | `quay_paving_worn` | `,` | `bg0_quay_stone` | `grey_4` `grey_5` `ink` `sea_1` | n/a (light 17%, 5 rows no dark, 15 runs, 16 inner dark) | the same stone with a stepped black crack, so a long walk is not one tile repeated |
| 2 | `quay_puddle` | `~` | `bg0_quay_stone` | `grey_4` `grey_5` `ink` `sea_1` | n/a (light 20%, 9 rows no dark, 13 runs, 32 inner dark) | standing water in a low slab: a black lip, one lit edge, two glints |
| 3 | `quay_edge` | `q` | `bg0_quay_stone` | `grey_4` `grey_5` `ink` `sea_1` | n/a (light 14%, 10 rows no dark, 10 runs, 33 inner dark) | the coping at the water, a lit lip and a black drop, the tile that ends the stone honestly |
| 4 | `water_deep` | `w` | `bg1_harbour_water` | `sea_1` `sea_2` `sea_4` | n/a (light 3%, 0 rows no dark, 16 runs, 166 inner dark) | harbour water, frame 1 of 2 |
| 5 | `water_ripple` | `W` | `bg1_harbour_water` | `sea_1` `sea_2` `sea_4` | n/a (light 1%, 0 rows no dark, 19 runs, 175 inner dark) | harbour water, frame 2 of 2: the swell moves three pixels and the glints swap sides |
| 6 | `water_reflection` | `R` | `bg1_harbour_water` | `sea_1` `sea_4` | n/a (light 3%, 0 rows no dark, 20 runs, 188 inner dark) | the lamp's glint path on the water, broken into dashes so the water answers the light |
| 7 | `bollard` | `B` | `bg0_quay_stone` | `grey_4` `grey_5` `ink` `sea_1` | PASS (light 12%, 0 rows no dark, 43 runs, 126 inner dark) | iron bollard on wet stone: a black outline, a lit left edge, a shadow on the right |
| 8 | `chain` | `c` | `bg0_quay_stone` | `grey_4` `grey_5` `ink` `sea_1` | PASS (light 20%, 0 rows no dark, 41 runs, 93 inner dark) | a chain draped between two bollards: one arc with a black shadow under it, the ground showing through |
| 9 | `barrier` | `b` | `bg0_quay_stone` | `grey_4` `grey_5` `ink` `sea_1` | PASS (light 22%, 0 rows no dark, 48 runs, 124 inner dark) | steel barrier across the quay mouth: a lit rail top, two outlined posts |
| 10 | `brick_wall` | `#` | `bg2_brick_iron` | `blood_3` `blood_4` `ink` `stone_2` | n/a (light 11%, 12 rows no dark, 4 runs, 28 inner dark) | the office frontage: two courses, black mortar, a lit top edge per brick |
| 11 | `brick_wall_damp` | `=` | `bg2_brick_iron` | `blood_3` `blood_4` `ink` `stone_2` | n/a (light 11%, 10 rows no dark, 6 runs, 32 inner dark) | the same wall with bricks gone dark where the rain runs |
| 12 | `door_office` | `D` | `bg2_brick_iron` | `blood_3` `blood_4` `ink` `stone_2` | PASS (light 17%, 0 rows no dark, 52 runs, 99 inner dark) | the one door in the block that opens: a lit frame, a handle catching the lamp |
| 13 | `door_shut` | `d` | `bg2_brick_iron` | `blood_3` `blood_4` `ink` `stone_2` | PASS (light 16%, 0 rows no dark, 53 runs, 111 inner dark) | a shut door, boarded, no handle light: seven of these teach the rule |
| 14 | `window_lit` | `o` | `bg3_lamp_glass` | `gold_4` `gold_5` `ink` `stone_2` | n/a (light 5%, 0 rows no dark, 29 runs, 14 inner dark) | a lit window: the room in gold with the hot core at the top left, waived from the light share rule |
| 15 | `window_dark` | `O` | `bg2_brick_iron` | `blood_3` `blood_4` `ink` `stone_2` | PASS (light 10%, 0 rows no dark, 37 runs, 72 inner dark) | the same window with nobody home, glass in the dark ramp |
| 16 | `lamp_base` | `L` | `bg3_lamp_glass` | `gold_4` `gold_5` `ink` `stone_2` | n/a (light 4%, 1 rows no dark, 30 runs, 137 inner dark) | a lamp post and the pool it throws on the stone, waived: it is a light |
| 17 | `sign_board` | `S` | `bg3_lamp_glass` | `gold_4` `gold_5` `ink` `stone_2` | n/a (light 6%, 0 rows no dark, 33 runs, 62 inner dark) | a harbour sign board, lettering as dashes, waived: it is a light |
| 18 | `office_floor` | `f` | `bg2_brick_iron` | `blood_3` `blood_4` `ink` `stone_2` | n/a (light 11%, 0 rows no dark, 30 runs, 27 inner dark) | the dock office boards, a black joint and a lit edge per board |
| 19 | `office_desk` | `k` | `bg2_brick_iron` | `blood_3` `blood_4` `ink` `stone_2` | PASS (light 16%, 0 rows no dark, 34 runs, 79 inner dark) | the office desk Nye works behind, drawn on its own boards |

## How to wire it

1. Every tile is 16 x 16 and index i in the sheet is `floor(i / 8)` rows down and `i % 8` cells across.
2. A tile draws from exactly one background palette, so a 16 x 16 attribute area can never carry a fourth colour. Give the area the palette named in the table and no other.
3. `water_deep` and `water_ripple` are the two frames of one animation; hold each for about 24 game frames, which is the slow swell the night quay wants and not a flicker.
4. Objects stand ON their own ground: `bollard`, `chain` and `barrier` include the paving they sit on, and `door_office`, `door_shut` and the windows include the brick around them, so a map can place them without a transparent layer.
5. The office pair (`office_floor`, `office_desk`) is the same warm ramp, so the interior scene uses the office night set and needs no fifth palette.

## What this set does not do

1. **The light does not spill across tile edges.** A tile carries three colours plus the backdrop, so the lamp's pool is inside its own cell.
2. **There is no building wall above three courses.** The block's upper floors are the same brick tile repeated; a window sill course and a roofline are the next two tiles this set needs.
3. **Nothing here is a sprite.** These are background tiles on the 16 x 16 attribute grid: characters, the clerk and the sailor stand on them and obey the sprite rules in SPRITE-CRAFT, not these.

