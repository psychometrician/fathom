"""pydash — ESPN quarterback rating, 2019

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   176 KB, 28 athletes
  measured      2026-08-09
  run           cd corpus/06-espn-qbr/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   1 what is in here                             2   no                  YES
   2 how deep                                    1   no                  YES
   7 how many records                            1   YES                 YES
   7a related by position, not nesting           4   no                  CANNOT
"""
import json, sys
from collections import Counter, defaultdict
from importlib.metadata import version
import pydash
print(f"python {sys.version.split()[0]}, pydash {version('pydash')}")
doc = json.load(open("../source.json"))
names, deepest = Counter(), 0
def walk(n, d):
    global deepest
    deepest = max(deepest, d)
    if isinstance(n, dict):
        for k, v in n.items(): names[k] += 1; walk(v, d+1)
    elif isinstance(n, list):
        for v in n: walk(v, d+1)
walk(doc, 0)
print(f"\n7. athletes: {len(doc['athletes'])}")
print(f"1. distinct key names: {len(names)}")
print(f"2. deepest nesting: {deepest}   (axes.py grades 7)")
print(f"\n7a. pydash.get('categories.0.labels') -> "
      f"{pydash.get(doc, 'categories.0.labels')}")
print(f"    pydash.get('athletes.0.categories.0.totals') -> "
      f"{pydash.get(doc, 'athletes.0.categories.0.totals')}")
print("""    Both fetch cleanly and no dotted-key ambiguity bites here, unlike on
    npm. Relating them is a zip a person writes, and choosing `labels` over
    `glossary` is a judgement pydash has no way to inform.""")
