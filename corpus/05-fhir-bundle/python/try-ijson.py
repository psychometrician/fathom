"""ijson — a Synthea FHIR bundle

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   2,024,911 bytes, 564 resources, 20 resourceTypes
  measured      2026-08-09
  run           cd corpus/05-fhir-bundle/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   1 what is in here                             2   no                  YES
   2 how deep                                    1   no                  YES
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 5   YES                 YES
   5 does any field change type                  4   no                  PARTLY
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            2   YES                 YES

WHY THIS FILE. ijson was the memory winner on `04-gharchive` at 71 MB. Here the
question is different: a streaming parser sees `resourceType` go past BEFORE the
rest of each resource, so it is the one tool whose reading order would let it
partition without a second pass. Does it?
"""
import sys
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"python {sys.version.split()[0]}, ijson {version('ijson')}")

names, types, deepest = Counter(), defaultdict(Counter), 0
per_resource, cur, kind, kinds = [], None, None, Counter()

with open("../source.json", "rb") as fh:
    for prefix, event, value in ijson.parse(fh):
        if prefix:
            deepest = max(deepest, prefix.count(".") + 1)
        if prefix == "entry.item.resource" and event == "start_map":
            if cur is not None:
                per_resource.append(cur)
            cur = set()
        elif prefix == "entry.item.resource" and event == "map_key":
            cur.add(value)
        if prefix == "entry.item.resource.resourceType":
            kinds[value] += 1
        if event == "map_key":
            names[value] += 1
        elif prefix and event in ("string", "number", "boolean", "null"):
            types[prefix][event] += 1
if cur:
    per_resource.append(cur)

print(f"\n7. resources: {len(per_resource)}")
print(f"1. distinct key names anywhere: {len(names)}")
print(f"2. deepest prefix: {deepest}   (axes.py grades 11)")

always = set.intersection(*per_resource)
union = set().union(*per_resource)
print(f"\n4. {len(always)} keys on every resource ({', '.join(sorted(always))}), "
      f"{len(union)} in the union")
shapes = len({frozenset(r) for r in per_resource})
print(f"   {shapes} distinct key-sets across {len(per_resource)} resources")

print(f"\n3. ijson READ `resourceType` on every resource as it went, and counted:")
for k, v in kinds.most_common(5):
    print(f"     {k:<24} {v:>4}")
print(f"     ... {len(kinds) - 5} more, {len(kinds)} kinds in total")
print("   this cost nothing extra — the value streamed past anyway. What it did")
print("   NOT do is connect the 20 kinds to the 42 key-sets, because that needs")
print("   both facts held at once and the whole point of streaming is not to.")

poly = {p: c for p, c in types.items() if len(c) > 1}
print(f"\n5. paths taking more than one value type: {len(poly)}")
print("   and NOT `category`, which is an array of strings on")
print("   AllergyIntolerance and of objects elsewhere. ijson records the event")
print("   type of scalars at a path; an array is not a scalar, so array-of-X")
print("   versus array-of-Y is invisible here for the same reason it is")
print("   invisible to jq and to design/probe.py's shape(). DuckDB, which has")
print("   to unify element types to build a column, is the only tool that saw it.")

print("""
6. cannot.

  The interesting near-miss is question 3. Streaming gives ijson the
  discriminator FIRST, before the fields it discriminates — `resourceType` is the
  second key of every resource — so a partitioning describer could be written as
  a single streaming pass with no more memory than this attempt used. Nothing
  ships it. The order was free and the conclusion was never drawn.
""")
