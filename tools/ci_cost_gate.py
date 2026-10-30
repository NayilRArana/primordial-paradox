r"""ci_cost_gate.py: the measurement CI has to pass before it may touch the Meta path (card t_fc0cb4d9).

What this gate is for
=====================
The nightly suite is the thing that would cost money if it ever reached the real Meta Model API: a
few hundred token-heavy calls is a few dollars, and a retry storm is a rate limit at the worst
moment. So the Meta door is not trusted to the test authors' memory. It is measured, per run, by
this gate, and the gate is cheap: no key, no account, no egress.

The six checks, each named in the output, and what fails it
==========================================================
1. FAKE UP              the loopback stand-in from tools\fake_meta.py answers GET /health.
2. FIVE KINDS           chat, vision, image, segment and transcribe each get an answer through the
                        real client (tools\meta_client.py, live mode, the real urllib transport).
3. PINNED ONLY          a request for a model other than the pinned spark / image / sam id is refused
                        with a 400 and the client raises. "spark-1.3 only" is measured, not restated.
4. NO EGRESS            a socket audit hook is armed for the whole driving phase: any connect,
                        getaddrinfo or sendto aimed anywhere but loopback raises, so a call that
                        slipped past the fake base URL fails the gate instead of spending credits.
5. NO PLAYER TEXT       a sentinel player line goes out on two kinds, and afterwards the fake's own
                        record, the cache directory, the ledger and this gate's report are searched
                        for it. One hit fails the gate.
6. SUITE GREEN          pytest runs tests\test_fake_meta_ci.py, tests\test_meta_client.py and
                        tests\test_ai_client.py with no Meta key in the environment, so a live call
                        in the suite refuses rather than spends. The cache is compared before and
                        after: a new `network: true` entry fails the gate.
7. COST                 0.000000 USD spent, and the counterfactual printed at the documented list
                        prices so the number is visible rather than assumed.

Exit codes: 0 every check passed, 1 a check failed (the failing line says which), 2 the gate could
not run at all (a missing interpreter or a port it could not bind).

Usage
=====
    python tools\ci_cost_gate.py                       # the gate, human readable
    python tools\ci_cost_gate.py --report X.json       # and write the evidence as JSON
    python tools\ci_cost_gate.py --skip-suite          # the driving checks only (about 2 seconds)
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import fake_meta  # noqa: E402  - the module under test is a sibling tool, by design

SENTINEL = "SENTINEL-PLAYER-LINE-7f3a the captain is a fool and you know it"
LOOPBACK = ("127.0.0.1", "::1", "localhost")
SUITE_FILES = ("tests/test_fake_meta_ci.py", "tests/test_meta_client.py", "tests/test_ai_client.py",
               "tests/test_ai_bridge.py", "tests/test_bake_meta.py")


class Egress(Exception):
    """A connection that was not loopback. Raised from the audit hook, so it stops the call."""


class EgressWatch(object):
    """Arms a socket audit hook that refuses everything but loopback, and counts what it saw."""

    def __init__(self):
        self.attempts = []
        self.installed = False

    def install(self):
        if self.installed:
            return self
        watch = self

        def allowed(host):
            if isinstance(host, bytes):
                host = host.decode("ascii", "replace")
            if not isinstance(host, str):
                return False
            return host.split(":")[0].strip("[]") in LOOPBACK

        def hook(event, args):
            if event == "socket.getaddrinfo":
                host = args[0] if args else None
                if not allowed(host):
                    watch.attempts.append({"event": event, "host": str(host)})
                    raise Egress("a DNS lookup for %r is not loopback, so CI would have spent money"
                                 % (host,))
                return
            if event in ("socket.connect", "socket.sendto"):
                address = args[1] if len(args) > 1 else None
                host = address[0] if isinstance(address, tuple) and address else address
                if not allowed(host):
                    watch.attempts.append({"event": event, "host": str(host)})
                    raise Egress("a %s to %r is not loopback, so CI would have spent money"
                                 % (event, host))
                return

        sys.addaudithook(hook)
        self.installed = True
        return self


def cache_network_entries():
    """How many entries in data\\ai_cache claim network true: the number the gate holds still."""
    folder = os.path.join(ROOT, "data", "ai_cache")
    if not os.path.isdir(folder):
        return 0
    count = 0
    for name in os.listdir(folder):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(folder, name), "r", encoding="utf-8") as handle:
                if json.load(handle).get("network"):
                    count += 1
        except (ValueError, OSError):
            continue
    return count


def files_under(folder):
    found = []
    for base, _dirs, names in os.walk(folder):
        for name in names:
            found.append(os.path.join(base, name))
    return found


def drive(fake, quick, results):
    """The five kinds, through the real client, with a sentinel player line on two of them."""
    import meta_client

    meta_client.reset_rate_state()
    results["chat"] = str(meta_client.chat([{"role": "user", "content": SENTINEL}],
                                           sleep=quick))[:80]
    results["vision"] = str(meta_client.vision(SENTINEL, fake_meta._png_probe(), sleep=quick))[:80]
    made = meta_client.generate_image("a flat knight in profile", size="16x16", sleep=quick)
    results["image"] = "%d b64 chars" % len(made.get("image_b64") or "")
    segment = meta_client.segment(fake_meta._png_probe(), "ship", sleep=quick)
    results["segment"] = "boxes=%r" % (segment.get("boxes"),)
    results["transcribe"] = str(meta_client.transcribe(fake_meta._wav_probe(),
                                                       sleep=quick).get("text"))[:80]
    return results


def refuse_pinned(fake, quick):
    """Ask for a model that is not pinned; the fake must say 400 and the client must raise."""
    import meta_client

    try:
        meta_client.chat([{"role": "user", "content": "anything"}], model="muse-spark-0.9",
                         sleep=quick)
    except meta_client.MetaError as exc:
        return "refused as asked: %s" % str(exc)[:90]
    return None


def run_suite(environment, timeout=900):
    command = [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"] \
        + list(SUITE_FILES)
    started = time.time()
    process = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True,
                             timeout=timeout, stdin=subprocess.DEVNULL)
    tail = [line for line in (process.stdout or "").strip().splitlines() if line.strip()]
    return {"command": " ".join(command[1:]), "returncode": process.returncode,
            "seconds": round(time.time() - started, 1),
            "tail": tail[-3:], "stderr_tail": (process.stderr or "").strip().splitlines()[-3:]}


def main(argv=None):
    parser = argparse.ArgumentParser(description="The fake-Meta CI cost gate (card t_fc0cb4d9).")
    parser.add_argument("--report", default=None, help="write the evidence as JSON here")
    parser.add_argument("--skip-suite", action="store_true", help="driving checks only")
    parser.add_argument("--suite-timeout", type=int, default=900)
    args = parser.parse_args(argv)

    checks = []

    def check(name, passed, detail):
        checks.append({"check": name, "pass": bool(passed), "detail": detail})
        print("%-16s %s  %s" % (name, "PASS" if passed else "FAIL", detail))
        return passed

    scratch = tempfile.mkdtemp(prefix="ci-cost-gate-")
    cache_dir = os.path.join(scratch, "ai_cache")
    ledger = os.path.join(scratch, "ai_ledger.jsonl")
    os.makedirs(cache_dir, exist_ok=True)

    keep = {name: os.environ.get(name) for name in
            ("META_API_BASE", "MODEL_API_KEY", "META_API_KEY", "PP_AI_BACKEND", "PP_AI_MODE",
             "PP_AI_CACHE", "PP_AI_LEDGER", "PP_META_MAX_RETRIES", "PP_META_RPM")}
    fake = None
    report = {"card": "t_fc0cb4d9", "checks": checks,
              "sentinel_sha256": fake_meta.digest_of(SENTINEL.encode("utf-8")),
              "sentinel_chars": len(SENTINEL)}
    try:
        try:
            fake = fake_meta.FakeMeta.start()
        except OSError as exc:
            print("ci_cost_gate: the fake could not bind loopback: %s" % exc)
            return 2
        watch = EgressWatch().install()
        os.environ.update({"META_API_BASE": fake.url,
                           "MODEL_API_KEY": "fake-ci-not-a-real-key",
                           "META_API_KEY": "",
                           "PP_AI_BACKEND": "meta",
                           "PP_AI_MODE": "live",
                           "PP_AI_CACHE": cache_dir,
                           "PP_AI_LEDGER": ledger,
                           "PP_META_MAX_RETRIES": "0",
                           "PP_META_RPM": "0"})
        quick = lambda seconds: None  # noqa: E731 - the gate must never sleep, it is measuring
        before_network = cache_network_entries()

        health = _health(fake.base)
        check("FAKE UP", bool(health and health.get("fake")),
              "GET /health at %s answered %r" % (fake.base, (health or {}).get("models")))

        answers = drive(fake, quick, {})
        answered = sorted(name for name, value in answers.items() if value)
        check("FIVE KINDS", len(answered) == 5, "answered: %s" % ", ".join(answered))

        refused = refuse_pinned(fake, quick)
        check("PINNED ONLY", refused is not None and fake.refusals,
              refused or "an unpinned model was answered, which would be a real-API shape drift")

        check("NO EGRESS", not watch.attempts,
              "audit hook saw %d non-loopback attempt(s)%s"
              % (len(watch.attempts), (": %r" % watch.attempts[0]) if watch.attempts else ""))

        report.update(fake.report())
        hits = find_sentinel(SENTINEL, [json.dumps(report), cache_dir, ledger,
                                        os.path.join(scratch, "gate.json")])
        check("NO PLAYER TEXT", hits == 0,
              "the sentinel appears in %d place(s) it must not" % hits if hits
              else "absent from the fake's record, the cache, the ledger and this report")

        if not args.skip_suite:
            # A clean Meta environment on purpose: no key, no base URL, no mode. A test that tried a
            # live call then refuses at api_key() instead of spending, and a test that asserts the
            # documented default base URL still sees the documented default. The fake's own address
            # is not handed to the suite either, because the suite starts its own (test_fake_meta_ci).
            environment = {name: value for name, value in os.environ.items()
                           if name not in ("META_API_BASE", "MODEL_API_KEY", "META_API_KEY",
                                           "PP_AI_MODE", "PP_AI_BACKEND", "PP_AI_CACHE",
                                           "PP_AI_LEDGER", "PP_META_RPM", "PP_META_MAX_RETRIES")}
            suite = run_suite(environment, timeout=args.suite_timeout)
            report["suite"] = suite
            after_network = cache_network_entries()
            check("SUITE GREEN", suite["returncode"] == 0 and after_network == before_network,
                  "%s in %ss, exit %d, network-true cache entries %d -> %d (%s)"
                  % (suite["command"], suite["seconds"], suite["returncode"], before_network,
                     after_network, " / ".join(suite["tail"])[:120]))

        spent = report["spent_usd"]
        check("COST", spent == 0.0,
              "spent %.6f USD on %d call(s); the same calls would have cost %.6f USD at list price"
              % (spent, report["requests"], report["would_have_cost_usd"]))
        report["passed"] = all(entry["pass"] for entry in checks)
    finally:
        if fake is not None:
            fake.stop()
        for name, value in keep.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    if args.report:
        with open(args.report, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print("report: %s" % args.report)
    failed = [entry["check"] for entry in checks if not entry["pass"]]
    print("CI COST GATE: %s (%s)"
          % ("PASS" if not failed else "FAIL", "all %d checks" % len(checks)
             if not failed else "failed: " + ", ".join(failed)))
    return 0 if not failed else 1


def _health(base):
    import urllib.request
    try:
        with urllib.request.urlopen("%s/health" % base, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 - a fake that cannot answer its own health check is a FAIL
        return None


def find_sentinel(needle, targets):
    """Count the places a string can be read out of: JSON blobs, files and whole directories."""
    hits = 0
    for target in targets:
        if not target:
            continue
        if isinstance(target, str) and target.startswith("{"):
            hits += target.count(needle)
            continue
        paths = files_under(target) if isinstance(target, str) and os.path.isdir(target) else \
            ([target] if isinstance(target, str) and os.path.exists(target) else [])
        for path in paths:
            try:
                with open(path, "rb") as handle:
                    blob = handle.read()
            except OSError:
                continue
            hits += blob.count(needle.encode("utf-8"))
    return hits


if __name__ == "__main__":
    sys.exit(main())
