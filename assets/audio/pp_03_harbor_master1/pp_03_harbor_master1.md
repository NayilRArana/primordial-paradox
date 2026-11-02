# pp_03_harbor_master1: the final mix of assets/audio/pp_03_harbor/pp_03_harbor.ogg

Card t_120dc9f2 (W5 SCORE-FINAL, musician). Built by `tools/final_mix.py`, which is the only writer:

    python tools\final_mix.py --build --only PP-03

Source: `assets/audio/pp_03_harbor/pp_03_harbor.ogg`, sha256 `58f2de8b355e8d5f0d3737f8f9786bce0bf4a2a3a2e8bb93f011187e17b15582`.

The source file, its MIDI, its WAV and its MP3 are untouched. This folder is a new version; the cue row
that names a build is a person's edit, not this tool's. The file is the source's own samples: nothing
was composed, nothing was re-rendered and the sample count is unchanged (so the duration is too).

## Loudness

| | integrated | true peak | LRA |
| --- | --- | --- | --- |
| source | -16.89 LUFS | -0.79 dBTP | 2.9 LU |
| master | -14.02 LUFS | -0.55 dBTP | 2.8 LU |

Target -14.0 LUFS integrated, ceiling -0.5 dBTP. Gain applied +2.93 dB, then a lookahead limiter at
-1.30 dBFS (5 ms attack, 15 ms release, auto level disabled).

| pass | gain | limiter | measured | true peak | LRA |
| --- | --- | --- | --- | --- | --- |
| 1 | +2.89 dB | -1.00 dBFS | -14.04 LUFS | -0.32 dBTP | 2.8 LU |
| 2 | +2.93 dB | -1.30 dBFS | -14.02 LUFS | -0.55 dBTP | 2.8 LU |

## Loop and seam

The source's own loop sidecar said: pp_03_harbor_loop.json.

The trim rule: trimmed 1.0 ms of head and 76.6 ms of tail under 20 dB below the body.
Splice applied: yes, 30 ms.

Loop points of this master: sample 44 to 9958036, 225.805 s, of a file 9961412 samples long.
The file length is the source's, so a scene that plays the whole cue is unaffected; only the wrap moved.

| seam | wrap jump | file's own p99.9 step | head RMS | tail RMS | body RMS | level delta | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| source, at its own points | -69.41 dBFS | -11.26 dBFS | -12.36 | -64.02 | -16.08 | -47.94 dB | dip |
| master, at the trimmed points | -12.43 dBFS | -9.15 dBFS | -14.63 | -12.45 | -13.20 | -1.43 dB | clean |

The seam is measured on the decoded deliverable, not on the render, because that is what the game
plays. `dip` means the wrap passes through a level hole, `step` a level drop of more than 6 dB, and
`click` a wrap jump that is an outlier against the file's own sample motion.

## What this file does not claim

It does not claim the cue is now the accepted take. Naming a build is a cue row edit, and this tool
never writes `data/audio.json`. It does not claim stereo: the library and the game's bus are mono and
spec 12 asks for stereo music, so the channel count is an open Q, recorded in
`knowledge/FINAL-MIX-2026-10-26.md`.

## Re-cut from the repaired recipe, 2026-11-02 (card t_1a7c13cc)

The recipe was repaired on 2026-11-01 (card t_79152146: the harmony under the untouched melody changed,
Em to G under the crest and three first inversions), and the render did not follow, so this master was
still the pre-repair mix. This folder was re-cut from the new source through the same writer, the same
command and the same settings:

    python tools\final_mix.py --build --only PP-03

Source sha256 is now `58f2de8b355e8d5f0d3737f8f9786bce0bf4a2a3a2e8bb93f011187e17b15582`, which is the
ogg rebuilt from the repaired recipe on this card. The pre-repair master (source sha256
`e536f397e27f84dca7a72e3b3b603ef363886f3f9374844f72d047238d62a28e`) was moved aside, not overwritten in
place, because the writer refuses an existing folder; its copy is
`/d/hermes-worktrees/pp03-shared-backup-t_1a7c13cc/pp_03_harbor_master1.pre/`.

Measured after the re-cut: -14.02 LUFS integrated, -0.55 dBTP true peak, LRA 2.8 LU, loop 44 to 9958036,
seam clean. The two numbers that moved from the pre-repair build are the same two that moved with the
harmony: source -16.89 LUFS (was -16.91) and master -14.02 (was -14.03). `final_mix.py --verify` reports
all four route masters inside the loudness and peak target, seam clean.

Nothing in this file is a hand measurement: the md and the loop json are the tool's own output, and the
only line a person wrote is this section.
