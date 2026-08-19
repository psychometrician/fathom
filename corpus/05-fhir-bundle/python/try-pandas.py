"""pandas — a Synthea FHIR bundle

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   2,024,911 bytes, 564 resources, 20 resourceTypes
  measured      2026-08-09
  run           cd corpus/05-fhir-bundle/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   0 is it sound                                 1   no                  YES
   1 what is in here                             4   no                  PARTLY
   2 how deep                                    -   -                   cannot
   3 what is one record                          5   no                  WRONG
   4 always present vs sometimes                 4   no                  YES
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            2   no                  PARTLY

WHY THIS FILE IS THE TEST. `design/probe.py` gained a fourth operation for this
document: partition on a discriminator, then fold. It turns one 97-field shape
that is 87% empty into 20 tables averaging 4% empty. **The discriminator,
`resourceType`, sits INSIDE each record**, which makes this the fairest chance a
competing tool has to find the same thing. The question this file asks of every
attempt is not "can it be made to group" — anything can — but **does anything
propose it, or even show you that you should?**
"""
import json
import sys
from importlib.metadata import version

import pandas as pd

print(f"python {sys.version.split()[0]}, pandas {version('pandas')}")

doc = json.load(open("../source.json"))

# ── 1 / 7 / 3. what json_normalize does unaided ──────────────────────────────
df = pd.json_normalize(doc["entry"])
print(f"\n1/7. json_normalize(doc['entry']) -> {df.shape[0]} rows x "
      f"{df.shape[1]} cols")
empty = df.isna().to_numpy().mean()
print(f"     {empty:.0%} of the cells are NaN")
print(f"     the probe reports the same document folded as 564 x 97 at 87% empty,")
print(f"     and json_normalize flattens further so the column count is higher.")

# ── 4. always present vs sometimes ───────────────────────────────────────────
present = df.notna().sum()
always = (present == len(df)).sum()
print(f"\n4. columns present on every row: {always} of {df.shape[1]}")
print(f"   the widest ten by absence:")
for c, n in present.nsmallest(5).items():
    print(f"     {c[:52]:<54} {n:>4} of {len(df)}")

# ── 3. the question this file is about ───────────────────────────────────────
print("\n3. what pandas offers you, unprompted, about what a row is:")
print("   nothing. It returned one table because `entry` is one array, and a")
print("   564-row frame that is mostly NaN is a normal-looking pandas object.")
print("   No warning, no dtype complaint, no hint that the rows are 20 kinds.")

col = "resource.resourceType"
kinds = df[col].nunique()
print(f"\n   once a PERSON names `{col}`:")
print(f"     {kinds} distinct values, and grouping gives:")
for k, g in sorted(df.groupby(col), key=lambda kv: -len(kv[1]))[:6]:
    sub = g.dropna(axis=1, how="all")
    print(f"       {k:<24} {len(g):>4} rows x {sub.shape[1]:>3} cols   "
          f"{sub.isna().to_numpy().mean():.0%} empty")
print(f"     ... {kinds - 6} more")
print("   which is the probe's answer, reached by being told the answer.")

print("""
2, 5, 6. cannot.

  Nothing here is a pandas defect. `json_normalize` did what it says: it
  flattened an array of objects into a frame. The observation is that the frame
  it produced is 87% empty and pandas has no vocabulary for saying so — sparsity
  is not an error, a NaN is not a complaint, and `df.info()` will report the
  column count without ever suggesting that 20 narrower frames exist.

  **The one number that would tell you is `nunique()` on a column you have to
  pick first**, and picking it is question 3.
""")
