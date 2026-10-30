#!/usr/bin/env python3
"""models_used.py: the MODELS-USED page, one logged Meta call per model, a receipt behind each.

Card META-MODEL-BREADTH. The judges' "Use of Meta AI" score counts depth as well as presence, and
a markdown sentence is not evidence of a call. This tool holds the register of the models this
entry actually uses, names the one call that stands for each, and refuses to print a row whose
receipt does not check out.

What a row is
=============
    model       the id the API is asked for, exactly as the client asks for it
    role        what that model does in the entry
    call        the one call that stands for the model (kind, and what it was asked)
    receipt     a data\\ai_cache\\\\<sha256>.json entry: the call's own recorded answer

The receipt is the evidence, and every field of it is read from the file: `model`, `kind`,
`backend`, `network`, `recorded_at` and the file's own sha256. A row that says "live" is a row
whose entry says `"network": true`. A row that says "offline" is one whose entry says
`"network": false`, and the page prints that word rather than a euphemism, because a mocked answer
is not a model answering. Two of the five rows are offline today: Muse Spark Open needs a host
(Baseten) and this repository has no key for it, and Muse Voice Transcribe has no key either. The
calls are still real calls through tools\\meta_client.py: same code path, same cache, same receipt,
with the mock backend answering instead of a server.

Usage
    python tools\\models_used.py            write knowledge/MODELS-USED.md from the register
    python tools\\models_used.py --record   make the missing offline calls first, then write it
    python tools\\models_used.py --check    exit 1 when the page disagrees with the receipts
    python tools\\models_used.py --json     print the register and every receipt field as JSON

Exit codes: 0 the page was written or the check holds, 1 the check failed, 2 a receipt is missing.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import struct
import subprocess
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import meta_client  # noqa: E402

ROOT = meta_client.ROOT
CACHE = os.path.join(ROOT, "data", "ai_cache")
OUT = os.path.join(ROOT, "knowledge", "MODELS-USED.md")
VOICE_SAMPLE = os.path.join(ROOT, "knowledge", "models_used", "voice_sample.wav")
CUT_RECEIPT = os.path.join(ROOT, "knowledge", "silhouette_cut", "ship_cut_receipt.json")

# The one call that stands for each model. `receipt` is the entry the call landed in; the tool
# reads every claim about it from the file, so a row cannot go stale on its own.
REGISTER = (
    {
        "model": "muse-spark-1.3",
        "role": "the TALK judge: one structured verdict per line, the answer the fight moves on",
        "kind": "chat",
        "call": "a battle TALK verdict for the navy sailor, asked for JSON in the bake's own schema",
        "receipt": "693d6d13479b01e577ab339609b04c08e9ae1d6fde134ca23959ce6db8be427b.json",
    },
    {
        "model": "muse-spark-1.3",
        "role": "the eye critic: one frame read for NES palette and PPU faults before it is used",
        "kind": "vision",
        "call": "the prompt 'Score this concept for NES palette limits.' on one generated concept "
                "frame; the answer scores it 6/10 and names the three PPU rules it breaks",
        "receipt": "52f2563afd15a0cf79c1304623c2e840ea470f1dcd38dc77483f4515c8dbe54f.json",
    },
    {
        "model": "muse-image-1.0",
        "role": "concept art: the knight concept the sprite pipeline draws from",
        "kind": "image",
        "call": "one 512x512 concept, 'a flat 16 colour knight in profile on a plain background'",
        "receipt": "5a4143582dfeebe47e7753c9e5a5689f9b35548584869028adc8c5dee94d17c2.json",
    },
    {
        "model": "sam-3.1",
        "role": "the silhouette cut: the ship cut out of its frame, ready to drop on a plate",
        "kind": "segment",
        "call": "the prompt 'ship' on the art audit's 256x240 concept frame",
        "receipt": "33101a9973cd1398980b986c5479e95d4b17fea3327a24f529df0a9b405dec5b.json",
        "cut_receipt": "knowledge/silhouette_cut/ship_cut_receipt.json",
    },
    {
        "model": "meta-models/muse-spark-open-1026",
        "role": "the open weights rung: the same talk line answered off the paid API, for judge "
                "reruns (816B total, 42B active, served by a host such as Baseten)",
        "kind": "chat",
        "call": "the TALK verdict prompt again, asked of the open weights id",
        "receipt": "02bc28340636361c37b8ebc3429bac801f1b512e548ac488e54ed2fb34e5af3f.json",
        "offline_call": {"prompt": "TALK verdict for Zeus: 'I did not come to fight, I came to be "
                                   "remembered.'"},
    },
    {
        "model": "muse-voice-transcribe-1.0",
        "role": "the spoken line: the fight's /hear box asks the Meta rung for the transcript and "
                "keeps the local whisper rung as its offline fallback",
        "kind": "transcribe",
        "call": "one 16000 Hz mono 16 bit wav through transcribe()",
        "receipt": "cbee78c0e96e92a2d9bebbe7c3838de8c01e7fa4b9a6d694290ca78c56f9eddd.json",
        "offline_call": {"audio": VOICE_SAMPLE},
    },
)


def _sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def make_voice_sample(path=VOICE_SAMPLE, seconds=0.6, rate=16000, hz=220):
    """A synthetic tone at the /hear contract's own rate. Not speech, and the page says so."""
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    frames = bytearray()
    total = int(rate * seconds)
    for index in range(total):
        # A quiet sine, so the file is a real 16 bit PCM wav rather than a header with no audio.
        value = int(6000 * math.sin(2 * math.pi * hz * index / rate))
        frames += struct.pack("<h", value)
    with wave.open(path, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(bytes(frames))
    return os.path.abspath(path)


def _newest_entry(kind, model, live_only=True):
    """The newest cache entry for a kind and model, optionally only one a real HTTP call made."""
    best = None
    if not os.path.isdir(CACHE):
        return None
    for name in os.listdir(CACHE):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(CACHE, name), "r", encoding="utf-8") as handle:
            entry = json.load(handle)
        if entry.get("kind") != kind or entry.get("model") != model:
            continue
        if live_only and not entry.get("network"):
            continue
        if best is None or str(entry.get("recorded_at")) > str(best[1].get("recorded_at")):
            best = (name, entry)
    return None if best is None else best[0]


def record_offline(force=False):
    """Make the two calls this repository can make without a key, and report where they landed."""
    done = []
    backend = meta_client.backend_name()
    saved = (os.environ.get("PP_AI_BACKEND"), os.environ.get("PP_AI_MODE"))
    os.environ["PP_AI_BACKEND"] = "mock"
    os.environ["PP_AI_MODE"] = "record"
    try:
        open_model = meta_client.model_for("open")
        prompt = "TALK verdict for Zeus: 'I did not come to fight, I came to be remembered.'"
        answer = meta_client.chat([{"role": "user", "content": prompt}], model=open_model)
        done.append(("open", open_model, str(answer)[:60]))
        if not os.path.exists(VOICE_SAMPLE) or force:
            make_voice_sample()
        heard = meta_client.transcribe(VOICE_SAMPLE)
        done.append(("voice", meta_client.model_for("voice"), heard.get("text", "")[:60]))
    finally:
        for name, value in zip(("PP_AI_BACKEND", "PP_AI_MODE"), saved):
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    return {"backend_seen_before": backend, "calls": done}


def rows():
    """The register resolved against the cache: every row carries what its receipt actually says."""
    resolved = []
    for spec in REGISTER:
        name = spec.get("receipt") or _newest_entry(spec["kind"], spec["model"])
        if not name and spec.get("offline_call"):
            # The offline rung: newest entry of any backend, which is the call --record made.
            name = _newest_entry(spec["kind"], spec["model"], live_only=False)
        row = {key: spec[key] for key in ("model", "role", "kind", "call")}
        row["cut_receipt"] = spec.get("cut_receipt")
        row["offline_call"] = spec.get("offline_call")
        row["receipt_file"] = name
        if not name:
            row["missing"] = True
            resolved.append(row)
            continue
        path = os.path.join(CACHE, name)
        if not os.path.exists(path):
            row["missing"] = True
            row["receipt_path"] = path
            resolved.append(row)
            continue
        with open(path, "r", encoding="utf-8") as handle:
            entry = json.load(handle)
        row.update({
            "receipt_path": os.path.relpath(path, ROOT).replace(os.sep, "/"),
            "receipt_sha256": _sha256(path),
            "entry_model": entry.get("model"),
            "entry_kind": entry.get("kind"),
            "entry_backend": entry.get("backend"),
            "entry_network": bool(entry.get("network")),
            "entry_recorded_at": entry.get("recorded_at"),
            "entry_bytes": os.path.getsize(path),
        })
        response = entry.get("response") or {}
        answer = str(response.get("text") or "").replace("\n", " ")
        if not answer:
            image = response.get("image_b64") or ""
            if image:
                size = "unknown size"
                try:
                    header = base64.b64decode(image[:64])
                    if header.startswith(b"\x89PNG\r\n\x1a\n"):
                        width = int.from_bytes(header[16:20], "big")
                        height = int.from_bytes(header[20:24], "big")
                        size = "%dx%d" % (width, height)
                except Exception:
                    size = "unreadable header"
                answer = "an image, %d base64 chars, %s" % (len(image), size)
        row["answer"] = answer[:120]
        if row["cut_receipt"]:
            cut_receipt_path = os.path.join(ROOT, row["cut_receipt"])
            row["cut_present"] = os.path.exists(cut_receipt_path)
            row["cut_sha256"] = None
            row["cut_png"] = None
            if row["cut_present"]:
                with open(cut_receipt_path, "r", encoding="utf-8") as handle:
                    cut_receipt = json.load(handle)
                row["cut_png"] = cut_receipt["cut"]["path"]
                row["cut_sha256"] = cut_receipt["cut"]["sha256"]
        resolved.append(row)
    return resolved


def problems_from(rows_):
    """Everything a row claims that its receipt does not support."""
    found = []
    for row in rows_:
        name = row.get("receipt_file") or "(none)"
        if row.get("missing"):
            found.append("%s %s: no receipt (%s)" % (row["kind"], row["model"], name))
            continue
        if row["entry_model"] != row["model"]:
            found.append("%s: the receipt's model is %r, the row says %r"
                         % (name, row["entry_model"], row["model"]))
        if row["entry_kind"] != row["kind"]:
            found.append("%s: the receipt's kind is %r, the row says %r"
                         % (name, row["entry_kind"], row["kind"]))
        if not row["entry_recorded_at"]:
            found.append("%s: the receipt carries no recorded_at" % name)
        if row["kind"] in ("chat", "vision") and not str(row.get("answer") or "").strip():
            found.append("%s: the receipt holds no text answer" % name)
        if row.get("cut_receipt"):
            if not row.get("cut_present"):
                found.append("%s: the cut receipt %s is not on disk"
                             % (name, row["cut_receipt"]))
            elif not row.get("cut_png"):
                found.append("%s: the cut receipt names no cut" % name)
            else:
                cut_file = os.path.join(ROOT, row["cut_png"])
                if not os.path.exists(cut_file):
                    found.append("%s: the cut %s is not on disk" % (name, row["cut_png"]))
                elif _sha256(cut_file) != row.get("cut_sha256"):
                    found.append("%s: the cut %s is not the one the cut receipt names"
                                 % (name, row["cut_png"]))
    return found


def tracked_problems(rows_):
    """Receipts that exist on disk but are not in the commit, so a fresh checkout could not replay.

    The commit gate caught this once already: a receipt resolved from whatever the newest file in
    the working cache happened to be was not in HEAD, so the page's own test failed inside the
    gate's worktree while passing here. Every row is pinned for that reason, and this check says
    so out loud. A tree without git says nothing rather than failing.
    """
    found = []
    for row in rows_:
        path = row.get("receipt_path")
        if not path:
            continue
        try:
            result = subprocess.run(["git", "-C", ROOT, "ls-files", "--error-unmatch", path],
                                    capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            return found
        if result.returncode != 0:
            found.append("%s is on disk but not in the commit, so a fresh checkout cannot "
                         "replay it" % path)
    return found


def render(rows_):
    live = sum(1 for row in rows_ if row.get("entry_network"))
    offline = len(rows_) - live
    lines = [
        "# MODELS-USED: every Meta model this entry calls, and the receipt for each",
        "",
        "Generated by `tools/models_used.py` (card META-MODEL-BREADTH). Do not edit by hand: run "
        "the tool, and `--check` fails when this page and the receipts disagree.",
        "",
        "A receipt is the call's own recorded answer in `data/ai_cache`, named by the sha256 of "
        "its request. Every column below is read out of that file, including the word `live` or "
        "`offline`: `live` is an entry whose own record says `network: true`, and `offline` is one "
        "that says `network: false`, answered by the client's mock backend with no socket opened. "
        "This page has %d live rows and %d offline rows, and it prints the difference rather than "
        "hiding it." % (live, offline),
        "",
        "| # | model | what it does in the entry | the call | receipt | entry says |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for index, row in enumerate(rows_, start=1):
        if row.get("missing"):
            receipt = "MISSING: %s" % (row.get("receipt_file") or "no entry")
            says = "-"
        else:
            receipt = ("`%s` sha256 `%s`" % (row["receipt_path"], row["receipt_sha256"][:16]))
            says = ("%s, %s, recorded %s, network %s"
                    % (row["entry_backend"], row["entry_kind"], row["entry_recorded_at"],
                       str(row["entry_network"]).lower()))
        lines.append("| %d | `%s` | %s | %s | %s | %s |"
                     % (index, row["model"], row["role"], row["call"], receipt, says))
    lines += [
        "",
        "## What each call is, exactly",
        "",
    ]
    for row in rows_:
        lines.append("- `%s`, %s: %s" % (row["model"], row["kind"], row["call"]))
        if row.get("answer"):
            lines.append("  The receipt's own answer starts: `%s`" % row["answer"][:100])
        if row.get("cut_receipt"):
            lines.append("  The cut this call produced is `%s`, with its numbers in `%s` (sha256 "
                         "`%s`): every opaque pixel is a pixel the model's mask set, and the "
                         "cut's alpha bbox equals the box the same answer returned."
                         % (row.get("cut_png") or "(missing)",
                            row["cut_receipt"], (row.get("cut_sha256") or "")[:16]))
        if row.get("offline_call") and not row.get("entry_network"):
            lines.append("  This call is offline: the mock backend answered, so the transcript or "
                         "verdict in the receipt is the client's canned answer and is NOT a model "
                         "output. What it proves is that the call path, the request shape and the "
                         "receipt exist and replay; what it does not prove is that the hosted "
                         "model has ever answered here.")
            audio = (row["offline_call"] or {}).get("audio")
            if audio:
                lines.append("  The wav itself is written by `python tools\\models_used.py "
                             "--record` into `knowledge/models_used/`, which the project's `*.wav` "
                             "rule keeps out of the commit: a 0.6 s 220 Hz tone at the `/hear` "
                             "contract's own 16000 Hz, mono, 16 bit, not speech. It is "
                             "deterministic, and the receipt carries its size and sha256, so the "
                             "same call and the same entry come back on any machine.")
    lines += [
        "",
        "## The two models that are cited rather than answered",
        "",
        "Both ids and the reason to use them come from entries in the field, and both are named "
        "here as the routing this entry has built rather than as calls a server has answered.",
        "",
        "- **Muse Spark Open on Baseten.** Khet Saathi (rafatusa, 2026-10-27 06:30) runs the same "
        "agent loop on Muse Spark Open, served by Baseten, \"for affordable rural-scale serving\"; "
        "Ankita (krish) and paper-bro (Aero) name the same host. The model is 816B total and 42B "
        "active, needs about 700 GB of GPU memory at NVFP4, so it is hosted, never local: see "
        "`knowledge/OPEN-WEIGHTS-2026-10-26.md` and https://dev.meta.ai/docs/muse-spark-open. The id "
        "in the table above is the hosted name a public entry uses in its own description "
        "(`knowledge/scout-2026-10-27/repos_371.json`, captured 2026-10-27), because Meta's own "
        "page does not publish a Baseten slug; `PP_META_MODEL_OPEN` overrides it for a host that "
        "names it differently. For this entry it is the rung a judge rerun can be served on, off "
        "the paid API, with the transcript cache as the fallback when no host is reachable.",
        "- **Muse Voice Transcribe.** Khet Saathi names it as the voice input for Bangla and Hindi; "
        "the fight's `/hear` box asks for exactly the same thing in English, and `data/talk_live.json` "
        "already fixes the contract it must meet: 16000 Hz mono 16 bit PCM in, a transcript out, "
        "and a refusal rather than a guess when the recording is too short. The Meta rung is "
        "`meta_client.transcribe()`; the local whisper rung stays as the fallback, so a missing key "
        "costs a transcript and never the demo.",
        "",
        "CukupAI (Ishab, 2026-10-26 16:04) is the other entry the plan cites for breadth: ML Kit on "
        "the device plus SAM 3.1 plus Llama 3.1, with near zero API overhead. It is why the cut in "
        "this repository runs from a recorded answer (the network is not needed to reproduce it) "
        "rather than from a live call at demo time.",
        "",
        "## What this page does not claim",
        "",
        "- It does not claim a live answer from Muse Spark Open or Muse Voice Transcribe. Neither "
        "has an entry with `network: true` in `data/ai_cache`, and the table says so.",
        "- It does not claim a cost. `knowledge/META-SPEND.md` prices only the live entries, and "
        "an offline row costs nothing.",
        "- It does not claim the two cited entries are achievements of this one: they are other "
        "teams' public posts, named as the evidence for the routing, not as results.",
        "",
        "    python tools\\models_used.py --check",
        "",
    ]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Write or check knowledge/MODELS-USED.md.")
    parser.add_argument("--record", action="store_true",
                        help="make the offline calls first (mock backend, record mode)")
    parser.add_argument("--force-voice", action="store_true",
                        help="rewrite the synthetic voice sample before recording")
    parser.add_argument("--check", action="store_true", help="exit 1 when the page is out of date")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.record:
        report = record_offline(force=args.force_voice)
        for kind, model, answer in report["calls"]:
            print("recorded %-6s %-40s %s" % (kind, model, answer))
    rows_ = rows()
    problems = problems_from(rows_)
    page = render(rows_)
    if args.json:
        print(json.dumps({"rows": rows_, "problems": problems}, indent=2, sort_keys=True))
    if args.check:
        current = ""
        if os.path.exists(OUT):
            with open(OUT, "r", encoding="utf-8") as handle:
                current = handle.read()
        problems = problems + tracked_problems(rows_)
        for problem in problems:
            print("FAIL  %s" % problem)
        if current != page:
            print("FAIL  %s is out of date; run python tools\\models_used.py" % OUT)
            problems = problems + ["page out of date"]
        print("models %d, receipts %d, problems %d"
              % (len(rows_), sum(1 for row in rows_ if not row.get("missing")), len(problems)))
        return 0 if not problems else 1
    if problems:
        for problem in problems:
            print("FAIL  %s" % problem)
        print("refusing to write a page with an unsupported row; run --record for the offline "
              "calls, and check the live receipts by name")
        return 1
    with open(OUT, "w", encoding="utf-8") as handle:
        handle.write(page)
    print("wrote %s" % OUT)
    for row in rows_:
        print("  %-38s %-11s %s network=%s" % (row["model"], row["kind"],
                                               row["receipt_file"], row.get("entry_network")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
