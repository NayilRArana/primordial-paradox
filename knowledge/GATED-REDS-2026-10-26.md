# GATED REDS, 2026-10-26: the eleven gated audit reds, what each one was, and which ones had no owner

Card `t_30746cd8` (gamedev, node CitadelArana), following `t_b8e56b9d` AUDIT-TRUTH. That card split the audit's red
count by class and found that the eleven gated reds had no open card anywhere on the board. This page is the record
of what they were, what was measured, what was fixed, and what was retired, so that nothing here depends on a PNG
that no tool writes.

Measured at the start of this card, on HEAD `cba6ec0f`:

    python tools/nes_audit_all.py
    nes_audit_all: FAIL  184 file(s), 35 failing (frame 10, asset 1, sheet 20, capture 4), 0 unmeasured
      class frame     25 file(s),  15 pass, 10 fail (10 gated)
      class asset    130 file(s), 129 pass,  1 fail (1 gated)
      class sheet     21 file(s),   1 pass, 20 fail          (advisory)
      class capture    8 file(s),   4 pass,  4 fail          (advisory)

## 1. The nine frames, and why none of them is kept

`output/bg_battle_{corridor,deck_night,quay_dusk,wardroom}_{text,fight}_preview.png` and
`output/gameover_preview.png` were untracked 256x240 PNGs dated 2026-10-22, carrying four colours that no 2C02 entry
can produce: `#0b0b0f`, `#1c1c24`, `#4a4a58`, `#c8c8d4`. Three measurements decided them.

**a. No tool in this tree writes them, and none ever did.** `git log -S "_text_preview" -- tools/` and
`git log -S "_fight_preview" -- tools/` both return nothing across the whole history, so no tracked tool ever
contained either name. The only tools that write a `%s_preview.png` are `tools/art/make_drive_tiles.py` and
`tools/art/make_quay_tiles.py`, for different names. `output/_eye_r6_sources.py`, `_eye_r6_build_sheets.py`,
`_eye_r6_probe.py` and `_eye_r6_queue.py` all READ these files and write none of them. An artefact with no generator
cannot be kept truthful: any later change to the screen makes the picture a lie that the audit then measures as an
art defect forever, which is exactly how eleven reds ended up with no owner.

**b. Eight of the nine can never pass, by construction.** They carry a HUD. The repository's own composed-frame tool
says so in its own docstring (`tools/art/compose_battle_frame.py`, lines 24 to 29): the command band, the message
window, the enemy name and the health bar are drawn in `data/room_palettes.json`'s four universal roles, and "a frame
that carries the HUD cannot read 0 failures in `tools/palette_synergy.py`". Measured here with the audit's own
checkers, snapping the four colours to their 2C02 entries clears the palette rule on all nine and still leaves the
eight `bg_battle` frames failing `background_area` by 3 to 7 areas each, because a HUD over a background puts four
non backdrop colours inside 16x16 areas the PPU allows three. The nine were design mockups of a screen, not frames
the repository can produce.

**c. The defect they found is real, and it is not in a picture.** `data/palette.json` carries the four hexes as its
grey family, `game/scripts/pp_data/pp_data.gml` lines 150 to 165 resolve a role straight to those design hexes with
no 2C02 test, and `pp_role_colour()` is what every menu, every dialogue window, the battle band and the game over
panel draw with. That is measured on the running game, not on a mock: `knowledge/BATTLE-DIM-OFF-PALETTE-2026-10-26.md`
section 2 records the `dim` role `#4a4a58` reading `(73, 72, 87)` in a window capture of the first fight. Measured
here today, **0 of the 54 colours in `data/palette.json` is an output of the Ricoh 2C02**, so the defect is four
colours wide in the picture and fifty four colours wide in the machine.

So the frames go and the defect stays, written down where a check can read it. Deleted on 2026-10-26, all nine
untracked, with their sha256 recorded here so the record is auditable without keeping the bytes:

| file | sha256 |
| --- | --- |
| `bg_battle_corridor_text_preview.png` | `6f201d8fe669ff0d86c8756378fe31383eb883db826034dadb063bdfc7257f9f` |
| `bg_battle_deck_night_text_preview.png` | `7945058e27d8fdc163b6f0dbea67208569f2e0025d74dcfde98cf9b322f237ef` |
| `bg_battle_quay_dusk_text_preview.png` | `391d6344022df6d3997f39620fd36254f01afa8c934738382aa463437d00eb8e` |
| `bg_battle_wardroom_text_preview.png` | `f030f56ae1a4741831d813eb266a4f63cafe7c6a1c57f1939bc96138b7f89c71` |
| `bg_battle_corridor_fight_preview.png` | `8fa92785b672953b86d39dbbb2bdce2e8e6affb64a553eb1684bc4747e429f47` |
| `bg_battle_deck_night_fight_preview.png` | `704ff3cb35a72cc16249202b4557d7c96e5645a918eb2ac0e50f780c1b423aa7` |
| `bg_battle_quay_dusk_fight_preview.png` | `fe1104c0a498dec714285c66aa83b0ba909a484947882bb41f305e885a16fb4a` |
| `bg_battle_wardroom_fight_preview.png` | `e5429bc462926fc2624133031fe15757beb4198f585eb69d6b562ea054c4c4b1` |
| `gameover_preview.png` | `b11177af23e8faad30af216893cda164e2b430c08b184e91991d23d9b4a0d10b` |

The queue rows that measured them are retired in the same commit, and their names are out of
`data/sprite_redraw_queue.json`, because that file is scanned by `tools/nes_audit_all.py` `named_output_files()`: a
name left behind there would print as an output file "named by this repository's data" that the tree does not hold.

`knowledge/PALETTE-RULINGS-2026-10-25.md` section 8 point 3 ruled `gameover_preview.png` "a real defect of a shipping
screen" whose "fix belongs on the machine that draws it". Deleting the mock and carding the machine is that ruling
followed, not reversed: the picture never could hold the fix.

## 2. What replaced the rows: one row that reads the code

`data/sprite_redraw_queue.json` gains one P0 row, `runtime_role_colours_not_2c02`, whose files are the three files
that carry the defect (`game/scripts/pp_data/pp_data.gml`, `data/palette.json`, `tools/check_runtime_palette.py`) and
whose check is a command that exists:

    python tools/check_runtime_palette.py

It is red today and says why in two lines: `data/palette_ppu.json` is missing, so the runtime draws every design
colour as it was painted, and `pp_data.gml` never names that file, so such a table would sit beside the code instead
of being what the runtime reads. It goes green only when every one of the 54 design colours has a mapping to a
usable 2C02 entry AND the runtime names the table. That is a check that cannot pass by absence: it reads
`data/palette.json` and `data/nes_palette.json` and the GML, all three committed.

The fix itself is a design decision and this card did not take it. Snapping all 54 colours changes the look of every
screen in a game that cannot be built on this machine (no licence on this box), and the four universal roles alone
would leave 50 illegal colours drawn. The row carries the measurement; gamedev takes the ruling.

## 3. The two reds that were fixed rather than retired

**`output/drive_gantry_preview.png`, 2 px over the area limit at [240, 176].** The two `#f8f8f8` pixels were the top of
`t_barrier_end`'s diagonal grey edge, at tile offsets (13, 4) and (14, 3). In `GANTRY` the tile is placed at x 232, so
its 16x16 area at [240, 176] straddles the `verge_shadow` row: two bg1 greens plus the tile's own `dim` and `bright`
made four non backdrop colours where the PPU allows three. `tools/art/make_drive_tiles.py` now carries the diagonal on
to (14, 3) in `dim` instead of capping it with `bright`, the sheet is regenerated, and the audit reads
`nes_audit_all: PASS  1 file(s), 0 failing` for that file. No tolerance moved: the tile still spends three roles of
its own palette, as it always declared.

**`game/sprites_src/title/spr_pp_dither.png`, 128 px of `#ffffff`.** The pixel is not art, it is the tint identity:
`draw_sprite_tiled_ext` multiplies the mask by the role colour that asks for it, so `#ffffff` resolves to exactly that
role and any legal substitution would tint the frame to a colour nobody asked for. `tools/nes_check.py` already
carries `check_mask()` for this (card `t_06ef8607`), and the audit never reached it, because `classify_asset()` sent
the sheet down the sprite path on its `spr` prefix. The audit now honours a sidecar `"kind": "mask"` before the naming
rules, so the row is measured by the mask rule (tint identity, 50 percent checker, half the pixels drawn) instead of
being charged a palette it cannot have. `tests/test_nes_audit_all.py` pins both halves of that.

## 4. What this card did not do

No pixel of `data/nes_palette.json` changed. No tolerance, floor or limit moved. `data/palette.json` is untouched,
including its frozen 54 and its digest. No GML changed, so nothing here claims the game looks different yet. Nothing
was posted, published or uploaded, and no game build was run: there is no licence on this box, so every claim above
is a measurement of files and captures that already existed.
