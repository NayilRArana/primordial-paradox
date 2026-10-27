#!/usr/bin/env python3
"""Check that every tool file named in knowledge/ART-STYLE.md exists, and that the doc has no long dashes."""
import os
import re

ROOT = r"<repo>"
ART = os.path.join(ROOT, "tools", "art")
DOC = os.path.join(ROOT, "knowledge", "ART-STYLE.md")

present = set(os.listdir(ART))
with open(DOC, "r", encoding="utf-8") as handle:
    text = handle.read()

named = sorted(set(re.findall(r"`(tools/art/[A-Za-z0-9_]+\.py)`", text)))
missing = []
for item in named:
    leaf = item.rsplit("/", 1)[-1]
    if leaf not in present:
        missing.append(item)
print("tool files named in the doc:", len(named))
print("MISSING:", missing or "none")

data_claims = sorted(set(re.findall(r"`(data/[A-Za-z0-9_]+\.json)`", text)))
for claim in data_claims:
    print("data claim %s exists: %s" % (claim, os.path.exists(os.path.join(ROOT, claim))))

bad = []
for index, line in enumerate(text.splitlines(), start=1):
    for char in ("\u2014", "\u2013", "\u2015", "\u2212"):
        if char in line:
            bad.append((index, char))
print("long dashes:", bad or "none")

# scene ids and map ids the doc asserts
for scene in ("s1_move_in", "s2_high_street"):
    path = os.path.join(ROOT, "data", "authoring", "scenes", scene + ".json")
    print("scene %s exists: %s" % (scene, os.path.exists(path)))

maps = os.path.join(ROOT, "data", "maps", "all.json")
with open(maps, "r", encoding="utf-8") as handle:
    map_text = handle.read()
for map_id in ("wessex_lane_montefiore", "southampton_high_street", "southampton_town_quay",
               "quay_gate_checkpoint", "quay_yard_walk", "navy_sailor"):
    print("map id %-26s in data/maps/all.json: %s" % (map_id, ('"%s"' % map_id) in map_text))
