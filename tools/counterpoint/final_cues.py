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


CUES = {"storm": storm, "percy": percy, "kill": kill, "spare": spare}
