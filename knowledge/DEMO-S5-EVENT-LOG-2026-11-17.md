# S5's event log: the Morgan talk take is a cut, not a recording (card t_b24aa225)

Musician lane card t_f19fa5c3 (JUDGE-PANEL-2026-11-17 fix 3) closed with one named gap: the cut's third layer
places 137 text blips and battle stingers read from the captures' own event logs, and S5 (78.000 to 110.000 s)
got none, because `output/demo_2026-11-04/morgan_talk.mp4` has no `morgan_talk.events.json` beside it. That
card asked this lane for the log or for a ruling that S5 stays without a blip layer.

The ruling: no re-record is needed, and the naming question has a concrete answer. `morgan_talk.mp4` was never
recorded. It is a clip assembled by the 2026-11-04 session's own recorder script,
`output/demo_2026-11-04/recorder/demo_cut.py`, from the `story_good` run: its `CLIPS["morgan_talk"]` row is
four segments of that run, the first sped to 1.5x for the picture. The take's log therefore already exists,
under the run's name: `output/demo_2026-11-04/story_good.events.json`, which the events layer already reads for
S4 and S6. What was missing is that log in the clip's clock, and that is arithmetic, not a judgement.

## The two clocks

`make_clip` in the recorder trims the picture from `a + LAG` to `b + LAG` and plays it at `sp`, so a segment
lasts `(b - a) / sp` seconds on screen. The sound is never time stretched: for the same segment it takes the
last `(b - a) / sp` seconds of the run's audio at normal speed. The clip's sound therefore starts at run time
`b - (b - a) / sp`, not at `a`.

    clip time = (the segment durations before this one) + (stamp - audio window start)

`LAG` cancels: the recorder adds the same lag to the picture trim and the audio trim, so the two stay together
inside a clip whatever it measured on the night. At speed 1.0 the window is the segment and the rule is the
cut's own, a stamp `d` seconds into the segment lands `d` seconds into that segment's clock.

The one honest subtraction: inside the 1.5x segment the clip kept the picture for run 8.7 to 21.8 s and the
sound only for 13.067 to 21.8 s. A blip stamped in 8.7 to 13.067 s was in the picture and heard by nobody, so
it gets no place in the layer. 33 of the run's log lines inside the clip fall in that hole and are counted in
the file's own `derived` block, not placed.

## What was written

`tools/demo_clip_event_log.py` writes `<clip>.events.json` beside the clip, from the run's log, through the
recorder's own table. The table is imported from `demo_cut.py` rather than typed again, so the two cannot
disagree, and the write is refused when the segments do not add to the clip's own ffprobe length (tolerance
0.15 s, which is frame rounding at 60 fps).

| reading | value |
| --- | --- |
| clip | `output/demo_2026-11-04/morgan_talk.mp4`, 34.158 s on disk |
| segments | 8.700 to 21.800 at 1.5x, then 22.600 to 32.000, 32.000 to 38.300, 38.300 to 48.000 at 1.0x |
| segments add to | 34.134 s, so 24 ms of frame rounding against the file |
| log written | `output/demo_2026-11-04/morgan_talk.events.json`, 107 rows in the clip's clock |
| rows dropped, no sound | 33 (the head of the 1.5x segment) |
| rows the cut's S5 uses | 30 of them have a clip stamp below 32.000 s, which is S5's own in point and length |

The file keeps the recorder's own shape (`name`, `events` as `[second, line]`, `audio_fmt`, `peak`) so
`tools/demo_music_bed.py` reads it with no change, and it carries a `derived` block naming the run's log, the
segment table, the rule and the dropped stamps. A log the game wrote live has no `derived` key, so the two
cannot be confused.

## The measurement, not the claim

Two readings, both on a candidate file built with the musician lane's own commands, never by hand:

    python tools/demo_music_bed.py --events output/demo/event-bed-2026-11-17-s5.wav \
        --video output/demo/nightly-2026-11-17.mp4 --before output/demo/nightly-2026-11-15e.mp4
    python tools/demo_music_bed.py --mix --video output/demo/nightly-2026-11-17-s5cand.mp4 \
        --before output/demo/nightly-2026-11-15e.mp4 --bed-file output/demo/music-bed-2026-11-17.wav \
        --events-file output/demo/event-bed-2026-11-17-s5.wav
    python tools/demo_music_bed.py --verify --video output/demo/nightly-2026-11-17-s5cand.mp4 \
        --before output/demo/nightly-2026-11-15e.mp4 --bed-file output/demo/music-bed-2026-11-17.wav \
        --events-file output/demo/event-bed-2026-11-17-s5.wav

1. The layer now holds 167 events against the 137 that passed before: S5 adds 29 `text_blip_a` and 1
   `encounter_swoosh`, all inside 78.743 to 86.813 s. Nothing else about the layer moved: the other shots'
   rows are the same rows.
2. The derived log's own median shift is -17.2 ms, measured by cross-correlating the clip's audio against each
   cue file, against -97.2 ms for the run's log read straight. The clip's frame rounding predicts about -24 ms,
   so the correction the derivation needs is the size of the thing that caused it.
3. Three of the S5 rows are confirmed by the capture's own audio at `EVENT_ALIGN_MIN_R`: the stinger at
   86.813 s finds its copy at -17.2 ms with r=0.71, and the pair of blips at 86.11 s finds one copy at +-50 ms
   with r=0.61 (the two are 90 ms apart, so the search can hand either of them the other's copy; the median is
   what the rest of the rows take).
4. On the delivered candidate the events rows in S5 pass: `events_S5_text_blip_a` 29 blips, the high band
   6.8x the pre-mix band against 3.1x at the control clocks in the same shot, and `events_S5_encounter_swoosh`
   13.8x against 2.4x. The quiet control S3 still reads 1.36x. `demo_music_bed --verify`: 28 of 28 PASS.

## So the next cut cannot lose it silently

`tools/demo_cut_180.py --verify` now carries a `capture_logs` row: every S4 to S6 source has to resolve its
own event log by the reader's naming rule, and the row names each source and the log it found. S1 to S3 are
exempt with the reason in the code: S1's row is the drawn title card's clock and S3 is the shot the events
layer uses as its quiet control, so neither is scored with blips. A future derived clip in S4 to S6 that keeps
no log turns that row red instead of going quiet.

Cut verify on the candidate: 27 of 27 PASS, `capture_logs` reads `doors.mp4 -> doors.events.json,
raw_story_good.mkv -> story_good.events.json, morgan_talk.mp4 -> morgan_talk.events.json`.

## What this page does not claim

- The delivered `output/demo/nightly-2026-11-17.mp4` is not replaced here. That file is the musician lane's
  delivery and its sha256 is recorded on card t_f19fa5c3, so this lane hands them the log and a measured
  candidate (`output/demo/nightly-2026-11-17-s5cand.mp4`) and lets them re-land the cut.
- S5's blip layer is not "the whole shot blipped": the rows land where the clip's own sound holds Morgan's
  typing. The rest of S5's 32 s has no typed page in that stretch of the take's sound, so it carries none.
- The verify proves the delivered file's high band rises at the event clocks against control clocks in the same
  shots. It is a measurement of the mix, not a listening judgement.
- `output/` is not tracked by git, so the log itself lives in the capture bundle beside the clip and the tool is
  what survives a checkout: `python tools\demo_clip_event_log.py --clip morgan_talk` writes it again, and
  `--check` refuses a stale one.
