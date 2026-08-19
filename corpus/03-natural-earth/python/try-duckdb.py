"""DuckDB — Natural Earth country geometry

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   3.9 MB, 241 features, GeoJSON
  measured      2026-08-09
  run           cd corpus/03-natural-earth/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   0 is it sound                                 1   no                  YES
   1 what is in here                             4   no                  PARTLY
   2 how deep                                    2   no                  PARTLY
   3 what is one record                          3   YES                 partly
   4 always present vs sometimes                 3   YES                 YES
   5 does any field change type                  6   no                  see below
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            2   YES                 YES

WHY THIS FILE, AND IT IS A DIRECT REMATCH. `03-natural-earth` is the file that
made `design/probe.py` grow `shape()`: its polymorphism is in array DEPTH —
`coordinates` is `[[[x,y]]]` for a Polygon and `[[[[x,y]]]]` for a MultiPolygon,
same JSON type, different nesting, 122 against 119 features.

On `05-fhir-bundle`, DuckDB caught a field the probe misses by refusing to unify
array ELEMENT types. **This file asks the mirror question: does refusing to unify
also catch a difference in array DEPTH?** If it does, DuckDB has found both
halves of the defect `shape()` was written for and half of what it still has.
"""
import re
import sys
from importlib.metadata import version

import duckdb

print(f"python {sys.version.split()[0]}, duckdb {version('duckdb')}")

con = duckdb.connect()
SRC = "'../source.json'"

desc = con.sql(f"DESCRIBE SELECT * FROM read_json_auto({SRC})").fetchall()
size = len(open("../source.json", "rb").read())
total = sum(len(str(r[1])) for r in desc)
widest = max(desc, key=lambda r: len(str(r[1])))

print(f"\n1. DESCRIBE returns {len(desc)} rows for a {size:,}-byte file")
print(f"   total type text: {total:,} characters ({total / size:.2%} of it)")
print(f"   npm 378,036 in one cell · thread 2,514 · gharchive 15,714 · fhir 8,238")

n = con.sql(f"SELECT len(features) FROM read_json_auto({SRC})").fetchone()[0]
print(f"\n7. rows DuckDB reports: 1. Features inside: {n}")

# ── 5. the rematch ───────────────────────────────────────────────────────────
s = str(widest[1])
print(f"\n5. does the type fall back to JSON anywhere? "
      f"{s.count('JSON')} place(s)")
for m in re.finditer(r'"?(\w+)"?\s+JSON', s):
    print(f"     {m.group(1)}")

geom = con.sql(f"""
    SELECT typeof(f.geometry.coordinates) AS t, count(*) AS n
    FROM read_json_auto({SRC}), unnest(features) AS x(f)
    GROUP BY 1 ORDER BY n DESC
""").fetchall()
print(f"\n   the type DuckDB gave `geometry.coordinates`:")
for t, c in geom:
    print(f"     {str(t)[:64]:<66} x{c}")

kinds = con.sql(f"""
    SELECT f.geometry.type AS t, count(*) AS n
    FROM read_json_auto({SRC}), unnest(features) AS x(f)
    GROUP BY 1 ORDER BY n DESC
""").fetchall()
print(f"\n   and what the document says those features are:")
for t, c in kinds:
    print(f"     {t:<24} {c}")

print("""
3, 6. cannot.

  Question 3 is easy here and that is worth stating plainly: GeoJSON declares its
  own record. `features` is an array, every element is a Feature, and one row per
  feature is right. This is the only corpus file where question 3 has an obvious
  answer, and it is obvious because a specification made it so rather than because
  a tool worked it out.
""")
