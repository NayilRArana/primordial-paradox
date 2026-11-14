# Picture review checklist

Every picture that enters this game is reviewed against the NES hardware limits before a lane reports it
done: an art source under `game/sprites_src/`, a composed 256 by 240 frame, and any capture a card offers as
evidence. This page is the checklist, and `tools/review_gate.py` is the command that applies it, so a review
is a run and not an opinion. The limits come from `knowledge/ART-BIBLE.md` and `specs/13-8bit-look.md`, and
the arithmetic lives in `tools/nes_check.py` and `tools/nes_composite_check.py`; this page restates neither,
it points at them.

## The gate

One command per picture, from the repository root:

```sh
python tools/review_gate.py output/title_run_1.png --no-sprites
python tools/review_gate.py frame.png --sprite-mask mask.png --sprite-height 16
python tools/review_gate.py game/sprites_src/chars/hadrian_ow.png --type sprite
python tools/review_gate.py layer.png --type background --backdrop "#000000"
```

Exit 0 is a pass and nothing else is. Exit 1 is a reject, or a rule that applies to the picture and was not
measured. Exit 2 is a picture or an argument the gate cannot read. The gate imports the two shipped checkers
and prints one row per rule, with every offending area, tile, sprite or colour the checker named.

`--type auto` reads a 256 by 240 picture and its 768 by 720 three times capture as a frame, and anything
else as a background layer. A demo still is 768 by 784, because the capture carries a band, so it needs
`--type frame`: the gate then looks for a 768 by 720 viewport that is made only of PPU colours and refuses
the picture at R2 when there is none, which is what a still cut from the h264 is.

## The eight checks

| id | rule | limit | enforced by |
| --- | --- | --- | --- |
| R1 | the picture is readable and on the 8 by 8 grid | 8 pixel tiles | `tools/nes_check.py` |
| R2 | every pixel is a PPU output; a full colour frame is refused | the 64 entries of `data/nes_palette.json`, less the ones flagged unusable | `tools/nes_composite_check.py` |
| R3 | colours besides the shared backdrop in one 16 by 16 area | 3 | `tools/nes_composite_check.py` |
| R4 | background palettes in one frame | 4 groups of 3 | `tools/nes_composite_check.py` |
| R5 | opaque colours per sprite tile | 3 plus transparency | `tools/nes_check.py` |
| R6 | sprite palettes in one frame | 4 groups of 3 | `tools/nes_composite_check.py` |
| R7 | sprites on any scanline, and in OAM | 8 per line, 64 per frame | `tools/nes_composite_check.py` |
| R8 | colours on screen in one frame | 25 | both checkers |

R2 is the rule the checklist exists for. A photograph, a 32 bit screenshot with smoothing, a capture whose
viewport was resampled, or any picture produced by a filter fails it no matter how retro it looks, because
the pixels are not outputs of the Ricoh 2C02. R5 to R7 need to know which pixels belong to sprites, so a
frame is judged on them only with `--sprite-mask` or `--sprites`; without either the gate says NOT MEASURED
and exits 1. `--no-sprites` is the reviewer stating that the picture carries no sprites, and it is the only
way those three pass without evidence. NOT MEASURED is never a pass, and a SKIP is never a pass.

## The whole tree, before a release

```sh
python tools/nes_audit_all.py
python tools/check_runtime_palette.py
```

`tools/nes_audit_all.py` runs both checkers over every art source and every 256 by 240 frame and fails on a
gated file, and its page is `knowledge/NES-AUDIT.md`. `tools/check_runtime_palette.py` covers what no picture
can: the flat rectangles and glyphs the game draws at run time, resolved through the palette table.

## What a reviewer writes on the card

A review is closed only by a run, so paste its output, not a sentence about it:

```text
review_gate: <path>  (<kind>, <width> by <height>)
  R2 PASS  every pixel is a PPU output
  R3 PASS  every 16 by 16 area carries 3 colours besides the backdrop
  R8 PASS  the frame shows at most 25 colours
review_gate: PASS, every rule that applies to this picture passed
```

`review_gate: REJECT` or `review_gate: NOT MEASURED` on the last line is a card that stays open. The JSON
form, `--json`, is the record to attach when the card asks for one.

## What is not evidence

* A still cut from the demo h264. The video is 768 by 784, three times the frame plus a band, and the
  encoder is not the chip: the gate refuses such a still at R2, because no 768 by 720 box inside it is made
  only of PPU colours. The frame it came from is what gets judged, or the run that produced it.
* A screenshot of the game window used as proof of the art. It carries the compositor's own scaling, so a
  failure there measures the capture path; `tools/nes_audit_all.py` marks those captures advisory for that
  reason, and an advisory red is still a red.
* A number typed into a card or a page. Every limit on this page is read from the module that enforces it,
  and every command is one a reader can run.
* "It reads as 8 bit." R2 is a pixel membership test and R1 to R8 are counts, not impressions.

## Where this checklist is held to the tree

`tests/test_review_gate.py` proves the gate refuses a full colour frame, passes a legal one, and answers
exit 1 when the sprite rules are unmeasured. The same file runs `tools/check_readme.py` over this page, so a
path or a command named here that has moved fails the suite instead of aging quietly.
