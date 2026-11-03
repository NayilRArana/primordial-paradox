# PP-04 fight cue, take C, round 1 (`pp_04_fight_baroque_v3`)

Card AUTO-MUSIC-NEXT (`t_ff00a640`). This is round 1 of take C: the same score as
`../pp_04_fight_baroque_v4/`, rendered without round 2's changes. It is kept because the card says
to keep the previous version, and because the score table in `../pp_04_fight_baroque_v4/NOTES.md`
lists its ear row next to v2's and v4's.

Round 2 changed three things in `tools/counterpoint/m3_cues.py` and `m3_build.py`: the off-beat
eighths are swung a 16th late, bars 4, 8 and 12 close with a four hit 32nd roll instead of a two hit
fill, and the render gained a pulse 1 duty change at bar 9 plus a delayed vibrato on the triangle.
The score is otherwise identical, so hook score is the same 87 of 100 as v4.
