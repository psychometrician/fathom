"""pandas.json_normalize — Open-Meteo hourly forecast, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   12 KB, 336 hours x 5 variables, stored COLUMN-WISE
  measured      2026-08-09
  run           cd corpus/08-open-meteo/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   NO                  PARTLY
   3 what is one record                           -  -                   CANNOT
   7 how many records                             2  YES                 YES
  12 flattest honest table                        6  YES                 YES
"""
import json, sys
import pandas as pd
print(f"python {sys.version.split()[0]}, pandas {pd.__version__}")
doc = json.load(open("../source.json"))

# 1. json_normalize is the closest thing pandas has to a describer, and on a
#    column-oriented document it produces the wrong-shaped answer confidently.
flat = pd.json_normalize(doc)
print(f"\n1. json_normalize(root): {flat.shape[0]} row x {flat.shape[1]} cols")
print(f"   {[c for c in flat.columns][:6]} ...")
print("   ONE row, and each weather variable is a single cell holding a")
print("   336-element list. The document is a table and pandas has produced")
print("   a 1-row table whose cells are the columns.")

print(f"\n7. hours: {len(doc['hourly']['time'])}")
print("   which pandas did not tell you — it is len() of a cell you picked.")

# 12. The honest table needs the transpose, and pandas CAN do it — but only
#     because a human already knew `hourly` was the thing and that its values
#     align by position. Nothing in the output above says either.
df = pd.DataFrame(doc["hourly"])
print(f"\n12. pd.DataFrame(doc['hourly']): {df.shape[0]} rows x {df.shape[1]} cols")
print(df.head(3).to_string(index=False))
print("   This IS the answer, and getting it took knowing the answer.")
print("   pd.DataFrame() over a dict-of-equal-length-lists transposes silently,")
print("   which is right here and would be wrong on any dict whose lists")
print("   happen to match in length without being a table.")
print(f"   lost: the 7 scalar fields at the root ({', '.join(list(doc)[:4])}, …)")
print(f"   and hourly_units, which names the unit of every column.")

print("\n3. CANNOT. There is no candidate-row verb, and the naive read gives")
print("   one row. The document offers no signal that 336 is the row count.")
