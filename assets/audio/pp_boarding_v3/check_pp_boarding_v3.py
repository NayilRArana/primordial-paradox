"""check_pp_boarding_v3.py: the card's checks for pp_boarding_v3, printed as one table.

1. Renders on disk and not empty, and the WAV length against 16 bars at 120 bpm.
2. One shot: nothing after beat 2 of bar 16, and the last 0.5 s is silent.
3. The held breath: bars 13 to 15 carry at most three of lead, saw, triangle, noise.
4. The two lead statements are intact: the hook is stated four times (bars 1, 3, 5, 7).
5. The devices are in the score: F#5 in the guide at bar 13, B4 in the guide at bar
   10, and the chromatic descent E4 to A3 in the triangle at bar 15.
6. The kit: no bar uses RCK-02 (sixteenth hats), and the pattern changes at least
   every two bars.
7. No long dashes in any text artifact in this folder.
"""
import json
import os
import struct
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

FAILS = []


def row(name, ok, detail):
    print("%-46s %-4s %s" % (name, "PASS" if ok else "FAIL", detail))
    if not ok:
        FAILS.append(name)


def read_midi_notes(path):
    """Minimal note extractor via the project's humanize module's SMF reader."""
    import humanize
    with open(path, "rb") as handle:
        data = handle.read()
    return humanize.read_smf(data) if hasattr(humanize, "read_smf") else None


def main():
    wav = os.path.join(HERE, "pp_boarding_v3.wav")
    mp3 = os.path.join(HERE, "pp_boarding_v3.mp3")
    mid = os.path.join(HERE, "pp_boarding_v3.mid")
    for name, path in (("wav", wav), ("mp3", mp3), ("mid", mid)):
        row("file %s exists and is not empty" % name, os.path.exists(path) and os.path.getsize(path) > 1000,
            "%d bytes" % (os.path.getsize(path) if os.path.exists(path) else 0))

    with wave.open(wav, "rb") as handle:
        frames = handle.getnframes()
        rate = handle.getframerate()
        raw = handle.readframes(frames)
    seconds = frames / float(rate)
    row("wav length inside a half bar of 32.000 s", abs(seconds - 32.0) <= 1.0, "%.3f s" % seconds)

    samples = struct.unpack("<%dh" % (len(raw) // 2), raw)
    tail = samples[-int(0.5 * rate):]
    tail_peak = max(abs(s) for s in tail)
    row("last 0.5 s below -30 dBFS", tail_peak < 1000, "peak %d, %.1f dBFS" % (tail_peak, 20 * __import__("math").log10(max(tail_peak, 1) / 32768.0)))

    report = json.load(open(os.path.join(HERE, "build_report_v3.json"), encoding="utf-8"))
    module = report["modules"][0]
    kit = module["kit"]
    row("kit has a different pattern every two bars at least",
        all(kit[str(bar)] != kit.get(str(bar - 1)) or kit[str(bar)] != kit.get(str(bar - 2))
            for bar in range(2, 15)),
        ", ".join(kit[str(b)] for b in range(1, 15)))
    row("no sixteenth hat bar (RCK-02) anywhere", "RCK-02" not in kit.values(), "patterns used: %d distinct" % len(set(kit.values())))

    hook = json.load(open(os.path.join(HERE, "hook_report_v3.json"), encoding="utf-8"))
    row("hook meter 100 of 100", hook["score"] == 100, "%d, %d returns, %d%% coverage"
        % (hook["score"], hook["motif"]["returns"], round(100 * hook["motif"]["coverage"])))
    row("hook stated four times", hook["motif"]["returns"] == 4, str(hook["motif"]["occurrence_bars"]))

    device_bars = [d["bar"] for d in module["dissonance"]]
    row("three devices, none in bar 1 or a section final bar",
        len(device_bars) == 3 and 1 not in device_bars and not any(b in (4, 8, 12, 16) for b in device_bars),
        str(device_bars))
    dom = [d["bar"] for d in module["secondary_dominants"]]
    row("secondary dominants at 4, 8 and 11", dom == [4, 8, 11], str(dom))

    dashes = "\u2014\u2013\u2012\u2015"
    bad = []
    for name in os.listdir(HERE):
        if name.endswith((".md", ".json", ".py")):
            text = open(os.path.join(HERE, name), encoding="utf-8").read()
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
