"""The fake Meta door: a loopback server the suite can drive without spending credits (card t_fc0cb4d9).

Why a server and not another fake transport
===========================================
`tests/test_meta_client.py` already drives the client through a `FakeTransport`, which is the right
seam for the request shapes. It stops one layer short of the wire: the urllib transport, its headers,
the timeout, the response decoding and the retry policy are exercised only by a live call. A live
call costs credits and can be rate limited, and CI must never do either. So these tests start
`tools/fake_meta.py` on 127.0.0.1, point the real client at it, and measure what crossed the socket.

What is measured here
=====================
* the fake refuses to bind anything but loopback, so a harness cannot publish it;
* five kinds get an answer through the real client, and the fake's own record shows five requests
  and a spend of exactly 0.000000 USD;
* a model that is not pinned is refused with a 400 and the client raises, which is what "spark-1.3
  only" means on the wire;
* the answer never repeats the request text, and neither does the fake's record: a sentinel player
  line goes out on a chat and a vision call and is searched for afterwards;
* the egress guard, run in a child process so a passing test never leaves a hook armed in the
  suite, refuses a non-loopback connect;
* `tools/ci_cost_gate.py --skip-suite` exits 0, so the gate itself is measured and not just written.

The environment is always restored: a test that leaks MODEL_API_KEY or META_API_BASE would change
what every later test in the same process believes about the network.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import fake_meta  # noqa: E402
import meta_client  # noqa: E402

SENTINEL = "the captain is a fool and you know it"


def quick(_seconds):
    """The rate gate's sleep, replaced: the gate is measuring calls, not pacing them."""
    return None


@pytest.fixture()
def fake(monkeypatch, tmp_path):
    """A running fake, with the client's environment pointed at it and restored afterwards."""
    server = fake_meta.FakeMeta.start()
    monkeypatch.setenv("META_API_BASE", server.url)
    monkeypatch.setenv("MODEL_API_KEY", "fake-ci-not-a-real-key")
    monkeypatch.delenv("META_API_KEY", raising=False)
    monkeypatch.setenv("PP_AI_BACKEND", "meta")
    monkeypatch.setenv("PP_AI_MODE", "live")
    monkeypatch.setenv("PP_AI_CACHE", str(tmp_path / "ai_cache"))
    monkeypatch.setenv("PP_META_MAX_RETRIES", "0")
    monkeypatch.setenv("PP_META_RPM", "0")
    meta_client.reset_rate_state()
    try:
        yield server
    finally:
        server.stop()
        meta_client.reset_rate_state()


def test_the_fake_refuses_to_bind_anything_but_loopback():
    with pytest.raises(ValueError) as caught:
        fake_meta.FakeMeta(("0.0.0.0", 0))
    assert "loopback only" in str(caught.value), (
        "a fake API that can bind a routable address is a fake API that could be published")


def test_five_kinds_answer_through_the_real_client_and_cost_nothing(fake, tmp_path):
    chat = meta_client.chat([{"role": "user", "content": SENTINEL}], sleep=quick)
    assert chat.startswith("FAKE META"), chat
    vision = meta_client.vision(SENTINEL, fake_meta._png_probe(), sleep=quick)
    assert vision.startswith("FAKE META"), vision
    image = meta_client.generate_image("a flat knight", size="16x16", sleep=quick)
    assert image.get("image_b64"), "the image answer carried no bytes"
    segment = meta_client.segment(fake_meta._png_probe(), "ship", sleep=quick)
    assert segment.get("boxes") == [[8, 8, 24, 24]], segment
    transcript = meta_client.transcribe(fake_meta._wav_probe(), sleep=quick)
    assert transcript.get("text") == "hold the line, sailor.", transcript

    report = fake.report()
    assert report["requests"] == 5, report
    assert report["spent_usd"] == 0.0, "the fake is not allowed to claim a cost it did not incur"
    assert report["would_have_cost_usd"] > 0, (
        "the counterfactual is printed, so zero spend is a measured number and not a blank field")
    assert report["live_requests_off_loopback"] == 0
    assert set(report["models"]) == {"muse-spark-1.3", "muse-image-1.0", "sam-3.1",
                                     "muse-voice-transcribe-1.0"}, report["models"]
    assert (tmp_path / "ai_cache").exists() is False or not list((tmp_path / "ai_cache").iterdir()), \
        "live mode must not write a cache entry for a call that cost nothing"


def test_a_model_that_is_not_pinned_is_refused_and_the_client_raises(fake):
    with pytest.raises(meta_client.MetaError) as caught:
        meta_client.chat([{"role": "user", "content": "anything"}], model="muse-spark-0.9",
                         sleep=quick)
    assert "not pinned" in str(caught.value), str(caught.value)
    assert fake.refusals and fake.refusals[0]["model"] == "muse-spark-0.9", fake.refusals
    assert fake.report()["requests"] == 0, "a refused request must not be counted as an answer"


def test_neither_the_answer_nor_the_record_repeats_the_player_line(fake):
    answer = meta_client.chat([{"role": "user", "content": SENTINEL}], sleep=quick)
    assert SENTINEL not in answer, "the answer echoed a player's line back"
    blob = json.dumps(fake.report(), sort_keys=True)
    assert SENTINEL not in blob, "the fake's record holds the player's line"
    assert SENTINEL not in "".join(str(value) for record in fake.report()["records"]
                                   for value in record.values())
    # What it does hold is a digest and a length, which is what makes replay and dedupe possible
    # without keeping the text.
    record = fake.report()["records"][0]
    assert len(record["body_sha256"]) == 64 and record["body_bytes"] > len(SENTINEL)
    assert sorted(record) == sorted(["at", "path", "kind", "model", "status", "body_sha256",
                                     "body_bytes", "prompt_tokens", "output_tokens",
                                     "answer_b64_chars"]), (
        "the record gained a field; if it can hold the request text it has to be named here first")


def test_the_egress_guard_refuses_a_non_loopback_connect_in_a_child_process():
    """A child process, so this never leaves a hook armed in the suite it runs inside."""
    probe = os.path.join(os.environ.get("TMPDIR") or ROOT, "egress_probe.py")
    with open(probe, "w", encoding="utf-8") as handle:
        handle.write(
            "import socket, sys\n"
            "sys.path.insert(0, %r)\n"
            "import ci_cost_gate\n"
            "ci_cost_gate.EgressWatch().install()\n"
            "try:\n"
            "    socket.create_connection(('93.184.216.34', 80), timeout=1)\n"
            "except ci_cost_gate.Egress:\n"
            "    print('refused')\n"
            "else:\n"
            "    print('connected')\n" % TOOLS)
    result = subprocess.run([sys.executable, probe], capture_output=True, text=True, timeout=60,
                            stdin=subprocess.DEVNULL)
    assert result.returncode == 0, result.stderr[-400:]
    assert result.stdout.strip() == "refused", result.stdout


def test_the_gate_itself_passes_its_driving_checks():
    report = os.path.join(os.environ.get("TMPDIR") or ROOT, "ci_cost_gate_selftest.json")
    result = subprocess.run([sys.executable, os.path.join(TOOLS, "ci_cost_gate.py"),
                             "--skip-suite", "--report", report],
                            capture_output=True, text=True, timeout=300, cwd=ROOT,
                            stdin=subprocess.DEVNULL)
    assert result.returncode == 0, (result.stdout or "")[-1200:] + (result.stderr or "")[-600:]
    assert "CI COST GATE: PASS" in result.stdout, result.stdout[-600:]
    with open(report, "r", encoding="utf-8") as handle:
        evidence = json.load(handle)
    assert evidence["spent_usd"] == 0.0 and evidence["requests"] == 5, evidence
