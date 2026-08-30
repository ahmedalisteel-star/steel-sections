# Catalogue extraction toolchain

These scripts produced `steel_sections/data/dbmsc_catalogue.json` and the
rows appended to the three dimension CSVs. They are kept in the repo so the
transcription is auditable and re-runnable — a hand-typed 900-row property
table is worth very little if nobody can check where the numbers came from.

## What they do

The catalogue PDF's text layer has no table structure: a page's cells come
out grouped by column band, not by row, and a third of the tables are
typeset landscape. So instead of reading the text stream, `lib.py` pulls
every word with its `(x, y)` box via PyMuPDF, buckets words into rows by
`y` (or by `x` for a rotated page), and snaps each numeric token onto a
named column by its centre coordinate. Missing cells stay missing instead
of shifting the row.

`validate.py` then checks every extracted row against identities that hold
for any rolled section — `A = m/0.785`, `A` from the rolled geometry,
`i = √(I/A)`, `Wel = I/(h/2)`, `d = h − 2t − 2r`, `Iw = Iz·(h−t)²/4` — and
resolves disagreements by consensus between the independent witnesses.
A cell recoverable by a power-of-ten shift is repaired (`REPAIR`); a cell an
identity reproduces exactly is substituted (`DERIVE`); anything else is
reported (`FLAG`) and was resolved by hand. Every correction the shipped
data carries is listed in the repo README.

## Running them

Needs `pymupdf` and a copy of the catalogue PDF, which this repo does not
redistribute. `lib.py` searches upward from itself for a file named like the
handbook; set `DBMSC_PDF` to point at yours if it lives elsewhere:

```bash
export DBMSC_PDF="/path/to/Section Table Product Catalogue.pdf"
```

`find_data_dir()` locates `data/` in either repo layout — flat (the package is
the repo root) or vendored one level deeper — so the scripts run unchanged from
a clone or from inside a bundled copy.

```bash
python ex_bs.py        # UB, UC, UBP            -> bs_raw.json
python ex_en.py        # HE / IPE variants      -> en_extra_raw.json
python ex_ipn.py       # IPN                    -> ipn_raw.json
python ex_jis.py       # JIS H shapes, channels -> jis_raw.json
python ex_chan.py      # PFC, UPN, RSC          -> chan_raw.json
python ex_ang.py       # equal / unequal angles -> ang_raw.json
python ex_hollow.py    # RHS, SHS               -> hollow_raw.json
python ex_pipe.py      # ASTM A53/A106 pipe     -> pipe_raw.json

python assemble.py     # merge -> steel_sections/data/dbmsc_catalogue.json
python append_csv.py   # append new sizes to the UPN / angle CSVs
python qa.py           # full identity sweep over the shipped file
```

`assemble.py` drops any designation the bundled eurocodepy tables already
publish, and `append_csv.py` only ever appends — both are what keeps the
import additive. `qa.py` currently reports **2931 identity checks, 0
failures**.
