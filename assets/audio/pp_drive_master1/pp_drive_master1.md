# pp_drive_master1: the final mix of assets/audio/pp_drive_v2/pp_drive_v2.ogg

Card t_120dc9f2 (W5 SCORE-FINAL, musician). Built by `tools/final_mix.py`, which is the only writer:

    python tools\final_mix.py --build --only PP-02

Source: `assets/audio/pp_drive_v2/pp_drive_v2.ogg`, sha256 `88835655c4877db934320d865dbb98a1433299aec2ddd7305e2927d1f8f2ee04`.

The source file, its MIDI, its WAV and its MP3 are untouched. This folder is a new version; the cue row
that names a build is a person's edit, not this tool's. The file is the source's own samples: nothing
was composed, nothing was re-rendered and the sample count is unchanged (so the duration is too).

## Loudness

| | integrated | true peak | LRA |
| --- | --- | --- | --- |
| source | -17.43 LUFS | -0.72 dBTP | 4.9 LU |
| master | -14.08 LUFS | -0.60 dBTP | 4.3 LU |

Target -14.0 LUFS integrated, ceiling -0.5 dBTP. Gain applied +3.77 dB, then a lookahead limiter at
-2.20 dBFS (5 ms attack, 15 ms release, auto level disabled).

| pass | gain | limiter | measured | true peak | LRA |
| --- | --- | --- | --- | --- | --- |
| 1 | +3.43 dB | -1.00 dBFS | -14.15 LUFS | 0.76 dBTP | 4.7 LU |
| 2 | +3.58 dB | -1.30 dBFS | -14.06 LUFS | 0.38 dBTP | 4.6 LU |
| 3 | +3.64 dB | -1.60 dBFS | -14.06 LUFS | 0.11 dBTP | 4.5 LU |
| 4 | +3.70 dB | -1.90 dBFS | -14.07 LUFS | -0.17 dBTP | 4.4 LU |
| 5 | +3.77 dB | -2.20 dBFS | -14.08 LUFS | -0.60 dBTP | 4.3 LU |

## Loop and seam

The source's own loop sidecar said: pp_drive_v2_loop.json.

The trim rule: trimmed 2.0 ms of head and 0.2 ms of tail under 20 dB below the body.
Splice applied: no, the trimmed seam already read clean.

Loop points of this master: sample 88 to 7874636, 178.561 s, of a file 7874643 samples long.
The file length is the source's, so a scene that plays the whole cue is unaffected; only the wrap moved.

| seam | wrap jump | file's own p99.9 step | head RMS | tail RMS | body RMS | level delta | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| source, at its own points | -54.96 dBFS | -11.79 dBFS | -19.32 | -18.07 | -15.92 | -3.40 dB | clean |
| master, at the trimmed points | -17.33 dBFS | -9.40 dBFS | -18.47 | -11.77 | -12.54 | -5.93 dB | clean |

The seam is measured on the decoded deliverable, not on the render, because that is what the game
plays. `dip` means the wrap passes through a level hole, `step` a level drop of more than 6 dB, and
`click` a wrap jump that is an outlier against the file's own sample motion.

## What this file does not claim

It does not claim the cue is now the accepted take. Naming a build is a cue row edit, and this tool
never writes `data/audio.json`. It does not claim stereo: the library and the game's bus are mono and
spec 12 asks for stereo music, so the channel count is an open Q, recorded in
`knowledge/FINAL-MIX-2026-10-26.md`.
