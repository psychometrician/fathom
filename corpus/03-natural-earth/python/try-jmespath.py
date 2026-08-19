"""jmespath — Natural Earth country geometry

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   3.9 MB, 241 features, GeoJSON
  measured      2026-08-09
  run           cd corpus/03-natural-earth/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   1 what is in here                             2   no                  PARTLY
   5 does any field change type                  3   no                  WRONG
   7 how many records                            1   YES                 YES
   8 three named fields to a table               3   YES                 YES

WHY THIS FILE. jmespath's best case: flat, regular, no recursion, and a record
declared by the format. If it looks weak here it is weak everywhere.
"""
import json, sys
from importlib.metadata import version
import jmespath

print(f"python {sys.version.split()[0]}, jmespath {version('jmespath')}")
doc = json.load(open("../source.json"))
ask = lambda e: jmespath.search(e, doc)

print(f"\n7. features: {ask('length(features)')}")
print(f"1. keys(@): {sorted(ask('keys(@)'))}; "
      f"properties has {len(ask('keys(features[0].properties)'))} keys")

rows = ask("features[].{name: properties.name, iso: properties.iso_a3, "
           "kind: geometry.type}")
nulls = sum(1 for r in rows if r["name"] is None)
print(f"\n8. three named fields: {len(rows)} rows, {nulls} with a null name")
bad = ask("features[].{name: properties.NAME}")
print(f"   the SAME expression with `properties.NAME` instead of `properties.name`:")
print(f"     {len(bad)} rows, {sum(1 for r in bad if r['name'] is None)} of them all-null")
print("   jmespath reports no error for a path that matches nothing. glom, given")
print("   the identical wrong path, raises PathAccessError and names the key.")
print("   On a document nobody has seen, every path is a guess, and a full-size")
print("   table of nulls is the most expensive possible way to be told so.")

kinds = {}
for k in ask("features[].geometry.type"):
    kinds[k] = kinds.get(k, 0) + 1
print(f"\n5. `geometry.type` values: {kinds}")
print("   jmespath has `type()` but no way to ask how deeply a list nests, so")
print("   the 3-vs-4 difference behind those two names is unreachable. It can")
print("   report that the document CALLS them different things and not that they")
print("   ARE shaped differently — which is the same answer by luck, on a format")
print("   that happens to label its own variation.")
