"""glom — Open-Meteo hourly forecast, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   12 KB, 336 hours x 5 variables, stored COLUMN-WISE
  measured      2026-08-09
  run           cd corpus/08-open-meteo/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   1 what is in here                             -   -                   CANNOT
   7 how many records                             1  YES                 YES
   8 three named fields to a table                6  YES                 YES
  7a related by position, not nesting             6  YES                 PARTLY
  12 flattest honest table                        4  YES                 YES
"""
import json, sys
from importlib.metadata import version
from glom import glom, T
print(f"python {sys.version.split()[0]}, glom {version('glom')}")
doc = json.load(open("../source.json"))

print(f"\n7. hours: {len(glom(doc, 'hourly.time'))}")

# 8 and 12. glom has no transpose. The zip is plain Python, and glom's part is
#    only reaching the three arrays — which is the easy half on this document.
cols = ["time", "temperature_2m", "relative_humidity_2m"]
arrays = [glom(doc, f"hourly.{c}") for c in cols]
rows = [dict(zip(cols, vals)) for vals in zip(*arrays)]
print(f"\n8. {len(rows)} rows x {len(cols)} cols, via zip(*...) in plain Python")
for r in rows[:3]:
    print(f"     {r}")

print("\n7a. glom will zip whatever it is handed, and the check that the arrays")
print("    align is one a human does:")
lens = {c: len(glom(doc, f"hourly.{c}")) for c in glom(doc, "hourly").keys()}
print(f"    {lens}")
print("    All five are 336. glom reported the lengths because I asked for each")
print("    key by name; it has no verb for 'every array under this parent'.")

print("\n12. the flattest honest table is 336 x 5, and the scalars at the root")
print(f"    are lost: {[k for k,v in doc.items() if not isinstance(v, dict)]}")
print("    so is hourly_units, which is the only record of what the numbers")
print("    mean — degrees, km/h, percent.")

print("\n1. CANNOT. glom describes nothing; every spec names a path already known.")
