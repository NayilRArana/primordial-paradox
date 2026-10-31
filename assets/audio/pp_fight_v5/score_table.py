"""Build the current-version score table from data/ear_ledger.csv.

For each audio file take its LATEST summary row, then for each cue family keep
only the highest version suffix, and print a sorted table. Also prints every
summary row per file so a stale read can be spotted.
"""
import csv, re, sys, os
from collections import defaultdict

LEDGER = r"<repo>\data\ear_ledger.csv"

def vnum(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    m = re.search(r"_v(\d+)(b?)$", stem)
    if m:
        return int(m.group(1)), m.group(2)
    m = re.search(r"_v(\d+)", stem)
    if m:
        return int(m.group(1)), ""
    return 0, ""

def family(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    stem = re.sub(r"_v\d+b?$", "", stem)
    stem = re.sub(r"_v\d+", "", stem)
    stem = re.sub(r"(_humanized)+$", "", stem)
    return stem

rows = []
with open(LEDGER, newline="", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r.get("role") != "summary":
            continue
        rows.append(r)

latest = {}
for r in rows:
    p = r["file"]
    if p not in latest or r["at"] > latest[p]["at"]:
        latest[p] = r

def total(r):
    try:
        return sum(int(r[k]) for k in ("hook","drums","tension","human","variety","structure"))
    except (ValueError, KeyError):
        return None

by_file = []
for p, r in latest.items():
    t = total(r)
    if t is None:
        continue
    if not os.path.exists(p):
        continue
    by_file.append((family(p), vnum(p), t, r, p))

# per family keep the highest version (and highest letter)
best = {}
for fam, v, t, r, p in by_file:
    if fam not in best or (v > best[fam][1]):
        best[fam] = (fam, v, t, r, p)

print(f"{'cue':28s} {'ver':>6s} {'hook':>4s} {'drm':>3s} {'ten':>3s} {'hum':>3s} {'var':>3s} {'str':>3s} {'TOT':>4s}  model                 at")
print("-" * 128)
for fam in sorted(best, key=lambda k: best[k][2]):
    fam_, v, t, r, p = best[fam]
    print(f"{fam:28s} {'v%d%s' % v:>6s} {r['hook']:>4s} {r['drums']:>3s} {r['tension']:>3s} "
          f"{r['human']:>3s} {r['variety']:>3s} {r['structure']:>3s} {t:>4d}  {r['model']:24s} {r['at']}")

print()
print("FLOOR:", min(((best[f][2], f, best[f][4]) for f in best), key=lambda x: x[0]))
print()
print("all latest summary rows per file, offline-file skipped:")
for fam, v, t, r, p in sorted(by_file, key=lambda x: (x[0], x[1])):
    print(f"  {t:>3d}  v{v[0]}{v[1]:>2s}  {os.path.basename(p):45s} {r['model']:24s} {r['at']}")
