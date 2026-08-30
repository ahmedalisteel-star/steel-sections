"""
EN / Eurocode steel shapes.

Three different data sources feed this module, matching the note in the
package docstring / README:

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

3. IPN taper-flange beams, the HE AA / HE C and IPE AA/A/O/R/V variants,
   and a batch of RHS/SHS sizes come from the DBMSC catalogue tables in
   ``data/dbmsc_catalogue.json`` (see :mod:`steel_sections.dbmsc`). These
   were added **additively**: every designation eurocodepy already
   publishes still resolves to the eurocodepy row, and a lookup only falls
   through to the catalogue when the eurocodepy table has no such size.
   ``sec.source`` always names which table answered.

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
>>> ss.en.IPN("IPN300").Iy      # cm^4, catalogue table
9800.0
>>> ss.en.IPE("IPE O 300").A    # IPE variant, catalogue table
62.8
>>> ss.en.HEAA("HEAA300").A     # cm^2, catalogue table
88.9
"""

from __future__ import annotations

import csv
import json
import warnings
from pathlib import Path

from . import dbmsc as _dbmsc
from ._common import Section, data_path

_DATA = Path(__file__).parent / "data"
_UNITS_TABLE = "cm-based: cm, cm^2, cm^3, cm^4, kg/m (eurocodepy, LGPL-3.0)"
_UNITS_COMPUTED = "cm-based: cm, cm^2, cm^3, cm^4 (computed from dimensions via sectionproperties, MIT)"


def _load_json(name: str) -> dict:
    with open(data_path(_DATA / name), encoding="utf-8") as f:
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

# --------------------------------------------------------------------------
# Catalogue fall-back: sizes the eurocodepy tables above do not carry
# --------------------------------------------------------------------------
# The DBMSC catalogue (see steel_sections.dbmsc) publishes the HE AA / HE C
# and IPE AA/A/O/R/V variants that eurocodepy's I-profile table stops short
# of, plus a batch of RHS/SHS sizes it does not list.  Those extras were
# imported *additively*: nothing that eurocodepy already provides was taken
# from the catalogue, so a designation only ever falls through to here when
# the primary table genuinely has no row for it.  Anything resolved this way
# reports ``source``/``units`` naming the catalogue, so you can always tell
# which table a number came from.
_CAT_FALLBACK = {
    "I": {_normalize_hollow(d): d for d in _dbmsc.available("HE_IPE")},
    "RHS": {_normalize_hollow(d): d for d in _dbmsc.available("RHS")},
    "SHS": {_normalize_hollow(d): d for d in _dbmsc.available("SHS")},
}


def _lookup_table(idx: dict, designation: str, family: str, source: str,
                  fallback: str | None = None) -> Section:
    key = _normalize_hollow(designation)
    row = idx.get(key)
    if row is None:
        if fallback and key in _CAT_FALLBACK[fallback]:
            cat_family = "HE_IPE" if fallback == "I" else fallback
            sec = _dbmsc.section(cat_family, _CAT_FALLBACK[fallback][key])
            return Section(designation=sec.designation, family=family,
                           standard="EN", units=sec.units, source=sec.source,
                           properties=sec.as_dict())
        matches = [k for k in idx if key.split("X")[0] in k][:8]
        if fallback:
            matches += [k for k in _CAT_FALLBACK[fallback] if key.split("X")[0] in k][:8]
        hint = f" Close matches: {matches}" if matches else ""
        raise KeyError(f"{designation!r} not found among EN {family} sections.{hint}")
    props = {k: v for k, v in row.items() if k != "Section"}
    return Section(designation=row["Section"], family=family, standard="EN",
                    units=_UNITS_TABLE, source="eurocodepy (LGPL-3.0)", properties=props)


def IPE(designation: str) -> Section:
    """e.g. IPE('IPE300'); the IPE AA/A/O/R/V variants resolve here too."""
    return _lookup_table(_I_PROFILES_IDX, designation, "IPE", "eurocodepy", "I")


def HEA(designation: str) -> Section:
    return _lookup_table(_I_PROFILES_IDX, designation, "HEA", "eurocodepy", "I")


def HEB(designation: str) -> Section:
    return _lookup_table(_I_PROFILES_IDX, designation, "HEB", "eurocodepy", "I")


def HEM(designation: str) -> Section:
    return _lookup_table(_I_PROFILES_IDX, designation, "HEM", "eurocodepy", "I")


def HEAA(designation: str) -> Section:
    """Extra-light HE series, e.g. HEAA('HEAA300') -- catalogue-sourced."""
    return _lookup_table(_I_PROFILES_IDX, designation, "HEAA", "dbmsc", "I")


def HEC(designation: str) -> Section:
    """HE C series (only HEC300 is rolled), catalogue-sourced."""
    return _lookup_table(_I_PROFILES_IDX, designation, "HEC", "dbmsc", "I")


def HE(designation: str) -> Section:
    """Any HE shape by full designation: HE('HEB300'), HE('HEAA400')."""
    return _lookup_table(_I_PROFILES_IDX, designation, "HE", "eurocodepy", "I")


def IPN(designation: str) -> Section:
    """Taper-flange I section to EN 10365 / DIN 1025-1, e.g. IPN('IPN300').

    Flange slope 14%; the catalogue publishes ``tf`` at the reference point,
    so ``d`` (depth between fillets) is the printed value rather than
    ``h - 2*tf - 2*r1``.
    """
    sec = _dbmsc.section("IPN", designation)
    return Section(designation=sec.designation, family="IPN", standard="EN",
                   units=sec.units, source=sec.source, properties=sec.as_dict())


def CHS(designation: str) -> Section:
    """e.g. CHS('CHS168.3x5') -- outer diameter x wall thickness, mm."""
    return _lookup_table(_CHS_IDX, designation, "CHS", "eurocodepy")


def RHS(designation: str) -> Section:
    """e.g. RHS('RHS150x100x6') -- h x b x wall thickness, mm."""
    return _lookup_table(_RHS_IDX, designation, "RHS", "eurocodepy", "RHS")


def SHS(designation: str) -> Section:
    """e.g. SHS('SHS100x100x6') -- b x b x wall thickness, mm."""
    return _lookup_table(_SHS_IDX, designation, "SHS", "eurocodepy", "SHS")


def available(family: str) -> list[str]:
    """Designations available in an EN family, both tables merged."""
    fam = family.upper()
    if fam == "IPN":
        return _dbmsc.available("IPN")
    _I_FAMS = ("IPE", "IPEA", "IPEAA", "IPEO", "IPER", "IPEV",
               "HE", "HEA", "HEAA", "HEB", "HEC", "HEM")
    table = dict.fromkeys(_I_FAMS, _I_PROFILES)
    table.update({"CHS": _CHS, "RHS": _RHS, "SHS": _SHS})
    table = table[fam]
    names = set(table)
    if table is _I_PROFILES:
        names |= set(_dbmsc.available("HE_IPE"))
    elif fam in ("RHS", "SHS"):
        names |= set(_dbmsc.available(fam))
    if fam == "HE":
        return sorted(n for n in names if n.startswith("HE"))
    if table is _I_PROFILES:
        # HEA must not swallow HEAA, nor IPE the IPE A/AA/O/R/V variants
        siblings = {"HEA": ("HEAA",), "IPEA": ("IPEAA",),
                    "IPE": ("IPEA", "IPEAA", "IPEO", "IPER", "IPEV")}
        drop = siblings.get(fam, ("\0",))
        return sorted(n for n in names
                      if n.startswith(fam) and not n.startswith(drop))
    return sorted(names)


# --------------------------------------------------------------------------
# UPN and angles: dimensions-only table + sectionproperties computation
# --------------------------------------------------------------------------

def _read_csv(name: str) -> dict:
    with open(data_path(_DATA / name), newline="", encoding="utf-8") as f:
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
