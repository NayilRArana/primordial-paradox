# pp_04_navy_sailors_master1: the final mix of assets/audio/pp_04_navy_sailors/pp_04_navy_sailors.ogg

Card t_120dc9f2 (W5 SCORE-FINAL, musician). Built by `tools/final_mix.py`, which is the only writer:

    python tools\final_mix.py --build --only PP-04

Source: `assets/audio/pp_04_navy_sailors/pp_04_navy_sailors.ogg`, sha256 `74de226bc36decf7f5591a830ccb522d61070691648fa7956a66a4b951a85f23`.

The source file, its MIDI, its WAV and its MP3 are untouched. This folder is a new version; the cue row
that names a build is a person's edit, not this tool's. The file is the source's own samples: nothing
was composed, nothing was re-rendered and the sample count is unchanged (so the duration is too).

## Loudness

| | integrated | true peak | LRA |
| --- | --- | --- | --- |
| source | -18.53 LUFS | -0.80 dBTP | 5.3 LU |
| master | -14.10 LUFS | -0.59 dBTP | 4.2 LU |

Target -14.0 LUFS integrated, ceiling -0.5 dBTP. Gain applied +5.29 dB, then a lookahead limiter at
-1.60 dBFS (5 ms attack, 15 ms release, auto level disabled).

| pass | gain | limiter | measured | true peak | LRA |
| --- | --- | --- | --- | --- | --- |
| 1 | +4.53 dB | -1.00 dBFS | -14.50 LUFS | -0.27 dBTP | 4.6 LU |
| 2 | +5.03 dB | -1.30 dBFS | -14.20 LUFS | -0.51 dBTP | 4.3 LU |
| 3 | +5.23 dB | -1.30 dBFS | -14.06 LUFS | -0.25 dBTP | 4.3 LU |
| 4 | +5.29 dB | -1.60 dBFS | -14.10 LUFS | -0.59 dBTP | 4.2 LU |

## Loop and seam

The source's own loop sidecar said: pp_04_navy_sailors_loop.json.

The trim rule: trimmed 0.0 ms of head and 39.4 ms of tail under 20 dB below the body.
Splice applied: no, the trimmed seam already read clean.

Loop points of this master: sample 0 to 1922624, 43.597 s, of a file 1924363 samples long.
The file length is the source's, so a scene that plays the whole cue is unaffected; only the wrap moved.

| seam | wrap jump | file's own p99.9 step | head RMS | tail RMS | body RMS | level delta | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| source, at its own points | -69.56 dBFS | -13.88 dBFS | -16.09 | -240.00 | -15.65 | -224.35 dB | dip |
| master, at the trimmed points | -41.26 dBFS | -11.01 dBFS | -13.91 | -10.53 | -11.27 | -2.64 dB | clean |

The seam is measured on the decoded deliverable, not on the render, because that is what the game
plays. `dip` means the wrap passes through a level hole, `step` a level drop of more than 6 dB, and
`click` a wrap jump that is an outlier against the file's own sample motion.

## What this file does not claim

It does not claim the cue is now the accepted take. Naming a build is a cue row edit, and this tool
never writes `data/audio.json`. It does not claim stereo: the library and the game's bus are mono and
spec 12 asks for stereo music, so the channel count is an open Q, recorded in
`knowledge/FINAL-MIX-2026-10-26.md`.
