"""whisper_worker: the small child process tools/ai_bridge.py keeps alive for /hear.

Why a process and not an import. On this PC the project's Python is 3.14 and the interpreter that has
faster-whisper is 3.11, so the bridge cannot import the package in the process the game's launcher started. It
finds an interpreter that can (PP_WHISPER_PYTHON, then its own, then py -3.11) and runs this file there. The
model loads once, at startup, and then one JSON object per line goes in and one comes out, which keeps a three
second line's transcription at a few hundred milliseconds instead of paying the model load every time.

Protocol, one JSON object per line
    in   {"wav_b64": "<base64 of a 16000 Hz mono 16 bit PCM wav>"}
    out  {"transcript": "...", "language": "en", "duration_s": 2.4, "model": "tiny"}
    out  {"error": "what went wrong"}   and the process keeps serving unless the error was startup

Environment
    PP_WHISPER_MODEL      model size or a local path, default tiny
    PP_WHISPER_DEVICE     cpu (default) or cuda
    PP_WHISPER_COMPUTE    int8 (default on cpu), float16 on cuda

Usage
    python tools\\whisper_worker.py --model tiny        # what the bridge starts
    python tools\\whisper_worker.py --selftest          # load the model, print its name and exit

Audio never leaves this process: it comes in as bytes, is decoded in memory, and is not written to disk.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
import time
import wave

SAMPLE_RATE = 16000


class WavError(Exception):
    """The bytes are not the wav this bridge accepts."""


def wav_to_float32(raw, sample_rate=SAMPLE_RATE):
    """A 16 kHz mono 16 bit PCM wav as float32 samples in -1.0 to 1.0, with its duration in seconds."""
    try:
        with wave.open(io.BytesIO(raw), "rb") as handle:
            channels = handle.getnchannels()
            width = handle.getsampwidth()
            rate = handle.getframerate()
            frames = handle.readframes(handle.getnframes())
    except (wave.Error, EOFError) as exc:
        raise WavError("not a readable wav: %s" % exc)
    if channels != 1:
        raise WavError("expected mono, got %d channel(s)" % channels)
    if width != 2:
        raise WavError("expected 16 bit samples, got %d byte(s) per sample" % width)
    if rate != sample_rate:
        raise WavError("expected %d Hz, got %d Hz" % (sample_rate, rate))
    import numpy as np

    samples = np.frombuffer(frames, dtype="<i2").astype("float32") / 32768.0
    duration = float(len(samples)) / float(rate) if rate else 0.0
    return samples, duration


def load_model(name, device, compute_type):
    import faster_whisper

    return faster_whisper.WhisperModel(name, device=device, compute_type=compute_type)


def transcribe(model, samples, language=None):
    segments, info = model.transcribe(samples, language=language, beam_size=1, vad_filter=False,
                                      condition_on_previous_text=False)
    text = " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
    return text, getattr(info, "language", ""), getattr(info, "language_probability", None)


def main(argv=None):
    parser = argparse.ArgumentParser(description="faster-whisper worker for tools/ai_bridge.py")
    parser.add_argument("--model", default=os.environ.get("PP_WHISPER_MODEL", "tiny"))
    parser.add_argument("--device", default=os.environ.get("PP_WHISPER_DEVICE", "cpu"))
    parser.add_argument("--compute-type", default=os.environ.get("PP_WHISPER_COMPUTE", "int8"))
    parser.add_argument("--language", default=os.environ.get("PP_WHISPER_LANGUAGE", "en"))
    parser.add_argument("--selftest", action="store_true", help="load the model and print its name")
    args = parser.parse_args(argv)

    started = time.monotonic()
    try:
        model = load_model(args.model, args.device, args.compute_type)
    except Exception as exc:
        sys.stdout.write(json.dumps({"error": "model %r did not load: %s: %s"
                                              % (args.model, type(exc).__name__, exc)}) + "\n")
        sys.stdout.flush()
        return 1
    load_ms = int(round((time.monotonic() - started) * 1000))
    if args.selftest:
        print("whisper_worker: model %s (%s, %s) loaded in %d ms, python %s"
              % (args.model, args.device, args.compute_type, load_ms, sys.version.split()[0]))
        return 0

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        began = time.monotonic()
        try:
            request = json.loads(line)
            raw = base64.b64decode(request.get("wav_b64") or "")
            samples, duration = wav_to_float32(raw)
            if duration <= 0.0:
                raise WavError("the wav holds no samples")
            text, language, probability = transcribe(model, samples, args.language or None)
            sys.stdout.write(json.dumps({"transcript": text, "language": language,
                                         "language_probability": probability,
                                         "duration_s": round(duration, 3), "model": args.model,
                                         "ms": int(round((time.monotonic() - began) * 1000))}) + "\n")
        except Exception as exc:
            sys.stdout.write(json.dumps({"error": "%s: %s" % (type(exc).__name__, exc)}) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
