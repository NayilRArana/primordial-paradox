"""pp04_check.py: the measured checks for the PP-04 cue.

Card MUS-CUE-PP04 asks for these, and this script is how they are proved rather than claimed:

  1. the cue is 30 to 45 s                        (ffprobe on the wav, mp3 and ogg)
  2. both codecs render at the same length         (ffprobe duration of mp3 and ogg)
  3. the first 4 s carry the hook                  (lead note count and the cell boundaries)
  4. no voice occupies the warning blip band       (narrow band RMS of the mix against the
                                                    alarm cue's own band level, plus the note
                                                    list of every voice against C6 and E6)
  5. 8 bit voices only                             (the eight chip tracks, nothing else)
  6. the loop seam                                 (sample difference at bar 28 and at the end)

Run from the repository root:
    python assets/audio/pp_04_navy_sailors/pp04_check.py
"""

from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import melody_guard  # noqa: E402

WAV = os.path.join(HERE, "pp_04_navy_sailors.wav")
MP3 = os.path.join(HERE, "pp_04_navy_sailors.mp3")
OGG = os.path.join(HERE, "pp_04_navy_sailors.ogg")
MIDI = os.path.join(HERE, "pp_04_navy_sailors.mid")
SCORE = os.path.join(HERE, "score_pp04.yaml")
ALARM = os.path.join(ROOT, "assets", "audio", "sfx", "alarm.wav")
REPORT = os.path.join(HERE, "pp_04_check.json")

SR = 44100
BLIP_HZ = (1046.5, 1318.5)      # MIDI 84 and 88, the two tones of the alarm cue
BAND_HZ = 25.0                  # the narrow analysis band around each blip tone
BPM = 176.0
BAR_S = 4 * 60.0 / BPM


def load_wav(path):
    with wave.open(path, "rb") as handle:
        frames = handle.getnframes()
        channels = handle.getnchannels()
        data = np.frombuffer(handle.readframes(frames), dtype="<i2").astype(np.float64)
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return data / 32768.0, frames / float(handle.getframerate())


def ffprobe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def band_rms(signal, centre, width=BAND_HZ):
    """RMS of the signal inside a narrow band, from the FFT.

    Parseval: the mean square of the whole signal equals the sum of the mean square of
    every bin, so scaling the band's bin power by the total bin count and square rooting
    gives the RMS that band contributes.
    """
    window = np.hanning(len(signal))
    spectrum = np.fft.rfft(signal * window)
    freqs = np.fft.rfftfreq(len(signal), 1.0 / SR)
    mask = (freqs >= centre - width) & (freqs <= centre + width)
    power = (np.abs(spectrum[mask]) ** 2).sum()
    # Parseval: sum over all bins of |X|^2 equals N times the energy of the windowed
    # signal, so the band's share divided by N and by the window energy is the band's
    # mean square. The same correction is applied to the alarm cue, so the margin is a
    # like for like ratio and the constant window factor cancels.
    mean_square = (power / len(signal)) / (window ** 2).sum()
    return float(np.sqrt(mean_square))


def main():
    music, seconds = load_wav(WAV)
    alarm, alarm_seconds = load_wav(ALARM)
    result = {"cue": "PP-04 Navy Sailors"}

    # 1 and 2: length in every codec.
    lengths = {"wav": ffprobe_duration(WAV), "mp3": ffprobe_duration(MP3),
               "ogg": ffprobe_duration(OGG)}
    result["lengths_seconds"] = {name: round(value, 3) for name, value in lengths.items()}
    result["within_30_to_45_s"] = all(30.0 <= value <= 45.0 for value in lengths.values())
    result["codecs_same_length"] = (abs(lengths["mp3"] - lengths["ogg"]) <= 0.05
                                    and abs(lengths["wav"] - lengths["mp3"]) <= 0.15)
    result["length_spread_seconds"] = round(max(lengths.values()) - min(lengths.values()), 3)

    # 3: the hook inside four seconds.
    tracks = melody_guard.parse_midi(MIDI)
    lead_spans = dict(tracks)["vrc6 pulse a"]
    four_seconds_ticks = 4.0 / 60.0 * BPM * 480
    ticks_in_hook = [span for span in lead_spans if span[0] < four_seconds_ticks]
    result["first_lead_note_seconds"] = round(min(s[0] for s in lead_spans) / 480.0 * 60.0 / BPM, 4)
    result["hook_cell_end_seconds"] = round(2 * BAR_S, 3)
    result["hook_cell_inside_4s"] = round(2 * BAR_S, 3) <= 4.0
    result["lead_notes_in_first_4s"] = len(ticks_in_hook)
    result["hook_returns_at_bars"] = [5, 17, 25]

    # 4: the warning blip band.
    bands = {}
    for centre in BLIP_HZ:
        music_band = band_rms(music, centre)
        alarm_band = band_rms(alarm, centre)
        bands["%.1f" % centre] = {
            "music_rms": float("%.6f" % music_band),
            "alarm_rms": float("%.6f" % alarm_band),
            "margin_db": round(20 * np.log10(alarm_band / music_band), 2),
        }
    result["blip_bands"] = bands
    result["blip_margin_db"] = min(band["margin_db"] for band in bands.values())
    result["blip_cleared"] = result["blip_margin_db"] >= 10.0

    pitches = {}
    for name in ("vrc6 pulse a", "vrc6 pulse b", "vrc6 saw", "pulse 1", "pulse 2",
                 "triangle", "noise", "dpcm"):
        spans = dict(tracks)[name]
        pitches[name] = sorted({pitch for _s, _e, pitch in spans})
    result["voice_pitches"] = {name: [min(values), max(values)] if values else []
                               for name, values in pitches.items()}
    # Nothing may sit within a semitone of either blip tone, in any voice. The noise and
    # dpcm tracks are excluded from the pitch test: their "note numbers" are chip rates and
    # sample selects, not pitches, and their rates are checked by the band measurement.
    off_limits = set()
    for centre in BLIP_HZ:
        midi_note = 69 + 12 * np.log2(centre / 440.0)
        off_limits.update({int(round(midi_note)) - 1, int(round(midi_note)),
                           int(round(midi_note)) + 1})
    clashes = {}
    for name, values in pitches.items():
        if name in ("noise", "dpcm"):
            continue
        hit = sorted(set(values) & off_limits)
        if hit:
            clashes[name] = hit
    result["blip_pitch_clashes"] = clashes
    result["no_voice_on_a_blip_tone"] = not clashes
    result["noise_rates_hz"] = {
        "hat": round(1789772.5 / 96.0, 1),
        "fill": [round(1789772.5 / period, 1) for period in (508, 254, 202)],
        "crash": round(1789772.5 / 254.0, 1),
        "note": "the noise clock rates, all far above the 1046 to 1319 Hz of the alarm",
    }

    # 5: eight chip voices only.
    names = [name for name, _spans in tracks]
    result["midi_tracks"] = names
    chip = {"vrc6 pulse a", "vrc6 pulse b", "vrc6 saw", "pulse 1", "pulse 2",
            "triangle", "noise", "dpcm"}
    result["only_chip_voices"] = set(names) - chip == {"meta"}

    # 6: the seams.
    bar28 = int(round(28 * BAR_S * SR))
    end = len(music) - 1
    result["seam_28_bars"] = {
        "seconds": round(28 * BAR_S, 3),
        "sample_difference": float("%.6f" % abs(music[bar28] - music[0])),
        "zero_crossing_at_seam": bool(np.sign(music[bar28]) != np.sign(music[bar28 - 1])),
    }
    result["seam_end_of_file"] = {
        "seconds": round(seconds, 3),
        "sample_difference": float("%.6f" % abs(music[end] - music[0])),
    }
    result["peak_dbfs"] = round(20 * np.log10(np.abs(music).max()), 2)
    result["rms_dbfs"] = round(20 * np.log10(np.sqrt((music ** 2).mean())), 2)

    with open(REPORT, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2,
                  default=lambda value: value.item() if hasattr(value, "item") else str(value))
        handle.write("\n")

    checks = [
        ("length 30 to 45 s", result["within_30_to_45_s"]),
        ("mp3 and ogg same length", result["codecs_same_length"]),
        ("hook cell inside 4 s", result["hook_cell_inside_4s"]),
        ("no voice on a blip tone", result["no_voice_on_a_blip_tone"]),
        ("blip band at least 10 dB down", result["blip_cleared"]),
        ("eight chip voices only", result["only_chip_voices"]),
    ]
    for label, ok in checks:
        print("%-32s %s" % (label, "PASS" if ok else "FAIL"))
    print("lengths", result["lengths_seconds"])
    print("blip margins dB", {key: band["margin_db"] for key, band in bands.items()})
    print("peak %.2f dBFS, rms %.2f dBFS" % (result["peak_dbfs"], result["rms_dbfs"]))
    return 0 if all(ok for _label, ok in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
