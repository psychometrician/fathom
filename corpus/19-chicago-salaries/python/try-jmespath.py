"""jmespath — Chicago employee salaries, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   923 KB, 5,000 records, 8 fields, depth 2
  measured      2026-08-10
  run           cd corpus/19-chicago-salaries/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   PARTLY              PARTLY
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          -   -                   CANNOT
   4 always present vs sometimes                 4   YES                 PARTLY
   5 does any field change type                  -   -                   CANNOT
   6 are any object keys data                    -   -                   n/a
   7 how many records                            1   YES                 YES
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              5   YES                 DANGEROUS
  10 flatten the deepest array                   2   -                   n/a
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       4   YES                 yes
  13 needed the shape in advance?                    YES, for everything
  14 survives the next file unchanged?               no, and it will not say so
  15 readable a week later?                          yes, the syntax is compact
  16 lines, and how much is ceremony?                ~30, none
"""
import json
import sys
from importlib.metadata import version

import jmespath

print(f"python {sys.version.split()[0]}, jmespath {version('jmespath')}")
doc = json.load(open("../source.json"))

print(f"\n1. keys([0]): {jmespath.search('[0]|keys(@)', doc)}")
print(f"   keys([4]): {jmespath.search('[4]|keys(@)', doc)}")
print("   PARTLY. `keys()` works one object at a time; the union across 5,000")
print("   records is the caller's job. Records 0 and 4 differ, and only because")
print("   one is salaried and one is hourly — which jmespath does not say.")

print("\n2, 3, 11. CANNOT. No depth verb, no row-shape proposal, and no")
print("   recursive descent at all — there is no `..` in jmespath.")
print("\n5. CANNOT. No verb reports a field's type across records.")

print(f"\n7. {jmespath.search('length(@)', doc)} records.")

print("\n4. PARTLY — a projection counts what is there, once you name it:")
for f in ("name", "department", "salary_or_hourly", "annual_salary", "hourly_rate"):
    print(f"     {f:22} {len(jmespath.search(f'[].{f}', doc) or []):>5} of 5000")
print("   3,938 + 1,062 = 5,000, and the projection silently drops the rows it")
print("   cannot fill rather than returning a null for them.")

rows = jmespath.search("[].{name: name, dept: department, salary: annual_salary}", doc)
print(f"\n8. three fields: {len(rows)} rows, e.g. {rows[0]}")

print(f"\n9. salary is None on {sum(1 for r in rows if r['salary'] is None)} of "
      f"{len(rows)} rows, all kept — the multiselect keeps the row. Correct.")
print("   DANGEROUS one step over, and this document makes it concrete:")
print(f"     [0].annual_salary   -> {jmespath.search('[0].annual_salary', doc)!r}")
print(f"     [4].annual_salary   -> {jmespath.search('[4].annual_salary', doc)!r}")
print(f"     [0].anual_salary    -> {jmespath.search('[0].anual_salary', doc)!r}")
print("   A legitimately-absent field and a MISSPELLED one are both None. On")
print("   this document the misspelling would show as 5,000 nulls and the real")
print("   field as 1,062 — but only if you thought to count.")

print("\n10, 6. n/a. No nested array, no keys that are data.")

groups = jmespath.search("[?salary_or_hourly=='HOURLY'] | length(@)", doc)
print(f"\n12. flattest honest table: {len(rows)} x 3 as written. jmespath CAN")
print(f"   filter — `[?salary_or_hourly=='HOURLY']` gives {groups} rows — so the")
print("   better two-table answer is one expression away. There is no group_by,")
print("   so you must know both values in advance to write both filters.")
print("   WHAT IS LOST: nothing selected wrongly. What is missing is any signal")
print("   that the 22% of holes had a reason.")
