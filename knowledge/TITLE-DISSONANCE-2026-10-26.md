# PP-01 "Title Theme": the title dissonance, measured (musician, 2026-10-26, card t_c0597404 / M0)

Nayil's note was that v7 and v8 "are a bit dissonant" and that the music should manage "more
sophisticated stuff like counterpoint, actual Baroque techniques". This is the measurement behind that
note, done symbolically because the ear critic still scored v7 and v8 highest: it hears the mix, so
something else has to count the intervals. Then `assets/audio/pp_01_title_v9/` is the build that acts on
the count, with the ear critic run before and after.

Everything below is produced by code in `tools/counterpoint/`, pinned by `tests/test_clash.py`,
`test_repair.py`, `test_keycheck.py`, `test_analyze.py` and `test_build_pp01_v9.py`, and can be re-run:

    python tools/counterpoint/analyze.py assets/audio/pp_01_title_v7/pp_01_title_v7.mid --json out.json
    python tools/counterpoint/analyze.py FILE --voices "pulse 1,pulse 2,triangle"
    python tools/counterpoint/analyze.py assets/audio/pp_01_title_v8/pp_01_title_v8.mid --added-from assets/audio/pp_01_title_v7/pp_01_title_v7.mid
    python tools/counterpoint/keycheck.py FILE [FILE ...]
    python assets/audio/pp_01_title_v9/build_pp01_v9.py

## The rules the count is made with

`tools/counterpoint/clash.py`. The choices that decide the numbers, and why each was made:

- **Every sounding pair, at every articulation, not outer voices only.** The plan names the outer voice
  rule for parallels; for clashes every pair counts, because a major second between the arpeggio and the
  pad is heard as one note wrong, whoever the outer voices are.
- **A perfect fourth is consonant except above the lowest sounding note**, where the classic rule
  applies (dissonant unless a third or a sixth sits above the bass). A fourth between two upper voices is
  a chord member, and counting it would be counting triad spacings, not clashes.
- **Onsets snap to the sixteenth grid.** Measured first: every onset in v7 sits within 19 ticks of that
  grid and the pad's strum spreads one chord across 14 ticks, so snapping merges a rolled triad without
  moving a rhythm.
- **The chord is read from the pad and the bass together**, because between them they state it, and a
  resolution landing on any chord member is accepted.
- **A suspension is the UPPER voice held while the bass moves.** A bass that sits still under a moving
  soprano is a pedal, not a suspension. This matters: before the rule was written that way, 5 of v7's
  "suspensions" were the bass stepping down while the melody moved, which is not a device at all.
- **A dissonance is a device when** it is prepared and resolves down by step (suspension), or sits on the
  downbeat and resolves by step (appoggiatura), or is entered and left by step off the beat (passing or
  neighbour), or when it is the next chord's tone arriving an eighth early and held across the bar line
  (anticipation, the injector's DIS-09 family). **Everything else is a raw clash.** Beat 2 of the waltz
  may carry a passing tone; only the downbeat is reserved for the appoggiatura.
- **An anticipation is judged against the chord the bass implies, not only the notes the pad doubles**,
  because the pad is often two notes and the trio has no pad at all. Without that, the echo's early
  arrivals counted as clashes.

## The clash table, card scope: pulse 1, pulse 2 and the triangle

| class | v7 | v8 | v9 |
| --- | --- | --- | --- |
| suspension | 0 | 0 | 0 |
| appoggiatura | 13 | 14 | 8 |
| passing | 2 | 2 | 0 |
| neighbour | 0 | 0 | 2 |
| anticipation | 11 | 11 | 6 |
| **raw clash** | **26** | **30** | **0** |
| of those, on the downbeat | 8 | 10 | **0** |
| dissonances judged | 52 | 57 | 16 |

Raw clashes per 8 bars, card scope:

| bars | v7 | v8 | v9 |
| --- | --- | --- | --- |
| 1 to 8 | 0 | 0 | 0 |
| 9 to 16 | 4 | 4 | 0 |
| 17 to 24 | 5 | 5 | 0 |
| 25 to 32 | 9 | 9 | 0 |
| 33 to 40 | 1 | 1 | 0 |
| 41 to 48 | 4 | 8 | 0 |
| 49 to 52 | 3 | 3 | 0 |

There is no suspension anywhere in the three 2A03 voices in v7 or v8: the injector's suspension went to
`vrc6 pulse b`, which is not one of these three voices. That is why the card's scope alone would have
missed the device it wrote.

## The same count over all six pitched voices

The three voice scope is where the plan's trio sonata idea lives, but the pad and the counter line are
the other half of what the ear hears, so the same rules were run over all six. Per file JSON with every
event is in `assets/audio/pp_01_title_v9/clash_v7.json`, `clash_v8.json`, `clash_v9.json`.

| class | v7 | v8 | v9 |
| --- | --- | --- | --- |
| suspension | 25 | 25 | 15 |
| appoggiatura | 25 | 26 | 15 |
| passing | 41 | 41 | 20 |
| neighbour | 6 | 6 | 5 |
| anticipation | 19 | 19 | 18 |
| **raw clash** | **196** | **204** | **2** |
| of those, on the downbeat | 30 | 35 | **0** |
| dissonances judged | 312 | 321 | 75 |

Raw clashes per 8 bars, six voices: v7 6, 44, 25, 44, 35, 22, 20; v8 6, 44, 25, 44, 35, 30, 20; v9 0, 0,
0, 0, 0, 2, 0.

By voice pair in v7, the worst five: melody against pad 32, arpeggio against pad 26, arpeggio against
melody 20, arpeggio against counter 19, counter against pad 17. Per voice, counting every clash the voice
is part of: melody 85, pad 84, arpeggio 84, counter 61, echo 50, bass 28. By interval: major second 68,
tritone 47, major seventh 30, minor second 26, minor seventh 23, perfect fourth 2. The tritone count is
the one that reads as a wrong note rather than as colour. By beat: 59 weak, 55 offbeat, 52 on beat 2, 30
on the downbeat, which is why an ear judging the mix does not flag them: most last an eighth and pass. By
section: intro bars 1 to 8, 6; bars 9 to 24, 69; bars 25 to 40, 79; bars 41 to 52, 42. The worst single
bars are 27 (17), 34 (14) and 11 (12).

The commonest single reason a clash is raw is "the upper voice arrives over a held note" (74 events plus
22 on beat 2): a line landing on a non-chord tone against a pad that does not move. That is the texture
problem in one sentence.

## Which clashes the injector added

`build_pp01_v7.py` writes two devices, and the rules file defines both.

**DIS-04, suspension 4 to 3, bars 38 to 39, `vrc6 pulse b`.** The build writes E5 (76) from bar 38 to bar
39 beat 2 and resolves to D#5 (75). The analyser calls it a **suspension**, twice, at bar 39 beat 1
against the bass (a fourth above B2) and at bar 39 beat 1.5 against the arpeggio. The device works and the
count agrees with it. This is the one place where the injector and the checker clearly agree.

**DIS-09, anticipation of the next chord's third, bar 36 last eighth, `vrc6 pulse a`.** The build writes
G4 (67) on the last eighth of bar 36, on the reasoning that G is the third of the trio's Em in bar 37. The
analyser does **not** call it an anticipation: bar 36's own pad sounds G#3, and the melody's G4 against it
is a major seventh and a semitone contradiction at the same time. It is therefore one of the bar 36 raw
clashes, and one of them sits on the downbeat. The rule's trigger was satisfied ("a semitone or a tone
from the melody note"), but nothing looked at what the bar being left already sounds. That is the concrete
answer to "which clashes the injector added", and a defect to fix in the checker (M1a).

**DIS-21, pedal tone, bars 43 and 44, v8.** v8's only pitched change. It removes the moving bass line and
holds A2. In the six voice count v8's extra 8 raw clashes are all in block 6 (bars 41 to 48: 22 to 30) and
0 of them involve a note v8 added (`--added-from` reports 0 of 204), which is the interesting part: the
pedal does not add a wrong note, it removes the note that made the chord read as a chord, so pairs that
were consonant as chord members become raw. A device that "just holds a pedal" is not neutral to this
count.

## Cross relations and notes outside the key

`tools/counterpoint/keycheck.py`. The key is A minor with G# available as the leading tone, so G# is not
reported as outside the key.

| | v7 | v8 | v9 |
| --- | --- | --- | --- |
| notes outside the key | 17 | 17 | 12 |
| cross relations, within an octave | 64 | 65 | 30 |
| cross relations, any span | 166 | 169 | 77 |

The out of key notes are not scattered: they are the B7 and C# material of the trio and bars 41 to 42
(F#4 and D#4 in the arpeggio, D#5 and F#5 in the melody at bar 39, A#4 at bar 42, A#5 in the counter line
at bar 13). That is chromatic harmony doing its job, not a bug, and it is listed so nobody "corrects" it
later. The cross relations are a real smell: the most common shape is a G in the bass or triangle against
a G# in the pad, then the echo's G#4 against the melody's A4.

## The v9 build

`assets/audio/pp_01_title_v9/`, built by `build_pp01_v9.py`, which reads v7 and writes a new file. v7 and
v8 are untouched.

| | v7 | v9 |
| --- | --- | --- |
| raw clash, six voices | 196 | 2 |
| raw clash, card scope | 26 | 0 |
| on the downbeat, either scope | 30 and 8 | **0 and 0** |
| devices kept | 116 | 73 |
| melody and drums | | identical, note for note |
| hook meter | 83 of 100 | 83 of 100 |

216 edits, 23 notes dropped, 6 whole pad chords re-voiced, mean movement 0.5 to 1.6 semitones per voice,
234 of 287 arpeggio notes, 101 of 121 pad notes and 100 of 114 bass notes untouched. Two raw clashes
remain, at bars 41 and 42 beat 2, the melody's C#5 and G#4 against the pad's D3: the pad cannot leave D
without leaving a triad, and no triad containing the melody note fitted there. They are recorded, not
hidden.

The build is deterministic: two runs write the same file.

The loop: `pp_01_title_v9_loop.json`, 52 bars, 74.286 s, loop from bar 5, seam sample difference 0, peak
-1.00 dBFS, RMS -17.40 dBFS.

## The ear, before and after

One call, one judge (`gemini-3.5-flash`), v7 and v9 back to back so the two numbers are comparable to each
other. **The call ran on the first build of v9**, before the anticipation rule was widened and before the
pedal fix, which is a few edits heavier than the file shipped; the free tier quota (20 requests a day) was
exhausted by that call, so the shipped build could not be re-scored the same day.

| file | hook | drums | tension | human | variety | structure | total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v7 | 8 | 6 | 7 | 5 | 8 | 7 | **41** |
| v9 | 5 | 7 | 5 | 6 | 5 | 5 | **33** |

Review: `assets/audio/ear_reviews/compare_pp_01_title_v7_pp_01_title_v9_20261026T190437Z.md`. The judge
prefers v7 by 8 points, well outside its own 1 point per criterion noise floor, and says why: v7's lead
cuts above the accompaniment, v9's blends into it. That is the honest cost of the repair, and it is the
finding to act on. The goal is not zero clashes; it is every clash prepared and resolved. A build that
keeps the v7 pitch and delays the accompaniment's move would keep the bite with a preparation in front of
it and a resolution behind it, and the analyser already labels what that needs.

## What the next cards should take from this

- The card scope of three voices undercounts: the pad and the counter line are in 128 of v7's 196 raw
  clashes. A checker that only watches pulse 1, pulse 2 and the triangle will pass a score the ear finds
  dissonant.
- Most clashes are not an interval choice, they are a texture choice: a moving line over a pad that does
  not move. Fixing the pad's rhythm would remove them without touching a single melody note.
- An anticipation rule has to look at the chord being left, not only the chord being entered, or it
  certifies exactly the cross relation DIS-09 created.
- A pedal tone is not neutral: it changes what the chord is read as, and v8 pays 8 raw clashes for it.
- Removing clashes costs the hook its edge when the fix is consonance. The next title build should fix by
  preparation and resolution instead.
