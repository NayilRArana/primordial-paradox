# PP-01 "Title Theme" v8, notes. Card AUTO-MUSIC-NEXT (t_61d9e8a2), round 2, 2026-10-24 19:31 UTC.

This is the second loop round, built from v7 (`assets/audio/pp_01_title_v7/`). It is **not** the
recommended file: the ear read it one point lower than v7 and the hook meter is identical. It is kept
because the card asks for the loop to run and for every version to live in its own folder.

## What it adds over v7

| change | measure | check |
| --- | --- | --- |
| sixteenth offbeat ghost hats in both B sections, a falling velocity snare figure across bars 21 to 24, open hat flams before bars 13, 21, 29, 37, 45, and a low noise pitch on 8 offbeats as a kick substitute | noise 266 to 335 hits, 40 ghost hats | `build_report_v8.json` drums |
| DIS-21 pedal tone, risk 2: the triangle drops its moving line for the trio's cold half (bars 41 to 43) and holds A2, returning on bar 44 where A is a chord tone again | 5 notes removed, 3 pedals written | `build_report_v8.json` devices |
| human feel: the pad staggered 1 to 2 frames late, offbeat hats delayed one frame, the kick allowed a frame of slop outside section downbeats, repeated melody pitches played 4 quieter | 160 pad notes, 261 noise notes, 99 dpcm notes moved; 2 repeated melody pitches pulled down | `build_report_v8.json` human |

Every motif cell, the form, the key, 126 bpm, 3/4, 52 bars and the loop point are v7's.

## The two measures

| file | hook meter | ear (gemini-3.5-flash) |
| --- | --- | --- |
| v7 | 83 / 100 | hook 8, drums 5, tension 6, human 4, variety 8, structure 7 = **38** |
| v8 | 83 / 100 | hook 7, drums 5, tension 6, human 4, variety 7, structure 8 = **37** |

Review: `assets/audio/ear_reviews/pp_01_title_v8_20261024T192130Z.md`. The judge's own noise floor is
1 point per criterion (`assets/audio/EAR_SWEEP_2026-10-22.md`), so structure +1 against hook -1 and
variety -1 is a wash, not a win. That is why the loop stopped at round 2 of the allowed 4.

## Loop seam

`pp_01_title_v8_loop.json`: 3275997 samples, loop seam sample difference 0, peak -1.00 dBFS, RMS
-17.46 dBFS, edge peak head 0, edge peak tail 0. The head peak is 0 where v7's is 206 because the pad
stagger pushes the file's first attack 1 frame (16.8 ms) late, so the first millisecond of the file
is silence. Inaudible as a start, and it does not touch the bar 52 to bar 5 junction the game loops
through, but it is the one measurable regression in this build and it is recorded rather than hidden.
