# The runtime palette, 2026-10-26: what each of the 54 design colours becomes on the 2C02

Card `t_54db4d0f` (gamedev, node CitadelArana), raised by `t_30746cd8` GATED-REDS-UNOWNED. This page records the
decision the card existed for, the measured numbers behind it, and the one thing it could not do on this box: look at
the game.

## 1. What was wrong, measured

`game/scripts/pp_data/pp_data.gml` built `global.pp_data.palette_rgb` straight out of the hex strings in
`data/palette.json`, and `pp_role_colour()` handed that hex to `draw_set_colour`. Not one of those 54 hex values is an
output of the Ricoh 2C02, so every flat rectangle and every window fill drawn from a role was an off palette pixel.
It was on screen: a window capture of the first fight carries the `dim` role `#4a4a58` reading `(73, 72, 87)`
(`knowledge/BATTLE-DIM-OFF-PALETTE-2026-10-26.md` section 2).

    python tools/check_runtime_palette.py        before this card
    runtime palette: 54 colour(s) in data/palette.json, 0 mapped in data/palette_ppu.json, 0 resolved to a 2C02
    output, 54 not
    FAIL data/palette_ppu.json is missing, so the runtime draws every design colour as it was painted
    FAIL game/scripts/pp_data/pp_data.gml never names palette_ppu.json
    exit 1

## 2. The decision: route (a), snap at load

Route (b), re cutting the design palette to a different 54, was refused. The 54 are addressed **by index** from
`data/room_palettes.json` (role name to index), from every `data/palettes/scene_*.json` (entry numbers), and from
`data/palette_recipes.json` (57 recipes whose numbers are 2C02 entries). A new 54 re opens `frozen_digest`, invalidates
every recipe, and buys a look nobody on this box can look at. Route (a) keeps the design palette frozen, keeps
`data/nes_palette.json` untouched, moves no tolerance, and puts the one decision that actually changes the screen in a
file with a check on it.

So: `data/palette_ppu.json` maps design index to 2C02 entry, `pp_data.gml` resolves through it at load, and the colour
that reaches `draw_set_colour` is the entry's hex.

## 3. The table, family by family

The mapping is **curated, not nearest neighbour**. The 2C02's dark end holds one usable black (`$0F`) and no second
dark neutral; the next grey up is `$00` at luminance 0.202, which is lighter than most of this palette's mid tones. A
nearest colour search therefore hands a near black design grey a saturated blue or green, which is the wrong answer
arriving confidently.

54 design colours resolve to **30 of the 55 usable entries**. Measured luminance in brackets, from
`tools/art/contrast_check.py`.

| Family | Design indices | Entries | Order preserved |
| --- | --- | --- | --- |
| grey (UI) | 0 to 5 | `$0F` (0.000), `$0C` (0.044), `$02` (0.036), `$00` (0.202), `$10` (0.503), `$20` (0.939) | ink < paper, one 0.008 inversion at the shadow |
| sea | 6 to 11 | `$0F`, `$02`, `$0C`, `$12` (0.138), `$22` (0.276), `$2C` (0.627) | yes |
| bronze | 12 to 17 | `$0F`, `$08` (0.038), `$07` (0.057), `$18` (0.232), `$17` (0.242), `$27` (0.463) | yes |
| wine | 18 to 23 | `$0F`, `$05` (0.084), `$05`, `$16` (0.228), `$26` (0.341), `$35` (0.503) | yes |
| moss | 24 to 29 | `$0F`, `$0B` (0.070), `$0A` (0.099), `$09` (0.134), `$19` (0.343), `$2A` (0.518) | yes |
| stone | 30 to 35 | `$0F`, `$08`, `$08`, `$07`, `$00`, `$10` | yes |
| gold | 36 to 41 | `$0F`, `$08`, `$18`, `$28` (0.542), `$28`, `$38` (0.704) | yes |
| violet | 42 to 47 | `$0F`, `$02`, `$03` (0.064), `$13` (0.141), `$23` (0.269), `$33` (0.557) | yes |
| blood | 48 to 53 | `$0F`, `$06` (0.087), `$06`, `$06`, `$16` (0.228), `$16` | yes |

The seven roles any screen actually draws with (`grep pp_role_colour` over `game/scripts` on 2026-10-26: ink 19 calls,
text 16, dim 15, paper 14, warn 1, marker 1, hazard 1):

| Role | Design | Becomes | Why |
| --- | --- | --- | --- |
| `ink` | `#0b0b0f` | `$0F` black | The fade rectangle, the game over backdrop and every window border. The one usable black is the right answer. |
| `paper` | `#1c1c24` | `$0C` dark cyan | The panel the white 8x8 glyphs sit on, so it must stay near black; `$0C` is the darkest desaturated output after black (0.044 against `ink` 0.000, which is five times the gap the design itself had). |
| `dim` | `#4a4a58` | `$00` grey | The only usable mid grey, 0.202. |
| `text` | `#c8c8d4` | `$20` white | Cursor rules, choice arrows, the HP marker. |
| `warn` | `#e07a86` | `$35` pale rose | Legible on both the daylight deck and the night quay. |
| `marker` | `#e8c65a` | `$38` pale yellow | Distinct from `marker_trail` at `$28`, so the marker and its trail stay two yellows. |
| `hazard` | `#c24040` | `$16` strong red | The chip's reds are all bright; `$16` is the strong one. |

The card warned that the title's own table (`tools/art/nes_snap.py`, `NIGHT_TABLE`) maps `INK` to `$0C` and `ASPHALT`
to `$0F`, which would lose the outline if copied here. It is not copied: that table colours a night title scene where
silhouettes must read against a black sky, this one colours UI where ink must be the black. Two tables, two jobs.

## 4. What still collapses, and why that is not a bug

- `paper` `$0C` (0.044) sits 0.008 **brighter** than `window_shadow` `$02` (0.036). The order is inverted and stays
  inverted: the chip has no second dark neutral, and a shadow darker than its panel is the correct reading of the role.
  The alternative was both roles on black, which is the defect this card fixed.
- `window` (design index 6) lands on `$0F`, the same entry as `ink`. No code path draws `window` today.
- Six painted reds become two entries, and two painted stone/bronze steps share `$08`. Six levels of one hue on four
  rows cannot be six entries.
- Every room palette set still spends **10 or 12 distinct entries** (cap is 16, screen ceiling is 25): deck_day 11,
  ship_cabin 12, lower_deck 11, quay_night 11, office_night 11, drive_night 10, ui 10.

## 5. What the check proves now, and what it cannot

`tools/check_runtime_palette.py` has five parts, up from three. The new two pin the visual decision, because "it looks
right on a built game" is not something this box can run:

4. a material family never runs backwards in measured luminance (a shadow drawn brighter than its highlight);
5. `ink`, `paper`, `dim` and `text` stay four different entries, `window_shadow` stays different from `ink` and
   `paper`, and no room palette set spends two design colours of one family on one entry.

    python tools/check_runtime_palette.py        after this card
    runtime palette: 54 colour(s) in data/palette.json, 54 mapped in data/palette_ppu.json, 54 resolved to a 2C02
    output, 0 not
    runtime palette: 30 distinct 2C02 entry(s) for the 54 design colours
    check_runtime_palette: PASS
    exit 0

    python -m pytest tests/test_runtime_palette.py -q
    12 passed

**Not proven: nobody has looked at this on a built game.** No GameMaker licence exists on this box, so the build step
could not run and the look of every screen changed unmeasured. The card's own acceptance, a window capture of the
battle screen and of the game over screen measuring 0 off palette in `tools/nes_audit_all.py`, is still owed by
whoever has Igor. What stands in for it today is arithmetic: the ramp order, the four-role separation, the per-set
entry counts above, and the fact that every colour the runtime now hands to `draw_set_colour` is a
`data/nes_palette.json` entry by construction.

Two look questions the mapping raises and cannot settle without a screen:

- **Q: the panel is `$0C` dark cyan, not black.** A dialogue box now reads as a very dark teal with a black border and
  the sheet's white glyphs, which is the classic NES window, but it is not the near black the design painted. If it
  reads wrong on a CRT, the move is `paper` to `$02` and `window_shadow` to `$0C`, which trades a blue panel for a
  teal shadow.
- **Q: `dim` is `$00` grey at 0.202, nearly three times the luminance of the design's `#4a4a58`.** The HP band track
  and the menu border are therefore a light grey line rather than a dark one. There is no darker usable grey that is
  not `$0F` black, so the alternative is a black rule.

## 6. Where the pieces are

- `data/palette_ppu.json`: the table, 54 mappings, the per family reasoning, and the list of collapses above.
- `game/scripts/pp_data/pp_data.gml`: `pp_data_palette_rgb()` resolves the design palette through the table against
  `data/nes_palette.json`; a hole reports itself and draws `PP_COLOUR_MISSING` instead of a guess.
- `game/PrimordialParadox.yyp`: `palette_ppu.json` added as an Included File, so a build carries it.
- `tools/check_runtime_palette.py`: the five part check.
- `tests/test_runtime_palette.py`: 12 rows, one per way of cheating the check.
- `data/sprite_redraw_queue.json`: row `runtime_role_colours_not_2c02` is `done`.

Provenance: the mechanic studied is a role to hardware palette resolve, from the project's own `data/nes_palette.json`
and `knowledge/PALETTE-SYNERGY.md` sections 1, 5 and 7 (NESdev PPU palette structure, the 2C02 luminance rows, the
outline colour choices). No other game's code, art or palette was read for this card. Ours differs by being a data
file with a guard on ramp order and role separation rather than a per scene hand painted table.
