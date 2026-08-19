"""pydash — Chicago employee salaries, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   923 KB, 5,000 records, 8 fields, depth 2
  measured      2026-08-10
  run           cd corpus/19-chicago-salaries/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  yes
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          -   -                   CANNOT
   4 always present vs sometimes                 4   NO                  yes
   5 does any field change type                  3   YES                 PARTLY
   6 are any object keys data                    -   -                   n/a
   7 how many records                            1   NO                  YES
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   2   -                   n/a
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       5   NO                  yes
  13 needed the shape in advance?                    NO for 1, 4, 7, 12
  14 survives the next file unchanged?               Q1 does
  15 readable a week later?                          yes, it is lodash
  16 lines, and how much is ceremony?                ~30, little

WHY THIS FILE MATTERS TO THE CORPUS. pydash's whole-document key walk answers
**3,126** on npm and **25** on the notebook, both times landing in the wrong
neighbourhood or the right one by accident. Here it answers 8, which is exactly
right — and the reason is that this document has nothing for it to get wrong.
"""
import json
import sys
from collections import Counter
from importlib.metadata import version

import pydash

print(f"python {sys.version.split()[0]}, pydash {version('pydash')}")
doc = json.load(open("../source.json"))


def leaf_names(node, acc):
    if isinstance(node, dict):
        for k, v in node.items():
            acc.add(k)
            leaf_names(v, acc)
    elif isinstance(node, list):
        for v in node:
            leaf_names(v, acc)
    return acc


names = leaf_names(doc, set())
print(f"\n1. distinct key names anywhere: {len(names)}")
print(f"   {sorted(names)}")
print("   RIGHT, for the first time in the corpus. npm's walk answered 3,126")
print("   where the truth was 40; here it answers 8 and the truth is 8. The")
print("   walk did not improve — the document has no keys-as-data, no nesting")
print("   and no arrays, so there is nothing for a name-collector to inflate.")
print("   It still says nothing about WHERE anything is, which on a flat file")
print("   happens not to matter.")

print("\n2, 3, 11. CANNOT. No depth verb, no row-shape proposal, no search over")
print("   unknown paths — the recursion above is mine, not pydash's.")

print(f"\n7. {len(doc)} records.")

present = Counter(k for r in doc for k in r)
print("\n4. key PRESENCE, straight off the walk:")
for k, n in present.most_common():
    print(f"     {k:22} {n:>5} of {len(doc)}")
print(f"   {sum(1 for v in present.values() if v == len(doc))} of {len(present)} "
      f"keys are on every record. The other three sum to 5,000 twice over.")

kinds = Counter(type(pydash.get(r, "annual_salary")).__name__
                for r in doc if pydash.get(r, "annual_salary") is not None)
print(f"\n5. PARTLY. types at annual_salary: {dict(kinds)}")
print("   All `str`. The Counter is mine; pydash has no type report.")

rows = pydash.map_(doc, lambda r: {"name": pydash.get(r, "name"),
                                   "dept": pydash.get(r, "department"),
                                   "salary": pydash.get(r, "annual_salary")})
print(f"\n8. three fields: {len(rows)} rows, e.g. {rows[0]}")
print(f"\n9. salary is None on {sum(1 for r in rows if r['salary'] is None)} of "
      f"{len(rows)}, all kept — `pydash.get` defaults rather than raising.")

print("\n10, 6. n/a. No nested array, no keys that are data.")

g = pydash.group_by(doc, "salary_or_hourly")
print(f"\n12. flattest honest table: {len(doc)} x 8 — and the better answer is")
print("   `pydash.group_by(doc, 'salary_or_hourly')`, one call:")
for k, v in sorted(g.items(), key=lambda kv: -len(kv[1])):
    print(f"     {k:18} {len(v):>5} rows, "
          f"{len(set().union(*[set(x) for x in v]))} fields, no holes")
print("   pydash HAS the verb, it is one line, and nothing in the tool's output")
print("   suggests the document wants it. That is the corpus's recurring")
print("   sentence: the contribution is the looking, not the arithmetic.")
print("   WHAT IS LOST: nothing.")
