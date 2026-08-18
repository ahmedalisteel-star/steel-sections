"""
AISC steel shapes, via steelpy (https://github.com/evanfaler/steelpy, Apache-2.0).

steelpy reproduces the official AISC Steel Construction Manual, 16th Ed.
shape tables (imperial units: in, in^2, in^3, in^4, kip). Install it with::

    pip install steelpy

Categories available (AISC "shape series"):
    W, M, S, HP        -- I/wide-flange shapes
    C, MC               -- channels
    L                    -- single angles
    DBL_L                -- back-to-back double angles
    WT, MT, ST           -- structural tees (cut from W/M/S)
    HSS                  -- rectangular & square hollow sections (RHS/SHS analog)
    HSS_R                -- round hollow sections (CHS analog)
    PIPE                 -- pipe

Usage
-----
>>> import steel_sections as ss
>>> ss.aisc.W("W12X40").Ix
307.0
>>> ss.aisc.HSS_round("HSS4.000X0.250").A   # note: steelpy needs the padded decimal form
...
>>> ss.aisc.available("L")[:5]
[...]
"""

from __future__ import annotations

from ._common import Section

try:
    from steelpy import aisc as _aisc
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The AISC module needs the 'steelpy' package. Install it with:\n"
        "    pip install steelpy"
    ) from exc

_UNITS = "imperial: in, in^2, in^3, in^4, kip (AISC Manual 16th Ed., via steelpy)"

_CATEGORY_MAP = {
    "W": "W_shapes", "M": "M_shapes", "S": "S_shapes", "HP": "HP_shapes",
    "C": "C_shapes", "MC": "MC_shapes",
    "L": "L_shapes", "DBL_L": "DBL_L_shapes",
    "WT": "WT_shapes", "MT": "MT_shapes", "ST": "ST_shapes",
    "HSS": "HSS_shapes", "HSS_R": "HSS_R_shapes",
    "PIPE": "PIPE_shapes",
}


def _normalize(designation: str) -> str:
    return designation.strip().upper().replace(" ", "").replace(".", "_").replace("-", "_")


def get(category: str, designation: str) -> Section:
    """Look up any AISC shape by category code (see module docstring) and
    designation, e.g. ``get("HSS_R", "HSS4X0.250")`` or ``get("L", "L4X4X1/2")``.
    """
    if category not in _CATEGORY_MAP:
        raise KeyError(f"Unknown AISC category {category!r}. Choose from {sorted(_CATEGORY_MAP)}")
    profile = getattr(_aisc, _CATEGORY_MAP[category])
    key = _normalize(designation)
    # steelpy stores fractions like 1/2 as "1_2" in section names
    key = key.replace("/", "_")
    try:
        sec = profile.sections[key]
    except KeyError:
        matches = [k for k in profile.sections if key in k]
        hint = f" Close matches: {matches[:8]}" if matches else ""
        raise KeyError(f"{designation!r} not found in AISC {category} shapes.{hint}") from None
    return Section(designation=key, family=category, standard="AISC",
                    units=_UNITS, source="steelpy (Apache-2.0)",
                    properties=sec.properties)


def available(category: str) -> list[str]:
    """List every designation available for a given AISC category."""
    profile = getattr(_aisc, _CATEGORY_MAP[category])
    return sorted(profile.sections)


# Convenience per-category shortcuts -----------------------------------------
def W(designation: str) -> Section: return get("W", designation)
def M(designation: str) -> Section: return get("M", designation)
def S(designation: str) -> Section: return get("S", designation)
def HP(designation: str) -> Section: return get("HP", designation)
def C(designation: str) -> Section: return get("C", designation)
def MC(designation: str) -> Section: return get("MC", designation)
def L(designation: str) -> Section: return get("L", designation)
def DBL_L(designation: str) -> Section: return get("DBL_L", designation)
def WT(designation: str) -> Section: return get("WT", designation)
def MT(designation: str) -> Section: return get("MT", designation)
def ST(designation: str) -> Section: return get("ST", designation)
def HSS(designation: str) -> Section: return get("HSS", designation)
def HSS_round(designation: str) -> Section: return get("HSS_R", designation)
def Pipe(designation: str) -> Section: return get("PIPE", designation)
