"""jmespath — Open-Meteo hourly forecast, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   12 KB, 336 hours x 5 variables, stored COLUMN-WISE
  measured      2026-08-09
  run           cd corpus/08-open-meteo/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   1 what is in here                             3   YES                 PARTLY
   3 what is one record                           -  -                   CANNOT
   7 how many records                             2  YES                 YES
   8 three named fields to a table                4  YES                 PARTLY
"""
import json, sys
from importlib.metadata import version
import jmespath
print(f"python {sys.version.split()[0]}, jmespath {version('jmespath')}")
doc = json.load(open("../source.json"))

print("\n1. keys, one level at a time:")
print(f"     root:   {jmespath.search('keys(@)', doc)}")
print(f"     hourly: {jmespath.search('keys(hourly)', doc)}")

print(f"\n7. hours: {jmespath.search('length(hourly.time)', doc)}")

# 8. jmespath's multiselect builds objects from a LIST of objects. This
#    document has no list of objects, so the idiom does not apply at all and
#    the answer has to be assembled by index.
print("\n8. jmespath has no zip and no transpose. Per-index it is:")
for i in range(3):
    r = jmespath.search(
        f"{{time: hourly.time[{i}], temp: hourly.temperature_2m[{i}], "
        f"rh: hourly.relative_humidity_2m[{i}]}}", doc)
    print(f"     {r}")
print("   336 of those, one expression each, with the index written in.")
print("   The multiselect idiom that works on every other corpus file needs a")
print("   list of objects to project over, and this document contains none.")

print("\n   and the silent-failure property again:")
print(f"     hourly.nosuchvar        -> {jmespath.search('hourly.nosuchvar', doc)!r}")
print(f"     hourly.time[999]        -> {jmespath.search('hourly.time[999]', doc)!r}")
print("   A misspelled variable and an out-of-range hour are both None, with")
print("   no error. On a document nobody has seen, both are easy mistakes.")

print("\n3. CANNOT. No verb proposes a row shape, and the correct answer here")
print("   is a transpose, which jmespath cannot express at any length.")
