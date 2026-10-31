"""Seam check for pp_05_small_ship_v5: the loop is all 32 bars of 4/4 at 128 bpm."""
import math
import struct
import sys
import wave

path = sys.argv[1]
loop_bars = int(sys.argv[2]) if len(sys.argv) > 2 else 32
bpm = float(sys.argv[3]) if len(sys.argv) > 3 else 128.0
beats = 4
rate = 44100
period = rate * beats * 60.0 / bpm

with wave.open(path, "rb") as handle:
    frames = handle.getnframes()
    width = handle.getsampwidth()
    channels = handle.getnchannels()
    raw = handle.readframes(frames)
if width != 2:
    raise SystemExit("expected 16 bit, got %d bytes" % width)
data = struct.unpack("<%dh" % (len(raw) // 2), raw)
if channels > 1:
    data = data[::channels]

point = int(round(loop_bars * period))
tail = len(data) - point
if point >= len(data):
    point = len(data)
    jump = abs(data[0] - data[point - 1])
    window = 441
    before = data[point - window:point]
    after = data[:window]
else:
    jump = abs(data[point] - data[point - 1])
    window = 441
    before = data[point - window:point]
    after = data[point:point + window]
print("file samples", len(data), "loop bars", loop_bars, "loop point sample", point,
      "(%.4f s)" % (point / float(rate)))
rms_before = math.sqrt(sum(v * v for v in before) / float(len(before)))
rms_after = math.sqrt(sum(v * v for v in after) / float(len(after)))
jumps = [abs(b - a) for a, b in zip(data[point - 20000:point], data[point - 19999:point])]
jumps.sort()
print("seam jump %d | rms 10 ms before %.0f after %.0f | local jump p99 %d max %d"
      % (jump, rms_before, rms_after, jumps[int(len(jumps) * 0.99)], jumps[-1]))
print("last sample of the loop %d, first sample %d" % (data[point - 1], data[0]))
print("tail beyond loop point:", tail, "samples")
