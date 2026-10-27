# PP-01 "Title Theme" v9, notes. Card M0 counterpoint repair (t_c0597404), 2026-10-26.

Built from v7 (`assets/audio/pp_01_title_v7/`) by `build_pp01_v9.py` in this folder, which reads v7 and
writes a new file: nothing in v7 is edited in place. This is the version where the score has been made to
answer the counterpoint question the card asks. It is **not** the version the ear prefers. v7 stays the
recommended file unless Nayil hears otherwise. The measurement behind it is
`knowledge/TITLE-DISSONANCE-2026-10-26.md`.

## What it is

v7 with its vertical intervals repaired. The melody (`vrc6 pulse a`) and the drums (`noise`, `dpcm`) are
v7's notes, unchanged, checked note for note in `build_report_v9.json` (`frozen`: all three true), so the
hook meter is 83 before and after. Every other pitched voice could move a pitch or drop a note where the
analyser found a raw clash. The movement is small: mean 0.5 to 1.6 semitones per voice, 234 of 287
arpeggio notes, 101 of 121 pad notes and 100 of 114 bass notes unchanged.

| item | count |
| --- | --- |
| edits | 216 (pulse 1 66, pulse 2 48, saw 47, pulse b 35, triangle 20) |
| notes dropped | 23 |
| whole pad chords re-voiced | 6 (bars 10, 27, 32, 50) |

## The clash count

Same analyser (`tools/counterpoint/analyze.py`) on all three, per file JSON in this folder.

| class | v7 | v8 | v9 |
| --- | --- | --- | --- |
| suspension | 25 | 25 | 15 |
| appoggiatura | 25 | 26 | 15 |
| passing | 41 | 41 | 20 |
| neighbour | 6 | 6 | 5 |
| anticipation | 19 | 19 | 18 |
| **raw clash** | **196** | **204** | **2** |
| raw clashes on the downbeat | 30 | 35 | **0** |
| dissonances judged | 312 | 321 | 75 |

In the card's own scope (pulse 1, pulse 2 and the triangle) v9 goes from 26 raw clashes in v7 to **0**,
and from 8 on a downbeat to **0**.

The two clashes left are bars 41 and 42 beat 2, the melody's C#5 and G#4 against the pad's D3. The pad
cannot leave D there without leaving a triad, and no pad chord that contains the melody note fitted, so
they are recorded rather than hidden.

The devices survive: 73 of v7's 116 remain, because the repair only touches raw clashes. The injector's
suspension at bar 39 is still a suspension. Its anticipation at bar 36 was never one by the rules (the bar
it leaves sounds G#, so the G4 there is a cross relation), and that is part of what moved.

## The ear

One call, one judge (`gemini-3.5-flash`), both files back to back. **This review covers the first build of
v9**, before the anticipation rule was widened and before the pedal fix, so it is a few edits heavier than
the file shipped. The free tier quota ran out on that call, so the shipped build could not be re-scored
the same day. Treat the numbers as a strong indication, not a measurement of the exact file shipped.

| file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v7 | 8 | 6 | 7 | 5 | 8 | 7 | **41** |
| v9 (first build) | 5 | 7 | 5 | 6 | 5 | 5 | **33** |

Review: `assets/audio/ear_reviews/compare_pp_01_title_v7_pp_01_title_v9_20261026T190437Z.md`. The judge
prefers v7 by 8 points, outside its own 1 point per criterion noise floor. Its stated reason is that v7's
lead cuts above the accompaniment while v9's blends into it, and that reads as the honest cost of the
repair: consonant accompaniment blends, and blend costs a hook its edge. The judge also describes timbre
differences between the two files that the MIDI cannot explain (both render on the default duty cycles, no
CC data in either file), so treat its per axis detail as a hint, not a measurement.

## Recommendation

v9 answers the card: no raw clash on a downbeat, 2 raw clashes in 52 bars, 0 in the three 2A03 voices, 73
devices kept, hook and drums untouched. It is not a better cue by ear. Two ways forward, and the second is
the one this build points at:

1. Nayil picks by ear between v7 and v9.
2. If the smooth version is the wrong direction, the next build turns raw clashes into *prepared and
   resolved* devices instead of into consonances: keep the v7 pitch and delay the accompaniment's move, so
   the bite survives with a preparation in front of it and a resolution behind it. The analyser already
   labels what that would need, and "the upper voice arrives over a held note" is the shape to go after
   first: 96 of v7's 196 raw clashes are that one texture.

## Loop seam

`pp_01_title_v9_loop.json`: 3275997 samples, loop seam sample difference 0, peak -1.00 dBFS, RMS -17.40
dBFS, edge peak head 215, tail 0. 52 bars, 74.286 s, loop from bar 5.

## What is not in this commit

`pp_01_title_v9.ogg` sits in this folder uncommitted, on purpose. The pre-commit gate refuses a new
`assets/audio/**` .ogg that `game/PrimordialParadox.yyp` does not declare as an Included File
(`check_build_inputs.py --staged`: `UNPAIRED IN COMMIT ... names no datafiles/streams/pp_01_title_v9.ogg`),
and the live `.yyp` was mid-change by another card while this landed (three new tile Included Files from
ART-B-MAPS), so staging a regenerated `.yyp` here would have carried that lane's uncommitted projection
into this commit. Registering v9 as a stream is one `.yyp` entry plus a mirror run, and it belongs after
Nayil picks v9 (handoff t_9ed296f1) or after that lane lands its `.yyp`. The render is regenerable in the
meantime: `render_chip.py --humanize --loop-bars 52`.

## Checks run

`python build_pp01_v9.py` prints the counts above and is deterministic: two runs write the same MIDI.
`render_chip.py --humanize --loop-bars 52` rendered the WAV, MP3 and loop JSON. `analyze.py --json` wrote
`clash_v7.json`, `clash_v8.json`, `clash_v9.json`. `keycheck.py` gave the out of key note and cross
relation counts. `ear_critic.py --compare` wrote the review. The register check in the build report is 0
notes outside the span each voice holds in v7. The tools are pinned by `tests/test_clash.py`,
`test_repair.py`, `test_keycheck.py`, `test_analyze.py` and `test_build_pp01_v9.py`.
