"""Integration step for the repo gates: compile the GameMaker project, and name what is unmeasured.

The unit gate is pytest over tools\\check_data.py, tools\\check_project.py and tools\\check_cleanroom.py, which needs no
GameMaker. This step is the part a unit test cannot reach: Igor compiling the .yyp. It runs tools\\run.ps1 with
-SkipChecks -Compile, that is: sync nothing, do not run the Python gates again, and COMPILE ONLY.

Compile only, and not Run, is the whole point of this rewrite (card t_9d9b5b1d, 2026-10-25). Igor's
`-- Windows Run` does NOT return while the launched game is still open: it waits for the game process to exit.
Measured three times on 2026-10-25 against runtime-2026.0.0.23, a Run built the project, launched the game, and
then sat until something posted WM_CLOSE to the window titled `Primordial Paradox` (process Runner.exe). A gate
step that runs on every push cannot wait for a window nobody in CI will close, so this step no longer launches the
game at all. The launch is still measured, by a human: `tools\\run.ps1` with no flags builds and runs.

Outcomes. Exit 3 is declared as this step's unmeasured result in suite_config.json, where the gate prints it as
"UNMEASURED (GameMaker not installed)" and never as PASS:

    exit 0 and "BUILD PASS"        Igor compiled (Igor complete, GMA stats and a fresh .win on disk)
    exit 3 and "BUILD UNMEASURED"  GameMaker, Igor or the licence folder is absent (run.ps1 exit 2)
    exit 1                        anything else: a compile error, a watchdog trip, or an empty exit 0

Two things this step refuses to do. It never reports PASS when nothing was built: exit 0 from the script is not
enough, the .win has to be newer than this run and the Igor log has to carry "Igor complete." and its
`Stats : GMA` line, which is what a real compile writes. And it never sits until the gate's own timeout: the
compile gets GATE_BUILD_TIMEOUT_S, after which the powershell/Igor process tree is killed and the step fails, so
the step is bounded no matter what Igor does.

Usage:
    python tools/integration_build.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_PS1 = os.path.join(ROOT, "tools", "run.ps1")
OUTPUT_EXE = os.path.join(ROOT, "output", "PrimordialParadox", "PrimordialParadox.win")
IGOR_LOG = os.path.join(ROOT, "build", "last-igor.log")

# A measured compile of this project takes a couple of minutes on a cold build directory. The cap is
# deliberately far above that and far below the gate's own timeout_s, so a hung Igor fails THIS step with a
# readable sentence instead of looking like the whole gate hanging.
GATE_BUILD_TIMEOUT_S = 480
KILL_GRACE_S = 30


def gate_command() -> list[str]:
    """The one command this step runs. -Compile is required: see the module docstring."""
    return [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", RUN_PS1, "-SkipChecks", "-Compile",
    ]


def _kill_tree(pid: int) -> None:
    """Kill powershell AND the Igor process it started. proc.kill() alone would orphan Igor.

    A failed kill is printed, never swallowed: this is the branch that runs when a build has already
    misbehaved, and a silent failure there would leave Igor running with nothing in the log saying so.
    """
    try:
        result = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                                stdin=subprocess.DEVNULL, capture_output=True, text=True)
    except OSError as exc:
        print("watchdog: taskkill could not run (%s), so only the direct process was killed" % exc)
        return
    if result.returncode != 0:
        print("watchdog: taskkill returned %d for pid %d: %s"
              % (result.returncode, pid, (result.stdout or result.stderr or "").strip()))


def run_command(command: list[str], timeout_s: int = GATE_BUILD_TIMEOUT_S) -> tuple[int | None, str]:
    """Run the build. Returns (exit code, output); exit code is None when the watchdog fired."""
    # stdin=DEVNULL on purpose: with no stdin given, CPython hands the child this process's own
    # STD_INPUT_HANDLE and duplicates it, which raises OSError [WinError 6] if that handle is already
    # invalid. The build reads no stdin, so DEVNULL costs nothing.
    process = subprocess.Popen(command, cwd=ROOT, text=True, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        output = process.communicate(timeout=timeout_s)[0]
        return process.returncode, output or ""
    except subprocess.TimeoutExpired:
        _kill_tree(process.pid)
        try:
            output = process.communicate(timeout=KILL_GRACE_S)[0] or ""
        except subprocess.TimeoutExpired:
            process.kill()
            output = ""
        return None, output


def _short(path: str) -> str:
    """Repo-relative when it can be, otherwise as given (a test may point at another drive)."""
    try:
        return os.path.relpath(path, ROOT)
    except ValueError:
        return path


def compiled_artefact_problem(started_at: float) -> str | None:
    """None when a real compile happened, otherwise one sentence naming what is missing.

    Exit 0 from run.ps1 is a claim, not the build. The evidence a compile leaves is the runner's output file
    rewritten by this run and an Igor log carrying its completion line and its GMA statistics line (the
    `Stats : GMA : ... da=N` line, measured 2026-10-25 by card t_4848159e).
    """
    rel = _short(OUTPUT_EXE)
    if not os.path.isfile(OUTPUT_EXE):
        return "run.ps1 exited 0 but %s does not exist, so nothing was compiled" % rel
    if os.path.getmtime(OUTPUT_EXE) < started_at - 5:
        return "run.ps1 exited 0 but %s was not rewritten by this run, so nothing was compiled" % rel

    try:
        with open(IGOR_LOG, encoding="utf-8", errors="replace") as fh:
            log = fh.read()
    except OSError as exc:
        return "run.ps1 exited 0 but %s could not be read (%s), so the compile is not evidenced" % (
            _short(IGOR_LOG), exc)

    if "Igor complete." not in log:
        return ("run.ps1 exited 0 but the Igor log has no 'Igor complete.' line, "
                "so Igor did not finish a compile")
    if "Stats : GMA" not in log:
        return "run.ps1 exited 0 but the Igor log has no 'Stats : GMA' line, so no project was compiled"
    return None


def main() -> int:
    """Run the compile, print its output, and return the step's exit code (0, 1 or 3)."""
    if not os.path.isfile(RUN_PS1):
        print("BUILD FAIL: tools/run.ps1 is missing")
        return 1

    started_at = time.time()
    returncode, output = run_command(gate_command())
    for line in output.splitlines():
        print(line)

    if returncode is None:
        print("BUILD FAIL: the compile did not finish inside %d s, so powershell and Igor were killed. "
              "A compile that hangs is a broken build step, not a slow one." % GATE_BUILD_TIMEOUT_S)
        return 1
    if returncode == 0:
        problem = compiled_artefact_problem(started_at)
        if problem is not None:
            print("BUILD FAIL: %s" % problem)
            return 1
        print("BUILD PASS: Igor compiled the project (compile mode, the game was not run)")
        return 0
    if returncode == 2:
        print("BUILD UNMEASURED: GameMaker (or its licence folder) is not installed on this machine, so no "
              "build was measured. This is NOT a pass, it is an unmeasured integration step.")
        return 3

    print("BUILD FAIL: run.ps1 exited %d" % returncode)
    return 1


if __name__ == "__main__":
    sys.exit(main())
