# -*- coding: utf-8 -*-
"""Channels: PFC (pp.54-55), UPN (pp.56-58), RSC (pp.60-61)."""
import sys, io, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from lib import table
from validate import _chk, _consensus, RHO, FILLET

def area_channel(h, b, tw, tf, r):
    if None in (h, b, tw, tf, r):
        return None
    return (2 * b * tf + (h - 2 * tf) * tw + (FILLET / 2) * r * r) / 100.0

def validate_channel(r, log, tag, nominal_mass=None):
    g = r.get
    ag = area_channel(g("h"), g("b"), g("tw"), g("tf"), g("r1"))
    cands = [ag, (g("m") / RHO if g("m") else None)]
    for I, i in (("Iy", "iy"), ("Iz", "iz")):
        if g(I) and g(i):
            cands.append(g(I) / g(i) ** 2)
    exp_A = _consensus([c for c in cands if c], 0.03)
    if exp_A:
        _chk(r, "A", exp_A, 0.05, log, tag, derive=True, exact=0.05)
    A = g("A")
    if A:
        _chk(r, "m", A * RHO, 0.05, log, tag, derive=bool(exp_A), exact=0.05)
    if nominal_mass:
        _chk(r, "m", nominal_mass, 0.03, log, tag)
    for I, i, W, dim in (("Iy", "iy", "Wel_y", g("h")),
                         ("Iz", "iz", "Wel_z", (g("b") - g("cy") * 10) if g("cy") else None)):
        if g(I) and A:
            _chk(r, i, math.sqrt(g(I) / A), 0.03, log, tag, derive=True)
        if g(I) and dim and W == "Wel_y":
            _chk(r, W, g(I) / (dim / 20.0), 0.06, log, tag, derive=True)
        elif g(I) and dim:
            _chk(r, W, g(I) / (dim / 10.0), 0.06, log, tag, derive=True)
    if g("Wel_y"): _chk(r, "Wpl_y", g("Wel_y") * 1.17, 0.20, log, tag)
    if g("Wel_z"): _chk(r, "Wpl_z", g("Wel_z") * 1.80, 0.35, log, tag)

log = {}
# ---------------------------------------------------------------- PFC -------
P53 = [("Iz",44),("d_s",98),("b_t",126),("d",155),("r1",184),("cy",209),
       ("tf",236),("tw",265),("b",293),("h",320),("m",347)]
P54 = [("m2",44),("A",71),("IT",99),("H",123),("x",154),("U",180),("Wpl_z",210),
       ("Wpl_y",238),("Wel_z",264),("Wel_y",292),("iz",319),("iy",347)]
a = table(53, P53, y_min=125, rotated=True, desig_min=375, min_cells=8,
          desig_join="", desig_reverse=True)
b = table(54, P54, y_min=125, rotated=True, desig_min=375, min_cells=8,
          desig_join="", desig_reverse=True)
assert len(a) == len(b), (len(a), len(b))
pfc = []
for x, y in zip(a, b):
    r = {"Section": x["_desig"]}
    r.update({k: x[k] for k, _ in P53})
    r.update({k: y[k] for k, _ in P54 if k != "m2"})
    r["Iy"] = None
    pfc.append(r)
lg = []
for r in pfc:
    # Ix is missing from the printed page (over-printed) -- rebuild it from the
    # two published identities that pin it down: Iy = ry^2*A and Wel_y*(h/2).
    c1 = r["iy"] ** 2 * r["A"] if r["iy"] and r["A"] else None
    c2 = r["Wel_y"] * r["h"] / 20.0 if r["Wel_y"] and r["h"] else None
    c = (c1 + c2) / 2 if c1 and c2 and abs(c1 - c2) <= 0.02 * c1 else c1
    r["Iy"] = float(f"{c:.4g}") if c else None
    validate_channel(r, lg, "PFC " + str(r["Section"]))
log["PFC"] = lg
print(f"PFC: {len(pfc)} ({pfc[0]['Section']} ... {pfc[-1]['Section']})")

# ---------------------------------------------------------------- UPN -------
P55 = [("AG",44),("AL",67),("emax",98),("emin",122),("d",171),("A",196),("r2",221),
       ("r1",247),("tf",273),("tw",298),("b",325),("h",350),("m",372)]
P56 = [("ym",93),("cy",112),("Iw",134),("IT",155),("SS",176),("iz",194),("Wpl_z",213),
       ("Wel_z",234),("Iz",253),("Avz",274),("iy",295),("Wpl_y",314),("Wel_y",334),
       ("Iy",354),("m2",376)]
P57 = [("d",50),("A",88),("r2",126),("r1",159),("tf",191),("tw",225),("b",257),
       ("h",290),("m",320)]
a = table(55, P55, y_min=125, rotated=True, desig_min=395, min_cells=8,
          desig_join=" ", desig_reverse=True)
b = table(56, P56, y_min=125, rotated=True, desig_min=395, min_cells=8,
          desig_join=" ", desig_reverse=True)
assert len(a) == len(b), (len(a), len(b))
upn = []
for x, y in zip(a, b):
    r = {"Section": x["_desig"].replace(" ", "")}
    r.update({k: x[k] for k, _ in P55})
    r.update({k: y[k] for k, _ in P56 if k != "m2"})
    r["A"] = r["A"]            # cm^2 already
    upn.append(r)
small = table(57, P57, y_min=125, rotated=True, desig_min=380, min_cells=6,
              desig_join="", desig_reverse=True)
for x in small:
    r = {"Section": "UPN" + x["_desig"].replace("UPN", "")}
    r.update({k: x[k] for k, _ in P57})
    r["A"] = r["A"]            # printed as mm^2 x10^2 == cm^2
    upn.append(r)
lg = []
for r in upn:
    validate_channel(r, lg, r["Section"])
log["UPN"] = lg
print(f"UPN: {len(upn)} ({upn[0]['Section']} ... {upn[-1]['Section']})")

# ---------------------------------------------------------------- RSC -------
R59 = [("m",82),("h",103),("b",123),("tw",144),("tf",163),("r1",181),("r2",200),
       ("d",217),("b_t",236),("d_s",255),("Iy",273),("Iz",292)]
R60 = [("iy",43),("iz",67),("Wel_y",90),("Wel_z",113),("Wpl_y",136),("Wpl_z",159),
       ("U",181),("x",206),("H",232),("IT",262),("A",286)]
a = table(59, R59, y_min=115, desig_max=78, min_cells=8, desig_join="")
b = table(60, R60, y_min=115, min_cells=8)
assert len(a) == len(b), (len(a), len(b))
rsc = []
for x, y in zip(a, b):
    r = {"Section": x["_desig"]}
    r.update({k: x[k] for k, _ in R59})
    r.update({k: y[k] for k, _ in R60})
    rsc.append(r)
lg = []
for r in rsc:
    if r["d"] and r["d_s"] and r["tw"]:
        _chk(r, "d", r["d_s"] * r["tw"], 0.03, lg, "RSC " + str(r["Section"]), derive=True)
    validate_channel(r, lg, "RSC " + str(r["Section"]))
    if r["b"] and r["tf"]:
        _chk(r, "b_t", r["b"] / r["tf"], 0.03, lg, "RSC " + str(r["Section"]), derive=True)
    if r["d"] and r["tw"]:
        _chk(r, "d_s", r["d"] / r["tw"], 0.03, lg, "RSC " + str(r["Section"]), derive=True)
log["RSC"] = lg
print(f"RSC: {len(rsc)} ({rsc[0]['Section']} ... {rsc[-1]['Section']})")

json.dump({"PFC": pfc, "UPN": upn, "RSC": rsc}, open("chan_raw.json", "w"), indent=1)
for k, v in log.items():
    print(f"--- {k}: {len(v)} issues")
    print("\n".join(v))
