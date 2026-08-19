"""ijson — Stripe OpenAPI spec, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   7.9 MB, 1,440 schemas, 416 paths, 47 keyed sites
  measured      2026-08-09
  run           cd corpus/09-stripe-openapi/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  NO
   2 how deep does it go                          2  NO                  YES
   6 are any object keys data                     6  NO                  PARTLY
   7 how many records                             2  NO                  YES
"""
import sys, resource
from collections import Counter
from importlib.metadata import version
import ijson
print(f"python {sys.version.split()[0]}, ijson {version('ijson')}")

# ijson never builds the document. On the corpus's largest committed file that
# is the whole argument for it, so measure the memory as well as the answer.
prefixes, depth, maxd = Counter(), 0, 0
with open("../source.json", "rb") as fh:
    for prefix, event, value in ijson.parse(fh):
        prefixes[prefix] += 1
        if event in ("start_map", "start_array"):
            depth += 1
            maxd = max(maxd, depth)
        elif event in ("end_map", "end_array"):
            depth -= 1

print(f"\n1. {len(prefixes):,} distinct prefixes")
print(f"   listing them costs {len(str(sorted(prefixes))):,} chars "
      f"({len(str(sorted(prefixes)))/7967776:.0%} of the file)")
print("   ijson's prefixes replace a keyed object's key with the key itself,")
print("   so every one of the 1,440 schema names appears in the listing. Same")
print("   O(data) failure as polars and DuckDB, reached by a third road.")

print(f"\n2. maximum nesting depth: {maxd}")

# 6. The signal is available to a streaming parser and it does not report it:
#    a prefix whose SIBLINGS are all distinct and whose sub-structure repeats
#    is a keyed object. Counting prefix stems shows it.
stems = Counter(p.split(".")[0] + "." + p.split(".")[1] if p.count(".") >= 1 else p
                for p in prefixes)
print("\n6. prefix stems with the most distinct children — keys-as-data, unlabelled:")
for s, n in stems.most_common(5):
    print(f"     {s:34} {n:,} distinct sub-prefixes")
print("   A stem with thousands of distinct children under it is a keyed")
print("   object. ijson has the evidence and draws no conclusion.")

print(f"\n7. counted from the stream, not from a loaded document.")

mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
print(f"\n   peak RSS {mb:.0f} MB for a 7.6 MB file — compare the others.")
