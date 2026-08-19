"""polars — Chicago employee salaries, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   923 KB, 5,000 records, 8 fields, depth 2
  measured      2026-08-10
  run           cd corpus/19-chicago-salaries/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   NO                  yes
   2 how deep                                    2   NO                  yes
   3 what is one record                          6   NO                  PARTLY
   4 always present vs sometimes                 4   NO                  yes
   5 does any field change type                  5   NO                  DANGEROUS
   6 are any object keys data                    2   -                   n/a
   7 how many records                            1   NO                  YES
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   2   -                   n/a
  11 find every path matching something          4   YES                 PARTLY
  12 flattest honest table                       4   NO                  yes
  13 needed the shape in advance?                    NO — the file is flat
  14 survives the next file unchanged?               yes, for this shape
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~35, no ceremony
"""
import sys
from importlib.metadata import version

import polars as pl

print(f"python {sys.version.split()[0]}, polars {version('polars')}")
df = pl.read_json("../source.json")

schema = str(df.schema)
print(f"\n1. read_json: {df.height} x {df.width}. Schema {len(schema)} chars "
      f"({100 * len(schema) / 944651:.2f}% of the file) — the corpus's smallest")
print(f"   {dict(df.schema)}")

print("\n2. depth 2. No Struct and no List anywhere in the schema, which is")
print("   polars saying `nothing here is nested` without being asked.")

print("\n4. non-null per column:")
for c in sorted(df.columns, key=lambda c: df[c].null_count()):
    print(f"     {c:22} {df.height - df[c].null_count():>5} of {df.height}")
print("   `annual_salary` 3,938 + `hourly_rate` 1,062 = 5,000 exactly. Mutually")
print("   exclusive, and nothing in the schema or the null counts says so.")

# ── 5. the trap ──────────────────────────────────────────────────────────────
print("\n5. DANGEROUS. Every column is String, including `annual_salary`")
print("   ('165624') and `hourly_rate` ('9.46'). polars is right — the JSON")
print("   really does hold text — and a type report cannot flag a document that")
print("   is internally consistent about being wrong.")
mx = df.select(pl.col("annual_salary").max()).item()
print(f"   max(annual_salary) = {mx!r}  <- a STRING maximum, silently")
print("   No warning, no coercion, no error. polars' honesty is the problem.")

# ── 3, 7 ─────────────────────────────────────────────────────────────────────
print(f"\n7. {df.height} records.")
print("\n3. one employee per row, and TWO defensible tables:")
tot = 100 * sum(df[c].null_count() for c in df.columns) / (df.height * df.width)
print(f"     all employees      {df.height} rows x {df.width} cols   {tot:.0f}% empty")
for k, sub in df.group_by("salary_or_hourly"):
    live = [c for c in sub.columns if sub[c].null_count() < sub.height]
    e = 100 * sum(sub[c].null_count() for c in live) / (sub.height * len(live))
    print(f"     {k[0]:18} {sub.height:>5} rows x {len(live):>2} cols   {e:.0f}% empty")
print("   22% to 0%, in one group_by that polars will do and never propose.")

# ── 8, 9 ─────────────────────────────────────────────────────────────────────
print(f"\n8. three fields:\n{df.select('name', 'department', 'annual_salary').head(3)}")
print(f"\n9. `annual_salary` null on "
      f"{df['annual_salary'].null_count()} of {df.height} rows, all kept.")

# ── 10, 6, 11, 12 ────────────────────────────────────────────────────────────
print("\n10, 6. n/a. No nested array, and no object keys are data.")
print("\n11. PARTLY, and this is polars at its best on a flat file: one")
hits = {c: df.select(pl.col(c).str.contains("DEPARTMENT").sum()).item()
        for c in df.columns}
print(f"   expression over EVERY column at once: {hits}")
print("   It is not a path search — the columns are named by `df.columns`, not")
print("   discovered — but on a document with no nesting the two coincide.")

print(f"\n12. flattest honest table: {df.height} x {df.width}, already flat.")
print("   WHAT IS LOST: nothing. What is not said: three numeric columns are")
print("   strings, and the 22% of holes has a two-word explanation sitting in")
print("   column five.")
