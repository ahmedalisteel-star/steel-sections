# -*- coding: utf-8 -*-
"""Rectangular (pp.94-109) and square (pp.112-120) hollow sections."""
import sys, io, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from lib import table
from validate import _chk, _consensus, RHO

R = [("As",42),("Ct",69),("IT",95),("Wpl_z",120),("Wpl_y",146),("Wel_z",171),
     ("Wel_y",196),("iz",224),("iy",250),("Iz",275),("Iy",301),("A",327),("m",352),("t",379)]
S = [("As",46),("Ct",85),("IT",121),("Wpl_y",157),("Wel_y",193),("iy",229),
     ("Iy",264),("A",300),("m",333),("t",367)]

def grab(pages, cols, desig_min, ymin=118):
    out, size = [], None
    for pg in pages:
        cur = None
        for r in table(pg, cols, y_min=ymin, rotated=True, desig_min=desig_min,
                       min_cells=6, desig_join="", desig_reverse=True):
            if r["_desig"]:
                cur = r["_desig"]
            if cur is None or r["t"] is None:
                continue
            rec = {"_size": cur}
            rec.update({k: r[k] for k, _ in cols})
            out.append(rec)
    return out

log = []
rhs = grab(range(93, 109), R, 390)
for r in rhs:
    h, b = (float(v) for v in r["_size"].split("x"))
    r["h"], r["b"] = h, b
    r["Section"] = "RHS%gx%gx%g" % (h, b, r["t"])
shs = grab(range(111, 120), S, 390)
for r in shs:
    h, b = (float(v) for v in r["_size"].split("x"))
    r["h"] = r["b"] = h
    r["Section"] = "SHS%gx%gx%g" % (h, b, r["t"])
    r["Iz"], r["iz"] = r["Iy"], r["iy"]
    r["Wel_z"], r["Wpl_z"] = r["Wel_y"], r["Wpl_y"]

def wall_from_area(h, b, A):
    """Wall thickness implied by the gross area, ignoring corner radii."""
    disc = (h + b) ** 2 - 4 * A * 100.0
    if disc < 0:
        return None
    return ((h + b) - math.sqrt(disc)) / 4.0

def validate_hollow(r, log):
    g, tag = r.get, r["Section"]
    cands = [g("m") / RHO if g("m") else None]
    if g("Iy") and g("iy"): cands.append(g("Iy") / g("iy") ** 2)
    if g("Iz") and g("iz") and r["h"] != r["b"]:
        cands.append(g("Iz") / g("iz") ** 2)
    exp = _consensus([c for c in cands if c], 0.03)
    if exp:
        _chk(r, "A", exp, 0.05, log, tag, derive=True, exact=0.05)
    A = g("A")
    if A:
        _chk(r, "m", A * RHO, 0.04, log, tag, derive=bool(exp), exact=0.04)
        if g("Iy"): _chk(r, "iy", math.sqrt(g("Iy") / A), 0.03, log, tag, derive=True)
        if g("Iz"): _chk(r, "iz", math.sqrt(g("Iz") / A), 0.03, log, tag, derive=True)
    if g("Iy"): _chk(r, "Wel_y", g("Iy") / (r["h"] / 20.0), 0.05, log, tag, derive=True)
    if g("Iz"): _chk(r, "Wel_z", g("Iz") / (r["b"] / 20.0), 0.05, log, tag, derive=True)
    if g("Wel_y"): _chk(r, "Wpl_y", g("Wel_y") * 1.20, 0.22, log, tag)
    if g("Wel_z"): _chk(r, "Wpl_z", g("Wel_z") * 1.20, 0.25, log, tag)
    # wall thickness is the one cell with no other column to check it, so
    # verify it against the area it would have to produce
    tc = wall_from_area(r["h"], r["b"], g("A")) if g("A") else None
    if tc and abs(r["t"] - tc) > 0.12 * tc:
        near = min(WALLS, key=lambda w: abs(w - tc))
        if abs(near - tc) <= 0.05 * tc:
            log.append(f"REPAIR {tag:22s} t      {r['t']:<11g} -> {near:<11g} "
                       f"(area implies {tc:.2f})")
            r["t"] = near
        else:
            log.append(f"FLAG   {tag:22s} t      {r['t']:<11g}    area implies {tc:.2f}")

WALLS = sorted({r["t"] for r in rhs + shs if r["t"]})
for r in rhs + shs:
    validate_hollow(r, log)
    fam = "RHS" if r["h"] != r["b"] else "SHS"
    r["Section"] = "%s%gx%gx%g" % (fam, r["h"], r["b"], r["t"])
print(f"RHS: {len(rhs)}  SHS: {len(shs)}")
json.dump({"RHS": rhs, "SHS": shs}, open("hollow_raw.json", "w"), indent=1)
print("\n".join(log)); print(len(log), "issues")
