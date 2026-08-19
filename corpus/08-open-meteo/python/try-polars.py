"""polars — Open-Meteo hourly forecast, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   12 KB, 336 hours x 5 variables, stored COLUMN-WISE
  measured      2026-08-09
  run           cd corpus/08-open-meteo/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  YES
   3 what is one record                           -  -                   CANNOT
   7 how many records                             2  YES                 YES
  12 flattest honest table                        5  YES                 YES
"""
import json, sys
import polars as pl
print(f"python {sys.version.split()[0]}, polars {pl.__version__}")
doc = json.load(open("../source.json"))

# 1. polars' schema is the best description any tool gives of this file, and it
#    is still the wrong shape — it says list[f64] where the truth is a column.
df = pl.DataFrame([doc])
schema = str(df.schema)
print(f"\n1. schema: {len(schema)} chars for a 12,198-byte file "
      f"({len(schema)/12198:.1%})")
print(f"   {schema[:300]}")
print("   The five hourly variables are typed `list[...]` of length 336, which")
print("   is literally true and structurally misleading: they are not lists,")
print("   they are columns, and the thing that says so is that all five have")
print("   the same length and sit under one parent.")

print(f"\n7. hours: {len(doc['hourly']['time'])}")

# 12. polars transposes as readily as pandas, and equally only on request.
hourly = pl.DataFrame(doc["hourly"])
print(f"\n12. pl.DataFrame(doc['hourly']): {hourly.height} rows x {hourly.width} cols")
print("   " + str(hourly.head(3)).replace("\n", "\n   "))
print(f"   lost: {len(doc)-2} root scalars and hourly_units, which holds the")
print("   unit for every column and is the only place they are recorded.")

print("\n3. CANNOT. polars types the lists correctly and has no verb that would")
print("   propose 336 rows. Its own answer to 'how many rows' is 1.")
