"""
steel_sections
===============

A single Python interface to standard structural steel section properties,
covering both **AISC** (US) and **EN / Eurocode** (European) families:

    AISC  : W, M, S, HP, C, MC, L, 2L, WT, MT, ST, Pipe, HSS (round/rect/square)
    EN    : IPE, HEA, HEB, HEM, UPN, equal & unequal angles (L), CHS, RHS, SHS
    Generic: solid round bar ("rod"), solid flat/rectangular bar,
             parametric cold-formed lipped C ("cee") and Z ("zed") sections

This package is a *composition* of existing open-source building blocks
rather than a from-scratch database -- see ``README.md`` for exactly which
files come from where, and their licenses. In short:

  * AISC properties are looked up from **steelpy** (Apache-2.0), which
    reproduces the official AISC Steel Construction Manual values.
  * EN hot-rolled I/H sections (IPE/HEA/HEB/HEM) and hollow sections
    (CHS/RHS/SHS) are looked up from data published by the **eurocodepy**
    project (LGPL-3.0).
  * EN sections that are not shipped as ready-made property tables in either
    upstream project -- UPN channels and equal/unequal angles -- are
    computed on the fly from a small hand-compiled dimension table
    (``data/upn_en10365.csv``, ``data/angles_*_en10056.csv``) using the
    **sectionproperties** (MIT) finite-element section analysis engine.
  * Cold-formed sections and rod/flat bar have no universal designation
    standard, so they are always generated parametrically from dimensions
    you supply, also via sectionproperties.

IMPORTANT -- verify before production use
------------------------------------------
The UPN and angle dimension tables (and therefore every property computed
from them) are a **hand-compiled convenience subset**, not a certified
reproduction of EN 10365 / EN 10056-1. Cold-formed / rod / flat-bar results
are *nominal gross* properties (no effective-width reduction per AISI
S100 / EN 1993-1-3). Always check final values against the mill/manufacturer
catalogue or the standard itself before using them in a stamped calculation.

Quick start
-----------
>>> import steel_sections as ss
>>> ss.aisc.W("W12X40").Ix
307.0
>>> ss.en.IPE("IPE300").Iy          # cm^4
8356.0
>>> ss.en.UPN("UPN200").A           # cm^2 (computed via sectionproperties)
32.9
>>> ss.en.Angle("L100x100x10").Iy   # cm^4
```
"""

from . import aisc
from . import en
from .generic import rod, flat_bar, cold_formed_cee, cold_formed_zed

__all__ = ["aisc", "en", "rod", "flat_bar", "cold_formed_cee", "cold_formed_zed"]
__version__ = "0.1.0"
