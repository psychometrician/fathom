"""polars — one hour of public GitHub events

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json.gz   10.6 MB gzipped, 50 MB / 37,883 records raw
  measured      2026-08-09
  run           cd corpus/04-gharchive/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   0 is it sound                                 8   YES, see below      WRONG
   1 what is in here                             3   no                  PARTLY
   2 how deep                                    2   no                  PARTLY
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 4   no                  YES
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            1   no                  YES

WHY THIS FILE. The `scale` axis. `design/probe.py` needed 968 MB and sampled the
first 20,000 records; DuckDB read all 37,883 from the gzip in 133 MB. polars has
`read_ndjson` and a lazy `scan_ndjson`, so it is the other serious candidate.
"""
import gzip
import resource
import shutil
import sys
import time
from importlib.metadata import version

import polars as pl

print(f"python {sys.version.split()[0]}, polars {version('polars')}")

def rss():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r / 1e6 if sys.platform == "darwin" else r / 1e3

# ── 0. can it read the file as it SHIPS? ─────────────────────────────────────
# Measured across both forms and both settings, because the first draft of this
# file guessed that the gzip was the problem and it is not.
print("\n0. what polars does with this file:")
for label, kw in [("default", {}), ("infer_schema_length=None", {"infer_schema_length": None})]:
    for src in ("../source.json.gz", "../source.jsonl"):
        try:
            h = pl.read_ndjson(src, **kw).height
            print(f"     {label:<26} {src:<20} OK, {h:,} rows")
        except Exception as e:
            print(f"     {label:<26} {src:<20} FAILED — {type(e).__name__}: "
                  f"{str(e).splitlines()[0][:38]}")

print("""
   GZIP IS NOT THE PROBLEM — polars reads it directly, which is worth saying
   because the probe could not. The default FAILS on both forms with
   `expected null in json value, got object`.

   polars infers the schema from the first 100 records. GH Archive is ragged by
   null in 33 fields, so a field that is null in the first hundred events and an
   object in the hundred-and-first contradicts the inferred type and the read
   aborts. `infer_schema_length=None` reads all 37,883 in 1.7 seconds.

   **The flag that fixes it is one you only know to pass once you know the data
   is ragged, which is question 4.** The error message names a type conflict and
   does not mention the setting. This is jmespath's problem in another costume:
   the tool needs an answer it is being asked to produce.
""")

t0 = time.time()
df = pl.read_ndjson("../source.json.gz", infer_schema_length=None)
elapsed = time.time() - t0

# ── 7. how many records ──────────────────────────────────────────────────────
print(f"\n7. records: {df.height:,}   ({elapsed:.1f}s)")

# ── 1. what is in here ───────────────────────────────────────────────────────
schema = df.schema
print(f"\n1. top-level columns: {len(schema)}")
print(f"   schema as one string: {len(str(schema)):,} characters")
print(f"   (npm: 486,924 = 60% of file; thread: 3,154 = 1.6%)")

# ── 2. how deep ──────────────────────────────────────────────────────────────
def type_depth(dt):
    inner = getattr(dt, "inner", None)
    if inner is not None:
        return 1 + type_depth(inner)
    fields = getattr(dt, "fields", None)
    if fields:
        return 1 + max(type_depth(f.dtype) for f in fields)
    return 0

print(f"\n2. deepest nesting in the schema: "
      f"{max(type_depth(t) for t in schema.values())}   (true depth 7)")

# ── 4. always present vs sometimes ───────────────────────────────────────────
nulls = df.null_count().row(0)
sometimes = [(c, n) for c, n in zip(df.columns, nulls) if n]
print(f"\n4. top-level columns null on some rows: {len(sometimes)} of {len(schema)}")
for c, n in sometimes:
    print(f"     {c:<22} null on {n:,} of {df.height:,}")

# ── peak memory, measured in a CLEAN process ─────────────────────────────────
# `ru_maxrss` is a high-water mark for the whole process, and the probing in
# section 0 above loads this file three times. Reporting that number would have
# put ~1,180 MB in a comparison column and blamed polars for this file's own
# instrumentation. One read, one process, measured from outside.
import subprocess
ONE_READ = (
    "import polars as pl, resource, sys;"
    "pl.read_ndjson('../source.json.gz', infer_schema_length=None);"
    "r=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;"
    "print(r/1e6 if sys.platform=='darwin' else r/1e3)"
)
clean = float(subprocess.run([sys.executable, "-c", ONE_READ],
                             capture_output=True, text=True).stdout.strip())
print(f"\n   peak RSS, one read in a clean process: {clean:,.0f} MB")
print(f"   this process, after loading the file three times while probing: "
      f"{rss():,.0f} MB")
print(f"   probe 968 MB on a 20,000-record SAMPLE; DuckDB 133 MB on all 37,883")

print("""
3, 5, 6. cannot, and 5 is the one this file was chosen for.

  polars must give `payload` one type across 37,883 events. GitHub's payloads
  differ completely between a PushEvent and a WatchEvent, so that single type is
  the UNION of every event's shape, and every field in it is null for most rows.
  The reconciliation is the answer to question 5 and polars performs it silently.

  NOTES.md grades `path variance 76` here, the highest in the corpus, and none of
  it survives into the schema. What survives is one very wide struct.
""")
