"""DuckDB — Chicago employee salaries, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   923 KB, 5,000 records, 8 fields, depth 2
  measured      2026-08-10
  run           cd corpus/19-chicago-salaries/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   NO                  yes
   2 how deep                                    2   NO                  yes
   3 what is one record                          5   NO                  PARTLY
   4 always present vs sometimes                 4   NO                  yes
   5 does any field change type                  5   NO                  DANGEROUS
   6 are any object keys data                    2   -                   n/a
   7 how many records                            1   NO                  YES
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   2   -                   n/a
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       4   NO                  yes
  13 needed the shape in advance?                    NO — the file is flat
  14 survives the next file unchanged?               yes, for this shape
  15 readable a week later?                          yes, it is SQL
  16 lines, and how much is ceremony?                ~35, some SQL ceremony
"""
import sys
from importlib.metadata import version

import duckdb

print(f"python {sys.version.split()[0]}, duckdb {version('duckdb')}")
con = duckdb.connect()
SRC = "read_json_auto('../source.json', maximum_object_size=100000000)"

d = con.sql(f"DESCRIBE SELECT * FROM {SRC}").df()
total = sum(len(str(t)) for t in d["column_type"])
print(f"\n1. DESCRIBE: {len(d)} rows, all type cells {total} chars "
      f"({100 * total / 944651:.3f}% of the file)")
print("   " + ", ".join(f"{c} {t}" for c, t in zip(d["column_name"], d["column_type"])))
print("   Eighteen tidy rows hid 378,036 characters on npm. Here the tidy table")
print("   IS the answer — no STRUCT, no list, nothing hiding in a cell.")

print("\n2. depth 2. Every column_type is a scalar, which is DuckDB saying")
print("   nothing is nested.")

print("\n4. non-null count per column:")
q = ", ".join(f'count("{c}") AS "{c}"' for c in d["column_name"])
row = con.sql(f"SELECT {q} FROM {SRC}").df().iloc[0].sort_values(ascending=False)
for k, v in row.items():
    print(f"     {k:22} {int(v):>5} of 5000")
print("   3,938 + 1,062 = 5,000. Mutually exclusive and unremarked.")

print("\n5. DANGEROUS. Every column is VARCHAR, `annual_salary` included.")
mx = con.sql(f"SELECT max(annual_salary) FROM {SRC}").fetchone()[0]
print(f"   max(annual_salary) = {mx!r}  <- lexicographic, no warning")
print("   DuckDB's read_json_auto DOES coerce numeric-looking JSON numbers, but")
print("   these are JSON STRINGS in the document, so there is nothing for it to")
print("   infer. The tool is right and the answer is wrong, which is the one")
print("   failure a type system cannot reach.")

n = con.sql(f"SELECT count(*) FROM {SRC}").fetchone()[0]
print(f"\n7. {n} records.")
print("\n3. one employee per row, and TWO defensible tables:")
for r in con.sql(f"""SELECT salary_or_hourly k, count(*) n,
                     count(annual_salary) a, count(hourly_rate) h
                     FROM {SRC} GROUP BY 1 ORDER BY 2 DESC""").fetchall():
    print(f"     {r[0]:18} {r[1]:>5} rows   annual {r[2]:>5}  hourly {r[3]:>5}")
print("   One GROUP BY away, 22% empty to 0%, and SQL will not propose it.")

print("\n8. three fields:")
print(con.sql(f"SELECT name, department, annual_salary FROM {SRC} LIMIT 3").df()
      .to_string(index=False))
miss = con.sql(f"SELECT count(*) FROM {SRC} WHERE annual_salary IS NULL").fetchone()[0]
print(f"\n9. `annual_salary` NULL on {miss} of {n} rows, all kept.")

print("\n10, 6. n/a. No nested array, no keys that are data.")
print("\n11. CANNOT. No path search over an arbitrary document; every column is")
print("   named. On a flat file that is a smaller loss than usual.")
print(f"\n12. flattest honest table: {n} x {len(d)}, already flat.")
print("   WHAT IS LOST: nothing. What is not said: three numeric columns are")
print("   text, and the holes have a two-word explanation in column five.")
