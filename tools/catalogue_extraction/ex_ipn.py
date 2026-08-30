# -*- coding: utf-8 -*-
"""IPN taper-flange I sections (DIN 1025-1 / EN 10365), catalogue pages 48-49."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from lib import table
from validate import validate_isection

DIM = [("m",78),("h",99),("b",118),("tw",137),("tf",156),("r1",175),("r2",195),
       ("A",211),("d",230)]
PROP= [("AL",39),("AG",58),("Iy",78),("Wel_y",96),("Wpl_y",116),("iy",136),("Avz",154),
       ("Iz",174),("Wel_z",194),("Wpl_z",213),("iz",231),("SS",250),("IT",269),("Iw",288)]

d = table(47, DIM, y_min=140, desig_max=72, min_cells=6, desig_join="")
p = table(48, PROP, y_min=140, min_cells=8)
print(len(d), len(p), d[0]["_desig"], d[-1]["_desig"])
log, recs = [], []
for a, b in zip(d, p):
    r = {"Section": a["_desig"]}
    r.update({k: a[k] for k, _ in DIM})
    r.update({k: b[k] for k, _ in PROP})
    if r["d"] and r["h"] and r["d"] > r["h"]:
        log.append(f"REPAIR {r['Section']:24s} {'d':6s} {r['d']:<11g} -> {r['d']/10:<11g} (d > h)")
        r["d"] = r["d"] / 10
    r["Iw"] = r["Iw"] / 1000.0 if r["Iw"] is not None else None   # 10^9 mm^6 -> dm^6
    recs.append(r)
for r in recs:
    validate_isection(r, log, r["Section"], web="tw", flange="tf",
                      warp_field="Iw", geom=False, fillet_check=False)
json.dump(recs, open("ipn_raw.json", "w"), indent=1)
print("\n".join(log)); print(len(log), "issues")
