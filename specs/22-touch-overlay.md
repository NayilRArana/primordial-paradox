# Spec 22: the touch overlay

Goal: give the three touch targets the same seven actions the keys and the pad already give, without
changing the Windows desktop build and without letting any module read a finger outside one place.

## Rules

1. Touch is the second input source. pp_input stays the only reader of keys and pads (spec 02 rule 1),
   and pp_touch is the only reader of a finger. It publishes the SAME action ids into the action table,
   so every other module keeps reading one action map and never learns whether a key or a finger set it.

2. The overlay runs only on the touch targets: os_android, os_operagx and os_browser. On os_windows and
   every other target pp_touch_init reports disabled, pp_touch_sample returns at once and pp_touch_draw
   returns at once, so the desktop build is byte for byte the same game it was before this spec.

3. The controls are a left thumb pad and right thumb A, B and Menu, drawn with pp_role_colour in the
   current room palette and the sheet font (spec 13). A palette pass recolours them with the room.

4. The overlay is semi transparent and it only adds held actions. It never hides the game and it never
   eats a keyboard key or a gamepad button.

5. Never over text. While overworld or scene dialogue is open the controls re-lay to the top edge, clear
   of the dialogue box, and the Menu button hides, so every line stays readable and A still advances it
   (spec 05). The draw and the sample read the same layout, so what the player sees is what the finger
   hits.

6. The pad is 8 way. The finger's angle inside the ring picks one of eight sectors, and the sectors feed
   the same four walk actions pp_input_update_vector already turns into the walk vector (spec 17 free
   movement). A finger owns the control it first touches until it lifts, so a thumb that slides off the
   pad keeps walking instead of dropping the control.

## Notes

- Provenance: knowledge\PROVENANCE.md, entry "pp_touch", written from this spec.
- Tested by: tests\test_touch.py.
- The overlay is proved by rendering: tools\render_touch.py writes frames to output\android_touch\.
