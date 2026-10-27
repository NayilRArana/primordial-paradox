# pp_03_harbor_master1: the final mix of assets/audio/pp_03_harbor/pp_03_harbor.ogg

Card t_120dc9f2 (W5 SCORE-FINAL, musician). Built by `tools/final_mix.py`, which is the only writer:

    python tools\final_mix.py --build --only PP-03

Source: `assets/audio/pp_03_harbor/pp_03_harbor.ogg`, sha256 `e536f397e27f84dca7a72e3b3b603ef363886f3f9374844f72d047238d62a28e`.

The source file, its MIDI, its WAV and its MP3 are untouched. This folder is a new version; the cue row
that names a build is a person's edit, not this tool's. The file is the source's own samples: nothing
was composed, nothing was re-rendered and the sample count is unchanged (so the duration is too).

## Loudness

| | integrated | true peak | LRA |
| --- | --- | --- | --- |
| source | -16.91 LUFS | -0.79 dBTP | 2.9 LU |
| master | -14.03 LUFS | -0.56 dBTP | 2.8 LU |

Target -14.0 LUFS integrated, ceiling -0.5 dBTP. Gain applied +2.96 dB, then a lookahead limiter at
-1.30 dBFS (5 ms attack, 15 ms release, auto level disabled).

| pass | gain | limiter | measured | true peak | LRA |
| --- | --- | --- | --- | --- | --- |
| 1 | +2.91 dB | -1.00 dBFS | -14.05 LUFS | -0.29 dBTP | 2.8 LU |
| 2 | +2.96 dB | -1.30 dBFS | -14.03 LUFS | -0.56 dBTP | 2.8 LU |

## Loop and seam

The source's own loop sidecar said: pp_03_harbor_loop.json.

The trim rule: trimmed 1.0 ms of head and 76.6 ms of tail under 20 dB below the body.
Splice applied: yes, 30 ms.

Loop points of this master: sample 44 to 9958036, 225.805 s, of a file 9961412 samples long.
The file length is the source's, so a scene that plays the whole cue is unaffected; only the wrap moved.

| seam | wrap jump | file's own p99.9 step | head RMS | tail RMS | body RMS | level delta | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| source, at its own points | -69.41 dBFS | -11.28 dBFS | -12.36 | -64.02 | -16.08 | -47.93 dB | dip |
| master, at the trimmed points | -12.53 dBFS | -9.16 dBFS | -14.63 | -12.43 | -13.19 | -1.43 dB | clean |

The seam is measured on the decoded deliverable, not on the render, because that is what the game
plays. `dip` means the wrap passes through a level hole, `step` a level drop of more than 6 dB, and
`click` a wrap jump that is an outlier against the file's own sample motion.

## What this file does not claim

It does not claim the cue is now the accepted take. Naming a build is a cue row edit, and this tool
never writes `data/audio.json`. It does not claim stereo: the library and the game's bus are mono and
spec 12 asks for stereo music, so the channel count is an open Q, recorded in
`knowledge/FINAL-MIX-2026-10-26.md`.
