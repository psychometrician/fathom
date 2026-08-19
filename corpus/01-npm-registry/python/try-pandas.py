"""pandas.json_normalize — npm registry metadata for `express`

Scoring header follows ../r/try-purrr.R, which is the template.

  tool          pandas 3.0.5, json_normalize
  file          ../source.json   786 KB, 288 versions, 25,044 paths
  measured      2026-08-08
  run           cd corpus/01-npm-registry/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   1 what is in here                             -   -                   TODO
   2 how deep                                    -   -                   TODO
   3 what is one record                          -   -                   TODO
   4 always present vs sometimes                 -   -                   TODO
   5 does any field change type                  -   -                   TODO
   6 are any keys actually data                  -   -                   TODO
   7 how many records                            -   -                   TODO
   8 three named fields to a table               3   YES, and post-flat  yes
   9 a field missing from some rows              -   -                   TODO
  10 flatten the deepest array                   -   -                   TODO
  11 find every path matching something          -   -                   TODO
  12 flattest honest table                       -   -                   TODO
  13 needed the shape in advance?                    see notes below
  14 survives the next file unchanged?               TODO
  15 readable a week later?                          TODO
  16 lines, and how much is ceremony?                TODO
"""
import json
import sys
from importlib.metadata import version

import pandas as pd

# Printed rather than typed. The header above records what produced the scores;
# this line records what just ran, and a difference between them means the re-run
# is not comparable. It is code rather than trust because two of this corpus's
# first three headers named a version that was not installed.
print(f"python {sys.version.split()[0]}, pandas {version('pandas')}")

doc = json.load(open("../source.json"))

# Q8. Three named fields, one row per version. 288 rows.
tbl = pd.json_normalize(list(doc["versions"].values()))[
    ["version", "author.name", "dist.tarball"]
]
assert len(tbl) == 288

# WHAT IT COST.
#
# json_normalize flattens the whole record and *then* you select, which is the
# opposite order from purrr and it changes what you must know. The names are the
# POST-FLATTENING names: `author.name`, not `author`. So you have to have seen the
# flattened frame before you can name a column, and on this file that frame is
# very wide.
#
# It also silently swallows the raggedness that purrr made you write `%||%` for.
# Missing keys become NaN with no mention. That is friendlier and it is also how
# you fail to notice that 31 of 40 fields are ragged.
#
# Q13. Same four things purrr needed, plus a fifth: the flattened column names.
