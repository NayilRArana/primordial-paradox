r"""fake_meta.py: a Meta Model API stand-in that CI can run against for $0.000000 (card t_fc0cb4d9).

Why this exists
===============
`tools/meta_client.py` is honest about needing a key for a live call, and the suite already runs it
on a `FakeTransport` and on the mock backend. Neither exercises the real HTTP door: the header, the
rate gate, the retry policy, the response shapes and the cache policy. The only way to exercise them
without spending credits is a server, so this is one, on loopback, with no account behind it.

What it answers, and what it refuses
====================================
Four routes, the four `_live_call()` uses: POST /v1/chat/completions, /v1/images/generations,
/v1/images/edits and /v1/responses (segment and transcribe). Each answer is deterministic in the
request body, so a rerun returns the same bytes and a diff means something changed.

Three refusals, and none of them is a skip:

1. NOT LOOPBACK, NOT STARTED. The server binds 127.0.0.1 only. Handed any other host it raises
   before the socket exists, so a CI harness can never accidentally publish a fake API.
2. MODEL NOT PINNED, 400. The card is "spark-1.3 only", so a request is answered only when its
   model is the id `tools/meta_client.py` pins for that kind (muse-spark-1.3 chat and vision,
   muse-image-1.0 image and edit, sam-3.1 segment, muse-voice-transcribe-1.0 transcribe). Any other
   id is refused with a named 400, and the gate records it.
3. NO ANSWER ECHOES THE PROMPT. The answer carries the request's sha256 and its length, never the
   request text. A player's typed line goes to the fake server in the request body and comes back
   nowhere, so a test can search the whole log for it and find nothing.

What it records, and what it deliberately does not
=================================================
One record per request: when, route, kind, model, status, the sha256 of the body, the body's byte
length, and the fake token counts it answered with. There is no field for the body, and no record
is written anywhere the request text could be reconstructed from. `--report` writes those records as
JSON, which is the evidence a cost harness prices.

The fake token counts are the request's byte length divided by four and the answer's by four: they
are arithmetic over the request, not a model's usage, and every priced figure derived from them is
labelled `would_have_cost_usd` because this server spent nothing. Credits are not a thing it can
spend: there is no key, no account and no route off the host.

Usage
=====
    python tools\fake_meta.py --serve                 # 127.0.0.1:0, prints the URL, answers until Ctrl-C
    python tools\fake_meta.py --serve --port 7071     # a fixed port, for a client that needs one
    python tools\fake_meta.py --selftest              # drive tools\meta_client.py through it, print the report
    python tools\fake_meta.py --selftest --report X.json

The selftest is the measurement the card asks for: five calls through the real client, the fake
server's own record of them, and a printed spend of 0.000000 USD.
"""
import argparse
import hashlib
import json
import os
import struct
import sys
import threading
import time
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOOPBACK = ("127.0.0.1", "::1", "localhost")

# The ids tools/meta_client.py pins per role. A request for anything else is refused, which is what
# "spark-1.3 only" means on the wire.
PINNED = {
    "chat": "muse-spark-1.3",
    "vision": "muse-spark-1.3",
    "image": "muse-image-1.0",
    "edit": "muse-image-1.0",
    "segment": "sam-3.1",
    "transcribe": "muse-voice-transcribe-1.0",
}

# The documented list prices tools/meta_spend_ledger.py already uses, so a counterfactual here and a
# measured figure there are the same arithmetic over the same table.
FRESH_IN = 1.25 / 1_000_000
CACHED_IN = 0.15 / 1_000_000
OUTPUT = 4.25 / 1_000_000
PER_IMAGE = 0.01
PER_SEGMENT = 0.0025

ROUTES = {
    "/v1/chat/completions": "chat",
    "/v1/images/generations": "image",
    "/v1/images/edits": "edit",
    "/v1/responses": "responses",
}

MAX_BODY = 16 * 1024 * 1024


def short(text, limit=120):
    return str(text or "")[:limit]


def digest_of(raw):
    return hashlib.sha256(raw or b"").hexdigest()


def prompt_estimate(payload):
    """Bytes of the request with its big blobs (an inline image or audio) replaced by their size.

    A data URL is not prompt text, so counting its base64 as tokens would price a fake call at
    roughly the image's size. This keeps the counterfactual close to what the same call would ask a
    real server for, and it never keeps the blob itself.
    """

    def shrink(value):
        if isinstance(value, str) and len(value) > 512:
            return "<%d chars>" % len(value)
        if isinstance(value, dict):
            return {key: shrink(sub) for key, sub in value.items()}
        if isinstance(value, list):
            return [shrink(sub) for sub in value]
        return value

    return json.dumps(shrink(payload), sort_keys=True).encode("utf-8")


def tokens_for(raw):
    """A fake but deterministic token count: four bytes to a token, rounded up."""
    return (len(raw or b"") + 3) // 4


def png_bytes(width, height, rgb=(15, 15, 15)):
    """A tiny valid PNG, so an image answer is real bytes and not a placeholder string."""
    raw = bytearray()
    row = bytes(rgb) * width
    for _ in range(height):
        raw += b"\x00" + row

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def schema_instance(schema, depth=0):
    """A minimal deterministic instance of a JSON schema, so a structured call gets an object back."""
    if not isinstance(schema, dict) or depth > 8:
        return "fake"
    if schema.get("enum"):
        return schema["enum"][0]
    kind = schema.get("type")
    if kind == "object" or "properties" in schema:
        return {name: schema_instance(sub, depth + 1)
                for name, sub in (schema.get("properties") or {}).items()}
    if kind == "array":
        return [schema_instance(schema.get("items") or {}, depth + 1)]
    if kind == "integer":
        return 0
    if kind == "number":
        return 0.0
    if kind == "boolean":
        return False
    if kind == "null":
        return None
    return "fake"


def kind_for(path, payload):
    """The kind a route means: /responses is segment or transcribe, and the payload says which.

    Both carry a `metadata` block, so the block's own keys decide it: an audio_format (or an
    input_audio content part) is a transcription, and a mask_encoding is a segmentation. Neither
    answer is guessed from the request text. (A first cut searched the raw JSON for the word
    "audio", which the image data URL can contain by chance; that misread a segment as a
    transcribe and the fake refused its own model, measured on 2026-10-29.)
    """
    route = ROUTES.get(path)
    if route != "responses":
        return route
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    if "audio_format" in metadata or "audio_bytes" in metadata:
        return "transcribe"
    for item in payload.get("input") or []:
        for part in (item or {}).get("content") or []:
            if isinstance(part, dict) and part.get("type") in ("input_audio", "audio"):
                return "transcribe"
    return "segment"


class Record(object):
    """One answered request, with no field that can hold the request text."""

    fields = ("at", "path", "kind", "model", "status", "body_sha256", "body_bytes",
              "prompt_tokens", "output_tokens", "answer_b64_chars")

    def __init__(self, **values):
        for name in self.fields:
            setattr(self, name, values.get(name))

    def as_dict(self):
        return {name: getattr(self, name) for name in self.fields}

    def usd(self):
        """What this call would have cost on the real API, at the documented list prices."""
        if self.kind in ("image", "edit"):
            return PER_IMAGE
        if self.kind == "segment":
            return PER_SEGMENT
        return ((self.prompt_tokens or 0) * FRESH_IN + (self.output_tokens or 0) * OUTPUT)


class FakeMeta(ThreadingHTTPServer):
    """The server. Use `with FakeMeta.start() as fake:` and read `fake.records` afterwards."""

    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address=("127.0.0.1", 0)):
        if str(address[0]) not in LOOPBACK:
            raise ValueError("the fake Meta API binds loopback only, and %r is not loopback"
                             % (address[0],))
        self.records = []
        self.refusals = []
        self.started_at = time.time()
        super().__init__(address, FakeMetaHandler)

    @classmethod
    def start(cls, port=0):
        fake = cls(("127.0.0.1", int(port)))
        thread = threading.Thread(target=fake.serve_forever, kwargs={"poll_interval": 0.05})
        thread.daemon = True
        thread.start()
        fake.thread = thread
        return fake

    # -- lifecycle

    def __enter__(self):
        if not getattr(self, "thread", None):
            thread = threading.Thread(target=self.serve_forever, kwargs={"poll_interval": 0.05})
            thread.daemon = True
            thread.start()
            self.thread = thread
        return self

    def __exit__(self, *exc_info):
        self.stop()

    def stop(self):
        """Stop the server. A server that never started has nothing to stop, and says so."""
        stopped = []
        try:
            self.shutdown()
            stopped.append("shutdown")
        except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
            stopped.append("shutdown refused: %s" % exc.__class__.__name__)
        try:
            self.server_close()
            stopped.append("closed")
        except Exception as exc:  # noqa: BLE001
            stopped.append("close refused: %s" % exc.__class__.__name__)
        self.stop_report = stopped
        return False

    # -- what it saw

    @property
    def url(self):
        host, port = self.server_address[:2]
        return "http://%s:%d/v1" % (host, port)

    @property
    def base(self):
        host, port = self.server_address[:2]
        return "http://%s:%d" % (host, port)

    def note(self, record):
        self.records.append(record)

    def refuse(self, path, model, reason):
        self.refusals.append({"path": path, "model": model, "reason": reason,
                              "at": time.time()})
        return self.refusals[-1]

    def report(self):
        by_model = {}
        for record in self.records:
            bucket = by_model.setdefault(record.model, {"calls": 0, "prompt_tokens": 0,
                                                        "output_tokens": 0, "usd": 0.0})
            bucket["calls"] += 1
            bucket["prompt_tokens"] += record.prompt_tokens or 0
            bucket["output_tokens"] += record.output_tokens or 0
            bucket["usd"] += record.usd()
        would = sum(record.usd() for record in self.records)
        return {
            "url": self.url,
            "requests": len(self.records),
            "refused": len(self.refusals),
            "kinds": sorted({record.kind for record in self.records}),
            "models": sorted({record.model for record in self.records}),
            "by_model": by_model,
            # Two different numbers, both true: nothing was spent here, and this is what the same
            # calls would have cost on the documented list prices.
            "spent_usd": 0.0,
            "would_have_cost_usd": round(would, 8),
            "live_requests_off_loopback": 0,
            "records": [record.as_dict() for record in self.records],
            "refusals": self.refusals,
        }

    def text_hits(self, needle):
        """How many records hold this string anywhere. The record has no text field, so it is 0."""
        blob = json.dumps(self.report(), sort_keys=True)
        return blob.count(str(needle)) if needle else 0


class FakeMetaHandler(BaseHTTPRequestHandler):
    server_version = "FakeMeta/1.0 (no credits, no account, loopback only)"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        # The default writes the client address to stderr. Nothing here logs a body, ever.
        sys.stderr.write("fake_meta %s\n" % (fmt % args))

    def _send(self, status, payload):
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError) as exc:
            # The client went away mid answer. Counted on the server, so a run of them is visible
            # instead of vanishing.
            self.server.interrupted = getattr(self.server, "interrupted", 0) + 1
            _ = exc
        self.close_connection = True

    def do_GET(self):
        route = self.path.split("?")[0]
        if route in ("/", "/health"):
            report = self.server.report()
            self._send(200, {"ok": True, "fake": True, "url": report["url"],
                             "requests": report["requests"], "spent_usd": 0.0,
                             "models": sorted(set(PINNED.values()))})
            return
        self._send(404, {"error": "no route %r (GET /health)" % route})

    def do_POST(self):
        route = self.path.split("?")[0]
        started = time.monotonic()
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY:
            self._send(400, {"error": "a body of %d bytes is not acceptable" % length})
            return
        raw = self.rfile.read(length)
        if route not in ROUTES:
            self._send(404, {"error": "no route %r (POST %s)" % (route, ", ".join(sorted(ROUTES)))})
            return
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._send(400, {"error": "the body is not JSON"})
            return
        if not isinstance(payload, dict):
            self._send(400, {"error": "the body is not a JSON object"})
            return
        kind = kind_for(route, payload)
        model = str(payload.get("model") or "")
        pinned = PINNED.get(kind)
        if pinned is None:
            self._send(400, {"error": "no pinned model for kind %r" % kind})
            return
        if model != pinned:
            self.server.refuse(route, model, "model is not pinned for %s (want %s)" % (kind, pinned))
            self._send(400, {"error": {"message": "model %r is not pinned for %s; this fake answers "
                                                  "%r only (card t_fc0cb4d9: spark-1.3 only)"
                                                  % (model, kind, pinned),
                                       "type": "fake_meta_model_not_pinned"}})
            return
        answer, prompt_tokens, output_tokens, b64_chars = self._answer(kind, raw, payload)
        self.server.note(Record(at=time.time(), path=route, kind=kind, model=model, status=200,
                                body_sha256=digest_of(raw), body_bytes=len(raw),
                                prompt_tokens=prompt_tokens, output_tokens=output_tokens,
                                answer_b64_chars=b64_chars))
        self._send(200, answer)
        _ = started

    def _answer(self, kind, raw, payload):
        """The answer for one call. Deterministic in the body, and it never repeats the body."""
        tag = digest_of(raw)[:12]
        prompt_tokens = tokens_for(prompt_estimate(payload))
        if kind in ("chat", "vision"):
            schema = ((payload.get("response_format") or {}).get("json_schema") or {}).get("schema")
            if schema:
                text = json.dumps(schema_instance(schema), sort_keys=True)
            else:
                text = ("FAKE META %s: a canned %s answer, no credits spent, and the request's "
                        "%d bytes are not repeated here." % (tag, kind, len(raw)))
            answer = {
                "id": "fake-%s" % tag,
                "object": "chat.completion",
                "model": str(payload.get("model") or ""),
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": text}}],
                "usage": {"prompt_tokens": prompt_tokens,
                          "completion_tokens": tokens_for(text.encode("utf-8")),
                          "total_tokens": prompt_tokens + tokens_for(text.encode("utf-8"))},
                "fake": True,
            }
            return answer, prompt_tokens, tokens_for(text.encode("utf-8")), 0
        if kind in ("image", "edit"):
            png = png_bytes(8, 8)
            import base64
            b64 = base64.b64encode(png).decode("ascii")
            answer = {"created": int(time.time()), "output_format": "png",
                      "data": [{"b64_json": b64, "revised_prompt": None}],
                      "usage": {"images": 1}, "fake": True}
            return answer, 0, 0, len(b64)
        if kind == "segment":
            boxes = [[8, 8, 24, 24]]
            answer = {"id": "fake-sam-%s" % tag, "object": "response",
                      "output_text": "fake segmentation: one box, no player text",
                      "output": [{"type": "message",
                                  "content": [{"type": "output_text",
                                               "text": "fake segmentation: one box, no player text"}]}],
                      "boxes": boxes,
                      "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": 8},
                      "fake": True}
            return answer, prompt_tokens, 8, 0
        answer = {"id": "fake-transcribe-%s" % tag, "object": "response",
                  "output_text": "hold the line, sailor.",
                  "output": [{"type": "message",
                              "content": [{"type": "output_text", "text": "hold the line, sailor."}]}],
                  "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": 6},
                  "fake": True}
        return answer, prompt_tokens, 6, 0


# ---------------------------------------------------------------- the selftest

def selftest(report_path=None, out=sys.stdout):
    """Drive the real client through the fake server once per kind, and price what it did."""
    import meta_client

    result = {"fake": True, "spent_usd": 0.0}
    environment = {
        "META_API_BASE": None, "MODEL_API_KEY": "fake-ci-not-a-real-key",
        "META_API_KEY": "", "PP_AI_BACKEND": "meta", "PP_AI_MODE": "live",
        "PP_AI_CACHE": os.path.join(os.environ.get("TMPDIR") or os.path.abspath("."),
                                    "fake_meta_selftest_cache"),
        "PP_META_MAX_RETRIES": "0", "PP_META_RPM": "0",
    }
    previous = {name: os.environ.get(name) for name in environment}
    fake = FakeMeta.start()
    try:
        os.environ.update({name: value for name, value in environment.items() if value is not None})
        os.environ["META_API_BASE"] = fake.url
        meta_client.reset_rate_state()
        quick = lambda seconds: None  # noqa: E731 - the rate gate must not sleep in a selftest
        answers = {}
        answers["chat"] = meta_client.chat([{"role": "user", "content": "hold the line"}],
                                           sleep=quick)[:60]
        answers["vision"] = meta_client.vision("what colour is this?", _png_probe(),
                                              sleep=quick)[:60]
        made = meta_client.generate_image("a flat knight", size="16x16", sleep=quick)
        answers["image"] = "%d bytes" % len(made.get("image_b64") or "")
        segment = meta_client.segment(_png_probe(), "ship", sleep=quick)
        answers["segment"] = "boxes=%r" % (segment.get("boxes"),)
        answers["transcribe"] = str(meta_client.transcribe(_wav_probe(), sleep=quick).get("text"))[:60]
        result["answers"] = answers
        result["report"] = fake.report()
    finally:
        fake.stop()
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    report = result["report"]
    lines = [
        "FAKE META: %d request(s), %d refused, spent 0.000000 USD, would-have-cost %.6f USD"
        % (report["requests"], report["refused"], report["would_have_cost_usd"]),
        "models answered: %s" % (", ".join(report["models"]) or "none"),
        "kinds answered: %s" % (", ".join(kinds_of(report)) or "none"),
    ]
    for name in ("chat", "vision", "image", "segment", "transcribe"):
        lines.append("  %-10s %s" % (name, answers.get(name, "(not answered)")))
    text = "\n".join(lines)
    out.write(text + "\n")
    if report_path:
        with open(report_path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
            handle.write("\n")
    return 0 if report["requests"] >= 5 and not report["refused"] else 1


def kinds_of(report):
    return sorted({record["kind"] for record in report["records"]})


def _scratch(name):
    folder = os.environ.get("TMPDIR") or os.path.abspath(".")
    return os.path.join(folder, name)


def _png_probe():
    path = _scratch("fake_meta_probe.png")
    with open(path, "wb") as handle:
        handle.write(png_bytes(16, 16))
    return path


def _wav_probe():
    path = _scratch("fake_meta_probe.wav")
    with open(path, "wb") as handle:
        handle.write(b"RIFF" + struct.pack("<I", 36) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1,
                    16000, 32000, 2, 16) + b"data" + struct.pack("<I", 0))
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description="A fake Meta Model API on loopback, for no credits.")
    parser.add_argument("--serve", action="store_true", help="run the server until Ctrl-C")
    parser.add_argument("--selftest", action="store_true", help="drive the real client through it")
    parser.add_argument("--port", type=int, default=0, help="port for --serve (0 picks a free one)")
    parser.add_argument("--report", default=None, help="write the record JSON here")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest(report_path=args.report)
    if args.serve:
        fake = FakeMeta.start(port=args.port)
        sys.stdout.write("fake_meta listening on %s (loopback only, 0.000000 USD)\n" % fake.url)
        sys.stdout.flush()
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            sys.stdout.write("fake_meta stopping on Ctrl-C\n")
            sys.stdout.flush()
        finally:
            report = fake.report()
            fake.stop()
            if args.report:
                with open(args.report, "w", encoding="utf-8", newline="\n") as handle:
                    json.dump(report, handle, indent=2, sort_keys=True)
                    handle.write("\n")
            sys.stdout.write("fake_meta answered %d request(s), spent 0.000000 USD\n"
                             % report["requests"])
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
