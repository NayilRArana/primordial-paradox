"""Composition toolkit for the final scope cues (2026-11-03, MUSIC role).

Four original cues are written here as Python data and compiled to the project's eight track
chip MIDI layout (the one assets/audio/pp_03_harbor/build_pp03.py writes and tools/render_chip.py
renders): vrc6 pulse a, vrc6 pulse b, vrc6 saw, pulse 1, pulse 2, triangle, noise, dpcm.

Nothing is quoted from any published game. Motifs come from the game's own music:
  L  the title leitmotif (A minor, 3/4): E D C B | B | E C D E | B G# A B
  H  the harbor tide (A minor): A C E (rise), D B G (crest and fall), A C F
  M  Morgan's cell (D minor): A Bb A D E D

A note is written as token "Name:steps" where a step is a sixteenth; "r:n" is a rest.
Every track is monophonic (one note at a time), like the chip.
"""

from __future__ import annotations

import os
import re
import struct

PPQ = 480
STEP = 120   # one sixteenth

TRACKS = ("vrc6 pulse a", "vrc6 pulse b", "vrc6 saw", "pulse 1", "pulse 2",
          "triangle", "noise", "dpcm")
RANGES = {
    "vrc6 pulse a": (55, 96), "vrc6 pulse b": (45, 84), "vrc6 saw": (36, 71),
    "pulse 1": (48, 83), "pulse 2": (43, 96), "triangle": (33, 55),
    "noise": (1, 16), "dpcm": (36, 38),
}
LETTERS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
NOTE_RE = re.compile(r"^([A-G])(#|b)?(-?\d)$")
CHORD_RE = re.compile(r"^([A-G][#b]?)(maj7|m7|dim7|dim|aug|sus4|m|7)?(?:/([A-G][#b]?))?$")
QUALITY = {"": (0, 4, 7), "m": (0, 3, 7), "dim": (0, 3, 6), "aug": (0, 4, 8),
           "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10), "dim7": (0, 3, 6, 9),
           "sus4": (0, 5, 7), "maj7": (0, 4, 7, 11)}


def midi(name):
    m = NOTE_RE.match(name)
    if not m:
        raise ValueError("not a note name: %r" % (name,))
    letter, acc, octave = m.groups()
    return (int(octave) + 1) * 12 + LETTERS[letter] + (1 if acc == "#" else -1 if acc == "b" else 0)


def pc_of(name):
    m = re.match(r"^([A-G])(#|b)?$", name)
    if not m:
        raise ValueError("not a pitch class: %r" % (name,))
    return (LETTERS[m.group(1)] + (1 if m.group(2) == "#" else -1 if m.group(2) == "b" else 0)) % 12


class Chord(object):
    def __init__(self, symbol):
        m = CHORD_RE.match(symbol)
        if not m:
            raise ValueError("unknown chord %r" % (symbol,))
        root, quality, bass = m.groups()
        self.symbol = symbol
        self.root = pc_of(root)
        self.ivs = QUALITY[quality or ""]
        self.bass = pc_of(bass) if bass else self.root
        self.tones = [(self.root + i) % 12 for i in self.ivs]

    def pitch(self, token, base):
        """Token R 3 5 7 (optionally followed by ^ for an octave up) above the root placed at/after base."""
        up = token.count("^")
        t = token.replace("^", "")
        root = base + ((self.root - base) % 12)
        iv = {"R": 0, "3": self.ivs[1], "5": self.ivs[2],
              "7": self.ivs[3] if len(self.ivs) > 3 else 10}[t]
        return root + iv + 12 * up


class Cue(object):
    def __init__(self, slug, title, bpm, beats, bars, key):
        self.slug, self.title, self.bpm, self.beats, self.bars, self.key = slug, title, bpm, beats, bars, key
        self.spb = beats * 4
        self.notes = {t: [] for t in TRACKS}
        self.ccs = {t: [] for t in TRACKS}
        self.sections = []

    # ---- time
    def tick(self, bar, step):
        return (bar * self.spb + step) * STEP

    @property
    def body_ticks(self):
        return self.bars * self.spb * STEP

    # ---- raw writers
    def put(self, track, bar, step, steps, pitch, vel=100):
        lo, hi = RANGES[track]
        if not lo <= pitch <= hi:
            raise ValueError("%s: pitch %d out of range %d..%d (bar %d)" % (track, pitch, lo, hi, bar + 1))
        s = self.tick(bar, step)
        e = s + int(steps * STEP)
        if e > self.body_ticks:
            raise ValueError("%s: note past the loop end (bar %d)" % (track, bar + 1))
        self.notes[track].append((s, e, pitch, int(vel)))

    def cc(self, track, bar, step, ctrl, value):
        self.ccs[track].append((self.tick(bar, step), ctrl, int(value)))

    def level(self, track, bar, value):
        self.cc(track, bar, 0, 11, value)

    # ---- melody
    def melody(self, track, bar, spec, vel=100, vib=None, shift=0):
        """spec 'A4:6 C5:6 E5:4'. vib=(depth, delay_eighths, min_steps) sets vibrato on long notes."""
        cur = 0
        for tok in spec.split():
            name, n = tok.split(":")
            n = int(n)
            if name != "r":
                p = midi(name) + shift
                self.put(track, bar, cur, n, p, vel)
                if vib and n >= vib[2]:
                    self.cc(track, bar, cur, 1, vib[0])
                    self.cc(track, bar, cur, 20, vib[1])
                    self.cc(track, bar, cur + n, 1, 0)
                    self.cc(track, bar, cur + n, 20, 0)
            cur += n
        if cur != self.spb:
            raise ValueError("melody bar %d holds %d steps, not %d: %r" % (bar + 1, cur, self.spb, spec))

    # ---- patterns on a chord
    def arp(self, track, bar, chord, pattern, base, vel=90, length=1, step0=0):
        """pattern: space separated tokens (R 3 5 7 with ^ for octave, '-' rest), one per `length` steps."""
        for i, tok in enumerate(pattern.split()):
            if tok == "-":
                continue
            self.put(track, bar, step0 + i * length, length, chord.pitch(tok, base), vel)

    def bass(self, track, bar, chord, pattern, base, vel=105, length=2):
        for i, tok in enumerate(pattern.split()):
            if tok == "-":
                continue
            root = base + ((chord.bass - base) % 12)
            if tok == "R":
                p = root
            elif tok == "R^":
                p = root + 12
            elif tok == "5":
                p = root + 7
            elif tok == "5v":
                p = root - 5
            elif tok == "3":
                p = root + chord.ivs[1]
            else:
                p = chord.pitch(tok, base)
            while p > RANGES[track][1]:
                p -= 12
            self.put(track, bar, i * length, length, p, vel)

    # ---- drums
    def kick(self, bar, step, vel=100):
        self.put("dpcm", bar, step, 1, 36, vel)

    def snare(self, bar, step, vel=100):
        self.put("dpcm", bar, step, 1, 38, vel)

    def noise(self, bar, step, steps, idx, vel):
        self.put("noise", bar, step, steps, idx + 1, vel)

    def drum_bar(self, bar, kick="", snare="", hats="", idx=3, kvel=100, svel=100, hscale=1.0, hlen=1):
        """kick/snare: strings of 16 chars, 'x' hit. hats: 16 chars of 0-9 (noise velocity digits)."""
        for i, ch in enumerate(kick):
            if ch == "x" and not (i < len(snare) and snare[i] == "x"):
                self.kick(bar, i, kvel)
        for i, ch in enumerate(snare):
            if ch == "x":
                self.snare(bar, i, svel)
        for i, ch in enumerate(hats):
            if ch.isdigit() and ch != "0":
                self.noise(bar, i, hlen, idx, max(8, int(int(ch) * 9 * hscale)))

    # ---- output
    def check_mono(self):
        for t, ns in self.notes.items():
            ns.sort()
            for a, b in zip(ns, ns[1:]):
                if a[1] > b[0]:
                    raise ValueError("%s: overlapping notes at tick %d (bar %d)"
                                     % (t, b[0], b[0] // (self.spb * STEP) + 1))

    def midi_bytes(self, passes=1):
        self.check_mono()
        chunks = [self._meta()]
        for t in TRACKS:
            chunks.append(self._track(t, passes))
        head = b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), PPQ)
        return head + b"".join(chunks)

    def _meta(self):
        body = bytearray()
        body += b"\x00\xff\x03" + _vl(9) + b"conductor"
        den = 2 if self.beats in (3, 4) else 2
        body += b"\x00\xff\x58\x04" + bytes((self.beats, den, 24, 8))
        body += b"\x00\xff\x51\x03" + int(round(60000000.0 / self.bpm)).to_bytes(3, "big")
        body += b"\x00\xff\x59\x02" + bytes((0, 0 if "minor" in self.key else 0))
        body += b"\x00\xff\x2f\x00"
        return b"MTrk" + struct.pack(">I", len(body)) + bytes(body)

    def _track(self, name, passes):
        ev = []
        n = 0
        for k in range(passes):
            off = k * self.body_ticks
            for s, e, p, v in self.notes[name]:
                ev.append((e + off, 1, n, bytes((0x80, p, 64))))
                ev.append((s + off, 2, n + 1, bytes((0x90, p, v))))
                n += 2
            for tk, c, v in self.ccs[name]:
                # controls take effect strictly before the note that reads them (see build notes)
                t = off + tk - (1 if (tk > 0 or k > 0) else 0)
                ev.append((t, 0, n, bytes((0xB0, c, v))))
                n += 1
        ev.sort(key=lambda r: (r[0], r[1], r[2]))
        nm = name.encode("latin-1")
        body = bytearray(b"\x00\xff\x03" + _vl(len(nm)) + nm)
        cur = 0
        for t, _o, _n, payload in ev:
            body += _vl(t - cur) + payload
            cur = t
        body += b"\x00\xff\x2f\x00"
        return b"MTrk" + struct.pack(">I", len(body)) + bytes(body)


def _vl(v):
    buf = bytearray([v & 0x7F])
    v >>= 7
    while v:
        buf.insert(0, 0x80 | (v & 0x7F))
        v >>= 7
    return bytes(buf)


def chords_of(spec):
    return [Chord(s) for s in spec.split()]


# ======================================================================================
# CUE 1: PP-03 Harbor Storm. A minor, 4/4, 160 bpm, 48 bars (72.000 s).
# ======================================================================================

HOOK = ["A4:6 C5:6 E5:4", "D5:6 B4:6 G4:4", "A4:6 C5:6 F5:4", "E5:6 B4:6 G#4:4"]
ARPS_S2 = ["A4:2 C5:2 E5:2 C5:2 A5:6 r:2", "G5:2 D5:2 B4:2 D5:2 G5:6 r:2",
           "F5:2 C5:2 A4:2 C5:2 F5:6 r:2", "E5:2 B4:2 G#4:2 B4:2 E5:8",
           "D5:2 F5:2 A5:2 F5:2 D5:6 r:2", "C5:2 E5:2 A5:2 E5:2 C5:6 r:2",
           "Bb4:2 D5:2 F5:2 D5:2 Bb4:4 A4:2 G#4:2", "E5:2 B4:2 G#4:2 B4:2 E5:4 r:4"]


def storm():
    c = Cue("pp_03_quay_storm", "Harbor Storm", 160, 4, 48, "A minor")
    chords = (chords_of("Am G/B F E/G# Am G/B F E/G#") + chords_of("Am G/B F E/G# Dm/F Am Bb E")
              + chords_of("E E Am E Am E F Dm") + chords_of("Am G/B F E/G# Am G/B F E/G#")
              + chords_of("Am G/B F E/G# Dm/F Am Bb E") + chords_of("Am G/B F Dm/F Bb G/B E E"))
    lead = {}
    # S1 squall: the harbor tide in 3+3+2, then L's descending head on the last bar
    lead.update({i: HOOK[i % 4] for i in range(0, 7)})
    lead[7] = "E5:6 D5:2 C5:2 B4:6"
    # S2 gale: arpeggio development
    lead.update({8 + i: ARPS_S2[i] for i in range(8)})
    # S3 eye: the title leitmotif in long breaths
    eye = ["E5:6 D5:2 C5:2 B4:2 r:4", "B4:12 r:4", "E5:6 C5:2 D5:2 E5:2 r:4", "B4:6 G#4:2 A4:2 B4:2 r:4",
           "C5:6 A4:2 B4:2 C5:2 r:4", "B4:12 r:4", "F5:6 D5:2 E5:2 F5:2 r:4", "D5:8 r:8"]
    lead.update({16 + i: eye[i] for i in range(8)})
    # S4 lightning: the hook again, octave doubled by pulse 2
    lead.update({24 + i: HOOK[i % 4] for i in range(7)})
    lead[31] = "E5:6 D5:2 C5:2 B4:6"
    # S5 gale again: the arpeggios
    lead.update({32 + i: ARPS_S2[i] for i in range(8)})
    # S6 rolling
    roll = ["A4:6 C5:6 E5:4", "D5:6 B4:6 G4:4", "A4:6 C5:6 F5:4", "D5:2 F5:2 A5:2 F5:2 D5:6 r:2",
            "Bb4:2 D5:2 F5:2 D5:2 Bb4:6 r:2", "G4:2 B4:2 D5:2 B4:2 G4:6 r:2",
            "E5:2 B4:2 G#4:2 B4:2 E5:8", "E5:4 D5:2 C5:2 B4:4 G#4:4"]
    lead.update({40 + i: roll[i] for i in range(8)})

    sect = lambda b: b // 8
    c.sections = ["squall", "gale", "eye", "lightning", "gale2", "rolling"]
    base_lv = {"vrc6 pulse a": 11, "vrc6 pulse b": 4, "vrc6 saw": 5, "pulse 1": 5,
               "pulse 2": 4, "triangle": 8, "noise": 6, "dpcm": 8}
    for t, v in base_lv.items():
        c.cc(t, 0, 0, 11, v)
    c.cc("vrc6 pulse a", 0, 0, 12, 3)
    c.cc("vrc6 pulse b", 0, 0, 12, 3)
    c.cc("pulse 1", 0, 0, 12, 0)
    c.cc("pulse 2", 0, 0, 12, 1)
    eye_lv = {"vrc6 pulse a": 10, "pulse 1": 3, "triangle": 7, "noise": 4, "dpcm": 6, "vrc6 saw": 6}
    for b in range(48):
        ch = chords[b]
        s = sect(b)
        calm = s == 2
        if b % 8 == 0:
            for t, v in base_lv.items():
                c.level(t, b, (eye_lv.get(t, v) if calm else v + (1 if s == 3 and t in ("noise", "dpcm") else 0)))
        c.melody("vrc6 pulse a", b, lead[b], 100, vib=(30, 1, 6))
        # bass: pumping roots (quarters in the eye)
        if calm:
            c.bass("triangle", b, ch, "R - - - R - - -", 33, 100, 2)
        else:
            c.bass("triangle", b, ch, "R R R R^ R R R R^", 33, 105, 2)
        # ostinato on pulse 1
        if calm:
            c.arp("pulse 1", b, ch, "R 5 R 5 R 5 R 5", 48, 85, 2)
        else:
            c.arp("pulse 1", b, ch, "R 5 R 5 R 5 R 5 R 5 R 5 R 5 R 5", 48, 90, 1)
        # saw drone: root then fifth, half bars (whole bar in the eye)
        if calm:
            c.put("vrc6 saw", b, 0, 16, ch.pitch("5", 52) , 80)
        else:
            c.put("vrc6 saw", b, 0, 8, ch.pitch("R", 48), 85)
            c.put("vrc6 saw", b, 8, 8, ch.pitch("5", 48), 80)
        # second pulse: echo of the lead (S2, S3, S5, S6), octave double (S4)
        if s in (1, 4, 5):
            for off, tok in _spans(lead[b]):
                n, p = tok
                if off + 2 + n <= c.spb:
                    c.put("pulse 2", b, off + 2, n, p, 70)
        elif s == 3:
            for off, tok in _spans(lead[b]):
                n, p = tok
                if p - 12 >= 48:
                    c.put("pulse 2", b, off, n, p - 12, 75)
        # harmony on pulse b: chord tone a sixth/third under the lead on S2 and S5
        if s in (1, 4):
            for off, tok in _spans(lead[b]):
                n, p = tok
                h = _below(ch, p, 3)
                if h is not None and 45 <= h <= 84:
                    c.put("vrc6 pulse b", b, off, n, h, 70)
        # drums
        if calm:
            c.drum_bar(b, kick="x.......x.......", snare="", hats="3030303030303030", idx=4, kvel=80, hscale=0.8)
        else:
            snare = "....x.......x..." if s != 3 else "....x...x...x..x"
            kick = "x.....x.x.......x.......x.x....."[:16] if False else "x.....x.x.....x."
            if b % 8 == 7:
                snare = "....x.....x.xxxx"
                kick = "x.......x......."
            hats = "9353535393535353" if s != 3 else "9353935393539353"
            c.drum_bar(b, kick=kick, snare=snare, hats=hats, idx=4, kvel=105, svel=105,
                       hscale=0.9 if s in (0, 5) else 1.0)
    return c


# ======================================================================================
# CUE 1b: PP-03 Harbor Storm, take B (pp_03_quay_storm_v2). Same key, tempo and length as
# the delivered take (A minor, 4/4, 160 bpm, 48 bars) because data/audio.json registers
# those three numbers for PP-03 and gamedev is a head on this project. What changes is the
# melody: the harbor tide's own fifth (A to E) followed by the title leitmotif's descending
# head, which makes every statement an arch with exactly one leap and mostly steps, and the
# filler sixteenths leave the gale so more of what the lead plays is the motif.
# ======================================================================================

# One statement, four notes, 16 steps: H's rise by a fifth, then L's stepwise fall.
# Every note that lands on a beat is a chord tone (the gate's CP-01 rule), the leap is
# the only one, and the shape rises to a peak then falls (the meter's arch).
H0 = "A4:4 E5:2 D5:2 C5:8"
H1 = "G4:4 D5:2 C5:2 B4:8"
H2 = "A4:4 C5:2 Bb4:2 A4:8"
H3 = "E4:4 B4:2 A4:2 G#4:8"
# The third return of every run closes differently: it falls past the fifth to the root.
H2V = "A4:4 C5:2 Bb4:2 A4:2 G4:2 F4:4"
# The two chords take B did not state before, written to the same rule.
HD = "D4:4 A4:2 G4:2 F4:8"
HBb = "Bb4:4 F5:2 G5:2 F5:8"
HOOK_B = [H0, H1, H2, H3, H0, H1, H2V]
TAIL_L = "E5:4 D5:2 C5:2 B4:8"

# The gale is four notes a bar instead of eight: the arpeggio keeps its shape and the
# sixteenth pickups that used to blur it are gone (the same fix take D of PP-04 made).
# The top note is short so no chord tone is held across a strong beat.
ARPS_B = ["A4:2 C5:2 E5:2 A5:6 r:4", "G4:2 B4:2 D5:2 G5:6 r:4",
          "F4:2 A4:2 C5:2 F5:6 r:4", "E4:2 G#4:2 B4:2 E5:6 r:4",
          "D4:2 F4:2 A4:2 D5:6 r:4", "A4:2 C5:2 E5:2 A5:6 r:4",
          "Bb4:2 D5:2 F5:2 Bb5:6 r:4", "E4:2 G#4:2 B4:2 E5:6 r:4"]


def storm_v2():
    c = Cue("pp_03_quay_storm_v2", "Harbor Storm (take B)", 160, 4, 48, "A minor")
    chords = (chords_of("Am G/B F E/G# Am G/B F E/G#") + chords_of("Am G/B F E/G# Dm/F Am Bb E")
              + chords_of("E E Am E Am E F Dm") + chords_of("Am G/B F E/G# Am G/B F E/G#")
              + chords_of("Am G/B F E/G# Dm/F Am Bb E") + chords_of("Am G/B F Dm/F Bb G/B E E"))
    lead = {}
    for i in range(7):
        lead[i] = HOOK_B[i]
    lead[7] = TAIL_L
    for i in range(8):
        lead[8 + i] = ARPS_B[i]
    eye = ["E5:6 D5:2 C5:2 B4:2 r:4", "B4:12 r:4", "E5:6 C5:2 D5:2 E5:2 r:4", "B4:6 G#4:2 A4:2 B4:2 r:4",
           "C5:6 A4:2 B4:2 C5:2 r:4", "B4:12 r:4", "F5:6 D5:2 E5:2 F5:2 r:4", "D5:8 r:8"]
    for i in range(8):
        lead[16 + i] = eye[i]
    for i in range(7):
        lead[24 + i] = HOOK_B[i]
    lead[31] = TAIL_L
    for i in range(8):
        lead[32 + i] = ARPS_B[i]
    # S6 is the delivered take's own rolling melody, kept note for note: it is the one
    # phrase already proved clean against this chord run (Am G/B F Dm/F Bb G/B E E), and
    # every rewrite of it in this take put a passing tone on a strong beat.
    roll = ["A4:6 C5:6 E5:4", "D5:6 B4:6 G4:4", "A4:6 C5:6 F5:4", "D5:2 F5:2 A5:2 F5:2 D5:6 r:2",
            "Bb4:2 D5:2 F5:2 D5:2 Bb4:6 r:2", "G4:2 B4:2 D5:2 B4:2 G4:6 r:2",
            "E5:2 B4:2 G#4:2 B4:2 E5:8", "E5:4 D5:2 C5:2 B4:4 G#4:4"]
    for i in range(8):
        lead[40 + i] = roll[i]

    c.sections = ["squall", "gale", "eye", "lightning", "gale2", "rolling"]
    base_lv = {"vrc6 pulse a": 11, "vrc6 pulse b": 4, "vrc6 saw": 5, "pulse 1": 5,
               "pulse 2": 4, "triangle": 8, "noise": 6, "dpcm": 8}
    for t, v in base_lv.items():
        c.cc(t, 0, 0, 11, v)
    c.cc("vrc6 pulse a", 0, 0, 12, 3)
    c.cc("vrc6 pulse b", 0, 0, 12, 3)
    c.cc("pulse 1", 0, 0, 12, 0)
    c.cc("pulse 2", 0, 0, 12, 1)
    eye_lv = {"vrc6 pulse a": 10, "pulse 1": 3, "triangle": 7, "noise": 4, "dpcm": 6, "vrc6 saw": 6}
    for b in range(48):
        ch = chords[b]
        s = b // 8
        calm = s == 2
        if b % 8 == 0:
            for t, v in base_lv.items():
                c.level(t, b, (eye_lv.get(t, v) if calm else v + (1 if s == 3 and t in ("noise", "dpcm") else 0)))
        c.melody("vrc6 pulse a", b, lead[b], 100, vib=(30, 1, 6))
        if calm:
            c.bass("triangle", b, ch, "R - - - R - - -", 33, 100, 2)
        else:
            c.bass("triangle", b, ch, "R R R R^ R R R R^", 33, 105, 2)
        if calm:
            c.arp("pulse 1", b, ch, "R 5 R 5 R 5 R 5", 48, 85, 2)
        else:
            c.arp("pulse 1", b, ch, "R 5 R 5 R 5 R 5 R 5 R 5 R 5", 48, 90, 1)
        if calm:
            c.put("vrc6 saw", b, 0, 16, ch.pitch("5", 52), 80)
        else:
            c.put("vrc6 saw", b, 0, 8, ch.pitch("R", 48), 85)
            c.put("vrc6 saw", b, 8, 8, ch.pitch("5", 48), 80)
        if s in (1, 4, 5):
            for off, tok in _spans(lead[b]):
                n, p = tok
                if off + 2 + n <= c.spb:
                    c.put("pulse 2", b, off + 2, n, p, 70)
        elif s == 3:
            for off, tok in _spans(lead[b]):
                n, p = tok
                if p - 12 >= 48:
                    c.put("pulse 2", b, off, n, p - 12, 75)
        if s in (1, 4):
            for off, tok in _spans(lead[b]):
                n, p = tok
                h = _below(ch, p, 3)
                if h is not None and 45 <= h <= 84:
                    c.put("vrc6 pulse b", b, off, n, h, 70)
        # drums: a different figure in each 4 bar block, and a different one again in each
        # 8 bar block, so the kit never repeats for a whole phrase (card requirement).
        q = (b % 8) // 4
        if calm:
            hats = "3030303030303030" if q == 0 else "3030303030302040"
            c.drum_bar(b, kick="x.......x.......", snare="", hats=hats, idx=4, kvel=80, hscale=0.8)
        else:
            if b % 8 == 7:
                # last bar of an 8 bar block: the roll and the open hat, the block's signature
                c.drum_bar(b, kick="x.......x.......", snare="....x.....x.xxxx",
                           hats="9393939393939393", idx=4, kvel=105, svel=105, hscale=1.0)
            elif q == 0:
                c.drum_bar(b, kick="x.....x.x.....x.", snare="....x.......x...",
                           hats="9353535393535353", idx=4, kvel=105, svel=105,
                           hscale=0.9 if s in (0, 5) else 1.0)
            elif q == 1:
                c.drum_bar(b, kick="x..x..x.x.....x.", snare="....x.......x...",
                           hats="9393535393935353", idx=4, kvel=105, svel=105,
                           hscale=0.9 if s in (0, 5) else 1.0)
            elif q == 2:
                c.drum_bar(b, kick="x.....x.x.....x.", snare="....x.......x.x",
                           hats="9353535393935393", idx=4, kvel=105, svel=105,
                           hscale=0.9 if s in (0, 5) else 1.0)
            else:
                c.drum_bar(b, kick="x.......x...x...", snare="....x.......xx.x",
                           hats="9393535393539353", idx=4, kvel=105, svel=105,
                           hscale=0.9 if s in (0, 5) else 1.0)
    return c


def _spans(spec):
    out = []
    cur = 0
    for tok in spec.split():
        name, n = tok.split(":")
        n = int(n)
        if name != "r":
            out.append((cur, (n, midi(name))))
        cur += n
    return out


def _below(chord, pitch, min_gap):
    """Highest chord tone at least min_gap semitones below pitch."""
    for p in range(pitch - min_gap, pitch - 15, -1):
        if p % 12 in chord.tones:
            return p
    return None



FLAT_NAMES = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def transpose_chord(sym, n):
    m = CHORD_RE.match(sym)
    root, q, bass = m.groups()
    out = FLAT_NAMES[(pc_of(root) + n) % 12] + (q or "")
    if bass:
        out += "/" + FLAT_NAMES[(pc_of(bass) + n) % 12]
    return out


def _spans_shift(spec, shift):
    return [(o, (n, p + shift)) for o, (n, p) in _spans(spec)]


# ======================================================================================
# CUE 2: PP-06 Percy, possessed. E minor then G minor, 3/4, 150 bpm, 48 bars (57.600 s).
# The title leitmotif L is stated whole (shifted a fifth down to E minor), the harbor tide H
# becomes one arpeggio per bar, and the second statement climbs a minor third.
# ======================================================================================

PERCY_L = ["B4:6 A4:2 G4:2 F#4:2", "B4:12", "B4:6 G4:2 A4:2 B4:2", "F#4:6 D#4:2 E4:2 F#4:2",
           "G4:6 E4:2 F#4:2 G4:2", "F#4:12", "E4:4 G4:4 B4:4", "D#5:6 B4:6"]
PERCY_H = ["E4:2 G4:2 B4:2 E5:2 B4:2 G4:2", "D5:2 A4:2 F#4:2 A4:2 D5:2 A4:2",
           "C5:2 G4:2 E4:2 G4:2 C5:2 G4:2", "B4:2 F#4:2 D#4:2 F#4:2 B4:2 D#5:2",
           "E4:2 G4:2 B4:2 E5:2 B4:2 G4:2", "D5:2 A4:2 F#4:2 A4:2 D5:2 A4:2",
           "C5:2 G4:2 E4:2 G4:2 C5:2 G4:2", "B4:2 D#5:2 F#5:2 D#5:2 B4:4"]
PERCY_LC = "Em Em Em B/D# Em B Em B"
PERCY_HC = "Em/G D C B Em/G D C B"


def percy():
    c = Cue("pp_06_percy_possessed", "Percy, Possessed", 150, 3, 48, "E minor")
    plan = [(PERCY_L, PERCY_LC, 0), (PERCY_H, PERCY_HC, 0), (PERCY_L, PERCY_LC, 3),
            (PERCY_H, PERCY_HC, 3), (PERCY_L, PERCY_LC, 0), (PERCY_H, PERCY_HC, 0)]
    c.sections = ["possession", "tide", "rise", "tide up", "possession again", "drowning"]
    base = {"vrc6 pulse a": 11, "vrc6 pulse b": 5, "vrc6 saw": 5, "pulse 1": 5,
            "pulse 2": 4, "triangle": 8, "noise": 6, "dpcm": 9}
    for t, v in base.items():
        c.cc(t, 0, 0, 11, v)
    c.cc("vrc6 pulse a", 0, 0, 12, 2)
    c.cc("vrc6 pulse b", 0, 0, 12, 1)
    c.cc("pulse 1", 0, 0, 12, 0)
    c.cc("pulse 2", 0, 0, 12, 1)
    for si, (leads, chs, sh) in enumerate(plan):
        chords = [Chord(transpose_chord(x, sh)) for x in chs.split()]
        for i in range(8):
            b = si * 8 + i
            ch = chords[i]
            if i == 0 and si:
                for t, v in base.items():
                    c.level(t, b, v + (1 if si >= 4 and t in ("noise", "dpcm") else 0))
            c.melody("vrc6 pulse a", b, leads[i], 100, vib=(35, 1, 6), shift=sh)
            c.bass("triangle", b, ch, "R R R R R R^", 33, 105, 2)
            c.arp("pulse 1", b, ch, "R 5 R 5 R 5 R 5 R 5 R 5", 48, 88, 1)
            c.put("vrc6 saw", b, 0, 12, ch.pitch("5", 48), 85)
            if si in (1, 3, 5):
                for off, (n, p) in _spans_shift(leads[i], sh):
                    if off + 2 + n <= c.spb:
                        c.put("pulse 2", b, off + 2, n, p, 70)
                    h = _below(ch, p, 3)
                    if h is not None and h >= 45:
                        c.put("vrc6 pulse b", b, off, n, h, 70)
            elif si == 4:
                for off, (n, p) in _spans_shift(leads[i], sh):
                    if p - 12 >= 48:
                        c.put("pulse 2", b, off, n, p - 12, 75)
            snare = "....x...x..." if i != 7 else "....x.x.x.xx"
            kick = "x..........."
            hats = "933533533533" if si % 2 == 0 else "935535535535"
            c.drum_bar(b, kick=kick, snare=snare, hats=hats, idx=5, kvel=108, svel=100, hscale=0.9)
    return c


# ======================================================================================
# CUE 2b: PP-06 Percy, possessed, take B (pp_06_percy_possessed_v2, card t_809cc617).
# Same key, tempo and length as the delivered take (E minor, 3/4, 150 bpm, 48 bars) because
# data/audio.json registers those numbers for PP-06 and gamedev is a head on this project.
# The delivered take scored 52 / 100 on tools/hook_score.py: motif coverage 23 percent, 0
# percent steps over leaps (6 leaps), no arch or pedal on any return, the third return a
# straight copy. Take B answers the meter directly with one 2 bar motif that owns the whole
# cue: bar one holds a pedal B, bar two is an arch with exactly one leap, every note that
# lands on a quarter is a chord tone (the gate's CP-01 rule), and the third return of every
# four statements starts differently and drops the leap.
# ======================================================================================

# Pedal B over a five note cell: durations 4 2 2 2 2 repeat every bar, which is what the
# meter's hook cell rule asks for (a cell that reappears at non overlapping places), the
# phrase stays inside a five semitone window so its contour reads as a pedal, and every
# note that lands on a quarter (steps 0, 4 and 8) is a chord tone.
P6_X1 = "B4:4 B4:2 A4:2 B4:2 C5:2"
# Up a third then a stepwise fall to the low sixth and back: the only interval of four or
# more semitones in the motif is the drop from B to G, which is the meter's one leap.
P6_X2 = "B4:4 G4:2 A4:2 B4:2 A4:2"
# The third return starts its second bar on the sixth instead of the fifth.
P6_X2V = "G4:4 B4:2 A4:2 B4:2 C5:2"
# Section six only: the tide bar sinks to the low tonic before the cadence.
P6_E1 = "B4:4 A4:2 G4:2 E4:2 G4:2"
# The last bar of the loop: a plain arpeggio down to the tonic so the seam is a cadence.
P6_E2 = "B4:4 G4:2 A4:2 B4:2 E4:2"

# (shift, chord on bar one, chord on bar two, bar one notes, bar two notes). Two bars per
# row, 24 rows, six sections of four rows. Sections three and four climb a minor third.
# Bar one chords carry B (Em, G, B) and bar two chords carry B and E (Em, E), which is
# what the motif's quarter notes ask for; a minor third up the same two rules read Gm, Bb,
# D on bar one and Gm, G on bar two.
P6_PLAN = [
    (0, "Em", "Em", P6_X1, P6_X2), (0, "G", "Em", P6_X1, P6_X2),
    (0, "B", "Em", P6_X1, P6_X2V), (0, "Em", "Em", P6_X1, P6_X2),
    (0, "G", "Em", P6_X1, P6_X2), (0, "Em", "Em", P6_X1, P6_X2V),
    (0, "B", "Em", P6_X1, P6_X2), (0, "G", "Em", P6_X1, P6_X2),
    (3, "Em", "Em", P6_X1, P6_X2), (3, "G", "Em", P6_X1, P6_X2),
    (3, "B", "Em", P6_X1, P6_X2V), (3, "Em", "Em", P6_X1, P6_X2),
    (3, "G", "Em", P6_X1, P6_X2), (3, "Em", "Em", P6_X1, P6_X2V),
    (3, "B", "Em", P6_X1, P6_X2), (3, "G", "Em", P6_X1, P6_X2),
    (0, "Em", "Em", P6_X1, P6_X2), (0, "G", "Em", P6_X1, P6_X2),
    (0, "B", "Em", P6_X1, P6_X2V), (0, "Em", "Em", P6_X1, P6_X2),
    (0, "G", "Em", P6_X1, P6_X2), (0, "Em", "Em", P6_X1, P6_X2V),
    (0, "Em", "Em", P6_E1, P6_X2), (0, "Em", "Em", P6_X1, P6_E2),
]


def percy_v2():
    c = Cue("pp_06_percy_possessed_v3", "Percy, Possessed (take C)", 150, 3, 48, "E minor")
    c.sections = ["possession", "tide", "rise", "tide up", "possession again", "drowning"]
    base = {"vrc6 pulse a": 11, "vrc6 pulse b": 5, "vrc6 saw": 5, "pulse 1": 5,
            "pulse 2": 4, "triangle": 8, "noise": 6, "dpcm": 9}
    for t, v in base.items():
        c.cc(t, 0, 0, 11, v)
    c.cc("vrc6 pulse a", 0, 0, 12, 2)
    c.cc("vrc6 pulse b", 0, 0, 12, 1)
    c.cc("pulse 1", 0, 0, 12, 0)
    c.cc("pulse 2", 0, 0, 12, 1)
    # A small velocity table so no two bars of the lead arrive at the same level, and a
    # two bar swell per section instead of one flat CC11 for the whole cue.
    vel_of = (100, 102, 99, 101)
    for si, (sh, csym1, csym2, bar1, bar2) in enumerate(P6_PLAN):
        chords = [Chord(transpose_chord(csym1, sh)), Chord(transpose_chord(csym2, sh))]
        for half in range(2):
            b = si * 2 + half
            ch = chords[half]
            spec = bar1 if half == 0 else bar2
            if half == 0 and si % 4 == 0:
                for t, v in base.items():
                    swell = v + (1 if si >= 4 and t in ("noise", "dpcm") else 0)
                    c.level(t, b, swell)
            c.level("vrc6 pulse a", b, 10 + (1 if b % 4 == 0 else 0))
            c.melody("vrc6 pulse a", b, spec, vel_of[b % 4], vib=(35, 1, 4), shift=sh)
            if si in (1, 2, 3):
                c.bass("triangle", b, ch, "R R R R R R", 33, 105, 2)
            elif si in (4, 5):
                c.bass("triangle", b, ch, "R - R R - R^", 33, 105, 2)
            elif si in (21, 22):
                c.bass("triangle", b, ch, "R - -", 33, 100, 4)
            else:
                c.bass("triangle", b, ch, "R - R - R R", 33, 100, 2)
            if si in (2, 3):
                c.arp("pulse 1", b, ch, "R 5 R 5 R 5", 60, 92, 2)
            elif si in (22, 23):
                c.arp("pulse 1", b, ch, "R 5 3 5 R 5", 48, 78, 2)
            else:
                c.arp("pulse 1", b, ch, "R 5 R 5 R 5", 48, 88, 2)
            if si in (22, 23):
                c.put("vrc6 saw", b, 0, 12, ch.pitch("R", 48), 80)
            else:
                c.put("vrc6 saw", b, 0, 6, ch.pitch("5", 48), 85)
                c.put("vrc6 saw", b, 6, 6, ch.pitch("R", 48), 80)
            if si in (1, 3, 5):
                for off, (n, p) in _spans_shift(spec, sh):
                    if off + 2 + n <= c.spb:
                        c.put("pulse 2", b, off + 2, n, p, 70)
                    h = _below(ch, p, 3)
                    if h is not None and 45 <= h <= 84:
                        c.put("vrc6 pulse b", b, off, n, h, 70)
            elif si in (4, 21):
                for off, (n, p) in _spans_shift(spec, sh):
                    if p - 12 >= 48:
                        c.put("pulse 2", b, off, n, p - 12, 72)
            # drums: one figure per 4 bar block, a different one again in each 8 bar block,
            # and the last bar of every 8 takes the fill, so the kit never holds one bar for
            # a whole phrase (card requirement).
            q = (b % 8) // 4
            if b % 8 == 7:
                c.drum_bar(b, kick="x...........", snare="....x.x.x.xx",
                           hats="939393939393", idx=5, kvel=108, svel=104, hscale=0.95)
            elif q == 0:
                c.drum_bar(b, kick="x...x...x...", snare="....x.......",
                           hats="933533533533", idx=5, kvel=108, svel=100, hscale=0.9)
            elif q == 1:
                c.drum_bar(b, kick="x.....x.x...", snare="....x...x...",
                           hats="935535535535", idx=5, kvel=108, svel=100, hscale=0.9)
            else:
                c.drum_bar(b, kick="x...x.....x.", snare="....x.......",
                           hats="939353539393", idx=5, kvel=106, svel=101, hscale=0.85)
    return c


# ======================================================================================
# CUE 3: PP-15a credits, Percy killed. A minor, 4/4, 72 bpm, 24 bars (80.000 s).
# The leitmotif is stated whole, then erased note by note, and the loop begins it again.
# ======================================================================================

def kill():
    c = Cue("pp_15a_credits_kill", "Entropy", 72, 4, 24, "A minor")
    chords = (chords_of("Am E Am E F G Am E") + chords_of("Am E Am E F G Am E")
              + chords_of("Am Am F F G G E Am"))
    intact = ["E5:6 D5:2 C5:2 B4:6", "B4:12 r:4", "E5:6 C5:2 D5:2 E5:2 r:4", "B4:6 G#4:2 A4:2 B4:2 r:4",
              "C5:6 A4:2 B4:2 C5:2 r:4", "B4:12 r:4", "E5:6 C5:2 D5:2 E5:2 r:4", "B4:12 r:4"]
    erased = ["E5:6 D5:2 r:8", "B4:6 r:10", "E5:6 r:10", "r:16",
              "C5:6 r:10", "r:16", "E5:4 r:12", "r:16"]
    last = ["r:16", "r:16", "C5:12 r:4", "r:16", "B4:12 r:4", "r:16", "G#4:8 B4:8", "A4:16"]
    lead = intact + erased + last
    base = {"vrc6 pulse a": 10, "vrc6 pulse b": 4, "vrc6 saw": 6, "pulse 1": 4,
            "pulse 2": 4, "triangle": 8, "noise": 3, "dpcm": 5}
    for t, v in base.items():
        c.cc(t, 0, 0, 11, v)
    c.cc("vrc6 pulse a", 0, 0, 12, 3)
    c.cc("vrc6 pulse b", 0, 0, 12, 3)
    c.cc("pulse 1", 0, 0, 12, 2)
    c.cc("pulse 2", 0, 0, 12, 1)
    for b in range(24):
        ch = chords[b]
        s = b // 8
        c.melody("vrc6 pulse a", b, lead[b], 95, vib=(40, 2, 6))
        if b == 23:
            c.bass("triangle", b, ch, "R - - R", 33, 95, 4)
        else:
            c.bass("triangle", b, ch, "R - - - R - - -" if s < 2 else "R - - - - - - -", 33, 95, 2)
        c.arp("pulse 1", b, ch, "R 5 3^ 5 R 5 3^ 5" if s < 2 else "R - 5 - 3^ - 5 -", 48, 75, 2)
        c.put("vrc6 saw", b, 0, 16, ch.pitch("R", 48), 85)
        if s == 0:
            for off, (n, p) in _spans(lead[b]):
                h = _below(ch, p, 3)
                if h is not None and h >= 45:
                    c.put("vrc6 pulse b", b, off, n, h, 60)
                if off + 4 + n <= c.spb:
                    c.put("pulse 2", b, off + 4, n, p, 55)
        if s == 0:
            c.drum_bar(b, kick="x.......x.......", snare="", hats="5030503050305030", idx=4, kvel=70, hscale=0.6)
        elif s == 1:
            c.drum_bar(b, kick="x...............", snare="", hats="3000300030003000", idx=4, kvel=60, hscale=0.5)
    return c


# ======================================================================================
# CUE 4: PP-15b credits, Percy spared. A major, 4/4, 144 bpm, 32 bars (53.333 s).
# The leitmotif in the sun, the harbor tide rising in major, Morgan's cell as a bounce.
# ======================================================================================

SPARE_S1 = ["E5:2 D5:2 C#5:2 B4:2 A4:8", "G#4:4 B4:4 E5:8", "D5:2 C#5:2 B4:2 A4:2 F#4:8",
            "A4:2 C#5:2 E5:2 C#5:2 A4:8", "F#5:2 E5:2 C#5:2 E5:2 F#5:8", "G#5:2 E5:2 B4:2 E5:2 G#4:8",
            "D5:2 F#5:2 A5:2 F#5:2 D5:8", "E5:2 B4:2 G#4:2 B4:2 E5:6 r:2"]
SPARE_S3 = ["E4:2 F#4:2 E4:2 A4:2 B4:2 A4:6", "A4:2 B4:2 A4:2 D5:2 E5:2 D5:6",
            "B4:2 C#5:2 B4:2 E5:2 F#5:2 E5:6", "E5:2 F#5:2 E5:2 A5:2 B5:2 A5:6",
            "A4:2 B4:2 A4:2 D5:2 E5:2 D5:6", "B4:2 C#5:2 B4:2 E5:2 F#5:2 E5:6",
            "C#5:2 E5:2 A5:2 E5:2 C#5:8", "G#4:4 B4:4 E5:8"]


def spare():
    c = Cue("pp_15b_credits_spare", "Mercy", 144, 4, 32, "A major")
    c1 = "A E D A F#m E D E"
    c3 = "A D E A D E A E"
    chords = chords_of(c1) + chords_of(c1) + chords_of(c3) + chords_of(c1)
    lead = SPARE_S1 + SPARE_S1 + SPARE_S3 + SPARE_S1
    base = {"vrc6 pulse a": 11, "vrc6 pulse b": 5, "vrc6 saw": 5, "pulse 1": 5,
            "pulse 2": 4, "triangle": 8, "noise": 5, "dpcm": 8}
    for t, v in base.items():
        c.cc(t, 0, 0, 11, v)
    c.cc("vrc6 pulse a", 0, 0, 12, 3)
    c.cc("vrc6 pulse b", 0, 0, 12, 3)
    c.cc("pulse 1", 0, 0, 12, 1)
    c.cc("pulse 2", 0, 0, 12, 1)
    for b in range(32):
        ch = chords[b]
        s = b // 8
        c.melody("vrc6 pulse a", b, lead[b], 100, vib=(25, 1, 8))
        c.bass("triangle", b, ch, "R R 5 5 R R 5 5", 33, 100, 2)
        c.arp("pulse 1", b, ch, "- 3 - 5 - 3 - 5", 57, 80, 2)
        c.put("vrc6 saw", b, 0, 16, ch.pitch("R", 45), 70)
        if s in (1, 3):
            for off, (n, p) in _spans(lead[b]):
                h = _below(ch, p, 3)
                if h is not None and h >= 45:
                    c.put("vrc6 pulse b", b, off, n, h, 70)
                if p - 12 >= 48:
                    c.put("pulse 2", b, off, n, p - 12, 60)
        fill = b % 8 == 7
        c.drum_bar(b, kick="x.......x.......",
                   snare="....x.......x..." if not fill else "....x...x.x.xxxx",
                   hats="9050905090509050" if s != 3 else "9353935393539353", idx=4, kvel=95, svel=95, hscale=0.8)
    return c


# ======================================================================================
# CUE 5: PP-15b take B (card t_17870e1f). Same cue sheet facts as the shipped
# pp_15b_credits_spare: A major, 4/4, 144 bpm, 32 bars, same chord plan. The take changes
# the melody's shape, not the sheet.
#
# Why: the shipped take scores 61 / 100 on tools/hook_score.py and its worst criterion is
# motif coverage, 19 percent of 158 notes inside the motif, because its eight bar sections
# never restate one phrase. Take B writes a two bar cell and states it in every unit:
#
#   bar 1 (rise): B4 C#5 D5 E5 F#5 F#5 E5   steps up to the peak, the peak repeated
#   bar 2 (fall): D5 C#5 B4 A4 G#4 E4       steps down, one leap (G#4 to E4) to close
#
# That is 13 notes, 92 percent steps (11 of 12 intervals), exactly one leap, 14 semitones
# of range (E4 to F#5), a repeated pitch, and an arch shape (up five, down eight). The third
# statement of each four raises the peak to A5 and ends on C#5 instead of E4, so the third
# return is not a copy: the meter reads it 77 percent the same as the first. Four bars carry a
# chromatic D# appoggiatura that resolves up a semitone into E, 4 of 211 melody notes, 1.9
# percent, under the 3 to 6 percent budget of knowledge/MUSIC-DISSONANCE.md, and no device
# sits on a statement's first or last note (F1) or in a cadence bar (F2).
#
# State at the last build: hook_score 91 / 100 (was 61), seam clean, and the counterpoint cue
# gate still REFUSED with 15 CP-01 findings, all on beat 3.0, where a melody note held across
# the beat meets the bass root a second above it. Take B is therefore measured better and not
# yet shippable; the record is assets/audio/pp_15b_credits_spare_v2/TAKE-B-2026-11-11.md.
# ======================================================================================

SPARE2_M1 = "B4:2 C#5:2 D5:2 E5:4 F#5:2 F#5:2 E5:2"
SPARE2_M2 = "D5:2 C#5:2 B4:2 A4:4 G#4:2 E4:4"
SPARE2_M3 = "B4:2 C#5:2 D5:2 E5:4 A5:2 A5:2 E5:2"
SPARE2_M4 = "D5:2 C#5:2 B4:2 A4:4 G#4:2 C#5:4"
SPARE2_END = "D5:2 C#5:2 B4:2 A4:2 A4:6 r:2"
# the appoggiatura bar: G#4 splits into D#4 (a semitone under E) then E4, which resolves it
SPARE2_M2D = "D5:2 C#5:2 B4:2 A4:4 G#4:2 D#4:2 E4:2"

SPARE2_PLAN = [
    ("A", "E", SPARE2_M1, SPARE2_M2),      # bars 1-2, statement 1
    ("D", "A", SPARE2_M1, SPARE2_M2),      # bars 3-4, statement 2
    ("F#m", "E", SPARE2_M3, SPARE2_M4),    # bars 5-6, statement 3, varied
    ("D", "E", SPARE2_M1, SPARE2_M2),      # bars 7-8
    ("A", "E", SPARE2_M1, SPARE2_M2),      # bars 9-10
    ("D", "A", SPARE2_M1, SPARE2_M2D),     # bars 11-12, device
    ("F#m", "E", SPARE2_M3, SPARE2_M4),    # bars 13-14
    ("D", "E", SPARE2_M1, SPARE2_M2D),     # bars 15-16, device
    ("A", "D", SPARE2_M1, SPARE2_M2),      # bars 17-18
    ("E", "A", SPARE2_M1, SPARE2_M2),      # bars 19-20
    ("D", "E", SPARE2_M3, SPARE2_M4),      # bars 21-22
    ("A", "E", SPARE2_M1, SPARE2_M2D),     # bars 23-24, device
    ("A", "E", SPARE2_M1, SPARE2_M2),      # bars 25-26
    ("D", "A", SPARE2_M1, SPARE2_M2D),     # bars 27-28, device
    ("F#m", "E", SPARE2_M3, SPARE2_M4),    # bars 29-30
    ("D", "E", SPARE2_M1, SPARE2_END),     # bars 31-32, cadence on the tonic
]


def spare_v2():
    c = Cue("pp_15b_credits_spare_v2", "Mercy (take B)", 144, 4, 32, "A major")
    c.sections = ["sunrise", "tide", "rise", "home"]
    base = {"vrc6 pulse a": 11, "vrc6 pulse b": 5, "vrc6 saw": 5, "pulse 1": 5,
            "pulse 2": 4, "triangle": 8, "noise": 5, "dpcm": 8}
    for t, v in base.items():
        c.cc(t, 0, 0, 11, v)
    c.cc("vrc6 pulse a", 0, 0, 12, 3)
    c.cc("vrc6 pulse b", 0, 0, 12, 3)
    c.cc("pulse 1", 0, 0, 12, 1)
    c.cc("pulse 2", 0, 0, 12, 1)
    vel_of = (100, 102, 99, 101)
    for unit, (c1sym, c2sym, bar1, bar2) in enumerate(SPARE2_PLAN):
        for half in range(2):
            b = unit * 2 + half
            s = b // 8
            ch = Chord(c1sym if half == 0 else c2sym)
            spec = bar1 if half == 0 else bar2
            if half == 0 and b % 8 == 0:
                # a two bar swell at each section head, so no section arrives flat
                for t, v in base.items():
                    c.level(t, b, v + (1 if s >= 2 else 0))
            c.level("vrc6 pulse a", b, 10 + (1 if b % 4 == 0 else 0))
            c.melody("vrc6 pulse a", b, spec, vel_of[b % 4], vib=(25, 1, 8))
            if s == 0:
                c.bass("triangle", b, ch, "R R 5 5 R R 5 5", 33, 100, 2)
            elif s == 1:
                c.bass("triangle", b, ch, "R - R R 5 - 5 R", 33, 102, 2)
            elif s == 2:
                c.bass("triangle", b, ch, "R - 5 -", 33, 104, 4)
            else:
                c.bass("triangle", b, ch, "R R - 5 R R R R", 33, 98, 2)
            if s == 2:
                c.arp("pulse 1", b, ch, "R - 5 - 3 - 5 -", 57, 82, 2)
            elif s == 1:
                c.arp("pulse 1", b, ch, "R 3 5 3 R 3 5 3", 57, 78, 2)
            else:
                c.arp("pulse 1", b, ch, "- 3 - 5 - 3 - 5", 57, 80, 2)
            c.put("vrc6 saw", b, 0, 16, ch.pitch("R", 48 if s == 2 else 45), 70)
            if s in (1, 3):
                for off, (n, p) in _spans(spec):
                    h = _below(ch, p, 3)
                    if h is not None and 45 <= h <= 84:
                        c.put("vrc6 pulse b", b, off, n, h, 70)
                    if p - 12 >= 48:
                        c.put("pulse 2", b, off, n, p - 12, 60)
            elif s == 2:
                for off, (n, p) in _spans(spec):
                    if p - 12 >= 48 and off % 4 == 2:
                        c.put("pulse 2", b, off, n, p - 12, 62)
            # drums: one figure per four bar block, a different one again in each eight bar
            # block, and the eighth bar takes the fill, so the kit never holds one figure for
            # a whole phrase (card requirement).
            idx = 5 if s == 2 else 4
            q = (b % 8) // 4
            if b % 8 == 7:
                c.drum_bar(b, kick="x.....x.........", snare="....x...x.x.xxxx",
                           hats="9353935393539353", idx=idx, kvel=100, svel=100, hscale=0.9)
            elif b % 8 == 3:
                c.drum_bar(b, kick="x...............", snare="........x.......",
                           hats="9000900093579357", idx=idx, kvel=88, svel=92, hscale=0.7)
            elif q == 0:
                c.drum_bar(b, kick="x.......x.......", snare="....x.......x...",
                           hats="9050905090509050", idx=idx, kvel=95, svel=95, hscale=0.8)
            else:
                c.drum_bar(b, kick="x...x.......x...", snare="....x.......x...",
                           hats="9353935393539353", idx=idx, kvel=97, svel=95, hscale=0.85)
    return c


# ======================================================================================
# CUE 6: PP-15a take B (card t_7acb517d, 2026-11-12). Same cue sheet facts as the
# shipped pp_15a_credits_kill: A minor, 4/4, 72 bpm, 32 bars, the title leitmotif
# stated whole and then erased note by note. Take B changes the shape of the theme,
# not the sheet, except the loop length.
#
# Why: the shipped take scores 71 / 100 on tools/hook_score.py. Its two measured
# weaknesses are contour (returns that neither arch nor hold a pedal) and leaps (0 per
# motif). It is also 24 bars, and the hook grammar's loop lengths are 8, 16 and 32, so
# it gives away that criterion outright. It has no ear review on record at all.
#
# Take B writes one two bar cell and states it eleven times:
#
#   bar 1 (rise):  A4 B4 C5 D5 E5 E5          stepwise rise to a held peak, the peak repeated
#   bar 2 (fall):  E5 D5 C5 B4 A4 E4          stepwise fall, one leap (A4 to E4, 7 semitones)
#
# That is 12 notes, 91 percent steps (10 of 11 intervals), exactly one leap, a repeated pitch
# and one turn in the contour, so every return reads as an arch. The third statement of each
# phrase raises the peak to A5 (range 17 semitones from E4, still under the 18 limit) so the
# third return is 83 percent the same rather than a copy. Every 8 bar section restates the cell,
# so motif coverage is 81 percent. The last four units erase the head of the cell, which is the
# cue's brief, and the final bar holds one tonic A4 over a whole bar triangle pedal.
#
# Chromatic budget: five melody notes of 167 (3.0 percent, inside the 3 to 6 percent band of
# knowledge/MUSIC-DISSONANCE.md). All five are D#4 appoggiaturas, a semitone under E4, resolving
# up by step into E4 over the E chord (bars 12, 20, 24, 28, 30). Each one is prepared by the G#4
# before it, sits off the first and last note of a statement (F1), and none is in the cadence
# bar 32 (F2).
#
# Measured 2026-11-12: hook_score 97 / 100 (was 71), cue gate PASS with 0 CP-01 and 0 CP-09,
# seam clean (level delta +3.84 dB), -14.07 LUFS, -1.18 dBTP, 106.667 s, 72.01 bpm measured.
# The record is assets/audio/pp_15a_credits_kill_v2/TAKE-B-2026-11-12.md. The seam needs the
# whole bar triangle pedal in the last bar: every other voice in render_chip decays to zero at
# its own note end, so a bar that stops on the loop point is silent exactly at the seam.
# ======================================================================================

KILL2_M1 = "A4:2 B4:1 C5:1 D5:2 E5:2 E5:8"
KILL2_M2 = "E5:2 D5:1 C5:1 B4:2 A4:2 E4:8"
KILL2_M3 = "A4:2 B4:1 C5:1 D5:2 A5:2 A5:8"
KILL2_M4 = "A5:2 G5:1 E5:1 D5:2 C5:2 A4:8"
# the device bar: G#4 splits into D#4, a semitone under E4, and resolves up into it
KILL2_M2D = "E5:2 D5:1 C5:1 B4:2 G#4:2 D#4:2 E4:6"
# erasure: the head goes first, so what is left is the tail of the cell and then holes
KILL2_M1E = "r:4 D5:2 E5:2 E5:8"
KILL2_M2E = "E5:2 r:6 A4:2 r:6"
KILL2_M2ED = "r:4 A4:2 G#4:2 D#4:2 E4:2 r:4"
KILL2_M3E = "r:8 A5:8"
KILL2_END_A = "r:8 E5:2 r:6"
KILL2_END_B = "A4:12 A4:4"

KILL2_PLAN = [
    ("Am", "E", KILL2_M1, KILL2_M2),    # bars 1-2, statement 1
    ("F", "E", KILL2_M1, KILL2_M2),     # bars 3-4
    ("Am", "E", KILL2_M3, KILL2_M2),    # bars 5-6, third return, peak raised
    ("C", "E", KILL2_M1, KILL2_M2),     # bars 7-8
    ("Am", "E", KILL2_M1, KILL2_M2),    # bars 9-10
    ("F", "E", KILL2_M1, KILL2_M2D),    # bars 11-12, device
    ("Dm", "E", KILL2_M3, KILL2_M4),    # bars 13-14
    ("G", "E", KILL2_M1, KILL2_M2),     # bars 15-16
    ("Am", "E", KILL2_M1, KILL2_M2),    # bars 17-18
    ("F", "E", KILL2_M1, KILL2_M2D),    # bars 19-20, device
    ("Am", "E", KILL2_M3, KILL2_M2),    # bars 21-22
    ("C", "E", KILL2_M1, KILL2_M2D),    # bars 23-24, device
    ("Am", "E", KILL2_M1E, KILL2_M2E),  # bars 25-26, erasure starts
    ("F", "E", KILL2_M1E, KILL2_M2ED),  # bars 27-28, device inside the erasure
    ("Dm", "E", KILL2_M3E, KILL2_M2ED), # bars 29-30
    ("F", "Am", KILL2_END_A, KILL2_END_B),  # bars 31-32, cadence on the tonic
]


def kill_v2():
    c = Cue("pp_15a_credits_kill_v2", "Entropy (take B)", 72, 4, 32, "A minor")
    c.sections = ["whole", "thinning", "erasing", "last light"]
    base = {"vrc6 pulse a": 10, "vrc6 pulse b": 4, "vrc6 saw": 6, "pulse 1": 4,
            "pulse 2": 4, "triangle": 8, "noise": 3, "dpcm": 5}
    for t, v in base.items():
        c.cc(t, 0, 0, 11, v)
    c.cc("vrc6 pulse a", 0, 0, 12, 3)
    c.cc("vrc6 pulse b", 0, 0, 12, 3)
    c.cc("pulse 1", 0, 0, 12, 2)
    c.cc("pulse 2", 0, 0, 12, 1)
    vel_of = (95, 98, 93, 96)
    for unit, (c1sym, c2sym, bar_a, bar_b) in enumerate(KILL2_PLAN):
        for half in range(2):
            b = unit * 2 + half
            s = b // 8
            spec = bar_a if half == 0 else bar_b
            ch = Chord(c1sym if half == 0 else c2sym)
            # a level move at each section head and at each four bar half, so the
            # texture changes on the 4 and the 8
            if b % 4 == 0:
                for t, v in base.items():
                    c.level(t, b, max(1, v + (b // 8) - (1 if b >= 24 else 0)))
            c.melody("vrc6 pulse a", b, spec, vel_of[b % 4], vib=(40, 2, 6))
            if b == 31:
                # the triangle voice is the one with no decay envelope, so a whole bar
                # tonic under the last bar is what keeps the level at the loop point
                root = 33 + ((ch.bass - 33) % 12)
                c.put("triangle", 31, 0, 16, root, 92)
            elif spec == KILL2_END_B:
                c.bass("triangle", b, ch, "R - - - - - - -", 33, 92, 2)
            elif s == 0:
                c.bass("triangle", b, ch, "R - - - - - 5 -", 33, 95, 2)
            elif s == 1:
                c.bass("triangle", b, ch, "R - - R - R - -", 33, 96, 2)
            elif s == 2:
                c.bass("triangle", b, ch, "R - - - - - - -", 33, 90, 2)
            else:
                c.bass("triangle", b, ch, "R - - - - - - -", 33, 86, 2)
            if s == 0:
                c.arp("pulse 1", b, ch, "R - 5 - - - 3 -", 48, 75, 2)
            elif s == 1:
                c.arp("pulse 1", b, ch, "R 3 5 3 - 3 5 -", 48, 72, 2)
            elif s == 2:
                c.arp("pulse 1", b, ch, "R - 3 - - - 3 -", 48, 66, 2)
            else:
                c.arp("pulse 1", b, ch, "- - - R", 48, 58, 4)
            # pad: the root, except on an F chord, where the root a seventh under the
            # held E5 is the one raw clash the gate still counts, so the third sounds
            pad_tok = "3" if "F" in (c1sym, c2sym) else "R"
            if spec == KILL2_END_B:
                # two pad attacks in the last bar, so the level at the loop point is a
                # fresh note rather than the tail of a three second decay
                c.put("vrc6 saw", b, 0, 8, ch.pitch(pad_tok, 45), 70)
                c.put("vrc6 saw", b, 8, 8, ch.pitch(pad_tok, 45), 74)
            else:
                c.put("vrc6 saw", b, 0, 16, ch.pitch(pad_tok, 48 if s >= 2 else 45), 70 if s < 2 else 62)
            if s in (1, 3):
                for off, (n, p) in _spans(spec):
                    h = _below(ch, p, 3)
                    if h is not None and 45 <= h <= 84:
                        c.put("vrc6 pulse b", b, off, n, h, 60 if s == 1 else 50)
                    if p - 12 >= 48 and off % 4 == 0:
                        c.put("pulse 2", b, off + 2, max(1, n - 2), p - 12, 50)
            elif s == 2:
                for off, (n, p) in _spans(spec):
                    if 45 <= (_below(ch, p, 3) or 0) <= 84 and off % 4 == 0:
                        c.put("vrc6 pulse b", b, off, n, _below(ch, p, 3), 52)
            # drums: one figure per four bar half, a different one per eight bar block,
            # the eighth bar takes the fill, and the kit thins as the notes are erased
            q = (b % 8) // 4
            if b == 31:
                # the last bar comes back up so the loop point is not a fade, and a
                # sixteenth before the bar line keeps the level at the seam
                idx, hs, kvel = 4, 0.6, 72
            elif s < 2:
                idx, hs = 4, 0.6
                kvel = 72 if s == 0 else 68
            elif s == 2:
                idx, hs = 4, 0.45
                kvel = 62
            else:
                idx, hs = 5, 0.35
                kvel = 54
            if b % 8 == 7:
                c.drum_bar(b, kick="x.....x...x.....", snare="....x...x.x.xx..",
                           hats="5030503050305030", idx=idx, kvel=kvel, svel=kvel, hscale=hs)
            elif b % 8 == 3:
                c.drum_bar(b, kick="x...............", snare="........x.......",
                           hats="3000300030003000", idx=idx, kvel=kvel - 8, svel=kvel, hscale=hs * 0.75)
            elif q == 0:
                c.drum_bar(b, kick="x.......x.......", snare="....x.......x...",
                           hats="5030503050305030", idx=idx, kvel=kvel, svel=kvel, hscale=hs)
            else:
                c.drum_bar(b, kick="x...x.......x...", snare="....x.......x...",
                           hats="5040504050405040", idx=idx, kvel=kvel - 4, svel=kvel, hscale=hs * 0.9)
    return c


CUES = {"storm": storm, "storm2": storm_v2, "percy": percy, "percy2": percy_v2,
        "kill": kill, "kill2": kill_v2, "spare": spare, "spare2": spare_v2}
