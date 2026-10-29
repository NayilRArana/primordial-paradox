# Two-state cues, the PP-04 fight row, and the 168 against 176 against 126 tempo lines

Card t_279ef225, gamedev ruling, 2026-10-29. Measured at HEAD `e56f9e94` in
`<repo>`. Builds on ruling D3
(`knowledge/GAMEDEV-DECISIONS-2026-10-26.md`) and on `knowledge/MUSIC-CUE-LEDGER-2026-10-26.md`
section 8, which already separated the row's tempo from the candidate lane's.

Question asked by the musician (card AUTO-MUSIC-NEXT t_47a92d70): does the fight row become
`pp_fight_v2`, which state does the director cut between, and is it 126 or 168 bpm.

## Ruling, one line

No v2 and no states. `data/audio.json` `PP-04` keeps
`assets/audio/pp_04_navy_sailors_master1/pp_04_navy_sailors_master1.ogg` (43.636349 s, 176 bpm,
32 bars), the fight row stays one file with `loop: true`, and the candidate fight lane stays at
**168 bpm**. Neither number moves on this card.

## The tempo, stated three ways because three numbers are in play

* The file PP-04 names is at **176.0 bpm** (`pp_04_navy_sailors_master1_loop.json`, quoted in
  `knowledge/MUSIC-CUE-LEDGER-2026-10-26.md` section 8), 32 bars, loop bars 1 to 28 with a four bar
  tail. D3's sentence "the battle cue stays 168 bpm" is true of the `pp_fight` family, which no row
  names, and is not a measurement of the shipped row. The ledger says the same thing; this note
  does not change it.
* The candidate lane (`pp_fight_v2` through `v6`, `pp_04_fight_baroque_v1` and `_v2`) is at
  **168 bpm**, 16 bars, 22.857143 s per state, which is the CUE-FIGHT card's number
  (`assets/audio/pp_fight/NOTES.md` line 26). 168 is what makes one state's bar 16 land tick for
  tick on the other's bar 1.
* **126 is the waltz family, not the battle.** `assets/audio/pp_04_navy_sailors_v3/NOTES.md:73-75`
  says it plainly: the card's "126 bpm family" is the waltz family (PP-01 is the 126), and PP-04 is
  the fight cue whose 45 to 60 s fight is timed on 176. So the AUTO-MUSIC-NEXT brief's 126 line was
  never a battle instruction. Against that, 168 in the candidate lane stands because the CUE-FIGHT
  card sets it, and moving to 126 would cost the state seam and 30.476 s per state.

If a 168 take is ever promoted onto PP-04, the row's tempo changes from 176 to 168 and anything
timed on 176 has to be re-checked on the promoting card. That cost is real and belongs to that
card, not this one.

## Why not v2, in file terms

`assets/audio/pp_fight_v2/` is four takes old: v3, v4, v5, v6 followed it, and on 2026-10-29
`pp_04_fight_baroque_v1` and `_v2` (card M3 BAROQUE-CUES t_65512e1c) landed two more candidates at
168 bpm, 16 bars, 22.857143 s each (ffprobe, this session).

v2 is the only two-state take with OGGs. `assets/audio/pp_fight_v6/` ships MIDI, MP3 and WAV only
and no OGG, so v6 cannot be wired at all: the bus streams OGG through `audio_create_stream`
(`game/scripts/pp_audio/pp_audio.gml:229`). A take becomes the cue when a row's `delivered_file`
names its OGG, on a forward card; nothing else promotes it.

## Why no states, in code terms

* One file per cue. `pp_audio_music(_cue, _fade_steps)` resolves `_entry.asset` to one path
  (`pp_audio.gml:190-210`) and streams it. There is no second path, no state selector, no
  alternate.
* One music source at a time. The incoming stream starts and the outgoing one is handed to the
  same fade (`pp_audio.gml:244`, header comment 185-189). A repeat request for the cue already
  playing is ignored (`pp_audio.gml:199`).
* The fade is 30 steps at 16.6667 ms per step (`pp_audio.gml:42`, `pp_audio.gml:51`), which is
  500 ms. The shortest cut the function will make is `pp_audio_music(cue, 1)`, 16.7 ms.
* `loop` is read from the row (`pp_audio.gml:226-227`). The row fields the bus reads are `id`,
  `asset`, `delivered_file`, `loop`, `boss`, `placeholder_sound` and `volume`. No other key is
  consulted, and `grep -c '"states"' data/audio.json` returns 0.
* Music is requested in exactly one place: the scene `music` command
  (`game/scripts/pp_scene/pp_scene.gml:276`). The battle director never asks for music; its six
  `pp_audio` calls are the hit and menu sounds (`pp_battle_director.gml:612, 725, 735, 756, 759,
  769`). There is therefore no director that could cut between two states of a fight cue.

So "which state does the director cut between" has one answer today: none exists. A two-state cue
would need a caller that switches, which means a scene command change, and the 500 ms crossfade
would smear the tick-for-tick seam anyway unless the call passes `fade_steps = 1`.

The cheap shape, if a two-state cue is ever wanted, is two cue rows (PP-04 and a second id) and a
scene command that picks between them: two rows, no schema change, no bus change. It still cuts on
a step, not on a bar line.

## The bar line, in steps

The step clock is 60 Hz (`PP_AUDIO_STEP_MS` 16.6667). At 168 bpm in 4/4 one bar is
4 x (60 / 168) = 1.428571 s = 85.714 steps, which is not a whole number. Whole step bar lines at
168 are bars 7, 14, 21 and 28 only; 7 bars is 10.000 s, which is 600 steps at 60 Hz.

Consequence: the tick-for-tick seam is a property of the two files and is worth keeping, because it
lets a 500 ms crossfade land inside the music. It is not something the engine can execute as a cut
on an arbitrary bar line at 168. If a bar-locked call ever becomes a requirement, the tempos near
168 that put every bar on a step are 180 bpm (bar 1.3333 s, 80 steps) and 144 bpm (bar 1.6667 s,
100 steps). Do not move 168 for a cut the bus does not make. At the row's 176 bpm a bar is
1.363636 s = 81.818 steps, whole step bar lines are bars 11 and 22 only, and 11 bars is 15.000 s,
900 steps at 60 Hz.

## The trade (unchanged from D3)

The hook meter wins. If the fight state reads static, the fix is more instrumental variation in the
second half (the break at bars 9 and 10, the noise timbre per phrase, the drum rungs, the counterline
from bar 5), never a second melody.

## Promotion, as one line plus its note

| candidate | OGG | tempo, bars | length | named by a row |
| --- | --- | --- | --- | --- |
| `pp_04_navy_sailors_master1` | yes | 176, 32 (loop 1 to 28) | 43.636349 s | yes, PP-04 |
| `pp_fight_v2` fight and calm | yes | 168, 16 each | 22.857143 s each | no |
| `pp_fight_v6` fight and calm | no | 168, 16 each | n/a | no, cannot stream |
| `pp_04_fight_baroque_v1` | yes | 168, 16 | 22.857143 s | no |
| `pp_04_fight_baroque_v2` | yes | 168, 16 | 22.857143 s | no |

Nothing in `assets/audio/` or `data/audio.json` was changed by this ruling.
