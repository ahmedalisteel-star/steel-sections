# -*- coding: utf-8 -*-
"""Full internal-consistency sweep over every shipped catalogue row."""
import io
import json
import math
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from lib import find_data_dir

D = str(find_data_dir() / "dbmsc_catalogue.json")
cat = json.load(open(D, encoding="utf-8"))["sections"]
bad = 0
tot = 0
def chk(tag, name, got, exp, tol):
    global bad, tot
    if got is None or exp is None or exp == 0:
        return
    tot += 1
    if abs(got - exp) > tol * abs(exp):
        global_bad(tag, name, got, exp)
def global_bad(tag, name, got, exp):
    global bad
    bad += 1
    if bad <= 30:
        print(f"  {tag:28s} {name:7s} {got:<12g} expect ~{exp:.4g}")
for fam, rows in cat.items():
    if fam == "PIPE":
        for r in rows:
            d = r["D"] - 2 * r["t"]
            A = math.pi / 4 * (r["D"] ** 2 - d ** 2)
            chk(f"{fam} {r['Section']}", "m", r["m"], A * 0.785, 0.03)
        continue
    for r in rows:
        t = f"{fam} {r['Section']}"
        A, m = r.get("A"), r.get("m")
        if A and m: chk(t, "m", m, A * 0.785, 0.05)
        for I, i in (("Iy", "iy"), ("Iz", "iz")):
            if A and r.get(I) and r.get(i):
                chk(t, i, r[i], math.sqrt(r[I] / A), 0.04)
        h = r.get("h") or r.get("a")
        if r.get("Iy") and r.get("Wel_y") and h and fam not in ("L_EQUAL", "L_UNEQUAL"):
            chk(t, "Wel_y", r["Wel_y"], r["Iy"] / (h / 2.0), 0.07)
print(f"\n{tot} identity checks over {sum(len(v) for v in cat.values())} sections; {bad} outside tolerance")
