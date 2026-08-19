"""DuckDB read_json — npm registry metadata for `express`

Scoring header follows ../r/try-purrr.R, which is the template.

  tool          duckdb 1.5.5, read_json + JSON path operators
  file          ../source.json   786 KB, 288 versions, 25,044 paths
  measured      2026-08-08
  run           cd corpus/01-npm-registry/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   8 three named fields to a table               6   YES, and worse      yes
  (all others TODO)
"""
import sys
from importlib.metadata import version

import duckdb

# Printed rather than typed. The header above records what produced the scores;
# this line records what just ran. pandas is named here even though this file
# never imports it, because `.df()` needs it: that dependency is invisible in the
# code and it is what took this attempt down when a file called pandas.py
# shadowed the library.
print(f"python {sys.version.split()[0]}, duckdb {version('duckdb')}, "
      f"pandas {version('pandas')} (for .df())")

# Q8. Three named fields, one row per version.
#
# `versions` is an object keyed by version string, so there is no array to unnest
# and no column to select. The keys have to be listed and then pasted back into a
# JSON path as text.
rows = duckdb.sql("""
  SELECT unnest(json_keys(versions)) AS version,
         json_extract_string(
           versions -> ('$."' || unnest(json_keys(versions)) || '"'),
           '$.author.name') AS author
  FROM (SELECT json(versions) AS versions FROM read_json('../source.json'))
""").df()
assert len(rows) == 288

# WHAT IT COST.
#
# Fastest to run and the worst to write, and the reason is one axis: keys-as-data.
# Every other tool iterates a dict. SQL has no dict, so the keys become a list and
# each one is concatenated back into a path string, quotes and all. `'$."' || k ||
# '"'` is the whole problem in one expression, and it is unreadable a week later
# by the standard this project is testing against.
#
# THIS IS THE FINDING THIS TOOL CONTRIBUTES. Keys-as-data does not merely make a
# document large. It makes a tool ugly, and it does so in proportion to how far the
# tool is from having a dict.
