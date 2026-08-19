"""polars — Wikidata entity Q30, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   1.4 MB, 469 claim properties, 7 keyed sites
  measured      2026-08-09
  run           cd corpus/10-wikidata/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  NO
   5 does any field change type                   5  NO                  PARTLY
   6 are any object keys data                     3  YES                 PARTLY
   7 how many records                             2  YES                 YES
"""
import json, sys, resource
import polars as pl
print(f"python {sys.version.split()[0]}, polars {pl.__version__}")
doc = json.load(open("../source.json"))
ent = doc["entities"]["Q30"]

df = pl.DataFrame([doc])
schema = str(df.schema)
print(f"\n1. schema: {len(schema):,} chars for a 1,466,078-byte file "
      f"({len(schema)/1466078:.0%})")
print("   The inferred type contains a struct field per property id, per")
print("   language code and per wiki. polars is describing the data because")
print("   in this document the keys ARE the data, at four separate levels.")

print(f"\n7. claim properties: {len(ent['claims'])}   "
      f"labels: {len(ent['labels'])}   sitelinks: {len(ent['sitelinks'])}")

# 5. The corpus's genuine polymorphism. polars must be pointed at it, and when
#    it is, it does the thing this project already recorded as dangerous:
#    it picks one type and makes the data fit.
snaks = [c["mainsnak"] for cl in ent["claims"].values() for c in cl
         if "datavalue" in c.get("mainsnak", {})]
vals = [s["datavalue"]["value"] for s in snaks]
kinds = {}
for v in vals:
    kinds[type(v).__name__] = kinds.get(type(v).__name__, 0) + 1
print(f"\n5. datavalue.value across {len(vals):,} mainsnaks: {kinds}")
try:
    got = pl.DataFrame({"value": vals})
    print(f"   pl.DataFrame(...) gives dtype {got['value'].dtype}")
    print("   polars accepted a column that is a string in some rows and a")
    print("   struct in others by choosing one representation for all of them.")
except Exception as e:
    print(f"   pl.DataFrame(...) REFUSES: {type(e).__name__}: {str(e)[:120]}")
    print("   Same refusal as on 05-fhir-bundle, which polars cannot open at")
    print("   all. A refusal is honest; it is also the end of the attempt.")

print("\n6. no keys-as-data verb. The schema size above is the report.")

mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
print(f"\n   peak RSS {mb:.0f} MB for a 1.4 MB file")
