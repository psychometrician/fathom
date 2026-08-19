"""pandas.json_normalize — one Hacker News comment thread

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time), json_normalize
  file          ../source.json   193 KB, 336 nodes, 13 levels of recursion
  measured      2026-08-09
  run           cd corpus/02-hn-thread/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   1 what is in here                             3   no                  WRONG
   2 how deep                                    -   -                   cannot
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 -   -                   cannot
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            2   YES                 WRONG
  10 flatten the deepest array                   4   YES                 partly

WHY THIS FILE EXISTS. `json_normalize` has a `max_level` argument and a
`record_path` argument, and neither can express "this record contains itself".
This is the file that shows what a flattener does with recursion when nobody
tells it the depth.
"""
import json
import sys
from importlib.metadata import version

import pandas as pd

print(f"python {sys.version.split()[0]}, pandas {version('pandas')}")

doc = json.load(open("../source.json"))

# ── 1 / 7. what json_normalize does unaided ──────────────────────────────────
flat = pd.json_normalize(doc)
print(f"\n1. columns after json_normalize(doc): {flat.shape[1]}")
print(f"7. rows: {flat.shape[0]}   (the thread has 336 nodes)")
print("   One row, because the document is one object. `children` arrives as a")
print("   single cell holding a list of 25 dicts, each holding more.")
print(f"   type of the `children` cell: {type(flat['children'][0]).__name__} "
      f"of {len(flat['children'][0])}")

# ── 10. flattening one level, which is as far as record_path goes ────────────
one = pd.json_normalize(doc, record_path="children")
print(f"\n10. json_normalize(doc, record_path='children'): {one.shape[0]} rows "
      f"x {one.shape[1]} cols")
print("    25 rows: the top-level replies only. The other 311 nodes are still")
print("    inside list cells. `record_path` takes a FIXED path, and this")
print("    document's records are at thirteen different depths.")

# The honest way to get 336 rows out of pandas is to do the recursion yourself
# and hand it a flat list — at which point pandas has answered nothing.
def descend(n):
    yield {k: v for k, v in n.items() if k != "children"}
    for c in n.get("children", []):
        yield from descend(c)

full = pd.DataFrame(list(descend(doc)))
print(f"\n    after recursing in Python first: {full.shape[0]} rows x "
      f"{full.shape[1]} cols")
print("    which is the right table, and pandas contributed the constructor.")

print("""
2, 3, 4, 5, 6. cannot.

  `max_level` is the closest thing to an answer for question 2 and it is
  backwards: it takes the depth as INPUT to limit flattening. You cannot ask
  json_normalize how deep something is; you tell it, and it obeys.

  Question 3 is again the load-bearing one. `record_path='children'` is a person
  saying what a record is, and it is still wrong here — it names one level of a
  structure that repeats thirteen times.
""")
