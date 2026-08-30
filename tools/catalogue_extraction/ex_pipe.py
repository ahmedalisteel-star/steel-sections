# -*- coding: utf-8 -*-
"""ASTM A53 / A106 schedule pipe, catalogue pp.122-127."""
import sys, io, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from lib import table

COLS = [("OD_in",72),("D",98),("t_in",120),("t",146),("m_lbft",169),("m",192),("schedule",287)]
log, out, nps = [], [], None
for pg in range(121, 127):
    for r in table(pg, COLS, y_min=118, desig_max=66, min_cells=5, desig_join=""):
        if r["_desig"]:
            nps = r["_desig"]
        if nps is None or r["D"] is None or r["t"] is None:
            continue
        D, t = r["D"], r["t"]
        d = D - 2 * t
        A = math.pi / 4 * (D ** 2 - d ** 2) / 100.0                 # cm^2
        I = math.pi / 64 * (D ** 4 - d ** 4) / 1e4                  # cm^4
        rec = {
            "Section": "PIPE%s-%gx%g" % (nps.replace(" ", ""), D, t),
            "NPS": nps, "D": D, "t": t, "m": r["m"],
            "schedule": r["schedule"],
            "A": float(f"{A:.4g}"), "I": float(f"{I:.4g}"),
            "i": float(f"{math.sqrt(I / A):.4g}"),
            "Wel": float(f"{2 * I / (D / 10.0):.4g}"),
            "Wpl": float(f"{(D ** 3 - d ** 3) / 6.0 / 1e3:.4g}"),
            "IT": float(f"{2 * I:.4g}"),
        }
        if rec["m"] and abs(rec["m"] - A * 0.785) > 0.04 * rec["m"]:
            # the lb/ft column is the independent witness for a mistyped kg/m
            alt = r["m_lbft"] * 1.48816 if r["m_lbft"] else None
            if alt and abs(alt - A * 0.785) <= 0.04 * alt:
                log.append(f"REPAIR {rec['Section']:22s} m {rec['m']} -> {alt:.2f} (from lb/ft)")
                rec["m"] = float(f"{alt:.4g}")
            else:
                log.append(f"FLAG   {rec['Section']:22s} m {rec['m']} vs computed {A*0.785:.3f}")
        out.append(rec)
print(f"pipes: {len(out)} ({out[0]['Section']} ... {out[-1]['Section']})")
json.dump(out, open("pipe_raw.json", "w"), indent=1)
print("\n".join(log[:25])); print(len(log), "issues")
