"""tests for tools/judge_panel.py: the video pick, the sample, the score parse, and the five card bodies.

Card W4 JUDGE-PANEL (t_70840bce). What is worth pinning here is everything that could turn the
nightly panel into a number the team is not entitled to trust:

  1. the newest `nightly-*.mp4` by modification time, not by the date in the name, because a run
     that re-recorded an older date is still the newest picture;
  2. the frame sample refuses a request over the API's pixel ceiling instead of sending it;
  3. a score outside 1 to 10 is NOT JUDGED and never a zero, and the weighted total is computed
     here (score / 10 * weight) so it can be reproduced by hand;
  4. no more than five fixes are kept, and the count of the ones dropped is stated;
  5. a card body that names a path this repository does not have is flagged beside the fix;
  6. the panel text carries no em dash or en dash, which is the house rule for every artifact.

The tests that would need the real capture do not depend on it: `output\\` is gitignored, so the
nightly video is absent from a clean worktree and a test that read it would pass here and fail in
the gate. The one test that sends a request uses a fake transport and a one pixel PNG built in the
test, so the model rotation is measured without a key and without the network.
"""

from __future__ import annotations

import os
import sys
import urllib.error

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import eye_critic  # noqa: E402
import judge_panel  # noqa: E402

ANSWER = (
    "### The four scores\n"
    "Impact: 6/10, because the talk mechanic is not visible in the sample.\n"
    "Use of Meta AI tooling: 5/10, because the model runs but the screen does not show it.\n"
    "Technical depth: 7/10, because the hardware limits are enforced in code.\n"
    "Demo: 4/10, because the capture is 106 seconds short of the script.\n"
    "### Machine readable block\n"
    "```json\n"
    '{"impact": 6, "impact_reason": "the talk mechanic is not visible in the sample", '
    '"meta_tooling": 5, "meta_tooling_reason": "the model runs but the screen does not show it", '
    '"technical_depth": 7, "technical_depth_reason": "the hardware limits are enforced in code", '
    '"demo": 4, "demo_reason": "the capture is 106 seconds short of the script", '
    '"fixes": ['
    '{"title": "Show the AI answer in the NES box", "lane": "gamedev", "criterion": "Impact", '
    '"body": "Draw the model answer inside the 256 by 240 text box in the first fight so the '
    'verdict is on screen. The judge sees the sailor answer your line, not a caption that says '
    'he did."}, '
    '{"title": "Record the full three minutes", "lane": "testing", "criterion": "Demo", '
    '"body": "Record 180 seconds as the script plans, not 73, so the arrival and the fight are in '
    'the video at all."}, '
    '{"title": "Print the bake row on screen", "lane": "builder", "criterion": "Use of Meta AI '
    'tooling", "body": "Print the model name, the latency and the offline flag for each TALK so a '
    'judge can see a Meta model doing the work."}, '
    '{"title": "Commit the missing theme stream", "lane": "audit", "criterion": "Technical depth", '
    '"body": "Add datafiles/streams/percy_theme_v3.ogg to the commit so the nightly suite stops '
    'failing on a missing asset."}, '
    '{"title": "Name the file in the body", "lane": "engineering", "criterion": "Demo", '
    '"body": "Rewrite scenes/walk.py to route the right presses to the walk so the avatar moves '
    'on screen in the last third of the capture."}, '
    '{"title": "A sixth fix that must be dropped", "lane": "gamedev", "criterion": "Impact", '
    '"body": "This one is over the limit of five and must not appear as a card."}]}\n'
    "```\n"
)

FRAMES = [
    {"index": 1, "at_s": 6.1, "path": "a.png", "blank": False},
    {"index": 2, "at_s": 18.4, "path": "b.png", "blank": True},
    {"index": 3, "at_s": 42.9, "path": "c.png", "blank": False},
]
INFO = {"duration_s": 73.483, "width": 768, "height": 720, "fps": 60.0, "codec": "h264"}
SCRIPT = {"excerpt": "", "verify": {"planned_seconds": 71.0, "recorded_seconds": 73.5,
                                   "has_audio": True, "failures": ["no footstep cue"]},
          "nightly_line": "", "missing": []}


def test_the_newest_nightly_is_picked_by_time_not_by_name(tmp_path):
    older = tmp_path / "nightly-2026-10-27.mp4"
    newer = tmp_path / "nightly-2026-10-26.mp4"
    other = tmp_path / "demo-box-2026-10-26.mp4"
    for path in (older, newer, other):
        path.write_bytes(b"x")
    os.utime(older, (1_700_000_000, 1_700_000_000))
    os.utime(newer, (1_700_000_900, 1_700_000_900))
    os.utime(other, (1_800_000_000, 1_800_000_000))
    assert judge_panel.newest_nightly(str(tmp_path)) == str(newer)


def test_no_nightly_is_none_and_not_an_error(tmp_path):
    assert judge_panel.newest_nightly(str(tmp_path)) is None


def test_a_sample_over_the_pixel_ceiling_is_refused(monkeypatch):
    monkeypatch.setattr(judge_panel, "probe_video", lambda video: dict(INFO))
    with pytest.raises(judge_panel.PanelError) as caught:
        judge_panel.sample_frames("x.mp4", count=8)
    assert "megapixels" in str(caught.value)


def test_the_script_excerpt_holds_the_shot_table_once():
    script = judge_panel.script_facts(None)
    assert script["script_path"] and os.path.exists(script["script_path"])
    assert script["excerpt"].count("| Shot |") == 1
    assert "| S6 |" in script["excerpt"], "the sixth shot is where the TALK claim lives"
    assert "the sailor" in script["excerpt"] or "caption" in script["excerpt"].lower()


def test_measured_lines_state_the_duration_gap_and_the_blank_frames():
    lines = judge_panel.measured_lines(FRAMES, INFO, SCRIPT, None)
    text = " ".join(lines)
    assert "73.483 s" in text
    assert "106.5 s short of" in text, "the gap to the judged 180 s is the measured headline"
    assert "1 of the 3 frames are one colour" in text
    assert "no footstep cue" in text
    assert "h264" in text and "not a PPU palette measurement" in text


def test_scores_reasons_and_the_weighted_total():
    parsed = judge_panel.parse_panel(ANSWER)
    assert parsed["scores"] == {"impact": 6, "meta_tooling": 5, "technical_depth": 7, "demo": 4}
    assert parsed["reasons"]["impact"].startswith("the talk mechanic")
    # 6/10*30 + 5/10*25 + 7/10*20 + 4/10*25 = 18 + 12.5 + 14 + 10
    assert parsed["weighted"] == {"points": 54.5, "of": 100, "criteria_scored": 4,
                                  "complete": True}


def test_five_fixes_are_kept_and_the_sixth_is_counted_as_dropped():
    parsed = judge_panel.parse_panel(ANSWER)
    assert len(parsed["fixes"]) == judge_panel.MAX_FIXES == 5
    assert parsed["dropped_fixes"] == 1
    assert "A sixth fix" not in " ".join(fix["body"] for fix in parsed["fixes"])
    assert [fix["priority"] for fix in parsed["fixes"]] == list(judge_panel.FIX_PRIORITY)


def test_a_lane_the_fleet_does_not_run_is_marked_not_guessed():
    parsed = judge_panel.parse_panel(ANSWER)
    lanes = [fix["lane"] for fix in parsed["fixes"]]
    assert lanes[:4] == ["gamedev", "testing", "builder", "audit"]
    assert lanes[4] == "builder", "'engineering' is mapped to the builder lane"
    assert parsed["fixes"][4]["lane_raw"] == "engineering"


def test_a_score_outside_one_to_ten_is_not_judged_never_zero():
    parsed = judge_panel.parse_panel('```json\n{"impact": 11, "demo": 0, '
                                     '"technical_depth": 7, "technical_depth_reason": "x"}\n```')
    assert parsed["scores"]["impact"] is None
    assert parsed["scores"]["demo"] is None
    assert parsed["scores"]["technical_depth"] == 7
    assert parsed["weighted"]["criteria_scored"] == 1
    assert parsed["weighted"]["complete"] is False


def test_scores_are_read_from_the_human_lines_when_the_json_block_is_missing():
    text = "Impact: 6/10, because the mechanic is not visible.\nDemo: 4/10, because it is short.\n"
    parsed = judge_panel.parse_panel(text)
    assert parsed["scores"]["impact"] == 6 and parsed["scores"]["demo"] == 4
    assert parsed["scores"]["meta_tooling"] is None
    assert parsed["reasons"]["impact"].startswith("the mechanic")


def test_a_body_that_names_a_path_the_repo_lacks_is_flagged():
    assert judge_panel.unknown_paths("Rewrite scenes/walk.py to route the presses.") == \
        ["scenes/walk.py"]
    assert judge_panel.unknown_paths("Use tools/judge_panel.py, which exists.") == []


def test_the_panel_words_are_checked_against_the_measured_frames():
    frozen = {"reasons": {"demo": "The final frames are a frozen static screen."}}
    notes = judge_panel.measured_disagreements(frozen, FRAMES, INFO)
    assert any("1 of 3" in note for note in notes), notes
    lying = {"reasons": {"demo": "The video runs for 40.0 seconds only."}}
    assert any("40.0 s" in note for note in
               judge_panel.measured_disagreements(lying, FRAMES, INFO))
    # A reason that agrees with the measurement raises nothing at all.
    assert judge_panel.measured_disagreements(judge_panel.parse_panel(ANSWER), FRAMES, INFO) == []


def test_the_panel_text_is_complete_and_has_no_long_dashes(tmp_path):
    parsed = judge_panel.parse_panel(ANSWER)
    cards, folder = judge_panel.card_bodies(parsed["fixes"], "2026-10-26", str(tmp_path))
    text = judge_panel.render_panel(
        os.path.join(ROOT, "output", "demo", "nightly-2026-10-26.mp4"), INFO, FRAMES, SCRIPT,
        {"model": "gemini-3.5-flash", "tokens": "1 in / 1 out", "attempts": []},
        parsed, cards, [], "user environment", "2026-10-26",
        [{"model": "gemini-3.5-flash", "outcome": "answered"}], parsed["dropped_fixes"])
    for dash in ("\u2014", "\u2015", "\u2013", "\u2212", "\u2011"):
        assert dash not in text
    assert "Weighted total: **54.5 of 100**" in text
    assert text.count("### Fix ") == 5
    assert len(cards) == 5 and all(os.path.exists(row["body_path"]) for row in cards)
    assert "hermes kanban --board nayil-ops create" in text
    assert "This tool creates no cards." in text
    assert "The sixth fix" not in text
    assert "scenes/walk.py" in text, "the invented path in fix 5 must be flagged"


def test_a_real_request_walks_the_chain_on_a_per_day_refusal(tmp_path, monkeypatch):
    """The rotation is measured, not claimed: the first model answers a real 429 body."""
    from PIL import Image

    frame = tmp_path / "frame.png"
    Image.new("RGB", (16, 16), (16, 16, 16)).save(frame)
    answer = {"candidates": [{"content": {"parts": [{"text": ANSWER}]},
                              "finishReason": "STOP"}],
              "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 10}}
    refused, answered = "model-a", "model-b"

    def fake_transport(request, timeout=None):
        if "/models/%s:" % refused in request.full_url:
            raise urllib.error.HTTPError(request.full_url, 429, "quota", {},
                                         __import__("io").BytesIO(
                                             judge_panel.eye_drive.QUOTA_BODY.encode("utf-8")))
        return judge_panel._FakeResponse(answer)

    monkeypatch.setenv("PP_EYE_LEDGER", str(tmp_path / "ledger.csv"))
    monkeypatch.setenv(eye_critic.KEY_ENV, "test-placeholder")
    monkeypatch.delenv("PP_AI_BACKEND", raising=False)
    monkeypatch.setattr(eye_critic, "_urlopen", fake_transport)
    gate = eye_critic.RateGate(path=str(tmp_path / "ledger.csv"), per_minute=0, per_day=0)
    log = []
    frames = [{"index": 1, "at_s": 0.5, "path": str(frame), "blank": False}]
    result = judge_panel.ask_panel(frames, INFO, SCRIPT, chain=(refused, answered), gate=gate,
                                   log=log)
    assert result["model"] == answered
    assert [attempt["outcome"] for attempt in result["attempts"]] == ["refused", "answered"]
    assert log and refused in log[0]
    parsed = judge_panel.parse_panel(result["text"])
    assert parsed["weighted"]["points"] == 54.5


# --------------------------------------------------------------------------- the Meta judge path
# Added after the manager's 2026-10-26 17:15 comment on this card: muse-spark-1.3 is the judge model,
# a billed call must not be described as free, and the five drafts land in the manager's inbox.

def test_the_judge_model_is_muse_spark_on_the_meta_backend(monkeypatch):
    monkeypatch.setenv("PP_AI_BACKEND", "meta")
    assert judge_panel.meta_backend() is True
    assert judge_panel.active_chain() == ("muse-spark-1.3",)
    assert "muse-spark-1.3" in judge_panel.chain_note()


def test_the_gemini_free_tier_chain_is_kept_for_the_gemini_backend(monkeypatch):
    monkeypatch.setenv("PP_AI_BACKEND", "gemini")
    assert judge_panel.meta_backend() is False
    assert judge_panel.active_chain() == judge_panel.MODEL_CHAIN
    assert judge_panel.chain_note() == judge_panel.CHAIN_NOTE


def test_a_billed_meta_panel_says_billed_and_never_free(tmp_path):
    parsed = judge_panel.parse_panel(ANSWER)
    cards, _folder = judge_panel.card_bodies(parsed["fixes"], "2026-10-27", str(tmp_path))
    text = judge_panel.render_panel(
        "nightly.mp4", INFO, FRAMES, SCRIPT,
        {"model": "muse-spark-1.3", "tokens": "900 in / 120 out", "attempts": []},
        parsed, cards, [], "user environment (META_API_KEY)", "2026-10-27",
        [{"model": "muse-spark-1.3", "outcome": "answered"}], parsed["dropped_fixes"],
        chain=judge_panel.META_CHAIN, inbox=str(tmp_path / "director.md"))
    assert "billed: this call ran on the Meta Model API" in text
    assert "the free tier is free" not in text
    assert "data\\ai_cache" in text, "the replay cache the judges use is named on the panel"
    assert "`muse-spark-1.3`" in text
    for dash in ("\u2014", "\u2015", "\u2013", "\u2212", "\u2011"):
        assert dash not in text


def test_the_meta_ceiling_counts_only_todays_judge_model_rows(tmp_path):
    import csv
    import datetime
    path = tmp_path / "ledger.csv"
    now = datetime.datetime(2026, 10, 27, 1, 0, tzinfo=datetime.timezone.utc)
    rows = [
        {"at": "2026-10-27T00:10:00Z", "model": "muse-spark-1.3", "status": "ok",
         "role": "judge-panel"},
        {"at": "2026-10-27T00:40:00Z", "model": "muse-spark-1.3", "status": "error",
         "role": "judge-panel"},
        {"at": "2026-10-26T22:00:00Z", "model": "muse-spark-1.3", "status": "ok",
         "role": "judge-panel"},
        {"at": "2026-10-27T00:41:00Z", "model": "gemini-3.5-flash", "status": "ok",
         "role": "judge-panel"},
        {"at": "2026-10-27T00:42:59Z", "model": "muse-spark-1.3", "status": "ok",
         "role": "review"},
    ]
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=eye_critic.LEDGER_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    assert judge_panel.meta_runs_today(str(path), now.timestamp()) == 2, \
        "an errored call spent credits too, and yesterday's row is not today's"
    refusal = judge_panel.meta_budget_refusal(limit=2, path=str(path), now=now.timestamp())
    assert refusal and "ceiling is 2" in refusal
    assert judge_panel.meta_budget_refusal(limit=3, path=str(path), now=now.timestamp()) is None
    assert judge_panel.meta_budget_refusal(limit=0, path=str(path), now=now.timestamp()) is None, \
        "a ceiling of zero means no ceiling, the documented escape hatch"


def test_the_inbox_gets_five_drafts_and_one_header_across_two_runs(tmp_path):
    parsed = judge_panel.parse_panel(ANSWER)
    cards, _folder = judge_panel.card_bodies(parsed["fixes"], "2026-10-27",
                                            str(tmp_path / "cards"))
    path = tmp_path / "director.md"
    done = {"model": "muse-spark-1.3", "tokens": "1 in / 1 out", "attempts": []}
    for _ in range(2):
        judge_panel.write_inbox("2026-10-27", cards, parsed, "nightly.mp4", done,
                                chain=judge_panel.META_CHAIN, folder=str(path))
    text = path.read_text(encoding="utf-8")
    assert text.count("# Director inbox") == 1
    assert text.count("### ") == 10, "five drafts a run, two runs, and no sixth"
    assert text.count("hermes kanban --board nayil-ops create") == 10
    assert "panel 54.5 of 100" in text
    assert "fix-01.md" in text and "fix-05.md" in text
    assert "A sixth fix" not in text
    for dash in ("\u2014", "\u2015", "\u2013", "\u2212", "\u2011"):
        assert dash not in text


def test_an_inbox_night_without_a_fix_says_so_instead_of_nothing(tmp_path):
    parsed = {"scores": {key: None for key in judge_panel.WEIGHTS},
              "reasons": {}, "fixes": [], "dropped_fixes": 0,
              "weighted": judge_panel.weighted_total({})}
    path = tmp_path / "director.md"
    judge_panel.write_inbox("2026-10-27", [], parsed, "nightly.mp4", None, folder=str(path))
    text = path.read_text(encoding="utf-8")
    assert "No draft tonight" in text
    assert "NOT JUDGED" in text


def test_the_meta_key_loader_reports_the_place_and_not_the_value(monkeypatch):
    monkeypatch.setenv("META_API_KEY", "not-a-real-key-1234567890")
    place, name = judge_panel.load_meta_key_from_user_environment()
    assert place == "environment" and name == "META_API_KEY"
    assert "not-a-real-key" not in "%s%s" % (place, name)


def test_a_meta_client_error_is_an_error_attempt_and_not_a_traceback(tmp_path, monkeypatch):
    import meta_client
    from PIL import Image

    frame = tmp_path / "frame.png"
    Image.new("RGB", (8, 8), (10, 10, 10)).save(frame)
    monkeypatch.setenv("PP_AI_BACKEND", "meta")
    monkeypatch.setenv("PP_EYE_LEDGER", str(tmp_path / "ledger.csv"))

    def boom(model, payload, timeout=None, sleep=None):
        raise meta_client.BadResponse("the Meta API answered 500: upstream said no")

    monkeypatch.setattr(eye_critic, "post_generate", boom)
    log = []
    frames = [{"index": 1, "at_s": 0.5, "path": str(frame), "blank": False}]
    gate = eye_critic.RateGate(path=str(tmp_path / "ledger.csv"), per_minute=0, per_day=0)
    with pytest.raises(judge_panel.PanelError) as caught:
        judge_panel.ask_panel(frames, INFO, SCRIPT, gate=gate, log=log)
    assert "muse-spark-1.3 error" in str(caught.value)
    assert any("error" in line for line in log)
