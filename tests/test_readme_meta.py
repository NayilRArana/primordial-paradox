"""The README gate: the front page may only change through tools/readme_meta.py, which has a Meta model write it and stamps the result."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import readme_meta  # noqa: E402


def test_the_readme_was_written_by_a_meta_model_and_not_edited_since():
    path = os.path.join(ROOT, "README.md")
    assert os.path.exists(path), "no README.md"
    assert readme_meta.check_file(path) == "", readme_meta.check_file(path)


def test_a_stamp_round_trips_and_a_hand_edit_breaks_it(tmp_path):
    body = "## A\n\nSome text with 3 numbers and `code`.\n"
    f = tmp_path / "README.md"
    f.write_text(body + "\n<!-- readme-author: muse-spark-1.3 body-sha256: %s -->\n" % readme_meta.body_hash(body), encoding="utf-8")
    assert readme_meta.check_file(str(f)) == ""
    f.write_text(f.read_text(encoding="utf-8").replace("Some", "Other"), encoding="utf-8")
    assert "changed after the Meta model wrote it" in readme_meta.check_file(str(f))


def test_a_stamp_naming_a_non_meta_model_is_refused(tmp_path):
    body = "## A\n\ntext\n"
    f = tmp_path / "README.md"
    f.write_text(body + "\n<!-- readme-author: some-other-model body-sha256: %s -->\n" % readme_meta.body_hash(body), encoding="utf-8")
    assert "not a Meta model" in readme_meta.check_file(str(f))


def test_the_validator_rejects_a_rewrite_that_loses_a_fact_or_uses_a_dash():
    orig = "## H\n\nWe ran 2,694 tests, see `tools/x.py` and https://example.org/a.\n"
    ok, bad = readme_meta.valid(orig, "## H\n\nWe ran some tests.\n")
    assert not ok and "2,694" in bad
    ok, bad = readme_meta.valid(orig, "## H\n\nWe ran 2,694 tests " + chr(0x2014) + " see `tools/x.py` and https://example.org/a.\n")
    assert not ok and "dash" in bad
    ok, bad = readme_meta.valid(orig, "## H\n\nWe ran 2,694 tests: see `tools/x.py` and https://example.org/a.\n")
    assert ok, bad
