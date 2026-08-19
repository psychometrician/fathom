"""ijson — Wikidata entity Q30, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   1.4 MB, 469 claim properties, 7 keyed sites
  measured      2026-08-09
  run           cd corpus/10-wikidata/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  NO
   2 how deep does it go                          2  NO                  YES
   5 does any field change type                   5  NO                  YES
   6 are any object keys data                     5  NO                  PARTLY
   7 how many records                             2  NO                  YES
"""
import sys, resource
from collections import Counter
from importlib.metadata import version
import ijson
print(f"python {sys.version.split()[0]}, ijson {version('ijson')}")

prefixes, depth, maxd = Counter(), 0, 0
valuetypes = Counter()
with open("../source.json", "rb") as fh:
    for prefix, event, value in ijson.parse(fh):
        prefixes[prefix] += 1
        if event in ("start_map", "start_array"):
            depth += 1
            maxd = max(maxd, depth)
        elif event in ("end_map", "end_array"):
            depth -= 1
        # 5. A streaming parser sees the TYPE of every value as an event, so
        #    polymorphism is free if you know which prefix to watch.
        if prefix.endswith("datavalue.value"):
            valuetypes[event] += 1

print(f"\n1. {len(prefixes):,} distinct prefixes")
print(f"   listing them costs {len(str(sorted(prefixes))):,} chars "
      f"({len(str(sorted(prefixes)))/1466078:.0%} of the file)")
print("   ijson substitutes the KEY into the prefix, so every property id and")
print("   language code appears. Same O(data) failure as pandas and polars,")
print("   arrived at from a streaming parser that never built the document.")

print(f"\n2. maximum nesting depth: {maxd}")

print(f"\n5. events at ANY prefix ending `datavalue.value`: "
      f"{ {k: v for k, v in valuetypes.items() if k in ('string', 'start_map')} }")
print("   `start_map` means an object and `string` means a scalar. The genuine")
print("   polymorphism, reported as a by-product of parsing, in one Counter.")
print("   ijson is the only Python tool here that gets question 5 for free —")
print("   and it still needed the prefix, which is question 3.")
print("   NOTE the scope: this counts mainsnak AND qualifier AND reference")
print("   snaks, so it does not match try-jq.py's 512/1,210, which is mainsnak")
print("   only. Both are right for what they asked. The prefix is doing the")
print("   scoping and nothing in the output says which scope you chose — which")
print("   is question 3 arriving disguised as a filter.")

n = sum(1 for p in prefixes if p.startswith("entities.Q30.claims.")
        and p.count(".") == 3)
print(f"\n7. distinct claim-property prefixes: {n}")
print("   which is the row count, arrived at by counting prefix segments.")

mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
print(f"\n   peak RSS {mb:.0f} MB for a 1.4 MB file — compare the others.")
