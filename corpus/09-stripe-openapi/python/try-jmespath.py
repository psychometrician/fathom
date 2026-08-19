"""jmespath — Stripe OpenAPI spec, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   7.9 MB, 1,440 schemas, 416 paths, 47 keyed sites
  measured      2026-08-09
  run           cd corpus/09-stripe-openapi/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   NO                  NO
   6 are any object keys data                     3  YES                 PARTLY
   7 how many records                             2  YES                 YES
   8 three named fields to a table                4  YES                 PARTLY
"""
import json, sys
from importlib.metadata import version
import jmespath
print(f"python {sys.version.split()[0]}, jmespath {version('jmespath')}")
doc = json.load(open("../source.json"))

# 1. keys() at the root is fine; keys() one level down is the O(data) failure
#    in its rawest form — a list of 1,440 values presented as a field listing.
print(f"\n1. root keys: {jmespath.search('keys(@)', doc)}")
sk = jmespath.search("keys(components.schemas)", doc)
pk = jmespath.search("keys(paths)", doc)
print(f"   keys(components.schemas): {len(sk):,} names, "
      f"{len(str(sk)):,} chars to print")
print(f"   keys(paths):              {len(pk):,} names, "
      f"{len(str(pk)):,} chars to print")
print(f"   first three schema 'fields': {sk[:3]}")

print(f"\n7. schemas: {len(sk):,}   paths: {len(pk):,}")

print("\n6. jmespath has keys(), so it can LIST them, and nothing that says")
print("   they are data. The three names above are values — `account`,")
print("   `account_annual_revenue` — and jmespath presents them exactly as it")
print("   presents `openapi` and `info`, which are genuinely fields.")

# 8. The keyed object defeats the multiselect idiom: there is no list to
#    project over, so the values have to be pulled with values() and the keys
#    are lost in the process.
print("\n8. one row per schema — and jmespath cannot keep the key:")
vals = jmespath.search("values(components.schemas)[:3].{type: type}", doc)
print(f"     {vals}")
print("   The schema NAME is gone, because values() discards it and there is")
print("   no zip. Recovering it means keys() and values() separately and a")
print("   plain-Python zip, at which point jmespath has done nothing.")

print(f"\n   silent failure, again: components.schemas.nosuchschema -> "
      f"{jmespath.search('components.schemas.nosuchschema', doc)!r}")
print("   indistinguishable from a schema that exists and is null.")
