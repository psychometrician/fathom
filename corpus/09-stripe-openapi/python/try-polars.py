"""polars — Stripe OpenAPI spec, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   7.9 MB, 1,440 schemas, 416 paths, 47 keyed sites
  measured      2026-08-09
  run           cd corpus/09-stripe-openapi/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   1 what is in here                             6   NO                  NO
   6 are any object keys data                     4  YES                 PARTLY
   7 how many records                             2  YES                 YES
"""
import json, sys, resource
import polars as pl
print(f"python {sys.version.split()[0]}, polars {pl.__version__}")
doc = json.load(open("../source.json"))

# 1. polars infers a real nested schema, which is the right idea, and on the
#    corpus's most keys-as-data-heavy file it is the sharpest version of the
#    O(data) claim. On npm this was 60% of the file.
df = pl.DataFrame([doc])
schema = str(df.schema)
print(f"\n1. schema: {len(schema):,} chars for a 7,967,776-byte file "
      f"({len(schema)/7967776:.0%})")
sub = str(df.schema["components"]) if "components" in df.schema.names() else ""
print(f"   the `components` type alone: {len(sub):,} chars")
print(f"   the `paths` type alone: {len(str(df.schema['paths'])):,} chars")
print("   Every one of the 1,440 schema names and 416 URL paths is a STRUCT")
print("   FIELD in the inferred type. polars is describing the data, correctly")
print("   and uselessly, because in this document the keys ARE the data.")

print(f"\n7. schemas: {len(doc['components']['schemas']):,}   "
      f"paths: {len(doc['paths']):,}")

print("\n6. polars has no keys-as-data verb. The evidence is the schema size")
print("   above: a type that grows with the number of records is a type that")
print("   has mistaken records for fields. That is the whole claim, and this")
print("   file is where it is least deniable.")

mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
print(f"\n   peak RSS {mb:.0f} MB for a 7.6 MB file")
