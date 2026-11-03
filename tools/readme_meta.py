#!/usr/bin/env python3
"""readme_meta.py: every README in this project is written by a Meta model, and this tool is the gate that proves it.

Why: the author wants the front pages to read like a person wrote them (the model that the project is built to showcase), not like the
house style of the coding assistants that wrote the code. So a README may only change through this tool.

  python tools/readme_meta.py rewrite README.md      send each section to muse-spark-1.3 (Meta Model API), keep every fact, stamp the file
  python tools/readme_meta.py check README.md ...    exit 1 unless each file's stamp matches its text (used by the tests and the git hook)
  python tools/readme_meta.py hash README.md         print the body hash

The stamp is the last line: <!-- readme-author: muse-spark-1.3 body-sha256: HEX -->. Any hand edit changes the body hash and fails the check.
Rewrite keeps numbers, backticked names, URLs, code fences and table rows (validated per section; a section the model garbles keeps its text).
The key is read from META_API_KEY at call time and never printed.
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("META_API_BASE", "https://api.meta.ai/v1").rstrip("/")
MODEL = os.environ.get("README_META_MODEL", "muse-spark-1.3")
STAMP_RX = re.compile(r"\n*<!-- readme-author: (\S+) body-sha256: ([0-9a-f]{64}) -->\s*$")
SYSTEM = ("You are a clear technical writer preparing a hackathon project page for judges and curious readers. Rewrite the Markdown you are given so it is easy for a human to read: "
          "plain direct English, short paragraphs (three sentences at most), concrete verbs, short bullet lists where natural, explain jargon in half a sentence, no hype words, keep the author's honest voice. "
          "HARD RULES: keep EVERY fact, number, date, file path, URL, command, code block and table row exactly as given (you may tighten the words around them). Keep any heading line unchanged. "
          "Add no new claims and no new numbers. Never use an em dash or an en dash; use commas, colons or periods. Output only the rewritten Markdown.")
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
TICK = re.compile(r"`[^`\n]+`")
URL = re.compile(r"https?://[^\s)>\]]+")


def split_stamp(text):
    m = STAMP_RX.search(text)
    if not m:
        return text, None, None
    return text[:m.start()], m.group(1), m.group(2)


def body_hash(body):
    return hashlib.sha256(body.rstrip("\n").replace("\r\n", "\n").encode("utf-8")).hexdigest()


def check_file(path):
    text = open(path, encoding="utf-8").read()
    body, author, digest = split_stamp(text)
    if digest is None:
        return "no readme-author stamp: run tools/readme_meta.py rewrite %s" % path
    if not author.startswith(("muse-", "llama", "meta-")):
        return "the stamp names %s, which is not a Meta model" % author
    if body_hash(body) != digest:
        return "the text changed after the Meta model wrote it (stamp does not match): run tools/readme_meta.py rewrite %s" % path
    return ""


def call(text, extra=""):
    key = os.environ.get("META_API_KEY", "")
    if not key:
        raise SystemExit("META_API_KEY is not set in this environment")
    body = json.dumps({"model": MODEL, "temperature": 0.2, "max_tokens": 4000,
                       "messages": [{"role": "system", "content": SYSTEM + extra}, {"role": "user", "content": text}]}).encode("utf-8")
    req = urllib.request.Request(BASE + "/chat/completions", data=body, headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503):
                time.sleep(6 * (attempt + 1)); continue
            raise SystemExit("HTTP %s from the Meta API" % e.code)
        except Exception:
            time.sleep(5)
    return None


def missing(orig, new):
    return [t for rx in (NUM, TICK, URL) for t in set(rx.findall(orig)) if t not in new]


def valid(orig, new):
    if not new:
        return False, ["no answer"]
    bad = missing(orig, new)
    if re.search("[" + chr(0x2013) + chr(0x2014) + "]", new):
        bad.append("dash")
    if orig.count("\n|") and new.count("\n|") < orig.count("\n|"):
        bad.append("table rows lost")
    if orig.count("```") != new.count("```"):
        bad.append("code fences")
    first = orig.splitlines()[0]
    if first.startswith("#") and new.splitlines()[0].strip() != first.strip():
        bad.append("heading changed")
    return (not bad), bad


def chunks(body, limit=2600):
    """Split on headings, then on blank lines, so each call is short enough to answer reliably."""
    out, cur, size = [], [], 0
    for block in body.split("\n\n"):
        if size + len(block) > limit and cur:
            out.append("\n\n".join(cur)); cur, size = [], 0
        cur.append(block); size += len(block) + 2
    if cur:
        out.append("\n\n".join(cur))
    return out


def rewrite(path):
    text = open(path, encoding="utf-8").read()
    body, _a, _d = split_stamp(text)
    parts = [p for p in re.split(r"(?m)(?=^## )", body) if p.strip()]
    result, changed, kept = [], 0, 0
    for part in parts:
        pieces = [part] if len(part) <= 2600 else chunks(part)
        for piece in pieces:
            if len(piece.strip()) < 140 or piece.lstrip().startswith("|"):
                result.append(piece.rstrip("\n")); continue
            new = call(piece)
            ok, bad = valid(piece, new)
            if not ok:
                new = call(piece, " A previous attempt dropped or changed these items, keep them verbatim: %s." % json.dumps(bad[:12]))
                ok, bad = valid(piece, new)
            if ok:
                result.append(new.rstrip("\n")); changed += 1
            else:
                result.append(piece.rstrip("\n")); kept += 1
                print("  kept the original of a piece starting %r (%s)" % (piece.strip().splitlines()[0][:50], bad[:4]))
    final = "\n\n".join(result).rstrip("\n") + "\n"
    stamp = "\n<!-- readme-author: %s body-sha256: %s -->\n" % (MODEL, body_hash(final))
    open(path, "w", encoding="utf-8", newline="\n").write(final + stamp)
    print("%s: %d pieces rewritten by %s, %d kept; stamped" % (path, changed, MODEL, kept))


def main(argv):
    if len(argv) < 2 or argv[0] not in ("rewrite", "check", "hash"):
        print(__doc__); return 2
    cmd, files = argv[0], argv[1:]
    code = 0
    for f in files:
        if cmd == "rewrite":
            rewrite(f)
        elif cmd == "hash":
            print(body_hash(split_stamp(open(f, encoding="utf-8").read())[0]))
        else:
            why = check_file(f)
            print("%s: %s" % (f, why or "ok, written by a Meta model"))
            code = code or (1 if why else 0)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
