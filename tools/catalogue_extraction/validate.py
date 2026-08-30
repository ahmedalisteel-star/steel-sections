# -*- coding: utf-8 -*-
"""Physics-based sanity checks + repair for rows extracted from the catalogue.

The catalogue's typesetting drops or duplicates the odd cell (a lost decimal
point, a value repeated from the neighbouring column).  Every repair below is
justified by an independent identity -- rolled-section geometry, i = sqrt(I/A),
Wel = I/(h/2), m = 0.785*A -- and anything that cannot be reconciled is
reported as a FLAG rather than silently kept.

Units: dimensions in mm, section properties in cm-based units (cm^2, cm^3,
cm^4), warping constant in dm^6, mass in kg/m.
"""
import math

RHO = 0.785          # kg/m per cm^2 of steel section area
FILLET = 4.0 - math.pi   # area of the four root fillets is (4-pi)*r^2

def _scale_fix(val, target, tol):
    for k in (1, -1, 2, -2, 3, -3, 4, -4):
        v = val * (10.0 ** k)
        if abs(v - target) <= tol * abs(target):
            return v
    return None

def _chk(rec, field, expected, tol, log, tag, derive=False, exact=0.001):
    """Compare rec[field] against an identity-derived `expected`.

    `derive=True` marks a field the identity reproduces exactly (d, Wel, i,
    ratios): if the printed cell cannot be recovered by a 10^k shift landing
    within `exact`, the identity value is substituted so the row stays
    internally consistent.  Primaries are only ever repaired by a 10^k shift.
    """
    v = rec.get(field)
    if v is None or expected is None or expected == 0:
        return
    if abs(v - expected) <= tol * abs(expected):
        return
    fixed = _scale_fix(v, expected, tol)
    if fixed is not None and (not derive or abs(fixed - expected) <= exact * abs(expected)):
        log.append(f"REPAIR {tag:24s} {field:6s} {v:<11g} -> {fixed:<11g} (expect ~{expected:.4g})")
        rec[field] = float(f"{fixed:.6g}")
    elif derive:
        val = float(f"{expected:.4g}")
        log.append(f"DERIVE {tag:24s} {field:6s} {v:<11g} -> {val:<11g} (identity)")
        rec[field] = val
    else:
        log.append(f"FLAG   {tag:24s} {field:6s} {v:<11g}    expect ~{expected:.4g}")

def _consensus(cands, tol):
    """Mean of the largest mutually-agreeing group of candidate values."""
    cands = [c for c in cands if c]
    best = []
    for c in cands:
        grp = [d for d in cands if abs(d - c) <= tol * abs(c)]
        if len(grp) > len(best):
            best = grp
    return sum(best) / len(best) if len(best) >= 2 else None

def area_geom(h, b, tw, tf, r):
    """Gross area of a doubly-symmetric rolled I/H section, cm^2."""
    if None in (h, b, tw, tf, r):
        return None
    return (2 * b * tf + (h - 2 * tf) * tw + FILLET * r * r) / 100.0

def validate_isection(r, log, tag, nominal_mass=None, warping=True,
                      web="s", flange="t", warp_field="H", geom=True,
                      fillet_check=True):
    """Staged validation of a rolled I/H row."""
    g = r.get
    tw, tf = g(web), g(flange)
    h, b, rr = g("h"), g("b"), g("r")

    # -- stage 0: depth, arbitrated by Wel_y = Iy / (h/2) and by gross area ----
    if h and g("Iy") and g("Wel_y"):
        h_alt = 20.0 * g("Iy") / g("Wel_y")
        if abs(h_alt - h) > 0.02 * h and g("A"):
            a0, a1 = area_geom(h, b, tw, tf, rr), area_geom(h_alt, b, tw, tf, rr)
            if a1 and a0 and abs(a1 - g("A")) < abs(a0 - g("A")):
                log.append(f"DERIVE {tag:24s} {'h':6s} {h:<11g} -> {h_alt:<11.4g} (2*Iy/Wel_y)")
                r["h"] = h = float(f"{h_alt:.4g}")

    # -- stage 1: gross area, by consensus of geometry and mass ------------
    ag = area_geom(h, b, tw, tf, rr) if geom else None
    cands = [ag, (g("m") / RHO if g("m") else None)]
    for I, i in (("Iy", "iy"), ("Iz", "iz")):
        if g(I) and g(i):
            cands.append(g(I) / g(i) ** 2)
    cands = [c for c in cands if c]
    exp_A = _consensus(cands, 0.03)
    if exp_A:
        _chk(r, "A", exp_A, 0.05, log, tag, derive=True, exact=0.05)
    elif ag:
        _chk(r, "A", ag, 0.05, log, tag)
    A = g("A")
    if A:
        _chk(r, "m", A * RHO, 0.05, log, tag,
             derive=bool(exp_A), exact=0.05)
    if nominal_mass:
        _chk(r, "m", nominal_mass, 0.03, log, tag)

    # -- stage 1b: second moments, by consensus of i^2*A and Wel*(h/2) -------
    for I, i, W, dim in (("Iy", "iy", "Wel_y", h), ("Iz", "iz", "Wel_z", b)):
        if not g(I):
            continue
        cands = []
        if A and g(i):
            cands.append(g(i) ** 2 * A)
        if g(W) and dim:
            cands.append(g(W) * dim / 20.0)
        exp_I = _consensus(cands, 0.04)
        if exp_I:
            _chk(r, I, exp_I, 0.06, log, tag)

    # -- stage 2: depth between fillets / straight web portion ----------------
    if fillet_check and h and tf and rr is not None and g("d"):
        _chk(r, "d", h - 2 * tf - 2 * rr, 0.03, log, tag, derive=True)
    if fillet_check and h and tf and g("hi"):
        _chk(r, "hi", h - 2 * tf, 0.03, log, tag, derive=True)

    # -- stage 3: radii of gyration -------------------------------------------
    A = g("A")
    if A:
        if g("Iy"): _chk(r, "iy", math.sqrt(g("Iy") / A), 0.03, log, tag, derive=True)
        if g("Iz"): _chk(r, "iz", math.sqrt(g("Iz") / A), 0.03, log, tag, derive=True)

    # -- stage 4: elastic moduli ----------------------------------------------
    if g("Iy") and h:
        _chk(r, "Wel_y", g("Iy") / (h / 20.0), 0.06, log, tag, derive=True)
    if g("Iz") and b:
        _chk(r, "Wel_z", g("Iz") / (b / 20.0), 0.06, log, tag, derive=True)

    # -- stage 5: plastic moduli (ratio bounds only -- no exact identity) -----
    if g("Wel_y"): _chk(r, "Wpl_y", g("Wel_y") * 1.15, 0.18, log, tag)
    if g("Wel_z"): _chk(r, "Wpl_z", g("Wel_z") * 1.60, 0.28, log, tag)

    # -- stage 6: local-buckling ratios and warping constant ------------------
    if fillet_check and b and tf: _chk(r, "b_2t", b / (2 * tf), 0.03, log, tag, derive=True)
    if fillet_check and g("d") and tw: _chk(r, "d_s", g("d") / tw, 0.03, log, tag, derive=True)
    if warping and g("Iz") and h and tf:
        exp = g("Iz") * ((h - tf) / 10.0) ** 2 / 4.0 / 1e6
        if exp >= 0.01:                     # below this the table rounds to 0.000
            _chk(r, warp_field, exp, 0.12, log, tag)
