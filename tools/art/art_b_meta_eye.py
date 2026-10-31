"""art_b_meta_eye.py: score art_b frames with the eye critic, on the Meta backend, and print only the numbers.

Card t_760a7325 (the old man on the high street in style B). The card's check is "the Meta eye critic (card
EYE-CRITIC-META's tool) scores the after frames higher than the before frames on readability", so the run has to be
the project's own critic, on the project's own rubric, with a score per frame that a reader can compare.

HOW IT RUNS
    python tools\\art\\art_b_meta_eye.py output\\art_b\\ART-B-CHARACTERS\\ouranos_before_frame_256x240.png ...

  * It imports tools\\eye_critic.py and calls review_image() on each file. The rubric, the measured facts, the ledger
    row and the review markdown are all that tool's own, unchanged.
  * PP_AI_BACKEND=meta makes eye_critic hand its generateContent payload to tools\\meta_client.py, which is the Meta
    route card EYE-CRITIC-META built. The model is named by PP_EYE_MODEL if set, else muse-spark-1.3.
  * MODEL_API_KEY (or META_API_KEY) is read at call time by meta_client. A worker shell is often spawned before
    `setx` reaches it, so when neither is in this process's environment the Windows user environment is read
    (HKCU\\Environment), which is the environment and not a key file. The value goes into os.environ and nowhere
    else: it is never printed, never written, never in an exception, and this script prints only file, model and the
    three scores.

WHY IT REFUSES TO GUESS A SCORE
  A frame the critic could not see is not a low score. Every review is checked for the model's own words about the
  picture before its numbers are reported; a review whose text says it cannot see the frame is printed as UNSEEN and
  exits 2, because a score from a call that carried no pixels is a number about nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import eye_critic  # noqa: E402  the rubric, the ledger and the parsing, all the project's own

META_KEY_ENVS = ("MODEL_API_KEY", "META_API_KEY")
UNSEEN_MARKERS = ("no image pixels", "cannot see the frame", "no pixels were provided", "was not provided",
                  "cannot describe what is shown", "no frame is visible", "missing submission",
                  "i cannot describe what is shown")


def load_meta_key_from_user_environment():
    """Put the Windows user environment's META_API_KEY (or MODEL_API_KEY) into os.environ, never printed."""
    if any(os.environ.get(name, "").strip() for name in META_KEY_ENVS):
        return "environment"
    try:
        import winreg
    except ImportError:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as handle:
            index = 0
            values = {}
            while True:
                try:
                    name, value, kind = winreg.EnumValue(handle, index)
                except OSError:
                    break
                index += 1
                values[name.upper()] = value
    except OSError:
        return None
    for name in META_KEY_ENVS:
        value = str(values.get(name, "") or "").strip()
        if value:
            os.environ[name] = value
            return "user environment"
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score art_b frames with the eye critic on the Meta backend.")
    parser.add_argument("files", nargs="+", help="PNG frames to review")
    parser.add_argument("--model", default=os.environ.get("PP_EYE_MODEL") or "muse-spark-1.3")
    parser.add_argument("--json", action="store_true", help="print the result as one JSON object")
    args = parser.parse_args(argv)

    os.environ["PP_AI_BACKEND"] = "meta"
    source = load_meta_key_from_user_environment()
    if source is None:
        print("no Meta key in the environment or in HKCU\\Environment: no request was made", file=sys.stderr)
        return 3

    rows = []
    unseen = []
    for path in args.files:
        result = eye_critic.review_image(path, model=args.model)
        review = result.get("review_path") or result.get("review")
        text = ""
        if review and os.path.exists(review):
            with open(review, "r", encoding="utf-8") as handle:
                text = handle.read()
        scores = result.get("scores") or {}
        blind = any(marker in text.lower() for marker in UNSEEN_MARKERS)
        row = {"file": os.path.basename(path), "model": result.get("plan", {}).get("model", args.model),
               "scores": scores, "review": review, "seen": not blind}
        rows.append(row)
        if blind:
            unseen.append(row["file"])
        if not args.json:
            print("%-36s %-15s nes %s readability %s charm %s  %s"
                  % (row["file"], row["model"], scores.get("nes"), scores.get("readability"),
                     scores.get("charm"), "UNSEEN" if blind else "seen"))
            print("    review: %s" % review)
    if args.json:
        print(json.dumps({"key_source": source, "rows": rows}, indent=1))
    if unseen:
        print("UNSEEN: %s" % ", ".join(unseen), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
