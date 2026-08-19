# pandas — one hour of public GitHub events, at 17x the size of entry 04
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          pandas (version printed at run time)
#  file          ../source.json.gz   118 MB gzipped, 870 MB / 286,864 records raw
#  measured      2026-08-14
#  run           cd corpus/26-gharchive-scale/python && uv run try-pandas.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# **The prediction was that pandas does not complete within ten minutes.** It is
# tested three ways rather than one, because "pandas cannot read this" would be
# a claim about the wrong thing if only the worst spelling were tried:
#   1. read_json(lines=True) on the whole file
#   2. the same with chunksize, which is pandas' own streaming answer
#   3. a scaling probe on 10k / 40k records, to say WHERE the wall is

import gzip
import io
import json
import sys
import time
import pandas as pd
from _budget import Attempt, rss_mb, RECORDS, in_subprocess

SRC = "../source.json.gz"

# ── one strategy per process, so peak RSS is that strategy's own ─────────────
if len(sys.argv) > 1:
    mode = sys.argv[1]
    shape = (0, 0) if 'shape' == 'shape' else 0
    with Attempt(mode, quiet=True) as a:
        if mode == "whole":
            df = pd.read_json(SRC, lines=True, compression="gzip")
            shape = df.shape
        else:
            rows = cols = 0
            with pd.read_json(SRC, lines=True, compression="gzip",
                              chunksize=20_000) as it:
                for c in it:
                    rows += len(c); cols = max(cols, c.shape[1])
            shape = (rows, cols)
    print(f"{a.finished}\t{a.secs:.1f}\t{a.rss:.0f}\t{shape[0]}\t{shape[1]}\t{a.why}")
    sys.exit(0)

print(f"pandas {pd.__version__} · file {SRC} · {RECORDS:,} records, 870 MB raw")

print("\nQ0  pandas parses and says nothing. Python's json has bignums, so")
print(f"    9007199254740993 -> {json.loads('{\"n\":9007199254740993}')['n']} (exact). CANNOT.")

# ── THE SCALING PROBE. Where is the wall? ────────────────────────────────────
print("\n── read_json(lines=True) on the first N records ─────────────────────────")
print("  N            rows x cols        seconds     peak RSS")
curve = []
for n in (10_000, 40_000, 80_000):
    with gzip.open(SRC, "rt") as fh:
        head = "".join(next(fh) for _ in range(n))
    t0 = time.perf_counter()
    # StringIO, because pandas 3.0 refuses a literal JSON string and its
    # error message echoes the entire payload back at you.
    df = pd.read_json(io.StringIO(head), lines=True)
    s = time.perf_counter() - t0
    print(f"  {n:<12,} {df.shape[0]:>7,} x {df.shape[1]:<4} {s:>10.1f} s {rss_mb():>9,.0f} MB")
    curve.append((n, s, rss_mb()))
    del df
per_rec_mb = (curve[-1][2] - curve[0][2]) / (curve[-1][0] - curve[0][0])
print(f"  marginal cost: {per_rec_mb*1000:.1f} MB per 1,000 records")
print(f"  -> extrapolated for all {RECORDS:,}: {per_rec_mb*RECORDS:,.0f} MB")

# ── THE WHOLE FILE, two ways, EACH IN ITS OWN PROCESS. ───────────────────────
print("\n── the whole file, one strategy per process ─────────────────────────────")
print("  strategy                    finished   seconds   peak RSS        shape")
res = {}
for mode in ("whole", "chunked"):
    out, rc = in_subprocess("try-pandas.py", mode)
    if out.startswith("!\t"):
        print(f"  {mode:<24} {'FAILED':>10}   {out[2:]}")
        res[mode] = (False, 0, 0, 0, 0)
        continue
    fin, secs, rss, rows, cols, why = (out.split("\t") + [""])[:6]
    res[mode] = (fin == "True", float(secs), float(rss), int(rows), int(cols))
    print(f"  {mode:<24} {fin:>10} {float(secs):>9.1f} {float(rss):>9,.0f} MB "
          f"{int(rows):>10,} x {cols}")
full_ok, chunk_ok = res["whole"][0], res["chunked"][0]
rows, cols = res["chunked"][3], res["chunked"][4]

# ── The questions, answered from whatever survived. ──────────────────────────
print(f"\nQ1  {cols if chunk_ok else '?'} top-level columns, from the chunked read.")
print("    ONE LEVEL — every event's `payload` stays a dict in an object column.")
print("\nQ2  CANNOT from pandas. Depth needs a walk, and a walk needs the document.")
print(f"\nQ7  {rows:,} records." if chunk_ok else "\nQ7  CANNOT — nothing completed.")
print("\nQ3  pandas names no candidates and prices none. CANNOT.")
print("\nQ6  CANNOT.")
print("\nQ5  PARTLY at best: an `object` column holds mixed Python types and the")
print("    dtype does not report them. On entry 29 this counted pandas' own NaN")
print("    fills as a value type the document did not contain.")
print("\nQ12 json_normalize on 286,864 nested records is the 427,019-column")
print("    explosion of entry 29 multiplied by the record count. NOT ATTEMPTED,")
print("    and saying so is the honest answer rather than a timing.")
print("\nQ8/Q9  fine on a chunk, once somebody has said what a row is — which is Q3.")
print("Q10/Q11 CANNOT. No path search, and record_path must be named.")

print(f"""
CONCLUSION. Written after the run and corrected against what printed.
  whole-file read finished: {full_ok} · chunked read finished: {chunk_ok}

THE PREDICTION SAID pandas WOULD NOT COMPLETE IN TEN MINUTES AND IT WAS WRONG.
The whole 870 MB file reads in about 13 seconds at roughly 6 GB, and the
chunked form does it in 6 seconds at half the memory.

IT SURVIVES BY NOT LOOKING INSIDE, and that is the whole explanation. The
result is 286,864 x 8 — `payload` stays an opaque dict in an object column, so
pandas never meets the nesting that produced entry 29's 427,019-column
explosion. It has READ the file without DESCRIBING it, which on this grid is
questions 7 and 8 answered and questions 1, 2, 3, 6, 10, 11 and 12 not.

CHUNKING IS THE RIGHT ANSWER AND IT IS PANDAS' OWN. `chunksize=20_000` is the
same number fathom samples at, and it costs 6 seconds against 13 and half the
peak — while covering ALL 286,864 records rather than the first 20,000. A
bounded reader beats a bounded sample here on every axis at once.

THE SCALING PROBE OVER-PREDICTED BY FOUR TIMES and it is kept as printed. From
10k/40k/80k it extrapolated about 25 GB for the full read, which actually took
6 GB. `ru_maxrss` is a HIGH-WATER MARK, so each probe iteration inherits the
garbage of the ones before it and the marginal cost reads far too high. THE
LESSON IS THE MEASUREMENT'S, not pandas': a memory curve built from repeated
allocation inside one process measures the allocator, not the workload. The
whole-file and chunked figures avoid it by running in their own processes.

AND A FIRST DRAFT OF THIS FILE HAD EXACTLY THAT BUG IN ITS HEADLINE NUMBER,
reporting the chunked read at 4,672 MB against the whole-file read's 3,755 —
making the strategy that never holds the file look more expensive than the one
that does. Measured properly, in separate processes, it is 3,312 against 5,972.
""")
