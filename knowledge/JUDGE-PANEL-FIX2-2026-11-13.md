# JUDGE-PANEL fix 2, drawn: the judged line, the bridge log, three receipts and the network line (2026-11-13)

Card `t_bdb645a5`, testing lane. Continues `t_21951674` (commit `db1d30c5`, Morgan's judged player
line inside the NES dialogue box from scene data) and `t_29a8e5e1` (`tools\demo_overlay.py`'s receipt
plates). Source of the requirement, verbatim from `knowledge\JUDGE-PANEL-2026-11-14.md`, fix 2,
priority 91, criterion "Use of Meta AI tooling":

> Change the morgan battle scene to print the live verdict line inside the NES text box with the label
> MUSE SPARK 1.3 and the mercy delta. Log the request to the local bridge and draw the three bake
> receipts plus the network line during S5 from 1:18 to 1:50. A judge will see the talk judged on
> screen and the receipts prove the model did the work in the video.

Four clauses, four places. Nothing here re-does `db1d30c5`: the dialogue box still gets its Morgan
line from `data\scenes\all.json`.

## 1. The verdict line in the box, with the label and the delta

- `pp_talk_judge_label()` (`game\scripts\pp_battle_text\pp_battle_text.gml`) joins two data files by id:
  `data\meta_bake.json`'s `bake.model` is the id, and `data\credits.json`'s `roll.models` is the one
  table in this project that already prints a model to a player. The label is `display` for that
  `model_id`, which is `MUSE SPARK 1.3`. No GML and no second data file types the name, so a rebake that
  names another model changes the line or stops it instead of leaving the old name over a new answer.
  `pp_credits_roll_data()` now carries `models` so the box and the S6 roll read the same table.
- `pp_talk_judge_line(_delta)` builds `MUSE SPARK 1.3 MERCY UP 20`, `... MERCY DOWN 10` or
  `... MERCY HELD 0`, from `data\talk_live.json`'s `will.label` (the bar's own name) and three new
  string keys `judge_up`, `judge_down`, `judge_held`. It returns `""` when the line is wider than the
  box's `cols` or carries a character `spr_pp_font8` cannot draw, so a box with no room says nothing.
- It is appended to the **same reply board** the reply types on, which is the row inside the box:
  `pp_talk_step` adds it for a bake row (`_record.baked`), `pp_talk_live_answer` adds it for an answer
  whose bridge source is `meta`. A card pool reply and a fallback answer carry no model, so neither
  prints one.
- The line has no `* ` narration marker on purpose: at 28 columns the marker is exactly what pushes
  `MERCY DOWN 10` over the box's width, and the marker is the reply's shape, not the record's.

## 2. The request to the local bridge, logged

`pp_talk_live_send_talk` (`game\scripts\pp_talk_live\pp_talk_live.gml`) now logs, before the send:

    PP: talk live request to <host>:<port><talk_path> for <whom>, <n> bytes of body

Host, port and path come from `data\talk_live.json` (`_d.host`, `_d.port`, `_d.talk_path`); `whom`
comes from `pp_talk_live_whom`, the scene's character, the persona id or the fight's enemy. The
player's own words appear only as `string_length(_battle.live_text)`, which is what spec 19 section 3
and the existing scene-answer log already require. No address literal is typed in GML.

## 3. The three bake receipts and the network line inside S5

`tools\demo_cut_180.py` composites them, before this card, only as a network window and with no plates
at all. Now `OVERLAY_WINDOWS` carries `("S5", "receipts", 83.40, 104.00, [])` and
`("S5", "network", 101.00, 104.00, [])`: the strip starts on section 4's first receipt clock (1:23.4)
and both end on the network window's last frame (1:44.0), inside S5's 1:18.00 to 1:50.00.

- `overlay_plan()` is new and is the one list of rectangles: the render crops it and the check measures
  it, so a plate cannot be drawn where the frame test did not measure it. One window can be several
  rectangles, which is how the receipts window lays down three plates instead of one plate with the
  game's picture in the gaps between them.
- The plates are `meta.model_calls`, `meta.live_rows` and `meta.live_share_pct` (306x50, 306x50,
  316x50 at x 24, y 334, 390, 446), each under the id of the ledger receipt that backs it, and they
  clear the game's own dialogue box, which starts at y 504.
- `RECEIPT_NOT_DRAWN` still says, in the plan and in the record, that S5's three rows are `fallback`
  and that no per-row receipt may be printed for them.

## 4. The commit boundary, and why the cut tool is not in it

This card's commit carries the three GML modules, `data\talk_live.json`, `tools\talk_live.py`,
`tests\test_talk_live.py` and this file. It does **not** carry `tools\demo_cut_180.py` or
`tests\test_demo_cut_180.py`, although this card wrote both, because at the moment of landing
`demo_cut_180.py` imports `tools\demo_voiceover.py` and `tools\video_builder.py`, and both of those
were written by the fix-1 card (`t_5876de50`, title card and narration) and were still uncommitted.
Committing the cut tool without them ships a module that cannot import, which the suite measured as
five collection errors in a tree of HEAD plus this card's paths. Both files stay in the working tree,
green, and land with the fix-1 card's files; the video below was built from them.

## 5. What was measured, and the command that measures it

    ./.venv/Scripts/python.exe -m pytest tests/test_talk_live.py tests/test_demo_cut_180.py -q
    -> 47 passed

    ./.venv/Scripts/python.exe -m pytest tests/test_scene_talk.py tests/test_talk_scene_live.py \
        tests/test_talk_turns.py tests/test_credits.py tests/test_demo_overlay.py \
        tests/test_video_builder.py tests/test_demo_shots.py -q
    -> 146 passed

    ./.venv/Scripts/python.exe tools/check_data.py           -> all files pass
    ./.venv/Scripts/python.exe tools/sync_data.py --check     -> datafiles mirror is current: 91 files

`tests\test_demo_cut_180.py` reads S5's clock out of `knowledge\DEMO-SCRIPT.md`'s own heading, so a
window that drifts out of the shot fails there and not in a capture. It also asserts that the three
plates name the ledger receipts and values they print, that no receipt rectangle covers the dialogue
box, and that `RECEIPT_NOT_DRAWN` names both what is drawn and what is refused.

The cut, built and verified on this machine:

    ./.venv/Scripts/python.exe tools\demo_cut_180.py --build \
        --video output\demo\cut-180-2026-11-13.mp4 --workdir output\demo\work-2026-11-13
    ./.venv/Scripts/python.exe tools\demo_cut_180.py --verify \
        --video output\demo\cut-180-2026-11-13.mp4

    PASS  duration  180.000 s against 180.000 s
    PASS  frames    10800 frames against 10800 (180 x 60)
    PASS  audio     an audio stream is present, mean volume -20.3 dB
    PASS  plate_S5_receipts_meta.model_calls      0.57 of the rectangle is the plate's own paper at 93.7 s
    PASS  plate_S5_receipts_meta.live_rows        0.57 at 93.7 s
    PASS  plate_S5_receipts_meta.live_share_pct   0.55 at 93.7 s
    PASS  plate_S5_network_network                0.80 at 102.5 s

The three plate PNGs the cut laid down, read back from the frames, print
`META.MODEL_CALLS 21 / RECEIPT rcpt-a505930564032c7c`, `META.LIVE_ROWS 11 / RECEIPT rcpt-d207989303deff10`,
`META.LIVE_SHARE_PCT 52.4% / RECEIPT rcpt-d5160e529fdadb6f`.

## What this card does not claim

- **The judged line is not in the video.** The cut's S5 picture is a recording of the built game, and
  that recording predates this code. GameMaker is not installed on this machine and must not be opened,
  so the line is proven at the level it can be: the data join, the glyph sheet, the 28 column width, and
  the two call sites. A capture is the only thing that shows it on a frame.
- The three plates are the bake header's numbers with their ledger receipts. They are not a receipt for
  any single reply, and S5's rows still carry none, because they are `fallback`.
- The label is fail-closed: if `data\credits.json` lost its model row, the box would draw no judged line
  rather than a misspelled model name.

## The two traps this card walked into, so the next one does not

1. `demo_cut_180.py` wrote relative clip paths into `concat.txt`, and ffmpeg's concat demuxer resolves
   an entry against the list file's own directory, so any relative `--workdir` pointed every entry at
   `work\work\clips`. Entries are now `os.path.abspath`, for picture and audio both.
2. 28 columns is one column of headroom short of `MUSE SPARK 1.3 MERCY DOWN 10` with a `* ` marker.
   The measured width is what decided the line's shape, not taste.
