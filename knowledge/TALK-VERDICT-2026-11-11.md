# TALK VERDICT ON THE FIGHT SHOT: the box, the verdict and the two build receipts, measured (card t_b9173f05)

Judge panel fix 2 of 5, `knowledge/JUDGE-PANEL-2026-11-12.md`, Impact. The panel's reason was "No TALK
interaction or verdict is visible and last three frames are identical frozen walk so player care claim is
unproven". This file records what the tree already held, what this card changed, and the one thing that is
still not measured.

## 1. What the tree already held, checked rather than assumed

- The local AI bridge and the live TALK leg exist and are tested. `game/scripts/pp_talk_live/pp_talk_live.gml`
  opens a fifth TALK entry, SAY IT YOURSELF, sends the player's line to `tools/ai_bridge.py` on 127.0.0.1
  (async, 780 step budget, deterministic fallback at the end of it), and the answer moves the MERCY bar.
  `tools/capture_talk_live.py`'s frames in `output/talk_live_capture/` are a RECONSTRUCTION from the sheet and
  the GML geometry, not a screenshot, and their own `capture.json` says so.
- The three TALK rows for the deck watch are LIVE answers in the current bake:
  `fight/navy_sailor/1` (soften, persuaded, +20), `/2` (nudge, persuaded, +5), `/3` (setback, angered, -10),
  all `source: live`, `network: true`, all model `muse-spark-1.3`, bake written 2026-11-03T09:33:41Z.
- The bake header carries `calls_attempted` 21 and `system_chars` 2408, the two numbers the panel named, and
  every row's own `request.system_chars` is 2408 as well.
- `tools/demo_overlay.py` already drew the S5 TALK box (row, verdict, receipt) and the S6 three row plate.

So the verdict itself was never missing from the record. What was missing on the fight shot was a drawing
that shows the *player's line being judged* and the verdict beside it.

## 2. What this card changed

1. `tools/demo_overlay.py`, the S6 TALK box. `TALK_BOX_SHOTS` is now `("S5", "S6")` and the box holds, in
   order: the header, the row's own `player_line` (the line the player typed, wrapped to the box's 28
   columns), the row's reply lines, the verdict and the WILL it moved, that verdict's ledger receipt, then
   the two build numbers the panel asked to keep visible, each with its own receipt:
   `BAKE CALLS 21 RECEIPT rcpt-a505930564032c7c` and `SYSTEM PROMPT 2408 CHARS RECEIPT rcpt-f3f7be8c49be6e61`.
   Not one id is typed in the file: `ledger_number()` reads the newest ledger row for the name and refuses
   if its own `value` is not the number the bake now holds, so a receipt for 21 calls can never stand beside
   a bake that says 22.
2. Placement. The band between the battle's message window (y 0 to 48) and its command menu (y 168) is the
   battle stage itself: the sailor, his label and the HP/WILL strip are in it. Drawing the box there would
   cover the fight the shot is about, so on S6 both the plate and the box are drawn under the frame
   (`--below`, `TALK_BOX_ANCHOR["S6"] = "below"`), which is DEMO-SCRIPT section 4 rule 2 kept: the overlay
   goes under the frame or beside it, never inside the 256 by 240 area. The two game text boxes stay byte
   identical, and the frame test says so on every run.
3. `tools/render_talk_box_still.py` renders the still, measures it with `demo_overlay.check_frame`, and
   writes the verify file beside it. `tools/receipts.py`'s `_log` now re-issues a receipt whose source file
   moved: the id is a hash of name, label, value, source and locator, so the 2026-11-03 rebake kept every id
   and the ledger went on naming the 2026-10-30 sha256, which failed every verify file that quoted one.
4. `tests/test_demo_overlay.py` gained six tests and one rewritten one (34 in the file, all passing): the
   player's line is drawn as recorded, the reply and verdict follow it, both build receipts are printed with
   their own ids, every line fits the window in pixels and the player's and sailor's words fit in 28 columns,
   a header and a row that disagree about the system prompt length are refused, a ledger receipt for another
   number is refused, and the frame test on S6 leaves the frame untouched.

## 3. The measured result

    python tools\render_talk_box_still.py --frame output\first_fight_talk_frames\t_0025.png
    PASS  S6 still at output\demo\overlay\S6_talk_box.png, 26 checks, verify at output\demo\overlay\S6_talk_box_verify.json

- still `output/demo/overlay/S6_talk_box.png`, 768x1174, sha256
  b2349fa8d6b9f7eac9b49af416fbeedc799035fee944aa47f41d8d0f0912b5b9
- frame it was drawn on `output/first_fight_talk_frames/t_0025.png`, sha256
  c6f224e8b070489e520e09d2d165dcb7d84b59a9374502442d59066250f0b4a1, a real frame of the first TALK
  fight whose own message window is EMPTY, so no word of the game's own contradicts the box
- 26 of 26 checks pass: plate pixels, ink on all seven bake lines, ink on all eight box lines, the verdict in
  the warn role, the receipt id on a line of its own, no ink outside a line box, both game text boxes byte
  identical to the frame, and nothing outside the two drawn rectangles changed
- `tools/check_receipts.py --verify output/demo/overlay/S6_talk_box_verify.json` exits 0: 8 Meta numbers,
  8 quoted receipts, all three labels present
- tests: `test_demo_overlay.py` 34 passed, `test_judge_frames.py` 12, `test_receipts.py` 15,
  `test_demo_shots.py` + `test_copy_tells.py` + `test_video_builder.py` with those 98 passed, the six TALK
  suites (`test_talk_live`, `test_talk_scene_live`, `test_talk_baked`, `test_talk_guard`, `test_talk_personas`,
  `test_scene_talk`) 139 passed
- `tools/check_copy_tells.py`: 0 flags across the four channels

Note on RULE 0 (ART-BIBLE, palette first): nothing here invents art or a colour. The plate, its border, the
badge and the box take their colours from `data/palette.json` roles and the text from the video's own caption
font, so there is no off palette pixel to convert afterwards.

## 4. What is NOT measured, and why

The panel judged a video, and this card still cannot show one. `python tools/idle_check.py` exits 4 with
"a desktop automation is running (codex.exe)" on this host at 2026-11-11 21:5x, so no game window may open
and `tools/play_demo.py` cannot record. The still is the drawing and the record measured on real game pixels;
the take itself is unrecorded, and the honest name for the claim is "the card is ready to be recorded", not
"the video shows it".

## 5. Q: for gamedev

None of these is decided here.

1. Q1, the S6 box and the script's claim line. `knowledge/DEMO-SCRIPT.md` section 4 gives the box to S5 and
   gives S6 "the three TALK replies, one per turn" as a plate of three bake rows. This card adds the box to
   S6 as well, under the frame, and leaves the plate and its three rows exactly as they were. If gamedev
   wants the S6 row of the shot table to say so, the line becomes "caption plus three bake rows plus the TALK
   box plus the network line". No second of the shot changes.
2. Q2, the take and the dead network. Section 5 records S6 with the network adapter down, which is the
   architecture's promise (D5: the shipped build holds no key and makes no call). The bridge is loopback
   only, so a live leg *could* answer during that take from `data/ai_cache` and say on its own line where the
   words came from, but the panel's sentence ("a live Meta model verdict types into the NES textbox") reads
   as a WAN call, which section 5 forbids. Either the shot keeps the record (this card's still, plus the box
   during the take) or the script allows a warmed cache answer on the live leg. That is the script owner's
   call, not this lane's.
3. Q3, the demo path's fourth option. Section 8 says the demo takes the three context options and not the
   free typed line. Fix 2 asks for a player line judged on screen, which is the typed line. If gamedev wants
   it, the shot table needs the fifth entry (SAY IT YOURSELF) plus a typed line, and `tools/play_demo.py`
   already reports which leg a take used (`talk_report`, LIVE_TALK_NEEDLE), so the take would prove itself.
