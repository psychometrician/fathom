"""glom — Chicago employee salaries, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   923 KB, 5,000 records, 8 fields, depth 2
  measured      2026-08-10
  run           cd corpus/19-chicago-salaries/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   1 what is in here                             -   -                   CANNOT
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          -   -                   CANNOT
   4 always present vs sometimes                 4   YES                 PARTLY
   5 does any field change type                  3   YES                 PARTLY
   6 are any object keys data                    -   -                   n/a
   7 how many records                            1   YES                 YES
   8 three named fields to a table               4   YES                 yes
   9 a field missing from some rows              5   YES                 yes
  10 flatten the deepest array                   2   -                   n/a
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       4   YES                 yes
  13 needed the shape in advance?                    YES, for everything
  14 survives the next file unchanged?               no — every spec is a path
  15 readable a week later?                          yes, specs read as data
  16 lines, and how much is ceremony?                ~30, almost none
"""
import json
import sys
from importlib.metadata import version

from glom import Coalesce, PathAccessError, glom

print(f"python {sys.version.split()[0]}, glom {version('glom')}")
doc = json.load(open("../source.json"))

print("\n1, 2, 3, 11. CANNOT. glom is an EXTRACTOR — every spec names a path")
print("   the caller already knows. It has no describer, no depth verb, no")
print("   row-shape proposal and no search. On a flat 8-column document that")
print("   costs less than anywhere else in the corpus, and it is the same")
print("   CANNOT: glom cannot start you on a file you have not seen.")

print(f"\n7. {len(doc)} records.")

print("\n4. PARTLY — glom tests a key once you name it:")
for f in ("name", "department", "salary_or_hourly", "annual_salary", "hourly_rate"):
    have = sum(1 for r in doc if glom(r, Coalesce(f, default=None)) is not None)
    print(f"     {f:22} {have:>5} of {len(doc)}")
print("   The five names came from reading the file.")

kinds = {}
for r in doc:
    v = glom(r, Coalesce("annual_salary", default=None))
    if v is not None:
        kinds[type(v).__name__] = kinds.get(type(v).__name__, 0) + 1
print(f"\n5. PARTLY. types at annual_salary: {kinds}")
print("   All `str`. A Python loop with glom as the accessor; glom has no type")
print("   report and would not have flagged a number stored as text anyway.")

spec = [{"name": "name", "dept": "department",
         "salary": Coalesce("annual_salary", default=None)}]
rows = glom(doc, spec)
print(f"\n8. three fields, one row per employee: {len(rows)} rows")
print(f"     {rows[0]}")

missing = sum(1 for r in rows if r["salary"] is None)
print(f"\n9. salary absent on {missing} of {len(rows)} rows, all kept.")
try:
    glom(doc, ["annual_salary"])
    print("   expected a PathAccessError and did not get one")
except PathAccessError as e:
    print(f"   WITHOUT Coalesce it RAISES: {str(e).splitlines()[-1][:56]}…")
print("   And this is the case where raising is most clearly right: the 1,062")
print("   missing salaries are not a data problem, they are a DIFFERENT KIND OF")
print("   RECORD, and an error is the only thing that makes you look.")

print("\n10, 6. n/a. No nested array, no keys that are data.")

split = {}
for r in doc:
    split.setdefault(glom(r, "salary_or_hourly"), []).append(r)
print(f"\n12. flattest honest table: {len(rows)} x 3 as written above — and glom")
print("   makes the better answer just as easy once you know to ask:")
for k, v in sorted(split.items(), key=lambda kv: -len(kv[1])):
    print(f"     {k:18} {len(v):>5} rows, {len(set().union(*[set(x) for x in v]))} fields")
print("   WHAT IS LOST: nothing. glom reshapes nothing and volunteers nothing,")
print("   and on a document this simple those are the same sentence.")
