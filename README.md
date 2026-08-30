# steel_sections

A single Python interface to standard structural steel section properties,
covering **AISC** (US), **EN / Eurocode** (European), **BS** (British) and
**JIS** (Japanese) shape families, plus generic rod / flat bar / cold-formed
C & Z sections.

This is **not** a from-scratch database. It is a thin, uniform wrapper around
a few existing open-source building blocks found on GitHub, a small
hand-compiled gap-filler, and the published tables of a stockholder's steel
catalogue for the families nobody ships as open data.

| Family | Shapes | Where the numbers come from | License |
|---|---|---|---|
| AISC | W, M, S, HP, C, MC, L, 2L, WT, MT, ST, Pipe, HSS (round/rect/square) | [`evanfaler/steelpy`](https://github.com/evanfaler/steelpy) — reproduces the official AISC Steel Construction Manual, 16th Ed. tables | Apache-2.0 |
| EN | IPE, HEA, HEB, HEM, CHS, RHS, SHS | [`pcachim/eurocodepy`](https://github.com/pcachim/eurocodepy) — pre-computed Eurocode 3 section tables | LGPL-3.0 |
| EN | UPN (EN 10365), equal & unequal angles (EN 10056-1) | hand-compiled dimension table in `steel_sections/data/*.csv` (**convenience subset — verify before production use**) + properties computed geometrically | dims: this repo; engine: [`robbievanleeuwen/section-properties`](https://github.com/robbievanleeuwen/section-properties) (MIT) |
| EN | IPN, HE AA / HE C, IPE AA/A/O/R/V, extra RHS/SHS sizes | DBMSC steel catalogue tables in `steel_sections/data/dbmsc_catalogue.json` | facts from a published catalogue; see NOTICE.md |
| BS | UB, UC, UBP, PFC, RSC | same catalogue | " |
| JIS | Wide-flange H shapes, channels (JIS G 3192) | same catalogue | " |
| ASTM | A53 / A106 schedule pipe | catalogue OD/wall/mass; A, I, W, i computed exactly from the annulus | " |
| Generic | Solid rod, flat bar, cold-formed lipped C / Z | closed-form / computed geometrically from dimensions you supply | engine: `sectionproperties` (MIT) |

I looked for a single existing GitHub repo that already covered
AISC + full EN (including UPN/angles/IPN) + BS + JIS + cold-formed in one
place and didn't find one — `steelpy` is AISC-only, `eurocodepy` covers I/H
and hollow EN sections but not channels, angles, IPN or the HE/IPE variants,
the British and Japanese families have no open table at all, and cold-formed
shapes don't have a universal designation table (they're mill/project
specific). This package composes the pieces that do exist and fills the rest
from published tables rather than re-deriving everything by hand.

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

# EN (cm-based: cm, cm^2, cm^3, cm^4)
ipe = ss.en.IPE("IPE300")
print(ipe.A, ipe.Iy, ipe.Wpl_y)

hea = ss.en.HEA("HEA200")
chs = ss.en.CHS("CHS168.3x5")
rhs = ss.en.RHS("RHS150x100x6")
shs = ss.en.SHS("SHS100x100x6")

# EN families added from the catalogue -- same call style, same units
ipn  = ss.en.IPN("IPN300")                 # taper-flange I, DIN 1025-1
heaa = ss.en.HEAA("HEAA300")               # extra-light HE series
hec  = ss.en.HEC("HEC300")
ipeo = ss.en.IPE("IPE O 300")              # IPE AA/A/O/R/V resolve through IPE()

# EN UPN / angles -- convenience-subset dimensions, computed via FE analysis
upn = ss.en.UPN("UPN200")
print(upn.A, upn.Iy, upn.Iz)

ang  = ss.en.Angle("L100x100x10")          # equal leg
ang2 = ss.en.Angle("L100x65x7")            # unequal leg, auto-detected

# British families (BS 4-1 serial size, EN 10365 dimensions)
ub  = ss.bs.UB("457x191x67")               # prefix and spaces optional
uc  = ss.bs.UC("203x203x60")
ubp = ss.bs.UBP("305x305x149")
pfc = ss.bs.PFC("430x100x64")
rsc = ss.bs.RSC("305x102")
print(ub.A, ub.Iy, ub.Wpl_y)               # 85.5 cm^2, 29380 cm^4, 1471 cm^3

# Japanese families (JIS G 3192)
h = ss.jis.H("H300x300x10x15")             # keyed by full rolled size
c = ss.jis.C("C200x80x7.5")

# ASTM A53/A106 schedule pipe
p = ss.dbmsc.Pipe("PIPE6-168.3x7.11")
print(p.D, p.t, p.m, p.A, p.I, p.schedule)
print([s.designation for s in ss.dbmsc.find_pipe("6", schedule=40)])

# Generic
bar  = ss.rod(diameter=20)                 # mm in -> mm^2, mm^4 out
flat = ss.flat_bar(width=100, thickness=10)
c_section = ss.cold_formed_cee(d=150, b=50, lip=15, t=1.5)
z_section = ss.cold_formed_zed(d=200, b_left=65, b_right=65, lip=20, t=2.0)

# Every Section object supports .as_dict(), and knows its own units/source:
print(upn.units, upn.source)
print(ub.as_dict())

# What's available
ss.en.available("IPE"); ss.en.available("IPN"); ss.en.available("RHS")
ss.bs.available_ub(); ss.jis.available_h()
ss.dbmsc.families(); ss.dbmsc.available("UC")
```

Every lookup returns a `steel_sections._common.Section` object: attribute
access (`sec.Ix`), dict-style access (`sec["Ix"]`), `.as_dict()`, and
`.units` / `.source` so you always know where a number came from and what
unit system it's in.

## Where a catalogue number comes from, and where it doesn't

The catalogue-sourced data was added **additively**. Nothing that `steelpy`
or `eurocodepy` already publishes was replaced or edited:

* `en_i_profiles.json`, `en_rhs.json`, `en_shs.json`, `en_chs.json` are
  untouched. A designation only falls through to the catalogue table when
  the eurocodepy table has no row for it — 97 HE/IPE variants, 169 RHS
  sizes and 51 SHS sizes. `sec.source` names which table answered.
* `upn_en10365.csv` and the two angle CSVs kept every row they had; the
  catalogue's additional sizes were appended (UPN 18 → 28 rows, equal
  angles 37 → 71, unequal angles 18 → 49). Root and toe radii for the new
  angle rows follow EN 10056-1, taken from the rows already in the table
  for the same leg width.
* Everything else — UB, UC, UBP, PFC, RSC, IPN, JIS H, JIS channels,
  equal/unequal angle *properties*, schedule pipe — is a family neither
  upstream project shipped at all.

**Units.** The catalogue prints dimensions in mm and its warping constant in
three different units depending on the family. Both are converted on import to
the convention `steel_sections.en` already used — **cm-based throughout**, so
`en.IPN("IPN300").h` is `30.0` exactly like `en.IPE("IPE300").h`, and `Iw` is
cm⁶ for every family. Only the detailing dimensions (`SS`, `emax`, `emin`) and
surface areas stay as printed; `meta["units"]` in the data file lists them.

932 catalogue sections in total:

| UB | UC | UBP | HE/IPE | IPN | PFC | UPN | RSC | JIS H | JIS C | L eq | L uneq | RHS | SHS | Pipe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 80 | 31 | 17 | 97 | 21 | 16 | 26 | 17 | 80 | 20 | 61 | 42 | 169 | 51 | 204 |

## Accuracy / verification status

* **AISC** and **EN IPE/HEA/HEB/HEM/CHS/RHS/SHS**: sourced from tables
  published by actively-maintained open-source projects that reproduce the
  official Manual/Eurocode values. Spot-checked here against known
  reference values (e.g. HEA100 A=21.24 cm², IPE300 Iy≈8356 cm⁴,
  W12X40 Ix=307 in⁴) and matched.
* **EN UPN and angle *dimensions***: hand-compiled from manufacturer
  datasheets and **not** independently certified against EN 10365 /
  EN 10056-1. Root/toe fillet radii in particular carry the most
  uncertainty for the less common sizes. Treat these as a first-pass
  convenience subset and verify against the standard or a mill certificate
  before using them in a stamped calculation.
* **Catalogue families** (UB/UC/UBP/PFC/RSC/IPN/JIS/HE-IPE variants/extra
  RHS-SHS/angle properties/pipe): these are the catalogue's own published
  figures, transcribed from its PDF by coordinate-based table extraction,
  not re-derived. The printed tables contain a handful of cells with a
  dropped or misplaced decimal point (an area printed as `904` for 90.4, a
  warping constant as `644` for 64.4, a wall thickness as `16.0` for 6.0).
  Each was found and corrected against an independent identity —
  `A = m/0.785`, `i = √(I/A)`, `Wel = I/(h/2)`, the rolled-section gross
  area from the dimensions, and for pipe the lb/ft column — and the
  corrections are listed per family in the extraction notes below. The
  shipped file passes **2931 identity checks with zero failures**, but it
  has **not** been certified against EN 10365 / EN 10056-1 / JIS G 3192 /
  ASTM A6. Same rule as the UPN/angle tables: fine to size and compare
  with, verify before it carries a signature.
* **PFC major-axis Iy** is the one reconstructed quantity: the catalogue
  page carrying that column is over-printed and unreadable on every row, so
  `Iy` is rebuilt from the two published values that pin it down
  (`iy²·A` and `Wel_y·h/2`), which agree to better than 1% on every size.
* **Schedule pipe** A, I, Wel, Wpl, i and IT are computed exactly from the
  annulus — there is nothing to approximate for a circular tube. Only OD,
  wall, mass and schedule number are transcribed.
* **Cold-formed C/Z and rod/flat bar**: purely geometric ("nominal gross")
  properties computed from the dimensions you provide. These are **not**
  effective-width-reduced properties per AISI S100 / EN 1993-1-3 — that's a
  separate local-buckling calculation this package does not perform.

### Corrections applied during extraction

| Family | Section | Cell | Printed | Used | Justified by |
|---|---|---|---|---|---|
| UB | 1016x305x487 | H | 644 | 64.4 | `Iz·(h−t)²/4` |
| UB | 533x210x109 | d | 4755 | 476.5 | `h − 2t − 2r` |
| UB | 356x127x39 | Wpl_z | 891 | 89.1 | ratio to `Wel_z` |
| UB | 305x102x33 | Wel_y | 4.16 | 416 | `Iy/(h/2)` |
| UC | 356x406x634 | iy | 184 | 18.4 | `√(Iy/A)` |
| UC | 203x203x71 | A | 904 | 90.4 | gross area, `m/0.785`, `Iy/iy²` |
| UBP | 305x305x223 | Wel_z | 107 | 1080 | `Iz/(b/2)` |
| UBP | 305x305x79 | d/s | 224 | 22.4 | `d/s` |
| HE/IPE | HE600x137 | Wel_y | 2529 | 3530 | `Iy/(h/2)` |
| HE/IPE | IPE R 160 / R 180 | h | 177 / 200 | 162 / 183 | `2·Iy/Wel_y`, gross area |
| HE/IPE | IPE R 220 | m | 26.2 | 31.6 | `0.785·A`, `A` confirmed by `Iy/iy²` |
| IPN | IPN100, IPN120 | d | 757, 924 | 75.7, 92.4 | `d < h` |
| IPN | IPN140 | Wpl_y | 954 | 95.4 | ratio to `Wel_y` |
| IPN | IPN500 | iy | 195 | 19.6 | `√(Iy/A)` |
| PFC | 180x90x26, 100x50x10 | Wpl_z | 835, 175 | 83.5, 17.5 | ratio to `Wel_z` |
| PFC | 125x65x15 | Wel_y | 773 | 77.3 | `Iy/(h/2)` |
| PFC | 100x50x10 | iz | 158 | 1.58 | `√(Iz/A)` |
| RSC | 305x89 | d | 254.4 | 245.8 | `d/t` ratio column |
| JIS H | 148x100x6x9, 150x150x7x10 | Iy | 1.020, 1.640 | 1020, 1640 | `iy²·A` and `Wel_y·h/2` |
| JIS H | 248x124x5x8 | Wel_z | 411 | 41.1 | `Iz/(b/2)` |
| JIS H | 386x299x9x14 | iz | 7.81 | 7.21 | `√(Iz/A)` |
| JIS H | 612x202x13x23 | A | 107.7 | 170.7 | gross area, `m/0.785`, `Iy/iy²` |
| JIS C | 300x90x9, 300x90x10 | iy, iz | 115, 259 | 11.5, 2.59 | `√(I/A)` |
| L | 100x100x6 | iy | 107 | 3.07 | `√(Iy/A)` |
| L | 150x100x12 | Wel_y | 642 | 64.3 | `Iy/(a − cx)` |
| RHS | 5 sizes | m, A, Wel_z, iz | see extraction log | ×10±1 | `0.785·A`, `√(I/A)`, `I/(h/2)` |
| RHS | 400x120x16 (1st row) | t | 16.0 | 6.0 | wall implied by `A` |
| Pipe | 6" × 4.78 | m | 29.27 | 19.23 | lb/ft column |

The scripts that produced the catalogue data live in
`tools/catalogue_extraction/` — coordinate-based PDF table extraction plus
the identity checker that found the corrections above. They are re-runnable
against the source PDF if you want to audit any number.

## Running the self-check

```bash
python selfcheck.py
```

reproduces known reference values from every source family — including
UB 457x191x67 (A = 85.5 cm², Iy = 29 400 cm⁴), UC 254x254x73,
JIS H400x400x13x21 (A = 218.7 cm²), IPN300 and 6" sch-40 pipe — and asserts
that the pre-existing EN designations still resolve to the eurocodepy
tables rather than the catalogue.
