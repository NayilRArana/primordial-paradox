"""Pins for card t_5d1a6ec4: a window over the game mid recording is a polluted take, never an art finding.

What these tests hold down, and why each one earns its place:
  1. a take with two frames of a foreign window is reported POLLUTED and named, and the report never sends the
     art lane to look at it;
  2. a clean take still passes its six checks: a palette verdict that reds a good recording would cost the
     submission more than the defect it fixes;
  3. the pollution watch names the process that owned the rectangle, marks the take polluted on one sample and
     asks the run to stop after two consecutive ones;
  4. a whole-screen jump is evidence and never a verdict on its own, because the game's own scene change
     measures as a jump (0.896) while the same window twelve seconds apart measures 0.000;
  5. the palette floor that splits "art" from "not the game" sits between the two populations measured on the
     real takes (0.9285 to 0.9939 for the game, 0.0024 and 0.0025 for the covered frames), and one frame's
     verdict follows from its own share;
  6. the one reading taken once the recorder has stopped is asked while the game is still the raised window and
     is a NOTE, never a failure (card t_4da3eb20: asked after `restore_foreground` it measured the window this
     tool itself put there, and its failure text reached tools/judge_panel.py as "Recorded failure in that run"
     on takes whose frames were all the game's).

Why the takes are built here and not read from output/demo: the recordings are gitignored outputs, so a checkout
at HEAD has none, and tools/check_test_inputs.py forbids a test that skips because a path is missing. The two game
frames are committed (output/nes_title_frame.png, output/bg_battle_deck_night_frame.png) and the stand-in window
is drawn in the colours the real defect measured.

Run: python -m pytest tests/test_play_demo_cover.py -q
"""

from __future__ import annotations

import importlib.util
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
GAME_FRAME_ONE = os.path.join(ROOT, "output", "nes_title_frame.png")
GAME_FRAME_TWO = os.path.join(ROOT, "output", "bg_battle_deck_night_frame.png")
SIX_CHECKS = ("file", "duration", "stream", "not_black", "not_a_terminal", "motion")
# The shares measured on the real takes on 2026-10-26: 33 frames of the game landed between the first two
# numbers, and the two frames a window covered landed on the last two.
MEASURED_GAME_SHARES = (0.9285, 0.9939)
MEASURED_COVERED_SHARES = (0.0024, 0.0025)
# The frame the recorder writes, which is what verify_video measures.
WIDTH, HEIGHT, FPS = 768, 720, 60


def load_tool(name: str):
    path = os.path.join(TOOLS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def demo_module():
    """play_demo with its drawing path available, or a skip when this host cannot run it at all.

    Card TEST-CLASSIFY-33: tools/play_demo.py reaches tools/capture_title.py, which binds ctypes.windll at
    module level, so the import raises off Windows. A missing ffmpeg is a capability of the machine and not an
    input this repository carries, which is the distinction tools/check_test_inputs.py draws.
    """
    if sys.platform != "win32":
        pytest.skip("Windows host only: play_demo reaches capture_title, which binds ctypes.windll")
    demo = load_tool("play_demo")
    try:
        if not demo.ffmpeg_path():
            pytest.skip("ffmpeg is not installed on this machine, so no frame can be read")
    except demo.PlatformUnavailable as error:
        pytest.skip("the drawing path is not importable here: %s" % error)
    return demo


def window_frame(path):
    """A stand-in for a foreign window over the game, in the colours the real defect measured.

    Measured on the two covered frames of output/demo/demo-box-2026-10-26.mp4 on 2026-10-26: a field of
    (30,31,34) with a (137,177,246) accent. Drawn at 768x720, the size of the frame the recorder writes.
    """
    from PIL import Image, ImageDraw
    image = Image.new("RGB", (WIDTH, HEIGHT), (30, 31, 34))
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, WIDTH - 1, 34], fill=(137, 177, 246))
    for row in range(60, HEIGHT - 20, 22):
        draw.line([(40, row), (40 + (row * 7) % 500, row)], fill=(200, 200, 200), width=2)
    image.save(str(path))
    return str(path)


def build_take(demo, out_path, segments):
    """One mp4 from a list of (png, seconds), scaled to the recorder's frame, by ffmpeg. Returns the path."""
    cap = demo.capture_module()
    arguments = []
    for png, seconds in segments:
        arguments += ["-loop", "1", "-framerate", str(FPS), "-t", "%.2f" % seconds, "-i", png]
    scaled = ["[%d:v]scale=%d:%d:flags=neighbor,setsar=1[v%d]" % (index, WIDTH, HEIGHT, index)
              for index in range(len(segments))]
    joined = "".join("[v%d]" % index for index in range(len(segments)))
    graph = ";".join(scaled) + ";%sconcat=n=%d:v=1:a=0[out]" % (joined, len(segments))
    arguments += ["-filter_complex", graph, "-map", "[out]", "-r", str(FPS), "-c:v", "libx264",
                  "-preset", "ultrafast", "-crf", "20", "-pix_fmt", "yuv420p", str(out_path)]
    ok, note = cap.run_ffmpeg(demo.ffmpeg_path(), arguments, timeout=300)
    assert ok, "ffmpeg could not build the test take: %s" % note
    return str(out_path)


def check_script():
    """A script dict with the fields verify_video reads, and a 3 s floor so the fixture stays short."""
    return {"record": {"min_seconds": 3.0, "fps": FPS, "width": WIDTH, "height": HEIGHT, "scale": 3,
                       "out": "build/_cover_test.mp4"},
            "checks": {}}


@pytest.fixture(scope="module")
def takes(tmp_path_factory):
    """The two synthetic takes: one all game, one with two seconds of a window over it."""
    demo = demo_module()
    work = tmp_path_factory.mktemp("cover_takes")
    window = window_frame(work / "window.png")
    clean = build_take(demo, work / "clean.mp4", [(GAME_FRAME_ONE, 3.0), (GAME_FRAME_TWO, 4.0)])
    covered = build_take(demo, work / "covered.mp4",
                         [(GAME_FRAME_ONE, 2.0), (window, 2.0), (GAME_FRAME_TWO, 3.0)])
    return {"demo": demo, "clean": clean, "covered": covered, "window": window}


# ---------------------------------------------------------------------------------------------------------------------
# 1 and 2: the verdict on a take

@pytest.mark.windows_only
def test_a_take_with_a_window_over_the_game_is_polluted_and_never_an_art_finding(takes):
    """The card's own defect: frames of a window were reported as the game drawn off the palette."""
    demo, take = takes["demo"], takes["covered"]
    # The stand-in window is off the palette the way the real one was, and that is measured here, not assumed.
    share = demo.palette_share(takes["window"], demo.palette_entries(), 12)
    assert share is not None and share < demo.OFF_PALETTE_ART_MIN, share

    ok, report = demo.verify_video(take, check_script())
    findings = " ".join(report.get("findings", []))
    assert ok is False, "a take with a window over the game must not pass"
    assert report["polluted"] is True
    assert "POLLUTED 2 of 7" in findings, findings
    assert "NOT an art finding" in findings, findings
    assert "the art lane's to look at" not in findings, "the art lane was sent to look at a window: %s" % findings
    line = report["checks"]["not_polluted"]
    assert line.startswith("FAIL"), line
    assert "t=2.4" in line and "t=3.5" in line, line
    verdicts = {row["t"]: row.get("verdict") for row in report["samples"]}
    assert verdicts[2.38] == "not the game" and verdicts[3.5] == "not the game", verdicts
    # The palette check still passes the take, which is exactly why the split was needed: "5 of 7 are the
    # game's own picture" reads healthy and says nothing about the two that are not.
    assert report["checks"]["not_a_terminal"].startswith("PASS"), report["checks"]["not_a_terminal"]


@pytest.mark.windows_only
def test_a_clean_take_still_passes_its_six_checks(takes):
    demo, take = takes["demo"], takes["clean"]
    ok, report = demo.verify_video(take, check_script())
    assert ok is True, report["checks"]
    for name in SIX_CHECKS:
        assert report["checks"][name].startswith("PASS"), "%s on a clean take: %s" % (name, report["checks"][name])
    assert report["polluted"] is False
    assert not [row for row in report["samples"] if row.get("verdict")]


@pytest.mark.windows_only
def test_a_covered_frame_is_named_by_the_process_that_owned_the_rectangle(takes):
    """What the during-recording watch adds: the owner's image name, which a finished file cannot give."""
    demo, take = takes["demo"], takes["covered"]
    pollution = [
        {"at": 2.4, "kind": "cover", "points": 3, "who": ["codex.exe 'Primordial Paradox'"]},
        {"at": 3.5, "kind": "cover", "points": 4, "who": ["codex.exe 'Primordial Paradox'"]},
        {"at": 1.0, "kind": "jump", "changed": 0.87},
    ]
    ok, report = demo.verify_video(take, check_script(), pollution=pollution)
    assert ok is False
    assert report["polluted"] is True
    line = report["checks"]["not_polluted"]
    assert "codex.exe" in line and line.startswith("FAIL"), line
    findings = " ".join(report.get("findings", []))
    assert "covered by codex.exe" in findings, findings
    # A jump that no game log line explains is reported as evidence and never as the verdict by itself.
    assert report["checks"]["jumps"].startswith("NOTE"), report["checks"]["jumps"]
    assert "0.87" in report["checks"]["jumps"]


@pytest.mark.windows_only
def test_a_jump_alone_never_pollutes_a_clean_take(takes):
    """A whole-screen jump with no covering owner and no foreign frame: evidence, not a verdict."""
    demo, take = takes["demo"], takes["clean"]
    ok, report = demo.verify_video(take, check_script(),
                                   pollution=[{"at": 1.0, "kind": "jump", "changed": 0.85}])
    assert ok is True, report["checks"]
    assert report["polluted"] is False, "a jump on its own must not condemn a take"
    assert report["checks"]["not_polluted"].startswith("PASS"), report["checks"]["not_polluted"]
    assert report["checks"]["jumps"].startswith("NOTE"), report["checks"]["jumps"]


# ---------------------------------------------------------------------------------------------------------------------
# 3: the watch itself

class FakeScreen(object):
    """A screen the test controls: the same colour until the test changes it."""

    def __init__(self, colour=(20, 30, 40)):
        self.colour = colour

    def grab(self, bbox):
        from PIL import Image
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return Image.new("RGB", (width, height), self.colour)


CLEAR = (lambda: ([], [(1234, "PrimordialParadox.exe", "Primordial Paradox")]))
COVERED = (lambda: ([(100, 100, "codex.exe", "Primordial Paradox")],
                    [(999, "codex.exe", "Primordial Paradox")]))


def watch(demo, owners, screen=None, log_lines=None, stop_polls=2):
    ticks = {"t": 0.0}
    watcher = demo.PollutionWatch(
        hwnd=1234, rect=(0, 0, WIDTH, HEIGHT), owners_at=owners,
        log_lines=log_lines or (lambda: 0), grab=(screen or FakeScreen()).grab,
        clock=lambda: ticks["t"], stop_polls=stop_polls)
    watcher.started_at = watcher.clock()
    return watcher, ticks


@pytest.mark.windows_only
def test_the_watch_names_the_owner_and_stops_the_run_after_two_cover_samples(takes):
    demo = takes["demo"]
    watcher, _ticks = watch(demo, COVERED)
    first = watcher.poll()
    assert "cover" in first and first["cover"]["owners"] == ["codex.exe"]
    assert watcher.polluted() is True
    assert watcher.stop_requested is False, "one sample during a focus handover must not kill a take"
    watcher.poll()
    assert watcher.stop_requested is True
    assert "codex.exe" in watcher.cover_summary()
    assert watcher.first_cover_at() == 0.0
    assert [row["kind"] for row in watcher.evidence()] == ["cover", "cover"]


@pytest.mark.windows_only
def test_one_cover_sample_is_evidence_of_a_polluted_take_without_stopping_it(takes):
    demo = takes["demo"]
    answers = [COVERED, CLEAR, CLEAR]

    def owners():
        return answers.pop(0)() if answers else CLEAR()

    watcher, _ticks = watch(demo, owners)
    watcher.poll()
    watcher.poll()
    assert watcher.polluted() is True
    assert watcher.stop_requested is False
    assert len(watcher.evidence()) == 1


@pytest.mark.windows_only
def test_a_clean_watch_leaves_a_take_alone(takes):
    watcher, _ticks = watch(takes["demo"], CLEAR)
    for _ in range(4):
        watcher.poll()
    assert watcher.polluted() is False
    assert watcher.stop_requested is False
    assert watcher.evidence() == []


@pytest.mark.windows_only
def test_a_jump_the_log_does_not_explain_is_evidence_and_a_logged_jump_is_not(takes):
    """The card's own wording: a jump the run's log does not explain. A logged scene change is not evidence."""
    demo = takes["demo"]
    screen = FakeScreen((10, 10, 10))
    lines = {"n": 5}
    watcher, ticks = watch(demo, CLEAR, screen=screen, log_lines=lambda: lines["n"])
    watcher._previous = demo.screen_signature(watcher.rect, screen.grab)
    watcher._previous_lines = lines["n"]

    screen.colour = (250, 250, 250)
    ticks["t"] += 1.0
    first = watcher.poll()
    assert first.get("jump", {}).get("explained_by_log") is False, first
    assert [row["kind"] for row in watcher.evidence()] == ["jump"]
    assert watcher.polluted() is False, "a jump alone is never a verdict"

    # The same kind of jump, with the game's own log growing during the poll: a scene change it explains.
    lines["n"] = 6
    screen.colour = (10, 10, 10)
    ticks["t"] += 1.0
    second = watcher.poll()
    assert second.get("jump", {}).get("explained_by_log") is True, second
    assert [row["kind"] for row in watcher.evidence()] == ["jump"], "a logged jump was kept as evidence"


@pytest.mark.windows_only
def test_the_jump_threshold_notices_a_window_and_not_a_still_screen(takes):
    """Measured on fixture frames: the same frame twice is 0.000, the game to the window is a whole jump."""
    demo = takes["demo"]
    from PIL import Image

    def signature(path):
        def grab(bbox):
            with Image.open(path) as opened:
                return opened.convert("RGB")
        return demo.screen_signature((0, 0, WIDTH, HEIGHT), grab)

    game = signature(GAME_FRAME_ONE)
    again = signature(GAME_FRAME_ONE)
    window = signature(takes["window"])
    assert demo.signature_jump(game, again) == pytest.approx(0.0, abs=1e-9)
    assert demo.signature_jump(game, window) >= demo.SIGNATURE_JUMP


# ---------------------------------------------------------------------------------------------------------------------
# 5: the floor, and one frame's verdict

@pytest.mark.windows_only
def test_the_palette_floor_sits_between_the_two_measured_populations(takes):
    demo = takes["demo"]
    assert max(MEASURED_COVERED_SHARES) < demo.OFF_PALETTE_ART_MIN < min(MEASURED_GAME_SHARES)


@pytest.mark.windows_only
def test_one_frame_is_split_into_game_art_or_not_the_game_by_its_own_share(takes):
    """The five answers, on the numbers measured for each population on 2026-10-26."""
    demo = takes["demo"]
    palette_min, min_colours = 0.90, 6
    assert demo.frame_verdict(0.9285, 20741, min_colours, palette_min) == "game"
    assert demo.frame_verdict(0.9939, 193, min_colours, palette_min) == "game"
    assert demo.frame_verdict(0.0025, 11681, min_colours, palette_min) == "not the game"
    assert demo.frame_verdict(0.75, 40, min_colours, palette_min) == "art", "mostly palette and off it is art"
    assert demo.frame_verdict(0.20, 3, min_colours, palette_min) == "blank"
    assert demo.frame_verdict(None, 900, min_colours, palette_min) == "unjudged", "no measurement is no verdict"


# ---------------------------------------------------------------------------------------------------------------------
# 6: the single reading taken once the recorder has stopped (card t_4da3eb20)

@pytest.mark.windows_only
def test_the_stopped_recording_is_asked_who_owns_the_rectangle_before_the_previous_window_returns(takes):
    """The card's own defect: the question was asked after this tool had raised the previous window again."""
    with open(os.path.join(TOOLS, "play_demo.py"), "r", encoding="utf-8") as handle:
        source = handle.read()
    body = source[source.index("def run_demo("):]
    restore = body.index("cap.restore_foreground(previous)")
    before, after = body[:restore], body[restore:body.index("if recorder.returncode")]
    assert "cap.cover_report(hwnd, rect)" in before, "nothing asks who owns the rectangle while the game is raised"
    assert "cover_report" not in after, (
        "the post-recording cover question still runs after restore_foreground, so it can measure the window "
        "this tool itself put back in front")
    # The wording that reached the judge panel on a clean take, and the list it was pushed into.
    assert "after the recording another window owns" not in source
    assert "report.setdefault(\"notes\", []).append(post_record_note)" in source
    assert "failures.append(\"after the recording" not in source


@pytest.mark.windows_only
def test_a_window_over_the_rectangle_when_the_recorder_stopped_is_a_note_and_names_the_process(takes, capsys):
    """Evidence, not a verdict: the six checks and the during-recording samples are what decide a take."""
    demo = takes["demo"]
    assert demo.post_recording_cover_note([]) is None, "a clean reading has to say nothing at all"
    note = demo.post_recording_cover_note([(100, 100, "codex.exe", "Primordial Paradox")])
    assert note.startswith("NOTE"), note
    assert "codex.exe" in note and "1 of the sampled points" in note, note
    assert "not a verdict" in note, note
    # Nothing in it reads as a defect: judge_panel.py quotes run.failures as "Recorded failure in that run".
    assert "fail" not in note.lower(), note
    # And it is printed beside the checks, where the other evidence lines go.
    demo.print_report({"checks": {}, "notes": [note]})
    printed = capsys.readouterr().out
    assert printed.strip() == note, printed

