# -*- coding: utf-8 -*-
"""Merge every extracted family into one catalogue data file for the repo."""
import io
import json
import os
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from lib import find_data_dir

DATA = str(find_data_dir())

def load(f): return json.load(open(f, encoding="utf-8"))
def norm(s): return s.upper().replace(" ", "").replace(".", "_")

existing = {}
for f, fam in (("en_rhs.json", "RHS"), ("en_shs.json", "SHS"),
               ("en_i_profiles.json", "I")):
    existing[fam] = {norm(r["Section"]) for r in load(os.path.join(DATA, f))}

def clean(r, drop=(), rename=None):
    rename = rename or {}
    out = {}
    for k, v in r.items():
        if k.startswith("_") or k in drop:
            continue
        out[rename.get(k, k)] = v
    return out


# --------------------------------------------------------------------------
# Normalise to the unit convention the rest of steel_sections.en already uses
# --------------------------------------------------------------------------
# eurocodepy publishes EN profiles fully cm-based -- IPE300.h is 30.0, not 300 --
# and en.UPN()/en.Angle() convert their computed results the same way. The
# catalogue prints dimensions in mm and the warping constant in three different
# units depending on the family, so both are converted here: every length below
# becomes cm and every warping constant becomes Iw in cm^6. Without this a
# catalogue row would report a depth ten times an eurocodepy row's for the same
# `sec.h`, which is exactly the kind of silent unit error a design tool must not
# ship.
_LENGTH_MM = ("h", "b", "tw", "tf", "t", "r", "r1", "r2", "d", "hi", "a", "D")
_WARP_TO_CM6 = {          # family -> factor from the printed unit to cm^6
    "UB": 1e6, "UC": 1e6, "UBP": 1e6,      # dm^6
    "HE_IPE": 1e6, "IPN": 1e6,             # dm^6
    "PFC": 1e6, "RSC": 1e6,                # dm^6, printed under the name "H"
    "UPN": 1e3,                            # 10^3 cm^6
}

def normalise(fam, rows):
    for r in rows:
        for k in _LENGTH_MM:
            if isinstance(r.get(k), (int, float)):
                r[k] = float(f"{r[k] / 10.0:.6g}")
        warp = _WARP_TO_CM6.get(fam)
        if warp:
            src = "H" if "H" in r else "Iw"
            if isinstance(r.get(src), (int, float)):
                r["Iw"] = float(f"{r.pop(src) * warp:.6g}")
            elif src == "H":
                r["Iw"] = r.pop("H", None)
    return rows

fam = {}

# ---- UB / UC / UBP -------------------------------------------------------
bs = load("bs_raw.json")
REN_I = {"s": "tw", "t": "tf", "H": "Iw", "b_2t": "b_2tf", "d_s": "d_tw"}
ORDER_I = ["Section", "m", "h", "b", "tw", "tf", "r", "d", "b_2tf", "d_tw",
           "A", "Iy", "iy", "Wel_y", "Wpl_y", "Iz", "iz", "Wel_z", "Wpl_z",
           "IT", "Iw", "U", "x"]
def order(r, keys):
    return {k: r[k] for k in keys if k in r} | {k: v for k, v in r.items() if k not in keys}
for k in ("UB", "UC", "UBP"):
    fam[k] = [order(clean(r, rename=REN_I), ORDER_I) for r in bs[k]]

# ---- EN parallel-flange beams: only variants the repo does not ship -------
en = load("en_extra_raw.json")
ORDER_EN = ["Section", "m", "h", "b", "tw", "tf", "r", "A", "hi", "d",
            "Iy", "iy", "Wel_y", "Wpl_y", "Iz", "iz", "Wel_z", "Wpl_z", "IT", "Iw"]
fam["HE_IPE"] = [order(clean(r), ORDER_EN) for r in en
                 if norm(r["Section"]) not in existing["I"]]
skipped_i = [r["Section"] for r in en if norm(r["Section"]) in existing["I"]]

# ---- IPN -----------------------------------------------------------------
ipn = load("ipn_raw.json")
ORDER_IPN = ["Section", "m", "h", "b", "tw", "tf", "r1", "r2", "d", "A",
             "Iy", "iy", "Wel_y", "Wpl_y", "Iz", "iz", "Wel_z", "Wpl_z",
             "IT", "Iw", "Avz", "SS", "AL", "AG"]
fam["IPN"] = [order(clean(r), ORDER_IPN) for r in ipn]

# ---- channels ------------------------------------------------------------
ch = load("chan_raw.json")
ORDER_CH = ["Section", "m", "h", "b", "tw", "tf", "r1", "r2", "d", "cy",
            "b_t", "d_s", "A", "Iy", "iy", "Wel_y", "Wpl_y", "Iz", "iz",
            "Wel_z", "Wpl_z", "IT", "Iw", "H", "U", "x", "ym", "Avz",
            "SS", "emax", "emin", "AL", "AG"]
for k in ("PFC", "UPN", "RSC"):
    fam[k] = [order(clean(r), ORDER_CH) for r in ch[k]]

# ---- JIS -----------------------------------------------------------------
jis = load("jis_raw.json")
ORDER_J = ["Section", "m", "h", "b", "tw", "tf", "r", "r1", "r2", "A",
           "Iy", "iy", "Wel_y", "Iz", "iz", "Wel_z"]
fam["JIS_H"] = [order(clean(r), ORDER_J) for r in jis["H"]]
fam["JIS_C"] = [order(clean(r), ORDER_J) for r in jis["C"]]

# ---- angles --------------------------------------------------------------
ang = load("ang_raw.json")
ORDER_A = ["Section", "a", "b", "t", "m", "A", "cx", "cy",
           "Iy", "iy", "Wel_y", "Wpl_y", "Iz", "iz", "Wel_z", "Wpl_z"]
fam["L_EQUAL"] = [order(clean(r), ORDER_A) for r in ang["EQ"]]
fam["L_UNEQUAL"] = [order(clean(r), ORDER_A) for r in ang["UN"]]

# ---- hollow sections: only sizes the repo does not ship ------------------
hol = load("hollow_raw.json")
ORDER_H = ["Section", "h", "b", "t", "m", "A", "Iy", "iy", "Wel_y", "Wpl_y",
           "Iz", "iz", "Wel_z", "Wpl_z", "IT", "Ct", "As"]
for k in ("RHS", "SHS"):
    fam[k] = [order(clean(r), ORDER_H) for r in hol[k]
              if norm(r["Section"]) not in existing[k]]

# ---- pipe ----------------------------------------------------------------
fam["PIPE"] = load("pipe_raw.json")

for _f, _rows in fam.items():
    normalise(_f, _rows)

meta = {
  "source": "DBMSC-STEEL GROUP, 'The Structural Steel Specification Handbook' "
            "(DBMSC/QMP07/R6), tables read from the published PDF",
  "extracted": "2026-08-30",
  "units": {
    "note": "cm-based throughout, matching the eurocodepy tables and the "
            "computed UPN/angle path in steel_sections.en",
    "dimensions h b tw tf t r r1 r2 d hi a D cx cy ym": "cm",
    "area A": "cm^2", "second_moment I": "cm^4", "modulus W": "cm^3",
    "radius_of_gyration i": "cm", "mass m": "kg/m",
    "torsion_constant IT": "cm^4", "warping_constant Iw": "cm^6",
    "detailing SS emax emin": "mm (as printed; detailing dimensions only)",
    "surface_area AL As": "m^2/m", "AG": "m^2/t", "torsion_modulus Ct": "cm^3",
    "ratios b_2tf d_tw b_t d_s U x": "dimensionless",
  },
  "families": {
    "UB":  "Universal beams, BS 4-1 designation, dims EN 10365",
    "UC":  "Universal columns, BS 4-1 designation, dims EN 10365",
    "UBP": "Universal bearing piles with wide flanges, EN 10365",
    "HE_IPE": "European parallel-flange beams: the HE AA/C and IPE AA/A/O/R/V "
              "variants that the bundled eurocodepy table does not carry",
    "IPN": "Taper-flange I sections, EN 10365 / DIN 1025-1",
    "PFC": "Parallel flange channels, EN 10365, tol. EN 10279",
    "UPN": "European standard (taper flange) channels, EN 10365",
    "RSC": "Rolled steel channels, EN 10365, tol. EN 10279",
    "JIS_H": "JIS G 3192 wide-flange H shapes",
    "JIS_C": "JIS G 3192 channels",
    "L_EQUAL": "Equal angles, EN 10056-1",
    "L_UNEQUAL": "Unequal angles, EN 10056-1",
    "RHS": "Rectangular hollow sections not present in the bundled EN table",
    "SHS": "Square hollow sections not present in the bundled EN table",
    "PIPE": "ASTM A53/A106 schedule pipe: catalogue OD/wall/mass, section "
            "properties computed exactly from the annulus",
  },
}
out = {"meta": meta, "sections": fam}
path = os.path.join(DATA, "dbmsc_catalogue.json")
json.dump(out, open(path, "w", encoding="utf-8"), indent=1)
total = sum(len(v) for v in fam.values())
for k, v in fam.items():
    print(f"  {k:10s} {len(v):4d}")
print(f"TOTAL {total} sections -> {path}")
print(f"(skipped {len(skipped_i)} HE/IPE keys already in en_i_profiles.json)")
