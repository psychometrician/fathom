"""jmespath — Wikidata entity Q30, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   1.4 MB, 469 claim properties, 7 keyed sites
  measured      2026-08-09
  run           cd corpus/10-wikidata/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   YES                 PARTLY
   5 does any field change type                   -  -                   CANNOT
   6 are any object keys data                     3  YES                 PARTLY
   7 how many records                             2  YES                 YES
   8 three named fields to a table                4  YES                 PARTLY
"""
import json, sys
from importlib.metadata import version
import jmespath
print(f"python {sys.version.split()[0]}, jmespath {version('jmespath')}")
doc = json.load(open("../source.json"))

print(f"\n1. root keys: {jmespath.search('keys(@)', doc)}")
print(f"   keys(entities): {jmespath.search('keys(entities)', doc)}")
ek = jmespath.search("keys(entities.Q30)", doc)
print(f"   keys(entities.Q30): {ek}")
ck = jmespath.search("keys(entities.Q30.claims)", doc)
print(f"   keys(entities.Q30.claims): {len(ck)} names, {len(str(ck)):,} chars")

print(f"\n7. claim properties: {len(ck)}   "
      f"labels: {jmespath.search('length(entities.Q30.labels)', doc)}")

print("\n6. jmespath lists the keys and cannot say they are data. `Q30` is an")
print("   entity id, `P31` a property id, `en` a language — all values, all")
print("   presented exactly the way `type` and `pageid` are presented.")

print("\n8. one row per claim property — the key cannot be kept:")
v = jmespath.search("values(entities.Q30.claims)[:3][].mainsnak.datatype", doc)
print(f"     {v[:3]}")
print("   The property id is gone. values() drops it and jmespath has no zip,")
print("   so recovering it means keys() and values() and plain Python — at")
print("   which point the tool has contributed nothing to the answer.")

print("\n   silent failure, on a document made of ids you have to guess:")
print(f"     entities.Q31        -> {jmespath.search('entities.Q31', doc)!r}")
print(f"     entities.Q30.claims.P99999 -> "
      f"{jmespath.search('entities.Q30.claims.P99999', doc)!r}")
print("   Both None, no error. Every path into this file is a guess about a")
print("   value, which is the worst possible case for a tool that fails quietly.")

print("\n5. CANNOT. jmespath has no verb reporting the type of a field across")
print("   records, so the string-versus-object split in datavalue.value is")
print("   invisible.")
