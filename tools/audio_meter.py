#!/usr/bin/env python3
"""audio_meter.py: the level the Windows mixer sees from PrimordialParadox.exe, every 500 ms, into a CSV.

Why this exists (card MUSIC-REAL, 2026-11-02): every earlier proof of the game's music ran muted (PP_MUTE=1) or read the
game's own log, and a log that says "playing" says nothing about what reaches the speaker. This tool reads the Windows audio
session of the game process through Core Audio's IAudioMeterInformation (the same peak meter the volume mixer draws), so an
UNMUTED run shows a per scene peak in dBFS. It starts nothing and opens no window; it only reads.

What it uses: plain ctypes against the Core Audio COM interfaces (IMMDeviceEnumerator, IAudioSessionManager2,
IAudioSessionEnumerator, IAudioSessionControl2, IAudioMeterInformation). Neither pycaw nor comtypes is installed on this PC
(checked 2026-11-02), so neither is imported. The vtable slot numbers are the ones in the Windows SDK headers
(mmdeviceapi.h, audiopolicy.h, endpointvolume.h).

What the number is: the session meter reports the peak sample of that process's output since the last read, linear 0..1,
after the process's own session volume and before the endpoint (master) volume. dBFS is 20*log10(peak), floored at -120.
It is NOT the game's gain; a game muted with audio_master_gain(0) reads -120 here, which is exactly the point.

Usage:
    python tools\\audio_meter.py --seconds 300 --out output\\music_real_2026-11-02\\meter.csv
    python tools\\audio_meter.py --seconds 300 --out meter.csv --log build\\demo-game.log   also stamp each new game log line
    python tools\\audio_meter.py --list                                                      list the audio sessions and exit
The CSV columns are: iso_time, epoch_s, pid, session, peak_linear, peak_dbfs. `session` is 1 when the game has an audio
session and 0 when it has none yet (a game that has not made a sound has no session; that row is -120 and says why).
With --log, <out stem>_log.csv gets one row (epoch_s, line) for each new line of the game log that mentions "PP audio",
"PP route", "PP drive: shot", "PP: battle" or "PP: fight", stamped with the poll that saw it (500 ms resolution), which is
what tools\\audio_route_report.py uses to put the game's scene on the meter's clock.
"""

from __future__ import annotations

import argparse
import csv
import ctypes
import math
import os
import subprocess
import sys
import time
from ctypes import POINTER, byref, c_float, c_int, c_long, c_ulong, c_void_p, c_wchar_p

EXE_NAME = "PrimordialParadox.exe"
POLL_S = 0.5
FLOOR_DB = -120.0
LOG_KEYS = ("PP audio", "PP route", "PP drive: shot", "PP: battle", "PP: fight")


def peak_to_dbfs(peak):
    """Linear peak (0..1) to dBFS, floored at FLOOR_DB. Pure arithmetic, tested without a sound card."""
    try:
        value = float(peak)
    except (TypeError, ValueError):
        return FLOOR_DB
    if value <= 0.0:
        return FLOOR_DB
    return max(FLOOR_DB, 20.0 * math.log10(value))


class GUID(ctypes.Structure):
    _fields_ = [("Data1", ctypes.c_ulong), ("Data2", ctypes.c_ushort), ("Data3", ctypes.c_ushort),
                ("Data4", ctypes.c_ubyte * 8)]


def make_guid(text):
    guid = GUID()
    if ctypes.windll.ole32.IIDFromString(c_wchar_p(text), byref(guid)) != 0:
        raise OSError("bad GUID " + text)
    return guid


CLSID_MMDeviceEnumerator = "{BCDE0395-E52F-467C-8E3D-C4579291692E}"
IID_IMMDeviceEnumerator = "{A95664D2-9614-4F35-A746-DE8DB63617E6}"
IID_IAudioSessionManager2 = "{77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F}"
IID_IAudioSessionControl2 = "{BFB7FF88-7239-4FC9-8FA2-07C950BE9C6D}"
IID_IAudioMeterInformation = "{C02216F6-8C67-4B5B-9D00-D008E73E0064}"
CLSCTX_ALL = 23
E_RENDER, E_MULTIMEDIA = 0, 1


def vcall(ptr, index, argtypes, *args):
    """Call slot `index` of a COM object's vtable. Returns the HRESULT (a signed int)."""
    table = ctypes.cast(ptr, POINTER(c_void_p))[0]
    slot = ctypes.cast(table, POINTER(c_void_p))[index]
    prototype = ctypes.WINFUNCTYPE(c_long, c_void_p, *argtypes)
    return prototype(slot)(ptr, *args)


def release(ptr):
    if ptr:
        try:
            table = ctypes.cast(ptr, POINTER(c_void_p))[0]
            slot = ctypes.cast(table, POINTER(c_void_p))[2]
            ctypes.WINFUNCTYPE(c_ulong, c_void_p)(slot)(ptr)
        except Exception:  # gate: ok a release on a dead object must never stop the meter
            pass


def hr_ok(hr):
    return hr >= 0


class Sessions:
    """The default render device's session manager, opened once and enumerated on every poll."""

    def __init__(self):
        ctypes.windll.ole32.CoInitializeEx(None, 0)
        self.enumerator = c_void_p()
        hr = ctypes.windll.ole32.CoCreateInstance(byref(make_guid(CLSID_MMDeviceEnumerator)), None, CLSCTX_ALL,
                                                  byref(make_guid(IID_IMMDeviceEnumerator)), byref(self.enumerator))
        if not hr_ok(hr):
            raise OSError("CoCreateInstance(MMDeviceEnumerator) failed 0x%08x" % (hr & 0xFFFFFFFF))
        self.device = c_void_p()
        hr = vcall(self.enumerator, 4, [c_int, c_int, POINTER(c_void_p)], E_RENDER, E_MULTIMEDIA, byref(self.device))
        if not hr_ok(hr):
            raise OSError("no default render device 0x%08x" % (hr & 0xFFFFFFFF))
        self.manager = c_void_p()
        hr = vcall(self.device, 3, [POINTER(GUID), c_ulong, c_void_p, POINTER(c_void_p)],
                   byref(make_guid(IID_IAudioSessionManager2)), CLSCTX_ALL, None, byref(self.manager))
        if not hr_ok(hr):
            raise OSError("no session manager on the default device 0x%08x" % (hr & 0xFFFFFFFF))

    def read(self):
        """[(pid, peak_linear)] for every session on the device right now."""
        out = []
        sess_enum = c_void_p()
        if not hr_ok(vcall(self.manager, 5, [POINTER(c_void_p)], byref(sess_enum))):
            return out
        try:
            count = c_int(0)
            if not hr_ok(vcall(sess_enum, 3, [POINTER(c_int)], byref(count))):
                return out
            for index in range(count.value):
                control = c_void_p()
                if not hr_ok(vcall(sess_enum, 4, [c_int, POINTER(c_void_p)], index, byref(control))):
                    continue
                control2 = c_void_p()
                meter = c_void_p()
                try:
                    if not hr_ok(vcall(control, 0, [POINTER(GUID), POINTER(c_void_p)],
                                       byref(make_guid(IID_IAudioSessionControl2)), byref(control2))):
                        continue
                    pid = c_ulong(0)
                    if not hr_ok(vcall(control2, 14, [POINTER(c_ulong)], byref(pid))):
                        continue
                    if not hr_ok(vcall(control, 0, [POINTER(GUID), POINTER(c_void_p)],
                                       byref(make_guid(IID_IAudioMeterInformation)), byref(meter))):
                        continue
                    peak = c_float(0.0)
                    if hr_ok(vcall(meter, 3, [POINTER(c_float)], byref(peak))):
                        out.append((int(pid.value), float(peak.value)))
                finally:
                    release(meter)
                    release(control2)
                    release(control)
        finally:
            release(sess_enum)
        return out


def game_pids(image=EXE_NAME):
    """The process ids whose image name is the game's, from tasklist (no extra module needed)."""
    try:
        proc = subprocess.run(["tasklist", "/FI", "IMAGENAME eq " + image, "/FO", "CSV", "/NH"], capture_output=True,
                              text=True, timeout=10, creationflags=0x08000000 if sys.platform == "win32" else 0)
    except (OSError, subprocess.SubprocessError):
        return []
    pids = []
    for row in csv.reader(proc.stdout.splitlines()):
        if len(row) >= 2 and row[0].lower() == image.lower() and row[1].strip().isdecimal():
            pids.append(int(row[1]))
    return pids


class LogTail:
    """New lines of the game log, each stamped with the poll that saw it."""

    def __init__(self, path, from_end=True):
        self.path = path
        self.rest = b""
        # A log that exists before the game starts holds the PREVIOUS run: start at its end, never replay it.
        self.offset = 0
        if from_end and os.path.isfile(path):
            self.offset = os.path.getsize(path)

    def poll(self):
        out = []
        try:
            # The game truncates its log at launch: a file shorter than the offset is a new run, read it from 0.
            if os.path.getsize(self.path) < self.offset:
                self.offset = 0
                self.rest = b""
            with open(self.path, "rb") as handle:
                handle.seek(self.offset)
                data = handle.read()
                self.offset += len(data)
        except OSError:
            return out
        data = self.rest + data
        parts = data.split(b"\n")
        self.rest = parts.pop()
        for raw in parts:
            text = raw.decode("utf-8", errors="replace").rstrip("\r")
            if any(key in text for key in LOG_KEYS):
                out.append(text)
        return out


def run(seconds, out_path, log_path=None, pid_arg=None, say=print):
    sessions = Sessions()
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    events_path = None
    events = None
    tail = None
    if log_path:
        events_path = os.path.splitext(out_path)[0] + "_log.csv"
        events = open(events_path, "w", newline="", encoding="utf-8")
        ev_writer = csv.writer(events)
        ev_writer.writerow(["epoch_s", "line"])
        tail = LogTail(log_path)
    rows = 0
    loud = 0
    started = time.time()
    with open(out_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["iso_time", "epoch_s", "pid", "session", "peak_linear", "peak_dbfs"])
        next_tick = started
        while time.time() - started < seconds:
            now = time.time()
            pids = [pid_arg] if pid_arg else game_pids()
            peak = 0.0
            found = 0
            use_pid = pids[0] if pids else ""
            if pids:
                for pid, value in sessions.read():
                    if pid in pids:
                        found = 1
                        use_pid = pid
                        peak = max(peak, value)
            db = peak_to_dbfs(peak) if found else FLOOR_DB
            writer.writerow([time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now)), "%.3f" % now, use_pid, found,
                             "%.6f" % peak, "%.1f" % db])
            handle.flush()
            rows += 1
            if found and db > -50.0:
                loud += 1
            if tail is not None:
                for line in tail.poll():
                    ev_writer.writerow(["%.3f" % now, line])
                events.flush()
            next_tick += POLL_S
            delay = next_tick - time.time()
            if delay > 0:
                time.sleep(delay)
    if events is not None:
        events.close()
    say("audio_meter: %d samples over %.0f s into %s; %d samples above -50 dBFS%s"
        % (rows, time.time() - started, out_path, loud, ("; log events in " + events_path) if events_path else ""))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Per process audio peak meter for PrimordialParadox.exe")
    parser.add_argument("--seconds", type=float, default=300.0)
    parser.add_argument("--out", default=os.path.join("output", "music_real_2026-11-02", "meter.csv"))
    parser.add_argument("--log", default=None, help="game log to tail and stamp (build\\demo-game.log)")
    parser.add_argument("--pid", type=int, default=None, help="meter this pid instead of every PrimordialParadox.exe")
    parser.add_argument("--list", action="store_true", help="list audio sessions (pid, peak) once and exit")
    args = parser.parse_args(argv)
    if sys.platform != "win32":
        print("audio_meter: Windows Core Audio is not available on this host, nothing measured")
        return 4
    if args.list:
        for pid, peak in Sessions().read():
            print("pid %d peak %.4f (%.1f dBFS)" % (pid, peak, peak_to_dbfs(peak)))
        return 0
    return run(args.seconds, args.out, args.log, args.pid)


if __name__ == "__main__":
    sys.exit(main())
