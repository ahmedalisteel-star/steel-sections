# Third-party data & code notices

This package bundles / depends on data and code from the following
upstream open-source projects. Their original license text applies to
the respective files.

## steelpy (Apache License 2.0)
https://github.com/evanfaler/steelpy
Used as a runtime dependency (`pip install steelpy`) for all AISC shape
lookups in `steel_sections/aisc.py`. Not vendored into this repo.

## eurocodepy (GNU LGPL v3)
https://github.com/pcachim/eurocodepy
The following files under `steel_sections/data/` are copied, unmodified,
from eurocodepy's `src/eurocodepy/data/` directory:
  - en_i_profiles.json   (from i_profiles_euro.json)
  - en_chs.json          (from chs_profiles_euro.json)
  - en_rhs.json          (from rhs_profiles_euro.json)
  - en_shs.json          (from shs_profiles_euro.json)
These remain licensed under LGPL-3.0. Per LGPL-3.0 terms: the full
corresponding source is publicly available at the URL above, these files
are kept as separable data (not compiled/merged into proprietary code),
and you are free to replace them with a modified version and relink.
See https://www.gnu.org/licenses/lgpl-3.0.html for the full license text.

## sectionproperties (MIT License)
https://github.com/robbievanleeuwen/section-properties
Used as a runtime dependency (`pip install sectionproperties`) as the
geometric/finite-element engine for UPN, angle, cold-formed C/Z, rod and
flat-bar property computation. Not vendored into this repo.

## Hand-compiled data (this repository)
`steel_sections/data/upn_en10365.csv`,
`steel_sections/data/angles_equal_en10056.csv`,
`steel_sections/data/angles_unequal_en10056.csv`
are dimension tables compiled during this session from published
manufacturer/standard datasheets (dimensions are facts, not copyrightable
expression). See README.md's "Accuracy / verification status" section for
the associated disclaimer.

## DBMSC steel catalogue (published tables, transcribed)
`steel_sections/data/dbmsc_catalogue.json`, and the rows appended to
`steel_sections/data/upn_en10365.csv`,
`steel_sections/data/angles_equal_en10056.csv` and
`steel_sections/data/angles_unequal_en10056.csv`, are section dimensions and
properties transcribed from

  DBMSC-STEEL GROUP, *The Structural Steel Specification Handbook*
  (document DBMSC/QMP07/R6), https://www.dbmscsteel.ae

They cover the families neither steelpy nor eurocodepy publishes -- British
UB / UC / UBP / PFC / RSC, JIS G 3192 H shapes and channels, IPN, the HE AA
/ HE C and IPE AA/A/O/R/V variants, EN 10056 angle properties, ASTM
A53/A106 schedule pipe -- plus the individual RHS/SHS/angle/UPN sizes those
two projects happen to miss. Nothing already provided by an upstream table
was replaced.

These are measurements and physical properties of standard rolled products:
dimensions and section properties are facts, not copyrightable expression,
and no part of the handbook's text, layout or artwork is reproduced here.
The values are the catalogue's own and are **not** certified against
EN 10365, EN 10056-1, JIS G 3192 or ASTM A6 -- see README.md's "Accuracy /
verification status" for the checks that were applied and the corrections
that were needed.
