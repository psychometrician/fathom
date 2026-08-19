"""pandas.json_normalize — Stripe OpenAPI spec, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   7.9 MB, 1,440 schemas, 416 paths, 47 keyed sites
  measured      2026-08-09
  run           cd corpus/09-stripe-openapi/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  NO
   6 are any object keys data                     5  YES                 PARTLY
   7 how many records                             3  YES                 YES
   8 three named fields to a table                4  YES                 YES
"""
import json, sys, resource
import pandas as pd
print(f"python {sys.version.split()[0]}, pandas {pd.__version__}")
doc = json.load(open("../source.json"))

# 1. THE O(data) FAILURE AT ITS WORST. This file has the corpus's highest
#    keys-as-data count — 47 sites — and json_normalize turns every one of the
#    1,440 schema names into its own column.
flat = pd.json_normalize(doc)
cols = len(str(list(flat.columns)))
print(f"\n1. json_normalize(root): {flat.shape[0]} row x {flat.shape[1]:,} cols")
print(f"   listing the column names costs {cols:,} chars")
print(f"   the file is 7,967,776 bytes, so the description is {cols/7967776:.0%} of it")
print("   Every schema name and every URL path became a column. The truth is")
print("   about a dozen fields; the answer is tens of thousands of columns.")

print(f"\n7. schemas: {len(doc['components']['schemas']):,}")
print(f"   paths:   {len(doc['paths']):,}")
print("   Both of those are KEYED objects, so both are keys-as-data.")

# 6. pandas has no notion of this, and the shape of the wrong answer is the
#    evidence: a column count in the tens of thousands IS the keys-as-data
#    report, unlabelled.
print("\n6. pandas cannot answer this. What it does instead is turn every data")
print("   key into a column name, so the failure is visible only as size.")
print("   A sample of the columns it produced under components.schemas:")
for c in [c for c in flat.columns if c.startswith("components.schemas.")][:3]:
    print(f"     {c[:88]}")
print("   `account`, `account_annual_revenue` are SCHEMA NAMES — values wearing")
print("   column names. This is the highest O(data) figure the corpus has:")
print("   npm measured 60% (polars) and 61% (tidyjson); this is 77%.")

print("\n8. one row per schema, the answer NOTES.md records:")
df = pd.DataFrame([
    {"schema": k, "type": v.get("type"), "nprops": len(v.get("properties", {}))}
    for k, v in doc["components"]["schemas"].items()])
print(f"   {df.shape[0]:,} rows x {df.shape[1]} cols")
print("   " + df.head(3).to_string(index=False).replace("\n", "\n   "))
print("   Built with a dict comprehension, not with pandas: json_normalize has")
print("   no way to say 'the keys are the rows'.")

mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
print(f"\n   peak RSS {mb:.0f} MB for a 7.6 MB file")
