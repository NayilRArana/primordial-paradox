# pp_boarding_master1: the final mix of assets/audio/pp_boarding/pp_boarding.ogg

Card t_120dc9f2 (W5 SCORE-FINAL, musician). Built by `tools/final_mix.py`, which is the only writer:

    python tools\final_mix.py --build --only PP-17

Source: `assets/audio/pp_boarding/pp_boarding.ogg`, sha256 `52c1d67c0f239835c6dc35f90140343888185fef8d9eb8a1073f47ac4eee0348`.

The source file, its MIDI, its WAV and its MP3 are untouched. This folder is a new version; the cue row
that names a build is a person's edit, not this tool's. The file is the source's own samples: nothing
was composed, nothing was re-rendered and the sample count is unchanged (so the duration is too).

## Loudness

| | integrated | true peak | LRA |
| --- | --- | --- | --- |
| source | -17.55 LUFS | -0.81 dBTP | 1.1 LU |
| master | -14.01 LUFS | -0.58 dBTP | 1.0 LU |

Target -14.0 LUFS integrated, ceiling -0.5 dBTP. Gain applied +3.57 dB, then a lookahead limiter at
-1.30 dBFS (5 ms attack, 15 ms release, auto level disabled).

| pass | gain | limiter | measured | true peak | LRA |
| --- | --- | --- | --- | --- | --- |
| 1 | +3.55 dB | -1.00 dBFS | -14.02 LUFS | -0.29 dBTP | 1.0 LU |
| 2 | +3.57 dB | -1.30 dBFS | -14.01 LUFS | -0.58 dBTP | 1.0 LU |

## Loop and seam

No loop sidecar beside the source, so the whole file is the loop.

The trim rule: trimmed 1.0 ms of head and 1518.3 ms of tail under 20 dB below the body.
Splice applied: no, the trimmed seam already read clean.

Loop points of this master: sample 44 to 1344244, 30.481 s, of a file 1411200 samples long.
The file length is the source's, so a scene that plays the whole cue is unaffected; only the wrap moved.

| seam | wrap jump | file's own p99.9 step | head RMS | tail RMS | body RMS | level delta | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| source, at its own points | -73.72 dBFS | -14.10 dBFS | -13.44 | -240.00 | -15.32 | -224.68 dB | dip |
| master, at the trimmed points | -9.23 dBFS | -10.82 dBFS | -14.80 | -11.36 | -11.76 | -3.04 dB | clean |

The seam is measured on the decoded deliverable, not on the render, because that is what the game
plays. `dip` means the wrap passes through a level hole, `step` a level drop of more than 6 dB, and
`click` a wrap jump that is an outlier against the file's own sample motion.

## What this file does not claim

It does not claim the cue is now the accepted take. Naming a build is a cue row edit, and this tool
never writes `data/audio.json`. It does not claim stereo: the library and the game's bus are mono and
spec 12 asks for stereo music, so the channel count is an open Q, recorded in
`knowledge/FINAL-MIX-2026-10-26.md`.
