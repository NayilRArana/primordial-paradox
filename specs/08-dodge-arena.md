# Spec 08: dodge arena

Status: spec, 2026-10-19. No code yet. Numbers are DECISIONS.

Goal: on the enemy turn the field dims and a framed box appears with a bright marker the player steers to avoid
hazards. Every hazard is telegraphed, the player's marker is always the highest contrast thing on screen, and a hit
costs one enemy attack's worth of health.

Geometry
- Box 160x100 centred at (128, 120); 2 pixel frame in the first ink, 1 pixel dark line outside; the rest of the field
  is dimmed to half brightness by a 50 percent checker of the ink role, one pixel cells, drawn from the 16x16 mask
  `spr_pp_dither` tinted to that role.
  Amendment, 2026-10-26, card t_06ef8607. This line read "the rest of the field is dimmed by a 60 percent black
  rectangle" from 2026-10-19, and a rectangle at alpha 0.6 is a blended ramp: it turns every pixel under it into a
  colour outside the 54 master entries, which spec 13 line 21 forbids and ART-BIBLE RULE 0 point 1 refuses. A real dodge
  frame of the 2026-10-26 recording measured 0.6702 against the capture's 0.90 picture floor, and the dim was the whole
  of the difference (knowledge\BATTLE-DIM-OFF-PALETTE-2026-10-26.md). The density is kept, the mechanism is not: a 50
  percent checker halves the field's brightness, the closest legal statement to a 60 percent band, the same frame
  measures 0.9582 with it, and every pixel on screen stays a colour the palette names. The field is dimmed, not
  replaced, so the baked strips stay visible through the checker.
- Marker 8x8 in the brightest palette colour, with a 4 step trail, starting at the box centre every phase.
  Amendment, 2026-10-26, card t_06ef8607. The arena spends roles, not colours, and it may only ask for roles every set
  in `data\room_palettes.json` carries, which are ink, paper, dim and text, the same four card R48 gave the battle
  field. The marker is text, the brightest of the four and the brightest role in the master palette; the hazards are
  dim, so they read as solid blocks against the dimmed field; the trail is paper, the quietest of the four, so the
  marker stays the highest contrast thing on screen; the warning flash is text.
- Hazards are 8x8 or 16x16 with a hitbox 2 pixels smaller per side, so near misses read as near misses.
- Marker speed 2 pixels per step in 8 directions from the input vector (spec 02), clamped inside the box.

Fairness rules
1. Every pattern opens with a 12 step warning: the border flashes twice, no hazard on screen.
2. No hazard spawns within 24 pixels of the marker.
3. No hazard spawns in the last 12 steps of a pattern.
4. Invulnerability 30 steps after a hit, marker blinking every 4 steps; an overlapping hazard does not re-hit.
5. Hard cap 900 steps per phase, so a data bug cannot trap the player.

Feedback: one hit costs the enemy's attack value, minimum 1; 6 steps of border flash, one low sound, health bar
animates over 12 steps. Reaching 0 ends the phase and the battle goes to defeat. A clean pattern plays a chime and shows
"clear" for 12 steps.

Lifecycle: the arena asks the pattern player (spec 09) for hazards each step; the phase ends when the pattern is done
and no hazard remains, or at the cap.

Debug: F2 steps one frame; hitboxes drawn as 1 pixel outlines; a preview room runs any pattern id with a driven marker,
with no battle around it.

PP content: the tutorial's single slow hazard teaches the box; Percy's three patterns are the first real weaving test;
Hector's pattern punishes edge hugging; Kronos reuses Percy's shapes at higher speed, which is only possible because
patterns are data.

Acceptance (Nayil)
1. The warning flashes, the marker starts centred, the first hazard is never on top of it.
2. Holding into a wall stops the marker at the border without jitter.
3. One hit costs exactly one attack value, then nothing for half a second even if a hazard overlaps.
4. A clean pattern shows the clear text and returns the menu.
5. A deliberately broken speed value in the preview room ends at 15 seconds and the game does not hang.

Out of scope: shooting back, a second marker, gravity, touch dragging.
