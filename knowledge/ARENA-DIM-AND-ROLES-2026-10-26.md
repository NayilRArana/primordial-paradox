# The dodge dim is a dither now, and the arena spends the four roles every room declares (card t_06ef8607)

Written 2026-10-26 by gamedev, on node CitadelArana. Parent finding: `knowledge\BATTLE-DIM-OFF-PALETTE-2026-10-26.md`
(commit ff212f5, card t_e92abcb0), whose probe is `build\_probe_battle_dim.py`. Every number below was produced on this
PC by a command printed beside it; none is inferred from a report.

## The two defects, in one line each

1. `pp_arena_draw()` dimmed the whole 256x240 frame with `draw_rectangle` at alpha 0.6 in the ink role, which is spec 08
   line 11 read literally and a blended ramp by spec 13 line 21. A real dodge frame of the 2026-10-26 recording measured
   0.6702 against the capture's 0.90 floor because of it.
2. The same function asked for `hazard`, `marker_trail` and `marker`, and the set the demo fights in (`deck_day`)
   declares none of the three, so the dodge phase drew its hazards and the player's marker in `PP_COLOUR_MISSING`
   magenta. The parent measured 251 px of exactly `(255,0,255)` in that frame and the 2026-10-24 run log says so in
   words (`build\first_fight_talk_game.log:88` to `:90`).

## Item 1: why a dither, and which dither

The card asked not to pick the look on my own authority, and named `knowledge\PALETTE-SYNERGY.md:261` as the tiebreak.
That line is not a tiebreak on a dim: it is an open question about whether the room palette roles should resolve into
`data\nes_palette.json`. The tiebreak that does exist is one the card also names, and it decides the question without a
new ruling:

- ART-BIBLE RULE 0 point 1 (Nayil, 2026-10-22, `knowledge\ART-BIBLE.md:286` to `:288`): every scene's colours are picked
  from the 54 usable NES master colours. A blend produces colours that are not among them, so the blend is refused by
  the newer of the two decisions.
- Spec 13 line 21 (2026-10-19): "Two dither patterns only, 50 percent checker and 25 percent ... A gradient is a stack of
  those, never a blended ramp", and line 44: the veil is "a 25 percent dither over the world rather than a transparency
  effect".
- The codebase already draws this line for the other full frame statement: `pp_overworld.gml:579` (card t_531bc76c) calls
  a flood "a palette change, never a blend, so the screen still spends one declared colour".

So the dim stays and the blend goes, which is route A. Within route A, spec 08's own words decide the shape: "the rest of
the field is dimmed", not replaced, so redrawing the field in the `dim` role was refused (it erases the baked strips and
the enemy behind them) and a dither was taken. Between spec 13's two allowed patterns the stronger one is the closer
statement of a 60 percent band, and the two were measured on the recording's own passing frames:

| frame | as recorded | 50 percent checker, 1 px, drawn at 1x | 25 percent dither |
| --- | --- | --- | --- |
| `f_0046.png` | 0.9163 | 0.9663 | 0.9373 |
| `f_0090.png` | 0.9260 | 0.9713 | 0.9448 |

The 25 percent figures are the parent's simulation (its own probe), the 50 percent ones are
`python build\_probe_arena_fix.py`. The parent's 50 percent figure was 0.9582 and 0.9630, higher than these: it laid a
one pixel checker over the 3x recording, so its pattern is three times finer than the game can draw. These are measured
on the frame drawn at 1x and then scaled by 3, which is what the game does.

## Item 1: what the code does now

`pp_arena_draw()` draws the dim with `pp_art_draw_tiled("spr_pp_dither", 0, 0, pp_role_colour("ink"), 1)`. The sheet is
new, written by `tools\art\make_pp_dither.py`: 16x16, a one pixel 50 percent checker, every drawn pixel pure white and
every other pixel a hole. White is the tint identity, so tinting it with a role draws exactly that role's colour, which
is why the screen still spends one declared colour and the code still carries no colour literal.

Why a sheet and not rectangles: the same checker built from `draw_rectangle` calls is 30,720 draw calls a frame at one
pixel cells. Tiled, it is 240 quads in one call. `draw_sprite_tiled_ext` fills from (0,0) to the room edge, and the tile
divides 256 and 240 exactly, so no partial cell lands at the frame edge.

`tools\nes_check.py` gained `--type mask` for this sheet. A mask is a tint source, not art: it may not use `#ffffff`
under the palette rule, because that entry does not exist in the 2C02 table and it is not the colour the frame shows.
What the rule asks of a mask instead is that it carries nothing but the tint identity and holes, and that it is the 50
percent checker. Measured: `python tools\nes_check.py --type mask game\sprites_src\title\spr_pp_dither.png` prints
`16x16 4 tiles 1 colours PASS`, exit 0, where `--type sprite` says `#ffffff off palette at 128 pixels`.

If the mask is not in the art index the field is simply not dimmed and the log says so. Drawing nothing keeps the frame
legal; drawing a blend would not.

## Item 2: the roles the arena can spend

The parent's measurement stands: `deck_day` carries 14 roles and 13 distinct colours, and a 17th colour on screen is what
spec 13 rule 2 forbids. The sets also keep one slot free for `PP_COLOUR_MISSING` (`tests\test_look.py`,
`test_a_set_plus_the_missing_colour_still_fits_the_cap`), so a set may declare at most 15 distinct colours and `deck_day`
could take at most two new ones, not the three the arena asked for. The arena therefore asks for roles every set
declares, the same four card R48 gave the battle field (`pp_battle_director.gml:1060` to `:1068`):

| role | hex | relative luminance | every set | arena use |
| --- | --- | --- | --- | --- |
| `text` | `#c8c8d4` | 0.5834 | yes | the marker, 8x8, and the border flash |
| `dim` | `#4a4a58` | 0.0605 | yes | the hazards |
| `paper` | `#1c1c24` | 0.0146 | yes | the 4 step trail |
| `ink` | `#0b0b0f` | 0.0035 | yes | the frame, and the dim's checker |

Measured by `python build\_probe_arena_roles.py`: `text` is not only the brightest of the four, it is the brightest role
in the whole master palette bar `sea_5` at 0.5838 and the master's own `marker` at 0.5828, and neither of those is in
every set. So spec 08's "the marker is the brightest palette colour" is now a measurement, and it is pinned by
`tests\test_arena_dim_and_roles.py`.

The compromise, stated rather than hidden: with four roles there is exactly one bright one, so the hazards had to be dark.
Measured by `python build\_probe_deck_contrast.py` against the seven colours `bg_battle_deck_night` is drawn in, weighted
by the area each covers, the contrast of each shared role against the field is:

| field colour | share | dim | paper | ink | text |
| --- | --- | --- | --- | --- | --- |
| `#0000bc` sky | 29.6 pc | 1.40 | 1.39 | 1.61 | 7.34 |
| `#7c7c7c` grey | 25.9 pc | 2.09 | 4.05 | 4.71 | 2.52 |
| `#0000fc` sea | 23.1 pc | 1.00 | 1.94 | 2.25 | 5.27 |
| `#000000` black | 9.6 pc | 2.41 | 1.24 | 1.07 | 12.67 |
| `#fcfcfc` white | 7.0 pc | 8.49 | 16.49 | 19.15 | 1.62 |
| `#0078f8` | 2.9 pc | 2.09 | 4.06 | 4.72 | 2.51 |
| `#3cbcfc` | 2.0 pc | 4.06 | 7.89 | 9.16 | 1.29 |

Share of the strip under 3:1: `dim` 91.0 pc, `paper` 62.3 pc, `ink` 62.3 pc, `text` 37.7 pc. Nothing dark clears the 3:1
the art bible uses for "these can be told apart" across the deck's blues: `dim` sits at 1.00:1 against the sea's
`#0000fc`, which is the same luminance in a different hue, and `paper` and `ink` are no better on the sky at 1.39 and
1.61. `dim` was chosen because the checker guarantees half of every hazard's edge sits on the ink half of the dither,
where it measures 2.41:1 against that same role's own dark pixels, and because it is the only one of the three that
reads at all against black. The hazards on the night deck are therefore legible by shape and texture more than by tone.

That is the honest limit of the code route, and it is why a second card is filed rather than a quiet data edit made: to
keep the marker brightest and give the hazards a bright role, the set needs a colour it does not have, which is a re-cut
of `deck_day` and therefore a ruling, not a bug fix.

## What the fix measures on the real dodge frame

`python build\_probe_arena_fix.py` takes the recorded dodge frame, inverts the band the build drew (0.4 * in + 0.6 * ink,
the only way to recover the field under it, which is lossy), lays the new checker over it, redraws the magenta marks in a
declared role, and measures with the verifier's own loader at the recording's own 3x:

```
sample_20_23s48.png  768x720 at 3x
  today, as recorded:                    0.6702  (under the floor)
  magenta marks redrawn as dim: 125 px
  with the fix drawn over it:            0.9594  (un blend is lossy, so this is pessimistic)
  the same, every pixel snapped:         1.0000  (what a lossless capture would read)
```

## What is proven, and what is not

Proven: the project compiles with the new draw (`python tools\integration_build.py` prints `BUILD PASS: Igor compiled the
project`, exit 0, runtime-2026.0.0.23); the mask is a one pixel 50 percent checker of one colour (`nes_check --type mask`
PASS, and the same geometry asserted in the test); the arena asks only for roles every set carries, and its marker role
is the brightest one there is (both pinned); and the frame the fix draws measures above the floor on the recording's own
pixels.

Not proven: no frame of the running game has been captured with this draw. The recording on disk is the old build's, the
card forbids re-cutting it, and the capture tool would overwrite `output\first_fight_verify.json` and the frames the
parent's finding rests on. The next capture of the first fight is what closes that, and the number to expect is above
0.95 on every dodge frame rather than 0.67.

## What was not done

No threshold moved: `VIDEO_PICTURE_MIN` is still 0.90 and `palette_share` still allows 12 px. No frame, recording or
report was edited; the only new frames written are the probe's own under `build\resume_frames\_probe_out\`. No entry was
appended to `data\palette.json`, whose digest is untouched, and nothing was added to any room palette set. Nothing was
posted, published or pushed, no window was opened, `a protected profile` was not touched.
