"""judge_panel.py: score the newest nightly demo the way the judges will, and write five fixes as card bodies.

Card W4 JUDGE-PANEL (t_70840bce, testing lane, 2026-10-26), from `WIN-PLAN-2026-10-26.md` section
"W4 JUDGE-PANEL". The team has critics for frames (`tools\\eye_critic.py`) and for audio
(`tools\\ear_critic.py`), and none for the thing the judges actually watch: the video. This tool
once a night puts the newest `output\\demo\\nightly-*.mp4` in front of a vision model with the
judging rubric, and writes `knowledge\\JUDGE-PANEL-<date>.md` with four scores, one reason each, and
the top five fixes as paste-ready card bodies.

THE RUBRIC IS THE HACKATHON'S, NOT AN INVENTED ONE
    Impact 30, Use of Meta AI tooling 25, Technical depth 20, Demo 25, submission Nov 4 9 PM ET,
    from `WIN-PLAN-2026-10-26.md` line 3 and `HACKATHON-BRIEF.md`. Each criterion is asked for as a
    score from 1 to 10 with ONE reason, and the tool computes the weighted total itself
    (score / 10 * weight, so the total is out of 100). The model's own arithmetic is never used.

WHAT IS SENT, and what a judge would see
    Frames sampled evenly from the newest nightly capture (6 by default), each one inline, plus the
    measured facts about the file (duration, resolution, frame rate, and the run's own recorded
    numbers), plus an excerpt of the script the demo was planned from. The prompt carries the rule
    the manager set for every card: would a judge see it in the 3 minute video, the README or the
    repo? A frame from an h264 capture has thousands of colours because the encoder made them, so
    the PPU palette check that `eye_critic.py` applies to a PNG is deliberately NOT applied here:
    these are video frames, judged for what they show, not for legal 2C02 colours.

THE MODEL PATH IS THE ONE THAT ALREADY EXISTS
    The transport is `eye_critic.post_generate()`, so the same code sends the request, the same
    `PP_AI_BACKEND=meta` switch hands it to `tools\\meta_client.py` (Meta vision, once billing
    works), the same `RateGate` counts calls in `data\\eye_ledger.csv`, and the same `redact()`
    keeps the key out of every line this tool can print or write. On top of that it carries the
    model rotation `tools\\eye_drive.py` proved: the free tier is 20 requests per project per MODEL
    per day, so a per-day refusal or a 503 moves to the next model instead of losing the night.

THE JUDGE MODEL IS MUSE-SPARK-1.3 (manager, 2026-10-26 17:15)
    The Meta Model API went live when Nayil set up billing, and the manager made muse-spark-1.3 the
    judge model: the panel sends through `tools\\meta_client.py` (`PP_AI_BACKEND=meta`) with that
    model first and only, against the same four official weights. Meta's answer is translated back
    into the generateContent shape by `meta_client.gemini_compat_generate()`, so the rubric, the
    parsing and the ledger are untouched. When no Meta key can be found the panel refuses to
    pretend: it names the missing key, falls back to the Gemini free-tier chain only if
    `PP_AI_BACKEND=gemini` was asked for by hand, and otherwise writes the measured half with
    NOT JUDGED rows. Every billed answer is recorded in `data\\ai_cache` (meta_client's record mode),
    so the judges' replay mode can play the same panel without a key and without a spend.

KEYS
    Meta: MODEL_API_KEY (or META_API_KEY). Gemini: GEMINI_API_KEY. Each is read from the
    environment, or, when the shell that spawned this process does not carry it, from the Windows
    user environment (HKCU\\Environment, read through `eye_drive.load_key_from_user_environment()` for
    Gemini and through `load_meta_key_from_user_environment()` here for Meta, which is the same
    registry read and never a key file). A key is never printed, never written to a panel file and
    never put in an exception: only the place it came from is printed.

CARD LIMIT, AND WHY THIS TOOL CREATES NOTHING
    It writes at most five fixes, each as a body file under `output\\judge_cards\\<date>\\`, and the
    card says exactly five. It never creates a card itself: creating cards is the balancer feed's or
    the manager's call, and the panel file carries the ready-to-paste command for each fix. A night
    that produced six fixes has its sixth dropped, with the count stated in the panel, because
    "no more than five cards a night" is the rule and a silently truncated list would look like five.

    The five also land as card drafts in `../arananet/manager/inbox/director.md` (manager,
    2026-10-26 17:15), one dated section per night, each draft beside the command that would create
    it. That file is append only and this tool only appends: a second run on the same date replaces
    nothing, so the drafts on disk are the last run's, and the panel file says which run wrote them.

Usage
    python tools\\judge_panel.py --measure-only     sample frames and measure, send nothing
    python tools\\judge_panel.py                    sample, judge, write the panel and the card bodies
    python tools\\judge_panel.py --backend gemini   use the Gemini free-tier chain instead of Meta
    python tools\\judge_panel.py --dry-run          print the plan and exit, send nothing
    python tools\\judge_panel.py --self-test        prove the model rotation on a fake 429, then stop
    python tools\\judge_panel.py --video PATH --frames 8 --report-out X.md --inbox-out Y.md

Sources
    judging weights and the deadline  ..\\arananet\\meta-hackathon\\WIN-PLAN-2026-10-26.md line 3
    the judge model and the inbox     manager comment on card t_70840bce, 2026-10-26 17:15
    free tier ceiling and the 429 body  tools\\eye_critic.py header, measured 2026-10-22
    model rotation on a per day refusal tools\\eye_drive.py, measured 2026-10-24
    the Meta API shape and its cache  tools\\meta_client.py header, read 2026-10-26
    the demo script this reads       knowledge\\DEMO-SCRIPT.md
"""

from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS_DIR)
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import eye_critic  # noqa: E402  the one transport, ledger, pacekeeper and redactor
import eye_drive  # noqa: E402  the one reader of the Windows user environment for the key

OUTPUT = os.path.join(ROOT, "output")
DEMO_DIR = os.path.join(OUTPUT, "demo")
FRAME_DIR = os.path.join(OUTPUT, "judge_frames")
CARD_DIR = os.path.join(OUTPUT, "judge_cards")
KNOWLEDGE = os.path.join(ROOT, "knowledge")
SCRIPT_MD = os.path.join(KNOWLEDGE, "DEMO-SCRIPT.md")
NIGHTLY_LOG = os.path.join(KNOWLEDGE, "DEMO-NIGHTLY.md")
# The manager's inbox (card t_70840bce comment, 2026-10-26 17:15): the five fixes land here as card
# drafts every night, one dated section each, beside the command that would create the card.
INBOX = os.path.join(ROOT, os.pardir, "arananet", "manager", "inbox", "director.md")

# The judging rubric, from WIN-PLAN-2026-10-26.md line 3. The weights are the hackathon's and are
# not tuned here; the total is out of 100, which is the number a judge would recognise.
CRITERIA = (
    ("impact", "Impact", 30,
     "does the game do something only these models make possible, and would a player care"),
    ("meta_tooling", "Use of Meta AI tooling", 25,
     "are Meta models doing real work in the game or the pipeline, visibly, not as a bolt-on"),
    ("technical_depth", "Technical depth", 20,
     "hardware limits enforced in code, a real engine, a local AI bridge, work a builder respects"),
    ("demo", "Demo", 25,
     "would a judge understand and want to share the 3 minute video, without being told what to see"),
)
WEIGHTS = {key: weight for key, _label, weight, _text in CRITERIA}
LABELS = {key: label for key, label, _w, _t in CRITERIA}
WHY = {key: text for key, _label, _w, text in CRITERIA}

SCORE_MIN, SCORE_MAX = 1, 10
MAX_FIXES = 5
# The panel's order is the ranking, so fix 1 lands ahead of fix 5 in the dispatcher.
FIX_PRIORITY = (93, 91, 90, 88, 86)
LANES = ("gamedev", "builder", "assistant", "musician", "testing", "research-assistant",
         "code-review", "audit")
# The lanes the model may name in its own words. A name outside this map is kept verbatim in the
# panel and marked unassigned rather than quietly filed under a lane it did not ask for.
LANE_ALIASES = {
    "gamedev": "gamedev", "game_dev": "gamedev", "gameplay": "gamedev", "game": "gamedev",
    "engine": "gamedev", "gml": "gamedev", "frontend": "gamedev",
    "builder": "builder", "build": "builder", "engineering": "builder", "backend": "builder",
    "infrastructure": "builder", "ai_bridge": "builder",
    "assistant": "assistant", "docs": "assistant", "documentation": "assistant",
    "writing": "assistant",
    "musician": "musician", "audio": "musician", "music": "musician", "sound": "musician",
    "testing": "testing", "qa": "testing", "test": "testing", "capture": "testing",
    "quality": "testing",
    "research_assistant": "research-assistant", "research": "research-assistant",
    "code_review": "code-review", "review": "code-review",
    "audit": "audit", "security": "audit",
}
DEFAULT_FRAMES = 6

# The free tier is per project per MODEL per day, so the chain buys budget. The order is the three
# models the ledger shows answering (data\eye_ledger.csv, 2026-10-25), then the one that answered
# when gemini-3.8-flash returned an error on the same day, which is why the newest name is not first.
MODEL_CHAIN = ("gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite",
               "gemini-3.1-flash-lite")
# The judge model, set by the manager on 2026-10-26 17:15 once Nayil's billing was live: muse-spark-1.3
# through tools\meta_client.py, with its vision role on the same model. One model, not a rotation,
# because a billed API does not hand out a per-model free tier to walk.
META_JUDGE_MODEL = "muse-spark-1.3"
META_CHAIN = (META_JUDGE_MODEL,)
META_KEY_ENVS = ("MODEL_API_KEY", "META_API_KEY")
# A billed panel call is the one place this tool can spend money, so it carries its own small ceiling
# even though the feed asks for one a night: a hand-run second or third panel in the same UTC day is
# allowed up to this number, and a fourth is refused rather than quietly billed.
META_CALLS_PER_DAY_DEFAULT = 2
META_CALLS_PER_DAY_ENV = "PP_JUDGE_META_CALLS_PER_DAY"
# Measured facts about the ledger, quoted in the panel so the rotation is not a claim.
CHAIN_NOTE = (
    "the chain order comes from data\\eye_ledger.csv, read 2026-10-26: gemini-3.5-flash and "
    "gemini-3.6-flash answered, gemini-3.8-flash recorded status=error after 226.72 s on 2026-10-25, "
    "and gemini-3.5-flash-lite answered on the same day, so the newest name is tried last and not "
    "first")
# The Meta path has no rotation to describe, so it says what it is instead of quoting the gemini note.
META_CHAIN_NOTE = (
    "the judge model is muse-spark-1.3 on the Meta Model API, set by the manager on 2026-10-26 "
    "17:15, and it is the only model in this chain: a billed API does not hand out a per-model "
    "free tier to walk, so a refusal from it is reported rather than walked past")

WARNING = (
    "Warning: the panel is a rough critic. It sees six still frames from a video, not the video, it "
    "cannot hear the audio, it cannot read the repository and it cannot know what the judges value "
    "beyond the four weights quoted here. Where a panel sentence disagrees with a measured number in "
    "this file, the measured number wins. Treat the scores as a prompt for the team's own judgement, "
    "not as a verdict.")

# Aliases the model may use for the four scores and their reasons. Anything else is ignored rather
# than guessed at, so a missing criterion reads as NOT JUDGED instead of as a made up number.
SCORE_ALIASES = {
    "impact": "impact", "impact_score": "impact", "score_impact": "impact",
    "meta_tooling": "meta_tooling", "meta_ai_tooling": "meta_tooling",
    "use_of_meta_ai_tooling": "meta_tooling", "use_of_meta_tooling": "meta_tooling",
    "meta": "meta_tooling", "meta_score": "meta_tooling", "metatooling": "meta_tooling",
    "technical_depth": "technical_depth", "technical": "technical_depth",
    "technical_score": "technical_depth", "depth": "technical_depth",
    "demo": "demo", "demo_score": "demo", "score_demo": "demo",
    "demo_quality": "demo",
}
REASON_ALIASES = {
    "impact_reason": "impact", "why_impact": "impact",
    "meta_tooling_reason": "meta_tooling", "meta_ai_tooling_reason": "meta_tooling",
    "use_of_meta_ai_tooling_reason": "meta_tooling", "meta_reason": "meta_tooling",
    "technical_depth_reason": "technical_depth", "technical_reason": "technical_depth",
    "depth_reason": "technical_depth",
    "demo_reason": "demo", "why_demo": "demo",
}


class PanelError(RuntimeError):
    """Anything this tool refuses to do, with a message safe to print."""


# --------------------------------------------------------------------------- video and frames

def newest_nightly(folder=None):
    """The newest `nightly-*.mp4` under output\\demo\\, or None when there is none.

    Newest by modification time, which is what "tonight's video" means. The date in the name is not
    trusted for the choice: a run that re-recorded an older date is still the newest picture, and
    picking by name would score yesterday's file.
    """
    folder = folder or DEMO_DIR
    files = [path for path in glob.glob(os.path.join(folder, "nightly-*.mp4"))
             if os.path.isfile(path)]
    if not files:
        return None
    return max(files, key=lambda path: (os.path.getmtime(path), path))


def _ffmpeg(name):
    found = shutil.which(name)
    if not found:
        raise PanelError("%s is not on PATH, so a video cannot be sampled or measured" % name)
    return found


def probe_video(video):
    """Duration, size, frame rate and codec, read by ffprobe. Nothing is guessed.

    A value ffprobe does not report stays None, so the panel can say "not measured" instead of
    printing a number it made up.
    """
    probe = _ffmpeg("ffprobe")
    result = subprocess.run(
        [probe, "-v", "error", "-show_entries",
         "format=duration:stream=codec_name,width,height,r_frame_rate", "-of", "json", video],
        capture_output=True, encoding="utf-8", errors="replace", timeout=120)
    if result.returncode != 0:
        raise PanelError("ffprobe could not read %s: %s"
                         % (os.path.basename(video), (result.stderr or "").strip()[:200]))
    try:
        payload = json.loads(result.stdout or "{}")
    except ValueError:
        raise PanelError("ffprobe answered something that is not JSON for %s" % video)
    streams = payload.get("streams") or [{}]
    video_stream = next((s for s in streams if s.get("width")), streams[0])
    rate = str(video_stream.get("r_frame_rate") or "")
    fps = None
    if re.match(r"^\d+/\d+$", rate):
        num, den = (int(part) for part in rate.split("/"))
        fps = round(num / float(den), 2) if den else None
    try:
        duration = float((payload.get("format") or {}).get("duration"))
    except (TypeError, ValueError):
        duration = None
    return {"duration_s": duration, "width": video_stream.get("width"),
            "height": video_stream.get("height"), "fps": fps,
            "codec": video_stream.get("codec_name"), "frames": None}


def sample_frames(video, count=DEFAULT_FRAMES, folder=None):
    """Write `count` frames spread evenly across the video and measure each one.

    The sample times are the middle of `count` equal slices, so the first frame is not the black
    first frame of a fade and the last is not the closing fade either. Each frame is decoded exactly
    (`-ss` after `-i`), which is a full decode of a five megabyte file: measured on today's capture,
    six frames took well under a second each.

    A frame that comes out empty or all one colour is reported as `blank` with its share of the
    largest colour, because a near black frame in a demo is a finding, not a measurement error.
    """
    folder = folder or FRAME_DIR
    if not os.path.isdir(folder):
        os.makedirs(folder)
    info = probe_video(video)
    duration = info.get("duration_s")
    if not duration:
        raise PanelError("ffprobe reported no duration for %s, so no frame time can be chosen"
                         % os.path.basename(video))
    pixel_budget = eye_critic._env_int("PP_EYE_MAX_PIXELS", eye_critic.DEFAULT_MAX_PIXELS)
    width, height = info.get("width") or 0, info.get("height") or 0
    if width and height and width * height * count > pixel_budget:
        raise PanelError("%d frames at %dx%d is %.1f megapixels per request, over the %d pixel "
                         "ceiling; use --frames %d or fewer"
                         % (count, width, height, count * width * height / 1e6, pixel_budget,
                            max(1, pixel_budget // (width * height))))
    ffmpeg = _ffmpeg("ffmpeg")
    stem = os.path.splitext(os.path.basename(video))[0]
    rows = []
    for index in range(count):
        at = duration * (index + 0.5) / float(count)
        path = os.path.join(folder, "%s_f%02d.png" % (stem, index + 1))
        result = subprocess.run(
            [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
             "-i", video, "-ss", "%.3f" % at, "-frames:v", "1", path],
            capture_output=True, encoding="utf-8", errors="replace", timeout=300)
        if result.returncode != 0 or not os.path.exists(path):
            raise PanelError("ffmpeg could not take the frame at %.3f s from %s: %s"
                             % (at, os.path.basename(video), (result.stderr or "").strip()[:200]))
        facts = eye_critic.measure_image(path)
        share = facts.get("largest_colour_share")
        rows.append({"index": index + 1, "at_s": round(at, 3), "path": path,
                     "width": facts.get("width"), "height": facts.get("height"),
                     "colours": facts.get("colours"), "largest_colour_share": share,
                     "blank": (share is not None and share >= 0.90)})
    return rows, info


# --------------------------------------------------------------------------- the script it was planned from

def script_facts(video=None):
    """The caption and script text the panel is shown beside the frames.

    Three sources, each read for what it says about the picture on screen and nothing else:
      knowledge\\DEMO-SCRIPT.md  the six shot table (what each shot is supposed to show and the
                                  claim it proves) and every line that mentions a caption;
      knowledge\\DEMO-NIGHTLY.md the last line, which is the run's own record of checks and counts;
      output\\demo\\<stem>_verify.json  the run's measured duration, plan and any recorded failure.
    Each is optional: a missing file is reported as missing, never invented.
    """
    facts = {"script_path": None, "excerpt": "", "nightly_line": "", "verify_path": None,
             "verify": {}, "missing": []}

    if os.path.exists(SCRIPT_MD):
        with open(SCRIPT_MD, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
        # The shot table only, taken from its first header so the booth sheet copy of the same
        # rows (section 8) cannot appear twice, then the prose lines that say what the overlay
        # draws. A table row that happens to hold the word "caption" is not a caption.
        table, started = [], False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("| Shot"):
                started = True
            if started:
                if not stripped.startswith("|"):
                    break
                table.append(stripped)
        prose = [line.strip() for line in lines
                 if "caption" in line.lower() and not line.strip().startswith("|")
                 and len(line.strip()) > 40]
        picked = table[:9] + prose[:6]
        facts["script_path"] = SCRIPT_MD
        facts["excerpt"] = "\n".join(picked)[:2400]
    else:
        facts["missing"].append("knowledge\\DEMO-SCRIPT.md")

    if os.path.exists(NIGHTLY_LOG):
        with open(NIGHTLY_LOG, "r", encoding="utf-8", errors="replace") as handle:
            entries = [line.strip() for line in handle.read().splitlines()
                       if line.strip() and not line.startswith("#")]
        if entries:
            facts["nightly_line"] = entries[-1][:900]
    else:
        facts["missing"].append("knowledge\\DEMO-NIGHTLY.md")

    if video:
        verify = os.path.join(os.path.dirname(video),
                              "%s_verify.json" % os.path.splitext(os.path.basename(video))[0])
        if os.path.exists(verify):
            facts["verify_path"] = verify
            try:
                with open(verify, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                run = payload.get("run") or {}
                facts["verify"] = {"duration_s": payload.get("duration_s"),
                                   "planned_seconds": run.get("planned_seconds"),
                                   "recorded_seconds": run.get("recorded_seconds"),
                                   "has_audio": payload.get("has_audio"),
                                   "stream": payload.get("stream") or {},
                                   "failures": run.get("failures") or [],
                                   "ok": payload.get("ok"),
                                   # Card t_7450df91: the labelled Meta numbers travel with the measured
                                   # facts, so the panel reads a label and a receipt for each one.
                                   "meta_numbers": payload.get("meta_numbers") or [],
                                   "meta_numbers_why": payload.get("meta_numbers_why")}
            except (OSError, ValueError) as exc:
                facts["missing"].append("%s (unreadable: %s)" % (verify, exc))
        else:
            facts["missing"].append(os.path.basename(verify))
    return facts


DEMO_SECONDS = 180  # knowledge\DEMO-SCRIPT.md section 2: three minutes, 10,800 steps


def measured_lines(frames, info, script, video):
    """The measured half, as the prompt lines and the report lines both use.

    Every line here comes from the file or from ffprobe, not from the model, so it outranks an
    impression. Lines that could not be measured are stated as not measured.
    """
    lines = []
    if info.get("duration_s"):
        lines.append("Measured duration: %.3f s. The demo the script plans is %d s (three minutes), "
                     "so this capture is %s the judged length."
                     % (info["duration_s"], DEMO_SECONDS,
                        "inside" if abs(info["duration_s"] - DEMO_SECONDS) <= 20
                        else ("%.1f s short of" % (DEMO_SECONDS - info["duration_s"])
                              if info["duration_s"] < DEMO_SECONDS
                              else "%.1f s over" % (info["duration_s"] - DEMO_SECONDS))))
    else:
        lines.append("Duration: not measured.")
    if info.get("width") and info.get("height"):
        scale = info["width"] / 256.0 if info["width"] else None
        lines.append("Measured stream: %d x %d, %s fps, codec %s%s."
                     % (info["width"], info["height"], info.get("fps"),
                        info.get("codec") or "unknown",
                        ", which is %.0fx the 256 x 240 frame" % scale
                        if scale and abs(scale - round(scale)) < 0.01 else ""))
    if frames:
        times = ", ".join("%.1f s" % row["at_s"] for row in frames)
        lines.append("Frames shown to the panel: %d, taken at %s." % (len(frames), times))
        blanks = [row for row in frames if row.get("blank")]
        if blanks:
            lines.append("Measured: %d of the %d frames are one colour over at least 90 percent of "
                         "the picture (%s), which reads as a fade or a black screen."
                         % (len(blanks), len(frames),
                            ", ".join("%.1f s" % row["at_s"] for row in blanks)))
        else:
            lines.append("Measured: none of the %d frames is one colour over 90 percent of the "
                         "picture, so the capture has picture at every sample." % len(frames))
    else:
        lines.append("Frames: none sampled, so the panel has nothing to look at.")
    verify = script.get("verify") or {}
    if verify:
        bits = []
        if verify.get("planned_seconds") is not None:
            bits.append("the run planned %.1f s and recorded %.1f s"
                        % (verify["planned_seconds"], verify.get("recorded_seconds") or 0.0))
        bits.append("audio is %s" % ("present" if verify.get("has_audio") else "absent"))
        lines.append("From the capture's own verify file: %s." % "; ".join(bits))
        # Card t_7450df91: the panel is shown the labels, not the numbers alone, so it can tell a measured
        # count from a reading of the plan and can say which one it is scoring.
        meta = verify.get("meta_numbers") or []
        for row in meta:
            if not isinstance(row, dict):
                continue
            lines.append("Labelled Meta number: %s is %s, labelled %s, receipt %s."
                         % (row.get("name"), row.get("value"), row.get("label"), row.get("receipt")))
        if meta:
            lines.append("Every Meta number above carries one of three labels (measured, computed or "
                         "inferred) and a receipt in data/receipts/meta_receipts.jsonl, so no Meta number "
                         "in this capture is a number a reader has to take on trust.")
        elif verify.get("meta_numbers_why"):
            lines.append("The capture's verify file labels no Meta number: %s." % verify["meta_numbers_why"])
        else:
            lines.append("The capture's verify file labels no Meta number, so nothing in it says which "
                         "Meta figures were measured, computed or inferred.")
        for failure in (verify.get("failures") or [])[:4]:
            lines.append("Recorded failure in that run: %s." % failure)
    if script.get("nightly_line"):
        lines.append("The nightly log's own last row, verbatim: %s" % script["nightly_line"])
    if script.get("missing"):
        lines.append("Not available for this run: %s." % ", ".join(script["missing"]))
    lines.append("The frames are stills from an h264 capture, so their colour counts include the "
                 "encoder's own colours and are not a PPU palette measurement; this panel judges "
                 "what the frames show, not legal 2C02 colours.")
    return lines


# --------------------------------------------------------------------------- prompt

def judge_prompt(frames, info, script, measured=None):
    """The judging prompt: the hackathon rubric, the measured facts, then the machine readable ask."""
    measured = measured if measured is not None else measured_lines(frames, info, script, None)
    criteria_text = "\n".join(
        "- %s, weight %d of 100: %s." % (label, weight, text)
        for _key, label, weight, text in CRITERIA)
    lines = [
        "You are a judge for a Meta AI developer hackathon. You are shown %d still frames sampled "
        "evenly from the newest nightly capture of an original NES style game in development, plus "
        "an excerpt of the script it was planned from. Judge what a judge could actually see: the "
        "3 minute video, the README and the repository. Anything you cannot see, say you cannot "
        "see." % len(frames),
        "",
        "The four criteria and their weights, from the submission's own plan:",
        criteria_text,
        "",
        "The rule the team works to: would a judge see it in the 3 minute video, the README or the "
        "repo? A feature nobody can see in those three places earns nothing, however good it is.",
        "",
        "Measured facts about this exact capture, taken from the file and from the run's own "
        "records. These outrank your impression:",
    ]
    lines += ["- " + line for line in measured]
    excerpt = (script or {}).get("excerpt") or ""
    if excerpt:
        lines += ["", "The demo script this capture was planned from (shot table rows and caption "
                      "rows, verbatim):", "", excerpt]
    lines += [
        "",
        "Answer in this order.",
        "",
        "### What the video shows",
        "One short paragraph: what a judge sees, in order, from the frames alone. Name what is "
        "missing that a 3 minute demo would need (for example a person talking to the game, a "
        "verdict on screen, a before and after, a title card that says what this is).",
        "",
        "### The four scores",
        "For each criterion, one line: the label, a score from 1 (bad) to 10 (excellent), and ONE "
        "reason, concrete and tied to something visible or measurable. Do not average, do not "
        "round to be kind, and do not score a criterion you cannot judge: say so instead.",
        "",
        "### Five fixes, ranked",
        "Exactly five numbered fixes, most valuable first. Each one must be a change a worker can "
        "start today and a judge could see in the 3 minute video, the README or the repo. For each: "
        "a title under 80 characters, the criterion it raises, the lane that should own it (one of "
        "%s), and a body of two to four sentences that names the file or scene to change, what to "
        "change, and how a reader will see it in the video." % ", ".join(LANES),
        "",
        "### Machine readable block",
        "End the reply with exactly one fenced json block, these keys and nothing after it:",
        "```json",
        '{"impact": 6, "impact_reason": "...", "meta_tooling": 5, "meta_tooling_reason": "...", '
        '"technical_depth": 7, "technical_depth_reason": "...", "demo": 4, "demo_reason": "...", '
        '"fixes": [{"title": "...", "criterion": "Impact", "lane": "gamedev", '
        '"body": "..."}]}',
        "```",
        "The scores are integers from 1 to 10. The fixes array must hold exactly five entries, in "
        "the order you ranked them, and every body must be ready to paste into a task card as it "
        "stands: plain sentences, no headings, no bullet points, no em dashes or en dashes.",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- parsing

def _normalise_key(text):
    return re.sub(r"[^a-z0-9]+", "_", str(text or "").strip().lower()).strip("_")


def _clamp(value):
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    if number < SCORE_MIN or number > SCORE_MAX:
        return None
    return number


def parse_panel(text):
    """Scores, reasons and fixes out of the model's answer.

    A score with no reason is kept as a score and flagged, because a number without a reason is
    not what the card asked for and the panel must say which row is incomplete rather than fill the
    reason in. A score that is absent, or outside 1 to 10, is None (NOT JUDGED), never a default.
    """
    payload = eye_critic._last_json_object(text)
    scores = {key: None for key in WEIGHTS}
    reasons = {key: "" for key in WEIGHTS}
    reasons_block = payload.get("reasons") if isinstance(payload.get("reasons"), dict) else {}

    for key, value in (payload or {}).items():
        if isinstance(value, (dict, list)):
            continue
        name = SCORE_ALIASES.get(_normalise_key(key))
        if name and scores.get(name) is None:
            number = _clamp(value)
            if number is not None:
                scores[name] = number
        reason_key = REASON_ALIASES.get(_normalise_key(key))
        if reason_key and isinstance(value, str) and value.strip() and not reasons[reason_key]:
            reasons[reason_key] = value.strip()
    for key, value in reasons_block.items():
        name = SCORE_ALIASES.get(_normalise_key(key))
        if name and isinstance(value, str) and value.strip() and not reasons[name]:
            reasons[name] = value.strip()

    # Fall back to the human readable lines: "<label>: 6/10, because ...".
    for key, label, _weight, _text in CRITERIA:
        if scores[key] is not None and reasons[key]:
            continue
        match = re.search(re.escape(label) + r"[^0-9\n]{0,40}?(\d{1,2})\s*(?:/|out of)\s*10"
                          r"([^\n]{0,400})", text or "", re.I)
        if not match:
            continue
        if scores[key] is None:
            scores[key] = _clamp(match.group(1))
        if not reasons[key]:
            tail = match.group(2).strip(" .,:;")
            reasons[key] = re.sub(r"^(because|since|as)\s+", "", tail, flags=re.I).strip()

    fixes = []
    for item in (payload.get("fixes") or []):
        if isinstance(item, dict):
            title = str(item.get("title") or item.get("name") or "").strip()
            body = str(item.get("body") or item.get("card") or item.get("text") or "").strip()
            lane = _normalise_key(item.get("lane") or item.get("owner") or "")
            criterion = str(item.get("criterion") or item.get("axis") or "").strip()
            if title or body:
                fixes.append({"title": title, "body": body, "lane": lane,
                              "criterion": criterion})
        elif isinstance(item, str) and item.strip():
            fixes.append({"title": item.strip()[:80], "body": item.strip(), "lane": "",
                          "criterion": ""})
    dropped = max(0, len(fixes) - MAX_FIXES)
    fixes = fixes[:MAX_FIXES]
    for index, fix in enumerate(fixes):
        fix["priority"] = FIX_PRIORITY[index] if index < len(FIX_PRIORITY) else FIX_PRIORITY[-1]
        fix["lane_raw"] = fix["lane"]
        fix["lane"] = LANE_ALIASES.get(fix["lane"], "")
    return {"scores": scores, "reasons": reasons, "fixes": fixes, "dropped_fixes": dropped,
            "weighted": weighted_total(scores)}


def weighted_total(scores):
    """score / 10 * weight for every criterion that has a score, out of 100.

    Computed here, never taken from the model: a model that adds its own weights wrong would
    otherwise hand the team a total nobody can reproduce. A missing score contributes nothing and
    is reported as missing, so a partial panel cannot read as a low total.
    """
    total = 0.0
    counted = 0
    for key, _label, weight, _text in CRITERIA:
        score = (scores or {}).get(key)
        if score is None:
            continue
        total += score / 10.0 * weight
        counted += 1
    return {"points": round(total, 1), "of": 100, "criteria_scored": counted,
            "complete": counted == len(CRITERIA)}


def measured_disagreements(parsed, frames, info):
    """Where the panel's own sentences contradict a number measured from the file.

    Two checks, both mechanical, because both are ways this panel could mislead the team:
      * a reason that reads the capture as blank or frozen, when the measured sample says which
        frames are one colour and how many are not;
      * a reason that quotes a duration for the video which is not the measured duration.

    A disagreement is printed beside the score it belongs to, not instead of it: the panel's
    judgement stands, and the measured number is what a reader should act on.
    """
    notes = []
    reasons = (parsed or {}).get("reasons") or {}
    blanks = [row for row in frames if row.get("blank")]
    times = ", ".join("%.1f s" % row["at_s"] for row in blanks) or "none"
    if re.search(r"blank|black|frozen|freeze|static|stuck on", " ".join(reasons.values()), re.I):
        if blanks:
            notes.append("the panel reads the picture as blank or frozen; measured, %d of %d "
                         "sampled frames are one colour over 90 percent (%s), and the other %d are "
                         "lit, so a sentence about the whole capture being static is stronger than "
                         "the sample supports."
                         % (len(blanks), len(frames), times, len(frames) - len(blanks)))
        else:
            notes.append("the panel reads the picture as blank or frozen; measured, none of the %d "
                         "sampled frames is one colour over 90 percent, so the picture was lit at "
                         "every sample." % len(frames))
    duration = (info or {}).get("duration_s")
    if duration:
        for reason in reasons.values():
            for match in re.finditer(r"(?:runs for|lasts|duration of|length of|only)\s*(?:about\s*)?"
                                     r"(\d+(?:\.\d+)?)\s*(?:seconds|secs|s)\b", reason or "",
                                     re.I):
                quoted = float(match.group(1))
                if abs(quoted - duration) > 1.5:
                    notes.append("the panel quotes the capture as %s s; measured, it is %.3f s."
                                 % (match.group(1), duration))
                    break
    return notes


UNKNOWN_PATH_PATTERN = re.compile(
    r"[A-Za-z0-9_.\\/-]+\.(?:py|gml|yy|json|md|ogg|wav|png|mp4|txt|csv)")


def unknown_paths(body, limit=6):
    """File paths a card body names that this repository does not have at that place.

    The panel cannot browse the repository, so a body like "update scenes/walk.py" may name a file
    that does not exist, and a worker would spend its run looking for it. Every path-shaped token is
    checked against the tree and against tools\\; the ones that are absent are named beside the fix,
    so the body is read as a direction to find the real file, not as a location.
    """
    found = []
    for token in UNKNOWN_PATH_PATTERN.findall(str(body or "")):
        candidate = token.strip(".,;:()[]`\"'")
        if "/" not in candidate and "\\" not in candidate:
            continue
        if os.path.exists(os.path.join(ROOT, candidate)) or \
                os.path.exists(os.path.join(TOOLS_DIR, candidate)):
            continue
        if candidate not in found:
            found.append(candidate)
        if len(found) >= limit:
            break
    return found



# --------------------------------------------------------------------------- card bodies

def _clean_body(text):
    """A card body that can be pasted as it stands: no long dashes, no stray markdown headings."""
    body = eye_critic._plain_dashes(str(text or ""))
    body = re.sub(r"^#+\s*", "", body, flags=re.MULTILINE)
    body = re.sub(r"^\s*[-*]\s+", "", body, flags=re.MULTILINE)
    return " ".join(body.split())


def card_bodies(fixes, date, folder=None):
    """Write one paste-ready body file per fix, and return the manifest rows.

    Writing the body to a file is what makes "ready to paste" checkable: the balancer and the
    manager both create cards with `--body-file`, so the file the panel wrote is the file a card
    would carry, not a copy of it.
    """
    folder = folder or os.path.join(CARD_DIR, date)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    rows = []
    for index, fix in enumerate(fixes):
        path = os.path.join(folder, "fix-%02d.md" % (index + 1))
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(_clean_body(fix["body"]))
        rows.append({"index": index + 1, "title": eye_critic._plain_dashes(fix["title"]),
                     "lane": fix["lane"], "lane_raw": fix.get("lane_raw") or "",
                     "priority": fix["priority"],
                     "criterion": fix["criterion"], "body_path": path,
                     "unknown_paths": unknown_paths(fix["body"]),
                     "body": _clean_body(fix["body"])})
    return rows, folder


def paste_command(row):
    lane = row["lane"] or "UNASSIGNED"
    return ("hermes kanban --board nayil-ops create --created-by judge-panel --assignee %s "
            "--priority %d --body-file \"%s\" \"%s\""
            % (lane, row["priority"], row["body_path"], row["title"]))


# --------------------------------------------------------------------------- the model and the key

def meta_backend():
    """True when this run sends through tools\\meta_client.py instead of the Gemini endpoint."""
    return os.environ.get("PP_AI_BACKEND", "").strip().lower() == "meta"


def active_chain():
    """The models to walk for the chosen backend: one Meta judge model, or the gemini rotation."""
    return META_CHAIN if meta_backend() else MODEL_CHAIN


def chain_note(chain=None):
    """The measured sentence that belongs beside the chain this run actually used."""
    chain = tuple(chain or active_chain())
    return META_CHAIN_NOTE if chain == META_CHAIN else CHAIN_NOTE


def load_meta_key_from_user_environment():
    """Put the Windows user environment's Meta key into os.environ, without printing it.

    The same registry read as `tools\\eye_drive.py`'s Gemini loader, for MODEL_API_KEY then
    META_API_KEY, because `meta_client` reads only os.environ and a worker shell is often spawned
    before `setx` reaches it. HKCU\\Environment is the environment, not a key file, and the value
    never leaves this function except into os.environ. Returns (place, env name) or (None, None).
    """
    for name in META_KEY_ENVS:
        if os.environ.get(name, "").strip():
            return "environment", name
    try:
        import winreg
    except ImportError:
        return None, None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as handle:
            found = {}
            index = 0
            while True:
                try:
                    name, value, kind = winreg.EnumValue(handle, index)
                except OSError:
                    break
                index += 1
                found[str(name).upper()] = (value, kind)
    except OSError:
        return None, None
    for want in META_KEY_ENVS:
        if want not in found:
            continue
        value, kind = found[want]
        if kind == winreg.REG_EXPAND_SZ and "%" in str(value):
            value = os.path.expandvars(value)
        value = str(value or "").strip()
        if value:
            os.environ[want] = value
            return "user environment", want
    return None, None


def meta_runs_today(path=None, now=None):
    """How many billed calls THIS tool made today, in UTC, from the eye ledger.

    Counted from the ledger rather than from a file this tool keeps: a run that sent the request and
    then failed still spent credits, and its ledger row is written at that moment. Only rows with
    role `judge-panel` and the judge model count: other lanes run muse-spark on the same ledger for
    eye reviews (measured 2026-10-27 00:42, two `review` rows), and their spend is not this
    tool's ceiling, so counting them would refuse the panel for another lane's calls.
    """
    import datetime
    now = now or time.time()
    day = datetime.datetime.fromtimestamp(now, datetime.timezone.utc).date()
    count = 0
    for row in eye_critic._call_rows(path):
        if str(row.get("role") or "") != "judge-panel":
            continue
        if str(row.get("model") or "") not in META_CHAIN:
            continue
        seconds = eye_critic._parse_stamp(str(row.get("at", "")))
        if seconds is None:
            continue
        if datetime.datetime.fromtimestamp(seconds, datetime.timezone.utc).date() == day:
            count += 1
    return count


def meta_budget_refusal(limit=None, path=None, now=None):
    """The sentence that refuses a billed call over the day's ceiling, or None when it fits."""
    limit = (limit if limit is not None
             else eye_critic._env_int(META_CALLS_PER_DAY_ENV, META_CALLS_PER_DAY_DEFAULT))
    if not limit:
        return None
    used = meta_runs_today(path, now)
    if used < limit:
        return None
    return ("%d billed Meta panel call(s) are already recorded today and the ceiling is %d (%s), "
            "so this run sent nothing. Raise the ceiling or wait for the next UTC day."
            % (used, limit, META_CALLS_PER_DAY_ENV))


def panel_gate():
    """The rate gate for this run's backend.

    eye_critic's gate counts every row in `data\\eye_ledger.csv` against the Gemini free tier's 20 a
    day. That budget belongs to Gemini: a Meta call is billed, served by a different API with its
    own RPM, and refusing it because Gemini's quota is spent would drop the night the manager asked
    for. The Meta ceiling is `meta_budget_refusal()` and meta_client keeps its own RPM gate, so the
    gate is off only for the billed path, and never for the free tier it was written for.
    """
    if meta_backend():
        return eye_critic.RateGate(per_minute=0, per_day=0)
    return eye_critic.RateGate()


def _meta_error_class():
    """meta_client's own exception base, or None when the Meta path is not in play."""
    if not meta_backend():
        return None
    try:
        import meta_client
    except ImportError:
        return None
    return getattr(meta_client, "MetaError", None)


# --------------------------------------------------------------------------- the call

def ask_panel(frames, info, script, chain=None, gate=None, log=None):
    """One request with every frame in it, walking the model chain on a refusal.

    Every sampled frame goes in ONE request, because the free tier is capped per request and not
    per image: six frames in six requests would cost six times the budget for the same judgement.
    A per-day refusal or a 503 moves to the next model in the chain, which is the behaviour
    `tools\\eye_drive.py` proved on 2026-10-24 and this tool inherits rather than re-proving.
    On the Meta path the chain is one billed model and meta_client raises its own `MetaError`
    family, which is caught here as an error attempt so the panel says what happened instead of
    dying with a traceback.
    """
    chain = chain or active_chain()
    gate = gate or panel_gate()
    log = log if log is not None else []
    measured = measured_lines(frames, info, script, None)
    prompt = judge_prompt(frames, info, script, measured=measured)
    parts = [{"text": prompt}]
    for row in frames:
        parts += eye_critic.inline_part(row["path"])
    payload = {"contents": [{"role": "user", "parts": parts}]}
    attempts = []
    for model in chain:
        gate.before_call()
        started = eye_critic.utc_now()
        try:
            data, _retries = eye_critic.post_generate(model, payload)
            text, usage = eye_critic.read_response(data)
        except (eye_critic.DailyLimit, eye_critic.RateLimited) as exc:
            detail = eye_critic.redact(str(exc))[:200]
            attempts.append({"model": model, "outcome": "refused", "detail": detail})
            eye_critic.append_ledger({"at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                      "file": frames[0]["path"] if frames else "",
                                      "role": "judge-panel", "model": model,
                                      "status": "rate_limited"})
            log.append("%s refused on quota, moving to the next model (%s)" % (model, detail))
            continue
        except eye_critic.EyeError as exc:
            detail = eye_critic.redact(str(exc))[:200]
            attempts.append({"model": model, "outcome": "error", "detail": detail})
            eye_critic.append_ledger({"at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                      "file": frames[0]["path"] if frames else "",
                                      "role": "judge-panel", "model": model, "status": "error"})
            log.append("%s answered with an error, moving to the next model (%s)" % (model, detail))
            continue
        except Exception as exc:  # noqa: BLE001 - only the Meta client's own errors are handled
            meta_error = _meta_error_class()
            if meta_error is None or not isinstance(exc, meta_error):
                raise
            detail = eye_critic.redact(str(exc))[:200]
            attempts.append({"model": model, "outcome": "error", "detail": detail})
            eye_critic.append_ledger({"at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                      "file": frames[0]["path"] if frames else "",
                                      "role": "judge-panel", "model": model, "status": "error"})
            log.append("%s answered with an error, moving to the next model (%s)" % (model, detail))
            continue
        attempts.append({"model": model, "outcome": "answered"})
        eye_critic.append_ledger({
            "at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "file": frames[0]["path"] if frames else "", "role": "judge-panel", "model": model,
            "seconds": "", "status": "ok"})
        return {"text": text, "model": model, "attempts": attempts,
                "tokens": "%s in / %s out" % ((usage or {}).get("promptTokenCount", "?"),
                                              (usage or {}).get("candidatesTokenCount", "?")),
                "prompt": prompt, "measured": measured}
    raise PanelError("no model in the chain answered: %s"
                     % "; ".join("%s %s" % (a["model"], a["outcome"]) for a in attempts))


# --------------------------------------------------------------------------- the panel file

def render_panel(video, info, frames, script, result, parsed, cards, log, key_source, date,
                 attempts, dropped, chain=None, inbox=None):
    """The JUDGE-PANEL markdown: the run, the four scores, the five fixes, the measured half."""
    chain = tuple(chain or MODEL_CHAIN)
    total = parsed["weighted"]
    lines = ["# JUDGE-PANEL %s: what a judge would mark down" % date, "",
             "Card t_70840bce (W4 JUDGE-PANEL), testing lane. Rubric from",
             "`../arananet/meta-hackathon/WIN-PLAN-2026-10-26.md` line 3: Impact 30, Use of Meta AI",
             "tooling 25, Technical depth 20, Demo 25. Submission Nov 4, 9 PM ET.",
             "",
             "## The run", "",
             "- tool: `tools\\judge_panel.py`, which sends through `tools\\eye_critic.py` "
             "(`post_generate`, `RateGate`, `inline_part`, `redact`) and reads the key through "
             "`tools\\eye_drive.py`'s loader or this tool's Meta loader; neither transport was "
             "reimplemented here.",
             "- backend: %s%s"
             % (os.environ.get("PP_AI_BACKEND", "gemini").strip().lower() or "gemini",
                ", which hands the same payload to `tools\\meta_client.py` and records the answer "
                "in `data\\ai_cache`" if meta_backend() else ", the Gemini generateContent endpoint"),
             "- video judged: `%s`" % _rel(video),
             "- frames: %d, taken at %s, kept in `%s`"
             % (len(frames), ", ".join("%.1f s" % row["at_s"] for row in frames),
                _rel(FRAME_DIR)),
             "- model chain, in order: %s; %s"
             % (", ".join("`%s`" % m for m in chain), chain_note(chain)),
             "- model that answered: %s" % (("`%s`" % result["model"]) if result else
                                            "none: the measured half ran alone"),
             ]
    if attempts:
        lines.append("- attempts in this run: %s"
                     % ", ".join("%s %s" % (a["model"], a["outcome"]) for a in attempts))
    lines += ["- credential: %s, never printed and never written to this file"
              % (key_source or "absent, so no model was called"),
              "- the five drafts are also appended to `%s` for the manager"
              % _rel(inbox or INBOX),
              "- warning: %s" % WARNING,
              "",
              "## The score card", "",
              "| criterion | weight | score | points | one reason |",
              "| --- | --- | --- | --- | --- |"]
    for key, label, weight, _text in CRITERIA:
        score = parsed["scores"].get(key)
        points = round(score / 10.0 * weight, 1) if score is not None else 0.0
        reason = parsed["reasons"].get(key) or ("**no reason was given, which is a gap in the "
                                                "panel, not a zero**" if score is not None
                                                else "**NOT JUDGED: the panel gave no score**")
        lines.append("| %s | %d | %s | %s | %s |"
                     % (label, weight, score if score is not None else "NOT JUDGED",
                        ("%.1f" % points) if score is not None else "-",
                        eye_critic._plain_dashes(reason)))
    lines += ["",
              "Weighted total: **%.1f of %d** (%d of the 4 criteria scored).%s"
              % (total["points"], total["of"], total["criteria_scored"],
                 "" if total["complete"] else " A total with a criterion missing is a floor, not a "
                                              "score: the missing criterion would only add points."),
              "",
              "Computed as score / 10 * weight for each criterion, by this tool and not by the "
              "model, so the total can be reproduced from the table above.",
              ""]

    disagreements = measured_disagreements(parsed, frames, info)
    if disagreements:
        lines += ["### Where the panel's words disagree with a measured number", ""]
        lines += ["- %s" % eye_critic._plain_dashes(note) for note in disagreements]
        lines += ["", "The score beside a sentence like this still stands as the panel's judgement. "
                      "The measured number is what a reader should act on.", ""]

    lines += ["## The top five fixes, each a card body ready to paste", ""]
    if dropped:
        lines.append("The panel offered %d more fix(es) than the card allows. They are dropped "
                     "here on purpose: the rule is no more than five cards a night, and a list of "
                     "six would quietly become six cards." % dropped)
        lines.append("")
    if not cards:
        lines += ["No fix was parsed out of the panel's answer. That is a finding about the answer, "
                  "not about the game: the machine readable block was missing or unreadable, and "
                  "the panel text above is the only record of what it said.", ""]
    for row in cards:
        lines += ["### Fix %d: %s" % (row["index"], row["title"] or "(untitled)"), "",
                  "- lane: %s" % (row["lane"] or
                                  "**UNASSIGNED: the panel said `%s`, which is not a lane this "
                                  "fleet runs, so a human or the manager must pick one**"
                                  % (row.get("lane_raw") or "nothing")),
                  "- priority: %d (the panel's order, so fix 1 is dispatched first)" % row["priority"],
                  "- criterion it raises: %s" % (row["criterion"] or "not named"),
                  "- body file: `%s`" % _rel(row["body_path"])]
        if row.get("unknown_paths"):
            lines.append("- paths the body names that are not in this repository at that place: %s. "
                         "The body is a direction, not a location: find the real file before "
                         "editing anything."
                         % ", ".join("`%s`" % path for path in row["unknown_paths"]))
        lines += ["", "Body, as the file holds it:", "",
                  "```text", row["body"], "```", "",
                  "Paste:", "", "```text", paste_command(row), "```", ""]
    if cards:
        lines += ["This tool creates no cards. Five bodies are written and the command above is "
                  "the whole of what a card needs, so the limit of five a night cannot be broken "
                  "by running it twice: a second run writes the same five files again and creates "
                  "nothing.", ""]

    lines += ["## What the panel was shown, measured", ""]
    lines += ["- %s" % eye_critic._plain_dashes(line)
              for line in measured_lines(frames, info, script, video)]
    lines += ["",
              "The model's impression is not in this section and does not outrank it. Where the two "
              "disagree, these numbers win.", ""]

    if (script.get("excerpt") or "").strip():
        lines += ["## The script excerpt it judged against", "",
                  "From `%s`, verbatim:" % _rel(SCRIPT_MD), "",
                  "```text", script["excerpt"], "```", ""]

    if log:
        lines += ["## Model fallbacks taken in this run", ""]
        lines += ["- %s" % line for line in log]
        lines.append("")
    if result and result.get("tokens"):
        lines += ["## Cost", "",
                  "- tokens reported by the API: %s" % result["tokens"],
                  "- calls: %d (one request carrying all %d frames, plus %d refused model(s))"
                  % (1 + len([a for a in attempts if a["outcome"] != "answered"]), len(frames),
                     len([a for a in attempts if a["outcome"] != "answered"])),
                  ]
        if result.get("model") in META_CHAIN:
            lines += ["- billed: this call ran on the Meta Model API and is charged to the team's "
                      "credits, so it is not free and the token count above is the spend's shape.",
                      "- recorded for replay: the answer is in `data\\ai_cache` (meta_client record "
                      "mode), so the same panel can be played with `PP_AI_MODE=replay` and no key.",
                      "- the ledger row is in `data\\eye_ledger.csv` with role `judge-panel`, and "
                      "that row is what the tool's own %d calls a day ceiling counts."
                      % eye_critic._env_int(META_CALLS_PER_DAY_ENV, META_CALLS_PER_DAY_DEFAULT),
                      ""]
        else:
            lines += ["- the free tier is free: this run spent no money, and the ledger row is in "
                      "`data\\eye_ledger.csv` with role `judge-panel` so the daily budget counts it.",
                      ""]

    current = (panel_row(date, video, result, parsed, frames)
               if result and parsed["weighted"]["criteria_scored"] else None)
    lines += render_trend(read_panel_ledger(), current)

    lines += ["## Sources", "",
              "- judging weights and the deadline: `../arananet/meta-hackathon/WIN-PLAN-2026-10-26.md`"
              " line 3, read 2026-10-26",
              "- the judge model, the inbox and the cache rule: manager comment on card t_70840bce,"
              " 2026-10-26 17:15",
              "- the Meta API shape, its record and replay modes: `tools/meta_client.py` header,"
              " read 2026-10-26",
              "- the three minute demo and its six shots: `knowledge/DEMO-SCRIPT.md` sections 1 and 2,"
              " read 2026-10-26",
              "- free tier ceiling of 20 requests per project per model per day: "
              "`tools/eye_critic.py` header, measured 2026-10-22",
              "- model rotation on a per day refusal: `tools/eye_drive.py`, measured 2026-10-24",
              "- the capture's own numbers: `%s`" % (_rel(script["verify_path"])
                                                    if script.get("verify_path") else
                                                    "none present for this video"),
              ""]
    return "\n".join(_no_long_dashes_per_line(lines))


def _no_long_dashes_per_line(lines):
    out = []
    for line in lines:
        fixed = line
        for dash in ("\u2014", "\u2015", "\u2013", "\u2212", "\u2011"):
            fixed = fixed.replace(dash, "-")
        out.append(fixed)
    return out


def _rel(path, start=None):
    """A path relative to the repository, or the absolute path when it sits on another drive.

    `os.path.relpath` raises ValueError across Windows drives, and a test or a rerun that writes the
    card bodies into a temporary folder must still render a panel rather than crash on the label.
    """
    try:
        return os.path.relpath(path, start or ROOT).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def panel_path(date, folder=None):
    return os.path.join(folder or KNOWLEDGE, "JUDGE-PANEL-%s.md" % date)


# --------------------------------------------------------------------------- the trend

PANEL_LEDGER = os.path.join(OUTPUT, "judge_panel_ledger.csv")
PANEL_LEDGER_COLUMNS = ("at", "date", "video", "model", "impact", "meta_tooling",
                        "technical_depth", "demo", "points", "frames")
TREND_ROWS = 6


def read_panel_ledger(path=None):
    """Every finished panel, newest last. One row per run, because a nightly number is only worth
    something when the nights can be put beside each other."""
    import csv
    path = path or PANEL_LEDGER
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def append_panel_ledger(row, path=None):
    """Append one row to the panel ledger, header written once."""
    import csv
    path = path or PANEL_LEDGER
    folder = os.path.dirname(os.path.abspath(path))
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    fresh = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PANEL_LEDGER_COLUMNS)
        if fresh:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in PANEL_LEDGER_COLUMNS})
    return path


def panel_row(date, video, result, parsed, frames):
    return {"at": eye_critic.utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"), "date": date,
            "video": _rel(video),
            "model": (result or {}).get("model") or "none",
            "impact": parsed["scores"].get("impact") or "",
            "meta_tooling": parsed["scores"].get("meta_tooling") or "",
            "technical_depth": parsed["scores"].get("technical_depth") or "",
            "demo": parsed["scores"].get("demo") or "",
            "points": parsed["weighted"]["points"] if parsed["weighted"]["criteria_scored"]
            else "",
            "frames": len(frames)}


def render_trend(history, current, path=None):
    """The last few panels as a table, plus the warning that makes them comparable.

    Two runs of the same capture on two models scored 19.0 and 46.5 on 2026-10-26 (gemini-3.5-flash
    then gemini-3.5-flash-lite, the second one after the first two models hit the daily cap), which
    is the reason this table names the model on every row: a nightly number is a trend only when the
    same model answered, and a change of model is a change of instrument.
    """
    rows = list(history or [])[-TREND_ROWS:]
    if current:
        rows.append(current)
    if not rows:
        return []
    lines = ["## Across nights", "",
             "| date, run | model | impact | meta | depth | demo | points | video |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in rows:
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s |"
                     % (row.get("at") or row.get("date"), row.get("model"),
                        row.get("impact") or "-", row.get("meta_tooling") or "-",
                        row.get("technical_depth") or "-", row.get("demo") or "-",
                        row.get("points") or "-", row.get("video") or "-"))
    models = {str(row.get("model") or "") for row in rows}
    lines += ["", "The ledger behind this table is `%s`, one row per run."
              % _rel(path or PANEL_LEDGER)]
    if len(models) > 1:
        lines.append("**The model changed inside this table (%s).** A panel score is comparable "
                     "across nights only when the same model answered: a change comes from a "
                     "free-tier daily cap on the Gemini chain or from the team switching the judge "
                     "model, and a different model scores the same capture differently. Read the "
                     "direction only where the model column matches, and read a change of model as "
                     "a change of instrument."
                     % ", ".join(sorted(model for model in models if model)))
    # The spread of the same capture on the same model is the noise floor of this instrument, and
    # it is measured here rather than assumed: a single night's total is not a trend on its own.
    groups = {}
    for row in rows:
        try:
            groups.setdefault((row.get("model"), row.get("video")), []).append(float(row["points"]))
        except (KeyError, TypeError, ValueError):
            continue
    for (model, video), points in groups.items():
        if len(points) < 2 or max(points) - min(points) < 3.0:
            continue
        lines.append("**The same capture on the same model scored %s (a spread of %.1f points).** "
                     "That spread is this instrument's own noise on one night, so a single run's "
                     "total is not a trend: compare the direction across several nights, and treat "
                     "a move smaller than about %.0f points as no move at all."
                     % (", ".join("%.1f" % point for point in points),
                        max(points) - min(points), max(points) - min(points)))
    lines.append("")
    return lines


# --------------------------------------------------------------------------- self test

def self_test(folder=None):
    """Prove the rotation: the first model answers a per-day 429, the next one answers the rubric.

    Nothing leaves this process. `eye_critic._urlopen` is replaced, the ledger and results file are
    redirected into a scratch folder, and the key is a placeholder, so a real credential is not
    needed to prove a fallback. This is the same proof `tools\\eye_drive.py --self-test` carries,
    run again here because a rotation this tool inherits is only worth what its own run shows.
    """
    folder = folder or os.path.join(OUTPUT, "_judge_panel_selftest")
    frames = []
    if os.path.isdir(FRAME_DIR):
        frames = [{"index": 1, "at_s": 0.0, "path": path}
                  for path in sorted(glob.glob(os.path.join(FRAME_DIR, "*.png")))[:1]]
    if not frames:
        raise PanelError("run the panel once first, so there is a frame to send: %s is empty"
                         % FRAME_DIR)
    refused, answered = MODEL_CHAIN[0], MODEL_CHAIN[1]
    saved = {"transport": eye_critic._urlopen,
             "env": {name: os.environ.get(name) for name in
                     ("PP_EYE_LEDGER", "PP_EYE_RESULTS", eye_critic.KEY_ENV, "PP_AI_BACKEND")}}
    answer = {"candidates": [{"content": {"parts": [{"text":
              "### Machine readable block\n```json\n"
              '{"impact": 6, "impact_reason": "one", "meta_tooling": 5, "meta_tooling_reason": "two", '
              '"technical_depth": 7, "technical_depth_reason": "three", "demo": 4, '
              '"demo_reason": "four", "fixes": ['
              '{"title": "a", "lane": "gamedev", "body": "a"}, '
              '{"title": "b", "lane": "gamedev", "body": "b"}, '
              '{"title": "c", "lane": "gamedev", "body": "c"}, '
              '{"title": "d", "lane": "gamedev", "body": "d"}, '
              '{"title": "e", "lane": "gamedev", "body": "e"}]}\n```'}]},
              "finishReason": "STOP"}],
              "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 10}}

    def fake_transport(request, timeout=None):
        if "/models/%s:" % refused in request.full_url:
            raise urllib.error.HTTPError(request.full_url, 429, "quota", {},
                                         io.BytesIO(eye_drive.QUOTA_BODY.encode("utf-8")))
        return _FakeResponse(answer)

    if not os.path.isdir(folder):
        os.makedirs(folder)
    os.environ["PP_EYE_LEDGER"] = os.path.join(folder, "ledger.csv")
    os.environ["PP_EYE_RESULTS"] = os.path.join(folder, "results.jsonl")
    os.environ[eye_critic.KEY_ENV] = "self-test-placeholder"
    os.environ.pop("PP_AI_BACKEND", None)
    eye_critic._urlopen = fake_transport
    try:
        gate = eye_critic.RateGate(path=os.environ["PP_EYE_LEDGER"], per_minute=0, per_day=0)
        log = []
        result = ask_panel(frames, {"duration_s": 1.0, "width": 256, "height": 240, "fps": 60.0,
                                    "codec": "h264"}, {}, chain=(refused, answered), gate=gate,
                           log=log)
    finally:
        eye_critic._urlopen = saved["transport"]
        for name, value in saved["env"].items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    if result["model"] != answered:
        raise PanelError("self test FAILED: expected the chain to answer on %s, it answered on %s"
                         % (answered, result["model"]))
    parsed = parse_panel(result["text"])
    if parsed["weighted"]["points"] != 54.5:
        raise PanelError("self test FAILED: the weighted total should be 54.5 for 6/5/7/4 "
                         "(18 + 12.5 + 14 + 10), it read %s" % parsed["weighted"]["points"])
    if len(parsed["fixes"]) != MAX_FIXES:
        raise PanelError("self test FAILED: expected %d fixes, parsed %d"
                         % (MAX_FIXES, len(parsed["fixes"])))
    print("self test PASS: %s refused on the per-day quota, the chain moved on, %s answered, "
          "scores %s, weighted %.1f, %d fixes"
          % (refused, answered, parsed["scores"], parsed["weighted"]["points"],
             len(parsed["fixes"])))
    return {"refused": refused, "answered": answered}


class _FakeResponse(object):
    def __init__(self, payload):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


# --------------------------------------------------------------------------- the manager's inbox

INBOX_HEADER = """# Director inbox: the nightly judge panel's five card drafts

Written by `projects/primordial-paradox/tools/judge_panel.py` (card t_70840bce, W4 JUDGE-PANEL) once
the manager made muse-spark-1.3 the judge model on 2026-10-26 17:15. One section per panel run,
newest last: the scores against the official weights (Impact 30, Meta tooling 25, Technical depth
20, Demo 25), then the top five fixes, each beside the body a card would carry and the command that
would create it. Append only, one writer (this tool).

Nothing here is a card. The tool creates none: a draft becomes a card only when the manager or a
human runs the command beside it, so the limit of five a night cannot be broken by a rerun.
"""


def render_inbox(date, cards, parsed, video, result, chain=None, now=None):
    """One dated section: the scores, then the five drafts with their body and create command."""
    chain = tuple(chain or MODEL_CHAIN)
    stamp = (now or eye_critic.utc_now()).strftime("%H:%M UTC")
    model = (result or {}).get("model") or "no model answered"
    total = parsed["weighted"]
    lines = ["## %s, run %s: %d draft(s), panel %.1f of 100 on `%s`"
             % (date, stamp, len(cards), total["points"], model),
             "",
             "- capture judged: `%s`" % _rel(video),
             "- scores: %s"
             % ", ".join("%s %s/10" % (label, parsed["scores"].get(key) if
                                      parsed["scores"].get(key) is not None else "NOT JUDGED")
                         for key, label, _weight, _text in CRITERIA),
             "- panel file: `%s`" % _rel(panel_path(date)),
             ""]
    if not cards:
        lines += ["No draft tonight: the panel's answer carried no readable fix block, so there is "
                  "nothing to paste. That is a finding about the answer, not about the game. Read "
                  "the panel file above before deciding what to do.", ""]
        return lines
    for row in cards:
        lines += ["### %d. %s" % (row["index"], row["title"] or "(untitled)"), "",
                  "- lane: %s, priority %d, raises: %s"
                  % (row["lane"] or "UNASSIGNED", row["priority"], row["criterion"] or "not named"),
                  "- body file: `%s`" % _rel(row["body_path"]),
                  "- body: %s" % row["body"],
                  "- create:", "", "```text", paste_command(row), "```", ""]
    lines += ["These %d drafts are the whole of tonight's allowance: the panel keeps five and drops "
              "the rest, so a sixth fix in the answer is not a sixth card." % len(cards), ""]
    return lines


def write_inbox(date, cards, parsed, video, result, chain=None, folder=None, now=None):
    """Append tonight's section to the manager's inbox, creating it with its header once."""
    path = folder or INBOX
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    fresh = not os.path.exists(path) or os.path.getsize(path) == 0
    section = _no_long_dashes_per_line(
        render_inbox(date, cards, parsed, video, result, chain=chain, now=now))
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        if fresh:
            header = _no_long_dashes_per_line(INBOX_HEADER.splitlines())
            handle.write("\n".join(header) + "\n")
        handle.write("\n".join(section) + "\n")
    return path


# --------------------------------------------------------------------------- main

def build_parser():
    parser = argparse.ArgumentParser(
        description="Score the newest nightly demo like a judge and write five fixes as cards.")
    parser.add_argument("--video", default=None,
                        help="the capture to judge (default: the newest output\\demo\\nightly-*.mp4)")
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAMES,
                        help="frames to sample (default %d)" % DEFAULT_FRAMES)
    parser.add_argument("--date", default=None, help="the date in the panel file name (YYYY-MM-DD)")
    parser.add_argument("--report-out", default=None, help="write the panel here")
    parser.add_argument("--measure-only", action="store_true",
                        help="sample and measure, send nothing, write the panel with NOT JUDGED rows")
    parser.add_argument("--dry-run", action="store_true", help="print the plan and exit")
    parser.add_argument("--self-test", action="store_true",
                        help="prove the model rotation on a fake per-day 429, then stop")
    parser.add_argument("--backend", default=None, choices=("gemini", "meta"),
                        help="sets PP_AI_BACKEND for this run (meta sends through meta_client)")
    parser.add_argument("--no-card-files", action="store_true",
                        help="do not write the five paste-ready body files")
    parser.add_argument("--inbox-out", default=None,
                        help="append the five drafts here (default: ../arananet/manager/inbox/director.md)")
    parser.add_argument("--no-inbox", action="store_true",
                        help="do not append the five drafts to the manager's inbox")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.self_test:
        try:
            self_test()
        except PanelError as exc:
            print("self test FAILED: %s" % eye_critic.redact(exc))
            return 1
        return 0

    backend = (args.backend or os.environ.get("PP_AI_BACKEND", "").strip().lower() or "meta")
    if backend not in ("meta", "gemini"):
        print("unknown backend %r: this tool runs on meta or gemini" % backend)
        return 2
    os.environ["PP_AI_BACKEND"] = backend
    chain = active_chain()
    key_source = None
    if backend == "meta":
        os.environ.setdefault("PP_AI_MODE", "record")  # record keeps the judges' replay keyless
        place, key_name = load_meta_key_from_user_environment()
        if place:
            key_source = "%s (%s)" % (place, key_name)
    else:
        place = eye_drive.load_key_from_user_environment()
        if place:
            key_source = "%s (%s)" % (place, eye_critic.KEY_ENV)

    video = args.video or newest_nightly()
    if not video:
        print("no nightly capture under %s: nothing to judge, no panel written. Run the nightly "
              "demo first." % DEMO_DIR)
        return 2
    if not os.path.exists(video):
        print("no such video: %s" % video)
        return 2
    date = args.date or eye_critic.utc_now().strftime("%Y-%m-%d")
    try:
        frames, info = sample_frames(video, count=max(1, args.frames))
    except PanelError as exc:
        print("error: %s" % eye_critic.redact(exc))
        return 1
    script = script_facts(video)
    out = args.report_out or panel_path(date)
    inbox = args.inbox_out or INBOX
    measured = measured_lines(frames, info, script, video)
    print("video:  %s" % os.path.relpath(video, ROOT))
    print("frames: %d at %s" % (len(frames), ", ".join("%.1f s" % r["at_s"] for r in frames)))
    print("panel:  %s" % os.path.relpath(out, ROOT))
    print("backend: %s, model chain: %s" % (backend, ", ".join(chain)))
    if backend == "meta":
        print("mode:   %s, cache: %s, ceiling: %d billed call(s) a day, %d used today"
              % (os.environ.get("PP_AI_MODE", "record"), _rel(os.path.join(ROOT, "data", "ai_cache")),
                 eye_critic._env_int(META_CALLS_PER_DAY_ENV, META_CALLS_PER_DAY_DEFAULT),
                 meta_runs_today()))
    print("key:    %s" % ("present in the %s" % key_source if key_source else
                          "absent from the environment and the Windows user environment"))
    if args.dry_run:
        print("duration: %.3f s, %s x %s, %s fps"
              % (info.get("duration_s") or 0.0, info.get("width"), info.get("height"),
                 info.get("fps")))
        print("inbox:  %s (the five drafts would be appended here)" % _rel(inbox))
        print("measured facts the panel would be shown:")
        for line in measured:
            print("  - %s" % line)
        print("dry run: nothing sent, nothing written")
        return 0

    result = None
    parsed = {"scores": {key: None for key in WEIGHTS}, "reasons": {key: "" for key in WEIGHTS},
              "fixes": [], "dropped_fixes": 0, "weighted": weighted_total({})}
    log, attempts = [], []
    if args.measure_only:
        print("measure only: no model called")
    elif not key_source:
        print("no %s in the environment or the Windows user environment: the measured half runs "
              "alone and the scores are NOT JUDGED"
              % (" or ".join(META_KEY_ENVS) if backend == "meta" else eye_critic.KEY_ENV))
    else:
        refusal = meta_budget_refusal() if backend == "meta" else None
        if refusal:
            print(refusal)
            log.append(refusal)
        else:
            try:
                result = ask_panel(frames, info, script, chain=chain, gate=panel_gate(), log=log)
            except PanelError as exc:
                print("error: %s" % eye_critic.redact(str(exc)))
                result = None
            if result is not None:
                attempts = result["attempts"]
                parsed = parse_panel(result["text"])
                print("model:  %s, scores %s, weighted %.1f of 100"
                      % (result["model"], parsed["scores"], parsed["weighted"]["points"]))

    cards, folder = ([], None)
    if parsed["fixes"] and not args.no_card_files:
        cards, folder = card_bodies(parsed["fixes"], date)
    text = render_panel(video, info, frames, script, result, parsed, cards, log, key_source, date,
                        attempts, parsed["dropped_fixes"], chain=chain, inbox=inbox)
    panel_folder = os.path.dirname(os.path.abspath(out))
    if panel_folder and not os.path.isdir(panel_folder):
        os.makedirs(panel_folder)
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("wrote:  %s (%d bytes)" % (os.path.relpath(out, ROOT), os.path.getsize(out)))
    if result is not None and parsed["weighted"]["criteria_scored"]:
        append_panel_ledger(panel_row(date, video, result, parsed, frames))
        print("ledger: %s" % os.path.relpath(PANEL_LEDGER, ROOT))
    if cards:
        print("cards:  %d body files in %s, none created"
              % (len(cards), os.path.relpath(folder, ROOT)))
    if not args.measure_only and not args.no_inbox:
        path = write_inbox(date, cards, parsed, video, result, chain=chain, folder=inbox)
        print("inbox:  %s (appended %d draft(s), none created)" % (_rel(path), len(cards)))
    print(WARNING)
    if not parsed["weighted"]["complete"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
