# DEMO-AUDIO-LAYERS-2026-11-17: the storm, the text blips and the battle stingers in the 180 s cut

Card: t_f19fa5c3 (JUDGE-PANEL-2026-11-17 fix 3). The panel's words were "add hurricane wind, text blips and
battle stingers in the quay, morgan and percy scenes using the musician lane tracks and wire them to the
capture mix; update the verify step to fail when audio is absent; a judge will hear storm and UI sound through
the 180 s video and see audio present in the verify file."

## What the mix is made of, and where every number comes from

`tools/demo_music_bed.py` is the capture mix: it copies the cut's picture (`-c:v copy`), sums layers under its
audio and writes a `_music_verify.json` beside the delivered file. It now sums three layers, and none of the
three is typed into the tool:

| layer | what it is | where the reading comes from |
| --- | --- | --- |
| music bed | the game's own cue for each shot: PP-01 S1/S2, PP-03 S3/S4/S5, PP-06 the Percy fight, PP-03 again when the spare reopens the quay, PP-15b the credits | `data/audio.json` cue rows; the windows come from the cut's own `_verify.json` segments |
| hurricane wind | `wind_quay`, the loop the game holds while the storm is up | `data/audio.json` sounds row; laid under S3, S4, S5 and the S6 seconds the spare reopens the quay |
| text blips and battle stingers | every `PP audio: <cue> played` line in the captures' own logs whose cue is a talk blip (`text_blip_a` narrator, `text_blip_c` Percy, and the speaker files the blip card delivered) or a stinger (`encounter_swoosh`, and the hit family for a take that logs one) | the recorder's JSONs beside the sources: `output/demo_2026-11-04/story_good.events.json` for `raw_story_good.mkv`, `doors.events.json` for `doors.mp4`, and `morgan_talk.events.json` for `morgan_talk.mp4`. The log name is derived from the source name (`raw_` prefix stripped), so a recut re-reads the logs. `morgan_talk.mp4` is not a recording but a cut the November 4 recorder script made out of the `story_good` run, so its log does not exist beside it in the run's clock: `tools/demo_clip_event_log.py` writes it from that run's log through the recorder's own segment table, in the clip's own sound clock, and marks it with a `derived` block. The derivation and its measurement are on `knowledge/DEMO-S5-EVENT-LOG-2026-11-17.md` |

Levels are the engine's own macros, parsed from `game/scripts/pp_audio/pp_audio.gml`: `PP_AUDIO_GAIN_SFX`
0.9 and `PP_AUDIO_GAIN_BLIP` 0.5, so a blip plays at 0.45 and a stinger at 0.9. The bed stays at 0.55 of the
game's 0.7 music level (`0.385`) and the wind at 0.90 of its 0.32 (`0.288`), the numbers the previous two
panels were measured against.

## The clock correction (why the layer does not flam the capture)

The recorder writes its log line one flush after the sound starts, so a raw stamp is late. For every event the
tool cross-correlates the capture's own audio against the cue file within 0.25 s of the stamp; when the match
is at least r = 0.50 the event is placed on the copy the capture holds. The shift is per source, because each
take has its own lag: `story_good.events.json` -97.2 ms across 31 confirmed rows (its two encounter stingers
match at r 0.72 and 0.74), `morgan_talk.events.json` -17.2 ms across 3 (the clip's 24 ms of frame rounding
predicts that), and `doors.events.json` has no confirmed row, so its 16 rows stay on the raw stamp. A row the
capture cannot confirm takes its source's median shift; a source with no confirmed row stays on the raw stamp.
The plan prints the basis of every row (`capture`, `source` or `log`): on this take 34 rows are capture-confirmed,
117 take their source's median and 16 stay on the raw stamp.

## The layer this card produced, and the S5 rows that landed after it

`output/demo/event-bed-2026-11-17-s5.wav`, 180.000 s, 48 kHz stereo, 167 events. The 137-event layer this card
originally shipped (`output/demo/event-bed-2026-11-17.wav`) is superseded by this one; the difference is exactly
the 29 `text_blip_a` and 1 `encounter_swoosh` that S5 gained when `morgan_talk.events.json` existed to be read:

| shot | cue | count |
| --- | --- | --- |
| S4 (Morgan's pages and the quay door pages) | text_blip_a | 67 |
| S4 | encounter_swoosh (Morgan's fight starts at 62.12 s) | 1 |
| S5 (Morgan's talk take) | text_blip_a | 29 |
| S5 | encounter_swoosh (Morgan's stinger at 86.813 s) | 1 |
| S6 (Percy's pages, his fight, the pages after the spare) | text_blip_a | 34 |
| S6 | text_blip_c | 34 |
| S6 | encounter_swoosh (Percy's fight starts at 119.64 s) | 1 |

798 further logged events were dropped because they fall outside the seconds the cut actually uses, and the
clip's derivation dropped 33 more before the layer ever saw them because the clip's sound never carries that
head of its 1.5x segment; the plan and the log's `derived` block report those numbers instead of hiding them.

The sum of 167 events peaks at 1.74 before limiting, so the layer itself is limited to 0.90 (`LAYER_HEADROOM`)
rather than turned down as a whole: the blips keep the level the game plays them at. The mix limiter moved
from 0.95 to 0.86, because music, wind and events together pushed the AAC true peak to +0.2 dBFS; the
re-landed file measures -0.2 dBFS true peak and -16.4 LUFS integrated (ebur128), 0.2 dB hotter than the
137-event file, because 30 more events sum under the same limiter.

## The delivered file and what the verify measures

`output/demo/nightly-2026-11-17.mp4`: 180.000 s, 768x784 h264 with aac 48 kHz stereo, picture packets
unchanged from `nightly-2026-11-15e.mp4` (MD5 `1f5e103646348e8c0d258ce4739374f5` on both, `picture_unchanged`
PASS), so every frame the panel sees is the frame it saw before and only the sound moved. The re-landed file's
sha256 is `56de7bcb9ad7fafa5ee5927c8422cbb11d26283954c51c16d1f51a34b89a274c`, which is the file the S5 lane
measured as its candidate: rebuilding the mix from `nightly-2026-11-15e.mp4` with the 167-event layer
reproduces it byte for byte.

`output/demo/nightly-2026-11-17_music_verify.json`: 28 of 28 PASS, measured on the delivered file. The rows that
carry this card, and the two S5 rows that t_5110295a added:

```
PASS has_audio          audio stream aac 48000 Hz 2 channel(s) is present
PASS picture_unchanged  video packets MD5=1f5e103646348e8c0d258ce4739374f5 against the same MD5: the bed is
                        summed under the audio and the picture is untouched
PASS events_S4_encounter_swoosh  1 encounter_swoosh: the delivered high band is 4.6x the pre-mix band at
                                  those clocks, against 1.5x at the control clocks in the same shot
PASS events_S4_text_blip_a       67 text_blip_a: 5.1x, against 2.9x at the control clocks
PASS events_S5_encounter_swoosh  1 encounter_swoosh: 13.8x, against 2.4x
PASS events_S5_text_blip_a       29 text_blip_a: 6.8x, against 3.1x
PASS events_S6_encounter_swoosh  1 encounter_swoosh: 5.9x, against 1.7x
PASS events_S6_text_blip_a       34 text_blip_a: 8.6x, against 1.9x
PASS events_S6_text_blip_c       34 text_blip_c: 20.7x, against 9.6x
PASS events_absent_S3   S3 at 31.0 s: 1.36x where no text blip or stinger is scheduled, against 2.56x at
                        the control clocks
```

The probe is the film's own 2 to 7 kHz band, where a blip, a noise stinger and the swoosh live, read in the
delivered file and in the same file before the mix at the same clocks. The same bed and the same wind sit in
the event windows and in the control windows, so they cancel; what does not cancel is the layer. A layer that
was planned but never mixed cannot pass, an empty or missing events file fails the row that names it, and a
layer smeared across the whole film fails the S3 control. `tests/test_demo_music_bed_events.py` pins the
reading, the mapping and both failure modes: the reading against `tests/fixtures/story_good.events.sample.json`
(a byte-for-byte excerpt of the November 4 log, committed so the suite passes in a tree that does not hold the
capture), the mapping against a twelve-second silent capture read through the module's own two readers, and the
two failure modes.

`output/demo/nightly-2026-11-17_verify.json` (written by `tools/demo_cut_180.py --verify`) now carries
`"has_audio": true`, `"ok": true` and an `"audio"` block (aac, 48000 Hz, 2 channels). That is the field
`tools/judge_panel.py` reads: on the previous takes it was absent, and the panel was told "audio is absent"
for a film that had sound. `--measure-only --dry-run` now prints "From the capture's own verify file: audio is
present." for this file.

## The honest limit, stated where the panel can read it

S5 (78 to 110 s) now carries a blip layer, 30 rows, but not across the whole shot. `morgan_talk.mp4` is a cut of
the `story_good` run rather than a recording, and once its log is moved into the clip's own sound clock
(`output/demo_2026-11-04/morgan_talk.events.json`, written by `tools/demo_clip_event_log.py`) the 30 rows the
cut's 32.000 s of that clip holds fall between 78.743 and 86.813 s: 29 `text_blip_a` and 1 `encounter_swoosh`.
The rest of S5's stretch has no typed page in the clip's own sound, so it carries no blip, and this is not a
fully blipped shot. That part of the shot still plays its own recorded track, the bed and the wind, and its
narration row passes at -16.9 dB against -27.9 dB for the ducked game track. The measurement behind those 30
rows, including the two clocks and the 33 stamps the clip never sound carries, is on
`knowledge/DEMO-S5-EVENT-LOG-2026-11-17.md`.

## Rebuilding it

```
python tools\demo_clip_event_log.py --clip morgan_talk --check
python tools\demo_cut_180.py --verify --video output\demo\nightly-2026-11-15e.mp4
python tools\demo_music_bed.py --bed output\demo\music-bed-2026-11-17.wav ^
    --bed-file output\demo\music-bed-2026-11-17.wav ^
    --events output\demo\event-bed-2026-11-17-s5.wav ^
    --events-file output\demo\event-bed-2026-11-17-s5.wav ^
    --mix --before output\demo\nightly-2026-11-15e.mp4 --video output\demo\nightly-2026-11-17.mp4
python tools\demo_music_bed.py --verify --video output\demo\nightly-2026-11-17.mp4 ^
    --before output\demo\nightly-2026-11-15e.mp4 ^
    --bed-file output\demo\music-bed-2026-11-17.wav ^
    --events-file output\demo\event-bed-2026-11-17-s5.wav
python tools\demo_cut_180.py --verify --video output\demo\nightly-2026-11-17.mp4
```

The first line is not optional: the derived log is keyed to the clip's segment table, so a re-cut
`morgan_talk.mp4` needs the check to pass or `--clip morgan_talk` to regenerate the log before the layer is
built. `--plan` prints the bed windows, the event rows and the shift basis of each row without writing anything.
