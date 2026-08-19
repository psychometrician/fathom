"""ijson — Natural Earth country geometry

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   3.9 MB, 241 features, GeoJSON
  measured      2026-08-09
  run           cd corpus/03-natural-earth/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   1 what is in here                             2   no                  YES
   2 how deep                                    2   no                  WRONG
   5 does any field change type                  4   no                  WRONG
   7 how many records                            1   no                  YES

WHY THIS FILE. ijson's prefix collapses every array index to `item`, so a
3-deep and a 4-deep coordinate list produce prefixes that differ in LENGTH. This
is the one tool whose path representation could have caught the depth difference
for free, and the question is whether anything looks.
"""
import sys
from collections import Counter, defaultdict
from importlib.metadata import version
import ijson

print(f"python {sys.version.split()[0]}, ijson {version('ijson')}")

names, types, prefixes = Counter(), defaultdict(Counter), Counter()
feats, deepest = 0, 0
with open("../source.json", "rb") as fh:
    for prefix, event, value in ijson.parse(fh):
        if prefix == "features.item" and event == "start_map":
            feats += 1
        if event == "map_key":
            names[value] += 1
        elif prefix and event in ("string", "number", "boolean", "null"):
            types[prefix][event] += 1
        if prefix:
            deepest = max(deepest, prefix.count(".") + 1)
            if prefix.startswith("features.item.geometry.coordinates"):
                prefixes[prefix] += 1

print(f"\n7. features: {feats}")
print(f"1. distinct key names: {len(names)}")
print(f"2. deepest prefix: {deepest}   (jq: 8, axes.py: 8)")
poly = {p: c for p, c in types.items() if len(c) > 1}
print(f"5. paths taking more than one value type: {len(poly)}")

print(f"\n   the coordinate prefixes ijson actually emitted:")
for p, c in sorted(prefixes.items(), key=lambda kv: len(kv[0])):
    print(f"     {p:<58} x{c:,}")
print("""
   THE ANSWER WAS SITTING IN THE PREFIXES. Two distinct prefix lengths for one
   field is exactly the polymorphism this file was chosen for, and it arrives
   for free in every parse. Nothing in ijson aggregates prefixes — that counter
   is four lines written by hand here — so the tool emits the evidence and
   discards it.

   design/probe.py needed `shape()` to see this. A path-shaped stream shows it
   without a type system at all, which is worth recording as a design note as
   much as a measurement.
""")
