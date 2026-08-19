"""jq (Python binding) — Stripe OpenAPI spec, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq (version printed at run time)
  file          ../source.json   7.9 MB, 1,440 schemas, 416 paths, 47 keyed sites
  measured      2026-08-09
  run           cd corpus/09-stripe-openapi/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  NO
   2 how deep does it go                          1  NO                  YES
   6 are any object keys data                     6  NO                  PARTLY
   7 how many records                             2  YES                 YES
   8 three named fields to a table                4  YES                 YES
"""
import json, sys
from importlib.metadata import version
import jq
print(f"python {sys.version.split()[0]}, jq {version('jq')}")
doc = json.load(open("../source.json"))

scal = jq.compile('[paths(type != "object" and type != "array")|map(select(type=="string"))|join(".")]|unique'
                  ).input(doc).first()
print(f"\n1. paths(scalars): {len(scal):,} distinct")
print(f"   listing them costs {len(str(scal)):,} chars "
      f"({len(str(scal))/7967776:.0%} of the file)")
print("   Five implementations agreed on npm at 2,852-3,126 for a truth of")
print("   about 40 fields. This file is ten times the size and 47 keyed sites")
print("   against npm's 6, and the listing scales with the keys, not the fields.")

print(f"\n2. depth: {jq.compile('[paths|length]|max').input(doc).first()}")

print(f"\n7. schemas: {jq.compile('.components.schemas|length').input(doc).first():,}"
      f"   paths: {jq.compile('.paths|length').input(doc).first():,}")

# 6. jq is the only tool here that can express the keys-as-data TEST in one
#    line, because it can compare the key-sets of an object's children. It
#    still will not tell you unprompted.
print("\n6. the test, in one jq expression per site:")
expr = ('to_entries|{children:length,'
        'keysets:([.[]|.value|if type=="object" then (keys|join(",")) else "-" end]'
        '|unique|length)}')
for site in [".components.schemas", ".paths"]:
    r = jq.compile(f"{site}|{expr}").input(doc).first()
    print(f"     {site:22} {r['children']:5,} children, "
          f"{r['keysets']:4,} distinct key-sets")
print("   jq can compute it and has no verb that volunteers it. The whole")
print("   distance between 25,043 paths and 40 fields is this one number, and")
print("   you have to already suspect the answer to ask for it.")

print("\n8. three named fields, one row per schema — jq keeps the key:")
rows = jq.compile(
    '.components.schemas|to_entries[:3]|map({schema:.key,type:.value.type,'
    'nprops:(.value.properties//{}|length)})').input(doc).first()
for r in rows:
    print(f"     {r}")
print("   to_entries IS the keys-as-data operator, and jq is the only tool in")
print("   the Python half whose idiom for a keyed object is this direct.")
