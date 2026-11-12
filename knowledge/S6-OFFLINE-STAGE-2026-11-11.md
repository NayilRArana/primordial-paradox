# S6 OFFLINE STAGE 2026-11-11: the TALK fight shot with three bake rows and the network line on screen

Card t_0a284b7e, fix 4 of the JUDGE-PANEL 2026-11-12 five, testing lane, priority 88. The panel's reason on the
"Use of Meta AI tooling" criterion was `Receipts list 21 calls with 52.4 percent live but frames show no textbox
verdict, bake row or caption so no real work is visible`. `knowledge/DEMO-SCRIPT.md` section 5 says what the S6
offline shot must show. `tools/demo_overlay.py` already draws that plate. What did not exist was a moving shot: every
proof of the plate in this tree was a still frame, and the DEVLOG entry of 2026-10-29 says so in its own words
("the badge proof is a still frame rather than a fresh capture").

## What was staged, measured

`tools/stage_s6_offline.py` cuts a real recording of the game's TALK fight, pads it to the plate's canvas, and
composites the plate that `tools/demo_overlay.py` draws from `data/meta_bake.json`, in the window section 5 puts it.

| fact | value | where it was measured |
| --- | --- | --- |
| shot | `output/demo/s6-offline-2026-11-11.mp4` | this card |
| shot bytes | 1,514,054 | `output/demo/s6-offline-2026-11-11_verify.json` `shot_bytes` |
| shot sha256 | `ec5925bc7c92dc9f19d7731763d7acaaced7b23d222aeb67137601324aaa93a4` | same file, `shot_sha256` |
| stream | 768 x 990, 60 fps (`60/1`), 3,312 frames, 55.200 s | `ffprobe` on the shot |
| recording cut | `output/first_fight_talk_capture.mp4`, 73.8 s, cut from 18.600 s | that recording's own verify file and `ffprobe` |
| plate window | 1.400 s to 43.400 s of the shot, 42.0 s | `tools/stage_s6_offline.py` `PLATE_IN` and `PLATE_OUT` |
| plate | rect (24, 732, 744, 978), 11 lines | `output/demo/s6-offline-2026-11-11_plate.png` and the verify file's `plate_plan` |
| bake state printed | `offline` true, `network` false, mode `replay`, live 11, fallback 10 of 21, created `2026-11-03T09:33:41Z` | `data/meta_bake.json` `bake` block |

The plate's eleven lines, in the order it draws them: three caption lines, `BAKE MODEL muse-spark-1.3  MODE replay
BACKEND meta`, `BAKE TIME 2026-11-03T09:33:41Z  ROWS 21 live 11`, the three TALK turn hashes T1, T2 and T3 (three
different `request_hash` values, which is what proves three calls and not one line reused), the `NETWORK OFF`
badge, `NETWORK DEAD SINCE THE FIRST FRAME.` and `THESE REPLIES CAME FROM data/meta_bake.json.`

## The measurements on the shot itself

`python tools\stage_s6_offline.py --check-only output\demo\s6-offline-2026-11-11.mp4` decodes frames out of the
encoded mp4 and measures them. All fifteen rows pass:

- frame size 768x990, frame rate 60/1, one stream and no audio (the recording it cuts carries none)
- plate on screen at 2.00 s, 22.40 s and 42.80 s: 132,519, 132,500 and 132,504 of 177,120 plate pixels
- bake ink on screen at those three times: 19,878, 19,875 and 19,877 ink pixels
- band not black at those three times: 178,309 and 178,092 of 207,360 pixels lit
- band black outside the window at 0.80 s and 44.00 s: 4 and 5 of 207,360 pixels lit, which is encoder ringing at
  the plate's own edge and is reported rather than rounded to zero
- the game's frame is the recording's: mean channel difference 1.42, 7 of 552,960 pixels over 48 levels

The fight resolving is measured too, not assumed. The recording's own verify file puts its `spare_result_in_sample`
frame at `t_0059.png` (second 59.0 of the recording, which is second 40.4 of the shot). A one-off probe compared
frames decoded out of the shot at 39.9 s to 40.9 s against that frame: from 40.6 s on the mean channel difference is
1.85 with 0 of 552,960 pixels over 48 levels, so the SPARE outcome is on screen from 40.6 s and the plate stays up to
43.4 s. That probe is not in `tools/stage_s6_offline.py` yet; it is recorded here so the next lane can measure it
again rather than take it on trust.

## The project's own frame test, on a lossless render of the same plate

`python tools\demo_overlay.py --check --shot S6 --source output\first_fight_talk_frames\t_0047.png --frame
output\s6_offline_2026-11-11\plate_render_t0047.png --below` prints sixteen PASS rows, among them
`PASS network badge  NETWORK OFF in the hazard role: 1564 pixels`, `PASS text box untouched: battle text window
(pp_battle_director.gml text box y2)  rect (0, 0, 768, 144)`, `PASS text box untouched: battle command menu
(specs/07-battle-director.md line 47)  rect (0, 504, 768, 720)` and `PASS the bake lines are what put ink there
11262 ink pixels against 0 blanked`. The 1564 badge pixels are the same count the 2026-10-29 entry recorded.

## The offline half, measured on Pine

`python pine_offload.py --cmd "cd projects/primordial-paradox && python -m pytest tests/test_no_network_in_build.py -q"
--name s6net3` ran the build's own offline proof on Pine and reports `13 passed in 5.25s`, exit 0, in
`../arananet/pine/data/results/offload-s6net3-0.json`. That test is the project's definition of "the bake is still
served with the network off": it forces `PP_AI_MODE=replay`, removes every key from the environment, replaces
`urllib.request.urlopen` with a trap that fails on any socket, rebuilds every talk request from committed source data
and looks it up by `request_hash`, and proves `game/datafiles/meta_bake.json` is byte identical to the source.

The stage run itself is also socket-trapped. `output/demo/s6-offline-2026-11-11_verify.json` records
`"socket_opens_during_stage": 0`, so the staging run opened no connection of any kind.

## The receipts, labelled

`python tools\check_receipts.py --verify output\demo\s6-offline-2026-11-11_verify.json` re-reads every number,
re-hashes its source and exits 0: `12 Meta numbers, 12 quoted receipts, 17 logged`. The four this stage added:

```
meta.s6_offline_plate_lines = 11 (measured, receipt rcpt-b0745d6029a19fae) from data/meta_bake.json
meta.s6_offline_source_seconds = 73.8 (measured, receipt rcpt-95d81b3b69338f64) from output/first_fight_talk_capture.mp4
meta.s6_offline_window_seconds = 42.0 (computed, receipt rcpt-d803f931d91388ce) from tools/stage_s6_offline.py
meta.s6_offline_cut_seconds = 55.2 (computed, receipt rcpt-952cf8158a3b7c47) from output/first_fight_talk_capture.mp4
```

The eight build numbers the panel quoted travel in the same block on the same labels: `meta.fallback_rows` 10
computed (`rcpt-a25d011c60f7d140`, the panel's own receipt), `meta.live_rows` 11 measured, `meta.live_share_pct` 52.4
computed, `meta.model_calls` 21 measured, `meta.rows` 21 measured, `meta.system_chars` 2408 measured,
`meta.bridge_receipts` 157 measured (the count moved up from the panel's 156 because another lane logged a bridge
call after that panel ran), `meta.talk_turns_onscreen` 3 inferred.

## What this does not prove

1. **The take was not recorded with the adapter down.** The verify file records the adapter's own state at stage
   time as up (`host_network_at_stage.adapter_up` true, DNS lookup and TCP connect both answered). This tool does not
   disable the adapter and does not claim it did: the fight pixels in this shot come from
   `output/first_fight_talk_capture.mp4`, recorded 2026-10-24, and what was forced down was every socket the stage
   could open, not the machine's network card. The adapter-down take section 5 describes still needs a desktop no
   automation is driving: `python tools\idle_check.py` refuses with exit 4 while `codex.exe` runs, exactly as it did
   for the 2026-11-11 nightly (card t_a990b663).
2. **No audio.** The recording carries none, and this card did not add a bed. Sound belongs to the cut, and
   `tools/demo_bed.py` builds it there.
3. **The plate is static for its whole window.** Section 4 gives the three TALK rows three separate marks; this shot
   shows all three rows together from the battle's first frame, because the overlay draws them as one plate. A cut
   that wants one row per turn has to draw three plates, which is a change to `tools/demo_overlay.py` and not to
   this stage.

## Q: for gamedev

`NETWORK DEAD SINCE THE FIRST FRAME.` is drawn from the bake's own `network` and `offline` flags, which are measured,
and the same plate is already burned into `output/demo/cut-180-2026-11-11.mp4`. Tonight's stage has the host adapter
up, so the sentence is true of the bake and not of the recording session. Three readings exist and one is gamedev's
to rule:

1. the line describes the bake, and the bake's flags are the authority (today's behaviour, and what the plate says it
   does in its own docstring);
2. the line describes the take, so no shot carries it until someone records with the adapter down and the idle gate
   is free;
3. the line is reworded to what can always be proved, for example `NO REQUEST LEFT THIS MACHINE`, which is the same
   claim the socket trap measures.

Until that ruling, this shot and the 180 s cut carry reading 1.

## Re-run

```
python tools\stage_s6_offline.py                 stage today's shot
python tools\stage_s6_offline.py --check-only output\demo\s6-offline-2026-11-11.mp4
python tools\check_receipts.py --verify output\demo\s6-offline-2026-11-11_verify.json
```

A second stage over the same recording writes the same bytes: measured twice on 2026-11-11, both runs produced
1,514,054 bytes and sha256 `ec5925bc7c92dc9f19d7731763d7acaaced7b23d222aeb67137601324aaa93a4`.
