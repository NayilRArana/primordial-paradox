# DEMO MUSIC BED, 2026-11-15 (card t_04749694, fix 4 of JUDGE-PANEL-2026-11-15)

## What the panel asked, and what the film actually measured

The panel wrote that "the verify file reports audio is absent for the full 180 seconds". That sentence
is false against the file it names, and this card's own body calls the measured number the winner:

| measure | `output/demo/nightly-2026-11-14.mp4` |
| --- | --- |
| streams | h264 768x784 60 fps + aac, 48 kHz, stereo |
| duration | 180.000 s |
| mean volume, whole film | -20.3 dB (`volumedetect`), -26 to -27 dB in the credits |
| narration_S1..S6 | 6 of 6 PASS in its own verify file, -18.5 to -22.0 dB per window |

So the film was never silent. What it did not carry is a game cue under the voice in a way a listener
can name: the shots were cut from captures with their own audio, and the six narration clips sit over
that at -18.5 to -22.0 dB, which leaves the music under the voice unmeasured and unnamed.

## What was delivered

`output/demo/audiofix-2026-11-15.mp4` is the judged cut with one more layer: the game's own cue for
each shot, looped from the delivered OGG at the game's own 0.7 volume scaled to 0.385, faded at its
edges, summed under the existing audio, limited at 0.95. Picture is copied, not re-encoded.

| window | shot | cue | before dB | after dB | residual vs bed |
| --- | --- | --- | --- | --- | --- |
| 0.000 to 16.000 | S1 | PP-01 Title Theme | -20.0 | -19.1 | r 0.48 |
| 16.000 to 29.000 | S2 | PP-01 Title Theme | -18.5 | -18.2 | r 0.24 |
| 29.000 to 39.000 | S3 quay, the hurricane | PP-03 Harbor Storm | -18.6 | -17.2 | r 0.45 |
| 39.000 to 78.000 | S4 quay and Morgan | PP-03 Harbor Storm | -19.8 | -18.2 | r 0.47 |
| 78.000 to 110.000 | S5 Morgan talk | PP-03 Harbor Storm | -20.0 | -18.4 | r 0.47 |
| 110.000 to 140.833 | S6 Percy's fight | PP-06 Percy, Possessed | -19.2 | -17.8 | r 0.39 |
| 140.833 to 151.083 | S6 the spare lands | PP-03 Harbor Storm | -26.4 | -21.7 | r 0.65 |
| 151.083 to 180.000 | S6 credits | PP-15b Mercy | -27.1 | -21.8 | r 0.70 |

Every cue is read from `data/audio.json` by id; nothing was composed, downloaded or re-rendered. The
windows are read from the cut's own `segments` in its verify file, so a recut moves the bed with it or
the tool refuses.

## How the bed is proved to be in the delivered file

Correlating a delivered window against the bed proves nothing here: the window holds the film's own
music, the voice and the AAC encoder's noise, all of them louder than a 0.385 bed, and the measured
number sits between -0.11 and -0.44. The tool subtracts the same window of the file before the bed
(leaving the bed as the residual) and sweeps +-200 ms for the lag. Every one of the eight windows finds
its own cue at -5.0 ms with a spread of 0.0 ms, which is the AAC frame, not chance. The video stream's
packet md5 is identical before and after (`e1c474ec1468f88303b2e4df09fdf316`), so no pixel changed.

All 12 checks PASS in `output/demo/audiofix-2026-11-15_music_verify.json`.

## The one cue this card did NOT decide

`output/demo/run_002_verify.json` line "101.084 s: ... fight morgan_gate asked PP-04" shows the game
starting Navy Sailors for Morgan's fight, while `data/maps/all.json` line 459 gives the quay map
`"music": "PP-03"` and Morgan's encounter sits in it. Which cue that fight plays is gamedev's, and its
ruling card t_279ef225 is still blocked, so this bed keeps the room's own PP-03 under Morgan and does
not override the ruling with a demo edit. If gamedev names PP-04 for the fight, the change is one row
of `BED_TABLE` in `tools/demo_music_bed.py`.

## Files

- `tools/demo_music_bed.py` (new): `--plan`, `--bed`, `--mix`, `--verify`. It refuses a cut whose audio
  is missing, whose duration is not 180.000 s, whose verify file has no segments, or a cue that is
  pending in `data/audio.json`.
- `output/demo/music-bed-2026-11-15.wav`, 180.000 s, 48 kHz stereo, md5 `9f26837dc23e453ccd7b3bcd2f4ce27f`.
- `output/demo/audiofix-2026-11-15.mp4`, md5 `e83d60a96743c3a5491a8c59de23a1b4`, plus its
  `_verify.json` (picture and captions, copied from the cut's own verify) and `_music_verify.json`.
- To fold it into a nightly, render the cut, then
  `python tools\demo_music_bed.py --mix --video <cut> --bed-file output\demo\music-bed-2026-11-15.wav`,
  then `--verify --video <cut> --before <copy of the cut before the mix>`.
