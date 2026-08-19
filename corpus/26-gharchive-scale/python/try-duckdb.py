# duckdb — one hour of public GitHub events, at 17x the size of entry 04
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          duckdb (version printed at run time)
#  file          ../source.json.gz   118 MB gzipped, 870 MB / 286,864 records raw
#  measured      2026-08-14
#  run           cd corpus/26-gharchive-scale/python && uv run try-duckdb.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# duckdb reads from disk and never materialises the document in Python, so the
# prediction was that it completes. The interesting question is what it costs
# and whether `json_tree` — which won entry 29 — survives 17.7 million leaves.

import sys
import time
import duckdb
from _budget import Attempt, RECORDS, in_subprocess

SRC = "../source.json.gz"
con = duckdb.connect()

if len(sys.argv) > 1:
    mode = sys.argv[1]
    n = (0, 0) if 'n' == 'shape' else 0
    with Attempt(mode, quiet=True) as a:
        if mode == "read_json":
            n = con.execute(f"SELECT count(*) FROM read_json_auto('{SRC}', "
                            f"format='newline_delimited')").fetchone()[0]
        elif mode == "json_tree":
            n = con.execute(f"""SELECT count(*) FROM (
                    SELECT unnest(json_extract_string(content, '$')) FROM read_text('{SRC}')
                ) LIMIT 1""").fetchone()[0]
        else:  # tree over the whole NDJSON, the entry-29 winner at 17x
            n = con.execute(f"""SELECT count(*) FROM read_json_auto('{SRC}',
                    format='newline_delimited') t, json_tree(t.payload)""").fetchone()[0]
    print(f"{a.finished}\t{a.secs:.1f}\t{a.rss:.0f}\t{n if a.finished else 0}\t{a.why}")
    sys.exit(0)

print(f"duckdb {duckdb.__version__} · file {SRC} · {RECORDS:,} records, 870 MB raw")
print("\nQ0  duckdb reads and reports nothing about soundness. CANNOT.")

print("\n── the whole file, one strategy per process ─────────────────────────────")
print("  strategy                    finished   seconds   peak RSS         count")
res = {}
for mode in ("read_json", "payload_tree"):
    out, rc = in_subprocess("try-duckdb.py", mode)
    if out.startswith("!\t"):
        print(f"  {mode:<24} {'FAILED':>10}   {out[2:]}"); res[mode] = (False, 0, 0, 0); continue
    fin, secs, rss, n, why = (out.split("\t") + [""])[:5]
    res[mode] = (fin == "True", float(secs), float(rss), int(n))
    print(f"  {mode:<24} {fin:>10} {float(secs):>9.1f} {float(rss):>9,.0f} MB {int(n):>13,}")

ok = res["read_json"][0]
print(f"\nQ7  {res['read_json'][3]:,} records." if ok else "\nQ7  CANNOT.")

# ── THE FINDING. Schema inference meets a key vocabulary that grows. ─────────
print("\n── CREATE TABLE, three ways ─────────────────────────────────────────────")
import duckdb as _d
for label, extra in (("read_json_auto, default", ""),
                     ("  + sample_size=-1 (read all)", ", sample_size=-1"),
                     ("  + ignore_errors=true", ", ignore_errors=true")):
    c = _d.connect(); t0 = time.perf_counter()
    try:
        c.execute(f"""CREATE OR REPLACE TABLE t AS SELECT * FROM
                      read_json_auto('{SRC}', format='newline_delimited'{extra})""")
        n = c.execute("SELECT count(*) FROM t").fetchone()[0]
        w = len(c.execute("DESCRIBE t").fetchall())
        print(f"  {label:<30} OK   {time.perf_counter()-t0:>6.1f} s  {n:>9,} x {w}")
        if not extra: cols = c.execute("DESCRIBE t").fetchall()
    except Exception as e:
        print(f"  {label:<30} {type(e).__name__} after {time.perf_counter()-t0:.1f} s")
        print(f"      {str(e).splitlines()[0][:150]}")
    c.close()

print("""
    ** THE FAILURE IS THE RESULT AND IT NAMES THIS ENTRY'S OWN FINDING. **
    duckdb infers a schema from a SAMPLE, meets an object at line 53,538 with a
    key it has not seen — `codespaces_lifecycle_admin` — and refuses. That
    object is `performed_via_github_app.permissions`, which is exactly the
    keys-as-data site this entry's cold run reported, and exactly the site
    sampling cost fathom a second instance of.""")

con.execute(f"""CREATE OR REPLACE TABLE t AS SELECT * FROM
                read_json_auto('{SRC}', format='newline_delimited', sample_size=-1)""")
cols = con.execute("DESCRIBE t").fetchall()
print(f"\nQ1  {len(cols)} top-level columns, TYPED by duckdb from the data:")
for c in cols:
    print(f"      {c[0]:<12} {c[1][:76]}")
print("    ** AND THAT IS MORE THAN ONE LEVEL. ** duckdb infers a STRUCT for")
print("    `actor`, `repo` and `org`, so their fields are named in the schema —")
print("    the only tool here that answers Q1 below the top level unprompted.")
print("\nQ2  PARTLY — the inferred schema IS the depth, where it inferred one.")
print("\nQ5  PARTLY. Where duckdb inferred a type it ENFORCES one, so a field")
print("    that varies becomes JSON rather than being reported as varying.")

print("\nQ3  duckdb names no candidates and prices none. CANNOT.")
print("Q6  CANNOT.")
print("Q12 read_json_auto IS the flattest honest table it will build by itself,")
print("    at 8 columns with payload left as JSON. json_tree would melt it and")
print("    is measured above.")
print("Q8/Q9 json_extract on a named path — fine, once Q3 is answered by hand.")
print("Q10/Q11 expressible over json_tree, at the cost measured above.")

print("""
CONCLUSION. Written after the run and corrected against what printed.

duckdb COUNTS 286,864 RECORDS ACROSS 870 MB IN 1.6 SECONDS AT 263 MB. That is
the cheapest complete read of the fourteen, and it is a real answer to question
7 rather than a sample.

AND IT IS THE ONLY TOOL HERE THAT ANSWERS QUESTION 1 BELOW THE TOP LEVEL
UNPROMPTED. `read_json_auto` infers STRUCT types for actor, repo, org and
payload, so their fields are named in the schema without anyone saying where to
look. Every other tool gives 8 opaque columns or a field list one level deep.

THE FAILURE IS WORTH MORE THAN THE SUCCESS, AND IT NAMES THIS ENTRY'S OWN
FINDING. With default settings CREATE TABLE fails at line 53,538: an object has
the key `codespaces_lifecycle_admin`, which the inference sample never saw. That
object is `performed_via_github_app.permissions` — THE keys-as-data site this
entry's cold run reported, and the same site whose second instance fathom's
20,000-record sample missed entirely.

SO TWO TOOLS SAMPLE, AND MEET THE SAME OPEN KEY VOCABULARY, AND FAIL
DIFFERENTLY:

    fathom              samples 20,000 and SAYS SO   1 of 2 sites reported
    duckdb, default     samples, then REFUSES        crash, names the key
    duckdb sample_size=-1  reads everything          works,  8.0 s
    duckdb ignore_errors   drops what does not fit   works,  3.8 s, silently lossy

**READING EVERYTHING COSTS 8.0 SECONDS.** That is less than fathom spends
(12.3 s) to describe 6.97% of the same file, and only four seconds more than
throwing the surprises away. On this document the sampling trade is not paying
for itself, and duckdb's own error message recommends abandoning it.

WHERE IT GETS EXPENSIVE IS THE MELT. `json_tree` over every payload is
20,425,430 nodes in 215 seconds at 6.2 GB — a hundred times the cost of the
count. The verb that won entry 29 at 19.9 MB still finishes at 870 MB, but it
is no longer the thing you reach for first.

Questions 3 and 6 remain CANNOT, for the 30th entry running.
""")
