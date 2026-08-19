# polars — one hour of public GitHub events, at 17x the size of entry 04
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          polars (version printed at run time)
#  file          ../source.jsonl   870 MB / 286,864 records  (see note)
#  measured      2026-08-14
#  run           cd corpus/26-gharchive-scale/python && uv run try-polars.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# **The prediction was that polars completes IF `scan_ndjson` is used and fails
# on `read_ndjson` — that a streaming reader is the difference, not the engine.**
# Both are measured, each in its own process.
#
# It reads the PLAIN .jsonl rather than the .gz, unlike the other Python
# attempts here: polars' ndjson readers do not take a gzip path. That is itself
# an answer and it is stated rather than worked around.

import sys
import time
import polars as pl
from _budget import Attempt, RECORDS, in_subprocess

SRC = "../source.jsonl"

if len(sys.argv) > 1:
    mode = sys.argv[1]
    shape = (0, 0) if 'shape' == 'shape' else 0
    with Attempt(mode, quiet=True) as a:
        if mode == "read_eager":
            df = pl.read_ndjson(SRC); shape = df.shape
        elif mode == "scan_len_only":
            # counts rows WITHOUT materialising a single value
            lf = pl.scan_ndjson(SRC)
            shape = (lf.select(pl.len()).collect().item(), len(lf.collect_schema()))
        elif mode == "scan_collect_all":
            shape = pl.scan_ndjson(SRC).collect().shape
        else:  # read everything before deciding the schema
            df = pl.scan_ndjson(SRC, infer_schema_length=None).collect()
            shape = df.shape
    print(f"{a.finished}\t{a.secs:.1f}\t{a.rss:.0f}\t{shape[0]}\t{shape[1]}\t{a.why}")
    sys.exit(0)

print(f"polars {pl.__version__} · file {SRC} · {RECORDS:,} records, 870 MB raw")
print("\nQ0  polars reads and reports nothing about soundness. CANNOT.")
print("\n    (and it will not take the .gz at all: pl.read_ndjson on a gzipped")
print("     path is not supported, so this attempt uses the 912 MB plain file")
print("     while every other Python attempt here reads the 118 MB archive.)")

print("\n── the whole file, one strategy per process ─────────────────────────────")
print("  strategy                    finished   seconds   peak RSS         shape")
res = {}
for mode in ("read_eager", "scan_len_only", "scan_collect_all", "infer_all"):
    out, rc = in_subprocess("try-polars.py", mode)
    if out.startswith("!\t"):
        print(f"  {mode:<24} {'FAILED':>10}   {out[2:]}"); res[mode] = (False, 0, 0, 0, 0); continue
    fin, secs, rss, a_, b_, why = (out.split("\t") + [""])[:6]
    res[mode] = (fin == "True", float(secs), float(rss), int(a_), int(b_))
    print(f"  {mode:<24} {fin:>10} {float(secs):>9.1f} {float(rss):>9,.0f} MB "
          f"{int(a_):>10,} x {b_}" if fin == "True" else f"  {mode:<24} {'FAILED':>10}   {why}")

print("""
    ** LAZINESS IS NOT WHAT SAVES IT, AND THE PREDICTION SAID IT WAS. **
    `scan_ndjson` survives `select(len())` only because that never materialises
    a value. Ask it to `collect()` the data and it fails with the SAME error as
    the eager reader. What actually works is `infer_schema_length=None` — read
    everything before deciding the schema — which is duckdb's `sample_size=-1`
    under another name, and fails for the same reason without it.""")
lazy = res["infer_all"][0]
print(f"\nQ7  {res['scan_len_only'][3]:,} records.")
print(f"\nQ1  {res['scan_len_only'][4]} top-level columns from the lazy schema.")
print("    ONE LEVEL, with payload a struct polars types but does not name here.")
print("\nQ2  CANNOT without a walk, and a walk needs the document in memory.")
print("Q3  polars names no candidates and prices none. CANNOT.")
print("Q6  CANNOT.")
print("Q5  PARTLY — polars TYPES a column, so a field that varies either becomes")
print("    a struct union or fails the read. Variation is enforced, not reported.")
print("Q12 the melt has no polars spelling: unnest needs a named struct column,")
print("    explode a named list column, and neither has a 'whatever is there'")
print("    form. Same conclusion as entry 29, now with 286,864 records behind it.")
print("Q8/Q9  fine once a row is chosen, which is Q3.")
print("Q10/Q11 CANNOT.")

print("""
CONCLUSION. Written after the run and corrected against what printed.

THE PREDICTION WAS HALF RIGHT FOR THE WRONG REASON. It said polars completes if
`scan_ndjson` is used and fails on `read_ndjson` — that a STREAMING READER is
the difference. The eager reader does fail and the lazy one does complete, so
the prediction scores as right and its reasoning is wrong.

LAZINESS IS NOT WHAT SAVES IT. `scan_ndjson().select(len())` succeeds only
because it never materialises a value. Ask the same lazy frame to `collect()`
and it fails with the IDENTICAL error:

    ComputeError: expected null in json value, got object

What actually works is `infer_schema_length=None` — read the whole file before
deciding the schema — at 20 seconds and 5 GB.

AND THAT IS duckdb's `sample_size=-1` UNDER ANOTHER NAME. Two engines, two
languages, the same failure and the same fix: infer from a PREFIX and this file
contradicts you later. duckdb met an unseen key in
`performed_via_github_app.permissions`; polars met a field that is null early
and an object later. **THREE TOOLS NOW — fathom, duckdb, polars — decide what
this document is from its first records, and all three are wrong about it.**

fathom is the only one of the three that SAYS it sampled. duckdb crashes and
names the key; polars crashes and names the type; fathom reports a description
of the first 20,000 records and tells you so. Of the three that is the best
behaviour and it is still incomplete: on this file the sample cost it one of
two keys-as-data sites, and reading everything would have cost 8 seconds in
duckdb and 20 in polars.

AND IT WILL NOT READ THE ARCHIVE. Every other Python attempt here opens the
118 MB `.gz`; polars' ndjson readers take no gzip path, so this one reads the
912 MB plain file. On a format whose whole point is streaming from cheap
storage, that is a real gap rather than a preference.

Q3 and Q6 remain CANNOT, for the 30th entry running, and Q12 has no polars
spelling at all — unnest needs a named struct, explode a named list, and
neither has a form meaning `whatever is there`.
""")
