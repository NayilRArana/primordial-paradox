# PP-BOARDING v2: the weakest cue on the ear and the hook meter, repaired

Card AUTO-MUSIC-NEXT (t_5424b71f, musician). Clean room: this is the lane's own revision of the
project's own cue, composed on the project's own grid; nothing is quoted or transcribed from a
published game. `assets/audio/pp_boarding/` (v1 and its render) is untouched; every file here is new.

## Why this cue

Every registry cue's newest build was scored with `tools/hook_score.py`, and the newest ear row per
cue was read from `data/ear_ledger.csv` (six criteria, of 60):

| cue | newest build | hook | ear (of 60) |
| --- | --- | --- | --- |
| PP-01 Title | pp_01_title_v8 | 83 | 37 |
| PP-02 Drive | pp_drive_v4 | 92 | 29 (v3 humanized row; v4 not yet heard) |
| PP-03 Harbor | pp_03_harbor_v3 | 100 | 29 |
| PP-04 Navy Sailors | pp_04_navy_sailors_v3 | 100 | 32 |
| PP-05 Small Ship | pp_05_small_ship_v4 | 91 | 30 |
| PP-06 Percy | percy_theme_v2 | 91 | 31 |
| Boarding | pp_boarding | 90 | 29 |
| Arrival | pp_arrival_v2 | 100 | no ear row |
| Fight | pp_fight_v2 | 100 | 30 to 31 |

Boarding sits on the floor of the ear ledger (29, tied with PP-03 and PP-02) and has the lowest hook
score of that tie (90, against 100 and 92), so it is the weakest cue on the two measures together.
PP-01's 83 is the lowest hook number in the registry, but its ear row is the highest (37), so the ear
already says that one sings.

## The score table, before and after

| measure | v1 | v2 (on the grid) | v2 (humanized render) |
| --- | --- | --- | --- |
| hook_score | 90 | **100** | 93 |
| ear total (six criteria, of 60) | 29 | 30 | **31** |
| ear hook / drums / tension / human / variety / structure | 6 4 5 3 6 5 | 7 5 4 3 6 5 | 7 4 5 3 6 6 |
| ear model | gemini-3.5-flash-lite | gemini-3.5-flash-lite | gemini-3.5-flash-lite |

The meter falls back to 93 on the humanized MIDI because `humanize.py` moves onsets off the
sixteenth grid, which pulls motif coverage from 64 to 50 percent; that is the same 7 point effect
`pp_drive_v4` recorded. The ear hears the humanized render 1 point higher, so the recommendation is
the humanized render (`pp_boarding_v2_humanized.mp3`) as the shipping master, with the on-grid
`pp_boarding_v2.ogg` kept as the mechanically exact alternative.

## What changed, criterion by criterion

| criterion | v1 | v2 | how |
| --- | --- | --- | --- |
| loop length | 0 of 6 (melody ended in bar 14) | 6 of 6 (16 bars) | the lead joins the stop: bar 16's stab is now the lead's A4 held two beats, so the melody track ends inside the last bar |
| motif coverage | 15.9 of 20 (48 percent) | 20 of 20 (64 percent) | bars 7 and 8 are now a fourth statement of the hook (head then answer) instead of the varied head and the deck arrival figure |
| motif returns | 3 | 4 | the same change |
| the other eight criteria | all passing | all passing | untouched: one leap per motif, 90 percent steps, four arches, 73 percent third return variation, range 17 semitones, 12 repeated pitches, 6 note cell with the 2/2/2/2/4/4 rhythm |

Nothing else moved: same 120 bpm, same 4/4, same 16 bars, same 32.000 s, same chords, same drums,
same held breath in bars 13 to 15, same two beats of air after the stop.

## The rest of the card's list, with its evidence

- Leitmotifs K, Z, P and H: not present, and not added. This cue carries its own hook by the design of
  card CUE-BOARDING (t_8158e5f9); the K, Z, P and H statements live in the title and drive cues
  (`tools/drive_v2.py` PLAN and LITERAL tables). Inserting a K statement into the deck would change
  the cue's identity and its clean room result, so it is left as the Q at the bottom of this file.
- Drums vary every 4 and 8 bars: `DRUMS` in the build script still assigns one library bar per bar,
  with the 4 bar cadence at bars 4, 8, 12 (FLF-01 fill, FLF-01 fill, FLT-01 tom sweep) and the rung 5
  tutti with the crash once, at bar 9; the run of rungs never puts two rung 3 bars next to each other.
- Dissonance: unchanged, and the cue's one note outside A minor is still the Bb4 in the bar 10 answer,
  which lands in G minor. `knowledge/MUSIC-DISSONANCE.md` rule F1 is not touched: the chromatic note
  is inside the phrase, never the first or last note of a motif statement.
- Humanize: `render_chip.py --humanize` wrote `pp_boarding_v2_humanized_humanized.mid` and rendered
  from it: 391 of 418 notes changed length, 6 melody notes vibrato, 609 envelope points, 7 breaths,
  1 grace note, 1 mordent, 8 fills before the section change at bar 17.
- 126 bpm family: this cue is 120 bpm on purpose. 16 bars at 120 in 4/4 is 32.000 s, which is exactly
  the 1920 step gangway beat of card t_a3fa132a; 126 bpm would put the same 16 bars at 30.476 s and
  break the scene's authored length. Recorded rather than changed.
- Chip limits: 8 voices written (2 pulse, 2 VRC6 pulse, VRC6 saw, triangle, noise, dpcm), 418 notes,
  noise and dpcm hold one pitch at a time, and no added note doubles another on the same channel and
  tick.

## Checks run

- `python build_pp_boarding_v2.py`: 16 bars, 32.000 s, 418 notes, 8 voices.
- `python ../../../tools/hook_score.py pp_boarding_v2.mid --json hook_report_v2.json`: 100 of 100.
  On the humanized MIDI: 93 of 100 (`hook_report_v2_humanized.json`).
- `render_chip.py`: 32.000 s, peak minus 1.00 dBFS, rms minus 14.72 dBFS (minus 15.10 humanized),
  renderer v2, soft limiter.
- Seam: this cue is a one shot, so there is no loop point to close; the renderer reports seam sample
  difference 0 for the 16 bar trim, an edge peak of 1050 at the head and 0 at the tail, and the last
  second measures minus 120 dBFS, so the file can end anywhere in the last beat and nothing is cut.
- `python check_pp_boarding_v2.py`: all checks passed, 9 sections, including the hook score, the held
  breath, the stop, the clean room (113 references, highest 5-gram Jaccard 0.0000, longest identical
  interval run 7) and 0 long dashes. The clean room compares against every other cue, and the
  guard's own lineage rule (`tools/melody_guard.py`, `cue_lineage`) skips this cue's revisions,
  `pp_boarding` and `pp_boarding_v3` and their humanized renders, because a revision necessarily
  shares its melody with the version it revises; against the predecessor it scores 0.5714 Jaccard
  and a 32 note identical run, which is the point of a revision. Before that rule existed the folder
  passed a hand-filtered folder list to the guard instead.
- Ear loop, round 1: `pp_boarding_v2.mp3` scored 30 of 60 on `gemini-3.5-flash-lite`
  (`assets/audio/ear_reviews/pp_boarding_v2_20261024T232006Z.md`).
- Ear loop, round 2: `pp_boarding_v2_humanized.mp3` scored 31 of 60 on the same model
  (`assets/audio/ear_reviews/pp_boarding_v2_humanized_20261024T232031Z.md`).
- The loop stopped at two rounds rather than four because the card's 45 minute budget put the
  remaining time into the checks and this file; both rounds scored the same model, so the two ear
  rows are comparable, and the rotation was exercised in code (a quota failure on one model falls
  through to the next, `tools/ear_loop.py --self-check` proves it offline).

## To adopt it

`data/audio.json` has no boarding row to change: the gangway cue is not a registry cue, so adopting
v2 means pointing the boarding scene's music at
`assets/audio/pp_boarding_v2/pp_boarding_v2_humanized.mp3` in the scene data and in whatever the bus
calls. That file is not this lane's to edit. Q below.

## Q for gamedev (this card does not decide it)

1. **Which render ships.** The humanized render scores higher with the ear (31 against 30) and lower
   on the meter (93 against 100). This lane recommends the humanized render; the choice is gamedev's.
2. **A leitmotif, or not.** The card asks for K, Z, P and H to be clear, and this cue has never
   carried one: it was briefed as its own gangway theme. Adding a K statement to the deck is one bar
   of work and changes the cue's identity, so it is gamedev's call, not this lane's.
3. **The scene row.** Priced by the specs the row is 539 steps (366 from the commands and a 173 step
   `say` floor), 8.983 s, against the 1920 step beat this cue is cut to. Gamedev ruled in
   `knowledge/GAMEDEV-DECISIONS-2026-10-26.md` amendment D1a: the row is not padded, because the two
   measure different clocks (the `say` is player paced), and the cue hands back to PP-05 with spec 12
   rule 4's 30 step crossfade. Closed.
