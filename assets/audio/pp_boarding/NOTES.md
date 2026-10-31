# PP-BOARDING: the gangway cue that stops at the hatch

Card CUE-BOARDING (t_8158e5f9), created 2026-10-23 by gamedev for the boarding
scene SHIP-DECK-MAP (t_a3fa132a). Output folder: `assets/audio/pp_boarding/`.
This card does not write `data/audio.json`; the cue row is gamedev's.

Clean room: composed here from the brief in the card, the ship_boarding row in
`data/scenes/all.json` (read only) and the three knowledge files the card names.
No tune is quoted from any other cue. `tools/melody_guard.py` run against every
other cue folder in the project reports the longest identical (interval, rhythm)
run at 4 and the highest 5-gram Jaccard at 0.0000 across 113 references; this
cue's own revisions (`pp_boarding_v2`, `pp_boarding_v3` and their humanized
renders) are skipped by the guard's lineage rule, because a revision is not an
independent reference.

## Files

| File | What it is |
| --- | --- |
| `build_pp_boarding.py` | writes the MIDI from note lists written in the file |
| `check_pp_boarding.py` | the card's checks, printed as one table, exit 1 on any failure |
| `pp_boarding.mid`, `.wav`, `.mp3`, `.ogg` | the cue, 16 bars, one shot |
| `hook_report.json` | `tools/hook_score.py` report, written by the renderer |
| `build_report.json` | bars, seconds, notes and voices per module |
| `check_output.txt` | the last full run of `check_pp_boarding.py` |

There is no `_loop.json` in this folder on purpose. The cue plays once, so no
loop point exists to give the bus.

## The length, and the one number that does not agree

16 bars at 120 bpm in 4/4 is 32.000 s. At 60 steps per second that is 1920 steps,
and 1920 steps is exactly the authored length of the gangway beat as the scene
card states it: "a gangway scene (the horn, the deck, the door, 32 s)" (t_a3fa132a).

The row in `data/scenes/all.json` prices at 539 steps. `check_pp_boarding.py`
prints both numbers, and it reads every constant out of
`game/scripts/pp_config/pp_config.gml` so a retired number cannot come back:

    2. length against the scene's authored step count
       music PP-05: 0 steps, its 30 step crossfade runs under the scene
       shake 40: 40 steps
       wait 120: 120 steps
       camera: 24 steps
       wait 90: 90 steps
       say ship_gangway: 173 steps (58 + 61 + 54)
       camera: 24 steps
       move 1 tiles at 8 a tile: 8 steps
       wait 60: 60 steps
       setflag: 0 steps
       end: 0 steps
       row today: 539 steps / 60 = 8.983 s
       beat sheet: 1920 steps / 60 = 32.000 s (card t_a3fa132a)
       module 32.000 s, difference 0.000 s, half a bar 1.000 s: PASS

366 of those steps belong to the commands: `shake` and each `wait` are their own
steps, a `camera` move is `PP_CAMERA_MOVE_STEPS` 24, a scripted `move` is
`PP_WALK_STEPS_RAIL` 8 a tile, `setflag` and `end` spend nothing, and `music`
spends nothing because its 30 step crossfade runs under the scene. The other 173
are the `say` floor from spec 05 rules 1 and 2: 2 steps a character, 3 after a
comma, 8 after a full stop, and the leading `* ` narration marker is not priced
because `tools/ai_bridge.py` draws it.

Earlier prints of this check said 282 steps for a 208 step row. Both were wrong:
the `say` priced at 0 (its lines live under `pages`, and the comma rule was
missing), a tile walked at the retired 12 steps, and `shake` and both `camera`
commands were unpriced. A number quoted on a card has to come from this print.

The 539 steps and the 1920 step beat do not have to agree: they measure different
clocks, because the `say` is player paced. Gamedev ruled that in
`knowledge/GAMEDEV-DECISIONS-2026-10-26.md` amendment D1a: the row is not padded
to 1920, and the cue hands back to PP-05 with spec 12 rule 4's 30 step crossfade.
No 16 to 24 bar cue could fit 539 steps at a playable tempo anyway: 16 bars in
539 steps is 0.561 s a bar, which is 428 bpm.

## The shape, four blocks of four bars

| Bars | What happens |
| --- | --- |
| 1 to 4 | the gangway, walking. The hook, then the hook again with the answer rewritten to hold B4. Bass drum only under bars 1 and 2, so the walk starts on the feet and the kit joins at bar 3 |
| 5 to 8 | over the water. The echo voice and the guide tone enter, the harmony opens to Dm, a changed answer closes on A, then a varied head and a rising bar that lands on a held E5, the dominant |
| 9 to 12 | the deck. The hook and the answer sequenced up a perfect fourth into D minor, the full kit with the crash on bar 9 and a tom fill at 12, then a climb that lands on E5 |
| 13 to 15 | the hatch, one held breath. The kit drops to rim ticks, the pad and the triangle hold E, the lead holds one E5 across bars 13 and 14 and then stops playing at all |
| 16 | the stop. One A minor stab on the downbeat held two beats, then two beats of air |

The bass is a march oom pah on the triangle, root on 1 and 3 and the fifth on 2
and 4, then a pedal E through the breath and a held A that stops.

## The hook

Two bars, eleven notes, A4 to E5 up and E4 down, twelve semitones in all:

    head    A4 B4 C5 D5 E5 E5    six notes, four steps up, the peak held
    answer  A4 G4 F4 E4 E4       five notes, the one leap down from E5 to A4,
                                 then steps to E4

Nine of the ten intervals are a step of one or two semitones, the single leap
larger than a fourth is E5 down to A4 and it sits at bar 2 beat 1 in every
statement, the phrase rises to one peak and falls (arch on all three returns),
and the E5 is repeated. The third statement is the same two cells up a perfect
fourth, so the sequence is transposition and not a new idea; the Bb4 in its
answer is the cue's one note outside A minor and it lands in G minor.

`tools/hook_score.py` through the renderer:

    90 of 100
    [ok ] motif returns 3, hook cell 6 notes with the rhythm 2/2/2/2/4/4 repeated 5 times
    [ok ] steps over leaps 90 percent (9 of 10 intervals) with 1 leap
    [ok ] contour 3 of 3 returns are an arch, variation on the third return 73 percent,
          range 17 semitones (64 to 81), 12 repeated pitches
    [fix] motif coverage 48 percent of 67 notes inside the motif
    [fix] loop length 0 of 6, because the melody track ends in bar 14

The two it marks are both true and both intended: bars 13 to 16 are the breath
and the stop rather than more hook, and a cue that plays once has no loop length
to score. The arrival cue carries the same two kinds of mark at 83.

## Drums

From `data/drum_patterns.json` by id, expanded with the mapping in
`knowledge/MUSIC-DRUMS.md` section 6 (noise period p becomes MIDI note p + 1,
`dpcm_kick` 36, `dpcm_snare` 38, a short loop hit sets CC12 to 1 at that tick).

MAR-04 bass drum only at bars 1 and 2 (the feet), MAR-01 march at 3, MAR-05
dotted pickup at 4, MAR-01 at 5, MAR-14 ghost sixteenths at 6, MAR-01 at 7, FLF-01
fill at 8, MAR-13 tutti with the crash at 9 (the one rung 5 in the cue), MAR-02
eighth snare rudiment at 10, MAR-01 at 11, FLT-01 tom sweep at 12, then CLM-02 rim
ticks at 13, 14 and 15. Bar 16 is hand written: one kick, one low noise wash on
the downbeat, nothing else.

Hard rules from section 4 hold: no two rung 3 bars touch (8 and 12), rung 5 once
(bar 9), and the three bar breath gets rungs 0 and 1 only.

## The stop, and why nothing is cut

Bar 16 is one stab on beat 1 and two beats of air. The last second of the render
measures a peak of minus 120 dBFS, which is the renderer's own silence, so the
file can end anywhere in the last beat and nothing is truncated. There is no loop
json, so nothing can ask the bus to repeat it. If gamedev wants the cue to end
harder, the lever is the release in bar 16, not the mix.

## Numbers measured by the check

- renders: mid 4273, wav 2822444, mp3 769296, ogg 387408 bytes
- wav 32.000 s at 44.1 kHz, 1411200 samples, 16 bars of 2.000 s
- peak minus 1.00 dBFS, rms minus 15.34 dBFS
- voices written: 8, 419 notes
- held breath: bars 13 and 14 have one lead note each and three other voices,
  bar 15 has no lead note and three voices; no broken chord, no echo and no guide
  tone sounds in any of the three
- stop: 0 notes start after beat 2 of bar 16
- long dashes in the folder's text: 0

## Q for gamedev (this card does not decide it)

1. **The scene row prices at 539 steps; the authored beat is 1920.** Gamedev ruled
   this in amendment D1a (`knowledge/GAMEDEV-DECISIONS-2026-10-26.md`): the two
   numbers measure different clocks because the `say` is player paced, the row is
   not padded, and the cue hands back to PP-05 with spec 12 rule 4's 30 step
   crossfade. Closed, and nothing is asked of this lane.
2. **Which cue plays after it.** The ship maps carry `PP-05` as their music. If
   PP-BOARDING is a stinger that hands back to PP-05, its stop in bar 16 gives the
   bus two beats to crossfade (30 steps). If it replaces PP-05 for the scene only,
   the row needs a fallback that is not this cue.
3. **The mix row.** Music is spec 12's 0.7 for every cue; this render is peak
   minus 1.00 and rms minus 15.34 dBFS, the same as the other landed cues. If the
   breath should sit under the deck's ambience, its own row is the lever, and
   `data/audio.json` is gamedev's file.

## How to rebuild

```
cd assets/audio/pp_boarding
python build_pp_boarding.py
python ../../../tools/render_chip.py pp_boarding.mid pp_boarding.wav --loop-bars 16 --hook-report hook_report.json
rm -f pp_boarding_loop.json
ffmpeg -y -i pp_boarding.wav -c:a libvorbis -q:a 5 pp_boarding.ogg
python check_pp_boarding.py | tee check_output.txt
```

`--loop-bars 16` is used as a length trim, not as a loop: it makes the renderer
hold the file to exactly 16 bars so the bar 16 air is inside the file. The loop
json it writes is deleted straight after, because this cue has no loop point.
