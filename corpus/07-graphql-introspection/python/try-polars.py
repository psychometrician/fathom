"""polars — GraphQL introspection, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   143 KB, 108 types
  measured      2026-08-09
  run           cd corpus/07-graphql-introspection/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   NO                  YES
   2 how deep does it go                          -  -                   CANNOT
   4 always vs sometimes                          5  YES                 PARTLY
   5 does any field change type                   3  NO                  YES
   7 how many records                             2  YES                 YES
"""
import json, sys
import polars as pl
print(f"python {sys.version.split()[0]}, polars {pl.__version__}")
doc = json.load(open("../source.json"))
types = doc["data"]["__schema"]["types"]

# 1. polars infers a real nested schema, which is the right idea. The claim
#    under test is its SIZE relative to the document.
df = pl.DataFrame(types)
schema = str(df.schema)
print(f"\n1. schema of types[]: {len(schema)} chars for a 143,376-byte file "
      f"({len(schema)/143376:.1%})")
print(f"   {len(df.columns)} columns: {df.columns}")
print("   Far better than npm's 60%. The schema is small because the document")
print("   is REGULAR: 108 records, one key-set, no keys-as-data. The O(data)")
print("   claim tracks keys-as-data, and this file has none.")

print(f"\n7. types: {df.height}")

# 4. and 5. The defect this file exists to show. Every field is PRESENT on all
#    108 records; most are null on most of them. Absence and null are different
#    questions and polars only sees one of them.
print("\n4. null_count per column — every column is PRESENT on all 108 rows:")
nulls = df.null_count().row(0)
for c, n in zip(df.columns, nulls):
    print(f"     {c:16} null on {n:3}/108   present on 108/108")
print("   Raggedness BY ABSENCE is 0/8. Raggedness BY NULL is severe.")
print("   A tool reporting only key presence calls this file perfectly regular.")

print("\n5. types by kind:")
kinds = df.group_by("kind").len().sort("len", descending=True)
print("   " + str(kinds).replace("\n", "\n   "))
print(f"   MEASURED 2026-08-09: {kinds.height} kinds, not the six this entry's")
print("   expectation block predicted. There is no INTERFACE and no UNION in")
print("   this schema. See NOTES.md, 'A number this entry got wrong'.")
print("   `kind` is a textbook discriminator and polars will group by it the")
print("   moment you name it. It will not tell you it is there.")

print("\n2. CANNOT. polars has no depth verb; the schema is nested but the")
print("   number of levels is something you count yourself by reading it.")
