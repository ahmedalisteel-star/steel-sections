"""
steel_sections
===============

A single Python interface to standard structural steel section properties,
covering both **AISC** (US) and **EN / Eurocode** (European) families:

    AISC  : W, M, S, HP, C, MC, L, 2L, WT, MT, ST, Pipe, HSS (round/rect/square)
    EN    : IPE (+ AA/A/O/R/V), HEA, HEAA, HEB, HEC, HEM, IPN, UPN,
            equal & unequal angles (L), CHS, RHS, SHS
    BS    : UB, UC, UBP, PFC, RSC
    JIS   : wide-flange H shapes, channels
    Other : ASTM A53/A106 schedule pipe (steel_sections.dbmsc.Pipe)
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
  * The families neither upstream project publishes at all -- British UB /
    UC / UBP / PFC / RSC, JIS H shapes and channels, IPN, the HE AA/C and
    IPE AA/A/O/R/V variants, ASTM A53/A106 schedule pipe -- plus the
    individual RHS/SHS/angle/UPN sizes they happen to miss, come from the
    published **DBMSC steel catalogue** tables bundled in
    ``data/dbmsc_catalogue.json`` (see ``steel_sections.dbmsc``). This
    addition is strictly additive: no existing table was edited or
    overridden, and ``sec.source`` always names which table answered.

IMPORTANT -- verify before production use
------------------------------------------
The UPN and angle dimension tables (and therefore every property computed
from them) are a **hand-compiled convenience subset**, not a certified
reproduction of EN 10365 / EN 10056-1. The catalogue-sourced families are
the DBMSC handbook's own published figures, transcribed from its PDF and
cross-checked against section identities, but likewise not certified
against EN 10365 / EN 10056-1 / JIS G 3192 / ASTM A6.
Cold-formed / rod / flat-bar results
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
>>> ss.bs.UB("457x191x67").Wpl_y    # cm^3
1471.0
>>> ss.jis.H("H300x300x10x15").A    # cm^2
119.8
>>> ss.en.IPN("IPN300").Iy          # cm^4
9800.0
```
"""

from . import aisc
from . import en
from . import bs
from . import jis
from . import dbmsc
from .generic import rod, flat_bar, cold_formed_cee, cold_formed_zed

__all__ = ["aisc", "en", "bs", "jis", "dbmsc",
           "rod", "flat_bar", "cold_formed_cee", "cold_formed_zed"]
__version__ = "0.2.0"
