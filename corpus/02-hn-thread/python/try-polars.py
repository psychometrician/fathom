"""polars — one Hacker News comment thread

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   193 KB, 336 nodes, 13 levels of recursion
  measured      2026-08-09
  run           cd corpus/02-hn-thread/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   no                  PARTLY
   2 how deep                                    3   no                  PARTLY
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 -   -                   cannot
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            2   YES                 partly

WHY THIS FILE EXISTS. On `01-npm-registry` polars produced a schema **486,924
characters long, 60% of the file**, because it turned 288 version strings into
288 struct fields. This document has no keys-as-data at all — 13 field names,
repeated at 13 levels. **If the O(data) claim is really about data rather than
about polars, the schema here should be small.** That is the test.
"""
import json
import sys
from importlib.metadata import version

import polars as pl

print(f"python {sys.version.split()[0]}, polars {version('polars')}")

df = pl.read_json("../source.json")
schema = df.schema

# ── 1. what is in here ───────────────────────────────────────────────────────
print(f"\n1. columns at the top level: {len(schema)}")
print(f"   the schema, printed as one string: {len(str(schema)):,} characters")
print(f"   on 01-npm-registry the same call gave 486,924 characters, 60% of a")
print(f"   804,956-byte file. This file is {len(open('../source.json','rb').read()):,} bytes.")

# ── 2. how deep ──────────────────────────────────────────────────────────────
def type_depth(dtype):
    inner = getattr(dtype, "inner", None)
    if inner is not None:
        return 1 + type_depth(inner)
    fields = getattr(dtype, "fields", None)
    if fields:
        return 1 + max(type_depth(f.dtype) for f in fields)
    return 0

d = max(type_depth(t) for t in schema.values())
print(f"\n2. deepest nesting in the schema: {d}   (true depth 25)")

# ── 7. how many records ──────────────────────────────────────────────────────
doc = json.load(open("../source.json"))
def count(n):
    return 1 + sum(count(c) for c in n.get("children", []))
print(f"\n7. rows polars reports: {df.height}")
print(f"   nodes in the thread, counted in Python: {count(doc)}")

print("""
3, 4, 5, 6. cannot, and on a recursive document the reason sharpens.

  polars must give a column ONE type. A comment contains comments, so the honest
  type of `children` is infinite, and polars resolves that by inferring the
  nesting it actually observed and stopping. The schema is therefore a picture of
  how deep THIS file happens to go, not of what the document is.

  That is the recursion failure this project already measured on its own probe:
  describing a self-similar structure once per level is O(depth) for a thing
  whose entire point is that it repeats. polars has no fold, so it has no way to
  say "a comment, containing comments".
""")
