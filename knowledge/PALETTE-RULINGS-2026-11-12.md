# PALETTE AND CLASSIFICATION RULINGS 2026-11-12

gamedev rulings for card `t_8df7aab4`, the four decisions D1 to D4 that card `t_ed17952d`
(AUTO-SPRITE-NEXT) recorded in `data/sprite_redraw_queue.json` under `open_rows_2026_11_12`.
Every number below was measured in this repository on 2026-11-12 by the tool named beside it.
Nothing was quoted from a card, and no picture was taken on faith.

D1 holds 2 rows, D2 holds 2, D3 holds 9 and D4 holds 1, which is the 14 rows this block names; card
`t_ed17952d` counted 16 open rows because its count includes the two rows already retired before it.
11 of the 14 close on this card: 2 are `done` (`spr_title_konrad`, `ts_exterior`) and 9 are `retired`
(the R18 candidates). 3 stay open (`spr_title_zander`, `spr_pp_portrait_percy`,
`spr_pp_portrait_prometheus`), each with the question that was blocking it now answered and the
remaining work carded to the lane that draws.

---

## 1. D1 and D2 are ONE defect, and it is a measurement defect

Both pairs of rows were held by a `palette_synergy` question, and in both the tool was measuring a
layer that the game draws OVER the sheet and calling it the sheet's ground or its body.

- D1: `tools/art/make_title_bust_v2.py` crops the car's glass pane as the bust's ground, and the crop
  includes the car BODY, which the car draws after the bust. The body is `$20` there, so the pane read
  as two grounds. Measured, that is the whole wall.
- D2: a dialogue bust draws its own interior in `$02`, the dialogue window's fill. The tool takes the
  largest fill as the figure's BODY, so the body was the box's fill, and body against a ground that is
  that same fill can never clear 3:1. Measured, that is the whole wall, and it needs no rule change.

Both are fixed by removing the over-drawn layer from the measurement, not by adding an entry, not by
reclassifying a sheet, and not by weakening a rule. The sentence that follows is the ruling:

**A measurement must not count a layer the game draws over the sheet as that sheet's ground or as its
body.** A ground is the pixels the sheet is drawn ON. A body is a colour the sheet itself paints as
the figure. The car body, the pillars, the roof edge and the bust's own window-fill panel are neither.

---

## 2. D1: the `$20` in the car's glass is the car body, so the busts stand on `$0C` alone

### 2.1 The two panes, measured

`game/sprites_src/title/spr_title_car.png` is 192x32, three frames of 64x32, 96 8x8 tiles of which 25
are distinct, sha256 `6525913013b3b97d...`. `tools/art/title_car_v2.py` paints it on three entries:
BODY `$20` (`#f8f8f8`, the largest fill), SHADOW `$0B`, DARK `$0C`. The glass band is rows 8 to 15 and
`compose_title_preview.window_openings()` finds TWO openings, not one:

| opening | columns | rows | `$0C` glass | `$20` body | transparent |
| --- | --- | --- | --- | --- | --- |
| rear window | x 11 to 25 | 8 to 15 | 103 px | 14 px | 3 px |
| front window | x 29 to 45 | 8 to 15 | 132 px | 4 px | 0 px |

The 14 px in the rear pane is not a second surface. It is the car's single diagonal moonlight glint,
`GLINT_FROM (13, 9)` to `GLINT_TO (23, 15)`, painted in BODY. The 4 px in the front pane are the raked
A pillar, also BODY. Both are the same entry as the wings, the roof and the sills.

### 2.2 Why it is not ground: the draw order the generator already wrote down

`tools/art/make_title_bust_v2.py` `build_ground()` docstring, lines 178 to 180, says it in words:

> The pane, not the whole 16x16 box: the head is 12 wide and 8 rows tall and the window is the 11 x 8
> it fills, while the pillars and the roof are the car body, which is drawn OVER the bust and is
> therefore not ground.

`game/scripts/pp_title/pp_title.gml` draws the busts behind the car, and the car body paints its own
pixels, so a `$20` pixel is never a pixel the bust stands on: it is a pixel that covers the bust. The
crop never implemented the sentence, which is why the pane measured two entries.

### 2.3 The three routes the card named, all measured

1. **The `$20` streak comes out of the car sheet. Refused.** It is the car's only read on the glass:
   the v2 repaint (card `t_1738de73`) put the body on `$20` because `$0B` read 1.00:1 against itself
   and the glint is the single light mark on an otherwise flat dark band. It would also buy nothing:
   with the glint recoloured `$0C` the pane is one entry and the same result is reached (measured: 0
   failing pairs), so deleting the art buys exactly what masking the body buys, and costs the art.
2. **The busts are classified again, as layers. Refused.** `knowledge/PALETTE-RULINGS-2026-10-25.md`
   section 2 tables both as figures because each has ONE ground, the car interior behind the glass, and
   section 2's closing sentence refuses the declaration as a way around a figure that cannot be drawn.
3. **An entry between the two. Not needed, and it costs a row.** The band that clears 3:1 on both
   `$0C` (luminance 0.0437) and `$20` (0.9387) is luminance 0.232 to 0.271, and exactly two master
   entries sit there: `$17` `#e45c10` at 0.2419 and `$23` `#9878f8` at 0.2689. No title sprite row
   carries either, and the cheapest way to carry one is to spend an entry currently used by a shipping
   sheet: `$28` on sp0 (the logo, 230 tiles), `$09`/`$00`/`$20` on sp1 (the sign, 144 tiles), and so on.
   That is a row spent to answer a question that has a free answer.

**Ruling: the body comes out of the ground, by masking the ground crop, and nothing else moves.** The
glint stays on the car, the busts stay figures, no palette entry moves, and no rule changes.

### 2.4 What landed, and what it measures

`tools/art/make_title_bust_v2.py` `build_ground()` now masks every non-glass pixel of the pane to alpha
0 and prints the count. `palette_synergy.ground_pixels()` skips alpha 0 by design, so the ground set
becomes the glass and the question becomes the real one. No rule code was touched.

| reading | before | after |
| --- | --- | --- |
| `python tools/art/make_title_bust_v2.py` | pane entries `['#004058', '#f8f8f8']` | 14 car-body px masked, pane entries `['#004058']` |
| `python tools/palette_synergy.py --scene title --background output/spr_title_konrad_ground.png --sprite output/redraws/spr_title_konrad.png` | FAIL, 8 failing pairs (body `$28` on `$20` at 1.67:1, once per frame) | **PASS, 0 failing pairs**, 8 frames, body `$28`, `palettes that fit [0]`, 32 inked 8x8 tiles, 0 uncovered |
| `python tools/nes_check.py output/redraws/spr_title_konrad.png --type sprite` | PASS | PASS, 128x16, 32 tiles, 3 colours |

So `spr_title_konrad` is `done`: its check passes, its ground is ruled, and its measured numbers are in
the row. The redraw is `output/redraws/spr_title_konrad.png`, 8 frames of 16x16, three entries
`$0F $00 $28`, which is title sp0 exactly.

**Named cost, one entry.** `data/scene_palettes.json` `hero_palettes.konrad` is `$0F $00 $27` (amber
`#fca044`), not `$0F $00 $28` (gold `#f8b800`), and the row's own generator docstring says otherwise.
The title's sp0 carries `$28`, and re-solving sp0 to `$27` would repaint the logo's 230 tiles, which are
carried by sp0 and nothing else. Konrad's title bust therefore spends the title's gold and not his
reserved amber. It is one entry, both read as amber, and it is written here rather than passed silently.

### 2.5 The passenger, `spr_title_zander`: which row, measured

Zander's shipped sheet fails for a reason D1 does not touch. It is 128x16 with five entries
(`$0F $00 $02 $10 $28`) and a 16x16 frame is read WHOLE by R6 (RULE 0, amendment on card `t_af6fd431`),
so it needs one row and no row carries five entries. Measured on the ruled ground it is still 16 failing
pairs: 8 `sprite_tile` and 8 `palette_count`, one per frame. That is a redraw, and the redraw needs a
row and a named colour set.

`hero_palettes.zander` is `$0F $21 $31` and no title sprite row carries it. The four rows and the sheets
that spend them, measured per 8x8 tile over every PNG in `game/sprites_src/title/`:

| row | entries | the shipping sheets it carries, and nothing else does |
| --- | --- | --- |
| sp0 | `$0F $00 $28` | `spr_pp_title_logo.png`, 230 tiles |
| sp1 | `$09 $00 $20` | `spr_title_sign.png`, 144 tiles |
| sp2 | `$0C $10 $20` | `spr_title_cloud.png`, `spr_title_bubble.png`, `spr_title_star.png` |
| sp3 | `$0C $0B $20` | `spr_title_car.png` 69 tiles, `spr_title_wheel.png` 16 tiles |

Re-solving sp1 to `$0F $21 $31` was measured as the obvious way to give Zander his blue: it uncovers all
144 of the sign's tiles, because `$09 $00 $20` is the only row in the file that carries the sign. That is
a sign repaint, not a bust palette.

**Ruling: Zander's bust is drawn in title sp1 `$09 $00 $20`, and his body is `$20`.** The reason is the
glass, measured: on `$0C` the candidates read `$20` 10.55:1, `$10` 5.90:1, `$00` 2.68:1, `$09` 1.97:1,
`$28` 6.32:1, `$0C` 1.00:1 and `$0B` 1.28:1, and of sp1's three entries only `$20` clears 3:1 and is two
rows away in the same reading. So his figure is white, his mid is `$00` grey and his outline is `$09`,
which is a different hue family from the teal glass, which is what RULE 0 point 2 asks of an outline.

**Named cost.** He is not in his reserved light blue. A title bust that reads light blue needs a title
sprite row carrying `$21` and `$31`, and the cheapest way to get one is a repaint of the sign's 144
tiles. The row stays `queued` with the ground, the row, and the body named, so the lane can draw it now.

---

## 3. D2: the ui scene spends skin on its two spare rows, and the `$02` interior comes out of the sprite layer

`spr_pp_portrait_percy` and `spr_pp_portrait_prometheus` are 48x48, redrawn by cards `t_255c054d` and
`t_a61c01b7`, and both are held by two questions. Both are answered here with the same measurement.

### 3.1 Q1: yes, and it is two rows, and they are the two rows nothing spends

Per 8x8 tile, measured on the three shipped sheets (the guard is included because it is the same
generator and the same question):

| sheet | tile colour sets, with the panel drawn | 1 px ring |
| --- | --- | --- |
| guard | `{02 30}` x12, `{02 0F 30}` x10, `{02 0F}` x6, `{02 0F 36}` x4, `{0F 30}` x2, `{0F 36}` x2 | `$30`, 188 px |
| percy | `{02 0F 30}` x17, `{02 30}` x7, `{02 0F}` x6, `{0F 30 36}` x4, `{0F 36}` x2 | `$30`, 188 px |
| prometheus | `{02 0F 28}` x12, `{02 28}` x10, `{02 0F}` x6, `{02 0F 36}` x4, `{0F 28 36}` x2, `{0F 36}` x2 | `$28`, 188 px |

With the panel kept, the three sheets between them need five sprite rows: `{02 0F 30}`, `{02 0F 36}`,
`{0F 30 36}`, `{02 0F 28}` and `{0F 28 36}`, and the ui scene has four. Two of the four are not spare:

| ui row | entries | the shipping sheet that needs it |
| --- | --- | --- |
| sp0 | `$0F $28 $30` | `spr_pp_ui_enemy.png`, `{0F 28 30}` on 7 tiles |
| sp1 | `$0F $00 $30` | `spr_pp_ui_party.png`, `{00 0F 30}` on 6 tiles |
| sp2 | `$0F $00 $28` | nothing: the cursor is `{28}`, which sp0 and sp2 both carry |
| sp3 | `$02 $00 $30` | nothing |

`data/palettes/scene_ui.json` says of sp3 in its own notes: "sp3 is spare; the screens need 3 sprite
palettes". Measured, sp2 is spare too.

**So the panel comes out of the sprite layer**, and it is the only reading that fits: `$02` is the
dialogue window's fill, a BACKGROUND colour that `bg0` (`$02 $30 $00`) already carries on every 16x16
area the window covers, and a portrait that paints it as sprite pixels is spending sprite entries on the
box. With every `$02` pixel transparent, the same three sheets need two rows:

| sheet | tile colour sets, panel out | row that carries all 36 tiles |
| --- | --- | --- |
| guard | `{30}` x12, `{0F 30}` x12, `{0F}` x6, `{0F 36}` x6 | `{0F 30 36}` |
| percy | `{0F 30}` x17, `{30}` x7, `{0F}` x6, `{0F 30 36}` x4, `{0F 36}` x2 | `{0F 30 36}` |
| prometheus | `{0F 28}` x12, `{28}` x10, `{0F}` x6, `{0F 36}` x6, `{0F 28 36}` x2 | `{0F 28 36}` |

**Ruling: sp2 becomes `$0F $28 $36` and sp3 becomes `$0F $30 $36`, and every `$02` pixel of the three
bust sheets becomes transparent.** Measured, that lands as:

| sheet | `palettes that fit` | body | failing pairs against the real map crop |
| --- | --- | --- | --- |
| guard | `[3]` | `$30` | 1, and it is the ground's own `$20` |
| percy | `[3]` | `$30` | 1, and it is the ground's own `$20` |
| prometheus | `[2]` | `$28` | 1, and it is the ground's own `$20` |

The single remaining problem on each is `set_member` on a BACKGROUND colour: `$20` under the sprite is
not in any of the ui scene's four background palettes. That is the capture's own 16 px of white, the
pair the earlier cards already named as belonging to the capture and not to the sprite.

No shipped ui sprite sheet moves: the cursor is `{28}` (sp0 or sp2), the party is `{00 0F 30}` (sp1),
the enemy is `{0F 28 30}` (sp0). `spr_pp_ui_window.png` (`{02 0F 30}`) and `spr_pp_ui_tab.png`
(`{02 0F 28}`) need `$02` and are carried by no sprite row today either: they are nine-slice tile sheets
that `pp_window_draw()` draws as background, and they fit `bg0` and `bg1` as background rows.

### 3.2 Q2: a framed portrait IS in scope for R1b, and it passes once its panel is not sprite pixels

The 48x48 bust is a tiled layer by the size test (`is_sprite_frame`), so R1b is the rule that judges it,
and that is the right rule: the bust is drawn over a room, it has no feet, and the question is whether
the pixels under it can be told from it. What the tool measured was not that question, because the body
it took was the largest fill, which was the box's own `$02` panel, and the ground was `$02` as well, so
the pairing was 1.00:1 by construction.

With the panel out, the largest fill is the figure itself and the rule passes on its existing two
instruments, with no amendment:

| pair | contrast |
| --- | --- |
| body `$30` (guard, percy) on `$0F` | 20.47:1 |
| body `$30` on `$00` | 4.07:1 |
| body `$30` on `$20` | 1.02:1, and the ink `$0F` is 19.77:1 there |
| body `$28` (prometheus) on `$0F` | 11.85:1 |
| body `$28` on `$00` | 2.35:1, and the ink `$0F` is 5.03:1 there |

The ground is `output/spr_pp_portrait_ground_map.png`, the 48x48 crop at (16,120) of the shipped
dialogue capture: `$0F` on 2112 px, `$00` on 176 and `$20` on 16. R1b asks that the ink OR the body
clear the floor, so every one of those pairs clears.

**So no rule change is asked for and none is made.** The classification was never the problem: the
panel was.

### 3.3 What is carded, and why it is not landed here

The change is a drawing change inside the owning generator plus two palette rows, and the palette rows
are only legal together with the drawing: re-solving sp2 and sp3 before the panels are transparent would
leave the ui set with no row carrying `$02` while the shipped sheets still paint it. One card carries
both halves, with the target rows and the exact operation in its body.

---

## 4. D3: the nine R18 candidate rows retire, and the numbers that retire them

Every one of the nine rows carries `path: null` and the note that gamedev has no ruling on the asset, so
nothing can be promoted. The question was "promote with a named slot and palette row, or retire". Both
classes are measured against what the game can draw.

### 4.1 The three 32x32 portraits retire: two have no subject and the third duplicates a shipped sheet

- **Zeus and Kronos are not in the game.** `data/enemies/all.json` carries four enemy ids
  (`navy_sailor`, `percy`, `deck_hound`, `morgan`) and `data/enemies/roster.json` seven sheets; neither
  name appears in either file, and `data/encounters/all.json` has five encounters
  (`tutorial_sailors`, `deck_hound`, `deck_collapse`, `percy`, `morgan_gate`). A 32x32 cell for a
  character no encounter names is art for a slot nobody has named.
- **Percy already ships at the size the battle screen draws.** `percy` is an encounter, its enemy row
  names `spr_pp_percy`, and `game/sprites_src/enemies/percy_big.png` is 192x80. The candidate cell is
  32x32, which is one frame of the 96x32 enemy sheets, so it is a smaller duplicate of a sheet that
  exists.
- The slot arithmetic agrees: `data/ui_layouts.json` gives the battle screen two 32x32 enemy slots (tile
  3,8 and tile 12,11) and three 24x32 party slots, `battle_b` gives its one enemy a 64x80 frame, and
  `game/scripts/pp_dialogue/pp_dialogue.gml` makes a dialogue portrait 48x48 at `PP_PORTRAIT_X 16`,
  `PP_PORTRAIT_Y 120`. There is no 32x32 portrait slot on any screen.

### 4.2 The six 256x240 plates retire: a plate is not a screen the PPU can build

Measured, distinct 8x8 tile bitmaps per candidate:

| candidate | tiles | distinct 8x8 | palettes used |
| --- | --- | --- | --- |
| `halls_room` seed 141 | 960 | 540 | 4 |
| `high_street` seed 141 | 960 | 463 | 2 |
| `town_quay_hurricane` seed 141 | 960 | 154 | 1 |
| `halls_room` seed 149 | 960 | 649 | 2 |
| `high_street` seed 149 | 960 | 606 | 2 |
| `town_quay_hurricane` seed 149 | 960 | 499 | 2 |

A background is one pattern table of 256 tiles (`knowledge/ART-BIBLE.md` 1.1 rule 4), 512 on the
console with the sprite table counted. Every one of the six needs more than 256 distinct tiles and three
need more than both tables together. A plate is therefore concept art, not a screen, and the screen it
would become is built from a tileset, which is the tool that owns that name
(`tools/art/make_battle_bg.py`, `tools/art/make_exterior_maps.py`). The row's own `check` command is
`nes_check --type sprite`, which is the wrong rule set for a 256x240 background as well, the same defect
the `ts_exterior` row already had and fixed.

**Ruling: all nine rows retire.** Nothing is promoted and nothing is redrawn. A candidate comes back
as an asset when all three of these exist: a slot in `data/ui_layouts.json` (or a tileset that already
owns the name), a sprite or background row in the scene file that carries its colour set, and a reader
in GML that draws it. Measured today, none of the nine has the first.

---

## 5. D4: `ts_exterior`'s "tiles too busy to read as parts" is not a defect, and the inventory and the budget are these

`python tools/check_ts_exterior.py` returns **PASS, 58 checks, 0 failed** (the row records 57, so one
check was added since it was written; nothing failed then and nothing fails now). Measured on
`game/sprites_src/env/ts_exterior.png`: 256x64, 64 tiles of 16x16, 256 8x8 subtiles of which 204 are
distinct, 13 entries, the largest entry 26.7 percent of the pixels, and every 16x16 tile inside the
budget:

| 16x16 tile colour set | tiles |
| --- | --- |
| `{00 0F}` | 16 |
| `{00 0F 10 30}` | 8 |
| `{00 0F 10}` | 7 |
| `{07 0F 17 28}` | 6 |
| `{09 0A 0F 2A}` | 5 |
| `{00 0F 16 30}` | 4 |
| `{09 0A 0F}`, `{02 12 30}`, `{07 17}`, `{07 0F 28}`, `{07 0F 17}`, `{00 16 30}`, `{00 0F 16}`, `{00 07 09 0F}`, `{0F}`, `{09 0A 2A}`, `{00 10 30}` (x2) | 1 to 2 each |

Eighteen distinct colour sets, and the largest of them is three entries plus the shared backdrop `$0F`,
which is the rule. "Busy" is not a number any tool in this tree measures, and a redraw would have to
beat a check that already passes.

**The colour budget per 16x16 attribute area, stated: three entries plus the one shared backdrop
`$0F`.** Per frame a scene spends at most 4 background palettes (`knowledge/ART-BIBLE.md` 1.2 and the
generator's `enforce_palette_budget()`), which is why the atlas may declare more groups than a scene
uses: it is a pool a scene picks four from, and the three composed town frames measure 8 distinct
colour sets covered by 3 palettes of the 4 allowed.

**The tile list, stated: the sidecar's own inventory is the list, and it is unchanged.** 24 feature
groups and 64 named tiles: road (4), kerb (2), pavement (3), cobbles (3), brick walls (3), shop front
(4), doors (2), windows (2), phone box (2), post box (1), hedge (2), tree (4), lamp post (2), bollard
(1), quay stone (3), water (2, animated `water_a`/`water_b`), railing (2), bench (1), traffic light (2),
crosswalk (1), Big Ben (4), cathedral (4), and the trim tiles the groups share. That inventory is
gamedev's and it does not change on this card.

**One real defect found while measuring, and it is not the row's:** the sidecar's `rule` string still
reads "NES: 5 background palettes of 3 entries, a scene spends at most 4 of them", and the file now
declares SIX (`bg0_stone`, `bg1_brick`, `bg2_green`, `bg3_water`, `bg4_red`, `bg5_plant`). The rule text
is stale, nothing measures it, and it is a one line fix in the generator that writes the sidecar.

**Ruling: the row is `done`.** The palette is legal, the inventory is this document's, the budget is the
hardware's, and there is no defect to fix.

---

## 6. What landed on this card

- `tools/art/make_title_bust_v2.py`: `build_ground()` masks the car body out of the pane and prints the
  count, so the ground file is the glass the bust stands on. This is the D1 ruling in code.
- `data/sprite_redraw_queue.json`: `spr_title_konrad` done, `ts_exterior` done, the nine R18 rows
  retired, `spr_title_zander` and the two portraits carry the ruling that unblocks them, and a
  `rulings_2026_11_12` block records the four decisions in one place.
- `knowledge/ART-BIBLE.md` RULE 0 point 2: one sentence, pointing here, that a measurement must not
  count a layer drawn over the sheet as its ground or its body.
- Two cards for the work this ruling does not draw: the three bust sheets' panel plus the two ui rows,
  and the `ts_exterior` sidecar's stale rule text.
- The ruling, the ART-BIBLE amendment and the ground crop are committed. The queue edit itself is
  NOT: `data/` is a consequential class in `manager/guard/suite_config.json`, and the only review
  artifact root is `projects/arananet/manager/reviews`, so a lane cannot commit its own data change
  and this card has no second lane to sign it. The queue carries the same numbers as sections 2 to 5
  of this file and waits on disk for a lane that is not gamedev to commit it.

## 7. Checks run on this tree, 2026-11-12, and what they returned

- `python tools/art/make_title_bust_v2.py`: 14 car-body px masked, pane entries `['#004058']`.
- `python tools/palette_synergy.py --scene title --background output/spr_title_konrad_ground.png
  --sprite output/redraws/spr_title_konrad.png`: PASS, 0 failing pairs, 8 frames, body `$28`,
  `palettes that fit [0]`, 32 inked tiles, 0 uncovered.
- `python tools/nes_check.py output/redraws/spr_title_konrad.png --type sprite`: PASS, 128x16, 32
  tiles, 3 colours.
- `python tools/check_ts_exterior.py`: PASS, 58 checks, 0 failed.
- `python tools/palette_synergy.py --gate`: 10 entries, 0 gated failure(s), 3 advisory failure(s), 0 not
  measured, exit 0, report `output/palette_synergy.json`. Both D1 and D2 were measured with
  `frame_report` directly against ad hoc grounds, which never enter the gate, so the gate number is
  unchanged by this card and that is the honest reading.
- The per sheet, per opening and per tile numbers are from measurement scripts in this card's
  workspace that call `palette_synergy.Grid`, `frame_report`, `scene_palette_set.scene`,
  `contrast_check.load_palette` and `compose_title_preview.window_openings` rather than restating the
  arithmetic.

## 8. What this does not decide

- **The title's four sprite rows as a set.** Zander's light blue needs a row that carries `$21` and
  `$31`, and the only free ones are spent on the logo (sp0, 230 tiles) and the sign (sp1, 144 tiles).
  A title repaint that re-solves the four rows together is its own card, with its own price.
- **Konrad's gold versus his reserved amber.** `$28` ships on the title, `$27` is his hero entry, and
  moving the title to `$27` repaints the logo. Named in 2.4, not changed.
- **The two ui scene rows' effect on the menu and battle screens.** sp2 and sp3 are re-solved for the
  busts; measured, no shipped ui sprite sheet spends either, so the cursor, the party and the enemy
  keep their rows. Whether sp2's `$00` grey leaves the sprite union matters only to a future sheet that
  wants it, and none exists.
- **A judged row for the portraits.** The three bust sheets are on no `judged` row today, so the gate
  cannot see them; the ruling gives the two ui rows and the classification, and writing the row is the
  card that lands the drawing.
- **`spr_pp_ui_enemy` in `make_ui_nes.py`, and `spr_pp_ui_party`'s `$0F $30 $00`.** Both were carried
  forward from earlier cards and both are still open. Measured here for the first time, the party sheet
  is `{00 0F 30}` on 6 tiles and `{00}` on 2, so the triple the old note asks for is not what the
  sheet spends; the enemy sheet is `{0F 28 30}` and is carried by sp0. Neither blocks a row that this
  card closes.

Provenance: studied this repository's own files only (`data/sprite_redraw_queue.json`,
`data/scene_palettes.json`, `data/palettes/scene_title.json`, `data/palettes/scene_ui.json`,
`data/ui_layouts.json`, `data/enemies/all.json`, `data/enemies/roster.json`, `data/encounters/all.json`,
`knowledge/ART-BIBLE.md`, `game/scripts/pp_dialogue/pp_dialogue.gml`, `game/scripts/pp_config/pp_config.gml`,
`tools/palette_synergy.py`, `tools/scene_palette_set.py`, `tools/art/contrast_check.py`,
`tools/art/title_car_v2.py`, `tools/art/make_title_bust_v2.py`, `tools/art/compose_title_preview.py`,
`tools/check_ts_exterior.py`, the title sheets, the three portrait sheets, the ui sheets,
`game/sprites_src/env/ts_exterior.json` and the R18 candidate cells under `output/art_candidates_r18/`).
No decompiled material, and no expression from another game, is in this card. Copied expression: none.


## 9. The sprite redraw queue reopens: seven rows, four of them with a measured failing pair

Card `t_80024831` (AUTO-SPRITE-NEXT) closed the queue at 52 entries, 41 done and 11 retired, and asked two
questions instead of opening a row, because a row's priority and `palette_roles` are this lane's. Both are answered
here. Every number in this section was measured on this tree on 2026-11-12 by the command named beside it.

### 9.1 What reproduces, and the four counts in the card that do not

Reproduced exactly: `data/sprite_redraw_queue.json` held 52 entries, 41 `done`, 11 `retired`, 0 queued.

Re-measured, and different:

| reading | the card says | measured today | how |
| --- | --- | --- | --- |
| sprite sheets under `game/sprites_src`, with the card's exclusions | 97 | 95 | 155 PNGs in the tree, minus `title_L*`, `title_BG_*`, `ts_*`, `*_tiles` and `bg_*` |
| sprite sheets with no queue row | 69 | 67 | the 95 minus the 28 a row already names |
| of those, named somewhere in the project | 31 | 61 | 47 in the `.yyp` resource list only, 8 as a literal `.gml` string, 6 as a data JSON string |
| named nowhere at all | 38 | 6 | the six `spr_pp_icon_*` sheets, with the caveat below |
| title fade and flash twins | 21 over six bases | 22 over five bases | car 4, cloud 4, cone 4 plus `_flash`, exhaust 4, sign 4 plus `_flash` |

Caveat on the last row of the table: "appears nowhere in the tree" is not "no reader asks for it", because a name
can be built as well as written. `pp_battle_director.gml:1469` builds a hero's battle sheet as
`string(_id) + "_battle"`. The six are the set whose stem appears in no file at all; treat that as an upper bound on
dead art and not as a list of it.

And one reading in the card that is true but narrower than it looks. Its "0 true failures" is a
`python tools/nes_check.py --type sprite` number, and that rule asks the palette, the 8x8 grid and the per-tile
colour ceiling. It does not ask whether a sheet can be told apart from the ground the game draws it over. Four of the
seven sheets below cannot.

### 9.2 Q1: seven rows open, and the standard for the ones that do not

**The standard.** A row opens for a sheet the game resolves by name (a literal string, a data value, or a name the
GML builds) and that either fails a rule on a ground the game draws it over, or carries an open art question a later
lane can act on. A sheet that is named and clean is recorded by measurement, not by a row: the queue is a work list,
not an inventory. That narrows the file's own `rule` string, and the narrowing is written into the file so the next
reader does not have to re-derive it from here.

All seven sheets the card asked about are resolved by name by a reader, and each is carried by exactly one sprite row
of the scene that draws it, measured per 8x8 tile against the rows
`tools/scene_palette_set.py:199 allowed_sprite_rows` returns:

| sheet | px, frames | entries | the row that carries every tile | reader | status |
| --- | --- | --- | --- | --- | --- |
| `spr_pp_knife` | 64x16, 4 of 16x16 | `$0F $21 $31` | zander, 16 of 16 tiles | `pp_battle_draw_slash`; `data/items.json:16` names it as the item's sprite | done, P2 |
| `spr_pp_master_bolt` | 128x32, 4 of 32x32 | `$0F $21 $31` | zander, 64 of 64 | the same, and `pp_battle_draw_power_fx` (`:2195`) | done, P2 |
| `spr_pp_trident` | 128x32, 4 of 32x32 | `$0F $12 $28` | percy, 64 of 64 | `pp_battle_draw_slash` | queued, P1 |
| `spr_pp_bident` | 128x32, 4 of 32x32 | `$0F $03 $23` | hadrian, 64 of 64 | the same | queued, P1 |
| `spr_pp_adamantine_scythe` | 128x32, 4 of 32x32 | `$0F $00 $27` | konrad, 64 of 64 | the same | queued, P1 |
| `spr_pp_portrait_guard` | 48x48, 1 | `$0F $30 $36` | ui sp3, 36 of 36 | `pp_dialogue.gml:410`, `"spr_pp_portrait_" + _bust`, `data/dialogue/all.json` | done, P2 |
| `spr_title_star` | 24x8, 3 of 8x8 | `$0C $10 $20` | title sp2, 3 of 3 | `pp_title.gml:1033` | queued, P1 |

`nes_check --type sprite` PASSes all seven on this tree. That is why the card could see nothing wrong. What that rule
cannot see is section 9.3.

The guard's `ui sp3` is the row section 3.1 of this file re-solved this morning and card `t_299de3bc` landed
(`$0F $30 $36`): the guard bust is the sheet that arithmetic was for, it ships with no `$02` pixel, and its 36 tiles
are the reason sp3 stops being spare. On the dialogue ground crop the sprite side measures 0 of 12 pairs failing; the
2 pairs the tool still reports are the capture's own `$00` and `$20`, the pair section 3.2 names.

Not opened, and why: the 61 named sheets with no row (nothing measured wrong on any of them, and a row each would be
an inventory), and the six `spr_pp_icon_*` sheets (named in no `.yyp` entry, no `.gml` string and no data JSON, so no
reader is known; that is a dead-art question for the tree-cleanup lane, not a redraw).

### 9.3 The four rows that carry a failing pair, and the fix that costs no entry

`pp_battle_draw_slash(_battle, _enemy_slot)` (`pp_battle_director.gml:1702`) centres the sheet on the ENEMY's slot,
so a weapon's ground is the enemy's own cells and not the party's. On the deck strip, the strip the tutorial fight
runs on, those cells are `bg2 $00 $30 $02` plus the shared backdrop `$0F`
(`data/palettes/scene_battle_deck_night.json`; ruling 15 of `knowledge/PALETTE-RULINGS-2026-10-25.md` for why the
enemy is background art there). A strip whose enemy cells carry `$02` (wardroom's bg2 is `$02 $01 $30`) shows the
same pairs, which is why each row names the ground it was measured on.

| sheet | verdict | the failing pair, as the tool prints it |
| --- | --- | --- |
| knife | PASS, 0 | none |
| master_bolt | PASS, 0 | none |
| trident | FAIL, 2 | `body $12 reads 2.17:1 and its ink $0F reads 1.73:1 on ground $02`, on the frames at 0,0 and 32,0 |
| bident | FAIL, 2 | `body $03 reads 1.32:1 and its ink $0F reads 1.73:1 on ground $02`, then `2.28:1` and `1.00:1` on `$0F`, on the frame at 64,0 |
| scythe | FAIL, 4 | `body $00 reads 2.91:1 and its ink $0F reads 1.73:1 on ground $02`, once per frame |

and the star, against the live sky `$11` it twinkles over before the sky fades: `body $10 (row 1) and ground $11
(row 1) are 0 luminance row(s) apart at 2.19:1` on the frames at 8,0 and 16,0. Frame 0 passes because its body is
`$20`.

**The fix is the car's fix (card `t_1738de73`, section 11 Q2 of the 2026-10-25 file) and it costs no palette entry:
the largest fill of every frame moves onto the light entry the row already carries.** Measured with the tool's own
luminance table:

| row | largest fill today | target | on `$02` | on `$0F` | on `$00` | on `$30` |
| --- | --- | --- | --- | --- | --- | --- |
| percy `$0F $12 $28`, trident | `$12`, 2.17:1 | `$28` | 6.86:1 | 11.85:1 | ink 5.03:1 | ink 20.47:1 |
| hadrian `$0F $03 $23`, bident | `$03`, 1.32:1 | `$23` | 3.69:1 | 6.38:1 | ink 5.03:1 | ink 20.47:1 |
| konrad `$0F $00 $27`, scythe | `$00`, 2.91:1 | `$27` | 5.94:1 | 10.25:1 | ink 5.03:1 | ink 20.47:1 |
| title sp2 `$0C $10 $20`, star | `$10`, 2.19:1 on the sky | `$20` | 11.46:1 | 19.77:1 | 3.93:1 | ink 19.77:1 |

R1b asks the ink OR the body to clear 3.0:1 on every ground shown, so the ink column is what carries `$00` and
`$30`. Every target is already on its sheet and inside its own row, so no scene palette moves, no sheet leaves its
row and no rule changes. `master_bolt` is the proof the target works: its largest fill is already the pale `$31` and
it measures 0 failing pairs.

For the star there is a second reading worth naming rather than hiding: a star is a light source and not a figure
standing on ground, and an exemption on those lines would weigh the same as the layer clause. This ruling does not
grant it, because the free fix exists and the live sky is the ground for the opening frames of the shot. The row
records both readings.

### 9.4 Q2: the twins stay derived, and each base row carries its own

22 sheets over 5 bases, all 22 named in `PrimordialParadox.yyp` and in the generated art index
`game/datafiles/art/title_manifest.json`, and all drawn by name: `pp_title_fade_name(name, level)` builds
`<name>_fade<level>`, `pp_title_flash_name` (`pp_title.gml:563`) builds `<name>_flash`, and the intro draws the whole
world through the first of those (`pp_title_draw_intro_scene`, `pp_title.gml:974`).

Three things in the tree already treat them as derived, and each would go red if that stopped being true:

- `tools/pp_intro_art.py write_fades` writes `<name>_fade1` to `<name>_fade4` from the base beside it, for the five
  sprite animations and the seven parallax strips, and `python tools/pp_intro_art.py --check` exits 0 on this tree
  today, which is the measurement that every committed twin is the twin of the base that ships.
- The order is enforced, not hoped for: `tools/art/scene_palette.py apply_title` ends by calling `write_fades()` and
  `rebuild_flash()` (`:836`, `:844`), so the pass that repaints a base is the pass that rewrites its twins.
- `tests/test_intro.py:159` pins every committed fade strip to the fade of the base committed beside it, by name.

**Ruling: no row per twin.** Each of the five base rows names its own twins in a `twins` field with the generator and
the pin, the way `spr_title_exhaust` carried its four after card `t_474cde50`. A twin is redrawn by redrawing its base
and re-running the generator; it can never be redrawn on its own, because the next `apply_title` overwrites it. If a
twin ever fails a rule that is the base row's failing pair, and the measurement that says so is `--check`.

### 9.5 AUTO-SPRITE-NEXT does not retire, and here is the job it has

The card's third option was to retire itself while the set is clean. The set is not clean; it was unmeasured on the
one question that decides whether an overlay is visible. 95 of 95 sheets are palette and grid legal, and that is a
real guarantee, but four of the seven sheets this card opened fail the ground question on the ground the game draws
them over, and none of them had ever had a row. So the card keeps its name, its next run takes the four P1 rows, and
the measurement that closes each row is the same command that opened it.

What would let it rest is the check it has never had: a sweep that measures every drawn sheet against the ground the
GML draws it on, at the placement the GML draws it at. The 95 of 95 number is a `nes_check` number and there is no
equivalent R1b number for the whole set. That is a follow-up card, not this one.

### 9.6 What landed on this card

- This section.
- `data/sprite_redraw_queue.json`: 7 entries, 4 `queued P1` and 3 `done P2`, each with its path, frames, entries, the
  scene row that carries it, its reader, its failing pair and its fix; a `twins` field on `spr_title_car`,
  `spr_title_cloud`, `spr_title_cone`, `spr_title_exhaust` and `spr_title_sign`; a `queue_reopened_2026_11_12` block
  carrying 9.1 and 9.2; `count` from 52 to 59; the `rule` string narrowed; one sentence added to `count_note`. No
  pre-existing entry's status, priority, path or measured number moved.

No drawing. The four redraws are rows, not files.

### 9.7 Checks run on this tree, 2026-11-12, and what they returned

- `python tools/nes_check.py <sheet> --type sprite` on all seven: PASS each (64x16 16 tiles; 128x32 64 tiles four
  times; 48x48 36 tiles; 24x8 3 tiles; three colours each; worst 8x8 tile 3 opaque, the guard's 2).
- `python tools/palette_synergy.py --scene battle_deck_night --background output/bg_battle_deck_night_frame.png
  --sprite <weapon> --at 24,64` on the five weapons: PASS on knife and master_bolt, FAIL 2 on trident, FAIL 2 on
  bident, FAIL 4 on scythe.
- `python tools/palette_synergy.py --scene title --background output/cloud_sky_ground.png --sprite
  game/sprites_src/title/spr_title_star.png --frame-w 8 --frame-h 8 --at 0,0`: FAIL, 2 failing pairs, 3 inked 8x8
  tiles, 0 uncovered.
- `python tools/palette_synergy.py --scene ui --background output/spr_pp_portrait_ground_map.png --sprite
  game/sprites_src/chars/spr_pp_portrait_guard.png --frame-w 48 --frame-h 48 --at 0,0`: 0 of 12 sprite pairs failing,
  the 2 reported pairs belonging to the capture.
- `python tools/pp_intro_art.py --check`: exit 0, so every fade and flash twin is the twin of its base as committed.
- `python tools/palette_synergy.py --gate`: 10 entry(ies), 0 gated failure(s), 3 advisory failure(s), 0 not
  measured, exit 0.
- `python tools/check_ts_exterior.py`: 58 checks passed, 0 failed, exit 0.

The per-sheet, per-tile and per-pair numbers come from scripts that call `palette_synergy.Grid`,
`scene_palette_set.allowed_sprite_rows` and PIL directly instead of restating arithmetic, and the queue rows carry the
numbers they measured.

### 9.8 What this does not decide

- **The 61 named sheets with no row.** Nothing measured wrong on them. They get rows when a ground measurement or an
  art question says so, and section 9.1 is the inventory so the next card does not redo it.
- **The six `spr_pp_icon_*` sheets.** No known reader, so no row and no verdict. Dead art or art from a cut plan, and
  either way a cleanup question.
- **The star's band plan.** `data/palettes/scene_title.json band_sprites` excludes it on purpose ("the intro is a
  different shot with its own fade art, and giving it a band plan of its own is a separate card"). The row carries
  the `$20` fix and the band question together.
- **Aeson's knife in Zander's triple.** `data/characters/party.json` gives the hero `spr_pp_hero` and
  `dads_good_knife`, and the sheet spends `$0F $21 $31`, which is Zander's triple. It is legal (a party_cast
  strip's four sprite rows ARE the four hero triples) and it is recorded as an art reading, not changed. The item
  icon reading of the same sheet (frame 0 on the icons ground) is not judged here: no built scene draws an item icon
  yet, card `t_f5253687` already drew a separate 16x16 cell for it, and that row holds the open question of which of
  the two kept icons the inventory uses.
- **The guard's dialogue ground.** The 2 pairs that fail on the crop are the capture's own `$00` and `$20`, section
  3.2's question; nothing about the sprite is open.
- **The twins' R1b.** Section 6 of `knowledge/PALETTE-RULINGS-2026-10-25.md` already says a fade twin is drawn while
  the ground fades under it, so the unfaded ground is not its ground. Nothing here changes that.

Provenance: built by reading this repository's own files (`data/sprite_redraw_queue.json`,
`knowledge/PALETTE-RULINGS-2026-11-12.md`, `knowledge/PALETTE-RULINGS-2026-10-25.md`, `data/scene_palettes.json`,
`data/palettes/scene_battle_deck_night.json`, `data/palettes/scene_title.json`, `data/items.json`,
`data/characters/party.json`, `game/scripts/pp_battle_director/pp_battle_director.gml`,
`game/scripts/pp_title/pp_title.gml`, `game/scripts/pp_dialogue/pp_dialogue.gml`, `game/PrimordialParadox.yyp`,
`game/datafiles/art/title_manifest.json`, `tools/palette_synergy.py`, `tools/nes_check.py`,
`tools/scene_palette_set.py`, `tools/pp_intro_art.py`, `tools/art/scene_palette.py`, `tools/art/make_god_weapons.py`,
`tools/art/make_dialogue_busts.py`, `tests/test_intro.py`, and the seven PNGs with their sidecars). No decompiled
material and no expression from another game is in this card. Copied expression: none.
