"""Where is the last half second of pp_boarding_v3.wav not silent? Print the envelope."""
import os
import struct
import wave

WAV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "pp_boarding_v3.wav")
with wave.open(WAV, "rb") as handle:
    frames = handle.getnframes()
    rate = handle.getframerate()
    raw = handle.readframes(frames)
samples = struct.unpack("<%dh" % (len(raw) // 2), raw)
window = int(0.05 * rate)
start = len(samples) - int(1.0 * rate)
i = start
while i + window <= len(samples):
    chunk = samples[i:i + window]
    peak = max(abs(s) for s in chunk)
    t = i / float(rate)
    db = 20 * (peak / 32768.0) ** 0.5 if peak else 0.0
    print("t=%.2f s  peak=%5d  %.1f dBFS" % (t, peak, 20 * __import__("math").log10(max(peak, 1) / 32768.0)))
    i += window
