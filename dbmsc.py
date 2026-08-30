"""
Sections read from the DBMSC steel catalogue.

This module is the home of every shape family that is **published as a
finished property table** in

    DBMSC-STEEL GROUP, *The Structural Steel Specification Handbook*
    (DBMSC/QMP07/R6)

but that neither ``steelpy`` (AISC) nor ``eurocodepy`` (EN) ships, plus the
individual sizes those two upstream tables happen to miss.  Nothing here
replaces or shadows an existing lookup: families the repo already covered
keep their original source, and for RHS/SHS and the EN parallel-flange
beams only the designations that were *absent* were taken from the
catalogue (see ``data/dbmsc_catalogue.json`` -> ``meta``).

You will normally reach these through the friendlier standard-named
front doors rather than this module directly:

    ``steel_sections.bs``   -> UB, UC, UBP, PFC, RSC   (British families)
    ``steel_sections.jis``  -> H shapes, channels      (JIS G 3192)
    ``steel_sections.en``   -> IPN, and the HE AA/C and IPE AA/A/O/R/V
                               variants, wired into the existing EN lookups

...but ``dbmsc.section("UB", "457x191x67")`` and ``dbmsc.available("UB")``
work for anything, and ``dbmsc.Pipe(...)`` is the only route to the
ASTM A53/A106 schedule-pipe table.

Units
-----
**cm-based throughout**: lengths cm, A cm^2, I cm^4, W cm^3, i cm, torsion
constant IT cm^4, warping constant Iw cm^6, mass kg/m.  The catalogue prints
dimensions in mm and its warping constant in three different units depending
on the family; both are converted on import so that ``sec.h`` means the same
thing here as it does for an eurocodepy row (``en.IPE("IPE300").h`` is 30.0)
and for the computed ``en.UPN`` / ``en.Angle`` path.  The only fields left as
printed are the detailing dimensions ``SS``, ``emax``, ``emin`` (mm) and the
surface areas ``AL`` / ``As`` (m^2/m) / ``AG`` (m^2/t); ``meta["units"]`` in
the data file spells all of this out.

Accuracy -- read this before using the numbers in a stamped calculation
------------------------------------------------------------------------
These are the catalogue's own published figures, transcribed from the PDF
by coordinate-based table extraction, not re-derived.  A handful of cells
in the printed tables have a dropped or misplaced decimal point; each of
those was detected and corrected against an independent identity
(``A = m/0.785``, ``i = sqrt(I/A)``, ``Wel = I/(h/2)``, rolled-section
gross area, and for pipe the lb/ft column), and every correction is listed
in ``data/dbmsc_catalogue.json``'s sibling report in the README.  The
tables have **not** been certified against the underlying standards
(EN 10365, EN 10056-1, JIS G 3192, ASTM A6/A53).  Treat them the same way
as the hand-compiled UPN/angle tables already in this package: good enough
to size and compare with, verify against the standard or a mill
certificate before they carry a signature.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ._common import Section, data_path

_DATA = Path(__file__).parent / "data"
_FILE = _DATA / "dbmsc_catalogue.json"

with open(data_path(_FILE), encoding="utf-8") as _f:
    _CATALOGUE = json.load(_f)

META = _CATALOGUE["meta"]
_SECTIONS = _CATALOGUE["sections"]

_UNITS = ("cm-based: cm, cm^2, cm^3, cm^4, cm^6 (Iw); mass kg/m "
          "(DBMSC catalogue, converted from the printed mm/dm^6)")
_SOURCE = "DBMSC Structural Steel Specification Handbook (DBMSC/QMP07/R6)"

#: Which standard each family's numbers are published against.
STANDARD = {
    "UB": "BS 4-1 designation / EN 10365",
    "UC": "BS 4-1 designation / EN 10365",
    "UBP": "BS 4-1 designation / EN 10365",
    "HE_IPE": "EN 10365",
    "IPN": "EN 10365 / DIN 1025-1",
    "PFC": "EN 10365 (tol. EN 10279)",
    "UPN": "EN 10365 (tol. EN 10279)",
    "RSC": "EN 10365 (tol. EN 10279)",
    "JIS_H": "JIS G 3192",
    "JIS_C": "JIS G 3192",
    "L_EQUAL": "EN 10056-1",
    "L_UNEQUAL": "EN 10056-1",
    "RHS": "EN 10210 / EN 10219",
    "SHS": "EN 10210 / EN 10219",
    "PIPE": "ASTM A53 / A106",
}

#: Designation prefixes that may be given or omitted when looking a shape up.
_PREFIX = {
    "UB": ("UB",), "UC": ("UC",), "UBP": ("UBP", "UBPILE"),
    "PFC": ("PFC",), "RSC": ("RSC",), "UPN": ("UPN",), "IPN": ("IPN",),
    "JIS_H": ("H", "JISH"), "JIS_C": ("C", "JISC"),
    "L_EQUAL": ("L",), "L_UNEQUAL": ("L",),
    "RHS": ("RHS",), "SHS": ("SHS",), "PIPE": ("PIPE",),
    "HE_IPE": (),
}


def _norm(designation: str) -> str:
    return re.sub(r"[\s_*-]", "", str(designation)).upper()


def _build_index(family: str) -> dict:
    idx = {}
    for row in _SECTIONS[family]:
        key = _norm(row["Section"])
        idx[key] = row
    # the family prefix is optional either way round: index "UB457X191X67"
    # alongside "457X191X67" so both spellings resolve
    for row in _SECTIONS[family]:
        key = _norm(row["Section"])
        for pre in _PREFIX.get(family, ()):
            if key.startswith(pre) and len(key) > len(pre):
                idx.setdefault(key[len(pre):], row)
            else:
                idx.setdefault(pre + key, row)
    return idx


_INDEX = {fam: _build_index(fam) for fam in _SECTIONS}


def families() -> list[str]:
    """Every catalogue family name, in catalogue order."""
    return list(_SECTIONS)


def available(family: str) -> list[str]:
    """Designations available in `family`, as printed in the catalogue."""
    fam = family.upper()
    if fam not in _SECTIONS:
        raise KeyError(f"{family!r} is not a catalogue family. Available: {families()}")
    return [row["Section"] for row in _SECTIONS[fam]]


def section(family: str, designation: str) -> Section:
    """Look a shape up, e.g. ``section("UB", "457x191x67")``.

    The family's own prefix is optional: ``"UB457x191x67"`` and
    ``"457 x 191 x 67"`` both resolve.
    """
    fam = family.upper()
    if fam not in _INDEX:
        raise KeyError(f"{family!r} is not a catalogue family. Available: {families()}")
    idx = _INDEX[fam]
    key = _norm(designation)
    row = idx.get(key)
    if row is None:
        stem = re.split(r"X", key)[0]
        near = [k for k in idx if k.startswith(stem)][:8]
        hint = f" Close matches: {near}" if near else ""
        raise KeyError(f"{designation!r} not found in catalogue family {fam}.{hint}")
    props = {k: v for k, v in row.items() if k != "Section"}
    return Section(designation=row["Section"], family=fam,
                   standard=STANDARD.get(fam, "DBMSC catalogue"),
                   units=_UNITS, source=_SOURCE, properties=props)


def Pipe(designation: str) -> Section:
    """ASTM A53/A106 schedule pipe, e.g. ``Pipe("PIPE6-168.3x7.11")``.

    Outside diameter, wall thickness, mass and schedule number are the
    catalogue's; A, I, Wel, Wpl, i and IT are computed exactly from the
    annulus (there is nothing to approximate for a circular tube).
    """
    return section("PIPE", designation)


def find_pipe(nps: str, thickness: float | None = None,
              schedule: str | float | None = None) -> list[Section]:
    """Every schedule-pipe row for a nominal size, optionally narrowed.

    >>> find_pipe("6", schedule=40)[0].t     # cm, like every other length
    0.711
    """
    want = str(nps).strip()
    out = []
    for row in _SECTIONS["PIPE"]:
        if str(row["NPS"]).strip() != want:
            continue
        if thickness is not None and abs(row["t"] - thickness) > 1e-6:
            continue
        if schedule is not None and str(row.get("schedule")) != str(float(schedule)):
            continue
        out.append(section("PIPE", row["Section"]))
    return out
