#!/usr/bin/env python3
"""kaggle_r7_gpu.py: drive the R7 GPU lane from this machine, and say plainly when it cannot.

The lane is three steps and this tool is all three in one command:

  1. PUSH. Upload tools/kaggle/r7_concepts/ as a PRIVATE Kaggle kernel with a GPU and internet, and wait for the
     run. The kernel generates the four concept frames with an image model, then optionally runs SAM over them.
     Nothing here reads a token: the Kaggle client resolves KAGGLE_API_TOKEN itself.
  2. FETCH. Download the run's output into output/kaggle_r7/concepts_gpu/, next to the run's r7_manifest.json,
     which carries the model, the LoRA, the seed, the prompt and the sha256 of every frame.
  3. MEASURE. Run tools/kaggle_r7.py --concepts on that folder, so the segment, quantise, measure and score
     steps happen on this machine with the rules this repository owns.

Why the three steps are separate files in the report: the frames are the model's, the measurement is ours, and a
reader has to be able to see which half produced which number.

Usage
    python tools\\\\kaggle_r7_gpu.py                     push, wait, fetch, measure
    python tools\\\\kaggle_r7_gpu.py --fetch-only        just pull the last run's output
    python tools\\\\kaggle_r7_gpu.py --no-measure        push and fetch, leave the local tool to me
    python tools\\\\kaggle_r7_gpu.py --slug nayilarana/primordial-paradox-r7-gpu-concepts

Exit codes: 0 the whole lane ran, 2 bad argument, 3 the kaggle client or its credential is missing on this
machine, 4 the kernel run did not complete, 5 the local measurement failed.

A note on the credential, because it is the thing that used to block this lane: the client is not part of this
repository's interpreter. Install it in a virtual environment you own and run this file with THAT interpreter, or
point --python at an interpreter that has both the client and this repository's requirements.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KERNEL_DIR = os.path.join(ROOT, "tools", "kaggle", "r7_concepts")
OUTPUT = os.path.join(ROOT, "output", "kaggle_r7")
CONCEPTS_GPU = os.path.join(OUTPUT, "concepts_gpu")
DEFAULT_SLUG = "nayilarana/primordial-paradox-r7-gpu-concepts"
TOOL = os.path.join(ROOT, "tools", "kaggle_r7.py")


def client():
    """The Kaggle client, or a one line reason why this interpreter has none."""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except Exception as error:
        return None, ("the kaggle package is not installed in this interpreter (%s); credential env var %s"
                      % (type(error).__name__,
                         "KAGGLE_API_TOKEN" if os.environ.get("KAGGLE_API_TOKEN") else "absent"))
    if not (os.environ.get("KAGGLE_API_TOKEN") or os.environ.get("KAGGLE_KEY")
            or os.path.exists(os.path.join(os.path.expanduser("~"), ".kaggle", "kaggle.json"))):
        return None, "no Kaggle credential in the environment and no ~/.kaggle/kaggle.json"
    api = KaggleApi()
    try:
        api.authenticate()
    except Exception as error:
        return None, "the Kaggle client could not authenticate (%s)" % type(error).__name__
    return api, None


def push(api, slug: str, timeout: int) -> int:
    print("push: uploading %s as %s" % (KERNEL_DIR, slug))
    response = api.kernels_push(KERNEL_DIR, timeout=timeout)
    version = getattr(response, "version_number", "?")
    print("push: version %s accepted, waiting for the run" % version)
    started = time.time()
    status = None
    while time.time() - started < timeout:
        state = api.kernels_status(slug)
        status = str(getattr(state, "status", "?"))
        if "COMPLETE" in status:
            print("push: run complete after %ds" % (time.time() - started))
            return 0
        if "ERROR" in status or "CANCEL" in status:
            print("push: run ended %s: %s" % (status, (getattr(state, "failureMessage", "") or "")[:400]))
            return 4
        time.sleep(20)
    print("push: still %s after %ds, giving up on the wait (the run itself may still finish)" % (status, timeout))
    return 4


def fetch(api, slug: str) -> int:
    os.makedirs(CONCEPTS_GPU, exist_ok=True)
    api.kernels_output(slug, path=CONCEPTS_GPU, force=True, quiet=True)
    frames = sorted(name for name in os.listdir(CONCEPTS_GPU) if name.endswith(".png"))
    manifest = os.path.join(CONCEPTS_GPU, "r7_manifest.json")
    if not os.path.exists(manifest):
        print("fetch: no r7_manifest.json in the run output, so nothing here is attributable")
        return 4
    with open(manifest, encoding="utf-8") as handle:
        data = json.load(handle)
    print("fetch: %d frame(s) and a manifest for %d concept(s) in %s"
          % (len(frames), len(data.get("concepts", [])), CONCEPTS_GPU))
    sam = data.get("sam3") or {}
    print("fetch: sam3 attempted=%s reason=%s" % (sam.get("attempted"), sam.get("reason_if_skipped")))
    return 0 if frames else 4


def measure(python: str) -> int:
    command = [python, TOOL, "--concepts", CONCEPTS_GPU]
    print("measure: %s" % " ".join(command))
    return subprocess.call(command, cwd=ROOT)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Push, fetch and measure the R7 GPU concept lane.")
    parser.add_argument("--slug", default=DEFAULT_SLUG, help="kernel ref, owner/slug")
    parser.add_argument("--timeout", type=int, default=3600, help="seconds to wait for the run")
    parser.add_argument("--fetch-only", action="store_true", help="skip the push, pull the last output")
    parser.add_argument("--no-measure", action="store_true", help="stop after the fetch")
    parser.add_argument("--python", default=sys.executable, help="interpreter for the local measurement step")
    args = parser.parse_args(argv)

    if not os.path.isdir(KERNEL_DIR) and not args.fetch_only:
        print("kaggle_r7_gpu: the kernel folder is missing: %s" % KERNEL_DIR)
        return 2

    api, reason = client()
    if api is None:
        print("kaggle_r7_gpu: the GPU lane cannot run here: %s" % reason)
        return 3

    if not args.fetch_only:
        code = push(api, args.slug, args.timeout)
        if code:
            return code
    code = fetch(api, args.slug)
    if code:
        return code
    if args.no_measure:
        return 0
    return 0 if measure(args.python) == 0 else 5


if __name__ == "__main__":
    sys.exit(main())
