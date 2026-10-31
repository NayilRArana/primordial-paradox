# PP-DRIVE v3, the drive cue: 178 seconds on the shot list's bar grid

Card CUE-DRIVE (t_b84a9264), musician lane, written 2026-10-23. Clean room: the cue is this lane's
own composition on the project's own grid; nothing is quoted or transcribed from a published game.

The music is v2's (`assets/audio/pp_drive_v2/`, hook score 83), because v2 is the cue the slice
already plays. What this card adds is the thing it asks for and v2 never proved: the cut grid, with
a dump that shows every hard cut sitting on a bar line, and the two listening conditions measured
against the sound the project already accepted. v1 stays in this folder untouched; every file below
is new, and none of it rewrites a delivered file.

## 1. The grid

| what | value | source |
| --- | --- | --- |
| tempo | 126 bpm, 3/4 | `data/title_timing.json` `bpm`, `beats_per_bar` |
| steps a bar | 85.714 exact; the shot list snaps to 86, `data/title_timing.json` `bar_steps` is 87 | see the Q below |
| seconds a bar | 1.4286 | 60 / 126 x 3 |
| cue length | 125 bars = 178.571 s | this cue |
| film length | 10,680 steps = 178.00 s | `knowledge/DRIVE-SHOT-LIST.md` section 8 |
| tail past the fade | 0.571 s, less than one bar (1.429 s) | within the card's plus or minus one bar |

## 2. The eleven cuts, each on a downbeat

Printed by `cue_cut_v3.py` from the shot list's own numbers and the arranged MIDI:

```
cut  1  step   688 (11.467 s)  bar   8 downbeat at step 685.7 (11.429 s)  drift +2.29 steps +0.038 s  snaps to the stated bar
cut  2  step  1548 (25.800 s)  bar  18 downbeat at step 1542.9 (25.714 s)  drift +5.15 steps +0.086 s  snaps to the stated bar
cut  3  step  2150 (35.833 s)  bar  25 downbeat at step 2142.8 (35.714 s)  drift +7.15 steps +0.119 s  snaps to the stated bar
cut  4  step  2924 (48.733 s)  bar  34 downbeat at step 2914.3 (48.571 s)  drift +9.72 steps +0.162 s  snaps to the stated bar
cut  5  step  3956 (65.933 s)  bar  46 downbeat at step 3942.8 (65.714 s)  drift +13.16 steps +0.219 s  snaps to the stated bar
cut  6  step  5074 (84.567 s)  bar  59 downbeat at step 5057.1 (84.285 s)  drift +16.87 steps +0.281 s  snaps to the stated bar
cut  7  step  5934 (98.900 s)  bar  69 downbeat at step 5914.3 (98.571 s)  drift +19.73 steps +0.329 s  snaps to the stated bar
cut  8  step  6794 (113.233 s)  bar  79 downbeat at step 6771.4 (112.857 s)  drift +22.59 steps +0.377 s  snaps to the stated bar
cut  9  step  7912 (131.867 s)  bar  92 downbeat at step 7885.7 (131.428 s)  drift +26.31 steps +0.439 s  snaps to the stated bar
cut 10  step  9030 (150.500 s)  bar 105 downbeat at step 9000.0 (149.999 s)  drift +30.03 steps +0.501 s  snaps to the stated bar
cut 11  step  9718 (161.967 s)  bar 113 downbeat at step 9685.7 (161.428 s)  drift +32.32 steps +0.539 s  snaps to the stated bar
```

Every cut rounds to the bar the shot list names, and every one of those bars is attacked on its
downbeat by the arranged cue (lead, bass, a drum hit, or all three; `cue_cut_v3.py` prints the note
count at each). `cut_dump_v3.txt` is the text dump the card asks for: 125 lines, one a bar, with the
cut marker on the downbeat each shot opens on.

## 3. The two listening conditions

`mix_check_v3.py`, A weighted band share of energy, cue against the identity reference
`assets/audio/pp_01_title/pp_01_title.wav`. Absolute shares are meaningless for chip music (a
triangle bass wins raw energy), so the check is against the cue the project already accepted.

| band | cue | reference | delta | why it matters |
| --- | --- | --- | --- | --- |
| 20 to 80 Hz | 0.3 percent | 0.2 percent | +0.1 | nothing a laptop speaker can play either way |
| 80 to 320 Hz | 13.2 percent | 15.1 percent | -1.9 | the engine loop's band, and the cue leaves more of it free than the title cue does |
| 320 to 3000 Hz | 68.6 percent | 71.8 percent | -3.2 | where a laptop speaker actually works; the lead and the hats live here |
| 3000 to 16000 Hz | 17.5 percent | 12.5 percent | +5.0 | hats and noise, the cue's crispness |

- crest 15.29 dB (reference 15.97), so nothing is squashed for a small driver.
- low duty 85.4 percent of 100 ms frames carry near peak engine band energy (reference 83.8), so the
  cue and a car engine loop share a band the way the accepted title cue and it would: the engine sfx
  does not exist yet in `assets/audio/sfx/`, so this is measured against the band, not against a file.
- engine band median: bars 1 to 2 (car at rest) 52.4 dB, bars 3 to 25 (rolling) 50.8 dB, the drum
  hole at 24 to 26 at 52.2 dB. The triangle plays a root on beat one throughout, which is the
  arrangement and not an accident; reported, not gated.
- gated checks: crest, hook share, engine share, low duty. All four pass.

## 4. The rest of the checks, with the numbers

- `tools/arrange.py --self-check`: exit 0, temps 476190 us, sections A 25 / B 34 / A_return 66,
  eight tracks, `out_of_range: []`.
- `tools/render_chip.py`: 178.563 s, 44.1 kHz, peak -1.00 dBFS, rms -15.69 dBFS, renderer v2.
  Humanized: 178.550 s, peak -1.00 dBFS, rms -16.29 dBFS, different MIDI and different bytes.
- `tools/hook_score.py` printed: 83 of 100 (83.31 points), 125 bars, 420 notes, weakest criterion
  loop length at 0 of 6 because a film cue is 125 bars and cannot be 8, 16 or 32.
- `tools/check_cleanroom.py`: exit 0, no blacklist hit. `tools/check_music_style_bible.py`: PASS.
- `tools/check_build_inputs.py`: still red, and this cue adds two rows to it. `.gitignore` takes
  `*.ogg` and `*.mid`, so neither `pp_drive_v3.ogg` nor `pp_drive_v3_humanized.ogg` can be committed
  through `guard/lane_commit.py`, which does not force an ignored path; they show as UNCOMMITTED
  SOURCE, as their mirror rows show as MISSING FROM COMMIT. `pp_05_small_ship_v2.ogg` was already
  red the same way before this card.
- Nothing in this folder is committed. `guard/lane_commit.py` passed the pre-commit gate and then
  its own `git commit` hit its 180 second timeout twice, because the primordial-paradox gate runs
  the project suite, which takes about seven minutes on this host alone. So every file here is on
  disk and untracked, exactly like the pp_arrival and pp_fight folders from the same night. The
  staged copies were cleared from the shared index, so no other lane's commit can carry them.
  Q for gamedev: the guard needs a longer git timeout for this repo (or a cached gate), because a
  card cannot commit through it at all while the suite is that slow.

## 5. Q: for gamedev

- `Q1` (the cut steps drift) The shot list's cut steps are `86 x bar`. The exact bar at 126 bpm is
  85.714 steps, so the eleven cuts run late against the music by 0.038 s at cut 1 and 0.539 s at cut
  11, which is a third of a beat at the end and audible as a late cut. The cue is right and the step
  numbers are the integer snap, so the fix belongs in the scene card: type the corrected steps
  `686, 1543, 2143, 2914, 3943, 5057, 5914, 6771, 7886, 9000, 9686` (printed by `cue_cut_v3.py`),
  or have the runner snap a cut to `round(bar x 85.714)`. This card does not touch
  `data/scenes/all.json`.
- `Q2` (which cue the film plays) `DRIVE-SHOT-LIST.md` section 1 says the drive plays one cue,
  `title_theme`, the A minor waltz. `data/audio.json` PP-02 is this cue, and PP-01 is the waltz.
  Both are 126 bpm 3/4 on the same grid, so either answer works musically; the shot list's `Q2`
  makes the settlement this lane's, and this lane's answer is: keep PP-02 as the drive cue (it is
  the one the slice already plays), and treat the waltz as the title card's. Gamedev confirms.
- `Q3` (the humanized master) `data/audio.json` notes that no OGG of the humanized master exists, so
  PP-02 ships the pre-humanized render. `pp_drive_v3_humanized.ogg` is that file, rendered here. If
  gamedev wants it shipped, the audio row points at it; this card does not write `data/audio.json`.
- `Q4` (tracker) The project has no tracker module (no `.ftm` or `.dnm` anywhere in the repo), so the
  text dump `cut_dump_v3.txt` is the tracker shaped artefact the check asks for. If a real module is
  wanted, that is a new card and a new deliverable format.

## 6. Files

| File | What |
| --- | --- |
| `score_pp_drive_v3.yaml` | the score, v2's music with this card's header and grid notes |
| `pp_drive_v3.mid` | arranged MIDI, eight chip voices, drums rewritten by `tools/drive_v2.py` |
| `pp_drive_v3.wav` / `.mp3` / `.ogg` | render, 178.563 s, 44.1 kHz |
| `pp_drive_v3_humanized.wav` / `.mp3` / `.ogg` | humanized render, 178.550 s |
| `pp_drive_v3_loop.json`, `pp_drive_v3_humanized_loop.json` | loop and voice maps from the renderer |
| `arrange_report_v3.json` | arranger self check |
| `hook_report_v3.json` | the hook grammar reading, 83 of 100 |
| `cue_map_v3.json` | the shot to cue bar map with the drift of every cut |
| `cut_dump_v3.txt` | the tracker shaped dump, 125 bars, cut markers on the downbeats |
| `cue_cut_v3.py` | how the map, the drift and the dump are computed and checked |
| `mix_check_v3.py`, `mix_check_v3.json` | the laptop and engine measurements in section 3 |

Not done, by scope: `data/audio.json`, the scenes, the art, the engine, and no upload or publish.
