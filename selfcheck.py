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
