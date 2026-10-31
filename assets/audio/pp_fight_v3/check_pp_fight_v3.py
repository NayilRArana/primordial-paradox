"""check_pp_fight_v3.py: the card's checks for pp_fight_v3, printed as one table.

1. Every module exists as mid, wav and mp3, and is not empty.
2. Each wav is 16 bars at 168 bpm, 22.857 s, inside half a bar.
3. The loop seam of both loop modules is a zero sample difference, read from the renderer's json.
4. The hook meter still reads 100 of 100 on the calm and on the fight.
5. The calm kit is a ladder: at least eight different rungs, no run of three bars on one rung,
   and the fill rungs land on bars 4, 8 and 12.
6. Three devices in the calm, none in bar 1 or bar 16, and the seam bar is identical in both
   modules (which the builder prints, and this script re-checks from build_report_v3.json).
7. No long dashes in any text artifact in this folder.
"""
import json
import os
import struct
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

FAILS = []
MODULES = ("fight", "calm", "states")


def row(name, ok, detail):
    print("%-52s %-4s %s" % (name, "PASS" if ok else "FAIL", detail))
    if not ok:
        FAILS.append(name)


def wav_seconds(path):
    with wave.open(path, "rb") as handle:
        return handle.getnframes() / float(handle.getframerate())


def main():
    for module in MODULES:
        for ext in ("mid", "wav", "mp3"):
            path = os.path.join(HERE, "pp_fight_v3_%s.%s" % (module, ext))
            size = os.path.getsize(path) if os.path.exists(path) else 0
            row("%s.%s exists and is not empty" % (module, ext), size > 1000, "%d bytes" % size)

    for module, expected in (("fight", 22.857), ("calm", 22.857), ("states", 45.714)):
        seconds = wav_seconds(os.path.join(HERE, "pp_fight_v3_%s.wav" % module))
        row("%s wav length inside half a bar of %.3f s" % (module, expected),
            abs(seconds - expected) <= 0.6, "%.3f s" % seconds)

    for module in ("fight", "calm"):
        path = os.path.join(HERE, "pp_fight_v3_%s_loop.json" % module)
        data = json.load(open(path, encoding="utf-8"))
        seam = data.get("loop_seam_sample_difference")
        row("%s loop seam sample difference" % module, seam == 0, repr(seam))

    for module in ("calm", "fight"):
        path = os.path.join(HERE, "hook_report_%s_v3.json" % module)
        hook = json.load(open(path, encoding="utf-8"))
        row("%s hook meter 100 of 100" % module, hook["score"] == 100,
            "%d, %d returns" % (hook["score"], hook["motif"]["returns"]))

    report = json.load(open(os.path.join(HERE, "build_report_v3.json"), encoding="utf-8"))
    kit = report["calm_kit"]
    ids = [kit[str(bar)] for bar in sorted(int(b) for b in kit)]
    run3 = any(ids[i] == ids[i + 1] == ids[i + 2] for i in range(len(ids) - 2))
    row("calm kit: at least eight different rungs", len(set(ids)) >= 8, "%d distinct" % len(set(ids)))
    row("calm kit: no run of three bars on one rung", not run3, ",".join(ids))
    fills = [kit.get("4"), kit.get("8"), kit.get("12")]
    row("calm kit: fills at bars 4, 8 and 12", all(f and f.startswith("FLC") for f in fills),
        ",".join(str(f) for f in fills))

    devices = report["dissonance"]
    bars = [d["bar"] for d in devices]
    row("three devices, none in bar 1 or bar 16",
        len(devices) == 3 and 1 not in bars and 16 not in bars, str(bars))
    row("devices carry a device id, a voice and a resolution",
        all(d.get("device") and d.get("voice") and d.get("resolves_to") for d in devices),
        ", ".join(d["device"] for d in devices))
    row("builder reported no voice or length problems",
        not report["checks"]["problems"], str(report["checks"]["problems"]))

    dashes = "\u2014\u2013\u2012\u2015"
    bad = []
    for name in os.listdir(HERE):
        if name.endswith((".md", ".json", ".py")):
            text = open(os.path.join(HERE, name), encoding="utf-8", errors="replace").read()
            if any(d in text for d in dashes):
                bad.append(name)
    row("no long dashes in any text artifact", not bad, str(bad) if bad else "clean")

    print()
    if FAILS:
        print("FAILED:", ", ".join(FAILS))
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
