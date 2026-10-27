# Demo audio capture: what this host offers, and the track a take can carry instead

Card DEMO-AUDIO-CAPTURE, written 2026-10-27 by the testing lane, on the host CitadelArana. The question the
card asks: does the submission video carry the game's real audio, or a stand-in. Sources for every number are
on the line that carries it.

## 1. The answer in one line

This host has no loopback capture device and this ffmpeg build has no WASAPI input at all, so a take recorded
here cannot carry a capture of the sound card, and `tools/play_demo.py` now rebuilds the track from the game's
own log instead and labels it `reconstructed` (`tools/play_demo.py`).

## 2. The device list, from ffmpeg's own words

Command: `ffmpeg -hide_banner -list_devices true -f dshow -i dummy`, ffmpeg 9.0.2-full_build-www.gyan.dev
(`build/` ffmpeg found on PATH, `tools/capture_title.py` `find_ffmpeg`).

| what ffmpeg printed | reading |
| --- | --- |
| `"moto g power 5G - 2024 (Windows Virtual Camera)" (video)` | one DirectShow device, and it is a camera (`tools/play_demo.py` `dshow_devices`) |
| `Could not enumerate audio only devices (or none found).` | dshow offers no audio input on this host (`tools/play_demo.py` `dshow_devices`) |
| `Error opening input file dummy.` | the list probe's own expected failure, not a device error (`tools/play_demo.py` `dshow_devices`) |

Command: `ffmpeg -hide_banner -formats | grep -ci wasapi` returned `0`, and `ffmpeg -hide_banner -h
demuxer=wasapi` returned `Unknown format 'wasapi'.`, so no WASAPI loopback can be opened by this binary
whatever the sound card does (`tools/play_demo.py` `wasapi_demuxer`).

The Windows endpoint list agrees: 7 capture endpoints and not one of them active (Line In and three
Microphones not present, three Headsets unplugged), while 3 render endpoints are active (Headphones, Digital
Audio (S/PDIF), C27G4), read from
`HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\{Render,Capture}` with `DeviceState` and the
friendly name property (probe kept in this card's run, not committed).

There is no Stereo Mix, no CABLE Output, no VoiceMeeter and no virtual-audio-capturer in either list, which is
the same finding `knowledge/DEMO-BED-2026-10-26.md` and section 3 of
`projects/arananet/meta-hackathon/SUBMISSION-CHECKLIST.md` already recorded.

`python tools\play_demo.py --audio-devices` re-prints this list on any host, with the install below when there
is no loopback, and it opens no window (`tools/play_demo.py` `main`).

## 3. The one install Nayil has to do for a capture of the game's own output

One line, printed by the tool itself when it finds no loopback device (`tools/play_demo.py`
`LOOPBACK_INSTALL`): install VB-Audio Virtual Cable (vb-audio.com/Cable) and set the game's output to CABLE
Input, so ffmpeg can record CABLE Output with the video; OBS Studio's Audio Output Capture with the virtual
audio device is the other way to the same device.

Nothing was installed here: the card says Nayil installs any audio device, and installing one would change the
machine every other capture tool measures (`tools/play_demo.py` docstring, card body).

## 4. The second path, which is what a take carries today

The game writes one `PP audio:` line for every cue it asks for, plays, ducks or leaves silent, in
`game/scripts/pp_audio/pp_audio.gml` (`pp_audio_music`, `pp_audio_sfx`, `pp_audio_duck_db`, `pp_audio_unduck`).
Those lines are the record of the game's sound, and the game keeps writing them under `PP_MUTE=1`, because the
mute takes the master gain to 0 and changes no code path (`game/scripts/pp_app/pp_app.gml` line 42 to 44;
`build/demo-game.log` line 32 says `PP: muted` and line 35 still says `title_theme streaming`).

`tools/play_demo.py` now does this on every take with no loopback device:

1. `LogAudioWatch` reads the game's log every 50 ms while the recording runs and stamps each `PP audio:` line
   with the second it arrived on the recording's clock; lines already in the file at record start (the title
   theme streams at boot) are placed at 0.0 and flagged `before_recording` (`tools/play_demo.py`).
2. `audio_events` turns each line into a cue with the file it names, found on this checkout: the title theme
   stream, a music cue by id, a cue the game could not start, a stop, a duck, an unduck, or an effect
   (`tools/play_demo.py` `audio_events`, `resolve_stream`, `sfx_table`).
3. `log_audio_plan` places them at the game's own gains and splits the music at each duck: music 0.7, an effect
   0.9, a text blip 0.45, a 6 dB duck 0.3508, crossfade 30 steps of 16.6667 ms at the edges
   (`game/scripts/pp_audio/pp_audio.gml` lines 42 to 51; `tools/play_demo.py` constants).
4. `render_log_audio` builds one ffmpeg filtergraph: an `anullsrc` base, one input per cue (music looped with
   `-stream_loop -1`), each trimmed, gained, faded and delayed to its second, mixed with `normalize=0`, out as
   AAC 48 kHz stereo (`tools/play_demo.py`).
5. `reconstruct_audio` refuses to call the result audio when ffmpeg's own `volumedetect` mean is at or under
   -70 dBFS, so a silent track is a failure and never a pass (`tools/play_demo.py` `SILENT_TRACK_DB`).

A cue the game asked for and could not start stays silent in the rebuild, because the cue's OGG is not where
the music path looks today (`knowledge/nodes/audio-routing.md` section 3). The rebuild reproduces the game's
sound, not the sound the game was supposed to make (`tools/play_demo.py` `log_audio_plan`).

The files the log names are resolved in two places and neither is in the commit: `game/datafiles/` is gitignored
(`.gitignore` line 5), so `game/datafiles/streams/title_theme_v3_126.ogg` and `game/datafiles/sfx/footstep.wav`
exist on a machine that has synced the build and in no checkout (`git check-ignore -v`, measured 2026-10-27).
When a file is not found the line becomes a note and the track stays silent there, which is why a take must be
recorded on the machine that has the mirrors, and why `tests/test_play_demo_audio.py` feeds the tool copies of
the tracked `assets/audio` OGGs instead of reading the mirrors (`tests/test_play_demo_audio.py` `delivered`).

`tools/demo_bed.py` is a separate bed tool that writes its own wav from the beat windows of a finished recording
and is not this path: nothing here muxes that file into a take (`tools/demo_bed.py`; this card's scope).

## 5. What was measured, on the real log and the real files

The log of the 2026-10-27 take at `build/demo-game.log` holds 166 `PP audio:` lines and no timestamps of its
own (`build/demo-game.log`). Fed through the new path with arrival seconds spread over 73.5 s (a stand-in for
the watch's stamps, because this log predates it), the tool built 158 segments, placed
`game/datafiles/streams/title_theme_v3_126.ogg` at 0.0 s, and measured a mean of -20.8 dBFS on the track
(`tools/play_demo.py` `reconstruct_audio`).

The tool's own mux (`tools/play_demo.py` `cut_and_scale`) was then run for real against
`output/demo/demo-talk-2026-10-26.mp4` and that track: ffprobe reports `h264` video plus `aac` audio at 48000
Hz and 2 channels, duration 73.5 s, and the mp4's own `comment` tag saying, in words, that the audio is
reconstructed from the game's own log and is not a capture of the sound card. ffmpeg's volumedetect over the
first 6 s of that file reads mean -18.1 dB and max -2.8 dB, so the title theme is audible at the title beat
rather than a silent stream (`<agent-runtime>/profiles/testing/cache/scratch/probe_mux.py`,
run output of 2026-10-27).

The pixels of that probe are a 2026-10-26 take, not a new capture: it proves the audio path and the mux, and it
is not offered as a new take (this card, and `output/demo/`).

## 6. The field, and the test that keeps it honest

A take's verify file now carries `audio_source`, and a final take may read `game` or `reconstructed` and
nothing else (`tools/play_demo.py` `AUDIO_SOURCES`, `audio_check`):

| `audio_source` | verdict |
| --- | --- |
| `game` | PASS, with the loopback device named, only when the finished file really has an audio stream (`tools/play_demo.py` `audio_check`) |
| `reconstructed` | PASS, with the segment count and the first music second, labelled as not a capture (`tools/play_demo.py` `audio_check`) |
| `none`, a stand-in, a missing label | FAIL, and the line carries the one install above (`tools/play_demo.py` `audio_check`) |
| no record at all (`--check` on a file with no sibling verify) | UNMEASURED either way, because a file alone cannot say where its sound came from (`tools/play_demo.py` `audio_check`) |

The old stand-in has no code path left: `render_stand_in_audio` and `newest_theme` are gone from
`tools/play_demo.py`, and a take whose sibling verify still says "stand-in" fails the audio check when
`--check` reads it (`tools/play_demo.py` `read_audio_record`, `audio_check`).

`tests/test_play_demo_audio.py` pins all of it: the two-value enum and the absence of the stand-in renderer,
the PASS and FAIL verdicts above, the log line shapes at the game's own gains, a cue the game could not start
staying silent, the duck splitting the music into three pieces, a log with nothing to place being a failure,
and a real render whose `volumedetect` mean is above the silence floor at 48000 Hz stereo
(`tests/test_play_demo_audio.py`). Measured twice, because this suite has the gitignored-mirror trap in
`projects/arananet/manager/continuity/lanes/testing.md`: in the shared worktree
`python -m pytest tests/test_play_demo_audio.py tests/test_play_demo.py tests/test_play_demo_cover.py
tests/test_demo_bed.py -q` gave `45 passed in 19.63s`, and in a clean export of HEAD plus these three files
(`git archive HEAD projects/primordial-paradox | tar -x`) the gate's own command
`python -m pytest -q tests/test_build_inputs.py tests/test_play_demo.py tests/test_play_demo_audio.py
tests/test_play_demo_cover.py tests/test_project.py` gave `60 passed, 16 skipped in 36.29s`, with all 9 audio
tests passing and none skipped (`_t7540_audio_tests.log`, `/tmp/t7540_tree_tests.log`).

## 7. What is not done, and the exact step that finishes it

No new take was recorded on 2026-10-27, so no verify file yet reads `audio_source: reconstructed` from a real
recording. The reason is measured, not assumed: `python tools/idle_check.py` exits 4 and refuses with
`a desktop automation is running (codex-computer-use-swift.exe, codex.exe)`, and the lane's own finding is that
this gate refuses on presence and never clears by waiting (`tools/idle_check.py`;
`projects/arananet/manager/continuity/lanes/testing.md`).

The step that finishes it, on a desktop where that automation is stopped:

    python tools\play_demo.py --script data\demo\run_001.json --out output\demo\audio-2026-10-27.mp4

Then the take passes only if all of these hold: `output\demo\audio-2026-10-27_verify.json` reads
`"audio_source": "reconstructed"` (or `"game"` on a host with a loopback), `"has_audio": true`, and an `audio`
check line starting with `PASS`; `ffprobe` on the mp4 shows an `aac` stream beside the `h264` one; and
`ffmpeg -t 6 -i <mp4> -af volumedetect -f null -` reports a mean well above -70 dB, which is the title theme
at the title beat (`tools/play_demo.py` `verify_video`, `audio_check`, `mean_volume_db`).

Until that run exists, no take after 2026-10-30 may ship: the only two labels that pass are the ones above, and
`none` fails (this card; `tools/play_demo.py` `audio_check`).
