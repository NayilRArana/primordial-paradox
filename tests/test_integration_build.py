"""The build step must be bounded, must compile rather than launch, and must not pass with nothing built.

Three rewrites are pinned here, all from card t_9d9b5b1d (2026-10-25):

1. The step asks run.ps1 for -Compile. Igor's `-- Windows Run` waits for the launched game to exit, so
   the step used to sit on the open window until the gate's 900 s timeout.
2. The word "launched" is gone from the pass line, because nothing is launched any more.
3. Exit 0 from the script is a claim, not the build: the .win has to be newer than this run and the Igor
   log has to carry its completion and GMA statistics lines, or the step FAILS.

And it must never sit until the gate's own timeout: the tool has its own watchdog (GATE_BUILD_TIMEOUT_S)
and fails itself when it trips.

No powershell and no Igor run here: run_command is stubbed, so the branch under test is the one that reads
its result.
"""

from __future__ import annotations

import io
import os
from contextlib import redirect_stdout

import integration_build


def _run_with(monkeypatch, returncode, artefact_problem=None) -> tuple[int, str]:
    monkeypatch.setattr(integration_build, "run_command",
                        lambda *a, **k: (returncode, "run.ps1 said something"))
    monkeypatch.setattr(integration_build, "compiled_artefact_problem",
                        lambda started_at: artefact_problem)
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = integration_build.main()
    return code, buf.getvalue()


def test_the_step_compiles_and_does_not_launch(monkeypatch):
    """-Compile is the fix. Without it Igor waits on the game window and the gate step blocks."""
    command = integration_build.gate_command()
    assert "-Compile" in command
    assert "-SkipChecks" in command
    assert command[-1] == "-Compile", "the switch has to survive to the end of the argument list"


def test_successful_build_is_a_pass_that_says_compiled(monkeypatch):
    code, out = _run_with(monkeypatch, 0)
    assert code == 0
    assert "BUILD PASS" in out
    assert "compiled" in out
    assert "launched" not in out, "the step no longer launches, so the pass line must not claim it"


def test_an_exit_zero_with_no_artefact_is_a_failure(monkeypatch):
    """The rule the card owns: never report PASS when nothing was built."""
    code, out = _run_with(monkeypatch, 0, artefact_problem="Igor exited 0 but nothing was compiled")
    assert code == 1
    assert "BUILD FAIL" in out
    assert "BUILD PASS" not in out
    assert "nothing was compiled" in out


def test_a_watchdog_trip_is_a_failure_not_a_wait(monkeypatch):
    code, out = _run_with(monkeypatch, None)
    assert code == 1
    assert "BUILD FAIL" in out
    assert "did not finish inside" in out
    assert "killed" in out


def test_missing_game_maker_is_unmeasured_not_a_pass(monkeypatch):
    # run.ps1 exit 2 means no runtime, no Igor, or no licence folder. That is unmeasured.
    code, out = _run_with(monkeypatch, 2)
    assert code == 3
    assert "BUILD UNMEASURED" in out
    assert "NOT a pass" in out
    assert "BUILD PASS" not in out


def test_other_failure_is_a_failure(monkeypatch):
    code, out = _run_with(monkeypatch, 1)
    assert code == 1
    assert "BUILD FAIL" in out
    assert "BUILD UNMEASURED" not in out


def test_missing_run_script_fails_rather_than_skips(monkeypatch, tmp_path):
    # A missing script is a broken install, not an absent GameMaker: it must not read as a skip.
    monkeypatch.setattr(integration_build, "RUN_PS1", str(tmp_path / "run.ps1"))
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = integration_build.main()
    assert code == 1
    assert "BUILD FAIL" in buf.getvalue()


def test_the_artefact_check_reads_a_real_compile(monkeypatch, tmp_path):
    """The evidence branch, exercised on real files instead of a stub."""
    exe = tmp_path / "PrimordialParadox.win"
    log = tmp_path / "last-igor.log"
    monkeypatch.setattr(integration_build, "OUTPUT_EXE", str(exe))
    monkeypatch.setattr(integration_build, "IGOR_LOG", str(log))
    started_at = 1_000_000.0

    assert "does not exist" in integration_build.compiled_artefact_problem(started_at)

    exe.write_bytes(b"runner")
    os.utime(exe, (started_at - 600, started_at - 600))
    assert "was not rewritten" in integration_build.compiled_artefact_problem(started_at)

    os.utime(exe, (started_at + 1, started_at + 1))
    assert "could not be read" in integration_build.compiled_artefact_problem(started_at)

    log.write_text("Stats : GMA : sp=0,da=275\n", encoding="utf-8")
    assert "no 'Igor complete.'" in integration_build.compiled_artefact_problem(started_at)

    log.write_text("Igor complete.\n", encoding="utf-8")
    assert "no 'Stats : GMA'" in integration_build.compiled_artefact_problem(started_at)

    log.write_text("Stats : GMA : sp=0,da=275\nIgor complete.\n", encoding="utf-8")
    assert integration_build.compiled_artefact_problem(started_at) is None
