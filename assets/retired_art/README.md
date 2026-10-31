# assets/retired_art: art that was retired but had no other copy

Card t_4e54cc9e deleted `game/art` on 2026-10-23 (ruling 3 in
`knowledge/PALETTE-RULINGS-2026-10-23.md`: the sprite queue measures `game/sprites_src`, and
`game/art` retires). Twenty of the twenty two sheets in that folder were either a tracked copy of
a `game/sprites_src` sheet or output that a tracked generator can redraw, so deleting them lost
nothing. These two were not: no sheet with these names exists under `game/sprites_src` anywhere.

| file | sha256 | what it was |
| --- | --- | --- |
| `spr_player_ow.png` | `112d5a97b5abd2f8b3327ad367d9c31cba5b139b1c56bd052db5ba79c0fa6e89` | 128x16, 8 frames of 16x16, 5 entries, `nes_check` PASS: the 2026-10-23 redraw of the player |
| `spr_gate_sentry_ow.png` | `f4be8f6c5cf01ec5e001e2e8f7789d1cec844f8014d60a72e83f97538df92248` | 128x16, 8 frames of 16x16, 4 entries, `nes_check` PASS: the 2026-10-23 redraw of Morgan, the gate sentry |

Both names are retired: the overworld walker draws the `game/sprites_src/chars/spr_*_ow` sheets, so
these drawings are superseded rather than lost, and the queue rows for them are retired on
`data/sprite_redraw_queue.json`. `tools/art/make_redraw_rows.py` can redraw both (it now writes
`output/redraws/`, not the retired folder), and running it on 2026-10-23 reproduced both files byte
for byte, so the kept copies are evidence rather than the only way back.

These two files were untracked when they were copied here, and they stay untracked until the next
commit: the pre-commit suite is red on the audio lane's uncommitted `pp_05_small_ship_v4.ogg`, which is
not art. Until that commit lands, the only copy of them in a clone is no copy at all, which is exactly
the problem this folder was made to avoid.

Nothing in the build reads this folder. It is kept because it was the only copy at retirement, not
because it ships.
