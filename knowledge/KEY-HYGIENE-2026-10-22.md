# Key hygiene, primordial paradox, 2026-10-22

VERDICT: nothing in this project holds a key or a login, and no line of code there writes
one anywhere it could be read back. 310 hits across five scans, and not one of them is a
value. This page is the evidence, the rule, and the two things the next worker must carry.

Card t_363f729a (GAME-ROADMAP-1 R19). Written by security-organization-audit. Measured at
HEAD 10ec031f6f79b17dde0fdfa3fa30fc25d5adb15a, scan finished 2026-10-22T21:13:59Z.

## 1. What was scanned

| Scan | What it covers | Size |
| --- | --- | --- |
| A, tracked tree at HEAD | every tracked text file, full content, through git grep | 552 files of 748 tracked; the other 196 are binary or over the 20 MB cap |
| B, working tree | the tracked files as they sit on disk now | 552 files |
| C, every text file on disk | tracked 552, ignored 16617, untracked 43, each labelled by git check-ignore | 17212 files read; 7042 binary or unreadable skipped, 1 over 20 MB skipped |
| D, last 50 commits | every added and removed line in the diff of the 50 commits that touched this project | 50 commits, dc7dc87e3c29 2026-10-22 back to db0215130498 2026-10-21, 231764 lines |
| E, the whole history | the same diff scan over the project's entire life, added because D's window starts on 2026-10-21 and the project starts 2026-10-19 | 73 commits, dc7dc87e3c29 back to 2fb415840e4b 2026-10-19, 248439 lines |

Eight patterns, not six: the three variable names, the Google key prefix, AKIA, and the PEM
private key header, plus an exact shape and a bare prefix for both the Google key and AKIA.
The bare prefix counts exist so a prefix can never hide behind a shape test that misses it:
a 39 char Google key is matched by the shape, and the same prefix inside a redaction regex is
matched by the loose test and then classified for what it is.

The tree is live. While this scan ran, other lanes modified DEVLOG.md and 21 .ogg files. Every
number on this page is one pass at one moment, not a guarantee about the next write. This page
is inside the scanned tree, so its own lines are counted in the on-disk pass: they are all
names or prefix in code, and none is a value, which is the state a page about keys should be in.

## 2. What was found, per pattern

| pattern | hits | by scan | verdicts |
| --- | --- | --- | --- |
| GEMINI_API_KEY | 291 | HEAD 46, disk-ignored 3, disk-tracked 46, disk-untracked 58, history 46, history-all 46, worktree 46 | name 291 |
| GOOGLE_KEY_PREFIX | 0 | none | none |
| GOOGLE_KEY_LOOSE | 14 | HEAD 2, disk-tracked 2, disk-untracked 4, history 2, history-all 2, worktree 2 | prefix-in-code 14 |
| AWS_ACCESS_KEY_ID | 0 | none | none |
| AWS_KEYID_LOOSE | 3 | disk-untracked 3 | prefix-in-code 3 |
| KAGGLE_API_TOKEN | 1 | disk-untracked 1 | name 1 |
| PINE_SANDBOX_API_KEY | 1 | disk-untracked 1 | name 1 |
| PEM_PRIVATE_KEY | 0 | none | none |

The one Kaggle name hit and the one Pinecone name hit, and the three AWS key id prefix hits, are
inside this page's own text. No project file reads either of those two variables, and the exact
Google and AWS key shapes return 0 everywhere, so no key shape exists anywhere to be found.

## 3. What was found, per file in the tracked tree at HEAD

| file (tracked, HEAD) | hits | line range | patterns |
| --- | --- | --- | --- |
| tests/test_ai_client.py | 20 | 31 to 423 | GEMINI_API_KEY 20 |
| tests/test_ear_critic.py | 14 | 31 to 495 | GEMINI_API_KEY 14 |
| DEVLOG.md | 4 | 1403 to 1491 | GEMINI_API_KEY 4 |
| tools/ai_client.py | 3 | 16 to 303 | GEMINI_API_KEY 3 |
| tools/ear_critic.py | 3 | 40 to 170 | GEMINI_API_KEY 2, GOOGLE_KEY_LOOSE 1 |
| tools/eye_critic.py | 3 | 47 to 179 | GEMINI_API_KEY 2, GOOGLE_KEY_LOOSE 1 |
| assets/audio/EAR_SWEEP_2026-10-22.md | 1 | 31 to 31 | GEMINI_API_KEY 1 |

## 4. Every hit at HEAD, one line each

Variable name in code is fine. A value is a leak, and a value would have blocked this card
instead of passing it. The scan classified the raw line and only masked the context below for
display, so a real key assignment could not slip through as a name.

The working tree and both history windows return these same 48 lines with the same verdicts, so
every hit in the project is on this list, plus the three lines in the ignored file listed in
section 5. No hit is missing from this page.

    tests/test_ai_client.py (20)
      tests/test_ai_client.py:31  GEMINI_API_KEY  name  "GEMINI_API_KEY", "AZURE_OPENAI_API_KEY", "META_API_KEY", "AZURE_OPENAI_ENDPOINT",
      tests/test_ai_client.py:94  GEMINI_API_KEY  name  os.environ["GEMINI_API_KEY"] = SENTINEL
      tests/test_ai_client.py:99  GEMINI_API_KEY  name  del os.environ["GEMINI_API_KEY"]
      tests/test_ai_client.py:102  GEMINI_API_KEY  name  assert "present in GEMINI_API_KEY" in out
      tests/test_ai_client.py:204  GEMINI_API_KEY  name  os.environ["GEMINI_API_KEY"] = SENTINEL
      tests/test_ai_client.py:217  GEMINI_API_KEY  name  del os.environ["GEMINI_API_KEY"]
      tests/test_ai_client.py:240  GEMINI_API_KEY  name  os.environ["GEMINI_API_KEY"] = SENTINEL
      tests/test_ai_client.py:253  GEMINI_API_KEY  name  del os.environ["GEMINI_API_KEY"]
      tests/test_ai_client.py:277  GEMINI_API_KEY  name  assert "GEMINI_API_KEY" in str(caught.value)
      tests/test_ai_client.py:282  GEMINI_API_KEY  name  os.environ["GEMINI_API_KEY"] = SENTINEL
      tests/test_ai_client.py:297  GEMINI_API_KEY  name  del os.environ["GEMINI_API_KEY"]
      tests/test_ai_client.py:304  GEMINI_API_KEY  name  os.environ["GEMINI_API_KEY"] = SENTINEL
      tests/test_ai_client.py:318  GEMINI_API_KEY  name  del os.environ["GEMINI_API_KEY"]
      tests/test_ai_client.py:327  GEMINI_API_KEY  name  os.environ["GEMINI_API_KEY"] = SENTINEL
      tests/test_ai_client.py:338  GEMINI_API_KEY  name  del os.environ["GEMINI_API_KEY"]
      tests/test_ai_client.py:347  GEMINI_API_KEY  name  os.environ["GEMINI_API_KEY"] = SENTINEL
      tests/test_ai_client.py:359  GEMINI_API_KEY  name  del os.environ["GEMINI_API_KEY"]
      tests/test_ai_client.py:403  GEMINI_API_KEY  name  monkeypatch.setenv("GEMINI_API_KEY", SENTINEL)
      tests/test_ai_client.py:410  GEMINI_API_KEY  name  del os.environ["GEMINI_API_KEY"]
      tests/test_ai_client.py:423  GEMINI_API_KEY  name  env["GEMINI_API_KEY"] = SENTINEL

    tests/test_ear_critic.py (14)
      tests/test_ear_critic.py:31  GEMINI_API_KEY  name  ENV_VARS = ("GEMINI_API_KEY", "PP_EAR_MODEL", "PP_EAR_LEDGER", "PP_EAR_CALIBRATION",
      tests/test_ear_critic.py:34  GEMINI_API_KEY  name  "PP_EAR_MAX_BACKOFF", "GEMINI_API_BASE", "GEMINI_API_KEY")
      tests/test_ear_critic.py:217  GEMINI_API_KEY  name  monkeypatch.setenv("GEMINI_API_KEY", SENTINEL)
      tests/test_ear_critic.py:223  GEMINI_API_KEY  name  assert "present in GEMINI_API_KEY" in out
      tests/test_ear_critic.py:232  GEMINI_API_KEY  name  assert "GEMINI_API_KEY is not set" in out
      tests/test_ear_critic.py:237  GEMINI_API_KEY  name  monkeypatch.setenv("GEMINI_API_KEY", SENTINEL)
      tests/test_ear_critic.py:252  GEMINI_API_KEY  name  monkeypatch.setenv("GEMINI_API_KEY", SENTINEL)
      tests/test_ear_critic.py:263  GEMINI_API_KEY  name  monkeypatch.setenv("GEMINI_API_KEY", SENTINEL)
      tests/test_ear_critic.py:302  GEMINI_API_KEY  name  monkeypatch.setenv("GEMINI_API_KEY", SENTINEL)
      tests/test_ear_critic.py:361  GEMINI_API_KEY  name  monkeypatch.setenv("GEMINI_API_KEY", SENTINEL)
      tests/test_ear_critic.py:374  GEMINI_API_KEY  name  monkeypatch.setenv("GEMINI_API_KEY", SENTINEL)
      tests/test_ear_critic.py:436  GEMINI_API_KEY  name  monkeypatch.setenv("GEMINI_API_KEY", SENTINEL)
      tests/test_ear_critic.py:469  GEMINI_API_KEY  name  monkeypatch.setenv("GEMINI_API_KEY", SENTINEL)
      tests/test_ear_critic.py:495  GEMINI_API_KEY  name  monkeypatch.setenv("GEMINI_API_KEY", SENTINEL)

    DEVLOG.md (4)
      DEVLOG.md:1403  GEMINI_API_KEY  name  - Nothing here has met a live API: no key is set in this environment, and python tools\ai_client...
      DEVLOG.md:1408  GEMINI_API_KEY  name  Still unproven: the wire format is proven against the documented schema and a fake urlopen, not...
      DEVLOG.md:1483  GEMINI_API_KEY  name  What exists: `tools\ear_critic.py` (1,205 lines) sends an MP3, OGG, WAV or FLAC to the Gemini AP...
      DEVLOG.md:1491  GEMINI_API_KEY  name  Honest limits: the chunked path and the 429 retry are proven with a fake HTTP layer and were nev...

    tools/ai_client.py (3)
      tools/ai_client.py:16  GEMINI_API_KEY  name  gemini               GEMINI_API_KEY, PP_GEMINI_MODEL, PP_GEMINI_MODEL_<ROLE>
      tools/ai_client.py:146  GEMINI_API_KEY  name  for name in ("GEMINI_API_KEY", "AZURE_OPENAI_API_KEY", "META_API_KEY"):
      tools/ai_client.py:303  GEMINI_API_KEY  name  key_env = "GEMINI_API_KEY"

    tools/ear_critic.py (3)
      tools/ear_critic.py:40  GEMINI_API_KEY  name  GEMINI_API_KEY is read from os.environ at call time and put in the x-goog-api-key
      tools/ear_critic.py:75  GEMINI_API_KEY  name  KEY_ENV = "GEMINI_API_KEY"
      tools/ear_critic.py:170  GOOGLE_KEY_LOOSE  prefix-in-code  text = re.sub(r"AIza[0-9A-Za-z_\-]{10,}", "[redacted]", text)

    tools/eye_critic.py (3)
      tools/eye_critic.py:47  GEMINI_API_KEY  name  GEMINI_API_KEY is read from os.environ at call time and put in the x-goog-api-key
      tools/eye_critic.py:91  GEMINI_API_KEY  name  KEY_ENV = "GEMINI_API_KEY"
      tools/eye_critic.py:179  GOOGLE_KEY_LOOSE  prefix-in-code  text = re.sub(r"AIza[0-9A-Za-z_\-]{10,}", "[redacted]", text)

    assets/audio/EAR_SWEEP_2026-10-22.md (1)
      assets/audio/EAR_SWEEP_2026-10-22.md:31  GEMINI_API_KEY  name  - Key handling: `GEMINI_API_KEY` was read at call time only (process environment, filled from

## 5. The three things that look like a key and are not

1. `AIza` appears in `tools/ear_critic.py:170`, `tools/eye_critic.py:179` as the first four characters of a redaction regex,
   `AIza[0-9A-Za-z_\-]{10,}` to `[redacted]`, run over every error string before it can
   reach a log or a review file. It is code that removes keys, not a key. The exact Google
   shape test returns 0, which is what proves it: no 39 char Google key exists anywhere in
   this project.
2. `SENTINEL` in `tests/test_ai_client.py` and `tests/test_ear_critic.py` is a stand in string
   the tests put in the environment to prove the client never echoes a key. It is a test
   fixture, and the tests assert that it never reaches the output, the URL, the ledger or an
   error message: tests/test_ai_client.py lines 104, 222, 223, 227, 340 and 428, and
   tests/test_ear_critic.py lines 224, 240, 242, 243 and 244. Read at those lines, not taken
   on trust.
3. `output/_eye_r2_runner.py` is the one place where a key moves between two stores. It is
   ignored by `output/*` in the project .gitignore, it is never tracked, and it reads the value
   from the Windows user environment with winreg and puts it in `os.environ` for a child
   process. Three name hits, no literal, no print:

      output/_eye_r2_runner.py:27  GEMINI_API_KEY  name
      output/_eye_r2_runner.py:38  GEMINI_API_KEY  name
      output/_eye_r2_runner.py:45  GEMINI_API_KEY  name

## 6. One gap and one rule the next worker must carry

The gap is real and cheap to close. The rule is what keeps this page true after the next
commit.

1. The credential exclusion rule does not live in this project. It lives one level up, in
   `<workspace>\Shared\.gitignore` lines 14 to 44 (`.env`, `.env.*`,
   `**/*secret*`, `**/*token*`, `**/*credential*`, `auth.json`, `auth.lock`, `**/vault/**`,
   `*.pem`, `*.key`). The project's own .gitignore has no credential line at all. Measured with
   `git check-ignore` from the project directory: `.env` is ignored by the root rule, `*.pem`
   is ignored, `auth.json` is ignored, and `id_rsa` is NOT ignored by any rule. Nothing named
   `id_rsa` exists in this project today (the only files whose names match credential words are
   two room files inside the ignored decompilation study copy), so nothing is exposed right
   now, but a file with that name would be committable on the next `git add -A`.
2. The keys are meant to arrive in the process environment, never in the tree. `tools/ai_client.py`
   and `tools/ear_critic.py` both read them at call time, put them in a request header, and pass
   every error string through `redact()`. That is the rule the next worker must keep: no env
   file in the project, no key in a JSON, YAML or CSV the tooling writes, no key in a log line,
   no key in an exception message, and no key echoed into a review or ledger file.

## 7. Method, and the defect the control caught

The scanner is key_scan3.py in this card's workspace, and it is deterministic: git grep, an
os.walk with git check-ignore, and a git log diff parse. The classifier reads the raw line,
decides name or value, and only then masks the context for display.

A scan that finds nothing proves nothing unless it can find something. `control_scan.py` builds
synthetic lines in memory (the Google shape filled with the letter x, a synthetic AKIA shape, a
PEM header, and a name assignment with a literal) and requires every one to be classified as a
value, plus four real code lines from this project to be classified as names. On the first run
the control FAILED one case: the scan was classifying the masked context, so a line reading
`GEMINI_API_KEY="<39 characters>"` came back as a harmless name, because the mask had already
turned the literal into `[MASKED 39 chars]`. That is the exact failure mode this card exists to
rule out. Fixed by classifying the raw line and masking only for display. The control now prints
RESULT: PASS (0 failure(s)), which is 9 of 9 checks passing, and the scan was
re-run after the fix.

## 8. What was not measured

- No environment variable was read. No check on this page needed one, so no key value was
  accessed at all, not even to compare (the card's scope says read one only if a check needs it).
- No live API call was made. Whether the Gemini key works, is rotated, or is scoped to a
  billing account is UNKNOWN here and is not this card's question.
- 7042 binary or unreadable files and 1 file over 20 MB were skipped. A key
  inside a PNG, an .ogg or a game archive would not be measured by a text scan. The tracked
  binary count is 196.
- The history scan reads diffs, so it sees every line that entered or left the tree. It does
  not see a value that was never committed, and it does not read git objects that no commit
  in this project touches.
- The scan cannot see the Windows registry, the user environment, or a shell history. Those
  are the stores `output/_eye_r2_runner.py` reads from, and they are outside this repository
  and outside this card's scope.

## 9. The rule, one sentence

Read every key from `os.environ` at call time and put it in the request header and nowhere
else, which is the rule written in the Keys section of `tools\ai_client.py` (and repeated in
`tools\ear_critic.py` and `tools\eye_critic.py`), with `redact()` as its enforcement point and
the shared root .gitignore as its exclusion half.

## 10. Reproduce

In the card workspace, `python key_scan3.py` writes scan3_result.json and scan3_hits.txt,
`python control_scan.py` prints the positive control, and `python make_page.py` rebuilds this
page from the JSON. The page refuses to build itself as a pass if any hit is a value.

This page is written and not committed. 49 files in the project are modified by other lanes
right now (measured with git status at the time of writing), so a commit from this card would
sweep their work in with it. The card's file scope is this one page, and gamedev commits it
with the rest of the roadmap lane.
