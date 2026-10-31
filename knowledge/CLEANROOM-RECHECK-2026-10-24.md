# Clean-room re-check: everything that landed since 2026-10-22 00:00

Card t_02f2dd46, security-organization-audit, by Nayil's security lane. Run 2026-10-23 00:58 to 01:25 PDT.
The card names this file `CLEANROOM-RECHECK-2026-10-24.md`; the run is in the first hour of 2026-10-23, which is the
same night `ROADMAP-2026-10-24.md` files as W4. The file name is the roadmap's date, the measurements are timestamped
with the hour they were taken.

VERDICT: the clean room holds on every shipped path; two paths are flagged, and neither is an expression problem. One
shipped GML module has no clean-room verdict, and one third party data file has no licence record. The gate's own exit
code says both are fine, which is the finding that matters.

## 1. What was measured, and the tree that moved during the run

Three sources, all read only:

1. `git log --since="2026-10-22 00:00" --diff-filter=A --name-only -- .` gives **656 paths added by 56 commits**.
2. `git status --porcelain -uall -- .` gives **103 staged or untracked paths** in the working tree at 01:05, which are
   work that landed today in the sense the card means even though no commit carries them yet.
3. De-duplicated, that is **758 distinct paths**: game/ 233, assets/ 244, tools/ 82, data/ 72, knowledge/ 58,
   tests/ 48, output/ 6, specs/ 6, repository root 9. Every one is verdicted in the appendix.

The tree changed while I measured it, and both readings are reported rather than the convenient one:

- at **00:58** `python tools/check_cleanroom.py` **failed, exit 1**, on four modules with no review row
  (`obj_pp_drive/Create_0.gml`, `Draw_0.gml`, `Step_0.gml`, `pp_drive.gml`) plus one pending row;
- at about **01:05** `knowledge/CLEANROOM-REVIEW.md` gained four rows for exactly those modules, reviewer `builder`,
  date 2026-10-23, while this card was running (uncommitted, `git diff` shows 4 added lines);
- at **01:10** the same check **passed, exit 0**, with one module still pending.

I edited no file in this repository except the one this card owns. The review rows are builder's, not mine.

## 2. Verdicts, by count

| Verdict | Paths | What the label means here |
| --- | --- | --- |
| own work | 641 | no banned name or phrase survived the scan, no third party licence claim, nothing to trace |
| public domain myth | 111 | our own text whose only external proper names are public domain myth names (Percy, Prometheus, Kronos, Poseidon, Hades, Zeus). It means nothing in the file needs a licence, not that anything was copied from a myth text |
| ODbL data | 4 | OpenStreetMap derived, proven from inside the file, not from its path |
| flagged | 2 | see section 6 |

The four ODbL paths, each proven from its own bytes:

- `data/osm_cache/southampton_town_quay.json` (241,556 bytes), generator `Overpass API` and the osm3s copyright naming
  openstreetmap.org.
- `data/osm_cache/winchester_high_street.json` (192,300 bytes), same proof.
- `data/osm_cache/westminster_big_ben.json` (475,236 bytes), same proof.
- `data/maps/real_places.json` (37,127 bytes), `kind: real_places`, `licence` naming ODbL, `attribution` naming
  openstreetmap.org, and a source marker naming the cache.

The gate skips the six cache files (three here and the three mirrors under `game/datafiles/osm_cache/`) on that same
proof, and exempts 242 OSM place names inside the two generated `real_places.json` cards. Both exemptions are reported
by the gate on every run, by path and by count, so they cannot widen quietly.

## 3. The gate, pasted verbatim, both runs

Run at 00:58 (exit 1):

```
check_cleanroom: 355 files scanned for 26 names and 12 phrases, 40 GML modules, 1 awaiting review, 6 downloaded map file(s) skipped, 242 OSM place name(s) exempt in 2 generated geography card(s)
OSM place names exempt from the foreign name pass: game/datafiles/maps/real_places.json (121 name(s))
OSM place names exempt from the foreign name pass: data/maps/real_places.json (121 name(s))
PENDING clean-room review: game/scripts/pp_map_tile/pp_map_tile.gml
FAIL game/objects/obj_pp_drive/Create_0.gml: no clean-room review row in knowledge/CLEANROOM-REVIEW.md
FAIL game/objects/obj_pp_drive/Draw_0.gml: no clean-room review row in knowledge/CLEANROOM-REVIEW.md
FAIL game/objects/obj_pp_drive/Step_0.gml: no clean-room review row in knowledge/CLEANROOM-REVIEW.md
FAIL game/scripts/pp_drive/pp_drive.gml: no clean-room review row in knowledge/CLEANROOM-REVIEW.md

4 clean room problem(s)
```

Run at 01:10 (exit 0):

```
check_cleanroom: 355 files scanned for 26 names and 12 phrases, 40 GML modules, 1 awaiting review, 6 downloaded map file(s) skipped, 242 OSM place name(s) exempt in 2 generated geography card(s)
OSM place names exempt from the foreign name pass: game/datafiles/maps/real_places.json (121 name(s))
OSM place names exempt from the foreign name pass: data/maps/real_places.json (121 name(s))
PENDING clean-room review: game/scripts/pp_map_tile/pp_map_tile.gml
check_cleanroom: no blacklist hit, but 1 of 40 modules still await clean-room review (listed above)
```

**The defect this exposes.** The check exits **0** while a module is pending, and `tools/run.ps1` blocks a build only
on a non-zero exit (`tools/run.ps1` line 61 lists the checkers, lines 65 to 70 fail the build on `$code -ne 0`). So a
build today would pass the clean-room gate while carrying `game/scripts/pp_map_tile/pp_map_tile.gml`, a module the
review file itself says is not a pass. That is not a leak; it is a gate that reports a debt in text and clears it in
its exit code, and the build reads the exit code.

## 4. The git grep, and what "returns nothing" can honestly mean

Inside the shipped tree, which is what the gate protects, the banned patterns return nothing:

```
$ git grep -n -i -w -E "undertale|deltarune|toby fox|deltamodkit|kris|susie|ralsei|noelle|berdly|lancer|queen|undyne|toriel|asgore|alphys|papyrus|sans|napstablook|asriel|chara|frisk|gaster|jevil|spamton|flowey|temmie" -- game data ':!data/osm_cache' ':!game/datafiles/osm_cache' ':!data/maps/real_places.json' ':!game/datafiles/maps/real_places.json'
$ echo $?
1
$ git grep -n -i -E "a beautiful day outside|sins crawling|bad time|but nobody came|stay determined|karmic retribution|gaster blaster" -- game data
$ echo $?
1
```

Zero hits, both lists, after the two documented exemptions. That is the measurement the card asks for.

Across the **whole repository** the same grep does not return nothing, and claiming otherwise would be a lie the next
auditor can disprove in one command: **15 tracked files** carry one of the names, and none is shipped.

| File | Why it is allowed |
| --- | --- |
| `tools/check_cleanroom.py` | it is the blacklist itself; the words are the gate's data |
| `tests/test_cleanroom.py` | negative fixtures; the test asserts the scanner refuses the word |
| `tools/check_music_style_bible.py` | asserts the style bible does not copy a tune, so it names what it refuses |
| `knowledge/LICENSES.md`, `knowledge/PROVENANCE.md`, `knowledge/README.md` | the rule and its rejected list, which has to name the rejected thing |
| `knowledge/MUSIC-STYLE-BIBLE.md`, `knowledge/music-styles/fox.md`, `knowledge/music-styles/nintendo.md` | composition analysis citing published interviews, reviews and theory tabs. Technique study is allowed by `PLAN.md` line 6 and `PLAN-V2-2026-10-21.md` line 6; no tune, sprite, string or code is reproduced |
| `knowledge/mechanics/*`, `knowledge/genre-design.md` | genre mechanics, which are ideas and not protected |
| `specs/16-talk-command.md` | cites "Toby Fox's ACT idea" as an idea, in the spec that replaces it with a model judged free text |
| `PLAN.md`, `PLAN-V2-2026-10-21.md`, `DEVLOG.md` | the order of 2026-10-19, the reference rule and the incident record |

Of the 758 new paths, **10 name a banned word anywhere in their text and 0 of those are shipped** (`game/` or `data/`).

## 5. Quarantine, binaries, and the limits of a text scan

- `knowledge/study/` **exists on disk**. `git ls-files` reports **0 tracked files** under it, and the ignore rule is
  `.gitignore` line 2, `knowledge/study/`. I did not open, list or read that folder; presence and tracking status are
  the only two things measured about it.
- No file under `game/` or `data/` names a study copy, the quarantine or the decompilation repository: **0 hits** for
  `knowledge/study`, `quarantine`, `deltamodkit` in the shipped tree.
- **2,416 files walked** outside the study folder. Suspicious extensions: exactly two, `output/PrimordialParadox/
  PrimordialParadox.exe` and `PrimordialParadox.win`, which are our own build in `output/`, gitignored by
  `.gitignore` line 30, not tracked. No foreign game's data file, ROM, archive or decompiler output exists here.
- **Binary assets are UNKNOWN at byte level.** 244 of the new paths sit under `assets/`, which is art, audio and their
  notes. A PNG or an OGG cannot be compared to anything by text, and the one comparison that would prove provenance, a
  diff against the study copy, is
  the check the doctrine forbids. What each folder does carry is its own note and the generator that made it
  (`quay/TILES.md`, `pp_drive/NOTES.md`, `title_theme_v3/STUDY.md`, the `make_*.py` and `build_*.py` tools in the
  same commit), and `title_theme_v3/STUDY.md` states its sources and the rules it followed. That is provenance by
  record, not by bytes, and this file does not pretend otherwise.

## 6. The thirty cards' output paths

31 cards (`ROADMAP-2026-10-23.md`, R22 to R51 plus A2) declare **46 output paths** between them. **43 resolve** on
disk, whether as a file, a directory, or by suffix where the card used a short form. Three do not resolve literally:

| Card | Declared | State as measured | Reading |
| --- | --- | --- | --- |
| R42 REVIEW-DIALOGUE-V2 | `knowledge/REVIEW-DIALOGUE-2026-10-23.md` | **not on disk** | the card has not run yet; nothing landed, nothing to verdict |
| R46 QUAY-TILES | `assets/tiles/quay/` | **not on disk**; the tiles are at `game/sprites_src/env/quay/` (TILES.md, quay_tiles.json, quay_tiles.png, commit f74dc25) | the declared path is stale, the work landed somewhere else; catalog drift, not a clean-room problem |
| R26 SAVE-SLICE | `pp_overworld` | **not on disk as written**; the module is `game/scripts/pp_overworld/pp_overworld.gml`, reviewed 2026-10-22 | the card named the module, not a path |

One declared path is flagged: R49's `data/talk_profanity.json`, section 7.

## 7. The two flagged paths, with the commit and the fix

**1. `game/scripts/pp_map_tile/pp_map_tile.gml`, commit 49fd2ef (card t_7d1380f9, 2026-10-22 22:06).**
The review row says `pending | builder | 2026-10-22`. `pending` is not a pass by the review file's own words. Nothing
in the file scans dirty, so this is an unread file, not a suspect one.
Fix, for gamedev to rule: `code-review` reads the module and either raises the row to `confirmed` with a reviewer and a
date, or returns it with required changes. No deletion, no edit to the module from this lane.

**2. `data/talk_profanity.json`, commit b36c28c (card t_cd908367, 2026-10-22 21:15).**
The file records its own source as `dariusk/corpora` `data/words/expletives.json` under CC0 1.0, and
`knowledge/LICENSES.md` has no row for it; `knowledge/licences/` holds only `PressStart2P-OFL.txt`. The project's own
rule at the top of that file is "nothing enters the project until its licence file has been read and recorded here",
and this file entered without that record. CC0 asks for no attribution, so the expression risk is nil; the rule break
is the record.
Fix, for gamedev to rule: add the row to `knowledge/LICENSES.md` (source URL, CC0 1.0, date read, what was reused) and
the licence text to `knowledge/licences/`, or rule that a CC0 dedication needs no copy and say so in the file. The
27 word list itself is data, not expression, and `tools/talk_guard.py` is ours.

Two bookkeeping notes, neither flagged:

- The four drive rows added at 01:05 are `builder` reviewing `builder`. That is the same shape as `gamedev` reviewing
  gamedev elsewhere in the file, and it is within this repository's practice, but it is not a second pair of eyes and
  should not be counted as one when the gate is discussed.
- The gate exits 0 on `pending` (section 3). Proposed fix: exit non-zero when `PENDING > 0`, with an explicit
  `--allow-pending` for a lane that wants to see the list without failing. This is the only change proposed here that
  touches code, and it is gamedev's call, not mine.

## 8. What this run does not establish

- It does not compare any text to the study copy, which is the breach the rule exists to prevent.
- It does not prove that no sentence resembles a sentence somewhere else; the blacklist proves the listed names and
  phrases are absent, and the review rows prove a human read the module. Both are narrower than "original".
- It does not verify the bytes of any PNG, OGG or WAV asset.
- It does not verify art or audio against a published game by listening, looking or hashing; that evidence does not
  exist in this repository and cannot be manufactured here.
- It does not re-measure the four OSM exemption conditions for every run in the future; it measured them today, and
  the gate re-checks them on every run from inside each file.

## 9. Q: for gamedev

1. **Q1.** `pp_map_tile.gml` has said `pending` since 2026-10-22 22:06 and the build gate clears it. Do you want
   `code-review` to rule on it before the next build, or is the tile module allowed to ship unreviewed on the record?
2. **Q2.** Should `check_cleanroom.py` exit non-zero on `pending`? I recommend yes, with `--allow-pending`; it is a
   four line change and it makes the gate agree with the review file.
3. **Q3.** For R46, does the tile set stay at `game/sprites_src/env/quay/` (where it landed) or move to the
   `assets/tiles/quay/` the roadmap declared? If it stays, the roadmap line needs correcting so the next catalog pass
   does not report it missing.

## Appendix: every new path, verdicted

One row per path from section 1, sorted by path. Commit is the commit that added it, or `uncommitted` for work in the
working tree at 01:05. The evidence column is the reason the verdict was given, and a row that says "names the
reference in analysis, outside shipped paths" is naming a work, which is allowed, not copying it.

| Path, as it landed | Verdict | The evidence for that verdict | Commit |
| --- | --- | --- | --- |
| PLAN-V2-2026-10-21.md | own work | names the reference in analysis, outside shipped paths: deltarune, toby fox, undertale | 10e0b00 |
| README.md | public domain myth | own text; myth names only (kronos) | 25ed137 |
| ROADMAP-2026-10-22.md | public domain myth | own text; myth names only (percy, prometheus) | 5643daf |
| ROADMAP-2026-10-23.md | public domain myth | own text; myth names only (percy, prometheus) | 708d442 |
| ROADMAP-2026-10-24.md | public domain myth | own text; myth names only (percy, prometheus) | 02b7d52 |
| TITLE-COORD.md | own work | nothing external to trace | 10e0b00 |
| _r45_check.py | own work | nothing external to trace | 25ed137 |
| assets/audio/EAR_SWEEP_2026-10-22.md | public domain myth | own text; myth names only (percy) | 10e0b00 |
| assets/audio/ear_reviews/compare_title_theme_v3_126_title_theme_v2_20261022T064111Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/game_over_20261023T020642Z.md | own work | nothing external to trace | uncommitted |
| assets/audio/ear_reviews/hadrian_theme_20261022T142955Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/percy_theme_20261022T142852Z.md | public domain myth | own text; myth names only (percy) | 10e0b00 |
| assets/audio/ear_reviews/pp_03_harbor_20261023T015743Z.md | own work | nothing external to trace | uncommitted |
| assets/audio/ear_reviews/pp_03_harbor_20261023T020554Z.md | own work | nothing external to trace | uncommitted |
| assets/audio/ear_reviews/pp_03_harbor_v2_20261023T022756Z.md | own work | nothing external to trace | uncommitted |
| assets/audio/ear_reviews/pp_03_harbor_v2_20261023T023922Z.md | own work | nothing external to trace | uncommitted |
| assets/audio/ear_reviews/pp_04_navy_sailors_20261023T015613Z.md | own work | nothing external to trace | uncommitted |
| assets/audio/ear_reviews/pp_04_navy_sailors_20261023T020542Z.md | own work | nothing external to trace | uncommitted |
| assets/audio/ear_reviews/pp_05_small_ship_20261023T015636Z.md | own work | nothing external to trace | uncommitted |
| assets/audio/ear_reviews/pp_05_small_ship_20261023T020546Z.md | own work | nothing external to trace | uncommitted |
| assets/audio/ear_reviews/pp_05_small_ship_v2_20261023T053410Z.md | own work | nothing external to trace | uncommitted |
| assets/audio/ear_reviews/pp_05_small_ship_v2_20261023T053812Z.md | own work | nothing external to trace | uncommitted |
| assets/audio/ear_reviews/pp_drive_v2_humanized_20261023T020630Z.md | own work | nothing external to trace | uncommitted |
| assets/audio/ear_reviews/save_jingle_20261023T020426Z.md | own work | nothing external to trace | uncommitted |
| assets/audio/ear_reviews/title_theme_20261022T142752Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_20261022T143036Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v2_20261022T064029Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v2_20261022T143107Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v2_20261022T143223Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v3_126_20261022T063958Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v3_126_20261022T143319Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v3_126_20261022T143350Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v3_20261022T142819Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v3_20261022T143250Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v4_medium_20261022T064058Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v4_medium_20261022T065123Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v4_medium_20261022T143429Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v4_medium_20261022T143504Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v4_spicy_20261022T064125Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v4_spicy_20261022T065155Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v4_subtle_20261022T063813Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v4_subtle_20261022T065048Z.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/ear_reviews/title_theme_v5_20261022T231713Z.md | own work | nothing external to trace | uncommitted |
| assets/audio/ear_reviews/title_theme_v5_20261023T020536Z.md | own work | nothing external to trace | uncommitted |
| assets/audio/hadrian_theme/NOTES.md | public domain myth | own text; myth names only (percy) | 10e0b00 |
| assets/audio/hadrian_theme/arrange_report.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/hadrian_theme/hadrian_theme_loop.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/hadrian_theme/melody_guard.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/hadrian_theme/melody_lead.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/hadrian_theme/score_check.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/hadrian_theme/score_hadrian.yaml | public domain myth | own text; myth names only (percy) | 10e0b00 |
| assets/audio/percy_theme/arrange_report.json | public domain myth | own text; myth names only (percy) | 10e0b00 |
| assets/audio/percy_theme/percy_theme.ogg | own work | nothing external to trace | f22ca08 |
| assets/audio/percy_theme/percy_theme_loop.json | public domain myth | own text; myth names only (percy) | 10e0b00 |
| assets/audio/percy_theme/score_percy.yaml | public domain myth | own text; myth names only (percy) | 10e0b00 |
| assets/audio/pp_01_title/NOTES.md | own work | nothing external to trace | 59f1b52 |
| assets/audio/pp_01_title/hook_v4_medium.json | own work | nothing external to trace | 59f1b52 |
| assets/audio/pp_01_title/hook_v5.json | own work | nothing external to trace | 59f1b52 |
| assets/audio/pp_01_title/land_asset.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_01_title/measure_candidates.json | own work | nothing external to trace | 59f1b52 |
| assets/audio/pp_01_title/measure_candidates.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_01_title/pp_01_title.ogg | own work | nothing external to trace | 59f1b52 |
| assets/audio/pp_01_title/pp_01_title_alt_v4_medium.ogg | own work | nothing external to trace | 59f1b52 |
| assets/audio/pp_01_title/pp_01_title_alt_v4_medium_loop.json | public domain myth | own text; myth names only (kronos, percy) | 59f1b52 |
| assets/audio/pp_01_title/pp_01_title_loop.json | public domain myth | own text; myth names only (kronos, percy) | 59f1b52 |
| assets/audio/pp_03_harbor/NOTES.md | public domain myth | own text; myth names only (percy) | e585535 |
| assets/audio/pp_03_harbor/arrange_report.json | own work | nothing external to trace | e585535 |
| assets/audio/pp_03_harbor/build_pp03.py | own work | nothing external to trace | c05d907 |
| assets/audio/pp_03_harbor/check_pp03.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_03_harbor/melody_guard.json | own work | nothing external to trace | e585535 |
| assets/audio/pp_03_harbor/pp_03_harbor.ogg | own work | nothing external to trace | e585535 |
| assets/audio/pp_03_harbor/pp_03_harbor_loop.json | own work | nothing external to trace | e585535 |
| assets/audio/pp_03_harbor/score_check.json | own work | nothing external to trace | e585535 |
| assets/audio/pp_03_harbor/score_pp03.yaml | public domain myth | own text; myth names only (percy) | e585535 |
| assets/audio/pp_03_harbor_v2/NOTES.md | own work | nothing external to trace | d082b51 |
| assets/audio/pp_03_harbor_v2/arrange_report.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_03_harbor_v2/arrange_report_v2.json | own work | nothing external to trace | d082b51 |
| assets/audio/pp_03_harbor_v2/build_pp03_v2.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_03_harbor_v2/check_pp03.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_03_harbor_v2/hook_report_v2.json | own work | nothing external to trace | d082b51 |
| assets/audio/pp_03_harbor_v2/pp_03_harbor_v2.ogg | own work | nothing external to trace | d082b51 |
| assets/audio/pp_03_harbor_v2/pp_03_harbor_v2_loop.json | own work | nothing external to trace | d082b51 |
| assets/audio/pp_03_harbor_v2/score_pp03_v2.yaml | public domain myth | own text; myth names only (percy) | d082b51 |
| assets/audio/pp_04_navy_sailors/RENDER-NOTE.md | own work | nothing external to trace | e585535 |
| assets/audio/pp_04_navy_sailors/build_pp04.py | own work | nothing external to trace | c05d907 |
| assets/audio/pp_04_navy_sailors/melody_guard.json | own work | nothing external to trace | e585535 |
| assets/audio/pp_04_navy_sailors/melody_lead.json | own work | nothing external to trace | e585535 |
| assets/audio/pp_04_navy_sailors/pp04_check.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_04_navy_sailors/pp_04_check.json | own work | nothing external to trace | e585535 |
| assets/audio/pp_04_navy_sailors/pp_04_hook.json | own work | nothing external to trace | e585535 |
| assets/audio/pp_04_navy_sailors/pp_04_loop_points.json | own work | nothing external to trace | e585535 |
| assets/audio/pp_04_navy_sailors/pp_04_navy_sailors.ogg | own work | nothing external to trace | e585535 |
| assets/audio/pp_04_navy_sailors/pp_04_navy_sailors_loop.json | own work | nothing external to trace | e585535 |
| assets/audio/pp_04_navy_sailors/pp_04_score_report.json | own work | nothing external to trace | e585535 |
| assets/audio/pp_04_navy_sailors/score_pp04.yaml | own work | nothing external to trace | e585535 |
| assets/audio/pp_05_small_ship/NOTES.md | own work | nothing external to trace | e585535 |
| assets/audio/pp_05_small_ship/arrange_report.json | own work | nothing external to trace | e585535 |
| assets/audio/pp_05_small_ship/check_motif.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_05_small_ship/hook_report.json | own work | nothing external to trace | e585535 |
| assets/audio/pp_05_small_ship/measure_pp_05.json | own work | nothing external to trace | e585535 |
| assets/audio/pp_05_small_ship/measure_pp_05.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_05_small_ship/melody_guard.json | own work | nothing external to trace | e585535 |
| assets/audio/pp_05_small_ship/pp_05_small_ship.ogg | own work | nothing external to trace | e585535 |
| assets/audio/pp_05_small_ship/pp_05_small_ship_loop.json | own work | nothing external to trace | e585535 |
| assets/audio/pp_05_small_ship/score_pp_05.yaml | public domain myth | own text; myth names only (percy) | e585535 |
| assets/audio/pp_05_small_ship_v2/NOTES.md | own work | nothing external to trace | uncommitted |
| assets/audio/pp_05_small_ship_v2/build_pp05_v2.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_05_small_ship_v2/build_report_v2.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_05_small_ship_v2/check_v2.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_05_small_ship_v2/hook_report_v2.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_05_small_ship_v2/pp_05_small_ship_v2.ogg | own work | nothing external to trace | uncommitted |
| assets/audio/pp_05_small_ship_v2/pp_05_small_ship_v2_loop.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_arrival/NOTES.md | own work | nothing external to trace | uncommitted |
| assets/audio/pp_arrival/build_arrival.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_arrival/build_report.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_arrival/check_arrival.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_arrival/hook_report.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_arrival/pp_arrival.ogg | own work | nothing external to trace | uncommitted |
| assets/audio/pp_arrival/pp_arrival_loop.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_arrival/score_pp_arrival.yaml | own work | nothing external to trace | uncommitted |
| assets/audio/pp_drive/NOTES-v3.md | own work | nothing external to trace | uncommitted |
| assets/audio/pp_drive/NOTES.md | own work | nothing external to trace | 59f1b52 |
| assets/audio/pp_drive/arrange_report.json | own work | nothing external to trace | 59f1b52 |
| assets/audio/pp_drive/arrange_report_v3.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_drive/compute_map.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_drive/cue_cut_v3.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_drive/cue_map_v3.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_drive/cut_dump_v3.txt | own work | nothing external to trace | uncommitted |
| assets/audio/pp_drive/drive_cue_map.json | own work | nothing external to trace | 59f1b52 |
| assets/audio/pp_drive/hook_report.json | own work | nothing external to trace | 59f1b52 |
| assets/audio/pp_drive/hook_report_v3.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_drive/mix_check_v3.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_drive/mix_check_v3.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_drive/pp_drive.ogg | own work | nothing external to trace | 59f1b52 |
| assets/audio/pp_drive/pp_drive_loop.json | own work | nothing external to trace | 59f1b52 |
| assets/audio/pp_drive/pp_drive_v3.ogg | own work | nothing external to trace | uncommitted |
| assets/audio/pp_drive/pp_drive_v3_humanized.ogg | own work | nothing external to trace | uncommitted |
| assets/audio/pp_drive/pp_drive_v3_humanized_loop.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_drive/pp_drive_v3_loop.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_drive/score_pp_drive.yaml | own work | nothing external to trace | 59f1b52 |
| assets/audio/pp_drive/score_pp_drive_v3.yaml | own work | nothing external to trace | uncommitted |
| assets/audio/pp_drive_v2/NOTES.md | public domain myth | own text; myth names only (percy) | 79564da |
| assets/audio/pp_drive_v2/arrange_report_v2.json | own work | nothing external to trace | 79564da |
| assets/audio/pp_drive_v2/hook_report_v2.json | own work | nothing external to trace | 79564da |
| assets/audio/pp_drive_v2/pp_drive_v2.ogg | own work | nothing external to trace | 79564da |
| assets/audio/pp_drive_v2/pp_drive_v2_humanized_loop.json | own work | nothing external to trace | 79564da |
| assets/audio/pp_drive_v2/pp_drive_v2_loop.json | own work | nothing external to trace | 79564da |
| assets/audio/pp_drive_v2/score_pp_drive_v2.yaml | own work | nothing external to trace | 79564da |
| assets/audio/pp_fight/build_pp_fight.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_fight/build_report.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_fight/check_pp_fight.py | own work | nothing external to trace | uncommitted |
| assets/audio/pp_fight/hook_report_calm.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_fight/hook_report_fight.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_fight/pp_fight_calm.ogg | own work | nothing external to trace | uncommitted |
| assets/audio/pp_fight/pp_fight_calm_loop.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_fight/pp_fight_fight.ogg | own work | nothing external to trace | uncommitted |
| assets/audio/pp_fight/pp_fight_fight_loop.json | own work | nothing external to trace | uncommitted |
| assets/audio/pp_fight/pp_fight_states.ogg | own work | nothing external to trace | uncommitted |
| assets/audio/pp_fight/pp_fight_states_loop.json | own work | nothing external to trace | uncommitted |
| assets/audio/sfx/SFX.md | public domain myth | own text; myth names only (percy) | d81dfff |
| assets/audio/sfx/alarm.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/alarm.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/crit.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/crit.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/door_hatch.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/door_hatch.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/encounter_swoosh.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/encounter_swoosh.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/footstep.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/footstep.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/game_over.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/game_over.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/heal.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/heal.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/hit_heavy.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/hit_heavy.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/hit_light.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/hit_light.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/item_get.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/item_get.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/level_up.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/level_up.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/manifest.json | public domain myth | own text; myth names only (percy) | d81dfff |
| assets/audio/sfx/menu_cancel.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/menu_cancel.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/menu_move.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/menu_move.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/menu_select.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/menu_select.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/miss.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/miss.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/save_jingle.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/save_jingle.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/text_blip_a.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/text_blip_a.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/text_blip_b.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/text_blip_b.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/text_blip_c.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/text_blip_c.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/thunder_soft.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/thunder_soft.wav | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/wave_wash.ogg | own work | nothing external to trace | d81dfff |
| assets/audio/sfx/wave_wash.wav | own work | nothing external to trace | d81dfff |
| assets/audio/title_theme/title_theme.mid | own work | nothing external to trace | 176bab9 |
| assets/audio/title_theme/title_theme.wav | own work | nothing external to trace | 176bab9 |
| assets/audio/title_theme_v2/NOTES.md | public domain myth | own text; myth names only (kronos) | 10e0b00 |
| assets/audio/title_theme_v2/title_theme_v2.mid | own work | nothing external to trace | 176bab9 |
| assets/audio/title_theme_v2/title_theme_v2.ogg | own work | nothing external to trace | bd255e5 |
| assets/audio/title_theme_v2/title_theme_v2_arranged_loop.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/title_theme_v2/title_theme_v2_loop.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/title_theme_v3/EAR_REVIEW_126.md | own work | nothing external to trace | 10e0b00 |
| assets/audio/title_theme_v3/STUDY.md | public domain myth | own text; myth names only (kronos) | 10e0b00 |
| assets/audio/title_theme_v3/arrange_report_126.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/title_theme_v3/motif_candidates.yaml | public domain myth | own text; myth names only (kronos) | 10e0b00 |
| assets/audio/title_theme_v3/spice/SPICE.md | own work | nothing external to trace | befc1c7 |
| assets/audio/title_theme_v3/spice/report_d1.json | own work | nothing external to trace | befc1c7 |
| assets/audio/title_theme_v3/spice/report_d1.txt | own work | nothing external to trace | befc1c7 |
| assets/audio/title_theme_v3/spice/report_d2.json | own work | nothing external to trace | befc1c7 |
| assets/audio/title_theme_v3/spice/report_d2.txt | own work | nothing external to trace | befc1c7 |
| assets/audio/title_theme_v3/spice/report_d3.json | own work | nothing external to trace | befc1c7 |
| assets/audio/title_theme_v3/spice/report_d3.txt | own work | nothing external to trace | befc1c7 |
| assets/audio/title_theme_v3/spice/report_d3_humanize.json | own work | nothing external to trace | befc1c7 |
| assets/audio/title_theme_v3/spice/report_d3_humanize.txt | own work | nothing external to trace | befc1c7 |
| assets/audio/title_theme_v3/title_theme_v3.mid | own work | nothing external to trace | 9cf8aec |
| assets/audio/title_theme_v3/title_theme_v3.ogg | own work | nothing external to trace | e526c5f |
| assets/audio/title_theme_v3/title_theme_v3_126.mid | own work | nothing external to trace | 9cf8aec |
| assets/audio/title_theme_v3/title_theme_v3_126.ogg | own work | nothing external to trace | e526c5f |
| assets/audio/title_theme_v3/title_theme_v3_126_loop.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/title_theme_v4/NOTES.md | public domain myth | own text; myth names only (kronos, percy) | 10e0b00 |
| assets/audio/title_theme_v4/arrange_report_v4.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/title_theme_v4/hook_v4.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/title_theme_v4/humanize_medium.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/title_theme_v4/humanize_spicy.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/title_theme_v4/humanize_subtle.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/title_theme_v4/score_v4.yaml | public domain myth | own text; myth names only (kronos, percy) | 10e0b00 |
| assets/audio/title_theme_v4/spice_medium.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/title_theme_v4/spice_spicy.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/title_theme_v4/spice_subtle.json | own work | nothing external to trace | 10e0b00 |
| assets/audio/title_theme_v4/title_theme_v4_medium.ogg | own work | nothing external to trace | bd255e5 |
| assets/audio/title_theme_v4/title_theme_v4_medium_loop.json | public domain myth | own text; myth names only (kronos, percy) | 10e0b00 |
| assets/audio/title_theme_v4/title_theme_v4_spicy.ogg | own work | nothing external to trace | bd255e5 |
| assets/audio/title_theme_v4/title_theme_v4_spicy_loop.json | public domain myth | own text; myth names only (kronos, percy) | 10e0b00 |
| assets/audio/title_theme_v4/title_theme_v4_subtle.ogg | own work | nothing external to trace | bd255e5 |
| assets/audio/title_theme_v4/title_theme_v4_subtle_loop.json | public domain myth | own text; myth names only (kronos, percy) | 10e0b00 |
| assets/audio/title_theme_v5/NOTES.md | public domain myth | own text; myth names only (kronos, percy) | 59f1b52 |
| assets/audio/title_theme_v5/arrange_report_v5.json | own work | nothing external to trace | 59f1b52 |
| assets/audio/title_theme_v5/humanize_v5.json | own work | nothing external to trace | 59f1b52 |
| assets/audio/title_theme_v5/score_v5.yaml | public domain myth | own text; myth names only (kronos, percy) | 59f1b52 |
| assets/audio/title_theme_v5/title_theme_v5.ogg | own work | nothing external to trace | 59f1b52 |
| assets/audio/title_theme_v5/title_theme_v5_loop.json | public domain myth | own text; myth names only (kronos, percy) | 59f1b52 |
| assets/fonts/PressStart2P-Regular.ttf | own work | nothing external to trace | e526c5f |
| data/ai_cache/1000ab04c3e51c4af3001ce57132eb861e4d044528342361de7e521d2dfdd83a.json | own work | nothing external to trace | fd105d1 |
| data/ai_cache/10f8a49297ccc492ef1861f52e5853cb29181c6b713bc458602b8c7a1733c463.json | own work | nothing external to trace | fd105d1 |
| data/ai_cache/2866797e4d4ac3189ec50332fcb221cf5372e31ef1f6adf22869f25ba62268dc.json | own work | nothing external to trace | fd105d1 |
| data/ai_cache/7a97d917027bae48320fa1be7ee95be82873cbbd6b4e00343103117f654423bd.json | own work | nothing external to trace | fd105d1 |
| data/ai_cache/README.md | own work | nothing external to trace | fd105d1 |
| data/ai_cache/d66efc739922917283736fc3de6f43d3e85ba8829455ae6f8fc8b4c2d38cfe56.json | own work | nothing external to trace | fd105d1 |
| data/ai_cache/dfb1b67e32102629d2437c6616bdcded4aaa3f8600d7044ebd0205b13c629bbe.json | own work | nothing external to trace | fd105d1 |
| data/demo/manifest.json | public domain myth | own text; myth names only (kronos) | 25ed137 |
| data/demo/run_001.json | own work | nothing external to trace | 25ed137 |
| data/dissonance_rules.json | own work | nothing external to trace | 10e0b00 |
| data/drum_patterns.json | own work | nothing external to trace | 10e0b00 |
| data/ear_calibration.csv | public domain myth | own text; myth names only (percy) | 10e0b00 |
| data/ear_ledger.csv | public domain myth | own text; myth names only (percy) | 10e0b00 |
| data/enemies/roster.json | public domain myth | own text; myth names only (percy) | 10e0b00 |
| data/eye_ledger.csv | own work | nothing external to trace | 10e0b00 |
| data/intro_stars.json | public domain myth | own text; myth names only (kronos) | 0fa9d0a |
| data/intro_text.json | own work | nothing external to trace | 0fa9d0a |
| data/maps/osm/southampton_town_quay.json | own work | nothing external to trace | 10e0b00 |
| data/maps/osm/southampton_town_quay_preview_3x.png | own work | nothing external to trace | 10e0b00 |
| data/maps/osm/southampton_town_quay_tileset.png | own work | nothing external to trace | 10e0b00 |
| data/maps/osm/westminster_big_ben.json | own work | nothing external to trace | 10e0b00 |
| data/maps/osm/westminster_big_ben_preview_3x.png | own work | nothing external to trace | 10e0b00 |
| data/maps/osm/westminster_big_ben_tileset.png | own work | nothing external to trace | 10e0b00 |
| data/maps/osm/winchester_high_street.json | own work | nothing external to trace | 10e0b00 |
| data/maps/osm/winchester_high_street_preview_3x.png | own work | nothing external to trace | 10e0b00 |
| data/maps/osm/winchester_high_street_tileset.png | own work | nothing external to trace | 10e0b00 |
| data/maps/real_places.json | ODbL data | kind real_places, ODbL and openstreetmap.org inside the card | 2360155 |
| data/maps/ship_sample_tiled.json | public domain myth | own text; myth names only (percy) | 10e0b00 |
| data/maps/southampton_sample.json | own work | nothing external to trace | 10e0b00 |
| data/maps/westminster_sample.json | own work | nothing external to trace | 10e0b00 |
| data/maps/winchester_sample.json | own work | nothing external to trace | 10e0b00 |
| data/mechanics/action_recipes.json | public domain myth | own text; myth names only (kronos, percy, prometheus) | 10e0b00 |
| data/mechanics/jrpg_recipes.json | public domain myth | own text; myth names only (kronos, percy) | 27f9c37 |
| data/mechanics/pacing_recipes.json | public domain myth | own text; myth names only (kronos) | 10e0b00 |
| data/meta_bake.json | public domain myth | own text; myth names only (percy) | c862814 |
| data/music_recipes.json | own work | nothing external to trace | 10e0b00 |
| data/nes_palette.json | own work | nothing external to trace | e526c5f |
| data/osm_cache/southampton_town_quay.json | ODbL data | its own generator and osm3s copyright name openstreetmap.org | 10e0b00 |
| data/osm_cache/westminster_big_ben.json | ODbL data | its own generator and osm3s copyright name openstreetmap.org | 10e0b00 |
| data/osm_cache/winchester_high_street.json | ODbL data | its own generator and osm3s copyright name openstreetmap.org | 10e0b00 |
| data/palette_recipes.json | public domain myth | own text; myth names only (percy) | 72ce654 |
| data/palettes/scene_battle_corridor.json | own work | nothing external to trace | 10e0b00 |
| data/palettes/scene_battle_deck_night.json | own work | nothing external to trace | 10e0b00 |
| data/palettes/scene_battle_quay_dusk.json | own work | nothing external to trace | 10e0b00 |
| data/palettes/scene_battle_wardroom.json | own work | nothing external to trace | 10e0b00 |
| data/palettes/scene_icons.json | own work | nothing external to trace | 10e0b00 |
| data/palettes/scene_sea.json | own work | nothing external to trace | 10e0b00 |
| data/palettes/scene_ship.json | own work | nothing external to trace | 7a73469 |
| data/palettes/scene_southampton.json | own work | nothing external to trace | 10e0b00 |
| data/palettes/scene_title.json | own work | nothing external to trace | 7a73469 |
| data/palettes/scene_ui.json | own work | nothing external to trace | 10e0b00 |
| data/palettes/scene_westminster.json | own work | nothing external to trace | 10e0b00 |
| data/palettes/scene_winchester.json | own work | nothing external to trace | 10e0b00 |
| data/recipes/capcom.json | own work | nothing external to trace | 10e0b00 |
| data/recipes/classical.json | own work | nothing external to trace | 10e0b00 |
| data/recipes/composers.json | own work | nothing external to trace | 10e0b00 |
| data/recipes/fox.json | own work | nothing external to trace | 10e0b00 |
| data/recipes/jrpg.json | own work | nothing external to trace | 10e0b00 |
| data/recipes/konami.json | own work | nothing external to trace | 10e0b00 |
| data/recipes/nintendo.json | own work | nothing external to trace | 10e0b00 |
| data/room_palettes.json | own work | nothing external to trace | 8014e1c |
| data/scene_palettes.json | public domain myth | own text; myth names only (percy) | fc25bcc |
| data/schemas/dissonance_rules.schema.json | own work | nothing external to trace | 10e0b00 |
| data/schemas/talk_cards.schema.json | public domain myth | own text; myth names only (percy) | 14d786e |
| data/sprite_recipes.json | public domain myth | own text; myth names only (percy) | 10e0b00 |
| data/sprite_redraw_queue.json | public domain myth | own text; myth names only (percy) | 10e0b00 |
| data/talk_cards.json | public domain myth | own text; myth names only (percy, prometheus) | 14d786e |
| data/talk_profanity.json | flagged | data carries a CC0 source claim (dariusk/corpora) and knowledge/LICENSES.md has no row for it | b36c28c |
| data/title.json | own work | nothing external to trace | dc30317 |
| data/title_flash.json | own work | nothing external to trace | dc30317 |
| data/title_timing.json | own work | nothing external to trace | 0fa9d0a |
| data/ui_layouts.json | public domain myth | own text; myth names only (percy) | 10e0b00 |
| game/objects/obj_pp_drive/Create_0.gml | own work | nothing external to trace | uncommitted |
| game/objects/obj_pp_drive/Draw_0.gml | own work | nothing external to trace | uncommitted |
| game/objects/obj_pp_drive/Step_0.gml | own work | nothing external to trace | uncommitted |
| game/objects/obj_pp_drive/obj_pp_drive.yy | own work | nothing external to trace | uncommitted |
| game/rooms/rm_pp_drive/rm_pp_drive.yy | own work | nothing external to trace | uncommitted |
| game/scripts/pp_drive/pp_drive.gml | own work | nothing external to trace | uncommitted |
| game/scripts/pp_drive/pp_drive.yy | own work | nothing external to trace | uncommitted |
| game/scripts/pp_look/pp_look.gml | own work | nothing external to trace | 8014e1c |
| game/scripts/pp_look/pp_look.yy | own work | nothing external to trace | 8014e1c |
| game/scripts/pp_map_tile/pp_map_tile.gml | flagged | clean-room review row says 'pending' | 49fd2ef |
| game/scripts/pp_map_tile/pp_map_tile.yy | own work | nothing external to trace | 49fd2ef |
| game/scripts/pp_text/pp_text.gml | own work | nothing external to trace | ab4b80a |
| game/scripts/pp_text/pp_text.yy | own work | nothing external to trace | ab4b80a |
| game/sprites_src/bg/bg_battle_corridor.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/bg/bg_battle_corridor.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/bg/bg_battle_deck_night.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/bg/bg_battle_deck_night.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/bg/bg_battle_quay_dusk.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/bg/bg_battle_quay_dusk.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/bg/bg_battle_wardroom.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/bg/bg_battle_wardroom.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/chars/hadrian_battle.json | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/hadrian_battle.png | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/hadrian_god_battle.json | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/hadrian_god_battle.png | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/hadrian_ow.json | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/hadrian_ow.png | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/hadrian_ow_v2.json | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/hadrian_ow_v2.png | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/konrad_battle.json | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/konrad_battle.png | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/konrad_god_battle.json | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/konrad_god_battle.png | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/konrad_ow.json | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/konrad_ow.png | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/konrad_ow_v2.json | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/konrad_ow_v2.png | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/percy_battle.json | public domain myth | own text; myth names only (percy) | e29612f |
| game/sprites_src/chars/percy_battle.png | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/percy_god_battle.json | public domain myth | own text; myth names only (percy) | e29612f |
| game/sprites_src/chars/percy_god_battle.png | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/percy_ow.json | public domain myth | own text; myth names only (percy) | e29612f |
| game/sprites_src/chars/percy_ow.png | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/percy_ow_v2.json | public domain myth | own text; myth names only (percy) | e29612f |
| game/sprites_src/chars/percy_ow_v2.png | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/sailor_battle.json | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/sailor_battle.png | own work | nothing external to trace | 7a73469 |
| game/sprites_src/chars/sailor_ow.json | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/sailor_ow.png | own work | nothing external to trace | 7a73469 |
| game/sprites_src/chars/sailor_ow_v2.json | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/sailor_ow_v2.png | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/zander_battle.json | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/zander_battle.png | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/zander_god_battle.json | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/zander_god_battle.png | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/zander_ow.json | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/zander_ow.png | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/zander_ow_v2.json | own work | nothing external to trace | e29612f |
| game/sprites_src/chars/zander_ow_v2.png | own work | nothing external to trace | e29612f |
| game/sprites_src/enemies/bilge_slime.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/enemies/bilge_slime.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/enemies/deck_rat.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/enemies/deck_rat.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/enemies/gull.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/enemies/gull.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/enemies/navy_sailor.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/enemies/navy_sailor.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/enemies/petty_officer.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/enemies/petty_officer.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/enemies/rogue_wave.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/enemies/rogue_wave.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/enemies/rope_knot.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/enemies/rope_knot.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/env/quay/TILES.md | own work | nothing external to trace | f74dc25 |
| game/sprites_src/env/quay/quay_tiles.json | own work | nothing external to trace | f74dc25 |
| game/sprites_src/env/quay/quay_tiles.png | own work | nothing external to trace | f74dc25 |
| game/sprites_src/env/ts_exterior.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/env/ts_exterior.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/env/ts_exterior_tiled.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/env/ts_ship.json | own work | nothing external to trace | 7a73469 |
| game/sprites_src/env/ts_ship.png | own work | nothing external to trace | 7a73469 |
| game/sprites_src/env/ts_ship_tiled.json | own work | nothing external to trace | 7a73469 |
| game/sprites_src/icons/spr_pp_icon_cursor_16.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/icons/spr_pp_icon_cursor_16.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/icons/spr_pp_icon_cursor_8.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/icons/spr_pp_icon_cursor_8.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/icons/spr_pp_icon_items_16.json | public domain myth | own text; myth names only (percy) | 10e0b00 |
| game/sprites_src/icons/spr_pp_icon_items_16.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/icons/spr_pp_icon_items_8.json | public domain myth | own text; myth names only (percy) | 10e0b00 |
| game/sprites_src/icons/spr_pp_icon_items_8.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/icons/spr_pp_icon_status_16.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/icons/spr_pp_icon_status_16.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/icons/spr_pp_icon_status_8.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/icons/spr_pp_icon_status_8.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/title/spr_title_car_fade1.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_car_fade1.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_car_fade2.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_car_fade2.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_car_fade3.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_car_fade3.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_car_fade4.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_car_fade4.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cloud_fade1.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cloud_fade1.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cloud_fade2.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cloud_fade2.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cloud_fade3.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cloud_fade3.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cloud_fade4.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cloud_fade4.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cone_fade1.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cone_fade1.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cone_fade2.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cone_fade2.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cone_fade3.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cone_fade3.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cone_fade4.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cone_fade4.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cone_flash.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_cone_flash.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_exhaust_fade1.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_exhaust_fade1.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_exhaust_fade2.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_exhaust_fade2.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_exhaust_fade3.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_exhaust_fade3.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_exhaust_fade4.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_exhaust_fade4.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_sign_fade1.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_sign_fade1.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_sign_fade2.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_sign_fade2.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_sign_fade3.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_sign_fade3.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_sign_fade4.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_sign_fade4.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_sign_flash.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_sign_flash.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_star.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/spr_title_star.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_BG_bigben.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_BG_bigben.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_BG_bigben_flash.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_BG_bigben_flash.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L1_sky_fade1.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L1_sky_fade1.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L1_sky_fade2.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L1_sky_fade2.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L1_sky_fade3.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L1_sky_fade3.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L1_sky_fade4.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L1_sky_fade4.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L1_sky_flash.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L1_sky_flash.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L2_clouds_fade1.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L2_clouds_fade1.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L2_clouds_fade2.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L2_clouds_fade2.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L2_clouds_fade3.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L2_clouds_fade3.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L2_clouds_fade4.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L2_clouds_fade4.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L2_clouds_flash.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L2_clouds_flash.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L3_downs_fade1.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L3_downs_fade1.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L3_downs_fade2.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L3_downs_fade2.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L3_downs_fade3.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L3_downs_fade3.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L3_downs_fade4.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L3_downs_fade4.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L3_downs_flash.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L3_downs_flash.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L4_fields_fade1.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L4_fields_fade1.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L4_fields_fade2.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L4_fields_fade2.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L4_fields_fade3.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L4_fields_fade3.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L4_fields_fade4.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L4_fields_fade4.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L4_fields_flash.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L4_fields_flash.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L5_verge_fade1.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L5_verge_fade1.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L5_verge_fade2.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L5_verge_fade2.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L5_verge_fade3.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L5_verge_fade3.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L5_verge_fade4.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L5_verge_fade4.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L5_verge_flash.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L5_verge_flash.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L6_road_fade1.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L6_road_fade1.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L6_road_fade2.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L6_road_fade2.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L6_road_fade3.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L6_road_fade3.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L6_road_fade4.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L6_road_fade4.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L6_road_flash.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L6_road_flash.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L7_fg_fade1.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L7_fg_fade1.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L7_fg_fade2.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L7_fg_fade2.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L7_fg_fade3.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L7_fg_fade3.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L7_fg_fade4.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L7_fg_fade4.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L7_fg_flash.json | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/title/title_L7_fg_flash.png | own work | nothing external to trace | 0fa9d0a |
| game/sprites_src/ui/screens/ui_battle.json | public domain myth | own text; myth names only (percy) | 10e0b00 |
| game/sprites_src/ui/screens/ui_battle.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/ui/screens/ui_battle_sprites.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/ui/screens/ui_dialogue.json | public domain myth | own text; myth names only (percy) | 10e0b00 |
| game/sprites_src/ui/screens/ui_dialogue.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/ui/screens/ui_dialogue_sprites.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/ui/screens/ui_menu.json | public domain myth | own text; myth names only (percy) | 10e0b00 |
| game/sprites_src/ui/screens/ui_menu.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/ui/screens/ui_menu_sprites.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/ui/spr_pp_ui_cursor.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/ui/spr_pp_ui_cursor.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/ui/spr_pp_ui_enemy.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/ui/spr_pp_ui_enemy.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/ui/spr_pp_ui_party.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/ui/spr_pp_ui_party.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/ui/spr_pp_ui_tab.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/ui/spr_pp_ui_tab.png | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/ui/spr_pp_ui_window.json | own work | nothing external to trace | 10e0b00 |
| game/sprites_src/ui/spr_pp_ui_window.png | own work | nothing external to trace | 10e0b00 |
| knowledge/.hermes-tmp.5hMOZz | own work | nothing external to trace | 10e0b00 |
| knowledge/ARRIVAL-CONTENT.md | public domain myth | own text; myth names only (percy, prometheus) | uncommitted |
| knowledge/ART-BIBLE.md | public domain myth | own text; myth names only (percy) | 10e0b00 |
| knowledge/BUG-TRIAGE-2026-10-23.md | public domain myth | own text; myth names only (percy) | uncommitted |
| knowledge/BUILD-TIMELINE.md | own work | nothing external to trace | 25ed137 |
| knowledge/CARD-MAP.md | public domain myth | own text; myth names only (kronos, percy) | cbad4dc |
| knowledge/CARD-MAP.md.bak-2026-10-22-cardmap2 | own work | nothing external to trace | uncommitted |
| knowledge/CHARACTER-BIBLE.md | public domain myth | own text; myth names only (kronos, percy) | 10e0b00 |
| knowledge/DEMO-KIT-2026-10-22.md | own work | nothing external to trace | b614512 |
| knowledge/DEMO-SCRIPT.md | public domain myth | own text; myth names only (kronos, percy, prometheus) | uncommitted |
| knowledge/DRIVE-SHOT-LIST.md | own work | nothing external to trace | uncommitted |
| knowledge/EAR-GATE-2026-10-23.md | own work | nothing external to trace | uncommitted |
| knowledge/FOX-STYLE-AUDIT.md | public domain myth | own text; myth names only (kronos) | cbad4dc |
| knowledge/FOX-STYLE.md | own work | nothing external to trace | cbad4dc |
| knowledge/GAMEDEV-DECISIONS-2026-10-22.md | public domain myth | own text; myth names only (kronos) | 708d442 |
| knowledge/GAMEDEV-DECISIONS-2026-10-23.md | public domain myth | own text; myth names only (kronos, percy, prometheus) | 02b7d52 |
| knowledge/GATE-DIALOGUE.md | public domain myth | own text; myth names only (kronos, prometheus) | 79564da |
| knowledge/GATE-GREEN-2026-10-22.md | own work | nothing external to trace | uncommitted |
| knowledge/HACKATHON-AUDIT-2026-10-22.md | public domain myth | own text; myth names only (percy) | uncommitted |
| knowledge/KEY-HYGIENE-2026-10-22.md | own work | nothing external to trace | uncommitted |
| knowledge/KEY-LEAK-SCAN-2026-10-23.md | own work | nothing external to trace | uncommitted |
| knowledge/MUSIC-DISSONANCE.md | own work | nothing external to trace | 10e0b00 |
| knowledge/MUSIC-DRUMS.md | own work | nothing external to trace | 10e0b00 |
| knowledge/MUSIC-HOOK-GRAMMAR.md | own work | nothing external to trace | 10e0b00 |
| knowledge/MUSIC-STYLE-BIBLE.md | own work | names the reference in analysis, outside shipped paths: deltarune, papyrus, toby fox, undertale, snowdin town | 10e0b00 |
| knowledge/NAMES-BIBLE.md | public domain myth | own text; myth names only (atlas, kronos, ouranos, percy, prometheus) | 10e0b00 |
| knowledge/NES-AUDIT-SLICE-2026-10-23.md | own work | nothing external to trace | uncommitted |
| knowledge/NES-AUDIT.json | own work | nothing external to trace | 10e0b00 |
| knowledge/NES-AUDIT.json.bak-2026-10-23-r41 | own work | nothing external to trace | uncommitted |
| knowledge/NES-AUDIT.md | public domain myth | own text; myth names only (percy) | dc30317 |
| knowledge/PALETTE-GATE-DECISIONS-2026-10-22.md | public domain myth | own text; myth names only (percy) | 5a385eb |
| knowledge/PALETTE-PASS-LIST.md | public domain myth | own text; myth names only (percy) | uncommitted |
| knowledge/PALETTE-SYNERGY.md | public domain myth | own text; myth names only (percy) | 9a5a56f |
| knowledge/READINESS-2026-10-22.md | public domain myth | own text; myth names only (percy) | uncommitted |
| knowledge/READINESS-2026-10-23.md | public domain myth | own text; myth names only (percy) | uncommitted |
| knowledge/REFINEMENT-BACKLOG-TEMPLATE.md | own work | nothing external to trace | 708d442 |
| knowledge/REVIEW-ACTION-PHASES-2026-10-22.md | public domain myth | own text; myth names only (percy, prometheus) | uncommitted |
| knowledge/REVIEW-META-BAKE-2026-10-23.md | public domain myth | own text; myth names only (percy) | cfc3012 |
| knowledge/SPRITE-CRAFT.md | public domain myth | own text; myth names only (percy) | 10e0b00 |
| knowledge/SPRITE-CRITIQUE.md | public domain myth | own text; myth names only (kronos, percy) | 10e0b00 |
| knowledge/TEST-TRIAGE-PINE-2026-10-22.md | own work | names the reference in analysis, outside shipped paths: queen | uncommitted |
| knowledge/VIDEO-PLAN.md | public domain myth | own text; myth names only (kronos) | uncommitted |
| knowledge/char-pipe-review/review_char_pipe5_reconfirm.py | own work | nothing external to trace | 10e0b00 |
| knowledge/char-pipe-review/review_char_pipe6_f1_fresh.py | own work | nothing external to trace | e9df60f |
| knowledge/char-pipe-review/review_char_pipe7_f234_fresh.py | own work | nothing external to trace | e9df60f |
| knowledge/maps/REAL-PLACES.md | own work | nothing external to trace | uncommitted |
| knowledge/maps/SCENE-FACT-SHEETS.md | public domain myth | own text; myth names only (percy) | uncommitted |
| knowledge/mechanics/ACTION-MECHANICS.md | public domain myth | own text; myth names only (kronos, percy, prometheus) | 10e0b00 |
| knowledge/mechanics/JRPG-MECHANICS.md | own work | names the reference in analysis, outside shipped paths: undertale | 27f9c37 |
| knowledge/mechanics/PACING-AND-CUTSCENES.md | own work | names the reference in analysis, outside shipped paths: queen, toriel, undertale | 10e0b00 |
| knowledge/music-styles/capcom.md | own work | nothing external to trace | 10e0b00 |
| knowledge/music-styles/classical.md | own work | nothing external to trace | 10e0b00 |
| knowledge/music-styles/composers.md | own work | nothing external to trace | 10e0b00 |
| knowledge/music-styles/fox.md | own work | names the reference in analysis, outside shipped paths: berdly, deltarune, flowey, papyrus, queen, toby fox | 10e0b00 |
| knowledge/music-styles/jrpg.md | own work | nothing external to trace | 10e0b00 |
| knowledge/music-styles/konami.md | own work | nothing external to trace | 10e0b00 |
| knowledge/music-styles/nintendo.md | own work | names the reference in analysis, outside shipped paths: the underground | 10e0b00 |
| knowledge/readiness-2026-10-24/build.out | own work | nothing external to trace | uncommitted |
| output/env_ship_preview.png | own work | nothing external to trace | 2360db5 |
| output/nes_title_frame.png | own work | nothing external to trace | 0e0c50a |
| output/scene_palettes.json | own work | nothing external to trace | 2360db5 |
| output/sfx_preview_3x.png | own work | nothing external to trace | 2360db5 |
| output/ts2_bigben_preview.png | own work | nothing external to trace | 2360db5 |
| output/ts2_world_preview.png | own work | nothing external to trace | 2360db5 |
| pal_check_synergy_deck.json | public domain myth | own text; myth names only (percy) | uncommitted |
| pytest.ini | own work | nothing external to trace | uncommitted |
| specs/14-title-screen-drive.md | public domain myth | own text; myth names only (kronos) | 9080887 |
| specs/15-env-tiles-ship.md | public domain myth | own text; myth names only (percy) | 10e0b00 |
| specs/16-talk-command.md | own work | names the reference in analysis, outside shipped paths: toby fox | 10e0b00 |
| specs/17-action-movement.md | public domain myth | own text; myth names only (percy) | uncommitted |
| specs/18-boss-phases.md | public domain myth | own text; myth names only (kronos, percy, prometheus) | 43b6fe6 |
| specs/19-llm-talk.md | public domain myth | own text; myth names only (kronos, percy) | dd9fe93 |
| tests/test_ai_client.py | own work | nothing external to trace | 10e0b00 |
| tests/test_audio.py | public domain myth | own text; myth names only (percy, prometheus) | 10e0b00 |
| tests/test_bake_meta.py | own work | nothing external to trace | c862814 |
| tests/test_beat_sheet.py | own work | nothing external to trace | fc25bcc |
| tests/test_build_inputs.py | own work | nothing external to trace | 99f0d91 |
| tests/test_build_pp03.py | own work | nothing external to trace | c05d907 |
| tests/test_build_pp04.py | own work | nothing external to trace | c05d907 |
| tests/test_capture_quiet.py | own work | nothing external to trace | 39ed5c6 |
| tests/test_capture_title.py | own work | nothing external to trace | 10e0b00 |
| tests/test_cleanroom.py | own work | names the reference in analysis, outside shipped paths: queen | 0f27329 |
| tests/test_dialogue_v2.py | public domain myth | own text; myth names only (percy, prometheus) | 79564da |
| tests/test_dissonance_rules.py | own work | nothing external to trace | 10e0b00 |
| tests/test_drive_v2.py | own work | nothing external to trace | uncommitted |
| tests/test_ear_critic.py | own work | nothing external to trace | 10e0b00 |
| tests/test_first_fight.py | own work | nothing external to trace | fc25bcc |
| tests/test_hook_score.py | own work | nothing external to trace | 10e0b00 |
| tests/test_humanize.py | own work | nothing external to trace | 10e0b00 |
| tests/test_intro.py | own work | nothing external to trace | dc30317 |
| tests/test_ledger.py | public domain myth | own text; myth names only (percy) | 9e6e1ea |
| tests/test_look.py | own work | nothing external to trace | 8014e1c |
| tests/test_make_characters_v2.py | public domain myth | own text; myth names only (percy) | e29612f |
| tests/test_make_env_ship.py | public domain myth | own text; myth names only (percy) | 10e0b00 |
| tests/test_make_quay_tiles.py | own work | nothing external to trace | f74dc25 |
| tests/test_make_title_world.py | own work | nothing external to trace | 10e0b00 |
| tests/test_meta_client.py | own work | nothing external to trace | fd105d1 |
| tests/test_nes_audit_all.py | own work | nothing external to trace | 10e0b00 |
| tests/test_nes_composite_check.py | own work | nothing external to trace | 72a9da5 |
| tests/test_no_network_in_build.py | own work | nothing external to trace | 43995a0 |
| tests/test_osm_to_map.py | own work | nothing external to trace | 10e0b00 |
| tests/test_palette_synergy.py | public domain myth | own text; myth names only (percy) | 0e0c50a |
| tests/test_play_demo.py | own work | nothing external to trace | uncommitted |
| tests/test_pp_drive_cue.py | own work | nothing external to trace | uncommitted |
| tests/test_quantize_concept.py | own work | nothing external to trace | fc25bcc |
| tests/test_quay_tiles_wire.py | public domain myth | own text; myth names only (atlas) | 49fd2ef |
| tests/test_save_gameover.py | public domain myth | own text; myth names only (percy, prometheus) | 43995a0 |
| tests/test_scene_palette_set.py | public domain myth | own text; myth names only (percy) | fc25bcc |
| tests/test_scene_palettes.py | own work | nothing external to trace | 7a73469 |
| tests/test_scene_runner.py | own work | nothing external to trace | 02bc154 |
| tests/test_sfx.py | own work | nothing external to trace | d81dfff |
| tests/test_slice_route.py | own work | nothing external to trace | 26a8820 |
| tests/test_slice_story.py | public domain myth | own text; myth names only (percy, prometheus) | uncommitted |
| tests/test_spice.py | own work | nothing external to trace | befc1c7 |
| tests/test_talk_guard.py | own work | nothing external to trace | b36c28c |
| tests/test_test_inputs.py | own work | nothing external to trace | 176bab9 |
| tests/test_text_reveal.py | own work | nothing external to trace | ab4b80a |
| tests/test_title_bands.py | own work | nothing external to trace | 43995a0 |
| tests/test_title_path.py | own work | nothing external to trace | 24adf10 |
| tests/test_title_timing.py | own work | nothing external to trace | e26709b |
| tools/_drum_dsl.py | own work | nothing external to trace | 10e0b00 |
| tools/_drum_feels.py | own work | nothing external to trace | 10e0b00 |
| tools/_drum_fills.py | own work | nothing external to trace | 10e0b00 |
| tools/_drum_waltz.py | own work | nothing external to trace | 10e0b00 |
| tools/_fade_probe.py | own work | nothing external to trace | 10e0b00 |
| tools/_intro_probe.py | own work | nothing external to trace | 10e0b00 |
| tools/_logo_probe.py | own work | nothing external to trace | 10e0b00 |
| tools/_save_load_probe.py | own work | nothing external to trace | 483d230 |
| tools/ai_client.py | own work | nothing external to trace | 10e0b00 |
| tools/apply_title_timing.py | own work | nothing external to trace | 10e0b00 |
| tools/art/check_icons_nes.py | own work | nothing external to trace | 10e0b00 |
| tools/art/contrast_check.py | public domain myth | own text; myth names only (percy) | fc25bcc |
| tools/art/make_battle_bg.py | own work | nothing external to trace | 10e0b00 |
| tools/art/make_characters.py | public domain myth | own text; myth names only (atlas, percy) | 7a73469 |
| tools/art/make_characters_v2.py | public domain myth | own text; myth names only (percy) | e29612f |
| tools/art/make_enemies.py | public domain myth | own text; myth names only (percy) | 10e0b00 |
| tools/art/make_env_ship.py | public domain myth | own text; myth names only (percy) | 10e0b00 |
| tools/art/make_exterior_maps.py | own work | nothing external to trace | 10e0b00 |
| tools/art/make_icons_nes.py | public domain myth | own text; myth names only (percy) | 10e0b00 |
| tools/art/make_palette_sheet.py | own work | nothing external to trace | 10e0b00 |
| tools/art/make_quay_tiles.py | own work | nothing external to trace | f74dc25 |
| tools/art/make_ts_exterior.py | own work | nothing external to trace | 10e0b00 |
| tools/art/make_ui_nes.py | public domain myth | own text; myth names only (percy) | 10e0b00 |
| tools/art/measure_compose_areas.py | own work | nothing external to trace | 10e0b00 |
| tools/art/nes_bg.py | own work | nothing external to trace | 10e0b00 |
| tools/art/nes_palette_build.py | own work | nothing external to trace | 10e0b00 |
| tools/art/nes_snap.py | own work | nothing external to trace | 10e0b00 |
| tools/art/pixel_map.py | own work | nothing external to trace | 10e0b00 |
| tools/art/report_battle_bg.py | own work | nothing external to trace | 10e0b00 |
| tools/art/scene_palette.py | own work | nothing external to trace | 7a73469 |
| tools/art/serif_caps.py | own work | nothing external to trace | 10e0b00 |
| tools/art/tile_report.py | own work | nothing external to trace | 10e0b00 |
| tools/art/title_bands.py | own work | nothing external to trace | 43995a0 |
| tools/bake_meta.py | own work | nothing external to trace | c862814 |
| tools/capture_drive.py | own work | nothing external to trace | uncommitted |
| tools/check_action_recipes.py | own work | nothing external to trace | 10e0b00 |
| tools/check_art_bible.py | own work | nothing external to trace | 10e0b00 |
| tools/check_build_inputs.py | own work | nothing external to trace | 99f0d91 |
| tools/check_cues.py | own work | nothing external to trace | uncommitted |
| tools/check_dissonance_rules.py | own work | nothing external to trace | 10e0b00 |
| tools/check_drum_patterns.py | own work | nothing external to trace | 10e0b00 |
| tools/check_env_tiles.py | public domain myth | own text; myth names only (percy) | 10e0b00 |
| tools/check_font_coverage.py | own work | nothing external to trace | 43995a0 |
| tools/check_hadrian_score.py | own work | nothing external to trace | 10e0b00 |
| tools/check_music_style_bible.py | own work | names the reference in analysis, outside shipped paths: deltarune, papyrus, toby fox, undertale | 10e0b00 |
| tools/check_pacing.py | own work | nothing external to trace | 10e0b00 |
| tools/check_palette_recipes.py | own work | nothing external to trace | fc25bcc |
| tools/check_scene_palettes.py | own work | nothing external to trace | 83c042c |
| tools/check_test_inputs.py | own work | nothing external to trace | 176bab9 |
| tools/check_ts_exterior.py | own work | nothing external to trace | 10e0b00 |
| tools/drive_v2.py | own work | nothing external to trace | 79564da |
| tools/ear_critic.py | own work | nothing external to trace | 10e0b00 |
| tools/eye_critic.py | public domain myth | own text; myth names only (percy) | 10e0b00 |
| tools/gen_drum_patterns.py | own work | nothing external to trace | 10e0b00 |
| tools/hook_score.py | own work | nothing external to trace | 83c042c |
| tools/humanize.py | own work | nothing external to trace | 83c042c |
| tools/idle_check.py | own work | nothing external to trace | 39ed5c6 |
| tools/measure_demo_voices.py | own work | nothing external to trace | 10e0b00 |
| tools/measure_percy.py | public domain myth | own text; myth names only (percy) | 10e0b00 |
| tools/measure_theme_render.py | own work | nothing external to trace | 10e0b00 |
| tools/measure_title_scroll.py | own work | nothing external to trace | 10e0b00 |
| tools/measure_title_scroll_native.py | own work | nothing external to trace | e26709b |
| tools/meta_client.py | own work | nothing external to trace | fd105d1 |
| tools/nes_audit_all.py | own work | nothing external to trace | dc30317 |
| tools/nes_composite_check.py | own work | nothing external to trace | 72a9da5 |
| tools/nes_enforce.py | own work | nothing external to trace | 72a9da5 |
| tools/osm_to_map.py | own work | nothing external to trace | 10e0b00 |
| tools/palette_synergy.py | public domain myth | own text; myth names only (percy) | fc25bcc |
| tools/play_demo.py | own work | nothing external to trace | 39ed5c6 |
| tools/pp_intro_art.py | own work | nothing external to trace | 0fa9d0a |
| tools/pp_launch.py | own work | nothing external to trace | 39ed5c6 |
| tools/probe_quay_tiles.py | own work | nothing external to trace | 49fd2ef |
| tools/quantize_concept.py | own work | nothing external to trace | fc25bcc |
| tools/render_recipe_preview.py | own work | nothing external to trace | 10e0b00 |
| tools/scene_palette_set.py | public domain myth | own text; myth names only (percy) | fc25bcc |
| tools/sfx.py | public domain myth | own text; myth names only (percy) | d81dfff |
| tools/shrink_preview.py | own work | nothing external to trace | 10e0b00 |
| tools/spice.py | own work | nothing external to trace | befc1c7 |
| tools/talk_guard.py | own work | nothing external to trace | b36c28c |
| tools/theme_v4.py | own work | nothing external to trace | 10e0b00 |
| tools/theme_v5.py | own work | nothing external to trace | uncommitted |
| tools/title_preview_3x.py | own work | nothing external to trace | 10e0b00 |
