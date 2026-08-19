"""DuckDB — one Hacker News comment thread

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   193 KB, 336 nodes, 13 levels of recursion
  measured      2026-08-09
  run           cd corpus/02-hn-thread/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   no                  PARTLY
   2 how deep                                    2   no                  PARTLY
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 -   -                   cannot
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            2   YES                 WRONG

WHY THIS FILE EXISTS. On `01-npm-registry` DuckDB's `DESCRIBE` returned eighteen
tidy rows and hid a **378,036-character** type inside one cell — the single most
quoted measurement in `VERDICT.md`. This document has no keys-as-data. If the
type here is small, the explosion was caused by keys-as-data specifically and not
by nesting, which is a sharper claim than the one currently written down.
"""
import sys
from importlib.metadata import version

import duckdb

print(f"python {sys.version.split()[0]}, duckdb {version('duckdb')}")

con = duckdb.connect()

# ── 1. what is in here ───────────────────────────────────────────────────────
desc = con.sql("DESCRIBE SELECT * FROM read_json('../source.json')").fetchall()
print(f"\n1. DESCRIBE returns {len(desc)} rows")
widest = max(desc, key=lambda r: len(str(r[1])))
print(f"   widest type in one cell: {len(str(widest[1])):,} characters "
      f"(column {widest[0]!r})")
print(f"   total across all {len(desc)} type strings: "
      f"{sum(len(str(r[1])) for r in desc):,} characters")
print(f"   on 01-npm-registry the widest cell held 378,036 characters.")

# ── 2. how deep ──────────────────────────────────────────────────────────────
# The nesting is legible in the type string, which is the only place it lives.
depth = max(str(r[1]).count("STRUCT") for r in desc)
print(f"\n2. STRUCT keywords nested in the widest type: {depth}")
print("   which is depth information, in a string, that you would have to parse")
print("   out of a type declaration to use.")

# ── 7. how many records ──────────────────────────────────────────────────────
n = con.sql("SELECT count(*) FROM read_json('../source.json')").fetchone()[0]
print(f"\n7. rows: {n}   (the thread has 336 nodes)")
print("   One, and it is the same answer polars and pandas give: the document is")
print("   one object, so it is one row, and the 336 records are inside it.")

print("""
3, 4, 5, 6. cannot.

  DuckDB has a recursive CTE and could walk this thread if a person wrote the
  join. That person has to supply the same three facts everything else needed:
  that a node contains nodes, that `children` is the recursive field, and that
  every node is a record.

  The type string is the honest summary of the position. It contains the
  document's whole structure and it is not a description — it is the structure,
  serialised, in one cell, which is what `VERDICT.md` means by output
  proportional to the data.
""")
