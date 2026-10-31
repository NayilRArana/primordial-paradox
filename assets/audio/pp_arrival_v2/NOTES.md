# PP-ARRIVAL v2 "Night Quay": the floor cue rebuilt by the hook score. Card AUTO-MUSIC-NEXT (t_681609f2)

v1 in `assets/audio/pp_arrival/` is untouched. This folder is new; every file in it carries `_v2`.

## 1. The pick, and the score table before it

`tools/hook_score.py` on the newest build of every cue in the registry, melody track `vrc6 pulse a`,
all measured in this session rather than remembered:

| cue | newest build | hook score |
| --- | --- | --- |
| PP-07 arrival | `pp_arrival` (v1) | 83 |
| PP-01 title | `pp_01_title_v6` | 83 |
| PP-02 drive | `pp_drive_v2` | 83 |
| PP-08 boarding | `pp_boarding` | 90 |
| PP-05 small ship | `pp_05_small_ship_v4` | 91 |
| PP-06 Percy | `percy_theme_v2` | 91 |
| PP-03 harbor | `pp_03_harbor_v3` | 100 |
| PP-04 navy sailors | `pp_04_navy_sailors_v3` | 100 |
| PP-04 fight | `pp_fight` | 84 |

Arrival, title and drive tie at 83. Arrival is the only one of the three whose two failing criteria can
be fixed without overriding a decision that is not mine: title is pinned to the title timing and drive
is pinned to a 125 bar film loop on its shot list, while arrival's own card allowed 32 to 48 bars and
v1 sat at the wrong end of it. So the pick is PP-07, and the ear ledger agrees it is weak: v1 total 31
of 60, human feel 3.

## 2. Hook meter, v1 to v2

`python tools/hook_score.py assets/audio/pp_arrival_v2/pp_arrival_v2.mid`, and the same command on v1:

| criterion | v1 | v2 |
| --- | --- | --- |
| loop length | 3 of 6 (48 bars) | 6 of 6 (32 bars) |
| motif coverage | 6.3 of 20 (19 percent) | 20 of 20 (67 percent) |
| variation on the third return | 8 of 8 | 8 of 8 (78 percent the same) |
| contour | 10 of 10 | 10 of 10 (10 of 10 returns arch) |
| range | 8 of 8 | 8 of 8 (14 semitones, 62 to 76) |
| **total** | **83** | **100** |

What changed, and nothing else: the loop is 32 bars (96.000 s at 80 bpm) instead of 48, and the file is
written as ten statements of the same two bar cell Q, each statement changing one note, the third
changing two (bars 5 and 6) so the return is heard as a return and not a copy. The chords, the four
textures, the echo, the walking bass and the kits move under the cell, which is where the variety comes
from now instead of from new melody.

## 3. Checks

`python check_arrival_v2.py` prints 12 lines and all 12 passed: form 32 bars, every melody bar 8
eighths, sections add to 32, 96.000 s, loop 0 to 4233600 samples with seam sample difference 0, loop
json 96.0 s, 4 eighths of air in the last bar, all eight voices carry notes, hook 100, range 62 to 76,
blip band 1.44 percent against the title cue's 1.55, drums 4 rungs over 8 bars in quay, 4 over 8 in
lamplight, 5 over 12 in gate, 2 over 4 in turn.

`python probe_motif.py pp_arrival_v2.mid` prints every two bar segment against the cell, which is how
the third return was tuned to 78 percent: ten segments match, each at 0.78 or above.

## 4. The ear loop did not run, and that is a gap, not a result

`tools/ear_critic.py` exits immediately in this session: "not configured: GEMINI_API_KEY is not set in
the environment". The key is read from `os.environ` only, by this card's own rule and by `tools/ai_client.py`,
so no round of the Gemini ear was spent: zero of the four allowed. v2's ear score is therefore unknown,
and nothing in this note claims one. The hook meter, the checks above and the seam are measured.

## 5. Wiring is still gamedev's

`data/audio.json` has no `PP-ARRIVAL` row, and I did not add one; that was already a Q: on the v1 note
and it stays one. v2 is a new asset folder, so no landed cue changed underneath the bus.

## Files here

| file | what it is |
| --- | --- |
| `score_pp_arrival_v2.yaml` | the score: 32 bars, four sections, the cell written out ten times |
| `build_report_v2.json` | the arranger's numbers: 775 notes over 8 voices, drum rungs per section |
| `hook_report_v2.json` | the hook meter, 100 of 100, with every criterion row |
| `pp_arrival_v2.mid` / `.wav` / `.mp3` / `.ogg` | the delivered arrangement and renders, 96.000 s |
| `pp_arrival_v2_humanized.mid` | the renderer's chip legal humanization of the same MIDI |
| `pp_arrival_v2_loop.json` | loop record, sample 0 to 4233600, seam sample difference 0 |
| `probe_motif.py` | per segment similarity print, the tuning instrument for the third return |
| `check_arrival_v2.py` | the 12 checks, copied from v1's checker with this folder's names |
