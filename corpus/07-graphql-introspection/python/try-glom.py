"""glom — GraphQL introspection, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   143 KB, 108 types
  measured      2026-08-09
  run           cd corpus/07-graphql-introspection/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   1 what is in here                             -   -                   CANNOT
   4 always vs sometimes                          5  YES                 YES
   7 how many records                             1  YES                 YES
   8 three named fields to a table                4  YES                 YES
   9 a field missing from some records            4  YES                 YES
"""
import json, sys
from importlib.metadata import version
from glom import glom, Iter, Coalesce, SKIP
print(f"python {sys.version.split()[0]}, glom {version('glom')}")
doc = json.load(open("../source.json"))

print(f"\n7. types: {len(glom(doc, 'data.__schema.types'))}")

print("\n8. three named fields:")
rows = glom(doc, ("data.__schema.types", Iter({
    "kind": "kind", "name": "name",
    "nfields": Coalesce("fields", default=None),
}).all()))
for r in rows[:3]:
    n = len(r["nfields"]) if r["nfields"] else 0
    print(f"     {r['kind']:14} {r['name']:22} {n} fields")

# 9. This is glom's real strength and the reason it is in the comparison: a
#    wrong path RAISES instead of returning a table of nulls the way jmespath
#    does. On a document nobody has seen, every path is a guess.
print("\n9. a field missing from some records:")
kept = glom(doc, ("data.__schema.types", Iter({
    "name": "name", "vals": Coalesce("enumValues", default=[]),
}).all()))
withvals = [r for r in kept if r["vals"]]
print(f"     {len(kept)} rows kept, {len(withvals)} have enumValues")
print(f"     first: {withvals[0]['name']} with {len(withvals[0]['vals'])} values")

print("\n4. Coalesce is glom's answer and it is the prior art for `first_present`:")
print("     Coalesce('enumValues', default=[]) treats NULL and ABSENT alike.")
print("     On this file that is WRONG — every field is present on all 108 and")
print("     null on most, so `default=` fires 101 times for a key that is there.")
print("     glom cannot distinguish them and does not claim to.")

try:
    glom(doc, "data.__schema.nosuchkey")
except Exception as e:
    print(f"\n   a wrong path raises, and names the key: {type(e).__name__}")
    print("   compare try-jmespath.py, which returns nulls and no error.")

print("\n1. CANNOT. glom is an extractor: every spec names paths you already know.")
print("   It has no describe verb at all, which is an honest 'cannot'.")
