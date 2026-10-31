# PP-03 "Harbor" v4: the floor of the ear ledger, repaired in the arrangement

Card AUTO-MUSIC-NEXT (t_9861be83, musician). Clean room: this is the lane's own composition on the
project's own grid; nothing is quoted or transcribed from a published game.

`assets/audio/pp_03_harbor/` (v1), `pp_03_harbor_v2/` and `pp_03_harbor_v3/` are untouched. Every
file in this folder is new. The shipping master of this pass is `pp_03_harbor_v4b.mp3` (round 2);
`pp_03_harbor_v4.mp3` is round 1, kept so the two rounds can be heard against each other.

## 1. Why this cue

The pick came from the two measures the card names, on the newest build of every cue. The ear side
is the newest `summary` row per cue folder in `data/ear_ledger.csv`; the hook side is
`tools/hook_score.py` on that cue's newest MIDI.

| cue | newest build | hook (on grid) | ear (six criteria, of 60) |
| --- | --- | --- | --- |
| PP-01 Title | pp_01_title_v8 | 83 | 37 |
| PP-02 Drive | pp_drive_v4 | 92 | 32 (measured on this card, first ear row for v4) |
| **PP-03 Harbor** | **pp_03_harbor_v3** | **100** | **29 to 32** |
| PP-04 Navy Sailors | pp_04_navy_sailors_v3 | 99 | 32 |
| PP-05 Small Ship | pp_05_small_ship_v4 | 91 | 30 |
| PP-06 Percy | percy_theme_v2 | 91 | 31 |
| Boarding | pp_boarding_v2 | 93 to 100 | 31 |
| Arrival | pp_arrival_v2 | 98 | 31 |
| Fight | pp_fight_v2 | 97 | 30 |

Two readings changed the pick from the one the last card made:

- Drive v4 had never been heard, so its 29 was a v3 number. One call fixed that: `pp_drive_v4.mp3`
  scores 32 on `gemini-3.5-flash` (`ear_reviews/pp_drive_v4_20261025T032015Z.md`), so drive is off
  the floor and only harbor and boarding were left at the bottom, both already revised once.
- Harbor v3's two ear rows are 32 (`pp_03_harbor_v3_20261024T071744Z.md`) and 29
  (`pp_03_harbor_v3_20261024T071837Z.md`) on the same judge with the same audio, which is the ear's
  own noise floor. 29 is therefore the floor of the ledger among newest builds, and harbor is the
  pick. Its hook is the best in the registry, which is the point: the card says arrangement is where
  this cue's headroom is, and the ear agrees (drums 4, human 3, tension 5, variety 6, structure 6).

## 2. The score table, before and after

Hook meter (`tools/hook_score.py`, melody track `vrc6 pulse a`):

| build | on grid | humanized MIDI |
| --- | --- | --- |
| v3 | 100 | 95 |
| v4 round 1 | 100 | 95 (in `hook_report_render_v4.json`) |
| **v4 round 2 (shipped)** | **100** | **95** |

Ear, one judge (`gemini-3.5-flash`), same rubric, three calls of the same cue:

| build | hook | drums | tension | human | variety | structure | total | review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v3 (measured on this card, for a matched baseline) | 6 | 4 | 5 | 3 | 6 | 6 | **30** | `ear_reviews/pp_03_harbor_v3_20261025T032419Z.md` |
| v4 round 1 | 7 | 4 | 5 | 4 | 6 | 6 | **32** | `ear_reviews/pp_03_harbor_v4_20261025T032356Z.md` |
| **v4 round 2 (shipped)** | **7** | **5** | **5** | **4** | **7** | **7** | **35** | `ear_reviews/pp_03_harbor_v4b_20261025T032613Z.md` |

The ledger's 29 and 32 for v3 were taken on `gemini-3.5-flash-lite`. That model had a daily bucket
spent earlier in the day (the rotation moved every call onto `gemini-3.5-flash`), so the honest
comparison is the matched one above: v3 and v4 were heard by the same model on the same day, which
is the condition `knowledge/EAR-LOOP-2026-10-24.md` section 3 asks for before two rows are compared.

So: hook unchanged at 100 on the grid, ear up 5 points on the matched judge, with drums reaching 5,
which the 2026-10-22 ear sweep never gave a cue in this set, and variety and structure each up 1.

## 3. What changed, and why each change was the right lever

The melody, the cell, the chords and the tempo are byte identical to v3: 107 melody notes, the same
two bar H statement ten times, the same four sections of 8 bars, 68 bpm, 4/4, 32 bars, 112.941 s.
Nothing was added to the melody, because the hook meter is already full and the ear's low axes were
all in the arrangement.

| change | round | criterion it aims at | measure |
| --- | --- | --- | --- |
| the rung lists are rewritten so each 4 bar group has its own arc (arrival 5 1 0 2 then 4 1 6 3; settle 0 1 2 4 then 3 1 6 7; light 5 2 1 4 then 3 6 1 7; close 5 1 2 4 then 3 6 4 7), on top of the builder's one beat fill every fourth bar and two beat fill every eighth | 1 | drums 4, the card's "vary every 4 and 8 bars" | 32 bars, no two adjacent bars share a rung, four home patterns in use |
| the broken chord sits out close bars 5 and 6, so the lift to G5 is heard against the pad and the bass only | 1 | variety and structure (the 32 bar form now has a hole in it before the cadence) | pulse 1 falls from 224 to 208 notes, the 16 eighths of those two bars |
| a brighter roll through close bars 7 and 8 (`build_up`), so the loop point is approached rather than arrived at | 1 | drums, structure, and the loop seam's feel | dpcm 81 to 89 notes |
| the light section carries a second prepared ninth, bar 7, four bars after bar 5 | 1 | tension 5 | 2 devices per 8 bars, the top of the `MUSIC-DISSONANCE.md` section 4 budget (F4 spacing kept) |
| the lead's humanize block widens: velocity table [0, 6, -5, 8, -4, 4, -7, 5], 3 tick micro shift, 4 tick gate | 1 | human 3 | human 3 to 4 |
| the light section changes its drum identity to CLM-02 (rim ticks only) and its long fill to a tom sweep (FLT-02), and drops to level 0.8 | 2 | drums 4 to 5, and the 8 bar contrast between sections | drums 4 to 5, variety 6 to 7, structure 6 to 7 |

Everything the drums play is read by id from `data/drum_patterns.json` at build time; nothing is
invented. The ladder and the phrase plan are `knowledge/MUSIC-DRUMS.md` section 4.

## 4. The rest of the card's list, with its evidence

- Leitmotifs K, Z, P, H: H is this cue's material and is unchanged, the rise A4 C5 D5 E5 in bar one
  of every statement with the fall onto the tonic A, and the hook meter finds it as a 2 bar motif
  with 10 returns at 66 percent coverage. K, Z and P are the title and drive cues' statements
  (`tools/drive_v2.py` PLAN and LITERAL tables). Inserting one here would change this cue's
  identity and its clean room result, so it stays a Q rather than a silent edit.
- Drums vary every 4 and 8 bars: section 3, first row. Four calm home patterns (CLM-01, CLM-02,
  CLM-03, CLM-08), a one beat fill on every fourth bar, a two beat fill on every eighth, a rung
  change per bar, and a roll through the last two bars.
- Tasteful dissonance by `knowledge/MUSIC-DISSONANCE.md`: two prepared ninths in the light section
  (bars 5 and 7, four bars apart, F4), one in the other three sections, and one DIS-02 chromatic
  lower neighbour in the lead at light bar 22. Prepared and resolved by step, never on the first or
  last note of an H statement (F1), never in a cadence bar (F2). `tools/check_dissonance_rules.py`
  passes.
- Humanize: the lead's own velocity and micro timing, plus `tools/render_chip.py --humanize`, which
  re-articulated every note of the file: 1154 envelope points, 16 melody notes with vibrato, 4
  breaths, 1 grace note, 1 mordent, and 13 fills before the section changes at bars 9, 17, 25, 33.
- 126 bpm family: this cue is 68 bpm on purpose, as v1, v2 and v3 were. It is a low intensity cue
  under intro text and no spec pins a tempo for PP-03; 126 would be a spec decision, not this
  card's, so it is recorded here rather than changed. The card's phrasing is the balancer's, and
  PP-02 Drive is the cue that lives at 126.
- Real 2A03 plus VRC6 limits: 8 voices written (2A03 pulse 1, pulse 2, triangle, noise, dpcm; VRC6
  pulse a, pulse b, saw), 755 notes, noise and dpcm hold one pitch at a time, and no note doubles
  another on the same channel and tick (the builder refuses a note past the loop point and the
  register check refuses an out of range note).
- Palette first (ART-BIBLE RULE 0) is a visual rule: 4 background and 4 sprite palettes from the 54
  usable colours, written to `data/scene_palettes.json` before art. A music cue has no palette
  step; its equivalent is the style bible and the hook grammar, and both checks pass (`check_music_style_bible`,
  `hook_score`).

## 5. Checks run

- `build_pp03_v4.py --check`: 32 bars, 112.941 s, 68 bpm, 4/4, 751 notes (round 2: 755), 8 voices,
  first chord C, last chord E7.
- Hook meter: v4b 100 of 100 on the grid (`hook_report_v4b.json`), 95 on the humanized MIDI
  (`hook_report_v4b_humanized.json`), identical to v3 on both.
- Render: `render_chip.py --loop-bars 32 --humanize`, 112.941 s, peak -1.00 dBFS, rms -16.09 dBFS,
  4980706 samples, seam sample difference 0, edge peak head 718 tail 0, renderer v2, soft limiter.
- Seam: `check_seam_v4.py pp_03_harbor_v4b.wav 32` gives loop point sample 4980706 (112.9412 s),
  seam jump 0, last sample of the loop 0, first sample 0, 0 samples of tail beyond the loop point.
  The 10 ms before the loop point measure 0 rms, so the seam is silence into silence by design and
  the loop cannot click.
- Project gates: `check_cues` exit 0 (landed 6, pending 11), `check_dissonance_rules` exit 0 (30
  devices, every rule resolves), `check_drum_patterns` exit 0, `check_music_style_bible` PASS,
  `check_cleanroom` "no study reference, no foreign name, no foreign phrase, every module
  reviewed".
- Dashes: this file, the score and the build script carry no em dash, en dash, figure dash or
  horizontal bar.

## 6. Rounds (the card caps at 4)

1. Baseline on a matched judge: v3, ear 30, hook 100.
2. Round 1: drums rung arcs, the close's two bar hole and its roll, the light section's second
   ninth, wider humanize. Ear 32. Hook 100 unchanged.
3. Round 2: the light section's drum identity (CLM-02, FLT-02) and a lower level for it. Ear 35.
   Kept as the shipping master.
4. Not used: the remaining 5s are tension 5 and drums 5, the ceiling the sweep and the earlier
   harbor card both recorded for a calm cue, and one more device per section would push the
   dissonance budget past what `knowledge/MUSIC-DISSONANCE.md` allows.

## 7. Files

The shipped set: `score_pp03_v4b.yaml`, `build_pp03_v4.py`, `pp_03_harbor_v4b.mid`,
`pp_03_harbor_v4b_humanized.mid`, `pp_03_harbor_v4b.wav`, `pp_03_harbor_v4b.mp3`,
`pp_03_harbor_v4b.ogg`, `pp_03_harbor_v4b_loop.json`, `arrange_report_v4b.json`,
`hook_report_v4b.json`, `hook_report_v4b_humanized.json`, `check_seam_v4.py`, this note.

Round 1, kept for the comparison: `score_pp03_v4.yaml`, `pp_03_harbor_v4.mid`,
`pp_03_harbor_v4_humanized.mid`, `pp_03_harbor_v4.wav`, `pp_03_harbor_v4.mp3`,
`pp_03_harbor_v4_loop.json`, `arrange_report_v4.json`, `hook_report_v4.json`,
`hook_report_render_v4.json`.

The MIDI, WAV, MP3 and OGG are regenerated from the score by one command each and are not committed
by this lane; the ear ledger rows are appended by the ear tool.

## 8. Q: for gamedev

1. **Which build ships, and whether it lands at all.** PP-03 is landed from
   `assets/audio/pp_03_harbor/pp_03_harbor.ogg` (v1, hook 63, ear 27). This pass adds v4b (hook 100,
   ear 35 on `gemini-3.5-flash`, from v3's 30 on the same judge). Pointing the registry row and the
   scene at `pp_03_harbor_v4b.ogg` is a `data/audio.json` and yyp edit, which is yours.
2. **Whether the 113 s loop is the length wanted.** It is half of v2's 225.9 s and it restarts under
   the arrival text twice as often. v3 already asked this; this pass does not change it.
3. **Whether a K, Z or P statement belongs in the harbor cue.** It has never carried one and the
   cue was briefed as its own theme; adding one is one bar of work and a change of identity, so it
   is your call, not a silent edit here.
