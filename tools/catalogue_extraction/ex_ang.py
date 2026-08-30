# -*- coding: utf-8 -*-
"""EN 10056 equal (pp.68-71) and unequal (pp.74-77) angles."""
import sys, io, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from lib import table
from validate import _chk, _consensus, RHO

EQD = [("t",120),("m",163),("A",211),("cy",267)]
EQP = [("Iy",62),("iy",129),("Wel_y",195),("Wpl_y",262)]
UND = [("t",103),("m",134),("A",168),("cx",203),("cy",237),("Iy",275)]
UNP = [("Iz",54),("iy",96),("iz",133),("Wel_y",169),("Wel_z",205),
       ("Wpl_y",240),("Wpl_z",277)]

def collect(dp, pp, dcols, pcols, desig_max):
    d = table(dp, dcols, y_min=115, desig_max=desig_max, min_cells=1, desig_join="")
    p = table(pp, pcols, y_min=115, min_cells=1)
    assert len(d) == len(p), (dp, pp, len(d), len(p))
    out, size = [], None
    for x, y in zip(d, p):
        if x["_desig"]:
            size = x["_desig"]
        r = {"_size": size}
        r.update({k: x[k] for k, _ in dcols})
        r.update({k: y[k] for k, _ in pcols})
        out.append(r)
    return out

log = []
eq = collect(67, 68, EQD, EQP, 100) + collect(69, 70, EQD, EQP, 100)
for r in eq:
    a = float(r["_size"].split("x")[0])
    r["a"], r["b"] = a, a
    r["Section"] = "L%gx%gx%g" % (a, a, r["t"])
    r["cx"] = r["cy"]
un = collect(73, 74, UND, UNP, 100) + collect(75, 76, UND, UNP, 100)
for r in un:
    a, b = (float(v) for v in r["_size"].replace("x", " ").split())
    r["a"], r["b"] = a, b
    r["Section"] = "L%gx%gx%g" % (a, b, r["t"])

def validate_angle(r, log):
    g, tag = r.get, r["Section"]
    cands = [g("m") / RHO if g("m") else None]
    for I, i in (("Iy", "iy"), ("Iz", "iz")):
        if g(I) and g(i):
            cands.append(g(I) / g(i) ** 2)
    exp_A = _consensus([c for c in cands if c], 0.03)
    if exp_A:
        _chk(r, "A", exp_A, 0.05, log, tag, derive=True, exact=0.05)
    A = g("A")
    if A:
        _chk(r, "m", A * RHO, 0.05, log, tag, derive=bool(exp_A), exact=0.05)
        if g("Iy"): _chk(r, "iy", math.sqrt(g("Iy") / A), 0.03, log, tag, derive=True)
        if g("Iz"): _chk(r, "iz", math.sqrt(g("Iz") / A), 0.03, log, tag, derive=True)
    if g("Iy") and g("cx"): _chk(r, "Wel_y", g("Iy") / (g("a") / 10.0 - g("cx")), 0.05, log, tag, derive=True)
    if g("Iz") and g("cy"): _chk(r, "Wel_z", g("Iz") / (g("b") / 10.0 - g("cy")), 0.05, log, tag, derive=True)
    if g("Wel_y"): _chk(r, "Wpl_y", g("Wel_y") * 1.82, 0.25, log, tag)
    if g("Wel_z"): _chk(r, "Wpl_z", g("Wel_z") * 1.82, 0.25, log, tag)

for r in eq + un:
    validate_angle(r, log)
for r in eq:                      # equal legs: y-y mirrors x-x
    r["Iz"], r["iz"] = r["Iy"], r["iy"]
    r["Wel_z"], r["Wpl_z"] = r["Wel_y"], r["Wpl_y"]
print(f"equal: {len(eq)} ({eq[0]['Section']} ... {eq[-1]['Section']})")
print(f"unequal: {len(un)} ({un[0]['Section']} ... {un[-1]['Section']})")
json.dump({"EQ": eq, "UN": un}, open("ang_raw.json", "w"), indent=1)
print("\n".join(log)); print(len(log), "issues")
