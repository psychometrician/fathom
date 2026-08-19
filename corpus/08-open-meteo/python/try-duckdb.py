"""DuckDB read_json_auto — Open-Meteo hourly forecast, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   12 KB, 336 hours x 5 variables, stored COLUMN-WISE
  measured      2026-08-09
  run           cd corpus/08-open-meteo/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   NO                  YES
   3 what is one record                           -  -                   CANNOT
   7 how many records                             2  YES                 YES
  12 flattest honest table                        5  YES                 YES
"""
import sys
import duckdb
print(f"python {sys.version.split()[0]}, duckdb {duckdb.__version__}")
con = duckdb.connect()

d = con.sql("DESCRIBE SELECT * FROM read_json_auto('../source.json')").df()
print(f"\n1. DESCRIBE: {len(d)} rows")
print("   " + d.to_string(index=False).replace("\n", "\n   ")[:700])
print("   Nine tidy rows, and `hourly` is one STRUCT cell holding five arrays.")
print("   DuckDB reports one row for a document that is 336 rows.")

n = con.sql("SELECT len(hourly.time) FROM read_json_auto('../source.json')").fetchone()[0]
print(f"\n7. hours: {n}")

# 12. DuckDB is the only tool in this comparison with a first-class operator for
#     the transpose — unnest over several equal-length lists at once. It still
#     has to be told which lists, and that is question 3.
print("\n12. unnest of the five hourly arrays together:")
q = """SELECT unnest(hourly.time) AS time,
              unnest(hourly.temperature_2m) AS temp,
              unnest(hourly.wind_speed_10m) AS wind,
              unnest(hourly.relative_humidity_2m) AS rh
       FROM read_json_auto('../source.json')"""
t = con.sql(q).df()
print(f"   {t.shape[0]} rows x {t.shape[1]} cols")
print("   " + t.head(3).to_string(index=False).replace("\n", "\n   "))
print("   The right answer, in one statement, and every column name in it was")
print("   typed by somebody who already knew the shape. DuckDB will zip any")
print("   arrays you name; it has no opinion on whether they align.")

print("\n3. CANNOT. `DESCRIBE` says one row. Nothing proposes 336.")
