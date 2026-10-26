# PLAY-DEMO-COVER: a window over the game is a polluted take, not an art finding (card t_5d1a6ec4)

Written 2026-10-26, while closing the gap the SHIP-BOX-FRAME card (t_769b545d) left behind. Two problems, one
card, because they have one cause: a desktop automation on this host was taking focus and input every 90 to 110 s
and the capture harness could not tell that from Nayil at the keyboard or from the art lane drawing badly.

## The measurement the whole split rests on

`tools/play_demo.py` sampled seven frames from every take on disk. The share of a frame's pixels that sit within
12 levels of a legal 2C02 colour, measured on 2026-10-26:

| take | frames of the game | frames a window covered |
| --- | --- | --- |
| demo-box-2026-10-26 | 0.9285, 0.9730, 0.9939, 0.9406, 0.9343 | 0.0025 and 0.0024 at t=36.8 and t=48.5 |
| demo-talk-2026-10-26 | 0.9311 to 0.9936 over all seven | none |
| demo-walk-2026-10-26 | 0.9280 to 0.9938 over all seven | none |
| nightly-2026-10-26 | 0.9297 to 0.9936 over all seven | none |
| hold_walk-2026-10-26 | 0.9402 to 0.9443 over all five samples | none |

Thirty three frames of the game, all between 0.9285 and 0.9939. Two frames of a window, at 0.0025 and 0.0024. So:

- `OFF_PALETTE_ART_MIN = 0.50` is the split. Under it, most of the screen is not a 2C02 colour, which a drawing
  mistake cannot produce, because the game resolves every colour it draws through `data/palette_ppu.json` (card
  RUNTIME-PALETTE, t_54db4d0f). Those frames are "not the game" and fail the take as polluted.
- Between 0.50 and the 0.90 palette floor is the art lane's case: the game's own picture with some colours the NES
  cannot output. That finding still exists and still says so.

Two other measurements were tried and thrown away, honestly:

- a 3x block structure score (the game is a 3x nearest neighbour upscale of 256x240, so a foreign window should not
  have 3x blocks). It does NOT discriminate: the covered frames scored 0.9416 and 0.9442, the game's own frames
  0.7696 to 0.9939. The covering window was itself scaled. Rejected.
- a colour count (flat pixel art has few colours, a window has thousands). It does not discriminate either, because
  h264 turns a real game frame into 4,535 to 20,741 distinct colours. Rejected.

A whole screen jump signature was measured too, on real frames: a game scene change reads 0.896, a window arriving
reads 0.968, and the same window twelve seconds later reads 0.000. So a jump cannot say who caused it, which is why
it is recorded as evidence and never as a verdict.

## What the harness does now

1. While the recording runs, `PollutionWatch` asks Windows who owns the rectangle once a second
   (`capture_title.cover_report`, the same five points the pre and post checks use) and keeps a 48x45 signature of
   the pixels. A foreign owner marks the take polluted, names the process image and the window title, and after two
   consecutive samples the run is stopped instead of finished. A jump is recorded only when the game's own log did
   not grow during that poll, which is the card's wording ("a whole-screen jump that the run's own log does not
   explain"), and it never fails a take on its own.
2. `verify_video` has a seventh check, `not_polluted`, and the palette finding is split into two verdicts. A take
   checked from disk alone (`--check`) has no run log, so that check says UNMEASURED when every frame is the game's
   and FAIL when a frame is not, and the finding text says "not the game ... NOT an art finding" instead of sending
   the audit lane to look at a terminal window.
3. `tools/idle_check.py` asks the process list (`tasklist /NH /FO CSV`, because its table form cuts an image name at
   25 characters and `codex-computer-use-swift.exe` is longer) and, when a desktop automation is running, refuses
   and names it. It does not allow a launch on the strength of the automation's silence: a window opened under a
   desktop automation is covered mid recording, which is exactly how this card's two frames happened. A process list
   that cannot be read is one line saying so, and the tick still decides.

## What was proven, and what was not

Proven, on this host, 2026-10-26:

- `python tools/play_demo.py --check --video output/demo/demo-box-2026-10-26.mp4` -> exit 1, "POLLUTED 2 of 7
  sampled frames are not the game: t=36.8 share 0.003, t=48.5 share 0.002 ... NOT an art finding". Before this card
  the same file printed "FINDING 2 of 7 ... this is an art finding for the audit lane".
- The same command on demo-talk, demo-walk and nightly -> exit 0, six checks PASS. A clean take still passes.
- The watch's two real Windows hooks, run live for four seconds against a rectangle on this desktop: four samples,
  each naming `Hermes.exe` as the owner, stop requested after two, thread stopped. It opened no window and pressed
  no key.
- `python tools/idle_check.py` -> exit 4, "a desktop automation is running (codex-computer-use-swift.exe, codex.exe)
  ... That input is not Nayil at the keyboard". Before this card the same command said "input 8 s ago, 180 s
  required", which is the sentence that hid the cause through four re-records.

NOT proven: a take actually recorded with a window raised over the game mid run. The idle gate refuses on this host
because the automation that caused the defect is still running, `--force` is forbidden by the card, and opening a
window to prove the point would break the standing rule the gate exists for. The during-recording path is proven
with injected samplers (owner sampler, screen grab, log line counter) and with the real hooks run live against a
rectangle that is not the game's; the verdict on a covered take is proven against the real take that carries the
defect this card was written about.

## Follow-ups this card does not take

- `play_demo` still appends a failure if, after the recording, another window owns a sampled point of the rectangle.
  That check runs after `restore_foreground(previous)`, so it can be measuring the window this tool itself brought
  back. It is not part of the pollution verdict on purpose (feeding it in would condemn clean takes), but somebody
  should measure whether it ever fires on a clean run.
- No automatic re-record on pollution. The take is kept, marked and named, because a polluted file is evidence of
  the automation, and a retry loop would fight that automation for the screen.
