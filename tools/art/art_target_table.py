#!/usr/bin/env python3
"""Print the art-target measurements as a compact table for quoting in the docs."""
import json
import os

ROOT = r"<repo>"
with open(os.path.join(ROOT, "output", "art_target", "make_art_target_report.json"), "r",
          encoding="utf-8") as handle:
    reports = json.load(handle)

for report in reports:
    print("%s %s" % (report["style"], report["name"]))
    print("   distinct colours      %d (ceiling 25)" % report["distinct_colours"])
    print("   colours               %s" % report["distinct_colour_indices"])
    print("   sprite objects        %d" % report["sprite_objects"])
    print("   max sprites/scanline  %d (limit 8)" % report["max_sprites_per_scanline"])
    print("   outline pixels drawn  %d" % (report["figures"]["zeus"]["outline_pixels"]
                                           + report["figures"]["kronos"]["outline_pixels"]))
    print("   outline leaks         %d" % report["outline_leaks"])
    print("   dither patches        %d" % report["dither_patches"])
    print("   light up-left/down-right %d / %d" % (report["light_up_left"], report["light_down_right"]))
    print("   off palette           %s" % (report["off_palette"] or "none"))
    print("   zeus   at %s size %s oam %s" % (report["figures"]["zeus"]["at"],
                                             report["figures"]["zeus"]["size"],
                                             report["figures"]["zeus"]["oam_entries"]))
    print("   kronos at %s size %s oam %s" % (report["figures"]["kronos"]["at"],
                                             report["figures"]["kronos"]["size"],
                                             report["figures"]["kronos"]["oam_entries"]))
    print("   failures              %d" % len(report["failures"]))
    print()
