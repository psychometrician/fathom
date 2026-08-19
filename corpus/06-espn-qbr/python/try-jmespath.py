"""jmespath — ESPN quarterback rating, 2019

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   176 KB, 28 athletes
  measured      2026-08-09
  run           cd corpus/06-espn-qbr/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   1 what is in here                             1   no                  PARTLY
   7 how many records                            1   YES                 YES
   8 three named fields to a table               2   YES                 YES
   7a related by position, not nesting           -   -                   cannot
"""
import json, sys
from importlib.metadata import version
import jmespath
print(f"python {sys.version.split()[0]}, jmespath {version('jmespath')}")
doc = json.load(open("../source.json"))
ask = lambda e: jmespath.search(e, doc)
print(f"\n7. athletes: {ask('length(athletes)')}")
print(f"1. keys(@): {sorted(ask('keys(@)'))}")
rows = ask("athletes[].{name: athlete.displayName, team: athlete.teamName}")
print(f"\n8. {len(rows)} rows, first: {rows[0]}")
print(f"\n7a. cannot. jmespath has no zip and no index-of, so relating")
print(f"    `categories[0].labels` to `athletes[].categories[0].totals` by")
print(f"    position is not expressible. It can fetch either array whole:")
print(f"      {ask('categories[0].labels')}")
print("    and the pairing is left entirely to the host language.")
