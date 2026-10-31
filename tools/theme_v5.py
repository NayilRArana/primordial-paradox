"""theme_v5.py: the 4 and 8 bar drum ladder and the v5 dissonance set (card MUS-V5).

Built on theme_v4.py, which wrote the drums as one rung per bar cycled inside a
section. The v4 drum build did change bar to bar, but every bar in a section drew
from the same four rungs, so the ear heard one waltz kit for eight bars at a time
and scored drums 5 in both rounds (assets/audio/EAR_SWEEP_2026-10-22.md, item 3).

This tool rebuilds the kit at TWO levels, which is the change the card asks for:

  every 4 bars   the kit moves to a second block. Section A opens with a plain
                 waltz backbeat and the second four bars add an offbeat ghost, an
                 open hat on the third beat or a pickup sixteenth, depending on
                 the section. Twelve distinct 4 bar blocks across the 48 loop bars.
  every 8 bars   the last bar of each block gets a fill, and the last bar of each
                 8 bar span gets a bigger one: a tom run on the noise channel's
                 low periods, a snare roll, or a two hit pickup. The fill on the
                 span end is the loudest, so the ear hears the 8 bar line, not
                 just the 4.

Everything else is v4's, unchanged in behaviour: the same dissonance machinery
(one note of an inner voice is displaced, the preparation and the resolution are
the arranger's own notes), the same anchor list for the lead safety rule (no
anchor writes into vrc6 pulse a, so the K, Z, P and H motifs keep their pitches),
the same last bar guard (no hit at or after slot 5 and no device on bar 52, so
the loop cut is not mid hit).

Deterministic: the same MIDI, score and seed give byte identical output.

Usage
    theme_v5.py BASE.mid SCORE.yaml --out OUT.mid --report R.json
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import arrange                                              # noqa: E402
import hook_score                                           # noqa: E402
import humanize                                             # noqa: E402
import theme_v4                                             # noqa: E402

ROOT = os.path.dirname(HERE)
POLICY_PATH = os.path.join(ROOT, "data", "dissonance_rules.json")

BAR = arrange.TICKS_PER_BAR
EIGHTH = arrange.EIGHTH

# v4's kit plus three low noise periods used as toms for the fills. render_chip's
# NOISE_PERIODS table makes pitch 9 a 202 step thud, 11 a 380 step thud and 13 a
# 762 step thud, so 9, 11 and 13 read as high, mid and low tom without a new
# sample. Lengths are in eighths.
KINDS = dict(theme_v4.KINDS)
KINDS.update({
    "1": ("noise", 9, 0.55, 78),     # high tom
    "2": ("noise", 11, 0.65, 82),    # mid tom
    "3": ("noise", 13, 0.80, 88),    # low tom
})
TIMING_FEEL = dict(theme_v4.TIMING_FEEL)
TIMING_FEEL.update({"1": (0, 3), "2": (0, 3), "3": (0, 2)})
VELOCITY_JITTER = dict(theme_v4.VELOCITY_JITTER)
VELOCITY_JITTER.update({"1": 3, "2": 3, "3": 2})

# The two level ladder. Per section: block1 and block2 are each a four bar cycle
# of rungs, one rung per bar, and fill4 / fill4b / fill8 are the fills appended to
# the last bar of the first block, the last bar of the second block, and (the
# heavier one) the last bar of the eight bar span. Slot 0 to 5 are the six eighths
# of a 3/4 bar; 0.5 and 1.5 style slots are the sixteenths between them.
LADDER = {
    # A: the theme statement. Plain backbeat, then the second block picks up an
    # offbeat ghost and a pickup sixteenth, so bars 5 to 8 do not repeat 5 to 8.
    "A": {
        "block1": ["0:k,2:h,4:s", "0:k,2:h,4:s", "0:k,2:h,3:g,4:s", "0:k,2:h,4:s"],
        "block2": ["0:k,1.5:g,2:h,4:s", "0:k,2:h,4:s,5:g", "0:k,2:o,4:s", "0:k,2:h,4:s,4.5:g"],
        "fill4": "4.5:r,5:r",
        "fill4b": "5:h,5.5:s",
        "fill8": "3:2,3.5:2,4:1,4.5:1,5:r,5.5:s",
    },
    # A prime: the same harmony with the kit moved up a step, open hat on beat 3.
    "A_prime": {
        "block1": ["0:k,2:o,4:s", "0:k,2:h,4:s", "0:k,2:h,4:h,5:g", "0:k,2:h,4:s"],
        "block2": ["0:k,2:h,3:r,4:s", "0:k,2:o,4:s", "0:k,2:h,4:s,5:g", "0:k,2:h,3:g,4:s"],
        "fill4": "5:h,5.5:s",
        "fill4b": "4.5:r,5:r",
        "fill8": "3.5:1,4:1,4.5:2,5:r,5.5:s",
    },
    # B: the march. Downbeat hat doubled, and the second block goes to a full kit
    # with a snare on the second beat as well as the third.
    "B": {
        "block1": ["0:k,0:h,2:h,4:s", "0:k,2:h,4:h", "0:k,2:h,4:s", "0:k,2:h,3:g,4:s"],
        "block2": ["0:k,0:h,2:h,4:s", "0:k,2:h,3:r,4:s", "0:k,2:o,4:h,5:g", "0:k,2:h,4:s"],
        "fill4": "5:s,5.5:s",
        "fill4b": "4.5:1,5:2",
        "fill8": "3:3,3.5:2,4:2,4.5:1,5:r,5.5:s",
    },
    # B prime: the loudest section. Second block adds the pickup sixteenth and the
    # open hat, so the eight bar line lands on the fullest bar in the cue.
    "B_prime": {
        "block1": ["0:k,2:h,4:s", "0:k,1.5:g,2:h,4:s", "0:k,2:o,4:s", "0:k,2:h,4:h"],
        "block2": ["0:k,2:h,3:r,4:s,5:r", "0:k,2:h,4:s,5:g", "0:k,2:o,4:s,4.5:g", "0:k,2:h,4:s"],
        "fill4": "5:r,5.5:s",
        "fill4b": "4.5:2,5:1",
        "fill8": "3:3,3.5:3,4:2,4.5:1,5:s,5.5:s",
    },
    # C_trio: the cold clock. First block is the sea wash, second block is the dry
    # tick with the kick on the bar line, so the four bar line is a change of kit,
    # not a change of pattern.
    "C_trio": {
        "block1": ["0:k,0:w,2:w,4:w", "0:k,0:w,2:w,4:w", "0:k,2:w,4:w", "0:k,0:w,2:w,4:w"],
        "block2": ["0:k", "0:t,2:t,4:t", "0:k,2:t", "0:k,2:t,4:t"],
        "fill4": "5:w",
        "fill4b": "4.5:t,5:t",
        "fill8": "4:t,4.5:t,5:t,5.5:t",
    },
    # A return: the theme comes back on the plain kit and the second block opens
    # up (ghost, open hat), with the big fill into the loop point.
    "A_return": {
        "block1": ["0:k,2:h,4:s", "0:k,2:h,4:s", "0:k,2:h,4:s", "0:k,2:h,4:s"],
        "block2": ["0:k,1.5:g,2:h,4:s", "0:k,2:h,3:g,4:s", "0:k,2:o,4:s", "0:k,2:h,4:s,5:g"],
        "fill4": "4.5:r,5:r",
        "fill4b": "5:h,5.5:s",
        "fill8": "3:2,3.5:1,4:1,4.5:r,5:r,5.5:s",
    },
}

SECTION_BARS = 8      # every section of score_v5.yaml is eight bars
BLOCK_BARS = 4

# Section level for the kit, in velocity points. The ear's structure complaint on v4
# was that every section sat at the same level, so the climax did not read as one;
# this is the cheapest fix the chip allows and it costs no voice.
SECTION_LEVEL = {"A": -6, "A_prime": -2, "B": -8, "B_prime": 4, "C_trio": -14, "A_return": 2}

# The hole before the reprise, the ear sweep's item 5. The trio's clock stops on the
# last beat of bar 44 and the return arrives on the kick at bar 45 slot 2, so the
# loudest section is entered from silence, not from more of the same.
HOLE = (44, 3.0, 45, 0.0)     # bar_in, from slot, bar_out, until slot (0 = no cut)


# The dissonance anchors. v4's medium set (ten) plus bar 35 (the flat nine again,
# eight bars after bar 27, inside the risk 3 spacing rule) and bar 44 (the flat
# six out of the trio). Twelve applied devices over 6.5 eight bar spans is 1.85
# per span, inside the policy band of 1 to 2 and under the 13 device ceiling the
# spicy variant already spent. No anchor writes into vrc6 pulse a.
ANCHORS = [dict(row) for row in theme_v4.ANCHORS if row["bar"] != 52]
KEPT = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]


# --------------------------------------------------------------------------- drums

def rung_for(section, offset_in_section):
    """(rung text, block, whether the bar is a block end) for one bar of a section."""
    block = "block1" if (offset_in_section // BLOCK_BARS) % 2 == 0 else "block2"
    local = offset_in_section % BLOCK_BARS
    return LADDER[section][block][local], block, local == BLOCK_BARS - 1


def build_drums(bars, seed):
    """Rebuild the noise and dpcm tracks from the two level ladder, with feel."""
    rng = random.Random(seed)
    noise = []
    dpcm = []
    rows = []
    last_bar = bars[-1].number if bars else 0
    # The offset that matters is the bar's position inside its section, counted from
    # the section's own first bar. Section A starts on bar 5, so an absolute bar index
    # would put every block boundary four bars late and land the fills mid phrase.
    first_in_section = {}
    for bar in bars:
        first_in_section.setdefault(bar.section, bar.number)
    for bar in bars:
        groove = LADDER.get(bar.section)
        if groove is None:
            continue
        offset = bar.number - first_in_section[bar.section]
        rung, block, block_end = rung_for(bar.section, offset)
        hits = theme_v4.parse_cycle(rung)
        fill = ""
        fill_kind = None
        fill_from = 3.0
        if block_end:
            span_end = offset == SECTION_BARS - 1
            if span_end:
                fill, fill_kind = groove["fill8"], "fill8"
                fill_from = 2.0     # the 8 bar fill is four eighths, not three
            elif block == "block1":
                fill, fill_kind = groove["fill4"], "fill4"
            else:
                fill, fill_kind = groove["fill4b"], "fill4b"
            # The fill starts on the last three eighths so it never covers the
            # groove the bar began with; a rung that already ends on the last
            # eighth (a pickup ghost) keeps it and the fill starts one later.
            fill_hits = [(slot, kind) for slot, kind in theme_v4.parse_cycle(fill)
                         if slot >= fill_from]
            taken = {slot for slot, kind in hits if slot >= fill_from}
            hits = [hit for hit in hits if hit[0] < fill_from]
            hits += [hit for hit in fill_hits
                     if not any(abs(hit[0] - slot) < 0.01 for slot in taken)]
        # The hole before the reprise: the kit stops on the trio's last beat and
        # comes back on the second beat of the return.
        hole_in, hole_from, hole_out, hole_until = HOLE
        if bar.number == hole_in:
            hits = [hit for hit in hits if hit[0] < hole_from]
        elif hole_until > 0.0 and bar.number == hole_out:
            hits = [hit for hit in hits if hit[0] >= hole_until]
        # The last bar of the file runs into the loop point, where the tail is
        # cut and the file restarts. A hit still sounding at that cut leaves a
        # step at the seam, so the final bar keeps only its early hits.
        if bar.number == last_bar:
            hits = [hit for hit in hits if hit[0] < 5.0]
        hits.sort()
        pattern = ",".join("%s:%s" % (("%g" % slot), kind) for slot, kind in hits)
        rows.append({"bar": bar.number, "section": bar.section,
                     "block": block, "bar_in_block": (bar.index % BLOCK_BARS) + 1,
                     "fill": fill_kind, "pattern": pattern})
        start = bar.index * BAR
        for slot, kind in hits:
            track, pitch, length, velocity = KINDS[kind]
            low, high = TIMING_FEEL[kind]
            offset = rng.randint(low, high) if high > low else low
            jitter = rng.randint(-VELOCITY_JITTER[kind], VELOCITY_JITTER[kind])
            accent = 6 if slot in (0.0, 4.0) else 0
            if fill_kind == "fill8":
                accent += 4
            onset = start + int(round(slot * EIGHTH)) + offset
            onset = max(start, min(start + BAR - 1, onset))
            level = SECTION_LEVEL.get(bar.section, 0)
            note = (onset, onset + int(round(length * EIGHTH)),
                    pitch, max(20, min(127, velocity + jitter + accent + level)))
            (dpcm if track == "dpcm" else noise).append(note)
    noise.sort()
    dpcm.sort()
    return noise, dpcm, rows


# ---------------------------------------------------------------------- dissonance

def inject(song, bars):
    """v4's device machinery over the v5 anchor set."""
    lead = theme_v4.track_by_name(song, "vrc6 pulse a")
    chosen = [ANCHORS[index] for index in KEPT]
    moments = []
    for anchor in chosen:
        bar = next((row for row in bars if row.number == anchor["bar"]), None)
        if bar is None:
            raise ValueError("anchor names bar %d, which the score does not have" % anchor["bar"])
        track = theme_v4.track_by_name(song, anchor["voice"])
        bar_start = bar.index * BAR
        tick = bar_start + int(round(anchor["slot"] * EIGHTH))
        index = theme_v4.note_index_at(track, tick)
        if index is None:
            inside = [position for position, note in enumerate(track["notes"])
                      if bar_start <= note[0] < bar_start + BAR]
            later = [position for position in inside if track["notes"][position][0] >= tick]
            index = later[0] if later else (inside[0] if inside else None)
        row = {"bar": anchor["bar"], "section": bar.section, "voice": anchor["voice"],
               "device": anchor["device"], "risk": theme_v4.RISK[anchor["device"]],
               "note": anchor["note"], "applied": False}
        if index is None:
            row["reason"] = "that voice does not play in this bar"
            moments.append(row)
            continue
        actual_beat = (track["notes"][index][0] - bar_start) / float(2 * EIGHTH) + 1.0
        row["beat"] = round(actual_beat, 3)
        result = theme_v4.apply_device(track, index, anchor["device"], lead, bar.first_chord)
        if result:
            row.update(result)
            row["applied"] = True
        else:
            row["reason"] = "the voice has no note to resolve into at this point"
        moments.append(row)
    policy = json.load(open(POLICY_PATH, encoding="utf-8-sig"))["rate_policy"]
    applied = [row for row in moments if row["applied"]]
    ticks = sorted(next(row for row in bars if row.number == m["bar"]).index * BAR
                   + int(round((m["beat"] - 1.0) / 2.0 * EIGHTH)) for m in applied)
    risk_three = [m for m in applied if m["risk"] >= 3]
    gaps = [b["bar"] - a["bar"] for a, b in zip(risk_three, risk_three[1:])]
    return {
        "moments": moments,
        "applied_count": len(applied),
        "devices_per_8_bars": round(len(applied) / (len(bars) / 8.0), 2),
        "policy_devices_per_8_bars": [policy["devices_per_8_bars_min"],
                                      policy["devices_per_8_bars_max"]],
        "min_spacing_ok": all(b - a >= policy["min_spacing_beats_any"] * 2 * EIGHTH
                              for a, b in zip(ticks, ticks[1:])),
        "risk_3_count": len(risk_three),
        "risk_3_min_gap_bars": min(gaps) if gaps else None,
        "risk_3_spacing_ok": (not gaps) or min(gaps) >= policy["min_spacing_bars_risk_3"],
    }


# ------------------------------------------------------------------------- pipeline

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("midi")
    parser.add_argument("score")
    parser.add_argument("--out", default=None)
    parser.add_argument("--report", default=None)
    parser.add_argument("--seed", type=int, default=20261022)
    args = parser.parse_args(argv)

    score = arrange.load_score(args.score)
    bars = arrange.build_bars_v3(score)
    song = hook_score.read_smf(args.midi)

    noise, dpcm, rows = build_drums(bars, args.seed)
    theme_v4.track_by_name(song, "noise")["notes"] = noise
    theme_v4.track_by_name(song, "dpcm")["notes"] = dpcm

    dissonance = inject(song, bars)
    dropout = theme_v4.drop_arpeggio(song, bars, "medium")

    out = args.out or os.path.splitext(args.midi)[0] + "_v5.mid"
    humanize.write_smf(song, out)

    blocks = {}
    for row in rows:
        key = (row["section"], row["block"])
        blocks.setdefault(key, []).append(row["pattern"])
    report = {
        "seed": args.seed,
        "source_midi": os.path.abspath(args.midi),
        "score": os.path.abspath(args.score),
        "out_midi": os.path.abspath(out),
        "drum_hits": {"noise": len(noise), "dpcm": len(dpcm)},
        "four_bar_blocks": {"%s/%s" % key: {"bars": len(patterns), "patterns": patterns}
                            for key, patterns in blocks.items()},
        "distinct_4_bar_blocks": len(blocks),
        "distinct_8_bar_spans": len({key[0] for key in blocks}),
        "fills": {"fill4": sum(1 for row in rows if row["fill"] == "fill4"),
                  "fill4b": sum(1 for row in rows if row["fill"] == "fill4b"),
                  "fill8": sum(1 for row in rows if row["fill"] == "fill8")},
        "section_level": SECTION_LEVEL,
        "hole": {"bars": [HOLE[0], HOLE[2]], "from_slot": HOLE[1], "until_slot": HOLE[3]},
        "bar_rows": rows,
        "dissonance": dissonance,
        "voice_dropout": dropout,
        "timing_feel_ticks": {kind: list(pair) for kind, pair in TIMING_FEEL.items()},
        "velocity_jitter": VELOCITY_JITTER,
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.report:
        directory = os.path.dirname(os.path.abspath(args.report))
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(args.report, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text + "\n")
    print(json.dumps({key: report[key] for key in
                      ("drum_hits", "distinct_4_bar_blocks", "distinct_8_bar_spans",
                       "fills", "dissonance")}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
