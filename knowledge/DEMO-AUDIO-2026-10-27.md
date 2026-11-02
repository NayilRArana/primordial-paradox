# Demo audio capture: this host's device inventory, the verdict, and the track a take carries instead

Card t_25c22ae1 (child of DEMO-AUDIO-CAPTURE, t_7540e6ff), on the host CitadelArana. Root of every claim on
this page: probe logs written 2026-11-01 by the security-organization-audit lane into the card workspace
`t_25c22ae1/` (`enumerate_ffmpeg.log`, `enumerate_openal.log`, `endpoints.log`, `probe_audio_names.log`), plus
the 2026-10-27 measurements of the testing lane that this page keeps. Nothing here installed, opened, muted or
changed an audio device: every command below is an enumeration or a probe that fails on purpose. No secret was
read, printed or copied.

Plain answer first: this host cannot capture the game's own sound. It has no active capture endpoint of any
kind, nothing named Stereo Mix or CABLE Output or VoiceMeeter, an ffmpeg build with no WASAPI input at all, and
a DirectShow audio list that is empty. A take recorded here is a silent picture unless the track is rebuilt from
the game's own log, which is what `tools/play_demo.py` does and labels `reconstructed`.

## 1. Device inventory: every device this host offers

### 1.1 The binary doing the enumerating

`ffmpeg -version` reports `ffmpeg version 9.0.2-full_build-www.gyan.dev`, on PATH at
`<home>\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe`
(the same path `tools/play_demo.py` finds through its own `ffmpeg_path`).

`ffmpeg -hide_banner -devices` lists the input devices this build carries:

    Devices:
     D. = Demuxing supported
     .E = Muxing supported
     ---
      E caca            caca (color ASCII art) output device
     D  dshow           DirectShow capture
     D  gdigrab         GDI API Windows frame grabber
     D  lavfi           Libavfilter virtual input device
     D  libcdio
     D  openal          OpenAL audio capture device
     D  vfwcap          VfW video capture

So exactly two of them can hand over a sound: `dshow` and `openal`. There is no `wasapi` row, which is the first
of the three findings below.

### 1.2 DirectShow device list (raw, all of it)

    ffmpeg -hide_banner -list_devices true -f dshow -i dummy

    [in#0 @ 0000017c093e77c0] "moto g power 5G - 2024 (Windows Virtual Camera)" (video)
    [in#0 @ 0000017c093e77c0]   Alternative name "@device_pnp_\\?\swd#vcamdevapi#2f2155060eb24e67c1231e94e791d77f26bcaf37fe868c3fdcd246f6dda3a430#{65e8773d-8f56-11d0-a3b9-00a0c9223196}\{fcebba03-9d13-4c13-9940-cc84fcd132d1}"
    [in#0 @ 0000017c093e77c0] Could not enumerate audio only devices (or none found).
    Error opening input file dummy.

That is the complete output: **one device, and it is a camera**. There are zero DirectShow audio devices, and
`Error opening input file dummy.` is the probe's own expected failure (the name `dummy` is not a device), not a
device fault (source: `enumerate_ffmpeg.log`; the same parse lives in `tools/play_demo.py` `dshow_devices`).

### 1.3 WASAPI: not in this binary

| command | raw answer |
| --- | --- |
| `ffmpeg -hide_banner -formats \| grep -i wasapi` | no line, grep exit 1 |
| `ffmpeg -hide_banner -h demuxer=wasapi` | `Unknown format 'wasapi'.` |

A WASAPI loopback capture is therefore impossible on this machine whatever the sound card does, because the
binary cannot open the API at all. This is a fact about the ffmpeg build, not about the audio hardware
(source: `enumerate_ffmpeg.log`; `tools/play_demo.py` `wasapi_demuxer`).

### 1.4 OpenAL capture: the demuxer exists, and it sees nothing

OpenAL is the one other audio input this build offers, so it was asked directly:

    ffmpeg -hide_banner -f openal -list_devices 1 -i dummy

    [in#0 @ 000001dc9b007180] List of OpenAL capture devices on this system:
    Error opening input file dummy.

The header line is printed and then nothing, so **zero OpenAL capture devices** (source:
`enumerate_openal.log`). `tools/play_demo.py --audio-devices` prints the same list on any host and agrees:
`loopback device for the game's own audio: none`.

### 1.5 Every Windows audio endpoint, from the MMDevices registry

Read only, with `winreg` in `enumerate_endpoints.py`: `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render`
and `\Capture`, each endpoint's `DeviceState` and friendly name. This is the list Windows itself uses, so it
catches a device that ffmpeg might skip.

36 render endpoints, 3 of them active:

| # | state | friendly name |
| --- | --- | --- |
| 1 | 536870916 | Digital Output |
| 2 | UNPLUGGED | Headset |
| 3 | UNPLUGGED | Headphones |
| 4 | 536870916 | Digital Output |
| 5 | 536870916 | ASUS VA229 |
| 6 | 536870916 | Digital Output |
| 7 | NOTPRESENT | NVIDIA Output |
| 8 | **ACTIVE** | **Headphones** |
| 9 | UNPLUGGED | Headphones |
| 10 | 536870916 | Digital Output |
| 11 | NOTPRESENT | NVIDIA Output |
| 12 | 536870916 | Digital Output |
| 13 | 536870916 | NVIDIA Output |
| 14 | 536870916 | G2490W1G4 |
| 15 | NOTPRESENT | NVIDIA Output |
| 16 | 536870916 | C27G4 |
| 17 | 536870916 | Digital Output |
| 18 | **ACTIVE** | **Digital Audio (S/PDIF)** |
| 19 | UNPLUGGED | Headset |
| 20 | NOTPRESENT | C27G4 |
| 21 | 536870916 | Digital Output |
| 22 | NOTPRESENT | Speakers |
| 23 | NOTPRESENT | Speakers |
| 24 | 536870916 | Digital Output |
| 25 | 536870916 | Digital Output |
| 26 | 536870916 | Digital Output |
| 27 | UNPLUGGED | Headset |
| 28 | NOTPRESENT | Headphones |
| 29 | 536870916 | Digital Output |
| 30 | 536870916 | NVIDIA Output |
| 31 | 536870916 | Digital Output |
| 32 | UNPLUGGED | Headphones |
| 33 | 536870916 | Digital Output |
| 34 | 536870916 | Digital Output |
| 35 | **ACTIVE** | **C27G4** |
| 36 | 536870916 | Digital Output |

7 capture endpoints, none of them active:

| # | state | friendly name | loopback or virtual cable? |
| --- | --- | --- | --- |
| 1 | NOTPRESENT | Line In | no, a line input |
| 2 | NOTPRESENT | Microphone | no, a microphone |
| 3 | UNPLUGGED | Headset | no, a headset microphone |
| 4 | NOTPRESENT | Microphone | no, a microphone |
| 5 | NOTPRESENT | Microphone | no, a microphone |
| 6 | UNPLUGGED | Headset | no, a headset microphone |
| 7 | UNPLUGGED | Headset | no, a headset microphone |

The state word 536870916 is 0x20000004: the low nibble 4 is `DEVICE_STATE_NOTPRESENT`, and bit 0x20000000 is a
flag this Windows build sets on endpoints it has unloaded. Nothing carrying it is active, and every name in that
group is a display or HDMI output, so the reading does not depend on the flag being decoded. Headphone and
headset render endpoints are outputs: they cannot be opened as a capture source either.

That is 43 endpoints in total and not one usable loopback: no Stereo Mix, no CABLE Output, no VoiceMeeter, no
virtual-audio-capturer, no OBS virtual device. The same finding, with the same seven capture endpoints, is in
`knowledge/DEMO-BED-2026-10-26.md` and in section 3 of
`projects/arananet/meta-hackathon/SUBMISSION-CHECKLIST.md` (source: `endpoints.log`).

### 1.6 No virtual cable software is installed

| path | result |
| --- | --- |
| `C:\Program Files\VB` | not found |
| `C:\Program Files (x86)\VB` | not found |
| `C:\Program Files\OBS Studio` | not found |
| `C:\Program Files (x86)\OBS Studio` | not found |
| `C:\Program Files\VoiceMeeter` | not found |
| `HKLM\...\Uninstall` search for `CABLE` | 0 matches |
| `HKLM\...\Uninstall` search for `OBS` | no `DisplayName` rows |

So the empty capture list is not a missing driver that is present but asleep: the software that would create a
loopback endpoint has never been installed here.

### 1.7 Asking for the usual loopback names by hand

Enumeration can miss a device that is present but unnamed in a list, so each usual name was also opened
directly. All three fail at the device, not at the syntax:

    ffmpeg -f dshow -i "audio=CABLE Output (VB-Audio Virtual Cable)" -t 0.1 -f null -
    -> Could not find audio only device with name [CABLE Output (VB-Audio Virtual Cable)] ... exit 127

    ffmpeg -f dshow -i "audio=Stereo Mix (Realtek(R) Audio)" -t 0.1 -f null -
    -> Could not find audio only device with name [Stereo Mix (Realtek(R) Audio)] ... exit 127

    ffmpeg -f dshow -i "audio=Line In (Realtek(R) Audio)" -t 0.1 -f null -
    -> Could not find audio only device with name [Line In (Realtek(R) Audio)] ... exit 127

The exit code is ffmpeg's own and not a shell artifact: `ffmpeg -version` returns 0 and a plain `false` returns
1 in the same shell, while these three return 127 (sources: `probe_audio_names.log`, `probe_cable_rc.log`).
Even the name Windows would give the one capture device it knows about, Line In, cannot be opened, which is
what `NOTPRESENT` means in section 1.5.

## 2. Verdict: is there a usable loopback or virtual cable on this host

**No.** Four independent measurements agree:

1. DirectShow, the only audio input format the capture path can use, lists zero audio devices (1.2).
2. The binary has no WASAPI input at all, so a WASAPI loopback could not be opened even if Windows offered one (1.3).
3. OpenAL, the second audio input this build has, sees zero capture devices (1.4).
4. Windows itself reports 7 capture endpoints and 0 active, none of them loopback style, and 3 active render
   endpoints that cannot be captured (1.5), with no virtual cable software installed (1.6).

Consequence, stated plainly: a take recorded on this host today carries a silent audio track or no audio track.
Any pipeline that says otherwise is wrong. The one thing that would flip this verdict is a single active
capture endpoint whose name reads like a loopback (`stereo mix`, `cable output`, `voicemeeter`, `vb-audio`,
`what u hear`, `virtual-audio-capturer`, `obs virtual`, the hint list in `tools/play_demo.py` `LOOPBACK_HINTS`).

## 3. The install Nayil has to do, and the fallback if he does not

The card says Nayil installs any audio device and a worker must not, so nothing was installed and nothing was
changed. The single line, which is also what `tools/play_demo.py` prints when it finds no loopback
(`LOOPBACK_INSTALL`):

    audio install: install VB-Audio Virtual Cable (vb-audio.com/Cable) and set the game's output to CABLE Input, so ffmpeg can record CABLE Output with the video; OBS Studio's Audio Output Capture with the virtual audio device is the other way to the same device

That is the only install line, and it is needed while the measurement above stands.

The fallback, which needs no install and is what a take carries today: rebuild the track from the game's own
event log. The game writes one `PP audio:` line for every cue it asks for, plays, ducks or leaves silent, in
`game/scripts/pp_audio/pp_audio.gml` (`pp_audio_music`, `pp_audio_sfx`, `pp_audio_duck_db`, `pp_audio_unduck`).
Those lines are the record of the game's sound, and the game keeps writing them under `PP_MUTE=1`, because the
mute takes the master gain to 0 and changes no code path (`game/scripts/pp_app/pp_app.gml` lines 42 to 44;
`build/demo-game.log` line 32 says `PP: muted` and line 35 still says `title_theme streaming`).

That second path is honest only if it is labelled as a rebuild. `tools/play_demo.py` labels it
`reconstructed` and never calls it a capture (section 6).

## 4. The capture command, and what the fallback needs

### 4.1 With a virtual cable installed

`tools/play_demo.py` already has the capture branch; with a loopback device present it adds the audio input to
the same ffmpeg process that records the window (`tools/play_demo.py` `start_recorder`, lines 1043 to 1045):

    ffmpeg -hide_banner -y -f gdigrab -framerate 30 -offset_x <L> -offset_y <T> -video_size <W>x<H> \
      -i desktop -t <DURATION> -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -r 30 \
      -c:v libx264 -preset ultrafast -crf 20 -pix_fmt yuv420p \
      -f dshow -i "audio=CABLE Output (VB-Audio Virtual Cable)" \
      -map 0:v -map 1:a -c:a aac -b:a 160k <OUT>.mp4

The take command stays the same either way, because the tool picks the device itself
(`pick_game_audio_device`) and then writes `audio_source: game` with the device name:

    python tools\play_demo.py --script data\demo\run_002.json --out output\demo\audio-2026-10-27.mp4

That branch was **not executed here**: the device it names does not exist (1.7), so its behaviour on this host is
UNKNOWN and the reading above comes from the code, not from a run. What is measured is that the line fails at
device lookup today with exit 127.

### 4.2 Today's fallback requirements

The rebuild path needs all five of these, and its pass conditions are the last two:

1. The game running with its log at `build/demo-game.log` (`tools/play_demo.py` `BUILD_DIR`, line 2458), writing
   `PP audio:` lines for the run that is being recorded.
2. The audio files the log names, present on the recording machine: `game/datafiles/streams/` holds the stream and
   music OGGs and `game/datafiles/sfx/` the effects (both exist here, `ls` 2026-11-01). `game/datafiles/` is
   gitignored, so a clean checkout has none of them and every cue it cannot find stays silent.
3. ffmpeg 9.0.2 on PATH with libx264, aac and vorbis (section 1.1).
4. A desktop with no automation process driving it: `python tools/idle_check.py` must not exit 4 (section 8).
5. The run command, `python tools\play_demo.py --script data\demo\run_002.json --out output\demo\audio-2026-10-27.mp4`,
   which muxes an AAC 48 kHz stereo track beside the h264 video and stamps the mp4's `comment` with its
   provenance.
6. The pass checks: `audio_source` reads `reconstructed`, `has_audio` is true, the `audio` check line starts with
   `PASS`, `ffprobe` shows an `aac` stream beside the `h264` one, and
   `ffmpeg -t 6 -i <mp4> -af volumedetect -f null -` reports a mean well above -70 dB, which is the title theme
   at the title beat (`tools/play_demo.py` `verify_video`, `audio_check`, `mean_volume_db`).

## 5. How the rebuild works, so a reader can audit it

`tools/play_demo.py` does this on every take when no loopback device exists:

1. `LogAudioWatch` reads the game's log every 50 ms while the recording runs and stamps each `PP audio:` line
   with the second it arrived on the recording's clock; lines already in the file at record start (the title
   theme streams at boot) are placed at 0.0 and flagged `before_recording`.
2. `audio_events` turns each line into a cue with the file it names, found on this checkout: the title theme
   stream, a music cue by id, a cue the game could not start, a stop, a duck, an unduck, a focus pause, a focus
   resume, or an effect (`audio_events`, `resolve_stream`, `sfx_table`). Every row the watch hands over ends as
   one of three things: a placement, a silent cue, or a note. A line with a shape this tool does not know is a
   note naming the line, and the once-a-second `PP audio status:` lines are counted into one note, so a take's
   record is a full account of its log instead of a count that implies it (`audio_events`, review round 1).
3. `log_audio_plan` places them at the game's own gains and splits the music at each duck: music 0.7, an effect
   0.9, a text blip 0.45, a 6 dB duck 0.3508, crossfade 30 steps of 16.6667 ms at the edges
   (`game/scripts/pp_audio/pp_audio.gml` lines 42 to 51; `tools/play_demo.py` constants).
4. The game's focus pause is part of its sound. `pp_audio_focus` pauses the music and stops every ringing
   effect when the window loses focus, and resumes the music where it stopped when focus returns
   (`game/scripts/pp_audio/pp_audio.gml` lines 415 to 434). `focus_windows` reads the two log lines into
   (lost, back) pairs, the music carries no segment inside a pair, and the piece after it starts at the second
   of the file the music had reached, which every music segment carries as its `offset` and
   `render_log_audio` trims from (`atrim=start=...`, `tools/play_demo.py`). A piece that ends at a pause carries no
   fade out and a resumed piece no fade in, because the engine pauses and resumes dead
   (`game/scripts/pp_audio/pp_audio.gml` line 420 and line 431, `log_audio_plan`).
5. Which reading of the pause line the rebuild uses is stated in the take's record and not chosen in silence:
   the pause stops the effects that were already ringing at that instant, which the plan cuts at the pause
   second, and an effect the log prints after the pause is kept, because the game prints a play line when it
   starts a sound and a stopped sound cannot print one (`FOCUS_EFFECTS_READING`, `tools/play_demo.py`). The
   record carries that sentence plus the pause seconds under `audio_detail.focus`
   (`reconstruct_audio`, `verify_video`).
6. `render_log_audio` builds one ffmpeg filtergraph: an `anullsrc` base, one input per cue (music looped with
   `-stream_loop -1`), each trimmed from its offset, gained, faded and delayed to its second, mixed with
   `normalize=0`, out as AAC 48 kHz stereo (`render_log_audio`, `tools/play_demo.py`).
7. `reconstruct_audio` refuses to call the result audio when ffmpeg's own `volumedetect` mean is at or under
   -70 dBFS, so a silent track is a failure and never a pass (`SILENT_TRACK_DB`, `tools/play_demo.py`).

A cue the game asked for and could not start stays silent in the rebuild, because the cue's OGG is not where
the music path looks today (`knowledge/nodes/audio-routing.md` section 3). The rebuild reproduces the game's
sound, not the sound the game was supposed to make (`log_audio_plan`).

The files the log names are resolved in two places and neither is in the commit: `game/datafiles/` is gitignored
(`.gitignore` line 5), so `game/datafiles/streams/title_theme_v3_126.ogg` and `game/datafiles/sfx/footstep.wav`
exist on a machine that has synced the build and in no checkout (`git check-ignore -v`, measured 2026-10-27).
When a file is not found the line becomes a note and the track stays silent there, which is why a take must be
recorded on the machine that has the mirrors, and why `tests/test_play_demo_audio.py` feeds the tool copies of
the tracked `assets/audio` OGGs instead of reading the mirrors.

`tools/demo_bed.py` is a separate bed tool that writes its own wav from the beat windows of a finished recording
and is not this path: nothing here muxes that file into a take.

## 6. The field, and the test that keeps it honest

A take's verify file carries `audio_source`, and a final take may read `game` or `reconstructed` and nothing
else (`tools/play_demo.py` `AUDIO_SOURCES`, `audio_check`):

| `audio_source` | verdict |
| --- | --- |
| `game` | PASS, with the loopback device named, only when the finished file really has an audio stream |
| `reconstructed` | PASS, with the segment count and the first music second, labelled as not a capture |
| `none`, a stand-in, a missing label | FAIL, and the line carries the one install above |
| no record at all (`--check` on a file with no sibling verify) | UNMEASURED either way, because a file alone cannot say where its sound came from |
| no record at all, asked the shipping question (`--check --final`) | FAIL: a take that is about to be submitted has to name its audio |

The UNMEASURED row is a measurement and it is the right answer to "where did this file's sound come from": a
file on disk cannot say. The last row is the other question a launch gate asks, "may this file be submitted",
and there the honest answer to a missing record is no. Without that split the cut that would ship today reads
as not-wrong instead of not-allowed: measured 2026-10-27 18:23,
`python tools/play_demo.py --check --final --video output/demo/DEMO-CUT-V3.mp4` exits 1 with
`FAIL this take carries no record of where its audio came from (no sibling verify file), and a final take may
not ship on a guess`, where the same file under plain `--check` measures UNMEASURED (`_t7540_final_cut_check.log`).

The old stand-in has no code path left: `render_stand_in_audio` and `newest_theme` are gone from
`tools/play_demo.py`, and a take whose sibling verify still says "stand-in" fails the audio check when
`--check` reads it (`read_audio_record`, `audio_check`). `tests/test_play_demo_audio.py` pins all of it.

## 7. What was measured on the real log and the real files

The log of the 2026-10-27 take at `build/demo-game.log` holds 166 `PP audio:` lines and no timestamps of its
own. Fed through the rebuild path with arrival seconds spread over 73.5 s (a stand-in for the watch's stamps,
because this log predates it), the tool built 158 segments, placed
`game/datafiles/streams/title_theme_v3_126.ogg` at 0.0 s, and measured a mean of -20.8 dBFS on the track
(`reconstruct_audio`).

The tool's own mux (`cut_and_scale`) was then run for real against `output/demo/demo-talk-2026-10-26.mp4` and
that track: ffprobe reports `h264` video plus `aac` audio at 48000 Hz and 2 channels, duration 73.5 s, and the
mp4's own `comment` tag says in words that the audio is reconstructed from the game's own log and is not a
capture of the sound card. ffmpeg's volumedetect over the first 6 s of that file reads mean -18.1 dB and max
-2.8 dB, so the title theme is audible at the title beat rather than a silent stream.

The pixels of that probe are a 2026-10-26 take, not a new capture: it proves the audio path and the mux, and it
is not offered as a new take.

Test runs: in the shared worktree `python -m pytest tests/test_play_demo_audio.py tests/test_play_demo.py
tests/test_play_demo_cover.py tests/test_demo_bed.py -q` gave `45 passed in 19.63s` in the first run and
`47 passed in 15.39s` at HEAD `388b5326` after two more `--final` tests were added (`_t7540_audio_tests.log`,
`_t7540_audio_r3.log`).

## 8. What is not done, and the exact step that finishes it

No new take was recorded on 2026-10-27, so no verify file yet reads `audio_source: reconstructed` from a real
recording. The reason is measured, not assumed: `python tools/idle_check.py --json` answered
`"allowed": false` with `automations_running: ["codex-computer-use-swift.exe", "codex.exe"]` and
`idle_seconds: 551.641` (`_t7540_idle_r2.log`). The refusal is on the presence of the two automation processes
and not on the keyboard: nothing had been typed for 551 s and the gate still refused.

A second route is closed as well: both window recordings already on disk are truncated, so a take cannot be
stitched from a previous recording. `ffprobe` on `output/demo/_run_002_raw.mp4` (28311600 B, 13:35) and
`output/demo/_qa_full_route_raw.mp4` (18350128 B, 07:06) both answer `moov atom not found`, which is what a
recorder killed before its trailer writes.

The step that finishes it, on a desktop where that automation is stopped:

    python tools\play_demo.py --script data\demo\run_002.json --out output\demo\audio-2026-10-27.mp4

Then the card's own check is one command:

    python tools\play_demo.py --check --final --video output\demo\audio-2026-10-27.mp4

Until that run exists, no take after 2026-10-30 may ship: the only two labels that pass are the ones in
section 6, `none` fails, and a take with no record at all fails the shipping question. The cut that would be
submitted today, `output/demo/DEMO-CUT-V3.mp4`, is one of those unrecorded files: it has no verify file beside
it, so it fails `--check --final` on its audio rather than being submitted on a guess.


## 9. Review round 1: the focus pause and the accounting, measured 2026-11-02

Two corrections were asked for on this card after the 2026-11-02 take, and both are in `tools/play_demo.py` now.

### 9.1 The music no longer plays across a pause the game's own log records

The 2026-11-02 take's own record is the defect: `output/demo/audio-2026-11-02_verify.json` has one music
segment, `title_theme` from `in` 0.0 to `out` 256.0, while `build/demo-game.log` line 47 says
`PP audio: focus lost, music paused (cue and theme) and every effect stopped` and line 72 says
`PP audio: focus back, music resumed where it stopped` (`build/demo-game.log`). The pause came before the first
thunder placement at 7.031 s and the resume after the last one at 251.328 s, so that record played the theme
for about 244 s of the 256 s the log says the music was paused (`output/demo/audio-2026-11-02_verify.json`).

Now `audio_events` reads both lines as events, `focus_windows` pairs them, `log_audio_plan` emits no music
segment inside a pair, and the piece after the pause starts at the second of the file the music had reached:
the plan carries it as `offset`, and `render_log_audio` trims from there with `atrim=start=...`
(`tools/play_demo.py` `focus_windows`, `log_audio_plan`, `render_log_audio`). The take's record gains
`audio_detail.focus` with the pause seconds, one sentence on the music and `FOCUS_EFFECTS_READING`
(`reconstruct_audio`, `tools/play_demo.py`).

Measured on the real log, with a DECLARED uniform clock: `build/demo-game.log` has no timestamps of its own, so
the probe gives one audio line per second in log order, which is a shape proof and not that take's real
seconds (`output/demo/focus-proof-2026-11-02.json`, `_t7540_focus_probe_r1.log` in this card's workspace):

| measure | value | source |
| --- | --- | --- |
| audio lines in the log | 32 | `build/demo-game.log` |
| focus window read from the log | 3.0 s to 27.0 s | `output/demo/focus-proof-2026-11-02.json` |
| music segments overlapping the pause | 0 | same file |
| music pieces | 0.0 to 3.0 at offset 0.000, then 27.0 to 32.0 at offset 3.000 | same file |
| effect placements the log prints inside the pause, kept by the stated reading | 22 | same file |
| rebuilt track mean | -17.2 dBFS, aac 48000 Hz 2 channels, 32.000000 s | ffprobe of `output/demo/focus-proof-2026-11-02.m4a` |
| mean before the pause, inside it, after the resume | -19.4 dB, -16.7 dB, -16.3 dB | `ffmpeg -ss ... -af volumedetect` on that file |

The pause window is not silent in that rebuild, and the record says why: the 22 effect plays the log prints
between the two focus lines are kept, per the reading above. What the fix removes is the music playing through
the pause, and the segments show it: 0 music segments overlap the window (`output/demo/focus-proof-2026-11-02.json`).

### 9.2 A pause with nothing but music in it measures as silence

`tests/test_play_demo_audio.py::test_the_rendered_track_is_silent_in_the_pause_and_sounds_after_it` renders a
log of a title cue, a pause at 10 s and a resume at 20 s, and measures three windows of the finished file with
ffmpeg's own `volumedetect`: 1.0 to 4.0 s is above the -70 dB floor, 12.0 to 17.0 s is at or under it, and
22.0 to 25.0 s is above it again. That is the pause held as a silence in the rendered track, not only in the
plan (`tests/test_play_demo_audio.py`, `SILENT_TRACK_DB` in `tools/play_demo.py`).

### 9.3 Every audio line now ends as a placement, a silent cue, or a note

On the 2026-11-02 take the record read `lines: 27`, `notes: []`, `segments: 24`, which implies every line was
accounted for while the two focus lines had simply been dropped (`output/demo/audio-2026-11-02_verify.json`).
`audio_events` now appends a note for any line whose shape it does not know, names the line in it, and counts
the once-a-second `PP audio status:` lines into one note (`audio_events`, `tools/play_demo.py`). On the real log
that is visible at once: 32 audio lines give 30 events and 2 notes, and the two notes name the `car_engine_loop
loaded` and `thunder_soft loaded` lines, which the old code dropped without a word
(`output/demo/focus-proof-2026-11-02.json`).

### 9.4 Tests, measured 2026-11-02

    .venv/Scripts/python.exe -m pytest tests/test_play_demo_audio.py tests/test_event_audio_map.py \
        tests/test_play_demo.py tests/test_play_demo_cover.py tests/test_demo_bed.py -q
    -> 73 passed

The new pins are the four in section 6 to 8 of `tests/test_play_demo_audio.py`: the pause with no music segment
in it and the resume at the playing-time offset, the effect cut at the pause with a later play kept whole, the
reading stated in the record, the full accounting of a log, and the rendered track's three windows.

### 9.5 What is still owed, and it is not a code item

The check the card names has to be run on a real take after the route fix lands and the manager's 2026-11-02
15:25 hold lifts. `output/demo/audio-2026-11-02.mp4` is not that take: its picture is a route that stalled on
the title and its audio predates this fix, so it is evidence for the field and the mux only
(`output/demo/audio-2026-11-02_verify.json`). The command for the next take is the one in section 8.
