"""Sanity-check steel_sections against known published reference values."""
import math
import sys

import steel_sections as ss

failures = []


def check(label, got, expected, tol=0.02):
    err = abs(got - expected) / abs(expected)
    status = "OK" if err <= tol else "FAIL"
    print(f"[{status}] {label}: got {got:.4g}, expected ~{expected:.4g} ({err:.1%})")
    if err > tol:
        failures.append(label)


# --- AISC (via steelpy) ------------------------------------------------
w = ss.aisc.W("W12X40")
check("AISC W12X40 A (in^2)", w.A if hasattr(w, "A") else w.area, 11.7)
check("AISC W12X40 Ix (in^4)", w.Ix, 307.0)

# --- EN I-profiles (via eurocodepy data) --------------------------------
hea100 = ss.en.HEA("HEA100")
check("EN HEA100 A (cm^2)", hea100.A, 21.24)
check("EN HEA100 Iy (cm^4)", hea100.Iy, 349.2)

ipe300 = ss.en.IPE("IPE300")
check("EN IPE300 A (cm^2)", ipe300.A, 53.81, tol=0.03)
check("EN IPE300 Iy (cm^4)", ipe300.Iy, 8356, tol=0.03)

# --- EN hollow sections --------------------------------------------------
chs = ss.en.CHS("CHS168.3x5")
check("EN CHS168.3x5 A (cm^2)", chs.A, 25.7, tol=0.03)

# --- EN UPN (computed via sectionproperties) ----------------------------
upn200 = ss.en.UPN("UPN200")
check("EN UPN200 A (cm^2, computed)", upn200.A, 32.2, tol=0.06)
check("EN UPN200 Iy (cm^4, computed)", upn200.Iy, 1910, tol=0.06)

# --- EN angle (computed) -------------------------------------------------
l100 = ss.en.Angle("L100x100x10")
check("EN L100x100x10 A (cm^2, computed)", l100.A, 19.2, tol=0.06)

# --- Catalogue families: BS UB / UC / UBP / PFC / RSC ---------------------
ub = ss.bs.UB("457x191x67")
check("BS UB 457x191x67 A (cm^2)", ub.A, 85.5)
check("BS UB 457x191x67 Iy (cm^4)", ub.Iy, 29400)
check("BS UB 457x191x67 Wpl_y (cm^3)", ub.Wpl_y, 1470)

uc = ss.bs.UC("254x254x73")
check("BS UC 254x254x73 A (cm^2)", uc.A, 93.1)
check("BS UC 254x254x73 Iy (cm^4)", uc.Iy, 11400)

check("BS UBP 305x305x186 Iy (cm^4)", ss.bs.UBP("305x305x186").Iy, 42600)
check("BS PFC 200x90x30 Iy (cm^4)", ss.bs.PFC("200x90x30").Iy, 2520)
check("BS RSC 305x102 Iy (cm^4)", ss.bs.RSC("305x102").Iy, 8210)

# --- Catalogue families: JIS G 3192 --------------------------------------
jh = ss.jis.H("H400x400x13x21")
check("JIS H400x400x13x21 A (cm^2)", jh.A, 218.7)
check("JIS H400x400x13x21 Iy (cm^4)", jh.Iy, 66600)
check("JIS C200x80x7.5 Iy (cm^4)", ss.jis.C("C200x80x7.5").Iy, 1950)

# --- EN families added from the catalogue --------------------------------
ipn = ss.en.IPN("IPN300")
check("EN IPN300 A (cm^2)", ipn.A, 69.0)
check("EN IPN300 Iy (cm^4)", ipn.Iy, 9800)
check("EN IPN300 Wel_y (cm^3)", ipn.Wel_y, 653)
check("EN HEAA300 A (cm^2)", ss.en.HEAA("HEAA300").A, 88.9)
check("EN IPE O 300 A (cm^2)", ss.en.IPE("IPE O 300").A, 62.8)

# a hollow size the bundled EN table does not carry, checked against the
# closed-form area of the tube: 4*t*(b-t) - (4-pi)*t^2
_b, _t = 76.2, 4.0
check("EN SHS76.2x76.2x4 A (cm^2)",
      ss.en.SHS("SHS76.2x76.2x4").A,
      (4 * _t * (_b - _t) - (4 - math.pi) * _t ** 2) / 100, tol=0.05)

# --- ASTM A53/A106 schedule pipe (properties computed from the annulus) ---
p6 = ss.dbmsc.Pipe("PIPE6-168.3x7.11")
check("Pipe 6in sch40 mass (kg/m)", p6.m, 28.26)
check("Pipe 6in sch40 A (cm^2)", p6.A, 36.0)
check("Pipe 6in sch40 I (cm^4)", p6.I, 1170)

# --- sizes appended to the existing dimension tables still compute --------
check("EN L100x100x8 A (cm^2, computed)", ss.en.Angle("L100x100x8").A, 15.5, tol=0.05)
check("EN L125x75x10 A (cm^2, computed)", ss.en.Angle("L125x75x10").A, 19.1, tol=0.06)

# --- no regressions: the pre-existing tables still answer for their own ---
assert ss.en.IPE("IPE300").source.startswith("eurocodepy"), "IPE300 changed source"
assert ss.en.RHS("RHS150x100x6").source.startswith("eurocodepy"), "RHS changed source"
print("[OK] existing EN designations still resolve to the eurocodepy tables")

# --- one unit system across both tables: a depth means the same thing --------
# eurocodepy publishes EN profiles cm-based (IPE300.h == 30.0); the catalogue
# prints mm and is converted on import. If that conversion is ever dropped, a
# catalogue depth comes back 10x too large and every check built on it is wrong.
assert abs(ss.en.IPN("IPN300").h - ss.en.IPE("IPE300").h) < 1e-9, \
    "IPN300 and IPE300 are both 300 mm deep but report different h -- unit drift"
for _fam in ss.dbmsc.families():
    for _d in ss.dbmsc.available(_fam):
        _h = ss.dbmsc.section(_fam, _d).get("h") or ss.dbmsc.section(_fam, _d).get("D")
        assert _h is None or _h < 150, f"{_fam} {_d}: h={_h} looks like mm, not cm"
print("[OK] catalogue lengths are cm, consistent with the eurocodepy tables")

# --- Generic rod / flat bar (closed form) --------------------------------
r = ss.rod(20)
check("rod d=20 A (mm^2)", r.A, math.pi * 100)
check("rod d=20 Ix (mm^4)", r.Ix, math.pi * 20 ** 4 / 64)

fb = ss.flat_bar(100, 10)
check("flat_bar 100x10 A (mm^2)", fb.A, 1000.0)

# --- Cold-formed C section runs without error ----------------------------
cee = ss.cold_formed_cee(d=150, b=50, lip=15, t=1.5)
print(f"[OK] cold_formed_cee ran: A={cee.A:.1f} mm^2, Ix={cee.Ix:.0f} mm^4")

print()
if failures:
    print(f"{len(failures)} check(s) FAILED: {failures}")
    sys.exit(1)
print("All checks passed.")
