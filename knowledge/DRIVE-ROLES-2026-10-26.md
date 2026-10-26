# The drive film's palette roles: seven asks no set answers, and why nobody saw the magenta

Card t_415541ee, 2026-10-26. Found while closing t_769b545d. Measurement first, then the fix; this note is the
measurement, kept because the numbers outlive the card.

## What was measured

`game/scripts/pp_drive/pp_drive.gml` asked the palette for eleven roles. The set the drive map names, `drive_night`
(`data/maps/all.json`, room `drive_m4_corridor`), declares thirteen and answers four of them. The probe
(`build/_drive_roles_probe_pre_fix.json`, run 2026-10-26 this session) printed the lookup role by role, and the answer is
`pp_role_colour`'s own rule: a role the set does not declare draws PP_COLOUR_MISSING (255, 0, 255).

| role asked | in drive_night | in every set |
| --- | --- | --- |
| ink, paper, dim, text | colour | yes |
| accent | PP_COLOUR_MISSING | no |
| window | PP_COLOUR_MISSING | no |
| window_edge | PP_COLOUR_MISSING | no |
| window_shadow | PP_COLOUR_MISSING | no |
| marker | PP_COLOUR_MISSING | no |
| marker_trail | PP_COLOUR_MISSING | no |
| hazard | PP_COLOUR_MISSING | no |

So the card's six `accent` bands were six of a class of seven roles and thirty-three draw sites. `accent` was not the
worst of them: `window` paints the sky, the Thames and the docks backdrop, `window_shadow` paints the hills, the storm
cloud and the chalk cutting's walls, so a draw under `drive_night` would have been mostly magenta.

The log a draw would write, once per role per set:

```
PP: role accent is not in the room palette set drive_night, drawing it as PP_COLOUR_MISSING
PP: role hazard is not in the room palette set drive_night, drawing it as PP_COLOUR_MISSING
PP: role marker is not in the room palette set drive_night, drawing it as PP_COLOUR_MISSING
PP: role marker_trail is not in the room palette set drive_night, drawing it as PP_COLOUR_MISSING
PP: role window is not in the room palette set drive_night, drawing it as PP_COLOUR_MISSING
PP: role window_edge is not in the room palette set drive_night, drawing it as PP_COLOUR_MISSING
PP: role window_shadow is not in the room palette set drive_night, drawing it as PP_COLOUR_MISSING
```

## Why no recording shows it

The room asked for the `ui` set (`#macro PP_DRIVE_PALETTE "ui"`), and `ui` declares all eleven, so every capture of the
drive to date drew a picture in a set the drive never plays in. The twelve committed frames (`output/drive/`, written
from inside the room's draw on 2026-10-23) carry zero PP_COLOUR_MISSING pixels for exactly that reason. They are also
stale in the other direction: their palette share against `data/palette_ppu.json` measures 0.0000 to 0.2125, because they
were captured before card t_54db4d0f mapped the 54 design colours onto 2C02 output. Neither the colour nor the floor can
be read off them today.

## The fix

The rule is card R48's (battle field) and t_769b545d's (dialogue box and map fallback): a screen that can be drawn in any
room spends only the roles every palette set declares, and here that is `ink`, `paper`, `dim`, `text`. `text` is the
brightest of the four, measured, and takes the marks that must read against a dark field. The seven replaced roles map by
value:

| old role | colour | new role | why |
| --- | --- | --- | --- |
| accent | #d8a55c | text | the headlight pool, a lit clock face, water lights, dock lamps: all must read |
| marker | #e8c65a | text | lane paint, ship windows, the lightning bolt |
| window_edge | #c8c8d4 | text | the trim line along the car is already text's own colour |
| hazard | #c24040 | text | the bumper lamp and the bright container row |
| marker_trail | #b38f28 | dim | a trail behind the pool does not need to read |
| window | #081420 | ink | sky, water, the docks backdrop and the caption plate are the darkest field |
| window_shadow | #2e2e3a | paper | a silhouette one step off ink |

The room now draws in `drive_night` (`#macro PP_DRIVE_PALETTE "drive_night"`), the set the map names, so a capture proves
the picture the shipped scene draws and not one from another set. No room palette set was changed: `drive_night` keeps
its thirteen roles, and the four the film spends resolve in it.

## What is still unproven

No take was made in this pass. `python tools/capture_drive.py` answered

```
P: idle gate REFUSED: a desktop automation is running (codex-computer-use-swift.exe, codex.exe) ...
```

so the check that matters on screen, `grep "PP: role" build/capture-drive-game.log` empty on a fresh drive run and the
twelve frames at or above the 0.90 picture floor, is **unmeasured**, not passed. The source compiles
(`Igor.exe -- Windows Compile -> exit 0, Igor complete.`) and the role lookup is measured at the data level by
`tests/test_drive_roles.py`, which fails on the pre-fix module (4 of its 5 rows) and passes on the fixed one.

To close it: run `python tools/capture_drive.py` when the idle gate is open, then `grep "PP: role"
build/capture-drive-game.log` (expect no line) and re-run the probe in this card's workspace for the frame shares.
