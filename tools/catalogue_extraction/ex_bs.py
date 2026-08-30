# -*- coding: utf-8 -*-
"""Extract UB / UC / UBP (BS 4-1 designations, EN 10365 dims) from the catalogue."""
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from lib import table
from validate import validate_isection

DIM = [("m",94),("h",117),("b",141),("s",167),("t",191),("r",214),("d",236),("b_2t",262),("d_s",286)]
PROP= [("Iy",41),("Iz",68),("iy",92),("iz",110),("Wel_y",126),("Wel_z",148),
       ("Wpl_y",169),("Wpl_z",192),("U",211),("x",234),("H",252),("IT",270),("A",289)]
FAMS = {"UB": ([7,9,11],[8,10,12]), "UC": ([13],[14]), "UBP": ([15],[16])}

log, all_out = [], {}
for fam, (dpages, ppages) in FAMS.items():
    dims = [r for p in dpages for r in table(p, DIM, y_min=112, desig_max=90, min_cells=6)]
    props = [r for p in ppages for r in table(p, PROP, y_min=112, min_cells=8)]
    assert len(dims) == len(props), (fam, len(dims), len(props))
    recs = []
    for d, pr in zip(dims, props):
        r = {"Section": d["_desig"]}
        r.update({k: d[k] for k, _ in DIM})
        r.update({k: pr[k] for k, _ in PROP})
        recs.append(r)
    for r in recs:
        nom = float(r["Section"].split("x")[-1])
        validate_isection(r, log, f"{fam} {r['Section']}", nominal_mass=nom)
    all_out[fam] = recs
    print(f"{fam}: {len(recs)} sections ({recs[0]['Section']} ... {recs[-1]['Section']})")
json.dump(all_out, open("bs_raw.json", "w"), indent=1)
print()
print("\n".join(log))
print(f"\n{len(log)} issues")
