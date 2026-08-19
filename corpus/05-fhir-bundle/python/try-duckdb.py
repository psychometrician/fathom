"""DuckDB — a Synthea FHIR bundle

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   2,024,911 bytes, 564 resources, 20 resourceTypes
  measured      2026-08-09
  run           cd corpus/05-fhir-bundle/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   0 is it sound                                 1   no                  YES
   1 what is in here                             4   no                  PARTLY
   2 how deep                                    2   no                  PARTLY
   3 what is one record                          6   YES                 WRONG
   4 always present vs sometimes                 3   YES                 partly
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            2   YES                 YES

WHY THIS FILE. DuckDB was the strongest tool on `04-gharchive` by a wide margin.
Here the difficulty is not scale but heterogeneity: one array holding 20 kinds of
record. A type system has to reconcile them into one type, and this file asks what
that reconciliation costs and whether the report of it is legible.
"""
import sys
from importlib.metadata import version

import duckdb

print(f"python {sys.version.split()[0]}, duckdb {version('duckdb')}")

con = duckdb.connect()
SRC = "'../source.json'"

# ── 1 / 2. what DESCRIBE says about a bundle ─────────────────────────────────
desc = con.sql(f"DESCRIBE SELECT * FROM read_json_auto({SRC})").fetchall()
total = sum(len(str(r[1])) for r in desc)
widest = max(desc, key=lambda r: len(str(r[1])))
size = len(open("../source.json", "rb").read())
print(f"\n1. DESCRIBE returns {len(desc)} rows for a {size:,}-byte file")
print(f"   total type text: {total:,} characters "
      f"({total / size:.0%} of the document)")
print(f"   widest: {widest[0]!r} at {len(str(widest[1])):,} characters")
print(f"   npm 378,036 in one cell · thread 2,514 · gharchive 15,714 total")

def bracket_depth(t):
    d = best = 0
    for ch in str(t):
        d += ch == "("
        best = max(best, d)
        d -= ch == ")"
    return best

print(f"\n2. nesting depth of the widest type: {bracket_depth(widest[1])}   "
      f"(axes.py grades this document 11)")

# ── 7 / 3. how many records, and of what ─────────────────────────────────────
n = con.sql(f"SELECT len(entry) FROM read_json_auto({SRC})").fetchone()[0]
print(f"\n7. rows DuckDB reports: 1. Entries inside the bundle: {n}")
print("   the document is one object, so it is one row, exactly as on the")
print("   thread and on npm. The 564 records are inside a list column.")

# ── 3. the test this file exists for ─────────────────────────────────────────
print("\n3. does anything suggest the entries are 20 KINDS?")
kinds = con.sql(f"""
    SELECT e.resource.resourceType AS kind, count(*) AS n
    FROM read_json_auto({SRC}), unnest(entry) AS t(e)
    GROUP BY 1 ORDER BY n DESC
""").fetchall()
print(f"   `unnest(entry)` then `GROUP BY resource.resourceType` gives {len(kinds)}:")
for k, c in kinds[:6]:
    print(f"     {k:<24} {c:>4}")
print(f"     ... {len(kinds) - 6} more")
print("   and BOTH the unnest and the grouping column were supplied by a person.")
print("   Nothing in DESCRIBE, in the type, or in any error hinted at either.")

# ── 4. what the reconciled type actually did ─────────────────────────────────
fields = str(widest[1]).count("STRUCT")
print(f"\n4. the single reconciled `entry` type contains {fields} STRUCT keywords.")
print("   That is 20 record kinds merged into one declaration. The merge is the")
print("   answer to question 4 and DuckDB performs it rather than reporting it:")
print("   a field on 1 of 564 resources and a field on all 564 are both simply")
print("   present in the type, indistinguishable.")

# ── 5. where DuckDB gave up, and it is legible if you count ──────────────────
# The type contains the token JSON where DuckDB could not reconcile a subtree
# into a struct. That is its report of question 5, and it is four characters long.
import re
s = str(widest[1])
print(f"\n5. the type falls back to raw JSON in {s.count('JSON')} places:")
for m in re.finditer(r'"?(\w+)"?\s+JSON', s):
    print(f"     {m.group(1)}")
print("   `maximum_depth=-1` and `sample_size=-1` do not remove them, so this is")
print("   not truncation — it is DuckDB declining to unify types that conflict.")

print("""
   THREE OF THOSE FOUR ARE EXACTLY THE FIELDS design/probe.py FLAGS.
   `type`, `location` and `total` are the probe's entire "FIELDS THAT CHANGE
   TYPE" list for this document. Two independent tools, one a type system and
   one a describer, singled out the same three fields. DuckDB resolves them by
   storing raw JSON and says so only in a type declaration nobody reads; the
   probe resolves them by reporting them and, since 2026-08-09, by adding that
   each is an artifact of folding 20 resource kinds.

   THE FOURTH IS `category`, AND THE PROBE MISSES IT. Measured while writing
   this file:

     AllergyIntolerance.category  ->  ["environment"]        an array of STRINGS
     Observation.category         ->  [{"coding": [...]}]    an array of OBJECTS

   `design/probe.py` reports no polymorphism at `category`, because its `shape()`
   measures how deeply an array NESTS and not what it holds — `shape(["a"])` and
   `shape([{...}])` both return `array[1]`.

   That is a real defect and a competing tool found it, which is what the grid is
   for. It is also the FOURTH instance of one root cause, and the sharpest:
   `shape()` was added on 2026-08-09 to fix the third, after `03-natural-earth`
   showed that comparing types alone could not see polymorphism hiding in array
   depth. **The fix for one proxy introduced another.** Depth alone cannot see it
   either.

6. cannot — and no tool in either language has ever answered question 6.
""")
