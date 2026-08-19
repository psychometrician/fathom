"""glom — Wikidata entity Q30, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   1.4 MB, 469 claim properties, 7 keyed sites
  measured      2026-08-09
  run           cd corpus/10-wikidata/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   1 what is in here                             -   -                   CANNOT
   6 are any object keys data                     4  YES                 PARTLY
   7 how many records                             1  YES                 YES
   8 three named fields to a table                4  YES                 YES
   9 a field missing from some records            5  YES                 YES
"""
import json, sys
from importlib.metadata import version
from glom import glom, Iter, Coalesce, T
print(f"python {sys.version.split()[0]}, glom {version('glom')}")
doc = json.load(open("../source.json"))

claims = glom(doc, "entities.Q30.claims")
print(f"\n7. claim properties: {len(claims)}")

print("\n6. T.items() turns the keys into data — after you decide they are:")
rows = glom(doc, ("entities.Q30.claims", T.items(), Iter({
    "property": lambda kv: kv[0],
    "n": lambda kv: len(kv[1]),
}).all()))
print(f"     {len(rows)} rows, first three: {rows[:3]}")
print("   glom has the operator and no opinion about when to reach for it.")

print("\n8. three named fields, one row per claim property:")
full = glom(doc, ("entities.Q30.claims", T.items(), Iter({
    "property": lambda kv: kv[0],
    "n": lambda kv: len(kv[1]),
    "datatype": lambda kv: kv[1][0]["mainsnak"].get("datatype"),
}).all()))
for r in full[:3]:
    print(f"     {r}")

# 9. `datavalue` is absent from a novalue/somevalue snak. This is the case
#    Coalesce exists for, and it is the shipped prior art for `first_present`.
print("\n9. `datavalue` is absent from novalue/somevalue snaks:")
snaks = [c["mainsnak"] for cl in claims.values() for c in cl]
kept = glom(snaks, Iter({
    "prop": "property",
    "value": Coalesce("datavalue.value", default=None),
}).all())
missing = sum(1 for r in kept if r["value"] is None)
print(f"     {len(kept):,} snaks, {missing} have no datavalue, all rows kept")
print("     Coalesce('a', 'b', default=...) is `first_present` already shipped.")
print("     design/vocabulary.md must record that before the word is built.")

print("\n1. CANNOT. No describe verb. On a document with four levels of")
print("   keys-as-data, every path you could write is a guess about the data.")
