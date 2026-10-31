# PP-FIGHT v2 "the battle cue": the weakest cue rebuilt for the hook meter and the ear

Card AUTO-MUSIC-NEXT (t_47a92d70), 2026-10-24. Owner: musician. v1 in `assets/audio/pp_fight/` is
untouched; every file in this folder carries `_v2`.

## 1. The pick, and the score table before it

`tools/hook_score.py` reads the melody track of a MIDI file. `data/audio.json` lands six cues and
the audio tree holds four more cue folders built by their own cards (fight, boarding, arrival,
Hadrian), so a cue has to be scored on every state it plays, not on the file that happened to be
measured last. Measured in this session, newest build of each, melody track `vrc6 pulse a`:

| cue | newest build | hook score |
| --- | --- | --- |
| PP-04 fight, FIGHT state | `pp_fight/pp_fight_fight.mid` | 84 |
| PP-04 fight, CALM state | `pp_fight/pp_fight_calm.mid` | **67** |
| PP-04 fight, both states in one file | `pp_fight/pp_fight_states.mid` | 79 |
| PP-01 title | `pp_01_title_v6` | 83 |
| PP-02 drive | `pp_drive_v2` | 83 |
| PP-08 boarding | `pp_boarding` | 90 |
| PP-05 small ship | `pp_05_small_ship_v4` | 91 |
| PP-06 Percy | `percy_theme_v2` | 91 |
| Hadrian, the data centre | `hadrian_theme` | 81 |
| PP-03 harbor | `pp_03_harbor_v3` | 100 |
| PP-04 navy sailors | `pp_04_navy_sailors_v3` | 100 |
| PP-07 arrival (rebuilt 3 hours ago) | `pp_arrival_v2` | 100 |

The floor of the whole set is the FIGHT cue's CALM state at 67, and the FIGHT state sits at 84 with
three measured failures. Title (83) and drive (83) were passed over by the previous round for the
reason it gave and it still holds: title is pinned to `data/title_timing.json` and drive to a 125
bar film loop on its shot list, so neither can change its length. Boarding (90) is a one shot cue
with no loop, so its loop length row is not a real failure. Hadrian (81) is a theme at 92 bpm with
no state pair. The fight cue is a two state pair that plays every time the player touches a battle,
so it is both the lowest measured cue and the one heard most.

## 2. Hook meter, before and after

`python tools/hook_score.py pp_fight_v2_fight.mid` and the same command on the v1 file, then the
calm pair:

| criterion | v1 fight | v2 fight | v1 calm | v2 calm |
| --- | --- | --- | --- | --- |
| motif coverage | 12.3 of 20 (37 percent) | 20 of 20 (78 percent) | 11.4 of 20 (34 percent) | 20 of 20 (74 percent) |
| motif returns | 12 of 12 (3) | 12 of 12 (6) | 8 of 12 (2) | 12 of 12 (5) |
| leaps per motif | 4 of 8 (0 leaps) | 8 of 8 (1) | 8 of 8 (1) | 8 of 8 (1) |
| steps over leaps | 12 of 12 (88 percent) | 12 of 12 (83 percent) | 9.2 of 12 (50 percent) | 12 of 12 (71 percent) |
| contour | 10 of 10 | 10 of 10 | 0 of 10 (0 of 2 returns) | 10 of 10 (5 of 5) |
| variation on the third return | 3.2 of 8 (100 percent the same) | 8 of 8 (77 percent) | 0 of 8 (no third return) | 8 of 8 (62 percent) |
| range | 8 of 8 (15 semitones) | 8 of 8 (17) | 8 of 8 (10) | 8 of 8 (10) |
| loop length | 6 of 6 (16 bars) | 6 of 6 (16 bars) | 6 of 6 (16 bars) | 6 of 6 (16 bars) |
| **total** | **84** | **100** | **67** | **100** |

What changed, and nothing else:

1. The hook is now a two bar arch, 13 notes: A4 up a fifth to D5, stepwise to A5, one turn, then a
   walk down to G4. v1's cell was two bars of nine notes whose third return was an exact copy and
   whose leap sat outside the window the scorer measures. The new cell carries its leap inside
   (A4 to D5), has one turn, and is 83 percent steps.
2. It is stated six times in the 16 bars with three notes changed in every alternate statement, so
   the third return reads at 77 percent the same: a return, not a copy.
3. Bars 9 and 10 transpose the arch up a fourth into G minor and then Eb. Those two bars are the
   only material the metre does not count as the motif, which is why coverage stops at 78 and not
   higher.
4. The calm state is the same arch at half values, eight notes a statement, five statements plus a
   four bar answer and the leading tone. v1's calm had no contour on any return and two returns.

## 3. The ear, four rounds, and what it says about itself

Every round used `tools/ear_critic.py` through the rotation in `tools/ear_loop.py` (lite, then
flash, then 3.7, then 3.8 on a quota error, a 429 or a 503). The first model answered every call,
so no round switched models; the key came from `HKCU\Environment` and was never printed. v1 was
scored in the same session on the same model so the columns are comparable.

| file | v1 | round 1 | round 2 | round 3 | round 4 |
| --- | --- | --- | --- | --- | --- |
| fight | 33 | 29 | 30 | 30 | **32** |
| calm | 27 | 30 | 32 | 31 | **30** |

Fight, criterion by criterion, v1 then round 4: hook 7 then 7, drums 5 then 4, tension 4 then 6,
human 3 then 3, variety 8 then 7, structure 6 then 5. Calm: 6 then 7, 3 then 4, 4 then 5, 2 then
3, 7 then 6, 5 then 5.

What each round changed, in the order it was changed:

- **Round 1** scored the first build. The ear's complaints: drums rigid, no human feel, tension
  only from speed, contrast only from adding channels.
- **Round 2** answered the drums and the human feel: a four bar velocity arc (0.88, 0.94, 1.04,
  1.10) under the kit, four ghost notes on off sixteenths, bar 13 moved to BAT-03 (its snare roll
  turns the loop around), the counterline extended back to bar 5 so the opening four bars are
  thinner, a chromatic passing tone in the counter at bars 6 and 14 (device DIS-01 of
  knowledge/MUSIC-DISSONANCE.md: an eighth on a weak beat between two chord tones a tone apart,
  resolving up a semitone; the lead never carries it, which is rule F1), and vibrato depth and
  onset written per phrase (46/1, 34/2, 52/1, 40/3) instead of one fixed setting.
- **Round 3** answered the timbre and structure note: the noise period moves with the phrase (0,
  +1, -1, +2) so the backbeat is a different colour in each quarter, and bars 9 and 10 drop the
  pad, the arpeggio and the counterline, which makes the pad's return at bar 11 hearable.
- **Round 4** fixed three chip limits inherited from v1 (below) and that was the last round the
  card allows.

The honest reading of that table: the ear does not track these changes. The calm file was byte
identical in rounds 1 and 2 and scored 30 then 32; the same file in round 3 fell back to 31. Two
points is its noise floor on this material, and its "human feel 3" is the score it gives every cue
in this project (harbor, navy sailors, Percy, arrival and this one all sit at 3 on the same model).
The fight ends one point under v1 and the calm three points over it.

## 4. Chip limits v1 was over, found while checking ranges

`tools/arrange.py` declares `VOICE_RANGES` and those are the numbers the project enforces. v1 broke
three of them, and v2 does not:

| voice | declared range | v1 reached | v2 |
| --- | --- | --- | --- |
| pulse 1 | 60 to 79 | 51 (the Eb, Bb and Gm arpeggios, and A7's C) | 62 to 77, each arpeggio shape transposed up an octave as a whole when its lowest note was under 60 |
| triangle | 36 to 55 | 69 (the ostinato played root and fifth an octave up, with an octave note on top) | 38 to 55, written where the voice lives with the octave note capped at 55 |
| noise | 1 to 15 | 16 (period 15 hits, and the ghost notes) | 1 to 15, capped |

The check re-reads `VOICE_RANGES` out of `tools/arrange.py` instead of copying it, so the two files
cannot drift apart.

## 5. Checks

`python check_pp_fight_v2.py` prints 26 rows and all 26 pass; the full run is in
`check_output.txt`. It covers: three render sets present (WAV, MIDI, MP3, OGG), both loop files at
1,008,000 samples with seam sample difference 0, 16 and 32 bars as whole 4 bar phrases, the drum
ladder changing at every 4 bar line and again at every 8 bar line, the fight's bar 16 equal to the
calm's bar 1 on the lead and the triangle, the same equality inside the states render at bar 17 on
all five pitch voices with only the kit changing, both hook reports at 100 of 100, every voice
inside its declared range, and no long dashes.

`python tools/ear_critic.py` wrote ten reviews today for this cue (four v2 fight, four v2 calm, two
v1 as the baseline, one call each); every row is in `data/ear_ledger.csv` with its model.

## 6. Left open, for the head of the project, not for me

1. **Q: for gamedev, wiring.** v2 is a new folder and `data/audio.json` is gamedev's file, so the
   PP-04 fight row still points at `pp_fight/pp_fight_fight.ogg`. Nothing landed underneath the bus.
   Which state the director cuts between, and whether the fight row's asset becomes `pp_fight_v2`,
   is the same call v1 left open, and it is still open.
2. **Tempo.** This card's brief says "126 bpm family". The cue's own card (CUE-FIGHT) fixes 168 bpm
   for both states so that the last bar of one is the first bar of the other, tick for tick. The
   chain of command puts gamedev's specs above this card's line, so v2 stays at 168 and the 126
   family was not applied. Say the word and a 126 variant is a tempo constant plus the two
   render calls, but it breaks the tick for tick seam that lets the states be cut on any bar.
3. **The trade the two meters disagree about, and the one thing only Nayil's ear can settle.** The
   hook meter wants one cell heard six times; the ear scored v1's fight two points higher on
   variety and drums, because v1's second half was new melodic material. v2 is built so the variety
   lives under the hook (breaks, timbre, drum rungs, counterline) instead of in new melody. If the
   fight state now reads as too static to him, the fix that keeps the hook metre is to vary the
   second half's instrumentation further, not to write a second melody.

## Files here

| file | what it is |
| --- | --- |
| `build_pp_fight_v2.py` | writes all three MIDI files from note lists written in the file |
| `check_pp_fight_v2.py` | the 26 checks, one table, exit 1 on any failure |
| `check_output.txt` | the last full run of the check |
| `pp_fight_v2_fight.mid` / `.wav` / `.mp3` / `.ogg` | state A, the FIGHT loop, 16 bars, 22.86 s |
| `pp_fight_v2_calm.mid` / `.wav` / `.mp3` / `.ogg` | state B, the TALK loop, 16 bars |
| `pp_fight_v2_states.mid` / `.wav` / `.mp3` / `.ogg` | both states end to end so the junction can be heard |
| `pp_fight_v2_fight_loop.json`, `pp_fight_v2_calm_loop.json` | the loop points the OGGs loop on |
| `hook_report_fight_v2.json`, `hook_report_calm_v2.json` | the hook meter, 100 of 100 each |
| `build_report_v2.json` | the builder's own numbers: bars, seconds, notes, voices, humanizing |
| `ear_round_1.json` to `ear_round_4.json` | the models asked per round, and the key source, never the key |
| `ear_round_1_v1_baseline.json` | the v1 baseline rows |

## How to rebuild

```
cd assets/audio/pp_fight_v2
python build_pp_fight_v2.py
python ../../../tools/render_chip.py pp_fight_v2_fight.mid pp_fight_v2_fight.wav --loop-bars 16 --hook-report hook_report_fight_v2.json
python ../../../tools/render_chip.py pp_fight_v2_calm.mid  pp_fight_v2_calm.wav  --loop-bars 16 --hook-report hook_report_calm_v2.json
python ../../../tools/render_chip.py pp_fight_v2_states.mid pp_fight_v2_states.wav
ffmpeg -y -i pp_fight_v2_fight.wav -c:a libvorbis -q:a 5 pp_fight_v2_fight.ogg   (and the other two)
python check_pp_fight_v2.py
```

## Lessons for the next AUTO-MUSIC-NEXT round

- `find_motif` in `tools/hook_score.py` scores the 1 bar and the 2 bar window and keeps the one
  with the most coverage, so a cell that arches over one bar inside a two bar phrase loses the
  contour row: the two bar window wins coverage and carries two turns. Write the arch across the
  whole cell, at the width the metre will pick.
- Coverage counts bar aligned windows, so a transposed sequence (up a fourth) is not a return. Aim
  for the transposed bars to be the only uncovered notes, and count them before scoring.
- The third return is `occurrences[0]` against `occurrences[2]`, not "the third statement" and not
  the last one. With a 14 note window one note changed reads 93 percent, which is a copy, and the
  point is lost; three notes changed reads 79, which passes. With an 8 note window one change (80
  percent) passes.
- The ear saturates. Score the same file twice before believing a one or two point move, and score
  the previous version in the same session on the same model or the two columns are not comparable.
