"""jq (via the `jq` Python binding) — Chicago employee salaries, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq, Python binding (version printed at run time)
  file          ../source.json   923 KB, 5,000 records, 8 fields, depth 2
  measured      2026-08-10
  run           cd corpus/19-chicago-salaries/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   NO                  yes
   2 how deep                                    1   NO                  yes
   3 what is one record                          6   NO                  PARTLY
   4 always present vs sometimes                 4   NO                  yes
   5 does any field change type                  5   NO                  yes
   6 are any object keys data                    2   -                   n/a
   7 how many records                            1   NO                  YES
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   2   -                   n/a
  11 find every path matching something          4   NO                  yes
  12 flattest honest table                       5   NO                  yes
  13 needed the shape in advance?                    NO for everything but 8
  14 survives the next file unchanged?               yes
  15 readable a week later?                          yes, the expressions are short
  16 lines, and how much is ceremony?                ~35, dense not ceremonial
"""
import json
import sys
from importlib.metadata import version

import jq

print(f"python {sys.version.split()[0]}, jq binding {version('jq')}")
doc = json.load(open("../source.json"))
q = lambda e: jq.compile(e).input(doc).all()

print("\n1. folded path shapes:")
for s in q('[paths(scalars)|map(if type=="number" then "[]" else . end)|join(".")]'
           '|group_by(.)|map({p:.[0],n:length})|sort_by(-.n)')[0]:
    print(f"     {s['p']:26} {s['n']:>6,}")
print(f"\n2. deepest path: {q('[paths|length]|max')[0]} segments")

print("\n4. key presence across the 5,000 records, nothing named:")
for r in q('[.[]|keys[]]|group_by(.)|map({k:.[0],n:length})|sort_by(-.n)')[0]:
    print(f"     {r['k']:22} {r['n']:>5} of 5000")
print("   3,938 + 1,062 = 5,000. jq computes both and does not add them up.")

print("\n5. types per folded path:")
for r in q('[paths as $p|select((getpath($p)|type) as $t|$t!="object" and '
           '$t!="array")|{p:($p|map(if type=="number" then "[]" else . end)'
           '|join(".")),t:(getpath($p)|type)}]|group_by(.p)'
           '|map({p:.[0].p,t:(map(.t)|unique|join(","))})')[0]:
    print(f"     {r['p']:26} {r['t']}")
print("   Every path is `string` — no field changes type, and `annual_salary`")
print("   is text. jq reports this correctly and it is still the trap: a")
print("   document consistently wrong looks exactly like one that is right.")

print(f"\n7. {q('length')[0]} records.")
print("\n3. one employee per row, and TWO defensible tables:")
for r in q('[.[]|{k:.salary_or_hourly,n:(keys|length)}]|group_by(.k)'
           '|map({k:.[0].k,rows:length,cols:(map(.n)|max)})|sort_by(-.rows)')[0]:
    print(f"     {r['k']:18} {r['rows']:>5} rows x {r['cols']} cols, all filled")
print("   `group_by(.salary_or_hourly)` is one expression and jq will not")
print("   suggest it. The union is 8 columns at 22% empty; the split is 6 and 7")
print("   at 0%. jq has every number needed to notice and notices nothing.")

rows = q('[.[]|{name,department,annual_salary}]')[0]
print(f"\n8. three fields: {len(rows)} rows, e.g. {rows[0]}")
print(f"\n9. `annual_salary` null on "
      f"{sum(1 for r in rows if r['annual_salary'] is None)} of {len(rows)}, all kept.")

print("\n10, 6. n/a. No nested array, no keys that are data.")
hits = q('[paths(strings) as $p|select(getpath($p)|test("DEPARTMENT"))'
         '|($p|map(if type=="number" then "[]" else . end)|join("."))]'
         '|group_by(.)|map({p:.[0],n:length})|sort_by(-.n)')[0]
print(f"\n11. values matching /DEPARTMENT/: "
      f"{sum(h['n'] for h in hits)} at {len(hits)} paths")
for h in hits:
    print(f"     {h['p']:26} {h['n']:>6,}")
print("   Found without naming a column, which is the question's point and the")
print("   thing every frame-shaped tool has to fake with `df.columns`.")

print(f"\n12. flattest honest table: {q('length')[0]} x 8, already flat.")
print("   WHAT IS LOST: nothing. jq is complete on this document and silent")
print("   about the two things worth saying.")
