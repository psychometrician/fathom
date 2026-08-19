"""glom — ESPN quarterback rating, 2019

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   176 KB, 28 athletes
  measured      2026-08-09
  run           cd corpus/06-espn-qbr/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   1 what is in here                             1   YES                 PARTLY
   7 how many records                            1   YES                 YES
   8 three named fields to a table               4   YES                 YES
   7a related by position, not nesting           5   YES                 partly
"""
import json, sys
from importlib.metadata import version
from glom import glom, Iter, T
print(f"python {sys.version.split()[0]}, glom {version('glom')}")
doc = json.load(open("../source.json"))
print(f"\n7. athletes: {len(doc['athletes'])}")
rows = glom(doc, ("athletes", Iter({
    "name": "athlete.displayName",
    "team": "athlete.teamName",
    "totals": "categories.0.totals",
}).all()))
print(f"\n8. {len(rows)} rows. First: {rows[0]['name']} ({rows[0]['team']})")

labels = glom(doc, "categories.0.labels")
named = dict(zip(labels, rows[0]["totals"]))
print(f"\n7a. zipped against categories.0.labels:")
print(f"    {named}")
wrong = dict(zip([g["abbreviation"] for g in doc["glossary"]], rows[0]["totals"]))
print(f"    zipped against glossary instead — the same shape, wrong answers:")
print(f"    TQBR = {wrong['TQBR']} (really {named['TQBR']}), PA = {wrong['PA']} (really {named['PA']})")
print("""    glom will zip whatever it is handed and has no opinion about which
    array is correct. Both dicts are well-formed, both have ten entries, both
    have the right keys, and one is wrong throughout.""")
