# ART-B-OURANOS 2026-10-30: the old man on the high street, hand authored

Card t_760a7325. Nayil picked direction B, late NES polish, on 2026-10-26 19:00: bold dark outlines, three tone
shading lit from the top left, detailed tiles. This page is the record of the redraw of queue row
`cand_r18_ouranos_ow` (`data/sprite_redraw_queue.json`, label `OURANOS`), the old man who stands on the high street
in scene `s2_high_street`.

The cell is 16 x 24, the cell the queue row itself asks for ("over world stander, 16 x 24 cell"). The sheet is
`game/sprites_src/chars/ouranos_ow24.png`, one frame, the `down` stand the game draws, written by
`tools/art/make_characters_v2.py --only-style-b`. No state was added or removed.

## 1. What was wrong, in one sentence

He was the shared tall puppet: the same head as the rest of the cast, a straight back, no beard, so a man the game
calls old read as another young man in a coat. Age has to arrive through posture, hair and outline weight, because
at 1x there is no room for the detail that would otherwise carry it.

## 2. What changed in the drawing

The figure is now authored as a whole cell instead of assembled from the parametric body. `OLD_MAN_DOWN` is the
drawing, sixteen characters a row, with the tone roles named in the comments. The parametric path is untouched for
every other figure: `tall_frame()` returns `old_man_frame()` when the build names `"grid": "OLD_MAN_DOWN"`.

| change | where | why |
|---|---|---|
| posture: the shoulders sit one row under the jaw, the head is narrower than them by four columns | rows 6 to 10 | a stoop is a relationship of head to shoulders, not a bent line. Head 10 x 5 against shoulders 14 is what makes him read as old before any face is visible. |
| hair: a bald crown and a beard that is wider than the jaw and tapers to a two pixel point | rows 1 to 14 | the card names hair. White over the whole skull with no hairline drawn is a bald head; the beard below the jaw is what puts the age on the silhouette. Measured: 9 rows from the jaw, 51 px. |
| outline weight: ink at the jaw corners, both beard flanks, the brow, the arm sockets, the cuffs and the hem | rows 4 to 17 | the card names outline weight. Ink is placed where the cast puts tone, so the shoulders and the beard edges are lines and the coat is flat. Measured: 112 ink px of 280 drawn, 40.0 %. |
| the shade pass covers the head and the beard only | `OLD_MAN_SHADE_ROWS` | direction B's "the last pixel of every run is the shadow". The coat is already two tones; shading it as well would put a mid entry on top of the mid entry. |
| legs: bent knees, close feet | rows 18 to 22 | the same stoop read in the lower half, so the figure is not a head on a straight column. |

## 3. The numbers as shipped

Drawn 2026-10-30 by `python tools/art/make_characters_v2.py --only-style-b`, from the working tree. The generator
refuses a cell with a fourth colour in a tile, an outline leak, an entry that is not a 2C02 output, or a figure that
fails `old_man_read()`, so this sheet cannot be written red.

| sheet | tile colours worst | ink share | light correct/wrong | orphans | leaks | dither | drawn px | frame box |
|---|---|---|---|---|---|---|---|---|
| `ouranos_ow24` | 3 of 3 | 40.0 % | 18 / 0 | 0 | 0 | 0 | 280 | 14 x 22 |

`old man read: beard 9 rows / 51 px, head 10x5 against shoulders 14 (narrower by 4), ink 112 px (40.0% of 280
drawn)`. He carries the lowest ink share of the six figures drawn so far (the Percy cast runs 46.8 to 49.3, Zeus
43.3, Konrad 41.3), which is the measurement that matters: the read comes from a white head and beard against a
grey coat, not from being darker than the others.

## 4. The checks the card asked for

| check | command | result |
|---|---|---|
| NES audit on every frame | `python tools/nes_audit_all.py --only ouranos` | `class asset 1 file(s), 1 pass, 0 fail`, exit 0 |
| NES audit, whole tree | `python tools/nes_audit_all.py --no-write` | `PASS 193 file(s), 24 failing (sheet 20, capture 4)`; every gated class clean (asset 142/142, frame 22/22). The 24 are contact sheets and window captures under `output/`, pre-existing and unrelated. |
| sprite rules | `python tools/nes_check.py game/sprites_src/chars/ouranos_ow24.png --type sprite` | `16x24 6 tiles 3 colours PASS` |
| section 2 rules | the generator's own report | worst tile 3/3, no orphans, no leaks, no dither, light 18 correct and 0 wrong |
| before and after sheet at 3x | `python tools/art/art_b_characters_before_after.py --asset OURANOS` | `output/art_b/ART-B-CHARACTERS/ouranos_before_after_3x.png`, columns BEFORE, R18 seed141, R18 seed142, AFTER |
| eye critic, after higher than before on readability | `python tools/art/art_b_meta_eye.py <frame> <frame>` | before nes 7 / readability 5 / charm 2; after nes 7 / readability 8 / charm 4 |
| suite selection | `python -m pytest tests -q -k "art or palette or nes"` | `328 passed, 2098 deselected, 164 warnings in 204.97s`, exit 0 |

The eye critic ran on the project's own `tools/eye_critic.py` with `PP_AI_BACKEND=meta` (card EYE-CRITIC-META's
route), model `muse-spark-1.3`, one 256 x 240 frame per column, all three reviews describing the picture they were
given. Reviews: `output/eye_reviews/ouranos_before_frame_256x240_20261031T030845Z.md`,
`..._after_frame_256x240_20261031T030914Z.md`, `..._r18_seed142_frame_256x240_20261031T031019Z.md`.

## 5. Why no R18 candidate was adopted

The card allows a candidate "only if one is genuinely better". Both kept candidates were built and scored on the
same rubric, same model, same day: `seed142` (the row's rank 1) took nes 8, readability 6, charm 3, and `seed141`
(the pack's before) took 7, 5, 2. The hand authored cell took 7, 8, 4. So the candidate is one point better on
authenticity and two worse on the dimension the card names, and the redraw stands.

## 6. On the high street at 1x

`output/art_b/ART-B-CHARACTERS/ouranos_on_street_1x.png` (and the 3x beside it) pastes the shipped sheet onto
`output/art_b/ART-B-MAPS/street_frame_1x.png` with his feet on the pavement. The 104 background pixels he stands on
are one colour, `#bcbcbc`. Against it: ink 188 away, white 64, mid grey 64, and 0 of his 280 drawn pixels sit inside
the 24 band where a sprite starts to disappear into the ground. His outline is what separates him; the tones hold him
too.

## 7. Provenance

Hand authored in `tools/art/make_characters_v2.py` by this lane: comments, spans and the project's own outline and
shade passes. No Muse Image call, no generated art, no decompiled code, no third party artwork, so `CREDITS.md` is
unchanged. The five other cast sprites were hashed before and after (`sha256sum -c`): only `ouranos_ow24.png`
changed.
