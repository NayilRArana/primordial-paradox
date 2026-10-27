# SAM 3.1 segmentation, recorded live (card SAM-SEGMENT-LIVE)

Written 2026-10-26 on the desktop node CitadelArana, from a live call through
`tools/meta_client.py`. This note is the human readable record of the artifact; the artifact
itself is the cache entry it names, and the numbers here are copied from the run that produced
it, not from memory.

## What was called

    model          sam-3.1 (the id tools/meta_client.py routes for the segment role)
    endpoint       POST https://api.meta.ai/v1/responses, non streaming
    prompt         "ship"  (one noun phrase, as the docs ask)
    image          output/art_audit_2026-10-26/frames/concept_sdxl.png
                   256 x 240, RGB, 9888 distinct colours, 47263 bytes
                   sha256 7ee47548795ba47d2090ad95e29aefd0b16daba5efb34ca4ea651155fdc60e26
    metadata       {"mask_encoding": "one_bit"}
    mode           record, so the answer went to data/ai_cache
    call time      1.2 s, HTTP 200

The key was read from `HKCU\Environment` inside the runner process because the worker environment
did not carry it. It was never printed, written to a file, put in argv or committed; only the
variable name and its length were echoed.

## What is on disk

The cache entry, backend `meta`, model `sam-3.1`, network `true`, recorded at
`2026-10-27T00:59:26Z`:

    data/ai_cache/33101a9973cd1398980b986c5479e95d4b17fea3327a24f529df0a9b405dec5b.json   2384 bytes

Its response holds the raw special token line, the two boxes, the two mask payloads, and two
`objects` records with each mask's own raster size:

    object 0   box [144, 105, 219, 163]   frame [256, 240]   mask 76 x 59   one_bit
    object 1   box [35, 39, 92, 144]      frame [256, 240]   mask 58 x 106  one_bit

Every mask is the size of its own box: 219 - 144 + 1 = 76 and 163 - 105 + 1 = 59, and
92 - 35 + 1 = 58 and 144 - 39 + 1 = 106.

The rendered masks sit beside the entry:

    data/ai_cache/33101a9973cd1398980b986c5479e95d4b17fea3327a24f529df0a9b405dec5b_mask_obj0.png   271 bytes
    data/ai_cache/33101a9973cd1398980b986c5479e95d4b17fea3327a24f529df0a9b405dec5b_mask_obj1.png   405 bytes

Each is an 8 bit grey PNG the size of the source frame, 256 x 240, with 255 where the model says
the object is and 0 everywhere else. The mask is drawn at the box origin, so the PNG's own
bounding box can be measured and compared with the box the response returned.

## The check, printed both ways

    python tools/sam_mask.py data/ai_cache/<entry>.json --out data/ai_cache/<entry>_mask.png --verify-against <extracted meta_sam_parser>

    obj0  mask 76x59, box size 76x59, set pixels 2673
          PNG bbox [144, 105, 219, 163]   box from the response [144, 105, 219, 163]   equal
    obj1  mask 58x106, box size 58x106, set pixels 3262
          PNG bbox [35, 39, 92, 144]      box from the response [35, 39, 92, 144]      equal
    exit 0

Decoded independently, both rasters are byte identical to Meta's own `meta_sam_parser` 0.1.0
`decode_mask_to_raster`, 4484 and 6148 bytes, 100 percent equal. The package was read from an
extracted wheel; nothing was installed into this machine's site packages. The port in
`tools/sam_mask.py` is our own standard library code, reduced to the one_bit encoding.

A separate reading of the obj0 PNG describes a ship silhouette with three masts in the middle
right of the frame, which is where box 0 is. The shape is the model's.

## The grammar this needed

The client could not read a real answer before this card, which is why `boxes` came back empty on
a 200. The published grammar, read on 2026-10-26, is one line per frame, a frame marker, then
comma separated records of object id, box token and mask token:

    <Nf>id<|box;x1=..;y1=..;x2=..;y2=..;w=<frameW>;h=<frameH>|><|mask;x=0;y=0;data=<H>,<W>,<enc>PAYLOAD|>

`tools/meta_client.py` now has `segmentation_records()` for it, and `parse_segmentation()` reads
it before its older tolerant lanes. `tools/sam_mask.py` decodes the payload: length prefixed
base85, then a byte oriented range decoder over a 12 bit neighbourhood context, one bit per
pixel.

Two properties of the mask worth writing down, both from the same documentation:

> A mask record always carries a complete payload, so the raster is never partial.

Source: https://dev.meta.ai/docs/sam/reading-segmentation

> Zero matches is a valid outcome.

Source: https://dev.meta.ai/docs/sam/reading-segmentation

## The zero match entry, kept

`data/ai_cache/49e9eb8070ac...json` is a second live call, backend `meta`, network `true`, prompt
`"character"`, image `output/char_pipe/concept_synthetic.png`, and ZERO records. `person`,
`figure` and `robot` on that same flat geometric concept also returned zero in live mode probes.
The sprite pipeline's synthetic concept is not an object SAM finds, and that is a fact about the
input rather than a defect in the client, so the entry stays rather than being deleted.

## Which sprite row consumes it

`data/sprite_recipes.json` row `SP-035`, "The black silhouette test", is the recipe that reads a
silhouette: fill the figure in one colour, two identifiable features, three seconds to judge.

The sheet rows that consume `segment()`'s mask today are the overworld frames `down_0`, `up_0`,
`right_0` and battle `idle_0` in `output/char_pipe/no_poses/char_pipe_report.json`, whose
`segmentation.mask_source` is still `"local corner matte"`.

## What is still open

`tools/sprite_pipe.py` calls `ai_client.segment()`, not `meta_client.segment()`, and
`sprite_pipe.mask_from_reply()` still raises NotImplementedError. So the pipeline does not yet eat
this mask; wiring it, and segmenting a real character concept rather than a harbour scene, is the
follow up, and it is a builder lane card.

Nothing here was posted or published. Nothing is committed.
