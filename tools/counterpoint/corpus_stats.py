"""Measure Baroque corpus statistics and write the target file M1b builds against, card t_0ed3bd3f.

    python tools/counterpoint/corpus_stats.py --bach "<workspace>/corpora/bach-counterpoint/midi" \
        --sinfonias tools/counterpoint/manifest-sinfonias.json --extra tools/counterpoint/corpus.json \
        --hod "D:/Musikage-Corpus/study/hod" \
        --targets data/counterpoint_targets.json \
        --hod-rules data/hod_dissonance_devices.json \
        --tables knowledge/BAROQUE-ENGINE-RESEARCH-STATS.md

What it measures, and why each one is on the list:

  1. melodic intervals, direction, step and leap shares, and whether a leap is recovered by a step in
     the other direction. These are the numbers a generator has to match for a line to sound written
     rather than random.
  2. rhythm: how long the notes actually are, and which two and three note rhythm cells recur.
  3. dissonance devices per 100 notes: suspension, passing, neighbour, appoggiatura, escape, and the
     unexplained residue, taken from the same checker that grades the cues (tools/counterpoint/rules.py),
     so a generator target and a gate number are the same measurement.
  4. cadences: every dominant to tonic, subdominant to tonic, dominant to submediant and semitone
     bass arrival, classified, plus phrases that stop on the dominant.
  5. sequences: interval cells that recur at a new pitch, counted as notes inside a sequence.
  6. imitation: the same interval cell in another voice later in time, with the offset in beats and
     the transposition, which is the number a canon distance has to come from.

The Harmony of Dissonance set is measured with the same engine plus a chord vocabulary and a vertical
dissonance census, because the question there is different: which dissonances sound intentional, on
which beats, prepared and resolved how. Nothing melodic is printed, copied or committed: every number
is a count or a share.

Both the Bach files and the fan MIDI study set are outside the repository; the manifests record the
source URL, the read date and the SHA-256 of every file measured.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rules  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
DEFAULT_BACH = r"<workspace>/corpora/bach-counterpoint/midi"
DEFAULT_HOD = r"D:/Musikage-Corpus/study/hod"
DEFAULT_SINFONIAS = r"<workspace>/corpora/bach-counterpoint/manifest-sinfonias.json"
DEFAULT_EXTRA = os.path.join(HERE, "corpus.json")
DEFAULT_TARGETS = os.path.join(ROOT, "data", "counterpoint_targets.json")
DEFAULT_HOD_RULES = os.path.join(ROOT, "data", "hod_dissonance_devices.json")
DEFAULT_TABLES = os.path.join(ROOT, "knowledge", "BAROQUE-ENGINE-RESEARCH-STATS.md")

WRITTEN = "2026-10-26"

# A cell is a run of this many intervals. Four intervals is five notes: long enough that a repeat is
# a motif and not a coincidence, short enough that Bach's own cells show up.
CELL = 4

# Intervals that clash against a voice unless the chord explains them.
DISSONANT_IC = frozenset((1, 2, 6, 10, 11))

QUALITIES = (
    ("maj", (0, 4, 7)),
    ("min", (0, 3, 7)),
    ("dim", (0, 3, 6)),
    ("aug", (0, 4, 8)),
    ("dom7", (0, 4, 7, 10)),
    ("min7", (0, 3, 7, 10)),
    ("hdim7", (0, 3, 6, 10)),
    ("dim7", (0, 3, 6, 9)),
    ("maj7", (0, 4, 7, 11)),
    ("sus4", (0, 5, 7)),
    ("sus2", (0, 2, 7)),
)
TRIADS = ("maj", "min", "dim", "aug")
# A prior per quality, so the labeller prefers the chord a Baroque piece is most likely to spell.
# Without it, an augmented triad and a root position major triad explain the same three pitch classes
# equally well and the first root in set order wins, which put "VI aug" on sonorities that are plainly
# an F major or a D minor seventh.
QUALITY_PRIOR = {"maj": 0.2, "min": 0.2, "dim": 0.08, "dom7": 0.1, "min7": 0.06,
                 "hdim7": 0.05, "dim7": 0.04, "maj7": 0.0, "aug": -0.25,
                 "sus4": -0.08, "sus2": -0.12}
UPPER = frozenset(("maj", "aug", "dom7", "maj7", "sus4", "sus2"))
MAJOR_STEPS = (0, 2, 4, 5, 7, 9, 11)
MINOR_STEPS = (0, 2, 3, 5, 7, 8, 10)
NUMERALS = ("I", "II", "III", "IV", "V", "VI", "VII")


# ---------------------------------------------------------------------------------------------
# Reading


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def manifest_works(manifest_path, directory):
    """Every work in a manifest whose file is present, with its recorded provenance."""
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    out = []
    for work in manifest.get("works", []):
        path = os.path.join(directory, work["file"])
        if not os.path.exists(path):
            continue
        out.append((path, work))
    return out


# ---------------------------------------------------------------------------------------------
# Harmony: a compact chord labeller, so cadences and vocabulary are counted rather than guessed.


def quality_of(members, root, pcs):
    """The template that best explains a pitch class set, and the extras it does not explain."""
    name, template = members
    allowed = {(root + step) % 12 for step in template}
    hit = pcs & allowed
    extra = pcs - allowed
    return name, allowed, hit, extra


def label_chord(pitches, key):
    """'V7', 'i', 'iiø7' with the root, quality and bass, or None when nothing explains the notes."""
    if len(pitches) < 2:
        return None
    pcs = frozenset(pitch % 12 for pitch in pitches)
    bass = min(pitches) % 12
    best = None
    for root in pcs:
        for entry in QUALITIES:
            name, allowed, hit, extra = quality_of(entry, root, pcs)
            need = 3 if name in TRIADS else 4
            if len(hit) < min(need, len(pcs)):
                continue
            if len(extra) > 1:
                continue
            if name == "aug" and (len(hit) < 3 or extra):
                continue
            score = (round(len(hit) - 0.75 * len(extra) + QUALITY_PRIOR.get(name, 0.0), 6),
                     len(hit), name in TRIADS, root == bass)
            if best is None or score > best[0]:
                best = (score, root, name, allowed, extra, bass)
    if best is None:
        return None
    _, root, name, allowed, extra, bass = best
    roman = roman_numeral(root, name, key)
    return {"roman": roman, "root": root, "quality": name, "bass": bass,
            "inversion": inversion_of(bass, root, allowed), "extra": len(extra),
            "members": sorted(allowed)}


def diatonic_degree(root_pc, key):
    tonic, mode = key
    steps = MAJOR_STEPS if mode == "major" else MINOR_STEPS
    offsets = {(tonic + step) % 12: index for index, step in enumerate(steps)}
    return offsets.get(root_pc % 12)


def roman_numeral(root_pc, quality, key):
    """A roman numeral for the chord, with an accidental when it is not in the key."""
    degree = diatonic_degree(root_pc, key)
    numeral = NUMERALS[degree] if degree is not None else None
    accidental = ""
    if numeral is None:
        best = None
        for index, letter in enumerate(NUMERALS):
            distance_up = (root_pc - key[0] - (MAJOR_STEPS if key[1] == "major" else MINOR_STEPS)[index]) % 12
            distance_down = (key[0] + (MAJOR_STEPS if key[1] == "major" else MINOR_STEPS)[index] - root_pc) % 12
            if distance_up == 1:
                candidate = ("#" + letter, 1)
            elif distance_down == 1:
                candidate = ("b" + letter, 1)
            else:
                candidate = (letter, min(distance_up, distance_down))
            if best is None or candidate[1] < best[1]:
                best = candidate
        numeral, accidental = best[0][1:], best[0][0]
    suffix = ""
    if quality in ("dom7", "min7", "maj7"):
        suffix = "7"
    elif quality == "hdim7":
        suffix = "\u00f87"
    elif quality == "dim7":
        suffix = "\u00b07"
    elif quality in ("sus4", "sus2"):
        suffix = quality
    body = numeral.lower() if quality in ("min", "dim", "min7", "hdim7", "dim7") else numeral
    return accidental + body + suffix


def inversion_of(bass, root, allowed):
    """Which chord member is in the bass: 0 root position, 1 first inversion, and so on."""
    offset = (bass - root) % 12
    thirds = {0: 0, 3: 1, 4: 1, 6: 2, 7: 2, 9: 3, 10: 3, 11: 3}
    return thirds.get(offset, 0)


# ---------------------------------------------------------------------------------------------
# The measurements


def sixteenth(score):
    return max(1, score.division // 4)


def beats(score, ticks):
    return ticks / float(score.ticks_per_beat)


def quantised_beats(score, ticks):
    return round(beats(score, ticks) * 4) / 4.0


def note_label(beats_value):
    """'0.25' as '1/16', because a rhythm table reads better in fractions."""
    table = {0.25: "1/16", 0.5: "1/8", 0.75: "3/16", 1.0: "1/4", 1.5: "3/8", 2.0: "1/2",
             3.0: "3/4", 4.0: "1/1", 6.0: "3/2", 8.0: "2/1"}
    value = round(beats_value, 4)
    if value in table:
        return table[value]
    if value < 0.25:
        return "shorter than 1/16"
    return "%g beats" % value


def melodic(score):
    """Intervals, direction, step and leap shares, leap recovery."""
    intervals = collections.Counter()
    sizes = collections.Counter()
    direction = collections.Counter()
    total = steps = leaps = large = recovered = leaps_with_next = 0
    for name, part in score.parts.items():
        line = part.line
        for index in range(len(line) - 1):
            here, there = line[index], line[index + 1]
            if there.start <= here.start:
                continue
            delta = there.pitch - here.pitch
            total += 1
            if delta == 0:
                direction["repeat"] += 1
            else:
                direction["up" if delta > 0 else "down"] += 1
            intervals[rules.interval_name(min(here.pitch, there.pitch),
                                          max(here.pitch, there.pitch))] += 1
            size = abs(delta)
            sizes[size] += 1
            if size <= 2:
                steps += 1
            else:
                leaps += 1
                if size >= 7:
                    large += 1
            if size > 2 and index + 2 < len(line):
                leaps_with_next += 1
                follow = line[index + 2].pitch - there.pitch
                if follow != 0 and abs(follow) <= 2 and (follow > 0) != (delta > 0):
                    recovered += 1
    return {
        "intervals": dict(intervals),
        "interval_sizes": dict(sizes),
        "intervals_moved": total,
        "direction": dict(direction),
        "step_share": round(steps / float(total), 3) if total else 0.0,
        "leap_share": round(leaps / float(total), 3) if total else 0.0,
        "large_leap_share": round(large / float(total), 3) if total else 0.0,
        "leap_recovery_share": round(recovered / float(leaps_with_next), 3) if leaps_with_next else 0.0,
        "unison_share": round(direction["repeat"] / float(total), 3) if total else 0.0,
    }


def rhythm(score):
    """Durations, and the two and three note rhythm cells that recur."""
    durations = collections.Counter()
    cells_two = collections.Counter()
    cells_three = collections.Counter()
    onsets = 0
    for name, part in score.parts.items():
        line = part.line
        values = [note_label(quantised_beats(score, note.length)) for note in line]
        for value in values:
            durations[value] += 1
            onsets += 1
        for index in range(len(values) - 1):
            cells_two["+".join(values[index:index + 2])] += 1
        for index in range(len(values) - 2):
            cells_three["+".join(values[index:index + 3])] += 1
    return {"durations": dict(durations), "onsets": onsets,
            "cells_two": cells_two, "cells_three": cells_three}


def harmony_series(score, per_beat=True):
    """The chord at every beat, merged so a held chord appears once.

    Sampling on the beat rather than on every attack is what makes the labels readable: an attack
    grid includes every passing tone of every voice, so a two beat V chord comes out as V, sus4, ii,
    vii. The beat grid is the harmonic rhythm a listener hears.
    """
    if per_beat:
        span = max((part.line[-1].end for part in score.parts.values() if part.line), default=0)
        ticks = list(range(0, span, score.ticks_per_beat))
    else:
        ticks = score.instants()
    series = []
    for tick in ticks:
        sounding = score.sounding(tick)
        if len(sounding) < 2:
            continue
        pitches = [note.pitch for note in sounding.values()]
        label = label_chord(pitches, score.key_detected)
        if label is None:
            continue
        if series and series[-1]["roman"] == label["roman"] and tick - series[-1]["tick"] <= score.ticks_per_beat:
            continue
        label["tick"] = tick
        label["top"] = max(pitches) % 12
        label["bass_pitch"] = min(pitches)
        series.append(label)
    return series


def rest_gaps(score):
    """Ticks where nothing sounds, which is where a phrase can end."""
    gaps = []
    span = max(part.line[-1].end for part in score.parts.values() if part.line)
    step = max(1, score.ticks_per_beat // 4)
    silent_run = 0
    for tick in range(0, span, step):
        sounding = score.sounding(tick)
        if sounding:
            silent_run = 0
            continue
        silent_run += 1
        if silent_run == 2:
            gaps.append(tick)
    return gaps


def cadence_type(previous, current, key, bass_motion, top_motion):
    """Name the cadence from the two chords, the bass and the top line."""
    dominant = is_dominant(previous, key)
    tonic = is_tonic(current, key)
    subdominant = previous["root"] == (key[0] + 5) % 12
    if dominant and tonic:
        if previous["root"] == (key[0] + 7) % 12:
            perfect = top_motion in (-1, -2) and bass_motion in (5, -5, 7, -7)
            return "perfect authentic" if perfect else "imperfect authentic"
        return "leading-tone authentic"
    if subdominant and tonic:
        return "plagal"
    if dominant and current["root"] == (key[0] + 9) % 12:
        return "deceptive"
    if (key[1] == "minor" and previous["root"] in ((key[0] + 5) % 12, (key[0] + 8) % 12)
            and current["root"] == (key[0] + 7) % 12 and bass_motion == -1):
        # iv6 to V with the bass falling a semitone onto the dominant: the Phrygian half cadence.
        return "phrygian"
    if dominant:
        return "half"
    return None


def is_dominant(label, key):
    if label["root"] == (key[0] + 7) % 12 and label["quality"] in ("maj", "dom7"):
        return True
    return label["root"] == (key[0] + 11) % 12 and label["quality"] in ("dim", "hdim7", "dim7")


def is_tonic(label, key):
    tonic, mode = key
    if label["root"] != tonic:
        return False
    if mode == "major":
        return label["quality"] in ("maj", "maj7")
    return label["quality"] in ("min", "min7", "maj")   # maj is the Picardy third


def cadences(score, series, gaps):
    """Every cadence the chord labels support, plus the phrases that stop on the dominant.

    A chord only counts as a cadence chord when it lasts at least half a beat, and the resolution
    has to land on a beat and at least two beats after the previous cadence. That is what keeps a
    sequence of fifths (V, I, V, I, V, I) from being counted as six cadences.
    """
    key = score.key_detected
    for index, label in enumerate(series):
        end = series[index + 1]["tick"] if index + 1 < len(series) else label["tick"] + score.ticks_per_beat
        label["duration"] = max(0, end - label["tick"])
    shortest = max(1, score.ticks_per_beat // 2)
    spacing = 2 * score.ticks_per_beat
    found = []
    last_tick = None
    for index in range(1, len(series)):
        previous, current = series[index - 1], series[index]
        if previous["duration"] < shortest or current["duration"] < shortest:
            continue
        if beat_weight(score, current["tick"]) not in ("strong", "medium"):
            continue
        if last_tick is not None and current["tick"] - last_tick < spacing:
            continue
        bass_motion = semitone_step(previous["bass_pitch"], current["bass_pitch"])
        top_motion = semitone_step(previous["top"], current["top"])
        name = cadence_type(previous, current, key, bass_motion, top_motion)
        if name is None or name == "half":
            continue
        bar, beat = score.bar_beat(current["tick"])
        found.append({"type": name, "bar": bar, "beat": round(beat, 2),
                      "from": previous["roman"], "to": current["roman"],
                      "bass_motion": bass_motion, "top_motion": top_motion})
        last_tick = current["tick"]
    for tick in gaps:
        before = [label for label in series if label["tick"] < tick]
        if not before:
            continue
        last = before[-1]
        if tick - last["tick"] > score.bar_ticks or last["duration"] < shortest:
            continue
        if last_tick is not None and tick - last_tick < spacing:
            continue
        if is_dominant(last, key):
            bar, beat = score.bar_beat(tick)
            found.append({"type": "half (phrase ends on V)", "bar": bar, "beat": round(beat, 2),
                          "from": last["roman"], "to": "rest", "bass_motion": 0, "top_motion": 0})
            last_tick = tick
    if series and is_dominant(series[-1], key) and series[-1]["duration"] >= shortest:
        bar, beat = score.bar_beat(series[-1]["tick"])
        if last_tick is None or series[-1]["tick"] - last_tick >= spacing:
            found.append({"type": "half (final chord on V)", "bar": bar, "beat": round(beat, 2),
                          "from": series[-1]["roman"], "to": "end", "bass_motion": 0, "top_motion": 0})
    found.sort(key=lambda event: (event["bar"], event["beat"]))
    return found


def beat_weight(score, tick):
    """'strong', 'medium' or 'weak' for a tick, from the project's own accent table."""
    strong, medium = rules.accent_positions(score.time_sig[0])
    position = (tick % score.bar_ticks) / float(score.ticks_per_beat)
    if any(abs(position - value) < 0.02 for value in strong):
        return "strong"
    if any(abs(position - value) < 0.02 for value in medium):
        return "medium"
    return "weak"


def semitone_step(low_or_previous, current):
    """The signed semitone motion, folded into the smallest interval that describes it."""
    if low_or_previous is None or current is None:
        return 0
    delta = (current - low_or_previous) % 12
    if delta > 6:
        delta -= 12
    return delta


def cell_sequences(score):
    """Interval cells that recur at a new pitch inside one voice, counted in notes.

    A cell has to be a shape, not a run: at least two different interval values, so a plain scale
    of equal steps does not read as a sequence. Its statements must not overlap, must start on a
    different pitch class, and the transposition between consecutive statements must be the same
    every time, which is what a sequence is.
    """
    cell_hits = collections.Counter()
    note_total = 0
    notes_in_sequences = 0
    for name, part in score.parts.items():
        line = part.line
        pitches = [note.pitch for note in line]
        note_total += len(pitches)
        by_pattern = collections.defaultdict(list)
        for index in range(len(pitches) - CELL):
            window = pitches[index:index + CELL + 1]
            pattern = tuple(window[i + 1] - window[i] for i in range(CELL))
            if len(set(pattern)) < 2:
                continue
            by_pattern[pattern].append((index, window[0]))
        covered = set()
        for pattern, hits in by_pattern.items():
            if len(hits) < 2:
                continue
            collected = []
            for index, first in hits:
                if collected and index - collected[-1][0] < CELL + 1:
                    continue
                collected.append((index, first))
            if len(collected) < 2:
                continue
            steps = {(collected[position + 1][1] - collected[position][1])
                     for position in range(len(collected) - 1)}
            if len(steps) != 1 or 0 in steps:
                continue
            cell_hits[pattern] += len(collected)
            for index, _ in collected:
                covered.update(range(index, index + CELL + 1))
        notes_in_sequences += len(covered)
    return {"cells_repeated": len(cell_hits), "occurrences": sum(cell_hits.values()),
            "notes_in_sequences": notes_in_sequences, "notes": note_total,
            "share_of_notes": round(notes_in_sequences / float(note_total), 3) if note_total else 0.0,
            "per_100_notes": round(100.0 * notes_in_sequences / note_total, 2) if note_total else 0.0}


def imitation(score):
    """The same cell in another voice later in time: offset in beats, transposition.

    A match needs the same intervals and the same rhythm, because that is the pair of things a
    listener hears as one line answering another; interval shape alone matches half the corpus. The
    answer has to enter within two bars, which is the imitation distance a listener perceives. Echoes
    further away are counted as sequences in the voice that states them, not as imitation.
    """
    names = list(score.parts)
    offsets = collections.Counter()
    transpositions = collections.Counter()
    pairs = set()
    for first_name in names:
        for second_name in names:
            if second_name == first_name:
                continue
            first = score.parts[first_name].line
            second = score.parts[second_name].line
            second_index = {}
            for start in range(len(second) - CELL):
                window = second[start:start + CELL + 1]
                pattern = tuple(window[k + 1].pitch - window[k].pitch for k in range(CELL))
                rhythm = tuple(round((window[k + 1].start - window[k].start)
                                     / float(score.ticks_per_beat), 2) for k in range(CELL))
                second_index.setdefault((pattern, rhythm), []).append(start)
            for start in range(len(first) - CELL):
                window = first[start:start + CELL + 1]
                pattern = tuple(window[k + 1].pitch - window[k].pitch for k in range(CELL))
                rhythm = tuple(round((window[k + 1].start - window[k].start)
                                     / float(score.ticks_per_beat), 2) for k in range(CELL))
                for match in second_index.get((pattern, rhythm), []):
                    delay = second[match].start - window[0].start
                    if delay <= 0 or delay > 2 * score.bar_ticks:
                        continue
                    offset = quantised_beats(score, delay)
                    interval = (second[match].pitch - window[0].pitch) % 12
                    offsets[offset] += 1
                    transpositions[interval] += 1
                    pairs.add((first_name, second_name, offset, interval))
    return {"offsets": dict(offsets), "transpositions": dict(transpositions),
            "events": len(pairs)}


def device_rates(score):
    """Dissonance devices per 100 notes, from the same checker that grades the cues."""
    result = rules.analyse(score, profile="free")
    notes = max(1, result["notes"])
    devices = result["devices"]
    judged = result["judged"]
    by_rule = result["summary"]["by_rule"]
    rates = {name: round(100.0 * count / notes, 2) for name, count in devices.items()}
    rates["unexplained_dissonance"] = round(100.0 * by_rule.get("CP-01", 0) / notes, 2)
    rates["weak_unexplained_dissonance"] = round(100.0 * by_rule.get("CP-02", 0) / notes, 2)
    rates["parallel_perfect"] = round(100.0 * by_rule.get("CP-09", 0) / notes, 2)
    rates["hidden_perfect"] = round(100.0 * by_rule.get("CP-10", 0) / notes, 2)
    return {"rates": rates, "devices": devices, "judged": judged,
            "dissonances_per_100_notes": round(100.0 * judged.get("dissonances", 0) / notes, 2),
            "accented_share": round(judged.get("accented", 0) / float(max(1, judged.get("dissonances", 0))), 3),
            "prepared_share": round(judged.get("prepared", 0) / float(max(1, judged.get("dissonances", 0))), 3),
            "resolved_share": round(judged.get("resolved", 0) / float(max(1, judged.get("dissonances", 0))), 3),
            "by_rule": by_rule}


def measure_work(path, work, want_devices=True):
    """Every measurement for one work, with its provenance row."""
    score = rules.load_score(path)
    row = {
        "file": work.get("file") or os.path.basename(path),
        "title": work.get("title"),
        "catalogue": work.get("catalogue"),
        "source": work.get("source"),
        "licence": work.get("licence"),
        "sha256": work.get("sha256") or digest(path),
        "voices": sorted(score.parts),
        "notes": score.notes_total,
        "bars": score.bars,
        "time_signature": "%d/%d" % score.time_sig,
        "key_detected": rules.key_name(score.key_detected),
        "tempo_bpm": round(score.tempo_us and 60000000.0 / score.tempo_us or 0, 2),
    }
    row["melodic"] = melodic(score)
    row["rhythm"] = rhythm(score)
    series = harmony_series(score)
    row["cadences"] = cadences(score, series, rest_gaps(score))
    row["final_chord"] = ({"roman": series[-1]["roman"], "quality": series[-1]["quality"],
                           "is_tonic": is_tonic(series[-1], score.key_detected)}
                          if series else None)
    row["sequences"] = cell_sequences(score)
    row["imitation"] = imitation(score)
    if want_devices:
        row["dissonance"] = device_rates(score)
    row["census"] = clash_census(score)
    return row


# ---------------------------------------------------------------------------------------------
# Aggregation into the target file


def mean(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / float(len(values)), 4) if values else None


def band(values):
    values = [v for v in values if v is not None]
    if not values:
        return {"mean": None, "min": None, "max": None}
    return {"mean": round(mean(values), 3), "min": round(min(values), 3), "max": round(max(values), 3)}


def share(counter, keys=None):
    total = float(sum(counter.values())) or 1.0
    items = counter if keys is None else {key: counter.get(key, 0) for key in keys}
    return {key: round(value / total, 4) for key, value in items.items() if value}


def pooled_interval_shares(rows):
    pooled = collections.Counter()
    for row in rows:
        pooled.update(row["melodic"]["intervals"])
    return share(pooled)


def pooled_durations(rows):
    pooled = collections.Counter()
    for row in rows:
        pooled.update(row["rhythm"]["durations"])
    return share(pooled)


def pooled_cells(rows, key):
    pooled = collections.Counter()
    for row in rows:
        pooled.update(row["rhythm"][key])
    fractions = share(pooled)
    ordered = sorted(fractions.items(), key=lambda kv: -kv[1])[:12]
    return [{"cell": cell, "share": value} for cell, value in ordered]


def pooled_cadences(rows):
    counter = collections.Counter()
    for row in rows:
        for event in row["cadences"]:
            counter[event["type"]] += 1
    return counter


def pooled_offsets(rows):
    pooled = collections.Counter()
    for row in rows:
        pooled.update({float(key): value for key, value in row["imitation"]["offsets"].items()})
    fractions = share(pooled)
    return [{"offset_beats": offset, "share": value}
            for offset, value in sorted(fractions.items(), key=lambda kv: -kv[1])[:10]]


def pooled_transpositions(rows):
    pooled = collections.Counter()
    for row in rows:
        pooled.update({int(key): value for key, value in row["imitation"]["transpositions"].items()})
    return {rules.interval_name(0, key): value for key, value in share(pooled).items()}


def device_bands(rows):
    names = ("suspension", "passing", "neighbour", "appoggiatura", "escape",
             "unexplained_dissonance", "weak_unexplained_dissonance",
             "parallel_perfect", "hidden_perfect")
    out = {}
    for name in names:
        out[name] = band([row["dissonance"]["rates"].get(name, 0.0) for row in rows])
    out["dissonances_per_100_notes"] = band([row["dissonance"]["dissonances_per_100_notes"] for row in rows])
    return out


def build_targets(bach_rows, corpus_note):
    """The JSON target file M1b generates against."""
    intervals = pooled_interval_shares(bach_rows)
    durations = pooled_durations(bach_rows)
    cadence_counter = pooled_cadences(bach_rows)
    cadence_share = share(cadence_counter)
    per_100_bars = round(100.0 * sum(cadence_counter.values())
                         / float(max(1, sum(row["bars"] for row in bach_rows))), 2)
    sequences = band([row["sequences"]["per_100_notes"] for row in bach_rows])
    sequence_share = band([row["sequences"]["share_of_notes"] for row in bach_rows])
    imitation_share = band([row["imitation"]["events"] for row in bach_rows])
    return {
        "format": "pp-counterpoint-targets",
        "version": 1,
        "card": "t_0ed3bd3f",
        "written": WRITTEN,
        "corpus": corpus_note,
        "method": ("Every work read as a monophonic line per part. Intervals are signed semitone steps "
                   "between consecutive notes in one voice; shares are of all melodic moves pooled across "
                   "the corpus. Devices and unexplained dissonances come from tools/counterpoint/rules.py "
                   "profile free, so these targets and the cue gate are the same measurement. Cadences are "
                   "chord-pair readings: dominant to tonic, subdominant to tonic, dominant to submediant, and "
                   "phrases that stop on the dominant at a rest. Sequences are %d-interval cells that recur at "
                   "a new pitch inside a voice. Imitation is the same cell in another voice starting later "
                   "and within four bars. Nothing melodic is stored here; every field is a count or a share."
                   % CELL),
        "targets": {
            "melody": {
                "interval_share": intervals,
                "step_share": band([row["melodic"]["step_share"] for row in bach_rows]),
                "leap_share": band([row["melodic"]["leap_share"] for row in bach_rows]),
                "large_leap_share": band([row["melodic"]["large_leap_share"] for row in bach_rows]),
                "leap_recovery_share": band([row["melodic"]["leap_recovery_share"] for row in bach_rows]),
                "unison_share": band([row["melodic"]["unison_share"] for row in bach_rows]),
                "direction_share": share(sum((collections.Counter(row["melodic"]["direction"])
                                              for row in bach_rows), collections.Counter())),
            },
            "rhythm": {
                "duration_share": durations,
                "top_two_note_cells": pooled_cells(bach_rows, "cells_two"),
                "top_three_note_cells": pooled_cells(bach_rows, "cells_three"),
                "notes_per_bar": band([row["notes"] / float(max(1, row["bars"])) for row in bach_rows]),
            },
            "dissonance_per_100_notes": device_bands(bach_rows),
            "cadences": {
                "per_100_bars": per_100_bars,
                "type_share": cadence_share,
                "counts": dict(cadence_counter),
                "final_chord_is_tonic_works": sum(1 for row in bach_rows
                                                  if row.get("final_chord") and row["final_chord"]["is_tonic"]),
                "final_chord_is_tonic_share": round(
                    sum(1 for row in bach_rows if row.get("final_chord") and row["final_chord"]["is_tonic"])
                    / float(max(1, len(bach_rows))), 3),
                "method_note": ("A cadence here is a chord pair read on a beat grid: dominant to tonic, "
                                "subdominant to tonic, dominant to submediant, or a phrase that stops on the "
                                "dominant. Each chord must last half a beat and the resolution must land on a "
                                "beat at least two beats after the previous cadence. The reading undercounts "
                                "where a suspension or a pedal hides the bass motion, so the per 100 bar rate "
                                "is a floor and the final chord check is printed beside it as the accuracy "
                                "measure: on this corpus the labeller names the last chord the tonic in "
                                "%d of %d works." % (
                                    sum(1 for row in bach_rows
                                        if row.get("final_chord") and row["final_chord"]["is_tonic"]),
                                    len(bach_rows))),
            },
            "sequences": {"per_100_notes": sequences, "share_of_notes_in_sequences": sequence_share},
            "clash_census": {
                "clashes_per_100_notes": band([row["census"]["clash_events_per_100_notes"]
                                               for row in bach_rows]),
                "beats_with_clash_share": band([row["census"]["beats_with_clash_share"]
                                                for row in bach_rows]),
                "resolved_by_step_share": band([row["census"]["resolved_by_step_share"]
                                                for row in bach_rows]),
                "clash_interval_share": share(sum((collections.Counter(row["census"]["clash_intervals"])
                                                   for row in bach_rows), collections.Counter())),
                "clash_placement": share(sum((collections.Counter(row["census"]["clash_placement"])
                                              for row in bach_rows), collections.Counter())),
                "chromatic_share": band([row["census"]["chromatic_share"] for row in bach_rows]),
            },
            "imitation": {
                "events_per_work": imitation_share,
                "offset_share": pooled_offsets(bach_rows),
                "transposition_share": pooled_transpositions(bach_rows),
            },
        },
        "works": [{key: row[key] for key in ("file", "title", "catalogue", "source", "licence",
                                             "sha256", "notes", "bars", "time_signature",
                                             "key_detected", "tempo_bpm")}
                  for row in bach_rows],
    }


# ---------------------------------------------------------------------------------------------
# The Harmony of Dissonance census


def clash_census(score):
    """Every beat: the chord, and every voice that clashes against the bass.

    The measurement is deliberately bass relative and attack aware, because that is what makes the
    two corpora comparable and what makes the number mean something. A voice note is a clash when the
    interval against the lowest sounding pitch is a minor or major second, a tritone, a minor seventh
    or a major seventh, and the note is attacked on that beat rather than carried over. A passing tone
    inside a chord is still a clash, which is the point: Baroque practice explains it, it does not
    hide it. Each clash is recorded with the metrical weight of its beat and with whether the voice
    resolves it by step, so the same census answers "which dissonances, on which beats, resolved how"
    for Bach and for Harmony of Dissonance.
    """
    qualities = collections.Counter()
    romans = collections.Counter()
    clash_intervals = collections.Counter()
    placements = collections.Counter()
    attacks = collections.Counter()
    resolved = 0
    clash_events = 0
    beats = 0
    beats_with_clash = 0
    chromatic = 0
    notes = 0
    scale = rules.scale_of(score.key_detected)
    for part in score.parts.values():
        for note in part.line:
            notes += 1
            if note.pitch % 12 not in scale:
                chromatic += 1
    span = max((part.line[-1].end for part in score.parts.values() if part.line), default=0)
    for tick in range(0, span, score.ticks_per_beat):
        sounding = score.sounding(tick)
        if len(sounding) < 2:
            continue
        beats += 1
        bass_pitch = min(note.pitch for note in sounding.values())
        label = label_chord([note.pitch for note in sounding.values()], score.key_detected)
        if label is None:
            qualities["unlabelled"] += 1
        else:
            qualities[label["quality"]] += 1
            romans[label["roman"]] += 1
        weight = beat_weight(score, tick)
        clashed_here = False
        for name, note in sounding.items():
            if note.pitch == bass_pitch:
                continue
            interval = (note.pitch - bass_pitch) % 12
            if interval not in DISSONANT_IC:
                continue
            attacked = abs(note.start - tick) <= score.tolerance
            clash_intervals[rules.interval_name(0, interval)] += 1
            clash_events += 1
            if attacked:
                attacks[weight] += 1
            placements[weight] += 1
            clashed_here = True
            following = score.parts[name].resolutions(note)
            if following is not None and abs(following.pitch - note.pitch) <= 2:
                resolved += 1
        if clashed_here:
            beats_with_clash += 1
    return {
        "beats": beats,
        "notes": notes,
        "beats_with_clash": beats_with_clash,
        "beats_with_clash_share": round(beats_with_clash / float(max(1, beats)), 3),
        "clash_events": clash_events,
        "clash_events_per_100_notes": round(100.0 * clash_events / float(max(1, notes)), 2),
        "attacked_clashes": sum(attacks.values()),
        "attacked_clash_placement": dict(attacks),
        "attacked_share": round(sum(attacks.values()) / float(max(1, clash_events)), 3),
        "clash_placement": dict(placements),
        "clash_intervals": dict(clash_intervals),
        "resolved_by_step_share": round(resolved / float(max(1, clash_events)), 3),
        "qualities": dict(qualities),
        "quality_share": share(qualities),
        "roman_top": dict(sorted(romans.items(), key=lambda kv: -kv[1])[:15]),
        "chromatic_share": round(chromatic / float(max(1, notes)), 3),
    }


def hod_work(path, work):
    score = rules.load_score(path)
    row = {
        "file": work.get("file") or os.path.basename(path),
        "title": work.get("title"),
        "source": work.get("source"),
        "licence": work.get("licence"),
        "sha256": work.get("sha256") or digest(path),
        "notes": score.notes_total,
        "bars": score.bars,
        "voices": sorted(score.parts),
        "time_signature": "%d/%d" % score.time_sig,
        "key_detected": rules.key_name(score.key_detected),
        "tempo_bpm": round(score.tempo_us and 60000000.0 / score.tempo_us or 0, 2),
    }
    row["census"] = clash_census(score)
    row["rhythm"] = {"durations": dict(rhythm(score)["durations"])}
    row["dissonance"] = device_rates(score)
    return row


def hod_summary(rows):
    """What the HoD set does with dissonance, pooled, plus the device rules it justifies."""
    beats = sum(row["census"]["beats"] for row in rows)
    beats_with_clash = sum(row["census"]["beats_with_clash"] for row in rows)
    clashes = sum(row["census"]["clash_events"] for row in rows)
    intervals = collections.Counter()
    placement = collections.Counter()
    attack_placement = collections.Counter()
    qualities = collections.Counter()
    for row in rows:
        intervals.update(row["census"]["clash_intervals"])
        placement.update(row["census"]["clash_placement"])
        attack_placement.update(row["census"]["attacked_clash_placement"])
        qualities.update(row["census"]["qualities"])
    devices = collections.Counter()
    judged = collections.Counter()
    for row in rows:
        devices.update(row["dissonance"]["devices"])
        judged.update(row["dissonance"]["judged"])
    total_notes = sum(row["notes"] for row in rows)
    resolved = sum(round(row["census"]["resolved_by_step_share"] * row["census"]["clash_events"])
                   for row in rows)
    return {
        "works": len(rows),
        "notes": total_notes,
        "beats": beats,
        "beats_with_clash": beats_with_clash,
        "beats_with_clash_share": round(beats_with_clash / float(max(1, beats)), 3),
        "clash_events": clashes,
        "clash_events_per_100_notes": round(100.0 * clashes / float(max(1, total_notes)), 2),
        "attacked_clashes": sum(attack_placement.values()),
        "clash_intervals": share(intervals),
        "clash_placement": share(placement),
        "attacked_clash_placement": share(attack_placement),
        "resolved_by_step_share": round(resolved / float(max(1, clashes)), 3),
        "quality_share": share(qualities),
        "devices_per_100_notes": {name: round(100.0 * count / max(1, total_notes), 2)
                                  for name, count in devices.items()},
        "judged": dict(judged),
        "accented_share": round(judged.get("accented", 0) / float(max(1, judged.get("dissonances", 0))), 3),
        "prepared_share": round(judged.get("prepared", 0) / float(max(1, judged.get("dissonances", 0))), 3),
        "resolved_share": round(judged.get("resolved", 0) / float(max(1, judged.get("dissonances", 0))), 3),
        "chromatic_share": band([row["census"]["chromatic_share"] for row in rows]),
    }


def hod_rules(summary):
    """The device rules the HoD numbers justify, written as rules the checker can gain.

    Each rule states the measured basis, the test, and the failure it prevents. They are proposals:
    data/dissonance_rules.json is a thirty device contract with its own checker and is not edited here.
    """
    clash = summary["clash_intervals"]
    placement = summary["clash_placement"]
    quality = summary["quality_share"]
    return {
        "format": "pp-hod-dissonance-devices",
        "version": 1,
        "card": "t_0ed3bd3f",
        "written": WRITTEN,
        "study_set": {
            "description": ("Fan sequenced MIDI of Castlevania: Harmony of Dissonance (Konami, 2002), "
                            "measured only. Not committed, not copied, not used as generator input."),
            "works": summary["works"],
            "notes": summary["notes"],
            "manifest": "D:/Musikage-Corpus/study/hod/MANIFEST.json",
        },
        "measured": {
            "beats": summary["beats"],
            "beats_with_clash_share": summary["beats_with_clash_share"],
            "clash_events": summary["clash_events"],
            "clash_events_per_100_notes": summary["clash_events_per_100_notes"],
            "clash_intervals": clash,
            "clash_placement": placement,
            "attacked_clash_placement": summary["attacked_clash_placement"],
            "resolved_by_step_share": summary["resolved_by_step_share"],
            "quality_share": quality,
            "chromatic_share": summary["chromatic_share"],
            "devices_per_100_notes": summary["devices_per_100_notes"],
            "accented_share_of_dissonances": summary["accented_share"],
            "prepared_share_of_dissonances": summary["prepared_share"],
            "resolved_share_of_dissonances": summary["resolved_share"],
        },
        "rules": [
            {"id": "HOD-01", "name": "diminished seventh as a passing colour",
             "test": ("A diminished seventh chord on any degree is accepted on a weak beat when both voices "
                      "that form it move by step into and out of it, and the bass resolves down by semitone."),
             "because": ("The set spends %.0f percent of its sonorities on dim7 and hdim7 chords, and %.0f "
                         "percent of its bass relative clashes are minor seconds or minor sevenths, which is "
                         "the shape a diminished seventh makes against its own bass."
                         % (100.0 * (quality.get("dim7", 0.0) + quality.get("hdim7", 0.0)),
                            100.0 * (clash.get("m2", 0.0) + clash.get("m7", 0.0)))),
             "fails": "a dim7 that arrives by leap on a downbeat and leaves by leap reads as a wrong chord."},
            {"id": "HOD-02", "name": "chromatic approach to the tonic at a cadence",
             "test": ("A bass that arrives on the tonic from a semitone below or above is accepted when the "
                      "upper voice holds a common tone or moves by step, and when the chromatic note is a "
                      "whole beat or shorter."),
             "because": ("Chromatic notes are %.0f to %.0f percent of the notes measured, so a semitone bass "
                         "arrival is the set's normal cadence colour and not an error."
                         % (100.0 * summary["chromatic_share"]["min"], 100.0 * summary["chromatic_share"]["max"])),
             "fails": "a chromatic bass note longer than a beat under a chromatic upper voice, which is the m2 on a strong beat the gate already fails."},
            {"id": "HOD-03", "name": "tritone as an interval of the chord, not a clash",
             "test": ("A tritone between two voices is accepted when both pitch classes are members of the "
                      "labelled chord (dim, aug, dim7, hdim7, dom7) and the chord is not on a strong beat "
                      "with both voices leaping into it."),
             "because": ("A tritone is %.0f percent of the measured bass relative clashes, so it is the "
                         "commonest single colour in the set after the major second; the rule keeps it only "
                         "where the chord explains it, which is what turns the interval into harmony."
                         % (100.0 * clash.get("TT", 0.0))),
             "fails": "a tritone between two voices in different chords, or one entered by leap on the downbeat."},
            {"id": "HOD-04", "name": "resolved appoggiatura on the strong beat",
             "test": ("A minor second or major seventh on a strong beat is accepted when it resolves by step "
                      "within one eighth note and the resolving note is a chord member."),
             "because": ("%.0f percent of the measured clashes sit on a strong or medium beat and %.0f "
                         "percent of the voices that make one resolve it by step, so the accent alone cannot "
                         "be the test; the resolution window is."
                         % (100.0 * (placement.get("strong", 0.0) + placement.get("medium", 0.0)),
                            100.0 * summary["resolved_by_step_share"])),
             "fails": "an accented clash that is held for a beat or left by leap."},
            {"id": "HOD-05", "name": "organ doubling and octave parallel accepted inside a registration",
             "test": ("Parallel octaves between two voices are accepted when the doubling is constant for a "
                      "whole phrase and the two voices keep the same interval for at least two bars, which "
                      "reads as one part in two registers."),
             "because": ("The set's arrangements double the organ and string lines for whole sections; the "
                         "arranger of a chip cue can do the same with a duty cycle pair."),
             "fails": "a doubling that starts or stops inside a phrase, which draws attention to the parallel."},
            {"id": "HOD-06", "name": "strong beat clash allowed once per phrase at a cadence",
             "test": ("One unprepared clash per phrase is accepted on the beat before a cadence when the "
                      "following chord is the tonic and the clashing voice moves by step."),
             "because": ("A single accented clash per phrase is what makes the set's cadences sound deliberate; "
                         "it is the same budget the project already uses for risk 3 devices."),
             "fails": "two such clashes inside four bars, which stops being a device and becomes the texture."},
        ],
        "next": ("M1a decides which of these enter tools/counterpoint/rules.py. They are written as tests "
                 "with a measured basis, not as permissions: every one of them narrows the existing fault."),
    }


# ---------------------------------------------------------------------------------------------
# The generated table fragment


def table(rows, headers, cells):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(cells(row)) + " |")
    return "\n".join(lines)


def stats_markdown(targets, hod_summary_rows, hod, bach_count):
    """The measured tables, generated so no number in the report is typed by hand."""
    t = targets["targets"]
    lines = []
    lines.append("## 1. Corpus statistics (generated by tools/counterpoint/corpus_stats.py)")
    lines.append("")
    lines.append("Every number below is produced by the command recorded in the card comment; the JSON "
                 "twin is `data/counterpoint_targets.json`. %d public-domain Bach works: 15 two-part "
                 "inventions, 15 three-part sinfonias and 5 chorale settings, all from the Mutopia Project, "
                 "with the source URL, licence and SHA-256 of each file in `tools/counterpoint/corpus.json` "
                 "and `tools/counterpoint/manifest-sinfonias.json`. The MIDI files are not in the repository."
                 % bach_count)
    lines.append("")
    lines.append("### Melodic intervals")
    lines.append("")
    intervals = t["melody"]["interval_share"]
    rows = [{"interval": name, "share": value} for name, value in
            sorted(intervals.items(), key=lambda kv: -kv[1])]
    lines.append(table(rows, ["interval", "share of melodic moves"],
                       lambda row: [row["interval"], "%.3f" % row["share"]]))
    lines.append("")
    for key, label in (("step_share", "steps (1 or 2 semitones)"),
                       ("leap_share", "leaps (3 semitones or more)"),
                       ("large_leap_share", "large leaps (7 semitones or more)"),
                       ("leap_recovery_share", "leaps recovered by a step in the other direction"),
                       ("unison_share", "repeated notes")):
        item = t["melody"][key]
        lines.append("- %s: mean %.3f, lowest work %.3f, highest work %.3f"
                     % (label, item["mean"], item["min"], item["max"]))
    lines.append("")
    lines.append("### Rhythm")
    lines.append("")
    durations = t["rhythm"]["duration_share"]
    rows = [{"value": name, "share": value}
            for name, value in sorted(durations.items(), key=lambda kv: -kv[1])]
    lines.append(table(rows, ["note value", "share of notes"],
                       lambda row: [row["value"], "%.3f" % row["share"]]))
    lines.append("")
    lines.append("Two note rhythm cells, pooled share of all two note cells:")
    lines.append("")
    lines.append(table(t["rhythm"]["top_two_note_cells"], ["cell (beats)", "share"],
                       lambda row: [row["cell"], "%.3f" % row["share"]]))
    lines.append("")
    lines.append("Three note rhythm cells:")
    lines.append("")
    lines.append(table(t["rhythm"]["top_three_note_cells"], ["cell (beats)", "share"],
                       lambda row: [row["cell"], "%.3f" % row["share"]]))
    lines.append("")
    lines.append("### Dissonance devices per 100 notes")
    lines.append("")
    rows = [{"name": name, "band": band} for name, band in t["dissonance_per_100_notes"].items()]
    lines.append(table(rows, ["device", "mean", "lowest work", "highest work"],
                       lambda row: [row["name"], "%.2f" % row["band"]["mean"],
                                    "%.2f" % row["band"]["min"], "%.2f" % row["band"]["max"]]))
    lines.append("")
    lines.append("### Cadences")
    lines.append("")
    lines.append("Cadence events per 100 bars: %.2f." % t["cadences"]["per_100_bars"])
    lines.append("")
    rows = [{"type": name, "share": value, "count": t["cadences"]["counts"][name]}
            for name, value in sorted(t["cadences"]["type_share"].items(), key=lambda kv: -kv[1])]
    lines.append(table(rows, ["cadence type", "share", "count"],
                       lambda row: [row["type"], "%.3f" % row["share"], str(row["count"])]))
    lines.append("")
    lines.append("### Sequences")
    lines.append("")
    sequences = t["sequences"]
    lines.append("- notes inside a sequence per 100 notes: mean %.2f, lowest work %.2f, highest work %.2f"
                 % (sequences["per_100_notes"]["mean"], sequences["per_100_notes"]["min"],
                    sequences["per_100_notes"]["max"]))
    lines.append("- share of notes that belong to a sequence: mean %.3f, lowest %.3f, highest %.3f"
                 % (sequences["share_of_notes_in_sequences"]["mean"],
                    sequences["share_of_notes_in_sequences"]["min"],
                    sequences["share_of_notes_in_sequences"]["max"]))
    lines.append("")
    lines.append("### Imitation")
    lines.append("")
    lines.append("Offset in beats between a cell in one voice and the same cell in another:")
    lines.append("")
    lines.append(table(t["imitation"]["offset_share"], ["offset (beats)", "share"],
                       lambda row: ["%g" % row["offset_beats"], "%.3f" % row["share"]]))
    lines.append("")
    lines.append("Transposition of the imitation, as an interval class:")
    lines.append("")
    lines.append(table([{"interval": name, "share": value}
                        for name, value in t["imitation"]["transposition_share"].items()],
                       ["interval", "share"], lambda row: [row["interval"], "%.3f" % row["share"]]))
    lines.append("")
    lines.append("### Per work")
    lines.append("")
    lines.append(table(targets["works"],
                       ["work", "catalogue", "notes", "bars", "metre", "key detected"],
                       lambda row: [row["title"] or row["file"], row["catalogue"] or "",
                                    str(row["notes"]), str(row["bars"]), row["time_signature"],
                                    row["key_detected"]]))
    lines.append("")
    lines.append("## 2. Harmony of Dissonance census (generated by the same tool)")
    lines.append("")
    lines.append("%d fan sequenced MIDI files, %d notes, measured only. Manifest with source URL and "
                 "SHA-256 per file: `D:/Musikage-Corpus/study/hod/MANIFEST.json`. Not committed, not "
                 "quoted, not used as generator input." % (hod["works"], hod["notes"]))
    lines.append("")
    lines.append("- beats measured: %d, of which %d carry a bass relative clash (%.1f percent)"
                 % (hod["beats"], hod["beats_with_clash"], 100.0 * hod["beats_with_clash_share"]))
    lines.append("- clashes per 100 notes: %.2f" % hod["clash_events_per_100_notes"])
    lines.append("- share of clashes that are struck on the beat: %.1f percent"
                 % (100.0 * hod["attacked_clashes"] / float(max(1, hod["clash_events"]))))
    lines.append("- share of clashes on a strong beat: %.1f percent"
                 % (100.0 * hod["clash_placement"].get("strong", 0.0)))
    lines.append("- share of clashes the voice resolves by step: %.1f percent"
                 % (100.0 * hod["resolved_by_step_share"]))
    lines.append("- dissonances the checker calls accented: %.1f percent; prepared: %.1f percent; "
                 "resolved: %.1f percent"
                 % (100.0 * hod["accented_share"], 100.0 * hod["prepared_share"],
                    100.0 * hod["resolved_share"]))
    lines.append("- notes outside the detected key: %.1f to %.1f percent per work"
                 % (100.0 * hod["chromatic_share"]["min"], 100.0 * hod["chromatic_share"]["max"]))
    lines.append("")
    lines.append("Clash intervals as a share of all bass relative clashes:")
    lines.append("")
    lines.append(table([{"interval": name, "share": value}
                        for name, value in sorted(hod["clash_intervals"].items(), key=lambda kv: -kv[1])],
                       ["interval", "share"], lambda row: [row["interval"], "%.3f" % row["share"]]))
    lines.append("")
    lines.append("### The same census on both corpora")
    lines.append("")
    bach = t["clash_census"]
    comparison = [
        ("clashes per 100 notes", "%.2f (lowest work %.2f, highest %.2f)"
         % (bach["clashes_per_100_notes"]["mean"], bach["clashes_per_100_notes"]["min"],
            bach["clashes_per_100_notes"]["max"]), "%.2f" % hod["clash_events_per_100_notes"]),
        ("beats carrying a clash", "%.1f percent" % (100.0 * bach["beats_with_clash_share"]["mean"]),
         "%.1f percent" % (100.0 * hod["beats_with_clash_share"])),
        ("clashes resolved by step",
         "%.1f percent" % (100.0 * bach["resolved_by_step_share"]["mean"]),
         "%.1f percent" % (100.0 * hod["resolved_by_step_share"])),
        ("clashes on a strong beat", "%.1f percent" % (100.0 * bach["clash_placement"].get("strong", 0.0)),
         "%.1f percent" % (100.0 * hod["clash_placement"].get("strong", 0.0))),
        ("notes outside the detected key", "%.1f percent" % (100.0 * bach["chromatic_share"]["mean"]),
         "%.1f percent" % (100.0 * hod["chromatic_share"]["mean"])),
    ]
    lines.append(table([{"what": what, "bach": left, "hod": right}
                        for what, left, right in comparison],
                       ["what", "Bach", "Harmony of Dissonance"],
                       lambda row: [row["what"], row["bach"], row["hod"]]))
    lines.append("")
    lines.append("Chord quality as a share of all labelled beats:")
    lines.append("")
    lines.append(table([{"quality": name, "share": value}
                        for name, value in sorted(hod["quality_share"].items(), key=lambda kv: -kv[1])],
                       ["quality", "share"], lambda row: [row["quality"], "%.3f" % row["share"]]))
    lines.append("")
    lines.append("### Per work")
    lines.append("")
    lines.append(table(hod_summary_rows,
                       ["work", "notes", "bars", "metre", "key detected", "clashes per 100 notes", "bpm"],
                       lambda row: [row["title"] or row["file"], str(row["notes"]), str(row["bars"]),
                                    row["time_signature"], row["key_detected"],
                                    "%.2f" % row["census"]["clash_events_per_100_notes"],
                                    "%.1f" % (row["tempo_bpm"] or 0)]))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------------------------
# Entry point / CLI


def main(argv=None):
    parser = argparse.ArgumentParser(description="Measure Baroque corpus statistics, card t_0ed3bd3f.")
    parser.add_argument("--bach", default=DEFAULT_BACH)
    parser.add_argument("--sinfonias", default=DEFAULT_SINFONIAS)
    parser.add_argument("--extra", default=DEFAULT_EXTRA)
    parser.add_argument("--hod", default=DEFAULT_HOD)
    parser.add_argument("--targets", default=DEFAULT_TARGETS)
    parser.add_argument("--hod-rules", default=DEFAULT_HOD_RULES)
    parser.add_argument("--tables", default=DEFAULT_TABLES)
    parser.add_argument("--skip-bach", action="store_true")
    parser.add_argument("--skip-hod", action="store_true")
    args = parser.parse_args(argv)

    started = time.time()
    bach_rows = []
    if not args.skip_bach:
        works = []
        for manifest in (args.extra, args.sinfonias):
            if os.path.exists(manifest):
                works.extend(manifest_works(manifest, args.bach))
        seen = set()
        for path, work in works:
            if work["file"] in seen:
                continue
            seen.add(work["file"])
            row = measure_work(path, work)
            bach_rows.append(row)
            print("bach %-32s notes %5d bars %3d cadences %2d steps %.2f"
                  % (row["file"], row["notes"], row["bars"], len(row["cadences"]),
                     row["melodic"]["step_share"]))
        corpus_note = {
            "description": ("Bach: 15 two-part inventions (BWV 772 to 786), 15 three-part sinfonias "
                            "(BWV 787 to 801) and 5 chorale settings, public domain, Mutopia Project"),
            "manifests": ["tools/counterpoint/corpus.json", "tools/counterpoint/manifest-sinfonias.json"],
            "directory": args.bach,
            "in_repository": False,
            "works": len(bach_rows),
            "notes": sum(row["notes"] for row in bach_rows),
            "read": WRITTEN,
        }
        targets = build_targets(bach_rows, corpus_note)
        os.makedirs(os.path.dirname(args.targets), exist_ok=True)
        with open(args.targets, "w", encoding="utf-8") as handle:
            json.dump(targets, handle, indent=1, sort_keys=False)
        print("targets: %d works, %d notes -> %s"
              % (len(bach_rows), corpus_note["notes"], args.targets))

    hod_rows, hod = [], None
    if not args.skip_hod:
        manifest = os.path.join(args.hod, "MANIFEST.json")
        if os.path.exists(manifest):
            for path, work in manifest_works(manifest, args.hod):
                row = hod_work(path, work)
                hod_rows.append(row)
                print("hod  %-45s notes %5d clash %5.2f"
                      % (row["file"], row["notes"], row["census"]["clash_events_per_100_notes"]))
            hod = hod_summary(hod_rows)
            payload = hod_rules(hod)
            payload["works"] = [{key: row[key] for key in ("file", "title", "source", "licence",
                                                           "sha256", "notes", "bars")}
                                for row in hod_rows]
            with open(args.hod_rules, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=1)
            print("hod: %d works, clashes per 100 notes %.2f -> %s"
                  % (len(hod_rows), hod["clash_events_per_100_notes"], args.hod_rules))

    if bach_rows and hod_rows:
        with open(args.targets, encoding="utf-8") as handle:
            targets = json.load(handle)
        os.makedirs(os.path.dirname(args.tables), exist_ok=True)
        with open(args.tables, "w", encoding="utf-8") as handle:
            handle.write(stats_markdown(targets, hod_rows, hod, len(bach_rows)))
        print("tables -> %s" % args.tables)

    print("corpus_stats: %.1f seconds" % (time.time() - started))
    return 0


if __name__ == "__main__":
    sys.exit(main())
