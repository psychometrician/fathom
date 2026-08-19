"""DuckDB — one hour of public GitHub events

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json.gz   10.6 MB gzipped, 50 MB / 37,883 records raw
  measured      2026-08-09
  run           cd corpus/04-gharchive/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   0 is it sound                                 3   no                  YES
   1 what is in here                             3   no                  PARTLY
   2 how deep                                    2   no                  PARTLY
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 4   no                  YES
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            2   no                  YES

WHY THIS FILE IS THE INTERESTING ONE. `design/probe.py` needed **968 MB of RSS**
for this document, an 18.8x multiplier, and on its held-out run **could not read
the gzip at all**. This is the corpus's only reading on the `scale` axis, and it
is the axis where an established engine should beat a 400-line prototype. The
point of this attempt is to find out by how much, and to say so.
"""
import resource
import sys
from importlib.metadata import version

import duckdb

print(f"python {sys.version.split()[0]}, duckdb {version('duckdb')}")

def rss():
    # macOS reports ru_maxrss in bytes; Linux in kilobytes.
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r / 1e6 if sys.platform == "darwin" else r / 1e3

con = duckdb.connect()
GZ = "'../source.json.gz'"

# ── 0. is it sound / can it be read at all ───────────────────────────────────
# The whole question for this file. It is NDJSON, which is not valid JSON, and it
# ships gzipped. The probe managed neither on its first attempt.
n = con.sql(f"SELECT count(*) FROM read_json_auto({GZ}, format='newline_delimited')"
            ).fetchone()[0]
print(f"\n0/7. records read straight from the GZIP: {n:,}")
print(f"     no decompression step, no `lines=True`, no flag beyond the format.")
print(f"     the probe's held-out run could not open this file.")

# ── 1. what is in here ───────────────────────────────────────────────────────
desc = con.sql(f"DESCRIBE SELECT * FROM read_json_auto({GZ}, "
               f"format='newline_delimited')").fetchall()
total = sum(len(str(r[1])) for r in desc)
widest = max(desc, key=lambda r: len(str(r[1])))
print(f"\n1. DESCRIBE returns {len(desc)} rows")
print(f"   total type text: {total:,} characters   "
      f"(npm: 378,036 in one cell; thread: 2,514)")
print(f"   widest: {widest[0]!r} at {len(str(widest[1])):,} characters")

# ── 2. how deep ──────────────────────────────────────────────────────────────
# Counting `STRUCT` keywords measures BREADTH, not depth: `payload` holds 57 of
# them across the union of every event type's shape, and the document is 7 levels
# deep. The first draft of this line called 57 "nesting", which would have put a
# wrong depth in a comparison column. Real depth needs the brackets balanced.
def bracket_depth(t):
    d = best = 0
    for ch in str(t):
        d += ch == "("
        best = max(best, d)
        d -= ch == ")"
    return best

print(f"\n2. STRUCT keywords in the widest type: "
      f"{str(widest[1]).count('STRUCT')} — that is breadth, not depth")
print(f"   nesting depth of the type, by balancing brackets: "
      f"{bracket_depth(widest[1])}   (true document depth 7)")

# ── 4. always present vs sometimes ───────────────────────────────────────────
# The thing DuckDB is genuinely excellent at, and it is worth showing.
cols = [r[0] for r in desc]
sel = ", ".join(f"count({c!r}) AS {c!r}" for c in cols)
counts = con.sql(f"SELECT {sel} FROM read_json_auto({GZ}, "
                 f"format='newline_delimited')").fetchall()[0]
sometimes = [(c, v) for c, v in zip(cols, counts) if v < n]
print(f"\n4. top-level fields: {len(cols)}, of which {len(sometimes)} are not on "
      f"every record")
for c, v in sometimes:
    print(f"     {c:<22} {v:,} of {n:,}")

print(f"\n   peak RSS for everything above: {rss():,.0f} MB")
print(f"   design/probe.py needed 968 MB, and sampled the first 20,000 records.")

print("""
3, 5, 6. cannot.

  Question 5 is the sharp one here. DuckDB inferred ONE type per column across
  37,883 records, so a field that is a string on some events and an object on
  others has already been resolved — into a union, or a VARCHAR, or an error,
  depending on the sample it read. The reconciliation happened, and the report of
  what was reconciled is not available. `path variance 76` is the highest in the
  corpus and none of it is visible here.

  Question 3 is the usual one. `payload` differs completely by `type`, and every
  answer above treats all 37,883 events as one table because the file has one
  row shape at the top. The eight row shapes NOTES.md grades are not reachable
  without a person naming `type` first.
""")
