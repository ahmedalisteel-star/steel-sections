# -*- coding: utf-8 -*-
"""Coordinate-based table extraction from the DBMSC catalogue PDF."""
import os
import re
from pathlib import Path

import pymupdf

# The catalogue PDF is not redistributed with this repo. Point DBMSC_PDF at
# your copy, or drop it in the repo root under this name.
def find_pdf() -> str:
    """Locate the catalogue PDF, which this repo does not redistribute.

    Set DBMSC_PDF to your copy; otherwise the nearest file named like the
    handbook, searched upward from this script, is used.
    """
    override = os.environ.get("DBMSC_PDF")
    if override:
        return override
    for base in Path(__file__).resolve().parents:
        for match in sorted(base.glob("*Section Table Product Catalogue*.pdf")):
            return str(match)
    return str(Path(__file__).resolve().parents[2] / "Section Table Product Catalogue.pdf")


PDF = find_pdf()
def find_data_dir() -> Path:
    """Locate the package's data/ directory from either repo layout.

    Flat repo: the package is the repo root, so data/ is a sibling of tools/.
    Vendored: the package is nested, so it is steel_sections/data/. Probe for a
    file that is certainly there rather than assuming a fixed depth.
    """
    for base in Path(__file__).resolve().parents:
        for cand in (base / "data", base / "steel_sections" / "data"):
            if (cand / "en_chs.json").is_file():
                return cand
    raise SystemExit(
        "could not find the steel_sections data/ directory above "
        f"{Path(__file__).resolve()}"
    )

_doc = None
def doc():
    global _doc
    if _doc is None:
        _doc = pymupdf.open(PDF)
    return _doc

NUMRE = re.compile(r"^[-+]?[\d][\d.,:]*\.?$")

def parse_num(tok):
    t = tok.strip()
    if t in ("-", "--", "", "\u2014"):
        return None
    t = t.replace(":", ".").rstrip(".")
    if re.match(r"^\d{1,3}(,\d{3})+(\.\d+)?$", t):      # 46,800 thousands
        t = t.replace(",", "")
    t = t.replace(",", ".")                              # 5,5 -> 5.5
    try:
        return float(t)
    except ValueError:
        return None

def rows(page, rotated=False, tol=2.6):
    """[(row_key, [(col_key, word), ...]), ...] top-to-bottom, left-to-right."""
    ws = doc()[page].get_text("words")
    pts = [((y0, x0, w) if rotated else (x0, y0, w)) for x0, y0, x1, y1, w, *_ in ws]
    buckets = []
    for col, row, w in sorted(pts, key=lambda t: (t[1], t[0])):
        for b in buckets:
            if abs(b[0] - row) <= tol:
                b[1].append((col, w)); break
        else:
            buckets.append([row, [(col, w)]])
    for b in buckets:
        b[1].sort(key=lambda t: t[0])
    buckets.sort(key=lambda b: b[0])
    return [(b[0], b[1]) for b in buckets]

def table(page, cols, y_min, y_max=1e9, desig_max=None, desig_min=None,
          rotated=False, tol=2.6, win=8.0, min_cells=3, desig_join="",
          desig_reverse=False):
    """Extract rows of a table.

    cols: list of (name, x_centre). Tokens snap to the nearest centre within `win`.
    desig_max: tokens left of this x are the designation stub.
    Returns list of dicts: {"_y":.., "_desig":.., name: value|None, ...}
    """
    out = []
    for rk, toks in rows(page, rotated, tol):
        if not (y_min <= rk <= y_max):
            continue
        rec = {"_y": round(rk, 1), "_desig": None}
        stub, cells = [], {}
        for cx, w in toks:
            if desig_max is not None and cx < desig_max:
                stub.append(w); continue
            if desig_min is not None and cx > desig_min:
                stub.append(w); continue
            if not (NUMRE.match(w) or w in ("-", "—")):
                continue
            best, bd = None, win
            for name, cxx in cols:
                d = abs(cx - cxx)
                if d < bd:
                    best, bd = name, d
            if best is not None and best not in cells:
                cells[best] = parse_num(w)
        if len(cells) < min_cells:
            continue
        if desig_reverse:
            stub.reverse()
        rec["_desig"] = desig_join.join(stub) if stub else None
        for name, _ in cols:
            rec[name] = cells.get(name)
        out.append(rec)
    return out

def dump(recs, keys=None, n=99):
    for r in recs[:n]:
        ks = keys or [k for k in r if not k.startswith("_")]
        print(f"{r['_y']:6.1f} {str(r['_desig']):22s} " +
              " ".join(f"{k}={r[k]}" for k in ks))
