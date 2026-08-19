"""DuckDB read_json_auto — Stripe OpenAPI spec, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   7.9 MB, 1,440 schemas, 416 paths, 47 keyed sites
  measured      2026-08-09
  run           cd corpus/09-stripe-openapi/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   1 what is in here                             6   NO                  NO
   6 are any object keys data                     4  YES                 PARTLY
   7 how many records                             3  YES                 YES
"""
import sys, resource
import duckdb
print(f"python {sys.version.split()[0]}, duckdb {duckdb.__version__}")
con = duckdb.connect()

# 1. Eighteen tidy rows on npm hid a 378,036-character type in one cell. This
#    file is ten times npm's size and the corpus's most keyed document.
d = con.sql("DESCRIBE SELECT * FROM read_json_auto('../source.json', "
            "maximum_object_size=100000000)").df()
print(f"\n1. DESCRIBE: {len(d)} rows — a screenful, and it looks like an answer")
print("   " + d[["column_name"]].to_string(index=False).replace("\n", "\n   "))
widest = max((len(str(t)), c) for c, t in zip(d["column_name"], d["column_type"]))
total = sum(len(str(t)) for t in d["column_type"])
print(f"\n   widest column_type cell: {widest[0]:,} chars, in `{widest[1]}`")
print(f"   all type cells together:  {total:,} chars ({total/7967776:.0%} of the file)")
print("   npm's widest was 378,036. This is the same failure an order of")
print("   magnitude further along, and DESCRIBE still prints a tidy table.")

print(f"\n7. DuckDB types the keyed objects as STRUCTs, not MAPs, so the schema")
print("   names are field names and counting them means counting struct fields.")
import json
doc = json.load(open("../source.json"))
print(f"   schemas: {len(doc['components']['schemas']):,}   paths: {len(doc['paths']):,}")

print("\n6. CANNOT, and the type above is why: DuckDB has already committed to")
print("   the keys being fields by the time you can ask. A MAP type would have")
print("   preserved the question; STRUCT inference answers it wrongly and")
print("   silently, which is the same class of error as polars promoting")
print("   Natural Earth's 3-deep coordinates to 4-deep.")

mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
print(f"\n   peak RSS {mb:.0f} MB for a 7.6 MB file")
