# steel_sections

A single Python interface to standard structural steel section properties,
covering both **AISC** (US) and **EN / Eurocode** (European) shape
families, plus generic rod / flat bar / cold-formed C & Z sections.

This is **not** a from-scratch database. It is a thin, uniform wrapper
around a few existing open-source building blocks found on GitHub, plus a
small hand-compiled gap-filler for the two EN shape families that neither
upstream project ships as ready-made tables (UPN channels, angles).

| Family | Shapes | Where the numbers come from | License |
|---|---|---|---|
| AISC | W, M, S, HP, C, MC, L, 2L, WT, MT, ST, Pipe, HSS (round/rect/square) | [`evanfaler/steelpy`](https://github.com/evanfaler/steelpy) — reproduces the official AISC Steel Construction Manual, 16th Ed. tables | Apache-2.0 |
| EN | IPE, HEA, HEB, HEM, CHS, RHS, SHS | [`pcachim/eurocodepy`](https://github.com/pcachim/eurocodepy) — pre-computed Eurocode 3 section tables | LGPL-3.0 |
| EN | UPN (EN 10365), equal & unequal angles (EN 10056-1) | hand-compiled dimension table in `steel_sections/data/*.csv` (**convenience subset — verify before production use**) + properties computed geometrically | dims: this repo; engine: [`robbievanleeuwen/section-properties`](https://github.com/robbievanleeuwen/section-properties) (MIT) |
| Generic | Solid rod, flat bar, cold-formed lipped C / Z | closed-form / computed geometrically from dimensions you supply | engine: `sectionproperties` (MIT) |

I looked for a single existing GitHub repo that already covered
AISC + full EN (including UPN/angles) + cold-formed in one place and
didn't find one — `steelpy` is AISC-only, `eurocodepy` covers I/H and
hollow EN sections but not channels or angles, and cold-formed shapes
don't have a universal designation table at all (they're mill/project
specific). This package composes the pieces that do exist rather than
re-deriving everything by hand.

## Install

```bash
pip install -r requirements.txt
```

(`steelpy` and `sectionproperties` are pulled from PyPI; this repo itself
just needs to be on your `PYTHONPATH` / installed in editable mode.)

## Usage

```python
import steel_sections as ss

# AISC (imperial: in, in^2, in^3, in^4)
w = ss.aisc.W("W12X40")
print(w.A, w.Ix, w.Iy, w.rx)

hss = ss.aisc.HSS_round("HSS4X0.250")     # CHS-equivalent
angle = ss.aisc.L("L4X4X1/2")

# EN (cm-based: cm, cm^2, cm^3, cm^4) -- from eurocodepy, verified tables
ipe = ss.en.IPE("IPE300")
print(ipe.A, ipe.Iy, ipe.Wpl_y)

hea = ss.en.HEA("HEA200")
chs = ss.en.CHS("CHS168.3x5")
rhs = ss.en.RHS("RHS150x100x6")
shs = ss.en.SHS("SHS100x100x6")

# EN UPN / angles -- convenience-subset dimensions, computed via FE analysis
upn = ss.en.UPN("UPN200")
print(upn.A, upn.Iy, upn.Iz)

ang = ss.en.Angle("L100x100x10")          # equal leg
ang2 = ss.en.Angle("L100x65x7")           # unequal leg, auto-detected

# Generic
bar = ss.rod(diameter=20)                  # mm in -> mm^2, mm^4 out
flat = ss.flat_bar(width=100, thickness=10)
c_section = ss.cold_formed_cee(d=150, b=50, lip=15, t=1.5)
z_section = ss.cold_formed_zed(d=200, b_left=65, b_right=65, lip=20, t=2.0)

# Every Section object supports .as_dict(), and knows its own units/source:
print(upn.units, upn.source)
print(upn.as_dict())
```

Every lookup returns a `steel_sections._common.Section` object: attribute
access (`sec.Ix`), dict-style access (`sec["Ix"]`), `.as_dict()`, and
`.units` / `.source` so you always know where a number came from and what
unit system it's in.

## Accuracy / verification status

- **AISC** and **EN IPE/HEA/HEB/HEM/CHS/RHS/SHS**: sourced from tables
  published by actively-maintained open-source projects that reproduce
  the official Manual/Eurocode values. Spot-checked here against known
  reference values (e.g. HEA100 A=21.24 cm², IPE300 Iy≈8356 cm⁴,
  W12X40 Ix=307 in⁴) and matched.
- **EN UPN and angles**: dimensions were hand-compiled from manufacturer
  datasheets during this session and have **not** been independently
  certified against EN 10365 / EN 10056-1. Root/toe fillet radii in
  particular carry the most uncertainty for the less common sizes.
  Treat these as a first-pass convenience subset — the same caveat the
  `aisc-steel-design` skill's own `shapes.py` convenience subset carries
  — and verify against the standard or a mill certificate before using
  them in a stamped calculation.
- **Cold-formed C/Z and rod/flat bar**: purely geometric ("nominal
  gross") properties computed from the dimensions you provide. These are
  **not** effective-width-reduced properties per AISI S100 / EN
  1993-1-3 — that's a separate local-buckling calculation this package
  does not perform.

## Running the self-check

```bash
python selfcheck.py
```

reproduces a handful of known reference values from each source family
and flags anything that drifts.
