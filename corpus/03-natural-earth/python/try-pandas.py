"""pandas — Natural Earth country geometry

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   3.9 MB, 241 features, GeoJSON
  measured      2026-08-09
  run           cd corpus/03-natural-earth/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   1 what is in here                             3   YES                 YES
   2 how deep                                    -   -                   cannot
   3 what is one record                          2   YES                 partly
   4 always present vs sometimes                 2   YES                 YES
   5 does any field change type                  3   no                  WRONG
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            1   YES                 YES

WHY THIS FILE. GeoJSON is the one corpus document with a regular, fully populated
property table, so this is where json_normalize should look best — and it does.
The interest is entirely in what happens at the `geometry` column.
"""
import json
import sys
from importlib.metadata import version

import pandas as pd

print(f"python {sys.version.split()[0]}, pandas {version('pandas')}")

doc = json.load(open("../source.json"))
df = pd.json_normalize(doc["features"])
print(f"\n1/7. json_normalize(doc['features']) -> {df.shape[0]} rows x "
      f"{df.shape[1]} cols, {df.isna().to_numpy().mean():.1%} NaN")
print("     the cleanest result any tool gets on any file in this corpus, and")
print("     the document earned it: 63 properties present on all 241 features.")

n_null = int((df.isna().sum() > 0).sum())
n_all_null = int((df.isna().sum() == len(df)).sum())
print(f"\n4. columns null on some rows: {n_null} of {df.shape[1]}, of which "
      f"{n_all_null} are null on EVERY row")
print("   This does not contradict the line above, and the distinction is one")
print("   the corpus grades as two separate axes. Every property KEY is present")
print("   on every feature — ragged by absence, 0. Some of those keys hold null")
print("   — ragged by null, 6 by the grading, plus `fips_10` which is null on")
print("   all 241 and so is not 'sometimes'. pandas shows both as NaN and has")
print("   no way to tell an absent field from a present null one.")

# 5 — the coordinates question
col = "geometry.coordinates"
print(f"\n5. dtype of {col!r}: {df[col].dtype}")
print(f"   distinct Python types in it: "
      f"{set(type(v).__name__ for v in df[col])}")
depths = pd.Series([
    (lambda f: f(f, v))(lambda s, x: 1 + s(s, x[0]) if isinstance(x, list) else 0)
    for v in df[col]
]).value_counts().to_dict()
print(f"   nesting depth per feature: {depths}")
print("   WRONG in the same way as jq: the column is `object` dtype holding")
print("   `list` for every row, and 122 of those lists nest 3 deep while 119")
print("   nest 4. pandas has one dtype for both and no vocabulary for the")
print("   difference. The depth line above is hand-written recursion.")

print("""
2, 3, 6. cannot.

  Question 3 is answered by GeoJSON rather than by pandas: `record_path` was not
  needed because `features` is obviously the array. This file is the one place
  the extraction half is genuinely easy in every tool, and it is easy because a
  specification decided what a record is before anyone opened the file.
""")
