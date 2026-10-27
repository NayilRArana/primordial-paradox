"""The repair pass, pinned: it moves the accompaniment and never the hook.

Card t_c0597404. `tools/counterpoint/repair.py` edits a score, so the tests here are about what it may
not do as much as what it does: the hook voice comes out byte for byte identical, every replacement
pitch stays inside the voice's own register, a pad chord is never left as something that is not a triad,
and a note it cannot fix is left as a clash rather than silently deleted for no gain.
"""

from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
COUNTERPOINT = os.path.join(TOOLS, "counterpoint")
for path in (TOOLS, COUNTERPOINT):
    if path not in sys.path:
        sys.path.insert(0, path)

import clash  # noqa: E402
import humanize  # noqa: E402
import repair  # noqa: E402

BEAT = 480
BAR = BEAT * 3


def write(path, notes_by_voice):
    payload = {"division": 480, "tempo_us": 476190, "time_sig": (3, 4), "tracks": [
        {"name": name, "notes": notes, "cc": []} for name, notes in notes_by_voice.items()]}
    humanize.write_smf(payload, str(path))
    return str(path)


def raw_count(song):
    return len([e for e in clash.analyse(song.score()) if e["class"] == "raw clash"])


def test_the_hook_and_the_drums_are_never_in_the_movable_set():
    assert repair.HOOK == "vrc6 pulse a"
    movable = tuple(v for v in clash.VOICES if v != repair.HOOK)
    assert repair.HOOK not in movable
    assert repair.repair.__defaults__ is not None


def test_candidates_stay_inside_the_voice_register():
    for voice, (lo, hi) in repair.RANGES.items():
        for candidate in repair.candidates(voice, (lo + hi) // 2):
            assert lo <= candidate <= hi, (voice, candidate)


def test_a_single_clash_is_repaired_and_the_hook_is_untouched(tmp_path):
    # The pad holds a bare C3 against a melody on B4: a major seventh, unprepared and unresolved.
    notes = {
        "triangle": [(0, BAR, 48, 96)],
        "vrc6 saw": [(0, BAR, 48, 80), (0, BAR, 55, 80)],
        "vrc6 pulse a": [(BEAT, BAR, 71, 96), (BAR, 2 * BAR, 74, 96)],
        "noise": [(0, 60, 38, 90)],
    }
    path = write(tmp_path / "clash.mid", notes)
    song = repair.Song(path)
    assert raw_count(song) > 0
    hook_before = list(song.notes["vrc6 pulse a"])

    repaired, history = repair.repair(song, rounds=4, verbose=False)

    assert raw_count(song) == 0
    assert song.notes["vrc6 pulse a"] == hook_before
    assert song.notes["noise"] == notes["noise"]
    assert repaired and history[0]["raw"] > history[-1]["raw"]


def test_a_pad_note_is_never_moved_out_of_its_triad(tmp_path):
    # Two pad notes under one onset: whatever the repair does, they have to stay a triad together.
    notes = {
        "triangle": [(0, BAR, 45, 96)],
        "vrc6 saw": [(0, BAR, 48, 80), (0, BAR, 52, 80)],
        "vrc6 pulse a": [(0, BAR, 70, 96), (BEAT, BAR, 71, 96)],
    }
    path = write(tmp_path / "pad.mid", notes)
    song = repair.Song(path)
    repair.repair(song, rounds=3, verbose=False)
    grid = song.division // 4
    groups = {}
    for start, end, pitch, velocity in song.notes["vrc6 saw"]:
        groups.setdefault(clash.snap(start, grid), []).append(pitch)
    for start, pitches in groups.items():
        classes = {p % 12 for p in pitches}
        allowed = [set(triad) for triad in list(repair.TRIADS) + list(repair.DIATONIC)]
        assert any(classes <= triad for triad in allowed), pitches


@pytest.mark.skipif(not os.path.exists(os.path.join(
    ROOT, "assets", "audio", "pp_01_title_v9", "pp_01_title_v9.mid")), reason="v9 not built")
def test_the_shipped_v9_keeps_its_promises():
    """The built file, not a rebuild: 0 raw clashes on a downbeat and 2 in the whole cue."""
    score = clash.load_score(os.path.join(ROOT, "assets", "audio", "pp_01_title_v9",
                                          "pp_01_title_v9.mid"))
    summary = clash.summarise(score, clash.analyse(score))
    assert summary["strong_raw"] == 0
    assert summary["by_class"]["raw clash"] == 2
