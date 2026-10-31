# ART-B-PERCY 2026-10-30: Lt. Percy and his three men redrawn to direction B

Card t_3dfd69d1. Nayil picked direction B, late NES polish, on 2026-10-26 19:00: bold dark outlines, three
tone shading lit from the top left, detailed tiles. This page is the record of the redraw of queue row 11
(knowledge/ART-STYLE.md section 7), the four overworld standers of the ship cast.

The cell is 16 x 24. That is the cell the queue rows themselves ask for: `data/sprite_redraw_queue.json` rows
`cand_r18_percy_ow`, `cand_r18_percy_man_1`, `cand_r18_percy_man_2` and `cand_r18_percy_man_3` each name
"over world stander, 16 x 24 cell". The four sheets are drawn by `tools/art/make_characters_v2.py --only-style-b`
and land beside the rest of the cast, one frame each, the `down` stand the game draws.

## 1. What changed in the drawing

Four changes, each one a named key in the figure's build so the next card can move it without hunting:

| change | key | why |
|---|---|---|
| the face is the light entry and the cap is the mid entry | `face_light` | direction B's own reference frame (output/art_target/sprites_B.png) reads the face as the lightest tone on the figure with the hair a tone around it. The white uniform triple is $02 $12 $30, navy, blue, white: it has no skin entry, so on the first draft the face was the blue and the cap the white, which reads as a helmet with a white visor band and not as a man. |
| the trident is a fork over a shaft planted on the ground line | `accessory: trident` | the first draft drew a solid ink shaft from the shoulder to the hip in column 14, which is a black bar welded to his side and says nothing about rank. The fork is a centre spike on row 1, the outer tines on row 2 with the gap left for the outline pass to ink, and the crossbar on row 3. Three tines with two visible gaps need five columns and a 16 px figure leaves three, so the head is drawn as a fork and reads as one. |
| all three men wear the cap; their mass tells them apart | `torso_half`, `leg_w`, `boot_w` | the first pass made man 3 the only bare headed man in the party, and the eye read that as a different character and not as one of the crew. The card asks for three men who are clearly one unit, so the cap stays and the silhouette carries the difference: man 1 is 10 px wide, man 3 is 12, man 2 is 14 with the chest stripe. |
| rank details on Percy | `cuff: True`, `chest: stripe` (man 2) | one ink row across each cuff, and a full width band across man 2's jumper. Ink only, so neither costs a fourth colour. |

Percy keeps the beard he shipped with (beard depth 2, which draws the mouth inside the beard), and the three men
keep the shared three entry palette. Hue is what makes them one crew; shape is what makes Percy the officer.

## 2. The numbers as shipped

Drawn 2026-10-30 by `python tools/art/make_characters_v2.py --only-style-b`, from the working tree, after the
edits above. The generator refuses a sheet with a fourth colour in a tile, an outline leak, or an entry that is
not a 2C02 output, so these four sheets cannot be written red.

| sheet | tile colours worst | ink share | light correct/wrong | orphans | leaks | dither | drawn px | frame box |
|---|---|---|---|---|---|---|---|---|
| `percy_ow24` | 3 of 3 | 48.8 % | 18 / 2 | 0 | 0 | 0 | 303 | 14 x 24 (12 without the trident) |
| `percy_man_1_ow24` | 3 of 3 | 49.3 % | 16 / 4 | 0 | 0 | 0 | 209 | 10 x 24 |
| `percy_man_2_ow24` | 3 of 3 | 46.8 % | 21 / 2 | 0 | 0 | 0 | 263 | 14 x 24 |
| `percy_man_3_ow24` | 3 of 3 | 47.1 % | 18 / 4 | 0 | 0 | 0 | 227 | 12 x 24 |

`tools/nes_audit_all.py`, the whole tree: `nes_audit_all: PASS 193 file(s), 24 failing (sheet 20, capture 4), 0
unmeasured`. The 24 failing rows are previews and captures under `output/`, which the audit reports and does not
gate. The four sheets measure `ok true, gated true, colours 3, off_palette 0, problems 0` in
`output/nes_audit/game__sprites_src__chars__<name>.json`.

`python tools/art/style_b.py --report` on the four: `colours 3 areas 2 orphans 0 dither 0 offpalette 0` for each,
with Percy at `1: 0 2: 0 3: 2` and each of the three men at `1: 0 2: 1 3: 1`, which is the count of 16 x 16
areas carrying one, two and three tones. Its light direction column reads `lit 0/0` on all four, and that is the
tool's limit and not a pass: its TONES table is the fourteen colours the title frame spends, and these three
entries are not in it, so the tool has no pair to count. The sprite pipeline measures the light direction itself,
and those are the correct/wrong numbers in the table above. Every one of them passes section 2's rule, correct at
least wrong.

The before and after material is built by `python tools/art/art_b_percy_before_after.py`:

| file | what |
|---|---|
| `output/art_b/ART-B-CHARACTERS/percy_before_after_3x.png` | four rows, the shipped 16 x 16 cell against the 16 x 24 redraw, at 3x |
| `docs/art-b-percy-before-after-3x.png` | the same sheet, tracked, because `output/` is ignored by this repository |
| `output/art_b/ART-B-CHARACTERS/percy_before_256x240.png` | the four shipped figures on one 256 x 240 frame at 4x, 4 colours, 0 off palette |
| `output/art_b/ART-B-CHARACTERS/percy_after_256x240.png` | the four redraws, same canvas, same scale, 4 colours, 0 off palette |

The before is read out of git HEAD, never the working tree, so a rerun of the generator cannot turn the before
into the after. The three men share the one sailor sheet the game ships, `sailor_ow_v2.png`, so that is the
before for each of them and the sheet says so.

## 3. What was not run, and why

The card's fourth check is the Meta eye critic scoring the after frame higher than the before frame on
readability. It was NOT run, and no score is claimed. The tool refuses without a model key in this session's
environment:

    python tools/eye_critic.py --dry-run output/art_b/ART-B-CHARACTERS/percy_before_256x240.png
    file:     .../percy_before_256x240.png
    model:    gemini-3.5-flash
    size:     0.00 MB, 256 x 240, 4 distinct colours, 0 off palette
    key:      absent from GEMINI_API_KEY, a real run would refuse
    calls:    1 planned

`GEMINI_API_KEY`, `MODEL_API_KEY` and `META_API_KEY` are all unset in this worker. The two frames the critic
reads are built and named above, so the check is one command away for anyone with the key. This is the same wall
card ART-B-OPENING (t_3a2d0514) hit and recorded in knowledge/ART-B-OPENING-2026-10-27.md section 4.

## 4. Commands

    python tools/art/make_characters_v2.py --only-style-b
    python tools/nes_audit_all.py
    python tools/art/style_b.py --report game/sprites_src/chars/percy_ow24.png game/sprites_src/chars/percy_man_1_ow24.png game/sprites_src/chars/percy_man_2_ow24.png game/sprites_src/chars/percy_man_3_ow24.png
    python tools/art/art_b_percy_before_after.py
    python tools/eye_critic.py --dry-run output/art_b/ART-B-CHARACTERS/percy_before_256x240.png
    python -m pytest tests -q -k "art or palette or nes"
