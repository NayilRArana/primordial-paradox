"""Fresh score table plus today's ear call count per model (card t_7417cbca)."""
import csv, os, re, datetime
from collections import defaultdict

ROOT = r"<repo>"
LEDGER = os.path.join(ROOT, "data", "ear_ledger.csv")

def vnum(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    m = re.search(r"_v(\d+)(b)$", stem)
    if m:
        return int(m.group(1)), m.group(2)
    m = re.search(r"_v(\d+)", stem)
    if m:
        return int(m.group(1)), ""
    return 0, ""

def family(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    stem = re.sub(r"_v\d+b$", "", stem)
    stem = re.sub(r"_v\d+", "", stem)
    stem = re.sub(r"(_humanized)+$", "", stem)
    return stem

rows = []
with open(LEDGER, newline="", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        rows.append(r)

today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
per_model_today = defaultdict(int)
for r in rows:
    if r.get("at", "").startswith(today):
        per_model_today[r.get("model", "?")] += 1

latest = {}
for r in rows:
    if r.get("role") != "summary":
        continue
    p = r["file"]
    if p not in latest or r["at"] > latest[p]["at"]:
        latest[p] = r

def total(r):
    try:
        return sum(int(r[k]) for k in ("hook","drums","tension","human","variety","structure"))
    except (ValueError, KeyError):
        return None

best = {}
for p, r in latest.items():
    t = total(r)
    if t is None or not os.path.exists(p):
        continue
    fam, v = family(p), vnum(p)
    if fam not in best or v > best[fam][0]:
        best[fam] = (v, t, r, p)

print("TODAY", today, "calls per model:", dict(per_model_today))
print()
print(f"{'cue':26s} {'ver':>6s} {'hook':>4s} {'drm':>3s} {'ten':>3s} {'hum':>3s} {'var':>3s} {'str':>3s} {'TOT':>4s}  model                  at")
print("-" * 124)
for fam in sorted(best, key=lambda k: best[k][1]):
    v, t, r, p = best[fam]
    print(f"{fam:26s} {'v%d%s' % v:>6s} {r['hook']:>4s} {r['drums']:>3s} {r['tension']:>3s} "
          f"{r['human']:>3s} {r['variety']:>3s} {r['structure']:>3s} {t:>4d}  {r['model']:22s} {r['at']}")
