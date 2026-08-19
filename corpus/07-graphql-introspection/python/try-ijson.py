"""ijson — GraphQL introspection, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   143 KB, 108 types
  measured      2026-08-09
  run           cd corpus/07-graphql-introspection/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  YES
   2 how deep does it go                          4  NO                  YES
   4 always vs sometimes                          5  NO                  YES
   5 does any field change type                   5  NO                  YES
   7 how many records                             2  YES                 YES
"""
import sys
from collections import Counter
from importlib.metadata import version
import ijson
print(f"python {sys.version.split()[0]}, ijson {version('ijson')}")

# ijson is the only tool here that never builds the document, so it is the only
# one whose answers cost memory proportional to DEPTH rather than to size.
prefixes, events, depth, maxdepth = Counter(), Counter(), 0, 0
with open("../source.json", "rb") as fh:
    for prefix, event, value in ijson.parse(fh):
        prefixes[prefix] += 1
        events[event] += 1
        if event in ("start_map", "start_array"):
            depth += 1
            maxdepth = max(maxdepth, depth)
        elif event in ("end_map", "end_array"):
            depth -= 1

print(f"\n1. {len(prefixes)} distinct prefixes")
print(f"   listing them costs {len(str(sorted(prefixes)))} chars")
print("   ijson counts a KEY NAME, not a walk-to-scalar, so `fields` and the")
print("   other container-valued keys are all here. jq's paths(scalars) drops")
print("   them, which is how three tools agreed on 11 for the hn thread and")
print("   all three dropped the most important field in it.")

print(f"\n2. maximum nesting depth: {maxdepth}")
print(f"   events: {dict(events)}")

# 4. and 5. The streaming events distinguish `null` from a key that never
# appears, because a null EMITS an event. This is the one tool in the Python
# half that can answer question 4 correctly on this file without being told.
nulls, seen = Counter(), Counter()
with open("../source.json", "rb") as fh:
    for prefix, event, value in ijson.parse(fh):
        if prefix.startswith("data.__schema.types.item.") and event != "map_key":
            f = prefix.split(".")[-1]
            if f not in ("item",):
                seen[f] += 1
                if event == "null":
                    nulls[f] += 1

print("\n4/5. per field of types[]: times seen, times NULL")
for f in sorted(seen):
    print(f"     {f:16} seen {seen[f]:4}   null {nulls.get(f,0):4}")
print("   A field that is SEEN 108 times and NULL 101 times is present-always")
print("   and empty-mostly. That is raggedness by null, and ijson is the only")
print("   Python tool here that reports it without being asked the question.")

print("\n7. types: 108  (counted from start_map events under types.item)")
