"""DuckDB read_json_auto — GraphQL introspection, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   143 KB, 108 types
  measured      2026-08-09
  run           cd corpus/07-graphql-introspection/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  PARTLY
   4 always vs sometimes                          4  YES                 PARTLY
   5 does any field change type                   4  NO                  PARTLY
   7 how many records                             2  YES                 YES
   8 three named fields to a table                2  YES                 YES
"""
import sys
import duckdb
print(f"python {sys.version.split()[0]}, duckdb {duckdb.__version__}")
con = duckdb.connect()

# 1. DESCRIBE is the tidy-looking answer that hides the type in a cell. On npm
#    that cell held 378,036 characters. Measure it here.
d = con.sql("DESCRIBE SELECT * FROM read_json_auto('../source.json')").df()
print(f"\n1. DESCRIBE: {len(d)} rows")
widest = max(len(str(t)) for t in d["column_type"])
print(f"   widest column_type cell: {widest} chars")
print(f"   total of all type cells: {sum(len(str(t)) for t in d['column_type'])} chars")
print("   npm's widest was 378,036 and hn's 2,514. This file is SMALLER than")
print("   both, on a document deeper than either — 13 levels, the corpus's")
print("   deepest. Depth is not the driver of the O(data) failure and neither")
print("   is size: keys-as-data is, and this file has none.")
print("   The type is still one opaque cell that no reader would read, which")
print("   is DuckDB's real failure here and is separate from how big it is.")

q = "SELECT unnest(data.__schema.types) AS t FROM read_json_auto('../source.json')"
n = con.sql(f"SELECT count(*) FROM ({q})").fetchone()[0]
print(f"\n7. types: {n}")

# 4. and 5. DuckDB infers ONE struct type covering all 108, so every field is
#    in the type whether or not it holds anything. Absent and null are the same
#    thing to it, which is exactly this file's trap.
print("\n4. non-null count per field of the unnested struct:")
cols = ["kind", "name", "description", "fields", "inputFields",
        "interfaces", "enumValues", "possibleTypes"]
sel = ", ".join(f"count(t.{c}) AS {c}" for c in cols)
row = con.sql(f"SELECT {sel} FROM ({q})").fetchone()
for c, v in zip(cols, row):
    print(f"     {c:16} {v:3}/108 non-null")
print("   DuckDB's struct type lists all eight as though they were always there.")
print("   They ARE always there. That is the point, and it is why the schema")
print("   cannot tell you this document holds several kinds of record.")

print("\n5. kinds present:")
k = con.sql(f"SELECT t.kind, count(*) c FROM ({q}) GROUP BY 1 ORDER BY c DESC").df()
print("   " + k.to_string(index=False).replace("\n", "\n   "))

print("\n8. three named fields:")
t3 = con.sql(f"SELECT t.kind, t.name, t.description[1:40] d FROM ({q}) LIMIT 3").df()
print("   " + t3.to_string(index=False).replace("\n", "\n   "))
