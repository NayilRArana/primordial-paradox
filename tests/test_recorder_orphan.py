"""Card RECORDER-ORPHAN (2026-11-02): the play_demo watchdog must stop the ffmpeg recorder too.

The watchdog in tools/capture_title.py killed the game process and exited the harness without touching the
recorder, so when the replay overran its bound, ffmpeg kept recording the desktop for 22 minutes after the
harness was gone. These tests fire the watchdog against two dummy long-sleeping processes (a fake game and a
fake recorder; no game and no ffmpeg) and hold down the two claims the fix makes: the watchdog kills both
children and exits with its own code 3, and a recorder that already exited is ignored.

Run: python -m pytest tests/test_recorder_orphan.py -q
"""

from __future__ import annotations

import ctypes
import json
import os
import subprocess
import sys

import pytest

# Card TEST-CLASSIFY-33: every test here loads tools/capture_title.py, which binds ctypes.windll.user32 at
# module level, so on a Linux host the import raises AttributeError before a line of any test runs. The
# marker is a skip there, never a pass.
pytestmark = pytest.mark.windows_only

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")

WATCHDOG_S = 0.5
HARNESS_TIMEOUT_S = 30.0
STILL_ACTIVE = 259
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def pid_alive(pid):
    """True while a Windows process id is still running."""
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
    if not handle:
        return False
    try:
        code = ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return True
        return code.value == STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


def run_harness(code, tmp_path):
    """Run the watchdog harness in its own process and hand back its result plus the pid file path.

    stdin is DEVNULL, never inherited: a parent with no valid standard input handle makes the spawn
    itself raise OSError [WinError 6] under pytest's capture (card t_668201ec, same rule as
    conftest._is_git_checkout).
    """
    pidfile = str(tmp_path / "pids.json")
    result = subprocess.run([sys.executable, "-c", code, TOOLS, pidfile],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=HARNESS_TIMEOUT_S)
    return result, pidfile


# The harness is the whole point of a separate process: start_watchdog ends with os._exit(3), which would
# kill the test runner itself if it fired in-process. Each harness starts a fake game and a fake recorder
# (both "import time; time.sleep(60)"), writes their pids to a file the test reads, then fires the watchdog
# with a half second bound. The try/finally is a backstop that reaps the children on the unchanged-code path
# (where start_watchdog rejects the recorder argument and raises) so a red run leaves no sleeping orphans.
HARNESS = r'''
import json
import subprocess
import sys
import time

sys.path.insert(0, sys.argv[1])
import capture_title as cap

game = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
recorder = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
with open(sys.argv[2], "w", encoding="utf-8") as fh:
    json.dump({"game": game.pid, "recorder": recorder.pid}, fh)

holder = [None]
try:
    cap.start_watchdog(game, 0.5, recorder=holder)
    holder[0] = recorder
    time.sleep(10)
finally:
    for proc in (game, recorder):
        if proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
'''

# A recorder that has already ended: kill_tree must skip it without a traceback, and the watchdog must
# still exit 3 after stopping the game. The fake only needs poll(), because kill_tree returns before it
# ever asks for terminate(), kill() or wait().
GONE_HARNESS = r'''
import json
import subprocess
import sys
import time

sys.path.insert(0, sys.argv[1])
import capture_title as cap

class Gone:
    def poll(self):
        return 0

game = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
with open(sys.argv[2], "w", encoding="utf-8") as fh:
    json.dump({"game": game.pid}, fh)

holder = [Gone()]
try:
    cap.start_watchdog(game, 0.5, recorder=holder)
    time.sleep(10)
finally:
    if game.poll() is None:
        try:
            game.terminate()
            game.wait(timeout=3)
        except Exception:
            try:
                game.kill()
            except Exception:
                pass
'''


def test_the_watchdog_stops_both_the_game_and_the_recorder(tmp_path):
    result, pidfile = run_harness(HARNESS, tmp_path)
    assert result.returncode == 3, (result.returncode, result.stdout, result.stderr)
    pids = json.load(open(pidfile, encoding="utf-8"))
    assert not pid_alive(pids["game"]), "the fake game survived the watchdog"
    assert not pid_alive(pids["recorder"]), "the fake recorder survived the watchdog"


def test_a_recorder_that_already_exited_is_ignored(tmp_path):
    result, pidfile = run_harness(GONE_HARNESS, tmp_path)
    assert result.returncode == 3, (result.returncode, result.stdout, result.stderr)
    pids = json.load(open(pidfile, encoding="utf-8"))
    assert not pid_alive(pids["game"]), "the fake game survived the watchdog"
