"""pandas.json_normalize — Wikidata entity Q30, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   1.4 MB, 469 claim properties, 7 keyed sites
  measured      2026-08-09
  run           cd corpus/10-wikidata/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  NO
   5 does any field change type                   -  -                   CANNOT
   6 are any object keys data                     4  YES                 PARTLY
   7 how many records                             3  YES                 YES
   8 three named fields to a table                4  YES                 YES
"""
import json, sys, resource
import pandas as pd
print(f"python {sys.version.split()[0]}, pandas {pd.__version__}")
doc = json.load(open("../source.json"))
ent = doc["entities"]["Q30"]

flat = pd.json_normalize(doc)
cols = len(str(list(flat.columns)))
print(f"\n1. json_normalize(root): {flat.shape[0]} row x {flat.shape[1]:,} cols")
print(f"   listing the column names costs {cols:,} chars "
      f"({cols/1466078:.0%} of the 1,466,078-byte file)")
print("   The entity id `Q30` is itself a column-name component, and so is")
print("   every property id and every language code. Four levels of")
print("   keys-as-data, all of them promoted to fields.")

print(f"\n7. claim properties: {len(ent['claims']):,}")
print(f"   labels: {len(ent['labels'])}   sitelinks: {len(ent['sitelinks'])}")
print("   Each of those is a keyed object, so each count is a row count.")

print("\n6. pandas cannot answer this, and the column names are the evidence:")
for c in [c for c in flat.columns if ".claims.P" in c][:3]:
    print(f"     {c[:88]}")
print("   `P2924`, `P31` are property ids — data — presented as field names.")

print("\n8. one row per claim property, which is the answer NOTES.md records:")
df = pd.DataFrame([{"property": k, "n": len(v),
                    "datatype": v[0]["mainsnak"].get("datatype")}
                   for k, v in ent["claims"].items()])
print(f"   {df.shape[0]} rows x {df.shape[1]} cols")
print("   " + df.head(3).to_string(index=False).replace("\n", "\n   "))
print("   Built with a dict comprehension. json_normalize cannot say")
print("   'the keys are the rows', which is this document's whole structure.")

print("\n5. CANNOT. `datavalue.value` is text on 512 snaks and an object on")
print("   1,210 — the corpus's genuine polymorphism — and every mixed column")
print("   arrives as dtype=object with nothing reported.")

mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
print(f"\n   peak RSS {mb:.0f} MB for a 1.4 MB file")
