# PP-04 fight take F (pp_04_fight_baroque_v10): take E's fill moved into the subject's window

Musician lane, card t_9c3806a0 (AUTO-MUSIC-NEXT), 2026-11-14. Files here:

    pp_04_fight_baroque_v10.mid           the score take F; 100 / 100 on tools/hook_score.py
    pp_04_fight_baroque_v10.ogg           the delivered stream, rendered from that score
    pp_04_fight_baroque_v10.mp3           the same render, mp3 for review
    pp_04_fight_baroque_v10_master.wav    -14.10 LUFS / -0.60 dBTP
    pp_04_fight_baroque_v10_humanized.mid the humanize pass, kept beside the stream (88 / 100)
    hook_report.json                      the score of the delivered score
    hook_report_humanized.json            the score of the humanize pass
    pp_04_fight_baroque_v10_loop.json     the loop seam measurements
    build_report.json                     patch list, loudness, what was rendered from what
    build_pp_04_fight_v10.py              the whole build, rerunnable

## What changed, in one table

Take E (pp_04_fight_baroque_v8) measured 88 of 100 and lost 11.75 points on three criteria:

| criterion | take E | take F |
| --- | --- | --- |
| contour | 2.5 / 10, "1 of 4 returns arch or pedal" | 10.0 / 10, "4 of 4 returns (pedal pedal pedal pedal)" |
| leaps per motif | 4.0 / 8, 2 leaps | 8.0 / 8, 1 leap |
| steps over leaps | 11.75 / 12, 64% steps | 12.0 / 12, 91% steps |
| total | **88** | **100** |

The other seven criteria were already full and stay full: motif coverage 20/20 at 62%, motif
returns 12/12 at 4 returns, hook cell 10/10 (rhythm 2/2/2/2/2/8 repeated 4 times), variation
on the third return 8/8 at 75%, range 8/8 (12 semitones, 64 to 76), repeated pitch 6/6,
loop length 6/6 at 16 bars.

## The 12 notes that moved

The motif the scorer reads is the five pitch leitmotif FIGHT_SUBJECT (76 74 72 71 71) at bars
1, 5, 9 and 13, plus the seven note answer fill in the bar after each statement. The subject
is byte for byte untouched. Only the fill moved, in statements 1, 2 and 4:

    bar 2, 6 and 14 pitches   was 76 72 74 76 71 68 69   now 76 76 74 72 71 71 71

That moves the phrase back inside the subject's own five semitone window (71 to 76), leaves
one leap (the step onto E5 at the top), makes every other interval a step, and lands the held
note on the B4 the subject already holds. Statement 3 keeps the score's own varied tail
(76 72 74 76 71 71 72), so the third return still differs from the first by 25 percent and
still reads pedal.

Twelve note events changed (a note on and its own note off per changed pitch, at three
statements). No duration, velocity, channel, drum figure or other bar moved: the patch is
byte level on the pulse 1 track of take E's score, and take E's midi sha256 is still
002f979d23732a5aaee95634c7b24d812fb38af09697e759e01c0443e7788f61.

## Loop seam

Same renderer settings as take E (renderer v2, 16 bar loop, 44100 Hz mono):

    loop_seam_sample_difference 0        (take E: 0)
    loop_edge_peak_head 2283             (take E: 2283)
    loop_edge_peak_tail 894              (take E: 894)
    loop_edge_max_jump 499               (take E: 499)

Identical, because bars 15 and 16 and the loop tail are take E's. No seam was introduced.

## Humanize, and why it is beside the stream and not under it

The humanize pass is a real artefact here (pp_04_fight_baroque_v10_humanized.mid, 5994 bytes)
and it measures 88 of 100: its ornaments and grace notes give the melody 81 notes instead of
78, and the motif finder then prefers an 11 note window from bar 6 with 3 returns at 47
percent coverage. That is the same trade card t_50cbadb5 documented for take E, so the
delivered stream is rendered from the plain score: what scores is what plays.

## Ear loop

tools/ear_critic.py needs GEMINI_API_KEY. It is unset in this session (os.environ only, no
file was opened), so zero of the four ear rounds ran. Same wall as cards t_50cbadb5,
t_160851e2, t_1f112e10 and t_6f6882cd. Q: for gamedev, third repeat: is the ear key meant to
be exported into musician sessions, or are the ear rounds expected to be skipped when it is
not?
