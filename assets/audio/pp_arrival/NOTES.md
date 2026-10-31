# PP-ARRIVAL "Night Quay", notes. Card CUE-ARRIVAL (t_9ba8559f), written 2026-10-23.

A new cue folder, `assets/audio/pp_arrival/`. Nothing in it existed before this card, and no other
cue folder was written. The composition is mine, from the brief in the card and the three knowledge
files it names (`ARRIVAL-CONTENT.md`, `MUSIC-STYLE-BIBLE.md`, `MUSIC-HOOK-GRAMMAR.md`); no tune is
quoted from `pp_01_title` or from any other cue.

## What it is

A night quay walking bed in A minor, 4/4, 80 bpm, 48 bars, 144.000 s a loop. Four textures inside
the one loop, so five to seven minutes of walking and talking does not sit on one idea:

| section | bars | what it is |
| --- | --- | --- |
| quay | 1 to 16 | the block itself, thin: lead, pad, guide tone, half note broken chord, bass, a brushed pulse |
| lamplight | 17 to 32 | the same walk with the lamps lit: echo, a louder broken chord, a walking bass on bars 23, 24 and 31, heartbeat kick |
| gate | 33 to 44 | the B section, for when the gate is in sight: the line climbs a fourth higher, the kit changes to a soft noise floor with a downbeat wash and a build up into bars 36, 40 and 44, the bass walks, and the section closes on the dominant, unresolved |
| turn | 45 to 48 | the way home: the parts thin out, and bar 48 ends with three eighths of air so the loop point lands on a rest and not on a cut |

The theme is a two bar cell: A4 E5 D5 C5 A4, one leap up a fifth and three steps down, answered by
A4 G4 F4 E4, a stepwise descent onto the fifth. It returns four times: plainly in bars 1 and 9, with
its tail lifted to B4 at bar 17, and plainly again at bar 25. Everything else is written by step, so
the one leap in the cell is the leap the cue is recognised by.

## The numbers this card is checked on

Hook score, printed by `tools/hook_score.py` through the renderer and stored in `hook_report.json`:

    83 of 100, 8 of 10 criteria at full marks
    motif returns 12/12, hook cell 10/10, steps 12/12 (75 percent), leaps per motif 8/8 (1 leap),
    contour 10/10 (arch in all four returns), third return variation 8/8, range 8/8 (15 semitones),
    repeated pitch 6/6
    the two that do not: loop length 3/6 (48 bars is not 8, 16 or 32, and 48 is what the card asks
    for), motif coverage 6.3/20 (19 percent of 190 notes sit inside the two bar motif)

Loop seam, printed by `tools/render_chip.py`:

    loop 48 bars | 6350400 samples | seam sample difference 0 | edge peak head 593 tail 0

So the last sample of bar 48 and the first sample of bar 1 are the same value, and the five
millisecond fade the renderer writes at both ends leaves the seam silent. `check_arrival.py` also
holds the loop json to starting at sample 0, ending at 6350400, and lasting 144.000 s.

## What the checks measure, one line each

`check_arrival.py` prints 12 lines and exits 0 only when all pass (all 12 passed on this build):

| check | what it measured |
| --- | --- |
| form | 48 bars, inside the card's 32 to 48 |
| bars of 8 | every melody bar of every section holds exactly 8 eighths |
| sections add | 48 section bars against 48 in the meta block |
| duration | 144.000 s at 80 bpm, 144.000 s expected |
| loop points | loop 0 to 6350400 samples, seam sample difference 0 |
| loop covers | loop json duration 144.0 s |
| seam air | the last bar ends with 3 eighths of rest |
| voices | all seven melodic and percussion voices carry notes; 190 lead, 101 guide, 96 pad, 236 arp, 112 echo, 108 bass, 132 noise, 118 dpcm |
| hook | 83 of 100, 8 of 10 criteria at full marks |
| range | melody 64 to 79, 15 semitones, inside the 60 to 84 register and the 18 semitone hook limit |
| blip room | 1.58 percent of the energy in the 1.5 to 3 kHz band, against the title cue's 1.55 percent |
| drums | 4 rungs over 16 bars in quay, 4 in lamplight, 5 over 12 in gate, 2 over 4 in turn, so no section is one repeated bar |

## Mix, and the text blips

The blips fire one per three characters at half the effect bus, pitched per speaker (spec 12 rule 6), so
the bed has to leave the 1.5 to 3 kHz band and the half second after each dialogue line quiet. Three
choices do that: the lead sits at chip level 10 rather than the 12 to 14 a foreground theme would
take; the broken chord is in half notes in three of the four sections, at level 3 in quay and the
turn, so the offbeats are empty; and the noise kit is brushed (CLM quiet set) at level 4, with the
loudest single hit a downbeat wash in the gate section.

The measured band share is honest but tight: 1.58 percent against the title cue's 1.55 percent, which
is inside the check's one point tolerance and not a large margin. If gamedev hears the blips fight the
bed, the cheapest lever is the lead's level, 10 down to 9, and the guide tone's, 3 down to 2, both in
`score_pp_arrival.yaml`, with no arrangement change.

## What this cue does not do, stated plainly

- **Loudness.** Spec 12 asks for music at minus 14 LUFS. This cue is delivered at the renderer's own
  levels, peak minus 1.00 dBFS and rms minus 16.30 dBFS, the same as every landed cue in this repo
  (`pp_05_small_ship_v2` rms minus 19.90, `pp_03_harbor_v2` likewise unnormalised). No LUFS pass was
  run, because the project has no loudness tool and adding one changes every cue. The music bus volume
  of 0.7 in `data/audio.json` is gamedev's field and I did not write it.
- **OGG loop metadata.** Spec 12 rule 3 wants the loop points inside the OGG. The encode is plain
  libvorbis at quality 6, 44.1 kHz mono, 144.000 s; the loop lives in the sidecar
  `pp_arrival_loop.json`, which is the second half of what spec 12 asks for ("plus a sidecar text file
  naming source tempo and loop"). No cue in this repo carries LOOPSTART tags today, so this cue is
  consistent with them rather than better.
- **Wiring.** I did not write `data/audio.json`. The cue id used in the score is `PP-ARRIVAL`, which is
  not one of the seventeen rows in that file; which row plays this cue, and under which map or scene,
  is gamedev's call on ARRIVAL-MAP-2.
- **Stereo.** Spec 12 asks for stereo music. The renderer is mono, as every landed cue is.

## Files here

| file | what it is |
| --- | --- |
| `score_pp_arrival.yaml` | the score: meta, motifs, voice levels, four sections with chords, melody, texture and drum plan |
| `build_arrival.py` | the arranger: reads the score and the drum library, writes the eight voice MIDI. `--probe` prints every melody bar and its eighth count |
| `check_arrival.py` | the 12 checks above, printed as PASS or FAIL lines, exit 0 only on all pass |
| `pp_arrival.mid` | the delivered arrangement, 1093 notes across 8 voices |
| `pp_arrival.wav` / `.mp3` / `.ogg` | 44.1 kHz mono, 16 bit, 144.000 s, peak minus 1.00 dBFS, rms minus 16.30 dBFS |
| `pp_arrival_loop.json` | the renderer's loop record: sample 0 to 6350400, seam sample difference 0 |
| `build_report.json` | the arranger's own numbers: sections, note counts, levels, drum rungs, drum source path |
| `hook_report.json` | the hook meter, 83 of 100, with its criteria rows |

No key or login file was opened or written. The build is deterministic: the same score and the same
drum pattern file produce the same MIDI bytes.
