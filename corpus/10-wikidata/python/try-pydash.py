"""pydash — Wikidata entity Q30, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   1.4 MB, 469 claim properties, 7 keyed sites
  measured      2026-08-09
  run           cd corpus/10-wikidata/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  NO
   2 how deep does it go                          2  NO                  YES
   5 does any field change type                   4  NO                  PARTLY
   6 are any object keys data                     5  NO                  PARTLY
   7 how many records                             2  YES                 YES
"""
import json, sys, resource
from collections import Counter
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
      f"({len(str(distinct))/1466078:.0%} of the 1,466,078-byte file)")
print("   pydash counts KEY NAMES, and this document's key names are property")
print("   ids, language codes and wiki names. The listing is a listing of the")
print("   data, which is the O(data) claim in its purest form.")

def depth(o):
    if isinstance(o, dict) and o: return 1 + max(depth(v) for v in o.values())
    if isinstance(o, list) and o: return 1 + max(depth(v) for v in o)
    return 0
print(f"\n2. depth: {depth(doc)}")

ent = pydash.get(doc, "entities.Q30")
print(f"\n7. claim properties: {len(ent['claims'])}   "
      f"labels: {len(ent['labels'])}   sitelinks: {len(ent['sitelinks'])}")

print("\n5. datavalue.value type across every mainsnak, by hand:")
vals = [pydash.get(c, "mainsnak.datavalue.value")
        for cl in ent["claims"].values() for c in cl]
print(f"     {dict(Counter(type(v).__name__ for v in vals))}")
print("   The genuine polymorphism. pydash.get() returned each value happily")
print("   and has no verb that would have told you the types differ.")

print("\n6. the keys-as-data signal, computed by hand:")
def keyset(v):
    # A claims value is a LIST of statements, not a dict. Filtering to dicts
    # reported 0 key-sets for the most keyed site in the document, which was a
    # defect in this measurement rather than in pydash.
    if isinstance(v, list):
        v = v[0] if v else {}
    return frozenset(v) if isinstance(v, dict) else frozenset()

for site in ["entities", "entities.Q30.claims", "entities.Q30.labels",
             "entities.Q30.sitelinks"]:
    obj = pydash.get(doc, site)
    ks = {keyset(v) for v in obj.values()}
    print(f"     {site:26} {len(obj):4} children, {len(ks):3} distinct key-sets")
print("   Four of the seven keyed sites, and pydash reports none of them.")

mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
print(f"\n   peak RSS {mb:.0f} MB for a 1.4 MB file")
