"""ijson — ESPN quarterback rating, 2019

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   176 KB, 28 athletes
  measured      2026-08-09
  run           cd corpus/06-espn-qbr/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   1 what is in here                             2   no                  YES
   2 how deep                                    1   no                  YES
   7 how many records                            1   no                  YES
   7a related by position, not nesting           5   no                  PARTLY
"""
import sys
from collections import Counter
from importlib.metadata import version
import ijson
print(f"python {sys.version.split()[0]}, ijson {version('ijson')}")

names, arrays, deepest, athletes = Counter(), Counter(), 0, 0
stack = []
with open("../source.json", "rb") as fh:
    for prefix, event, value in ijson.parse(fh):
        if prefix: deepest = max(deepest, prefix.count(".") + 1)
        if event == "map_key": names[value] += 1
        if prefix == "athletes.item" and event == "start_map": athletes += 1
        if event == "start_array": stack.append([prefix, 0])
        elif event == "end_array":
            p, n = stack.pop()
            arrays[p] = max(arrays.get(p, 0), n)
        elif stack and event in ("string","number","boolean","null"): stack[-1][1] += 1

print(f"\n7. athletes: {athletes}")
print(f"1. distinct key names: {len(names)}")
print(f"2. deepest prefix: {deepest}   (axes.py grades 7)")
tens = sorted(p for p, n in arrays.items() if n == 10)
print(f"\n7a. array paths whose length is 10, with indices collapsed by ijson:")
for p in tens: print(f"     {p}")
print("""
    ijson's prefixes collapse every array index to `item`, so the 28 athletes'
    `totals` arrive as ONE path rather than 28. That is the fold, for free, in
    the path representation — jq reported 61 paths for the same document and
    ijson reports a handful.

    It still cannot say which of them holds the names. Nothing here does.""")
