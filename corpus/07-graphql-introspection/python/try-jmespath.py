"""jmespath — GraphQL introspection, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   143 KB, 108 types
  measured      2026-08-09
  run           cd corpus/07-graphql-introspection/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   1 what is in here                             2   YES                 PARTLY
   4 always vs sometimes                          4  YES                 PARTLY
   7 how many records                             1  YES                 YES
   8 three named fields to a table                3  YES                 YES
"""
import json, sys
from importlib.metadata import version
import jmespath
print(f"python {sys.version.split()[0]}, jmespath {version('jmespath')}")
doc = json.load(open("../source.json"))

print("\n1. keys, one level at a time, because there is no recursive descent:")
print(f"     root: {jmespath.search('keys(@)', doc)}")
print(f"     __schema: {jmespath.search('keys(data.__schema)', doc)}")

print(f"\n7. types: {jmespath.search('length(data.__schema.types)', doc)}")

print("\n8. three named fields:")
rows = jmespath.search("data.__schema.types[:3].[kind, name, description]", doc)
for k, n, d in rows:
    print(f"     {k:14} {n:22} {str(d)[:30]}")

# 4. jmespath CAN count nulls, but only if you already know the field names,
#    and it reports null and absent identically.
print("\n4. how many of the 108 have a non-null value:")
for f in ["fields", "enumValues", "inputFields", "possibleTypes"]:
    n = jmespath.search(f"length(data.__schema.types[?{f} != null])", doc)
    print(f"     {f:16} {n:3}/108")

# THE DANGEROUS PART, and the reason this tool is in the comparison at all.
bogus = jmespath.search("data.__schema.types[*].nosuchfield", doc)
print(f"\n   a path matching NOTHING returns {bogus!r} — no error, no warning.")
allnull = jmespath.search("data.__schema.types[*].possibleTypes", doc)
print(f"   and `possibleTypes`, a REAL field, returns {allnull!r} too.")
print("   A field that exists on all 108 records and a field that exists on")
print("   none are indistinguishable from the output. On this document that")
print("   is not a corner case: it is the document's defining property.")

print("\n3. CANNOT. jmespath has no verb that proposes a row shape.")
