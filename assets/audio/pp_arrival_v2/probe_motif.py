"""Print every 2 bar segment's similarity to the motif, by start bar.

Usage: python probe_motif.py FILE.mid [track name]
Reads tools/hook_score.py's own analysis, so the numbers match the meter.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "tools")))
import hook_score as H  # noqa: E402

path = sys.argv[1]
track = sys.argv[2] if len(sys.argv) > 2 else "vrc6 pulse a"
cfg, _src = H.load_grammar()
song = H.read_smf(path)
report = H.score_file(path, track=track, config=cfg)
melody = H.Melody(H.pick_melody_track(song, track)["notes"], song["division"],
                  song["time_sig"][0], H.GRID_DIVISIONS.get(cfg["grid"], 4), name=track)
motif = H.find_motif(melody, cfg)
print("score %s / 100  motif bars %d from bar %d, %d notes, %d returns, coverage %d%%"
      % (report["score"], motif["bars"], motif["start_bar"] + 1, motif["notes"],
         motif["returns"], round(motif["coverage"] * 100)))
base = melody.segment(motif["start_bar"], motif["bars"])
for start in range(0, melody.bars - motif["bars"] + 1):
    seg = melody.segment(start, motif["bars"])
    sim = H._similarity(base, seg)
    shape = H._contour(melody.pitches_of(start, motif["bars"]),
                       cfg["pedal_range_semitones"]) or "-"
    mark = "*" if sim >= cfg["motif_match_min"] else " "
    print("%s bar %2d  notes %2d  sim %.2f  %-5s %s"
          % (mark, start + 1, len(seg), sim, shape,
             " ".join(str(n.pitch) for n in melody.segment_notes(start, motif["bars"]))))
