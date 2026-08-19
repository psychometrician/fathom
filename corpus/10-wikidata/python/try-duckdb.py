"""DuckDB read_json_auto — Wikidata entity Q30, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   1.4 MB, 469 claim properties, 7 keyed sites
  measured      2026-08-09
  run           cd corpus/10-wikidata/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  NO
   5 does any field change type                   4  NO                  PARTLY
   6 are any object keys data                     4  YES                 PARTLY
   7 how many records                             2  YES                 YES
"""
import sys, json, resource
import duckdb
print(f"python {sys.version.split()[0]}, duckdb {duckdb.__version__}")
con = duckdb.connect()
SRC = "read_json_auto('../source.json', maximum_object_size=100000000)"

d = con.sql(f"DESCRIBE SELECT * FROM {SRC}").df()
print(f"\n1. DESCRIBE: {len(d)} row(s) — one column, `entities`")
total = sum(len(str(t)) for t in d["column_type"])
print(f"   the whole type prints as {total:,} chars "
      f"({total/1466078:.0%} of the 1,466,078-byte file)")
print("   One tidy row. Inside that cell is a struct with a field named `Q30`,")
print("   holding a struct with 469 fields named after property ids. The")
print("   tidiest possible presentation of the least useful answer.")

doc = json.load(open("../source.json"))
ent = doc["entities"]["Q30"]
print(f"\n7. claim properties: {len(ent['claims'])}   "
      f"labels: {len(ent['labels'])}   sitelinks: {len(ent['sitelinks'])}")

# 5. MEASURED, and the result is the opposite of what was expected. DuckDB
#    does NOT reconcile the two shapes, and the reason is its OTHER failure.
for p in ["P31", "P2924"]:
    t = con.sql(f"SELECT typeof(entities.Q30.claims.{p}[1].mainsnak"
                f".datavalue.value) FROM {SRC}").fetchone()[0]
    print(f"\n5. typeof claims.{p} …datavalue.value: {t[:70]}")
print("   P31 is a STRUCT and P2924 is a VARCHAR. DuckDB never had to reconcile")
print("   the string-on-512 against the object-on-1,210, because it had already")
print("   made every property id its own FIELD, and a field gets its own type.")
print("   **The keys-as-data failure and the polymorphism failure cancel.**")
print("   The cost is that there is no field called `datavalue.value` at all —")
print("   there are 469 unrelated ones — so the question 'does this field")
print("   change type' has no subject left to ask it about.")

print("\n6. CANNOT. STRUCT inference has already decided the keys are fields.")
print("   A MAP type would have kept the question open. This is the same class")
print("   of silent decision as polars promoting Natural Earth's coordinates,")
print("   and it is invisible from the output in both cases.")

mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
print(f"\n   peak RSS {mb:.0f} MB for a 1.4 MB file")
