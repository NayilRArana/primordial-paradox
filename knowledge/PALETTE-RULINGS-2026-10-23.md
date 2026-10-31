# Palette rulings, 2026-10-23: the title wordmark

Card `t_1c04d011`, gamedev. Three questions came up from card `t_213621d8` (AUTO-SPRITE-NEXT, assistant) about
`game/art/spr_pp_title_logo.png`. None of them was a request for art, so this file is the ruling and the evidence
behind it. Nothing in it hands the assistant a licence to skip a check: two of the three answers change a tool or a
path, and both changes are written here with the numbers that justify them.

Read with: `knowledge/ART-BIBLE.md` RULE 0 (the clause under point 2 is this ruling, in the bible's own words),
`specs/14-title-screen-drive.md` line 28 (the wordmark design), `data/palettes/scene_title.json` (the title's set),
`output/SPRITE-NEXT-2026-10-23-LOGO.md` (the redraw's own report).

## Ruling 1: RULE 0 point 2 does not apply to a tiled layer, and R1b replaces it

No, the 2 luminance row gap between body and ground is not meant for a wordmark, and it is not meant for any layer
that has no feet. RULE 0 point 2's own subject is "a character sprite palette" that "must separate from the
background it stands on". A wordmark does not stand on anything; it is set into the sky. The intent of the rule,
separation, still applies, and it is measured with the instrument that can see it.

Why the row arithmetic cannot judge a wordmark, measured on the title's own ground (`output/logo_sky_ground.png`,
rows 0 to 15 the $0F backdrop, rows 16 to 63 the $12 sky, read from the pixels, not assumed):

| entry | code | 2C02 row | luminance | contrast on the $12 sky | contrast on the $0F backdrop |
| --- | --- | --- | --- | --- | --- |
| ink | $0F | 0 | 0.000 | 3.75:1 | 1.00:1 |
| stone body | $00 | 0 | 0.202 | 1.34:1 | 5.03:1 |
| gold | $28 | 2 | 0.542 | 3.16:1 | 11.85:1 |
| sky | $12 | 1 | 0.138 | 1.00:1 | 3.76:1 |

The ink and the stone body are both hardware row 0 while their luminances are 0.000 and 0.202. That is the whole
problem: the four row grid is a hardware bucket, not a perception, and on this pair it is blind to the difference
that makes the letters read. The rule's own remedy under it is also wrong here. To be 2 rows from the $12 sky a body
must sit in row 3, the whites, so the wordmark would have to lose its stone body and become white marble: a palette
change and a spec 14 change, taken to satisfy a rule written about characters. The answer is not that, it is scope.

What the wordmark is held to, and passes, measured the day this was written:

- set membership: three colours, $0F, $00 and $28, exactly title sprite palette sp0 for `spr_pp_title_logo`.
- a 1 px ink outline: $0F, with the drop shadow in the same ink so the shadow costs no colour.
- per tile colour count: worst 8x8 tile 3 opaque colours, the sprite ceiling.
- separation, the part of point 2 that survives: the layer's ink or its body must clear 3:1 (the WCAG large text
  floor already implemented in `tools/art/contrast_check.py`) on every ground colour under it. Ink on the sky is
  3.75:1 and stone on the backdrop is 5.03:1, so it reads on both.

Where the ground behind a letter is the ink itself, the top 16 rows of the title, the outline is correctly invisible
and must stay that way: the letters separate by their body luminance, 5.03:1, and a second outline colour would
break sp0, which has three entries. No halo, no fourth colour.

Implemented as R1b `overlay_contrast` in `tools/palette_synergy.py`, on the same size test the tool already used to
skip the 3 colour sprite rule for a tiled layer (a frame wider than 16 px or taller than 32 px). The size test is
shared with R4 and R6 deliberately: one definition of "this is not one sprite object", not two. The frame line now
says "tiled layer so R1b: ink $0F, separation by contrast on every ground", so nothing is silently skipped, and a
body that is the ground colour comes out as a 1.00:1 `overlay_contrast` fail, which is R3's invisible case in the
reading that fits a layer.

Proof that character verdicts are untouched, which is the only thing that mattered in this change: the advisory
audit (`tools/palette_synergy.py --gate`, all six entries are advisory, none gated) went from 238 problems on the
title entry to 211. `body_ground` 75 to 2, `same_hue_row` 7 to 0, `invisible` 13 to 0, `overlay_contrast` 0 to 66,
`palette_count` 116 and `set_member` 27 unchanged. The ship entry, which is all character sprites, has the same
count in every rule: `white_blob` 8, `body_ground` 8, `sprite_tile` 8, `set_member` 16, `palette_count` 218, and no
`overlay_contrast` at all. The 2 remaining `body_ground` on the title
entry are both on `spr_pp_menu_cursor`, an 8x8 sheet that is still one object and is still asked the row gap.

## Ruling 2: `tools/art/title_logo_v2.py` keeps ownership of the shipped sheet

One generator owns one asset name. `spr_pp_title_logo` belongs to `tools/art/title_logo_v2.py`, that is written in
`tools/art/make_title_ui.py` line 19, and it is tested: `tests/test_make_title_ui.py` line 158 exists because this
exact bug happened once already, a second writer putting the v1 art back over the v2 sheet. Handing the name to
`make_title_rows_v2.py` would reopen it, and on top of that `make_title_rows_v2.py` writes `game/art`, which ships
nowhere (ruling 3). So no: the title lane may not regenerate `game/sprites_src/title/spr_pp_title_logo.png` from
`logo_frames`. The crack moves into `title_logo_v2.py` instead.

Cheap, because the redraw's own contribution is smaller than its report suggests. Diffed pixel by pixel against the
shipped sheet (both 448x64, two frames of 224x64):

- frame 0: 17 pixels differ, all in x 142 to 145, y 44 to 60, and all of them gold in the redraw: that is the crack,
  and nothing else. The gold foot inlay spec 14 asks for is ALREADY in the shipped sheet, which spends gold on row
  18 and row 61, the foot row of each line.
- frame 1: 35 pixels differ, inside the shimmer band, 11 stone to gold and 10 gold to stone around the band's shape,
  because the two files implement the band separately.

So the port is the crack and one band implementation, not a generator handover. Concretely, keep
`make_title_rows_v2.py` as the row's builder and the contact sheet, and have `logo_frames` call the owner instead of
drawing its own copy:

```
wordmark.logo_frame(index, {wordmark.INK: ink, wordmark.BASE: stone,
                            wordmark.HIGHLIGHT: stone, wordmark.GOLD: gold})
```

`title_logo_v2.logo_frame` already takes its colours by role, so passing stone for `HIGHLIGHT` gives the shipped
three entries with no band pass needed and no second band. Add the crack (`CRACK_PATH`, `letter_box`,
`crack_pixels` from `make_title_rows_v2.py`, which places it inside the O's own box from
`wordmark.scaled_mask`) to `title_logo_v2.py`, and the shipped sheet carries spec 14's crack after one rerun of the
owner plus `tools/art/title_bands.py apply`.

## Ruling 3: the queue measures `game/sprites_src`, and `game/art` is retired

Yes. `game/art` is a ghost folder and every row that points at it measures something that does not ship:

- 19 of the queue's 19 sprite rows carry `"path": "game/art/..."`.
- `git ls-files game/art` is 0 files: the folder is untracked and `.gitignore` line 12 ignores it. A before number
  measured off it cannot be reproduced from a clone, which is what a number in a committed data file has to be.
- `game/datafiles/` is gitignored too (line 5) and is build output: `tools/sync_art.py` rebuilds
  `game/datafiles/art` from `game/sprites_src/{title,env,chars,env/quay}`, and `--check` says "art mirror is
  current: 105 animations". The runtime reads that mirror, and `game/PrimordialParadox.yyp` names `datafiles` 246
  times and `game/art` zero times.
- The drift is real, not theoretical: the redraw at `game/art/spr_pp_title_logo.png` (sha256 `a81769b0`) and the
  shipped `game/sprites_src/title/spr_pp_title_logo.png` (sha256 `a45c020b`, identical to the runtime mirror) are
  different files today.

So: the source of truth is `game/sprites_src`, and the queue measures it. `game/art` retires, together with the
`.gitignore` line, and `tools/sync_art.py`'s docstring gets fixed at the same time, because it still says the mirror
goes into `game\art\` while its code writes `game\datafiles\art\`.

Four of the 19 rows cannot be repointed as they stand, and this is the part that has to be done with eyes open:

| row path | truth |
| --- | --- |
| `game/art/spr_title_ronan.png` | retired name: the sheet is `game/sprites_src/title/spr_title_konrad.png` |
| `game/art/spr_title_theo.png` | retired name: the sheet is `game/sprites_src/title/spr_title_zander.png` |
| `game/art/spr_player_ow.png` | no copy under `game/sprites_src`; the overworld walker draws `chars/spr_*_ow` sheets, so this is superseded art, not a lost sheet |
| `game/art/spr_gate_sentry_ow.png` | same, superseded by the chars sheets |

The other 15 have a `game/sprites_src` home already and repoint cleanly. A before number for a repointed row has to
be measured again from the source; copying the old number across is how a committed file ends up quoting a ghost.

## What was changed here, and what was not

Changed: `tools/palette_synergy.py` (R1b, the shared size test, the `--gate` report path bug that crashed on an
`--out` on another drive), `knowledge/ART-BIBLE.md` (the scope clause under RULE 0 point 2, same words),
`data/sprite_redraw_queue.json` and its mirror (this row's palette verdict, now PASS under R1b, and the ruling
recorded on the row), `DEVLOG.md`.

Not changed: any art file. The redraw is still proven and waiting, which is what the card asked.

Not regenerated, on purpose: `knowledge/NES-AUDIT.md` (its title row still reads 238 problems with the old rule
breakdown) and `knowledge/PALETTE-PASS-LIST.md` (body_ground 91 across the six pairs). Both are records of an audit
run on the date they carry and both are written by tools, `tools/nes_audit_all.py` among them. Editing them by hand
would make a run record disagree with the run. They come back true on the next audit, and until then a reader takes
the numbers there as of that date.
