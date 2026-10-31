# PALETTE PASS LIST, run 13, 2026-10-30

Owner of this page: the testing lane. Thirteenth run of the AUTO-PINE-CHECKS card series, this run on card
`t_8c00ed82`, measured on 30 October between 18:24 and 18:34 Pacific on HEAD `a47498dd` (VC-2 `t_1d9bc0a9`,
committed 18:20:37). It answers one question for the rebrand week and the store submission: for every frame and every
sprite in the project, does it pass `knowledge/ART-BIBLE.md` RULE 0 (palette first), and if it fails, which rule fails
and whose card fixes it. RULE 0 was re-read this run at `knowledge/ART-BIBLE.md` line 283, sha256
`02767323d888b91c...`, and the palette tool is unchanged at `bdcb0b6e5066004e...` (`tools/palette_synergy.py`), so the
palette half is like for like with run 12. The audit is NOT: `tools/nes_audit_all.py` now hashes `8e384e067150f5d8...`
and run 12 measured `20fabd83d9760657...`; two commits landed it on 26 October, `cba6ec0f` (AUDIT-TRUTH, card
`t_b8e56b9d`) and `9fd284cf` (GATED-REDS-UNOWNED, card `t_30746cd8`), so every NES trend below is read against a
different tool as well as a different tree, and section 4 says so on each line.

The headline: both gates are clean for the first time in this series. Local audit `PASS  193 file(s), 24 failing
(sheet 20, capture 4), 0 unmeasured`, exit 0, with the two gated classes at `frame 22 pass 0 fail` and `asset 142 pass
0 fail`. Pine audit `PASS  157 file(s), 5 failing (sheet 5), 0 unmeasured`, `AUDIT_EXIT=0`. Palette gate `10
entry(ies), 0 gated failure(s), 3 advisory failure(s), 0 not measured`, unchanged problem for problem from run 12 at
386. All eleven gated reds run 12 raised are closed: `ts_ship.png` by `t_4d5984b4`, the two repairable ones
(`drive_gantry_preview.png`, `spr_pp_dither.png`) and nine unregenerable mocks by `9fd284cf`/`t_30746cd8`, which
deleted them with their measurements recorded at `knowledge/GATED-REDS-2026-10-26.md`. The 24 reds that remain are
exactly the 24 advisory rows run 12 already had, every one a contact sheet or a window capture. And the RULE 0 check
that sits outside both tools now passes on screen data: `tools/check_runtime_palette.py` reads `runtime palette: 54
colour(s) in data/palette.json, 54 mapped in data/palette_ppu.json, 54 resolved to a 2C02 output, 0 not`, exit 0, where
`9fd284cf` recorded 0 of 54 on 26 October.

## 1. What ran, and the jobs

```
python pine_offload.py --shards 1 --name autochecks-v13a2 --cmd '( cd ~/repo/projects/primordial-paradox; python tools/art/make_characters_v2.py > ~/make_sheet13.txt 2>&1; echo SHEET_EXIT=$?; python tools/palette_synergy.py --gate --out output/ps_auto13.json; echo TOOL_EXIT=$? )'
python pine_offload.py --shards 1 --name autochecks-v13b --cmd '( cd ~/repo/projects/primordial-paradox; python tools/nes_audit_all.py --no-write; echo AUDIT_EXIT=$? )'
```

| Job | Pine computer | Started | Finished | Wall | Upload attempts | Exit | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| palette sweep, 10 entries | `po-autochecks-v13a2-0` | 2026-10-30 18:27:36 | 18:29:15 | 68.4 s, 13 turns | 1 | `SHEET_EXIT=0`, `TOOL_EXIT=0` | `arananet/pine/data/results/offload-autochecks-v13a2-0.json`, `results_txt`: `palette_synergy: 10 entry(ies), 0 gated failure(s), 3 advisory failure(s), 0 not measured; report output/ps_auto13.json` |
| every art file, audit | `po-autochecks-v13b-0` | 18:31:18 | 18:33:50 | 116.4 s, 22 turns | 1 | `AUDIT_EXIT=0` | `offload-autochecks-v13b-0.json`, `results_txt`: `nes_audit_all: PASS  157 file(s), 5 failing (sheet 5), 0 unmeasured`, `class frame 9 file(s), 9 pass, 0 fail`, `class asset 142 file(s), 142 pass, 0 fail` |
| same audit, local, the tree this page's per file rows come from | this PC | 18:26 | 18:29 | 1 s of tool time | not uploaded | exit 0 | `scratch\audit13_local.txt`, `nes_audit_all: PASS  193 file(s), 24 failing (sheet 20, capture 4), 0 unmeasured`, `scope: 193 file(s) measured (142 asset, 51 output); 245 PNG(s) in output/ on disk, 194 of them skipped by name` |
| the runtime palette rule, the half no audit row carries | this PC | 18:38 | 18:38 | 1 s | not uploaded | `RUNTIME_EXIT=0` | `runtime palette: 54 colour(s) in data/palette.json, 54 mapped in data/palette_ppu.json, 54 resolved to a 2C02 output, 0 not`, `runtime palette: 30 distinct 2C02 entry(s) for the 54 design colours` |

One job was thrown away and its result is not cited: `autochecks-v13a-0` (18:24:33, 437 bytes) died in the harness with
`PineConfigError: the pinesandbox SDK is not importable in this process (ModuleNotFoundError)`, no tool lines in
`results_txt`, nothing about the art. The cause is on this PC and not on Pine: the `python` on the shell PATH is the
Hermes venv at `hermes-agent/venv/Scripts/python`, which has no `pinesandbox`; `<home>\AppData\Local\Microsoft\
WindowsApps\python` (3.14.7) does, and the two jobs above ran on it. The card's literal `--all` switch does not exist on
the palette tool either, `--help` this run lists `--gate`, the same trap run 12 named.

## 2. The ten palette entries (palette synergy, this run)

All ten entries in `data/scene_palettes.json` are ADVISORY today: `grep -n '"gate": true'` returns nothing, so this half
gates nothing and the tool's own line reads `10 entry(ies), 0 gated failure(s), 3 advisory failure(s), 0 not measured`.
The file hashes `d54e77413115b5d5...` and carries 12 `scene` palette sets with 10 of them under `audit`, the ten measured
here, 34 sprite rows in total.

| Entry | Scene | Ground | Gated | Problems, Pine | Rules, Pine | What the row is |
| --- | --- | --- | --- | --- | --- | --- |
| E0 | battle_corridor | `output/bg_battle_corridor_frame.png` | no (advisory) | 0 | - | the party's four battle sheets, one reserved hero triple each |
| E1 | battle_corridor | `output/bg_battle_corridor_frame.png` | no (advisory) | 6 | set_member 6 | the sprites_v2 contact sheet, rebuilt on the far side by `tools/art/make_characters_v2.py`, `by_product` true |
| E2 | battle_deck_night | `output/bg_battle_deck_night_frame.png` | no (advisory) | 0 | - | the same four battle sheets on the deck strip |
| E3 | ship | `game/sprites_src/env/ts_ship.png` | no (advisory) | 0 | - | the ship's four walking sheets plus sailor_ow_v2 on the tileset (`t_a6a7f436`, `t_1dc346b9`); 0 again after `t_4d5984b4` fixed the 3 pixels |
| E4 | ship | `output/nes_title_frame.png` | no (advisory) | 245 | palette_count 213, set_member 16, white_blob 8, body_ground 8 | sailor_ow_v2 on the title ground: the diagnostic row for what a shared ground costs |
| E5 | southampton | `output/southampton_sample_frame.png` | no (advisory) | 0 | - | the four walking sheets at spawn tile 17,18 (`t_dec4e92c`, closed by `t_454c1876`) |
| E6 | title | `output/nes_title_frame.png` | no (advisory) | 135 | palette_count 116, overlay_contrast 10, set_member 9 | the car, the wordmark and the cursor (`t_4f18c0ac`, `t_758934a8`) |
| E7 | westminster | `output/westminster_sample_frame.png` | no (advisory) | 0 | - | the four walking sheets at spawn tile 16,20 |
| E8 | westminster | `output/westminster_sample_frame.png` | no (advisory) | 0 | - | the park at map cell 14,24, `--at 96,176` (`t_b01c88ff`) |
| E9 | winchester | `output/winchester_sample_frame.png` | no (advisory) | 0 | - | the four walking sheets at spawn tile 16,19 |

34 sprite rows are measured across those ten entries: 30 pass, 4 fail. The four failing sprite rows, plus the two frame
rows counted separately:

| Entry | Sprite or frame | Problems, Pine | Problems, local | Rules | Owner |
| --- | --- | --- | --- | --- | --- |
| E1 | `output/sprites_v2_sheet.png` | 6 | 216 | Pine set_member 6; local set_member 13, sprite_tile 203 | by product, advisory by ruling (`t_c93a983f`); no owner |
| E4 | `game/sprites_src/chars/sailor_ow_v2.png` on `nes_title_frame.png` | 32 | 32 | set_member 16, white_blob 8, body_ground 8 | diagnostic row, no open card, the Q in section 6 |
| E4 | the frame itself | 213 | 213 | palette_count 213 | same row, the title ground is not designed on the ship's sets |
| E6 | `game/sprites_src/title/spr_pp_title_logo.png` | 16 | 16 | overlay_contrast 10, set_member 6 | `t_758934a8` TS2-ART-A (done); the repaint ruled on `t_4f18c0ac` was measured on the CAR |
| E6 | `game/sprites_src/title/spr_title_car.png` | 3 | 3 | set_member 3 | `t_4f18c0ac` (done), the car keeps its cast |
| E6 | the frame itself | 116 | 116 | palette_count 116 | title frame against its own three sheets |

The local column exists because the local audit run writes `output/palette_synergy.json` as its own step at 18:26, so the
per rule split costs no second palette pass. E1 reads 216 there against 6 on the far side because the sheet on this disk
is the older 1024x5696 by product while the far side rebuilds it, the same divergence run 12 and run 11 both measured and
the reason `t_c93a983f` marked the row `by_product`. Every other entry number is identical on both hands. `spr_pp_menu_cursor.png`
is the third title sprite and passes at 0.

## 3. Every file in the NES audit: 193 files, 169 pass, 24 fail

Scope: 142 game assets (83 sprite rows, 58 background rows and 1 mask, `spr_pp_dither.png`, the tint identity that
`9fd284cf` taught the audit to classify before the naming rules) and 51 output files (22 frames, 21 sheets, 8 captures). Assets and 256x240 `frame` rows gate; `sheet` and `capture` rows are advisory, exactly as
`tools/nes_audit_all.py` classes them since `cba6ec0f`. By class: `frame 22 pass, 0 fail`, `asset 142 pass, 0 fail`,
`sheet 1 pass, 20 fail`, `capture 4 pass, 4 fail`. The verdict is `PASS` and the exit code is 0, because the 24 reds are
all advisory, and the tool says so in one line rather than hiding it.

| Path | Kind | Size | Pixels | Rules measured | Owner card |
| --- | --- | --- | --- | --- | --- |
| `output/music_style_bible_preview.png` | sheet | 1980x5844 | 11,571,120 px | background_area x9694, grid x2, palette x61, screen_colours x1 | music lane; no open card |
| `output/render2_demo_preview.png` | sheet | 1920x2026 | 3,889,920 px | background_area x186, grid x1, palette x538, screen_colours x1 | demo render; no open card |
| `output/title_theme_v2_preview_3x.png` | sheet | 1920x2004 | 3,847,680 px | background_area x181, grid x1, palette x530, screen_colours x1 | `t_758934a8` (done) |
| `output/sfx_preview_3x.png` | sheet | 1560x2430 | 3,790,800 px | background_area x1766, grid x1, palette x547, screen_colours x1 | music lane; no open card |
| `output/title_ui_preview.png` | sheet | 1920x784 | 1,488,817 px | background_area x301, palette x7 | `t_758934a8` (done) |
| `output/icons_preview.png` | sheet | 884x804 | 576,091 px | background_area x613, grid x2, palette x418, screen_colours x1 | `t_0df13164` UI-NES (done) |
| `output/title_car_preview.png` | sheet | 400x744 | 297,312 px | background_area x28, palette x16 | `t_758934a8` (done) |
| `output/title_preview_3x.png` | sheet | 512x240 | 122,880 px | background_area x267, palette x32, screen_colours x1 | `t_758934a8` (done) |
| `output/percy_theme_preview_3x.png` | sheet | 512x128 | 65,536 px | background_area x137, palette x292, screen_colours x1 | music lane; no open card |
| `output/title_run_1_marks_overlay.png` | capture | 256x240 | 14,776 px | background_area x39, palette x11, screen_colours x1 | `t_758934a8` (done) |
| `output/winchester_sample_preview_2x.png` | sheet | 1024x960 | 7,140 px | background_area x241 | `t_dec4e92c` (done) |
| `output/southampton_sample_preview_2x.png` | sheet | 1024x960 | 4,456 px | background_area x150 | `t_dec4e92c` (done) |
| `output/bg_battle_preview.png` | sheet | 520x232 | 4,099 px | background_area x183 | `t_8ebcb489` (done) |
| `output/westminster_sample_preview_2x.png` | sheet | 1024x960 | 4,000 px | background_area x152 | `t_dec4e92c` (done) |
| `output/env_ship_preview.png` | sheet | 996x1092 | 2,258 px | background_area x131, grid x2 | `t_4f58c88d` (done) |
| `output/chars_preview_3x.png` | sheet | 552x2076 | 438 px | background_area x33, grid x1 | `t_b2acf67d` SPRITE-1 (done) |
| `output/ts_exterior_preview_3x.png` | sheet | 256x64 | 172 px | background_area x11 | `t_4f58c88d` (done) |
| `output/nes_palette_preview.png` | sheet | 768x824 | 144 px | background_area x8 | `t_c8156a77` (done) |
| `output/ts2_art_a_preview.png` | sheet | 224x168 | 60 px | background_area x7 | `t_758934a8` (done) |
| `output/title_run_1.png` | capture | 256x240 | 2 px | background_area x2, palette x2 | `t_758934a8` (done) |
| `output/title_run_2.png` | capture | 256x240 | 2 px | background_area x2, palette x2 | `t_758934a8` (done) |
| `output/title_run_reference_3x.png` | capture | 256x240 | 2 px | background_area x2, palette x2 | `t_758934a8` (done) |
| `output/enemies_preview.png` | sheet | 560x996 | 0 px | grid x1 | `t_97871d4b` (done) |
| `output/enemies_preview_3x.png` | sheet | 464x772 | 0 px | grid x1 | `t_97871d4b` (done) |

The pass side, by kind: 142 of 142 assets pass, every sprite, every background and every tileset in the tree, including
the 13 added since 26 October (`kronos_ow24.png`, `ouranos_ow24.png`, `percy_ow24.png`, `percy_man_1_ow24.png` to
`percy_man_3_ow24.png`, `zeus_ow_walk8.png`, `halls_tiles.png`, `quay_v2_tiles.png`, `quay_storm_tiles.png`,
`street_tiles.png`, `spr_pp_dither.png`, `spr_pp_knife.png`, read from `git log --diff-filter=A -- game/sprites_src`).
22 of 22 frames pass, the frames that ship. 5 of 29 sheets and captures pass. No row is unmeasured: the local run prints
`0 unmeasured` and `every output file this repository's data names is in this tree`.

The far side measured 157 files, `142 asset, 15 output`, and the same verdict: `frame 9 pass 0 fail`, `asset 142 pass 0
fail`, `sheet 1 pass 5 fail`, `0 unmeasured`, but also `129 output file(s) named by this repository's data are not in this
tree, so they were not measured`. That gap is the zip's universe, not the art: it ships 34 tracked `output/` files and
skips 4,546 by products. On that tree the E1 by product is absent too, so its synergy line reads `2 advisory` instead of
3, the exclusion `t_c93a983f` built so a missing by product cannot refuse a run.

## 4. Trend versus run 12 (measured 26 October 06:59 to 07:30 on card `t_585efccb`)

| Measure | Run 12 | Run 13 | Change, and what moved it |
| --- | --- | --- | --- |
| Palette entries | 10 | 10 | unchanged (`data/scene_palettes.json`) |
| Palette problems, Pine | 386 | 386 | 0, the same three advisory rows |
| Gated palette failures | 0 | 0 | unchanged, the gate is clean |
| Advisory palette failures | 3 | 3 | 0 (E1 6, E4 245, E6 135, every count identical) |
| Ship on the title ground (E4) | 245 | 245 | 0 |
| Title entry (E6) | 135 | 135 | 0 |
| Corridor contact sheet (E1) | 6 | 6 | 0 (far side, rebuilt the same way) |
| Audit universe, local | 183 files (129 asset, 54 output) | 193 files (142 asset, 51 output) | +13 assets, 9 mocks deleted, 6 output files new |
| Audit failing, local | 35 = 34 output + 1 asset, 11 gated | 24 = 24 output, 0 gated | -11, every gated red closed: `ts_ship.png` by `t_4d5984b4`; `drive_gantry_preview.png` and `spr_pp_dither.png` fixed and nine unregenerable mocks deleted by `9fd284cf` (`t_30746cd8`) |
| Frame class, local | 25 files, 10 fail (GATED) | 22 files, 22 pass (GATED) | the 10 gated frames are gone, 9 deleted and 1 repaired |
| Asset class, local | 129 files, 1 fail (GATED) | 142 files, 142 pass (GATED) | `ts_ship.png` `background_area x3` closed |
| Verdict and exit, local | `FAIL`, exit 1 | `PASS`, exit 0 | no gated red remains |
| Audit failing, Pine | 152 files, 14 failing | 157 files, 5 failing | -9 on a different tool and a different zip |
| Runtime role colours | 0 of 54 resolved to a 2C02 output, a P0 row in `data/sprite_redraw_queue.json` | 54 of 54 resolved, 30 distinct entries | closed since; measured this run by `tools/check_runtime_palette.py`, exit 0 |
| Art that ships red | 1 asset, 10 frames | 0 | the store submission's own question, answered |

Read the NES half with care: the audit tool changed between the two runs (`cba6ec0f`, `9fd284cf`), so the fall from 35
to 24 is the fix plus the deletion plus the tool's own two commits, and the honest split is the one `9fd284cf` recorded
in its own message, `PASS 175 files / 24 failing (sheet 20, capture 4)` on 26 October at 10:21, which is the same 24
advisory rows this run measures on a bigger universe.

## 5. Who fixes what

| What | Card | State | Owns |
| --- | --- | --- | --- |
| `game/sprites_src/env/ts_ship.png`, `background_area x3` | `t_4d5984b4` TS-SHIP-AREA | done, closed since run 12 | the 3 pixels, now 0 on both hands |
| the 11 gated audit reds run 12 carried | `t_30746cd8` GATED-REDS-UNOWNED, rulings at `knowledge/GATED-REDS-2026-10-26.md` | done | the 2 repairs and the 9 deletions, with the measurement of each |
| the 54 runtime role colours | decided by `tools/check_runtime_palette.py`, recorded under `t_30746cd8` | now PASS, 54 of 54 | the screen data every GML `draw_set_colour` call resolves through `data/palette.json` |
| the wordmark's `overlay_contrast 10` and cast `set_member 6`, the car's `set_member 3` | `t_758934a8` TS2-ART-A (done), ruled on `t_4f18c0ac` | done, no open card | the title layers; unchanged for two runs |
| the two `palette_count` frame rows (E4 213, E6 116) | none | advisory diagnostics | these say a ground is not designed on another scene's sets, which is what the rows exist to show |
| the 20 advisory sheets and 4 captures | the generator cards in section 3, none open | unchanged from run 12, same 24 paths | by products of the generators, not art that ships |
| sailor_ow_v2 on the title ground (E4, 245) | none | diagnostic, the Q in section 6 | the design question, not a pixel to repaint |

No card is raised by this run: nothing that ships is red, on either hand. The owner column in section 3 is inherited from
this page's run 12 table and every state above was re-read from `kanban.db` today at 18:40, not carried over.

## 6. Q: for gamedev

- `Q: E4 still measures 245, sailor_ow_v2 on output/nes_title_frame.png, and it is the largest single palette row in the project, but no screen in the game draws that pair and no card owns it. Either the game does put the sailor on the title ground at some point, in which case 245 problems sit on a shipped 256x240 screen and the row needs a card, or it never does and the entry should be retired from data/scene_palettes.json the way t_30746cd8 retired the nine mocks. Which one, and if it is a real screen, does the ground get designed on the ship's sets or the sailor get its own?`
- `Q: the 24 advisory reds are all contact sheets and window captures with no owner, and 20 of them are sheets that ship nowhere. Does the audit keep counting them every run, so the page shows 24 forever, or does each get an owner card the way the eleven gated reds did on t_30746cd8? tools/nes_audit_all.py already prints them apart from the gated classes since cba6ec0f, so either answer is a one line change on this page, but the choice is gamedev's.`

## 7. What this run did not do, and why

- No second full pass on either tool. Token rule 4 on the card: one clean run. The local audit did run twice, once at
  18:26 piped through `tail` which cost it its header, then once at 18:29 into `scratch\audit13_local.txt`; 1 s each,
  both `PASS 193 file(s), 24 failing`, and this page quotes the saved second one. The per rule palette split was not
  bought with a second palette pass: it comes from `output/palette_synergy.json`, written by the local audit's own
  synergy step.
- `tools/nes_composite_check.py` was not re-run. Nothing this run changed a frame that ships; the last measured state is
  run 11 section 6.
- The far side's `output/ps_auto13.json` stays on Pine; the local `offload-autochecks-v13a2-0.json` keeps its
  `results_txt`, which is what section 2 quotes, and the per rule split is read locally as section 2 says.
- No new art was drawn, no tolerance moved, no rule text changed: `knowledge/ART-BIBLE.md` still hashes
  `02767323d888b91c...` at RULE 0 line 283.

## 8. Check list for this card

| The card asks for | State |
| --- | --- |
| palette and NES checks on every frame and sprite, run through Pine | yes, section 1, two Pine job files named and one discarded job disclosed |
| the Pine result JSON | yes, `offload-autochecks-v13a2-0.json` (10 entries, 0 gated, 3 advisory) and `offload-autochecks-v13b-0.json` (157 files, 5 failing, all sheet) |
| every frame and sprite in the pass list, pass or fail | yes, section 2 for the 34 palette sprite rows plus the 2 frame rows, section 3 for all 193 audit files, 24 spelled out and 169 counted by class |
| the failing rule | yes, the rules column on every row |
| the owner card | yes, the owner column, and the card map in section 5, all states re-read today |
| the trend versus the last run | yes, section 4, run 12 read from this page's previous revision, with the tool change named on each NES line |
| the note attached to the card, not left in scratch | yes, `kanban_attach` on `t_8c00ed82` |
