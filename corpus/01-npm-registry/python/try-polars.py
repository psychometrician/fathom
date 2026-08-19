"""polars — npm registry metadata for `express`

Scoring header follows ../r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   786 KB, 288 versions, 25,044 paths
  measured      2026-08-09
  run           cd corpus/01-npm-registry/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   no                  PARTLY
   2 how deep                                    3   no                  yes
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 -   -                   cannot
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            2   YES                 partly
  13 needed the shape in advance?                    see notes below
  16 lines, and how much is ceremony?                see notes below

WHAT THIS FILE IS FOR. `VERDICT.md` claims every existing describer's output is
proportional to the DATA rather than to the structure. That claim was measured on
R tools only. polars is the strongest Python counter-candidate, because unlike
pandas it infers a real nested schema instead of flattening to strings.
"""
import json
import sys
from importlib.metadata import version

import polars as pl

# Printed rather than typed. The header above records what produced the scores;
# this line records what just ran, and a difference between them means the re-run
# is not comparable. It is code rather than trust because two of this corpus's
# first three headers named a version that was not installed.
print(f"python {sys.version.split()[0]}, polars {version('polars')}")

# ── 1. what is in here ───────────────────────────────────────────────────────
# polars infers a schema, which is the right IDEA and the reason this tool is
# worth measuring. The question is how big the answer is.
df = pl.read_json("../source.json")
schema = df.schema
print(f"\n1. columns at the top level: {len(schema)}")
print(f"   the schema, printed as one string: {len(str(schema)):,} characters")

# The comparison that matters. DuckDB's DESCRIBE returned eighteen tidy rows and
# hid a 378,036-character type inside one cell. Does polars do the same thing?
widest = max(schema.items(), key=lambda kv: len(str(kv[1])))
print(f"   widest single column: {widest[0]!r} -> "
      f"{len(str(widest[1])):,} characters of type")

# ── 2. how deep ──────────────────────────────────────────────────────────────
def type_depth(dtype):
    inner = getattr(dtype, "inner", None)
    if inner is not None:
        return 1 + type_depth(inner)
    fields = getattr(dtype, "fields", None)
    if fields:
        return 1 + max(type_depth(f.dtype) for f in fields)
    return 0

print(f"\n2. deepest nesting visible in the schema: "
      f"{max(type_depth(d) for d in schema.values())}")

# ── 7. how many records ──────────────────────────────────────────────────────
# Only answerable because a human already decided a version is a record. polars
# read the document as ONE row, which is the honest reading of a JSON object and
# is not the answer anybody wants.
print(f"\n7. rows polars thinks there are: {df.height}")
print(f"   versions, once a human says a version is a record: "
      f"{len(json.load(open('../source.json'))['versions'])}")

# ── 3, 4, 5, 6 — cannot, and the reason is the same one every time ───────────
print("""
3,4,5,6. cannot.

  A schema is not a description of records. polars reports ONE row with N
  columns whose types are deeply nested structs, so:

    - question 3 has no answer to give: polars has already committed to the
      whole document being one row, which is the reading nobody wanted.
    - questions 4 and 5 are about variation ACROSS sibling records, and polars
      has folded that variation into the struct type rather than reporting it.
      A field present in 200 of 288 versions and a field present in all 288 are
      the same struct field here.
    - question 6 needs to know that `versions` keys ARE data. polars turned each
      version string into its own struct FIELD, which is the opposite reading and
      is exactly what makes the schema enormous.
""")
