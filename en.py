"""
EN / Eurocode steel shapes.

Two different data sources feed this module, matching the DRY_RUN note in
the package docstring / README:

1. IPE, HEA, HEB, HEM (hot-rolled I/H sections) and CHS, RHS, SHS (hollow
   sections) are looked up directly from JSON tables copied from the
   **eurocodepy** project (https://github.com/pcachim/eurocodepy,
   LGPL-3.0). These are pre-computed Eurocode 3 section properties
   (cm-based units), not re-derived here.

2. UPN channels (EN 10365) and equal/unequal angles (EN 10056-1) are *not*
   available as ready-made property tables in eurocodepy, so this module
   keeps a small hand-compiled **dimensions-only** table
   (``data/upn_en10365.csv``, ``data/angles_equal_en10056.csv``,
   ``data/angles_unequal_en10056.csv``) and computes A, I, W, i, J, etc. on
   the fly with the **sectionproperties** finite-element section analysis
   engine (https://github.com/robbievanleeuwen/section-properties, MIT).
   Results are cached after first computation.

   These dimensions were hand-compiled from published manufacturer/standard
   datasheets and have *not* been independently certified against EN
   10365 / EN 10056-1 -- treat them as a convenience subset and verify
   before production use (see README.md).

Units: everything in this module is **cm-based** (cm, cm^2, cm^3, cm^4),
matching how eurocodepy publishes its tables and how Eurocode 3
calculations are usually done by hand. Dimension tables (h_mm etc.) stay
in mm as-received; computed property outputs are converted to cm units for
consistency with the IPE/HEA/HEB/HEM/CHS/RHS/SHS lookups.

Usage
-----
>>> import steel_sections as ss
>>> ss.en.IPE("IPE300").Iy      # cm^4
8356.0
>>> ss.en.HEA("HEA200").A       # cm^2
53.83
>>> ss.en.CHS("CHS168.3x5").A   # cm^2
...
>>> ss.en.UPN("UPN200").Iy      # cm^4, computed via sectionproperties
...
>>> ss.en.Angle("L100x100x10").Iy
...
"""

from __future__ import annotations

import csv
import json
import warnings
from pathlib import Path

from ._common import Section

_DATA = Path(__file__).parent / "data"
_UNITS_TABLE = "cm-based: cm, cm^2, cm^3, cm^4, kg/m (eurocodepy, LGPL-3.0)"
_UNITS_COMPUTED = "cm-based: cm, cm^2, cm^3, cm^4 (computed from dimensions via sectionproperties, MIT)"


def _load_json(name: str) -> dict:
    with open(_DATA / name, encoding="utf-8") as f:
        rows = json.load(f)
    return {row["Section"]: row for row in rows}


def _index(table: dict) -> dict:
    """Case-insensitive, dot-normalized lookup index over a Section table."""
    return {_normalize_hollow(k): v for k, v in table.items()}


def _normalize_hollow(designation: str) -> str:
    d = designation.strip().upper().replace(" ", "")
    return d.replace(".", "_")


_I_PROFILES = _load_json("en_i_profiles.json")   # IPE, HEA, HEB, HEM
_CHS = _load_json("en_chs.json")
_RHS = _load_json("en_rhs.json")
_SHS = _load_json("en_shs.json")

_I_PROFILES_IDX = _index(_I_PROFILES)
_CHS_IDX = _index(_CHS)
_RHS_IDX = _index(_RHS)
_SHS_IDX = _index(_SHS)


def _lookup_table(idx: dict, designation: str, family: str, source: str) -> Section:
    key = _normalize_hollow(designation)
    row = idx.get(key)
    if row is None:
        matches = [k for k in idx if key.split("X")[0] in k][:8]
        hint = f" Close matches: {matches}" if matches else ""
        raise KeyError(f"{designation!r} not found among EN {family} sections.{hint}")
    props = {k: v for k, v in row.items() if k != "Section"}
    return Section(designation=row["Section"], family=family, standard="EN",
                    units=_UNITS_TABLE, source="eurocodepy (LGPL-3.0)", properties=props)


def IPE(designation: str) -> Section:
    return _lookup_table(_I_PROFILES_IDX, designation, "IPE", "eurocodepy")


def HEA(designation: str) -> Section:
    return _lookup_table(_I_PROFILES_IDX, designation, "HEA", "eurocodepy")


def HEB(designation: str) -> Section:
    return _lookup_table(_I_PROFILES_IDX, designation, "HEB", "eurocodepy")


def HEM(designation: str) -> Section:
    return _lookup_table(_I_PROFILES_IDX, designation, "HEM", "eurocodepy")


def CHS(designation: str) -> Section:
    """e.g. CHS('CHS168.3x5') -- outer diameter x wall thickness, mm."""
    return _lookup_table(_CHS_IDX, designation, "CHS", "eurocodepy")


def RHS(designation: str) -> Section:
    """e.g. RHS('RHS150x100x6') -- h x b x wall thickness, mm."""
    return _lookup_table(_RHS_IDX, designation, "RHS", "eurocodepy")


def SHS(designation: str) -> Section:
    """e.g. SHS('SHS100x100x6') -- b x b x wall thickness, mm."""
    return _lookup_table(_SHS_IDX, designation, "SHS", "eurocodepy")


def available(family: str) -> list[str]:
    table = {"IPE": _I_PROFILES, "HEA": _I_PROFILES, "HEB": _I_PROFILES,
              "HEM": _I_PROFILES, "CHS": _CHS, "RHS": _RHS, "SHS": _SHS}[family.upper()]
    if family.upper() in ("IPE", "HEA", "HEB", "HEM"):
        return sorted(k for k in table if k.startswith(family.upper()))
    return sorted(table)


# --------------------------------------------------------------------------
# UPN and angles: dimensions-only table + sectionproperties computation
# --------------------------------------------------------------------------

def _read_csv(name: str) -> dict:
    with open(_DATA / name, newline="", encoding="utf-8") as f:
        return {row["designation"].upper(): row for row in csv.DictReader(f)}


_UPN_DIMS = _read_csv("upn_en10365.csv")
_ANGLE_EQ_DIMS = _read_csv("angles_equal_en10056.csv")
_ANGLE_UNEQ_DIMS = _read_csv("angles_unequal_en10056.csv")

_compute_cache: dict = {}


def _analyze(geometry, mesh_size: float):
    """Run a sectionproperties geometric + warping analysis, return section_props."""
    from sectionproperties.analysis import Section as SPSection

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        geometry.create_mesh(mesh_sizes=[mesh_size])
        sec = SPSection(geometry)
        sec.calculate_geometric_properties()
        sec.calculate_warping_properties()
    return sec.section_props


def UPN(designation: str) -> Section:
    """EN 10365 European standard channel, e.g. UPN('UPN200').

    Dimensions come from the hand-compiled convenience table (see module
    docstring); full properties (A, Ix, Iy, J, etc.) are computed from
    those dimensions via sectionproperties. Units: cm-based.
    """
    key = designation.strip().upper().replace(" ", "").replace("-", "")
    if key not in _UPN_DIMS:
        raise KeyError(f"{designation!r} not found. Available: {sorted(_UPN_DIMS)}")
    cache_key = ("UPN", key)
    if cache_key not in _compute_cache:
        row = _UPN_DIMS[key]
        h, b, tw, tf, r1 = (float(row[k]) for k in ("h_mm", "b_mm", "tw_mm", "tf_mm", "r1_mm"))
        from sectionproperties.pre.library import steel_sections as ss_lib
        geom = ss_lib.channel_section(d=h, b=b, t_f=tf, t_w=tw, r=r1, n_r=8)
        props = _analyze(geom, mesh_size=min(tw, tf) ** 2 / 2)
        computed = {
            "h": h / 10, "b": b / 10, "tw": tw / 10, "tf": tf / 10, "r1": r1 / 10,
            "m": float(row["mass_kg_m"]),
            "A": props.area / 100,
            "Iy": props.ixx_c / 1e4, "iy": props.rx_c / 10,
            "Iz": props.iyy_c / 1e4, "iz": props.ry_c / 10,
            "Wel_y": (props.zxx_plus / 1e3), "Wel_z": (props.zyy_plus / 1e3),
            "IT": props.j / 1e4,
            "cx": props.cx / 10, "cy": props.cy / 10,
        }
        _compute_cache[cache_key] = Section(
            designation=row["designation"], family="UPN", standard="EN",
            units=_UNITS_COMPUTED, source="dimensions: hand-compiled; properties: sectionproperties (MIT)",
            properties=computed)
    return _compute_cache[cache_key]


def Angle(designation: str, equal: bool | None = None) -> Section:
    """EN 10056-1 hot-rolled angle, e.g. Angle('L100x100x10') or Angle('L100x65x7').

    Accepts 'LaxAxT' (equal) or 'Lb1xb2xT' (unequal); which table to search
    is auto-detected from the two leg dimensions unless `equal` is given
    explicitly. Dimensions come from the hand-compiled convenience table;
    full properties are computed via sectionproperties. Units: cm-based.
    """
    key = designation.strip().upper().replace(" ", "")
    if key.startswith("L"):
        key = key[1:]
    parts = key.split("X")
    if len(parts) != 3:
        raise ValueError(f"Expected 'LaXbXt' (e.g. 'L100X100X10'), got {designation!r}")
    b1, b2, t = float(parts[0]), float(parts[1]), float(parts[2])
    is_equal = (equal if equal is not None else abs(b1 - b2) < 1e-6)
    full_key = "L" + "X".join(parts)

    table = _ANGLE_EQ_DIMS if is_equal else _ANGLE_UNEQ_DIMS
    if full_key not in table:
        raise KeyError(f"{designation!r} not found in {'equal' if is_equal else 'unequal'} "
                        f"angle table. Available: {sorted(table)}")
    cache_key = ("ANGLE_EQ" if is_equal else "ANGLE_UNEQ", full_key)
    if cache_key not in _compute_cache:
        row = table[full_key]
        r1 = float(row["r1_mm"])
        r2 = float(row["r2_mm"])
        from sectionproperties.pre.library import steel_sections as ss_lib
        if is_equal:
            a = float(row["a_mm"])
            geom = ss_lib.angle_section(d=a, b=a, t=t, r_r=r1, r_t=r2, n_r=8)
        else:
            geom = ss_lib.angle_section(d=b1, b=b2, t=t, r_r=r1, r_t=r2, n_r=8)
        props = _analyze(geom, mesh_size=t ** 2 / 2)
        computed = {
            "b1": b1 / 10, "b2": b2 / 10, "t": t / 10, "r1": r1 / 10, "r2": r2 / 10,
            "m": float(row["mass_kg_m"]),
            "A": props.area / 100,
            "Iy": props.ixx_c / 1e4, "iy": props.rx_c / 10,
            "Iz": props.iyy_c / 1e4, "iz": props.ry_c / 10,
            "Iu_max": props.i11_c / 1e4, "Iv_min": props.i22_c / 1e4,
            "iu": props.r11_c / 10, "iv": props.r22_c / 10,
            "IT": props.j / 1e4,
            "cx": props.cx / 10, "cy": props.cy / 10,
        }
        _compute_cache[cache_key] = Section(
            designation="L" + "x".join(parts), family="L (equal)" if is_equal else "L (unequal)",
            standard="EN", units=_UNITS_COMPUTED,
            source="dimensions: hand-compiled; properties: sectionproperties (MIT)",
            properties=computed)
    return _compute_cache[cache_key]


def available_upn() -> list[str]:
    return sorted(_UPN_DIMS)


def available_angles(equal: bool = True) -> list[str]:
    return sorted(_ANGLE_EQ_DIMS if equal else _ANGLE_UNEQ_DIMS)
