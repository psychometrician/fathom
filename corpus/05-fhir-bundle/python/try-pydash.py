"""pydash — a Synthea FHIR bundle

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   2,024,911 bytes, 564 resources, 20 resourceTypes
  measured      2026-08-09
  run           cd corpus/05-fhir-bundle/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   1 what is in here                             2   no                  YES
   2 how deep                                    2   no                  YES
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 4   YES                 YES
   5 does any field change type                  5   no                  YES
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            1   YES                 YES

WHY THIS FILE. pydash is the floor — a plain recursion with a fetching library
attached. It is here to show what nine lines get you on the hardest document in
the corpus, and specifically whether the naive walk sees the `category` conflict
that jq, ijson and design/probe.py all miss.
"""
import json
import sys
from collections import Counter, defaultdict
from importlib.metadata import version

import pydash

print(f"python {sys.version.split()[0]}, pydash {version('pydash')}")

doc = json.load(open("../source.json"))
res = [e["resource"] for e in doc["entry"]]

names, types, deepest = Counter(), defaultdict(set), 0

def walk(node, depth):
    global deepest
    deepest = max(deepest, depth)
    if isinstance(node, dict):
        for k, v in node.items():
            names[k] += 1
            types[k].add(type(v).__name__)
            walk(v, depth + 1)
    elif isinstance(node, list):
        for v in node:
            walk(v, depth + 1)

walk(doc, 0)

print(f"\n7. resources: {len(res)}")
print(f"1. distinct key names: {len(names)}")
print(f"2. deepest nesting: {deepest}   (jq: 11)")

per = [set(r) for r in res]
always, union = set.intersection(*per), set().union(*per)
print(f"\n4. {len(always)} keys on every resource ({', '.join(sorted(always))}), "
      f"{len(union)} in the union")

varying = {k: v for k, v in types.items() if len(v) > 1}
print(f"\n5. key names taking more than one Python type: {len(varying)}")
for k, v in sorted(varying.items()):
    print(f"     {k:<16} {', '.join(sorted(v))}")
print("   ELEVEN, against jq's THREE, and jq is right. This groups by key NAME")
print("   across the whole document, so `code` as an object on a resource and")
print("   `code` as a string inside a Coding are counted as one field varying.")
print("   Same defect as on 04-gharchive: a name is not a path. The cheap walk")
print("   over-reports exactly where the careful one under-reports.")

# ── the `category` question, asked directly ──────────────────────────────────
cat = Counter(type(r["category"][0]).__name__ for r in res
              if isinstance(r.get("category"), list) and r["category"])
print(f"\n   and `category` element types, which the walk above cannot see:")
for t, n in cat.items():
    print(f"     list of {t:<10} on {n} resources")
print("   pydash's walk records the type of the VALUE at each key. `category` is")
print("   a list either way, so it never varies. Seeing this needs the type of")
print("   the list's ELEMENTS, which is one level deeper than any of these tools")
print("   look — jq, ijson and design/probe.py all miss it identically.")

print("""
3, 6. cannot.

  Everything above is right and the file's actual difficulty is untouched: 2
  reliable fields out of 97, across 564 records that are 20 different kinds of
  thing. The numbers that say so are printed in question 4 and nothing connects
  them.
""")
