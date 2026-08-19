"""pandas — Chicago employee salaries, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   923 KB, 5,000 records, 8 fields, depth 2
  measured      2026-08-10
  run           cd corpus/19-chicago-salaries/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   NO                  yes
   2 how deep                                    2   NO                  yes
   3 what is one record                          6   NO                  PARTLY
   4 always present vs sometimes                 4   NO                  yes
   5 does any field change type                  6   NO                  DANGEROUS
   6 are any object keys data                    2   YES                 n/a
   7 how many records                            1   NO                  YES
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   2   -                   n/a
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       5   NO                  yes
  13 needed the shape in advance?                    NO — the file is flat
  14 survives the next file unchanged?               yes, for this shape
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~35, no ceremony

WHY THIS FILE IS THE EASY ONE, AND WHY IT STILL HAS A TRAP. Depth 2, no arrays,
no keys-as-data, one record per employee. Every tool in the corpus gets the
table. What almost none of them says is that `annual_salary` is a NUMBER STORED
AS TEXT, and that the 22% of holes has a perfect two-way explanation.
"""
import json
import sys
from importlib.metadata import version

import pandas as pd

print(f"python {sys.version.split()[0]}, pandas {version('pandas')}")
doc = json.load(open("../source.json"))
df = pd.json_normalize(doc)

print(f"\n1. json_normalize: {df.shape[0]} rows x {df.shape[1]} cols")
print(f"   {list(df.columns)}")
print("   A complete answer, and the only corpus file where json_normalize")
print("   gives one — because there is no array for it to stop at.")

print("\n2. depth 2. json_normalize produced no dotted names, which IS the")
print("   answer here: nothing was nested.")

# ── 4 ────────────────────────────────────────────────────────────────────────
print("\n4. non-null count per column:")
for k, v in (df.notna().sum()).sort_values(ascending=False).items():
    print(f"     {k:22} {int(v):>5} of {len(df)}")
print("   Five always, three sometimes. `annual_salary` 3,938 and `hourly_rate`")
print("   1,062 sum to exactly 5,000 — they are MUTUALLY EXCLUSIVE, and nothing")
print("   in this output says so.")

# ── 5. the trap ──────────────────────────────────────────────────────────────
print(f"\n5. dtypes: {dict(df.dtypes.astype(str))}")
print("   DANGEROUS. Every column is `str` — including `annual_salary`, which")
print("   holds '165624', and `hourly_rate`, which holds '9.46'. pandas read")
print("   them as text because the JSON has them as text, and reports no type")
print("   change because there is none. **The document is wrong and the tool is")
print("   right**, which is the failure mode a type report cannot catch.")
print(f"   df['annual_salary'].max() = {df['annual_salary'].max()!r}   <- STRING max")
print("   That is the highest salary alphabetically, not numerically. No error.")

# ── 3, 7 ─────────────────────────────────────────────────────────────────────
print(f"\n7. {len(df)} records.")
print("\n3. one record is one employee — and there are TWO defensible tables:")
print(f"     all employees      {len(df)} rows x {df.shape[1]} cols   "
      f"{100 * df.isna().mean().mean():.0f}% empty")
g = df.groupby("salary_or_hourly")
for k, sub in g:
    print(f"     {k:18} {len(sub):>5} rows x "
          f"{int(sub.notna().any().sum()):>2} cols   "
          f"{100 * sub[sub.columns[sub.notna().any()]].isna().mean().mean():.0f}% empty")
print("   22% empty folded, 0% in each group. pandas computes this in one")
print("   groupby and never suggests it — the column that explains the holes is")
print("   sitting in the frame, named `salary_or_hourly`.")

# ── 8, 9 ─────────────────────────────────────────────────────────────────────
t = df[["name", "department", "annual_salary"]]
print(f"\n8. three fields:\n{t.head(3).to_string(index=False)}")
print(f"\n9. `annual_salary` is NaN on {int(t['annual_salary'].isna().sum())} of "
      f"{len(t)} rows, all kept — the 1,062 hourly employees.")

# ── 10, 6, 11 ────────────────────────────────────────────────────────────────
print("\n10. n/a. There is no nested array in this document.")
print("\n6. n/a. No object keys are data; every key is a field name.")
print("\n11. CANNOT. No whole-document path search — though on a flat frame")
print("   `df.apply(lambda c: c.str.contains(...))` is close enough to count.")

# ── 12 ───────────────────────────────────────────────────────────────────────
print(f"\n12. flattest honest table: {df.shape[0]} x {df.shape[1]}, already flat.")
print("   WHAT IS LOST: nothing structural. What is NOT SAID is that three")
print("   columns are numbers in string clothing and that 22% of the cells are")
print("   empty for one knowable reason. A perfect extraction of a table that")
print("   should have been two.")
