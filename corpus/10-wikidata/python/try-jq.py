"""jq (Python binding) — Wikidata entity Q30, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq (version printed at run time)
  file          ../source.json   1.4 MB, 469 claim properties, 7 keyed sites
  measured      2026-08-09
  run           cd corpus/10-wikidata/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   NO                  NO
   2 how deep does it go                          1  NO                  YES
   5 does any field change type                   5  NO                  YES
   6 are any object keys data                     5  NO                  PARTLY
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
      f"({len(str(scal))/1466078:.0%} of the file)")
print("   Every property id, language code and wiki name is in that listing")
print("   as though it were a field. The truth is a few dozen field names.")

print(f"\n2. depth: {jq.compile('[paths|length]|max').input(doc).first()}")

print(f"\n7. claim properties: "
      f"{jq.compile('.entities.Q30.claims|length').input(doc).first()}")
print(f"   labels: {jq.compile('.entities.Q30.labels|length').input(doc).first()}"
      f"   sitelinks: "
      f"{jq.compile('.entities.Q30.sitelinks|length').input(doc).first()}")

# 5. THE CORPUS'S GENUINE POLYMORPHISM, and jq reports it in one expression
#    without being told the document's shape.
print("\n5. the type of `datavalue.value`, counted across every mainsnak:")
kinds = jq.compile(
    '[.entities.Q30.claims[][]|.mainsnak.datavalue.value?|type]'
    '|group_by(.)|map({(.[0]):length})|add').input(doc).first()
print(f"     {kinds}")
print("   A field that is a string on some records and an object on others,")
print("   named in one expression with no prior knowledge of Wikidata. jq is")
print("   the only tool in the Python half that answers question 5 this")
print("   directly, and it still needed the PATH, which is question 3.")

print("\n6. the keys-as-data test, one expression per site:")
for site in [".entities", ".entities.Q30.claims", ".entities.Q30.labels"]:
    r = jq.compile(f'{site}|{{children:length,keysets:([.[]|'
                   f'if type=="object" then (keys|join(",")) else "-" end]'
                   f'|unique|length)}}').input(doc).first()
    print(f"     {site:28} {r['children']:4} children, {r['keysets']:3} key-sets")
print("   469 children sharing few key-sets is a keyed object. jq computes it")
print("   and never volunteers it.")

print("\n8. three named fields, one row per claim property:")
rows = jq.compile(
    '.entities.Q30.claims|to_entries[:3]|map({property:.key,n:(.value|length),'
    'datatype:.value[0].mainsnak.datatype})').input(doc).first()
for r in rows:
    print(f"     {r}")
