#!/usr/bin/env python3
"""talk_scene_probe.py: the manual test for the scene chat's listen -> verdict path (card t_330b12ce).

It makes the same two calls the game makes, to the same local bridge, and prints the rows the NES box would draw:

    POST /talk   {"persona": "nye", "player_text": "my name is nayil", ...}
                 -> {"verdict", "will_delta", "reply": [...], "source", ...}
    POST /hear   a 16 kHz mono 16 bit wav -> {"transcript": "..."}

and then prints

    * NAYIL. N A Y I L.
    * NYE IS PERSUADED.

which is the answer row and the verdict row, in the box's own columns. Nothing here talks to anything but 127.0.0.1,
and the address is refused before a byte is sent if it is not a loopback literal.

Usage, from the repo root:

    python tools/talk_scene_probe.py                       # start a bridge, ask as Nye, stop it
    python tools/talk_scene_probe.py --line "percy sent me"
    python tools/talk_scene_probe.py --hear output/ai_bridge/selftest_speech.wav
    python tools/talk_scene_probe.py --no-start            # use a bridge that is already running
    python tools/talk_scene_probe.py --offline            # no network at all: print the visible fallback rows

Exit codes
    0  an answer came back and the rows are drawable (or, with --offline, the fallback rows are)
    2  the bridge was not reachable and was not started
    3  the bridge answered something the box would refuse
    4  a row is not drawable on the 8x8 sheet, so the box would print a hole
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import talk_scene_live as scene  # noqa: E402  (the mirror this probe renders with)

LOOPBACK = ("127.0.0.1", "localhost", "::1")


class ProbeError(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


def base_url(host, port):
    if (urlsplit("http://%s" % host).hostname or "").lower() not in LOOPBACK:
        raise ProbeError("host %r is not loopback: the player's words must not leave this machine" % host, 3)
    return "http://%s:%d" % (host, int(port))


def call(url, body, content_type, timeout):
    request = urlrequest.Request(url, data=body, headers={"Content-Type": content_type})
    try:
        with urlrequest.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urlerror.HTTPError as exc:
        return exc.code, exc.read()
    except OSError as exc:
        raise ProbeError("no answer from %s: %s" % (url, exc), 2)


def health(base, timeout=2.0):
    try:
        status, body = call(base + "/health", None, "application/json", timeout)
    except ProbeError:
        return None
    if status != 200:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except ValueError:
        return None


def wait_health(base, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        report = health(base)
        if report and report.get("ok"):
            return report
        time.sleep(0.25)
    return None


def start_bridge(port):
    """A bridge this script owns and stops in its finally block. Never detached, never left running."""
    env = dict(os.environ)
    env["PP_BRIDGE_PORT"] = str(int(port))
    env.setdefault("TEMP", os.path.join(ROOT, "cache"))
    env.setdefault("TMP", env["TEMP"])
    return subprocess.Popen([sys.executable, os.path.join(HERE, "ai_bridge.py"), "--serve"],
                            cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def stop_bridge(proc):
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def read_wav(path):
    with open(path, "rb") as handle:
        return handle.read()


def print_rows(rows, alphabet):
    for row in rows:
        mark = "ok " if scene.drawable(row, alphabet) else "NO "
        print("  %s %s" % (mark, row))


def main(argv=None):
    data = scene.load(ROOT)
    bridge = data["doc"].get("bridge") or {}
    parser = argparse.ArgumentParser(description="Ask the local bridge as the S5 dock clerk and print the box's rows")
    parser.add_argument("--line", default="my name is nayil", help="the player's line (default: my name is nayil)")
    parser.add_argument("--npc", default="nye", help="the persona id the scene asks as (default: nye)")
    parser.add_argument("--plate", default="NYE", help="the name plate the box draws (default: NYE)")
    parser.add_argument("--host", default=bridge.get("host", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(bridge.get("port", 8791)))
    parser.add_argument("--timeout", type=float, default=20.0, help="seconds for one whole request")
    parser.add_argument("--hear", default="", help="a wav to transcribe through /hear as well")
    parser.add_argument("--no-start", action="store_true", help="do not start a bridge if none is running")
    parser.add_argument("--offline", action="store_true", help="no network: print the visible fallback rows")
    parser.add_argument("--verbose", action="store_true", help="print the whole answer document, rungs and repairs")
    args = parser.parse_args(argv)

    alphabet = scene.glyphs(ROOT)

    if args.offline:
        answer = scene.fallback(data, alphabet)
        print("offline fallback, the rows a dead bridge draws:")
        print_rows(scene.render(args.plate, answer, data, alphabet), alphabet)
        print("  note: %s" % answer["note"])
        return 0

    try:
        base = base_url(args.host, args.port)
    except ProbeError as exc:
        print("PROBE FAIL: %s" % exc)
        return exc.code

    proc = None
    try:
        report = health(base)
        if report is None:
            if args.no_start:
                raise ProbeError("no bridge on %s (start it with: python tools\\ai_bridge.py --serve)" % base, 2)
            print("no bridge on %s, starting one for this probe" % base)
            proc = start_bridge(args.port)
            report = wait_health(base, 30.0)
            if report is None:
                raise ProbeError("the bridge did not answer /health within 30 s", 2)
        print("bridge ok: local model %s, key present %s, sources %s"
              % ((report.get("local") or {}).get("model", "?"),
                 (report.get("meta") or {}).get("key_present"),
                 ",".join(report.get("sources") or [])))

        body = json.dumps(scene.request_body(args.npc, args.line)).encode("utf-8")
        started = time.monotonic()
        status, raw = call(base + str(bridge.get("talk_path", "/talk")), body, "application/json", args.timeout)
        elapsed = time.monotonic() - started
        if status != 200:
            raise ProbeError("/talk answered HTTP %d: %s" % (status, raw[:300]), 3)
        try:
            answer_doc = json.loads(raw.decode("utf-8"))
        except ValueError as exc:
            raise ProbeError("/talk answer is not JSON: %s" % exc, 3)
        answer = scene.clean_answer(answer_doc, data, alphabet)
        if args.verbose:
            print(json.dumps(answer_doc, indent=2, ensure_ascii=True))
        if answer is None:
            raise ProbeError("the box would refuse this answer: %s" % raw[:300], 3)
        print("answer in %.2f s: source %s, verdict %s, delta %s"
              % (elapsed, answer_doc.get("source", answer["source"]), answer["verdict"],
                 answer_doc.get("will_delta")))
        print("the box draws:")
        rows = scene.render(args.plate, answer, data, alphabet)
        print_rows(rows, alphabet)

        if args.hear:
            wav = read_wav(args.hear)
            started = time.monotonic()
            status, raw = call(base + str(bridge.get("hear_path", "/hear")), wav, "audio/wav", args.timeout)
            elapsed = time.monotonic() - started
            if status != 200:
                raise ProbeError("/hear answered HTTP %d: %s" % (status, raw[:300]), 3)
            heard = json.loads(raw.decode("utf-8"))
            transcript = scene.scrub(heard.get("transcript", ""), data, alphabet)
            print("/hear in %.2f s: %r" % (elapsed, transcript))
            if not transcript:
                raise ProbeError("the transcriber returned no drawable transcript", 3)
            print("the box fills with: %s" % transcript)

        bad = [row for row in scene.render(args.plate, answer, data, alphabet) if not scene.drawable(row, alphabet)]
        if bad:
            raise ProbeError("%d row(s) are not drawable on the sheet: %r" % (len(bad), bad), 4)
        print("PROBE PASS")
        return 0
    except ProbeError as exc:
        print("PROBE FAIL: %s" % exc)
        return exc.code
    finally:
        stop_bridge(proc)


if __name__ == "__main__":
    raise SystemExit(main())
