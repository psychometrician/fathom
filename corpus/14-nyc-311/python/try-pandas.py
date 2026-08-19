"""pandas — NYC 311 service requests, the 20,000 most recent

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   28.1 MB, 20,000 records, depth 4
  measured      2026-08-11
  run           cd corpus/14-nyc-311/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             3   NO                  yes
   2 how deep                                    2   NO                  NO — says 2
   3 what is one record                          4   NO                  PARTLY
   4 always present vs sometimes                 4   NO                  YES — exactly right
   5 does any field change type                  6   NO                  NO — 36 false positives
   6 are any object keys data                    1   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          4   NO                  PARTLY
  12 flattest honest table                       2   NO                  yes
  13 needed the shape in advance?                    NO for 1, 3, 4, 7, 12
  14 survives the next file unchanged?               Q8/Q9/Q10 name columns; rest yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~105, of which 3 are imports

**pandas GETS QUESTION 4 EXACTLY RIGHT ON THIS FILE, AND THAT IS THE FINDING.**
13 always and 36 sometimes, which is the probe's 13 and 35 with `location` split
into its two dotted children. On `25-usgs-quakes` this same code was WRONG,
because six fields were present-and-null and a frame cannot tell that from
absent. **This document contains ZERO nulls** — 0 across 20,000 records and
963,000 field occurrences — so absent and null cannot be confused, and every
tool in this directory agrees. That is item 22's split with the mechanism held
still: pandas was never bad at question 4, it was bad at nulls.

**QUESTION 5 IS THE OPPOSITE, AND IT IS THE WORST FALSE-POSITIVE COUNT IN THIS
ENTRY BY A WIDE MARGIN.** The document has no type variation whatsoever: every
scalar in it is a JSON string, and the only non-strings are the floats inside
`location.coordinates`. The naive `type(v).__name__` check reports **36 of 49
columns as holding more than one type.** All 36 are `str` against the `float`
that is `NaN`. Same code, same defect as entry 25, thirty-six times over —
because raggedness here is 35 fields deep and the holes are everywhere.

**pandas ALSO INFERS NO TYPES IT WAS NOT GIVEN**, which was not predicted.
`latitude` stays `str`, not `float64`. Socrata ships every column as text and
pandas 3's `StringDtype` believes it. duckdb does the same; polars does the
same. Not one of the three frame tools invented a type here.
"""
import json
import time
from importlib.metadata import version

import pandas as pd

print(f"pandas {version('pandas')}")

RAW = "../source.json"
t0 = time.time()
doc = json.load(open(RAW))
print(f"    json.load: {time.time() - t0:.1f}s for 28.1 MB")

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
# pandas has no opinion. `json.load` read the file and is silent on duplicate
# keys by design — the last one wins and nothing is reported.
print("\nQ0  pandas does not read JSON without being told a shape; json.load did.")
print("    duplicate keys, big ints, NaN: not reported by either. Answered CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
t0 = time.time()
norm = pd.json_normalize(doc)
print(f"\nQ1  json_normalize gives {norm.shape[1]} columns in {time.time() - t0:.1f}s")
print("   ", list(norm.columns))
print(f"Q2  depth: the deepest dotted name has "
      f"{max(c.count('.') for c in norm.columns) + 1} segments. The document is 4 deep.")
print("    json_normalize stops at the list inside `location.coordinates` and")
print("    does not report depth itself. Same failure as on 25-usgs-quakes.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
holes = norm.isna().sum().sum() / (norm.shape[0] * norm.shape[1])
print(f"\nQ3  the obvious record is a request: {len(norm):,} rows x {norm.shape[1]} cols")
print(f"Q3  {holes:.1%} of that table is NaN — the probe prices the same shape at 25%")
print("    pandas names ONE candidate because json_normalize was handed one level.")
print("    It does not enumerate alternatives or price them. PARTLY.")
print(f"Q7  {len(doc):,} records")

# ── Q4. Always present vs sometimes. THE ONE IT GETS RIGHT. ──────────────────
present = norm.notna().sum()
always = [c for c in norm.columns if present[c] == len(norm)]
some = {c: int(present[c]) for c in norm.columns if present[c] < len(norm)}
print(f"\nQ4  always: {len(always)} columns — {always}")
print(f"Q4  sometimes: {len(some)} columns, rarest five:")
for c, n in sorted(some.items(), key=lambda kv: kv[1])[:5]:
    print(f"      {c:34} {n:6,} of {len(norm):,}")
print("    THIS IS CORRECT, and on the previous corpus file it was not. There are")
print("    ZERO nulls in this document, so every NaN is a genuine absence.")

# ── Q5. Does any field change type between records? ──────────────────────────
print("\nQ5  dtypes pandas inferred:", norm.dtypes.value_counts().to_dict())
mixed = [c for c in norm.columns if norm[c].map(lambda v: type(v).__name__).nunique() > 1]
print(f"Q5  columns holding more than one python type: {len(mixed)} of {norm.shape[1]}")
print(f"    {mixed[:6]} ...")
kinds = norm[mixed[0]].map(lambda v: type(v).__name__).value_counts().to_dict()
print(f"    e.g. {mixed[0]}: {kinds}")
print("    ALL 36 ARE FALSE. The document has no type variation at all: every")
print("    scalar is a JSON string. The second 'type' is float, and it is NaN.")
print("    Same defect as entry 25's `alert`, thirty-six times, because this")
print("    document is ragged 35 fields deep.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections — Socrata ships fixed column names. n/a")
print("    Four keys DO look like machinery: the `:@computed_region_*` set.")
print("    They are fixed names too, but they break every dotted path language")
print("    in this directory. pandas is unbothered: a column name is a string.")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
t = norm[["complaint_type", "borough", "created_date"]]
print(f"\nQ8  {t.shape[0]:,} rows x {t.shape[1]} cols")
print(t.head(3).to_string())

# ── Q9. A field missing from some records, keeping those rows. ───────────────
print(f"\nQ9  closed_date present on {int(present['closed_date']):,} of {len(norm):,}")
print(norm[["unique_key", "status", "closed_date"]].head(3).to_string())
print("    The rows are kept because they were never dropped: json_normalize")
print("    unions the keys and fills the gaps. No default had to be written.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
coords = norm["location.coordinates"].dropna().apply(pd.Series)
coords.columns = ["lon", "lat"]
print(f"\nQ10 coordinates exploded to {coords.shape[0]:,} x {coords.shape[1]}")
print(coords.head(3).to_string())

# ── Q11. Find every path whose value matches something — here, a URL. ────────
urlish = {c: int(norm[c].astype("string").str.contains("http", na=False).sum())
          for c in norm.columns}
hits = {c: n for c, n in urlish.items() if n}
print(f"\nQ11 columns holding a URL anywhere in the value: {hits}")
print("    Correct — 19 of 20,000 resolution_description strings carry one, buried")
print("    in prose. But this is a COLUMN scan over an already-flat frame, not a")
print("    path scan: it works here only because nothing is nested but coordinates.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print(f"\nQ12 {norm.shape[0]:,} x {norm.shape[1]}, and what is lost:")
print("    location.coordinates stays a python list in one cell — a list-column,")
print("    which is the thing god's spec refuses. It is the ONLY one: 48 of 49")
print("    columns are scalar, so this table is one column away from honest.")
print("    rrapply's `how=\"bind\"` closes that last column and no other tool does.")
