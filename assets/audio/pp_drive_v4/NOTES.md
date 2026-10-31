# PP-DRIVE v4: the drive cue's hook, repaired on the three criteria the meter failed

Card AUTO-MUSIC-NEXT (t_6a70f6e8, musician). Clean room: this is the lane's own composition on the
project's own grid; nothing is quoted or transcribed from a published game. Every file here is new.
`assets/audio/pp_drive/` (v1 and v3), `assets/audio/pp_drive_v2/` and the delivered
`pp_drive_v2.ogg` are untouched.

## Why this cue

Scored every registry cue's newest build with `tools/hook_score.py`, and read the newest ear row per
cue from `data/ear_ledger.csv`:

| cue | newest build | hook | ear (six criteria, of 60) |
| --- | --- | --- | --- |
| PP-01 Title | pp_01_title_v8 | 83 | 37 |
| PP-02 Drive | pp_drive (v3 humanized) | 87 | 29 |
| PP-03 Harbor | pp_03_harbor_v3 | 100 | 29 |
| PP-04 Navy Sailors | pp_04_navy_sailors_v3 | 100 | 32 |
| PP-05 Small Ship | pp_05_small_ship_v4 | 91 | 30 |
| PP-06 Percy | percy_theme_v2 | 91 | 31 |
| Boarding | pp_boarding | 90 | 29 |
| Arrival | pp_arrival_v2 | 100 | 31 |
| Fight | pp_fight_v2 | 97 | 31 |

PP-02 is at the floor of the ear ledger (29, tied with PP-03 and boarding) and has the lowest hook
score of that tie (87, against 100 and 90), so it is the weakest cue on the two measures together.
PP-01's 83 comes with the highest ear score in the registry (37), so the ear already says that one
sings. No em dashes, no en dashes, anywhere in this folder.

## What changed, and what it bought

| criterion | v3 | v4 | change |
| --- | --- | --- | --- |
| leaps per motif | 0 leaps, 4.0 of 8 | 1 leap, 8.0 of 8 | the cell now rises C5 D5 E5 then leaps a fourth-and-a-semitone to A5, the peak of the arch |
| steps over leaps | 6 of 7, 12.0 of 12 | 2 of 3 in the detected motif, 12.0 of 12 | still above the 0.65 floor the grammar asks for |
| variation on the third return | 89 percent the same, 3.2 of 8 | 67 percent, 8.0 of 8 | bar 9 is the variant half, which moves the third return to bar 13 where the lead opens on Ki |
| contour | 30 of 37 arch or pedal, 8.11 of 10 | 30 of 36, 8.29 of 10 | unchanged in kind: the segments led by a held note still read as neither |
| loop length | 125 bars, 0 of 6 | 125 bars, 0 of 6 | fixed by the film: 125 bars of 3/4 at 126 bpm is 178.571 s, `data/title_timing.json` |
| **total** | **87** | **92** | |

Loop length is the one criterion v4 does not fix, and it must not be fixed: the cue is cut to the
shot list, and shortening it to 32 bars would break every cut in `NOTES-v3.md`. It costs 6 points on
the meter and nothing at the mix.

## The rest of the card's list, with its evidence

- Leitmotifs K, Z, P and H: the PLAN and LITERAL tables of `tools/drive_v2.py` are unchanged, so K is
  literal in A minor at bars 5, 6 and 74, Ki at 13, Kc in C at 34, Z in C at 26 and 28, P in E minor
  at 60, 61, 64, 65 and 98 and in A minor at 114, 115, H at 17, 18, 38, 39, 94, 95 and 123.
- Drums vary every 4 and 8 bars: `drive_v2.drum_bar` rewrites the noise and dpcm tracks after the
  arrange step, noise 289 to 382 notes, dpcm 66 to 73, with the two bar hole before each seam.
- Dissonance: DIS-02, the chromatic lower neighbour D sharp in the E minor stretches, at the rate
  `knowledge/MUSIC-DISSONANCE.md` allows, and never on the first or last note of a K, Z, P or H
  statement.
- Humanize: `render_chip.py --humanize` wrote `pp_drive_v4_humanized.mid` and rendered from it.
- 126 bpm, 3/4, 125 bars: unchanged from v1, `data/title_timing.json`.
- Chip limits: 8 voices in the arranged MIDI, noise and dpcm hold one pitch at a time, every added
  hit is checked against the arranged notes on the same channel and tick.

## Checks run

- `build_pp_drive_v4.py v4a --render`: exit 0. `hook_report_v4.json`: 92 of 100.
- The meter on the humanized MIDI that actually renders (`pp_drive_v4_humanized.mid`): 85 of 100.
  `humanize.py` moves onsets off the sixteenth grid by up to a frame, which drops motif coverage
  from 62 to 52 percent, so the number the ear hears is lower than the number the arrangement
  scores. v3 measured 87 both before and after its humanize pass; recorded rather than gated.
- `render_chip.py`: 178.550 s, 44.1 kHz, peak -1.00 dBFS, rms -16.42 dBFS, renderer v2, soft
  limiter. `pp_drive_v4.mp3` and `pp_drive_v4.ogg` written beside the WAV.
- Seam (`drive_v2.py seam`): A to A step across the join 178 against a max step inside of 11698
  (0.02), B to B 990 against 15823 (0.06). Both clean.
- Ear loop: NOT run. `tools/ear_critic.py` refuses with "GEMINI_API_KEY is not set in the
  environment" in this worker's shell, and this lane never opens key files or prints a key. The
  four round ear loop the card asks for is therefore unplayed; the improvement above is the meter's
  number, not the ear's.

## To adopt it

`data/audio.json` still points PP-02 at `assets/audio/pp_drive_v2/pp_drive_v2.ogg`, and that file is
not this lane's to edit (R36 owns the row). Adopting v4 is a one line change of `asset` and
`delivered_file` to `pp_drive_v4`, and it also closes the open note there about PP-02 shipping a
pre-humanized render. Q: for gamedev.
