"""build_pp01_v10.py: PP-01 "Title Theme" v10, card t_65512e1c (M3 BAROQUE-CUES).

A two-part invention on the game's own leitmotif with a triangle continuo. The composer is
tools/counterpoint/m3_cues.py (it reads the leitmotif out of pp_01_title_v7.mid, generates
the countersubjects and the continuo, repairs against the checker, polishes the soft
findings and writes the MIDI), and the pipeline around it is
tools/counterpoint/m3_build.py (render through tools/render_chip.py, master to -14 LUFS,
measure the delivered file, run the cue gate and the hook meter).

Nothing earlier is touched: this script writes only into its own folder, and the build tool
refuses a folder that already holds a .wav or .ogg.

Usage: build_pp01_v10.py
"""

from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PYTHON = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
BUILD = os.path.join(ROOT, "tools", "counterpoint", "m3_build.py")


def main():
    command = [PYTHON, BUILD, "--piece", "title",
               "--asset-dir", os.path.join("assets", "audio", os.path.basename(HERE)),
               "--slug", os.path.basename(HERE), "--loop-bars", "32"]
    print(" ".join(command))
    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())
