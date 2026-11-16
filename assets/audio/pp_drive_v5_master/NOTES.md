# pp_drive_v5_master: the final mix of assets/audio/pp_drive_v5/pp_drive_v5.ogg

Card t_71c5dea2 (AUTO-MUSIC-NEXT, musician), 2026-11-14. Built by `tools/final_mix.py`'s own
`master_entry`, called with this folder as its `--asset` and the v5 OGG as its source:

    python <scratch>/pp02_master.py      # F.master_entry({"cue": "PP-02", "asset": "pp_drive_v5_master",
                                         #   "source": "assets/audio/pp_drive_v5/pp_drive_v5.ogg", "row": False}, ...)

Source: `assets/audio/pp_drive_v5/pp_drive_v5.ogg`, sha256
`f35d226a12e8f9467d85fd53c9fdff7b1d92ac5a76b298be49057424b71dbe0f`.

Nothing that already existed was written, moved or re-rendered: `pp_drive/`, `pp_drive_v2/`,
`pp_drive_v4/`, `pp_drive_v5/`, the delivered `pp_drive_master1/` and `data/audio.json` are
untouched. This folder is new, so the previous master is still on disk and still the one the game
names.

## Loudness

| | integrated | true peak | LRA |
| --- | --- | --- | --- |
| source (pp_drive_v5.ogg) | -17.72 LUFS | -0.84 dBTP | 4.9 LU |
| shipped master (pp_drive_master1) | -14.08 LUFS | -0.60 dBTP | 4.3 LU |
| this master | -14.08 LUFS | -0.86 dBTP | 4.3 LU |

Target -14.0 LUFS integrated, ceiling -1.0 dBTP. Gain +4.09 dB, then a 5 ms / 15 ms lookahead
limiter at -2.20 dBFS. The file is the source's own samples: nothing composed, sample count
7,874,643 unchanged, 178.563333 s.

## Loop seam

The tool's default pass trimmed the head by 2.0 ms and left the loop at samples 88 to 7874636,
and the louder body turned the 10 ms after the loop start into a 6.04 dB hole, which its own rule
calls `step` (the band is -6.0 dB). Every combination of 0, 88, 220, 441 and 882 samples at each
edge was measured; the renderer's head and tail fades are 220 samples (5 ms, recorded in the
source sidecar), so the loop now starts past the head fade and ends 10 ms before the file end:

| loop points | verdict | seam level delta | wrap jump against an ordinary step |
| --- | --- | --- | --- |
| 88 to 7874636 (the tool's default) | step | -6.04 dB | -12.52 dBFS against -9.77 dBFS |
| 220 to 7874202 (this master) | clean | -3.24 dB | -25.91 dBFS against -9.77 dBFS |

Loop length 178.548345 s against the source's 178.563333 s: 5 ms of head fade and 10 ms of tail
fade are outside the loop, no musical bar is cut.

## The score numbers this take carries

`tools/hook_score.py` on the MIDI each file renders from:

| file | hook |
| --- | --- |
| pp_drive_v2.mid, the composition the shipped master1 is made of | 83 |
| pp_drive_v4.mid | 92 |
| pp_drive_v5.mid, mastered here | 93 |
| pp_drive_v5_humanized.mid | 83 (not rendered: the meter graded a file nobody hears) |

## What this master does not decide

1. `data/audio.json` still names `pp_drive_master1`. Naming this folder is a data edit, and
   Q: for gamedev whether PP-02 adopts take v5.
2. `tools/counterpoint/cue_gate.py` REFUSES the v5 MIDI as a new cue: G1 CP-01 67 raw clashes on
   a strong beat, G2 CP-09 4 parallel perfect intervals between the outer voices, M1a verdict FAIL
   (hard 343, soft 60, style 294). A landed v5 would need a counterpoint repair pass
   (`tools/counterpoint/repair.py`, accompaniment only, the hook frozen) first. That repair is not
   this card's, and it is the second reason the row edit is gamedev's call.
3. The ear loop did not run. `tools/ear_critic.py` answered "not configured: GEMINI_API_KEY is not
   set in the environment" in this worker's shell; the key is never read from a file here and never
   printed, so the four round ear pass the card asks for is unplayed and no ear number exists for
   this master. Q: for gamedev, whether the ear pass should run in a worker with the key exported.
