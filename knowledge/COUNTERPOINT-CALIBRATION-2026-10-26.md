# Counterpoint calibration: the free Baroque profile measured on Bach

Card t_836dbb1a, written 2026-10-26 by the audit lane. The machine readable twin is
`tools/counterpoint/calibration.json`, the corpus record is
`tools/counterpoint/corpus.json`, and the engine is `tools/counterpoint/rules.py`.

## What was measured

20 Bach works, 8913 notes: 4 under Creative Commons Attribution-ShareAlike 3.0, 16 under Public Domain. The MIDI files are NOT in this repository:
they live in `<workspace>/corpora/bach-counterpoint/midi`, and the manifest records each source URL, the licence as the
source states it, and the SHA-256 that was measured. Nothing melodic is copied here;
the numbers are counts of rule violations.

The key in the last column is detected from note durations by `detect_key()`, not read
from the file, and it is printed so a reader can disagree with it by name.

| work | catalogue | licence | notes | bars | key detected |
| --- | --- | --- | --- | --- | --- |
| Aus meines Herzens Grunde | BWV 269 | Public Domain | 137 | 21 | G major |
| Chorale setting (title not in the source) | BWV 510 | Public Domain | 93 | 23 | F major |
| Chorale setting (title not in the source) | BWV 511 | Public Domain | 125 | 10 | G minor |
| Chorale setting (title not in the source) | BWV 512 | Public Domain | 135 | 10 | E minor |
| Invention 1 | BWV 772 | Creative Commons Attribution-ShareAlike 3.0 | 455 | 22 | C major |
| Invention 2 | BWV 773 | Public Domain | 634 | 27 | G minor |
| Invention 3 | BWV 774 | Public Domain | 495 | 59 | D major |
| Invention 4 | BWV 775 | Public Domain | 443 | 52 | D minor |
| Invention 5 | BWV 776 | Public Domain | 734 | 32 | Eb major |
| Invention 6 | BWV 777 | Creative Commons Attribution-ShareAlike 3.0 | 547 | 62 | E major |
| Invention 7 | BWV 778 | Public Domain | 473 | 23 | E minor |
| Invention 08 | BWV 779 | Public Domain | 596 | 34 | F major |
| Invention 9 | BWV 780 | Creative Commons Attribution-ShareAlike 3.0 | 558 | 34 | F minor |
| Invention 10 | BWV 781 | Public Domain | 439 | 32 | G major |
| Invention 11 | BWV 782 | Public Domain | 568 | 23 | G minor |
| Invention 12 | BWV 783 | Creative Commons Attribution-ShareAlike 3.0 | 685 | 21 | A major |
| Invention 13 | BWV 784 | Public Domain | 564 | 25 | A minor |
| Invention 14 | BWV 785 | Public Domain | 592 | 20 | Bb major |
| Invention 15 | BWV 786 | Public Domain | 477 | 22 | B minor |
| Chorale prelude “Wer nur den lieben Gott läßt walten” | BWV Anh. 691 | Public Domain | 163 | 9 | A minor |

## The table

Rates are violations per 100 notes across the whole corpus work. `works` is how many
of the 20 works show the rule at least once.

| rule | what it catches | severity (free) | mean | max | works | budget |
| --- | --- | --- | --- | --- | --- | --- |
| CP-01 | dissonance on an accented beat, unprepared or unresolved | hard | 0.28 | 1.42 | 12 | 2.84 |
| CP-02 | dissonance on a weak beat that is not a passing or neighbour tone | hard | 0.39 | 4.29 | 7 | 8.59 |
| CP-04 | suspension not resolved down by step | hard | 0.18 | 1.24 | 10 | 2.48 |
| CP-05 | suspension figure outside 4-3, 7-6, 9-8, 2-3 | style | 0.06 | 0.61 | 2 | 1.23 |
| CP-06 | appoggiatura | style | 2.01 | 4.83 | 18 | 9.67 |
| CP-07 | passing tone entered or left by leap | hard | 0.69 | 2.84 | 11 | 5.67 |
| CP-08 | neighbour tone that does not return | soft | 0.01 | 0.21 | 1 | 0.42 |
| CP-09 | parallel perfect fifth or octave | hard | 0.01 | 0.14 | 1 | 0.27 |
| CP-10 | hidden (direct) perfect fifth or octave | soft | 0.51 | 1.46 | 16 | 2.92 |
| CP-11 | leading tone not resolved up to the tonic | soft | 0.85 | 2.63 | 16 | 5.25 |
| CP-12 | chordal seventh not resolved down by step | soft | 1.21 | 3.40 | 16 | 6.81 |
| CP-13 | voice crossing | soft | 0.04 | 0.21 | 5 | 0.42 |
| CP-14 | voice overlap | soft | 0.04 | 0.21 | 5 | 0.42 |
| CP-15 | spacing wider than an octave between upper voices | soft | 0.00 | 0.00 | 0 | 0.25 |
| CP-16 | two leaps in the same direction (an unshaped line) | style | 0.72 | 3.37 | 15 | 6.74 |
| CP-17 | note outside the voice's NES range | hard | 0.00 | 0.00 | 0 | 0.25 |
| CP-18 | escape tone (a stepwise dissonance left by leap) | style | 1.15 | 4.36 | 17 | 8.72 |

## The budget rule

`budget = 2 x the highest rate any work shows`, and `0.25` per 100 notes for a rule Bach never
breaks. The second number exists because a rule with a corpus maximum of zero would
otherwise forbid a single slip in a four hundred note cue, which is not what the
numbers can support: the corpus is two voices and a cue is five or six, and a rule
that needs a chord to be judged cannot fire the same way in both.

## How to use it

    python tools/counterpoint/check.py CUE.mid            # compares with this table
    python tools/counterpoint/calibrate.py --corpus DIR    # rebuild this table

`check.py` compares each rule with its own budget and fails only when a rule is over it.
A cue over budget on one rule is not automatically wrong; it is a cue whose texture
does something this corpus does not, and the report names the bar, the beat and the
notes so the musician lane can decide whether it was intended.

## What this cannot do

- There are no chord symbols. Consonance is judged from the interval classes plus two
  exceptions (a fourth above the bass is consonant in a 6/4 chord; a real seventh above
  the bass is a chordal seventh), so a note that is a chord tone in a rich cue can be
  read as a dissonance. The cue report is a list to read, not a verdict to obey.
- The corpus is two voices and a six voice cue is not. Parallells and hidden perfects are
  therefore restricted to the outer voices, as the card says, because inner voices in a
  chip texture double each other on purpose.
- A held note that is the bass is treated as a pedal and is not asked to resolve; the
  moving voices carry the finding. Without that exception every bass pedal note became a
  failed suspension and the finding named the wrong voice: a long bass note that the
  upper voices move against was reported as a suspension the bass failed to resolve.
- CP-15 and CP-17 never fire here: two-part keyboard music has no upper-voice spacing and
  no NES register. Their budget is the floor below, and they are measured on the cue.
- Each pair of notes is judged once, at the instant it first becomes dissonant, so a
  dissonance that later changes its role is not re-judged. A held note that was already
  dissonant when it began is judged at that attack, which is why there is no separate
  rule for an unprepared suspension: unprepared is what CP-01 and CP-02 already say.
