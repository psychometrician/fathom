"""ijson — Open-Meteo hourly forecast, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   12 KB, 336 hours x 5 variables, stored COLUMN-WISE
  measured      2026-08-09
  run           cd corpus/08-open-meteo/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   NO                  YES
   2 how deep does it go                          2  NO                  YES
   3 what is one record                           -  -                   CANNOT
   7 how many records                             3  NO                  PARTLY
  7a related by position, not nesting             5  NO                  PARTLY
"""
import sys
from collections import Counter
from importlib.metadata import version
import ijson
print(f"python {sys.version.split()[0]}, ijson {version('ijson')}")

prefixes, lengths, depth, maxd = Counter(), Counter(), 0, 0
with open("../source.json", "rb") as fh:
    for prefix, event, value in ijson.parse(fh):
        prefixes[prefix] += 1
        if event in ("start_map", "start_array"):
            depth += 1
            maxd = max(maxd, depth)
        elif event in ("end_map", "end_array"):
            depth -= 1
        elif prefix.endswith(".item"):
            lengths[prefix] += 1

print(f"\n1. {len(prefixes)} distinct prefixes, "
      f"{len(str(sorted(prefixes)))} chars to list them all")
print(f"2. depth: {maxd}")

print("\n7/7a. every array in the document, with its length:")
for p, n in lengths.most_common():
    print(f"     {p:32} {n}")
print("   FIVE arrays, all exactly 336, all under one parent `hourly`.")
print("   That is the structural signal that this is a table stored column-")
print("   wise, and ijson is the only Python tool here that surfaces it as a")
print("   by-product of describing rather than because it was asked.")
print("   It still does not SAY so: a reader has to notice the 336s line up.")

print("\n3. CANNOT. ijson emits events; it proposes nothing. The count that")
print("   matters — 336 — is visible above, and calling it the row count is")
print("   an inference the tool never makes.")
