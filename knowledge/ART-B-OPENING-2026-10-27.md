# ART-B-OPENING: the first 39 seconds redrawn to direction B

Card ART-B-OPENING (t_3a2d0514). Nayil picked direction B, late NES polish, on 2026-10-26 19:00: bold dark
outlines, three tone shading lit from the top left, detailed tiles. This page is the record of the redraw of
the three queue rows the card owns (knowledge/ART-STYLE.md section 7 rows 1 to 3): the title screen, the
crawl and the drive. Nothing here changes the title timing data or the drive's scripted route; it is pixels
and the tools that draw them.

## 1. What is measured, and with what

    python tools/art/style_b.py --report --json <png> ...      the ART-STYLE section 2 rows, per file
    python tools/nes_audit_all.py                              the NES limits, the whole tree
    python tools/art/make_art_b_sheets.py                      before and after sheets at 3x
    python tools/pp_intro_art.py --check                       every fade strip is the fade of its base

The section 2 verdict on a strip is the one the Pine pre-gate run applies (projects/arananet/pine/batch/
pine_run.py, job_art): dither patches 0, orphan pixels 0, off palette 0, and light direction correct at
least wrong. Row 1 of section 2 (a 1 pixel dark outline on characters) and row 5 (silhouette readable at 1x)
are not measured by that tool and are not claimed here.

## 2. The three passes

Pass 1, the mechanical pass. tools/art/style_b.py is direction B as one measured step: 4-connected regions
of one palette index, the rim light on a region's top and left boundary, the shadow on its bottom and right,
and an ink line where two materials meet, darker material drawing it. It is wired into make_title_world.py
before the 16x16 solver, into make_drive_tiles.py on the role grid, and its dither flatten into
pp_intro_art.py for the fade twins. That pass alone left 8 of the card's 23 PNGs red on section 2, seven of
them on the light direction row, all of them full screen gradient layers lit the other way.

Pass 2, the light direction. Four separate causes, each measured before it was touched:

* The sky ramp was painted dark at the zenith and bright at the horizon, which section 2 counts wrong on
  every column: 4097 correct against 4585 wrong. SKY_BANDS now runs SKY_LOW at the zenith down to SKY_DEEP
  at the horizon, which is also where the moon is, so the ramp rises toward the frame's own light source.
  Same three colours, so the 16 colour budget does not move.
* The downs crest and the cloud crown were drawn in DIM, which tools/art/nes_snap.py hands $00 grey, a row 0
  entry: a hardware fade drops row 0 straight to black while the body under it only drops one row, so the
  lit line came out darker than the thing it lit in every fade twin. The crest is now BRIGHT ($20, white,
  which is what chalk is) and the cloud has no separate crown row at all, because the cloud's bands only
  carry $12 $00 $28 and the band pass snapped any other light tone back to $00.
* The foreground was ink, which ships as $0C teal, and the pass lit its top edge in asphalt, which ships as
  $0F black: the strip read 157 correct against 655 wrong. The grass is GREEN_DEEP ($0B) with a GREEN_MID
  rim ($0A), so the lit row is brighter than the body it sits on.
* The road's near verge sat under the tarmac and the tarmac ships black, so the band was a light pixel under
  a dark one 512 times. The near verge is the foreground layer's job and is no longer drawn on the road
  strip; the far verge's moonlit edge moved to the top row of the strip.

Pass 3, the dither and the darkness. drive_tiles.png carried five 2x2 checker patches in the shipped sheet,
three of them whole inside a tile and two straddling a tile seam; make_drive_tiles.py now flattens the role
grid per tile and the assembled sheet, so a partner takes the other partner's tone and no colour is added.
The sky band boundaries were then rebalanced to 0 to 47, 48 to 79, 80 to 119, because the first fix left
78 percent of the composed title frame black; that rebalance brings it to 72 percent and keeps every strip
green.

## 3. The numbers as shipped

Measured 2026-10-27 on the strips as they now sit in the working tree, by the same rules the Pine pre-gate
run uses. 27 PNGs, 27 PASS, 0 FAIL.

| file | verdict | light correct/wrong | dither | colours | three tone areas |
|---|---|---|---|---|---|
| `assets/tiles/drive/drive_tiles.png` | PASS | 1546/1332 | 0 | 9 | 17 |
| `game/sprites_src/title/spr_title_star.png` | PASS | 10/6 | 0 | 3 | 2 |
| `game/sprites_src/title/title_BG_bigben.png` | PASS | 2207/1829 | 0 | 6 | 3 |
| `game/sprites_src/title/title_BG_bigben_flash.png` | PASS | 2186/1995 | 0 | 5 | 0 |
| `game/sprites_src/title/title_L1_sky.png` | PASS | 5175/4599 | 0 | 4 | 122 |
| `game/sprites_src/title/title_L1_sky_fade1.png` | PASS | 4337/3314 | 0 | 3 | 0 |
| `game/sprites_src/title/title_L1_sky_fade2.png` | PASS | 0/0 | 0 | 1 | 0 |
| `game/sprites_src/title/title_L1_sky_flash.png` | PASS | 5175/3623 | 0 | 4 | 122 |
| `game/sprites_src/title/title_L2_clouds.png` | PASS | 542/28 | 0 | 3 | 0 |
| `game/sprites_src/title/title_L2_clouds_fade1.png` | PASS | 542/28 | 0 | 3 | 0 |
| `game/sprites_src/title/title_L2_clouds_flash.png` | PASS | 542/28 | 0 | 2 | 0 |
| `game/sprites_src/title/title_L3_downs.png` | PASS | 1141/191 | 0 | 4 | 26 |
| `game/sprites_src/title/title_L3_downs_fade1.png` | PASS | 760/441 | 0 | 3 | 8 |
| `game/sprites_src/title/title_L3_downs_fade2.png` | PASS | 205/13 | 0 | 2 | 0 |
| `game/sprites_src/title/title_L3_downs_flash.png` | PASS | 1106/187 | 0 | 3 | 26 |
| `game/sprites_src/title/title_L4_fields.png` | PASS | 4172/3675 | 0 | 3 | 4 |
| `game/sprites_src/title/title_L4_fields_flash.png` | PASS | 4172/3675 | 0 | 3 | 4 |
| `game/sprites_src/title/title_L5_verge.png` | PASS | 2036/920 | 0 | 4 | 0 |
| `game/sprites_src/title/title_L5_verge_flash.png` | PASS | 2522/1475 | 0 | 4 | 0 |
| `game/sprites_src/title/title_L6_road.png` | PASS | 5693/5669 | 0 | 4 | 32 |
| `game/sprites_src/title/title_L6_road_flash.png` | PASS | 6365/6244 | 0 | 3 | 64 |
| `game/sprites_src/title/title_L7_fg.png` | PASS | 16/16 | 0 | 2 | 0 |
| `game/sprites_src/title/title_L7_fg_fade1.png` | PASS | 0/0 | 0 | 1 | 0 |
| `game/sprites_src/title/title_L7_fg_fade2.png` | PASS | 0/0 | 0 | 1 | 0 |
| `game/sprites_src/title/title_L7_fg_fade3.png` | PASS | 0/0 | 0 | 1 | 0 |
| `game/sprites_src/title/title_L7_fg_fade4.png` | PASS | 0/0 | 0 | 1 | 0 |
| `game/sprites_src/title/title_L7_fg_flash.png` | PASS | 16/16 | 0 | 2 | 0 |

The NES limit audit over the tree: `nes_audit_all: PASS, 192 file(s), 24 failing (0 gated), 0 unmeasured,
189 output file(s) skipped, exit 0`. The 24 failing rows are all previews and captures under output/, which
the audit reports but does not gate; every shipped strip and sheet above is green.

The composed night frame (`output/art_b/ART-B-OPENING/title_after_256x240.png`) is 8 distinct colours with
light direction 3195 correct against 2734 wrong, and 72 percent of its 61440 pixels are black (28 percent are
not), down from 78 percent before the band rebalance.

## 4. What this pass did not do, and why

* The Meta eye critic could not be run in this worker: `python tools/eye_critic.py --dry-run <frame>` prints
  `key: absent from GEMINI_API_KEY, a real run would refuse`, and no Meta key (MODEL_API_KEY, META_API_KEY)
  is set in the environment either. So the card's "the critic scores the after frame higher than the before
  frame" is NOT claimed. The measured rows above are what stands in its place, and section 5 of ART-STYLE.md
  already says a model's opinion loses to a measurement where they disagree.
* No Muse Image concept reference was used and no SAM 3.1 cutout was made, so CREDITS.md needs no row from
  this card. Every shipped pixel here is placed by the project's own tools.
* The crawl's TYPE is not redrawn. spr_pp_font8 is one ink by the font contract
  (knowledge/FONT-CONTRACT-AUDIT-2026-10-23.md row A1, game/scripts/pp_font/pp_font.gml rule 6) and
  tests/test_make_title_ui.py pins it pixel for pixel to the licensed Press Start 2P rasterisation, so a
  three tone or outlined glyph is a gamedev decision and not an art lane's. The crawl's star field
  (spr_title_star) is redrawn: 3 colours, three tone areas 2.
* The title's row 6 (`title_L6_road`) passes the light direction by 24 pairs. That is thin, and it is the
  honest shape of a strip that is mostly black tarmac with two white lines running through it: a bright
  horizontal line inside a dark field gains one correct pair on its underside and loses one on its top.
  A future card that wants more margin has to give the road a lit surface, which is a palette decision
  (nes_snap.NIGHT_TABLE sends ASPHALT to $0F) and not a drawing one.
