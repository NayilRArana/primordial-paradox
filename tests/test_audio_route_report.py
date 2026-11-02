"""Card MUSIC-REAL: the meter's dB arithmetic and the route report's verdicts, on synthetic data (no sound card, no game)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import audio_meter  # noqa: E402
import audio_route_report as rep  # noqa: E402


def test_peak_to_dbfs():
    assert abs(audio_meter.peak_to_dbfs(1.0)) < 1e-9
    assert abs(audio_meter.peak_to_dbfs(0.1) + 20.0) < 1e-6
    assert audio_meter.peak_to_dbfs(0) == -120.0 and audio_meter.peak_to_dbfs("x") == -120.0


def _line(mode, room, cue, inst=1, playing=1):
    return ("PP audio status: mode=%s room=%s cue=%s instance=%d playing=%d gain=0.7 master=1 paused=0"
            % (mode, room, cue, inst, playing))


def test_report_marks_audible_silent_and_no_cue():
    t0 = 1000.0
    events, meter = [], []
    plan = [("title", "rm_pp_title", "title_theme", -20.0, 8), ("overworld", "southampton_town_quay", "PP-03", -90.0, 8),
            ("overworld", "ship_small", "none", -120.0, 8), ("overworld", "x", "PP-05", -30.0, 3)]
    t = t0
    for mode, room, cue, db, secs in plan:
        for _ in range(secs):
            events.append((t, _line(mode, room, cue, inst=-1 if cue == "none" else 1)))
            meter.append((t, 1, db))
            meter.append((t + 0.5, 1, db))
            t += 1.0
    rows = [rep.judge(s, meter) for s in rep.segments(rep.status_points([], events, meter))]
    verdicts = [r["verdict"] for r in rows]
    assert verdicts == ["AUDIBLE", "SILENT", "NO_CUE", "TOO_SHORT"]
    assert rows[0]["peak"] == -20.0 and rows[1]["playing"] == "yes"
    assert "| AUDIBLE |" in rep.table(rows)
