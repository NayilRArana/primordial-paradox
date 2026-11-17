# PP-06 "Percy, Possessed", take F (`pp_06_percy_possessed_v6`): the first heard take on disk

Card `t_f6b21e0b` (AUTO-MUSIC-NEXT, musician lane), 2026-11-16, node CitadelArana. Clean room:
the scored MIDI in this folder is take E's file byte for byte (`pp_06_percy_possessed_v5.mid`,
sha256 `29d18bafe1be45d27a42637359eade31a1e96dbad36465bd5585e0a4175da4bd`), and every earlier
take, `data/audio.json` and `data/ear_ledger.csv` are untouched.

## 1. The pick, measured

Every `.mid` under `assets/audio/` was scored in this session with `tools/hook_score.py`: 163
files, 20 cue families; the newest take per family, plain and the humanized sibling where one
exists.

| cue | newest take | plain | heard | weakest criterion |
| --- | --- | --- | --- | --- |
| PP-02 pp_drive | pp_drive_v7 | **93** | none | loop length 0.0 of 6 (125 bar film grid), contour 8.9 of 10 |
| PP-01 title | pp_01_title_v13 | 100 | 99 | contour 9.23 of 10 |
| PP-04 navy | pp_04_navy_sailors_v3 | 100 | 99 | contour 9.0 of 10 |
| PP-04b fight | pp_04_fight_baroque_v11 | 100 | 100 | full |
| PP-03 quay storm | pp_03_quay_storm_v4 | 100 | none | full |
| PP-05 small ship | pp_05_small_ship_v7 | 100 | none | full |
| **PP-06 percy** | **pp_06_percy_possessed_v5** | **100** | **none** | **full, but no heard take exists** |
| PP-15a, PP-15b, PP-17, PP-18, pp_arrival | newest take | 100 | 100 where present | full |

PP-02 is the lowest number on the board and it stayed out of scope for a measured reason, checked
again today instead of copied: the meter itself says `125 bars does not loop cleanly; write 8, 16
or 32 bars`, the 125 bars are the film grid in `data/title_timing.json`, and
`knowledge/PP-02-CEILING-2026-11-14.md` records three repairs that each bought the contour point
by spending 7 to 8 points of motif coverage. That is a gamedev film-grid decision, not a take.

The gap this card closed is on PP-06, the boss cue: take E scores 100 plain and there is no
humanized variant of it on disk, so the family has no heard candidate at all. The ear review of
v3 (`assets/audio/ear_reviews/pp_06_percy_possessed_v3_20261112T014147Z.md`) scored the cue
hook 7, drums 5, tension 5, **human 4**, variety 7, structure 6, and its second concrete change
asks for note length and envelope variation; `tools/humanize.py` is exactly that pass and take E
never ran it.

## 2. Score table, before and after

`tools/hook_score.py`, melody track `vrc6 pulse a`, same grammar (`knowledge/MUSIC-HOOK-GRAMMAR.md`).

| file | bars | hook |
| --- | --- | --- |
| pp_06_percy_possessed.mid (shipped stream, hook 52) | 48 | 52 |
| pp_06_percy_possessed_v2.mid | 48 | 66 |
| pp_06_percy_possessed_v3.mid | 48 | 88 |
| pp_06_percy_possessed_v4.mid (take D) | 32 | 96 |
| pp_06_percy_possessed_v5.mid (take E) | 32 | 100 |
| **pp_06_percy_possessed_v6.mid (take F plain)** | **32** | **100** |
| **pp_06_percy_possessed_v6_humanized.mid (take F heard)** | **32** | **100** |

Per criterion, take F heard against take E plain:

| criterion | weight | take E plain | take F heard |
| --- | --- | --- | --- |
| motif coverage | 20 | 20.0 (74% of 156) | 20.0 (70% of 159) |
| motif returns | 12 | 12.0 (12) | 12.0 (11) |
| hook cell | 10 | 10.0 (5 notes 2/2/2/2/4, 30x) | 10.0 (6 notes 2/2/2/2/3/2, 6x) |
| steps over leaps | 12 | 12.0 (78% of 9, 1 leap) | 12.0 (67% of 9, 1 leap) |
| leaps per motif | 8 | 8.0 (1) | 8.0 (1) |
| contour | 10 | 10.0 (12 of 12 pedal) | 10.0 (11 of 11 pedal) |
| variation on the third return | 8 | 8.0 (80%) | 8.0 (55%) |
| range | 8 | 8.0 (8 semitones) | 8.0 (8 semitones, 67 to 75) |
| repeated pitch | 6 | 6.0 (22) | 6.0 (21) |
| loop length | 6 | 6.0 (32 bars) | 6.0 (32 bars) |
| **total** | **100** | **100** | **100** |

Take F does not claim a new hook point over take E; the meter is already full on this score and
the plain MIDI here is take E byte for byte. What the card gains is the heard file, which did not
exist.

## 3. The humanize pass, and what it wrote

`tools/humanize.py --onset-frames 1 --ornament-note second`, seed 20261021, 150 bpm, 20.00 ticks
per frame, 1080 notes in and 1091 out:

- articulation: 481 of 1080 notes changed length (44.5%), one left under the 85% floor by the
  frame grid; noise and dpcm (the drums) untouched, pulse 1 187 of 187, melody 108 of 159.
- envelopes 1224 points, vibrato on 1 melody note, 16 breaths, 1 grace note, 1 mordent.
- fills: 8, before the section changes at bars 9, 17, 25 and 33, on the cue's own 8 bar period;
  with the 4 bar rung take E already carries that is the "drums vary every 4 and 8 bars" line.
- ornament on the second note: the placement take E and take D both measured as the one that
  does not move the motif the meter reads.

## 4. The cue gate, both files

`tools/counterpoint/cue_gate.py`, run in this session:

| file | state | strong-beat raw clashes | parallel perfect intervals | M1a |
| --- | --- | --- | --- | --- |
| take F plain (= take E) | **PASS** | 0 | 0 | FAIL (hard 71, soft 6, style 26), 564 notes |
| take F heard | **PASS** | 0 | 0 | FAIL (hard 77, soft 11, style 25), 575 notes |

## 5. Render, seam and delivery

`tools/render_chip.py` on the heard MIDI, v2 voices, `--loop-bars 32`, 150.0 bpm, 3/4, 38.400 s:
peak -1.00 dBFS, RMS -15.46 dBFS before master.

Loop seam from `pp_06_percy_possessed_v6_loop.json`:

| field | value |
| --- | --- |
| loop_bars | 32 |
| loop_start_sample / loop_end_sample | 0 / 1693440 |
| loop_seam_sample_difference | **0** |
| loop_edge_peak_head / tail | 705 / 41 (of 32768) |
| loop_edge_max_jump | 103 |
| fade | 5.0 ms raised cosine, 220 samples |

Master (`limit_master_v6.py`, fixed gain plus a look-ahead limiter at a -2.6 dBFS limit):
gain walked 2.50 dB (-14.60 LUFS, -1.59 dBTP) then **3.10 dB, which lands -14.11 LUFS and
-1.52 dBTP** on the delivered OGG, next to take E's PP-15b delivery at -14.13 LUFS.

## 6. Files

| path | bytes | what |
| --- | --- | --- |
| assets/audio/pp_06_percy_possessed_v6/pp_06_percy_possessed_v6.ogg | 504694 | the delivered stream, from the master |
| assets/audio/pp_06_percy_possessed_v6/pp_06_percy_possessed_v6.mp3 | 505052 | codec sibling |
| assets/audio/pp_06_percy_possessed_v6/pp_06_percy_possessed_v6_master.wav | 3686478 | -14.11 LUFS mono master |
| assets/audio/pp_06_percy_possessed_v6/pp_06_percy_possessed_v6.wav | 3386924 | the render before master |
| assets/audio/pp_06_percy_possessed_v6/pp_06_percy_possessed_v6.mid | 9862 | take E byte for byte, hook 100 |
| assets/audio/pp_06_percy_possessed_v6/pp_06_percy_possessed_v6_humanized.mid | 15819 | the heard take, hook 100, gate PASS |
| assets/audio/pp_06_percy_possessed_v6/pp_06_percy_possessed_v6_loop.json | 1704 | loop points and seam |
| assets/audio/pp_06_percy_possessed_v6/build_report_v6.json | 2889 | the numbers in one file |
| assets/audio/pp_06_percy_possessed_v6/hook_report_v6.json, hook_report_v6_humanized.json, hook_report_v6_render.json | 3796, 3791, 3791 | the three score grids |
| assets/audio/pp_06_percy_possessed_v6/humanize_report_v6.json | 2334 | the humanize pass |
| assets/audio/pp_06_percy_possessed_v6/master_report_v6.json | 318 | the master walk |
| assets/audio/pp_06_percy_possessed_v6/gate_plain_v6.log, gate_heard_v6.log | 447, 458 | both gate runs |
| assets/audio/pp_06_percy_possessed_v6/limit_master_v6.py | 2626 | the master pass |
| assets/audio/pp_06_percy_possessed_v5/ and earlier | untouched | take E and every take before it |

The heard MIDI hashes to
`878ecdac259034701afc5880c7b9d99efc367e5e2bb96af684ad0a0db42a5ed3` and the delivered OGG to
`d55d7d72cdd413611cd45a914820b552ea52d0c0ad9d448a9d91c585a151d0c0`.

Tests: `python -m pytest tests/test_hook_score.py tests/test_music_coverage.py -q` -> 19 passed.

## 7. The ear loop did not run, again

`python tools/ear_critic.py --dry-run assets/audio/pp_06_percy_possessed_v6/pp_06_percy_possessed_v6.ogg`
prints `key:     absent from GEMINI_API_KEY, a real run would refuse`. `GEMINI_API_KEY`,
`GOOGLE_API_KEY` and `GOOGLE_GENAI_API_KEY` are all unset in this session's environment (checked
through `os.environ`, no file opened, nothing printed). This is the fifth card on this wall
(t_50cbadb5, t_5b93b0cc, t_71c5dea2, t_e2731314), so the four rounds went to the deterministic
meter, the cue gate and the tests, and no model rotation was possible or needed.

## 8. Not this card's call

- `data/audio.json` was not touched: PP-06 still names `pp_06_percy_possessed.ogg`, the 52 point
  render, while takes D, E and F sit on disk. Adoption is the gamedev head's row to change, and
  the measured size of that gap (52 against 100 on the same meter) is the largest music
  improvement left in the project. Q: for gamedev.
- Whether the heard take is better by ear than take E's plain score. The meter ties them at 100
  and the gate passes both; the ear critic could not argue either side.
- The 150 bpm, E minor, 3/4, 32 bars and the chord plan stay as registered in `specs/12-audio.md`.
- No `sync_art` or `gen_project` was run, so the OGG is on disk and not an Included File.
