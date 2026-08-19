"""pydash — Natural Earth country geometry

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   3.9 MB, 241 features, GeoJSON
  measured      2026-08-09
  run           cd corpus/03-natural-earth/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   1 what is in here                             2   no                  YES
   2 how deep                                    2   no                  YES
   5 does any field change type                  3   no                  WRONG
   7 how many records                            1   YES                 YES

WHY THIS FILE. The floor: what a plain recursion sees. It is here to confirm that
the depth blind spot is not a quirk of one library but of the way every one of
these tools asks the question.
"""
import json, sys
from collections import Counter, defaultdict
from importlib.metadata import version
import pydash

print(f"python {sys.version.split()[0]}, pydash {version('pydash')}")
doc = json.load(open("../source.json"))

names, types, deepest = Counter(), defaultdict(set), 0
def walk(n, d):
    global deepest
    deepest = max(deepest, d)
    if isinstance(n, dict):
        for k, v in n.items():
            names[k] += 1; types[k].add(type(v).__name__); walk(v, d + 1)
    elif isinstance(n, list):
        for v in n: walk(v, d + 1)
walk(doc, 0)

print(f"\n7. features: {len(doc['features'])}")
print(f"1. distinct key names: {len(names)}")
print(f"2. deepest nesting: {deepest}   (jq: 8)")
print(f"\n5. key names taking more than one Python type: "
      f"{len({k: v for k, v in types.items() if len(v) > 1})}")
def dep(x): return 1 + dep(x[0]) if isinstance(x, list) else 0
c = Counter(dep(f["geometry"]["coordinates"]) for f in doc["features"])
print(f"   and `coordinates` nesting depth, counted by hand: {dict(c)}")
print("   WRONG for the same reason as jq and pandas: type() is `list` for both")
print("   3-deep and 4-deep, so the walk sees no variation. Every tool in this")
print("   comparison that asks 'what type is this value' misses it, and the one")
print("   that asks 'what type can hold all of these' — DuckDB — does not.")
