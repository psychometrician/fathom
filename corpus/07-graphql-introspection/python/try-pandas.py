"""pandas.json_normalize — GraphQL introspection, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   143 KB, 108 types
  measured      2026-08-09
  run           cd corpus/07-graphql-introspection/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   1 what is in here                             3   NO                  PARTLY
   3 what is one record                           -  -                   CANNOT
   4 always vs sometimes                          4  YES                 YES
   5 does any field change type                   -  -                   CANNOT
   7 how many records                             2  YES                 YES
   8 three named fields to a table                3  YES                 YES
"""
import json, sys
import pandas as pd
print(f"python {sys.version.split()[0]}, pandas {pd.__version__}")
doc = json.load(open("../source.json"))

# 1. MEASURED, and it contradicts what this file was written expecting.
#    json_normalize(root) was predicted to blow up the way it does on npm. It
#    does not: it descends through objects and STOPS at the first array, so a
#    143 KB document is described in a few dozen characters that say nothing.
flat = pd.json_normalize(doc)
print(f"\n1. json_normalize(root): {flat.shape[0]} row x {flat.shape[1]} cols")
print(f"   the whole description: {len(str(list(flat.columns)))} chars")
print(f"   {list(flat.columns)}")
print("   NOT the O(data) failure. pandas descends objects and stops dead at the")
print("   first array, so the 108 types are one opaque cell. npm blew up because")
print("   its versions are an OBJECT; here they are a LIST and nothing expands.")
print("   The O(data) claim is about keyed documents. This is the opposite")
print("   failure and it is worse: the answer is small and empty.")

types = doc["data"]["__schema"]["types"]
print(f"\n7. types: {len(types)}")

# 4. Present-vs-absent is what pandas can see. It cannot see null-vs-absent
#    without being asked, and that distinction is this file's whole defect.
df = pd.json_normalize(types)
present = (df.notna().sum() / len(df)).sort_values(ascending=False)
print("\n4. fraction of the 108 types where each top-level field is NOT null:")
for k, v in present.items():
    if "." not in k:
        print(f"     {k:16} {v:.0%}")
print("   `fields` and `enumValues` are PRESENT on all 108 and null on most.")
print("   json_normalize reports NaN for both absent and null, so questions 4")
print("   and 5 collapse into one column and the answer to 4 is wrong.")

print("\n8. three named fields:")
three = df[["kind", "name", "description"]].head(3).copy()
three["description"] = three["description"].astype(str).str.slice(0, 40)
print(three.to_string(index=False))

print("\n3. CANNOT. pandas has no notion of a candidate row shape; it normalizes")
print("   whatever path you name. Naming the path IS answering question 3.")
print("5. CANNOT. Every mixed column arrives as dtype=object and is not reported.")
