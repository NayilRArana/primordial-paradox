"""Tests for tools/window_ledger.py (card t_a1228645).

What is pinned here, in order of what a judge would catch:

1. Every row of the ledger resolves, in THIS checkout, to a commit that is inside the window: it is
   not the baseline commit, and the baseline commit is its ancestor. That is the whole claim the
   ledger makes, so it is asked of the real repository rather than of a fixture, and a row that loses
   its commit fails here instead of on submission day.
2. A feature with no in-window commit is an exposure: the run exits non-zero and names the row,
   because a demo shot with no commit behind it is the disqualification risk the ledger exists for.
   That case needs history that is not this one, so it is built in a throwaway repository.
3. The pieces the answers are read from: the folder, glob and file match rules, the log parser that
   keeps a commit's files with it, the folder collapsing that keeps a row readable, and the shot
   coverage the cut is held to.

No test writes WINDOW-LEDGER.md in this checkout.
"""

import os
import subprocess
import sys

import pytest

import window_ledger

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, encoding="utf-8",
                          errors="replace", check=True, stdin=subprocess.DEVNULL).stdout.strip()


def new_repo(path):
    """A repository with the baseline tag on its first commit and one event commit after it."""
    os.makedirs(path, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.name", "ledger test")
    git(path, "config", "user.email", "ledger@example.invalid")
    with open(os.path.join(path, "game.gml"), "w", encoding="utf-8") as handle:
        handle.write("// baseline\n")
    git(path, "add", "game.gml")
    git(path, "commit", "-q", "-m", "Baseline: before the window")
    git(path, "tag", window_ledger.TAG)
    return path


def test_every_row_resolves_to_an_in_window_commit():
    data = window_ledger.collect(ROOT)
    assert data["tag_sha"], "the baseline tag must resolve in this checkout"
    for feature in window_ledger.FEATURES:
        row = window_ledger.resolve(feature, data["commits"], data["baseline"], data["head"])
        assert row["commit"] is not None, "%s has no in-window commit in this checkout" % feature["id"]
        sha = row["commit"]["sha"]
        full = git(ROOT, "rev-parse", sha)
        assert full, "%s names %s, which does not resolve" % (feature["id"], sha)
        assert git(ROOT, "merge-base", "--is-ancestor", window_ledger.TAG, sha) == ""
        assert full != git(ROOT, "rev-parse", window_ledger.TAG + "^{commit}"), \
            "%s maps to the baseline commit itself" % feature["id"]


def test_a_feature_with_no_window_commit_is_named_and_fails(tmp_path, capsys):
    repo = new_repo(str(tmp_path / "repo"))
    with open(os.path.join(repo, "unrelated.txt"), "w", encoding="utf-8") as handle:
        handle.write("nothing the demo shows\n")
    git(repo, "add", "unrelated.txt")
    git(repo, "commit", "-q", "-m", "UNRELATED (t_00000000): a file no ledger row names")

    code = window_ledger.main(["--repo", repo, "--check"])
    out = capsys.readouterr().out
    assert code == 1, out
    assert "L1 has no in-window commit" in out


def test_matches_reads_folders_globs_and_files():
    assert window_ledger.matches("game/scripts/pp_input/pp_input.gml", ["game/scripts/pp_input/"])
    assert window_ledger.matches("tools/nes_check.py", ["tools/nes_check.py"])
    assert window_ledger.matches("data/maps/osm/quay.json", ["data/maps/*.json"]) is False
    assert window_ledger.matches("data/audio.json", ["data/audio.json"]) is True
    assert window_ledger.matches("data/audio_extra.json", ["data/audio.json"]) is False, \
        "a file rule must not swallow its neighbours"
    assert window_ledger.matches("tests/test_one.py", ["tests/"]) is True


def test_parse_log_keeps_each_commits_files_with_it():
    raw = "\n".join([
        "aaaaaaa\x002026-10-26 09:00\x00FIRST: one file",
        "",
        "game/scripts/a.gml",
        "bbbbbbb\x002026-10-26 10:00\x00SECOND: two files",
        "game/scripts/b.gml",
        "tests/test_b.py",
        "",
    ])
    commits = window_ledger.parse_log(raw)
    assert [c["sha"] for c in commits] == ["aaaaaaa", "bbbbbbb"]
    assert commits[0]["files"] == ["game/scripts/a.gml"]
    assert commits[1]["files"] == ["game/scripts/b.gml", "tests/test_b.py"]
    assert commits[1]["when"] == "2026-10-26 10:00"


def test_names_collapses_a_folder_so_a_row_stays_readable():
    cached = ["data/ai_cache/%02d.json" % n for n in range(9)]
    assert window_ledger.names(cached) == "`data/ai_cache/` (9 files)"
    assert window_ledger.names(["README.md", "HACKATHON.md"]) == "`README.md`, `HACKATHON.md`"


def test_coverage_finds_a_shot_no_row_covers():
    rows = [(feature, {}) for feature in window_ledger.FEATURES]
    covered, uncovered = window_ledger.coverage(["A1", "Z9"], rows)
    assert "A1" in covered and covered["A1"] == "L6"
    assert uncovered == ["Z9"]
