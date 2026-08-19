"""glom — Stripe OpenAPI spec, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   7.9 MB, 1,440 schemas, 416 paths, 47 keyed sites
  measured      2026-08-09
  run           cd corpus/09-stripe-openapi/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   1 what is in here                             -   -                   CANNOT
   6 are any object keys data                     4  YES                 PARTLY
   7 how many records                             2  YES                 YES
   8 three named fields to a table                5  YES                 YES
   9 a field missing from some records            5  YES                 YES
"""
import json, sys
from importlib.metadata import version
from glom import glom, Iter, Coalesce, T
print(f"python {sys.version.split()[0]}, glom {version('glom')}")
doc = json.load(open("../source.json"))

schemas = glom(doc, "components.schemas")
print(f"\n7. schemas: {len(schemas):,}   paths: {len(glom(doc, 'paths')):,}")

# 6. glom's T.items() is the closest any Python tool comes to naming a keyed
#    object as data — it turns the keys into values. It still has to be aimed.
print("\n6. glom can TURN the keys into data, which is not the same as telling")
print("   you they are data. T.items() does it and you must decide to call it:")
named = glom(doc, ("components.schemas", T.items(), Iter({
    "schema": lambda kv: kv[0],
    "type": lambda kv: kv[1].get("type"),
}).all()))
print(f"     {len(named):,} rows, first three:")
for r in named[:3]:
    print(f"       {r}")

print("\n8. three named fields, one row per schema:")
rows = glom(doc, ("components.schemas", T.items(), Iter({
    "schema": lambda kv: kv[0],
    "type": lambda kv: kv[1].get("type"),
    "nprops": lambda kv: len(kv[1].get("properties", {})),
}).all()))
for r in rows[:3]:
    print(f"     {r}")

# 9. `description` is absent from some schemas. Coalesce keeps the row.
print("\n9. a field missing from some records, rows kept:")
desc = glom(doc, ("components.schemas", T.values(), Iter(
    Coalesce("description", default=None)).all()))
have = sum(1 for d in desc if d is not None)
print(f"     {len(desc):,} schemas, {have:,} have a description, "
      f"{len(desc)-have:,} do not")
print("     Coalesce(default=None) keeps every row, which is the behaviour")
print("     `first_present` is named after. glom shipped it first and")
print("     design/vocabulary.md must say so before the word is built.")

print("\n1. CANNOT. glom is an extractor and has no describe verb at all.")
print("   On a 7.9 MB document nobody has seen, that is the whole problem.")
