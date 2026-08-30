# -*- coding: utf-8 -*-
"""JIS G 3192 wide-flange H shapes (pp. 50-52) and JIS channels (p. 59)."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from lib import table
from validate import validate_isection

H = [("m",74),("h",92),("b",109),("tw",128),("tf",146),("r",163),("A",178),
     ("Iy",200),("Iz",220),("iy",238),("iz",255),("Wel_y",272),("Wel_z",290)]
C = [("m",81),("tw",103),("tf",121),("r1",142),("r2",161),("A",179),
     ("Iy",202),("Iz",221),("iy",239),("iz",256),("Wel_y",273),("Wel_z",291)]

log = []
hrecs = []
for pg in (49, 50, 51):
    for r in table(pg, H, y_min=115, desig_max=70, min_cells=8):
        rec = {k: r[k] for k, _ in H}
        if None in (rec["h"], rec["b"], rec["tw"], rec["tf"]):
            continue
        rec["Section"] = "H%gx%gx%gx%g" % (rec["h"], rec["b"], rec["tw"], rec["tf"])
        hrecs.append(rec)
for r in hrecs:
    validate_isection(r, log, r["Section"], web="tw", flange="tf",
                      warping=False, fillet_check=False)
print(f"JIS H: {len(hrecs)} sections ({hrecs[0]['Section']} ... {hrecs[-1]['Section']})")

crecs = []
for r in table(58, C, y_min=118, desig_max=75, min_cells=8):
    rec = {k: r[k] for k, _ in C}
    rec["Section"] = "C" + r["_desig"]
    crecs.append(rec)
for r in crecs:
    validate_isection(r, log, r["Section"], web="tw", flange="tf",
                      warping=False, geom=False, fillet_check=False)
print(f"JIS C: {len(crecs)} sections ({crecs[0]['Section']} ... {crecs[-1]['Section']})")
json.dump({"H": hrecs, "C": crecs}, open("jis_raw.json", "w"), indent=1)
print("\n".join(log)); print(len(log), "issues")
