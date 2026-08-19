"""ijson — Chicago employee salaries, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   923 KB, 5,000 records, 8 fields, depth 2
  measured      2026-08-10
  run           cd corpus/19-chicago-salaries/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  yes
   2 how deep                                    1   NO                  yes
   3 what is one record                          -   -                   CANNOT
   4 always present vs sometimes                 4   NO                  yes
   5 does any field change type                  4   NO                  yes
   6 are any object keys data                    2   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               -   -                   CANNOT
   9 a field missing from some rows              -   -                   CANNOT
  10 flatten the deepest array                   2   -                   n/a
  11 find every path matching something          4   NO                  yes
  12 flattest honest table                       -   -                   CANNOT
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 7, 11
  14 survives the next file unchanged?               YES — nothing is named
  15 readable a week later?                          the event loop is fiddly
  16 lines, and how much is ceremony?                ~35, mostly bookkeeping
"""
import re
import sys
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"python {sys.version.split()[0]}, ijson {version('ijson')}")

prefixes, types, depths = Counter(), defaultdict(Counter), []
n_rec = 0
dept = re.compile("DEPARTMENT")
hits = Counter()

with open("../source.json", "rb") as fh:
    for prefix, event, value in ijson.parse(fh):
        if event == "start_map" and prefix == "item":
            n_rec += 1
        if event in ("start_map", "start_array", "end_map", "end_array"):
            continue
        if prefix:
            prefixes[prefix] += 1
            depths.append(prefix.count(".") + 1)
            if event != "map_key":
                types[prefix][event] += 1
        if event == "string" and dept.search(value or ""):
            hits[prefix] += 1

print(f"\n1. {len(prefixes)} distinct prefixes, listing them costs "
      f"{len(str(sorted(prefixes)))} chars "
      f"({100 * len(str(sorted(prefixes))) / 944651:.3f}% of the file)")
for p, n in prefixes.most_common():
    print(f"     {p:26} {n:>6,}")
print("   0.02% — the corpus's smallest ijson listing by a distance, against")
print("   111% on npm and 174% on Stripe. Nine prefixes for 5,000 records is")
print("   what `proportional to structure` looks like when the tool gets it")
print("   free: there are no keys-as-data and no array indices to mint.")

print(f"\n2. deepest prefix: {max(depths)} segments (+1 for the root array = 2)")
print(f"\n7. {n_rec:,} records, counted from the stream with nothing named.")

print("\n4. counts per prefix ARE the always/sometimes answer, unasked:")
for p, n in prefixes.most_common():
    print(f"     {p:26} {n:>6,} of {n_rec:,}")
print("   `item.annual_salary` 3,938 and `item.hourly_rate` 1,062 sum to 5,000.")
print("   ijson has both numbers on screen and no way to relate them.")

poly = {p: c for p, c in types.items() if len(c) > 1}
print(f"\n5. prefixes taking more than one event type: {len(poly)}")
print("   None. Every value in this document is a `string` event — including")
print("   the salaries. ijson reports the truth and the truth is the problem.")

print(f"\n11. values matching /DEPARTMENT/: {sum(hits.values()):,} at "
      f"{len(hits)} prefixes")
for p, n in hits.most_common():
    print(f"     {p:26} {n:>6,}")
print("   Found with nothing named — the streaming parser's one clear win over")
print("   every frame-shaped tool, which must enumerate `df.columns` first.")

print("\n3, 8, 9, 12. CANNOT. ijson has no record, row or table. On a flat")
print("   document that is a bigger loss than usual: the table is RIGHT THERE")
print("   and assembling it from events is a hand-written state machine.")
print("\n10, 6. n/a. No nested array, no keys that are data.")
