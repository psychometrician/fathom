"""pydash — Open-Meteo hourly forecast, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   12 KB, 336 hours x 5 variables, stored COLUMN-WISE
  measured      2026-08-09
  run           cd corpus/08-open-meteo/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   NO                  YES
   2 how deep does it go                          2  NO                  YES
   7 how many records                             1  YES                 YES
  12 flattest honest table                        5  YES                 YES
"""
import json, sys
from importlib.metadata import version
import pydash
print(f"python {sys.version.split()[0]}, pydash {version('pydash')}")
doc = json.load(open("../source.json"))

def paths(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield f"{p}.{k}"
            yield from paths(v, f"{p}.{k}")
    elif isinstance(o, list):
        for v in o:
            yield from paths(v, p + "[]")

distinct = sorted(set(paths(doc)))
print(f"\n1. {len(distinct)} distinct paths, {len(str(distinct))} chars to list")
print(f"   {distinct}")
print(f"   {len(distinct)} paths for the whole document, and it is COMPLETE — this is")
print("   the one corpus file where a path listing is a genuinely good answer.")
print("   It is also completely silent about the file being a table.")

def depth(o):
    if isinstance(o, dict) and o: return 1 + max(depth(v) for v in o.values())
    if isinstance(o, list) and o: return 1 + max(depth(v) for v in o)
    return 0
print(f"\n2. depth: {depth(doc)}")

print(f"\n7. hours: {len(pydash.get(doc, 'hourly.time'))}")

# 12. pydash.zip_ is the transpose, and it is the only tool in this comparison
#     whose native vocabulary contains the operation by name.
cols = list(doc["hourly"])
rows = pydash.zip_(*[doc["hourly"][c] for c in cols])
print(f"\n12. pydash.zip_(*hourly.values()): {len(rows)} rows x {len(rows[0])} cols")
print(f"    columns: {cols}")
for r in rows[:3]:
    print(f"      {r}")
print("    Right answer, and `zip_` had to be aimed at `hourly` by a human.")
