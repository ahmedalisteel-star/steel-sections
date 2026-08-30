# -*- coding: utf-8 -*-
"""EN 'European specification beams with parallel flanges' -> HE*/IPE* variants."""
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from lib import table
from validate import validate_isection

DIM = [("m",88),("h",114),("b",136),("tw",161),("tf",184),("r",210),("A",231),("hi",255),("d",283)]
PROP= [("Iy",45),("Iz",72),("iy",100),("iz",126),("Wel_y",153),("Wel_z",181),
       ("Wpl_y",207),("Wpl_z",232),("Iw",259),("IT",287)]
PAIRS = [(35,36),(37,38),(39,40),(41,42),(43,44),(45,46)]

def key(desig):
    toks = desig.split()
    if toks[0] == "HE":
        if "x" in toks:                      # HE 600 x 137
            return "HE" + "".join(toks[1:])
        size = next(t for t in toks[1:] if t.isdigit())
        var  = "".join(t for t in toks[1:] if t.isalpha())
        return "HE" + var + size
    if toks[0] == "IPE":
        if "x" in toks:                      # IPE 750 x 220
            return "IPE" + "".join(toks[1:])
        size = next(t for t in toks[1:] if t.isdigit())
        var  = "".join(t for t in toks[1:] if t.isalpha())
        return "IPE" + var + size
    raise ValueError(desig)

log, recs = [], []
for dp, pp in PAIRS:
    ds = table(dp, DIM, y_min=105, desig_max=80, min_cells=6, desig_join=" ")
    ps = table(pp, PROP, y_min=105, min_cells=6)
    assert len(ds) == len(ps)
    for d, p in zip(ds, ps):
        r = {"Section": key(d["_desig"]), "_printed": d["_desig"]}
        r.update({k: d[k] for k, _ in DIM})
        r.update({k: p[k] for k, _ in PROP})
        recs.append(r)

for r in recs:
    r["s"], r["t"] = r["tw"], r["tf"]
    r["H"] = r["Iw"]
    validate_isection(r, log, r["Section"], web="tw", flange="tf")
    r["Iw"] = r.pop("H")
    del r["s"], r["t"]

print(f"{len(recs)} rows; keys unique: {len(set(x['Section'] for x in recs))}")
json.dump(recs, open("en_extra_raw.json", "w"), indent=1)
print("\n".join(log)); print(len(log), "issues")
