"""Primordial Paradox R7 concepts, generated on a Kaggle GPU.

Runs on a Kaggle kernel. Writes every frame into /kaggle/working/concepts/ plus
/kaggle/working/r7_manifest.json, which records the exact model, revision, seed, prompt and
sha256 of each file, so the local tool can be re-run against real model output instead of our
own deterministic painter.

Order matters: the four concepts are finished and written to disk BEFORE anything touches
segmentation, so a segmentation failure can never cost the concept run.
"""

import gc
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import traceback
from importlib.util import find_spec

WORK = "/kaggle/working"
CONCEPTS = os.path.join(WORK, "concepts")
RAW = os.path.join(WORK, "raw")
os.makedirs(CONCEPTS, exist_ok=True)
os.makedirs(RAW, exist_ok=True)


def ensure(module, spec):
    if find_spec(module) is not None:
        return "%s already present" % module
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--no-warn-script-location", spec],
                   check=False)
    return "%s installed from %s" % (module, spec)


PREP = [ensure("diffusers", "diffusers"), ensure("transformers", "transformers"),
        ensure("accelerate", "accelerate"), ensure("safetensors", "safetensors"),
        ensure("keras_hub", "keras-hub")]


MANIFEST = {
    "lane": "kaggle-gpu",
    "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "python": platform.python_version(),
    "host": os.environ.get("KAGGLE_KERNEL_RUN_TYPE", ""),
    "concepts": [],
    "steps": [],
}
MANIFEST["prep"] = PREP


def note(message):
    print("R7| " + str(message), flush=True)


def record(key, value):
    MANIFEST["steps"].append({"step": key, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                              "detail": value})
    note("%s: %s" % (key, str(value)[:400]))


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


# --------------------------------------------------------------------------------------------------------------------
# The four subjects. Frame size matches what tools/kaggle_r7.py reads for each kind.

SUBJECTS = [
    {
        "id": "quay_dusk_scene",
        "kind": "scene",
        "size": [256, 240],
        "seed": 70241,
        "prompt": (
            "8-bit NES pixel art background for a side-on RPG battle, ship harbour quay at dusk, "
            "three wooden masts against a burnt orange and purple sky, calm dark water with thin "
            "highlights, stacked wooden crates on grey stone, two lit lanterns, limited palette of "
            "thirteen colours, chunky pixels, hard colour steps, no dithering, no text, no characters"
        ),
        "negative": "photo, 3d render, blurry, gradient mesh, text, watermark, signature, dithering",
    },
    {
        "id": "deck_night_scene",
        "kind": "scene",
        "size": [256, 240],
        "seed": 70242,
        "prompt": (
            "8-bit NES pixel art background for a side-on RPG battle, wooden ship deck at night, "
            "plank floor, a thick mast, a rope rail, one lit lantern, cold blue night sky with a few "
            "stars, limited palette of thirteen colours, chunky pixels, hard colour steps, no "
            "dithering, no text, no characters"
        ),
        "negative": "photo, 3d render, blurry, gradient mesh, text, watermark, signature, dithering",
    },
    {
        "id": "wardroom_scene",
        "kind": "scene",
        "size": [256, 240],
        "seed": 70243,
        "prompt": (
            "8-bit NES pixel art background for a side-on RPG battle, ship wardroom interior, "
            "painted plank wall, long wooden table with paper charts on it, an oil lamp on the wall, "
            "a heavy door, brass fittings, warm dim light, limited palette of thirteen colours, "
            "chunky pixels, hard colour steps, no dithering, no text, no characters"
        ),
        "negative": "photo, 3d render, blurry, gradient mesh, text, watermark, signature, dithering",
    },
    {
        "id": "percy_deck_sprite",
        "kind": "sprite",
        "size": [16, 16],
        "seed": 70244,
        "prompt": (
            "8-bit NES pixel art character sprite, one single full body figure, a tall naval captain "
            "in a long dark blue coat with gold buttons and gold trim, tan skin, dark hair, white "
            "shirt, standing still facing the viewer, plain flat mid grey background, thick dark "
            "outline, limited palette, chunky pixels, no text"
        ),
        "negative": "photo, 3d render, blurry, multiple characters, text, watermark, signature, dithering",
    },
]


# --------------------------------------------------------------------------------------------------------------------
# Model ladder. First rung wins; every rung that fails is recorded with its exception.

import torch  # noqa: E402

record("torch", {"version": torch.__version__, "cuda": torch.cuda.is_available(),
                 "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                 "vram_gb": round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)
                 if torch.cuda.is_available() else None})


def build_pipe():
    from diffusers import DPMSolverMultistepScheduler, StableDiffusionXLPipeline

    attempts = []
    rungs = [
        {"repo": "stabilityai/stable-diffusion-xl-base-1.0", "lora": "nerijs/pixel-art-xl",
         "adapter": "pixel", "steps": 28, "guidance": 6.5},
        {"repo": "stabilityai/stable-diffusion-xl-base-1.0", "lora": None,
         "adapter": None, "steps": 28, "guidance": 6.5},
        {"repo": "stabilityai/sdxl-turbo", "lora": None, "adapter": None, "steps": 6, "guidance": 0.0},
    ]

    def soft(pipe, label, call):
        # An optional speed or memory tweak must never cost the run. Newer diffusers moved these.
        try:
            call(pipe)
            return "%s ok" % label
        except Exception as error:
            return "%s skipped (%s: %s)" % (label, type(error).__name__, str(error)[:120])

    for rung in rungs:
        try:
            note("loading %s" % rung["repo"])
            pipe = StableDiffusionXLPipeline.from_pretrained(
                rung["repo"], torch_dtype=torch.float16, variant="fp16", use_safetensors=True,
                add_watermarker=False)
        except Exception as error:
            attempts.append({"repo": rung["repo"], "lora": rung["lora"], "ok": False,
                             "error": "load %s: %s" % (type(error).__name__, str(error)[:300])})
            note("rung failed to load: %s" % attempts[-1]["error"])
            continue

        extras = []
        loaded_lora = None
        if rung["lora"]:
            # The Kaggle image ships a torchao that diffusers' peft bridge refuses, so the first attempt
            # removes peft and lets diffusers load the LoRA through its own path. Honest either way: if
            # both fail, the frame is plain SDXL and the manifest says so.
            for plan in ("drop-peft", "upgrade-torchao"):
                try:
                    if plan == "drop-peft":
                        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "peft"],
                                       check=False)
                    else:
                        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U",
                                        "torchao>=0.16"], check=False)
                    pipe.load_lora_weights(rung["lora"], weight_name="pixel-art-xl.safetensors",
                                           adapter_name=rung["adapter"])
                    pipe.set_adapters([rung["adapter"]], adapter_weights=[0.85])
                    loaded_lora = rung["lora"]
                    extras.append("lora ok via %s" % plan)
                    break
                except Exception as error:
                    extras.append("lora %s failed (%s: %s)"
                                  % (plan, type(error).__name__, str(error)[:160]))
            if loaded_lora is None:
                note("lora skipped, continuing with plain SDXL")
        if rung["guidance"] > 0:
            try:
                pipe.scheduler = DPMSolverMultistepScheduler.from_config(
                    pipe.scheduler.config, use_karras_sigmas=True)
                extras.append("scheduler ok")
            except Exception as error:
                extras.append("scheduler skipped (%s)" % type(error).__name__)
        extras.append(soft(pipe, "progress_bar", lambda p: p.set_progress_bar_config(disable=True)))
        extras.append(soft(pipe, "vae_slicing", lambda p: p.enable_vae_slicing()))
        extras.append(soft(pipe, "attention_slicing", lambda p: p.enable_attention_slicing()))
        try:
            pipe.to("cuda")
        except Exception as error:
            attempts.append({"repo": rung["repo"], "lora": rung["lora"], "ok": False,
                             "error": "to_cuda %s: %s" % (type(error).__name__, str(error)[:300])})
            note("rung failed to reach the gpu")
            continue
        attempts.append({"repo": rung["repo"], "lora": rung["lora"], "lora_effective": loaded_lora,
                         "ok": True, "extras": extras})
        record("pipe", {"chosen": rung["repo"], "lora": rung["lora"], "lora_effective": loaded_lora,
                        "rungs": attempts})
        rung["lora_effective"] = loaded_lora
        return pipe, rung
    record("pipe", {"chosen": None, "rungs": attempts})
    return None, None


def generate(pipe, rung, subject):
    generator = torch.Generator(device="cuda").manual_seed(subject["seed"])
    kwargs = dict(prompt=subject["prompt"], negative_prompt=subject["negative"], width=640, height=640,
                  num_inference_steps=rung["steps"], generator=generator)
    if rung["guidance"] > 0:
        kwargs["guidance_scale"] = rung["guidance"]
    return pipe(**kwargs).images[0]


# --------------------------------------------------------------------------------------------------------------------
# Frame reduction. The concept has to be a frame the 16x16 area quantiser can read: blocky 2x2 pixels for a
# scene, and a 16x16 cutout for a sprite.


def to_frame(image, subject):
    from PIL import Image

    if subject["kind"] == "scene":
        small = image.resize((subject["size"][0] // 2, subject["size"][1] // 2), Image.LANCZOS)
        return small.resize(tuple(subject["size"]), Image.NEAREST)

    # Sprite: cut the flat background out by the corner colour, then land on 16x16 with alpha.
    frame_size = tuple(subject["size"])
    rgb = image.convert("RGB")
    corners = [rgb.getpixel(point) for point in [(0, 0), (rgb.width - 1, 0), (0, rgb.height - 1),
                                                 (rgb.width - 1, rgb.height - 1)]]
    backdrop = tuple(sum(colour[index] for colour in corners) // 4 for index in range(3))
    cut = image.convert("RGBA")
    pixels = cut.load()
    for y in range(cut.height):
        for x in range(cut.width):
            red, green, blue, _ = pixels[x, y]
            if abs(red - backdrop[0]) + abs(green - backdrop[1]) + abs(blue - backdrop[2]) < 66:
                pixels[x, y] = (red, green, blue, 0)
    small = cut.resize(frame_size, Image.LANCZOS)
    kept = small.load()
    opaque = 0
    for y in range(frame_size[1]):
        for x in range(frame_size[0]):
            red, green, blue, alpha = kept[x, y]
            kept[x, y] = (red, green, blue, 255 if alpha >= 96 else 0) if alpha >= 96 else (red, green, blue, 0)
            opaque += 1 if alpha >= 96 else 0
    if opaque < 24:
        note("%s: cutout kept only %d pixels, keeping the frame opaque instead" % (subject["id"], opaque))
        small = cut.resize(frame_size, Image.LANCZOS)
        fixed = small.load()
        for y in range(frame_size[1]):
            for x in range(frame_size[0]):
                red, green, blue, _ = fixed[x, y]
                fixed[x, y] = (red, green, blue, 255)
    return small


# --------------------------------------------------------------------------------------------------------------------

CONCEPT_ROWS = []
pipe, rung = build_pipe()
if pipe is None:
    record("concepts", "no image model loaded, nothing generated")
else:
    for subject in SUBJECTS:
        started = time.time()
        try:
            raw = generate(pipe, rung, subject)
            raw_path = os.path.join(RAW, subject["id"] + "_raw.png")
            raw.save(raw_path, "PNG")
            frame = to_frame(raw, subject)
            out_path = os.path.join(CONCEPTS, subject["id"] + ".png")
            frame.save(out_path, "PNG")
            row = {"id": subject["id"], "kind": subject["kind"], "size": list(frame.size),
                   "seed": subject["seed"], "prompt": subject["prompt"],
                   "negative": subject["negative"], "model": rung["repo"],
                   "lora": rung.get("lora_effective"),
                   "lora_requested": rung["lora"],
                   "steps": rung["steps"], "guidance": rung["guidance"],
                   "raw": os.path.basename(raw_path), "frame": os.path.basename(out_path),
                   "frame_sha256": sha256(out_path), "raw_sha256": sha256(raw_path),
                   "seconds": round(time.time() - started, 1),
                   "colours_in_frame": len({colour for _, colour in
                                            (frame.convert("RGBA").getcolors(maxcolors=1 << 20) or [])})}
            CONCEPT_ROWS.append(row)
            MANIFEST["concepts"].append(row)
            note("wrote %s %s in %.1fs" % (out_path, frame.size, row["seconds"]))
            with open(os.path.join(WORK, "r7_manifest.json"), "w", encoding="utf-8") as handle:
                json.dump(MANIFEST, handle, indent=2)
        except Exception as error:
            CONCEPT_ROWS.append({"id": subject["id"], "error": "%s: %s"
                                 % (type(error).__name__, str(error)[:300])})
            record("generate_fail", {"id": subject["id"], "error": traceback.format_exc()[-800:]})

# Free the card before segmentation: SDXL plus a TF model on one card does not fit.
if pipe is not None:
    del pipe
gc.collect()
torch.cuda.empty_cache()
note("vram in use after release: %.2f GB" % (torch.cuda.memory_allocated() / 1e9))

# --------------------------------------------------------------------------------------------------------------------
# SAM 3, text prompted, on the same kernel and the same frames. SAM 3.1 does not exist as a Meta published
# checkpoint on either hub (Hugging Face facebook/sam3 is gated manual, which needs a click nobody here can make,
# and the only sam3.1 entry on Kaggle Models is a third party re-upload), so this rung is SAM 3 itself.

SAM = {"attempted": True, "model": "keras_hub sam3_pcs", "handle": "kaggle://keras/sam3/keras/sam3_pcs/1",
       "prompts": {}, "reason_if_skipped": None}

SAM_PROMPTS = {
    "quay_dusk_scene": ["wooden mast", "wooden crate", "water", "sky"],
    "deck_night_scene": ["wooden mast", "lantern", "plank", "night sky"],
    "wardroom_scene": ["wooden table", "oil lamp", "door", "wall"],
    "percy_deck_sprite": ["naval captain", "character"],
}

if not any(row.get("frame") for row in CONCEPT_ROWS):
    SAM["attempted"] = False
    SAM["reason_if_skipped"] = "no concept frames were generated, so there was nothing to segment"
else:
    try:
        os.environ.setdefault("KERAS_BACKEND", "tensorflow")
        import glob
        import numpy as np
        import keras_hub
        from PIL import Image

        record("keras_hub", {"version": getattr(keras_hub, "__version__", "unknown")})

        def find_preset():
            """SAM 3 weights arrive mounted at /kaggle/input from model_sources, never downloaded here.

            kagglehub refuses to attach a model in a non interactive session (measured on run 2), so the
            mount is the only honest way in, and the preset is loaded from that directory by path.
            """
            for config in sorted(glob.glob("/kaggle/input/**/config.json", recursive=True)):
                folder = os.path.dirname(config)
                weights = glob.glob(os.path.join(folder, "*.weights.h5"))
                if weights or os.path.exists(os.path.join(folder, "model.weights.h5")):
                    return folder
            return None

        preset_path = find_preset()
        record("sam3_mount", {"path": preset_path,
                              "input_tree": sorted(os.listdir("/kaggle/input"))[:20]})
        if preset_path is None:
            raise RuntimeError("no SAM 3 preset mounted under /kaggle/input")
        segmenter = keras_hub.models.SAM3PromptableConceptImageSegmenter.from_preset(preset_path)
        record("sam3_loaded", {"ok": True, "from": preset_path})
        for row in CONCEPT_ROWS:
            if "frame" not in row:
                continue
            frame_path = os.path.join(CONCEPTS, row["frame"])
            with Image.open(frame_path) as handle:
                frame = handle.convert("RGB")
            pixels = np.asarray(frame).astype("float32") / 255.0
            per_prompt = []
            for prompt in SAM_PROMPTS.get(row["id"], ["object"]):
                started = time.time()
                try:
                    # The task expects a batch axis on every input, even for one image and one prompt.
                    out = segmenter.predict({"images": pixels[None, ...], "prompts": [prompt]}, verbose=0)
                except Exception as error:
                    per_prompt.append({"prompt": prompt, "instances": 0, "masks": [],
                                       "error": "%s: %s" % (type(error).__name__, str(error)[:300]),
                                       "seconds": round(time.time() - started, 1), "mask_file": None})
                    note("sam3 %s / %s failed: %s" % (row["id"], prompt, type(error).__name__))
                    continue
                scores = np.asarray(out["scores"]).reshape(-1)
                masks = np.asarray(out["masks"])
                if masks.ndim == 4:
                    masks = masks[0]
                target = (frame.width, frame.height)
                boxes = np.asarray(out["boxes"]).reshape(-1, 4)

                def resized_mask(query):
                    mask = masks[query] > 0.5
                    if mask.shape != (target[1], target[0]):
                        # The model answers at its own resolution. Scale the mask to the frame so the
                        # coverage number is a share of THIS frame, not of the model's input size.
                        mask = np.asarray(Image.fromarray((mask.astype("uint8") * 255)).resize(
                            target, Image.NEAREST)) > 127
                    return mask

                # The score distribution is the finding, not the cutoff. Record the best queries so a
                # zero instance answer can be read as "the model was not confident" rather than silence.
                order = np.argsort(scores)[::-1][:8]
                top = [{"score": round(float(scores[q]), 4),
                        "coverage_percent": round(100.0 * float(resized_mask(q).mean()), 2)}
                       for q in order]
                kept = []
                threshold = None
                index_map = np.zeros((target[1], target[0]), dtype="uint8")
                for level in (0.5, 0.25, 0.1):
                    kept = []
                    index_map = np.zeros((target[1], target[0]), dtype="uint8")
                    for query in range(masks.shape[0]):
                        if scores[query] < level:
                            continue
                        mask = resized_mask(query)
                        if mask.sum() < 8:
                            continue
                        kept.append({"score": round(float(scores[query]), 4),
                                     "coverage_percent": round(100.0 * float(mask.mean()), 2),
                                     "box": [round(float(value), 3) for value in boxes[query]]
                                     if query < len(boxes) else None})
                        index_map[mask] = len(kept)
                    if kept:
                        threshold = level
                        break
                mask_path = os.path.join(CONCEPTS, "%s_sam_%s.png"
                                         % (row["id"], prompt.replace(" ", "_")))
                if kept:
                    Image.fromarray(index_map, mode="L").save(mask_path, "PNG")
                per_prompt.append({"prompt": prompt, "instances": len(kept), "threshold": threshold,
                                   "queries": int(masks.shape[0]), "top_queries": top,
                                   "masks": kept[:12],
                                   "seconds": round(time.time() - started, 1),
                                   "mask_file": os.path.basename(mask_path) if kept else None})
                note("sam3 %s / %s -> %d instance(s) at %s, best score %s"
                     % (row["id"], prompt, len(kept), threshold, top[0]["score"] if top else "none"))
            SAM["prompts"][row["id"]] = per_prompt
        attempts_total = sum(len(rows) for rows in SAM["prompts"].values())
        attempts_ok = sum(1 for rows in SAM["prompts"].values() for row in rows if "error" not in row)
        SAM["attempted"] = attempts_ok > 0
        if attempts_total and not attempts_ok:
            first = next(row["error"] for rows in SAM["prompts"].values() for row in rows if "error" in row)
            SAM["reason_if_skipped"] = ("the model loaded from the mount but every prompt failed; first: %s"
                                        % first)
    except Exception as error:
        SAM["attempted"] = False
        SAM["reason_if_skipped"] = "%s: %s" % (type(error).__name__, str(error)[:400])
        record("sam3_fail", traceback.format_exc()[-1200:])

MANIFEST["sam3"] = SAM
MANIFEST["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
with open(os.path.join(WORK, "r7_manifest.json"), "w", encoding="utf-8") as handle:
    json.dump(MANIFEST, handle, indent=2)

note("done. concepts: %d, sam3 attempted: %s" % (len(MANIFEST["concepts"]), SAM["attempted"]))
note("output tree: %s" % json.dumps(sorted(os.listdir(CONCEPTS))))

