# PRIVACY-SWEEP-2026-11-02: the public repo's whole history, not only the new commits

Card t_0428107f. Sweep run 2026-11-02. Verdict: the final tree the judges read is clean, and the first
27 commits of the public history are not.

## What was scanned

- A fresh, full clone of the public repository into a new folder under `D:\Temp`, read only, nothing
  pushed. HEAD `cd937d60a87476d838a5374aed5c9b300b3446eb`, 178 commits from
  2026-10-25T22:21:08-07:00 to 2026-11-02T14:57:11-08:00, 2314 files in the tree, 2966 distinct blobs
  reachable from HEAD.
- `tools/sweep_public_history.py` (this card) imports the publisher's own code instead of copying it:
  `publish_pp.push_gate`, `publish_pp.private_findings`, `publish_pp.read_names`,
  `publish_pp.name_matcher` and `guard\leak_scan.py`. A rule widened in the publisher cannot be
  narrower here.
- Three passes. (1) `push_gate` over the full rev-list, the publisher's own path with the whole history
  as its input instead of a push range. (2) The final tree, every path at HEAD. (3) A blob census: every
  distinct blob reachable from HEAD, read once and put through both rule sets, which is the
  completeness proof for the first two.
- The names list is read through `publish_pp.read_names` and never printed. It held 240 entries.

## Numbers from the run

| measure | value |
|---|---|
| commits scanned | 178 |
| files in the final tree | 2314 |
| distinct blobs reachable from HEAD | 2966 |
| blobs read by at least one rule | 2552 |
| blobs the rules skip (extension or size) | 414, over 342 distinct paths |
| findings, per-commit pass | 466 |
| findings, final tree | 9 |
| findings, blob census | 462 |
| distinct findings (path, line, rule) | 464 |
| distinct findings still present at HEAD | 9 |
| credential shapes found (history and tree) | 0 |

Which pattern fired, counted by the census:

| pattern | lines |
|---|---|
| user path, private workspace folder name | 432 |
| user path, home directory spelling | 21 |
| dating | 7 |
| health | 1 |
| personal name | 1 |

No tailnet address, no Private folder path, no uncredited email and no credential shape fired
anywhere in the history or the tree.

## The history exposure

- 27 of the 178 commits carry a file with an absolute host path in their tree. The first is
  `831bcc65`, the baseline commit (2026-10-25T22:21:08-07:00). The last is `b597c67e`
  (2026-10-26T10:07:23-07:00, "manager: README names the baseline by its tag").
- Commit `d9310040` (2026-10-26T10:44:14-07:00, "Publish rules update: local machine paths and internal
  names replaced with placeholders") scrubbed all of them, and the 151 commits after it carry none.
  That is why the tree is clean and the history is not: the scrub is a commit, so it fixed every later
  snapshot and left the earlier ones exactly as they were pushed.
- 138 distinct blobs carry one of the markers, out of 2966. 131 of them carry the private workspace
  folder name; 17 carry a home-directory spelling with the Windows account name (5 with backslashes,
  12 with forward slashes).
- What a reader of those 27 commits learns: the name of the private workspace folder, and in 21 lines
  the Windows account name. That is the whole exposure. It is enough to identify the machine and the
  private folder layout, and it is not a credential, not an address, not a client or personal record.
- Verified against the commit itself, not only against the census: the baseline copy of the audio
  review notes carries the path on line 4, and `git log --reverse --format=%H -- <path>` names
  `831bcc65` as the commit that introduced it. The mask in that check hid only the folder name.

## The final tree

- Byte-level check, independent of the text scanners and their extension and size rules: all 2314 blobs
  at HEAD were read as bytes and none carries the workspace folder name, either home-directory spelling,
  or the POSIX home shape. The tree is clean.
- The 9 rule hits that remain at HEAD are word collisions, not disclosures:
  - 7 are one English word, the name of the pivot note of a diminished chord, in
    `data/recipes/konami.json`, `knowledge/music-styles/konami.md` and
    `assets/audio/title_theme_v3/motif_candidates.yaml`. It is also the name of a product in the rule's
    app-brand list, which is why the rule matches it; the pages are about chord voicings and nothing
    there is personal.
  - 1 is a seven-letter word for a therapeutic treatment, used inside the triangle-channel comment at
    `tools/render_chip.py:384`, where the health rule reads it as a personal health term.
  - 1 is a surname on the names list that also belongs to a credited third-party author in the source
    row `knowledge/SOURCES.md:27`, which carries the article URL. A citation, not a disclosure.
- No decision is needed on those 9. They should stay as they are: changing a correct citation to dodge a
  word rule would make the page worse.

## What this sweep does not cover

- Blobs not reachable from HEAD. A clone carries none, and a GitHub-side pull-request ref or a fork is
  outside this measurement.
- The rules skip by extension, and that is a publisher gap worth its own card: `.gml` (46 files at HEAD),
  `.vbs`, `.jsonl`, `.tla`, `.tex` and `.svg` are never read by the credential shapes, and `.gml` is
  read by the private patterns but not by the credential ones. I read the 17 skipped text-ish blobs and
  the 6 SVG and 1 TTF at HEAD with both rule sets anyway: 0 hits, and no marker bytes in any of them.
- 3 recorded-model-answer JSON blobs of 2.2, 2.4 and 3.6 MB exceed the publisher's 2 MB cap. Read
  separately with no cap: 0 hits.
- Binary media (260 PNG, 90 OGG, 33 WAV, 6 MID and more) is not text, so the rules never open it. All of
  it was read as bytes for the four markers and none carries one. A marker list is not a scanner, so
  this is a measured absence of these markers, not proof of clean metadata.
- Nothing here says the history was ever read by anyone. It says it is readable.

## Decision this card does not take

The tree is clean, so the repository as it stands passes. The history cannot be cleaned without a force
push that rewrites 27 commits, changes every later commit id, moves the baseline tag, and leaves the old
objects reachable by SHA until GitHub garbage-collects them. Judges' links and any copy of the old ids
would break, so this is Nayil's call, and the public export is written only by the publisher. Nothing in
the public repository was touched by this card.

Two follow-ups worth naming, neither of them this card's work:

1. Publisher rule: add `.gml`, `.vbs`, `.jsonl`, `.tla`, `.tex`, `.svg` to the credential shapes, or
   state the extension gap in the publisher's own docstring so the next sweep does not rediscover it.
2. Publisher gate scope: it scans the commits a push sends, which is right for a push and cannot see a
   history that was pushed before a rule changed. A nightly run of this sweep, or this script on the
   pre-push path with `--skip-history` off, would close that.

## Every finding

Path, line and rule. Never the matched text.
### rule: user path, 455 line(s) over 139 path(s), 0 still at HEAD

| path | lines | at HEAD |
|---|---|---|
| `assets/audio/ear_reviews/hadrian_theme_20261022T142955Z.md` | 4 | no |
| `assets/audio/ear_reviews/percy_theme_20261022T142852Z.md` | 4 | no |
| `assets/audio/ear_reviews/pp_03_harbor_v3_20261024T071744Z.md` | 4 | no |
| `assets/audio/ear_reviews/pp_03_harbor_v3_20261024T071837Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_20261022T142752Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_20261022T143036Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_v2_20261022T064029Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_v2_20261022T143107Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_v2_20261022T143223Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_v3_126_20261022T063958Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_v3_126_20261022T143319Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_v3_126_20261022T143350Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_v3_20261022T142819Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_v3_20261022T143250Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_v4_medium_20261022T064058Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_v4_medium_20261022T065123Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_v4_medium_20261022T143429Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_v4_medium_20261022T143504Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_v4_spicy_20261022T064125Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_v4_spicy_20261022T065155Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_v4_subtle_20261022T063813Z.md` | 4 | no |
| `assets/audio/ear_reviews/title_theme_v4_subtle_20261022T065048Z.md` | 4 | no |
| `assets/audio/hadrian_theme/NOTES.md` | 40 | no |
| `assets/audio/hadrian_theme/arrange_report.json` | 75, 108 | no |
| `assets/audio/hadrian_theme/hadrian_theme_loop.json` | 2, 52, 53 | no |
| `assets/audio/hadrian_theme/melody_guard.json` | 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 68 | no |
| `assets/audio/hadrian_theme/score_check.json` | 270 | no |
| `assets/audio/percy_theme/arrange_report.json` | 188, 225 | no |
| `assets/audio/percy_theme/percy_theme_loop.json` | 2, 54, 55, 58, 334, 337, 359 | no |
| `assets/audio/pp_01_title/NOTES.md` | 127 | no |
| `assets/audio/pp_01_title/hook_v4_medium.json` | 115, 145 | no |
| `assets/audio/pp_01_title/hook_v5.json` | 115, 145 | no |
| `assets/audio/pp_01_title/measure_candidates.json` | 32, 33, 316, 317 | no |
| `assets/audio/pp_01_title/pp_01_title_alt_v4_medium_loop.json` | 2, 53 | no |
| `assets/audio/pp_03_harbor/NOTES.md` | 62 | no |
| `assets/audio/pp_03_harbor/arrange_report.json` | 5, 123, 135 | no |
| `assets/audio/pp_03_harbor/melody_guard.json` | 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 68 | no |
| `assets/audio/pp_03_harbor/pp_03_harbor_loop.json` | 2, 54, 55 | no |
| `assets/audio/pp_03_harbor/score_check.json` | 116 | no |
| `assets/audio/pp_03_harbor_v2/arrange_report_v2.json` | 5, 123, 135 | no |
| `assets/audio/pp_03_harbor_v2/hook_report_v2.json` | 115, 150 | no |
| `assets/audio/pp_03_harbor_v2/pp_03_harbor_v2_loop.json` | 2, 54, 55 | no |
| `assets/audio/pp_03_harbor_v3/arrange_report_v3.json` | 5, 67, 79 | no |
| `assets/audio/pp_03_harbor_v3/hook_report_v3.json` | 115, 151 | no |
| `assets/audio/pp_03_harbor_v3/pp_03_harbor_v3_loop.json` | 2, 54, 55 | no |
| `assets/audio/pp_04_navy_sailors/RENDER-NOTE.md` | 47 | no |
| `assets/audio/pp_04_navy_sailors/melody_guard.json` | 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 68 | no |
| `assets/audio/pp_04_navy_sailors/pp_04_hook.json` | 146 | no |
| `assets/audio/pp_04_navy_sailors/pp_04_navy_sailors_loop.json` | 2, 54, 55 | no |
| `assets/audio/pp_04_navy_sailors_v2/hook_render_v2.json` | 115, 151 | no |
| `assets/audio/pp_04_navy_sailors_v2/hook_report_v2.json` | 115, 151 | no |
| `assets/audio/pp_04_navy_sailors_v2/pp_04_navy_sailors_v2_loop.json` | 2, 53, 54 | no |
| `assets/audio/pp_04_navy_sailors_v3/hook_render_v3.json` | 115, 151 | no |
| `assets/audio/pp_04_navy_sailors_v3/hook_report_v3.json` | 115, 151 | no |
| `assets/audio/pp_04_navy_sailors_v3/pp_04_navy_sailors_v3_loop.json` | 2, 53, 54 | no |
| `assets/audio/pp_05_small_ship/NOTES.md` | 58 | no |
| `assets/audio/pp_05_small_ship/arrange_report.json` | 62, 95 | no |
| `assets/audio/pp_05_small_ship/hook_report.json` | 132 | no |
| `assets/audio/pp_05_small_ship/measure_pp_05.json` | 87 | no |
| `assets/audio/pp_05_small_ship/melody_guard.json` | 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 68 | no |
| `assets/audio/pp_05_small_ship/pp_05_small_ship_loop.json` | 2, 52, 53 | no |
| `assets/audio/pp_drive/arrange_report.json` | 200, 231 | no |
| `assets/audio/pp_drive/hook_report.json` | 139 | no |
| `assets/audio/pp_drive/pp_drive_loop.json` | 2, 53, 54 | no |
| `assets/audio/pp_drive_v2/arrange_report_v2.json` | 164, 195 | no |
| `assets/audio/pp_drive_v2/hook_report_v2.json` | 115, 162 | no |
| `assets/audio/pp_drive_v2/pp_drive_v2_humanized_loop.json` | 2, 53 | no |
| `assets/audio/pp_drive_v2/pp_drive_v2_loop.json` | 2, 53, 54 | no |
| `assets/audio/pp_fight/hook_report_calm.json` | 115, 140 | no |
| `assets/audio/pp_fight/hook_report_fight.json` | 115, 143 | no |
| `assets/audio/pp_fight/pp_fight_calm_loop.json` | 2, 48, 49 | no |
| `assets/audio/pp_fight/pp_fight_fight_loop.json` | 2, 54, 55 | no |
| `assets/audio/pp_fight/pp_fight_states_loop.json` | 2, 53, 54 | no |
| `assets/audio/title_theme/title_theme_loop.json` | 2, 37, 38 | no |
| `assets/audio/title_theme_v2/arrange_report.json` | 18, 49 | no |
| `assets/audio/title_theme_v2/title_theme_v2_arranged_loop.json` | 2, 54, 55 | no |
| `assets/audio/title_theme_v2/title_theme_v2_loop.json` | 2, 54, 55, 184 | no |
| `assets/audio/title_theme_v3/STUDY.md` | 382, 418 | no |
| `assets/audio/title_theme_v3/arrange_report.json` | 125, 156 | no |
| `assets/audio/title_theme_v3/arrange_report_126.json` | 125, 156 | no |
| `assets/audio/title_theme_v3/spice/report_d1.json` | 115, 836, 883, 884 | no |
| `assets/audio/title_theme_v3/spice/report_d1.txt` | 1, 2, 72 | no |
| `assets/audio/title_theme_v3/spice/report_d2.json` | 145, 953, 1000, 1001 | no |
| `assets/audio/title_theme_v3/spice/report_d2.txt` | 1, 2, 75 | no |
| `assets/audio/title_theme_v3/spice/report_d3.json` | 158, 1038, 1085, 1086 | no |
| `assets/audio/title_theme_v3/spice/report_d3.txt` | 1, 2, 79 | no |
| `assets/audio/title_theme_v3/spice/report_d3_humanize.json` | 158, 1038, 1097, 1098 | no |
| `assets/audio/title_theme_v3/spice/report_d3_humanize.txt` | 1, 2, 80 | no |
| `assets/audio/title_theme_v3/title_theme_v3_126_loop.json` | 2, 54, 55 | no |
| `assets/audio/title_theme_v3/title_theme_v3_loop.json` | 2, 54, 55, 562 | no |
| `assets/audio/title_theme_v4/arrange_report_v4.json` | 156, 187 | no |
| `assets/audio/title_theme_v4/hook_v4.json` | 134 | no |
| `assets/audio/title_theme_v4/humanize_medium.json` | 12, 13 | no |
| `assets/audio/title_theme_v4/humanize_spicy.json` | 12, 13 | no |
| `assets/audio/title_theme_v4/humanize_subtle.json` | 12, 13 | no |
| `assets/audio/title_theme_v4/spice_medium.json` | 263, 264, 266 | no |
| `assets/audio/title_theme_v4/spice_spicy.json` | 301, 302, 304 | no |
| `assets/audio/title_theme_v4/spice_subtle.json` | 210, 211, 213 | no |
| `assets/audio/title_theme_v4/title_theme_v4_medium_loop.json` | 2, 53, 54, 561 | no |
| `assets/audio/title_theme_v4/title_theme_v4_spicy_loop.json` | 2, 53, 54, 561 | no |
| `assets/audio/title_theme_v4/title_theme_v4_subtle_loop.json` | 2, 53, 54, 561 | no |
| `assets/audio/title_theme_v5/arrange_report_v5.json` | 696, 697, 707 | no |
| `assets/audio/title_theme_v5/humanize_v5.json` | 13, 14 | no |
| `assets/audio/title_theme_v5/title_theme_v5_loop.json` | 2, 53, 54, 561 | no |
| `assets/tiles/ship/ship_tiles.json` | 989 | no |
| `data/ear_ledger.csv` | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46 | no |
| `data/eye_ledger.csv` | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15 | no |
| `data/music_recipes.json` | 141 | no |
| `data/recipes/jrpg.json` | 92 | no |
| `data/sprite_redraw_queue.json` | 5502, 5521, 5540 | no |
| `knowledge/BATTLE-DIM-OFF-PALETTE-2026-10-26.md` | 7 | no |
| `knowledge/BUILD-TIMELINE.md` | 18 | no |
| `knowledge/CHAR-PIPE-REVIEW.md` | 33, 127, 133, 142 | no |
| `knowledge/HACKATHON-AUDIT-2026-10-22.md` | 7 | no |
| `knowledge/LAUNCH-2026-10-24.md` | 42 | no |
| `knowledge/MUSIC-STYLE-BIBLE.md` | 338 | no |
| `knowledge/NAMES-BIBLE.md` | 280 | no |
| `knowledge/NES-AUDIT.json` | 18, 40, 62, 84, 106, 128, 150, 172, 194, 216, 238, 260, 282, 304, 326, 708, 730, 752, 814, 836, 858, 931, 1482, 1592, 1614, 1636, 1758, 2090, 2112, 2134, 2404, 2478, 2500, 2522, 2544, 2566, 2588, 2610, 2632, 2654, 2676, 2698, 2964, 2986, 3662, 3684, 3706, 3728, 5724, 5734, 7341, 56291, 56301, 56334, 56355, 64466, 64487, 69141, 69162, 72115, 72136, 72146, 73998, 74247, 74257, 74385, 74395, 75415, 75802, 75812, 77621, 77631, 77662, 77672, 77703, 77713, 77745, 77755, 79469 | no |
| `knowledge/PALETTE-PASS-LIST.md` | 46 | no |
| `knowledge/PALETTE-RULINGS-2026-10-25.md` | 297, 1645 | no |
| `knowledge/REFINEMENT-BACKLOG-2026-10-26.md` | 103 | no |
| `knowledge/SPRITE-CRAFT.md` | 586 | no |
| `knowledge/char-pipe-review/review_char_pipe.py` | 15 | no |
| `knowledge/char-pipe-review/review_char_pipe2.py` | 12, 13 | no |
| `knowledge/char-pipe-review/review_char_pipe3.py` | 11, 12 | no |
| `knowledge/char-pipe-review/review_char_pipe4.py` | 14, 15 | no |
| `knowledge/char-pipe-review/review_char_pipe5_reconfirm.py` | 18, 19 | no |
| `knowledge/char-pipe-review/review_char_pipe6_f1_fresh.py` | 17, 18 | no |
| `knowledge/char-pipe-review/review_char_pipe7_f234_fresh.py` | 13, 14 | no |
| `knowledge/mechanics/ACTION-MECHANICS.md` | 28, 29 | no |
| `knowledge/music-styles/capcom.md` | 547 | no |
| `knowledge/nodes/drive-scene-dependency.md` | 39 | no |
| `knowledge/nodes/save-layout.md` | 114, 173 | no |
| `output/ui_battle_nes_report.json` | 83, 99, 102 | no |
| `output/ui_dialogue_nes_report.json` | 78, 94, 97 | no |
| `output/ui_menu_nes_report.json` | 67, 83, 86 | no |
| `tools/capture_title.py` | 914, 915 | no |
| `tools/run.ps1` | 6 | no |
| `tools/walk_ship_aboard.py` | 32 | no |

### rule: dating, 7 line(s) over 3 path(s), 7 still at HEAD

| path | lines | at HEAD |
|---|---|---|
| `assets/audio/title_theme_v3/motif_candidates.yaml` | 132, 134 | yes |
| `data/recipes/konami.json` | 177, 202, 397 | yes |
| `knowledge/music-styles/konami.md` | 237, 403 | yes |

### rule: health, 1 line(s) over 1 path(s), 1 still at HEAD

| path | lines | at HEAD |
|---|---|---|
| `tools/render_chip.py` | 384 | yes |

### rule: personal name, 1 line(s) over 1 path(s), 1 still at HEAD

| path | lines | at HEAD |
|---|---|---|
| `knowledge/SOURCES.md` | 27 | yes |

## The check, as the card asked for it

The script's final summary line, pasted from the run:

```
SWEEP SUMMARY: commits 178 | tree files 2314 | blobs reachable 2966 (read 2552, unread by rule 414) | findings history 466, tree 9, census 462, distinct 464 | by rule user path=455 dating=7 health=1 personal name=1 | VERDICT FINDINGS
```

Reproduce with:

```
python tools/sweep_public_history.py --clone <fresh clone of the public repo> --json <out.json>
```

Exit 0 means clean, 1 means any finding, 2 means a rule that could not run (never a pass).

## How this page was checked

- Every count above is read from the sweep's JSON, not from memory.
- This page was itself put through both rule sets before committing: 0 findings, so the page that
  reports the leak does not repeat it.
- No long dashes are used anywhere in this page.
