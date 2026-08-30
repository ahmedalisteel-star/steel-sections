# -*- coding: utf-8 -*-
"""Append the catalogue's new angle / UPN sizes to the existing dimension CSVs.

Purely additive: existing rows are read, kept verbatim, and only designations
that are absent are appended.  Root/toe radii follow EN 10056-1 / EN 10365,
taken from the rows the table already carries for the same leg width.
"""
import csv
import io
import json
import os
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from lib import find_data_dir

DATA = str(find_data_dir())

cat = json.load(open(os.path.join(DATA, "dbmsc_catalogue.json"), encoding="utf-8"))["sections"]

# EN 10056-1 root (r1) / toe (r2) radii for leg widths the CSVs do not yet have
EXTRA_R = {(125.0, 75.0): (11.0, 5.5), (150.0, 75.0): (11.0, 5.5)}

def read(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        return rd.fieldnames, list(rd)

def write(name, fields, rows):
    with open(os.path.join(DATA, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

def g(x):
    """Catalogue values are cm; the dimension CSVs are mm."""
    return f"{x:g}"


def mm(x):
    return f"{x * 10:g}"

# ---------------------------------------------------------------- equal ----
fields, rows = read("angles_equal_en10056.csv")
have = {r["designation"].upper() for r in rows}
radii = {float(r["a_mm"]): (r["r1_mm"], r["r2_mm"]) for r in rows}
added = 0
for s in cat["L_EQUAL"]:
    key = s["Section"].upper()
    if key in have:
        continue
    a = s["a"] * 10
    if a not in radii:
        print(f"  !! no radius reference for equal leg {a}: {key} skipped")
        continue
    r1, r2 = radii[a]
    rows.append({"designation": s["Section"], "a_mm": mm(a), "t_mm": mm(s["t"]),
                 "r1_mm": r1, "r2_mm": r2, "mass_kg_m": g(s["m"])})
    added += 1
rows.sort(key=lambda r: (float(r["a_mm"]), float(r["t_mm"])))
write("angles_equal_en10056.csv", fields, rows)
print(f"equal angles: +{added} -> {len(rows)} rows")

# -------------------------------------------------------------- unequal ----
fields, rows = read("angles_unequal_en10056.csv")
have = {r["designation"].upper() for r in rows}
radii = {(float(r["b1_mm"]), float(r["b2_mm"])): (r["r1_mm"], r["r2_mm"]) for r in rows}
radii.update({k: (g(v[0]), g(v[1])) for k, v in EXTRA_R.items()})
added = 0
for s in cat["L_UNEQUAL"]:
    key = s["Section"].upper()
    if key in have:
        continue
    pair = (s["a"] * 10, s["b"] * 10)
    if pair not in radii:
        print(f"  !! no radius reference for {pair}: {key} skipped")
        continue
    r1, r2 = radii[pair]
    rows.append({"designation": s["Section"], "b1_mm": g(s["a"]), "b2_mm": mm(s["b"]),
                 "t_mm": mm(s["t"]), "r1_mm": r1, "r2_mm": r2, "mass_kg_m": g(s["m"])})
    added += 1
rows.sort(key=lambda r: (float(r["b1_mm"]), float(r["b2_mm"]), float(r["t_mm"])))
write("angles_unequal_en10056.csv", fields, rows)
print(f"unequal angles: +{added} -> {len(rows)} rows")

# ------------------------------------------------------------------ UPN ----
fields, rows = read("upn_en10365.csv")
have = {r["designation"].upper() for r in rows}
added = 0
for s in cat["UPN"]:
    key = s["Section"].upper()
    if key in have:
        continue
    rows.append({"designation": s["Section"], "h_mm": mm(s["h"]), "b_mm": mm(s["b"]),
                 "tw_mm": mm(s["tw"]), "tf_mm": mm(s["tf"]), "r1_mm": mm(s["r1"]),
                 "r2_mm": mm(s["r2"]), "mass_kg_m": g(s["m"])})
    added += 1
rows.sort(key=lambda r: (float(r["h_mm"]), float(r["b_mm"]), float(r["tw_mm"])))
write("upn_en10365.csv", fields, rows)
print(f"UPN: +{added} -> {len(rows)} rows")
