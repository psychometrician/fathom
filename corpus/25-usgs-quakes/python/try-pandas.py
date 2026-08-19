"""pandas — USGS earthquakes, one month

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   7.4 MB, 10,885 features, depth 5
  measured      2026-08-10
  run           cd corpus/25-usgs-quakes/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             4   NO                  yes
   2 how deep                                    2   NO                  NO — says 2
   3 what is one record                          4   YES                 PARTLY
   4 always present vs sometimes                 4   NO                  PARTLY
   5 does any field change type                  6   NO                  DANGEROUS
   6 are any object keys data                    1   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          3   NO                  PARTLY
  12 flattest honest table                       2   NO                  yes
  13 needed the shape in advance?                    for 3, 8, 9, 10 — yes
  14 survives the next file unchanged?               no: Q8/Q9/Q10 name columns
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~95, of which 2 are imports

THREE RESULTS WORTH THE RUN, and two of them were wrong in the first draft:

  Q2 IS WRONG AND CONFIDENTLY SO. `json_normalize` reports the deepest dotted
  name as 2 segments. The document is 5 levels deep. Nothing warns you.

  Q5 IS A FALSE POSITIVE OF EXACTLY THE KIND THIS CORPUS RULED ON.
  `properties.alert` reads as two python types — and it is 76 strings against
  10,809 NULLS. Defect 11 and `design/axes.py` both say a null is not a type,
  and the probe reports no type change on this document at all. **Once a frame
  exists, absent and null are the same hole**, which is item 22's five-to-eight
  split reappearing on a document chosen for something else.

  Q11 RETURNED NOTHING on the first run, because the filter tested
  `dtype == object` and pandas 3 gives string columns a StringDtype. Two real
  URL columns were invisible until the test looked at values instead of dtypes.
  Corrected here; recorded because it is the process warning working.
"""
import json
from importlib.metadata import version

import pandas as pd

print(f"pandas {version('pandas')}")

RAW = "../source.json"
doc = json.load(open(RAW))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
# pandas has no opinion. `json.load` is what read the file, and it is silent on
# duplicate keys by design — the last one wins and nothing is reported.
print("\nQ0  pandas does not read JSON without being told a shape; json.load did.")
print("    duplicate keys, big ints, NaN: not reported by either. Answered CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
print("\nQ1  top-level keys:", list(doc))
norm = pd.json_normalize(doc["features"])
print(f"Q1  json_normalize gives {norm.shape[1]} columns")
print("   ", list(norm.columns))
print(f"Q2  depth: json_normalize flattened to dotted names, so the deepest name")
print(f"    has {max(c.count('.') for c in norm.columns) + 1} segments. It does not report depth itself.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print(f"\nQ3  the obvious record is a feature: {len(norm):,} rows x {norm.shape[1]} cols")
holes = norm.isna().sum().sum() / (norm.shape[0] * norm.shape[1])
print(f"Q3  {holes:.1%} of that table is NaN")
print(f"Q7  {len(doc['features']):,} features")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
present = norm.notna().sum()
always = [c for c in norm.columns if present[c] == len(norm)]
some = {c: int(present[c]) for c in norm.columns if present[c] < len(norm)}
print(f"\nQ4  always: {len(always)} columns")
print(f"Q4  sometimes: {some}")
print("    NOTE pandas cannot tell an ABSENT key from a NULL one here — both are NaN.")

# ── Q5. Does any field change type between records? ──────────────────────────
print("\nQ5  dtypes pandas inferred:")
print(norm.dtypes.value_counts().to_dict())
mixed = [c for c in norm.columns if norm[c].map(lambda v: type(v).__name__).nunique() > 1]
print(f"Q5  columns holding more than one python type: {mixed}")
for c in mixed:
    kinds = norm[c].map(lambda v: type(v).__name__).value_counts().to_dict()
    print(f"    {c}: {kinds}")
print("    THIS IS A FALSE POSITIVE, and it is the one this corpus already ruled on.")
print("    `alert` is 76 strings and 10,809 NULLS, not two types. `design/axes.py`")
print("    and defect 11 both say a null is not a type; pandas has no way to say so,")
print("    because by the time a frame exists absent and null are the same hole.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections here; every level names its fields. n/a")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
t = norm[["properties.mag", "properties.place", "properties.time"]]
print(f"\nQ8  {t.shape[0]:,} rows x {t.shape[1]} cols")
print(t.head(3).to_string())

# ── Q9. A field missing from some records, keeping those rows. ───────────────
print(f"\nQ9  properties.alert present on {int(present['properties.alert'])} of {len(norm):,}")
print(norm[["properties.place", "properties.alert"]].head(3).to_string())

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
coords = norm["geometry.coordinates"].apply(pd.Series)
coords.columns = ["lon", "lat", "depth_km"]
print(f"\nQ10 coordinates exploded to {coords.shape[0]:,} x {coords.shape[1]}")
print(coords.head(3).to_string())

# ── Q11. Find every path whose value matches something — here, a URL. ────────
# The first draft of this filtered on `dtype == object` and returned NOTHING,
# because pandas 3 gives string columns a StringDtype and only the two genuinely
# mixed columns are `object`. The test now looks at the values.
urlish = [c for c in norm.columns
          if norm[c].astype("string").str.startswith("http").fillna(False).mean() > 0.9]
print(f"\nQ11 columns whose values are URLs: {urlish}")
print("    This is a COLUMN scan, not a path scan: pandas only sees what")
print("    json_normalize already flattened, so a URL nested inside a list is invisible.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print(f"\nQ12 {norm.shape[0]:,} x {norm.shape[1]}, and what is lost:")
print("    geometry.coordinates stays a python list in one cell — a list-column,")
print("    which is the thing god's spec refuses. Everything else is scalar.")

# ── Q26. The packed strings, asked because defect 26 came from this file. ────
print("\nDEFECT 26  does pandas notice a list packed into a string?")
print(norm[["properties.types", "properties.ids", "properties.sources"]].head(2).to_string())
print("    dtype:", norm["properties.types"].dtype, "— reported as text, which it is.")
