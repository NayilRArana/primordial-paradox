"""The rotating ear: score the four new cues with the first Gemini model that still answers.

Card EAR-ROTATE (t_154766b8), created 2026-10-23 by gamedev. The problem this solves is the one
knowledge\\EAR-GATE-2026-10-23.md ran into: the ear calls one model, `gemini-3.5-flash` answers 429
with a per day free tier cap, and the run stops with cues unscored. The fix is not more retries. It
is a named rotation order, one model per cue recorded in the ledger and in the report, and a
fallthrough to the next model when a model says no.

WHAT IT DOES
    For each cue in CUES (drive, arrival, boarding, fight) it calls tools\\ear_critic.py, which owns
    the fixed six line rubric, the audio chunking and the ledger. This module owns only three
    things: which model is asked, what happens when that model refuses, and the report.

THE ROTATION
    MODEL_ORDER is the order, and every entry carries the evidence that put it there. The loop takes
    the first model that is not marked exhausted, scores the cues on it, and when a cue fails with a
    quota, a 429 or a model the key is not served, marks that model exhausted in the state file and
    asks the next model for the cue that failed. Cues already scored keep the model that scored
    them: a failure never throws away a finished verdict.

    The state file (data\\ear_loop_state.json) is what makes the rotation survive a restart. A model
    that ran out of daily quota at 02:03 is still out at 09:30, so the 09:30 run does not spend its
    first minute learning the same 429.

WHAT IT NEVER DOES
    It never prints, logs or writes the key. GEMINI_API_KEY comes from the process environment; on
    a Windows host where the shell has not inherited it, the value is read from the user environment
    key HKCU\\Environment into the process and the report names only the source. Every error string
    goes through ear_critic.redact() before it reaches a line of output.

Usage
    python tools\\ear_loop.py --dry-run                     show the order, the files and the state
    python tools\\ear_loop.py                               score all four cues, write the report
    python tools\\ear_loop.py --cues drive,fight            score a subset
    python tools\\ear_loop.py --reset-state                 forget exhausted marks and start over
    python tools\\ear_loop.py --self-check                  prove rotation and fallthrough, no network
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import ear_critic  # noqa: E402  the rubric, the transport, the ledger, the score parsing

COUNTERPOINT = os.path.join(HERE, "counterpoint")
if COUNTERPOINT not in sys.path:
    sys.path.insert(0, COUNTERPOINT)

import cue_gate  # noqa: E402  the M4 gate: the measured clash count that now scores a cue

DATA = os.path.join(ROOT, "data")
CACHE = os.path.join(ROOT, "cache", "ear_loop_stub")
DEFAULT_REPORT = os.path.join(ROOT, "knowledge", "EAR-LOOP-2026-10-24.md")
STATE_PATH = os.path.join(DATA, "ear_loop_state.json")
GATE_DOC = "knowledge/EAR-GATE-2026-10-23.md"

# The four gate axes, in the order EAR-GATE ranks them by headroom. Hook and variety are recorded
# and are not gated, because the 17 file sweep scored them at their ceiling.
GATE_AXES = ("drums", "tension", "human", "structure")
ALL_DIMENSIONS = ear_critic.DIMENSIONS

# The rotating order. Each row says why it sits where it sits, and the evidence is a file in this
# tree or a ledger row, not a guess. Re-read knowledge/EAR-GATE-2026-10-23.md section 1 before
# editing this list: it is the record of what the free tier actually served on 2026-10-23.
MODEL_ORDER = (
    {
        "model": "gemini-3.5-flash-lite",
        "why": ("the judge the 2026-10-23 gate finished on; it has its own free tier bucket, so it "
                "survived the day the other models were capped"),
        "evidence": "knowledge/EAR-GATE-2026-10-23.md section 1, 8 of 8 rows",
    },
    {
        "model": "gemini-3.5-flash",
        "why": ("the ear default; a separate daily bucket, 20 free tier requests per UTC day, so it "
                "is the first model to try after lite runs out"),
        "evidence": ("the 429 body quoted in knowledge/EAR-GATE-2026-10-23.md line 14: "
                     "generate_content_free_tier_requests, limit 20"),
    },
    {
        "model": "gemini-3.7-flash",
        "why": "a third bucket, proven to answer this key with a full review",
        "evidence": "data/ear_ledger.csv row 2026-10-23T02:39:22Z, pp_03_harbor_v2, status ok",
    },
    {
        "model": "gemini-3.8-flash",
        "why": "a fourth bucket; the default of tools/ai_client.py and priced on the free tier",
        "evidence": "tools/ai_client.py PRICE_TABLE free_tier True; exhausted at 02:03 on 2026-10-23",
    },
)

MODELS_NOT_IN_ORDER = (
    {
        "model": "gemini-3.5-pro",
        "why": "not served to this key, so a rotation that included it would spend a call to learn that",
        "evidence": "knowledge/EAR-GATE-2026-10-23.md section 1",
    },
)

# The cues this card names, with the file that is the delivered master for each. A cue that lists a
# second file is a cue with a state pair; the pair is scored end to end so one verdict can name the
# junction as well as the states.
CUES = (
    {"cue": "drive", "label": "PP-02 drive",
     "path": "assets/audio/pp_drive/pp_drive_v3_humanized.mp3",
     "score": "assets/audio/pp_drive/pp_drive_v3_humanized_humanized.mid",
     "note": "the v3 humanized master, 178.571 s on the 126 bpm 3/4 grid"},
    {"cue": "arrival", "label": "PP-03 arrival, night quay",
     "path": "assets/audio/pp_arrival/pp_arrival.mp3",
     "score": "assets/audio/pp_arrival/pp_arrival.mid",
     "note": "48 bar loop at 80 bpm, 144.000 s, four textures inside one loop"},
    {"cue": "boarding", "label": "PP-06 boarding",
     "path": "assets/audio/pp_boarding/pp_boarding.mp3",
     "score": "assets/audio/pp_boarding/pp_boarding.mid",
     "note": "16 bars, one shot, no loop point by design"},
    {"cue": "fight", "label": "PP-04 fight",
     "path": "assets/audio/pp_fight/pp_fight_states.mp3",
     "score": "assets/audio/pp_fight/pp_fight_states.mid",
     "note": "FIGHT and CALM end to end, so the junction between the states is heard"},
)


class LoopError(RuntimeError):
    """Anything this tool refuses to do, with a message safe to print."""


class AllExhausted(LoopError):
    pass


# ----------------------------------------------------------------------------- small helpers

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def stamp(moment=None):
    return (moment or utc_now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_id(moment=None):
    return (moment or utc_now()).strftime("%Y%m%dT%H%M%SZ")


def rel(path):
    try:
        return os.path.relpath(os.path.abspath(str(path)), ROOT).replace("\\", "/")
    except ValueError:
        return str(path)


def dash_clean(text):
    """House style, and the same rule ear_critic applies to a review body."""
    return ear_critic._plain_dashes(text)


def _parse_when(text):
    text = (text or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.datetime.strptime(text, fmt).replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            continue
    return None


def _retry_after_seconds(text):
    """The wait Gemini asked for, if its body named one. Used only for the state file."""
    import re
    match = re.search(r'"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"', text or "")
    if match:
        return float(match.group(1))
    match = re.search(r"Please retry in ([0-9hms.]+)", text or "")
    if not match:
        return None
    total = 0.0
    for value, unit in re.findall(r"(\d+(?:\.\d+)?)([hms])", match.group(1)):
        total += float(value) * {"h": 3600.0, "m": 60.0, "s": 1.0}[unit]
    return total or None


def ensure_key():
    """Make sure the key is in the process environment, and say where it came from.

    Never returns, prints or logs the value: the source string is the whole report.
    """
    if os.environ.get(ear_critic.KEY_ENV, "").strip():
        return "the process environment"
    if sys.platform != "win32":
        return None
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            try:
                value, _kind = winreg.QueryValueEx(key, ear_critic.KEY_ENV)
            except FileNotFoundError:
                return None
    except (ImportError, OSError):
        return None
    value = str(value or "").strip()
    if not value:
        return None
    os.environ[ear_critic.KEY_ENV] = value  # in this process only, never written anywhere
    return ("the Windows user environment (HKCU\\Environment), read into this process "
            "and never printed")


# ----------------------------------------------------------------------------- state

def state_path(stub=False):
    return os.path.join(CACHE, "state.json") if stub else STATE_PATH


def read_state(path):
    if not os.path.exists(path):
        return {"version": 1, "models": {}, "runs": []}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            state = json.load(handle)
    except (OSError, ValueError):
        return {"version": 1, "models": {}, "runs": []}
    if not isinstance(state, dict):
        return {"version": 1, "models": {}, "runs": []}
    state.setdefault("version", 1)
    state.setdefault("models", {})
    state.setdefault("runs", [])
    return state


def write_state(path, state):
    folder = os.path.dirname(os.path.abspath(path))
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    state["runs"] = state.get("runs", [])[-20:]
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path


def exhausted_until(state, model, now=None):
    """The moment this model comes back, or None when it is live."""
    entry = (state.get("models") or {}).get(model) or {}
    until = _parse_when(entry.get("until"))
    if until is None:
        return None
    now = now or utc_now()
    return until if until > now else None


def mark_exhausted(state, model, reason, retry_after=None, now=None):
    now = now or utc_now()
    if retry_after:
        until = now + datetime.timedelta(seconds=float(retry_after))
    else:
        # No retryDelay in the body: the free tier buckets reset on the UTC day, so wait for it.
        until = (now + datetime.timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
    state.setdefault("models", {})[model] = {
        "exhausted_at": stamp(now),
        "until": stamp(until),
        "reason": ear_critic.redact(str(reason))[:300],
    }
    return state["models"][model]


def live_models(state, now=None):
    """MODEL_ORDER entries that are not marked exhausted, in order, with their wait if any."""
    now = now or utc_now()
    live, waiting = [], []
    for entry in MODEL_ORDER:
        until = exhausted_until(state, entry["model"], now)
        if until is None:
            live.append(entry)
        else:
            waiting.append((entry["model"], stamp(until)))
    return live, waiting


def is_quota_failure(exc):
    """True for the failures a rotation exists to survive."""
    text = str(exc or "")
    lowered = text.lower()
    if isinstance(exc, (ear_critic.RateLimited, ear_critic.DailyLimit)):
        return True
    if "429" in text or "quota" in lowered or "resource_exhausted" in lowered:
        return True
    # A model this key is not served is also a "try the next one", not a reason to stop.
    return "404" in text or "not found" in lowered or "not supported" in lowered


# ----------------------------------------------------------------------------- transports

def gemini_transport():
    """The real one: ear_critic's own POST, with the loop controlling the retry budget.

    The loop owns the retries now, so the per call backoff drops to zero attempts and a short cap:
    a 429 that lasts all day should move the run to the next model in seconds, not in minutes.
    """
    os.environ.setdefault("PP_EAR_MAX_RETRIES", "0")
    os.environ.setdefault("PP_EAR_MAX_BACKOFF", "5")
    return "gemini"


STUB_BODY = """SIMULATED RUN. No audio was sent and no model was asked. This text exists only to prove
that the loop reaches every cue and rotates when a model refuses, so every score below is a
placeholder, not a measurement, and must never be read as one.

### 2) Evaluation and scores (1 to 10)
- Hook memorability: 1 (simulated)
- Rhythm and drum interest: 1 (simulated)
- Tension and dissonance: 1 (simulated)
- Human feel versus mechanical: 1 (simulated)
- Instrumentation variety: 1 (simulated)
- Structure and contrast: 1 (simulated)

### 5) Scores as JSON
```json
{"hook": 1, "drums": 1, "tension": 1, "human": 1, "variety": 1, "structure": 1}
```
"""


def install_stub_transport(simulated_models=()):
    """Replace ear_critic's transport with a labelled placeholder, and the quota list with fakes.

    Nothing here touches the network, the real ledger or the real review folder: the caller points
    PP_EAR_LEDGER and PP_EAR_REVIEW_DIR at the stub cache before any call happens.
    """
    simulated = {str(name).strip() for name in simulated_models if str(name).strip()}

    def _post(model, payload, timeout=None, sleep=None):
        if model in simulated:
            raise ear_critic.RateLimited(
                "simulated 429 for %s: Quota exceeded for metric: "
                "generate_content_free_tier_requests, limit: 20, model: %s (this is the loop's own "
                "simulation, no call was made)" % (model, model))
        return {"candidates": [{"content": {"parts": [{"text": STUB_BODY}]}}],
                "usageMetadata": {"promptTokenCount": 0, "candidatesTokenCount": 0}}, 0

    ear_critic.post_generate = _post
    return simulated


# ----------------------------------------------------------------------------- measured clashes

# Card t_aa3ab04e. A critic score on its own let the title's v7 and v8 sit at the top of the table
# while the M0 clash counter measured 196 and 204 raw clashes on them (30 and 35 of those on a strong
# beat), and Nayil's verdict on both was "a bit dissonant". The score that ranks a cue is therefore
# the critic's total multiplied by the share of it the cue's own clashes leave standing:
#
#     dose  = (strong + WEAK_CLASH_SHARE * (raw - strong)) / bars
#     share = max(0, 1 - dose / CLASH_DOSE_PER_BAR)
#     final = critic_total * share
#
# The scale is a dose per bar rather than a subtraction, because these counters are dense: raw
# clashes run to the hundreds on a two-pulse texture, so a subtraction of one point per clash floors
# every legacy cue at zero and says nothing. One clash per bar is the dose that takes a whole score,
# and a clash off the strong beat counts a tenth of one on it, because those are the passing and
# neighbour tones the style wants and the same counter counts all of them.
#
# The share only ever falls as the clash count rises, so with two rows on the same rubric scores the
# one with more clashes always sits lower: no critic score can rise while its clashes do. That is
# what tests/test_ear_loop_clashes.py pins.
#
# A cue whose score cannot be read gets no count, so it gets no final score, and a row without a
# final never ranks above one that has it: an unmeasured cue is not a clean cue.
CLASH_DOSE_PER_BAR = 1.0
WEAK_CLASH_SHARE = 0.1


def critic_total(scores):
    """The six rubric points added up, or None while the judge has not filled every line."""
    values = [scores.get(dimension) for dimension in ALL_DIMENSIONS]
    if any(value is None for value in values):
        return None
    return float(sum(values))


def measured_clash(score_rel):
    """The gate's counts for one cue's score file. Returns (measured, why_not)."""
    if not score_rel:
        return None, "no score file is named for this cue, so its clashes are uncounted"
    path = os.path.join(ROOT, str(score_rel).replace("/", os.sep))
    if not os.path.isfile(path):
        return None, "%s is not in the tree" % score_rel
    facts, verdict = cue_gate.gate(path, root=ROOT)
    if facts is None:
        return None, verdict.get("why") or "the gate could not measure %s" % score_rel
    counts = cue_gate.counts_of(facts)
    return {"score": score_rel, "state": verdict["state"],
            "cp01": counts["cp01"], "cp09": counts["cp09"],
            "raw": counts["raw_clash"], "strong": counts["strong_raw"],
            "bars": facts["bars"], "notes": facts["notes"]}, ""


def clash_dose(measured):
    """The cue's weighted clashes per bar, or None when they were never counted."""
    if not measured or measured.get("raw") is None:
        return None
    bars = int(measured.get("bars") or 0)
    if bars <= 0:
        return None
    raw = int(measured.get("raw") or 0)
    strong = int(measured.get("strong") or 0)
    return (strong + WEAK_CLASH_SHARE * max(0, raw - strong)) / float(bars)


def clean_share(measured):
    """The fraction of a critic score a cue's clashes leave standing, 1.0 when it has none."""
    dose = clash_dose(measured)
    if dose is None:
        return None
    return max(0.0, 1.0 - dose / CLASH_DOSE_PER_BAR)


def final_score(scores, measured):
    """The critic's total times the cue's clean share. None when either half is unmeasured."""
    total = critic_total(scores or {})
    share = clean_share(measured)
    if total is None or share is None:
        return None
    return round(total * share, 2)


def rank_rows(rows):
    """Rows by final score, highest first, with every unmeasured row after every measured one."""
    return sorted(rows, key=lambda row: (row.get("final") is not None,
                                         row.get("final") if row.get("final") is not None else 0.0),
                  reverse=True)


# ----------------------------------------------------------------------------- scoring

def resolve_cues(names=None):
    wanted = None
    if names:
        wanted = {part.strip().lower() for part in str(names).split(",") if part.strip()}
    chosen = []
    for cue in CUES:
        if wanted is not None and cue["cue"] not in wanted:
            continue
        path = os.path.join(ROOT, cue["path"].replace("/", os.sep))
        if not os.path.exists(path):
            raise LoopError("cue %s: no audio at %s" % (cue["cue"], cue["path"]))
        record = {"cue": cue["cue"], "label": cue["label"], "path": cue["path"],
                  "score": cue.get("score", ""),
                  "note": cue.get("note", ""), "abs_path": path,
                  "size_mb": round(os.path.getsize(path) / (1024.0 * 1024.0), 2)}
        chosen.append(record)
    if not chosen:
        raise LoopError("no cue matched %r; the cues are %s"
                        % (names, ", ".join(c["cue"] for c in CUES)))
    return chosen


def weakest_axis(scores):
    """The weakest gate axis and the next weakest, both named, the way EAR-GATE reports them."""
    pairs = [(axis, scores.get(axis)) for axis in GATE_AXES]
    pairs = [(axis, value) for axis, value in pairs if value is not None]
    if not pairs:
        return "", ""
    pairs.sort(key=lambda pair: (pair[1], GATE_AXES.index(pair[0])))
    return pairs[0][0], (pairs[1][0] if len(pairs) > 1 else "")


def score_row(row, measured, why):
    """Attach the measured clash count and the final score to a row, in place."""
    row["measured_clash"] = measured
    row["critic_total"] = critic_total(row.get("scores") or {})
    row["final"] = final_score(row.get("scores") or {}, measured)
    row["clash_why"] = why
    return row


def score_cues(cues, state, gate, save=True, now=None, verbose=True):
    """Score every cue on the first live model, rotating on refusal. Returns a run dict."""
    now = now or utc_now()
    run = {
        "run": run_id(now),
        "at": stamp(now),
        "rows": [],
        "trials": [],
        "live_order": [entry["model"] for entry in MODEL_ORDER],
        "skipped": [],
    }
    # The clash count is a property of the cue's own score, not of the judge, so it is measured
    # once per cue here and survives a rotation: a cue that fails on one model still carries the
    # number that will score it when another model answers.
    measured = {cue["cue"]: measured_clash(cue.get("score", "")) for cue in cues}
    live, waiting = live_models(state, now)
    run["skipped"] = [{"model": model, "until": until} for model, until in waiting]
    if not live:
        raise AllExhausted("every model in the rotation is marked exhausted until %s"
                           % (", ".join("%s at %s" % pair for pair in waiting) or "never"))

    pending = list(cues)
    tried = set()
    while pending:
        live, _waiting = live_models(state, utc_now())
        live = [entry for entry in live if entry["model"] not in tried]
        if not live:
            # Nothing left to try. Whatever is still pending is recorded as failed, and the run is
            # kept: a partial run with its reasons is worth more than a run that vanishes.
            for cue in pending:
                facts, why = measured.get(cue["cue"], (None, "the cue was never measured"))
                run["rows"].append(score_row(
                    {"cue": cue["cue"], "label": cue["label"], "file": cue["path"],
                     "model": "", "status": "failed",
                     "error": "no model left in the rotation", "scores": {}}, facts, why))
            break
        entry = live[0]
        model = entry["model"]
        tried.add(model)
        still_pending = []
        for index, cue in enumerate(pending):
            if verbose:
                print("cue %-9s model %s" % (cue["cue"], model))
            started = utc_now()
            try:
                result = ear_critic.review_file(cue["abs_path"], model=model, gate=gate, save=save)
            except (ear_critic.NotConfigured, LoopError):
                raise
            except Exception as exc:  # noqa: BLE001 - classified below, then either rotated or recorded
                reason = ear_critic.redact(str(exc))[:400]
                quota = is_quota_failure(exc)
                run["trials"].append({"cue": cue["cue"], "model": model,
                                      "status": "quota" if quota else "error", "detail": reason})
                if verbose:
                    print("  %s on %s: %s" % ("quota" if quota else "error", model, reason))
                if quota:
                    wait = _retry_after_seconds(str(exc))
                    mark_exhausted(state, model, reason, retry_after=wait)
                    # This model is out for the whole run. Keep this cue and every cue after it
                    # for the next model; the cues already scored keep the model that scored them.
                    still_pending = list(pending[index:])
                    break
                facts, why = measured.get(cue["cue"], (None, "the cue was never measured"))
                run["rows"].append(score_row(
                    {"cue": cue["cue"], "label": cue["label"], "file": cue["path"],
                     "model": model, "status": "failed", "error": reason,
                     "scores": {}}, facts, why))
                continue
            scores = result.get("scores") or {}
            facts, why = measured.get(cue["cue"], (None, "the cue was never measured"))
            row = score_row(
                {"cue": cue["cue"], "label": cue["label"], "file": cue["path"], "model": model,
                 "status": "ok", "scores": scores,
                 "review": rel(result.get("review")) if result.get("review") else "",
                 "calls": result.get("calls"),
                 "seconds": round((utc_now() - started).total_seconds(), 1),
                 "error": ""}, facts, why)
            run["rows"].append(row)
            run["trials"].append({"cue": cue["cue"], "model": model, "status": "ok", "detail": ""})
            if verbose:
                print("  scores: %s" % ", ".join("%s %s" % (d, scores.get(d) if scores.get(d) is not None else "?")
                                                 for d in ALL_DIMENSIONS))
                print("  clash:  %s raw, %s on a strong beat; final %s"
                      % ((facts or {}).get("raw", "?"), (facts or {}).get("strong", "?"),
                         row["final"] if row["final"] is not None else "unmeasured"))
        pending = still_pending
    run["models_used"] = sorted({row["model"] for row in run["rows"] if row.get("model")})
    run["cues_scored"] = sum(1 for row in run["rows"] if row["status"] == "ok")
    return run


# ----------------------------------------------------------------------------- report

def _score_cell(score):
    return "?" if score is None else str(score)


def _clash_cell(row):
    """The measured clash count as 'raw / strong', or the reason it was never counted."""
    measured = row.get("measured_clash") or {}
    if measured.get("raw") is None:
        return "unmeasured"
    return "%s / %s" % (measured.get("raw"), measured.get("strong"))


def _final_cell(row):
    """The final score, or 'unmeasured' when the cue's own score could not be read."""
    final = row.get("final")
    return "unmeasured" if final is None else ("%g" % final)


def render_table(run):
    lines = ["| # | cue | file | hook | drums | tension | human | variety | structure | critic total | clashes raw / strong | final | weakest gate axis | model | review |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for index, row in enumerate(rank_rows(run["rows"]), 1):
        scores = row.get("scores") or {}
        weakest, second = weakest_axis(scores)
        if weakest:
            gate = "%s %s%s" % (weakest, _score_cell(scores.get(weakest)),
                                " (%s %s)" % (second, _score_cell(scores.get(second))) if second else "")
        else:
            gate = "not scored"
        status = row.get("status")
        model = row.get("model") or "none"
        review = row.get("review") or row.get("error") or ""
        if status == "failed":
            model = "%s (failed: %s)" % (model, (row.get("error") or "")[:60])
        total = row.get("critic_total")
        lines.append("| %d | %s | `%s` | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
                     % (index, row["label"], row["file"],
                        _score_cell(scores.get("hook")), _score_cell(scores.get("drums")),
                        _score_cell(scores.get("tension")), _score_cell(scores.get("human")),
                        _score_cell(scores.get("variety")), _score_cell(scores.get("structure")),
                        "not scored" if total is None else "%g" % total,
                        _clash_cell(row), _final_cell(row), gate, model, review))
    return "\n".join(lines)


def render_order():
    lines = ["| # | model | why it sits here | evidence |", "| --- | --- | --- | --- |"]
    for index, entry in enumerate(MODEL_ORDER, 1):
        lines.append("| %d | `%s` | %s | %s |" % (index, entry["model"], entry["why"], entry["evidence"]))
    return "\n".join(lines)


def render_trials(run):
    if not run.get("trials"):
        return "_No call was attempted._"
    lines = ["| cue | model | outcome | detail |", "| --- | --- | --- | --- |"]
    for trial in run["trials"]:
        detail = (trial.get("detail") or "").replace("|", "/")[:200]
        lines.append("| %s | `%s` | %s | %s |" % (trial["cue"], trial["model"], trial["status"], detail))
    return "\n".join(lines)


def render_report(state, transport, key_source, simulated=False):
    lines = ["# EAR LOOP, the rotating ear, 2026-10-24", "",
             "Card EAR-ROTATE (t_154766b8), created 2026-10-23 by gamedev. Owner: musician. "
             "This file is written by `tools/ear_loop.py`; do not edit it by hand, re-run the tool.",
             "",
             "The criteria are not restated here. They live in `%s`: the fixed six line rubric "
             "(hook, drums, tension, human, variety, structure) and the four gate axes (drums, "
             "tension, human, structure) that card 2 of that file calls the headroom. This run "
             "records a score per criterion, the axis that is weakest, and the model that gave it."
             % GATE_DOC, "",
             "From card t_aa3ab04e the score carries a measured number as well. "
             "`tools/counterpoint/cue_gate.py` runs the counterpoint checker and the M0 clash "
             "counter on the cue's own score file, and the final column is the critic's total "
             "times the share its measured clashes leave standing (one clash per bar takes the "
             "whole score; a clash off the strong beat counts a tenth). A critic score therefore "
             "cannot rise while the clashes do, which is the failure that let v7 and v8 win the "
             "table while Nayil heard them as \"a bit dissonant\".", ""]

    if simulated:
        lines += ["> SIMULATED RUN. The transport was the loop's own stub: no audio was sent, no "
                  "model was asked, and every score in this file is a placeholder (1) that exists "
                  "only to prove the rotation. This file is in the stub cache, not in knowledge/, "
                  "for exactly that reason.", ""]

    lines += ["## 1. The rotating order", "",
              "The order is not a preference list, it is the record of what the free tier served on "
              "2026-10-23 (see `%s` section 1). A model that answers 429, a quota error or a model "
              "this key is not served is marked exhausted in `data/ear_loop_state.json`, with the "
              "`retryDelay` the API named when it named one, and the next model takes over. The "
              "mark survives a restart, so a run at midday does not spend its first call learning a "
              "cap that was known at dawn." % GATE_DOC, "",
              render_order(), "",
              "Deliberately not in the order: " + "; ".join(
                  "`%s`, %s (%s)" % (entry["model"], entry["why"], entry["evidence"])
                  for entry in MODELS_NOT_IN_ORDER) + ".", ""]

    waiting = state.get("models") or {}
    if waiting:
        lines += ["### Models marked exhausted right now", "",
                  "| model | marked at | live again at | what it said |",
                  "| --- | --- | --- | --- |"]
        for model in [entry["model"] for entry in MODEL_ORDER] + [e["model"] for e in MODELS_NOT_IN_ORDER]:
            entry = waiting.get(model)
            if not entry:
                continue
            lines.append("| `%s` | %s | %s | %s |"
                         % (model, entry.get("exhausted_at", "?"), entry.get("until", "?"),
                            (entry.get("reason") or "").replace("|", "/")[:180]))
        lines.append("")

    latest = (state.get("runs") or [{}])[-1]
    calls_ok = len([t for t in (latest.get("trials") or []) if t.get("status") == "ok"])
    lines += ["## 2. This run", "",
              "- run: `%s`" % latest.get("run", "?"),
              "- transport: %s" % transport,
              "- key: %s" % (key_source or "absent from the environment, so nothing was sent"),
              "- calls that returned a review: %d; cues scored: %d of %d"
              % (calls_ok, latest.get("cues_scored", 0), len(latest.get("rows") or [])),
              ""]

    for run in list(state.get("runs") or [])[-3:][::-1]:
        lines += ["### Run %s (%s)" % (run.get("run"), run.get("at")), ""]
        if run.get("skipped"):
            lines.append("Skipped before any call: " + ", ".join(
                "`%s` until %s" % (item["model"], item["until"]) for item in run["skipped"]) + ".")
            lines.append("")
        lines += [render_table(run), "",
                  "Rows are ranked by the final score: the critic's total times the cue's clean "
                  "share, where the share is 1 minus its weighted clashes per bar (one clash per bar "
                  "takes the whole score, and a clash off the strong beat counts a tenth of one). A "
                  "cue whose score file could not be read shows `unmeasured` and sits below every "
                  "measured row, because an uncounted cue is not a clean one.",
                  "",
                  "Every call, in the order it was made:", "",
                  render_trials(run), ""]
        if run.get("models_used"):
            lines.append("Model per cue on this run: " + ", ".join(
                "%s `%s`" % (row["cue"], row["model"] or "none") for row in run["rows"]) + ".")
        else:
            lines.append("No cue was scored on this run. The report keeps the reason rather than "
                         "dropping the run.")
        lines.append("")

    lines += ["## 3. What this file does not say", "",
              "- The judge is not the judge in `%s`. That gate ran entirely on "
              "`gemini-3.5-flash-lite`; a run here that falls through to `gemini-3.5-flash` is a "
              "different listener with a 14 point swing on the ship master already measured in that "
              "file. The `model` column is the only thing that makes two rows comparable, which is "
              "why it is a column and not a footnote." % GATE_DOC,
              "- The ear misnames channels and miscounts bars. It hears the mix, not the score. A "
              "score here is a queue position, not a verdict.",
              "- Scores are per cue and inline (every cue is under the 15 MB inline limit), so one "
              "cue is one call and a rotation cannot split a single cue across two models. A cue "
              "that is too long for one call is chunked by `ear_critic.py`, and that is the case "
              "where one verdict can be mixed; the ledger records the model of every chunk.",
              ""]

    lines += ["## 4. How to check this file", "",
              "- Order: `python tools/ear_loop.py --dry-run` prints the order, the files and the "
              "state without sending anything.",
              "- Rotation: `python tools/ear_loop.py --self-check` simulates a 429 on the first model "
              "and proves the run still scores all four cues, with no network and no key.",
              "- Rows: `python tools/ear_loop.py --json` reprints the last run as JSON, and "
              "`data/ear_ledger.csv` holds one row per call with the model that made it.",
              "- Dashes: this file carries no em dash, en dash, figure dash or horizontal bar; the "
              "tool rewrites long dashes in the model's own text before it writes them here.",
              ""]
    return dash_clean("\n".join(lines))


def write_report(path, text):
    folder = os.path.dirname(os.path.abspath(path))
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path


# ----------------------------------------------------------------------------- cli

def _print_state(state):
    live, waiting = live_models(state)
    print("rotation order (first live model is the one that scores this run):")
    for index, entry in enumerate(MODEL_ORDER, 1):
        until = exhausted_until(state, entry["model"])
        print("  %d %-22s %s" % (index, entry["model"],
                                 "exhausted until %s" % stamp(until) if until else "live"))
    for entry in MODELS_NOT_IN_ORDER:
        print("  - %-22s not in the order: %s" % (entry["model"], entry["why"]))
    if not live:
        print("  every model is exhausted; the next run would refuse rather than spend a call")


def _self_check():
    """Prove rotation and fallthrough with no network, no key and no audio sent."""
    for folder in (CACHE, os.path.dirname(CACHE)):
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
    os.environ["PP_EAR_LEDGER"] = os.path.join(CACHE, "ledger.csv")
    os.environ["PP_EAR_REVIEW_DIR"] = os.path.join(CACHE, "reviews")
    sim_state_path = state_path(stub=True)
    if os.path.exists(sim_state_path):
        os.remove(sim_state_path)
    state = read_state(sim_state_path)
    first = MODEL_ORDER[0]["model"]
    second = MODEL_ORDER[1]["model"]
    install_stub_transport(simulated_models=[first])
    cues = resolve_cues()
    gate = ear_critic.RateGate(per_minute=0, per_day=0)
    run = score_cues(cues, state, gate, save=True, verbose=False)
    write_state(sim_state_path, state)
    state["runs"].append(run)
    write_state(sim_state_path, state)

    failures = []
    scored = [row for row in run["rows"] if row["status"] == "ok"]
    if len(scored) != len(CUES):
        failures.append("scored %d of %d cues" % (len(scored), len(CUES)))
    if any(row["model"] == first for row in run["rows"]):
        failures.append("a cue was scored on the model that was told to answer 429")
    if not scored or any(row["model"] != second for row in scored):
        failures.append("the fallthrough did not land on %s" % second)
    if not any(state["models"].get(first)):
        failures.append("%s was not marked exhausted" % first)
    if not all(row.get("scores", {}).get(d) is not None for row in scored for d in ALL_DIMENSIONS):
        failures.append("a scored row is missing a rubric dimension")
    if any((row.get("scores") or {}).get(d) != 1 for row in scored for d in ALL_DIMENSIONS):
        failures.append("the stub's placeholder score did not survive parsing")
    # The clash debt is the half of the score the judge cannot give: every scored row must carry a
    # measured count, and its final must be the total minus exactly that count.
    for row in scored:
        if row.get("measured_clash") is None:
            failures.append("cue %s has no measured clash count (%s), so its score cannot be ranked"
                            % (row["cue"], row.get("clash_why") or "no reason given"))
            continue
        expected = final_score(row["scores"], row["measured_clash"])
        if row.get("final") != expected:
            failures.append("cue %s: final %r is not the critic total times the clean share (%r)"
                            % (row["cue"], row.get("final"), expected))
    finals = [row.get("final") for row in rank_rows(scored) if row.get("final") is not None]
    if finals != sorted(finals, reverse=True):
        failures.append("the rows do not rank by final score")

    print("self check: simulated 429 on %s, fallthrough to %s" % (first, second))
    print("cues scored: %d of %d" % (len(scored), len(CUES)))
    for row in rank_rows(run["rows"]):
        measured = row.get("measured_clash") or {}
        print("  %-9s critic %-4s clash %s raw / %s strong  final %s"
              % (row["cue"], row.get("critic_total"), measured.get("raw", "?"),
                 measured.get("strong", "?"), row.get("final")))
    print("models used: %s" % ", ".join(run.get("models_used") or []) or "none")
    print("state marked: %s" % ", ".join(sorted(state["models"])) or "none")
    print("review files: %s" % (os.environ["PP_EAR_REVIEW_DIR"]))
    print("ledger: %s (the stub ledger, never data/ear_ledger.csv)" % os.environ["PP_EAR_LEDGER"])
    if failures:
        print("RESULT: FAIL")
        for failure in failures:
            print("  - %s" % failure)
        return 1
    print("RESULT: PASS")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description="Score the new cues with the first Gemini model that still answers.")
    parser.add_argument("--cues", default=None,
                        help="comma separated subset of %s" % ", ".join(c["cue"] for c in CUES))
    parser.add_argument("--dry-run", action="store_true",
                        help="print the order, the files and the state, send nothing")
    parser.add_argument("--json", action="store_true", help="print the run as JSON after the report")
    parser.add_argument("--report", default=DEFAULT_REPORT,
                        help="where the report goes (default: knowledge/EAR-LOOP-2026-10-24.md)")
    parser.add_argument("--no-save", action="store_true",
                        help="do not write a review file per cue (the ledger is still written)")
    parser.add_argument("--reset-state", action="store_true",
                        help="forget every exhausted mark before this run")
    parser.add_argument("--self-check", action="store_true",
                        help="prove the rotation and the fallthrough offline, then exit")
    parser.add_argument("--simulate-quota", action="append", default=[], metavar="MODEL",
                        help="treat this model as if it answered a 429 (repeatable)")
    parser.add_argument("--stub", action="store_true",
                        help="use the labelled placeholder transport: no network, stub ledger and "
                             "stub report, for checking the loop itself")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.self_check:
        return _self_check()

    stub = bool(args.stub or args.simulate_quota)
    if stub:
        os.environ["PP_EAR_LEDGER"] = os.path.join(CACHE, "ledger.csv")
        os.environ["PP_EAR_REVIEW_DIR"] = os.path.join(CACHE, "reviews")

    state_file = state_path(stub=stub)
    state = read_state(state_file)
    if args.reset_state:
        state = {"version": 1, "models": {}, "runs": []}

    if args.dry_run:
        _print_state(state)
        print("")
        for cue in resolve_cues(args.cues):
            print("cue %-9s %-52s %5.2f MB" % (cue["cue"], cue["path"], cue["size_mb"]))
        print("")
        report = os.path.join(CACHE, "EAR-LOOP-SIMULATED.md") if stub else args.report
        print("report: %s" % rel(report))
        print("key:    %s" % ("present in %s" % ear_critic.KEY_ENV
                              if ear_critic.key_present()
                              else "absent from this process; a real run would read it from the "
                                   "Windows user environment or refuse"))
        return 0

    key_source = None
    transport = "the loop's stub, no network"
    if stub:
        installed = install_stub_transport(simulated_models=args.simulate_quota)
        if installed:
            transport = ("the loop's stub, no network, with a simulated 429 on %s"
                         % ", ".join(sorted(installed)))
        gate = ear_critic.RateGate(per_minute=0, per_day=0)
    else:
        key_source = ensure_key()
        if not key_source:
            print("not configured: %s is absent from the process environment and from the Windows "
                  "user environment, so no cue was scored" % ear_critic.KEY_ENV)
            return 2
        transport = gemini_transport()
        gate = ear_critic.RateGate()

    try:
        cues = resolve_cues(args.cues)
        run = score_cues(cues, state, gate, save=not args.no_save)
    except AllExhausted as exc:
        print("rate limited: %s" % ear_critic.redact(str(exc)))
        _print_state(state)
        return 3
    except ear_critic.NotConfigured as exc:
        print("not configured: %s" % ear_critic.redact(str(exc)))
        return 2
    except LoopError as exc:
        print("error: %s" % ear_critic.redact(str(exc)))
        return 1
    except (ear_critic.DailyLimit, ear_critic.RateLimited) as exc:
        print("rate limited: %s" % ear_critic.redact(str(exc)))
        return 3

    state["runs"].append(run)
    write_state(state_file, state)

    report_path = os.path.join(CACHE, "EAR-LOOP-SIMULATED.md") if stub else args.report
    text = render_report(state, transport, key_source, simulated=stub)
    write_report(report_path, text)

    print("")
    print("run:     %s" % run["run"])
    print("scored:  %d of %d cues" % (run["cues_scored"], len(run["rows"])))
    print("models:  %s" % (", ".join(run.get("models_used") or []) or "none"))
    for row in run["rows"]:
        print("  %-9s %-22s %s" % (row["cue"], row["model"] or "none",
                                   "ok" if row["status"] == "ok" else "failed: %s" % row["error"][:80]))
    print("report:  %s" % rel(report_path))
    print("state:   %s" % rel(state_file))
    if args.json:
        print(json.dumps({"run": run}, indent=2, sort_keys=True))
    if run["cues_scored"] < len(run["rows"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
