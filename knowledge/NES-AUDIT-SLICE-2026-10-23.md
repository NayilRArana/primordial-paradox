# NES audit of the slice, 2026-10-23

Card R41 NES-AUDIT-SLICE (`t_c56b82b3`), the pixel gate of `ROADMAP-2026-10-23.md`. Owner of this page: the audit
lane. This page reruns the NES audit over everything the slice draws and gives one row per artifact, with the
verdict for each rule the card names.

Method, in one line: `tools/nes_audit_all.py` was run from the repo root over the whole tree, and the eight slice
frames the tool's discovery rule does not reach were measured by hand with the same checker it calls,
`tools/nes_composite_check.py`. No checker, rule, palette or piece of art was edited.

The tree moved during this card. The first run at 19:41 saw 160 files. `tools/art/make_quay_tiles.py` landed
`game/sprites_src/env/quay/quay_tiles.png` and two frames at 19:50, and the final run at 19:52 saw 163. Every
number below is from the 19:52 run. The page was written at 20:05 local on 2026-10-22, for the card dated
2026-10-23.

## 1. Verdict

- The tool's own verdict on the whole tree: **PASS**, 163 files, 24 failing, 0 unmeasured, exit 0
  (`output/nes_audit/SUMMARY.json`).
- Gated rows that fail: **0 of 134** (127 shipped art sources and 7 finished frames). Every failing row is a
  contact sheet or a window capture, which the tool marks advisory (`output/nes_audit/SUMMARY.json`).
- Slice artifacts: **15 rows measured, 0 fail the NES rules**, 4 to 11 colours each. One of the five artifacts the
  card names, the game over frame, **is not in the tree**, so its verdict is unknown, not pass. Section 3.
- One criterion as the card words it fails on **15 of 15** rows: no drawn colour is a role in
  `data/palette.json`. That is a defect in the criterion, not fifteen defects in the art. Section 6.
- Nothing here says the art is good. It says the rules the project's own checkers enforce are met.

## 2. The run, pasted

Command, from the repo root, this card:

```
python tools/nes_audit_all.py
```

Output of the run the numbers come from:

```
nes_audit_all: PASS  163 file(s), 24 failing, 0 unmeasured
  palette: data/nes_palette.json (data\nes_palette.json, the 2C02 palette)
  synergy: 6 pair(s), 0 gated failure(s), 6 advisory (report output/palette_synergy.json)
  ...
  page: knowledge\NES-AUDIT.md
  json: output\nes_audit
  3x:   output/nes_audit_worst_3x.png (9694 box(es) on output/music_style_bible_preview.png)
  exit: 0
```

The quiet form of the same gate, rerun at the end of the card:

```
python tools/nes_audit_all.py --quiet
nes_audit_all: PASS, 163 file(s), 24 failing (0 gated), 0 unmeasured, exit 0
```

The palette recipe check, run for the palette first half of the card:

```
python tools/check_palette_recipes.py
PASS palette_recipes: 57 recipes, 4 hero palettes, 8 scene sets, 0 failure(s)
```

What the 163 rows are, from `output/nes_audit/SUMMARY.json`: 127 gated shipped art sources, 7 gated finished
frames, 21 advisory contact sheets, 8 advisory window captures. Of the 24 failures, 20 are contact sheets and 4 are
window captures. No shipped asset and no finished frame fails.

## 3. The five artifacts the card names, and whether they exist

| Artifact the card names | File found | Exists | In the tool's 163 rows | Owner card |
|---|---|---|---|---|
| exterior map frame | `output/southampton_sample_frame.png`, `output/westminster_sample_frame.png`, `output/winchester_sample_frame.png`, all 256x240, written by `tools/art/make_exterior_maps.py` line 611; plus the quay block mock `output/quay_block_preview.png` from `tools/art/make_quay_tiles.py` | yes, 4 frames | the 3 sample frames no, the quay block yes as a gated frame | R28 EXTERIOR-TILESET `t_7d1380f9`, R46 QUAY-TILES `t_abfb6024` |
| dock office frame | `output/quay_office_preview.png`, 256x240, written at 19:50 by `tools/art/make_quay_tiles.py` (lines 34 and 35), sidecar `output/quay_office_preview.json` declaring its backdrop | **yes, landed during this card** | yes, gated frame row, PASS | R46 QUAY-TILES `t_abfb6024` |
| game over frame | none. The only game over asset in the tree is `assets/audio/sfx/game_over.ogg` | **no** | no | R27 GAME-OVER `t_24eab5ff` |
| four battle strips composited | `output/bg_battle_corridor_frame.png`, `output/bg_battle_deck_night_frame.png`, `output/bg_battle_quay_dusk_frame.png`, `output/bg_battle_wardroom_frame.png`, all 256x240, plus `output/enemies_battle_frame.png` with its `output/enemies_battle_mask.png` | yes, 5 frames | no | R48 BATTLE-BG-WIRING `t_59bfc884` |
| the gate text box | `game/sprites_src/ui/screens/ui_dialogue.png` (source) and `output/ui_dialogue_preview.png` (3x frame) | yes | yes, both rows, both PASS | `t_5b27880e` R22, `t_8cd9c10a` R30 |

Why eight of the rows in section 4 are outside the tool: `tools/nes_audit_all.py` treats a file under `output/` as a
finished frame only when its name contains `preview` (lines 256 to 267), and a name starting `title_run_` as a
capture (lines 250 to 255). I counted 31 files in `output/` that are exactly 256x240 and the tool produces 7 gated
frame rows. A 256x240 frame named `*_frame.png` is skipped in silence; the two quay mocks are seen only because
their author named them `*_preview.png`.

## 4. The pass list, one row per artifact

Both colour limits are shown because the card asks for 16 and the tool enforces 25 (`tools/nes_audit_all.py` line
65, `tools/nes_composite_check.py` line 72). 25 is the hardware ceiling: 4 background palettes of 3 plus 4 sprite
palettes of 3 plus one backdrop.

Legend: blended = a pixel that is not one of the 64 PPU outputs; areas = 16x16 attribute blocks carrying more than
3 colours besides the backdrop; groups = distinct background palettes needed, 4 available; CHR = distinct 8x8 tiles
the frame draws, against the 256 a pattern table holds; OAM = sprites against 64, checked only when a sprite mask
is supplied.

| # | Artifact | Path | Colours (16 / 25) | Blended pixels | Areas over | Groups over 4 | CHR tiles (256) | OAM (64) | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | exterior map frame | `output/southampton_sample_frame.png` | 9 / ok | 0 | 0 | 0 | 55 | not checked, no mask | PASS |
| 2 | exterior map frame | `output/westminster_sample_frame.png` | 10 / ok | 0 | 0 | 0 | 85 | not checked, no mask | PASS |
| 3 | exterior map frame | `output/winchester_sample_frame.png` | 8 / ok | 0 | 0 | 0 | 82 | not checked, no mask | PASS |
| 4 | exterior map frame, quay block | `output/quay_block_preview.png` | 11 / ok | 0 | 0 | 0, 4 of 4 spent | 59 | not checked, no mask | PASS |
| 5 | battle strip composited | `output/bg_battle_corridor_frame.png` | 9 / ok | 0 | 0 | 0 | 41 | not checked, no mask | PASS |
| 6 | battle strip composited | `output/bg_battle_deck_night_frame.png` | 8 / ok | 0 | 0 | 0 | 30 | not checked, no mask | PASS |
| 7 | battle strip composited | `output/bg_battle_quay_dusk_frame.png` | 9 / ok | 0 | 0 | 0 | 42 | not checked, no mask | PASS |
| 8 | battle strip composited | `output/bg_battle_wardroom_frame.png` | 9 / ok | 0 | 0 | 0 | 31 | not checked, no mask | PASS |
| 9 | battle sprites over a strip | `output/enemies_battle_frame.png` with `output/enemies_battle_mask.png` | 8 / ok | 0 | 0 | 0, 4 of 4 spent | 40 | 7, busiest line 4 of 8 | PASS |
| 10 | dock office frame | `output/quay_office_preview.png` | 6 / ok | 0 | 0 | 0, 2 of 4 spent | 20 | not checked, no mask | PASS |
| 11 | gate text box, source | `game/sprites_src/ui/screens/ui_dialogue.png` | 5 / ok | 0 | 0 | 0 | 51 | not checked, no mask | PASS |
| 12 | gate text box, frame | `output/ui_dialogue_preview.png` (3x, read at 1x) | 5 / ok | 0 | 0 | 0 | 51 | not checked, no mask | PASS |
| 13 | battle box, frame | `output/ui_battle_preview.png` (3x, read at 1x) | 5 / ok | 0 | 0 | 0 | 65 | not checked, no mask | PASS |
| 14 | menu box, frame | `output/ui_menu_preview.png` (3x, read at 1x) | 4 / ok | 0 | 0 | 0 | 50 | not checked, no mask | PASS |
| 15 | quay tileset source | `game/sprites_src/env/quay/quay_tiles.png` (128x48) | 11 / ok | 0 | 0 | 0 | 68 | not checked, no mask | PASS |
| 16 | game over frame | none | unknown | unknown | unknown | unknown | unknown | unknown | **UNKNOWN, not drawn** |

Rows 1 to 8 and 10 to 15: `tools/nes_composite_check.py` returned `PASS: 0 block(s) violate the background rules,
0 sprite(s) violate the sprite rules`. Row 9 is the one hand run with a mask, quoted in full: `sprites: 7, 1
palette(s), busiest scanline 127 carries 4, 8 per line and 64 total allowed`.

Two rows sit exactly at a limit and are worth a watch, not a failure: the quay block frame spends 4 background
palettes of 4, and so does the enemy composite. A fourth or fifth colour set on either one fails the frame.

The colour and CHR columns are my own count over the same pixels, because no tool counts CHR. The frame verdicts are
reproducible with the commands in section 8.

The palette first verdict, every colour a role in `data/palette.json`, is the same for all 15 measured rows and
unknown for the one that does not exist; the reason is in section 6.

## 5. Rows that fail, with the fix and the owner

Count of rows that fail: **0 of the 15 measured slice artifacts** fail the NES rules, and **24 of the tool's 163
rows** fail; all 24 are advisory. The failing rows that touch slice art:

| Failing row | Rule | Visibility | Fix | Owner |
|---|---|---|---|---|
| `output/southampton_sample_preview_2x.png` | background_area x150 | 4,456 px | The 1x frame behind it passes (row 1). Regenerate the 2x sheet from the frame's own 4 palettes instead of pasting the frame beside its neighbours. | `tools/art/make_exterior_maps.py`; no open card names the sheet |
| `output/westminster_sample_preview_2x.png` | background_area x152 | 4,000 px | Same fix as above. | as above |
| `output/winchester_sample_preview_2x.png` | background_area x241 | 7,140 px | Same fix as above. | as above |
| `output/bg_battle_preview.png` | background_area x117 | 2,525 px | The four 1x frames pass (rows 5 to 8). Drop the strip borders from the sheet or composite it at 1x. | `tools/art/make_battle_bg.py`; no open card |
| `output/enemies_preview.png` | background_area x5, grid x1 | 112 px | The seven enemy sheets pass as sprites (3 colours each). Crop the sheet to whole 16 pixel rows. | `tools/art/make_enemies.py`; no open card |
| `output/enemies_preview_3x.png` | background_area x4, grid x1 | 55 px | Same fix as above. | as above |

The other 18 failing rows are sheets and captures for the title, music, sfx, icons and palette pages. They are not
on the slice path and they do not change the verdict.

One row cannot be fixed because it cannot be measured yet:

- **Game over frame.** Fix: R27 GAME-OVER `t_24eab5ff` draws it, then name the output `output/*_preview.png`, or the
  gate will skip it the way it skips every `*_frame.png`. Owner: `t_24eab5ff`.

The dock office frame was the other unknown when this card started. It landed at 19:50 and passes; no action left on
it beyond the frame naming rule in section 6.

## 6. The criteria the card names that nothing in the toolchain measures

1. **16 colours or fewer on screen.** No tool enforces 16. `MAX_COLOURS_ON_SCREEN` is 25 in both checkers, because
   25 is what the PPU can show. Every measured artifact is at or under 11 colours, so all 15 meet 16 as well, and
   the card's number is met but not the number the gate tests.
2. **8x8 tile budget against 256.** No tool counts tiles. `knowledge/ART-BIBLE.md` line 35 states 256 tiles per
   pattern table as a rule for S1 and S3 with no check behind it. The CHR column above is my own count of distinct
   8x8 tiles, so it is a proxy, not a gate. The worst measured frame is 85 tiles of 256.
3. **Palette first, every colour a role in `data/palette.json`.** `data/palette.json` holds 54 colours
   (`#0b0b0f`, `#1c1c24`, ...) and `data/nes_palette.json` holds 55 usable 2C02 entries. The two sets have **zero
   colours in common**, measured, so every pixel of every frame is off role and all 15 rows fail the criterion as
   worded: 61,440 of 61,440 visible pixels on a full frame, 6,144 of 6,144 on the quay tileset. This is a criterion
   defect: the checkers enforce the 2C02 palette, and `knowledge/ART-BIBLE.md` lines 283 to 292 (RULE 0 point 1)
   names the 54 usable NES master colours and `data/scene_palettes.json`, not `data/palette.json`. Against the
   palette the art is actually drawn in, all 15 rows pass: 0 blended pixels, 0 off-palette pixels.
4. **The frame budget itself.** `tools/nes_audit_all.py` only sees a finished frame when the name contains
   `preview`, so a `*_frame.png` at 256x240 is invisible to the gate. Eight of the fifteen slice rows above would
   never have been audited by a scheduled run.
5. **Sprite budget against 64** is measured only when a sprite mask or sprite list is passed
   (`tools/nes_composite_check.py` line 713). One of the fifteen rows had a mask; the rest report the rule as not
   checked, which is not a pass.

## 7. Q: for gamedev

- `Q:` Which palette is binding for the audit, `data/nes_palette.json` (what every checker enforces and what the
  art is drawn in) or `data/palette.json` (what this card's text names)? Answering this closes 15 failing rows at
  once, one way or the other, and decides whether `data/palette.json` needs a role for every usable 2C02 entry.
- `Q:` Should `tools/nes_audit_all.py` treat any 256x240 file under `output/` as a gated frame, `*_frame.png`
  included? Until it does, the gate cannot see the exterior sample frames, the four battle frames or any future
  game over frame, and this page has to be produced by hand.
- `Q:` The quay block frame and the enemy composite each spend 4 of the 4 background palettes. Is a full spend the
  intended ceiling, in which case one more colour set on either is a redraw, or is it acceptable until something
  else gives?

## 8. Reproduce

```
python tools/nes_audit_all.py                       # the 163 row run, exit 0, rewrites knowledge\NES-AUDIT.md
python tools/check_palette_recipes.py               # 57 recipes, 8 scene sets, 0 failures
python tools/nes_composite_check.py output/southampton_sample_frame.png
python tools/nes_composite_check.py output/quay_block_preview.png
python tools/nes_composite_check.py output/quay_office_preview.png
python tools/nes_composite_check.py output/bg_battle_corridor_frame.png
python tools/nes_composite_check.py output/enemies_battle_frame.png --sprite-mask output/enemies_battle_mask.png --sprite-height 16
```

The row level evidence is `output/nes_audit/SUMMARY.json` (the tool's own 163 records). The machine readable copy of
this page is `knowledge/NES-AUDIT.json`, regenerated from that summary plus the eight hand measured rows in the same
row scheme as the previous version: 171 rows, 163 from the tool, 8 measured by hand, each row carrying
`in_audit_universe` and `measurement_source`, and the rows that were also measured by hand carrying `chr_8x8_tiles`
and `role_palette_off_pixels`. The counting scripts behind the hand rows live in the card run only, not in the repo,
because this card owns two knowledge files and no tools.

Backup of the previous copy: `knowledge/NES-AUDIT.json.bak-2026-10-23-r41`.
