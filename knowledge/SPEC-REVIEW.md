# Clean-room review of the specs

Rule, set by Nayil and restated by the manager after the breach of 2026-10-19: no code is written from a spec that a
fresh reviewer has not confirmed from public genre design notes and the official GameMaker manual only. Specs 01 to 13
were drafted before the notice, so each of them started as `pending` here.

This file is the ledger for that gate. `tools/check_spec_review.py` reads it:

- `python tools/check_spec_review.py` reports every pending spec by name and exits 0, so the debt is visible on every
  run without blocking work that is not derived from a spec.
- `python tools/check_spec_review.py --strict` exits 1 while any spec is pending. It is the check an implementation
  card runs before it writes code, and the check the gate card turns green.

A row may only say `confirmed` or `rewritten` when it names a reviewer and a date. `rewritten` means the spec text was
changed in that same change; the note says what changed and why. A row may not say `reviewed`, `checked` or `ok`.

Reviewer: code-review. Date: 2026-10-19. Cards: t_ec0fb8be did the review and t_e78500a3 was the gate pass after it,
which re-read the manual pages the specs cite and added the two findings listed at the end of this file. The full
reasoning, including the three closest calls, is in the "clean-room re-review 2026-10-19" section of
`knowledge\PROVENANCE.md`; the module rows are in `knowledge\CLEANROOM-REVIEW.md`.

| Spec | Status | Reviewer | Date | Note |
| --- | --- | --- | --- | --- |
| specs/01-state-machine.md | confirmed | code-review | 2026-10-19 | Mode enum, one owner, one request door, fades and input lock are our decisions. What happens to the map under a battle is not asserted here and stays open as delta T1. |
| specs/02-input.md | confirmed | code-review | 2026-10-19 | Action table, one sample point and edge derivation from the manual's keyboard_check_pressed and Event Order pages; deadzone and repeat are ours. |
| specs/03-camera-and-scaling.md | confirmed | code-review | 2026-10-19 | Integer scale, one viewport and an application surface resize from the manual's page, whose own example is camera size times a resolution scale (re-read 2026-10-19). The page also states that Draw events draw to that surface while Draw GUI does not, which is what lets `display_set_gui_size(256, 240)` stand beside a scaled surface. Dead zone, look ahead and the 4 pixel cap are ours. |
| specs/04-overworld-rails-and-triggers.md | rewritten | gamedev | 2026-10-26 | Rewritten twice on Nayil's orders of 2026-10-26: card t_771e78ef set "hold to walk, tap for one tile" and made the left stick walk, and card PP-FREE-MOVE replaced the tile walk with free movement in pixels, eight directions, at `PP_WALK_SPEED`, with a 10x6 feet hitbox resolved per axis, a 3 pixel corner nudge, a confirm that reaches in front of the feet, touch triggers that fire once per entry and a camera pinned to the walker while he walks. The 2026-10-19 clean-room verdict stands on everything else: tile grid, separate collision grid, trigger list, rails and visible markers are genre-design section 6, and the trigger lock and marker respawn are our fixes. Nothing outside this repository was read for either change and no expression was taken from any game. |
| specs/05-dialogue.md | confirmed | code-review | 2026-10-19 | Typewriter, portrait, pages and conditional choices are the ordinary text box of the genre; the geometry and the two control codes are ours. Its own text metrics do not fit its line length: 168 pixels of text area fits 21 characters at an 8 pixel advance, not the 30 it states. That is delta C4, a number for Nayil, not a clean-room finding. |
| specs/06-cutscene-runner.md | confirmed | code-review | 2026-10-19 | A data command list with one blocking command at a time and branch as the only control flow is the ordinary scripted scene form. |
| specs/07-battle-director.md | confirmed | code-review | 2026-10-19 | Five entry menu, trust and spare thresholds and no EXP are genre-design sections 3 to 5. Closest call: the turn loop shape, which is the spec's own phase list. |
| specs/08-dodge-arena.md | confirmed | code-review | 2026-10-19 | Box, marker, telegraph, damage per hit and invulnerability are genre-design section 2; every number is a PP decision. |
| specs/09-bullet-pattern-recipes.md | confirmed | code-review | 2026-10-19 | Data recipes and the fairness ladder are ours and need no public source: the emitter fields are our own generalisation, asked for by authoring needs. The angle convention is stated in screen terms while the engine's own maths runs the other way, which is delta C5 and is named there rather than settled here. |
| specs/10-route-ledger.md | rewritten | gamedev | 2026-10-22 | Additive refresh by card t_48020b30: the per enemy exit rows (an id, one of `down`, `spared` and `turned`, and the round) and the fight verdict (`quiet`, `mixed`, `violent`), plus rule 6 (one door, row then verdict then counter) and rule 7 (a turned enemy moves no counter), two acceptance cases and an out of scope line narrowed to name what is still not built. The source of the addition is `knowledge\FOX-STYLE.md` section 2 and this project's own spec 11, nothing outside the repo was read, and the counters, flags, derived route and their conditions are unchanged. |
| specs/11-save.md | rewritten | gamedev | 2026-10-22 | Additive refresh by card t_48020b30: an "Optional keys:" paragraph naming `fight_exits`, and rule 5 extended to say a load restores the last fight's exit rows and that a file without the optional key still loads with an empty record. Nothing in the 16 required keys, the format number, the backup rotation, the validation order or the manual citations changed, so the code-review verdict of 2026-10-19 on those parts stands. |
| specs/12-audio.md | confirmed | code-review | 2026-10-19 | Bus priorities follow the manual's audio_play_sound page (re-read 2026-10-19): the priority argument decides which sound is stopped when the channel limit is reached, and the third argument is a whole file loop. Crossfade is ours, built on the gain functions, not a manual feature. Rule 3's loop point claim is unsupported by that page and is open defect C1 in SPEC-DELTAS, not a clean-room finding. |
| specs/13-8bit-look.md | confirmed | code-review | 2026-10-19 | Palette size, dither and frame rules are ours; the sprite convention is genre-design section 7. The per pixel check in rule 2 cannot run yet, as delta C3 records. |
| specs/14-title-screen-drive.md | confirmed | gamedev | 2026-10-21 | Parallax layers at different scroll rates, a scrolling road and a title logo over a scene are the ordinary shape of a title screen and the shape the engine already had for the overworld (spec 04's camera and map). The scene itself is original: the two reincarnations driving from London to Southampton, the night drive and the waltz are Nayil's notebook and this project's own invention, and no element of it comes from a studied source. The pixel art, the palette, the 8 pixel font and the cue names are this project's own, checked by tools\art\make_title_ui.py against data\palette.json. The sound hook names are spec 12's cue idea. Reviewed against the public manual pages for sprite_add, draw_sprite_part_ext and audio playback, and against genre-design sections 2 and 7, and against nothing else. |
| specs/15-env-tiles-ship.md | confirmed | gamedev | 2026-10-22 | Read at the source on 2026-10-22 by card G0-3, which did not write this spec or its code. The hardware rules are the NES PPU's own (a 16x16 background area carries 3 colours plus the shared backdrop, an 8x8 sprite carries 3 plus transparent), restated from `data\nes_palette.json`, whose own citation is the NESdev wiki's PPU palettes page and the 2C02 `.pal` decode set. Every tile is drawn by `tools\art\make_env_ship.py` from geometry, with no sampled art: the placement, the 48 tile names, the solid flags carried on the tile rather than the map, the flag derived collision layer and the animation of the sea and the porthole glare are this project's own decisions. The 10 colour scene budget is stricter than spec 13's 16, so the two agree rather than conflict. Nothing outside this repository and that public hardware document was read for it. |
| specs/16-talk-command.md | confirmed | gamedev | 2026-10-22 | Read at the source on 2026-10-22 by card G0-3, which did not write this spec or its code. The one study reference the spec names is the ACT command as a DESIGN idea (a menu entry where the player speaks and the enemy answers), and a design idea is not protected expression, so nothing is taken from it: the system message, both enemy cards, the pool lines, the cache key, the validation pipeline V1 to V9, the clamp arithmetic, the offline keyword scorer and the budget are this project's own writing and engineering. The prompt is written as a data/instruction boundary rather than as a quoted prompt from anywhere, which is the safer shape and also the original one. Section 17 lists six deltas it opens, including spec 07's fifth menu entry and one sentence needed in spec 05; those are decisions for the manager and are recorded there, not settled here. Hostile input handling was judged as engineering, not as taken text: clamping, an allowlist schema with no extra fields, a fallback pool and a per battle call cap are our own choices. |
| specs/17-action-movement.md | pending | code-review | 2026-10-22 | FAIL on the writability gate, card t_eab7904b; full text in `knowledge\REVIEW-ACTION-PHASES-2026-10-22.md`. Five blocking findings, each named by line there: the deep landing cancel allows a whip during the 10 step stun while the cancel needs the press 12 to 19 steps before contact (section 5 rules 4 and 5 against section 3 rule 6); the arc table that "commits in data" names no file, key, type or range; F4 to F6 are new debug keys with no rows in spec 02's key table, whose rule 1 makes it the only key reader; `whip_level` is called a save field with no type while spec 11's 16 key list has no such key and no delta is written; and the proposed `action` mode would own "confirm on doors", a second owner of the job spec 04 rule 2 already does. Not confirmed and not rewritten. |
| specs/18-boss-phases.md | pending | code-review | 2026-10-22 | FAIL on the writability gate, card t_eab7904b, against sha256 `dfaa8b8e` (commit b066c64, 512 lines, 14:40:42). Full text in `knowledge\REVIEW-ACTION-PHASES-2026-10-22.md`. Seven blocking findings, each named by line there: the returned interrupt scene id has no consumer in spec 06, whose `battle` command takes no result scene and whose only control flow is `branch` on a flag (section 4 item 4 against spec 06's command table and rule 3); the 30 step break has no home in spec 07's turn flow, which has no break state and no rule saying the enemy turn's 12 step telegraph is skipped (section 1 against spec 07 rule 1); acceptance 7 asks for a refusal of a phase row on a regular enemy that section 7's eleven refusals do not contain; the 16 character `CONTROLS FLIPPED` label centred on x 128 spans x 64 to 192 and so falls 8 px outside spec 05's text area, which starts at x 72; the slow key the spec depends on is not in spec 08 and no delta assigns it (C18-5 covers only the second marker and the fixed speed 2); C18-2's `interrupt` object omits `unless_flag`, which section 4 defines and C18-7 says the enemy keeps; and the attack band is undefined, since Percy's row is 3 to 5 while phase 3 asks for max 6 and no refusal mentions `attack`. Was 440 lines at 13:52 and rewritten by its owner card t_00a94c86 through five hashes (63287b9f, cf265d5e, c62bf910, 158864f2, 8400125b) to adb31da2 and then dfaa8b8e; the kill wall numbers this review flagged at adb31da2 were answered in b066c64 and re-measured here over every percent from 1 to 99 (9 percent at the 12 ceiling, 14 with `tide_step`, crossing at 10 and 16 hp on 120). Not confirmed and not rewritten. |
| specs/19-llm-talk.md | pending | - | - | Written 2026-10-22 by card t_ec26b957, which is not a clean-room verdict. Gamedev approved its ten questions on 2026-10-22 (`knowledge/GAMEDEV-DECISIONS-2026-10-22.md` D6) and D5 there supplies the architecture (the shipped build makes no network call, every model output is baked into `data/`, `PP_AI_MODE=replay` is the demo path). What a reviewer still has to confirm: that the prompt contract, the four field schema, the effect table and the fallback ladder are reachable from this repository's own specs 05, 07, 16, 17 and 18 plus public genre design, with the bake architecture taken from D5 and nothing read outside the repo to write it. Checks run by the author on the spec as landed: the schema validates as draft 2020-12 and refuses six bad instances for the right reason, every effect maps to a row that exists in spec 16 section 2 with the same number, the font's 46 glyphs and the 28 column arithmetic are measured from `data/ui_layouts.json` and SPEC-DELTAS C4, and the cost table is recomputed from the measured token counts. Not confirmed and not rewritten. |

## What a confirmed row does and does not claim

It claims the spec's content is reachable from public genre design and the official manual, read by a reviewer who did
not open the quarantined copies. It does not claim the spec is correct: two factual defects are open in
`knowledge\SPEC-DELTAS.md` (C1 on audio loop points, C3 on the sprite pixel check), and both are recorded where they
belong rather than hidden inside a clean-room verdict. It also does not claim a text comparison against the quarantined
copy was made, because that comparison is the one thing the rule forbids.

## Gate pass, card t_e78500a3

The first pass read the specs against public material. This pass read them against each other and against the manual
pages again, and ran the arithmetic the specs state as if it were the acceptance test.

Pages re-read at the source today, all public, all five agreeing with the spec text:

- application_surface: the page's own example is camera size multiplied by a resolution scale, which is the pattern
  spec 03 uses, and it separates Draw events (this surface) from Draw GUI (not this surface), which is what makes
  `display_set_gui_size(256, 240)` correct next to a surface already scaled by the same factor.
- audio_play_sound: the priority argument decides which sound is stopped when `audio_channel_num` is reached, the
  third argument is a whole file loop, and the call returns a unique index. This confirms spec 12 rules 1 and 2 and
  leaves rule 3's loop point claim exactly as unsupported as C1 says.
- json_parse: an invalid value throws. Confirms spec 11 rule 6.
- Save/Load async event: `id` and `status`, on buffer_save_async and buffer_load_async. Confirms spec 11's file rule.
- json_stringify: an asset is stored as an internal handle whose index changes between runs, and assets are saved by
  name. Confirms spec 11's rule that ids are names, never indexes.

Arithmetic checked and found sound: 1080p at scale 4 is 1024x960 as acceptance 5 says; 256x240 is 16 by 15 tiles of
16 pixels; 900 steps is 15 seconds and 30 steps is half a second; 9 hues by 6 levels is 54; the FIGHT mapping in delta
T7 lands inside the 2 to 12 the spec promises.

Two findings, both new, both recorded rather than fixed inside a verdict, because each is a decision number and not a
traceability problem:

- C4, specs\05-dialogue.md: the stated 30 characters per line needs a 5.6 pixel advance, and the 168 pixel text area at
  an 8 pixel advance holds 21. Dialogue is the slice's main visible output, so this would have been found the hard way.
- C5, specs\09-bullet-pattern-recipes.md: the data says 90 degrees is down, the engine's own angle maths turns the
  other way, and the manual states that in a picture rather than in words. The fix is a named conversion in one place
  and one test, not a change to the authored data.

One conflict between a knowledge file and a spec was corrected here: `knowledge\genre-design.md` section 2 gave the
stick speed as 1.6 with an 8 direction clamp, while specs\02-input.md reads the stick raw and quantises only the
keyboard, and specs\08-dodge-arena.md takes its vector from spec 02. Section 8 of that file says the spec wins and the
file is corrected, so it now says 2 pixels per step with the keyboard quantised and the stick read raw.

