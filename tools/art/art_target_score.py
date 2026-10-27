#!/usr/bin/env python3
"""Score the three art-target frames with the project's eye critic (Gemini).

Card PP-ART-TARGET step 4. The key is copied from the user environment into this process and is never
printed, never written to a file, and never included in an error string: eye_critic.redact() handles the
last of those.

The frames are sent at 4x nearest neighbour. At 1x a 256x240 frame is too small for a vision model to judge
faces or line weight, and at 4x the palette is unchanged because the upscale is nearest neighbour, so the
measured facts the critic is given (distinct colours, off palette count) are still the frame's own.
"""
import os
import sys

ROOT = r"<repo>"
sys.path.insert(0, os.path.join(ROOT, "tools"))

import eye_critic as eye


def bootstrap_key():
    if eye.key_present():
        print("key: PRESENT in this process environment", flush=True)
        return True
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as handle:
            value, _kind = winreg.QueryValueEx(handle, "GEMINI_API_KEY")
    except Exception:  # noqa: BLE001
        print("key: ABSENT", flush=True)
        return False
    if not value:
        print("key: ABSENT (empty)", flush=True)
        return False
    os.environ["GEMINI_API_KEY"] = value
    print("key: PRESENT (read from user environment, never printed)", flush=True)
    return True


if not bootstrap_key():
    raise SystemExit(2)

frames = [os.path.join(ROOT, "output", "art_target", "look", "frame_%s_4x.png" % key)
          for key in ("A", "B", "C")]
for path in frames:
    if not os.path.exists(path):
        raise SystemExit("missing frame: %s" % path)

argv = ["--json"] + frames + sys.argv[1:]
raise SystemExit(eye.main(argv))
