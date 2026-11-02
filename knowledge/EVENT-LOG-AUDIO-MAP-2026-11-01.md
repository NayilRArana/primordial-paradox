# Event log to OGG map, 2026-11-01

Card t_37855a33 (DEMO-AUDIO-CAPTURE, the mapping child, gamedev). Node CitadelArana, the desktop.

What this file answers in one sentence: for every line the game can write into its own audio log, which real
`.ogg` on disk is that sound, at what gain the game played it, and where the beat of the title theme sits.

The machine readable twin is `knowledge/EVENT-LOG-AUDIO-MAP-2026-11-01.json`. It is built from the game's data
and measured from the files, not typed, and it is what a renderer should read. This page is the reading of it.
A sample of real log lines to work from is `knowledge/EVENT-LOG-SAMPLE-2026-11-01.txt`, copied verbatim from
four runs whose paths are named in its header.

## 0. The commands

    python tools/event_audio_map.py --check
    python tools/event_audio_map.py --plan  knowledge/EVENT-LOG-SAMPLE-2026-11-01.txt
    python tools/event_audio_map.py --render knowledge/EVENT-LOG-SAMPLE-2026-11-01.txt out.m4a --uniform-seconds 12
    python tools/event_audio_map.py --build      (rewrites the JSON from data/audio.json, sfx.json and the gml)
    python tools/event_audio_map.py --fixture    (rewrites the sample log from the four source logs)

`--check` is the gate: it re-parses the `PP_AUDIO_*` macros out of `game/scripts/pp_audio/pp_audio.gml`,
re-measures every file, re-reads the title theme ledger, and fails if any number in the map has drifted, if a
message site in the bus has no row, or if a real log line classifies to no row. It exits 0 only when the map is
usable by someone who has never seen it.

## 1. How one log line becomes sound

1. The game asks the bus for a name, never a file: `pp_audio_play("footstep")`, `pp_audio_sfx("sfx", id)`,
   `pp_audio_blip(speaker)`, or `pp_audio_music("PP-04", 30)`.
2. The bus writes one `PP audio:` line, in the shape the table below names.
3. The map says what that shape means: start music, stop it, change its gain, play one effect, or no sound.
4. The map names the file and the gain. Music is the OGG `data/audio.json` names in `delivered_file`, streamed
   from the build's flattening of it (`game/datafiles/streams/<leaf>`). An effect is
   `assets/audio/sfx/<id>.ogg`, the delivered original of the `game/datafiles/sfx/<id>.wav` the game loads.

A renderer that gets those four steps right never guesses: no row of the map is a name that has to be
interpreted, and the plan for a real log leaves nothing unresolved.

## 2. The clock, which the log does not carry

The log line has no timestamp and no step offset. Two honest clocks exist, and the map records both:

- the capture harness's arrival stamp. `tools/play_demo.py` (`LogAudioWatch`) polls the log every 0.05 s and
  places each line at the second it read it, so a placed second is accurate to 0.05 s; lines already in the
  file when the watch starts are placed at 0.0, which is where the title theme is, because it streams at boot.
- a scripted run's own step clock. The line is written in the step the game played the sound, so a step offset
  from the demo script bounds it to one 1/60 s step, but the log itself does not say which step.

The rule that follows: a renderer with no harness stamps may place the lines in their written order and must
not invent spacing. The proof render in section 8 does exactly that and says so in a JSON beside its output.

## 3. The gains the game actually applies

| what | gain | where it comes from |
| --- | --- | --- |
| music, cue and theme | 0.7 | `PP_AUDIO_GAIN_MUSIC`, printed on the theme's own start line |
| music fade in and out | 0.5 s (30 steps of 16.6667 ms) | `PP_AUDIO_FADE_STEPS * PP_AUDIO_STEP_MS` |
| effect through `pp_audio_sfx` (a scene command) | 0.9 | `PP_AUDIO_GAIN_SFX` |
| effect through `pp_audio_play` (footsteps, menus, doors, thunder, the engine, the swoosh) | 1.0 | the gain argument is left off; the manual's `audio_play_sound` page says gain defaults to 1 (read 2026-11-01) |
| a text blip | 0.45 | `PP_AUDIO_GAIN_SFX * PP_AUDIO_GAIN_BLIP`, applied on the instance the same step |
| priorities | music 10, boss 12, effect 5, blip 4, 10 channels | the same macros |

The log prints a gain on the theme's start line and on the duck line, and nowhere else. So for an effect the
map gives the level of the call path that plays that id (measured by grepping the call sites) and, for the ids
that more than one path can reach, the other candidate: the two are 0.9 dB apart. The map marks that per id as
`gain_alternatives` and says so in `gain_note`. That is the honest limit of what a log line can tell you.

## 4. The thirty events

Ten of these rows make or change a sound (two starts, one effect, three stops, two gain changes, one pause and
one resume), and twenty mean the game was silent. A renderer places nothing for the last group.

| type | what a renderer does | sample lines | source |
| --- | --- | --- | --- |
| `no_manifest` | the effect manifest is missing, so every effect in the run is silent | unobserved | `pp_audio.gml:77` |
| `no_cue_table` | the music table is missing, so every cue in the run is silent | unobserved | `pp_audio.gml:130` |
| `focus_lost` | the window lost focus: the music is paused and every effect is stopped | 4 | `pp_audio.gml:412` |
| `focus_back` | focus is back: the music resumes from the paused position | 3 | `pp_audio.gml:417` |
| `theme_handed` | a cue is starting: the theme fades out over the bus fade and the cue takes the slot | 2 | `pp_audio.gml:217` |
| `theme_stopping` | the theme fades out over the printed number of steps and stops | unobserved | `pp_audio.gml:337` |
| `music_stopping` | the cue fades out over the printed number of steps and stops | unobserved | `pp_audio.gml:344` |
| `theme_stream` | the title theme starts from the named stream at the printed gain, looped | 4 | `pp_audio.gml:567` |
| `theme_ducked_state` | a duck level is recorded for the next theme start; nothing is playing to turn down | unobserved | `pp_audio.gml:647` |
| `theme_ducked` | the theme's gain changes to the printed number right now | 2 | `pp_audio.gml:654` |
| `theme_unducked` | the theme's gain goes back to the bus music level | 1 | `pp_audio.gml:667` |
| `music_stream` | a music cue starts from the named file at the bus music level, looped, fading in | 8 | `pp_audio.gml:322` |
| `music_fallback` | the asked cue has no file, so the bus asked for the fallback; the next start line is the sound | unobserved | `pp_audio.gml:267` |
| `music_missing` | the cue has no file where the game looks: silence, and the game plays no music here | 3 | `pp_audio.gml:286` |
| `music_stream_failed` | the file is there and the stream would not open: silence | unobserved | `pp_audio.gml:304` |
| `music_no_channel` | no audio channel was free at the music priority: silence | unobserved | `pp_audio.gml:311` |
| `music_unknown` | a cue id the table does not know: silence | unobserved | `pp_audio.gml:257` |
| `sfx_not_in_manifest` | the effect is not in the manifest: silence | unobserved | `pp_audio.gml:362` |
| `sfx_loaded` | the effect file was read into a buffer: no sound yet, the play line is the sound | 15 | `pp_audio.gml:539` |
| `sfx_no_file` | the effect file is missing: silence | unobserved | `pp_audio.gml:501` |
| `sfx_buffer_failed` | the effect file would not load: silence | unobserved | `pp_audio.gml:507` |
| `sfx_length_bad` | the manifest's measured length does not fit the file: silence | unobserved | `pp_audio.gml:517` |
| `sfx_create_failed` | the buffer sound would not be created: silence | unobserved | `pp_audio.gml:531` |
| `sfx_played` | one effect plays once, at the level of the bus path that asked for it | 324 | `pp_audio.gml:381, pp_audio.gml:611` |
| `sfx_silent_manifest` | an effect the cue list knows but the manifest does not ship: silence | 1 | `pp_audio.gml:600` |
| `cue_unknown_name` | a name that is not an effect at all: silence | 1 | `pp_audio.gml:592` |
| `room_no_cue` | the room names no cue: whatever music is playing keeps playing | unobserved | `pp_audio.gml:448` |
| `room_asked` | the room asked for a cue; the start line above or below is the sound, this line is the verdict | 10 | `pp_audio.gml:455` |
| `fight_asked` | the fight asked for a cue; the start line is the sound, this line is the verdict | 4 | `pp_audio.gml:476` |
| `no_theme_stream` | no theme stream file was found at boot: silence where the theme would be | unobserved | `pp_audio.gml:572` |

"Sample lines" counts real lines in the four source logs and in the shipped sample. Sixteen rows are
`unobserved`: no run in the tree reached that branch, so their wording is pinned by the gml line and their
reason is written in the map (`why_unobserved`), not by a log. They are in the map because a renderer must not
treat an unknown line as sound; they are marked because no log proves them at run time.

Two lines are easy to mix up. `room_asked` and `fight_asked` never make a sound themselves: they report a
verdict about the `music_stream` line that came just before them (`started` or `kept`). A reconstruction that
placed a sound on the room line would play every cue twice.

## 5. The twenty two effects

The `.ogg` column is relative to `assets/audio/sfx/`. The game plays the `.wav` twin from
`game/datafiles/sfx/`, whose data chunk starts at byte 44 and holds the number of bytes the manifest records;
the durations below are the manifest's own measured seconds, and ffprobe reads the same duration on the OGG.

| id | .ogg | s | gain | path | loop |
| --- | --- | --- | --- | --- | --- |
| `alarm` | `alarm.ogg` | 0.64 | 0.9 | bus/sfx | once |
| `car_engine_loop` | `car_engine_loop.ogg` | 0.8 | 1.0 | play | data says loop, bus plays once |
| `crit` | `crit.ogg` | 0.42 | 0.9 | bus/sfx | once |
| `door_hatch` | `door_hatch.ogg` | 0.3 | 1.0 | play | once |
| `encounter_swoosh` | `encounter_swoosh.ogg` | 0.7 | 1.0 | play | once |
| `footstep` | `footstep.ogg` | 0.09 | 1.0 | play | once |
| `game_over` | `game_over.ogg` | 1.4 | 0.9 | bus/sfx | once |
| `heal` | `heal.ogg` | 0.52 | 0.9 | bus/sfx | once |
| `hit_heavy` | `hit_heavy.ogg` | 0.34 | 0.9 | bus/sfx | once |
| `hit_light` | `hit_light.ogg` | 0.12 | 0.9 | bus/sfx | once |
| `item_get` | `item_get.ogg` | 0.32 | 0.9 | bus/sfx | once |
| `level_up` | `level_up.ogg` | 1.2 | 0.9 | bus/sfx | once |
| `menu_cancel` | `menu_cancel.ogg` | 0.18 | 1.0 | play | once |
| `menu_move` | `menu_move.ogg` | 0.06 | 1.0 | play | once |
| `menu_select` | `menu_select.ogg` | 0.16 | 1.0 | play | once |
| `miss` | `miss.ogg` | 0.2 | 0.9 | bus/sfx | once |
| `save_jingle` | `save_jingle.ogg` | 1.4 | 0.9 | bus/sfx | once |
| `text_blip_a` | `text_blip_a.ogg` | 0.06 | 0.45 | blip | once |
| `text_blip_b` | `text_blip_b.ogg` | 0.06 | 0.45 | blip | once |
| `text_blip_c` | `text_blip_c.ogg` | 0.06 | 0.45 | blip | once |
| `thunder_soft` | `thunder_soft.ogg` | 1.45 | 1.0 | play | once |
| `wave_wash` | `wave_wash.ogg` | 1.1 | 0.9 | bus/sfx | once |

Trim notes. Play the whole file once, at the gain above; the game truncates nothing. `car_engine_loop` is the
one asset with loop points in its own Vorbis comments (`LOOPSTART=0`, `LOOPLENGTH=35280`, which is 0.800 s at
44100 Hz), but the bus plays every effect with loop off (`pp_audio_sfx` and `pp_audio_play` both pass false), so
that loop is not heard today: a reconstruction that looped it would not match the game. The speaker blips
`text_blip_zeus`, `text_blip_kronos`, `text_blip_percy`, `text_blip_oldman`, `text_blip_narrator`,
`footstep_a`, `footstep_b` and `knife_slash` are on disk and in `data/audio.json`, but they are not in the
manifest the bus reads, so the bus cannot play them and no log line will ever name them. `pp_audio_blip_cue`
maps a speaker to `text_blip_a`, `text_blip_b` or `text_blip_c` only.

## 6. The eighteen music cues

`data/audio.json` is the table; the log names the file the game opened, which is the build's flattening of the
row's `delivered_file` into `game/datafiles/streams/<leaf>` (the leaf of the delivered path). Both copies are
byte identical on this machine, sha256, checked by `--check`.

| cue | title | file (under `assets/audio/`) | s | pri | state |
| --- | --- | --- | --- | --- | --- |
| PP-01 | Title Theme | `pp_01_title/pp_01_title.ogg` | 74.266803 | 10 | landed |
| PP-02 | The Drive | `pp_drive_master1/pp_drive_master1.ogg` | 178.563333 | 10 | landed |
| PP-03 | Harbor | `pp_03_harbor_master1/pp_03_harbor_master1.ogg` | 225.882358 | 10 | landed |
| PP-04 | Navy Sailors | `pp_04_navy_sailors_master1/pp_04_navy_sailors_master1.ogg` | 43.636349 | 10 | landed |
| PP-05 | Small Ship | `pp_05_small_ship/pp_05_small_ship.ogg` | 60.0 | 10 | landed |
| PP-06 | Percy, Tyrant of the Harbor | `percy_theme/percy_theme.ogg` | 43.636327 | 12 | landed |
| PP-07 | Prometheus Explains | none | - | 10 | pending, falls back to PP-05 |
| PP-08 | Dead Rising | none | - | 10 | pending, falls back to PP-03 |
| PP-09 | The Data Center | none | - | 10 | pending, falls back to PP-03 |
| PP-10 | Hector, Warden of the Dead | none | - | 12 | pending, falls back to PP-06 |
| PP-11 | Rush to Prison | none | - | 10 | pending, falls back to PP-02 |
| PP-12 | One North Quay | none | - | 10 | pending, falls back to PP-03 |
| PP-13 | Titan Employees | none | - | 10 | pending, falls back to PP-03 |
| PP-14 | Kronos | none | - | 12 | pending, falls back to PP-06 |
| PP-15a | Entropy | none | - | 10 | pending, falls back to PP-01 |
| PP-15b | Mercy | none | - | 10 | pending, falls back to PP-01 |
| PP-16 | Ouranos | none | - | 10 | pending, falls back to PP-01 |
| PP-17 | Boarding | `pp_boarding_v2/pp_boarding_v2_humanized.ogg` | 32.0 | 10 | landed, played once (loop false) |

A pending row never reaches the log as a silent room: `pp_audio_music` resolves the row's `fallback` chain
before it plays, and prints `has no OGG yet, falling back to` when it does. A cue whose fallback chain never
reaches a file prints `has no OGG yet, expected <name>` and plays nothing, and the map keeps the
reconstruction silent there, because that is what the game did.

## 7. The title theme beat

The bus asks for the theme in this order, and four lines of that function are the whole rule:

    streams/title_theme_v3_126.ogg, streams/title_theme_v3.ogg, streams/title_theme_v2.ogg, streams/title_theme.ogg

The first one is on disk, so it is the theme a take carries: `assets/audio/title_theme_v3/title_theme_v3_126.ogg`,
mirrored to `game/datafiles/streams/title_theme_v3_126.ogg`. Measured:

- 126.0001 bpm in 3/4 (`assets/audio/title_theme_v3/title_theme_v3_126_loop.json`), so one beat is
  **0.4761901 s** and one bar is **1.4285703 s**; 21000 samples per beat at 44100 Hz.
- bar 1 beat 1 is at **0.000 s**: the ledger's loop starts at sample 0.
- the loop is 52 bars, 3275997 samples, **74.285646 s**, loop seam sample difference 0, and ffprobe reads
  74.285646 s on the OGG, so the loop and the file agree to the sample.
- the theme starts at the bus music level 0.7 (the start line prints it) and loops the whole stream.

The rendering consequence: the title theme belongs at the title beat, which is 0.000 s of the game's own clock,
and a rebuild that starts it anywhere else has moved the piece off its own bar grid. If a later take starts its
recording after the theme did, the theme still sits at 0.0 and the recording's own offset is what moves.

## 8. Worked example, six real lines

Source: `output/music_everywhere_2026-11-01/music_tour.log`, the MUSIC-EVERYWHERE tour. Left as written, with
what the map does about each one.

    PP audio: title_theme streaming streams/title_theme_v3_126.ogg, instance 400001, gain 0.70
    PP audio: car_engine_loop loaded car_engine_loop.wav (0.80 s, 44100 Hz, buffer ref buffer 2)
    PP audio: car_engine_loop played, instance 400002
    PP audio: title_theme handed to the fade, the cue takes the one music source
    PP audio: music cue PP-05 streaming ...\streams/pp_05_small_ship.ogg, instance 400005, priority 10, fade 30 steps
    PP audio: room ship_small asked PP-05, playing PP-05 (started), stream yes

1. `theme_stream`: start `assets/audio/title_theme_v3/title_theme_v3_126.ogg` at gain 0.70, looped, from 0.
2. `sfx_loaded`: no sound. It only says the wav was read.
3. `sfx_played`: place `assets/audio/sfx/car_engine_loop.ogg` once, at gain 1.0 (the `pp_audio_play` path).
4. `theme_handed`: fade the theme to 0 over 0.5 s and stop it; the cue is about to take the one music source.
5. `music_stream`: start `assets/audio/pp_05_small_ship/pp_05_small_ship.ogg` at gain 0.70, looped, fading in
   over 30 steps (0.5 s).
6. `room_asked`: no sound. The room line is the verdict that line 5 succeeded.

`--plan` on that log resolves all 31 lines: 9 music starts, 3 effects, 1 stop, 1 pause, 1 resume, 16 lines that
mean no sound, and no line with an unknown type.

## 9. Known silences and defects this map records

- `PP audio: unknown cue hit`: `pp_battle_director.gml:646` asks for `hit`, and no id of that name is in
  `sfx.json` or `pp_audio_cues()`, so a battle hit is silent today and only the log line exists. The file that
  would fit is `assets/audio/sfx/hit_light.ogg`. Whether the call or the table is wrong is a game ruling, not
  this map's; the map records the silence so no reconstruction invents a hit sound.
- The theme duck raises the theme instead of lowering it. `pp_title.gml:67` defines `PP_TITLE_DUCK_DB 6` and
  `pp_audio_duck_db` computes `0.7 * power(10, db / 20)`, so a real log reads `title_theme ducked 6 dB, gain
  1.40`: six dB louder, not six dB quieter. The map follows the printed gain because that is what the game
  played, and records the defect on the title theme row. `tests/test_audio.py:580` pins the same expression and
  `tests/test_play_demo_audio.py:50` expects a `-6 dB, gain 0.3508` line that no run in the tree has printed.
  Filed as a separate card so the map does not quietly rewrite the game's behaviour.
- `car_engine_loop` carries loop points and a `loop: true` row in `data/audio.json`, and the bus plays it once,
  because effects are played with loop off. The map records `loop_played: false`.
- A pending cue's fallback means the log names one file for two cue ids. `room ship_cabin asked PP-05, playing
  PP-05 (kept)` and a `PP-07` room both stream `pp_05_small_ship.ogg`; the sound is right and the id in the log
  is the resolved one, not the asked one.

## 10. What was measured for this map

- `python tools/event_audio_map.py --check`: PASS. 30 event rows against 31 `show_debug_message("PP audio:` sites
  (`sfx_played` is written by two functions and has one row), 22 effects against `sfx.json`, 18 cues against
  `data/audio.json`, 7 of them landed, 764 real audio lines in four logs and the sample, 0 unmatched.
- The macros the map carries are parsed out of `pp_audio.gml` at check time: 0.7, 0.9, 0.5, 30, 16.6667, the
  four priorities and 10 channels. A macro edit fails the check instead of silently making the map wrong.
- The seven landed cues' build mirrors and the seventeen delivered effect files under `game/datafiles/streams`
  are byte identical to their `assets/audio` originals, sha256, 24 of 24 pairs.
- Every effect `.ogg` probes as vorbis, mono, 44100 Hz, at the same duration the manifest records for its wav
  (0.06 s blips to 1.45 s thunder). `car_engine_loop` also probes `LOOPSTART=0`, `LOOPLENGTH=35280`.
- `tests/test_event_audio_map.py`: 18 passed, and it needs no ffprobe and no `game/datafiles`, so it is green in
  a clean export as well as on this desktop.
- The proof render: `output/demo/eventmap-proof-2026-11-01.m4a`, 12.000 s, `aac` 48000 Hz stereo, mean
  -18.3 dB from the first 64 sounds of the sample log. Its timing is a stated uniform clock and
  `output/demo/eventmap-proof-2026-11-01_proof.json` says so; it proves the map's names and levels, not a take.

## 11. What this map does not do

- It does not capture audio and does not claim a capture device. `knowledge/DEMO-AUDIO-2026-10-27.md` carries
  the device verdict for this host (none usable), and the take itself belongs to card t_7540e6ff.
- It does not change `tools/play_demo.py`. Wiring the tool's reconstruction to read this map is card
  t_4fa327aa (builder); the map is the input that card needs.
- It does not give timing. No log line carries one, and the map says so in its `clock` block rather than
  dressing an invention up as a measurement.
