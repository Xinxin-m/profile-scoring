#!/usr/bin/env python3
"""Merge both judges' scores, compare rankings, and stress-test the rubric itself."""
import json, os, glob, statistics as st, math, sys

SP = os.path.dirname(os.path.abspath(__file__))
CRIT = ["code", "difficulty", "ingenuity", "product", "organization", "completeness"]
MAXC = {"code": 22, "difficulty": 20, "ingenuity": 18, "product": 18, "organization": 12, "completeness": 10}

man = {m["id"]: m for m in json.load(open(f"{SP}/manifest.json"))}


def load(d):
    out = {}
    bad = []
    for f in sorted(glob.glob(f"{SP}/{d}/*.json")):
        try:
            j = json.load(open(f))
        except Exception as e:
            bad.append((os.path.basename(f), f"parse: {e}")); continue
        rows = j.get("results") if isinstance(j, dict) else j
        if not rows:
            bad.append((os.path.basename(f), "empty")); continue
        for r in rows:
            if r.get("id") in out:
                continue
            s = r.get("scores", {})
            if not all(k in s for k in CRIT):
                bad.append((r.get("id"), "missing crit")); continue
            r["total"] = sum(int(s[k]) for k in CRIT)   # recompute, never trust
            out[r["id"]] = r
    return out, bad


def ranks(vals):
    """Average ranks, 1 = highest."""
    order = sorted(range(len(vals)), key=lambda i: -vals[i])
    rk = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            rk[order[k]] = avg
        i = j + 1
    return rk


def pearson(a, b):
    n = len(a)
    if n < 3:
        return float("nan")
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((x - mb) ** 2 for x in b)
    if va == 0 or vb == 0:
        return float("nan")
    return sum((a[i] - ma) * (b[i] - mb) for i in range(n)) / math.sqrt(va * vb)


def spearman(a, b):
    return pearson(ranks(a), ranks(b))


O, obad = load("opus_out")
C, cbad = load("codex_out")
both = sorted(set(O) & set(C))

print(f"opus scored {len(O)}   codex scored {len(C)}   overlap {len(both)}   of {len(man)} skills")
if obad: print("opus problems:", obad[:8])
if cbad: print("codex problems:", cbad[:8])
missing = sorted(set(man) - set(O) | set(man) - set(C))
if missing: print(f"unscored ({len(missing)}):", missing[:15])
print()

ot = [O[i]["total"] for i in both]
ct = [C[i]["total"] for i in both]

print("=== CALIBRATION ===")
for nm, v in (("opus", ot), ("codex-terra", ct)):
    print(f"{nm:12s} mean {st.mean(v):5.1f}  sd {st.pstdev(v):4.1f}  "
          f"min {min(v):3d}  p25 {sorted(v)[len(v)//4]:3d}  med {st.median(v):5.1f}  "
          f"p75 {sorted(v)[3*len(v)//4]:3d}  max {max(v):3d}  >85 {sum(1 for x in v if x>85)}")
print(f"mean gap (opus - codex): {st.mean([a-b for a,b in zip(ot,ct)]):+.1f}")
print(f"total: spearman {spearman(ot,ct):.3f}   pearson {pearson(ot,ct):.3f}   "
      f"mean |delta| {st.mean([abs(a-b) for a,b in zip(ot,ct)]):.1f}")
print()

print("=== PER-CRITERION AGREEMENT (does the criterion mean the same thing to both judges?) ===")
print(f"{'criterion':14s} {'max':>4} {'opus mu':>8} {'codex mu':>9} {'opus sd':>8} {'codex sd':>9} {'spearman':>9} {'used range':>12}")
for c in CRIT:
    a = [O[i]["scores"][c] for i in both]
    b = [C[i]["scores"][c] for i in both]
    both_v = a + b
    print(f"{c:14s} {MAXC[c]:>4} {st.mean(a):8.1f} {st.mean(b):9.1f} {st.pstdev(a):8.2f} "
          f"{st.pstdev(b):9.2f} {spearman(a,b):9.3f} {min(both_v):>5}-{max(both_v):<6}")
print()

print("=== CRITERION REDUNDANCY (opus scores; high r = the two criteria are one criterion) ===")
print(f"{'':14s}" + "".join(f"{c[:6]:>8}" for c in CRIT))
for c1 in CRIT:
    row = f"{c1:14s}"
    for c2 in CRIT:
        r = pearson([O[i]["scores"][c1] for i in both], [O[i]["scores"][c2] for i in both])
        row += f"{r:8.2f}"
    print(row)
print()

print("=== HOW MUCH DOES EACH CRITERION DRIVE THE RANKING? ===")
print("(spearman of total-without-this-criterion vs full total; low = the criterion is doing work)")
for c in CRIT:
    for nm, J in (("opus", O), ("codex", C)):
        full = [J[i]["total"] for i in both]
        drop = [J[i]["total"] - J[i]["scores"][c] for i in both]
        print(f"  {c:14s} {nm:6s} rho_without = {spearman(full,drop):.3f}")
print()

rk_o = dict(zip(both, ranks(ot)))
rk_c = dict(zip(both, ranks(ct)))

rows = []
for i in both:
    rows.append({
        "id": i, "name": man[i]["name"], "author": man[i]["author"], "set": man[i]["set"],
        "o": O[i]["total"], "c": C[i]["total"], "avg": (O[i]["total"] + C[i]["total"]) / 2,
        "ro": rk_o[i], "rc": rk_c[i], "dr": abs(rk_o[i] - rk_c[i]),
        "web_o": O[i].get("web_evidence"), "web_c": C[i].get("web_evidence"),
        "flags": sorted(set(O[i].get("flags", []) or []) | set(C[i].get("flags", []) or [])),
        "note_o": O[i].get("note", ""), "note_c": C[i].get("note", ""),
        "so": O[i]["scores"], "sc": C[i]["scores"],
    })
rows.sort(key=lambda r: -r["avg"])
for n, r in enumerate(rows, 1):
    r["rank"] = n
json.dump(rows, open(f"{SP}/merged.json", "w"), indent=1)

print("=== BIGGEST JUDGE DISAGREEMENTS (rubric ambiguity lives here) ===")
for r in sorted(rows, key=lambda r: -abs(r["o"] - r["c"]))[:12]:
    d = {c: r["so"][c] - r["sc"][c] for c in CRIT}
    worst = max(d, key=lambda k: abs(d[k]))
    print(f"  {r['name'][:36]:36s} opus {r['o']:3d}  codex {r['c']:3d}  d={r['o']-r['c']:+4d}"
          f"   widest: {worst} {d[worst]:+d}")
print()

print("=== WEB EVIDENCE AGREEMENT ===")
agree = sum(1 for r in rows if r["web_o"] == r["web_c"])
print(f"  {agree}/{len(rows)} agree ({agree/len(rows)*100:.0f}%)")
from collections import Counter
print("  opus :", dict(Counter(r["web_o"] for r in rows)))
print("  codex:", dict(Counter(r["web_c"] for r in rows)))
print()

print("=== AUTHOR AGGREGATE (0.5*best + 0.3*median + 0.2*worst, authors with 3+ skills) ===")
byauth = {}
for r in rows:
    byauth.setdefault(r["author"], []).append(r)
agg = []
for a, rs in byauth.items():
    if len(rs) < 3:
        continue
    for key, lbl in (("o", "opus"), ("c", "codex")):
        v = sorted((x[key] for x in rs), reverse=True)
        med = st.median(v)
        sc = 0.5 * v[0] + 0.3 * med + 0.2 * v[-1]
        agg.append((a, lbl, sc, len(rs), v[0], med, v[-1]))
byname = {}
for a, lbl, sc, n, hi, med, lo in agg:
    byname.setdefault(a, {})[lbl] = (sc, n, hi, med, lo)
print(f"{'author':30s} {'n':>3} {'opus agg':>9} {'codex agg':>10} {'opus hi/med/lo':>18} {'codex hi/med/lo':>18}")
for a, d in sorted(byname.items(), key=lambda kv: -(kv[1]["opus"][0] + kv[1]["codex"][0]) / 2):
    o, c = d["opus"], d["codex"]
    print(f"{a[:30]:30s} {o[1]:>3} {o[0]:9.1f} {c[0]:10.1f} "
          f"{f'{o[2]}/{o[3]:.0f}/{o[4]}':>18} {f'{c[2]}/{c[3]:.0f}/{c[4]}':>18}")
print()

print("=== FLAGS RAISED ===")
fl = Counter(f for r in rows for f in r["flags"])
for f, n in fl.most_common():
    print(f"  {n:3d}  {f}")
print()
print("wrote merged.json")
