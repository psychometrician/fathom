"""pydash — Stripe OpenAPI spec, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   7.9 MB, 1,440 schemas, 416 paths, 47 keyed sites
  measured      2026-08-09
  run           cd corpus/09-stripe-openapi/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  NO
   2 how deep does it go                          2  NO                  YES
   6 are any object keys data                     5  NO                  PARTLY
   7 how many records                             2  YES                 YES
"""
import json, sys, resource
from importlib.metadata import version
import pydash
print(f"python {sys.version.split()[0]}, pydash {version('pydash')}")
doc = json.load(open("../source.json"))

def paths(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield f"{p}.{k}"
            yield from paths(v, f"{p}.{k}")
    elif isinstance(o, list):
        for v in o:
            yield from paths(v, p + "[]")

distinct = sorted(set(paths(doc)))
print(f"\n1. {len(distinct):,} distinct paths")
print(f"   listing them costs {len(str(distinct)):,} chars "
      f"({len(str(distinct))/7967776:.0%} of the 7,967,776-byte file)")
print("   pydash counts KEY NAMES, which on npm gave 3,126 for a truth of about")
print("   40 fields. Here the multiplier is worse, because this file has 47")
print("   keyed sites against npm's 6.")

def depth(o):
    if isinstance(o, dict) and o: return 1 + max(depth(v) for v in o.values())
    if isinstance(o, list) and o: return 1 + max(depth(v) for v in o)
    return 0
print(f"\n2. depth: {depth(doc)}")

print(f"\n7. schemas: {len(doc['components']['schemas']):,}   "
      f"paths: {len(doc['paths']):,}")

# 6. The structural signal is there for anyone who computes it, and no tool in
#    the Python half does: a parent whose children all share a key-set is a
#    keyed object rather than a record.
print("\n6. the signal, computed by hand because pydash has no verb for it:")
for site in ["components.schemas", "paths"]:
    obj = pydash.get(doc, site)
    keysets = {frozenset(v) for v in obj.values() if isinstance(v, dict)}
    print(f"     {site:20} {len(obj):5,} children, "
          f"{len(keysets):4,} distinct key-sets among them")
print("   Thousands of children sharing a handful of key-sets is what a keyed")
print("   object looks like from the outside. pydash reports neither number.")

mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
print(f"\n   peak RSS {mb:.0f} MB for a 7.6 MB file")
